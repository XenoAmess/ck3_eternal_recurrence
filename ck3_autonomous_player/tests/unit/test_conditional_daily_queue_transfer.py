"""One service case for logical daily queue transfer and its first request."""
from copy import deepcopy
import unittest

from test_conditional_monthly_loss_budgets import monthly_budget_packet, MemoryStrengthService


def daily_queue_packet(raw_ids, identities):
    packet = monthly_budget_packet()
    rows = []
    for index, (raw_id, identity) in enumerate(zip(raw_ids or [], identities)):
        if identity is None:
            rows.append({
                "status": "unavailable", "unavailable_reason": "initial_resolution_unavailable",
                "stored_index": index, "raw_army_reference_id": raw_id,
                "resolved_army_id": None, "used_fallback": None,
                "army_magic_14_raw": None, "native_army_identity_valid": None,
            })
        else:
            resolved, fallback, magic = identity
            rows.append({
                "status": "available", "unavailable_reason": None,
                "stored_index": index, "raw_army_reference_id": raw_id,
                "resolved_army_id": resolved, "used_fallback": fallback,
                "army_magic_14_raw": magic,
                "native_army_identity_valid": magic == 0x41726D79 and resolved != -1,
            })
    ready = raw_ids is not None and all(row["status"] == "available" for row in rows)
    packet["monthly_daily_queue_inputs_v1"] = {
        "status": "available" if ready else "unavailable", "ready": ready,
        "unavailable_reason": None if ready else "initial_queue_inputs_unavailable",
        "manager_army_id_list_2a5a8": raw_ids,
        "initial_army_resolution_rows": rows if raw_ids is not None else None,
    }
    return packet


