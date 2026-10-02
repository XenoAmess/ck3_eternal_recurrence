"""A historical WAR31 option cannot decide the later Robert war exit."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.formal_defender_exit_observation import (  # noqa: E402
    observe_primary_defender_de_jure_exit,
)
from xar_autoplayer import strategy  # noqa: E402


EVIDENCE = ROOT / "docs" / "autonomous-agent-progress" / "coordination" / "war-requests" / "evidence" / "WAR-INPUT-R0221-WAR31-20260927.termination-options.json"


def _h2743_snapshot() -> dict[str, object]:
    return {
        "paused": True,
        "active_event": None,
        "pending_character_interaction": None,
        "snapshot_id": "native:30",
        "revision": 31,
        "native_revision": 30,
        "date_raw": 53217264,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "diagnostics": {"connection_generation": 1},
        "played_character": {"character_id": 29829},
        "active_wars": [{
            "war_id": 16777231,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
            "player_relative_war_score": -12,
        }],
        "war_termination_options": [],
    }


def _h2743_snapshot_with_current_options() -> dict[str, object]:
    snapshot = _h2743_snapshot()
    historical = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    options = copy.deepcopy(historical["war_termination_options"])
    options["player_relative_war_score"] = -12
    options["attacker_war_score"] = 12
    options["defender_war_score"] = -12
    options["war_score_breakdown"]["occupation"] = 36
    snapshot["war_termination_options"] = [{
        **options,
        "query_sequence": 1,
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"],
        "queried_connection_generation": 1,
        "episode_run_id": snapshot["episode_run_id"],
    }]
    return snapshot


class FormalDefenderExitObservationTests(unittest.TestCase):
    def test_formal_turn_preserves_bounded_tactical_candidate_without_exit_authority(self) -> None:
        original_plan = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_route",
            "selected_step": "advance-route-contact-horizon-v1-candidate",
        }
        with (
            patch.object(strategy, "_choose_one_life_turn_core", return_value=original_plan),
            patch.object(strategy, "_primary_defender_siege_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_general_battle_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_annotate_active_combat_resume_input", side_effect=lambda plan, _: plan),
        ):
            plan = strategy.choose_one_life_turn(
                [], snapshot=_h2743_snapshot_with_current_options(),
                action_steps=[original_plan["selected_step"]],
            )
        self.assertEqual(plan["selected_step"], original_plan["selected_step"])
        handoff = plan["formal_defender_exit_observation"]["continuation_handoff"]
        self.assertEqual(handoff["candidate_selected_step"], original_plan["selected_step"])
        self.assertTrue(handoff["current_frame_revalidation_required"])
        self.assertFalse(handoff["exit_action_authorized"])

    def test_other_war_terminal_step_is_not_blocked_by_this_war(self) -> None:
        selected_step = "surrender-war-16777232"
        original_plan = {"policy": "one-life-turn-v1", "selected_step": selected_step}
        with (
            patch.object(strategy, "_choose_one_life_turn_core", return_value=original_plan),
            patch.object(strategy, "_primary_defender_siege_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_general_battle_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_annotate_active_combat_resume_input", side_effect=lambda plan, _: plan),
        ):
            plan = strategy.choose_one_life_turn(
                [], snapshot=_h2743_snapshot_with_current_options(),
                action_steps=[selected_step],
            )
        self.assertEqual(plan["selected_step"], selected_step)
        self.assertIsNone(
            plan["formal_defender_exit_observation"]["continuation_handoff"]
            ["candidate_selected_step"]
        )

    def test_readonly_exit_metadata_preserves_current_native_emergency_policy(self) -> None:
        selected_step = "surrender-war-16777231"
        original_plan = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_de_jure_emergency_exit",
            "selected_step": selected_step,
            "decision": {"policy": "de-jure-no-safe-route-emergency-exit-v1"},
        }
        with (
            patch.object(strategy, "plan_raiktor_formal_exit", return_value=None),
            patch.object(strategy, "_choose_one_life_turn_core", return_value=original_plan),
            patch.object(strategy, "_primary_defender_siege_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_general_battle_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_annotate_active_combat_resume_input", side_effect=lambda plan, _: plan),
        ):
            plan = strategy.choose_one_life_turn(
                [], snapshot=_h2743_snapshot_with_current_options(),
                action_steps=[selected_step],
            )
        self.assertEqual(plan["selected_step"], selected_step)
        self.assertEqual(plan["decision"], original_plan["decision"])
        handoff = plan["formal_defender_exit_observation"]["continuation_handoff"]
        self.assertEqual(handoff["status"], "no_tactical_candidate")
        self.assertIsNone(handoff["candidate_selected_step"])
        self.assertFalse(handoff["exit_action_authorized"])

    def test_h2743_excerpt_requires_its_own_native_options(self) -> None:
        result = observe_primary_defender_de_jure_exit(_h2743_snapshot())
        self.assertEqual(result["status"], "current_native_options_required")
        self.assertEqual(
            result["required_observation_step"],
            "query-war-termination-options-16777231",
        )
        self.assertIsNone(result["action_literal"])
        self.assertIsNone(result["recommended_outcome"])

    def test_historical_r0221_options_are_rejected_on_h2743(self) -> None:
        snapshot = _h2743_snapshot()
        historical = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        snapshot["war_termination_options"] = [{
            **historical["war_termination_options"],
            "query_sequence": historical["query_sequence"],
            "queried_snapshot_id": historical["queried_snapshot_id"],
            "queried_revision": historical["queried_revision"],
            "queried_native_revision": historical["queried_native_revision"],
            "queried_connection_generation": historical["queried_connection_generation"],
            "episode_run_id": historical["queried_episode_run_id"],
        }]
        result = observe_primary_defender_de_jure_exit(snapshot)
        self.assertEqual(result["status"], "observation_red")
        self.assertEqual(result["reason"], "native_options_frame_or_cardinality_mismatch")
        self.assertIsNone(result["action_literal"])

    def test_current_frame_legality_does_not_fill_unknown_material_terms(self) -> None:
        result = observe_primary_defender_de_jure_exit(
            _h2743_snapshot_with_current_options()
        )
        self.assertEqual(
            result["status"],
            "native_legality_observed_material_comparison_open",
        )
        self.assertTrue(result["options"]["surrender"]["native_legal_now"])
        self.assertFalse(result["options"]["surrender"]["material_terms_observable"])
        self.assertIsNone(result["material_terms"]["signed_actor_and_opponent_resources"])
        self.assertEqual(result["decision_readiness"]["status"], "exit_selection_blocked")
        self.assertEqual(result["decision_readiness"]["legal_outcomes_now"], ["surrender"])
        self.assertFalse(result["decision_readiness"]["generic_claim_cb_terms_query_applicable"])
        self.assertIsNone(result["recommended_outcome"])
        self.assertIsNone(result["action_literal"])

    def test_formal_turn_attaches_read_only_observation_to_tactical_plan(self) -> None:
        original_plan = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_termination_query",
            "selected_step": "query-war-termination-options-16777231",
        }
        with (
            patch.object(strategy, "_choose_one_life_turn_core", return_value=original_plan),
            patch.object(strategy, "_primary_defender_siege_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_general_battle_forecast_ingress", side_effect=lambda plan, **_: plan),
            patch.object(strategy, "_annotate_active_combat_resume_input", side_effect=lambda plan, _: plan),
        ):
            plan = strategy.choose_one_life_turn(
                [], snapshot=_h2743_snapshot(),
                action_steps=["query-war-termination-options-16777231"],
            )
        self.assertEqual(plan["selected_step"], original_plan["selected_step"])
        self.assertEqual(
            plan["formal_defender_exit_observation"]["status"],
            "current_native_options_required",
        )


if __name__ == "__main__":
    unittest.main()
