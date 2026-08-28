# 落地所需材料清单（NEED.md）

> 配合 `PLAN.md` 使用。本文列出项目涉及的技术栈各自需要你**提供什么**（账号、密钥、配置项、资源），  
> 并映射到后端 `.env` 环境变量，方便 `pydantic-settings` 读取。  
> 标注「必需」的没有就无法跑起来；「可选/建议」可后续补。

---

## 一、总览表

| 技术栈        | 需要你提供                         | 必需程度      | 对应环境变量            |
| ---------- | ----------------------------- | --------- | ----------------- |
| MySQL 8.0  | 数据库地址/账号/密码/库名                | 必需        | `MYSQL_*`         |
| Redis 7    | 地址/端口/密码                      | 强烈建议      | `REDIS_*`         |
| MinIO      | 端点/AccessKey/SecretKey/Bucket | 推荐        | `MINIO_*`         |
| Milvus     | 向量库 URL/Token/集合名（已引入语义检索）      | 已引入       | `MILVUS_*`        |
| FastAPI 后端 | JWT 密钥、CORS 域名、运行环境           | 必需        | `APP_*` / `JWT_*` |
| LLM（可选）    | 供应商 + API Key + 模型名 + BaseURL | 可选（默认关闭）  | `LLM_*` / `OPENAI_API_KEY` / `MODEL_API_BASE_URL` |
| 联网/可观测(可选) | Tavily 搜索 Key、LangSmith Key        | 可选        | `TAVILY_*` / `LANGSMITH_*` |
| 邮件（v0.2）   | SMTP 服务器/账号/密码                | 可选（忘记密码用） | `SMTP_*`          |
| 前端 Vue3    | 后端接口地址                        | 必需        | `.env.frontend`   |
| Nginx / 域名 | 域名 + SSL 证书                   | 生产必需      | —                 |

---

## 二、逐项说明

### 2.1 MySQL 8.0（必需）

你需要准备一个可用的 MySQL 实例（本地装、Docker、或云数据库都行）。

| 提供项  | 说明                     | 环境变量             |
| ---- | ---------------------- | ---------------- |
| 主机地址 | 如 `127.0.0.1` 或云库内网地址  | `MYSQL_HOST`     |
| 端口   | 默认 `3306`              | `MYSQL_PORT`     |
| 用户名  | 有建库/读写权限的账号            | `MYSQL_USER`     |
| 密码   | 上述账号密码                 | `MYSQL_PASSWORD` |
| 数据库名 | 提前建好空库，如 `light_agent` | `MYSQL_DATABASE` |

> 建议用 Docker 起一个，或阿里云/腾讯云 RDS。本地开发可直接 `docker run mysql:8.0`。

### 2.2 Redis 7（强烈建议）

用于 Token 黑名单、限流、缓存。

| 提供项   | 说明            | 环境变量             |
| ----- | ------------- | ---------------- |
| 主机地址  | 如 `127.0.0.1` | `REDIS_HOST`     |
| 端口    | 默认 `6379`     | `REDIS_PORT`     |
| 密码    | 建议设置；无密码可留空   | `REDIS_PASSWORD` |
| DB 编号 | 默认 `0`        | `REDIS_DB`       |

> 不配置 Redis 时，Token 注销将退化为"仅依赖过期时间"，功能可用但不安全，不建议生产关闭。

### 2.3 MinIO（推荐）

S3 兼容对象存储，存文档/附件/头像。

| 提供项         | 说明                                          | 环境变量                 |
| ----------- | ------------------------------------------- | -------------------- |
| 服务端口 Port   | MinIO 数据端口，如 `9900`（你的 .env 当前为 9900）         | `MINIO_PORT`         |
| 控制台端口       | 管理控制台端口，如 `9901`                            | `MINIO_CONSOLE_PORT` |
| 端点 Endpoint | 由 `HOST_IP:MINIO_PORT` 拼接，如 `http://127.0.0.1:9900` | `MINIO_ENDPOINT`     |
| Access Key  | 控制台创建的访问密钥（你的 .env 当前为 `minio123`）            | `MINIO_ACCESS_KEY`   |
| Secret Key  | 对应密钥（当前为 `minio123`，本地可接受，生产请改强）              | `MINIO_SECRET_KEY`   |
| 主 Bucket    | 如 `easy_workbuddy`（与项目命名一致）                  | `MINIO_BUCKET`       |

