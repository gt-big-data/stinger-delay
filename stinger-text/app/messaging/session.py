import time
from typing import Any, Optional

from app.models import LatLng

_now = time.monotonic

LOC_TTL = 15 * 60
PENDING_TTL = 10 * 60
SEEN_TTL = 10 * 60
WIN_TTL = 10 * 60
MAX_ENTRIES = 2000


class TTLStore:
    def __init__(self, max_entries: int = MAX_ENTRIES) -> None:
        self._d: dict[str, tuple[float, Any]] = {}
        self._max = max_entries

    def purge(self) -> None:
        now = _now()
        for k in [k for k, (exp, _) in self._d.items() if exp <= now]:
            del self._d[k]

    def set(self, key: str, value: Any, ttl: float) -> None:
        self.purge()
        self._d.pop(key, None)  # re-insert so dict order == age
        self._d[key] = (_now() + ttl, value)
        while len(self._d) > self._max:
            del self._d[next(iter(self._d))]

    def get(self, key: str) -> Any:
        item = self._d.get(key)
        if item is None or item[0] <= _now():
            return None
        return item[1]

    def pop(self, key: str) -> Any:
        value = self.get(key)
        self._d.pop(key, None)
        return value

    def __len__(self) -> int:
        return len(self._d)


_store = TTLStore()


def set_location(user_id: str, loc: LatLng) -> None:
    _store.set(f"loc:{user_id}", loc, LOC_TTL)


def get_location(user_id: str) -> Optional[LatLng]:
    return _store.get(f"loc:{user_id}")


def set_pending(user_id: str, text: Optional[str]) -> None:
    if text is None:  # C's handler clears the pending question with None
        _store.pop(f"pending:{user_id}")
    else:
        _store.set(f"pending:{user_id}", text, PENDING_TTL)


def get_pending(user_id: str) -> Optional[str]:
    return _store.get(f"pending:{user_id}")


def pop_pending(user_id: str) -> Optional[str]:
    return _store.pop(f"pending:{user_id}")


def mark_seen(guid: str) -> bool:
    key = f"seen:{guid}"
    if _store.get(key) is not None:
        return False
    _store.set(key, True, SEEN_TTL)
    return True


def open_window(user_id: str) -> None:
    _store.set(f"win:{user_id}", True, WIN_TTL)


def in_window(user_id: str) -> bool:
    return _store.get(f"win:{user_id}") is not None


def reset_all() -> None:
    _store._d.clear()

clear_all = reset_all  # name C's tests use
