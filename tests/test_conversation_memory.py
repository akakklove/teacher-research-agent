"""
会话记忆管理 — 单元测试（纯内存，无数据库依赖）

覆盖：
- 会话创建/获取/过期
- 追问检测（7 种追问模式）
- 对话轮次记录
- Session.last_user_intent / last_metric_ids
"""
import time
import pytest
from agent.conversation_memory import (
    ConversationMemory, Session, ConversationTurn
)


@pytest.fixture
def memory():
    """短 TTL 便于测试过期的记忆管理器"""
    return ConversationMemory(ttl_seconds=2)


@pytest.fixture
def session(memory):
    """预置一条会话"""
    return memory.get_or_create(
        teacher_id="GH20200001",
        teacher_info={"name": "张三", "department": "计算机学院"},
    )


# ── 会话生命周期 ──

class TestSessionLifecycle:
    """会话创建/获取/过期"""

    def test_create_session(self, memory):
        sess = memory.get_or_create("GH20200001")
        assert sess.teacher_id == "GH20200001"
        assert isinstance(sess.session_id, str)
        assert len(sess.session_id) > 0

    def test_same_teacher_reuses_session(self, memory):
        s1 = memory.get_or_create("GH20200001")
        s2 = memory.get_or_create("GH20200001")
        assert s1.session_id == s2.session_id

    def test_different_teacher_new_session(self, memory):
        s1 = memory.get_or_create("GH20200001")
        s2 = memory.get_or_create("GH20200002")
        assert s1.session_id != s2.session_id

    def test_session_expiry(self, memory):
        sess = memory.get_or_create("GH20200001")
        # get() 返回存在的 session
        assert memory.get(sess.session_id) is not None

        # 等 TTL 过期
        time.sleep(2.1)

        # 过期后 cleanup_expired 清理
        memory.cleanup_expired()
        assert memory.get(sess.session_id) is None

    def test_session_count(self, memory):
        assert memory.active_count == 0
        memory.get_or_create("GH20200001")
        assert memory.active_count == 1
        memory.get_or_create("GH20200002")
        assert memory.active_count == 2


# ── 对话轮次 ──

class TestConversationTurns:
    """添加/查询对话轮次"""

    def test_add_turn(self, memory, session):
        memory.add_turn(
            session.session_id, "user", "我的论文情况",
            intent="paper_analysis",
        )
        memory.add_turn(
            session.session_id, "assistant",
            "您的论文共 15 篇，其中 SCI 5 篇",
            metric_ids=["paper_count_total", "paper_by_level"],
        )

        sess = memory.get(session.session_id)
        assert sess is not None
        assert len(sess.history) >= 2
        assert sess.history[0].role == "user"
        assert sess.history[1].role == "assistant"

    def test_history_limit(self, memory):
        """超 20 轮后旧轮次应被裁剪"""
        sess = memory.get_or_create("GH20200001")
        for i in range(25):
            memory.add_turn(sess.session_id, "user", f"question {i}")
            memory.add_turn(sess.session_id, "assistant", f"answer {i}")

        sess = memory.get(sess.session_id)
        assert sess is not None
        # 保留最近 20 轮（每轮 2 条=40 条历史）
        assert len(sess.history) <= 40

    def test_touch_updates_last_active(self, memory):
        sess = memory.get_or_create("GH20200001")
        t0 = sess.last_active
        time.sleep(0.1)
        memory.add_turn(sess.session_id, "user", "hello")
        sess2 = memory.get(sess.session_id)
        assert sess2 is not None
        assert sess2.last_active > t0


# ── 追问检测 ──

class TestFollowupDetection:
    """追问模式检测"""

    FOLLOWUP_QUERIES = [
        "那论文情况呢？",
        "那再看看专利",
        "还有获奖呢",
        "另外经费使用情况",
        "顺便看看著作",
        "具体说说论文",
        "详细讲讲项目",
        "再问一下软著",
    ]

    NON_FOLLOWUP_QUERIES = [
        "帮我看看整体科研情况",
        "我的论文发表在哪些期刊",
        "今年到账多少经费",
    ]

    @pytest.mark.parametrize("query", FOLLOWUP_QUERIES)
    def test_is_followup(self, memory, session, query):
        """追问词应被检测为追问"""
        memory.add_turn(
            session.session_id, "user", "科研全景",
            intent="personal_overview",
        )
        assert memory.is_followup(session.session_id, query) is True, \
            f"Query '{query}' should be detected as followup"

    @pytest.mark.parametrize("query", NON_FOLLOWUP_QUERIES)
    def test_not_followup(self, memory, session, query):
        """非追问词不应被检测为追问"""
        assert memory.is_followup(session.session_id, query) is False, \
            f"Query '{query}' should NOT be detected as followup"

    def test_no_context_no_followup(self, memory):
        """无上下文时不误判"""
        memory.get_or_create("GH20200001")  # 空历史
        # is_followup 无历史返回 False
        sess = memory.get_or_create("GH20200001")
        assert memory.is_followup(sess.session_id, "那论文呢？") is False


# ── Session 属性 ──

class TestSessionProperties:
    """Session 数据类属性"""

    def test_last_user_intent(self, memory):
        sess = memory.get_or_create("GH20200001")
        assert sess.last_user_intent is None

        memory.add_turn(sess.session_id, "user", "论文", intent="paper_analysis")
        assert sess.last_user_intent == "paper_analysis"

    def test_last_metric_ids(self, memory):
        sess = memory.get_or_create("GH20200001")
        assert sess.last_metric_ids == []

        memory.add_turn(
            sess.session_id, "assistant", "结果",
            metric_ids=["paper_count_total", "paper_by_level"],
        )
        assert sess.last_metric_ids == ["paper_count_total", "paper_by_level"]


# ── ConversationTurn 数据类 ──

class TestConversationTurn:
    """ConversationTurn 数据类"""

    def test_create_turn(self):
        t = ConversationTurn(
            role="user",
            content="我的科研情况",
            intent="personal_overview",
        )
        assert t.role == "user"
        assert t.content == "我的科研情况"
        assert t.intent == "personal_overview"
        assert isinstance(t.timestamp, float)

    def test_default_values(self):
        t = ConversationTurn(role="user", content="hello")
        assert t.intent is None
        assert t.metric_ids == []
        assert t.confidence == 1.0


# ── 全局单例 ──

class TestGlobalMemory:
    """验证 get_memory() 单例模式"""

    def test_get_memory_is_singleton(self):
        from agent.conversation_memory import get_memory
        m1 = get_memory()
        m2 = get_memory()
        assert m1 is m2
