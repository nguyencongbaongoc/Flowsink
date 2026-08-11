"""Configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..core.decisions import EnforcementMode

class MonitoringConfig(BaseModel):
    """Which monitors to enable."""

    model_config = ConfigDict(frozen=True)

    process: bool = True
    browser: bool = True
    network: bool = True

class LoggingConfig(BaseModel):
    """Logging settings."""

    model_config = ConfigDict(frozen=True)

    level: str = "INFO"
    structured: bool = True

class RuntimeConfig(BaseModel):
    """Runtime behavior."""

    model_config = ConfigDict(frozen=True)

    mode: EnforcementMode = EnforcementMode.DRY_RUN

class DeviceConfig(BaseModel):
    """Device identification."""

    model_config = ConfigDict(frozen=True)

    id: str = "auto"

class Config(BaseModel):
    """Top-level configuration."""

    model_config = ConfigDict(frozen=True)

    device: DeviceConfig = Field(default_factory=DeviceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    policy_file: str = "config/policy.yaml"