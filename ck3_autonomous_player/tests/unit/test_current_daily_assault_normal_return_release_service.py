"""One production-service compound for actual-header normal-return release."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_current_daily_assault_queue_append_service import (
    EXPECTED_SEQUENCE, PENDING, _state, observe_pending, queued_assault_packet,
    query_with_fake_driver, vector,
)
from xar_autoplayer.bridge.army_daily_assault_allocator_witness_contract import (
    ARMY_ALLOCATOR_RVA, ARRG_ALLOCATOR_RVA,
)


def raw_header(present: bool | None, count: int | None, capacity: int | None, identity: str) -> dict:
    ready = present is not None and count is not None and capacity is not None
    return {"status": "available" if ready else "unavailable", "ready": ready,
        "unavailable_reason": "" if ready else "actual_header_operand_unreadable",
        "data_present": present, "data_identity": identity if present else None,
        "count_raw_i32": count, "capacity_raw_i32": capacity}


def allocator_witness(*, arrg: bool, canonical: bool = True) -> dict:
    address = ARRG_ALLOCATOR_RVA if arrg else ARMY_ALLOCATOR_RVA
    expected = f"image+0x{address:X}"
    return {**_state(True), "actual_read_ready": True,
        "actual_identity": expected if canonical else "fixture:other_allocator",
        "expected_identity": expected, "expected_rva_u32": address,
        "matches_expected": canonical}


def with_release_inputs(source: dict) -> dict:
    for group in source["current_daily_assault_table_v1"]["groups"]:
        for name, arrg in (("arrgs", True), ("armies", False)):
            values = group[name]
            identity = f"buffer:{group['physical_slot_i64']}:{name}"
            values["release_header_v1"] = raw_header(True, values["count_raw_i32"], 17, identity)
            values["allocator_witness"] = allocator_witness(arrg=arrg)
    return source


def empty_vectors_packet(*, present: bool = True) -> dict:
    source = queued_assault_packet()
    table = source["current_daily_assault_table_v1"]
    leaf = source["current_daily_assault_loss_inputs_v1"]
    table["groups"] = table["groups"][:1]
    table["groups"][0].update(armies=vector([]), arrgs=vector([], arrg=True, currents=[]))
    table["observed_occupied_group_count"] = 1
    table["header"]["occupied_count_raw_i32"] = 1
    table["physical_controls"][7]["control_raw_u8"] = 0
    leaf["groups"] = leaf["groups"][:1]
    leaf["groups"][0].update(native_current_expected_loss=0, province_magic_raw_u32=0,
                               besieging_inputs_v1=None, army_counts=[])
    leaf["target_regiments"] = []
    with_release_inputs(source)
    for name, arrg in (("arrgs", True), ("armies", False)):
        values = table["groups"][0][name]
        values["release_header_v1"] = raw_header(present, 0, 17, f"allocated-empty:{name}")
        if not present:
            values["allocator_witness"] = allocator_witness(arrg=arrg, canonical=False)
    return source


class CurrentDailyAssaultNormalReturnReleaseServiceTests(unittest.TestCase):
    def test_actual_headers_count_driven_release_and_preserved_queue_normal_return(self):
        outputs = {}

        def query(name: str, source: dict):
            before = deepcopy(source)
            returned, driver = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            item = returned["same_input_current_daily_assault_normal_return_release_v1"][0]
            self.assertEqual(item["army_id"], source["army_id"])
            value = item["projection"]
            for key in ("actual_record_release", "actual_effects", "queue_execution_ready", "queue_drain_replayed",
                        "Army_removal_replayed", "next_day_pending_ready", "full_daily_assault_ready",
                        "full_regular_refill_ready", "full_monthly_ready", "full_calendar_ready", "live"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_post_table"])
            self.assertIsNone(value["actual_post_release_pending_sequence"])
            self.assertEqual(value["native_writes_executed"], 0)
            self.assertEqual(value["stage"], "conditional_current_table_cleanup_normal_return")
            outputs[name] = returned
            if destination := os.environ.get("XAR_DAILY_NORMAL_RETURN_RELEASE_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return returned, value

        source = with_release_inputs(queued_assault_packet())
        returned, value = query("nonnull-canonical-groups-duplicate-pending-and-appends", source)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertEqual(value["conditional_occupied_count_raw_i32"], 0)
        self.assertEqual([step["physical_slot_i64"] for step in value["table_control_count_prefix"]], [4, 7])
        self.assertEqual([step["conditional_occupied_count_after_raw_i32"] for step in value["table_control_count_prefix"]], [1, 0])
        self.assertEqual([vector["role"] for record in value["record_release_prefix"] for vector in record["vectors"]],
                         ["ArRg", "Army", "ArRg", "Army"])
        for record in value["record_release_prefix"]:
            self.assertTrue(record["normal_return_ready"])
            for values in record["vectors"]:
                self.assertTrue(values["normal_return_ready"])
                self.assertEqual(values["conditional_post_header"], {
                    "data_present": False, "data_identity": None, "count_raw_i32": 0, "capacity_raw_i32": 0})
                self.assertEqual(values["buffer_release_call_request"]["element_width"], 4)
                self.assertEqual(values["known_store_requests"][0]["timing"], "before_buffer_release_call")
        controls = {item["physical_slot_i64"]: item["control_raw_u8"] for item in value["conditional_physical_controls"]}
        self.assertEqual((controls[4], controls[7]), (0, 0))
        self.assertTrue(value["conditional_post_release_pending_sequence_ready"])
        self.assertEqual(value["conditional_post_release_pending_sequence"], EXPECTED_SEQUENCE)
        self.assertEqual(value["conditional_post_release_pending_prefix"], EXPECTED_SEQUENCE)
        self.assertEqual([entry["raw_full_id_u32"] for entry in value["conditional_post_release_pending_occurrences"]][2], 0x80000005)
        self.assertEqual(returned["army_strengths"][0]["current_daily_assault_table_v1"][
            "header"]["occupied_count_raw_i32"], 2)

        _, allocated = query("zero-count-nonnull-allocated-empty-vectors-still-release", empty_vectors_packet())
        self.assertTrue(allocated["conditional_table_cleanup_ready"])
        for values in allocated["record_release_prefix"][0]["vectors"]:
            self.assertTrue(values["observed_release_header_v1"]["data_present"])
            self.assertEqual(values["observed_release_header_v1"]["count_raw_i32"], 0)
            self.assertEqual(values["observed_release_header_v1"]["capacity_raw_i32"], 17)
            self.assertEqual(values["release_branch"], "nonnull_canonical_normal_return")
            self.assertEqual(values["conditional_post_header"]["capacity_raw_i32"], 0)
            self.assertIsNotNone(values["buffer_release_call_request"])
        self.assertEqual(allocated["conditional_post_release_pending_sequence"], PENDING)

        _, actual_null = query("actual-null-vectors-preserve-capacity-ignore-noncanonical-witness", empty_vectors_packet(present=False))
        self.assertTrue(actual_null["conditional_table_cleanup_ready"])
        for values in actual_null["record_release_prefix"][0]["vectors"]:
            self.assertEqual(values["release_branch"], "actual_null_data_skip_all_stores")
            self.assertEqual(values["conditional_post_header"]["capacity_raw_i32"], 17)
            self.assertEqual(values["known_store_requests"], [])
            self.assertIsNone(values["buffer_release_call_request"])

        null_capacity_unknown = empty_vectors_packet(present=False)
        null_capacity_unknown["current_daily_assault_table_v1"]["groups"][0]["armies"][
            "release_header_v1"].update(status="unavailable", ready=False,
                unavailable_reason="actual_capacity_unreadable", capacity_raw_i32=None)
        _, value = query("null-unread-capacity-does-not-block-table-or-queue", null_capacity_unknown)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertTrue(value["conditional_post_release_pending_sequence_ready"])
        army = value["record_release_prefix"][0]["vectors"][1]
        self.assertTrue(army["normal_return_ready"])
        self.assertFalse(army["conditional_post_header_ready"])
        self.assertIsNone(army["conditional_post_header"]["capacity_raw_i32"])
        self.assertEqual(value["header_partial_fields"], [{"physical_slot_i64": 4, "role": "Army", "field": "capacity_raw_i32"}])

        nonnull_capacity_unknown = empty_vectors_packet()
        for values in nonnull_capacity_unknown["current_daily_assault_table_v1"]["groups"][0].values():
            if isinstance(values, dict) and "release_header_v1" in values:
                values["release_header_v1"].update(status="unavailable", ready=False,
                    unavailable_reason="unused_before_capacity_unreadable", capacity_raw_i32=None)
        _, value = query("nonnull-unread-before-capacity-still-postzero", nonnull_capacity_unknown)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertTrue(all(values["conditional_post_header_ready"] for values in value["record_release_prefix"][0]["vectors"]))
        self.assertEqual(value["header_partial_fields"], [])

        nonnull_count_unknown = empty_vectors_packet()
        table = nonnull_count_unknown["current_daily_assault_table_v1"]
        group = table["groups"][0]
        for key in ("armies", "arrgs"):
            values = group[key]
            values.update(_state(False, "actual_vector_count_unreadable"), references_ready=False,
                          count_raw_i32=None, data_present=None, data_identity=None)
            values["release_header_v1"].update(status="unavailable", ready=False,
                unavailable_reason="unused_before_count_capacity_unreadable", count_raw_i32=None, capacity_raw_i32=None)
        group.update(_state(False, "actual_vector_count_unreadable"), denominator_ready=False)
        table.update(_state(False, "actual_vector_count_unreadable"), raw_groups_ready=False)
        _, value = query("nonnull-unread-before-count-cap-independent-cleanup", nonnull_count_unknown)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertTrue(all(values["conditional_post_header_ready"] for values in value["record_release_prefix"][0]["vectors"]))
        self.assertFalse(value["conditional_post_release_pending_sequence_ready"])

        second_allocator_unknown = with_release_inputs(queued_assault_packet())
        second_allocator_unknown["current_daily_assault_table_v1"]["groups"][0]["armies"]["allocator_witness"] = allocator_witness(arrg=False, canonical=False)
        _, value = query("Army-noncanonical-retains-completed-ArRg-and-precall-countzero", second_allocator_unknown)
        self.assertFalse(value["conditional_table_cleanup_ready"])
        first = value["record_release_prefix"][0]
        self.assertTrue(first["vectors"][0]["normal_return_ready"])
        self.assertFalse(first["vectors"][1]["normal_return_ready"])
        self.assertEqual(first["vectors"][0]["conditional_post_header"]["capacity_raw_i32"], 0)
        self.assertEqual(first["vectors"][1]["conditional_header_before_free_call"]["count_raw_i32"], 0)
        self.assertIsNone(first["vectors"][1]["conditional_post_header"])
        self.assertEqual(first["vectors"][1]["known_store_requests"], [
            {"field": "count_raw_i32", "value": 0, "timing": "before_buffer_release_call"}])
        self.assertEqual(value["table_control_count_prefix"], [])
        self.assertEqual(value["conditional_occupied_count_raw_i32"], 2)
        self.assertEqual(value["next_missing_record"]["role"], "Army")
        self.assertEqual(value["preserved_pre_release_pending_prefix"], EXPECTED_SEQUENCE)
        self.assertIsNone(value["conditional_post_release_pending_sequence"])

        first_allocator_absent = with_release_inputs(queued_assault_packet())
        first_allocator_absent["current_daily_assault_table_v1"]["groups"][0]["arrgs"]["allocator_witness"] = None
        _, value = query("nonnull-missing-actual-witness-stops-first-vector", first_allocator_absent)
        self.assertFalse(value["conditional_table_cleanup_ready"])
        self.assertEqual(len(value["record_release_prefix"][0]["vectors"]), 1)
        self.assertEqual(value["next_missing_record"]["role"], "ArRg")
        self.assertEqual(value["record_release_prefix"][0]["vectors"][0]["conditional_header_before_free_call"]["count_raw_i32"], 0)

        legacy_header = empty_vectors_packet(present=False)
        legacy_header["current_daily_assault_table_v1"]["groups"][0]["arrgs"]["release_header_v1"] = None
        _, value = query("legacy-optional-null-does-not-infer-actual-data-null-from-zero-count", legacy_header)
        self.assertFalse(value["conditional_table_cleanup_ready"])
        self.assertEqual(value["next_missing_record"]["role"], "ArRg")
        self.assertEqual(value["record_release_prefix"][0]["vectors"][0]["known_store_requests"], [])

        _, value = query("legacy-optional-header-absent", queued_assault_packet())
        self.assertFalse(value["conditional_table_cleanup_ready"])
        self.assertEqual(value["next_missing_record"]["role"], "ArRg")

        smaller_count = with_release_inputs(queued_assault_packet())
        smaller_count["current_daily_assault_table_v1"]["header"]["occupied_count_raw_i32"] = 1
        _, value = query("positive-count-one-releases-only-first-of-two-captured-groups", smaller_count)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertEqual([record["physical_slot_i64"] for record in value["record_release_prefix"]], [4])
        self.assertEqual(value["untouched_captured_group_slots"], [7])
        controls = {entry["physical_slot_i64"]: entry["control_raw_u8"] for entry in value["conditional_physical_controls"]}
        self.assertEqual((controls[4], controls[7]), (0, 1))

        larger_count = with_release_inputs(queued_assault_packet())
        larger_count["current_daily_assault_table_v1"]["header"]["occupied_count_raw_i32"] = 3
        _, value = query("positive-count-needs-uncaptured-end-marker-record", larger_count)
        self.assertFalse(value["conditional_table_cleanup_ready"])
        self.assertEqual(value["conditional_occupied_count_raw_i32"], 1)
        self.assertEqual(len(value["table_control_count_prefix"]), 2)
        self.assertEqual(value["next_missing_record"], {
            "physical_slot_i64": 10, "control_raw_u8": 255,
            "missing_operand": "uncaptured_end_marker_record_payload", "remaining_occupied_count_raw_i32": 1})
        self.assertFalse(value["conditional_post_release_pending_sequence_ready"])

        for count in (0, -2):
            skip = queued_assault_packet()
            skip["current_daily_assault_table_v1"]["header"]["occupied_count_raw_i32"] = count
            _, value = query(f"signed-occupied-count-{count}-skips-release-not-numeric-groups", skip)
            self.assertTrue(value["conditional_table_cleanup_ready"])
            self.assertEqual(value["conditional_occupied_count_raw_i32"], count)
            self.assertEqual(value["record_release_prefix"], [])
            self.assertEqual(value["table_control_count_prefix"], [])
            self.assertEqual(value["untouched_captured_group_slots"], [4, 7])
            self.assertEqual(value["conditional_post_release_pending_sequence"], EXPECTED_SEQUENCE)

        numerical_partial = with_release_inputs(queued_assault_packet(partial_next_group=True))
        _, value = query("numerical-prefix-partial-independent-normal-return-table-ready", numerical_partial)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertTrue(value["conditional_post_release_pending_prefix_ready"])
        self.assertFalse(value["conditional_post_release_pending_sequence_ready"])
        self.assertEqual(value["conditional_post_release_pending_prefix"], [7, 7, -2147483643, 12, 12, -2147483643])

        missing_pending = with_release_inputs(queued_assault_packet())
        observe_pending(missing_pending, None)
        _, value = query("missing-pending-does-not-block-known-table-release", missing_pending)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertFalse(value["preserved_pre_release_pending_prefix_ready"])
        self.assertFalse(value["conditional_post_release_pending_sequence_ready"])

        empty_table = queued_assault_packet()
        table = empty_table["current_daily_assault_table_v1"]
        table.update(groups=[], physical_controls=[], observed_occupied_group_count=0, physical_scan_ready=False)
        table["header"] = {key: None for key in table["header"]}
        table["header"].update(_state(False, "unused_empty_header"), occupied_count_raw_i32=0)
        del empty_table["current_daily_assault_loss_inputs_v1"]
        _, value = query("known-empty-count-skips-with-unused-table-header", empty_table)
        self.assertTrue(value["conditional_table_cleanup_ready"])
        self.assertEqual(value["conditional_post_release_pending_sequence"], PENDING)


if __name__ == "__main__":
    unittest.main()
