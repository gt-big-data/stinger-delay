#!/usr/bin/env python3
"""
NWS weather for Georgia Tech / Midtown Atlanta (or any lat/lon).

Usage:
  python nws_gt_weather.py            # uses GT coords (33.7756, -84.3963)
  python nws_gt_weather.py 33.7756 -84.3963
"""

import sys
import time
import requests
import requests
from dotenv import load_dotenv
import os
# Load environment variables from .env
load_dotenv()

BASE = "https://api.weather.gov"
USER_AGENT = os.getenv("NWS_USER_AGENT")

if not USER_AGENT:
    raise ValueError("Missing NWS_USER_AGENT in .env file")

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/geo+json",
}
def fetch_json(url, timeout=15, max_retries=3):
    """GET JSON with basic retry on 429 or transient errors."""
    url = url.strip()  # avoids the %0A (newline) bug
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 429:
                # Respect Retry-After if present; fall back to 5s
                wait = int(r.headers.get("Retry-After", "5"))
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)  # backoff and retry

def get_points(lat, lon):
    return fetch_json(f"{BASE}/points/{lat},{lon}")

def get_forecast_urls(lat, lon):
    pts = get_points(lat, lon)
    props = pts.get("properties", {})
    return {
        "forecast": props.get("forecast"),
        "forecastHourly": props.get("forecastHourly"),
        "forecastGridData": props.get("forecastGridData"),
        "cwa": props.get("cwa"),
        "gridX": props.get("gridX"),
        "gridY": props.get("gridY"),
    }

def get_hourly_periods(lat, lon, hours=6):
    urls = get_forecast_urls(lat, lon)
    hourly_url = urls["forecastHourly"]
    if not hourly_url:
        # Fallback to gridpoints if hourly URL missing
        cwa, x, y = urls["cwa"], urls["gridX"], urls["gridY"]
        if not all([cwa, x, y]):
            raise RuntimeError("Could not resolve gridpoint for hourly forecast.")
        hourly_url = f"{BASE}/gridpoints/{cwa}/{x},{y}/forecast/hourly"
    data = fetch_json(hourly_url)
    return data.get("properties", {}).get("periods", [])[:hours]

def get_active_alerts(lat, lon):
    # Alerts near a point
    url = f"{BASE}/alerts?point={lat},{lon}&status=actual&message_type=alert"
    data = fetch_json(url)
    return data.get("features", [])

def fmt_temp(p):
    t = p.get("temperature")
    u = p.get("temperatureUnit", "F")
    return f"{t}°{u}" if t is not None else "—"

def main():
    # Default: Georgia Tech (Tech Tower vicinity)
    lat = 33.7756
    lon = -84.3963
    if len(sys.argv) == 3:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])

    try:
        periods = get_hourly_periods(lat, lon, hours=8)
        alerts = get_active_alerts(lat, lon)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"NWS hourly forecast (next {len(periods)} hrs) for {lat:.4f}, {lon:.4f}")
    print("-" * 72)
    for p in periods:
        start = p.get("startTime", "")[:16].replace("T", " ")
        wind = p.get("windSpeed", "—")
        gusts = p.get("windGust")
        precip = p.get("probabilityOfPrecipitation", {}).get("value")
        precip_str = f"{int(precip)}%" if precip is not None else "—"
        short = p.get("shortForecast", "—")
        extra = f", gusts {gusts}" if gusts else ""
        print(f"{start}  {fmt_temp(p)}  PoP {precip_str}  Wind {wind}{extra}  | {short}")

    if alerts:
        print("\nActive weather alerts:")
        for a in alerts[:5]:
            props = a.get("properties", {})
            print(f" - {props.get('event', 'Alert')}: {props.get('headline', '').strip()}")

if __name__ == "__main__":
    main()
