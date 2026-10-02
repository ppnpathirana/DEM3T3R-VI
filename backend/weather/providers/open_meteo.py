"""
@file: open_meteo.py
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
DEMETER Weather Intelligence System - Open-Meteo Provider (Primary)
==============================================================================
Free, keyless, high-resolution global weather provider.
==============================================================================
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.weather.providers.base import (
    WeatherProvider, WeatherData, CurrentWeather, HourlyItem, DailyItem,
    deg_to_cardinal, wmo_code_to_condition
)

class OpenMeteoProvider(WeatherProvider):
    """Primary free weather provider powered by Open-Meteo API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

    @property
    def name(self) -> str:
        return "Open-Meteo"

    def is_available(self) -> bool:
        # Open-Meteo requires no API keys and is always available
        return True

    def _get_location_name(self, lat: float, lon: float) -> str:
        """Reverse geocode or format coordinates."""
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10"
            res = requests.get(url, headers={"User-Agent": "DEMETER-Agricultural-Robot/2.0"}, timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or addr.get("state")
                country = addr.get("country", "")
                if city:
                    return f"{city}, {country}" if country else city
        except Exception:
            pass
        return f"{lat:.4f}°N, {lon:.4f}°E"

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Fetches current conditions, 24-hour hourly, and 7-day daily forecasts."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "rain", "weather_code", "cloud_cover",
                "surface_pressure", "wind_speed_10m", "wind_direction_10m", "uv_index"
            ],
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation_probability", "precipitation", "rain",
                "weather_code", "visibility", "wind_speed_10m", "uv_index"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "apparent_temperature_max", "apparent_temperature_min",
                "sunrise", "sunset", "uv_index_max", "precipitation_sum",
                "rain_sum", "precipitation_probability_max",
                "wind_speed_10m_max", "wind_direction_10m_dominant"
            ],
            "timezone": "auto"
        }

        response = requests.get(self.BASE_URL, params=params, timeout=8.0)
        if response.status_code != 200:
            raise RuntimeError(f"Open-Meteo API error HTTP {response.status_code}: {response.text[:200]}")

        data = response.json()
        now_iso = datetime.now().isoformat()

        # Parse Current
        curr = data.get("current", {})
        w_code = curr.get("weather_code", 0)
        cond_text, cond_icon = wmo_code_to_condition(w_code)
        wind_deg = curr.get("wind_direction_10m", 0)
        
        # Extract sunrise/sunset from first daily entry
        daily_raw = data.get("daily", {})
        sunrises = daily_raw.get("sunrise", ["06:00"])
        sunsets = daily_raw.get("sunset", ["18:00"])
        sunrise_str = sunrises[0].split("T")[-1][:5] if sunrises else "06:00"
        sunset_str = sunsets[0].split("T")[-1][:5] if sunsets else "18:00"

        current_weather = CurrentWeather(
            temperature=round(curr.get("temperature_2m", 25.0), 1),
            feels_like=round(curr.get("apparent_temperature", 25.0), 1),
            humidity=int(curr.get("relative_humidity_2m", 60)),
            pressure=round(curr.get("surface_pressure", 1013.0), 1),
            rain_probability=int(daily_raw.get("precipitation_probability_max", [0])[0] if daily_raw.get("precipitation_probability_max") else 0),
            precipitation=round(curr.get("precipitation", 0.0), 1),
            wind_speed=round(curr.get("wind_speed_10m", 0.0), 1),
            wind_direction=int(wind_deg),
            wind_direction_cardinal=deg_to_cardinal(wind_deg),
            uv_index=round(curr.get("uv_index", 0.0), 1),
            cloud_cover=int(curr.get("cloud_cover", 0)),
            visibility=round(data.get("hourly", {}).get("visibility", [10000])[0] / 1000.0, 1),
            weather_code=w_code,
            weather_condition=cond_text,
            weather_icon=cond_icon,
            sunrise=sunrise_str,
            sunset=sunset_str,
            is_day=bool(curr.get("is_day", 1)),
            timestamp=curr.get("time", now_iso)
        )

        # Parse Hourly (Next 24 hours starting from current hour)
        hourly_list: List[HourlyItem] = []
        h_raw = data.get("hourly", {})
        h_times = h_raw.get("time", [])
        
        # Find current hour index or start at 0
        current_time_str = curr.get("time", "")
        start_idx = 0
        if current_time_str in h_times:
            start_idx = h_times.index(current_time_str)

        for i in range(start_idx, min(start_idx + 24, len(h_times))):
            t_full = h_times[i]
            t_hour = t_full.split("T")[-1][:5]
            code_h = h_raw.get("weather_code", [0])[i] if i < len(h_raw.get("weather_code", [])) else 0
            c_text_h, c_icon_h = wmo_code_to_condition(code_h)
            
            hourly_list.append(HourlyItem(
                time=t_hour,
                full_time=t_full,
                temperature=round(h_raw.get("temperature_2m", [0])[i], 1),
                feels_like=round(h_raw.get("apparent_temperature", [0])[i], 1),
                humidity=int(h_raw.get("relative_humidity_2m", [0])[i]),
                rain_probability=int(h_raw.get("precipitation_probability", [0])[i]),
                precipitation=round(h_raw.get("precipitation", [0])[i], 1),
                wind_speed=round(h_raw.get("wind_speed_10m", [0])[i], 1),
                uv_index=round(h_raw.get("uv_index", [0])[i] if "uv_index" in h_raw else 0.0, 1),
                weather_condition=c_text_h,
                weather_icon=c_icon_h,
                weather_code=code_h
            ))

        # Parse 7-Day Daily Forecast
        daily_list: List[DailyItem] = []
        d_times = daily_raw.get("time", [])
        
        day_names_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for i in range(min(7, len(d_times))):
            d_date = d_times[i]
            dt_obj = datetime.strptime(d_date, "%Y-%m-%d")
            
            if i == 0:
                day_name = "Today"
            elif i == 1:
                day_name = "Tomorrow"
            else:
                day_name = day_names_map[dt_obj.weekday()]

            code_d = daily_raw.get("weather_code", [0])[i]
            c_text_d, c_icon_d = wmo_code_to_condition(code_d)
            wind_deg_d = daily_raw.get("wind_direction_10m_dominant", [0])[i]
            
            # Estimate daily average humidity from hourly values on that day
            h_start = i * 24
            h_end = min((i + 1) * 24, len(h_raw.get("relative_humidity_2m", [])))
            h_slice = h_raw.get("relative_humidity_2m", [])[h_start:h_end]
            avg_hum = int(sum(h_slice) / len(h_slice)) if h_slice else 70

            daily_list.append(DailyItem(
                date=d_date,
                day_name=day_name,
                temp_max=round(daily_raw.get("temperature_2m_max", [28])[i], 1),
                temp_min=round(daily_raw.get("temperature_2m_min", [20])[i], 1),
                rain_probability=int(daily_raw.get("precipitation_probability_max", [0])[i]),
                precipitation_sum=round(daily_raw.get("precipitation_sum", [0])[i], 1),
                humidity_avg=avg_hum,
                wind_speed_max=round(daily_raw.get("wind_speed_10m_max", [0])[i], 1),
                wind_direction=deg_to_cardinal(wind_deg_d),
                uv_index_max=round(daily_raw.get("uv_index_max", [5])[i], 1),
                weather_condition=c_text_d,
                weather_icon=c_icon_d,
                weather_code=code_d,
                sunrise=daily_raw.get("sunrise", ["06:00"])[i].split("T")[-1][:5],
                sunset=daily_raw.get("sunset", ["18:00"])[i].split("T")[-1][:5]
            ))

        location_name = self._get_location_name(latitude, longitude)

        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            provider=self.name,
            current=current_weather,
            hourly=hourly_list,
            daily=daily_list,
            fetched_at=now_iso,
            is_cached=False,
            is_offline_fallback=False
        )
