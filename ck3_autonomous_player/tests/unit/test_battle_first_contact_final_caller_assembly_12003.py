"""One new production-normalizer/getter/caller/setter integration case."""
from copy import deepcopy
from dataclasses import replace
import unittest

from test_battle_current_condition import Q, SUBJECT, _entry, _raw_frame, _side
from test_battle_current_refresh import _counter
from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
from xar_autoplayer.bridge.maa_stat_inputs_contract import (
    ENV_NAMES, FIELDS, STAT_NAMES, normalize_maa_stat_inputs_v1,
)
from xar_autoplayer.bridge.ordinary_stat_inputs_contract import normalize_ordinary_stat_inputs_v1
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_first_contact_final_caller_assembly_12003 import (
    FinalCallerGetterOccurrence12003, assemble_closed_final_caller_12003,
)
from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import (
    EntrySixStatCache12003, PersonStatStage12003,
)
from xar_autoplayer.simulation.battle_maa_observed_inputs_12003 import maa_six_stats_from_combat_regiment_12003
from xar_autoplayer.simulation.battle_maa_regiment_stats_12003 import finish_maa_environment_stage_12003
from xar_autoplayer.simulation.battle_maa_source_stages_12003 import (
    add_maa_culture_contributions_12003, apply_maa_accolade_aggregate_stage_12003,
    construct_maa_baseline_stage_12003,
)
from xar_autoplayer.simulation.battle_ordinary_regiment_stats_12003 import (
    ordinary_six_stats_from_combat_regiment_12003,
    ordinary_six_stats_from_person_stage_12003,
)


def _properties(values):
    keys = sorted(values)
    return {"count": len(keys), "keys_u16": keys, "values_q64": [values[key] for key in keys]}


