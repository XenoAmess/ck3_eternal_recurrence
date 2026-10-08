"""Sole FIRST registered MCP consumption of six compiled native join-input wires.

Authored NOTRUN. Root supplies genuine compiled whole packets. This fixture
uses the existing Service route and never creates or repairs native result
bodies. Only the outer request nonce is correlated for protocol ingestion.
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


TOOL = "ck3_query_player_ordinary_holy_war_declaration_context_v1"
STEP = "query-player-ordinary-holy-war-declaration-context-v1"
CONTEXT_KEY = "player_ordinary_holy_war_declaration_context"
CHILD_KEY = "player_holy_war_defender_join_inputs"
FILES = (
    "ordered_npc_rows_positive_values.json",
    "legal_zero_and_same_faith.json",
    "empty_native_joiner_set.json",
    "defender_faith_branch_disabled.json",
    "row_fervor_failure_retains_native_set.json",
    "native_role_fallback_independent_of_old_status.json",
)
NPC_IDS = [134217734, 100663300]
NPC_RITES = [855638020, 872415237]
DEFENDER_FAITH_ID = 570425347


class HolyWarDefenderJoinRegisteredMcpCompound(unittest.IsolatedAsyncioTestCase):
    """One compound through the real registered Service, driver and transport."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_six_actual4_compiled_native_sets_registered_mcp(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Run standalone with Root's fresh compiled native fixtures")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import (
            NativeHeadlessGameplayDriver, NativeProtocolState,
        )
        from xar_autoplayer.bridge import (
            player_ordinary_holy_war_declaration_context_private_transport as context_transport,
        )
        from xar_autoplayer.bridge.player_holy_war_defender_join_inputs import (
            SCHEMA12004 as SCHEMA, normalize_holy_war_defender_join_inputs,
        )
        from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_observation import (
            RESOURCE_KEYS,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        original_service_query = (
            GameplayBridgeService.query_player_ordinary_holy_war_declaration_context_private_v1
        )
        self.evidence["production_source_files"] = {
            "registered_mcp": inspect.getsourcefile(create_server),
            "actual_service_method": inspect.getsourcefile(original_service_query),
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
            "registered create_server tool -> actual GameplayBridgeService method -> "
            "NativeHeadlessGameplayDriver method -> existing selected-declaration transport -> "
            "NativeProtocolState.ingest/wait -> production strict child normalizer"
        )
        exact = {
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
        }
        service_calls: list[dict[str, object]] = []
        normalizer_calls: list[dict[str, object]] = []
        test = self

        class CompiledWireDriver:
            allow_private_player_ordinary_holy_war_declaration_context_query = True
            command_timeout_seconds = 1.0
            query_player_ordinary_holy_war_declaration_context_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1
            )

            def __init__(self, packet: dict[str, object]) -> None:
                self.packet = packet
                result = packet["result"]
                context = result[CONTEXT_KEY]
                # Synthetic public fixture state uses the unchanged compiled
                # frame/selection; it is not a generated native result.
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": context["public_revision"],
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {
                        "character_id": context["played_character_id"], "alive": True,
                    },
                    "declarable_wars": [{
                        **deepcopy(context["selected_declaration"]),
                        "declaration_id": context["declaration_id"],
                    }],
                    "paused": True, "map_ready": True,
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.correlated_packets: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:holy-war-defender-join")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                self.sent.append(deepcopy(request))
                correlated = deepcopy(self.packet)
                correlated["request_id"] = request["request_id"]
                test.assertEqual(correlated["result"], self.packet["result"])
                test.assertEqual(
                    {key: item for key, item in correlated.items() if key != "request_id"},
                    {key: item for key, item in self.packet.items() if key != "request_id"},
                )
                self.correlated_packets.append(deepcopy(correlated))
                self.ingested_types.append(self.state.ingest(correlated))

        def record_real_service_query(service: GameplayBridgeService, **kwargs: object) -> dict[str, object]:
            service_calls.append(deepcopy(kwargs))
            return original_service_query(service, **kwargs)

        def record_real_normalizer(value: object, **kwargs: object) -> dict[str, object]:
            normalized = normalize_holy_war_defender_join_inputs(value, **kwargs)
            normalizer_calls.append({
                "native_value": deepcopy(value),
                "current_context": deepcopy(kwargs["current_context"]),
                "snapshot": deepcopy(kwargs["snapshot"]),
                "normalized_value": deepcopy(normalized),
            })
            return normalized

        outputs: dict[str, dict[str, object]] = {}
        for filename in FILES:
            with self.subTest(file=filename):
                native_text = (self.args.native_fixtures_dir / filename).read_text(encoding="utf-8")
                packet = json.loads(native_text)
                original_packet = deepcopy(packet)
                record: dict[str, object] = {
                    "file": filename, "compiled_native_wire_text": native_text,
                    "compiled_native_packet": deepcopy(packet),
                    "compiled_request_id": packet["request_id"],
                }
                self.observations.append(record)
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                result = packet["result"]
                context = result[CONTEXT_KEY]
                child = result[CHILD_KEY]
                self.assertEqual(result["step"], STEP)
                self.assertEqual(child["schema"], SCHEMA)
                self.assertEqual(context["game_version"], exact["game_version"])
                self.assertEqual(context["executable_sha256"], exact["executable_sha256"])
                self.assertEqual(result["game_version"], exact["game_version"])
                self.assertEqual(result["executable_sha256"], exact["executable_sha256"])
                self.assertIs(context["available"], True)
                self.assertEqual(result["status"], "observed")
                self.assertEqual(context["played_character_id"], 50331649)
                self.assertEqual(context["context_recipient_character_id"], 67108866)
                self.assertEqual(result["snapshot_revision"], context["native_revision"])
                self.assertEqual(result["public_revision"], context["public_revision"])
                self.assertEqual(result["date_raw"], context["date_raw"])
                for key in (
                    "capture_epoch", "native_revision", "public_revision", "date_raw",
                    "played_character_id", "declaration_id", "selected_declaration",
                ):
                    self.assertEqual(child[key], context[key])
                self.assertIs(context["final_can_send"], False)
                self.assertIs(context["cb_cost"]["available"], True)
                self.assertEqual(context["cb_cost"]["resource_keys"], list(RESOURCE_KEYS))
                self.assertTrue(any(item != 0 for item in context["cb_cost"]["resource_costs_raw"]))

                driver = CompiledWireDriver(packet)
                record["synthetic_public_fixture_snapshot"] = deepcopy(driver.snapshot)
                server = create_server(driver)
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertIn(TOOL, tools)
                self.assertIs(tools[TOOL].annotations.read_only_hint, True)
                previous_service_count = len(service_calls)
                previous_normalizer_count = len(normalizer_calls)
                # Both wrappers call the actual original production function.
                # No Service API or transport route is invented by this test.
                with patch.object(
                    GameplayBridgeService,
                    "query_player_ordinary_holy_war_declaration_context_private_v1",
                    record_real_service_query,
                ), patch.object(
                    context_transport, "normalize_holy_war_defender_join_inputs",
                    record_real_normalizer,
                ):
                    response = await server.call_tool(TOOL, {
                        "expected_revision": context["public_revision"],
                        "declaration_id": context["declaration_id"],
                    })
                self.assertFalse(response.is_error, response)
                actual = response.structured_content
                self.assertIsInstance(actual, dict)
                record["registered_mcp_output"] = deepcopy(actual)
                record["sent_requests"] = deepcopy(driver.sent)
                record["protocol_ingested_packets"] = deepcopy(driver.correlated_packets)
                record["ingested_types"] = list(driver.ingested_types)
                record["outer_envelope_nonce_correlation_only"] = True
                self.assertEqual(packet, original_packet)
                self.assertEqual({key: actual[key] for key in context}, context)
                self.assertEqual(actual[CHILD_KEY], child)
                self.assertIs(actual["available"], True)
                self.assertEqual(actual["query_status"], result["status"])
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(actual["snapshot_revision"], context["native_revision"])
                self.assertEqual(actual["queried_revision"], context["public_revision"])
                self.assertEqual(actual["queried_native_revision"], context["native_revision"])
                self.assertEqual(actual["exact_ck3_build"], exact["game_version"])
                self.assertEqual(actual["exe_sha256"], exact["executable_sha256"])
                self.assertEqual(actual["cb_cost"], context["cb_cost"])
                self.assertIs(actual["final_can_send"], False)
                self.assertIsNone(actual["generic_interaction_cost_raw"])
                self.assertIsNone(actual["total_declaration_cost_raw"])
                self.assertIs(actual["total_cost_ready"], False)
                self.assertEqual(len(service_calls), previous_service_count + 1)
                self.assertEqual(service_calls[-1], {
                    "expected_revision": context["public_revision"],
                    "declaration_id": context["declaration_id"],
                })
                self.assertEqual(len(normalizer_calls), previous_normalizer_count + 1)
                normalizer_record = normalizer_calls[-1]
                self.assertEqual(normalizer_record["native_value"], child)
                self.assertEqual(normalizer_record["current_context"], context)
                self.assertEqual(normalizer_record["normalized_value"], child)
                self.assertEqual(normalizer_record["snapshot"]["revision"], context["public_revision"])
                record["production_normalizer_call"] = deepcopy(normalizer_record)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                sent = driver.sent[0]
                self.assertEqual(sent["step"], STEP)
                self.assertEqual(sent["expected_public_revision"], context["public_revision"])
                self.assertEqual(sent["expected_revision"], context["native_revision"])
                self.assertEqual(sent["expected_snapshot_revision"], context["native_revision"])
                self.assertEqual(sent["declaration_id"], context["declaration_id"])
                for key, item in context["selected_declaration"].items():
                    self.assertEqual(sent[key], item)
                self.assertNotIn("played_character_id", sent)
                self.assertIsNone(driver.state.wait_for_command_result(sent["request_id"], 0))
                record["compiled_native_result_preserved"] = True
                outputs[filename] = actual

        self.assertEqual(len(outputs), len(FILES))
        self.assertEqual(len(service_calls), len(FILES))
        self.assertEqual(len(normalizer_calls), len(FILES))
        self.evidence["actual_service_calls"] = service_calls
        self.evidence["actual_production_normalizer_calls"] = len(normalizer_calls)

        for filename in (FILES[0], FILES[1], FILES[4]):
            child = outputs[filename][CHILD_KEY]
            self.assertIs(child["available"], True)
            self.assertIs(child["native_joiner_set_observed"], True)
            self.assertIs(child["defender_faith_can_join"], True)
            self.assertEqual(child["joiner_count"], 2)
            self.assertEqual([row["character_id"] for row in child["joiners"]], NPC_IDS)
            self.assertEqual([row["rite_id"] for row in child["joiners"]], NPC_RITES)
            self.assertEqual([row["faith_id"] for row in child["joiners"]], [DEFENDER_FAITH_ID] * 2)
            self.assertEqual(child["primary_defender_faith_id"], DEFENDER_FAITH_ID)
            self.assertEqual(child["primary_attacker_character_id"], 83886083)
            self.assertNotEqual(child["primary_attacker_character_id"], child["played_character_id"])
            self.assertEqual(child["primary_defender_character_id"], 67108866)
            self.assertEqual([row["matches_primary_defender_faith"] for row in child["joiners"]], [True, True])
            self.assertIs(child["is_final_join_score"], False)
            self.assertEqual(child["raw_scale"], 100000)
            self.assertEqual(child["unit"], "fervor_points")
        positive = outputs[FILES[0]][CHILD_KEY]
        self.assertEqual([row["faith_fervor_raw"] for row in positive["joiners"]], [7500000, 7500000])
        self.assertTrue(all(row["row_fervor_available"] for row in positive["joiners"]))
        zero = outputs[FILES[1]][CHILD_KEY]
        self.assertEqual([row["faith_fervor_raw"] for row in zero["joiners"]], [0, 0])
        self.assertTrue(all(row["row_fervor_available"] for row in zero["joiners"]))
        # A zero observed input is not a calculated score and does not erase
        # accepted NPCs when identities resolve to the defender's same FaithID.
        self.assertIs(zero["is_final_join_score"], False)
        for filename, can_join in ((FILES[2], True), (FILES[3], False)):
            empty = outputs[filename][CHILD_KEY]
            self.assertIs(empty["available"], True)
            self.assertIs(empty["native_joiner_set_observed"], True)
            self.assertIs(empty["defender_faith_can_join"], can_join)
            self.assertEqual(empty["joiner_count"], 0)
            self.assertEqual(empty["joiners"], [])
        self.assertEqual(outputs[FILES[3]][CHILD_KEY]["cb_flags_raw"], 0)
        failed = outputs[FILES[4]][CHILD_KEY]
        self.assertEqual([row["faith_fervor_raw"] for row in failed["joiners"]], [7500000, None])
        self.assertIs(failed["joiners"][1]["row_faith_available"], True)
        self.assertIs(failed["joiners"][1]["row_fervor_available"], False)
        self.assertEqual(failed["joiners"][1]["unavailable_reason"], "fervor_unavailable")
        fallback = outputs[FILES[5]]
        self.assertEqual(fallback["context_additional_role_character_id"], -1)
        self.assertIs(fallback["additional_role_uses_native_fallback"], True)
        self.assertIs(fallback["available"], True)
        self.assertEqual(fallback["query_status"], "observed")
        child = fallback[CHILD_KEY]
        self.assertIs(child["available"], False)
        self.assertIs(child["native_joiner_set_observed"], False)
        self.assertEqual(child["unavailable_reason"], "native_role_fallback")
        self.assertEqual(child["primary_attacker_character_id"], 4294967295)
        self.assertEqual(child["joiner_count"], 0)
        self.assertEqual(child["joiners"], [])
        self.assertIs(fallback["cb_cost"]["available"], True)
        self.assertIs(fallback["final_can_send"], False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixtures-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = HolyWarDefenderJoinRegisteredMcpCompound(
        "test_six_actual4_compiled_native_sets_registered_mcp",
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.holy-war-defender-join-registered-mcp-first-consumption/v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "compiled_native_files": list(FILES),
        "native_fixtures_dir": str(args.native_fixtures_dir),
        "source_root": str(args.source_root),
        "source_identity_owner": "Root qualification receipt",
        "source_hashes": None,
        "input_provenance": "Root-supplied compiled whole wires; synthetic native callbacks/frame",
        "native_result_bodies_constructed": False,
        "native_result_bodies_repaired": False,
        "outer_envelope_request_id_correlation_only": True,
        "public_snapshot_provenance": "Explicit synthetic frame/selection from compiled native context",
        "registered_mcp_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "official_sdk_client_sessions": 0, "pipe_operations": 0,
        "game_operations": 0, "game_actions": 0, "new_exe_bytes": 0,
        "readiness_scope": "Compiled synthetic fixture consumption; no live capability credit",
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors],
        **evidence,
    }
    for filename, payload in (("OBSERVED.json", observations), ("RESULT.json", report)):
        with (args.output_dir / filename).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
