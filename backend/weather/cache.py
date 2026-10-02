"""
@file: cache.py
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
DEMETER Weather Intelligence System - Cache Module
==============================================================================
Intelligent coordinate-rounded in-memory & Redis caching layer.
==============================================================================
"""

import os
import json
import time
from typing import Optional, Dict, Any

class WeatherCache:
    """
    Coordinates-rounded caching layer supporting in-memory LRU storage
    and optional Redis server connection if available.
    """

    def __init__(self, default_ttl_sec: int = 300):
        self.default_ttl = default_ttl_sec
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.last_valid_data: Optional[Dict[str, Any]] = None
        self.redis_client = None

        # Attempt optional Redis connection
        redis_url = os.getenv("REDIS_URL", "").strip()
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                print("[WEATHER CACHE] ✅ Connected to Redis server.")
            except Exception as e:
                print(f"[WEATHER CACHE] ⚠️ Redis unavailable ({e}), using in-memory store.")
                self.redis_client = None

    def _make_key(self, lat: float, lon: float, key_type: str = "weather") -> str:
        """
        Rounds GPS coordinates to 3 decimal places (~110m grid)
        to prevent minute GPS jitter from duplicating cache entries.
        """
        rounded_lat = round(lat, 3)
        rounded_lon = round(lon, 3)
        return f"{key_type}:{rounded_lat}:{rounded_lon}"

    def get(self, lat: float, lon: float, key_type: str = "weather") -> Optional[Dict[str, Any]]:
        """Retrieves cached weather payload if not expired."""
        key = self._make_key(lat, lon, key_type)

        # 1. Check Redis if active
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    parsed = json.loads(data)
                    parsed["is_cached"] = True
                    return parsed
            except Exception as e:
                print(f"[WEATHER CACHE] Redis get error: {e}")

        # 2. Check Memory Store
        entry = self.memory_store.get(key)
        if entry:
            if time.time() < entry["expires_at"]:
                cached_dict = entry["data"]
                cached_dict["is_cached"] = True
                return cached_dict
            else:
                # Keep last valid data before deleting expired entry
                self.last_valid_data = entry["data"]
                del self.memory_store[key]

        return None

    def set(self, lat: float, lon: float, data: Dict[str, Any], ttl_sec: Optional[int] = None, key_type: str = "weather"):
        """Saves weather payload into cache with TTL."""
        ttl = ttl_sec or self.default_ttl
        key = self._make_key(lat, lon, key_type)
        now = time.time()

        # Update last known valid
        self.last_valid_data = data

        # 1. Save to Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(data))
            except Exception as e:
                print(f"[WEATHER CACHE] Redis set error: {e}")

        # 2. Save to In-Memory store
        self.memory_store[key] = {
            "data": data,
            "saved_at": now,
            "expires_at": now + ttl
        }

    def get_last_known_offline(self) -> Optional[Dict[str, Any]]:
        """
        Returns the last valid weather snapshot when the robot is off-grid / offline.
        Flags data as offline fallback.
        """
        if self.last_valid_data:
            fallback = dict(self.last_valid_data)
            fallback["is_offline_fallback"] = True
            fallback["is_cached"] = True
            return fallback
        return None

    def clear(self):
        """Clears memory and Redis cache."""
        self.memory_store.clear()
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
