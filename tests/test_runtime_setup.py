"""Packaged runtime-data setup tests using only temporary invented files."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QDialog

from acamp.paths import ApplicationPaths
from acamp.runtime_data import (
    DATA_LOCATION_CONFIG,
    RuntimeDataConfigStore,
    import_runtime_files,
    missing_required_files,
)
from acamp.ui.setup_dialog import RuntimeDataSetupDialog


def _create_required_files(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in ("participants.json", "items.json", "teams.json"):
        (root / name).write_text("[]\n", encoding="utf-8")


class RuntimeDataConfigurationTests(unittest.TestCase):
    def test_external_folder_configuration_is_loaded_in_packaged_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            executable = temporary_root / "portable" / "Acamp_App_GUI.exe"
            managed_root = executable.parent / "user_data"
            external_root = temporary_root / "selected-data"
            _create_required_files(external_root)
            store = RuntimeDataConfigStore(managed_root)
            self.assertTrue(store.save_external(external_root))

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch.object(
                    sys,
                    "_MEIPASS",
                    str(temporary_root / "bundle"),
                    create=True,
                ),
            ):
                paths = ApplicationPaths.from_runtime()

            self.assertEqual(paths.root, external_root.resolve())
            self.assertEqual(paths.data_mode, "external")
            self.assertTrue(paths.configuration_valid)
            self.assertFalse(paths.needs_data_setup)

    def test_unconfigured_packaged_mode_requests_setup_without_json_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            executable = temporary_root / "portable" / "Acamp_App_GUI.exe"
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
            ):
                paths = ApplicationPaths.from_runtime()

            self.assertEqual(paths.data_mode, "unconfigured")
            self.assertTrue(paths.needs_data_setup)
            self.assertTrue(paths.ensure_private_data_directory())
            self.assertEqual(list(paths.managed_root.iterdir()), [])

    def test_managed_configuration_contains_no_private_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            managed_root = Path(directory) / "user_data"
            _create_required_files(managed_root)
            store = RuntimeDataConfigStore(managed_root)
            self.assertTrue(store.save_managed())

            payload = json.loads(
                (managed_root / DATA_LOCATION_CONFIG).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(payload, {"version": 1, "mode": "managed"})


class RuntimeDataImportTests(unittest.TestCase):
    def test_explicit_import_copies_only_recognized_selected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected"
            destination = root / "user_data"
            source.mkdir()
            selected_participants = source / "participants.json"
            selected_participants.write_text(
                '[{"name": "Pessoa Fictícia"}]\n',
                encoding="utf-8",
            )
            rejected = source / "notes.json"
            rejected.write_text('{"note": "inventada"}\n', encoding="utf-8")

            result = import_runtime_files(
                (selected_participants, rejected),
                destination,
            )

            self.assertEqual(result.copied, ("participants.json",))
            self.assertEqual(result.rejected, ("notes.json",))
            self.assertTrue((destination / "participants.json").is_file())
            self.assertFalse((destination / "notes.json").exists())
            self.assertEqual(
                missing_required_files(destination),
                ("items.json", "teams.json"),
            )

    def test_import_never_searches_unselected_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unrelated = root / "unrelated"
            destination = root / "user_data"
            _create_required_files(unrelated)

            result = import_runtime_files((), destination)

            self.assertEqual(result.copied, ())
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])


class RuntimeDataSetupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _unconfigured_paths(managed_root: Path) -> ApplicationPaths:
        return ApplicationPaths(
            managed_root,
            packaged=True,
            managed_root=managed_root,
            data_mode="unconfigured",
            configuration_valid=False,
        )

    def test_existing_folder_choice_persists_and_accepts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            managed_root = root / "portable" / "user_data"
            external_root = root / "selected"
            _create_required_files(external_root)
            dialog = RuntimeDataSetupDialog(
                self._unconfigured_paths(managed_root)
            )

            with patch(
                "acamp.ui.setup_dialog.QFileDialog.getExistingDirectory",
                return_value=str(external_root),
            ):
                dialog._choose_existing_folder()

            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            selection = RuntimeDataConfigStore(managed_root).load()
            self.assertIsNotNone(selection)
            self.assertEqual(selection.mode, "external")
            self.assertEqual(selection.root, external_root.resolve())

    def test_file_picker_imports_required_files_and_uses_managed_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            managed_root = root / "portable" / "user_data"
            selected_root = root / "selected"
            _create_required_files(selected_root)
            selected = tuple(
                str(selected_root / name)
                for name in ("participants.json", "items.json", "teams.json")
            )
            dialog = RuntimeDataSetupDialog(
                self._unconfigured_paths(managed_root)
            )

            with patch(
                "acamp.ui.setup_dialog.QFileDialog.getOpenFileNames",
                return_value=(selected, "Arquivos JSON (*.json)"),
            ):
                dialog._choose_import_files()

            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            self.assertEqual(missing_required_files(managed_root), ())
            selection = RuntimeDataConfigStore(managed_root).load()
            self.assertIsNotNone(selection)
            self.assertEqual(selection.mode, "managed")
            self.assertEqual(selection.root, managed_root.resolve())


if __name__ == "__main__":
    unittest.main()
