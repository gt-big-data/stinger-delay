import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import capture_webhook as cw  # noqa: E402


def _ev(chat_guid: str) -> dict:
    return {"type": "new-message", "data": {"guid": "g", "text": "x", "handle": {"address": "+15550002222"},
                                            "chats": [{"guid": chat_guid}], "attachments": [], "isFromMe": False}}


def test_only_admin_dms_are_saved(monkeypatch, tmp_path):
    monkeypatch.setattr(cw, "RAW", tmp_path)
    monkeypatch.setenv("ADMIN_HANDLES", "+1 (555) 000-2222")
    c = TestClient(cw.app)
    c.post("/webhook/bluebubbles", json=_ev("iMessage;-;+15550002222"))
    assert len(list(tmp_path.glob("*.json"))) == 1
    for guid in ("iMessage;-;+15559999999", "iMessage;+;chat123"):
        c.post("/webhook/bluebubbles", json=_ev(guid))
    assert len(list(tmp_path.glob("*.json"))) == 1
