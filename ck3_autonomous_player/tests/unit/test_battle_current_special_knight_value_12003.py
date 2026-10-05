"""One new production-normalizer -> raw knight kernel -> batch-value case."""
from copy import deepcopy
import unittest

from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot
from xar_autoplayer.bridge.combat_contract import (
    combat_simulation_encounter_scope, normalize_combat_simulation_inputs,
)
from xar_autoplayer.simulation.battle_current_special_knight_value_12003 import (
    estimate_current_special_knight_initial_stats_12003,
)

OBSERVATIONS = {}


def normalize_source(raw):
    return normalize_combat_simulation_inputs(
        raw, expected_target_province_id=900,
        expected_attacker_entry_province_id=800,
        expected_encounter_scope=combat_simulation_encounter_scope(_snapshot(), [12], [22]))


def special_knight_value_source():
    raw = _combat_inputs()
    context = {
        "schema": "ck3_12003_knight_effectiveness_context_v1", "status": "available",
        "character_id": 29829, "modifier_indices": list(range(0xC1, 0xCA)),
        "modifier_raw": [25000, -1000, 3000, 2000, -1000, 500, -700, 800, -900],
        "operand_raw": [100000, 0, -50000, 3000000, 1000000, 900000, 0, 400000, 900000],
        "scale": 100000, "unavailable_reason": None,
    }
    for index, army in enumerate(raw["armies"]):
        linked, prowess, effectiveness = (56513, 0, 173100) if index == 0 else (56514, 7, 125000)
        selected = deepcopy(context)
        if index == 1:
            selected.update(status="unavailable", modifier_raw=None, operand_raw=None,
                            unavailable_reason="effectiveness_context_modifiers_unavailable")
        army["knights"] = {
            "status": "available", "loaded_damage_multiplier": 50,
            "loaded_toughness_multiplier": 10, "unavailable_reason": None,
            "members": [{"eligible": True, "character_id": linked,
                         "source_regiment_id": army["regiments"][0]["regiment_id"],
                         "army_id": army["native_carmy_id"],
                         "participant_army_membership_verified": True,
                         "prowess": prowess, "knight_effectiveness_raw": effectiveness,
                         "effective_damage_raw": max(1, prowess)*effectiveness*50,
                         "effective_toughness_raw": max(1, prowess)*effectiveness*10,
                         "scale": 100000, "effectiveness_context": selected}],
        }
    return raw


class CurrentSpecialKnightValue12003Tests(unittest.TestCase):
    def test_nonempty_selected_context_independent_gap_and_known_empty_coverage(self):
        raw = special_knight_value_source()
        original = deepcopy(raw)
        normalized = normalize_source(raw)
        result = estimate_current_special_knight_initial_stats_12003(
            normalized, source_provenance={"kind": "offline_source_shaped_fixture"})
        ready, partial = result["members_in_query_order"]
        self.assertEqual((ready["linked_character_full_id"], ready["selected_character_full_id"]),
                         (56513, 29829))
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["effectiveness_raw"], 173100)
        self.assertEqual(ready["initial_stat_cache"], {
            "effective_max_size": 0, "effective_siege_raw": 0,
            "effective_damage_raw": 8655000, "effective_toughness_raw": 1731000,
            "effective_pursuit_raw": 0, "effective_screen_raw": 0})
        self.assertTrue(all(ready["observed_matches_calculation"].values()))
        terms = ready["calculation_ledger"]["effectiveness_terms"]
        self.assertEqual(terms[1]["branch"], "zero_operand_skips_property")
        self.assertEqual(terms[2]["term_q64"], -1500)
        self.assertFalse(partial["ready"])
        self.assertIsNone(partial["initial_stat_cache"])
        self.assertEqual(partial["current_observation"]["effective_damage_raw"], 43750000)
        self.assertIn("armies[1].knights.members[0].operand_raw[0]", result["missing_inputs"])
        self.assertEqual((result["observed_member_count"], result["ready_member_count"]), (2, 1))
        self.assertFalse(result["all_observed_member_inputs_ready"])
        self.assertEqual(result["ready_member_contributions_by_role"]["attacker"]["ready_member_damage_raw_sum"], 8655000)
        self.assertEqual(result["ready_member_contributions_by_role"]["defender"]["partial_member_count"], 1)

        # The same selected source can qualify both linked knights; it does not
        # replace the second knight's separate prowess or invent a final stage.
        coherent = deepcopy(raw)
        coherent["armies"][1]["knights"]["members"][0]["effectiveness_context"] = deepcopy(
            coherent["armies"][0]["knights"]["members"][0]["effectiveness_context"])
        member = coherent["armies"][1]["knights"]["members"][0]
        member.update(knight_effectiveness_raw=173100,
                      effective_damage_raw=60585000, effective_toughness_raw=12117000)
        complete = estimate_current_special_knight_initial_stats_12003(
            normalize_source(coherent))
        self.assertTrue(complete["all_observed_member_inputs_ready"])
        self.assertEqual(complete["ready_member_count"], 2)
        self.assertEqual(complete["ready_member_contributions_by_role"]["defender"]["ready_member_damage_raw_sum"], 60585000)

        coefficient_gap = deepcopy(coherent)
        coefficient_gap["armies"][0]["knights"]["loaded_damage_multiplier"] = None
        missing_coefficient = estimate_current_special_knight_initial_stats_12003(
            normalize_source(coefficient_gap))
        self.assertFalse(missing_coefficient["all_observed_member_inputs_ready"])
        self.assertIn("armies[0].knights.members[0].loaded_damage_multiplier",
                      missing_coefficient["missing_inputs"])
        self.assertEqual(missing_coefficient["ready_member_count"], 1)
        self.assertEqual(missing_coefficient["members_in_query_order"][0]["effectiveness_raw"], 173100)

        empty = deepcopy(raw)
        for army in empty["armies"]:
            army["knights"]["members"] = []
        empty_value = estimate_current_special_knight_initial_stats_12003(
            normalize_source(empty))
        self.assertTrue(empty_value["all_observed_member_inputs_ready"])
        self.assertEqual(empty_value["observed_member_count"], 0)
        for value in (result, complete, missing_coefficient, empty_value):
            self.assertFalse(value["full_entry_ready"])
            self.assertFalse(value["constructor_final_stage_inferred"])
            self.assertFalse(value["native_write_performed"])
            self.assertEqual(value["actual_game_days_advanced"], 0)
        self.assertEqual(raw, original)
        OBSERVATIONS.update(partial_value=result, complete_value=complete,
                            missing_coefficient_value=missing_coefficient, empty_value=empty_value)


if __name__ == "__main__":
    unittest.main()
