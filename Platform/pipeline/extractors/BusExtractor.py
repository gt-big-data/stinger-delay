from BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd
from datetime import datetime, timedelta
import pytz
import re

class BusExtractor(BaseExtractor):
    def get_bus_data(self):
        endpoint = "Services/JSONPRelay.svc/GetMapVehiclePoints"
        params = {
            "apiKey": self.api_key,
            "isPublicMap": "true"
        }
        
        vehicles = self._get(endpoint, params=params)
        
        bus_data = []
        
        for vehicle in vehicles:
            raw_timestamp = vehicle["TimeStamp"]
            match = re.search(r'/Date\((\d+)([+-]\d{4})\)/', raw_timestamp)
            
            if not match:
                continue
            
            timestamp_ms = int(match.group(1))
            utc_offset = match.group(2)
            offset_hours = int(utc_offset[:3])
            offset_minutes = int(utc_offset[0] + utc_offset[3:])
            
            utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.utc)
            offset = timedelta(hours=offset_hours, minutes=offset_minutes)
            adjusted_time = utc_time + offset
            timestamp = adjusted_time.astimezone(pytz.timezone('America/New_York'))
            
            bus_id = vehicle["VehicleID"]
            route_id = vehicle["RouteID"]
            latitude = vehicle["Latitude"]
            longitude = vehicle["Longitude"]
            day_of_week = timestamp.strftime('%A')
            month = timestamp.strftime('%m')
            time_of_day = timestamp.strftime('%H:%M:%S')
            bus_speed = vehicle["GroundSpeed"]
            
            stop_id, eta_to_stop = self.get_stop_info(bus_id)
            
            bus_data.append({
                "busid": bus_id,
                "routeid": route_id,
                "latitude": latitude,
                "longitude": longitude,
                "day_of_week": day_of_week,
                "month": month,
                "time_of_day": time_of_day,
                "bus_speed": bus_speed,
                "stop_id": stop_id,
                "eta_to_stop": eta_to_stop
            })
        
        return bus_data
    
    def get_stop_info(self, vehicle_id):
        endpoint = "Services/JSONPRelay.svc/GetVehicleRouteStopEstimates"
        params = {
            "vehicleIdStrings": vehicle_id,
        }

        response = self._get(endpoint, params=params)
        #api call returns current stop bus is heading to and stop after, we want to access current
        estimates = response[0].get("Estimates")

        if estimates:
            est = estimates[0]
            stop_id = est.get("RouteStopID")
            estimate_time = est.get("EstimateTime")
            match = re.search(r'\\?/Date\((\d+)\)\\?/', estimate_time)
            if match:
                timestamp_ms = int(match.group(1))
                utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.utc)
                timestamp = utc_time.astimezone(pytz.timezone('America/New_York'))
                eta_time_of_day = timestamp.strftime('%H:%M:%S')
                return stop_id, eta_time_of_day
        return None, None
    
    def extract(self) -> pd.DataFrame:
        bus_data = self.get_bus_data()
        return pd.DataFrame(bus_data)