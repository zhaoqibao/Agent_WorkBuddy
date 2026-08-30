"""工具（Tools）体系：注册表 + 各工具实现。

每个工具包含 OpenAI function-calling 格式的 definition 与异步 handler。
handler 统一签名为 async def handler(db, user, **kwargs) -> str（返回给模型的文本结果）。
"""
from __future__ import annotations

import csv
import io
import json

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.models import Document


# ---------- VLM 统一调用（langchain_openai ChatOpenAI） ----------
def _vlm_client() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.BASE_VLM,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.MODEL_API_BASE_URL,
        timeout=90,
        max_retries=1,
        temperature=0,
    )


async def _vlm_describe(data_url: str, prompt: str = "请详细描述这张图片的内容") -> str:
    """用 langchain_openai 的 ChatOpenAI 调 VLM 识别图片内容。"""
    client = _vlm_client()
    msg = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )
    try:
        resp = await client.ainvoke([msg])
        return resp.content or ""
    except Exception as e:
        return f"图片识别失败: {e}"


# ---------- 工具 1：天气查询（open-meteo，无需 key） ----------
async def _get_weather(db, user, city: str = "") -> str:
    if not city:
        return "未提供城市名"
    async with httpx.AsyncClient(timeout=20.0) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "language": "zh", "count": 1},
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return f"未找到城市「{city}」"
        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = loc.get("name", city)
        w = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
        )
        w.raise_for_status()
        cw = w.json().get("current_weather") or {}
        return (
            f"{name}当前天气：温度 {cw.get('temperature')}°C，"
            f"风速 {cw.get('windspeed')} km/h，"
            f"天气代码 {cw.get('weathercode')}（0 晴/1-3 多云/45-48 雾/51-67 雨/71-77 雪/95-99 雷暴）"
        )


# ---------- 工具 2：实时新闻搜索（Tavily） ----------
async def _get_news(db, user, query: str = "") -> str:
    if not query:
        return "未提供搜索关键词"
    if not settings.TAVILY_SEARCH_KEY:
        return "未配置 TAVILY_SEARCH_KEY，新闻搜索不可用"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.TAVILY_SEARCH_KEY,
                "query": query,
                "max_results": 5,
                "search_depth": "basic",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    items = data.get("results") or []
    if not items:
        return f"未找到与「{query}」相关的新闻"
    lines = [f"关于「{query}」的最新结果："]
    for it in items:
        lines.append(f"- {it.get('title', '')}（{it.get('url', '')}）")
    return "\n".join(lines)


# ---------- 工具 3/4：文档读取与格式互转 ----------
_IMAGE_TYPES = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"}


async def _recognize_document_image(doc) -> str:
    """图片文档：从 MinIO 下载后用 VLM 识别内容。"""
    import base64

    from app.services import storage

    try:
        raw = storage.get_object(doc.stored_path)
    except Exception as e:
        return f"读取图片失败: {e}"

    ext = (doc.file_type or "").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else (ext or "png")
    data_url = f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"

    if not settings.BASE_VLM:
        return "未配置 VLM 模型（BASE_VLM），无法识别图片"
    return await _vlm_describe(data_url)


async def _read_document(db, user, document_id: int = 0) -> str:
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        return "文档不存在或无权访问"

    # 图片类型走 VLM 识别
    if (doc.file_type or "").lower() in _IMAGE_TYPES:
        return await _recognize_document_image(doc)

    text = doc.text_content or ""
    if not text:
        return "该文档暂无解析文本"
    return text[:6000] if len(text) > 6000 else text


def _extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    try:
        if ext in ("txt", "md", "csv"):
            return data.decode("utf-8", errors="ignore")
        if ext == "docx":
            from docx import Document as Docx
            return "\n".join(p.text for p in Docx(io.BytesIO(data)).paragraphs)
        if ext == "xlsx":
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            out = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    out.append("\t".join("" if c is None else str(c) for c in row))
            return "\n".join(out)
        if ext == "pdf":
            import pdfplumber
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as e:
        return f"[解析失败: {e}]"
    return "[不支持的格式]"


def _xlsx_to_csv(data: bytes) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            writer.writerow(["" if c is None else c for c in row])
    return buf.getvalue()


def _csv_to_json(text: str) -> str:
    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader]
    return json.dumps(rows, ensure_ascii=False, indent=2)


