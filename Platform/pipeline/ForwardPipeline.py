from Config import Config
from extractors import BusExtractor, WeatherExtractor, TrafficExtractor
from repository import DbRepository
import os
from datetime import datetime, timezone

class ForwardPipeline:
    def __init__(self, cfg: Config):
        self.repo = DbRepository(cfg.pg_dsn)
        self.bus = BusExtractor(base_url=os.environ["BUS_API_URL"], api_key=cfg.bus_key)
        self.weather = WeatherExtractor(base_url=os.environ["WEATHER_API_URL"], api_key=cfg.weather_key)
        self.traffic = TrafficExtractor(base_url=os.environ["TRAFFIC_API_URL"], api_key=cfg.traffic_key)

    def run_once(self, since: str | None = None):
        batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        bus_df = self.bus.extract(since=since)
        self.repo.copy_to_staging(bus_df, "staging_stop_events", {"source_batch": batch})

        weather_df = self.weather.extract(since=since)
        self.repo.copy_to_staging(weather_df, "staging_weather", {"source_batch": batch})

        traffic_df = self.traffic.extract(since=since)
        self.repo.copy_to_staging(traffic_df, "staging_traffic", {"source_batch": batch})

        self.repo.merge_core(SQL_MERGE_STOP_EVENTS)
        self.repo.merge_core(SQL_MERGE_WEATHER)
        self.repo.merge_core(SQL_MERGE_TRAFFIC)
