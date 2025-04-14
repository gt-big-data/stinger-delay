import http.client
import ssl
import json
import pytz
from datetime import datetime, timedelta
import re
import psycopg2
import random
from traffic_api import get_traffic_level


# Create an unverified SSL context to bypass SSL certificate errors
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

#postgresql connection
db_host = #'enter db host here'
db_name = #'enter db name here'
db_user = #'enter user here'
db_pass = #'enter password here'
conn = psycopg2.connect(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_pass
)
cur = conn.cursor()

create_table_query = '''
CREATE TABLE IF NOT EXISTS bus_data (
    Latitude FLOAT,
    Longitude FLOAT,
    Weather TEXT,
    Day_Of_Week TEXT,
    Month TEXT,
    Time_Of_Day TEXT,
    Bus_Line TEXT,
    Traffic_Patterns TEXT,
    Bus_Speed FLOAT
);
'''
cur.execute(create_table_query)
conn.commit()

eastern = pytz.timezone('America/New_York')

conn_http = http.client.HTTPSConnection("bus.gatech.edu")


payload = ""

headers = {
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "en-US,en;q=0.9",
    'Connection': "keep-alive",
    'Cookie': "_ga_YL9TMCYRVW=GS1.1.1727204420.1.1.1727204469.0.0.0; _ga_CZ8LWWH02E=GS1.1.1727204478.1.1.1727204525.0.0.0; _ga_SJ0WV16TMZ=GS1.1.1727205516.2.1.1727205531.0.0.0; IDMSESSID=B86F66E469A320FD4FA2D7FFA7F49E783A3CAC5E909F6CF469FE5090696CA67B4A1D21D64A72C0F803830C2574E986A14CADC4C758DAB030138F7CFB948D25F3; _ga_Z1H13P8866=GS1.1.1727300878.1.1.1727300912.0.0.0; __utmzz=utmcsr=google|utmcmd=organic|utmccn=(not set)|utmctr=(not provided); __utmzzses=1; _gcl_au=1.1.2074628732.1727880427; _uetvid=3279c09080cd11efa032a97d265041df; __qca=P0-1197909643-1727880427621; _ga_8XJDVR2ZKP=GS1.1.1727880427.1.1.1727880559.60.0.123814909; _ga_9CNBFQSR13=GS1.1.1727887908.6.1.1727888501.0.0.0; _hjSessionUser_3867652=eyJpZCI6ImNhNDMxZDliLTkwOGYtNTRiNC04Yjc5LWYxZDBkYzcwNjNlOSIsImNyZWF0ZWQiOjE3MjgwMDI0Nzc2NzEsImV4aXN0aW5nIjpmYWxzZX0=; _clck=1624b3h%7C2%7Cfpq%7C0%7C1738; _ga_L3KDESR6P8=GS1.1.1728002477.1.0.1728002479.0.0.0; _ga_2MBD9GQBMN=GS1.1.1728002486.1.0.1728002491.0.0.0; uvts=877f2d29-080e-486e-5eef-955ad1fc4ef9; uvts=877f2d29-080e-486e-5eef-955ad1fc4ef9; _ga_YQ2T2WEJGD=GS1.1.1728009995.1.0.1728010001.0.0.0; _ga_93GEGKW8BW=GS1.1.1728012632.4.0.1728012632.0.0.0; _ga_EF4W4FWYSY=GS1.1.1728012698.3.0.1728012698.0.0.0; _ga_DBY1MDQHS1=GS1.1.1728013191.4.0.1728013191.0.0.0; _ga_0JX343VW9C=GS1.1.1728015605.5.0.1728015605.0.0.0; _ga_GP3B01FPCR=GS1.1.1728318962.1.1.1728319108.0.0.0; _ga_4TW76PBJ0Q=GS1.1.1728326489.3.0.1728326489.0.0.0; _ga_FLTL39B1PG=GS1.1.1728399177.2.0.1728399190.47.0.0; _ga_Z4692LF09P=GS1.2.1728399191.1.1.1728399312.0.0.0; _ga_8KYT382EEK=GS1.1.1728440477.1.1.1728440489.0.0.0; _ga_1GCJM0BLWC=GS1.1.1728440477.1.1.1728440489.0.0.0; _ga_Q31MNNV2D0=GS1.1.1728484225.4.1.1728484226.0.0.0; _ga_D33HBH7FLV=GS1.1.1729100749.2.0.1729100749.0.0.0; _ga_LZK8E5FSWB=GS1.1.1729101112.9.1.1729101457.0.0.0; _ga_6RZR70FHRV=GS1.1.1729189874.10.0.1729189877.0.0.0; _ga_30TT54P0XE=GS1.1.1729189874.19.0.1729189877.0.0.0; _gid=GA1.2.214760471.1729189879; _ga=GA1.1.132668840.1727107358; _ga_8GV2SFW61G=GS1.1.1729189878.15.0.1729189878.0.0.0; _ga_88F5K1QFR9=GS1.1.1729189878.15.0.1729189878.60.0.0",
    'Referer': "https://bus.gatech.edu/routes/9/stops",
    'Sec-Fetch-Dest': "empty",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Site': "same-origin",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': "?0",
    'sec-ch-ua-platform': '"macOS"'
    }

