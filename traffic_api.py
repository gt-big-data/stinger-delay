import requests
import pytz
from datetime import datetime
import random

TRAFFIC_API_KEY = "AIzaSyCeOi3OLyGCSnYNgLAeU9UBMWiT6JyMt2Y"  # Replace with your actual key

def get_traffic_level(origin, destination):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": f"{origin[0]},{origin[1]}",  # Convert tuple to lat,lng format
        "destinations": f"{destination[0]},{destination[1]}",  # Convert tuple to lat,lng format
        "departure_time": 'now',  
        "traffic_model": "best_guess",
        "key": TRAFFIC_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes (e.g., 400, 500)
        data = response.json()

        # Check if the API returns valid data
        if data.get("status") != "OK":
            print("Error: API response status is not OK")
            return None

        element = data["rows"][0]["elements"][0]
        normal_duration = element["duration"]["value"]
        traffic_duration = element.get("duration_in_traffic", {}).get("value", normal_duration)
        
        if origin == destination:
            return "Origin and destination are the same."

        if traffic_duration <= normal_duration:
            #print('Low')
            return "Low"
        elif traffic_duration <= 1.3 * normal_duration:
            #print('Medium')
            return "Medium"
        else:
            #print('High')
            return "High"
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None


stops_dict = {
    "Marta": (33.78124531457225, -84.38609515855521),
    "Technology square": (33.77693168042234, -84.38985431852313),
    "5th Street WB": (33.77696524446127, -84.39177713175643),
    "Russ Chandler Stadium": (33.77700226733594, -84.39405232716865),
    "Klaus Building WB": (33.77750297477602, -84.3955435318594),
    "Nanotechnology": (33.778361110340406, -84.39806140119877),
    "Kendeda Building": (33.7784220826717, -84.39957983900081),
    "Couch Park": (33.77804350814352, -84.4020813989256),
    "CRC & Stamps Health": (33.7750633043881, -84.40272409315902),
    "Ferst Drive & Campus Center": (33.7733218207678, -84.39921557992542),
    "Transit Hub": (33.77314438101725, -84.39700294107278),
    "Campus Center": (33.77347874294925, -84.3991488920771),
    "Exhibition Hall": (33.77508233091718, -84.40238068190583),
    "Ferst Dr & Hemphill Ave": (33.778433040576374, -84.40085640923526),
    "Cherry Emerson": (33.77822274400314, -84.3973364838895),
    "Klaus Building EB": (33.77715065747476, -84.39554176833916),
    "Ferst Dr & Fowler St": (33.776870955985096, -84.39380500062757),
    "5th Street Bridge EB": (33.7768316079988, -84.39190623554501),
    "Technology Square EB": (33.77679019002961, -84.38972625670338),
    "College of Business": (33.77675787854372, -84.38777167574695),
    "Academy of Medicine": (33.77848885105469, -84.38719153190587)
}

origin_stop = random.choice(list(stops_dict.keys()))
origin_coords = stops_dict[origin_stop]
print(origin_stop)

destination_stop = random.choice(list(stops_dict.keys()))
destination_coords = stops_dict[destination_stop]
print(destination_stop)

print(get_traffic_level(origin_coords, destination_coords))


