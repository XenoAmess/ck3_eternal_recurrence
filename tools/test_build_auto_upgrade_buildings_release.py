#!/usr/bin/env python3
"""Unit tests for the Auto Upgrade Buildings release builder."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_auto_upgrade_buildings_release as release


REVISION = "a" * 40


class BuildAutoUpgradeBuildingsReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="auto-upgrade-builder-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / release.PRODUCT_ID
        shutil.copytree(release.DEFAULT_SOURCE, self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self):
        return release.build_release(
            self.source, self.root / "dist" / release.PRODUCT_ID, REVISION
        )

    def test_exact_inventory_and_readme_exclusion(self) -> None:
        staging, _, archive, manifest = self.build()
        expected = sorted(release.RUNTIME_FILES)
        self.assertEqual([item["path"] for item in manifest["files"]], expected)
        self.assertFalse((staging / "README.md").exists())
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(
                zipped.namelist(),
                [f"{release.PRODUCT_ID}/{relative}" for relative in expected],
            )

    def test_repeated_build_is_byte_identical(self) -> None:
        first = self.build()
        first_manifest = first[1].read_bytes()
        first_zip = first[2].read_bytes()
        second = self.build()
        self.assertEqual(second[1].read_bytes(), first_manifest)
        self.assertEqual(second[2].read_bytes(), first_zip)

    def test_missing_and_extra_files_fail_closed(self) -> None:
        (self.source / "events/auto_build.txt").unlink()
        (self.source / "unexpected.txt").write_text("x", encoding="utf-8")
        errors = release.source_errors(self.source)
        self.assertTrue(any("missing runtime file" in error for error in errors))
        self.assertTrue(any("outside allowlist" in error for error in errors))

    def test_canonical_workshop_identity_is_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        descriptor.write_text(
            descriptor.read_text(encoding="utf-8")
            + f'remote_file_id="{release.UPSTREAM_WORKSHOP_ITEM_ID}"\n',
            encoding="utf-8",
        )
        errors = release.source_errors(self.source)
        self.assertTrue(any("remote_file_id" in error for error in errors))
        self.assertTrue(any("Workshop identity" in error for error in errors))

    def test_manifest_identity(self) -> None:
        _, manifest_path, _, manifest = self.build()
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, manifest)
        self.assertEqual(loaded["product_id"], release.PRODUCT_ID)
        self.assertEqual(loaded["mod_version"], "1.19.0")
        self.assertIsNone(loaded["workshop_item_id"])


if __name__ == "__main__":
    unittest.main()
