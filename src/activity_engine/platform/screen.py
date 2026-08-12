"""Screen provider abstraction.

This module defines the :class:`ScreenProvider` port used by the activity engine
to capture screenshots and query screen geometry in a cross-platform way.

Windows runtime uses :mod:`activity_engine.platform.windows_screen` which is
backed by ``mss``.  macOS and other platforms fall back to a mock provider so
the application never crashes when screen capture is unavailable.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScreenInfo:
    """Geometry of one monitor."""

    left: int
    top: int
    width: int
    height: int

    @property
    def resolution(self) -> tuple[int, int]:
        return (self.width, self.height)


class ScreenProvider(ABC):
    """Port that must be implemented by every platform screen adapter."""

    @abstractmethod
    def get_monitors(self) -> list[ScreenInfo]:
        """Return geometry for every connected monitor."""

    @abstractmethod
    def capture(self, monitor_index: int = 0) -> Any:
        """Capture one monitor as a raw image object (PIL-compatible)."""

    @abstractmethod
    def save_screenshot(
        self,
        directory: Path,
        session_id: str | None = None,
        prefix: str = "screenshot",
    ) -> Path | None:
        """Capture the screen and save it to ``directory``.

        Returns the saved file path, or ``None`` when capture is unavailable.
        """


def create_screen_provider() -> ScreenProvider:
    """Pick the correct provider for the current platform."""
    if sys.platform.startswith("win"):
        from .windows_screen import WindowsScreenProvider

        return WindowsScreenProvider()
    from .mock_screen import MockScreenProvider

    return MockScreenProvider()


_provider: ScreenProvider | None = None


def get_screen_provider() -> ScreenProvider:
    """Return a cached :class:`ScreenProvider` instance."""
    global _provider
    if _provider is None:
        _provider = create_screen_provider()
    return _provider


def default_screenshot_dir() -> Path:
    """Return the cross-platform default screenshot directory.

    Windows: ``%LOCALAPPDATA%/Flowsink/screenshots``
    macOS/Linux: ``~/Flowsink/screenshots``
    """
    if sys.platform.startswith("win"):
        local = Path.home() / "AppData" / "Local" / "Flowsink"
    else:
        local = Path.home() / "Flowsink"
    return local / "screenshots"


def make_screenshot_filename(
    prefix: str = "screenshot",
    session_id: str | None = None,
    timestamp: datetime | None = None,
) -> str:
    """Build a cross-platform safe screenshot filename."""
    ts = (timestamp or datetime.now(UTC)).strftime("%Y%m%d_%H%M%S_%f")
    sid = f"_{session_id}" if session_id else ""
    return f"{prefix}{sid}_{ts}.png"