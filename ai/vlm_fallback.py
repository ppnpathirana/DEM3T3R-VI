"""
@file: vlm_fallback.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Local VLM Fallback - Offline diagnosis when internet unavailable
Uses smaller vision-language model running locally
"""
# TODO: Implement local VLM (e.g., LLaVA, MiniGPT-4)
# This is a placeholder for offline fallback

class VLMFallback:
    def __init__(self):
        self.model = None
        print("[VLM] Local fallback model not yet implemented")
    
    def diagnose(self, image, sensor_context, crop_name):
        """Fallback diagnosis when Claude API unavailable"""
        print("[VLM] Using offline fallback (basic rules)")
        
        # Simple rule-based fallback
        if sensor_context.get('humidity_pct', 0) > 85:
            return {
                "diagnosis": "possible fungal infection",
                "reasoning": "High humidity detected",
                "confidence": 0.3,
                "treatment": "improve ventilation"
            }
        
        return {
            "diagnosis": "unknown",
            "reasoning": "offline mode - limited analysis",
            "confidence": 0.2,
            "treatment": "manual inspection required"
        }
