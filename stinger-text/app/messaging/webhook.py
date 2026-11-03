"""BlueBubbles webhook (owner: A, task A2). STUB from C1.

POST /webhook/bluebubbles. Stub: builds an Inbound from a minimal new-message
payload, runs admin then handler.handle(), sends each reply via
bluebubbles.send_text, and returns the replies in the response body.

A2 replaces this with: password check, isFromMe/group drop, guid dedupe, 200 within
100 ms and background processing, ack, and .vcf attachment download.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.core import handler
from app.messaging import admin, bluebubbles, location
from app.models import Inbound

router = APIRouter()


def inbound_from_payload(payload: dict) -> Inbound | None:
    if payload.get("type") != "new-message":
        return None
    data = payload.get("data") or {}
    if data.get("isFromMe"):
        return None
    text = data.get("text")
    user_id = ((data.get("handle") or {}).get("address")) or "unknown"
    chats = data.get("chats") or [{}]
    chat_guid = chats[0].get("guid") or f"iMessage;-;{user_id}"
    loc = location.extract_latlng(text or "")
    if loc is not None:
        text = None  # a bare map link counts as a pin
    return Inbound(user_id=user_id, chat_guid=chat_guid, text=text, location=loc, audio_path=None)


@router.post("/webhook/bluebubbles")
async def bluebubbles_webhook(request: Request) -> dict:
    payload = await request.json()
    msg = inbound_from_payload(payload)
    if msg is None:
        return {"ok": True, "replies": []}
    replies = admin.handle_admin(msg)
    if replies is None:
        replies = handler.handle(msg)
    for r in replies:
        bluebubbles.send_text(msg.chat_guid, r)
    return {"ok": True, "replies": replies}
