"""Log context helpers — correlation IDs and context management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from .logger import get_log_context, reset_log_context, set_log_context


@contextmanager
def log_context(
    *,
    event_id: str | None = None,
    session_id: str | None = None,
    device_id: str | None = None,
) -> Iterator[None]:
    """Context manager that sets and restores log context.

    Example::

        with log_context(event_id=event.event_id, session_id=session_id):
            logger.info("processing event")
    """
    previous = get_log_context()
    set_log_context(
        event_id=event_id or previous.get("event_id"),
        session_id=session_id or previous.get("session_id"),
        device_id=device_id or previous.get("device_id"),
    )
    try:
        yield
    finally:
        reset_log_context()
        # Restore previous context
        set_log_context(**previous)


__all__ = ["log_context", "get_log_context", "set_log_context", "reset_log_context"]