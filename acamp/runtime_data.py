"""Safe packaged-runtime data selection and explicit file import."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


REQUIRED_DATA_FILES = (
    "participants.json",
    "items.json",
    "teams.json",
)
OPTIONAL_DATA_FILES = (
    "client_secret.json",
    "token.json",
)
ALLOWED_RUNTIME_FILES = REQUIRED_DATA_FILES + OPTIONAL_DATA_FILES
DATA_LOCATION_CONFIG = "data_location.json"


@dataclass(frozen=True, slots=True)
class RuntimeDataSelection:
    mode: str
    root: Path


@dataclass(frozen=True, slots=True)
class RuntimeImportResult:
    copied: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return bool(self.copied) and not self.failed


class RuntimeDataConfigStore:
    """Persist only the packaged data-location strategy."""

    def __init__(self, managed_root: Path):
        self.managed_root = Path(managed_root).resolve()

    @property
    def path(self) -> Path:
        return self.managed_root / DATA_LOCATION_CONFIG

    def load(self) -> RuntimeDataSelection | None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or payload.get("version") != 1:
            return None

        mode = payload.get("mode")
        if mode == "managed":
            return RuntimeDataSelection(mode, self.managed_root)
        if mode != "external":
            return None

        configured_path = payload.get("path")
        if not isinstance(configured_path, str) or not configured_path.strip():
            return None
        root = Path(configured_path).expanduser()
        if not root.is_absolute():
            return None
        return RuntimeDataSelection(mode, root.resolve())

    def save_managed(self) -> bool:
        return self._write({"version": 1, "mode": "managed"})

    def save_external(self, root: Path) -> bool:
        selected_root = Path(root).resolve()
        if not selected_root.is_dir():
            return False
        return self._write({
            "version": 1,
            "mode": "external",
            "path": str(selected_root),
        })

    def _write(self, payload: dict[str, object]) -> bool:
        temporary_path: Path | None = None
        try:
            self.managed_root.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.managed_root,
                prefix=f".{DATA_LOCATION_CONFIG}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(payload, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return False
        return True


def missing_required_files(root: Path) -> tuple[str, ...]:
    data_root = Path(root)
    return tuple(
        name
        for name in REQUIRED_DATA_FILES
        if not (data_root / name).is_file()
    )


def present_optional_files(root: Path) -> tuple[str, ...]:
    data_root = Path(root)
    return tuple(
        name
        for name in OPTIONAL_DATA_FILES
        if (data_root / name).is_file()
    )


def import_runtime_files(
    source_files: tuple[Path, ...],
    managed_root: Path,
) -> RuntimeImportResult:
    """Copy only explicitly selected recognized files into user_data."""

    destination_root = Path(managed_root).resolve()
    canonical_names = {
        name.casefold(): name
        for name in ALLOWED_RUNTIME_FILES
    }
    copied: list[str] = []
    rejected: list[str] = []
    failed: list[str] = []

    try:
        destination_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        return RuntimeImportResult(
            failed=tuple(Path(path).name for path in source_files)
        )

    for source_value in source_files:
        source = Path(source_value)
        canonical_name = canonical_names.get(source.name.casefold())
        if canonical_name is None or not source.is_file():
            rejected.append(source.name)
            continue

        destination = destination_root / canonical_name
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=destination_root,
                prefix=f".{canonical_name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
            shutil.copyfile(source, temporary_path)
            os.replace(temporary_path, destination)
        except OSError:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            failed.append(canonical_name)
            continue
        copied.append(canonical_name)

    return RuntimeImportResult(
        copied=tuple(copied),
        rejected=tuple(rejected),
        failed=tuple(failed),
    )
