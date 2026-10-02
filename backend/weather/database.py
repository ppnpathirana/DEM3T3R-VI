"""
@file: database.py
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
DEMETER Weather Intelligence System - Database Storage Module
==============================================================================
Persistent storage for weather observations and forecasts (SQLite / PostgreSQL).
==============================================================================
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "weather_history.db")

class WeatherDatabase:
    """Stores weather observations and 7-day forecast records."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    def _init_db(self):
        """Creates tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Weather Observations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                robot_id TEXT DEFAULT 'DEMETER-01',
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                temperature REAL,
                humidity INTEGER,
                pressure REAL,
                rain_probability INTEGER,
                precipitation REAL,
                wind_speed REAL,
                wind_direction TEXT,
                uv_index REAL,
                cloud_cover INTEGER,
                visibility REAL,
                weather_condition TEXT,
                timestamp TEXT NOT NULL
            )
            """)

            # 2. Weather Forecasts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                robot_id TEXT DEFAULT 'DEMETER-01',
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                forecast_date TEXT NOT NULL,
                temperature_max REAL,
                temperature_min REAL,
                rain_probability INTEGER,
                precipitation REAL,
                humidity INTEGER,
                wind_speed REAL,
                uv_index REAL,
                weather_condition TEXT,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()

    def save_observation(self, lat: float, lon: float, curr: Any, robot_id: str = "DEMETER-01"):
        """Saves current weather reading."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO weather_observations (
                    robot_id, latitude, longitude, temperature, humidity, pressure,
                    rain_probability, precipitation, wind_speed, wind_direction,
                    uv_index, cloud_cover, visibility, weather_condition, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    robot_id, lat, lon, curr.temperature, curr.humidity, curr.pressure,
                    curr.rain_probability, curr.precipitation, curr.wind_speed, curr.wind_direction_cardinal,
                    curr.uv_index, curr.cloud_cover, curr.visibility, curr.weather_condition,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            print(f"[WEATHER DB] Save observation error: {e}")

    def save_forecasts(self, lat: float, lon: float, daily_list: List[Any], robot_id: str = "DEMETER-01"):
        """Saves 7-day forecast records."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now().isoformat()
                for item in daily_list:
                    cursor.execute("""
                    INSERT INTO weather_forecasts (
                        robot_id, latitude, longitude, forecast_date, temperature_max,
                        temperature_min, rain_probability, precipitation, humidity,
                        wind_speed, uv_index, weather_condition, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        robot_id, lat, lon, item.date, item.temp_max, item.temp_min,
                        item.rain_probability, item.precipitation_sum, item.humidity_avg,
                        item.wind_speed_max, item.uv_index_max, item.weather_condition, now_str
                    ))
                conn.commit()
        except Exception as e:
            print(f"[WEATHER DB] Save forecasts error: {e}")

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches recent observation rows."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM weather_observations ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[WEATHER DB] Query error: {e}")
            return []
