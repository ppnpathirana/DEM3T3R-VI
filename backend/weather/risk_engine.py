"""
==============================================================================
DEMETER Weather Intelligence System - Disease Risk & Irrigation Engine
==============================================================================
Calculates plant disease risks and smart irrigation recommendations by fusing
YOLO detections, environmental sensors, plant species, and 7-day weather predictions.
==============================================================================
"""

from typing import Dict, Any, List, Optional

class DiseaseRiskEngine:
    """Calculates multi-pathogen risk index and smart irrigation decision support."""

    # Fungal pathogens thrive in high humidity (>75%) and moderate-to-warm temperatures (18-28°C)
    # Bacterial pathogens thrive in warm, wet conditions (>25°C, high moisture, leaf splash)

    @staticmethod
    def calculate_risks(
        crop_name: str,
        current_weather: Dict[str, Any],
        forecast_daily: List[Dict[str, Any]],
        sensor_data: Optional[Dict[str, Any]] = None,
        detected_diseases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Fuses real-time sensor metrics + 7-day forecast + YOLO detections
        to compute disease risk percentages and smart irrigation guidance.
        """
        sensors = sensor_data or {}
        detections = detected_diseases or []

        # 1. Resolve environmental variables (blend ESP32 local sensor + weather station)
        temp = sensors.get("temperature") or current_weather.get("temperature", 26.0)
        humidity = sensors.get("humidity") or current_weather.get("humidity", 65)
        soil_raw = sensors.get("soilMoisture", 2000) # 0 to 4095
        soil_pct = max(0, min(100, int((soil_raw / 4095.0) * 100)))

        rain_chance_today = current_weather.get("rain_probability", 0)
        precipitation_today = current_weather.get("precipitation", 0.0)
        wind_speed = current_weather.get("wind_speed", 10.0)
        uv_index = current_weather.get("uv_index", 5.0)

        # 7-day weather trend
        next_3_days_rain_prob = [d.get("rain_probability", 0) for d in forecast_daily[:3]]
        avg_rain_prob_3d = sum(next_3_days_rain_prob) / len(next_3_days_rain_prob) if next_3_days_rain_prob else 0
        total_precip_7d = sum(d.get("precipitation_sum", 0.0) for d in forecast_daily[:7])

        # 2. Calculate Base Fungal Infection Risk
        fungal_score = 15.0
        if humidity > 80:
            fungal_score += 40.0
        elif humidity > 70:
            fungal_score += 25.0
        elif humidity > 60:
            fungal_score += 10.0

        if 18 <= temp <= 28:
            fungal_score += 20.0
        elif 15 <= temp <= 32:
            fungal_score += 10.0

        if rain_chance_today > 60 or avg_rain_prob_3d > 50:
            fungal_score += 20.0

        fungal_score = min(95.0, max(10.0, fungal_score))

        # 3. Calculate Bacterial Disease Risk
        bacterial_score = 10.0
        if temp > 25 and humidity > 75:
            bacterial_score += 35.0
        if precipitation_today > 2.0 or avg_rain_prob_3d > 60:
            bacterial_score += 30.0
        if wind_speed > 25:
            bacterial_score += 15.0 # Wind driven rain spread

        bacterial_score = min(90.0, max(8.0, bacterial_score))

        # 4. Specific Pathogen Risk Scores based on Crop Type
        crop_lower = crop_name.lower()
        specific_risks = []

        if "tomato" in crop_lower:
            late_blight_risk = min(98, int(fungal_score * 1.1 if humidity > 75 and 17 <= temp <= 24 else fungal_score * 0.8))
            early_blight_risk = min(95, int(fungal_score * 1.05 if temp > 24 else fungal_score * 0.75))
            bacterial_spot = min(90, int(bacterial_score * 0.95))
            
            specific_risks = [
                {"name": "Tomato Late Blight", "type": "Fungal", "risk_pct": late_blight_risk, "level": _risk_level(late_blight_risk)},
                {"name": "Tomato Early Blight", "type": "Fungal", "risk_pct": early_blight_risk, "level": _risk_level(early_blight_risk)},
                {"name": "Bacterial Spot", "type": "Bacterial", "risk_pct": bacterial_spot, "level": _risk_level(bacterial_spot)},
            ]
        elif "potato" in crop_lower:
            late_blight = min(98, int(fungal_score * 1.15))
            scab = min(80, int(30 + (temp * 1.2)))
            specific_risks = [
                {"name": "Potato Late Blight", "type": "Fungal", "risk_pct": late_blight, "level": _risk_level(late_blight)},
                {"name": "Common Scab", "type": "Bacterial", "risk_pct": scab, "level": _risk_level(scab)},
            ]
        elif "chilli" in crop_lower or "capsicum" in crop_lower:
            anthracnose = min(95, int(fungal_score * 1.1 if temp > 26 and humidity > 70 else fungal_score * 0.8))
            leaf_curl = min(85, int(35 + (temp * 1.1)))
            specific_risks = [
                {"name": "Chilli Anthracnose", "type": "Fungal", "risk_pct": anthracnose, "level": _risk_level(anthracnose)},
                {"name": "Chilli Leaf Curl", "type": "Viral Vector", "risk_pct": leaf_curl, "level": _risk_level(leaf_curl)},
            ]
        else:
            leaf_spot = min(92, int(fungal_score))
            powdery_mildew = min(88, int(fungal_score * 0.9))
            specific_risks = [
                {"name": f"{crop_name} Leaf Spot", "type": "Fungal", "risk_pct": leaf_spot, "level": _risk_level(leaf_spot)},
                {"name": "Powdery Mildew", "type": "Fungal", "risk_pct": powdery_mildew, "level": _risk_level(powdery_mildew)},
            ]

        # 5. Integrate YOLO Active Detections if spotted
        top_detected_name = None
        yolo_boost = False
        if detections:
            top_det = detections[0]
            top_detected_name = top_det.get("class", "").replace("_", " ")
            yolo_conf = top_det.get("confidence", 0.8)
            yolo_boost = True

        # 6. Smart Irrigation Decision Support
        # Combines soil moisture + rain probability in next 24-48 hours
        irrigation_status = "GREEN"
        irrigation_headline = "🟢 No Irrigation Needed"
        irrigation_advice = "Soil moisture is optimal and upcoming rainfall is expected. Delay irrigation to conserve water and prevent root saturation."

        if soil_pct < 35:
            if avg_rain_prob_3d < 30 and total_precip_7d < 5.0:
                irrigation_status = "RED"
                irrigation_headline = "🔴 Irrigation May Be Required"
                irrigation_advice = f"Soil moisture is low ({soil_pct}%) with minimal rain expected in the next 3 days. Recommend scheduled furrow or drip irrigation under manual supervision."
            else:
                irrigation_status = "YELLOW"
                irrigation_headline = "🟡 Monitor Soil Moisture"
                irrigation_advice = f"Soil moisture is low ({soil_pct}%), but precipitation ({int(avg_rain_prob_3d)}% chance) is forecasted. Monitor before irrigating."
        elif soil_pct < 55:
            if avg_rain_prob_3d < 25 and temp > 30:
                irrigation_status = "YELLOW"
                irrigation_headline = "🟡 Monitor Soil Evaporation"
                irrigation_advice = "High daytime temperatures may accelerate evaporation. Inspect root zone moisture."
            else:
                irrigation_status = "GREEN"
                irrigation_headline = "🟢 Soil Moisture Adequate"
                irrigation_advice = f"Current soil moisture ({soil_pct}%) is within healthy range for {crop_name}."
        else:
            irrigation_status = "GREEN"
            irrigation_headline = "🟢 Moisture High / Sufficient"
            irrigation_advice = f"Soil moisture ({soil_pct}%) is well saturated. Ensure adequate drainage to avoid fungal buildup."

        return {
            "crop": crop_name,
            "fungal_risk_pct": int(fungal_score),
            "bacterial_risk_pct": int(bacterial_score),
            "overall_environmental_risk": "HIGH" if fungal_score > 70 or bacterial_score > 70 else ("MODERATE" if fungal_score > 40 else "LOW"),
            "specific_pathogen_risks": specific_risks,
            "yolo_detection_active": yolo_boost,
            "detected_pathogen": top_detected_name,
            "smart_irrigation": {
                "status": irrigation_status,
                "headline": irrigation_headline,
                "advice": irrigation_advice,
                "soil_moisture_pct": soil_pct,
                "avg_rain_chance_3d": int(avg_rain_prob_3d),
                "total_rain_7d_mm": round(total_precip_7d, 1)
            },
            "disclaimer": "AI / Environmental Risk Estimate — Decision-support tool, not a scientific diagnostic guarantee."
        }

def _risk_level(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    elif score >= 55:
        return "HIGH"
    elif score >= 35:
        return "MODERATE"
    return "LOW"
