"""
@file: mock_sensor_data.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Mock Sensor Data - Generates fake telemetry for testing without hardware
"""
import random
import time

class MockSensorData:
    def __init__(self):
        self.seq = 0
        
    def generate(self):
        """Generate one packet of mock sensor data"""
        self.seq += 1
        return {
            'type': 'telemetry',
            'seq': self.seq,
            'timestamp': int(time.time() * 1000),
            'temperature_c': round(random.uniform(20.0, 35.0), 1),
            'humidity_pct': round(random.uniform(40.0, 90.0), 1),
            'pressure_hpa': round(random.uniform(1000.0, 1020.0), 1),
            'lux': round(random.uniform(100.0, 5000.0), 0),
            'uv_voltage': round(random.uniform(0.1, 2.0), 2),
            'soil1_raw': random.randint(1000, 3500),
            'soil2_raw': random.randint(1000, 3500),
            'valid_flags': 0x1F  # All sensors valid
        }

if __name__ == "__main__":
    mock = MockSensorData()
    for i in range(5):
        data = mock.generate()
        print(data)
        time.sleep(0.5)
