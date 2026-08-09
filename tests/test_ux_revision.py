"""Structural safeguards for the Phase 5A reference-based interface."""

from __future__ import annotations

import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget

from acamp.models import Participant
from acamp.pricing import PaymentStatus
from acamp.repositories import ParticipantLoadResult, ParticipantLoadStatus
from acamp.services import InventoryService, TeamService
from acamp.ui.main_window import MainWindow
from acamp.ui.widgets import CampLandscape, Card


class ReferenceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow(
            ParticipantLoadResult.empty(),
            InventoryService(),
            TeamService(),
        )

    def tearDown(self):
        self.window.close()

    def test_sidebar_and_all_six_page_footers_follow_reference_structure(self):
        sidebar = self.window.findChild(QWidget, "sidebar")
        self.assertIsNotNone(sidebar)
        self.assertEqual(sidebar.width(), 280)
        self.assertEqual(len(self.window.navigation_buttons), 6)

        for page in (
            self.window.registrations_page,
            self.window.finance_page,
            self.window.inventory_page,
            self.window.activities_page,
            self.window.reports_page,
        ):
            self.assertGreaterEqual(len(page.findChildren(CampLandscape)), 1)
        self.assertEqual(
            len(self.window.dashboard_page.findChildren(CampLandscape)),
            1,
        )

    def test_gui_contains_no_second_confirmation_question_api(self):
        project_root = Path(__file__).resolve().parents[1]
        gui_sources = tuple((project_root / "acamp" / "ui").rglob("*.py"))
        gui_text = "\n".join(
            source.read_text(encoding="utf-8")
            for source in gui_sources
        )
        service_text = (project_root / "acamp" / "services.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("QMessageBox.question", gui_text)
        self.assertNotIn("confirm_destructive", gui_text)
        self.assertNotIn("confirmation_required", service_text)

    def test_dashboard_renders_the_five_reference_metrics(self):
        dashboard = self.window.dashboard_page
        visible_keys = (
            "participants",
            "entries",
            "expenses",
            "pending",
            "transportation",
        )
        expected_titles = (
            "TOTAL DE INSCRITOS",
            "ENTRADAS",
            "GASTOS",
            "PAGAMENTOS PENDENTES",
            "PRECISAM DE TRANSPORTE",
        )
        self.assertEqual(
            tuple(
                dashboard.metric_cards[key].title_label.text()
                for key in visible_keys
            ),
            expected_titles,
        )
        for key in visible_keys:
            self.assertFalse(dashboard.metric_cards[key].isHidden())
        for legacy_key in ("paid", "inventory", "teams"):
            self.assertTrue(dashboard.metric_cards[legacy_key].isHidden())

    def test_reports_use_compact_reference_card_heights(self):
        reports = self.window.reports_page
        self.assertEqual(reports.age_chart.height(), 285)
        self.assertEqual(reports.food_chart.height(), 285)
        self.assertEqual(reports.accommodation_chart.height(), 285)
        self.assertEqual(reports.transportation_chart.height(), 265)
        self.assertEqual(reports.payment_chart.height(), 245)
        self.assertFalse(hasattr(reports, "team_chart"))
        self.assertFalse(hasattr(reports, "warning_banner"))

        section_titles = tuple(
            card.title_label.text()
            for card in reports.findChildren(Card)
            if card.title_label.text()
        )
        self.assertEqual(
            section_titles,
            (
                "1. FAIXAS ETÁRIAS",
                "2. ALIMENTAÇÃO",
                "3. ACOMODAÇÃO",
                "4. TRANSPORTE",
                "5. FINANCEIRO",
                "6. PAGAMENTOS",
            ),
        )

    def test_isento_is_consistent_across_registration_finance_and_reports(self):
        participant = Participant.from_mapping({
            "name": "Criança Fictícia",
            "age": 7,
            "inscription": "criança",
            "accommodation": "cabine",
            "payment": 0,
            "id": "ID-FICTICIO-ISENTO",
        }, source_index=0)
        state = ParticipantLoadResult(
            ParticipantLoadStatus.VALID,
            (participant,),
        )
        window = MainWindow(state, InventoryService(), TeamService())
        try:
            registration_payment = window.registrations_page.table_model.data(
                window.registrations_page.table_model.index(0, 4)
            )
            self.assertEqual(registration_payment, "Isento")
            self.assertEqual(
                window.finance_page.status_labels[PaymentStatus.SPECIAL].text(),
                "1",
            )
            self.assertEqual(
                window.finance_page.status_labels[PaymentStatus.PENDING].text(),
                "0",
            )
            self.assertEqual(
                window.finance_page.summary_labels["entries"].text(),
                "$0.00",
            )
            self.assertEqual(
                window.dashboard_page.metric_cards["pending"].value_label.text(),
                "0",
            )
            self.assertEqual(
                window.reports_page.last_snapshot.payment_statuses[3].label,
                "Isentos",
            )
            legend_labels = tuple(
                marker.label()
                for marker in window.reports_page.payment_chart.chart_view
                .chart().legend().markers()
            )
            self.assertIn("Isentos — 1 (100%)", legend_labels)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
