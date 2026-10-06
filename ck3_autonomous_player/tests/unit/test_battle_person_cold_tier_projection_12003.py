"""One new normalizer-to-stage case for source-derived cold tier emptiness."""
from copy import deepcopy
import json
import unittest

from test_battle_person_stage_baseline_12003 import ACTOR, Q, frame, normalize
from _following_2921350_fixture import following2921350_cold_leaf
from following_2921020_fixture_inputs import (
    build_following2921020_positive_leaf, build_following2921020_nonowner_leaf,
)
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainStart12003, continue_explicit_person_following_stages_12003,
    project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}
COLD = "tier_default_2560620_result"
INCOMING, AFTER1350, AFTER1020 = (
    "post2920D60_pre291CD9D", "post2921350_pre291CDA8", "post2921020_pre291CDB3")


def source_frame(first, second=None):
    raw = frame()
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"] = {
        "status": "partial", "ready": False, "character_id": ACTOR,
        "branch_291e210": None, "reason": "earlier_actual_sources_not_observed",
        "following_2921350": first,
        "following_2921020": build_following2921020_positive_leaf() if second is None else second,
    }
    return raw


class ColdTierProjection12003Tests(unittest.TestCase):
    def test_explicit_normal_return_keeps_raw_cold_and_other_group_contributions(self):
        baseline = PersonStageChainStart12003(ACTOR,
            NativeModifierContext12003(PropertyContainer12003((2,), (2 * Q,), 1), (), 0),
            stage=INCOMING, source_provenance={
                "input_kind": "explicit_conditional_fixture_post2920D60_context",
                "historical_stage_observed": False, "earlier_admission_proved": False,
                "coherent_live_pair_observed": False,
            })

        def evaluate(first, second=None, *, projected=True):
            raw = source_frame(first, second)
            frozen = deepcopy(raw)
            person = normalize(raw)
            result = continue_explicit_person_following_stages_12003(person,
                start_baseline=baseline, project_cold_initializer_normal_return=projected)
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertEqual(raw, frozen)
            self.assertEqual(person["raw_numeric_inputs"]["context"], frozen[
                "character_observations"][0]["current_person_state"]["raw_numeric_inputs"]["context"])
            self.assertFalse(person["current_context_source_inputs"]["ready"])
            self.assertFalse(raw["battle_terminal_transition_ready"])
            self.assertFalse(result.full_person_preparation_ready)
            self.assertFalse(result.full_entry_ready)
            self.assertFalse(result.native_write_performed)
            self.assertFalse(result.source_ledger["native_cold_initializer_invoked"])
            self.assertFalse(result.source_ledger["actual_cold_tls_sync_recheck_or_completion_observed"])
            self.assertFalse(result.source_ledger["fresh_installed_stage_identity_inferred"])
            return person, result, skills

        cold = following2921350_cold_leaf()
        _, observed, observed_skills = evaluate(cold, projected=False)
        self.assertFalse(observed.ready)
        self.assertEqual(observed.stage, INCOMING)
        self.assertEqual(observed_skills.final_cache_points, (6, 6, 8, 6, 6, 6))

        for guard in (0, -1):
            first = deepcopy(cold)
            for province in first["provinces"]:
                province["sources"][2]["tiers"]["default_guard_raw_i32"] = guard
            person, projected, skills = evaluate(first)
            leaf = person["current_context_source_inputs"]["following_2921350"]
            self.assertFalse(leaf["ready"])
            self.assertEqual(leaf["reason"], COLD)
            for province in leaf["provinces"]:
                self.assertIsNone(province["sources"][2]["tiers"]["pc"]["property_block"])
                self.assertIsNone(province["sources"][2]["tiers"]["pc"]["property_identity"])
            self.assertTrue(projected.ready, projected.missing_inputs)
            self.assertEqual(projected.stage, AFTER1020)
            self.assertEqual(len(projected.independent_stage_outputs["2921350"]), 1)
            self.assertEqual(len(projected.independent_stage_outputs["2921020"]), 4)
            self.assertEqual(projected.context.weighted_count, 5)
            self.assertEqual(skills.final_cache_points, (3, 7, 8, 6, 5, 17))
            stage = projected.source_ledger["ordered_stages"][0]
            self.assertFalse(stage["observed_leaf_ready"])
            self.assertTrue(stage["requests_ready"])
            provenance = stage["source_derived_normal_return_occurrences"]
            self.assertEqual(len(provenance), 2)
            for item in provenance:
                self.assertEqual(item["kind"], "modeled_2560620_normal_return")
                self.assertEqual(item["actual_default_guard_raw_i32"], guard)
                self.assertEqual(item["tier_pc_rva"], 0x5D65E80)
                self.assertEqual((item["key_count"], item["value_count"]), (0, 0))
                self.assertFalse(item["raw_pc_observed"])

        # The cold source joins A's group. Empty inner input cannot erase A.
        same_group = deepcopy(cold)
        for province in same_group["provinces"]:
            province["sources"][2]["group_index_raw_i32"] = 0
        _, mixed, mixed_skills = evaluate(same_group)
        self.assertTrue(mixed.ready, mixed.missing_inputs)
        group = mixed.independent_stage_outputs["2921350"][0].base_property_block
        self.assertEqual(group["keys_u16"], [0, 5, 65535])
        self.assertEqual(group["values_q64"], [-4 * Q, 8 * Q, -3 * Q])
        self.assertEqual(mixed_skills.final_cache_points, (3, 7, 8, 6, 5, 17))

        # A known zero-valued key survives the same cold-empty inner occurrence.
        zero_key = deepcopy(same_group)
        for province in zero_key["provinces"]:
            for source in province["sources"][:2]:
                source["tiers"]["pc"]["property_block"] = {
                    "keys_count": 1, "values_count": 1,
                    "keys_u16": [4], "values_q64": [0], "reason": None}
        _, zero, zero_skills = evaluate(zero_key)
        self.assertTrue(zero.ready, zero.missing_inputs)
        self.assertEqual(zero.independent_stage_outputs["2921350"][0].base_property_block["values_q64"], [0])
        self.assertEqual(zero.context.weighted_count, 5)
        self.assertEqual(zero_skills.final_cache_points, (7, 7, 8, 6, 5, 9))

        warm = deepcopy(cold)
        warm.update(status="available", ready=True, reason=None)
        for province in warm["provinces"]:
            province["reason"] = None
            source = province["sources"][2]
            source["reason"] = None
            source["tiers"].update(status="available", ready=True, reason=None,
                selection="initialized_default_5d65b00", default_guard_raw_i32=1,
                pc={"property_identity": "actual_warm_tier_pc", "reason": None,
                    "property_block": {"keys_count": 1, "values_count": 1,
                        "keys_u16": [4], "values_q64": [-2 * Q], "reason": None}})
        _, actual_warm, warm_skills = evaluate(warm)
        self.assertTrue(actual_warm.ready)
        self.assertEqual(actual_warm.context.weighted_count, 6)
        self.assertEqual(warm_skills.final_cache_points, (3, 7, 8, 6, 1, 17))
        self.assertEqual(actual_warm.source_ledger["ordered_stages"][0]["source_derived_normal_return_occurrences"], ())

        unknown = deepcopy(cold)
        reason = "following2921350_tier_default_guard_unavailable"
        unknown["reason"] = reason
        for province in unknown["provinces"]:
            province["reason"] = reason
            source = province["sources"][2]
            source["reason"] = reason
            source["tiers"].update(reason=reason, selection=None, default_guard_raw_i32=None,
                pc={"property_identity": None, "property_block": None, "reason": reason})
        _, unresolved, unresolved_skills = evaluate(unknown)
        self.assertFalse(unresolved.ready)
        self.assertEqual(unresolved.stage, INCOMING)
        self.assertEqual(unresolved_skills.final_cache_points, (6, 6, 8, 6, 6, 6))
        self.assertEqual(unresolved.source_ledger["ordered_stages"][0]["source_derived_normal_return_occurrences"], ())

        diagnostic = build_following2921020_nonowner_leaf()
        diagnostic.update(status="partial", ready=False, reason="rank_diagnostic_3f7ab90_result",
            rank_raw_i8=-1, tier_selection="diagnostic_3f7ab90_outcome_unobserved",
            selected_row_identity=None, composite_ready=False)
        for name in ("base_pc", "tier_pc"):
            diagnostic[name] = {"property_identity": None, "property_block": None,
                                "reason": "rank_diagnostic_3f7ab90_result"}
        _, later_gap, later_skills = evaluate(cold, diagnostic)
        self.assertFalse(later_gap.ready)
        self.assertEqual(later_gap.stage, AFTER1350)
        self.assertEqual(later_gap.context.weighted_count, 1)
        self.assertEqual(later_skills.final_cache_points, (2, 6, 8, 6, 6, 14))

        OBSERVATIONS.update({
            "normalizer": "normalize_battle_terminal_transition_v1",
            "raw_cold_leaf_and_PC_preserved": True,
            "guards_projected": [0, -1], "projected_frontier": projected.stage,
            "source_derived_postimages": 2, "projected_weighted_rows": 5,
            "projected_skills": list(skills.final_cache_points),
            "mixed_group_nonempty_preserved": True, "zero_key_occurrence_preserved": True,
            "warm_actual_skills": list(warm_skills.final_cache_points),
            "unknown_guard_frontier": unresolved.stage,
            "later_diagnostic_frontier": later_gap.stage,
            "initializer_execution_or_live_pair_inferred": False,
            "current_final_prior": False, "full_person_or_entry_ready": False,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
