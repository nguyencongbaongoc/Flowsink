"""Windows Device Controller stub (LEGACY).

[LEGACY] Phase 1 stub — real Windows device control (restricted mode, lock)
is not yet implemented.

Only :meth:`get_capabilities` returns data (all capabilities ``False``
except process monitoring); the rest raise :class:`NotImplementedError`
so accidental use fails fast.  When real Windows device control is
implemented the ``*monitoring`` flags here should flip to ``True``.
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