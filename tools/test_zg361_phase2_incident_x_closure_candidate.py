#!/usr/bin/env python3
"""Regression tests for the no-stub Incident-X production closure builder."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import zg361_phase2_incident_x_closure_candidate as closure


def tree_rows(root: Path) -> list[tuple[str, int, str]]:
    """Return stable path/size/hash rows without builder-private helpers."""

    rows: list[tuple[str, int, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        data = path.read_bytes()
        rows.append(
            (
                path.relative_to(root).as_posix(),
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
        )
    return rows


class Phase2IncidentXClosureCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = closure.load_contract()
        cls.baseline_root = ROOT / cls.contract["baseline"]["root"]

    def _require_baseline(self) -> None:
        if not (self.baseline_root / "source").is_dir() or not (
            self.baseline_root / "projection.json"
        ).is_file():
            self.skipTest("local frozen B2 r2 projection is not present")

    def _copy_candidate_view(self, destination: Path) -> Path:
        """Build an in-memory-equivalent view without invoking materialize()."""

        self._require_baseline()
        shutil.copytree(self.baseline_root / "source", destination)
        for relative in closure.overlay_paths(self.contract):
            source = closure.MOD_ROOT / PurePosixPath(relative)
            self.assertTrue(source.is_file(), relative)
            target = destination / PurePosixPath(relative)
            self.assertFalse(target.exists(), f"overlay unexpectedly exists in r2: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return destination

    def test_contract_cardinalities_and_generator_selection(self) -> None:
        self.assertTrue(Path(closure.__file__).read_bytes().startswith(closure.BOM))
        self.assertTrue(Path(__file__).read_bytes().startswith(closure.BOM))

        candidate = self.contract["candidate"]
        incident = self.contract["incident"]
        kernel = self.contract["dependencies"]["case_kernel"]
        self.assertEqual(135, candidate["expected_file_count"])
        self.assertEqual(16, candidate["expected_overlay_file_count"])
        self.assertEqual(16, len(closure.overlay_paths(self.contract)))
        self.assertEqual(11, len(incident["effect_shards"]))
        self.assertEqual(4, len(incident["event_shards"]))
        self.assertEqual(46, len(incident["fixture_reachable_effects"]))
        self.assertEqual(1, len(incident["production_only_effects"]))
        self.assertEqual(20, len(incident["reachable_events"]))
        self.assertEqual(13, len(kernel["reachable_effects"]))
        self.assertEqual(6, len(kernel["reachable_triggers"]))

        check = closure.validate_generator_selection(self.contract)
        self.assertEqual("GREEN", check["status"])
        self.assertEqual(11, check["incident_effect_shards"])
        self.assertEqual(46, check["fixture_incident_effects"])
        self.assertEqual(47, check["production_incident_effects"])
        self.assertEqual(4, check["incident_event_shards"])
        self.assertEqual(20, check["incident_events"])
        self.assertEqual([], check["extra_effects"])
        self.assertEqual([], check["missing_effects"])
        self.assertEqual([], check["extra_events"])
        self.assertEqual([], check["missing_events"])

    def test_static_view_has_exact_fixture_and_production_fixed_points(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-static-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            checks = closure.validate_dependency_closures(root, self.contract)
            self.assertEqual("GREEN", checks["status"])

            fixture = checks["fixture"]
            production = checks["production"]
            triggers = checks["triggers"]
            self.assertEqual(59, fixture["effects"])
            self.assertEqual(20, fixture["events"])
            self.assertEqual(60, production["effects"])
            self.assertEqual(20, production["events"])
            self.assertEqual(6, triggers["count"])

            incident = self.contract["incident"]
            kernel = self.contract["dependencies"]["case_kernel"]
            expected_fixture = set(incident["fixture_reachable_effects"]) | set(
                kernel["reachable_effects"]
            )
            expected_production = expected_fixture | set(
                incident["production_only_effects"]
            )
            self.assertEqual(expected_fixture, set(fixture["effect_names"]))
            self.assertEqual(expected_production, set(production["effect_names"]))
            self.assertEqual(set(incident["reachable_events"]), set(fixture["event_ids"]))
            self.assertEqual(set(incident["reachable_events"]), set(production["event_ids"]))
            self.assertEqual(set(kernel["reachable_triggers"]), set(triggers["names"]))

    def test_static_view_has_small_shards_callable_closure_loc_and_formatting(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-gates-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")

            boundaries = closure.validate_file_boundaries(root, self.contract)
            self.assertEqual("GREEN", boundaries["status"])
            self.assertEqual(11, len(boundaries["incident_effects"]))
            self.assertEqual(4, len(boundaries["incident_events"]))
            self.assertTrue(
                all(1 <= row["definitions"] <= 10 for row in boundaries["incident_effects"])
            )
            self.assertTrue(
                all(1 <= row["definitions"] <= 10 for row in boundaries["incident_events"])
            )
            self.assertLessEqual(
                max(row["definitions"] for row in boundaries["incident_effects"]),
                7,
            )
            self.assertEqual([], boundaries["target_exceptions"])
            self.assertEqual([], boundaries["over_target"])
            self.assertEqual([], boundaries["over_hard_max"])

            callable_check = closure.validate_whole_file_callable_closure(root)
            self.assertEqual("GREEN", callable_check["status"])
            self.assertEqual([], callable_check["missing_callables"])
            self.assertEqual([], callable_check["missing_events"])

            localization = closure.validate_localization(root, self.contract)
            self.assertEqual("GREEN", localization["status"])
            self.assertEqual(20, localization["event_definitions"])
            self.assertEqual(3, localization["referenced_keys"])
            self.assertEqual([], localization["missing"])
            self.assertEqual({}, localization["duplicate_owners"])
            incident_path = self.contract["incident"]["localization_file"]
            self.assertEqual({incident_path: 3}, localization["owner_counts"])

            formatting = closure.validate_bom_braces_and_stubs(root, self.contract)
            self.assertEqual("GREEN", formatting["status"])
            self.assertEqual([], formatting["bom_missing"])
            self.assertEqual([], formatting["brace_unbalanced"])
            self.assertEqual([], formatting["stub_marker_hits"])
            self.assertEqual([], formatting["forbidden_paths_present"])

    def test_contract_rejects_generator_order_drift(self) -> None:
        altered = copy.deepcopy(self.contract)
        shards = altered["incident"]["effect_shards"]
        shards[0], shards[1] = shards[1], shards[0]
        with self.assertRaisesRegex(
            closure.IncidentXClosureError, "drifted from generator"
        ):
            closure.validate_generator_selection(altered)

    def test_forbidden_monoliths_are_absent_from_canonical_and_overlay(self) -> None:
        overlays = set(closure.overlay_paths(self.contract))
        for relative in self.contract["forbidden_paths"]:
            with self.subTest(relative=relative):
                self.assertFalse((closure.MOD_ROOT / PurePosixPath(relative)).exists())
                self.assertNotIn(relative, overlays)

    def test_forbidden_legacy_monolith_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-monolith-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            legacy = root / PurePosixPath(self.contract["forbidden_paths"][0])
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_bytes(
                closure.BOM
                + b"# forbidden historical aggregate\n"
                + b"zg361_ip_forbidden_legacy_effect = {\n"
                + b"\tset_variable = { name = forbidden value = 1 }\n"
                + b"}\n"
            )
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "forbidden|legacy monolith"
            ):
                closure.validate_bom_braces_and_stubs(root, self.contract)

    def test_historical_nonempty_diagnostic_stub_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-stub-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            target = root / PurePosixPath(self.contract["incident"]["effect_shards"][0])
            with target.open("ab") as stream:
                stream.write(
                    b"\n# DIAGNOSTIC STUB\n"
                    b"zg361_ip_historical_diagnostic_effect = {\n"
                    b'\tdebug_log = "ZG361 incident diagnostic stub: nonempty"\n'
                    b"}\n"
                )
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "DIAGNOSTIC STUB|diagnostic stub"
            ):
                closure.validate_bom_braces_and_stubs(root, self.contract)

    def test_missing_bom_and_unbalanced_brace_are_rejected(self) -> None:
        for mode in ("bom", "brace"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                prefix=f"zg361-incident-x-{mode}-"
            ) as temp:
                root = self._copy_candidate_view(Path(temp) / "candidate")
                target = root / PurePosixPath(
                    self.contract["incident"]["effect_shards"][0]
                )
                data = target.read_bytes()
                if mode == "bom":
                    self.assertTrue(data.startswith(closure.BOM))
                    target.write_bytes(data[len(closure.BOM) :])
                    pattern = "BOM|bom"
                else:
                    target.write_bytes(data + b"{\n")
                    pattern = "brace|unbalanced"
                with self.assertRaisesRegex(closure.IncidentXClosureError, pattern):
                    closure.validate_bom_braces_and_stubs(root, self.contract)

    def test_duplicate_effect_and_event_providers_are_rejected(self) -> None:
        incident = self.contract["incident"]
        cases = (
            (incident["effect_shards"][0], "common/scripted_effects/zz_duplicate.txt"),
            (incident["event_shards"][0], "events/zz_duplicate.txt"),
        )
        for source_relative, duplicate_relative in cases:
            with self.subTest(source=source_relative), tempfile.TemporaryDirectory(
                prefix="zg361-incident-x-duplicate-"
            ) as temp:
                root = self._copy_candidate_view(Path(temp) / "candidate")
                duplicate = root / PurePosixPath(duplicate_relative)
                duplicate.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / PurePosixPath(source_relative), duplicate)
                with self.assertRaisesRegex(
                    closure.IncidentXClosureError, "duplicate"
                ):
                    closure.validate_whole_file_callable_closure(root)

    def test_missing_callable_and_event_providers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-callable-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            lifecycle = root / "common/scripted_effects/zg361_incident_platform_x_lifecycle_effects.txt"
            data = lifecycle.read_bytes()
            needle = b"zg361_case_x_open_effect = yes"
            self.assertIn(needle, data)
            lifecycle.write_bytes(
                data.replace(needle, b"zg361_missing_provider_effect = yes", 1)
            )
            with self.assertRaisesRegex(
                closure.IncidentXClosureError,
                "zg361_missing_provider_effect|unresolved|missing",
            ):
                closure.validate_whole_file_callable_closure(root)

        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-event-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            event_shard = root / PurePosixPath(
                self.contract["incident"]["event_shards"][0]
            )
            event_shard.unlink()
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "unresolved|missing"
            ):
                closure.validate_dependency_closures(root, self.contract)

    def test_missing_localization_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-loc-") as temp:
            root = self._copy_candidate_view(Path(temp) / "candidate")
            loc_path = root / PurePosixPath(
                self.contract["incident"]["localization_file"]
            )
            data = loc_path.read_bytes()
            needle = b" zg361ip.190.t:0 "
            self.assertIn(needle, data)
            loc_path.write_bytes(
                data.replace(needle, b" zg361ip.190.t_missing:0 ", 1)
            )
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "localization|missing"
            ):
                closure.validate_localization(root, self.contract)

    def test_frozen_b2_r2_identity_is_exact_and_manifest_tampering_fails(self) -> None:
        self._require_baseline()
        source, manifest, projection, identity = closure.verify_baseline_identity(
            self.contract, self.baseline_root
        )
        self.assertEqual(self.baseline_root / "source", source)
        self.assertEqual(self.baseline_root / "projection.json", manifest)
        self.assertEqual(self.contract["baseline"]["projection"], projection)
        self.assertEqual("GREEN", identity["status"])
        self.assertEqual(119, identity["file_count"])

        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-baseline-") as temp:
            altered = Path(temp) / "altered"
            (altered / "source").mkdir(parents=True)
            shutil.copy2(manifest, altered / "projection.json")
            with (altered / "projection.json").open("ab") as stream:
                stream.write(b" ")
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "manifest SHA|manifest.*changed"
            ):
                closure.verify_baseline_identity(self.contract, altered)

    def test_authoritative_freeze_materializes_twice_byte_stably(self) -> None:
        self._require_baseline()
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-build-") as temp:
            output_a = Path(temp) / "candidate-a"
            output_b = Path(temp) / "candidate-b"
            projection_name = "test-phase2-incident-x-production-closure"
            results = (
                closure.materialize(output=output_a, projection_name=projection_name),
                closure.materialize(output=output_b, projection_name=projection_name),
            )
            for result in results:
                self.assertEqual("GREEN_STATIC", result["status"])
                self.assertTrue(result["no_stubs"])
                self.assertEqual(135, result["candidate"]["file_count"])
                self.assertEqual(16, result["overlay"]["file_count"])
                self.assertEqual("NOT_RUN", result["runtime"]["ck3_launch"])
                replay = result["checks"]["deterministic_materialization"]
                self.assertEqual("GREEN", replay["status"])
                self.assertTrue(replay["source_equals_product"])
                self.assertTrue(replay["source_equals_replay"])

            rows_a = tree_rows(output_a / "source")
            rows_b = tree_rows(output_b / "source")
            self.assertEqual(rows_a, tree_rows(output_a / "product"))
            self.assertEqual(rows_a, tree_rows(output_a / "materialized-check"))
            self.assertEqual(rows_b, tree_rows(output_b / "product"))
            self.assertEqual(rows_b, tree_rows(output_b / "materialized-check"))
            self.assertEqual(rows_a, rows_b)
            self.assertEqual(
                (output_a / "projection.json").read_bytes(),
                (output_b / "projection.json").read_bytes(),
            )

    def test_existing_output_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-incident-x-existing-") as temp:
            output = Path(temp)
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(
                closure.IncidentXClosureError, "output already exists"
            ):
                closure.materialize(
                    output=output,
                    projection_name="test-incident-x-existing-output",
                )
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_output_overlap_is_rejected_before_creation(self) -> None:
        cases = (
            (
                "canonical",
                closure.MOD_ROOT / "__incident_x_output_must_not_be_created__",
                "canonical mod source",
            ),
            (
                "baseline",
                self.baseline_root / "__incident_x_output_must_not_be_created__",
                "frozen B2 baseline root",
            ),
        )
        for label, output, message in cases:
            with self.subTest(label=label):
                self.assertFalse(output.exists())
                with self.assertRaisesRegex(closure.IncidentXClosureError, message):
                    closure.materialize(
                        output=output,
                        projection_name=f"test-incident-x-overlap-{label}",
                        canonical_source=closure.MOD_ROOT,
                        baseline_root=self.baseline_root,
                    )
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
