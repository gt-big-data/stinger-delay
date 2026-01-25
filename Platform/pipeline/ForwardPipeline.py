from Config import Config
from extractors.BusExtractor import BusExtractor
from extractors.TrafficExtractor import TrafficExtractor
from extractors.WeatherExtractor import WeatherExtractor
from repository import DbRepository
import os
from datetime import datetime, timezone

class ForwardPipeline:
    def __init__(self, cfg: Config):
        #self.repo = DbRepository(cfg.pg_dsn)
        self.bus = BusExtractor(base_url=os.environ["BUS_API_URL"], api_key=cfg.bus_key)
        self.weather = WeatherExtractor(base_url=os.environ["WEATHER_API_URL"], api_key="", user_agent=cfg.weather_user_agent)
        self.traffic = TrafficExtractor(base_url=os.environ["TRAFFIC_API_URL"], api_key=cfg.traffic_key)

    def run_once(self, since: str | None = None):
        batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        bus_df = self.bus.extract()
        print("\n=== BUS DATA ===")
        print(f"batch={batch} rows={len(bus_df)}")
        print(bus_df.head())
        print(bus_df.dtypes)
        #self.repo.copy_to_staging(bus_df, "staging_stop_events", {"source_batch": batch})

        weather_df = self.weather.extract(since=since)
        #self.repo.copy_to_staging(weather_df, "staging_weather", {"source_batch": batch})
        print("\n=== WEATHER DATA ===")
        print(f"batch={batch} rows={len(weather_df)}")
        print(weather_df.head())
        print(weather_df.dtypes)

        traffic_df = self.traffic.extract()
        print("\n=== TRAFFIC DATA ===")
        print(f"batch={batch} rows={len(traffic_df)}")
        print(traffic_df.head())
        print(traffic_df.dtypes)
        #self.repo.copy_to_staging(traffic_df, "staging_traffic", {"source_batch": batch})

        #self.repo.merge_core(SQL_MERGE_STOP_EVENTS)
        #self.repo.merge_core(SQL_MERGE_WEATHER)
        #self.repo.merge_core(SQL_MERGE_TRAFFIC)
