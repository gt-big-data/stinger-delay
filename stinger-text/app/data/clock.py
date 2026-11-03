"""Demo clock for StingerText.

App logic must call ``now()``. The only wall-clock read in this package is
``_system_wall``; replay time is ``anchor + (wall_now - set_at)``.

Default mode is REPLAY anchored at Tuesday 12:00 America/New_York on the
recorded date that actually covers that weekday and time.

``set_demo(weekday, hhmm)`` maps each route onto a recorded date that has a
snapshot at or before the requested minute, at most 60 seconds old:

1. same weekday with that coverage
2. else any weekday with that coverage
3. else the route has no service (``route_time`` / ``replay_frame`` are None)

The clock's own ``now()`` uses a same-weekday covered date when any route has
one, so Tuesday 09:20 stays on Tuesday 2026-03-03 (Red).
"""

from __future__ import annotations

import csv
from bisect import bisect_right
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal, Optional
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
STALE_S = 60

ROUTE_RED = 20
ROUTE_GREEN = 17
ROUTE_GOLD = 29
ROUTE_IDS = (ROUTE_RED, ROUTE_GREEN, ROUTE_GOLD)

DEFAULT_WEEKDAY = "Tue"
DEFAULT_HHMM = "12:00"

Mode = Literal["LIVE", "REPLAY"]

_WEEKDAYS = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def _system_wall() -> datetime:
    """Sole ``datetime.now`` read. Everything else calls ``now()``."""
    return datetime.now(TZ)


def _as_ny(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        red = candidate / "Platform" / "red_line" / "data" / "red_line_data.csv"
        if red.is_file():
            return candidate
    raise FileNotFoundError("recorded CSVs not found above clock.py")


def _parse_snapshot(raw: str, *, aware: bool) -> datetime:
    dt = datetime.fromisoformat(raw)
    if aware:
        return dt.astimezone(TZ)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def _read_column(path: Path, column: str, *, aware: bool) -> set[datetime]:
    found: set[datetime] = set()
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            raw = row.get(column)
            if raw:
                found.add(_parse_snapshot(raw, aware=aware))
    return found


@lru_cache(maxsize=1)
def snapshots_by_route() -> dict[int, dict[date, tuple[datetime, ...]]]:
    """Unique America/New_York snapshot times grouped by route and local date."""
    root = _repo_root()
    buckets: dict[int, set[datetime]] = {route_id: set() for route_id in ROUTE_IDS}

    red_csv = root / "Platform" / "red_line" / "data" / "red_line_data.csv"
    buckets[ROUTE_RED].update(
        _read_column(red_csv, "snapshot_time_utc", aware=True)
    )

    for path in sorted((root / "Analysis" / "green_bus_data").glob("*.csv")):
        buckets[ROUTE_GREEN].update(
            _read_column(path, "snapshot_time", aware=False)
        )

    for path in sorted((root / "Analysis" / "bus_data").glob("gt_gold_bus_data_*.csv")):
        buckets[ROUTE_GOLD].update(
            _read_column(path, "snapshot_time", aware=False)
        )

    grouped: dict[int, dict[date, tuple[datetime, ...]]] = {}
    for route_id, stamps in buckets.items():
        by_date: dict[date, list[datetime]] = {}
        for stamp in stamps:
            by_date.setdefault(stamp.date(), []).append(stamp)
        grouped[route_id] = {
            day: tuple(sorted(day_stamps)) for day, day_stamps in by_date.items()
        }
    return grouped


def fresh_frame(stamps: tuple[datetime, ...] | list[datetime], target: datetime) -> Optional[datetime]:
    """Nearest snapshot at or before ``target``, or None if it is >60s stale."""
    if not stamps:
        return None
    index = bisect_right(stamps, target) - 1
    if index < 0:
        return None
    snap = stamps[index]
    if (target - snap).total_seconds() > STALE_S:
        return None
    return snap


def parse_weekday(weekday: str) -> int:
    key = weekday.strip().lower()
    if key not in _WEEKDAYS:
        raise ValueError(f"unknown weekday: {weekday!r}")
    return _WEEKDAYS[key]


def parse_hhmm(hhmm: str) -> time:
    text = hhmm.strip()
    hour_s, _, minute_s = text.partition(":")
    if not minute_s or hour_s == "":
        raise ValueError(f"expected HH:MM, got {hhmm!r}")
    hour = int(hour_s)
    minute = int(minute_s)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"expected HH:MM, got {hhmm!r}")
    return time(hour, minute)


def _at(day: date, tod: time) -> datetime:
    return datetime.combine(day, tod, tzinfo=TZ)


