import logging

import pytest

from app.core import handler
from app.messaging import bluebubbles, gate, pipeline, session
from app.models import LatLng

U = "+15550001111"
ADMIN = "+15550009999"
PIN = "http://maps.apple.com/?ll=33.77720,-84.39560&q=My%20Location"
n = 0


def ev(user: str, text: str) -> dict:
    global n
    n += 1
    return {"type": "new-message", "data": {
        "guid": f"gate{n}", "text": text, "handle": {"address": user},
        "chats": [{"guid": f"iMessage;-;{user}"}], "attachments": [], "isFromMe": False}}


@pytest.fixture
def rig(monkeypatch: pytest.MonkeyPatch):
    session.reset_all()
    monkeypatch.setenv("TRIGGER_WORD", "stinger")
    monkeypatch.setenv("ADMIN_HANDLES", ADMIN)
    handled: list = []
    sent: list = []

    def fake_handle(msg):
        handled.append(msg)
        return ["ok"]

    async def fake_send(chat, text):
        sent.append(text)

    monkeypatch.setattr(handler, "handle", fake_handle)
    monkeypatch.setattr(bluebubbles, "send_text", fake_send)
    yield handled, sent
    session.reset_all()


async def test_ignored_message_no_handler_no_send(rig):
    handled, sent = rig
    await pipeline.process(ev(U, "hey mom call me"))
    assert handled == [] and sent == []


async def test_trigger_stripped(rig):
    handled, _ = rig
    await pipeline.process(ev(U, "Stinger can I make it to Klaus"))
    await pipeline.process(ev(U, "STINGER, can I make it to Klaus"))
    assert [h.text for h in handled] == ["can I make it to Klaus"] * 2


def test_stingers_ignored(rig):
    assert gate.allow(U, "stingers are cool", False) == (False, None)


def test_pin_needs_window(monkeypatch):
    monkeypatch.setenv("TRIGGER_WORD", "stinger")
    session.reset_all()
    assert gate.allow(U, PIN, True) == (False, None)
    assert gate.allow(U, "stinger hi", False)[0]
    assert gate.allow(U, PIN, True) == (True, PIN)


def test_followup_window_and_expiry(monkeypatch):
    monkeypatch.setenv("TRIGGER_WORD", "stinger")
    session.reset_all()
    t = [1000.0]
    monkeypatch.setattr(session, "_now", lambda: t[0])
    gate.allow(U, "stinger hi", False)
    t[0] += 9 * 60
    assert gate.allow(U, "West Village by 12:15", False)[0]  # restarts window
    t[0] += 9 * 60
    assert gate.allow(U, "and then?", False)[0]
    t[0] += 11 * 60
    assert gate.allow(U, "too late", False) == (False, None)
    session.reset_all()


async def test_admin_bypass(rig):
    handled, sent = rig
    await pipeline.process(ev(ADMIN, "/status"))
    assert sent and handled == []
    await pipeline.process(ev(ADMIN, "is it busy at Klaus"))
    assert [h.text for h in handled] == ["is it busy at Klaus"]


def test_empty_trigger_allows_all(monkeypatch):
    monkeypatch.setenv("TRIGGER_WORD", "")
    assert gate.allow(U, "anything", False) == (True, "anything")
    assert gate.allow(U, None, True) == (True, None)


async def test_no_log_of_ignored_text(rig, caplog):
    caplog.set_level(logging.DEBUG)
    await pipeline.process(ev(U, "secret dinner plans"))
    assert "secret dinner plans" not in caplog.text
