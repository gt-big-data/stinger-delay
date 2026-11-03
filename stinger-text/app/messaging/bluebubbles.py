"""BlueBubbles REST client (owner: A, task A3). STUB from C1.

Contract:
    send_text(chat_guid: str, text: str) -> None

Stub: logs and records to OUTBOX instead of calling BlueBubbles.
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

OUTBOX: list[tuple[str, str]] = []


def send_text(chat_guid: str, text: str) -> None:
    log.info("[stub send_text] %s: %s", chat_guid, text)
    OUTBOX.append((chat_guid, text))


def download_attachment(attachment_guid: str) -> Optional[bytes]:
    """Stub: A3 downloads via the BlueBubbles attachment endpoint."""
    return None
