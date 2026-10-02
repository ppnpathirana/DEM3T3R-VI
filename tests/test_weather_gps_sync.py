"""
@file: test_weather_gps_sync.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Tests for GPS coordinate synchronization, exact location tracking, and location-dependent UV Index and Humidity.
"""
import pytest
import time
from backend.weather.service import WeatherService


def test_weather_service_initial_gps():
    service = WeatherService()
    gps = service.get_current_gps()
    assert "latitude" in gps
    assert "longitude" in gps
    assert gps["is_fixed"] is True


def test_weather_service_update_gps_movement():
    service = WeatherService()
    # Initial update
    service.update_gps(6.9271, 79.8612, alt=15.0)
    time.sleep(0.1)
    
    # Large movement (> 10m)
    service.update_gps(6.9350, 79.8700, alt=18.0)
    gps2 = service.get_current_gps()
    assert gps2["latitude"] == 6.9350
    assert gps2["longitude"] == 79.8700
    assert gps2["altitude"] == 18.0


def test_dynamic_synthetic_uv_and_humidity():
    service = WeatherService()
    # Baseline for Peradeniya (7.26°N, 80.59°E)
    weather = service._generate_synthetic_baseline(7.2600, 80.5900)
    
    assert weather["latitude"] == 7.2600
    assert weather["longitude"] == 80.5900
    curr = weather["current"]
    assert "uv_index" in curr
    assert "humidity" in curr
    assert 0.0 <= curr["uv_index"] <= 15.0
    assert 30 <= curr["humidity"] <= 100
    assert "7.26" in weather["location_name"]


def test_haversine_distance():
    from backend.weather.service import haversine_distance_meters
    # Distance between Colombo and Kandy is ~95 km
    dist = haversine_distance_meters(6.9271, 79.8612, 7.2906, 80.6337)
    assert 90000 <= dist <= 105000
