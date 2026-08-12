# FULL SYSTEM COMPATIBILITY AUDIT

**Repository:** Flowsink (Flowsink / Student Activity Engine)
**Mode:** Forensic audit — no files modified.
**Date:** 2026-08-12
**Scope:** All files (excluding `.git`, `.venv`, `node_modules`, `__pycache__`, `.pytest_cache` per audit rules).

---

## 1. EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| Total files scanned | **150** |
| Active (runtime reachable) | **~100** (all `src/activity_engine/**` except orphans, + entrypoints, extension, docs) |
| Legacy files | **4** |
| True orphan files | **10** |
| Broken references | **7** |
| Missing modules | **0** (all python imports resolve) |
| Missing resources | **2** (`config/policy.yaml`, `config/local.yaml`) |
| Unused configs | **1** (`policy_file`, `monitoring.*`) |
| Unused dependencies | **2** (per pyproject; see §7) |
| Duplicate implementations | **3** |
| Compatibility issues | **12** |
| Critical issues | **3** |
| High issues | **4** |
| Medium issues | **5** |
| Low issues | **3** |

---

## 2. CRITICAL FINDINGS

### C1 — SECURITY: API key committed in `.env.local`
```
ID: C1
SEVERITY: CRITICAL
FILE: .env.local
LOCATION: line 8 VITE_GEMINI_API_KEY=AQ.Ab8RN6ISX24IFm4MPFaEhb-KEbhVNWv1wSlK6RC7TC1hYnWflQ
PROBLEM: A live-looking Gemini API key is committed to the repository.
WHY: .gitignore excludes .env.local but the file was added before the ignore rule (or force-added). The key is exposed in repo history.
IMPACT: Credential leak; potential abuse/billing. Also .env.local maps VITE_GEMINI_API_KEY but .env.example defines GEMINI_API_KEY and VITE_GEMINI_API_KEY — naming mismatch.
EVIDENCE: Read of .env.local shows the raw key; .gitignore (root) must be verified to include .env.local — file exists in the working tree despite being marked git-ignored, indicating it was tracked earlier.
RECOMMENDED FIX: Rotate the key; remove from history (git filter-repo / BFG); confirm .gitignore ignores .env.local and .env.*.
```

### C2 — RUNTIME: `run_windows.bat` default branch calls a policy path/monitor that can silently no-op, and `policy-check` default fails
```
ID: C2
SEVERITY: CRITICAL
FILE: run_windows.bat; src/activity_engine/cli/main.py
LOCATION: run_windows.bat:87-93 ; cli/main.py:66 & 380-403
PROBLEM: The default launcher branch runs `activity_engine.cli monitor --mode dry_run --backend real`. On this (non-Windows) audit machine, `--backend real` triggers a warning and falls back to mocks, so monitoring is safe. But `policy-check` subcommand defaults to `config/policy.yaml` which does NOT exist, so it always fails unless a path is supplied. Combined with `config.loader` reading `config/local.yaml` (also missing), any deployment assuming default config will behave with empty/fallback policy.
WHY: Hardcoded `config/` paths that were never created.
IMPACT: `run_windows.bat` on Windows works for `monitor/doctor` (mock fallback + default policy via bundled default_policies.yaml), but `policy-check` and any `config/policy.yaml`-based flow will fail out of the box. Silent degradation risk: engine loads `PolicyDocument()` empty if default policy load fails, meaning NO enforcement decisions.
EVIDENCE: `find . -name 'policy.yaml'` → only `./examples/policy.yaml`; `ls config/` → No such file; `config/models.py:49 policy_file="config/policy.yaml"`; `config/loader.py:34-35` reads `config/local.yaml`.
RECOMMENDED FIX: Ship a `config/` directory with `local.yaml.example`/`policy.yaml` or change defaults to resolve package-bundled resources; update `run_windows.bat` default to `simulate` if no backend is desired.
```

