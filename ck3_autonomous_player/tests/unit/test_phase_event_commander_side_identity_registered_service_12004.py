"""One Root-run FIRST for new physical Side Commander identity observations.

Only the three new whole-V2 scenes traverse registered service. Prior role,
caller and calendar compounds are neither loaded as suites nor rerun.
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
_SCENES = ["matched", "different_generation", "ambiguous_side"]
_LEAF = "phase_event_commander_side_identity_v1"
_SIDE_FIELDS = (
    "actual_side_index", "actual_side_role", "actual_side_parent_matches_selected_combat",
    "actual_side_commander_full_id_raw", "actual_side_commander_present", "full_id_equal",
)


class PhaseEventCommanderSideIdentityRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_new_side_identity_whole_registered_service(self) -> None:
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
        from xar_autoplayer.bridge.phase_event_commander_side_identity_contract import (
            normalize_phase_event_commander_side_identity_v1,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-commander-side-identity-registered-service-12004.json"
        report = {
            "result": "RUNNING", "wire": str(_CONFIG["wire"]),
            "source_qualified_synthetic_fixture": True, "live_queries": 0,
            "old_compounds_rerun": 0, "samples": [],
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
                    structured = result.structured_content
                    normalized = structured["combat_simulation_inputs"]
                    self.assertEqual(normalized[_LEAF], raw_leaf)
                    self.assertEqual(normalized["completeness"], base["completeness"])
                    self.assertEqual(structured["missing_required_domains"],
                                     base["completeness"]["missing_required_domains"])
                    self.assertIn("phase_event_rng_and_effects", structured["missing_required_domains"])
                    self.assertIs(structured["input_observation_ready"], True)
                    self.assertIs(structured["monte_carlo_ready"], False)
                    self.assertIs(raw_leaf["commander_side_identity_source_closed"], True)
                    self.assertIs(raw_leaf["native_candidate_admission_observed"], False)
                    self.assertIs(raw_leaf["complete_phase_effects_ready"], False)
                    self.assertEqual(raw_leaf["source_ck3_sha256"], CK3_12004.executable_sha256.upper())
                    self.assertEqual(raw_leaf["status"], "unavailable" if scene == "ambiguous_side" else "available")
                    rows = normalized[_LEAF]["occurrences"]
                    expected = []
                    ordinal = 0
                    for army in normalized["armies"]:
                        if army["commander"]["status"] == "available":
                            expected.append((ordinal, army))
                            ordinal += 1
                        ordinal += len(army["knights"].get("members") or [])
                    self.assertEqual(len(rows), len(expected))
                    self.assertGreater(len(rows), 0)
                    comparisons = []
                    for row, (ordinal, army) in zip(rows, expected, strict=True):
                        self.assertEqual(row["occurrence_index"], ordinal)
                        self.assertEqual(row["character_id"], army["commander"]["character_id"])
                        self.assertEqual(row["source_public_cunit_id"], army["army_id"])
                        self.assertEqual(row["source_native_carmy_id"], army["native_carmy_id"])
                        self.assertNotEqual(row["source_public_cunit_id"], row["source_native_carmy_id"])
                        self.assertEqual(row["actual_physical_army_full_id_raw"],
                                         army["native_carmy_id"] & 0xFFFFFFFF)
                        self.assertEqual(row["encounter_role"], army["encounter_role"])
                        self.assertIs(row["source_active_combat"], True)
                        self.assertIsNotNone(row["actual_selected_combat_full_id_raw"])
                        counts = [row["attacker_membership_count"], row["defender_membership_count"]]
                        if scene == "ambiguous_side":
                            self.assertEqual(sorted(counts), [1, 2])
                            self.assertIs(row["unique_physical_membership"], False)
                            self.assertEqual(row["status"], "unavailable")
                            self.assertTrue(row["unavailable_reason"])
                            for field in _SIDE_FIELDS:
                                self.assertIsNone(row[field])
                        else:
                            self.assertEqual(sorted(counts), [0, 2])
                            self.assertIs(row["unique_physical_membership"], True)
                            self.assertEqual(row["status"], "available")
                            actual_side = 0 if counts[0] else 1
                            self.assertEqual(row["actual_side_index"], actual_side)
                            self.assertEqual(row["actual_side_role"], "attacker" if actual_side == 0 else "defender")
                            self.assertNotEqual(row["actual_side_role"], row["encounter_role"])
                            self.assertIs(row["actual_side_parent_matches_selected_combat"], True)
                            self.assertIs(row["actual_side_commander_present"], True)
                            actual_commander = row["actual_side_commander_full_id_raw"]
                            if scene == "matched":
                                self.assertEqual(actual_commander, row["character_id"])
                                self.assertIs(row["full_id_equal"], True)
                            else:
                                self.assertEqual(actual_commander, row["character_id"] ^ 0x01000000)
                                self.assertEqual(actual_commander & 0xFFFFFF, row["character_id"] & 0xFFFFFF)
                                self.assertNotEqual(actual_commander, row["character_id"])
                                self.assertIs(row["full_id_equal"], False)
                        comparisons.append({
                            "occurrence_index": ordinal,
                            "source_public_cunit_id": row["source_public_cunit_id"],
                            "source_native_carmy_id": row["source_native_carmy_id"],
                            "character_id": row["character_id"],
                            "actual_side_index": row["actual_side_index"],
                            "actual_side_commander_full_id_raw": row["actual_side_commander_full_id_raw"],
                            "full_id_equal": row["full_id_equal"],
                        })
                    self.assertEqual(endpoint.base, base)
                    self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"], normalized)
                    roundtrip = json.loads(result.model_dump_json(by_alias=True))
                    self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                    self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                    self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                    if "phase_event_role_compatibility_v1" in base:
                        self.assertEqual(normalized["phase_event_role_compatibility_v1"],
                                         base["phase_event_role_compatibility_v1"])
                    report["samples"].append({
                        "scene": scene, "transport_requests": 1,
                        "leaf_status": raw_leaf["status"], "comparisons": comparisons,
                        "base_input_observation_ready": True, "base_monte_carlo_ready": False,
                    })
                    if scene == "matched":
                        options = {
                            "expected_target_province_id": arguments["target_province_id"],
                            "expected_attacker_entry_province_id": arguments["attacker_entry_province_id"],
                            "expected_encounter_scope": combat_simulation_encounter_scope(
                                snapshot, arguments["attacker_army_ids"], arguments["defender_army_ids"]),
                        }
                        legacy = deepcopy(base)
                        del legacy[_LEAF]
                        self.assertIsNone(normalize_combat_simulation_inputs(legacy, **options).get(_LEAF))
                        malformed = deepcopy(base)
                        malformed[_LEAF]["native_candidate_admission_observed"] = True
                        isolated = normalize_combat_simulation_inputs(malformed, **options)
                        self.assertEqual(isolated[_LEAF]["status"], "unavailable")
                        self.assertEqual(isolated["completeness"], normalized["completeness"])
                        inactive = deepcopy(raw_leaf)
                        inactive["status"] = "unavailable"
                        inactive["unavailable_reason"] = "physical_army_not_in_active_combat"
                        for row in inactive["occurrences"]:
                            row.update({
                                "status": "unavailable",
                                "unavailable_reason": "physical_army_not_in_active_combat",
                                "actual_selected_combat_full_id_raw": 0xFFFFFFFF,
                                "source_active_combat": False,
                                "attacker_membership_count": None, "defender_membership_count": None,
                                "unique_physical_membership": None,
                            })
                            for field in _SIDE_FIELDS:
                                row[field] = None
                        self.assertEqual(normalize_phase_event_commander_side_identity_v1(
                            inactive, armies=normalized["armies"]), inactive)
                        self.assertEqual(len(endpoint.requests), 1)
                finally:
                    endpoint.close()
                persist()
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
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventCommanderSideIdentityRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "report": str(_CONFIG["output_dir"] / "phase-event-commander-side-identity-registered-service-12004.json"),
    }))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
