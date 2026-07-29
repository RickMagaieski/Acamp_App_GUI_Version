"""Phase 2E report tests using invented in-memory and temporary data."""

from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLabel

from acamp.models import Participant, Team
from acamp.pricing import PaymentStatus, calculate_financial_snapshot
from acamp.reporting import (
    ACCOMMODATION_LABELS,
    AGE_GROUP_LABELS,
    FOOD_LABELS,
    PAYMENT_STATUS_LABELS,
    TRANSPORTATION_LABELS,
    build_report_snapshot,
    rank_teams,
)
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantLoadStatus,
    TeamRepository,
)
from acamp.services import (
    FinanceService,
    InventoryService,
    ReportingService,
    TeamService,
    validate_inventory_draft,
    validate_team_draft,
)
from acamp.ui.main_window import MainWindow


def _participant(**values) -> Participant:
    return Participant.from_mapping(values)


def _counts(entries) -> dict[str, int]:
    return {entry.label: entry.count for entry in entries}


def _report_for(participants=(), teams=()):
    financial = calculate_financial_snapshot(participants, ())
    return build_report_snapshot(participants, financial, teams)


class ParticipantAggregationTests(unittest.TestCase):
    def test_age_boundaries_are_mutually_exclusive(self):
        ages = (
            0, 5, 6, 12, 13, 17, 18, 29, 30, 59, 60,
            -1, "", "idade inválida", "12.5",
        )
        participants = tuple(
            _participant(name=f"Pessoa Fictícia {index}", age=age)
            for index, age in enumerate(ages)
        )

        snapshot = _report_for(participants)
        counts = _counts(snapshot.age_groups)

        self.assertEqual(
            counts,
            {
                AGE_GROUP_LABELS[0]: 2,
                AGE_GROUP_LABELS[1]: 2,
                AGE_GROUP_LABELS[2]: 2,
                AGE_GROUP_LABELS[3]: 2,
                AGE_GROUP_LABELS[4]: 2,
                AGE_GROUP_LABELS[5]: 1,
                AGE_GROUP_LABELS[6]: 4,
            },
        )
        self.assertEqual(sum(counts.values()), len(participants))
        self.assertEqual(snapshot.participant_total, len(participants))

    def test_food_normalization_does_not_invent_diet_labels(self):
        participants = (
            _participant(food=" SIM "),
            _participant(food="não"),
            _participant(food="NAO"),
            _participant(food="resposta livre"),
            _participant(food=""),
        )
        counts = _counts(_report_for(participants).food_categories)
        self.assertEqual(counts[FOOD_LABELS[0]], 1)
        self.assertEqual(counts[FOOD_LABELS[1]], 2)
        self.assertEqual(counts[FOOD_LABELS[2]], 2)
        self.assertNotIn("Vegano", counts)
        self.assertNotIn("Vegetariano", counts)

    def test_accommodation_normalization_preserves_unknowns(self):
        participants = tuple(
            _participant(accommodation=value)
            for value in (" barraca ", "RV", "Cabine", "FLAG", "", "outro")
        )
        counts = _counts(
            _report_for(participants).accommodation_categories
        )
        self.assertEqual(
            counts,
            {
                ACCOMMODATION_LABELS[0]: 1,
                ACCOMMODATION_LABELS[1]: 1,
                ACCOMMODATION_LABELS[2]: 1,
                ACCOMMODATION_LABELS[3]: 1,
                ACCOMMODATION_LABELS[4]: 2,
            },
        )

    def test_transportation_normalization_preserves_unknowns(self):
        participants = tuple(
            _participant(transportation=value)
            for value in ("sim", "Não", "nao", "", "talvez")
        )
        counts = _counts(
            _report_for(participants).transportation_categories
        )
        self.assertEqual(counts[TRANSPORTATION_LABELS[0]], 1)
        self.assertEqual(counts[TRANSPORTATION_LABELS[1]], 2)
        self.assertEqual(counts[TRANSPORTATION_LABELS[2]], 2)

    def test_payment_counts_come_from_central_finance_snapshot(self):
        participants = (
            _participant(
                inscription="adulto",
                accommodation="cabine",
                payment=135,
            ),
            _participant(
                inscription="criança",
                accommodation="cabine",
                payment=10,
            ),
            _participant(
                inscription="sábado adulto",
                accommodation="cabine",
                payment=0,
            ),
            _participant(
                inscription="adulto",
                accommodation="flag",
                payment=0,
            ),
            _participant(
                inscription="tipo desconhecido",
                accommodation="cabine",
                payment=5,
            ),
        )
        financial = calculate_financial_snapshot(participants, ())
        report = build_report_snapshot(participants, financial, ())
        report_counts = _counts(report.payment_statuses)

        for status in PaymentStatus:
            self.assertEqual(
                report_counts[PAYMENT_STATUS_LABELS[status]],
                financial.status_counts[status],
            )

    def test_empty_and_unclassified_datasets_are_safe(self):
        empty = _report_for()
        self.assertEqual(empty.participant_total, 0)
        self.assertEqual(sum(_counts(empty.age_groups).values()), 0)
        self.assertEqual(empty.team_ranking, ())

        unknown = build_report_snapshot(
            (_participant(age="?", food="?", accommodation="?", transportation="?"),),
            calculate_financial_snapshot(
                (_participant(inscription="?", payment="?"),),
                (),
            ),
            (),
            skipped_participant_records=1,
        )
        self.assertTrue(unknown.has_unclassified_records)


