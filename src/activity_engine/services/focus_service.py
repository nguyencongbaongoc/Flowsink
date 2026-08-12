"""Focus Service — manages focus mode and classroom enforcement."""

from __future__ import annotations

from ..core.actions import ActionType
from ..core.events import ActivityEvent
from ..engine.action_engine import ActionEngine
from ..engine.escalation_engine import EscalationEngine
from ..engine.event_engine import EventEngine
from ..engine.policy_engine import PolicyEngine
from ..engine.state_engine import StateEngine
from ..logging import get_logger

logger = get_logger("activity_engine.focus_service", component="FLOW", event="PIPELINE")

class FocusService:
    """Orchestrates focus-mode enforcement for a single student."""

    def __init__(
        self,
        event_engine: EventEngine,
        policy_engine: PolicyEngine,
        state_engine: StateEngine,
        action_engine: ActionEngine,
        escalation_engine: EscalationEngine,
        student_id: str,
        device_id: str,
    ) -> None:
        self._event_engine = event_engine
        self._policy_engine = policy_engine
        self._state_engine = state_engine
        self._action_engine = action_engine
        self._escalation_engine = escalation_engine
        self._student_id = student_id
        self._device_id = device_id
        self._restricted_mode_active = False

    def begin(self) -> None:
        """Start a focus session."""
        logger.info(
            "student_id=%s device_id=%s",
            self._student_id,
            self._device_id,
            event="SESSION_START",
            component="SESSION",
        )
        self._state_engine.start_session(self._student_id, self._device_id)

    def end(self) -> None:
        """End a focus session."""
        logger.info(
            "student_id=%s device_id=%s",
            self._student_id,
            self._device_id,
            event="SESSION_END",
            component="SESSION",
        )
        self._state_engine.end_session(self._student_id, self._device_id)

    async def handle_event(self, event: ActivityEvent) -> None:
        """Process one canonical event through policy -> state -> action pipeline."""
        session = self._state_engine.get_session(self._student_id, self._device_id)
        if event.session_id is None and session is not None:
            event = event.model_copy(update={"session_id": session.session_id})

        logger.debug(
            "event_id=%s type=%s session_id=%s",
            event.event_id,
            event.type.value,
            event.session_id or "none",
            event="EVENT_IN",
            component="FLOW",
        )

        decision = self._policy_engine.evaluate(event)
        self._state_engine.apply_decision(decision)
        logger.info(
            "event_id=%s decision=%s state=%s",
            event.event_id,
            decision.outcome.value,
            self.state,
            event="POLICY",
            component="FLOW",
        )

        actions = self._escalation_engine.plan(decision)
        for action in actions:
            result = await self._action_engine.execute(action)
            logger.info(
                "event_id=%s action=%s status=%s",
                event.event_id,
                result.action.value,
                result.status.value,
                event="ACTION",
                component="FLOW",
            )
            if result.status.value == "SUCCESS":
                if result.action == ActionType.ENABLE_RESTRICTED_MODE:
                    self._restricted_mode_active = True
                elif result.action == ActionType.DISABLE_RESTRICTED_MODE:
                    self._restricted_mode_active = False

    @property
    def state(self) -> str:
        snapshot = self._state_engine.get_snapshot(self._student_id, self._device_id)
        return snapshot.state.value if snapshot else "UNKNOWN"
