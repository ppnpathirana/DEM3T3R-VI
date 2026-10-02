"""
@file: test_mathworks_robotics.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import pytest
import numpy as np
import math
from backend.mathworks_optical_flow import OpticalFlowObstacleAvoidance
from backend.pure_pursuit import PurePursuitController, TrapezoidalVelocityProfile


def test_optical_flow_baseline():
    detector = OpticalFlowObstacleAvoidance(flow_threshold=3.0)
    frame1 = np.ones((240, 320, 3), dtype=np.uint8) * 128
    frame2 = np.ones((240, 320, 3), dtype=np.uint8) * 128
    
    # First frame initializes
    _, telem1 = detector.process_frame(frame1)
    assert telem1["action"] == "FORWARD"
    
    # Identical second frame produces near-zero flow
    _, telem2 = detector.process_frame(frame2)
    assert telem2["detected"] is False
    assert telem2["action"] == "FORWARD"
    assert telem2["flow_magnitudes"]["center"] == 0.0


def test_optical_flow_obstacle_divergence():
    detector = OpticalFlowObstacleAvoidance(flow_threshold=2.0)
    
    # Create two frames simulating an expanding looming object in center
    frame1 = np.ones((240, 320, 3), dtype=np.uint8) * 100
    frame2 = np.ones((240, 320, 3), dtype=np.uint8) * 100
    
    # Center circle expansion
    import cv2
    cv2.circle(frame1, (160, 160), 20, (255, 255, 255), -1)
    cv2.circle(frame2, (160, 160), 50, (255, 255, 255), -1)
    
    detector.process_frame(frame1)
    _, telem = detector.process_frame(frame2)
    
    # Expansion in center creates high flow magnitude
    assert telem["flow_magnitudes"]["center"] > 0.5


def test_pure_pursuit_straight_line():
    controller = PurePursuitController(lookahead_distance=1.0, wheel_base=0.35)
    
    # Robot at origin facing east (0 radians)
    current_pose = (0.0, 0.0, 0.0)
    # Path straight along x-axis
    path = [(1.0, 0.0), (2.0, 0.0), (5.0, 0.0)]
    
    cmd = controller.compute_steering(current_pose, path)
    
    # Curvature should be near 0 on a straight line
    assert abs(cmd["curvature"]) < 0.05
    assert abs(cmd["motor_left"] - cmd["motor_right"]) < 10
    assert cmd["goal_reached"] is False


def test_pure_pursuit_left_turn():
    controller = PurePursuitController(lookahead_distance=1.0, wheel_base=0.35)
    
    # Robot at origin facing east (0 rad), waypoint to the left (0, 2)
    current_pose = (0.0, 0.0, 0.0)
    path = [(0.5, 1.0), (0.5, 2.0)]
    
    cmd = controller.compute_steering(current_pose, path)
    
    # Positive curvature = left turn (right wheel moves faster than left)
    assert cmd["curvature"] > 0.5
    assert cmd["motor_right"] > cmd["motor_left"]


def test_pure_pursuit_goal_reached():
    controller = PurePursuitController(goal_radius=0.5)
    current_pose = (4.9, 0.0, 0.0)
    path = [(1.0, 0.0), (5.0, 0.0)]
    
    cmd = controller.compute_steering(current_pose, path)
    assert cmd["goal_reached"] is True
    assert cmd["motor_left"] == 0
    assert cmd["motor_right"] == 0


def test_trapezoidal_velocity_ramp():
    profiler = TrapezoidalVelocityProfile(v_max=0.6, a_max=0.5, d_max=0.8, v_min=0.1)
    
    # Far from goal -> ramps up
    v1 = profiler.compute_velocity(distance_to_goal=10.0, dt=0.5)
    assert v1 > 0.1
    v2 = profiler.compute_velocity(distance_to_goal=10.0, dt=0.5)
    assert v2 > v1
    
    # Close to goal -> decelerates
    v_stop = profiler.compute_velocity(distance_to_goal=0.02, dt=0.1)
    assert v_stop == 0.0
