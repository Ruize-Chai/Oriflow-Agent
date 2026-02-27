from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Workflow import llm_config

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMPayload(BaseModel):
    api_key: str | None = None
    endpoint: str | None = None


@router.get("/")
def get_llm():
    return llm_config.get_llm_api()


@router.post("/save")
def save_llm(payload: LLMPayload):
    try:
        llm_config.set_llm_api(api_key=payload.api_key, endpoint=payload.endpoint)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
