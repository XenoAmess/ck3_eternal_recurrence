"""Corruption and reproducibility tests for Superman Qiang's release boundary."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import prepare_live_fixture
from product import REPO, RUNTIME_FILES, SOURCE, VERSION, spec
import sys

sys.path.insert(0, str(REPO / "tools"))
import independent_mod_release as release

REVISION = "a" * 40


class SupermanReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sxad-release-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        shutil.copytree(SOURCE, self.source)
        self.product = replace(spec(), source=self.source)

    def build(self, name: str = "build"):
        return release.build(self.product, self.root / name, REVISION, git_tag="superman-qiang-v" + VERSION)

    def test_release_has_exact_allowlist_and_excludes_source_and_fixture_assets(self) -> None:
        fixture = self.source / "tools" / "fixture" / "sxadt_test.txt"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text("namespace = sxadt\n", encoding="utf-8-sig")
        staging, manifest, archive, payload = self.build()
        paths = {path.relative_to(staging).as_posix() for path in staging.rglob("*") if path.is_file()}
        self.assertEqual(paths, RUNTIME_FILES)
        self.assertEqual(len(payload["files"]), len(RUNTIME_FILES))
        self.assertIsNone(payload["workshop_item_id"])
        self.assertEqual(release.verify_manifest(self.product, staging, manifest), len(RUNTIME_FILES))
        self.assertNotIn("remote_file_id", (staging / "descriptor.mod").read_text(encoding="utf-8-sig"))
        with zipfile.ZipFile(archive) as stream:
            self.assertEqual(set(stream.namelist()), {self.product.product_id + "/" + path for path in RUNTIME_FILES})
            for entry in stream.infolist():
                self.assertEqual(entry.date_time, release.ZIP_TIMESTAMP)

    def test_manifest_and_archive_are_byte_reproducible(self) -> None:
        first, second = self.build("one"), self.build("two")
        self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
        self.assertEqual(first[2].read_bytes(), second[2].read_bytes())

    def test_mutated_staging_is_rejected_even_with_same_file_size(self) -> None:
        staging, manifest, _, _ = self.build()
        counter = staging / "common/scripted_effects/sxad_experience_effects.txt"
        original = counter.read_bytes()
        counter.write_bytes(original[:-1] + (b"X" if original[-1:] != b"X" else b"Y"))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            release.verify_manifest(self.product, staging, manifest)

    def test_descriptor_workshop_id_and_unreviewed_runtime_are_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        original = descriptor.read_bytes()
        descriptor.write_bytes(original + b'remote_file_id="3800000000"\n')
        with self.assertRaisesRegex(ValueError, "remote_file_id"):
            self.build()
        descriptor.write_bytes(original)
        extra = self.source / "events" / "sxadt_test.txt"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("namespace = sxadt\n", encoding="utf-8-sig")
        with self.assertRaisesRegex(ValueError, "outside allowlist"):
            self.build()

    def test_existing_attempt_and_wrong_product_tag_are_rejected(self) -> None:
        _, manifest, archive, _ = self.build()
        before = (manifest.read_bytes(), archive.read_bytes())
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.build()
        self.assertEqual(before, (manifest.read_bytes(), archive.read_bytes()))
        with self.assertRaisesRegex(ValueError, "git_tag"):
            release.build(self.product, self.root / "wrong-tag", REVISION, git_tag="v1.0.0")


class SupermanNotificationFixtureTests(unittest.TestCase):
    """Exercise the real emitter; template markers are never gameplay results."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sxad-notification-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.templates = self.source / "tools" / "notification_fixture"
        shutil.copytree(SOURCE / "tools" / "notification_fixture", self.templates)

    def prepare(self, output: Path) -> prepare_live_fixture.NotificationFixtureReport:
        with patch.object(prepare_live_fixture, "SOURCE", self.source):
            return prepare_live_fixture.prepare_notification_fixture(output)

    def replace_case_field(self, field: str, value: bool | float | int | str | None) -> None:
        path = self.templates / "cases.json"
        original = path.read_text(encoding="utf-8")
        pattern = rf'("{re.escape(field)}"\s*:\s*)(?:"[^"\n]*"|true|false|null|-?\d+(?:\.\d+)?)'
        changed, count = re.subn(pattern, lambda match: match.group(1) + json.dumps(value), original, count=1)
        self.assertEqual(count, 1, field)
        path.write_text(changed, encoding="utf-8")

    def test_materialized_files_are_complete_byte_copies_with_roundtrip_receipt(self) -> None:
        output = self.root / "fixture"
        report = self.prepare(output)
        expected_runtime = {
            "descriptor.mod", "common/on_action/sxant_on_actions.txt",
            "common/scripted_effects/sxant_vanilla_pair_control.txt",
            "events/sxant_events.txt", "localization/english/sxant_l_english.yml",
            "localization/simp_chinese/sxant_l_simp_chinese.yml",
        }
        actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected_runtime | {"_notification_cells.json"})
        self.assertEqual({entry["path"] for entry in report["files"]}, actual)
        self.assertEqual(len(report["files"]), len(actual))
        for relative in expected_runtime:
            self.assertEqual((output / relative).read_bytes(), (self.templates / relative).read_bytes())
        self.assertEqual((output / "_notification_cells.json").read_bytes(), (self.templates / "cases.json").read_bytes())
        for entry in report["files"]:
            raw = (output / entry["path"]).read_bytes()
            self.assertEqual(entry["size"], len(raw))
            self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["case_count"], 32)
        self.assertEqual(report["candidate_results"], "not_run")
        self.assertEqual(report["expected_pass_markers"], [])
        self.assertIs(report["ck3_started"], False)
        receipt: object = json.loads((self.root / "fixture.fixture.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt, report)
        cells: object = json.loads((output / "_notification_cells.json").read_text(encoding="utf-8"))
        self.assertIsInstance(cells, dict)
        if not isinstance(cells, dict):
            self.fail("copied cell contract must remain a JSON object")
        self.assertEqual(cells.get("case_count"), 32)

    def test_existing_output_and_product_paths_are_rejected_without_overwrite(self) -> None:
        output = self.root / "existing"
        output.mkdir()
        sentinel = output / "original.txt"
        sentinel.write_bytes(b"original evidence")
        with self.assertRaisesRegex(ValueError, "new directory outside product source"):
            self.prepare(output)
        self.assertEqual(sentinel.read_bytes(), b"original evidence")
        self.assertEqual(list(output.iterdir()), [sentinel])
        for target in (self.source, self.source / "uncreated-output"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "new directory outside product source"):
                    self.prepare(target)
        self.assertFalse((self.source / "uncreated-output").exists())

    def test_existing_sidecar_receipt_is_rejected_without_creating_output(self) -> None:
        output = self.root / "prior-receipt"
        receipt = self.root / "prior-receipt.fixture.json"
        receipt.write_bytes(b"original receipt")
        with self.assertRaisesRegex(ValueError, "already exists|new directory|receipt"):
            self.prepare(output)
        self.assertEqual(receipt.read_bytes(), b"original receipt")
        self.assertFalse(output.exists())

    def test_json_integer_fields_reject_bool_and_equal_float_values(self) -> None:
        path = self.templates / "cases.json"
        original = path.read_bytes()
        cases: tuple[tuple[str, bool | float, str], ...] = (
            ("case_index", True, "invalid notification cell index"),
            ("case_index", 1.0, "invalid notification cell index"),
            ("repetitions", False, "invalid notification repetition count"),
            ("repetitions", 0.0, "invalid notification repetition count"),
            ("case_count", 32.0, "expected 32 unexecuted notification cells"),
        )
        for index, (field, value, message) in enumerate(cases):
            with self.subTest(field=field, value=value):
                path.write_bytes(original)
                self.replace_case_field(field, value)
                output = self.root / f"invalid-integer-{index}"
                with self.assertRaisesRegex(ValueError, message):
                    self.prepare(output)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix(".fixture.json").exists())

    def test_claimed_or_malformed_notification_results_are_rejected(self) -> None:
        path = self.templates / "cases.json"
        original = path.read_bytes()
        for index, result in enumerate(("GREEN", "passed", "not_run ", True, None)):
            with self.subTest(result=result):
                path.write_bytes(original)
                self.replace_case_field("notification_result", result)
                output = self.root / f"invalid-result-{index}"
                with self.assertRaisesRegex(ValueError, "may not claim an actual result"):
                    self.prepare(output)
                self.assertFalse(output.exists())

    def test_missing_cell_fields_and_duplicate_indices_are_rejected(self) -> None:
        path = self.templates / "cases.json"
        original = path.read_text(encoding="utf-8")
        expected_errors = {
            "case_index": "invalid notification cell index",
            "repetitions": "invalid notification repetition count",
            "notification_result": "may not claim an actual result",
        }
        for field, message in expected_errors.items():
            with self.subTest(missing_field=field):
                pattern = (rf',\n\s*"{field}"\s*:[^\n]*'
                           if field == "notification_result"
                           else rf'^\s*"{field}"\s*:[^\n]*\n')
                changed, count = re.subn(pattern, "", original, count=1, flags=re.MULTILINE)
                self.assertEqual(count, 1)
                path.write_text(changed, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    self.prepare(self.root / f"missing-{field}")
        path.write_text(original, encoding="utf-8")
        self.replace_case_field("case_index", 2)
        with self.assertRaisesRegex(ValueError, "invalid notification cell index"):
            self.prepare(self.root / "duplicate-index")


if __name__ == "__main__":
    unittest.main(verbosity=2)
