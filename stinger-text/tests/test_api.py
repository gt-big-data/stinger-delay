"""Stop and plan-trip payloads match the Stinger Delay shapes."""

from __future__ import annotations

import unittest
from datetime import datetime

from fastapi import HTTPException

from app.api import OriginIn, PlanIn, plan, stops
from app.data import clock
from app.data.clock import TZ
from app.data.places import resolve
from app.data.sources import reset_state


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        clock.reset(lambda: datetime(2026, 11, 3, 15, 0, tzinfo=TZ))
        reset_state()

    def test_stops_shape(self) -> None:
        rows = stops()
        self.assertGreaterEqual(len(rows), 40)
        sample = rows[0]
        self.assertEqual(
            set(sample),
            {"id", "name", "latitude", "longitude", "sequence", "routeId"},
        )
        self.assertIsInstance(sample["id"], str)
        red = stops(routeId="20")
        self.assertTrue(red)
        self.assertTrue(all(row["routeId"] == "20" for row in red))

    def test_plan_trip_shapes(self) -> None:
        klaus = resolve("klaus")[0]
        walked = plan(PlanIn(
            origin=OriginIn(lat=klaus.loc.lat, lng=klaus.loc.lng),
            destination="west village",
        ))
        self.assertEqual(walked["mode"], "REPLAY")
        self.assertEqual(walked["verdict"], "NO_DEADLINE")
        self.assertEqual(walked["destination"]["id"], "west_village")
        self.assertEqual(walked["best"]["kind"], "walk")
        self.assertEqual(walked["delayPredictions"], [])

        west = resolve("west village")[0]
        ridden = plan(PlanIn(
            origin=OriginIn(lat=west.loc.lat, lng=west.loc.lng),
            destination="klaus",
        ))
        self.assertEqual(ridden["best"]["routeId"], "20")
        self.assertEqual(ridden["best"]["boardStop"]["id"], "273")
        self.assertEqual(ridden["best"]["alightStop"]["name"], "Klaus Building EB")
        prediction = ridden["delayPredictions"][0]
        self.assertEqual(
            set(prediction),
            {"routeId", "stopId", "predictedDelayMinutes", "eta", "confidence"},
        )
        self.assertEqual(prediction["routeId"], "20")
        self.assertEqual(prediction["stopId"], "273")
        self.assertIn("T", prediction["eta"])

    def test_unknown_destination(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            plan(PlanIn(origin=OriginIn(lat=33.77, lng=-84.39), destination="not a place xyz"))
        self.assertEqual(caught.exception.status_code, 404)
