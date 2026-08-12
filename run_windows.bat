@echo off
REM ============================================================
REM  Flowsink Activity Engine - Windows launcher
REM  Double-click or run from cmd:
REM      run_windows.bat
REM
REM  Optional arguments are passed through to activity-engine.
REM  Examples:
REM      run_windows.bat doctor
REM      run_windows.bat monitor --mode dry_run --backend real
REM      run_windows.bat simulate --events 20
REM ============================================================
setlocal enabledelayedexpansion

REM Switch to this script's directory so paths always resolve.
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYTHON=python"

REM ------------------------------------------------------------
REM 1. Locate Python
REM ------------------------------------------------------------
where %PYTHON% >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo and make sure you tick "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 2. Verify Python version is 3.11 or newer (CRITICAL)
REM    The engine requires Python >= 3.11.  A bare `python` may
REM    resolve to Python 2.x on some systems, which would break
REM    venv creation, dependency install and the application.
REM ------------------------------------------------------------
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.11 or newer is required.
    for /f "delims=" %%v in ('%PYTHON% -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "DETECTED=%%v"
    if defined DETECTED (
        echo Detected: !DETECTED!
    ) else (
        echo Detected: unknown
    )
    echo.
    echo Please install Python 3.11+ and retry.
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 3. Create virtual environment if missing
REM ------------------------------------------------------------
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

REM ------------------------------------------------------------
REM 4. Install dependencies if missing (marker file based)
REM ------------------------------------------------------------
if not exist "%VENV_DIR%\.deps_installed" (
    echo [SETUP] Installing dependencies...
    "%PIP_EXE%" install -r requirements-windows.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        echo Try running:  "%PIP_EXE%" install -r requirements-windows.txt
        pause
        exit /b 1
    )
    echo ok > "%VENV_DIR%\.deps_installed"
)

REM ------------------------------------------------------------
REM 5. Make the src/ package importable
REM ------------------------------------------------------------
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

REM ------------------------------------------------------------
REM 6. Run the engine
REM ------------------------------------------------------------
if /I "%~1"=="server" (
    echo [RUN] Starting FastAPI server on http://127.0.0.1:8000...
    if not exist "%VENV_DIR%\.server_deps_installed" (
        echo [SETUP] Installing server dependencies...
        "%PIP_EXE%" install -r requirements-server.txt
        if errorlevel 1 (
            echo [ERROR] Server dependency installation failed.
            pause
            exit /b 1
        )
        echo ok > "%VENV_DIR%\.server_deps_installed"
    )
    "%PYTHON_EXE%" -m uvicorn activity_engine.server:app --host 127.0.0.1 --port 8000
) else if "%~1"=="" (
    echo [RUN] No command given - starting doctor then monitor.
    "%PYTHON_EXE%" -m activity_engine.cli doctor
    echo.
    echo [RUN] Starting monitoring (dry_run, real backend)...
    echo       Press Ctrl+C to stop.
    "%PYTHON_EXE%" -m activity_engine.cli monitor --mode dry_run --backend real
) else (
    "%PYTHON_EXE%" -m activity_engine.cli %*
)

set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo [DONE] Exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%