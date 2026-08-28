"""任务 CRUD + 状态流转（按 workspace + user 隔离）。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Task
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(workspace_id: int, current: CurrentUser, db: DBDep):
    rows = (await db.scalars(
        select(Task).where(
            Task.workspace_id == workspace_id, Task.user_id == current.id,
            Task.deleted_at.is_(None),
        )
    )).all()
    return ok([TaskOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_task(body: TaskCreate, current: CurrentUser, db: DBDep):
    data = body.model_dump()
    data["user_id"] = current.id
    task = Task(**data)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return ok(TaskOut.model_validate(task).model_dump())


@router.put("/{task_id}")
async def update_task(task_id: int, body: TaskUpdate, current: CurrentUser, db: DBDep):
    task = await db.get(Task, task_id)
    if not task or task.deleted_at is not None or task.user_id != current.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    data = body.model_dump(exclude_unset=True)
    # 状态变为已完成时记录完成时间
    if data.get("status") == 2 and task.completed_at is None:
        data["completed_at"] = datetime.utcnow()
    for k, v in data.items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return ok(TaskOut.model_validate(task).model_dump())


@router.delete("/{task_id}")
async def delete_task(task_id: int, current: CurrentUser, db: DBDep):
    task = await db.get(Task, task_id)
    if not task or task.deleted_at is not None or task.user_id != current.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.deleted_at = datetime.utcnow()
    await db.commit()
    return ok(message="已删除")