class ConditionalDailyQueueTransferTests(unittest.TestCase):
    def test_query_transfers_order_then_selects_only_initial_first_removal_request(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            allocation = service.query_army_strengths([0], expected_revision=2)["loss_allocation_requests_v1"][0]
            transfer = allocation["same_input_conditional_daily_id_transfer_v1"]
            self.assertEqual(packet, original)
            self.assertEqual(service.calls, 1)
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            self.assertFalse(transfer["actual_transfer"])
            self.assertFalse(transfer["actual_removal"])
            self.assertIsNone(transfer["actual_source_queue_after"])
            self.assertIsNone(transfer["actual_removal_post_state"])
            self.assertFalse(transfer["full_ordered_removal_requests_ready"])
            self.assertFalse(transfer["full_monthly_lifecycle_ready"])
            caller = allocation["same_input_conditional_monthly_caller_effects_v1"]
            self.assertEqual(caller["native_date_pointer_origin"], "GameState+8")
            self.assertTrue(caller["native_date_pointer_origin_source_closed"])
            self.assertIsNone(caller["actual_caller_passed_date_raw64"])
            return allocation, transfer

        magic = 0x41726D79
        packet = daily_queue_packet(
            [19, 23, 7, 7, 8],
            [(-1, True, magic), (23, False, 0), (7, False, magic),
             (7, False, magic), (8, False, magic)],
        )
        allocation, transfer = query(packet)
        self.assertTrue(transfer["conditional_transfer_ready"])
        self.assertEqual(transfer["transfer_branch"], "transfer")
        self.assertEqual(transfer["source_manager_army_id_list_before"], [19, 23, 7, 7, 8])
        self.assertEqual(transfer["conditional_temporary_ordered_army_ids"], [19, 23, 7, 7, 8])
        self.assertEqual(transfer["conditional_source_manager_army_id_list_after_transfer"], [])
        self.assertEqual([row["stored_index"] for row in transfer["initial_invalid_prefix_occurrences"]], [0, 1])
        self.assertTrue(transfer["initial_removal_selection_ready"])
        self.assertTrue(transfer["first_removal_call_request_ready"])
        first = transfer["first_removal_call_request"]
        self.assertEqual((first["stored_index"], first["raw_army_reference_id"], first["resolved_army_id"]), (2, 7, 7))
        self.assertEqual(first["native_entry_rva"], "0x2A978A0")
        self.assertFalse(first["used_fallback"])
        # Initial duplicate7 still looks valid. The first call can change its
        # database slot and generation, so neither later request is invented.
        self.assertEqual(transfer["remaining_occurrences"], [
            {"stored_index": 3, "raw_army_reference_id": 7},
            {"stored_index": 4, "raw_army_reference_id": 8},
        ])
        self.assertTrue(transfer["post_removal_stage_required"])
        self.assertEqual(transfer["remaining_occurrences_basis"], "requires_post_removal_stage_frames")
        self.assertEqual(transfer["status"], "partial")
        self.assertIn("post_removal_stage_full_id_slot_and_virtual_effects", transfer["missing_inputs"])
        self.assertTrue(allocation["same_input_conditional_monthly_loss_budgets_v1"]["conditional_budgets_ready"])

        _, fallback = query(daily_queue_packet([991], [(77, True, magic)]))
        self.assertTrue(fallback["first_removal_call_request_ready"])
        self.assertEqual(fallback["first_removal_call_request"]["resolved_army_id"], 77)
        self.assertTrue(fallback["first_removal_call_request"]["used_fallback"])
        self.assertFalse(fallback["post_removal_stage_required"])
        self.assertEqual(fallback["status"], "available")

        _, empty = query(daily_queue_packet([], []))
        self.assertTrue(empty["conditional_transfer_ready"])
        self.assertEqual(empty["transfer_branch"], "not_called")
        self.assertEqual(empty["conditional_temporary_ordered_army_ids"], [])
        self.assertEqual(empty["conditional_source_manager_army_id_list_after_transfer"], [])
        self.assertTrue(empty["initial_removal_selection_ready"])
        self.assertFalse(empty["first_removal_call_request_ready"])
        self.assertIsNone(empty["first_removal_call_request"])
        self.assertEqual(empty["remaining_occurrences"], [])

        _, missing = query(daily_queue_packet(None, []))
        self.assertFalse(missing["conditional_transfer_ready"])
        self.assertIsNone(missing["conditional_temporary_ordered_army_ids"])
        self.assertIsNone(missing["conditional_source_manager_army_id_list_after_transfer"])
        self.assertEqual(missing["status"], "unavailable")

        _, unknown = query(daily_queue_packet(
            [19, 20, 7], [(-1, True, magic), None, (7, False, magic)]))
        self.assertTrue(unknown["conditional_transfer_ready"])
        self.assertEqual(unknown["conditional_source_manager_army_id_list_after_transfer"], [])
        self.assertEqual(len(unknown["initial_invalid_prefix_occurrences"]), 1)
        self.assertFalse(unknown["initial_removal_selection_ready"])
        self.assertFalse(unknown["first_removal_call_request_ready"])
        self.assertIsNone(unknown["first_removal_call_request"])
        self.assertFalse(unknown["post_removal_stage_required"])
        self.assertEqual(unknown["remaining_occurrences_basis"], "unknown_initial_resolution")
        self.assertEqual(unknown["remaining_occurrences"], [
            {"stored_index": 1, "raw_army_reference_id": 20},
            {"stored_index": 2, "raw_army_reference_id": 7},
        ])

        _, invalid = query(daily_queue_packet([19, 23], [(-1, True, magic), (23, False, 0)]))
        self.assertTrue(invalid["initial_removal_selection_ready"])
        self.assertFalse(invalid["first_removal_call_request_ready"])
        self.assertEqual(len(invalid["initial_invalid_prefix_occurrences"]), 2)
        self.assertEqual(invalid["status"], "available")

        # Queue value remains independently useful when no initial resolution
        # family is available; optional absence never manufactures a request.
        partial = daily_queue_packet([7], [(7, False, magic)])
        partial["monthly_daily_queue_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="initial_resolution_unavailable",
            initial_army_resolution_rows=None)
        _, no_rows = query(partial)
        self.assertTrue(no_rows["conditional_transfer_ready"])
        self.assertFalse(no_rows["initial_removal_selection_ready"])
        self.assertEqual(no_rows["status"], "partial")

        absent = monthly_budget_packet()
        _, disabled = query(absent)
        self.assertFalse(disabled["conditional_transfer_ready"])
        self.assertIsNone(disabled["first_removal_call_request"])


if __name__ == "__main__":
    unittest.main()
