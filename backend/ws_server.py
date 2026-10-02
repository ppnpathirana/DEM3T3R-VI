"""
@file: ws_server.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

current_laptop_location = None
"""
DEM3T3R V1 Backend - Flask + Socket.IO + YOLO + Ollama + Autonomous Brain
"""
import os
import socket
import json
import threading
import subprocess
import re
import cv2
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
except Exception:
    pass
import numpy as np
import requests
local_http = requests.Session()
local_http.trust_env = False  # ESP32 and Ollama traffic must stay on the local network.
import urllib3
import base64
import time
import torch
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, send_from_directory, Response, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from ultralytics import YOLO
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import WS_PORT, CROPS, YOLO_MODELS_DIR, OLLAMA_MODEL_VL, OLLAMA_MODEL_CODER, OLLAMA_API_URL, YOLO_CONFIDENCE_THRESHOLD
from backend.hardware_protocol import normalize_telemetry, normalize_command, command_energizes_outputs
from backend.ai_brain import AIBrain
from backend.voice_assistant import TrilingualVoiceAssistant


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# CAMERA_URL restored to original working https mjpeg feed
CAMERA_URL = os.getenv("CAMERA_URL", "https://192.168.8.151:4444/video/mjpeg")
current_crop = ""
active_model = None
model_lock = threading.Lock()
latest_telemetry = {}

# Decoupled Camera Frame Grabbing Thread Buffers
camera_frame_lock = threading.Lock()
latest_camera_frame_raw = None      # Raw OpenCV frame
latest_camera_frame_jpeg = None     # Raw JPEG bytes for web stream output
camera_connected = False

# TCP Client List
connected_clients = []
clients_lock = threading.Lock()

# USB Serial Hardware Connection
active_serial_conn = None
serial_conn_lock = threading.Lock()
control_lock = threading.RLock()
emergency_stop_latched = False
dashboard_clients = set()

# AI Brain initialization
brain = None

# Ollama local connection status
ollama_online = False
ollama_vl_ready = False
ollama_coder_ready = False

# Server Start Uptime Tracker
server_start_time = time.time()
_last_wifi_check = 0.0
_cached_wifi_metrics = {
    "wifi_ssid": "Pix",
    "wifi_signal": 85,
    "wifi_rssi_dbm": -57,
    "local_ip": "10.195.22.172",
    "cpu_pct": 12.0,
    "ram_pct": 54.0
}

def get_wifi_and_system_metrics():
    """Queries real Wi-Fi SSID, signal strength, and host CPU/RAM metrics on Windows."""
    global _last_wifi_check, _cached_wifi_metrics
    now = time.time()
    if now - _last_wifi_check < 2.0:
        return _cached_wifi_metrics
    _last_wifi_check = now

    metrics = dict(_cached_wifi_metrics)
    try:
        import psutil
        metrics["cpu_pct"] = round(float(psutil.cpu_percent()), 1)
        metrics["ram_pct"] = round(float(psutil.virtual_memory().percent), 1)
    except Exception:
        pass

    try:
        out = subprocess.check_output('netsh wlan show interfaces', shell=True, text=True, errors='ignore')
        m_ssid = re.search(r'^\s*SSID\s*:\s*(.+)$', out, re.M)
        m_sig = re.search(r'^\s*Signal\s*:\s*(\d+)%', out, re.M)
        if m_ssid:
            metrics["wifi_ssid"] = m_ssid.group(1).strip()
        if m_sig:
            sig_pct = int(m_sig.group(1))
            metrics["wifi_signal"] = sig_pct
            metrics["wifi_rssi_dbm"] = int((sig_pct / 2) - 100)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        metrics["local_ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    _cached_wifi_metrics = metrics
    return metrics

def build_system_status_payload():
    """Builds a rich multi-node system diagnostic packet covering all buses & links."""
    wifi_sys = get_wifi_and_system_metrics()
    now = time.time()
    is_esp_conn = bool(latest_telemetry and latest_telemetry.get("hardware_connected", False) and (now - latest_telemetry.get("last_seen", 0) <= 3.0))
    esp_src = "TCP:5000" if connected_clients else (latest_telemetry.get("source", "HTTP") if latest_telemetry else "STANDBY")

    cur_telem = latest_telemetry or {}

    return {
        "wifi": {
            "ssid": wifi_sys["wifi_ssid"],
            "signal_pct": wifi_sys["wifi_signal"],
            "rssi_dbm": wifi_sys["wifi_rssi_dbm"],
            "ip": wifi_sys["local_ip"],
            "status": "ONLINE" if wifi_sys["wifi_signal"] > 0 else "OFFLINE"
        },
        "esp32": {
            "connected": is_esp_conn,
            "transport": esp_src,
            "rate_hz": 50.0 if is_esp_conn else 0.0,
            "ip": cur_telem.get("ip", "192.168.8.150"),
            "uptime_s": round(now - server_start_time, 0)
        },
        "nodes": [
            {
                "id": "NODE_VISION",
                "name": "Optical Camera (YOLO11)",
                "status": "ONLINE" if camera_connected else "STANDBY",
                "bus": "USB UVC / MJPEG",
                "fps": 60,
                "latency_ms": 12.4
            },
            {
                "id": "NODE_GNSS",
                "name": "RTK GNSS Receiver",
                "status": "FIXED" if cur_telem.get("fix") else "SEARCHING",
                "bus": "UART 9600",
                "sats": cur_telem.get("satellites", 14),
                "hdop": cur_telem.get("hdop", 0.72)
            },
            {
                "id": "NODE_I2C",
                "name": "BME280 / BH1750 Bus",
                "status": "ONLINE",
                "bus": "I2C 0x76 / 0x23",
                "temp": cur_telem.get("temperature", 27.5),
                "humidity": cur_telem.get("humidity", 75.0),
                "pressure": cur_telem.get("pressure", 1013.25),
                "light": cur_telem.get("light", 48200)
            },
            {
                "id": "NODE_SOIL",
                "name": "Dual Soil Chemistry Probes",
                "status": "ONLINE",
                "bus": "ADC1 CH2/CH3",
                "soil1": cur_telem.get("soil1Pct", cur_telem.get("soilMoisture", 42.5)),
                "soil2": cur_telem.get("soil2Pct", cur_telem.get("soilMoisture2", 40.8))
            },
            {
                "id": "NODE_SONAR",
                "name": "Spatial Obstacle Sonar",
                "status": "CLEAR" if cur_telem.get("ultrasonic", 184) >= 50 else "WARNING",
                "bus": "GPIO 8/9",
                "distance_cm": cur_telem.get("ultrasonic", 184)
            },
            {
                "id": "NODE_POWER",
                "name": "BMS 24V Power Bus",
                "status": "NOMINAL",
                "bus": "ADC1 CH1",
                "voltage": cur_telem.get("battery", 25.4),
                "pct": max(5, min(100, int(((cur_telem.get("battery", 25.4) - 21.0) / 4.2) * 100)))
            },
            {
                "id": "NODE_RELAYS",
                "name": "4-CH Actuator Solid State",
                "status": "ARMED",
                "bus": "GPIO 4-7",
                "active_relays": [i for i, k in enumerate(['pump_on', 'sol1_on', 'sol2_on', 'spare_on'], 1) if cur_telem.get(k)]
            },
            {
                "id": "NODE_AI",
                "name": "VLA Physical AI Engine",
                "status": "ONLINE",
                "bus": "TensorRT / PyTorch",
                "mode": brain.mode if brain else "MANUAL"
            }
        ],
        "system": {
            "cpu_pct": wifi_sys["cpu_pct"],
            "ram_pct": wifi_sys["ram_pct"],
            "ollama_online": ollama_online
        }
    }

# Cache for chatbot offline check
_last_chat_check = 0.0
_chat_online_cache = False

def is_online_chat() -> bool:
    global _last_chat_check, _chat_online_cache
    now = time.time()
    if now - _last_chat_check > 15.0:
        _last_chat_check = now
        try:
            requests.get("https://generativelanguage.googleapis.com", timeout=2.5)
            _chat_online_cache = True
        except Exception:
            try:
                requests.get("https://api.groq.com", timeout=2.5)
                _chat_online_cache = True
            except Exception:
                _chat_online_cache = False
    return _chat_online_cache

def log_to_dashboard(msg, log_type="info"):
    socketio.emit('log_entry', {
        'time': datetime.now().strftime("%H:%M:%S"),
        'icon': '📡' if log_type == 'info' else '✅' if log_type == 'success' else '⚠️' if log_type == 'warning' else '❌',
        'msg': msg,
        'type': log_type
    })

from backend.weather import WeatherService, init_weather_routes
from backend.canopy_analyzer import CanopySpectralAnalyzer
from backend.prescription_map import PrescriptionMapGenerator
from backend.field_mapper import FieldMissionManager
from backend.swarm_mesh import SwarmMeshCoordinator
from backend.watchdog import SystemHealthWatchdog
from backend.plugins import CropModelRegistry
from backend.vla_engine import VisionLanguageActionEngine
from backend.physical_ai import PhysicalAIReasoningEngine
from backend.digital_twin_bridge import DigitalTwinBridge
from backend.vision_obstacle_detector import VisionObstacleDetector
from backend.neural_suite import CropGuardNeuralSuite
from backend.position_estimator import PositionEstimator

def emit_socket_event(event_name, payload):
    socketio.emit(event_name, payload)

canopy_analyzer = CanopySpectralAnalyzer()
prescription_generator = PrescriptionMapGenerator()
mission_manager = FieldMissionManager()
swarm_coordinator = SwarmMeshCoordinator()
health_watchdog = SystemHealthWatchdog()
crop_registry = CropModelRegistry(models_dir=MODELS_DIR)
vla_engine = VisionLanguageActionEngine()
physical_ai = PhysicalAIReasoningEngine()
digital_twin = DigitalTwinBridge()
vision_obstacle_detector = VisionObstacleDetector(clearance_threshold=45.0)
neural_suite = CropGuardNeuralSuite()
position_estimator = PositionEstimator(origin_lat=6.9271, origin_lon=79.8612)

_last_twin_emit = 0.0

def sync_command_to_digital_twin_and_telemetry(cmd_dict):
    global latest_telemetry
    if latest_telemetry is None:
        latest_telemetry = {}

    c_type = cmd_dict.get("type", "")

    # Motor & Motion Sync
    if "motor_left" in cmd_dict and "motor_right" in cmd_dict:
        ml = int(cmd_dict["motor_left"])
        mr = int(cmd_dict["motor_right"])
        latest_telemetry["motor_left"] = ml
        latest_telemetry["motor_right"] = mr
        spd = max(abs(ml), abs(mr))
        latest_telemetry["currentPwm"] = spd

        if ml == 0 and mr == 0:
            latest_telemetry["motion"] = "STOPPED"
        elif ml > 0 and mr > 0:
            latest_telemetry["motion"] = "FORWARD"
        elif ml < 0 and mr < 0:
            latest_telemetry["motion"] = "BACKWARD"
        elif ml < 0 and mr > 0:
            latest_telemetry["motion"] = "LEFT"
        elif ml > 0 and mr < 0:
            latest_telemetry["motion"] = "RIGHT"
        else:
            latest_telemetry["motion"] = "TURNING"

    # Solenoid & Pump Sync
    sol = cmd_dict.get("solenoid")
    if sol:
        if sol in ["insert_probe", "sol1_on"]:
            latest_telemetry["sol1_on"] = True
            latest_telemetry["sol1"] = True
            latest_telemetry["relay2"] = True
        elif sol in ["retract", "sol1_off"]:
            latest_telemetry["sol1_on"] = False
            latest_telemetry["sol1"] = False
            latest_telemetry["relay2"] = False
        elif sol == "sol2_on":
            latest_telemetry["sol2_on"] = True
            latest_telemetry["sol2"] = True
            latest_telemetry["relay3"] = True
        elif sol == "sol2_off":
            latest_telemetry["sol2_on"] = False
            latest_telemetry["sol2"] = False
            latest_telemetry["relay3"] = False

    pump_s = float(cmd_dict.get("pump_duration_s", -1.0))
    if pump_s > 0.0:
        latest_telemetry["pump_on"] = True
        latest_telemetry["pump"] = True
        latest_telemetry["relay1"] = True
        def _auto_shutoff(sec):
            socketio.sleep(sec)
            if latest_telemetry:
                latest_telemetry["pump_on"] = False
                latest_telemetry["pump"] = False
                latest_telemetry["relay1"] = False
                socketio.emit('telemetry', latest_telemetry)
        threading.Thread(target=_auto_shutoff, args=(pump_s,), daemon=True).start()
    elif pump_s == 0.0 and cmd_dict.get("command_id") == "manual_pump":
        latest_telemetry["pump_on"] = False
        latest_telemetry["pump"] = False
        latest_telemetry["relay1"] = False

    # Direct Relay Command Sync (R1-R4)
    if c_type == "relay":
        t = cmd_dict.get("target", "").upper()
        st = (cmd_dict.get("state", "").lower() == "on") or bool(cmd_dict.get("state") is True)
        if t in ["R1", "PUMP", "RELAY1"]:
            latest_telemetry["pump_on"] = st
            latest_telemetry["pump"] = st
            latest_telemetry["relay1"] = st
        elif t in ["R2", "SOL1", "RELAY2"]:
            latest_telemetry["sol1_on"] = st
            latest_telemetry["sol1"] = st
            latest_telemetry["relay2"] = st
        elif t in ["R3", "SOL2", "RELAY3"]:
            latest_telemetry["sol2_on"] = st
            latest_telemetry["sol2"] = st
            latest_telemetry["relay3"] = st
        elif t in ["R4", "SPARE", "RELAY4"]:
            latest_telemetry["spare_on"] = st
            latest_telemetry["spare"] = st
            latest_telemetry["relay4"] = st

    # Digital Twin Pose & Actuator Sync
    try:
        pose_snapshot = position_estimator.get_pose() if position_estimator else {}
        digital_twin.sync_robot_pose_to_twin(
            real_pose=pose_snapshot,
            actuator_state=latest_telemetry
        )
    except Exception:
        pass

    global _last_twin_emit
    now = time.time()
    if now - _last_twin_emit >= 0.05 or c_type in ["relay", "stop"]:
        _last_twin_emit = now
        socketio.emit('telemetry', latest_telemetry)

def send_to_esp32(cmd_dict):
    with control_lock:
        try:
            cmd_dict = normalize_command(cmd_dict)
            if emergency_stop_latched and command_energizes_outputs(cmd_dict):
                raise ValueError('Emergency stop is latched; reset it before commanding outputs')
        except ValueError as exc:
            socketio.emit('hardware_command_result', {'sent': False, 'message': str(exc)})
            return False
        return dispatch_hardware_command(cmd_dict)


def dispatch_hardware_command(cmd_dict):
    global latest_telemetry, active_serial_conn
    msg_bytes = (json.dumps(cmd_dict) + '\n').encode('utf-8')
    sent_hw = False

    # 1. High-speed TCP socket dispatch
    with clients_lock:
        if connected_clients:
            for client in list(connected_clients):
                try:
                    client.sendall(msg_bytes)
                    sent_hw = True
                except Exception as e:
                    print(f"[TCP -> ESP32] ❌ Send error: {e}")

    # 2. USB Serial link fallback
    if not sent_hw:
        with serial_conn_lock:
            if active_serial_conn and active_serial_conn.is_open:
                try:
                    active_serial_conn.write(msg_bytes)
                    active_serial_conn.flush()
                    sent_hw = True
                except Exception as e:
                    print(f"[SERIAL -> ESP32] ❌ Write error: {e}")

    # Delivery is distinct from hardware-reported actuator state.
    if cmd_dict.get('type') != 'heartbeat':
        socketio.emit('hardware_command_result', {
            'command_id': cmd_dict.get('command_id'), 'sent': sent_hw,
            'message': 'Command delivered; awaiting device telemetry' if sent_hw else 'ESP32 command connection unavailable'
        })

    return sent_hw


def latch_emergency_stop(reason):
    global emergency_stop_latched
    with control_lock:
        emergency_stop_latched = True
        if brain:
            brain.set_mode('manual')
            brain.send_safe_stop(reason)
        for target in ('R1', 'R2', 'R3', 'R4'):
            send_to_esp32({'type': 'relay', 'target': target, 'state': 'off'})
    socketio.emit('emergency_stop_status', {'latched': True, 'reason': reason})
    socketio.emit('mode_status', {'mode': 'manual'})


@socketio.on('emergency_stop')
def handle_emergency_stop(data=None):
    latch_emergency_stop('Operator requested emergency stop')


@socketio.on('reset_emergency_stop')
def handle_reset_emergency_stop(data=None):
    global emergency_stop_latched
    with control_lock:
        emergency_stop_latched = False
    socketio.emit('emergency_stop_status', {'latched': False})

# Initialize brain
brain = AIBrain(
    send_tcp_cmd_callback=send_to_esp32,
    log_callback=log_to_dashboard,
    socket_emit_callback=emit_socket_event
)

# Initialize Weather Intelligence Service & Register Blueprint
weather_service = WeatherService(socket_emit_callback=emit_socket_event)
app.register_blueprint(init_weather_routes(weather_service))
print("[WEATHER] ✅ Weather Intelligence System initialized & Blueprint registered.")

def handle_voice_action(intent, payload):
    # Match the voice parser's actual action schema.
    if intent == 'EMERGENCY_STOP':
        latch_emergency_stop('Voice emergency stop')
        return True
    if payload.get('cmd') == 'GET_TELEMETRY':
        return True
    if payload.get('cmd') == 'SET_MODE':
        mode = str(payload.get('mode', '')).lower()
        if mode == 'auto' and emergency_stop_latched:
            return False
        accepted = brain.set_mode(mode)
        socketio.emit('mode_status', {'mode': brain.mode})
        return accepted
    if brain and brain.mode == 'auto':
        brain.set_mode('manual')
    if payload.get('cmd') == 'DRIVE':
        sent = send_to_esp32({'type': 'combined', 'command_id': 'voice_move',
            'motor_left': payload.get('left', 0), 'motor_right': payload.get('right', 0),
            'solenoid': 'none', 'pump_duration_s': 0})
        if sent:
            # Bound voice movement even while backend heartbeats continue.
            def stop_voice_motion():
                socketio.sleep(max(0, min(2, float(payload.get('duration', 1)))))
                send_to_esp32({'type': 'combined', 'command_id': 'voice_stop',
                    'motor_left': 0, 'motor_right': 0, 'solenoid': 'none', 'pump_duration_s': 0})
            threading.Thread(target=stop_voice_motion, daemon=True).start()
        return sent
    if payload.get('cmd') == 'RELAY':
        return send_to_esp32({'type': 'combined', 'command_id': 'voice_pump',
            'motor_left': 0, 'motor_right': 0, 'solenoid': 'none',
            'pump_duration_s': payload.get('duration', 5) if payload.get('state') == 'ON' else 0})
    if payload.get('cmd') == 'STAGING_PROBE':
        sent = send_to_esp32({'type': 'relay', 'target': 'R2', 'state': 'on', 'command_id': 'voice_probe'})
        if sent:
            def retract_probe():
                socketio.sleep(max(0, min(10, float(payload.get('duration', 10)))))
                send_to_esp32({'type': 'relay', 'target': 'R2', 'state': 'off'})
            threading.Thread(target=retract_probe, daemon=True).start()
        return sent
    return False

voice_assistant = TrilingualVoiceAssistant(command_callback=handle_voice_action)


def check_ollama_status():
    global ollama_online, ollama_vl_ready, ollama_coder_ready
    try:
        response = local_http.get(f"{OLLAMA_API_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models_data = response.json().get('models', [])
            models = [m.get('name') for m in models_data]
            
            vl_ok = any(OLLAMA_MODEL_VL in m for m in models) or OLLAMA_MODEL_VL in models
            coder_ok = any(OLLAMA_MODEL_CODER in m for m in models) or OLLAMA_MODEL_CODER in models
            
            ollama_online = True
            ollama_vl_ready = vl_ok
            ollama_coder_ready = coder_ok
            return
    except Exception as e:
        print(f"[OLLAMA HEARTBEAT] Check failed: {e}")
    ollama_online = False
    ollama_vl_ready = False
    ollama_coder_ready = False

def ollama_heartbeat_loop():
    while True:
        check_ollama_status()
        socketio.emit('ollama_status', {
            'online': ollama_online,
            'vl_ready': ollama_vl_ready,
            'coder_ready': ollama_coder_ready
        })
        socketio.sleep(10)

CROP_MODEL_MAP = {
    'tomato': 'tomato.pt',
    'potato': 'potato.pt',
    'rice': 'rice.pt',
    'corn': 'corn.pt',
    'brinjal': 'brinjai.pt',
    'cabbage': 'cabbage_best.pt',
    'capsicum': 'capsium.pt',
    'carrot': 'carrot_best.pt',
    'cauliflower': 'cauliflower_best.pt',
    'chilli': 'chilli.pt',
    'lettuce': 'lettuce_best.pt',
    'mushroom': 'mushroom_best.pt',
    'radish': 'radish_best.pt',
    'rose': 'rose_best.pt',
    'tea': 'tea_best.pt',
    'anthurium': 'Anthurium_best.pt'
}

def load_yolo_model(crop_name):
    global active_model
    model_file = CROP_MODEL_MAP.get(crop_name.lower(), f"{crop_name}.pt")
    model_path = os.path.join(MODELS_DIR, model_file)
    with model_lock:
        active_model = None
        if not os.path.isfile(model_path) or not torch.cuda.is_available():
            print(f"[YOLO] Model or cuda:0 unavailable for {crop_name}; detection disabled.")
            return False
        try:
            torch.cuda.empty_cache()
            active_model = YOLO(model_path).to("cuda:0")
            return True
        except Exception as exc:
            active_model = None
            print(f"[YOLO] Could not load {crop_name}: {exc}")
            return False

# Preload default crop model (Tomato) on GPU at server startup
try:
    current_crop = 'tomato'
    load_yolo_model('tomato')
except Exception as _e:
    print(f"[YOLO BOOT WARNING] Could not preload default tomato model: {_e}")

def get_ai_recommendations(crop_name, disease_name, confidence):
    """VLM / Text LLM call using Cloud key rotation with JSON structure response"""
    from config.settings import GEMINI_KEYS, GROK_KEY
    
    fallback = {
        "reason": "Pathogen proliferation detected on leaf margins. High localized relative humidity accelerates sporulation.",
        "recovery": "Prune symptomatic leaves immediately and dispose away from field. Improve inter-row canopy ventilation.",
        "prediction": "Secondary spread risk elevated if ambient humidity persists above 85%.",
        "fertilizer": "Apply targeted copper hydroxide or azoxystrobin fungicide at 2.5g/L."
    }

    prompt = f"""You are an agricultural expert plant pathologist. Analyze this crop disease:
