"""A qualified contact horizon can select an existing halt, never replay its ACK."""
from pathlib import Path
import copy
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import strategy


class UnsafeCommittedRouteHalt(unittest.TestCase):
    def setUp(self):
        self.snapshot = {"paused": True, "map_ready": True, "date_raw": 1000,
                         "native_revision": 3, "active_event": None,
                         "pending_character_interaction": None,
                         "played_character": {"character_id": 4, "alive": True}}
        self.army = {"army_id": 0, "controllable": True, "owner_character_id": 4,
                     "current_province_id": 20, "move_target_province_id": 30,
                     "in_combat": False, "retreating": False, "army_state": "moving",
                     "route_read_status": "complete_nonempty", "route_province_ids": [20, 30]}
        self.audit = {"target_province_id": 30,
                      "contact_policy": "blocked_without_qualified_combat_permission",
                      "contact_horizon": {"status": "available", "one_day_contact_free": False,
                                          "subject_army_id": 0, "target_province_id": 30,
                                          "date_raw": 1000, "snapshot_revision": 3}}

    def choose(self):
        return strategy._unsafe_committed_route_halt_plan(
            self.snapshot, self.army, self.audit, army_id=0,
            available_steps={"halt-army-0"}, war_summary=[],
        )

    def test_existing_native_halt_requires_complete_same_frame_contact(self):
        plan = self.choose()
        self.assertEqual(plan["selected_step"], "halt-army-0")
        self.assertEqual(plan["halt_intent"]["postcondition_required"],
                         "fresh_route_empty_and_move_target_none")
        self.audit["contact_horizon"]["snapshot_revision"] += 1
        self.assertIsNone(self.choose())

    def test_active_combat_never_selects_halt(self):
        self.army.update(in_combat=True, army_state="combat")
        self.assertIsNone(self.choose())

    def test_pending_ack_is_retained_until_fresh_route_observation(self):
        rows = [{"command": "halt-army-0", "ok": True, "result": {
            "step": "halt-army-0", "accepted": True,
            "war_action": {"status": "halt_submitted", "army_id": 0,
                           "submitted_date_raw": 1000, "postcondition_verified": False}}}]
        pending = strategy._pending_unsafe_route_halt(rows, self.snapshot, army_id=0)
        self.assertFalse(pending["postcondition_verified"])
        self.snapshot["date_raw"] += 24
        self.assertIsNone(strategy._pending_unsafe_route_halt(rows, self.snapshot, army_id=0))


if __name__ == "__main__":
    unittest.main()
