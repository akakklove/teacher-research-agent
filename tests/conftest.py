"""
测试配置与共享 Fixtures

用法：
    cd teacher-research-agent
    python -m pytest tests/ -v
    python -m pytest tests/ -v --tb=short          # 短回溯
    python -m pytest tests/ -v -k "intent"         # 只跑 intent 相关
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# 把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── SQLite 临时数据库 Fixtures ──

@pytest.fixture
def temp_db_dir():
    """创建临时 data 目录，自动清理"""
    d = tempfile.mkdtemp(prefix="tr_test_")
    data_dir = Path(d) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def temp_users_db(temp_db_dir):
    """临时用户数据库路径"""
    return str(temp_db_dir / "users.db")


@pytest.fixture
def temp_templates_db(temp_db_dir):
    """临时模板数据库路径"""
    return str(temp_db_dir / "templates.db")


@pytest.fixture
def temp_custom_metrics_db(temp_db_dir):
    """临时自定义指标数据库路径"""
    return str(temp_db_dir / "custom_metrics.db")


# ── 服务客户端 Fixture ──

@pytest.fixture
def test_app(temp_db_dir):
    """返回 FastAPI TestClient（使用临时数据库，避免污染真实数据）"""
    # 临时替换 DB 路径环境变量
    os.environ["TR_USER_DB"] = str(temp_db_dir / "users.db")
    os.environ["TR_TEMPLATE_DB"] = str(temp_db_dir / "templates.db")
    os.environ["TR_CUSTOM_METRICS_DB"] = str(temp_db_dir / "custom_metrics.db")

    from data_service.api import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
