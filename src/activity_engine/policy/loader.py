"""Policy loading from YAML with validation."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from ..core.errors import ConfigurationError
from ..core.policies import PolicyDocument


def load_default_policy() -> PolicyDocument:
    """Load the bundled default policy document."""
    raw = resources.read_text(__package__, "default_policies.yaml")
    return PolicyLoader.from_dict(yaml.safe_load(raw) or {})


class PolicyLoader:
    """Loads :class:`PolicyDocument` from a YAML file or dict."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> PolicyDocument:
        if not self.path.exists():
            raise ConfigurationError(f"Policy file not found: {self.path}")
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Invalid policy YAML in {self.path}: {exc}") from exc
        return self.from_dict(raw)

    @staticmethod
    def from_dict(raw: dict) -> PolicyDocument:
        try:
            return PolicyDocument.model_validate(raw)
        except Exception as exc:
            raise ConfigurationError(f"Invalid policy document: {exc}") from exc