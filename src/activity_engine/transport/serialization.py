"""Serialization helpers for events, decisions, and snapshots."""

from __future__ import annotations

import json
from datetime import UTC, datetime, date
from enum import Enum
from typing import Any

def to_jsonable(value: Any) -> Any:
    """Convert common domain objects into JSON-serializable primitives."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)

def dumps(value: Any) -> str:
    """Serialize a domain object to a compact JSON string."""
    return json.dumps(to_jsonable(value), ensure_ascii=False, separators=(",", ":"))

def loads(raw: str) -> dict[str, Any]:
    """Parse a wire JSON message into a dict."""
    return json.loads(raw)  # type: ignore[no-any-return]
