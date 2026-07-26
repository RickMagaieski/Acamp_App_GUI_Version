"""Read-only repositories used by the standalone GUI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .models import Participant


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
