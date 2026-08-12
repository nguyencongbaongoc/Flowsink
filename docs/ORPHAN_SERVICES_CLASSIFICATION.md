# Orphan Services Classification Report

## Scope

This document classifies the three service modules under
`src/activity_engine/services/` that are **not wired into the active runtime
pipeline**:

| # | Module | Class | Classification |
|---|--------|-------|----------------|
| 1 | `activity_service.py` | `ActivityService` | **Dead code (unconnected)** |
| 2 | `bedtime_service.py` | `BedtimeService` | **Dead code (unconnected)** |
| 3 | `focus_service.py`   | `FocusService`  | **Dead code (unconnected)** |

> **Policy:** Per audit rules, untested-orphan files are **classified, not deleted**.
> They are retained so future work can adopt or remove them deliberately.

---

## 1. ActivityService (`activity_service.py`)

**Status:** Dead code — defined, never imported or instantiated.

**What it does:**
- Maintains a `CurrentActivity` aggregate (application, browser, last_seen)
- Provides `update_from_event()`, `.current` property, `.reset()`

**Why it is unconnected:**
The `ActivityEngine` facade already owns the canonical activity-tracking
pipeline via `EventEngine → PolicyEngine → StateEngine`. The
`ActivityService` reimplements a thin parallel aggregate that is never fed
events or queried by any caller.

**Cross-reference:** `domain/activity.py` (`CurrentActivity`) exists only for
this service and is otherwise unused.

**Recommendation:** Either wire `ActivityService` into the facade's event
route (to provide a lightweight `current` query API) or delete both
`activity_service.py` and `domain/activity.py` in a future cleanup.

---

## 2. BedtimeService (`bedtime_service.py`)

**Status:** Dead code — defined, never imported or instantiated.

**What it does:**
- Schedules bedtime warnings and restricted-mode entry based on a
  `BedtimePolicy` start time.
- Uses an injectable `clock` callable for testability.

**Why it is unconnected:**
The `BedtimePolicy` model is embedded in `PolicyDocument` and loaded by the
policy engine, but `BedtimeService` itself is never invoked by the facade
or CLI. There is no schedule-tick loop that calls `BedtimeService.check()`.

**Known bug (documented, not fixed in this phase):**
- `_issue_warning()` and `_enter_restricted_mode()` both perform an
  `import asyncio` inside the method body on every call (redundant — `asyncio`
  is already a top-level dependency).
- They use `asyncio.get_event_loop().create_task(...)` which is deprecated in
  Python 3.10+ and raises `DeprecationWarning` / `RuntimeError` when no
  running loop exists. This would crash if called from a non-async context.

**Recommendation:** Either integrate `BedtimeService` into a periodic
scheduler (async task in the facade or CLI `monitor` command) or defer
bedtime enforcement to the `PolicyEngine` via time-based event enrichment.

---

## 3. FocusService (`focus_service.py`)

**Status:** Dead code — defined, never imported or instantiated.

**What it does:**
- Orchestrates a full focus session: session lifecycle, event processing,
  policy evaluation, state transitions, and action execution (delegated to
  `ActionEngine`).

**Why it is unconnected:**
This is a **parallel reimplementation of the `ActivityEngine` facade**. It
duplicates the event → policy → state → action pipeline that the facade
already provides via `_route()` and the subscribed engines. No module in the
system imports or constructs `FocusService`.

**Recommendation:** Remove `FocusService` (and its dependency on
`bedtime_service.py`'s `BedtimeService` if removed) once the facade's
public API is confirmed sufficient. The facade already exposes
`start_session()`, `feed_raw()`, `current_state()`, `recent_events()`,
`violations()`, and `metrics()`.

---

## Dependency Graph Impact

```
facade.py (ActivityEngine)
  ├── core/       (events, policies, decisions, actions, states)
  ├── engine/     (event_engine, policy_engine, state_engine,
  │                 action_engine, escalation_engine)
  ├── persistence/  (InMemoryActivityRepository)
  ├── adapters/     (mock.*, windows.*, extension)
  └── services/
       ├── monitoring_service.py  ← ACTIVE (used by CLI monitor)
       ├── screenshot_service.py  ← ACTIVE (used by facade)
       ├── browser_state.py       ← ACTIVE (used by server + extension bridge)
       ├── browser_events.py      ← ACTIVE (used by browser_state)
       ├── activity_service.py   ← ORPHAN (not imported)
       ├── bedtime_service.py    ← ORPHAN (not imported)
       └── focus_service.py      ← ORPHAN (not imported)
```

---

## Conclusion

None of the three orphan services contribute to the running system. The
canonical pipeline flows through `ActivityEngine` (facade) → `EventEngine`
(subscribes to `_route`) → `PolicyEngine` → `StateEngine` →
`EscalationEngine` → `ActionEngine`. `MonitoringService` feeds adapters
into `EventEngine.process_raw()`.

The orphans are retained as-is (not deleted, per audit rules) and are
documented here for future cleanup decisions.
