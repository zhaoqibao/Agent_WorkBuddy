"""途牛旅游子 agent：把每个途牛 MCP 服务封装成一个子 agent。

每个子 agent 是一个声明式 SubAgent 字典（name / description / system_prompt / tools），
主 agent 通过 `task` 工具根据 description 判断并调用对应子 agent。
"""
from __future__ import annotations

import asyncio
import logging

from app.mcps.tuniu import load_tools

logger = logging.getLogger(__name__)

# 工具列表缓存（避免每次对话都重新连接 MCP 服务加载工具）
_cache: list | None = None
_cache_lock = asyncio.Lock()

# 途牛各服务的子 agent 元信息
_TUNIU_SUBAGENTS = [
    {
        "key": "order",
        "name": "tuniu-order",
        "description": (
            "查询途牛用户订单信息（订单列表、订单详情、订单状态等）。"
            "当用户询问「我的途牛订单」「订单状态」「订单详情」等订单相关问题时调用此子代理。"
        ),
        "system_prompt": (
            "你是途牛订单查询助手。使用订单服务工具查询用户的途牛订单信息，"
            "返回准确、简洁的结果。回答用中文。"
        ),
    },
    {
        "key": "hotel",
        "name": "tuniu-hotel",
        "description": (
            "酒店搜索、详情查询与预订。"
            "当用户需要「查酒店」「订酒店」「比较酒店价格」「看酒店详情/评分/位置」时调用此子代理。"
        ),
        "system_prompt": (
            "你是途牛酒店预订助手。使用酒店服务工具搜索酒店、查询详情、辅助预订，"
            "返回酒店名称、价格、评分、位置等关键信息。回答用中文。"
        ),
    },
    {
        "key": "flight",
        "name": "tuniu-flight",
        "description": (
            "国内机票航班搜索与预订。"
            "当用户需要「查机票」「订机票」「查航班/票价/时刻」时调用此子代理。"
        ),
        "system_prompt": (
            "你是途牛机票预订助手。使用机票服务工具搜索国内航班、查询票价与时刻、辅助预订，"
            "返回航班号、起飞降落时间、价格等关键信息。回答用中文。"
        ),
    },
    {
        "key": "train",
        "name": "tuniu-train",
        "description": (
            "火车票班次查询与预订。"
            "当用户需要「查火车票」「订火车票」「查车次/余票/时刻」时调用此子代理。"
        ),
        "system_prompt": (
            "你是途牛火车票助手。使用火车票服务工具查询车次、余票、时刻并辅助预订，"
            "返回车次、出发到达时间、席别、票价等关键信息。回答用中文。"
        ),
    },
    {
        "key": "ticket",
        "name": "tuniu-ticket",
        "description": (
            "景点门票搜索与预订。"
            "当用户需要「查景点门票」「订门票」「查景区价格/开放时间」时调用此子代理。"
        ),
        "system_prompt": (
            "你是途牛景点门票助手。使用门票服务工具搜索景点门票、查询价格与开放时间、辅助预订，"
            "返回景区名称、票价、开放时间等关键信息。回答用中文。"
        ),
    },
]


async def _load_subagents() -> list:
    """实际加载途牛子 agent 列表（每个服务一个子 agent，加载失败的服务跳过）。"""
    subagents = []
    for meta in _TUNIU_SUBAGENTS:
        try:
            tools = await load_tools(meta["key"])
        except Exception as e:  # noqa: BLE001
            logger.warning("途牛子代理 %s 加载失败，跳过：%s", meta["name"], e)
            continue
        if not tools:
            logger.warning("途牛子代理 %s 无可用工具，跳过", meta["name"])
            continue
        subagents.append({
            "name": meta["name"],
            "description": meta["description"],
            "system_prompt": meta["system_prompt"],
            "tools": tools,
        })
    return subagents


async def get_tuniu_subagents(use_cache: bool = True) -> list:
    """加载途牛子 agent 列表（带缓存，避免每次对话重复连接 MCP 服务）。"""
    global _cache
    if use_cache and _cache is not None:
        return _cache
    async with _cache_lock:
        # 双重检查：并发下避免重复加载
        if _cache is None:
            _cache = await _load_subagents()
        return _cache


def invalidate_tuniu_cache() -> None:
    """清空缓存（MCP 服务变更或需要重新加载时调用）。"""
    global _cache
    _cache = None
