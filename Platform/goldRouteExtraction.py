import http.client
import ssl
import csv
import json
import os
import pytz
from datetime import datetime, timedelta
import re

# Create an unverified SSL context to bypass SSL certificate errors
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


eastern = pytz.timezone('America/New_York')

#Add the location where you wanna save the csv here!
directory = os.path.expanduser('~/Desktop/Bus_Delay_Project/')
file_path = os.path.join(directory, 'gold_bus_data.csv')

# Creates the directory if it doesn't exist in ur machine
if not os.path.exists(directory):
    os.makedirs(directory)

# Check if the CSV file already exists to avoid writing headers multiple times
file_exists = os.path.isfile(file_path)

# If the file doesn't exist, write the header row once
if not file_exists:
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['VehicleId', 'Latitude', 'Longitude', 'GroundSpeed', 'Timestamp'])

conn = http.client.HTTPSConnection("bus.gatech.edu")

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

conn.request("GET", "/Services/JSONPRelay.svc/GetMapVehiclePoints?apiKey=8882812681&isPublicMap=true", payload, headers)

res = conn.getresponse()
data = res.read()


vehicles = json.loads(data.decode("utf-8"))


route_9_data = []

for vehicle in vehicles:
    if vehicle["RouteID"] == 9:
        raw_timestamp = vehicle["TimeStamp"]
        match = re.search(r'/Date\((\d+)([+-]\d{4})\)/', raw_timestamp)
        
        if match:
            
            timestamp_ms = int(match.group(1)) 
            
            utc_offset = match.group(2)
            offset_hours = int(utc_offset[:3])  
            offset_minutes = int(utc_offset[0] + utc_offset[3:])  
            
            utc_time = datetime.utcfromtimestamp(timestamp_ms / 1000)
            
            offset = timedelta(hours=offset_hours, minutes=offset_minutes)
            adjusted_time = utc_time - offset 
            

            local_time = pytz.utc.localize(adjusted_time).astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S')


        route_9_data.append({
            "Latitude": vehicle["Latitude"],
            "Longitude": vehicle["Longitude"],
            "VehicleID": vehicle["VehicleID"],
            "GroundSpeed": vehicle["GroundSpeed"],
            "TimeStamp": local_time
        })

with open(file_path, mode='a', newline='') as file:
    writer = csv.writer(file)
    for bus in route_9_data:
        writer.writerow([bus['VehicleID'], bus['Latitude'], bus['Longitude'], bus['GroundSpeed'], bus['TimeStamp']])

print(f"Data for {len(route_9_data)} buses saved to {file_path}.")