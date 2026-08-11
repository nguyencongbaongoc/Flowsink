"""Device domain model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class Device(BaseModel):
    """A monitored student device."""

    model_config = ConfigDict(frozen=True)

    device_id: str
    machine_name: str | None = None
    platform: str | None = None
    os_version: str | None = None

class DeviceCapabilities(BaseModel):
    """Capabilities the device exposes to the engine."""

    model_config = ConfigDict(frozen=True)

    process_monitoring: bool = True
    browser_monitoring: bool = False
    network_monitoring: bool = False
    action_executor: bool = False
    device_controller: bool = False
    restricted_mode: bool = False