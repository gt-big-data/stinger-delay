import asyncio
import logging
import os
import re
from typing import Any

from app.core import handler
from app.messaging import admin, bluebubbles, gate, location, replies, session
from app.models import Inbound

log = logging.getLogger(__name__)
FINDMY_TEXT = "I can't read Find My locations. Share a pin from Apple Maps, or tell me a building name."


def normalize(address: str) -> str:
    a = address.strip()
    return a.lower() if "@" in a else re.sub(r"[^\d+]", "", a)


def _admins() -> set[str]:
    return {normalize(h) for h in os.environ.get("ADMIN_HANDLES", "").split(",") if h.strip()}


async def _send(chat: str, texts: list[str]) -> None:
    for t in texts:
        await bluebubbles.send_text(chat, t)


async def _ack(chat: str) -> None:
    try:
        await bluebubbles.send_text(chat, replies.ACK)
    except Exception as e:
        log.warning("ack failed: %s", type(e).__name__)


async def _answer(user_id: str, chat: str, text: str, loc: Any) -> None:
    await _ack(chat)
    # C's handler is sync and already appends the mode footer.
    out = await asyncio.wait_for(asyncio.to_thread(handler.handle, Inbound(user_id, chat, text, loc, None)), 12)
    await _send(chat, out)


async def process(event: dict) -> None:
    data = event.get("data")
    if isinstance(data, list):
        data = data[0] if len(data) == 1 else None
    if not isinstance(data, dict):
        return
    # 1. filter
    chats = data.get("chats") or []
    addr = (data.get("handle") or {}).get("address")
    text = (data.get("text") or "").replace("\ufffc", "").strip() or None  # drop attachment placeholder char
    findmy = "findmy" in str(data.get("balloonBundleId") or "").lower()  # "Send My Current Location": no coordinates
    atts = data.get("attachments") or []
    if data.get("isFromMe") or data.get("isGroup") or len(chats) != 1 or not addr:
        return
    chat = chats[0].get("guid") or ""
    if ";+;" in chat or not chat or not (text or atts or findmy):
        return
    guid = data.get("guid")
    # 2. dedupe
    if not guid or not session.mark_seen(guid):
        return
    # 3. normalize
    user_id = normalize(addr)
    tail = user_id[-4:]
    try:
        # 4. gate
        has_pin = findmy or any(location._is_loc(a) for a in atts) or (
            bool(text) and location.parse_map_text(text) is not None
        )
        allowed, cleaned = gate.allow(user_id, text, has_pin)
        if not allowed:
            return
        # 5. admin
        if admin.is_command(text):
            if user_id in _admins():
                await _send(chat, admin.run(user_id, text or ""))
            return
        # 6. pin
        loc = await location.extract(text, atts, bluebubbles)
        if loc:
            session.set_location(user_id, loc)
            pending = session.pop_pending(user_id)
            if pending:
                await _answer(user_id, chat, pending, loc)
            else:
                await bluebubbles.send_text(chat, "Got your location. Where to?")
            return
        if findmy:
            await bluebubbles.send_text(chat, FINDMY_TEXT)
            return
        # 7. text
        if not cleaned or not cleaned.strip():
            return
        await _answer(user_id, chat, cleaned, session.get_location(user_id))
    except Exception as e:
        # 8. errors
        log.error("pipeline failed for ...%s: %s", tail, type(e).__name__)
        replies.record_error("pipeline", e)
        msg = replies.TIMEOUT_TEXT if isinstance(e, asyncio.TimeoutError) else replies.ERROR_TEXT
        try:
            await bluebubbles.send_text(chat, msg)
        except Exception as e2:
            log.error("error reply failed: %s", type(e2).__name__)
