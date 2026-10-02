"""
Actuator Control - Sends motor/solenoid/pump commands to ESP32
Implements safety timeouts and severity-based dosing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from config.settings import PUMP_DURATION_MAP, SOLENOID_TIMEOUT

class Actuator:
    def __init__(self, tcp_server):
        self.tcp = tcp_server
        self.cmd_counter = 0
        
    def move(self, left_speed, right_speed):
        """Send motor speed command (-255 to +255)"""
        cmd = {
            'type': 'motor',
            'cmd_id': self.cmd_counter,
            'left': left_speed,
            'right': right_speed,
            'timestamp': int(time.time() * 1000)
        }
        self.cmd_counter += 1
        self.tcp.send_command(cmd)
        print(f"[ACT] Motor: L={left_speed} R={right_speed}")
    
    def stop_motors(self):
        """Emergency stop all motors"""
        self.move(0, 0)
        print("[ACT] Motors STOPPED")
    
    def insert_probe(self):
        """Activate solenoid to insert soil probe"""
        cmd = {
            'type': 'solenoid',
            'cmd_id': self.cmd_counter,
            'action': 'insert',
            'timeout_ms': SOLENOID_TIMEOUT
        }
        self.cmd_counter += 1
        self.tcp.send_command(cmd)
        print("[ACT] Probe INSERTING")
    
    def retract_probe(self):
        """Retract soil probe"""
        cmd = {
            'type': 'solenoid',
            'cmd_id': self.cmd_counter,
            'action': 'retract',
            'timeout_ms': SOLENOID_TIMEOUT
        }
        self.cmd_counter += 1
        self.tcp.send_command(cmd)
        print("[ACT] Probe RETRACTING")
    
    def spray(self, severity='mild'):
        """Activate pump for severity-based duration"""
        duration = PUMP_DURATION_MAP.get(severity, 3.0)
        cmd = {
            'type': 'pump',
            'cmd_id': self.cmd_counter,
            'duration_s': duration
        }
        self.cmd_counter += 1
        self.tcp.send_command(cmd)
        print(f"[ACT] Pump: {severity} severity → {duration}s spray")
