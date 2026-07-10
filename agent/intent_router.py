"""
意图路由 — 用户自然语言输入 → 结构化意图 + 推荐指标组合

双模式：
1. LangChain + LLM（有 API Key 时）：语义理解准
2. 规则引擎兜底（无 API Key 时）：关键词匹配，零延迟
"""
import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: str           # personal_overview / funding_detail / paper_analysis / ...
    time_range: str       # last_3_years / last_year / all
    confidence: float     # 0.0-1.0
    recommended_metrics: list[str] = field(default_factory=list)


class IntentRouter:
    """
    意图路由
    用法：
        router = IntentRouter(llm_api_key=None)  # 纯规则模式
        result = router.route("帮我查查近两年的科研情况")
        print(result.intent)  # "personal_overview"
    """

    # 意图 → 推荐指标组合
    INTENT_METRICS_MAP = {
        "personal_overview": [
            "project_count_leader", "project_by_level",
            "fund_total_arrived", "fund_execution_rate",
            "paper_first_author_count", "paper_by_level",
            "patent_count", "book_count", "software_count",
            "award_count", "award_by_level",
        ],
        "funding_detail": [
            "fund_total_arrived", "fund_total_spent",
            "fund_execution_rate", "fund_monthly_trend",
            "fund_expense_structure", "fund_yearly_comparison",
        ],
        "paper_analysis": [
            "paper_count_total", "paper_first_author_count",
            "paper_by_level", "paper_yearly_trend", "paper_author_role",
        ],
        "award_query": [
            "award_count", "award_by_level", "award_timeline",
        ],
        "project_query": [
            "project_count_total", "project_count_leader",
            "project_by_level", "project_status_distribution",
            "project_yearly_trend",
        ],
        "annual_summary": [
            "project_count_leader", "project_yearly_trend",
            "fund_total_arrived", "fund_execution_rate",
            "paper_first_author_count",
            "patent_yearly_trend",
            "award_count", "award_timeline",
        ],
        "title_evaluation": [
            "project_count_leader", "project_by_level",
            "fund_total_arrived",
            "paper_count_total", "paper_by_level",
            "patent_count", "patent_by_type",
            "book_count", "software_count",
            "award_count", "award_by_level",
        ],
    }

    # 时间范围映射
    TIME_KEYWORDS = {
        "last_year": ["去年", "这一年", "近一年", "最近一年", "今年"],
        "last_3_years": ["近三年", "近两年", "这几年", "两年", "三年"],
        "specific_year": [],  # 需要 LLM 提取
        "all": ["全部", "所有"],
    }

    def __init__(self, llm=None):
        """
        Args:
            llm: LangChain ChatModel 实例，None 则使用纯规则模式
        """
        self.llm = llm

    def route(self, user_input: str) -> IntentResult:
        """主入口：分析用户输入，返回意图 + 推荐指标"""
        if self.llm:
            result = self._route_with_llm(user_input)
        else:
            result = self._route_with_rules(user_input)

        # 补充推荐指标
        result.recommended_metrics = self.INTENT_METRICS_MAP.get(
            result.intent,
            self.INTENT_METRICS_MAP["personal_overview"]
        )
        return result

    # ── LLM 模式 ──
    def _route_with_llm(self, user_input: str) -> IntentResult:
        """使用 LangChain + LLM 做意图识别"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import PydanticOutputParser
        from pydantic import BaseModel

        class IntentSchema(BaseModel):
            intent: str
            time_range: str = "last_3_years"
            confidence: float = 0.8

        parser = PydanticOutputParser(pydantic_object=IntentSchema)

        # 读取 Prompt 模板
        prompt_path = Path(__file__).parent / "prompts" / "intent_classifier.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8")

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n{format_instructions}"),
            ("human", "{user_input}")
        ])

        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({
                "user_input": user_input,
                "format_instructions": parser.get_format_instructions()
            })
            return IntentResult(
                intent=result.intent,
                time_range=result.time_range,
                confidence=result.confidence,
            )
        except Exception:
            # LLM 调用失败，降级到规则引擎
            return self._route_with_rules(user_input)

    # ── 规则引擎模式（兜底） ──
    def _route_with_rules(self, user_input: str) -> IntentResult:
        """基于关键词的规则匹配"""
        text = user_input.lower()

        # 意图识别
        scores = {
            "personal_overview": self._score(text, ["科研","情况","全貌","全景","总览","整体","综合","帮我看","查一下"]),
            "funding_detail":    self._score(text, ["经费","到账","支出","财务","钱","花了","预算"]),
            "paper_analysis":    self._score(text, ["论文","文章","发表","期刊","SCI","EI","核心"]),
            "award_query":       self._score(text, ["获奖","奖项","奖励","荣誉","评奖"]),
            "project_query":     self._score(text, ["项目","课题","在研","结题","立项"]),
            "annual_summary":    self._score(text, ["年度","年终","总结","考核","汇报","报告","PPT"]),
            "title_evaluation":  self._score(text, ["职称","评审","评职称","材料","副教授","教授","升职"]),
        }

        # 取最高分
        best = max(scores, key=scores.get)
        confidence = 0.6 if scores[best] > 2 else 0.4

        # 时间范围识别
        time_range = "last_3_years"  # 默认
        for tr, keywords in self.TIME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                time_range = tr
                break

        return IntentResult(
            intent=best,
            time_range=time_range,
            confidence=confidence,
        )

    def _score(self, text: str, keywords: list) -> int:
        """计算关键词匹配度"""
        return sum(1 for kw in keywords if kw in text)
