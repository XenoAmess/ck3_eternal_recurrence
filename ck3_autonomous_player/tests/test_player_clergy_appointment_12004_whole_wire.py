"""One actual4 migration FIRST consumer of six compiled whole clergy packets.

AUTHORED_NOTRUN. Root supplies fresh native output and its compiled receipt.
Native packets are never constructed, relabelled or repaired here. Official
SDK and live qualification remain separate Root-owned work.
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


TOOL = "ck3_query_player_clergy_appointment_v1"
STEP = "query-player-clergy-appointment-v1"
BASE_SCHEMA = "xar.ck3.religion-clergy-appointment/v1"
NATIVE_RECEIPT_SCHEMA = "xar.ck3.clergy-appointment-12004-native-whole-fixture/v1"
FILES = (
    "occupied-reassign-true-fire-false.json",
    "occupied-reassign-false-fire-true.json",
    "vacant-fire-null.json",
    "absent-position.json",
    "candidate-unavailable.json",
    "bindings-unavailable.json",
)
FRAME = {
    "public_revision": 2, "native_revision": 11, "capture_epoch": 1007,
    "date_raw": 53288256, "owner_character_id": 29829, "active_task_id": 7162,
    "incumbent_character_id": 56513, "candidate_character_id": 16777232,
    "paused": True, "map_ready": True,
}
PROVENANCE = {
    "native_memory": "fixture-synthetic",
    "native_callbacks": "fixture-synthetic",
    "source_frame": "fixture-synthetic",
    "public_revision": "fixture-synthetic",
    "capture_epoch": "fixture-synthetic",
    "whole_wires": "compiled-production-serializer",
    "whole_wire_rows_repaired": False,
}
ACTION_PROFILE = {
    "positions": ["councillor_steward", "councillor_chancellor", "councillor_spymaster"],
    "chaplain_assignment_supported": False,
    "action_eligibility_complete": False,
}
PREDICATES = (
    "native_valid_position", "native_valid_character",
    "native_can_reassign", "native_can_fire",
)


class PlayerClergyAppointment12004WholeWireTests(unittest.IsolatedAsyncioTestCase):
    """The sole compound method consumes every new migration case."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_six_actual4_compiled_whole_wires_registered_mcp_and_original_action_profile(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use the standalone consumer with fresh compiled actual4 whole wires")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge.player_clergy_appointment_private_transport import (
            normalize_player_clergy_appointment_v1, query_player_clergy_appointment_private_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        receipt = json.loads(
            (self.args.native_wire_dir / "native-whole-receipt.json").read_text(encoding="utf-8")
        )
        self.evidence["native_receipt"] = deepcopy(receipt)
        self.evidence["production_source_files"] = {
            "mcp": inspect.getsourcefile(create_server),
            "service_class": inspect.getsourcefile(GameplayBridgeService),
            "native_wrapper": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            ),
            "query_transport": inspect.getsourcefile(query_player_clergy_appointment_private_v1),
            "base_normalizer": inspect.getsourcefile(normalize_player_clergy_appointment_v1),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        exact = {
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
        }
        self.assertEqual(receipt["schema"], NATIVE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], 6)
        self.assertEqual(receipt["whole_wire_files"], list(FILES))
        self.assertEqual(receipt["exact_build"], exact)
        self.assertEqual({key: receipt["frame"][key] for key in FRAME}, FRAME)
        self.assertEqual(receipt["provenance"], PROVENANCE)
        self.assertEqual(receipt["original_action_profile"], ACTION_PROFILE)
        # This registration invokes the real Driver wrapper directly. Do not
        # invent a clergy Service query because create_server builds a Service.
        self.assertFalse(callable(getattr(
            GameplayBridgeService, "query_player_clergy_appointment_private_v1", None,
        )))
        self.evidence["service_query_method"] = None
        self.evidence["dispatch_path"] = (
            "registered clergy MCP -> NativeHeadlessGameplayDriver wrapper -> "
            "existing private query transport -> real NativeProtocolState.ingest/wait -> "
            "existing base normalizer with exact actual4 identity"
        )

        test_case = self

        class CompiledWholeWireDriver:
            allow_private_player_clergy_appointment_query = True
            command_timeout_seconds = 1.0
            query_player_clergy_appointment_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            )

            def __init__(self, packet: dict[str, object]) -> None:
                self.packet = packet
                result = packet["result"]
                frame = receipt["frame"]
                # This semantic snapshot is explicit synthetic fixture input.
                # Frame owner/paused/map come from the native receipt; build,
                # native revision/date come from the actual whole packet.
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": frame["public_revision"],
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {"character_id": frame["owner_character_id"], "alive": True},
                    "paused": frame["paused"], "map_ready": frame["map_ready"],
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:clergy-appointment-actual4-whole")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test_case.assertEqual(request["request_id"], self.packet["request_id"])
                self.sent.append(deepcopy(request))
                # Entire native packet is ingested untouched. Only outgoing
                # UUID generation is aligned with its compiled request ID.
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        outputs: dict[str, dict[str, object]] = {}
        for index, filename in enumerate(FILES, start=0x4401):
            with self.subTest(file=filename):
                packet = json.loads((self.args.native_wire_dir / filename).read_text(encoding="utf-8"))
                original = deepcopy(packet)
                record: dict[str, object] = {"file": filename, "original_native_packet": original}
                self.observations.append(record)
                request_id = f"g2-read-{index:032x}"
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(packet["request_id"], request_id)
                result = packet["result"]
                clergy = result["player_clergy_appointment"]
                self.assertEqual(clergy["schema"], BASE_SCHEMA)
                self.assertEqual(clergy["exact_build"], exact)
                self.assertEqual(result["game_version"], exact["game_version"])
                self.assertEqual(result["executable_sha256"], exact["executable_sha256"])
                self.assertEqual(result["snapshot_revision"], receipt["frame"]["native_revision"])
                self.assertEqual(result["date_raw"], receipt["frame"]["date_raw"])
                self.assertEqual(clergy["capture_epoch"], receipt["frame"]["capture_epoch"])
                self.assertEqual(clergy["owner_character_id"], receipt["frame"]["owner_character_id"])
                self.assertEqual(clergy["date_raw"], receipt["frame"]["date_raw"])
                self.assertEqual(clergy["candidate_character_id"], receipt["frame"]["candidate_character_id"])
                self.assertNotIn("candidate_terms", result)
                self.assertNotIn("county_conversion", result)

                driver = CompiledWholeWireDriver(packet)
                record["fixture_public_snapshot"] = deepcopy(driver.snapshot)
                server = create_server(driver)
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertIn(TOOL, tools)
                self.assertIs(tools[TOOL].annotations.read_only_hint, True)
                with patch(
                    "xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                    return_value=SimpleNamespace(hex=request_id[len("g2-read-"):]),
                ):
                    response = await server.call_tool(TOOL, {
                        "expected_revision": driver.snapshot["revision"],
                        "candidate_character_id": clergy["candidate_character_id"],
                    })
                self.assertFalse(response.is_error, response)
                actual = response.structured_content
                self.assertIsInstance(actual, dict)
                record["registered_mcp_output"] = deepcopy(actual)
                record["sent_requests"] = deepcopy(driver.sent)
                record["ingested_types"] = list(driver.ingested_types)
                self.assertEqual({key: actual[key] for key in clergy}, clergy)
                self.assertEqual(packet, original)
                self.assertEqual(actual["query_status"], result["status"])
                self.assertEqual(actual["status"], clergy["status"])
                self.assertEqual(actual["snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(actual["queried_revision"], FRAME["public_revision"])
                self.assertEqual(actual["queried_native_revision"], FRAME["native_revision"])
                self.assertEqual(actual["query_date_raw"], FRAME["date_raw"])
                self.assertEqual(actual["backend_id"], result["backend_id"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertIs(actual["action_eligibility_complete"], False)
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                for key in ("candidate_terms", "county_conversion", "action_ready", "actionReady", "can_assign"):
                    self.assertNotIn(key, actual)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                sent = driver.sent[0]
                self.assertEqual(sent["step"], STEP)
                self.assertEqual(sent["candidate_character_id"], FRAME["candidate_character_id"])
                self.assertEqual(sent["expected_public_revision"], FRAME["public_revision"])
                self.assertEqual(sent["expected_revision"], FRAME["native_revision"])
                self.assertEqual(sent["expected_snapshot_revision"], FRAME["native_revision"])
                self.assertNotIn("owner_character_id", sent)
                self.assertIsNone(driver.state.wait_for_command_result(request_id, 0))
                outputs[filename] = actual

        self.assertEqual(len(outputs), 6)
        for filename in FILES[:3]:
            actual = outputs[filename]
            self.assertEqual(actual["status"], "available")
            self.assertEqual(actual["query_status"], "observed")
            self.assertEqual(actual["failure"], "none")
            self.assertIs(actual["position_present"], True)
            self.assertEqual(actual["active_task_id"], FRAME["active_task_id"])
            self.assertIs(actual["candidate_is_incumbent"], False)
            self.assertIs(actual["native_valid_position"], True)
            self.assertIs(actual["native_valid_character"], True)
        first = outputs[FILES[0]]
        second = outputs[FILES[1]]
        self.assertEqual(first["incumbent_character_id"], FRAME["incumbent_character_id"])
        self.assertEqual(second["incumbent_character_id"], FRAME["incumbent_character_id"])
        self.assertIs(first["native_can_reassign"], True)
        self.assertIs(first["native_can_fire"], False)
        self.assertIs(second["native_can_reassign"], False)
        self.assertIs(second["native_can_fire"], True)
        self.assertIsNone(outputs["vacant-fire-null.json"]["incumbent_character_id"])
        self.assertIsNone(outputs["vacant-fire-null.json"]["native_can_fire"])
        absent = outputs["absent-position.json"]
        self.assertEqual(absent["status"], "available")
        self.assertEqual(absent["query_status"], "observed")
        self.assertEqual(absent["failure"], "none")
        self.assertIs(absent["position_present"], False)
        self.assertIsNone(absent["active_task_id"])
        self.assertIsNone(absent["incumbent_character_id"])
        for key in PREDICATES:
            self.assertIsNone(absent[key])
        for filename, failure in (
            ("candidate-unavailable.json", "candidate_unavailable"),
            ("bindings-unavailable.json", "bindings_unavailable"),
        ):
            actual = outputs[filename]
            self.assertEqual(actual["status"], "unavailable")
            self.assertEqual(actual["query_status"], "unavailable")
            self.assertEqual(actual["failure"], failure)
            self.assertIs(actual["position_present"], False)
            for key in ("active_task_id", "incumbent_character_id",
                        "candidate_court_owner_id", "owner_rite_id", "candidate_rite_id",
                        "candidate_matches_owner_context", *PREDICATES):
                self.assertIsNone(actual[key])
            # Existing mailbox projects its owning owner/date into unavailable
            # full wires. This consumer preserves those actual native fields.
            self.assertEqual(actual["owner_character_id"], FRAME["owner_character_id"])
            self.assertEqual(actual["date_raw"], FRAME["date_raw"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True,
                        help="Root's immutable source pin; no git/hash runs in this consumer")
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = PlayerClergyAppointment12004WholeWireTests(
        "test_six_actual4_compiled_whole_wires_registered_mcp_and_original_action_profile"
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    successful = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.clergy-appointment-12004-registered-mcp-first-consumption/v1",
        "status": "GREEN" if successful else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "native_wire_files": list(FILES), "native_wire_dir": str(args.native_wire_dir),
        "source_root": str(args.source_root), "source_identity_supplied_by_root": args.source_sha,
        "source_hashes": None, "source_hashes_owner": "Root qualification receipt",
        "input_provenance": "Explicit synthetic native/source/epoch fixture; genuine compiled actual4 whole packets",
        "whole_native_packets_constructed": False, "whole_native_packets_relabelled": False,
        "whole_native_packets_repaired": False,
        "readiness_scope": "Actual4 static fixture consumption only; no live or action credit",
        "old_candidate_terms_six_case_green_reused": False, "old_cases_rerun": 0,
        "registered_mcp_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "official_sdk_executed": False, "sdk_sessions": 0, "pipe_operations": 0,
        "game_operations": 0, "game_actions": 0, "new_exe_bytes": 0,
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors],
        **evidence,
    }
    with (args.output_dir / "OBSERVED.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(observations, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (args.output_dir / "RESULT.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
