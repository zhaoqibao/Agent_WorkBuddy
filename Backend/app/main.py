"""FastAPI 应用入口。"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.core.config import settings
from app.routers import (
    agents,
    auth,
    conversations,
    documents,
    knowledge,
    tasks,
    workspaces,
)

app = FastAPI(title="easy_workbuddy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            {"code": exc.status_code, "message": exc.detail, "data": None},
            status_code=exc.status_code,
        )
    import traceback
    traceback.print_exc()
    return JSONResponse({"code": 500, "message": "服务器内部错误", "data": None}, status_code=500)


@app.get("/api/health")
async def health():
    return {"code": 0, "message": "ok", "data": {"env": settings.APP_ENV}}


for r in (
    auth.router,
    agents.router,
    workspaces.router,
    tasks.router,
    conversations.router,
    knowledge.router,
    documents.router,
):
    app.include_router(r)
