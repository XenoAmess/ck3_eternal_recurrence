#!/usr/bin/env python3
"""Regression tests for the no-stub B2 production-closure materializer."""

from __future__ import annotations

import copy
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import zg361_phase2_b2_closure_candidate as closure


class Phase2B2ClosureCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = closure.load_contract()
        baseline = cls.contract["baseline"]
        cls.baseline_root = ROOT / baseline["root"]

    def _copy_static_closure_view(self, destination: Path) -> Path:
        paths = list(closure.overlay_paths(self.contract))
        case_kernel = self.contract["dependencies"]["case_kernel"]["file"]
        paths.append(case_kernel)
        for relative in paths:
            frozen = self.baseline_root / "source" / PurePosixPath(relative)
            source = frozen if frozen.is_file() else closure.MOD_ROOT / PurePosixPath(relative)
            self.assertTrue(source.is_file(), relative)
            target = destination / PurePosixPath(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return destination

    def test_contract_cardinalities_and_generator_selection(self) -> None:
        self.assertTrue(Path(closure.__file__).read_bytes().startswith(closure.BOM))
        self.assertTrue(Path(__file__).read_bytes().startswith(closure.BOM))
        self.assertEqual(60, len(closure.overlay_paths(self.contract)))
        effects, events = closure.expected_closure(self.contract)
        self.assertEqual(71, len(effects))
        self.assertEqual(28, len(events))
        check = closure.validate_generator_selection(self.contract)
        self.assertEqual("GREEN", check["status"])
        self.assertEqual(25, check["b2_effect_shards"])
        self.assertEqual(16, check["workforce_effect_shards"])
        self.assertEqual(40, check["workforce_effects"])
        self.assertEqual(7, check["workforce_event_shards"])
        self.assertEqual(19, check["workforce_events"])
        self.assertEqual([], check["extra_effects"])
        self.assertEqual([], check["missing_effects"])
        self.assertEqual([], check["extra_events"])
        self.assertEqual([], check["missing_events"])

    def test_current_static_view_has_exact_fixed_point_and_file_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b2-closure-static-") as temp:
            root = self._copy_static_closure_view(Path(temp))
            fixed_point = closure.validate_dependency_closure(root, self.contract)
            self.assertEqual(71, fixed_point["effects"])
            self.assertEqual(28, fixed_point["events"])
            self.assertEqual(
                [
                    "zg361we.4606",
                    "zg361we.4706",
                    "zg361we.4801",
                    "zg361we.4901",
                ],
                fixed_point["event_parameter_abi_ids"],
            )
            boundaries = closure.validate_file_boundaries(root, self.contract)
            self.assertEqual("GREEN", boundaries["status"])
            self.assertTrue(
                all(row["definitions"] <= 10 for row in boundaries["b2"])
            )
            self.assertTrue(
                all(
                    row["definitions"] <= 10
                    for row in boundaries["workforce_effects"]
                )
            )
            self.assertEqual([], boundaries["over_hard_max"])
            localization = closure.validate_localization(root, self.contract)
            self.assertEqual(51, localization["event_definitions"])
            self.assertEqual(64, localization["referenced_keys"])
            self.assertEqual({}, localization["duplicate_owners"])
            self.assertEqual([], localization["missing"])
            formatting = closure.validate_bom_braces_and_stubs(root, self.contract)
            self.assertEqual("GREEN", formatting["status"])

    def test_event_parameter_abi_is_a_real_reference(self) -> None:
        block = closure.ScriptBlock(
            name="zg361_probe_effect",
            path="probe.txt",
            data=(
                b"zg361_probe_effect = {\n"
                b"\tzg361_we_ad_schedule_stage_06_deadline_effect = {\n"
                b"\t\tEVENT = zg361we.4606\n"
                b"\t}\n"
                b"}\n"
            ),
        )
        effects, events, callables = closure.block_references(block)
        self.assertEqual(
            {"zg361_we_ad_schedule_stage_06_deadline_effect"}, effects
        )
        self.assertEqual({"zg361we.4606"}, events)
        self.assertEqual(effects, callables)

    def test_comments_and_strings_do_not_create_false_edges(self) -> None:
        block = closure.ScriptBlock(
            name="zg361_probe_effect",
            path="probe.txt",
            data=(
                b"zg361_probe_effect = {\n"
                b"\t# zg361_fake_effect = yes; EVENT = zg361we.9999\n"
                b'\tset_variable = { name = probe value = "zg361_string_effect = yes" }\n'
                b"\tzg361_real_effect = yes\n"
                b"\ttrigger_event = zg361real.1\n"
                b"}\n"
            ),
        )
        effects, events, callables = closure.block_references(block)
        self.assertEqual({"zg361_real_effect"}, effects)
        self.assertEqual({"zg361real.1"}, events)
        self.assertEqual(effects, callables)

    def test_historical_nonempty_b2_diagnostic_stub_is_rejected(self) -> None:
        historical_stub = (
            closure.BOM
            + b"# DISPOSABLE DIAGNOSTIC STUBS - not production behavior.\n"
            + b"zg361_we_submit_al_357_359_receipts_effect = {\n"
            + b'\tdebug_log = "ZG361 B2 diagnostic stub: '
            + b'zg361_we_submit_al_357_359_receipts_effect"\n'
            + b"}\n"
        )
        with tempfile.TemporaryDirectory(prefix="zg361-b2-historical-stub-") as temp:
            root = Path(temp)
            stub = (
                root
                / "common"
                / "scripted_effects"
                / "zg361_b2_cross_domain_diagnostic_stubs.txt"
            )
            stub.parent.mkdir(parents=True)
            stub.write_bytes(historical_stub)
            with self.assertRaises(closure.B2ClosureError) as caught:
                closure.validate_bom_braces_and_stubs(root, self.contract)
            message = str(caught.exception)
            self.assertIn("# DISPOSABLE DIAGNOSTIC STUBS", message)
            self.assertIn("ZG361 B2 diagnostic stub:", message)
            # The historical shape has a real debug_log body, so this proves
            # marker rejection rather than the separate empty-effect guard.
            self.assertNotIn("empty_effects=[{'", message)

    def test_contract_rejects_generator_order_drift(self) -> None:
        altered = copy.deepcopy(self.contract)
        shards = altered["b2"]["effect_shards"]
        shards[0], shards[1] = shards[1], shards[0]
        with self.assertRaisesRegex(closure.B2ClosureError, "drifted from generator"):
            closure.validate_generator_selection(altered)

    def test_three_legacy_monoliths_are_absent(self) -> None:
        for relative in self.contract["forbidden_paths"]:
            with self.subTest(relative=relative):
                self.assertFalse((closure.MOD_ROOT / PurePosixPath(relative)).exists())
                self.assertNotIn(relative, closure.overlay_paths(self.contract))

    def test_authoritative_freeze_materializes_119_files_twice(self) -> None:
        if not (self.baseline_root / "projection.json").is_file():
            self.skipTest("local frozen B1 formal projection is not present")
        with tempfile.TemporaryDirectory(prefix="zg361-b2-closure-build-") as temp:
            output = Path(temp) / "candidate"
            result = closure.materialize(
                output=output,
                projection_name="test-phase2-b2-production-closure",
            )
            self.assertEqual("GREEN_STATIC", result["status"])
            self.assertTrue(result["no_stubs"])
            self.assertEqual(119, result["candidate"]["file_count"])
            self.assertEqual("NOT_RUN", result["runtime"]["ck3_launch"])
            replay = result["checks"]["deterministic_materialization"]
            self.assertEqual("GREEN", replay["status"])
            self.assertTrue(replay["source_equals_product"])
            self.assertTrue(replay["source_equals_replay"])
            self.assertEqual(
                closure.tree_rows(output / "source"),
                closure.tree_rows(output / "product"),
            )
            self.assertEqual(
                closure.tree_rows(output / "source"),
                closure.tree_rows(output / "materialized-check"),
            )

    def test_existing_output_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b2-closure-existing-") as temp:
            output = Path(temp)
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(closure.B2ClosureError, "output already exists"):
                closure.materialize(
                    output=output,
                    projection_name="test-existing-output",
                )
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_output_below_authoritative_inputs_is_rejected_before_creation(self) -> None:
        cases = (
            (
                "canonical",
                closure.MOD_ROOT / "__b2_closure_output_must_not_be_created__",
                closure.MOD_ROOT,
                self.baseline_root,
                "canonical mod source",
            ),
            (
                "baseline",
                self.baseline_root / "__b2_closure_output_must_not_be_created__",
                closure.MOD_ROOT,
                self.baseline_root,
                "frozen B1 baseline root",
            ),
        )
        for label, output, canonical_source, baseline_root, message in cases:
            with self.subTest(label=label):
                self.assertFalse(output.exists())
                with self.assertRaisesRegex(closure.B2ClosureError, message):
                    closure.materialize(
                        output=output,
                        projection_name=f"test-overlap-{label}",
                        canonical_source=canonical_source,
                        baseline_root=baseline_root,
                    )
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
