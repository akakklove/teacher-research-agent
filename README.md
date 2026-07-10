# 教师个人科研查询器

> **一句话**：教师用自然语言问一问，3 秒生成个人科研全景报告。

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/akakklove/teacher-research-agent)
[![Python](https://img.shields.io/badge/python-3.13-3776AB)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://mysql.com)
[![LLM](https://img.shields.io/badge/LLM-通义千问_qwen--max-FF6B00)](https://bailian.aliyun.com)

---

## 项目简介

高校教师的科研数据分散在多个系统（科研管理、财务、人事），做一次年度总结或职称评审材料准备往往耗时数天。

本产品把「登录 5 个系统 + 手工整理 3 天」压缩为「说一句话 + 等 3 秒」。

### 核心功能

| 功能 | 说明 |
|------|------|
| 🔄 **多轮对话** | 追问「那论文呢？」自动关联上下文，无需重复输入工号 |
| 📊 **科研大屏** | 1920×1080 深色主题，26 个指标（11 KPI + 15 图表） |
| 📝 **场景模板** | 年度总结 / 职称评审 / 基金申报 一键生成报告 |
| 💾 **模板复用** | 自定义指标组合存为模板，下次一键刷新 |
| 🔍 **指标发现** | 注册表外的指标自动探索 Schema → LLM 生成 SQL |
| 🔐 **JWT 登录** | 教师密码登录，超管后台权限分离 |
| 📥 **报告导出** | 一键导出 PPT / Markdown 科研报告 |
| 🤖 **AI 洞察** | 通义千问自动生成 2-3 条业务洞察 |

### 技术架构

```
┌─────────────────────────────────────────────┐
│  展示层    HTML大屏 + Chat UI + 指标选择器     │
├─────────────────────────────────────────────┤
│  Agent层   意图路由 + 指标引擎 + 洞察 + 编排   │
│            场景模板 + 模板存储 + 指标发现      │
├─────────────────────────────────────────────┤
│  服务层    FastAPI + 数据接口                │
├─────────────────────────────────────────────┤
│  数据层    MySQL + 指标引擎 + Schema探索     │
├─────────────────────────────────────────────┤
│  治理层    Schema Registry + Mock Generator  │
└─────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- Docker Desktop
- 通义千问 API Key（可选，无 Key 使用规则引擎）

### Docker 一键启动（推荐）

```bash
git clone https://github.com/akakklove/teacher-research-agent.git
cd teacher-research-agent

# 设置 API Key（可选，不设则使用规则引擎）
# Linux/Mac: export DASHSCOPE_API_KEY=sk-your-key
# Windows PS: $env:DASHSCOPE_API_KEY="sk-your-key"

# 一键启动 MySQL + FastAPI
docker compose up -d

# 灌入 Mock 数据
docker exec tr_app python data_governance/mock_generator/seeder.py
```

### 本地开发模式

```bash
# 1. 启动 MySQL
cd docker && docker compose up -d

# 2. 灌入数据
cd ../data_governance/mock_generator && pip install pymysql && python seeder.py

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python main.py
```

### 访问

| 界面 | URL |
|------|-----|
| 聊天对话 | `http://127.0.0.1:8000/api/chat` |
| 大屏报告 | `http://127.0.0.1:8000/api/teacher/GH20200001/report` |
| API 文档 | `http://127.0.0.1:8000/docs` |

**登录密码**：工号后 6 位（如 `GH20200001` → `200001`）

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
| GET | `/api/chat` | 聊天界面 |
| POST | `/api/chat/send` | 发送消息（支持 session_id 多轮） |
| POST | `/api/chat/scenario` | 场景模板一键生成 |
| POST | `/api/chat/discover` | 指标自动发现 |
| GET | `/api/chat/sessions` | 活跃会话数 |

### 模板管理

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/templates/{teacher_id}` | 列出教师模板 |
| POST | `/api/templates/save` | 保存模板 |
| DELETE | `/api/templates/{id}` | 删除模板 |
| PATCH | `/api/templates/{id}` | 重命名模板 |

### 场景列表

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/scenarios` | 列出所有场景模板 |

---

## 项目结构

```
teacher-research-agent/
├── docker/                         # Docker MySQL 环境
│   ├── docker-compose.yml
│   └── init.sql                    # 19 张表建表脚本（utf8mb4）
├── data_governance/                # 数据治理层
│   ├── schema_registry/            #   15 数据集 Schema（3636 字段）
│   └── mock_generator/             #   Mock 生成器（4252 条数据，SEED=42）
├── data_service/                   # 服务层
│   └── api.py                      #   FastAPI（17 条路由）
├── agent/                          # Agent 编排层
│   ├── metrics.yaml                #   30 个指标定义（SQL 模板 + 数据来源）
│   ├── metric_engine.py            #   指标查询引擎
│   ├── intent_router.py            #   意图路由（11 种意图，LLM + 规则）
│   ├── insight_engine.py           #   洞察生成器（LLM + 阈值规则）
│   ├── dashboard_composer.py       #   大屏编排（ECharts）
│   ├── conversation_memory.py      #   会话记忆管理（TTL 3600s）
│   ├── scenario_templates.py       #   场景模板引擎（3 个场景）
│   ├── template_store.py           #   模板存储（SQLite）
│   ├── metric_discovery.py         #   指标自动发现（LLM + 关键词）
│   ├── llm.py                      #   通义千问初始化（LangChain）
│   └── prompts/                    #   5 个 LLM Prompt 模板
├── dashboard/                      # 展示层
│   └── templates/
│       ├── dashboard.html          #   1920×1080 ECharts 大屏（深色主题）
│       └── chat.html               #   聊天对话界面（KPI 卡片 + 模板面板）
├── main.py                         # Uvicorn 启动入口
├── start.bat                       # Windows 一键启动
├── .env                            # API Key（gitignored）
├── .gitignore
├── README.md                       # 本文档
└── 项目进度记录.md                   # 详细项目文档
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

| 版本 | 内容 | 状态 |
|------|------|:--:|
| v0.1 | 数据治理层 + Docker MySQL + Mock 数据 | ✅ |
| v0.2 | 30 个指标 + FastAPI 服务层 + 通义千问集成 | ✅ |
| v0.3 | Agent 层（意图路由/洞察/编排）+ 1920×1080 大屏 | ✅ |
| v0.4 | 多轮对话 + 场景模板 + 模板复用 + 指标发现 | ✅ |
| v1.0 | JWT 登录 + PPT/MD导出 + Docker化 + 超管后台 | ✅ |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL 8.0（Docker） |
| LLM | 通义千问 qwen-max（阿里百炼） |
| LLM 框架 | LangChain（ChatModel + PromptTemplate） |
| 大屏 | ECharts 5 + Jinja2 |
| 前端 | 原生 HTML/CSS/JS（零框架） |
| 数据治理 | 高校科研管理数据标准 3.0 |

---

## License

MIT
