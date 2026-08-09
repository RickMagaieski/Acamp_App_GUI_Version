"""Phase 2C finance tests using only invented in-memory records."""

from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from acamp.models import InventoryItem, Participant
from acamp.pricing import (
    INITIAL_BALANCE,
    REGISTRATION_PRICES,
    PaymentStatus,
    calculate_financial_snapshot,
    classify_payment,
    normalize_registration_type,
)
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantLoadStatus,
)
from acamp.services import InventoryService, validate_inventory_draft
from acamp.ui.main_window import MainWindow


class PricingPolicyTests(unittest.TestCase):
    def test_central_price_table(self):
        self.assertEqual(REGISTRATION_PRICES["adulto"], Decimal("135.00"))
        self.assertEqual(REGISTRATION_PRICES["criança"], Decimal("67.75"))
        self.assertEqual(REGISTRATION_PRICES["rv"], Decimal("125.00"))
        self.assertEqual(
            REGISTRATION_PRICES["sábado adulto"],
            Decimal("55.00"),
        )
        self.assertEqual(
            REGISTRATION_PRICES["sábado infantil"],
            Decimal("27.50"),
        )

    def test_registration_normalization(self):
        self.assertEqual(normalize_registration_type(" Criança "), "criança")
        self.assertEqual(normalize_registration_type("CRIanca"), "criança")
        self.assertEqual(
            normalize_registration_type("  SABADO   ADULTO "),
            "sábado adulto",
        )
        self.assertEqual(
            normalize_registration_type("sábado infantil"),
            "sábado infantil",
        )
        self.assertIsNone(normalize_registration_type("tipo desconhecido"))

    def test_paid_partial_pending_special_and_unknown(self):
        paid = classify_payment("adulto", "cabine", Decimal("135"))
        self.assertEqual(paid.status, PaymentStatus.PAID)
        self.assertEqual(paid.remaining, Decimal("0.00"))

        partial = classify_payment("criança", "cabine", Decimal("20"))
        self.assertEqual(partial.status, PaymentStatus.PARTIAL)
        self.assertEqual(partial.remaining, Decimal("47.75"))

        pending = classify_payment(
            "sábado adulto",
            "cabine",
            Decimal("0"),
        )
        self.assertEqual(pending.status, PaymentStatus.PENDING)
        self.assertEqual(pending.remaining, Decimal("55.00"))

        special = classify_payment("adulto", "flag", Decimal("0"))
        self.assertEqual(special.status, PaymentStatus.SPECIAL)
        self.assertEqual(special.remaining, Decimal("0.00"))

        unknown = classify_payment("desconhecido", "cabine", Decimal("10"))
        self.assertEqual(unknown.status, PaymentStatus.UNCLASSIFIED)
        self.assertIsNone(unknown.expected)

    def test_overpayment_is_paid(self):
        assessment = classify_payment("rv", "cabine", Decimal("150"))
        self.assertEqual(assessment.status, PaymentStatus.PAID)
        self.assertEqual(assessment.paid, Decimal("150"))

    def test_malformed_and_negative_payments_are_unclassified(self):
        self.assertEqual(
            classify_payment("adulto", "cabine", None).status,
            PaymentStatus.UNCLASSIFIED,
        )
        self.assertEqual(
            classify_payment("adulto", "cabine", Decimal("-1")).status,
            PaymentStatus.UNCLASSIFIED,
        )

    def test_age_seven_and_younger_are_isento_but_age_eight_is_not(self):
        for age in (0, 6, 7):
            assessment = classify_payment(
                "criança", "cabine", None, age
            )
            self.assertEqual(assessment.status, PaymentStatus.SPECIAL)
            self.assertEqual(assessment.expected, Decimal("0.00"))
            self.assertEqual(assessment.paid, Decimal("0.00"))
            self.assertEqual(assessment.remaining, Decimal("0.00"))

        age_eight = classify_payment(
            "criança", "cabine", Decimal("0"), 8
        )
        self.assertEqual(age_eight.status, PaymentStatus.PENDING)
        self.assertEqual(age_eight.expected, Decimal("67.75"))

    def test_missing_or_invalid_age_is_not_automatically_isento(self):
        for age in (None, "", "inválida", -1, "7.5"):
            assessment = classify_payment(
                "criança", "cabine", Decimal("0"), age
            )
            self.assertEqual(assessment.status, PaymentStatus.PENDING)


