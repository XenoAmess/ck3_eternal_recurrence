from __future__ import annotations

import unittest

from xar_autoplayer.simulation.combat_core import (
    CURRENT_BOUNDED_CORE_MANIFEST,
    BackingComponent,
    BattleEndBranch,
    CombatExperiment,
    CombatPhase,
    CombatRegimentState,
    CommanderRollRequest,
    DrawState,
    FIXED_SCALE,
    PhaseEventCandidate,
    PursuitInitialPools,
    RegimentKind,
    RetreatBlockReason,
    RetreatGateInput,
    TransitionFidelityManifest,
    TrialOutcome,
    TrialRandomStreams,
    TrialResult,
    allocate_attacker_hard_credit,
    allocate_hard_casualties_to_components,
    apply_main_phase_casualties,
    apply_forced_winner_effect,
    apply_pursuit_day,
    apply_three_day_pursuit,
    avalanche32,
    fire_phase_event_seeds,
    fixed_div,
    fixed_mul,
    phase_schedule_state,
    run_combat_experiment,
    schedule_main_day_randomness,
    schedule_battle_result_envelopes,
    select_phase_event,
    summarize_trial_outcomes,
    transition_after_winner_is_known,
    trunc_div_toward_zero,
    weighted_choice_index,
    winner_at_main_tick_start,
    evaluate_can_retreat,
    forced_winner_side,
)


class CombatFixedPointTests(unittest.TestCase):
    def test_signed_operations_truncate_toward_zero(self) -> None:
        self.assertEqual(trunc_div_toward_zero(-7, 3), -2)
        self.assertEqual(trunc_div_toward_zero(7, -3), -2)
        self.assertEqual(fixed_mul(-150_001, 50_000), -75_000)
        self.assertEqual(fixed_div(-100_001, 300_000), -33_333)
        self.assertEqual(fixed_div(1, 0), -1)

    def test_component_golden_vector_preserves_fractional_remainder(self) -> None:
        levy = allocate_hard_casualties_to_components(
            (BackingComponent(3, 3), BackingComponent(5, 5)),
            456_516,
        )
        maa = allocate_hard_casualties_to_components(
            (BackingComponent(2, 2), BackingComponent(5, 5)),
            579_461,
        )
        self.assertEqual(
            tuple(item.current_soldiers for item in levy.components), (0, 4)
        )
        self.assertEqual(levy.whole_soldier_losses, (3, 1))
        self.assertEqual(
            tuple(item.current_soldiers for item in maa.components), (0, 2)
        )
        self.assertEqual(maa.whole_soldier_losses, (2, 3))


class MainCasualtyGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = (
            CombatRegimentState(
                regiment_id=1,
                kind=RegimentKind.LEVY,
                current_raw=40_000_000,
                soft_casualties_raw=0,
                toughness_raw=1_100_000,
                components=(BackingComponent(3, 3), BackingComponent(5, 5)),
            ),
            CombatRegimentState(
                regiment_id=2,
                kind=RegimentKind.MEN_AT_ARMS,
                current_raw=60_000_000,
                soft_casualties_raw=0,
                toughness_raw=1_300_000,
                components=(BackingComponent(2, 2), BackingComponent(5, 5)),
            ),
        )

    def test_mixed_levy_maa_original_formula_vector(self) -> None:
        result = apply_main_phase_casualties(
            self.entries,
            incoming_damage_raw=31_000_000,
            defending_total_fighting_men_raw=100_000_000,
            defending_hard_modifier_raw=10_000,
            attacking_enemy_hard_modifier_raw=20_000,
            combat_hard_winter_raw=5_000,
        )
        self.assertEqual(result.conversion_raw, 40_500)
        self.assertEqual(
            tuple(row.total_raw for row in result.rows), (1_127_200, 1_430_769)
        )
        self.assertEqual(
            tuple(row.hard_raw for row in result.rows), (456_516, 579_461)
        )
        self.assertEqual(
            tuple(row.soft_raw for row in result.rows), (670_684, 851_308)
        )
        self.assertEqual(result.total_hard_raw, 1_035_977)
        self.assertEqual(
            tuple(
                tuple(component.current_soldiers for component in entry.components)
                for entry in result.entries
            ),
            ((0, 4), (0, 2)),
        )

    def test_attribution_remainder_is_not_refilled(self) -> None:
        first = allocate_attacker_hard_credit(
            (18_000_000, 13_000_000),
            hard_raw=456_516,
            incoming_damage_raw=31_000_000,
        )
        second = allocate_attacker_hard_credit(
            (18_000_000, 13_000_000),
            hard_raw=579_461,
            incoming_damage_raw=31_000_000,
        )
        self.assertEqual(first, (265_073, 191_442))
        self.assertEqual(second, (336_461, 242_999))
        totals = tuple(left + right for left, right in zip(first, second))
        self.assertEqual(totals, (601_534, 434_441))
        self.assertEqual(sum(totals), 1_035_975)


class PursuitGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.retreater = (
            CombatRegimentState(
                1, RegimentKind.LEVY, 0, 35_000_000, 1_000_000
            ),
            CombatRegimentState(
                2, RegimentKind.LEVY, 0, 25_000_000, 1_000_000
            ),
            CombatRegimentState(
                3,
                RegimentKind.MEN_AT_ARMS,
                0,
                40_000_000,
                2_000_000,
                screen_raw=500_000,
            ),
        )
        self.pursuer = (
            CombatRegimentState(
                4,
                RegimentKind.MEN_AT_ARMS,
                30_000_000,
                0,
                1,
                pursuit_raw=1_500_000,
            ),
        )
        self.initial = PursuitInitialPools.from_entries(self.retreater)

    def test_stock_mixed_day_one_golden_trace(self) -> None:
        result = apply_pursuit_day(
            self.retreater, self.pursuer, initial_pools=self.initial
        )
        self.assertEqual(result.toughness_soft_raw, 1_400_000_000)
        self.assertEqual(result.pursuit_damage_raw, 225_000_000)
        self.assertEqual(result.screen_raw, 200_000_000)
        self.assertEqual(
            (result.base_raw, result.minimum_raw, result.extra_raw),
            (70_000_000, 14_000_000, 25_000_000),
        )
        self.assertEqual(result.floor_component_raw, 70_000_000)
        self.assertEqual(
            (
                result.domains[0].extra_daily_raw,
                result.domains[0].floor_daily_raw,
                result.domains[1].extra_daily_raw,
                result.domains[1].floor_daily_raw,
            ),
            (357_000, 1_000_000, 238_000, 666_666),
        )
        self.assertEqual(
            result.hard_by_regiment_raw,
            ((1, 791_584), (2, 565_416), (3, 904_666)),
        )
        self.assertEqual(result.total_hard_raw, 2_261_666)
        self.assertEqual(result.domains[0].allocation_remainder_raw, 1)

    def test_three_days_reuse_frozen_initial_pools(self) -> None:
        result = apply_three_day_pursuit(
            self.retreater, self.pursuer, initial_pools=self.initial
        )
        self.assertEqual(len(result.days), 3)
        self.assertEqual(result.days[0].total_hard_raw, 2_261_666)
        self.assertEqual(
            sum(entry.soft_casualties_raw for entry in result.entries)
            + result.total_hard_raw,
            100_000_000,
        )
        self.assertGreater(result.days[2].total_hard_raw, 0)


class CombatRandomGoldenTests(unittest.TestCase):
    def test_schedule_draw_weight_and_effect_seed_vectors(self) -> None:
        state = phase_schedule_state(42)
        self.assertEqual(state, DrawState(counter=0x6DA1654D, salt=0))
        random31, next_state = state.draw31()
        self.assertEqual(random31, 0x226BC740)
        self.assertEqual(next_state.counter, 0x6DA1654E)
        self.assertEqual(
            weighted_choice_index((1000, 25, 10, 5), random31), 0
        )
        seeds = fire_phase_event_seeds(
            0x12345678, executed_knight_count=2, commander_executes=True
        )
        self.assertEqual(seeds.base, 0xBEA2D282)
        self.assertEqual(seeds.knight_effect_seeds, (0x30A25E2C, 0x1A6D02EB))
        self.assertEqual(seeds.commander_effect_seed, 0x0CB9C14A)

    def test_selector_draws_once_if_any_trigger_is_valid(self) -> None:
        state = phase_schedule_state(42)
        selection = select_phase_event(
            (
                PhaseEventCandidate("none", True, 1000, empty_effect=True),
                PhaseEventCandidate("wound", True, 25),
                PhaseEventCandidate("invalid", False, 1_000_000),
            ),
            state,
        )
        self.assertEqual(selection.selected_candidate_key, "none")
        self.assertIsNone(selection.executable_event_key)
        self.assertEqual(selection.random31, 0x226BC740)
        self.assertEqual(selection.state.counter, 0x6DA1654E)

    def test_main_day_scheduler_consumes_fire_before_rolls(self) -> None:
        initial = DrawState(0x6DA1654D, 0)
        result = schedule_main_day_randomness(
            initial,
            roll_cadence=0,
            side_0_roll=CommanderRollRequest(True, 0, 10),
            side_1_roll=CommanderRollRequest(True, -1, 11),
        )
        self.assertEqual(result.side_0_fire_draw, 0x226BC740)
        self.assertEqual(result.state.counter, (initial.counter + 4) & 0xFFFFFFFF)
        self.assertIsNotNone(result.side_0_roll_draw)
        self.assertIsNotNone(result.side_1_roll_draw)
        self.assertEqual(result.next_roll_cadence, 1)


