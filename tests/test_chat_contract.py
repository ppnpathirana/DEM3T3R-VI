import ast
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = pathlib.Path(__file__).resolve().parents[1] / 'backend/ws_server.py'


class ChatContractTests(unittest.TestCase):
    def run_chat(self, available):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        handler = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'handle_chat_message')
        handler.decorator_list = []
        events, prompts = [], []
        def post(url, json, **kwargs):
            prompts.append(json['prompt'])
            return types.SimpleNamespace(status_code=200 if available else 503, json=lambda: {'response': 'Test advice'})
        settings = types.ModuleType('config.settings')
        settings.GEMINI_KEYS = []
        settings.GROK_KEY = ''
        settings.OLLAMA_MODEL_VL = 'test'
        settings.OLLAMA_API_URL = 'http://local.test'
        scope = dict(request=types.SimpleNamespace(sid='client-one'),
                     socketio=types.SimpleNamespace(emit=lambda *args, **kwargs: events.append((args, kwargs))),
                     is_online_chat=lambda: False, current_crop='rice', json=json,
                     requests=types.SimpleNamespace(post=post), local_http=types.SimpleNamespace(post=post), print=lambda *args: None)
        with patch.dict(sys.modules, {'config.settings': settings}):
            exec(compile(ast.Module(body=[handler], type_ignores=[]), 'chat', 'exec'), scope)
            scope['handle_chat_message']({'message': 'Help', 'crop': 'tomato', 'request_id': 'request-one', 'detections': [{'class': 'Early_blight', 'confidence': .8}]})
        return events, prompts

    def test_reply_is_private_and_correlated(self):
        events, prompts = self.run_chat(True)
        self.assertEqual(events[0][1], {'to': 'client-one'})
        self.assertEqual(events[0][0][1]['request_id'], 'request-one')
        self.assertIn('tomato', prompts[0])
        self.assertIn('Early_blight', prompts[0])

    def test_unavailable_service_is_reported(self):
        events, _ = self.run_chat(False)
        self.assertIn('unavailable', events[0][0][1]['message'])


if __name__ == '__main__':
    unittest.main()
