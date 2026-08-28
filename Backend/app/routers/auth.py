"""登录 / 注册 / 刷新 / 当前用户。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.response import ok
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.deps import CurrentUser, DBDep
from app.models import User, UserProfile
from app.schemas import (
    LoginIn,
    PasswordUpdate,
    ProfileOut,
    ProfileUpdate,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(body: RegisterIn, db: DBDep):
    # 用户名 / 邮箱唯一性校验
    exists = await db.scalar(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if exists:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被占用")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # 拿到 user.id
    db.add(UserProfile(user_id=user.id, nickname=body.username))
    await db.commit()
    await db.refresh(user)
    return ok(UserOut.model_validate(user).model_dump())


@router.post("/login")
async def login(body: LoginIn, db: DBDep):
    user = await db.scalar(
        select(User).where(
            (User.username == body.account) | (User.email == body.account)
        )
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    user.last_login_at = datetime.utcnow()
    await db.commit()
    tokens = TokenOut(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
    return ok(tokens.model_dump())


@router.post("/refresh")
async def refresh(refresh_token: str):
    from app.core.security import decode_token

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="令牌类型错误")
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="刷新令牌无效")
    return ok({"access_token": create_access_token(str(user_id)), "token_type": "bearer"})


@router.get("/me")
async def me(current: CurrentUser):
    return ok(UserOut.model_validate(current).model_dump())


@router.get("/profile")
async def get_profile(current: CurrentUser, db: DBDep):
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == current.id)
    )
    if not profile:
        profile = UserProfile(user_id=current.id, nickname=current.username)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return ok(ProfileOut.model_validate(profile).model_dump())


@router.put("/profile")
async def update_profile(body: ProfileUpdate, current: CurrentUser, db: DBDep):
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == current.id)
    )
    if not profile:
        profile = UserProfile(user_id=current.id)
        db.add(profile)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)
    await db.commit()
    await db.refresh(profile)
    return ok(ProfileOut.model_validate(profile).model_dump())


@router.put("/password")
async def change_password(body: PasswordUpdate, current: CurrentUser, db: DBDep):
    if not verify_password(body.old_password, current.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current.password_hash = hash_password(body.new_password)
    await db.commit()
    return ok(message="密码已修改")
