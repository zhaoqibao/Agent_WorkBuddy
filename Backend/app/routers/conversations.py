"""会话与消息管理 + Agent 驱动的 LLM 对话（流式 + function calling）。"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Agent, Conversation, Message
from app.schemas import ChatIn, ConversationOut, ConversationCreate, MessageOut
from app.services.agent import create_agent

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("")
async def list_conversations(current: CurrentUser, db: DBDep, workspace_id: int | None = None):
    stmt = select(Conversation).where(
        Conversation.user_id == current.id, Conversation.deleted_at.is_(None)
    )
    if workspace_id is not None:
        stmt = stmt.where(Conversation.workspace_id == workspace_id)
    stmt = stmt.order_by(Conversation.updated_at.desc())
    rows = (await db.scalars(stmt)).all()
    return ok([ConversationOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_conversation(body: ConversationCreate, current: CurrentUser, db: DBDep):
    agent = None
    if body.agent_id is not None:
        agent = await db.get(Agent, body.agent_id)
        if not agent or agent.deleted_at is not None or agent.user_id != current.id:
            raise HTTPException(status_code=404, detail="Agent 不存在")
    conv = Conversation(
        user_id=current.id,
        workspace_id=body.workspace_id,
        agent_id=body.agent_id,
        title=body.title or (agent.name if agent else "新会话"),
        model=agent.model if agent else None,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ok(ConversationOut.model_validate(conv).model_dump())


@router.get("/{conv_id}")
async def get_conversation(conv_id: int, current: CurrentUser, db: DBDep):
    conv = await db.get(Conversation, conv_id)
    if not conv or conv.deleted_at is not None or conv.user_id != current.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = (await db.scalars(
        select(Message).where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )).all()
    return ok({
        "conversation": ConversationOut.model_validate(conv).model_dump(),
        "messages": [MessageOut.model_validate(m).model_dump() for m in msgs],
    })


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: int, current: CurrentUser, db: DBDep):
    conv = await db.get(Conversation, conv_id)
    if not conv or conv.deleted_at is not None or conv.user_id != current.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    # 物理删除会话历史（消息）+ 会话本身
    msgs = (await db.scalars(
        select(Message).where(Message.conversation_id == conv_id)
    )).all()
    for m in msgs:
        await db.delete(m)
    await db.delete(conv)
    await db.commit()
    return ok(message="已删除")


async def _prepare(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    """校验会话、加载 agent、保存用户消息、构建 langchain 消息上下文。"""
    conv = await db.get(Conversation, conv_id)
    if not conv or conv.deleted_at is not None or conv.user_id != current.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent = await db.get(Agent, conv.agent_id) if conv.agent_id else None

    db.add(Message(conversation_id=conv_id, role="user", content=body.content))
    await db.commit()

    history = (await db.scalars(
        select(Message).where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )).all()

    # 转成 langchain 消息（create_deep_agent 使用）
    lc_messages = []
    for m in history:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    system_prompt = agent.system_prompt if agent else ""
    model = body.model or conv.model or (agent.model if agent else None)
    return conv, lc_messages, system_prompt, model


@router.post("/{conv_id}/messages")
async def send_message(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    """非流式对话（兼容保留）。"""
    conv, lc_messages, system_prompt, model = await _prepare(conv_id, body, current, db)
    try:
        agent = create_agent(system_prompt, model)
        res = await agent.ainvoke(
            {"messages": lc_messages},
            config={"configurable": {"user_id": current.id}},
        )
        answer = res["messages"][-1].content or ""
    except Exception:
        answer = f"[LLM 未启用] {body.content}"
    db.add(Message(conversation_id=conv_id, role="assistant", content=answer))
    conv.summary = body.content[:50] if not conv.summary else conv.summary
    await db.commit()
    return ok({"content": answer})


@router.post("/{conv_id}/messages/stream")
async def send_message_stream(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    """流式对话（SSE）：基于 create_deep_agent 智能体，支持工具调用与流式输出。"""
    conv, lc_messages, system_prompt, model = await _prepare(conv_id, body, current, db)

    async def event_gen():
        try:
            agent = create_agent(system_prompt, model)
            config = {"configurable": {"user_id": current.id}}
            full = ""

            async for ev in agent.astream_events(
                {"messages": lc_messages}, config=config, version="v2"
            ):
                kind = ev.get("event")
                name = ev.get("name", "")
                if kind == "on_chat_model_stream":
                    chunk = ev["data"].get("chunk")
                    if chunk and chunk.content:
                        full += chunk.content
                        yield _sse({"type": "token", "content": chunk.content})
                elif kind == "on_tool_start":
                    yield _sse({"type": "tool", "name": name})
                elif kind == "on_tool_end":
                    output = ev["data"].get("output")
                    content = output.content if hasattr(output, "content") else str(output)
                    artifact = getattr(output, "artifact", None)
                    data = artifact if isinstance(artifact, dict) else None
                    # convert_document 返回 JSON（含对象 key）：解析出下载信息传给前端
                    if name == "convert_document" and isinstance(content, str):
                        try:
                            info = json.loads(content)
                            if isinstance(info, dict) and info.get("key"):
                                data = {
                                    "key": info["key"],
                                    "filename": info.get("filename"),
                                    "preview": info.get("preview"),
                                }
                                content = info.get("message", content)
                        except Exception:
                            pass
                    yield _sse({"type": "tool_result", "name": name, "result": content, "data": data})

            # 保存 assistant 最终回答
            if full:
                async with SessionLocal() as s:
                    s.add(Message(conversation_id=conv_id, role="assistant", content=full))
                    await s.commit()
            yield _sse({"type": "done", "content": full})
        except Exception as e:
            yield _sse({"type": "error", "message": f"服务器错误: {e}"})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
