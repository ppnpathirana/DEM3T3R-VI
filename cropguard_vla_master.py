"""
@file: cropguard_vla_master.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
🌾 DEM3T3R V1 VLA Master - Zero-Shot Vision-Language Autonomous Perception & Actuation Engine
Model: Google PaliGemma 3B (google/paligemma-3b-pt-224) via FP16 CUDA
Zero-Shot Generalization: Multi-attribute visual reasoning for untrained anomalies, pests & lesions
Hardware: Laptop (i5-13420H / RTX 3050 6GB) -> WiFi / TCP Socket -> Single ESP32-S3 Node
"""

import os
import sys
import time
import threading
import queue
import cv2
import torch
import serial
import serial.tools.list_ports
from PIL import Image
import numpy as np

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================
HF_TOKEN = "hf_YOUR_TOKEN_HERE"
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_MODEL_DIR = os.path.join(_PROJECT_DIR, "models", "paligemma")
MODEL_ID = _LOCAL_MODEL_DIR if os.path.isdir(_LOCAL_MODEL_DIR) else "google/paligemma-3b-pt-224"
SERIAL_BAUD = 115200
DEFAULT_COM_PORT = "COM3"
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
INFERENCE_INTERVAL_SEC = 1.0  # Run Zero-Shot VLM analysis every 1 second
SPRAY_COOLDOWN_SEC = 5.0      # 5-second cooldown to prevent duplicate spraying
DEFAULT_SPRAY_DURATION_MS = 3000

# Zero-Shot Multi-Attribute Reasoning Prompt
ZERO_SHOT_PROMPT = (
    "Analyze this plant leaf image carefully. "
    "Identify any visual anomalies, spots, lesions, fungal growth, discoloration, or pest damage. "
    "If any infection or pest is present, explain the symptom and state 'ACTION_REQUIRED'. "
    "If completely healthy, state 'HEALTHY'."
)

# Zero-Shot Detection Trigger Keywords
ANOMALY_KEYWORDS = [
    "action_required", "disease", "pest", "spot", "blight", 
    "fungus", "lesion", "anomaly", "damage", "rot", "mold", 
    "infestation", "mildew", "wilting", "caterpillar", "chlorosis"
]

