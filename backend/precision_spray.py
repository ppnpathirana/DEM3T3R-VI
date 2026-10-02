"""
@file: precision_spray.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Decision & Action Suite:
1. ConfidenceRouter: High confidence auto-proceeds to treatment, low confidence queues for farmer review
2. TreatmentAdvisor: Generates Organic, Chemical, and Cultural treatment options with cost & speed trade-offs
3. PrecisionSprayController: Calculates exact pulse spray duration based on YOLO segmentation mask area and severity level
"""
import time
from typing import Dict, Any, List

class ConfidenceRouter:
    def __init__(self, auto_threshold: float = 0.75):
        self.auto_threshold = auto_threshold
        self.farmer_review_queue: List[Dict[str, Any]] = []

    def route_diagnosis(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes detection:
        - confidence >= auto_threshold -> AUTO_TREAT
        - confidence < auto_threshold -> FARMER_REVIEW
        """
        confidence = float(diagnosis.get("confidence", 0.0))
        if confidence >= self.auto_threshold:
            return {
                "decision": "AUTO_TREAT",
                "reason": f"High confidence ({confidence*100:.1f}% >= {self.auto_threshold*100:.0f}%)",
                "queue_id": None
            }
        else:
            queue_item = {
                "id": f"rev_{int(time.time()*1000)}",
                "timestamp": time.time(),
                "diagnosis": diagnosis,
                "status": "PENDING_REVIEW"
            }
            self.farmer_review_queue.append(queue_item)
            return {
                "decision": "FARMER_REVIEW",
                "reason": f"Moderate/Low confidence ({confidence*100:.1f}% < {self.auto_threshold*100:.0f}%). Queued for confirmation.",
                "queue_id": queue_item["id"]
            }

    def resolve_review(self, queue_id: str, approved: bool) -> bool:
        for item in self.farmer_review_queue:
            if item["id"] == queue_id:
                item["status"] = "APPROVED" if approved else "REJECTED"
                return True
        return False

class TreatmentAdvisor:
    @staticmethod
    def get_options(crop: str, disease: str, severity: str = "moderate") -> List[Dict[str, Any]]:
        """Returns 3 treatment tiers (Organic, Chemical, Cultural) with cost/speed tradeoffs."""
        return [
            {
                "tier": "Biological / Organic",
                "method": "Neem Extract + Bacillus subtilis bio-fungicide",
                "cost_rating": "$ (Lowest Cost)",
                "speed_rating": "Moderate (4-6 days)",
                "safety": "100% Organic certified, zero harvest delay",
                "recommended_dose": "5ml / Liter water spray"
            },
            {
                "tier": "Chemical / Fungicide",
                "method": "Targeted Contact & Systemic Fungicide (e.g. Mancozeb / Azoxystrobin)",
                "cost_rating": "$$ (Standard Commercial)",
                "speed_rating": "Fast Acting (24-48 hours)",
                "safety": "Standard protective gear required, 7-day pre-harvest interval",
                "recommended_dose": "2g / Liter water spray"
            },
            {
                "tier": "Cultural / Mechanical",
                "method": "Precision Pruning of Infected Leaves + Raised Bed Airflow Optimization",
                "cost_rating": "Zero Chemical Cost (Labor Only)",
                "speed_rating": "Immediate Pathogen Removal",
                "safety": "Completely residue-free",
                "recommended_dose": "Prune lower 20% foliage, sanitize shears in alcohol"
            }
        ]

class PrecisionSprayController:
    @staticmethod
    def calculate_spray_duration(severity: str = "moderate", mask_area_pct: float = 5.0) -> float:
        """
        Calculates exact pulse spray duration in seconds:
        - Mild: ~3.0s
        - Moderate: ~5.0s
        - Severe: ~8.0s
        - Scaled by mask area percentage, capped at 10.0s hard safety limit.
        """
        base_durations = {"mild": 3.0, "moderate": 5.0, "severe": 8.0}
        base = base_durations.get(severity.lower(), 4.0)
        
        # Scale slightly if the diseased canopy area is exceptionally large (>15%)
        scale_factor = 1.0 + min(0.3, max(0.0, (mask_area_pct - 5.0) / 100.0))
        duration = base * scale_factor
        
        # Hard safety cap: never exceed 10.0 seconds
        return round(min(10.0, max(1.0, duration)), 1)
