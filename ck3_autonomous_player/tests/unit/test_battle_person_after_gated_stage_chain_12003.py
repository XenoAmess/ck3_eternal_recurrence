"""One new four-family person source chain -> six-skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_gated_stage_chain_12003 import gated_frame
from test_battle_person_after_gated_tail_12003 import (
    FIELD, FAMILIES, after_gated_source, availability, date, named, operand,
)
from test_battle_person_tail_stage_chain_12003 import Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def after_gated_frame():
    raw = gated_frame()
    leaf = after_gated_source()[FIELD]

    def use_prowess_key(value):
        if isinstance(value, dict):
            if "keys_u16" in value:
                value["keys_u16"] = [5 if key != 65535 else key for key in value["keys_u16"]]
            for item in value.values():
                use_prowess_key(item)
        elif isinstance(value, list):
            for item in value:
                use_prowess_key(item)

    use_prowess_key(leaf)
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD] = leaf
    return raw


class PersonAfterGatedStageChain12003Tests(unittest.TestCase):
    def test_four_actual_families_join_skills_and_keep_dynamic_and_empty_source_boundaries(self):
        raw = after_gated_frame()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="after_gated_tail")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "post326A8E0_and2920310_pre291CB14")
        self.assertEqual(result.context.aggregate_properties.values_q64, (85 * Q,))
        self.assertEqual(result.context.weighted_count, 38)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 91))
        requests = result.independent_stage_outputs["after_gated_tail"]
        self.assertEqual(len(requests), 16)
        self.assertEqual([row.source_ordinal for row in requests], [0] + [1] * 6 + [2] * 5 + [3] * 4)
        self.assertEqual([row.weight_q64 for row in requests], [Q] * 16)
        self.assertEqual([row.first_row_index for row in requests[1:7]], [0, 0, 0, 1, 1, 1])
        self.assertEqual([row.base_property_block["keys_count"] for row in requests[-4:]], [1, 0, 0, 0])
        normalized = person["current_context_source_inputs"][FIELD]
        self.assertEqual(normalized[FAMILIES[0]]["completed_months_raw"], 2)
        self.assertEqual(normalized[FAMILIES[0]]["chosen_date_selection"], "handle")
        self.assertIs(requests[1].base_property_block,
                      normalized[FAMILIES[1]]["rows"][0]["base_pc"]["property_block"])

        dynamic_raw = deepcopy(raw)
        dynamic = dynamic_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD]
        dynamic.update(availability(False, "kind_missing"))
        branch = dynamic[FAMILIES[2]]
        branch.update(availability(False, "definition_600_dynamic_fixed_result"))
        row = branch["rows"][0]
        row.update(ready=False, reason="definition_600_dynamic_fixed_result")
        for key in ("kind", "other_kind"):
            item = row[key]
            item.update(availability(False, "definition_600_dynamic_fixed_result"))
            item.update(kind_raw=None, rule={**availability(False, "definition_600_dynamic_fixed_result"),
                "mode_raw": 1, "tree_present": False, "tree_identity": None, "named_present": False,
                "named": named(), "target_count_raw": 1, "raw_98_q64": None,
                "value_q64": None, "selection": "dynamic_targets"})
        row["tier_pc"] = operand()
        row["other_tier_pc"] = operand()
        _, partial, partial_skills = evaluate(dynamic_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "post2920310_current1B8_preCurrent1C0")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (68 * Q,))
        self.assertEqual(partial.context.weighted_count, 32)
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 74))
        self.assertEqual(len(partial.independent_stage_outputs["after_gated_tail"]), 7)
        self.assertEqual(len(partial.independent_stage_outputs["after_gated_tail.related_court_positions"]), 4)
        ledger = next(item for item in partial.source_ledger["ordered_tail_stages"] if item["stage"] == "after_gated_tail")
        self.assertEqual([item["in_contiguous_family_prefix"] for item in ledger["after_gated_family_stages"]],
                         [True, True, False, False])

        empty_raw = deepcopy(raw)
        empty = empty_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD][FAMILIES[0]]
        empty.update(level_raw=None, handle_date=date(), fifth_date=date(), current_date=date(),
                     chosen_date_selection=None, completed_months_raw=None)
        for key in ("level_rows", "month_rows"):
            empty[key] = {**availability(), "count_raw": 0, "array_present": None, "rows": []}
        _, empty_result, empty_skills = evaluate(empty_raw)
        self.assertTrue(empty_result.ready, empty_result.missing_inputs)
        self.assertEqual(empty_result.context.aggregate_properties.values_q64, (81 * Q,))
        self.assertEqual(empty_result.context.weighted_count, 37)
        self.assertEqual(empty_skills.final_cache_points, (6, 6, 6, 6, 6, 87))
        self.assertEqual(len(empty_result.independent_stage_outputs["after_gated_tail"]), 16)
        self.assertEqual(empty_result.independent_stage_outputs["after_gated_tail"][0].base_property_block["keys_count"], 0)
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["after_gated_native_evaluation_equivalence_claimed"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            source_requests=16, materialized_weighted_rows=38, four_family_request_counts=[1, 6, 5, 4],
            source_occurrence_and_empty_pair_order_preserved=True,
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            independently_ready_related_requests=4, dynamic_typed_result_not_guessed=True,
            empty_326_skills=empty_skills.final_cache_points, empty_326_source_request_preserved=True,
            next_source_stage="291CB14_provider192_2920850",
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
