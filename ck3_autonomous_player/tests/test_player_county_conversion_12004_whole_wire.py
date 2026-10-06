"""One actual4 FIRST consumer of adopted county read/action whole packets.

AUTHORED_NOTRUN. Root supplies six genuinely compiled full native packets and
the actual compiled receipt. Packets/rows are never constructed or repaired.
The delivered assignment is explicitly synthetic fixture memory delivery;
official SDK, game execution and county conversion completion are not claimed.
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


READ_TOOL = "ck3_query_player_clergy_appointment_v1"
SUBMIT_TOOL = "ck3_submit_county_conversion_task"
RESULT_TOOL = "ck3_query_county_conversion_task_result"
READ_STEP = "query-player-clergy-appointment-v1"
SUBMIT_STEP = "county-conversion-task-submit-private-v1"
RESULT_STEP = "county-conversion-task-result-private-v1"
RECEIPT_SCHEMA = "xar.ck3.county-conversion-native-whole-fixture12004/v1"
FILES = (
    "clergy-rr-county-dispatch-false.json",
    "clergy-current-county-conversion.json",
    "county-task-final-denied.json",
    "county-task-queued.json",
    "county-task-independent-pending.json",
    "county-task-independent-delivered.json",
)
FRAME = {
    "public_revision": 2, "native_revision": 9, "date_raw": 53230008,
    "owner_character_id": 29829, "incumbent_character_id": 56513,
    "active_task_id": 7162, "paused": True, "map_ready": True,
}
PROVENANCE = {
    "native_memory": "fixture-synthetic",
    "native_callbacks": "fixture-synthetic",
    "source_frame": "fixture-synthetic",
    "public_revision": "fixture-synthetic",
    "capture_epoch": "fixture-synthetic",
    "whole_wires": "compiled-production-serializer",
    "whole_wire_rows_repaired": False,
    "fixture_delivery": (
        "After pending output, explicit fixture-only task memory delivery before final independent read. "
        "Production native apply not emulated or claimed."
    ),
    "live": False,
}
ACTION_ID = "county4-selected-assignment"
QUEUED_REQUEST_ID = "county-task-" + f"{0x4404:032x}"


class PlayerCountyConversion12004WholeWireTests(unittest.IsolatedAsyncioTestCase):
    """The sole compound method covers two reads and four typed action packets."""

    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_six_actual4_county_whole_wires_registered_mcp_receipt_and_independent_result(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use the standalone consumer with fresh compiled actual4 county whole wires")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge.player_clergy_appointment_private_transport import (
            query_player_clergy_appointment_private_v1,
        )
        from xar_autoplayer.bridge.player_county_conversion_private_observation import (
            normalize_player_county_conversion_v1,
        )
        from xar_autoplayer.bridge.county_conversion_task_private_action_v1 import (
            submit_county_conversion_task_private_v1, query_county_conversion_task_result_private_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        receipt = json.loads(
            (self.args.native_wire_dir / "county-native-whole-receipt.json").read_text(encoding="utf-8")
        )
        exact = {
            "game_version": CK3_12004.game_version, "steam_build": 25734779,
            "executable_sha256": CK3_12004.executable_sha256,
        }
        base_exact = {key: exact[key] for key in ("game_version", "executable_sha256")}
        self.evidence["native_receipt"] = deepcopy(receipt)
        self.evidence["production_source_files"] = {
            "mcp": inspect.getsourcefile(create_server),
            "service_submit": inspect.getsourcefile(
                GameplayBridgeService.submit_county_conversion_task_private_v1
            ),
            "service_result": inspect.getsourcefile(
                GameplayBridgeService.query_county_conversion_task_result_private_v1
            ),
            "native_wrapper": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            ),
            "clergy_transport": inspect.getsourcefile(query_player_clergy_appointment_private_v1),
            "county_normalizer": inspect.getsourcefile(normalize_player_county_conversion_v1),
            "submit_transport": inspect.getsourcefile(submit_county_conversion_task_private_v1),
            "result_transport": inspect.getsourcefile(query_county_conversion_task_result_private_v1),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], 6)
        self.assertEqual(receipt["whole_wire_files"], list(FILES))
        self.assertEqual(receipt["exact_build"], exact)
        self.assertEqual({key: receipt["frame"][key] for key in FRAME}, FRAME)
        self.assertEqual(receipt["provenance"], PROVENANCE)
        case_frames = receipt["case_frames"]
        self.assertEqual([row["file"] for row in case_frames], list(FILES))
        frames_by_file = {row["file"]: row for row in case_frames}
        for row in case_frames:
            self.assertIs(type(row["capture_epoch"]), int)
            self.assertGreater(row["capture_epoch"], 0)
            self.assertIs(type(row["mailbox_sequence"]), int)
            self.assertGreater(row["mailbox_sequence"], 0)
        self.assertFalse(callable(getattr(
            GameplayBridgeService, "query_player_clergy_appointment_private_v1", None,
        )))
        self.evidence["clergy_service_query_method"] = None
        self.evidence["dispatch_paths"] = {
            "read": "registered clergy MCP -> actual Driver wrapper/private transport -> real ingest/wait -> base and county normalizers",
            "submit": "registered submit MCP -> existing Service -> actual Driver wrapper -> typed private action transport -> real ingest/wait",
            "result": "registered result MCP -> existing Service -> actual Driver wrapper -> independent result transport -> real ingest/wait",
        }

        test_case = self

        class CompiledWholeWireDriver:
            allow_private_player_clergy_appointment_query = True
            command_timeout_seconds = 1.0
            query_player_clergy_appointment_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            )
            submit_county_conversion_task_private_v1 = (
                NativeHeadlessGameplayDriver.submit_county_conversion_task_private_v1
            )
            query_county_conversion_task_result_private_v1 = (
                NativeHeadlessGameplayDriver.query_county_conversion_task_result_private_v1
            )

            def __init__(self, packet: dict[str, object]) -> None:
                self.packet = packet
                result = packet["result"]
                frame = receipt["frame"]
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
                self.state = NativeProtocolState("offline-fixture:county-conversion-actual4-whole")

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test_case.assertEqual(request["request_id"], self.packet["request_id"])
                self.sent.append(deepcopy(request))
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        outputs: dict[str, dict[str, object]] = {}
        for ordinal, filename in enumerate(FILES):
            with self.subTest(file=filename):
                packet = json.loads((self.args.native_wire_dir / filename).read_text(encoding="utf-8"))
                original = deepcopy(packet)
                record: dict[str, object] = {"file": filename, "original_native_packet": original}
                self.observations.append(record)
                prefix = "g2-read-" if ordinal < 2 else "county-task-"
                request_id = prefix + f"{0x4401 + ordinal:032x}"
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(packet["request_id"], request_id)
                native = packet["result"]
                self.assertEqual(native["game_version"], exact["game_version"])
                self.assertEqual(native["executable_sha256"], exact["executable_sha256"])
                self.assertEqual(native["snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(native["date_raw"], FRAME["date_raw"])
                epoch = frames_by_file[filename]["capture_epoch"]
                driver = CompiledWholeWireDriver(packet)
                record["fixture_public_snapshot"] = deepcopy(driver.snapshot)
                server = create_server(driver)
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertTrue({READ_TOOL, SUBMIT_TOOL, RESULT_TOOL} <= set(tools))
                self.assertIs(tools[READ_TOOL].annotations.read_only_hint, True)
                self.assertIs(tools[RESULT_TOOL].annotations.read_only_hint, True)
                if ordinal < 2:
                    tool = READ_TOOL
                    clergy = native["player_clergy_appointment"]
                    self.assertEqual(clergy["exact_build"], base_exact)
                    self.assertEqual(clergy["capture_epoch"], epoch)
                    self.assertEqual(native["county_conversion"]["capture_epoch"], epoch)
                    self.assertEqual(native["county_conversion"]["exact_build"], exact)
                    self.assertNotIn("candidate_terms", native)
                    arguments = {
                        "expected_revision": FRAME["public_revision"],
                        "candidate_character_id": clergy["candidate_character_id"],
                    }
                    uuid_path = "xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4"
                else:
                    self.assertEqual(native["backend_id"], "native-headless")
                    self.assertEqual(native["public_revision"], FRAME["public_revision"])
                    self.assertEqual(native["capture_epoch"], epoch)
                    uuid_path = "xar_autoplayer.bridge.county_conversion_task_private_action_v1.uuid.uuid4"
                    if ordinal < 4:
                        tool = SUBMIT_TOOL
                        arguments = {
                            "expected_revision": FRAME["public_revision"],
                            "expected_active_task_id": FRAME["active_task_id"],
                            "expected_incumbent_character_id": FRAME["incumbent_character_id"],
                            "province_id": 1, "replace_existing_task": False, "action_id": ACTION_ID,
                        }
                    else:
                        tool = RESULT_TOOL
                        arguments = {
                            "expected_revision": FRAME["public_revision"],
                            "submitted_request_id": QUEUED_REQUEST_ID, "action_id": ACTION_ID,
                        }
                with patch(uuid_path, return_value=SimpleNamespace(hex=request_id[len(prefix):])):
                    response = await server.call_tool(tool, arguments)
                self.assertFalse(response.is_error, response)
                actual = response.structured_content
                self.assertIsInstance(actual, dict)
                record["registered_mcp_output"] = deepcopy(actual)
                record["sent_requests"] = deepcopy(driver.sent)
                record["ingested_types"] = list(driver.ingested_types)
                self.assertEqual(packet, original)
                self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertIs(actual["advertised"], False)
                if ordinal < 2:
                    self.assertEqual({key: actual[key] for key in clergy}, clergy)
                    self.assertEqual(actual["county_conversion"], native["county_conversion"])
                    self.assertIs(actual["action_eligibility_complete"], False)
                    self.assertIs(actual["read_only"], True)
                    self.assertEqual(actual["queried_revision"], FRAME["public_revision"])
                    self.assertEqual(actual["queried_native_revision"], FRAME["native_revision"])
                    self.assertNotIn("candidate_terms", actual)
                else:
                    self.assertEqual(actual["owner_submission"], native["submission"])
                    self.assertEqual(actual["before_task"], native["submission"]["before"])
                    self.assertIs(actual["automatic_retry"], False)
                    self.assertIs(actual["county_conversion_completed"], False)
                    if ordinal >= 4:
                        self.assertEqual(actual["owner_result"], native["independent_result"])
                        self.assertEqual(actual["after_task"], native["independent_result"]["after"])
                        self.assertEqual(actual["request_id"], QUEUED_REQUEST_ID)
                for key in ("action_ready", "actionReady", "can_assign"):
                    self.assertNotIn(key, actual)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                sent = driver.sent[0]
                self.assertEqual(sent["step"], READ_STEP if ordinal < 2 else SUBMIT_STEP if ordinal < 4 else RESULT_STEP)
                self.assertEqual(sent["expected_revision"], FRAME["native_revision"])
                self.assertEqual(sent["expected_snapshot_revision"], FRAME["native_revision"])
                self.assertEqual(sent["expected_public_revision"], FRAME["public_revision"])
                if ordinal >= 2:
                    self.assertEqual(sent["expected_date_raw"], FRAME["date_raw"])
                    self.assertEqual(sent["expected_player_character_id"], FRAME["owner_character_id"])
                self.assertIsNone(driver.state.wait_for_command_result(request_id, 0))
                outputs[filename] = actual

        self.assertEqual(len(outputs), 6)
        expected_rows = {
            3: (1537, 0, 153, 500000, 3, -12),
            1: (2173, 1, 0, 125000, 0, 0),
            2: (1982, 2, 0x83000003, 350000, 4, 7),
        }
        for filename in FILES[:2]:
            county = outputs[filename]["county_conversion"]
            self.assertEqual(county["status"], "available")
            self.assertEqual(county["failure"], "none")
            self.assertEqual(county["candidate_count"], 3)
            self.assertEqual([row["county_title_id"] for row in county["candidates"]], [1537, 1982, 2173])
            values = county["value_inputs"]
            self.assertEqual(values["status"], "available")
            self.assertIs(values["owner_has_access_to_ministry"], False)
            self.assertEqual(values["owner_faith_id"], 0)
            self.assertEqual(values["incumbent_faith_id"], 0)
            for candidate, value in zip(county["candidates"], values["candidates"], strict=True):
                title, native_ordinal, rite, rate, faith, opinion = expected_rows[candidate["province_id"]]
                self.assertEqual(candidate["county_title_id"], title)
                self.assertEqual(candidate["native_collection_ordinal"], native_ordinal)
                self.assertEqual(candidate["county_rite_id"], rite)
                self.assertEqual(candidate["native_monthly_rate_raw"], rate)
                self.assertEqual(value["county_faith_id"], faith)
                self.assertEqual(value["current_popular_opinion"], opinion)
                self.assertEqual(value["destination_rite_id"], 152)
                self.assertEqual(value["destination_faith_id"], 0)
            self.assertEqual(county["task_dispatch"]["status"], "available")
            self.assertIs(county["task_dispatch"]["eligibility_inputs_complete"], True)
            self.assertIs(county["action_eligibility_complete"], True)
        rr = outputs[FILES[0]]["county_conversion"]
        self.assertEqual(rr["current_task_key"], "task_religious_relations")
        self.assertIsNone(rr["current_target_province_id"])
        self.assertIsNone(rr["current_conversion_monthly_rate_raw"])
        for row in rr["task_dispatch"]["candidates"]:
            self.assertIs(row["native_final_can_dispatch"], False)
        current = outputs[FILES[1]]["county_conversion"]
        self.assertEqual(current["current_task_key"], "task_conversion")
        self.assertEqual(current["current_target_province_id"], 1)
        self.assertEqual(current["current_target_county_title_id"], 2173)
        self.assertEqual(current["current_target_county_rite_id"], 0)
        self.assertIs(current["current_task_frozen"], True)
        self.assertEqual(current["current_percentage_progress_raw"], 8750000)
        self.assertEqual(current["current_conversion_monthly_rate_raw"], 777000)
        denied = outputs[FILES[2]]
        self.assertEqual(denied["status"], "not_submitted")
        self.assertEqual(denied["failure"], "county_task_native_final_denied")
        self.assertIs(denied["owner_submission"]["native_final_can_dispatch"], False)
        self.assertIs(denied["owner_submission"]["native_submit_copy_called"], False)
        queued = outputs[FILES[3]]
        self.assertEqual(queued["status"], "queued_verification_pending")
        self.assertIs(queued["submitted"], True)
        self.assertIs(queued["verification_pending"], True)
        self.assertIs(queued["material_result"], False)
        self.assertIs(queued["task_assignment_material_observed"], False)
        self.assertEqual(queued["owner_submission"]["command_channel"], 0x0E)
        self.assertIs(queued["owner_submission"]["native_final_can_dispatch"], True)
        pending = outputs[FILES[4]]
        self.assertEqual(pending["status"], "queued_verification_pending")
        self.assertIs(pending["verification_pending"], True)
        self.assertIs(pending["material_result"], False)
        self.assertIs(pending["actual_task_assignment_matches"], False)
        delivered = outputs[FILES[5]]
        self.assertEqual(delivered["status"], "task_assignment_material_observed")
        self.assertIs(delivered["verification_pending"], False)
        self.assertIs(delivered["material_result"], True)
        self.assertIs(delivered["actual_task_assignment_matches"], True)
        for result in (pending, delivered):
            self.assertIs(result["actual_task_id_unchanged"], True)
            self.assertIs(result["county_conversion_completed"], False)
            self.assertEqual(result["owner_submission"], queued["owner_submission"])
            self.assertGreater(result["after_task"]["capture_epoch"], queued["owner_submission"]["capture_epoch"])
        self.assertEqual(delivered["after_task"]["task_key"], "task_conversion")
        self.assertEqual(delivered["after_task"]["target_scope_tag"], 8)
        self.assertEqual(delivered["after_task"]["target_province_id"], 1)
        self.assertEqual(delivered["after_task"]["target_county_title_id"], 2173)
        self.assertEqual(delivered["after_task"]["percentage_progress_raw"], 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True, help="Root's immutable source pin; no Git/hash run here")
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = PlayerCountyConversion12004WholeWireTests(
        "test_six_actual4_county_whole_wires_registered_mcp_receipt_and_independent_result"
    )
    test.args = args
    test.observations = observations
    test.evidence = evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    successful = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.county-conversion-12004-registered-mcp-first-consumption/v1",
        "status": "GREEN" if successful else "RED",
        "test_method": test._testMethodName, "test_methods_run": result.testsRun,
        "source_root": str(args.source_root), "source_identity_supplied_by_root": args.source_sha,
        "source_hashes": None, "source_hashes_owner": "Root qualification receipt",
        "native_wire_dir": str(args.native_wire_dir), "native_wire_files": list(FILES),
        "whole_native_packets_constructed": False, "whole_native_packets_repaired": False,
        "whole_native_packets_relabelled": False,
        "readiness_scope": "Actual4 static fixture consumption only",
        "fixture_delivery": PROVENANCE["fixture_delivery"], "production_native_apply_executed": False,
        "county_conversion_completion_claimed": False,
        "base_six_cases_replayed": 0, "old_cases_replayed": 0,
        "registered_mcp_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "official_sdk_executed": False, "sdk_sessions": 0, "pipe_operations": 0,
        "game_operations": 0, "game_actions": 0, "new_exe_bytes": 0,
        "failures": [trace for _, trace in result.failures], "errors": [trace for _, trace in result.errors],
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
