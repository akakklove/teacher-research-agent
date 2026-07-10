"""FastAPI 服务层 — 教师科研查询 API"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path
import os

# 添加 agent 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
from metric_engine import MetricEngine
from intent_router import IntentRouter
from insight_engine import InsightEngine
from dashboard_composer import DashboardComposer
from conversation_memory import ConversationMemory, get_memory
from scenario_templates import ScenarioEngine
from template_store import TemplateStore
from metric_discovery import MetricDiscovery
from auth import AuthManager, get_current_user
from llm import create_chat_model

# 初始化 LLM（首次启动时创建，后续复用）
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        try:
            _llm = create_chat_model()
            print("[LLM] 通义千问已连接")
        except Exception as e:
            print(f"[LLM] 连接失败，将使用规则引擎兜底: {e}")
            _llm = None
    return _llm

app = FastAPI(
    title="教师个人科研查询器",
    version="0.4.0",
    description="输入教师工号，返回个人科研全景数据 — 支持多轮对话"
)

# ── 数据库配置（支持环境变量覆盖） ──
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3307")),
    "user": os.getenv("DB_USER", "tr_user"),
    "password": os.getenv("DB_PASSWORD", "tr_pass_2025"),
    "database": os.getenv("DB_NAME", "teacher_research"),
    "charset": "utf8mb4",
}


def get_engine() -> MetricEngine:
    return MetricEngine(DB_CONFIG)


# ── 响应模型 ──
class MetricValue(BaseModel):
    metric_id: str
    name: str
    category: str
    chart_type: str
    unit: str = ""
    value: Optional[float] = None
    rows: list = []
    error: Optional[str] = None


class TeacherOverview(BaseModel):
    teacher: dict
    metrics: list[MetricValue]
    category_summary: dict  # 各模块摘要


# v0.4: 聊天请求/响应模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None      # 继续已有会话
    teacher_id: Optional[str] = None       # 首次对话必须提供


class ChatResponse(BaseModel):
    session_id: str
    reply: str                             # AI 文本回复
    intent: str                            # 识别的意图
    is_followup: bool                      # 是否为追问
    metrics: list[dict]                    # 指标数据
    insights: list[str]                    # AI 洞察
    teacher: dict                          # 教师信息
    metric_ids: list[str] = []             # v0.4: 查询的指标ID列表（供模板保存用）


# ── API 路由 ──
@app.get("/")
def root():
    return {"name": "教师个人科研查询器", "version": "0.2.0", "status": "running"}


@app.get("/api/health")
def health():
    try:
        engine = get_engine()
        engine.conn.ping()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/metrics")
def list_metrics(category: Optional[str] = None):
    """列出所有可用指标（指标超市接口）"""
    engine = get_engine()
    try:
        all_metrics = engine.list_metrics()
        if category:
            all_metrics = [m for m in all_metrics if m["category"] == category]
        return {
            "total": len(all_metrics),
            "categories": engine.list_categories(),
            "metrics": all_metrics,
        }
    finally:
        engine.close()


@app.get("/api/teacher/{teacher_id}")
def get_teacher_info(teacher_id: str):
    """获取教师基本信息"""
    engine = get_engine()
    try:
        info = engine.get_teacher_info(teacher_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"教师 {teacher_id} 不存在")
        return info
    finally:
        engine.close()


@app.get("/api/teacher/{teacher_id}/overview", response_model=TeacherOverview)
def get_teacher_overview(
    teacher_id: str,
    start_date: str = "2022-01-01",
    end_date: str = "2025-12-31",
    metric_ids: Optional[str] = None,  # 逗号分隔：project_count_leader,fund_total_arrived,...
):
    """
    教师科研全景查询 — 核心接口

    参数：
    - teacher_id: 工号，如 GH20200001
    - start_date / end_date: 时间范围
    - metric_ids: 可选，指定要查哪些指标（逗号分隔），不传则返回全部
    """
    engine = get_engine()
    try:
        # 查教师信息
        teacher = engine.get_teacher_info(teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail=f"教师 {teacher_id} 不存在")

        # 解析要查的指标
        mid_list = None
        if metric_ids:
            mid_list = [m.strip() for m in metric_ids.split(",")]

        # 执行查询
        results = engine.execute(teacher_id, mid_list, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        # 组装结果
        metrics = []
        cat_summary = {}
        for r in results:
            mv = MetricValue(
                metric_id=r.metric_id,
                name=r.name,
                category=r.category,
                chart_type=r.chart_type,
                unit=r.unit,
                value=r.value,
                rows=r.rows,
                error=r.error,
            )
            metrics.append(mv)

            # 按模块统计
            if r.category not in cat_summary:
                cat_summary[r.category] = {"total": 0, "success": 0}
            cat_summary[r.category]["total"] += 1
            if r.success:
                cat_summary[r.category]["success"] += 1

        return TeacherOverview(
            teacher=teacher,
            metrics=metrics,
            category_summary=cat_summary,
        )

    finally:
        engine.close()


@app.get("/api/teacher/{teacher_id}/report", response_class=HTMLResponse)
def get_teacher_report(
    teacher_id: str,
    start_date: str = "2022-01-01",
    end_date: str = "2025-12-31",
    query: Optional[str] = None,
    metric_ids: Optional[str] = None,   # v1.0: 逗号分隔的指标ID
):
    """
    教师科研大屏报告 — 直接返回 HTML 页面
    浏览器打开即可看到完整大屏
    """
    engine = MetricEngine(DB_CONFIG)
    router = IntentRouter(llm=get_llm())
    insight_engine = InsightEngine(llm=get_llm())
    composer = DashboardComposer()

    try:
        teacher = engine.get_teacher_info(teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail=f"教师 {teacher_id} 不存在")

        # 优先使用 URL 指定的指标，其次用意图路由推荐
        intent = None
        if metric_ids:
            mid_list = [m.strip() for m in metric_ids.split(",")]
        else:
            intent = router.route(query or "我的科研情况")
            mid_list = intent.recommended_metrics

        results = engine.execute(teacher_id, mid_list, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        summary = {r.metric_id: r.value or len(r.rows) for r in results if r.success}
        insights = insight_engine.generate(teacher, summary, start_date, end_date)

        # v1.0: 根据意图选择大屏布局
        from dashboard_layouts import get_layout
        intent_name = intent.intent if intent else "personal_overview"
        layout = get_layout(intent_name)

        html = composer.render(teacher, results, insights, start_date, end_date, layout=layout)
        return HTMLResponse(content=html)

    finally:
        engine.close()


@app.get("/api/teacher/{teacher_id}/chat")
def chat_query(
    teacher_id: str,
    q: str = Query(..., description="自然语言问题"),
    start_date: str = "2022-01-01",
    end_date: str = "2025-12-31",
):
    """
    旧版对话式查询 — 输入自然语言，返回 JSON（供前端 Chat UI 调用）
    无状态模式，每次调用独立。
    新版请使用 POST /api/chat/send（支持多轮对话）
    """
    engine = MetricEngine(DB_CONFIG)
    router = IntentRouter(llm=get_llm())
    insight_engine = InsightEngine(llm=get_llm())

    try:
        teacher = engine.get_teacher_info(teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail=f"教师 {teacher_id} 不存在")

        intent = router.route(q)
        results = engine.execute(teacher_id, intent.recommended_metrics, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        summary = {r.metric_id: r.value or len(r.rows) for r in results if r.success}
        insights = insight_engine.generate(teacher, summary, start_date, end_date)

        return {
            "teacher": teacher,
            "intent": {"type": intent.intent, "confidence": intent.confidence},
            "metrics": [
                {"metric_id": r.metric_id, "name": r.name,
                 "category": r.category, "chart_type": r.chart_type,
                 "unit": r.unit, "value": r.value, "rows": r.rows}
                for r in results if r.success
            ],
            "insights": insights,
        }

    finally:
        engine.close()


# ── v0.4: 多轮对话 API ──

@app.post("/api/chat/send", response_model=ChatResponse)
def chat_send(req: ChatRequest):
    """
    多轮对话入口 — 发送消息，获取 AI 回复。

    请求：
    ```json
    {
        "message": "那论文情况呢？",
        "session_id": "abc123",     // 可选：继续已有会话
        "teacher_id": "GH20200001"  // 首次对话时必须提供
    }
    ```

    首次对话流程：
    1. 用户提供 teacher_id → 系统创建 session → 执行意图路由 → 返回数据

    追问流程：
    2. 用户只发消息 + session_id → 系统检测追问 → 继承上下文 → 自动关联教师和时间范围
    """
    memory = get_memory()
    engine = MetricEngine(DB_CONFIG)
    router = IntentRouter(llm=get_llm())
    insight_engine = InsightEngine(llm=get_llm())

    try:
        session_id = req.session_id
        teacher_id = req.teacher_id
        teacher_info = None

        # ── Step 1: 解析会话上下文 ──
        if session_id:
            session = memory.get(session_id)
            if session:
                teacher_id = session.teacher_id
                teacher_info = session.teacher_info

        if not teacher_id:
            raise HTTPException(
                status_code=400,
                detail="首次对话需要提供 teacher_id 字段"
            )

        # 获取教师信息
        if not teacher_info:
            teacher_info = engine.get_teacher_info(teacher_id)
            if not teacher_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"教师 {teacher_id} 不存在"
                )

        # 创建或获取会话
        session = memory.get_or_create(
            teacher_id=teacher_id,
            teacher_info=teacher_info,
            session_id=session_id,
        )

        # ── Step 2: 意图识别 ──
        context = memory.build_context(session.session_id, req.message)
        intent = router.route_with_context(req.message, context=context)

        # ── Step 2.5: 闲聊/问候直接返回 ──
        if intent.intent == "chitchat":
            memory.add_turn(session.session_id, role="user", content=req.message, intent="chitchat")
            reply = _build_chitchat_reply(req.message, teacher_info)
            memory.add_turn(session.session_id, role="assistant", content=reply, intent="chitchat")
            return ChatResponse(
                session_id=session.session_id,
                reply=reply,
                intent="chitchat",
                is_followup=context.get("is_followup", False),
                metrics=[],
                insights=[],
                teacher=teacher_info,
                metric_ids=[],
            )

        # ── Step 3: 执行指标查询 ──
        start_date, end_date = session.time_range
        results = engine.execute(teacher_id, intent.recommended_metrics, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        summary = {r.metric_id: r.value or len(r.rows) for r in results if r.success}
        insights = insight_engine.generate(teacher_info, summary, start_date, end_date)

        # ── Step 4: 记录对话轮次 ──
        memory.add_turn(
            session.session_id,
            role="user",
            content=req.message,
            intent=intent.intent,
        )
        memory.add_turn(
            session.session_id,
            role="assistant",
            content=f"查询了{intent.intent}，返回 {len([r for r in results if r.success])} 个指标",
            intent=intent.intent,
            metric_ids=intent.recommended_metrics,
        )

        # ── Step 5: 生成自然语言回复 ──
        reply = _build_natural_reply(
            teacher_info, intent, results, insights, context.get("is_followup", False)
        )

        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            intent=intent.intent,
            is_followup=context.get("is_followup", False),
            metrics=[
                {"metric_id": r.metric_id, "name": r.name,
                 "category": r.category, "chart_type": r.chart_type,
                 "unit": r.unit, "value": r.value, "rows": r.rows}
                for r in results if r.success
            ],
            insights=insights,
            teacher=teacher_info,
            metric_ids=intent.recommended_metrics,
        )

    finally:
        engine.close()


@app.get("/api/chat/sessions")
def list_sessions():
    """列出当前活跃会话数（调试用）"""
    memory = get_memory()
    memory.cleanup_expired()
    return {"active_sessions": memory.active_count}


@app.get("/api/chat/debug/{session_id}")
def debug_session(session_id: str, test_input: str = None):
    """调试端点：查看会话内部状态 + 追问检测"""
    memory = get_memory()
    s = memory.get(session_id)
    if not s:
        return {"error": "session not found"}
    result = {
        "session_id": s.session_id,
        "teacher_id": s.teacher_id,
        "time_range": s.time_range,
        "history_count": len(s.history),
        "history": [
            {"role": t.role, "content": t.content[:60],
             "intent": t.intent, "metric_count": len(t.metric_ids)}
            for t in s.history
        ],
        "last_intent": s.last_user_intent,
        "last_metric_ids": s.last_metric_ids,
    }
    if test_input:
        result["is_followup"] = memory.is_followup(session_id, test_input)
        result["inferred_intent"] = memory.infer_followup_intent(session_id, test_input)
        ctx = memory.build_context(session_id, test_input)
        result["context"] = {
            "is_followup": ctx.get("is_followup"),
            "suggested_intent": ctx.get("suggested_intent"),
        }
    return result


# ── v0.4: 场景模板 API ──

class ScenarioRequest(BaseModel):
    scenario_id: str                                   # annual_summary / title_evaluation / grant_application
    teacher_id: str
    start_date: str = "2022-01-01"
    end_date: str = "2025-12-31"


@app.get("/api/scenarios")
def list_scenarios():
    """列出所有可用场景模板"""
    engine = ScenarioEngine()
    return {
        "total": len(engine.TEMPLATES),
        "scenarios": engine.list_templates(),
    }


@app.post("/api/chat/scenario")
def run_scenario(req: ScenarioRequest):
    """
    执行场景模板 — 一键生成场景化报告

    请求：
    ```json
    {
        "scenario_id": "annual_summary",
        "teacher_id": "GH20200001",
        "start_date": "2022-01-01",
        "end_date": "2025-12-31"
    }
    ```

    返回：指标数据 + AI洞察 + LLM叙事文案（Markdown格式）
    """
    engine = MetricEngine(DB_CONFIG)
    scenario_engine = ScenarioEngine(llm=get_llm())

    try:
        result = scenario_engine.execute(
            teacher_id=req.teacher_id,
            scenario_id=req.scenario_id,
            metric_engine=engine,
            custom_time_range=(req.start_date, req.end_date) if req.start_date else None,
        )

        return {
            "scenario": {
                "id": result.scenario_id,
                "name": result.scenario_name,
            },
            "teacher": result.teacher,
            "time_range": list(result.time_range),
            "metrics": [
                {"metric_id": r.metric_id, "name": r.name,
                 "category": r.category, "chart_type": r.chart_type,
                 "unit": r.unit, "value": r.value, "rows": r.rows}
                for r in result.metrics if r.success
            ],
            "insights": result.insights,
            "narrative": result.narrative,
        }

    finally:
        engine.close()


# ── v0.4: 模板存储 API ──

class TemplateSaveRequest(BaseModel):
    teacher_id: str
    name: str
    metric_ids: list[str]
    time_range_start: str = "2022-01-01"
    time_range_end: str = "2025-12-31"


class TemplateRenameRequest(BaseModel):
    name: str


@app.get("/api/templates/{teacher_id}")
def list_templates(teacher_id: str):
    """列出某教师的所有保存模板"""
    store = TemplateStore()
    templates = store.list_by_teacher(teacher_id)
    return {
        "total": len(templates),
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "metric_count": len(t.metric_ids),
                "metric_ids": t.metric_ids,
                "time_range_start": t.time_range_start,
                "time_range_end": t.time_range_end,
                "created_at": t.created_at,
            }
            for t in templates
        ],
    }


@app.post("/api/templates/save")
def save_template(req: TemplateSaveRequest):
    """保存自定义模板"""
    store = TemplateStore()
    tid = store.save(
        teacher_id=req.teacher_id,
        name=req.name,
        metric_ids=req.metric_ids,
        time_range_start=req.time_range_start,
        time_range_end=req.time_range_end,
    )
    return {"id": tid, "message": f"模板「{req.name}」已保存"}


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int):
    """删除模板"""
    store = TemplateStore()
    if store.delete(template_id):
        return {"message": "已删除"}
    raise HTTPException(status_code=404, detail="模板不存在")


@app.patch("/api/templates/{template_id}")
def rename_template(template_id: int, req: TemplateRenameRequest):
    """重命名模板"""
    store = TemplateStore()
    if store.rename(template_id, req.name):
        return {"message": f"已重命名为「{req.name}」"}
    raise HTTPException(status_code=404, detail="模板不存在")


# ── v0.4: 指标自动发现 API ──

class DiscoverRequest(BaseModel):
    question: str
    teacher_id: str


@app.post("/api/chat/discover")
def discover_metric(req: DiscoverRequest):
    """
    指标自动发现 — 当注册表中没有匹配指标时，自动探索 Schema 生成 SQL。

    请求：
    ```json
    {
        "question": "查一下论文的被引次数分布",
        "teacher_id": "GH20200001"
    }
    ```
    """
    discovery = MetricDiscovery(llm=get_llm())
    result = discovery.discover(
        user_question=req.question,
        db_config=DB_CONFIG,
        teacher_id=req.teacher_id,
    )

    if result.error and not result.sql:
        raise HTTPException(status_code=400, detail=result.error)

    # 执行 SQL 获取数据
    rows = []
    if result.sql and not result.error:
        try:
            import pymysql
            conn = pymysql.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                cursor.execute(result.sql)
                rows_raw = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                rows = [dict(zip(cols, row)) for row in rows_raw]
            conn.close()
        except Exception as e:
            result.error = str(e)

    return {
        "name": result.name,
        "sql": result.sql,
        "chart_type": result.chart_type,
        "explanation": result.explanation,
        "tables_used": result.tables_used,
        "rows": rows,
        "row_count": len(rows),
        "error": result.error,
    }


# ── v1.0: JWT 认证 ──

class LoginRequest(BaseModel):
    teacher_id: str
    password: str


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """教师登录 → 返回 JWT token"""
    auth = AuthManager()
    result = auth.login(req.teacher_id, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="工号或密码错误")
    return result


@app.post("/api/auth/sync")
def sync_users():
    """从 MySQL 同步教师账号（初始密码 = 工号后 6 位）"""
    auth = AuthManager()
    count = auth.sync_teachers(DB_CONFIG)
    return {"message": f"已同步 {count} 个教师账号", "count": count}


@app.get("/api/auth/me")
def get_me(user=Depends(get_current_user)):
    """获取当前登录用户信息（需 JWT）"""
    return {"teacher_id": user.teacher_id, "name": user.name, "role": user.role}


# ── v1.0: 导出 ──

class ExportRequest(BaseModel):
    teacher_id: str
    format: str = "pptx"
    scenario_id: str = "annual_summary"
    start_date: str = "2022-01-01"
    end_date: str = "2025-12-31"


@app.post("/api/export")
def export_report(req: ExportRequest):
    """导出科研报告为 PPT 或 Markdown"""
    from scenario_templates import ScenarioEngine
    from dashboard.export import ReportExporter
    from fastapi.responses import FileResponse

    engine = MetricEngine(DB_CONFIG)
    scenario_engine = ScenarioEngine(llm=get_llm())

    try:
        result = scenario_engine.execute(
            teacher_id=req.teacher_id,
            scenario_id=req.scenario_id,
            metric_engine=engine,
            custom_time_range=(req.start_date, req.end_date),
        )

        metrics = [
            {"metric_id": r.metric_id, "name": r.name,
             "category": r.category, "chart_type": r.chart_type,
             "unit": r.unit, "value": r.value, "rows": r.rows}
            for r in result.metrics if r.success
        ]

        if req.format == "pptx":
            path = ReportExporter.to_pptx(
                teacher=result.teacher,
                metrics=metrics,
                insights=result.insights,
                narrative=result.narrative,
                scenario_name=result.scenario_name,
                time_range=result.time_range,
            )
            return FileResponse(path, filename=Path(path).name,
                      media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        else:
            path = ReportExporter.to_markdown(
                teacher=result.teacher,
                metrics=metrics,
                insights=result.insights,
                narrative=result.narrative,
                scenario_name=result.scenario_name,
            )
            return FileResponse(path, filename=Path(path).name,
                      media_type="text/markdown; charset=utf-8")

    finally:
        engine.close()


# ── v1.0: 超管后台 API ──

@app.get("/api/admin/stats")
def admin_stats(user=Depends(get_current_user)):
    """超管仪表盘数据"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    engine = MetricEngine(DB_CONFIG)
    try:
        with engine.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM t_jzg_jbxx")
            teachers = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM t_ky_xmjbxx")
            projects = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM t_ky_lw")
            papers = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM t_ky_zl")
            patents = cursor.fetchone()[0]

            # 各学院统计
            cursor.execute("SELECT dw_mc, COUNT(*) as cnt FROM t_jzg_jbxx GROUP BY dw_mc ORDER BY cnt DESC")
            depts = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

        memory = get_memory()
        return {
            "stats": {
                "teachers": teachers,
                "projects": projects,
                "papers": papers,
                "patents": patents,
                "active_sessions": memory.active_count,
            },
            "departments": depts,
            "db_status": "connected",
        }
    except Exception as e:
        return {"error": str(e), "db_status": "disconnected"}
    finally:
        engine.close()


