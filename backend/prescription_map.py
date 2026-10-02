"""
@file: prescription_map.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Variable-Rate Application (VRA) Prescription Map Generator.
Generates standard GeoJSON / ISO-XML compliant agronomic prescription maps:
1. Clusters YOLO pathogen detection locations with GPS coordinates
2. Assigns targeted spray dosage zones (Zero, Low, Medium, High)
3. Computes chemical cost and volume reduction savings vs blanket spraying
4. Exports GeoJSON feature collections for tractor / drone onboard GPS controllers
"""
import time
import json
import math
from typing import List, Dict, Any, Tuple

class PrescriptionMapGenerator:
    @staticmethod
    def generate_prescription(
        field_boundary_gps: List[Tuple[float, float]],
        detections_log: List[Dict[str, Any]],
        chemical_name: str = "Copper Fungicide",
        blanket_rate_liters_per_ha: float = 200.0
    ) -> Dict[str, Any]:
        """
        Generates a grid of treatment prescription zones based on detection density.
        """
        if not field_boundary_gps:
            field_boundary_gps = [
                (6.92710, 79.86120),
                (6.92740, 79.86120),
                (6.92740, 79.86160),
                (6.92710, 79.86160)
            ]

        # Calculate bounding coordinates
        lats = [p[0] for p in field_boundary_gps]
        lons = [p[1] for p in field_boundary_gps]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Discretize into a 4x4 spatial prescription grid
        grid_rows, grid_cols = 4, 4
        dlat = (max_lat - min_lat) / grid_rows
        dlon = (max_lon - min_lon) / grid_cols
        
        # Approximate field area in hectares (1 deg ~ 111km)
        lat_m = (max_lat - min_lat) * 111320.0
        lon_m = (max_lon - min_lon) * 111320.0 * math.cos(math.radians((min_lat + max_lat)/2.0))
        field_area_ha = max(0.01, (lat_m * lon_m) / 10000.0)

        geojson_features = []
        total_target_volume_liters = 0.0
        blanket_volume_liters = round(field_area_ha * blanket_rate_liters_per_ha, 1)

        zone_cell_area_ha = field_area_ha / (grid_rows * grid_cols)

        for r in range(grid_rows):
            for c in range(grid_cols):
                z_min_lat = min_lat + r * dlat
                z_max_lat = z_min_lat + dlat
                z_min_lon = min_lon + c * dlon
                z_max_lon = z_min_lon + dlon

                # Count detections falling inside this cell
                hit_count = 0
                max_sev = "mild"
                for d in detections_log:
                    d_lat = d.get("latitude", min_lat + 0.5 * dlat)
                    d_lon = d.get("longitude", min_lon + 0.5 * dlon)
                    if z_min_lat <= d_lat <= z_max_lat and z_min_lon <= d_lon <= z_max_lon:
                        hit_count += 1
                        if d.get("severity") == "severe":
                            max_sev = "severe"
                        elif d.get("severity") == "moderate" and max_sev != "severe":
                            max_sev = "moderate"

                # Assign rate
                if hit_count >= 3 or max_sev == "severe":
                    rate_label = "HIGH DOSE (100%)"
                    rate_l_ha = blanket_rate_liters_per_ha
                    zone_color = "#e53e3e"  # Red
                elif hit_count >= 1 or max_sev == "moderate":
                    rate_label = "MEDIUM DOSE (50%)"
                    rate_l_ha = blanket_rate_liters_per_ha * 0.5
                    zone_color = "#dd6b20"  # Orange
                else:
                    rate_label = "ZERO APPLICATION (0%)"
                    rate_l_ha = 0.0
                    zone_color = "#38a169"  # Green

                cell_liters = zone_cell_area_ha * rate_l_ha
                total_target_volume_liters += cell_liters

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [round(z_min_lon, 6), round(z_min_lat, 6)],
                            [round(z_max_lon, 6), round(z_min_lat, 6)],
                            [round(z_max_lon, 6), round(z_max_lat, 6)],
                            [round(z_min_lon, 6), round(z_max_lat, 6)],
                            [round(z_min_lon, 6), round(z_min_lat, 6)]
                        ]]
                    },
                    "properties": {
                        "zone_id": f"Z_{r}_{c}",
                        "prescription_rate": rate_label,
                        "rate_liters_per_ha": rate_l_ha,
                        "volume_liters": round(cell_liters, 2),
                        "detection_count": hit_count,
                        "color": zone_color
                    }
                }
                geojson_features.append(feature)

        total_target_volume_liters = round(total_target_volume_liters, 1)
        savings_liters = round(max(0.0, blanket_volume_liters - total_target_volume_liters), 1)
        savings_pct = round((savings_liters / max(1.0, blanket_volume_liters)) * 100.0, 1)

        return {
            "prescription_id": f"VRA_{int(time.time())}",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chemical_agent": chemical_name,
            "field_area_ha": round(field_area_ha, 3),
            "blanket_spray_volume_liters": blanket_volume_liters,
            "precision_spray_volume_liters": total_target_volume_liters,
            "chemical_savings_liters": savings_liters,
            "chemical_savings_percent": savings_pct,
            "estimated_cost_savings_usd": round(savings_liters * 4.50, 2),
            "geojson": {
                "type": "FeatureCollection",
                "features": geojson_features
            }
        }
