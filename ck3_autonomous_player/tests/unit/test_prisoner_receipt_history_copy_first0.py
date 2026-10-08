"""One connected FIRST0 for the real retained-release receipt copy path.

Root alone runs this fixture. It reuses one qualified whole native packet as
input, without rerunning its producer or claiming a live latency improvement.
"""
from __future__ import annotations

import asyncio
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, load_native_driver_state_for_resume,
)
from xar_autoplayer.bridge import player_prisoner_collection_private_transport as transport
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer import prisoner_release_receipt_consumer_12004 as receipt
from xar_autoplayer.prisoner_release_formal_consumer import (
    _LEDGER, plan_release_formal, read_release_ledger,
)


class _CountedPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        detached = list(self)
        memo[id(self)] = detached
        return detached


class _ReceiptFixtureService(GameplayBridgeService):
    def _plan_turn_internal(self):
        # Only unrelated campaign arbitration is fixture-selected. The real
        # pending planner, public plan detachment and ordinary typed dispatch
        # remain connected to NativeDriver and the whole transport response.
        snapshot = self.driver.take_internal_semantic_snapshot()
        planned = {"snapshot_id": snapshot["snapshot_id"], "revision": snapshot["revision"],
                   "plan": {"selected_step": "life-advance", "phase": "fixture_idle"}}
        return plan_release_formal(self.driver, planned, snapshot)


