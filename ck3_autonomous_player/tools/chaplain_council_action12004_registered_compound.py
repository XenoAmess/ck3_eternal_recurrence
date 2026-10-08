"""Consume fresh actual4 Chaplain Council query/action/independent receipt wires.

SOURCE_NOTRUN. Root supplies the compiled whole packets and case manifest.
Only outgoing request UUIDs are correlated; native bodies are not repaired.
This compound does not execute CK3, an official SDK session or a native target.
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


RECEIPT_SCHEMA = "xar.ck3.chaplain-council-action-12004-native-whole-fixture/v1"
POSITION = "councillor_court_chaplain"
QUERY_TOOL = "ck3_query_council_final_gates_private_v1"
ASSIGN_TOOL = "ck3_assign_councillor_private_v1"
RESULT_TOOL = "ck3_query_council_assign_receipt_private_v1"


class ChaplainCouncilAction12004RegisteredCompound(unittest.IsolatedAsyncioTestCase):
    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_fresh_chaplain_query_typed_action_and_independent_incumbent_receipt(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use the standalone consumer with Root's fresh compiled whole packets")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
            build_assign_councillor_request_v1,
            normalize_assign_councillor_ack_v1,
            normalize_assign_councillor_receipt_v1,
        )
        from xar_autoplayer.bridge.council_private_transport_v1 import (
            query_council_private_v1, submit_council_assign_private_v1,
            query_council_assign_receipt_private_v1,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.private_council_formal_consumer_v1 import select_council_candidate_v1

        receipt = json.loads((self.args.native_fixtures_dir / "native-whole-receipt.json").read_text(encoding="utf-8"))
        self.evidence["native_receipt"] = deepcopy(receipt)
        self.evidence["production_source_files"] = {
            "registration": inspect.getsourcefile(create_server),
            "driver": inspect.getsourcefile(NativeHeadlessGameplayDriver),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
            "query_transport": inspect.getsourcefile(query_council_private_v1),
            "submit_transport": inspect.getsourcefile(submit_council_assign_private_v1),
            "receipt_transport": inspect.getsourcefile(query_council_assign_receipt_private_v1),
            "request_contract": inspect.getsourcefile(build_assign_councillor_request_v1),
            "ack_contract": inspect.getsourcefile(normalize_assign_councillor_ack_v1),
            "receipt_contract": inspect.getsourcefile(normalize_assign_councillor_receipt_v1),
            "selector": inspect.getsourcefile(select_council_candidate_v1),
            "normal_service_plan": inspect.getsourcefile(GameplayBridgeService.plan_turn),
        }
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["exact_build"], {
            "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256,
        })
        cases = receipt["cases"]
        self.assertIsInstance(cases, list)
        self.assertTrue(cases)
        observed_applied_routes: set[str] = set()
        observed_rejections: set[str] = set()
        test = self

        class CompiledWholeDriver:
            allow_private_council_query = True
            allow_private_council_action = True
            command_timeout_seconds = 1.0
            query_council_final_gates_private_v1 = NativeHeadlessGameplayDriver.query_council_final_gates_private_v1
            submit_council_assign_private_v1 = NativeHeadlessGameplayDriver.submit_council_assign_private_v1
            query_council_assign_receipt_private_v1 = NativeHeadlessGameplayDriver.query_council_assign_receipt_private_v1

            def __init__(self, frame: dict[str, object]) -> None:
                self.endpoint = self
                self.state = NativeProtocolState("offline-fixture:chaplain-council-action-actual4-whole")
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.packet: dict[str, object] = {}
                self.set_frame(frame)

            def set_frame(self, frame: dict[str, object]) -> None:
                # This public semantic snapshot is declared synthetic. Its
                # frame is supplied by the compiled producer's case receipt.
                self.snapshot = {
                    "snapshot_id": f"native:{frame['native_revision']}",
                    "revision": frame["public_revision"], "native_revision": frame["native_revision"],
                    "date_raw": frame["date_raw"], "paused": frame["paused"], "map_ready": frame["map_ready"],
                    "played_character": {"character_id": frame["owner_character_id"], "alive": True},
                    "active_wars": [], "player_armies": [], "history": [],
                    "active_event": None, "pending_character_interaction": None,
                    "diagnostics": {"hello": {
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                    }},
                }

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                test.assertEqual(request["request_id"], self.packet["request_id"])
                self.sent.append(deepcopy(request))
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        def load_packet(filename: str) -> dict[str, object]:
            packet = json.loads((self.args.native_fixtures_dir / filename).read_text(encoding="utf-8"))
            self.assertEqual(packet["type"], "command_result")
            self.assertEqual(packet["protocol_version"], 1)
            self.assertIs(packet["ok"], True)
            return packet

        async def call(server, driver, tool: str, arguments: dict[str, object], packet: dict[str, object]):
            original = deepcopy(packet)
            driver.packet = packet
            request_id = packet["request_id"]
            if tool == ASSIGN_TOOL:
                response = await server.call_tool(tool, arguments)
            else:
                self.assertTrue(request_id.startswith("council-read-"))
                with patch("xar_autoplayer.bridge.council_private_transport_v1.uuid.uuid4",
                           return_value=SimpleNamespace(hex=request_id.removeprefix("council-read-"))):
                    response = await server.call_tool(tool, arguments)
            self.assertFalse(response.is_error, response)
            self.assertEqual(packet, original)
            self.assertIsInstance(response.structured_content, dict)
            return response.structured_content

        for case in cases:
            with self.subTest(case=case["name"]):
                record = {"case": deepcopy(case), "native_packets": {}}
                self.observations.append(record)
                driver = CompiledWholeDriver(case["pre_frame"])
                server = create_server(driver)
                available_tools = {tool.name: tool for tool in await server.list_tools()}
                for tool in (QUERY_TOOL, ASSIGN_TOOL, RESULT_TOOL):
                    self.assertIn(tool, available_tools)
                self.assertIs(available_tools[QUERY_TOOL].annotations.read_only_hint, True)
                self.assertIs(available_tools[RESULT_TOOL].annotations.read_only_hint, True)
                query_packet = load_packet(case["query_file"])
                record["native_packets"]["query"] = deepcopy(query_packet)
                record["fixture_pre_snapshot"] = driver.take_snapshot()
                query = await call(server, driver, QUERY_TOOL, {
                    "expected_revision": driver.snapshot["revision"], "position_key": POSITION,
                }, query_packet)
                record["registered_query"] = deepcopy(query)
                self.assertEqual(query["status"], case.get("expected_query_status", "available"))
                if query["status"] != "available":
                    self.assertIsNone(case.get("ack_file"))
                    record["sent_requests"] = deepcopy(driver.sent)
                    record["ingested_types"] = list(driver.ingested_types)
                    self.assertEqual(len(driver.sent), 1)
                    observed_rejections.add(case["name"])
                    continue
                payload = query["council_composition_candidates"]
                self.assertEqual(payload["position"]["position_key"], POSITION)
                self.assertEqual(query["exact_build"], receipt["exact_build"])
                decision = select_council_candidate_v1(query, position_key=POSITION)
                record["production_decision"] = deepcopy(decision)
                candidate = case["candidate_character_id"]
                self.assertEqual(decision["selected_candidate"]["character_id"], candidate)
                self.assertIn(decision["outcome"], ("ASSIGN_REQUIRED", "REPLACE_REQUIRED"))
                ack_packet = load_packet(case["ack_file"])
                record["native_packets"]["ack"] = deepcopy(ack_packet)
                request = build_assign_councillor_request_v1(
                    payload, candidate_character_id=candidate, request_id=ack_packet["request_id"],
                )
                record["production_request"] = request.as_wire_fields()
                submitted = await call(server, driver, ASSIGN_TOOL, {
                    "query": query, "candidate_character_id": candidate,
                    "expected_revision": driver.snapshot["revision"],
                    "action_request_id": request.request_id,
                }, ack_packet)
                record["registered_submit"] = deepcopy(submitted)
                ack = submitted["council_assign_councillor_ack"]
                self.assertEqual(ack, ack_packet["result"]["council_assign_councillor_ack"])
                self.assertEqual(ack["position_key"], POSITION)
                self.assertEqual(ack["status"], case["expected_ack_status"])
                self.assertEqual(ack["failure"], case["expected_ack_failure"])
                if ack["status"] == "rejected_before_submit":
                    self.assertIs(ack["native_helper_invoked"], False)
                    self.assertIsNone(case.get("receipt_file"))
                    observed_rejections.add(case["name"])
                else:
                    self.assertIs(ack["verification_pending"], True)
                    self.assertIs(ack["queue_acceptance_observed"], False)
                    driver.set_frame(case["post_frame"])
                    record["fixture_independent_post_snapshot"] = driver.take_snapshot()
                    result_packet = load_packet(case["receipt_file"])
                    record["native_packets"]["receipt"] = deepcopy(result_packet)
                    verified = await call(server, driver, RESULT_TOOL, {
                        "pending": submitted, "expected_revision": driver.snapshot["revision"],
                    }, result_packet)
                    record["registered_independent_receipt"] = deepcopy(verified)
                    value = verified["council_assign_councillor_receipt"]
                    self.assertEqual(value, result_packet["result"]["council_assign_councillor_receipt"])
                    self.assertEqual(value["status"], case["expected_receipt_status"])
                    self.assertEqual(value["position_key"], POSITION)
                    if value["status"] == "applied":
                        self.assertEqual(value["incumbent_character_id"], candidate)
                        self.assertIs(value["postcondition_verified"], True)
                        observed_applied_routes.add(ack["route"])
                    else:
                        self.assertIs(value["postcondition_verified"], False)
                        observed_rejections.add(case["name"])
                record["sent_requests"] = deepcopy(driver.sent)
                record["ingested_types"] = list(driver.ingested_types)
                self.assertEqual(driver.ingested_types, ["command_result"] * len(driver.sent))
                self.assertEqual(sum(request["step"] == "private-assign-councillor-v1"
                                     for request in driver.sent), 1)
        self.assertEqual(observed_applied_routes, {"assign_vacant", "replace_incumbent"})
        self.assertTrue(observed_rejections)
        self.evidence.update(applied_routes=sorted(observed_applied_routes),
                             rejected_cases=sorted(observed_rejections))

        # Only the ordinary baseline and its no-op S/C providers are synthetic.
        # The real normal Service reaches the new Chaplain fallback; its
        # Chaplain query still uses the real Driver/transport/protocol reader
        # over the fresh compiled whole packet, which is never renamed S/C.
        normal_case = next(case for case in cases if case["name"] == "occupied-applied")
        normal_packet = load_packet(normal_case["query_file"])
        baseline = {"policy": "explicit-synthetic-normal-baseline",
                    "phase": "life_advance", "selected_step": "life-advance"}
        from xar_autoplayer.bridge.council_composition_candidates_contract import (
            CHANCELLOR_POSITION_KEY, STEWARD_POSITION_KEY,
        )

        class NormalFallbackDriver(CompiledWholeDriver):
            nonwar_only = False

            def __init__(self, *, name: str) -> None:
                super().__init__(normal_case["pre_frame"])
                self.state_dir = self_args.output_dir / ("synthetic-normal-state-" + name)
                self.synthetic_baseline_queries: list[str] = []
                self.synthetic_root_reads = 0
                self.packet = normal_packet

            def capabilities(self) -> dict[str, object]:
                return {"format_version": 1, "backend_id": "explicit-synthetic-driver",
                        "snapshot": True, "action_steps": ["life-advance", "query-army-strengths-v1"],
                        "bridge_capabilities": []}

            def query_council_final_gates_private_v1(self, *, expected_revision: int,
                                                    position_key: str = STEWARD_POSITION_KEY):
                if position_key == POSITION:
                    return super().query_council_final_gates_private_v1(
                        expected_revision=expected_revision, position_key=position_key)
                # Construct explicitly nonmaterial S/C no-op input. It is not
                # a rewritten Chaplain wire or a claim of native S/C evidence.
                self.synthetic_baseline_queries.append(position_key)
                skill = "stewardship" if position_key == STEWARD_POSITION_KEY else "diplomacy"
                holder = 1001 if position_key == STEWARD_POSITION_KEY else 1002
                observation = {
                    "snapshot": {"snapshot_id": self.snapshot["snapshot_id"],
                                 "public_revision": self.snapshot["revision"],
                                 "native_revision": self.snapshot["native_revision"],
                                 "date_raw": self.snapshot["date_raw"], "paused": True},
                    "owner_character_id": self.snapshot["played_character"]["character_id"],
                    "position": {"position_key": position_key, "incumbent_character_id": holder,
                                 "incumbent_main_skill": {"key": skill, "value": 17},
                                 "vacant": False, "action_route": "replace"},
                    "candidate_collection_complete": True, "candidates": [],
                    "readiness": {key: True for key in (
                        "identity_ready", "candidate_collection_ready", "incumbent_ready",
                        "incumbent_main_skill_ready", "candidate_legality_ready", "main_skill_ready",
                        "action_route_ready", "same_frame_ready", "ready")},
                }
                return {"status": "available", "council_composition_candidates": observation,
                        "council_final_gates": {"status": "available", "candidate_count": 0, "rows": []}}

            def execute_step(self, step: str, *, expected_revision: int):
                test.assertEqual(step, "query-campaign-root-context-v1")
                self.synthetic_root_reads += 1
                return {"campaign_root_context": {
                    "status": "available", "player_character_id": 29829,
                    "snapshot_revision": self.snapshot["native_revision"], "date_raw": self.snapshot["date_raw"],
                    "council": {"positions": [
                        {"position_key": STEWARD_POSITION_KEY, "incumbent_character_id": 1001},
                        {"position_key": CHANCELLOR_POSITION_KEY, "incumbent_character_id": 1002},
                        {"position_key": POSITION, "incumbent_character_id": 56513,
                         "task_key": "task_religious_relations", "task_type": "general",
                         "target": None, "frozen": False,
                         "progress": {"kind": "infinite", "current": None, "maximum": None}},
                    ]},
                }}

        self_args = self.args
        normal_driver = NormalFallbackDriver(name="chaplain")
        normal_server = create_server(normal_driver)
        query_nonce = normal_packet["request_id"].removeprefix("council-read-")
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=deepcopy(baseline)), \
                patch("xar_autoplayer.bridge.council_private_transport_v1.uuid.uuid4",
                      return_value=SimpleNamespace(hex=query_nonce)):
            response = await normal_server.call_tool("ck3_plan_turn", {})
        self.assertFalse(response.is_error, response)
        normal_plan = response.structured_content
        self.assertEqual(normal_plan["plan"]["selected_step"], "private-assign-councillor-v1")
        self.assertEqual(normal_plan["plan"]["council_decision"]["position_key"], POSITION)
        self.assertEqual(normal_plan["plan"]["council_decision"]["selected_candidate"]["character_id"],
                         normal_case["candidate_character_id"])
        self.assertEqual(normal_plan["plan"]["council_decision"]["skill_gain"], 12)
        self.assertEqual(normal_driver.synthetic_baseline_queries, [STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY])
        self.assertEqual(len(normal_driver.sent), 1)
        self.observations.append({
            "case": "registered-normal-chaplain-fallback", "registered_normal_plan": deepcopy(normal_plan),
            "fixture_public_snapshot": normal_driver.take_snapshot(),
            "sent_requests": deepcopy(normal_driver.sent),
            "synthetic_noop_baseline_roles": list(normal_driver.synthetic_baseline_queries),
            "synthetic_root_reads": normal_driver.synthetic_root_reads,
            "reused_fresh_native_query_file": normal_case["query_file"],
            "normal_action_executed": False,
        })
        urgent_driver = NormalFallbackDriver(name="war-priority")
        urgent_driver.snapshot["active_wars"] = [{"war_id": 100663329, "casus_belli_key": "claim_cb"}]
        urgent = {"policy": "explicit-synthetic-current-war-baseline", "phase": "native_war_army_query",
                  "selected_step": "query-army-strengths-v1"}
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=urgent):
            response = await create_server(urgent_driver).call_tool("ck3_plan_turn", {})
        self.assertFalse(response.is_error, response)
        self.assertEqual(response.structured_content["plan"]["selected_step"], urgent["selected_step"])
        self.assertEqual(urgent_driver.sent, [])
        self.assertEqual(urgent_driver.synthetic_baseline_queries, [])
        self.assertEqual(urgent_driver.synthetic_root_reads, 0)
        self.evidence["normal_fixture_seams"] = {
            "baseline_chooser": "explicit synthetic choose_one_life_turn life-advance / selected war action",
            "steward_chancellor_inputs": "explicit synthetic no-op providers; no S/C native packet rewritten",
            "root_seat_row": "explicit synthetic current Chaplain seat; no production-live root qualification",
            "chaplain_query": "real Driver/transport/state/normalizer over fresh native query whole file",
            "normal_service_and_consumer": "actual production methods, unmodified by fixture",
            "normal_action_execution": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixtures-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    test = ChaplainCouncilAction12004RegisteredCompound(
        "test_fresh_chaplain_query_typed_action_and_independent_incumbent_receipt")
    test.args, test.observations, test.evidence = args, observations, evidence
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test]))
    successful = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    report = {
        "schema": "xar.ck3.chaplain-council-action-12004-registered-compound/v1",
        "status": "GREEN" if successful else "RED", "test_method": test._testMethodName,
        "test_methods_run": result.testsRun, "source_root": str(args.source_root),
        "native_fixtures_dir": str(args.native_fixtures_dir), "case_attempts": len(observations),
        "compiled_packets_constructed": False, "compiled_packets_repaired": False,
        "nonce_correlation_only": True,
        "readiness_scope": "Fresh actual4 static action/receipt and ordinary fallback fixture; normal-live pending",
        "synthetic_public_snapshot": True, "game_operations": 0, "official_sdk_sessions": 0,
        "native_execution": 0, "old_candidate_six_case_reruns": 0,
        "game_days": 0, "m6_complete": False, "g2_credit": 0,
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors], **evidence,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (("OBSERVED.json", observations), ("RESULT.json", report)):
        with (args.output_dir / name).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
