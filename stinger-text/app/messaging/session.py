"""Per-user sessions, in memory only (owner: A, task A5). STUB from C1.

Contract:
    get_location(user_id) -> Optional[LatLng]       15-min TTL
    set_location(user_id, loc: LatLng) -> None
    get_pending(user_id) -> Optional[str]           question waiting for a location, 10-min TTL
    set_pending(user_id, text) -> None               text=None clears it (contract point for A)

Stub uses time.monotonic for TTLs (not wall-clock time, so the demo clock does not
affect expiry). Nothing is written to disk.
"""
from __future__ import annotations

import time
from typing import Optional

from app.models import LatLng

LOC_TTL_S = 15 * 60
PENDING_TTL_S = 10 * 60

_store: dict[str, tuple[object, float]] = {}


def _get(key: str):
    item = _store.get(key)
    if item is None:
        return None
    value, expires = item
    if time.monotonic() >= expires:
        _store.pop(key, None)
        return None
    return value


def get_location(user_id: str) -> Optional[LatLng]:
    return _get(f"loc:{user_id}")  # type: ignore[return-value]


def set_location(user_id: str, loc: LatLng) -> None:
    _store[f"loc:{user_id}"] = (loc, time.monotonic() + LOC_TTL_S)


def get_pending(user_id: str) -> Optional[str]:
    return _get(f"pending:{user_id}")  # type: ignore[return-value]


def set_pending(user_id: str, text: Optional[str]) -> None:
    if text is None:
        _store.pop(f"pending:{user_id}", None)
    else:
        _store[f"pending:{user_id}"] = (text, time.monotonic() + PENDING_TTL_S)


def clear_all() -> None:  # test helper
    _store.clear()
