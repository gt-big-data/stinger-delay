import requests
from typing import Optional, Dict, Any, List
import pandas as pd

class ABCBaseExtractor:
    """
    Abstract base class for data extrators (bus, weather, traffic).
    Handles HTTP setup and Dataframe conversion
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, headers=headers)
        return response.json()
    
    def extract(self) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement extract()")



