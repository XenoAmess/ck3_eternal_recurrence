from __future__ import annotations

import copy
from decimal import Decimal
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.native_battle_case import (
    NativeBattleCaseError,
    _validate,
    _validate_repeatability,
    _validate_phase_event_observations,
    _validate_phase_event_save_feedback,
    _validate_join_day_casualties,
    _validate_join_day_kernel_parity,
    _validate_join_day_kernel_parity_v2,
    _validate_phase_event_regiment_feedback,
    _validate_main_outgoing_conditional_parity,
    _validate_main_outgoing_conditional_parity_v2,
    load_episode01_native_battle_case,
    load_episode01_native_battle_repeatability,
    load_episode01_phase_event_observations,
    load_episode01_phase_event_save_feedback,
    load_episode01_join_day_casualties,
    load_episode01_join_day_kernel_parity,
    load_episode01_join_day_kernel_parity_v2,
    load_episode01_phase_event_regiment_feedback,
    load_episode01_main_outgoing_conditional_parity,
    load_episode01_main_outgoing_conditional_parity_v2,
    load_episode01_paired_counter_r14_parity,
    load_episode01_prejoin_counter_r14_parity_v2,
    load_episode01_paired_advantage_parity,
    load_episode01_paired_trace_failure_boundaries,
    load_episode01_paired_trace_day26_identity,
    load_episode01_phase_event_kill_replay_feedback,
    load_episode01_phase_event_kill_trace_recovery,
    load_episode01_phase_event_kill_trace_release,
    load_episode01_conditional_kill_effect_audit,
    load_episode01_selected_phase_event_row,
    load_episode01_knight_kill_reward_scaling,
    original_daily_timeline,
)
from xar_autoplayer.simulation.native_advantage import resolved_advantage_with_commander_rolls_raw
from xar_autoplayer.simulation.native_phase_event_rewards import knight_kill_inverse_prestige_raw


