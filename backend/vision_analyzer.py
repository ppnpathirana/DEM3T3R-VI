"""
@file: vision_analyzer.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import json
import requests
import base64
import time
from config.settings import OLLAMA_MODEL_VL, OLLAMA_API_URL, GEMINI_KEYS, GROK_KEY

_last_internet_check = 0.0
_internet_cache = False

def is_online() -> bool:
    """Checks internet connectivity with a cached result to avoid blocking."""
    global _last_internet_check, _internet_cache
    now = time.time()
    if now - _last_internet_check > 15.0:
        _last_internet_check = now
        try:
            # Fast ping-like check
            requests.get("https://www.google.com", timeout=1.0)
            _internet_cache = True
        except Exception:
            _internet_cache = False
    return _internet_cache

def analyze_disease(frame_b64: str, detection: dict, sensors: dict) -> dict:
    """
    Input: Camera frame (base64 string), YOLO detection, sensor readings
    Output: {
        "disease": "Tomato Early Blight",
        "severity": "moderate",
        "reason_sinhala": "  ...",
        "recovery_plan": ["Copper fungicide spray", "Improve airflow"],
        "treatment_duration_sec": 5,
        "confidence": 0.85
    }
    """
    # Fallback default response in case of any failures
    fallback = {
        "disease": detection.get("class", "Unknown Pathogen"),
        "severity": "moderate",
        "reason": f"Environmental parameters: Temperature {sensors.get('temperature', 0)}C and Humidity {sensors.get('humidity', 0)}% favor condition onset.",
        "recovery_plan": ["Apply recommended fungicide spray treatment.", "Prune and isolate infected foliar tissue."],
        "treatment_duration_sec": 5,
        "confidence": float(detection.get("confidence", 0.70))
    }

    # If image base64 starts with data URI prefix, strip it
    if "," in frame_b64:
        frame_b64 = frame_b64.split(",")[1]

    prompt = f"""You are an agricultural plant pathologist. Analyze this crop disease detection.
        
Active Detection: {json.dumps(detection)}
Environmental Sensors Telemetry: {json.dumps(sensors)}

You must return a JSON object with the following fields:
- "disease": String (English name of detected disease, e.g., "Tomato Early Blight")
- "severity": String ("mild" | "moderate" | "severe")
- "reason_sinhala": String (Sinhala explanation of why this occurred based on environmental sensors like humidity and temperature)
- "recovery_plan": List of Strings (Step by step action plan to treat/recover)
- "treatment_duration_sec": Integer (Estimated spray duration in seconds, e.g. 5)
- "confidence": Float (Estimated certainty score between 0.0 and 1.0)

Your response must contain ONLY the raw JSON object, no explanation, no markdown backticks, just valid JSON."""

    # Check internet connectivity status
    online = is_online()
    print(f"[VISION ANALYZER] Internet connectivity status: {'ONLINE' if online else 'OFFLINE (Skip Cloud)'}")

    if online:
        # ----------------------------------------------------
        # PHASE 1: Rotate through Gemini Keys
        # ----------------------------------------------------
        for idx, key in enumerate(GEMINI_KEYS):
            if not key or "your-" in key:
                continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
                print(f"[VISION ANALYZER] Trying Gemini API (Key {idx+1}/{len(GEMINI_KEYS)})...")
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": frame_b64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if response.status_code == 200:
                    result = response.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = json.loads(text)
                    print(f"[VISION ANALYZER] ✅ Gemini API Key {idx+1} Success!")
                    return validate_and_repair(parsed, fallback)
                else:
                    print(f"[VISION ANALYZER] ⚠️ Gemini API Key {idx+1} returned code {response.status_code}")
            except Exception as e:
                print(f"[VISION ANALYZER] ❌ Gemini API Key {idx+1} Error: {e}")

        # ----------------------------------------------------
        # PHASE 2: Fallback to Groq API
        # ----------------------------------------------------
        if GROK_KEY and "your-" not in GROK_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                print("[VISION ANALYZER] Trying Groq API...")
                
                headers = {
                    "Authorization": f"Bearer {GROK_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": { "type": "json_object" }
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    text = result["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(text)
                    print("[VISION ANALYZER] ✅ Groq API Success!")
                    return validate_and_repair(parsed, fallback)
                else:
                    print(f"[VISION ANALYZER] ⚠️ Groq API returned code {response.status_code}")
            except Exception as e:
                print(f"[VISION ANALYZER] ❌ Groq API Error: {e}")

    # ----------------------------------------------------
    # PHASE 3: Fallback to Local VLM (Ollama Qwen2.5-VL)
    # ----------------------------------------------------
    try:
        url = f"{OLLAMA_API_URL}/api/chat"
        print(f"[VISION ANALYZER] Falling back to Local VLM ({OLLAMA_MODEL_VL})...")
        
        payload = {
            "model": OLLAMA_MODEL_VL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [frame_b64]
                }
            ],
            "options": {
                "temperature": 0.2
            },
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            result_data = response.json()
            message_content = result_data.get("message", {}).get("content", "").strip()
            parsed = json.loads(message_content)
            print("[VISION ANALYZER] ✅ Local VLM Success!")
            return validate_and_repair(parsed, fallback)
    except Exception as e:
        print(f"[VISION ANALYZER] ❌ Local VLM Error: {e}")

    print("[VISION ANALYZER] ⚠️ All models failed. Returning hardcoded default.")
    return fallback

def validate_and_repair(parsed: dict, fallback: dict) -> dict:
    required_keys = ["disease", "severity", "reason_sinhala", "recovery_plan", "treatment_duration_sec", "confidence"]
    for key in required_keys:
        if key not in parsed:
            parsed[key] = fallback[key]
    return parsed
