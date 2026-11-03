"""Minimal webhook sink: saves raw BlueBubbles events to fixtures/raw/. Never prints message text."""
import json
import os
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

RAW = Path(__file__).resolve().parent.parent / "fixtures" / "raw"
app = FastAPI()


def _norm(h: str) -> str:
    h = h.strip()
    return h.lower() if "@" in h else "".join(c for c in h if c.isdigit() or c == "+")


def _admins() -> set[str]:
    return {_norm(h) for h in os.environ.get("ADMIN_HANDLES", "").split(",") if h.strip()}


def _is_admin_dm(data: dict) -> bool:
    """Personal-ID safety: save only DMs with an admin handle (their texts or our replies to them)."""
    chats = data.get("chats") or []
    guid = str(chats[0].get("guid", "")) if len(chats) == 1 else ""
    if ";-;" not in guid:
        return False
    return _norm(guid.split(";-;", 1)[1]) in _admins()


@app.post("/webhook/bluebubbles")
async def webhook(request: Request) -> dict:
    body = await request.json()
    etype = str(body.get("type", "unknown")) if isinstance(body, dict) else "unknown"
    safe = "".join(ch for ch in etype if ch.isalnum() or ch in "-_")
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        data = {}
    if not _is_admin_dm(data):
        print(f"{etype} skipped (not an admin DM)", flush=True)
        return {"ok": True}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{time.time_ns()}_{safe}.json").write_text(json.dumps(body, indent=2))
    chats = data.get("chats") or [{}]
    chat_guid = str(chats[0].get("guid", ""))
    kind = "group" if ";+;" in chat_guid else "dm"
    names = [a.get("transferName") for a in data.get("attachments") or []]
    print(f"{etype} isFromMe={data.get('isFromMe')} {kind} attachments={len(names)} {names}", flush=True)
    return {"ok": True}


if __name__ == "__main__":
    # access_log off: the request line would include ?password=...
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    uvicorn.run(app, host=["127.0.0.1", "::1"], port=8000, access_log=False, log_level="warning")
