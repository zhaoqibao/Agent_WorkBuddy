"""途牛旅游 MCP 服务接入（Streamable HTTP + API Key Bearer 鉴权）。

途牛开放平台将酒店、机票、门票、火车票、订单等能力封装为远程 MCP 服务，
统一使用 HTTPS + Streamable HTTP 协议，通过 `Authorization: Bearer <TUNIU_API_KEY>`
鉴权。本模块负责建立连接并加载各服务的工具列表。
"""
from __future__ import annotations

from app.core.config import settings

# 途牛 MCP 服务地址（服务名 -> URL）
TUNIU_MCP_SERVERS: dict[str, str] = {
    "order": "https://openapi.tuniu.cn/hybrid/mcp/order",
    "hotel": "https://openapi.tuniu.cn/hybrid/mcp/hotel",
    "flight": "https://openapi.tuniu.cn/hybrid/mcp/flight",
    "train": "https://openapi.tuniu.cn/hybrid/mcp/train",
    "ticket": "https://openapi.tuniu.cn/hybrid/mcp/ticket",
}


def _server_config(url: str) -> dict:
    """构造 langchain_mcp_adapters 的服务连接配置。"""
    return {
        "url": url,
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {settings.TUNIU_API_KEY}"},
    }


async def load_tools(name: str) -> list:
    """加载指定途牛 MCP 服务（order/hotel/flight/train/ticket）的工具列表。"""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    if name not in TUNIU_MCP_SERVERS:
        raise KeyError(f"未知途牛 MCP 服务：{name}")

    client = MultiServerMCPClient({name: _server_config(TUNIU_MCP_SERVERS[name])})
    return await client.get_tools()
