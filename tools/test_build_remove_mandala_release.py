#!/usr/bin/env python3
"""Unit tests for the Mandala Purge deterministic release builder."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_remove_mandala_release as release


REVISION = "a" * 40


class BuildRemoveMandalaReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mrm-builder-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / release.PRODUCT_ID
        shutil.copytree(release.DEFAULT_SOURCE, self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, **kwargs):
        return release.build_release(
            self.source, self.root / "dist" / release.PRODUCT_ID, REVISION, **kwargs
        )

    def test_exact_inventory_and_readme_exclusion(self) -> None:
        staging, _, archive, manifest = self.build()
        self.assertEqual(
            [entry["path"] for entry in manifest["files"]], sorted(release.RUNTIME_FILES)
        )
        self.assertFalse((staging / "README.md").exists())
        with __import__("zipfile").ZipFile(archive) as zipped:
            self.assertEqual(
                zipped.namelist(),
                [f"{release.PRODUCT_ID}/{path}" for path in sorted(release.RUNTIME_FILES)],
            )

    def test_repeated_build_is_byte_identical(self) -> None:
        first = self.build()
        manifest_bytes = first[1].read_bytes()
        archive_bytes = first[2].read_bytes()
        second = self.build()
        self.assertEqual(second[1].read_bytes(), manifest_bytes)
        self.assertEqual(second[2].read_bytes(), archive_bytes)

    def test_missing_and_extra_files_fail_closed(self) -> None:
        (self.source / "events/mrm_events.txt").unlink()
        (self.source / "unexpected.txt").write_text("x", encoding="utf-8")
        errors = release.release_source_errors(self.source)
        self.assertTrue(any("required runtime file missing" in error for error in errors))
        self.assertTrue(any("outside exact runtime allowlist" in error for error in errors))

    def test_canonical_remote_id_is_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        descriptor.write_text(
            descriptor.read_text(encoding="utf-8") + 'remote_file_id="9999999999"\n',
            encoding="utf-8",
        )
        self.assertTrue(any("remote_file_id" in error for error in release.release_source_errors(self.source)))

    def test_existing_item_ids_and_invalid_ids_are_rejected(self) -> None:
        for item_id in release.FORBIDDEN_WORKSHOP_ITEM_IDS:
            with self.assertRaises(ValueError):
                release.normalize_workshop_item_id(item_id)
        for item_id in ("0", "01", "-1", "abc", str(2**64)):
            with self.assertRaises(ValueError):
                release.normalize_workshop_item_id(item_id)

    def test_manifest_verification_and_tamper_detection(self) -> None:
        staging, manifest_path, _, _ = self.build()
        self.assertEqual(
            release.verify_manifest(staging, manifest_path), len(release.RUNTIME_FILES)
        )
        (staging / "events/mrm_events.txt").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "mismatch: events/mrm_events.txt"):
            release.verify_manifest(staging, manifest_path)

    def test_workshop_descriptor_allows_only_one_final_id_line(self) -> None:
        item_id = "9999999999"
        staging, manifest_path, _, _ = self.build(workshop_item_id=item_id)
        descriptor = staging / "descriptor.mod"
        canonical = descriptor.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n")
        descriptor.write_bytes(
            canonical.replace(b"\n", b"\r\n")
            + b"\r\n"
            + f'remote_file_id="{item_id}"\r\n'.encode("ascii")
        )
        self.assertEqual(
            release.verify_manifest(staging, manifest_path, workshop_cache=True),
            len(release.RUNTIME_FILES),
        )
        descriptor.write_bytes(descriptor.read_bytes() + b"extra=true\r\n")
        with self.assertRaisesRegex(ValueError, "descriptor.mod"):
            release.verify_manifest(staging, manifest_path, workshop_cache=True)

    def test_manifest_identity(self) -> None:
        _, manifest_path, _, manifest = self.build()
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, manifest)
        self.assertEqual(loaded["product_id"], "mod_remove_mandala")
        self.assertEqual(loaded["mod_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
