"""
@file: main.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 Main Entry Point
Orchestrates all components: TCP server, WebSocket, state machine, AI
"""
import threading
import time
from backend.tcp_server import TCPServer
from backend.ws_server import start_server as start_ws_server
from backend.state_machine import StateMachine
from backend.actuator import Actuator
from ai.sensor_fusion import SensorFusion
from mock.mock_sensor_data import MockSensorData

def main():
    print("=" * 60)
    print("DEM3T3R V1 - Autonomous Crop Disease Detection Robot")
    print("=" * 60)
    
    # Initialize components
    tcp_server = TCPServer()
    state_machine = StateMachine()
    actuator = Actuator(tcp_server)
    sensor_fusion = SensorFusion()
    mock_sensors = MockSensorData()
    
    # Start WebSocket server in background
    ws_thread = threading.Thread(target=start_ws_server, daemon=True)
    ws_thread.start()
    print("[MAIN] WebSocket server started")
    
    # Start TCP server in background
    tcp_thread = threading.Thread(target=tcp_server.start, daemon=True)
    tcp_thread.start()
    print("[MAIN] TCP server started")
    
    # Main loop
    try:
        while True:
            # Generate mock sensor data (remove when real sensors connected)
            sensor_data = mock_sensors.generate()
            sensor_fusion.update_sensors(sensor_data)
            
            # Check state machine timeout
            state_machine.check_timeout()
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
        tcp_server.stop()

if __name__ == "__main__":
    main()
