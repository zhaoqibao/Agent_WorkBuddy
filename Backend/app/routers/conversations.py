"""会话与消息管理 + 基础 LLM 对话（可插拔）。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Conversation, Message
from app.schemas import ChatIn, ConversationOut, ConversationCreate, MessageOut
from app.services.llm import llm_client

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(current: CurrentUser, db: DBDep, workspace_id: int | None = None):
    stmt = select(Conversation).where(
        Conversation.user_id == current.id, Conversation.deleted_at.is_(None)
    )
    if workspace_id is not None:
        stmt = stmt.where(Conversation.workspace_id == workspace_id)
    rows = (await db.scalars(stmt)).all()
    return ok([ConversationOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_conversation(body: ConversationCreate, current: CurrentUser, db: DBDep):
    conv = Conversation(
        user_id=current.id,
        workspace_id=body.workspace_id,
        title=body.title or "新会话",
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
    conv.deleted_at = datetime.utcnow()
    await db.commit()
    return ok(message="已删除")


@router.post("/{conv_id}/messages")
async def send_message(conv_id: int, body: ChatIn, current: CurrentUser, db: DBDep):
    conv = await db.get(Conversation, conv_id)
    if not conv or conv.deleted_at is not None or conv.user_id != current.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    user_msg = Message(conversation_id=conv_id, role="user", content=body.content)
    db.add(user_msg)

    history = (await db.scalars(
        select(Message).where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )).all()
    messages = [{"role": m.role, "content": m.content} for m in history] + [
        {"role": "user", "content": body.content}
    ]

    try:
        answer = await llm_client.chat(messages, model=body.model or conv.model)
        db.add(Message(conversation_id=conv_id, role="assistant", content=answer))
        conv.summary = (body.content[:50] or conv.title) if not conv.summary else conv.summary
        conv.model = body.model or conv.model
    except RuntimeError as e:
        # LLM 未配置：降级为回显，保证会话链路可用
        db.add(Message(conversation_id=conv_id, role="assistant",
                       content=f"[LLM 未启用] {body.content}"))
        answer = f"[LLM 未启用] {body.content}"

    await db.commit()
    return ok({"content": answer})
