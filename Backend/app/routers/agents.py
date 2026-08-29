"""Agent（智能体）CRUD：名称、系统提示词、模型、启用的工具。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Agent
from app.schemas import AgentCreate, AgentOut, AgentUpdate

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(current: CurrentUser, db: DBDep, workspace_id: int | None = None):
    stmt = select(Agent).where(
        Agent.user_id == current.id, Agent.deleted_at.is_(None)
    )
    if workspace_id is not None:
        stmt = stmt.where(Agent.workspace_id == workspace_id)
    rows = (await db.scalars(stmt)).all()
    return ok([AgentOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_agent(body: AgentCreate, current: CurrentUser, db: DBDep):
    agent = Agent(user_id=current.id, **body.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return ok(AgentOut.model_validate(agent).model_dump())


@router.put("/{agent_id}")
async def update_agent(agent_id: int, body: AgentUpdate, current: CurrentUser, db: DBDep):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.deleted_at is not None or agent.user_id != current.id:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(agent, k, v)
    await db.commit()
    await db.refresh(agent)
    return ok(AgentOut.model_validate(agent).model_dump())


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, current: CurrentUser, db: DBDep):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.deleted_at is not None or agent.user_id != current.id:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    agent.deleted_at = datetime.utcnow()
    await db.commit()
    return ok(message="已删除")
