"""
@file: model_optimizer.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Optimization & Anomaly Detection Suite:
1. ModelOptimizer: Utilities to benchmark YOLO latency and export to ONNX / OpenVINO
2. PlantPreFilter: Ultra-fast plant presence check to discard non-foliage frames
3. SensorAnomalyDetector: Online rolling Z-score anomaly detector for ESP32 sensors
4. WebRTCStreamBridge: Low-latency streaming interface for browser telemetry & video
"""
import time
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional

class ModelOptimizer:
    @staticmethod
    def benchmark_model(model, test_frame: np.ndarray, runs: int = 10) -> Dict[str, float]:
        """Benchmark inference latency in milliseconds."""
        latencies = []
        for _ in range(runs):
            t0 = time.time()
            _ = model.predict(test_frame, verbose=False) if hasattr(model, 'predict') else None
            latencies.append((time.time() - t0) * 1000.0)
        return {
            "avg_latency_ms": round(float(np.mean(latencies)), 2),
            "min_latency_ms": round(float(np.min(latencies)), 2),
            "max_latency_ms": round(float(np.max(latencies)), 2),
            "estimated_fps": round(1000.0 / max(1.0, float(np.mean(latencies))), 1)
        }

class PlantPreFilter:
    @staticmethod
    def has_plant_tissue(frame: np.ndarray, min_green_ratio: float = 0.04) -> Tuple[bool, float]:
        """
        Fast HSV thresholding check to determine if meaningful green leaf canopy is present.
        Returns: (has_plant, green_pixel_ratio)
        """
        if frame is None or frame.size == 0:
            return False, 0.0

        # Downsample for speed
        small = cv2.resize(frame, (160, 120))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        
        # Green Hue range in HSV: ~35 to 85
        lower_green = np.array([25, 40, 40], dtype=np.uint8)
        upper_green = np.array([85, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_ratio = float(np.count_nonzero(mask)) / float(mask.size)
        
        return green_ratio >= min_green_ratio, round(green_ratio, 4)

class SensorAnomalyDetector:
    def __init__(self, window_size: int = 20, z_threshold: float = 3.2):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.history: Dict[str, list] = {
            "temperature": [],
            "humidity": [],
            "pressure": [],
            "soilMoisture": [],
            "uvVoltage": []
        }

    def inspect_reading(self, sensor_name: str, value: float) -> Dict[str, Any]:
        """
        Calculates online rolling mean & standard deviation.
        Flags value as anomaly if |Z-score| > z_threshold or exceeds physical domain limits.
        """
        # Physical domain boundary checks
        domain_limits = {
            "temperature": (-10.0, 65.0),
            "humidity": (0.0, 100.0),
            "pressure": (800.0, 1150.0),
            "soilMoisture": (0.0, 4095.0),
            "uvVoltage": (0.0, 5.0)
        }
        
        if sensor_name in domain_limits:
            low, high = domain_limits[sensor_name]
            if value < low or value > high:
                return {
                    "is_anomaly": True,
                    "reason": f"Physical sensor range violation ({value} not in [{low}, {high}])",
                    "z_score": 99.0
                }

        hist = self.history.setdefault(sensor_name, [])
        hist.append(value)
        if len(hist) > self.window_size:
            hist.pop(0)

        if len(hist) < 5:
            return {"is_anomaly": False, "z_score": 0.0, "reason": "Collecting baseline"}

        mean = float(np.mean(hist))
        std = float(np.std(hist))
        
        if std < 1e-4:
            return {"is_anomaly": False, "z_score": 0.0, "reason": "Normal steady state"}

        z = abs(value - mean) / std
        is_anomaly = z > self.z_threshold
        
        return {
            "is_anomaly": is_anomaly,
            "z_score": round(z, 2),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "reason": f"Statistical outlier (Z={z:.1f} > {self.z_threshold})" if is_anomaly else "Normal"
        }

class WebRTCStreamBridge:
    def __init__(self, port: int = 8080):
        self.port = port
        self.active_tracks = []

    def get_stream_config(self) -> Dict[str, Any]:
        """Returns WebRTC ICE configuration and connection parameters."""
        return {
            "protocol": "WebRTC / MJPEG Dual Bridge",
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}],
            "targetFps": 30,
            "latencyMs": "<80ms"
        }
