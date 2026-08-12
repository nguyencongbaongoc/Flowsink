"""Screenshot trigger service.

Browser/process events that produce a WARNING (or worse) decision trigger an
async screenshot capture through the existing :mod:`platform.screen` abstraction.
This mirrors the intended flow:

    Browser Event -> Backend -> EventEngine -> PolicyEngine
    -> Screenshot Trigger -> ScreenProvider

The service is fault-isolated: capture failures are logged, never raised, and
screenshots are optional telemetry, not enforcement.
"""

from __future__ import annotations

from pathlib import Path

from ..core.decisions import PolicyDecision, PolicyOutcome
from ..core.events import ActivityEvent
from ..platform.screen import default_screenshot_dir, get_screen_provider
from ..logging import get_logger

logger = get_logger("activity_engine.screenshot", component="SCREENSHOT", event="CAPTURE")

# Outcomes that justify a screenshot as corroborating evidence.
_TRIGGER_OUTCOMES = {
    PolicyOutcome.WARNING,
    PolicyOutcome.BLOCKED,
    PolicyOutcome.RESTRICT,
    PolicyOutcome.OFF_TASK,
}


class ScreenshotService:
    """Captures screen snapshots when policy decisions warrant it."""

    def __init__(
        self,
        directory: Path | None = None,
        provider=None,
        min_interval_seconds: float = 10.0,
    ) -> None:
        """Construct the service.

        Args:
            directory: Screenshot output directory. Defaults to
                ``default_screenshot_dir()``.
            provider: A :class:`ScreenProvider` instance. Defaults to the
                cached provider from :func:`get_screen_provider`.
            min_interval_seconds: Minimum seconds between captures for the
                same device/domain (anti-spam / anti-burst).
        """
        self._directory = directory or default_screenshot_dir()
        self._provider = provider or get_screen_provider()
        self._min_interval_seconds = min_interval_seconds
        self._last_capture: dict[str, float] = {}
        import time

        self._time = time

    def should_capture(self, decision: PolicyDecision, event: ActivityEvent) -> bool:
        """Return True when a screenshot should be attempted for this decision.

        Only screenshots on WARNING+ outcomes and never more often than
        ``min_interval_seconds`` per domain/device pair.
        """
        if decision.outcome not in _TRIGGER_OUTCOMES:
            logger.debug(
                "event_id=%s outcome=%s reason=policy_not_triggered",
                event.event_id,
                decision.outcome.value,
                event="SKIP",
                component="SCREENSHOT",
            )
            return False
        domain = decision.domain or event.browser.domain or "unknown"
        key = f"{event.device_id}:{domain}"
        now = self._time.monotonic()
        last = self._last_capture.get(key, 0.0)
        if now - last < self._min_interval_seconds:
            logger.debug(
                "event_id=%s domain=%s reason=cooldown cooldown=%.1fs",
                event.event_id,
                domain,
                self._min_interval_seconds,
                event="SKIP",
                component="SCREENSHOT",
            )
            return False
        self._last_capture[key] = now
        logger.info(
            "event_id=%s domain=%s reason=policy_violation",
            event.event_id,
            domain,
            event="TRIGGER",
            component="SCREENSHOT",
        )
        return True

    def capture(self, decision: PolicyDecision, event: ActivityEvent) -> Path | None:
        """Capture the screen into the configured directory.

        Returns the saved file path, or ``None`` when capture is unavailable
        (mock provider / missing dependency).
        """
        logger.info(
            "event_id=%s outcome=%s stage=capture",
            event.event_id,
            decision.outcome.value,
            event="DECISION",
            component="SCREENSHOT",
        )
        try:
            path = self._provider.save_screenshot(
                directory=self._directory,
                session_id=event.session_id,
                prefix="auto_capture",
            )
            if path is not None:
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                logger.info(
                    "event_id=%s path=%s size=%dKB outcome=%s",
                    event.event_id,
                    path,
                    size // 1024,
                    decision.outcome.value,
                    event="SAVE",
                    component="SCREENSHOT",
                )
            return path
        except Exception as exc:  # noqa: BLE001 - capture must never crash engine
            logger.error(
                "event_id=%s stage=capture error_type=%s message=%s",
                event.event_id,
                exc.__class__.__name__,
                exc,
                event="ERROR",
                component="SCREENSHOT",
                exc_info=True,
            )
            return None
