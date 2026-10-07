"""One Root-run FIRST for three new production-serialized Commander trigger scenes.

This script is authored without execution. It imports only reusable whole-wire
helpers from the prior role module and does not run any prior test class.
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
_SCENES = ["native_mixed", "identity_mismatch", "row_pointer_missing"]
_LEAF = "phase_event_commander_trigger_conditions_v1"
_ROLE_LEAF = "phase_event_role_compatibility_v1"
_IDENTITY_LEAF = "phase_event_commander_side_identity_v1"


class PhaseEventCommanderTriggerConditionsRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_new_commander_trigger_whole_registered_service(self) -> None:
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
        from xar_autoplayer.bridge.phase_event_commander_trigger_conditions_contract import (
            current_commander_role_trigger_row_sets,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-commander-trigger-conditions-registered-service-12004.json"
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
                    self.assertIs(raw_leaf["trigger_source_closed"], True)
                    self.assertIs(raw_leaf["complete_phase_effects_ready"], False)
                    self.assertIs(raw_leaf["native_role_and_trigger_evaluation_observed"],
                                  scene != "identity_mismatch")
                    self.assertEqual(raw_leaf["source_ck3_sha256"], CK3_12004.executable_sha256.upper())
                    self.assertEqual(raw_leaf["status"], "available" if scene == "native_mixed" else "partial")
                    self.assertEqual(normalized[_ROLE_LEAF], base[_ROLE_LEAF])
                    self.assertEqual(normalized[_IDENTITY_LEAF], base[_IDENTITY_LEAF])
                    self.assertEqual([row["role_operand_raw"]
                                      for row in normalized[_ROLE_LEAF]["loaded_registry"]["rows"]],
                                     [0, 1, 0, 2])
                    expected = []
                    ordinal = 0
                    for army_index, army in enumerate(normalized["armies"]):
                        if army["commander"]["status"] == "available":
                            expected.append((ordinal, army_index, army))
                            ordinal += 1
                        ordinal += len(army["knights"].get("members") or [])
                    rows = normalized[_LEAF]["occurrences"]
                    self.assertEqual(len(rows), len(expected))
                    self.assertGreater(len(rows), 0)
                    identity_by_ordinal = {row["occurrence_index"]: row
                                           for row in normalized[_IDENTITY_LEAF]["occurrences"]}
                    projections = []
                    for row, (ordinal, army_index, army) in zip(rows, expected, strict=True):
                        self.assertEqual(row["occurrence_index"], ordinal)
                        self.assertEqual(row["character_id"], army["commander"]["character_id"])
                        self.assertEqual(row["source_public_cunit_id"], army["army_id"])
                        self.assertEqual(row["source_native_carmy_id"], army["native_carmy_id"])
                        self.assertNotEqual(row["source_public_cunit_id"], row["source_native_carmy_id"])
                        self.assertEqual(row["encounter_role"], army["encounter_role"])
                        self.assertEqual(row["requested_role_raw"], 0)
                        identity = identity_by_ordinal[ordinal]
                        self.assertEqual(row["actual_combat_full_id_raw"],
                                         identity["actual_selected_combat_full_id_raw"])
                        self.assertEqual(row["actual_combat_full_id_raw"], 0x87000321 + army_index)
                        self.assertEqual(row["actual_side_index"], identity["actual_side_index"])
                        self.assertNotEqual(identity["actual_side_role"], army["encounter_role"])
                        self.assertEqual([condition["loaded_row_index"] for condition in row["conditions"]],
                                         [0, 1, 2, 3])
                        conditions = row["conditions"]
                        self.assertEqual([condition["role_compatible"] for condition in conditions],
                                         [True, False, True, False])
                        for row_index in (1, 3):
                            self.assertIsNone(conditions[row_index]["native_trigger_valid"])
                            self.assertIs(conditions[row_index]["role_and_trigger_valid"], False)
                            self.assertIsNone(conditions[row_index]["unavailable_reason"])
                        self.assertEqual(row["role_compatible_count"], 2)
                        projection = current_commander_role_trigger_row_sets(row)
                        if scene == "identity_mismatch":
                            self.assertIs(row["current_commander_context_ready"], False)
                            self.assertIs(identity["full_id_equal"], False)
                            self.assertEqual(identity["actual_side_commander_full_id_raw"] & 0xFFFFFF,
                                             row["character_id"] & 0xFFFFFF)
                            self.assertNotEqual(identity["actual_side_commander_full_id_raw"], row["character_id"])
                            for row_index in (0, 2):
                                self.assertIsNone(conditions[row_index]["native_trigger_valid"])
                                self.assertIsNone(conditions[row_index]["role_and_trigger_valid"])
                                self.assertTrue(conditions[row_index]["unavailable_reason"])
                            self.assertEqual((row["evaluated_count"], row["admitted_count"], row["unknown_count"]),
                                             (0, 0, 2))
                            self.assertEqual(projection["admitted_row_indices"], [])
                            self.assertEqual(projection["rejected_row_indices"], [1, 3])
                            self.assertEqual(projection["unknown_row_indices"], [0, 2])
                        else:
                            self.assertIs(row["current_commander_context_ready"], True)
                            self.assertIs(identity["full_id_equal"], True)
                            self.assertIsInstance(row["loaded_named_side_key_raw"], int)
                            self.assertIs(conditions[0]["native_trigger_valid"], False)
                            self.assertIs(conditions[0]["role_and_trigger_valid"], False)
                            self.assertIsNone(conditions[0]["unavailable_reason"])
                            self.assertEqual(projection["rejected_row_indices"], [0, 1, 3])
                            if scene == "native_mixed":
                                self.assertIs(conditions[2]["native_trigger_valid"], True)
                                self.assertIs(conditions[2]["role_and_trigger_valid"], True)
                                self.assertIsNone(conditions[2]["unavailable_reason"])
                                self.assertEqual((row["evaluated_count"], row["admitted_count"], row["unknown_count"]),
                                                 (2, 1, 0))
                                self.assertEqual(projection["admitted_row_indices"], [2])
                                self.assertEqual(projection["unknown_row_indices"], [])
                            else:
                                self.assertIsNone(conditions[2]["native_trigger_valid"])
                                self.assertIsNone(conditions[2]["role_and_trigger_valid"])
                                self.assertTrue(conditions[2]["unavailable_reason"])
                                self.assertEqual((row["evaluated_count"], row["admitted_count"], row["unknown_count"]),
                                                 (1, 0, 1))
                                self.assertEqual(projection["admitted_row_indices"], [])
                                self.assertEqual(projection["unknown_row_indices"], [2])
                        ready = scene == "native_mixed"
                        self.assertIs(row["role_trigger_observation_ready"], ready)
                        self.assertEqual(row["status"], "available" if ready else "partial")
                        self.assertIs(projection["role_trigger_observation_ready"], ready)
                        projections.append(projection)
                    self.assertEqual(endpoint.base, base)
                    self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"], normalized)
                    roundtrip = json.loads(result.model_dump_json(by_alias=True))
                    self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                    self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                    self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                    whole_path = output / f"{scene}-whole-registered-service.json"
                    whole_path.write_text(json.dumps(roundtrip, indent=2) + "\n", encoding="utf-8")
                    if scene == "native_mixed":
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
                        malformed[_LEAF]["occurrences"][0]["admitted_count"] += 1
                        isolated = normalize_combat_simulation_inputs(malformed, **options)
                        self.assertEqual(isolated[_LEAF]["status"], "unavailable")
                        self.assertEqual(isolated["completeness"], normalized["completeness"])
                        self.assertEqual(isolated[_ROLE_LEAF], normalized[_ROLE_LEAF])
                        self.assertEqual(isolated[_IDENTITY_LEAF], normalized[_IDENTITY_LEAF])
                        empty_catalog = deepcopy(base)
                        empty_catalog[_ROLE_LEAF]["loaded_registry"].update({
                            "status": "available", "count_raw": 0,
                            "rows": [], "unavailable_reason": None,
                        })
                        for role_row in empty_catalog[_ROLE_LEAF]["occurrences"]:
                            role_row["conditions"] = []
                        empty_catalog[_LEAF].update({
                            "status": "available", "unavailable_reason": None,
                            "native_role_and_trigger_evaluation_observed": False,
                        })
                        for trigger_row in empty_catalog[_LEAF]["occurrences"]:
                            trigger_row.update({
                                "conditions": [], "role_compatible_count": 0,
                                "evaluated_count": 0, "admitted_count": 0, "unknown_count": 0,
                                "role_trigger_observation_ready": True,
                                "status": "available", "unavailable_reason": None,
                            })
                        empty_normalized = normalize_combat_simulation_inputs(empty_catalog, **options)
                        self.assertEqual(empty_normalized[_LEAF], empty_catalog[_LEAF])
                        self.assertEqual(empty_normalized["completeness"], normalized["completeness"])
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
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventCommanderTriggerConditionsRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "report": str(_CONFIG["output_dir"] / "phase-event-commander-trigger-conditions-registered-service-12004.json"),
    }))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
