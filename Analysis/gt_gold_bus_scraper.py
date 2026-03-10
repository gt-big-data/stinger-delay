"""
GT Stinger Bus Scraper — polls gatech.transloc.com every 30s indefinitely.

Usage:
  python gt_bus_scraper.py --discover   # show routes/stops/vehicles
  python gt_bus_scraper.py              # start collecting
"""

import csv
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE_URL = "https://gatech.transloc.com/Services/JSONPRelay.svc"
API_KEY = os.environ["TRANSLOC_API_KEY"]
TARGET_ROUTE_IDS = {29}

POLL_INTERVAL = 30
SERVICE_HOURS = (6, 23)

OUTPUT_DIR = Path("bus_data")
CSV_COLUMNS = [
    "snapshot_time", "vehicle_id", "route_id", "route_stop_id",
    "vehicle_lat", "vehicle_lon", "vehicle_speed", "estimated_time_arrival",
]


def api_get(session, endpoint):
    resp = session.get(
        f"{BASE_URL}/{endpoint}",
        params={"apiKey": API_KEY, "isPublicMap": "true"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def poll(session, snapshot_time):
    """Fetch vehicles + ETAs, merge into CSV rows for target routes."""
    vehicles = {
        v["VehicleID"]: v for v in api_get(session, "GetMapVehiclePoints")
        if v.get("RouteID") in TARGET_ROUTE_IDS
    }
    if not vehicles:
        return []

    # Build VehicleID -> [(RouteStopID, SecondsToStop)] index
    vehicle_etas = {}
    try:
        arrivals = api_get(session, "GetRouteStopArrivals")
    except Exception:
        arrivals = []
    for entry in arrivals:
        if entry.get("RouteID") not in TARGET_ROUTE_IDS:
            continue
        rsid = entry.get("RouteStopID", "")
        for est in entry.get("VehicleEstimates", []):
            vid, secs = est.get("VehicleID"), est.get("SecondsToStop")
            if vid is not None and secs is not None:
                vehicle_etas.setdefault(vid, []).append((rsid, secs))

    # Merge: one row per (vehicle, stop) pair
    snapshot_str = snapshot_time.isoformat()
    rows = []
    for vid, v in vehicles.items():
        base = {
            "snapshot_time": snapshot_str,
            "vehicle_id": vid,
            "route_id": v.get("RouteID"),
            "vehicle_lat": v.get("Latitude", ""),
            "vehicle_lon": v.get("Longitude", ""),
            "vehicle_speed": v.get("GroundSpeed", ""),
        }
        etas = vehicle_etas.get(vid, [("", None)])
        for rsid, secs in etas:
            rows.append({
                **base,
                "route_stop_id": rsid,
                "estimated_time_arrival": (
                    (snapshot_time + timedelta(seconds=secs)).isoformat()
                    if secs else ""
                ),
            })
    return rows


def write_rows(rows, csv_path):
    is_new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerows(rows)


def _discover_section(label, fn):
    """Run a discover section, printing errors instead of crashing."""
    time.sleep(1)
    print(f"\n=== {label} ===")
    try:
        fn()
    except Exception as e:
        print(f"  Failed: {e}")


def discover(session):
    """Print routes, active vehicles, and sample ETAs."""
    def routes():
        for r in api_get(session, "GetRoutes"):
            rid = r.get("RouteID", r.get("ID", "?"))
            name = r.get("Description", r.get("LongName", r.get("Name", "?")))
            print(f"  RouteID={rid:<5} {name}")

    def vehicles():
        for v in api_get(session, "GetMapVehiclePoints"):
            print(f"  Vehicle {v.get('Name', '?')} (ID={v.get('VehicleID')}) "
                  f"RouteID={v.get('RouteID')} Speed={v.get('GroundSpeed', 0)}")

    def arrivals():
        for entry in api_get(session, "GetRouteStopArrivals")[:5]:
            ests = ", ".join(
                f"Vehicle {e['VehicleID']} in {e['SecondsToStop']}s"
                for e in entry.get("VehicleEstimates", [])[:3]
            )
            print(f"  RouteID={entry.get('RouteID')} StopID={entry.get('RouteStopID')} "
                  f"ETAs: [{ests}]")

    def stops():
        for s in api_get(session, "GetMapStopPoints")[:10]:
            sid = s.get("RouteStopID", s.get("StopID", s.get("ID", "?")))
            print(f"  StopID={sid:<5} RouteID={s.get('RouteID', '?'):<5} "
                  f"{s.get('Description', s.get('Name', '?'))}")

    _discover_section("Routes", routes)
    _discover_section("Active Vehicles", vehicles)
    _discover_section("Sample Arrivals", arrivals)
    _discover_section("Stops", stops)


def run_scraper(session):
    OUTPUT_DIR.mkdir(exist_ok=True)
    total_polls = total_rows = errors = 0

    print(f"Scraping routes {TARGET_ROUTE_IDS} every {POLL_INTERVAL}s "
          f"({SERVICE_HOURS[0]}:00-{SERVICE_HOURS[1]}:00 weekdays)")

    try:
        while True:
            now = datetime.now()
            if now.weekday() >= 5:
                time.sleep(300)
                continue
            if not (SERVICE_HOURS[0] <= now.hour < SERVICE_HOURS[1]):
                time.sleep(60)
                continue

            try:
                rows = poll(session, now)
                if rows:
                    csv_path = OUTPUT_DIR / f"gt_bus_data_{now:%Y-%m-%d}.csv"
                    write_rows(rows, csv_path)
                    total_rows += len(rows)
                total_polls += 1
                print(f"Poll #{total_polls}: {len(rows)} rows | "
                      f"Total: {total_rows} | Errors: {errors}")
            except Exception as e:
                errors += 1
                print(f"Error: {e}", file=sys.stderr)

            elapsed = (datetime.now() - now).total_seconds()
            time.sleep(max(0, POLL_INTERVAL - elapsed))

    except KeyboardInterrupt:
        print("\nShutting down...")

    print(f"Finished — {total_polls} polls, {total_rows} rows, {errors} errors")


def main():
    parser = argparse.ArgumentParser(description="GT Stinger Bus Scraper")
    parser.add_argument("--discover", action="store_true",
                        help="Show routes, vehicles, stops, then exit")
    args = parser.parse_args()

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))

    if args.discover:
        discover(session)
    else:
        run_scraper(session)


if __name__ == "__main__":
    main()
