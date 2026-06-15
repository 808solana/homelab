"""Love — FastAPI orchestration service (M1).

Pipeline proven here: query -> rules router -> OpenRouter inference -> stream.
Search, logging, and the full Love reshape pass are later milestones.

The /api/chat endpoint streams Server-Sent Events. The first frame is metadata
(which model, which route, why) so the UI can show attribution before the answer
arrives — transparency is the brand. Then token frames, then a done frame.
"""
from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, love, openrouter, router

app = FastAPI(title=config.APP_TITLE)


class ChatRequest(BaseModel):
    query: str


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "models": config.MODELS}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    route, why = router.choose_route(req.query)
    model = config.MODELS.get(route, config.MODELS["default"])

    messages = [
        {"role": "system", "content": love.LOVE_SYSTEM_PROMPT},
        {"role": "user", "content": req.query},
    ]

    async def gen():
        yield _sse({"type": "meta", "model": model, "route": route, "why": why})
        try:
            async for token in openrouter.stream_chat(model, messages):
                yield _sse({"type": "token", "text": token})
        except Exception as exc:  # surfaced to the UI in Love's voice
            yield _sse({"type": "error", "text": str(exc)})
        yield _sse({"type": "done"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Tell Nginx / NPM not to buffer this response (needed for streaming).
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("static/index.html")


# Static assets (none yet beyond index.html, but wired for later).
app.mount("/static", StaticFiles(directory="static"), name="static")
