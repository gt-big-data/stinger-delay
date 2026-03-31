import os
import time
import csv
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv

# load api key from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# constants
BASE_URL = "https://bus.gatech.edu/Services/JSONPRelay.svc"
ROUTE_ID = 28  # clough route id
POLL_INTERVAL = 30  # seconds between polls
OUTPUT_FILE = "clough_bus_data.csv"
TIMEZONE = pytz.timezone("America/New_York")

# create CSV file with header if it doesn't exist
if not os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "snapshot_time",
            "vehicle_id",
            "route_id",
            "route_stop_id",
            "vehicle_lat",
            "vehicle_lon",
            "vehicle_speed",
            "estimated_time_arrival"
        ])
    print(f"created csv file: {OUTPUT_FILE}")

# function to get vehicle positions from API
def get_vehicle_points():
    url = f"{BASE_URL}/GetMapVehiclePoints?apiKey={API_KEY}&isPublicMap=true"
    r = requests.get(url, timeout=15)
    r.raise_for_status()  # will raise an error if request failed
    print(f"fetched {len(r.json())} vehicles from API")
    return r.json()

# function to get stop estimates for given vehicle IDs
def get_estimates(vehicle_ids):
    if not vehicle_ids:
        print("no vehicles to fetch estimates for")
        return {}
    ids = ",".join(str(v) for v in vehicle_ids)
    url = f"{BASE_URL}/GetVehicleRouteStopEstimates?vehicleIdStrings={ids}&quantity=1"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    out = {}
    for v in data:
        vid = v.get("VehicleID")
        ests = v.get("Estimates") or []
        if ests:
            out[vid] = ests[0]
    print(f"fetched estimates for {len(out)} vehicles")
    return out

# Main scraper loop
def main():
    print("clough route scraper has started")
    while True:
        try:
            vehicles = get_vehicle_points() # get all vehicles
            vehicles = [v for v in vehicles if v.get("RouteID") == ROUTE_ID] # filters out other routes
            print(f"found {len(vehicles)} vehicles on route {ROUTE_ID}")

            vehicle_ids = [v.get("VehicleID") for v in vehicles]
            estimates = get_estimates(vehicle_ids) # get stop estimates

            snapshot_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z") # current timestamp
            print(f"snapshot time: {snapshot_time}")

            # adds data to CSV
            with open(OUTPUT_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                for v in vehicles:
                    vid = v.get("VehicleID")
                    est = estimates.get(vid, {})
                    writer.writerow([
                        snapshot_time,
                        vid,
                        v.get("RouteID"),
                        est.get("RouteStopId"),
                        v.get("Latitude"),
                        v.get("Longitude"),
                        v.get("GroundSpeed"),
                        est.get("EstimateTime")
                    ])
                    print(f"wrote data for vehicle {vid}")

        except Exception as e:
            print(f"error occurred: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()