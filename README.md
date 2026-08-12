# Student Activity Monitoring & Focus Control Engine

A standalone, production-ready foundation module designed to monitor student activity, evaluate policies, and execute safe enforcement actions. 

Designed using **Clean Architecture**, **Hexagonal Architecture (Ports & Adapters)**, and **Event-Driven Architecture**, this engine remains completely independent of platform-specific APIs, databases, browser implementations, or the main application core.

## Features

- **Telemetry Normalization**: Unifies process, browser, and network DNS traffic into canonical schema-versioned `ActivityEvent` objects.
- **Deduplication & Debouncing**: Prevents high-frequency event spam.
- **Explicit State Machine**: Mutation of state is guarded by an explicit state transitions model to prevent invalid state configurations.
- **Three-Level Enforcement**: Escalates violations through warnings, browser redirection, domain blocks, and device-level Focus/Restricted Mode.
- **Structured Logging**: Fully compatible with SIEM and observability stacks; redacts all privacy-sensitive payloads (cookies, passwords, keystrokes).
- **Dry-Run Mode**: Supports full auditing and testing of policy decisions without performing system mutations.

## Getting Started

### Installation

```bash
pip install -e .[dev]
```

### Running CLI

```bash
# System diagnostic check (works on macOS and Windows)
activity-engine doctor

# Simulate events and observe policy evaluation
activity-engine simulate --events 10

# Live monitoring (macOS/Linux: mock; Windows: real backend automatically)
activity-engine monitor --mode dry_run

# Force the real Windows backend (process + network)
activity-engine monitor --mode dry_run --backend real
```

> **Windows users:** double-click `setup_windows.bat` once, then `run_windows.bat`.
> See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for details.

### Integration Example

```python
from activity_engine import ActivityEngine

engine = ActivityEngine(student_id="ST001")
session_id = engine.start_session()

# Feed raw telemetry
await engine.feed_raw({
    "kind": "browser_navigation",
    "browser": {"domain": "youtube.com", "tab_id": "tab-1"}
})

snapshot = engine.current_state()
print(f"Current State: {snapshot.state.value}") # State: WARNING
```

## Platform Support

| Feature            | macOS            | Windows 10/11                 |
|--------------------|------------------|-------------------------------|
| Process monitoring | mock             | real (`Win32` + `psutil`)     |
| Screen capture     | mock (unavailable)| real (`mss` / GDI)           |
| Network monitoring | mock             | real (`psutil.net_connections`) |
| Browser monitoring | stub             | stub (Phase 2)                |
| Action executor    | mock             | mock (Phase 2)                |

See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for the full Windows guide.

For detailed guides, see the `docs/` folder:
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Integration Contract](docs/INTEGRATION.md)
- [Event Schema Contract](docs/EVENT_CONTRACT.md)
- [Policy Syntax](docs/POLICY_ENGINE.md)
- [Security & Threat Model](docs/SECURITY.md)
