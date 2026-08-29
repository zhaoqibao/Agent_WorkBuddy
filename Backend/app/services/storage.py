"""MinIO 对象存储封装：上传、预签名下载、删除。"""
from __future__ import annotations

import io
from datetime import timedelta

from minio import Minio

from app.core.config import settings

client = Minio(
    settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_ENDPOINT.startswith("https"),
)


def ensure_bucket():
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def put_object(key: str, data: bytes, size: int, content_type: str = "application/octet-stream"):
    ensure_bucket()
    client.put_object(
        settings.MINIO_BUCKET,
        key,
        io.BytesIO(data),
        length=size,
        content_type=content_type,
    )


def get_presigned_url(key: str, expires_minutes: int = 15) -> str:
    return client.presigned_get_object(
        settings.MINIO_BUCKET, key, expires=timedelta(minutes=expires_minutes)
    )


def get_object(key: str) -> bytes:
    """下载对象内容为字节（用于文档转换/解析）。"""
    try:
        resp = client.get_object(settings.MINIO_BUCKET, key)
        return resp.read()
    finally:
        try:
            resp.close()
            resp.release_conn()
        except Exception:
            pass


def delete_object(key: str):
    client.remove_object(settings.MINIO_BUCKET, key)