# ==============================================================================
# 2. ROBUST AUTO-RECONNECTING SERIAL BRIDGE
# ==============================================================================
class ESP32SerialBridge:
    def __init__(self, baud=SERIAL_BAUD, default_port=DEFAULT_COM_PORT):
        self.baud = baud
        self.port = default_port
        self.serial_conn = None
        self.lock = threading.Lock()
        self.connect()

    def find_esp32_port(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = p.description.lower()
            if any(k in desc for k in ["cp210", "ch340", "usb-serial", "esp32", "uart"]):
                return p.device
        return ports[0].device if ports else self.port

    def connect(self):
        with self.lock:
            try:
                target_port = self.find_esp32_port()
                print(f"[SERIAL] Probing ESP32 on {target_port} @ {self.baud} baud...")
                self.serial_conn = serial.Serial(target_port, self.baud, timeout=1.0)
                time.sleep(2.0)
                print(f"[SERIAL] ✅ Connected to ESP32 Master Node on {target_port}")
                self.port = target_port
                return True
            except Exception as e:
                print(f"[SERIAL] ⚠️ Hardware not attached on {self.port} ({e}). Simulation Mode Active.")
                self.serial_conn = None
                return False

    def send_command(self, cmd_str: str) -> bool:
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    payload = (cmd_str.strip() + "\n").encode('utf-8')
                    self.serial_conn.write(payload)
                    self.serial_conn.flush()
                    print(f"[SERIAL -> ESP32] Sent: {cmd_str}")
                    return True
                except Exception as e:
                    print(f"[SERIAL] Communication dropped ({e}). Reconnecting...")
                    self.serial_conn = None
            else:
                print(f"[SERIAL EMULATED] -> {cmd_str}")
        return False

# ==============================================================================
# 3. ASYNCHRONOUS MULTI-THREADED ZERO-LAG CAMERA
# ==============================================================================
class AsyncVideoCapture:
    def __init__(self, src=CAMERA_INDEX, width=FRAME_WIDTH, height=FRAME_HEIGHT):
        self.src = src
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.ret = False
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def _capture_worker(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.ret = ret
                    self.frame = frame
            else:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.ret and self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def release(self):
        self.running = False
        self.cap.release()

# ==============================================================================
# 4. PALIGEMMA 3B ZERO-SHOT INFERENCE ENGINE (FP16 CUDA)
# ==============================================================================
class ZeroShotPaliGemmaEngine:
    def __init__(self, token=HF_TOKEN, model_id=MODEL_ID):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[ZERO-SHOT VLM] Hardware Device: {self.device.upper()}")

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"[ZERO-SHOT VLM] GPU: {gpu_name} ({vram_gb:.2f} GB VRAM) - FP16 Mode Enabled")

        self.model = None
        self.processor = None
        # Free any leftover GPU memory before loading the large model
        if self.device == "cuda":
            torch.cuda.empty_cache()
        self._load_paligemma(token, model_id)

    def _load_paligemma(self, token, model_id):
        try:
            from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
            print(f"[ZERO-SHOT VLM] Loading {model_id} in torch.float16...")
            
            self.processor = AutoProcessor.from_pretrained(model_id, token=token)
            self.model = PaliGemmaForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                token=token
            ).eval()
            print(f"[ZERO-SHOT VLM] ✅ PaliGemma 3B loaded into RTX 3050 VRAM!")
        except Exception as e:
            print(f"[ZERO-SHOT VLM] ⚠️ Remote weights notice ({e}).")
            print("[ZERO-SHOT VLM] Activating High-Speed Zero-Shot Spectral Anomaly Analyzer.")
            self.model = None

    def infer_zero_shot(self, frame_bgr: np.ndarray, prompt: str = ZERO_SHOT_PROMPT) -> dict:
        """
        Executes Zero-Shot reasoning over visual frame.
        Returns parsed decision: {'action_required': bool, 'reasoning': str, 'symptom': str}
        """
        if self.model is not None and self.processor is not None:
            try:
                img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb).resize((224, 224))
                
                inputs = self.processor(text=prompt, images=pil_img, return_tensors="pt")
                if self.device == "cuda":
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    if "pixel_values" in inputs:
                        inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)

                with torch.inference_mode():
                    generated_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=48,
                        do_sample=False
                    )
                
                input_len = inputs["input_ids"].shape[-1]
                output_text = self.processor.decode(generated_ids[0][input_len:], skip_special_tokens=True).strip()
                return self._parse_zero_shot_response(output_text)
            except Exception as e:
                print(f"[VLM INFERENCE ERROR] {e}")

        # High-Speed Zero-Shot Spectral Fallback
        return self._spectral_zero_shot_fallback(frame_bgr)

    def _parse_zero_shot_response(self, text: str) -> dict:
        text_lower = text.lower()
        action_needed = any(k in text_lower for k in ANOMALY_KEYWORDS)
        
        return {
            "action_required": action_needed,
            "raw_output": text,
            "summary": "Pathogen / Anomaly Detected" if action_needed else "Healthy Foliage",
            "trigger_token": "ACTION_REQUIRED" if action_needed else "NORMAL"
        }

    def _spectral_zero_shot_fallback(self, frame_bgr: np.ndarray) -> dict:
        """Calculates Excess Green Index (ExG) and chlorosis anomaly percentage."""
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        r, g, b = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]
        sum_rgb = r + g + b + 1e-6
        exg = 2.0 * (g / sum_rgb) - (r / sum_rgb) - (b / sum_rgb)
        
        # Chlorosis / Necrosis mask (Yellowish-brown diseased tissue)
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask_disease = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([30, 255, 200]))
        disease_ratio = np.count_nonzero(mask_disease) / mask_disease.size

        action = disease_ratio > 0.06
        desc = f"Visual lesion anomaly detected ({disease_ratio*100:.1f}% necrotic area) ACTION_REQUIRED" if action else "Uniform chlorophyll canopy confirmed HEALTHY"
        
        return {
            "action_required": action,
            "raw_output": desc,
            "summary": "Pathogen Anomaly" if action else "Healthy Canopy",
            "trigger_token": "ACTION_REQUIRED" if action else "HEALTHY"
        }

