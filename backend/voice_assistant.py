"""
@file: voice_assistant.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 Precision AI Voice Assistant.
Edge-ready NLP intent recognition and voice command dispatcher for DEM3T3R V1 robot.

Supports 10 core autonomous agricultural robot actions:
1. MOVE_FORWARD
2. MOVE_BACKWARD
3. TURN_LEFT
4. TURN_RIGHT
5. EMERGENCY_STOP
6. SPRAY_PUMP
7. SOIL_PROBE
8. STATUS_QUERY
9. MODE_AUTO
10. MODE_MANUAL

Provides natural language vocalization feedback in international English.
"""
import time
from typing import Dict, Any, Optional, Tuple


class TrilingualVoiceAssistant:
    """
    Precision Voice Assistant for Autonomous Agricultural Rover.
    Maintains class name for backward compatibility while delivering 100% English precision.
    """
    def __init__(self, ai_brain=None, command_callback=None):
        self.ai_brain = ai_brain
        self.command_callback = command_callback
        
        # Comprehensive Keyword & Synonym Intent Dictionaries
        self.intent_patterns = {
            "MOVE_FORWARD": {
                "en": [
                    "forward", "move forward", "go forward", "advance", "drive forward",
                    "straight", "go straight", "ahead", "proceed", "drive ahead", "accelerate"
                ]
            },
            "MOVE_BACKWARD": {
                "en": [
                    "backward", "move backward", "reverse", "go back", "back up",
                    "backwards", "drive back", "retreat"
                ]
            },
            "TURN_LEFT": {
                "en": [
                    "turn left", "left", "steer left", "rotate left", "pivot left", "go left", "bearing left"
                ]
            },
            "TURN_RIGHT": {
                "en": [
                    "turn right", "right", "steer right", "rotate right", "pivot right", "go right", "bearing right"
                ]
            },
            "EMERGENCY_STOP": {
                "en": [
                    "stop", "halt", "emergency stop", "brake", "freeze", "kill motor",
                    "pause", "hold on", "standby", "abort", "cut power"
                ]
            },
            "SPRAY_PUMP": {
                "en": [
                    "spray", "pump", "start spray", "apply spray", "fungicide", "mist",
                    "spray pump", "turn on pump", "water spray", "pesticide spray", "solenoid spray"
                ]
            },
            "SOIL_PROBE": {
                "en": [
                    "soil probe", "check soil", "soil moisture", "soil test", "measure soil",
                    "soil sensor", "probe soil", "ground moisture"
                ]
            },
            "STATUS_QUERY": {
                "en": [
                    "status", "report", "robot status", "system status", "diagnostics",
                    "battery level", "sensor report", "telemetry", "health check"
                ]
            },
            "MODE_AUTO": {
                "en": [
                    "auto", "auto mode", "autonomous", "start mission", "autonomous mode",
                    "waypoint mode", "start auto", "self drive"
                ]
            },
            "MODE_MANUAL": {
                "en": [
                    "manual", "manual mode", "rc mode", "joystick mode", "hand control",
                    "user control", "take control", "stop auto"
                ]
            }
        }
        
        self.response_templates = {
            "MOVE_FORWARD": {
                "en": "Moving forward."
            },
            "MOVE_BACKWARD": {
                "en": "Reversing backward."
            },
            "TURN_LEFT": {
                "en": "Turning left."
            },
            "TURN_RIGHT": {
                "en": "Turning right."
            },
            "EMERGENCY_STOP": {
                "en": "Emergency stop activated. All motors halted."
            },
            "SPRAY_PUMP": {
                "en": "Precision spray pump engaged for 5 seconds."
            },
            "SOIL_PROBE": {
                "en": "Lowering soil probes and sampling moisture levels."
            },
            "STATUS_QUERY": {
                "en": "System active. All sensor telemetry nominal."
            },
            "MODE_AUTO": {
                "en": "Autonomous field inspection mode engaged."
            },
            "MODE_MANUAL": {
                "en": "Switched to manual joystick control mode."
            },
            "UNKNOWN": {
                "en": "Sorry, command not recognized. Please repeat."
            }
        }

    def detect_language(self, text: str) -> str:
        """Always return 'en' as standard international language."""
        return "en"

    def parse_intent(self, text: str, preferred_lang: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Extract robotic intent from input text with confidence scoring.
        Returns: (intent_name, confidence, detected_language)
        """
        clean_text = text.lower().strip()
        if not clean_text:
            return "UNKNOWN", 0.0, "en"
            
        detected_lang = "en"
        best_intent = "UNKNOWN"
        max_confidence = 0.0

        for intent, lang_dict in self.intent_patterns.items():
            for lang, keywords in lang_dict.items():
                for kw in keywords:
                    if kw in clean_text:
                        # Confidence based on match ratio
                        conf = min(0.95, 0.70 + (len(kw) / max(len(clean_text), 1)) * 0.25)
                        if conf > max_confidence:
                            max_confidence = conf
                            best_intent = intent
                            
        # If no direct keyword match, check AI Brain / fallback
        if best_intent == "UNKNOWN" and self.ai_brain:
            try:
                # Optional LLM fallback
                pass
            except Exception:
                pass
                
        return best_intent, max_confidence if max_confidence > 0 else 0.0, detected_lang

    def execute_command(self, text: str, user_lang: Optional[str] = "en") -> Dict[str, Any]:
        """
        End-to-end voice command execution pipeline.
        Parses intent, triggers robotic actuators, and provides localized response.
        """
        t_start = time.time()
        intent, conf, detected_lang = self.parse_intent(text, user_lang)
        lang = "en"
        
        executed = False
        action_payload = None

        if conf >= 0.50 and intent != "UNKNOWN":
            action_payload = self._map_intent_to_action(intent)
            if self.command_callback and action_payload:
                try:
                    executed = self.command_callback(intent, action_payload) is not False
                except Exception as e:
                    print(f"[VoiceAssistant] Execution error: {e}")
            else:
                executed = True

        resp_text = self.response_templates.get(intent, {}).get(lang, self.response_templates["UNKNOWN"][lang])
        if action_payload and not executed:
            resp_text = 'Command was not delivered. Check the robot connection and emergency stop status.'

        return {
            "query": text,
            "intent": intent,
            "confidence": round(conf, 2),
            "language": lang,
            "executed": executed,
            "action": action_payload,
            "response_text": resp_text,
            "latency_ms": round((time.time() - t_start) * 1000, 2),
            "timestamp": time.time()
        }

    def _map_intent_to_action(self, intent: str) -> Dict[str, Any]:
        """Maps recognized intent to low-level rover hardware commands."""
        actions = {
            "MOVE_FORWARD": {"cmd": "DRIVE", "left": 180, "right": 180, "duration": 1.5},
            "MOVE_BACKWARD": {"cmd": "DRIVE", "left": -180, "right": -180, "duration": 1.5},
            "TURN_LEFT": {"cmd": "DRIVE", "left": -150, "right": 150, "duration": 0.8},
            "TURN_RIGHT": {"cmd": "DRIVE", "left": 150, "right": -150, "duration": 0.8},
            "EMERGENCY_STOP": {"cmd": "STOP", "hard_brake": True},
            "SPRAY_PUMP": {"cmd": "RELAY", "relay": 1, "state": "ON", "duration": 5.0},
            "SOIL_PROBE": {"cmd": "STAGING_PROBE", "relays": [2, 3], "duration": 10.0},
            "STATUS_QUERY": {"cmd": "GET_TELEMETRY"},
            "MODE_AUTO": {"cmd": "SET_MODE", "mode": "AUTO"},
            "MODE_MANUAL": {"cmd": "SET_MODE", "mode": "MANUAL"}
        }
        return actions.get(intent, {})
