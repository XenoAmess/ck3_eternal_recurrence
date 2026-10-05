"""One production-service case for all current helper point-store families."""
from copy import deepcopy
import unittest

from test_conditional_current_helper_domain_updates import domain_row
from test_conditional_monthly_loss_budgets import MemoryStrengthService, monthly_budget_packet
from xar_autoplayer.bridge.service import BridgeUnavailableError

RAW_A, RAW_B, ACTUAL_REGI = -1728053247, -2013265918, 67108866
MEMBERSHIP = [RAW_A, 9, RAW_A, RAW_B, 11]


def point_record(index, chunk, target, state=4, valid=True):
    result = {
        "stored_index": index, "record_regiment_reference_id": ACTUAL_REGI, "chunk_index": chunk,
        "record_regiment_resolved_id": ACTUAL_REGI, "record_regiment_used_fallback": False,
        "record_regiment_magic_14_raw": 0x52656769 if valid else 0,
        "data_record_present": True, "data_alias_ordinal": chunk, "data_byte_14_raw": 7,
        "data_state_18_raw": state, "data_owner_regiment_reference_id": target,
        "receiver_regiment_resolved_id": ACTUAL_REGI, "receiver_regiment_used_fallback": True,
        "receiver_title_reference_130_raw": -1, "receiver_character_reference_12c_raw": 29829,
        "owner_title_resolved_id": None, "owner_title_used_fallback": None,
        "owner_title_holder_character_id_128_raw": None,
        "selected_character_reference_id": 29829, "selected_character_resolved_id": 29829,
        "selected_character_used_fallback": False, "character_child_1c0_present": True,
        "membership_alias_ordinal": 0, "membership_count_2b4_raw": len(MEMBERSHIP),
        "ordered_persistent_regiment_ids_2a8": list(MEMBERSHIP),
    }
    if not valid:
        keep = {"stored_index", "record_regiment_reference_id", "chunk_index",
                "record_regiment_resolved_id", "record_regiment_used_fallback", "record_regiment_magic_14_raw"}
        for key in result.keys() - keep:
            result[key] = None
    return result


def character_row(index, c8, c0, present=True, fallback=False):
    return {
        "stored_index": index, "character_reference_id": 29829 + index,
        "character_resolved_id": -1 if fallback else 29829 + index,
        "character_used_fallback": fallback, "character_child_1b8_present": present,
        "character_child_1c8_present": c8, "character_child_1c0_present": c0,
        "child_1b8_alias_ordinal": 0 if present else None,
        "child_byte_108_raw": 7 if present else None,
        "child_character_reference_fc_raw": 42 if present else None,
    }


def point_packet():
    packet = monthly_budget_packet()
    groups = [
        {"group_index": 0, "record_count_14_raw": 4, "character_count_2c_raw": 5,
         "record_rows": [point_record(0, 0, RAW_A), point_record(1, 1, RAW_B),
                         point_record(2, 2, RAW_A, state=1), point_record(3, 3, RAW_A, valid=False)],
         "character_rows": [character_row(0, True, False), character_row(1, False, True),
                            character_row(2, False, False), character_row(3, False, False, fallback=True),
                            character_row(4, True, True, present=False)]},
        {"group_index": 1, "record_count_14_raw": 1, "character_count_2c_raw": 0,
         "record_rows": [point_record(0, 0, RAW_A)], "character_rows": []},
    ]
    packet["monthly_current_helper_point_store_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "entry_army_id": 0, "helper_resolved_army_id": 0, "helper_used_fallback": False,
        "helper_same_current_army_pointer": True, "group_count_5c_raw": 2, "groups": groups,
    }
    domain_rows = []
    for group in groups:
        for record in group["record_rows"]:
            domain = domain_row(record["stored_index"])
            for key in set(record) & set(domain):
                domain[key] = deepcopy(record[key])
            domain.update(group_index=group["group_index"], receiver_state_138_raw=0)
            if record["record_regiment_magic_14_raw"] == 0:
                keep = {"group_index", "stored_index", "record_regiment_reference_id", "chunk_index",
                        "record_regiment_resolved_id", "record_regiment_used_fallback", "record_regiment_magic_14_raw"}
                for key in domain.keys() - keep:
                    domain[key] = None
            domain_rows.append(domain)
    packet["monthly_current_helper_domain_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "entry_army_id": 0, "group_count_5c_raw": 2, "rows": domain_rows,
    }
    return packet


