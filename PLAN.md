# 轻量版智能体项目规划（PLAN.md）

> 目标：构建一个类似 WorkBuddy 的轻量级 AI 智能体应用，聚焦「任务 / 会话 / 工作空间 / 资料库 / 文档 / 账户」六大类常见功能。
> 前端 Vue3，后端 FastAPI + Python + MySQL。
> 已落地组件：MySQL · Redis · MinIO · Aliyun Milvus · SiliconFlow(Qwen) LLM；前端目录 `Front/`，后端目录 `Backend/`。
> 版本：v0.1 · 规划日期：2026-08-25

---

## 一、项目定位与范围

| 维度 | 说明 |
|------|------|
| 定位 | 轻量、可私有部署的个人/小团队智能体工作台 |
| 核心能力 | 任务管理、历史会话、工作空间隔离、资料库、文档处理、账户体系 |
| 非目标（v0.1 不做） | 多租户 SaaS、插件市场、复杂 RAG 向量库、实时协作、移动端原生 App |
| 智能体能力 | 内置一个基础 LLM 对话/任务执行入口（接入可选 LLM），保持可插拔 |

---

## 二、技术栈选型

### 2.1 前端
| 类别 | 选型 | 用途 |
|------|------|------|
| 框架 | **Vue 3**（Composition API + `<script setup>`） | 核心 UI 框架 |
| 构建 | **Vite** | 开发服务器与打包 |
| 语言 | **TypeScript**（建议） | 类型安全，降低维护成本 |
| 状态管理 | **Pinia** | 全局状态（用户、工作空间、会话） |
| 路由 | **Vue Router 4** | 页面路由与鉴权守卫 |
| UI 组件库 | **Element Plus** 或 **Naive UI** | 表单、表格、弹窗等基础组件 |
| HTTP 客户端 | **Axios**（封装拦截器） | 接口请求、Token 注入、错误统一处理 |
| 工具 | **dayjs**（时间）、**lodash-es**（工具） | 通用辅助 |
| 文档预览 | **@vue-office/docx / @vue-office/pdf**（可选） | 在线预览 Office/PDF |

### 2.2 后端
| 类别 | 选型 | 用途 |
|------|------|------|
| Web 框架 | **FastAPI** | 高并发异步接口、自动 OpenAPI 文档 |
| 语言 | **Python 3.11+** | 运行环境 |
| ORM | **SQLAlchemy 2.0**（异步） + **Tortoise-ORM**（备选） | 数据库建模与查询 |
| 异步驱动 | **asyncmy** / **aiomysql** | MySQL 异步连接 |
| 数据校验 | **Pydantic v2** | 请求/响应模型校验 |
| 鉴权 | **JWT**（PyJWT 或 python-jose）+ **passlib[bcrypt]** | 登录态与密码哈希 |
| 文件上传 | **python-multipart** | 表单/文件解析 |
| 文档处理 | **python-docx / openpyxl / pdfplumber / PyPDF2** | 解析 Word/Excel/PDF 文本 |
| 迁移 | **Alembic** | 数据库版本迁移 |
| 服务进程 | **Uvicorn**（+ **Gunicorn** 多 worker，生产） | ASGI 服务器 |
| 配置 | **pydantic-settings** | 环境变量与配置管理 |

### 2.3 基础设施与配套（必要补充）
| 组件 | 是否必需 | 用途 |
|------|----------|------|
| **MySQL 8.0** | 必需 | 主数据库 |
| **Redis 7** | 强烈建议 | 缓存、会话黑名单（Token 注销）、限流；也可用作用户级速率限制 |
| **MinIO** | 推荐（取代本地磁盘） | S3 兼容对象存储，统一存放文档/附件/头像，支持预签名 URL 安全下载 |
| **Milvus**（Aliyun 云服务） | 已引入（语义检索） | 向量数据库，资料库语义检索走 embedding 向量召回；接入 BGE-M3 等 embedding 模型 |
| **Nginx** | 生产建议 | 反向代理、静态资源、HTTPS |
| **Docker / docker-compose** | 建议 | 一键搭建 MySQL/Redis/MinIO/后端环境，统一开发体验 |

### 2.3.1 为什么引入 MinIO（S3 兼容对象存储）
MinIO 是轻量、可私有部署的对象存储服务，API 与 AWS S3 完全兼容。在本项目中的角色：

