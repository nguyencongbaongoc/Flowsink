# Windows Compatibility Report — Flowsink Activity Engine

**Audit date:** 2026-08-12  
**Audit platform:** macOS (Darwin, arm64) — static + platform-safe runtime checks  
**Windows runtime verification:** NOT executed (requires a real Windows machine; see [WINDOWS_SETUP.md](../WINDOWS_SETUP.md))

---

## 1. Executive summary

| Area                          | Status      | Notes                                                        |
|-------------------------------|-------------|--------------------------------------------------------------|
| Python packaging (pyproject)  | ✅ Ready    | `src/` layout, wheel metadata, `activity-engine` entry point |
| Dependencies                  | ✅ Ready    | `psutil`, `mss` added; wheels available for Windows          |
| CLI `doctor`                  | ✅ Ready    | platform-aware, no `ctypes.WinDLL` crash on macOS            |
| CLI `monitor`                 | ✅ Ready    | `--backend real` auto-selects Windows real adapters          |
| Process monitoring            | ✅ Real     | `WindowsProcessMonitor` (Win32 `user32.dll` + `psutil`)      |
| Network monitoring            | ✅ Fixed    | replaced stub with real `psutil.net_connections()` monitor   |
| Screen capture / screenshots  | ✅ Implemented | new `platform/` abstraction + `WindowsScreenProvider` (mss)  |
| Browser monitoring            | ⚠️ Stub     | Phase-2 native browser extension required                     |
| Action executor               | ⚠️ Stub     | `MockActionExecutor`; enforce mode unsafe until Phase 2       |
| Startup scripts               | ✅ Ready    | `setup_windows.bat`, `run_windows.bat`                       |
| Docs                          | ✅ Ready    | `WINDOWS_SETUP.md`, README platform table                    |

---

## 2. Critical fixes applied

### 2.1 `doctor` crashed on non-Windows hard-import of Windows adapters
- **Before:** `cli/main.py` unconditionally imported `WindowsProcessMonitor`, which calls `ctypes.WinDLL("user32.dll")` at module import time → `OSError` on macOS.
- **After:** `_cmd_doctor` selects adapters by `sys.platform`; Windows modules import cleanly on macOS (verified) and only instantiate Win32 APIs on Windows.

### 2.2 `WindowsNetworkMonitor` was a stub raising `NotImplementedError`
- **Before:** network monitoring was always unavailable.
- **After:** real implementation using `psutil.net_connections(kind="inet")`; stable `ip:port` endpoint labels; no admin rights needed.

### 2.3 No screen/screenshot provider existed
- **After:** new `src/activity_engine/platform/` package:
  - `screen.py` — `ScreenProvider` port, `ScreenInfo`, `get_screen_provider()`, `default_screenshot_dir()`, `make_screenshot_filename()`
  - `windows_screen.py` — `mss`-backed real capture (native GDI, no PIL required)
  - `mock_screen.py` — safe fallback on macOS/Linux (reports no capture instead of installing Quartz)
- Doctor reports screen capability without crashing.

### 2.4 Violation records had two sources of truth
- **Before:** facade `violations()` read from `InMemoryActivityRepository._violations`, which was never populated → always empty. `PolicyEngine.violations()` was ignored.
- **After:** facade returns canonical `PolicyEngine.violations_for(student_id, limit)` (repository `store_violation` left unused intentionally). Regression test added.

### 2.5 Events were not stamped with the active session id
- **Before:** `EventEngine` never set `session_id` → stored events/violations had `session_id=None`.
- **After:** facade `_route` stamps the active session id onto every normalized event before policy evaluation/storage. Regression test added.

---

## 3. Files changed / added

