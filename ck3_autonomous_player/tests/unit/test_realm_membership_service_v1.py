"""Actual Service planning/copy/dispatch/hook chain with a synthetic Driver.

Only the strategic choice is fixed. The ordinary planning reader, public copy,
Service execute_step and after-query hook are production code; no Game or RPC.
"""
from copy import deepcopy
from unittest.mock import patch
import unittest

from test_realm_membership_feedback_v1 import inputs, COMPONENT
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.realm_membership_after_query_v1 import (
    observe_realm_membership_after_query_v1 as consume,
)


STEP = "query-player-faction-alerts-v1"
OTHER = "fixture-readonly-other"


class Driver:
    def __init__(self):
        self.load(inputs())
        self.snapshot_calls = 0
        self.public_snapshot_calls = 0
        self.calls = []
        self.error = None
        self.during_execute = None

    def load(self, args):
        self.frame, self.source, self.packet = deepcopy(args)
        del self.packet["binding"]
        self.frame.update(active_wars=[], history=[], native_command_history=[])
        self.packet.update(step=STEP, accepted=True, status="available",
            snapshot_revision=self.source["native_revision"], player_faction_alerts_ready=True,
            queried_snapshot_id=self.source["snapshot_id"], queried_revision=self.source["revision"],
            queried_native_revision=self.source["native_revision"])

    def capabilities(self):
        return {"format_version": 1, "backend_id": "native-headless", "source": "named-pipe",
                "snapshot": True, "wait_for_change": False, "action_steps": [STEP, OTHER],
                "bridge_capabilities": ["query-player-faction-alerts-v1"]}

    def take_internal_semantic_snapshot(self):
        self.snapshot_calls += 1
        return self.frame

    def _with_internal_planning_view(self, snapshot, callback):
        return callback(snapshot, [])

    def take_snapshot(self):
        self.public_snapshot_calls += 1
        raise AssertionError("query hook must reuse the original planning frame")

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        if self.during_execute:
            self.during_execute()
        if self.error:
            raise self.error
        if expected_revision != self.source["revision"]:
            raise AssertionError("dispatch lost the original public revision")
        return deepcopy(self.packet) if step == STEP else {"accepted": True, "step": step}


class Camera:
    def schedule(self, _):
        return {"status": "fixture_no_camera"}


class RealmMembershipServiceTests(unittest.TestCase):
    def setUp(self):
        self.driver = Driver()
        self.service = GameplayBridgeService(self.driver)
        self.service._auto_camera_worker = Camera()
        self.step = STEP
        self.choice = patch("xar_autoplayer.bridge.service.choose_one_life_turn",
            side_effect=lambda *a, **k: {"selected_step": self.step, "phase": "fixture_query"})
        self.choice.start()
        self.addCleanup(self.choice.stop)

    def test_actual_planning_public_copy_dispatch_and_vassal_loss(self):
        public = self.service.plan_turn()
        slot = self.service._realm_membership_query_slot_v1
        self.assertIs(slot["plan"], public)
        self.assertIsNot(slot["source_frame"], public["planning_source_frame"])
        self.assertIsNot(slot["snapshot"], public)
        self.assertNotIn("_realm_membership_query_snapshot_v1", public)
        self.assertEqual(self.driver.calls, [])
        # auto_turn starts a new plan, then executes exactly its one query.
        first = self.service.auto_turn()
        self.assertEqual(first["realm_membership_feedback_v1"]["raw_metrics"]["realm_county_count"]["value"], "3")
        self.driver.load(inputs((2231, 2262), native=42, public=10, date=53144352, query=2))
        second = self.service.auto_turn()
        self.assertEqual(second["realm_membership_feedback_v1"]["difference"]["lost_county_title_ids"], [2488])
        self.assertEqual(self.driver.calls, [(STEP, 9), (STEP, 10)])
        self.assertEqual(self.driver.snapshot_calls, 3)
        self.assertEqual(self.driver.public_snapshot_calls, 0)
        self.assertIsNone(self.service._realm_membership_query_slot_v1)

    def test_old_epoch_completion_cannot_consume_new_public_plan(self):
        old = self.service.plan_turn()
        new = self.service.plan_turn()
        stale = consume(self.service, old,
            {"status": "executed", "selected_step": STEP, "result": self.driver.packet})
        self.assertEqual(stale["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertIs(self.service._realm_membership_query_slot_v1["plan"], new)
        self.assertFalse(hasattr(self.service, "_realm_membership_observation_v1"))

    def test_actual_dispatch_exception_and_planning_exception_clear_private_slot(self):
        self.driver.error = BridgeUnavailableError("synthetic transport unknown")
        with self.assertRaises(BridgeUnavailableError):
            self.service.auto_turn()
        self.assertIsNone(self.service._realm_membership_query_slot_v1)
        self.driver.error = None
        self.service.plan_turn()
        with patch("xar_autoplayer.bridge.ordinary_sway_service_v1.stage_ordinary_sway_v1",
                   side_effect=ValueError("synthetic staging failure")):
            with self.assertRaises(ValueError):
                self.service.plan_turn()
        self.assertIsNone(self.service._realm_membership_query_slot_v1)
        self.assertEqual(self.driver.calls, [(STEP, 9)])

    def test_cross_actor_material_and_absent_component_remain_unknown(self):
        self.service.auto_turn()
        retained = deepcopy(self.service._realm_membership_observation_v1)
        self.driver.load(inputs(native=42, public=10, query=2))
        self.driver.packet["player_faction_alerts"][COMPONENT]["actor_character_id"] = 7
        result = self.service.auto_turn()
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertEqual(self.service._realm_membership_observation_v1, retained)
        del self.driver.packet["player_faction_alerts"][COMPONENT]
        self.assertEqual(self.service.auto_turn()["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertEqual(self.driver.public_snapshot_calls, 0)

    def test_new_plan_during_actual_driver_call_invalidates_late_return(self):
        newer = []
        self.driver.during_execute = lambda: newer.append(self.service.plan_turn())
        result = self.service.auto_turn()
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertIs(self.service._realm_membership_query_slot_v1["plan"], newer[0])
        self.assertFalse(hasattr(self.service, "_realm_membership_observation_v1"))
        self.assertEqual(self.driver.calls, [(STEP, 9)])

    def test_other_cycle_does_not_retain_or_copy_query_snapshot(self):
        self.step = OTHER
        with patch("xar_autoplayer.bridge.realm_membership_after_query_v1.bind_current_realm_membership_plan_v1") as bind:
            result = self.service.auto_turn()
        bind.assert_not_called()
        self.assertNotIn("realm_membership_feedback_v1", result)
        self.assertIsNone(self.service._realm_membership_query_slot_v1)
        self.assertEqual(self.driver.snapshot_calls, 1)
        self.assertEqual(self.driver.public_snapshot_calls, 0)
        self.assertEqual(self.driver.calls, [(OTHER, 9)])


if __name__ == "__main__":
    unittest.main()
