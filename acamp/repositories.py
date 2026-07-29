"""GUI repositories with controlled loading and atomic persistence."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from .models import InventoryItem, Participant, Team


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
    records: tuple[Any, ...] = ()
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


@dataclass(frozen=True, slots=True)
class ParticipantSaveResult:
    succeeded: bool
    technical_code: str = ""


def participant_result_from_records(
    records: Sequence[Any],
) -> ParticipantLoadResult:
    preserved_records = tuple(records)
    participants: list[Participant] = []
    skipped_records = 0
    for source_index, record in enumerate(preserved_records):
        if not isinstance(record, dict):
            skipped_records += 1
            continue
        participants.append(
            Participant.from_mapping(record, source_index)
        )

    status = (
        ParticipantLoadStatus.VALID
        if participants
        else ParticipantLoadStatus.VALID_EMPTY
    )
    return ParticipantLoadResult(
        status=status,
        participants=tuple(participants),
        records=preserved_records,
        skipped_records=skipped_records,
    )


class ParticipantRepository:
    """Loads and atomically replaces the local participant cache."""

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

        return participant_result_from_records(raw_records)

    def save(self, records: Sequence[Any]) -> ParticipantSaveResult:
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
            return ParticipantSaveResult(True)
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return ParticipantSaveResult(
                False,
                technical_code="participant_atomic_save_failed",
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


class TeamLoadStatus(str, Enum):
    LOADING = "loading"
    FILE_MISSING = "file_missing"
    FILE_EMPTY = "file_empty"
    INVALID_JSON = "invalid_json"
    ROOT_NOT_LIST = "root_not_list"
    READ_ERROR = "read_error"
    VALID_EMPTY = "valid_empty"
    VALID = "valid"


@dataclass(frozen=True, slots=True)
class TeamLoadResult:
    status: TeamLoadStatus
    teams: tuple[Team, ...] = ()
    records: tuple[Any, ...] = ()
    skipped_records: int = 0
    technical_code: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status in {
            TeamLoadStatus.VALID,
            TeamLoadStatus.VALID_EMPTY,
        }

    @property
    def editable(self) -> bool:
        return self.status in {
            TeamLoadStatus.FILE_MISSING,
            TeamLoadStatus.FILE_EMPTY,
            TeamLoadStatus.VALID_EMPTY,
            TeamLoadStatus.VALID,
        }

    @classmethod
    def loading(cls) -> "TeamLoadResult":
        return cls(TeamLoadStatus.LOADING)


@dataclass(frozen=True, slots=True)
class TeamSaveResult:
    succeeded: bool
    technical_code: str = ""


def team_result_from_records(records: Sequence[Any]) -> TeamLoadResult:
    preserved_records = tuple(records)
    teams: list[Team] = []
    skipped_records = 0
    for source_index, record in enumerate(preserved_records):
        if not isinstance(record, dict):
            skipped_records += 1
            continue
        teams.append(Team.from_mapping(record, source_index))

    status = TeamLoadStatus.VALID if teams else TeamLoadStatus.VALID_EMPTY
    return TeamLoadResult(
        status=status,
        teams=tuple(teams),
        records=preserved_records,
        skipped_records=skipped_records,
    )


class TeamRepository:
    """Loads and atomically saves the local team document."""

    def __init__(self, path: Path):
        self._path = Path(path)

    def load(self) -> TeamLoadResult:
        try:
            with self._path.open("r", encoding="utf-8") as source:
                raw_text = source.read()
        except FileNotFoundError:
            return TeamLoadResult(TeamLoadStatus.FILE_MISSING)
        except (OSError, UnicodeError):
            return TeamLoadResult(
                TeamLoadStatus.READ_ERROR,
                technical_code="team_file_read_failed",
            )

        if not raw_text.strip():
            return TeamLoadResult(TeamLoadStatus.FILE_EMPTY)

        try:
            records = json.loads(raw_text)
        except json.JSONDecodeError:
            return TeamLoadResult(
                TeamLoadStatus.INVALID_JSON,
                technical_code="team_json_invalid",
            )

        if not isinstance(records, list):
            return TeamLoadResult(
                TeamLoadStatus.ROOT_NOT_LIST,
                technical_code="team_json_root_not_list",
            )
        return team_result_from_records(records)

    def save(self, records: Sequence[Any]) -> TeamSaveResult:
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
            return TeamSaveResult(True)
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return TeamSaveResult(
                False,
                technical_code="team_atomic_save_failed",
            )
