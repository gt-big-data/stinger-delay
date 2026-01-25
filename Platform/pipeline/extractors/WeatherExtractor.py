"""
WeatherExtractor.py
Extracts weather data from weather.gov API and formats it for the database.
"""

from BaseExtractor import ABCBaseExtractor as BaseExtractor
import pandas as pd
from datetime import datetime
import re
from typing import Optional


class WeatherExtractor(BaseExtractor):
    """
    Extracts hourly weather data from weather.gov (National Weather Service) API.
    
    Important: weather.gov doesn't use API keys - it requires a User-Agent header.
    The api_key parameter is kept for compatibility with BaseExtractor but not used.
    """
    
    # Georgia Tech coordinates
    GT_LATITUDE = 33.7756
    GT_LONGITUDE = -84.3963
    
    # Schema that matches your weather_data table
    SCHEMA_COLUMNS = [
        'recorded_at',        # When weather.gov recorded this
        'fetched_at',         # When we fetched it
        'temperature',        # Temperature in Fahrenheit
        'precipitation_probability',  # 0-100%
        'wind_speed',         # mph
        'conditions'          # Description like "Partly Cloudy"
    ]
    
    def __init__(self, base_url: str, api_key: str, user_agent: str = None):
        """
        Initialize WeatherExtractor.
        
        Args:
            base_url: Base URL for weather.gov API (https://api.weather.gov)
            api_key: Not used by weather.gov, but required by BaseExtractor signature
            user_agent: User-Agent string required by weather.gov
                       Format: (YourApp, your-email@gatech.edu)
        """
        super().__init__(base_url, api_key)
        
        # Weather.gov requires a User-Agent header
        if not user_agent:
            raise ValueError(
                "weather.gov requires a User-Agent header. "
                "Format: (YourAppName, your-email@gatech.edu)"
            )
        
        self.user_agent = user_agent
        
        # Set up session headers for all requests
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/geo+json'
        })
    
    def extract(self, since: Optional[str] = None) -> pd.DataFrame:
        """
        Extract current weather data from weather.gov API.
        
        Args:
            since: Not used for weather (always gets current data), 
                   but kept for compatibility with pipeline interface
        
        Returns:
            pd.DataFrame: Single row with current weather data matching
                         weather_data table schema
                         
        Raises:
            Exception: If API request fails or data parsing fails
        """
        try:
            # Step 1: Get forecast URL for Georgia Tech location
            print(f"Fetching weather for coordinates: {self.GT_LATITUDE}, {self.GT_LONGITUDE}")
            
            points_endpoint = f"points/{self.GT_LATITUDE},{self.GT_LONGITUDE}"
            points_data = self._get(points_endpoint)
            
            # Extract the hourly forecast URL from the response
            # Response structure:
            # {
            #   "properties": {
            #     "forecastHourly": "https://api.weather.gov/gridpoints/FFC/52,87/forecast/hourly"
            #   }
            # }
            forecast_hourly_url = points_data['properties']['forecastHourly']
            
            # Step 2: Get hourly forecast data
            # We need to extract just the endpoint part (after base_url)
            # Example: "https://api.weather.gov/gridpoints/FFC/52,87/forecast/hourly"
            #          becomes "gridpoints/FFC/52,87/forecast/hourly"
            forecast_endpoint = forecast_hourly_url.replace(self.base_url + "/", "")
            
            print(f"Fetching hourly forecast from: {forecast_endpoint}")
            forecast_data = self._get(forecast_endpoint)
            
            # Step 3: Extract current period (first in the list)
            # Response structure:
            # {
            #   "properties": {
            #     "periods": [
            #       {
            #         "startTime": "2025-10-18T14:00:00-04:00",
            #         "temperature": 72,
            #         "windSpeed": "10 mph",
            #         "shortForecast": "Partly Cloudy",
            #         "probabilityOfPrecipitation": {"value": 20},
            #         ...
            #       },
            #       ...
            #     ]
            #   }
            # }
            periods = forecast_data['properties']['periods']
            
            if not periods:
                raise ValueError("No forecast periods returned from API")
            
            current_period = periods[0]  # Current hour
            
            # Step 4: Parse data from the current period
            weather_dict = {
                'recorded_at': self._parse_timestamp(current_period['startTime']),
                'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': self._parse_temperature(current_period),
                'precipitation_probability': self._parse_precipitation_probability(current_period),
                'wind_speed': self._parse_wind_speed(current_period),
                'conditions': self._parse_conditions(current_period)
            }
            
            # Step 5: Convert to DataFrame
            df = pd.DataFrame([weather_dict])
            
            # Step 6: Validate DataFrame has correct columns
            self._validate_dataframe(df)
            
            print(f"✓ Extracted weather: {weather_dict['temperature']}°F, "
                  f"{weather_dict['conditions']}, "
                  f"{weather_dict['precipitation_probability']}% precip")
            
            return df
            
        except KeyError as e:
            print(f"✗ Error: Missing expected field in API response: {e}")
            raise
        except Exception as e:
            print(f"✗ Error extracting weather data: {e}")
            raise
    
    # =========================================================================
    # HELPER METHODS - Parse specific fields from API response
    # =========================================================================
    
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """
        Parse ISO 8601 timestamp from weather.gov API.
        
        Converts: "2025-10-18T14:00:00-04:00"
        To:       "2025-10-18 14:00:00"
        
        Args:
            timestamp_str: ISO 8601 timestamp string
            
        Returns:
            str: Formatted timestamp for MySQL DATETIME
        """
        # Take first 19 characters (YYYY-MM-DDTHH:MM:SS)
        # Replace 'T' with space for MySQL format
        return timestamp_str[:19].replace('T', ' ')
    
    def _parse_temperature(self, period: dict) -> float:
        """
        Extract temperature from period data.
        
        Args:
            period: Period dictionary from API response
            
        Returns:
            float: Temperature in Fahrenheit
        """
        temp = period.get('temperature')
        if temp is None:
            print("Warning: Temperature is None, using 0.0")
            return 0.0
        return float(temp)
    
    def _parse_precipitation_probability(self, period: dict) -> int:
        """
        Extract precipitation probability from period data.
        
        API returns: {"value": 20, "unitCode": "wmoUnit:percent"}
        or: null
        
        Args:
            period: Period dictionary from API response
            
        Returns:
            int: Precipitation probability (0-100)
        """
        precip = period.get('probabilityOfPrecipitation')
        
        # Handle null case
        if precip is None:
            return 0
        
        # Handle dict case
        if isinstance(precip, dict):
            value = precip.get('value')
            return int(value) if value is not None else 0
        
        # Handle direct value case (shouldn't happen, but defensive)
        return int(precip) if precip else 0
    
    def _parse_wind_speed(self, period: dict) -> float:
        """
        Parse wind speed from string format.
        
        Handles various formats:
        - "10 mph"
        - "5 to 10 mph"
        - "10 to 15 mph"
        
        For ranges, returns the average.
        
        Args:
            period: Period dictionary from API response
            
        Returns:
            float: Wind speed in mph
        """
        wind_speed_str = period.get('windSpeed', '0 mph')
        
        try:
            # Extract all numbers from the string
            numbers = re.findall(r'\d+', wind_speed_str)
            
            if len(numbers) == 0:
                return 0.0
            elif len(numbers) == 1:
                # Single value: "10 mph"
                return float(numbers[0])
            else:
                # Range: "5 to 10 mph" -> average
                return sum(float(n) for n in numbers) / len(numbers)
                
        except Exception as e:
            print(f"Warning: Could not parse wind speed '{wind_speed_str}': {e}")
            return 0.0
    
    def _parse_conditions(self, period: dict) -> str:
        """
        Extract weather conditions description.
        
        Args:
            period: Period dictionary from API response
            
        Returns:
            str: Conditions description (max 100 chars for VARCHAR(100))
        """
        conditions = period.get('shortForecast', 'Unknown')
        
        # Limit to 100 characters to match database VARCHAR(100)
        return conditions[:100]
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate that DataFrame has all required columns.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If DataFrame is missing required columns
        """
        missing = set(self.SCHEMA_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
        
        print(f"✓ DataFrame validated: {len(df)} row(s), {len(df.columns)} columns")


