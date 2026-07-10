"""FastAPI 服务层 — 教师科研查询 API"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

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

# ── 数据库配置 ──
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "tr_user",
    "password": "tr_pass_2025",
    "database": "teacher_research",
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

        intent = router.route(query or "我的科研情况")
        results = engine.execute(teacher_id, intent.recommended_metrics, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        summary = {r.metric_id: r.value or len(r.rows) for r in results if r.success}
        insights = insight_engine.generate(teacher, summary, start_date, end_date)

        html = composer.render(teacher, results, insights, start_date, end_date)
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


@app.get("/api/chat", response_class=HTMLResponse)
def chat_page():
    """聊天对话界面"""
    template_path = Path(__file__).parent.parent / "dashboard" / "templates" / "chat.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


# ── 自然语言回复构建 ──

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

    # 获取 KPI 值
    kpi_values = {}
    for r in results:
        if r.success and r.chart_type == "kpi_card":
            kpi_values[r.metric_id] = r.value

    intent_replies = {
        "personal_overview": (
            f"{name}老师好！这是您的个人科研全景：\n"
            f"· 主持项目 {int(kpi_values.get('project_count_leader', 0))} 个"
            f"（共参与 {int(kpi_values.get('project_count_total', 0))} 个）\n"
            f"· 到账经费 {kpi_values.get('fund_total_arrived', 0):.0f} 元\n"
            f"· 发表论文 {int(kpi_values.get('paper_count_total', 0))} 篇"
            f"（一作 {int(kpi_values.get('paper_first_author_count', 0))} 篇）\n"
            f"· 专利 {int(kpi_values.get('patent_count', 0))} 项"
            f" | 著作 {int(kpi_values.get('book_count', 0))} 部"
            f" | 软著 {int(kpi_values.get('software_count', 0))} 项\n"
            f"· 获奖 {int(kpi_values.get('award_count', 0))} 项"
            f" | 学术会议 {int(kpi_values.get('conference_hosted', 0))} 次"
        ),
        "funding_detail": (
            f"{name}老师的科研经费概况：\n"
            f"· 到账总额 {kpi_values.get('fund_total_arrived', 0):.0f} 元\n"
            f"· 支出总额 {kpi_values.get('fund_total_spent', 0):.0f} 元\n"
            f"· 经费执行率 {kpi_values.get('fund_execution_rate', 0):.1f}%"
        ),
        "paper_analysis": (
            f"{name}老师的论文成果：\n"
            f"· 共发表 {int(kpi_values.get('paper_count_total', 0))} 篇"
            f"（一作 {int(kpi_values.get('paper_first_author_count', 0))} 篇）"
        ),
        "patent_analysis": (
            f"{name}老师的专利成果：共 {int(kpi_values.get('patent_count', 0))} 项"
        ),
        "project_query": (
            f"{name}老师的科研项目："
            f"主持 {int(kpi_values.get('project_count_leader', 0))} 个，"
            f"共参与 {int(kpi_values.get('project_count_total', 0))} 个"
        ),
        "award_query": (
            f"{name}老师的获奖情况：共 {int(kpi_values.get('award_count', 0))} 项"
        ),
        "book_analysis": (
            f"{name}老师的著作：共 {int(kpi_values.get('book_count', 0))} 部"
        ),
        "software_analysis": (
            f"{name}老师的软著：共 {int(kpi_values.get('software_count', 0))} 项"
        ),
        "conference_analysis": (
            f"{name}老师的学术活动：参与学术会议 {int(kpi_values.get('conference_hosted', 0))} 次"
        ),
        "annual_summary": (
            f"{name}老师的年度科研总结已生成。"
        ),
        "title_evaluation": (
            f"{name}老师的职称评审材料已汇总。"
        ),
    }

    base = intent_replies.get(intent, f"{name}老师，查询完成。")

    # 拼接 AI 洞察
    if insights:
        base += "\n\n💡 **AI 洞察：**\n" + "\n".join(insights)

    # 追问时加提示
    if is_followup:
        base += "\n\n_💬 您可以继续追问，比如「那经费呢？」「只看2024年的」等。_"

    return base
