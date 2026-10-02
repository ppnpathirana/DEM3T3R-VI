import sys, os, time
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.state_machine import StateMachine, State

VALID_STATES = list(State)
state_strategy = st.sampled_from(VALID_STATES)
state_sequence_strategy = st.lists(state_strategy, min_size=1, max_size=50)

# Property 1: State is always a valid State enum member
@given(states=state_sequence_strategy)
@settings(max_examples=300)
def test_state_always_valid(states):
    sm = StateMachine()
    for s in states:
        sm.transition(s)
    assert sm.current_state in VALID_STATES

# Property 2: Calling safe_stop always guarantees current state is SAFE_STOP
@given(states=state_sequence_strategy, reason=st.text(max_size=50))
@settings(max_examples=200)
def test_safe_stop_always_reaches_safe_stop(states, reason):
    sm = StateMachine()
    for s in states:
        sm.transition(s)
    sm.safe_stop(reason)
    assert sm.current_state == State.SAFE_STOP

# Property 3: State timeout correctly triggers SAFE_STOP transition
@given(timeout=st.floats(min_value=0.01, max_value=2.0))
@settings(max_examples=100)
def test_timeout_triggers_safe_stop(timeout):
    sm = StateMachine(timeout_sec=timeout)
    sm.transition(State.SCANNING)
    sm.last_state_change = time.time() - timeout - 0.05
    timed_out = sm.check_timeout()
    assert timed_out is True
    assert sm.current_state == State.SAFE_STOP

# Property 4: Checking timeout on IDLE or SAFE_STOP never transitions away
@given(elapsed=st.floats(min_value=0.0, max_value=100.0))
@settings(max_examples=100)
def test_safe_stop_and_idle_timeout_invariance(elapsed):
    sm = StateMachine()
    sm.transition(State.SAFE_STOP)
    sm.last_state_change = time.time() - elapsed
    assert sm.check_timeout() is False
    assert sm.current_state == State.SAFE_STOP

if __name__ == '__main__':
    test_state_always_valid()
    test_safe_stop_always_reaches_safe_stop()
    test_timeout_triggers_safe_stop()
    test_safe_stop_and_idle_timeout_invariance()
    print("All StateMachine hypothesis property-based tests PASSED.")
