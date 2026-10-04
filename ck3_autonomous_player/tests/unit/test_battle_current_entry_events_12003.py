from __future__ import annotations

import copy
from dataclasses import replace
import unittest

from test_battle_current_condition import Q, _entry, _raw_frame, _side
from test_battle_current_refresh import _carried, _counter
from xar_autoplayer.simulation.battle_current_entry_events_12003 import (
    AdmittedArmyJoin12003, CommittedKnightCleanup12003, IncomingRegiment12003,
    apply_closed_entry_events_12003, owner_subset_pursuit_worklist_12003,
)
from xar_autoplayer.simulation.battle_current_terminal import TerminalBackingRegiment
from xar_autoplayer.simulation.combat_core import RegimentKind


class BattleCurrentEntryEvents12003Tests(unittest.TestCase):
    """Two caller-conditioned source-closed cases; no actual native event claim."""

    def test_new_join_and_duplicate_outer_consequences_preserve_retained_losses(self):
        _, _, carried = _carried(_raw_frame(2))
        carried = replace(carried, condition=replace(carried.condition,
                           phase="pursuit", phase_raw=2, phase_day=7))
        source_before = copy.deepcopy(carried.condition.source_snapshot)
        retained = carried.condition.sides[1].entries
        self.assertEqual([row.state.current_raw for row in retained], [325000, 325000])
        self.assertEqual([row.hard_casualties_raw for row in retained], [375000, 475000])
        incoming = (
            IncomingRegiment12003(105, 3, RegimentKind.LEVY, True, 200000, Q,
                                 property_source={"kind": "caller_frozen_encounter"}),
            IncomingRegiment12003(104, 4, RegimentKind.MEN_AT_ARMS, False, 300000, 200000,
                                 knight_character_id_raw=34335,
                                 property_source={"kind": "caller_frozen_encounter"}),
        )
        event = AdmittedArmyJoin12003(carried.condition.combat_id, 1, 404, 67108909,
                                     38901, incoming, (1000, 1200), {"operation": "2586760"})
        result = apply_closed_entry_events_12003(carried, (event,), backing_by_army={}, modeled_winner_raw=1)
        condition = result.carried.condition
        side = condition.sides[1]
        self.assertEqual([row.state.regiment_id for row in side.entries], [105, 99, 3, 104])
        self.assertEqual([row.bucket_index for row in side.entries], [0, 0, 1, 2])
        self.assertEqual([row.state.current_raw for row in side.entries], [300000, 325000, 325000, 0])
        self.assertEqual((side.entries[0].starting_raw, side.entries[3].starting_raw), (300000, 400000))
        self.assertEqual((side.entries[0].state.soft_casualties_raw, side.entries[3].state.soft_casualties_raw), (0, 0))
        self.assertIsNone(side.entries[3].hard_casualties_raw)
        self.assertEqual(side.entries[1:3], retained)
        self.assertEqual(side.participant_hard_ledger, carried.condition.sides[1].participant_hard_ledger)
        self.assertEqual(side.participant_hard_total_raw, 850000)
        self.assertEqual(side.stored_current_fighting_raw, 950000)
        self.assertEqual(side.stored_levy_current_fighting_raw, 300000)
        self.assertEqual((condition.phase_raw, condition.phase_day, result.modeled_winner_raw), (1, 0, -1))
        self.assertEqual((condition.base_combat_width, condition.final_combat_width), (1000, 1200))
        self.assertEqual(result.initial_baseline_deltas_by_side[1],
                         {"side_A8_initial_raw": 700000, "side_B0_levy_initial_raw": 300000})
        self.assertEqual([row.current_soldiers for row in result.backing_by_army[404]], [3, 4])
        self.assertEqual(condition.source_snapshot, source_before)
        self.assertIs(result.carried.draw_state, carried.draw_state)
        self.assertEqual(result.carried.simulated_main_ticks, carried.simulated_main_ticks)
        self.assertFalse(result.event_ledger[0]["actual_execution_claimed"])

        # Inner duplicate skips initialization; the invoked outer branch still runs.
        duplicate_carry = replace(result.carried, condition=replace(condition,
                                  phase="pursuit", phase_raw=2, phase_day=9))
        duplicate = replace(event, regiments_in_source_order=(replace(incoming[0], current_soldiers=999),),
                            refreshed_width=(1300, 1400))
        again = apply_closed_entry_events_12003(duplicate_carry, (duplicate,),
                    backing_by_army=result.backing_by_army, modeled_winner_raw=0)
        self.assertEqual(again.carried.condition.sides[1].entries, side.entries)
        self.assertEqual(again.carried.condition.sides[1].ordered_armies, side.ordered_armies)
        self.assertEqual(again.initial_baseline_deltas_by_side[1],
                         {"side_A8_initial_raw": 0, "side_B0_levy_initial_raw": 0})
        self.assertTrue(again.event_ledger[0]["duplicate_inner_add"])
        self.assertTrue(again.event_ledger[0]["both_current_caches_refreshed"])
        self.assertTrue(again.event_ledger[0]["width_refresh_called"])
        self.assertTrue(again.event_ledger[0]["phase2_restart"])
        self.assertEqual(again.event_ledger[0]["result_initial_rows"], [])
        self.assertEqual((again.carried.condition.phase_raw, again.carried.condition.phase_day,
                          again.modeled_winner_raw), (1, 0, -1))
        self.assertEqual((again.carried.condition.base_combat_width, again.carried.condition.final_combat_width), (1300, 1400))

        # Ordinary main duplicate keeps its phase/day and caller modeled winner.
        main_carry = replace(again.carried, condition=replace(again.carried.condition, phase_day=6))
        main = apply_closed_entry_events_12003(main_carry, (duplicate,), modeled_winner_raw=0)
        self.assertEqual((main.carried.condition.phase_raw, main.carried.condition.phase_day, main.modeled_winner_raw), (1, 6, 0))

    def test_committed_cleanup_debits_only_current_and_erases_true_zero_without_death_inference(self):
        raw = _raw_frame(1)
        army = raw["attacker"]["ordered_armies"][0]
        target = raw["attacker"]["men_at_arms_entries"][0]
        target["knight_character_id_raw"] = 34333
        zero = _entry(103, army, bucket="men_at_arms", index=1,
                      current=0, damage=0, toughness=0, main=False)
        zero.update(starting_raw=Q, knight_character_id_raw=34334)
        raw["attacker"] = _side(0, [army], raw["attacker"]["levy_entries"], [target, zero], [(29829, 0)])
        _counter(raw, Q)
        _, _, carried = _carried(raw)
        before = carried.condition
        rows = before.sides[0].entries
        self.assertEqual([row.state.current_raw for row in rows], [300000, 450000, 0])
        self.assertEqual(rows[1].state.soft_casualties_raw, 75000)
        census = {101: (TerminalBackingRegiment(101, 90, 3),
                        TerminalBackingRegiment(101, 7, 4), TerminalBackingRegiment(101, 103, 1))}
        no_cause = apply_closed_entry_events_12003(carried, (), backing_by_army=census)
        self.assertIs(no_cause.carried.condition, before)
        event = CommittedKnightCleanup12003(before.combat_id, 34333, 7, 101,
                    True, True, True, True, True, {"cause": "death_cleanup_remove_regiment"},
                    regiment_mapping_valid=True, army_mapping_valid=True, combat_mapping_valid=True)
        requested_only = apply_closed_entry_events_12003(carried, (replace(event, death_commit_selected=False),))
        self.assertIs(requested_only.carried.condition, before)
        self.assertEqual(requested_only.event_ledger[0]["branch"], "native_knight_cleanup_not_selected")
        flag_only = apply_closed_entry_events_12003(carried, (replace(event, linked_regiment_id=-1),))
        self.assertIs(flag_only.carried.condition, before)
        self.assertEqual(flag_only.event_ledger[0]["branch"], "flag_clear_no_linked_regiment")
        invalid_reg = apply_closed_entry_events_12003(carried, (replace(event, regiment_mapping_valid=False),), backing_by_army=census)
        self.assertIs(invalid_reg.carried.condition, before)
        self.assertEqual(invalid_reg.event_ledger[0]["branch"], "flag_clear_invalid_regiment_mapping")
        self.assertEqual(invalid_reg.event_ledger[0]["CourtLink_16C_after"], 0)
        self.assertEqual(invalid_reg.backing_by_army, census)
        invalid_army = apply_closed_entry_events_12003(carried, (replace(event, army_mapping_valid=False),), backing_by_army=census)
        self.assertEqual(invalid_army.carried.condition, before)
        self.assertEqual(invalid_army.backing_by_army, census)
        self.assertEqual(invalid_army.event_ledger[0]["CourtLink_F8_after"], -1)
        self.assertIsNone(invalid_army.event_ledger[0]["Regiment_140_after"])
        invalid_combat = apply_closed_entry_events_12003(carried, (replace(event, combat_mapping_valid=False),), backing_by_army=census)
        self.assertEqual(invalid_combat.carried.condition, before)
        self.assertEqual([row.regiment_id for row in invalid_combat.backing_by_army[101]], [90, 103])
        self.assertEqual(invalid_combat.event_ledger[0]["Regiment_140_after"], -1)
        self.assertFalse(invalid_combat.event_ledger[0]["side_callbacks_in_native_order"][0]["invoked"])
        zero_event = replace(event, character_id=34334, linked_regiment_id=103)
        result = apply_closed_entry_events_12003(carried, (event, zero_event), backing_by_army=census)
        after = result.carried.condition
        side = after.sides[0]
        self.assertEqual([row.state.regiment_id for row in side.entries], [90])
        self.assertEqual(side.entries[0], rows[0])
        self.assertEqual(side.stored_current_fighting_raw, before.sides[0].stored_current_fighting_raw-450000)
        self.assertEqual(side.stored_levy_current_fighting_raw, before.sides[0].stored_levy_current_fighting_raw)
        self.assertEqual(side.derived_current_fighting_raw, 300000)
        self.assertNotEqual(side.stored_current_fighting_raw, side.derived_current_fighting_raw)
        self.assertEqual(side.participant_hard_ledger, before.sides[0].participant_hard_ledger)
        self.assertEqual(side.participant_hard_total_raw, before.sides[0].participant_hard_total_raw)
        self.assertEqual(side.ordered_armies, before.sides[0].ordered_armies)
        self.assertEqual(after.sides[1], before.sides[1])
        self.assertEqual([row.regiment_id for row in result.backing_by_army[101]], [90])
        self.assertEqual(census[101][-1].regiment_id, 103)
        self.assertEqual((after.phase_raw, after.phase_day, side.selected_commander_character_id),
                         (before.phase_raw, before.phase_day, before.sides[0].selected_commander_character_id))
        self.assertEqual((after.snapshot_revision, after.observed_date_raw), (before.snapshot_revision, before.observed_date_raw))
        self.assertEqual(after.source_snapshot, before.source_snapshot)
        self.assertIs(result.carried.draw_state, carried.draw_state)
        callbacks = result.event_ledger[1]["side_callbacks_in_native_order"]
        self.assertTrue(callbacks[0]["matched"])
        self.assertEqual(callbacks[0]["current_debit_raw"], 0)
        self.assertFalse(callbacks[1]["matched"])
        self.assertFalse(result.event_ledger[0]["destroyed_physical_Regiment_148_zero_is_live_identity"])
        self.assertFalse(result.complete_transition)
        self.assertFalse(result.complete_monte_carlo)
        work = owner_subset_pursuit_worklist_12003(before.sides[0], 29829)
        self.assertEqual([row.state.regiment_id for row in work["entries_by_bucket_in_reverse_selection_order"]["men_at_arms"]], [103, 7])
        self.assertEqual(work["arg5_arg7_maa_soft_raw"], 75000)
        self.assertEqual(work["duration_divisor"], 1)
        self.assertTrue(work["native_mixed_owner_fifth_flag"])
        self.assertFalse(work["side_C2_read_as_skip_gate"])
        self.assertTrue(work["pursuit_pending"])
        self.assertIsNone(work["numeric_writeback"])


if __name__ == "__main__":
    unittest.main()
