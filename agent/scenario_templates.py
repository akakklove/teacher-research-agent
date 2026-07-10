"""
场景模板引擎 — 预设指标组合 + LLM 叙事文案生成

三个预设场景：
1. 年度科研总结 — 趋势回顾、同比增长、院系对比
2. 职称评审材料 — 成果量化、成果清单、对标分析
3. 基金申报支撑 — 前期基础、经费能力、团队实力
"""
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class ScenarioTemplate:
    """场景模板定义"""
    id: str
    name: str
    description: str
    icon: str
    metric_ids: list[str]          # 预设指标 ID 列表
    time_range_months: int = 36    # 默认时间范围（月）
    include_comparison: bool = False    # 是否包含院系对比
    narrative_prompt_key: str = ""      # 对应的叙事 Prompt 标识


@dataclass
class ScenarioResult:
    """场景模板执行结果"""
    scenario_id: str
    scenario_name: str
    teacher: dict
    metrics: list                  # MetricResult 列表
    insights: list[str]            # AI 洞察
    narrative: str = ""            # LLM 生成的叙事文案（HTML 格式）
    time_range: tuple = field(default_factory=tuple)


class ScenarioEngine:
    """
    场景模板引擎

    用法：
        engine = ScenarioEngine(llm=chat_model)
        result = engine.execute(
            teacher_id="GH20200001",
            scenario_id="annual_summary",
            metric_engine=metric_engine,
        )
    """

    # ── 场景模板定义 ──
    TEMPLATES = {
        "annual_summary": ScenarioTemplate(
            id="annual_summary",
            name="年度科研总结",
            description="生成年度科研工作总结，包含趋势分析、对比报告",
            icon="📝",
            metric_ids=[
                "project_count_leader", "project_count_total",
                "project_yearly_trend", "project_by_level",
                "fund_total_arrived", "fund_execution_rate",
                "paper_count_total", "paper_first_author_count",
                "paper_yearly_trend", "patent_count",
                "award_count", "conference_hosted",
            ],
            time_range_months=36,
            include_comparison=True,
            narrative_prompt_key="annual_summary",
        ),
        "title_evaluation": ScenarioTemplate(
            id="title_evaluation",
            name="职称评审材料",
            description="汇总职称评审所需全部科研指标，成果量化",
            icon="🏅",
            metric_ids=[
                "project_count_leader", "project_by_level",
                "fund_total_arrived",
                "paper_count_total", "paper_by_level", "paper_first_author_count",
                "patent_count", "patent_by_type",
                "book_count", "software_count",
                "award_count", "award_by_level",
            ],
            time_range_months=60,  # 职称评审一般看近5年
            include_comparison=True,
            narrative_prompt_key="title_evaluation",
        ),
        "grant_application": ScenarioTemplate(
            id="grant_application",
            name="基金申报支撑",
            description="展示前期科研基础、团队实力与经费管理能力",
            icon="💰",
            metric_ids=[
                "project_count_leader", "project_by_level",
                "fund_total_arrived", "fund_execution_rate",
                "paper_count_total", "paper_by_level",
                "patent_count", "award_count",
            ],
            time_range_months=36,
            include_comparison=False,
            narrative_prompt_key="grant_application",
        ),
    }

    def __init__(self, llm=None):
        self.llm = llm

    def list_templates(self) -> list[dict]:
        """列出所有可用场景模板"""
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "icon": t.icon,
                "metric_count": len(t.metric_ids),
                "time_range": f"近{t.time_range_months//12}年",
                "has_comparison": t.include_comparison,
            }
            for t in self.TEMPLATES.values()
        ]

    def execute(
        self,
        teacher_id: str,
        scenario_id: str,
        metric_engine,
        custom_time_range: tuple = None,
    ) -> ScenarioResult:
        """
        执行场景模板：查询指标 → 生成洞察 → 生成叙事文案

        Args:
            teacher_id: 教师工号
            scenario_id: 场景 ID（annual_summary / title_evaluation / grant_application）
            metric_engine: MetricEngine 实例
            custom_time_range: 可选自定义时间范围 (start_date, end_date)

        Returns:
            ScenarioResult
        """
        template = self.TEMPLATES.get(scenario_id)
        if not template:
            raise ValueError(f"未知场景模板: {scenario_id}，可用: {list(self.TEMPLATES.keys())}")

        # 计算时间范围
        if custom_time_range:
            start_date, end_date = custom_time_range
        else:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=template.time_range_months * 30)).strftime("%Y-%m-%d")

        # 获取教师信息
        teacher = metric_engine.get_teacher_info(teacher_id)
        if not teacher:
            raise ValueError(f"教师 {teacher_id} 不存在")

        # 执行指标查询
        results = metric_engine.execute(teacher_id, template.metric_ids, {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_date[:4],
            "end_year": end_date[:4],
        })

        # 生成洞察
        from insight_engine import InsightEngine
        insight_engine = InsightEngine(llm=self.llm)
        summary = {r.metric_id: r.value or len(r.rows) for r in results if r.success}
        insights = insight_engine.generate(teacher, summary, start_date, end_date)

        # 生成叙事文案
        narrative = ""
        if self.llm:
            narrative = self._generate_narrative(
                template, teacher, results, summary, start_date, end_date
            )

        return ScenarioResult(
            scenario_id=scenario_id,
            scenario_name=template.name,
            teacher=teacher,
            metrics=results,
            insights=insights,
            narrative=narrative,
            time_range=(start_date, end_date),
        )

    # ── LLM 叙事文案生成 ──
    def _generate_narrative(
        self,
        template: ScenarioTemplate,
        teacher: dict,
        results: list,
        summary: dict,
        start_date: str,
        end_date: str,
    ) -> str:
        """使用 LLM 生成场景化叙事文案"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt_path = (
            Path(__file__).parent / "prompts" / "scenario_narrative.txt"
        )
        if not prompt_path.exists():
            return self._fallback_narrative(template, teacher, summary)

        system_prompt = prompt_path.read_text(encoding="utf-8")

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", self._format_scenario_input(
                template, teacher, summary, start_date, end_date
            ))
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            text = chain.invoke({
                "scenario_name": template.name,
                "teacher_name": teacher.get("xm", ""),
                "teacher_dept": teacher.get("dw_mc", ""),
                "teacher_title": teacher.get("zc", ""),
                "start_date": start_date,
                "end_date": end_date,
                "data_summary": self._format_summary(summary),
            })
            return text
        except Exception:
            return self._fallback_narrative(template, teacher, summary)

    def _format_scenario_input(
        self, template, teacher, summary, start_date, end_date
    ) -> str:
        """构建场景化的 LLM 输入"""
        name = teacher.get("xm", "老师")
        dept = teacher.get("dw_mc", "")
        title = teacher.get("zc", "")

        parts = [
            f"## 场景：{template.name}",
            f"- 教师：{name}，{dept}，{title}",
            f"- 时间范围：{start_date} ~ {end_date}",
            "",
            "## 数据摘要",
            self._format_summary(summary),
        ]
        return "\n".join(parts)

    @staticmethod
    def _format_summary(summary: dict) -> str:
        """将指标摘要格式化为可读文本"""
        labels = {
            "project_count_leader": "主持项目数",
            "project_count_total": "参与项目数",
            "fund_total_arrived": "到账经费(元)",
            "fund_execution_rate": "经费执行率(%)",
            "paper_count_total": "发表论文数",
            "paper_first_author_count": "一作论文数",
            "patent_count": "专利数",
            "book_count": "著作数",
            "software_count": "软著数",
            "award_count": "获奖数",
            "conference_hosted": "学术会议数",
        }
        lines = []
        for key, val in summary.items():
            label = labels.get(key, key)
            if isinstance(val, float):
                lines.append(f"  {label}: {val:.1f}")
            else:
                lines.append(f"  {label}: {val}")
        return "\n".join(lines) if lines else "暂无数据"

    @staticmethod
    def _fallback_narrative(template, teacher: dict, summary: dict) -> str:
        """无 LLM 时的简单模板叙事"""
        name = teacher.get("xm", "老师")
        dept = teacher.get("dw_mc", "")

        proj = summary.get("project_count_leader", 0)
        fund = summary.get("fund_total_arrived", 0)
        paper = summary.get("paper_count_total", 0)
        award = summary.get("award_count", 0)

        fund_w = round(fund / 10000, 1) if fund else 0

        narratives = {
            "annual_summary": (
                f"## {name}老师 年度科研工作总结\n\n"
                f"**单位：**{dept}\n\n"
                f"### 一、科研项目\n"
                f"主持科研项目 **{proj}** 个，科研工作扎实推进。\n\n"
                f"### 二、科研经费\n"
                f"到账科研经费 **{fund_w}万元**，经费使用规范。\n\n"
                f"### 三、科研成果\n"
                f"发表论文 **{paper}** 篇，获科研奖项 **{award}** 项。\n\n"
                f"### 四、下一年度展望\n"
                f"继续积极申报各级科研项目，提升科研成果质量。"
            ),
            "title_evaluation": (
                f"## {name}老师 职称评审科研成果汇总\n\n"
                f"**单位：**{dept}\n\n"
                f"| 指标 | 数值 |\n|------|------|\n"
                f"| 主持项目 | {proj} 个 |\n"
                f"| 到账经费 | {fund_w}万元 |\n"
                f"| 发表论文 | {paper} 篇 |\n"
                f"| 科研获奖 | {award} 项 |\n\n"
                f"以上为近五年科研数据汇总。"
            ),
            "grant_application": (
                f"## {name}老师 基金申报前期基础\n\n"
                f"**单位：**{dept}\n\n"
                f"### 研究基础\n"
                f"已主持 **{proj}** 个科研项目，具备扎实的科研经验。\n\n"
                f"### 经费管理\n"
                f"累计到账经费 **{fund_w}万元**，经费管理规范。\n\n"
                f"### 成果积累\n"
                f"发表论文 **{paper}** 篇，获科研奖项 **{award}** 项。\n\n"
                f"前期基础扎实，具备承担本课题的研究能力。"
            ),
        }
        return narratives.get(template.id, f"{name}老师的科研数据汇总完成。")