class NativeBattleCaseTests(unittest.TestCase):
    def test_original_outcome_and_replay_divergence_stay_separate(self) -> None:
        case = load_episode01_native_battle_case()
        self.assertEqual(len(original_daily_timeline()), 31)
        self.assertEqual([row["day"] for row in case["joins"]], [1, 2, 12, 22])
        self.assertEqual(case["winner_relative_to_player"], "enemy")
        self.assertEqual(case["battle_warscore_player_delta_raw_q100000"], -5_000_000)
        self.assertEqual(case["first_numeric_divergence_source_day"], 6)
        self.assertTrue(case["phase_traces"][1]["replay_matches_original_day"])
        self.assertFalse(case["phase_traces"][2]["replay_matches_original_day"])
        self.assertFalse(case["phase_trace_may_bind_to_original_daily_transition"])
        self.assertFalse(case["calibrated_win_probability_available"])
        self.assertFalse(case["planner_usable"])

    def test_evidence_cannot_be_promoted_by_switching_a_flag(self) -> None:
        case = load_episode01_native_battle_case()
        for key in ("planner_usable", "calibrated_win_probability_available",
                    "same_random_trajectory_proven", "phase_trace_may_bind_to_original_daily_transition"):
            promoted = copy.deepcopy(case)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate(promoted)

    def test_checkpoint_replays_diverge_without_authorizing_win_probability(self) -> None:
        report = load_episode01_native_battle_repeatability()
        self.assertEqual([row["winner_side_raw"] for row in report["trials"]], [0, 0, 0])
        self.assertEqual([row["first_regiment_current_divergence_day"]
                          for row in report["pairwise_divergence"]], [6, 6, 6])
        self.assertEqual([row["mode"] for row in report["trials"]], [
            "live_continuation_after_contact_save", "checkpoint_restore", "checkpoint_restore",
        ])
        self.assertFalse(report["calibrated_win_probability_available"])
        for key in ("independent_random_draws_proven", "calibrated_win_probability_available",
                    "planner_usable"):
            promoted = copy.deepcopy(report)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate_repeatability(promoted)

    def test_phase_event_ledger_is_not_mistaken_for_effect_execution(self) -> None:
        report = load_episode01_phase_event_observations()
        self.assertEqual(report["battle_event_row_count"], 6)
        self.assertEqual([row["source_day"] for row in report["event_fire_pairs"]],
                         [5, 7, 9, 15, 16, 19])
        self.assertTrue(all(not row["observed_character_core_deltas_within_fire"]
                            for row in report["event_fire_pairs"]))
        wounded = report["event_fire_pairs"][0]["target_character_observations"][0]
        self.assertEqual(wounded["same_fire_before"]["prowess"], 8)
        self.assertEqual(wounded["same_fire_after"]["prowess"], 8)
        self.assertEqual(wounded["next_source_day_record0"]["prowess"], 8)
        self.assertEqual(wounded["next_source_day_record2"]["prowess"], 6)
        killed = report["event_fire_pairs"][3]["target_character_observations"][0]
        self.assertFalse(killed["same_fire_after"]["death_marker_present"])
        self.assertTrue(killed["next_source_day_record2"]["death_marker_present"])
        self.assertFalse(report["complete_effect_feedback_proven"])
        for key in ("complete_effect_feedback_proven", "planner_usable"):
            promoted = copy.deepcopy(report)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate_phase_event_observations(promoted)

    def test_same_date_save_binds_target_and_opponent_state(self) -> None:
        report = load_episode01_phase_event_save_feedback()
        by_day = {row["event_source_day"]: row for row in report["event_save_pairs"]}
        self.assertEqual(tuple(by_day), (5, 7, 9, 15, 16, 19))
        wound, killed = by_day[5], by_day[15]
        self.assertEqual(wound["saves"][0]["character"]["wounded_rank"], 0)
        self.assertEqual(wound["saves"][1]["character"]["wounded_rank"], 1)
        self.assertEqual(wound["saves"][1]["date_raw"], wound["event_native_date_raw"])
        self.assertEqual(wound["target_core_observations"]["next_source_day_record0"]["prowess"], 8)
        self.assertEqual(wound["target_core_observations"]["next_source_day_record2"]["prowess"], 6)
        self.assertTrue(killed["saves"][0]["character"]["alive_data_present"])
        self.assertTrue(killed["saves"][1]["character"]["dead_data_present"])
        self.assertEqual(killed["saves"][1]["character"]["death_reason"], "death_battle")
        self.assertEqual(killed["saves"][1]["character"]["killer_character_id"], 32716)
        self.assertEqual(killed["saves"][1]["date_raw"], killed["event_native_date_raw"])
        for day, opponent_id, gain, prowess_gain in (
            (5, 34867, 75, 1),
            (7, 54140, Decimal("37.5"), 1),
            (9, 34867, Decimal("37.5"), 0),
            (15, 32716, 300, 1),
            (16, 54144, 75, 1),
            (19, 35124, 75, 0),
        ):
            row = by_day[day]
            before, after = (save["opponent_character"] for save in row["saves"])
            self.assertEqual(row["opponent_character_id"], opponent_id)
            self.assertEqual(after["base_skill_values"][-1] - before["base_skill_values"][-1], prowess_gain)
            self.assertEqual(Decimal(after["prestige_currency"]) - Decimal(before["prestige_currency"]), gain)
            if before["prestige_accumulated"] is not None and after["prestige_accumulated"] is not None:
                self.assertEqual(Decimal(after["prestige_accumulated"])
                                 - Decimal(before["prestige_accumulated"]), gain)
            changed = copy.deepcopy(report)
            changed["event_save_pairs"][list(by_day).index(day)]["saves"][1][
                "opponent_character"]["prestige_currency"] = "0"
            with self.assertRaises(NativeBattleCaseError):
                _validate_phase_event_save_feedback(changed)
        for key in ("full_effect_write_set_proven", "calibrated_win_probability_available",
                    "planner_usable"):
            promoted = copy.deepcopy(report)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate_phase_event_save_feedback(promoted)

    def test_joined_regiments_take_observed_arrival_day_casualties(self) -> None:
        report = load_episode01_join_day_casualties()
        self.assertEqual([row["army_id"] for row in report["join_observations"]], [22, 28])
        self.assertEqual([row["fighting_regiment_count"] for row in report["join_observations"]], [12, 5])
        for row in report["join_observations"]:
            for regiment in row["regiments"]:
                if not regiment["fights_in_main_phase"]:
                    continue
                self.assertGreater(regiment["arrival_day_soft_casualties_raw"], 0)
                self.assertGreater(regiment["arrival_day_hard_casualties_raw"], 0)
                self.assertEqual(
                    regiment["prejoin_saved_current_raw"] - regiment["arrival_day_current_fighting_raw"],
                    regiment["arrival_day_soft_casualties_raw"]
                    + regiment["arrival_day_hard_casualties_raw"],
                )
        self.assertFalse(report["global_manager_order_proven"])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["global_manager_order_proven"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_join_day_casualties(promoted)

    def test_join_day_casualty_kernel_preserves_conditioning_and_residual(self) -> None:
        report = load_episode01_join_day_kernel_parity()
        day11, day21 = report["source_days"]
        self.assertEqual((day11["joined_regiment_current_exact_count"],
                          day21["joined_regiment_current_exact_count"]), (12, 5))
        self.assertEqual(day11["residuals"], [{
            "regiment_id": 220,
            "newly_joined": False,
            "predicted_minus_native_raw": 214,
        }])
        self.assertEqual(day21["residuals"], [])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["source_days"][0]["residuals"] = []
        with self.assertRaises(NativeBattleCaseError):
            _validate_join_day_kernel_parity(promoted)

    def test_pre_schedule_toughness_refresh_closes_only_conditional_parity(self) -> None:
        report = load_episode01_join_day_kernel_parity_v2()
        day11, day21 = report["source_days"]
        self.assertEqual(day11["old_regiment_effective_toughness_changes"], [{
            "regiment_id": 220,
            "control_toughness_raw": 7400000,
            "pre_schedule_toughness_raw": 3700000,
        }])
        self.assertEqual(day21["old_regiment_effective_toughness_changes"], [])
        self.assertTrue(all(row["whole_side_current_exact"] for row in report["source_days"]))
        self.assertFalse(report["effective_toughness_refresh_reconstructed"])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["effective_toughness_refresh_reconstructed"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_join_day_kernel_parity_v2(promoted)

    def test_wound_target_prowess_and_regiment_stats_refresh_at_distinct_boundaries(self) -> None:
        report = load_episode01_phase_event_regiment_feedback()
        self.assertEqual([row["prowess"] for row in report["stages"]], [4, 4, 2, 2])
        self.assertEqual([row["effective_toughness_raw"] for row in report["stages"]],
                         [7400000, 7400000, 7400000, 3700000])
        self.assertEqual(report["same_date_later_save_wounded_rank"], 1)
        self.assertFalse(report["event_unique_cause_proven"])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["event_unique_cause_proven"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_phase_event_regiment_feedback(promoted)

    def test_outgoing_damage_scaling_exact_only_with_native_operands(self) -> None:
        report = load_episode01_main_outgoing_conditional_parity()
        self.assertEqual(report["native_outgoing_values_compared"], 46)
        self.assertEqual(report["exact_outgoing_values"], 46)
        self.assertEqual([row["source_day"] for row in report["source_days"]], list(range(4, 27)))
        by_day = {row["source_day"]: row for row in report["source_days"]}
        self.assertEqual(by_day[11]["observed_joined_fighting_men_raw"], 256000000)
        self.assertEqual(by_day[21]["observed_joined_fighting_men_raw"], 105800000)
        self.assertEqual(by_day[16]["advantage_record_capture_failure_flags"], 0)
        self.assertFalse(report["post_counter_attack_reconstructed"])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["post_counter_attack_reconstructed"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_main_outgoing_conditional_parity(promoted)

    def test_stock_forest_and_observed_joins_reconstruct_width_history(self) -> None:
        report = load_episode01_main_outgoing_conditional_parity_v2()
        by_day = {row["source_day"]: row for row in report["source_days"]}
        self.assertEqual((by_day[4]["computed_base_combat_width"],
                          by_day[4]["computed_final_combat_width"]), (1645, 1480))
        self.assertEqual((by_day[11]["computed_base_combat_width"],
                          by_day[11]["computed_final_combat_width"]), (2467, 2220))
        self.assertEqual((by_day[21]["computed_base_combat_width"],
                          by_day[21]["computed_final_combat_width"]), (2467, 2220))
        self.assertTrue(all(row["combat_width_exact"] and row["both_sides_exact"]
                            for row in report["source_days"]))
        self.assertFalse(report["width_update_timing_reconstructed"])
        self.assertFalse(report["planner_usable"])
        promoted = copy.deepcopy(report)
        promoted["width_update_timing_reconstructed"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_main_outgoing_conditional_parity_v2(promoted)
        promoted = copy.deepcopy(report)
        promoted["outgoing_damage_reconstructed"] = True
        with self.assertRaises(NativeBattleCaseError):
            _validate_join_day_kernel_parity(promoted)

    def test_paired_counter_r14_does_not_promote_join_days_or_forecast(self) -> None:
        report = load_episode01_paired_counter_r14_parity()
        self.assertEqual(report["observed_days"], 23)
        self.assertEqual(report["conditional_exact_side_comparisons"], 43)
        self.assertEqual(report["unresolved_days"], [11, 21])
        rows = {row["day"]: row for row in report["days"]}
        self.assertEqual(rows[11]["side_comparison"], {
            "enemy": "mismatch", "player_or_allied": "mismatch"
        })
        self.assertEqual(rows[21]["side_comparison"], {
            "enemy": "mismatch", "player_or_allied": "exact"
        })
        self.assertEqual(rows[26]["trace_status"], "trace_unavailable")
        self.assertEqual(rows[26]["side_comparison"], {
            "enemy": "exact", "player_or_allied": "exact"
        })
        self.assertFalse(report["forecast_ready"])
        self.assertFalse(report["planner_usable"])

    def test_same_date_prejoin_query_closes_only_conditional_r14_arithmetic(self) -> None:
        report = load_episode01_prejoin_counter_r14_parity_v2()
        self.assertEqual(report["native_r14_side_comparisons"], 46)
        self.assertEqual(report["conditional_exact_r14_side_comparisons"], 46)
        self.assertEqual([row["source_day"] for row in report["join_day_repairs"]], [11, 21])
        self.assertEqual([row["joined_army_id"] for row in report["join_day_repairs"]], [22, 28])
        self.assertTrue(all(row["delta_raw"] == {"enemy": 0, "player_or_allied": 0}
                            for row in report["join_day_repairs"]))
        self.assertFalse(report["join_policy_reconstructed"])
        self.assertFalse(report["phase_effect_transition_complete"])
        self.assertFalse(report["advantage_reconstructed"])
        self.assertFalse(report["whole_battle_win_probability_available"])
        self.assertFalse(report["planner_usable"])

    def test_same_run_zero_roll_context_and_observed_rolls_match_local_advantage(self) -> None:
        report = load_episode01_paired_advantage_parity()
        self.assertEqual(report["observed_main_days"], 23)
        self.assertEqual(report["conditional_exact_advantage_days"], 23)
        self.assertEqual({row["zero_roll_advantage_raw"] for row in report["days"]}, {-1_000_000})
        for row in report["days"]:
            self.assertEqual(
                resolved_advantage_with_commander_rolls_raw(
                    row["zero_roll_advantage_raw"], *row["observed_roll_points"]
                ), row["native_advantage_raw"],
            )
        self.assertEqual([row["day"] for row in report["days"]
                          if row["whole_phase_trace_status"] != "bounded_trace_available"],
                         [11, 21, 26])
        self.assertFalse(report["future_rolls_predicted"])
        self.assertFalse(report["whole_battle_win_probability_available"])
        self.assertFalse(report["planner_usable"])

    def test_red_trace_boundary_diagnostics_preserve_green_local_only(self) -> None:
        report = load_episode01_paired_trace_failure_boundaries()
        self.assertEqual([row["day"] for row in report["red_days"]], [11, 21, 26])
        self.assertEqual([row["first_failing_boundary_index"] for row in report["red_days"]], [2, 2, 6])
        self.assertEqual([row["same_day_newly_joined_enemy_army_ids"] for row in report["red_days"]],
                         [[22], [28], []])
        self.assertTrue(all(row["full_trace_available"] is False for row in report["red_days"]))
        self.assertFalse(report["whole_battle_win_probability_available"])
        self.assertFalse(report["planner_usable"])

    def test_day26_stale_scheduled_regiment_diagnostic_keeps_trace_red(self) -> None:
        report = load_episode01_paired_trace_day26_identity()
        self.assertEqual(report["appended_event"]["stable_key"], "knight_killed_by_enemy")
        self.assertEqual(report["appended_event"]["left_character_id"], 34867)
        self.assertEqual(report["final_side1_scheduled_regiment_id"], 62)
        self.assertFalse(report["final_side1_knight_regiment_present"])
        self.assertFalse(report["final_side1_regiment_bucket_present"])
        self.assertEqual(report["inferred_first_failing_read"],
                         "ReadSide(side1).scheduled_knights.regiment_identity_guard")
        self.assertFalse(report["same_day_post_event_save_available"])
        self.assertFalse(report["full_trace_available"])
        self.assertFalse(report["planner_usable"])

    def test_independent_kill_replay_binds_same_date_save_without_forecast(self) -> None:
        report = load_episode01_phase_event_kill_replay_feedback()
        self.assertEqual(report["appended_event"]["left_character_id"], 33437)
        self.assertEqual(report["event_appended_between_boundaries"], [4, 5])
        self.assertEqual(report["target_core_at_last_valid_boundary"]["current_regiment_id"], 65)
        self.assertFalse(report["target_core_at_last_valid_boundary"]["death_marker_present"])
        self.assertTrue(report["target_before_and_after"][1]["dead_data_present"])
        self.assertEqual(report["target_before_and_after"][1]["death_reason"], "death_battle")
        self.assertEqual(report["target_before_and_after"][1]["killer_character_id"], 34120)
        self.assertEqual(report["opponent_prestige_currency_delta"], "150.0000")
        self.assertEqual(report["opponent_prestige_accumulated_delta"], "150.0000")
        self.assertEqual(report["opponent_base_prowess_delta"], 0)
        self.assertFalse(report["full_event_write_set_proven"])
        self.assertFalse(report["full_phase_trace_available"])
        self.assertFalse(report["planner_usable"])

    def test_stock_kill_reward_uses_victim_title_in_two_native_cases(self) -> None:
        report = load_episode01_knight_kill_reward_scaling()
        self.assertEqual(report["source_phase_events_sha256"],
                         "E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1")
        self.assertEqual(report["conditional_exact_cases"], 2)
        self.assertEqual([row["target_held_title_keys"] for row in report["cases"]],
                         [["b_baja_medjerda", "c_medjerda"], []])
        for row in report["cases"]:
            self.assertEqual(knight_kill_inverse_prestige_raw(
                victim_primary_title_tier=row["conditional_primary_title_tier"],
                victim_is_lowborn=row["conditional_lowborn"],
            ), row["native_prestige_delta_raw_q100000"])
            self.assertEqual(row["delta_raw_q100000"], 0)
        self.assertEqual(knight_kill_inverse_prestige_raw(
            victim_primary_title_tier=None, victim_is_lowborn=True), 7_500_000)
        self.assertFalse(report["title_rank_and_lowborn_conditions_proven_for_all_future_events"])
        self.assertFalse(report["planner_usable"])

    def test_kill_trace_recovers_seven_boundaries_without_effect_promotion(self) -> None:
        report = load_episode01_phase_event_kill_trace_recovery()
        self.assertEqual(report["boundary_capture_failure_flags"], [0] * 7)
        self.assertEqual(report["event_appended_between_boundaries"], [4, 5])
        self.assertFalse(report["target_core_before_final_query"]["death_marker_present"])
        self.assertTrue(report["target_core_at_final_query"]["death_marker_present"])
        self.assertEqual(report["target_core_at_final_query"]["current_regiment_id"], 0)
        self.assertEqual(report["target_core_at_final_query"]["prowess"], 2)
        self.assertEqual(report["scheduled_knight_at_final_query"]["regiment_id"], 65)
        self.assertEqual(report["scheduled_knight_at_final_query"]["current_character_id"], -1)
        self.assertEqual(report["killer_prestige_currency_delta"], "150.0000")
        self.assertFalse(report["full_mutable_transition_bundle_complete"])
        self.assertFalse(report["full_event_write_set_proven"])
        self.assertFalse(report["planner_usable"])

    def test_release_build_restores_v3_input_without_planner_promotion(self) -> None:
        report = load_episode01_phase_event_kill_trace_release()
        self.assertEqual(report["v3_phase_event_input_status"], "available")
        self.assertIsNone(report["v3_phase_event_input_unavailable_reason"])
        self.assertEqual(report["boundary_capture_failure_flags"], [0] * 7)
        self.assertTrue(report["target_core_at_final_query"]["death_marker_present"])
        self.assertEqual(report["scheduled_knight_at_final_query"]["current_character_id"], -1)
        self.assertFalse(report["full_mutable_transition_bundle_complete"])
        self.assertFalse(report["planner_usable"])

    def test_conditional_kill_path_records_native_stat_mismatch(self) -> None:
        report = load_episode01_conditional_kill_effect_audit()
        self.assertEqual(report["observed_killer_character_id"], 34120)
        self.assertIn(34120, report["eligible_enemy_character_ids"])
        self.assertTrue(report["conditional_participant_detach_matches_native"])
        self.assertEqual(report["modeled_root_prowess_raw_after"], 400000)
        self.assertEqual(report["native_derived_root_prowess_raw_after"], 200000)
        self.assertFalse(report["native_draw_trace_available"])
        self.assertFalse(report["planner_usable"])

    def test_native_selected_event_row_is_knight_killed_without_draw_proof(self) -> None:
        report = load_episode01_selected_phase_event_row()
        self.assertEqual(report["native_event_global_load_index"], 11)
        self.assertEqual(report["native_event_key"], "knight_killed")
        self.assertEqual(report["mapped_boundaries"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(report["appended_battle_event"]["right_character_id"], 34120)
        self.assertFalse(report["native_effect_internal_draws_observed"])
        self.assertFalse(report["planner_usable"])


if __name__ == "__main__":
    unittest.main()
