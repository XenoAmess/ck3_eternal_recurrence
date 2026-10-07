"""One file-only compound covers the original M4 window/receipt distinction."""

from __future__ import annotations

import copy
import unittest

from xar_autoplayer.m4_material_window_v1 import (
    TWO_GAME_YEARS_RAW, collect_m4_materials_v1,
    project_m4_window_progress_v1, select_m4_window_v1,
)


class M4MaterialWindowV1Tests(unittest.TestCase):
    def test_first_three_original_materials_share_an_explicit_window(self):
        actor, episode, start = 29829, "fixture-original-robert", 53288472
        snapshot = {"played_character": {"character_id": actor},
                    "episode_run_id": episode, "date_raw": start, "snapshot_id": "fixture:7"}
        window = select_m4_window_v1(snapshot, window_id="fixture-two-year-1",
                                    start_date_raw=start, end_date_raw=start + TWO_GAME_YEARS_RAW)
        construction = {"pending": None, "applied_prior": [], "applied": {
            "status": "applied", "postcondition_verified": True, "episode_run_id": episode,
            "actor_character_id": actor, "action_request_id": "fixture-build-1",
            "pre_date_raw": start, "post_date_raw": start + 24, "completion_status": "in_progress"}}
        council = {"pending": None, "applied": {
            "status": "applied", "episode_run_id": episode,
            "action_request_id": "fixture-council-1", "candidate_character_id": 43706,
            "action_ack": {"council_assign_councillor_ack": {"pre_date_raw": start}},
            "receipt": {"council_assign_councillor_receipt": {
                "status": "applied", "postcondition_verified": True,
                "action_request_id": "fixture-council-1", "owner_character_id": actor,
                "incumbent_character_id": 43706, "post_date_raw": start + 24,
                "position_key": "councillor_steward"}},
            "independent_position": {"incumbent_character_id": 43706},
            "next_turn_consumed": True, "next_turn_date_raw": start + 48}}
        sway = {"pending": None, "resolved": {
            "postcondition_verified": True, "actor_character_id": actor,
            "action_id": "fixture-sway-1", "post_date_raw": start,
            "native_receipt": {"scheme_instance_id": 134217986, "scheme_instance_generation": 8},
            "material_intervention": {"action_id": "fixture-sway-1", "actor_character_id": actor,
                "target_character_id": 34333, "source_date_raw": start + 48,
                "scheme_instance_id": 134217986, "scheme_instance_generation": 8,
                "dedicated_benefit_observed": True,
                "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
                "next_turn_consumed": True, "following_date_raw": start + 72}}}
        root = {"status": "available", "player_character_id": actor, "date_raw": start + 48,
                "direct_landed_vassal_character_ids": [34333]}

        def project(**overrides):
            inputs = {"construction": construction, "council": council,
                      "sway": sway, "campaign_root": root, **overrides}
            return project_m4_window_progress_v1(window, collect_m4_materials_v1(
                episode_run_id=episode, actor_character_id=actor, **inputs))

        good = project()
        self.assertEqual(good["material_parts_observed"], 3)
        self.assertTrue(good["three_window_materials_observed"])
        self.assertFalse(good["authoritative_milestone_credit_written"])
        self.assertEqual(good["parts"]["construction"]["observations"][0]["completion_status"], "in_progress")
        self.assertIsNone(good["parts"]["construction"]["observations"][0]["next_turn_consumed_observed"])

        ack_only = copy.deepcopy(council)
        ack_only["applied"].pop("receipt")
        self.assertEqual(project(council=ack_only)["material_parts_observed"], 2)
        old = copy.deepcopy(council)
        old["applied"]["action_ack"]["council_assign_councillor_ack"]["pre_date_raw"] = start - 24
        self.assertEqual(project(council=old)["material_parts_observed"], 2)
        wrong_holder = copy.deepcopy(council)
        wrong_holder["applied"]["independent_position"]["incumbent_character_id"] = 32716
        self.assertEqual(project(council=wrong_holder)["material_parts_observed"], 2)
        total_only = copy.deepcopy(sway)
        total_only["resolved"]["material_intervention"]["scheme_sway_opinion"] = {
            "observed": True, "present": False, "value": None}
        self.assertEqual(project(sway=total_only)["material_parts_observed"], 2)
        self.assertEqual(project(campaign_root={})["material_parts_observed"], 2)
        gifted = project(sway=None, faction_receipts=[{
            "episode_run_id": episode, "pre_date_raw": start,
            "receipt": {"schema_version": 1, "request_id": "fixture-gift-1", "status": "mitigated",
                "postcondition_verified": True, "mitigation_applied": True, "player_character_id": actor,
                "source_faction_id": 50331692, "post_observed_date_raw": start + 24,
                "post_gift_opinion_present": True, "post_gift_opinion_modifier_value": 20}}])
        self.assertEqual(gifted["material_parts_observed"], 3)
        unknown = project(sway=None, faction_receipts=[{
            "episode_run_id": episode, "pre_date_raw": start,
            "resolved_request_outcomes": {"fixture-gift-1": "applied"}}])
        self.assertEqual(unknown["material_parts_observed"], 2)
        with self.assertRaises(ValueError):
            select_m4_window_v1(snapshot, window_id="too-long", start_date_raw=start,
                                end_date_raw=start + TWO_GAME_YEARS_RAW + 24)


if __name__ == "__main__":
    unittest.main()
