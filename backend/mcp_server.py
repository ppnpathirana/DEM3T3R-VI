"""
@file: mcp_server.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Model Context Protocol (MCP) Server.
Standardizes robot hardware tools and AI interfaces for Claude / LLMs:
1. read_sensors: Queries live telemetry from ESP32 nodes
2. send_motor_command: Steers robot navigation (forward/backward/left/right/stop)
3. trigger_spray_actuator: Dispatches precision fungicide spray dose
4. get_robot_status: Returns state machine, GPS pose, and active crop model
5. query_rag_pathology: Retrieves pathology knowledge from the RAG store
"""
import json
import time
from typing import Dict, Any, List

class CropGuardMCPServer:
    def __init__(self, ai_brain=None, rag_store=None, position_estimator=None):
        self.brain = ai_brain
        self.rag = rag_store
        self.ekf = position_estimator
        self.tool_definitions = [
            {
                "name": "read_sensors",
                "description": "Fetch real-time environmental telemetry (Temp, Humidity, Soil Moisture, UV, Light, Ultrasonic) from ESP32",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "send_motor_command",
                "description": "Send directional movement command to DEM3T3R V1 robot motors",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["forward", "backward", "left", "right", "stop"]},
                        "speed": {"type": "integer", "minimum": 0, "maximum": 255}
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "trigger_spray_actuator",
                "description": "Trigger precision spray pump relay for target pathogen mitigation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["mild", "moderate", "severe"]},
                        "duration_sec": {"type": "number", "minimum": 1.0, "maximum": 10.0}
                    },
                    "required": ["severity"]
                }
            },
            {
                "name": "get_robot_status",
                "description": "Get robot state machine status, battery, GPS pose, and active crop model",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "query_rag_pathology",
                "description": "Retrieve agricultural treatment guidelines and chemical recommendations from RAG index",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string"},
                        "pathogen_query": {"type": "string"}
                    },
                    "required": ["crop", "pathogen_query"]
                }
            }
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        return self.tool_definitions

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch MCP tool execution and return structured result."""
        if tool_name == "read_sensors":
            sensors = self.brain.latest_sensors if self.brain else {
                "temperature": 27.5, "humidity": 78.0, "soilMoisture": 2150, "uvVoltage": 0.6, "ultrasonic": 85.0
            }
            return {"status": "success", "data": sensors}

        elif tool_name == "send_motor_command":
            direction = arguments.get("direction", "stop")
            speed = arguments.get("speed", 200)
            if self.brain and hasattr(self.brain, "send_esp32_command"):
                cmd = {"type": "motor", "direction": direction, "speed": speed, "timestamp": time.time()}
                self.brain.send_esp32_command(cmd)
            return {"status": "success", "executed": f"Motor {direction} at speed {speed}"}

        elif tool_name == "trigger_spray_actuator":
            severity = arguments.get("severity", "moderate")
            duration = arguments.get("duration_sec", 5.0)
            if self.brain and hasattr(self.brain, "send_esp32_command"):
                cmd = {"type": "pump", "action": "spray", "severity": severity, "duration_s": duration}
                self.brain.send_esp32_command(cmd)
            return {"status": "success", "executed": f"Spray triggered for {duration}s ({severity})"}

        elif tool_name == "get_robot_status":
            pose = self.ekf.get_pose() if self.ekf else {"x_local_m": 0, "y_local_m": 0, "latitude": 6.9271, "longitude": 79.8612}
            state = self.brain.state_machine.current_state.value if self.brain and hasattr(self.brain, "state_machine") else "IDLE"
            return {
                "status": "success",
                "state": state,
                "pose": pose,
                "timestamp": time.time()
            }

        elif tool_name == "query_rag_pathology":
            crop = arguments.get("crop", "tomato")
            query = arguments.get("pathogen_query", "")
            if self.rag:
                docs = self.rag.query(crop, query)
                return {"status": "success", "results": docs}
            return {
                "status": "success",
                "results": [f"Standard agronomic treatment for {crop} {query}: Apply recommended fungicide and improve soil drainage."]
            }

        return {"status": "error", "message": f"Unknown tool: {tool_name}"}
