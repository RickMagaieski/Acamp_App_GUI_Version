"""Structural safeguards for the Phase 5A reference-based interface."""

from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication, QWidget

from acamp.repositories import ParticipantLoadResult
from acamp.services import InventoryService, TeamService
from acamp.ui.main_window import MainWindow
from acamp.ui.widgets import CampLandscape


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
            self.window.dashboard_page,
            self.window.registrations_page,
            self.window.finance_page,
            self.window.inventory_page,
            self.window.activities_page,
            self.window.reports_page,
        ):
            self.assertGreaterEqual(len(page.findChildren(CampLandscape)), 1)

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
        self.assertEqual(reports.team_chart.height(), 300)


if __name__ == "__main__":
    unittest.main()
