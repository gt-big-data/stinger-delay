import asyncio
import time
from datetime import datetime

import pytest

from app.core import handler
from app.data import clock, sources
from app.messaging import bluebubbles, pipeline, replies, session

USER = "+15550001111"
n = 0


def ev(text: str) -> dict:
    global n
    n += 1
    return {"type": "new-message", "data": {
        "guid": f"r{n}", "text": text, "handle": {"address": USER},
        "chats": [{"guid": f"iMessage;-;{USER}"}], "attachments": [], "isFromMe": False}}


def test_footer(monkeypatch):
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 3, 3, 12, 0))
    monkeypatch.setattr(sources, "mode", lambda: "REPLAY")
    assert replies.with_footer(["a", "b"]) == ["a", "b\n[REPLAY Tue 3 Mar 12:00]"]
    assert replies.with_footer([]) == []
    monkeypatch.setattr(sources, "mode", lambda: "LIVE")
    assert replies.footer() == "[LIVE]"


@pytest.fixture
def sent(monkeypatch):
    session.reset_all()
    out: list = []

    async def fake_send(chat, text):
        out.append(text)

    monkeypatch.setattr(bluebubbles, "send_text", fake_send)
    monkeypatch.setattr(sources, "mode", lambda: "LIVE")
    monkeypatch.setattr(replies, "LAST_ERROR", None)
    yield out
    session.reset_all()


async def test_ack_before_handler(sent, monkeypatch):
    def slow(msg):
        sent.append("HANDLER")
        time.sleep(0.2)
        return ["ok"]

    monkeypatch.setattr(handler, "handle", slow)
    await pipeline.process(ev("to Klaus?"))
    assert sent == [replies.ACK, "HANDLER", "ok"]


async def test_ack_failure_does_not_block(sent, monkeypatch):
    async def send(chat, text):
        if text == replies.ACK:
            raise RuntimeError("boom")
        sent.append(text)

    def fast(msg):
        return ["ok"]

    monkeypatch.setattr(bluebubbles, "send_text", send)
    monkeypatch.setattr(handler, "handle", fast)
    await pipeline.process(ev("to Klaus?"))
    assert sent == ["ok"]


async def test_handler_error(sent, monkeypatch):
    def bad(msg):
        raise ValueError("secret user text")

    monkeypatch.setattr(handler, "handle", bad)
    await pipeline.process(ev("to Klaus?"))
    assert sent == [replies.ACK, replies.ERROR_TEXT]
    assert replies.LAST_ERROR == "pipeline: ValueError"


async def test_handler_timeout(sent, monkeypatch):
    def slow(msg):
        time.sleep(0.5)

    real = asyncio.wait_for
    monkeypatch.setattr(asyncio, "wait_for", lambda c, t: real(c, 0.1))
    monkeypatch.setattr(handler, "handle", slow)
    await pipeline.process(ev("to Klaus?"))
    assert sent == [replies.ACK, replies.TIMEOUT_TEXT]
    assert replies.LAST_ERROR == "pipeline: TimeoutError"
