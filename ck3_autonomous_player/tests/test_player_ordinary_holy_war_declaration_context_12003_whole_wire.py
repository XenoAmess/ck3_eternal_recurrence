"""Sole FIRST registered Service/MCP consumer of five compiled whole native wires.

Prepared NOTRUN. Root supplies fresh output from the compiled native producer;
this consumer never authors or repairs native packets and never opens CK3.
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
RECEIPT_SCHEMA = "xar.ck3.ordinary-holy-war-declaration-context-native-whole-fixture/v1"
FILES = (
    "native-wire-nonzero.json", "native-wire-known-zero.json",
    "native-wire-redirected-additional.json", "native-wire-native-fallback.json",
    "native-wire-cb-unavailable.json",
)
FRAME = {
    "public_revision": 2, "native_revision": 9, "date_raw": 53222304,
    "played_character_id": 50331649, "capture_epoch": 991,
    "paused": True, "map_ready": True,
}


class PlayerOrdinaryHolyWarDeclarationContext12003WholeWireTests(unittest.IsolatedAsyncioTestCase):
    """One actual production consumption compound, using unchanged whole wires."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_five_compiled_whole_native_contexts_registered_service_mcp(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Run standalone with the fresh compiled native-wire directory")
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
        from xar_autoplayer.bridge.version_identity import CK3_12003

        receipt = json.loads(
            (self.args.native_wire_dir / "producer-receipt.json").read_text(encoding="utf-8")
        )
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
            "registered create_server tool -> real GameplayBridgeService method -> "
            "NativeHeadlessGameplayDriver wrapper -> existing private query transport -> "
            "NativeProtocolState.ingest/wait -> strict normalizer"
        )
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], len(FILES))
        self.assertEqual(receipt["whole_wire_files"], list(FILES))
        self.assertEqual(receipt["frame"], FRAME)
        self.assertEqual(receipt["provenance"]["whole_wires"], "compiled-production-serializer")
        self.assertIs(receipt["provenance"]["whole_wire_rows_repaired"], False)
        exact = {
            "game_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
        }
        self.assertEqual(receipt["exact_build"], exact)

        test = self

        class CompiledWholeWireDriver:
            allow_private_player_ordinary_holy_war_declaration_context_query = True
            command_timeout_seconds = 1.0
            query_player_ordinary_holy_war_declaration_context_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_ordinary_holy_war_declaration_context_private_v1
            )

            def __init__(self, packet: dict[str, object]) -> None:
                self.packet = packet
                result = packet["result"]
                context = result["player_ordinary_holy_war_declaration_context"]
                # The public fixture snapshot is explicitly synthetic. Its
                # identity and selected row are the unchanged compiled wire's
                # values, never patched native return values.
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
                self.state = NativeProtocolState("offline-fixture:ordinary-holy-war-context-whole")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test.assertEqual(request["request_id"], self.packet["request_id"])
                self.sent.append(deepcopy(request))
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        original_service_query = (
            GameplayBridgeService.query_player_ordinary_holy_war_declaration_context_private_v1
        )
        service_calls: list[dict[str, object]] = []

        def record_real_service_query(service: GameplayBridgeService, **kwargs: object) -> dict[str, object]:
            service_calls.append(deepcopy(kwargs))
            return original_service_query(service, **kwargs)

        outputs: dict[str, dict[str, object]] = {}
        for ordinal, filename in enumerate(FILES, start=0x4701):
            with self.subTest(file=filename):
                packet = json.loads((self.args.native_wire_dir / filename).read_text(encoding="utf-8"))
                original_packet = deepcopy(packet)
                record: dict[str, object] = {
                    "file": filename, "original_native_packet": original_packet,
                }
                self.observations.append(record)
                request_id = f"g2-read-{ordinal:032x}"
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(packet["request_id"], request_id)
                result = packet["result"]
                context = result["player_ordinary_holy_war_declaration_context"]
                self.assertEqual(context["schema"], SCHEMA)
                self.assertEqual(result["step"], STEP)
                self.assertEqual(result["snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(result["public_revision"], FRAME["public_revision"])
                self.assertEqual(context["capture_epoch"], FRAME["capture_epoch"])
                self.assertEqual(context["native_revision"], FRAME["native_revision"])
                self.assertEqual(context["public_revision"], FRAME["public_revision"])
                self.assertEqual(context["date_raw"], FRAME["date_raw"])
                self.assertEqual(context["played_character_id"], FRAME["played_character_id"])
                self.assertEqual(context["game_version"], exact["game_version"])
                self.assertEqual(context["executable_sha256"], exact["executable_sha256"])

                driver = CompiledWholeWireDriver(packet)
                record["fixture_public_snapshot"] = deepcopy(driver.snapshot)
                server = create_server(driver)
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertIn(TOOL, tools)
                self.assertIs(tools[TOOL].annotations.read_only_hint, True)
                # Only the outgoing UUID source is fixed to the compiled native
                # correlation ID. The input packet remains completely intact.
                with patch(
                    "xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                    return_value=SimpleNamespace(hex=request_id[len("g2-read-"):]),
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
                self.assertEqual({key: actual[key] for key in context}, context)
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
                self.assertEqual(actual["cb_cost"]["resource_keys"], list(RESOURCE_KEYS))
                self.assertEqual(actual["cb_cost"]["raw_scale"], 100000)
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
                for key, item in context["selected_declaration"].items():
                    self.assertEqual(sent[key], item)
                self.assertNotIn("played_character_id", sent)
                self.assertIsNone(driver.state.wait_for_command_result(request_id, 0))
                outputs[filename] = actual

        self.assertEqual(len(outputs), len(FILES))
        self.assertEqual(len(service_calls), len(FILES))
        self.evidence["actual_service_calls"] = service_calls
        nonzero = outputs[FILES[0]]
        self.assertIs(nonzero["cb_cost"]["available"], True)
        self.assertTrue(any(nonzero["cb_cost"]["resource_costs_raw"]))
        # A final false gate must not erase a successfully evaluated CB quote.
        self.assertIs(nonzero["final_can_send"], False)
        zero = outputs[FILES[1]]
        self.assertIs(zero["cb_cost"]["available"], True)
        self.assertEqual(zero["cb_cost"]["resource_costs_raw"], [0] * 10)
        redirected = outputs[FILES[2]]
        self.assertNotEqual(redirected["context_additional_role_character_id"], redirected["played_character_id"])
        self.assertIs(redirected["additional_role_uses_native_fallback"], False)
        fallback = outputs[FILES[3]]
        self.assertEqual(fallback["context_claimant_character_id"], -1)
        self.assertIs(fallback["claimant_uses_native_fallback"], True)
        unavailable = outputs[FILES[4]]
        self.assertIs(unavailable["available"], True)
        self.assertIs(unavailable["cb_cost"]["available"], False)
        self.assertIsNone(unavailable["cb_cost"]["resource_costs_raw"])
        self.assertIsInstance(unavailable["cb_cost"]["unavailable_reason"], str)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True,
                        help="Root's source identity; this consumer runs no git/hash")
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = PlayerOrdinaryHolyWarDeclarationContext12003WholeWireTests(
        "test_five_compiled_whole_native_contexts_registered_service_mcp",
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.ordinary-holy-war-declaration-context-registered-mcp-first-consumption/v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "native_wire_files": list(FILES), "native_wire_dir": str(args.native_wire_dir),
        "source_root": str(args.source_root), "source_identity_supplied_by_root": args.source_sha,
        "source_hashes": None, "source_hashes_owner": "Root qualification receipt",
        "input_provenance": "Synthetic native callbacks/frame; genuine compiled whole native packets",
        "whole_native_packets_constructed": False, "whole_native_packets_repaired": False,
        "readiness_scope": "Static fixture consumption only; no live capability credit",
        "registered_mcp_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "official_sdk_executed": False, "sdk_sessions": 0, "pipe_operations": 0,
        "game_operations": 0, "game_actions": 0, "new_exe_bytes": 0,
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
