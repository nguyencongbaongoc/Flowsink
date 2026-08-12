"""Browser extension event bridge.

Normalizes telemetry received from the Chrome extension into the raw event
shape the ``EventEngine`` already understands (``browser_navigation``,
``browser_tab_focus``, ``browser_tab_close``), then feeds it through the facade.

Privacy by design: the extension already strips query parameters server-side it
is never trusted with sensitive data, but this module performs a second
validation pass (scheme allow-list, domain extraction) so only safe fields
reach the policy engine.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Raw event kind mapping accepted from the extension. Any unknown kind is dropped.
_KIND_MAP = {
    "browser_navigation": "browser_navigation",
    "browser_tab_focus": "browser_tab_focus",
    "browser_tab_close": "browser_tab_close",
    "tab_created": "browser_navigation",
    "tab_updated": "browser_navigation",
    "tab_activated": "browser_tab_focus",
    "active_tab_changed": "browser_tab_focus",
    "tab_closed": "browser_tab_close",
}

_ALLOWED_SCHEMES = {"http", "https"}


def normalize_extension_event(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one extension payload into a raw EventEngine event.

    Returns the raw event dict (ready for ``engine.feed_raw``) or ``None`` when
    the payload is invalid / not actionable.
    """
    kind_raw = str(raw.get("kind") or raw.get("event_type") or "")
    kind = _KIND_MAP.get(kind_raw)
    if kind is None:
        logger.warning("browser_event=drop reason=unknown_kind kind=%s", kind_raw)
        return None

    device_id = str(raw.get("device_id") or "").strip()
    timestamp = raw.get("timestamp")
    tab_id = str(raw.get("tab_id") or "").strip()
    domain = str(raw.get("domain") or "").strip().lower()
    url = str(raw.get("url") or "").strip()
    title = str(raw.get("title") or "").strip()

    # Validate / sanitize the URL for the policy engine.
    clean_url: str | None = None
    if url:
        parsed = urlparse(url)
        if parsed.scheme in _ALLOWED_SCHEMES and parsed.netloc:
            # Strip query/fragment server-side as a second safety net.
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        else:
            logger.warning("browser_event=drop reason=unsafe_url scheme=%s", parsed.scheme)
            return None

    # Derive domain from the URL when the extension did not supply one.
    if not domain and clean_url:
        domain = urlparse(clean_url).netloc.lower().removeprefix("www.")

    if not domain and kind != "browser_tab_close":
        logger.warning("browser_event=drop reason=missing_domain kind=%s", kind)
        return None

    browser: dict[str, Any] = {
        "name": str(raw.get("browser_name") or raw.get("name") or "chrome"),
        "tab_id": tab_id or None,
        "domain": domain or None,
        "url": clean_url,
        "title": title or None,
    }

    result: dict[str, Any] = {
        "kind": kind,
        "source": "extension",
        "browser": browser,
    }
    if timestamp:
        result["timestamp"] = timestamp

    # EventEngine.normalize() takes device_id from its constructor, not from
    # the raw dict. Preserve the extension-reported device id as metadata so
    # it is never silently dropped.
    extra_metadata = {
        k: v
        for k, v in raw.items()
        if k
        not in {
            "kind",
            "event_type",
            "source",
            "timestamp",
            "device_id",
            "tab_id",
            "domain",
            "url",
            "title",
            "browser_name",
            "name",
        }
    }
    if device_id:
        extra_metadata.setdefault("extension_device_id", device_id)
    if extra_metadata:
        result["metadata"] = extra_metadata

    return result
