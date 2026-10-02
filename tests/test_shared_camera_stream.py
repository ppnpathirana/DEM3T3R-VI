"""
@file: test_shared_camera_stream.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import ast
import pathlib
import threading
import unittest


class SharedCameraTests(unittest.TestCase):
    def test_multiple_viewers_share_packets_without_inference(self):
        path = pathlib.Path(__file__).resolve().parents[1] / 'backend/ws_server.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate_frames')
        scope = dict(stream_condition=threading.Condition(), stream_packet=b'frame-one', stream_sequence=1)
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'stream', 'exec'), scope)
        first, second = scope['generate_frames'](), scope['generate_frames']()
        self.assertEqual(next(first), b'frame-one')
        self.assertEqual(next(second), b'frame-one')
        with scope['stream_condition']:
            scope['stream_packet'] = b'frame-two'
            scope['stream_sequence'] = 2
            scope['stream_condition'].notify_all()
        self.assertEqual(next(first), b'frame-two')
        self.assertEqual(next(second), b'frame-two')
        first.close()
        second.close()


if __name__ == '__main__':
    unittest.main()
