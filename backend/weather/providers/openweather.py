"""
==============================================================================
DEMETER Weather Intelligence System - OpenWeatherMap Provider (Fallback 2)
==============================================================================
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any
from backend.weather.providers.base import (
    WeatherProvider, WeatherData, CurrentWeather, HourlyItem, DailyItem,
    deg_to_cardinal
)

class OpenWeatherProvider(WeatherProvider):
    """Fallback weather provider using OpenWeatherMap OneCall API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    @property
    def name(self) -> str:
        return "OpenWeather"

    def is_available(self) -> bool:
        key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        return bool(key and "your-" not in key)

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        if not key:
            raise ValueError("OPENWEATHER_API_KEY not set in .env")

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": key,
            "units": "metric"
        }

        response = requests.get(self.BASE_URL, params=params, timeout=8.0)
        if response.status_code != 200:
            raise RuntimeError(f"OpenWeather error HTTP {response.status_code}: {response.text[:200]}")

        data = response.json()
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather_list = data.get("weather", [{}])
        cond_main = weather_list[0].get("main", "Clear")
        cond_desc = weather_list[0].get("description", "Clear sky").title()

        now_iso = datetime.now().isoformat()
        current_weather = CurrentWeather(
            temperature=round(main.get("temp", 25.0), 1),
            feels_like=round(main.get("feels_like", 25.0), 1),
            humidity=int(main.get("humidity", 60)),
            pressure=round(main.get("pressure", 1013.0), 1),
            rain_probability=0,
            precipitation=0.0,
            wind_speed=round(wind.get("speed", 0.0) * 3.6, 1), # m/s to km/h
            wind_direction=int(wind.get("deg", 0)),
            wind_direction_cardinal=deg_to_cardinal(wind.get("deg", 0)),
            uv_index=5.0,
            cloud_cover=int(data.get("clouds", {}).get("all", 0)),
            visibility=round(data.get("visibility", 10000) / 1000.0, 1),
            weather_code=weather_list[0].get("id", 800),
            weather_condition=cond_desc,
            weather_icon="partly_cloudy_day",
            sunrise="06:00",
            sunset="18:00",
            is_day=True,
            timestamp=now_iso
        )

        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            location_name=data.get("name", f"{latitude:.4f}°N, {longitude:.4f}°E"),
            provider=self.name,
            current=current_weather,
            hourly=[],
            daily=[],
            fetched_at=now_iso
        )
