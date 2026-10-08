"""FIRST0 operation-count compound for the existing normal advance dispatch.

Uses small flat history rows; no invented nested data or timing threshold.
Root alone executes this new module. Offline frames grant no live day credit.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, load_native_driver_state_for_resume


class NativeNormalAdvanceCopyFirst0Tests(unittest.TestCase):
    def test_first0_normal_advance_avoids_history_tail_clones_and_keeps_one_full_barrier(self):
        with tempfile.TemporaryDirectory() as temporary:
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                state_dir=Path(temporary), command_timeout_seconds=0.1,
                life_advance_timeout_seconds=0.1)
            player = {"character_id": 707, "alive": True}
            army = _army(501, province_id=10, move_target_province_id=20,
                army_state="moving", army_state_code=7, route_province_ids=[20])
            endpoint.publish(_hello("game.state.snapshot", "game.command.pause-map",
                "game.command.resume-map", "game.command.set-speed-1",
                "game.command.set-speed-3", "game.command.set-speed-5"))
            endpoint.publish(_snapshot(1, played_character=player, player_armies=[army], active_wars=[]))
            before = driver.take_internal_semantic_snapshot()
            baseline_steps = driver.capabilities()["action_steps"]
            # Flat canonical history rows test the production copy operation,
            # without constructing a pretend large/nested performance sample.
            original_history = [{"index": index, "command": "query-flat-first0-" + str(index), "ok": True}
                for index in range(1, 257)]
            with driver._history_lock:
                driver._command_history = copy.deepcopy(original_history)
                driver._driver_state_dirty = True
            driver._persist_driver_state()
            issued_steps = []

            def answer(frame):
                if frame.get("type") != "execute_step":
                    return
                step = frame["step"]
                issued_steps.append(step)
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": True,
                    "result": {"step": step, "accepted": True}})
                if step == "set-speed-1":
                    endpoint.publish(_snapshot(2, played_character=player, speed=1,
                        player_armies=[army], active_wars=[]))
                elif step == "resume-map":
                    endpoint.publish(_snapshot(3, played_character=player, speed=1,
                        date_raw=before["date_raw"] + 24, paused=False,
                        player_armies=[army], active_wars=[]))
                elif step == "pause-map":
                    endpoint.publish(_snapshot(4, played_character=player, speed=1,
                        date_raw=before["date_raw"] + 24, paused=True,
                        player_armies=[army], active_wars=[]))
                else:
                    self.fail("FIRST0 unexpectedly changed the existing tactical speed/command path: " + step)

            endpoint.send_hook = answer
            with mock.patch.object(driver, "_history_tail_snapshot",
                    side_effect=AssertionError("normal advance readers must not deepcopy history tails")) as tail_copies, \
                 mock.patch.object(driver, "_history_snapshot",
                    side_effect=AssertionError("normal advance must not export complete history")) as full_copies, \
                 mock.patch.object(driver, "_encode_driver_state_locked",
                    wraps=driver._encode_driver_state_locked) as encodes:
                self.assertEqual(driver.capabilities()["action_steps"], baseline_steps)
                result = driver.execute_step("life-advance", expected_revision=int(before["revision"]))
            self.assertEqual((tail_copies.call_count, full_copies.call_count), (0, 0))
            self.assertEqual(encodes.call_count, 1)
            self.assertEqual(issued_steps, ["set-speed-1", "resume-map", "pause-map"])
            self.assertEqual(result["starting_date_raw"], before["date_raw"])
            self.assertEqual(result["ending_date_raw"], before["date_raw"] + 24)
            self.assertEqual(result["elapsed_days"], 1)
            self.assertIs(result["paused"], True)
            self.assertEqual(driver._command_history[:-1], original_history)
            self.assertEqual(driver._command_history[-1]["command"], "life-advance")
            self.assertIs(driver._command_history[-1]["ok"], True)
            self.assertFalse(driver._driver_state_dirty)
            saved = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
            restored = load_native_driver_state_for_resume(driver._native_driver_state_path(), endpoint.pipe_name)
            self.assertEqual(saved["command_history"], driver._command_history)
            self.assertEqual(restored["command_history"], driver._command_history)
            driver.close()


if __name__ == "__main__":
    unittest.main()
