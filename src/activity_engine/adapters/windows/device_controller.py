"""Windows Device Controller stub.

Phase 1: Real Windows device control (restricted mode, lock) is not yet
implemented. This stub documents the contract and raises
NotImplementedError if used.
"""

from __future__ import annotations

from ...domain.device import DeviceCapabilities

class WindowsDeviceController:
    """Stub for Windows device controller."""

    async def get_capabilities(self) -> DeviceCapabilities:
        return DeviceCapabilities(
            process_monitoring=True,
            browser_monitoring=False,
            network_monitoring=False,
            action_executor=False,
            device_controller=False,
            restricted_mode=False,
        )

    async def enable_restricted_mode(self) -> bool:
        raise NotImplementedError("Not implemented in Phase 1")

    async def disable_restricted_mode(self) -> bool:
        raise NotImplementedError("Not implemented in Phase 1")

    async def lock_device(self) -> bool:
        raise NotImplementedError("Not implemented in Phase 1")