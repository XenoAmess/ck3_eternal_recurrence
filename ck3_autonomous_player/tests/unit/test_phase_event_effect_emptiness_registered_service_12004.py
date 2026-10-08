"""One Root-run FIRST for the optional positive-row native emptiness extension.

Only three fresh whole-V2 scenes traverse registered service. Previous chance,
trigger and role compounds are not loaded as suites or rerun.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


_CONFIG: dict[str, Path] = {}
_SCENES = ["positive_empty_nonempty", "effect_operand_unavailable", "no_positive_weight_rows"]
_LEAF = "phase_event_commander_chance_weights_v1"
_SOURCE_FIELD = "effect_emptiness_source_closed"
_EXTENSION_FIELDS = {
    "effect_empty_operand_raw", "native_effect_empty", "effect_emptiness_unavailable_reason",
}
_PRIOR_LEAVES = (
    "phase_event_role_compatibility_v1", "phase_event_commander_trigger_conditions_v1",
    "phase_event_commander_side_identity_v1",
)


def _without_extension(leaf: dict[str, object]) -> dict[str, object]:
    result = deepcopy(leaf)
    result.pop(_SOURCE_FIELD, None)
    for occurrence in result["occurrences"]:
        for condition in occurrence["conditions"]:
            for field in _EXTENSION_FIELDS:
                condition.pop(field, None)
    return result


class PhaseEventEffectEmptinessRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_new_positive_effect_emptiness_whole_registered_service(self) -> None:
        if not _CONFIG:
            raise RuntimeError("use --source-root, --wire and --output-dir")
        from test_phase_event_role_compatibility_registered_service_12004 import (
            _WholeRoleEndpoint, _snapshot_for, _PUBLIC_REVISION, _NATIVE_REVISION,
        )
        from xar_autoplayer.bridge.combat_contract import (
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY, combat_simulation_encounter_scope,
            normalize_combat_simulation_inputs, query_combat_simulation_inputs_step,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.phase_event_commander_chance_weights_contract import (
            current_commander_chance_weight_row_sets,
            current_commander_positive_weight_effect_emptiness_sets,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-effect-emptiness-registered-service-12004.json"
        report = {
            "result": "RUNNING", "wire": str(_CONFIG["wire"]),
            "source_qualified_synthetic_fixture": True, "live_queries": 0,
            "old_compounds_rerun": 0, "transport_requests": 0, "samples": [],
        }

        def persist() -> None:
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        persist()
        try:
            bundle = json.loads(_CONFIG["wire"].read_text(encoding="utf-8-sig"))
            self.assertEqual(set(bundle), {"schema_version", "scene_order", "samples"})
            self.assertEqual(bundle["schema_version"], 1)
            self.assertEqual(bundle["scene_order"], _SCENES)
            self.assertEqual(set(bundle["samples"]), set(_SCENES))
            hello = {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            }
            for sequence, scene in enumerate(_SCENES, 1):
                report["active_scene"] = scene
                base = bundle["samples"][scene]
                raw_leaf = base[_LEAF]
                scenario = base["scenario"]
                arguments = {
                    "target_province_id": base["target_province_id"],
                    "attacker_entry_province_id": scenario["attacker_entry_province_id"],
                    "attacker_army_ids": scenario["attacker_army_ids"],
                    "defender_army_ids": scenario["defender_army_ids"],
                    "expected_revision": _PUBLIC_REVISION,
                }
                step = query_combat_simulation_inputs_step(
                    arguments["target_province_id"], arguments["attacker_entry_province_id"],
                    arguments["attacker_army_ids"], arguments["defender_army_ids"],
                )
                snapshot = _snapshot_for(base, scene, hello)
                capabilities = {
                    "backend_id": "native-headless", "snapshot": True, "action_steps": [step],
                    "bridge_capabilities": ["game.state.snapshot", QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
                    "diagnostics": deepcopy(snapshot["diagnostics"]),
                }
                endpoint = _WholeRoleEndpoint(base, step, sequence)
                driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
                try:
                    with (
                        patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)),
                        patch.object(driver, "capabilities", return_value=deepcopy(capabilities)),
                    ):
                        result = await create_server(driver).call_tool("ck3_query_combat_simulation_inputs", arguments)
                    self.assertIs(result.is_error, False)
                    self.assertEqual(len(endpoint.requests), 1)
                    report["transport_requests"] += 1
                    structured = result.structured_content
                    normalized = structured["combat_simulation_inputs"]
                    self.assertEqual(normalized[_LEAF], raw_leaf)
                    self.assertEqual(normalized["completeness"], base["completeness"])
                    self.assertEqual(structured["missing_required_domains"],
                                     base["completeness"]["missing_required_domains"])
                    self.assertIn("phase_event_rng_and_effects", structured["missing_required_domains"])
                    self.assertIs(structured["input_observation_ready"], True)
                    self.assertIs(structured["monte_carlo_ready"], False)
                    for previous_leaf in _PRIOR_LEAVES:
                        self.assertEqual(normalized[previous_leaf], base[previous_leaf])
                    leaf = normalized[_LEAF]
                    self.assertIs(leaf[_SOURCE_FIELD], True)
                    self.assertIs(leaf["chance_source_closed"], True)
                    self.assertIs(leaf["native_chance_evaluation_observed"], True)
                    self.assertIs(leaf["complete_phase_effects_ready"], False)
                    self.assertEqual(leaf["status"], "available")
                    self.assertEqual(leaf["source_ck3_sha256"], CK3_12004.executable_sha256.upper())
                    expected = []
                    ordinal = 0
                    for army in normalized["armies"]:
                        if army["commander"]["status"] == "available":
                            expected.append((ordinal, army))
                            ordinal += 1
                        ordinal += len(army["knights"].get("members") or [])
                    rows = leaf["occurrences"]
                    self.assertEqual(len(rows), len(expected))
                    self.assertGreater(len(rows), 0)
                    projections = []
                    for row, (ordinal, army) in zip(rows, expected, strict=True):
                        self.assertEqual(row["occurrence_index"], ordinal)
                        self.assertEqual(row["character_id"], army["commander"]["character_id"])
                        self.assertEqual(row["source_public_cunit_id"], army["army_id"])
                        self.assertEqual(row["source_native_carmy_id"], army["native_carmy_id"])
                        self.assertNotEqual(row["source_public_cunit_id"], row["source_native_carmy_id"])
                        self.assertEqual(row["encounter_role"], army["encounter_role"])
                        self.assertEqual(len(row), 17)
                        self.assertEqual((row["admitted_count"], row["evaluated_count"],
                                          row["not_admitted_count"], row["unknown_count"]), (4, 4, 2, 0))
                        self.assertIs(row["chance_weight_observation_ready"], True)
                        self.assertEqual(row["status"], "available")
                        self.assertEqual([condition["loaded_row_index"] for condition in row["conditions"]],
                                         list(range(6)))
                        numeric = current_commander_chance_weight_row_sets(row)
                        no_positive = scene == "no_positive_weight_rows"
                        expected_positive = [] if no_positive else [0, 5]
                        self.assertEqual([item["loaded_row_index"] for item in numeric["positive_rows"]],
                                         expected_positive)
                        self.assertEqual(numeric["unknown_row_indices"], [])
                        if no_positive:
                            self.assertEqual([row["conditions"][index]["chance_raw"] for index in (0, 2, 3, 5)],
                                             [99999, -199999, 0, 99999])
                            self.assertEqual([row["conditions"][index]["selection_weight_raw"] for index in (0, 2, 3, 5)],
                                             [0, -1, 0, 0])
                        for condition in row["conditions"]:
                            self.assertEqual(len(condition), 8)
                            index = condition["loaded_row_index"]
                            if no_positive or index not in (0, 5):
                                for field in _EXTENSION_FIELDS:
                                    self.assertIsNone(condition[field])
                            elif index == 0:
                                self.assertEqual(condition["effect_empty_operand_raw"], 0)
                                self.assertIs(condition["native_effect_empty"], True)
                                self.assertIsNone(condition["effect_emptiness_unavailable_reason"])
                            elif scene == "effect_operand_unavailable":
                                self.assertIsNone(condition["effect_empty_operand_raw"])
                                self.assertIsNone(condition["native_effect_empty"])
                                self.assertTrue(condition["effect_emptiness_unavailable_reason"])
                                self.assertGreater(condition["selection_weight_raw"], 0)
                            else:
                                self.assertEqual(condition["effect_empty_operand_raw"], 2)
                                self.assertIs(condition["native_effect_empty"], False)
                                self.assertIsNone(condition["effect_emptiness_unavailable_reason"])
                        projection = current_commander_positive_weight_effect_emptiness_sets(row)
                        self.assertIs(projection["effect_emptiness_observation_ready"],
                                      scene != "effect_operand_unavailable")
                        self.assertEqual([item["loaded_row_index"] for item in projection["empty_positive_rows"]],
                                         [] if no_positive else [0])
                        self.assertEqual([item["loaded_row_index"] for item in projection["nonempty_positive_rows"]],
                                         [5] if scene == "positive_empty_nonempty" else [])
                        self.assertEqual([item["loaded_row_index"] for item in projection["unknown_positive_rows"]],
                                         [5] if scene == "effect_operand_unavailable" else [])
                        self.assertEqual(sum(len(projection[field]) for field in (
                            "empty_positive_rows", "nonempty_positive_rows", "unknown_positive_rows",
                        )), len(numeric["positive_rows"]))
                        projections.append(projection)
                    self.assertEqual(endpoint.base, base)
                    self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"], normalized)
                    roundtrip = json.loads(result.model_dump_json(by_alias=True))
                    self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                    self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                    self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                    whole_path = output / f"{scene}-whole-registered-service.json"
                    whole_path.write_text(json.dumps(roundtrip, indent=2) + "\n", encoding="utf-8")
                    if scene == "positive_empty_nonempty":
                        options = {
                            "expected_target_province_id": arguments["target_province_id"],
                            "expected_attacker_entry_province_id": arguments["attacker_entry_province_id"],
                            "expected_encounter_scope": combat_simulation_encounter_scope(
                                snapshot, arguments["attacker_army_ids"], arguments["defender_army_ids"]),
                        }
                        legacy = deepcopy(base)
                        legacy[_LEAF] = _without_extension(raw_leaf)
                        legacy_normalized = normalize_combat_simulation_inputs(legacy, **options)
                        self.assertEqual(legacy_normalized[_LEAF], legacy[_LEAF])
                        self.assertEqual(len(legacy_normalized[_LEAF]), 9)
                        for row in legacy_normalized[_LEAF]["occurrences"]:
                            self.assertTrue(all(len(condition) == 5 for condition in row["conditions"]))
                            projected = current_commander_positive_weight_effect_emptiness_sets(row)
                            self.assertEqual([item["loaded_row_index"] for item in projected["unknown_positive_rows"]], [0, 5])
                            self.assertIs(projected["effect_emptiness_observation_ready"], False)
                        malformed = deepcopy(base)
                        malformed[_LEAF]["occurrences"][0]["conditions"][5]["native_effect_empty"] = True
                        isolated = normalize_combat_simulation_inputs(malformed, **options)
                        self.assertEqual(_without_extension(isolated[_LEAF]), _without_extension(raw_leaf))
                        self.assertEqual(isolated[_LEAF]["status"], "available")
                        failed_condition = isolated[_LEAF]["occurrences"][0]["conditions"][5]
                        self.assertIsNone(failed_condition["effect_empty_operand_raw"])
                        self.assertIsNone(failed_condition["native_effect_empty"])
                        self.assertTrue(failed_condition["effect_emptiness_unavailable_reason"])
                        self.assertEqual(isolated["completeness"], normalized["completeness"])
                        for previous_leaf in _PRIOR_LEAVES:
                            self.assertEqual(isolated[previous_leaf], normalized[previous_leaf])
                    self.assertEqual(len(endpoint.requests), 1)
                    report["samples"].append({
                        "scene": scene, "transport_requests": 1,
                        "numeric_leaf_status": "available", "emptiness_sets": projections,
                        "whole_result": str(whole_path),
                        "base_input_observation_ready": True, "base_monte_carlo_ready": False,
                    })
                finally:
                    endpoint.close()
                persist()
            self.assertEqual(report["transport_requests"], 3)
            report["result"] = "GREEN"
            persist()
        except BaseException as error:
            report["result"] = "RED"
            report["failure"] = f"{type(error).__name__}: {error}"
            persist()
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--wire", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    _CONFIG.update({
        "source_root": arguments.source_root.resolve(), "wire": arguments.wire.resolve(),
        "output_dir": arguments.output_dir.resolve(),
    })
    sys.path.insert(0, str(_CONFIG["source_root"]))
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventEffectEmptinessRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "report": str(_CONFIG["output_dir"] / "phase-event-effect-emptiness-registered-service-12004.json"),
    }))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
