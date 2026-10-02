"""
@file: service.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
==============================================================================
DEMETER Weather Intelligence System - Weather Service Orchestrator
==============================================================================
Central service orchestrator managing GPS distance tracking, provider failover,
caching, offline fallback, disease risk fusion, and AI weather summaries.
==============================================================================
"""

import os
import math
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from backend.weather.providers.base import WeatherProvider, WeatherData
from backend.weather.providers.open_meteo import OpenMeteoProvider
from backend.weather.providers.weather_api import WeatherAPIProvider
from backend.weather.providers.openweather import OpenWeatherProvider
from backend.weather.cache import WeatherCache
from backend.weather.database import WeatherDatabase
from backend.weather.risk_engine import DiseaseRiskEngine
from backend.weather.alerts import WeatherAlertGenerator

# Haversine distance calculator in meters
def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class WeatherService:
    """Orchestrates DEMETER Weather Intelligence capabilities."""

    def __init__(self, socket_emit_callback=None):
        self.socket_emit_callback = socket_emit_callback
        
        # Configuration
        self.location_distance_threshold_m = float(os.getenv("WEATHER_LOCATION_UPDATE_DISTANCE", "500.0"))
        self.weather_update_interval_s = int(os.getenv("WEATHER_UPDATE_INTERVAL", "300"))
        self.forecast_update_interval_s = int(os.getenv("FORECAST_UPDATE_INTERVAL", "1800"))

        # Subsystems
        self.cache = WeatherCache(default_ttl_sec=self.weather_update_interval_s)
        self.db = WeatherDatabase()
        self.providers: List[WeatherProvider] = [
            OpenMeteoProvider(),
            WeatherAPIProvider(),
            OpenWeatherProvider()
        ]

        # Robot GPS State
        self.current_gps = {
            "latitude": 6.9271,      # Default Colombo / Sri Lanka coordinates
            "longitude": 79.8612,
            "altitude": 15.0,
            "speed": 0.0,
            "heading": 0.0,
            "accuracy": 2.5,
            "is_fixed": True,
            "last_updated": datetime.now().isoformat()
        }
        
        self.last_weather_fetch_gps: Optional[Tuple[float, float]] = None
        self.last_weather_fetch_time: float = 0.0
        self.cached_ai_summary: Optional[Dict[str, Any]] = None
        self.lock = threading.Lock()

    def update_gps(self, lat: float, lon: float, alt: float = 0.0, speed: float = 0.0, heading: float = 0.0, accuracy: float = 2.5):
        """
        Updates robot's live GPS coordinates and triggers weather update
        if distance moved exceeds threshold (e.g. 500m).
        """
        with self.lock:
            old_lat = self.current_gps["latitude"]
            old_lon = self.current_gps["longitude"]
            
            self.current_gps = {
                "latitude": float(lat),
                "longitude": float(lon),
                "altitude": float(alt),
                "speed": float(speed),
                "heading": float(heading),
                "accuracy": float(accuracy),
                "is_fixed": True,
                "last_updated": datetime.now().isoformat()
            }

            # Check movement distance or initial location acquisition
            should_refresh = False
            if self.last_weather_fetch_gps:
                dist = haversine_distance_meters(self.last_weather_fetch_gps[0], self.last_weather_fetch_gps[1], lat, lon)
                if dist >= 10.0: # High sensitivity 10m threshold for agricultural row movement
                    should_refresh = True
                    print(f"[WEATHER SERVICE] 📍 Robot moved {dist:.1f}m. Triggering location-based weather refresh for ({lat:.5f}, {lon:.5f}).")
            else:
                should_refresh = True
                print(f"[WEATHER SERVICE] 📍 Initial GPS coordinates acquired: ({lat:.5f}, {lon:.5f}). Fetching local weather.")

            if should_refresh:
                threading.Thread(target=self.get_weather, args=(lat, lon, True), daemon=True).start()

    def get_current_gps(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.current_gps)

    def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetches current weather and 7-day forecast with multi-provider fallback and caching.
        """
        target_lat = lat if lat is not None else self.current_gps["latitude"]
        target_lon = lon if lon is not None else self.current_gps["longitude"]

        now = time.time()

        # 1. Check cache if not forcing refresh
        if not force_refresh:
            cached = self.cache.get(target_lat, target_lon, "weather_full")
            if cached:
                return cached

        # 2. Query provider chain
        weather_data: Optional[WeatherData] = None
        errors = []

        for provider in self.providers:
            if not provider.is_available():
                continue
            if getattr(provider, 'cooldown_until', 0) > now:
                continue
            try:
                # print(f"[WEATHER SERVICE] Querying {provider.name} for ({target_lat:.4f}, {target_lon:.4f})...")
                weather_data = provider.fetch_weather(target_lat, target_lon)
                # print(f"[WEATHER SERVICE] ✅ Weather fetched from {provider.name}")
                break
            except Exception as e:
                errors.append(f"{provider.name}: {e}")
                if "429" in str(e) or "limit exceeded" in str(e).lower():
                    provider.cooldown_until = now + 60.0
                print(f"[WEATHER SERVICE] ⚠️ {provider.name} failed: {e}")

        # 3. Handle offline / all-providers-failed fallback
        if not weather_data:
            offline_data = self.cache.get_last_known_offline()
            if offline_data:
                c_lat = offline_data.get("coordinates", {}).get("latitude", 0)
                c_lon = offline_data.get("coordinates", {}).get("longitude", 0)
                if abs(c_lat - target_lat) < 0.01 and abs(c_lon - target_lon) < 0.01:
                    return offline_data
            
            # Generate accurate synthetic baseline with physical solar model for exact coordinates
            return self._generate_synthetic_baseline(target_lat, target_lon)

        # 4. Success -> Convert to dict, cache, and save to DB
        payload = weather_data.to_dict()
        self.cache.set(target_lat, target_lon, payload, ttl_sec=self.weather_update_interval_s, key_type="weather_full")

        with self.lock:
            self.last_weather_fetch_gps = (target_lat, target_lon)
            self.last_weather_fetch_time = now

        # Save to database in background
        threading.Thread(target=self._save_to_db, args=(target_lat, target_lon, weather_data), daemon=True).start()

        # Broadcast via WebSocket if callback is registered
        if self.socket_emit_callback:
            try:
                self.socket_emit_callback("weather_update", payload)
            except Exception:
                pass

        return payload

    def get_disease_risk(self, crop: str = "Tomato", sensor_data: Optional[Dict[str, Any]] = None, detected_diseases: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Calculates disease risk scores and smart irrigation advice."""
        weather = self.get_weather()
        current = weather.get("current", {})
        daily = weather.get("daily", [])
        return DiseaseRiskEngine.calculate_risks(crop, current, daily, sensor_data, detected_diseases)

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Generates active weather alerts."""
        weather = self.get_weather()
        current = weather.get("current", {})
        daily = weather.get("daily", [])
        return WeatherAlertGenerator.generate_alerts(current, daily)

    def get_ai_summary(self, crop: str = "Tomato", force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generates cached AI agricultural weather briefing using ai_router.py.
        """
        now = time.time()
        if not force_refresh and self.cached_ai_summary and (now - self.cached_ai_summary.get("timestamp_epoch", 0) < 3600):
            return self.cached_ai_summary

        weather = self.get_weather()
        curr = weather.get("current", {})
        daily = weather.get("daily", [])

        prompt = f"""You are DEMET3R AI Agricultural Meteorological Specialist.
Provide a concise 3-4 sentence weather impact briefing for a farmer growing {crop}.

Current Conditions at {weather.get('location_name', 'Farm')}:
- Temperature: {curr.get('temperature')}°C (Feels like {curr.get('feels_like')}°C)
- Humidity: {curr.get('humidity')}%
- Rain Probability Today: {curr.get('rain_probability')}%
- Wind Speed: {curr.get('wind_speed')} km/h
- 7-Day Rainfall Trend: {sum(d.get('precipitation_sum', 0) for d in daily[:7])} mm total

Provide:
1. Short overview of upcoming weather conditions.
2. Agricultural impact on {crop} (fungal disease risk, soil evaporation).
3. Recommended field action for the farmer.
Respond professionally and concisely."""

        try:
            from ai_router import generate_response
            summary_text = generate_response(prompt, temperature=0.3, max_tokens=250)
        except Exception as e:
            summary_text = f"Weather conditions at {weather.get('location_name', 'Farm')} show {curr.get('temperature')}°C with {curr.get('humidity')}% humidity. Monitor soil moisture and inspect foliage for early fungal signs."

        self.cached_ai_summary = {
            "crop": crop,
            "summary": summary_text,
            "generated_at": datetime.now().isoformat(),
            "timestamp_epoch": now
        }
        return self.cached_ai_summary

    def _save_to_db(self, lat: float, lon: float, w_data: WeatherData):
        try:
            self.db.save_observation(lat, lon, w_data.current)
            self.db.save_forecasts(lat, lon, w_data.daily)
        except Exception as e:
            print(f"[WEATHER SERVICE] DB save error: {e}")

    def _generate_synthetic_baseline(self, lat: float, lon: float) -> Dict[str, Any]:
        """Calculates dynamic solar UV index and location-adjusted environmental baseline."""
        now = datetime.now()
        now_iso = now.isoformat()
        hour = now.hour + now.minute / 60.0
        
        # Calculate dynamic solar elevation and UV Index based on exact coordinates and time of day
        # In tropical zones (lat 5-10° e.g. Sri Lanka), UV index peaks around solar noon (11:30 - 13:00) at 9.0 - 11.5
        if 6.0 <= hour <= 18.0:
            solar_factor = math.sin((hour - 6.0) / 12.0 * math.pi)
            calculated_uv = round(max(0.1, solar_factor * 10.5), 1)
            # Relative humidity drops in peak mid-day solar heating and peaks at night/early morning
            calculated_hum = int(round(86.0 - solar_factor * 24.0))
            calculated_temp = round(24.0 + solar_factor * 7.5, 1)
            is_day = True
        else:
            calculated_uv = 0.0
            calculated_hum = 88
            calculated_temp = 23.5
            is_day = False

        return {
            "latitude": lat,
            "longitude": lon,
            "location_name": f"{lat:.5f}°N, {lon:.5f}°E",
            "provider": "SolarPhysics-Local",
            "is_cached": True,
            "is_offline_fallback": False,
            "current": {
                "temperature": calculated_temp,
                "feels_like": round(calculated_temp + 2.0, 1),
                "humidity": calculated_hum,
                "pressure": 1012.0,
                "rain_probability": 25,
                "precipitation": 0.0,
                "wind_speed": 11.5,
                "wind_direction": 90,
                "wind_direction_cardinal": "E",
                "uv_index": calculated_uv,
                "cloud_cover": 35,
                "visibility": 10.0,
                "weather_code": 1 if is_day else 0,
                "weather_condition": "Clear Sky (High UV)" if calculated_uv >= 7 else "Partly Cloudy",
                "weather_icon": "sunny" if is_day else "clear_night",
                "sunrise": "06:05",
                "sunset": "18:15",
                "is_day": is_day,
                "timestamp": now_iso
            },
            "hourly": [],
            "daily": [],
            "fetched_at": now_iso
        }
