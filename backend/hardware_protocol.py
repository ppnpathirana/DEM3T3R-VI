"""Canonical telemetry shared by ESP32 TCP, serial and HTTP transports."""
import time
import math

ALIASES = {
    'temperature': ('temp',), 'humidity': ('hum',), 'pressure': ('pres',),
    'light': ('lux',), 'uvVoltage': ('uvVolt', 'uv_voltage'),
    'soilMoisture': ('rawSoil1',), 'soilMoisture2': ('soilMoisture_2', 'rawSoil2'),
    'soil1Pct': ('soil1',), 'soil2Pct': ('soil2',),
    'latitude': ('lat',), 'longitude': ('lon',), 'altitude': ('alt',),
    'satellites': ('sats',), 'ultrasonic': ('dist_front',),
    'battery': ('bat', 'voltage'),
    'motor_left': ('left_speed',), 'motor_right': ('right_speed',),
    'pump_on': ('pump', 'relay1'), 'sol1_on': ('sol1', 'relay2'),
    'sol2_on': ('sol2', 'relay3'), 'spare_on': ('spare', 'relay4'),
}

def normalize_telemetry(payload, source, now=None):
    result = dict(payload)
    for field, aliases in ALIASES.items():
        if field not in result:
            for alias in aliases:
                if alias in payload:
                    result[field] = payload[alias]
                    break
    for field in ('pump_on', 'sol1_on', 'sol2_on', 'spare_on', 'fix'):
        if field in result:
            result[field] = str(result[field]).lower() in ('true', '1', 'on')
    result.update(type='telemetry', source=source, hardware_connected=True,
                  simulated=False, last_seen=time.time() if now is None else now)
    return result


def normalize_command(payload):
    """Validate actuator commands at the final transport boundary."""
    if not isinstance(payload, dict):
        raise ValueError('Command must be an object')
    result = dict(payload)
    kind = result.get('type')
    if kind not in ('heartbeat', 'combined', 'relay', 'drive'):
        raise ValueError('Unsupported hardware command')

    def number(key, low, high, default=0):
        try:
            value = float(result.get(key, default))
        except (ValueError, TypeError):
            raise ValueError(f'Invalid {key}') from None
        if not math.isfinite(value):
            raise ValueError(f'Invalid {key}')
        return max(low, min(high, value))

    if kind == 'combined':
        result['motor_left'] = int(number('motor_left', -255, 255))
        result['motor_right'] = int(number('motor_right', -255, 255))
        result['pump_duration_s'] = number('pump_duration_s', 0, 10)
        solenoid = result.get('solenoid', 'none')
        if solenoid not in ('none', 'insert_probe', 'retract', 'sol1_on', 'sol1_off',
                            'sol2_on', 'sol2_off', 'pump_on', 'pump_off', 'spare_on', 'spare_off'):
            raise ValueError('Invalid solenoid action')
        result['solenoid'] = solenoid
    elif kind == 'drive':
        result['throttle'] = int(number('throttle', -255, 255))
        result['steering'] = int(number('steering', -255, 255))
    elif kind == 'relay':
        target = str(result.get('target', '')).upper()
        target = {'PUMP': 'R1', 'SOL1': 'R2', 'SOL2': 'R3', 'SPARE': 'R4'}.get(target, target)
        if target not in ('R1', 'R2', 'R3', 'R4'):
            raise ValueError('Invalid relay target')
        state = str(result.get('state', '')).lower()
        if state not in ('on', 'off', 'true', 'false', '1', '0'):
            raise ValueError('Relay state must explicitly be on or off')
        result.update(target=target, state='on' if state in ('on', 'true', '1') else 'off')
    return result


def command_energizes_outputs(command):
    if command['type'] == 'relay':
        return command['state'] == 'on'
    if command['type'] == 'drive':
        return bool(command['throttle'] or command['steering'])
    if command['type'] == 'combined':
        return bool(command['motor_left'] or command['motor_right'] or
                    command['pump_duration_s'] or command['solenoid'] in
                    ('insert_probe', 'sol1_on', 'sol2_on', 'pump_on', 'spare_on'))
    return False
