"""Core logging configuration for Flowsink Activity Engine.

Format:
    [TIMESTAMP] [LEVEL] [COMPONENT] [EVENT] message

Supports:
- TRACE custom level
- Context variables for correlation (event_id, session_id, device_id)
- File rotation (10MB, 5 files)
- Console handler with --log-level and --quiet support
- Secret sanitization
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .sanitize import sanitize_message, sanitize_url

# ---------------------------------------------------------------------------
# TRACE level
# ---------------------------------------------------------------------------
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


def _trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    """Log with TRACE severity."""
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


logging.Logger.trace = _trace  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Context variables for correlation
# ---------------------------------------------------------------------------
_event_id_var: ContextVar[str | None] = ContextVar("event_id", default=None)
_session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
_device_id_var: ContextVar[str | None] = ContextVar("device_id", default=None)


def set_log_context(
    *,
    event_id: str | None = None,
    session_id: str | None = None,
    device_id: str | None = None,
) -> None:
    """Set the correlation context for the current async/sync context."""
    if event_id is not None:
        _event_id_var.set(event_id)
    if session_id is not None:
        _session_id_var.set(session_id)
    if device_id is not None:
        _device_id_var.set(device_id)


def get_log_context() -> dict[str, str]:
    """Return the current correlation context as a dict."""
    ctx: dict[str, str] = {}
    if _event_id_var.get() is not None:
        ctx["event_id"] = _event_id_var.get()  # type: ignore[assignment]
    if _session_id_var.get() is not None:
        ctx["session_id"] = _session_id_var.get()  # type: ignore[assignment]
    if _device_id_var.get() is not None:
        ctx["device_id"] = _device_id_var.get()  # type: ignore[assignment]
    return ctx


def reset_log_context() -> None:
    """Clear all correlation context variables."""
    _event_id_var.set(None)
    _session_id_var.set(None)
    _device_id_var.set(None)


# ---------------------------------------------------------------------------
# Default log directory
# ---------------------------------------------------------------------------
def _default_log_dir() -> Path:
    """Return the platform-appropriate log directory.

    Windows: %LOCALAPPDATA%/Flowsink/logs
    macOS/Linux: ~/Flowsink/logs
    """
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Flowsink" / "logs"
    return Path.home() / "Flowsink" / "logs"


# ---------------------------------------------------------------------------
# Structured formatter
# ---------------------------------------------------------------------------
class StructuredFormatter(logging.Formatter):
    """Produces ``[TIMESTAMP] [LEVEL] [COMPONENT] [EVENT] message`` lines."""

    def __init__(self, *, use_color: bool = False) -> None:
        super().__init__()
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        component = getattr(record, "component", "SYSTEM")
        event = getattr(record, "event", "LOG")
        level = record.levelname

        # Build `key=value` suffix from extra fields
        extra_parts: list[str] = []
        for key, value in record.__dict__.items():
            if key in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName", "asctime", "component", "event",
            }:
                continue
            extra_parts.append(f"{key}={_safe_value(value)}")

        # Add correlation context
        ctx = get_log_context()
        for key in ("event_id", "session_id", "device_id"):
            if key in ctx:
                extra_parts.append(f"{key}={ctx[key]}")

        message = sanitize_message(record.getMessage())

        # Render the line
        line = f"[{timestamp}] [{level}] [{component}] [{event}] {message}"
        if extra_parts:
            line += " " + " ".join(extra_parts)

        # Add exception info
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            line += f"\n  exception={exc_text}"

        if self._use_color:
            line = _colorize(level, line)

        return line


def _safe_value(value: Any) -> str:
    """Serialize values safely for logs."""
    if isinstance(value, str):
        return value.replace(" ", "_")
    try:
        import json

        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _colorize(level: str, line: str) -> str:
    """Apply ANSI colors for console output."""
    colors = {
        "TRACE": "\033[90m",  # bright black
        "DEBUG": "\033[36m",  # cyan
        "INFO": "\033[32m",  # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",  # red
        "CRITICAL": "\033[1;31m",  # bold red
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    return f"{color}{line}{reset}"


# ---------------------------------------------------------------------------
# Handler factory
# ---------------------------------------------------------------------------
def _console_handler(level: int = logging.INFO, quiet: bool = False) -> logging.Handler:
    """Create a console handler with the structured formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter(use_color=True))
    handler.setLevel(logging.WARNING if quiet else level)
    return handler


