import asyncio
import os
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.messaging import pipeline

router = APIRouter()
_tasks: set[asyncio.Task] = set()


@router.post("/webhook/bluebubbles")
async def bluebubbles_webhook(request: Request, password: str = "") -> JSONResponse:
    expected = os.environ.get("BB_PASSWORD", "")
    if not expected or not secrets.compare_digest(password.encode(), expected.encode()):
        return JSONResponse({"ok": False}, status_code=401)
    try:
        event = await request.json()
    except Exception:
        return JSONResponse({"ok": True})
    if not isinstance(event, dict) or event.get("type") != "new-message":
        return JSONResponse({"ok": True})
    data = event.get("data")
    if isinstance(data, list):
        data = data[0] if len(data) == 1 else None
    if isinstance(data, dict):
        task = asyncio.create_task(pipeline.process({**event, "data": data}))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    return JSONResponse({"ok": True})
