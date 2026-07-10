"""
意图路由 — 用户自然语言输入 → 结构化意图 + 推荐指标组合

双模式：
1. LangChain + LLM（有 API Key 时）：语义理解准
2. 规则引擎兜底（无 API Key 时）：关键词匹配，零延迟

v0.4 新增：route_with_context() 支持多轮对话上下文
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
    is_followup: bool = False   # v0.4: 是否为追问


class IntentRouter:
    """
    意图路由
    用法：
        router = IntentRouter(llm=None)  # 纯规则模式
        result = router.route("帮我查查近两年的科研情况")
        print(result.intent)  # "personal_overview"

        # v0.4 多轮对话：
        context = memory.build_context(session_id, "那论文呢？")
        result = router.route_with_context("那论文呢？", context=context)
    """

    # 意图 → 推荐指标组合
    INTENT_METRICS_MAP = {
        "chitchat": [],   # 闲聊/问候：不查询任何指标
        "personal_overview": [
            # KPI 卡片
            "project_count_leader", "project_count_total",
            "fund_total_arrived", "fund_total_spent",
            "paper_count_total", "paper_first_author_count",
            "patent_count", "book_count",
            "software_count", "award_count",
            "conference_hosted",
            # 排名
            "paper_rank_dept", "project_rank_dept", "fund_rank_dept",
            "composite_output_score", "department_percentile",
            # 图表
            "project_by_level", "project_status_distribution", "project_yearly_trend",
            "fund_monthly_trend", "fund_yearly_inout", "fund_execution_rate",
            "paper_by_level", "paper_yearly_trend", "paper_by_year_level",
            "patent_by_type", "patent_yearly_trend",
            "award_by_level", "award_yearly_category",
            "book_by_type", "software_yearly_trend",
            "achievement_yearly_table",
        ],
        "funding_detail": [
            "fund_total_arrived", "fund_total_spent",
            "fund_execution_rate", "fund_monthly_trend",
            "fund_yearly_inout", "fund_yearly_comparison",
            "fund_monthly_spent_trend", "fund_rank_dept",
            "fund_rank_school",
        ],
        "paper_analysis": [
            "paper_count_total", "paper_first_author_count",
            "paper_by_level", "paper_yearly_trend", "paper_author_role",
            "paper_journal_source", "paper_author_ranking",
            "paper_by_year_level", "paper_rank_dept", "paper_rank_school",
        ],
        "award_query": [
            "award_count", "award_by_level", "award_timeline",
            "award_category", "award_yearly_trend",
            "award_by_year_category",
        ],
        "project_query": [
            "project_count_total", "project_count_leader",
            "project_by_level", "project_status_distribution",
            "project_yearly_trend", "project_by_source",
            "project_fund_ranking", "project_rank_dept",
            "project_by_year_level",
        ],
        "annual_summary": [
            "project_count_leader", "project_yearly_trend",
            "fund_total_arrived", "fund_execution_rate",
            "paper_first_author_count",
            "patent_yearly_trend",
            "award_count", "award_timeline",
            "achievement_yearly_table", "composite_output_score",
            "department_percentile",
        ],
        "title_evaluation": [
            "project_count_leader", "project_by_level",
            "fund_total_arrived",
            "paper_count_total", "paper_by_level",
            "patent_count", "patent_by_type",
            "book_count", "software_count",
            "award_count", "award_by_level",
            "composite_output_score", "paper_rank_school",
            "project_rank_school",
        ],
        # v0.4 追问专用意图
        "patent_analysis": [
            "patent_count", "patent_by_type", "patent_yearly_trend",
            "patent_rank_dept", "patent_rank_school",
        ],
        "book_analysis": [
            "book_count", "book_by_type", "book_by_role",
            "book_publisher", "book_yearly_trend",
        ],
        "software_analysis": [
            "software_count", "software_yearly_trend",
            "software_by_type",
        ],
        "conference_analysis": [
            "conference_hosted", "conference_total_papers",
            "conference_by_type", "institution_by_type",
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

    def route_with_context(self, user_input: str, context: dict = None) -> IntentResult:
        """
        v0.4 新增：带上下文感知的意图路由。

        context 来自 ConversationMemory.build_context()，包含：
        - is_followup: 是否为追问
        - suggested_intent: 追问时推断的意图
        - conversation_history: 最近几轮对话摘要
        - time_range: 继承的时间范围
        """
        if context is None or not context.get("is_followup"):
            # 无上下文 → 普通路由
            return self.route(user_input)

        # ── 追问模式：优先用上下文推断 ──
        suggested = context.get("suggested_intent")

        if suggested:
            # 上下文已推断出意图 → 高置信度
            result = IntentResult(
                intent=suggested,
                time_range=context.get("time_range", "last_3_years"),
                confidence=0.85,
                is_followup=True,
            )
        elif self.llm:
            # LLM 模式：传入对话历史做上下文理解
            result = self._route_with_llm_and_history(user_input, context)
        else:
            # 规则引擎兜底
            result = self._route_with_rules(user_input)

        # 补充推荐指标
        result.recommended_metrics = self.INTENT_METRICS_MAP.get(
            result.intent,
            self.INTENT_METRICS_MAP["personal_overview"]
        )
        return result

    # ── LLM 模式（含上下文） ──
    def _route_with_llm_and_history(self, user_input: str, context: dict) -> IntentResult:
        """带对话历史的 LLM 意图识别"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import PydanticOutputParser
        from pydantic import BaseModel

        class IntentSchema(BaseModel):
            intent: str
            time_range: str = "last_3_years"
            confidence: float = 0.8

        parser = PydanticOutputParser(pydantic_object=IntentSchema)

        prompt_path = Path(__file__).parent / "prompts" / "intent_classifier_followup.txt"
        if not prompt_path.exists():
            # 兼容：没有追问专用 prompt 则用原始 + 拼接历史
            prompt_path = Path(__file__).parent / "prompts" / "intent_classifier.txt"

        system_prompt = prompt_path.read_text(encoding="utf-8")

        # 拼接对话历史
        history_text = "\n".join(context.get("conversation_history", []))

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n{format_instructions}"),
            ("human", "对话历史：\n{history}\n\n用户当前问题：{user_input}")
        ])

        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({
                "user_input": user_input,
                "history": history_text,
                "format_instructions": parser.get_format_instructions(),
            })
            return IntentResult(
                intent=result.intent,
                time_range=result.time_range,
                confidence=result.confidence,
                is_followup=True,
            )
        except Exception:
            return self._route_with_rules(user_input)

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

        # 1. 先识别闲聊/问候（优先级最高）
        # 强信号：直接问候/感谢/告别/身份询问，只要不含科研主题词就判定闲聊
        strong_chitchat = ["你好", "您好", "哈喽", "hi", "hello",
                           "早上好", "下午好", "晚上好", "谢谢", "感谢",
                           "再见", "拜拜", "bye", "你是谁", "你能做什么",
                           "介绍一下", "干嘛的", "在吗", "在不在"]
        # 弱信号：寒暄式问句，需要句子很短且不含科研/数据词才判定闲聊
        weak_chitchat = ["吃了吗", "忙吗", "最近好吗", "最近如何"]

        research_terms = ["科研", "论文", "项目", "经费", "专利", "获奖",
                          "著作", "软著", "会议", "职称", "年度", "情况",
                          "数据", "结果", "分析", "查询", "查一下", "看看"]
        data_words = any(t in text for t in research_terms)

        has_strong = any(kw in text for kw in strong_chitchat)
        has_weak = any(kw in text for kw in weak_chitchat)

        if has_strong and len(user_input) <= 25 and not data_words:
            return IntentResult(intent="chitchat", time_range="all", confidence=0.9)
        if has_weak and len(user_input) <= 12 and not data_words:
            return IntentResult(intent="chitchat", time_range="all", confidence=0.75)

        # 意图识别
        scores = {
            "personal_overview":   self._score(text, ["全貌","全景","总览","整体","综合","帮我看","查一下","查询"]),
            "funding_detail":      self._score(text, ["经费","到账","支出","财务","钱","花了","预算"]),
            "paper_analysis":      self._score(text, ["论文","文章","发表","期刊","SCI","EI","核心"]),
            "patent_analysis":     self._score(text, ["专利","发明","实用新型","外观"]),
            "award_query":         self._score(text, ["获奖","奖项","奖励","荣誉","评奖"]),
            "project_query":       self._score(text, ["项目","课题","在研","结题","立项"]),
            "book_analysis":       self._score(text, ["著作","专著","教材","编著","出版"]),
            "software_analysis":   self._score(text, ["软著","软件","著作权","程序"]),
            "conference_analysis": self._score(text, ["会议","学术会议","报告","交流"]),
            "annual_summary":      self._score(text, ["年度","年终","总结","考核","汇报","报告","PPT"]),
            "title_evaluation":    self._score(text, ["职称","评审","评职称","材料","副教授","教授","升职"]),
        }

        # 取最高分（平票时优先选非全景的专门类别）
        best_score = max(scores.values())
        if best_score == 0:
            return IntentResult(intent="personal_overview", time_range="last_3_years", confidence=0.3)

        # 平票时：排除 personal_overview，优先专门类别
        tied = [k for k, v in scores.items() if v == best_score]
        if len(tied) > 1 and "personal_overview" in tied:
            tied.remove("personal_overview")
        best = tied[0]
        confidence = 0.7 if best_score >= 2 else 0.5

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
