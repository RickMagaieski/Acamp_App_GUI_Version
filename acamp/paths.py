"""Runtime paths shared by source and packaged application builds."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).resolve())
        resource_root = self.resources_root or self.root
        object.__setattr__(
            self,
            "resources_root",
            Path(resource_root).resolve(),
        )

    @classmethod
    def from_runtime(cls) -> "ApplicationPaths":
        root = application_root()
        if getattr(sys, "frozen", False):
            return cls(
                root / "user_data",
                resources_root=bundled_resource_root(),
                packaged=True,
            )
        return cls(root, resources_root=bundled_resource_root())

    def ensure_private_data_directory(self) -> bool:
        """Create the external packaged data directory when possible."""

        if not self.packaged:
            return True
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
        return True

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
