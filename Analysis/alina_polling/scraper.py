"""
GT Bus Data Scraper
Polls vehicle positions and stop arrival times and appends to a CSV.

Usage:
    python scraper.py --route 30 --name "Night Gold/Clough" --interval 15
    python scraper.py --route 23 --name "Gold"
    python scraper.py --route 24 --name "Blue" --interval 30 --output my_data.csv

Arguments:
    --route     Route ID number to scrape (required)
    --name      Human-readable route name, used in logs and default filename (required)
    --interval  Polling interval in seconds (default: 15)
    --output    Output CSV filename (default: route_<id>_data.csv)

Known GT Route IDs (check bus.gatech.edu to confirm current IDs):
    23 = Gold
    24 = Blue  
    29 = Red
    30 = Night Gold/Clough
    31 = Green
"""

import argparse
import requests
import csv
import time
import os
from datetime import datetime, timezone

API_KEY     = "8882812681"
VEHICLE_URL = f"https://bus.gatech.edu/Services/JSONPRelay.svc/GetMapVehiclePoints?apiKey={API_KEY}&isPublicMap=true"
ARRIVAL_BASE = f"https://bus.gatech.edu/Services/JSONPRelay.svc/GetStopArrivalTimes?apiKey={API_KEY}&routeIds={{route_id}}&version=2"

FIELDNAMES = [
    "snapshot_time",
    "vehicle_id",
    "route_id",
    "route_stop_id",
    "vehicle_lat",
    "vehicle_lon",
    "vehicle_speed",
    "estimated_time_arrival",
]


def fetch_vehicles(route_id):
    """Return list of vehicle dicts filtered to the given route."""
    resp = requests.get(VEHICLE_URL, timeout=10)
    resp.raise_for_status()
    return [v for v in resp.json() if v.get("RouteID") == route_id]


def fetch_arrivals(route_id):
    """Return dict mapping VehicleID -> list of stop arrival entries."""
    url = ARRIVAL_BASE.format(route_id=route_id)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    vehicle_stops = {}
    for stop in resp.json():
        stop_id  = stop.get("StopId") or stop.get("RouteStopID") or stop.get("StopID")
        arrivals = stop.get("RouteStopArrivals") or stop.get("Arrivals") or []
        for arrival in arrivals:
            vid = arrival.get("VehicleId") or arrival.get("VehicleID")
            eta = arrival.get("SecondsToArrival") or arrival.get("ArrivalTime") or arrival.get("ETA")
            if vid is not None:
                vehicle_stops.setdefault(vid, []).append({
                    "route_stop_id":          stop_id,
                    "estimated_time_arrival": eta,
                })
    return vehicle_stops


def write_header_if_needed(path):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
        print(f"Created {path} with header.")


def append_rows(rows, path):
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerows(rows)


def poll(route_id, output_csv):
    snapshot_time = datetime.now(timezone.utc).isoformat()

    try:
        vehicles = fetch_vehicles(route_id)
    except Exception as e:
        print(f"[{snapshot_time}] ERROR fetching vehicles: {e}")
        return 0

    try:
        arrivals = fetch_arrivals(route_id)
    except Exception as e:
        print(f"[{snapshot_time}] ERROR fetching arrivals: {e}")
        arrivals = {}

    rows = []
    for v in vehicles:
        vid          = v.get("VehicleID")
        stop_entries = arrivals.get(vid) or [{}]
        for entry in stop_entries:
            rows.append({
                "snapshot_time":          snapshot_time,
                "vehicle_id":             vid,
                "route_id":               v.get("RouteID"),
                "route_stop_id":          entry.get("route_stop_id"),
                "vehicle_lat":            v.get("Latitude"),
                "vehicle_lon":            v.get("Longitude"),
                "vehicle_speed":          v.get("GroundSpeed"),
                "estimated_time_arrival": entry.get("estimated_time_arrival"),
            })

    if rows:
        append_rows(rows, output_csv)
    print(f"[{snapshot_time}] {len(vehicles)} vehicles | {len(rows)} rows saved")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="GT Bus Data Scraper")
    parser.add_argument("--route",    type=int,   required=True,  help="Route ID (e.g. 30)")
    parser.add_argument("--name",     type=str,   required=True,  help="Route name (e.g. 'Night Gold/Clough')")
    parser.add_argument("--interval", type=int,   default=15,     help="Poll interval in seconds (default: 15)")
    parser.add_argument("--output",   type=str,   default=None,   help="Output CSV filename")
    args = parser.parse_args()

    output_csv = args.output or f"route_{args.route}_data.csv"

    write_header_if_needed(output_csv)
    print(f"Scraping Route {args.route} ({args.name})")
    print(f"Polling every {args.interval}s → saving to '{output_csv}'")
    print("Press Ctrl+C to stop.\n")

    total_rows = 0
    try:
        while True:
            total_rows += poll(args.route, output_csv)
            print(f"  Total rows so far: {total_rows}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopped. Total rows collected: {total_rows}")
        print(f"Data saved to: {output_csv}")


if __name__ == "__main__":
    main()
