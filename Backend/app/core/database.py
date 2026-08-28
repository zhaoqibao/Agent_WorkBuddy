"""异步数据库引擎与会话。"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    # 注意：aiomysql 0.2.0 改了 ping 签名，与 SQLAlchemy 2.0.x 的 pool_pre_ping 不兼容；
    # 关闭 pre_ping，改用 pool_recycle 回收空闲连接，避免连接长时间空闲被 MySQL 断开。
    pool_pre_ping=False,
    pool_recycle=280,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
