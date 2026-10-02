"""
@file: neural_segmentation.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 Semantic Terrain & Crop Segmentation Neural Network
Segments agricultural fields pixel-by-pixel into:
  - Class 0: Sky / Background
  - Class 1: Crops / Foliage (Green)
  - Class 2: Navigable Soil Path (Brown/Gray)
  - Class 3: Obstacles / Weeds / Hard Hazards (Red)

Calculates the lateral row-centering offset to keep the robot aligned with crop furrows.
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Any, Optional


class MobileSegmenterNet(nn.Module):
    """Lightweight Mobile UNet for real-time agricultural terrain parsing."""
    def __init__(self, num_classes: int = 4):
        super().__init__()
        # Encoder
        self.enc1 = nn.Sequential(
            nn.Conv2d(3, 24, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(24),
            nn.ReLU6(inplace=True)
        )
        self.enc2 = nn.Sequential(
            nn.Conv2d(24, 48, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(48),
            nn.ReLU6(inplace=True)
        )
        self.enc3 = nn.Sequential(
            nn.Conv2d(48, 96, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(96),
            nn.ReLU6(inplace=True)
        )

        # Bottleneck
        self.mid = nn.Sequential(
            nn.Conv2d(96, 96, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(96),
            nn.ReLU6(inplace=True)
        )

        # Decoder
        self.dec2 = nn.Sequential(
            nn.Conv2d(96 + 48, 48, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(48),
            nn.ReLU6(inplace=True)
        )
        self.dec1 = nn.Sequential(
            nn.Conv2d(48 + 24, 24, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(24),
            nn.ReLU6(inplace=True)
        )
        self.classifier = nn.Conv2d(24, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        orig_h, orig_w = x.shape[2:]

        # Downsample
        e1 = self.enc1(x)  # 1/2
        e2 = self.enc2(e1) # 1/4
        e3 = self.enc3(e2) # 1/8

        m = self.mid(e3)

        # Upsample
        u2 = F.interpolate(m, size=e2.shape[2:], mode='bilinear', align_corners=False)
        d2 = self.dec2(torch.cat([u2, e2], dim=1))

        u1 = F.interpolate(d2, size=e1.shape[2:], mode='bilinear', align_corners=False)
        d1 = self.dec1(torch.cat([u1, e1], dim=1))

        out = self.classifier(d1)
        out = F.interpolate(out, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
        return out


class TerrainSegmenter:
    # Color palette for classes: [B, G, R]
    CLASS_COLORS = {
        0: (60, 60, 60),      # 0: Background/Sky (Dark Grey)
        1: (34, 180, 50),     # 1: Crops / Vegetation (Green)
        2: (42, 110, 160),    # 2: Navigable Soil Path (Earth Brown/Gold)
        3: (30, 30, 220)      # 3: Obstacle / Hazard (Red)
    }

    CLASS_NAMES = ["Sky/Background", "Crops", "Soil Path", "Obstacle"]

    def __init__(self, device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = MobileSegmenterNet(num_classes=4).to(self.device)
        self.model.eval()

        if self.device == "cuda":
            self.model.half()

    @torch.no_grad()
    def segment_terrain(
        self,
        frame: np.ndarray,
        create_overlay: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """
        Parses camera frame into semantic terrain categories and calculates furrow centering.
        
        Returns:
            class_map: (H, W) uint8 array of class indices (0 to 3).
            overlay_frame: (H, W, 3) image with semi-transparent segmentation mask.
            telemetry: Dict with class coverage and lateral path offset ratio.
        """
        if frame is None or frame.size == 0:
            return np.zeros((240, 320), dtype=np.uint8), None, {
                "path_detected": False,
                "path_offset_ratio": 0.0,
                "coverage_pct": {"crops": 0.0, "soil_path": 0.0, "obstacles": 0.0}
            }

        orig_h, orig_w = frame.shape[:2]
        net_w, net_h = 256, 192

        resized = cv2.resize(frame, (net_w, net_h))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm_img = (rgb - mean) / std

        tensor = torch.from_numpy(norm_img).permute(2, 0, 1).unsqueeze(0).to(self.device)
        if self.device == "cuda":
            tensor = tensor.half()

        logits = self.model(tensor)

        # Prior heuristic fusion for agricultural scenes:
        # Green pixels -> high probability of Crop (Class 1)
        # Low green/high red-brown -> Soil (Class 2)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, (25, 40, 40), (85, 255, 255)) > 0
        brown_mask = cv2.inRange(hsv, (8, 30, 20), (24, 255, 200)) > 0

        logits_cpu = logits.squeeze().cpu().float().numpy() # (4, H, W)
        logits_cpu[1, :, :] += (green_mask * 1.5)
        logits_cpu[2, :, :] += (brown_mask * 1.5)

        preds = np.argmax(logits_cpu, axis=0).astype(np.uint8)
        class_map = cv2.resize(preds, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

        total_px = float(orig_h * orig_w)
        pct_crops = float(np.sum(class_map == 1)) / total_px * 100.0
        pct_soil = float(np.sum(class_map == 2)) / total_px * 100.0
        pct_obs = float(np.sum(class_map == 3)) / total_px * 100.0

        # Calculate row-centering error on the lower 40% (ground horizon)
        ground_top = int(orig_h * 0.60)
        ground_path = (class_map[ground_top:orig_h, :] == 2).astype(np.uint8)

        moments = cv2.moments(ground_path)
        path_detected = False
        offset_ratio = 0.0

        if moments["m00"] > 100:
            cx = moments["m10"] / moments["m00"]
            center_x = orig_w / 2.0
            offset_ratio = (cx - center_x) / center_x
            offset_ratio = max(-1.0, min(1.0, offset_ratio))
            path_detected = True

        overlay_frame = None
        if create_overlay:
            color_mask = np.zeros((orig_h, orig_w, 3), dtype=np.uint8)
            for cls_idx, color in self.CLASS_COLORS.items():
                color_mask[class_map == cls_idx] = color

            overlay_frame = cv2.addWeighted(frame, 0.65, color_mask, 0.35, 0)
            if path_detected:
                target_x = int((orig_w / 2.0) + (offset_ratio * (orig_w / 2.0)))
                cv2.line(overlay_frame, (target_x, ground_top), (target_x, orig_h), (0, 255, 255), 2)
                cv2.circle(overlay_frame, (target_x, int((ground_top + orig_h) / 2)), 6, (0, 255, 255), -1)

        telemetry = {
            "path_detected": path_detected,
            "path_offset_ratio": round(offset_ratio, 3),
            "coverage_pct": {
                "crops": round(pct_crops, 1),
                "soil_path": round(pct_soil, 1),
                "obstacles": round(pct_obs, 1)
            },
            "device": self.device
        }

        return class_map, overlay_frame, telemetry
