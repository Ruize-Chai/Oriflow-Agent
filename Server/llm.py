from fastapi import APIRouter, HTTPException
from Schema.payload.llm_api_payload import LLMApiPayload
from Workflow import llm_config

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/")
def get_llm():
    return llm_config.get_llm_api()


@router.post("/save")
def save_llm(payload: LLMApiPayload):
    try:
        llm_config.set_llm_api(api_key=payload.api_key, endpoint=payload.endpoint)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
