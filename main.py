
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
#各种服务
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




### FOR FRONT END
# 跨域设置（CORS）
# 说明：前端开发服务器通常运行在 http://localhost:5173，浏览器发起跨域请求时需允许。
# 这里允许来自本地开发服务器的跨域请求，生产环境可根据需要收紧来源。
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
