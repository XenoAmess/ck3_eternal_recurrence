"""One new whole-service compound; expected arithmetic was sealed before source.

Authoring status: FIRST_NOT_RUN. The round24 coherent freeze owns first execution.
Existing fixture constructors and MemoryRoute are reused; no old test method runs.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT / "src"))
sys.path.insert(0, str(_PROJECT / "tests" / "unit"))

from daily_assault_roster_admission_fixture import fnv, references, state
from pre_date_pending_update_fixture import arrg, same_roster_standalone_source, source
from test_scoped_ordered_refill_service import MemoryRoute, row as strength_row


_REG_A = 0x2B000001
_REG_SKIP = 0x2B000002
_THRESHOLD_NINE_TENTHS = 0x3F666666
_THRESHOLD_ONE_HALF = 0x3F000000
_GENERAL = ((1, 4, 1, (601,)), (2, 7, 1, (701, 701, 702)),
            (3, 6, 1, (801, 801)), (4, 1, 1, (901, 902, 901)))

# Column order is physical slot, control, full key, count, full IDs, changed.
# These literals mirror the independently presealed round24 service receipt.
_EXPECTED = {
    "fastshift": {
        "branches": ["fast_shift"], "before": [0], "after": [1], "remove": [False],
        "header": [7, 3, 5, 13, False], "placements": 1,
        "physical": [[1, 1, 4, 1, [601], False], [2, 2, 12, 1, [_REG_A], True],
                     [3, 2, 7, 3, [701, 701, 702], True]],
        "events": ["fast_shift"],
    },
    "general-two-swaps": {
        "branches": ["general_carried_collision"], "before": [0], "after": [1], "remove": [False],
        "header": [7, 5, 5, 13, False], "placements": 1,
        "physical": [[1, 1, 4, 1, [601], False], [2, 2, 12, 1, [_REG_A], True],
                     [3, 2, 7, 3, [701, 701, 702], True], [4, 2, 6, 2, [801, 801], True],
                     [5, 2, 1, 3, [901, 902, 901], True]],
        "events": ["carry_start", "lower_distance_swap", "lower_distance_swap", "carry_empty"],
        "swaps": [[3, 1, 2, False], [4, 1, 2, False]],
    },
    "initial-density-growth": {
        "branches": ["initial_growth"], "before": [0], "after": [1], "remove": [False],
        "header": [15, 5, 6, 22, True], "placements": 1,
        "physical": [[1, 1, 4, 1, [601], True], [2, 1, 7, 3, [701, 701, 702], True],
                     [3, 1, 6, 2, [801, 801], True], [4, 1, 1, 3, [901, 902, 901], True],
                     [9, 1, 12, 1, [_REG_A], True]],
        "events": ["growth", "direct_empty", "direct_empty", "direct_empty", "direct_empty", "direct_empty"],
        "growth": ["initial_growth", 4, 7, 4, 16, 15, 6, 23, 22],
        "rehash": [[1, 4, 1], [2, 7, 2], [3, 6, 3], [4, 1, 4]],
    },
    "carried-overflow-growth": {
        "branches": ["carried_growth"], "before": [0], "after": [1], "remove": [False],
        "header": [15, 4, 6, 22, True], "placements": 1,
        "physical": [[1, 1, 4, 1, [601], True], [2, 1, 7, 3, [701, 701, 702], True],
                     [9, 1, 12, 1, [_REG_A], True], [10, 1, 15, 2, [801, 801], True]],
        "events": ["carry_start", "carried_overflow_first_slot_exchange", "growth",
                   "direct_empty", "direct_empty", "direct_empty", "direct_empty"],
        "growth": ["carried_overflow", 4, 7, 3, 16, 15, 6, 23, 22],
        "rehash": [[1, 4, 1], [2, 7, 2], [3, 15, 10]], "first_slot_exchange": 2,
    },
    "repeated-new-army": {
        "branches": ["direct_empty", "evolving_existing_key"],
        "before": [0, 1], "after": [1, 2], "remove": [False, True],
        "header": [7, 1, 5, 13, False], "placements": 2,
        "physical": [[1, 1, 12, 2, [_REG_A, _REG_A], True]], "events": ["direct_empty"],
        "queue": [12], "skip": [1],
    },
    "native-empty-buffer": {
        "branches": ["initial_growth"], "before": [0], "after": [1], "remove": [False],
        "header": [7, 1, 5, 13, True], "placements": 1,
        "physical": [[1, 1, 12, 1, [_REG_A], True]], "events": ["growth", "direct_empty"],
        "growth": ["initial_growth", 3, 0, 0, 8, 7, 5, 14, 13], "rehash": [],
    },
    "missing-allocator-witness": {
        "branches": ["existing_key", None], "before": [1, None], "after": [2, None],
        "remove": [True, None], "ready": False, "counts_ready": False,
        "values_ready": False, "completed": 1,
        "reason": "pending_required_vector_transfer_unmatched_or_unread",
        "header": [7, 4, 5, 13, False], "placements": 1,
        "physical": [[1, 1, 4, 2, [601, _REG_A], True], [2, 1, 7, 3, None, False],
                     [3, 1, 6, 2, [801, 801], False], [4, 1, 1, 3, [901, 902, 901], False]],
        "events": [], "physical_values_ready": True, "queue": [4], "skip": [0],
    },
    "matched-witness-unread-ids": {
        "branches": ["existing_key", "general_carried_collision"],
        "before": [1, 0], "after": [2, 1], "remove": [True, False],
        "ready": False, "counts_ready": True, "values_ready": False, "completed": 2,
        "reason": "updated_pending_values_incomplete",
        "header": [7, 5, 5, 13, False], "placements": 2,
        "physical": [[1, 1, 4, 2, [601, _REG_A], True], [2, 2, 12, 1, [_REG_A], True],
                     [3, 2, 7, 3, None, True], [4, 2, 6, 2, [801, 801], True],
                     [5, 2, 1, 3, [901, 902, 901], True]],
        "events": ["carry_start", "lower_distance_swap", "lower_distance_swap", "carry_empty"],
        "physical_values_ready": False, "queue": [4], "skip": [0],
    },
    "new-frame-free-existing": {
        "branches": ["existing_key"], "before": [1], "after": [2], "remove": [True],
        "pending_values": [[611, _REG_A]], "queue": [12], "skip": [0],
    },
    "new-frame-free-direct": {
        "branches": ["direct_empty"], "before": [0], "after": [1], "remove": [False],
        "pending_values": [[_REG_A]],
    },
}

_SOURCE_ARITHMETIC = {
    "home_mask7": {"12": 1, "4": 1, "7": 2, "6": 3, "1": 4, "15": 2},
    "home_mask15": {"12": 9, "4": 1, "7": 2, "6": 3, "1": 4, "15": 10},
    "general_density": "binary32(5/7) <= binary32(0.9)",
    "density_growth": "binary32(5/7) > binary32(0.5); index4/capacity16/mask15/tail6/terminal22",
    "carried_overflow": "control2 equal -> carried3 > tail2 -> exchange first slot2 -> count3 old rehash -> insert12",
    "known_empty_growth": "distance1 > tail0; index3/capacity8/mask7/tail5/terminal13",
    "repeated_A": "selected placements2/new inserts1; Army44=2; append1: 0->1->2; remove False/True",
}


def _new_leaf(roster=(12,), *, mode="direct", pending_ids=()) -> dict:
    leaf = source(roster=roster, mode=mode, pending_ids=pending_ids,
                  branches=["current_zero", "state_not_one"], queue=())
    for occurrence in leaf["occurrences"]:
        occurrence["original_arrg_references"] = references([_REG_A, _REG_SKIP])
        occurrence["arrg_occurrences"] = [arrg(0, _REG_A), arrg(1, _REG_SKIP, "state_not_one")]
    return leaf


def _new_frame(specs, *, mask=7, tail=5, threshold=_THRESHOLD_NINE_TENTHS,
               native_empty=False) -> dict:
    """Construct the raw schema only, retaining every physical control slot."""
    occupied = {slot: (key, control, ids) for slot, key, control, ids in specs}
    terminal = mask + tail + 1
    records = []
    for slot in range(terminal + 1):
        key, control, ids = occupied.get(slot, (None, 255 if slot == terminal else 0, None))
        records.append({**state(True), "native_index": slot, "physical_slot_i64": slot,
            "control_raw_u8": control, "stored_hash_raw_u32": fnv(key) if key is not None else None,
            "key_raw_full_id_u32": key, "vector_capacity_raw_i32": len(ids) if ids is not None else None,
            "vector_allocator_identity": "native:9900000" if key is not None else None,
            "vector_allocator_matches_expected": True if key is not None else None,
            "references": references(list(ids)) if ids is not None else references()})
    return {**state(True), "schema_version": 1, "entries_identity": "native:7700000",
        "entries_present": True, "data_is_native_empty_buffer": native_empty,
        "map_count_raw_i32": len(specs), "mask_raw_i32": mask, "tail_raw_u8": tail,
        "threshold_bits_u32": threshold, "physical_control_extent_last_slot_i64": terminal,
        "physical_controls_complete": True, "rehash_prefix_complete": True,
        "rehash_nonzero_records_observed_i32": len(specs), "records": records}


def _framed_leaf(frame: dict, *, roster=(12,)) -> dict:
    leaf = _new_leaf(roster)
    leaf["pending_table_frame_v1"] = frame
    physical = {record["physical_slot_i64"]: record for record in frame["records"]}
    for occurrence in leaf["occurrences"]:
        target = occurrence["raw_full_id_u32"]
        home = fnv(target) & frame["mask_raw_i32"]
        probes, slot, distance, existing = [], home, 1, False
        while True:
            record = physical[slot]
            probes.append({"native_index": len(probes), "physical_slot_i64": slot,
                "distance_raw_u8": distance, "control_raw_u8": record["control_raw_u8"],
                "key_raw_full_id_u32": record["key_raw_full_id_u32"]})
            if record["control_raw_u8"] < distance:
                break
            if record["key_raw_full_id_u32"] == target:
                existing = True
                break
            slot, distance = slot + 1, (distance + 1) & 255
        occurrence["pending_setup"] = {**state(True), "entries_identity": frame["entries_identity"],
            "entries_present": True, "mask_raw_i32": frame["mask_raw_i32"],
            "target_army_full_id_u32": target, "hash_raw_u32": fnv(target), "home_slot_i64": home,
            "terminal_physical_slot_i64": slot, "probes": probes, "existing_key": existing,
            "existing_references": deepcopy(record["references"]) if existing else references(),
            "map_count_raw_i32": None if existing else frame["map_count_raw_i32"],
            "insertion_tail_raw_u8": None if existing else frame["tail_raw_u8"],
            "insertion_threshold_bits_u32": None if existing else frame["threshold_bits_u32"]}
    return leaf


def _unread_resident_frame(*, allocator_witness: bool) -> dict:
    frame = _new_frame(_GENERAL)
    resident = frame["records"][2]
    reason = "pending_vector_references_unread" if allocator_witness else "pending_vector_allocator_unread"
    resident.update(state(False, reason, partial=True))
    resident["references"] = {**state(False, "raw_vector_data_unread", partial=True),
        "references_ready": False, "count_raw_i32": 3, "data_identity": None,
        "data_present": None, "occurrences": [], "observed_occurrence_count": 0}
    if not allocator_witness:
        resident.update(vector_allocator_identity=None, vector_allocator_matches_expected=None)
    frame.update(state(False, "pending_table_frame_partial", partial=True), rehash_prefix_complete=False)
    return frame


def _new_case_sources() -> dict[str, dict]:
    return {
        "fastshift": _framed_leaf(_new_frame(_GENERAL[:2])),
        "general-two-swaps": _framed_leaf(_new_frame(_GENERAL)),
        "initial-density-growth": _framed_leaf(_new_frame(_GENERAL, threshold=_THRESHOLD_ONE_HALF)),
        "carried-overflow-growth": _framed_leaf(_new_frame(
            ((1, 4, 1, (601,)), (2, 7, 1, (701, 701, 702)), (3, 15, 2, (801, 801))), tail=2)),
        "repeated-new-army": _framed_leaf(_new_frame(()), roster=(12, 12)),
        "native-empty-buffer": _framed_leaf(_new_frame((), mask=0, tail=0, native_empty=True)),
        "missing-allocator-witness": _framed_leaf(_unread_resident_frame(allocator_witness=False), roster=(4, 12)),
        "matched-witness-unread-ids": _framed_leaf(_unread_resident_frame(allocator_witness=True), roster=(4, 12)),
        "new-frame-free-existing": _new_leaf(mode="existing", pending_ids=(611,)),
        "new-frame-free-direct": _new_leaf(mode="direct"),
    }


class ArmyPreDatePendingCarryGrowthService12003Tests(unittest.TestCase):
    def test_complete_service_pending_physical_carry_growth_and_count_independence(self):
        cases = _new_case_sources()
        requested = os.environ.get("XAR_PENDING_CARRY_GROWTH_CASES")
        names = [name.strip() for name in requested.split(",") if name.strip()] if requested else list(cases)
        self.assertTrue(names, "case filtering must select at least one new case")
        self.assertEqual(len(names), len(set(names)), "new case retry must not repeat a selected case")
        self.assertFalse(set(names) - set(cases), "case filter names must belong to this new compound")
        output = os.environ.get("XAR_PENDING_CARRY_GROWTH_OUTPUT_DIR")
        output_dir = Path(output) if output else None
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
        receipt = {"topic": "round24/current-pending-carry-growth/service-compound",
                   "configured_case_count": 10, "selected_cases": names,
                   "source_arithmetic": _SOURCE_ARITHMETIC, "cases": {}}
        for name in names:
            with self.subTest(case=name):
                leaf, expected = cases[name], _EXPECTED[name]
                # Observed base aggregates are raw inputs, never replacement projections.
                payload = strength_row(maximum=120)
                payload["ai_base_power_raw"] = 300000
                payload["current_pre_date_pending_update_inputs_v1"] = leaf
                payload["current_daily_assault_roster_admission_v1"] = same_roster_standalone_source(leaf)
                before = deepcopy(payload)
                service = MemoryRoute(payload)
                returned = service.query_army_strengths([11], expected_revision=42)
                receipt["cases"][name] = {"raw_whole_strength_source": before,
                    "expected_source_arithmetic": expected, "actual_full_service": returned}
                if output_dir is not None:
                    (output_dir / (name + "-service.json")).write_text(
                        json.dumps(receipt["cases"][name], indent=2) + "\n", encoding="utf-8")
                self.assertEqual(payload, before)
                self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
                self.assertEqual(returned["status"], "available")
                self.assertEqual(returned["scope_status"], "available")
                self.assertEqual(returned["native_readiness"], {"current_strength": True, "full_monthly": False})
                self.assertEqual(returned["source"]["revision"], 42)
                self.assertEqual(returned["source"]["native_revision"], 7)
                actual_row = returned["army_strengths"][0]
                self.assertEqual(actual_row["current_soldiers"], 160)
                self.assertEqual(actual_row["maximum_soldiers"], 240)
                self.assertEqual(actual_row["ai_base_power_raw"], 300000)
                self.assertEqual(actual_row["current_supply_change_monthly_raw"], 700000)
                normalized_leaf = actual_row["current_pre_date_pending_update_inputs_v1"]
                self.assertEqual(normalized_leaf["occurrences"], leaf["occurrences"])
                for occurrence in normalized_leaf["occurrences"]:
                    self.assertEqual(occurrence["original_arrg_references"]["count_raw_i32"], 2)
                    self.assertEqual([item["append_to_pending"] for item in occurrence["arrg_occurrences"]], [True, False])
                projection = actual_row["same_input_conditional_current_pre_date_pending_update_v1"]
                for flag in ("actual_pre_date_callback_ready", "actual_tomorrow_roster_ready",
                             "full_daily_assault_ready", "full_monthly_ready"):
                    self.assertFalse(normalized_leaf[flag])
                    self.assertFalse(projection[flag])
                self.assertEqual(projection["native_mutator_invocations"], 0)
                self.assertEqual(projection["native_writes"], 0)
                self.assertTrue(projection["fixed_captured_nonphysical_context"])
                self.assertEqual(projection["ready"], expected.get("ready", True))
                self.assertEqual(projection["pending_counts_and_removal_requests_ready"], expected.get("counts_ready", True))
                self.assertEqual(projection["updated_pending_values_ready"], expected.get("values_ready", True))
                self.assertEqual(projection["completed_original_occurrence_count"], expected.get("completed", len(leaf["occurrences"])))
                self.assertEqual(projection["unavailable_reason"], expected.get("reason"))
                decisions = projection["occurrences"]
                self.assertEqual([item["pending_setup_branch"] for item in decisions], expected["branches"])
                self.assertEqual([item["pending_count_before"] for item in decisions], expected["before"])
                self.assertEqual([item["pending_count_after"] for item in decisions], expected["after"])
                self.assertEqual([item["removal_requested"] for item in decisions], expected["remove"])
                self.assertEqual(projection["conditional_removal_queue_full_ids_u32"], expected.get("queue", []))
                self.assertEqual(projection["conditional_skip_2a99b40_occurrence_indices"], expected.get("skip", []))
                self.assertEqual([item["army_full_id_u32"] for item in projection["removal_append_requests"]], expected.get("queue", []))
                table = projection["conditional_pending_table_v1"]
                if "header" not in expected:
                    self.assertIsNone(table)
                    self.assertIsNone(normalized_leaf["pending_table_frame_v1"])
                    self.assertNotIn("pending_table_frame_v1", leaf)
                    self.assertEqual([item["conditional_full_ids_u32"] for item in projection["pending_lists"]], expected["pending_values"])
                    continue
                self.assertEqual(normalized_leaf["pending_table_frame_v1"], leaf["pending_table_frame_v1"])
                self.assertEqual([table["mask_raw_i32"], table["conditional_map_count_raw_i32"],
                                  table["tail_raw_u8"], table["terminal_slot_i64"],
                                  table["sparse_generated_image"]], expected["header"])
                self.assertEqual(table["threshold_bits_u32"], leaf["pending_table_frame_v1"]["threshold_bits_u32"])
                self.assertEqual(table["placement_invocations"], expected["placements"])
                self.assertEqual(table["changed_physical_values_ready"], expected.get("physical_values_ready", True))
                self.assertFalse(table["actual_native_after_ready"])
                self.assertEqual(table["native_writes"], 0)
                self.assertEqual(table["native_mutator_invocations"], 0)
                occupied = [item for item in table["physical_records"] if item["key_raw_full_id_u32"] is not None]
                self.assertEqual([[item["physical_slot_i64"], item["control_raw_u8"],
                                   item["key_raw_full_id_u32"], item["conditional_count_raw_i32"],
                                   item["conditional_full_ids_u32"], item["physically_changed"]]
                                  for item in occupied], expected["physical"])
                for item in occupied:
                    self.assertEqual(item["stored_hash_raw_u32"], fnv(item["key_raw_full_id_u32"]))
                self.assertEqual([item["kind"] for item in table["events"]], expected["events"])
                if table["sparse_generated_image"]:
                    self.assertEqual(table["default_control_raw_u8"], 0)
                    self.assertEqual(table["terminal_control_raw_u8"], 255)
                else:
                    terminal = next(item for item in table["physical_records"]
                                    if item["physical_slot_i64"] == table["terminal_slot_i64"])
                    self.assertEqual(terminal["control_raw_u8"], 255)
                if "swaps" in expected:
                    swaps = [item for item in table["events"] if item["kind"] == "lower_distance_swap"]
                    self.assertEqual([[item["slot"], item["reloaded_control"],
                                       item["carried_control_after"], item["tail_test"]] for item in swaps], expected["swaps"])
                if "growth" in expected:
                    growth = [item for item in table["events"] if item["kind"] == "growth"]
                    self.assertEqual(len(growth), 1)
                    event = growth[0]
                    self.assertEqual([event["trigger"], event["index"], event["mask_before"],
                                      event["count_before"], event["capacity"], event["mask_after"],
                                      event["tail_after"], event["allocated_records"], event["terminal_slot"]], expected["growth"])
                    self.assertEqual([[item["physical_slot_i64"], item["key_raw_full_id_u32"],
                                       item["selected_slot_i64"]] for item in event["old_rehash_occurrences"]], expected["rehash"])
                    self.assertTrue(all(item["inserted"] for item in event["old_rehash_occurrences"]))
                if "first_slot_exchange" in expected:
                    exchanges = [item["slot"] for item in table["events"]
                                 if item["kind"] == "carried_overflow_first_slot_exchange"]
                    self.assertEqual(exchanges, [expected["first_slot_exchange"]])
                pending = projection["pending_lists"]
                if name == "missing-allocator-witness":
                    self.assertEqual([(item["army_full_id_u32"], item["conditional_count"],
                                       item["conditional_full_ids_u32"]) for item in pending], [(4, 2, [601, _REG_A])])
                    self.assertFalse(decisions[1]["ready"])
                    self.assertEqual(decisions[1]["arrg_selection_ledger"], [])
                elif name == "matched-witness-unread-ids":
                    self.assertTrue(all(item["ready"] for item in decisions))
                    self.assertTrue(all(item["values_ready"] for item in pending))
                    self.assertEqual([(item["army_full_id_u32"], item["conditional_count"],
                                       item["conditional_full_ids_u32"]) for item in pending],
                                     [(4, 2, [601, _REG_A]), (12, 1, [_REG_A])])
                else:
                    copies = 2 if name == "repeated-new-army" else 1
                    self.assertEqual([(item["army_full_id_u32"], item["initial_count"],
                                       item["conditional_count"], item["conditional_full_ids_u32"])
                                      for item in pending], [(12, 0, copies, [_REG_A] * copies)])
        if output_dir is not None:
            (output_dir / "service-compound-receipt.json").write_text(
                json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
