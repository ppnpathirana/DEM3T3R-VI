import time
import threading
import json
from backend.state_machine import StateMachine, State
from backend import vision_analyzer
from backend import command_generator
from config.settings import YOLO_CONFIDENCE_THRESHOLD

class AIBrain:
    def __init__(self, send_tcp_cmd_callback=None, log_callback=None, socket_emit_callback=None):
        self.mode = "manual"  # "manual" or "auto"
        self.running = False
        self.lock = threading.Lock()
        self.auto_thread = None
        
        # State machine
        self.state_machine = StateMachine()
        
        # Telemetry & state caching
        self.latest_sensors = {}
        self.latest_detection = None
        self.latest_obstacle_status = None
        self.latest_frame = None  # Base64 JPEG string
        self.last_telemetry_time = 0.0
        
        # Actuator state
        self.robot_state = {
            "solenoid_inserted": False,
            "treatment_completed": False,
            "motors_active": False
        }
        
        # ACK tracking
        self.last_cmd_id = None
        self.ack_event = threading.Event()
        self.cmd_counter = 0
        self.hardware_connected = False
        
        # Callbacks
        self.send_tcp_cmd_callback = send_tcp_cmd_callback
        self.log_callback = log_callback
        self.socket_emit_callback = socket_emit_callback

    def log(self, message, log_type="info"):
        print(f"[AI_BRAIN] {message}")
        if self.log_callback:
            self.log_callback(message, log_type)

    def set_mode(self, mode):
        if mode not in ('auto', 'manual'):
            raise ValueError('Unsupported robot mode')
        with self.lock:
            if mode == 'auto':
                if not self.hardware_connected or time.time() - self.last_telemetry_time > 3:
                    self.log('Auto mode requires fresh hardware telemetry.', 'warning')
                    return False
                if self.auto_thread and self.auto_thread.is_alive() and self.mode != 'auto':
                    self.log('Previous autonomous action is still cancelling.', 'warning')
                    return False
            old_mode = self.mode
            self.mode = mode
        if mode == "auto" and old_mode != "auto":
            self.start_auto_mode()
        elif mode == "manual" and old_mode != "manual":
            self.stop_auto_mode()
        return True

    def start_auto_mode(self):
        self.running = True
        self.robot_state["solenoid_inserted"] = False
        self.robot_state["treatment_completed"] = False
        self.state_machine.transition(State.SCANNING)
        self.log("Auto Mode initiated at full operational speed.", "success")
        self.auto_thread = threading.Thread(target=self._auto_loop, daemon=True)
        self.auto_thread.start()

    def stop_auto_mode(self):
        self.running = False
        self.state_machine.transition(State.IDLE)
        self.log("Auto Mode stopped, reverting to manual control.", "warning")
        self.send_safe_stop("Auto mode disabled")

    def update_telemetry(self, msg):
        with self.lock:
            self.latest_sensors = {
                "temperature": msg.get("temperature", 0),
                "humidity": msg.get("humidity", 0),
                "pressure": msg.get("pressure", 1013),
                "light": msg.get("light", 0),
                "uvVoltage": msg.get("uvVoltage", 0),
                "soilMoisture": msg.get("soilMoisture", 0),
                "ultrasonic": msg.get("ultrasonic", 999.0)  # distance in cm
            }
            self.hardware_connected = bool(msg.get("hardware_connected", False))
            self.last_telemetry_time = msg.get('last_seen', time.time()) if self.hardware_connected else 0

    def update_latest_detection(self, detection):
        with self.lock:
            self.latest_detection = detection

    def update_latest_frame(self, frame_b64):
        with self.lock:
            self.latest_frame = frame_b64

    def update_obstacle_status(self, obstacle_status):
        with self.lock:
            self.latest_obstacle_status = obstacle_status

    def handle_ack(self, ack_data):
        cmd_id = ack_data.get("command_id")
        if cmd_id == self.last_cmd_id:
            self.log(f"Received ACK for command {cmd_id}.", "info")
            self.ack_event.set()

    def send_esp32_command(self, payload):
        """Sends command with tracking ID and robust zero-lag execution."""
        if not self.running or self.mode != 'auto':
            return False
        if not self.hardware_connected or time.time() - self.last_telemetry_time > 3:
            self.send_safe_stop('Telemetry expired during autonomous action')
            return False
        self.cmd_counter += 1
        cmd_id = f"cmd_{self.cmd_counter}_{int(time.time())}"
        self.last_cmd_id = cmd_id
        self.ack_event.clear()

        # Build message
        msg = {
            "type": "combined",
            "command_id": cmd_id,
            "motor_left": payload.get("motor_left", 0),
            "motor_right": payload.get("motor_right", 0),
            "solenoid": payload.get("solenoid", "none"),
            "pump_duration_s": float(payload.get("pump_duration_s", 0.0))
        }

        if self.send_tcp_cmd_callback:
            is_cruise = payload.get("motor_left") == 200 and payload.get("motor_right") == 200 and payload.get("solenoid") == "none"
            if not is_cruise or (self.cmd_counter % 20 == 0):
                self.log(f"Actuator command {cmd_id}: {json.dumps(payload)}", "info")
            sent_to_hw = self.send_tcp_cmd_callback(msg)
            
            if not sent_to_hw:
                self.log('ESP32 unavailable; command was not executed.', 'error')
                self.send_safe_stop('Command delivery failed')
                return False
            acked = self.ack_event.wait(timeout=2.0)
            if not acked:
                self.log(f'No device acknowledgement for {cmd_id}.', 'error')
                self.send_safe_stop('Device acknowledgement timed out')
            return acked

        else:
            self.log("Actuator sender callback is missing. Cannot send command.", "error")
            return False

    def send_safe_stop(self, reason):
        self.running = False
        self.mode = 'manual'
        self.state_machine.safe_stop(reason)
        stop_cmd = {
            "motor_left": 0,
            "motor_right": 0,
            "solenoid": "none",
            "pump_duration_s": 0.0
        }
        # Send without waiting for ACK if system is killed/stopping
        if self.send_tcp_cmd_callback:
            self.send_tcp_cmd_callback({
                "type": "combined",
                "command_id": "emergency_stop",
                **stop_cmd
            })
        if self.socket_emit_callback:
            self.socket_emit_callback("state_changed", {"state": State.SAFE_STOP.value, "reason": reason})
            self.socket_emit_callback('mode_status', {'mode': 'manual'})

    def _auto_loop(self):
        self.log("Auto loop thread launched.", "info")
        while self.running and self.mode == "auto":
            try:
                # 1. Get snapshot of inputs safely
                with self.lock:
                    sensors = dict(self.latest_sensors)
                    detection = self.latest_detection
                    obstacle_status = self.latest_obstacle_status
                    frame = self.latest_frame
                    telemetry_age = time.time() - self.last_telemetry_time

                # 2. Network connection check (graceful 15.0s window)
                if not self.hardware_connected or telemetry_age > 3.0:
                    self.log("Network telemetry signal delayed (> 15s). Pausing movement for safety.", "warning")
                    self.send_safe_stop("Telemetry signal timeout")
                    break

                # 3. Vision & Ultrasonic Obstacle Safety Checks (Camera-First AI Guidance)
                if obstacle_status and obstacle_status.get("detected"):
                    v_action = obstacle_status.get("action", "FORWARD")
                    warning_msg = obstacle_status.get("warning", "Obstacle in path")
                    self.log(f"Camera Visual Avoidance: {v_action} | {warning_msg}", "warning")
                    if v_action == "STOP":
                        self.send_esp32_command({
                            "motor_left": 0,
                            "motor_right": 0,
                            "solenoid": "none",
                            "pump_duration_s": 0.0
                        })
                        time.sleep(0.3)
                        continue
                    elif v_action == "STEER_LEFT":
                        self.send_esp32_command({
                            "motor_left": -180,
                            "motor_right": 180,
                            "solenoid": "none",
                            "pump_duration_s": 0.0
                        })
                        time.sleep(0.35)
                        continue
                    elif v_action == "STEER_RIGHT":
                        self.send_esp32_command({
                            "motor_left": 180,
                            "motor_right": -180,
                            "solenoid": "none",
                            "pump_duration_s": 0.0
                        })
                        time.sleep(0.35)
                        continue

                # Ultrasonic distance hardware backup check (0.1cm to 20.0cm)
                ultrasonic_distance = sensors.get("ultrasonic", 999.0)
                if 0.1 < ultrasonic_distance < 20.0:
                    self.log(f"OBSTACLE DETECTED! Distance: {ultrasonic_distance}cm. Halting motors.", "warning")
                    self.send_esp32_command({
                        "motor_left": 0,
                        "motor_right": 0,
                        "solenoid": "none",
                        "pump_duration_s": 0.0
                    })
                    time.sleep(0.4)
                    continue

                # 4. State Machine logic
                current_state = self.state_machine.current_state

                if current_state == State.SCANNING:
                    # Check if YOLO detected a disease with conf > YOLO_CONFIDENCE_THRESHOLD
                    if detection and detection.get("confidence", 0.0) >= YOLO_CONFIDENCE_THRESHOLD:
                        self.log(f"High-confidence pathogen detected ({detection['class']} - {detection['confidence']}). Transitioning to DIAGNOSING...", "success")
                        
                        # Stop the robot
                        self.send_esp32_command({
                            "motor_left": 0,
                            "motor_right": 0,
                            "solenoid": "none",
                            "pump_duration_s": 0.0
                        })
                        
                        self.state_machine.transition(State.DIAGNOSING)
                        if self.socket_emit_callback:
                            self.socket_emit_callback("state_changed", {"state": State.DIAGNOSING.value, "disease": detection['class']})
                    else:
                        # Continue patrol forward at steady operational speed (200)
                        self.send_esp32_command({
                            "motor_left": 200,
                            "motor_right": 200,
                            "solenoid": "none",
                            "pump_duration_s": 0.0
                        })
                        time.sleep(0.1)

                elif current_state == State.DIAGNOSING:
                    # Step A: Perform Vision VLM analysis
                    if not frame:
                        self.log("Camera frame missing in diagnosing phase. Retrying...", "warning")
                        time.sleep(0.5)
                        continue
                        
                    self.log("Invoking vision_analyzer (qwen2.5vl:7b)...", "info")
                    analysis = vision_analyzer.analyze_disease(frame, detection, sensors)
                    
                    self.log(f"Diagnosis completed: {analysis.get('disease')}. Severity: {analysis.get('severity')}.", "success")
                    if self.socket_emit_callback:
                        self.socket_emit_callback("ai_analysis_report", analysis)

                    # Step B: Generate robot actuator commands
                    self.log("Invoking command_generator (qwen2.5-coder:7b)...", "info")
                    commands = command_generator.generate_robot_commands(analysis, self.robot_state)
                    
                    self.state_machine.transition(State.ACTING)
                    if self.socket_emit_callback:
                        self.socket_emit_callback("state_changed", {"state": State.ACTING.value})

                    # Step C: Execute Treatment Sequences sequentially (insert → spray → retract)
                    # Step 1: Insert Probe
                    self.log("Autonomous treatment: Inserting soil probe...", "info")
                    success = self.send_esp32_command({
                        "motor_left": 0,
                        "motor_right": 0,
                        "solenoid": "insert_probe",
                        "pump_duration_s": 0.0
                    })
                    if not success: break
                    self.robot_state["solenoid_inserted"] = True
                    time.sleep(2.0)  # Wait for solenoid to push probe into ground

                    # Step 2: Spray
                    duration = max(0.0, min(10.0, float(commands.get("pump_duration_sec", 5.0))))
                    self.log(f"Autonomous treatment: Spraying fungicide for {duration} seconds...", "info")
                    success = self.send_esp32_command({
                        "motor_left": 0,
                        "motor_right": 0,
                        "solenoid": "none",
                        "pump_duration_s": duration
                    })
                    if not success: break
                    self.robot_state["treatment_completed"] = True
                    time.sleep(duration + 1.0)  # Wait for spray execution to finish

                    # Step 3: Retract
                    self.log("Autonomous treatment: Retracting soil probe...", "info")
                    success = self.send_esp32_command({
                        "motor_left": 0,
                        "motor_right": 0,
                        "solenoid": "retract",
                        "pump_duration_s": 0.0
                    })
                    if not success: break
                    self.robot_state["solenoid_inserted"] = False
                    self.robot_state["treatment_completed"] = False
                    time.sleep(2.0)  # Wait for solenoid retraction travel

                    # Step D: Resume Patrol
                    self.log("Treatment sequence complete. Resuming patrol...", "success")
                    self.state_machine.transition(State.SCANNING)
                    if self.socket_emit_callback:
                        self.socket_emit_callback("state_changed", {"state": State.SCANNING.value})

                elif current_state == State.SAFE_STOP:
                    self.log("Swarm is in SAFE_STOP state. Idle loop run.", "warning")
                    break

            except Exception as ex:
                self.log(f"Exception in AI loop thread: {ex}", "error")
                self.send_safe_stop(f"Brain thread crash: {str(ex)}")
                break

            time.sleep(0.25 if current_state == State.SCANNING else 1.0)
