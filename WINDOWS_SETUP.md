# Windows Setup Guide

This guide explains how to install and run the Flowsink Activity Engine on **Windows 10/11**.

The project is developed on macOS but the engine, CLI, screen capture, process
monitoring and network monitoring are all Windows-compatible.

---

## 1. Install Python

1. Download Python 3.11 or newer from <https://www.python.org/downloads/>
2. Run the installer
3. **IMPORTANT:** Tick **"Add Python to PATH"** at the bottom of the first screen
4. Click **Install Now**

Verify from a new terminal:

```cmd
python --version
```

Expected output: `Python 3.11.x` or newer.

---

## 2. Clone / copy the project

```cmd
git clone <repository-url>
cd Flowsink
```

Or copy the project folder to your Windows machine.

---

## 3. One-time setup

Double-click **`setup_windows.bat`**, or run from a terminal:

```cmd
setup_windows.bat
```

This script:

1. Finds Python
2. Creates `.venv\` (a virtual environment)
3. Installs all dependencies from `requirements-windows.txt`

---

## 4. Run the application

Double-click **`run_windows.bat`**, or run from a terminal:

```cmd
run_windows.bat
```

By default this:

1. Runs `activity-engine doctor` (system health check)
2. Starts live monitoring in `dry_run` mode with the **real Windows backend**

### Useful commands

```cmd
:: Run doctor only (system diagnostics)
run_windows.bat doctor

:: Run doctor with JSON output
run_windows.bat doctor --json

:: Run monitoring in dry-run (safe; no enforcement)
run_windows.bat monitor --mode dry_run --backend real

:: Run monitoring in audit-only (records actions but does not execute)
run_windows.bat monitor --mode audit_only --backend real

:: Replay simulated events (no real monitoring)
run_windows.bat simulate --events 20

:: Validate a policy file
run_windows.bat policy-check examples/policy.yaml
```

### Alternative: start the FastAPI backend + dashboard

Install server dependencies (one time):

```cmd
.venv\Scripts\pip install -r requirements-server.txt
```

Start the API:

```cmd
.venv\Scripts\python -m uvicorn src.activity_engine.server:app --host 127.0.0.1 --port 8000
```

Open the dashboard at <http://127.0.0.1:8000> (or the static `index.html`).

---

## 5. What runs on Windows

| Component        | Implementation                                                                 |
|------------------|--------------------------------------------------------------------------------|
| Process monitor  | `WindowsProcessMonitor` — Win32 API (`user32.dll`) + `psutil`                   |
| Foreground app   | Active window → process → application name via Win32 API                       |
| Screen capture   | `WindowsScreenProvider` — `mss` (native GDI, no extra system deps)             |
| Network monitor  | `WindowsNetworkMonitor` — `psutil.net_connections()` (no admin rights needed)  |
| Browser monitor  | Not implemented in Phase 1 — mock stub used (logs a warning)                   |
| Action executor  | Not implemented in Phase 1 — mock executor used (dry-run only)                 |

**Note:** `activity-engine monitor --mode enforce` is not safe yet because the
Windows action executor (close apps, block domains, restricted mode) is a
Phase-1 stub. Use `dry_run` or `audit_only` for now.

---

## 6. Configuration

Copy the template:

```cmd
copy .env.example .env
```

Then edit `.env` for optional settings. All values are optional; defaults work
out of the box.

If you need a custom device id, set:

```txt
DEVICE_ID=my-pc-name
```

or leave `DEVICE_ID=auto` to use the Windows `COMPUTERNAME`.

---

## 7. Paths

| Item            | Location (Windows)                                    |
|-----------------|-------------------------------------------------------|
| Screenshots     | `%LOCALAPPDATA%\Flowsink\screenshots\`                |
| Virtual env     | `.venv\` (inside the project)                         |

No hard-coded `/Users/...`, `/tmp/...` or `/Applications/...` paths are used.

---

## 8. Troubleshooting

### `python` is not recognized

- Reinstall Python and tick **"Add Python to PATH"**
- Or use the full path, e.g. `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`

### `setup_windows.bat` fails during dependency install

Run these commands manually:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements-windows.txt
```

### `activity-engine doctor` reports FAIL for `screen_capture` or `process_monitor`

- Make sure you ran `setup_windows.bat` (dependencies installed)
- Screen capture on Windows may require a physical desktop session
  (not an RDP-disconnected session)
- Process monitor requires no special privileges for the active user

### `monitor --backend real` crashes with `window_title` / `GetForegroundWindow`

- This is a known limitation when running from a non-interactive session
  (for example a service or SSH session). Run it from a normal desktop session.

### Dashboard cannot reach the backend

- Check the API is running on `127.0.0.1:8000`
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` (Vite) and
  `http://localhost:3000`
- If you serve the static `index.html` from another port, add that origin in
  `src/activity_engine/server.py` → `CORSMiddleware`

---

## 9. Tests

```cmd
.venv\Scripts\pip install pytest pytest-asyncio
.venv\Scripts\python -m pytest tests/
```

---

## 10. Windows runtime verification status

Static audit was performed from macOS. **Actual Windows runtime verification was
NOT executed** in this environment. The startup scripts and adapter selection
are designed to be exercised on a real Windows machine by following this guide.