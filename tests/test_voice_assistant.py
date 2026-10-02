"""
@file: test_voice_assistant.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import pytest
from backend.voice_assistant import TrilingualVoiceAssistant


def test_voice_assistant_language_detection():
    assistant = TrilingualVoiceAssistant()
    assert assistant.detect_language("move forward") == "en"
    assert assistant.detect_language("emergency stop") == "en"


def test_voice_assistant_english_intents():
    assistant = TrilingualVoiceAssistant()
    
    intent, conf, lang = assistant.parse_intent("move forward")
    assert intent == "MOVE_FORWARD"
    assert conf > 0.6
    assert lang == "en"

    intent, conf, lang = assistant.parse_intent("emergency stop")
    assert intent == "EMERGENCY_STOP"

    intent, conf, lang = assistant.parse_intent("spray pump")
    assert intent == "SPRAY_PUMP"

    intent, conf, lang = assistant.parse_intent("check soil")
    assert intent == "SOIL_PROBE"

    intent, conf, lang = assistant.parse_intent("turn left")
    assert intent == "TURN_LEFT"

    intent, conf, lang = assistant.parse_intent("turn right")
    assert intent == "TURN_RIGHT"

    intent, conf, lang = assistant.parse_intent("reverse")
    assert intent == "MOVE_BACKWARD"

    intent, conf, lang = assistant.parse_intent("auto mode")
    assert intent == "MODE_AUTO"

    intent, conf, lang = assistant.parse_intent("manual mode")
    assert intent == "MODE_MANUAL"

    intent, conf, lang = assistant.parse_intent("robot status")
    assert intent == "STATUS_QUERY"


def test_voice_assistant_execution_callback():
    dispatched = []

    def mock_cb(intent, action):
        dispatched.append((intent, action))

    assistant = TrilingualVoiceAssistant(command_callback=mock_cb)

    res = assistant.execute_command("emergency stop")
    assert res["executed"] is True
    assert res["intent"] == "EMERGENCY_STOP"
    assert len(dispatched) == 1
    assert dispatched[0][0] == "EMERGENCY_STOP"
    assert dispatched[0][1]["hard_brake"] is True


def test_voice_assistant_unknown_query():
    assistant = TrilingualVoiceAssistant()
    res = assistant.execute_command("play some music on rover")
    assert res["intent"] == "UNKNOWN"
    assert res["executed"] is False
    assert "not recognized" in res["response_text"].lower()


def test_voice_does_not_report_failed_delivery_as_execution():
    assistant = TrilingualVoiceAssistant(command_callback=lambda intent, action: False)
    result = assistant.execute_command('spray pump')
    assert result['executed'] is False
    assert 'not delivered' in result['response_text']
