"""One new conference family -> actual weighted ranks -> skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import frame, normalize
from test_battle_person_2922070_stage_chain_12003 import ready_source
from test_battle_person_tail_stage_chain_12003 import pc, Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def selected_object(full_id, offset):
    return {"requested_full_id_raw": full_id, "selection": "registry_full_id_" + offset,
            "identity": "object:" + str(full_id), "full_id_raw": full_id, "reason": None}


def conference():
    return {
        "status": "available", "ready": True, "character_id": ACTOR, "carrier_present": True,
        "conference": selected_object(-2147483627, "8"), "conference_magic_raw": 0x436F6E66,
        "conference_admitted": True, "character_magic_raw": 0x43686172,
        "character_full_id_raw": ACTOR, "character_admitted": True, "admitted": True,
        "relation_registry_present": True, "first": selected_object(100, "10"),
        "second": selected_object(200, "10"),
        "first_group_identity": "pointer:0000000000000000",
        "second_group_identity": "pointer:0000000000000000", "category": "same_identity",
        "owner_full_id_raw": ACTOR + 1, "owner_matches": False, "reason": None,
        "pack": {"status": "available", "ready": True, "configuration_identity": "conf-config",
            "target_q64": 50, "enabled_u8": 1, "count_raw": 3, "array_present": True,
            "probes": [{"native_index": 2, "timestamp_q64": 70},
                       {"native_index": 1, "timestamp_q64": 40}],
            "selected_native_index": 1, "selection": "last_native_row_at_or_before_target",
            "pack_identity": "actual-inline-row1", "default_guard_raw": None, "reason": None},
        "families": [{"status": "available", "ready": True, "native_index": i,
            "admitted": True, "pc_offset": offset, "property_identity": "pack:PC:" + str(offset),
            "property_block": pc((i + 1) * Q), "reason": None}
            for i, offset in enumerate((0xC70, 0xE30, 0x730, 0x8F0))],
    }


def middle():
    families = []
    for i, (key, adjustment, value) in enumerate(zip((45, 44, 46, 47), (0, -2 * Q, Q, -Q), (Q, 2 * Q, Q, 3 * Q))):
        families.append({"status": "available", "ready": True, "native_index": i,
            "score_q64": None, "override_raw": None, "threshold_count": None,
            "threshold_array_present": None, "thresholds_consumed_q64": None,
            "rank_raw": 0, "manager_count_raw": 1, "definition_selection": "manager_rank_index",
            "definition_identity": "rank0:" + str(i), "definition_gate_raw": 1, "admitted": True,
            "weight_carrier_present": True, "weight_owner_matches": True,
            "weight_source_selection": "exact_owner_carrier_10", "weight_source_identity": "actual-weight-PC",
            "weight_default_guard_raw": None, "weight_keys_count_raw": 1, "weight_key_u16": key,
            "weight_key_probes": [{"native_index": 0, "key_u16": key}, {"native_index": 0, "key_u16": key}],
            "weight_found": True, "weight_native_index": 0, "weight_value_q64": adjustment,
            "weight_q64": Q + adjustment, "property_identity": "rank0:PC:" + str(i),
            "property_block": pc(value), "reason": None})
    unavailable = {"status": "unavailable", "ready": False, "header_selection": None,
                   "count": None, "array_present": None, "rows": None, "reason": "unobserved_FB10"}
    return {"status": "partial", "ready": False, "character_id": ACTOR, "reason": "unobserved_FB10",
        "helper_291f260": {"status": "available", "ready": True, "component_present": False,
            "families": families, "reason": None},
        "helper_291fb10": {"status": "unavailable", "ready": False, "land_present": None,
            "preferred": deepcopy(unavailable), "list_218": deepcopy(unavailable),
            "list_248": deepcopy(unavailable), "reason": "unobserved_FB10"}}


class PersonConferenceStageChain12003Tests(unittest.TestCase):
    def test_actual_conference_and_ranks_extend_and_preserve_internal_prefix_on_family_gap(self):
        raw = frame()
        section = ready_source()
        section["conference_24b1d00"] = conference()
        section["middle_helpers_291f260_291fb10"] = middle()
        raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"] = section
        original = deepcopy(raw)
        person = normalize(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})
        result = continue_current_person_stage_chain_tail_12003(person, prior,
            character_full_id=ACTOR, through_stage="291F260")
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "post291F260_pre291C558")
        self.assertEqual(result.context.aggregate_properties.values_q64, (24 * Q,))
        self.assertEqual(result.context.weighted_count, 12)
        self.assertEqual(result.source_ledger["first_contiguous_observation_dependency"], "signed2F8_provider_bucket")
        normalized = person["current_context_source_inputs"]
        self.assertFalse(normalized["middle_helpers_291f260_291fb10"]["ready"])
        self.assertEqual(normalized["conference_24b1d00"]["pack"]["selected_native_index"], 1)
        self.assertIsNone(normalized["conference_24b1d00"]["pack"]["default_guard_raw"])
        for family in ("classified_owner", "classified_common", "owner_common", "unconditional"):
            self.assertEqual(len(result.independent_stage_outputs["conference24B1D00." + family]), 1)
        weights = [row.weight_q64 for row in result.independent_stage_outputs["291F260"]]
        self.assertEqual(weights, [Q, -Q, 2 * Q, 0])
        numeric = from_raw_numeric_inputs_12003(person["raw_numeric_inputs"])
        projected = project_stage_chain_six_skills_12003(result, numeric)
        self.assertTrue(projected.calculation_ready, projected.missing_inputs)
        self.assertEqual(projected.final_cache_points, (6, 6, 6, 6, 6, 30))

        partial_raw = deepcopy(raw)
        helper = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["conference_24b1d00"]
        helper.update(status="partial", ready=False, reason="classified_common_PC_unavailable")
        helper["families"][1].update(status="partial", ready=False,
            property_block=None, reason="classified_common_PC_unavailable")
        partial_person = normalize(partial_raw)
        partial = continue_current_person_stage_chain_tail_12003(partial_person, prior,
            character_full_id=ACTOR, through_stage="291F260")
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "post24B1D00_classified_owner_pre24B1E67")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (14 * Q,))
        self.assertEqual(len(partial.independent_stage_outputs["conference24B1D00"]), 1)
        for family in ("owner_common", "unconditional"):
            self.assertEqual(len(partial.independent_stage_outputs["conference24B1D00." + family]), 1)
        self.assertEqual(len(partial.independent_stage_outputs["291F260"]), 4)
        partial_skills = project_stage_chain_six_skills_12003(partial,
            from_raw_numeric_inputs_12003(partial_person["raw_numeric_inputs"]))
        self.assertTrue(partial_skills.calculation_ready)
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 20))
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["all_tail_source_stream_ready"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=projected.final_cache_points,
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            mapped_pack_native_index=1, inline_default_guard_unused=True,
            rank_weights=weights, independent_later_conference_families_preserved=True,
            next_source_stage=result.source_ledger["first_contiguous_observation_dependency"],
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
