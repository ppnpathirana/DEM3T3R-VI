"""
==============================================================================
DEMETER Weather Intelligence System - Provider Base Module
==============================================================================
Abstract interface and structured data models for all weather providers.
==============================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class CurrentWeather:
    temperature: float               # °C
    feels_like: float                # °C
    humidity: int                    # %
    pressure: float                  # hPa
    rain_probability: int            # %
    precipitation: float             # mm
    wind_speed: float                # km/h
    wind_direction: int              # degrees (0-360)
    wind_direction_cardinal: str     # N, NE, E, SE, S, SW, W, NW
    uv_index: float                  # UV index
    cloud_cover: int                 # %
    visibility: float                # km
    weather_code: int                # WMO code
    weather_condition: str           # e.g., "Partly Cloudy", "Moderate Rain"
    weather_icon: str                # icon identifier
    sunrise: str                     # HH:MM format
    sunset: str                      # HH:MM format
    is_day: bool                     # True / False
    timestamp: str                   # ISO 8601 string

@dataclass
class HourlyItem:
    time: str                        # "13:00"
    full_time: str                   # "2026-08-28T13:00"
    temperature: float               # °C
    feels_like: float                # °C
    humidity: int                    # %
    rain_probability: int            # %
    precipitation: float             # mm
    wind_speed: float                # km/h
    uv_index: float
    weather_condition: str
    weather_icon: str
    weather_code: int

@dataclass
class DailyItem:
    date: str                        # "2026-08-28"
    day_name: str                    # "Today", "Sat", "Sun", etc.
    temp_max: float                  # °C
    temp_min: float                  # °C
    rain_probability: int            # %
    precipitation_sum: float         # mm
    humidity_avg: int                # %
    wind_speed_max: float            # km/h
    wind_direction: str              # Cardinal
    uv_index_max: float
    weather_condition: str
    weather_icon: str
    weather_code: int
    sunrise: str
    sunset: str

@dataclass
class WeatherData:
    latitude: float
    longitude: float
    location_name: str
    provider: str
    current: CurrentWeather
    hourly: List[HourlyItem]         # Next 24 hours
    daily: List[DailyItem]           # 7-Day forecast
    fetched_at: str                  # ISO timestamp
    is_cached: bool = False
    is_offline_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def deg_to_cardinal(deg: float) -> str:
    """Converts wind direction degrees to cardinal compass string."""
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(deg / 45) % 8
    return dirs[ix]

def wmo_code_to_condition(code: int) -> tuple[str, str]:
    """
    Maps WMO Weather Code to condition description and icon string.
    Returns (condition_text, icon_name).
    """
    mapping = {
        0: ("Clear Sky", "sunny"),
        1: ("Mainly Clear", "partly_cloudy_day"),
        2: ("Partly Cloudy", "partly_cloudy_day"),
        3: ("Overcast", "cloudy"),
        45: ("Foggy", "foggy"),
        48: ("Depositing Rime Fog", "foggy"),
        51: ("Light Drizzle", "rainy_light"),
        53: ("Moderate Drizzle", "rainy_light"),
        55: ("Dense Drizzle", "rainy"),
        61: ("Slight Rain", "rainy_light"),
        63: ("Moderate Rain", "rainy"),
        65: ("Heavy Rain", "rainy_heavy"),
        71: ("Slight Snow", "weather_snowy"),
        73: ("Moderate Snow", "weather_snowy"),
        75: ("Heavy Snow", "snowing_heavy"),
        80: ("Slight Rain Showers", "rainy_light"),
        81: ("Moderate Rain Showers", "rainy"),
        82: ("Violent Rain Showers", "rainy_heavy"),
        95: ("Thunderstorm", "thunderstorm"),
        96: ("Thunderstorm with Hail", "thunderstorm"),
        99: ("Severe Thunderstorm", "thunderstorm")
    }
    return mapping.get(code, ("Unknown", "cloud"))

class WeatherProvider(ABC):
    """Abstract interface for all weather data providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        pass
