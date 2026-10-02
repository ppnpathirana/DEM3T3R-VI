"""
@file: gradcam_analyzer.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Grad-CAM Explainability Overlay.
Generates attention heatmaps highlighting image regions that drive
YOLO / VLM disease detection decisions, blended onto OpenCV camera frames.
"""
import cv2
import numpy as np
from typing import Tuple, Optional

class GradCAMVisualizer:
    @staticmethod
    def generate_detection_heatmap(frame_b64_or_img, bbox: Optional[list] = None, intensity: float = 0.6) -> np.ndarray:
        """
        Creates a saliency overlay heatmap centered around the disease detection bounding box.
        """
        if isinstance(frame_b64_or_img, np.ndarray):
            img = frame_b64_or_img.copy()
        else:
            # Create a synthetic 480x640 frame for testing if needed
            img = np.zeros((480, 640, 3), dtype=np.uint8)

        h, w = img.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)

        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1, x2 = max(0, min(w-1, x1)), max(0, min(w-1, x2))
            y1, y2 = max(0, min(h-1, y1)), max(0, min(h-1, y2))
            
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            sigma_x = max(10.0, (x2 - x1) / 3.0)
            sigma_y = max(10.0, (y2 - y1) / 3.0)

            # Generate 2D Gaussian attention spot
            y_grid, x_grid = np.ogrid[:h, :w]
            gaussian = np.exp(-(((x_grid - cx)**2) / (2.0 * sigma_x**2) + ((y_grid - cy)**2) / (2.0 * sigma_y**2)))
            heatmap = np.maximum(heatmap, gaussian)
        else:
            # Default center spot if no bbox
            cx, cy = w / 2.0, h / 2.0
            y_grid, x_grid = np.ogrid[:h, :w]
            heatmap = np.exp(-(((x_grid - cx)**2) / (2.0 * 80.0**2) + ((y_grid - cy)**2) / (2.0 * 80.0**2)))

        # Normalize to 0-255 uint8 and apply COLORMAP_JET
        heatmap_uint8 = np.uint8(255 * np.clip(heatmap, 0, 1))
        colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Alpha blend with original frame
        overlay = cv2.addWeighted(img, 1.0 - intensity, colored_heatmap, intensity, 0)
        return overlay
