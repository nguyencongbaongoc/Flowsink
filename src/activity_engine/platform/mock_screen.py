"""Mock screen provider used on platforms without screen capture support.

On macOS the project does not depend on Quartz/AppKit, so screen capture is
reported as unavailable rather than crashing the application.  This keeps the
core monitoring loop functional on every platform.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .screen import ScreenInfo, ScreenProvider

class MockScreenProvider(ScreenProvider):
    """Fallback provider that reports a fake single monitor and no capture."""

    def get_monitors(self) -> list[ScreenInfo]:
        return [ScreenInfo(left=0, top=0, width=1920, height=1080)]

    def capture(self, monitor_index: int = 0) -> Any:
        raise NotImplementedError("Screen capture is not available on this platform.")

    def save_screenshot(
        self,
        directory: Path,
        session_id: str | None = None,
        prefix: str = "screenshot",
    ) -> Path | None:
        return None