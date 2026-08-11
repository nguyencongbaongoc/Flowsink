"""Canonical Event model.

Every telemetry source (process, browser, network) normalizes raw data into an
:class:`ActivityEvent`. This is the single stable contract that flows through
the Event Engine, Policy Engine and out to subscribers. The schema is versioned
(``schema_version``) so future changes remain backward-compatible.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventSource(StrEnum):
    """Origin of an event."""

    PROCESS = "process"
    BROWSER = "browser"
    NETWORK = "network"
    SYSTEM = "system"
    POLICY = "policy"
    ENGINE = "engine"


class EventType(StrEnum):
    """All canonical event types produced by the engine."""

    # --- Application lifecycle ---
    APP_STARTED = "APP_STARTED"
    APP_FOCUSED = "APP_FOCUSED"
    APP_CLOSED = "APP_CLOSED"

    # --- Browser ---
    WEB_NAVIGATION = "WEB_NAVIGATION"
    WEB_TAB_FOCUSED = "WEB_TAB_FOCUSED"
    WEB_TAB_CLOSED = "WEB_TAB_CLOSED"

    # --- Network / DNS ---
    DNS_REQUEST = "DNS_REQUEST"

    # --- User presence ---
    USER_IDLE = "USER_IDLE"
    USER_ACTIVE = "USER_ACTIVE"

    # --- Session ---
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"

    # --- Policy ---
    POLICY_CHANGED = "POLICY_CHANGED"

    # --- Focus / Bedtime mode ---
    FOCUS_MODE_STARTED = "FOCUS_MODE_STARTED"
    FOCUS_MODE_ENDED = "FOCUS_MODE_ENDED"
    BEDTIME_MODE_STARTED = "BEDTIME_MODE_STARTED"
    BEDTIME_MODE_ENDED = "BEDTIME_MODE_ENDED"

    # --- Action / enforcement audit trail ---
    WARNING_ISSUED = "WARNING_ISSUED"
    REDIRECT_EXECUTED = "REDIRECT_EXECUTED"
    APP_CLOSED_BY_POLICY = "APP_CLOSED_BY_POLICY"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"
    RESTRICTED_MODE_ENABLED = "RESTRICTED_MODE_ENABLED"
    RESTRICTED_MODE_DISABLED = "RESTRICTED_MODE_DISABLED"


class ApplicationInfo(BaseModel):
    """Identifies an application/process."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, description="Human readable name, e.g. 'Google Chrome'")
    process: str | None = Field(default=None, description="Process file name, e.g. 'chrome.exe'")
    pid: int | None = Field(default=None, description="Process id when known")
    window_title: str | None = Field(default=None, description="Foreground window title (if permitted by policy)")


class BrowserInfo(BaseModel):
    """Minimal browser tab context.

    Privacy by design: never includes passwords, cookies, tokens, form
    contents, page HTML or private messages.
    """

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, description="Browser identifier, e.g. 'chrome', 'edge', 'firefox'")
    tab_id: str | None = Field(default=None, description="Tab identifier from the browser extension")
    domain: str | None = Field(default=None, description="Normalized registrable domain, e.g. 'youtube.com'")
    url: str | None = Field(default=None, description="Full URL. Only populated when policy allows (store_full_url).")
    title: str | None = Field(default=None, description="Page title. Only populated when policy allows (store_page_title).")


class NetworkInfo(BaseModel):
    """Minimal DNS/network telemetry. Not treated as proof of active tab."""

    model_config = ConfigDict(frozen=True)

    domain: str | None = Field(default=None, description="Requested domain")
    protocol: str | None = Field(default=None, description="Protocol hint, e.g. 'dns', 'tls'")


class ActivityEvent(BaseModel):
    """Canonical, schema-versioned event flowing through the system."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = "unknown-device"
    student_id: str | None = None
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: EventSource
    type: EventType
    application: ApplicationInfo = Field(default_factory=ApplicationInfo)
    browser: BrowserInfo = Field(default_factory=BrowserInfo)
    network: NetworkInfo = Field(default_factory=NetworkInfo)
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = 1

    def dedupe_key(self) -> str:
        """Return a stable key used to deduplicate equivalent notifications.

        Two events are considered duplicates when they carry the same source,
        type and target identifiers/domains within a short debounce window.
        """
        target = (
            self.browser.tab_id
            or self.browser.domain
            or self.network.domain
            or self.application.process
            or self.application.name
            or ""
        )
        return f"{self.source.value}:{self.type.value}:{target}"