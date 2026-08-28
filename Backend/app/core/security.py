"""密码哈希与 JWT 签发/校验。

说明：出于可移植性与环境兼容性（部分环境无法可靠安装 bcrypt 原生扩展），
密码哈希改用 Python 标准库 hashlib.pbkdf2_hmac 实现，不依赖任何原生二进制。
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings

ALG = settings.JWT_ALGORITHM
_PBKDF2_ROUNDS = 260000


def hash_password(password: str) -> str:
    """返回形如 pbkdf2:sha256:<rounds>$<salt_hex>$<hash_hex> 的存储串。"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2:sha256:{_PBKDF2_ROUNDS}:{salt.hex()}:{dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        algo, hash_name, rounds, salt_hex, hash_hex = stored.split(":")
        if algo != "pbkdf2":
            return False
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(
            hash_name, plain.encode("utf-8"), salt, int(rounds)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def create_access_token(sub: str, expires_minutes: int | None = None) -> str:
    expire = timedelta(minutes=expires_minutes or settings.JWT_ACCESS_EXPIRE)
    payload: dict[str, Any] = {
        "sub": sub,
        "exp": datetime.now(timezone.utc) + expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALG)


def create_refresh_token(sub: str) -> str:
    expire = timedelta(minutes=settings.JWT_REFRESH_EXPIRE)
    payload: dict[str, Any] = {
        "sub": sub,
        "exp": datetime.now(timezone.utc) + expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALG)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALG])
