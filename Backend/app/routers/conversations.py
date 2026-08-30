"""会话与消息管理 + Agent 驱动的 LLM 对话（流式 + function calling）。"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Agent, Conversation, Message
from app.schemas import ChatIn, ConversationOut, ConversationCreate, MessageOut
from app.services.llm import llm_client
from app.services.tools import execute_tool, get_tool_definitions

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
    """校验会话、加载 agent、保存用户消息、构建 messages 上下文。"""
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

    messages: list[dict] = []
    if agent and agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})
    messages += [{"role": m.role, "content": m.content} for m in history]

    model = body.model or conv.model or (agent.model if agent else None)
    tools = get_tool_definitions(agent.tools) if agent else []
    return conv, messages, model, tools


@router.post("/{conv_id}/messages")
async def send_message(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    """非流式对话（兼容保留，无工具调用）。"""
    conv, messages, model, _ = await _prepare(conv_id, body, current, db)
    try:
        res = await llm_client.chat(messages, model=model)
        answer = res["content"]
    except RuntimeError:
        answer = f"[LLM 未启用] {body.content}"
    db.add(Message(conversation_id=conv_id, role="assistant", content=answer))
    conv.summary = body.content[:50] if not conv.summary else conv.summary
    await db.commit()
    return ok({"content": answer})


@router.post("/{conv_id}/messages/stream")
async def send_message_stream(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    """流式对话（SSE）：支持 Agent 工具调用（function calling）与流式输出。"""
    conv, messages, model, tools = await _prepare(conv_id, body, current, db)

    async def event_gen():
        async with SessionLocal() as s:
            try:
                work = list(messages)
                full = ""

                # function calling 循环：最多 3 轮
                for _ in range(3):
                    res = await llm_client.chat(work, model=model, tools=tools)
                    tcs = res.get("tool_calls")
                    if not tcs:
                        # 无工具调用：流式输出最终答案
                        async for token in llm_client.chat_stream(work, model=model):
                            full += token
                            yield _sse({"type": "token", "content": token})
                        break

                    work.append({"role": "assistant", "content": res.get("content"), "tool_calls": tcs})
                    for tc in tcs:
                        fn = tc.get("function", {})
                        name = fn.get("name", "")
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            args = {}
                        yield _sse({"type": "tool", "name": name, "args": args})
                        result, tool_data = await execute_tool(name, s, current, args)
                        yield _sse({"type": "tool_result", "name": name, "result": result, "data": tool_data})
                        work.append({"role": "tool", "tool_call_id": tc.get("id"), "content": result})
                else:
                    # 达到最大轮数，流式输出
                    async for token in llm_client.chat_stream(work, model=model):
                        full += token
                        yield _sse({"type": "token", "content": token})

                # 保存 assistant 消息
                if full:
                    s.add(Message(conversation_id=conv_id, role="assistant", content=full))
                    await s.commit()
                yield _sse({"type": "done", "content": full})
            except RuntimeError:
                yield _sse({"type": "error", "message": "LLM 未启用或调用失败"})
            except Exception as e:
                yield _sse({"type": "error", "message": f"服务器错误: {e}"})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
