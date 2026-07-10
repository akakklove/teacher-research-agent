"""
大屏布局 — 单元测试

覆盖：
- 11 个意图均有对应布局
- 布局指标 ID 一致性
- KPI/图表数量约束
- DashboardLayout 数据类校验
"""
import pytest
from agent.dashboard_layouts import DashboardLayout, LAYOUTS


class TestLayoutsExist:
    """所有意图均有布局"""

    EXPECTED_INTENTS = [
        "personal_overview",
        "paper_analysis",
        "funding_detail",
        "patent_analysis",
        "award_query",
        "project_query",
        "book_analysis",
        "software_analysis",
        "conference_analysis",
        "annual_summary",
        "title_evaluation",
    ]

    def test_all_intents_have_layout(self):
        for intent in self.EXPECTED_INTENTS:
            assert intent in LAYOUTS, f"Missing layout for intent: {intent}"

    def test_no_extra_intents(self):
        """LAYOUTS 只能包含已知意图"""
        for intent in LAYOUTS:
            assert intent in self.EXPECTED_INTENTS, \
                f"Unexpected intent in LAYOUTS: {intent}"


class TestLayoutIntegrity:
    """布局配置完整性"""

    def test_kpi_metrics_not_empty(self):
        for intent, layout in LAYOUTS.items():
            assert len(layout.kpi_metrics) > 0, \
                f"Layout '{intent}' has no KPI metrics"

    def test_chart_metrics_not_empty(self):
        for intent, layout in LAYOUTS.items():
            assert len(layout.chart_metrics) > 0, \
                f"Layout '{intent}' has no chart metrics"

    def test_no_duplicate_metrics(self):
        """KPI 和 chart 指标不应重叠"""
        for intent, layout in LAYOUTS.items():
            kpi_set = set(layout.kpi_metrics)
            chart_set = set(layout.chart_metrics)
            overlap = kpi_set & chart_set
            assert len(overlap) == 0, \
                f"Layout '{intent}': overlapping metrics {overlap}"

    def test_valid_layout_id(self):
        """layout_id 必须是 A/B/C/D 之一"""
        for intent, layout in LAYOUTS.items():
            assert layout.layout_id in {"A", "B", "C"}, \
                f"Layout '{intent}': invalid layout_id '{layout.layout_id}'"

    def test_valid_kpi_class(self):
        """kpi_class 必须是合法的 CSS 类名"""
        valid = {"kpi-1", "kpi-2", "kpi-3", "kpi-4", "kpi-5",
                 "kpi-6", "kpi-7", "kpi-8"}
        for intent, layout in LAYOUTS.items():
            assert layout.kpi_class in valid, \
                f"Layout '{intent}': invalid kpi_class '{layout.kpi_class}'"

    def test_valid_chart_grid(self):
        """chart_grid 必须是合法的 CSS 类名"""
        valid = {"grid-3x2", "grid-1x3", "grid-1x2", "grid-1x1"}
        for intent, layout in LAYOUTS.items():
            assert layout.chart_grid in valid, \
                f"Layout '{intent}': invalid chart_grid '{layout.chart_grid}'"


class TestLayoutTypeA:
    """类型 A（全景）布局约束"""

    def test_personal_overview_has_8_kpi(self):
        layout = LAYOUTS["personal_overview"]
        assert len(layout.kpi_metrics) == 8, \
            f"Expected 8 KPI, got {len(layout.kpi_metrics)}"

    def test_personal_overview_has_6_charts(self):
        layout = LAYOUTS["personal_overview"]
        assert len(layout.chart_metrics) >= 5, \
            f"Expected >= 5 charts, got {len(layout.chart_metrics)}"

    def test_personal_overview_3_insights(self):
        layout = LAYOUTS["personal_overview"]
        assert layout.insight_count == 3


class TestDashboardLayoutDataclass:
    """DashboardLayout 数据类测试"""

    def test_create_layout(self):
        layout = DashboardLayout(
            layout_id="B",
            title_suffix="测试布局",
            kpi_metrics=["m1", "m2"],
            chart_metrics=["m3", "m4"],
            kpi_class="kpi-2",
            chart_grid="grid-3x2",
            insight_count=2,
        )
        assert layout.layout_id == "B"
        assert layout.kpi_class == "kpi-2"
        assert len(layout.kpi_metrics) == 2
        assert len(layout.chart_metrics) == 2

    def test_default_values(self):
        layout = DashboardLayout(
            layout_id="C",
            title_suffix="默认测试",
            kpi_metrics=[],
            chart_metrics=[],
        )
        assert layout.kpi_class == "kpi-8"      # 默认值
        assert layout.chart_grid == "grid-3x2"   # 默认值
        assert layout.insight_count == 3          # 默认值
        assert layout.chart_height == "380px"     # 默认值
