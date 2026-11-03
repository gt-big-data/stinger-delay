"""Live feed cache and CSV replay.

Message handling calls ``get_arrivals()`` only. That reads the last poll
when the clock is live, and the recorded frame from ``clock.replay_frame``
in replay. The feed itself is touched only by the background poller.
"""

from __future__ import annotations

import csv
import json
import os
import threading
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.data import clock
from app.data.clock import ROUTE_GOLD, ROUTE_GREEN, ROUTE_RED, TZ
from app.models import StopArrival

ACTIVE = (ROUTE_RED, ROUTE_GREEN, ROUTE_GOLD)
_WEEKDAY = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

_frames: dict[tuple[int, int], list[StopArrival]] | None = None
_failures = 0
_cache: list[StopArrival] = []
_lock = threading.Lock()
_poller: threading.Thread | None = None
_stop = threading.Event()
_live_armed = False
_env_loaded = False


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        red = candidate / "Platform" / "red_line" / "data" / "red_line_data.csv"
        if red.is_file():
            return candidate
    raise FileNotFoundError("recorded CSVs not found above sources.py")


def _load_env() -> None:
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    for start in Path(__file__).resolve().parents:
        path = start / ".env"
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        break


def feed_host() -> str:
    _load_env()
    return os.environ.get("BUS_FEED_HOST", "bus.gatech.edu").strip() or "bus.gatech.edu"


def feed_key() -> str:
    _load_env()
    return os.environ.get("BUS_FEED_KEY", "8882812681").strip() or "8882812681"


def _stamp_key(moment: datetime) -> int:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=TZ)
    else:
        moment = moment.astimezone(TZ)
    return int(round(moment.timestamp() * 1_000_000))


def _parse_snapshot(raw: str, *, aware: bool) -> datetime:
    parsed = datetime.fromisoformat(raw.strip())
    if aware:
        return parsed.astimezone(TZ)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _load_frames() -> dict[tuple[int, int], list[StopArrival]]:
    root = _repo_root()
    grouped: dict[tuple[int, int], list[StopArrival]] = defaultdict(list)
    seen: set[tuple] = set()

    def add(route_id: int, snap: datetime, stop_id: int | None, vehicle_id: int | None, eta: float | None) -> None:
        if route_id not in ACTIVE or stop_id is None or vehicle_id is None or eta is None:
            return
        if eta < -30:
            return
        key = (route_id, _stamp_key(snap), stop_id, vehicle_id, round(eta, 3))
        if key in seen:
            return
        seen.add(key)
        grouped[(route_id, _stamp_key(snap))].append(
            StopArrival(route_id, stop_id, vehicle_id, float(eta))
        )

    red_path = root / "Platform" / "red_line" / "data" / "red_line_data.csv"
    with red_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw_snap = (row.get("snapshot_time_utc") or "").strip()
            if not raw_snap:
                continue
            add(
                _to_int(row.get("route_id")) or ROUTE_RED,
                _parse_snapshot(raw_snap, aware=True),
                _to_int(row.get("route_stop_id")),
                _to_int(row.get("vehicle_id")),
                _to_float(row.get("eta_seconds")),
            )

    folders = (
        (root / "Analysis" / "green_bus_data", "green_bus_*.csv", ROUTE_GREEN),
        (root / "Analysis" / "bus_data", "gt_gold_bus_data_*.csv", ROUTE_GOLD),
    )
    for folder, pattern, fallback in folders:
        for path in sorted(folder.glob(pattern)):
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    raw_snap = (row.get("snapshot_time") or "").strip()
                    raw_eta = (row.get("estimated_time_arrival") or "").strip()
                    if not raw_snap or not raw_eta:
                        continue
                    try:
                        snap = _parse_snapshot(raw_snap, aware=False)
                        eta_at = _parse_snapshot(raw_eta, aware=False)
                    except ValueError:
                        continue
                    add(
                        _to_int(row.get("route_id")) or fallback,
                        snap,
                        _to_int(row.get("route_stop_id")),
                        _to_int(row.get("vehicle_id")),
                        (eta_at - snap).total_seconds(),
                    )
    return dict(grouped)


