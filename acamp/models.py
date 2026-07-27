"""Immutable GUI-side data models.

The GUI models preserve compatibility with the legacy JSON shape without
modifying the source records.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


def _safe_text(value: Any) -> str:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return "-"
    text = str(value).strip()
    return text or "-"


def _safe_age(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return "-"
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return "-"
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        return "-"
    return str(int(number))


def _safe_payment_amount(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        return None
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not amount.is_finite() or amount < 0:
        return None
    return amount


def _safe_payment(value: Any) -> str:
    amount = _safe_payment_amount(value)
    return "-" if amount is None else f"${amount:,.2f}"


@dataclass(frozen=True, slots=True)
class Participant:
    """Read-only representation of one participant record."""

    name: str
    age: str
    phone: str
    inscription: str
    payment: str
    payment_amount: Decimal | None
    accommodation: str
    transportation: str
    medical: str
    email: str
    food: str
    participant_id: str

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "Participant":
        return cls(
            name=_safe_text(record.get("name")),
            age=_safe_age(record.get("age")),
            phone=_safe_text(record.get("phone")),
            inscription=_safe_text(record.get("inscription")),
            payment=_safe_payment(record.get("payment")),
            payment_amount=_safe_payment_amount(record.get("payment")),
            accommodation=_safe_text(record.get("accommodation")),
            transportation=_safe_text(record.get("transportation")),
            medical=_safe_text(record.get("medical")),
            email=_safe_text(record.get("email")),
            food=_safe_text(record.get("food")),
            participant_id=_safe_text(record.get("id")),
        )


def _inventory_quantity(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        quantity = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if quantity < 0:
        return None
    try:
        if Decimal(str(value).strip()) != Decimal(quantity):
            return None
    except (InvalidOperation, ValueError, TypeError):
        return None
    return quantity


def _inventory_value(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        return None
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not amount.is_finite() or amount < 0:
        return None
    return amount


def format_currency(value: Decimal | None) -> str:
    if value is None:
        return "-"
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


@dataclass(frozen=True, slots=True)
class InventoryItem:
    """Display-safe view of an existing inventory record."""

    source_index: int
    item: str
    quantity: int | None
    value: Decimal | None
    description: str

    @classmethod
    def from_mapping(
        cls,
        record: Mapping[str, Any],
        source_index: int,
    ) -> "InventoryItem":
        return cls(
            source_index=source_index,
            item=_safe_text(record.get("item")),
            quantity=_inventory_quantity(record.get("quantity")),
            value=_inventory_value(record.get("value")),
            description=_safe_text(record.get("description")),
        )

    @property
    def quantity_display(self) -> str:
        return "-" if self.quantity is None else str(self.quantity)

    @property
    def value_display(self) -> str:
        return format_currency(self.value)

    @property
    def total_value(self) -> Decimal | None:
        if self.quantity is None or self.value is None:
            return None
        return self.value * self.quantity

    @property
    def total_display(self) -> str:
        return format_currency(self.total_value)


@dataclass(frozen=True, slots=True)
class InventoryDraft:
    """Validated data for one new inventory record."""

    item: str
    quantity: int
    value: Decimal
    description: str

    def to_record(self) -> dict[str, str | int | float]:
        return {
            "item": self.item,
            "quantity": self.quantity,
            "value": float(self.value),
            "description": self.description,
        }


def _team_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not number.is_finite() or number != number.to_integral_value():
        return None
    return int(number)


@dataclass(frozen=True, slots=True)
class Team:
    """Display-safe view of an existing team record."""

    source_index: int
    name: str
    leader: str
    color: str
    participant_count: int | None
    score: int | None

    @classmethod
    def from_mapping(
        cls,
        record: Mapping[str, Any],
        source_index: int,
    ) -> "Team":
        people = record.get("pessoas")
        participant_count = len(people) if isinstance(people, list) else None
        return cls(
            source_index=source_index,
            name=_safe_text(record.get("equipe")),
            leader=_safe_text(record.get("lider")),
            color=_safe_text(record.get("cor")),
            participant_count=participant_count,
            score=_team_integer(record.get("score")),
        )

    @property
    def participant_count_display(self) -> str:
        return (
            "-"
            if self.participant_count is None
            else str(self.participant_count)
        )

    @property
    def score_display(self) -> str:
        return "-" if self.score is None else str(self.score)


@dataclass(frozen=True, slots=True)
class TeamDraft:
    """Validated information for a newly created team."""

    name: str
    leader: str
    color: str

    def to_record(self) -> dict[str, str | int | list]:
        return {
            "equipe": self.name,
            "lider": self.leader,
            "cor": self.color,
            "pessoas": [],
            "score": 0,
        }
