"""Unit tests for the activity state machine."""

from __future__ import annotations

import pytest

from activity_engine.core.states import (
    ActivityState,
    ActivityStateMachine,
    InvalidStateTransition,
)

class TestStateMachine:
    def test_initial_state_is_unknown(self) -> None:
        machine = ActivityStateMachine()
        assert machine.state == ActivityState.UNKNOWN

    def test_allowed_transition_from_unknown(self) -> None:
        machine = ActivityStateMachine()
        assert machine.transition(ActivityState.FOCUS) == ActivityState.FOCUS

    def test_same_state_is_noop(self) -> None:
        machine = ActivityStateMachine()
        machine.transition(ActivityState.ALLOWED)
        assert machine.state == ActivityState.ALLOWED
        # Same-state transition returns without error
        assert machine.transition(ActivityState.ALLOWED) == ActivityState.ALLOWED

    def test_invalid_transition_raises(self) -> None:
        machine = ActivityStateMachine()
        machine.transition(ActivityState.RESTRICTED)
        with pytest.raises(InvalidStateTransition):
            machine.transition(ActivityState.UNKNOWN)

    def test_valid_recovery_from_restricted(self) -> None:
        machine = ActivityStateMachine()
        machine.transition(ActivityState.RESTRICTED)
        assert machine.transition(ActivityState.ALLOWED) == ActivityState.ALLOWED

    def test_can_transition_check(self) -> None:
        machine = ActivityStateMachine(ActivityState.ALLOWED)
        assert machine.can_transition(ActivityState.BLOCKED)
        assert not machine.can_transition(ActivityState.UNKNOWN)  # illegal backwards jump

        machine.transition(ActivityState.BLOCKED)
        assert machine.can_transition(ActivityState.RESTRICTED)
        assert not machine.can_transition(ActivityState.UNKNOWN)  # forbidden from BLOCKED

    def test_reset(self) -> None:
        machine = ActivityStateMachine(ActivityState.BLOCKED)
        assert machine.state == ActivityState.BLOCKED
        machine.reset()
        assert machine.state == ActivityState.UNKNOWN

    @pytest.mark.parametrize(
        "start,target",
        [
            (ActivityState.UNKNOWN, ActivityState.ALLOWED),
            (ActivityState.ALLOWED, ActivityState.FOCUS),
            (ActivityState.FOCUS, ActivityState.WARNING),
            (ActivityState.WARNING, ActivityState.OFF_TASK),
            (ActivityState.OFF_TASK, ActivityState.BLOCKED),
            (ActivityState.BLOCKED, ActivityState.RESTRICTED),
            (ActivityState.RESTRICTED, ActivityState.ALLOWED),
            (ActivityState.RESTRICTED, ActivityState.BEDTIME),
            (ActivityState.BEDTIME, ActivityState.ALLOWED),
        ],
    )
    def test_all_valid_paths(self, start: ActivityState, target: ActivityState) -> None:
        machine = ActivityStateMachine(start)
        assert machine.transition(target) == target