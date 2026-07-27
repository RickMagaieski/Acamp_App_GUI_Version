"""Phase 2D1 tests using only invented teams in temporary files."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox

from acamp.models import Team
from acamp.repositories import (
    TeamLoadStatus,
    TeamRepository,
    TeamSaveResult,
)
from acamp.services import TeamService, validate_team_draft
from acamp.ui.models import filter_teams
from acamp.ui.pages.activities import ActivitiesPage


class TeamRepositoryTests(unittest.TestCase):
    def _load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            path.write_text(text, encoding="utf-8")
            return TeamRepository(path).load()

    def test_valid_team_load(self):
        result = self._load_text(json.dumps([{
            "equipe": "Equipe Inventada",
            "lider": "Capitão Inventado",
            "cor": "Verde",
            "pessoas": [],
            "score": 0,
        }], ensure_ascii=False))
        self.assertEqual(result.status, TeamLoadStatus.VALID)
        self.assertEqual(result.teams[0].participant_count, 0)
        self.assertEqual(result.teams[0].score, 0)

    def test_missing_empty_invalid_and_non_list_states(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = TeamRepository(Path(directory) / "missing.json").load()
        self.assertEqual(missing.status, TeamLoadStatus.FILE_MISSING)
        self.assertEqual(self._load_text("").status, TeamLoadStatus.FILE_EMPTY)
        self.assertEqual(
            self._load_text("[invalid").status,
            TeamLoadStatus.INVALID_JSON,
        )
        self.assertEqual(
            self._load_text('{"times": []}').status,
            TeamLoadStatus.ROOT_NOT_LIST,
        )

    def test_malformed_records_and_fields_are_safe(self):
        result = self._load_text(json.dumps([
            "registro inválido",
            {
                "equipe": "Equipe Parcial",
                "pessoas": "inválido",
                "score": "inválido",
            },
        ], ensure_ascii=False))
        self.assertEqual(result.skipped_records, 1)
        self.assertEqual(result.teams[0].participant_count_display, "-")
        self.assertEqual(result.teams[0].score_display, "-")

    def test_atomic_save_and_failed_replace_preserve_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            original = '[{"equipe": "Equipe Original"}]'
            path.write_text(original, encoding="utf-8")
            repository = TeamRepository(path)
            with patch(
                "acamp.repositories.os.replace",
                side_effect=OSError("synthetic failure"),
            ):
                failed = repository.save([{"equipe": "Equipe Proposta"}])
            self.assertFalse(failed.succeeded)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

            saved = repository.save([{
                "equipe": "Equipe Nova",
                "lider": "Capitão Novo",
                "cor": "Azul",
                "pessoas": [],
                "score": 0,
            }])
            self.assertTrue(saved.succeeded)
            self.assertFalse(list(Path(directory).glob("*.tmp")))


class TeamServiceTests(unittest.TestCase):
    def test_validation_normalizes_and_requires_all_team_fields(self):
        invalid = validate_team_draft(" ", "", None)
        self.assertFalse(invalid.succeeded)
        self.assertEqual(
            set(invalid.errors),
            {"name", "leader", "color"},
        )
        valid = validate_team_draft(
            "  Equipe Inventada  ",
            "  Capitão Inventado  ",
            "  Verde  ",
        )
        self.assertTrue(valid.succeeded)
        self.assertEqual(valid.draft.name, "Equipe Inventada")

    def test_search_is_partial_and_case_insensitive(self):
        teams = (
            Team.from_mapping({"equipe": "Equipe Alfa"}, 0),
            Team.from_mapping({"equipe": "Equipe Beta"}, 1),
        )
        filtered = filter_teams(teams, "ALF")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Equipe Alfa")

    def test_create_starts_empty_and_delete_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            path.write_text("[]", encoding="utf-8")
            service = TeamService(TeamRepository(path))
            service.load()
            draft = validate_team_draft(
                "Equipe Inventada",
                "Capitão Inventado",
                "Verde",
            ).draft
            self.assertTrue(service.create_team(draft).succeeded)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted[0]["pessoas"], [])
            self.assertEqual(persisted[0]["score"], 0)
            self.assertEqual(len(service.teams), 1)

            self.assertTrue(
                service.delete_team(service.teams[0].source_index).succeeded
            )
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])

    def test_failed_create_keeps_state_and_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            original = "[]"
            path.write_text(original, encoding="utf-8")
            repository = TeamRepository(path)
            service = TeamService(repository)
            service.load()
            draft = validate_team_draft(
                "Equipe Proposta",
                "Capitão Proposto",
                "Laranja",
            ).draft
            with patch.object(
                repository,
                "save",
                return_value=TeamSaveResult(False),
            ):
                result = service.create_team(draft)
            self.assertFalse(result.succeeded)
            self.assertEqual(service.teams, ())
            self.assertEqual(path.read_text(encoding="utf-8"), original)


class ActivitiesPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self, path: Path) -> ActivitiesPage:
        path.write_text(json.dumps([{
            "equipe": "Equipe Inventada",
            "lider": "Capitão Inventado",
            "cor": "Verde",
            "pessoas": [],
            "score": 0,
        }], ensure_ascii=False), encoding="utf-8")
        service = TeamService(TeamRepository(path))
        service.load()
        return ActivitiesPage(service)

    def test_selection_and_phase_2d2_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            page = self._build_page(Path(directory) / "teams.json")
            index = page.table_model.index(0, 0)
            page._table_clicked(index)
            self.assertIsNotNone(page._selected_source_index)
            self.assertTrue(page.delete_selected_button.isEnabled())
            self.assertFalse(page.add_participant_button.isEnabled())
            self.assertFalse(page.remove_participant_button.isEnabled())
            self.assertFalse(page.points_button.isEnabled())

    def test_cancelled_and_confirmed_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teams.json"
            page = self._build_page(path)
            original = path.read_text(encoding="utf-8")
            team = page.table_model.team_at(0)
            with patch(
                "acamp.ui.pages.activities.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ):
                page._confirm_delete(team)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(page.table_model.rowCount(), 1)

            with patch(
                "acamp.ui.pages.activities.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                page._confirm_delete(team)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])
            self.assertEqual(page.table_model.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
