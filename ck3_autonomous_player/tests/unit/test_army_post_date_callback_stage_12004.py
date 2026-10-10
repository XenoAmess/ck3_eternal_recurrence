"""One new offline source-stage consumer check; no native producer replay."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import unittest


_MODULE = Path(__file__).resolve().parents[2] / "src/xar_autoplayer/bridge/army_post_date_callback_stage_12004.py"
_SPEC = importlib.util.spec_from_file_location("owned_post_date_stage", _MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("owned stage leaf unavailable")
_LEAF = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_LEAF)
project = _LEAF.project_army_post_date_callback_stage_12004


class ArmyPostDateCallbackStage12004(unittest.TestCase):
    def test_source_route_entry_and_partial_capture_keep_historical_context_unknown(self):
        # Synthetic adapter inputs only. No engine, native fixture or old
        # qualification is replayed; source-route semantics are the new focus.
        event = {
            "sequence": 7, "army_id": 0x15000001, "native_carmy_id": 0x18000001,
            "passed_date_raw64": 0x1234567812345678,
            "caller_return_rva": 0x2A9AB4B,
            "before": {"supply_raw": 0, "last_supply_update_date_raw64": 0,
                       "supply_updated_byte_raw": 0},
            "after": {"supply_raw": 900000, "last_supply_update_date_raw64": 99,
                      "supply_updated_byte_raw": 1},
            "same_instance_after": True, "capture_failure_flags": 0,
        }
        second = deepcopy(event)
        second.update(sequence=8, passed_date_raw64=0xFEDCBA9887654321)
        second["before"]["supply_raw"] = -300000
        family = {
            "status": "available", "source": "native_natural_supply_callback_entry_return",
            "identity_basis": "public_unit_and_native_carmy_full_ids_at_invocation",
            "observer_installed": True, "oldest_available_sequence": 5,
            "latest_sequence": 99, "overwritten_events": 4,
            "unattributed_capture_failures": 2,
            "event_count": 2, "events": [event, second],
            # A later query's membership must have no influence on this join.
            "current_native_day_index_raw_i32": -1,
            "current_bucket_matching_positions": [0, 3],
        }
        original = deepcopy(family)
        result = project(family)
        self.assertEqual(family, original)
        self.assertEqual(result["source_matched_event_count"], 2)
        self.assertEqual(result["complete_source_matched_entry_count"], 2)
        self.assertEqual(result["journal_counters"]["latest_sequence"], 99)
        self.assertEqual([row["callback_entry_fields"]["supply_raw"]
                          for row in result["events"]], [0, -300000])
        self.assertEqual([row["passed_date_raw64"] for row in result["events"]],
                         [0x1234567812345678, 0xFEDCBA9887654321])
        for row in result["events"]:
            self.assertIsNone(row["stored_day_index_at_dispatch_u32"])
            self.assertIsNone(row["selected_bucket_at_dispatch_i32"])
            self.assertIsNone(row["actual_bucket_occurrence_index_i32"])
            self.assertIsNone(row["subject_late_reset_executed"])
            self.assertIsNone(row["subject_was_processed_in_late_roster"])
        self.assertFalse(result["full_daily_ready"])
        self.assertFalse(result["full_monthly_ready"])
        self.assertFalse(result["new_live_evidence"])
        self.assertFalse(result["current_query_membership_used"])

        partial = deepcopy(family)
        partial["events"][0]["before"]["last_supply_update_date_raw64"] = None
        partial["events"][0]["same_instance_after"] = False
        partial["events"][0]["capture_failure_flags"] = 6
        partial["events"][1]["caller_return_rva"] = 0x24E3430
        result = project(partial)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["source_matched_event_count"], 1)
        self.assertEqual(result["complete_source_matched_entry_count"], 0)
        self.assertEqual(result["events"][0]["callback_entry_fields"]["supply_raw"], 0)
        self.assertIsNone(result["events"][1]["source_stage"])
        self.assertEqual(result["events"][1]["callback_entry_fields"]["supply_raw"], -300000)

        empty = deepcopy(family)
        empty.update(event_count=0, events=[])
        result = project(empty)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["retained_event_count"], 0)
        self.assertIn("no retained", result["empty_matching_events_meaning"])
        self.assertFalse(result["full_daily_ready"])
        self.assertEqual(project(None)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
