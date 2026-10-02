"""
@file: command_generator.py
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
import time
from config.settings import OLLAMA_MODEL_CODER, OLLAMA_API_URL, GEMINI_KEYS, GROK_KEY

_last_internet_check = 0.0
_internet_cache = False

def is_online() -> bool:
    """Checks internet connectivity with a cached result to avoid blocking."""
    global _last_internet_check, _internet_cache
    now = time.time()
    if now - _last_internet_check > 15.0:
        _last_internet_check = now
        try:
            requests.get("https://www.google.com", timeout=1.0)
            _internet_cache = True
        except Exception:
            _internet_cache = False
    return _internet_cache

def generate_robot_commands(analysis: dict, robot_state: dict) -> dict:
    """
    Input: Disease analysis from vision model, current robot state
    Output: {
        "motor_left": int,           # 0-255 PWM
        "motor_right": int,          # 0-255 PWM
        "solenoid_action": "insert_probe" | "retract" | "none",
        "pump_action": "spray" | "off",
        "pump_duration_sec": float,
        "next_state": "ACTING" | "SCANNING" | "SAFE_STOP"
    }
    """
    # Strict fallback in case LLM output is malformed or times out
    fallback = {
        "motor_left": 0,
        "motor_right": 0,
        "solenoid_action": "insert_probe",
        "pump_action": "spray",
        "pump_duration_sec": float(analysis.get("treatment_duration_sec", 5)),
        "next_state": "ACTING"
    }

    # If the analysis indicates retracting the probe, adjust defaults
    if robot_state.get("solenoid_inserted") and not robot_state.get("treatment_completed"):
        fallback["solenoid_action"] = "retract"
        fallback["pump_action"] = "off"
        fallback["next_state"] = "SCANNING"

    prompt = f"""You are a robot controller compiler for the DEM3T3R V1 robot.
You must compile low level actuator commands in JSON format based on the following input:

Disease Analysis: {json.dumps(analysis)}
Current Robot State: {json.dumps(robot_state)}

Actuator JSON specifications:
- "motor_left": Integer (0 to 255 PWM speed. Set to 0 if treating/stopping)
- "motor_right": Integer (0 to 255 PWM speed. Set to 0 if treating/stopping)
- "solenoid_action": String ("insert_probe" | "retract" | "none")
- "pump_action": String ("spray" | "off")
- "pump_duration_sec": Float (duration of spray treatment in seconds, matched with analysis)
- "next_state": String ("ACTING" | "SCANNING" | "SAFE_STOP")

Guidelines:
1. If the robot detects a disease (confidence > 0.70) and has NOT inserted the soil probe, you must set motor_left/right to 0, solenoid_action to "insert_probe", pump_action to "off", and next_state to "ACTING".
2. If the probe is already inserted ("solenoid_inserted": true) and pump has not sprayed yet, set solenoid_action to "none", pump_action to "spray", and next_state to "ACTING".
3. If treatment is done ("treatment_completed": true), you must retract the probe: set solenoid_action to "retract", pump_action to "off", and next_state to "SCANNING" to resume patrol.

Return ONLY the raw valid JSON payload, no markdown blocks, no commentary."""

    online = is_online()
    print(f"[COMMAND GENERATOR] Internet connectivity status: {'ONLINE' if online else 'OFFLINE (Skip Cloud)'}")

    if online:
        # ----------------------------------------------------
        # PHASE 1: Rotate through Gemini Keys
        # ----------------------------------------------------
        for idx, key in enumerate(GEMINI_KEYS):
            if not key or "your-" in key:
                continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
                print(f"[COMMAND GENERATOR] Trying Gemini API (Key {idx+1}/{len(GEMINI_KEYS)})...")
                
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
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
                    print(f"[COMMAND GENERATOR] ✅ Gemini API Key {idx+1} Success!")
                    return validate_and_repair(parsed, fallback)
                else:
                    print(f"[COMMAND GENERATOR] ⚠️ Gemini API Key {idx+1} returned code {response.status_code}")
            except Exception as e:
                print(f"[COMMAND GENERATOR] ❌ Gemini API Key {idx+1} Error: {e}")

        # ----------------------------------------------------
        # PHASE 2: Fallback to Groq API
        # ----------------------------------------------------
        if GROK_KEY and "your-" not in GROK_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                print("[COMMAND GENERATOR] Trying Groq API...")
                
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
                    print("[COMMAND GENERATOR] ✅ Groq API Success!")
                    return validate_and_repair(parsed, fallback)
                else:
                    print(f"[COMMAND GENERATOR] ⚠️ Groq API returned code {response.status_code}")
            except Exception as e:
                print(f"[COMMAND GENERATOR] ❌ Groq API Error: {e}")

    # ----------------------------------------------------
    # PHASE 3: Fallback to Local Coder (Ollama Qwen2.5-Coder)
    # ----------------------------------------------------
    try:
        url = f"{OLLAMA_API_URL}/api/chat"
        print(f"[COMMAND GENERATOR] Falling back to Local Coder ({OLLAMA_MODEL_CODER})...")
        
        payload = {
            "model": OLLAMA_MODEL_CODER,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "options": {
                "temperature": 0.1
            },
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            result_data = response.json()
            message_content = result_data.get("message", {}).get("content", "").strip()
            parsed = json.loads(message_content)
            print("[COMMAND GENERATOR] ✅ Local Coder Success!")
            return validate_and_repair(parsed, fallback)
    except Exception as e:
        print(f"[COMMAND GENERATOR] ❌ Local Coder Error: {e}")

    print("[COMMAND GENERATOR] ⚠️ All models failed. Returning fallback commands.")
    return fallback

def validate_and_repair(parsed: dict, fallback: dict) -> dict:
    parsed["motor_left"] = int(parsed.get("motor_left", fallback["motor_left"]))
    parsed["motor_right"] = int(parsed.get("motor_right", fallback["motor_right"]))
    
    if parsed.get("solenoid_action") not in ["insert_probe", "retract", "none"]:
        parsed["solenoid_action"] = fallback["solenoid_action"]
        
    if parsed.get("pump_action") not in ["spray", "off"]:
        parsed["pump_action"] = fallback["pump_action"]
        
    parsed["pump_duration_sec"] = float(parsed.get("pump_duration_sec", fallback["pump_duration_sec"]))
    
    if parsed.get("next_state") not in ["ACTING", "SCANNING", "SAFE_STOP"]:
        parsed["next_state"] = fallback["next_state"]
        
    return parsed
