"""Qt and collection models for the participant table."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from acamp.models import Participant


def filter_participants(
    participants: Sequence[Participant],
    query: str,
) -> tuple[Participant, ...]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return tuple(participants)
    return tuple(
        participant
        for participant in participants
        if normalized_query in participant.name.casefold()
    )


@dataclass(frozen=True, slots=True)
class PageSlice:
    items: tuple[Participant, ...]
    page_index: int
    total_pages: int
    total_items: int


def paginate_participants(
    participants: Sequence[Participant],
    requested_page: int,
    page_size: int = 10,
) -> PageSlice:
    if page_size <= 0:
        raise ValueError("page_size must be positive")

    total_items = len(participants)
    if total_items == 0:
        return PageSlice((), 0, 0, 0)

    total_pages = ceil(total_items / page_size)
    page_index = min(max(requested_page, 0), total_pages - 1)
    start = page_index * page_size
    return PageSlice(
        items=tuple(participants[start : start + page_size]),
        page_index=page_index,
        total_pages=total_pages,
        total_items=total_items,
    )


class ParticipantTableModel(QAbstractTableModel):
    HEADERS = (
        "Nome",
        "Idade",
        "Telefone",
        "Inscrição",
        "Pagamento",
        "Acomodação",
        "Transporte",
    )

    def __init__(self, participants: Sequence[Participant] = (), parent=None):
        super().__init__(parent)
        self._participants = tuple(participants)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._participants)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._participants):
            return None

        participant = self._participants[index.row()]
        values = (
            participant.name,
            participant.age,
            participant.phone,
            participant.inscription,
            participant.payment,
            participant.accommodation,
            participant.transportation,
        )

        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_participants(self, participants: Sequence[Participant]) -> None:
        self.beginResetModel()
        self._participants = tuple(participants)
        self.endResetModel()