class TeamRankingTests(unittest.TestCase):
    @staticmethod
    def _team(index: int, name: str, score) -> Team:
        return Team.from_mapping(
            {
                "equipe": name,
                "lider": "Capitão Fictício",
                "cor": "Cor Fictícia",
                "pessoas": [],
                "score": score,
            },
            index,
        )

    def test_ranking_handles_ties_negative_and_malformed_scores(self):
        teams = (
            self._team(0, "Equipe Fictícia Um", -3),
            self._team(1, "Equipe Fictícia Dois", 7),
            self._team(2, "Equipe Fictícia Três", 7),
            self._team(3, "Equipe Fictícia Quatro", "inválido"),
        )
        original_order = tuple(team.name for team in teams)

        ranking = rank_teams(teams)

        self.assertEqual(
            [entry.team.score_value for entry in ranking],
            [7, 7, 0, -3],
        )
        self.assertEqual(
            [entry.position for entry in ranking],
            [1, 1, 3, 4],
        )
        self.assertEqual(tuple(team.name for team in teams), original_order)


class ReportingServiceTests(unittest.TestCase):
    def test_financial_totals_match_finance_service_exactly(self):
        participants = (
            _participant(
                name="Pessoa Fictícia",
                inscription="adulto",
                accommodation="cabine",
                payment=135,
            ),
        )
        participant_result = ParticipantLoadResult(
            ParticipantLoadStatus.VALID,
            participants,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "items.json").write_text(
                json.dumps([{
                    "item": "Item Fictício",
                    "quantity": 2,
                    "value": 4.25,
                    "description": "",
                }]),
                encoding="utf-8",
            )
            (root / "teams.json").write_text("[]", encoding="utf-8")
            inventory = InventoryService(
                InventoryRepository(root / "items.json")
            )
            teams = TeamService(TeamRepository(root / "teams.json"))
            inventory.load()
            teams.load()
            finance = FinanceService(participant_result, inventory)
            reporting = ReportingService(finance, teams)

            financial = finance.snapshot()
            report = reporting.snapshot()

            self.assertEqual(report.financial.entries, financial.entries)
            self.assertEqual(report.financial.expenses, financial.expenses)
            self.assertEqual(
                report.financial.event_result,
                financial.event_result,
            )
            self.assertEqual(
                report.financial.available_balance,
                financial.available_balance,
            )
            self.assertFalse(hasattr(report.financial, "payments"))


class ReportsApplicationStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_existing_mutations_refresh_reports_without_restart(self):
        participant_name = "Pessoa Fictícia Privada"
        participant = _participant(
            name=participant_name,
            age=24,
            food="sim",
            accommodation="cabine",
            transportation="não",
            inscription="adulto",
            payment=135,
        )
        participant_result = ParticipantLoadResult(
            ParticipantLoadStatus.VALID,
            (participant,),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory_path = root / "items.json"
            team_path = root / "teams.json"
            inventory_path.write_text("[]", encoding="utf-8")
            team_path.write_text(
                json.dumps([
                    {
                        "equipe": "Equipe Fictícia Norte",
                        "lider": "Capitão Fictício",
                        "cor": "Verde",
                        "pessoas": [],
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
            inventory = InventoryService(
                InventoryRepository(inventory_path)
            )
            teams = TeamService(TeamRepository(team_path))
            inventory.load()
            teams.load()
            window = MainWindow(participant_result, inventory, teams)
            try:
                for chart_card in (
                    window.reports_page.age_chart,
                    window.reports_page.food_chart,
                    window.reports_page.accommodation_chart,
                    window.reports_page.transportation_chart,
                    window.reports_page.payment_chart,
                    window.reports_page.team_chart,
                ):
                    self.assertFalse(chart_card.chart_view.isHidden())
                    self.assertEqual(
                        len(chart_card.chart_view.chart().series()),
                        1,
                    )

                self.assertEqual(
                    window.reports_page.last_snapshot.financial.expenses,
                    Decimal("0.00"),
                )

                inventory_draft = validate_inventory_draft(
                    "Item Temporário Fictício",
                    "4.50",
                    2,
                ).draft
                self.assertIsNotNone(inventory_draft)
                inventory_result = window.inventory_page._add_item(
                    inventory_draft
                )
                self.assertTrue(inventory_result.succeeded)
                self.assertEqual(
                    window.reports_page.last_snapshot.financial.expenses,
                    Decimal("9.00"),
                )
                self.assertEqual(
                    window.reports_page.financial_labels["expenses"].text(),
                    window.finance_page.summary_labels["expenses"].text(),
                )

                first_team = teams.teams[0]
                window.activities_page._select_team(first_team)
                score_result = window.activities_page._change_score(5)
                self.assertTrue(score_result.succeeded)
                self.assertEqual(
                    window.reports_page.last_snapshot.team_ranking[0]
                    .team.name,
                    "Equipe Fictícia Norte",
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
                self.assertEqual(
                    len(window.reports_page.last_snapshot.team_ranking),
                    3,
                )

                created_team = teams.teams[-1]
                with patch(
                    "acamp.ui.pages.activities.confirm_destructive",
                    return_value=True,
                ):
                    window.activities_page._confirm_delete_team(created_team)
                self.assertEqual(
                    len(window.reports_page.last_snapshot.team_ranking),
                    2,
                )

                visible_report_text = "\n".join(
                    label.text()
                    for label in window.reports_page.findChildren(QLabel)
                )
                self.assertNotIn(participant_name, visible_report_text)
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
