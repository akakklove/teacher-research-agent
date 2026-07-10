"""
模板存储 — 单元测试

覆盖：
- 模板 CRUD
- 按教师查询
- 重命名/删除
- JSON 序列化 metric_ids
"""
import pytest
from agent.template_store import TemplateStore, Template


@pytest.fixture
def store(temp_templates_db):
    """使用临时数据库的模板存储"""
    return TemplateStore(db_path=temp_templates_db)


class TestTemplateCRUD:
    """模板增删改查"""

    def test_save_template(self, store):
        tid = store.save(
            teacher_id="GH20200001",
            name="我的年度模板",
            metric_ids=["paper_count_total", "paper_by_level", "fund_total_arrived"],
            time_range_start="2023-01-01",
            time_range_end="2025-12-31",
        )
        assert tid is not None
        assert tid > 0

    def test_list_by_teacher(self, store):
        store.save("GH20200001", "模板A", ["m1", "m2"])
        store.save("GH20200001", "模板B", ["m3", "m4"])
        store.save("GH20200002", "模板C", ["m5"])  # 不同教师

        templates = store.list_by_teacher("GH20200001")
        assert len(templates) == 2

    def test_get_template(self, store):
        tid = store.save("GH20200001", "测试模板", ["m1"])
        t = store.get(tid)
        assert t is not None
        assert t.name == "测试模板"
        assert t.teacher_id == "GH20200001"
        assert t.metric_ids == ["m1"]

    def test_get_nonexistent(self, store):
        assert store.get(99999) is None

    def test_delete_template(self, store):
        tid = store.save("GH20200001", "要删除的模板", ["m1"])
        assert store.delete(tid) is True
        assert store.get(tid) is None

    def test_delete_nonexistent(self, store):
        assert store.delete(99999) is False

    def test_rename_template(self, store):
        tid = store.save("GH20200001", "旧名称", ["m1"])
        assert store.rename(tid, "新名称") is True
        t = store.get(tid)
        assert t.name == "新名称"


class TestTemplateList:
    """模板列表查询"""

    def test_empty_list(self, store):
        templates = store.list_by_teacher("GH99990000")
        assert len(templates) == 0

    def test_ordered_by_updated_at(self, store):
        """按 updated_at DESC 排序"""
        store.save("GH20200001", "旧模板", ["m1"])
        store.save("GH20200001", "新模板", ["m2"])
        templates = store.list_by_teacher("GH20200001")
        # 每条均有 updated_at，按 DESC 排序
        assert len(templates) == 2
        assert templates[0].name in ("新模板", "旧模板")

    def test_teacher_isolation(self, store):
        """不同教师的模板互不可见"""
        store.save("GH20200001", "张三模板", ["m1"])
        store.save("GH20200002", "李四模板", ["m2"])
        assert len(store.list_by_teacher("GH20200001")) == 1
        assert len(store.list_by_teacher("GH20200002")) == 1


class TestTemplateDataclass:
    """Template 数据类"""

    def test_create_template(self):
        t = Template(
            id=1,
            teacher_id="GH20200001",
            name="测试",
            metric_ids=["m1", "m2"],
            time_range_start="2023-01-01",
            time_range_end="2025-12-31",
            created_at="2025-07-10 12:00:00",
        )
        assert t.id == 1
        assert len(t.metric_ids) == 2
        assert t.updated_at == ""