def _file_handler(path: Path, level: int) -> logging.Handler:
    """Create a rotating file handler (10 MB, keep 5 files)."""
    handler = RotatingFileHandler(
        path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(StructuredFormatter(use_color=False))
    handler.setLevel(level)
    return handler


# ---------------------------------------------------------------------------
# Public configuration API
# ---------------------------------------------------------------------------
_LOG_CONFIGURED = False
_LOG_CONFIG_LOCK = threading.Lock()


def setup_logging(
    *,
    level: str | int = "INFO",
    log_dir: Path | None = None,
    quiet: bool = False,
    console: bool = True,
    file_logging: bool = True,
) -> None:
    """Configure the root activity_engine logger once.

    Args:
        level: Minimum log level. Accepts 'TRACE', 'DEBUG', 'INFO', 'WARNING',
            'ERROR', 'CRITICAL' or a numeric value.
        log_dir: Directory for log files. Defaults to platform-specific path.
        quiet: When True, console only shows WARNING+.
        console: Whether to attach a console handler.
        file_logging: Whether to attach rotating file handlers.
    """
    global _LOG_CONFIGURED
    with _LOG_CONFIG_LOCK:
        if _LOG_CONFIGURED:
            return
        _LOG_CONFIGURED = True

    numeric_level = _normalize_level(level)

    root = logging.getLogger("activity_engine")
    root.setLevel(TRACE if numeric_level <= TRACE else numeric_level)
    root.handlers.clear()
    root.propagate = False

    if console:
        root.addHandler(_console_handler(numeric_level, quiet=quiet))

    if file_logging:
        directory = log_dir or _default_log_dir()
        directory.mkdir(parents=True, exist_ok=True)

        root.addHandler(_file_handler(directory / "flowsink.log", logging.INFO))
        root.addHandler(_file_handler(directory / "flowsink-error.log", logging.ERROR))
        root.addHandler(_file_handler(directory / "flowsink-debug.log", TRACE))


def configure_logging(**kwargs: Any) -> None:
    """Alias for :func:`setup_logging`."""
    setup_logging(**kwargs)


def _normalize_level(level: str | int) -> int:
    """Convert a string level name to a numeric level, with TRACE support."""
    if isinstance(level, int):
        return level
    upper = level.upper()
    if upper == "TRACE":
        return TRACE
    return getattr(logging, upper, logging.INFO)


# Marker to prevent double-wrapping the same logger instance.
_BOUND_LOGGER_MARKER = "_flowbound"

def get_logger(
    name: str = "activity_engine",
    *,
    component: str | None = None,
    event: str | None = None,
) -> logging.Logger:
    """Return a configured logger with optional default component/event.

    The returned logger transparently converts kwargs such as
    ``event=``, ``component=``, ``session_id=``, and any other
    key=value pairs into LogRecord attributes rendered by
    :class:`StructuredFormatter`.

    Usage::

        logger = get_logger("activity_engine.screen", component="SCREEN")
        logger.info("Monitor detected", event="DETECTED", monitor=1, width=1920)
    """
    logger = logging.getLogger(name)

    # Always wrap — the kwargs-to-extra translation must work even when
    # no defaults are supplied (e.g. logger.info("x", event="Y")).
    if getattr(logger, _BOUND_LOGGER_MARKER, False):
        return logger

    original_class = logger.__class__

    def _apply_defaults(kwargs: dict[str, Any]) -> dict[str, Any]:
        if component is not None:
            kwargs.setdefault("component", component)
        if event is not None:
            kwargs.setdefault("event", event)
        return kwargs

    def _wrap(method_name: str):
        _orig = getattr(original_class, method_name)

        def _wrapped(self, msg, *args, **kwargs):
            kwargs = _apply_defaults(kwargs)
            # Extract Python-recognized kwargs before folding the rest into extra.
            exc_info = kwargs.pop("exc_info", None)
            stack_info = kwargs.pop("stack_info", False)
            extra = kwargs.pop("extra", None) or {}
            # Remaining kwargs (event, component, monitor, width, ...) become
            # LogRecord attributes that StructuredFormatter can render.
            for k, v in kwargs.items():
                extra.setdefault(k, v)
            call_kwargs: dict[str, Any] = {"extra": extra}
            if exc_info is not None:
                call_kwargs["exc_info"] = exc_info
            if stack_info:
                call_kwargs["stack_info"] = stack_info
            return _orig(self, msg, *args, **call_kwargs)

        return _wrapped

    class _BoundLogger(original_class):  # type: ignore[misc, valid-type]
        debug = _wrap("debug")
        info = _wrap("info")
        warning = _wrap("warning")
        error = _wrap("error")
        exception = _wrap("exception")
        critical = _wrap("critical")
        trace = _wrap("trace")  # type: ignore[attr-defined]

    setattr(logger, _BOUND_LOGGER_MARKER, True)
    logger.__class__ = _BoundLogger  # type: ignore[assignment]

    return logger


def log_error(
    logger: logging.Logger,
    operation: str,
    error: Exception,
    *,
    component: str = "SYSTEM",
    event: str = "ERROR",
    **context: Any,
) -> None:
    """Log an exception with structured context and traceback."""
    logger.error(
        "operation=%s error_type=%s message=%s",
        operation,
        error.__class__.__name__,
        error,
        component=component,
        event=event,
        exc_info=True,
        **context,
    )