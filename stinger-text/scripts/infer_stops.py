#!/usr/bin/env python3
"""Infer Stinger stop locations from recorded vehicle CSVs.

Location for each stop is the median vehicle lat/lng on snapshots where
speed < 2 and the ETA to that stop is between 5 and 20 seconds.

Names and loop order prefer the live GetStops / GetRoutesForMapWithSchedule
feeds (GetMapStopPoints times out). If the feed is down, a catalog captured
from that feed is used so the script still writes every Red, Green, and Gold
stop. Published coordinates are only a fallback when a stop has no qualifying
vehicle sample.

Routes: Red=20, Green=17, Gold=29. Clough is excluded.

Outputs stinger-text/app/data/stops.json:
  route_stop_id, route_id, name, lat, lng, seq
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STINGER_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STINGER_ROOT.parent
DEFAULT_OUT = STINGER_ROOT / "app" / "data" / "stops.json"

API_KEY = "8882812681"
FEED_HOST = "bus.gatech.edu"
ROUTES = (20, 17, 29)  # Red, Green, Gold — Red first
SPEED_MAX = 2.0
ETA_MIN_S = 5.0
ETA_MAX_S = 20.0
FEED_TIMEOUT_S = 12

# Loop order and names captured from GetRoutesForMapWithSchedule + GetStops.
# (route_stop_id, name, published_lat, published_lng)
FALLBACK_CATALOG: dict[int, list[tuple[int, str, float, float]]] = {
    20: [
        (250, "North Avenue Apts - To West Campus", 33.769921, -84.391754),
        (264, "Brown Residence Hall", 33.771857, -84.391920),
        (265, "Techwood Dr & Field Residence Hall", 33.774060, -84.391920),
        (266, "Techwood & 5th  - North", 33.776757, -84.392060),
        (267, "Russ Chandler Stadium", 33.776990, -84.394050),
        (268, "Klaus Building WB", 33.777485, -84.395576),
        (269, "Nanotechnology", 33.778320, -84.398084),
        (270, "Kendeda Building", 33.778360, -84.399560),
        (274, "Center St. Apartments & Hemphill Ave", 33.779710, -84.402416),
        (272, "Paper Tricentennial", 33.780598, -84.404657),
        (273, "West Village", 33.779616, -84.404709),
        (271, "8th St & Hemphill Ave", 33.779631, -84.402740),
        (275, "Ferst Dr & Hemphill Ave", 33.778450, -84.400824),
        (276, "Cherry Emerson", 33.778179, -84.397328),
        (277, "Klaus Building EB", 33.777097, -84.395484),
        (278, "Techwood Dr & 5th St - South", 33.776464, -84.392099),
        (279, "Techwood Dr & Bobby Dodd Way", 33.774356, -84.391996),
        (280, "COP & North Ave.", 33.770665, -84.392185),
    ],
    17: [
        (195, "Baker Building", 33.780346, -84.399230),
        (196, "Kendeda Building", 33.778360, -84.399560),
        (208, "Center St. Apartments & Hemphill Ave", 33.779710, -84.402416),
        (418, "Georgia Tech Police Department", 33.781098, -84.403725),
        (206, "Hemphill Ave & Curran St", 33.784654, -84.405967),
        (209, "GT Competition Center (575 14th Street)", 33.786368, -84.405321),
        (210, "14th St & State St", 33.786130, -84.398800),
        (211, "GTRI Conference Center", 33.786282, -84.395591),
        (212, "McCamish & 10th St.", 33.781612, -84.392611),
        (213, "Graduate Living Center", 33.781533, -84.396217),
    ],
    29: [
        (419, "Weber Loop", 33.773150, -84.397012),
        (420, "Student Center", 33.773428, -84.399173),
        (407, "Exhibition Hall", 33.774923, -84.402537),
        (408, "Ferst Dr & Hemphill Ave", 33.778450, -84.400824),
        (409, "Cherry Emerson", 33.778179, -84.397328),
        (410, "Klaus Building EB", 33.777097, -84.395484),
        (399, "5th Street Bridge EB", 33.776831, -84.392021),
        (400, "Technology Square EB", 33.776800, -84.389750),
        (401, "College of Business", 33.776770, -84.387753),
        (402, "Academy of Medicine", 33.778536, -84.387240),
        (396, "MARTA Midtown Station", 33.780822, -84.386406),
        (404, "Publix at the Plaza", 33.780670, -84.388671),
        (397, "Technology Square WB", 33.776920, -84.389780),
        (398, "5th Street Bridge WB", 33.776943, -84.391707),
        (411, "Russ Chandler Stadium", 33.776990, -84.394050),
        (412, "Klaus Building WB", 33.777485, -84.395576),
        (413, "Nanotechnology", 33.778320, -84.398084),
        (415, "Kendeda Building", 33.778360, -84.399560),
        (416, "Couch Park", 33.777962, -84.402015),
        (417, "CRC & Stamps Health", 33.775100, -84.402650),
        (421, "Ferst Drive & Student Center", 33.773404, -84.399583),
    ],
}

CSV_SOURCES = {
    20: [REPO_ROOT / "Platform" / "red_line" / "data" / "red_line_data.csv"],
    17: sorted((REPO_ROOT / "Analysis" / "green_bus_data").glob("*.csv")),
    29: sorted((REPO_ROOT / "Analysis" / "bus_data").glob("gt_gold_bus_data_*.csv")),
}


def _num(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def eta_seconds(row: dict[str, str]) -> float | None:
    """Seconds until the row's stop.

    Red stores a raw second count in eta_seconds (and copies it into
    estimated_time_arrival). Green and Gold store a naive local ISO timestamp
    in estimated_time_arrival, so ETA is that timestamp minus snapshot_time.
    """
    raw_eta = (row.get("estimated_time_arrival") or "").strip()
    eta_dt = _parse_dt(raw_eta)
    if eta_dt is not None and (eta_dt.year > 2000 or "T" in raw_eta):
        snap = _parse_dt(row.get("snapshot_time") or row.get("snapshot_time_utc"))
        if snap is None:
            return None
        return (eta_dt - snap).total_seconds()
    seconds = _num(row.get("eta_seconds"))
    if seconds is None:
        seconds = _num(raw_eta)
    return seconds


def _clean_name(name: str) -> str:
    return " ".join(name.replace("\u00a0", " ").split())


def fetch_live_catalog() -> dict[int, list[tuple[int, str, float, float]]] | None:
    """Names, published coords, and loop order from the public map feed."""
    base = f"https://{FEED_HOST}/Services/JSONPRelay.svc"
    params = f"apiKey={API_KEY}&isPublicMap=true"
    try:
        with urllib.request.urlopen(f"{base}/GetStops?{params}", timeout=FEED_TIMEOUT_S) as resp:
            stops = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(
            f"{base}/GetRoutesForMapWithSchedule?{params}", timeout=FEED_TIMEOUT_S
        ) as resp:
            routes = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, timeout, bad JSON — fall back
        print(f"live feed unavailable ({exc}); using captured catalog", file=sys.stderr)
        return None

    names: dict[tuple[int, int], tuple[str, float, float]] = {}
    for stop in stops:
        try:
            rid = int(stop["RouteID"])
            sid = int(stop["RouteStopID"])
        except (KeyError, TypeError, ValueError):
            continue
        if rid not in ROUTES:
            continue
        names[(rid, sid)] = (
            _clean_name(str(stop.get("Description") or f"Stop {sid}")),
            float(stop["Latitude"]),
            float(stop["Longitude"]),
        )

    catalog: dict[int, list[tuple[int, str, float, float]]] = {rid: [] for rid in ROUTES}
    for route in routes:
        try:
            rid = int(route["RouteID"])
        except (KeyError, TypeError, ValueError):
            continue
        if rid not in ROUTES:
            continue
        ordered = sorted(route.get("Stops") or [], key=lambda s: s.get("Order") or 0)
        for stop in ordered:
            try:
                sid = int(stop["RouteStopID"])
            except (KeyError, TypeError, ValueError):
                continue
            name, lat, lng = names.get((rid, sid), (None, None, None))
            if name is None:
                name = _clean_name(str(stop.get("Description") or f"Stop {sid}"))
                lat = float(stop["Latitude"])
                lng = float(stop["Longitude"])
            catalog[rid].append((sid, name, lat, lng))
    if any(catalog.values()):
        return catalog
    return None


def infer_positions(route_id: int) -> dict[int, tuple[float, float, int]]:
    """Median lat/lng where speed < 2 and ETA is in [5, 20] seconds."""
    points: dict[int, list[tuple[float, float]]] = defaultdict(list)
    seen: set[tuple[str, ...]] = set()
    files = CSV_SOURCES[route_id]
    if not files:
        raise FileNotFoundError(f"no CSVs for route {route_id}")
    for path in files:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = tuple(row.get(col, "") for col in row)
                if key in seen:
                    continue
                seen.add(key)
                sid_raw = (row.get("route_stop_id") or "").strip()
                if not sid_raw:
                    continue
                try:
                    sid = int(float(sid_raw))
                except ValueError:
                    continue
                speed = _num(row.get("vehicle_speed"))
                lat = _num(row.get("vehicle_lat"))
                lng = _num(row.get("vehicle_lon"))
                eta = eta_seconds(row)
                if None in (speed, lat, lng, eta):
                    continue
                if speed < SPEED_MAX and ETA_MIN_S <= eta <= ETA_MAX_S:
                    points[sid].append((lat, lng))

    medians: dict[int, tuple[float, float, int]] = {}
    for sid, samples in points.items():
        medians[sid] = (
            statistics.median(p[0] for p in samples),
            statistics.median(p[1] for p in samples),
            len(samples),
        )
    return medians


def build_stops(catalog: dict[int, list[tuple[int, str, float, float]]]) -> list[dict]:
    records: list[dict] = []
    for route_id in ROUTES:
        positions = infer_positions(route_id)
        loop = catalog.get(route_id) or FALLBACK_CATALOG[route_id]
        seen_ids: set[int] = set()
        for seq, (sid, name, pub_lat, pub_lng) in enumerate(loop, start=1):
            seen_ids.add(sid)
            if sid in positions:
                lat, lng, _n = positions[sid]
            else:
                lat, lng = pub_lat, pub_lng
            records.append(
                {
                    "route_stop_id": sid,
                    "route_id": route_id,
                    "name": _clean_name(name),
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "seq": seq,
                }
            )
        # Stops observed in the CSV but missing from the feed catalog.
        extras = sorted(sid for sid in positions if sid not in seen_ids)
        for sid in extras:
            lat, lng, _n = positions[sid]
            records.append(
                {
                    "route_stop_id": sid,
                    "route_id": route_id,
                    "name": f"Stop {sid}",
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "seq": len(seen_ids) + 1,
                }
            )
            seen_ids.add(sid)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="skip the feed and use the captured stop catalog",
    )
    args = parser.parse_args()

    catalog = None if args.no_live else fetch_live_catalog()
    if catalog is None:
        catalog = FALLBACK_CATALOG
        print("using captured GetStops catalog", file=sys.stderr)
    else:
        print("using live GetStops names and loop order", file=sys.stderr)

    stops = build_stops(catalog)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(stops, indent=2) + "\n", encoding="utf-8")
    counts: dict[int, int] = defaultdict(int)
    for stop in stops:
        counts[stop["route_id"]] += 1
    print(f"wrote {len(stops)} stops to {args.out} ({dict(counts)})")


if __name__ == "__main__":
    main()