class BattleEndRetreatGoldenTests(unittest.TestCase):
    def _gate(
        self,
        *,
        days: int = 15,
        disallow: bool = False,
        allow_early: bool = False,
        phase: CombatPhase = CombatPhase.MAIN,
        landless: bool = False,
    ) -> RetreatGateInput:
        return RetreatGateInput(
            disallow_retreat=disallow,
            allow_early_retreat=allow_early,
            elapsed_whole_days=days,
            phase=phase,
            landless_blocked=landless,
        )

    def test_day_14_fails_day_15_passes_and_allow_early_only_bypasses_day(self) -> None:
        day_14 = evaluate_can_retreat(self._gate(days=14))
        day_15 = evaluate_can_retreat(self._gate(days=15))
        early = evaluate_can_retreat(self._gate(days=0, allow_early=True))
        early_but_phase_2 = evaluate_can_retreat(
            self._gate(days=0, allow_early=True, phase=CombatPhase.PURSUIT)
        )
        self.assertEqual(day_14.blocked_by, RetreatBlockReason.MINIMUM_DAYS)
        self.assertFalse(day_14.can_retreat)
        self.assertTrue(day_15.can_retreat)
        self.assertTrue(early.can_retreat)
        self.assertEqual(early_but_phase_2.blocked_by, RetreatBlockReason.PHASE)

    def test_disallow_has_precedence(self) -> None:
        result = evaluate_can_retreat(
            self._gate(
                days=0,
                disallow=True,
                allow_early=True,
                phase=CombatPhase.PURSUIT,
                landless=True,
            )
        )
        self.assertEqual(result.blocked_by, RetreatBlockReason.DISALLOWED)

    def test_nonretreating_branch_clears_entries_and_components(self) -> None:
        entries = (
            CombatRegimentState(
                1,
                RegimentKind.LEVY,
                5_000_000,
                2_000_000,
                1_000_000,
                components=(BackingComponent(50, 50),),
            ),
        )
        result = transition_after_winner_is_known(
            entries,
            winner_side=0,
            retreat_gate_input=self._gate(days=14),
            skip_pursuit=False,
        )
        self.assertEqual(result.branch, BattleEndBranch.NON_RETREATING_CLEAR)
        self.assertEqual(result.phase, CombatPhase.DONE)
        self.assertEqual(result.loser_entries[0].current_raw, 0)
        self.assertEqual(result.loser_entries[0].soft_casualties_raw, 0)
        self.assertEqual(result.loser_entries[0].components[0].current_soldiers, 0)

    def test_skip_pursuit_goes_directly_to_done_without_damage(self) -> None:
        entries = (
            CombatRegimentState(
                1, RegimentKind.LEVY, 0, 2_000_000, 1_000_000
            ),
        )
        result = transition_after_winner_is_known(
            entries,
            winner_side=1,
            retreat_gate_input=self._gate(days=15),
            skip_pursuit=True,
        )
        self.assertEqual(result.branch, BattleEndBranch.SKIP_PURSUIT)
        self.assertEqual(result.phase, CombatPhase.DONE)
        self.assertEqual(result.loser_entries, entries)
        self.assertEqual(result.pursuit_initial_pools.levy_soft_raw, 2_000_000)

    def test_force_winner_mapping(self) -> None:
        self.assertEqual(forced_winner_side(scoped_side=0, scoped_yes=True), 0)
        self.assertEqual(forced_winner_side(scoped_side=1, scoped_yes=True), 1)
        self.assertEqual(forced_winner_side(scoped_side=0, scoped_yes=False), 1)
        self.assertEqual(forced_winner_side(scoped_side=1, scoped_yes=False), 0)
        main = apply_forced_winner_effect(
            phase=CombatPhase.MAIN,
            current_winner_side=None,
            scoped_side=0,
            scoped_yes=False,
        )
        pursuit = apply_forced_winner_effect(
            phase=CombatPhase.PURSUIT,
            current_winner_side=0,
            scoped_side=0,
            scoped_yes=False,
        )
        self.assertEqual(main.winner_side, 1)
        self.assertEqual(pursuit.forced_side_field, 1)
        self.assertEqual(pursuit.winner_side, 0)

    def test_winner_is_checked_next_main_tick_and_side0_is_checked_first(self) -> None:
        self.assertIsNone(
            winner_at_main_tick_start(
                forced_side_field=None,
                side_0_total_raw=1,
                side_1_total_raw=1,
            )
        )
        self.assertEqual(
            winner_at_main_tick_start(
                forced_side_field=None,
                side_0_total_raw=0,
                side_1_total_raw=0,
            ),
            1,
        )
        self.assertEqual(
            winner_at_main_tick_start(
                forced_side_field=None,
                side_0_total_raw=1,
                side_1_total_raw=0,
            ),
            0,
        )
        self.assertEqual(
            winner_at_main_tick_start(
                forced_side_field=0,
                side_0_total_raw=0,
                side_1_total_raw=0,
            ),
            0,
        )

    def test_normal_finalizer_draws_winner_then_loser_teardown_draws_none(self) -> None:
        initial = DrawState(0x6DA1654D, 0)
        normal = schedule_battle_result_envelopes(initial, teardown=False)
        teardown = schedule_battle_result_envelopes(initial, teardown=True)
        self.assertTrue(normal.normal_result_generated)
        self.assertEqual(normal.winner_envelope_draw, 0x226BC740)
        self.assertIsNotNone(normal.loser_envelope_draw)
        self.assertEqual(normal.state.counter, (initial.counter + 2) & 0xFFFFFFFF)
        self.assertTrue(teardown.terminal_no_resolution)
        self.assertIsNone(teardown.winner_envelope_draw)
        self.assertEqual(teardown.state, initial)


