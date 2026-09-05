"""智能体组装：用 deepagents 的 create_deep_agent 构建对话智能体。

模型用 ChatOpenAI（get_llm），工具用 @tool 写法，系统提示词来自 Agent 配置，
子代理（subagents）汇聚途牛旅游等垂直领域能力，主 agent 通过 task 工具调用。
"""
from __future__ import annotations

from deepagents import create_deep_agent

from app.services.llm import get_llm
from app.services.tools import get_agent_tools
from app.subagents.tuniu import get_tuniu_subagents

DEFAULT_SYSTEM_PROMPT = (
    "你是 Easy WorkBuddy 的智能助手。"
    "回答始终使用中文。"
    "需要查询实时天气时调用 get_weather 工具；"
    "需要搜索实时新闻/资讯时调用 get_news 工具；"
    "需要读取资料库文档时调用 read_document 工具；"
    "需要转换文档格式时调用 convert_document 工具；"
    "需要识别图片内容时调用 recognize_image 工具；"
    "需要生成图片时调用 generate_image 工具。"
    "当用户查询内容涉及时间时调用 get_current_time 工具。"
    "当用户涉及旅游出行需求（查/订酒店、机票、火车票、景点门票，或查询途牛订单）时，"
    "请通过 task 工具调用对应的途牛子代理（tuniu-hotel / tuniu-flight / tuniu-train / "
    "tuniu-ticket / tuniu-order），由子代理完成具体查询，不要自己臆造旅游信息。"
    "根据用户问题选择合适的工具或子代理，直到完成任务前不要停止。"
)


async def create_agent(system_prompt: str = "", model: str | None = None):
    """创建对话智能体（返回 create_deep_agent 的编译图）。

    每次调用返回一个新实例；工具通过 config.configurable.user_id 实现数据隔离；
    途牛子代理按需加载（加载失败的服务会被跳过，不影响主流程）。
    """
    subagents = await get_tuniu_subagents()
    return create_deep_agent(
        model=get_llm(model),
        tools=get_agent_tools(),
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        subagents=subagents or None,
    )
