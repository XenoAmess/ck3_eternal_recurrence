#!/usr/bin/env python3
"""Unit tests for the Celestial Commerce & Corruption release builder."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_celestial_commerce_corruption_release as release


REVISION = "a" * 40


class BuildCelestialCommerceCorruptionReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="xccc-builder-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / release.PRODUCT_ID
        shutil.copytree(release.DEFAULT_SOURCE, self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, **kwargs):
        return release.build_release(
            self.source, self.root / "dist" / release.PRODUCT_ID, REVISION, **kwargs
        )

    def test_exact_inventory_and_source_only_exclusion(self) -> None:
        staging, _, archive, manifest = self.build()
        self.assertEqual(
            [entry["path"] for entry in manifest["files"]],
            sorted(release.RUNTIME_FILES),
        )
        self.assertFalse((staging / "README.md").exists())
        self.assertFalse((staging / "docs").exists())
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
        (self.source / "common/script_values/xccc_corruption_values.txt").unlink()
        (self.source / "unexpected.txt").write_text("x", encoding="utf-8")
        errors = release.release_source_errors(self.source)
        self.assertTrue(any("required runtime file missing" in error for error in errors))
        self.assertTrue(any("outside exact runtime allowlist" in error for error in errors))

    def test_remote_id_is_rejected_in_source(self) -> None:
        descriptor = self.source / "descriptor.mod"
        descriptor.write_text(
            descriptor.read_text(encoding="utf-8") + 'remote_file_id="9999999999"\n',
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "remote_file_id" in error
                for error in release.release_source_errors(self.source)
            )
        )

    def test_upstream_and_existing_item_ids_are_rejected(self) -> None:
        self.assertIn("3596263413", release.FORBIDDEN_WORKSHOP_ITEM_IDS)
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
        target = staging / "common/script_values/xccc_corruption_values.txt"
        target.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "mismatch: common/script_values"):
            release.verify_manifest(staging, manifest_path)

    def test_workshop_descriptor_allows_native_or_one_final_id_line(self) -> None:
        item_id = "9999999999"
        staging, manifest_path, _, _ = self.build(workshop_item_id=item_id)
        descriptor = staging / "descriptor.mod"
        self.assertEqual(
            release.verify_manifest(staging, manifest_path, workshop_cache=True),
            len(release.RUNTIME_FILES),
        )
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
        self.assertEqual(loaded["product_id"], release.PRODUCT_ID)
        self.assertEqual(loaded["mod_version"], "1.0.1")

    def government_path(self) -> Path:
        return self.source / "common/governments/xccc_celestial_government.txt"

    def test_new_native_capabilities_cannot_be_dropped_from_build(self) -> None:
        path = self.government_path()
        original = path.read_text(encoding="utf-8-sig")
        for line in (
            "mechanic_type = administrative",
            "treasury_vassal_development = yes",
            "government_has_east_asian_estate",
            "government_uses_celestial_bureaucracy",
            "government_uses_salary_budget",
            "government_uses_military_budget",
            "government_uses_ministry_budget",
            "use_legends = yes",
            "possible_grant_vassal_governments = { theocracy_government ecclesiastical_government }",
        ):
            with self.subTest(capability=line):
                self.assertIn(line, original)
                path.write_text(original.replace(line, "", 1), encoding="utf-8-sig")
                with self.assertRaisesRegex(ValueError, "differs from frozen CK3 1.20.0.2"):
                    self.build()

    def test_barter_is_one_rule_in_the_native_rules_block(self) -> None:
        path = self.government_path()
        original = path.read_text(encoding="utf-8-sig")
        invalid = {
            "missing": original.replace("barter = yes", "", 1),
            "disabled": original.replace("barter = yes", "barter = no", 1),
            "duplicate": original.replace("barter = yes", "barter = yes\n\t\tbarter = yes", 1),
            "outside_rules": original.replace("barter = yes", "", 1).replace(
                "royal_court = any", "barter = yes\n\troyal_court = any", 1
            ),
        }
        for case, text in invalid.items():
            with self.subTest(case=case):
                path.write_text(text, encoding="utf-8-sig")
                with self.assertRaisesRegex(ValueError, "barter"):
                    self.build()

    def test_formatting_comments_do_not_change_frozen_semantics(self) -> None:
        path = self.government_path()
        text = path.read_text(encoding="utf-8-sig")
        path.write_text(
            "# Reviewed native CK3 1.20.0.2 projection\n" + text.replace(
                "mechanic_type = administrative", "mechanic_type   = administrative # native mechanic"
            ),
            encoding="utf-8-sig",
        )
        self.build()


if __name__ == "__main__":
    unittest.main()
