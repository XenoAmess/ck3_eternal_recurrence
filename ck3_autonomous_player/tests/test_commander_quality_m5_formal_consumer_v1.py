"""One real plan_turn/M5/typed assignment transport compound.

Native query bodies are four retained original R22 whole packets. Only the
endpoint and enclosing protocol/paused war scope are synthetic. The zero
case reaches the actual assignment request, then stops at that offline
transport boundary without producing a native result or readback.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ARMY_ID = 83886367
NATIVE_ARMY_ID = 50331794
PLAYER_ID = 29829
CURRENT_ID = 30000
PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53288448
QUERY_SEQUENCE = 7
EPISODE_RUN_ID = "synthetic-quality-m5-episode"
BASELINE_STEP = None
BASELINE_PHASE = "native_war_counterpolicy_hold"
STOP_MARKER = "synthetic_commander_assignment_transport_stop"
PACKETS = (
    ("quality-current-outside-pool.json", "keep_current", 37, -12),
    ("quality-current-zero.json", "assign_better_candidate", 0, 25),
    ("quality-current-unavailable.json", "current_quality_unavailable", None, None),
    ("quality-candidate-comparison.json", "keep_current", 37, -12),
)
HELPER_RELATIVE = (
    "ck3_autonomous_player/tests/"
    "test_current_commander_native_ai_base_quality_service_12004.py"
)
CONSUMER_RELATIVE = (
    "ck3_autonomous_player/src/xar_autoplayer/commander_quality_formal_consumer_v1.py"
)
REPORT_NAME = "commander-quality-m5-formal-consumer-result.json"
_CONFIG: dict[str, Path | None] | None = None


def _configuration() -> dict[str, Path | None]:
    if _CONFIG is not None:
        return _CONFIG
    native_dir = os.environ.get("XAR_COMMANDER_QUALITY_M5_NATIVE_DIR")
    output_dir = os.environ.get("XAR_COMMANDER_QUALITY_M5_OUTPUT_DIR")
    reuse_report = os.environ.get("XAR_COMMANDER_QUALITY_M5_REUSE_COMPLETED_REPORT")
    return {
        "source_root": Path(os.environ.get(
            "XAR_COMMANDER_QUALITY_M5_SOURCE_ROOT",
            str(Path(__file__).resolve().parents[2]),
        )).resolve(),
        "native_dir": Path(native_dir).resolve() if native_dir else None,
        "output_dir": Path(output_dir).resolve() if output_dir else None,
        "reuse_completed_report": Path(reuse_report).resolve() if reuse_report else None,
    }


def _persist(output_dir: Path | None, report: dict[str, object]) -> None:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / REPORT_NAME).write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8",
        )


def _load_implementation(source_root: Path):
    helper_path = (source_root / HELPER_RELATIVE).resolve()
    spec = importlib.util.spec_from_file_location(
        "commander_quality_m5_retained_fixture_helper", helper_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("retained implementation loader cannot be loaded")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    if Path(helper.__file__).resolve() != helper_path:
        raise RuntimeError("retained helper loaded outside the owned source projection")
    # Only its loader is reused; neither its old method nor driver factory runs.
    modules = helper._load_implementation(source_root)
    for name, relative in (
        ("army_commander_assignment", "bridge/army_commander_assignment.py"),
        ("commander_quality_formal_proposal_v1", "commander_quality_formal_proposal_v1.py"),
        ("commander_quality_formal_consumer_v1", "commander_quality_formal_consumer_v1.py"),
        ("strategy", "strategy.py"),
        ("m5_formal_proposal_collector", "m5_formal_proposal_collector.py"),
    ):
        import_name = f"xar_autoplayer.{name}"
        if name == "army_commander_assignment":
            import_name = "xar_autoplayer.bridge.army_commander_assignment"
        module = importlib.import_module(import_name)
        expected = source_root / f"ck3_autonomous_player/src/xar_autoplayer/{relative}"
        if Path(module.__file__).resolve() != expected.resolve():
            raise RuntimeError(f"formal consumer loaded outside its source projection: {name}")
        modules[name] = module
    return helper, modules


class _OfflineAssignmentTransportStop(RuntimeError):
    """A labeled endpoint stop, not a native assignment result."""


def _driver_for_packet(modules, packet, state_dir: Path):
    native = modules["native_driver"]
    contract = modules["army_commander_candidates"]
    assignment = modules["army_commander_assignment"]
    identity = modules["version_identity"].CK3_12004

    class WholeNativeEndpoint:
        pipe_name = native.DEFAULT_PIPE_NAME

        def __init__(self):
            self.requests = []
            self.control_requests = []
            self.responses = []
            self.assignment_requests = []
            self.on_frame = None
            self.on_disconnect = None

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame
            self.on_disconnect = on_disconnect

        def publish_scope(self):
            self.on_frame({
                "type": "hello", "protocol_version": 1, "pid": 4242,
                "connection_generation": 1,
                "game_version": identity.game_version,
                "executable_sha256": identity.executable_sha256,
                "expected_ck3_version": identity.game_version,
                "expected_ck3_sha256": identity.executable_sha256,
                "capabilities": [
                    "game.state.snapshot", "game.state.active-wars",
                    "game.state.player-armies",
                    "game.command.set-speed-1", "game.command.set-speed-3",
                    "game.command.set-speed-5", "game.command.resume-map",
                    "game.command.pause-map",
                    contract.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                    assignment.ASSIGN_ARMY_COMMANDER_V1_CAPABILITY,
                ],
            })
            # The enclosing war is explicitly synthetic; it never repairs
            # native candidate/current-role rows. Real protocol ingest gives
            # hello revision1 plus three identities => public revision4.
            for occurrence in (1, 2, 3):
                self.on_frame({
                    "type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": f"synthetic-quality-m5-paused-war-scope:{occurrence}",
                    "revision": NATIVE_REVISION,
                    "state": {
                        "paused": True, "speed": 0, "map_ready": True,
                        "date_raw": DATE_RAW,
                        "episode_run_id": EPISODE_RUN_ID,
                        "played_character": {"character_id": PLAYER_ID, "alive": True},
                        "player_armies": [{
                            "army_id": ARMY_ID, "owner_character_id": PLAYER_ID,
                            "controllable": True, "current_province_id": 2669,
                            "in_combat": False, "retreating": False,
                            "tactical_state": "regular", "route_province_ids": [],
                            "move_target_province_id": None,
                        }],
                        "active_wars": [{
                            "war_id": 700, "player_side": "attacker",
                            "player_is_primary_war_leader": True,
                            "player_relative_war_score": 0, "enemy_armies": [],
                            "enemy_primary_default_raise_province_id": None,
                            "war_objective_province_ids": [],
                        }],
                        "active_event": None,
                        "pending_character_interaction": None,
                    },
                })

        def send(self, request):
            if request["type"] == "ping":
                self.control_requests.append(deepcopy(request))
                self.on_frame({
                    "type": "pong", "protocol_version": 1,
                    "request_id": request["request_id"],
                })
                return
            if request["type"] != "execute_step":
                raise RuntimeError(f"unexpected fixture request: {request['type']}")
            self.requests.append(deepcopy(request))
            if assignment.parse_assign_army_commander_v1_step(request["step"]) is not None:
                self.assignment_requests.append(deepcopy(request))
                # No native success/rejection/ACK or readback is synthesized.
                raise _OfflineAssignmentTransportStop(STOP_MARKER)
            if request["step"] != packet["result"]["step"]:
                raise RuntimeError(f"unexpected fixture step: {request['step']}")
            response = deepcopy(packet)
            response["request_id"] = request["request_id"]
            self.responses.append(deepcopy(response))
            self.on_frame(response)

        def close(self):
            if self.on_disconnect is not None:
                self.on_disconnect()

    endpoint = WholeNativeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(
        endpoint=endpoint, state_dir=state_dir, save_dir=state_dir / "saves",
        command_timeout_seconds=1.0, episode_projection="native_campaign",
    )
    # Existing production configuration enables M5. No methods are patched.
    driver.allow_private_m5_joint_collector = True
    endpoint.publish_scope()
    return driver


class CommanderQualityM5FormalConsumerTests(unittest.TestCase):
    def test_registered_plan_turn_quality_and_assignment_transport_compound(self):
        config = _configuration()
        source_root = config["source_root"]
        native_dir = config["native_dir"]
        output_dir = config["output_dir"]
        reuse_report = config["reuse_completed_report"]
        required = [source_root / HELPER_RELATIVE, source_root / CONSUMER_RELATIVE]
        if reuse_report is not None:
            required.append(reuse_report)
        missing = [str(path) for path in required if not path.is_file()]
        if native_dir is None:
            missing.append("--native-dir")
        else:
            missing.extend(str(native_dir / filename) for filename, *_ in PACKETS
                           if not (reuse_report is not None and filename == PACKETS[0][0])
                           and not (native_dir / filename).is_file())
        if missing:
            _persist(output_dir, {
                "status": "NOTRUN", "missing_inputs": missing,
                "test_method_count": 1, "native_packets_consumed": 0,
                "native_producer_invocations": 0, "old_test_invocations": 0,
                "native_assignment_executed": False, "live_validation": False,
                "actual_executed_count": 0, "reused_completed_count": 0,
            })
            print("NOTRUN: owned formal consumer source and four retained native packets are required")
            self.skipTest("NOTRUN: formal whole-query inputs unavailable")

        report = {
            "schema": "commander-quality-m5-formal-consumer-compound-v1",
            "status": "RED", "test_method_count": 1,
            "native_packet_count": 4, "derived_packet_count": 0,
            "actual_executed_count": 0, "reused_completed_count": 0,
            "actual_native_packet_reads": 0, "skiplist": [],
            "reuse_completed_report": str(reuse_report) if reuse_report is not None else None,
            "aggregate_provenance": "Each completed occurrence identifies its original invocation; enclosing scopes may differ",
            "native_producer_invocations": 0, "old_test_invocations": 0,
            "production_driver_methods_patched": False,
            "production_chooser_patched": False,
            "production_state_and_history": True,
            "existing_m5_configuration_enabled": True,
            "fake_boundary": "protocol hello/paused war scope, query nonce, offline assignment transport stop",
            "native_body_rows_replaced": False,
            "native_assignment_result_fabricated": False,
            "native_assignment_executed": False, "native_assignment_verified": False,
            "game_or_sdk_operations": 0, "live_validation": False,
            "full_m5_joint_budget_closed": False, "occurrences": [],
        }
        try:
            if reuse_report is not None:
                prior = json.loads(reuse_report.read_text(encoding="utf-8-sig"))
                retained = [row for row in prior["occurrences"]
                            if row.get("status") == "GREEN"
                            and Path(row["wire"]).name == PACKETS[0][0]]
                self.assertEqual(len(retained), 1)
                completed = deepcopy(retained[0])
                completed.update({
                    "execution": "reused_completed_occurrence",
                    "reuse_source_report": str(reuse_report),
                    "source_report_status": prior["status"],
                    "native_packet_read_in_this_invocation": False,
                    "m5_enclosing_identity_revalidated": False,
                    "scope_provenance": "first02 original scope without the newly added synthetic episode_run_id",
                })
                report["occurrences"].append(completed)
                report["reused_completed_count"] = 1
                report["skiplist"] = [PACKETS[0][0]]
            helper, modules = _load_implementation(source_root)
            from mcp.server.mcpserver.exceptions import ToolError

            consumer = modules["commander_quality_formal_consumer_v1"]
            self.assertIs(modules["service"].plan_commander_quality_formal_v1,
                          consumer.plan_commander_quality_formal_v1)
            report["fixture_helper_path"] = str(Path(helper.__file__).resolve())
            report["loaded_module_paths"] = {
                name: str(Path(module.__file__).resolve()) for name, module in modules.items()
            }
            query_step = modules["army_commander_candidates"].query_army_commander_candidates_v1_step(
                ARMY_ID,
            )
            assignment = modules["army_commander_assignment"]
            canonical_assignment = assignment.assign_army_commander_v1_step(ARMY_ID, 30001)

            async def consume():
                for filename, expected_status, current_quality, gain in PACKETS:
                    if filename in report["skiplist"]:
                        continue
                    report["actual_executed_count"] += 1
                    packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                    report["actual_native_packet_reads"] += 1
                    original = deepcopy(packet)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertIs(packet["ok"], True)
                    envelope = packet["result"]
                    self.assertEqual(envelope["step"], query_step)
                    self.assertIs(envelope["accepted"], True)
                    self.assertIs(envelope["read_only"], True)
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["query_sequence"], QUERY_SEQUENCE)
                    native_candidates = envelope["army_commander_candidates"]
                    assign = expected_status == "assign_better_candidate"
                    unavailable = expected_status == "current_quality_unavailable"

                    with tempfile.TemporaryDirectory(prefix="quality-m5-service-scope-") as temporary:
                        driver = _driver_for_packet(modules, packet, Path(temporary))
                        try:
                            scope = driver.take_snapshot()
                            self.assertEqual(scope["revision"], PUBLIC_REVISION)
                            self.assertEqual(scope["native_revision"], NATIVE_REVISION)
                            self.assertEqual(scope["date_raw"], DATE_RAW)
                            self.assertEqual(scope["episode_run_id"], EPISODE_RUN_ID)
                            self.assertEqual(scope["played_character"]["character_id"], PLAYER_ID)
                            self.assertEqual(scope["active_wars"][0]["player_side"], "attacker")
                            self.assertEqual(scope["active_wars"][0]["enemy_armies"], [])
                            self.assertIsNone(scope["active_wars"][0].get(
                                "enemy_primary_default_raise_province_id",
                            ))
                            self.assertEqual(driver._command_history, [])
                            self.assertTrue(driver.state._raw_state_snapshot_accepted)
                            self.assertIn("life-advance", driver.capabilities()["action_steps"])
                            server = modules["mcp_server"].create_server(driver)
                            registered = await server.list_tools()
                            names = {row.name for row in registered}
                            self.assertIn("ck3_plan_turn", names)
                            self.assertIn("ck3_execute_step", names)
                            response = await server.call_tool("ck3_plan_turn", {})
                            self.assertFalse(getattr(response, "is_error",
                                                     getattr(response, "isError", False)))
                            planned = response.structured_content
                            # Preserve the actual production plan even when a
                            # later field assertion fails in this compound.
                            report["last_wire"] = str(native_dir / filename)
                            report["last_planned"] = deepcopy(planned)
                            _persist(output_dir, report)
                            self.assertIsInstance(planned, dict)
                            self.assertEqual(planned["snapshot_id"], scope["snapshot_id"])
                            self.assertEqual(planned["revision"], PUBLIC_REVISION)
                            plan = planned["plan"]
                            selection = plan["commander_quality_selection"]
                            proposal = selection["proposal"]
                            expected_proposal = {
                                "schema": "xar.ck3.commander-quality-proposal.v1",
                                "policy": "native_base_quality_current_baseline_v1",
                                "status": expected_status,
                                "read_only": True, "scope": "existing_mcp_queried_proposal",
                                "automatic_consumption": False, "assignment_executed": False,
                                "source": "native_ai_base_quality",
                                "army_id": ARMY_ID, "native_carmy_id": NATIVE_ARMY_ID,
                                "owner_character_id": PLAYER_ID,
                                "frame": {
                                    "snapshot_id": scope["snapshot_id"], "revision": PUBLIC_REVISION,
                                    "native_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
                                    "query_sequence": QUERY_SEQUENCE,
                                },
                                "current_commander_character_id": CURRENT_ID,
                                "current_native_ai_base_quality": current_quality,
                                "best_eligible_candidate_character_id": 30001,
                                "best_eligible_candidate_native_ai_base_quality": 25,
                                "quality_gain": gain,
                                "proposed_commander_character_id": 30001 if assign else None,
                                "selected_step": canonical_assignment if assign else None,
                                "unavailable_reason": (
                                    "current_native_ai_base_quality_unavailable" if unavailable else None
                                ),
                            }
                            self.assertEqual(selection, {
                                "schema": "xar.ck3.commander-quality-formal-consumer.v1",
                                "status": expected_status, "formal_action_ready": assign,
                                "automatic_consumption": True, "assignment_executed": False,
                                "selected_step": canonical_assignment if assign else None,
                                "baseline_selected_step": BASELINE_STEP,
                                "proposal": expected_proposal,
                            })
                            self.assertEqual(plan["selected_step"], canonical_assignment if assign else BASELINE_STEP)
                            self.assertEqual(plan["phase"],
                                             "native_commander_quality_assignment" if assign else BASELINE_PHASE)
                            self.assertIs(selection["automatic_consumption"], True)
                            self.assertIs(selection["assignment_executed"], False)
                            m5_observation = plan["m5_joint_wartime_observation"]
                            self.assertEqual(m5_observation["frame"], {
                                "played_character_id": PLAYER_ID,
                                "native_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
                                "snapshot_id": scope["snapshot_id"], "revision": PUBLIC_REVISION,
                                "episode_run_id": EPISODE_RUN_ID,
                            })
                            self.assertIs(m5_observation["read_only"], True)
                            self.assertIs(m5_observation["formal_action_ready"], False)
                            self.assertIsNone(m5_observation["war_cash_resource"])
                            self.assertEqual(len(driver.endpoint.responses), 1)
                            self.assertEqual(driver.endpoint.responses[0]["result"], original["result"])
                            self.assertEqual(packet, original)
                            self.assertEqual(len(driver.endpoint.requests), 1)
                            self.assertEqual(driver.endpoint.requests[0]["step"], query_step)
                            self.assertEqual(driver.endpoint.requests[0]["expected_revision"], NATIVE_REVISION)
                            self.assertEqual(len(driver._command_history), 1)
                            self.assertEqual(driver._command_history[0]["command"], query_step)
                            self.assertIs(driver._command_history[0]["ok"], True)

                            role = native_candidates["current_commander"]
                            quality = role["current_native_ai_base_quality"]
                            pool = native_candidates["candidates"]
                            self.assertEqual(role["character_id"], CURRENT_ID)
                            self.assertEqual(quality["source_character_id"], CURRENT_ID)
                            self.assertEqual(quality["value"], current_quality)
                            best = next(row for row in pool if row["character_id"] == 30001)
                            for key in ("available", "can_assign", "final_eligibility_observable", "quality_observable"):
                                self.assertIs(best[key], True)
                            self.assertEqual(best["native_ai_base_quality"], 25)
                            if filename == "quality-current-outside-pool.json":
                                self.assertNotIn(CURRENT_ID, [row["character_id"] for row in pool])
                                self.assertEqual(quality["status"], "available")
                                self.assertGreater(current_quality, best["native_ai_base_quality"])
                            elif unavailable:
                                self.assertEqual(quality["status"], "unavailable")
                                self.assertIsNone(proposal["current_native_ai_base_quality"])
                                self.assertIsNone(proposal["quality_gain"])
                                self.assertIsNone(selection["selected_step"])
                            elif filename == "quality-candidate-comparison.json":
                                self.assertEqual([row["character_id"] for row in pool], [30000, 30001])
                                self.assertIs(pool[0]["can_assign"], False)
                                self.assertEqual(quality["value"], pool[0]["native_ai_base_quality"])
                                self.assertEqual(role["current_total_martial"]["value"], 17)
                                self.assertEqual(pool[0]["generic_advantage_points"], 9)
                                self.assertNotEqual(quality["value"], role["current_total_martial"]["value"])
                                self.assertNotEqual(quality["value"], pool[0]["generic_advantage_points"])
                            else:
                                self.assertIs(type(quality["value"]), int)
                                self.assertEqual(quality["value"], 0)
                                self.assertEqual(proposal["quality_gain"], 25)

                            action_error = None
                            if assign:
                                self.assertEqual(assignment.parse_assign_army_commander_v1_step(
                                    plan["selected_step"],
                                ), (ARMY_ID, best["character_id"]))
                                with self.assertRaisesRegex(ToolError, STOP_MARKER) as stopped:
                                    await server.call_tool("ck3_execute_step", {
                                        "step": plan["selected_step"], "expected_revision": planned["revision"],
                                    })
                                caught = stopped.exception
                                cause = caught.__cause__
                                action_error = {
                                    "type": f"{type(caught).__module__}.{type(caught).__qualname__}",
                                    "text": str(caught),
                                    "cause": ({
                                        "type": f"{type(cause).__module__}.{type(cause).__qualname__}",
                                        "text": str(cause),
                                    } if cause is not None else None),
                                }
                                self.assertEqual(len(driver.endpoint.assignment_requests), 1)
                                request = driver.endpoint.assignment_requests[0]
                                self.assertEqual(set(request), {
                                    "type", "protocol_version", "request_id", "step", "expected_revision",
                                })
                                self.assertEqual(request["type"], "execute_step")
                                self.assertEqual(request["protocol_version"], 1)
                                self.assertEqual(request["step"], canonical_assignment)
                                self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                                self.assertTrue(request["request_id"])
                                self.assertEqual(len(driver.endpoint.requests), 2)
                                self.assertFalse(any(
                                    row.get("command") == canonical_assignment and row.get("ok") is True
                                    for row in driver._command_history
                                ))
                            else:
                                self.assertEqual(driver.endpoint.assignment_requests, [])
                                self.assertEqual(len(driver.endpoint.requests), 1)
                            # The only response remains the original native query.
                            self.assertEqual(len(driver.endpoint.responses), 1)
                            self.assertEqual(driver.endpoint.responses[0]["result"], original["result"])
                            self.assertEqual(packet, original)
                            report["occurrences"].append({
                                "wire": str(native_dir / filename), "status": "GREEN",
                                "execution": "executed_in_this_invocation",
                                "scope_provenance": "current synthetic paused war scope with required M5 episode_run_id",
                                "native_packet_read_in_this_invocation": True,
                                "selection": selection, "plan_phase": plan["phase"],
                                "selected_step": plan["selected_step"],
                                "native_query_commands": 1,
                                "assignment_transport_requests": 1 if assign else 0,
                                "assignment_result_returned": False,
                                "assignment_transport_exception": action_error,
                                "endpoint_requests": driver.endpoint.requests,
                            })
                        finally:
                            driver.endpoint.close()

            asyncio.run(consume())
            self.assertEqual(len(report["occurrences"]), 4)
            self.assertEqual(report["actual_executed_count"], 4 - report["reused_completed_count"])
            self.assertEqual(report["actual_native_packet_reads"], report["actual_executed_count"])
            self.assertEqual(sum(row["assignment_transport_requests"] for row in report["occurrences"]), 1)
            report["status"] = "GREEN"
            report["readiness"] = "static-ready; full Service selection and offline assignment transport fixture"
        except Exception as error:
            report["failure"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            _persist(output_dir, report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reuse-completed-report", type=Path)
    arguments = parser.parse_args()
    global _CONFIG
    _CONFIG = {
        "source_root": arguments.source_root.resolve(),
        "native_dir": arguments.native_dir.resolve(),
        "output_dir": arguments.output_dir.resolve(),
        "reuse_completed_report": (
            arguments.reuse_completed_report.resolve() if arguments.reuse_completed_report else None
        ),
    }
    suite = unittest.TestSuite([CommanderQualityM5FormalConsumerTests(
        "test_registered_plan_turn_quality_and_assignment_transport_compound",
    )])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
