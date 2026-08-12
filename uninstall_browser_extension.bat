@echo off
REM ============================================================
REM  Flowsink Browser Monitor - Windows uninstaller
REM  Double-click to remove the extension from Chrome.
REM ============================================================
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" uninstall_browser_extension.py %*
) else (
    python uninstall_browser_extension.py %*
)

set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo [DONE] Exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%