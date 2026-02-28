from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
import json
from Workflow.workflow import WorkflowEngine
from Server.utils import load_workflow

router = APIRouter(prefix="/runtime", tags=["runtime"])

# simple in-memory registry of running engines: workflow_id -> engine
RUNNING: Dict[str, WorkflowEngine] = {}


@router.post("/run")
async def run_workflow(body: Dict[str, Any]):
    """启动工作流并通过 Server-Sent Events 持续推送 `NodeStateList` 快照。

    POST body: {"workflow_id": "..."}
    返回: text/event-stream，每条 `data:` 为一个 JSON payload: {"workflow_id":..., "states":[{"node_id":..,"state":"..."}, ...]}
    """
    wid = body.get("workflow_id")
    if not wid:
        raise HTTPException(status_code=400, detail="workflow_id required")
    payload = load_workflow(wid)
    if payload is None:
        raise HTTPException(status_code=404, detail="workflow not found")

    engine = WorkflowEngine(payload)
    RUNNING[wid] = engine

    # start engine in background; try engine.start(), fallback to scheduling run_once
    try:
        engine.start()
    except Exception:
        loop = asyncio.get_event_loop()
        t = loop.create_task(engine.run_once())
        # ensure engine._task reflects the running task so emitter can detect completion
        setattr(engine, "_task", t)

    async def event_generator():
        # send initial snapshot
        states = []
        try:
            states = engine.listener.read()
            payload_out = {"workflow_id": wid, "states": states}
            yield f"data: {json.dumps(payload_out, ensure_ascii=False)}\n\n"
        except Exception:
            yield f"data: {json.dumps({'error': 'failed to read initial states'}, ensure_ascii=False)}\n\n"

        last_snapshot = json.dumps(states, sort_keys=True)

        # poll for changes until engine task finishes
        while True:
            await asyncio.sleep(0.5)
            try:
                states = engine.listener.read()
            except Exception:
                states = []

            snap = json.dumps(states, sort_keys=True)
            if snap != last_snapshot:
                payload_out = {"workflow_id": wid, "states": states}
                yield f"data: {json.dumps(payload_out, ensure_ascii=False)}\n\n"
                last_snapshot = snap

            # if background task finished, send final snapshot and close stream
            task = getattr(engine, "_task", None)
            if task is not None and task.done():
                try:
                    final = engine.listener.read()
                    payload_out = {"workflow_id": wid, "states": final}
                    yield f"data: {json.dumps(payload_out, ensure_ascii=False)}\n\n"
                except Exception:
                    pass
                break

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")


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
