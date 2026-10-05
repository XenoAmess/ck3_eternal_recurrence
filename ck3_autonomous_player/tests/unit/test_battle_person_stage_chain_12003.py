"""A new joined current-person observation -> ordered chain -> skill case.

Reuse fixture builders without executing their old test cases. The trait
observer's actual source schema is supplied by its production contract fixture.
"""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import frame, normalize, context, properties
from test_battle_pre_291e210_1640_12003 import section as pre_source
from test_battle_post_291d7e0_sources_12003 import section as post_source
from test_battle_person_helper_291f0a0_12003 import source as h0_source
from test_battle_person_later_direct_12003 import source as direct_source
from test_battle_person_remaining_helpers_12003 import source as tail_source
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainStart12003, START_STAGE_12003, STOP_STAGE_12003,
    assemble_current_person_stage_chain_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import from_raw_numeric_inputs_12003

Q, ACTOR = 100000, 29829
OBSERVATIONS = {}


def pc(value=Q):
    return {"keys_count": 1, "values_count": 1, "keys_u16": [5],
            "values_q64": [value], "reason": None}


def _unit_nonempty_blocks(value):
    if isinstance(value, dict):
        if value.get("keys_count", 0):
            value.update(pc())
        else:
            for child in value.values():
                _unit_nonempty_blocks(child)
    elif isinstance(value, list):
        for child in value:
            _unit_nonempty_blocks(child)


def joined_sources(trait_leaf):
    source = pre_source()
    source["pre_291e210_1640"]["property_block"] = pc()
    for key, factory in (("post_291d7e0_sources", post_source),
                         ("helper_291f0a0", h0_source),
                         ("later_direct_291c3fb_44c", direct_source),
                         ("later_helpers_291f550_291f940", tail_source)):
        source[key] = factory()[key]
    _unit_nonempty_blocks(source)
    # Direct source builder has legal empty PCs; make its three admitted
    # occurrences nonempty so losing duplicates changes the six-skill result.
    direct = source["later_direct_291c3fb_44c"]
    for row in direct["ordered_rows"][:2]:
        row["property_block"] = pc()
    direct["guarded_property_block"] = pc()
    resolution = {"status": "native_fallback", "requested_full_id": None,
                  "selected_full_id": None, "reason": None}
    span = lambda rows: {"selected_source": "fixture_actual_span", "count": len(rows),
                         "rows": rows, "reason": None}
    source["branch_291e210"] = {
        "status": "available", "ready": True, "component_present": True,
        "first_relation_resolution": resolution.copy(), "second_relation_resolution": resolution.copy(),
        "house_resolution": resolution.copy(), "house_extra_enabled": False,
        "selected_lifestyle_span": span([
            {"native_index": i, "definition_identity": "a", "weight_q64": Q}
            for i in range(2)]),
        "selected_dynasty_span": span([]), "selected_house_span": span([]),
        "selected_house_extra_span": span([]),
        "definition_blocks": [{"definition_identity": "a", "properties": pc(3 * Q)}],
        "reason": None,
    }
    row = {"native_index": 0, "source_identity": "b", "base_properties": pc(2 * Q),
           "auxiliary_410_provenance": "fixture_native_auxiliary", "auxiliary_retained_identity": None,
           "auxiliary_retained_present": False, "auxiliary_tag_u32": 0, "reason": None}
    for kind in "abc":
        row["conditional_" + kind + "_count"] = 0
        row["conditional_" + kind + "_rows"] = []
    source["branch_291d7e0"] = {
        "status": "available", "ready": True, "base_inputs_ready": True,
        "component_present": True, "selected_source": "fixture_actual_source",
        "source_count": 1, "source_rows": [row], "conditional_a_fallback_properties": None,
        "government_token_count": None, "government_token_ids_i32": None,
        "government_source": "unused", "condition_registry_guard": None,
        "condition_fallback_guard": None, "token_manager_present": None, "reason": None,
    }
    source["trait_stage_291d460"] = trait_leaf
    return source


def tasks():
    def branch(kind, value):
        return {"status": "available", "complete_no_contribution": False, "vectors_ready": True,
            "evaluated_rows": [{"task_native_index": 0, "declaration_native_index": 0,
                "contributor_kind": kind, "scope_root_character_id_raw": ACTOR,
                "scope_saved_character_id_raw": -1, "declaration_scale_q64": 7 * Q,
                "properties": properties((5, value)), "modifier_flags_raw": 0,
                "source_provenance": "explicit_native_evaluated_vector"}],
            "prefix_before": None, "prefix_source": "unobserved", "aggregate_properties_after": None,
            "aggregate_source": "unobserved", "unavailable_reason": None}
    # Independently complete evaluated vectors, with raw task census and old
    # historical aggregates unobserved. The assembler needs the vectors only.
    return {"schema_version": 1, "status": "partial", "character_id": ACTOR,
        "raw_task_inputs_ready": False, "branch_vectors_ready": True,
        "owner_council_present": None, "ordered_owned_tasks": None,
        "councillor_task_link_present": None, "councillor_task": None,
        "owned_passive": branch("position_passive", 4 * Q),
        "councillor_position_task": branch("councillor_task", -Q),
        "unavailable_reason": "raw_task_census_not_supplied_in_new_vector_fixture"}