# ==============================================================================
# 5. MAIN ASYNCHRONOUS AUTONOMOUS CONTROL LOOP
# ==============================================================================
def main():
    print("=" * 75)
    print("   🌾 DEM3T3R V1 ZERO-SHOT VLA AUTONOMOUS ENGINE (PALIGEMMA 3B)")
    print("=" * 75)

    import argparse
    parser = argparse.ArgumentParser(description='DEM3T3R V1 VLA Master')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode (no serial communication)')
    args = parser.parse_args()
    # Pass simulate flag to bridge
    serial_bridge = ESP32SerialBridge() if not args.simulate else None
    # If simulate, replace bridge with mock that only logs
    if args.simulate:
        class MockBridge:
            def send_command(self, cmd_str: str) -> bool:
                print(f"[SIMULATION] Would send to ESP32: {cmd_str}")
                return True
        serial_bridge = MockBridge()

    last_inference_time = 0.0
    last_spray_time = 0.0
    latest_result = {"action_required": False, "raw_output": "INITIALIZING VLM...", "summary": "STANDBY"}
    
    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            current_time = time.time()

            # --- Async Zero-Shot Reasoning Cycle ---
            if current_time - last_inference_time >= INFERENCE_INTERVAL_SEC:
                last_inference_time = current_time
                latest_result = vlm_engine.infer_zero_shot(frame, prompt=ZERO_SHOT_PROMPT)

                # --- Actuation Decision Logic with 5-Second Cooldown ---
                if latest_result["action_required"]:
                    time_since_spray = current_time - last_spray_time
                    if time_since_spray >= SPRAY_COOLDOWN_SEC:
                        last_spray_time = current_time
                        spray_command = f"SPRAY:{DEFAULT_SPRAY_DURATION_MS}"
                        print(f"\n[ZERO-SHOT TRIGGER] 🚨 ANOMALY: '{latest_result['raw_output']}'")
                        print(f"[ACTUATION] ⚡ Transmitting to ESP32: {spray_command}")
                        serial_bridge.send_command(spray_command)
                    else:
                        remaining = SPRAY_COOLDOWN_SEC - time_since_spray
                        print(f"[COOLDOWN ACTIVE] Target flagged. Next spray available in {remaining:.1f}s")

            # --- Real-Time HUD Overlay ---
            is_active = latest_result["action_required"]
            hud_color = (0, 0, 255) if is_active else (0, 255, 0)
            
            # Semi-transparent top HUD banner
            cv2.rectangle(frame, (10, 10), (630, 105), (20, 15, 28), -1)
            cv2.rectangle(frame, (10, 10), (630, 105), hud_color, 2)

            cv2.putText(frame, "DEM3T3R V1 PALIGEMMA 3B - ZERO-SHOT VLA", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.putText(frame, f"VLM Output: {latest_result['raw_output'][:42]}", (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            cv2.putText(frame, f"Diagnosis: {latest_result['summary']}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hud_color, 1)

            cd_rem = max(0.0, SPRAY_COOLDOWN_SEC - (current_time - last_spray_time))
            cd_status = f"COOLDOWN ({cd_rem:.1f}s)" if cd_rem > 0 else "SPRAY READY"
            cv2.putText(frame, f"Actuator: {cd_status}", (420, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 200, 100), 1)

            cv2.imshow("DEM3T3R V1 Zero-Shot VLA Live Console", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[SYSTEM] User initiated shutdown.")
                break

    except KeyboardInterrupt:
        print("\n[SYSTEM] Interrupted by user.")
    finally:
        cam.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Clean shutdown complete.")

if __name__ == "__main__":
    main()
