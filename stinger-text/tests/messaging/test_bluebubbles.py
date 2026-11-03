import json

import httpx
import pytest

from app.messaging import bluebubbles as bb

OK = {"status": 200, "message": "Success"}


@pytest.fixture(autouse=True)
async def setup(monkeypatch):
    monkeypatch.setenv("BB_URL", "http://bb.test")
    monkeypatch.setenv("BB_PASSWORD", "pw")
    monkeypatch.delenv("DRY_RUN", raising=False)

    async def nosleep(_):
        pass

    monkeypatch.setattr(bb.asyncio, "sleep", nosleep)
    yield
    await bb.aclose()
    bb.use_transport(None)


def install(handler):
    reqs = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        reqs.append(request)
        return handler(len(reqs), request)

    bb.use_transport(httpx.MockTransport(wrapped))
    return reqs


async def test_send_text_request_shape():
    reqs = install(lambda n, r: httpx.Response(200, json=OK))
    await bb.send_text("iMessage;-;+15550001111", "hi")
    await bb.send_text("iMessage;-;+15550001111", "hi")
    assert reqs[0].method == "POST"
    assert reqs[0].url.path == "/api/v1/message/text"
    assert reqs[0].url.params["password"] == "pw"
    b0, b1 = (json.loads(r.content) for r in reqs)
    assert set(b0) == {"chatGuid", "tempGuid", "message", "method"}
    assert b0["chatGuid"] == "iMessage;-;+15550001111"
    assert b0["message"] == "hi" and b0["method"] == "apple-script"
    assert b0["tempGuid"].startswith("temp-") and b0["tempGuid"] != b1["tempGuid"]


async def test_retry_on_5xx_not_on_4xx():
    reqs = install(lambda n, r: httpx.Response(500, json={}) if n == 1 else httpx.Response(200, json=OK))
    await bb.send_text("g", "hi")
    assert len(reqs) == 2

    reqs = install(lambda n, r: httpx.Response(400, json={"status": 400, "message": "bad field"}))
    with pytest.raises(bb.BlueBubblesError) as e:
        await bb.send_text("g", "secret text")
    assert len(reqs) == 1
    assert "400" in str(e.value) and "secret text" not in str(e.value)


async def test_dry_run_makes_no_requests(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    reqs = install(lambda n, r: httpx.Response(200, json=OK))
    await bb.send_text("iMessage;-;+15550001111", "hi")
    assert reqs == []


async def test_download_attachment():
    install(lambda n, r: httpx.Response(200, content=b"abc"))
    assert await bb.download_attachment("a1") == b"abc"
    install(lambda n, r: httpx.Response(200, content=b"x" * 1_000_001))
    with pytest.raises(bb.BlueBubblesError):
        await bb.download_attachment("a1")
