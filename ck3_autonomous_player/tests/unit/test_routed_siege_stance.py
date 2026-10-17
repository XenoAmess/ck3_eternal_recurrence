"""Portable actual-695 siege-stance regression; imports the installed source."""

import copy
import gzip
import json
from pathlib import Path
import unittest

from xar_autoplayer import strategy


FIXTURE = Path(__file__).parents[1] / "fixtures" / "portable_actual_695.json.gz"


class RoutedSiegePortable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with gzip.open(FIXTURE, "rt", encoding="utf-8") as stream:
            cls.case = json.load(stream)
        assert cls.case["schema"] == "xar.routed-siege-actual695-portable.v1"

    def relief(self, snapshot):
        army = snapshot["player_armies"][0]
        return strategy._primary_defender_siege_relief_assessment(
            snapshot,
            commands=[],
            active_wars=snapshot["active_wars"],
            controlled_armies=[army],
            pursuit_army=army,
        )

    def test_actual_departure_is_not_stationary_siege(self):
        snapshot = self.case["snapshot"]
        self.assertEqual(self.case["blocked_phase"],
                         "native_war_defender_siege_relief_observation_blocked")
        self.assertEqual(self.relief(snapshot)["status"], "not_applicable")
        self.assertEqual(self.case["army_query_result"]["status"], "available")
        self.assertTrue(all(row["status"] == "available"
                            for row in self.case["army_query_result"]["armies"]))
        war = next(w for w in snapshot["active_wars"] if w["war_id"] == 100663323)
        self.assertEqual({row["army_id"] for row in war["enemy_armies"]},
                         {436207707, 402653372})
        self.assertTrue(all(row["army_state"] == "sieging"
                            and row["move_target_observable"] is True
                            and row["move_target_province_id"] == 2623
                            and row["route_province_ids"] == [2623]
                            and row["route_read_status"] == "complete_nonempty"
                            for row in war["enemy_armies"]))

    def test_incomplete_or_ambiguous_departure_still_blocks(self):
        changes = (
            lambda row: row.update(move_target_observable=False),
            lambda row: row.update(move_target_province_id=None),
            lambda row: row.update(route_province_ids=[]),
            lambda row: row.update(route_read_status="partial"),
            lambda row: row.update(route_province_ids=[2624]),
            lambda row: row.update(move_target_province_id=row["current_province_id"]),
            lambda row: row.update(move_target_province_id=True),
        )
        for change in changes:
            with self.subTest(change=change):
                snapshot = copy.deepcopy(self.case["snapshot"])
                war = next(w for w in snapshot["active_wars"]
                           if w["war_id"] == 100663323)
                change(war["enemy_armies"][0])
                assessment = self.relief(snapshot)
                self.assertEqual(assessment["status"], "observation_unavailable")
                self.assertEqual(assessment["war_ids"], [100663323])

    def test_ordinary_choice_preserves_complete_hostile_scope(self):
        snapshot = self.case["snapshot"]
        plan = strategy.choose_one_life_turn(
            self.case["history_rows"],
            snapshot=snapshot,
            action_steps=self.case["action_steps"],
            bridge_capabilities=self.case["bridge_capabilities"],
            battle_speed_readiness=self.case["battle_speed_readiness"],
        )
        self.assertEqual(plan["phase"], "native_war_stationary_contact_horizon")
        self.assertEqual(
            plan["selected_step"],
            "query-route-contact-horizon-v1-167772577-to-2623-h-4-"
            "285212722-285212840-402653372-436207707",
        )
        self.assertEqual(
            {enemy["army_id"] for war in snapshot["active_wars"]
             for enemy in war.get("enemy_armies", [])},
            {285212722, 285212840, 402653372, 436207707},
        )


if __name__ == "__main__":
    unittest.main()