conn_http.request("GET", "/Services/JSONPRelay.svc/GetMapVehiclePoints?apiKey=8882812681&isPublicMap=true", payload, headers)

res = conn_http.getresponse()

data = res.read()


vehicles = json.loads(data.decode("utf-8"))

# sample stops for Gold route
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

# random origin stop choice
origin_stop = random.choice(list(stops_dict.keys()))
# its coordinates
origin_coords = stops_dict[origin_stop]
#print(origin_stop)

# random destination stop choice
destination_stop = random.choice(list(stops_dict.keys()))
# its coordinates 
destination_coords = stops_dict[destination_stop]
#print(destination_stop)

#print(get_traffic_level(origin_coords, destination_coords))

bus_data = []
"RouteID"
for vehicle in vehicles:
    
    raw_timestamp = vehicle["TimeStamp"]
    match = re.search(r'/Date\((\d+)([+-]\d{4})\)/', raw_timestamp)
        
    if match:
            
        timestamp_ms = int(match.group(1)) 
            
        utc_offset = match.group(2)
        offset_hours = int(utc_offset[:3])  
        offset_minutes = int(utc_offset[0] + utc_offset[3:])  
            
        utc_time = datetime.utcfromtimestamp(timestamp_ms / 1000)
            
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        adjusted_time = utc_time + offset
            

        day = adjusted_time.replace(tzinfo=pytz.utc).astimezone(eastern).strftime('%A')
        month = adjusted_time.replace(tzinfo=pytz.utc).astimezone(eastern).strftime('%m')
        time = adjusted_time.replace(tzinfo=pytz.utc).astimezone(eastern).strftime('%H:%M:%S')


        bus_data.append({
            "Latitude": vehicle["Latitude"],
            "Longitude": vehicle["Longitude"],
            "Weather": "N/A",
            "Day_Of_Week": day,
            "Month": month,
            "Time_Of_Day": time,
            "Bus_Line": vehicle["RouteID"],
            "Traffic_Patterns": get_traffic_level(origin_coords, destination_coords),
            "Bus_Speed": vehicle["GroundSpeed"]
            })

for bus in bus_data:
    cur.execute(
        "INSERT INTO bus_data (Latitude, Longitude, Weather, Day_Of_Week, Month, Time_Of_Day, Bus_Line, Traffic_Patterns, Bus_Speed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (bus['Latitude'], bus['Longitude'], bus['Weather'], bus['Day_Of_Week'], bus['Month'], bus['Time_Of_Day'], bus['Bus_Line'], bus['Traffic_Patterns'], bus['Bus_Speed'])
    )
conn.commit()

print(f"Data for {len(bus_data)} buses saved.")

cur.close()
conn.close()