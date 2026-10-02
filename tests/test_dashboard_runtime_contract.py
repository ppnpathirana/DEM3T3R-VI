"""
@file: test_dashboard_runtime_contract.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""Exercise the real loader without starting cameras, networks, or CUDA."""
import ast
import pathlib
import threading
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class DashboardRuntimeTests(unittest.TestCase):
    def loader(self, present=True, cuda=True, fail=False):
        tree = ast.parse((ROOT / 'backend/ws_server.py').read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'load_yolo_model')
        devices = []
        def model(path):
            if fail:
                raise RuntimeError('test corrupt model')
            return types.SimpleNamespace(to=lambda device: devices.append(device) or 'loaded')
        scope = dict(active_model='old', CROP_MODEL_MAP={}, MODELS_DIR='models',
                     os=types.SimpleNamespace(path=types.SimpleNamespace(join=lambda *args: '/'.join(args), isfile=lambda _: present)),
                     model_lock=threading.Lock(), YOLO=model,
                     torch=types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: cuda, empty_cache=lambda: None)))
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'loader', 'exec'), scope)
        return scope, devices

    def test_missing_corrupt_and_unavailable_gpu_degrade(self):
        for options in [dict(present=False), dict(cuda=False), dict(fail=True)]:
            scope, _ = self.loader(**options)
            self.assertFalse(scope['load_yolo_model']('cabbage'))
            self.assertIsNone(scope['active_model'])

    def test_model_is_pinned_to_first_cuda_device(self):
        scope, devices = self.loader()
        self.assertTrue(scope['load_yolo_model']('tomato'))
        self.assertEqual(devices, ['cuda:0'])

    def test_backend_syntax_and_clean_stream(self):
        for path in ['backend/ws_server.py', 'backend/vla_engine.py', 'CropGuard_App.pyw']:
            ast.parse((ROOT / path).read_text(encoding='utf-8'))
        source = (ROOT / 'backend/ws_server.py').read_text(encoding='utf-8')
        self.assertIn('draw_hud=False', source)
        self.assertNotIn('results[0].plot()', source)
        self.assertNotIn('time.sleep(', source)


if __name__ == '__main__':
    unittest.main()
