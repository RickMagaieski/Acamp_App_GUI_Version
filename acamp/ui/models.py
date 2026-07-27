"""Qt and collection models for the participant table."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from acamp.models import (
    InventoryItem,
    Participant,
    Team,
    TeamMember,
    format_currency,
)
from acamp.pricing import ParticipantPayment
from acamp.reporting import TeamRankingEntry, rank_teams


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


def filter_inventory_items(
    items: Sequence[InventoryItem],
    query: str,
) -> tuple[InventoryItem, ...]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return tuple(items)
    return tuple(
        item
        for item in items
        if normalized_query in item.item.casefold()
    )


class InventoryTableModel(QAbstractTableModel):
    HEADERS = (
        "Item",
        "Quantidade",
        "Valor unitário",
        "Valor total",
        "Descrição",
        "Ações",
    )
    ACTION_COLUMN = 5

    def __init__(self, items: Sequence[InventoryItem] = (), parent=None):
        super().__init__(parent)
        self._items = tuple(items)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None

        item = self._items[index.row()]
        values = (
            item.item,
            item.quantity_display,
            item.value_display,
            item.total_display,
            item.description,
            "Excluir",
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (0, 4):
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
        if (
            role == Qt.ItemDataRole.ForegroundRole
            and index.column() == self.ACTION_COLUMN
        ):
            return QColor("#d55a17")
        if (
            role == Qt.ItemDataRole.ToolTipRole
            and index.column() == self.ACTION_COLUMN
        ):
            return "Excluir item"
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_items(self, items: Sequence[InventoryItem]) -> None:
        self.beginResetModel()
        self._items = tuple(items)
        self.endResetModel()

    def item_at(self, row: int) -> InventoryItem | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None


class PaymentTableModel(QAbstractTableModel):
    HEADERS = (
        "Nome",
        "Tipo de inscrição",
        "Valor esperado",
        "Valor pago",
        "Valor pendente",
        "Status",
    )

    def __init__(self, payments: Sequence[ParticipantPayment] = (), parent=None):
        super().__init__(parent)
        self._payments = tuple(payments)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._payments)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._payments):
            return None

        payment = self._payments[index.row()]
        values = (
            payment.name,
            payment.registration_type,
            format_currency(payment.expected),
            format_currency(payment.paid),
            format_currency(payment.remaining),
            payment.status.value,
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (0, 1):
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


def filter_teams(
    teams: Sequence[Team],
    query: str,
) -> tuple[Team, ...]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return tuple(teams)
    return tuple(
        team for team in teams if normalized_query in team.name.casefold()
    )


class TeamTableModel(QAbstractTableModel):
    HEADERS = (
        "Time",
        "Capitão",
        "Cor",
        "Participantes",
        "Pontos",
        "Ação",
    )
    ACTION_COLUMN = 5

    def __init__(self, teams: Sequence[Team] = (), parent=None):
        super().__init__(parent)
        self._teams = tuple(teams)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._teams)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._teams):
            return None
        team = self._teams[index.row()]
        values = (
            team.name,
            team.leader,
            team.color,
            team.participant_count_display,
            team.score_display,
            "Excluir",
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (0, 1, 2):
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
        if (
            role == Qt.ItemDataRole.ForegroundRole
            and index.column() == self.ACTION_COLUMN
        ):
            return QColor("#d55a17")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_teams(self, teams: Sequence[Team]) -> None:
        self.beginResetModel()
        self._teams = tuple(teams)
        self.endResetModel()

    def team_at(self, row: int) -> Team | None:
        if 0 <= row < len(self._teams):
            return self._teams[row]
        return None


class TeamMemberTableModel(QAbstractTableModel):
    HEADERS = ("Nº", "Participante")

    def __init__(self, members: Sequence[TeamMember] = (), parent=None):
        super().__init__(parent)
        self._members = tuple(members)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._members)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._members):
            return None
        member = self._members[index.row()]
        values = (str(index.row() + 1), member.name)
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_members(self, members: Sequence[TeamMember]) -> None:
        self.beginResetModel()
        self._members = tuple(members)
        self.endResetModel()

    def member_at(self, row: int) -> TeamMember | None:
        if 0 <= row < len(self._members):
            return self._members[row]
        return None


class TeamRankingTableModel(QAbstractTableModel):
    HEADERS = ("Posição", "Time", "Pontos")

    def __init__(
        self,
        entries: Sequence[TeamRankingEntry] = (),
        parent=None,
    ):
        super().__init__(parent)
        self._entries = tuple(entries)

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        entry = self._entries[index.row()]
        values = (
            f"{entry.position}º",
            entry.team.name,
            str(entry.team.score_value),
        )
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 1:
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

    def set_entries(self, entries: Sequence[TeamRankingEntry]) -> None:
        self.beginResetModel()
        self._entries = tuple(entries)
        self.endResetModel()

    def entry_at(self, row: int) -> TeamRankingEntry | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None
