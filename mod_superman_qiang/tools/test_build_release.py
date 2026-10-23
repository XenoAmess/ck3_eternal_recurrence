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
import validate_static
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

    @staticmethod
    def statement_block(nodes: tuple[validate_static.EffectAssignment, ...], key: str) -> tuple[validate_static.EffectAssignment, ...]:
        matches = [node.value for node in nodes if node.key == key]
        if len(matches) != 1 or not isinstance(matches[0], tuple):
            raise ValueError(f"expected one fixture block: {key}")
        return matches[0]

    @staticmethod
    def nested_keys(nodes: tuple[validate_static.EffectAssignment, ...]) -> tuple[str, ...]:
        keys: list[str] = []
        for node in nodes:
            keys.append(node.key)
            if isinstance(node.value, tuple):
                keys.extend(SupermanNotificationFixtureTests.nested_keys(node.value))
        return tuple(keys)

    def test_n5_real_emitter_requires_five_visible_confirmations_before_probe(self) -> None:
        output = self.root / "five-confirmations"
        self.prepare(output)
        source = (output / "events/sxant_events.txt").read_text(encoding="utf-8-sig")
        # The shared scanner masks quoted logs; remove them before AST checks.
        statements = validate_static.effect_assignments(re.sub(r'debug_log\s*=\s*"[^"\n]*"', "", source))
        # The first if only restores the subject, so select the action if explicitly.
        event = self.statement_block(statements, "sxant.1012")
        immediate = self.statement_block(event, "immediate")
        action_ifs = [node.value for node in immediate if node.key == "if" and isinstance(node.value, tuple)]
        self.assertEqual(len(action_ifs), 2)
        setup = action_ifs[1]
        self.assertNotIn("had_sex_with_effect", self.nested_keys(event))
        self.assertEqual(dict((node.key, node.value) for node in self.statement_block(setup, "trigger_event")), {"id": "sxant.1201"})
        setup_variables = [dict((field.key, field.value) for field in node.value)
                           for node in setup if node.key == "set_variable" and isinstance(node.value, tuple)]
        self.assertIn({"name": "sxant_confirmed_invocations", "value": "0"}, setup_variables)
        self.assertNotIn({"name": "sxant_stage", "value": "2"}, setup_variables)
        for ordinal in range(1, 6):
            with self.subTest(ordinal=ordinal):
                event = self.statement_block(statements, f"sxant.{1200 + ordinal}")
                self.assertNotIn("hidden", [node.key for node in event])
                self.assertIn(validate_static.EffectAssignment("theme", "marriage"), event)
                self.assertNotIn("had_sex_with_effect", self.nested_keys(self.statement_block(event, "immediate")))
                option = self.statement_block(event, "option")
                action = self.statement_block(option, "if")
                limit = dict((node.key, node.value) for node in self.statement_block(action, "limit"))
                self.assertEqual(limit["var:sxant_stage"], "1")
                self.assertEqual(limit["var:sxant_case_index"], "12")
                self.assertEqual(limit["var:sxant_repetitions"], "5")
                self.assertEqual(limit["has_variable"], "sxant_confirmed_invocations")
                self.assertEqual(limit["var:sxant_confirmed_invocations"], str(ordinal - 1))
                self.assertEqual(self.nested_keys(event).count("had_sex_with_effect"), 1)
                invocation = self.statement_block(action, "had_sex_with_effect")
                self.assertEqual(dict((node.key, node.value) for node in invocation), {"CHARACTER": "scope:sxant_subject", "PREGNANCY_CHANCE": "0"})
                increment = self.statement_block(action, "change_variable")
                self.assertEqual(dict((node.key, node.value) for node in increment), {"name": "sxant_confirmed_invocations", "add": "1"})
                keys = [node.key for node in action]
                self.assertLess(keys.index("had_sex_with_effect"), keys.index("change_variable"))
                target = "sxant.4" if ordinal == 5 else f"sxant.{1201 + ordinal}"
                self.assertEqual(dict((node.key, node.value) for node in self.statement_block(action, "trigger_event")), {"id": target})
                final_variables = [dict((field.key, field.value) for field in node.value)
                                   for node in action if node.key == "set_variable" and isinstance(node.value, tuple)]
                self.assertEqual({"name": "sxant_stage", "value": "2"} in final_variables, ordinal == 5)
        self.assertEqual(source.count('debug_log = "SXANT: ACTIONS_COMPLETE hook-unequal N=5"'), 1)
        metadata: object = json.loads((output / "_notification_cells.json").read_bytes())
        if not isinstance(metadata, dict) or not isinstance(metadata.get("cells"), list):
            self.fail("notification metadata must contain the actual cells")
        selected = [cell for cell in metadata["cells"] if isinstance(cell, dict) and cell.get("case_index") == 12]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].get("confirmation_event_keys"), [f"sxant.{1200 + ordinal}" for ordinal in range(1, 6)])
        self.assertEqual(selected[0].get("invocation_counter"), "sxant_confirmed_invocations")

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
