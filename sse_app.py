# sse_app.py
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_stream():
    # 模拟持续输出进度/日志
    for i in range(1, 6):
        yield f"data: step {i}\n\n"
        await asyncio.sleep(1)
    yield "data: done\n\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")