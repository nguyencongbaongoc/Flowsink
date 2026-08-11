"""State Engine — maintains the explicit state machine per student."""

from __future__ import annotations

from datetime import UTC, datetime

from ..core.decisions import PolicyDecision, PolicyOutcome
from ..core.states import ActivityState, ActivityStateMachine, StateSnapshot
from ..domain.session import MonitoringSession

class StateEngine:
    """Owns one :class:`ActivityStateMachine` per student/device pair."""

    def __init__(self, device_id: str, student_id: str | None = None) -> None:
        self._device_id = device_id
        self._student_id = student_id or "unknown-student"
        self._machines: dict[tuple[str, str], ActivityStateMachine] = {}
        self._snapshots: dict[tuple[str, str], StateSnapshot] = {}
        self._sessions: dict[tuple[str, str], MonitoringSession] = {}

    def _key(self, student_id: str, device_id: str) -> tuple[str, str]:
        return (student_id or self._student_id, device_id or self._device_id)

    def _machine(self, student_id: str, device_id: str) -> ActivityStateMachine:
        key = self._key(student_id, device_id)
        if key not in self._machines:
            self._machines[key] = ActivityStateMachine()
        return self._machines[key]

    def start_session(self, student_id: str, device_id: str) -> MonitoringSession:
        key = self._key(student_id, device_id)
        session = MonitoringSession(student_id=key[0], device_id=key[1])
        self._sessions[key] = session
        return session

    def end_session(self, student_id: str, device_id: str) -> MonitoringSession | None:
        key = self._key(student_id, device_id)
        session = self._sessions.get(key)
        if session is not None:
            ended = session.end()
            self._sessions[key] = ended
            self._machine(*key).reset()
            return ended
        return None

    def get_session(self, student_id: str, device_id: str) -> MonitoringSession | None:
        return self._sessions.get(self._key(student_id, device_id))

    def get_snapshot(self, student_id: str, device_id: str) -> StateSnapshot | None:
        return self._snapshots.get(self._key(student_id, device_id))

    def apply_decision(self, decision: PolicyDecision) -> StateSnapshot:
        """Transition the state machine from a policy decision and return a snapshot."""
        student_id = decision.student_id or self._student_id
        device_id = self._device_id
        machine = self._machine(student_id, device_id)

        target = self._map_outcome(decision.outcome)
        try:
            machine.transition(target)
        except Exception:
            # Invalid transitions are normalized to nearest valid state.
            machine.reset()
            machine.transition(target)

        now = datetime.now(UTC)
        previous = self._snapshots.get(self._key(student_id, device_id))
        started_at = previous.started_at if previous and previous.state == target else now

        snapshot = StateSnapshot(
            student_id=student_id,
            device_id=device_id,
            state=target,
            application=decision.application,
            domain=decision.domain,
            started_at=started_at,
            duration_seconds=(now - started_at).total_seconds(),
            risk_score=decision.risk_score,
            session_id=self.get_session(student_id, device_id).session_id
            if self.get_session(student_id, device_id)
            else None,
            updated_at=now,
        )
        self._snapshots[self._key(student_id, device_id)] = snapshot
        return snapshot

    def force_state(self, student_id: str, device_id: str, state: ActivityState) -> StateSnapshot:
        """Force an explicit state (used by BedtimeService / FocusService)."""
        machine = self._machine(student_id, device_id)
        machine.reset()
        machine.transition(state)
        now = datetime.now(UTC)
        snapshot = StateSnapshot(
            student_id=student_id,
            device_id=device_id,
            state=state,
            started_at=now,
            duration_seconds=0.0,
            risk_score=1.0 if state in (ActivityState.RESTRICTED, ActivityState.BEDTIME) else 0.0,
            session_id=self.get_session(student_id, device_id).session_id
            if self.get_session(student_id, device_id)
            else None,
            updated_at=now,
        )
        self._snapshots[self._key(student_id, device_id)] = snapshot
        return snapshot

    @staticmethod
    def _map_outcome(outcome: PolicyOutcome) -> ActivityState:
        return {
            PolicyOutcome.FOCUS: ActivityState.FOCUS,
            PolicyOutcome.ALLOWED: ActivityState.ALLOWED,
            PolicyOutcome.WARNING: ActivityState.WARNING,
            PolicyOutcome.OFF_TASK: ActivityState.OFF_TASK,
            PolicyOutcome.BLOCKED: ActivityState.BLOCKED,
            PolicyOutcome.RESTRICT: ActivityState.RESTRICTED,
            PolicyOutcome.BEDTIME: ActivityState.BEDTIME,
            PolicyOutcome.POTENTIAL_ACTIVITY: ActivityState.ALLOWED,
            PolicyOutcome.IGNORED: ActivityState.UNKNOWN,
        }[outcome]