| File                           | Action | Purpose                                             |
|--------------------------------|--------|-----------------------------------------------------|
| `pyproject.toml`               | edited | added `psutil`, `mss` to runtime deps               |
| `requirements.txt`             | added  | cross-platform runtime deps                         |
| `requirements-windows.txt`     | added  | Windows install entry (includes requirements.txt)   |
| `requirements-server.txt`      | added  | optional FastAPI/uvicorn deps                       |
| `.env.example`                 | added  | env template (DEVICE_ID, LOG_LEVEL, server, keys)   |
| `src/activity_engine/platform/__init__.py`         | added | platform abstraction package                    |
| `src/activity_engine/platform/screen.py`           | added | ScreenProvider port + helpers                   |
| `src/activity_engine/platform/windows_screen.py`   | added | mss-backed Windows capture                      |
| `src/activity_engine/platform/mock_screen.py`      | added | macOS/Linux fallback                            |
| `src/activity_engine/adapters/windows/network_monitor.py` | rewritten | real psutil-based network monitor       |
| `src/activity_engine/cli/main.py` | rewritten | platform-aware doctor/monitor; `--backend` flag |
| `src/activity_engine/cli/__main__.py` | added | `python -m activity_engine.cli`              |
| `src/activity_engine/__main__.py`      | added | `python -m activity_engine`                  |
| `src/activity_engine/engine/facade.py` | edited | session_id stamping + canonical violations   |
| `tests/test_integration.py`      | edited | 2 regression tests added                         |
| `run_windows.bat`               | added  | Windows launcher (venv + deps + PYTHONPATH)        |
| `setup_windows.bat`             | added  | one-time Windows setup                             |
| `WINDOWS_SETUP.md`              | added  | full Windows user guide                            |
| `README.md`                     | edited | Windows CLI + platform-support table               |
| `docs/WINDOWS_COMPATIBILITY_REPORT.md` | added | this report                                    |

---

## 4. Validation results (on macOS, runtime-safe)

```
$ python -m pytest tests/
  collected 32 items
  32 passed, 7 warnings (0.06s)
```

```
$ python -m activity_engine.cli doctor
  Activity Engine Doctor v0.1.0
  Platform : darwin
  [OK ] psutil
  [OK ] yaml
  [OK ] pydantic
  [OK ] screen_capture   (monitors=1 dir=/Users/nguyenngoc/Flowsink/screenshots)
  [OK ] process_monitor
  [OK ] network_monitor
  [OK ] device_capabilities
  Overall: HEALTHY
```

| Test                                                                 | Result |
|----------------------------------------------------------------------|--------|
| Full unit/integration/contract suite (32 tests)                      | ✅ pass |
| `doctor` no-crash on macOS (previously crashed on WinDLL import)     | ✅ pass |
| `doctor --json` structured output                                    | ✅ pass |
| `monitor --backend real` gracefully falls back to mocks on macOS     | ✅ pass |
| Windows adapter modules import on macOS without executing Win32 APIs | ✅ pass |
| `simulate --events 6` end-to-end (session, events, warnings)         | ✅ pass |
| `monitor --backend mock` runs until terminated (SIGTERM exit -15)    | ✅ pass |
| `engine.violations()` returns canonical PolicyEngine violations       | ✅ pass (regression test) |
| All stored events carry active `session_id`                          | ✅ pass (regression test) |
| MonitoringService with seeded mock data emits events                 | ✅ pass (3 processed) |

---

## 5. Remaining Windows-only gaps (Phase 2 candidate)

1. **Browser monitoring** — requires a browser extension or accessibility API.
2. **Real action executor** — closing apps, blocking domains, restricted mode are stubs; `enforce` mode with real execution should not be used until implemented.
3. **Admin elevation** — `psutil.net_connections()` works without admin; hosts-file domain blocking would require elevation.

---

## 6. How to verify on real Windows

1. Copy project to Windows 10/11.
2. Install Python 3.11+ (tick “Add Python to PATH”).
3. Run `setup_windows.bat`.
4. Run `run_windows.bat doctor` → expect `screen_capture OK (monitors>=1)`.
5. Run `run_windows.bat monitor --mode dry_run --backend real`.
6. Confirm `psutil`, `yaml`, `pydantic`, `process_monitor`, `network_monitor` all show `OK`.

See [WINDOWS_SETUP.md](../WINDOWS_SETUP.md) for the complete guide.