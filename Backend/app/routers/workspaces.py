"""工作空间 CRUD（数据按 user 隔离）。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Workspace
from app.schemas import WorkspaceCreate, WorkspaceOut, WorkspaceUpdate

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("")
async def list_workspaces(current: CurrentUser, db: DBDep):
    rows = (await db.scalars(
        select(Workspace).where(Workspace.user_id == current.id, Workspace.deleted_at.is_(None))
    )).all()
    return ok([WorkspaceOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_workspace(body: WorkspaceCreate, current: CurrentUser, db: DBDep):
    if body.is_default:
        # 先取消其他默认空间
        others = (await db.scalars(
            select(Workspace).where(
                Workspace.user_id == current.id, Workspace.is_default == 1,
                Workspace.deleted_at.is_(None),
            )
        )).all()
        for w in others:
            w.is_default = 0
    ws = Workspace(user_id=current.id, **body.model_dump())
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ok(WorkspaceOut.model_validate(ws).model_dump())


@router.put("/{ws_id}")
async def update_workspace(ws_id: int, body: WorkspaceUpdate, current: CurrentUser, db: DBDep):
    ws = await db.get(Workspace, ws_id)
    if not ws or ws.deleted_at is not None or ws.user_id != current.id:
        raise HTTPException(status_code=404, detail="空间不存在")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_default"):
        others = (await db.scalars(
            select(Workspace).where(
                Workspace.user_id == current.id, Workspace.is_default == 1,
                Workspace.deleted_at.is_(None), Workspace.id != ws_id,
            )
        )).all()
        for w in others:
            w.is_default = 0
    for k, v in data.items():
        setattr(ws, k, v)
    await db.commit()
    await db.refresh(ws)
    return ok(WorkspaceOut.model_validate(ws).model_dump())


@router.delete("/{ws_id}")
async def delete_workspace(ws_id: int, current: CurrentUser, db: DBDep):
    ws = await db.get(Workspace, ws_id)
    if not ws or ws.deleted_at is not None or ws.user_id != current.id:
        raise HTTPException(status_code=404, detail="空间不存在")
    ws.deleted_at = datetime.utcnow()
    await db.commit()
    return ok(message="已删除")
