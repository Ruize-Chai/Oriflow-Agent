from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Server.registry import get_workflow


router = APIRouter()


class InjectRequest(BaseModel):
    channel: str
    message: Any


class RequestResponseRequest(BaseModel):
    channel: str
    message: Any
    timeout: Optional[float] = None


@router.post("/api/workflows/{wf_id}/input")
async def workflow_input(wf_id: str, payload: InjectRequest):
    """非阻塞外部注入：调用 `comm_hub.inject_external` 并立即返回。"""
    wf = get_workflow(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    try:
        wf.comm_hub.inject_external(payload.channel, payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


@router.post("/api/workflows/{wf_id}/request")
async def workflow_request(wf_id: str, payload: RequestResponseRequest):
    """阻塞 request-response：调用 `comm_hub.request_response` 并等待结果（或超时）。

    返回：{"status": "ok", "result": <value>} 或 504 on timeout
    """
    wf = get_workflow(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="workflow not found")
    try:
        # 调用 request_response 并等待
        res = await wf.comm_hub.request_response(payload.channel, payload.message, payload.timeout)
    except asyncio.CancelledError:
        raise HTTPException(status_code=500, detail="request cancelled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if res is None:
        # 把超时或空响应映射为 504
        raise HTTPException(status_code=504, detail="timeout or no response")
    return {"status": "ok", "result": res}


__all__ = ["router"]