class PersonStageChain12003Tests(unittest.TestCase):
    def test_normalized_join_retains_frontier_and_all_stage_occurrences(self):
        # Source-proven known-empty actual trait array, not an omitted unknown
        # helper. Positive composites are owned by the observer's own fixture.
        trait_leaf = {"status": "available", "ready": True, "character_id": ACTOR,
                      "trait_count": 0, "trait_array_present": None, "rows": [], "reason": None}
        for field in ("selector_a_key_raw", "selector_a_selection", "selector_a_identity",
                      "selector_b_key_raw", "selector_b_selection", "selector_b_identity",
                      "selector_a_membership_count", "selector_a_keys_i32", "selector_b_primary_count",
                      "selector_b_primary_keys_i32", "selector_b_nested_count", "selector_b_nested_keys"):
            trait_leaf[field] = None
        raw = frame()
        state = raw["character_observations"][0]["current_person_state"]
        state["current_context_source_inputs"] = joined_sources(trait_leaf)
        state["current_context_task_position_inputs"] = tasks()
        before = deepcopy(raw)
        person = normalize(raw)
        start = PersonStageChainStart12003(ACTOR, context((5, Q)),
            source_provenance={"input": "explicit_postD1D0_logical_baseline"})
        chain = assemble_current_person_stage_chain_12003(person, start_baseline=start, character_full_id=ACTOR)
        self.assertTrue(chain.ready, chain.missing_inputs)
        self.assertEqual(chain.stage, STOP_STAGE_12003)
        self.assertEqual(chain.character_full_id, ACTOR)
        self.assertFalse(chain.full_person_preparation_ready)
        self.assertFalse(chain.full_entry_ready)
        self.assertEqual(chain.independent_stage_outputs["291E210"][0].weight_q64, 2 * Q)
        self.assertEqual(len(chain.independent_stage_outputs["later_direct"]), 3)
        self.assertEqual(chain.stage_contexts["post291DED0_pre291C2AE"].aggregate_properties.values_q64[0]
                         - chain.stage_contexts["post291D7E0_pre291C2A3"].aggregate_properties.values_q64[0], 4 * Q)
        numeric = from_raw_numeric_inputs_12003(person["raw_numeric_inputs"])
        projected = project_stage_chain_six_skills_12003(chain, numeric)
        self.assertTrue(projected.calculation_ready, projected.missing_inputs)
        self.assertEqual(projected.final_cache_points[:5], (6, 6, 6, 6, 6))
        # Baseline1 + preA1 + A6 + B2 + tasks4-1 + post3 + H0 six
        # + direct3 + 550 five + 940 four =34 points, then base6.
        self.assertEqual(projected.final_cache_points[5], 40)
        self.assertEqual(projected.ledger["assembled_context_stage"], STOP_STAGE_12003)
        self.assertEqual(raw, before)

        # A missing earlier actual stage keeps the A prefix, while genuine
        # later vectors remain useful independently and are never folded over it.
        raw_missing = deepcopy(raw)
        del raw_missing["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["trait_stage_291d460"]
        partial_person = normalize(raw_missing)
        partial = assemble_current_person_stage_chain_12003(partial_person, start_baseline=start, character_full_id=ACTOR)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "post291E210_pre291C28D")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (8 * Q,))
        self.assertEqual(len(partial.independent_stage_outputs["291DED0"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs["291F940"]), 5)
        bounded = project_stage_chain_six_skills_12003(partial, from_raw_numeric_inputs_12003(partial_person["raw_numeric_inputs"]))
        self.assertTrue(bounded.calculation_ready)
        self.assertEqual(bounded.final_cache_points, (6, 6, 6, 6, 6, 14))
        self.assertFalse(bounded.ledger["bounded_chain_ready"])
        self.assertEqual(person["raw_numeric_inputs"]["context"]["aggregate_properties"]["values_q64"], [99 * Q])
        OBSERVATIONS.update(ready_stage=chain.stage, ready_skills=projected.final_cache_points,
            partial_stage=partial.stage, partial_skills=bounded.final_cache_points,
            trait_requests=len(chain.independent_stage_outputs["291D460"]),
            source_whole_ready=person["current_context_source_inputs"]["ready"],
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
