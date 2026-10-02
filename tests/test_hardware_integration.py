"""Offline protocol tests; never imports or starts the AI/hardware services."""
import ast
import json
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from backend.hardware_protocol import normalize_telemetry, normalize_command, command_energizes_outputs


class HardwareIntegrationTests(unittest.TestCase):
    def test_http_and_tcp_have_same_fields(self):
        result = normalize_telemetry({'temp': 25, 'hum': 0, 'rawSoil1': 2400,
            'soil1': 30, 'rawSoil2': 2100, 'soil2': 50, 'lat': 6.9, 'lon': 79.8,
            'left_speed': -150, 'right_speed': 150, 'pump': 'off', 'sol1': 1}, 'http', 10)
        self.assertEqual(result['humidity'], 0)
        self.assertEqual(result['soilMoisture'], 2400)
        self.assertEqual(result['soil1Pct'], 30)
        self.assertEqual(result['motor_left'], -150)
        self.assertFalse(result['pump_on'])
        self.assertTrue(result['sol1_on'])
        self.assertEqual(result['longitude'], 79.8)
        self.assertNotIn('battery', result)

    def load_function(self, name, namespace):
        tree = ast.parse(Path('backend/ws_server.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        node.decorator_list = []
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<hardware-test>', 'exec'), namespace)
        return namespace[name]

    def test_commands_do_not_fabricate_actuator_feedback(self):
        events, packets = [], []
        namespace = dict(json=json, clients_lock=threading.Lock(), serial_conn_lock=threading.Lock(),
            control_lock=threading.RLock(), emergency_stop_latched=False,
            normalize_command=normalize_command, command_energizes_outputs=command_energizes_outputs,
            active_serial_conn=None, connected_clients=[], latest_telemetry={'pump_on': False},
            socketio=SimpleNamespace(emit=lambda *args: events.append(args)))
        self.load_function('dispatch_hardware_command', namespace)
        send = self.load_function('send_to_esp32', namespace)
        self.assertFalse(send({'type': 'relay', 'target': 'R1', 'state': 'on'}))
        namespace['connected_clients'].append(SimpleNamespace(sendall=packets.append))
        self.assertTrue(send({'type': 'relay', 'target': 'R1', 'state': 'on'}))
        self.assertEqual(json.loads(packets[0]), {'type': 'relay', 'target': 'R1', 'state': 'on'})
        self.assertFalse(namespace['latest_telemetry']['pump_on'])
        self.assertFalse(any(e[0] == 'telemetry' for e in events))
        namespace['emergency_stop_latched'] = True
        self.assertFalse(send({'type': 'relay', 'target': 'R1', 'state': 'on'}))
        self.assertTrue(send({'type': 'relay', 'target': 'R1', 'state': 'off'}))

    def test_command_validation_and_limits(self):
        command = normalize_command({'type': 'combined', 'motor_left': 999,
                                     'motor_right': -999, 'pump_duration_s': 100})
        self.assertEqual(command['motor_left'], 255)
        self.assertEqual(command['motor_right'], -255)
        self.assertEqual(command['pump_duration_s'], 10)
        for invalid in ({'type': 'relay', 'target': 'R9', 'state': 'on'},
                        {'type': 'relay', 'target': 'R1', 'state': 'toggle'},
                        {'type': 'combined', 'pump_duration_s': float('nan')},
                        {'type': 'combined', 'motor_left': 'bad'}):
            with self.assertRaises(ValueError):
                normalize_command(invalid)

    def test_fragmented_tcp_telemetry_and_ack(self):
        events, readings, acks = [], [], []
        raw = (json.dumps({'type': 'telemetry', 'temp': 26, 'soilMoisture_2': 1800,
                           'left_speed': 100, 'right_speed': -100}) + '\n' +
               json.dumps({'type': 'ack', 'command_id': 'test-1'}) + '\n').encode()
        chunks = iter([raw[:17], raw[17:], b''])
        client = SimpleNamespace(recv=lambda size: next(chunks), close=lambda: None)
        namespace = dict(json=json, time=time, normalize_telemetry=normalize_telemetry,
            latest_telemetry={}, clients_lock=threading.Lock(), connected_clients=[client],
            socketio=SimpleNamespace(emit=lambda *args: events.append(args)),
            brain=SimpleNamespace(update_telemetry=readings.append, handle_ack=acks.append))
        self.load_function('handle_esp32', namespace)(client)
        self.assertEqual(readings[0]['temperature'], 26)
        self.assertEqual(readings[0]['soilMoisture2'], 1800)
        self.assertEqual(readings[0]['motor_right'], -100)
        self.assertEqual(acks[0]['command_id'], 'test-1')
        self.assertFalse(namespace['connected_clients'])

    def test_health_reports_stale_device_as_disconnected(self):
        import os
        namespace = dict(time=time, os=os, jsonify=lambda value: value,
                         camera_connected=False,
                         emergency_stop_latched=False,
                         latest_telemetry={'hardware_connected': True, 'last_seen': time.time() - 5,
                                           'source': 'tcp', 'ip': '192.0.2.1'})
        health = self.load_function('api_health', namespace)
        self.assertEqual(health()['service'], 'cropguard')
        self.assertFalse(health()['hardware_connected'])
        namespace['latest_telemetry']['last_seen'] = time.time()
        self.assertTrue(health()['hardware_connected'])

    def test_manual_stop_overrides_differential_motor_inputs(self):
        commands = []
        brain = SimpleNamespace(mode='auto', set_mode=lambda mode: setattr(brain, 'mode', mode))
        namespace = dict(brain=brain, send_to_esp32=lambda packet: commands.append(packet))
        handler = self.load_function('handle_robot_move', namespace)
        handler({'direction': 'stop', 'motor_left': 255, 'motor_right': 255})
        self.assertEqual(brain.mode, 'manual')
        self.assertEqual(commands[0]['motor_left'], 0)
        self.assertEqual(commands[0]['motor_right'], 0)
        handler({'direction': 'forward', 'speed': 'invalid'})
        self.assertEqual(len(commands), 1)

    def test_cancelled_autonomy_cannot_send_later_commands(self):
        from backend.ai_brain import AIBrain
        commands = []
        brain = AIBrain(send_tcp_cmd_callback=lambda packet: commands.append(packet))
        brain.running = False
        brain.mode = 'manual'
        self.assertFalse(brain.send_esp32_command({'motor_left': 200, 'motor_right': 200}))
        self.assertEqual(commands, [])
        self.assertFalse(brain.set_mode('auto'))

    def test_voice_action_matches_parser_schema(self):
        commands, stops = [], []
        namespace = dict(brain=None, latch_emergency_stop=stops.append,
                         send_to_esp32=lambda packet: commands.append(packet) or True)
        handler = self.load_function('handle_voice_action', namespace)
        self.assertTrue(handler('SPRAY_PUMP', {'cmd': 'RELAY', 'relay': 1, 'state': 'ON', 'duration': 5}))
        self.assertEqual(commands[0]['pump_duration_s'], 5)
        handler('EMERGENCY_STOP', {'cmd': 'STOP'})
        self.assertTrue(stops)


if __name__ == '__main__':
    unittest.main()
