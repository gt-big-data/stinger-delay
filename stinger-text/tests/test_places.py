"""Fuzzy place lookup. At least ten alias phrases must resolve."""

from __future__ import annotations

import unittest

from app.data.places import all_places, resolve

# phrase, expected place id
ALIASES = [
    ("klaus", "klaus"),
    ("kab", "klaus"),
    ("klaus building", "klaus"),
    ("culc", "culc"),
    ("the culc", "culc"),
    ("coc", "college_of_computing"),
    ("college of computing", "college_of_computing"),
    ("crc", "crc"),
    ("the gym", "crc"),
    ("stucen", "student_center"),
    ("west village", "west_village"),
    ("wv", "west_village"),
    ("north ave apts", "north_ave_apts"),
    ("tech square", "tech_square"),
    ("price gilbert", "library"),
    ("skiles", "skiles"),
    ("howey physics", "howey"),
    ("van leer", "van_leer"),
    ("vl", "van_leer"),
    ("kendeda", "kendeda"),
    ("brittain", "east_campus"),
    ("ferst center", "ferst_center"),
    ("bobby dodd", "bobby_dodd"),
    ("marta", "midtown_marta"),
    ("tech tower", "tech_tower"),
    ("exhibition hall", "exhibition_hall"),
    ("mrdc", "mrdc"),
    ("coda", "coda"),
    ("mccamish", "mccamish"),
    ("nave", "nave"),
    ("boggs", "boggs"),
    ("ebb", "ebb"),
    ("es&t", "es_and_t"),
    ("tsrb", "tsrb"),
]

REQUIRED = [
    "klaus",
    "culc",
    "college_of_computing",
    "crc",
    "student_center",
    "west_village",
    "north_ave_apts",
    "tech_square",
    "library",
    "skiles",
    "howey",
    "van_leer",
    "clough",
    "kendeda",
    "east_campus",
    "ferst_center",
    "bobby_dodd",
    "midtown_marta",
]


class PlaceTests(unittest.TestCase):
    def test_catalog_has_required_osm_places(self) -> None:
        places = {place.id: place for place in all_places()}
        for place_id in REQUIRED:
            self.assertIn(place_id, places)
            loc = places[place_id].loc
            self.assertGreater(loc.lat, 33.7)
            self.assertLess(loc.lat, 33.8)
            self.assertGreater(loc.lng, -84.42)
            self.assertLess(loc.lng, -84.37)
        self.assertGreaterEqual(len(places), 25)
        self.assertEqual(places["klaus"].loc.lat, 33.7771562)
        self.assertEqual(places["klaus"].loc.lng, -84.3962024)

    def test_at_least_ten_alias_lookups(self) -> None:
        self.assertGreaterEqual(len(ALIASES), 10)
        for phrase, place_id in ALIASES:
            with self.subTest(phrase=phrase):
                matches = resolve(phrase)
                self.assertTrue(matches, f"no match for {phrase!r}")
                self.assertEqual(matches[0].id, place_id)
                self.assertIsNotNone(matches[0].loc)

    def test_fuzzy_typos_rank_best_first(self) -> None:
        klaus = resolve("klaus buidling")
        self.assertTrue(klaus)
        self.assertEqual(klaus[0].id, "klaus")

        centre = resolve("student centre")
        self.assertTrue(centre)
        self.assertEqual(centre[0].id, "student_center")

    def test_shared_clough_commons_alias_returns_both(self) -> None:
        matches = resolve("clough commons")
        ids = [place.id for place in matches]
        self.assertEqual(ids[0], "clough")
        self.assertIn("culc", ids)

    def test_empty_and_unknown_return_nothing(self) -> None:
        self.assertEqual(resolve(""), [])
        self.assertEqual(resolve("   "), [])
        self.assertEqual(resolve("zzzz-not-a-place"), [])


if __name__ == "__main__":
    unittest.main()
