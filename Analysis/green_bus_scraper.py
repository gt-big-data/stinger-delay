import csv
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Green Route = 17
BASE_URL = "https://gatech.transloc.com/Services/JSONPRelay.svc"
API_KEY = "8882812681"
GREEN_ROUTE = {17}

POLL_INTERVAL = 15
# buses run from 6am to 11pm
START_HOUR = 6
END_HOUR = 23

OUTPUT_DIR = Path("green_bus_data")
CSV_COLUMNS = [
    "snapshot_time",
    "vehicle_id",
    "route_id",
    "route_stop_id",
    "vehicle_lat",
    "vehicle_lon",
    "vehicle_speed",
    "estimated_time_arrival",
]


def fetch(session, endpoint):
    resp = session.get(
        f"{BASE_URL}/{endpoint}",
        params={"apiKey": API_KEY, "isPublicMap": "true"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_rows(session, snapshot_time):
    # get all active green route buses
    active_buses = {
        v["VehicleID"]: v
        for v in fetch(session, "GetMapVehiclePoints")
        if v.get("RouteID") in GREEN_ROUTE
    }

    if not active_buses:
        return []

    # get ETAs for each bus at each stop
    eta_lookup = {}
    try:
        stop_arrivals = fetch(session, "GetRouteStopArrivals")
    except Exception:
        stop_arrivals = []

    for stop in stop_arrivals:
        if stop.get("RouteID") not in GREEN_ROUTE:
            continue
        stop_id = stop.get("RouteStopID", "")
        for estimate in stop.get("VehicleEstimates", []):
            vid = estimate.get("VehicleID")
            secs = estimate.get("SecondsToStop")
            if vid is not None and secs is not None:
                eta_lookup.setdefault(vid, []).append((stop_id, secs))

    # build one row per bus per stop
    snapshot_str = snapshot_time.isoformat()
    rows = []
    for vid, bus in active_buses.items():
        base_info = {
            "snapshot_time": snapshot_str,
            "vehicle_id": vid,
            "route_id": bus.get("RouteID"),
            "vehicle_lat": bus.get("Latitude", ""),
            "vehicle_lon": bus.get("Longitude", ""),
            "vehicle_speed": bus.get("GroundSpeed", ""),
        }
        stops_for_bus = eta_lookup.get(vid, [("", None)])
        for stop_id, secs in stops_for_bus:
            rows.append({
                **base_info,
                "route_stop_id": stop_id,
                "estimated_time_arrival": (
                    (snapshot_time + timedelta(seconds=secs)).isoformat()
                    if secs else ""
                ),
            })
    return rows


def save_to_csv(rows, csv_path):
    # write header only if file is new
    file_is_new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if file_is_new:
            writer.writeheader()
        writer.writerows(rows)


def discover_routes(session):
    # helper to explore whats available in the API
    time.sleep(1)
    print("\n=== Routes ===")
    try:
        for r in fetch(session, "GetRoutes"):
            rid = r.get("RouteID", "?")
            name = r.get("Description") or r.get("LongName") or r.get("Name", "?")
            print(f"  ID: {rid:<5} Name: {name}")
    except Exception as e:
        print(f"  Failed: {e}")

    time.sleep(1)
    print("\n=== Active Vehicles ===")
    try:
        for v in fetch(session, "GetMapVehiclePoints"):
            print(f"  VehicleID={v.get('VehicleID')} RouteID={v.get('RouteID')} Speed={v.get('GroundSpeed', 0)}")
    except Exception as e:
        print(f"  Failed: {e}")

    time.sleep(1)
    print("\n=== Sample ETAs ===")
    try:
        for entry in fetch(session, "GetRouteStopArrivals")[:5]:
            ests = ", ".join(
                f"Vehicle {e['VehicleID']} in {e['SecondsToStop']}s"
                for e in entry.get("VehicleEstimates", [])[:3]
            )
            print(f"  RouteID={entry.get('RouteID')} StopID={entry.get('RouteStopID')} ETAs: [{ests}]")
    except Exception as e:
        print(f"  Failed: {e}")


def run(session):
    OUTPUT_DIR.mkdir(exist_ok=True)
    poll_count = total_rows = error_count = 0

    print(f"Starting Green Route scraper — polling every {POLL_INTERVAL}s on weekdays {START_HOUR}:00-{END_HOUR}:00")

    try:
        while True:
            now = datetime.now()

            # skip weekends
            if now.weekday() >= 5:
                time.sleep(300)
                continue

            # skip outside service hours
            if not (START_HOUR <= now.hour < END_HOUR):
                time.sleep(60)
                continue

            try:
                rows = get_rows(session, now)
                if rows:
                    csv_path = OUTPUT_DIR / f"green_bus_{now:%Y-%m-%d}.csv"
                    save_to_csv(rows, csv_path)
                    total_rows += len(rows)
                poll_count += 1
                print(f"Poll #{poll_count}: {len(rows)} rows | Total: {total_rows} | Errors: {error_count}")
            except Exception as e:
                error_count += 1
                print(f"Error on poll #{poll_count}: {e}", file=sys.stderr)

            elapsed = (datetime.now() - now).total_seconds()
            time.sleep(max(0, POLL_INTERVAL - elapsed))

    except KeyboardInterrupt:
        print("\nStopped.")

    print(f"Done — {poll_count} polls, {total_rows} rows saved, {error_count} errors")


def main():
    parser = argparse.ArgumentParser(description="Green Route Bus Scraper")
    parser.add_argument("--discover", action="store_true", help="Print routes and vehicles then exit")
    args = parser.parse_args()

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))

    if args.discover:
        discover_routes(session)
    else:
        run(session)


if __name__ == "__main__":
    main()