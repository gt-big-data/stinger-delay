from .BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd
import polyline

# for __init__:
# base_url = "https://data.traffic.hereapi.com"
# api_key = HERE_API_KEY
class TrafficExtractor(BaseExtractor):

    def __init__(self, base_url: str, api_key: str) -> None:
        super().__init__(base_url, api_key)
        self.circle_center = "33.784562,-84.394732"  # circle around campus encompassing all bus routes *except emory route
        self.headers = {
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "en-US,en;q=0.9",
            'User-Agent': "StingerDelay/1.0 (contact: gtstingerdelay@gmail.com)",
        }
        self.params = {
            "in": f"circle:{self.circle_center};r=1900",
            "locationReferencing": "shape",
            "apiKey": {self.api_key}
        }

    def extract(self) -> pd.DataFrame:
        response = self._get("v7/incidents", headers=self.headers, params=self.params)
        if (response.get("error") is not None):
            raise Exception(f"Error in TrafficExtractor extract(): {response['error']['message']}")
        incidents: dict[str, dict] = response["results"]
        incidents_simplified: list[dict] = []
        for incident in incidents:
            # we're going to be primarily focused on whether or not there is an incident along our path rather than where exactly the incident is
            # documentation in api on what this int corresponds to
            location = incident["location"]
            shape = location["shape"]
            links = shape["links"]
            incident_polylines = []
            for link in links:
                incident_points = link["points"]
                # encode incidentLinks points as polyline
                incident_PL = polyline.encode([(pt["lat"], pt["lng"]) for pt in incident_points])
                incident_polylines.append(incident_PL)
            
            details = incident["incidentDetails"]
            type = details["type"]
            if (type == "congestion" and incident.get("parentID") is not None):
                continue
            if (type == "laneRestriction"):
                vehicle_restrictions = details.get("vehicleRestrictions")
                vehicle_type_restriction = vehicle_restrictions.get("vehicleType")
                if ("bus" not in vehicle_type_restriction): #dont even add the incident; we shouldnt ever have incident type laneRestriction if it's not for buses
                    continue
            start_time = details.get("startTime") 
            end_time = details.get("endTime")
            is_road_closed = details["roadClosed"]
            if (is_road_closed):
                #this value can only exist if roadClosed is true; if not all the junctions are closed, just treat them like they're open even though there's more possibilities
                if (details.get("junctionTraversability") != "allClosed"):
                    isJunctionsOpen = True
            comment = details.get("comment")
            incident_simplified = {
                "polylines": incident_polylines,
                "type": type,
                "is_road_closed": is_road_closed,
                "start_time": start_time,
                "end_time": end_time,
                "comment": comment
            }
            incidents_simplified.append(incident_simplified)

        dataframe = pd.DataFrame.from_dict(incidents_simplified)
        return dataframe


