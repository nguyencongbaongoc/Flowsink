"""Public facade — the single entry point for the Activity Engine.

The facade wires configuration, policy, engines, persistence and adapters
into a coherent pipeline:

    raw adapter events -> EventEngine -> PolicyEngine -> StateEngine
    -> EscalationEngine -> ActionEngine
"""

from __future__ import annotations

from typing import Any

from ..config.loader import load_dev_config, resolve_device_id
from ..config.models import Config, EnforcementMode
from ..core.events import ActivityEvent
from ..policy.loader import load_default_policy
from ..core.policies import PolicyDocument
from ..core.states import StateSnapshot
from ..domain.violations import ViolationRecord
from ..persistence.repository import InMemoryActivityRepository
from .action_engine import ActionEngine
from .escalation_engine import EscalationEngine
from .event_engine import EventEngine
from .policy_engine import PolicyEngine
from .state_engine import StateEngine
from ..services.screenshot_service import ScreenshotService
from ..logging import get_logger, set_log_context

_logger = get_logger("activity_engine.facade", component="SYSTEM", event="SESSION")

class ActivityEngine:
    """Configured and ready-to-run Activity Engine."""

    def __init__(
        self,
        config: Config | None = None,
        policy: PolicyDocument | None = None,
        executor: object | None = None,
        event_engine: EventEngine | None = None,
        policy_engine: PolicyEngine | None = None,
        state_engine: StateEngine | None = None,
        action_engine: ActionEngine | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the engine.

        Provide custom engines/adapters for full control; otherwise sensible
        defaults are created from ``config``.
        """
        self._config = config or load_dev_config()
        self._student_id = kwargs.pop("student_id", None)
        self._device_id = kwargs.pop("device_id", None) or resolve_device_id(self._config)

        try:
            self._policy = policy or load_default_policy()
        except Exception as exc:  # noqa: BLE001
            _logger.warning("default_policy_load_failed error=%s falling_back=empty", exc)
            self._policy = PolicyDocument()

        self._executor = executor or self._default_executor()
        mode = self._config.runtime.mode if hasattr(self._config, "runtime") else EnforcementMode.DRY_RUN

        # Engine wiring
        self._event_engine = event_engine or EventEngine(
            device_id=self._device_id,
            student_id=self._student_id,
        )
        self._state_engine = state_engine or StateEngine(
            device_id=self._device_id,
            student_id=self._student_id,
        )
        self._policy_engine = policy_engine or PolicyEngine(
            policy=self._policy,
            device_id=self._device_id,
            student_id=self._student_id,
        )
        self._action_engine = action_engine or ActionEngine(
            executor=self._executor,
            mode=mode,
        )
        self._escalation_engine = EscalationEngine(default_policy_id=self._policy.version)

        self._repository = InMemoryActivityRepository()
        self._screenshots = ScreenshotService()

        # Subscribe pipeline: raw/processed events flow to policy engine.
        async def _route(event: ActivityEvent) -> None:
            try:
                # Correlate logs with this event
                set_log_context(event_id=event.event_id, device_id=self._device_id)

                # Stamp the active session id so events, violations, snapshots
                # and future screenshots are all linked to the same session.
                session = self._state_engine.get_session(
                    event.student_id or self._student_id or "unknown-student",
                    self._device_id,
                )
                if session is not None and event.session_id is None:
                    event = event.model_copy(update={"session_id": session.session_id})
                    set_log_context(session_id=session.session_id)

                decision = self._policy_engine.evaluate(event)
                snapshot = self._state_engine.apply_decision(decision)

                # Screenshot trigger: WARNING+ outcomes capture optional
                # evidence through the platform screen provider. Fault-isolated;
                # never crashes the pipeline.
                if self._screenshots.should_capture(decision, event):
                    _logger.info(
                        "event_id=%s reason=policy_violation",
                        event.event_id,
                        event="TRIGGER",
                        component="SCREENSHOT",
                    )
                    self._screenshots.capture(decision, event)
                else:
                    _logger.debug(
                        "event_id=%s reason=policy_not_triggered",
                        event.event_id,
                        event="SKIP",
                        component="SCREENSHOT",
                    )

                _logger.debug(
                    "event_id=%s state=%s",
                    event.event_id,
                    snapshot.state.value if snapshot else "UNKNOWN",
                    event="STORED",
                    component="EVENT",
                )
                await self._repository.store_event(event)
                await self._repository.store_state(snapshot)
                if decision.action_types:
                    for action in self._escalation_engine.plan(decision):
                        _logger.info(
                            "action=%s event_id=%s",
                            action.action.value,
                            event.event_id,
                            event="REQUESTED",
                            component="ACTION",
                        )
                        result = await self._action_engine.execute(action)
                        if result.status.value != "SUCCESS":
                            _logger.warning(
                                "action=%s status=%s code=%s",
                                action.action.value,
                                result.status.value,
                                result.error_code,
                                event="FAILED",
                                component="ACTION",
                            )
                        else:
                            _logger.info(
                                "action=%s status=%s",
                                action.action.value,
                                result.status.value,
                                event="COMPLETED",
                                component="ACTION",
                            )
            except Exception as exc:  # noqa: BLE001 - fault isolation
                _logger.error(
                    "operation=pipeline error_type=%s message=%s",
                    exc.__class__.__name__,
                    exc,
                    event="ERROR",
                    component="SYSTEM",
                    exc_info=True,
                )

        self._event_engine.subscribe(_route)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start_session(self) -> str:
        """Begin a monitoring session. Returns the session id."""
        session = self._state_engine.start_session(
            self._student_id or "unknown-student",
            self._device_id,
        )
        set_log_context(session_id=session.session_id, device_id=self._device_id)
        _logger.info(
            "session_id=%s device_id=%s",
            session.session_id,
            self._device_id,
            event="START",
            component="SESSION",
        )
        return session.session_id

    def end_session(self) -> None:
        """End the active monitoring session."""
        ended = self._state_engine.end_session(self._student_id or "unknown-student", self._device_id)
        if ended is not None:
            _logger.info(
                "session_id=%s device_id=%s started=%s ended=%s",
                ended.session_id,
                ended.device_id,
                ended.started_at.isoformat(),
                (ended.ended_at or ended.started_at).isoformat(),
                event="END",
                component="SESSION",
            )
        set_log_context(session_id=None)

    # ------------------------------------------------------------------
    # Event intake
    # ------------------------------------------------------------------
    async def feed_raw(self, raw: dict[str, Any]) -> ActivityEvent | None:
        """Feed a raw adapter event into the pipeline."""
        return await self._event_engine.process_raw(raw)

    async def feed(self, event: ActivityEvent) -> ActivityEvent:
        """Feed an already-normalized event into the pipeline."""
        return await self._event_engine.process(event)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def current_state(self, student_id: str | None = None) -> StateSnapshot | None:
        return self._state_engine.get_snapshot(
            student_id or self._student_id or "unknown-student",
            self._device_id,
        )

    async def recent_events(self, limit: int = 50) -> list[ActivityEvent]:
        return await self._repository.get_events(limit=limit)

    async def violations(self, student_id: str | None = None, limit: int = 50) -> list[ViolationRecord]:
        # Canonical violation source is the PolicyEngine; the repository's
        # store_violation() is intentionally unused to avoid dual sources.
        return self._policy_engine.violations_for(
            student_id or self._student_id or "unknown-student",
            limit=limit,
        )

    def metrics(self) -> dict[str, Any]:
        """Aggregate engine metrics."""
        return {
            "event_engine": dict(self._event_engine.metrics),
            "policy_engine": dict(self._policy_engine.metrics),
            "action_engine": dict(self._action_engine.metrics),
        }

    @property
    def policy(self) -> PolicyDocument:
        return self._policy

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_executor(self) -> object:
        """Pick the default action executor for the current platform."""
        from ..adapters.mock.action_executor import MockActionExecutor
        return MockActionExecutor()