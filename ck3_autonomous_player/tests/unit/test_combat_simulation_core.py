from __future__ import annotations

import json
from pathlib import Path
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
    effect_child_state,
    fire_phase_event_seeds,
    fixed_div,
    fixed_mul,
    outgoing_damage_raw,
    update_combat_width,
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
    def test_joined_soldiers_raise_width_and_later_losses_do_not_lower_base(self) -> None:
        first = update_combat_width(
            200300000, 128800000, previous_base_width=0,
            terrain_width_multiplier_raw=90000,
        )
        joined = update_combat_width(
            410690163, 82785368, previous_base_width=first[0],
            terrain_width_multiplier_raw=90000,
        )
        later = update_combat_width(
            470651390, 12161798, previous_base_width=joined[0],
            terrain_width_multiplier_raw=90000,
        )
        self.assertEqual(first, (1645, 1480))
        self.assertEqual(joined, (2467, 2220))
        self.assertEqual(later, (2467, 2220))

    def test_r078_native_join_width_partial_vector(self) -> None:
        fixture_path = (
            Path(__file__).parents[2]
            / "src/xar_autoplayer/simulation/data"
            / "ck3_1_19_0_6_episode01_join_width_partial_parity_078.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], "ck3.native_join_width_partial_model_parity.v1")
        self.assertEqual(fixture["combat_id"], 16777218)
        self.assertEqual(fixture["candidate_joining_army_id"], 22)
        self.assertEqual(fixture["base_width_zero_residual_count"], 2)
        self.assertEqual(fixture["final_width_zero_residual_count"], 2)
        self.assertFalse(fixture["three_boundary_complete"])
        self.assertFalse(fixture["phase_fire_argument_observed"])
        self.assertIsNone(fixture["fire_width"])
        naive = fixture["naive_prejoin_plus_source_join"]
        self.assertEqual(naive["source_joining_fighting_before_raw"], 256_000_000)
        self.assertEqual(naive["naive_sum_raw"], 416_317_482)
        self.assertEqual(naive["native_join_return_side0_total_raw"], 410_690_163)
        self.assertEqual(naive["naive_minus_native_raw"], 5_627_319)
        self.assertFalse(naive["source_join_amount_same_exact_hook_boundary"])
        self.assertFalse(naive["cause_of_gap_identified"])
        self.assertFalse(naive["valid_width_update_input"])
        for row in fixture["rows"]:
            with self.subTest(boundary=row["boundary"]):
                actual = update_combat_width(
                    *row["side_fighting_total_raw"],
                    previous_base_width=row["previous_base_width_input"],
                    terrain_width_multiplier_raw=fixture["terrain"]["width_multiplier_raw"],
                )
                self.assertEqual(actual, (
                    row["native_base_width"], row["native_final_width"],
                ))

    def test_signed_operations_truncate_toward_zero(self) -> None:
        self.assertEqual(trunc_div_toward_zero(-7, 3), -2)
        self.assertEqual(trunc_div_toward_zero(7, -3), -2)
        self.assertEqual(fixed_mul(-150_001, 50_000), -75_000)
        self.assertEqual(fixed_div(-100_001, 300_000), -33_333)
        self.assertEqual(fixed_div(1, 0), -1)

    def test_r0217_original_tick_outgoing_damage_both_sides(self) -> None:
        fixture_path = (
            Path(__file__).parents[1]
            / "fixtures"
            / "combat"
            / "r0217_outgoing_order_native_tick.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["combat_id"], 738197508)
        for side in fixture["sides"]:
            with self.subTest(side=side["side_index"]):
                self.assertEqual(
                    outgoing_damage_raw(
                        side["post_counter_attack_raw"],
                        advantage_multiplier_raw=side["advantage_multiplier_raw"],
                        final_combat_width=fixture["final_combat_width"],
                        side_current_fighting_men_raw=side["current_fighting_men_raw"],
                        damage_scaling_raw=fixture["damage_scaling_raw"],
                    ),
                    side["native_outgoing_damage_raw"],
                )

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

    def test_signed_negative_hard_reaches_first_nonempty_component(self) -> None:
        # The exact-build first pass checks remaining <= 0 after its setter.
        # With current 5 < max 10, the setter's exceptional clear guard cannot
        # fire, so this signed-domain vector has an exact final integer state.
        result = allocate_hard_casualties_to_components(
            (BackingComponent(10, 0), BackingComponent(10, 5), BackingComponent(10, 5)),
            -200_000,
        )
        self.assertEqual(
            tuple(item.current_soldiers for item in result.components), (0, 7, 5)
        )
        self.assertEqual(result.whole_soldier_losses, (0, -2, 0))
        self.assertEqual(result.unallocated_raw, 0)

    def test_zero_remainder_second_pass_revisits_special_kind_three(self) -> None:
        # A kind-3 zero-current component uses max as first-pass capacity but
        # zero as setter base. The native second pass still starts at remainder
        # zero, revisits its now-negative current, and moves one whole death to
        # the following stored component. Both setter calls stay below max.
        result = allocate_hard_casualties_to_components(
            (BackingComponent(2, 0, kind=3), BackingComponent(5, 5)),
            150_000,
        )
        self.assertEqual(
            tuple(item.current_soldiers for item in result.components), (0, 4)
        )
        self.assertEqual(result.whole_soldier_losses, (0, 1))
        self.assertEqual(result.unallocated_raw, 0)


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

    def test_screen_dominates_pursuit_static_boundary(self) -> None:
        # Static 0x23CD2E0/0x23CD660 vector, not an independent live parity.
        # It covers extra=0, the minimum floor, signed modifier, and the
        # earliest-entry remainder which the Messina live case cannot cover.
        retreater = (
            CombatRegimentState(
                1, RegimentKind.LEVY, 0, 7_000_003, 1_000_000,
                screen_raw=2_000_000,
            ),
            CombatRegimentState(
                2, RegimentKind.LEVY, 0, 5_000_007, 1_200_000,
                screen_raw=500_000,
            ),
            CombatRegimentState(
                3, RegimentKind.MEN_AT_ARMS, 0, 3_000_011, 2_000_000,
                screen_raw=1_000_000,
            ),
        )
        pursuer = (
            CombatRegimentState(
                4, RegimentKind.MEN_AT_ARMS, 9_000_013, 0, 1,
                pursuit_raw=600_000,
            ),
        )
        result = apply_pursuit_day(
            retreater,
            pursuer,
            initial_pools=PursuitInitialPools.from_entries(retreater),
            retreater_loss_modifier_raw=25_000,
        )
        self.assertEqual(result.toughness_soft_raw, 190_000_334)
        self.assertEqual(result.pursuit_damage_raw, 27_000_039)
        self.assertEqual(result.screen_raw, 195_000_205)
        self.assertEqual(result.base_raw, 9_500_016)
        self.assertEqual(result.minimum_raw, 1_900_003)
        self.assertEqual(result.extra_raw, 0)
        self.assertEqual(result.floor_component_raw, 1_900_003)
        self.assertEqual(
            tuple(
                (domain.extra_daily_raw, domain.floor_daily_raw,
                 domain.allocation_remainder_raw)
                for domain in result.domains
            ),
            ((0, 49_950, 1), (0, 12_487, 1)),
        )
        self.assertEqual(
            result.hard_by_regiment_raw,
            ((1, 29_138), (2, 20_812), (3, 12_487)),
        )
        self.assertEqual(result.total_hard_raw, 62_437)
        self.assertEqual(
            tuple(entry.soft_casualties_raw for entry in result.entries),
            (6_970_865, 4_979_195, 2_987_524),
        )

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
    def test_native_random_list_child_scope_is_distinct_from_parent_seed_draw(self) -> None:
        cases = (
            (621006420, 1775997395, 222734186, 1945981592, 969825991),
            (4061646098, 3752165551, 1131396744, 3878703667, 518689972),
            (2080801941, 661296556, 632491899, 1844551402, 1422813481),
            (1645259625, 1775997395, 422551104, 1462316485, 51510340),
        )
        for parent_counter, node_hash, expected_parent, expected_child, expected_draw in cases:
            with self.subTest(parent_counter=parent_counter):
                parent_draw, parent_after, child = effect_child_state(
                    DrawState(parent_counter, 0), node_hash
                )
                self.assertEqual(parent_draw, expected_parent)
                self.assertEqual(parent_after.counter, parent_counter + 1)
                self.assertEqual(child.counter, expected_child)
                self.assertEqual(child.draw31()[0], expected_draw)
        self.assertEqual(weighted_choice_index((4, 2, 4, 4), 518689972), 0)

    def test_day26_selected_list_entry_consumes_seed_after_choice(self) -> None:
        _, _, list_scope = effect_child_state(
            DrawState(1645259625, 0), 1775997395
        )
        self.assertEqual(list_scope.counter, 1462316485)
        choice_draw, after_choice = list_scope.draw31()
        self.assertEqual(choice_draw, 51510340)
        self.assertEqual(weighted_choice_index((40, 30, 15), choice_draw), 0)
        entry_seed_draw, after_entry_seed = after_choice.draw31()
        self.assertEqual(entry_seed_draw, 114945994)
        self.assertEqual(after_entry_seed.counter, 1462316487)

    def test_schedule_draw_weight_and_effect_seed_vectors(self) -> None:
        state = phase_schedule_state(42)
        self.assertEqual(state, DrawState(counter=0x6DA1654D, salt=0))
        random31, next_state = state.draw31()
        self.assertEqual(random31, 0x226BC740)
        self.assertEqual(next_state.counter, 0x6DA1654E)
        self.assertEqual(
            weighted_choice_index((1000, 25, 10, 5), random31), 0
        )
        # The native weighted helper scales a 31-bit draw.  Modulo would
        # incorrectly choose entry 1 for this draw and weight vector.
        self.assertEqual(weighted_choice_index((40, 30, 15), 40), 0)
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
