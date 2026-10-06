from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pre_date_pending_update_fixture import (
    bypass_source, later_partial_source, missing_context_source, same_roster_standalone_source,
    source, zero_source,
)
from test_current_daily_assault_table_service import source_row
from test_scoped_ordered_refill_service import MemoryRoute


class PreDatePendingUpdateServiceTests(unittest.TestCase):
    def test_real_ordered_pending_counts_then_removal_requests_and_independent_current(self):
        outputs = {}

        def query(name, leaf):
            payload = source_row(None)
            if leaf is not None:
                payload["current_pre_date_pending_update_inputs_v1"] = leaf
                payload["current_daily_assault_roster_admission_v1"] = same_roster_standalone_source(leaf)
            before = deepcopy(payload)
            service = MemoryRoute(payload)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(payload, before)
            self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"], {"current_strength": True, "full_monthly": False})
            row = returned["army_strengths"][0]
            self.assertEqual(row["current_soldiers"], 160)
            projection = row["same_input_conditional_current_pre_date_pending_update_v1"]
            self.assertFalse(projection["actual_pre_date_callback_ready"])
            self.assertFalse(projection["actual_tomorrow_roster_ready"])
            self.assertFalse(projection["full_daily_assault_ready"])
            self.assertFalse(projection["full_monthly_ready"])
            self.assertEqual(projection["native_mutator_invocations"], 0)
            self.assertEqual(projection["native_writes"], 0)
            outputs[name] = {"service": returned}
            return projection

        main = query("existing-key-ordered-A-A", source())
        self.assertTrue(main["ready"])
        self.assertEqual([r["pending_count_before"] for r in main["occurrences"]], [0, 1])
        self.assertEqual([r["pending_count_after"] for r in main["occurrences"]], [1, 2])
        self.assertEqual([r["removal_requested"] for r in main["occurrences"]], [False, True])
        self.assertEqual(main["pending_lists"][0]["conditional_full_ids_u32"], [100, 100])
        self.assertEqual(main["conditional_removal_queue_full_ids_u32"], [99, 99, 13])
        self.assertEqual(main["conditional_skip_2a99b40_occurrence_indices"], [1])
        self.assertEqual(main["occurrences"][1]["pending_setup_branch"], "evolving_existing_key")

        old = query("existing-nonempty-duplicate-pending-values", source(pending_ids=(100, 100)))
        self.assertTrue(old["ready"])
        self.assertEqual([r["pending_count_after"] for r in old["occurrences"]], [3, 4])
        self.assertEqual(old["pending_lists"][0]["conditional_full_ids_u32"], [100, 100, 100, 100])
        self.assertEqual(old["removal_append_requests"], [])

        direct = query("direct-empty-then-evolving-existing-key", source(mode="direct"))
        self.assertTrue(direct["ready"])
        self.assertEqual([r["pending_setup_branch"] for r in direct["occurrences"]], ["direct_empty", "evolving_existing_key"])
        self.assertEqual(direct["pending_lists"][0]["conditional_full_ids_u32"], [100, 100])

        mixed = query("real-subject-contract-persistent-war-arms", source(roster=(13,), branches=[
            "current_zero", "contract_nonzero", "state_not_one", "persistent_sentinel",
            "war_magic_invalid", "war_full_id_invalid", "valid_war",
        ]))
        self.assertTrue(mixed["ready"])
        self.assertEqual(mixed["pending_lists"][0]["conditional_full_ids_u32"], [100, 101, 104, 105])
        self.assertEqual(mixed["pending_lists"][0]["conditional_count"], 4)
        self.assertEqual([r["append"] for r in mixed["occurrences"][0]["arrg_selection_ledger"]],
                         [True, True, False, False, True, True, False])
        self.assertFalse(mixed["occurrences"][0]["removal_requested"])

        partial = query("later-missing-contract-keeps-completed-prefix", later_partial_source())
        self.assertFalse(partial["ready"])
        self.assertEqual(partial["completed_original_occurrence_count"], 1)
        self.assertEqual(partial["pending_lists"][0]["conditional_count"], 1)
        self.assertEqual(partial["pending_lists"][0]["conditional_full_ids_u32"], [100])
        self.assertEqual(partial["removal_append_requests"], [])

        collision = query("actual-carried-pending-branch-stays-independent", source(mode="collision"))
        self.assertFalse(collision["ready"])
        self.assertEqual(collision["unavailable_reason"], "pending_table_carried_collision_unmodeled")
        self.assertEqual(collision["completed_original_occurrence_count"], 0)
        self.assertEqual(collision["pending_lists"], [])

        for kind in ("combat", "counter"):
            bypass = query("known-" + kind + "-bypass-unused-pending", bypass_source(kind))
            self.assertTrue(bypass["ready"])
            self.assertEqual(bypass["removal_append_requests"], [])
            self.assertTrue(all(r["pending_mutator_selected"] is False for r in bypass["occurrences"]))

        zero = query("known-zero-roster-independent-missing-old-queue", zero_source())
        self.assertTrue(zero["ready"])
        self.assertEqual(zero["pending_lists"], [])
        self.assertIsNone(zero["conditional_removal_queue_full_ids_u32"])
        missing = query("missing-manager-is-not-zero", missing_context_source())
        self.assertFalse(missing["ready"])
        legacy = query("legacy-current-strength-independent-newleaf", None)
        self.assertFalse(legacy["ready"])
        self.assertEqual(legacy["status"], "unavailable")

        output = os.environ.get("XAR_PRE_DATE_PENDING_CASE_OUTPUT")
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
