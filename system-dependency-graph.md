# System Dependency Graph — Flowsink Activity Engine

> PHASE 11 (updated): Reflects all changes from PHASE 0-4 fixes + orphan audit + frontend archive.

## Legend

- **CANONICAL** — component preserved unchanged per audit rules; never rewritten.
- **LEGACY STUB** — Windows adapter that raises `NotImplementedError`; marked with LEGACY docstring.
- **ORPHAN** — service defined but never imported/instantiated by any active code path.
- **ACTIVE** — service wired into the running pipeline.
- **OPTIONAL** — FastAPI/uvicorn server; imported only when server deps are installed.

## Canonical Components (Preserved)

| Component | Path |
|-----------|------|
| Logging layer | `src/activity_engine/logging/` |
| Mock action executor | `src/activity_engine/adapters/mock/action_executor.py` |
| Screen provider abstraction | `src/activity_engine/platform/screen.py` |
| Engine facade | `src/activity_engine/engine/facade.py` |
| Policy (default + loader + classifier + evaluator) | `src/activity_engine/policy/` |
| Extension browser monitor | `src/activity_engine/adapters/extension/browser_monitor.py` |
| FastAPI server | `src/activity_engine/server.py` |

## Active Pipeline (Runtime Call Chain)

```
CLI (doctor/monitor/simulate/policy-check)
  → ActivityEngine (facade)
    → load_dev_config() → Config
    → PolicyLoader / load_default_policy() → PolicyDocument  [FAIL-FAST]
    → EventEngine.subscribe(_route)  [async event pipeline]
      → EventEngine.process_raw()
        → normalize() → ActivityEvent
        → debounce / dedupe
        → _route callback:
          → PolicyEvaluator.evaluate() → PolicyDecision
          → StateEngine.apply_decision() → StateSnapshot
          → EscalationEngine.plan() → [ActionRequest]
            → ActionEngine.execute()
              → Adapter (MockActionExecutor by default)
          → ScreenshotService (if WARNING+) [fault-isolated]
          → InMemoryActivityRepository.store_event/state/
    → MonitoringService (CLI monitor --backend)
      → ExtensionBrowserMonitor (chrome extension bridge) OR
      → MockBrowserMonitor / WindowsProcessMonitor + WindowsNetworkMonitor
```

## Server API (`src/activity_engine/server.py`)

```
GET  /                    — health check
POST /api/session/start   — start monitoring session
POST /api/session/end     — end session
GET  /api/state           — current StateSnapshot JSON
GET  /api/metrics         — engine metrics
GET  /api/events          — recent events
POST /api/telemetry       — feed raw telemetry
POST /api/browser/telemetry — batched Chrome extension tab telemetry
GET  /api/browser/active  — latest active tab(s) per device  [POLL]
GET  /api/session/status  — session id + active flag
POST /api/screenshot      — manual capture trigger
WS   /ws                  — realtime broadcast
```

## Browser Extension Bridge Contract (PHASE 6)

```
Chrome Extension (browser-extension/background.js)
  ──POST──→ /api/browser/telemetry  {events: [...]}
  │           │
  │           └→ BrowserStateStore.record_event()
  │              → normalize_extension_event()  [scheme allow-list, query strip]
  │              → EventEngine.feed_raw()
  │
  ←─GET─── /api/browser/active  → {"tabs": [...], "count": N}
                     ↑
                     │
  ExtensionBrowserMonitor._poll_http()
    → data.get("tabs")  →  [tab.dict per device]
    → monitor.started = False  (if backend offline, returns [])
  │
  MonitoringService._poll_browser()
    → tabs[0].get("name"/"tab_id"/"domain")
    → EventEngine.process_raw({"kind":"browser_navigation", ...})
```

## Adapter Conformance (PHASE 5)

| Port (Protocol) | MonitoringService method | Canonical Adapter | Windows Adapter |
|-----------------|------------------------|-------------------|-----------------|
| ProcessMonitor | `start/stop`, `get_foreground_process()`, `get_running_processes()` | MockProcessMonitor | WindowsProcessMonitor ✅ (real), stubs raise NotImplementedError |
| BrowserMonitor | `start/stop`, `get_active_tabs()` | MockBrowserMonitor / ExtensionBrowserMonitor | WindowsBrowserMonitor 🚫 (LEGACY STUB) |
| NetworkMonitor | `start/stop`, `get_recent_domains()` | MockNetworkMonitor | WindowsNetworkMonitor ✅ (real) |
| ActionExecutor | `warn/redirect/close_application/block_domain/enable/disable_restricted_mode` | MockActionExecutor ✅ | WindowsActionExecutor 🚫 (LEGACY STUB) |
| DeviceController | `get_capabilities()`, `enable/disable_restricted_mode()`, `lock_device()` | — | WindowsDeviceController 🚫 (LEGACY STUB) |

### Fault Isolation

`MonitoringService._run_monitor()` catches `NotImplementedError` and logs `status=unavailable` — Windows stubs never crash the pipeline; they are skipped gracefully.

## Orphan Services (PHASE 9)

See [docs/ORPHAN_SERVICES_CLASSIFICATION.md](docs/ORPHAN_SERVICES_CLASSIFICATION.md) for full analysis.

| Service | Classification | Reason |
|---------|---------------|--------|
| `activity_service.py` | Dead code | Duplicate of facade's state tracking |
| `bedtime_service.py` | Dead code | Not scheduled; has deprecated asyncio bug |
| `focus_service.py` | Dead code (parallel impl) | Full duplicate of `ActivityEngine` facade pipeline |

## Frontend Scaffold (PHASE 8)

The `index.html`, `vite.config.js`, `package.json`, `src/assets/`, and `public/` were a disconnected frontend scaffold with **no React entry point**. Archived to `archive/frontend-disconnected/` (not deleted per audit rules).

## Dependency Layers (bottom → top)

```
Layer 1:  core/          (events, actions, states, decisions, policies, errors)
Layer 2:  domain/        (activity, device, session, student, violations)
Layer 3:  logging/       (logger, sanitize, context, formatters)
Layer 4:  policy/        (loader, classifier, evaluator)
Layer 5:  utils/         (ids, logging)
Layer 6:  persistence/   (repository)
Layer 7:  platform/      (screen — cross-platform factory)
Layer 8:  engine/        (event, policy, state, action, escalation engines + facade)
Layer 9:  adapters/      (mock, extension, windows)
Layer 10: services/      (monitoring, screenshot, browser_state, browser_events)
Layer 11: transport/     (dto, protocol, serialization)
Layer 12: cli/           (main entry point)
Layer 13: server/        (FastAPI — optional)
```
