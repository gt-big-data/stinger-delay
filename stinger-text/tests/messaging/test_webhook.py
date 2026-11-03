# TODO(SETUP): only bb_group is still a *.PLACEHOLDER.* fixture (never captured); the rest are real scrubbed captures.
import asyncio
import copy
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import handler
from app.messaging import bluebubbles, session
from scripts.dev_app import app

FIX = Path(__file__).resolve().parents[2] / "fixtures"
PW = "pw"


def fx(name: str) -> dict:
    f = FIX / f"{name}.json"
    if not f.exists():
        f = FIX / f"{name}.PLACEHOLDER.json"
    return json.loads(f.read_text())


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BB_PASSWORD", PW)
    session.reset_all()
    calls: list = []
    sent: list = []
    delay = {"s": 0}

    def fake_handle(msg):
        calls.append(msg)
        time.sleep(delay["s"])
        return ["ok"]

    async def fake_send(chat, text):
        sent.append((chat, text))

    monkeypatch.setattr(handler, "handle", fake_handle)
    monkeypatch.setattr(bluebubbles, "send_text", fake_send)
    with TestClient(app) as c:
        yield c, calls, delay
    session.reset_all()


def post(c, body, pw=PW):
    url = "/webhook/bluebubbles" + (f"?password={pw}" if pw is not None else "")
    return c.post(url, json=body)


def settle(calls, n, timeout=2.0):
    end = time.time() + timeout
    while len(calls) < n and time.time() < end:
        time.sleep(0.02)
    time.sleep(0.1)


def test_text_one_call(env):
    c, calls, _ = env
    assert post(c, fx("bb_text")).json() == {"ok": True}
    settle(calls, 1)
    assert len(calls) == 1
    assert calls[0].user_id == "+15550001111"
    assert calls[0].text == fx("bb_text")["data"]["text"]


@pytest.mark.parametrize("pw", [None, "wrong"])
def test_bad_password(env, pw):
    c, calls, _ = env
    assert post(c, fx("bb_text"), pw).status_code == 401
    settle(calls, 1, 0.3)
    assert calls == []


@pytest.mark.parametrize("name", ["bb_from_me", "bb_group"])
def test_dropped(env, name):
    c, calls, _ = env
    assert post(c, fx(name)).status_code == 200
    settle(calls, 1, 0.3)
    assert calls == []


def test_dedupe(env):
    c, calls, _ = env
    post(c, fx("bb_text"))
    post(c, fx("bb_text"))
    settle(calls, 2, 0.5)
    assert len(calls) == 1


def test_slow_handler_does_not_delay(env):
    c, calls, delay = env
    delay["s"] = 2
    t = time.perf_counter()
    assert post(c, fx("bb_text")).status_code == 200
    assert time.perf_counter() - t < 0.1


def test_other_type(env):
    c, calls, _ = env
    body = fx("bb_text")
    body["type"] = "typing-indicator"
    assert post(c, body).status_code == 200
    settle(calls, 1, 0.3)
    assert calls == []


def test_data_as_list(env):
    c, calls, _ = env
    body = copy.deepcopy(fx("bb_text"))
    body["data"] = [body["data"]]
    assert post(c, body).status_code == 200
    settle(calls, 1)
    assert len(calls) == 1 and calls[0].user_id == "+15550001111"