class PrisonerReceiptHistoryCopyFirst0Tests(unittest.TestCase):
    def test_one_connected_normal_receipt_avoids_three_history_exports(self):
        packet_path = Path(os.environ["XAR_PRISONER_RECEIPT_HISTORY_COPY_PACKET"])
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        self.assertEqual(set(packet), {"type", "protocol_version", "request_id", "ok", "result"})
        self.assertEqual(packet["type"], "command_result")
        self.assertTrue(packet["ok"])
        wire = packet["result"]
        leaf = wire["prisoner_retained_target_state"]
        self.assertEqual(leaf["custody_state"], "held_by_player")
        self.assertEqual(leaf["build_version"], "1.20.0.4")
        query = "query-player-prisoner-collection-private-v1"
        actor, target = leaf["actor_character_id"], leaf["target_character_id"]
        native, date = leaf["snapshot_revision"], leaf["date_raw"]
        original = {
            "stage": "receipt_pending", "material_result": False,
            "player_character_id": actor, "prisoner_character_id": target,
            "pre_native_revision": native - 1, "pre_date_raw": date - 1,
            "release_query_sequence": 91,
            "release_option_keys": [], "release_option_mask_bits": 0,
            "action_ack": {"status": "submitted_verification_pending",
                           "material_result": False, "request_id": "fixture-original-release"},
        }

        def exercise(*, legacy: bool):
            with tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
                    command_timeout_seconds=.1,
                )
                driver.allow_private_prisoner_collection_query = True
                driver.allow_private_prisoner_ransom_action = True
                snapshot_packet = {
                    "type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": f"native:{native}", "revision": native,
                    "state": {"phase": "map_hud", "date": "synthetic:receipt-copy-first0",
                              "date_raw": date, "speed": 1, "paused": True, "map_ready": True,
                              "history": [], "active_event": None,
                              "pending_character_interaction": None,
                              "played_character": {"character_id": actor, "alive": True},
                              "one_life_settlement": None, "active_wars": [], "player_armies": []},
                }
                endpoint.publish({
                    "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                    "pid": 80808, "session_generation": 0,
                    "game_version": leaf["build_version"],
                    "expected_ck3_version": leaf["build_version"],
                    "executable_sha256": leaf["executable_sha256"],
                    "capabilities": ["game.state.snapshot", "game.command." + query],
                })
                endpoint.publish(snapshot_packet)
                driver.take_internal_semantic_snapshot()
                retained = [{"index": index, "command": f"query-retained-copy-{index}",
                             "ok": True, "result": {"values": _CountedPayload(range(256))}}
                            for index in range(1, 4097)]
                with driver._history_lock:
                    driver._command_history = retained
                    driver._driver_state_dirty = True
                driver._persist_driver_state()
                (state_dir / _LEDGER).write_text(json.dumps({"pending": original}), encoding="utf-8")

                def send(request):
                    if request.get("type") == "ping":
                        return
                    self.assertEqual(request["step"], query)
                    self.assertEqual(request["expected_revision"], native)
                    self.assertEqual(request["release_material_target_character_id"], target)
                    # Preserve every original native field; only correlate the
                    # whole command_result nonce to this fresh transport call.
                    response = copy.deepcopy(packet)
                    response["request_id"] = request["request_id"]
                    endpoint.publish(response)

                endpoint.send_hook = send
                try:
                    with ExitStack() as stack:
                        if legacy:
                            stack.enter_context(mock.patch.object(transport, "_semantic_snapshot",
                                                                  lambda owner: owner.take_snapshot()))
                            stack.enter_context(mock.patch.object(receipt, "_semantic_snapshot",
                                                                  lambda owner: owner.take_snapshot()))
                        else:
                            stack.enter_context(mock.patch.object(driver, "_history_snapshot",
                                side_effect=AssertionError("receipt must not export complete history")))
                        stack.enter_context(mock.patch.object(mcp_server, "GameplayBridgeService",
                                                              _ReceiptFixtureService))
                        server = mcp_server.create_server(driver)
                        _CountedPayload.copies = 0
                        response = asyncio.run(server.call_tool("ck3_auto_turn", {}))
                        self.assertFalse(response.is_error)
                        outcome = response.structured_content
                        copy_count = _CountedPayload.copies
                    self.assertEqual(outcome["selected_step"], receipt.RECEIPT_STEP)
                    self.assertEqual(outcome["status"], "executed")
                    result = outcome["result"]
                    self.assertEqual(result["status"], "pending")
                    self.assertFalse(result["material_result"])
                    self.assertFalse(result["release_causation_observed"])
                    self.assertFalse(result["command_costs_verified"])
                    self.assertEqual(result["source_pending"], original)
                    readback = result["independent_readback"]
                    for key, value in wire.items():
                        self.assertEqual(readback[key], value)
                    requests = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(driver._command_history[-1]["result"], readback)
                    ledger = read_release_ledger(state_dir)
                    self.assertEqual(ledger["pending"]["last_receipt"], result)
                    self.assertIsNone(ledger["resolved"])

                    # Public export and durable state still keep all historical
                    # payloads and the complete new independent readback.
                    public = driver.take_snapshot()
                    self.assertEqual(len(public["native_command_history"]), 4097)
                    public["native_command_history"][0]["result"]["values"][0] = -1
                    self.assertEqual(retained[0]["result"]["values"][0], 0)
                    driver._persist_driver_state()
                    restored = load_native_driver_state_for_resume(
                        driver._native_driver_state_path(), endpoint.pipe_name,
                    )
                    self.assertEqual(restored["command_history"], driver._command_history)

                    # Preserve the existing post-query frame check. This is a
                    # new query on a changed fixture frame, never an action.
                    def drift(request):
                        send(request)
                        changed = copy.deepcopy(snapshot_packet)
                        changed["revision"] = native + 1
                        changed["snapshot_id"] = f"native:{native + 1}"
                        changed["state"]["date_raw"] += 1
                        endpoint.publish(changed)
                    endpoint.send_hook = drift
                    revision = driver.take_internal_semantic_snapshot()["revision"]
                    history_length = len(driver._command_history)
                    with self.assertRaisesRegex(BridgeUnavailableError, "crossed its paused frame"):
                        driver.query_player_prisoner_collection_private_v1(
                            expected_revision=revision, release_material_target_character_id=target)
                    self.assertEqual(len(driver._command_history), history_length)
                    return outcome, ledger, copy_count
                finally:
                    driver.close()

        baseline, baseline_ledger, baseline_copies = exercise(legacy=True)
        actual, actual_ledger, actual_copies = exercise(legacy=False)
        self.assertEqual(actual, baseline)
        self.assertEqual(actual_ledger, baseline_ledger)
        self.assertEqual(baseline_copies, 3 * 4096)
        self.assertEqual(actual_copies, 0)
        fallback_frame = {"snapshot_id": "offline", "native_command_history": [{"index": 1}]}
        fallback = SimpleNamespace(take_snapshot=lambda: fallback_frame)
        self.assertIs(transport._semantic_snapshot(fallback), fallback_frame)
        output = os.environ.get("XAR_PRISONER_RECEIPT_HISTORY_COPY_OUTPUT")
        if output:
            with Path(output).open("x", encoding="utf-8") as handle:
                json.dump({"status": "GREEN", "source_packet": str(packet_path),
                           "normal_receipt_baseline_history_payload_copies": baseline_copies,
                           "normal_receipt_optimized_history_payload_copies": actual_copies,
                           "retained_history_rows": 4096, "whole_query_result_retained": True,
                           "public_export_complete": True, "durable_history_complete": True,
                           "post_query_frame_drift_rejected": True,
                           "legacy_reader_fallback_preserved": True,
                           "native_producer_reruns": 0, "live_latency_claimed": False}, handle, indent=2)
                handle.write("\n")


if __name__ == "__main__":
    unittest.main()
