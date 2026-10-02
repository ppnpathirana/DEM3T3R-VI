"""
@file: test_advanced_features.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿import sys, os, time, pytest, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.canopy_analyzer import CanopySpectralAnalyzer
from backend.prescription_map import PrescriptionMapGenerator
from backend.field_mapper import FieldMissionManager
from backend.swarm_mesh import SwarmMeshCoordinator
from backend.watchdog import SystemHealthWatchdog

def test_canopy_spectral_indices():
    # Synthetic frame with green foliage
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[50:180, 50:250] = [30, 200, 40]  # Green pixels
    
    indices = CanopySpectralAnalyzer.compute_vegetation_indices(frame)
    assert "exg_mean" in indices
    assert "vari_mean" in indices
    assert "gli_mean" in indices
    assert indices["canopy_coverage_pct"] > 10.0
    assert "vigor_level" in indices
    
    heatmap = CanopySpectralAnalyzer.generate_vigor_heatmap(frame)
    assert heatmap.shape == (240, 320, 3)

def test_prescription_map_generator():
    boundary = [
        (6.92710, 79.86120),
        (6.92740, 79.86120),
        (6.92740, 79.86160),
        (6.92710, 79.86160)
    ]
    detections = [
        {"class": "tomato_early_blight", "severity": "severe", "latitude": 6.92720, "longitude": 79.86130},
        {"class": "tomato_early_blight", "severity": "moderate", "latitude": 6.92725, "longitude": 79.86135}
    ]
    res = PrescriptionMapGenerator.generate_prescription(boundary, detections, chemical_name="Mancozeb 75 WP")
    assert res["chemical_savings_percent"] > 0.0
    assert "geojson" in res
    assert len(res["geojson"]["features"]) == 16  # 4x4 grid

def test_field_mission_manager_with_exclusions():
    mgr = FieldMissionManager(home_lat=6.92710, home_lon=79.86120)
    # Add a tree/obstacle zone
    obstacle = [
        (6.92725, 79.86135),
        (6.92730, 79.86135),
        (6.92730, 79.86140),
        (6.92725, 79.86140)
    ]
    mgr.add_exclusion_zone(obstacle)
    
    boundary = [
        (6.92710, 79.86120),
        (6.92740, 79.86120),
        (6.92740, 79.86160),
        (6.92710, 79.86160)
    ]
    plan = mgr.plan_mission_with_exclusions(boundary, row_spacing_m=1.0)
    assert plan["mission_status"] in ["FEASIBLE", "WARNING_BATTERY_LOW"]
    assert plan["total_waypoints"] > 3
    assert plan["exclusion_zones_count"] == 1

def test_swarm_mesh_coordinator():
    coord = SwarmMeshCoordinator()
    status = coord.get_swarm_status()
    assert status["active_nodes_count"] == 3
    
    # Broadcast a hotspot
    spot = coord.broadcast_disease_hotspot("node-01", "Tomato Early Blight", 6.9272, 79.8613, "severe")
    assert spot["status"] == "ASSIGNED_FOR_TREATMENT"
    assert coord.get_swarm_status()["shared_hotspots_count"] == 1

def test_system_health_watchdog():
    dog = SystemHealthWatchdog()
    dog.ping_subsystem("yolo_inference_engine", {"fps": 31.0, "latency_ms": 32.0})
    check = dog.run_diagnostic_check()
    assert check["system_health_status"] == "ALL_SYSTEMS_GO"
    assert check["subsystems"]["yolo_inference_engine"]["fps"] == 31.0
