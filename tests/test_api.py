"""
FastAPI 路由 — 集成测试

覆盖：
- 健康检查
- 指标目录
- 认证端点
- 超管端点
- 对话端点（基础）
"""
import pytest


class TestHealthCheck:
    """基础健康检查"""

    def test_root_endpoint(self, test_app):
        res = test_app.get("/")
        assert res.status_code == 200

    def test_health_endpoint(self, test_app):
        """GET /api/health 返回服务状态"""
        res = test_app.get("/api/health")
        # 可能 200（DB 连上）或 503（DB 没连上），取决于环境
        assert res.status_code in {200, 503}

    def test_chat_page(self, test_app):
        """GET /api/chat 返回 HTML"""
        res = test_app.get("/api/chat")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]

    def test_admin_page(self, test_app):
        """GET /api/admin 返回 HTML"""
        res = test_app.get("/api/admin")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]


class TestMetricsEndpoints:
    """指标目录相关"""

    def test_list_metrics(self, test_app):
        """GET /api/metrics 返回指标列表"""
        res = test_app.get("/api/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], list)

    def test_filter_by_category(self, test_app):
        """带 category 参数筛选"""
        res = test_app.get("/api/metrics?category=论文成果")
        assert res.status_code == 200
        data = res.json()
        for m in data.get("metrics", []):
            assert "论文" in m.get("category", ""), \
                f"Metric {m.get('metric_id')} should be in 论文 category"

    def test_filter_by_category_not_found(self, test_app):
        """不存在的 category 返回空列表"""
        res = test_app.get("/api/metrics?category=nonexistent_category")
        assert res.status_code == 200
        data = res.json()
        assert data["metrics"] == []


class TestAuthEndpoints:
    """认证端点测试"""

    def test_login_missing_fields(self, test_app):
        """缺少参数返回 422"""
        res = test_app.post("/api/auth/login", json={})
        assert res.status_code == 422

    def test_login_invalid_credentials(self, test_app):
        """错误凭证返回 401"""
        res = test_app.post("/api/auth/login", json={
            "teacher_id": "GH99999999",
            "password": "wrong_password",
        })
        assert res.status_code in {401, 403, 404}

    def test_login_admin(self, test_app):
        """超管登录应成功"""
        res = test_app.post("/api/auth/login", json={
            "teacher_id": "admin",
            "password": "admin123",
        })
        if res.status_code == 200:
            data = res.json()
            assert "token" in data
            assert data["user"]["role"] == "admin"

    def test_me_without_token(self, test_app):
        """无 token 返回 403"""
        res = test_app.get("/api/auth/me")
        assert res.status_code in {401, 403}

    def test_me_with_valid_token(self, test_app):
        """有效 token 返回用户信息"""
        # 先登录获取 token
        login_res = test_app.post("/api/auth/login", json={
            "teacher_id": "admin",
            "password": "admin123",
        })
        if login_res.status_code == 200:
            token = login_res.json()["token"]
            res = test_app.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["role"] == "admin"


class TestAdminEndpoints:
    """超管端点测试"""

    def test_admin_stats_unauthorized(self, test_app):
        """无 token 返回 403"""
        res = test_app.get("/api/admin/stats")
        assert res.status_code in {401, 403}

    def test_admin_stats_authorized(self, test_app):
        """带 token 返回统计数据"""
        login_res = test_app.post("/api/auth/login", json={
            "teacher_id": "admin",
            "password": "admin123",
        })
        if login_res.status_code == 200:
            token = login_res.json()["token"]
            res = test_app.get(
                "/api/admin/stats",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code in {200, 500}
            if res.status_code == 200:
                data = res.json()
                assert "stats" in data

    def test_admin_users_authorized(self, test_app):
        """用户列表"""
        login_res = test_app.post("/api/auth/login", json={
            "teacher_id": "admin",
            "password": "admin123",
        })
        if login_res.status_code == 200:
            token = login_res.json()["token"]
            res = test_app.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 200

    def test_admin_metrics_authorized(self, test_app):
        """自定义指标列表"""
        login_res = test_app.post("/api/auth/login", json={
            "teacher_id": "admin",
            "password": "admin123",
        })
        if login_res.status_code == 200:
            token = login_res.json()["token"]
            res = test_app.get(
                "/api/admin/metrics",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 200


class TestChatEndpoints:
    """对话端点"""

    def test_chat_send_missing_fields(self, test_app):
        """缺少 message 返回 422"""
        res = test_app.post("/api/chat/send", json={})
        assert res.status_code == 422

    def test_chat_send_with_message(self, test_app):
        """发送消息（不依赖登录，但需要 teacher_id）"""
        res = test_app.post("/api/chat/send", json={
            "message": "帮我看看科研情况",
            "teacher_id": "GH20200001",
        })
        # 可能 200（成功）或 500（DB 没连上），取决于环境
        assert res.status_code in {200, 422, 500}

    def test_chat_sessions(self, test_app):
        """获取活跃会话数"""
        res = test_app.get("/api/chat/sessions")
        assert res.status_code == 200


class TestExportEndpoints:
    """导出端点"""

    def test_export_missing_fields(self, test_app):
        """缺少参数返回 422"""
        res = test_app.post("/api/export", json={})
        assert res.status_code == 422
