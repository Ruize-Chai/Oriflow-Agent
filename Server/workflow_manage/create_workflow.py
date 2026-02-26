from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from Workflow.workflow import Workflow
from Server.registry import register_workflow, get_workflow
from Nodes.pluginSeeker import Search_Node
from Logger import PluginImportError, PluginInstantiateError

router = APIRouter()


@router.post("/api/workflows")
async def create_workflow(data: Dict[str, Any]):
    """创建并注册一个运行时 Workflow 实例。请求体应为工作流定义 JSON。

    返回：{"wf_id": <id>}。
    注意：这是一个简易注册器，仅用于本地/测试用途。
    """
    # 确定 id
    wf_id = str(data.get("id") or data.get("wf_id") or data.get("name"))
    if not wf_id:
        raise HTTPException(status_code=400, detail="workflow must include an id/name/wf_id")
    # 避免重复注册
    if get_workflow(wf_id):
        raise HTTPException(status_code=409, detail="workflow already exists")

    try:
        wf = Workflow(data)
        register_workflow(wf_id, wf)
    except (PluginImportError, PluginInstantiateError) as e:
        # plugin not found/instantiation failed -> return 400 with clear message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"wf_id": wf_id}


__all__ = ["router"]