class FinalCallerAssembly12003Test(unittest.TestCase):
    def test_explicit_changed_and_held_sources_follow_both_calls_preserving_accounts(self):
        raw = _raw_frame(1)
        enemy = raw["defender"]["ordered_armies"][0]
        zero = _entry(8, enemy, bucket="men_at_arms", index=0,
                      current=0, damage=900000, toughness=800000, main=False)
        zero["starting_raw"] = Q
        raw["defender"] = _side(1, [enemy], raw["defender"]["levy_entries"],
                                [zero], [(enemy["owner_character_id"], 0)])
        _counter(raw, Q)
        normalized = normalize_battle_control_snapshot_v1(raw,
            expected_subject_public_cunit_id=SUBJECT,
            expected_observed_date_raw=raw["observed_date_raw"],
            expected_snapshot_revision=raw["snapshot_revision"])
        before = adapt_current_battle_condition(normalized)
        original = deepcopy(before.source_snapshot)
        province = before.province_id
        bases = {"siege_raw": 0, "damage_raw": 100000, "toughness_raw": 200000,
                 "pursuit_raw": -2, "screen_raw": 3}
        ordinary_leaf = normalize_ordinary_stat_inputs_v1({
            "status": "available", "selected_character_full_id": 71,
            "character_resolution": "generation_resolved",
            "aggregate_properties": _properties({}), "loaded_bases": bases,
            "scale": Q, "unavailable_reason": None}, name="new_caller_ordinary")
        held_ordinary = ordinary_six_stats_from_combat_regiment_12003(
            {"ordinary_stat_inputs_v1": ordinary_leaf})
        supplied_person = PersonStatStage12003(71, "supplied_context_A", {
            "aggregate_properties": _properties({0xB0: 50000, 0x1B3: 50000})}, None)
        changed_ordinary = ordinary_six_stats_from_person_stage_12003(
            supplied_person, loaded_bases=bases)

        def vector(*values):
            return dict(zip(STAT_NAMES, values))

        raw_maa = dict.fromkeys(FIELDS)
        raw_maa.update(
            status="available", source_target_province_id=province,
            source_regiment_full_id=7, selected_character_full_id=71,
            character_resolution="generation_resolved", inner_type_is_gdbo=True,
            selector_mode=False, selected_type_class=5,
            type_bases=vector(100, 100000, 200000, 300000, 400000, 500000),
            selected_properties=_properties({}), class_row_present=False,
            culture_full_id=80, government_index=0, government_rows=[], global_rows=[],
            selected_government_byte_4d6=1, linked_character_full_ids=[],
            accolade_blocks=[], definition620_present=False,
            environment_components={key: (None if "definition" in key else vector(0, 0, 0, 0, 0, 0))
                                    for key in ENV_NAMES},
            fallback_ordinary_bases=dict.fromkeys(STAT_NAMES[1:]), scale=Q)
        maa_leaf = normalize_maa_stat_inputs_v1(raw_maa, name="new_caller_maa")
        held_maa = maa_six_stats_from_combat_regiment_12003({"maa_stat_inputs_v1": maa_leaf})

        # The explicit changed branch starts from loaded type values, not the
        # observed final tuple. Reuse the existing culture/context/accolade APIs.
        type_stage = add_maa_culture_contributions_12003(
            EntrySixStatCache12003(220, 1000, 300000, 400000, 0, 6000),
            selected_type_class=5, government_rows=(), global_rows=(),
            stage="supplied_type_and_culture_B")
        empty_person = PersonStatStage12003(
            71, "supplied_context_B", {"aggregate_properties": _properties({})}, None)
        class_args = {"class_row_present": False,
                      "class_add_keys_u16": None, "class_mult_keys_u16": None}
        baseline = construct_maa_baseline_stage_12003(type_stage, person_stage=empty_person,
            extra_source=None, selector_mode=False, selected_government_byte_4d6=1,
            selected_script_value_4e_q64=None, stage="supplied_baseline_B", **class_args)
        after_accolade = apply_maa_accolade_aggregate_stage_12003(baseline,
            accolade_person_stage=empty_person, stage="supplied_accolade_B", **class_args)
        zero_cache = EntrySixStatCache12003(0, 0, 0, 0, 0, 0)
        components = {name: zero_cache for name in ENV_NAMES}
        components["type_terrain"] = EntrySixStatCache12003(5, 0, 50000, -450000, 0, 0)
        components["linked_province"] = EntrySixStatCache12003(0, 0, 0, 0, 0, -7000)
        changed_maa = finish_maa_environment_stage_12003(after_accolade,
            stage="supplied_environment_B", definition620_present=False,
            components=components, source_province_id=province, linked_character_full_ids=())
        self.assertTrue(all(result.ready for result in (
            held_ordinary, changed_ordinary, held_maa, changed_maa)))

        def occurrence(side, entry, kind, result, mode):
            return FinalCallerGetterOccurrence12003(
                side, entry.bucket, entry.bucket_index, entry.native_carmy_id,
                entry.state.regiment_id, province, kind, result, mode)

        own_levy, own_maa = before.sides[0].entries
        enemy_levy, enemy_maa = before.sides[1].entries
        # Source order deliberately differs; native call/entry order governs.
        supplied = (
            occurrence(1, enemy_maa, "maa", changed_maa, "explicit_named_stage"),
            occurrence(0, own_maa, "maa", held_maa, "declared_held_current_source"),
            occurrence(1, enemy_levy, "ordinary", held_ordinary, "declared_held_current_source"),
            occurrence(0, own_levy, "ordinary", changed_ordinary, "explicit_named_stage"),
        )
        output = assemble_closed_final_caller_12003(before, supplied)
        self.assertTrue(output.bounded_refresh_ready)
        self.assertEqual(output.refreshed_entry_count, 4)
        self.assertEqual([row["call_site"] for row in output.entry_ledger],
                         ["247AB32", "247AB32", "247AB41", "247AB41"])
        self.assertEqual([row["identity"][:3] for row in output.entry_ledger],
                         [(0, "levy", 0), (0, "men_at_arms", 0),
                          (1, "levy", 0), (1, "men_at_arms", 0)])
        self.assertEqual([row.effective_damage_raw for side in output.condition.sides for row in side.entries],
                         [225000, 200000, 100000, 350000])
        changed_entry = output.condition.sides[1].entries[1]
        self.assertEqual((changed_entry.state.current_raw, changed_entry.state.toughness_raw,
                          changed_entry.state.screen_raw), (0, Q, -1000))
        self.assertEqual([row["source"]["getter_real_stage"] for row in output.entry_ledger],
                         ["supplied_context_A", held_maa.stage, held_ordinary.stage, "supplied_environment_B"])
        for old_side, new_side in zip(before.sides, output.condition.sides):
            self.assertEqual(replace(new_side, entries=old_side.entries), old_side)
            for old, new in zip(old_side.entries, new_side.entries):
                self.assertEqual(
                    (new.starting_raw, new.state.current_raw, new.state.soft_casualties_raw,
                     new.hard_casualties_raw, new.fights_in_main_phase,
                     new.knight_character_id_raw, new.backing_components),
                    (old.starting_raw, old.state.current_raw, old.state.soft_casualties_raw,
                     old.hard_casualties_raw, old.fights_in_main_phase,
                     old.knight_character_id_raw, old.backing_components))
        self.assertEqual(output.condition.source_snapshot, original)
        self.assertEqual(before.source_snapshot, original)
        self.assertFalse(output.full_entry_ready)
        self.assertFalse(output.native_write_performed)
        self.assertFalse(output.historical_stage_observed)
        self.assertFalse(output.ledger["getter_math_duplicated"])

        # A real unavailable MAA source remains unrefreshed at this assembly.
        missing_source = deepcopy(raw_maa)
        missing_source.update(status="unavailable", selected_properties=None,
                              unavailable_reason="maa_selected_context_unavailable")
        missing_result = maa_six_stats_from_combat_regiment_12003({
            "maa_stat_inputs_v1": normalize_maa_stat_inputs_v1(missing_source, name="new_missing")})
        partial = assemble_closed_final_caller_12003(before, (
            supplied[0], replace(supplied[1], getter_result=missing_result), *supplied[2:]))
        self.assertFalse(partial.bounded_refresh_ready)
        self.assertEqual(partial.refreshed_entry_count, 3)
        self.assertEqual(partial.condition.sides[0].entries[1], own_maa)
        self.assertIn("partial_stat_calculation", partial.missing_inputs[0])
        self.assertEqual(partial.entry_ledger[1]["source"]["getter_missing_inputs"],
                         ("maa_stat_inputs_v1.available",))


if __name__ == "__main__":
    unittest.main()
