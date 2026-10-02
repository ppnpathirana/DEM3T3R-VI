"""
@file: test_vision_obstacle_detector.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import numpy as np
import pytest
from backend.vision_obstacle_detector import VisionObstacleDetector

def test_detector_clear_frame():
    detector = VisionObstacleDetector(clearance_threshold=45.0)
    # Completely uniform grey frame (smooth ground, no edges/obstacles)
    clear_frame = np.full((360, 640, 3), 120, dtype=np.uint8)
    
    annotated, telem = detector.process_frame(clear_frame, draw_hud=True)
    assert annotated.shape == clear_frame.shape
    assert telem["detected"] is False
    assert telem["action"] == "FORWARD"
    assert telem["clearance"]["center"] >= 70.0

def test_detector_center_obstacle():
    detector = VisionObstacleDetector(clearance_threshold=45.0)
    frame = np.full((360, 640, 3), 120, dtype=np.uint8)
    
    # Introduce high-contrast, high-edge obstacle in center corridor (w: 213 to 426, h: 200 to 360)
    noise = np.random.randint(0, 255, (160, 200, 3), dtype=np.uint8)
    frame[200:360, 220:420] = noise
    
    annotated, telem = detector.process_frame(frame, draw_hud=True)
    assert telem["detected"] is True
    assert telem["action"] in ["STEER_LEFT", "STEER_RIGHT"]
    assert telem["clearance"]["center"] < 45.0

def test_detector_hud_rendering():
    detector = VisionObstacleDetector()
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    annotated, telem = detector.process_frame(frame, draw_hud=True)
    assert annotated is not None
    assert "clearance" in telem
