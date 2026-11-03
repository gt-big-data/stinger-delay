"""Five Tuesday-noon trips against the frozen 2026-03-03 12:00 Red frame.

Walk wins Klaus → West Village: the bus already at Klaus cannot be caught,
and the next Red around the loop arrives later than a 14 minute walk.
West Village → Klaus, Kendeda → West Village, and Klaus → North Ave are
direct Red rides. CULC and Clough are the same building, so the plan is walk-only.
"""

from __future__ import annotations

import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.data import clock
from app.data.clock import TZ
from app.data.places import resolve
from app.data.sources import get_arrivals, reset_state
from app.models import LatLng, Place, StopArrival
from app.routing.params import TIGHT_WINDOW_S
from app.routing.router import (
    FAR_NOTE,
    NO_BUS_NOTE,
    SHORT_TRIP_NOTE,
    _forward_s,
    far_from_campus,
    plan_trip,
    stops_by_route,
)


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
        self.assertTrue(all(option.route_id != 29 for option in plan.alternatives))
        self.assertEqual(plan.notes, [])

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
        self.assertEqual(plan.notes, [SHORT_TRIP_NOTE])

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
        self.assertIn(FAR_NOTE, plan.notes)
        self.assertIn(NO_BUS_NOTE, plan.notes)

    def test_no_arrivals_is_walk_only(self) -> None:
        with patch("app.routing.router.get_arrivals", return_value=[]):
            plan = _trip("klaus", "west village")
        self.assertEqual(plan.best.kind, "walk")
        self.assertEqual(plan.alternatives, [])
        self.assertEqual(plan.notes, [NO_BUS_NOTE])

    def test_green_ride_uses_stop_etas_not_segments(self) -> None:
        catalog = stops_by_route()[17]
        by_id = {stop.route_stop_id: stop for stop in catalog}
        board = by_id[196]
        alight = by_id[418]
        dest = Place(id="green-alight", name="Green alight", loc=alight.loc)
        arrivals = [
            StopArrival(route_id=17, route_stop_id=196, vehicle_id=5, eta_s=120.0),
            StopArrival(route_id=17, route_stop_id=418, vehicle_id=5, eta_s=180.0),
        ]
        with patch("app.routing.router.get_arrivals", return_value=arrivals):
            plan = plan_trip(board.loc, dest, None)
        self.assertEqual(plan.best.kind, "bus")
        self.assertEqual(plan.best.route_id, 17)
        self.assertEqual(plan.best.board_stop.route_stop_id, 196)
        self.assertEqual(plan.best.alight_stop.route_stop_id, 418)
        self.assertEqual(plan.best.ride_s, 60.0)
        self.assertGreater(_forward_s(catalog, 17, 196, 418), 200.0)

        board_only = [StopArrival(route_id=17, route_stop_id=196, vehicle_id=5, eta_s=120.0)]
        with patch("app.routing.router.get_arrivals", return_value=board_only):
            walked = plan_trip(board.loc, dest, None)
        self.assertEqual(walked.best.kind, "walk")
        self.assertEqual(walked.notes, [NO_BUS_NOTE])

    def test_fixed_pairs_carry_deadlines_and_slip(self) -> None:
        """Verdict follows best arrival plus that option's slip, on every fixed pair."""
        pairs = [
            ("klaus", "west village", "walk", None, None, None, [], (267, 272)),
            ("west village", "klaus", "bus", 20, 273, 277, [], None),
            ("kendeda", "west village", "bus", 20, 270, 272, [], None),
            ("klaus", "north ave", "bus", 20, 277, 250, [], None),
            ("culc", "clough", "walk", None, None, None, [SHORT_TRIP_NOTE], None),
            ("howey", "bobby dodd", "walk", None, None, None, [], (275, 279)),
            ("skiles", "kendeda", "walk", None, None, None, [], (267, 270)),
            ("student center", "marta", "walk", None, None, None, [NO_BUS_NOTE], None),
        ]
        window = timedelta(seconds=TIGHT_WINDOW_S)
        for origin, dest, kind, route_id, board_id, alight_id, notes, alt in pairs:
            plan = _trip(origin, dest)
            self.assertEqual(plan.mode, "REPLAY", origin)
            self.assertEqual(plan.verdict, "NO_DEADLINE", origin)
            self.assertEqual(plan.best.kind, kind, origin)
            self.assertEqual(plan.best.route_id, route_id, origin)
            self.assertEqual(plan.notes, notes, origin)
            if board_id is None:
                self.assertIsNone(plan.best.board_stop, origin)
                self.assertIsNone(plan.best.alight_stop, origin)
            else:
                self.assertEqual(plan.best.board_stop.route_stop_id, board_id, origin)
                self.assertEqual(plan.best.alight_stop.route_stop_id, alight_id, origin)
                self.assertEqual(plan.best.slip_buffer_s, 17.0, origin)
                self.assertEqual(plan.best.slip_class, "on_time", origin)
            if alt is None:
                self.assertEqual(plan.alternatives, [], origin)
            else:
                self.assertEqual(plan.alternatives[0].route_id, 20, origin)
                self.assertEqual(plan.alternatives[0].board_stop.route_stop_id, alt[0], origin)
                self.assertEqual(plan.alternatives[0].alight_stop.route_stop_id, alt[1], origin)

            buffered = plan.best.arrive_at + timedelta(seconds=plan.best.slip_buffer_s)
            deadlines = [
                (buffered + window, "MAKE_IT"),
                (buffered + window - timedelta(seconds=1), "TIGHT"),
                (buffered, "TIGHT"),
                (buffered - window, "TIGHT"),
                (buffered - window - timedelta(seconds=1), "WONT_MAKE_IT"),
                ((buffered + window).replace(tzinfo=None), "MAKE_IT"),
                ((buffered + window).astimezone(timezone.utc), "MAKE_IT"),
            ]
            # Slip changes the verdict and leaves arrive_at alone.
            if plan.best.slip_buffer_s > 0:
                deadlines.append((plan.best.arrive_at + window, "TIGHT"))
            else:
                deadlines.append((plan.best.arrive_at + window, "MAKE_IT"))
            for deadline, verdict in deadlines:
                got = _trip(origin, dest, deadline)
                self.assertEqual(got.verdict, verdict, (origin, dest, verdict))
                self.assertEqual(got.best.kind, kind)
                self.assertEqual(got.best.route_id, route_id)
                self.assertEqual(got.best.arrive_at, plan.best.arrive_at)

    def test_green_and_gold_need_both_etas_on_one_vehicle(self) -> None:
        routes = (
            (17, 196, 418, 212),
            (29, 410, 396, 421),
        )
        for route_id, board_id, alight_id, other_id in routes:
            catalog = stops_by_route()[route_id]
            by_id = {stop.route_stop_id: stop for stop in catalog}
            board = by_id[board_id]
            alight = by_id[alight_id]
            dest = Place(id=f"stop-{alight_id}", name="Alight", loc=alight.loc)
            segment = _forward_s(catalog, route_id, board_id, alight_id)
            self.assertGreater(segment, 110.0)

            def planned(arrivals, dest=dest, board=board):
                with patch("app.routing.router.get_arrivals", return_value=arrivals):
                    return plan_trip(board.loc, dest, None)

            both = planned([
                StopArrival(route_id, board_id, 5, 120.0),
                StopArrival(route_id, alight_id, 5, 200.0),
            ])
            self.assertEqual(both.best.kind, "bus", route_id)
            self.assertEqual(both.best.route_id, route_id)
            self.assertEqual(both.best.board_stop.route_stop_id, board_id)
            self.assertEqual(both.best.alight_stop.route_stop_id, alight_id)
            self.assertEqual(both.best.ride_s, 80.0)
            self.assertNotEqual(both.best.ride_s, segment)
            self.assertEqual(both.notes, [])

            for arrivals in (
                [StopArrival(route_id, board_id, 5, 120.0)],
                [StopArrival(route_id, alight_id, 5, 200.0)],
                [
                    StopArrival(route_id, board_id, 5, 120.0),
                    StopArrival(route_id, alight_id, 5, 120.0),
                ],
                [
                    StopArrival(route_id, board_id, 5, 200.0),
                    StopArrival(route_id, alight_id, 5, 80.0),
                ],
                [
                    StopArrival(route_id, board_id, 1, 100.0),
                    StopArrival(route_id, alight_id, 2, 160.0),
                ],
                [
                    StopArrival(route_id, board_id, 5, 100.0),
                    StopArrival(route_id, other_id, 5, 400.0),
                ],
                [
                    StopArrival(route_id, board_id, 5, 44.0),
                    StopArrival(route_id, alight_id, 5, 90.0),
                ],
            ):
                walked = planned(arrivals)
                self.assertEqual(walked.best.kind, "walk", (route_id, arrivals))
                self.assertEqual(walked.notes, [NO_BUS_NOTE], (route_id, arrivals))
                self.assertEqual(walked.alternatives, [], (route_id, arrivals))

            mixed = planned([
                StopArrival(route_id, board_id, 1, 80.0),
                StopArrival(route_id, board_id, 2, 200.0),
                StopArrival(route_id, alight_id, 2, 260.0),
            ])
            self.assertEqual(mixed.best.kind, "bus", route_id)
            self.assertEqual(mixed.best.ride_s, 60.0, route_id)
            self.assertEqual(mixed.best.board_stop.route_stop_id, board_id)
            self.assertEqual(mixed.best.alight_stop.route_stop_id, alight_id)
            self.assertNotEqual(mixed.best.ride_s, segment)

            caught = planned([
                StopArrival(route_id, board_id, 5, 45.0),
                StopArrival(route_id, alight_id, 5, 90.0),
            ])
            self.assertEqual(caught.best.kind, "bus", route_id)
            self.assertEqual(caught.best.ride_s, 45.0, route_id)
