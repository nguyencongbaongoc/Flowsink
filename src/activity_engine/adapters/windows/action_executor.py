"""Windows Action Executor stub.

Phase 1: Real Windows action execution (Win32 API app close, registry blocks)
is not yet implemented. This stub documents the contract and raises
NotImplementedError if used.
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