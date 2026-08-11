"""Configuration loader with fail-fast validation."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from ..core.errors import ConfigurationError
from .models import Config

class ConfigLoader:
    """Loads and validates configuration from a YAML file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> Config:
        """Load configuration. Raises ConfigurationError on invalid input."""
        if not self.path.exists():
            raise ConfigurationError(f"Config file not found: {self.path}")
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Invalid YAML in {self.path}: {exc}") from exc
        try:
            return Config.model_validate(raw)
        except Exception as exc:  # pydantic ValidationError
            raise ConfigurationError(f"Invalid configuration in {self.path}: {exc}") from exc

def load_dev_config() -> Config:
    """Load config/local.yaml if present, otherwise sensible defaults."""
    local = Path("config/local.yaml")
    if local.exists():
        return ConfigLoader(local).load()
    return Config()

def resolve_device_id(config: Config) -> str:
    """Resolve 'auto' device id to hostname."""
    if config.device.id == "auto":
        return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown-device"
    return config.device.id