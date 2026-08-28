"""统一响应封装。"""
from __future__ import annotations

from typing import Any


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(message: str, code: int = 1) -> dict:
    return {"code": code, "message": message, "data": None}
