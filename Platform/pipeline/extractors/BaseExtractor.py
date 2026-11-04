import requests
from typing import Optional, Dict, Any, List
import pandas as pd

class ExtractorRequestError(Exception):
    """Base class for exceptions in this module."""

class ABCBaseExtractor:
    """
    Abstract base class for data extrators (bus, weather, traffic).
    Handles HTTP setup and Dataframe conversion
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()

    def _get(
            self,
            endpoint: str,
            params: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        extractor_name = type(self).__name__

        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise ExtractorRequestError(
                f"{extractor_name}: request timed out."
            ) from exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            raise ExtractorRequestError(
                f"{extractor_name}: request failed with HTTP status {status}."
            ) from exc
        except requests.RequestException as exc:
            raise ExtractorRequestError(
                f"{extractor_name}: request could not be completed."
            ) from exc

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise ExtractorRequestError(
                f"{extractor_name}: response was not valid JSON."
            ) from exc
    
    def extract(self) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement extract()")



