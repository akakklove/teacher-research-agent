"""
意图路由 — 单元测试（纯规则模式，无需 LLM / 数据库）

覆盖：
- 11 种意图识别
- 关键词权重匹配
- 平票处理逻辑
- 意图指标映射
"""
import pytest
from agent.intent_router import IntentRouter, IntentResult


@pytest.fixture
def router():
    """无 LLM 的纯规则路由器"""
    return IntentRouter(llm=None)


# ── 核心意图匹配 ──

class TestBasicIntentMatching:
    """基础意图路由测试"""

    @pytest.mark.parametrize("query,expected_intent", [
        ("你好", "chitchat"),
        ("谢谢", "chitchat"),
        ("你是谁", "chitchat"),
        ("在吗", "chitchat"),
        ("帮我看看整体科研情况", "personal_overview"),
        ("看一下我的科研全景", "personal_overview"),
        ("整体情况怎么样", "personal_overview"),
        ("经费到账了多少", "funding_detail"),
        ("经费使用情况", "funding_detail"),
        ("论文发了多少篇", "paper_analysis"),
        ("论文发表情况", "paper_analysis"),
        ("专利有哪些", "patent_analysis"),
        ("专利情况", "patent_analysis"),
        ("获得了什么奖项", "award_query"),
        ("获奖情况", "award_query"),
        ("科研项目有哪些", "project_query"),
        ("项目情况", "project_query"),
        ("著作出版了哪些", "book_analysis"),
        ("教材出版情况", "book_analysis"),
        ("软著有哪些", "software_analysis"),
        ("会议参加情况", "conference_analysis"),
    ])
    def test_basic_intent_matching(self, router, query, expected_intent):
        result = router.route(query)
        assert result.intent == expected_intent, \
            f"Query '{query}' → {result.intent}, expected {expected_intent}"

    def test_confidence_above_zero(self, router):
        """有效查询应返回 > 0 的置信度"""
        result = router.route("论文情况")
        assert result.confidence > 0

    def test_unknown_query_fallback(self, router):
        """无意义输入应回退到 personal_overview（低置信度）"""
        result = router.route("asdfghjkl")
        assert result.intent == "personal_overview"
        assert result.confidence < 0.5


# ── 时间范围推断 ──

class TestChitchatDetection:
    """闲聊/问候意图识别"""

    @pytest.mark.parametrize("query", [
        "你好", "您好", "哈喽", "hi", "hello",
        "早上好", "下午好", "晚上好",
        "谢谢", "感谢", "再见", "拜拜",
        "你是谁", "你能做什么", "介绍一下", "在吗", "忙吗",
        "吃了吗", "最近好吗",
    ])
    def test_greetings_detected_as_chitchat(self, router, query):
        result = router.route(query)
        assert result.intent == "chitchat", \
            f"Query '{query}' → {result.intent}, expected chitchat"

    def test_chitchat_has_no_metrics(self, router):
        result = router.route("你好")
        assert result.recommended_metrics == []

    def test_long_query_with_research_terms_not_chitchat(self, router):
        """含科研主题的较长句子不应被判定为闲聊"""
        result = router.route("你好，帮我查一下论文发表情况")
        assert result.intent != "chitchat", \
            f"Expected research intent, got {result.intent}"

    """时间范围推断 — 规则引擎使用关键词匹配"""

    @pytest.mark.parametrize("query,expected_range", [
        ("近三年科研情况", "last_3_years"),
        ("最近三年的论文", "last_3_years"),
        ("过去三年经费", "last_3_years"),
        ("去年的获奖", "last_year"),
    ])
    def test_time_range(self, router, query, expected_range):
        result = router.route(query)
        assert result.time_range == expected_range, \
            f"Query '{query}' → time_range={result.time_range}, expected {expected_range}"

    def test_default_time_range(self, router):
        """无特定时间词的查询使用路由默认值"""
        result = router.route("论文情况")
        # 规则引擎默认可能是 last_3_years 或 all
        assert result.time_range in ("all", "last_3_years", "last_year")


# ── 平票处理（regression test） ──

class TestTieBreaking:
    """验证 intent_router 平票逻辑修复"""

    def test_paper_keyword_not_overview(self, router):
        """含'论文'关键词时应匹配 paper_analysis 而非 personal_overview"""
        result = router.route("科研论文")
        assert result.intent != "personal_overview", \
            "bug regression: '科研论文' 误判为 personal_overview"

    def test_award_not_overview(self, router):
        """'获奖' 应精确匹配"""
        result = router.route("我的获奖")
        assert result.intent == "award_query", \
            f"Expected award_query, got {result.intent}"

    def test_project_not_overview(self, router):
        """'科研项目' 应精确匹配 project_query"""
        result = router.route("科研项目有哪些")
        assert result.intent == "project_query", \
            f"Expected project_query, got {result.intent}"


# ── 推荐指标验证 ──

class TestRecommendedMetrics:
    """验证每个意图都返回非空指标列表"""

    def test_all_intents_have_metrics(self, router):
        for intent in [
            "personal_overview", "funding_detail", "paper_analysis",
            "patent_analysis", "award_query", "project_query",
            "book_analysis", "software_analysis", "conference_analysis",
            "annual_summary", "title_evaluation",
        ]:
            intent_metrics = router.INTENT_METRICS_MAP.get(intent, [])
            assert len(intent_metrics) > 0, \
                f"Intent '{intent}' has no metrics defined"

    def test_route_returns_recommended_metrics(self, router):
        """route() 应填充 recommended_metrics"""
        result = router.route("论文发表了哪些")
        assert len(result.recommended_metrics) > 0
        assert any("paper" in m for m in result.recommended_metrics)


# ── IntentResult 数据结构验证 ──

class TestIntentResultDataClass:
    """验证 IntentResult 数据类字段"""

    def test_empty_result_has_defaults(self):
        r = IntentResult(intent="unknown", time_range="all", confidence=0.0)
        assert r.recommended_metrics == []
        assert r.is_followup is False

    def test_result_fields_access(self):
        r = IntentResult(
            intent="paper_analysis",
            time_range="last_3_years",
            confidence=0.85,
            recommended_metrics=["paper_count_total", "paper_by_level"],
            is_followup=True,
        )
        assert r.intent == "paper_analysis"
        assert r.confidence == pytest.approx(0.85)
        assert len(r.recommended_metrics) == 2
        assert r.is_followup is True
