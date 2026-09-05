#!/usr/bin/env python3
"""Tests for the boundary-only B3 effect-file A/B fallback."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
MOD_ROOT = ROOT / "mod_zhongguo_style"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import plan_zg361_b3_effect_split_fallback as fallback  # noqa: E402


class B3EffectSplitFallbackTests(unittest.TestCase):
    def _minimal_r3_shape(self, destination: Path) -> Path:
        source = destination / "source"
        effects = source / fallback.EFFECT_ROOT
        effects.mkdir(parents=True)
        canonical = MOD_ROOT / fallback.EFFECT_ROOT
        for owner in fallback.TARGET_OWNERS:
            shutil.copy2(canonical / owner, effects / owner)
        (effects / "zg361_small_sentinel_effects.txt").write_bytes(
            fallback.BOM
            + b"# Untouched sentinel.\n"
            + b"zg361_small_sentinel_effect = {\n\talways = yes\n}\n"
        )
        (source / "descriptor.mod").write_bytes(
            fallback.BOM + b'name="fallback-test"\n'
        )
        return source

    def test_current_owner_shape_and_purpose_plan(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = self._minimal_r3_shape(Path(raw))
            report = fallback.build_report(source)
        self.assertEqual("GREEN", report["result"])
        self.assertFalse(report["input_matches_r3"])
        self.assertEqual(4, report["inventory"]["effect_file_count"])
        self.assertEqual(1528, report["inventory"]["effect_definition_count"])
        candidate = report["candidate_B"]
        self.assertEqual(198, candidate["created_shard_count"])
        self.assertEqual(199, candidate["projected_effect_file_count"])
        self.assertEqual(1528, candidate["projected_effect_definition_count"])
        self.assertEqual(10, candidate["maximum_effects_per_file"])
        self.assertEqual(0, candidate["target_miss_count"])
        self.assertEqual(0, candidate["over_20_violation_count"])
        self.assertTrue(all(report["checks"].values()))

    def test_materialization_changes_only_declared_file_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self._minimal_r3_shape(root)
            output = root / "candidate-B"
            manifest = root / "candidate-B.effect-split-manifest.json"
            receipt = fallback.materialize_candidate(
                source, output, manifest
            )
            persisted = json.loads(manifest.read_text(encoding="utf-8"))
            effect_root = output / fallback.EFFECT_ROOT
            rendered = sorted(effect_root.glob("zg361_ab_b3_*_effects.txt"))
            original_owners_absent = all(
                not (effect_root / owner).exists()
                for owner in fallback.TARGET_OWNERS
            )
            source_hashes_after = fallback._tree_hashes(source)
        self.assertEqual("GREEN", receipt["result"])
        self.assertEqual(receipt["result"], persisted["result"])
        self.assertEqual(198, len(rendered))
        self.assertTrue(all(receipt["materialization_checks"].values()))
        self.assertTrue(original_owners_absent)
        self.assertEqual(
            fallback.sha256_bytes(
                (MOD_ROOT / fallback.EFFECT_ROOT / fallback.MECHANISM_OWNER).read_bytes()
            ),
            source_hashes_after[
                f"common/scripted_effects/{fallback.MECHANISM_OWNER}"
            ],
        )

    def test_semantic_body_change_is_carried_from_A_without_r3_identity_claim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self._minimal_r3_shape(root)
            owner = source / fallback.EFFECT_ROOT / fallback.B1_OWNER
            changed = owner.read_bytes().replace(
                b"zg361_b1_classify_function_effect = {",
                b"zg361_b1_classify_function_effect = {\n\t# r4 semantic correction",
                1,
            )
            owner.write_bytes(changed)
            report = fallback.build_report(source)
            output = root / "candidate-B"
            manifest = root / "candidate-B.json"
            receipt = fallback.materialize_candidate(source, output, manifest)
            first_b1 = (
                output
                / fallback.EFFECT_ROOT
                / "zg361_ab_b3_b1_01_case_bootstrap_policy_kpi_effects.txt"
            ).read_bytes()
        self.assertEqual("GREEN", report["result"])
        self.assertFalse(report["input_matches_r3"])
        self.assertEqual("GREEN", receipt["result"])
        self.assertIn(b"# r4 semantic correction", first_b1)

    def test_definition_anchor_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = self._minimal_r3_shape(Path(raw))
            owner = source / fallback.EFFECT_ROOT / fallback.B1_PART2_OWNER
            owner.write_bytes(
                owner.read_bytes().replace(
                    b"zg361_b1_finalize_agenda_audit_effect",
                    b"zg361_b1_unplanned_anchor_effect",
                    1,
                )
            )
            with self.assertRaises(fallback.EffectSplitFallbackError):
                fallback.build_report(source)

    def test_existing_output_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self._minimal_r3_shape(root)
            output = root / "candidate-B"
            output.mkdir()
            with self.assertRaises(fallback.EffectSplitFallbackError):
                fallback.materialize_candidate(
                    source, output, root / "candidate-B.json"
                )

    def test_manifest_must_be_a_sidecar_outside_b(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self._minimal_r3_shape(root)
            output = root / "candidate-B"
            with self.assertRaises(fallback.EffectSplitFallbackError):
                fallback.materialize_candidate(
                    source, output, output / "manifest.json"
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
