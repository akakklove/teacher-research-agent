"""
JWT 认证模块 — 登录/注册、令牌签发/验证、角色权限

架构：
- 用户表：SQLite 存储（data/users.db）
- 教师初始密码：工号后 6 位（如 GH20200001 → 000001）
- 超管账号：admin / admin123
"""
import sqlite3
import hashlib
import time
import jwt
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "users.db"
JWT_SECRET = os.getenv("JWT_SECRET", "teacher-research-secret-key-2025")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


@dataclass
class User:
    id: int
    teacher_id: str
    name: str
    role: str           # "teacher" | "admin"
    department: str = ""


class AuthManager:
    """认证管理器"""

    def __init__(self, db_path: str = None):
        path = Path(db_path) if db_path else DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'teacher',
                    department TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.commit()
            # 种子数据：创建默认超管
            self._seed_admin(conn)

    def _seed_admin(self, conn):
        existing = conn.execute(
            "SELECT id FROM users WHERE teacher_id = 'admin'"
        ).fetchone()
        if not existing:
            pw = self._hash("admin123")
            conn.execute(
                "INSERT INTO users (teacher_id, name, password_hash, role) VALUES (?,?,?,?)",
                ("admin", "系统管理员", pw, "admin")
            )
            conn.commit()

    def sync_teachers(self, db_config: dict):
        """从 MySQL 教师表同步用户（教师初始密码 = 工号后 6 位）"""
        import pymysql
        conn = pymysql.connect(**db_config)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT gh, xm, dw_mc FROM t_jzg_jbxx")
                teachers = cursor.fetchall()
        finally:
            conn.close()

        with sqlite3.connect(self.db_path) as conn:
            for gh, xm, dw_mc in teachers:
                # 跳过已存在的
                exist = conn.execute(
                    "SELECT id FROM users WHERE teacher_id = ?", (gh,)
                ).fetchone()
                if exist:
                    continue
                # 密码 = 工号后 6 位
                default_pw = gh[-6:]
                pw_hash = self._hash(default_pw)
                conn.execute(
                    "INSERT INTO users (teacher_id, name, password_hash, role, department) VALUES (?,?,?,?,?)",
                    (gh, xm, pw_hash, "teacher", dw_mc or "")
                )
            conn.commit()
            return len(teachers)

    def login(self, teacher_id: str, password: str) -> Optional[dict]:
        """用户名密码登录 → 返回用户信息 + JWT"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE teacher_id = ?", (teacher_id,)
            ).fetchone()

        if not row:
            return None

        pw_hash = self._hash(password)
        if pw_hash != row[3]:  # password_hash 在索引 3
            return None

        user = User(
            id=row[0],
            teacher_id=row[1],
            name=row[2],
            role=row[4],
            department=row[5] or "",
        )

        token = self._create_token(user)
        return {
            "token": token,
            "user": {
                "teacher_id": user.teacher_id,
                "name": user.name,
                "role": user.role,
                "department": user.department,
            }
        }

    def verify_token(self, token: str) -> Optional[User]:
        """验证 JWT → 返回 User"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return User(
                id=0,
                teacher_id=payload.get("teacher_id", ""),
                name=payload.get("name", ""),
                role=payload.get("role", "teacher"),
                department=payload.get("department", ""),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def change_password(self, teacher_id: str, old_pw: str, new_pw: str) -> bool:
        """修改密码"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE teacher_id = ?", (teacher_id,)
            ).fetchone()
            if not row or row[0] != self._hash(old_pw):
                return False
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE teacher_id = ?",
                (self._hash(new_pw), teacher_id)
            )
            conn.commit()
            return True

    def _get_conn(self):
        """获取数据库连接（供外部查询使用）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── 工具 ──

    def _create_token(self, user: User) -> str:
        now = int(time.time())
        payload = {
            "teacher_id": user.teacher_id,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "iat": now,
            "exp": now + JWT_EXPIRE_HOURS * 3600,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


# ── FastAPI 依赖 ──
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """FastAPI 依赖：从 Authorization Header 提取当前用户"""
    auth = AuthManager()
    user = auth.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return user
