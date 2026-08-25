from __future__ import annotations

from pathlib import Path
import unittest

from xar_autoplayer.simulation.combat_core import CURRENT_BOUNDED_CORE_MANIFEST
from xar_autoplayer.simulation.combat_core import CombatExperiment
from xar_autoplayer.simulation.combat_input import (
    engagement_readiness,
    load_live_combat_fixture,
)
from xar_autoplayer.simulation.research_envelope import (
    ResearchEnvelopeAssumptions,
    run_research_envelope_experiment,
)


FIXTURES = Path(__file__).parents[1] / "fixtures" / "combat"


class LiveCombatInputAdapterTests(unittest.TestCase):
    def _load(self, name: str):
        return load_live_combat_fixture(FIXTURES / name)

    def test_defensive_single_and_combined_live_inputs_are_frozen(self) -> None:
        single = self._load("live_rev4_vs_357.json")
        combined = self._load("live_rev4_vs_combined.json")
        self.assertEqual(single.capture_snapshot_id, "native:3")
        self.assertEqual(single.capture_revision, 4)
        self.assertEqual(single.capture_native_revision, 3)
        self.assertEqual(single.capture_date_raw, 53_175_816)
        self.assertTrue(single.input_observation_ready)
        self.assertFalse(single.native_monte_carlo_ready)
        self.assertEqual(single.encounter.target_province_id, 2596)
        self.assertEqual(single.encounter.attacker_side, "enemy")
        self.assertEqual(single.encounter.defender_side, "player_or_allied")
        self.assertFalse(single.encounter.holding_defender)
        self.assertEqual(single.encounter.terrain_key, "hills")
        self.assertEqual(single.encounter.terrain_width_multiplier_raw, 80_000)
        self.assertEqual(single.encounter.crossing_kind, "none")
        self.assertEqual(single.encounter.final_width, 1312)
        self.assertEqual(combined.encounter.final_width, 1717)
        self.assertEqual(combined.encounter.attacker_army_ids, (357, 33_554_657))
        self.assertNotEqual(single.input_sha256, combined.input_sha256)

    def test_offensive_live_inputs_preserve_player_attacker_and_holding(self) -> None:
        single = self._load("live_rev4_player_attacks_357.json")
        combined = self._load("live_rev4_player_attacks_combined.json")
        self.assertEqual(single.encounter.target_province_id, 2581)
        self.assertEqual(single.encounter.attacker_entry_province_id, 2587)
        self.assertEqual(single.encounter.attacker_side, "player_or_allied")
        self.assertEqual(single.encounter.defender_side, "enemy")
        self.assertTrue(single.encounter.holding_defender)
        self.assertEqual(single.encounter.final_width, 1312)
        self.assertEqual(combined.encounter.final_width, 1717)
        self.assertEqual(single.encounter.attacker_army_ids, (83_886_341,))
        self.assertEqual(combined.encounter.defender_army_ids, (357, 33_554_657))

    def test_live_army_census_stats_commander_and_knights_match_capture(self) -> None:
        combined = self._load("live_rev4_vs_combined.json")
        armies = {army.public_army_id: army for army in combined.armies}
        expected = {
            83_886_341: (1482, 1472, 38, 35, 12, 85),
            357: (1801, 1783, 23, 14, 6, 64),
            33_554_657: (1011, 1001, 22, 28, 7, 72),
        }
        for army_id, values in expected.items():
            army = armies[army_id]
            observed = (
                army.current_soldiers,
                army.main_phase_soldiers,
                len(army.regiments),
                army.commander.generic_advantage_points,
                len(army.knights),
                sum(knight.prowess for knight in army.knights),
            )
            self.assertEqual(observed, values)
            self.assertEqual(
                (
                    army.commander.effective_min_roll,
                    army.commander.effective_max_roll,
                ),
                (0, 10),
            )

    def test_counter_vectors_and_initial_entry_projection_are_value_complete(self) -> None:
        combined = self._load("live_rev4_player_attacks_combined.json")
        self.assertEqual(len(combined.counter_resolutions), 2)
        self.assertEqual(
            tuple(
                len(row.damage_retention_by_class_raw)
                for row in combined.counter_resolutions
            ),
            (13, 13),
        )
        player_entries = combined.initial_entries_for_side("player_or_allied")
        enemy_entries = combined.initial_entries_for_side("enemy")
        self.assertEqual(len(player_entries), 38)
        self.assertEqual(len(enemy_entries), 45)
        self.assertEqual(
            sum(entry.current_raw for entry in player_entries), 1472 * 100_000
        )
        self.assertEqual(
            sum(entry.soft_casualties_raw for entry in player_entries),
            10 * 100_000,
        )
        self.assertGreater(
            combined.counter_adjusted_damage_raw("player_or_allied"), 0
        )
        self.assertGreater(combined.counter_adjusted_damage_raw("enemy"), 0)

    def test_dynamic_counter_recompute_matches_all_independent_live_vectors(self) -> None:
        names = (
            "live_rev4_vs_357.json",
            "live_rev4_vs_33554657.json",
            "live_rev4_vs_combined.json",
            "live_rev4_player_attacks_357.json",
            "live_rev4_player_attacks_combined.json",
        )
        for name in names:
            with self.subTest(name=name):
                combat_input = self._load(name)
                entries = {
                    side: combat_input.initial_entries_for_side(side)
                    for side in ("player_or_allied", "enemy")
                }
                for resolution in combat_input.counter_resolutions:
                    observed = combat_input.dynamic_counter_retention_by_class_raw(
                        resolution.countered_side,
                        entries[resolution.countered_side],
                        entries[resolution.countering_side],
                    )
                    self.assertEqual(
                        observed,
                        resolution.damage_retention_by_class_raw,
                    )

    def test_both_defensive_and_offensive_inputs_fail_closed_for_active_attack(self) -> None:
        names = (
            "live_rev4_vs_357.json",
            "live_rev4_vs_combined.json",
            "live_rev4_player_attacks_357.json",
            "live_rev4_player_attacks_combined.json",
        )
        for name in names:
            with self.subTest(name=name):
                readiness = engagement_readiness(
                    self._load(name), CURRENT_BOUNDED_CORE_MANIFEST
                )
                self.assertTrue(readiness.input_observation_ready)
                self.assertFalse(readiness.transition_fidelity_gate)
                self.assertFalse(readiness.planner_usable)
                self.assertFalse(readiness.active_attack_allowed)
                self.assertEqual(readiness.forecast_status, "unavailable")
                self.assertEqual(readiness.sample_count, 0)
                self.assertIn(
                    "loaded_phase_event_effect_transition", readiness.reasons
                )

    def test_research_envelope_runs_but_never_becomes_planner_usable(self) -> None:
        single = self._load("live_rev4_player_attacks_357.json")
        assumptions = ResearchEnvelopeAssumptions(
            attacker_commander_army_id=83_886_341,
            defender_commander_army_id=357,
        )
        experiment = CombatExperiment(single.input_sha256, 42, 8, 120)
        first = run_research_envelope_experiment(
            single, experiment, assumptions, max_workers=1
        )
        second = run_research_envelope_experiment(
            single, experiment, assumptions, max_workers=1
        )
        self.assertEqual(first, second)
        self.assertEqual(first.sample_count, 8)
        self.assertEqual(first.player_wins + first.player_losses + first.no_resolution, 8)
        self.assertFalse(first.fidelity_gate)
        self.assertFalse(first.planner_usable)
        self.assertEqual(first.model_fidelity, "research-only-bounded-core")


if __name__ == "__main__":
    unittest.main()
