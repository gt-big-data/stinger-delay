from .BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd
from datetime import datetime, time, timedelta
import pytz
import re

"""
Route Ids
Red: 20
Blue: 21
Green: 17
Emory: 18
Gold: 29
Clough: 28
Night Gold/Clough: 30
Northside Dr. - Atlantic Station: 26
Nara/Science SQ: 22
"""
class BusExtractor(BaseExtractor):

    def __init__(self, base_url: str, api_key:str):
        super().__init__(base_url, api_key)
    
    def get_bus_data(self):
        endpoint = "/Services/JSONPRelay.svc/GetMapVehiclePoints?"
        params = {
            "apiKey": self.api_key,
            "isPublicMap": "true"
        }
        
        vehicles = self._get(endpoint, params=params)
        
        bus_data = {}
        
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
            
            destination_route_stop_id, eta_to_stop = self.get_stop_info(bus_id)
            #api call may return an eta where eta < t_o_d, in which we symbol with 0 to show bus already arrived or passed stop
            #this only matters when keeping eta as a timestamp
            # if eta_to_stop < time_of_day:
            #     eta_to_stop = 0
            
            bus_data[bus_id] = {
                "bus_id": bus_id,
                "route_id": route_id,
                "latitude": latitude,
                "longitude": longitude,
                "day_of_week": day_of_week,
                "month": month,
                "time_of_day": time_of_day,
                "bus_speed": bus_speed,
                "destination_route_stop_id": destination_route_stop_id,
                "eta_to_stop": eta_to_stop,
                "snapshot_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self.get_capacity_info(bus_data)
        
        return list(bus_data.values())
    
    def get_stop_info(self, vehicle_id):
        endpoint = "/Services/JSONPRelay.svc/GetVehicleRouteStopEstimates?"
        params = {
            "vehicleIdStrings": vehicle_id,
        }

        response = self._get(endpoint, params=params)
        estimates = response[0].get("Estimates")

        if estimates:
            est = estimates[0]
            route_stop_id = est.get("RouteStopID")
            eta = est.get("Seconds")
            # on_route = est.get("OnRoute")
            #add a log message to see if this value is ever actually false
            # if on_route == False:
                
            # this code will make eta a timestamp rather than a seconds count
            #
            # estimate_time = est.get("EstimateTime")
            # match = re.search(r'\\?/Date\((\d+)\)\\?/', estimate_time)
            # if match:
            #     timestamp_ms = int(match.group(1))
            #     utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.utc)
            #     timestamp = utc_time.astimezone(pytz.timezone('America/New_York'))
            #     eta_time_of_day = timestamp.strftime('%H:%M:%S')
            #     return route_stop_id, eta_time_of_day
            return route_stop_id, eta
        return None, None

    def get_capacity_info(self, bus_data):
        endpoint = "/Services/JSONPRelay.svc/GetVehicleCapacities"
        params = {}

        response = self._get(endpoint, params=params)

        for vehicle in response:
            bus_id = vehicle.get("VehicleID")
            capacity = vehicle.get("Capacity")
            occupancy = vehicle.get("CurrentOccupation")
            values = bus_data.get(bus_id)
            if values:
                values["capacity"] = capacity
                values["occupancy"] = occupancy

    
    def extract(self) -> pd.DataFrame:
        bus_data = self.get_bus_data()
        return pd.DataFrame(bus_data)
