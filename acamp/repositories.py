"""Read-only repositories used by the standalone GUI."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from .models import InventoryItem, Participant


class ParticipantLoadStatus(str, Enum):
    LOADING = "loading"
    FILE_MISSING = "file_missing"
    FILE_EMPTY = "file_empty"
    INVALID_JSON = "invalid_json"
    ROOT_NOT_LIST = "root_not_list"
    READ_ERROR = "read_error"
    VALID_EMPTY = "valid_empty"
    VALID = "valid"


@dataclass(frozen=True, slots=True)
class ParticipantLoadResult:
    status: ParticipantLoadStatus
    participants: tuple[Participant, ...] = ()
    skipped_records: int = 0
    technical_code: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status in {
            ParticipantLoadStatus.VALID,
            ParticipantLoadStatus.VALID_EMPTY,
        }

    @classmethod
    def empty(cls) -> "ParticipantLoadResult":
        return cls(ParticipantLoadStatus.VALID_EMPTY)

    @classmethod
    def loading(cls) -> "ParticipantLoadResult":
        return cls(ParticipantLoadStatus.LOADING)


class ParticipantRepository:
    """Loads the participant cache exactly once per explicit ``load`` call."""

    def __init__(self, path: Path):
        self._path = Path(path)

    def load(self) -> ParticipantLoadResult:
        try:
            with self._path.open("r", encoding="utf-8") as source:
                raw_text = source.read()
        except FileNotFoundError:
            return ParticipantLoadResult(ParticipantLoadStatus.FILE_MISSING)
        except (OSError, UnicodeError):
            return ParticipantLoadResult(
                ParticipantLoadStatus.READ_ERROR,
                technical_code="participant_file_read_failed",
            )

        if not raw_text.strip():
            return ParticipantLoadResult(ParticipantLoadStatus.FILE_EMPTY)

        try:
            raw_records = json.loads(raw_text)
        except json.JSONDecodeError:
            return ParticipantLoadResult(
                ParticipantLoadStatus.INVALID_JSON,
                technical_code="participant_json_invalid",
            )

        if not isinstance(raw_records, list):
            return ParticipantLoadResult(
                ParticipantLoadStatus.ROOT_NOT_LIST,
                technical_code="participant_json_root_not_list",
            )

        participants: list[Participant] = []
        skipped_records = 0
        for record in raw_records:
            if not isinstance(record, dict):
                skipped_records += 1
                continue
            participants.append(Participant.from_mapping(record))

        status = (
            ParticipantLoadStatus.VALID
            if participants
            else ParticipantLoadStatus.VALID_EMPTY
        )
        return ParticipantLoadResult(
            status=status,
            participants=tuple(participants),
            skipped_records=skipped_records,
        )


class InventoryLoadStatus(str, Enum):
    LOADING = "loading"
    FILE_MISSING = "file_missing"
    FILE_EMPTY = "file_empty"
    INVALID_JSON = "invalid_json"
    ROOT_NOT_LIST = "root_not_list"
    READ_ERROR = "read_error"
    VALID_EMPTY = "valid_empty"
    VALID = "valid"


@dataclass(frozen=True, slots=True)
class InventoryLoadResult:
    status: InventoryLoadStatus
    items: tuple[InventoryItem, ...] = ()
    records: tuple[Any, ...] = ()
    skipped_records: int = 0
    technical_code: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status in {
            InventoryLoadStatus.VALID,
            InventoryLoadStatus.VALID_EMPTY,
        }

    @property
    def editable(self) -> bool:
        return self.status in {
            InventoryLoadStatus.FILE_MISSING,
            InventoryLoadStatus.FILE_EMPTY,
            InventoryLoadStatus.VALID_EMPTY,
            InventoryLoadStatus.VALID,
        }

    @classmethod
    def loading(cls) -> "InventoryLoadResult":
        return cls(InventoryLoadStatus.LOADING)


@dataclass(frozen=True, slots=True)
class InventorySaveResult:
    succeeded: bool
    technical_code: str = ""


def inventory_result_from_records(
    records: Sequence[Any],
) -> InventoryLoadResult:
    preserved_records = tuple(records)
    items: list[InventoryItem] = []
    skipped_records = 0
    for source_index, record in enumerate(preserved_records):
        if not isinstance(record, dict):
            skipped_records += 1
            continue
        items.append(InventoryItem.from_mapping(record, source_index))

    status = (
        InventoryLoadStatus.VALID
        if items
        else InventoryLoadStatus.VALID_EMPTY
    )
    return InventoryLoadResult(
        status=status,
        items=tuple(items),
        records=preserved_records,
        skipped_records=skipped_records,
    )


class InventoryRepository:
    """Loads and atomically saves the local inventory document."""

    def __init__(self, path: Path):
        self._path = Path(path)

    def load(self) -> InventoryLoadResult:
        try:
            with self._path.open("r", encoding="utf-8") as source:
                raw_text = source.read()
        except FileNotFoundError:
            return InventoryLoadResult(InventoryLoadStatus.FILE_MISSING)
        except (OSError, UnicodeError):
            return InventoryLoadResult(
                InventoryLoadStatus.READ_ERROR,
                technical_code="inventory_file_read_failed",
            )

        if not raw_text.strip():
            return InventoryLoadResult(InventoryLoadStatus.FILE_EMPTY)

        try:
            records = json.loads(raw_text)
        except json.JSONDecodeError:
            return InventoryLoadResult(
                InventoryLoadStatus.INVALID_JSON,
                technical_code="inventory_json_invalid",
            )

        if not isinstance(records, list):
            return InventoryLoadResult(
                InventoryLoadStatus.ROOT_NOT_LIST,
                technical_code="inventory_json_root_not_list",
            )
        return inventory_result_from_records(records)

    def save(self, records: Sequence[Any]) -> InventorySaveResult:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(
                    list(records),
                    temporary,
                    ensure_ascii=False,
                    indent=4,
                )
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())

            os.replace(temporary_path, self._path)
            return InventorySaveResult(True)
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return InventorySaveResult(
                False,
                technical_code="inventory_atomic_save_failed",
            )
