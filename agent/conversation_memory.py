"""
会话记忆管理器 — 管理多轮对话的上下文状态

核心能力：
1. 会话生命周期管理（创建 / 查找 / 过期清理）
2. 追问检测（代词消解、时间/教师继承）
3. 对话历史存储（含意图和指标 ID，供 LLM 上下文使用）
"""
import time
import uuid
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationTurn:
    """单轮对话记录"""
    role: str              # "user" | "assistant"
    content: str           # 原始文本
    intent: Optional[str] = None        # 本轮意图
    metric_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    """一次对话会话"""
    session_id: str
    teacher_id: str
    teacher_info: dict = field(default_factory=dict)
    history: list[ConversationTurn] = field(default_factory=list)
    time_range: tuple = ("2022-01-01", "2025-12-31")
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def touch(self):
        self.last_active = time.time()

    @property
    def last_user_intent(self) -> Optional[str]:
        for turn in reversed(self.history):
            if turn.role == "user" and turn.intent:
                return turn.intent
        return None

    @property
    def last_metric_ids(self) -> list[str]:
        for turn in reversed(self.history):
            if turn.role == "assistant" and turn.metric_ids:
                return turn.metric_ids
        return []


class ConversationMemory:
    """
    会话记忆管理器

    用法：
        memory = ConversationMemory(ttl_seconds=3600)

        # 获取或创建会话
        session = memory.get_or_create(teacher_id="GH20200001", teacher_info={...})

        # 添加对话轮次
        memory.add_turn(session.session_id, "user", "我的科研情况", intent="personal_overview")

        # 检测是否追问
        is_follow = memory.is_followup(session.session_id, "那论文呢？")
    """

    # 追问信号词（常见省略主语/代词的追问开头）
    FOLLOWUP_PATTERNS = [
        r"^(那|那再|还有|另外|此外|追加|顺便|再|那么)",
        r"^(帮我也|帮我再|也帮|也再)",
        r"^(再问|追问|接着|继续|接下来)",
        r"^(具体|详细|细化|展开).{0,4}(说说|讲讲|看看|介绍)",
        r"^(这个|这些|那个|那些|它|它们)",
        r"^(呢|吗|吧)(\?|？)?$",
        r"^.*(呢|吗|吧)(\?|？)?$",  # 末尾语气词
    ]

    # 追问中包含主题词时的意图推断
    TOPIC_INTENT_MAP = {
        "论文": "paper_analysis",
        "文章": "paper_analysis",
        "paper": "paper_analysis",
        "sci": "paper_analysis",
        "经费": "funding_detail",
        "到账": "funding_detail",
        "支出": "funding_detail",
        "财务": "funding_detail",
        "项目": "project_query",
        "课题": "project_query",
        "获奖": "award_query",
        "奖项": "award_query",
        "荣誉": "award_query",
        "专利": "patent_analysis",
        "著作": "book_analysis",
        "书": "book_analysis",
        "软著": "software_analysis",
        "会议": "conference_analysis",
        "总结": "annual_summary",
        "年度": "annual_summary",
        "职称": "title_evaluation",
        "评审": "title_evaluation",
    }

    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl_seconds

    # ── 会话管理 ──

    def get_or_create(
        self,
        teacher_id: str,
        teacher_info: dict = None,
        session_id: str = None,
    ) -> Session:
        """
        获取或创建会话。
        优先用 session_id 查找，其次创建新会话（同一 teacher_id 复用旧会话）。
        """
        now = time.time()

        # 1. 优先按 session_id 查找
        if session_id and session_id in self._sessions:
            s = self._sessions[session_id]
            s.touch()
            return s

        # 2. 查找同一教师未过期的会话（复用）
        for sid, s in self._sessions.items():
            if s.teacher_id == teacher_id and (now - s.last_active) < self._ttl:
                s.touch()
                if teacher_info:
                    s.teacher_info = teacher_info
                return s

        # 3. 创建新会话
        new_session = Session(
            session_id=session_id or str(uuid.uuid4())[:8],
            teacher_id=teacher_id,
            teacher_info=teacher_info or {},
        )
        self._sessions[new_session.session_id] = new_session
        return new_session

    def get(self, session_id: str) -> Optional[Session]:
        s = self._sessions.get(session_id)
        if s:
            s.touch()
        return s

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str = None,
        metric_ids: list[str] = None,
        confidence: float = 1.0,
    ):
        """添加一轮对话"""
        s = self._sessions.get(session_id)
        if not s:
            return
        s.touch()
        s.history.append(ConversationTurn(
            role=role,
            content=content,
            intent=intent,
            metric_ids=metric_ids or [],
            confidence=confidence,
        ))
        # 限制历史长度（最近 20 轮）
        if len(s.history) > 20:
            s.history = s.history[-20:]

    def update_time_range(self, session_id: str, start_date: str, end_date: str):
        """更新时间范围（当用户追问时间时更新）"""
        s = self._sessions.get(session_id)
        if s:
            s.time_range = (start_date, end_date)

    # ── 追问检测 ──

    def is_followup(self, session_id: str, user_input: str) -> bool:
        """
        判断用户输入是否为追问（相对于上一轮）。

        规则：
        1. 没有提到教师工号/名字
        2. 匹配追问模式（开头或结尾）
        3. 句子较短（< 20 字，典型追问特征）
        """
        s = self._sessions.get(session_id)
        if not s or not s.history:
            return False

        text = user_input.strip()

        # 太长且包含完整描述 → 更可能是新问题
        if len(text) > 25:
            return False

        # 包含教师工号 → 新查询
        if re.search(r"GH\d{8}", text):
            return False

        # 匹配追问模式
        for pattern in self.FOLLOWUP_PATTERNS:
            if re.search(pattern, text):
                return True

        return False

    def infer_followup_intent(self, session_id: str, user_input: str) -> Optional[str]:
        """
        从追问中推断意图。
        先扫描主题词，没有则继承上一轮意图。
        """
        text = user_input.lower()

        # 扫描主题词
        for keyword, intent in self.TOPIC_INTENT_MAP.items():
            if keyword in text:
                return intent

        # 没有主题词 → 继承上一轮意图
        s = self._sessions.get(session_id)
        if s:
            return s.last_user_intent

        return None

    # ── 上下文构建 ──

    def build_context(self, session_id: str, user_input: str) -> dict:
        """
        为意图路由构建上下文。

        返回：
        {
            "is_followup": bool,
            "teacher_id": str,
            "teacher_info": dict,
            "time_range": (start, end),
            "suggested_intent": str | None,    # 追问时推断的意图
            "conversation_history": [str, ...], # 最近几轮对话摘要
            "last_metric_ids": [str, ...],
        }
        """
        s = self._sessions.get(session_id)
        if not s:
            return {"is_followup": False, "teacher_id": None}

        is_follow = self.is_followup(session_id, user_input)

        # 构建历史摘要（最近 6 轮）
        history_summary = []
        for turn in s.history[-6:]:
            prefix = "用户" if turn.role == "user" else "助手"
            summary = turn.content[:80] + ("..." if len(turn.content) > 80 else "")
            history_summary.append(f"{prefix}: {summary}")

        return {
            "is_followup": is_follow,
            "teacher_id": s.teacher_id,
            "teacher_info": s.teacher_info,
            "time_range": s.time_range,
            "suggested_intent": self.infer_followup_intent(session_id, user_input) if is_follow else None,
            "conversation_history": history_summary,
            "last_metric_ids": s.last_metric_ids,
        }

    # ── 维护 ──

    def cleanup_expired(self) -> int:
        """清理过期会话，返回清理数量"""
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if (now - s.last_active) > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    @property
    def active_count(self) -> int:
        return len(self._sessions)


# ── 全局单例 ──
_memory_instance: Optional[ConversationMemory] = None


def get_memory() -> ConversationMemory:
    """获取全局会话记忆实例"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory(ttl_seconds=3600)
    return _memory_instance
