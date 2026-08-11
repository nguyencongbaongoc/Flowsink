"""Engine error hierarchy.

All errors raised by the engine derive from :class:`ActivityEngineError` so
callers can catch a single base type. Errors are always recoverable: a failing
monitor or action executor never crashes the whole agent.
"""

from __future__ import annotations

class ActivityEngineError(Exception):
    """Base class for all engine errors."""


class ConfigurationError(ActivityEngineError):
    """Raised when configuration is invalid or missing. The engine fails fast."""


class EventValidationError(ActivityEngineError):
    """Raised when an incoming raw event cannot be normalized."""


class PolicyEvaluationError(ActivityEngineError):
    """Raised when a policy cannot be evaluated."""


class ActionExecutionError(ActivityEngineError):
    """Raised when an enforcement action fails."""

    def __init__(self, action_id: str, error_code: str, message: str) -> None:
        super().__init__(f"Action {action_id} failed: {error_code} — {message}")
        self.action_id = action_id
        self.error_code = error_code
        self.message = message


class MonitorError(ActivityEngineError):
    """Raised when a monitor adapter fails to start or stops unexpectedly."""