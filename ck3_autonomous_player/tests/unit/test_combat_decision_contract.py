from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.combat_decision_contract import (
    COMBAT_ENTRY_EU_ACTIVATION_ENABLED,
    COMBAT_ENTRY_EU_CONTRACT_SHA256,
    COMBAT_ENTRY_EU_CONTRACT_VERSION,
    assess_combat_entry_eu_contract,
    combat_entry_eu_contract,
)


def _complete_payload() -> dict[str, object]:
    identity = {
        "episode_run_id": "episode-17",
        "snapshot_id": "native:41",
        "revision": 9,
        "native_revision": 41,
    }
    tail = {
        "commander_wound_probability_raw": 1_000,
        "commander_maim_probability_raw": 500,
        "commander_death_probability_raw": 100,
        "knight_wound_probability_raw": 2_000,
        "knight_maim_probability_raw": 750,
        "knight_death_probability_raw": 250,
        "detach_or_capture_probability_raw": 300,
    }
    coefficient_keys = combat_entry_eu_contract()["utility_coefficient_keys"]
    return {
        "identity": {
            "observation": copy.deepcopy(identity),
            "forecast": copy.deepcopy(identity),
            "target_province_id": 2596,
            "entry_province_id": 2581,
            "war_id": 77,
            "player_war_side": 0,
            "player_ordered_army_ids": [101, 102],
            "opponent_ordered_army_ids": [201, 202],
        },
        "fidelity": {
            "loaded_playset_verified": True,
            "ast_evaluator_ready": True,
            "original_trace_ready": True,
            "transition_fidelity_gate": True,
            "monte_carlo_ready": True,
            "planner_usable": True,
            "active_attack_allowed": True,
        },
        "experiment": {
            "simulator_version": "future-exact-v1",
            "simulator_sha256": "A" * 64,
            "input_sha256": "B" * 64,
            "per_trial_component_vector_sha256": "C" * 64,
            "seed_u64": 42,
            "trial_count": 1_000,
            "horizon_days": 90,
            "wins": 900,
            "losses": 50,
            "no_resolution": 50,
        },
        "distribution": {
            "player_win_probability_raw": 90_000,
            "player_loss_probability_raw": 5_000,
            "no_resolution_probability_raw": 5_000,
            "resolved_win_wilson95": {"low_raw": 88_000, "high_raw": 92_000},
            "battle_days": {"p10": 8, "p50": 14, "p90": 28},
            "player_hard_losses_raw": {
                "p10": 10_000_000,
                "p50": 20_000_000,
                "p90": 40_000_000,
            },
            "enemy_hard_losses_raw": {
                "p10": 40_000_000,
                "p50": 70_000_000,
                "p90": 100_000_000,
            },
            "player_stack_wipe_probability_raw": 100,
        },
        "character_tails": {
            "player": copy.deepcopy(tail),
            "opponent": copy.deepcopy(tail),
            "player_one_life_catastrophic_probability_raw": 100,
        },
        "campaign_feedback": {
            "battle_warscore_raw": 500_000,
            "objective_siege_tempo_raw": 200_000,
            "reinforcement_route_raw": 100_000,
            "supply_attrition_raw": -100_000,
            "replacement_gold_time_raw": -150_000,
            "exit_option_value_raw": 50_000,
        },
        "utility_policy": {
            "policy_version": "one-life-risk-v1",
            "policy_sha256": "D" * 64,
            "action_alternatives": ["attack", "avoid", "wait_reinforce"],
            "coefficients_raw": {key: 100_000 for key in coefficient_keys},
            "risk_constraints": {
                "max_player_stack_wipe_probability_raw": 1_000,
                "max_player_one_life_catastrophic_probability_raw": 500,
                "min_resolved_win_wilson_low_raw": 70_000,
            },
            "uncertainty_penalty_raw": 10_000,
            "opportunity_cost_raw": 10_000,
            "minimum_attack_margin_raw": 100_000,
        },
    }


