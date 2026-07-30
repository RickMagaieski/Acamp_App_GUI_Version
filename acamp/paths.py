"""Runtime paths shared by source and packaged application builds."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .runtime_data import (
    RuntimeDataConfigStore,
    missing_required_files,
)


def application_root() -> Path:
    """Return the source root or the directory containing the executable."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_resource_root() -> Path:
    """Return the read-only root used for packaged application resources."""

    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", application_root())
        return Path(bundle_root).resolve()
    return application_root()


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Centralized writable-data and read-only resource locations."""

    root: Path
    resources_root: Path | None = None
    packaged: bool = False
    managed_root: Path | None = None
    data_mode: str = "source"
    configuration_valid: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).resolve())
        resource_root = self.resources_root or self.root
        object.__setattr__(
            self,
            "resources_root",
            Path(resource_root).resolve(),
        )
        managed_root = self.managed_root or self.root
        object.__setattr__(
            self,
            "managed_root",
            Path(managed_root).resolve(),
        )

    @classmethod
    def from_runtime(cls) -> "ApplicationPaths":
        root = application_root()
        if getattr(sys, "frozen", False):
            managed_root = (root / "user_data").resolve()
            selection = RuntimeDataConfigStore(managed_root).load()
            if selection is None:
                data_root = managed_root
                mode = "unconfigured"
                configuration_valid = False
            else:
                data_root = selection.root
                mode = selection.mode
                configuration_valid = True
            return cls(
                data_root,
                resources_root=bundled_resource_root(),
                packaged=True,
                managed_root=managed_root,
                data_mode=mode,
                configuration_valid=configuration_valid,
            )
        return cls(root, resources_root=bundled_resource_root())

    def ensure_private_data_directory(self) -> bool:
        """Create the external packaged data directory when possible."""

        if not self.packaged:
            return True
        try:
            self.managed_root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
        return True

    @property
    def data_config_store(self) -> RuntimeDataConfigStore:
        return RuntimeDataConfigStore(self.managed_root)

    @property
    def missing_required_data_files(self) -> tuple[str, ...]:
        return missing_required_files(self.root)

    @property
    def needs_data_setup(self) -> bool:
        return (
            self.packaged
            and (
                not self.configuration_valid
                or bool(self.missing_required_data_files)
            )
        )

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
        return self.resources_root / "assets"
