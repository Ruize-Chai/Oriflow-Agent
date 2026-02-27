
from fastapi import FastAPI
from pydantic import BaseModel

from Server.plugins import router as plugins_router
from Server.workflow import router as workflow_router
from Server.runtime import router as runtime_router
from Server.llm import router as llm_router
from Server.filebase import router as filebase_router


app = FastAPI(title="Oriflow API")


class HealthResponse(BaseModel):
    status: str
    version: str | None = None


@app.get("/", response_model=HealthResponse)
async def root():
    return {"status": "ok", "version": None}


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy", "version": None}


# include server routers
app.include_router(plugins_router)
app.include_router(workflow_router)
app.include_router(runtime_router)
app.include_router(llm_router)
app.include_router(filebase_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
