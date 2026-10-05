"""One service case for the exact first pre-mutation manager cleanup stage."""
from copy import deepcopy
import unittest

from test_conditional_daily_queue_transfer import daily_queue_packet
from test_conditional_monthly_loss_budgets import MemoryStrengthService, monthly_budget_packet


def manager_cleanup_packet(argument=77):
    packet = daily_queue_packet(
        [19, 991, 991, 8],
        [(-1, True, 0x41726D79), (argument, True, 0x41726D79),
         (argument, True, 0x41726D79), (8, False, 0x41726D79)],
    )
    lists = (
        ("50", [argument, 991, argument, 8]),
        ("68", [19, 991, 991, 8]),
        ("80", [argument, 5, argument, 9]),
        ("98", [5, 6]), ("c8", [argument]), ("158", [argument, argument]),
    )
    packet["monthly_first_removal_cleanup_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "candidate_found": True, "candidate_stored_index": 1,
        "argument_army_id": argument, "cleanup_resolved_army_id": argument,
        # Queued991 selected a valid fallback. Resolving that object's actual
        # ID again can select a regular same-ID object with different pointers.
        "cleanup_used_fallback": False, "selected_bucket_index": (argument & 0xFFFFFFFF) % 30,
        "id_lists": [{"manager_offset": offset, "ordered_army_ids": ids} for offset, ids in lists],
        "selected_bucket_rows": [
            {"stored_index": 0, "observed_army_id": argument, "native_same_cleanup_army_pointer": False},
            {"stored_index": 1, "observed_army_id": argument, "native_same_cleanup_army_pointer": True},
            {"stored_index": 2, "observed_army_id": 8, "native_same_cleanup_army_pointer": False},
            {"stored_index": 3, "observed_army_id": argument, "native_same_cleanup_army_pointer": True},
            {"stored_index": 4, "observed_army_id": None, "native_same_cleanup_army_pointer": False},
        ],
        "records_b0": [
            [argument & 0xFFFFFFFF, 0x12345678, 0xFFFFFFFF, 1],
            [5, 2, 3, 4], [argument & 0xFFFFFFFF, 99, 88, 77],
            [6, 0x80000000, 9, 10], [argument & 0xFFFFFFFF, 55, 66, 77],
        ],
    }
    return packet