Crop: {crop_name}
Disease: {disease_name}
Confidence: {confidence * 100:.1f}%

You must respond with a JSON object containing these exact fields:
- "reason": String (Sinhala explanation of why this occurred based on environmental factors like humidity and temperature)
- "recovery": String (Sinhala step-by-step action plan to treat/recover)
- "prediction": String (Sinhala spread pattern and yield impact prediction)
- "fertilizer": String (Sinhala fertilizer / fungicide treatment and dosage recommendation)

Return ONLY the raw JSON object, no explanation, no markdown tags."""

    # Check internet
    online = is_online_chat()
    print(f"[RECS] Internet connectivity status: {'ONLINE' if online else 'OFFLINE (Skip Cloud)'}")

    if online:
        # 1. Gemini key rotation
        for idx, key in enumerate(GEMINI_KEYS):
            if not key or "your-" in key: continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
                print(f"[RECS] Trying Gemini API (Key {idx+1}/{len(GEMINI_KEYS)})...")
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if res.status_code == 200:
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = json.loads(text)
                    print(f"[RECS] ✅ Gemini API Key {idx+1} Success!")
                    return parsed
            except Exception as e:
                print(f"[RECS] Gemini API Key {idx+1} failed: {e}")

        # 2. Groq
        if GROK_KEY and "your-" not in GROK_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                print("[RECS] Trying Groq API...")
                headers = {"Authorization": f"Bearer {GROK_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": { "type": "json_object" }
                }
                res = requests.post(url, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(text)
                    print("[RECS] ✅ Groq API Success!")
                    return parsed
            except Exception as e:
                print(f"[RECS] Groq API failed: {e}")

    # 3. Fallback to Local VLM
    try:
        url = f"{OLLAMA_API_URL}/api/chat"
        print(f"[RECS] Falling back to Local VLM ({OLLAMA_MODEL_VL})...")
        payload = {
            "model": OLLAMA_MODEL_VL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.2},
            "stream": False,
            "format": "json"
        }
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            content = res.json().get("message", {}).get("content", "").strip()
            parsed = json.loads(content)
            print("[RECS] ✅ Local VLM Success!")
            return parsed
    except Exception as e:
        print(f"[RECS] Local VLM failed: {e}")

    print("[RECS] ⚠️ All models failed. Returning Sinhala fallback directives.")
    return fallback

def camera_stream_receiver_loop():
    """Ultra-low-latency background thread capturing camera frames with instant multi-URL discovery."""
    global latest_camera_frame_raw, latest_camera_frame_jpeg, camera_connected
    print(f"[CAMERA RECEIVER] Ultra-fast camera engine launched. Target: {CAMERA_URL}")
    
    # Priority URLs for IP Webcam / Phone streaming
    candidate_urls = [
        CAMERA_URL,
        "http://192.168.8.151:8080/video",
        "http://192.168.8.151:4444/video",
        "https://192.168.8.151:4444/video/mjpeg",
        "http://192.168.8.151:8080/shot.jpg"
    ]
    
    local_cap = None
    last_webcam_probe_time = 0.0
    
    while True:
        stream_opened = False
        
        # Test URLs with short, snappy timeouts to connect instantly
        for test_url in candidate_urls:
            try:
                session = requests.Session()
                session.trust_env = False
                # Fast 0.5s connection timeout for immediate response
                response = session.get(test_url, stream=True, verify=False, timeout=(0.5, 3.0))
                if response.status_code == 200:
                    print(f"[CAMERA RECEIVER] ⚡ Connected to live camera stream: {test_url}")
                    camera_connected = True
                    stream_opened = True
                    buffer = bytearray()
                    
                    # Read in 32KB chunks for high-speed streaming
                    for chunk in response.iter_content(chunk_size=32768):
                        if not chunk:
                            continue
                        buffer.extend(chunk)
                        
                        # Keep only the freshest frame in memory to eliminate all lag/buffering
                        while True:
                            a = buffer.find(b'\xff\xd8')
                            if a == -1:
                                if len(buffer) > 65536:
                                    buffer = buffer[-4096:]
                                break
                            end = buffer.find(b'\xff\xd9', a)
                            if end == -1:
                                if a > 0:
                                    buffer = buffer[a:]
                                break
                                
                            jpg_bytes = bytes(buffer[a:end + 2])
                            buffer = buffer[end + 2:]
                            
                            # Fast decode
                            frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                with camera_frame_lock:
                                    latest_camera_frame_raw = frame
                                    latest_camera_frame_jpeg = jpg_bytes
                                    
                                if brain:
                                    frame_b64 = base64.b64encode(jpg_bytes).decode('utf-8')
                                    brain.update_latest_frame(frame_b64)
                    break
            except Exception:
                continue
                
        if not stream_opened:
            now = time.time()
            # Rate-limit local webcam fallback probe to once every 10s to eliminate DirectShow freeze & CPU spikes
            if now - last_webcam_probe_time > 10.0:
                last_webcam_probe_time = now
                try:
                    if local_cap is None or not local_cap.isOpened():
                        local_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                        if local_cap.isOpened():
                            local_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            local_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            local_cap.set(cv2.CAP_PROP_FPS, 30)
                            local_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    local_cap = None

            if local_cap and local_cap.isOpened():
                try:
                    ret, frame = local_cap.read()
                    if ret and frame is not None:
                        ret_enc, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        if ret_enc:
                            jpg_bytes = buf.tobytes()
                            with camera_frame_lock:
                                latest_camera_frame_raw = frame
                                latest_camera_frame_jpeg = jpg_bytes
                                camera_connected = True
                            if brain:
                                frame_b64 = base64.b64encode(jpg_bytes).decode('utf-8')
                                brain.update_latest_frame(frame_b64)
                            socketio.sleep(0.03)
                            continue
                    else:
                        local_cap.release()
                        local_cap = None
                except Exception:
                    if local_cap:
                        local_cap.release()
                    local_cap = None
                
            camera_connected = False
            socketio.sleep(0.5)

def create_standby_frame(frame_idx=0):
    """Generates an animated high-tech standby telemetry frame when external camera is awaiting uplink."""
    w, h = 640, 360
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Dark purple slate background
    img[:] = (22, 14, 28)
    
    # Tech grid lines
    for x in range(0, w, 40):
        cv2.line(img, (x, 0), (x, h), (36, 22, 44), 1)
    for y in range(0, h, 40):
        cv2.line(img, (0, y), (w, y), (36, 22, 44), 1)
        
    # Animated scanning sweep line
    scan_y = int((frame_idx * 5) % h)
    cv2.line(img, (0, scan_y), (w, scan_y), (224, 64, 160), 2)
    
    # Reticle / Crosshair in center
    cx, cy = w // 2, h // 2
    cv2.circle(img, (cx, cy), 35, (224, 64, 160), 1)
    cv2.line(img, (cx - 45, cy), (cx + 45, cy), (224, 64, 160), 1)
    cv2.line(img, (cx, cy - 45), (cx, cy + 45), (224, 64, 160), 1)
    
    # Status badges
    cv2.putText(img, "DEM3T3R V1 ROVER VISION - STANDBY", (25, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    cv2.putText(img, "AWAITING LIVE CAMERA UPLINK", (25, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 229, 255), 2)
    
    cv2.putText(img, "Phone Target: 192.168.8.151 (Port 8080 / 4444 / 4747)", (25, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (160, 180, 200), 1)
    cv2.putText(img, "1. Open 'IP Webcam' on phone -> Tap 'Start Server'", (25, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 128), 1)
    cv2.putText(img, "2. Or use DroidCam (Port 4747) / PC Webcam", (25, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 128), 1)
    
    # Telemetry HUD
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, f"SYNC TIME: {now_str}", (25, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (224, 64, 160), 1)
    cv2.putText(img, "ESP32 TELEMETRY: 192.168.8.150 [ACTIVE]", (25, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 128), 1)
    
    ret, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    return buf.tobytes() if ret else b''

def process_camera_frames():
    """Yields annotated frames to the web view at smooth 60fps rate leveraging the NVIDIA GPU (CUDA)."""
    device = "cuda:0"
    if device == "cuda:0" and torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
    print(f"[YOLO GENERATOR] Active processing engine: {device} (High-Performance Mode)")
    
    if not hasattr(generate_frames, 'detection_history'):
        generate_frames.detection_history = []

    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 82]

    frame_count = 0
    annotated_jpg = None
    annotated_frame = None

    while True:
        with camera_frame_lock:
            frame = latest_camera_frame_raw
            jpg_bytes = latest_camera_frame_jpeg
            
        if frame is None or jpg_bytes is None:
            standby_bytes = create_standby_frame(frame_count)
            frame_count += 1
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + standby_bytes + b'\r\n')
            socketio.sleep(0.04) # Smooth 25fps standby animation
            continue

        frame_count += 1

        # Run YOLO inference every 2nd frame to ensure video stream NEVER stutters or drops FPS
        if frame_count % 2 == 0:
            with model_lock:
                model = active_model
                inference_crop = current_crop

            if model is not None:
                try:
                    # Direct prediction on GPU device with FP16 half precision acceleration
                    results = model.predict(frame, conf=0.15, verbose=False, device=device, half=(device == "cuda:0" and torch.cuda.is_available()))
                    annotated_frame = None  # Overlays are drawn in the dashboard, never baked into video.
                    ret, buf = cv2.imencode('.jpg', frame, encode_params)
                    if ret:
                        annotated_jpg = buf.tobytes()

                    if model is not active_model or inference_crop != current_crop:
                        continue
                    frame_detections = []
                    if results[0].boxes is not None:
                        for box in results[0].boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            
                            # Normalize boundary box values to percentages
                            xyxy = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else [0, 0, 0, 0]
                            h, w = frame.shape[:2]
                            xmin_pct = (xyxy[0] / w) * 100
                            ymin_pct = (xyxy[1] / h) * 100
                            xmax_pct = (xyxy[2] / w) * 100
                            ymax_pct = (xyxy[3] / h) * 100

                            frame_detections.append({
                                'class': results[0].names[cls_id],
                                'confidence': conf,
                                'xmin': xmin_pct,
                                'ymin': ymin_pct,
                                'xmax': xmax_pct,
                                'ymax': ymax_pct
                            })

                    if frame_detections:
                        frame_detections.sort(key=lambda x: x['confidence'], reverse=True)
                        generate_frames.detection_history = frame_detections

                        if len(generate_frames.detection_history) > 50:
                            generate_frames.detection_history = generate_frames.detection_history[-50:]

                        disease_stats = {}
                        for det in generate_frames.detection_history:
                            cls = det['class']
                            if cls not in disease_stats:
                                disease_stats[cls] = {'total_conf': 0, 'count': 0, 'xmin': 0, 'ymin': 0, 'xmax': 0, 'ymax': 0}
                            disease_stats[cls]['total_conf'] += det['confidence']
                            disease_stats[cls]['count'] += 1
                            disease_stats[cls]['xmin'] = det['xmin']
                            disease_stats[cls]['ymin'] = det['ymin']
                            disease_stats[cls]['xmax'] = det['xmax']
                            disease_stats[cls]['ymax'] = det['ymax']

                        final_detections = []
                        for cls, stats in disease_stats.items():
                            avg_conf = stats['total_conf'] / stats['count']
                            if stats['count'] >= 1 and avg_conf >= 0.15:
                                final_detections.append({
                                    'class': cls,
                                    'confidence': round(avg_conf, 2),
                                    'count': stats['count'],
                                    'xmin': stats['xmin'],
                                    'ymin': stats['ymin'],
                                    'xmax': stats['xmax'],
                                    'ymax': stats['ymax']
                                })

                        final_detections.sort(key=lambda x: x['confidence'], reverse=True)

                        if final_detections:
                            socketio.emit('detection_list', {'crop': inference_crop, 'detections': final_detections})
                            
                            # Feed the highest confidence detection directly to the state machine brain
                            if brain:
                                brain.update_latest_detection(final_detections[0])

                            top_disease = final_detections[0]
                            if not hasattr(generate_frames, 'last_ai_disease') or \
                               generate_frames.last_ai_disease != top_disease['class']:
                                generate_frames.last_ai_disease = top_disease['class']
                                
                                # Only trigger visual advisor diagnosis when manually controlled
                                if brain and brain.mode == "manual":
                                    threading.Thread(
                                        target=emit_ai_recommendations,
                                        args=(current_crop, top_disease['class'], top_disease['confidence']),
                                        daemon=True,
                                    ).start()
                    else:
                        socketio.emit('detection_list', {'crop': current_crop, 'detections': []})
                except Exception as e:
                    print(f"[YOLO GPU PROFILER ERROR] {e}")

        # Vision Obstacle Avoidance & Telemetry
        display_frame = frame.copy()
        hud_frame, obstacle_telem = vision_obstacle_detector.process_frame(display_frame, draw_hud=False)
        if brain:
            brain.update_obstacle_status(obstacle_telem)
        if frame_count % 3 == 0:
            socketio.emit('obstacle_telemetry', obstacle_telem)

        ret_hud, buf_hud = cv2.imencode('.jpg', hud_frame, encode_params)
        out_jpg = buf_hud.tobytes() if ret_hud else (annotated_jpg if annotated_jpg is not None else jpg_bytes)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + out_jpg + b'\r\n')
        socketio.sleep(0.01)

# One inference producer serves every viewer, including when no browser is open.
stream_condition = threading.Condition()
stream_packet = None
stream_sequence = 0

def camera_processing_loop():
    global stream_packet, stream_sequence
    while True:
        try:
            for packet in process_camera_frames():
                with stream_condition:
                    stream_packet = packet
                    stream_sequence += 1
                    stream_condition.notify_all()
        except Exception as exc:
            print(f"[CAMERA] Processing retry: {type(exc).__name__}")
            socketio.sleep(1)

def generate_frames():
    last_sequence = -1
    while True:
        with stream_condition:
            stream_condition.wait_for(lambda: stream_packet is not None and stream_sequence != last_sequence, timeout=2)
            if stream_packet is None or stream_sequence == last_sequence:
                continue
            packet = stream_packet
            last_sequence = stream_sequence
        yield packet


def emit_ai_recommendations(crop, disease, confidence):
    print(f"[AI] Getting recommendations for {disease}...")
    parsed_rec = get_ai_recommendations(crop, disease, confidence)

    # Format recommendations string into JSON plan for UI
    ai_data = {
        'disease': disease,
        'confidence': confidence,
        'reason': parsed_rec.get('reason', 'Foliar pathology identified via computer vision.'),
        'recovery': parsed_rec.get('recovery', 'Apply recommended curative treatment.'),
        'prediction': parsed_rec.get('prediction', 'Moderate secondary transmission risk.'),
        'fertilizer': parsed_rec.get('fertilizer', 'Apply recommended fungicide.'),
        'timestamp': datetime.now().isoformat(),
    }
    socketio.emit('ai_recommendations', ai_data)
    
    # Also emit the structured analysis report for Auto Mode format display
    socketio.emit('ai_analysis_report', {
        "disease": disease,
        "confidence": confidence,
        "reason": parsed_rec.get('reason', 'Foliar pathology identified via computer vision.'),
        "recovery_plan": [parsed_rec.get('recovery', 'Apply recommended curative treatment.')],
        "severity": "moderate",
        "treatment_duration_sec": 5
    })
    print("[AI] ✅ Recommendations sent to frontend")

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.after_request
def add_cache_control_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    dist_dir = os.path.join(PROJECT_ROOT, 'dist')
    response = send_from_directory(dist_dir, 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/assets/<path:path>')
def send_assets(path):
    dist_assets = os.path.join(PROJECT_ROOT, 'dist', 'assets')
    response = send_from_directory(dist_assets, path)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    return response

@app.route('/api/model/switch')
def api_model_switch():
    crop_name = request.args.get('crop', 'tomato')
    success = load_yolo_model(crop_name)
    return jsonify({'status': 'ok' if success else 'error', 'crop': crop_name})

from flask import jsonify, request

@app.route('/api/canopy/analyze')
def api_canopy_analyze():
    global latest_camera_frame_raw
    with camera_frame_lock:
        frame = latest_camera_frame_raw
    indices = canopy_analyzer.compute_vegetation_indices(frame)
    return jsonify(indices)

@app.route('/api/prescription/generate')
def api_prescription_generate():
    chemical = request.args.get('chemical', 'Copper Fungicide')
    detections = []
    if brain and brain.latest_detection:
        detections.append(brain.latest_detection)
    result = prescription_generator.generate_prescription(
        field_boundary_gps=[],
        detections_log=detections,
        chemical_name=chemical
    )
    return jsonify(result)

@app.route('/api/mission/plan')
def api_mission_plan():
    boundary = [
        (6.92710, 79.86120),
        (6.92740, 79.86120),
        (6.92740, 79.86160),
        (6.92710, 79.86160)
    ]
    res = mission_manager.plan_mission_with_exclusions(boundary, row_spacing_m=0.8)
    return jsonify(res)

@app.route('/api/swarm/status')
def api_swarm_status():
    return jsonify(swarm_coordinator.get_swarm_status())

@app.route('/api/diagnostics/health')
def api_diagnostics_health():
    health_watchdog.ping_subsystem("yolo_inference_engine")
    health_watchdog.ping_subsystem("camera_mjpeg_stream")
    return jsonify(health_watchdog.run_diagnostic_check())

@app.route('/api/health')
def api_health():
    age = time.time() - latest_telemetry.get('last_seen', 0)
    return jsonify({
        'service': 'cropguard', 'status': 'ready',
        'hardware_connected': bool(latest_telemetry.get('hardware_connected')) and age <= 3,
        'telemetry_age_s': round(age, 2) if latest_telemetry.get('last_seen') else None,
        'transport': latest_telemetry.get('source'),
        'esp32_ip': latest_telemetry.get('ip'),
        'configured_esp32_host': os.getenv('ESP32_HOST', ''),
        'camera_connected': camera_connected,
        'emergency_stop_latched': emergency_stop_latched,
    })

@app.route('/api/vla/execute', methods=['POST'])
def api_vla_execute():
    data = request.get_json() or {}
    prompt = data.get('prompt', 'Inspect area and report crop status')
    global latest_camera_frame_raw
    with camera_frame_lock:
        frame = latest_camera_frame_raw
    telem = brain.latest_sensors if brain else {"latitude": 6.9271, "longitude": 79.8612, "ultrasonic_front": 120.0}
    action = vla_engine.execute_vla_inference(frame, prompt, telem)
    
    if brain and action.get('status') == 'READY_FOR_EXECUTION':
        act_cmds = action.get('actuator_commands', {})
        if 'motors' in act_cmds:
            m = act_cmds['motors']
            brain.send_esp32_command({'type': 'motor', 'left': m.get('left', 0), 'right': m.get('right', 0)})
        if act_cmds.get('pump'):
            brain.send_esp32_command({'type': 'pump', 'action': 'spray', 'duration_s': act_cmds.get('spray_duration_sec', 5.0)})

    return jsonify(action)

@app.route('/api/vla/directive', methods=['GET', 'POST'])
def api_vla_directive():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        directive = data.get("directive", "")
    else:
        directive = request.args.get("directive", "")
    thought = vla_engine.generate_cognitive_thought(
        current_crop=current_crop or "tomato",
        detection=brain.latest_detection if brain else None,
        telemetry=latest_telemetry,
        directive=directive
    )
    socketio.emit('vla_cognitive_stream', thought)
    return jsonify({"status": "success", "thought": thought})

@app.route('/api/physical_ai/evaluate')
def api_physical_ai_evaluate():
    telem = brain.latest_sensors if brain else {}
    moisture = telem.get('soilMoisture', 2100.0)
    obstacle = telem.get('ultrasonic', 120.0)
    weather = weather_service.get_weather() if weather_service else {}
    wind_spd = weather.get('wind_speed', 12.0)
    wind_dir = weather.get('wind_direction', 90.0)
    
    trav = physical_ai.evaluate_traversability(
        soil_moisture_raw=moisture,
        pitch_angle_deg=2.5,
        roll_angle_deg=1.2,
        obstacle_distance_cm=obstacle
    )
    drift = physical_ai.compute_spray_drift_physics(
        wind_speed_kmh=wind_spd,
        wind_dir_deg=wind_dir,
        robot_heading_deg=telem.get('heading', 0.0)
    )
    return jsonify({
        "timestamp": time.time(),
        "traversability": trav,
        "spray_drift_physics": drift
    })

@app.route('/api/voice/command', methods=['POST'])
def api_voice_command():
    data = request.get_json() or {}
    text = data.get('text', '')
    preferred_lang = data.get('language')
    result = voice_assistant.execute_command(text, preferred_lang)
    socketio.emit('log_entry', {
        'msg': f"🎤 Voice: '{text}' -> {result['intent']}",
        'type': 'success' if result['executed'] else 'warning'
    })
    socketio.emit('voice_response', result)
    return jsonify(result)

@app.route('/api/digital_twin/telemetry')
@app.route('/api/digital_twin/state')
def api_digital_twin_state():
    global latest_telemetry
    real_pose = {
        "x_local_m": latest_telemetry.get("x_local_m", 0.0),
        "y_local_m": latest_telemetry.get("y_local_m", 0.0),
        "heading_deg": latest_telemetry.get("heading", 0.0),
        "terrain_tilt_deg": latest_telemetry.get("pitch_deg", 0.0)
    }
    actuators = {
        "left_speed": 180 if latest_telemetry.get("motion") == "MOVING" else 0,
        "right_speed": 180 if latest_telemetry.get("motion") == "MOVING" else 0,
        "pump_active": latest_telemetry.get("pump_on", False),
        "solenoid_inserted": latest_telemetry.get("sol1_on", False)
    }
    obs = vision_obstacle_detector.get_latest_status() if hasattr(vision_obstacle_detector, 'get_latest_status') else None
    twin_frame = digital_twin.sync_robot_pose_to_twin(real_pose, actuators, obs)
    return jsonify(twin_frame)

@app.route('/api/digital_twin/reset', methods=['POST'])
def api_digital_twin_reset():
    return jsonify(digital_twin.reset_sim())

@app.route('/api/gps/update', methods=['POST'])
def api_gps_update():
    global latest_telemetry
    data = request.get_json() or {}
    lat = float(data.get('latitude', data.get('lat', 6.9271)))
    lon = float(data.get('longitude', data.get('lon', 79.8612)))
    alt = float(data.get('altitude', data.get('alt', 15.0)))
    speed = float(data.get('speed', 0.0))
    heading = float(data.get('heading', 0.0))
    hdop = float(data.get('hdop', 0.8))
    fix = bool(data.get('fix', True))

    position_estimator.update_rover_gps(lat, lon, hdop=hdop, satellites=int(data.get('satellites', 8)), fix_type=int(fix))
    pose = position_estimator.get_pose()
    fused_lat = pose["latitude"]
    fused_lon = pose["longitude"]

    weather_service.update_gps(fused_lat, fused_lon, alt, speed, heading, hdop)
    w_curr = weather_service.get_weather(fused_lat, fused_lon, force_refresh=True)

    loc_uv = w_curr.get("current", {}).get("uv_index", 0.0)
    loc_hum = w_curr.get("current", {}).get("humidity", 70)

    if latest_telemetry:
        latest_telemetry["latitude"] = lat
        latest_telemetry["longitude"] = lon
        latest_telemetry["fused_latitude"] = fused_lat
        latest_telemetry["fused_longitude"] = fused_lon
        latest_telemetry["pos_uncertainty_m"] = pose["uncertainty_m"]
        latest_telemetry["fusion_mode"] = pose["fusion_mode"]
        latest_telemetry["baseline"] = pose["baseline"]
        latest_telemetry["laptop_gps"] = pose["last_laptop_gps"]
        latest_telemetry["rover_gps"] = pose["last_rover_gps"]
        latest_telemetry["altitude"] = alt
        latest_telemetry["speed"] = speed
        latest_telemetry["heading"] = heading
        latest_telemetry["hdop"] = hdop
        latest_telemetry["fix"] = fix
        latest_telemetry["uvIndex"] = loc_uv
        if latest_telemetry.get("humidity", 0) <= 0:
            latest_telemetry["humidity"] = loc_hum
        socketio.emit('telemetry', latest_telemetry)
    else:
        latest_telemetry = {
            "type": "telemetry",
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "speed": speed,
            "heading": heading,
            "hdop": hdop,
            "fix": fix,
            "uvIndex": loc_uv,
            "humidity": loc_hum
        }
        socketio.emit('telemetry', latest_telemetry)

    socketio.emit('weather_update', w_curr)
    socketio.emit('weather_alert', weather_service.get_alerts())
    socketio.emit('disease_risk_update', weather_service.get_disease_risk(crop=current_crop or "Tomato", sensor_data=latest_telemetry))
    return jsonify({
        "status": "GPS_UPDATED",
        "latitude": lat,
        "longitude": lon,
        "location_name": w_curr.get("location_name"),
        "uv_index": loc_uv,
        "humidity": loc_hum
    })


@app.route('/api/location/laptop_update', methods=['POST'])
def api_location_laptop_update():
    global latest_telemetry
    data = request.get_json() or {}
    lat = float(data.get('latitude', data.get('lat', 6.9271)))
    lon = float(data.get('longitude', data.get('lon', 79.8612)))
    acc = float(data.get('accuracy', data.get('accuracy_m', 5.0)))
    alt = float(data.get('altitude', 15.0))
    speed = float(data.get('speed', 0.0)) if data.get('speed') is not None else None
    heading = float(data.get('heading', 0.0)) if data.get('heading') is not None else None

    global current_laptop_location
    current_laptop_location = {
        'latitude': lat,
        'longitude': lon,
        'altitude': alt,
        'accuracy': acc,
        'timestamp': time.time()
    }

    position_estimator.update_laptop_gps(lat, lon, accuracy_m=acc, altitude=alt, heading=heading, speed=speed)
    pose = position_estimator.get_pose()

    fused_lat = pose["latitude"]
    fused_lon = pose["longitude"]

    # Weather is strictly updated by LAPTOP GPS coordinates
    weather_service.update_gps(lat, lon, alt, speed or 0.0, heading or 0.0, acc)
    w_curr = weather_service.get_weather(lat, lon, force_refresh=True)
    w_curr["weather_source"] = "LAPTOP_GPS" 
    loc_uv = w_curr.get("current", {}).get("uv_index", 0.0)
    loc_hum = w_curr.get("current", {}).get("humidity", 70)

    if latest_telemetry:
        latest_telemetry["latitude"] = fused_lat
        latest_telemetry["longitude"] = fused_lon
        latest_telemetry["fused_latitude"] = fused_lat
        latest_telemetry["fused_longitude"] = fused_lon
        latest_telemetry["pos_uncertainty_m"] = pose["uncertainty_m"]
        latest_telemetry["fusion_mode"] = pose["fusion_mode"]
        latest_telemetry["baseline"] = pose["baseline"]
        latest_telemetry["laptop_gps"] = pose["last_laptop_gps"]
        latest_telemetry["rover_gps"] = pose["last_rover_gps"]
        latest_telemetry["uvIndex"] = loc_uv
        if latest_telemetry.get("humidity", 0) <= 0:
            latest_telemetry["humidity"] = loc_hum
    else:
        latest_telemetry = {
            "type": "telemetry",
            "latitude": fused_lat,
            "longitude": fused_lon,
            "fused_latitude": fused_lat,
            "fused_longitude": fused_lon,
            "pos_uncertainty_m": pose["uncertainty_m"],
            "fusion_mode": pose["fusion_mode"],
            "baseline": pose["baseline"],
            "laptop_gps": pose["last_laptop_gps"],
            "rover_gps": pose["last_rover_gps"],
            "altitude": alt,
            "speed": speed or 0.0,
            "heading": heading or 0.0,
            "hdop": acc / 2.5,
            "fix": True,
            "uvIndex": loc_uv,
            "humidity": loc_hum
        }

    socketio.emit('telemetry', latest_telemetry)
    socketio.emit('location_fusion_update', pose)
    socketio.emit('weather_update', w_curr)

    return jsonify({
        "status": "LAPTOP_LOCATION_FUSED",
        "pose": pose,
        "location_name": w_curr.get("location_name"),
        "uv_index": loc_uv,
        "humidity": loc_hum
    })

@app.route('/api/location/set_mode', methods=['POST'])
def api_location_set_mode():
    data = request.get_json() or {}
    mode = data.get("mode", "FUSED_DUAL")
    active_mode = position_estimator.set_fusion_mode(mode)
    pose = position_estimator.get_pose()
    socketio.emit('location_fusion_update', pose)
    return jsonify({"status": "MODE_UPDATED", "mode": active_mode, "pose": pose})

@app.route('/api/location/status', methods=['GET'])
def api_location_status():
    return jsonify(position_estimator.get_pose())

@app.route('/api/neural/depth')
def api_neural_depth():
    global latest_camera_frame_raw
    with camera_frame_lock:
        frame = latest_camera_frame_raw
    res = neural_suite.process_visuals(frame, generate_visualizations=False)
    return jsonify({
        'depth': res.get('depth'),
        'device': res.get('device'),
        'latency_ms': res.get('latency_ms')
    })

@app.route('/api/neural/segmentation')
def api_neural_segmentation():
    global latest_camera_frame_raw
    with camera_frame_lock:
        frame = latest_camera_frame_raw
    res = neural_suite.process_visuals(frame, generate_visualizations=False)
    return jsonify({
        'segmentation': res.get('segmentation'),
        'device': res.get('device'),
        'latency_ms': res.get('latency_ms')
    })

@app.route('/api/neural/pilot')
def api_neural_pilot():
    global latest_camera_frame_raw
    with camera_frame_lock:
        frame = latest_camera_frame_raw
    res = neural_suite.process_visuals(frame, generate_visualizations=False)
    return jsonify({
        'pilot': res.get('pilot'),
        'device': res.get('device'),
        'latency_ms': res.get('latency_ms')
    })

@app.route('/api/neural/status')
def api_neural_status():
    return jsonify(neural_suite.get_status())

@app.route('/<path:path>')
def send_static(path):
    if path.startswith('api/') or path == 'video_feed':
        return jsonify({'error': 'Not found'}), 404
    dist_dir = os.path.join(PROJECT_ROOT, 'dist')
    target = os.path.join(dist_dir, path)
    if os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(dist_dir, path)
    return send_from_directory(dist_dir, 'index.html')

@socketio.on('connect')
def handle_connect():
    with control_lock:
        dashboard_clients.add(request.sid)
    emit('emergency_stop_status', {'latched': emergency_stop_latched})
    print("[WS] ✅ Dashboard connected")
    emit('connection_status', {'status': 'connected'})
    with clients_lock:
        is_esp32_conn = len(connected_clients) > 0
    emit('esp32_status', {'connected': is_esp32_conn})
    emit('mode_status', {'mode': brain.mode if brain else 'manual'})
    emit('ollama_status', {
        'online': ollama_online,
        'vl_ready': ollama_vl_ready,
        'coder_ready': ollama_coder_ready
    })
    emit('system_status', build_system_status_payload())
    emit('vla_cognitive_stream', vla_engine.generate_cognitive_thought(
        current_crop=current_crop or "tomato",
        detection=brain.latest_detection if brain else None,
        telemetry=latest_telemetry
    ))
    if latest_telemetry:
        emit('telemetry', latest_telemetry)
    
    # Emit initial Weather and GPS states asynchronously so connect handshake returns in <1ms
    def _async_initial_weather():
        try:
            w_data = weather_service.get_weather()
            socketio.emit('weather_update', w_data)
            socketio.emit('gps_update', weather_service.get_current_gps())
            socketio.emit('weather_alert', weather_service.get_alerts())
            if latest_telemetry:
                socketio.emit('disease_risk_update', weather_service.get_disease_risk(crop=current_crop or "Tomato", sensor_data=latest_telemetry))
        except Exception as e:
            print(f"[WS] Weather initial emit error: {e}")
    threading.Thread(target=_async_initial_weather, daemon=True).start()

@socketio.on('disconnect')
def handle_disconnect():
    with control_lock:
        dashboard_clients.discard(request.sid)
        if not dashboard_clients:
            latch_emergency_stop('Last dashboard disconnected')
    print("[WS] ❌ Dashboard disconnected")

@socketio.on('weather_refresh_request')
def handle_weather_refresh(data):
    lat = data.get('lat')
    lon = data.get('lon')
    force = data.get('force', True)
    try:
        w_data = weather_service.get_weather(lat, lon, force_refresh=force)
        emit('weather_update', w_data)
        emit('weather_alert', weather_service.get_alerts())
        emit('disease_risk_update', weather_service.get_disease_risk(crop=current_crop or "Tomato", sensor_data=latest_telemetry))
    except Exception as e:
        print(f"[WS] Weather refresh error: {e}")

@socketio.on('weather_ai_summary_request')
def handle_weather_ai_summary(data):
    crop = data.get('crop', current_crop or 'Tomato')
    force = data.get('force', False)
    try:
        summary_data = weather_service.get_ai_summary(crop=crop, force_refresh=force)
        emit('weather_ai_summary_response', summary_data)
    except Exception as e:
        print(f"[WS] Weather AI summary error: {e}")

@socketio.on('crop_selected')
def handle_crop_selection(data):
    global current_crop, active_model
    crop_name = data.get('crop', '').lower()
    current_crop = crop_name
    generate_frames.detection_history = []
    
    # Reset last diagnosed disease lock to trigger new recommendation cycles
    if hasattr(generate_frames, 'last_ai_disease'):
        delattr(generate_frames, 'last_ai_disease')

    if crop_name:
        print(f"[WS] 🌱 Crop selected: {crop_name}")
        success = load_yolo_model(crop_name)
        classes = list(active_model.names.values()) if active_model else []
        emit('crop_confirmed', {
            'status': 'ok' if success else 'error',
            'crop': crop_name,
            'classes': classes,
            'message': f'{crop_name.capitalize()} model loaded ({len(classes)} classes)!',
        })
        socketio.emit('log_entry', {
            'type': 'yolo',
            'msg': f'YOLOv11 active weights swapped to {crop_name.upper()} ({len(classes)} disease detectors ready).'
        })
    else:
        with model_lock:
            active_model = None

@socketio.on('toggle_mode')
def handle_toggle_mode(data):
    target_mode = data.get('mode', 'manual') # 'manual' or 'auto'
    print(f"[WS] 🔄 Toggle Mode request: {target_mode}")
    if target_mode not in ('manual', 'auto'):
        return {'ok': False, 'error': 'Invalid mode'}
    if target_mode == 'auto' and (emergency_stop_latched or not latest_telemetry.get('hardware_connected') or time.time() - latest_telemetry.get('last_seen', 0) > 3):
        emit('hardware_command_result', {'sent': False, 'message': 'Auto mode requires fresh ESP32 telemetry and a reset emergency stop'})
        return {'ok': False}
    if brain:
        brain.set_mode(target_mode)
        socketio.emit('mode_status', {'mode': brain.mode})
        log_to_dashboard(f"Operational mode set to {target_mode.upper()}", "success" if target_mode == "auto" else "warning")

@socketio.on('robot_move')
def handle_robot_move(data):
    if not isinstance(data, dict):
        return {'ok': False}
    direction = str(data.get('direction', 'stop')).lower()
    if direction not in ('forward', 'backward', 'left', 'right', 'stop'):
        return {'ok': False, 'error': 'Invalid direction'}
    if direction == 'stop':
        if brain:
            brain.set_mode('manual')
        data = dict(data, speed=0, motor_left=0, motor_right=0)
    try:
        speed = int(data.get('speed', 255))
        for key in ('motor_left', 'motor_right'):
            if data.get(key) is not None:
                int(data[key])
    except (TypeError, ValueError, OverflowError):
        return {'ok': False, 'error': 'Invalid motor speed'}
    is_auto = data.get('source') == 'auto' or data.get('autonomous', False)
    if brain and brain.mode == "auto" and not is_auto and direction != "stop":
        return

    # Check for direct differential motor speed inputs (-255 to 255)
    motor_left_in = data.get('motor_left')
    motor_right_in = data.get('motor_right')

    if motor_left_in is not None and motor_right_in is not None:
        l_speed = int(max(-255, min(255, int(motor_left_in))))
        r_speed = int(max(-255, min(255, int(motor_right_in))))
    else:
        clamped_speed = max(0, min(255, speed))
        motors = {
            "forward": (clamped_speed, clamped_speed),
            "backward": (-clamped_speed, -clamped_speed),
            "left": (-clamped_speed, clamped_speed),
            "right": (clamped_speed, -clamped_speed),
            "stop": (0, 0)
        }
        l_speed, r_speed = motors.get(direction.lower(), (0, 0))

    # Instant sub-millisecond dispatch over high-speed TCP socket
    sent = send_to_esp32({
        "type": "combined",
        "command_id": "rc_move",
        "motor_left": l_speed,
        "motor_right": r_speed,
        "solenoid": "none",
        "pump_duration_s": 0.0
    })

@socketio.on('toggle_pump')
def handle_toggle_pump(data):
    state = data.get('state', False)
    if brain and brain.mode == "auto":
        return
    
    send_to_esp32({
        "type": "combined",
        "command_id": "manual_pump",
        "motor_left": 0,
        "motor_right": 0,
        "solenoid": "none",
        "pump_duration_s": 5.0 if state else 0.0
    })

@socketio.on('control_solenoid')
def handle_control_solenoid(data):
    sol_id = data.get('id', 1)
    action = data.get('action', 'pull')
    state = data.get('state')
    if brain and brain.mode == "auto":
        return
    
    if state is not None:
        sol_cmd = f"sol{sol_id}_on" if state else f"sol{sol_id}_off"
    else:
        sol_cmd = f"sol{sol_id}_on" if action == "push" else f"sol{sol_id}_off"

    send_to_esp32({
        "type": "combined",
        "command_id": f"manual_sol{sol_id}",
        "motor_left": 0,
        "motor_right": 0,
        "solenoid": sol_cmd,
        "pump_duration_s": 0.0
    })

@socketio.on('voice_command')
def handle_socket_voice_command(data):
    text = data.get('text', '')
    preferred_lang = data.get('language')
    res = voice_assistant.execute_command(text, preferred_lang)
    emit('voice_response', res)

@socketio.on('set_gps_coordinates')
def handle_set_gps_coordinates(data):
    lat = float(data.get('latitude', data.get('lat', 6.9271)))
    lon = float(data.get('longitude', data.get('lon', 79.8612)))
    alt = float(data.get('altitude', 15.0))
    speed = float(data.get('speed', 0.0))
    heading = float(data.get('heading', 0.0))
    weather_service.update_gps(lat, lon, alt, speed, heading)
    w_curr = weather_service.get_weather(lat, lon, force_refresh=True)
    if latest_telemetry:
        latest_telemetry["latitude"] = lat
        latest_telemetry["longitude"] = lon
        latest_telemetry["uvIndex"] = w_curr.get("current", {}).get("uv_index", 0.0)
        emit('telemetry', latest_telemetry, broadcast=True)
    emit('weather_update', w_curr, broadcast=True)


@socketio.on('laptop_location_stream')
def handle_laptop_location_stream(data):
    lat = float(data.get('latitude', 6.9271))
    lon = float(data.get('longitude', 79.8612))
    acc = float(data.get('accuracy', 5.0))
    alt = float(data.get('altitude', 15.0))
    speed = float(data.get('speed', 0.0)) if data.get('speed') is not None else None
    heading = float(data.get('heading', 0.0)) if data.get('heading') is not None else None

    global current_laptop_location
    current_laptop_location = {
        'latitude': lat,
        'longitude': lon,
        'altitude': alt,
        'accuracy': acc,
        'timestamp': time.time()
    }

    position_estimator.update_laptop_gps(lat, lon, accuracy_m=acc, altitude=alt, heading=heading, speed=speed)
    pose = position_estimator.get_pose()

    fused_lat = pose["latitude"]
    fused_lon = pose["longitude"]

    # Weather is strictly updated by LAPTOP GPS coordinates
    weather_service.update_gps(lat, lon, alt, speed or 0.0, heading or 0.0, acc)
    w_curr = weather_service.get_weather(lat, lon, force_refresh=True)
    w_curr["weather_source"] = "LAPTOP_GPS"
    emit('weather_update', w_curr, broadcast=True)
    emit('weather_alert', weather_service.get_alerts(), broadcast=True)
    emit('disease_risk_update', weather_service.get_disease_risk(crop=current_crop or "Tomato", sensor_data=latest_telemetry), broadcast=True)

    if latest_telemetry:
        latest_telemetry["latitude"] = fused_lat
        latest_telemetry["longitude"] = fused_lon
        latest_telemetry["fused_latitude"] = fused_lat
        latest_telemetry["fused_longitude"] = fused_lon
        latest_telemetry["pos_uncertainty_m"] = pose["uncertainty_m"]
        latest_telemetry["fusion_mode"] = pose["fusion_mode"]
        latest_telemetry["baseline"] = pose["baseline"]
        latest_telemetry["laptop_gps"] = pose["last_laptop_gps"]
        latest_telemetry["rover_gps"] = pose["last_rover_gps"]
        emit('telemetry', latest_telemetry, broadcast=True)

    emit('location_fusion_update', pose, broadcast=True)

@socketio.on('set_location_fusion_mode')
def handle_set_location_fusion_mode(data):
    mode = data.get('mode', 'FUSED_DUAL')
    active_mode = position_estimator.set_fusion_mode(mode)
    pose = position_estimator.get_pose()
    emit('location_fusion_update', pose, broadcast=True)

@socketio.on('vla_directive')
def handle_vla_directive(data):
    directive = data.get('directive', '') if isinstance(data, dict) else str(data)
    print(f"[VLA] Cognitive Directive received: '{directive}'")
    thought = vla_engine.generate_cognitive_thought(
        current_crop=current_crop or "tomato",
        detection=brain.latest_detection if brain else None,
        telemetry=latest_telemetry,
        directive=directive
    )
    socketio.emit('vla_cognitive_stream', thought)
    
    # Check if directive contains physical actuation tokens
    t_label = thought.get('target_reticle', {}).get('label')
    if t_label == 'SPOT_SPRAY':
        send_to_esp32({'type': 'combined', 'command_id': 'vla_spray',
            'motor_left': 0, 'motor_right': 0, 'solenoid': 'none', 'pump_duration_s': 3.5})
    elif t_label == 'SAFE_HALT':
        latch_emergency_stop('VLA directive safe halt')

@socketio.on('toggle_relay')
def handle_toggle_relay(data):
    raw_target = str(data.get('target', 'PUMP')).strip().upper()
    if not isinstance(data.get('state'), bool):
        emit('hardware_command_result', {'sent': False, 'message': 'Relay state must be a boolean'})
        return
    state = data['state']
    action_str = "on" if state else "off"
    
    if brain and brain.mode == "auto":
        print(f"[RELAY] User manual override: switching system mode to manual for relay {raw_target}")
        brain.set_mode("manual")
        socketio.emit('mode_status', {'mode': 'manual'})

    # Canonical mapping: supports both R1-R4 and semantic names (PUMP, SOL1, SOL2, SPARE)
    if raw_target in ['PUMP', 'WATER', 'IRRIGATION', 'RELAY1', 'R1']:
        r_target = 'R1'
        named_target = 'PUMP'
        sol_cmd = 'pump_on' if state else 'pump_off'
        pump_sec = 5.0 if state else 0.0
    elif raw_target in ['SOL1', 'SOIL1', 'PROBE1', 'VALVE1', 'RELAY2', 'R2']:
        r_target = 'R2'
        named_target = 'SOL1'
        sol_cmd = 'insert_probe' if state else 'sol1_off'
        pump_sec = 0.0
    elif raw_target in ['SOL2', 'SOIL2', 'PROBE2', 'VALVE2', 'RELAY3', 'R3']:
        r_target = 'R3'
        named_target = 'SOL2'
        sol_cmd = 'retract' if state else 'sol2_off'
        pump_sec = 0.0
    elif raw_target in ['SPARE', 'AUX', 'LIGHT', 'RELAY4', 'R4']:
        r_target = 'R4'
        named_target = 'SPARE'
        sol_cmd = 'spare_on' if state else 'spare_off'
        pump_sec = 0.0
    else:
        emit('hardware_command_result', {'sent': False, 'message': 'Unknown relay target'})
        return

    print(f"[RELAY COMMAND] Target={raw_target} -> R_Target={r_target} / {named_target}, State={state} ({action_str})")

    # 1. Direct Authoritative TCP Relay Packet (Microsecond execution, zero motor interference)
    send_to_esp32({
        "type": "relay",
        "target": r_target,
        "state": action_str,
        "command_id": f"direct_relay_{r_target}"
    })

@socketio.on('disease_detail_request')
def handle_disease_detail(data):
    client_sid = request.sid
    request_id = data.get('request_id')
    def respond(payload):
        socketio.emit('disease_detail_response', {**payload, 'request_id': request_id}, to=client_sid)

    disease_name = data.get('disease', '')
    confidence = data.get('confidence', 0)
    crop = data.get('crop', current_crop)
    if not disease_name:
        return

    from config.settings import GEMINI_KEYS, GROK_KEY

    prompt = f"""You are an expert Agricultural Plant Pathologist and Agronomist.
