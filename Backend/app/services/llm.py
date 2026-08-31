"""LLM 模型实例（langchain_openai ChatOpenAI）。

统一用 ChatOpenAI 创建模型实例（OpenAI 兼容接口，SiliconFlow/Qwen）。
供 create_deep_agent 及 VLM 图片识别使用。
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm(model: str | None = None) -> ChatOpenAI:
    """创建文本对话模型实例（默认 BASE_LLM）。"""
    return ChatOpenAI(
        model=model or settings.BASE_LLM,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.MODEL_API_BASE_URL,
        timeout=120,
        max_retries=2,
    )


def get_vlm(model: str | None = None) -> ChatOpenAI:
    """创建视觉模型实例（默认 BASE_VLM）。"""
    return ChatOpenAI(
        model=model or settings.BASE_VLM,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.MODEL_API_BASE_URL,
        timeout=120,
        max_retries=1,
    )
