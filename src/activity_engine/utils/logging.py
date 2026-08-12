"""Structured logging helpers (backward-compatible delegate).

This module now re-exports from :mod:`activity_engine.logging` and keeps the
old ``create_logger`` API for existing importers.

Never log passwords, cookies, tokens, full private content, or unnecessary
browsing payloads.
"""

from __future__ import annotations

import sys
from typing import Any

from ..logging.logger import (
    TRACE,
    configure_logging,
    get_log_context,
    get_logger,
    log_error,
    reset_log_context,
    set_log_context,
    setup_logging,
)
from ..logging.sanitize import sanitize_dict, sanitize_message, sanitize_url

def create_logger(name: str = "activity_engine", level: str = "INFO") -> Any:
    """Create a configured logger (backward-compatible API).

    Uses the new centralized logging system with structured formatting,
    sanitization, and file rotation.
    """
    return get_logger(name, component="SYSTEM", event="LOG")


__all__ = [
    "TRACE",
    "create_logger",
    "configure_logging",
    "setup_logging",
    "get_logger",
    "get_log_context",
    "set_log_context",
    "reset_log_context",
    "log_error",
    "sanitize_dict",
    "sanitize_message",
    "sanitize_url",
]