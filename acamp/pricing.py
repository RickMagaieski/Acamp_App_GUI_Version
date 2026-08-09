"""Central financial policy and pure Decimal-based calculations."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence

from .models import InventoryItem, Participant


INITIAL_BALANCE = Decimal("800.00")

REGISTRATION_PRICES: Mapping[str, Decimal] = MappingProxyType({
    "adulto": Decimal("135.00"),
    "criança": Decimal("67.75"),
    "rv": Decimal("125.00"),
    "sábado adulto": Decimal("55.00"),
    "sábado infantil": Decimal("27.50"),
})

REGISTRATION_LABELS: Mapping[str, str] = MappingProxyType({
    "adulto": "Adulto (14+)",
    "criança": "Criança",
    "rv": "Com RV",
    "sábado adulto": "Sábado Adulto",
    "sábado infantil": "Sábado Infantil",
})


def normalize_registration_type(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    collapsed = re.sub(r"\s+", " ", value.strip().casefold())
    if not collapsed:
        return None
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", collapsed)
        if not unicodedata.combining(character)
    )
    normalized_prices = {
        "adulto": "adulto",
        "crianca": "criança",
        "rv": "rv",
        "sabado adulto": "sábado adulto",
        "sabado infantil": "sábado infantil",
    }
    return normalized_prices.get(without_accents)


def normalize_accommodation(value: str) -> str:
    if not isinstance(value, str):
        return ""
    collapsed = re.sub(r"\s+", " ", value.strip().casefold())
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", collapsed)
        if not unicodedata.combining(character)
    )


def is_payment_exempt_age(age: object) -> bool:
    """Return whether a valid whole-number age is exempt from payment."""

    if isinstance(age, bool) or age is None:
        return False
    try:
        numeric_age = Decimal(str(age).strip())
    except (InvalidOperation, TypeError, ValueError):
        return False
    return (
        numeric_age.is_finite()
        and numeric_age >= 0
        and numeric_age == numeric_age.to_integral_value()
        and numeric_age <= 7
    )


class PaymentStatus(str, Enum):
    PAID = "Pago"
    PARTIAL = "Parcial"
    PENDING = "Pendente"
    SPECIAL = "Isento"
    UNCLASSIFIED = "Não classificado"


@dataclass(frozen=True, slots=True)
class PaymentAssessment:
    status: PaymentStatus
    expected: Decimal | None
    paid: Decimal | None
    remaining: Decimal | None


def classify_payment(
    registration_type: str,
    accommodation: str,
    payment: Decimal | None,
    age: object = None,
) -> PaymentAssessment:
    if is_payment_exempt_age(age):
        return PaymentAssessment(
            PaymentStatus.SPECIAL,
            expected=Decimal("0.00"),
            paid=Decimal("0.00"),
            remaining=Decimal("0.00"),
        )

    if payment is None or not payment.is_finite() or payment < 0:
        return PaymentAssessment(
            PaymentStatus.UNCLASSIFIED,
            expected=None,
            paid=None,
            remaining=None,
        )

    canonical_type = normalize_registration_type(registration_type)
    if normalize_accommodation(accommodation) == "flag" and payment == 0:
        expected = (
            REGISTRATION_PRICES.get(canonical_type)
            if canonical_type is not None
            else None
        )
        return PaymentAssessment(
            PaymentStatus.SPECIAL,
            expected=expected,
            paid=payment,
            remaining=Decimal("0.00"),
        )

    if canonical_type is None:
        return PaymentAssessment(
            PaymentStatus.UNCLASSIFIED,
            expected=None,
            paid=payment,
            remaining=None,
        )

    expected = REGISTRATION_PRICES[canonical_type]
    if payment >= expected:
        return PaymentAssessment(
            PaymentStatus.PAID,
            expected=expected,
            paid=payment,
            remaining=Decimal("0.00"),
        )
    if payment > 0:
        return PaymentAssessment(
            PaymentStatus.PARTIAL,
            expected=expected,
            paid=payment,
            remaining=expected - payment,
        )
    return PaymentAssessment(
        PaymentStatus.PENDING,
        expected=expected,
        paid=payment,
        remaining=expected,
    )


@dataclass(frozen=True, slots=True)
class ParticipantPayment:
    name: str
    registration_type: str
    expected: Decimal | None
    paid: Decimal | None
    remaining: Decimal | None
    status: PaymentStatus


@dataclass(frozen=True, slots=True)
class FinancialSnapshot:
    entries: Decimal
    expenses: Decimal
    event_result: Decimal
    available_balance: Decimal
    remaining_owed: Decimal
    status_counts: Mapping[PaymentStatus, int]
    payments: tuple[ParticipantPayment, ...]
    participants_available: bool
    inventory_available: bool


def calculate_financial_snapshot(
    participants: Sequence[Participant],
    inventory_items: Sequence[InventoryItem],
    *,
    participants_available: bool = True,
    inventory_available: bool = True,
) -> FinancialSnapshot:
    expenses = sum(
        (
            item.total_value
            for item in inventory_items
            if item.total_value is not None
        ),
        Decimal("0.00"),
    )

    counts = {status: 0 for status in PaymentStatus}
    payment_details: list[ParticipantPayment] = []
    entries = Decimal("0.00")
    remaining_owed = Decimal("0.00")
    for participant in participants:
        assessment = classify_payment(
            participant.inscription,
            participant.accommodation,
            participant.payment_amount,
            participant.age,
        )
        if assessment.paid is not None:
            entries += assessment.paid
        counts[assessment.status] += 1
        if assessment.status in {
            PaymentStatus.PARTIAL,
            PaymentStatus.PENDING,
        } and assessment.remaining is not None:
            remaining_owed += assessment.remaining
        payment_details.append(
            ParticipantPayment(
                name=participant.name,
                registration_type=participant.inscription,
                expected=assessment.expected,
                paid=assessment.paid,
                remaining=assessment.remaining,
                status=assessment.status,
            )
        )

    event_result = entries - expenses
    return FinancialSnapshot(
        entries=entries,
        expenses=expenses,
        event_result=event_result,
        available_balance=INITIAL_BALANCE + event_result,
        remaining_owed=remaining_owed,
        status_counts=MappingProxyType(counts),
        payments=tuple(payment_details),
        participants_available=participants_available,
        inventory_available=inventory_available,
    )
