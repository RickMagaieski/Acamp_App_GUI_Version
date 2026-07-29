"""Phase 3B tests with invented records and fake Google services only."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from acamp.config import GoogleSheetsConfig
from acamp.repositories import (
    ParticipantRepository,
    ParticipantSaveResult,
    participant_result_from_records,
)
from acamp.services import (
    InventoryService,
    ParticipantDeletionResult,
    ParticipantDeletionService,
    ParticipantSynchronizationResult,
    TeamService,
)
from acamp.sheets_gateway import (
    GoogleSheetsGateway,
    SheetsGatewayError,
)
from acamp.ui.main_window import MainWindow
from acamp.ui.models import ParticipantTableModel
from acamp.ui.pages.registrations import RegistrationsPage
from gui_main import create_application


def _record(
    name: str,
    participant_id: str,
    *,
    payment: int = 0,
) -> dict:
    return {
        "name": name,
        "age": 20,
        "phone": "000-000-0000",
        "medical": "",
        "transportation": "não",
        "email": "inventado@example.invalid",
        "accommodation": "cabine",
        "inscription": "adulto",
        "payment": payment,
        "food": "não",
        "id": participant_id,
    }


def _sheet_row(participant_id: str) -> list[str]:
    row = [""] * 14
    row[0] = "Pessoa"
    row[1] = "Fictícia"
    row[13] = participant_id
    return row


class _FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FakeSheetsService:
    def __init__(self, values, *, title="Sheet1", sheet_id=73):
        self.values_payload = {"values": values}
        self.metadata_payload = {
            "sheets": [{
                "properties": {
                    "title": title,
                    "sheetId": sheet_id,
                }
            }]
        }
        self.batch_calls: list[dict] = []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, **kwargs):
        if "range" in kwargs:
            return _FakeRequest(self.values_payload)
        return _FakeRequest(self.metadata_payload)

    def batchUpdate(self, **kwargs):  # noqa: N802
        self.batch_calls.append(kwargs)
        return _FakeRequest({"replies": [{}]})


class GoogleRowDeletionTests(unittest.TestCase):
    def _gateway(self, service):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        gateway = GoogleSheetsGateway(
            GoogleSheetsConfig(Path(temporary.name))
        )
        patcher = patch.object(
            gateway,
            "_create_service",
            return_value=service,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return gateway

    def test_matches_exact_normalized_id_and_deletes_one_row(self):
        service = _FakeSheetsService([
            ["Cabeçalho"],
            _sheet_row("ID-FICTICIO-A"),
            _sheet_row("ID-FICTICIO-B"),
        ])
        gateway = self._gateway(service)

        result = gateway.delete_participant("  ID-FICTICIO-B  ")

        self.assertEqual(result.deleted_row_number, 3)
        self.assertEqual(result.deleted_count, 1)
        self.assertEqual(len(service.batch_calls), 1)
        request = service.batch_calls[0]["body"]["requests"]
        self.assertEqual(len(request), 1)
        row_range = request[0]["deleteDimension"]["range"]
        self.assertEqual(row_range["sheetId"], 73)
        self.assertEqual(row_range["dimension"], "ROWS")
        self.assertEqual(row_range["startIndex"], 2)
        self.assertEqual(row_range["endIndex"], 3)

    def test_id_matching_is_case_sensitive(self):
        service = _FakeSheetsService([
            ["Cabeçalho"],
            _sheet_row("ID-EXATO"),
        ])
        gateway = self._gateway(service)

        with self.assertRaises(SheetsGatewayError) as context:
            gateway.delete_participant("id-exato")

        self.assertEqual(
            context.exception.technical_code,
            "participant_not_found",
        )
        self.assertEqual(service.batch_calls, [])

    def test_remote_not_found_does_not_issue_delete_request(self):
        service = _FakeSheetsService([
            ["Cabeçalho"],
            _sheet_row("OUTRO-ID"),
        ])
        gateway = self._gateway(service)

        with self.assertRaises(SheetsGatewayError) as context:
            gateway.delete_participant("ID-AUSENTE")

        self.assertIn(
            "não foi encontrada no Google Sheets",
            context.exception.user_message,
        )
        self.assertEqual(service.batch_calls, [])

    def test_missing_sheet_tab_is_controlled(self):
        service = _FakeSheetsService(
            [["Cabeçalho"], _sheet_row("ID-ALVO")],
            title="Outra página",
        )
        gateway = self._gateway(service)

        with self.assertRaises(SheetsGatewayError) as context:
            gateway.delete_participant("ID-ALVO")

        self.assertEqual(context.exception.technical_code, "sheet_tab_not_found")
        self.assertEqual(service.batch_calls, [])


class _FakeDeletionGateway:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list[str] = []

    def delete_participant(self, participant_id: str):
        self.calls.append(participant_id)
        if self.error is not None:
            raise self.error


class ParticipantDeletionServiceTests(unittest.TestCase):
    def test_duplicate_names_delete_only_selected_id_and_source_record(self):
        records = [
            _record("mesmo nome fictício", "ID-UM"),
            _record("mesmo nome fictício", "ID-DOIS"),
        ]
        current = participant_result_from_records(records)
        gateway = _FakeDeletionGateway()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            path.write_text(
                json.dumps(records, ensure_ascii=False),
                encoding="utf-8",
            )
            service = ParticipantDeletionService(
                gateway,
                ParticipantRepository(path),
            )

            result = service.delete(current.participants[1], current)

            self.assertTrue(result.succeeded)
            self.assertEqual(gateway.calls, ["ID-DOIS"])
            saved_records = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved_records), 1)
            self.assertEqual(saved_records[0]["id"], "ID-UM")
            self.assertEqual(
                result.participant_result.participants[0].participant_id,
                "ID-UM",
            )

    def test_missing_id_never_calls_remote_or_saves_locally(self):
        records = [_record("pessoa sem id", "")]
        current = participant_result_from_records(records)
        gateway = _FakeDeletionGateway()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            original = json.dumps(records, ensure_ascii=False)
            path.write_text(original, encoding="utf-8")
            service = ParticipantDeletionService(
                gateway,
                ParticipantRepository(path),
            )

            result = service.delete(current.participants[0], current)

            self.assertFalse(result.succeeded)
            self.assertEqual(result.technical_code, "participant_id_missing")
            self.assertEqual(gateway.calls, [])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_remote_failure_preserves_local_file_and_state(self):
        records = [_record("pessoa fictícia", "ID-LOCAL")]
        current = participant_result_from_records(records)
        gateway = _FakeDeletionGateway(SheetsGatewayError(
            "Esta inscrição não foi encontrada no Google Sheets.",
            "participant_not_found",
        ))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            original = json.dumps(records, ensure_ascii=False)
            path.write_text(original, encoding="utf-8")
            result = ParticipantDeletionService(
                gateway,
                ParticipantRepository(path),
            ).delete(current.participants[0], current)

            self.assertFalse(result.succeeded)
            self.assertFalse(result.remote_deleted)
            self.assertIsNone(result.participant_result)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_local_save_failure_returns_proposed_remote_truth(self):
        records = [
            _record("pessoa fictícia um", "ID-UM"),
            _record("pessoa fictícia dois", "ID-DOIS"),
        ]
        current = participant_result_from_records(records)
        gateway = _FakeDeletionGateway()

        with tempfile.TemporaryDirectory() as directory:
            repository = ParticipantRepository(
                Path(directory) / "participants.json"
            )
            with patch.object(
                repository,
                "save",
                return_value=ParticipantSaveResult(
                    False,
                    "invented_save_failure",
                ),
            ):
                result = ParticipantDeletionService(
                    gateway,
                    repository,
                ).delete(current.participants[0], current)

        self.assertFalse(result.succeeded)
        self.assertTrue(result.partially_succeeded)
        self.assertTrue(result.remote_deleted)
        self.assertTrue(result.requires_reconciliation)
        self.assertEqual(
            tuple(
                participant.participant_id
                for participant in result.participant_result.participants
            ),
            ("ID-DOIS",),
        )


class RegistrationsPageDeletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_id_is_hidden_and_search_maps_action_to_source_participant(self):
        state = participant_result_from_records([
            _record("alvo zulu", "ID-Z"),
            _record("outra pessoa", "ID-O"),
            _record("alvo alfa", "ID-A"),
        ])
        page = RegistrationsPage(state)
        requested = []
        page.deletion_requested.connect(requested.append)
        page.search_field.setText("alvo")
        page.table_view.sortByColumn(
            0,
            Qt.SortOrder.DescendingOrder,
        )
        QApplication.processEvents()

        self.assertNotIn("ID", page.table_model.HEADERS)
        self.assertEqual(page.table_model.columnCount(), 8)
        selected = page.table_model.participant_at(0)
        self.assertEqual(selected.participant_id, "ID-Z")
        with patch.object(page, "_confirm_deletion", return_value=True):
            page._on_table_clicked(
                page.table_model.index(
                    0,
                    ParticipantTableModel.ACTION_COLUMN,
                )
            )

        self.assertEqual(len(requested), 1)
        self.assertEqual(requested[0].source_index, 0)
        page.close()

    def test_cancelled_confirmation_emits_nothing(self):
        state = participant_result_from_records([
            _record("pessoa fictícia", "ID-CANCELAR"),
        ])
        page = RegistrationsPage(state)
        requested = []
        page.deletion_requested.connect(requested.append)

        with patch.object(page, "_confirm_deletion", return_value=False):
            page._on_table_clicked(
                page.table_model.index(
                    0,
                    ParticipantTableModel.ACTION_COLUMN,
                )
            )

        self.assertEqual(requested, [])
        page.close()

    def test_pagination_clamps_and_search_text_survives_state_replacement(self):
        records = [
            _record(f"pessoa fictícia {index:02d}", f"ID-{index:02d}")
            for index in range(11)
        ]
        page = RegistrationsPage(participant_result_from_records(records))
        page.search_field.setText("pessoa fictícia")
        page._next_page()
        self.assertEqual(page._page_index, 1)
        self.assertEqual(
            page.table_model.participant_at(0).source_index,
            10,
        )

        page.set_load_result(participant_result_from_records(records[:10]))

        self.assertEqual(page.search_field.text(), "pessoa fictícia")
        self.assertEqual(page._page_index, 0)
        self.assertEqual(page.table_model.rowCount(), 10)
        page.close()


class _ImmediateDeletionService:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def delete(self, _participant, _current_result):
        self.calls += 1
        return self.result


class _BlockingDeletionService(_ImmediateDeletionService):
    def __init__(self, result):
        super().__init__(result)
        self.started = threading.Event()
        self.release = threading.Event()

    def delete(self, _participant, _current_result):
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=2)
        return self.result


class _BlockingSynchronizationService:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()

    def local_cache_requires_replacement_confirmation(self):
        return False

    def synchronize(self, **_options):
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=2)
        return self.result


class DeletionApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _wait_until(predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            QApplication.processEvents()
            time.sleep(0.005)
        QApplication.processEvents()
        if not predicate():
            raise AssertionError("Timed out waiting for Qt worker")

    @staticmethod
    def _window(state, deletion_service, synchronization_service=None):
        return MainWindow(
            state,
            InventoryService(),
            TeamService(),
            synchronization_service,
            deletion_service,
        )

    def test_startup_never_calls_remote_deletion(self):
        with patch.object(
            GoogleSheetsGateway,
            "delete_participant",
        ) as deletion:
            _app, window = create_application(
                load_participants=False,
                load_inventory=False,
                load_teams=False,
            )
            QApplication.processEvents()
            deletion.assert_not_called()
            window.close()

    def test_complete_success_refreshes_every_participant_dependent_page(self):
        current = participant_result_from_records([
            _record("pessoa fictícia um", "ID-UM", payment=135),
            _record("pessoa fictícia dois", "ID-DOIS"),
        ])
        proposed = participant_result_from_records(current.records[1:])
        result = ParticipantDeletionResult(
            succeeded=True,
            message="A inscrição foi removida com sucesso.",
            participant_result=proposed,
            remote_deleted=True,
            local_saved=True,
        )
        service = _ImmediateDeletionService(result)
        window = self._window(current, service)
        state_changes = []
        window.participant_state_changed.connect(state_changes.append)

        try:
            with patch(
                "acamp.ui.pages.registrations.QMessageBox.information"
            ) as information:
                window._start_participant_deletion(
                    current.participants[0]
                )
                self._wait_until(
                    lambda: window._deletion_thread is None
                )

            information.assert_called_once()
            self.assertEqual(service.calls, 1)
            self.assertEqual(
                window.finance_service.participant_result,
                proposed,
            )
            self.assertEqual(window.registrations_page.table_model.rowCount(), 1)
            self.assertEqual(
                window.dashboard_page.last_snapshot.participant_total,
                1,
            )
            self.assertEqual(
                window.reports_page.last_snapshot.participant_total,
                1,
            )
            self.assertEqual(len(state_changes), 1)
        finally:
            window.close()

    def test_partial_success_updates_memory_and_requires_reconciliation(self):
        current = participant_result_from_records([
            _record("pessoa fictícia um", "ID-UM"),
            _record("pessoa fictícia dois", "ID-DOIS"),
        ])
        proposed = participant_result_from_records(current.records[1:])
        result = ParticipantDeletionResult(
            succeeded=False,
            message=ParticipantDeletionService.PARTIAL_SUCCESS_MESSAGE,
            participant_result=proposed,
            remote_deleted=True,
            local_saved=False,
            requires_reconciliation=True,
            technical_code="invented_save_failure",
        )
        window = self._window(
            current,
            _ImmediateDeletionService(result),
        )

        with (
            patch(
                "acamp.ui.pages.registrations.QMessageBox.warning"
            ) as warning,
            patch(
                "acamp.ui.main_window.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ),
        ):
            window._start_participant_deletion(current.participants[0])
            self._wait_until(lambda: window._deletion_thread is None)

            warning.assert_called_once()
            self.assertTrue(
                window.participant_cache_requires_reconciliation
            )
            self.assertEqual(
                window.finance_service.participant_result,
                proposed,
            )
            self.assertTrue(window.dashboard_page.sync_button.isEnabled())
            self.assertFalse(window.registrations_page.table_view.isEnabled())
            self.assertFalse(
                window.registrations_page.cache_warning_label.isHidden()
            )
            window.close()

    def test_deletion_blocks_duplicate_and_synchronization_attempts(self):
        current = participant_result_from_records([
            _record("pessoa fictícia um", "ID-UM"),
            _record("pessoa fictícia dois", "ID-DOIS"),
        ])
        proposed = participant_result_from_records(current.records[1:])
        deletion = _BlockingDeletionService(ParticipantDeletionResult(
            succeeded=True,
            message="ok",
            participant_result=proposed,
            remote_deleted=True,
            local_saved=True,
        ))
        synchronization = _BlockingSynchronizationService(
            ParticipantSynchronizationResult(
                succeeded=True,
                message="ok",
                participant_result=current,
            )
        )
        window = self._window(current, deletion, synchronization)

        try:
            with patch(
                "acamp.ui.pages.registrations.QMessageBox.information"
            ):
                window._start_participant_deletion(current.participants[0])
                self.assertTrue(deletion.started.wait(timeout=1))
                QApplication.processEvents()

                window._start_participant_deletion(
                    current.participants[0]
                )
                window._start_participant_sync()
                self.assertEqual(deletion.calls, 1)
                self.assertEqual(synchronization.calls, 0)
                self.assertFalse(window.dashboard_page.sync_button.isEnabled())

                deletion.release.set()
                self._wait_until(
                    lambda: window._deletion_thread is None
                )
        finally:
            deletion.release.set()
            window.close()

    def test_synchronization_blocks_deletion_attempt(self):
        current = participant_result_from_records([
            _record("pessoa fictícia", "ID-UM"),
        ])
        deletion = _ImmediateDeletionService(
            ParticipantDeletionResult(False, "não deveria executar")
        )
        synchronization = _BlockingSynchronizationService(
            ParticipantSynchronizationResult(
                succeeded=True,
                message="ok",
                participant_result=current,
            )
        )
        window = self._window(current, deletion, synchronization)

        try:
            with (
                patch(
                    "acamp.ui.main_window.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ),
                patch(
                    "acamp.ui.pages.dashboard.QMessageBox.information"
                ),
            ):
                window._start_participant_sync()
                self.assertTrue(synchronization.started.wait(timeout=1))
                QApplication.processEvents()

                window._start_participant_deletion(
                    current.participants[0]
                )
                self.assertEqual(deletion.calls, 0)
                self.assertFalse(
                    window.registrations_page.table_view.isEnabled()
                )

                synchronization.release.set()
                self._wait_until(lambda: window._sync_thread is None)
        finally:
            synchronization.release.set()
            window.close()


if __name__ == "__main__":
    unittest.main()
