"""Phase 2B inventory tests using only invented temporary data."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox

from acamp.models import InventoryDraft, InventoryItem
from acamp.repositories import (
    InventoryLoadStatus,
    InventoryRepository,
    InventorySaveResult,
)
from acamp.services import InventoryService, validate_inventory_draft
from acamp.ui.models import filter_inventory_items
from acamp.ui.pages.inventory import InventoryPage


class InventoryRepositoryTests(unittest.TestCase):
    def _load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            path.write_text(text, encoding="utf-8")
            return InventoryRepository(path).load()

    def test_valid_inventory_load(self):
        result = self._load_text(
            json.dumps(
                [{
                    "item": "Item Inventado",
                    "quantity": 2,
                    "value": 12.5,
                    "description": "Descrição inventada",
                }],
                ensure_ascii=False,
            )
        )
        self.assertEqual(result.status, InventoryLoadStatus.VALID)
        self.assertEqual(result.items[0].total_display, "$25.00")

    def test_missing_empty_invalid_and_non_list_states(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = InventoryRepository(Path(directory) / "missing.json").load()
        self.assertEqual(missing.status, InventoryLoadStatus.FILE_MISSING)
        self.assertEqual(
            self._load_text("").status,
            InventoryLoadStatus.FILE_EMPTY,
        )
        self.assertEqual(
            self._load_text("[invalid").status,
            InventoryLoadStatus.INVALID_JSON,
        )
        self.assertEqual(
            self._load_text('{"items": []}').status,
            InventoryLoadStatus.ROOT_NOT_LIST,
        )

    def test_malformed_records_are_safe(self):
        result = self._load_text(
            json.dumps([
                "registro inválido",
                {"item": "Item Parcial", "quantity": "x", "value": "nan"},
            ])
        )
        self.assertEqual(result.skipped_records, 1)
        self.assertEqual(result.items[0].quantity_display, "-")
        self.assertEqual(result.items[0].value_display, "-")

    def test_atomic_save_and_portuguese_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            repository = InventoryRepository(path)
            result = repository.save([{
                "item": "Item Inventado",
                "quantity": 1,
                "value": 2.5,
                "description": "Descrição inventada",
            }])
            self.assertTrue(result.succeeded)
            saved_text = path.read_text(encoding="utf-8")
            self.assertIn("Descrição inventada", saved_text)
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_failed_replace_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            original = '[{"item": "Original"}]'
            path.write_text(original, encoding="utf-8")
            repository = InventoryRepository(path)
            with patch(
                "acamp.repositories.os.replace",
                side_effect=OSError("synthetic failure"),
            ):
                result = repository.save([{"item": "Proposto"}])
            self.assertFalse(result.succeeded)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


class InventoryServiceTests(unittest.TestCase):
    def test_validation_rejects_invalid_fields(self):
        result = validate_inventory_draft("   ", "nan", 0)
        self.assertFalse(result.succeeded)
        self.assertEqual(set(result.errors), {"item", "quantity", "value"})

        result = validate_inventory_draft("Item", "inf", 1)
        self.assertFalse(result.succeeded)
        self.assertIn("value", result.errors)

    def test_search_is_partial_and_case_insensitive(self):
        items = (
            InventoryItem.from_mapping({"item": "Item Alfa"}, 0),
            InventoryItem.from_mapping({"item": "Item Beta"}, 1),
        )
        filtered = filter_inventory_items(items, "ALF")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].item, "Item Alfa")

    def test_add_and_delete_persist_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            path.write_text("[]", encoding="utf-8")
            service = InventoryService(InventoryRepository(path))
            service.load()

            validation = validate_inventory_draft(
                "  Item Novo  ",
                "5.25",
                2,
                "  descrição  ",
            )
            self.assertTrue(validation.succeeded)
            added = service.add_item(validation.draft)
            self.assertTrue(added.succeeded)
            self.assertEqual(len(service.items), 1)

            source_index = service.items[0].source_index
            deleted = service.delete_item(source_index)
            self.assertTrue(deleted.succeeded)
            self.assertEqual(service.items, ())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])

    def test_malformed_source_records_survive_an_add(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            original_records = [
                "registro preservado",
                {"item": "Item Parcial", "quantity": "x"},
            ]
            path.write_text(json.dumps(original_records), encoding="utf-8")
            service = InventoryService(InventoryRepository(path))
            service.load()
            draft = InventoryDraft(
                item="Item Novo",
                quantity=1,
                value=validate_inventory_draft("x", "1", 1).draft.value,
                description="",
            )
            self.assertTrue(service.add_item(draft).succeeded)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved[:2], original_records)

    def test_failed_add_keeps_live_state_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            original = '[{"item": "Item Original", "quantity": 1, "value": 2}]'
            path.write_text(original, encoding="utf-8")
            repository = InventoryRepository(path)
            service = InventoryService(repository)
            service.load()
            original_items = service.items
            draft = validate_inventory_draft("Item Proposto", "3", 1).draft

            with patch.object(
                repository,
                "save",
                return_value=InventorySaveResult(False),
            ):
                result = service.add_item(draft)

            self.assertFalse(result.succeeded)
            self.assertEqual(service.items, original_items)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


class InventoryPageDeletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self, path: Path) -> InventoryPage:
        path.write_text(
            json.dumps([{
                "item": "Item Inventado",
                "quantity": 1,
                "value": 3.0,
                "description": "",
            }]),
            encoding="utf-8",
        )
        service = InventoryService(InventoryRepository(path))
        service.load()
        return InventoryPage(service)

    def test_cancelled_deletion_changes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            page = self._build_page(path)
            original = path.read_text(encoding="utf-8")
            action = page.table_model.index(
                0,
                page.table_model.ACTION_COLUMN,
            )
            with patch(
                "acamp.ui.pages.inventory.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ):
                page._table_clicked(action)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(page.table_model.rowCount(), 1)

    def test_confirmed_deletion_updates_file_and_table(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.json"
            page = self._build_page(path)
            action = page.table_model.index(
                0,
                page.table_model.ACTION_COLUMN,
            )
            with patch(
                "acamp.ui.pages.inventory.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                page._table_clicked(action)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])
            self.assertEqual(page.table_model.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
