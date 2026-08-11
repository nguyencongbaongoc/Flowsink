"""Policy Engine — coordinates policy evaluation, escalation and violation tracking."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ..core.actions import ActionType
from ..core.decisions import PolicyDecision, PolicyOutcome
from ..core.events import ActivityEvent
from ..core.policies import PolicyDocument
from ..domain.violations import ViolationRecord
from ..core.states import ActivityState
from ..policy.evaluator import PolicyEvaluator


class PolicyEngine:
    """Combines the evaluator with violation counting and escalation."""

    def __init__(
        self,
        policy: PolicyDocument,
        device_id: str = "device-001",
        student_id: str | None = None,
    ) -> None:
        self._evaluator = PolicyEvaluator(policy)
        self._device_id = device_id
        self._student_id = student_id
        self._violation_counters: dict[tuple[str, str], int] = {}
        self._activity_started_at: dict[tuple[str, str], datetime] = {}
        self._violations: list[ViolationRecord] = []
        self.metrics = {
            "policy_violations": 0,
            "warnings": 0,
        }

    @property
    def policy(self) -> PolicyDocument:
        return self._evaluator.policy

    def set_policy(self, policy: PolicyDocument) -> None:
        self._evaluator.set_policy(policy)

    def evaluate(self, event: ActivityEvent) -> PolicyDecision:
        """Evaluate an event; escalate based on tracked violations."""
        decision = self._evaluator.evaluate(event)
        key = (event.student_id or self._student_id or "unknown", event.device_id)

        if decision.outcome == PolicyOutcome.WARNING:
            self.metrics["policy_violations"] += 1
            self.metrics["warnings"] += 1
            self._violation_counters[key] = self._violation_counters.get(key, 0) + 1
            if key not in self._activity_started_at:
                self._activity_started_at[key] = datetime.now(UTC)
            started = self._activity_started_at[key]
            duration = (datetime.now(UTC) - started).total_seconds()
            decision = self._evaluator.escalate(
                decision,
                violation_count=self._violation_counters[key],
                duration_seconds=duration,
            )
            self._record_violation(event, decision)
        else:
            if key in self._activity_started_at:
                self._activity_started_at.pop(key)

        if decision.outcome in (PolicyOutcome.FOCUS, PolicyOutcome.ALLOWED):
            self._violation_counters[key] = 0

        return decision

    def reset_violations(self, student_id: str | None = None, device_id: str | None = None) -> None:
        """Reset violation counters, e.g. after restricted mode ended."""
        key = (student_id or self._student_id or "unknown", device_id or self._device_id)
        self._violation_counters[key] = 0
        self._activity_started_at.pop(key, None)

    def violations_for(self, student_id: str, limit: int = 100) -> list[ViolationRecord]:
        return [v for v in reversed(self._violations) if v.student_id == student_id][:limit]

    def _record_violation(self, event: ActivityEvent, decision: PolicyDecision) -> None:
        key = (event.student_id or self._student_id or "unknown", event.device_id)
        before = self._state_from_outcome(decision.outcome)
        record = ViolationRecord(
            violation_id=str(uuid.uuid4()),
            student_id=key[0],
            device_id=event.device_id,
            session_id=event.session_id,
            state_before=before,
            state_after=before,
            domain=decision.domain,
            application=decision.application,
            policy_id=decision.policy_id,
            level=decision.level.value if decision.level else "level_1",
            action_types=decision.action_types,
            reason=decision.reason,
            risk_score=decision.risk_score,
        )
        self._violations.append(record)
        if len(self._violations) > 1000:
            self._violations = self._violations[-1000:]

    @staticmethod
    def _state_from_outcome(outcome: PolicyOutcome) -> ActivityState:
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