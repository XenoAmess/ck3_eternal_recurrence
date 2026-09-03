#!/usr/bin/env python3
"""Regression tests for the fixed-seed callback-closed production builder."""

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

import zg361_phase2_seed_closure_candidate as closure


def script_block(name: str, body: str) -> closure.closure_utils.ScriptBlock:
    data = f"{name} = {{\n{body}\n}}\n".encode("utf-8")
    return closure.closure_utils.ScriptBlock(name=name, path=f"{name}.txt", data=data)


class Phase2SeedClosureCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = closure.load_contract()
        cls.baseline_root = ROOT / cls.contract["baseline"]["root"]

    def _require_baseline(self) -> None:
        if not (self.baseline_root / "source").is_dir() or not (
            self.baseline_root / "projection.json"
        ).is_file():
            self.skipTest("local frozen Incident-X r3 projection is not present")

    def test_contract_fixture_and_frozen_cardinalities(self) -> None:
        self.assertTrue(Path(closure.__file__).read_bytes().startswith(closure.BOM))
        self.assertTrue(Path(__file__).read_bytes().startswith(closure.BOM))
        fixture = closure.validate_fixture(self.contract)
        self.assertEqual(4503, fixture["bytes"])
        self.assertEqual(
            "b35cf0c0e32932ea136da71f8d91bef4dbdcddf681f230ac6822cee0c30fa853",
            fixture["sha256"],
        )
        self.assertEqual(
            [
                "zg361_b1_open_cycle_effect",
                "zg361_ip_open_x_case_effect",
                "zg361_we_open_portfolio_effect",
                "zg361_b2_on_result_frozen_effect",
                "zg361_b2_on_notice_delivered_effect",
            ],
            fixture["ordered_root_effects"],
        )
        candidate = self.contract["candidate"]
        self.assertEqual(245, candidate["expected_file_count"])
        self.assertEqual(110, candidate["expected_overlay_file_count"])
        self.assertEqual(68, candidate["expected_effect_files"])
        self.assertEqual(35, candidate["expected_event_files"])
        self.assertEqual(2, candidate["expected_court_position_files"])
        self.assertEqual(5, candidate["expected_localization_files"])
        self.assertEqual(28, candidate["expected_new_localization_keys"])
        self.assertEqual(0, candidate["expected_effect_files_over_target"])
        self.assertEqual(0, candidate["expected_effect_files_over_hard_max"])
        self.assertEqual([], candidate["effect_boundary_exceptions"])
        self.assertEqual(12_097_112, candidate["expected_bytes"])
        self.assertEqual(2_938_670, self.contract["overlay"]["bytes"])

    def test_fixture_root_order_drift_is_rejected(self) -> None:
        altered = copy.deepcopy(self.contract)
        roots = altered["fixture"]["ordered_root_effects"]
        roots[0], roots[1] = roots[1], roots[0]
        with self.assertRaisesRegex(closure.SeedClosureError, "root order drifted"):
            closure.validate_fixture(altered)

    def test_court_position_callbacks_and_callable_dependencies_are_recursive(self) -> None:
        root = script_block(
            "zg361_probe_root_effect",
            "\ttype = zg361_probe_court_position",
        )
        callback = script_block(
            "zg361_probe_callback_effect",
            "\tzg361_probe_first_trigger = yes\n\ttrigger_event = zg361probe.2",
        )
        event = script_block("zg361probe.1", "\thidden = yes")
        event_two = script_block("zg361probe.2", "\thidden = yes")
        first_trigger = script_block(
            "zg361_probe_first_trigger",
            "\tzg361_probe_second_trigger = yes\n\tzg361_probe_value = yes",
        )
        second_trigger = script_block("zg361_probe_second_trigger", "\talways = yes")
        value = script_block("zg361_probe_value", "\tvalue = 1")
        position = script_block(
            "zg361_probe_court_position",
            "\ton_court_position_received = { zg361_probe_callback_effect = yes }\n"
            "\ton_court_position_revoked = { trigger_event = zg361probe.1 }",
        )
        graph = closure.ProviderGraph(
            effects={root.name: root, callback.name: callback},
            events={event.name: event, event_two.name: event_two},
            triggers={
                first_trigger.name: first_trigger,
                second_trigger.name: second_trigger,
            },
            values={value.name: value},
            court_positions={position.name: position},
        )
        result = closure.dependency_fixed_point(graph, (root.name,))
        self.assertFalse(result.unresolved)
        self.assertEqual({root.name, callback.name}, set(result.effects))
        self.assertEqual({event.name, event_two.name}, set(result.events))
        self.assertEqual(
            {first_trigger.name, second_trigger.name}, set(result.triggers)
        )
        self.assertEqual({value.name}, set(result.values))
        self.assertEqual({position.name}, set(result.court_positions))

        missing_callback = closure.ProviderGraph(
            effects={root.name: root},
            events={event.name: event},
            triggers={},
            values={},
            court_positions={position.name: position},
        )
        unresolved = closure.dependency_fixed_point(missing_callback, (root.name,))
        self.assertIn(callback.name, unresolved.missing_effects)

    def test_selected_workforce_overlay_is_exact_and_pure_owner(self) -> None:
        self._require_baseline()
        baseline_source, _manifest, _projection, identity = (
            closure.verify_baseline_identity(self.contract, self.baseline_root)
        )
        self.assertEqual(135, identity["file_count"])
        rows, selection = closure.select_overlay(
            closure.MOD_ROOT, baseline_source, self.contract
        )
        self.assertEqual(
            {
                "effects": 397,
                "events": 164,
                "triggers": 6,
                "values": 0,
                "court_positions": 2,
            },
            selection["full"],
        )
        self.assertEqual(
            {
                "effects": 314,
                "events": 142,
                "triggers": 0,
                "values": 0,
                "court_positions": 2,
            },
            selection["delta"],
        )
        self.assertEqual([], selection["manager_effects"])
        self.assertEqual([], selection["manager_events"])
        self.assertEqual([], selection["manager_triggers"])
        self.assertEqual([], selection["workforce_m360_effects"])
        self.assertEqual([], selection["workforce_m360_events"])
        self.assertEqual(110, len(rows))
        by_kind = {
            kind: [row for row in rows if row["kind"] == kind]
            for kind in ("effect", "event", "court_position", "localization")
        }
        self.assertEqual(68, len(by_kind["effect"]))
        self.assertEqual(35, len(by_kind["event"]))
        self.assertEqual(2, len(by_kind["court_position"]))
        self.assertEqual(5, len(by_kind["localization"]))
        self.assertEqual(314, sum(row["definitions"] for row in by_kind["effect"]))
        self.assertEqual(142, sum(row["definitions"] for row in by_kind["event"]))
        self.assertEqual(28, sum(row["definitions"] for row in by_kind["localization"]))
        self.assertEqual(10, max(row["definitions"] for row in by_kind["effect"]))
        by_path = {row["path"]: row for row in rows}
        split_paths = {
            "common/scripted_effects/zg361_workforce_endgame_046a_ac_m257_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_046b_ac_m262_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_048a_ac_m264_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_048b_ac_m265_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_050a_ad_m271_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_050b_ad_m267_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_053a_ad_m274_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_053b_ad_m275_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_061a_al_m361_consume_route_a_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_061b_al_m361_route_b_c_effects.txt",
        }
        retired_paths = {
            "common/scripted_effects/zg361_workforce_endgame_046_ac_m257_m262_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_048_ac_m264_m265_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_050_ad_m271_m267_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_053_ad_m274_m275_effects.txt",
            "common/scripted_effects/zg361_workforce_endgame_061_al_m361_effects.txt",
        }
        self.assertTrue(split_paths <= set(by_path))
        expected_definitions = {
            path: (2 if "_061" in path else 4) for path in split_paths
        }
        self.assertTrue(
            all(
                by_path[path]["definitions"] == expected_definitions[path]
                for path in split_paths
            )
        )
        self.assertTrue(retired_paths.isdisjoint(by_path))
        self.assertTrue(retired_paths <= set(self.contract["forbidden_paths"]))
        overlay = closure.validate_overlay_contract(
            rows, self.contract, allow_unfrozen=False
        )
        self.assertEqual("GREEN", overlay["status"])
        self.assertEqual(
            self.contract["overlay"]["inventory_sha256"],
            overlay["inventory_sha256"],
        )

    def test_mixed_owner_file_is_rejected_instead_of_block_slicing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-seed-mixed-owner-") as temp:
            root = Path(temp)
            relative = "common/scripted_effects/zg361_mixed.txt"
            path = root / PurePosixPath(relative)
            path.parent.mkdir(parents=True)
            path.write_bytes(
                closure.BOM
                + b"zg361_selected_effect = { always = yes }\n"
                + b"zg361_unselected_effect = { always = yes }\n"
            )
            providers, duplicates = closure._provider_map(
                root, closure.EFFECT_DIRS
            )
            self.assertEqual([], duplicates)
            with self.assertRaisesRegex(
                closure.SeedClosureError, "split by purpose first"
            ):
                closure._owner_rows(
                    root, providers, {"zg361_selected_effect"}, kind="effect"
                )

    def test_overlay_inventory_uses_explicit_print_then_freeze_contract(self) -> None:
        observed = [
            {
                "path": "common/scripted_effects/zg361_probe.txt",
                "kind": "effect",
                "definitions": 1,
                "definition_names": ["zg361_probe_effect"],
                "bytes": 12,
                "sha256": "0" * 64,
            }
        ]
        altered = copy.deepcopy(self.contract)
        altered["overlay"] = {
            "bytes": None,
            "inventory_sha256": None,
            "files": [],
        }
        pending = closure.validate_overlay_contract(
            observed, altered, allow_unfrozen=True
        )
        self.assertEqual("PENDING_FREEZE", pending["status"])
        with self.assertRaisesRegex(closure.SeedClosureError, "not frozen"):
            closure.validate_overlay_contract(observed, altered, allow_unfrozen=False)
        altered["overlay"]["bytes"] = 12
        altered["overlay"]["inventory_sha256"] = closure.overlay_inventory_sha256(
            observed
        )
        frozen = closure.validate_overlay_contract(
            observed, altered, allow_unfrozen=False
        )
        self.assertEqual("GREEN", frozen["status"])
        observed[0]["path"] = "common/scripted_effects/zg361_drift.txt"
        with self.assertRaisesRegex(closure.SeedClosureError, "SHA-256 drifted"):
            closure.validate_overlay_contract(observed, altered, allow_unfrozen=False)

    def test_boundary_contract_requires_evidence_for_every_over_hard_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-seed-boundary-") as temp:
            root = Path(temp) / "candidate"
            baseline = Path(temp) / "baseline"
            root.mkdir()
            baseline.mkdir()
            row = {
                "path": "common/scripted_effects/zg361_large.txt",
                "kind": "effect",
                "definitions": 21,
                "bytes": 1,
                "sha256": "0" * 64,
            }
            altered = copy.deepcopy(self.contract)
            altered["candidate"]["expected_effect_files_over_target"] = 1
            altered["candidate"]["expected_effect_files_over_hard_max"] = 1
            with self.assertRaisesRegex(closure.SeedClosureError, "boundary failed"):
                closure.validate_boundaries(root, baseline, [row], altered)
            altered["candidate"]["effect_boundary_exceptions"] = [
                {
                    "path": row["path"],
                    "reason": "purpose cannot be split without changing semantics",
                    "live_evidence": "artifacts/example/report.json",
                }
            ]
            result = closure.validate_boundaries(root, baseline, [row], altered)
            self.assertEqual(1, len(result["over_target"]))
            self.assertEqual(1, len(result["over_hard_max"]))
            self.assertEqual(1, len(result["exceptions"]))

    def test_whole_file_missing_and_duplicate_providers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-seed-missing-") as temp:
            root = Path(temp)
            effect = root / "common/scripted_effects/zg361_probe.txt"
            effect.parent.mkdir(parents=True)
            effect.write_bytes(
                closure.BOM
                + b"zg361_probe_effect = {\n"
                + b"\tzg361_missing_effect = yes\n"
                + b"\ttype = zg361_missing_court_position\n"
                + b"}\n"
            )
            with self.assertRaisesRegex(
                closure.SeedClosureError, "zg361_missing_effect|court_positions"
            ):
                closure.validate_whole_file_closure(root)

        with tempfile.TemporaryDirectory(prefix="zg361-seed-duplicate-") as temp:
            root = Path(temp)
            directory = root / "common/scripted_effects"
            directory.mkdir(parents=True)
            data = closure.BOM + b"zg361_probe_effect = { always = yes }\n"
            (directory / "a.txt").write_bytes(data)
            (directory / "b.txt").write_bytes(data)
            with self.assertRaisesRegex(closure.SeedClosureError, "duplicate"):
                closure.validate_whole_file_closure(root)

    def test_bom_brace_stub_and_forbidden_gates_reject_mutations(self) -> None:
        for mode in ("bom", "brace", "stub", "forbidden"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                prefix=f"zg361-seed-format-{mode}-"
            ) as temp:
                root = Path(temp)
                relative = "common/scripted_effects/zg361_probe.txt"
                path = root / PurePosixPath(relative)
                path.parent.mkdir(parents=True)
                data = closure.BOM + b"zg361_probe_effect = { always = yes }\n"
                if mode == "bom":
                    data = data[len(closure.BOM) :]
                elif mode == "brace":
                    data += b"{\n"
                elif mode == "stub":
                    data += b"# DIAGNOSTIC STUB\n"
                path.write_bytes(data)
                altered = copy.deepcopy(self.contract)
                if mode == "forbidden":
                    altered["forbidden_paths"] = [relative]
                row = {"path": relative, "kind": "effect"}
                with self.assertRaisesRegex(
                    closure.SeedClosureError, "format/no-stub/forbidden"
                ):
                    closure.validate_formatting_and_forbidden(root, [row], altered)

    def test_projection_name_is_hash_bound_before_output_creation(self) -> None:
        self._require_baseline()
        with tempfile.TemporaryDirectory(prefix="zg361-seed-projection-") as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(
                closure.SeedClosureError, "projection name drifted"
            ):
                closure.materialize(
                    output=output,
                    projection_name="different-projection-name",
                )
            self.assertFalse(output.exists())

    def test_frozen_candidate_materializes_source_product_and_replay_identically(self) -> None:
        self._require_baseline()
        with tempfile.TemporaryDirectory(prefix="zg361-seed-build-") as temp:
            output = Path(temp) / "candidate"
            result = closure.materialize(
                output=output,
                projection_name=self.contract["candidate"]["projection"],
            )
            self.assertEqual("GREEN_STATIC", result["status"])
            self.assertTrue(result["no_stubs"])
            self.assertEqual(245, result["candidate"]["expected_file_count"])
            self.assertEqual(12_097_112, result["candidate"]["expected_bytes"])
            self.assertEqual(110, result["overlay"]["file_count"])
            selection = result["checks"]["selection"]
            self.assertEqual(397, selection["full"]["effects"])
            self.assertEqual(164, selection["full"]["events"])
            self.assertEqual(314, selection["delta"]["effects"])
            self.assertEqual(142, selection["delta"]["events"])
            self.assertEqual(2, selection["delta"]["court_positions"])
            roots = result["checks"]["five_root_closure"]
            self.assertEqual(2042, roots["effects"])
            self.assertEqual(580, roots["events"])
            self.assertEqual(6, roots["triggers"])
            self.assertEqual(2, roots["court_positions"])
            self.assertEqual(9, len(roots["all_reachable_triggers"]))
            self.assertEqual(
                self.contract["candidate"]["expected_inherited_additional_triggers"],
                roots["inherited_additional_triggers"],
            )
            boundaries = result["checks"]["effect_boundaries"]
            self.assertEqual(10, boundaries["max_observed"])
            self.assertEqual([], boundaries["over_target"])
            self.assertEqual([], boundaries["over_hard_max"])
            self.assertEqual([], boundaries["exceptions"])
            replay = result["checks"]["deterministic_materialization"]
            self.assertTrue(replay["source_equals_product"])
            self.assertTrue(replay["source_equals_replay"])
            source_rows = closure.closure_utils.tree_rows(output / "source")
            self.assertEqual(
                source_rows, closure.closure_utils.tree_rows(output / "product")
            )
            self.assertEqual(
                source_rows,
                closure.closure_utils.tree_rows(output / "materialized-check"),
            )


if __name__ == "__main__":
    unittest.main()
