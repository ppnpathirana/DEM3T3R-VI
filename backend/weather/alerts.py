"""
@file: alerts.py
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
DEMETER Weather Intelligence System - Weather Alerts Module
==============================================================================
Generates real-time actionable agricultural weather warnings and alerts.
==============================================================================
"""

from typing import List, Dict, Any

class WeatherAlertGenerator:
    """Evaluates weather telemetry and generates prioritized warning alerts."""

    @staticmethod
    def generate_alerts(current: Dict[str, Any], daily: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alerts = []

        temp = current.get("temperature", 25.0)
        humidity = current.get("humidity", 60)
        wind_speed = current.get("wind_speed", 10.0)
        uv_index = current.get("uv_index", 5.0)
        rain_prob = current.get("rain_probability", 0)
        precip = current.get("precipitation", 0.0)

        # 1. Heavy Rain Warning
        if rain_prob >= 75 or precip >= 15.0:
            alerts.append({
                "id": "alert_heavy_rain",
                "severity": "CRITICAL" if (rain_prob >= 85 or precip >= 30.0) else "WARNING",
                "type": "RAIN",
                "icon": "rainy_heavy",
                "title": "🌧 Heavy Rain & Saturated Soil Alert",
                "description": f"High probability of rain ({rain_prob}%) with expected precipitation. Ensure drainage channels are clear and postpone all irrigation cycles.",
                "recommendation": "Inspect drainage beds, shield vulnerable seedlings, and avoid overhead spraying."
            })

        # 2. High Temperature / Crop Heat Stress Warning
        if temp >= 33.0:
            alerts.append({
                "id": "alert_heat_stress",
                "severity": "WARNING",
                "type": "HEAT",
                "icon": "thermostat",
                "title": "🔥 High Temperature & Crop Heat Stress",
                "description": f"Ambient temperature reaches {temp}°C. Increased transpiration may cause leaf wilting and accelerated moisture loss.",
                "recommendation": "Monitor root zone soil hydration. Provide shade cloth protection if available."
            })

        # 3. Strong Wind Alert
        if wind_speed >= 35.0:
            alerts.append({
                "id": "alert_strong_wind",
                "severity": "WARNING",
                "type": "WIND",
                "icon": "air",
                "title": "💨 High Wind Velocity Alert",
                "description": f"Wind gusts measured at {wind_speed} km/h. Drone and robotic rover navigation stability may be affected.",
                "recommendation": "Avoid high-precision spray applications due to wind drift. Secure lightweight crop supports."
            })

        # 4. High Humidity Fungal Infection Alert
        if humidity >= 85 and temp >= 20.0:
            alerts.append({
                "id": "alert_fungal_humidity",
                "severity": "INFO",
                "type": "FUNGAL_RISK",
                "icon": "water_drop",
                "title": "💧 Prolonged High Humidity / Fungal Risk",
                "description": f"Relative humidity is {humidity}%. High moisture accelerates fungal spore germination on crop leaves.",
                "recommendation": "Maintain adequate row spacing for ventilation and avoid late evening watering."
            })

        # 5. Extreme UV Alert
        if uv_index >= 9.0:
            alerts.append({
                "id": "alert_extreme_uv",
                "severity": "INFO",
                "type": "UV",
                "icon": "wb_sunny",
                "title": "☀️ Extreme Solar Radiation / UV Index",
                "description": f"Peak solar UV index reaches {uv_index}. Potential sunburn on delicate fruit surfaces.",
                "recommendation": "Ensure adequate soil moisture to reduce solar thermal stress."
            })

        return alerts