def _covered_dates(route_id: int, tod: time) -> list[date]:
    grouped = snapshots_by_route().get(route_id, {})
    covered: list[date] = []
    for day, stamps in grouped.items():
        if fresh_frame(stamps, _at(day, tod)) is not None:
            covered.append(day)
    return covered


def _pick_date(covered: list[date], weekday: int) -> Optional[date]:
    same = [day for day in covered if day.weekday() == weekday]
    pool = same or covered
    if not pool:
        return None
    return max(pool)


def _fallback_day(weekday: int) -> date:
    days = [day for grouped in snapshots_by_route().values() for day in grouped]
    same = [day for day in days if day.weekday() == weekday]
    if same:
        return max(same)
    if days:
        return max(days)
    return date(2026, 3, 3)


class DemoClock:
    """Replay/live clock. Construct with ``wall`` to freeze time in tests."""

    def __init__(self, wall: Optional[Callable[[], datetime]] = None):
        self._wall = wall or _system_wall
        self._mode: Mode = "REPLAY"
        self._epoch = 0
        self._anchor = _at(date(2026, 3, 3), time(12, 0))
        self._set_at = _as_ny(self._wall())
        self._route_dates: dict[int, Optional[date]] = {route_id: None for route_id in ROUTE_IDS}
        self.set_demo(DEFAULT_WEEKDAY, DEFAULT_HHMM)

    def mode(self) -> Mode:
        return self._mode

    def epoch(self) -> int:
        """Increments on every ``set_live`` / ``set_demo``. Live polls key off this."""
        return self._epoch

    def now(self) -> datetime:
        if self._mode == "LIVE":
            return _as_ny(self._wall())
        return self._anchor + (_as_ny(self._wall()) - self._set_at)

    def set_live(self) -> None:
        self._mode = "LIVE"
        self._set_at = _as_ny(self._wall())
        self._epoch += 1

    def set_demo(self, weekday: str, hhmm: str) -> datetime:
        """Enter replay at ``weekday`` ``hhmm`` and return the anchor instant."""
        week = parse_weekday(weekday)
        tod = parse_hhmm(hhmm)
        route_dates: dict[int, Optional[date]] = {}
        for route_id in ROUTE_IDS:
            route_dates[route_id] = _pick_date(_covered_dates(route_id, tod), week)

        matched = [day for day in route_dates.values() if day is not None and day.weekday() == week]
        fallback = [day for day in route_dates.values() if day is not None]
        anchor_day = max(matched) if matched else (max(fallback) if fallback else _fallback_day(week))

        self._mode = "REPLAY"
        self._anchor = _at(anchor_day, tod)
        self._set_at = _as_ny(self._wall())
        self._route_dates = route_dates
        self._epoch += 1
        return self._anchor

    def route_time(self, route_id: int) -> Optional[datetime]:
        """Recorded instant for ``route_id``, advanced with the demo clock.

        None when that route has no recorded service at the demo time.
        In live mode this is the wall clock.
        """
        if self._mode == "LIVE":
            return self.now()
        recorded = self._route_dates.get(route_id)
        if recorded is None:
            return None
        current = self.now()
        shifted = recorded + (current.date() - self._anchor.date())
        return datetime.combine(shifted, current.timetz())

    def replay_frame(self, route_id: int) -> Optional[datetime]:
        """Nearest recorded snapshot at or before the mapped time, else None if >60s stale."""
        if self._mode != "REPLAY":
            return None
        target = self.route_time(route_id)
        if target is None:
            return None
        stamps = snapshots_by_route().get(route_id, {}).get(target.date())
        if not stamps:
            return None
        return fresh_frame(stamps, target)


_default: Optional[DemoClock] = None


def _clock() -> DemoClock:
    global _default
    if _default is None:
        _default = DemoClock()
    return _default


def reset(wall: Optional[Callable[[], datetime]] = None) -> DemoClock:
    """Replace the process clock. Tests pass a frozen ``wall``."""
    global _default
    _default = DemoClock(wall=wall)
    return _default


def now() -> datetime:
    return _clock().now()


def mode() -> Mode:
    return _clock().mode()


def epoch() -> int:
    return _clock().epoch()


def set_demo(weekday: str, hhmm: str) -> datetime:
    return _clock().set_demo(weekday, hhmm)


def set_live() -> None:
    _clock().set_live()


def route_time(route_id: int) -> Optional[datetime]:
    return _clock().route_time(route_id)


def replay_frame(route_id: int) -> Optional[datetime]:
    return _clock().replay_frame(route_id)
