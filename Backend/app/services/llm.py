"""可插拔 LLM 客户端（OpenAI 兼容接口，SiliconFlow/Qwen）。

直接使用 httpx 调用 /chat/completions，避免引入整套 OpenAI SDK 及其版本耦合。
未配置或调用失败时抛出 RuntimeError，由调用方捕获降级。
"""
from __future__ import annotations

import httpx

from app.core.config import settings


class LLMClient:
    """对话补全。未配置时抛出 RuntimeError；由调用方捕获降级。"""

    def __init__(self):
        self.enabled = settings.LLM_ENABLED and bool(settings.OPENAI_API_KEY)
        self.base_url = settings.MODEL_API_BASE_URL.rstrip("/")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.BASE_LLM

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        if not self.enabled:
            raise RuntimeError("LLM 未启用（LLM_ENABLED=false 或缺少 API Key）")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("LLM 返回格式异常")


llm_client = LLMClient()
