"""FastAPI 服务层 — 教师科研查询 API"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
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
    version="0.3.0",
    description="输入教师工号，返回个人科研全景数据"
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
    """对话式查询 — 输入自然语言，返回 JSON（供前端 Chat UI 调用）"""
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
