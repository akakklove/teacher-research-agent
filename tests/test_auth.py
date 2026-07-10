"""
JWT 认证 — 单元测试

覆盖：
- 密码哈希/验证
- 登录/Token 签发/验证
- 超管种子数据
- Token 过期
"""
import os
import pytest
from agent.auth import AuthManager, User, JWT_SECRET


@pytest.fixture
def auth(temp_users_db):
    """使用临时数据库的 AuthManager"""
    return AuthManager(db_path=temp_users_db)


# ── 密码哈希 ──

class TestPasswordHashing:
    """SHA-256 密码哈希（私有方法 _hash）"""

    def test_hash_deterministic(self, auth):
        h1 = auth._hash("mypassword")
        h2 = auth._hash("mypassword")
        assert h1 == h2

    def test_hash_different(self, auth):
        h1 = auth._hash("password1")
        h2 = auth._hash("password2")
        assert h1 != h2

    def test_hash_not_plaintext(self, auth):
        h = auth._hash("mypassword")
        assert "mypassword" not in h
        assert len(h) == 64  # SHA-256 hex = 64 chars


# ── 登录验证 ──

class TestLogin:
    """登录流程 — login() 返回 dict 或 None"""

    def test_admin_login(self, auth):
        result = auth.login("admin", "admin123")
        assert result is not None
        assert isinstance(result, dict)
        assert "token" in result
        assert result["user"]["role"] == "admin"

    def test_admin_wrong_password(self, auth):
        result = auth.login("admin", "wrong_password")
        assert result is None

    def test_nonexistent_user(self, auth):
        result = auth.login("GH99999999", "anypassword")
        assert result is None


# ── JWT Token ──

class TestJWT:
    """JWT 签发与验证"""

    def test_admin_token_verifiable(self, auth):
        result = auth.login("admin", "admin123")
        assert result is not None
        token = result["token"]
        user = auth.verify_token(token)
        assert user is not None
        assert user.teacher_id == "admin"
        assert user.role == "admin"

    def test_invalid_token(self, auth):
        user = auth.verify_token("invalid.token.here")
        assert user is None

    def test_tampered_token(self, auth):
        """篡改过的 token 应返回 None"""
        result = auth.login("admin", "admin123")
        assert result is not None
        token = result["token"]
        parts = token.split(".")
        # 修改 payload 部分 1 个字符
        tampered = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        bad_token = ".".join([parts[0], tampered, parts[2]])
        user = auth.verify_token(bad_token)
        assert user is None

    def test_expired_token(self, auth):
        """过期 token 应返回 None"""
        # 手动构造过期 token（exp = 过去时间）
        import jwt as pyjwt
        import time
        token = pyjwt.encode(
            {
                "teacher_id": "admin",
                "role": "admin",
                "exp": int(time.time()) - 3600,  # 1 小时前过期
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        # PyJWT v2.x 返回 str
        user = auth.verify_token(token if isinstance(token, str) else token.decode())
        assert user is None


# ── 密码修改 ──

class TestPasswordChange:
    """change_password 方法"""

    def test_change_password_success(self, auth):
        assert auth.change_password("admin", "admin123", "newpass456") is True
        # 旧密码不应再可用
        assert auth.login("admin", "admin123") is None
        # 新密码可用
        result = auth.login("admin", "newpass456")
        assert result is not None

    def test_change_password_wrong_old(self, auth):
        assert auth.change_password("admin", "wrong_old_password", "newpass") is False


# ── User 数据类 ──

class TestUserDataclass:
    """User 数据类"""

    def test_create_user(self):
        u = User(id=1, teacher_id="GH99990001", name="张三", role="teacher")
        assert u.id == 1
        assert u.teacher_id == "GH99990001"
        assert u.department == ""

    def test_user_with_department(self):
        u = User(
            id=2, teacher_id="GH99990002", name="李四",
            role="teacher", department="计算机学院",
        )
        assert u.department == "计算机学院"


# ── 种子管理员 ──

class TestSeedAdmin:
    """种子管理员默认存在"""

    def test_seed_admin_exists(self, auth):
        """超管种子账号在数据库中"""
        import sqlite3
        with sqlite3.connect(auth.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE teacher_id = 'admin'"
            ).fetchone()
            assert row is not None
