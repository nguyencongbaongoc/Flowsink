"""Platform abstraction layer — picks the correct platform-specific adapter."""

from __future__ import annotations

from .screen import ScreenProvider, create_screen_provider, get_screen_provider

__all__ = ["ScreenProvider", "create_screen_provider", "get_screen_provider"]