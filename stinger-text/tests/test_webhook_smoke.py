"""C1 done-check: the app imports and a fake webhook returns a reply."""
from fastapi.testclient import TestClient

import time

import pytest

from app.core import handler
from app.main import app


@pytest.fixture(autouse=True)
def no_grok():
    handler.set_grok(None)  # never hit the real API from tests, even if .env has a key
    yield
    handler.set_grok(None)

FAKE_TEXT = {
    "type": "new-message",
    "data": {
        "guid": "fake-guid-1",
        "text": "Can I make it to West Village by 12:15?",
        "isFromMe": False,
        "handle": {"address": "+14045550123"},
        "chats": [{"guid": "iMessage;-;+14045550123"}],
        "attachments": [],
    },
}


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setenv("BB_PASSWORD", "pw")
    calls = []
    monkeypatch.setattr(handler, "handle", lambda msg: calls.append(msg) or ["ok"])
    return calls


def test_fake_webhook_returns_ok(env):
    with TestClient(app) as client:
        r = client.post("/webhook/bluebubbles?password=pw", json=FAKE_TEXT)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_wrong_password_rejected(env):
    with TestClient(app) as client:
        r = client.post("/webhook/bluebubbles?password=nope", json=FAKE_TEXT)
    assert r.status_code == 401


def test_is_from_me_dropped(env):
    payload = {**FAKE_TEXT, "data": {**FAKE_TEXT["data"], "isFromMe": True, "guid": "fake-guid-2"}}
    with TestClient(app) as client:
        r = client.post("/webhook/bluebubbles?password=pw", json=payload)
        time.sleep(0.2)
    assert r.status_code == 200
    assert env == []