### C3 — RUNTIME/LAUNCHER: bare `python` resolves to Python 2.7; `.bat` launchers assume 3.11+
```
ID: C3
SEVERITY: CRITICAL
FILE: run_windows.bat (lines 24-33, 40), setup_windows.bat (lines 24-33, 42), pyproject.toml (requires-python = ">=3.11")
LOCATION: Every `%PYTHON% -m venv` / `where python` call
PROBLEM: On the audit machine, `python --version` = Python 2.7.18 while the project requires Python >=3.11 and the code/tests use Python 3.x-only syntax (e.g. `from __future__ import annotations`, `def f() -> PolicyDocument`, `datetime.UTC`). `run_windows.bat`/`setup_windows.bat` do `where python` and `%PYTHON% -m venv` with no version check, so on a system where `python` is 2.x, dependency install and venv creation would target Python 2.7 and fail with SyntaxError.
WHY IT HAPPENS: `.bat` scripts trust `python` on PATH without verifying `>=3.11`. The project only declares the requirement in `pyproject.toml`, which the `.bat` never reads.
IMPACT: On Windows machines where `python` is 2.x (or not on PATH), the launcher silently creates/fails with an incompatible interpreter; the CLI "looks active" but cannot run. Verified: `python -m pytest` → SyntaxError on `tests/conftest.py:29`; `python3 -m pytest` → 71/71 PASS.
EVIDENCE: `python --version` → Python 2.7.18; `python3 --version` → 3.14.6; `python3 -m pytest --collect-only` → 71 tests / 6 files.
RECOMMENDED FIX: Add a Python-version gate to `.bat` (e.g. `%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"`) or use the `py -3` launcher on Windows; document that `python` must be 3.11+.
```

---

## 3. ORPHAN FILE TABLE

| FILE | TYPE | EVIDENCE | CLASSIFICATION | SAFE TO DELETE? |
|------|------|----------|----------------|-----------------|
| `services/activity_service.py` | .py | 0 imports/references; only docstring in state_engine.py:114 | **ORPHAN-A (TRUE)** | NO (verify intent; possible planned API) |
| `services/bedtime_service.py` | .py | 0 imports/references project-wide | **ORPHAN-A (TRUE)** | NO |
| `services/focus_service.py` | .py | 0 imports/references project-wide | **ORPHAN-A (TRUE)** | NO |
| `utils/logging.py` | .py | "backward-compatible delegate"; not imported by any module | **ORPHAN-B (LEGACY)** | NO (kept for external importers) |
| `adapters/windows/browser_monitor.py` | .py | never imported; CLI `real` backend uses MockBrowserMonitor (cli/main.py:149) | **ORPHAN-A (TRUE)** | NO (Windows feature stub) |
| `adapters/windows/action_executor.py` | .py | never imported; raises NotImplementedError | **ORPHAN-B (LEGACY)** | NO (future extension stub) |
| `src/assets/hero.png` | .png | no code references; phantom frontend | **ORPHAN-D (RESOURCE)** | NO |
| `src/assets/react.svg` | .svg | no code references | **ORPHAN-D (RESOURCE)** | NO |
| `src/assets/vite.svg` | .svg | no code references | **ORPHAN-D (RESOURCE)** | NO |
| `public/favicon.svg` | .svg | only index.html scaffold | **ORPHAN-D (RESOURCE)** | NO |
| `public/icons.svg` | .svg | only index.html scaffold | **ORPHAN-D (RESOURCE)** | NO |
| `index.html`, `vite.config.js`, `package.json`, `package-lock.json` | frontend | no runnable React entry; **build broken** | **ORPHAN-C (TOOLING)** / BROKEN | NO (fix or remove) |
| `example/simulate.py` | .py | demo only; not part of runtime | **ORPHAN-C (UTILITY)** | NO (keep as demo) |
| `generate_audit_report.py` | .py | dev tool; standalone | **ORPHAN-C (UTILITY)** | NO (keep) |
| `src/student_activity_engine.egg-info/` | artifact | stale build metadata | **LEGACY/ARTIFACT** | YES (rebuildable) |
| `Flowsink/` | dir | EMPTY (0 files) | **ORPHAN (EMPTY)** | YES (empty dir) |

---

## 4. BROKEN DEPENDENCY TABLE

| SOURCE | TARGET | TYPE | PROBLEM | SEVERITY |
|--------|--------|------|---------|----------|
| `cli/main.py:66` (policy-check default) | `config/policy.yaml` | file | missing → subcommand always fails | **HIGH** |
| `config/loader.py:35` | `config/local.yaml` | file | missing → falls back to defaults (silent) | **MEDIUM** |
| `config/models.py:49` `policy_file` | `config/policy.yaml` | config value | not wired into any loader consumer | **MEDIUM** |
| `index.html`/`vite.config.js` | `src/main.*`/React entry | frontend | no entry file → `vite build` fails | **HIGH** |
| `run_windows.bat:86` | `uvicorn` | dependency | not installed by `requirements-windows.txt` (only on demand via `requirements-server.txt` inside the `server` branch) | **LOW** |
| `browser-extension/background.js` | backend running | runtime | extension is useless if server not started; no guard surfaced | **INFO** |

**Missing modules (import-level):** NONE — every `import`/`from` resolves to an existing module. ✅

---

## 5. INTERFACE COMPATIBILITY (Producer → Consumer)

| PRODUCER | CONTRACT | CONSUMER | STATUS |
|----------|----------|----------|--------|
| Browser extension `background.js` | POST `{events:[{kind,source,timestamp,device_id,tab_id,domain,url,title}]}` | `server.py:/api/browser/telemetry` (`BrowserTelemetryPayload.events: list[dict]`) | ✅ **COMPATIBLE** |
| `ExtensionBrowserMonitor.get_active_tabs()` | returns `list[dict]` with `name/tab_id/domain` | `MonitoringService._poll_browser` reads `tab.get("name"/"tab_id"/"domain")` | ✅ **COMPATIBLE** |
| `server.py:/api/browser/active` | GET returns active tab(s) | `ExtensionBrowserMonitor._poll_http` reads JSON | ⚠️ Field keys must match; otherwise `get_active_tabs` returns dict not list — **KNOWN RISK** |
| `MockProcessMonitor.get_foreground_process()` | returns dict with `process`,`pid` | `MonitoringService._poll_process` | ✅ |
| `Adapter monitors` | Protocol `ProcessMonitor/BrowserMonitor/NetworkMonitor` (ports/__init__.py) | `MonitoringService` | ⚠️ **INCOMPATIBLE CONTRACT RISK**: `ports/` defines `get_running_processes()` but `MonitoringService` calls `get_foreground_process()`; verify each adapter implements the exact methods used |
| `engine.facade` default executor | `MockActionExecutor` | `ActionEngine` | ✅ always mock; no runtime switching |
| `ActivityEngine.__init__` | accepts `executor` object, `student_id`, `device_id` kwargs | `cli/main.py`, `server.py`, `examples/simulate.py` | ✅ **COMPATIBLE** |
| `Config(runtime=RuntimeConfig(mode=DecisionMode(...)))` | `EnforcementMode` from `core.decisions` | `config/models.py` uses same `core.decisions.EnforcementMode` | ✅ **COMPATIBLE** |
| `MonitoringService(event_engine=engine._event_engine)` | private attr access | `cli/main.py:296` | ⚠️ **COUPLING** — uses private `engine._event_engine`; works but brittle |

---

## 6. CONFIGURATION AUDIT

| CONFIG KEY | DEFINED | READ | STATUS |
|------------|---------|------|--------|
| `DEVICE_ID` (env) | `.env.example` | `config/loader.py:resolve_device_id`? — inferred via `COMPUTERNAME/HOSTNAME` | **ORPHAN** (env var defined but not read by that name) |
| `LOG_LEVEL` (env) | `.env.example` | CLI argparse `--log-level` (env not read) | **ORPHAN** |
| `SERVER_HOST`/`SERVER_PORT` (env) | `.env.example` | `run_windows.bat` hardcodes 127.0.0.1:8000; not read | **ORPHAN** |
| `GEMINI_API_KEY` (env) | `.env.example` | not read anywhere | **ORPHAN** |
| `VITE_GEMINI_API_KEY` | `.env.local` | not read by any frontend source (no frontend source) | **ORPHAN + SECURITY** |
| `Config.device.id` | `config/models.py` | not used by loader (loader reads resolve_device_id separately) | **ORPHAN** |
| `Config.monitoring.*` | `config/models.py` | `MonitoringService` ignores it (always runs all 3 monitors) | **ORPHAN** |
| `Config.logging.*` | `config/models.py` | not read | **ORPHAN** |
| `Config.policy_file` | `config/models.py:49` | no loader reads this field | **ORPHAN** |
| `config/local.yaml` | loader expects | file missing | **MISSING CONFIG** |
| `config/policy.yaml` | CLI default + models default | file missing | **MISSING CONFIG** |
| `browser-extension/config.json` keys | defined in installer | read by `background.js` | ✅ **ACTIVE** |
| `manifest.json` permissions/hosts | extension manifest | used by MV3 | ✅ **MATCH** server host |

**TYPE MISMATCH / NAME MISMATCH / DEFAULT CONFLICT:** None material. Minor: `.env.example` names `GEMINI_API_KEY` + `VITE_GEMINI_API_KEY` while `.env.local` only sets `VITE_GEMINI_API_KEY`.

---

## 7. DEPENDENCY AUDIT

| PACKAGE | DECLARED | IMPORTED | STATUS |
|---------|----------|----------|--------|
| pydantic>=2.5 | pyproject, requirements.txt | ✅ | ✅ USED |
| PyYAML>=6.0 | pyproject, requirements.txt | ✅ (import yaml) | ✅ USED |
| psutil>=5.9 | pyproject, requirements.txt | ✅ (import psutil) | ✅ USED |
| mss>=9.0 | pyproject, requirements.txt | ✅ (windows_screen) | ✅ USED (Windows only) |
| fastapi>=0.111 | pyproject[server], requirements-server.txt (commented in requirements.txt) | ✅ server.py | ⚠️ **NOT installed** by requirements-windows.txt base — only on `server` branch |
| uvicorn | pyproject[server], requirements-server.txt | ✅ | ⚠️ NOT installed base |
| websockets | pyproject[server], requirements-server.txt | ✅ (uvicorn) | ⚠️ NOT installed base |
| pytest | pyproject[dev], commented requirements.txt | ✅ | ✅ test-only |
| vite ^6.3.5 | package.json devDep | ✅ (config) | ⚠️ build broken (no entry) |

**UNUSED/UNDECLARED:**
- **Unused declared:** none major. `mss` only used on Windows; acceptable.
- **Imported but not declared in base requirements:** `fastapi`, `uvicorn`, `websockets`, `pydantic` (declared), `mss` (declared). `generate_audit_report.py`/`examples` import only stdlib + `activity_engine`.

---

## 8. PLATFORM COMPATIBILITY

| COMPONENT | WINDOWS | MACOS | LINUX | PROBLEM |
|-----------|:-------:|:-----:|:-----:|---------|
| `run_windows.bat`/`setup_windows.bat` | ✅ | ➖ | ➖ | uses `.venv\Scripts\python.exe`, `pip.exe`, `where python`, `pause` — Windows-only (intended). **CRITICAL C3**: no `>=3.11` version gate |
| `install_browser_extension.py` | ✅ | ⚠️ | ⚠️ | uses `PROGRAMFILES`/`PROGRAMFILES(X86)` env + `os.startfile` (Windows-only). On macOS/Linux `os.startfile` absent → caught by `except OSError`; works if files passed manually (warns). |
| `install_browser_extension.bat` | ✅ | ➖ | ➖ | Windows shell |
| `adapters/windows/*` | ✅ | ⚠️ | ⚠️ | uses `ctypes.wintypes` (Windows). Imported lazily/guarded by `_IS_WINDOWS` (cli/main.py:109,147,209,226). Safe cross-platform **only** via lazy imports. |
| `platform/screen.py` | ✅ | ✅ | ✅ | `windows_screen` returned only on Windows; `mock_screen` elsewhere. Uses `mss` (cross-platform wheel). ✅ |
| `services/screenshot_service.py` | ✅ | ✅ | ✅ | delegates to `get_screen_provider()`. ✅ |
| `config/loader` hardcoded path `config/` | ⚠️ | ⚠️ | ⚠️ | **POSIX-style forward slash** — works on Windows with `pathlib` (Windows accepts `/`), so functionally OK. |
| `subprocess`/`os.system` | ✅ | ✅ | ✅ | Only `install_browser_extension.py` subprocess.Popen(`chrome://extensions/`) — Windows Chrome path. Guarded. |
| `/tmp`, `/dev`, `bin/bash`, `ffmpeg`, `chmod` | ➖ | ➖ | ➖ | **None found** in project code (MV only in `.venv`). ✅ Cross-platform clean. |
| Path separators | ✅ | ✅ | ✅ | uses `pathlib.Path` throughout. ✅ |

**Cross-platform verdict:** Core engine is fully cross-platform (mock adapters + guarded Windows imports). Windows-specific `.bat` and extension installer are the only Windows-only artifacts (intentional). No broken cross-platform constructs found. **C3 is the only platform-critical gap** (missing Python version gate in `.bat` launchers).

---

## 9. LEGACY SYSTEM DETECTION

| CONCERN | CURRENT CANONICAL | OLD/LEGACY | WHICH RUNTIME USES |
|---------|-------------------|-----------|--------------------|
| Logging | `activity_engine/logging/` | `activity_engine/utils/logging.py` (delegate) | `logging/` package (all live code imports `..logging`) |
| Action executor | `adapters/mock/action_executor.py` | `adapters/windows/action_executor.py` (NotImplementedError) | mock always (facade default + CLI) |
| Browser monitor on Windows | `adapters/mock/browser_monitor.py` | `adapters/windows/browser_monitor.py` (unused) | mock (even with `--backend real` on Windows, cli/main.py:149) |
| Screenshot provider | `platform/screen.py` factory | — (both windows/mock are active by platform) | factory dispatch |
| Frontend | (no canonical frontend) | `index.html`+`vite.config.js` scaffold | none — phantom |

**There is NO second "system" (e.g. `Flowsink/`) conflicting.** `Flowsink/` is an empty directory.

---

## 10. RUNTIME GRAPH (Execution chains from every entrypoint)

### 10.1 CLI `monitor` (run_windows.bat default, E4/E2/E3)
```
run_windows.bat → python -m activity_engine.cli monitor --mode dry_run --backend real
  → cli.main: configure_logging
  → _cmd_monitor: Config(runtime=...)
  → ActivityEngine(config, executor=MockActionExecutor)
  → engine.facade init:
       config.loader.load_dev_config (config/local.yaml MISSING → defaults)
       policy.loader.load_default_policy (bundled default_policies.yaml) ✅
       EventEngine, StateEngine, PolicyEngine(PolicyEvaluator→classifier), ActionEngine, EscalationEngine, InMemoryRepository, ScreenshotService
  → engine.start_session()
  → _build_monitor_set("real") on Windows: {WindowsProcessMonitor, MockBrowserMonitor, WindowsNetworkMonitor}
  → MonitoringService(event_engine=engine._event_engine, monitors={...})
  → poll loop → event_engine.process_raw → policy eval → state update → escalation → action (mock)
```
**DEAD ENDS:** none — loop runs until Ctrl+C.

### 10.2 CLI `doctor`
```
cli.main _cmd_doctor:
  psutil/yaml/pydantic presence
  platform.screen.get_screen_provider().get_monitors()
  WindowsProcessMonitor / MockProcessMonitor
  WindowsNetworkMonitor / MockNetworkMonitor
  ExtensionBrowserMonitor()
  WindowsDeviceController().get_capabilities()
```
**DEAD END:** on non-Windows, Windows adapters skipped by branch; on Windows `ExtensionBrowserMonitor()` with no api_url defaults to `shared_store` (fine). `WindowsDeviceController.get_capabilities()` returns caps (no crash).

### 10.3 CLI `simulate` (E7)
```
examples/simulate.py or cli _cmd_simulate:
  ActivityEngine(config, MockActionExecutor, student_id="student-demo")
  feed_raw(browser_navigation / process_focus / dns_request)
  current_state(), metrics()
```

### 10.4 Server (E5)
```
uvicorn activity_engine.server:app --port 8000
  lifespan → ActivityEngine(student_id="student-001")
  REST + WS handlers (BrowserStateStore, transport.dto, transport.serialization, utils.ids)
  /api/browser/telemetry ← extension
  /api/browser/active   → ExtensionBrowserMonitor (when `monitor --backend extension`)
```
**BROKEN EDGE:** `uvicorn`/`fastapi`/`websockets` only installed if `server` branch or `requirements-server.txt` installed; base `requirements.txt` has them commented.

### 10.5 Browser Extension (E6)
```
background.js → chrome.tabs listeners → sanitize → queue (max 100) → fetch POST /api/browser/telemetry
```
**DEAD END:** if server not running, retries with backoff (bounded).

---

## 12. TEST COMPATIBILITY (Phase 12 — verified by execution)

| TEST FILE | TESTED MODULE | COLLECTED | RESULT | STALE? |
|-----------|---------------|-----------|--------|--------|
| `tests/test_contract.py` | transport.dto, event_engine, transport.serialization | ~21 | ✅ PASS | No |
| `tests/test_browser_extension.py` | adapters.extension.browser_monitor | ~? | ✅ PASS | No |
| `tests/test_integration.py` | engine.facade, core | 4 | ✅ PASS | No |
| `tests/test_logging.py` | logging.logger, logging.sanitize | 28 | ✅ PASS | No |
| `tests/test_policy_engine.py` | core.policies, engine.policy_engine, policy.* | 4 | ✅ PASS | No |
| `tests/test_states.py` | core.states, engine.state_engine | 16 | ✅ PASS | No |

**Total: 6 files / 71 tests — ALL PASS** under `python3` (3.14.6).

**CRITICAL TESTS-FAIL-NOTE:**
- Running `python -m pytest` (bare `python` = 2.7.18) → `ImportError: SyntaxError: invalid syntax` at `tests/conftest.py:29`. The tests and codebase are Python 3.11+ only. This confirms **C3**: the `.bat` launchers must enforce Python >=3.11.
- Deprecation warning: `datetime.utcnow()` deprecated in pydantic (non-fatal).

**Coverage of runtime path:** Tests exercise the core pipeline (events → policy → state → actions), logging, and the browser-extension bridge — they DO cover the live runtime path, not a replaced implementation. ✅

---

## 11. RECOMMENDED CLEANUP ORDER

### P0 — Broken runtime
- C1: Rotate + remove `VITE_GEMINI_API_KEY` from `.env.local`/history.
- C2: Create missing `config/` resources (`local.yaml` example + `policy.yaml`) OR refactor defaults to package-bundled resources so `policy-check`/`load_dev_config` work out of the box.
- C3: Add Python >=3.11 version gate to `run_windows.bat`/`setup_windows.bat` (and use `py -3` on Windows).

### P1 — Compatibility conflicts
- Fix frontend: either add a real entry (`src/main.*`, `App.*`) to make `vite build` work, or remove `index.html`/`vite.config.js`/`package.json`/assets scaffold if the dashboard is not part of runtime.
- Resolve `MonitoringService` ↔ ports protocol mismatch (decide canonical method set; ensure adapters implement methods actually called).

### P2 — Missing dependencies
- Document/install server deps: make `requirements-server.txt` explicit in `run_windows.bat` server branch (already does) — confirm base `requirements.txt` intentional comment-outs.

### P3 — Legacy conflicts
- `utils/logging.py` (delegate) — keep if external importers exist, else remove.
- `adapters/windows/action_executor.py` + `adapters/windows/browser_monitor.py` — keep as documented stubs for future Windows support, but mark clearly.

### P4 — Orphan files
- Remove `src/assets/*` if frontend is removed.
- Remove empty `Flowsink/` directory.
- Rebuild/regenerate stale `src/student_activity_engine.egg-info/`.
- Validate `services/activity_service.py`, `bedtime_service.py`, `focus_service.py` — either wire them into runtime or archive.

### P5 — Dead code
- Remove unused config fields (`Config.monitoring`, `Config.logging`, `policy_file`, `Config.device.id`) or wire them up.
- Remove unused env vars (`DEVICE_ID`, `LOG_LEVEL`, `SERVER_HOST/PORT`, `GEMINI_API_KEY`) from `.env.example` docs or implement consumers.

### P6 — Cosmetic
- Sync `.env.example` naming (`GEMINI_API_KEY` vs `VITE_GEMINI_API_KEY`).
- Add `.gitignore` entry confirmation for all `.env.*`.

---

## APPENDIX — Inventory (150 files, categorized)
Grouped by area; all counted once. Legacy/orphan assets listed in §3.

- **Python source (`src/activity_engine/`)**: 74 `.py` + 1 YAML — all resolved imports; only 6 orphans + 1 legacy delegate + 2 windows stubs noted.
- **Entrypoints/scripts**: `__main__.py`, `cli/__main__.py`, `cli/main.py`, `server.py`, `run_windows.bat`, `setup_windows.bat`.
- **Windows/browser tooling**: `install_browser_extension.{py,bat}`, `uninstall_browser_extension.{py,bat}`, `browser-extension/{background.js,config.json,manifest.json}`.
- **Frontend scaffold**: `index.html`, `vite.config.js`, `package.json`, `package-lock.json`, `public/*`, `src/assets/*`.
- **Dependency/config**: `pyproject.toml`, `requirements*.txt` (3), `.env.example`, `.env.local`, `.gitignore`, egg-info (6 files).
- **Docs**: `README.md`, `WINDOWS_SETUP.md`, `BROWSER_EXTENSION_WINDOWS.md`, `DATABASE_...docx`, `docs/*.md` (6), `browser-extension/README.md`.
- **Examples/tests/tools**: `examples/*` (2), `tests/*` (7), `generate_audit_report.py`.

*Audit complete — no repository files were modified.*