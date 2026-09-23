from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.combat_decision_contract import (
    COMBAT_ENTRY_ACTION_COMPONENTS_VERSION,
    COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256,
    COMBAT_ENTRY_EU_ACTIVATION_ENABLED,
    COMBAT_ENTRY_EU_CONTRACT_SHA256,
    COMBAT_ENTRY_EU_CONTRACT_VERSION,
    assess_combat_entry_eu_contract,
    combat_entry_action_components_contract,
    combat_entry_eu_contract,
    _canonical_digest,
    _signed_q100000_product,
)
from xar_autoplayer.simulation.combat_core import wilson_interval_95
from xar_autoplayer.strategy import _qualified_siege_forecast_move


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


def _calculator_inputs(
    *, wins: int = 900, losses: int = 50
) -> tuple[dict[str, object], dict[str, object]]:
    payload = _complete_payload()
    no_resolution = 1_000 - wins - losses
    payload["experiment"].update(
        wins=wins, losses=losses, no_resolution=no_resolution
    )
    payload["distribution"].update(
        player_win_probability_raw=wins * 100,
        player_loss_probability_raw=losses * 100,
        no_resolution_probability_raw=no_resolution * 100,
    )
    wilson = wilson_interval_95(wins, wins + losses)
    assert wilson is not None
    payload["distribution"]["resolved_win_wilson95"] = {
        "low_raw": round(wilson.lower * 100_000),
        "high_raw": round(wilson.upper * 100_000),
    }
    coefficients = payload["utility_policy"]["coefficients_raw"]
    for key in coefficients:
        coefficients[key] = 0
    coefficients.update(player_win=1_000_000, player_loss=-1_000_000)
    payload["utility_policy"]["minimum_attack_margin_raw"] = 50_000
    payload["utility_policy"]["uncertainty_penalty_raw"] = 10_000
    payload["utility_policy"]["opportunity_cost_raw"] = 10_000
    empty = {key: 0 for key in coefficients}
    for side in ("player", "opponent"):
        for key in payload["character_tails"][side]:
            payload["character_tails"][side][key] = 0
    payload["character_tails"]["player_one_life_catastrophic_probability_raw"] = 0
    payload["distribution"]["battle_days"] = {
        "p10": 14, "p50": 14, "p90": 14
    }
    payload["distribution"]["player_hard_losses_raw"] = {
        "p10": 20_000_000, "p50": 20_000_000, "p90": 20_000_000
    }
    payload["distribution"]["enemy_hard_losses_raw"] = {
        "p10": 70_000_000, "p50": 70_000_000, "p90": 70_000_000
    }
    attack_trials = []
    avoid_trials = []
    wait_trials = []
    for ordinal in range(1_000):
        attack_row = dict(empty)
        outcome = (
            "player_win" if ordinal < wins
            else "player_loss" if ordinal < wins + losses
            else "no_resolution"
        )
        attack_row[outcome] = 100_000
        attack_row.update(
            battle_day=1_400_000,
            player_hard_loss=20_000_000,
            enemy_hard_loss=70_000_000,
        )
        attack_row.update({
            key.removesuffix("_raw"): item
            for key, item in payload["campaign_feedback"].items()
        })
        attack_trials.append(attack_row)
        avoid_row = dict(empty)
        avoid_row["no_resolution"] = 100_000
        avoid_trials.append(avoid_row)
        wait_row = dict(empty)
        wait_row["player_win" if ordinal < 600 else "no_resolution"] = 100_000
        wait_trials.append(wait_row)
    payload["experiment"]["per_trial_component_vector_sha256"] = (
        _canonical_digest(attack_trials)
    )
    action_components = {
        "version": COMBAT_ENTRY_ACTION_COMPONENTS_VERSION,
        "identity": copy.deepcopy(payload["identity"]),
        "experiment_input_sha256": payload["experiment"]["input_sha256"],
        "per_trial_component_vector_sha256": payload["experiment"][
            "per_trial_component_vector_sha256"
        ],
        "policy_sha256": payload["utility_policy"]["policy_sha256"],
        "attack_trial_components_raw": attack_trials,
        "alternatives": {
            "avoid": {
                "trial_components_raw": avoid_trials,
                "uncertainty_penalty_raw": 0,
                "opportunity_cost_raw": 0,
            },
            "wait_reinforce": {
                "trial_components_raw": wait_trials,
                "uncertainty_penalty_raw": 0,
                "opportunity_cost_raw": 0,
            },
        },
    }
    return payload, action_components


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
        action_contract = combat_entry_action_components_contract()
        self.assertEqual(
            action_contract["version"], COMBAT_ENTRY_ACTION_COMPONENTS_VERSION
        )
        self.assertEqual(
            action_contract["base_contract_sha256"],
            COMBAT_ENTRY_EU_CONTRACT_SHA256,
        )
        self.assertEqual(len(COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256), 64)

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

    def test_explicit_high_win_can_prefer_attack_below_any_force_ratio(self) -> None:
        payload, actions = _calculator_inputs()
        # The contract contains no troop-ratio gate.  These inputs represent
        # a qualified forecast for a hypothetical 1.5x encounter.
        candidate = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertTrue(candidate["action_components_ready"])
        self.assertEqual(candidate["candidate_action"], "attack")
        self.assertEqual(candidate["eu_attack_raw"], 830_000)
        self.assertEqual(candidate["eu_wait_reinforce_raw"], 600_000)
        self.assertEqual(candidate["attack_margin_raw"], 230_000)
        self.assertEqual(candidate["status"], "calculated_not_activated")
        self.assertIsNone(candidate["selected_action"])
        self.assertFalse(candidate["automatic_attack_enabled"])
        with mock.patch(
            "xar_autoplayer.simulation.combat_decision_contract.COMBAT_ENTRY_EU_ACTIVATION_ENABLED",
            True,
        ):
            hypothetical = assess_combat_entry_eu_contract(
                payload, action_components=actions
            )
        self.assertEqual(hypothetical["selected_action"], "attack")
        self.assertTrue(hypothetical["automatic_attack_enabled"])

    def test_low_win_chooses_explicit_wait_projection(self) -> None:
        payload, actions = _calculator_inputs(wins=300, losses=650)
        candidate = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertTrue(candidate["action_components_ready"])
        self.assertEqual(candidate["candidate_action"], "wait_reinforce")
        self.assertEqual(candidate["dominant_risk"], "resolved_win_wilson_low")
        self.assertIsNone(candidate["selected_action"])
        with mock.patch(
            "xar_autoplayer.simulation.combat_decision_contract.COMBAT_ENTRY_EU_ACTIVATION_ENABLED",
            True,
        ):
            hypothetical = assess_combat_entry_eu_contract(
                payload, action_components=actions
            )
        self.assertEqual(hypothetical["selected_action"], "wait_reinforce")
        self.assertFalse(hypothetical["automatic_attack_enabled"])

    def test_avoid_is_chosen_when_its_explicit_value_exceeds_wait(self) -> None:
        payload, actions = _calculator_inputs(wins=300, losses=650)
        for row in actions["alternatives"]["avoid"]["trial_components_raw"][:700]:
            row["no_resolution"] = 0
            row["player_win"] = 100_000
        candidate = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertEqual(candidate["eu_avoid_raw"], 700_000)
        self.assertEqual(candidate["candidate_action"], "avoid")
        self.assertIsNone(candidate["selected_action"])

    def test_missing_or_stale_alternative_costs_never_default_to_zero(self) -> None:
        payload, actions = _calculator_inputs()
        del actions["alternatives"]["avoid"]["trial_components_raw"]
        incomplete = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertFalse(incomplete["action_components_ready"])
        self.assertIsNone(incomplete["eu_attack_raw"])
        self.assertIn("avoid_projection_schema_invalid", incomplete["action_components_errors"])
        _, fresh_actions = _calculator_inputs()
        fresh_actions["identity"]["target_province_id"] += 1
        stale = assess_combat_entry_eu_contract(
            payload, action_components=fresh_actions
        )
        self.assertIn("action_components_identity_mismatch", stale["action_components_errors"])
        self.assertIsNone(stale["candidate_action"])

    def test_calculator_checks_distribution_counts_and_wilson(self) -> None:
        payload, actions = _calculator_inputs()
        payload["distribution"]["player_win_probability_raw"] -= 100
        payload["distribution"]["player_loss_probability_raw"] += 100
        count_error = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertIn(
            "player_win_probability_raw_trial_count_mismatch",
            count_error["action_components_errors"],
        )
        payload, actions = _calculator_inputs()
        payload["distribution"]["resolved_win_wilson95"]["low_raw"] -= 100
        interval_error = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertIn(
            "resolved_win_wilson95_trial_count_mismatch",
            interval_error["action_components_errors"],
        )

    def test_attack_tape_cannot_disagree_with_published_campaign_mean(self) -> None:
        payload, actions = _calculator_inputs()
        actions["attack_trial_components_raw"][0]["battle_warscore"] += 100_000
        tape_hash = _canonical_digest(actions["attack_trial_components_raw"])
        payload["experiment"]["per_trial_component_vector_sha256"] = tape_hash
        actions["per_trial_component_vector_sha256"] = tape_hash
        result = assess_combat_entry_eu_contract(
            payload, action_components=actions
        )
        self.assertIn(
            "attack_trial_battle_warscore_campaign_mismatch",
            result["action_components_errors"],
        )
        self.assertIsNone(result["eu_attack_raw"])

    def test_signed_fixed_point_truncates_each_component_toward_zero(self) -> None:
        self.assertEqual(_signed_q100000_product(-150_000, 1), -1)
        self.assertEqual(_signed_q100000_product(150_000, -1), -1)
        self.assertEqual(_signed_q100000_product(-50_000, 1), 0)

    def test_under_two_siege_consumer_keeps_complete_forecast_inactive(self) -> None:
        payload = _complete_payload()
        payload["identity"]["player_ordered_army_ids"] = [101]
        frame = {
            **payload["identity"]["observation"],
            "combat_entry_eu_v1": payload,
        }
        decision = _qualified_siege_forecast_move(
            frame, war_id=77, army_id=101, target_province_id=2596,
            entry_province_id=2581, defender_army_ids=(201, 202),
            contact_scope_safe=True,
        )
        self.assertEqual(decision["status"], "contract_blocked")
        self.assertEqual(decision["contract_status"], "blocked_not_activated")
        self.assertIn("combat_entry_eu_activation_not_enabled", decision["blockers"])
        self.assertFalse(assess_combat_entry_eu_contract(payload)["automatic_attack_enabled"])
        frame["native_revision"] = 42
        self.assertEqual(
            _qualified_siege_forecast_move(
                frame, war_id=77, army_id=101,
                target_province_id=2596, entry_province_id=2581,
                defender_army_ids=(201, 202), contact_scope_safe=True,
            )["status"],
            "encounter_identity_mismatch",
        )

    def test_future_qualified_siege_consumer_checks_contact_risk_and_eu(self) -> None:
        # This mocked future calculator tests the strategy seam only.  The
        # actual contract remains inactive and produces no such assessment.
        payload = _complete_payload()
        payload["identity"]["player_ordered_army_ids"] = [101]
        payload["utility_policy"]["minimum_attack_margin_raw"] = 10
        frame = {
            **payload["identity"]["observation"],
            "combat_entry_eu_v1": payload,
        }
        future_assessment = {
            "contract_sha256": COMBAT_ENTRY_EU_CONTRACT_SHA256,
            "assessment_sha256": "E" * 64,
            "external_inputs_ready": True,
            "automatic_attack_enabled": True,
            "decision_status": "selected",
            "selected_action": "attack",
            "eu_attack_raw": 200,
            "eu_avoid_raw": 0,
            "eu_wait_reinforce_raw": 100,
            "attack_margin_raw": 100,
        }

        def decide(*, contact_scope_safe: bool) -> dict[str, object]:
            return _qualified_siege_forecast_move(
                frame, war_id=77, army_id=101,
                target_province_id=2596, entry_province_id=2581,
                defender_army_ids=(201, 202),
                contact_scope_safe=contact_scope_safe,
            )

        with (
            mock.patch(
                "xar_autoplayer.strategy.combat_entry_eu.COMBAT_ENTRY_EU_ACTIVATION_ENABLED",
                True,
            ),
            mock.patch(
                "xar_autoplayer.strategy.combat_entry_eu.assess_combat_entry_eu_contract",
                return_value=future_assessment,
            ),
        ):
            self.assertEqual(decide(contact_scope_safe=False)["status"], "contract_blocked")
            self.assertEqual(decide(contact_scope_safe=True)["status"], "ready")
            future_assessment["attack_margin_raw"] = 99
            self.assertEqual(decide(contact_scope_safe=True)["status"], "contract_blocked")
            future_assessment["attack_margin_raw"] = 100
            payload["distribution"]["resolved_win_wilson95"]["low_raw"] = 60_000
            self.assertEqual(decide(contact_scope_safe=True)["status"], "contract_blocked")


if __name__ == "__main__":
    unittest.main()
