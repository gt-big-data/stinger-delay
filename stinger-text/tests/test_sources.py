"""Replay arrivals at Tuesday noon, and the live-poll failure flip."""

from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path

from app.data import clock
from app.data.clock import ROUTE_GOLD, ROUTE_GREEN, ROUTE_RED, TZ
from app.data.sources import get_arrivals, parse_live, record_poll_failure, reset_state, ride_seconds


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

    def test_fixture_feed_drops_clough_and_blue(self) -> None:
        path = Path(__file__).resolve().parents[1] / "fixtures" / "feed_arrivals.json"
        payload = json.loads(path.read_text())
        rows = parse_live(payload)
        routes = {row.route_id for row in rows}
        self.assertIn(ROUTE_RED, routes)
        self.assertIn(ROUTE_GOLD, routes)
        self.assertNotIn(ROUTE_GREEN, routes)
        self.assertNotIn(21, routes)
        self.assertNotIn(28, routes)
        self.assertTrue(all(row.eta_s >= -30 for row in rows))
        self.assertGreater(len(rows), 10)

    def test_green_gold_ride_is_eta_difference(self) -> None:
        self.assertIsNone(ride_seconds(ROUTE_RED, 30.0, 90.0))
        self.assertIsNone(ride_seconds(ROUTE_GREEN, 100.0, 40.0))
        self.assertIsNone(ride_seconds(ROUTE_GREEN, None, 40.0))
        self.assertIsNone(ride_seconds(ROUTE_GOLD, 10.0, None))
        self.assertEqual(ride_seconds(ROUTE_GREEN, 120.0, 180.0), 60.0)
        self.assertEqual(ride_seconds(ROUTE_GOLD, 10.0, 40.0), 30.0)