> 首次启动后用浏览器开 `MINIO_CONSOLE_PORT` 控制台，创建 bucket 并生成 Access/Secret Key。  
> 想用云 OSS/COS 替代：端点与密钥换成对应的，业务代码不用改。

### 2.3.1 Milvus（已引入，向量检索）
语义检索依赖向量数据库（你已接入 Aliyun Milvus 云服务）。

| 提供项       | 说明                              | 环境变量                     |
| ---------- | ------------------------------- | ------------------------ |
| 实例 URL    | Aliyun Milvus 公网/内网地址，含端口 `19530` | `MILVUS_URL`             |
| Token      | 访问令牌（含用户名:密码）                  | `MILVUS_TOKEN`           |
| 数据库名      | 如 `default`                     | `MILVUS_DATABASE_NAME`   |
| 集合名        | 如 `easy_workbuddy`              | `MILVUS_COLLECTION_NAME` |

> embedding 模型建议用 **BGE-M3**（与你的 RAG FAQ 项目一致），文本向量化后写入 Milvus 集合，检索时做向量召回。  
> 若未来换向量库（pgvector 等），只需改向量层适配，表结构无需大改。

### 2.4 FastAPI 后端（必需）

| 提供项       | 说明                                         | 环境变量                                       |
| --------- | ------------------------------------------ | ------------------------------------------ |
| JWT 签名密钥  | **自己随机生成一段长字符串**（如 `openssl rand -hex 32`） | `JWT_SECRET_KEY`                           |
| Token 有效期 | 如 access 30 分钟、refresh 7 天                 | `JWT_ACCESS_EXPIRE` / `JWT_REFRESH_EXPIRE` |
| 允许的前端域名   | 用于 CORS，如 `http://localhost:5173`          | `CORS_ORIGINS`                             |
| 运行环境      | `dev` / `prod`                             | `APP_ENV`                                  |

> `JWT_SECRET_KEY` 务必随机且保密，泄露等于任何人可伪造登录态。

### 2.5 LLM 接入（已配置：SiliconFlow + Qwen，由 `LLM_ENABLED` 开关）

智能体对话/任务执行用到。你当前已确定方案：**通过 SiliconFlow 的 OpenAI 兼容接口调用 Qwen 系列模型**。

| 提供项            | 说明                              | 环境变量                                |
| -------------- | ------------------------------- | ----------------------------------- |
| 接口地址 Base URL | SiliconFlow 网关 `https://api.siliconflow.cn/v1` | `MODEL_API_BASE_URL`                |
| API Key        | SiliconFlow 密钥                    | `OPENAI_API_KEY`                    |
| 文本大模型         | 如 `Qwen/Qwen3.5-122B-A10B`        | `BASE_LLM`                          |
| 视觉大模型         | 如 `Qwen/Qwen3-VL-30B-A3B-Instruct` | `BASE_VLM`                          |
| 图像生成模型        | 如 `Qwen/Qwen-Image`              | `IMAGE_MODEL`                       |
| 图像编辑模型        | 如 `Qwen/Qwen-Image-Edit-2509`    | `EDIT_IMAGE_MODEL`                  |
| 是否启用           | `true` 才走 LLM，否则接口返回"未配置"        | `LLM_ENABLED`                       |

> 该方案本质仍是 OpenAI 兼容协议，若未来换 DeepSeek / DashScope / 本地 Ollama，只需改 `MODEL_API_BASE_URL` + Key + 模型名，业务代码无需改。  
> 不配置（或 `LLM_ENABLED=false`）则 v0.1 仍可正常运行其他模块，只是"智能体对话"不可用。

### 2.5.1 可选：联网搜索与可观测性

| 提供项        | 说明                    | 环境变量                                       |
| ---------- | --------------------- | ------------------------------------------ |
| Tavily 搜索  | Agent 联网检索能力           | `TAVILY_SEARCH_KEY`                        |
| LangSmith  | LLM 调用链路追踪（调试用）       | `LANGSMITH_API_KEY` / `LANGCHAIN_TRACING_V2` / `LANGCHAIN_PROJECT` |

> 二者均为可选项，缺失不影响核心功能；LangSmith 仅开发调试期建议开启。

### 2.6 邮件 SMTP（可选，v0.2 忘记密码用）

