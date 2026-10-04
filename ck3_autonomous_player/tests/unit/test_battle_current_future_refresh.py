from __future__ import annotations

from dataclasses import replace
import unittest

from test_battle_current_condition import Q, _entry, _raw_frame, _side
from test_battle_current_refresh import _carried, _counter
from xar_autoplayer.simulation.battle_current_future_refresh import (
    CommanderCandidateInputs,
    FutureCommanderSideInputs,
    FutureMainRefreshInputs,
    FutureMainScope,
    RelationModifierInputs,
    run_conditional_future_main_tick,
)
from xar_autoplayer.simulation.combat_core import CommanderRollRequest


def _carried_pair():
    raw = _raw_frame(1)
    for index, role in enumerate(("attacker", "defender")):
        army = raw[role]["ordered_armies"][0]
        raw[role] = _side(index, [army], [], [
            _entry(7 if index == 0 else 8, army, bucket="men_at_arms", index=0,
                   current=1_000_000, damage=400_000 if index == 0 else 0,
                   toughness=Q)], [(army["owner_character_id"], 0)])
        raw[role]["current_roll_points"] = 0
        raw["current_loss_inputs_v1"]["sides"][index].update(
            primary_participant_character_id=army["owner_character_id"], levy_damage_raw=0)
    raw.update(base_advantage_raw=-Q, resolved_advantage_raw=0)
    _counter(raw, Q)
    original, tick, carried = _carried(raw)
    return original, tick, carried


def _relation(source: str) -> RelationModifierInputs:
    return RelationModifierInputs(
        generic_raw=0, role_raw=0, terrain_raw=0,
        target_definition_applies=False, target_definition_raw=0,
        holding_applies=False, holding_raw=0,
        opposing_effect_modifier_raw=0, opposing_effect_rows=(),
        relation_kind_raw=0, relation_raw=0, source_label=source)


def _scope() -> FutureMainScope:
    return FutureMainScope(
        fixed_roster=True, no_joins=True, no_phase_events=True,
        no_character_deaths=True, fixed_target_terrain=True,
        stable_owner_modifiers=True, stable_entry_stats=True,
        stable_commander_context=True, maximum_main_ticks=2)


def _inputs(carried) -> FutureMainRefreshInputs:
    sides = []
    for index, side in enumerate(carried.condition.sides):
        candidate = CommanderCandidateInputs(
            candidate_character_id=side.selected_commander_character_id,
            effective_martial=1 if index == 0 else 0,
            opaque_opposing_primary_raw=0, opaque_province_context_raw=0,
            character_relation_inputs=_relation(f"fixture Character receiver side{index}; fixed context"),
            source_label=f"synthetic explicit current candidate operands side{index}; not an actual sample",
            army_1ae_present=False, army_1ae_raw=0, army_1ae_gate=False,
            primary_identity_modifier_raw=0, side_gathering=False,
            candidate_has_flag_1a5=False, loaded_gathering_points=0,
            roll_request=CommanderRollRequest(True, 4 if index == 0 else 2,
                                              4 if index == 0 else 2, 0))
        sides.append(FutureCommanderSideInputs(
            candidates=(candidate,), candidate_census_complete=True,
            side_relation_inputs=_relation(f"fixture actual side receiver{index}; fixed context"),
            source_label=f"synthetic explicit ordered single-candidate census side{index}"))
    return FutureMainRefreshInputs(
        scope=_scope(), side_inputs=tuple(sides), modeled_tick_index=1,
        roll_cadence_interval=5,
        roll_cadence_interval_source="synthetic explicit loaded slot5C69B48 fixture observation; not live",
        loaded_advantage_scaling_raw=200_000,
        loaded_advantage_scaling_source="synthetic explicit signed64 slot5C6A230 fixture observation; not live",
        resolve_boundary="after_modeled_due_rolls", width_update=None)


