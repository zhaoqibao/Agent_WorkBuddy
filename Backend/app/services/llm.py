"""可插拔 LLM 客户端（OpenAI 兼容接口，SiliconFlow/Qwen）。

直接使用 httpx 调用 /chat/completions，避免引入整套 OpenAI SDK 及其版本耦合。
支持非流式（含 tool_calls）与流式两种调用。
未配置或调用失败时抛出 RuntimeError，由调用方捕获降级。
"""
from __future__ import annotations

import json

import httpx

from app.core.config import settings


class LLMClient:
    """对话补全。未配置时抛出 RuntimeError；由调用方捕获降级。"""

    def __init__(self):
        self.enabled = settings.LLM_ENABLED and bool(settings.OPENAI_API_KEY)
        self.base_url = settings.MODEL_API_BASE_URL.rstrip("/")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.BASE_LLM

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, messages, model, tools) -> dict:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    async def chat(self, messages: list[dict], model: str | None = None, tools: list[dict] | None = None) -> dict:
        """非流式调用，返回 {"content": str, "tool_calls": list|None}。"""
        if not self.enabled:
            raise RuntimeError("LLM 未启用（LLM_ENABLED=false 或缺少 API Key）")

        payload = self._payload(messages, model, tools)
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        try:
            msg = data["choices"][0]["message"]
            return {"content": msg.get("content") or "", "tool_calls": msg.get("tool_calls")}
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("LLM 返回格式异常")

    async def chat_stream(self, messages: list[dict], model: str | None = None, tools: list[dict] | None = None):
        """流式调用，逐段 yield token 字符串。"""
        if not self.enabled:
            raise RuntimeError("LLM 未启用（LLM_ENABLED=false 或缺少 API Key）")

        payload = self._payload(messages, model, tools)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload, headers=self._headers()
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content


llm_client = LLMClient()