class ConditionalCurrentHelperPointStoresTests(unittest.TestCase):
    def test_service_projects_nonempty_point_effects_with_order_aliases_and_return_scope(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            response = service.query_army_strengths([0], expected_revision=2)
            allocation = response["loss_allocation_requests_v1"][0]
            projected = allocation["same_input_conditional_current_helper_point_stores_v1"]
            self.assertEqual(service.calls, 1)
            self.assertEqual(packet, original)
            self.assertFalse(projected["actual_effects_observed"])
            self.assertFalse(projected["actual_loss"])
            self.assertIsNone(projected["actual_post_state"])
            self.assertFalse(projected["real_late_caller_stage_ready"])
            self.assertFalse(projected["full_helper_ready"])
            self.assertFalse(projected["actual_full_army_lifecycle_ready"])
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            return projected

        packet = point_packet()
        projected = query(packet)
        self.assertTrue(projected["conditional_point_stores_ready"])
        self.assertTrue(projected["data_clears_ready"])
        self.assertTrue(projected["conditional_membership_erases_ready"])
        self.assertTrue(projected["membership_source_continuations_ready"])
        self.assertTrue(projected["group_child_stores_ready"])
        rows = projected["record_projections"]
        members = [row["membership_erase"] for row in rows]
        self.assertEqual(members[0]["raw_DATA8_target"], RAW_A)
        self.assertEqual(members[0]["receiver_regiment_resolved_id"], ACTUAL_REGI)
        self.assertEqual(members[0]["conditional_ordered_ids_after"], [9, RAW_B, 11])
        self.assertEqual(members[0]["conditional_removed_count"], 2)
        self.assertEqual(members[1]["conditional_ordered_ids_before"], [9, RAW_B, 11])
        self.assertEqual(members[1]["conditional_ordered_ids_after"], [9, 11])
        self.assertEqual(members[4]["conditional_ordered_ids_before"], [9, 11])
        self.assertEqual(members[4]["conditional_removed_count"], 0)
        self.assertEqual(projected["membership_value_projections"][0]["conditional_ordered_ids_after"], [9, 11])
        self.assertEqual(members[0]["ordinary_return_basis"], "source_closed_same_query_domain_record_ordinary_return")
        # receiver138==0 returns normally without a Domain store. Membership
        # still performs the nonzero raw-target erase after that return.
        self.assertTrue(members[0]["ordinary_return_ready"])
        self.assertTrue(members[0]["conditional_call_admitted"])
        self.assertFalse(members[2]["conditional_call_admitted"])
        self.assertFalse(members[3]["conditional_call_admitted"])
        self.assertEqual(rows[2]["data_clear"]["conditional_byte_14_after"], 0)
        self.assertTrue(rows[2]["data_clear"]["conditional_changed"])
        self.assertFalse(rows[3]["data_clear"]["conditional_store_admitted"])
        self.assertFalse(rows[4]["data_clear"]["conditional_changed"])
        chars = projected["character_projections"]
        self.assertTrue(chars[0]["conditional_byte_108_changed"])
        self.assertTrue(chars[0]["conditional_character_reference_fc_changed"])
        self.assertEqual(chars[1]["conditional_byte_108_before"], 0)
        self.assertEqual(chars[1]["conditional_character_reference_fc_before"], -1)
        self.assertFalse(chars[1]["conditional_byte_108_changed"])
        self.assertEqual(chars[3]["character_resolved_id"], -1)
        self.assertEqual(chars[3]["conditional_character_reference_fc_after"], -1)
        self.assertFalse(chars[4]["conditional_store_admitted"])
        order = [(row["group_index"], row["kind"]) for row in projected["ordered_effects"]]
        self.assertEqual(order[:8], [(0, kind) for _ in range(4) for kind in ("data_byte_14_clear", "membership_erase")])
        self.assertEqual(order[8:13], [(0, "group_child_constants")] * 5)
        self.assertEqual(order[13:], [(1, "data_byte_14_clear"), (1, "membership_erase")])

        # No old source loss family is required for this additive sibling.
        no_loss = deepcopy(packet)
        no_loss.pop("loss_application_inputs_v1")
        self.assertTrue(query(no_loss)["conditional_point_stores_ready"])

        partial = deepcopy(packet)
        partial["monthly_current_helper_point_store_inputs_v1"]["groups"][0]["record_rows"][0]["ordered_persistent_regiment_ids_2a8"] = None
        unknown = query(partial)
        self.assertTrue(unknown["data_clears_ready"])
        self.assertTrue(unknown["group_child_stores_ready"])
        self.assertTrue(unknown["membership_source_continuations_ready"])
        self.assertFalse(unknown["conditional_membership_erases_ready"])
        self.assertFalse(unknown["conditional_point_stores_ready"])
        self.assertIsNone(unknown["record_projections"][1]["membership_erase"]["conditional_ordered_ids_after"])

        unknown_alias = deepcopy(packet)
        unknown_alias["monthly_current_helper_point_store_inputs_v1"]["groups"][0]["record_rows"][0]["membership_alias_ordinal"] = None
        alias_partial = query(unknown_alias)
        self.assertIsNone(alias_partial["record_projections"][1]["membership_erase"]["conditional_ordered_ids_after"])
        self.assertFalse(alias_partial["conditional_point_stores_ready"])

        # A different physical helper receiver keeps its point operands and
        # leaf values, while the old current receiver cannot prove its returns.
        for same in (False, None):
            different = deepcopy(packet)
            different["monthly_current_helper_point_store_inputs_v1"]["helper_same_current_army_pointer"] = same
            limited = query(different)
            self.assertTrue(limited["data_clears_ready"])
            self.assertTrue(limited["conditional_membership_erases_ready"])
            self.assertTrue(limited["group_child_stores_ready"])
            self.assertFalse(limited["membership_source_continuations_ready"])
            self.assertFalse(limited["conditional_point_stores_ready"])
            self.assertEqual(limited["membership_value_projections"][0]["conditional_ordered_ids_after"], [9, 11])
        missing_domain = deepcopy(packet)
        missing_domain.pop("monthly_current_helper_domain_inputs_v1")
        limited = query(missing_domain)
        self.assertTrue(limited["data_clears_ready"])
        self.assertTrue(limited["conditional_membership_erases_ready"])
        self.assertFalse(limited["membership_source_continuations_ready"])

        negative_characters = deepcopy(packet)
        group = negative_characters["monthly_current_helper_point_store_inputs_v1"]["groups"][0]
        group.update(character_count_2c_raw=-1, character_rows=None)
        negative = query(negative_characters)
        self.assertTrue(negative["data_clears_ready"])
        self.assertFalse(negative["group_child_stores_ready"])
        self.assertFalse(negative["conditional_point_stores_ready"])
        self.assertEqual(negative["character_projections"], [])

        nonstate4 = deepcopy(packet)
        block = nonstate4["monthly_current_helper_point_store_inputs_v1"]
        block.update(group_count_5c_raw=1, groups=[block["groups"][0]])
        group = block["groups"][0]
        group.update(record_count_14_raw=1, record_rows=[point_record(0, 0, RAW_A, state=1)],
                     character_count_2c_raw=0, character_rows=[])
        nonstate4.pop("monthly_current_helper_domain_inputs_v1")
        self.assertTrue(query(nonstate4)["conditional_point_stores_ready"])

        empty_membership = deepcopy(packet)
        for group in empty_membership["monthly_current_helper_point_store_inputs_v1"]["groups"]:
            for row in group["record_rows"]:
                row.update(membership_count_2b4_raw=0, ordered_persistent_regiment_ids_2a8=[])
        empty = query(empty_membership)
        self.assertTrue(empty["conditional_point_stores_ready"])
        self.assertEqual(empty["membership_value_projections"][0]["conditional_ordered_ids_after"], [])

        no_groups = deepcopy(packet)
        no_groups["monthly_current_helper_point_store_inputs_v1"].update(group_count_5c_raw=0, groups=[])
        no_groups.pop("monthly_current_helper_domain_inputs_v1")
        self.assertTrue(query(no_groups)["conditional_point_stores_ready"])
        no_records = deepcopy(packet)
        block = no_records["monthly_current_helper_point_store_inputs_v1"]
        block.update(group_count_5c_raw=1, groups=[block["groups"][0]])
        block["groups"][0].update(record_count_14_raw=-1, record_rows=[])
        no_records.pop("monthly_current_helper_domain_inputs_v1")
        negative_record = query(no_records)
        self.assertTrue(negative_record["conditional_point_stores_ready"])
        self.assertEqual(negative_record["record_projections"], [])
        self.assertEqual(len(negative_record["character_projections"]), 5)
        self.assertFalse(query(monthly_budget_packet())["conditional_point_stores_ready"])

        for mutation in ("byte_width", "negative_character_empty"):
            malformed = deepcopy(packet)
            group = malformed["monthly_current_helper_point_store_inputs_v1"]["groups"][0]
            if mutation == "byte_width":
                group["record_rows"][0]["data_byte_14_raw"] = True
            else:
                group.update(character_count_2c_raw=-1, character_rows=[])
            service = MemoryStrengthService(malformed)
            with self.assertRaises(BridgeUnavailableError):
                service.query_army_strengths([0], expected_revision=2)
            self.assertEqual(service.calls, 1)


if __name__ == "__main__":
    unittest.main()
