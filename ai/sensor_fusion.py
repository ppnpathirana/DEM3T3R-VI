"""
Sensor Fusion - Combines vision + environmental data for context-aware diagnosis
"""

class SensorFusion:
    def __init__(self):
        self.latest_sensors = {}
        
    def update_sensors(self, sensor_data):
        """Store latest sensor readings"""
        self.latest_sensors = sensor_data
    
    def get_context(self):
        """Get current environmental context for AI reasoning"""
        return {
            'temperature_c': self.latest_sensors.get('temperature_c', 25.0),
            'humidity_pct': self.latest_sensors.get('humidity_pct', 60.0),
            'pressure_hpa': self.latest_sensors.get('pressure_hpa', 1013.0),
            'lux': self.latest_sensors.get('lux', 1000.0),
            'uv_voltage': self.latest_sensors.get('uv_voltage', 0.5),
            'soil1_raw': self.latest_sensors.get('soil1_raw', 2000),
            'soil2_raw': self.latest_sensors.get('soil2_raw', 2000)
        }
    
    def is_stress_condition(self):
        """Check if environmental conditions suggest abiotic stress"""
        temp = self.latest_sensors.get('temperature_c', 25.0)
        humidity = self.latest_sensors.get('humidity_pct', 60.0)
        soil = self.latest_sensors.get('soil1_raw', 2000)
        
        # High temp + low soil moisture = water stress
        if temp > 35 and soil < 1500:
            return True, "water stress likely"
        
        # Very high humidity = fungal risk
        if humidity > 90:
            return True, "high humidity - fungal risk"
        
        return False, "normal conditions"
