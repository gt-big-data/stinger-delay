import pytz
import json
import http.client
import os

eastern = pytz.timezone('America/New_York')

conn_http = http.client.HTTPSConnection("api.tomtom.com")

headers = {
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "en-US,en;q=0.9",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}

bbox = "33.7751983926161,33.7751983926161,33.77642014048971,33.77642014048971"
apikey = os.getenv('TRAFFIC_API_KEY')

# api.tomtom.com/traffic/services/{versionNumber}/incidentDetails?key={Your_Api_Key}&fields={fields}&language={language}&t={t}&categoryFilter={categoryFilter}&timeValidityFilter={timeValidityFilter}
fields = "{incidents{type,geometry{type,coordinates},properties{iconCategory}}}"
conn_http.request("GET", f"/traffic/services/5/incidentDetails?bbox={
                  bbox}&key={apikey}&fields={fields}&language=en-US&timeValidityFilter=present")

res = conn_http.getresponse()

data = res.read()

responsedict = json.loads(data.decode("utf-8"))
incidents: dict[str, dict] = responsedict["incidents"]
for incident in incidents:
    # we're going to be primarily focused on whether or not there is an incident along our path rather than where exactly the incident is
    # documentation in api on what this int corresponds to
    iconCategory: int = incident["iconCategory"]
    delayMagnitude: int = incident["magnitudeOfDelay"]
    delay: int = incident["delay"]  # in seconds
    certainty: str = incident["probabilityOfOccurrence"]
print(responsedict)
