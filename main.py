
from fastapi import FastAPI
from pydantic import BaseModel

from Server.comm_adapter import router as comm_router
from Server.workflow_manage.create_workflow import router as wf_manage_router
from Server.api_keys import router as keys_router

app = FastAPI(title="Oriflow Minimal API")

# mount comm adapter routes
app.include_router(comm_router)
app.include_router(wf_manage_router)
app.include_router(keys_router)


class HealthResponse(BaseModel):
    status: str
    version: str | None = None


@app.get("/", response_model=HealthResponse)
async def root():
    return {"status": "ok", "version": None}


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy", "version": None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
