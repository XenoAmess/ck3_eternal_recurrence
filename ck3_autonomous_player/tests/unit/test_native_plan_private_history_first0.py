"""FIRST0: ordinary planning does not clone unused full-history payloads.

The fixture is offline. It exercises the real ordinary service planner and
NativeDriver view, with one synthetic flat retained transcript. It grants no
live turn, event outcome or measured latency credit.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, load_native_driver_state_for_resume,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


class _CountedPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        detached = list(self)
        memo[id(self)] = detached
        return detached


class NativePlanPrivateHistoryFirst0Tests(unittest.TestCase):
    def test_first0_ordinary_plan_keeps_private_history_local_and_public_detached(self):
        with tempfile.TemporaryDirectory() as temporary:
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, state_dir=Path(temporary),
                command_timeout_seconds=0.1,
            )
            driver.allow_private_faction_gift_formal_trial = True
            driver.allow_private_construction_formal_trial = True
            driver.allow_private_council_action = True
            endpoint.publish(_hello(
                "game.state.snapshot", "game.state.active-event",
                "game.command.select-event-option-N",
            ))
            endpoint.publish(_snapshot(
                40, active_event={"instance_id": 419, "option_count": 3},
                played_character={"character_id": 29829, "alive": True},
                active_wars=[], player_armies=[],
            ))
            driver.take_internal_semantic_snapshot()
            history = [{
                "index": index, "command": f"query-retained-plan-first0-{index}",
                "ok": True, "result": {"values": _CountedPayload(range(256))},
            } for index in range(1, 4097)]
            with driver._history_lock:
                driver._command_history = history
                driver._driver_state_dirty = True
            driver._persist_driver_state()
            service = GameplayBridgeService(driver)

            # The public fallback is the unchanged full-history reference
            # behavior, using the same retained rows and actual planner.
            with mock.patch.object(driver, "_with_internal_planning_view", None):
                expected = service.plan_turn()
            _CountedPayload.copies = 0
            with mock.patch.object(driver, "_history_snapshot",
                    side_effect=AssertionError("ordinary plan must not export all history")), \
                 mock.patch.object(driver, "_history_tail_snapshot",
                    side_effect=AssertionError("ordinary plan must not clone the history tail")), \
                 mock.patch.object(driver, "_persist_driver_state",
                    side_effect=AssertionError("ordinary plan has no Driver write")), \
                 mock.patch.object(driver, "_encode_driver_state_locked",
                    side_effect=AssertionError("ordinary plan has no full encode")):
                actual = service.plan_turn()
            self.assertEqual(actual, expected)
            self.assertEqual(_CountedPayload.copies, 0)
            self.assertTrue(str(actual["plan"]["selected_step"]).startswith("select-event-option-"))
            self.assertFalse(any(key.endswith("_history_v1") for key in actual))
            self.assertFalse(any(row.get("type") == "execute_step" for row in endpoint.frames))
            self.assertEqual(len(driver._command_history), 4096)
            self.assertFalse(driver._driver_state_dirty)

            # The public boundary must also detach a selected nested result.
            # Only this small selected field is exported, never the transcript.
            selected = {"snapshot_id": "native:40", "revision": 40,
                "plan": {"selected_step": "life-advance",
                         "selected_values": history[-1]["result"]["values"]}}
            with mock.patch.object(service, "_plan_turn_internal", return_value=selected):
                public_selected = service.plan_turn()
            public_selected["plan"]["selected_values"][0] = -1
            self.assertEqual(history[-1]["result"]["values"][0], 0)

            public = driver.take_snapshot()
            self.assertEqual(len(public["native_command_history"]), 4096)
            public["native_command_history"][0]["result"]["values"][0] = -1
            self.assertEqual(history[0]["result"]["values"][0], 0)
            saved = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
            restored = load_native_driver_state_for_resume(
                driver._native_driver_state_path(), endpoint.pipe_name,
            )
            self.assertEqual(saved["command_history"], history)
            self.assertEqual(restored["command_history"], history)
            driver.close()


if __name__ == "__main__":
    unittest.main()
