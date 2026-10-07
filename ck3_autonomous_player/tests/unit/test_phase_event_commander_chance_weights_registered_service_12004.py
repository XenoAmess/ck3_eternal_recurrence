"""One Root-run FIRST for new signed compiled chance/weight whole-V2 scenes.

Authored without execution. Reuses only whole-wire helpers; prior GREEN
classes/compounds are not loaded or rerun.
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
_SCENES = ["signed_weights", "demanded_receiver_missing", "no_admitted_rows"]
_LEAF = "phase_event_commander_chance_weights_v1"
_ROLE_LEAF = "phase_event_role_compatibility_v1"
_TRIGGER_LEAF = "phase_event_commander_trigger_conditions_v1"
_IDENTITY_LEAF = "phase_event_commander_side_identity_v1"
_RAW_BY_ROW = {0: 250001, 2: -199999, 3: 99999, 5: 100000}
_WEIGHT_BY_ROW = {0: 2, 2: -1, 3: 0, 5: 1}


class PhaseEventCommanderChanceWeightsRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_new_compiled_chance_weights_whole_registered_service(self) -> None:
        if not _CONFIG:
            raise RuntimeError("use --source-root, --wire and --output-dir")
        from test_phase_event_role_compatibility_registered_service_12004 import (
            _WholeRoleEndpoint, _snapshot_for, _PUBLIC_REVISION, _NATIVE_REVISION,
        )
        from xar_autoplayer.bridge.combat_contract import (
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            combat_simulation_encounter_scope,
            normalize_combat_simulation_inputs,
            query_combat_simulation_inputs_step,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.phase_event_commander_chance_weights_contract import (
            current_commander_chance_weight_row_sets,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-commander-chance-weights-registered-service-12004.json"
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
                    self.assertIs(raw_leaf["chance_source_closed"], True)
                    self.assertIs(raw_leaf["native_chance_evaluation_observed"], scene != "no_admitted_rows")
                    self.assertIs(raw_leaf["complete_phase_effects_ready"], False)
                    self.assertEqual(raw_leaf["source_ck3_sha256"], CK3_12004.executable_sha256.upper())
                    self.assertEqual(raw_leaf["status"],
                                     "partial" if scene == "demanded_receiver_missing" else "available")
                    for previous_leaf in (_ROLE_LEAF, _TRIGGER_LEAF, _IDENTITY_LEAF):
                        self.assertEqual(normalized[previous_leaf], base[previous_leaf])
                    self.assertEqual([row["role_operand_raw"]
                                      for row in normalized[_ROLE_LEAF]["loaded_registry"]["rows"]],
                                     [0, 1, 0, 0, 0, 0])
                    expected = []
                    ordinal = 0
                    for army in normalized["armies"]:
                        if army["commander"]["status"] == "available":
                            expected.append((ordinal, army))
                            ordinal += 1
                        ordinal += len(army["knights"].get("members") or [])
                    rows = normalized[_LEAF]["occurrences"]
                    self.assertEqual(len(rows), len(expected))
                    self.assertGreater(len(rows), 0)
                    trigger_by_ordinal = {row["occurrence_index"]: row
                                          for row in normalized[_TRIGGER_LEAF]["occurrences"]}
                    projections = []
                    for row, (ordinal, army) in zip(rows, expected, strict=True):
                        self.assertEqual(row["occurrence_index"], ordinal)
                        self.assertEqual(row["character_id"], army["commander"]["character_id"])
                        self.assertEqual(row["source_public_cunit_id"], army["army_id"])
                        self.assertEqual(row["source_native_carmy_id"], army["native_carmy_id"])
                        self.assertNotEqual(row["source_public_cunit_id"], row["source_native_carmy_id"])
                        self.assertEqual(row["encounter_role"], army["encounter_role"])
                        trigger = trigger_by_ordinal[ordinal]
                        for field in ("actual_combat_full_id_raw", "actual_side_index", "loaded_named_side_key_raw"):
                            self.assertEqual(row[field], trigger[field])
                        self.assertIs(row["current_commander_context_ready"], True)
                        self.assertEqual([condition["loaded_row_index"] for condition in row["conditions"]],
                                         list(range(6)))
                        self.assertEqual([condition["role_and_trigger_valid"] for condition in row["conditions"]],
                                         [False] * 6 if scene == "no_admitted_rows"
                                         else [True, False, True, True, False, True])
                        self.assertEqual([condition["role_and_trigger_valid"] for condition in trigger["conditions"]],
                                         [condition["role_and_trigger_valid"] for condition in row["conditions"]])
                        for condition in row["conditions"]:
                            row_index = condition["loaded_row_index"]
                            if scene == "no_admitted_rows" or row_index in (1, 4):
                                self.assertIsNone(condition["chance_raw"])
                                self.assertIsNone(condition["selection_weight_raw"])
                                self.assertIsNone(condition["unavailable_reason"])
                            elif scene == "demanded_receiver_missing" and row_index == 2:
                                self.assertIs(condition["role_and_trigger_valid"], True)
                                self.assertIsNone(condition["chance_raw"])
                                self.assertIsNone(condition["selection_weight_raw"])
                                self.assertTrue(condition["unavailable_reason"])
                            else:
                                self.assertEqual(condition["chance_raw"], _RAW_BY_ROW[row_index])
                                self.assertEqual(condition["selection_weight_raw"], _WEIGHT_BY_ROW[row_index])
                                self.assertIsNone(condition["unavailable_reason"])
                        projection = current_commander_chance_weight_row_sets(row)
                        ready = scene != "demanded_receiver_missing"
                        self.assertIs(row["chance_weight_observation_ready"], ready)
                        self.assertIs(projection["chance_weight_observation_ready"], ready)
                        self.assertEqual(row["status"], "available" if ready else "partial")
                        if scene == "no_admitted_rows":
                            self.assertEqual((row["admitted_count"], row["evaluated_count"],
                                              row["not_admitted_count"], row["unknown_count"]), (0, 0, 6, 0))
                            self.assertEqual(projection["positive_rows"], [])
                            self.assertEqual(projection["nonpositive_rows"], [])
                            self.assertEqual(projection["not_admitted_row_indices"], list(range(6)))
                            self.assertEqual(projection["unknown_row_indices"], [])
                        else:
                            missing = scene == "demanded_receiver_missing"
                            self.assertEqual((row["admitted_count"], row["evaluated_count"],
                                              row["not_admitted_count"], row["unknown_count"]),
                                             (4, 3 if missing else 4, 2, 1 if missing else 0))
                            self.assertEqual(projection["positive_rows"], [
                                {"loaded_row_index": 0, "chance_raw": 250001, "selection_weight_raw": 2},
                                {"loaded_row_index": 5, "chance_raw": 100000, "selection_weight_raw": 1},
                            ])
                            expected_nonpositive = [
                                {"loaded_row_index": 3, "chance_raw": 99999, "selection_weight_raw": 0},
                            ]
                            if not missing:
                                expected_nonpositive.insert(0, {
                                    "loaded_row_index": 2, "chance_raw": -199999, "selection_weight_raw": -1,
                                })
                            self.assertEqual(projection["nonpositive_rows"], expected_nonpositive)
                            self.assertEqual(projection["not_admitted_row_indices"], [1, 4])
                            self.assertEqual(projection["unknown_row_indices"], [2] if missing else [])
                        projections.append(projection)
                    self.assertEqual(endpoint.base, base)
                    self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"], normalized)
                    roundtrip = json.loads(result.model_dump_json(by_alias=True))
                    self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                    self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                    self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                    whole_path = output / f"{scene}-whole-registered-service.json"
                    whole_path.write_text(json.dumps(roundtrip, indent=2) + "\n", encoding="utf-8")
                    if scene == "signed_weights":
                        options = {
                            "expected_target_province_id": arguments["target_province_id"],
                            "expected_attacker_entry_province_id": arguments["attacker_entry_province_id"],
                            "expected_encounter_scope": combat_simulation_encounter_scope(
                                snapshot, arguments["attacker_army_ids"], arguments["defender_army_ids"]),
                        }
                        legacy = deepcopy(base)
                        del legacy[_LEAF]
                        legacy_normalized = normalize_combat_simulation_inputs(legacy, **options)
                        self.assertIsNone(legacy_normalized.get(_LEAF))
                        self.assertEqual(legacy_normalized["completeness"], normalized["completeness"])
                        malformed = deepcopy(base)
                        malformed[_LEAF]["occurrences"][0]["conditions"][2]["selection_weight_raw"] = -2
                        isolated = normalize_combat_simulation_inputs(malformed, **options)
                        self.assertEqual(isolated[_LEAF]["status"], "unavailable")
                        self.assertEqual(isolated["completeness"], normalized["completeness"])
                        for previous_leaf in (_ROLE_LEAF, _TRIGGER_LEAF, _IDENTITY_LEAF):
                            self.assertEqual(isolated[previous_leaf], normalized[previous_leaf])
                    self.assertEqual(len(endpoint.requests), 1)
                    report["samples"].append({
                        "scene": scene, "transport_requests": 1,
                        "leaf_status": raw_leaf["status"], "row_sets": projections,
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
        "source_root": arguments.source_root.resolve(),
        "wire": arguments.wire.resolve(), "output_dir": arguments.output_dir.resolve(),
    })
    sys.path.insert(0, str(_CONFIG["source_root"]))
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventCommanderChanceWeightsRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "report": str(_CONFIG["output_dir"] / "phase-event-commander-chance-weights-registered-service-12004.json"),
    }))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
