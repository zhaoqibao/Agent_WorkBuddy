from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- 通用 ----------
class Msg(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Optional[dict] = None


# ---------- 鉴权 ----------
class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=10)


class LoginIn(BaseModel):
    account: str = Field(..., description="用户名或邮箱")
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------- 用户 / 个人信息 ----------
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    status: int
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: int
    user_id: int
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    settings: Optional[dict] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    settings: Optional[dict] = None

    model_config = {"extra": "forbid"}


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=10)


# ---------- 工作空间 ----------
class WorkspaceCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    is_default: bool = False


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None


class WorkspaceOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    is_default: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- 任务 ----------
class TaskCreate(BaseModel):
    workspace_id: int
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: int = 0
    priority: int = 2
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[int] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskOut(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    status: int
    priority: int
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- 会话 ----------
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    workspace_id: Optional[int] = None


class ConversationOut(BaseModel):
    id: int
    user_id: int
    workspace_id: Optional[int] = None
    title: str
    model: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = "user"


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    tokens: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatIn(BaseModel):
    content: str = Field(..., min_length=1)
    model: Optional[str] = None


# ---------- 资料库 / 文档 ----------
class KnowledgeCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=64)
    workspace_id: Optional[int] = None


class KnowledgeOut(BaseModel):
    id: int
    user_id: int
    workspace_id: Optional[int] = None
    title: str
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    knowledge_doc_id: Optional[int] = None
    user_id: int
    workspace_id: Optional[int] = None
    original_name: str
    stored_path: str
    file_type: Optional[str] = None
    file_size: int
    parse_status: int
    created_at: datetime

    model_config = {"from_attributes": True}
