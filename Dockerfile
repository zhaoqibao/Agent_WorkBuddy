# ================= 后端构建：FastAPI + uv 依赖安装 =================
# 使用 uv 官方镜像，自动按 Linux 平台解析依赖（跳过 pywin32/pyreadline3 等 Windows 专属包）
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# 先拷贝依赖清单，充分利用 Docker 层缓存
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 拷贝后端源码
COPY Backend/ ./Backend/

# ================= 运行镜像：精简 =================
FROM python:3.12-slim

# onnxruntime（markitdown/magika 依赖）在 Linux 需要 libgomp1；curl 供健康检查用
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY Backend/ ./Backend/
COPY pyproject.toml ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/Backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
