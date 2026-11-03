"""Demo clock: default Tuesday noon replay, and set_demo('Tue', '09:20')."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.data.clock import (
    ROUTE_GOLD,
    ROUTE_GREEN,
    ROUTE_RED,
    TZ,
    DemoClock,
    fresh_frame,
)

FROZEN = datetime(2026, 11, 3, 15, 0, tzinfo=TZ)


def _frozen_wall(start: datetime = FROZEN):
    state = {"now": start}

    def wall() -> datetime:
        return state["now"]

    def advance(seconds: float) -> None:
        state["now"] = state["now"] + timedelta(seconds=seconds)

    return wall, advance


class ClockTests(unittest.TestCase):
    def test_default_is_replay_tuesday_noon(self) -> None:
        wall, _advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        self.assertEqual(clock.mode(), "REPLAY")
        current = clock.now()
        self.assertEqual(current.strftime("%a"), "Tue")
        self.assertEqual(current.hour, 12)
        self.assertEqual(current.minute, 0)
        self.assertEqual(current.date().isoformat(), "2026-03-03")
        self.assertEqual(str(current.tzinfo), "America/New_York")
        red = clock.route_time(ROUTE_RED)
        self.assertIsNotNone(red)
        assert red is not None
        self.assertEqual(red.date().isoformat(), "2026-03-03")
        frame = clock.replay_frame(ROUTE_RED)
        self.assertIsNotNone(frame)
        assert frame is not None
        self.assertLessEqual(frame, red)
        self.assertLessEqual((red - frame).total_seconds(), 60)

    def test_set_demo_tue_0920_maps_onto_recorded_tuesday(self) -> None:
        wall, _advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        anchor = clock.set_demo("Tue", "09:20")

        self.assertEqual(clock.mode(), "REPLAY")
        self.assertEqual(anchor, datetime(2026, 3, 3, 9, 20, tzinfo=TZ))
        self.assertEqual(clock.now(), anchor)
        self.assertEqual(clock.now().strftime("%a %H:%M"), "Tue 09:20")

        red = clock.route_time(ROUTE_RED)
        self.assertEqual(red, datetime(2026, 3, 3, 9, 20, tzinfo=TZ))
        red_frame = clock.replay_frame(ROUTE_RED)
        self.assertIsNotNone(red_frame)
        assert red_frame is not None
        self.assertEqual(red_frame.date().isoformat(), "2026-03-03")
        self.assertLessEqual(red_frame, red)
        self.assertLessEqual((red - red_frame).total_seconds(), 60)

        # Green Tuesday recording starts at 09:51, so 09:20 uses Monday coverage.
        green = clock.route_time(ROUTE_GREEN)
        self.assertIsNotNone(green)
        assert green is not None
        self.assertEqual(green.date().isoformat(), "2026-03-16")
        self.assertEqual(green.hour, 9)
        self.assertEqual(green.minute, 20)
        green_frame = clock.replay_frame(ROUTE_GREEN)
        self.assertIsNotNone(green_frame)
        assert green_frame is not None
        self.assertLessEqual((green - green_frame).total_seconds(), 60)

        # Gold never has a snapshot within 60s of 09:20.
        self.assertIsNone(clock.route_time(ROUTE_GOLD))
        self.assertIsNone(clock.replay_frame(ROUTE_GOLD))

    def test_replay_advances_with_wall_offset(self) -> None:
        wall, advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        anchor = clock.set_demo("Tue", "09:20")
        advance(45)
        self.assertEqual(clock.now(), anchor + timedelta(seconds=45))
        self.assertEqual(clock.now() - anchor, timedelta(seconds=45))
        red = clock.route_time(ROUTE_RED)
        assert red is not None
        self.assertEqual(red, anchor + timedelta(seconds=45))

    def test_set_live_returns_wall_and_set_demo_restores_replay(self) -> None:
        wall, advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        clock.set_live()
        self.assertEqual(clock.mode(), "LIVE")
        self.assertEqual(clock.now(), FROZEN)
        advance(10)
        self.assertEqual(clock.now(), FROZEN + timedelta(seconds=10))
        self.assertIsNone(clock.replay_frame(ROUTE_RED))

        anchor = clock.set_demo("Tuesday", "12:00")
        self.assertEqual(clock.mode(), "REPLAY")
        self.assertEqual(anchor.strftime("%a %H:%M"), "Tue 12:00")
        self.assertEqual(clock.now(), anchor)

    def test_gap_time_has_no_service(self) -> None:
        wall, _advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        clock.set_demo("Wed", "04:30")
        self.assertEqual(clock.mode(), "REPLAY")
        self.assertEqual(clock.now().strftime("%H:%M"), "04:30")
        for route_id in (ROUTE_RED, ROUTE_GREEN, ROUTE_GOLD):
            self.assertIsNone(clock.route_time(route_id))
            self.assertIsNone(clock.replay_frame(route_id))

    def test_fresh_frame_rejects_stale_snapshot(self) -> None:
        target = datetime(2026, 3, 3, 9, 20, tzinfo=TZ)
        stamps = (
            datetime(2026, 3, 3, 9, 18, tzinfo=TZ),
            datetime(2026, 3, 3, 9, 19, 30, tzinfo=TZ),
        )
        self.assertEqual(fresh_frame(stamps, target), stamps[1])
        stale = (datetime(2026, 3, 3, 9, 18, tzinfo=TZ),)
        self.assertIsNone(fresh_frame(stale, target))
        self.assertIsNone(fresh_frame((), target))

    def test_wall_clock_is_not_used_when_injected(self) -> None:
        wall, _advance = _frozen_wall()
        clock = DemoClock(wall=wall)
        clock.set_demo("Tue", "09:20")
        first = clock.now()
        # Real wall time moving must not affect a frozen clock.
        self.assertEqual(clock.now(), first)

    def test_datetime_now_only_in_system_wall(self) -> None:
        source = Path(__file__).resolve().parents[1] / "app" / "data" / "clock.py"
        text = source.read_text()
        self.assertEqual(text.count("datetime.now("), 1)
        self.assertIn("def _system_wall", text)
        places = source.with_name("places.py").read_text()
        models = source.parents[1] / "models.py"
        self.assertNotIn("datetime.now", places)
        self.assertNotIn("datetime.now", models.read_text())


if __name__ == "__main__":
    unittest.main()
