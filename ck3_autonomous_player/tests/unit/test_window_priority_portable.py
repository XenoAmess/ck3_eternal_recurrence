"""Real Service branch tests for pending material versus foreground priority."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge import service as service_module


def frame(**values):
    base = {"snapshot_id": "native:61", "revision": 62,
            "native_revision": 61, "date_raw": 53145120,
            "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "top_exclusive_modal_choice_hint": None, "active_wars": [],
            "player_armies": [], "one_life_terminal": False,
            "played_character": {"character_id": 31254, "alive": True},
            "episode_run_id": "native-31254-test",
            "diagnostics": {"bridge_pid": 230672, "connection_generation": 1}}
    return {**base, **values}


def pending():
    return {"stage": "receipt_pending", "action_id": "crown-test-1",
            "actor_character_id": 31254, "episode_run_id": "native-31254-test",
            "pre_native_revision": 61, "pre_date_raw": 53145120,
            "source_context": {"bridge_pid": 230672,
                               "episode_run_id": "native-31254-test"}}


class PriorityTests(unittest.TestCase):
    def service_for(self, snapshot, state_dir):
        class Driver:
            _session_bridge_pid = 230672
            allow_private_realm_law_action = True
            allow_private_activity_feast_lifecycle_observation = False

            def take_internal_semantic_snapshot(self):
                return snapshot

            def _with_internal_planning_view(self, value, callback):
                return callback(value, [])

            def wait_for_change(self, *args, **kwargs):
                raise AssertionError("foreground or war priority must not wait on governance")

        driver = Driver()
        driver.state_dir = state_dir
        service = object.__new__(service_module.GameplayBridgeService)
        service.driver = driver
        service.capabilities = lambda: {}
        service._strategy_state_dir = lambda: state_dir
        service._prepare_succession_transition_v1 = (
            lambda value, steps, **kwargs: value)
        return service

    def call(self, snapshot, window_plan, *, choose_error="must not collect a new opportunity"):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp)
            (state_dir / "crown-authority-formal-v1.json").write_text(
                json.dumps({"pending": pending(), "resolved": None, "retry": None}),
                encoding="utf-8")
            service = self.service_for(snapshot, state_dir)
            with patch.object(service_module, "action_step_set", return_value={"life-advance-one-day"}), \
                 patch.object(service_module, "plan_one_life_window_priority_v1",
                              return_value=window_plan), \
                 patch.object(service_module, "read_one_life_strategy",
                              return_value={"episodes": []}), \
                 patch.object(service_module, "choose_one_life_turn",
                              side_effect=AssertionError(choose_error)):
                return service._plan_turn_internal_without_readonly_retry_v1()

    def test_event_interaction_and_modal_reach_existing_window_priority(self):
        for signal in (
            {"active_event": {"instance_id": 42}},
            {"pending_character_interaction": {"instance_id": 77}},
            {"top_exclusive_modal_choice_hint": {"status": "present", "owner_verified": True}},
        ):
            with self.subTest(signal=signal):
                selected = "typed-foreground-choice"
                plan = self.call(frame(**signal), {"selected_step": selected, "phase": "window"})
                # The synthetic literal is deliberately not a supported MCP
                # step. Service preserves the window plan and identifies its
                # required step; backend admission then correctly refuses it.
                self.assertEqual(plan["plan"]["phase"], "window")
                self.assertEqual(plan["plan"]["required_step"], selected)

    def test_unavailable_foreground_does_not_start_new_opportunity(self):
        plan = self.call(frame(active_event={"instance_id": 42}), None)
        self.assertEqual(plan["plan"]["selected_step"], None)
        self.assertEqual(plan["plan"]["phase"],
                         "foreground_window_unavailable_before_pending_receipt")
        self.assertFalse(plan["plan"]["business_credit"])

    def test_active_war_reaches_complete_planner_before_governance_receipt(self):
        with self.assertRaisesRegex(AssertionError, "WAR_PLANNER_REACHED"):
            self.call(frame(active_wars=[{"war_id": 42}]), None,
                      choose_error="WAR_PLANNER_REACHED")


if __name__ == "__main__":
    unittest.main()
