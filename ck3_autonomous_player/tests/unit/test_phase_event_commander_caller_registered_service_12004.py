"""One new Root-run FIRST for actual47-qualified Commander role arguments.

Consumes one full V2 body from the integrated production native serializer.
No old test class, three-scene bundle, scheduler, selector or live game is run.
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
_LEAF = "phase_event_role_compatibility_v1"


class PhaseEventCommanderCallerRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_actual47_commander_caller_registered_service(self) -> None:
        if not _CONFIG:
            raise RuntimeError("use --source-root, --wire and --output-dir")
        # Reuse transport/snapshot helpers only; never load or run the old class.
        from test_phase_event_role_compatibility_registered_service_12004 import (
            _WholeRoleEndpoint, _snapshot_for,
            _PUBLIC_REVISION, _NATIVE_REVISION, _DATE_RAW,
        )
        from xar_autoplayer.bridge.combat_contract import (
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            query_combat_simulation_inputs_step,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.phase_event_role_compatibility_contract import (
            compatible_loaded_row_indices,
            normalize_phase_event_role_compatibility_v1,
            source_qualified_role_row_indices,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-commander-caller-registered-service-12004.json"
        report = {
            "result": "RUNNING", "wire": str(_CONFIG["wire"]),
            "source_qualified_synthetic_fixture": True, "actual47_source_qualified": True,
            "live_queries": 0, "old_role_three_scene_checks_rerun": 0,
            "transport_requests": 0, "role_argument_projection": [],
        }

        def persist() -> None:
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        persist()
        try:
            base = json.loads(_CONFIG["wire"].read_text(encoding="utf-8-sig"))
            self.assertIsInstance(base, dict)
            self.assertIn("armies", base)
            self.assertNotIn("samples", base)
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
            hello = {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            }
            snapshot = _snapshot_for(base, "actual47_commander_caller", hello)
            capabilities = {
                "backend_id": "native-headless", "snapshot": True, "action_steps": [step],
                "bridge_capabilities": ["game.state.snapshot", QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
                "diagnostics": deepcopy(snapshot["diagnostics"]),
            }
            endpoint = _WholeRoleEndpoint(base, step, 1)
            driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
            try:
                with (
                    patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)),
                    patch.object(driver, "capabilities", return_value=deepcopy(capabilities)),
                ):
                    result = await create_server(driver).call_tool("ck3_query_combat_simulation_inputs", arguments)
                self.assertIs(result.is_error, False)
                self.assertEqual(len(endpoint.requests), 1)
                report["transport_requests"] = len(endpoint.requests)
                structured = result.structured_content
                normalized = structured["combat_simulation_inputs"]
                self.assertEqual(normalized[_LEAF], raw_leaf)
                self.assertEqual(normalized["completeness"], base["completeness"])
                self.assertEqual(structured["missing_required_domains"],
                                 base["completeness"]["missing_required_domains"])
                self.assertIn("phase_event_rng_and_effects", structured["missing_required_domains"])
                self.assertIs(structured["input_observation_ready"], True)
                self.assertIs(structured["monte_carlo_ready"], False)
                self.assertEqual(raw_leaf["status"], "available")
                self.assertEqual(raw_leaf["source_ck3_sha256"], CK3_12004.executable_sha256.upper())
                self.assertIs(raw_leaf["loaded_registry_source_closed"], True)
                self.assertIs(raw_leaf["role_compare_source_closed"], True)
                self.assertIs(raw_leaf["native_candidate_admission_observed"], False)
                self.assertIs(raw_leaf["complete_phase_effects_ready"], False)
                registry = raw_leaf["loaded_registry"]
                self.assertEqual(registry["status"], "available")
                self.assertEqual(registry["count_raw"], 4)
                self.assertEqual([row["role_operand_raw"] for row in registry["rows"]], [0, 1, 7, 1])
                occurrences = normalized[_LEAF]["occurrences"]
                self.assertEqual(len(occurrences), sum(
                    int(army["commander"]["status"] == "available")
                    + len(army["knights"].get("members") or []) for army in normalized["armies"]
                ))
                commander_count = knight_count = 0
                for ordinal, occurrence in enumerate(occurrences):
                    self.assertEqual(occurrence["occurrence_index"], ordinal)
                    self.assertIs(occurrence["native_role_argument_source_closed"], True)
                    is_knight = occurrence["phase_role"] == "knight"
                    self.assertEqual(occurrence["requested_role_raw"], int(is_knight))
                    if is_knight:
                        knight_count += 1
                    else:
                        commander_count += 1
                    expected = [1, 3] if is_knight else [0]
                    self.assertEqual(source_qualified_role_row_indices(occurrence), expected)
                    self.assertEqual(compatible_loaded_row_indices(occurrence), expected)
                    report["role_argument_projection"].append({
                        "occurrence_index": ordinal, "character_id": occurrence["character_id"],
                        "phase_role": occurrence["phase_role"],
                        "source_qualified_role_row_indices": expected,
                        "current_participant_identity_observed": False,
                        "native_candidate_admission_observed": False,
                    })
                self.assertGreater(commander_count, 0)
                self.assertGreater(knight_count, 0)
                self.assertEqual(endpoint.base, base)
                self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"], normalized)
                roundtrip = json.loads(result.model_dump_json(by_alias=True))
                self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                self.assertEqual(structured["source"]["date_raw"], _DATE_RAW)

                # Old conditional Commander false remains a valid pure leaf.
                # This does not issue another query or repeat the old compound.
                legacy = deepcopy(raw_leaf)
                for occurrence in legacy["occurrences"]:
                    if occurrence["phase_role"] == "commander":
                        occurrence["native_role_argument_source_closed"] = False
                legacy_normalized = normalize_phase_event_role_compatibility_v1(
                    legacy, armies=normalized["armies"],
                )
                self.assertEqual(legacy_normalized, legacy)
                for occurrence in legacy_normalized["occurrences"]:
                    if occurrence["phase_role"] == "commander":
                        self.assertIs(occurrence["native_role_argument_source_closed"], False)
                        self.assertIsNone(source_qualified_role_row_indices(occurrence))
                        self.assertEqual(compatible_loaded_row_indices(occurrence), [0])
                    else:
                        self.assertEqual(source_qualified_role_row_indices(occurrence), [1, 3])
                self.assertEqual(len(endpoint.requests), 1)
                report.update({
                    "result": "GREEN", "commander_occurrences": commander_count,
                    "knight_occurrences": knight_count, "legacy_conditional_false_preserved": True,
                    "base_input_observation_ready": True, "base_monte_carlo_ready": False,
                    "current_side_identity_or_admission_credit": False,
                })
                persist()
            finally:
                endpoint.close()
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
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventCommanderCallerRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "report": str(_CONFIG["output_dir"] / "phase-event-commander-caller-registered-service-12004.json"),
    }))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
