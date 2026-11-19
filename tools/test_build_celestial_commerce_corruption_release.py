#!/usr/bin/env python3
"""Unit tests for the Celestial Commerce & Corruption release builder."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import build_celestial_commerce_corruption_release as release
import validate_celestial_commerce_corruption_static as static_gate


REVISION = "a" * 40


class ManifestContractTests(unittest.TestCase):
    """Exercise the real manifest chain with tiny files, without copying a mod."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="xccc-manifest-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.staging = self.root / "staging"
        for relative in release.RUNTIME_FILES:
            path = self.staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode("utf-8"))
        self.manifest = release.create_manifest(self.staging, REVISION, "1.0.2")
        self.path = self.root / "release.manifest.json"
        self.path.write_bytes(release.manifest_bytes(self.manifest))

    def payload(self) -> dict[str, object]:
        return dict(self.manifest)

    def assert_rejected(self, payload: object) -> None:
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ValueError):
            release._load_manifest(self.path)
        with self.assertRaises(ValueError):
            release.verify_manifest(self.staging, self.path)

    def test_producer_serialization_loader_zip_and_verifier_share_one_contract(self) -> None:
        loaded = release._load_manifest(self.path)
        self.assertEqual(loaded, self.manifest)
        self.assertEqual(release.manifest_bytes(loaded), self.path.read_bytes())
        self.assertEqual(release.verify_manifest(self.staging, self.path), len(release.RUNTIME_FILES))
        archive = self.root / "release.zip"
        release.write_deterministic_zip(self.staging, archive, loaded)
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.namelist(), [f"{release.PRODUCT_ID}/{entry['path']}"
                                                for entry in loaded["files"]])
            for entry in loaded["files"]:
                self.assertEqual(zipped.read(f"{release.PRODUCT_ID}/{entry['path']}"),
                                 (self.staging / entry["path"]).read_bytes())

    def test_identity_types_and_values_fail_before_verification(self) -> None:
        invalid: tuple[tuple[str, object], ...] = (
            ("format_version", True), ("format_version", 1.0),
            ("format_version", "1"), ("format_version", 2),
            ("product_id", True), ("product_id", "another_product"),
            ("mod_version", True), ("mod_version", 1.0), ("mod_version", "bad"),
            ("git_tag", 1), ("git_tag", release.product_tag("9.9.9")),
            ("git_sha", False), ("git_sha", "A" * 40), ("git_sha", "short"),
            ("workshop_item_id", True), ("workshop_item_id", 1.0),
            ("workshop_item_id", 1), ("workshop_item_id", "0"),
            ("workshop_item_id", "01"), ("workshop_item_id", str(2**64)),
            ("workshop_item_id", sorted(release.FORBIDDEN_WORKSHOP_ITEM_IDS)[0]),
            ("files", {}), ("files", [None]),
        )
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                payload = self.payload()
                payload[field] = value
                self.assert_rejected(payload)

    def test_missing_extra_and_null_fields_have_explicit_semantics(self) -> None:
        for field in self.manifest:
            with self.subTest(missing=field):
                payload = self.payload()
                del payload[field]
                self.assert_rejected(payload)
            if field not in {"git_tag", "workshop_item_id"}:
                with self.subTest(null=field):
                    payload = self.payload()
                    payload[field] = None
                    self.assert_rejected(payload)
        payload = self.payload()
        payload["unexpected"] = True
        self.assert_rejected(payload)
        self.assertIsNone(release._parse_manifest(self.manifest)["git_tag"])
        self.assertIsNone(release._parse_manifest(self.manifest)["workshop_item_id"])
        for item_id in ("1", str(2**64 - 1)):
            tagged = release.create_manifest(self.staging, REVISION, "1.0.2", item_id,
                                             release.product_tag("1.0.2"))
            self.path.write_bytes(release.manifest_bytes(tagged))
            self.assertEqual(release._load_manifest(self.path), tagged)
        self.path.write_bytes(release.manifest_bytes(self.manifest))
        with self.assertRaisesRegex(ValueError, "requires a manifest item ID"):
            release.verify_manifest(self.staging, self.path, workshop_cache=True)

    def test_file_fields_sizes_hashes_and_inventory_are_validated(self) -> None:
        invalid: tuple[tuple[str, object], ...] = (
            ("size", True), ("size", 1.0), ("size", -1), ("size", "0"), ("size", None),
            ("path", True), ("path", None), ("path", "../escape"),
            ("sha256", None), ("sha256", True), ("sha256", 1.0),
            ("sha256", "A" * 64), ("sha256", "a" * 63),
        )
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                entries = [dict(entry) for entry in self.manifest["files"]]
                entries[0][field] = value
                payload = self.payload()
                payload["files"] = entries
                self.assert_rejected(payload)
        for field in ("path", "size", "sha256", "unexpected"):
            entries = [dict(entry) for entry in self.manifest["files"]]
            if field == "unexpected":
                entries[0][field] = True
            else:
                del entries[0][field]
            payload = self.payload()
            payload["files"] = entries
            self.assert_rejected(payload)
        for inventory in (self.manifest["files"][:-1], list(reversed(self.manifest["files"])),
                          [self.manifest["files"][0], *self.manifest["files"]]):
            payload = self.payload()
            payload["files"] = inventory
            self.assert_rejected(payload)

    def test_json_shape_duplicate_fields_and_encoding_are_rejected(self) -> None:
        invalid: tuple[object, ...] = (None, [], True, 1.0, "manifest")
        for value in invalid:
            self.assert_rejected(value)
        valid = release.manifest_bytes(self.manifest)
        for raw in (b"{", b"\xff", valid.replace(b'"format_version": 1,',
                    b'"format_version": 1, "format_version": 1,', 1),
                    valid.replace(b'"size":', b'"size": 0, "size":', 1)):
            with self.subTest(raw=raw[:20]):
                self.path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    release._load_manifest(self.path)


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
        self.assertEqual(loaded["mod_version"], "1.0.2")

    def government_path(self) -> Path:
        return self.source / "common/governments/xccc_celestial_government.txt"

    def test_old_native_levies_are_rejected_without_changing_product_tax(self) -> None:
        path = self.source / "common/subject_contracts/contracts/xccc_celestial_obligations.txt"
        current = path.read_text(encoding="utf-8-sig")
        self.assertIn("value = xccc_celestial_tax_default", current)
        self.assertEqual(current.count("subtract = xccc_corruption_"), 4)
        stock_common = self.root / "reviewed-stock/common"
        government = stock_common / "governments/00_government_types.txt"
        contract = stock_common / "subject_contracts/contracts/celestial.txt"
        government.parent.mkdir(parents=True)
        contract.parent.mkdir(parents=True)
        government.write_text(self.government_path().read_text(encoding="utf-8-sig").replace(
            "barter = yes", "", 1), encoding="utf-8-sig")
        # Reviewed minimal vanilla contract fixture, independent of the product tax block.
        contract.write_text("celestial_obligations = { obligation_levels = { default = {\n"
                            "levies = { value = 0.2 }\ntax = { value = 0.5 }\n} } }\n",
                            encoding="utf-8-sig")
        with patch.object(static_gate, "MOD", self.source), patch.object(
            static_gate, "GAME_GOVERNMENTS", (government,)
        ):
            self.assertEqual(static_gate.validate(), [])
            path.write_text(current.replace("value = 0.2", "value = 0.3", 1),
                            encoding="utf-8-sig", newline="\n")
            errors = static_gate.validate()
            self.assertIn("celestial levy projection differs from reviewed CK3 1.21.0.3", errors)
            self.assertIn("celestial obligations differ from installed CK3 beyond product tax", errors)

    def test_new_native_capabilities_cannot_be_dropped_from_build(self) -> None:
        path = self.government_path()
        original = path.read_text(encoding="utf-8-sig")
        for line in (
            "house_power",
            "title_maa_setup = vassals_and_top_liege",
            "build_gold_cost = 0.5",
            "district_build_gold_cost = 0.5",
            "holding_build_gold_cost = 0.5",
            "government_has_provincial_law",
            "government_is_settled_non_tribal",
            "government_uses_governor_efficiency",
            "government_uses_legitimacy",
            "government_uses_royal_court",
            "build_queue_reserve_categories",
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
                with self.assertRaisesRegex(ValueError, "differs from frozen CK3 1.21.0.3"):
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
            "# Reviewed native CK3 1.21.0.3 projection\n" + text.replace(
                "mechanic_type = administrative", "mechanic_type   = administrative # native mechanic"
            ),
            encoding="utf-8-sig",
        )
        self.build()


if __name__ == "__main__":
    unittest.main()
