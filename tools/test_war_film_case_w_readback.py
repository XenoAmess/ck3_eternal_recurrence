"""Offline projection tests: no CK3, process reader, or native query."""
import unittest
from war_film_case_w_readback import army_events


class PublicArmyProgressTests(unittest.TestCase):
    def setUp(self):
        self.row = {"army_id": 22, "owner_character_id": 32231, "controllable": False,
                    "current_province_id": 4598, "move_target_province_id": None,
                    "move_target_observable": False, "route_province_ids": [], "army_state": "gathering"}

    def compare(self, changed):
        return army_events(self.row, {**self.row, **changed}, before={"date_raw": 0}, after={"date_raw": 24})

    def test_route_submission_is_not_location_progress(self):
        events = self.compare({"move_target_province_id": 2633, "move_target_observable": True,
                               "route_province_ids": [4599, 4574, 2633], "army_state": "moving"})
        self.assertEqual([event["kind"] for event in events], ["state_changed", "route_fields_changed"])
        self.assertFalse(events[1]["current_province_changed"])

    def test_same_unit_progress_along_previous_route_is_explicit(self):
        self.row.update(move_target_province_id=2633, move_target_observable=True,
                        route_province_ids=[4599, 4574, 2633], army_state="moving")
        events = self.compare({"current_province_id": 4599, "route_province_ids": [4574, 2633]})
        progress = [event for event in events if event["kind"] == "province_changed"]
        self.assertEqual(len(progress), 1)
        self.assertEqual((progress[0]["from"], progress[0]["to"]), (4598, 4599))
        self.assertTrue(progress[0]["new_province_in_previous_remaining_route"])

    def test_location_outside_previous_route_does_not_claim_route_following(self):
        self.row["route_province_ids"] = [4599, 4574, 2633]
        event = self.compare({"current_province_id": 9000})[0]
        self.assertEqual(event["kind"], "province_changed")
        self.assertFalse(event["new_province_in_previous_remaining_route"])

    def test_identity_mismatch_is_rejected(self):
        for changed in [{"army_id": 16777238}, {"owner_character_id": 999}]:
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "identity changed"):
                self.compare(changed)

    def test_first_visible_moving_row_does_not_prove_prior_progress(self):
        events = army_events(None, {**self.row, "army_state": "moving",
                                    "route_province_ids": [4599]}, before=None, after={"date_raw": 24})
        self.assertEqual([event["kind"] for event in events], ["public_enemy_row_appeared"])


if __name__ == "__main__":
    unittest.main()