class CombatDecisionContractTests(unittest.TestCase):
    def test_field_inventory_and_contract_hash_are_frozen(self) -> None:
        contract = combat_entry_eu_contract()
        self.assertEqual(contract["version"], "combat-entry-eu-v1")
        self.assertEqual(COMBAT_ENTRY_EU_CONTRACT_VERSION, contract["version"])
        self.assertEqual(len(contract["fidelity_gates"]), 7)
        self.assertEqual(
            contract["probability_partition"],
            [
                "player_win_probability_raw",
                "player_loss_probability_raw",
                "no_resolution_probability_raw",
            ],
        )
        self.assertIn(
            "character_tails.player.commander_death_probability_raw",
            contract["required_paths"],
        )
        self.assertIn(
            "campaign_feedback.exit_option_value_raw",
            contract["required_paths"],
        )
        self.assertEqual(len(COMBAT_ENTRY_EU_CONTRACT_SHA256), 64)
        self.assertFalse(COMBAT_ENTRY_EU_ACTIVATION_ENABLED)

    def test_even_favorable_complete_inputs_cannot_select_attack(self) -> None:
        result = assess_combat_entry_eu_contract(_complete_payload())
        self.assertTrue(result["external_inputs_ready"])
        self.assertEqual(result["status"], "blocked_not_activated")
        self.assertEqual(result["decision_status"], "blocked")
        self.assertIsNone(result["selected_action"])
        self.assertIsNone(result["eu_attack_raw"])
        self.assertFalse(result["automatic_attack_enabled"])
        self.assertEqual(
            result["blockers"], ["combat_entry_eu_activation_not_enabled"]
        )

    def test_current_ast_and_trace_gates_block_before_any_eu(self) -> None:
        payload = _complete_payload()
        payload["fidelity"]["ast_evaluator_ready"] = False
        payload["fidelity"]["original_trace_ready"] = False
        result = assess_combat_entry_eu_contract(payload)
        self.assertFalse(result["fidelity_gates_ready"])
        self.assertFalse(result["external_inputs_ready"])
        self.assertIn("fidelity_gates_not_ready", result["blockers"])
        self.assertIsNone(result["selected_action"])

    def test_identity_drift_fails_same_frame_contract(self) -> None:
        payload = _complete_payload()
        payload["identity"]["forecast"]["native_revision"] += 1
        result = assess_combat_entry_eu_contract(payload)
        self.assertFalse(result["same_frame_identity_ready"])
        self.assertIn(
            "identity.observation_and_forecast_mismatch",
            result["validation_errors"],
        )
        self.assertIsNone(result["selected_action"])

    def test_no_resolution_partition_and_trial_accounting_are_mandatory(self) -> None:
        payload = _complete_payload()
        payload["distribution"]["no_resolution_probability_raw"] = 0
        payload["experiment"]["no_resolution"] = 0
        result = assess_combat_entry_eu_contract(payload)
        self.assertFalse(result["probability_partition_ready"])
        self.assertFalse(result["trial_accounting_ready"])
        self.assertIn("probability_partition_not_ready", result["blockers"])
        self.assertIn("trial_accounting_not_ready", result["blockers"])
        self.assertIsNone(result["selected_action"])

    def test_missing_inventory_is_reported_without_inventing_defaults(self) -> None:
        result = assess_combat_entry_eu_contract({})
        self.assertEqual(result["status"], "blocked_incomplete_or_invalid")
        self.assertIn("experiment.no_resolution", result["missing_required_paths"])
        self.assertIn(
            "character_tails.player_one_life_catastrophic_probability_raw",
            result["missing_required_paths"],
        )
        self.assertFalse(result["external_inputs_ready"])
        self.assertIsNone(result["selected_action"])

    def test_unknown_field_fails_exact_schema_closed(self) -> None:
        payload = _complete_payload()
        payload["distribution"]["resolved_win_probability_raw"] = 94_736
        result = assess_combat_entry_eu_contract(payload)
        self.assertIn(
            "distribution.resolved_win_probability_raw_unexpected",
            result["validation_errors"],
        )
        self.assertFalse(result["external_inputs_ready"])
        self.assertFalse(result["automatic_attack_enabled"])
        self.assertIsNone(result["selected_action"])


if __name__ == "__main__":
    unittest.main()
