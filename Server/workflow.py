from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from pydantic import BaseModel
from Server.utils import save_workflow, load_workflow, delete_workflow, read_workflow_lists
import uuid

router = APIRouter(prefix="/workflow", tags=["workflow"])


class WorkflowPayload(BaseModel):
    id: str | None = None
    name: str | None = None
    nodes: list | None = None


@router.post("/create")
def create_workflow(payload: WorkflowPayload):
    wid = payload.id or str(uuid.uuid4())
    data = payload.dict()
    data["id"] = wid
    save_workflow(wid, data)
    return {"status": "ok", "id": wid}


@router.post("/alter")
def alter_workflow(payload: WorkflowPayload):
    if not payload.id:
        raise HTTPException(status_code=400, detail="workflow id required")
    save_workflow(payload.id, payload.dict())
    return {"status": "ok", "id": payload.id}


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str):
    wf = load_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return wf


@router.post("/delete")
def remove_workflow(body: dict):
    wid = body.get("id")
    if not wid:
        raise HTTPException(status_code=400, detail="workflow id required")
    ok = delete_workflow(wid)
    if not ok:
        raise HTTPException(status_code=500, detail="delete failed")
    return {"status": "ok"}


@router.get("/list")
def list_workflows():
    return read_workflow_lists()