| 提供项     | 说明                        | 环境变量            |
| ------- | ------------------------- | --------------- |
| SMTP 主机 | 如 `smtp.qq.com`           | `SMTP_HOST`     |
| 端口      | 通常 `465`（SSL）或 `587`（TLS） | `SMTP_PORT`     |
| 发件账号    | 邮箱地址                      | `SMTP_USER`     |
| 授权码     | 邮箱的 SMTP 授权码（非登录密码）       | `SMTP_PASSWORD` |

> 微信/QQ 邮箱需在设置里开启 SMTP 并生成授权码。不配置则"忘记密码"功能暂不开放。

### 2.7 前端 Vue3（必需）

| 提供项    | 说明                              | 配置位置                                  |
| ------ | ------------------------------- | ------------------------------------- |
| 后端接口地址 | 如 `http://localhost:8000` 或生产域名 | `Front/.env` 的 `VITE_API_BASE_URL` |
| 上传大小上限 | 与后端/MinIO 对齐，如 `50MB`           | 前端 axios 配置                           |

### 2.8 Nginx / 域名（生产必需）

| 提供项    | 说明                                |
| ------ | --------------------------------- |
| 域名     | 如 `agent.yourdomain.com`          |
| SSL 证书 | 免费 Let's Encrypt 或云厂商证书（HTTPS 必需） |
| 反代规则   | 前端静态资源 + 后端 8000 +（可选）MinIO 控制台   |

---

## 三、汇总：后端 `.env` 示例

```dotenv
# ---- 基础/编码 ----
PYTHONIOENCODING=utf-8
PYTHONUTF8=1
HOST_IP=127.0.0.1
LOG_FILE=logs/app.log

# ---- 应用 ----
APP_ENV=dev
CORS_ORIGINS=http://localhost:5173

# ---- 数据库 ----
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_pwd
MYSQL_DATABASE=light_agent

# ---- Redis（强烈建议；未运行则后端需降级）----
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ---- MinIO ----
MINIO_PORT=9900
MINIO_CONSOLE_PORT=9901
MINIO_ENDPOINT=http://127.0.0.1:9900
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=easy_workbuddy

# ---- Milvus（语义检索）----
MILVUS_URL=http://<your-milvus>:19530
MILVUS_TOKEN=root:password
MILVUS_DATABASE_NAME=default
MILVUS_COLLECTION_NAME=easy_workbuddy

# ---- 鉴权（JWT_SECRET_KEY 务必随机且保密）----
JWT_SECRET_KEY=请替换为 openssl rand -hex 32 生成的随机串
JWT_ACCESS_EXPIRE=30
JWT_REFRESH_EXPIRE=10080

# ---- LLM（已配置 SiliconFlow + Qwen）----
LLM_ENABLED=true
MODEL_API_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEY=sk-xxxx
BASE_LLM=Qwen/Qwen3.5-122B-A10B
BASE_VLM=Qwen/Qwen3-VL-30B-A3B-Instruct
IMAGE_MODEL=Qwen/Qwen-Image
EDIT_IMAGE_MODEL=Qwen/Qwen-Image-Edit-2509

# ---- 可选：联网搜索 / 可观测 ----
# TAVILY_SEARCH_KEY=tvly-xxxx
# LANGSMITH_API_KEY=lsv2_xxxx
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_PROJECT=easy_workbuddy

# ---- 邮件（可选，v0.2）----
# SMTP_HOST=smtp.qq.com
# SMTP_PORT=465
# SMTP_USER=you@qq.com
# SMTP_PASSWORD=授权码
```

前端 `Front/.env`：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

---

## 四、优先级建议（先跑通最小集）

1. **第一梯队（必需，已具备）**：MySQL（库 `light_agent`）、JWT 密钥（已生成）、前端 API 地址 → 可完成登录/账户/任务/会话骨架。
2. **第二梯队（推荐/已引入）**：Redis（安全注销，需本地起服务）、MinIO（文档上传，端口 9900）、Milvus（语义检索，已接 Aliyun） → 补齐文档处理与智能检索。
3. **第三梯队（可选）**：LLM（已配 SiliconFlow+Qwen，开关 `LLM_ENABLED`）、Tavily/LangSmith、SMTP（忘记密码）、域名/SSL（上线）。

> 一句话：你的 `.env` 主体已齐，仅 Redis 服务需本地起、JWT 密钥已生成（请确认已落盘）、MySQL 密码与 MinIO 密钥本地可用、生产请改强。
