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


def _safe_payment(value: Any) -> str:
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        return "-"
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return "-"
    if not amount.is_finite():
        return "-"
    return f"${amount:,.2f}"


@dataclass(frozen=True, slots=True)
class Participant:
    """Read-only representation of one participant record."""

    name: str
    age: str
    phone: str
    inscription: str
    payment: str
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
            accommodation=_safe_text(record.get("accommodation")),
            transportation=_safe_text(record.get("transportation")),
            medical=_safe_text(record.get("medical")),
            email=_safe_text(record.get("email")),
            food=_safe_text(record.get("food")),
            participant_id=_safe_text(record.get("id")),
        )

