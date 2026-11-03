"""Replay arrivals at Tuesday noon, and the live-poll failure flip."""

from __future__ import annotations

import unittest
from datetime import datetime

from app.data import clock
from app.data.clock import ROUTE_GOLD, ROUTE_GREEN, ROUTE_RED, TZ
from app.data.sources import get_arrivals, parse_live, record_poll_failure, reset_state


class SourcesTests(unittest.TestCase):
    def setUp(self) -> None:
        clock.reset(lambda: datetime(2026, 11, 3, 15, 0, tzinfo=TZ))
        reset_state()

    def test_tuesday_noon_replay_frame(self) -> None:
        self.assertEqual(clock.mode(), "REPLAY")
        red_frame = clock.replay_frame(ROUTE_RED)
        self.assertIsNotNone(red_frame)
        assert red_frame is not None
        self.assertEqual(red_frame.date().isoformat(), "2026-03-03")
        self.assertEqual((red_frame.hour, red_frame.minute), (12, 0))
        self.assertIsNotNone(clock.replay_frame(ROUTE_GREEN))
        self.assertIsNone(clock.replay_frame(ROUTE_GOLD))

        rows = get_arrivals()
        routes = {row.route_id for row in rows}
        self.assertIn(ROUTE_RED, routes)
        self.assertNotIn(ROUTE_GOLD, routes)
        self.assertGreater(len(rows), 0)
        self.assertLess(len(rows), 200)
        self.assertTrue(all(row.eta_s >= -30 for row in rows))
        self.assertTrue(all(isinstance(row.vehicle_id, int) for row in rows))

    def test_parse_live_keeps_active_routes_only(self) -> None:
        payload = [
            {
                "RouteID": 20,
                "RouteStopID": 268,
                "VehicleEstimates": [{"VehicleID": 10, "SecondsToStop": 90}],
            },
            {
                "RouteID": 28,
                "RouteStopID": 392,
                "VehicleEstimates": [{"VehicleID": 34, "SecondsToStop": 10}],
            },
            {
                "RouteID": 17,
                "RouteStopID": 196,
                "Estimates": [{"VehicleID": 5, "SecondsToStop": -40}],
            },
        ]
        rows = parse_live(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].route_id, 20)
        self.assertEqual(rows[0].route_stop_id, 268)
        self.assertEqual(rows[0].vehicle_id, 10)
        self.assertEqual(rows[0].eta_s, 90)

    def test_three_live_failures_return_to_replay(self) -> None:
        clock.set_live()
        self.assertEqual(clock.mode(), "LIVE")
        record_poll_failure()
        record_poll_failure()
        self.assertEqual(clock.mode(), "LIVE")
        record_poll_failure()
        self.assertEqual(clock.mode(), "REPLAY")
