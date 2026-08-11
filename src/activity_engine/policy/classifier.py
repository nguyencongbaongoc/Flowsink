"""Domain and application classification helpers."""

from __future__ import annotations

import fnmatch
from urllib.parse import urlparse

def normalize_domain(value: str | None) -> str | None:
    """Normalize a domain or URL to its registrable-domain hint.

    Returns ``None`` for empty/irrelevant input.
    """
    if not value:
        return None
    value = value.strip().lower()
    if not value:
        return None
    # Strip protocol and path if a full URL was provided.
    if "://" in value:
        value = urlparse(value).netloc or value
    # Strip port
    if ":" in value:
        value = value.split(":", 1)[0]
    # Strip leading www.
    if value.startswith("www."):
        value = value[4:]
    return value or None

def domain_matches(domain: str | None, pattern_list: list[str]) -> bool:
    """Check whether ``domain`` matches any entry in ``pattern_list``.

    Entries may be exact domains (``youtube.com``) or wildcard patterns
    (``*.google.com``).
    """
    if not domain:
        return False
    domain = domain.lower()
    for pattern in pattern_list:
        pattern = pattern.strip().lower()
        if not pattern:
            continue
        if pattern.startswith("*."):
            base = pattern[2:]
            if domain == base or domain.endswith(f".{base}"):
                return True
        elif pattern == domain or domain.endswith(f".{pattern}"):
            return True
        elif fnmatch.fnmatch(domain, pattern):
            return True
    return False

def app_matches(app_name: str | None, process: str | None, pattern_list: list[str]) -> bool:
    """Check whether an application matches any entry in ``pattern_list``."""
    candidates = [value for value in (app_name, process) if value]
    if not candidates:
        return False
    for pattern in pattern_list:
        pattern = pattern.strip().lower()
        if not pattern:
            continue
        for candidate in candidates:
            candidate = candidate.strip().lower()
            if candidate == pattern or fnmatch.fnmatch(candidate, f"*{pattern}*"):
                return True
    return False