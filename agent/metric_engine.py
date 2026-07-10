"""
指标查询引擎 — 读取 metrics.yaml，对 MySQL 执行查询，返回结构化结果。
"""
import yaml
import pymysql
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class MetricResult:
    """单个指标的计算结果"""
    metric_id: str
    name: str
    category: str
    chart_type: str  # kpi_card / line_chart / bar_chart / pie_chart / gauge / table
    unit: str = ""
    value: Optional[float] = None       # KPI 类指标的值
    rows: list = field(default_factory=list)  # 分布/趋势类指标的多行结果
    sql: str = ""                        # 实际执行的 SQL（调试用）
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class MetricEngine:
    """指标查询引擎"""

    def __init__(self, db_config: dict, metrics_path: str = None):
        self.db_config = db_config
        self._conn = None

        # 加载指标定义
        if metrics_path is None:
            metrics_path = Path(__file__).parent / "metrics.yaml"
        with open(metrics_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self._metrics = {m["id"]: m for m in config["metrics"]}

    # ── 数据库连接 ──
    @property
    def conn(self):
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(**self.db_config)
        return self._conn

    def close(self):
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    # ── 查询 API ──
    def list_metrics(self) -> list[dict]:
        """列出所有可用指标（供前端展示指标超市）"""
        return [{
            "id": m["id"],
            "name": m["name"],
            "category": m["category"],
            "description": m.get("description", ""),
            "chart_type": m.get("chart_type", "table"),
            "unit": m.get("unit", ""),
        } for m in self._metrics.values()]

    def list_categories(self) -> list[str]:
        """列出所有指标分类"""
        cats = []
        for m in self._metrics.values():
            if m["category"] not in cats:
                cats.append(m["category"])
        return cats

    def get_metric_definition(self, metric_id: str) -> dict:
        """获取单个指标的完整定义"""
        return self._metrics.get(metric_id, {})

    def execute(
        self,
        teacher_id: str,
        metric_ids: list[str] = None,
        params: dict = None,
    ) -> list[MetricResult]:
        """
        批量执行指标查询

        Args:
            teacher_id: 教师工号，如 "GH20200001"
            metric_ids: 要查询的指标ID列表，None=查全部
            params: 额外参数 {"start_date": "2022-01-01", "end_date": "2025-12-31", ...}

        Returns:
            MetricResult 列表
        """
        if params is None:
            params = {}

        # 合并默认参数
        merged_params = {
            ":teacher_id": f"'{teacher_id}'",
            ":start_date": f"'{params.get('start_date', '2022-01-01')}'",
            ":end_date": f"'{params.get('end_date', '2025-12-31')}'",
            ":start_year": f"'{params.get('start_year', '2022')}'",
            ":end_year": f"'{params.get('end_year', '2025')}'",
        }

        # 选择要执行的指标
        if metric_ids is None:
            metric_ids = list(self._metrics.keys())
        selected = [self._metrics[mid] for mid in metric_ids if mid in self._metrics]

        results = []
        with self.conn.cursor() as cursor:
            for m in selected:
                result = self._execute_one(cursor, m, merged_params)
                results.append(result)

        return results

    def _execute_one(self, cursor, metric_def: dict, params: dict) -> MetricResult:
        """执行单个指标查询"""
        sql = metric_def["sql_template"]
        for k, v in params.items():
            sql = sql.replace(k, v)

        try:
            cursor.execute(sql)
            rows = cursor.fetchall()

            r = MetricResult(
                metric_id=metric_def["id"],
                name=metric_def["name"],
                category=metric_def["category"],
                chart_type=metric_def.get("chart_type", "table"),
                unit=metric_def.get("unit", ""),
                sql=sql,
            )

            # 根据图表类型决定如何解析结果
            ct = r.chart_type
            if ct == "kpi_card":
                if rows and len(rows[0]) == 1:
                    r.value = float(rows[0][0]) if rows[0][0] is not None else 0.0
                else:
                    r.value = 0.0
            elif ct == "gauge":
                # gauge 类型可能有多个字段，取第一个数值字段作为 value
                if rows and len(rows[0]) >= 1:
                    r.value = float(rows[0][0]) if rows[0][0] is not None else 0.0
                else:
                    r.value = 0.0
                # 附加其他字段
                if rows:
                    r.rows = [dict(zip([d[0] for d in cursor.description], row)) for row in rows]
            else:
                # 分布/趋势类：保留所有行
                r.rows = [dict(zip([d[0] for d in cursor.description], row)) for row in rows]
                if r.rows:
                    r.value = len(r.rows)

            return r

        except Exception as e:
            r = MetricResult(
                metric_id=metric_def["id"],
                name=metric_def["name"],
                category=metric_def["category"],
                chart_type=metric_def.get("chart_type", "table"),
                error=str(e),
            )
            return r

    def get_teacher_info(self, teacher_id: str) -> dict:
        """获取教师基本信息"""
        sql = """
            SELECT gh, xm, xb, dw_bm, dw_mc, zc, xkml_bm, ryrq
            FROM t_jzg_jbxx WHERE gh = %s
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (teacher_id,))
            row = cursor.fetchone()
            if row:
                cols = [d[0] for d in cursor.description]
                return dict(zip(cols, row))
        return {}
