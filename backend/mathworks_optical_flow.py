"""
DEM3T3R V1 MathWorks-Inspired Optical Flow Obstacle Avoidance Engine
Adapted from MathWorks Robotics: https://github.com/mathworks-robotics/obstacle-avoidance-using-camera

Computes dense optical flow (Farneback method) across spatial corridors to detect
approaching obstacles, ground obstructions, and looming hazards via motion divergence.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional


class OpticalFlowObstacleAvoidance:
    def __init__(self, flow_threshold: float = 3.5, process_scale: float = 0.5):
        """
        :param flow_threshold: Average flow magnitude triggering an obstacle warning.
        :param process_scale: Downscale factor for high-speed real-time optical flow computation.
        """
        self.flow_threshold = flow_threshold
        self.process_scale = process_scale
        self.prev_gray: Optional[np.ndarray] = None
        self.last_action = "FORWARD"

    def reset(self):
        """Resets optical flow temporal history."""
        self.prev_gray = None
        self.last_action = "FORWARD"

    def process_frame(self, frame: np.ndarray, draw_vectors: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Calculates optical flow divergence between the current and previous frame.
        
        Returns:
            annotated_frame: Frame with optional motion vector arrows.
            telemetry: Dict with corridor flow magnitudes and steering action.
        """
        if frame is None or frame.size == 0:
            return frame, {
                "detected": False,
                "action": "FORWARD",
                "flow_magnitudes": {"left": 0.0, "center": 0.0, "right": 0.0},
                "hazard_score": 0.0,
                "warning": "No visual frame data"
            }

        h, w = frame.shape[:2]
        
        # Downscale for real-time 60fps throughput
        small = cv2.resize(frame, (0, 0), fx=self.process_scale, fy=self.process_scale)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Focus on lower 60% of frame (navigation horizon and ground plane)
        sh, sw = gray.shape[:2]
        roi_top = int(sh * 0.40)
        curr_roi = gray[roi_top:sh, 0:sw]

        if self.prev_gray is None or self.prev_gray.shape != curr_roi.shape:
            self.prev_gray = curr_roi
            return frame, {
                "detected": False,
                "action": "FORWARD",
                "flow_magnitudes": {"left": 0.0, "center": 0.0, "right": 0.0},
                "hazard_score": 0.0,
                "warning": "Initializing optical flow baseline"
            }

        # Calculate Farneback dense optical flow
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, curr_roi, None,
            pyr_scale=0.5, levels=3, winsize=15, iterations=3,
            poly_n=5, poly_sigma=1.2, flags=0
        )
        self.prev_gray = curr_roi

        u = flow[..., 0] # horizontal velocity (dx/dt)
        v = flow[..., 1] # vertical velocity (dy/dt)
        mag, _ = cv2.cartToPolar(u, v)

        # Segment into 3 spatial corridors: Left, Center, Right
        col_w = sw // 3
        left_mag = float(np.mean(mag[:, 0:col_w]))
        center_mag = float(np.mean(mag[:, col_w:col_w * 2]))
        right_mag = float(np.mean(mag[:, col_w * 2:sw]))

        hazard_score = center_mag
        is_blocked = center_mag > self.flow_threshold
        action = "FORWARD"
        warning = "Path clear"

        if is_blocked:
            if left_mag > self.flow_threshold and right_mag > self.flow_threshold:
                action = "STOP"
                warning = f"CRITICAL: Looming obstacle in all corridors (Center Flow: {center_mag:.1f})"
            elif left_mag < right_mag:
                action = "STEER_LEFT"
                warning = f"Optical flow divergence detected! Steer Left (Left: {left_mag:.1f} < Right: {right_mag:.1f})"
            else:
                action = "STEER_RIGHT"
                warning = f"Optical flow divergence detected! Steer Right (Right: {right_mag:.1f} <= Left: {left_mag:.1f})"
        else:
            action = "FORWARD"
            warning = f"Normal optical flow (Center: {center_mag:.1f})"

        self.last_action = action

        # Draw motion vectors if requested
        if draw_vectors:
            step = 16
            scale_inv = 1.0 / self.process_scale
            for y in range(0, curr_roi.shape[0], step):
                for x in range(0, curr_roi.shape[1], step):
                    dx = float(u[y, x])
                    dy = float(v[y, x])
                    if abs(dx) + abs(dy) > 1.0:
                        pt1 = (int(x * scale_inv), int((roi_top + y) * scale_inv))
                        pt2 = (int((x + dx * 2) * scale_inv), int((roi_top + y + dy * 2) * scale_inv))
                        cv2.arrowedLine(frame, pt1, pt2, (0, 255, 255), 1, tipLength=0.3)

        telemetry = {
            "detected": is_blocked,
            "action": action,
            "flow_magnitudes": {
                "left": round(left_mag, 2),
                "center": round(center_mag, 2),
                "right": round(right_mag, 2)
            },
            "hazard_score": round(hazard_score, 2),
            "warning": warning
        }

        return frame, telemetry
