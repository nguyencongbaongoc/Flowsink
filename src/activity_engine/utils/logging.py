"""Structured logging helpers.

Never log passwords, cookies, tokens, full private content, or unnecessary
browsing payloads.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_STRUCTURED_FORMAT = "timestamp={timestamp} level={level} msg={message}"

class StructuredFormatter(logging.Formatter):
    """Minimal structured formatter producing key=value lines."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).isoformat()
        base = (
            f"{timestamp} {record.levelname} {record.getMessage()}"
        )
        extra: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName", "asctime",
            }:
                continue
            extra[key] = value
        parts = [base]
        for key in sorted(extra):
            parts.append(f"{key}={safe_value(extra[key])}")
        if record.exc_info:
            parts.append(f"exc={self.formatException(record.exc_info)!r}")
        return " ".join(parts)

def safe_value(value: Any) -> str:
    """Serialize values safely for logs (no nested secrets)."""
    if isinstance(value, str):
        return value.replace(" ", "_")
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)

def create_logger(name: str = "activity_engine", level: str = "INFO") -> logging.Logger:
    """Create a configured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
    return logger