class ConditionalManagerCleanupTests(unittest.TestCase):
    def test_query_projects_first_manager_stage_with_exact_native_membership_rules(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            allocation = service.query_army_strengths([0], expected_revision=2)["loss_allocation_requests_v1"][0]
            cleanup = allocation["same_input_conditional_first_removal_manager_cleanup_v1"]
            self.assertEqual(packet, original)
            self.assertEqual(service.calls, 1)
            self.assertFalse(cleanup["actual_cleanup"])
            self.assertFalse(cleanup["actual_removal"])
            self.assertIsNone(cleanup["actual_post_state"])
            self.assertFalse(cleanup["full_army_lifecycle_ready"])
            self.assertFalse(cleanup["full_monthly_lifecycle_ready"])
            self.assertFalse(cleanup["full_ordered_removal_requests_ready"])
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            return allocation, cleanup

        allocation, cleanup = query(manager_cleanup_packet())
        self.assertTrue(cleanup["conditional_manager_cleanup_ready"])
        self.assertEqual(cleanup["conditional_cleanup_branch"], "cleanup")
        self.assertEqual((cleanup["candidate_stored_index"], cleanup["argument_army_id"]), (1, 77))
        first = allocation["same_input_conditional_daily_id_transfer_v1"]["first_removal_call_request"]
        self.assertEqual(first["raw_army_reference_id"], 991)
        self.assertTrue(first["used_fallback"])
        self.assertFalse(cleanup["cleanup_used_fallback"])
        self.assertTrue(cleanup["observed_queue_matches_transfer"])
        self.assertTrue(cleanup["conditional_passed_army_identity_ready"])
        self.assertTrue(cleanup["conditional_passed_army_identity_after_top_stage"]["native_army_identity_valid"])
        lists = {row["manager_offset"]: row for row in cleanup["id_list_projections"]}
        self.assertEqual(lists["50"]["conditional_ordered_army_ids_after"], [991, 77, 8])
        self.assertEqual(lists["80"]["conditional_ordered_army_ids_after"], [9, 5, 77])
        self.assertEqual(lists["98"]["conditional_ordered_army_ids_after"], [5, 6])
        self.assertEqual(lists["c8"]["conditional_ordered_army_ids_after"], [])
        self.assertEqual(lists["158"]["conditional_ordered_army_ids_after"], [77])
        self.assertEqual(lists["50"]["removed_count"], 1)
        self.assertEqual(lists["68"]["observed_ordered_army_ids"], [19, 991, 991, 8])
        self.assertEqual(lists["68"]["conditional_stage_entry_ordered_army_ids"], [])
        self.assertEqual(lists["68"]["conditional_ordered_army_ids_after"], [])
        self.assertEqual(lists["68"]["stage_input_basis"], "derived_post_transfer_source_queue")
        self.assertEqual(cleanup["selected_bucket_index"], 17)
        self.assertEqual(cleanup["selected_bucket_removed_stored_indices"], [1, 3])
        # Same-ID ordinal0 survives because the source compares physical
        # pointers. The nullptr ordinal4 legally preserves observed IDnull.
        self.assertEqual([row["stored_index"] for row in cleanup["conditional_selected_bucket_rows_after"]], [0, 2, 4])
        self.assertIsNone(cleanup["conditional_selected_bucket_rows_after"][-1]["observed_army_id"])
        self.assertEqual(cleanup["conditional_records_b0_after"], [[6, 0x80000000, 9, 10], [5, 2, 3, 4]])
        self.assertEqual(cleanup["records_b0_removed_count"], 3)
        self.assertTrue(allocation["same_input_conditional_daily_id_transfer_v1"]["post_removal_stage_required"])

        _, negative = query(manager_cleanup_packet(-2147483647))
        self.assertEqual(negative["selected_bucket_index"], 9)
        self.assertEqual(negative["records_b0_removed_count"], 3)
        self.assertEqual(negative["conditional_records_b0_after"], [[6, 0x80000000, 9, 10], [5, 2, 3, 4]])

        partial = manager_cleanup_packet()
        block = partial["monthly_first_removal_cleanup_inputs_v1"]
        block.update(status="unavailable", ready=False, unavailable_reason="list80_and_second_resolution_unavailable",
                     cleanup_resolved_army_id=None, cleanup_used_fallback=None,
                     selected_bucket_index=None, selected_bucket_rows=None)
        block["id_lists"][2]["ordered_army_ids"] = None
        _, independently_known = query(partial)
        self.assertFalse(independently_known["conditional_manager_cleanup_ready"])
        self.assertFalse(independently_known["selected_bucket_cleanup_ready"])
        self.assertTrue(independently_known["records_b0_cleanup_ready"])
        partial_lists = {row["manager_offset"]: row for row in independently_known["id_list_projections"]}
        self.assertTrue(partial_lists["50"]["conditional_ready"])
        self.assertFalse(partial_lists["80"]["conditional_ready"])
        self.assertIsNone(partial_lists["80"]["conditional_ordered_army_ids_after"])

        no_observed_queue = manager_cleanup_packet()
        no_observed_queue["monthly_first_removal_cleanup_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="cleanup_queue_observation_unavailable")
        no_observed_queue["monthly_first_removal_cleanup_inputs_v1"]["id_lists"][1]["ordered_army_ids"] = None
        _, derived_queue = query(no_observed_queue)
        self.assertTrue(derived_queue["conditional_manager_cleanup_ready"])
        self.assertIsNone(derived_queue["observed_queue_matches_transfer"])
        queue_row = derived_queue["id_list_projections"][1]
        self.assertIsNone(queue_row["observed_ordered_army_ids"])
        self.assertEqual(queue_row["conditional_stage_entry_ordered_army_ids"], [])

        mismatch = manager_cleanup_packet()
        mismatch["monthly_first_removal_cleanup_inputs_v1"]["id_lists"][1]["ordered_army_ids"] = [8]
        _, wrong_queue = query(mismatch)
        self.assertFalse(wrong_queue["observed_queue_matches_transfer"])
        self.assertFalse(wrong_queue["candidate_selection_ready"])
        self.assertEqual(wrong_queue["id_list_projections"], [])

        wrong_candidate = manager_cleanup_packet()
        wrong_candidate["monthly_first_removal_cleanup_inputs_v1"]["argument_army_id"] = 991
        _, no_wrong_argument = query(wrong_candidate)
        self.assertFalse(no_wrong_argument["candidate_selection_ready"])
        self.assertEqual(no_wrong_argument["id_list_projections"], [])

        for packet in (daily_queue_packet([], []), daily_queue_packet([19], [(-1, True, 0x41726D79)])):
            _, no_call = query(packet)
            self.assertEqual(no_call["conditional_cleanup_branch"], "not_called")
            self.assertTrue(no_call["conditional_manager_cleanup_ready"])
            self.assertEqual(no_call["id_list_projections"], [])

        unknown = manager_cleanup_packet()
        unknown["monthly_daily_queue_inputs_v1"]["initial_army_resolution_rows"][0].update(
            status="unavailable", unavailable_reason="prefix_resolution_unavailable",
            resolved_army_id=None, used_fallback=None,
            army_magic_14_raw=None, native_army_identity_valid=None)
        unknown["monthly_daily_queue_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="prefix_resolution_unavailable")
        unknown["monthly_first_removal_cleanup_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="prefix_resolution_unavailable",
            candidate_found=None, candidate_stored_index=None, argument_army_id=None,
            cleanup_resolved_army_id=None, cleanup_used_fallback=None,
            selected_bucket_index=None, selected_bucket_rows=None)
        _, stopped = query(unknown)
        self.assertFalse(stopped["candidate_selection_ready"])
        self.assertIsNone(stopped["conditional_cleanup_branch"])
        self.assertEqual(stopped["id_list_projections"], [])

        _, absent = query(monthly_budget_packet())
        self.assertFalse(absent["conditional_manager_cleanup_ready"])


if __name__ == "__main__":
    unittest.main()
