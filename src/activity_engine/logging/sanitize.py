"""Secret sanitization for log messages.

Never log: passwords, API keys, bearer tokens, JWT, cookies, secrets,
browser credentials, Authorization headers, Set-Cookie, X-API-Key.
"""

from __future__ import annotations

import re
from typing import Any

# Keys whose values are always redacted
_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "bearer",
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "secret",
    "client_secret",
    "jwt",
    "session_token",
    "auth_token",
    "private_key",
    "credential",
    "credentials",
}

# Patterns for redacting inline secret=value pairs in messages
_SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(passwd\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(pwd\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(access[_-]?token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(refresh[_-]?token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9\-._~+/]+=*)"),
    re.compile(r"(?i)(authorization\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(x-api-key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(cookie\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(set-cookie\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(client[_-]?secret\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(jwt\s*[=:]\s*)([^\s,;]+)"),
]

_REDACTED = "*****"

def sanitize_message(message: str) -> str:
    """Replace sensitive values in a log message with a redaction marker."""
    result = message
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        result = pattern.sub(lambda m: f"{m.group(1)}{_REDACTED}", result)
    return result

def sanitize_url(url: str) -> str:
    """Remove query parameters from a URL to avoid leaking secret query strings."""
    if "?" not in url:
        return url
    base = url.split("?", 1)[0]
    return f"{base}?[REDACTED]"

def sanitize_value(key: str, value: Any) -> str:
    """Return a redacted string representation of a value for a given key."""
    key_lower = key.lower().strip()
    if key_lower in _SENSITIVE_KEYS:
        return _REDACTED
    if any(sensitive in key_lower for sensitive in ("password", "token", "secret", "api_key", "api-key")):
        return _REDACTED
    if isinstance(value, str):
        return sanitize_message(value)
    return str(value)

def sanitize_dict(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a sanitized copy of a dict, redacting sensitive keys."""
    if data is None:
        return None
    result: dict[str, Any] = {}
    for key, value in data.items():
        if str(key).lower() in _SENSITIVE_KEYS or any(
            s in str(key).lower() for s in ("password", "token", "secret", "api_key", "api-key")
        ):
            result[key] = _REDACTED
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, str):
            result[key] = sanitize_message(value)
        else:
            result[key] = value
    return result