"""Windows screen provider backed by ``mss``.

``mss`` is a cross-platform screen-capture library; on Windows it uses the
native GDI API and requires no extra system dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .screen import ScreenInfo, ScreenProvider, make_screenshot_filename

class WindowsScreenProvider(ScreenProvider):
    """Real screen capture for Windows using ``mss``."""

    def __init__(self) -> None:
        import mss

        self._sct = mss.mss()

    def get_monitors(self) -> list[ScreenInfo]:
        return [
            ScreenInfo(
                left=int(m["left"]),
                top=int(m["top"]),
                width=int(m["width"]),
                height=int(m["height"]),
            )
            for m in self._sct.monitors
        ]

    def capture(self, monitor_index: int = 0) -> Any:
        """Capture one monitor (0 = all monitors combined)."""
        return self._sct.grab(self._sct.monitors[monitor_index])

    def save_screenshot(
        self,
        directory: Path,
        session_id: str | None = None,
        prefix: str = "screenshot",
    ) -> Path | None:
        """Capture the primary monitor and save as PNG."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            filename = make_screenshot_filename(prefix=prefix, session_id=session_id)
            path = directory / filename
            # mss grabs are raw BGRA buffers; use mss.tools to write PNG.
            import mss.tools

            shot = self.capture(0)
            mss.tools.to_png(shot.rgb, shot.size, output=str(path))
            return path
        except Exception:
            return None