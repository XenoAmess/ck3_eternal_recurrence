"""One production-service case for the source-closed Domain subsystem."""
from copy import deepcopy
import unittest

from test_conditional_monthly_loss_budgets import MemoryStrengthService, monthly_budget_packet
from xar_autoplayer.bridge.service import BridgeUnavailableError


def domain_row(index=0, alias=0, count_base=10, old_value=200000):
    return {
        "group_index": 0, "stored_index": index,
        "record_regiment_reference_id": 700, "chunk_index": -2,
        "record_regiment_resolved_id": 700, "record_regiment_used_fallback": True,
        "record_regiment_magic_14_raw": 0x52656769, "data_record_present": True,
        "data_state_18_raw": 4, "data_owner_regiment_reference_id": 900,
        "receiver_regiment_resolved_id": 900, "receiver_regiment_used_fallback": False,
        "receiver_state_138_raw": 4,
        "receiver_title_reference_130_raw": 771, "receiver_character_reference_12c_raw": -1,
        # Actual Title fallback ID-1 is not a no-call gate. Its +128 holder
        # still supplies the Character reference; no Army+128 is consulted.
        "owner_title_resolved_id": -1, "owner_title_used_fallback": True,
        "owner_title_holder_character_id_128_raw": 29829,
        "selected_character_reference_id": 29829, "selected_character_resolved_id": 29829,
        "selected_character_used_fallback": False,
        "character_domain_child_present": True, "domain_reference_id": 300,
        "domain_resolved_id": 300, "domain_used_fallback": False,
        "domain_magic_0c_raw": 0x446F6D69, "domain_data_30_present": True,
        "domain_flag_17e_raw": 1, "count_base_128_raw": count_base,
        "count_records": [
            {"stored_index": 0, "count_00_raw": 5, "count_04_raw": 0, "state_18_raw": 3},
            {"stored_index": 1, "count_00_raw": 3, "count_04_raw": 1, "state_18_raw": 4},
            *[{"stored_index": i, "count_00_raw": 0, "count_04_raw": 0, "state_18_raw": 0}
              for i in range(2, 7)],
        ],
        "domain_owner_character_reference_id": 29829,
        "domain_owner_character_resolved_id": 29829, "domain_owner_character_used_fallback": False,
        "domain_owner_character_magic_1c_raw": 0x43686172,
        "domain_value_48_raw64": old_value, "domain_alias_ordinal": alias,
    }


def zero_records():
    return [{"stored_index": i, "count_00_raw": 0, "count_04_raw": 0, "state_18_raw": 0}
            for i in range(7)]


def domain_packet(rows, group_count=1):
    packet = monthly_budget_packet()
    packet["monthly_current_helper_domain_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "entry_army_id": 0, "group_count_5c_raw": group_count, "rows": rows,
    }
    return packet


