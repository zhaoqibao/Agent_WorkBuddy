# Easy WorkBuddy

一个轻量版的智能体工作台，仿 WorkBuddy 的核心功能精简实现。前端 Vue3，后端 FastAPI + Python + MySQL，支持登录注册、工作空间、任务、会话（可接入 LLM 对话）、资料库与文档上传（MinIO）。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Axios + Element Plus |
| 后端 | Python 3.12+ + FastAPI + SQLAlchemy 2.0（异步）+ Pydantic v2 |
| 数据库 | MySQL 8.0（`light_agent`） |
| 缓存 | Redis 7（可选，推荐） |
| 对象存储 | MinIO（S3 兼容，文档/附件上传） |
| 鉴权 | JWT（PyJWT）+ `hashlib.pbkdf2_hmac` 密码哈希 |
| LLM | OpenAI 兼容接口（httpx 直连，SiliconFlow/Qwen 等，可插拔） |
| 依赖管理 | uv（后端）、npm（前端） |

## 功能模块

- 登录 / 注册（JWT 鉴权，密码 6-10 位）
- 工作空间管理（新建 / 编辑 / 删除 / 设为默认）
- 任务管理（按空间筛选、优先级、状态流转）
- 会话与对话（历史消息回溯，接入 LLM 后返回智能回复，未配置时降级回显）
- 资料库 + 文档上传（存 MinIO，自动解析文本）
- 个人信息（资料维护、修改密码）

## 目录结构

```
Agent_WorkBuddy/
├── Backend/                     # 后端（FastAPI）
│   ├── app/
│   │   ├── core/                # 配置 / 数据库 / 安全 / 统一响应
│   │   ├── models/              # SQLAlchemy ORM 模型（8 张表）
│   │   ├── schemas/             # Pydantic 出入参模型
│   │   ├── routers/             # auth / workspaces / tasks / conversations / knowledge / documents
│   │   ├── services/            # LLM、MinIO 存储封装
│   │   ├── deps.py              # 依赖注入（当前用户、DB 会话）
│   │   └── main.py              # 应用入口
│   └── sql/                     # 建表 DDL 与自动执行脚本
├── Front/                       # 前端（Vue3 + Vite）
│   └── src/
│       ├── api/                 # 接口封装
│       ├── router/              # 路由 + 鉴权守卫
│       ├── stores/              # Pinia 状态
│       ├── utils/               # axios 封装（拦截器）
│       └── views/               # Login / Layout / Workspaces / Tasks / Conversations / Knowledge / Profile
├── .env                         # 环境配置（后端动态加载）
├── pyproject.toml / uv.lock     # 后端依赖（uv 管理）
├── requirements.txt             # 后端依赖（pip 清单）
├── PLAN.md                      # 项目规划
└── NEED.md                      # 落地所需材料清单
```

## 前置依赖

- **Python 3.12+**、**uv**（推荐，用于后端依赖管理）
- **Node.js 18+**（前端）
- **MySQL 8.0**（必需，需提前建好库 `light_agent`）
- **MinIO**（可选，文档上传/预览需要；不传文档可跳过）
- **Redis**（可选，推荐）

## 配置

所有配置集中在**项目根目录的 `.env`**（后端启动时动态加载，无需把 `.env` 放进子目录）。关键字段：

| 变量 | 说明 |
|------|------|
| `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` | MySQL 连接信息 |
| `REDIS_HOST/PORT/PASSWORD/DB` | Redis 连接信息（可选） |
| `MINIO_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET` | MinIO 对象存储 |
| `JWT_SECRET_KEY` | JWT 密钥（可用 `openssl rand -hex 32` 生成） |
| `LLM_ENABLED` / `OPENAI_API_KEY` / `MODEL_API_BASE_URL` / `BASE_LLM` | LLM 开关与模型 |
| `MILVUS_URL/TOKEN/...` | 阿里云 Milvus 向量库（预留） |
| `APP_ENV` / `CORS_ORIGINS` | 运行环境与跨域白名单 |

> 更多字段说明见 `NEED.md`。`.env` 已加入 `.gitignore`，请勿提交到 Git。

## 快速启动

### 1. 初始化数据库（首次）

```bash
# 方式一：自动读 .env 连库建表（推荐）
cd Backend
python sql/run_init.py

# 方式二：手动执行 DDL
mysql -u root -p light_agent < Backend/sql/init_tables.sql
```

> 会在 `light_agent` 库中创建 8 张表：`users`、`user_profiles`、`workspaces`、`tasks`、`conversations`、`messages`、`knowledge_docs`、`documents`。

### 2. 启动后端

```bash
# 在项目根目录用 uv 同步依赖（首次）
uv sync

# 启动（开发热重载）
cd Backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 不热重载
uv run --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后访问健康检查：`http://127.0.0.1:8000/api/health`，返回 `{"code":0,...}` 即正常。

> 也可用 `pip install -r requirements.txt` 安装依赖后直接 `uvicorn app.main:app` 运行（需在 `Backend` 目录）。

### 3. 启动前端

```bash
cd Front
npm install        # 首次
npm run dev        # 启动 Vite 开发服务器
```

默认地址 `http://localhost:5173`。开发服务器已配置 `/api` 代理到后端 `http://localhost:8000`（见 `Front/vite.config.js`）。

### 4. 登录使用

打开 `http://localhost:5173`，注册账号即可体验。本地联调已存在测试账号：`admin / admin`。

## 接口约定

- 所有接口以 `/api` 为前缀。
- 统一响应格式：`{"code": 0, "message": "ok", "data": {...}}`，`code=0` 表示成功。
- 除登录/注册外均需请求头 `Authorization: Bearer <access_token>`。
- 在线文档（启动后端后）：`http://127.0.0.1:8000/docs`（Swagger UI）。

## 常见问题

- **后端启动报 greenlet / aiomysql 错误**：请使用 `uv run` 启动（确保用项目 `.venv`），不要用系统裸 `python`。
- **上传文档报错**：确认 MinIO 已启动且 `MINIO_ENDPOINT` 可达，`MINIO_BUCKET` 名称不含下划线。
- **对话返回「LLM 未启用」**：`.env` 中 `LLM_ENABLED=false` 或未配置 `OPENAI_API_KEY`，属正常降级。
