"""
@file: test_digital_twin.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Tests for Digital Twin & Simulation Bridge (Sim2Real Synchronization).
"""
import pytest
from backend.digital_twin_bridge import DigitalTwinBridge


def test_digital_twin_initialization():
    bridge = DigitalTwinBridge()
    snap = bridge.get_telemetry_snapshot()
    assert snap["status"] == "ACTIVE_MIRROR"
    assert snap["fps"] == 60.0
    assert "pose_world_frame" in snap
    assert "actuators" in snap
    assert "safety_frustum" in snap


def test_sync_robot_pose():
    bridge = DigitalTwinBridge()
    
    real_pose = {"x_local_m": 1.25, "y_local_m": 3.40, "heading_deg": 45.0, "terrain_tilt_deg": 4.5}
    actuators = {"left_speed": 200, "right_speed": 200, "pump_active": True, "solenoid_inserted": True}
    obstacles = {"clearance": {"left": 1.8, "center": 0.8, "right": 2.2}, "collision_risk": "CAUTION", "recommended_steer": "STEER_RIGHT"}
    
    telemetry = bridge.sync_robot_pose_to_twin(real_pose, actuators, obstacles)
    
    assert telemetry["sim_tick"] == 1
    assert telemetry["pose_world_frame"]["x_m"] == 1.25
    assert telemetry["pose_world_frame"]["y_m"] == 3.40
    assert telemetry["pose_world_frame"]["yaw_deg"] == 45.0
    assert telemetry["pose_world_frame"]["pitch_deg"] == 4.5
    
    assert telemetry["actuators"]["spray_active"] is True
    assert telemetry["actuators"]["solenoid_depth_m"] == 0.06
    assert telemetry["actuators"]["wheel_rpm"] > 0
    
    assert telemetry["safety_frustum"]["clearance_center"] == 0.8
    assert telemetry["safety_frustum"]["recommended_steer"] == "STEER_RIGHT"
    assert 0.005 <= telemetry["sim2real_divergence_metric"] <= 0.035


def test_digital_twin_reset():
    bridge = DigitalTwinBridge()
    bridge.sync_robot_pose_to_twin({"x_local_m": 5.0, "y_local_m": 5.0}, {})
    assert bridge.sim_tick == 1
    
    res = bridge.reset_sim()
    assert res["status"] == "RESET_OK"
    assert bridge.sim_tick == 0
    assert bridge.current_pose["x_m"] == 0.0
