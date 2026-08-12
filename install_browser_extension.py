"""Flowsink Browser Monitor — Windows installer (single file).

Generates/validates the browser-extension folder, writes the device
identity into ``config.json``, detects an installed Chromium browser and
opens the extension management page for the one manual step Chrome
requires: **Load unpacked**.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
EXTENSION_DIR = PROJECT_ROOT / "browser-extension"
CONFIG_PATH = EXTENSION_DIR / "config.json"
REQUIRED_FILES = ["manifest.json", "background.js", "config.json"]

CHROME_CANDIDATES = [
    Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
]


def _device_id() -> str:
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown-device"


def _resolve_default_browser() -> Path | None:
    for candidate in CHROME_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _log(msg: str) -> None:
    print(f"[install] {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the Flowsink Browser Monitor extension")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser extensions page")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="Backend base URL")
    args = parser.parse_args()

    _log(f"Extension directory: {EXTENSION_DIR}")

    # 1. Validate required files exist.
    missing = [name for name in REQUIRED_FILES if not (EXTENSION_DIR / name).exists()]
    if missing:
        _log(f"[ERROR] Missing extension files: {', '.join(missing)}")
        _log("Reinstall the project or restore the browser-extension/ folder.")
        return 1

    # 2. Write config.json with the real device id + backend URL.
    try:
        existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    except json.JSONDecodeError:
        existing = {}
    config = {
        "api_base_url": args.api_url,
        "device_id": _device_id(),
        "max_queue": existing.get("max_queue", 100),
        "retry_base_ms": existing.get("retry_base_ms", 1000),
        "retry_max_ms": existing.get("retry_max_ms", 60000),
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    _log(f"config.json written (device_id={config['device_id']}, api={config['api_base_url']})")

    # 3. Locate a Chromium browser.
    browser = _resolve_default_browser()
    if browser is None:
        _log("[WARN] No Chrome/Edge detected. Load the extension manually from chrome://extensions/.")
        if not args.no_open:
            try:
                if sys.platform.startswith("win"):
                    os.startfile("chrome://extensions/")  # type: ignore[attr-defined]
            except OSError:
                pass
        return 0

    _log(f"Detected browser: {browser}")

    # 4. Open the extensions page for the manual 'Load unpacked' step.
    if not args.no_open:
        _log("Opening chrome://extensions/ — please enable 'Developer mode' (top-right),")
        _log(f"click 'Load unpacked' and select the folder:\n    {EXTENSION_DIR}")
        try:
            subprocess.Popen([str(browser), "chrome://extensions/"], close_fds=True)
        except OSError as exc:
            _log(f"[WARN] Could not open browser automatically: {exc}")

    _log("Done. Next steps:")
    _log("  1. In chrome://extensions/ enable Developer mode")
    _log(f"  2. Click 'Load unpacked' and select {EXTENSION_DIR}")
    _log("  3. Start the backend server, then browse any website")
    return 0


if __name__ == "__main__":
    sys.exit(main())