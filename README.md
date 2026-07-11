# 教师个人科研查询器

> **一句话**：教师用自然语言问一问，3 秒生成个人科研全景报告。

[![Version](https://img.shields.io/badge/version-v2.0-blue)](https://github.com/akakklove/teacher-research-agent)
[![Python](https://img.shields.io/badge/python-3.13-3776AB)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://mysql.com)
[![LLM](https://img.shields.io/badge/LLM-通义千问_qwen--max-FF6B00)](https://bailian.aliyun.com)
[![Tests](https://img.shields.io/badge/tests-130_passed-success)](tests/)

---

## 项目简介

高校教师的科研数据分散在多个系统（科研管理、财务、人事），做一次年度总结或职称评审材料准备往往耗时数天。

本产品把「登录 5 个系统 + 手工整理 3 天」压缩为「说一句话 + 等 3 秒」。

### 核心功能

| 功能 | 说明 |
|------|------|
| 🎨 **三栏布局** | 左侧历史对话 + 模板/技能管理 + 中间对话 + 底部输入（参考 WorkBuddy） |
| 🔄 **多轮对话** | 追问「那论文呢？」自动关联上下文，无需重复输入工号 |
| 📊 **60 个指标** | 排名（学院/全校）、多维交叉、复合积分、年度汇总表 |
| 🏷️ **模板系统** | 默认模板编辑/删除 + 自定义模板 CRUD + 指标多选弹窗 |
| 📝 **场景技能** | 年度总结 / 职称评审 一键生成报告 |
| 📥 **报告导出** | 一键导出 PPT / Markdown 科研报告 |
| 🤖 **AI 洞察** | 通义千问自动生成 2-3 条业务洞察，无 API Key 自动降级规则引擎 |
| 🔐 **JWT 登录** | 教师密码登录 + 超管后台权限分离 |
| 📜 **系统日志** | 超管后台实时日志查看（自动刷新/级别筛选/关键词搜索） |
| 💬 **历史记录** | localStorage 成对存储，单条删除，刷新不丢 |

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│  展示层    三栏HTML Chat UI + ECharts大屏 + Admin后台     │
├─────────────────────────────────────────────────────────┤
│  Agent层   意图路由(12种) + 指标引擎(60个) + 洞察 + 编排  │
│            场景模板 + 模板存储 + 指标发现 + 对话记忆       │
├─────────────────────────────────────────────────────────┤
│  服务层    FastAPI 38+路由 + JWT认证 + 日志中间件         │
├─────────────────────────────────────────────────────────┤
│  数据层    MySQL 19表 + 指标引擎 + Schema探索            │
├─────────────────────────────────────────────────────────┤
│  治理层    Schema Registry + Mock Generator(51人/4252条)  │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- Python 3.13+
- Docker Desktop（MySQL 8.0）
- 通义千问 API Key（可选，无 Key 使用规则引擎）

### 本地开发模式

```bash
git clone https://github.com/akakklove/teacher-research-agent.git
cd teacher-research-agent

# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 MySQL（Docker）
cd docker && docker compose up -d

# 3. 灌入 Mock 数据
cd ../data_governance/mock_generator && python seeder.py

# 4. 启动服务
cd ../.. && python main.py
```

### Docker 一键启动

```bash
docker compose up -d
docker exec tr_app python data_governance/mock_generator/seeder.py
```

### 访问

| 界面 | URL | 说明 |
|------|-----|------|
| 聊天对话 | `http://127.0.0.1:8000/api/chat` | 主界面 |
| 超管后台 | `http://127.0.0.1:8000/api/admin` | 仪表盘/用户/日志 |
| 大屏报告 | `http://127.0.0.1:8000/api/teacher/GH20200001/report` | ECharts 可视化 |
| API 文档 | `http://127.0.0.1:8000/docs` | Swagger |
| 日志查看 | 超管后台 → 系统日志 tab | 实时刷新 |

**登录密码**：工号后 6 位（如 `GH20200001` → `200001`，管理员 `admin`/`admin123`）

---

## 指标体系 (60 个)

| 类别 | 数量 | 示例 |
|------|------|------|
| KPI 卡片 | 11 | 主持项目数、到账经费、一作论文、专利数 |
| 排名对比 | 8 | 论文/项目/经费/专利 × 学院+全校排名 |
| 图表分布 | 33 | 项目级别分布、年度趋势、论文级别、经费月度 |
| 多维交叉 | 3 | 论文年度×级别、项目年度×级别、获奖年度×类别 |
| 复合指标 | 2 | 综合产出积分、学院内百分位 |
| 汇总表 | 1 | 年度成果汇总（5类成果×5年） |
| 收支对比 | 1 | 年到账 vs 年支出 |
| 其他 | 1 | 科研全景（19指标组合） |

---

## API 总览

### 数据查询

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/health` | 数据库联通检查 |
| GET | `/api/metrics` | 指标目录（支持 `?category=` 筛选） |
| GET | `/api/teacher/{id}` | 教师基本信息 |
| GET | `/api/teacher/{id}/overview` | 完整指标查询（JSON） |
| GET | `/api/teacher/{id}/report` | ECharts 大屏（HTML） |

### 对话交互

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/chat` | 聊天界面（HTML） |
| POST | `/api/chat/send` | 发送消息（支持多轮） |
| POST | `/api/chat/scenario` | 场景模板一键生成 |
| POST | `/api/chat/discover` | 指标自动发现 |
| GET | `/api/chat/sessions` | 活跃会话数 |

### 认证

| 方法 | 路由 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 教师/管理员登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/sync` | 从 MySQL 同步教师账号 |

### 模板管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/templates/{teacher_id}` | 列出教师模板 |
| POST | `/api/templates/save` | 保存模板 |
| DELETE | `/api/templates/{id}` | 删除模板 |
| PATCH | `/api/templates/{id}` | 重命名模板 |

### 超管后台

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/admin/stats` | 仪表盘统计 |
| GET | `/api/admin/users` | 用户列表 |
| GET | `/api/admin/datasource` | 数据源状态 |
| GET/POST | `/api/admin/metrics` | 指标管理 |
| GET | `/api/admin/logs` | 系统日志（按级别/关键词） |
| POST | `/api/admin/logs/clear` | 清空日志 |
| GET | `/api/admin/logs/download` | 下载完整日志 |

### 其他

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/scenarios` | 场景模板列表 |
| POST | `/api/export` | 导出报告（PPT/Markdown） |

---

## 项目结构

```
teacher-research-agent/
├── docker/                         # Docker MySQL 环境
│   ├── docker-compose.yml
│   └── init.sql                    # 19 张表建表脚本
├── data_governance/                # 数据治理层
│   ├── schema_registry/            # Schema 注册中心
│   └── mock_generator/             # Mock 数据生成器（51名教师, 4252条）
├── data_service/                   # 服务层
│   └── api.py                      # FastAPI（38+ 路由 + 日志中间件）
├── agent/                          # Agent 编排层
│   ├── metrics.yaml                # 60 个指标定义（SQL + 数据来源）
│   ├── metric_engine.py            # 指标查询引擎
│   ├── intent_router.py            # 意图路由（12种意图，LLM + 规则）
│   ├── insight_engine.py           # AI 洞察生成器
│   ├── dashboard_composer.py       # ECharts 大屏编排
│   ├── dashboard_layouts.py        # 按意图的大屏布局映射
│   ├── conversation_memory.py      # 会话记忆管理
│   ├── scenario_templates.py       # 场景模板引擎
│   ├── template_store.py           # SQLite 模板存储
│   ├── metric_discovery.py         # 指标自动发现
│   ├── auth.py                     # JWT 认证
│   ├── llm.py                      # 通义千问初始化
│   └── prompts/                    # LLM Prompt 模板
├── dashboard/                      # 展示层
│   ├── templates/
│   │   ├── chat.html               # 三栏布局聊天界面(1800+行)
│   │   ├── admin.html              # 超管后台（仪表盘/用户/指标/日志）
│   │   └── dashboard.html          # 1920×1080 ECharts 大屏
│   └── export.py                   # PPT/Markdown 导出
├── tests/                          # 单元测试（130用例）
├── main.py                         # Uvicorn 启动入口
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 数据模型

以 `t_ky_xmry`（项目人员关系表）为核心枢纽：

```
t_jzg_jbxx (教师) ──→ t_ky_xmry (项目人员) ←── t_ky_xmjbxx (项目)
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
    经费到账/支出/外拨    成果(论文/专利/   活动(会议/机构)
                          著作/软著/获奖)
```

19 张应用层表 = 固定数据契约。源系统变化通过 ETL 映射层隔离。

---

## 版本历史

| 版本 | 内容 |
|------|------|
| v0.1 | 数据治理层 + Docker MySQL + Mock 数据 |
| v0.2 | 30 个指标 + FastAPI 服务层 + 通义千问集成 |
| v0.3 | Agent 层（意图路由/洞察/编排）+ 1920×1080 大屏 |
| v0.4 | 多轮对话 + 场景模板 + 模板复用 + 指标发现 |
| v1.0 | JWT 登录 + PPT/MD导出 + Docker化 + 超管后台 + 130单元测试 |
| v2.0 | 三栏布局 + 指标体系60指标 + 历史/模板管理 + 结构化回复 + 系统日志 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL 8.0（Docker） + SQLite（模板/用户） |
| LLM | 通义千问 qwen-max（阿里百炼） |
| LLM 框架 | LangChain |
| 大屏 | ECharts 5 + Jinja2 |
| 前端 | 原生 HTML/CSS/JS（零框架，三栏布局） |
| 认证 | PyJWT（HS256，24h过期） |
| 测试 | pytest（130用例） |
| 数据治理 | 高校科研管理数据标准 3.0 |

---

## License

MIT
