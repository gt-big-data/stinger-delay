import requests
import pytz
from datetime import datetime
import random

TRAFFIC_API_KEY = "key"  # Replace with Traffic API key in google cloud platform starting with AIza


# upon calling should return a level of traffic - low, medium, high OR a message indicating the origin and destination are the same
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
