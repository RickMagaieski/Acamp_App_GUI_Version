"""Application-wide release-hardening tests with invented local data."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QWidget

from acamp.paths import ApplicationPaths, application_root
from acamp.repositories import (
    InventoryLoadStatus,
    ParticipantLoadStatus,
    TeamLoadStatus,
)
from acamp.sheets_gateway import GoogleSheetsGateway
from acamp.ui.widgets import MetricCard
import gui_main
from gui_main import create_application


def _write_invented_state(root: Path) -> None:
    (root / "participants.json").write_text(
        json.dumps([{
            "name": "pessoa fictícia",
            "age": 24,
            "phone": "000-000-0000",
            "medical": "",
            "transportation": "não",
            "email": "inventado@example.invalid",
            "accommodation": "cabine",
            "inscription": "adulto",
            "payment": 135,
            "food": "sim",
            "id": "ID-FICTICIO",
        }], ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "items.json").write_text(
        json.dumps([{
            "item": "Item Fictício",
            "quantity": 2,
            "value": 3.5,
            "description": "Registro inventado",
        }], ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "teams.json").write_text(
        json.dumps([{
            "equipe": "Equipe Fictícia",
            "lider": "Líder Fictício",
            "cor": "Verde",
            "pessoas": [{"participante": "Membro Fictício"}],
            "score": 7,
        }], ensure_ascii=False),
        encoding="utf-8",
    )


class RuntimePathTests(unittest.TestCase):
    def test_source_root_is_independent_of_working_directory(self):
        expected = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                self.assertEqual(application_root(), expected)
                self.assertEqual(
                    ApplicationPaths.from_runtime().root,
                    expected,
                )
            finally:
                os.chdir(previous)

    def test_packaged_root_uses_executable_directory(self):
        fake_executable = Path(tempfile.gettempdir()) / "app" / "acamp.exe"
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", str(fake_executable)),
        ):
            self.assertEqual(
                application_root(),
                fake_executable.resolve().parent,
            )

    def test_all_private_paths_are_centralized_below_runtime_root(self):
        root = Path(tempfile.gettempdir()) / "acamp-runtime"
        paths = ApplicationPaths(root)
        self.assertEqual(paths.participants_file, paths.root / "participants.json")
        self.assertEqual(paths.inventory_file, paths.root / "items.json")
        self.assertEqual(paths.teams_file, paths.root / "teams.json")
        self.assertEqual(
            paths.client_secret_file,
            paths.root / "client_secret.json",
        )
        self.assertEqual(paths.token_file, paths.root / "token.json")
        self.assertEqual(paths.assets_directory, paths.root / "assets")


class ReleaseApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _create_temp_application(self, root: Path):
        return create_application(
            application_paths=ApplicationPaths(root),
        )

    def test_smoke_entry_point_exits_cleanly_without_local_or_google_io(self):
        with (
            patch.object(sys, "argv", ["gui_main.py", "--smoke-test"]),
            patch.object(
                GoogleSheetsGateway,
                "_authenticate",
            ) as authenticate,
        ):
            self.assertEqual(gui_main.main(), 0)
        authenticate.assert_not_called()

    def test_local_state_is_loaded_before_window_is_returned_and_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_invented_state(root)
            with (
                patch.object(
                    GoogleSheetsGateway,
                    "download_participants",
                ) as download,
                patch.object(
                    GoogleSheetsGateway,
                    "delete_participant",
                ) as deletion,
                patch.object(
                    GoogleSheetsGateway,
                    "_authenticate",
                ) as authenticate,
            ):
                _app, window = self._create_temp_application(root)

            try:
                download.assert_not_called()
                deletion.assert_not_called()
                authenticate.assert_not_called()
                self.assertEqual(
                    window.finance_service.participant_result.status,
                    ParticipantLoadStatus.VALID,
                )
                self.assertEqual(
                    window.inventory_page._service.load_result.status,
                    InventoryLoadStatus.VALID,
                )
                self.assertEqual(
                    window.activities_page._service.load_result.status,
                    TeamLoadStatus.VALID,
                )
                self.assertEqual(
                    window.registrations_page.table_model.rowCount(),
                    1,
                )
                self.assertEqual(window.inventory_page.table_model.rowCount(), 1)
                self.assertEqual(window.activities_page.table_model.rowCount(), 1)
                self.assertEqual(window.current_page_index, 0)
            finally:
                window.close()

    def test_missing_and_invalid_files_are_visible_without_startup_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "items.json").write_text(
                "{json inválido",
                encoding="utf-8",
            )
            (root / "teams.json").write_text(
                '{"teams": []}',
                encoding="utf-8",
            )
            _app, window = self._create_temp_application(root)
            try:
                self.assertEqual(
                    window.finance_service.participant_result.status,
                    ParticipantLoadStatus.FILE_MISSING,
                )
                self.assertEqual(
                    window.inventory_page._service.load_result.status,
                    InventoryLoadStatus.INVALID_JSON,
                )
                self.assertEqual(
                    window.activities_page._service.load_result.status,
                    TeamLoadStatus.ROOT_NOT_LIST,
                )
                self.assertIn(
                    "não encontrado",
                    window.registrations_page.state_label.text(),
                )
                self.assertIn(
                    "Não foi possível",
                    window.inventory_page.state_label.text(),
                )
                self.assertIn(
                    "Não foi possível",
                    window.activities_page.team_state_label.text(),
                )
            finally:
                window.close()

    def test_navigation_reuses_six_pages_and_keeps_highlight_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_invented_state(root)
            _app, window = self._create_temp_application(root)
            try:
                original_pages = tuple(
                    window.page_stack.widget(index)
                    for index in range(window.page_stack.count())
                )
                self.assertEqual(len(original_pages), 6)
                self.assertEqual(len(set(map(id, original_pages))), 6)

                for index, button in enumerate(window.navigation_buttons):
                    button.click()
                    self.assertEqual(window.current_page_index, index)
                    self.assertTrue(button.isChecked())

                destinations = (
                    ("participants", 1),
                    ("paid", 2),
                    ("pending", 2),
                    ("inventory", 3),
                    ("teams", 4),
                )
                for key, page_index in destinations:
                    window.dashboard_page.metric_cards[key].clicked.emit()
                    self.assertEqual(window.current_page_index, page_index)
                    self.assertTrue(
                        window.navigation_buttons[page_index].isChecked()
                    )

                window.dashboard_page.reports_button.click()
                self.assertEqual(window.current_page_index, 5)
                window.dashboard_page.activities_button.click()
                self.assertEqual(window.current_page_index, 4)
                self.assertEqual(window.page_stack.count(), 6)
                self.assertEqual(
                    original_pages,
                    tuple(
                        window.page_stack.widget(index)
                        for index in range(window.page_stack.count())
                    ),
                )
            finally:
                window.close()

    def test_navigation_and_dashboard_reads_do_not_write_local_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_invented_state(root)
            paths = ApplicationPaths(root)
            private_paths = (
                paths.participants_file,
                paths.inventory_file,
                paths.teams_file,
            )
            originals = {
                path: path.read_bytes()
                for path in private_paths
            }
            _app, window = create_application(application_paths=paths)
            try:
                for _round in range(3):
                    for index in range(6):
                        window.navigate_to(index)
                window.dashboard_page.refresh_from_service()
                window.finance_page.refresh_from_service()
                window.reports_page.refresh_from_service()
            finally:
                window.close()

            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_minimum_window_size_keeps_sidebar_and_pages_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_invented_state(root)
            _app, window = self._create_temp_application(root)
            try:
                window.resize(window.minimumSize())
                window.show()
                QApplication.processEvents()
                sidebar = window.findChild(QWidget, "sidebar")
                content = window.findChild(QWidget, "contentPanel")
                self.assertIsNotNone(sidebar)
                self.assertIsNotNone(content)
                self.assertLess(sidebar.geometry().right(), content.geometry().left())
                for index in range(6):
                    window.navigate_to(index)
                    QApplication.processEvents()
                    page = window.page_stack.currentWidget()
                    self.assertGreater(page.viewport().width(), 0)
                    self.assertEqual(
                        page.horizontalScrollBarPolicy(),
                        Qt.ScrollBarPolicy.ScrollBarAsNeeded,
                    )
            finally:
                window.close()

    def test_dashboard_metric_card_is_keyboard_accessible(self):
        card = MetricCard("Métrica")
        activations = []
        card.clicked.connect(lambda: activations.append(True))
        card.set_clickable("Abrir destino")
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(card, event)
        self.assertEqual(activations, [True])


if __name__ == "__main__":
    unittest.main()
