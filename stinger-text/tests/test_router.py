"""Five Tuesday-noon trips against the frozen 2026-03-03 12:00 Red frame.

Walk wins Klaus → West Village: the bus already at Klaus cannot be caught,
and the next Red around the loop arrives later than a 14 minute walk.
West Village → Klaus, Kendeda → West Village, and Klaus → North Ave are
direct Red rides. CULC and Clough are the same building, so the plan is walk-only.
"""

from __future__ import annotations

import time
import unittest
from datetime import datetime, timedelta

from app.data import clock
from app.data.clock import TZ
from app.data.places import resolve
from app.data.sources import get_arrivals, reset_state
from app.models import LatLng
from app.routing.router import far_from_campus, plan_trip


def _trip(origin: str, dest: str, deadline=None):
    start = resolve(origin)[0]
    end = resolve(dest)[0]
    return plan_trip(LatLng(start.loc.lat, start.loc.lng), end, deadline)


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        clock.reset(lambda: datetime(2026, 11, 3, 15, 0, tzinfo=TZ))
        reset_state()
        get_arrivals()

    def test_klaus_to_west_village_valid(self) -> None:
        plan = _trip("klaus", "west village")
        self.assertEqual(plan.mode, "REPLAY")
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertEqual(plan.dest.id, "west_village")
        self.assertEqual(plan.best.kind, "walk")
        self.assertIsNone(plan.best.route_id)
        self.assertGreaterEqual(plan.best.arrive_at, plan.now)
        self.assertEqual(plan.walk.kind, "walk")
        red = [option for option in plan.alternatives if option.route_id == 20]
        self.assertEqual(len(red), 1)
        self.assertEqual(red[0].board_stop.route_stop_id, 267)
        self.assertEqual(red[0].alight_stop.route_stop_id, 272)

    def test_west_village_to_klaus(self) -> None:
        plan = _trip("west village", "klaus")
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertEqual(plan.best.kind, "bus")
        self.assertEqual(plan.best.route_id, 20)
        self.assertEqual(plan.best.route_name, "Red")
        self.assertEqual(plan.best.board_stop.route_stop_id, 273)
        self.assertEqual(plan.best.board_stop.name, "West Village")
        self.assertEqual(plan.best.alight_stop.route_stop_id, 277)
        self.assertEqual(plan.best.slip_class, "on_time")
        self.assertEqual(plan.best.slip_buffer_s, 17.0)
        self.assertGreater(plan.best.ride_s, 0)
        self.assertLessEqual(len(plan.alternatives), 2)

        made = _trip("west village", "klaus", plan.now + timedelta(hours=3))
        missed = _trip("west village", "klaus", plan.now - timedelta(hours=1))
        tight = _trip("west village", "klaus", plan.best.arrive_at)
        self.assertEqual(made.verdict, "MAKE_IT")
        self.assertEqual(made.best.board_stop.route_stop_id, 273)
        self.assertEqual(missed.verdict, "WONT_MAKE_IT")
        self.assertEqual(tight.verdict, "TIGHT")

    def test_kendeda_to_west_village(self) -> None:
        plan = _trip("kendeda", "west village")
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertEqual(plan.best.kind, "bus")
        self.assertEqual(plan.best.route_id, 20)
        self.assertEqual(plan.best.board_stop.route_stop_id, 270)
        self.assertEqual(plan.best.alight_stop.route_stop_id, 272)

    def test_klaus_to_north_ave(self) -> None:
        plan = _trip("klaus", "north ave")
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertEqual(plan.best.kind, "bus")
        self.assertEqual(plan.best.route_id, 20)
        self.assertEqual(plan.best.board_stop.route_stop_id, 277)
        self.assertEqual(plan.best.alight_stop.route_stop_id, 250)

    def test_same_building_is_walk_only_and_plan_is_fast(self) -> None:
        plan = _trip("culc", "clough")
        self.assertEqual(plan.best.kind, "walk")
        self.assertIsNone(plan.best.route_id)
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertEqual(plan.alternatives, [])
        self.assertEqual(plan.best.arrive_at, plan.now)

        started = time.perf_counter()
        _trip("west village", "klaus")
        self.assertLess(time.perf_counter() - started, 0.2)

    def test_far_origin_still_returns_a_plan(self) -> None:
        far = LatLng(33.84, -84.40)
        dest = resolve("klaus")[0]
        self.assertTrue(far_from_campus(far))
        plan = plan_trip(far, dest, None)
        self.assertEqual(plan.verdict, "NO_DEADLINE")
        self.assertIsNotNone(plan.best)
        self.assertEqual(plan.mode, "REPLAY")