class ConditionalCurrentHelperDomainUpdatesTests(unittest.TestCase):
    def test_service_projects_ordered_nonzero_domain_values_from_actual_raw_operands(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            response = service.query_army_strengths([0], expected_revision=2)
            allocation = response["loss_allocation_requests_v1"][0]
            projection = allocation["same_input_conditional_current_helper_domain_updates_v1"]
            self.assertEqual(service.calls, 1)
            self.assertEqual(packet, original)
            self.assertFalse(projection["actual_effects_observed"])
            self.assertIsNone(projection["actual_domain_value_48_after_raw64"])
            self.assertFalse(projection["real_late_caller_stage_ready"])
            self.assertFalse(projection["full_helper_ready"])
            self.assertFalse(projection["actual_full_army_lifecycle_ready"])
            self.assertFalse(projection["actual_loss"])
            self.assertIsNone(projection["actual_post_state"])
            self.assertFalse(projection["full_monthly_applied_loss_ready"])
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            for record in projection["record_projections"]:
                self.assertFalse(record["actual_effects_observed"])
                self.assertIsNone(record["actual_domain_value_48_after_raw64"])
            return response, projection

        packet = domain_packet([domain_row(0), domain_row(1)])
        response, projected = query(packet)
        self.assertTrue(projected["conditional_domain_updates_ready"])
        self.assertEqual(projected["conditional_domain_store_count"], 2)
        self.assertEqual(projected["native_subsystem_rva"], "0x2C57020")
        self.assertEqual(projected["input_basis"],
                         "isolated_ordered_2C57020_invocations_from_explicit_current_helper_entry")
        rows = projected["record_projections"]
        self.assertEqual([row["conditional_native_count"] for row in rows], [8, 8])
        self.assertEqual(rows[0]["conditional_count_record_deltas"], [0, -2, 0, 0, 0, 0, 0])
        self.assertEqual(rows[0]["owner_character_route"], "title_holder")
        self.assertEqual(rows[0]["derived_selected_character_reference_id"], 29829)
        self.assertEqual(rows[0]["receiver_regiment_resolved_id"], 900)
        self.assertEqual(rows[0]["chunk_index"], -2)
        self.assertEqual([row["conditional_domain_value_48_after_raw64"] for row in rows], [1000000, 1800000])
        self.assertEqual(rows[1]["conditional_domain_value_48_before_raw64"], 1000000)
        self.assertEqual(rows[1]["domain_value_input_basis"], "prior_conditional_domain_alias_value")
        self.assertEqual(projected["domain_value_projections"][0]["conditional_domain_value_48_after_raw64"], 1800000)
        self.assertTrue(response["army_strengths"][0]["monthly_current_helper_domain_inputs_v1"]["ready"])

        # The additive allocation sibling remains available when the existing
        # soldier-loss operand family is absent; it does not apply a casualty.
        no_loss = deepcopy(packet)
        no_loss.pop("loss_application_inputs_v1")
        _, independent = query(no_loss)
        self.assertTrue(independent["conditional_domain_updates_ready"])

        negative = domain_row(count_base=-2, old_value=100000)
        negative["count_records"] = zero_records()
        _, minus = query(domain_packet([negative]))
        self.assertEqual(minus["record_projections"][0]["conditional_delta_raw64"], -200000)
        self.assertEqual(minus["record_projections"][0]["conditional_domain_value_48_after_raw64"], 0)

        wrapping = domain_row(count_base=2147483647, old_value=1)
        wrapping["count_records"] = zero_records()
        wrapping["count_records"][0].update(count_00_raw=1, count_04_raw=4)
        _, wrapped = query(domain_packet([wrapping]))
        self.assertEqual(wrapped["record_projections"][0]["conditional_native_count"], -2147483646)
        self.assertEqual(wrapped["record_projections"][0]["conditional_domain_value_48_after_raw64"], 0)

        subtraction = domain_row(count_base=2, old_value=0)
        subtraction["count_records"] = zero_records()
        subtraction["count_records"][0].update(count_00_raw=-2147483648, count_04_raw=2147483647,
                                                  state_18_raw=None)
        _, sub = query(domain_packet([subtraction]))
        sub_row = sub["record_projections"][0]
        self.assertEqual(sub_row["conditional_count_record_deltas"][0], -1)
        self.assertEqual(sub_row["conditional_native_count"], 1)
        self.assertFalse(sub_row["count_source_witness_ready"])
        self.assertTrue(sub["conditional_domain_updates_ready"])

        add64 = domain_row(count_base=1, old_value=(1 << 63) - 1)
        add64["count_records"] = zero_records()
        _, overflow = query(domain_packet([add64]))
        self.assertEqual(overflow["record_projections"][0]["conditional_domain_value_48_after_raw64"], 0)

        fallback = domain_row(count_base=2, old_value=0)
        fallback["count_records"] = zero_records()
        fallback.update(receiver_title_reference_130_raw=-1, receiver_character_reference_12c_raw=8,
                        owner_title_resolved_id=None, owner_title_used_fallback=None,
                        owner_title_holder_character_id_128_raw=None,
                        selected_character_reference_id=8, selected_character_resolved_id=29829,
                        selected_character_used_fallback=True, character_domain_child_present=False,
                        domain_reference_id=-1, domain_used_fallback=True, domain_flag_17e_raw=255,
                        domain_owner_character_used_fallback=True)
        _, fall = query(domain_packet([fallback]))
        self.assertEqual(fall["record_projections"][0]["owner_character_route"], "direct_character")
        self.assertTrue(fall["record_projections"][0]["predicate_admitted"])
        self.assertEqual(fall["record_projections"][0]["conditional_domain_value_48_after_raw64"], 200000)

        # Both references present select -1, then the actual Character fallback.
        both = deepcopy(fallback)
        both.update(receiver_title_reference_130_raw=771, selected_character_reference_id=-1)
        _, both_route = query(domain_packet([both]))
        self.assertEqual(both_route["record_projections"][0]["owner_character_route"], "minus_one_character_fallback")

        zero = domain_row(count_base=0, old_value=None)
        zero["count_records"] = zero_records()
        zero["count_records"][0].update(count_00_raw=5, count_04_raw=0, state_18_raw=3)
        zero.update(domain_owner_character_reference_id=None, domain_owner_character_resolved_id=None,
                    domain_owner_character_used_fallback=None, domain_owner_character_magic_1c_raw=None)
        _, zero_count = query(domain_packet([zero]))
        self.assertEqual(zero_count["record_projections"][0]["conditional_branch"], "zero_native_count")
        self.assertTrue(zero_count["conditional_domain_updates_ready"])
        self.assertEqual(zero_count["conditional_domain_store_count"], 0)

        logical_count = domain_row(count_base=2, old_value=0)
        logical_count["count_records"] = zero_records()
        for count_record in logical_count["count_records"]:
            count_record.update(count_04_raw=None, state_18_raw=None)
        _, known_zero_contributions = query(domain_packet([logical_count]))
        self.assertEqual(known_zero_contributions["record_projections"][0]["conditional_native_count"], 2)
        self.assertTrue(known_zero_contributions["conditional_domain_updates_ready"])

        skipped = [domain_row(i) for i in range(5)]
        skipped[0].update(record_regiment_resolved_id=-1, count_records=None)
        skipped[1].update(data_record_present=False, record_regiment_resolved_id=None,
                          record_regiment_magic_14_raw=None, count_records=None)
        skipped[2].update(data_state_18_raw=3, count_records=None)
        skipped[3].update(receiver_state_138_raw=0, count_records=None)
        skipped[4].update(domain_flag_17e_raw=0, count_records=None)
        _, no_stores = query(domain_packet(skipped))
        self.assertTrue(no_stores["conditional_domain_updates_ready"])
        self.assertEqual([row["conditional_branch"] for row in no_stores["record_projections"]],
                         ["invalid_containing_regiment", "null_data_record", "data_not_state4",
                          "receiver_not_state4", "zero_predicate_flag"])

        invalid_owner = domain_row(old_value=None)
        invalid_owner.update(domain_owner_character_magic_1c_raw=0)
        _, owner_skip = query(domain_packet([invalid_owner]))
        self.assertEqual(owner_skip["record_projections"][0]["conditional_branch"], "invalid_domain_owner_character")
        self.assertTrue(owner_skip["conditional_domain_updates_ready"])

        # Captured traversal readiness does not promise every effect operand.
        # A missing known-alias count poisons that alias, not a distinct Domain.
        partial_rows = [domain_row(0), domain_row(1), domain_row(2, alias=1, old_value=300000)]
        partial_rows[0]["count_records"] = None
        _, partial = query(domain_packet(partial_rows))
        self.assertFalse(partial["conditional_domain_updates_ready"])
        self.assertIsNone(partial["record_projections"][1]["conditional_domain_value_48_after_raw64"])
        self.assertEqual(partial["record_projections"][2]["conditional_domain_value_48_after_raw64"], 1100000)
        self.assertFalse(partial["domain_value_projections"][0]["conditional_ready"])

        null_domain_data = domain_row()
        null_domain_data["domain_data_30_present"] = False
        _, unchecked = query(domain_packet([null_domain_data]))
        self.assertFalse(unchecked["conditional_domain_updates_ready"])
        self.assertIsNone(unchecked["record_projections"][0]["predicate_admitted"])
        self.assertIsNone(unchecked["record_projections"][0]["conditional_domain_store_admitted"])

        unresolved = [domain_row(0), domain_row(1, alias=1)]
        unresolved[0].update(domain_resolved_id=None, domain_magic_0c_raw=None, domain_alias_ordinal=None)
        _, unknown_target = query(domain_packet(unresolved))
        self.assertEqual(unknown_target["record_projections"][1]["domain_value_input_basis"], "unresolved_earlier_domain_target")
        self.assertIsNone(unknown_target["record_projections"][1]["conditional_domain_value_48_after_raw64"])

        wrong_holder = domain_row()
        wrong_holder["selected_character_reference_id"] = 999
        _, route_mismatch = query(domain_packet([wrong_holder]))
        self.assertFalse(route_mismatch["conditional_domain_updates_ready"])

        for group_count in (0, -1):
            no_groups = domain_packet([], group_count)
            no_groups["monthly_current_helper_domain_inputs_v1"].update(
                status="unavailable", ready=False, unavailable_reason="row_operands_not_needed", rows=None)
            _, empty = query(no_groups)
            self.assertTrue(empty["conditional_domain_updates_ready"])
            self.assertEqual(empty["conditional_domain_store_count"], 0)
            self.assertEqual(empty["record_projections"], [])
        _, positive_empty = query(domain_packet([]))
        self.assertTrue(positive_empty["conditional_domain_updates_ready"])
        _, absent = query(monthly_budget_packet())
        self.assertFalse(absent["conditional_domain_updates_ready"])

        missing = domain_packet([])
        missing["monthly_current_helper_domain_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="ordered_records_unavailable", rows=None)
        _, missing_rows = query(missing)
        self.assertFalse(missing_rows["conditional_invocation_order_ready"])

        # Malformed actual-source widths and seven-record shape are rejected
        # by the production authority, rather than coerced by the model.
        for key, value in (("domain_flag_17e_raw", True), ("count_records", zero_records()[:6])):
            bad = domain_packet([domain_row()])
            bad["monthly_current_helper_domain_inputs_v1"]["rows"][0][key] = value
            service = MemoryStrengthService(bad)
            with self.assertRaises(BridgeUnavailableError):
                service.query_army_strengths([0], expected_revision=2)
            self.assertEqual(service.calls, 1)


if __name__ == "__main__":
    unittest.main()
