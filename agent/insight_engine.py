"""
洞察生成器 — 科研指标数据 → 自然语言业务洞察

双模式：
1. LLM 模式（有 API Key）：语义丰富，趋势+异常+建议
2. 规则模式（无 API Key）：基于阈值的简单判断
"""
from pathlib import Path
from typing import Optional


class InsightEngine:
    """
    洞察生成器
    用法：
        engine = InsightEngine(llm=chat_model)
        insights = engine.generate(teacher_info, metric_results)
        # → ["· 近三年经费年均增长34%...", "· 论文SCI占比50%...", ...]
    """

    def __init__(self, llm=None):
        self.llm = llm

    def generate(
        self,
        teacher: dict,
        metrics_summary: dict,
        start_date: str = "2022-01-01",
        end_date: str = "2025-12-31",
    ) -> list[str]:
        """生成洞察"""
        if self.llm:
            return self._generate_with_llm(teacher, metrics_summary, start_date, end_date)
        else:
            return self._generate_with_rules(teacher, metrics_summary)

    # ── LLM 模式 ──
    def _generate_with_llm(self, teacher, metrics, start_date, end_date) -> list[str]:
        """使用 LLM 生成洞察"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt_path = Path(__file__).parent / "prompts" / "insight_generator.txt"
        template = prompt_path.read_text(encoding="utf-8")

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            text = chain.invoke({
                "teacher_name": teacher.get("xm", ""),
                "teacher_dept": teacher.get("dw_mc", ""),
                "teacher_title": teacher.get("zc", ""),
                "start_date": start_date,
                "end_date": end_date,
                "metrics_summary": self._format_summary(metrics),
            })
            # 按行拆分，过滤空行
            return [line.strip() for line in text.split("\n") if line.strip().startswith("·")]
        except Exception:
            return self._generate_with_rules(teacher, metrics)

    # ── 规则模式 ──
    def _generate_with_rules(self, teacher: dict, metrics: dict) -> list[str]:
        """基于规则 + 阈值生成简单洞察（零 LLM 依赖）"""
        insights = []
        dept = teacher.get("dw_mc", "")
        title = teacher.get("zc", "")

        # 项目数量
        proj_count = metrics.get("project_count_leader", 0)
        if proj_count >= 5:
            insights.append(f"· 主持科研项目 {proj_count} 个，科研活跃度较高")
        elif proj_count >= 1:
            insights.append(f"· 主持科研项目 {proj_count} 个")
        else:
            insights.append("· 暂无主持科研项目，建议积极申报各级科研课题")

        # 经费
        fund = metrics.get("fund_total_arrived", 0)
        if fund > 0:
            fund_w = round(fund / 10000, 1)
            insights.append(f"· 到账科研经费 {fund_w} 万元")

        # 论文
        paper = metrics.get("paper_first_author_count", 0)
        if paper > 0:
            insights.append(f"· 以第一作者发表论文 {paper} 篇")

        # 获奖
        award = metrics.get("award_count", 0)
        if award > 0:
            insights.append(f"· 获得科研奖项 {award} 项")

        # 职称相关的特殊洞察
        if title == "讲师" and proj_count >= 3:
            insights.append("· 作为讲师已主持多项科研项目，科研起步表现突出")
        elif title == "副教授" and proj_count >= 8:
            insights.append("· 科研产出丰富，已具备教授职称申报的基本条件")

        return insights[:3]  # 最多 3 条

    @staticmethod
    def _format_summary(metrics: dict) -> str:
        """把指标字典格式化为 LLM 友好的文本摘要"""
        lines = []
        for key, val in metrics.items():
            if isinstance(val, (int, float)) and val > 0:
                lines.append(f"  {key}: {val}")
            elif isinstance(val, list):
                lines.append(f"  {key}: 共 {len(val)} 项")
        return "\n".join(lines) if lines else "暂无数据"
