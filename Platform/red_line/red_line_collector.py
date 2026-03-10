#!/usr/bin/env python3
"""
Red Line Bus Data Collector
============================
Continuously polls the GT Bus API for Red Line (routeID=20) vehicle positions
and next-stop ETAs, writing one row per vehicle per tick to a CSV.

Risk mitigations implemented
-----------------------------
R1  Empty ETA response: guarded before indexing response[0]
R2  Missing routeID filter: routeID=20 sent as query param
R3  No request timeout: every request uses timeout=REQUEST_TIMEOUT
R4  ETA string comparison: raw Seconds integer stored, no HH:MM:SS compare
R5  No retry/backoff: _get_with_retry() — 3 attempts, 1 / 2 / 4 s delays
R7  Rate limiting: ETA_CALL_DELAY between per-vehicle calls; 429 handled
R8  CSV write corruption: single writerows() + immediate flush per tick
R9  Inactive hours: "0 vehicles" logged as normal heartbeat, not an error
R10 SSL bypass: requests verifies SSL by default — no override here
"""

import csv
import logging
import os
import re
import time
from datetime import datetime
from typing import Optional, Tuple

import pytz
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY         = "8882812681"
BASE_URL        = "https://bus.gatech.edu"
ROUTE_ID        = 20          # Red line

POLL_INTERVAL   = 15          # seconds between ticks
REQUEST_TIMEOUT = 10          # seconds before aborting a single request
MAX_RETRIES     = 3           # attempts per API call
RETRY_DELAYS    = [1, 2, 4]  # exponential backoff delays (seconds)
ETA_CALL_DELAY  = 0.2         # seconds to sleep between per-vehicle ETA calls

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
CSV_PATH   = os.path.join(DATA_DIR, "red_line_data.csv")
LOG_PATH   = os.path.join(DATA_DIR, "red_line_collector.log")

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
EASTERN = pytz.timezone("America/New_York")

CSV_FIELDNAMES = [
    "snapshot_time_utc",
    "vehicle_id",
    "route_id",
    "route_stop_id",
    "vehicle_lat",
    "vehicle_lon",
    "vehicle_speed",
    "eta_seconds",
    "estimated_time_arrival",
    "eta_time_local",
    "poll_interval_seconds",
    "source_method",
]

# ── HTTP helper ───────────────────────────────────────────────────────────────

def _get_with_retry(
    session: requests.Session,
    url: str,
    params: dict,
) -> Optional[list]:
    """
    GET url with params; retry up to MAX_RETRIES times using exponential
    backoff. Handles HTTP 429 (rate-limit) by doubling the back-off.
    Returns parsed JSON list, or None if all attempts fail.
    """
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)

            # R7: handle rate-limit explicitly
            if resp.status_code == 429:
                wait = delay * 2
                log.warning(
                    "Rate limited (429) attempt %d/%d on %s — sleeping %ds",
                    attempt, MAX_RETRIES, url, wait,
                )
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            log.warning(
                "Timeout attempt %d/%d for %s", attempt, MAX_RETRIES, url
            )
        except requests.exceptions.RequestException as exc:
            log.warning(
                "Request error attempt %d/%d: %s", attempt, MAX_RETRIES, exc
            )

        # sleep before next attempt (skip sleep after the final attempt)
        if attempt < MAX_RETRIES:
            time.sleep(delay)

    log.error("All %d attempts exhausted for %s", MAX_RETRIES, url)
    return None


# ── API calls ─────────────────────────────────────────────────────────────────

def fetch_vehicles(session: requests.Session) -> list:
    """
    Return vehicles on the Red line from GetMapVehiclePoints.
    Passes routeID=ROUTE_ID as a query param (R2).
    Returns [] on any failure.
    """
    url = f"{BASE_URL}/Services/JSONPRelay.svc/GetMapVehiclePoints"
    params = {
        "apiKey":      API_KEY,
        "routeID":     ROUTE_ID,   # R2: explicit route filter
        "isPublicMap": "true",
    }
    data = _get_with_retry(session, url, params)
    if not isinstance(data, list):
        return []
    # secondary filter: keep only rows actually matching ROUTE_ID
    return [v for v in data if v.get("RouteID") == ROUTE_ID]


