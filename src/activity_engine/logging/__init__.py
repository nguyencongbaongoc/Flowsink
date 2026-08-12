"""Centralized structured logging for Flowsink Activity Engine.

Provides:
- Consistent structured log format: [TIMESTAMP] [LEVEL] [COMPONENT] [EVENT] message
- Correlation IDs (event_id, session_id, device_id) via contextvars
- Secret sanitization (passwords, tokens, API keys, Authorization headers)
- File logging with rotation (logs/flowsink.log, flowsink-error.log, flowsink-debug.log)
- Console mode support with --log-level and --quiet
- TRACE custom level
"""

from __future__ import annotations

from .logger import (
    TRACE,
    configure_logging,
    get_log_context,
    get_logger,
    log_error,
    reset_log_context,
    set_log_context,
    setup_logging,
)
from .sanitize import sanitize_dict, sanitize_message, sanitize_url

__all__ = [
    "TRACE",
    "configure_logging",
    "get_log_context",
    "get_logger",
    "log_error",
    "reset_log_context",
    "set_log_context",
    "setup_logging",
    "sanitize_dict",
    "sanitize_message",
    "sanitize_url",
]