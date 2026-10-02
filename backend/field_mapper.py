"""
@file: field_mapper.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Multi-Zone GIS Mission Planner.
Supports:
1. Field boundary polygon definition & validation
2. Obstacle exclusion zones (trees, ponds, rock piles, irrigation junctions)
3. Return-To-Launch (RTL) safe flight/drive path computation
4. Battery & pesticide payload range estimation
"""
import math
from typing import List, Tuple, Dict, Any
from shapely.geometry import Polygon, Point, LineString
from backend.position_estimator import haversine_distance, lat_lon_to_local_xy, local_xy_to_lat_lon

class FieldMissionManager:
    def __init__(self, home_lat: float = 6.92710, home_lon: float = 79.86120):
        self.home_coords = (home_lat, home_lon)
        self.exclusion_zones: List[Polygon] = []
        self.battery_range_meters = 2500.0  # Approx 2.5km on 12V 10Ah LiFePO4

    def add_exclusion_zone(self, obstacle_gps: List[Tuple[float, float]]):
        """Add non-navigable zone (trees, ponds) in GPS coordinates."""
        if len(obstacle_gps) >= 3:
            local_pts = [lat_lon_to_local_xy(lat, lon, self.home_coords[0], self.home_coords[1]) for lat, lon in obstacle_gps]
            poly = Polygon(local_pts)
            if poly.is_valid:
                self.exclusion_zones.append(poly)

    def plan_mission_with_exclusions(
        self,
        boundary_gps: List[Tuple[float, float]],
        row_spacing_m: float = 0.8
    ) -> Dict[str, Any]:
        """
        Plans complete coverage swaths while routing around registered exclusion zones.
        """
        origin_lat, origin_lon = self.home_coords
        local_boundary = [lat_lon_to_local_xy(lat, lon, origin_lat, origin_lon) for lat, lon in boundary_gps]
        field_poly = Polygon(local_boundary)
        if not field_poly.is_valid:
            field_poly = field_poly.buffer(0)

        # Subtract all exclusion zones from field polygon
        navigable_area = field_poly
        for excl in self.exclusion_zones:
            navigable_area = navigable_area.difference(excl)

        min_x, min_y, max_x, max_y = navigable_area.bounds
        waypoints_gps: List[Tuple[float, float]] = []
        
        y_curr = min_y + row_spacing_m / 2.0
        reverse = False
        
        while y_curr <= max_y:
            sweep = LineString([(min_x - 5.0, y_curr), (max_x + 5.0, y_curr)])
            inter = navigable_area.intersection(sweep)
            
            if not inter.is_empty:
                if inter.geom_type == 'LineString':
                    coords = list(inter.coords)
                    if reverse:
                        coords.reverse()
                    for x, y in coords:
                        lat, lon = local_xy_to_lat_lon(x, y, origin_lat, origin_lon)
                        waypoints_gps.append((round(lat, 7), round(lon, 7)))
                    reverse = not reverse
                elif inter.geom_type == 'MultiLineString':
                    lines = list(inter.geoms)
                    if reverse:
                        lines.reverse()
                    for line in lines:
                        coords = list(line.coords)
                        if reverse:
                            coords.reverse()
                        for x, y in coords:
                            lat, lon = local_xy_to_lat_lon(x, y, origin_lat, origin_lon)
                            waypoints_gps.append((round(lat, 7), round(lon, 7)))
                    reverse = not reverse
            y_curr += row_spacing_m

        # Add RTL home waypoint at end
        waypoints_gps.append(self.home_coords)

        # Calculate mission length
        total_mission_dist = 0.0
        for i in range(len(waypoints_gps) - 1):
            total_mission_dist += haversine_distance(waypoints_gps[i][0], waypoints_gps[i][1], waypoints_gps[i+1][0], waypoints_gps[i+1][1])

        battery_consumption_pct = round((total_mission_dist / self.battery_range_meters) * 100.0, 1)

        return {
            "mission_status": "FEASIBLE" if battery_consumption_pct <= 80.0 else "WARNING_BATTERY_LOW",
            "total_waypoints": len(waypoints_gps),
            "total_distance_meters": round(total_mission_dist, 1),
            "estimated_battery_usage_pct": min(100.0, battery_consumption_pct),
            "exclusion_zones_count": len(self.exclusion_zones),
            "home_dock": {"latitude": origin_lat, "longitude": origin_lon},
            "waypoints": waypoints_gps
        }
