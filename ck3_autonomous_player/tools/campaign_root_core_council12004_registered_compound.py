"""Consume one new actual4 full-root Council whole through ordinary planning.

SOURCE_NOTRUN. Root supplies the fresh native projection/serializer packet.
Only its outer request ID is correlated. The full root body remains intact.
The normal fixture's chooser, plan-only life-advance capability and empty
Council candidates are explicitly synthetic. No life-advance is submitted;
no candidate, action or independent action receipt is replayed.
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


RECEIPT_SCHEMA = "xar.ck3.root-core-council-12004-native-whole-fixture/v1"
ROOT_STEP = "query-campaign-root-context-v1"
ROOT_TOOL = "ck3_query_campaign_root_context_v1"
CHAPLAIN = "councillor_court_chaplain"
STEWARD = "councillor_steward"
CHANCELLOR = "councillor_chancellor"
CORE_KEYS = (
    CHANCELLOR, CHAPLAIN, "councillor_marshal", "councillor_spymaster", STEWARD,
)


class CampaignRootCoreCouncil12004RegisteredCompound(unittest.IsolatedAsyncioTestCase):
    args: argparse.Namespace
    evidence: dict[str, object]

    async def test_new_native_core_seats_reach_registered_root_and_same_frame_ordinary_chaplain_query(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use the standalone consumer with Root's fresh root packet")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        # Production imports happen only in Root's new selected FIRST run.
        from xar_autoplayer.bridge.campaign_root_context_contract import normalize_campaign_root_context_v1
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.private_council_formal_consumer_v1 import plan_council_private

        receipt_path = self.args.native_fixtures_dir / "native-root-council-receipt.json"
        wire_path = self.args.native_fixtures_dir / "full-root-core-council.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        wire = json.loads(wire_path.read_text(encoding="utf-8"))
        self.evidence.update(native_receipt=deepcopy(receipt), native_wire=deepcopy(wire),
            production_source_files={
                "registration": inspect.getsourcefile(create_server),
                "driver": inspect.getsourcefile(NativeHeadlessGameplayDriver),
                "protocol_state": inspect.getsourcefile(NativeProtocolState),
                "root_contract": inspect.getsourcefile(normalize_campaign_root_context_v1),
                "service": inspect.getsourcefile(GameplayBridgeService),
                "ordinary_consumer": inspect.getsourcefile(plan_council_private),
            })
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(wire["type"], "command_result")
        self.assertEqual(wire["protocol_version"], 1)
        self.assertIs(wire["ok"], True)
        self.assertEqual(wire["request_id"], "root-read-00000000000000000000000000000071")
        native_root = wire["result"]["campaign_root_context"]
        self.assertEqual(native_root["player_character_id"], 29829)
        self.assertEqual(native_root["snapshot_revision"], 9)
        self.assertEqual(native_root["date_raw"], 53222304)
        self.assertEqual(native_root["provenance"]["game_version"], CK3_12004.game_version)
        self.assertEqual(native_root["provenance"]["executable_sha256"].upper(),
                         CK3_12004.executable_sha256.upper())
        test = self

        class WholeRootEndpoint:
            """One real protocol ingestion; fixture Hello/frame are disclosed."""

            def __init__(self) -> None:
                self.sent: list[dict[str, object]] = []
                self.ingestions = 0
                self.correlations: list[dict[str, str]] = []

            def start(self, on_frame, on_disconnect) -> None:
                self.on_frame = on_frame
                self.on_disconnect = on_disconnect
                on_frame({
                    "type": "hello", "protocol_version": 1, "pid": 12004,
                    "connection_generation": 1,
                    "expected_ck3_version": CK3_12004.game_version,
                    "expected_ck3_sha256": CK3_12004.executable_sha256,
                    "capabilities": ["bridge.ping", "game.state.snapshot",
                                     "game.command.query-campaign-root-context-v1"],
                })
                on_frame({
                    "type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": "native:9", "revision": 9,
                    "state": {
                        "date_raw": 53222304, "paused": True, "speed": 0,
                        "map_ready": True,
                        "played_character": {"character_id": 29829, "alive": True},
                        "active_wars": [], "player_armies": [], "history": [],
                        "active_event": None, "pending_character_interaction": None,
                    },
                })

            def send(self, command: dict[str, object], **kwargs) -> None:
                self.sent.append(deepcopy(command))
                if command.get("type") == "ping":
                    self.on_frame({"type": "pong", "protocol_version": 1,
                                   "request_id": command["request_id"]})
                    return
                test.assertEqual(command.get("type"), "execute_step")
                test.assertEqual(command.get("step"), ROOT_STEP)
                test.assertEqual(command.get("expected_revision"), 9)
                test.assertEqual(self.ingestions, 0, "The new root is consumed once")
                response = deepcopy(wire)
                response["request_id"] = command["request_id"]
                test.assertEqual(response["result"], wire["result"])
                self.correlations.append({"producer_request_id": wire["request_id"],
                                          "consumer_request_id": command["request_id"]})
                self.ingestions += 1
                self.on_frame(response)

            def transport_error(self):
                return None

            def close(self) -> None:
                pass

        class OrdinaryRootDriver(NativeHeadlessGameplayDriver):
            # Initial succession bookkeeping is outside this root-seat
            # projection test. No old getter or action is replayed for it.
            retain_succession_expectation_v1 = None
            reconcile_retained_succession_transition_v1 = None

            def capabilities(self) -> dict[str, object]:
                capabilities = super().capabilities()
                # Route the declared synthetic normal baseline. This capability
                # is planning-only; the endpoint permits only the root read.
                capabilities["action_steps"] = sorted(
                    set(capabilities["action_steps"]) | {"life-advance"})
                return capabilities

            def query_council_final_gates_private_v1(self, *, expected_revision: int,
                                                    position_key: str = STEWARD):
                frame = self.take_internal_semantic_snapshot()
                test.assertEqual(expected_revision, frame["revision"])
                self.synthetic_noop_roles.append(position_key)
                # Seat identities come from the one newly normalized root.
                # Skill/candidate inputs below are nonmaterial fixture setup,
                # not another native Council observation or packet repair.
                seat = next(row for row in self.new_root["council"]["positions"]
                            if row["position_key"] == position_key)
                skill = {STEWARD: "stewardship", CHANCELLOR: "diplomacy", CHAPLAIN: "learning"}[position_key]
                holder = seat["incumbent_character_id"]
                payload = {
                    "snapshot": {"snapshot_id": frame["snapshot_id"],
                                 "public_revision": frame["revision"],
                                 "native_revision": frame["native_revision"],
                                 "date_raw": frame["date_raw"], "paused": True},
                    "owner_character_id": 29829,
                    "position": {"position_key": position_key,
                                 "incumbent_character_id": holder,
                                 "incumbent_main_skill": {"key": skill, "value": 0} if holder is not None else None,
                                 "vacant": holder is None,
                                 "action_route": "assign" if holder is None else "replace"},
                    "candidate_collection_complete": True, "candidates": [],
                    "readiness": {key: True for key in (
                        "identity_ready", "candidate_collection_ready", "incumbent_ready",
                        "incumbent_main_skill_ready", "candidate_legality_ready", "main_skill_ready",
                        "action_route_ready", "same_frame_ready", "ready")},
                }
                return {"status": "available", "council_composition_candidates": payload,
                        "council_final_gates": {"status": "available", "candidate_count": 0, "rows": []}}

        endpoint = WholeRootEndpoint()
        driver = OrdinaryRootDriver(endpoint=endpoint, episode_projection="native_campaign",
                                    command_timeout_seconds=1.0,
                                    state_dir=self.args.output_dir / "isolated-driver-state")
        driver.allow_private_council_action = True
        driver.nonwar_only = False
        driver.synthetic_noop_roles = []
        try:
            before = driver.take_internal_semantic_snapshot()
            self.assertIn("life-advance", driver.capabilities()["action_steps"])
            server = create_server(driver)
            tools = {tool.name for tool in await server.list_tools()}
            self.assertIn(ROOT_TOOL, tools)
            self.assertIn("ck3_plan_turn", tools)
            response = await server.call_tool(ROOT_TOOL, {"expected_revision": before["revision"]})
            self.assertFalse(response.is_error, response)
            root_result = response.structured_content
            self.assertIsInstance(root_result, dict)
            self.evidence["registered_root_result"] = deepcopy(root_result)
            root = root_result["campaign_root_context"]
            driver.new_root = root
            self.assertEqual(root, native_root, "The whole native root body survives normalization")
            self.assertEqual(root_result["council"], native_root["council"])
            self.assertEqual(root_result["status"], "available")
            self.assertIs(root["readiness"]["council_ready"], True)
            council = root["council"]
            self.assertEqual(council["status"], "available")
            self.assertEqual(council["coverage_key"], "standard_landed_non_nomadic_core_v1")
            self.assertEqual(council["owner_character_id"], 29829)
            self.assertIs(council["auxiliary_vacancies_complete"], False)
            self.assertEqual(tuple(row["position_key"] for row in council["positions"]), CORE_KEYS)
            seats = {row["position_key"]: row for row in council["positions"]}
            self.assertEqual(seats[CHAPLAIN], {
                "position_key": CHAPLAIN, "incumbent_character_id": 56513,
                "task_key": "task_religious_relations", "task_type": "general",
                "target": None, "frozen": False,
                "progress": {"kind": "infinite", "current": None, "maximum": None},
                # Preserve and check the inherited Native36 observation field.
                "task_owner_monthly_piety_v1": {
                    "status": "unavailable", "value": None,
                    "unavailable_reason": "task_owner_monthly_piety_unavailable",
                },
            })
            self.assertTrue(all(seats[CHANCELLOR][key] is None for key in (
                "incumbent_character_id", "task_key", "task_type", "target", "frozen", "progress")))
            self.assertEqual(seats[STEWARD]["target"], {"kind": "province", "province_id": 77})
            self.assertEqual(seats[STEWARD]["progress"], {
                "kind": "value", "current": {"raw": 500000, "scale": 100000},
                "maximum": {"raw": 2000000, "scale": 100000},
            })
            self.assertEqual(seats["councillor_spymaster"]["target"], {"kind": "character", "character_id": 1005})
            self.assertEqual(seats["councillor_spymaster"]["progress"], {
                "kind": "percentage", "current": {"raw": 2500000, "scale": 100000},
                "maximum": {"raw": 10000000, "scale": 100000},
            })
            history_before_plan = driver._history_snapshot()
            self.assertEqual(len(history_before_plan), 1)
            self.assertEqual(history_before_plan[0]["command"], ROOT_STEP)
            self.assertIs(history_before_plan[0]["ok"], True)
            baseline = {"policy": "explicit-synthetic-root-seat-consumer-baseline",
                        "phase": "life_advance", "selected_step": "life-advance"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline):
                response = await server.call_tool("ck3_plan_turn", {})
            self.assertFalse(response.is_error, response)
            planned = response.structured_content
            self.evidence.update(registered_normal_plan=deepcopy(planned),
                synthetic_empty_candidate_roles=list(driver.synthetic_noop_roles),
                native_ingestions=endpoint.ingestions,
                native_sent_requests=deepcopy(endpoint.sent))
            self.assertEqual(planned["plan"]["selected_step"], "life-advance")
            self.assertEqual(driver.synthetic_noop_roles, [STEWARD, CHANCELLOR, CHAPLAIN])
            self.assertEqual(planned["plan"]["council_decision"]["position_key"], CHAPLAIN)
            self.assertEqual(planned["plan"]["council_job_progress_observation"]["incumbent_character_id"], 56513)
            self.assertEqual(planned["plan"]["council_job_progress_observation"]["task_key"], "task_religious_relations")
            self.assertEqual(planned["plan"]["council_job_progress_observation"]["progress"], seats[CHAPLAIN]["progress"])
            self.assertEqual(driver._history_snapshot(), history_before_plan)
            self.assertEqual(endpoint.ingestions, 1)
            self.assertEqual(sum(row.get("type") == "execute_step" for row in endpoint.sent), 1)
            self.evidence.update(registered_normal_plan=deepcopy(planned),
                same_frame_history_root_reused=True, native_ingestions=endpoint.ingestions,
                native_sent_requests=deepcopy(endpoint.sent), outer_correlations=deepcopy(endpoint.correlations),
                synthetic_empty_candidate_roles=list(driver.synthetic_noop_roles),
                native_body_unchanged=True, registered_mcp_calls=2,
                fixture_seams={
                    "public_frame_hello": "explicit fixture setup for compiled root revision9/date53222304/owner29829",
                    "non_council_native_root_baseline": "declared synthetic by native producer receipt",
                    "normal_chooser": "explicit synthetic life-advance baseline",
                    "normal_routing_capability": "synthetic plan-only life-advance capability; never submitted",
                    "council_queries": "explicit empty candidate/no-op providers; actual seats taken from the new native root",
                    "initial_succession": "unrelated initial succession retain/reconcile hooks disabled in fixture subclass",
                    "root_reader_protocol_strict_service_and_normal_consumer": "production code, unchanged",
                }, action_submissions=0, action_receipt_consumptions=0, candidate_wire_consumptions=0,
                game_or_sdk_used=False, production_live=False, game_days=0, g2_credit=0)
        finally:
            driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixtures-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    CampaignRootCoreCouncil12004RegisteredCompound.args = args
    CampaignRootCoreCouncil12004RegisteredCompound.evidence = {}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CampaignRootCoreCouncil12004RegisteredCompound)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    observed = CampaignRootCoreCouncil12004RegisteredCompound.evidence
    observed.update(schema="xar.ck3.root-core-council-12004-registered-observation/v1",
                    status="GREEN" if passed else "RED", source_root=str(args.source_root),
                    native_fixtures_dir=str(args.native_fixtures_dir), scope="new root-seat fixture only")
    outcome = {"schema": "xar.ck3.root-core-council-12004-registered-result/v1",
               "status": "GREEN" if passed else "RED", "methods": result.testsRun,
               "skipped": len(result.skipped), "failures": len(result.failures), "errors": len(result.errors),
               "readiness": "fixture only; actual root/current normal opportunity pending",
               "game_days": 0, "material_appointment": False, "m6_complete": False, "g2_credit": 0}
    for filename, value in (("OBSERVED.json", observed), ("RESULT.json", outcome)):
        with (args.output_dir / filename).open("x", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