class _NoResolutionKernel:
    manifest = CURRENT_BOUNDED_CORE_MANIFEST

    def simulate_trial(
        self,
        initial_state: object,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome:
        draw, _ = streams.global_state.draw31()
        return TrialOutcome(
            TrialResult.NO_RESOLUTION,
            battle_days=horizon_days,
            player_hard_loss_raw=draw % FIXED_SCALE,
            enemy_hard_loss_raw=(draw // 2) % FIXED_SCALE,
        )


class MonteCarloContractTests(unittest.TestCase):
    def test_summary_counts_quantiles_wilson_and_gate(self) -> None:
        experiment = CombatExperiment("0" * 64, 7, 5, 30)
        outcomes = (
            TrialOutcome(TrialResult.PLAYER_WIN, 1, 10, 50),
            TrialOutcome(TrialResult.PLAYER_WIN, 2, 20, 40),
            TrialOutcome(TrialResult.PLAYER_WIN, 3, 30, 30),
            TrialOutcome(TrialResult.PLAYER_LOSS, 4, 40, 20),
            TrialOutcome(TrialResult.NO_RESOLUTION, 5, 50, 10),
        )
        summary = summarize_trial_outcomes(
            outcomes,
            experiment=experiment,
            manifest=CURRENT_BOUNDED_CORE_MANIFEST,
        )
        self.assertEqual(
            (summary.player_wins, summary.player_losses, summary.no_resolution),
            (3, 1, 1),
        )
        self.assertEqual(summary.player_win_probability_resolved, 0.75)
        self.assertAlmostEqual(summary.player_win_wilson95.lower, 0.3006418, places=6)
        self.assertAlmostEqual(summary.player_win_wilson95.upper, 0.9544127, places=6)
        self.assertEqual(
            (summary.battle_days.p10, summary.battle_days.p50, summary.battle_days.p90),
            (1, 3, 5),
        )
        self.assertFalse(summary.fidelity_gate)
        self.assertFalse(summary.planner_usable)
        self.assertEqual(summary.model_fidelity, "research-only-bounded-core")
        self.assertIn(
            "loaded_phase_event_effect_transition",
            summary.missing_required_domains,
        )
        self.assertNotIn(
            "battle_end_transition", summary.missing_required_domains
        )

    def test_same_input_seed_and_n_reproduce_identical_summary(self) -> None:
        experiment = CombatExperiment("a" * 64, 0x123456789ABCDEF0, 16, 45)
        first = run_combat_experiment(object(), experiment, _NoResolutionKernel())
        second = run_combat_experiment(object(), experiment, _NoResolutionKernel())
        self.assertEqual(first, second)
        self.assertEqual(first.no_resolution, 16)
        self.assertIsNone(first.player_win_probability_resolved)
        self.assertFalse(first.planner_usable)

    def test_manifest_cannot_claim_fidelity_without_original_trace(self) -> None:
        manifest = TransitionFidelityManifest(
            simulator_build="test",
            loaded_phase_effects_exact=True,
            battle_end_exact=True,
            retreat_and_forced_result_exact=True,
            original_trace_fixture_sha256=None,
            closed_numeric_domains=(),
        )
        self.assertFalse(manifest.fidelity_gate)


if __name__ == "__main__":
    unittest.main()