class FinancialSnapshotTests(unittest.TestCase):
    @staticmethod
    def _participant(**values) -> Participant:
        return Participant.from_mapping(values)

    def test_totals_counts_and_decimal_conversion(self):
        participants = (
            self._participant(
                name="Pessoa Um",
                inscription="adulto",
                accommodation="cabine",
                payment=135,
            ),
            self._participant(
                name="Pessoa Dois",
                inscription="crianca",
                accommodation="cabine",
                payment=20,
            ),
            self._participant(
                name="Pessoa Três",
                inscription="sabado adulto",
                accommodation="cabine",
                payment=0,
            ),
            self._participant(
                name="Pessoa Quatro",
                inscription="RV",
                accommodation="cabine",
                payment=150,
            ),
            self._participant(
                name="Pessoa Cinco",
                inscription="desconhecido",
                accommodation="cabine",
                payment=10,
            ),
            self._participant(
                name="Pessoa Seis",
                inscription="adulto",
                accommodation="flag",
                payment=0,
            ),
            self._participant(
                name="Pessoa Sete",
                inscription="adulto",
                accommodation="cabine",
                payment="nan",
            ),
        )
        inventory = (
            InventoryItem.from_mapping(
                {"item": "Item Inventado", "quantity": 2, "value": 10.25},
                0,
            ),
            InventoryItem.from_mapping(
                {"item": "Item Inválido", "quantity": "x", "value": "inf"},
                1,
            ),
        )
        snapshot = calculate_financial_snapshot(participants, inventory)

        self.assertEqual(snapshot.entries, Decimal("315"))
        self.assertEqual(snapshot.expenses, Decimal("20.50"))
        self.assertEqual(snapshot.event_result, Decimal("294.50"))
        self.assertEqual(snapshot.available_balance, Decimal("1094.50"))
        self.assertEqual(snapshot.remaining_owed, Decimal("102.75"))
        self.assertEqual(snapshot.status_counts[PaymentStatus.PAID], 2)
        self.assertEqual(snapshot.status_counts[PaymentStatus.PARTIAL], 1)
        self.assertEqual(snapshot.status_counts[PaymentStatus.PENDING], 1)
        self.assertEqual(snapshot.status_counts[PaymentStatus.SPECIAL], 1)
        self.assertEqual(
            snapshot.status_counts[PaymentStatus.UNCLASSIFIED],
            2,
        )

    def test_float_input_converts_through_text(self):
        participant = self._participant(
            name="Pessoa Decimal",
            inscription="adulto",
            accommodation="cabine",
            payment=0.1,
        )
        self.assertEqual(participant.payment_amount, Decimal("0.1"))

    def test_empty_lists_keep_initial_balance(self):
        snapshot = calculate_financial_snapshot((), ())
        self.assertEqual(snapshot.entries, Decimal("0.00"))
        self.assertEqual(snapshot.expenses, Decimal("0.00"))
        self.assertEqual(snapshot.event_result, Decimal("0.00"))
        self.assertEqual(snapshot.available_balance, INITIAL_BALANCE)

    def test_isento_is_excluded_from_income_pending_and_amount_owed(self):
        participants = tuple(
            self._participant(
                name=f"Criança {age}",
                age=age,
                inscription="criança",
                accommodation="cabine",
                payment=99 if age == 7 else 0,
            )
            for age in (6, 7, 8)
        )
        snapshot = calculate_financial_snapshot(participants, ())

        self.assertEqual(snapshot.entries, Decimal("0.00"))
        self.assertEqual(snapshot.status_counts[PaymentStatus.SPECIAL], 2)
        self.assertEqual(snapshot.status_counts[PaymentStatus.PENDING], 1)
        self.assertEqual(snapshot.remaining_owed, Decimal("67.75"))
        self.assertEqual(snapshot.payments[0].status.value, "Isento")


class FinanceApplicationStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_inventory_gui_changes_refresh_finance_without_restart(self):
        participant = Participant.from_mapping({
            "name": "Pessoa Inventada",
            "inscription": "adulto",
            "accommodation": "cabine",
            "payment": 135,
        })
        participant_result = ParticipantLoadResult(
            ParticipantLoadStatus.VALID,
            (participant,),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            path.write_text("[]", encoding="utf-8")
            inventory_service = InventoryService(InventoryRepository(path))
            inventory_service.load()
            window = MainWindow(participant_result, inventory_service)

            draft = validate_inventory_draft(
                "Item Financeiro Inventado",
                "5",
                2,
            ).draft
            result = window.inventory_page._add_item(draft)
            self.assertTrue(result.succeeded)
            self.assertEqual(
                window.finance_page.summary_labels["expenses"].text(),
                "$10.00",
            )

            action = window.inventory_page.table_model.index(
                0,
                window.inventory_page.table_model.ACTION_COLUMN,
            )
            window.inventory_page._table_clicked(action)

            self.assertEqual(
                window.finance_page.summary_labels["expenses"].text(),
                "$0.00",
            )
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
