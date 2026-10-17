"""The actual Service wait must yield to a newly published window or war."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge import service as service_module


def frame(**changes):
    base = {
        "snapshot_id": "native:61", "revision": 62, "native_revision": 61,
        "date_raw": 53145120, "paused": True, "map_ready": True,
        "active_event": None, "pending_character_interaction": None,
        "top_exclusive_modal_choice_hint": None, "active_wars": [],
        "player_armies": [], "one_life_terminal": False,
        "played_character": {"character_id": 31254, "alive": True},
        "episode_run_id": "native-31254-test",
        "diagnostics": {"bridge_pid": 230672, "connection_generation": 1},
    }
    return {**base, **changes}


def pending():
    return {
        "stage": "receipt_pending", "action_id": "crown-test-1",
        "actor_character_id": 31254, "episode_run_id": "native-31254-test",
        "pre_native_revision": 61, "pre_date_raw": 53145120,
        "source_context": {"bridge_pid": 230672,
                           "episode_run_id": "native-31254-test"},
    }


class EmergentPriorityTests(unittest.TestCase):
    def run_plan(self, fresh, *, expected_war=False):
        initial = frame()

        class Driver:
            _session_bridge_pid = 230672
            allow_private_realm_law_action = True
            allow_private_activity_feast_lifecycle_observation = False

            def __init__(self):
                self.wait_calls = 0

            def take_internal_semantic_snapshot(self):
                return initial

            def _with_internal_planning_view(self, value, callback):
                return callback(value, [])

            def wait_for_change(self, *args, **kwargs):
                self.wait_calls += 1
                if self.wait_calls != 1:
                    raise AssertionError("fresh priority must stop the wait")
                return fresh

        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp)
            (state_dir / "crown-authority-formal-v1.json").write_text(
                json.dumps({"pending": pending(), "resolved": None, "retry": None}),
                encoding="utf-8")
            driver = Driver()
            driver.state_dir = state_dir
            service = object.__new__(service_module.GameplayBridgeService)
            service.driver = driver
            service.capabilities = lambda: {}
            service._strategy_state_dir = lambda: state_dir
            service._prepare_succession_transition_v1 = (
                lambda value, steps, **kwargs: value)
            with patch.object(service_module, "action_step_set",
                              return_value={"life-advance-one-day"}), \
                 patch.object(service_module, "plan_one_life_window_priority_v1",
                              return_value=(None if expected_war else
                                            {"selected_step": "typed-foreground-choice",
                                             "phase": "window"})), \
                 patch.object(service_module, "read_one_life_strategy",
                              return_value={"episodes": []}), \
                 patch.object(service_module, "choose_one_life_turn",
                              side_effect=AssertionError("WAR_PLANNER_REACHED")):
                if expected_war:
                    with self.assertRaisesRegex(AssertionError, "WAR_PLANNER_REACHED"):
                        service._plan_turn_internal_without_readonly_retry_v1()
                else:
                    planned = service._plan_turn_internal_without_readonly_retry_v1()
                    self.assertEqual(planned["plan"]["phase"], "window")
                    self.assertEqual(planned["plan"]["required_step"],
                                     "typed-foreground-choice")
            self.assertEqual(driver.wait_calls, 1)

    def test_window_published_while_pending_material_waits(self):
        for signal in (
            {"active_event": {"instance_id": 42}},
            {"pending_character_interaction": {"instance_id": 77}},
            {"top_exclusive_modal_choice_hint":
             {"status": "present", "owner_verified": True}},
        ):
            with self.subTest(signal=signal):
                self.run_plan(frame(snapshot_id="native:61:public63", revision=63,
                                    **signal))

    def test_war_published_while_pending_material_waits(self):
        self.run_plan(frame(snapshot_id="native:61:public63", revision=63,
                            active_wars=[{"war_id": 42}]), expected_war=True)


if __name__ == "__main__":
    unittest.main()