def fetch_eta(
    session: requests.Session,
    vehicle_id,
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Return (route_stop_id, eta_seconds, eta_time_local) for vehicle_id.
    Returns (None, None, None) on any failure or missing data.

    R1: guarded against empty/non-list/missing Estimates before indexing.
    R4: stores raw integer Seconds; no HH:MM:SS string comparison.
    """
    url = f"{BASE_URL}/Services/JSONPRelay.svc/GetVehicleRouteStopEstimates"
    params = {"vehicleIdStrings": vehicle_id}

    data = _get_with_retry(session, url, params)

    # R1: guard empty / wrong type before indexing
    if not isinstance(data, list) or len(data) == 0:
        return None, None, None

    estimates = data[0].get("Estimates")
    if not estimates or len(estimates) == 0:
        return None, None, None

    est      = estimates[0]
    stop_id  = est.get("RouteStopID")
    eta_sec  = est.get("Seconds")   # R4: integer seconds, not string time

    # Parse EstimateTime for a human-readable local column (supplementary only)
    eta_local      = None
    estimate_time  = est.get("EstimateTime") or ""
    match = re.search(r"/?Date\((\d+)\)/?", estimate_time)
    if match:
        ts_ms   = int(match.group(1))
        utc_dt  = datetime.fromtimestamp(ts_ms / 1000, tz=pytz.utc)
        eta_local = utc_dt.astimezone(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        if estimate_time:
            log.warning("Unparseable EstimateTime for vehicle %s: %s",
                        vehicle_id, estimate_time)

    return stop_id, eta_sec, eta_local


# ── CSV helpers ───────────────────────────────────────────────────────────────

def ensure_csv_headers() -> None:
    """Write header row if CSV is absent or empty."""
    needs_header = (
        not os.path.exists(CSV_PATH)
        or os.path.getsize(CSV_PATH) == 0
    )
    if needs_header:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writeheader()
        log.info("Created CSV with headers: %s", CSV_PATH)


# ── Polling tick ─────────────────────────────────────────────────────────────

def collect_tick(session: requests.Session, snapshot_utc: datetime) -> int:
    """
    Execute one poll tick:
      1. Fetch all Red Line vehicles.
      2. For each vehicle, fetch next-stop ETA.
      3. Append all rows to CSV in a single write + flush (R8).

    Returns the number of rows written.
    """
    vehicles = fetch_vehicles(session)

    # R9: 0 vehicles is a valid state (night / off-schedule); log as heartbeat
    if not vehicles:
        log.info(
            "HEARTBEAT | snapshot=%s | 0 vehicles (route may be inactive)",
            snapshot_utc.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return 0

    rows        = []
    error_count = 0
    snapshot_str = snapshot_utc.strftime("%Y-%m-%d %H:%M:%S+00:00")

    for idx, v in enumerate(vehicles):
        vehicle_id = v.get("VehicleID")

        # R7: small delay between successive ETA calls
        if idx > 0:
            time.sleep(ETA_CALL_DELAY)

        try:
            stop_id, eta_sec, eta_local = fetch_eta(session, vehicle_id)
        except Exception as exc:
            log.warning(
                "ETA call raised for vehicle %s: %s", vehicle_id, exc
            )
            stop_id, eta_sec, eta_local = None, None, None
            error_count += 1

        rows.append({
            "snapshot_time_utc":      snapshot_str,
            "vehicle_id":             vehicle_id,
            "route_id":               v.get("RouteID"),
            "route_stop_id":          stop_id,
            "vehicle_lat":            v.get("Latitude"),
            "vehicle_lon":            v.get("Longitude"),
            "vehicle_speed":          v.get("GroundSpeed"),
            "eta_seconds":            eta_sec,            # R4: integer
            "estimated_time_arrival": eta_sec if eta_sec is not None else "",
            "eta_time_local":         eta_local,
            "poll_interval_seconds":  POLL_INTERVAL,
            "source_method": (
                "GetMapVehiclePoints+GetVehicleRouteStopEstimates"
            ),
        })

    # R8: single writerows() + flush — minimises corruption window
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writerows(rows)
        f.flush()

    log.info(
        "HEARTBEAT | snapshot=%s | vehicles=%d | rows=%d | errors=%d",
        snapshot_utc.strftime("%Y-%m-%d %H:%M:%S"),
        len(vehicles),
        len(rows),
        error_count,
    )
    return len(rows)


# ── Main loop ─────────────────────────────────────────────────────────────────

def run() -> None:
    log.info("=" * 60)
    log.info(
        "Red Line Collector | routeID=%d | poll=%ds | timeout=%ds",
        ROUTE_ID, POLL_INTERVAL, REQUEST_TIMEOUT,
    )
    log.info("CSV  : %s", CSV_PATH)
    log.info("Log  : %s", LOG_PATH)
    log.info("=" * 60)

    ensure_csv_headers()
    session     = requests.Session()  # reuse connection pool across ticks
    total_rows  = 0
    tick_number = 0

    while True:
        tick_number  += 1
        snapshot_utc  = datetime.now(tz=pytz.utc)

        try:
            rows_written  = collect_tick(session, snapshot_utc)
            total_rows   += rows_written
        except Exception as exc:
            # Catch-all so one bad tick never kills the loop
            log.error(
                "Unhandled error in tick %d: %s",
                tick_number, exc, exc_info=True,
            )

        if tick_number % 100 == 0:
            log.info(
                "MILESTONE | tick=%d | total_rows=%d", tick_number, total_rows
            )

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
