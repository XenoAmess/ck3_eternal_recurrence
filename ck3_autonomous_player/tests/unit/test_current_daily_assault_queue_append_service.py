"""One production-service compound for bounded pre-release queue assembly."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_current_daily_assault_loss_service import (
    RA, RP, _state, all_currents, assault_packet, b_family, count_regiment,
    fixed_data, query_with_fake_driver, vector,
)
from test_post_refill_land_rate_service_join import row

HIGH_RAW = 0x80000005
HIGH_STORED = -2147483643
PENDING = [7, 7, HIGH_STORED]
APPENDED_RAW = [12, 12, HIGH_RAW, 12]
EXPECTED_SEQUENCE = [7, 7, HIGH_STORED, 12, 12, HIGH_STORED, 12]


def observe_pending(source: dict, values: list | None) -> dict:
    """Queue observation is useful without unconsumed removal predicates."""
    source["monthly_daily_queue_inputs_v1"] = {
        "status": "available" if values == [] else "unavailable",
        "ready": values == [],
        "unavailable_reason": None if values == [] else "initial_queue_resolution_unavailable",
        "manager_army_id_list_2a5a8": deepcopy(values),
        "initial_army_resolution_rows": [] if values == [] else None,
    }
    return source


def queued_assault_packet(*, partial_next_group: bool = False) -> dict:
    """A killed target queues original repeated IDs, including a valid fallback."""
    source = assault_packet()
    table = source["current_daily_assault_table_v1"]
    leaf = source["current_daily_assault_loss_inputs_v1"]
    all_currents(source, RP, 0)
    leaf["target_regiments"][1]["replenishment_records_v1"] = fixed_data(RP, 51002, 0, 100)
    table["groups"][0]["armies"] = vector([12, 12, HIGH_RAW])
    fallback = table["groups"][0]["armies"]["occurrences"][2]["resolution"]
    fallback.update(object_identity="army:12", selected_full_id_u32=12)
    leaf["groups"][0]["army_counts"] = []
    for ordinal, item in enumerate(table["groups"][0]["armies"]["occurrences"]):
        leaf["groups"][0]["army_counts"].append({**_state(True), "native_index": ordinal,
            "raw_full_id_u32": item["raw_full_id_u32"], "resolution": deepcopy(item["resolution"]),
            "native_whole_current_soldiers": 200, "regiments": [count_regiment(0, RA, 200, 300)]})
    leaf["groups"][1]["army_counts"][0].update(native_whole_current_soldiers=200,
        regiments=[count_regiment(0, RA, 200, 300)])
    first = leaf["groups"][0]
    first.update(native_current_expected_loss=400, besieging_inputs_v1=b_family(400, rp_current=0, all_rows=False))
    first["besieging_inputs_v1"]["assault_context"]["casualty_percentage_raw"] = 10000000
    second = leaf["groups"][1]
    second.update(native_current_expected_loss=53, besieging_inputs_v1=b_family(530, rp_current=0))
    second["besieging_inputs_v1"]["native_assault_expected_loss"] = 53
    if partial_next_group:
        second["besieging_inputs_v1"]["assault_context"].update(status="unavailable",
            unavailable_reason="actual_group_percentage_unreadable", casualty_percentage_raw=None)
    return observe_pending(source, PENDING)


class CurrentDailyAssaultQueueAppendServiceTests(unittest.TestCase):
    def test_current_pending_plus_qualified_raw_append_prefix_preserves_stage(self):
        outputs = {}

        def query(name: str, source: dict):
            before = deepcopy(source)
            returned, driver = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            item = returned["same_input_current_daily_assault_queue_append_v1"][0]
            self.assertEqual(item["army_id"], source["army_id"])
            value = item["projection"]
            for key in ("actual_append", "actual_effects", "queue_execution_ready", "queue_drain_replayed",
                        "record_release_effects_ready", "post_release_pending_ready", "next_day_pending_ready",
                        "full_daily_assault_ready", "full_regular_refill_ready", "full_monthly_ready", "full_calendar_ready"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_pre_release_pending_sequence"])
            self.assertIsNone(value["actual_post_release_pending_sequence"])
            self.assertEqual(value["native_writes_executed"], 0)
            self.assertEqual(value["stage"], "conditional_pre_release_pending_queue")
            outputs[name] = returned
            if destination := os.environ.get("XAR_DAILY_QUEUE_APPEND_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return returned, value

        source = queued_assault_packet()
        returned, value = query("nonempty-pending-duplicates-high-raw-fallback-repeats", source)
        self.assertTrue(value["observed_pending_ready"])
        self.assertTrue(value["known_append_prefix_ready"])
        self.assertTrue(value["append_requests_complete"])
        self.assertTrue(value["conditional_pre_release_pending_sequence_ready"])
        self.assertEqual(value["observed_pending_army_ids_i32"], PENDING)
        self.assertEqual(value["conditional_pre_release_pending_sequence"], EXPECTED_SEQUENCE)
        self.assertEqual(value["conditional_pre_release_pending_prefix"], EXPECTED_SEQUENCE)
        self.assertEqual([item["raw_full_id_u32"] for item in value["known_append_occurrences"]], APPENDED_RAW)
        self.assertEqual([item["stored_army_id_i32"] for item in value["known_append_occurrences"]], [12, 12, HIGH_STORED, 12])
        self.assertEqual([item["stored_index"] for item in value["conditional_pre_release_occurrences"]], list(range(7)))
        self.assertEqual([item["provenance"] for item in value["conditional_pre_release_occurrences"][:3]],
                         ["observed_primary68_pending"] * 3)
        self.assertEqual([item["group_native_index"] for item in value["known_append_occurrences"]], [0, 0, 0, 1])
        self.assertEqual([item["army_native_index"] for item in value["known_append_occurrences"]], [0, 1, 2, 0])
        fallback = source["current_daily_assault_table_v1"]["groups"][0]["armies"]["occurrences"][2]
        self.assertTrue(fallback["resolution"]["used_fallback"])
        self.assertEqual(fallback["resolution"]["selected_full_id_u32"], 12)
        self.assertEqual(value["known_append_occurrences"][2]["raw_full_id_u32"], HIGH_RAW)
        self.assertEqual(returned["army_strengths"][0]["monthly_daily_queue_inputs_v1"][
            "manager_army_id_list_2a5a8"], PENDING)

        _, partial = query("sequential-known-appends-before-missing-next-group", queued_assault_packet(partial_next_group=True))
        self.assertTrue(partial["known_append_prefix_ready"])
        self.assertFalse(partial["append_requests_complete"])
        self.assertFalse(partial["conditional_pre_release_pending_sequence_ready"])
        self.assertIsNone(partial["conditional_pre_release_pending_sequence"])
        self.assertTrue(partial["conditional_pre_release_pending_prefix_ready"])
        self.assertEqual(partial["conditional_pre_release_pending_prefix"], [7, 7, HIGH_STORED, 12, 12, HIGH_STORED])
        self.assertEqual(partial["completed_loss_group_count"], 1)
        self.assertEqual(partial["next_missing_group"]["native_index"], 1)
        self.assertEqual(partial["next_missing_group"]["physical_slot_i64"], 7)
        self.assertTrue(partial["next_missing_group"]["sequential_entry_reached"])
        self.assertTrue(partial["next_missing_group"]["missing_inputs"])

        missing_pending = queued_assault_packet()
        observe_pending(missing_pending, None)
        _, value = query("missing-pending-retains-independent-complete-appends", missing_pending)
        self.assertFalse(value["observed_pending_ready"])
        self.assertTrue(value["known_append_prefix_ready"])
        self.assertTrue(value["append_requests_complete"])
        self.assertEqual([item["raw_full_id_u32"] for item in value["known_append_occurrences"]], APPENDED_RAW)
        self.assertFalse(value["conditional_pre_release_pending_prefix_ready"])
        self.assertIsNone(value["conditional_pre_release_pending_prefix"])
        self.assertIsNone(value["conditional_pre_release_pending_sequence"])
        self.assertTrue(all(item["stored_index"] is None for item in value["known_append_occurrences"]))

        missing_both = queued_assault_packet(partial_next_group=True)
        observe_pending(missing_both, None)
        _, value = query("missing-pending-retains-partial-append-prefix", missing_both)
        self.assertTrue(value["known_append_prefix_ready"])
        self.assertFalse(value["append_requests_complete"])
        self.assertEqual(value["known_append_army_ids_i32"], [12, 12, HIGH_STORED])
        self.assertEqual(value["next_missing_group"]["native_index"], 1)

        first_missing = queued_assault_packet()
        first_missing["current_daily_assault_loss_inputs_v1"]["target_regiments"][0].update(
            _state(False, "target_DATA_unreadable"), replenishment_records_v1=None)
        _, value = query("first-consumed-DATA-missing-no-invented-empty-tail", first_missing)
        self.assertTrue(value["observed_pending_ready"])
        self.assertFalse(value["known_append_prefix_ready"])
        self.assertFalse(value["append_requests_complete"])
        self.assertIsNone(value["conditional_pre_release_pending_prefix"])
        self.assertEqual(value["next_missing_group"]["native_index"], 0)
        self.assertEqual(value["known_append_occurrences"], [])

        unchanged = observe_pending(assault_packet(), PENDING)
        _, value = query("complete-nonempty-loss-no-appends-copy-pending", unchanged)
        self.assertTrue(value["append_requests_complete"])
        self.assertEqual(value["known_append_occurrences"], [])
        self.assertEqual(value["conditional_pre_release_pending_sequence"], PENDING)

        empty_table = observe_pending(assault_packet(), PENDING)
        table = empty_table["current_daily_assault_table_v1"]
        table.update(groups=[], physical_controls=[], observed_occupied_group_count=0, physical_scan_ready=False)
        table["header"] = {key: None for key in table["header"]}
        table["header"].update(_state(False, "unused_empty_header"), occupied_count_raw_i32=0)
        del empty_table["current_daily_assault_loss_inputs_v1"]
        _, value = query("complete-empty-table-copy-nonempty-pending", empty_table)
        self.assertTrue(value["conditional_pre_release_pending_sequence_ready"])
        self.assertEqual(value["conditional_pre_release_pending_sequence"], PENDING)
        self.assertEqual(value["completed_loss_group_count"], 0)
        self.assertIsNone(value["next_missing_group"])

        observe_pending(empty_table, [])
        _, value = query("complete-empty-table-empty-pending-legal-zero", empty_table)
        self.assertTrue(value["conditional_pre_release_pending_sequence_ready"])
        self.assertEqual(value["conditional_pre_release_pending_sequence"], [])
        self.assertEqual(value["conditional_pre_release_occurrences"], [])

        legacy_with_queue = observe_pending(row(), PENDING)
        _, value = query("missing-loss-table-keeps-current-pending-observation", legacy_with_queue)
        self.assertTrue(value["observed_pending_ready"])
        self.assertFalse(value["known_append_prefix_ready"])
        self.assertIsNone(value["conditional_pre_release_pending_sequence"])
        self.assertEqual(value["loss_missing_inputs"], ["current_daily_assault_table_v1"])

        _, value = query("legacy-without-both-families", row())
        self.assertFalse(value["observed_pending_ready"])
        self.assertFalse(value["known_append_prefix_ready"])
        self.assertEqual(value["status"], "unavailable")
        self.assertIsNone(value["conditional_pre_release_pending_sequence"])


if __name__ == "__main__":
    unittest.main()
