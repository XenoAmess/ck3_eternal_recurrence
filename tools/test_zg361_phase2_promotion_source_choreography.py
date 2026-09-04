#!/usr/bin/env python3
"""Static contract for the real zg361pp.147 source choreography.

This test reads only committed source and the frozen seed contract.  It never
starts CK3 and deliberately fails if a future capability changes the currently
documented gap without updating the forensic contract.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
MOD = ROOT / "mod_zhongguo_style"
CONTRACT = json.loads(
    (TOOLS / "zg361_phase2_promotion_source_choreography_contract.json").read_text(
        encoding="utf-8-sig"
    )
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


class PromotionSourceChoreographyForensicsTests(unittest.TestCase):
    def test_frozen_seed_identity_and_honest_gap(self) -> None:
        seed = json.loads(
            (TOOLS / "zg361_phase2_seed_contract.json").read_text(
                encoding="utf-8-sig"
            )
        )
        expected = CONTRACT["canonical_seed"]
        self.assertEqual(seed["status"], expected["status"])
        self.assertEqual(seed["source"]["bytes"], expected["bytes"])
        self.assertEqual(seed["source"]["sha256"], expected["sha256"])
        self.assertEqual(seed["saved_state"]["date_raw"], expected["date_raw"])
        self.assertEqual(
            seed["saved_state"]["played_character_id"],
            expected["played_character_id"],
        )
        self.assertEqual(
            seed["saved_state"]["player_history_id"],
            expected["player_history_id"],
        )
        self.assertFalse(expected["played_character_promotion_prefix_observed"])
        self.assertIn(
            "no player-owned B1/central/PP stage provider",
            " ".join(CONTRACT["remaining_unknowns"]),
        )

    def test_product_entry_to_central_stage_three_graph_is_intact(self) -> None:
        decisions = text(MOD / "common" / "decisions" / "zg361_decisions.txt")
        scripted_gui = text(
            MOD / "common" / "scripted_guis" / "zg361_scoreboard_guis.txt"
        )
        b1 = text(
            MOD / "common" / "scripted_effects" / "zg361_b1_runtime_effects.txt"
        )
        b1_events = text(MOD / "events" / "zg361_b1_runtime_events.txt")
        publication = text(
            ROOT
            / "tools"
            / "frozen"
            / "zg361_phase2_b2_core"
            / "common"
            / "scripted_effects"
            / "zg361_core_review_cycle_effects.txt"
        )
        canonical_publication = text(
            MOD / "common" / "scripted_effects" / "zg361_effects.txt"
        )
        lifecycle = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_phase2_central_004_lifecycle_hooks_effects.txt"
        )
        pump = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_phase2_central_010_serial_pump_effects.txt"
        )
        stages = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_phase2_central_005_stage01_03_effects.txt"
        )

        self.assertIn("zg361_review_now_decision = {", decisions)
        self.assertIn("add_character_flag = zg361_review_now_pending", decisions)
        self.assertIn("remove_character_flag = zg361_review_now_pending", scripted_gui)
        self.assertIn("zg361_b1_open_cycle_effect = yes", scripted_gui)
        self.assertIn("trigger_event = { id = zg361b1.100 days = 180 }", b1)
        self.assertIn("trigger_event = { id = zg361b1.101 days = 60 }", b1_events)
        self.assertIn("trigger_event = { id = zg361b1.102 days = 60 }", b1_events)
        self.assertIn("zg361_run_review_effect = yes", b1_events)
        self.assertIn("trigger_event = { id = zg361b1.103 days = 30 }", b1)
        # The inherited B2 shard predates the central hook.  B3 must source the
        # current body from the canonical owner instead of mistaking the old
        # same-name definition for a complete provider.
        self.assertNotIn("zg361_p2c_on_review_published_effect = yes", publication)
        self.assertIn(
            "zg361_p2c_on_review_published_effect = yes", canonical_publication
        )
        expander = text(TOOLS / "expand_zg361_phase2_b3_projection_closure.py")
        self.assertIn("synchronize_current_core_effect_shards", expander)
        self.assertIn("set_variable = { name = zg361_p2c_stage value = 1 }", lifecycle)
        self.assertIn("zg361_p2c_schedule_pump_effect = { DAYS = 2 }", lifecycle)

        stage_1 = pump.index(
            "var:zg361_p2c_stage = 1 } zg361_p2c_stage_01_career_hc_effect"
        )
        stage_2 = pump.index(
            "var:zg361_p2c_stage = 2 } zg361_p2c_stage_02_compensation_effect"
        )
        stage_3 = pump.index(
            "var:zg361_p2c_stage = 3 } zg361_p2c_stage_03_feedback_promotion_pip_effect"
        )
        self.assertLess(stage_1, stage_2)
        self.assertLess(stage_2, stage_3)
        self.assertIn("zg361_p2c_call_pp_adapter_effect = yes", stages)

    def test_first_t_prompt_has_a_one_day_revision_bound_suffix(self) -> None:
        t_stage = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_feedback_promotion_pip_003_t_stages_01_effects.txt"
        )
        lifecycle = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_feedback_promotion_pip_015_t_m146_m147_lifecycle_effects.txt"
        )
        events = text(
            MOD / "events" / "zg361_feedback_promotion_pip_runtime_events.txt"
        )
        m146, m147_and_later = events.split("# 147:", 1)
        m147, _later = m147_and_later.split("# 148:", 1)

        self.assertIn("zg361_pp_open_t_case_effect = {", t_stage)
        self.assertIn(
            "set_variable = { name = zg361_pp_t_operation_capacity_available value = 11 }",
            t_stage,
        )
        self.assertIn(
            "set_variable = { name = zg361_pp_t_capacity_hours_available value = 10 }",
            t_stage,
        )
        self.assertIn("trigger_event = { id = zg361pp.146 days = 1 }", t_stage)
        self.assertIn("var:zg361_pp_t_operation_capacity_available >= 1", lifecycle)
        self.assertIn("var:zg361_pp_t_capacity_hours_available >= 1", lifecycle)
        self.assertEqual(m146.count("var:zg361_pp_m146_consumed = 1"), 3)
        self.assertEqual(
            m146.count("trigger_event = { id = zg361pp.147 days = 1 }"), 3
        )
        for suffix in ("a", "b", "c"):
            self.assertIn(f"name = zg361pp.147.{suffix}", m147)
        self.assertIn("ROUTE = 1", m147)

        suffix = CONTRACT["shortest_proven_executable_suffix"]
        self.assertIn("zg361pp.146", suffix["starts_at"])
        self.assertEqual(suffix["steps"][0]["action"], "select-event-option-1")
        self.assertEqual(suffix["steps"][1]["minimum_timeline_advance_days"], 1)
        self.assertEqual(suffix["steps"][-1]["action"], "save-checkpoint")

    def test_runner_can_execute_suffix_and_product_decision_entry(self) -> None:
        runner = text(TOOLS / "run_zhongguo_acceptance.py")
        scoreboard = text(
            ROOT
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "bridge"
            / "zhongguo_scoreboard_action_contract.py"
        )
        action_cell = text(
            TOOLS / "zg361_phase2_promotion_compensation_action_cell.py"
        )

        for token in (
            '"game.command.pause-map"',
            '"game.command.resume-map"',
            '"game.command.set-speed-1"',
            '"game.command.select-event-option-N"',
            '"game.command.save-checkpoint"',
            '"bounded_life_advance": "life-advance"',
        ):
            self.assertIn(token, runner)
        self.assertIn("enter_promotion_source_checkpoint_v1", runner)
        self.assertIn("phase2_promotion_source_capture_live", runner)
        for action in (
            '"open"',
            '"switch-managed"',
            '"switch-received"',
            '"switch-system"',
            '"close"',
            '"reopen"',
        ):
            self.assertIn(action, scoreboard)
        self.assertNotIn("review_now_decision", scoreboard)
        self.assertTrue(
            CONTRACT["unavailable_required_entry"]["phase2_runner_capability_present"]
        )
        self.assertEqual(
            CONTRACT["unavailable_required_entry"]["status"],
            "static-ready-default-off-live-pending",
        )
        self.assertIn("SOURCE_EVENT_DEFINITION_KEY: Final = \"zg361pp.147\"", action_cell)
        self.assertIn("SOURCE_OPTION_NUMBER: Final = 1", action_cell)
        self.assertIn('"action_ack_is_business_postcondition": False', action_cell)

    def test_capture_boundary_is_product_only_and_no_launch(self) -> None:
        acceptance = CONTRACT["capture_acceptance"]
        self.assertTrue(acceptance["product_only_mount"])
        self.assertTrue(acceptance["provider_observed"])
        self.assertTrue(acceptance["ui_state_verified"])
        self.assertFalse(acceptance["fixture_used"])
        self.assertFalse(acceptance["console_used"])
        self.assertFalse(acceptance["generic_character_rebind_used"])
        self.assertTrue(acceptance["source_option_must_remain_unselected"])
        self.assertFalse(CONTRACT["ack_boundary"]["action_ack_is_source_checkpoint"])
        self.assertFalse(
            CONTRACT["ack_boundary"]["action_ack_is_business_postcondition"]
        )
        self.assertFalse(CONTRACT["no_launch"]["ck3_started"])
        self.assertTrue(CONTRACT["no_launch"]["runner_modified"])


if __name__ == "__main__":
    unittest.main()
