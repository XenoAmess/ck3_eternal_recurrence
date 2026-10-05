"""One new bounded final-stat case; fixtures are source inputs, never live."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import unittest

from test_battle_current_condition import Q, SUBJECT, _entry, _raw_frame, _side
from test_battle_current_refresh import _counter
from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import (
    EntrySixStatCache12003, FinalEntryStatInput12003, PersonStatStage12003,
    apply_first_contact_final_stat_refresh_12003,
    compute_knight_stat_cache_at_stage_12003,
    final_entry_input_from_knight_stage_12003,
    knight_effectiveness_fixed_mul_12003,
    knight_inputs_from_current_observation_12003,
    knight_inputs_from_person_stages_12003,
    person_stage_from_chain_projection_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003,
)


class FirstContactFinalStatRefresh12003Tests(unittest.TestCase):
    def test_distinct_person_frontiers_and_whole_side_cache_writes(self):
        raw = _raw_frame(2)
        own = raw["attacker"]["ordered_armies"][0]
        zero = _entry(7, own, bucket="men_at_arms", index=0,
                      current=0, damage=999999, toughness=888888, main=False)
        zero.update(starting_raw=Q, knight_character_id_raw=56514)
        raw["attacker"] = _side(0, [own], raw["attacker"]["levy_entries"],
                                [zero], [(29829, 0)])
        raw["defender"]["men_at_arms_entries"][0]["knight_character_id_raw"] = 56513
        _counter(raw, Q)
        normalized = normalize_battle_control_snapshot_v1(
            raw, expected_subject_public_cunit_id=SUBJECT,
            expected_observed_date_raw=raw["observed_date_raw"],
            expected_snapshot_revision=raw["snapshot_revision"])
        before = adapt_current_battle_condition(normalized)
        snapshot_before = deepcopy(before.source_snapshot)

        context = NativeModifierContext12003(
            PropertyContainer12003((0xC1, 0xC4, 0xC5), (25000, 2000, -1000), 3))
        # The retained actual frontier is not renamed into full preparation.
        chain = SimpleNamespace(
            character_full_id=29829, stage="post291F940_pre291C467",
            context=context, ready=True, missing_inputs=(),
            source_ledger={"source": "explicit_conditional_person_frontier"})
        cache = SimpleNamespace(
            character_id=29829, final_cache_points=(10, 4, 9, 0, 0, 30),
            ledger={"source": "six_skill_projection_of_same_frontier"})
        selected = person_stage_from_chain_projection_12003(
            chain, cache, carrier_1c0_present=False)
        linked = PersonStatStage12003(
            56513, "explicit_linked_knight_stage", None, (0, 0, 0, 0, 0, 0))
        knight = compute_knight_stat_cache_at_stage_12003(
            knight_inputs_from_person_stages_12003(
                linked, selected, loaded_damage_multiplier=50,
                loaded_toughness_multiplier=10,
                source_provenance={"selection_source": "28BFC70 distinct Character"}))
        self.assertTrue(knight.ready)
        self.assertEqual((knight.linked_character_full_id, knight.selected_character_full_id),
                         (56513, 29829))
        self.assertEqual(knight.effectiveness_raw, 175000)
        self.assertEqual(knight.stat_cache, EntrySixStatCache12003(0, 0, 8750000, 1750000, 0, 0))
        self.assertEqual(knight.ledger["selected_stage"], "post291F940_pre291C467")
        self.assertEqual([row["branch"] for row in knight.ledger["effectiveness_terms"]][1:3],
                         ["zero_operand_skips_property"] * 2)
        self.assertFalse(knight.ledger["constructor_final_stage_inferred"])

        # Same production observation is usable for current arithmetic only.
        observed = {"character_id": 56513, "prowess": 0, "effectiveness_context": {
            "character_id": 29829, "modifier_raw": [25000, None, None, 2000, -1000, 0, 0, 0, 0],
            "operand_raw": [Q, 0, 0, 30*Q, 10*Q, 0, 0, 4*Q, 9*Q]}}
        current = compute_knight_stat_cache_at_stage_12003(
            knight_inputs_from_current_observation_12003(
                {"loaded_damage_multiplier": 50, "loaded_toughness_multiplier": 10}, observed))
        self.assertTrue(current.ready)
        self.assertEqual(current.stat_cache, knight.stat_cache)
        self.assertEqual(current.ledger["selected_stage"], "frozen_current_character_values")
        missing = compute_knight_stat_cache_at_stage_12003(
            knight_inputs_from_person_stages_12003(
                linked, replace(selected, context=None), loaded_damage_multiplier=50,
                loaded_toughness_multiplier=10))
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.stat_cache)

        # Exact large-product branch uses maximum decomposition; negative
        # signed ordering can differ from decomposing the minimum.
        self.assertEqual(knight_effectiveness_fixed_mul_12003(-5000000001, 7), -350000)
        self.assertEqual(knight_effectiveness_fixed_mul_12003(-5000000001, -7), 350000)

        own_levy, own_knight = before.sides[0].entries
        enemy_knight, enemy_ordinary = before.sides[1].entries
        ordinary_stats = EntrySixStatCache12003(200, 123, 321000, 222000, 111000, 444000)
        supplied = (
            FinalEntryStatInput12003(
                1, enemy_ordinary.bucket, enemy_ordinary.bucket_index,
                enemy_ordinary.native_carmy_id, enemy_ordinary.state.regiment_id,
                before.province_id+1, "247AB41", ordinary_stats,
                {"stage": "different_Province_is_not_final_Combat_tuple"}),
            final_entry_input_from_knight_stage_12003(
                knight, side_index=1, entry=enemy_knight, target_province_id=before.province_id),
            final_entry_input_from_knight_stage_12003(
                replace(knight, linked_character_full_id=56514),
                side_index=0, entry=own_knight, target_province_id=before.province_id),
            FinalEntryStatInput12003(
                0, "levy", 0, own_levy.native_carmy_id, own_levy.state.regiment_id,
                before.province_id, "247AB32", ordinary_stats,
                {"stage": "explicit_getter_output_after_constructor_sources"}),
        )
        result = apply_first_contact_final_stat_refresh_12003(before, supplied)
        self.assertFalse(result.bounded_refresh_ready)
        self.assertEqual(result.refreshed_entry_count, 3)
        self.assertEqual([row["identity"][:3] for row in result.entry_ledger],
                         [(0, "levy", 0), (0, "men_at_arms", 0),
                          (1, "men_at_arms", 0), (1, "men_at_arms", 1)])
        self.assertIn("different_combat_province", result.missing_inputs[0])
        self.assertEqual(result.condition.sides[1].entries[1], enemy_ordinary)
        self.assertEqual(result.condition.sides[0].entries[1].state.current_raw, 0)
        self.assertEqual(result.condition.sides[0].entries[1].effective_damage_raw, 8750000)
        for old_side, new_side in zip(before.sides, result.condition.sides):
            self.assertEqual(replace(new_side, entries=old_side.entries), old_side)
            for old, new in zip(old_side.entries, new_side.entries):
                self.assertEqual(
                    (new.starting_raw, new.state.current_raw, new.state.soft_casualties_raw,
                     new.hard_casualties_raw, new.fights_in_main_phase,
                     new.knight_character_id_raw, new.backing_components),
                    (old.starting_raw, old.state.current_raw, old.state.soft_casualties_raw,
                     old.hard_casualties_raw, old.fights_in_main_phase,
                     old.knight_character_id_raw, old.backing_components))
        self.assertEqual(before.source_snapshot, snapshot_before)
        self.assertEqual(result.condition.source_snapshot, snapshot_before)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.native_write_performed)
        self.assertFalse(result.historical_stage_observed)
        self.assertEqual(result.actual_game_days_advanced, 0)


if __name__ == "__main__":
    unittest.main()
