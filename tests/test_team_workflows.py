"""Team member, score, and ranking tests with invented data only."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from acamp.models import Team
from acamp.repositories import TeamRepository, TeamSaveResult
from acamp.reporting import rank_teams
from acamp.services import (
    TeamService,
    validate_score_amount,
    validate_team_member_name,
)
from acamp.ui.pages.activities import ActivitiesPage


def _team_record(
    name: str,
    *,
    members=None,
    score=0,
) -> dict:
    record = {
        "equipe": name,
        "lider": "Capitão Inventado",
        "cor": "Verde",
        "score": score,
    }
    if members is not None:
        record["pessoas"] = [
            {"participante": member} for member in members
        ]
    return record


class TeamMemberServiceTests(unittest.TestCase):
    def _service(self, path: Path, records: list) -> TeamService:
        path.write_text(
            json.dumps(records, ensure_ascii=False),
            encoding="utf-8",
        )
        service = TeamService(TeamRepository(path))
        service.load()
        return service

    def test_add_member_to_existing_and_missing_people_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            service = self._service(
                path,
                [_team_record("Equipe Inventada")],
            )
            draft = validate_team_member_name("  Pessoa Inventada  ").draft
            result = service.add_member(0, draft)
            self.assertTrue(result.succeeded)
            self.assertEqual(service.teams[0].members[0].name, "Pessoa Inventada")
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                persisted[0]["pessoas"],
                [{"participante": "Pessoa Inventada"}],
            )

    def test_duplicate_names_remain_and_one_selected_row_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            service = self._service(
                path,
                [_team_record(
                    "Equipe Inventada",
                    members=["Pessoa Repetida", "Pessoa Repetida"],
                )],
            )
            result = service.remove_member(0, 0)
            self.assertTrue(result.succeeded)
            self.assertEqual(len(service.teams[0].members), 1)
            self.assertEqual(
                service.teams[0].members[0].name,
                "Pessoa Repetida",
            )

    def test_malformed_people_list_is_preserved_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            original_records = [{
                "equipe": "Equipe Parcial",
                "lider": "Capitão",
                "cor": "Azul",
                "pessoas": "formato inválido",
                "score": 0,
            }]
            service = self._service(path, original_records)
            draft = validate_team_member_name("Pessoa Proposta").draft
            result = service.add_member(0, draft)
            self.assertFalse(result.succeeded)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                original_records,
            )

    def test_failed_member_save_preserves_live_and_file_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            records = [_team_record(
                "Equipe Inventada",
                members=["Pessoa Original"],
            )]
            repository = TeamRepository(path)
            path.write_text(json.dumps(records), encoding="utf-8")
            service = TeamService(repository)
            service.load()
            original_members = service.teams[0].members
            draft = validate_team_member_name("Pessoa Proposta").draft
            with patch.object(
                repository,
                "save",
                return_value=TeamSaveResult(False),
            ):
                result = service.add_member(0, draft)
            self.assertFalse(result.succeeded)
            self.assertEqual(service.teams[0].members, original_members)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                records,
            )

    def test_member_name_validation(self):
        self.assertFalse(validate_team_member_name("   ").succeeded)
        valid = validate_team_member_name("  Pessoa Inventada  ")
        self.assertTrue(valid.succeeded)
        self.assertEqual(valid.draft.name, "Pessoa Inventada")


class TeamScoreTests(unittest.TestCase):
    def test_add_remove_and_allow_below_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            path.write_text(
                json.dumps([_team_record(
                    "Equipe Inventada",
                    members=[],
                    score=100,
                )]),
                encoding="utf-8",
            )
            service = TeamService(TeamRepository(path))
            service.load()
            self.assertTrue(service.change_score(0, 25).succeeded)
            self.assertEqual(service.teams[0].score, 125)
            self.assertTrue(service.change_score(0, -40).succeeded)
            self.assertEqual(service.teams[0].score, 85)
            self.assertTrue(service.change_score(0, -100).succeeded)
            self.assertEqual(service.teams[0].score, -15)

    def test_score_input_validation(self):
        for invalid in ("", "0", "-2", "1.5", "texto"):
            self.assertFalse(validate_score_amount(invalid).succeeded)
        self.assertEqual(validate_score_amount("25").amount, 25)

    def test_malformed_score_uses_zero_only_after_explicit_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            records = [_team_record(
                "Equipe Parcial",
                members=[],
                score="inválido",
            )]
            path.write_text(json.dumps(records), encoding="utf-8")
            service = TeamService(TeamRepository(path))
            service.load()
            self.assertEqual(service.teams[0].score_value, 0)
            self.assertTrue(service.change_score(0, 5).succeeded)
            self.assertEqual(service.teams[0].score, 5)

    def test_failed_score_save_preserves_previous_score(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            records = [_team_record(
                "Equipe Inventada",
                members=[],
                score=10,
            )]
            path.write_text(json.dumps(records), encoding="utf-8")
            repository = TeamRepository(path)
            service = TeamService(repository)
            service.load()
            with patch.object(
                repository,
                "save",
                return_value=TeamSaveResult(False),
            ):
                result = service.change_score(0, 5)
            self.assertFalse(result.succeeded)
            self.assertEqual(service.teams[0].score, 10)


class TeamRankingTests(unittest.TestCase):
    def test_ranking_is_descending_and_ties_are_stable(self):
        teams = (
            Team.from_mapping(_team_record("Equipe Um", score=10), 0),
            Team.from_mapping(_team_record("Equipe Dois", score=30), 1),
            Team.from_mapping(_team_record("Equipe Três", score=30), 2),
            Team.from_mapping(_team_record("Equipe Quatro", score=-5), 3),
        )
        ranking = rank_teams(teams)
        self.assertEqual(
            [entry.team.source_index for entry in ranking],
            [1, 2, 0, 3],
        )
        self.assertEqual(
            [entry.position for entry in ranking],
            [1, 1, 3, 4],
        )


class ActivitiesWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _page(self, path: Path) -> ActivitiesPage:
        path.write_text(
            json.dumps([_team_record(
                "Equipe Inventada",
                members=["Pessoa Repetida", "Pessoa Repetida"],
                score=10,
            )], ensure_ascii=False),
            encoding="utf-8",
        )
        service = TeamService(TeamRepository(path))
        service.load()
        page = ActivitiesPage(service)
        page._team_table_clicked(page.table_model.index(0, 0))
        return page

    def test_no_selected_team_disables_member_and_score_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            page = self._page(Path(directory) / "teams.json")
            page._clear_team_selection()
            self.assertFalse(page.add_participant_button.isEnabled())
            self.assertFalse(page.remove_participant_button.isEnabled())
            self.assertFalse(page.add_points_button.isEnabled())
            self.assertFalse(page.remove_points_button.isEnabled())

    def test_add_member_and_score_preserve_selected_team_and_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            page = self._page(Path(directory) / "teams.json")
            selected = page._selected_source_index
            draft = validate_team_member_name("Pessoa Nova").draft
            self.assertTrue(page._add_member(draft).succeeded)
            self.assertEqual(page._selected_source_index, selected)
            self.assertEqual(page.member_model.rowCount(), 3)

            self.assertTrue(page._change_score(15).succeeded)
            self.assertEqual(page._selected_source_index, selected)
            self.assertIn("25", page.selected_score_label.text())
            self.assertEqual(
                page.ranking_model.entry_at(0).team.score,
                25,
            )

    def test_cancel_then_remove_exactly_one_selected_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            page = self._page(path)
            page._member_table_clicked(page.member_model.index(0, 1))
            original = path.read_text(encoding="utf-8")
            with patch(
                "acamp.ui.pages.activities.confirm_destructive",
                return_value=False,
            ):
                page._remove_selected_member()
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(page.member_model.rowCount(), 2)

            with patch(
                "acamp.ui.pages.activities.confirm_destructive",
                return_value=True,
            ):
                page._remove_selected_member()
            self.assertEqual(page.member_model.rowCount(), 1)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(persisted[0]["pessoas"]), 1)


if __name__ == "__main__":
    unittest.main()
