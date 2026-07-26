"""Focused Phase 2A tests using invented records in temporary files."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from acamp.models import Participant
from acamp.repositories import ParticipantLoadStatus, ParticipantRepository
from acamp.ui.models import filter_participants, paginate_participants


class ParticipantRepositoryTests(unittest.TestCase):
    def _load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            path.write_text(text, encoding="utf-8")
            return ParticipantRepository(path).load()

    def test_valid_json_loads_records(self):
        result = self._load_text(
            json.dumps(
                [{"name": "Pessoa Alfa", "age": 20, "payment": 135}],
                ensure_ascii=False,
            )
        )
        self.assertEqual(result.status, ParticipantLoadStatus.VALID)
        self.assertEqual(len(result.participants), 1)
        self.assertEqual(result.participants[0].payment, "$135.00")

    def test_missing_file_is_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            result = ParticipantRepository(path).load()
        self.assertEqual(result.status, ParticipantLoadStatus.FILE_MISSING)

    def test_empty_file_is_distinct(self):
        self.assertEqual(
            self._load_text("  \n").status,
            ParticipantLoadStatus.FILE_EMPTY,
        )

    def test_invalid_json_is_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participants.json"
            original = "[invalid"
            path.write_text(original, encoding="utf-8")
            result = ParticipantRepository(path).load()
            self.assertEqual(result.status, ParticipantLoadStatus.INVALID_JSON)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_non_list_root_is_distinct(self):
        self.assertEqual(
            self._load_text('{"records": []}').status,
            ParticipantLoadStatus.ROOT_NOT_LIST,
        )

    def test_valid_empty_list_is_distinct(self):
        self.assertEqual(
            self._load_text("[]").status,
            ParticipantLoadStatus.VALID_EMPTY,
        )

    def test_malformed_records_and_fields_are_safe(self):
        result = self._load_text(
            json.dumps(
                [
                    "not-a-record",
                    {
                        "name": "Pessoa Beta",
                        "age": "unexpected",
                        "payment": "not-a-number",
                    },
                ]
            )
        )
        self.assertEqual(result.status, ParticipantLoadStatus.VALID)
        self.assertEqual(result.skipped_records, 1)
        self.assertEqual(result.participants[0].age, "-")
        self.assertEqual(result.participants[0].payment, "-")


class ParticipantCollectionTests(unittest.TestCase):
    @staticmethod
    def _participant(name: str) -> Participant:
        return Participant.from_mapping({"name": name})

    def test_search_is_case_insensitive_and_partial(self):
        participants = (
            self._participant("Pessoa Alfa"),
            self._participant("Pessoa Beta"),
        )
        result = filter_participants(participants, "ALF")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Pessoa Alfa")

    def test_pagination_is_ten_per_page_and_clamps_page(self):
        participants = tuple(
            self._participant(f"Pessoa {number}") for number in range(21)
        )
        second_page = paginate_participants(participants, 1)
        self.assertEqual(len(second_page.items), 10)
        self.assertEqual(second_page.total_pages, 3)

        clamped_page = paginate_participants(participants[:3], 9)
        self.assertEqual(clamped_page.page_index, 0)
        self.assertEqual(len(clamped_page.items), 3)


if __name__ == "__main__":
    unittest.main()
