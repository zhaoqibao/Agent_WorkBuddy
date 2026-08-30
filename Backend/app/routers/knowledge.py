"""资料库条目 CRUD。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.response import ok
from app.deps import CurrentUser, DBDep
from app.models import Document, KnowledgeDoc
from app.schemas import KnowledgeCreate, KnowledgeOut
from app.services.storage import delete_object

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge(current: CurrentUser, db: DBDep, workspace_id: int | None = None):
    stmt = select(KnowledgeDoc).where(
        KnowledgeDoc.user_id == current.id, KnowledgeDoc.deleted_at.is_(None)
    )
    if workspace_id is not None:
        stmt = stmt.where(KnowledgeDoc.workspace_id == workspace_id)
    rows = (await db.scalars(stmt)).all()
    return ok([KnowledgeOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_knowledge(body: KnowledgeCreate, current: CurrentUser, db: DBDep):
    kd = KnowledgeDoc(
        user_id=current.id,
        workspace_id=body.workspace_id,
        title=body.title,
        category=body.category,
    )
    db.add(kd)
    await db.commit()
    await db.refresh(kd)
    return ok(KnowledgeOut.model_validate(kd).model_dump())


@router.delete("/{kd_id}")
async def delete_knowledge(kd_id: int, current: CurrentUser, db: DBDep):
    kd = await db.get(KnowledgeDoc, kd_id)
    if not kd or kd.deleted_at is not None or kd.user_id != current.id:
        raise HTTPException(status_code=404, detail="资料不存在")
    # 物理删除该条目下的所有文档 + 条目本身，并清理 MinIO 文件
    docs = (await db.scalars(
        select(Document).where(Document.knowledge_doc_id == kd_id)
    )).all()
    for d in docs:
        if d.stored_path:
            try:
                delete_object(d.stored_path)
            except Exception:
                pass  # MinIO 删除失败不影响数据库删除
        await db.delete(d)
    await db.delete(kd)
    await db.commit()
    return ok(message="已删除")
