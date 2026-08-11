"""Stable id helpers."""

from __future__ import annotations

import uuid


def new_id(prefix: str = "") -> str:
    """Generate a new id, optionally prefixed (e.g. ``act_...``)."""
    value = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{value}"
    return value


def short_id() -> str:
    """Compact id for logs and state keys."""
    return str(uuid.uuid4())[:8]