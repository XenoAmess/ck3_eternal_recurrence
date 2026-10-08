"""FIRST registered normal-plan consumption of qualified Runtime32 whole wires.

Authored SOURCE_NOTRUN. Root supplies the six unchanged compiled packets;
this script never invokes their native producer or the earlier normalization
compound. Only the outer request nonce is correlated. Public catalogue and
active claim-war state are explicit synthetic fixtures. The sole substituted
production behavior is choose_one_life_turn's fixed synthetic action baseline;
the registered MCP tool, Service.plan_turn, its new observation hook, Service
query, driver method, transport, protocol state and strict reader stay real.
This qualifies their integration, not the ordinary strategy or a live war.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


TOOL = "ck3_plan_turn"
STEP = "query-player-ordinary-holy-war-declaration-context-v1"
CONTEXT_KEY = "player_ordinary_holy_war_declaration_context"
CHILD_KEY = "player_holy_war_defender_join_inputs"
ANNOTATION_KEY = "ordinary_holy_war_candidate_observation"
PERMISSION = "allow_private_player_ordinary_holy_war_declaration_context_query"
FILES = (
    "ordered_npc_rows_positive_values.json",
    "legal_zero_and_same_faith.json",
    "empty_native_joiner_set.json",
    "defender_faith_branch_disabled.json",
    "row_fervor_failure_retains_native_set.json",
    "native_role_fallback_independent_of_old_status.json",
)
EXPECTED_STATUSES = (
    "extra_native_defenders_observed",
    "extra_native_defenders_observed",
    "no_extra_native_defenders_observed",
    "no_extra_native_defenders_observed",
    "extra_native_defenders_observed",
    "native_defender_set_unavailable",
)
WAR_ID = 100663329
PLAYED_ID = 50331649
NPC_IDS = [134217734, 100663300]
NPC_RITES = [855638020, 872415237]
DEFENDER_FAITH_ID = 570425347
ENDPOINT_FAILURE = "synthetic endpoint unavailable before native response"
BASELINE_PLAN = {
    "policy": "synthetic-active-claim-war-action-fixture-v1",
    "phase": "native_war_pursuit",
    "selected_step": "life-advance",
    "reason": "synthetic fixture retains its current claim-war continuation",
    "decision": {
        "war_id": WAR_ID,
        "casus_belli_key": "claim_cb",
        "decision": "continue_current_war",
    },
    "current_war_proposal": {
        "war_id": WAR_ID,
        "casus_belli_key": "claim_cb",
        "claimant_character_id": PLAYED_ID,
        "primary_attacker_character_id": PLAYED_ID,
        "primary_defender_character_id": 31050,
        "selected_step": "life-advance",
    },
}


class OrdinaryHolyWarDefenderObservationRegisteredCompound(unittest.IsolatedAsyncioTestCase):
    """One registered compound; all assertions concern the normal-plan hook."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_registered_normal_plan_consumes_compiled_defender_inputs_preserving_war_action(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Run standalone with Root's qualified Runtime32 compiled packets")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge import (
            player_ordinary_holy_war_declaration_context_private_transport as context_transport,
            service as service_module,
        )
        from xar_autoplayer.bridge.player_holy_war_defender_join_inputs import (
            SCHEMA12004, normalize_holy_war_defender_join_inputs,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.ordinary_holy_war_defender_observation_v1 import (
            plan_ordinary_holy_war_defender_observation_v1,
            project_ordinary_holy_war_defender_observation_v1,
        )

        original_service_query = (
            GameplayBridgeService.query_player_ordinary_holy_war_declaration_context_private_v1
        )
        self.evidence["production_source_files"] = {
            "registered_mcp": inspect.getsourcefile(create_server),
            "actual_service_plan_turn": inspect.getsourcefile(GameplayBridgeService.plan_turn),
            "actual_plan_observation_hook": inspect.getsourcefile(plan_ordinary_holy_war_defender_observation_v1),
            "actual_projection": inspect.getsourcefile(project_ordinary_holy_war_defender_observation_v1),
            "actual_service_query": inspect.getsourcefile(original_service_query),
            "native_driver_method": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1,
            ),
            "existing_transport": inspect.getsourcefile(
                context_transport.query_player_ordinary_holy_war_declaration_context_private_v1,
            ),
            "strict_child_normalizer": inspect.getsourcefile(normalize_holy_war_defender_join_inputs),
            "native_protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        self.evidence["dispatch_path"] = (
            "registered ck3_plan_turn -> actual GameplayBridgeService.plan_turn -> "
            "actual ordinary-holy-war observation hook -> actual Service query -> "
            "NativeHeadlessGameplayDriver query -> existing transport -> "
            "NativeProtocolState.ingest/wait -> production strict child reader -> "
            "pure projection attached to the existing plan"
        )
        self.evidence["strategy_baseline"] = deepcopy(BASELINE_PLAN)
        self.evidence["strategy_baseline_provenance"] = (
            "Only choose_one_life_turn is substituted with the disclosed synthetic "
            "active-claim-war plan; neither Robert's live plan nor native AI is qualified"
        )
        service_calls: list[dict[str, object]] = []
        normalizer_calls: list[dict[str, object]] = []
        choose_calls: list[dict[str, object]] = []
        test = self

        class CompiledWireDriver:
            command_timeout_seconds = 1.0
            query_player_ordinary_holy_war_declaration_context_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1
            )

            def __init__(self, packet: dict[str, object], *, no_candidate: bool = False,
                         fail_endpoint: bool = False) -> None:
                self.packet = packet
                self.fail_endpoint = fail_endpoint
                setattr(self, PERMISSION, True)
                result = packet["result"]
                context = result[CONTEXT_KEY]
                selected = {
                    **deepcopy(context["selected_declaration"]),
                    "declaration_id": context["declaration_id"],
                }
                # Catalogue rows are synthetic public state. The first holy
                # row exactly matches the unchanged compiled selection; a
                # claim row before it and a later holy row prove first-match
                # ordering without editing or inventing a native result.
                claim = deepcopy(selected)
                claim["casus_belli_index"] += 100
                claim["casus_belli_key"] = "claim_cb"
                claim["declaration_id"] = (
                    f"{claim['target_character_id']}-{claim['casus_belli_index']}-"
                    f"{claim['configuration_index']}"
                )
                later = deepcopy(selected)
                later["casus_belli_index"] += 101
                later["casus_belli_key"] = "major_religious_war"
                later["declaration_id"] = (
                    f"{later['target_character_id']}-{later['casus_belli_index']}-"
                    f"{later['configuration_index']}"
                )
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": context["public_revision"],
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {"character_id": context["played_character_id"], "alive": True},
                    "declarable_wars": [claim] if no_candidate else [claim, selected, later],
                    "active_wars": [{
                        "war_id": WAR_ID, "casus_belli_key": "claim_cb",
                        "claimant_character_id": PLAYED_ID,
                        "primary_attacker_character_id": PLAYED_ID,
                        "primary_defender_character_id": 31050,
                    }],
                    "player_armies": [], "history": [],
                    "paused": True, "map_ready": True,
                    "active_event": None, "pending_character_interaction": None,
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.correlated_packets: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:ordinary-holy-war-normal-plan")

            def capabilities(self) -> dict[str, object]:
                return {"format_version": 1, "backend_id": "explicit-synthetic-driver",
                        "snapshot": True, "action_steps": ["life-advance"],
                        "bridge_capabilities": []}

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                self.sent.append(deepcopy(request))
                if self.fail_endpoint:
                    # Exercise the real Service/driver/transport failure;
                    # there is no fabricated command_result or native body.
                    raise BridgeUnavailableError(ENDPOINT_FAILURE)
                correlated = deepcopy(self.packet)
                correlated["request_id"] = request["request_id"]
                test.assertEqual(correlated["result"], self.packet["result"])
                test.assertEqual(
                    {key: item for key, item in correlated.items() if key != "request_id"},
                    {key: item for key, item in self.packet.items() if key != "request_id"},
                )
                self.correlated_packets.append(deepcopy(correlated))
                self.ingested_types.append(self.state.ingest(correlated))

        def synthetic_choose(commands: list[dict[str, object]], **kwargs: object) -> dict[str, object]:
            choose_calls.append({"commands": deepcopy(commands), "inputs": deepcopy(kwargs)})
            return deepcopy(BASELINE_PLAN)

        def record_real_service_query(service: GameplayBridgeService, **kwargs: object) -> dict[str, object]:
            service_calls.append(deepcopy(kwargs))
            return original_service_query(service, **kwargs)

        def record_real_normalizer(value: object, **kwargs: object) -> dict[str, object]:
            normalized = normalize_holy_war_defender_join_inputs(value, **kwargs)
            normalizer_calls.append({"native_value": deepcopy(value),
                                     "current_context": deepcopy(kwargs["current_context"]),
                                     "normalized_value": deepcopy(normalized)})
            return normalized

        async def registered_pair(driver: CompiledWireDriver, record: dict[str, object],
                                  *, expected_queries: int) -> dict[str, object]:
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            self.assertIn(TOOL, tools)
            previous_service_count = len(service_calls)
            previous_normalizer_count = len(normalizer_calls)
            initial_snapshot = deepcopy(driver.snapshot)
            record["synthetic_public_fixture_snapshot"] = deepcopy(initial_snapshot)
            with patch.object(service_module, "choose_one_life_turn", synthetic_choose), patch.object(
                GameplayBridgeService,
                "query_player_ordinary_holy_war_declaration_context_private_v1",
                record_real_service_query,
            ), patch.object(context_transport, "normalize_holy_war_defender_join_inputs", record_real_normalizer):
                setattr(driver, PERMISSION, False)
                off_response = await server.call_tool(TOOL, {})
                self.assertFalse(off_response.is_error, off_response)
                off = off_response.structured_content
                self.assertIsInstance(off, dict)
                record["registered_mcp_flag_off"] = deepcopy(off)
                self.assertEqual(len(service_calls), previous_service_count)
                self.assertEqual(driver.sent, [])
                self.assertNotIn(ANNOTATION_KEY, off["plan"])
                self.assertEqual(off["plan"], BASELINE_PLAN)
                setattr(driver, PERMISSION, True)
                on_response = await server.call_tool(TOOL, {})
                self.assertFalse(on_response.is_error, on_response)
                on = on_response.structured_content
                self.assertIsInstance(on, dict)
                record["registered_mcp_flag_on"] = deepcopy(on)
            record["sent_requests"] = deepcopy(driver.sent)
            record["protocol_ingested_packets"] = deepcopy(driver.correlated_packets)
            record["ingested_types"] = list(driver.ingested_types)
            record["actual_service_calls"] = deepcopy(service_calls[previous_service_count:])
            record["strict_reader_calls"] = deepcopy(normalizer_calls[previous_normalizer_count:])
            self.assertEqual(len(service_calls), previous_service_count + expected_queries)
            self.assertEqual(len(driver.sent), expected_queries)
            self.assertEqual({key: item for key, item in on.items() if key != "plan"},
                             {key: item for key, item in off.items() if key != "plan"})
            self.assertEqual({key: item for key, item in on["plan"].items() if key != ANNOTATION_KEY}, off["plan"])
            for key in ("selected_step", "phase", "decision", "current_war_proposal"):
                self.assertEqual(on["plan"][key], off["plan"][key])
            annotation = on["plan"][ANNOTATION_KEY]
            self.assertIs(annotation["read_only"], True)
            self.assertEqual(annotation["decision"], "continue_current_war")
            self.assertIs(annotation["automatic_declaration_enabled"], False)
            self.assertEqual(annotation["source_frame"], {
                "snapshot_id": initial_snapshot["snapshot_id"], "revision": initial_snapshot["revision"],
                "native_revision": initial_snapshot["native_revision"], "date_raw": initial_snapshot["date_raw"],
                "played_character_id": PLAYED_ID,
            })
            self.assertEqual(driver.snapshot, initial_snapshot)
            self.assertEqual(driver.snapshot["active_wars"][0]["casus_belli_key"], "claim_cb")
            self.assertEqual(driver.snapshot["active_wars"][0]["claimant_character_id"], PLAYED_ID)
            self.assertNotEqual(PLAYED_ID, 29829)
            self.assertTrue(all(request["step"] == STEP for request in driver.sent))
            self.assertFalse(any(request["step"].startswith("declare-war-") for request in driver.sent))
            record["original_action_preserved"] = True
            return annotation

        packets: dict[str, dict[str, object]] = {}
        outputs: dict[str, dict[str, object]] = {}
        for filename, status in zip(FILES, EXPECTED_STATUSES, strict=True):
            with self.subTest(file=filename):
                native_text = (self.args.native_fixtures_dir / filename).read_text(encoding="utf-8")
                packet = json.loads(native_text)
                original_packet = deepcopy(packet)
                packets[filename] = packet
                record: dict[str, object] = {"case": filename, "compiled_native_wire_text": native_text,
                                             "compiled_native_packet": deepcopy(packet)}
                self.observations.append(record)
                result = packet["result"]
                context, child = result[CONTEXT_KEY], result[CHILD_KEY]
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(result["game_version"], CK3_12004.game_version)
                self.assertEqual(result["executable_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(child["schema"], SCHEMA12004)
                self.assertEqual(context["played_character_id"], PLAYED_ID)
                driver = CompiledWireDriver(packet)
                annotation = await registered_pair(driver, record, expected_queries=1)
                outputs[filename] = annotation
                self.assertEqual(annotation["status"], status)
                self.assertEqual(annotation["source_ordinal"], 1)
                self.assertEqual(annotation["declaration_id"], context["declaration_id"])
                self.assertEqual(annotation["selected_declaration"], context["selected_declaration"])
                self.assertEqual(record["actual_service_calls"], [{
                    "expected_revision": context["public_revision"], "declaration_id": context["declaration_id"],
                }])
                self.assertEqual(annotation[CHILD_KEY], child)
                self.assertEqual(annotation["joiners"], child["joiners"])
                self.assertEqual(annotation["joiner_count"], child["joiner_count"])
                self.assertIs(annotation["native_joiner_set_observed"], child["native_joiner_set_observed"])
                self.assertEqual(annotation["cb_cost"], context["cb_cost"])
                self.assertIs(annotation["cb_cost_available"], True)
                self.assertIs(annotation["final_can_send"], False)
                self.assertIs(annotation["total_cost_ready"], False)
                self.assertIsNone(annotation["generic_interaction_cost_raw"])
                self.assertIsNone(annotation["total_declaration_cost_raw"])
                self.assertIs(annotation["is_final_join_score"], False)
                self.assertEqual(annotation["native_roles"], {
                    key: context[key] for key in (
                        "context_actor_character_id", "context_recipient_character_id",
                        "context_additional_role_character_id", "context_claimant_character_id",
                        "recipient_uses_native_fallback", "additional_role_uses_native_fallback",
                        "claimant_uses_native_fallback",
                    )
                })
                self.assertEqual(len(record["strict_reader_calls"]), 1)
                strict_read = record["strict_reader_calls"][0]
                self.assertEqual(strict_read["native_value"], child)
                self.assertEqual(strict_read["current_context"], context)
                self.assertEqual(strict_read["normalized_value"], child)
                self.assertEqual(driver.ingested_types, ["command_result"])
                sent = driver.sent[0]
                self.assertEqual(sent["declaration_id"], context["declaration_id"])
                self.assertEqual(sent["expected_public_revision"], context["public_revision"])
                self.assertEqual(sent["expected_revision"], context["native_revision"])
                self.assertEqual(sent["expected_snapshot_revision"], context["native_revision"])
                for key, item in context["selected_declaration"].items():
                    self.assertEqual(sent[key], item)
                self.assertIsNone(driver.state.wait_for_command_result(sent["request_id"], 0))
                self.assertEqual(packet, original_packet)
                record["compiled_native_result_preserved"] = True

        self.assertEqual(len(outputs), len(FILES))
        for filename in (FILES[0], FILES[1], FILES[4]):
            annotation = outputs[filename]
            self.assertEqual([row["character_id"] for row in annotation["joiners"]], NPC_IDS)
            self.assertEqual([row["rite_id"] for row in annotation["joiners"]], NPC_RITES)
            self.assertEqual([row["faith_id"] for row in annotation["joiners"]], [DEFENDER_FAITH_ID] * 2)
            self.assertEqual(annotation["primary_defender_faith_id"], DEFENDER_FAITH_ID)
            self.assertIs(annotation["defender_faith_can_join"], True)
            self.assertEqual(annotation["raw_scale"], 100000)
            self.assertEqual(annotation["unit"], "fervor_points")
        self.assertEqual([row["faith_fervor_raw"] for row in outputs[FILES[0]]["joiners"]], [7500000, 7500000])
        zero = outputs[FILES[1]]
        self.assertEqual([row["faith_fervor_raw"] for row in zero["joiners"]], [0, 0])
        self.assertTrue(all(row["row_fervor_available"] for row in zero["joiners"]))
        for filename, can_join in ((FILES[2], True), (FILES[3], False)):
            self.assertIs(outputs[filename]["defender_faith_can_join"], can_join)
            self.assertEqual(outputs[filename]["joiners"], [])
            self.assertEqual(outputs[filename]["joiner_count"], 0)
        failed = outputs[FILES[4]]
        self.assertEqual([row["faith_fervor_raw"] for row in failed["joiners"]], [7500000, None])
        self.assertIs(failed["joiners"][1]["row_faith_available"], True)
        self.assertIs(failed["joiners"][1]["row_fervor_available"], False)
        self.assertEqual(failed["joiners"][1]["unavailable_reason"], "fervor_unavailable")
        fallback = outputs[FILES[5]]
        self.assertIs(fallback["declaration_context_available"], True)
        self.assertIs(fallback["defender_inputs_available"], False)
        self.assertEqual(fallback["defender_inputs_unavailable_reason"], "native_role_fallback")
        self.assertEqual(fallback["primary_attacker_character_id"], 4294967295)
        self.assertEqual(fallback["joiners"], [])

        with self.subTest(case="no_current_ordinary_holy_war_candidate"):
            record = {"case": "no_current_ordinary_holy_war_candidate",
                      "source_packet_file": FILES[0], "native_body_not_ingested": True}
            self.observations.append(record)
            driver = CompiledWireDriver(packets[FILES[0]], no_candidate=True)
            annotation = await registered_pair(driver, record, expected_queries=0)
            self.assertEqual(annotation["status"], "no_current_ordinary_holy_war_candidate")
            self.assertNotIn("declaration_id", annotation)
            self.assertEqual(record["strict_reader_calls"], [])
            self.assertEqual(driver.ingested_types, [])

        with self.subTest(case="current_query_endpoint_failure"):
            record = {"case": "current_query_endpoint_failure", "source_packet_file": FILES[0],
                      "native_body_not_ingested": True, "synthetic_endpoint_failure": ENDPOINT_FAILURE}
            self.observations.append(record)
            driver = CompiledWireDriver(packets[FILES[0]], fail_endpoint=True)
            annotation = await registered_pair(driver, record, expected_queries=1)
            context = packets[FILES[0]]["result"][CONTEXT_KEY]
            self.assertEqual(annotation["status"], "query_failed")
            self.assertEqual(annotation["reason"], ENDPOINT_FAILURE)
            self.assertEqual(annotation["declaration_id"], context["declaration_id"])
            self.assertEqual(annotation["selected_declaration"], context["selected_declaration"])
            self.assertEqual(annotation["source_ordinal"], 1)
            self.assertEqual(record["strict_reader_calls"], [])
            self.assertEqual(driver.ingested_types, [])
            self.assertEqual(driver.correlated_packets, [])

        self.assertEqual(len(self.observations), 8)
        self.assertEqual(len(choose_calls), 16)
        self.assertEqual(len(service_calls), 7)
        self.assertEqual(len(normalizer_calls), 6)
        self.evidence["registered_plan_turn_calls"] = len(choose_calls)
        self.evidence["actual_service_query_calls"] = service_calls
        self.evidence["actual_strict_child_calls"] = len(normalizer_calls)
        self.evidence["completed_packet_statuses"] = {name: row["status"] for name, row in outputs.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixtures-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = OrdinaryHolyWarDefenderObservationRegisteredCompound(
        "test_registered_normal_plan_consumes_compiled_defender_inputs_preserving_war_action",
    )
    test.args, test.observations, test.evidence = args, observations, evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.ordinary-holy-war-defender-normal-plan-registered-compound/v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "registered_tool": TOOL, "compiled_native_files": list(FILES),
        "source_root": str(args.source_root), "native_fixtures_dir": str(args.native_fixtures_dir),
        "source_identity_owner": "Root qualification receipt", "source_hashes": None,
        "input_provenance": "Root-supplied qualified Runtime32 compiled synthetic whole packets",
        "native_producer_invocations": 0, "previous_normalization_compound_invocations": 0,
        "native_result_bodies_constructed": False, "native_result_bodies_repaired": False,
        "outer_envelope_request_id_correlation_only": True,
        "public_snapshot_provenance": "Explicit synthetic catalogue/frame and active claim War100663329",
        "substituted_strategy_function": "bridge.service.choose_one_life_turn",
        "service_plan_turn_substituted": False, "observation_hook_substituted": False,
        "query_and_strict_instrumentation": "Call-original wrappers only; never replace their output",
        "normal_strategy_qualified": False, "live_capability_qualified": False,
        "registered_cases_attempted": len(observations),
        "completed_flag_on_outputs": sum("registered_mcp_flag_on" in row for row in observations),
        "official_sdk_client_sessions": 0, "pipe_operations": 0,
        "game_operations": 0, "game_actions": 0, "new_exe_bytes": 0,
        "readiness_scope": "Registered normal-Service observation integration over compiled synthetic packets",
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors], **evidence,
    }
    for filename, payload in (("OBSERVED.json", observations), ("RESULT.json", report)):
        with (args.output_dir / filename).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