| 能力 | 在本项目的作用 |
|------|----------------|
| **统一文件存储** | 取代「本地磁盘目录」，所有上传文档、附件、用户头像都存到 MinIO，避免服务器磁盘路径混乱、难以迁移 |
| **预签名 URL（Presigned URL）** | 前端下载/预览文档时，后端动态生成带时效（如 5 分钟）的临时 URL，文件不暴露真实存储地址，无需把存储桶公网开放 |
| **S3 兼容** | 以后想换阿里云 OSS / 腾讯云 COS / AWS S3，只需改配置端点，**业务代码零改动**（统一用 `boto3` / `minio-py` 客户端） |
| **分桶隔离** | 可按 `docs` / `avatars` / `exports` 等建 bucket，甚至按用户/工作空间前缀隔离，便于权限与生命周期管理 |
| **大文件支持** | 原生支持分片上传（multipart），适合大文档，避免接口超时 |
| **轻量自托管** | 单二进制、docker 一行启动，无外部依赖，契合「轻量私有部署」定位 |

> 接入方式：后端用 **minio-py**（或 `boto3`）客户端；配置项 `MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY / MINIO_BUCKET`（端点由 `HOST_IP:MINIO_PORT` 拼接）。`documents.stored_path` 改为存储 **MinIO object key**（如 `ws-12/u-3/2026/abc.docx`），不再存本地路径。

### 2.4 可选扩展（保持轻量，先留接口）
- **LLM 接入层**：已确定通过 **SiliconFlow（OpenAI 兼容接口）** 接入 **Qwen** 系列模型（`BASE_LLM` / `BASE_VLM` / `IMAGE_MODEL` / `EDIT_IMAGE_MODEL`），由 `OPENAI_API_KEY` + `MODEL_API_BASE_URL` 驱动；封装统一 `LLMClient` 接口，由 `LLM_ENABLED` 开关控制。
- **向量检索**：已引入 **Aliyun Milvus**（`MILVUS_URL` / `MILVUS_TOKEN` / `MILVUS_COLLECTION_NAME`），资料库语义检索走 Milvus 向量召回 + BGE-M3 embedding，替代 v0.1 原定的 MySQL 全文索引方案。
- **联网搜索（可选）**：`TAVILY_SEARCH_KEY` 为 Agent 提供联网检索能力。
- **可观测性（可选）**：`LANGSMITH_API_KEY` + `LANGCHAIN_TRACING_V2` 做 LLM 调用链路追踪，便于调试。
- **任务调度**：APScheduler（定时任务提醒）。

---

## 三、系统架构

```
┌─────────────── 前端 (Vue3 + Vite) ───────────────┐
│  Pages: 登录 / 工作空间 / 任务 / 会话 / 资料库 / 个人中心 │
│  Stores(Pinia) · Router(鉴权守卫) · Axios(拦截器)      │
└───────────────────────┬────────────────────────────┘
                        │  HTTPS / JSON (JWT Bearer)
┌───────────────────────┴────────────────────────────┐
│            后端 (FastAPI)                            │
│  Routers: /auth /users /workspaces /tasks            │
│           /conversations /knowledge /documents       │
│  Services: 鉴权 · 文档解析 · LLM(可选) · 存储         │
│  Deps: 当前用户 · 权限校验                            │
└──────┬───────────────────────────┬─────────────────┘
       │ SQLAlchemy(async)          │ MinIO (S3 兼容对象存储)
┌──────┴──────┐              ┌──────┴──────────────┐
│  MySQL 8.0  │              │  docs / avatars ... │
└─────────────┘              └─────────────────────┘
       ▲
       │ Redis（缓存 / Token 黑名单 / 限流）
```

**分层约定**
- `routers/` 仅做参数接收与权限校验，不含业务逻辑。
- `services/` 承载业务逻辑（任务 CRUD、文档解析、会话摘要）。
- `models/` 数据库 ORM 定义；`schemas/` Pydantic 出入参。
- `core/` 放配置、安全（JWT/密码）、数据库会话、依赖注入。

---

## 四、功能模块设计

| 模块 | 核心功能 | 关键实体 |
|------|----------|----------|
| 登录模块 | 注册、登录、登出、Token 刷新、忘记密码（v0.2） | users |
| 个人信息管理 | 昵称、头像、邮箱、密码修改、偏好设置 | users / user_profiles |
| 工作空间 | 创建/切换/重命名/删除空间，数据按空间隔离 | workspaces |
| 新建任务 | 任务增删改查、状态流转（待办/进行/完成）、优先级、截止日期 | tasks |
| 历史会话管理 | 会话列表、搜索、重命名、删除；消息记录与回溯 | conversations / messages |
| 资料库 | 文档上传、列表、检索、删除、按空间归类 | knowledge_docs / documents |
| 文档处理 | 解析 docx/xlsx/pdf 文本、预览、提取内容入库 | documents（file_meta） |

> 数据隔离原则：**所有业务数据都归属某个 `workspace_id`，且最终归属某个 `user_id`**，后端按当前用户 + 工作空间做行级过滤。

---

## 五、数据库设计（MySQL 8.0）

