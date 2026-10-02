"""
@file: weather_api.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
==============================================================================
DEMETER Weather Intelligence System - WeatherAPI Provider (Fallback 1)
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

class WeatherAPIProvider(WeatherProvider):
    """Fallback weather provider using WeatherAPI.com."""

    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    @property
    def name(self) -> str:
        return "WeatherAPI"

    def is_available(self) -> bool:
        key = os.getenv("WEATHERAPI_KEY", "").strip()
        return bool(key and "your-" not in key)

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        key = os.getenv("WEATHERAPI_KEY", "").strip()
        if not key:
            raise ValueError("WEATHERAPI_KEY not set in .env")

        params = {
            "key": key,
            "q": f"{latitude},{longitude}",
            "days": 7,
            "aqi": "no",
            "alerts": "no"
        }

        response = requests.get(self.BASE_URL, params=params, timeout=8.0)
        if response.status_code != 200:
            raise RuntimeError(f"WeatherAPI error HTTP {response.status_code}: {response.text[:200]}")

        data = response.json()
        curr_raw = data.get("current", {})
        loc_raw = data.get("location", {})
        forecast_days = data.get("forecast", {}).get("forecastday", [])

        location_name = f"{loc_raw.get('name', '')}, {loc_raw.get('country', '')}"
        now_iso = datetime.now().isoformat()

        current_weather = CurrentWeather(
            temperature=round(curr_raw.get("temp_c", 25.0), 1),
            feels_like=round(curr_raw.get("feelslike_c", 25.0), 1),
            humidity=int(curr_raw.get("humidity", 60)),
            pressure=round(curr_raw.get("pressure_mb", 1013.0), 1),
            rain_probability=int(forecast_days[0].get("day", {}).get("daily_chance_of_rain", 0)) if forecast_days else 0,
            precipitation=round(curr_raw.get("precip_mm", 0.0), 1),
            wind_speed=round(curr_raw.get("wind_kph", 0.0), 1),
            wind_direction=int(curr_raw.get("wind_degree", 0)),
            wind_direction_cardinal=curr_raw.get("wind_dir", "N"),
            uv_index=round(curr_raw.get("uv", 0.0), 1),
            cloud_cover=int(curr_raw.get("cloud", 0)),
            visibility=round(curr_raw.get("vis_km", 10.0), 1),
            weather_code=curr_raw.get("condition", {}).get("code", 1000),
            weather_condition=curr_raw.get("condition", {}).get("text", "Clear"),
            weather_icon="partly_cloudy_day",
            sunrise="06:00",
            sunset="18:00",
            is_day=bool(curr_raw.get("is_day", 1)),
            timestamp=now_iso
        )

        daily_list = []
        hourly_list = []

        day_names_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for i, day in enumerate(forecast_days):
            d_raw = day.get("day", {})
            d_date = day.get("date", "")
            dt_obj = datetime.strptime(d_date, "%Y-%m-%d") if d_date else datetime.now()
            
            day_name = "Today" if i == 0 else ("Tomorrow" if i == 1 else day_names_map[dt_obj.weekday()])
            astro = day.get("astro", {})

            daily_list.append(DailyItem(
                date=d_date,
                day_name=day_name,
                temp_max=round(d_raw.get("maxtemp_c", 28.0), 1),
                temp_min=round(d_raw.get("mintemp_c", 20.0), 1),
                rain_probability=int(d_raw.get("daily_chance_of_rain", 0)),
                precipitation_sum=round(d_raw.get("totalprecip_mm", 0.0), 1),
                humidity_avg=int(d_raw.get("avghumidity", 65)),
                wind_speed_max=round(d_raw.get("maxwind_kph", 15.0), 1),
                wind_direction="N",
                uv_index_max=round(d_raw.get("uv", 5.0), 1),
                weather_condition=d_raw.get("condition", {}).get("text", "Clear"),
                weather_icon="partly_cloudy_day",
                weather_code=d_raw.get("condition", {}).get("code", 1000),
                sunrise=astro.get("sunrise", "06:00 AM"),
                sunset=astro.get("sunset", "06:00 PM")
            ))

            if i == 0:
                for h in day.get("hour", [])[:24]:
                    t_str = h.get("time", "").split(" ")[-1]
                    hourly_list.append(HourlyItem(
                        time=t_str,
                        full_time=h.get("time", ""),
                        temperature=round(h.get("temp_c", 25.0), 1),
                        feels_like=round(h.get("feelslike_c", 25.0), 1),
                        humidity=int(h.get("humidity", 60)),
                        rain_probability=int(h.get("chance_of_rain", 0)),
                        precipitation=round(h.get("precip_mm", 0.0), 1),
                        wind_speed=round(h.get("wind_kph", 10.0), 1),
                        uv_index=round(h.get("uv", 0.0), 1),
                        weather_condition=h.get("condition", {}).get("text", "Clear"),
                        weather_icon="partly_cloudy_day",
                        weather_code=h.get("condition", {}).get("code", 1000)
                    ))

        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            provider=self.name,
            current=current_weather,
            hourly=hourly_list,
            daily=daily_list,
            fetched_at=now_iso
        )
