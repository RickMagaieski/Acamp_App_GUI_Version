"""Phase 2F Dashboard tests using only invented temporary data."""

from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLabel

from acamp.models import InventoryItem, Participant, Team
from acamp.pricing import calculate_financial_snapshot
from acamp.reporting import build_report_snapshot
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantLoadStatus,
    TeamRepository,
)
from acamp.services import (
    InventoryService,
    TeamService,
    validate_inventory_draft,
    validate_team_draft,
    validate_team_member_name,
)
from acamp.ui.main_window import MainWindow


def _participant(**values) -> Participant:
    return Participant.from_mapping(values)


class DashboardAggregationTests(unittest.TestCase):
    def test_dashboard_aggregates_and_leader_reuse_report_state(self):
        participants = (
            _participant(
                name="Pessoa Fictícia Um",
                inscription="adulto",
                accommodation="cabine",
                transportation="sim",
                payment=135,
            ),
            _participant(
                name="Pessoa Fictícia Dois",
                inscription="adulto",
                accommodation="cabine",
                transportation="não",
                payment=40,
            ),
            _participant(
                name="Pessoa Fictícia Três",
                inscription="adulto",
                accommodation="cabine",
                transportation="sim",
                payment=0,
            ),
        )
        inventory = (
            InventoryItem.from_mapping(
                {"item": "Item Fictício A", "quantity": 2, "value": 4},
                0,
            ),
            InventoryItem.from_mapping(
                {"item": "Item Fictício B", "quantity": 3, "value": 1.5},
                1,
            ),
            InventoryItem.from_mapping(
                {"item": "Item Fictício C", "quantity": "x", "value": 2},
                2,
            ),
        )
        teams = (
            Team.from_mapping(
                {
                    "equipe": "Equipe Fictícia Primeiro Registro",
                    "lider": "Líder Fictício",
                    "cor": "Verde",
                    "pessoas": [
                        {"participante": "Membro Fictício A"},
                        {"participante": "Membro Fictício B"},
                    ],
                    "score": 8,
                },
                0,
            ),
            Team.from_mapping(
                {
                    "equipe": "Equipe Fictícia Segundo Registro",
                    "lider": "Líder Fictício",
                    "cor": "Laranja",
                    "pessoas": [{"participante": "Membro Fictício C"}],
                    "score": 8,
                },
                1,
            ),
            Team.from_mapping(
                {
                    "equipe": "Equipe Fictícia Negativa",
                    "lider": "Líder Fictício",
                    "cor": "Azul",
                    "pessoas": [],
                    "score": -4,
                },
                2,
            ),
        )
        financial = calculate_financial_snapshot(participants, inventory)

        snapshot = build_report_snapshot(
            participants,
            financial,
            teams,
            inventory_items=inventory,
        )

        self.assertEqual(snapshot.participant_total, 3)
        self.assertEqual(snapshot.paid_count, 1)
        self.assertEqual(snapshot.partial_count, 1)
        self.assertEqual(snapshot.pending_count, 1)
        self.assertEqual(snapshot.transportation_help_count, 2)
        self.assertEqual(snapshot.inventory_item_count, 3)
        self.assertEqual(snapshot.inventory_unit_count, 5)
        self.assertEqual(snapshot.team_count, 3)
        self.assertEqual(snapshot.team_member_count, 3)
        self.assertEqual(
            snapshot.leading_team.team.name,
            "Equipe Fictícia Primeiro Registro",
        )
        self.assertEqual(snapshot.leading_team.position, 1)
        self.assertEqual(snapshot.team_ranking[1].position, 1)
        self.assertEqual(snapshot.team_ranking[-1].team.score_value, -4)
        self.assertEqual(snapshot.financial.entries, financial.entries)
        self.assertEqual(snapshot.financial.expenses, financial.expenses)
        self.assertTrue(snapshot.has_unclassified_records)

    def test_empty_snapshot_has_safe_zero_values(self):
        snapshot = build_report_snapshot(
            (),
            calculate_financial_snapshot((), ()),
            (),
        )
        self.assertEqual(snapshot.participant_total, 0)
        self.assertEqual(snapshot.paid_count, 0)
        self.assertEqual(snapshot.pending_count, 0)
        self.assertEqual(snapshot.inventory_item_count, 0)
        self.assertEqual(snapshot.inventory_unit_count, 0)
        self.assertEqual(snapshot.team_count, 0)
        self.assertEqual(snapshot.team_member_count, 0)
        self.assertIsNone(snapshot.leading_team)


class DashboardApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _participant_state() -> ParticipantLoadResult:
        return ParticipantLoadResult(
            ParticipantLoadStatus.VALID,
            (
                _participant(
                    name="Pessoa Fictícia Privada",
                    age=28,
                    food="sim",
                    transportation="sim",
                    inscription="adulto",
                    accommodation="cabine",
                    payment=135,
                ),
                _participant(
                    name="Outra Pessoa Fictícia",
                    age=31,
                    food="não",
                    transportation="não",
                    inscription="adulto",
                    accommodation="cabine",
                    payment=0,
                ),
            ),
        )

    def _make_window(self, root: Path):
        inventory_path = root / "items.json"
        team_path = root / "teams.json"
        inventory_path.write_text(
            json.dumps([{
                "item": "Item Inicial Fictício",
                "quantity": 2,
                "value": 3.5,
                "description": "",
            }]),
            encoding="utf-8",
        )
        team_path.write_text(
            json.dumps([
                {
                    "equipe": "Equipe Fictícia Norte",
                    "lider": "Capitão Fictício",
                    "cor": "Verde",
                    "pessoas": [
                        {"participante": "Membro Fictício Inicial"}
                    ],
                    "score": -2,
                },
                {
                    "equipe": "Equipe Fictícia Sul",
                    "lider": "Capitã Fictícia",
                    "cor": "Laranja",
                    "pessoas": [],
                    "score": 1,
                },
            ]),
            encoding="utf-8",
        )
        inventory = InventoryService(InventoryRepository(inventory_path))
        teams = TeamService(TeamRepository(team_path))
        inventory.load()
        teams.load()
        return (
            MainWindow(self._participant_state(), inventory, teams),
            inventory,
            teams,
        )

    def test_initial_metrics_finances_privacy_and_quick_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            window, _inventory, _teams = self._make_window(Path(directory))
            try:
                dashboard = window.dashboard_page
                self.assertEqual(window.current_page_index, 0)
                self.assertTrue(window.navigation_buttons[0].isChecked())
                self.assertEqual(
                    dashboard.metric_cards["participants"].value_label.text(),
                    "2",
                )
                self.assertEqual(
                    dashboard.metric_cards["paid"].value_label.text(),
                    "1",
                )
                self.assertEqual(
                    dashboard.metric_cards["pending"].value_label.text(),
                    "1",
                )
                self.assertEqual(
                    dashboard.metric_cards["inventory"].value_label.text(),
                    "1",
                )
                self.assertEqual(
                    dashboard.metric_cards["teams"].value_label.text(),
                    "2",
                )
                self.assertEqual(
                    dashboard.quick_labels["transportation"].text(),
                    "1",
                )
                self.assertEqual(
                    dashboard.quick_labels["inventory_units"].text(),
                    "2",
                )
                for key in ("entries", "expenses", "result", "available"):
                    self.assertEqual(
                        dashboard.financial_labels[key].text(),
                        window.reports_page.financial_labels[key].text(),
                    )
                self.assertEqual(
                    dashboard.financial_labels["expenses"].text(),
                    window.finance_page.summary_labels["expenses"].text(),
                )
                self.assertEqual(
                    dashboard.team_leader_label.text(),
                    "Equipe Fictícia Sul",
                )

                dashboard.metric_cards["participants"].clicked.emit()
                self.assertEqual(window.current_page_index, 1)
                self.assertTrue(window.navigation_buttons[1].isChecked())
                window.navigate_to(0)
                dashboard.reports_button.click()
                self.assertEqual(window.current_page_index, 5)
                self.assertTrue(window.navigation_buttons[5].isChecked())
                window.navigate_to(0)
                dashboard.activities_button.click()
                self.assertEqual(window.current_page_index, 4)
                self.assertTrue(window.navigation_buttons[4].isChecked())

                with patch(
                    "acamp.ui.pages.dashboard.QMessageBox.warning"
                ) as warning:
                    dashboard.sync_button.click()
                warning.assert_called_once()
                self.assertEqual(
                    dashboard.sync_status_label.text(),
                    "Ainda não sincronizado nesta sessão.",
                )

                visible_text = "\n".join(
                    label.text()
                    for label in dashboard.findChildren(QLabel)
                )
                self.assertNotIn("Pessoa Fictícia Privada", visible_text)
                self.assertNotIn("Outra Pessoa Fictícia", visible_text)
            finally:
                window.close()

    def test_shared_mutations_refresh_dashboard_without_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            window, inventory, teams = self._make_window(Path(directory))
            try:
                dashboard = window.dashboard_page
                inventory_draft = validate_inventory_draft(
                    "Item Temporário Fictício",
                    "4.50",
                    3,
                ).draft
                self.assertIsNotNone(inventory_draft)
                result = window.inventory_page._add_item(inventory_draft)
                self.assertTrue(result.succeeded)
                self.assertEqual(
                    dashboard.last_snapshot.inventory_item_count,
                    2,
                )
                self.assertEqual(
                    dashboard.last_snapshot.inventory_unit_count,
                    5,
                )
                self.assertEqual(
                    dashboard.last_snapshot.financial.expenses,
                    Decimal("20.50"),
                )

                action = window.inventory_page.table_model.index(
                    1,
                    window.inventory_page.table_model.ACTION_COLUMN,
                )
                with patch(
                    "acamp.ui.pages.inventory.confirm_destructive",
                    return_value=True,
                ):
                    window.inventory_page._table_clicked(action)
                self.assertEqual(
                    dashboard.last_snapshot.inventory_item_count,
                    1,
                )
                self.assertEqual(len(inventory.items), 1)

                north = teams.teams[0]
                window.activities_page._select_team(north)
                score_result = window.activities_page._change_score(5)
                self.assertTrue(score_result.succeeded)
                self.assertEqual(
                    dashboard.team_leader_label.text(),
                    "Equipe Fictícia Norte",
                )

                member_draft = validate_team_member_name(
                    "Novo Membro Fictício"
                ).draft
                self.assertIsNotNone(member_draft)
                member_result = window.activities_page._add_member(
                    member_draft
                )
                self.assertTrue(member_result.succeeded)
                self.assertEqual(
                    dashboard.last_snapshot.team_member_count,
                    2,
                )

                team_draft = validate_team_draft(
                    "Equipe Fictícia Leste",
                    "Capitão Inventado",
                    "Azul",
                ).draft
                self.assertIsNotNone(team_draft)
                create_result = window.activities_page._create_team(
                    team_draft
                )
                self.assertTrue(create_result.succeeded)
                self.assertEqual(dashboard.last_snapshot.team_count, 3)

                created_team = teams.teams[-1]
                with patch(
                    "acamp.ui.pages.activities.confirm_destructive",
                    return_value=True,
                ):
                    window.activities_page._confirm_delete_team(created_team)
                self.assertEqual(dashboard.last_snapshot.team_count, 2)

                replacement = ParticipantLoadResult(
                    ParticipantLoadStatus.VALID,
                    (
                        _participant(
                            name="Participante Futuro Fictício",
                            inscription="adulto",
                            accommodation="cabine",
                            transportation="não",
                            payment=135,
                        ),
                    ),
                )
                window.set_participant_result(replacement)
                self.assertEqual(
                    dashboard.last_snapshot.participant_total,
                    1,
                )
                self.assertEqual(dashboard.last_snapshot.paid_count, 1)
            finally:
                window.close()

    def test_missing_sources_show_safe_values(self):
        missing_participants = ParticipantLoadResult(
            ParticipantLoadStatus.FILE_MISSING
        )
        window = MainWindow(
            missing_participants,
            InventoryService(),
            TeamService(),
        )
        try:
            dashboard = window.dashboard_page
            for key in ("participants", "paid", "pending", "inventory", "teams"):
                self.assertEqual(
                    dashboard.metric_cards[key].value_label.text(),
                    "—",
                )
            self.assertTrue(dashboard.warning_banner.isVisibleTo(dashboard))
            self.assertIn(
                "Dados de participantes indisponíveis.",
                dashboard.warning_banner.text(),
            )
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
