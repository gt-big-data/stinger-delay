from dataclasses import dataclass
import os

class Config:
    pg_dsn: str = os.environ["PG_DSN"]
    bus_key: str = os.environ["BUS_API_KEY"]
    weather_user_agent: str = os.environ["WEATHER_USER_AGENT"]
    traffic_key: str = os.environ["TRAFFIC_API_KEY"]