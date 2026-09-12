#!/usr/bin/env python3
"""Unit tests for the Reclaim the Motherland deterministic release builder."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_reclaim_the_motherland_release as release


REVISION = "a" * 40


class BuildReclaimTheMotherlandReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="rmtm-builder-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / release.PRODUCT_ID
        shutil.copytree(release.DEFAULT_SOURCE, self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, **kwargs):
        return release.build_release(
            self.source,
            self.root / "dist" / release.PRODUCT_ID,
            REVISION,
            **kwargs,
        )

    def test_exact_skeleton_inventory_and_readme_exclusion(self) -> None:
        staging, _, archive, manifest = self.build()
        self.assertEqual(32, len(release.RUNTIME_FILES))
        self.assertEqual(
            18,
            sum(path.startswith("localization/") for path in release.RUNTIME_FILES),
        )
        self.assertEqual(
            [entry["path"] for entry in manifest["files"]],
            sorted(release.RUNTIME_FILES),
        )
        self.assertFalse((staging / "README.md").exists())
        self.assertTrue((staging / "thumbnail.png").is_file())
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(
                zipped.namelist(),
                [
                    f"{release.PRODUCT_ID}/{path}"
                    for path in sorted(release.RUNTIME_FILES)
                ],
            )

    def test_repeated_build_is_byte_identical(self) -> None:
        first = self.build()
        manifest_bytes = first[1].read_bytes()
        archive_bytes = first[2].read_bytes()
        second = self.build()
        self.assertEqual(second[1].read_bytes(), manifest_bytes)
        self.assertEqual(second[2].read_bytes(), archive_bytes)

    def test_missing_and_extra_files_fail_closed(self) -> None:
        (self.source / "localization/english/rmtm_l_english.yml").unlink()
        (self.source / "unexpected.txt").write_text("x", encoding="utf-8")
        errors = release.release_source_errors(self.source)
        self.assertTrue(any("required runtime file missing" in item for item in errors))
        self.assertTrue(any("outside exact runtime allowlist" in item for item in errors))

    def test_text_encoding_contracts_are_enforced(self) -> None:
        english = self.source / "localization/english/rmtm_l_english.yml"
        english.write_bytes(english.read_bytes().removeprefix(b"\xef\xbb\xbf"))
        errors = release.release_source_errors(self.source)
        self.assertTrue(any("lacks UTF-8 BOM" in item for item in errors))

        shutil.copyfile(
            release.DEFAULT_SOURCE / "localization/english/rmtm_l_english.yml",
            english,
        )
        descriptor = self.source / "descriptor.mod"
        descriptor.write_bytes(b"\xef\xbb\xbf" + descriptor.read_bytes())
        errors = release.release_source_errors(self.source)
        self.assertTrue(any("descriptor.mod must not contain" in item for item in errors))

    def test_canonical_remote_id_is_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        descriptor.write_text(
            descriptor.read_text(encoding="utf-8")
            + 'remote_file_id="9999999999"\n',
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "remote_file_id" in item
                for item in release.release_source_errors(self.source)
            )
        )

    def test_existing_item_ids_and_invalid_ids_are_rejected(self) -> None:
        for item_id in release.FORBIDDEN_WORKSHOP_ITEM_IDS:
            with self.subTest(item_id=item_id), self.assertRaises(ValueError):
                release.normalize_workshop_item_id(item_id)

    def test_release_localization_rejects_placeholders(self) -> None:
        self.assertEqual([], release.release_localization_errors(self.source))
        french = self.source / "localization/french/rmtm_l_french.yml"
        english = self.source / "localization/english/rmtm_l_english.yml"
        french.write_bytes(
            english.read_bytes().replace(b"l_english:", b"l_french:", 1)
        )
        self.assertTrue(
            any(
                "English placeholder" in item
                for item in release.release_localization_errors(self.source)
            )
        )
        for item_id in ("0", "01", "-1", "abc", str(2**64)):
            with self.subTest(item_id=item_id), self.assertRaises(ValueError):
                release.normalize_workshop_item_id(item_id)

    def test_manifest_verification_and_tamper_detection(self) -> None:
        staging, manifest_path, _, _ = self.build()
        self.assertEqual(
            release.verify_manifest(staging, manifest_path), len(release.RUNTIME_FILES)
        )
        changed = staging / "localization/english/rmtm_l_english.yml"
        changed.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "mismatch: localization/english"):
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
        self.assertEqual(loaded["product_id"], "mod_reclaim_the_motherland")
        self.assertEqual(loaded["mod_version"], "0.2.0")
        self.assertIsNone(loaded["workshop_item_id"])
        self.assertIsNone(loaded["git_tag"])
        self.assertEqual(release.product_tag("0.1.1"), "reclaim-motherland-v0.1.1")


if __name__ == "__main__":
    unittest.main()
