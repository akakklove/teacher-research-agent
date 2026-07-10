"""
指标自动发现 — 当注册表中没有对应指标时，自动探索 Schema 生成 SQL。

核心流程：
1. 加载 Schema 注册中心 → 构建表/字段索引
2. 用户自然语言问题 → LLM 匹配表+字段 → 生成 SQL
3. 执行 SQL → 返回结果（含图表类型建议）
"""
import json
import re
import pymysql
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiscoveredMetric:
    """自动发现的指标"""
    name: str                    # 自动生成的指标名称
    sql: str                     # LLM 生成的 SQL
    chart_type: str = "table"    # 推荐的图表类型
    explanation: str = ""        # LLM 对 SQL 的解释
    tables_used: list[str] = field(default_factory=list)
    error: Optional[str] = None


class SchemaExplorer:
    """
    Schema 浏览器 — 加载数据库表结构，提供 LLM 友好的文本摘要。

    用法：
        explorer = SchemaExplorer()
        summary = explorer.get_schema_summary()
        # → 包含所有表的名称、业务描述、字段列表的紧凑文本
        tables = explorer.search("论文")  # 搜索包含"论文"关键词的表
    """

    def __init__(self, schema_dir: str = None):
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "data_governance" / "schema_registry"
        self.schema_dir = Path(schema_dir)
        self._tables: dict = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        # 只加载 GXKY 科研管理数据集（19 张表）
        gxky_path = self.schema_dir / "GXKY科研管理数据集.json"
        if gxky_path.exists():
            with open(gxky_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._tables = data.get("tables", {})
        self._loaded = True

    def get_schema_summary(self) -> str:
        """
        生成 Schema 文本摘要，供 LLM Prompt 使用。

        格式：
        表名: t_ky_xmjbxx
          业务描述: 科研项目基本信息...
          字段:
            - XMBH (项目编号, 字符串, PK)
            - XMMC (项目名称, 字符串)
            ...
        """
        self._ensure_loaded()
        lines = []

        for table_name, table_def in self._tables.items():
            # 转为小写表名（匹配实际 MySQL 表名）
            short_name = self._to_short_name(table_name)
            biz_desc = table_def.get("biz_desc", table_def.get("entity_desc", ""))
            biz_desc_short = biz_desc[:120].replace("\n", " ")

            lines.append(f"表: {short_name}")
            lines.append(f"  描述: {biz_desc_short}")

            fields = table_def.get("fields", [])
            field_lines = []
            for f in fields:
                name = f.get("name", "")
                comment = f.get("comment", "")
                ftype = f.get("type", "")
                is_pk = "PK" if f.get("is_pk") else ""
                parts = [name]
                if comment:
                    parts.append(comment)
                if ftype:
                    parts.append(ftype)
                if is_pk:
                    parts.append(is_pk)
                field_lines.append(f"    - {' | '.join(parts)}")

            # 限制每个表最多 15 个字段（避免 Prompt 过长）
            if len(field_lines) > 15:
                field_lines = field_lines[:15]
                field_lines.append(f"    ... 共 {len(fields)} 个字段")

            lines.extend(field_lines)
            lines.append("")

        return "\n".join(lines)

    def search(self, keyword: str) -> list[dict]:
        """搜索包含关键词的表/字段"""
        self._ensure_loaded()
        results = []
        keyword_lower = keyword.lower()

        for table_name, table_def in self._tables.items():
            short_name = self._to_short_name(table_name)
            biz_desc = table_def.get("biz_desc", "") + table_def.get("entity_desc", "")

            # 匹配业务描述
            if keyword_lower in biz_desc.lower() or keyword_lower in short_name.lower():
                results.append({
                    "table": short_name,
                    "description": biz_desc[:100],
                    "match": "table_desc",
                })
                continue

            # 匹配字段名/注释
            fields = table_def.get("fields", [])
            matched_fields = []
            for f in fields:
                f_name = f.get("name", "").lower()
                f_comment = f.get("comment", "").lower()
                if keyword_lower in f_name or keyword_lower in f_comment:
                    matched_fields.append({
                        "name": f.get("name"),
                        "comment": f.get("comment"),
                        "type": f.get("type"),
                    })

            if matched_fields:
                results.append({
                    "table": short_name,
                    "description": biz_desc[:100],
                    "match": "field",
                    "matched_fields": matched_fields,
                })

        return results

    # Schema表名 → MySQL表名 映射
    SCHEMA_TO_MYSQL = {
        "T_GXKY_KYJGJBXX": "t_ky_kyjg",
        "T_GXKY_KYJGRYXX": "t_ky_kyjgry",
        "T_GXKY_KYXMJBXX": "t_ky_xmjbxx",
        "T_GXKY_KYXMRYXX": "t_ky_xmry",
        "T_GXKY_KYJFZCXX": "t_ky_jfzc",
        "T_GXKY_KYJFDZXX": "t_ky_jfdz",
        "T_GXKY_KYJFWBXX": "t_ky_jfwb",
        "T_GXKY_KYLWXX": "t_ky_lw",
        "T_GXKY_KYLWZZXX": "t_ky_lwzz",
        "T_GXKY_KYZZXX": "t_ky_zz",
        "T_GXKY_KYZZZZXX": "t_ky_zzzz",
        "T_GXKY_KYZLXX": "t_ky_zl",
        "T_GXKY_KYZLFMRXX": "t_ky_zlfmr",
        "T_GXKY_KYRJZZXX": "t_ky_rjzz",
        "T_GXKY_KYRJZZCYXX": "t_ky_rjzzcy",
        "T_GXKY_KYHJXX": "t_ky_hj",
        "T_GXKY_KYHJCYXX": "t_ky_hjry",  # 获奖人员，实际表名 hjry
        "T_GXKY_KYXSHYXX": "t_ky_xshy",
        "T_GXKY_JZGJBXX": "t_jzg_jbxx",
    }

    @classmethod
    def _to_short_name(cls, full_name: str) -> str:
        """T_GXKY_KYJGJBXX → t_ky_kyjg"""
        # 优先查映射表
        if full_name in cls.SCHEMA_TO_MYSQL:
            return cls.SCHEMA_TO_MYSQL[full_name]

        # 兜底规则
        name = full_name.lower()
        # 移除 T_GXKY_ 前缀
        name = re.sub(r"^t_gxky_", "t_ky_", name)
        # 移除 XX 后缀（信息表标记）
        name = re.sub(r"xx$", "", name)
        return name


class MetricDiscovery:
    """
    指标自动发现引擎

    用法：
        discovery = MetricDiscovery(llm=chat_model)
        result = discovery.discover(
            user_question="查一下论文的被引次数分布",
            db_config=db_config,
            teacher_id="GH20200001",
        )
    """

    def __init__(self, llm=None, schema_dir: str = None):
        self.llm = llm
        self.explorer = SchemaExplorer(schema_dir)

    def discover(
        self,
        user_question: str,
        db_config: dict,
        teacher_id: str,
    ) -> DiscoveredMetric:
        """
        自动发现指标：提问 → LLM 生成 SQL → 执行

        如果 LLM 不可用，回退到关键词搜索模式。
        """
        if self.llm:
            return self._discover_with_llm(user_question, db_config, teacher_id)
        else:
            return self._discover_with_search(user_question, db_config, teacher_id)

    # ── LLM 模式 ──
    def _discover_with_llm(
        self, question: str, db_config: dict, teacher_id: str
    ) -> DiscoveredMetric:
        """使用 LLM 分析问题 + Schema，生成 SQL"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import PydanticOutputParser
        from pydantic import BaseModel

        class SQLResult(BaseModel):
            sql: str
            name: str
            chart_type: str = "table"
            explanation: str = ""

        parser = PydanticOutputParser(pydantic_object=SQLResult)

        schema_text = self.explorer.get_schema_summary()

        # 读取或使用内联 Prompt
        prompt_path = Path(__file__).parent / "prompts" / "metric_discovery.txt"
        if prompt_path.exists():
            system_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            system_prompt = self._default_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n{format_instructions}"),
            ("human", (
                "数据库 Schema（仅包含科研管理相关表）：\n"
                "{schema}\n\n"
                "教师工号：{teacher_id}\n"
                "用户问题：{question}\n\n"
                "请生成 SQL 查询。注意：\n"
                "1. 如果要查某教师的数据，需要用教师工号关联 t_ky_xmry 表（ry_gh 字段）\n"
                "2. 只生成 SELECT 语句，不要 INSERT/UPDATE/DELETE\n"
                "3. 表名使用小写（如 t_ky_xmjbxx）"
            ))
        ])

        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({
                "question": question,
                "teacher_id": teacher_id,
                "schema": schema_text,
                "format_instructions": parser.get_format_instructions(),
            })

            metric = DiscoveredMetric(
                name=result.name,
                sql=result.sql,
                chart_type=result.chart_type,
                explanation=result.explanation,
            )

            # 执行 SQL 验证
            try:
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(result.sql)
                    rows = cursor.fetchall()
                conn.close()
                return metric  # SQL 正常，返回
            except Exception as e:
                metric.error = f"SQL执行失败: {e}"
                return metric

        except Exception as e:
            # LLM 调用失败，回退到搜索模式
            import sys
            print(f"[Discovery] LLM模式失败: {e}", file=sys.stderr, flush=True)
            return self._discover_with_search(question, db_config, teacher_id)

    # ── 搜索模式（无 LLM 兜底） ──
    def _discover_with_search(
        self, question: str, db_config: dict, teacher_id: str
    ) -> DiscoveredMetric:
        """基于关键词搜索 Schema，尝试自动构建简单查询"""
        # 提取多个关键词分别搜索
        keywords = self._extract_keywords(question)
        all_results = []
        for kw in keywords:
            results = self.explorer.search(kw)
            all_results.extend(results)

        # 去重
        seen = set()
        unique_results = []
        for r in all_results:
            if r["table"] not in seen:
                seen.add(r["table"])
                unique_results.append(r)

        if not unique_results:
            return DiscoveredMetric(
                name="未找到匹配",
                sql="",
                error=f"在科研数据集中未找到与「{question}」相关的表或字段。"
                       f" 尝试的关键词: {keywords}",
            )

        # 取最佳匹配
        # 优先：有字段匹配的 > 仅有表描述匹配的
        best = None
        for r in unique_results:
            if r.get("matched_fields"):
                best = r
                break
        if best is None:
            best = unique_results[0]

        table = best["table"]

        if best.get("matched_fields"):
            field = best["matched_fields"][0]["name"]
            sql = f"SELECT {field}, COUNT(*) as cnt FROM {table} GROUP BY {field} ORDER BY cnt DESC LIMIT 20"
            chart_type = "bar_chart"
            explanation = f"在 {table} 表中找到字段 {field}，生成分布统计"
        else:
            sql = f"SELECT * FROM {table} LIMIT 20"
            chart_type = "table"
            explanation = f"匹配到表 {table}：{best['description'][:60]}"

        return DiscoveredMetric(
            name=f"{table} 相关数据",
            sql=sql,
            chart_type=chart_type,
            explanation=explanation,
            tables_used=[table],
        )

    @staticmethod
    def _extract_keywords(question: str) -> list[str]:
        """从问题中提取核心关键词（分割后分别搜索）"""
        # 去掉常见问句词
        for word in ["查一下", "帮我查", "查询", "看看", "我想知道", "有没有",
                     "的情况", "的数据", "怎么样", "多少", "如何", "是什么"]:
            question = question.replace(word, " ")

        # 分词：按常见科研术语切分
        terms = [
            "论文", "专利", "著作", "软著", "软件", "获奖", "奖励", "荣誉",
            "经费", "到账", "支出", "财务", "预算",
            "项目", "课题", "在研", "结题", "立项",
            "会议", "学术会议", "报告", "交流",
            "被引", "引用", "影响因子",
            "教师", "人员", "参与",
            "年份", "年度", "月份", "月度", "日期", "时间",
            "级别", "类型", "来源", "状态", "分布", "趋势",
            "SCI", "EI", "核心", "期刊",
            "发明", "实用新型", "外观",
            "教材", "专著", "编著",
            "机构", "单位", "学院", "部门",
        ]

        found = []
        remaining = question
        for term in sorted(terms, key=len, reverse=True):
            if term in remaining:
                found.append(term)
                remaining = remaining.replace(term, " ")

        # 如果什么都没提取到，用原始问题
        if not found:
            found.append(question.strip())

        return found

    @staticmethod
    def _extract_keyword(question: str) -> str:
        """兼容旧接口"""
        return MetricDiscovery._extract_keywords(question)[0]

    @staticmethod
    def _default_prompt() -> str:
        return (
            "你是一位数据库专家，擅长根据自然语言问题和数据库 Schema 生成 SQL 查询。\n\n"
            "规则：\n"
            "1. 只生成 SELECT 语句\n"
            "2. 表名使用小写\n"
            "3. 查询教师数据时通过 t_ky_xmry 表的 ry_gh 字段关联\n"
            "4. 优先使用简单查询，避免不必要的 JOIN\n"
            "5. 对时间字段使用 DATE_FORMAT 而非 strftime\n"
            "6. 返回 JSON 格式：{\"sql\": \"...\", \"name\": \"指标名称\", "
            "\"chart_type\": \"bar_chart|line_chart|pie_chart|table|kpi_card\", "
            "\"explanation\": \"SQL 的文字解释\"}"
        )
