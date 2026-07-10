"""
大屏编排引擎 — 指标结果 → ECharts 配置 → 完整 HTML 页面
"""
import json
from pathlib import Path
from decimal import Decimal
from jinja2 import Template


class CustomEncoder(json.JSONEncoder):
    """处理 MySQL DECIMAL / date 类型的 JSON 序列化"""
    def default(self, obj):
        from decimal import Decimal
        from datetime import date, datetime
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return str(obj)
        return super().default(obj)


class DashboardComposer:
    """
    大屏编排器
    用法：
        composer = DashboardComposer()
        html = composer.render(teacher, metrics, insights)
        # → 完整 HTML 字符串，直接返回给浏览器
    """

    # 图表配色（中国高校科研风格）
    COLORS = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
        "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16"
    ]

    def render(
        self,
        teacher: dict,
        metrics: list,     # MetricResult 列表
        insights: list[str] = None,
        start_date: str = "2022-01-01",
        end_date: str = "2025-12-31",
    ) -> str:
        """生成完整大屏 HTML"""
        # 分离 KPI 卡片和图表
        kpi_metrics = [m for m in metrics if m.chart_type == "kpi_card" and m.success]
        chart_metrics = [m for m in metrics if m.chart_type != "kpi_card" and m.success and m.rows]

        # 生成 ECharts 配置
        charts_config = []
        for i, m in enumerate(chart_metrics):
            option = self._build_chart_option(m, i)
            if option:
                cfg = {
                    "dom_id": f"chart_{i}",
                    "title": m.name,
                    "chart_type": m.chart_type,
                }
                if m.chart_type == "table":
                    cfg["option"] = option  # 表格保留原始 dict
                else:
                    cfg["option"] = json.dumps(option, ensure_ascii=False, cls=CustomEncoder)
                charts_config.append(cfg)

        # 加载 HTML 模板
        template_path = Path(__file__).parent.parent / "dashboard" / "templates" / "dashboard.html"
        template = Template(template_path.read_text(encoding="utf-8"))

        return template.render(
            teacher=teacher,
            teacher_name=teacher.get("xm", ""),
            teacher_dept=teacher.get("dw_mc", ""),
            teacher_title=teacher.get("zc", ""),
            time_range=f"{start_date} 至 {end_date}",
            kpis=kpi_metrics,
            charts=charts_config,
            charts_json=json.dumps(charts_config, ensure_ascii=False, cls=CustomEncoder) if charts_config else "[]",
            insights=insights or [],
        )

    def _build_chart_option(self, metric, index: int) -> dict:
        """单指标 → ECharts option"""
        ct = metric.chart_type
        rows = metric.rows
        if not rows:
            return {}

        if ct == "line_chart":
            return self._build_line(metric, rows)
        elif ct == "bar_chart":
            return self._build_bar(metric, rows)
        elif ct == "pie_chart":
            return self._build_pie(metric, rows)
        elif ct == "horizontal_bar":
            return self._build_hbar(metric, rows)
        elif ct == "gauge":
            return self._build_gauge(metric, rows)
        elif ct == "table":
            return self._build_table(metric, rows)
        return {}

    def _build_line(self, metric, rows):
        labels = [r.get("label", "") for r in rows]
        values = [r.get("value", 0) for r in rows]
        return {
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 60, "right": 30, "top": 40, "bottom": 30},
            "xAxis": {"type": "category", "data": labels},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "line",
                "data": values,
                "smooth": True,
                "itemStyle": {"color": self.COLORS[0]},
                "areaStyle": {"color": "rgba(59,130,246,0.1)"},
            }],
        }

    def _build_bar(self, metric, rows):
        labels = [r.get("label", "") for r in rows]
        values = [r.get("value", 0) for r in rows]
        return {
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 60, "right": 30, "top": 40, "bottom": 30},
            "xAxis": {"type": "category", "data": labels, "axisLabel": {"rotate": 20}},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "bar",
                "data": values,
                "itemStyle": {"color": self.COLORS[1], "borderRadius": [4, 4, 0, 0]},
            }],
        }

    def _build_pie(self, metric, rows):
        data = [{"name": r.get("label", ""), "value": r.get("value", 0)} for r in rows]
        return {
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "55%"],
                "data": data,
                "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                "label": {"formatter": "{b}\n{d}%"},
            }],
            "color": self.COLORS,
        }

    def _build_hbar(self, metric, rows):
        labels = [r.get("label", "") for r in rows]
        values = [r.get("value", 0) for r in rows]
        return {
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 100, "right": 30, "top": 20, "bottom": 20},
            "xAxis": {"type": "value"},
            "yAxis": {"type": "category", "data": labels, "inverse": True},
            "series": [{
                "type": "bar",
                "data": values,
                "itemStyle": {"color": self.COLORS[2], "borderRadius": [0, 4, 4, 0]},
            }],
        }

    def _build_gauge(self, metric, rows):
        value = metric.value or 0
        return {
            "series": [{
                "type": "gauge",
                "startAngle": 210, "endAngle": -30,
                "center": ["50%", "60%"],
                "radius": "85%",
                "min": 0, "max": 100,
                "axisLine": {"lineStyle": {"width": 15, "color": [
                    [0.3, "#EF4444"], [0.7, "#F59E0B"], [1, "#10B981"]
                ]}},
                "pointer": {"length": "70%", "width": 6},
                "detail": {"valueAnimation": True, "formatter": "{value}%", "fontSize": 24},
                "data": [{"value": value, "name": metric.name}],
            }]
        }

    def _build_table(self, metric, rows):
        # 表格渲染在前端直接做，这里返回原始数据
        return {"columns": list(rows[0].keys()) if rows else [], "rows": rows}