@app.get("/api/admin/users")
def admin_users(user=Depends(get_current_user)):
    """列出所有用户"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    from agent.auth import AuthManager
    auth = AuthManager()
    try:
        with auth._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, teacher_id, name, role, department, created_at FROM users ORDER BY id"
            ).fetchall()
        return {
            "total": len(rows),
            "users": [
                {"id": r[0], "teacher_id": r[1], "name": r[2],
                 "role": r[3], "department": r[4], "created_at": r[5]}
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e), "users": []}


@app.get("/api/admin/datasource")
def admin_datasource(user=Depends(get_current_user)):
    """数据源状态"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        import pymysql
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM t_jzg_jbxx")
            teacher_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) as cnt FROM t_ky_xmjbxx")
            project_count = cursor.fetchone()[0]
        conn.close()

        return {
            "status": "connected",
            "host": DB_CONFIG["host"],
            "port": DB_CONFIG["port"],
            "database": DB_CONFIG["database"],
            "tables": {
                "teachers": teacher_count,
                "projects": project_count,
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/sync")
def admin_sync(user=Depends(get_current_user)):
    """触发教师账号同步"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    from agent.auth import AuthManager
    auth = AuthManager()
    count = auth.sync_teachers(DB_CONFIG)
    return {"message": f"已同步 {count} 个教师账号", "count": count}


# ── v1.0: 自定义指标管理 ──

class MetricSaveRequest(BaseModel):
    metric_id: str
    name: str
    sql_template: str
    category: str = "自定义"
    chart_type: str = "table"
    unit: str = ""
    description: str = ""


@app.get("/api/admin/metrics")
def admin_list_metrics(user=Depends(get_current_user)):
    """列出所有指标（内置 + 自定义），合并去重"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    from metric_manager import MetricManager
    import yaml
    from pathlib import Path

    # 加载内置指标
    builtin = {}
    metrics_path = Path(__file__).parent.parent / "agent" / "metrics.yaml"
    with open(metrics_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    for m in config["metrics"]:
        builtin[m["id"]] = {
            "metric_id": m["id"],
            "name": m["name"],
            "category": m.get("category", ""),
            "chart_type": m.get("chart_type", "table"),
            "unit": m.get("unit", ""),
            "sql_template": m.get("sql_template", ""),
            "description": m.get("description", ""),
            "source": "内置",
        }

    # 加载自定义指标（覆盖同ID的内置指标）
    mgr = MetricManager()
    custom = mgr.list_all()
    for c in custom:
        c["source"] = "自定义"
        c["sql_template"] = c.get("sql_template", "")[:80] + "..."
        builtin[c["metric_id"]] = c  # 自定义覆盖内置

    # 按分类排序
    metrics_list = sorted(builtin.values(), key=lambda x: (x["category"], x["name"]))
    return {"total": len(metrics_list), "metrics": metrics_list}


@app.post("/api/admin/metrics")
def admin_save_metric(req: MetricSaveRequest, user=Depends(get_current_user)):
    """新增/更新自定义指标"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    from metric_manager import MetricManager
    mgr = MetricManager()
    mid = mgr.save(req.metric_id, req.name, req.sql_template,
                   req.category, req.chart_type, req.unit, req.description)
    return {"id": mid, "message": f"指标「{req.name}」已保存"}


@app.delete("/api/admin/metrics/{metric_id}")
def admin_delete_metric(metric_id: str, user=Depends(get_current_user)):
    """删除自定义指标"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    from metric_manager import MetricManager
    mgr = MetricManager()
    if mgr.delete(metric_id):
        return {"message": "已删除"}
    raise HTTPException(status_code=404, detail="指标不存在")


# ── v1.0: AI 辅助生成指标 ──

class MetricSuggestRequest(BaseModel):
    description: str    # 自然语言描述，如"统计教师的教材出版数量"


@app.post("/api/admin/metrics/suggest")
def admin_suggest_metric(req: MetricSuggestRequest, user=Depends(get_current_user)):
    """
    AI 辅助生成指标：用户输入自然语言 → LLM 分析 Schema → 自动填表/SQL/分类。

    返回完整的指标定义，用户确认后调用 POST /api/admin/metrics 保存。
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM 未连接")

    from metric_discovery import SchemaExplorer
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from pydantic import BaseModel as PydanticBase

    class MetricSuggestion(PydanticBase):
        metric_id: str = ""       # 英文ID，如 book_textbook_count
        name: str = ""            # 中文名称，如"教材出版数量"
        category: str = "自定义"   # 分类
        chart_type: str = "kpi_card"
        unit: str = ""
        sql_template: str = ""
        description: str = ""
        explanation: str = ""     # LLM 对推理过程的解释

    parser = PydanticOutputParser(pydantic_object=MetricSuggestion)
    explorer = SchemaExplorer()
    schema_text = explorer.get_schema_summary()

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一位数据库专家，帮助管理员为教师科研系统创建新指标。\n\n"
            "数据库 Schema（MySQL 8.0，utf8mb4）：\n"
            "{schema}\n\n"
            "规则：\n"
            "1. 只生成 SELECT 语句，参数用 :teacher_id :start_date :end_date\n"
            "2. 教师工号在 t_jzg_jbxx.gh，通过各表的 ry_gh / zzgh / fmr_gh 等字段关联\n"
            "3. metric_id 用英文小写+下划线，如 book_textbook_count\n"
            "4. chart_type：kpi_card(单值)|pie_chart(占比)|bar_chart(对比)|line_chart(趋势)|horizontal_bar(横向)|table(列表)\n"
            "5. 使用 DATE_FORMAT() 处理日期\n\n"
            "{format_instructions}"
        )),
        ("human", "用户需求：{description}")
    ])

    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "description": req.description,
            "schema": schema_text,
            "format_instructions": parser.get_format_instructions(),
        })

        # 简单 SQL 校验
        sql_upper = result.sql_template.strip().upper()
        if not sql_upper.startswith("SELECT"):
            result.sql_template = "SELECT * FROM t_jzg_jbxx LIMIT 1"

        return {
            "metric_id": result.metric_id,
            "name": result.name,
            "category": result.category,
            "chart_type": result.chart_type,
            "unit": result.unit,
            "sql_template": result.sql_template,
            "description": result.description,
            "explanation": result.explanation,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 生成失败: {str(e)}")


@app.get("/api/admin", response_class=HTMLResponse)
def admin_page():
    """超管后台页面"""
    template_path = Path(__file__).parent.parent / "dashboard" / "templates" / "admin.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


@app.get("/api/chat", response_class=HTMLResponse)
def chat_page():
    """聊天对话界面"""
    template_path = Path(__file__).parent.parent / "dashboard" / "templates" / "chat.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


# ── 自然语言回复构建 ──

def _build_chitchat_reply(message: str, teacher: dict) -> str:
    """构建闲聊/问候回复"""
    text = message.lower()
    name = teacher.get("xm", "老师") if teacher else "老师"

    if any(kw in text for kw in ["你好", "您好", "哈喽", "hi", "hello", "早上好", "下午好", "晚上好"]):
        return f"{name}老师好！我是您的科研助手，可以帮您查询科研数据、生成年度总结或职称评审材料。请问有什么可以帮您？"
    if any(kw in text for kw in ["谢谢", "感谢"]):
        return "不客气！有任何科研相关问题随时问我。"
    if any(kw in text for kw in ["再见", "拜拜", "bye"]):
        return "再见！有需要随时回来找我。"
    if any(kw in text for kw in ["你是谁", "你能做什么", "介绍一下", "干嘛的", "能做什么"]):
        return ("我是教师科研助手，专门帮助您查询和分析个人科研数据。\n"
                "我可以：\n· 查看科研全景、论文、经费、项目、专利等数据\n"
                "· 生成年度科研总结\n· 生成职称评审材料\n"
                "· 探索新的科研指标\n· 导出 PPT 或 Markdown 报告")
    if any(kw in text for kw in ["在吗", "在不在", "忙吗"]):
        return "在的，随时为您服务。请直接说出您想查询的科研数据。"
    if any(kw in text for kw in ["吃了吗", "怎么样", "最近好吗", "最近如何"]):
        return "谢谢关心！我随时准备好帮您分析科研数据。今天想查点什么？"

    return f"{name}老师，我理解了。如果有科研相关的问题，请随时告诉我。"


def _format_money(v: float) -> str:
    """金额格式化：1.2万 / 12.3万 / 1234.5"""
    if v is None or v == 0:
        return "0元"
    if abs(v) >= 10000:
        return f"{v/10000:.1f}万元"
    return f"{int(v)}元"


def _format_yearly_trend(rows: list) -> str:
    """从年度趋势图表的 rows 提取关键年份信息"""
    if not rows:
        return ""
    items = []
    for r in rows[:5]:
        label = r.get("label", "")
        value = r.get("value", 0)
        if isinstance(value, (int, float)):
            items.append(f"{label}年{value}个")
    if not items:
        return ""
    return "、".join(items)


def _format_top_distribution(rows: list, n: int = 3) -> str:
    """从分布图表的 rows 提取 Top N 类别"""
    if not rows:
        return ""
    sorted_rows = sorted(rows, key=lambda r: r.get("value", 0), reverse=True)[:n]
    parts = []
    for r in sorted_rows:
        label = r.get("label", "")
        value = r.get("value", 0)
        if isinstance(value, (int, float)):
            parts.append(f"{label} {value}个")
    return "、".join(parts)


def _build_natural_reply(
    teacher: dict,
    intent_result,
    results: list,
    insights: list[str],
    is_followup: bool,
) -> str:
    """根据意图和查询结果生成简短的自然语言回复"""
    name = teacher.get("xm", "老师")
    intent = intent_result.intent if hasattr(intent_result, 'intent') else str(intent_result)

    # 获取所有指标数据（按 metric_id 索引）
    all_results = {r.metric_id: r for r in results if r.success}
    kpi_values = {mid: r.value for mid, r in all_results.items() if r.chart_type == "kpi_card"}
    chart_rows = {mid: r.rows for mid, r in all_results.items() if r.chart_type != "kpi_card" and r.rows}

    # 通用项目回复
    project_count_leader = int(kpi_values.get("project_count_leader", 0) or 0)
    project_count_total = int(kpi_values.get("project_count_total", 0) or 0)
    project_yearly = chart_rows.get("project_yearly_trend", [])
    project_by_level = chart_rows.get("project_by_level", [])
    project_status = chart_rows.get("project_status_distribution", [])
    project_by_source = chart_rows.get("project_by_source", [])
    project_rank_dept = kpi_values.get("project_rank_dept")

    # 经费
    fund_total_arrived = float(kpi_values.get("fund_total_arrived", 0) or 0)
    fund_total_spent = float(kpi_values.get("fund_total_spent", 0) or 0)
    fund_execution_rate = float(kpi_values.get("fund_execution_rate", 0) or 0)
    fund_monthly = chart_rows.get("fund_monthly_trend", [])
    fund_yearly_inout = chart_rows.get("fund_yearly_inout", [])

    # 论文
    paper_count_total = int(kpi_values.get("paper_count_total", 0) or 0)
    paper_first_author = int(kpi_values.get("paper_first_author_count", 0) or 0)
    paper_yearly = chart_rows.get("paper_yearly_trend", [])
    paper_by_level = chart_rows.get("paper_by_level", [])
    paper_rank_dept = kpi_values.get("paper_rank_dept")

    # 专利
    patent_count = int(kpi_values.get("patent_count", 0) or 0)
    patent_by_type = chart_rows.get("patent_by_type", [])

    # 获奖
    award_count = int(kpi_values.get("award_count", 0) or 0)
    award_by_level = chart_rows.get("award_by_level", [])

    # 著作
    book_count = int(kpi_values.get("book_count", 0) or 0)
    book_by_type = chart_rows.get("book_by_type", [])

    # 软著
    software_count = int(kpi_values.get("software_count", 0) or 0)

    # 会议
    conference_hosted = int(kpi_values.get("conference_hosted", 0) or 0)

    intent_replies = {
        "personal_overview": (
            f"{name}老师好！这是您的个人科研全景：\n\n"
            f"【项目情况】\n"
            f"· 主持 {project_count_leader} 个"
            f"（共参与 {project_count_total} 个）"
            f"{'，学院排名第 ' + str(int(project_rank_dept)) + ' 名' if project_rank_dept else ''}\n"
            f"· 年度趋势：{_format_yearly_trend(project_yearly) or '暂无数据'}\n"
            f"· 级别分布：{_format_top_distribution(project_by_level) or '暂无数据'}\n\n"
            f"【经费情况】\n"
            f"· 到账总额 {_format_money(fund_total_arrived)}，"
            f"支出 {_format_money(fund_total_spent)}，"
            f"执行率 {fund_execution_rate:.1f}%\n\n"
            f"【成果情况】\n"
            f"· 论文 {paper_count_total} 篇（一作 {paper_first_author} 篇）"
            f"{'，学院排名第 ' + str(int(paper_rank_dept)) + ' 名' if paper_rank_dept else ''}\n"
            f"· 专利 {patent_count} 项 | 著作 {book_count} 部 | 软著 {software_count} 项\n"
            f"· 获奖 {award_count} 项 | 学术会议 {conference_hosted} 次"
        ),
        "funding_detail": (
            f"{name}老师的科研经费概况：\n\n"
            f"【核心指标】\n"
            f"· 到账总额：{_format_money(fund_total_arrived)}\n"
            f"· 支出总额：{_format_money(fund_total_spent)}\n"
            f"· 经费执行率：{fund_execution_rate:.1f}%\n"
            f"· 净余额：{_format_money(fund_total_arrived - fund_total_spent)}\n\n"
            f"【月度趋势（最近月份）】\n"
            f"· {_format_yearly_trend(fund_monthly) or '暂无数据'}\n\n"
            f"【年度收支对比】\n"
            f"· {_format_yearly_trend(fund_yearly_inout) or '暂无数据'}"
        ),
        "paper_analysis": (
            f"{name}老师的论文成果：\n\n"
            f"【核心数据】\n"
            f"· 共发表 {paper_count_total} 篇\n"
            f"· 一作 {paper_first_author} 篇（占比 {paper_count_total and paper_first_author*100//paper_count_total}%）\n"
            f"{'· 学院排名：第 ' + str(int(paper_rank_dept)) + ' 名' if paper_rank_dept else ''}\n\n"
            f"【年度趋势】\n"
            f"· {_format_yearly_trend(paper_yearly) or '暂无数据'}\n\n"
            f"【级别分布】\n"
            f"· {_format_top_distribution(paper_by_level) or '暂无数据'}"
        ),
        "patent_analysis": (
            f"{name}老师的专利成果：\n\n"
            f"· 专利总数：{patent_count} 项\n"
            f"· 类型分布：{_format_top_distribution(patent_by_type) or '暂无数据'}"
        ),
        "project_query": (
            f"{name}老师的科研项目情况：\n\n"
            f"【项目数量】\n"
            f"· 主持项目：{project_count_leader} 个\n"
            f"· 参与项目：{project_count_total} 个（主持占比 {project_count_total and project_count_leader*100//project_count_total}%）\n"
            f"{'· 学院排名：第 ' + str(int(project_rank_dept)) + ' 名' if project_rank_dept else ''}\n\n"
            f"【年度立项趋势】\n"
            f"· {_format_yearly_trend(project_yearly) or '暂无数据'}\n\n"
            f"【项目级别分布】\n"
            f"· {_format_top_distribution(project_by_level) or '暂无数据'}\n\n"
            f"【项目状态】\n"
            f"· {_format_top_distribution(project_status) or '暂无数据'}\n\n"
            f"【项目来源】\n"
            f"· {_format_top_distribution(project_by_source) or '暂无数据'}"
        ),
        "award_query": (
            f"{name}老师的获奖情况：\n\n"
            f"· 获奖总数：{award_count} 项\n"
            f"· 级别分布：{_format_top_distribution(award_by_level) or '暂无数据'}"
        ),
        "book_analysis": (
            f"{name}老师的著作情况：\n\n"
            f"· 著作总数：{book_count} 部\n"
            f"· 类别分布：{_format_top_distribution(book_by_type) or '暂无数据'}"
        ),
        "software_analysis": (
            f"{name}老师的软著情况：\n\n"
            f"· 软著总数：{software_count} 项"
        ),
        "conference_analysis": (
            f"{name}老师的学术活动：\n\n"
            f"· 主持学术会议 {conference_hosted} 次\n"
            f"· 详情见下方图表"
        ),
        "annual_summary": (
            f"{name}老师的年度科研总结已生成，包含：\n"
            f"· 整体指标 {len([r for r in results if r.success])} 项\n"
            f"· 含 {sum(1 for r in results if r.success and r.chart_type=='kpi_card')} 张 KPI 卡片"
        ),
        "title_evaluation": (
            f"{name}老师的职称评审材料已汇总：\n"
            f"· 整体指标 {len([r for r in results if r.success])} 项\n"
            f"· 含 {sum(1 for r in results if r.success and r.chart_type=='kpi_card')} 张 KPI 卡片"
        ),
    }

    base = intent_replies.get(intent, f"{name}老师，查询完成，共返回 {len([r for r in results if r.success])} 项指标。")

    # AI 洞察由前端独立渲染（避免重复），此处不再拼接到 reply

    # 追问时加提示
    if is_followup:
        base += "\n\n_您可以继续追问，比如「那经费呢？」「只看2024年的」等。_"

    return base
