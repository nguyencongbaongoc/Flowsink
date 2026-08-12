"""Bedtime Service — schedules bedtime warnings and restricted mode.

Time is injected via a ``clock`` callable for testability.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from ..core.actions import ActionRequest, ActionType, EnableRestrictedModeRequest
from ..core.events import ActivityEvent, EventType
from ..core.policies import BedtimePolicy
from ..core.states import ActivityState
from ..engine.action_engine import ActionEngine
from ..engine.state_engine import StateEngine
from ..logging import get_logger

logger = get_logger("activity_engine.bedtime_service", component="BEDTIME", event="CHECK")

class BedtimeService:
    """Manages the bedtime flow independent of focus/classroom logic."""

    def __init__(
        self,
        state_engine: StateEngine,
        action_engine: ActionEngine,
        policy: BedtimePolicy,
        student_id: str,
        device_id: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._state_engine = state_engine
        self._action_engine = action_engine
        self._policy = policy
        self._student_id = student_id
        self._device_id = device_id
        self._clock = clock or (lambda: datetime.now(UTC))
        self._last_stage = "none"

    def startup_check(self) -> str:
        """Evaluate bedtime stage at startup. Returns current stage."""
        if not self._policy.enabled:
            return "none"
        stage = self._compute_stage()
        if stage != self._last_stage:
            self._last_stage = stage
        return stage

    def check(self) -> str:
        """Evaluate the bedtime stage for now and trigger actions if changed."""
        if not self._policy.enabled:
            return "none"

        stage = self._compute_stage()

        if stage != self._last_stage:
            logger.info(
                "student_id=%s previous=%s current=%s",
                self._student_id,
                self._last_stage,
                stage,
                event="STAGE_CHANGED",
                component="BEDTIME",
            )
            if stage == "level_1":
                self._issue_warning(
                    "Sắp đến giờ đi ngủ (15 phút). Vui lòng hoàn thành công việc và chuẩn bị nghỉ ngơi."
                )
            elif stage == "level_2":
                self._issue_warning(
                    "Còn 5 phút nữa đến giờ đi ngủ. Vui lòng lưu lại công việc."
                )
            elif stage == "level_3":
                self._enter_restricted_mode()
            elif stage == "none":
                self._leave_restricted_mode()
            self._last_stage = stage

        return stage

    @property
    def current_stage(self) -> str:
        return self._last_stage

    # ------------------------------------------------------------------
    def _compute_stage(self) -> str:
        now = self._clock()
        start = self._policy.start_time
        hour, minute = (int(part) for part in start.split(":"))
        start_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        minutes_before = (start_dt - now).total_seconds() / 60.0

        if minutes_before > self._policy.level_1_warning_minutes:
            return "none"
        if minutes_before > self._policy.level_2_warning_minutes:
            return "level_1"
        if minutes_before > 0:
            return "level_2"
        return "level_3"

    def _issue_warning(self, message: str) -> None:
        logger.info(
            "student_id=%s stage=%s",
            self._student_id,
            self._last_stage,
            event="WARNING",
            component="BEDTIME",
        )
        action = ActionRequest(
            action=ActionType.WARN,
            target="bedtime",
            student_id=self._student_id,
            policy_id="bedtime",
            reason="BEDTIME_WARNING",
            payload=type(
                "WarningRequest",
                (),
                {"student_id": self._student_id, "message": message, "policy_id": "bedtime", "reason": "BEDTIME_WARNING"},
            ),
        )
        # Warnings are routed through the action engine; in dry-run they are
        # recorded as NOT_EXECUTED rather than shown.
        asyncio_run = getattr(self._action_engine, "execute", None)
        if asyncio_run:
            import asyncio

            asyncio.get_event_loop().create_task(asyncio_run(action))
        self._state_engine.force_state(self._student_id, self._device_id, ActivityState.BEDTIME)

    def _enter_restricted_mode(self) -> None:
        logger.info(
            "student_id=%s mode=BEDTIME_RESTRICTED",
            self._student_id,
            event="RESTRICTED_MODE",
            component="BEDTIME",
        )
        action = ActionRequest(
            action=ActionType.ENABLE_RESTRICTED_MODE,
            target="device",
            student_id=self._student_id,
            policy_id="bedtime",
            reason="BEDTIME_MODE",
            payload=EnableRestrictedModeRequest(
                student_id=self._student_id,
                mode_name="BEDTIME_RESTRICTED",
                policy_id="bedtime",
                reason="BEDTIME_MODE",
            ),
        )
        asyncio_run = getattr(self._action_engine, "execute", None)
        if asyncio_run:
            import asyncio

            asyncio.get_event_loop().create_task(asyncio_run(action))
        self._state_engine.force_state(self._student_id, self._device_id, ActivityState.BEDTIME)

    def _leave_restricted_mode(self) -> None:
        logger.info(
            "student_id=%s",
            self._student_id,
            event="RESTRICTED_MODE_EXIT",
            component="BEDTIME",
        )
        self._state_engine.force_state(self._student_id, self._device_id, ActivityState.ALLOWED)
