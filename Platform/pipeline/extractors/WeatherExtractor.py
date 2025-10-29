from BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd

class WeatherExtractor(BaseExtractor):
    def extract(self) -> pd.DataFrame:
        #implement here
        return