> 统一约定：所有表含 `id`（BIGINT 自增主键）、`created_at`、`updated_at`；
> 软删除用 `deleted_at`（DATETIME NULL）；时间统一用 UTC 存储。

### 5.1 用户与账户
**users（用户表）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 用户 ID |
| username | VARCHAR(64) UNIQUE | 登录名 |
| email | VARCHAR(128) UNIQUE | 邮箱（登录/通知） |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| status | TINYINT | 0 禁用 / 1 正常 |
| last_login_at | DATETIME NULL | 最近登录 |
| created_at / updated_at / deleted_at | DATETIME | 时间戳 |

**user_profiles（个人信息扩展）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| user_id | BIGINT FK→users.id | 一对一 |
| nickname | VARCHAR(64) | 昵称 |
| avatar_url | VARCHAR(512) NULL | 头像 |
| phone | VARCHAR(32) NULL | 手机号 |
| bio | VARCHAR(500) NULL | 简介 |
| settings | JSON NULL | 偏好设置（主题、语言等） |
| created_at / updated_at | DATETIME | |

### 5.2 工作空间
**workspaces（工作空间）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| user_id | BIGINT FK→users.id | 拥有者 |
| name | VARCHAR(128) | 空间名 |
| description | VARCHAR(500) NULL | 描述 |
| is_default | TINYINT | 是否默认空间 |
| created_at / updated_at / deleted_at | DATETIME | |

### 5.3 任务
**tasks（任务表）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| workspace_id | BIGINT FK→workspaces.id | 所属空间 |
| user_id | BIGINT FK→users.id | 创建人 |
| title | VARCHAR(255) | 标题 |
| description | TEXT NULL | 描述 |
| status | TINYINT | 0 待办 / 1 进行中 / 2 已完成 / 3 已取消 |
| priority | TINYINT | 1 低 / 2 中 / 3 高 |
| due_date | DATETIME NULL | 截止时间 |
| completed_at | DATETIME NULL | 完成时间 |
| created_at / updated_at / deleted_at | DATETIME | |

> 索引：`idx_workspace_user (workspace_id, user_id)`、`idx_status (status)`。

### 5.4 会话与消息
**conversations（会话表）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| user_id | BIGINT FK→users.id | 归属用户 |
| workspace_id | BIGINT FK→workspaces.id NULL | 所属空间 |
| title | VARCHAR(255) | 会话标题（可自动生成） |
| model | VARCHAR(64) NULL | 使用的模型 |
| summary | VARCHAR(500) NULL | 摘要 |
| created_at / updated_at / deleted_at | DATETIME | |

**messages（消息表）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| conversation_id | BIGINT FK→conversations.id | 所属会话 |
| role | VARCHAR(16) | user / assistant / system |
| content | MEDIUMTEXT | 消息内容 |
| tokens | INT NULL | token 消耗 |
| created_at | DATETIME | |

> 索引：`idx_conversation (conversation_id, created_at)`。

### 5.5 资料库与文档
**knowledge_docs（资料库条目）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| user_id | BIGINT FK→users.id | 归属用户 |
| workspace_id | BIGINT FK→workspaces.id NULL | 所属空间 |
| title | VARCHAR(255) | 文档标题 |
| category | VARCHAR(64) NULL | 分类标签 |
| created_at / updated_at / deleted_at | DATETIME | |

**documents（文档/附件元数据）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | |
| knowledge_doc_id | BIGINT FK→knowledge_docs.id NULL | 关联资料库条目 |
| user_id | BIGINT FK→users.id | 上传人 |
| workspace_id | BIGINT FK→workspaces.id NULL | 所属空间 |
| original_name | VARCHAR(255) | 原始文件名 |
| stored_path | VARCHAR(512) | MinIO 对象 key（如 `ws-12/u-3/2026/abc.docx`） |
| file_type | VARCHAR(32) | docx/xlsx/pdf/... |
| file_size | BIGINT | 字节 |
| text_content | LONGTEXT NULL | 解析出的纯文本（用于检索） |
| parse_status | TINYINT | 0 待解析 / 1 成功 / 2 失败 |
| created_at / updated_at / deleted_at | DATETIME | |

> 检索：语义检索走 **Milvus**（embedding 向量召回）；关键词检索仍可用 MySQL 全文索引兜底。

---

## 六、后端目录结构（建议）

```
Backend/
├── app/
│   ├── main.py            # FastAPI 入口
│   ├── core/
│   │   ├── config.py      # pydantic-settings 配置
│   │   ├── security.py    # JWT / 密码哈希
│   │   └── database.py    # 异步引擎 / Session
│   ├── models/            # ORM 表定义
│   ├── schemas/           # Pydantic 模型
│   ├── routers/           # 路由：auth/users/workspaces/tasks/conversations/knowledge/documents
│   ├── services/          # 业务逻辑
│   ├── deps.py            # 依赖注入（当前用户）
│   └── utils/             # 文档解析、存储等
├── alembic/               # 迁移脚本
├── tests/
```

