"""
大屏布局配置 — 不同意图对应固定指标组合 + 图表网格

布局类型：
  A — 科研全景：8 KPI + 2×3 六宫格 + 3 洞察
  B — 论文/经费：2-3 大字KPI + 1×3 三列大图 + 2 洞察
  C — 获奖/专利/项目/著作/软著/会议：1-2 KPI + 1×2 两列 + 1-2 洞察
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DashboardLayout:
    """大屏布局定义"""
    layout_id: str                    # A / B / C
    title_suffix: str                 # 标题后缀，如"论文成果分析"
    kpi_metrics: list[str]            # 顶行 KPI 卡片指标
    chart_metrics: list[str]          # 图表区指标（按顺序排列）
    kpi_class: str = "kpi-8"         # CSS class: kpi-8 / kpi-2 / kpi-3 / kpi-1
    chart_grid: str = "grid-3x2"     # CSS class: grid-3x2 / grid-1x3 / grid-1x2
    insight_count: int = 3           # AI 洞察条数
    chart_height: str = "380px"      # 图表高度


# ── 布局定义 ──

LAYOUTS = {
    # ── 类型 A：科研全景（14 指标）──
    "personal_overview": DashboardLayout(
        layout_id="A",
        title_suffix="个人科研全景",
        kpi_metrics=[
            "project_count_leader", "fund_total_arrived",
            "paper_count_total", "paper_first_author_count",
            "patent_count", "book_count",
            "award_count", "conference_hosted",
        ],
        chart_metrics=[
            "project_by_level", "fund_monthly_trend", "paper_by_level",
            "paper_yearly_trend", "patent_by_type", "award_by_level",
        ],
        kpi_class="kpi-8",
        chart_grid="grid-3x2",
        insight_count=3,
        chart_height="340px",
    ),

    # ── 类型 B：论文分析（5 指标）──
    "paper_analysis": DashboardLayout(
        layout_id="B",
        title_suffix="论文成果分析",
        kpi_metrics=[
            "paper_count_total", "paper_first_author_count",
        ],
        chart_metrics=[
            "paper_by_level", "paper_yearly_trend", "paper_author_role",
        ],
        kpi_class="kpi-2",
        chart_grid="grid-1x3",
        insight_count=2,
        chart_height="420px",
    ),

    # ── 类型 B：经费分析（6 指标）──
    "funding_detail": DashboardLayout(
        layout_id="B",
        title_suffix="经费分析",
        kpi_metrics=[
            "fund_total_arrived", "fund_total_spent", "fund_execution_rate",
        ],
        chart_metrics=[
            "fund_monthly_trend", "fund_expense_structure", "fund_yearly_comparison",
        ],
        kpi_class="kpi-3",
        chart_grid="grid-1x3",
        insight_count=2,
        chart_height="420px",
    ),

    # ── 类型 B：项目查询（4 指标）──
    "project_query": DashboardLayout(
        layout_id="B",
        title_suffix="科研项目概览",
        kpi_metrics=[
            "project_count_total", "project_count_leader",
        ],
        chart_metrics=[
            "project_by_level", "project_status_distribution", "project_yearly_trend",
        ],
        kpi_class="kpi-2",
        chart_grid="grid-1x3",
        insight_count=2,
        chart_height="420px",
    ),

    # ── 类型 C：获奖（3 指标）──
    "award_query": DashboardLayout(
        layout_id="C",
        title_suffix="获奖荣誉",
        kpi_metrics=["award_count"],
        chart_metrics=["award_by_level", "award_timeline"],
        kpi_class="kpi-1",
        chart_grid="grid-1x2",
        insight_count=2,
        chart_height="460px",
    ),

    # ── 类型 C：专利（3 指标）──
    "patent_analysis": DashboardLayout(
        layout_id="C",
        title_suffix="专利成果",
        kpi_metrics=["patent_count"],
        chart_metrics=["patent_by_type", "patent_yearly_trend"],
        kpi_class="kpi-1",
        chart_grid="grid-1x2",
        insight_count=2,
        chart_height="460px",
    ),

    # ── 类型 C：著作（2 指标）──
    "book_analysis": DashboardLayout(
        layout_id="C",
        title_suffix="著作成果",
        kpi_metrics=["book_count"],
        chart_metrics=["book_by_type", "book_by_role"],
        kpi_class="kpi-1",
        chart_grid="grid-1x2",
        insight_count=1,
        chart_height="460px",
    ),

    # ── 类型 C：软著（2 指标）──
    "software_analysis": DashboardLayout(
        layout_id="C",
        title_suffix="软件著作权",
        kpi_metrics=["software_count"],
        chart_metrics=["software_yearly_trend"],
        kpi_class="kpi-1",
        chart_grid="grid-1x1",
        insight_count=1,
        chart_height="500px",
    ),

    # ── 类型 C：学术活动（1 指标）──
    "conference_analysis": DashboardLayout(
        layout_id="C",
        title_suffix="学术活动",
        kpi_metrics=["conference_hosted"],
        chart_metrics=["conference_total_papers"],
        kpi_class="kpi-1",
        chart_grid="grid-1x1",
        insight_count=1,
        chart_height="500px",
    ),

    # ── 年度总结：用全景布局 ──
    "annual_summary": DashboardLayout(
        layout_id="A",
        title_suffix="年度科研总结",
        kpi_metrics=[
            "project_count_leader", "fund_total_arrived",
            "paper_count_total", "paper_first_author_count",
            "patent_count", "award_count",
        ],
        chart_metrics=[
            "project_yearly_trend", "fund_monthly_trend", "paper_year_trend",
            "patent_yearly_trend", "award_by_level", "award_timeline",
        ],
        kpi_class="kpi-6",
        chart_grid="grid-3x2",
        insight_count=3,
        chart_height="340px",
    ),

    # ── 职称评审：用全景布局 ──
    "title_evaluation": DashboardLayout(
        layout_id="A",
        title_suffix="职称评审材料",
        kpi_metrics=[
            "project_count_leader", "fund_total_arrived",
            "paper_count_total", "patent_count",
            "book_count", "software_count", "award_count",
        ],
        chart_metrics=[
            "project_by_level", "paper_by_level", "patent_by_type",
            "book_by_type", "software_yearly_trend", "award_by_level",
        ],
        kpi_class="kpi-7",
        chart_grid="grid-3x2",
        insight_count=2,
        chart_height="340px",
    ),
}


def get_layout(intent: str) -> DashboardLayout:
    """根据意图获取对应的大屏布局"""
    return LAYOUTS.get(intent, LAYOUTS["personal_overview"])
