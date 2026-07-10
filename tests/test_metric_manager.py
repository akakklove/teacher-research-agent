"""
自定义指标管理 — 单元测试

覆盖：
- 指标 CRUD（增删改查）
- YAML 兼容格式输出（load_all）
- 覆盖已存在指标
"""
import pytest
from agent.metric_manager import MetricManager


@pytest.fixture
def manager(temp_custom_metrics_db):
    """使用临时数据库的指标管理器"""
    return MetricManager(db_path=temp_custom_metrics_db)


class TestMetricCRUD:
    """自定义指标增删改查"""

    def test_save_metric(self, manager):
        manager.save(
            metric_id="test_my_metric",
            name="测试指标",
            sql_template="SELECT COUNT(*) FROM t_ky_lw WHERE zgh = :teacher_id",
            category="自定义",
            chart_type="bar_chart",
            unit="个",
            description="单元测试指标",
        )
        all_metrics = manager.load_all()
        assert "test_my_metric" in all_metrics

    def test_save_overwrites_existing(self, manager):
        """覆盖已存在指标"""
        manager.save("dup_metric", "v1", "SELECT 1")
        manager.save("dup_metric", "v2", "SELECT 2")
        all_metrics = manager.load_all()
        assert all_metrics["dup_metric"]["name"] == "v2"

    def test_list_all(self, manager):
        manager.save("m1", "指标1", "SELECT 1")
        manager.save("m2", "指标2", "SELECT 2")
        all_list = manager.list_all()
        assert len(all_list) == 2

    def test_delete_metric(self, manager):
        manager.save("to_delete", "待删除", "SELECT 1")
        assert "to_delete" in manager.load_all()
        manager.delete("to_delete")
        assert "to_delete" not in manager.load_all()

    def test_delete_nonexistent(self, manager):
        # 不应抛异常
        result = manager.delete("nonexistent")
        assert result is False  # delete returns bool

    def test_load_all_empty(self, manager):
        """空数据库应返回空字典"""
        assert manager.load_all() == {}


class TestMetricFormat:
    """load_all() 输出格式验证"""

    def test_loaded_metric_uses_id_key(self, manager):
        """load_all 的每条指标用 'id' 作 key（与 metrics.yaml 格式兼容）"""
        manager.save(
            "fmt_test", "格式测试", "SELECT 1",
            category="测试", chart_type="table",
            unit="次", description="描述文本",
        )
        m = manager.load_all()["fmt_test"]
        assert m["id"] == "fmt_test"
        assert m["name"] == "格式测试"
        assert m["category"] == "测试"
        assert m["chart_type"] == "table"
        assert m["sql_template"] == "SELECT 1"
        assert m["unit"] == "次"
        assert m["description"] == "描述文本"

    def test_metric_without_unit_has_empty_default(self, manager):
        manager.save("no_unit", "无单位", "SELECT 1")
        m = manager.load_all()["no_unit"]
        assert m.get("unit", "") == ""

    def test_metric_marked_as_custom(self, manager):
        """load_all 的自定义指标有 _custom: True 标记"""
        manager.save("custom_m", "自定义", "SELECT 1")
        m = manager.load_all()["custom_m"]
        assert m.get("_custom") is True


class TestSaveSQLOnlyRequired:
    """save() 只要求 metric_id, name, sql_template"""

    def test_minimal_save(self, manager):
        manager.save("minimal", "极简指标", "SELECT 1")
        m = manager.load_all()["minimal"]
        assert m["name"] == "极简指标"
        assert m["sql_template"] == "SELECT 1"
        assert m["category"] == "自定义"  # 默认值
        assert m["chart_type"] == "table"  # 默认值
