"""One production-service compound for current and derived first-request context."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_current_daily_assault_normal_return_release_service import with_release_inputs
from test_current_daily_assault_queue_append_service import (
    HIGH_RAW, HIGH_STORED, _state, observe_pending, queued_assault_packet,
    query_with_fake_driver, vector,
)
from test_current_daily_assault_table_service import resolution

OFFSETS = ("50", "68", "80", "98", "c8", "158")
MAGIC = 0x41726D79


def selected_resolution(raw: int, actual: int, identity: str, *, fallback: bool) -> dict:
    value = resolution(raw, fallback=fallback, kind="army")
    value.update(selected_full_id_u32=actual, object_identity=identity)
    return value


def unknown_resolution(raw: int) -> dict:
    value = {key: None for key in resolution(raw, kind="army")}
    value.update(_state(False, "actual_resolution_unreadable"), requested_full_id_u32=raw)
    return value


def reference(index: int, raw: int, argument: int, *, pending_index=None,
              group_index=None, group_slot=None, army_index=None, valid=True,
              fallback=True, target_index=0) -> dict:
    scope = "current_pending" if pending_index is not None else "current_group_army"
    actual = argument if valid else 0xFFFFFFFF
    identity = f"army:fallback:{actual}" if fallback else f"army:regular:{actual}"
    return {**_state(True), "native_index": index, "reference_scope": scope,
        "pending_native_index": pending_index, "group_native_index": group_index,
        "group_physical_slot_i64": group_slot, "group_army_native_index": army_index,
        "raw_full_id_u32": raw, "resolution": selected_resolution(raw, actual, identity, fallback=fallback),
        "army_magic_14_raw_u32": MAGIC, "native_army_identity_valid": valid,
        "identity_scalar_basis": "copied_current_pending_magic" if scope == "current_pending" else "native_current_group_magic",
        "cleanup_target_index": target_index if valid else None}


def target(argument: int) -> dict:
    passed = f"army:fallback:{argument}"
    helper = f"army:regular:{argument}"
    return {**_state(True), "native_index": 0, "argument_full_id_u32": argument,
        "helper_resolution": selected_resolution(argument, argument, helper, fallback=False),
        "selected_bucket_index_u32": argument % 30, "bucket_count_raw_i32": 5,
        "bucket_data_present": True,
        "bucket_rows": [{"native_index": index, "pointer_identity": identity,
            "native_same_helper_pointer": matches} for index, (identity, matches) in enumerate([
                (passed, False), (helper, True), ("army:other", False),
                (helper, True), ("native:0", False)])]}


def attach_globals(source: dict, family: dict, argument: int, pending: list, *, candidate: bool) -> None:
    signed = argument - (1 << 32) if argument & (1 << 31) else argument
    lists = [
        ("50", [signed, 991, signed, 8]), ("68", pending),
        ("80", [signed, 5, signed, 9]), ("98", [5, 6]),
        ("c8", [signed]), ("158", [signed, signed])]
    records = [[argument, 0x12345678, 0xFFFFFFFF, 1], [5, 2, 3, 4],
        [argument, 99, 88, 77], [6, 0x80000000, 9, 10], [argument, 55, 66, 77]]
    family.update(manager_id_lists=[{"manager_offset": offset, "ordered_army_ids": deepcopy(ids)} for offset, ids in lists],
                  records_b0=deepcopy(records))
    source["monthly_first_removal_cleanup_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "candidate_found": candidate, "candidate_stored_index": 1 if candidate else None,
        "argument_army_id": signed if candidate else None,
        "cleanup_resolved_army_id": signed if candidate else None,
        "cleanup_used_fallback": False if candidate else None,
        "selected_bucket_index": argument % 30 if candidate else None,
        "id_lists": deepcopy(family["manager_id_lists"]),
        "selected_bucket_rows": [{"stored_index": index,
            "observed_army_id": signed if index in (0, 1, 3) else 8 if index == 2 else None,
            "native_same_cleanup_army_pointer": index in (1, 3)} for index in range(5)] if candidate else None,
        "records_b0": deepcopy(records)}


def removal_context_packet(*, current_pending=False, partial_next_group=False, argument=77) -> dict:
    source = with_release_inputs(queued_assault_packet(partial_next_group=partial_next_group))
    table = source["current_daily_assault_table_v1"]
    losses = source["current_daily_assault_loss_inputs_v1"]
    for group, loss in zip(table["groups"], losses["groups"]):
        ids = [HIGH_RAW] * len(group["armies"]["occurrences"])
        group["armies"]["occurrences"] = vector(ids)["occurrences"]
        for occurrence, count in zip(group["armies"]["occurrences"], loss["army_counts"]):
            resolved = selected_resolution(HIGH_RAW, argument, f"army:fallback:{argument}", fallback=True)
            occurrence["resolution"] = deepcopy(resolved)
            count.update(raw_full_id_u32=HIGH_RAW, resolution=deepcopy(resolved))
    signed = argument - (1 << 32) if argument & (1 << 31) else argument
    pending = [19, HIGH_STORED, signed, signed, 8] if current_pending else []
    scalar_rows = []
    references = []
    for index, identity in enumerate(pending):
        raw = identity & 0xFFFFFFFF
        valid = index != 0
        actual = argument if index in (1, 2, 3) else 8 if index == 4 else 0xFFFFFFFF
        fallback = index in (0, 1)
        references.append(reference(index, raw, actual, pending_index=index,
            valid=valid, fallback=fallback, target_index=1 if index == 4 else 0))
        scalar_rows.append({"status": "available", "unavailable_reason": None,
            "stored_index": index, "raw_army_reference_id": identity,
            "resolved_army_id": -1 if not valid else signed if index in (1, 2, 3) else 8,
            "used_fallback": fallback, "army_magic_14_raw": MAGIC,
            "native_army_identity_valid": valid})
    source["monthly_daily_queue_inputs_v1"] = {"status": "available", "ready": True,
        "unavailable_reason": None, "manager_army_id_list_2a5a8": pending,
        "initial_army_resolution_rows": scalar_rows}
    for group in table["groups"]:
        for occurrence in group["armies"]["occurrences"]:
            references.append(reference(len(references), HIGH_RAW, argument,
                group_index=group["native_index"], group_slot=group["physical_slot_i64"],
                army_index=occurrence["native_index"]))
    targets = [target(argument)]
    if current_pending:
        targets.append({**_state(False, "unused_later_argument_bucket_unreadable"),
            "native_index": 1, "argument_full_id_u32": 8,
            "helper_resolution": unknown_resolution(8), "selected_bucket_index_u32": None,
            "bucket_count_raw_i32": None, "bucket_data_present": None, "bucket_rows": None})
    family = {"schema_version": 1, "source": "native_current_assault_removal_references",
        "stage": "observed_current_removal_reference_context",
        **_state(not current_pending, "unused_later_argument_bucket_unreadable"),
        "manager_identity": "fixture:primary_manager", "observed_pending_ids_i32": deepcopy(pending),
        "manager_id_lists": [], "records_b0": None,
        "reference_occurrences": references, "cleanup_targets": targets}
    attach_globals(source, family, argument, pending, candidate=current_pending)
    source["current_assault_removal_reference_inputs_v1"] = family
    return source


def known_empty_table(source: dict) -> None:
    table = source["current_daily_assault_table_v1"]
    table.update(groups=[], physical_controls=[], observed_occupied_group_count=0, physical_scan_ready=False)
    table["header"] = {key: None for key in table["header"]}
    table["header"].update(_state(False, "unused_empty_header"), occupied_count_raw_i32=0)
    source.pop("current_daily_assault_loss_inputs_v1", None)


class CurrentAssaultFirstRemovalContextServiceTests(unittest.TestCase):
    def test_empty_current_derived_first_receiver_and_independent_manager_context(self):
        outputs = {}

        def query(case_name, source):
            before = deepcopy(source)
            returned, driver = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"], {"current_strength": True, "full_monthly": False})
            item = returned["same_input_current_assault_first_removal_v1"][0]
            self.assertEqual(item["army_id"], source["army_id"])
            value = item["projection"]
            for key in ("actual_removal", "actual_cleanup", "actual_effects", "future_drain_ready", "next_tick_ready",
                        "full_ordered_removal_requests_ready", "full_army_lifecycle_ready", "full_daily_assault_ready",
                        "full_regular_refill_ready", "full_monthly_ready", "full_calendar_ready", "live"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_post_stage"])
            self.assertIsNone(value["actual_post_registry"])
            self.assertEqual(value["native_writes_executed"], 0)
            for scope in ("current_direct_top_helper", "conditional_standalone_transfer_then_first_top_helper"):
                self.assertFalse(value[scope]["actual_cleanup"])
                self.assertIsNone(value[scope]["actual_post_state"])
            outputs[case_name] = returned
            if destination := os.environ.get("XAR_ASSAULT_FIRST_REMOVAL_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return returned, value

        run = query

        source = removal_context_packet()
        returned, value = run("empty-observed-nonempty-derived-valid-fallback-distinct-helper", source)
        self.assertEqual(value["current_pending_selection"]["selection_branch"], "not_called")
        selected = value["conditional_release_pending_selection"]
        self.assertTrue(selected["selection_ready"])
        self.assertTrue(selected["first_removal_call_request_ready"])
        request = selected["first_removal_call_request"]
        self.assertEqual(request["raw_full_id_u32"], HIGH_RAW)
        self.assertEqual(request["passed_full_id_u32"], 77)
        self.assertTrue(request["passed_used_fallback"])
        self.assertEqual(request["sequence_index"], 0)
        self.assertEqual(len(selected["remaining_known_occurrences"]), 3)
        self.assertTrue(selected["post_first_removal_state_required"])
        helper = value["conditional_standalone_transfer_then_first_top_helper"]
        self.assertTrue(helper["conditional_manager_cleanup_ready"])
        self.assertEqual(helper["helper_resolution"]["selected_full_id_u32"], request["passed_full_id_u32"])
        self.assertNotEqual(helper["helper_object_identity"], helper["passed_object_identity"])
        self.assertFalse(helper["helper_same_passed_pointer"])
        self.assertEqual(helper["selected_bucket_removed_stored_indices"], [1, 3])
        self.assertEqual([entry["native_index"] for entry in helper["conditional_selected_bucket_rows_after"]], [0, 2, 4])
        self.assertEqual(helper["conditional_selected_bucket_rows_after"][0]["pointer_identity"], request["passed_object_identity"])
        lists = {entry["manager_offset"]: entry for entry in helper["id_list_projections"]}
        self.assertEqual(lists["50"]["conditional_ordered_army_ids_after"], [991, 77, 8])
        self.assertEqual(lists["80"]["conditional_ordered_army_ids_after"], [9, 5, 77])
        self.assertEqual(lists["98"]["conditional_ordered_army_ids_after"], [5, 6])
        self.assertEqual(lists["c8"]["conditional_ordered_army_ids_after"], [])
        self.assertEqual(lists["158"]["conditional_ordered_army_ids_after"], [77])
        self.assertEqual(lists["68"]["conditional_stage_entry_ordered_army_ids"], [])
        self.assertEqual(lists["68"]["stage_input_basis"], "explicit_post_transfer_source_queue_empty")
        self.assertEqual(helper["conditional_records_b0_after"], [[6, 0x80000000, 9, 10], [5, 2, 3, 4]])
        self.assertEqual(helper["records_b0_removed_count"], 3)
        self.assertEqual(helper["conditional_passed_army_identity_after_top_stage"]["full_id_u32"], 77)

        _, value = run("nonempty-current-invalid-prefix-unused-later-target", removal_context_packet(current_pending=True))
        current = value["current_pending_selection"]
        self.assertEqual([entry["sequence_index"] for entry in current["known_invalid_prefix"]], [0])
        self.assertEqual(current["first_removal_call_request"]["sequence_index"], 1)
        self.assertTrue(value["current_direct_top_helper"]["conditional_manager_cleanup_ready"])
        direct = {entry["manager_offset"]: entry for entry in value["current_direct_top_helper"]["id_list_projections"]}
        self.assertEqual(direct["68"]["conditional_stage_entry_ordered_army_ids"], [19, HIGH_STORED, 77, 77, 8])
        self.assertEqual(direct["68"]["conditional_ordered_army_ids_after"], [19, HIGH_STORED, 8, 77])
        transferred = {entry["manager_offset"]: entry for entry in value["conditional_standalone_transfer_then_first_top_helper"]["id_list_projections"]}
        self.assertEqual(transferred["68"]["observed_ordered_army_ids"], [19, HIGH_STORED, 77, 77, 8])
        self.assertEqual(transferred["68"]["conditional_ordered_army_ids_after"], [])

        _, value = run("first-valid-known-release-prefix-does-not-demand-unknown-tail", removal_context_packet(partial_next_group=True))
        selected = value["conditional_release_pending_selection"]
        self.assertFalse(selected["sequence_complete"])
        self.assertTrue(selected["selection_ready"])
        self.assertTrue(selected["remaining_unknown_tail"])
        self.assertTrue(value["conditional_standalone_transfer_then_first_top_helper"]["conditional_manager_cleanup_ready"])

        missing_bucket = removal_context_packet()
        target_row = missing_bucket["current_assault_removal_reference_inputs_v1"]["cleanup_targets"][0]
        target_row.update(_state(False, "actual_bucket_unreadable"), bucket_rows=None)
        _, value = run("missing-used-bucket-retains-independent-list-and-B0-effects", missing_bucket)
        self.assertTrue(value["conditional_release_pending_selection"]["first_removal_call_request_ready"])
        helper = value["conditional_standalone_transfer_then_first_top_helper"]
        self.assertFalse(helper["conditional_manager_cleanup_ready"])
        self.assertFalse(helper["selected_bucket_cleanup_ready"])
        self.assertTrue(helper["records_b0_cleanup_ready"])
        self.assertTrue(all(entry["conditional_ready"] for entry in helper["id_list_projections"]))

        missing_list = removal_context_packet()
        missing_list["current_assault_removal_reference_inputs_v1"]["manager_id_lists"][2]["ordered_army_ids"] = None
        _, value = run("missing-one-list-preserves-other-independent-families", missing_list)
        helper = value["conditional_standalone_transfer_then_first_top_helper"]
        self.assertTrue(helper["selected_bucket_cleanup_ready"])
        self.assertTrue(helper["records_b0_cleanup_ready"])
        self.assertFalse(helper["id_list_projections"][2]["conditional_ready"])
        self.assertTrue(helper["id_list_projections"][0]["conditional_ready"])

        empty_bucket = removal_context_packet()
        empty_bucket["current_assault_removal_reference_inputs_v1"]["cleanup_targets"][0].update(
            bucket_count_raw_i32=0, bucket_data_present=None, bucket_rows=[])
        _, value = run("known-empty-bucket-does-not-demand-pointer-array", empty_bucket)
        self.assertTrue(value["conditional_standalone_transfer_then_first_top_helper"]["conditional_manager_cleanup_ready"])
        self.assertEqual(value["conditional_standalone_transfer_then_first_top_helper"]["conditional_selected_bucket_rows_after"], [])

        _, value = run("signed-argument-DWORD-and-unsigned-bucket-phase", removal_context_packet(argument=0x80000001))
        helper = value["conditional_standalone_transfer_then_first_top_helper"]
        self.assertEqual(helper["argument_army_id_i32"], -2147483647)
        self.assertEqual(helper["selected_bucket_index"], 9)
        self.assertEqual(helper["records_b0_removed_count"], 3)

        unknown_first = removal_context_packet(current_pending=True)
        family = unknown_first["current_assault_removal_reference_inputs_v1"]
        first = family["reference_occurrences"][0]
        first.update(_state(False, "actual_magic_unreadable"), native_army_identity_valid=None,
                     army_magic_14_raw_u32=None, resolution=resolution(19, kind="army"))
        old_first = unknown_first["monthly_daily_queue_inputs_v1"]["initial_army_resolution_rows"][0]
        old_first.update(status="unavailable", unavailable_reason="actual_magic_unreadable",
                         resolved_army_id=19, used_fallback=False, army_magic_14_raw=None, native_army_identity_valid=None)
        unknown_first["monthly_daily_queue_inputs_v1"].update(status="unavailable", ready=False, unavailable_reason="actual_magic_unreadable")
        old_context = unknown_first["monthly_first_removal_cleanup_inputs_v1"]
        old_context.update(status="unavailable", ready=False, unavailable_reason="actual_magic_unreadable",
            candidate_found=None, candidate_stored_index=None, argument_army_id=None,
            cleanup_resolved_army_id=None, cleanup_used_fallback=None, selected_bucket_index=None, selected_bucket_rows=None)
        _, value = run("unknown-earliest-reference-stops-before-later-valid-fallback", unknown_first)
        self.assertFalse(value["current_pending_selection"]["selection_ready"])
        self.assertFalse(value["conditional_release_pending_selection"]["selection_ready"])
        self.assertEqual(value["current_pending_selection"]["missing_inputs"][0]["sequence_index"], 0)
        self.assertEqual(value["current_direct_top_helper"]["id_list_projections"], [])

        invalid_only = removal_context_packet()
        known_empty_table(invalid_only)
        observe_pending(invalid_only, [19])
        invalid_only["monthly_daily_queue_inputs_v1"].update(status="available", ready=True, unavailable_reason=None,
            initial_army_resolution_rows=[{"status": "available", "unavailable_reason": None,
                "stored_index": 0, "raw_army_reference_id": 19, "resolved_army_id": -1,
                "used_fallback": True, "army_magic_14_raw": MAGIC, "native_army_identity_valid": False}])
        family = invalid_only["current_assault_removal_reference_inputs_v1"]
        family.update(_state(False, "unused_global_context_unreadable"), observed_pending_ids_i32=[19],
            reference_occurrences=[reference(0, 19, 0xFFFFFFFF, pending_index=0, valid=False)],
            cleanup_targets=[], records_b0=None,
            manager_id_lists=[{"manager_offset": offset, "ordered_army_ids": None} for offset in OFFSETS])
        invalid_only.pop("monthly_first_removal_cleanup_inputs_v1")
        _, value = run("known-invalid-no-call-needs-no-unused-global-target-context", invalid_only)
        self.assertEqual(value["current_pending_selection"]["selection_branch"], "not_called")
        self.assertEqual(value["conditional_release_pending_selection"]["selection_branch"], "not_called")
        self.assertTrue(value["current_direct_top_helper"]["conditional_manager_cleanup_ready"])
        self.assertTrue(value["conditional_standalone_transfer_then_first_top_helper"]["conditional_manager_cleanup_ready"])

        missing_reference = removal_context_packet()
        missing_reference["current_assault_removal_reference_inputs_v1"]["reference_occurrences"] = []
        _, value = run("missing-used-group-reference-does-not-substitute-subject-Army", missing_reference)
        self.assertTrue(value["current_pending_selection"]["selection_ready"])
        self.assertFalse(value["conditional_release_pending_selection"]["selection_ready"])

        legacy = removal_context_packet()
        legacy["current_assault_removal_reference_inputs_v1"] = None
        _, value = run("legacy-optional-null-preserves-empty-current-but-derived-is-partial", legacy)
        self.assertTrue(value["current_pending_selection"]["selection_ready"])
        self.assertFalse(value["conditional_release_pending_selection"]["selection_ready"])

        empty = removal_context_packet()
        known_empty_table(empty)
        empty.pop("current_assault_removal_reference_inputs_v1")
        _, value = run("known-empty-current-and-derived-do-not-demand-new-unused-family", empty)
        self.assertTrue(value["current_direct_top_helper"]["conditional_manager_cleanup_ready"])
        self.assertTrue(value["conditional_standalone_transfer_then_first_top_helper"]["conditional_manager_cleanup_ready"])


if __name__ == "__main__":
    unittest.main()