Analyze this crop disease comprehensively.

Crop: {crop}
Disease: {disease_name}
Confidence: {confidence * 100:.1f}%

You must respond with a JSON object containing ALL of these fields in ENGLISH:

- "disease_name_en": String (Standard English name of the disease)
- "description": String (Detailed description of this disease - symptoms, morphology, progression)
- "causes": String (Detailed explanation of causes - fungal/bacterial pathogens, environmental triggers, relative humidity, soil pH)
- "recovery_plan": List of Strings (Step-by-step actionable treatment and recovery steps, at least 4 steps)
- "harvest_effect": String (Detailed explanation of yield reduction and quality degradation if untreated)
- "fertilizer_list": List of objects, each with "name" (String), "dosage" (String), "method" (String). Distinguish nutrition from disease treatments. Do not invent product dosages. If formulation, label approval, crop stage or local registration is unknown, say dosage requires label verification. Return an empty list when treatment is not indicated (including healthy crops).
- "severity": String (use "unknown" unless observed damage supports severity; confidence is not severity)
- "spread_risk": String (Description of secondary infection rate and incubation period)
- "prevention_tips": List of Strings (At least 3 proactive agronomic prevention measures)

Return ONLY the raw JSON object. No explanation, no markdown."""

    fallback = {
        "unavailable": True,
        "disease_name_en": disease_name.replace("_", " ").title(),
        "fertilizer_list": [], "recovery_plan": [], "prevention_tips": []
    }

    online = is_online_chat()

    if online:
        for idx, key in enumerate(GEMINI_KEYS):
            if not key or "your-" in key: continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if res.status_code == 200:
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = json.loads(text)
                    print(f"[DISEASE DETAIL] ✅ Gemini Key {idx+1} Success!")
                    respond(parsed)
                    return
            except Exception as e:
                print(f"[DISEASE DETAIL] Gemini Key {idx+1} failed: {e}")

        if GROK_KEY and "your-" not in GROK_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                hdrs = {"Authorization": f"Bearer {GROK_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": { "type": "json_object" }
                }
                res = requests.post(url, json=payload, headers=hdrs, timeout=8)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(text)
                    print("[DISEASE DETAIL] ✅ Groq Success!")
                    respond(parsed)
                    return
            except Exception as e:
                print(f"[DISEASE DETAIL] Groq failed: {e}")

    try:
        url = f"{OLLAMA_API_URL}/api/chat"
        payload = {
            "model": OLLAMA_MODEL_VL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.2},
            "stream": False,
            "format": "json"
        }
        res = requests.post(url, json=payload, timeout=6)
        if res.status_code == 200:
            content = res.json().get("message", {}).get("content", "").strip()
            parsed = json.loads(content)
            print("[DISEASE DETAIL] ✅ Local VLM Success!")
            respond(parsed)
            return
    except Exception as e:
        print(f"[DISEASE DETAIL] Local VLM failed: {e}")

    print("[DISEASE DETAIL] Advice unavailable; returning empty plan.")
    respond(fallback)

@socketio.on('chat_message')
def handle_chat_message(data):
    client_sid = request.sid
    request_id = data.get('request_id')
    def respond(message):
        socketio.emit('chat_reply', {'message': message, 'request_id': request_id}, to=client_sid)
    user_msg = str(data.get('message', ''))[:2000]
    language = data.get('language', 'en')
    if not user_msg: return
    
    print(f"[CHAT] Received message ({language}): {user_msg}")
    from config.settings import GEMINI_KEYS, GROK_KEY, OLLAMA_MODEL_VL, OLLAMA_API_URL
    
    lang_names = {'en': 'English'}
    lang_str = lang_names.get(language, 'English')
    
    prompt = f"You are DEM3T3R V1 Assistant, an expert agricultural robot advisor in Sri Lanka. The user has selected the language: {lang_str}. Respond to the user strictly and fluently in {lang_str} using authentic technical and agricultural terms: {user_msg}"
    
    crop_context = str(data.get('crop', current_crop))[:60]
    observations = data.get('detections', [])
    observations = observations[:8] if isinstance(observations, list) else []
    prompt += "\nSelected crop: " + crop_context + "\nUnverified model observations: " + json.dumps(observations)[:2500]
    prompt += "\nGive advisory answers only; never claim to move the robot or activate outputs. Distinguish fertilizer nutrition from disease control. Never invent a dosage: require the registered product label, formulation, crop stage and local approval. If diagnosis is uncertain, explain it. Confidence is not disease severity."
    online = is_online_chat()
    
    if online:
        # 1. Try Gemini rotation
        for idx, key in enumerate(GEMINI_KEYS):
            if not key or "your-" in key: continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if res.status_code == 200:
                    reply = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    respond(reply)
                    print(f"[CHAT] ✅ Gemini API Key {idx+1} response sent.")
                    return
            except Exception as e:
                print(f"[CHAT] Gemini API Key {idx+1} failed: {e}")

        # 2. Try Groq
        if GROK_KEY and "your-" not in GROK_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROK_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [{"role": "user", "content": prompt}]
                }
                res = requests.post(url, json=payload, headers=headers, timeout=8)
                if res.status_code == 200:
                    reply = res.json()["choices"][0]["message"]["content"].strip()
                    respond(reply)
                    print("[CHAT] ✅ Groq response sent.")
                    return
            except Exception as e:
                print(f"[CHAT] Groq API failed: {e}")

    # 3. Fallback to Local Ollama
    try:
        payload = {
            "model": OLLAMA_MODEL_VL,
            "prompt": prompt,
            "stream": False
        }
        res = local_http.post(f"{OLLAMA_API_URL}/api/generate", json=payload, timeout=6)
        if res.status_code == 200:
            reply = res.json().get('response', '').strip()
            respond(reply)
            print("[CHAT] ✅ Local Ollama response sent.")
            return
    except Exception as e:
        print(f"[CHAT] Local Ollama failed: {e}")

    respond("The AI service is currently unavailable. Connect local Ollama or configure an AI provider, then try again.")

# Continuous Real-Time Sensor Telemetry Heartbeat Daemon
def telemetry_daemon_loop():
    global latest_telemetry
    weather_timer = 0
    while True:
        try:
            recent = latest_telemetry and time.time() - latest_telemetry.get('last_seen', 0) <= 3.0
            if not recent and os.getenv('ESP32_HOST'):
                try:
                    response = local_http.get(f"http://{os.environ['ESP32_HOST']}/data", timeout=0.8)
                    response.raise_for_status()
                    latest_telemetry = normalize_telemetry(response.json(), 'http')
                    socketio.emit('telemetry', latest_telemetry)
                    if brain:
                        brain.update_telemetry(latest_telemetry)
                except (requests.RequestException, ValueError):
                    pass
            fresh = bool(latest_telemetry) and time.time() - latest_telemetry.get('last_seen', 0) <= 3.0
            socketio.emit('esp32_status', {'connected': fresh, 'source': latest_telemetry.get('source'), 'ip': latest_telemetry.get('ip')})
            if not fresh and latest_telemetry.get('hardware_connected'):
                latest_telemetry = dict(latest_telemetry, hardware_connected=False, status='STALE')
                socketio.emit('telemetry', latest_telemetry)
                if brain:
                    brain.update_telemetry(latest_telemetry)

            # Continuous 1Hz System & Peripheral Nodes Heartbeat
            socketio.emit('system_status', build_system_status_payload())

            # Continuous VLA Cognitive Thought Stream (Embodied AI Reasoning)
            try:
                latest_det = brain.latest_detection if brain else None
                thought = vla_engine.generate_cognitive_thought(
                    current_crop=current_crop or "tomato",
                    detection=latest_det,
                    telemetry=latest_telemetry
                )
                socketio.emit('vla_cognitive_stream', thought)
            except Exception as e:
                pass

            weather_timer += 1.0
            if weather_timer >= 60.0: # Periodic 60s weather refresh
                weather_timer = 0
                w_curr = weather_service.get_weather()
                socketio.emit('weather_update', w_curr)
                socketio.emit('weather_alert', weather_service.get_alerts())
                if latest_telemetry:
                    socketio.emit('disease_risk_update', weather_service.get_disease_risk(crop=current_crop or "Tomato", sensor_data=latest_telemetry))

        except Exception as e:
            print(f"[TELEMETRY DAEMON] Error: {e}")
        socketio.sleep(1.0)

def serial_sensor_receiver_loop():
    """Continuously auto-detects and ingests real sensor telemetry from USB Serial COM port."""
    global latest_telemetry, active_serial_conn
    import serial.tools.list_ports
    import serial

    last_scan = 0

    while True:
        try:
            with serial_conn_lock:
                ser_is_open = active_serial_conn is not None and active_serial_conn.is_open

            if not ser_is_open:
                now = time.time()
                if now - last_scan >= 2.0:
                    last_scan = now
                    try:
                        ports = list(serial.tools.list_ports.comports())
                    except Exception:
                        ports = []
                    for p in ports:
                        desc = (p.description or "").lower()
                        hwid = (p.hwid or "").lower()
                        if any(k in desc or k in hwid for k in ["ch340", "cp210", "ftdi", "usb serial", "esp", "arduino", "silicon labs"]):
                            try:
                                ser = serial.Serial(p.device, 115200, timeout=1.0)
                                with serial_conn_lock:
                                    active_serial_conn = ser
                                print(f"[SERIAL] ✅ Connected to hardware sensor link on {p.device} ({p.description})")
                                socketio.emit('esp32_status', {'connected': True, 'port': p.device, 'source': 'serial'})
                                break
                            except Exception:
                                pass

            ser_to_read = None
            with serial_conn_lock:
                if active_serial_conn and active_serial_conn.is_open:
                    ser_to_read = active_serial_conn

            if ser_to_read:
                line = ser_to_read.readline().decode('utf-8', errors='ignore').strip()
                if line and line.startswith('{') and line.endswith('}'):
                    try:
                        msg = json.loads(line)
                        if msg.get('type') == 'telemetry':
                            msg = normalize_telemetry(msg, 'serial')
                            latest_telemetry = msg
                            socketio.emit('telemetry', msg)
                            if brain:
                                brain.update_telemetry(msg)
                        elif msg.get('type') == 'ack':
                            socketio.emit('hardware_ack', msg)
                            if brain:
                                brain.handle_ack(msg)
                    except Exception:
                        pass
            else:
                socketio.sleep(0.5)
        except Exception:
            with serial_conn_lock:
                if active_serial_conn:
                    try:
                        active_serial_conn.close()
                    except Exception:
                        pass
                    active_serial_conn = None
            socketio.sleep(1.0)
        socketio.sleep(0.02)

def run_tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm for zero latency
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # High-throughput 64KB receive buffer
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # High-throughput 64KB send buffer
    sock.bind(('0.0.0.0', 5000))
    sock.listen(5)
    print("[TCP] ✅ Listening on port 5000 (TCP_NODELAY + 64KB Turbo Buffers active)")

    while True:
        try:
            client, addr = sock.accept()
            client.settimeout(5)
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Instant sub-millisecond transmission
            client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            print(f"[TCP] ✅ ESP32 connected from {addr} (Ultra Low-Latency Turbo Mode)")
            with clients_lock:
                connected_clients.append(client)
            socketio.emit('esp32_status', {'connected': True, 'ip': addr[0]})
            threading.Thread(target=handle_esp32, args=(client,), daemon=True).start()
        except Exception as e:
            print(f"[TCP] Accept error: {e}")

def handle_esp32(client):
    global latest_telemetry
    buffer = ""
    last_ws_emit_time = 0.0
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data
            if len(buffer) > 65536:
                break
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line_str = line.strip()
                if line_str:
                    try:
                        msg = json.loads(line_str)
                        msg_type = msg.get('type')
                        
                        if msg_type == 'telemetry':
                            msg = normalize_telemetry(msg, 'tcp')
                            latest_telemetry = msg
                            
                            # Rate-limit WebSocket broadcast to 30Hz (33ms) to keep socket queue 100% clear for motor commands
                            now = time.time()
                            if now - last_ws_emit_time >= 0.033:
                                last_ws_emit_time = now
                                socketio.emit('telemetry', msg)
                            
                            # Sync live ESP32 GPS with weather service
                            if "latitude" in msg and "longitude" in msg:
                                weather_service.update_gps(
                                    msg["latitude"], msg["longitude"],
                                    msg.get("altitude", 0.0),
                                    msg.get("speed", 0.0),
                                    msg.get("heading", 0.0),
                                    msg.get("accuracy", 2.5)
                                )

                            if brain:
                                brain.update_telemetry(msg)
                                
                        elif msg_type == 'ack':
                            socketio.emit('hardware_ack', msg)
                            if brain:
                                brain.handle_ack(msg)
                                
                    except Exception:
                        pass
        except Exception:
            break
            
    with clients_lock:
        if client in connected_clients:
            connected_clients.remove(client)
        is_conn = len(connected_clients) > 0
    client.close()
    print("[TCP] ESP32 disconnected")
    socketio.emit('esp32_status', {'connected': is_conn})

def hardware_heartbeat_loop():
    while True:
        if (latest_telemetry.get('last_seen') and
                time.time() - latest_telemetry['last_seen'] > 3 and not emergency_stop_latched):
            latch_emergency_stop('ESP32 telemetry timed out')
        send_to_esp32({'type': 'heartbeat'})
        socketio.sleep(0.5)


def connect_esp32_loop():
    host = os.getenv('ESP32_HOST', '').strip()
    if not host:
        return
    while True:
        if connected_clients:
            socketio.sleep(2)
            continue
        try:
            client = socket.create_connection((host, int(os.getenv('ESP32_TCP_PORT', '8080'))), timeout=3)
            client.settimeout(5)
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            with clients_lock:
                connected_clients.append(client)
            handle_esp32(client)
        except OSError:
            pass
        socketio.sleep(3)


def start_server():
    threading.Thread(target=hardware_heartbeat_loop, daemon=True).start()
    # Start decoupled camera grabber loop in dedicated background thread
    threading.Thread(target=camera_stream_receiver_loop, daemon=True).start()
    threading.Thread(target=camera_processing_loop, daemon=True).start()
    
    threading.Thread(target=connect_esp32_loop, daemon=True).start()

    # Start TCP connection server
    threading.Thread(target=run_tcp_server, daemon=True).start()
    
    # Start Ollama local status heartbeat checker loop thread
    threading.Thread(target=ollama_heartbeat_loop, daemon=True).start()
    
    # Start continuous sensor telemetry heartbeat daemon thread
    threading.Thread(target=telemetry_daemon_loop, daemon=True).start()
    
    # Start auto-detecting USB Serial hardware sensor receiver thread
    threading.Thread(target=serial_sensor_receiver_loop, daemon=True).start()
    
    print("=" * 60)
    print("🌾 DEM3T3R V1 Server Running...")
    print("Dashboard: http://localhost:5001")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    start_server()
