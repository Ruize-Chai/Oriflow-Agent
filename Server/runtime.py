from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
from Workflow.workflow import WorkflowEngine
from Server.utils import load_workflow

router = APIRouter(prefix="/runtime", tags=["runtime"])

# simple in-memory registry of running engines: workflow_id -> engine
RUNNING: Dict[str, WorkflowEngine] = {}


@router.post("/run")
async def run_workflow(body: Dict[str, Any]):
    wid = body.get("workflow_id")
    if not wid:
        raise HTTPException(status_code=400, detail="workflow_id required")
    payload = load_workflow(wid)
    if payload is None:
        raise HTTPException(status_code=404, detail="workflow not found")

    engine = WorkflowEngine(payload)
    RUNNING[wid] = engine
    # start in background
    try:
        engine.start()
    except Exception:
        # fallback: create a background task
        loop = asyncio.get_event_loop()
        loop.create_task(engine.run_once())

    # return initial node states
    return {"status": "started", "nodes": engine.listener.read()}


@router.post("/{workflow_id}/input/text")
def runtime_text_input(workflow_id: str, body: Dict[str, Any]):
    engine = RUNNING.get(workflow_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="workflow not running")
    node_id = body.get("node_id")
    value = body.get("value")
    if node_id is None or value is None:
        raise HTTPException(status_code=400, detail="node_id and value required")
    try:
        engine.in_hub.send(int(node_id), value)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/input/number")
def runtime_number_input(workflow_id: str, body: Dict[str, Any]):
    engine = RUNNING.get(workflow_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="workflow not running")
    node_id = body.get("node_id")
    value = body.get("value")
    if node_id is None or value is None:
        raise HTTPException(status_code=400, detail="node_id and value required")
    try:
        engine.in_hub.send(int(node_id), value)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/checkbox/{node_id}")
def runtime_checkbox_get(workflow_id: str, node_id: int):
    engine = RUNNING.get(workflow_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="workflow not running")
    try:
        return engine.ex_hub.read(int(node_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/checkbox/{node_id}")
def runtime_checkbox_post(workflow_id: str, node_id: int, body: Dict[str, Any]):
    engine = RUNNING.get(workflow_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="workflow not running")
    selection = body.get("selection")
    if selection is None:
        raise HTTPException(status_code=400, detail="selection required")
    try:
        engine.in_hub.send(int(node_id), {"selection": selection})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/chatbox/{node_id}")
def runtime_chatbox_get(workflow_id: str, node_id: int):
    engine = RUNNING.get(workflow_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="workflow not running")
    try:
        # fetch and clear so front-end gets one-time output
        return engine.ex_hub.fetch(int(node_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interrupt")
def runtime_interrupt():
    for e in list(RUNNING.values()):
        try:
            e.interrupt.set_true()
        except Exception:
            pass
    return {"status": "ok"}
