"""Windows screen provider backed by ``mss``.

``mss`` is a cross-platform screen-capture library; on Windows it uses the
native GDI API and requires no extra system dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..logging import get_logger
from .screen import ScreenInfo, ScreenProvider, make_screenshot_filename

logger = get_logger("activity_engine.platform.screen", component="SCREEN", event="INIT")

class WindowsScreenProvider(ScreenProvider):
    """Real screen capture for Windows using ``mss``."""

    def __init__(self) -> None:
        import mss

        self._sct = mss.mss()
        logger.info(
            "provider=WindowsScreenProvider backend=mss status=READY",
            event="INIT",
            component="SCREEN",
        )

    def get_monitors(self) -> list[ScreenInfo]:
        monitors = [
            ScreenInfo(
                left=int(m["left"]),
                top=int(m["top"]),
                width=int(m["width"]),
                height=int(m["height"]),
            )
            for m in self._sct.monitors
        ]
        logger.debug(
            "monitors=%d",
            len(monitors),
            event="DETECTED",
            component="SCREEN",
        )
        return monitors

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
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            logger.debug(
                "path=%s size=%dKB",
                path,
                size // 1024,
                event="SAVE",
                component="SCREEN",
            )
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "error_type=%s message=%s",
                exc.__class__.__name__,
                exc,
                event="ERROR",
                component="SCREEN",
            )
            return None
