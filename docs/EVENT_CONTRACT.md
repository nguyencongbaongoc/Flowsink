# Event Schema Contract

The Activity Engine normalizes all telemetry into canonical `ActivityEvent` objects with this schema:

```python
class ActivityEvent(BaseModel):
    event_id: str  # UUID4
    device_id: str
    student_id: str | None
    session_id: str | None
    timestamp: datetime
    source: EventSource  # process/browser/network/system
    type: EventType  # APP_FOCUSED/WEB_NAVIGATION/etc.
    application: ApplicationInfo | None
    browser: BrowserInfo | None
    network: NetworkInfo | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = 1
```

## Event Types

| Source | Type | Description |
|--------|------|-------------|
| process | APP_STARTED | Application launched |
| process | APP_FOCUSED | Application became foreground |
| process | APP_CLOSED | Application terminated |
| browser | WEB_NAVIGATION | Page navigation |
| browser | WEB_TAB_FOCUSED | Tab became active |
| browser | WEB_TAB_CLOSED | Tab closed |
| network | DNS_REQUEST | DNS query |
| system | USER_IDLE | User inactive |
| system | USER_ACTIVE | User active |
| policy | POLICY_CHANGED | Policy updated |
| engine | FOCUS_MODE_STARTED | Focus mode activated |
| engine | FOCUS_MODE_ENDED | Focus mode deactivated |
| engine | BEDTIME_MODE_STARTED | Bedtime mode activated |
| engine | BEDTIME_MODE_ENDED | Bedtime mode deactivated |

## Privacy Considerations

- **Browser Events**: Only include `domain` and `url` when explicitly allowed by policy.
- **Application Events**: Never include window titles or clipboard contents.
- **Network Events**: Only include domains, never full URLs or payloads.
- **Metadata**: All metadata fields are optional and may be filtered by policy.

## Versioning

The `schema_version` field allows backward-compatible schema evolution. New fields may be added, but existing fields must never be removed or changed.