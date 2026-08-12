"""Windows Action Executor stub (LEGACY).

[LEGACY] Phase 1 stub — real Windows action execution (Win32 API app close,
registry blocks, restricted-mode toggles) is not yet implemented.

This stub documents the :class:`~activity_engine.ports.ActionExecutor` contract
and raises :class:`NotImplementedError` on every method so that any accidental
use fails fast rather than silently doing nothing.

The canonical / tested path is :class:`~activity_engine.adapters.mock.action_executor.MockActionExecutor`,
which is what the engine wires by default on every platform.
"""

from __future__ import annotations

from typing import Any

class WindowsActionExecutor:
    """Stub for Windows action executor."""

    async def warn(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Windows action execution is a future extension. Use MockActionExecutor.")

    async def redirect(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Not implemented in Phase 1")

    async def close_application(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Not implemented in Phase 1")

    async def block_domain(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Not implemented in Phase 1")

    async def enable_restricted_mode(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Not implemented in Phase 1")

    async def disable_restricted_mode(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Not implemented in Phase 1")