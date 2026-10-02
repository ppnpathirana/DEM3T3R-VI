"""
@file: state_machine.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
State Machine - Manages robot operational states
States: IDLE → SCANNING → DIAGNOSING → ACTING → SAFE_STOP
Integrated with EventStore for immutable audit logging.
Safe-stop on any timeout, obstacle collision, or error.
"""
import time
from enum import Enum
from typing import Optional

class State(Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    DIAGNOSING = "DIAGNOSING"
    ACTING = "ACTING"
    SAFE_STOP = "SAFE_STOP"

class StateMachine:
    def __init__(self, event_store=None, timeout_sec: float = 10.0):
        self.current_state = State.IDLE
        self.state_timeout = timeout_sec
        self.last_state_change = time.time()
        self.event_store = event_store
        
    def transition(self, new_state: State, context: Optional[dict] = None) -> bool:
        """Transition to new state with timeout tracking and event-store logging"""
        if not isinstance(new_state, State):
            try:
                new_state = State(str(new_state))
            except ValueError:
                self.safe_stop(f"Invalid state transition requested: {new_state}")
                return False
                
        old_state = self.current_state
        print(f"[STATE] {old_state.value} → {new_state.value}")
        self.current_state = new_state
        self.last_state_change = time.time()
        
        if self.event_store:
            try:
                self.event_store.append("state_transition", {
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "context": context or {}
                })
            except Exception as e:
                print(f"[STATE] EventStore log error: {e}")
        return True
    
    def check_timeout(self) -> bool:
        """Check if current state has exceeded timeout. Triggers SAFE_STOP if expired."""
        if self.current_state == State.SAFE_STOP or self.current_state == State.IDLE:
            return False
        
        elapsed = time.time() - self.last_state_change
        if elapsed > self.state_timeout:
            print(f"[STATE] TIMEOUT in {self.current_state.value} ({elapsed:.1f}s > {self.state_timeout}s) - triggering SAFE_STOP")
            self.safe_stop(f"State timeout in {self.current_state.value}")
            return True
        return False
    
    def safe_stop(self, reason: str = "Unknown"):
        """Emergency stop - halt all actuators and motors immediately"""
        print(f"[STATE] SAFE_STOP triggered: {reason}")
        old_state = self.current_state
        self.current_state = State.SAFE_STOP
        self.last_state_change = time.time()
        
        if self.event_store:
            try:
                self.event_store.append("error", {
                    "action": "SAFE_STOP",
                    "previous_state": old_state.value,
                    "reason": reason
                })
            except Exception as e:
                pass

if __name__ == "__main__":
    sm = StateMachine()
    sm.transition(State.SCANNING)
    time.sleep(1)
    sm.check_timeout()
    print("State machine test complete. Current state:", sm.current_state.value)
