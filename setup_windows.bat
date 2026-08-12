@echo off
REM ============================================================
REM  Flowsink Activity Engine - one-time Windows setup
REM  Run once after cloning:
REM      setup_windows.bat
REM
REM  Creates a virtual environment and installs dependencies.
REM  When finished, use run_windows.bat to start the engine.
REM ============================================================
setlocal

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYTHON=python"

echo.
echo ============================================================
echo  Flowsink Activity Engine - Windows Setup
echo ============================================================
echo.

REM 1. Locate Python
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

echo [1/3] Python found: 
%PYTHON% --version

REM 2. Create virtual environment
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo.
    echo [2/3] Creating virtual environment...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo.
    echo [2/3] Virtual environment already exists - skipping.
)

set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

REM 3. Install dependencies
echo.
echo [3/3] Installing dependencies...
"%PIP_EXE%" install --upgrade pip
"%PIP_EXE%" install -r requirements-windows.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo ok > "%VENV_DIR%\.deps_installed"

echo.
echo ============================================================
echo  Setup complete!
echo.
echo  Next steps:
echo    1. Double-click  run_windows.bat
echo       or run       run_windows.bat doctor
echo ============================================================
echo.
pause