class BattleCurrentFutureRefreshFixtureTests(unittest.TestCase):
    """Two new conditional fixed-roster cases with independent Q100000 arithmetic."""

    def test_carried_counts_rebuild_counter_and_declared_roll_resolve_factor(self):
        original, first_tick, carried = _carried_pair()
        self.assertEqual(first_tick["counter_retention_raw_by_side"], ((55_000,), (55_000,)))
        self.assertEqual(first_tick["outgoing_damage_raw_by_side"], [550_000, 0])
        self.assertEqual([side.entries[0].state.current_raw for side in carried.condition.sides],
                         [1_000_000, 450_000])
        self.assertEqual((carried.draw_state.counter, carried.draw_state.salt), (13, 17))
        self.assertEqual(carried.condition.sides[1].stored_current_fighting_raw, 1_000_000)

        modeled = run_conditional_future_main_tick(carried, inputs=_inputs(carried))
        context, result = modeled.context, modeled.result
        condition = context.condition
        self.assertEqual([side.stored_current_fighting_raw for side in condition.sides],
                         [1_000_000, 450_000])
        self.assertEqual([entry["current_chunk_raw"] for side in condition.active_counter_inputs["sides"]
                          for entry in side["men_at_arms_entries"]], [1_000_000, 450_000])
        self.assertEqual(result["counter_retention_raw_by_side"], ((79_750,), (10_000,)))
        self.assertEqual([side.current_roll_points for side in condition.sides], [4, 2])
        self.assertEqual(condition.base_advantage_raw, -Q)
        self.assertEqual(condition.resolved_advantage_raw, 200_000)
        self.assertEqual(condition.loss_inputs.stored_advantage_damage_factor_raw, 104_000)
        self.assertEqual([side.outgoing_advantage_factor_raw for side in condition.loss_inputs.sides], [104_000, Q])
        self.assertEqual(condition.roll_cadence_counter, 1)
        self.assertEqual((context.draw_state_before_rolls.counter, context.draw_state_before_rolls.salt), (13, 17))
        self.assertEqual((context.draw_state_after_rolls.counter, context.draw_state_after_rolls.salt), (15, 17))
        self.assertEqual((modeled.carried.draw_state.counter, modeled.carried.draw_state.salt), (15, 17))
        self.assertEqual(result["outgoing_damage_raw_by_side"], [829_400, 0])
        self.assertEqual(condition.source_snapshot, original.source_snapshot)
        self.assertEqual((condition.snapshot_revision, condition.observed_date_raw),
                         (original.snapshot_revision, original.observed_date_raw))
        self.assertTrue(context.conditional_assumptions)
        self.assertFalse(context.complete_transition)
        self.assertFalse(result["complete_monte_carlo"])
        self.assertIsNone(result["win_probability"])

    def test_wrap_to_zero_excludes_diagnostic_draws_and_retains_missing_operands(self):
        original, _, carried = _carried_pair()
        # This is explicitly caller-owned modeled cadence; the original observed
        # snapshot remains at cadence0 and is never rewritten into a native frame.
        condition = carried.condition
        loss_sides = list(condition.loss_inputs.sides)
        loss_sides[1] = replace(loss_sides[1], levy_damage_raw=None)
        sides = list(condition.sides)
        sides[1] = replace(sides[1], loss_inputs=loss_sides[1], levy_damage_raw=None)
        condition = replace(condition, roll_cadence_counter=4,
                            sides=tuple(sides),
                            loss_inputs=replace(condition.loss_inputs, sides=tuple(loss_sides)))
        carried = replace(carried, condition=condition)
        inputs = replace(_inputs(carried), side_inputs=None,
                         loaded_advantage_scaling_raw=None,
                         loaded_advantage_scaling_source=None,
                         resolve_boundary=None)
        modeled = run_conditional_future_main_tick(carried, inputs=inputs)
        context, result = modeled.context, modeled.result

        self.assertEqual(context.condition.roll_cadence_counter, 0)
        self.assertEqual([side.current_roll_points for side in context.condition.sides], [0, 0])
        self.assertEqual((context.draw_state_before_rolls.counter, context.draw_state_after_rolls.counter), (13, 13))
        self.assertEqual(result["rolls"]["input_draw_state"], {"counter": 13, "salt": 17})
        self.assertEqual(result["rolls"]["output_draw_state"], {"counter": 15, "salt": 17})
        self.assertEqual((modeled.carried.draw_state.counter, modeled.carried.draw_state.salt), (13, 17))
        self.assertEqual(context.condition.sides[1].entries[0].effective_damage_raw, 0)
        self.assertIsNone(context.condition.sides[1].levy_damage_raw)
        self.assertTrue(context.missing_inputs)
        self.assertTrue(context.conditional_assumptions)
        self.assertIsNone(context.condition.loss_inputs)
        self.assertEqual(carried.condition.loss_inputs.stored_advantage_damage_factor_raw, Q)
        self.assertEqual(context.condition.source_snapshot, original.source_snapshot)
        self.assertEqual(original.roll_cadence_counter, 0)
        self.assertFalse(context.complete_transition)
        self.assertFalse(result["complete_monte_carlo"])
        self.assertIsNone(result["win_probability"])


if __name__ == "__main__":
    unittest.main()
