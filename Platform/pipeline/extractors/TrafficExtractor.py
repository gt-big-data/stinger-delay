from BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd
import polyline

# for __init__:
# base_url = "https://data.traffic.hereapi.com"
# api_key = HERE_API_KEY
class TrafficExtractor(BaseExtractor):
    def extract(self) -> pd.DataFrame:
        headers = {
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "en-US,en;q=0.9",
            'User-Agent': "StingerDelay/1.0 (contact: gtstingerdelay@gmail.com)",
        }

        # circle around campus encompassing all bus routes *except emory route
        circleCenter = "33.784562,-84.394732"

        params = {
            "in": f"circle:{circleCenter};r=1900",
            "locationReferencing": "shape",
            "apiKey": {self.api_key}
        }

        response = self._get("v7/incidents/", headers=headers, params=params)
        incidents: dict[str, dict] = response["results"]
        incidents_simplified: list[dict] = []
        for incident in incidents:
            # we're going to be primarily focused on whether or not there is an incident along our path rather than where exactly the incident is
            # documentation in api on what this int corresponds to
            incidentPoints = incident["location"]["shape"]["links"]["points"]
            #encode incidentLinks points as polyline
            incidentPL = polyline.encode([(pt["latitude"], pt["longitude"]) for pt in incidentPoints])
            details = incident["incidentDetails"]
            type = details["type"]
            if (type == "congestion" and incident.get("parentID") is not None):
                continue
            if (type == "laneRestriction"):
                vehicleRestrictions = details.get("vehicleRestrictions")
                vehicleTypeRestriction = vehicleRestrictions.get("vehicleType")
                if ("bus" not in vehicleTypeRestriction): #dont even add the incident; we shouldnt ever have incident type laneRestriction if it's not for buses
                    continue
            startTime = details.get("startTime") 
            endTime = details.get("endTime")
            isRoadClosed = details["roadClosed"]
            if (isRoadClosed):
                #this value can only exist if roadClosed is true; if not all the junctions are closed, just treat them like they're open even though there's more possibilities
                if (details.get("junctionTraversability") != "allClosed"):
                    isJunctionsOpen = True
            comment = details.get("comment")
            incident_simplified = {
                "polyline": incidentPL,
                "type": type,
                "is_road_closed": isRoadClosed,
                "start_time": startTime,
                "end_time": endTime,
                "comment": comment
            }
            incidents_simplified.append(incident_simplified)

        dataframe = pd.DataFrame.from_dict(incidents_simplified)
        return dataframe
