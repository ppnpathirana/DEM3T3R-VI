"""
@file: tcp_server.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
TCP Server - High-reliability communication bridge between Single ESP32-S3 and DEM3T3R V1 backend.
Supports:
- Unified ESP32-S3 onboard sensor stream (GPS, dual ultrasonics, BME280, BH1750, GUVA-S12SD UV, dual Soil Moisture)
- Low-latency real-time telemetry streaming
- Sequence numbered command acknowledgments
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import socket
import json
import threading
import time
from config.settings import TCP_HOST, TCP_PORT, COMMAND_TIMEOUT_MS

try:
    from backend.ws_server import broadcast_telemetry
except ImportError:
    broadcast_telemetry = None

class TCPServer:
    def __init__(self, host=TCP_HOST, port=TCP_PORT, ack_timeout_ms=COMMAND_TIMEOUT_MS):
        self.host = host
        self.port = port
        self.ack_timeout_sec = ack_timeout_ms / 1000.0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.clients = []
        self.running = False
        self.last_telemetry = {}
        self.pending_acks = {}  # cmd_id -> threading.Event
        self.lock = threading.Lock()
        
    def start(self):
        """Start listening for ESP32 connections"""
        self.sock.bind((self.host, self.port))
        self.sock.listen(2)
        self.running = True
        print(f"[TCP] Server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client, addr = self.sock.accept()
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
                client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                client.settimeout(2.0)
                print(f"[TCP] ESP32 connected from {addr}")
                with self.lock:
                    self.clients.append(client)
                threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"[TCP] Accept error: {e}")
    
    def handle_client(self, client):
        """Handle incoming telemetry from ESP32"""
        buffer = ""
        while self.running:
            try:
                data = client.recv(2048).decode('utf-8')
                if not data:
                    break
                buffer += data
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.process_message(line.strip(), client)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[TCP] Client connection lost: {e}")
                break
        
        with self.lock:
            if client in self.clients:
                self.clients.remove(client)
        try:
            client.close()
        except:
            pass
        print("[TCP] ESP32 disconnected")
    
    def process_message(self, message, client):
        """Parse and route incoming JSON messages"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'telemetry')
            
            if msg_type == 'telemetry':
                self.handle_telemetry(data)
            elif msg_type == 'ack':
                self.handle_ack(data)
            elif msg_type in ['handshake', 'hello']:
                print(f"[TCP] Handshake/Hello received from: {data.get('device', 'ESP32')} v{data.get('version', '1.0')} IP: {data.get('ip', 'unknown')}")
                # Respond with handshake ACK
                ack_response = json.dumps({'type': 'handshake_ack', 'status': 'connected', 'timestamp': time.time()}) + '\n'
                try:
                    client.sendall(ack_response.encode('utf-8'))
                except:
                    pass
            else:
                print(f"[TCP] Unknown message type: {msg_type}")
        except json.JSONDecodeError:
            print(f"[TCP] Invalid JSON received: {message[:100]}")
    
    def handle_telemetry(self, data):
        """Process sensor telemetry from Single ESP32-S3 node"""
        # Normalize and unpack sensor fields
        normalized = {
            'seq': data.get('seq', 0),
            'timestamp': data.get('timestamp', time.time()),
            # Positioning & Spatial
            'latitude': float(data.get('latitude', data.get('lat', 6.9271))),
            'longitude': float(data.get('longitude', data.get('lon', 79.8612))),
            'altitude': float(data.get('altitude', data.get('alt', 10.0))),
            'speed': float(data.get('speed', 0.0)),
            'heading': float(data.get('heading', 0.0)),
            'ultrasonic_front': float(data.get('ultrasonic_front', data.get('ultrasonic', 999.0))),
            'ultrasonic_back': float(data.get('ultrasonic_back', 999.0)),
            'encoder_left': int(data.get('encoder_left', 0)),
            'encoder_right': int(data.get('encoder_right', 0)),
            
            # Onboard environmental sensors
            'temperature': float(data.get('temperature', data.get('bme280_temp', 28.0))),
            'humidity': float(data.get('humidity', data.get('bme280_humidity', 75.0))),
            'pressure': float(data.get('pressure', data.get('bme280_pressure', 1013.0))),
            'light': float(data.get('light', data.get('bh1750_lux', 500.0))),
            'uvVoltage': float(data.get('uvVoltage', data.get('guva_uv', 0.5))),
            'uvIndex': float(data.get('uvIndex', 0.0)),
            'soilMoisture': float(data.get('soilMoisture', data.get('soil_moisture_1', 2100.0))),
            'soilMoisture_2': float(data.get('soilMoisture_2', data.get('soil_moisture_2', 2050.0))),
            'soil1Pct': int(data.get('soil1Pct', 0)),
            'soil2Pct': int(data.get('soil2Pct', 0)),
            
            # Actuator & Motion states
            'pump_on': bool(data.get('pump_on', False)),
            'sol1_on': bool(data.get('sol1_on', False)),
            'sol2_on': bool(data.get('sol2_on', False)),
            'spare_on': bool(data.get('spare_on', False)),
            'motion': str(data.get('motion', 'STOPPED')),
            'left_speed': int(data.get('left_speed', 0)),
            'right_speed': int(data.get('right_speed', 0)),
            'satellites': int(data.get('satellites', 0)),
            'fix': bool(data.get('fix', data.get('gps_fix', False)))
        }
        
        with self.lock:
            self.last_telemetry = normalized
            
        if broadcast_telemetry:
            try:
                broadcast_telemetry(normalized)
            except Exception as e:
                pass
                
        return normalized
    
    def handle_ack(self, data):
        """Process acknowledgment from ESP32 for command delivery"""
        cmd_id = data.get('cmd_id') or data.get('command_id')
        if cmd_id:
            with self.lock:
                event = self.pending_acks.get(cmd_id)
                if event:
                    event.set()
            print(f"[TCP] Command ACK confirmed: {cmd_id}")
    
    def send_command(self, command, wait_ack=False):
        """
        Send command to connected ESP32s.
        If wait_ack=True, waits up to ack_timeout_sec before returning.
        Returns True if sent (and acknowledged if requested), False otherwise.
        """
        cmd_id = command.get('cmd_id')
        ack_event = None
        
        if wait_ack and cmd_id:
            ack_event = threading.Event()
            with self.lock:
                self.pending_acks[cmd_id] = ack_event
                
        msg = json.dumps(command) + '\n'
        sent_any = False
        
        with self.lock:
            active_clients = list(self.clients)
            
        for client in active_clients:
            try:
                client.sendall(msg.encode('utf-8'))
                sent_any = True
            except Exception as e:
                print(f"[TCP] Send command error: {e}")
                
        if wait_ack and ack_event:
            acked = ack_event.wait(timeout=self.ack_timeout_sec)
            with self.lock:
                self.pending_acks.pop(cmd_id, None)
            if not acked:
                print(f"[TCP] WARNING: Command {cmd_id} ACK timeout ({self.ack_timeout_sec}s)!")
            return acked
            
        return sent_any

    def get_latest_telemetry(self):
        with self.lock:
            return dict(self.last_telemetry)
    
    def stop(self):
        """Shutdown server"""
        self.running = False
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        try:
            self.sock.close()
        except:
            pass
