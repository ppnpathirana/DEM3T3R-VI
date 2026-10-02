"""
@file: vision_obstacle_detector.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 Vision-Based Obstacle Detector (Camera Only — No Hardware Distance Sensors)

Processes live camera video frames to detect obstacles in the rover's path.
Divides the lower navigation zone (ground horizon) into 3 spatial corridors:
  - LEFT ZONE   (0% – 33% width)
  - CENTER ZONE (33% – 66% width)
  - RIGHT ZONE  (66% – 100% width)

Uses adaptive multi-scale edge gradient energy (Sobel/Canny), contour area density,
and luminance variance to detect ground-plane obstructions (rocks, vegetation clumps,
walls, tools, animals, humans) without requiring ultrasonic or LiDAR hardware.

Steering Recommendation:
  - FORWARD: Center corridor is clear (> 45% clearance)
  - STEER_LEFT: Center blocked, Left corridor has higher clearance than Right
  - STEER_RIGHT: Center blocked, Right corridor has higher clearance than Left
  - STOP: All 3 corridors blocked (< 30% clearance)
"""

import cv2
import numpy as np
import time
from typing import Tuple, Dict, Any


from backend.mathworks_optical_flow import OpticalFlowObstacleAvoidance


class VisionObstacleDetector:
    def __init__(self, clearance_threshold: float = 45.0, enable_optical_flow: bool = True):
        self.clearance_threshold = clearance_threshold
        self.enable_optical_flow = enable_optical_flow
        self.optical_flow = OpticalFlowObstacleAvoidance(flow_threshold=3.5) if enable_optical_flow else None
        self.last_action = "FORWARD"
        self.last_check_time = 0.0
        self.last_status = {
            "detected": False,
            "action": "FORWARD",
            "clearance": {"left": 2.5, "center": 2.5, "right": 2.5},
            "collision_risk": "CLEAR",
            "recommended_steer": "STRAIGHT"
        }

    def get_latest_status(self) -> Dict[str, Any]:
        return getattr(self, "last_status", {
            "detected": False,
            "action": "FORWARD",
            "clearance": {"left": 2.5, "center": 2.5, "right": 2.5},
            "collision_risk": "CLEAR",
            "recommended_steer": "STRAIGHT"
        })

    def process_frame(self, frame: np.ndarray, draw_hud: bool = True) -> Tuple[np.ndarray, Dict[str, Any]]:
        if frame is None or frame.size == 0:
            return frame, {
                "detected": False,
                "action": "FORWARD",
                "clearance": {"left": 100.0, "center": 100.0, "right": 100.0},
                "warning": "No frame data"
            }

        h, w = frame.shape[:2]
        # Focus on lower 55% of the frame (the immediate ground plane in front of rover)
        nav_top = int(h * 0.45)
        nav_roi = frame[nav_top:h, 0:w]
        roi_h, roi_w = nav_roi.shape[:2]

        gray = cv2.cvtColor(nav_roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 1. High-frequency edge gradient magnitude
        edges = cv2.Canny(blurred, 40, 110)

        # 2. Adaptive luminance disparity / obstacle contour detection
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4
        )
        combined_energy = cv2.bitwise_or(edges, thresh)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(combined_energy, kernel, iterations=1)

        col_w = roi_w // 3
        left_mask = dilated[:, 0:col_w]
        center_mask = dilated[:, col_w:col_w * 2]
        right_mask = dilated[:, col_w * 2:roi_w]

        left_hazard = (np.count_nonzero(left_mask) / float(left_mask.size)) * 100.0
        center_hazard = (np.count_nonzero(center_mask) / float(center_mask.size)) * 100.0
        right_hazard = (np.count_nonzero(right_mask) / float(right_mask.size)) * 100.0

        left_clearance = max(0.0, min(100.0, 100.0 - (left_hazard * 2.8)))
        center_clearance = max(0.0, min(100.0, 100.0 - (center_hazard * 2.8)))
        right_clearance = max(0.0, min(100.0, 100.0 - (right_hazard * 2.8)))

        flow_telem = None
        if self.optical_flow:
            frame, flow_telem = self.optical_flow.process_frame(frame, draw_vectors=draw_hud)
            if flow_telem and flow_telem.get("detected"):
                flow_mags = flow_telem.get("flow_magnitudes", {})
                center_clearance = max(0.0, center_clearance - (flow_mags.get("center", 0.0) * 4.0))
                left_clearance = max(0.0, left_clearance - (flow_mags.get("left", 0.0) * 4.0))
                right_clearance = max(0.0, right_clearance - (flow_mags.get("right", 0.0) * 4.0))

        is_blocked = center_clearance < self.clearance_threshold
        action = "FORWARD"
        warning = "Path clear"

        if is_blocked:
            if left_clearance < 30.0 and right_clearance < 30.0:
                action = "STOP"
                warning = "CRITICAL: All corridors blocked! Halting rover."
            elif left_clearance >= right_clearance:
                action = "STEER_LEFT"
                warning = f"Obstacle in center! Steer Left (Left Clearance: {left_clearance:.0f}%)"
            else:
                action = "STEER_RIGHT"
                warning = f"Obstacle in center! Steer Right (Right Clearance: {right_clearance:.0f}%)"
        else:
            action = "FORWARD"
            warning = f"Clear path ahead (Center Clearance: {center_clearance:.0f}%)"

        self.last_action = action

        if draw_hud:
            frame = self._render_hud(
                frame, nav_top, col_w, left_clearance, center_clearance, right_clearance, action, warning
            )

        telemetry = {
            "detected": is_blocked,
            "action": action,
            "clearance": {
                "left": round(left_clearance, 1),
                "center": round(center_clearance, 1),
                "right": round(right_clearance, 1)
            },
            "optical_flow": flow_telem.get("flow_magnitudes") if flow_telem else None,
            "warning": warning,
            "timestamp": time.time()
        }

        return frame, telemetry

    def _render_hud(
        self,
        frame: np.ndarray,
        nav_top: int,
        col_w: int,
        left_c: float,
        center_c: float,
        right_c: float,
        action: str,
        warning: str
    ) -> np.ndarray:
        h, w = frame.shape[:2]
        overlay = frame.copy()

        def get_color(clearance: float) -> Tuple[int, int, int]:
            if clearance >= 60.0:
                return (0, 230, 0)
            elif clearance >= 40.0:
                return (0, 215, 255)
            else:
                return (0, 30, 255)

        col_l = get_color(left_c)
        col_c = get_color(center_c)
        col_r = get_color(right_c)

        # Semi-transparent ground corridors
        cv2.rectangle(overlay, (0, nav_top), (col_w, h), (col_l[0]//6, col_l[1]//6, col_l[2]//6), -1)
        cv2.rectangle(overlay, (col_w, nav_top), (col_w * 2, h), (col_c[0]//6, col_c[1]//6, col_c[2]//6), -1)
        cv2.rectangle(overlay, (col_w * 2, nav_top), (w, h), (col_r[0]//6, col_r[1]//6, col_r[2]//6), -1)

        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        line_color = (0, 229, 255)
        cv2.line(frame, (0, nav_top), (w, nav_top), line_color, 1)
        cv2.line(frame, (col_w, nav_top), (col_w, h), (80, 80, 80), 1)
        cv2.line(frame, (col_w * 2, nav_top), (col_w * 2, h), (80, 80, 80), 1)

        cx = w // 2
        cy = nav_top + int((h - nav_top) * 0.55)
        crosshair_col = col_c
        cv2.circle(frame, (cx, cy), 16, crosshair_col, 2)
        cv2.line(frame, (cx - 24, cy), (cx + 24, cy), crosshair_col, 1)
        cv2.line(frame, (cx, cy - 24), (cx, cy + 24), crosshair_col, 1)

        cv2.putText(frame, f"L: {left_c:.0f}%", (12, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, col_l, 2)
        cv2.putText(frame, f"CTR: {center_c:.0f}%", (cx - 36, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, col_c, 2)
        cv2.putText(frame, f"R: {right_c:.0f}%", (w - 75, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, col_r, 2)

        banner_bg = (18, 12, 28)
        cv2.rectangle(frame, (0, 0), (w, 36), banner_bg, -1)
        cv2.line(frame, (0, 36), (w, 36), line_color, 1)

        action_icons = {
            "FORWARD": ">> CRUISING FORWARD (PATH CLEAR)",
            "STEER_LEFT": "<< AVOIDING OBSTACLE -> STEERING LEFT",
            "STEER_RIGHT": ">> AVOIDING OBSTACLE -> STEERING RIGHT",
            "STOP": "!! EMERGENCY HALT: ALL PATHS BLOCKED"
        }
        action_text = action_icons.get(action, action)
        action_col = (0, 255, 0) if action == "FORWARD" else (0, 200, 255) if "STEER" in action else (0, 0, 255)
        
        cv2.putText(frame, "VISION AUTO-PILOT", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 229, 255), 1)
        cv2.putText(frame, action_text, (150, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, action_col, 2)

        return frame
