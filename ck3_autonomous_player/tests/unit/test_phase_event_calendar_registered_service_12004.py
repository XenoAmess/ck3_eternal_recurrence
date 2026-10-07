"""One Root-run compound FIRST for the native whole V2 calendar fixture.

Consumes source-qualified synthetic memory, not an actual4 live observation.
The child authors this consumer; Root supplies the compiled bundle and runs it.
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
_SCENES = ["available", "zero_interval", "unavailable"]
_PUBLIC_REVISION = 42
_NATIVE_REVISION = 7
_DATE_RAW = 53288448
_LEAF = "phase_event_calendar_observation_v1"


class _WholeCalendarEndpoint:
    pipe_name = r"\\.\pipe\xar-calendar-12004-compiled-fixture"

    def __init__(self, base: dict[str, object], step: str, query_sequence: int):
        self.base = deepcopy(base)
        self.step = step
        self.query_sequence = query_sequence
        self.requests: list[dict[str, object]] = []
        self.on_frame = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def send(self, request: dict[str, object]) -> None:
        if (request.get("type") != "execute_step" or request.get("step") != self.step
                or request.get("expected_revision") != _NATIVE_REVISION):
            raise AssertionError("unexpected compiled calendar fixture request")
        self.requests.append(deepcopy(request))
        self.on_frame({
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": {
                "step": self.step, "accepted": True, "status": "available",
                "query_sequence": self.query_sequence,
                "combat_simulation_inputs": deepcopy(self.base),
            },
        })

    def close(self) -> None:
        pass


def _snapshot_for(base: dict[str, object], scene: str, hello: dict[str, object]) -> dict[str, object]:
    armies = base["armies"]
    scope_rows = {
        army["army_id"]: {"army_id": army["army_id"],
                          "controllable": army["scope_role"] == "player",
                          "current_province_id": army["current_province_id"]}
        for army in armies
    }
    war_ids = list(dict.fromkeys(war_id for army in armies for war_id in army["war_ids"]))
    wars = [{
        "war_id": war_id,
        "allied_armies": [scope_rows[army["army_id"]] for army in armies
                          if war_id in army["war_ids"] and army["scope_role"] != "active_war_enemy"],
        "enemy_armies": [scope_rows[army["army_id"]] for army in armies
                         if war_id in army["war_ids"] and army["scope_role"] == "active_war_enemy"],
    } for war_id in war_ids]
    return {
        "snapshot_id": f"synthetic-calendar-{scene}", "revision": _PUBLIC_REVISION,
        "native_revision": _NATIVE_REVISION, "date_raw": _DATE_RAW,
        "paused": True, "map_ready": True, "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [scope_rows[army["army_id"]] for army in armies
                          if army["scope_role"] == "player"],
        "active_wars": wars,
        "diagnostics": {"connection_generation": 1, "hello": hello},
    }


class PhaseEventCalendarRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_whole_calendar_native_fixture_registered_service(self) -> None:
        if not _CONFIG:
            raise RuntimeError("use --source-root, --wire and --output-dir")
        from xar_autoplayer.bridge.combat_contract import (
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            combat_simulation_encounter_scope,
            normalize_combat_simulation_inputs,
            query_combat_simulation_inputs_step,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.phase_event_calendar_contract import (
            normalize_phase_event_calendar_observation_v1,
        )
        from xar_autoplayer.bridge.version_identity import CK3_12004

        output = _CONFIG["output_dir"]
        output.mkdir(parents=True, exist_ok=True)
        report_path = output / "phase-event-calendar-registered-service-12004.json"
        report = {"result": "RUNNING", "wire": str(_CONFIG["wire"]),
                  "source_qualified_synthetic_fixture": True, "live_queries": 0,
                  "old_green_checks_rerun": 0, "samples": []}

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
            for query_sequence, scene in enumerate(_SCENES, 1):
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
                    "backend_id": "native-headless", "snapshot": True,
                    "action_steps": [step],
                    "bridge_capabilities": ["game.state.snapshot", QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
                    "diagnostics": deepcopy(snapshot["diagnostics"]),
                }
                endpoint = _WholeCalendarEndpoint(base, step, query_sequence)
                driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
                try:
                    with (
                        patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)),
                        patch.object(driver, "capabilities", return_value=deepcopy(capabilities)),
                    ):
                        result = await create_server(driver).call_tool("ck3_query_combat_simulation_inputs", arguments)
                    self.assertIs(result.is_error, False)
                    structured = result.structured_content
                    self.assertIsInstance(structured, dict)
                    self.assertEqual(len(endpoint.requests), 1)
                    normalized = structured["combat_simulation_inputs"]
                    self.assertEqual(normalized[_LEAF], raw_leaf)
                    self.assertEqual(normalized["completeness"], base["completeness"])
                    self.assertEqual(structured["missing_required_domains"],
                                     base["completeness"]["missing_required_domains"])
                    self.assertIn("phase_event_rng_and_effects", structured["missing_required_domains"])
                    expected_occurrences = sum(
                        int(army["commander"]["status"] == "available")
                        + len(army["knights"].get("members") or [])
                        for army in base["armies"]
                    )
                    self.assertEqual(len(raw_leaf["occurrences"]), expected_occurrences)
                    first_army = normalized["armies"][0]
                    commander_id = first_army["commander"]["character_id"]
                    first_knights = first_army["knights"]["members"][:3]
                    self.assertEqual([knight["character_id"] for knight in first_knights],
                                     [commander_id, 0, 0x05007485])
                    first_roles = raw_leaf["occurrences"][:4]
                    self.assertEqual([role["phase_role"] for role in first_roles],
                                     ["commander", "knight", "knight", "knight"])
                    self.assertEqual([role["character_id"] for role in first_roles],
                                     [commander_id, commander_id, 0, 0x05007485])
                    self.assertEqual([role["source_public_cunit_id"] for role in first_roles],
                                     [first_army["army_id"]] * 4)
                    self.assertEqual([role["source_native_carmy_id"] for role in first_roles],
                                     [first_army["native_carmy_id"]] * 4)
                    self.assertEqual([role["source_regiment_id"] for role in first_roles],
                                     [None, *(knight["source_regiment_id"] for knight in first_knights)])
                    self.assertIs(structured["input_observation_ready"], True)
                    self.assertIs(structured["monte_carlo_ready"], False)
                    self.assertEqual(structured["source"]["date_raw"], _DATE_RAW)
                    self.assertEqual(structured["queried_revision"], _PUBLIC_REVISION)
                    self.assertEqual(structured["queried_native_revision"], _NATIVE_REVISION)
                    self.assertIs(raw_leaf["complete_phase_effects_ready"], False)
                    if scene == "available":
                        self.assertEqual(raw_leaf["status"], "available")
                        self.assertEqual(raw_leaf["loaded_interval_days_raw"], 7)
                        self.assertEqual((raw_leaf["date_low32"], raw_leaf["next_date_low32"]),
                                         (_DATE_RAW, _DATE_RAW + 24))
                        self.assertEqual((raw_leaf["day_index"], raw_leaf["next_day_index"]),
                                         (395353, 395354))
                        for role in first_roles[2:4]:
                            self.assertEqual((role["current_remainder_raw"], role["next_remainder_raw"]),
                                             (0, 1))
                            self.assertIs(role["current_calendar_predicate"], True)
                            self.assertIs(role["next_day_calendar_predicate"], False)
                    else:
                        self.assertEqual(raw_leaf["loaded_interval_days_raw"], 0 if scene == "zero_interval" else None)
                        if scene == "zero_interval":
                            self.assertEqual(raw_leaf["status"], "partial")
                        for occurrence in raw_leaf["occurrences"]:
                            for field in ("current_calendar_predicate", "next_day_calendar_predicate",
                                          "current_remainder_raw", "next_remainder_raw"):
                                self.assertIsNone(occurrence[field])
                    self.assertEqual(endpoint.base, base)
                    self.assertEqual(driver._combat_simulation_inputs_query["combat_simulation_inputs"][_LEAF], raw_leaf)
                    roundtrip = json.loads(result.model_dump_json(by_alias=True))
                    self.assertEqual(roundtrip["structuredContent"]["combat_simulation_inputs"][_LEAF], raw_leaf)
                    report["samples"].append({"scene": scene, "transport_requests": 1,
                                              "leaf_status": raw_leaf["status"],
                                              "occurrences": len(raw_leaf["occurrences"]),
                                              "base_input_observation_ready": True,
                                              "base_monte_carlo_ready": False})
                    if scene == "available":
                        # Exercise only this new optional failure and legacy absence.
                        options = {
                            "expected_target_province_id": arguments["target_province_id"],
                            "expected_attacker_entry_province_id": arguments["attacker_entry_province_id"],
                            "expected_encounter_scope": combat_simulation_encounter_scope(
                                snapshot, arguments["attacker_army_ids"], arguments["defender_army_ids"]),
                        }
                        malformed = deepcopy(base)
                        malformed[_LEAF]["complete_phase_effects_ready"] = True
                        isolated = normalize_combat_simulation_inputs(malformed, **options)
                        self.assertEqual(isolated[_LEAF]["status"], "unavailable")
                        self.assertEqual(isolated["completeness"], normalized["completeness"])
                        legacy = deepcopy(base)
                        del legacy[_LEAF]
                        self.assertIsNone(normalize_combat_simulation_inputs(legacy, **options).get(_LEAF))
                        self.assertIsNone(normalize_phase_event_calendar_observation_v1(None, armies=normalized["armies"]))
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
    _CONFIG.update({"source_root": arguments.source_root.resolve(),
                    "wire": arguments.wire.resolve(), "output_dir": arguments.output_dir.resolve()})
    sys.path.insert(0, str(_CONFIG["source_root"]))
    suite = unittest.TestLoader().loadTestsFromTestCase(PhaseEventCalendarRegisteredService12004Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"result": "GREEN" if result.wasSuccessful() else "RED",
                      "tests_run": result.testsRun,
                      "report": str(_CONFIG["output_dir"] / "phase-event-calendar-registered-service-12004.json")}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