async def _convert_document(db, user, document_id: int = 0, target_format: str = "txt") -> str:
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        return "文档不存在或无权访问"

    from app.services import storage

    try:
        raw = storage.get_object(doc.stored_path)
    except Exception as e:
        return f"读取文档失败: {e}"

    target = (target_format or "txt").lower().strip(".")
    text = _extract_text(doc.original_name, raw)

    if target in ("txt", "md"):
        result = text
    elif target == "csv":
        result = _xlsx_to_csv(raw) if (doc.file_type or "") == "xlsx" else text
    elif target == "json":
        result = _csv_to_json(text) if (doc.file_type or "") == "csv" else json.dumps({"content": text}, ensure_ascii=False, indent=2)
    else:
        return f"暂不支持转换到 {target}（支持 txt/md/csv/json）"
    return result


# ---------- 工具 5：图片识别（VLM） ----------
async def _recognize_image(db, user, image_url: str = "", prompt: str = "请描述这张图片的内容") -> str:
    if not image_url:
        return "未提供图片地址（image_url）"
    if not settings.BASE_VLM:
        return "未配置 VLM 模型（BASE_VLM）"
    return await _vlm_describe(image_url, prompt)


# ---------- 工具 6：图片生成（IMAGE_MODEL） ----------
async def _generate_image(db, user, prompt: str = "", size: str = "1024x1024"):
    if not prompt:
        return "未提供图片描述（prompt）", None
    if not settings.IMAGE_MODEL:
        return "未配置图片生成模型（IMAGE_MODEL）", None
    payload = {"model": settings.IMAGE_MODEL, "prompt": prompt, "size": size, "n": 1}
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{settings.MODEL_API_BASE_URL.rstrip('/')}/images/generations", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    try:
        item = data["data"][0]
        b64 = item.get("b64_json")
        url = item.get("url")
        if b64:
            return "已生成图片，展示在对话中", {"image": f"data:image/png;base64,{b64}"}
        if url:
            return "已生成图片，展示在对话中", {"image": url}
        return "图片生成失败", None
    except (KeyError, IndexError):
        return "图片生成失败", None


# ---------- 注册表 ----------
TOOLS: dict[str, dict] = {
    "get_weather": {
        "definition": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的实时天气",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "城市名，如北京"}},
                    "required": ["city"],
                },
            },
        },
        "handler": _get_weather,
    },
    "get_news": {
        "definition": {
            "type": "function",
            "function": {
                "name": "get_news",
                "description": "搜索实时新闻/资讯（基于 Tavily 搜索）",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                    "required": ["query"],
                },
            },
        },
        "handler": _get_news,
    },
    "read_document": {
        "definition": {
            "type": "function",
            "function": {
                "name": "read_document",
                "description": "读取资料库中某个文档的文本内容",
                "parameters": {
                    "type": "object",
                    "properties": {"document_id": {"type": "integer", "description": "文档 ID"}},
                    "required": ["document_id"],
                },
            },
        },
        "handler": _read_document,
    },
    "convert_document": {
        "definition": {
            "type": "function",
            "function": {
                "name": "convert_document",
                "description": "把资料库中的文档转换为指定格式（txt/md/csv/json）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "integer", "description": "文档 ID"},
                        "target_format": {"type": "string", "description": "目标格式：txt/md/csv/json"},
                    },
                    "required": ["document_id", "target_format"],
                },
            },
        },
        "handler": _convert_document,
    },
    "recognize_image": {
        "definition": {
            "type": "function",
            "function": {
                "name": "recognize_image",
                "description": "识别/理解一张图片的内容（视觉大模型）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_url": {"type": "string", "description": "图片的 URL 地址"},
                        "prompt": {"type": "string", "description": "关于图片的问题，如「描述这张图」"},
                    },
                    "required": ["image_url"],
                },
            },
        },
        "handler": _recognize_image,
    },
    "generate_image": {
        "definition": {
            "type": "function",
            "function": {
                "name": "generate_image",
                "description": "根据文字描述生成一张图片",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "图片描述"},
                        "size": {"type": "string", "description": "图片尺寸，如 1024x1024"},
                    },
                    "required": ["prompt"],
                },
            },
        },
        "handler": _generate_image,
    },
}


def get_tool_definitions(tool_names: list[str] | None) -> list[dict]:
    """根据启用的工具名列表，返回 function-calling 的 tools 定义。"""
    if not tool_names:
        return []
    return [TOOLS[n]["definition"] for n in tool_names if n in TOOLS]


async def execute_tool(name: str, db, user, arguments: dict):
    """执行某个工具，返回 (文本结果, 结构化数据)。

    文本结果回传给模型；结构化数据（如图片）直接透传给前端展示。
    """
    tool = TOOLS.get(name)
    if not tool:
        return f"未知工具 {name}", None
    try:
        result = await tool["handler"](db, user, **(arguments or {}))
        if isinstance(result, tuple):
            return result
        return result, None
    except Exception as e:
        return f"工具 {name} 执行出错: {e}", None


def list_tool_names() -> list[str]:
    return list(TOOLS.keys())
