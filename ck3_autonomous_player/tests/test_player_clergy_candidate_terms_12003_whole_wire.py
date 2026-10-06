"""One FIRST consumer of six compiled full native clergy wires; prepared NOTRUN.

No native packet is constructed or repaired here. Root supplies the fresh native
output directory and its compiled fixture receipt. Official SDK execution is a
separate Root-owned qualification.
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
TERMS_SCHEMA = "xar.ck3.clergy-candidate-terms/v1"
NATIVE_RECEIPT_SCHEMA = "xar.ck3.clergy-candidate-terms-native-whole-fixture/v1"
FILES = (
    "occupied-confirm-false.json",
    "occupied-confirm-true.json",
    "guest-pending-true.json",
    "incumbent-not-in-collection.json",
    "vacant-confirm-null.json",
    "native-terms-unavailable.json",
)
FRAME = {
    "public_revision": 2, "native_revision": 9,
    "date_raw": 53222304, "owner_character_id": 29829, "active_task_id": 7162,
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
    "function": "EvaluateCouncilGates12002",
    "position_key": "councillor_court_chaplain",
    "returned": False, "available": False, "native_predicate_calls": 0,
}
FINAL_FLAGS = (
    "candidate_already_councillor", "candidate_is_guest",
    "pending_character_interaction", "native_can_confirm_replacement",
)


class PlayerClergyCandidateTerms12003WholeWireTests(unittest.IsolatedAsyncioTestCase):
    """The sole test method covers six fresh files and the native action receipt."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_six_compiled_whole_clergy_wires_registered_mcp_and_original_action_profile(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Run the standalone consumer with the fresh compiled native-wire directory")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import (
            NativeHeadlessGameplayDriver, NativeProtocolState,
        )
        from xar_autoplayer.bridge.player_clergy_appointment_private_transport import (
            query_player_clergy_appointment_private_v1,
        )
        from xar_autoplayer.bridge.player_clergy_candidate_terms_private_observation import (
            normalize_player_clergy_candidate_terms_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12003

        native_receipt = json.loads(
            (self.args.native_wire_dir / "native-whole-receipt.json").read_text(encoding="utf-8")
        )
        self.evidence["native_receipt"] = deepcopy(native_receipt)
        self.evidence["production_source_files"] = {
            "mcp": inspect.getsourcefile(create_server),
            "service_class": inspect.getsourcefile(GameplayBridgeService),
            "native_wrapper": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            ),
            "query_transport": inspect.getsourcefile(query_player_clergy_appointment_private_v1),
            "terms_normalizer": inspect.getsourcefile(normalize_player_clergy_candidate_terms_v1),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        self.assertEqual(native_receipt["schema"], NATIVE_RECEIPT_SCHEMA)
        self.assertEqual(native_receipt["status"], "GREEN")
        self.assertEqual(native_receipt["cases"], 6)
        self.assertEqual(native_receipt["whole_wire_files"], list(FILES))
        fixture_frame = native_receipt["frame"]
        self.assertEqual({key: fixture_frame[key] for key in FRAME}, FRAME)
        self.assertIs(type(fixture_frame["capture_epoch"]), int)
        self.assertGreater(fixture_frame["capture_epoch"], 0)
        self.assertEqual(native_receipt["provenance"], PROVENANCE)
        self.assertEqual(native_receipt["original_action_profile"], ACTION_PROFILE)
        exact_build = {
            "game_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
        }
        self.assertEqual(native_receipt["exact_build"], exact_build)
        # The currently registered clergy query calls the driver directly. Its
        # actual path must not be represented as a nonexistent Service method.
        self.assertFalse(callable(getattr(
            GameplayBridgeService, "query_player_clergy_appointment_private_v1", None,
        )))
        self.evidence["service_query_method"] = None
        self.evidence["dispatch_path"] = (
            "create_server creates GameplayBridgeService; registered clergy tool invokes "
            "NativeHeadlessGameplayDriver wrapper directly -> existing private query "
            "transport -> NativeProtocolState.ingest/wait -> strict normalizers"
        )

        test = self

        class CompiledWholeWireDriver:
            allow_private_player_clergy_appointment_query = True
            command_timeout_seconds = 1.0
            query_player_clergy_appointment_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            )

            def __init__(self, packet: dict[str, object]) -> None:
                self.packet = packet
                # The native revision/date/player/build come from this actual
                # whole wire. Its public revision and paused/map bindings are
                # explicit synthetic fixture inputs, never guessed revisions.
                frame = native_receipt["frame"]
                result = packet["result"]
                clergy = result["player_clergy_appointment"]
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": frame["public_revision"],
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {
                        "character_id": clergy["owner_character_id"], "alive": True,
                    },
                    "paused": frame["paused"], "map_ready": frame["map_ready"],
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:clergy-candidate-terms-whole")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test.assertEqual(request["request_id"], self.packet["request_id"])
                self.sent.append(deepcopy(request))
                # Feed the genuine entire parsed file unchanged. Do not patch
                # its request_id, build, sibling, failure or raw native rows.
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        outputs: dict[str, dict[str, object]] = {}
        for index, filename in enumerate(FILES, start=0x4301):
            with self.subTest(file=filename):
                packet = json.loads((self.args.native_wire_dir / filename).read_text(encoding="utf-8"))
                original_packet = deepcopy(packet)
                record: dict[str, object] = {"file": filename, "original_native_packet": original_packet}
                self.observations.append(record)
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                request_id = f"g2-read-{index:032x}"
                self.assertEqual(packet["request_id"], request_id)
                result = packet["result"]
                clergy = result["player_clergy_appointment"]
                terms = result["candidate_terms"]
                self.assertEqual(clergy["schema"], BASE_SCHEMA)
                self.assertEqual(terms["schema"], TERMS_SCHEMA)
                self.assertEqual(clergy["exact_build"], exact_build)
                self.assertEqual(terms["exact_build"], exact_build)
                self.assertEqual(result["game_version"], exact_build["game_version"])
                self.assertEqual(result["executable_sha256"], exact_build["executable_sha256"])
                self.assertEqual(result["snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(result["date_raw"], FRAME["date_raw"])
                # Epoch comes from the actual native mailbox pump and compiled
                # wire; the consumer never installs a guessed capture epoch.
                self.assertEqual(terms["capture_epoch"], clergy["capture_epoch"])
                self.assertEqual(clergy["capture_epoch"], fixture_frame["capture_epoch"])
                self.assertEqual(terms["public_revision"], FRAME["public_revision"])
                self.assertEqual(terms["native_revision"], FRAME["native_revision"])
                self.assertEqual(terms["owner_character_id"], FRAME["owner_character_id"])
                self.assertEqual(terms["active_task_id"], FRAME["active_task_id"])
                self.assertEqual(terms["incumbent_character_id"], clergy["incumbent_character_id"])
                self.assertEqual(terms["candidate_character_id"], clergy["candidate_character_id"])
                self.assertIs(terms["candidate_collection_available"], True)
                self.assertEqual(terms["candidate_count"], 2)

                driver = CompiledWholeWireDriver(packet)
                record["fixture_public_snapshot"] = deepcopy(driver.snapshot)
                server = create_server(driver)
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertIn(TOOL, tools)
                self.assertIs(tools[TOOL].annotations.read_only_hint, True)
                # Only the outgoing UUID source is controlled to match the
                # already compiled native correlation ID. No return is edited.
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
                self.assertEqual(actual["candidate_terms"], terms)
                if "county_conversion" in result:
                    self.assertEqual(actual["county_conversion"], result["county_conversion"])
                else:
                    self.assertNotIn("county_conversion", actual)
                self.assertEqual(packet, original_packet)
                self.assertEqual(actual["query_status"], result["status"])
                self.assertEqual(actual["status"], clergy["status"])
                self.assertEqual(actual["status"], "available")
                self.assertEqual(actual["query_status"], "observed")
                self.assertIs(actual["native_valid_position"], True)
                self.assertIs(actual["native_valid_character"], True)
                self.assertIs(actual["native_can_reassign"], False)
                if filename == "vacant-confirm-null.json":
                    self.assertIsNone(actual["native_can_fire"])
                else:
                    self.assertIs(actual["native_can_fire"], False)
                self.assertEqual(actual["snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(actual["queried_revision"], FRAME["public_revision"])
                self.assertEqual(actual["queried_native_revision"], FRAME["native_revision"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertIs(actual["action_eligibility_complete"], False)
                self.assertIs(actual["candidate_terms"]["action_eligibility_complete"], False)
                self.assertIs(actual["read_only"], True)
                for value in (actual, actual["candidate_terms"]):
                    for key in ("action_ready", "actionReady", "can_assign"):
                        self.assertNotIn(key, value)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                sent = driver.sent[0]
                self.assertEqual(sent["step"], STEP)
                self.assertEqual(sent["candidate_character_id"], clergy["candidate_character_id"])
                self.assertEqual(sent["expected_public_revision"], FRAME["public_revision"])
                self.assertEqual(sent["expected_revision"], FRAME["native_revision"])
                self.assertEqual(sent["expected_snapshot_revision"], FRAME["native_revision"])
                self.assertNotIn("owner_character_id", sent)
                self.assertIsNone(driver.state.wait_for_command_result(request_id, 0))
                outputs[filename] = actual

        self.assertEqual(len(outputs), 6)
        for filename in FILES:
            terms = outputs[filename]["candidate_terms"]
            if filename == "incumbent-not-in-collection.json":
                self.assertIs(terms["available"], True)
                self.assertEqual(terms["failure"], "none")
                self.assertEqual(terms["candidate_character_id"], 56513)
                self.assertEqual(terms["candidate_match_count"], 0)
                self.assertIs(terms["candidate_in_native_collection"], False)
                self.assertIsNone(terms["candidate_learning"])
                self.assertIsNone(terms["native_collection_ordinal"])
                self.assertIs(terms["final_predicates_available"], False)
                for key in FINAL_FLAGS:
                    self.assertIsNone(terms[key])
                continue
            self.assertEqual(terms["candidate_character_id"], 16777232)
            self.assertEqual(terms["candidate_match_count"], 1)
            self.assertIs(terms["candidate_in_native_collection"], True)
            self.assertEqual(terms["candidate_learning"], 29)
            self.assertEqual(terms["native_collection_ordinal"], 1)
            if filename == "native-terms-unavailable.json":
                self.assertIs(terms["available"], False)
                self.assertEqual(terms["failure"], "native_predicate_unavailable")
                self.assertIs(terms["final_predicates_available"], False)
                for key in FINAL_FLAGS:
                    self.assertIsNone(terms[key])
                # Known collection fields survive the independent route read
                # failure; the available base clergy domain stays available.
                self.assertEqual(outputs[filename]["status"], "available")
                continue
            self.assertIs(terms["available"], True)
            self.assertEqual(terms["failure"], "none")
            self.assertIs(terms["final_predicates_available"], True)
            is_guest_pending_case = filename == "guest-pending-true.json"
            for key in FINAL_FLAGS[:3]:
                self.assertIs(terms[key], is_guest_pending_case)
            if filename == "vacant-confirm-null.json":
                self.assertIsNone(terms["incumbent_character_id"])
                self.assertIsNone(terms["native_can_confirm_replacement"])
            else:
                self.assertEqual(terms["incumbent_character_id"], 56513)
                self.assertIs(terms["native_can_confirm_replacement"],
                              filename == "occupied-confirm-true.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True,
                        help="Root's already qualified immutable source identity; no git/hash is run here")
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = PlayerClergyCandidateTerms12003WholeWireTests(
        "test_six_compiled_whole_clergy_wires_registered_mcp_and_original_action_profile"
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    suite = unittest.TestSuite([test])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.clergy-candidate-terms-registered-mcp-first-consumption/v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "native_wire_files": list(FILES), "native_wire_dir": str(args.native_wire_dir),
        "source_root": str(args.source_root), "source_identity_supplied_by_root": args.source_sha,
        "source_hashes": None, "source_hashes_owner": "Root qualification receipt",
        "input_provenance": "Fixture-synthetic native/source/epoch metadata; genuine compiled whole native packets",
        "whole_native_packets_constructed": False, "whole_native_packets_repaired": False,
        "readiness_scope": "Static fixture consumption only; no live capability credit",
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
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
