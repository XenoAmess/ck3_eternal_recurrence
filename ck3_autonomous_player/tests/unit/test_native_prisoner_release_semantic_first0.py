"""FIRST0: normal release dispatch reads current frames without transcript copies.

All offer amounts and source identities below are synthetic offline inputs.
This test grants no production release/freedom or gameplay outcome credit.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, load_native_driver_state_for_resume
from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import RELEASE_COST_KEYS_12003, RELEASE_OPTION_KEYS_12003
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.prisoner_release_formal_consumer import _observed_choice, read_release_ledger


class NativePrisonerReleaseSemanticFirst0Tests(unittest.TestCase):
    def test_first0_normal_release_preserves_current_offer_and_complete_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                state_dir=Path(temporary), command_timeout_seconds=0.1)
            driver.allow_private_prisoner_ransom_action = True
            hello = _hello("game.state.snapshot")
            hello.update(expected_ck3_version="1.20.0.4",
                expected_ck3_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")
            endpoint.publish(hello)
            endpoint.publish(_snapshot(40, played_character={"character_id": 29829, "alive": True},
                active_wars=[], player_armies=[]))
            before = driver.take_internal_semantic_snapshot()
            history = [{"index": index, "command": "query-frozen-release-first0-" + str(index),
                "ok": True, "result": {"retained_values": list(range(16))}}
                for index in range(1, 257)]
            with driver._history_lock:
                driver._command_history = copy.deepcopy(history)
                driver._driver_state_dirty = True
            driver._persist_driver_state()

            preview = {
                "private_build": True, "read_only": True, "advertised": False,
                "action_surface_present": False, "status": "available",
                "snapshot_id": "native:40", "public_revision": 40, "native_revision": 40,
                "proof_epoch": 7, "date_raw": before["date_raw"],
                "definition": {"canonical_key": "release_from_prison_interaction",
                    "deterministic_key_hash": 123, "runtime_ordinal": 2},
                "payload_shape": "two_role_all_release_options_off",
                "roles": {"actor_character_id": 29829, "recipient_character_id": 34486},
                "unconditional_prisoner_release": True, "can_send": True,
                "costs": {"raw_scale": 100000, "payer_role": "actor", "application_timing": "on_send",
                    "entries": [{"resource_key": key, "raw": 0} for key in RELEASE_COST_KEYS_12003]},
                "acceptance": {"kind": "auto_accept", "auto_accept": True, "would_accept_now": True},
                "readiness": {key: True for key in ("definition_ready", "actor_ready", "recipient_ready",
                    "finalized_context_ready", "can_send_ready", "costs_ready", "acceptance_ready", "same_frame_ready")},
                "option_keys": list(RELEASE_OPTION_KEYS_12003), "selected_option_mask_bits": 0,
                "puppet_or_actor_character_id": 29829,
            }
            collection = {"step": "query-player-prisoner-collection-private-v1", "status": "available",
                "snapshot_revision": 40, "query_sequence": 7, "observation_revision": 7,
                "player_prisoner_collection": {"status": "available", "played_character_id": 29829,
                    "date_raw": before["date_raw"], "collection_complete": True, "prisoners": [{
                        "source_ordinal": 0, "prisoner_character_id": 34486,
                        "collection_owner_character_id": 29829, "jailer_character_id": 29829,
                        "custody_relation_verified": True, "unconditional_release_preview": preview,
                        "ransom_quote_preview": {"status": "unavailable"}}]}}
            choice, observation = _observed_choice(before, collection, [])
            self.assertEqual(observation["status"], "actionable")
            planned = {"snapshot_id": before["snapshot_id"], "revision": before["revision"],
                "plan": {"selected_step": "submit-player-prisoner-release-v1",
                    "prisoner_release_choice": choice, "prisoner_release_war_reads": []}}
            submitted = []

            def answer(frame):
                if frame.get("type") != "execute_step":
                    return
                self.assertEqual(frame["step"], "submit-player-prisoner-release-private-v1")
                self.assertEqual(frame["expected_revision"], 40)
                self.assertEqual(frame["prisoner_character_id"], 34486)
                self.assertEqual(frame["release_query_sequence"], 7)
                self.assertEqual(frame["release_option_mask_bits"], 0)
                submitted.append(copy.deepcopy(frame))
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": True,
                    "result": {"step": frame["step"], "accepted": True,
                        "status": "submitted_verification_pending"}})

            endpoint.send_hook = answer
            service = GameplayBridgeService(driver)
            with mock.patch.object(service, "plan_turn", return_value=planned), \
                 mock.patch("xar_autoplayer.prisoner_release_formal_consumer._fresh_private_pump") as pump, \
                 mock.patch.object(driver, "take_internal_semantic_snapshot",
                    wraps=driver.take_internal_semantic_snapshot) as semantic, \
                 mock.patch.object(driver, "_history_snapshot",
                    side_effect=AssertionError("FIRST0 normal release must not export all history")) as copies, \
                 mock.patch.object(driver, "_encode_driver_state_locked",
                    side_effect=AssertionError("this typed pending-only submit does not write Driver history")) as encodes:
                outcome = service.auto_turn()
            self.assertEqual(len(submitted), 1)
            self.assertEqual(semantic.call_count, 2)
            self.assertEqual((copies.call_count, encodes.call_count), (0, 0))
            pump.assert_called_once_with(driver, before["date_raw"])
            self.assertEqual(outcome["status"], "executed")
            pending = outcome["result"]
            self.assertEqual(pending["status"], "submitted_verification_pending")
            self.assertIs(pending["material_result"], False)
            self.assertEqual(pending["pre_native_revision"], 40)
            self.assertEqual(pending["pre_date_raw"], before["date_raw"])
            self.assertEqual(pending["costs"], preview["costs"])
            self.assertEqual(pending["acceptance"], preview["acceptance"])
            self.assertEqual(read_release_ledger(driver.state_dir)["pending"], pending)
            self.assertEqual(driver._command_history, history)
            public = driver.take_snapshot()
            self.assertEqual(public["native_command_history"], history)
            public["native_command_history"][0]["result"]["retained_values"].append(-1)
            self.assertEqual(driver._command_history, history)
            driver._persist_driver_state()
            saved = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
            restored = load_native_driver_state_for_resume(driver._native_driver_state_path(), endpoint.pipe_name)
            self.assertEqual(saved["command_history"], history)
            self.assertEqual(restored["command_history"], history)
            driver.close()


if __name__ == "__main__":
    unittest.main()