---

## 七、核心 API 规划（RESTful）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册 | 否 |
| POST | `/api/auth/login` | 登录获取 Token | 否 |
| POST | `/api/auth/refresh` | 刷新 Token | 是 |
| GET | `/api/auth/me` | 当前用户 | 是 |
| GET/PUT | `/api/users/me` | 个人信息管理 | 是 |
| GET/POST/PUT/DELETE | `/api/workspaces` | 工作空间 CRUD | 是 |
| GET/POST/PUT/DELETE | `/api/tasks` | 任务 CRUD | 是 |
| GET/POST | `/api/conversations` | 会话列表 / 新建 | 是 |
| GET/DELETE | `/api/conversations/{id}` | 会话详情 / 删除 | 是 |
| GET/POST | `/api/conversations/{id}/messages` | 消息列表 / 发送 | 是 |
| GET/POST/DELETE | `/api/knowledge` | 资料库条目 CRUD | 是 |
| POST | `/api/documents/upload` | 文档上传与解析 | 是 |
| GET | `/api/documents/{id}/preview` | 文档预览/下载 | 是 |

> 统一响应：`{ code, message, data }`；错误用 HTTP 状态码 + 业务 code。

---

## 八、前端目录结构（建议）

```
Front/
├── src/
│   ├── api/          # Axios 接口封装
│   ├── stores/       # Pinia：user / workspace / task / conversation
│   ├── router/       # 路由 + 鉴权守卫
│   ├── views/        # 页面：Login / Workspace / Tasks / Chat / Knowledge / Profile
│   ├── components/   # 公共组件
│   ├── utils/        # 请求、格式化
│   └── layouts/      # 主框架布局（侧边栏 + 顶栏）
├── public/
└── vite.config.ts
```

---

## 九、开发里程碑

| 阶段 | 内容 | 交付 |
|------|------|------|
| M1 地基 | 后端骨架 + MySQL 建表 + JWT 登录 | 可登录的 API |
| M2 账户 | 注册、个人信息管理、工作空间切换 | 账户体系可用 |
| M3 任务 | 任务 CRUD + 状态流转 + 前端页面 | 任务模块可用 |
| M4 会话 | 会话/消息 CRUD + 基础 LLM 接入（可选） | 历史会话可用 |
| M5 资料库 | 文档上传 + 解析 + 检索 + 预览 | 文档处理可用 |
| M6 打磨 | 权限校验、限流、错误处理、Docker 部署 | 可部署版本 |

---

## 十、部署建议（轻量）

```yaml
# docker-compose 最小集
services:
  mysql:   { image: mysql:8.0 }
  redis:   { image: redis:7 }
  minio:   { image: minio/minio, command: server /data --console-address ":9901", ports: ["9900:9900","9901:9901"] }
  backend: { build: ./Backend, expose: 8000 }
  frontend:{ build: ./Front, expose: 80 }
  nginx:   { image: nginx, ports: ["80:80"] }
```

- 开发期可用 `docker-compose` 起 MySQL/Redis/MinIO。
- 生产用 Nginx 反代前端静态资源 + 后端 8000，启用 HTTPS。
- 配置通过环境变量（`.env`）注入，不硬编码密钥；MinIO 的 `MINIO_ACCESS_KEY / MINIO_SECRET_KEY` 同样走环境变量。

---

## 十一、风险与扩展提示

1. **数据隔离**：务必在 service 层强制 `user_id` + `workspace_id` 过滤，避免越权。
2. **文件安全**：限制上传类型/大小，object key 由后端生成（用户不可控路径），下载统一走 MinIO **预签名 URL**（带时效、不暴露存储桶）。
3. **Token 注销**：JWT 无状态，需用 Redis 维护短期黑名单或缩短有效期 + refresh 机制。
4. **文档解析**：大文件异步解析（Celery/后台任务），避免阻塞接口。
5. **可插拔 LLM**：模型调用已抽象为统一 `LLMClient`，由 `LLM_ENABLED` 开关控制；SiliconFlow/Qwen 仅是当前实现，可平滑替换为其他 OpenAI 兼容供应商。
6. **向量检索落地**：资料库语义检索已接 Aliyun Milvus（`MILVUS_COLLECTION_NAME=easy_workbuddy`），embedding 用 BGE-M3；MySQL 全文索引作为关键词兜底，二者互补。

---

_本规划为 v0.1 轻量版蓝图，可按实际节奏裁剪模块、调整技术选型。_
