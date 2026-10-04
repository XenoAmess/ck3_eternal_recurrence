from __future__ import annotations

import unittest

from xar_autoplayer.simulation.battle_current_adapter import (
    CurrentBattleCondition,
    CurrentBattleEntry,
    CurrentBattleSide,
)
from xar_autoplayer.simulation.battle_current_terminal import (
    TerminalBackingRegiment,
    project_current_terminal_accounting,
)
from xar_autoplayer.simulation.combat_core import CombatRegimentState, RegimentKind


Q = 100_000


def _entry(regiment_id: int, kind: RegimentKind, current: int, soft: int,
           starting: int) -> CurrentBattleEntry:
    return CurrentBattleEntry(
        state=CombatRegimentState(
            regiment_id=regiment_id, kind=kind, current_raw=current,
            soft_casualties_raw=soft, toughness_raw=Q,
        ),
        bucket=kind.value, bucket_index=0, native_carmy_id=101,
        public_cunit_id=83_886_341, owner_character_id=29_829,
        starting_raw=starting, effective_damage_raw=Q,
        fights_in_main_phase=True, hard_casualties_raw=starting-current-soft,
        knight_character_id_raw=None, backing_components=None,
        source_entry={"regiment_id": regiment_id},
    )


def _side(index: int, entries: tuple[CurrentBattleEntry, ...]) -> CurrentBattleSide:
    current = sum(entry.state.current_raw for entry in entries)
    levy_current = sum(entry.state.current_raw for entry in entries
                       if entry.state.kind is RegimentKind.LEVY)
    owner = 29_829 if index == 0 else 36_108
    ledger = ({"row_index": 0, "participant_character_id": owner,
               "hard_casualties_raw": 400_011},) if index == 0 else ()
    return CurrentBattleSide(
        side_index=index, role="attacker" if index == 0 else "defender",
        primary_participant_character_id=owner,
        selected_commander_character_id=-1, current_roll_points=0,
        roll_request=None, entries=entries,
        ordered_armies=({"native_carmy_id": 101+index,
                        "public_cunit_id": 83_886_341+index,
                        "owner_character_id": owner,
                        "combat_backlink_id": 335_544_325},),
        stored_current_fighting_raw=current,
        stored_levy_current_fighting_raw=levy_current,
        derived_current_fighting_raw=current,
        derived_soft_casualties_raw=sum(entry.state.soft_casualties_raw
                                       for entry in entries),
        derived_main_fighting_entry_hard_casualties_raw=sum(
            entry.hard_casualties_raw or 0 for entry in entries),
        non_main_start_minus_current_minus_soft_raw=0,
        participant_hard_ledger=ledger,
        participant_hard_total_raw=400_011 if index == 0 else 0,
        loss_inputs=None, levy_damage_raw=None, levy_damage_source="unavailable",
        levy_damage_native_observed=False,
        levy_damage_primary_participant_character_id=None,
    )


def _condition() -> CurrentBattleCondition:
    entries = (
        _entry(99, RegimentKind.LEVY, 600_003, 200_005, 1_500_000),
        _entry(7, RegimentKind.MEN_AT_ARMS, 400_004, 300_009, 1_200_000),
    )
    return CurrentBattleCondition(
        snapshot_revision=57, observed_date_raw=53_178_264,
        combat_id=335_544_325, province_id=2586,
        subject_side_index=0, side_scope="full_side", phase="done", phase_raw=3,
        phase_day=0, base_combat_width=5, final_combat_width=5,
        roll_cadence_counter=0, base_advantage_raw=0, resolved_advantage_raw=0,
        sides=(_side(0, entries), _side(1, ())), loss_inputs=None,
        active_counter_inputs=None, pursuit_modifier_sides=None,
        missing_inputs=(),
        source_snapshot={
            "attacker": {"stored_terminal_loss_baseline_raw": 3_000_000},
            "defender": {"stored_terminal_loss_baseline_raw": 0},
        },
    )


class CurrentTerminalAccountingFocusedTests(unittest.TestCase):
    def test_native_baseline_accounts_and_integer_survivors_remain_distinct(self):
        condition = _condition()
        # The explicit complete backing list keeps its own native order. It is
        # separate from combat bucket order and fractional current/soft values.
        backing = {
            0: (TerminalBackingRegiment(101, 7, 9),
                TerminalBackingRegiment(101, 99, 7)),
            1: (),
        }
        result = project_current_terminal_accounting(
            condition, stop_reason="fixture_terminal_accounting", winner_side=0,
            normal_result_intent=True,
            backing_current_by_side=backing,
            side_baseline_raw_by_side={0: 9_900_000, 1: 9_900_000},
        )
        self.assertEqual(result["scale"], Q)
        self.assertEqual(result["observed_frame"]["combat_id"], condition.combat_id)
        self.assertEqual((result["winner_side"], result["loser_side"]), (0, 1))
        self.assertEqual([row["side_index"] for row in result["sides"]], [0, 1])
        attacker, defender = result["sides"]
        self.assertEqual(attacker["baseline_raw_q100000"], 3_000_000)
        self.assertEqual(attacker["baseline_source"],
                         "source_snapshot.attacker.stored_terminal_loss_baseline_raw")
        self.assertNotEqual(attacker["baseline_raw_q100000"],
                            sum(entry.starting_raw for entry in condition.sides[0].entries))
        self.assertEqual(attacker["stored_current_fighting_raw_q100000"], 1_000_007)
        self.assertEqual(attacker["levy_soft_raw_q100000"], 200_005)
        self.assertEqual(attacker["men_at_arms_soft_raw_q100000"], 300_009)
        self.assertEqual(attacker["hard_loss_raw_q100000"], 1_499_979)
        self.assertEqual(attacker["participant_hard_ledger"],
                         list(condition.sides[0].participant_hard_ledger))
        self.assertEqual(attacker["participant_hard_total_raw_q100000"], 400_011)
        self.assertNotEqual(attacker["hard_loss_raw_q100000"],
                            attacker["participant_hard_total_raw_q100000"])
        self.assertEqual(attacker["final_survivors_raw_q100000"], 1_600_000)
        self.assertEqual([row["regiment_id"] for row in attacker["backing_regiments"]], [7, 99])
        self.assertNotEqual(attacker["final_survivors_raw_q100000"],
                            attacker["stored_current_fighting_raw_q100000"])
        self.assertEqual(defender["hard_loss_raw_q100000"], 0)
        self.assertEqual(defender["final_survivors_raw_q100000"], 0)
        self.assertEqual(defender["backing_regiments"], [])
        self.assertEqual(defender["unavailable_inputs"], [])
        unavailable = project_current_terminal_accounting(
            condition, stop_reason="fixture_terminal_accounting", winner_side=0,
            normal_result_intent=True,
        )
        for row in unavailable["sides"]:
            self.assertIsNone(row["final_survivors_raw_q100000"])
            self.assertIsNone(row["backing_regiments"])
            self.assertTrue(row["unavailable_inputs"])
        self.assertEqual(unavailable["sides"][0]["hard_loss_raw_q100000"], 1_499_979)
        for key in ("hard_summary_is_participant_ledger_or_named_deaths",
                    "final_survivors_are_cached_fighting_current", "complete_monte_carlo",
                    "ai_retreat_decision_predicted", "named_character_outcomes_predicted"):
            self.assertFalse(result[key])
