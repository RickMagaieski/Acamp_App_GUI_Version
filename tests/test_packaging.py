"""Focused tests for source and packaged runtime behavior."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from acamp.paths import ApplicationPaths, bundled_resource_root


class PackagedPathTests(unittest.TestCase):
    def test_packaged_private_data_is_beside_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            executable = temporary_root / "portable" / "Acamp_App_GUI.exe"
            bundle_root = temporary_root / "bundle"
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch.object(sys, "_MEIPASS", str(bundle_root), create=True),
            ):
                paths = ApplicationPaths.from_runtime()

            self.assertTrue(paths.packaged)
            self.assertEqual(
                paths.root,
                executable.resolve().parent / "user_data",
            )
            self.assertEqual(paths.resources_root, bundle_root.resolve())
            self.assertEqual(
                paths.assets_directory,
                bundle_root.resolve() / "assets",
            )

    def test_packaged_data_directory_can_be_created_without_fake_files(self):
        with tempfile.TemporaryDirectory() as directory:
            data_root = Path(directory) / "portable" / "user_data"
            paths = ApplicationPaths(data_root, packaged=True)

            self.assertTrue(paths.ensure_private_data_directory())
            self.assertTrue(data_root.is_dir())
            self.assertEqual(list(data_root.iterdir()), [])

    def test_bundled_resource_root_is_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle_root = Path(directory) / "bundle"
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle_root), create=True),
            ):
                self.assertEqual(
                    bundled_resource_root(),
                    bundle_root.resolve(),
                )


class PackagingConfigurationTests(unittest.TestCase):
    def test_spec_is_windowed_one_folder_and_uses_gui_entry_point(self):
        project_root = Path(__file__).resolve().parent.parent
        specification = (
            project_root / "Acamp_App_GUI.spec"
        ).read_text(encoding="utf-8")

        self.assertIn('"gui_main.py"', specification)
        self.assertIn("console=False", specification)
        self.assertIn("COLLECT(", specification)
        self.assertNotIn("icon=", specification)

    def test_private_files_and_outputs_remain_ignored(self):
        project_root = Path(__file__).resolve().parent.parent
        ignore_rules = (
            project_root / ".gitignore"
        ).read_text(encoding="utf-8").splitlines()

        for private_name in (
            "participants.json",
            "items.json",
            "teams.json",
            "client_secret.json",
            "token.json",
        ):
            self.assertIn(private_name, ignore_rules)
        for generated_directory in ("build/", "dist/", "release/"):
            self.assertIn(generated_directory, ignore_rules)
        self.assertIn("!Acamp_App_GUI.spec", ignore_rules)


if __name__ == "__main__":
    unittest.main()
