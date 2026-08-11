# Integration Contract

The Activity Engine is designed to be integrated into any host application via the `ActivityEngine` facade.

## Public API

```python
from activity_engine import ActivityEngine

engine = ActivityEngine(student_id="ST001")
session_id = engine.start_session()

# Feed raw telemetry
await engine.feed_raw({
    "kind": "browser_navigation",
    "browser": {"domain": "youtube.com", "tab_id": "tab-1"}
})

# Query current state
snapshot = engine.current_state()
print(snapshot.state.value)  # WARNING

# End session
engine.end_session()
```

## Runtime Modes

| Mode | Behavior |
|------|----------|
| `dry_run` | Record decisions and metrics only; no system mutations. |
| `audit_only` | Like `dry_run`, but writes detailed audit records. |
| `enforce` | Execute real enforcement actions (warnings, blocks, restricted mode). |

## Telemetry Sources

The engine normalizes three types of raw telemetry into canonical `ActivityEvent` objects:

1. **Process Monitor** (`process_focus`, `process_start`, `process_stop`)
2. **Browser Monitor** (`browser_navigation`, `browser_tab_focus`, `browser_tab_close`)
3. **Network Monitor** (`dns_request`)

Each adapter must emit events with a `kind` field matching the `EventInput` enum in `engine/event_engine.py`.

## Action Executors

The engine issues typed `ActionRequest` objects to an adapter implementing the `ActionExecutor` port:

```python
class ActionExecutor(Protocol):
    async def warn(self, request: dict) -> dict: ...
    async def redirect(self, request: dict) -> dict: ...
    async def close_application(self, request: dict) -> dict: ...
    async def block_domain(self, request: dict) -> dict: ...
    async def enable_restricted_mode(self, request: dict) -> dict: ...
    async def disable_restricted_mode(self, request: dict) -> dict: ...
```

For testing, use `MockActionExecutor` from `activity_engine.adapters.mock.action_executor`.

## Configuration

```python
from activity_engine.config.models import Config, RuntimeConfig
from activity_engine.core.decisions import EnforcementMode

config = Config(
    runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN)
)
engine = ActivityEngine(config=config, student_id="ST001")
```

## Policy

Policies are loaded from YAML files. See `docs/POLICY_ENGINE.md` for syntax.

## Observability

All engines expose metrics dictionaries:

```python
metrics = engine.metrics()
# {
#   "event_engine": {...},
#   "policy_engine": {...},
#   "action_engine": {...}
# }
```

Structured logs are emitted via Python’s `logging` module with `INFO`/`WARNING` levels. Sensitive fields (cookies, passwords, keystrokes) are never logged.