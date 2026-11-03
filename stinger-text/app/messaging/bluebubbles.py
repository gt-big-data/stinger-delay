import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

log = logging.getLogger(__name__)

MAX_TEXT = 2000
MAX_ATTACHMENT = 1_000_000

_client: Optional[httpx.AsyncClient] = None
_transport: Any = None


class BlueBubblesError(Exception):
    pass


def use_transport(transport: Any) -> None:
    """Tests inject httpx.MockTransport; drops any existing client."""
    global _client, _transport
    _transport = transport
    _client = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=os.environ.get("BB_URL", ""),
            timeout=10.0,
            params={"password": os.environ.get("BB_PASSWORD", "")},
            transport=_transport,
        )
    return _client


async def aclose() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def _request(method: str, path: str, **kw: Any) -> httpx.Response:
    """One retry after 1s on timeout, connection error, or 5xx. Never retries 4xx."""
    for attempt in (0, 1):
        try:
            resp = await _get_client().request(method, path, **kw)
        except (httpx.TimeoutException, httpx.ConnectError):
            if attempt == 1:
                raise BlueBubblesError("request failed: timeout/connection error")
        else:
            if resp.status_code < 500 or attempt == 1:
                return resp
        await asyncio.sleep(1)
    raise BlueBubblesError("unreachable")  # pragma: no cover


def _envelope(resp: httpx.Response) -> dict:
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


async def send_text(chat_guid: str, text: str) -> None:
    if len(text) > MAX_TEXT:
        raise ValueError(f"text too long ({len(text)} > {MAX_TEXT})")
    if os.environ.get("DRY_RUN") == "1":
        log.info("DRY_RUN send to ...%s", chat_guid[-4:])
        return
    # Body confirmed against the real server (S4, 2 Nov).
    body = {
        "chatGuid": chat_guid,
        "tempGuid": f"temp-{uuid.uuid4()}",
        "message": text,
        "method": "apple-script",
    }
    resp = await _request("POST", "/api/v1/message/text", json=body)
    env = _envelope(resp)
    if resp.status_code != 200 or env.get("status") != 200:
        raise BlueBubblesError(f"send failed: http {resp.status_code}, {env.get('message')}")
    log.info("sent to ...%s status=%s", chat_guid[-4:], resp.status_code)


async def download_attachment(attachment_guid: str) -> bytes:
    # TODO(SETUP): confirm this attachment endpoint against the real server.
    resp = await _request("GET", f"/api/v1/attachment/{attachment_guid}/download")
    if resp.status_code != 200:
        raise BlueBubblesError(f"download failed: http {resp.status_code}")
    if len(resp.content) > MAX_ATTACHMENT:
        raise BlueBubblesError("attachment over 1 MB refused")
    return resp.content


async def ping() -> bool:
    try:
        resp = await _request("GET", "/api/v1/ping")
    except BlueBubblesError:
        return False
    return resp.status_code == 200
