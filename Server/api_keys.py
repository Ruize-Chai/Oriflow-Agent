from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Server.keys_manager import set_api_key, get_api_key, clear_api_key, has_key

router = APIRouter()


class APIKeyModel(BaseModel):
    api_key: str


@router.post("/api/keys/openai")
async def set_openai_key(payload: APIKeyModel):
    """设置 OpenAI API Key（内存）。"""
    try:
        set_api_key("openai", payload.api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


@router.get("/api/keys/openai")
async def get_openai_key():
    """获取 OpenAI API Key 存在状态与掩码（不返回完整 key）。"""
    try:
        if not has_key("openai"):
            return {"present": False}
        k = get_api_key("openai") or ""
        # mask key for safety
        if len(k) <= 8:
            masked = "*" * len(k)
        else:
            masked = k[:4] + "*" * (len(k) - 8) + k[-4:]
        return {"present": True, "key_masked": masked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/keys/openai")
async def delete_openai_key():
    try:
        clear_api_key("openai")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


__all__ = ["router"]
