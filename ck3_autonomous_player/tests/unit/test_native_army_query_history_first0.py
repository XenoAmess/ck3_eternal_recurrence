"""FIRST0: real Python query dispatch with retained transcript and current frames."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint, _army, _army_strength, _hello, _snapshot
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, load_native_driver_state_for_resume


class NativeArmyQueryHistoryFirst0Tests(unittest.TestCase):
    def make_driver(self, state_dir: Path):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            state_dir=state_dir, command_timeout_seconds=0.1)
        player = _army(81, controllable=True)
        endpoint.publish(_hello("game.state.snapshot", "game.command.query-army-strengths-v1"))
        endpoint.publish(_snapshot(40, played_character={"character_id": 707, "alive": True},
            active_wars=[], player_armies=[player]))
        before = driver.take_internal_semantic_snapshot()
        history = [{"index": index, "command": "query-frozen-first0-" + str(index),
            "ok": True, "result": {"values": list(range(32)), "original": index}}
            for index in range(1, 257)]
        with driver._history_lock:
            driver._command_history = copy.deepcopy(history)
            driver._driver_state_dirty = True
        driver._persist_driver_state()

        def answer(frame):
            if frame.get("type") != "execute_step":
                return
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": {"step": frame["step"], "accepted": True,
                    "status": "available", "query_sequence": 7,
                    "army_strengths": [_army_strength(81, "player", [])]}})

        endpoint.send_hook = answer
        return driver, endpoint, before, history, player

    def test_first0_query_avoids_full_history_copy_and_retains_resume_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver, endpoint, before, original, player = self.make_driver(Path(temporary))
            with mock.patch.object(driver, "_history_snapshot",
                    side_effect=AssertionError("FIRST0 query must not export full transcript")) as copies, \
                 mock.patch.object(driver, "_read_driver_state",
                    side_effect=AssertionError("FIRST0 query must not reload Driver JSON")) as reads, \
                 mock.patch.object(driver, "_encode_driver_state_locked",
                    side_effect=AssertionError("successful readonly query must defer full persistence")) as encodes:
                result = driver.execute_step("query-army-strengths-v1",
                    expected_revision=int(before["revision"]))
            self.assertEqual((copies.call_count, reads.call_count, encodes.call_count), (0, 0, 0))
            self.assertEqual(result["queried_snapshot_id"], "native:40")
            self.assertEqual(result["army_strengths"][0]["army_id"], 81)
            self.assertEqual(driver._command_history[:-1], original)
            self.assertEqual(driver._command_history[-1]["command"], "query-army-strengths-v1")
            self.assertTrue(driver._driver_state_dirty)
            public = driver.take_snapshot()
            self.assertEqual(len(public["native_command_history"]), 257)
            public["native_command_history"][0]["result"]["original"] = -1
            self.assertEqual(driver._command_history[0]["result"]["original"], 1)
            driver._persist_driver_state()
            saved = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
            restored = load_native_driver_state_for_resume(driver._native_driver_state_path(), endpoint.pipe_name)
            self.assertEqual(saved["command_history"], driver._command_history)
            self.assertEqual(restored["command_history"], driver._command_history)
            driver.close()

    def test_first0_query_still_rejects_changed_after_frame(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver, endpoint, before, original, player = self.make_driver(Path(temporary))
            answer = endpoint.send_hook

            def changed_answer(frame):
                answer(frame)
                if frame.get("type") == "execute_step":
                    endpoint.publish(_snapshot(41, played_character={"character_id": 707, "alive": True},
                        active_wars=[], player_armies=[player]))

            endpoint.send_hook = changed_answer
            with self.assertRaisesRegex(BridgeUnavailableError, "crossed a snapshot revision"):
                driver.execute_step("query-army-strengths-v1", expected_revision=int(before["revision"]))
            self.assertEqual(driver._command_history[:-1], original)
            self.assertIs(driver._command_history[-1]["ok"], False)
            driver.close()

    def test_first0_query_keeps_pending_control_submission_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver, endpoint, before, original, player = self.make_driver(Path(temporary))
            driver._player_control_authorization_blocked_v1 = True
            count = len(endpoint.frames)
            with self.assertRaisesRegex(BridgeUnavailableError, "stock player control is pending"):
                driver.execute_step("query-army-strengths-v1", expected_revision=int(before["revision"]))
            self.assertEqual(len(endpoint.frames), count)
            self.assertEqual(driver._command_history[:-1], original)
            driver.close()


if __name__ == "__main__":
    unittest.main()
