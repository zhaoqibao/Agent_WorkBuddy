"""智能体组装：用 deepagents 的 create_deep_agent 构建对话智能体。

参照 all_agent.py 的结构：模型用 ChatOpenAI（get_llm），工具用 @tool 写法，
系统提示词来自 Agent 配置，中间件/subagents 暂未启用。
"""
from __future__ import annotations

from deepagents import create_deep_agent

from app.services.llm import get_llm
from app.services.tools import get_agent_tools

DEFAULT_SYSTEM_PROMPT = (
    "你是 Easy WorkBuddy 的智能助手。"
    "回答始终使用中文。"
    "需要查询实时天气时调用 get_weather 工具；"
    "需要搜索实时新闻/资讯时调用 get_news 工具；"
    "需要读取资料库文档时调用 read_document 工具；"
    "需要转换文档格式时调用 convert_document 工具；"
    "需要识别图片内容时调用 recognize_image 工具；"
    "需要生成图片时调用 generate_image 工具。"
    "根据用户问题选择合适的工具，直到完成任务前不要停止。"
)


def create_agent(system_prompt: str = "", model: str | None = None):
    """创建对话智能体（返回 create_deep_agent 的编译图）。

    每次调用返回一个新实例；工具通过 config.configurable.user_id 实现数据隔离。
    """
    return create_deep_agent(
        model=get_llm(model),
        tools=get_agent_tools(),
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
    )
