"""Phase 3A tests with mocked Google behavior and invented records only."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from google.auth.exceptions import RefreshError
from PySide6.QtWidgets import QApplication, QMessageBox

from acamp.config import GoogleSheetsConfig
from acamp.models import Participant
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantLoadStatus,
    ParticipantRepository,
    ParticipantSaveResult,
    TeamRepository,
    participant_result_from_records,
)
from acamp.services import (
    InventoryService,
    ParticipantSynchronizationResult,
    SynchronizationService,
    TeamService,
)
from acamp.sheets_gateway import (
    GoogleSheetsGateway,
    SheetParseResult,
    SheetsGatewayError,
    parse_sheet_values,
)
from acamp.ui.main_window import MainWindow
from gui_main import create_application


def _sheet_row(**overrides) -> list[str]:
    values = [
        "Nome",
        "Sobrenome",
        "25",
        "001-555-0100",
        "",
        "não",
        "pessoa@example.invalid",
        "cabine",
        "adulto",
        "135.00",
        "sim",
        "",
        "",
        "ID-FICTICIO",
    ]
    columns = {
        "first_name": 0,
        "last_name": 1,
        "age": 2,
        "phone": 3,
        "medical": 4,
        "transportation": 5,
        "email": 6,
        "accommodation": 7,
        "inscription": 8,
        "payment": 9,
        "food": 10,
        "participant_id": 13,
    }
    for key, value in overrides.items():
        values[columns[key]] = value
    return values


def _participant_result(records) -> ParticipantLoadResult:
    return participant_result_from_records(records)


class SheetParsingTests(unittest.TestCase):
    def test_valid_mapping_preserves_portuguese_and_string_fields(self):
        values = [
            ["Cabeçalho"],
            _sheet_row(
                first_name="  Áurea ",
                last_name=" Fictícia  ",
                phone="001-555-0199",
                payment="67,75",
                participant_id="00042",
            ),
        ]

        result = parse_sheet_values(values)

        self.assertEqual(result.loaded_count, 1)
        self.assertEqual(result.skipped_rows, 0)
        self.assertEqual(result.warning_rows, 0)
        record = result.records[0]
        self.assertEqual(record["name"], "áurea fictícia")
        self.assertEqual(record["phone"], "001-555-0199")
        self.assertEqual(record["payment"], 67.75)
        self.assertEqual(record["id"], "00042")

    def test_short_row_and_invalid_age_are_preserved_with_warning(self):
        values = [
            ["Cabeçalho"],
            ["Pessoa", "Curta", "idade inválida"],
        ]

        result = parse_sheet_values(values)

        self.assertEqual(result.loaded_count, 1)
        self.assertEqual(result.warning_rows, 1)
        self.assertEqual(result.records[0]["age"], 0)
        self.assertEqual(result.records[0]["payment"], 0.0)
        self.assertEqual(result.records[0]["accommodation"], "cabine")
        self.assertEqual(result.records[0]["phone"], "")
        self.assertEqual(result.records[0]["id"], "")

    def test_missing_name_is_skipped_without_exposing_row(self):
        result = parse_sheet_values([
            ["Cabeçalho"],
            _sheet_row(first_name="", last_name=""),
        ])
        self.assertEqual(result.loaded_count, 0)
        self.assertEqual(result.skipped_rows, 1)

    def test_invalid_nan_infinity_and_negative_payments_become_zero(self):
        values = [
            ["Cabeçalho"],
            _sheet_row(first_name="Pessoa", last_name="NaN", payment="NaN"),
            _sheet_row(
                first_name="Pessoa",
                last_name="Infinita",
                payment="Infinity",
            ),
            _sheet_row(
                first_name="Pessoa",
                last_name="Negativa",
                payment="-5",
            ),
        ]

        result = parse_sheet_values(values)

        self.assertEqual(result.loaded_count, 3)
        self.assertEqual(result.warning_rows, 3)
        self.assertEqual(
            [record["payment"] for record in result.records],
            [0.0, 0.0, 0.0],
        )

    def test_invalid_response_is_controlled(self):
        with self.assertRaises(SheetsGatewayError) as context:
            parse_sheet_values({"values": []})
        self.assertEqual(
            context.exception.technical_code,
            "sheet_values_not_list",
        )


class GatewayFailureTests(unittest.TestCase):
    def test_missing_client_secret_has_portuguese_error(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = GoogleSheetsGateway(
                GoogleSheetsConfig(Path(directory))
            )
            with self.assertRaises(SheetsGatewayError) as context:
                gateway._authenticate()
            self.assertEqual(
                context.exception.user_message,
                "O arquivo client_secret.json não foi encontrado.",
            )

    def test_invalid_client_secret_is_controlled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client_secret.json").write_text(
                "{}",
                encoding="utf-8",
            )
            gateway = GoogleSheetsGateway(GoogleSheetsConfig(root))
            with patch(
                "acamp.sheets_gateway.InstalledAppFlow"
                ".from_client_secrets_file",
                side_effect=ValueError,
            ):
                with self.assertRaises(SheetsGatewayError) as context:
                    gateway._authenticate()
            self.assertEqual(
                context.exception.technical_code,
                "client_secret_invalid",
            )

    def test_failed_token_refresh_is_controlled(self):
        class ExpiredCredentials:
            valid = False
            expired = True
            refresh_token = object()

            def refresh(self, _request):
                raise RefreshError("invented refresh failure")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "token.json").write_text("{}", encoding="utf-8")
            gateway = GoogleSheetsGateway(GoogleSheetsConfig(root))
            with patch(
                "acamp.sheets_gateway.Credentials"
                ".from_authorized_user_file",
                return_value=ExpiredCredentials(),
            ):
                with self.assertRaises(SheetsGatewayError) as context:
                    gateway._authenticate()
            self.assertEqual(
                context.exception.technical_code,
                "google_token_refresh_failed",
            )

    def test_network_failure_is_controlled(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = GoogleSheetsGateway(
                GoogleSheetsConfig(Path(directory))
            )
            with (
                patch.object(
                    gateway,
                    "_authenticate",
                    return_value=object(),
                ),
                patch(
                    "acamp.sheets_gateway.AuthorizedHttp",
                    side_effect=OSError,
                ),
            ):
                with self.assertRaises(SheetsGatewayError) as context:
                    gateway.download_participants()
            self.assertEqual(
                context.exception.user_message,
                "A conexão com a internet não está disponível.",
            )


class ParticipantAtomicSaveTests(unittest.TestCase):
    def test_atomic_save_uses_utf8_and_readable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            repository = ParticipantRepository(path)
            records = [{
                "name": "pessoa fictícia açucena",
                "age": 22,
                "phone": "001-555-0110",
                "medical": "",
                "transportation": "não",
                "email": "inventado@example.invalid",
                "accommodation": "cabine",
                "inscription": "adulto",
                "payment": 135.0,
                "food": "sim",
                "id": "FICTICIO-1",
            }]

            result = repository.save(records)

            self.assertTrue(result.succeeded)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                records,
            )
            self.assertIn(
                "açucena",
                path.read_text(encoding="utf-8"),
            )

    def test_failed_replace_preserves_original_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            original = '[{"name": "registro local fictício"}]\n'
            path.write_text(original, encoding="utf-8")
            repository = ParticipantRepository(path)

            with patch(
                "acamp.repositories.os.replace",
                side_effect=OSError,
            ):
                result = repository.save([{
                    "name": "novo registro fictício"
                }])

            self.assertFalse(result.succeeded)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


class FakeGateway:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def download_participants(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class SynchronizationServiceTests(unittest.TestCase):
    def test_success_saves_then_returns_replacement_state(self):
        records = tuple(parse_sheet_values([
            ["Cabeçalho"],
            _sheet_row(first_name="Nova", last_name="Pessoa"),
        ]).records)
        downloaded = SheetParseResult(records, skipped_rows=2, warning_rows=1)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            path.write_text(
                '[{"name": "estado local fictício"}]',
                encoding="utf-8",
            )
            service = SynchronizationService(
                FakeGateway(downloaded),
                ParticipantRepository(path),
            )

            result = service.synchronize()

            self.assertTrue(result.succeeded)
            self.assertEqual(result.loaded_count, 1)
            self.assertEqual(result.skipped_rows, 2)
            self.assertEqual(result.warning_rows, 1)
            self.assertEqual(
                len(result.participant_result.participants),
                1,
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                list(records),
            )

    def test_gateway_failure_preserves_local_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            original = '[{"name": "estado local fictício"}]\n'
            path.write_text(original, encoding="utf-8")
            service = SynchronizationService(
                FakeGateway(
                    error=SheetsGatewayError(
                        "Não foi possível conectar ao Google Sheets.",
                        "invented_network_failure",
                    )
                ),
                ParticipantRepository(path),
            )

            result = service.synchronize()

            self.assertFalse(result.succeeded)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_save_failure_returns_error_without_replacement_state(self):
        downloaded = SheetParseResult(({
            "name": "nova pessoa fictícia",
            "age": 20,
            "payment": 0.0,
        },))
        repository = ParticipantRepository(
            Path(tempfile.gettempdir()) / "unused-participants.json"
        )
        service = SynchronizationService(
            FakeGateway(downloaded),
            repository,
        )

        with patch.object(
            repository,
            "save",
            return_value=ParticipantSaveResult(
                False,
                "invented_save_failure",
            ),
        ):
            result = service.synchronize()

        self.assertFalse(result.succeeded)
        self.assertIsNone(result.participant_result)
        self.assertEqual(
            result.message,
            "Os dados foram baixados, mas não puderam ser salvos.",
        )

    def test_damaged_cache_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            path.write_text("{json inválido", encoding="utf-8")
            service = SynchronizationService(
                FakeGateway(SheetParseResult(())),
                ParticipantRepository(path),
            )
            self.assertTrue(
                service.local_cache_requires_replacement_confirmation()
            )
            refused = service.synchronize()
            self.assertFalse(refused.succeeded)
            self.assertEqual(
                refused.technical_code,
                "damaged_cache_confirmation_required",
            )
            self.assertEqual(service._gateway.calls, 0)


class ImmediateSynchronizationService:
    def __init__(self, result, *, damaged=False):
        self.result = result
        self.damaged = damaged
        self.calls = 0

    def local_cache_requires_replacement_confirmation(self):
        return self.damaged

    def synchronize(self, **_options):
        self.calls += 1
        return self.result


class BlockingSynchronizationService(ImmediateSynchronizationService):
    def __init__(self, result):
        super().__init__(result)
        self.started = threading.Event()
        self.release = threading.Event()

    def synchronize(self, **_options):
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=2)
        return self.result


class SynchronizationUiTests(unittest.TestCase):
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
    def _window(root: Path, sync_service):
        (root / "items.json").write_text(
            '[{"item":"Item Fictício","quantity":1,"value":2}]',
            encoding="utf-8",
        )
        (root / "teams.json").write_text(
            '[{"equipe":"Equipe Fictícia","lider":"Líder",'
            '"cor":"Verde","pessoas":[],"score":1}]',
            encoding="utf-8",
        )
        inventory = InventoryService(
            InventoryRepository(root / "items.json")
        )
        teams = TeamService(TeamRepository(root / "teams.json"))
        inventory.load()
        teams.load()
        local_state = _participant_result(({
            "name": "pessoa local fictícia",
            "inscription": "adulto",
            "accommodation": "cabine",
            "payment": 0,
        },))
        return MainWindow(
            local_state,
            inventory,
            teams,
            sync_service,
        )

    def test_success_updates_all_participant_pages_and_prevents_duplicate(self):
        new_state = _participant_result((
            {
                "name": "nova pessoa fictícia um",
                "inscription": "adulto",
                "accommodation": "cabine",
                "payment": 135,
            },
            {
                "name": "nova pessoa fictícia dois",
                "inscription": "adulto",
                "accommodation": "cabine",
                "payment": 0,
            },
        ))
        result = ParticipantSynchronizationResult(
            succeeded=True,
            message="Sincronização concluída.",
            participant_result=new_state,
            loaded_count=2,
            skipped_rows=1,
            warning_rows=1,
        )
        service = BlockingSynchronizationService(result)

        with tempfile.TemporaryDirectory() as directory:
            window = self._window(Path(directory), service)
            try:
                with (
                    patch(
                        "acamp.ui.main_window.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.Yes,
                    ) as confirmation,
                    patch(
                        "acamp.ui.pages.dashboard.QMessageBox.information"
                    ) as information,
                ):
                    window.dashboard_page.sync_button.click()
                    self.assertTrue(service.started.wait(timeout=1))
                    QApplication.processEvents()
                    self.assertFalse(
                        window.dashboard_page.sync_button.isEnabled()
                    )
                    self.assertEqual(
                        window.dashboard_page.sync_button.text(),
                        "Sincronizando...",
                    )

                    window._start_participant_sync()
                    self.assertEqual(service.calls, 1)
                    service.release.set()
                    self._wait_until(
                        lambda: window._sync_thread is None
                    )

                confirmation.assert_called_once()
                information.assert_called_once()
                self.assertIn(
                    "2 participantes carregados",
                    information.call_args.args[2],
                )
                self.assertIn(
                    "1 linha ignorada",
                    information.call_args.args[2],
                )
                self.assertTrue(
                    window.dashboard_page.sync_button.isEnabled()
                )
                self.assertTrue(
                    window.dashboard_page.sync_status_label.text().startswith(
                        "Última sincronização nesta sessão:"
                    )
                )
                self.assertEqual(
                    window.finance_service.participant_result,
                    new_state,
                )
                self.assertEqual(
                    window.registrations_page.table_model.rowCount(),
                    2,
                )
                self.assertEqual(
                    window.dashboard_page.last_snapshot.participant_total,
                    2,
                )
                self.assertEqual(
                    window.reports_page.last_snapshot.participant_total,
                    2,
                )
                self.assertEqual(
                    window.finance_page.summary_labels["entries"].text(),
                    "$135.00",
                )
                self.assertEqual(len(window.inventory_page._service.items), 1)
                self.assertEqual(
                    len(window.activities_page._service.teams),
                    1,
                )
            finally:
                window.close()

    def test_failure_preserves_shared_state_and_restores_button(self):
        failed = ParticipantSynchronizationResult(
            succeeded=False,
            message="A conexão com a internet não está disponível.",
            technical_code="invented_failure",
        )
        service = ImmediateSynchronizationService(failed)

        with tempfile.TemporaryDirectory() as directory:
            window = self._window(Path(directory), service)
            original_state = window.finance_service.participant_result
            try:
                with (
                    patch(
                        "acamp.ui.main_window.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.Yes,
                    ),
                    patch(
                        "acamp.ui.pages.dashboard.QMessageBox.warning"
                    ) as warning,
                ):
                    window.dashboard_page.sync_button.click()
                    self._wait_until(
                        lambda: window._sync_thread is None
                    )

                warning.assert_called_once()
                self.assertEqual(
                    window.finance_service.participant_result,
                    original_state,
                )
                self.assertTrue(
                    window.dashboard_page.sync_button.isEnabled()
                )
                self.assertEqual(
                    window.dashboard_page.sync_status_label.text(),
                    "Ainda não sincronizado nesta sessão.",
                )
            finally:
                window.close()

    def test_startup_does_not_call_google_gateway(self):
        with patch.object(
            GoogleSheetsGateway,
            "download_participants",
        ) as download:
            _app, window = create_application(
                load_participants=False,
                load_inventory=False,
                load_teams=False,
            )
            QApplication.processEvents()
            download.assert_not_called()
            window.close()


if __name__ == "__main__":
    unittest.main()
