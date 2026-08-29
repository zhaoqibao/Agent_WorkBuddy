from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,  # noqa: F401
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 与建表脚本一致的无符号 BIGINT（主键/外键）
def ubigint(**kw):
    return mapped_column(BIGINT(unsigned=True), **kw)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_default: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime,  nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_workspace_user", "workspace_id", "user_id"),
        Index("idx_status", "status"),
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tools: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_agent_user", "user_id"),
        Index("idx_agent_ws", "workspace_id"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    agent_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="新会话", nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_user", "user_id"),
        Index("idx_ws", "workspace_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_conversation", "conversation_id", "created_at"),
    )


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_user", "user_id"),
        Index("idx_ws", "workspace_id"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = ubigint(primary_key=True, autoincrement=True)
    knowledge_doc_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("knowledge_docs.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    file_size: Mapped[int] = mapped_column(BIGINT(unsigned=True), default=0, nullable=False)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parse_status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_kd", "knowledge_doc_id"),
        Index("idx_user", "user_id"),
        Index("idx_ws", "workspace_id"),
    )
