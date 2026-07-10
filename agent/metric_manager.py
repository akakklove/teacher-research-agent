"""
指标管理器 — 自定义指标的持久化存储（SQLite）

超管可以新增/编辑/删除自定义指标，系统自动合并 YAML 指标 + 自定义指标。
"""
import sqlite3
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "custom_metrics.db"


@dataclass
class CustomMetric:
    id: int
    metric_id: str
    name: str
    category: str
    chart_type: str
    unit: str
    sql_template: str
    description: str = ""
    created_at: str = ""


class MetricManager:
    """自定义指标管理器"""

    def __init__(self, db_path: str = None):
        path = Path(db_path) if db_path else DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '自定义',
                    chart_type TEXT NOT NULL DEFAULT 'table',
                    unit TEXT DEFAULT '',
                    sql_template TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.commit()

    def save(self, metric_id: str, name: str, sql_template: str,
             category: str = "自定义", chart_type: str = "table",
             unit: str = "", description: str = "") -> int:
        """新增或更新自定义指标"""
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM custom_metrics WHERE metric_id = ?",
                (metric_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE custom_metrics SET name=?,category=?,chart_type=?,
                       unit=?,sql_template=?,description=?
                       WHERE metric_id=?""",
                    (name, category, chart_type, unit, sql_template, description, metric_id)
                )
            else:
                conn.execute(
                    """INSERT INTO custom_metrics (metric_id,name,category,chart_type,
                       unit,sql_template,description) VALUES (?,?,?,?,?,?,?)""",
                    (metric_id, name, category, chart_type, unit, sql_template, description)
                )
            conn.commit()
            return existing[0] if existing else conn.execute(
                "SELECT id FROM custom_metrics WHERE metric_id = ?", (metric_id,)
            ).fetchone()[0]

    def list_all(self) -> list[dict]:
        """列出所有自定义指标"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM custom_metrics ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, metric_id: str) -> bool:
        """删除自定义指标"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM custom_metrics WHERE metric_id = ?", (metric_id,))
            conn.commit()
            return conn.total_changes > 0

    def load_all(self) -> dict:
        """加载所有自定义指标（格式与 metrics.yaml 兼容）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM custom_metrics").fetchall()
        result = {}
        for r in rows:
            result[r["metric_id"]] = {
                "id": r["metric_id"],
                "name": r["name"],
                "category": r["category"],
                "chart_type": r["chart_type"],
                "unit": r["unit"],
                "sql_template": r["sql_template"],
                "description": r["description"],
                "_custom": True,
            }
        return result
