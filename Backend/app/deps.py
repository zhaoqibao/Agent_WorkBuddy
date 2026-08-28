"""依赖注入：解析当前登录用户。"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, get_db
from app.core.security import decode_token
from app.models import User

DBDep = Annotated[AsyncSession, Depends(get_db)]

_bearer_err = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="无效或未提供令牌",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: DBDep = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise _bearer_err
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise _bearer_err
        user_id = int(payload.get("sub"))
    except Exception:
        raise _bearer_err

    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None or user.status != 1:
        raise _bearer_err
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
