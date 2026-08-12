"""Flowsink Browser Monitor — uninstaller helper.

Chrome extensions loaded via 'Load unpacked' cannot be removed from the
filesystem while Chrome is running. This script:
  1. Opens chrome://extensions/ so the user can click 'Remove'.
  2. Restores browser-extension/config.json to the default (identity removed).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
EXTENSION_DIR = PROJECT_ROOT / "browser-extension"
CONFIG_PATH = EXTENSION_DIR / "config.json"

CHROME_CANDIDATES = [
    Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
]

def _log(msg: str) -> None:
    print(f"[uninstall] {msg}")

def _resolve_default_browser() -> Path | None:
    for candidate in CHROME_CANDIDATES:
        if candidate.exists():
            return candidate
    return None

def main() -> int:
    # 1. Reset config.json to defaults (device id removed).
    if CONFIG_PATH.exists():
        try:
            CONFIG_PATH.write_text(
                json.dumps(
                    {
                        "api_base_url": "http://127.0.0.1:8000",
                        "device_id": "unknown-device",
                        "max_queue": 100,
                        "retry_base_ms": 1000,
                        "retry_max_ms": 60000,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            _log("config.json reset to defaults (no device identity).")
        except OSError as exc:
            _log(f"[WARN] Could not reset config.json: {exc}")

    # 2. Open the extensions page for manual removal.
    browser = _resolve_default_browser()
    if browser is not None:
        _log(f"Opening {browser.name} extensions page...")
        try:
            subprocess.Popen([str(browser), "chrome://extensions/"], close_fds=True)
        except OSError as exc:
            _log(f"[WARN] Could not open browser: {exc}")
    else:
        try:
            if sys.platform.startswith("win"):
                os.startfile("chrome://extensions/")  # type: ignore[attr-defined]
        except OSError:
            pass

    _log("Done. In chrome://extensions/ click 'Remove' on 'Flowsink Browser Monitor'.")
    _log("The extension folder is kept for future installs; delete it manually if not needed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())