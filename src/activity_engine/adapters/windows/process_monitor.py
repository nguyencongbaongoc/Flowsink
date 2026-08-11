"""Windows process monitor using psutil.

This is a real implementation that can run on Windows. It uses psutil to
enumerate processes and detect the foreground window.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
from typing import Any

import psutil

class WindowsProcessMonitor:
    """Real Windows process monitor using psutil and Win32 API."""

    def __init__(self) -> None:
        self._running = False
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def get_running_processes(self) -> list[dict[str, Any]]:
        """Return a list of running processes."""
        procs = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                procs.append(
                    {
                        "name": proc.info.get("name"),
                        "process": os.path.basename(proc.info.get("exe") or ""),
                        "pid": proc.info.get("pid"),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return procs

    async def get_foreground_process(self) -> dict[str, Any] | None:
        """Return the foreground window's process."""
        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = ctypes.wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            proc = psutil.Process(pid.value)
            return {
                "name": proc.name(),
                "process": os.path.basename(proc.exe() or ""),
                "pid": proc.pid,
                "window_title": self._get_window_title(hwnd),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def _get_window_title(self, hwnd: int) -> str:
        length = self._user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value