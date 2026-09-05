"""配置中心：动态读取项目根目录 .env，不写死任何值。

- .env 路径动态发现：优先环境变量 ENV_FILE / DOTENV_PATH，其次从当前工作目录逐级向上搜索，最后回退到项目根目录。
- 所有敏感值（密码、密钥、Token）与端点、模型名均无默认值，完全由 .env 驱动。
- extra="allow" 保留 .env 中未显式声明的键，可通过 settings.get(key) 动态读取。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

# 项目根目录：config.py 位于 Backend/app/core/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@lru_cache
def _raw_dotenv() -> dict:
    """解析 .env 全文，返回所有键值对（含未显式声明的键）。

    用于支持动态读取 .env 中任意新增配置项，无需改动本文件。
    """
    env_file = _find_env_file()
    if not env_file:
        return {}
    try:
        from dotenv import dotenv_values

        return dict(dotenv_values(env_file))
    except Exception:
        return {}


def _find_env_file() -> Optional[str]:
    """动态定位 .env 文件路径，避免写死。

    优先级：
    1. 环境变量 ENV_FILE 或 DOTENV_PATH 显式指定；
    2. 从当前工作目录逐级向上搜索 .env；
    3. 回退到项目根目录的 .env。
    """
    explicit = os.getenv("ENV_FILE") or os.getenv("DOTENV_PATH")
    if explicit:
        p = Path(explicit).expanduser()
        if p.is_file():
            return str(p)

    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return str(candidate)

    root_env = _PROJECT_ROOT / ".env"
    return str(root_env) if root_env.is_file() else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="allow",          # 保留 .env 中未声明的键，供动态读取
        case_sensitive=False,   # 环境变量键名大小写不敏感
    )

    # ---- 应用 ----
    APP_ENV: str = "dev"
    CORS_ORIGINS: str = "http://localhost:5173"

    # ---- 数据库（主机/账号/密码/库名全部来自 .env，不写死）----
    MYSQL_HOST: str = ""
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""

    # ---- Redis ----
    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ---- MinIO ----
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""

    # ---- 鉴权 ----
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE: int = 30        # 分钟
    JWT_REFRESH_EXPIRE: int = 10080    # 分钟（7 天）

    # ---- LLM（OpenAI 兼容，可选；模型名/密钥来自 .env）----
    LLM_ENABLED: bool = False
    OPENAI_API_KEY: str = ""
    MODEL_API_BASE_URL: str = ""
    BASE_LLM: str = ""
    BASE_VLM: str = ""
    IMAGE_MODEL: str = ""
    EDIT_IMAGE_MODEL: str = ""

    # ---- 检索 / 可观测 ----
    MILVUS_URL: str = ""
    MILVUS_TOKEN: str = ""
    MILVUS_DATABASE_NAME: str = "default"
    MILVUS_COLLECTION_NAME: str = "easy_workbuddy"
    TAVILY_SEARCH_KEY: str = ""

    # ---- 途牛开放平台（旅游 MCP 服务）----
    TUNIU_API_KEY: str = ""

    # ---- 计算属性 ----
    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ---- 动态读取 ----
    def get(self, key: str, default: Any = None) -> Any:
        """读取任意配置项（大小写不敏感）。

        优先返回显式声明的字段，其次返回 .env 中未声明的键。
        这样在 .env 新增配置项时，无需改动本文件即可读取。
        """
        if key in self.__class__.model_fields:
            return getattr(self, key)
        raw = _raw_dotenv()
        if key in raw:
            return raw[key]
        # 大小写不敏感回退
        lowered = key.lower()
        for k, v in raw.items():
            if k.lower() == lowered:
                return v
        return default


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
