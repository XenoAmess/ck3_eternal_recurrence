"""Production Select/primitive paths with memory transport; no game callbacks."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, NativeNamedPipeServer, _NativeCommandRejectedError,
)
from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
from xar_autoplayer.bridge.ingame_decision_item_action_contract import SELECT_STEP
from xar_autoplayer.bridge.ingame_decision_predispatch_contract import ERROR
from test_ingame_decision_item_actions import SyntheticDriver, KEY, frame


def rejection(request):
    expected = {"native_revision": request["expected_revision"], "game_pid": request["expected_game_pid"],
                "connection_generation": request["expected_connection_generation"],
                "played_character_id": request["expected_player_character_id"]}
    previous = {"type": "state_snapshot", "protocol_version": 1, "revision": request["expected_revision"],
                "state": {"date_raw": 1234, "speed": 0, "paused": True, "local_player_id": 0}}
    current = deepcopy(previous)
    current["state"]["local_player_id"] = 1
    return {"type": "command_result", "protocol_version": 1, "request_id": request["request_id"],
            "ok": False, "error": ERROR, "decision_action_pre_dispatch_rejection_v1": {
                "schema": "ck3-decision-action-pre-dispatch-rejection-v1",
                "guard_source_id": "ingame_decision_item_action_admission_v1",
                "dispatch_stage": "before_main_thread_submit", "submitted": False, "dispatch_invoked": False,
                "request_id": request["request_id"], "step": SELECT_STEP, "decision_key": KEY,
                "failed_predicates": ["snapshot_equal"], "expected": expected, "actual": deepcopy(expected),
                "previous_snapshot_available": True, "snapshot_read_attempted": True, "snapshot_read_ok": True,
                "snapshot_equal": False, "map_ready": True, "paused": True,
                "has_played_character": True, "played_character_alive": True,
                "current_snapshot": current, "previous_snapshot": previous,
                "snapshot_differing_fields": ["player_id"]}}


class MemorySelect(SyntheticDriver):
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step
    _verify_idempotent_map_control_postcondition = NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition

    def __init__(self, directory, mutate=None):
        super().__init__(directory)
        self._request_sequence = 0
        self.command_timeout_seconds = .1
        self.packets = []
        self.reply = None
        self.mutate = mutate
        self.endpoint = SimpleNamespace(send=self.send)
        self.state = SimpleNamespace(wait_for_command_result=lambda request_id, timeout: deepcopy(self.reply))

    def send(self, request):
        fake_pipe = SimpleNamespace(_write_lock=threading.Lock(), _current_handle=lambda: 1)
        with patch("xar_autoplayer.bridge.native_driver._write_all",
                   side_effect=lambda handle, packet: self.packets.append(bytes(packet)) or True):
            NativeNamedPipeServer.send(fake_pipe, request)
        self.reply = rejection(json.loads(self.packets[-1][4:]))
        if self.mutate:
            self.mutate(self.reply)


class PreDispatchSelectTests(unittest.TestCase):
    def directory(self):
        parent = os.environ.get("XAR_WHITE_DECISION_ACTION_TEST_ARTIFACTS")
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="pre-submit-select-", dir=parent))

    def rejected(self, mutate=None):
        driver = MemorySelect(self.directory(), mutate)
        with self.assertRaises(_NativeCommandRejectedError) as raised:
            driver.select_ingame_decision_item_v1(KEY, expected_revision=1)
        return driver, raised.exception

    def later(self, driver, **changes):
        next_frame = frame()
        next_frame.update(revision=2, native_revision=8)
        for key, value in changes.items():
            if key == "generation":
                next_frame["diagnostics"]["connection_generation"] = value
            else:
                next_frame[key] = value
        return SyntheticDriver(driver.directory, source_frame=next_frame)

    def test_actual_encoder_primitive_and_select_preserve_received_error_without_success(self):
        driver, error = self.rejected()
        self.assertEqual(len(driver.packets), 1)
        packet = driver.packets[0]
        self.assertEqual(struct.unpack("<I", packet[:4])[0], len(packet) - 4)
        request = json.loads(packet[4:])
        self.assertEqual(request["expected_revision"], 7)
        self.assertEqual(error.native_request_frame, request)
        self.assertEqual(error.native_command_result_frame, driver.reply)
        claim = next((driver.directory / "ingame-decision-item-actions").glob("*.claim.json"))
        original = claim.read_bytes()
        stored = json.loads(claim.with_suffix(".error.json").read_bytes())
        self.assertEqual(stored["request"], request)
        self.assertEqual(stored["native_command_result"], driver.reply)
        self.assertEqual(stored["claim_sha256"], hashlib.sha256(original).hexdigest())
        self.assertTrue(claim.with_suffix(".rejected-before-dispatch.json").is_file())
        self.assertFalse(claim.with_suffix(".result.json").exists())
        self.assertFalse(claim.with_suffix(".verified.json").exists())
        self.assertEqual(json.loads(original)["status"], "claimed_result_unknown_no_retry")
        self.assertIsNone(driver.records[-1][1]["result"]["raw"])

    def test_only_later_public_and_native_revision_same_binding_can_make_new_explicit_select(self):
        driver, _ = self.rejected()
        directory = driver.directory / "ingame-decision-item-actions"
        originals = {p: p.read_bytes() for p in directory.iterdir()}
        for changes in ({"revision": 1}, {"native_revision": 7}, {"generation": 2},
                        {"date_raw": 1235}, {"episode_run_id": "another-episode"}):
            later = self.later(driver, **changes)
            # Another episode is a distinct semantic identity under the old
            # contract, so exercise the resolver without switching identity.
            if "episode_run_id" in changes:
                from xar_autoplayer.bridge.ingame_decision_predispatch_contract import allows_later_select
                claim = next(directory.glob("*.claim.json"))
                value = json.loads(claim.read_bytes())
                identity = {**value["action_identity"], "public_revision": 2}
                self.assertFalse(allows_later_select(claim, value, identity, opening_binding(later.frame)))
                continue
            with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
                later.select_ingame_decision_item_v1(KEY, expected_revision=later.frame["revision"])
            self.assertEqual(later.submissions, [])
        later = self.later(driver)
        self.assertEqual(later.submissions, [])
        result = later.select_ingame_decision_item_v1(KEY, expected_revision=2)
        self.assertTrue(result["postcondition_verified"])
        self.assertEqual(len(later.submissions), 1)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)

    def test_unknown_after_submit_foreign_or_malformed_errors_are_preserved_but_stay_locked(self):
        mutations = [
            lambda r: r.pop("decision_action_pre_dispatch_rejection_v1"),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(dispatch_stage="after_main_thread_submit"),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(submitted=True),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(dispatch_invoked=True),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(request_id="foreign"),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(step="confirm-ingame-decision-item-v1"),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(guard_source_id="another-guard"),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"]["expected"].update(native_revision=8),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(snapshot_equal=True),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(failed_predicates=["unknown"]),
            lambda r: r["decision_action_pre_dispatch_rejection_v1"].update(submitted=0),
            lambda r: r.update(error="owner_thread_timeout_after_submit"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                driver, _ = self.rejected(mutation)
                claim = next((driver.directory / "ingame-decision-item-actions").glob("*.claim.json"))
                self.assertTrue(claim.with_suffix(".error.json").is_file())
                self.assertFalse(claim.with_suffix(".rejected-before-dispatch.json").exists())
                later = self.later(driver)
                with self.assertRaisesRegex(BridgeUnavailableError, "unresolved"):
                    later.select_ingame_decision_item_v1(KEY, expected_revision=2)
                self.assertEqual(later.submissions, [])

    def test_timeout_old_error_confirm_and_tampered_evidence_never_resolve_unknown(self):
        for error in (TimeoutError("lost ACK"), _NativeCommandRejectedError(ERROR)):
            driver = SyntheticDriver(self.directory(), action_error=error)
            with self.assertRaises(type(error)):
                driver.select_ingame_decision_item_v1(KEY)
            later = self.later(driver)
            with self.assertRaisesRegex(BridgeUnavailableError, "unresolved"):
                later.select_ingame_decision_item_v1(KEY, expected_revision=2)
            self.assertEqual(later.submissions, [])
        driver = SyntheticDriver(self.directory(), action="confirm", action_error=TimeoutError("Confirm unknown"))
        with self.assertRaises(TimeoutError):
            driver.confirm_ingame_decision_item_v1(KEY, "vivhite_courtier")
        later = SyntheticDriver(driver.directory, action="confirm", source_frame={**frame(), "revision": 2, "native_revision": 8})
        with self.assertRaisesRegex(BridgeUnavailableError, "unresolved"):
            later.confirm_ingame_decision_item_v1(KEY, "vivhite_courtier", expected_revision=2)
        self.assertEqual(later.submissions, [])
        driver, _ = self.rejected()
        claim = next((driver.directory / "ingame-decision-item-actions").glob("*.claim.json"))
        claim.with_suffix(".error.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(BridgeUnavailableError, "unresolved"):
            self.later(driver).select_ingame_decision_item_v1(KEY, expected_revision=2)


if __name__ == "__main__":
    unittest.main()
