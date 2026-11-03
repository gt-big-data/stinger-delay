# TODO(SETUP): uses placeholder-style payloads; switch to scrubbed real fixtures once captured.
import pytest

from app.core import handler
from app.messaging import bluebubbles, pipeline, session
from app.models import LatLng

PIN = "http://maps.apple.com/?ll=33.77720,-84.39560&q=My%20Location"
KLAUS = LatLng(33.7772, -84.3956)
n = 0


def ev(user: str, text: str) -> dict:
    global n
    n += 1
    return {"type": "new-message", "data": {
        "guid": f"g{n}", "text": text, "handle": {"address": user},
        "chats": [{"guid": f"iMessage;-;{user}"}], "attachments": [], "isFromMe": False}}


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list:
    session.reset_all()
    rec: list = []

    def fake_handle(msg):
        rec.append(msg)
        return ["ok"]

    async def fake_send(chat, text):
        pass

    monkeypatch.setattr(handler, "handle", fake_handle)
    monkeypatch.setattr(bluebubbles, "send_text", fake_send)
    yield rec
    session.reset_all()


async def test_question_then_pin(calls):
    session.set_pending("+15550001111", "to Klaus?")
    await pipeline.process(ev("+15550001111", PIN))
    assert len(calls) == 1
    assert calls[0].text == "to Klaus?" and calls[0].location == KLAUS
    await pipeline.process(ev("+15550001111", PIN))
    assert len(calls) == 1


async def test_pin_then_question(calls):
    await pipeline.process(ev("+15550001111", PIN))
    assert calls == []
    await pipeline.process(ev("+15550001111", "to Klaus?"))
    assert calls[0].location == KLAUS


async def test_users_independent(calls):
    await pipeline.process(ev("+15550001111", PIN))
    await pipeline.process(ev("+15550002222", "to Klaus?"))
    assert calls[0].user_id == "+15550002222" and calls[0].location is None


async def test_findmy_share_gets_guidance_not_handler(monkeypatch):
    # Real iOS "Send My Current Location": Find My balloon, text is only U+FFFC, no attachments.
    sent, calls = [], []
    async def fake_send(chat, text): sent.append(text)
    def fake_handle(msg): calls.append(msg); return ["x"]
    monkeypatch.setattr(pipeline.bluebubbles, "send_text", fake_send)
    monkeypatch.setattr(pipeline.handler, "handle", fake_handle)
    session.reset_all()
    ev = {"type": "new-message", "data": {"guid": "fm-1", "text": "￼", "handle": {"address": "+15550001111"},
          "chats": [{"guid": "any;-;+15550001111"}], "attachments": [], "isFromMe": False,
          "balloonBundleId": "com.apple.messages.MSMessageExtensionBalloonPlugin:0:com.apple.findmy.FindMyMessagesApp"}}
    await pipeline.process(ev)
    assert sent == [pipeline.FINDMY_TEXT] and calls == []