def _ensure_frames() -> dict[tuple[int, int], list[StopArrival]]:
    global _frames
    if _frames is None:
        _frames = _load_frames()
    return _frames


def mode() -> str:
    return clock.mode()


def replay_arrivals() -> list[StopArrival]:
    frames = _ensure_frames()
    rows: list[StopArrival] = []
    for route_id in ACTIVE:
        frame = clock.replay_frame(route_id)
        if frame is None:
            continue
        rows.extend(frames.get((route_id, _stamp_key(frame)), ()))
    return rows


def ride_seconds(route_id: int, board_eta_s: float | None, alight_eta_s: float | None) -> float | None:
    """Green and Gold ride time when both stop ETAs exist.

    Red does not use this. Its ride time is the median segment run from the
    board stop to the alight stop, added to the next-stop ETA in the router.
    """
    if route_id == ROUTE_RED or board_eta_s is None or alight_eta_s is None:
        return None
    ride = alight_eta_s - board_eta_s
    if ride <= 0:
        return None
    return ride


def parse_live(payload) -> list[StopArrival]:
    rows: list[StopArrival] = []
    if not isinstance(payload, list):
        return rows
    for entry in payload:
        try:
            route_id = int(entry.get("RouteID"))
            stop_id = int(entry.get("RouteStopID"))
        except (TypeError, ValueError):
            continue
        if route_id not in ACTIVE:
            continue
        estimates = entry.get("VehicleEstimates") or entry.get("Estimates") or []
        for est in estimates:
            try:
                vehicle_id = int(est.get("VehicleID"))
                eta = float(est.get("SecondsToStop"))
            except (TypeError, ValueError):
                continue
            if eta < -30:
                continue
            rows.append(StopArrival(route_id, stop_id, vehicle_id, eta))
    return rows


def _fetch_live() -> list[StopArrival]:
    query = urllib.parse.urlencode({"apiKey": feed_key(), "isPublicMap": "true"})
    url = f"https://{feed_host()}/Services/JSONPRelay.svc/GetRouteStopArrivals?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "stinger-text/0.1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode())
    return parse_live(payload)


def _flip_to_replay() -> None:
    current = clock.now()
    clock.set_demo(_WEEKDAY[current.weekday()], f"{current.hour:02d}:{current.minute:02d}")


def record_poll_failure() -> None:
    """Count a failed live poll. The third consecutive failure returns the clock to replay."""
    global _failures
    with _lock:
        _failures += 1
        failed = _failures
    if failed >= 3 and clock.mode() == "LIVE":
        _flip_to_replay()


def record_poll_success(rows: list[StopArrival]) -> None:
    global _failures, _cache
    with _lock:
        _failures = 0
        _cache = list(rows)


def _poll_loop() -> None:
    while not _stop.is_set():
        if clock.mode() == "LIVE":
            try:
                record_poll_success(_fetch_live())
            except Exception:
                record_poll_failure()
        if _stop.wait(20):
            break


def ensure_poller() -> None:
    global _poller
    if _poller and _poller.is_alive():
        return
    _stop.clear()
    _poller = threading.Thread(target=_poll_loop, name="stinger-feed", daemon=True)
    _poller.start()


def get_arrivals() -> list[StopArrival]:
    """Cached live rows, or the replay frame for the demo clock. Does not call the feed."""
    global _live_armed, _failures
    if clock.mode() == "LIVE":
        if not _live_armed:
            with _lock:
                _failures = 0
            _live_armed = True
        ensure_poller()
        with _lock:
            return list(_cache)
    _live_armed = False
    return replay_arrivals()


def reset_state() -> None:
    """Clear live-poll bookkeeping. Replay frames stay cached."""
    global _failures, _cache, _live_armed
    with _lock:
        _failures = 0
        _cache = []
        _live_armed = False
