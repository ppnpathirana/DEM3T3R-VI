"""
@file: position_estimator.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Extended Kalman Filter (EKF) Position Estimator & Dual-Source Sensor Fusion for DEM3T3R V1 Robot.
Fuses:
1. Rover Hardware GPS Module (UART / NMEA from ESP32 - HDOP, Satellites, RTK fix)
2. Laptop Ground Control Station (GCS) Geolocation (High-Accuracy Browser Geolocation API)
3. Compass / Gyroscope Heading (radians)
4. Wheel Encoders / Velocity (m/s)
5. Ultrasonic Obstacle Range (m)

State Vector: [x, y, theta, v]
  x:     East position (meters from origin)
  y:     North position (meters from origin)
  theta: Heading angle (radians from East, counter-clockwise)
  v:     Forward velocity (m/s)
"""
import math
import time
import numpy as np
from typing import Dict, Any, Tuple, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass initial bearing from (lat1, lon1) to (lat2, lon2) in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    initial_bearing = math.atan2(y, x)
    return (math.degrees(initial_bearing) + 360.0) % 360.0


def lat_lon_to_local_xy(lat: float, lon: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """Convert WGS84 GPS to local tangent plane (East, North) in meters."""
    R = 6371000.0
    dlat = math.radians(lat - origin_lat)
    dlon = math.radians(lon - origin_lon)
    lat_avg = math.radians((lat + origin_lat) / 2.0)
    
    x = dlon * math.cos(lat_avg) * R  # East
    y = dlat * R                      # North
    return x, y


def local_xy_to_lat_lon(x: float, y: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """Convert local (East, North) in meters back to WGS84 GPS."""
    R = 6371000.0
    lat_avg = math.radians(origin_lat)
    dlat = math.degrees(y / R)
    dlon = math.degrees(x / (R * math.cos(lat_avg)))
    return origin_lat + dlat, origin_lon + dlon


class PositionEstimator:
    def __init__(self, origin_lat: float = 6.9271, origin_lon: float = 79.8612):
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        
        # State vector: [x, y, theta, v]^T
        self.x = np.zeros((4, 1), dtype=float)
        
        # State covariance matrix P
        self.P = np.diag([10.0, 10.0, 1.0, 1.0])
        
        # Process noise covariance Q
        self.Q = np.diag([0.1, 0.1, 0.05, 0.2])
        
        # Default measurement noise R_gps (approx 2.5m standard deviation)
        self.R_gps = np.diag([6.25, 6.25])
        
        # Heading measurement noise R_heading (approx 3 degrees)
        self.R_heading = np.array([[0.003]])
        
        self.last_update_time = time.time()
        self.latest_ultrasonic_m = 9.99
        self.gps_fix_count = 0
        
        # Dual-source tracking metadata
        self.fusion_mode = 'FUSED_DUAL'  # 'FUSED_DUAL' | 'ROVER_GPS_ONLY' | 'LAPTOP_GCS_ONLY'
        self.last_rover_gps: Optional[Dict[str, Any]] = None
        self.last_laptop_gps: Optional[Dict[str, Any]] = None
        self.laptop_update_count = 0

    def predict(self, dt: float):
        """EKF Prediction step using non-linear kinematics model."""
        if dt <= 0.0 or dt > 5.0:
            dt = 0.1
            
        x, y, theta, v = self.x[0, 0], self.x[1, 0], self.x[2, 0], self.x[3, 0]
        
        x_next = x + v * math.cos(theta) * dt
        y_next = y + v * math.sin(theta) * dt
        theta_next = (theta + math.pi) % (2.0 * math.pi) - math.pi
        v_next = v
        
        self.x = np.array([[x_next], [y_next], [theta_next], [v_next]], dtype=float)
        
        # Jacobian of f(x) with respect to x: F_k
        F = np.eye(4, dtype=float)
        F[0, 2] = -v * math.sin(theta) * dt
        F[0, 3] = math.cos(theta) * dt
        F[1, 2] = v * math.cos(theta) * dt
        F[1, 3] = math.sin(theta) * dt
        
        # Predict covariance: P_k|k-1 = F * P * F^T + Q
        self.P = F @ self.P @ F.T + self.Q * dt

    def _ekf_measurement_update(self, z_x: float, z_y: float, R_cov: np.ndarray):
        """Internal generic 2D position measurement update for EKF."""
        z = np.array([[z_x], [z_y]], dtype=float)
        H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=float)
        
        # Innovation: y = z - H * x
        hx = H @ self.x
        y_innov = z - hx
        
        # Innovation covariance: S = H * P * H^T + R
        S = H @ self.P @ H.T + R_cov
        
        # Kalman Gain: K = P * H^T * S^-1
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # Update state and covariance
        self.x = self.x + K @ y_innov
        self.P = (np.eye(4) - K @ H) @ self.P

    def update_gps(self, lat: float, lon: float, timestamp: Optional[float] = None):
        """Standard backwards-compatible GPS measurement update."""
        self.update_rover_gps(lat, lon, hdop=1.0, satellites=8, fix_type=1, timestamp=timestamp)

    def update_rover_gps(
        self,
        lat: float,
        lon: float,
        hdop: float = 1.0,
        satellites: int = 8,
        fix_type: int = 1,
        timestamp: Optional[float] = None
    ):
        """
        EKF measurement update with hardware Rover GPS module.
        Adjusts measurement noise R dynamically based on HDOP and RTK fix type.
        """
        now = timestamp or time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        self.predict(dt)
        
        # Record rover telemetry
        self.last_rover_gps = {
            "latitude": lat,
            "longitude": lon,
            "hdop": hdop,
            "satellites": satellites,
            "fix_type": fix_type,
            "timestamp": now
        }
        self.gps_fix_count += 1
        
        # Determine Rover GPS measurement variance sigma^2
        if fix_type >= 4:  # RTK Fixed
            sigma = 0.05
        elif fix_type == 2:  # DGPS / RTK Float
            sigma = 0.5
        else:  # Standard GNSS
            sigma = max(0.8, hdop * 2.0)
            if satellites < 6:
                sigma *= 1.5
                
        R_rover = np.diag([sigma**2, sigma**2])
        
        # If rover GPS is part of current mode, update filter
        if self.fusion_mode in ('FUSED_DUAL', 'ROVER_GPS_ONLY'):
            z_x, z_y = lat_lon_to_local_xy(lat, lon, self.origin_lat, self.origin_lon)
            self._ekf_measurement_update(z_x, z_y, R_rover)

    def update_laptop_gps(
        self,
        lat: float,
        lon: float,
        accuracy_m: float = 5.0,
        altitude: float = 15.0,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
        timestamp: Optional[float] = None
    ):
        """
        EKF measurement update with Laptop/GCS High-Accuracy Geolocation.
        Adjusts measurement noise R based on browser geolocation accuracy radius.
        """
        now = timestamp or time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        self.predict(dt)
        
        # Record laptop telemetry
        self.last_laptop_gps = {
            "latitude": lat,
            "longitude": lon,
            "accuracy_m": max(0.5, float(accuracy_m)),
            "altitude": float(altitude or 15.0),
            "heading": float(heading) if heading is not None else None,
            "speed": float(speed) if speed is not None else None,
            "timestamp": now
        }
        self.laptop_update_count += 1
        
        # If heading is available from laptop motion, update heading
        if heading is not None and speed is not None and speed > 0.5:
            self.update_heading_and_velocity(heading, speed, timestamp=now)
            
        # Measurement variance from laptop accuracy (95% confidence radius -> 2*sigma)
        sigma = max(0.5, float(accuracy_m) / 2.0)
        R_laptop = np.diag([sigma**2, sigma**2])
        
        # If laptop GPS is part of current mode, update filter
        if self.fusion_mode in ('FUSED_DUAL', 'LAPTOP_GCS_ONLY'):
            z_x, z_y = lat_lon_to_local_xy(lat, lon, self.origin_lat, self.origin_lon)
            self._ekf_measurement_update(z_x, z_y, R_laptop)

    def set_fusion_mode(self, mode: str) -> str:
        """Switch between 'FUSED_DUAL', 'ROVER_GPS_ONLY', 'LAPTOP_GCS_ONLY'."""
        if mode in ('FUSED_DUAL', 'ROVER_GPS_ONLY', 'LAPTOP_GCS_ONLY'):
            self.fusion_mode = mode
        return self.fusion_mode

    def update_heading_and_velocity(self, heading_deg: float, velocity_ms: float, timestamp: Optional[float] = None):
        """EKF measurement update with heading sensor & wheel encoders."""
        now = timestamp or time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        self.predict(dt)
        
        heading_rad = math.radians(heading_deg)
        heading_rad = (heading_rad + math.pi) % (2.0 * math.pi) - math.pi
        
        z = np.array([[heading_rad]], dtype=float)
        H = np.array([[0.0, 0.0, 1.0, 0.0]], dtype=float)
        
        y_innov = z - H @ self.x
        y_innov[0, 0] = (y_innov[0, 0] + math.pi) % (2.0 * math.pi) - math.pi
        
        S = H @ self.P @ H.T + self.R_heading
        K = self.P @ H.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y_innov
        self.x[3, 0] = 0.8 * self.x[3, 0] + 0.2 * velocity_ms
        self.P = (np.eye(4) - K @ H) @ self.P

    def update_ultrasonic(self, distance_cm: float):
        """Record ultrasonic obstacle distance in meters."""
        self.latest_ultrasonic_m = max(0.01, distance_cm / 100.0)

    def get_baseline_vector(self) -> Optional[Dict[str, Any]]:
        """Calculate vector (distance & bearing) between Laptop GCS and Rover."""
        if not self.last_laptop_gps or not self.last_rover_gps:
            return None
            
        lap_lat = self.last_laptop_gps["latitude"]
        lap_lon = self.last_laptop_gps["longitude"]
        rov_lat = self.last_rover_gps["latitude"]
        rov_lon = self.last_rover_gps["longitude"]
        
        dist_m = haversine_distance(lap_lat, lap_lon, rov_lat, rov_lon)
        bearing_deg = calculate_bearing(lap_lat, lap_lon, rov_lat, rov_lon)
        
        return {
            "distance_m": round(dist_m, 2),
            "bearing_deg": round(bearing_deg, 1),
            "laptop_to_rover_vector": f"{round(dist_m, 1)}m @ {round(bearing_deg, 0)}°"
        }

    def get_pose(self) -> Dict[str, Any]:
        """Return smoothed robot pose and position estimate."""
        x = float(self.x[0, 0])
        y = float(self.x[1, 0])
        theta_rad = float(self.x[2, 0])
        theta_deg = math.degrees(theta_rad) % 360.0
        v = float(self.x[3, 0])
        
        # Uncertainty metric (trace of position covariance submatrix)
        pos_uncertainty = float(math.sqrt(max(0.01, self.P[0, 0] + self.P[1, 1])))
        
        current_lat, current_lon = local_xy_to_lat_lon(x, y, self.origin_lat, self.origin_lon)
        
        baseline = self.get_baseline_vector()
        
        return {
            "x_local_m": round(x, 3),
            "y_local_m": round(y, 3),
            "latitude": round(current_lat, 7),
            "longitude": round(current_lon, 7),
            "heading_deg": round(theta_deg, 2),
            "heading_rad": round(theta_rad, 4),
            "velocity_ms": round(v, 2),
            "uncertainty_m": round(pos_uncertainty, 2),
            "ultrasonic_obstacle_m": round(self.latest_ultrasonic_m, 2),
            "gps_fixes": self.gps_fix_count,
            "laptop_updates": self.laptop_update_count,
            "fusion_mode": self.fusion_mode,
            "last_rover_gps": self.last_rover_gps,
            "last_laptop_gps": self.last_laptop_gps,
            "baseline": baseline
        }
