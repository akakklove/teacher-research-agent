"""
模板存储 — 教师自定义指标模板的持久化存储（SQLite）

支持：
- 保存模板（名称 + 指标ID列表 + 时间范围）
- 按教师查询模板列表
- 加载单个模板
- 删除/重命名模板
"""
import sqlite3
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


DB_PATH = Path(__file__).parent.parent / "data" / "templates.db"


@dataclass
class Template:
    """用户自定义模板"""
    id: int
    teacher_id: str
    name: str
    metric_ids: list[str]
    time_range_start: str       # YYYY-MM-DD
    time_range_end: str
    created_at: str
    updated_at: str = ""


class TemplateStore:
    """
    模板存储引擎

    用法：
        store = TemplateStore()
        store.save(teacher_id="GH20200001", name="我的年度模板", metric_ids=[...])
        templates = store.list_by_teacher("GH20200001")
    """

    def __init__(self, db_path: str = None):
        path = Path(db_path) if db_path else DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    metric_ids TEXT NOT NULL,       -- JSON array
                    time_range_start TEXT NOT NULL,
                    time_range_end TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_teacher_id ON templates(teacher_id)
            """)
            conn.commit()

    # ── CRUD ──

    def save(
        self,
        teacher_id: str,
        name: str,
        metric_ids: list[str],
        time_range_start: str = "2022-01-01",
        time_range_end: str = "2025-12-31",
    ) -> int:
        """保存模板，返回模板ID"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO templates (teacher_id, name, metric_ids, time_range_start, time_range_end, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (teacher_id, name, json.dumps(metric_ids), time_range_start, time_range_end, now, now)
            )
            conn.commit()
            return cursor.lastrowid

    def list_by_teacher(self, teacher_id: str) -> list[Template]:
        """列出某教师的所有模板"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM templates WHERE teacher_id = ? ORDER BY updated_at DESC",
                (teacher_id,)
            ).fetchall()
        return [self._row_to_template(r) for r in rows]

    def get(self, template_id: int) -> Optional[Template]:
        """获取单个模板"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM templates WHERE id = ?", (template_id,)
            ).fetchone()
        return self._row_to_template(row) if row else None

    def rename(self, template_id: int, new_name: str) -> bool:
        """重命名模板"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE templates SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, now, template_id)
            )
            conn.commit()
            return conn.total_changes > 0

    def delete(self, template_id: int) -> bool:
        """删除模板"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            return conn.total_changes > 0

    # ── 工具 ──

    @staticmethod
    def _row_to_template(row) -> Template:
        return Template(
            id=row["id"],
            teacher_id=row["teacher_id"],
            name=row["name"],
            metric_ids=json.loads(row["metric_ids"]),
            time_range_start=row["time_range_start"],
            time_range_end=row["time_range_end"],
            created_at=row["created_at"],
            updated_at=row["updated_at"] if "updated_at" in row.keys() else "",
        )
