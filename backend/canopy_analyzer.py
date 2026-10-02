"""
DEM3T3R V1 Canopy Vigor & Spectral Chlorophyll Index Engine.
Calculates RGB-derived precision agriculture vegetation indices from live camera feed:
1. ExG (Excess Green Index): ExG = 2*G - R - B (Foliage extraction & biomass)
2. VARI (Visible Atmospherically Resistant Index): VARI = (G - R) / (G + R - B) (Chlorophyll & nitrogen vigor)
3. GLI (Green Leaf Index): GLI = (2*G - R - B) / (2*G + R + B)
4. Canopy Coverage Ratio (% green cover)
5. False-color Heatmap visualization for plant stress mapping
"""
import cv2
import numpy as np
from typing import Dict, Any, Tuple

class CanopySpectralAnalyzer:
    @staticmethod
    def compute_vegetation_indices(frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes normalized RGB image to extract vegetation vigor metrics.
        Returns numerical scores and a colormapped stress visualization.
        """
        if frame is None or frame.size == 0:
            return {
                "exg_mean": 0.0,
                "vari_mean": 0.0,
                "gli_mean": 0.0,
                "canopy_coverage_pct": 0.0,
                "vigor_level": "UNKNOWN",
                "nitrogen_stress_risk": "UNKNOWN"
            }

        # Convert to float normalized [0.0, 1.0]
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        r = img_rgb[:, :, 0]
        g = img_rgb[:, :, 1]
        b = img_rgb[:, :, 2]
        
        sum_rgb = r + g + b
        sum_rgb[sum_rgb == 0] = 1e-6
        
        r_norm = r / sum_rgb
        g_norm = g / sum_rgb
        b_norm = b / sum_rgb

        # 1. Excess Green Index (ExG)
        exg = 2.0 * g_norm - r_norm - b_norm
        
        # 2. Visible Atmospherically Resistant Index (VARI)
        denom_vari = g + r - b
        denom_vari[np.abs(denom_vari) < 1e-5] = 1e-5
        vari = (g - r) / denom_vari
        vari = np.clip(vari, -1.0, 1.0)
        
        # 3. Green Leaf Index (GLI)
        denom_gli = 2.0 * g + r + b
        denom_gli[denom_gli == 0] = 1e-6
        gli = (2.0 * g - r - b) / denom_gli
        gli = np.clip(gli, -1.0, 1.0)

        # Plant tissue mask (ExG > 0.05)
        plant_mask = exg > 0.05
        canopy_pixels = int(np.count_nonzero(plant_mask))
        total_pixels = frame.shape[0] * frame.shape[1]
        canopy_coverage_pct = round((canopy_pixels / max(1, total_pixels)) * 100.0, 2)

        if canopy_pixels > 0:
            exg_mean = float(np.mean(exg[plant_mask]))
            vari_mean = float(np.mean(vari[plant_mask]))
            gli_mean = float(np.mean(gli[plant_mask]))
        else:
            exg_mean, vari_mean, gli_mean = 0.0, 0.0, 0.0

        # Classify vigor
        if vari_mean > 0.25:
            vigor = "HIGH (Optimal Chlorophyll)"
            nitrogen_risk = "LOW (Healthy Photosynthesis)"
        elif vari_mean > 0.10:
            vigor = "MODERATE (Slight Chlorosis)"
            nitrogen_risk = "MODERATE (Monitor Nitrogen/Iron)"
        else:
            vigor = "LOW (Severe Canopy Stress)"
            nitrogen_risk = "HIGH (Fertilizer Boost Recommended)"

        return {
            "exg_mean": round(exg_mean, 3),
            "vari_mean": round(vari_mean, 3),
            "gli_mean": round(gli_mean, 3),
            "canopy_coverage_pct": canopy_coverage_pct,
            "vigor_level": vigor,
            "nitrogen_stress_risk": nitrogen_risk
        }

    @staticmethod
    def generate_vigor_heatmap(frame: np.ndarray) -> np.ndarray:
        """Generates green-yellow-red False Color colormap representing vegetation vigor."""
        if frame is None or frame.size == 0:
            return np.zeros((480, 640, 3), dtype=np.uint8)

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        r, g, b = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]
        
        sum_rgb = r + g + b
        sum_rgb[sum_rgb == 0] = 1e-6
        exg = 2.0 * (g / sum_rgb) - (r / sum_rgb) - (b / sum_rgb)
        
        # Normalize ExG [-0.5, 0.5] to [0, 255]
        norm_exg = np.clip((exg + 0.2) / 0.6, 0.0, 1.0)
        heatmap_u8 = (norm_exg * 255).astype(np.uint8)
        
        colored = cv2.applyColorMap(heatmap_u8, cv2.COLORMAP_SUMMER)
        return cv2.addWeighted(frame, 0.4, colored, 0.6, 0)
