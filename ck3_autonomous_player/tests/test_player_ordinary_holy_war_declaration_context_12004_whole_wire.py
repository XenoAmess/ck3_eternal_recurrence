"""Sole actual-.4 FIRST registered Service/MCP whole native consumption.

Prepared NOTRUN. Root supplies the fresh compiled synthetic whole-native fixture.
Native packets remain unchanged; only the outgoing UUID joins its correlation ID.
No old FIRST, SDK, game, EXE read, source hash or packet repair runs here.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


TOOL = "ck3_query_player_ordinary_holy_war_declaration_context_v1"
STEP = "query-player-ordinary-holy-war-declaration-context-v1"
SCHEMA = "player_ordinary_holy_war_declaration_context_v1"
RECEIPT_FILE = "actual4-producer-receipt.json"
RECEIPT_SCHEMA = "xar.ck3.ordinary-holy-war-declaration-context-actual4-native-whole-fixture/v1"
WIRE_FILE = "native-wire-actual4-redirected-claimant-fallback.json"
REQUEST_ID = "g2-read-00000000000000000000000000004901"
ACTOR = 0x0B000001
TARGET = 0x0C000002
ADDITIONAL = 0x0D000003
TITLE_IDS = [0x0E000031, 0x0F000021]
FRAME = {
    "public_revision": 4, "native_revision": 17, "date_raw": 53222312,
    "played_character_id": ACTOR, "capture_epoch": 1007,
    "paused": True, "map_ready": True,
}
CB_COSTS_RAW = [-375001, 2234567, 25000001, 0, 103, 104, 105, 106, 107, 108]


class PlayerOrdinaryHolyWarDeclarationContext12004WholeWireTests(unittest.IsolatedAsyncioTestCase):
    """One compound reaches the actual registered tool and real service method."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_actual4_compiled_whole_native_context_registered_service_mcp(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Run standalone with the fresh compiled actual-.4 wire directory")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import (
            NativeHeadlessGameplayDriver, NativeProtocolState,
        )
        from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_transport import (
            query_player_ordinary_holy_war_declaration_context_private_v1,
        )
        from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_observation import (
            RESOURCE_KEYS, normalize_player_ordinary_holy_war_declaration_context_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        receipt = json.loads((self.args.native_wire_dir / RECEIPT_FILE).read_bytes())
        self.evidence["native_producer_receipt"] = deepcopy(receipt)
        self.evidence["production_source_files"] = {
            "mcp": inspect.getsourcefile(create_server),
            "service_method": inspect.getsourcefile(
                GameplayBridgeService.query_player_ordinary_holy_war_declaration_context_private_v1,
            ),
            "native_wrapper": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1,
            ),
            "query_transport": inspect.getsourcefile(
                query_player_ordinary_holy_war_declaration_context_private_v1,
            ),
            "strict_normalizer": inspect.getsourcefile(
                normalize_player_ordinary_holy_war_declaration_context_v1,
            ),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        self.evidence["dispatch_path"] = (
            "registered same MCP tool -> real GameplayBridgeService method -> "
            "NativeHeadlessGameplayDriver wrapper -> existing query transport -> "
            "NativeProtocolState.ingest/wait -> strict actual-.4 normalizer"
        )
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], 1)
        self.assertEqual(receipt["whole_wire_files"], [WIRE_FILE])
        self.assertEqual(receipt["frame"], FRAME)
        self.assertEqual(receipt["provenance"]["whole_wires"], "compiled-production-serializer")
        self.assertIs(receipt["provenance"]["whole_wire_rows_repaired"], False)
        for key in (
            "actual4_declaration_factory", "actual4_cb_cost_factory", "actual4_core_reader",
            "actual4_pump_profile", "actual_request_parser", "actual_named_mailbox",
            "actual_selected_context_reader", "actual_cb_cost_reader", "actual_full_serializer",
            "actual4_build_identity_renderer",
        ):
            self.assertIs(receipt["pipeline"][key], True)
        self.assertIs(receipt["pipeline"]["offline_native_image_handler_invoked"], False)
        self.assertIs(receipt["pipeline"]["live"], False)
        self.assertEqual(receipt["native_calls"], {
            "evaluate_cb": 1, "construct_context": 1, "refresh_context": 1,
            "finalize_context": 1, "validate_context": 1, "construct_scope": 1,
            "populate_scope": 1, "evaluate_cost": 1,
        })
        self.assertEqual(receipt["cleanup"], {
            "destroy_configuration": 1, "destroy_context": 1, "destroy_scope": 1,
            "scratch_count": 0, "mailbox_reclaimed": True,
        })
        self.assertEqual(receipt["gameplay_commands"], 0)
        exact = {
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
        }
        self.assertEqual(exact, {
            "game_version": "1.20.0.4",
            "executable_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
        })
        self.assertEqual(receipt["exact_build"], exact)

        whole_native_bytes = (self.args.native_wire_dir / WIRE_FILE).read_bytes()
        packet = json.loads(whole_native_bytes)
        original_packet = deepcopy(packet)
        record: dict[str, object] = {
            "file": WIRE_FILE, "whole_native_wire_utf8": whole_native_bytes.decode("utf-8"),
            "original_native_packet": original_packet,
        }
        self.observations.append(record)
        self.assertEqual(packet["type"], "command_result")
        self.assertEqual(packet["protocol_version"], 1)
        self.assertIs(packet["ok"], True)
        self.assertEqual(packet["request_id"], REQUEST_ID)
        result = packet["result"]
        context = result["player_ordinary_holy_war_declaration_context"]
        self.assertEqual(result["step"], STEP)
        self.assertEqual(result["domain_key"], SCHEMA)
        self.assertEqual(result["backend_id"], CK3_12004.backend_id("player-ordinary-holy-war-declaration-context-v1"))
        self.assertEqual(result["game_version"], exact["game_version"])
        self.assertEqual(result["executable_sha256"], exact["executable_sha256"])
        self.assertEqual(result["snapshot_revision"], FRAME["native_revision"])
        self.assertEqual(result["public_revision"], FRAME["public_revision"])
        self.assertEqual(result["date_raw"], FRAME["date_raw"])
        self.assertEqual(context["schema"], SCHEMA)
        for key in ("capture_epoch", "native_revision", "public_revision", "date_raw", "played_character_id"):
            self.assertEqual(context[key], FRAME[key])
        self.assertEqual(context["game_version"], exact["game_version"])
        self.assertEqual(context["executable_sha256"], exact["executable_sha256"])
        self.assertEqual(context["selected_declaration"]["target_character_id"], TARGET)
        self.assertEqual(context["selected_declaration"]["target_title_ids"], TITLE_IDS)
        self.assertEqual(context["selected_declaration"]["claimant_character_id"], -1)
        self.assertEqual(context["selected_declaration"]["casus_belli_index"], 0)
        self.assertEqual(context["selected_declaration"]["configuration_index"], 0)
        self.assertEqual(context["selected_declaration"]["casus_belli_key"], "religious_war")
        self.assertEqual(context["declaration_id"], "201326594-0-0")

        test = self

        class CompiledWholeActual4Driver:
            allow_private_player_ordinary_holy_war_declaration_context_query = True
            command_timeout_seconds = 1.0
            query_player_ordinary_holy_war_declaration_context_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1
            )

            def __init__(self) -> None:
                # The paused public fixture snapshot is explicitly synthetic.
                # Native identity and selection come from the intact packet.
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": FRAME["public_revision"],
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {
                        "character_id": context["played_character_id"], "alive": True,
                    },
                    "declarable_wars": [{
                        **context["selected_declaration"],
                        "declaration_id": context["declaration_id"],
                    }],
                    "paused": FRAME["paused"], "map_ready": FRAME["map_ready"],
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:actual4-holy-war-whole")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test.assertEqual(request["request_id"], packet["request_id"])
                self.sent.append(deepcopy(request))
                self.ingested_types.append(self.state.ingest(deepcopy(packet)))

        original_service_query = (
            GameplayBridgeService.query_player_ordinary_holy_war_declaration_context_private_v1
        )
        service_calls: list[dict[str, object]] = []

        def record_real_service_query(service: GameplayBridgeService, **kwargs: object) -> dict[str, object]:
            service_calls.append(deepcopy(kwargs))
            return original_service_query(service, **kwargs)

        driver = CompiledWholeActual4Driver()
        record["fixture_public_snapshot"] = deepcopy(driver.snapshot)
        server = create_server(driver)
        registered_tools = await server.list_tools()
        self.evidence["registered_tool_count"] = len(registered_tools)
        selected_tools = [tool for tool in registered_tools if tool.name == TOOL]
        self.evidence["registered_selected_tool_count"] = len(selected_tools)
        self.assertEqual(len(selected_tools), 1)
        self.assertIs(selected_tools[0].annotations.read_only_hint, True)
        # Only outgoing UUID generation is pinned. The complete native packet
        # is ingested unchanged; the service spy calls the real implementation.
        with patch(
            "xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
            return_value=SimpleNamespace(hex=REQUEST_ID[len("g2-read-"):]),
        ), patch.object(
            GameplayBridgeService,
            "query_player_ordinary_holy_war_declaration_context_private_v1",
            record_real_service_query,
        ):
            response = await server.call_tool(TOOL, {
                "expected_revision": FRAME["public_revision"],
                "declaration_id": context["declaration_id"],
            })
        self.assertFalse(response.is_error, response)
        actual = response.structured_content
        self.assertIsInstance(actual, dict)
        record["registered_mcp_output"] = deepcopy(actual)
        record["sent_requests"] = deepcopy(driver.sent)
        record["ingested_types"] = list(driver.ingested_types)
        self.evidence["actual_service_calls"] = service_calls
        self.assertEqual(len(service_calls), 1)
        for key, value in context.items():
            self.assertEqual(actual[key], value)
        self.assertEqual(packet, original_packet)
        self.assertIs(actual["read_only"], True)
        self.assertIs(actual["advertised"], False)
        self.assertIs(actual["available"], True)
        self.assertEqual(actual["query_status"], "observed")
        self.assertEqual(actual["snapshot_revision"], FRAME["native_revision"])
        self.assertEqual(actual["queried_revision"], FRAME["public_revision"])
        self.assertEqual(actual["queried_native_revision"], FRAME["native_revision"])
        self.assertEqual(actual["exact_ck3_build"], exact["game_version"])
        self.assertEqual(actual["exe_sha256"], exact["executable_sha256"])
        self.assertEqual(actual["context_actor_character_id"], ACTOR)
        self.assertEqual(actual["context_recipient_character_id"], TARGET)
        self.assertEqual(actual["context_additional_role_character_id"], ADDITIONAL)
        self.assertNotEqual(actual["context_additional_role_character_id"], actual["context_actor_character_id"])
        self.assertEqual(actual["context_claimant_character_id"], -1)
        self.assertIs(actual["recipient_uses_native_fallback"], False)
        self.assertIs(actual["additional_role_uses_native_fallback"], False)
        self.assertIs(actual["claimant_uses_native_fallback"], True)
        self.assertIs(actual["final_can_send"], False)
        cost = actual["cb_cost"]
        self.assertIs(cost["available"], True)
        self.assertIsNone(cost["unavailable_reason"])
        self.assertEqual(cost["resource_keys"], list(RESOURCE_KEYS))
        self.assertEqual(cost["raw_scale"], 100000)
        self.assertEqual(len(cost["resource_costs_raw"]), 10)
        self.assertEqual(cost["resource_costs_raw"], CB_COSTS_RAW)
        for value in cost["resource_costs_raw"]:
            self.assertIs(type(value), int)
            self.assertGreaterEqual(value, -(1 << 63))
            self.assertLessEqual(value, (1 << 63) - 1)
        self.assertIsNone(actual["generic_interaction_cost_raw"])
        self.assertIsNone(actual["total_declaration_cost_raw"])
        self.assertIs(actual["total_cost_ready"], False)
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        sent = driver.sent[0]
        self.assertEqual(sent["step"], STEP)
        self.assertEqual(sent["expected_public_revision"], FRAME["public_revision"])
        self.assertEqual(sent["expected_revision"], FRAME["native_revision"])
        self.assertEqual(sent["expected_snapshot_revision"], FRAME["native_revision"])
        self.assertEqual(sent["declaration_id"], context["declaration_id"])
        for key, value in context["selected_declaration"].items():
            self.assertEqual(sent[key], value)
        self.assertNotIn("played_character_id", sent)
        self.assertIsNone(driver.state.wait_for_command_result(REQUEST_ID, 0))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True,
                        help="Root's supplied source identity; this consumer runs no git/hash")
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = PlayerOrdinaryHolyWarDeclarationContext12004WholeWireTests(
        "test_actual4_compiled_whole_native_context_registered_service_mcp",
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.ordinary-holy-war-declaration-context-actual4-registered-mcp-first-consumption/v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "native_wire_files": [WIRE_FILE], "native_wire_dir": str(args.native_wire_dir),
        "source_root": str(args.source_root), "source_identity_supplied_by_root": args.source_sha,
        "source_hashes": None, "source_hashes_owner": "Root qualification receipt",
        "input_provenance": "Synthetic native callbacks/frame; genuine compiled actual-.4 whole packet",
        "whole_native_packets_constructed": False, "whole_native_packets_repaired": False,
        "readiness_scope": "New actual-.4 static fixture consumption only; no live capability credit",
        "registered_mcp_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "old_first_executed": False, "official_sdk_executed": False,
        "sdk_sessions": 0, "pipe_operations": 0, "game_operations": 0,
        "game_actions": 0, "new_exe_bytes": 0,
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors], **evidence,
    }
    with (args.output_dir / "OBSERVED.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(observations, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (args.output_dir / "RESULT.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
