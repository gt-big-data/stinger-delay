from pyproj import Transformer
import polyline
import requests
import os
from dotenv import load_dotenv
from shapely.geometry import LineString, MultiLineString
from shapely.ops import transform

load_dotenv()
HERE_API_KEY = os.getenv('TRAFFIC_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

headers = {
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "en-US,en;q=0.9",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}
def get_traffic_incidents():
    # circle around campus encompassing all bus routes *except emory route
    circleCenter = "33.784562,-84.394732"
    url = "https://data.traffic.hereapi.com/v7/incidents"

    params = {
        "in": f"circle:{circleCenter};r=1900",
        "locationReferencing": "shape",
        "apiKey": {HERE_API_KEY}
    }

    # example request for new york: https://data.traffic.hereapi.com/v7/incidents?in=circle:40.67745729675291,-73.95143080826574;r=4000&locationReferencing=shape&apiKey=[key]
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        responsedict = res.json()
        incidents: dict[str, dict] = responsedict["results"]
        for incident in incidents:
            # we're going to be primarily focused on whether or not there is an incident along our path rather than where exactly the incident is
            # documentation in api on what this int corresponds to
            incidentPoints = incident["location"]["shape"]["links"]["points"]
            #encode incidentLinks points as polyline
            incidentPL = polyline.encode([(pt["latitude"], pt["longitude"]) for pt in incidentPoints])
            details = incident["details"]
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
        print(responsedict)
    else:
        print(f"Error: {res.status_code}")


def snap_segment_to_roads(points):
    '''
    Snap a list of (lat, lng) coordinate pairs to the nearest roads using
    Google Roads API's Snap-to-Roads endpoint.

    Returns:
        List[Tuple[float, float]]: snapped points.
    '''

    snapped = []
    # Google Roads API accepts a maximum of 100 points per request
    CHUNK_SIZE = 100

    for i in range(0, len(points), CHUNK_SIZE):
        chunk = points[i: i + CHUNK_SIZE]
        # build the pipe-delimited path parameter
        path_param = "|".join(f"{lat},{lng}" for lat, lng in chunk)
        params = {
            "path": path_param,
            "key": GOOGLE_MAPS_API_KEY,
            "interpolate": "true"
        }
        url = "https://roads.googleapis.com/v1/snapToRoads"
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get("snappedPoints", [])

        for pt in data:
            loc = pt["location"]
            snapped.append((loc["latitude"], loc["longitude"]))

    return snapped

def buffered_overlap_length(busRoutePL, incidentSegmentPL):
    busRoute = polyline.decode(busRoutePL)
    incidentSegment = polyline.decode(incidentSegmentPL)
    # 2) build lon/lat LineStrings
    busLineString = LineString([(lng,lat) for lat,lng in busRoute])
    incidentLineString = LineString([(lng,lat) for lat,lng in incidentSegment])
    #convert to metres
    _to_m = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True).transform
    busLineString_m = transform(_to_m, busLineString)
    incidentLineString_m = transform(_to_m, incidentLineString)
    #buffer L1 by 1 m and clip L2 to it
    clip = incidentLineString_m.intersection(busLineString_m.buffer(1.0))
    #clip might be a LineString or MultiLineString
    if clip.is_empty:
        return 0.0
    if clip.geom_type == "LineString":
        return clip.length
    # sum up if it’s a MultiLineString
    return sum(part.length for part in clip.geoms)

''' example calculation
tenth = [(33.7815323302537, -84.40298051970377), (33.78154928547461, -84.40514810444054)]
tenthNhemphill = [(33.7815323302537, -84.40298051970377), (33.781555870463414, -84.40423663101498), (33.7823777273216, -84.40474060390883)]
hemphill = [(33.78108199939774, -84.40378518236166), (33.78207629110042, -84.40452547200691)]
aSnapped = snap_segment_to_roads(tenth)
bSnapped = snap_segment_to_roads(hemphill)
aSnappedPoly = polyline.encode(aSnapped)
bSnappedPoly = polyline.encode(bSnapped)
print("Snapped A:", aSnapped)
print("Snapped B:", bSnapped)
print(buffered_overlap_length(aSnappedPoly, bSnappedPoly))
'''
