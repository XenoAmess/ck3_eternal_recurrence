"""SOURCE_NOTRUN: six ordered cases through the registered selected Finish MCP.

Root supplies one new actual4 native wholeproducer directory via
XAR_SWAY_STOP_12004_PACKET_DIR (or its manifest path via
XAR_SWAY_STOP_12004_WIRE_MANIFEST). Its five Stop/completion packet bodies are
unchanged except request/action correlation. Hello, paused world, current
target/opinion baselines and ordinary time advancement are synthetic fixture
context. This compound makes no live or native outcome-cause claim.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT.parent / "tools"),
               str(ROOT.parent / "ck3_workshop_mcp" / "src")]

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger


ACTOR, TARGET, INSTANCE, GENERATION, DATE, NATIVE_REVISION = (
    29829, 34333, 134217986, 8, 53288448, 19)
FINISH = "ck3_finish_active_scheme_sway_private_v1"
COMPLETION = "ck3_query_active_scheme_sway_completion_private_v1"
OPINION = "ck3_query_active_scheme_sway_outcome_opinion_private_v1"
COMPLETION_STEP = "query-sway-completion-v1-private"
OPINION_STEP = "query-sway-outcome-opinion-v1-private"
TARGET_PREFIX = "query-active-scheme-sway-target-v1-private-"
ROLES = ("stop_ack", "current", "terminated", "reused", "purged")


def _load_packets():
    explicit = os.environ.get("XAR_SWAY_STOP_12004_WIRE_MANIFEST")
    path = (Path(explicit) if explicit else
            Path(os.environ["XAR_SWAY_STOP_12004_PACKET_DIR"]) / "manifest.json")
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    files = {role: manifest["packets"][role] for role in ROLES}
    packets = {
        role: json.loads((path.parent / files[role]).read_text(
            encoding="utf-8-sig"))
        for role in ROLES
    }
    return path, packets


def _synthetic_read_packet(step: str, field: str, body: dict) -> dict:
    return {
        "type": "command_result", "protocol_version": 1, "request_id": "synthetic-baseline",
        "ok": True, "result": {
            "step": step, "accepted": True, "status": "available",
            "private_build": True, "read_only": True, "advertised": False,
            "backend_id": "native-headless", field: body,
        },
    }


class WholePacketSelectedStopDriver:
    """Real production methods and protocol cache; fixture endpoint/context only."""

    command_timeout_seconds = 30.0
    allow_private_active_scheme_sway_query = True
    allow_private_active_scheme_sway_action = True
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    query_active_scheme_sway_target_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_target_private_v1)
    query_active_scheme_sway_completion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_completion_private_v1)
    query_active_scheme_sway_outcome_opinion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_outcome_opinion_private_v1)
    stop_active_scheme_sway_private_v1 = (
        NativeHeadlessGameplayDriver.stop_active_scheme_sway_private_v1)

    def __init__(self, state_dir: Path, packets: dict, trace: list, case="current"):
        self.state_dir = state_dir
        self.packets = deepcopy(packets)
        self.trace = trace
        self.case = case
        self.endpoint = self
        self.state = NativeProtocolState("offline-selected-sway-stop-whole-packet")
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        })
        self._snapshot(NATIVE_REVISION, DATE)

    def _snapshot(self, revision: int, date: int):
        assert self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{revision}", "revision": revision,
            "state": {
                "date_raw": date, "speed": 1, "paused": True, "map_ready": True,
                "played_character": {"character_id": ACTOR, "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [],
                "player_armies": [], "history": [],
            },
        }) == "state_snapshot"

    def take_snapshot(self):
        return self.state.semantic_snapshot()

    def take_snapshot_without_native_command_history(self):
        return self.take_snapshot()

    def _target_packet(self):
        # The unrelated active scheme is deliberately outside the selected ID.
        return _synthetic_read_packet(TARGET_PREFIX + str(TARGET), "active_scheme_sway", {
            "schema": "active-scheme-sway-private-read-v1",
            "snapshot_revision": NATIVE_REVISION, "capture_epoch": 10,
            "container_generation": 20, "date_raw": DATE,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "target_opinion_of_actor": 61, "active_scheme_count": 2,
            "matching_sway_active": True, "native_complete_can_send": False,
            "native_legal_now": False, "native_failure_classification": "",
            "active_sway_instances": [{
                "scheme_instance_id": INSTANCE, "scheme_instance_generation": GENERATION,
                "target_character_id": TARGET, "progress": 32, "progress_goal": 355,
                "is_exposed": False, "is_frozen": False,
            }],
        })

    def _opinion_packet(self):
        return _synthetic_read_packet(OPINION_STEP, "sway_outcome_opinion", {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "build": CK3_12004.game_version,
            "available": True, "unavailable_reason": "",
            "snapshot_revision": NATIVE_REVISION, "date_raw": DATE,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "target_opinion_of_actor": 61,
            "scheme_sway_opinion": {"observed": True, "present": True, "value": 45},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        })

    def send(self, request):
        assert request["expected_revision"] == NATIVE_REVISION
        step = request["step"]
        if step == self.packets["stop_ack"]["result"]["step"]:
            role = "stop_ack"
            pending = read_sway_ledger(self.state_dir)["resolved"]["stop_intervention"]
            assert pending["action_id"] == request["action_id"]
            assert pending["status"] == "stop_submission_unresolved"
            assert request["actor_character_id"] == ACTOR
            assert request["target_character_id"] == TARGET
            assert request["scheme_instance_id"] == INSTANCE
            assert request["scheme_instance_generation"] == GENERATION
            packet = deepcopy(self.packets[role])
            # UUID correlation changes no command fact or terminal observation.
            packet["result"]["sway_stop"]["action_id"] = request["action_id"]
        elif step == COMPLETION_STEP:
            role = self.case
            assert request["actor_character_id"] == ACTOR
            assert request["target_character_id"] == TARGET
            assert request["scheme_instance_id"] == INSTANCE
            packet = deepcopy(self.packets[role])
        elif step == OPINION_STEP:
            role, packet = "synthetic_opinion", self._opinion_packet()
        elif step == TARGET_PREFIX + str(TARGET):
            role, packet = "synthetic_target", self._target_packet()
        else:
            raise AssertionError(f"unexpected operation {step}; no original Start is permitted")
        packet["request_id"] = request["request_id"]
        assert self.state.ingest(packet) == "command_result"
        self.trace.append({"role": role, "request": deepcopy(request)})

    def execute_step(self, step, *, expected_revision):
        before = self.take_snapshot()
        assert step == "life-advance" and expected_revision == before["revision"]
        self._snapshot(before["native_revision"] + 1, before["date_raw"] + 24)
        self.trace.append({"role": "ordinary_turn", "step": step})
        return {"status": "completed", "step": step}


class SelectedStopSoleCompoundTests(unittest.IsolatedAsyncioTestCase):
    async def test_six_cases_pending_recovery_and_normal_turn(self):
        from mcp import Client

        manifest_path, packets = _load_packets()
        originals = deepcopy(packets)
        native_ack = packets["stop_ack"]["result"]["sway_stop"]
        self.assertEqual(native_ack["snapshot_revision"], NATIVE_REVISION)
        self.assertEqual(native_ack["date_raw"], DATE)
        self.assertEqual(native_ack["scheme_instance_id"], INSTANCE)
        self.assertEqual(native_ack["scheme_instance_generation"], GENERATION)
        self.assertFalse(native_ack["postcondition_verified"])
        self.assertFalse(native_ack["terminal_observed"])
        outputs, trace = {}, []
        original = {
            "status": "applied", "postcondition_verified": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "action_id": "sway-original", "post_native_revision": NATIVE_REVISION - 1,
            "post_date_raw": DATE - 24, "next_turn_consumed": True,
            "native_receipt": {"scheme_instance_id": INSTANCE,
                               "scheme_instance_generation": GENERATION},
        }
        with tempfile.TemporaryDirectory(prefix="xar-sway-stop-compound-") as temporary:
            state_dir = Path(temporary)
            (state_dir / LEDGER_FILE).write_text(json.dumps({
                "schema": SCHEMA, "pending": None, "resolved": original,
            }), encoding="utf-8")
            driver = WholePacketSelectedStopDriver(state_dir, packets, trace)

            async def call(client, name, arguments):
                response = await client.call_tool(name, arguments)
                self.assertFalse(response.is_error, response.content)
                return response.structured_content

            def selected_arguments(current):
                return {"expected_revision": current.take_snapshot()["revision"],
                        "target_character_id": TARGET, "scheme_instance_id": INSTANCE,
                        "scheme_instance_generation": GENERATION}

            def planned_turn(service):
                return {"revision": service.driver.take_snapshot()["revision"],
                        "plan": {"selected_step": "life-advance"}}

            with patch.object(GameplayBridgeService, "plan_turn", planned_turn):
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertIn(FINISH, tools)
                    self.assertTrue(tools[COMPLETION].annotations.read_only_hint)
                    self.assertTrue(tools[OPINION].annotations.read_only_hint)

                    # Case1: existing query005/query006 stage current facts, with no Stop.
                    args = selected_arguments(driver)
                    current = await call(client, COMPLETION, {
                        key: value for key, value in args.items()
                        if key != "scheme_instance_generation"})
                    opinion = await call(client, OPINION, {
                        "expected_revision": args["expected_revision"],
                        "target_character_id": TARGET})
                    self.assertEqual(current["native_status_raw"], 0)
                    self.assertFalse(current["native_terminal_state_observed"])
                    self.assertEqual(opinion["scheme_sway_opinion"]["value"], 45)
                    self.assertNotIn("stop_ack", [row["role"] for row in trace])
                    self.assertNotIn("stop_intervention", read_sway_ledger(state_dir)["resolved"])
                    outputs["1_current_queries_read_only"] = current

                    # Case2: explicit selected Finish performs one Stop, then an independent read.
                    queued = await call(client, FINISH, args)
                    self.assertEqual(queued["status"], "stop_postcondition_pending")
                    self.assertFalse(queued["postcondition_verified"])
                    self.assertFalse(queued["ack"]["terminal_observed"])
                    self.assertEqual(queued["independent_instance_observation"]["native_status_raw"], 0)
                    self.assertEqual([row["role"] for row in trace].count("stop_ack"), 1)
                    outputs["2_stop_ack_pending_only"] = queued

                    # Case3: status0 recovery reads only; it does not resubmit.
                    driver.case = "current"
                    active = await call(client, FINISH, args)
                    self.assertEqual(active["status"], "stop_postcondition_pending")
                    self.assertFalse(active["postcondition_verified"])
                    outputs["3_exact_current_still_pending"] = active

                    # Case4: purged storage gives no terminal credit.
                    driver.case = "purged"
                    purged = await call(client, FINISH, args)
                    self.assertFalse(purged["postcondition_verified"])
                    self.assertFalse(purged["independent_instance_observation"]["instance_present"])
                    outputs["4_purged_not_terminal"] = purged

                    # Case5: slot reuse gives no terminal credit and no second action.
                    driver.case = "reused"
                    reused = await call(client, FINISH, args)
                    self.assertFalse(reused["postcondition_verified"])
                    self.assertTrue(reused["independent_instance_observation"]["storage_slot_reused"])
                    outputs["5_reused_not_terminal"] = reused
                    self.assertEqual([row["role"] for row in trace].count("stop_ack"), 1)
                    self.assertFalse(read_sway_ledger(state_dir)["resolved"][
                        "terminal_intervention"]["instance_terminal_outcome_observed"])

                # Case6: cold client reads exact retained status1, then the ordinary turn consumes it.
                cold_driver = WholePacketSelectedStopDriver(state_dir, packets, trace, "terminated")
                async with Client(create_server(cold_driver)) as cold:
                    terminal = await call(cold, FINISH, selected_arguments(cold_driver))
                    self.assertEqual(terminal["status"], "terminal_observed_after_stop_request")
                    self.assertTrue(terminal["postcondition_verified"])
                    self.assertFalse(terminal["terminal_cause_observed"])
                    self.assertEqual(terminal["terminal_cause"], "unknown")
                    self.assertEqual([row["role"] for row in trace].count("stop_ack"), 1)
                    await call(cold, OPINION, {
                        "expected_revision": cold_driver.take_snapshot()["revision"],
                        "target_character_id": TARGET})
                    outcome = await call(cold, "ck3_auto_turn", {})
                    retained = outcome["sway_following_turn"]
                    self.assertEqual(retained["action_id"], original["action_id"])
                    self.assertEqual(retained["native_receipt"], original["native_receipt"])
                    for key in ("stop_intervention", "terminal_intervention", "material_intervention"):
                        self.assertTrue(retained[key]["next_turn_consumed"])
                    self.assertEqual(retained["material_intervention"]["scheme_sway_opinion"]["value"], 45)
                    self.assertEqual(retained["terminal_intervention"]["terminal_cause"], "unknown")
                    repeated = await call(cold, FINISH, selected_arguments(cold_driver))
                    self.assertEqual(repeated["status"], "already_terminal_observed")
                    self.assertNotIn("sway_following_turn", await call(cold, "ck3_auto_turn", {}))
                    outputs["6_cold_terminal_and_ordinary_turn"] = retained
            self.assertIsNone(read_sway_ledger(state_dir)["pending"])
            self.assertEqual(driver.packets, originals)
            self.assertEqual(cold_driver.packets, originals)
        self.assertEqual(packets, originals)
        self.assertEqual([row["role"] for row in trace].count("stop_ack"), 1)
        self.assertEqual(len(outputs), 6)
        output_path = os.environ.get("XAR_SWAY_STOP_12004_CONSUMER_OUTPUT")
        if output_path:
            Path(output_path).write_text(json.dumps({
                "qualification": "offline registered-MCP consumer; synthetic context; not live",
                "source_manifest": str(manifest_path), "compound_cases": 6,
                "new_native_packet_roles": list(ROLES), "native_stop_submit_calls": 1,
                "native_packet_changes": "request_id and Stop action_id correlation only",
                "synthetic_context": ["hello", "world", "target", "opinion", "ordinary_turn"],
                "terminal_cause": "unknown", "outputs": outputs, "trace": trace,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
