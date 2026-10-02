"""
Coverage-Path Planning & Waypoint Navigation for CropGuard.
Calculates complete agricultural coverage trajectories (Boustrophedon / lawnmower pattern)
for a given field boundary polygon and outputs GPS waypoints for autonomous navigation.
"""
import math
from typing import List, Tuple, Dict, Any, Optional
from shapely.geometry import Polygon, LineString, Point
from backend.position_estimator import haversine_distance, lat_lon_to_local_xy, local_xy_to_lat_lon

class CoveragePlanner:
    def __init__(self, row_spacing_m: float = 0.8, robot_width_m: float = 0.4, overlap_m: float = 0.1):
        """
        Args:
            row_spacing_m: Distance between parallel patrol rows in meters.
            robot_width_m: Physical width of DEM3T3R V1 robot chassis.
            overlap_m: Swath overlap to prevent uninspected strip gaps.
        """
        self.effective_spacing = max(0.2, row_spacing_m - overlap_m)
        self.robot_width = robot_width_m

    def plan_field(self, boundary_gps: List[Tuple[float, float]], sweep_angle_deg: float = 0.0) -> List[Tuple[float, float]]:
        """
        Takes a list of (latitude, longitude) boundary vertices.
        Generates a sequence of (lat, lon) waypoints covering the entire area.
        """
        if len(boundary_gps) < 3:
            return boundary_gps

        origin_lat, origin_lon = boundary_gps[0]
        
        # 1. Convert GPS polygon to local metric (x, y) coordinates
        local_pts = [lat_lon_to_local_xy(lat, lon, origin_lat, origin_lon) for lat, lon in boundary_gps]
        poly = Polygon(local_pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
            
        min_x, min_y, max_x, max_y = poly.bounds
        
        # 2. Generate parallel sweep lines across bounding box
        waypoints_local: List[Tuple[float, float]] = []
        y_curr = min_y + self.effective_spacing / 2.0
        reverse_direction = False
        
        while y_curr <= max_y:
            sweep_line = LineString([(min_x - 5.0, y_curr), (max_x + 5.0, y_curr)])
            intersection = poly.intersection(sweep_line)
            
            if not intersection.is_empty:
                if intersection.geom_type == 'LineString':
                    coords = list(intersection.coords)
                    if reverse_direction:
                        coords.reverse()
                    waypoints_local.extend(coords)
                    reverse_direction = not reverse_direction
                elif intersection.geom_type == 'MultiLineString':
                    lines = list(intersection.geoms)
                    if reverse_direction:
                        lines.reverse()
                    for line in lines:
                        coords = list(line.coords)
                        if reverse_direction:
                            coords.reverse()
                        waypoints_local.extend(coords)
                    reverse_direction = not reverse_direction
                    
            y_curr += self.effective_spacing

        # 3. Convert back to GPS (lat, lon) waypoints
        waypoints_gps: List[Tuple[float, float]] = []
        for x, y in waypoints_local:
            lat, lon = local_xy_to_lat_lon(x, y, origin_lat, origin_lon)
            waypoints_gps.append((round(lat, 7), round(lon, 7)))
            
        return waypoints_gps

    def estimate_coverage_time_sec(self, waypoints: List[Tuple[float, float]], robot_speed_ms: float = 0.4) -> float:
        """Estimate total travel and inspection time in seconds."""
        if len(waypoints) < 2:
            return 0.0
        total_dist = 0.0
        for i in range(len(waypoints) - 1):
            total_dist += haversine_distance(waypoints[i][0], waypoints[i][1], waypoints[i+1][0], waypoints[i+1][1])
        return round(total_dist / max(0.1, robot_speed_ms), 1)

class WaypointNavigator:
    def __init__(self, waypoints: List[Tuple[float, float]], arrival_radius_m: float = 1.2):
        self.waypoints = waypoints
        self.current_idx = 0
        self.arrival_radius_m = arrival_radius_m
        self.completed = False

    def update_position(self, current_lat: float, current_lon: float) -> Dict[str, Any]:
        """
        Updates robot's current GPS position and checks waypoint progression.
        Returns guidance info for ESP32 motor controller.
        """
        if not self.waypoints or self.completed:
            return {
                "current_waypoint_idx": self.current_idx,
                "total_waypoints": len(self.waypoints),
                "target_lat": 0.0,
                "target_lon": 0.0,
                "distance_to_target_m": 0.0,
                "bearing_to_target_deg": 0.0,
                "coverage_pct": 100.0,
                "completed": True,
                "esp32_cmd": "NAV_STOP"
            }

        target_lat, target_lon = self.waypoints[self.current_idx]
        dist = haversine_distance(current_lat, current_lon, target_lat, target_lon)
        
        # Calculate true bearing from current pos to target
        lat1, lon1 = math.radians(current_lat), math.radians(current_lon)
        lat2, lon2 = math.radians(target_lat), math.radians(target_lon)
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing_deg = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

        # Check if arrived within radius
        if dist <= self.arrival_radius_m:
            self.current_idx += 1
            if self.current_idx >= len(self.waypoints):
                self.completed = True
                return {
                    "current_waypoint_idx": len(self.waypoints),
                    "total_waypoints": len(self.waypoints),
                    "target_lat": target_lat,
                    "target_lon": target_lon,
                    "distance_to_target_m": 0.0,
                    "bearing_to_target_deg": 0.0,
                    "coverage_pct": 100.0,
                    "completed": True,
                    "esp32_cmd": "NAV_COMPLETE"
                }

        coverage_pct = round((self.current_idx / max(1, len(self.waypoints))) * 100.0, 1)
        esp32_cmd = f"GOTO {target_lat:.6f} {target_lon:.6f} {dist:.1f}m"

        return {
            "current_waypoint_idx": self.current_idx,
            "total_waypoints": len(self.waypoints),
            "target_lat": target_lat,
            "target_lon": target_lon,
            "distance_to_target_m": round(dist, 2),
            "bearing_to_target_deg": round(bearing_deg, 1),
            "coverage_pct": coverage_pct,
            "completed": False,
            "esp32_cmd": esp32_cmd
        }
