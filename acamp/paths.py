"""Runtime paths shared by source and future packaged application builds."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


def application_root() -> Path:
    """Return the directory containing runtime data and credentials."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Centralized locations for private data and optional runtime assets."""

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).resolve())

    @classmethod
    def from_runtime(cls) -> "ApplicationPaths":
        return cls(application_root())

    @property
    def participants_file(self) -> Path:
        return self.root / "participants.json"

    @property
    def inventory_file(self) -> Path:
        return self.root / "items.json"

    @property
    def teams_file(self) -> Path:
        return self.root / "teams.json"

    @property
    def client_secret_file(self) -> Path:
        return self.root / "client_secret.json"

    @property
    def token_file(self) -> Path:
        return self.root / "token.json"

    @property
    def assets_directory(self) -> Path:
        return self.root / "assets"
