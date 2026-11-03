"""Replay arrivals at Tuesday noon, and the live-poll failure flip."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.data import clock
from app.data.clock import ROUTE_GOLD, ROUTE_GREEN, ROUTE_RED, TZ
from app.data.sources import (
    get_arrivals,
    parse_live,
    poll_once,
    record_poll_failure,
    record_poll_success,
    reset_state,
    ride_seconds,
)
from app.models import StopArrival


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
        # Failover anchors replay at the live weekday and minute, not the default noon.
        self.assertEqual(clock.now().strftime("%a %H:%M"), "Tue 15:00")
        self.assertEqual(clock.now().date().isoformat(), "2026-03-03")

        # A new live session needs three fresh failures. The old streak does not carry.
        clock.set_live()
        record_poll_failure()
        record_poll_failure()
        self.assertEqual(clock.mode(), "LIVE")
        record_poll_failure()
        self.assertEqual(clock.mode(), "REPLAY")

    def test_success_and_replay_gap_reset_the_streak(self) -> None:
        clock.set_live()
        record_poll_failure()
        record_poll_failure()
        record_poll_success([])
        record_poll_failure()
        record_poll_failure()
        self.assertEqual(clock.mode(), "LIVE")

        clock.set_demo("Tue", "12:00")
        record_poll_failure()
        record_poll_failure()
        record_poll_failure()
        self.assertEqual(clock.mode(), "REPLAY")
        clock.set_live()
        record_poll_failure()
        record_poll_failure()
        self.assertEqual(clock.mode(), "LIVE")

    def test_poll_once_flips_and_message_path_keeps_the_cache(self) -> None:
        clock.set_live()
        planted = [StopArrival(ROUTE_RED, 268, 99999, 15.0)]
        record_poll_success(planted)
        with patch("app.data.sources.ensure_poller") as poller, patch(
            "app.data.sources._fetch_live", side_effect=OSError("feed down")
        ) as fetch:
            self.assertEqual(get_arrivals(), planted)
            poller.assert_called()
            fetch.assert_not_called()

            poll_once()
            poll_once()
            self.assertEqual(clock.mode(), "LIVE")
            self.assertEqual(get_arrivals()[0].vehicle_id, 99999)
            self.assertEqual(fetch.call_count, 2)

            poll_once()
            self.assertEqual(clock.mode(), "REPLAY")
            self.assertEqual(clock.now().strftime("%a %H:%M"), "Tue 15:00")
            rows = get_arrivals()
            fetch.assert_called()
            self.assertEqual(fetch.call_count, 3)
            self.assertTrue(rows)
            self.assertNotIn(99999, {row.vehicle_id for row in rows})
            self.assertIn(ROUTE_RED, {row.route_id for row in rows})
            self.assertNotIn(ROUTE_GOLD, {row.route_id for row in rows})

        clock.set_live()
        live_rows = [StopArrival(ROUTE_GOLD, 410, 35, 40.0)]
        with patch("app.data.sources.ensure_poller"), patch(
            "app.data.sources._fetch_live", return_value=live_rows
        ) as fetch:
            # The message path still has the last live cache and does not call the feed.
            self.assertEqual(get_arrivals()[0].vehicle_id, 99999)
            fetch.assert_not_called()
            poll_once()
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(get_arrivals(), live_rows)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(clock.mode(), "LIVE")
            clock.set_demo("Tue", "12:00")
            poll_once()
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(clock.mode(), "REPLAY")

    def test_readme_and_fixture_shape(self) -> None:
        path = Path(__file__).resolve().parents[1] / "fixtures" / "feed_arrivals.json"
        payload = json.loads(path.read_text())
        self.assertIsInstance(payload, list)
        self.assertEqual(len(payload), 63)
        self.assertEqual(Counter(entry["RouteID"] for entry in payload), {20: 18, 29: 21, 21: 13, 28: 11})
        for entry in payload:
            self.assertIsInstance(entry["RouteStopID"], int)
            estimates = entry["VehicleEstimates"]
            self.assertIsInstance(estimates, list)
            self.assertTrue(estimates)
            for estimate in estimates:
                self.assertIsInstance(estimate["VehicleID"], int)
                self.assertIsInstance(estimate["SecondsToStop"], int)
                self.assertGreaterEqual(estimate["SecondsToStop"], 0)

        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
        for phrase in (
            "fixtures/feed_arrivals.json",
            "bus.gatech.edu",
            "gatech.transloc.com",
            "GetRouteStopArrivals",
            "63 stop",
            "one ETA",
            "fresh streak",
            "requirements.txt",
            "python3 -m unittest discover -s tests -v",
        ):
            self.assertIn(phrase, readme)

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
