"""
@file: test_vla_physical_ai.py
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

from backend.vla_engine import VisionLanguageActionEngine
from backend.physical_ai import PhysicalAIReasoningEngine
from backend.digital_twin_bridge import DigitalTwinBridge

def test_vla_action_generation():
    import torch
    from types import SimpleNamespace
    vla = VisionLanguageActionEngine(warm_up=False)
    class Inputs(dict):
        def to(self, *args):
            return self
    class Processor:
        response = 'SPOT_SPRAY'
        def __call__(self, **kwargs):
            return Inputs(input_ids=torch.tensor([[10, 11]]))
        def batch_decode(self, tokens, **kwargs):
            # Prompt tokens must never leak into the action parser.
            assert tokens.tolist() == [[12]]
            return [self.response]
    vla.processor = Processor()
    vla.model = SimpleNamespace(generate=lambda **kwargs: torch.tensor([[10, 11, 12]]))
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    telem = {"latitude": 6.9271, "longitude": 79.8612, "ultrasonic_front": 120.0}

    # 1. Test Stop command
    res_stop = vla.execute_vla_inference(frame, "Emergency halt now!", telem)
    assert res_stop["action_type"] == "SAFE_HALT"
    assert res_stop["actuator_commands"]["motors"]["left"] == 0

    # 2. Test Spray command
    res_spray = vla.execute_vla_inference(frame, "Detected severe blight, spray immediately", telem)
    assert res_spray["action_type"] == "SPOT_SPRAY"
    assert res_spray["actuator_commands"]["pump"] is True
    assert res_spray["actuator_commands"]["spray_duration_sec"] == 5.0

    # Repeated spraying must stop, and must not access undefined navigation targets.
    repeat = vla.execute_vla_inference(frame, 'spray again', telem)
    assert repeat['action_type'] == 'SAFE_HALT'

    # 3. Test Navigation command
    vla.processor.response = 'NAVIGATE'
    res_nav = vla.execute_vla_inference(frame, "Scan crop row 2", telem)
    assert res_nav["action_type"] == "NAVIGATE"
    assert res_nav["actuator_commands"]["motors"]["left"] > 0
    vla.processor.response = 'unrecognized response'
    assert vla.execute_vla_inference(frame, 'inspect', telem)['action_type'] == 'SAFE_HALT'

def test_physical_ai_affordance():
    phys = PhysicalAIReasoningEngine()
    # High soil moisture + slope -> warning
    eval_res = phys.evaluate_traversability(soil_moisture_raw=3400, pitch_angle_deg=15.0, roll_angle_deg=5.0, obstacle_distance_cm=150.0)
    assert eval_res["traction_state"] == "HIGH_SLIPPAGE_HAZARD"
    assert eval_res["stability_rating"] == "MODERATE_SLOPE"
    assert eval_res["safe_to_advance"] is True

    # Drift physics calculation
    drift = phys.compute_spray_drift_physics(wind_speed_kmh=12.0, wind_dir_deg=90.0, robot_heading_deg=0.0)
    assert drift["safe_to_spray"] is True
    assert "lateral_drift_offset_cm" in drift

def test_digital_twin_synchronization():
    twin = DigitalTwinBridge()
    real_pose = {"x_local_m": 2.5, "y_local_m": 4.1, "heading_deg": 90.0}
    actuators = {"left_speed": 180, "right_speed": 180, "pump_active": True}
    
    sync_frame = twin.sync_robot_pose_to_twin(real_pose, actuators)
    assert sync_frame["pose_world_frame"]["x_m"] == 2.5
    assert sync_frame["actuators"]["spray_relay_active"] is True
    assert sync_frame["sim_tick"] == 1
    
    scenario = twin.fetch_synthetic_training_scenario()
    assert "randomized_lighting_lux" in scenario
