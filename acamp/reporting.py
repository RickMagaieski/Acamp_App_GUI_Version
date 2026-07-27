"""Pure, read-only aggregations for the GUI reports page."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Sequence

from .models import InventoryItem, Participant, Team
from .pricing import FinancialSnapshot, PaymentStatus


AGE_GROUP_LABELS = (
    "Bebês (0–5)",
    "Crianças (6–12)",
    "Adolescentes (13–17)",
    "Jovens (18–29)",
    "Adultos (30–59)",
    "Terceira idade (60+)",
    "Sem informação",
)

FOOD_LABELS = (
    "Come carne",
    "Não come carne",
    "Sem informação/Outro",
)

ACCOMMODATION_LABELS = (
    "Barraca",
    "RV",
    "Cabine",
    "Especial",
    "Sem informação/Outro",
)

TRANSPORTATION_LABELS = (
    "Precisa de ajuda",
    "Não precisa de ajuda",
    "Sem informação/Outro",
)

PAYMENT_STATUS_ORDER = (
    PaymentStatus.PAID,
    PaymentStatus.PARTIAL,
    PaymentStatus.PENDING,
    PaymentStatus.SPECIAL,
    PaymentStatus.UNCLASSIFIED,
)

PAYMENT_STATUS_LABELS = {
    PaymentStatus.PAID: "Pagos",
    PaymentStatus.PARTIAL: "Parciais",
    PaymentStatus.PENDING: "Pendentes",
    PaymentStatus.SPECIAL: "Especiais/Isentos",
    PaymentStatus.UNCLASSIFIED: "Não classificados",
}


@dataclass(frozen=True, slots=True)
class CategoryCount:
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class TeamRankingEntry:
    position: int
    team: Team


@dataclass(frozen=True, slots=True)
class FinancialReport:
    entries: Decimal
    expenses: Decimal
    event_result: Decimal
    available_balance: Decimal

    @classmethod
    def from_snapshot(
        cls,
        snapshot: FinancialSnapshot,
    ) -> "FinancialReport":
        return cls(
            entries=snapshot.entries,
            expenses=snapshot.expenses,
            event_result=snapshot.event_result,
            available_balance=snapshot.available_balance,
        )


@dataclass(frozen=True, slots=True)
class ReportSnapshot:
    participant_total: int
    age_groups: tuple[CategoryCount, ...]
    food_categories: tuple[CategoryCount, ...]
    accommodation_categories: tuple[CategoryCount, ...]
    transportation_categories: tuple[CategoryCount, ...]
    payment_statuses: tuple[CategoryCount, ...]
    financial: FinancialReport
    team_ranking: tuple[TeamRankingEntry, ...]
    inventory_item_count: int
    inventory_unit_count: int
    team_count: int
    team_member_count: int
    unknown_inventory_quantity_count: int
    unknown_team_member_list_count: int
    participants_available: bool
    inventory_available: bool
    teams_available: bool
    skipped_participant_records: int = 0
    skipped_inventory_records: int = 0
    skipped_team_records: int = 0

    @property
    def has_unclassified_records(self) -> bool:
        unknown_labels = {
            "Sem informação",
            "Sem informação/Outro",
            PAYMENT_STATUS_LABELS[PaymentStatus.UNCLASSIFIED],
        }
        categorical_sections = (
            self.age_groups,
            self.food_categories,
            self.accommodation_categories,
            self.transportation_categories,
            self.payment_statuses,
        )
        return (
            any(
                entry.count > 0 and entry.label in unknown_labels
                for section in categorical_sections
                for entry in section
            )
            or self.skipped_participant_records > 0
            or self.skipped_inventory_records > 0
            or self.skipped_team_records > 0
            or self.unknown_inventory_quantity_count > 0
            or self.unknown_team_member_list_count > 0
        )

    def _category_value(
        self,
        entries: Sequence[CategoryCount],
        label: str,
    ) -> int:
        return next(
            (entry.count for entry in entries if entry.label == label),
            0,
        )

    @property
    def paid_count(self) -> int:
        return self._category_value(
            self.payment_statuses,
            PAYMENT_STATUS_LABELS[PaymentStatus.PAID],
        )

    @property
    def partial_count(self) -> int:
        return self._category_value(
            self.payment_statuses,
            PAYMENT_STATUS_LABELS[PaymentStatus.PARTIAL],
        )

    @property
    def pending_count(self) -> int:
        return self._category_value(
            self.payment_statuses,
            PAYMENT_STATUS_LABELS[PaymentStatus.PENDING],
        )

    @property
    def transportation_help_count(self) -> int:
        return self._category_value(
            self.transportation_categories,
            TRANSPORTATION_LABELS[0],
        )

    @property
    def leading_team(self) -> TeamRankingEntry | None:
        return self.team_ranking[0] if self.team_ranking else None


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    collapsed = re.sub(r"\s+", " ", value.strip().casefold())
    if collapsed in {"", "-", "n/a", "none", "null"}:
        return ""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", collapsed)
        if not unicodedata.combining(character)
    )


def _age_group(age_value: str) -> str:
    try:
        age = Decimal(str(age_value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return AGE_GROUP_LABELS[-1]
    if (
        not age.is_finite()
        or age < 0
        or age != age.to_integral_value()
    ):
        return AGE_GROUP_LABELS[-1]

    numeric_age = int(age)
    if numeric_age <= 5:
        return AGE_GROUP_LABELS[0]
    if numeric_age <= 12:
        return AGE_GROUP_LABELS[1]
    if numeric_age <= 17:
        return AGE_GROUP_LABELS[2]
    if numeric_age <= 29:
        return AGE_GROUP_LABELS[3]
    if numeric_age <= 59:
        return AGE_GROUP_LABELS[4]
    return AGE_GROUP_LABELS[5]


def _food_category(value: str) -> str:
    normalized = _normalize_text(value)
    if normalized == "sim":
        return FOOD_LABELS[0]
    if normalized == "nao":
        return FOOD_LABELS[1]
    return FOOD_LABELS[2]


def _accommodation_category(value: str) -> str:
    normalized = _normalize_text(value)
    return {
        "barraca": ACCOMMODATION_LABELS[0],
        "rv": ACCOMMODATION_LABELS[1],
        "cabine": ACCOMMODATION_LABELS[2],
        "flag": ACCOMMODATION_LABELS[3],
    }.get(normalized, ACCOMMODATION_LABELS[4])


def _transportation_category(value: str) -> str:
    normalized = _normalize_text(value)
    if normalized == "sim":
        return TRANSPORTATION_LABELS[0]
    if normalized == "nao":
        return TRANSPORTATION_LABELS[1]
    return TRANSPORTATION_LABELS[2]


def _count_categories(
    participants: Sequence[Participant],
    labels: Sequence[str],
    classifier: Callable[[Participant], str],
) -> tuple[CategoryCount, ...]:
    counts = {label: 0 for label in labels}
    for participant in participants:
        counts[classifier(participant)] += 1
    return tuple(CategoryCount(label, counts[label]) for label in labels)


def rank_teams(teams: Sequence[Team]) -> tuple[TeamRankingEntry, ...]:
    """Return a stable competition ranking without changing shared order."""

    ordered = sorted(
        teams,
        key=lambda team: (-team.score_value, team.source_index),
    )
    entries: list[TeamRankingEntry] = []
    previous_score: int | None = None
    previous_position = 0
    for index, team in enumerate(ordered):
        if previous_score is None or team.score_value != previous_score:
            previous_position = index + 1
            previous_score = team.score_value
        entries.append(TeamRankingEntry(previous_position, team))
    return tuple(entries)


def build_report_snapshot(
    participants: Sequence[Participant],
    financial: FinancialSnapshot,
    teams: Sequence[Team],
    *,
    inventory_items: Sequence[InventoryItem] = (),
    participants_available: bool = True,
    inventory_available: bool = True,
    teams_available: bool = True,
    skipped_participant_records: int = 0,
    skipped_inventory_records: int = 0,
    skipped_team_records: int = 0,
) -> ReportSnapshot:
    """Aggregate shared in-memory state without reading or writing storage."""

    age_groups = _count_categories(
        participants,
        AGE_GROUP_LABELS,
        lambda participant: _age_group(participant.age),
    )
    food_categories = _count_categories(
        participants,
        FOOD_LABELS,
        lambda participant: _food_category(participant.food),
    )
    accommodation_categories = _count_categories(
        participants,
        ACCOMMODATION_LABELS,
        lambda participant: _accommodation_category(
            participant.accommodation
        ),
    )
    transportation_categories = _count_categories(
        participants,
        TRANSPORTATION_LABELS,
        lambda participant: _transportation_category(
            participant.transportation
        ),
    )
    payment_statuses = tuple(
        CategoryCount(
            PAYMENT_STATUS_LABELS[status],
            financial.status_counts[status],
        )
        for status in PAYMENT_STATUS_ORDER
    )
    inventory_item_count = len(inventory_items)
    inventory_unit_count = sum(
        item.quantity
        for item in inventory_items
        if item.quantity is not None
    )
    unknown_inventory_quantity_count = sum(
        item.quantity is None
        for item in inventory_items
    )
    team_member_count = sum(
        team.participant_count
        for team in teams
        if team.participant_count is not None
    )
    unknown_team_member_list_count = sum(
        team.participant_count is None
        for team in teams
    )

    return ReportSnapshot(
        participant_total=len(participants),
        age_groups=age_groups,
        food_categories=food_categories,
        accommodation_categories=accommodation_categories,
        transportation_categories=transportation_categories,
        payment_statuses=payment_statuses,
        financial=FinancialReport.from_snapshot(financial),
        team_ranking=rank_teams(teams),
        inventory_item_count=inventory_item_count,
        inventory_unit_count=inventory_unit_count,
        team_count=len(teams),
        team_member_count=team_member_count,
        unknown_inventory_quantity_count=(
            unknown_inventory_quantity_count
        ),
        unknown_team_member_list_count=unknown_team_member_list_count,
        participants_available=participants_available,
        inventory_available=inventory_available,
        teams_available=teams_available,
        skipped_participant_records=skipped_participant_records,
        skipped_inventory_records=skipped_inventory_records,
        skipped_team_records=skipped_team_records,
    )
