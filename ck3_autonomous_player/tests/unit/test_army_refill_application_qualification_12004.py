"""Evidence-level counterexamples: callback net does not identify an ADD."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.army_refill_application_qualification_12004 import (
    qualify_regular_refill_application_12004,
)
from xar_autoplayer.replenishment_numeric import same_input_chunk_q
from xar_autoplayer.bridge.army_scoped_ordered_refill_projection import (
    project_observed_prepared_ordered_physical_core_v1,
)


def consumed(before=80, after=90, *, maximum_before=100, maximum_after=100):
    chunks = []
    for i in range(7):
        left, right = (before, after) if i == 0 else (0, 0)
        lm, rm = (maximum_before, maximum_after) if i == 0 else (0, 0)
        chunks.append({"physical_index": i,
            "before_raw": {"current_soldiers": left, "maximum_soldiers": lm},
            "returned_raw": {"current_soldiers": right, "maximum_soldiers": rm},
            "delta_current_soldiers": right-left, "delta_maximum_soldiers": rm-lm})
    return {"owned_original_return_observed": True,
        "conditional_entry_projection": {"conditional_regular_core_current_maximum_ready": True},
        "subject_raw_physical_delta_v1": {
            "basis": "owned_same_core_entry_and_return_raw_physical_seven",
            "status": "available", "actual_ADD_observed": False,
            "causal_attribution_ready": False, "conditional_entry_projection_used": False,
            "physical_objects": [{"physical_token": 0x1000, "chunks": chunks}]}}


def qualify(value, **kwargs):
    return qualify_regular_refill_application_12004(value, exact_source=True,
        observer_installed=True, **kwargs)


def physical_input(*, fraction=10000, repeats=1):
    chunks = []
    for i in range(7):
        chunks.append({'physical_index': i, 'q_ordinal_raw': i,
            'current_soldiers': 80 if i == 0 else 0,
            'maximum_soldiers': 100 if i == 0 else 0, 'state_raw': 0,
            'origin_province_788_raw': -1, 'origin_province_73c_raw': -1,
            'associated_arrg_magic_raw': 0, 'associated_arrg_resolved_full_id': -1,
            'army_regiment_id_raw': 7, 'exclusion_byte_14_raw': 0,
            'owner_guard_138_raw': 0, 'owner_definition_magic_38_raw': 0})
    return {'native_persistent_occurrence_count': repeats,
        'persistent_occurrences': [{'stored_index': i, 'persistent_regiment_id': 1}
                                   for i in range(repeats)],
        'persistent_regiments': [{'persistent_regiment_id': 1,
            'prepared_fraction_raw': fraction, 'chunks': chunks}]}


class RefillEvidenceTests(unittest.TestCase):
    def test_positive_net_keeps_actual_amount_unknown(self):
        value = consumed()
        original = deepcopy(value)
        result = qualify(value)
        self.assertTrue(result["subject_physical_net_ready"])
        self.assertEqual(result["raw_current_net"], 10)
        self.assertFalse(result["actual_ADD_observed"])
        self.assertIsNone(result["applied_positive_refill_soldiers"])
        self.assertFalse(result["toggle_effect_proven"])
        self.assertFalse(result["conditional_projection_promoted"])
        self.assertEqual(value, original)

    def test_add_then_clear_can_have_negative_net(self):
        # Source permits 90 + 10, followed by a separate max/current pair clear.
        result = qualify(consumed(90, 0, maximum_after=0))
        self.assertEqual(result["raw_current_net"], -90)
        self.assertEqual(result["raw_maximum_net"], -100)
        self.assertIsNone(result["applied_positive_refill_soldiers"])
        self.assertFalse(result["no_ADD_proven"])

    def test_zero_net_does_not_prove_no_add(self):
        result = qualify(consumed(0, 0))
        self.assertEqual(result["raw_current_net"], 0)
        self.assertFalse(result["no_ADD_proven"])

    def test_signed_endpoint_difference_is_not_wrapped_or_clamped(self):
        result = qualify(consumed((1 << 31)-1, -(1 << 31)))
        self.assertEqual(result["raw_current_net"], -(1 << 32)+1)
        self.assertFalse(result["actual_ADD_observed"])

    def test_duplicate_alias_cannot_double_count_physical_net(self):
        value = consumed()
        objects = value["subject_raw_physical_delta_v1"]["physical_objects"]
        objects.append(deepcopy(objects[0]))
        result = qualify(value)
        self.assertFalse(result["subject_physical_net_ready"])
        self.assertIsNone(result["raw_current_net"])

    def test_partial_cannot_be_completed_by_conditional_projection(self):
        value = consumed()
        value["subject_raw_physical_delta_v1"]["status"] = "unavailable"
        self.assertFalse(qualify(value)["subject_physical_net_ready"])

    def test_historical_raw_fact_does_not_invent_runtime_binding(self):
        result = qualify(consumed())
        self.assertTrue(result["subject_physical_net_ready"])
        self.assertFalse(result["current_runtime_binding_proven"])

    def test_claimed_add_flag_cannot_smuggle_a_future_producer(self):
        value = consumed()
        value["subject_raw_physical_delta_v1"]["actual_ADD_observed"] = True
        self.assertFalse(qualify(value)["subject_physical_net_ready"])

    def test_forged_endpoint_delta_is_refused(self):
        value = consumed()
        value["subject_raw_physical_delta_v1"]["physical_objects"][0]["chunks"][0]["delta_current_soldiers"] = 99
        self.assertFalse(qualify(value)["subject_physical_net_ready"])

    def test_seven_slots_are_required(self):
        value = consumed()
        value["subject_raw_physical_delta_v1"]["physical_objects"][0]["chunks"].pop()
        self.assertFalse(qualify(value)["subject_physical_net_ready"])

    def test_q_zero_still_qualifies_without_observing_add(self):
        numeric = same_input_chunk_q(10, 9, 1, True)
        self.assertTrue(numeric["native_core_chunk_qualifies"])
        self.assertEqual(numeric["same_input_q"], 0)

    def test_q_cap_uses_chunk_maximum_and_signed_overflow(self):
        self.assertEqual(same_input_chunk_q(100, 99, 10000, True)["same_input_q"], 1)
        self.assertEqual(same_input_chunk_q(100, 80, 10000, True)["same_input_q"], 10)
        # Positive rate does not license clamping a wrapped negative request.
        numeric = same_input_chunk_q(100, 0, ((1 << 64)-100000)//100, True)
        self.assertTrue(numeric["native_core_chunk_qualifies"])
        self.assertEqual(numeric["same_input_q"], -1)

    def test_prepared_nonpositive_skips_q(self):
        numeric = same_input_chunk_q(100, 10, 0, True)
        self.assertFalse(numeric["native_core_chunk_qualifies"])

    def test_duplicate_manager_occurrences_are_repeated_execution(self):
        result = project_observed_prepared_ordered_physical_core_v1(physical_input(repeats=2))
        self.assertTrue(result['ordered_core_ready'])
        self.assertEqual([row['writes'][0]['after_current'] for row in result['occurrences']], [90, 100])

    def test_final_shared_q_slot_can_exceed_another_chunks_cap(self):
        value = physical_input()
        chunks = value['persistent_regiments'][0]['chunks']
        chunks[0]['current_soldiers'] = 90
        chunks[1].update(current_soldiers=900, maximum_soldiers=1000, q_ordinal_raw=0)
        result = project_observed_prepared_ordered_physical_core_v1(value)
        self.assertEqual(result['occurrences'][0]['q_buffer'][0], 100)
        self.assertEqual(result['physical_chunks'][0]['current_soldiers'], 190)

    def test_qualified_zero_q_still_dispatches_other_slots_pair_clear(self):
        value = physical_input(fraction=1)
        chunks = value['persistent_regiments'][0]['chunks']
        chunks[1].update(current_soldiers=10, maximum_soldiers=10, army_regiment_id_raw=-1)
        result = project_observed_prepared_ordered_physical_core_v1(value)
        self.assertTrue(result['occurrences'][0]['native_core_admitted'])
        self.assertEqual(result['occurrences'][0]['q_buffer'], [0]*7)
        self.assertTrue(result['occurrences'][0]['writes'][1]['pair_cleared'])


if __name__ == "__main__":
    unittest.main()
