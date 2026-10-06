"""One complete-service compound for the initial current detach mapper seed."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_current_assault_first_removal_context_service import (
    HIGH_RAW, removal_context_packet, selected_resolution, unknown_resolution,
    query_with_fake_driver,
)
from test_current_daily_assault_table_service import _state

REGI_MAGIC = 0x52656769
FALLBACK_REGI = "regi:fallback:actual"
FAMILY = "current_candidate_detachment_mapper_inputs_v1"
SERVICE_FIELD = "same_input_current_candidate_detachment_mapper_v1"


def physical_count(index: int, identity: str, base: int, active: list[tuple[int, int, int | None]]) -> dict:
    chunks = [{"physical_index": ordinal, "maximum_00_raw_i32": 0,
        "current_04_raw_i32": None, "state_18_raw_i32": None} for ordinal in range(7)]
    for ordinal, (maximum, current, state) in enumerate(active):
        chunks[ordinal].update(maximum_00_raw_i32=maximum, current_04_raw_i32=current,
                               state_18_raw_i32=state)
    return {**_state(True), "native_index": index, "regi_identity": identity,
            "count_base_128_raw_i32": base, "chunks": chunks}


def mapper(index: int, arrg_identity: str, kind: int, selected: int | None,
           *, data_count: int | None = 1, count_index: int | None = None,
           selected_valid: bool = True, fallback: bool = False, state: int = 4) -> dict:
    requested = 0xFFFFFFFF if data_count == 0 else selected
    resolution = (selected_resolution(requested, selected,
        FALLBACK_REGI if selected == 0xFFFFFFFF else f"regi:{selected}",
        fallback=selected == 0xFFFFFFFF) if kind in (1, 4) else None)
    returned = FALLBACK_REGI if fallback else f"regi:{selected}"
    return {**_state(True), "native_index": index, "arrg_identity": arrg_identity,
        "kind_14c_raw_i32": kind, "data_count_raw_i32": data_count,
        "first_data_record_identity": None if data_count in (None, 0) else f"DATA:{arrg_identity}:0",
        "first_regi_full_id_u32": None if data_count in (None, 0) else selected,
        "selected_regi_resolution": resolution,
        "selected_regi_magic_14_raw_u32": (REGI_MAGIC if selected_valid else 0) if kind in (1, 4) else None,
        "selected_regi_identity_valid": selected_valid if kind in (1, 4) else None,
        "count_input_index": count_index, "return_selection_ready": True,
        "return_selection": "native_fallback" if fallback else "selected_regi",
        "fallback_regi_identity": FALLBACK_REGI if fallback else None,
        "returned_regi_identity": returned,
        # The caller only reads returned138; these extra identity scalars
        # deliberately remain absent for the valid selected branch too.
        "returned_regi_full_id_u32": 0xFFFFFFFF if fallback else None,
        "returned_regi_magic_14_raw_u32": 0 if fallback else None,
        "returned_state_138_raw_i32": state,
        "return_basis": "source2A977A0_from_same_capture_raw_operands"}


def candidate_mapper_packet() -> dict:
    source = removal_context_packet(current_pending=True)
    mappings = [
        mapper(0, "arrg:fallback:actual", 4, 601, data_count=-2),
        mapper(1, "arrg:101", 1, 602, count_index=0, state=2),
        mapper(2, "arrg:102", 1, 603, count_index=1, fallback=True),
        mapper(3, "arrg:103", 9, None, data_count=None, fallback=True),
        mapper(4, "arrg:104", 1, 0xFFFFFFFF, data_count=0, selected_valid=False, fallback=True),
        mapper(5, "arrg:105", 4, 606, selected_valid=False, fallback=True),
        mapper(6, "arrg:106", 1, 607, count_index=2, state=0),
        mapper(7, "arrg:107", 1, 602, count_index=0, state=2),
    ]
    ordered = [(0xFFFFFFFF, 0), (101, 1), (101, 1), (HIGH_RAW, 0),
               (102, 2), (103, 3), (104, 4), (105, 5), (106, 6), (107, 7)]
    occurrences = []
    for ordinal, (requested, mapper_index) in enumerate(ordered):
        identity = mappings[mapper_index]["arrg_identity"]
        fallback = mapper_index == 0
        actual = 77 if fallback else requested
        occurrences.append({**_state(True), "native_index": ordinal,
            "raw_full_id_u32": requested, "mapper_index": mapper_index,
            "resolution": selected_resolution(requested, actual, identity, fallback=fallback)})
    source[FAMILY] = {"schema_version": 1,
        "source": "native_current_candidate_detachment_mapper_inputs",
        "stage": "observed_current_first_candidate_mapper_seed", **_state(True),
        "selection_ready": True, "selection_branch": "first_valid_current_receiver",
        "candidate_reference_native_index": 1, "candidate_pending_native_index": 1,
        "candidate_raw_full_id_u32": HIGH_RAW, "candidate_actual_full_id_u32": 77,
        "candidate_army_identity": "army:fallback:77",
        "roster_count_raw_i32": len(occurrences), "roster_data_present": True,
        "roster_data_identity": "Army77:38:raw-buffer", "roster_ready": True,
        "occurrences": occurrences, "mappers": mappings,
        "count_inputs": [
            physical_count(0, "regi:602", 2147483647, [(7, 10, None)]),
            physical_count(1, "regi:603", 8, []),
            physical_count(2, "regi:607", -3, [(9, 0, 3), (4, -3, None)]),
        ]}
    return source


def single_mapper_packet(index: int) -> dict:
    source = candidate_mapper_packet()
    leaf = source[FAMILY]
    selected = deepcopy(leaf["mappers"][index])
    selected["native_index"] = 0
    original = next(item for item in leaf["occurrences"] if item["mapper_index"] == index)
    occurrence = deepcopy(original)
    occurrence.update(native_index=0, mapper_index=0)
    leaf.update(roster_count_raw_i32=1, occurrences=[occurrence], mappers=[selected], count_inputs=[])
    return source


class CurrentCandidateDetachmentMapperServiceTests(unittest.TestCase):
    def test_current_candidate_whole_roster_shared_counts_and_branch_partials(self):
        outputs = {}

        def query(name, source):
            before = deepcopy(source)
            returned, driver = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"], {"current_strength": True, "full_monthly": False})
            entry = returned[SERVICE_FIELD][0]
            self.assertEqual(entry["army_id"], source["army_id"])
            value = entry["projection"]
            self.assertEqual(value["input_basis"], "initial_current_first_candidate_seed_only")
            self.assertEqual(value["subject_army_id"], source["army_id"])
            for field in ("actual_effects", "actual_detachment", "future_drain_ready",
                          "full_army_lifecycle_ready", "full_monthly_ready", "full_calendar_ready", "live"):
                self.assertFalse(value[field])
            self.assertIsNone(value["actual_post_stage"])
            self.assertEqual(value["native_writes_executed"], 0)
            outputs[name] = returned
            if destination := os.environ.get("XAR_CURRENT_CANDIDATE_MAPPER_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return value

        source = candidate_mapper_packet()
        value = query("whole-raw-roster-repeats-fallback-shared-count-wrap", source)
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertEqual(value["candidate_pending_native_index"], 1)
        self.assertEqual(value["candidate_raw_full_id_u32"], HIGH_RAW)
        self.assertEqual(value["candidate_actual_full_id_u32"], 77)
        self.assertEqual([item["raw_full_id_u32"] for item in value["occurrences"]],
                         [0xFFFFFFFF, 101, 101, HIGH_RAW, 102, 103, 104, 105, 106, 107])
        self.assertEqual(len(value["mapper_results"]), 8)
        self.assertEqual(len(value["count_results"]), 3)
        self.assertEqual([item["mapper_index"] for item in value["occurrences"]],
                         [0, 1, 1, 0, 2, 3, 4, 5, 6, 7])
        self.assertEqual([item["signed_count_i32"] for item in value["count_results"]],
                         [-2147483646, 8, -10])
        self.assertEqual([item["return_selection"] for item in value["mapper_results"]],
                         ["selected_regi", "selected_regi", "native_fallback", "native_fallback",
                          "native_fallback", "native_fallback", "selected_regi", "selected_regi"])
        self.assertEqual(value["mapper_results"][0]["source_requested_regi_full_id_u32"], 601)
        self.assertEqual(value["mapper_results"][0]["data_count_raw_i32"], -2)
        self.assertFalse(value["mapper_results"][0]["count_demanded"])
        self.assertEqual(value["mapper_results"][4]["source_requested_regi_full_id_u32"], 0xFFFFFFFF)
        self.assertFalse(value["mapper_results"][4]["count_demanded"])
        self.assertEqual(value["mapper_results"][2]["returned_regi_identity"], FALLBACK_REGI)
        self.assertEqual(value["mapper_results"][2]["observed_returned_regi_full_id_u32"], 0xFFFFFFFF)
        self.assertTrue(value["mapper_results"][2]["caller_state_ready"])
        self.assertTrue(value["mapper_results"][2]["state4_branch_admitted"])
        self.assertEqual(value["mapper_results"][6]["returned_regi_identity"], "regi:607")
        self.assertEqual(value["mapper_results"][1]["count_input_index"], value["mapper_results"][7]["count_input_index"])

        kind4 = single_mapper_packet(0)
        value = query("kind4-negative-DATA-count-no-unused-seven-count-or-fallback", kind4)
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertEqual(value["count_results"], [])
        self.assertEqual(value["mapper_results"][0]["return_selection"], "selected_regi")

        unrelated = single_mapper_packet(3)
        unrelated[FAMILY]["mappers"][0].update(selected_regi_magic_14_raw_u32=None,
            returned_regi_full_id_u32=None, returned_regi_magic_14_raw_u32=None)
        value = query("unrelated-kind-invalid-fallback-state-no-DATA-or-identity-scalar-gate", unrelated)
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertEqual(value["count_results"], [])
        self.assertTrue(value["mapper_results"][0]["state4_branch_admitted"])

        value = query("zero-DATA-count-sentinel-resolution-no-first-record-or-count", single_mapper_packet(4))
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertEqual(value["mapper_results"][0]["source_requested_regi_full_id_u32"], 0xFFFFFFFF)

        value = query("invalid-selected-Regi-kind4-falls-back-without-count", single_mapper_packet(5))
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertFalse(value["mapper_results"][0]["selected_regi_identity_valid"])

        partial = candidate_mapper_packet()
        partial[FAMILY]["count_inputs"][0].update(_state(False, "used_current_unreadable"))
        partial[FAMILY]["count_inputs"][0]["chunks"][0]["current_04_raw_i32"] = None
        partial[FAMILY].update(_state(False, "used_current_unreadable"))
        for index in (1, 7):
            partial[FAMILY]["mappers"][index].update(_state(False, "used_current_unreadable"),
                return_selection_ready=False, return_selection=None,
                returned_regi_identity=None, returned_state_138_raw_i32=None)
        value = query("missing-used-physical-count-preserves-independent-mappers", partial)
        self.assertFalse(value["initial_current_seed_ready"])
        self.assertTrue(value["roster_ready"])
        self.assertFalse(value["occurrences"][1]["preview_ready"])
        self.assertFalse(value["occurrences"][2]["preview_ready"])
        self.assertFalse(value["occurrences"][9]["preview_ready"])
        self.assertTrue(value["occurrences"][0]["preview_ready"])
        self.assertTrue(value["occurrences"][4]["preview_ready"])
        self.assertFalse(value["count_results"][0]["count_ready"])
        self.assertTrue(value["count_results"][1]["count_ready"])

        state_partial = candidate_mapper_packet()
        state_partial[FAMILY]["mappers"][0].update(_state(False, "returned138_unreadable"), returned_state_138_raw_i32=None)
        state_partial[FAMILY].update(_state(False, "returned138_unreadable"))
        value = query("return-selection-ready-caller-state-partial", state_partial)
        mapping = value["mapper_results"][0]
        self.assertTrue(mapping["return_selection_ready"])
        self.assertFalse(mapping["caller_state_ready"])
        self.assertIsNone(mapping["state4_branch_admitted"])
        self.assertTrue(value["occurrences"][1]["preview_ready"])

        missing_fallback = candidate_mapper_packet()
        missing_fallback[FAMILY]["mappers"][2].update(_state(False, "actual_fallback_pointer_unreadable"),
            fallback_regi_identity=None, returned_regi_identity=None, returned_state_138_raw_i32=None,
            return_selection_ready=False, return_selection=None)
        missing_fallback[FAMILY].update(_state(False, "actual_fallback_pointer_unreadable"))
        value = query("positive-count-demands-actual-fallback-identity-only-on-selected-branch", missing_fallback)
        self.assertTrue(value["mapper_results"][2]["return_branch_ready"])
        self.assertFalse(value["mapper_results"][2]["return_selection_ready"])
        self.assertTrue(value["mapper_results"][0]["return_selection_ready"])

        first_missing = candidate_mapper_packet()
        first_missing[FAMILY]["mappers"][0].update(_state(False, "first_record8_unreadable"),
            first_regi_full_id_u32=None, selected_regi_resolution=None,
            return_selection_ready=False, return_selection=None,
            returned_regi_identity=None, returned_state_138_raw_i32=None)
        first_missing[FAMILY].update(_state(False, "first_record8_unreadable"))
        value = query("negative-nonzero-DATA-count-demands-first-record8", first_missing)
        self.assertFalse(value["occurrences"][0]["preview_ready"])
        self.assertFalse(value["occurrences"][3]["preview_ready"])
        self.assertIn("first_data_record_regi_id_8_for_nonzero_count", value["mapper_results"][0]["missing_inputs"])
        self.assertTrue(value["occurrences"][1]["preview_ready"])

        zero_current = candidate_mapper_packet()
        chunk = zero_current[FAMILY]["count_inputs"][2]["chunks"][0]
        chunk["state_18_raw_i32"] = None
        zero_current[FAMILY]["count_inputs"][2].update(_state(False, "used_zero_current_state_unreadable"))
        zero_current[FAMILY].update(_state(False, "used_zero_current_state_unreadable"))
        zero_current[FAMILY]["mappers"][6].update(_state(False, "used_zero_current_state_unreadable"),
            return_selection_ready=False, return_selection=None,
            returned_regi_identity=None, returned_state_138_raw_i32=None)
        value = query("zero-current-nonzero-maximum-demands-state", zero_current)
        self.assertFalse(value["mapper_results"][6]["return_selection_ready"])
        self.assertTrue(value["mapper_results"][1]["return_selection_ready"])

        missing_raw = candidate_mapper_packet()
        missing_raw[FAMILY]["occurrences"][0].update(_state(False, "actual_roster_DWORD_unreadable"),
            raw_full_id_u32=None, mapper_index=None,
            resolution={**unknown_resolution(0), "requested_full_id_u32": None})
        missing_raw[FAMILY].update(_state(False, "actual_roster_DWORD_unreadable"), roster_ready=False)
        value = query("partial-roster-DWORD-does-not-substitute-legacy-strength-list", missing_raw)
        self.assertFalse(value["roster_ready"])
        self.assertIsNone(value["occurrences"][0]["raw_full_id_u32"])
        self.assertTrue(value["occurrences"][3]["preview_ready"])

        for count, label in ((0, "zero-roster-count"), (-3, "negative-raw-roster-count")):
            empty = candidate_mapper_packet()
            empty[FAMILY].update(roster_count_raw_i32=count, occurrences=[], mappers=[], count_inputs=[])
            value = query(label, empty)
            self.assertTrue(value["initial_current_seed_ready"])
            self.assertEqual(value["roster_count_raw_i32"], count)
            self.assertEqual(value["occurrences"], [])

        no_call = removal_context_packet()
        no_call[FAMILY] = deepcopy(candidate_mapper_packet()[FAMILY])
        leaf = no_call[FAMILY]
        leaf.update(selection_branch="not_called", candidate_reference_native_index=None,
            candidate_pending_native_index=None, candidate_raw_full_id_u32=None,
            candidate_actual_full_id_u32=None, candidate_army_identity=None,
            roster_count_raw_i32=None, roster_data_present=None, roster_data_identity=None,
            occurrences=[], mappers=[], count_inputs=[])
        value = query("known-current-no-candidate-does-not-demand-unused-roster", no_call)
        self.assertTrue(value["initial_current_seed_ready"])
        self.assertEqual(value["selection_branch"], "not_called")

        unknown = candidate_mapper_packet()
        reason = "earliest_current_pending_resolution_unavailable"
        pending = unknown["monthly_daily_queue_inputs_v1"]
        pending.update(status="unavailable", ready=False, unavailable_reason=reason)
        pending["initial_army_resolution_rows"][0].update(status="unavailable", unavailable_reason=reason,
            resolved_army_id=19, used_fallback=False, army_magic_14_raw=None, native_army_identity_valid=None)
        references = unknown["current_assault_removal_reference_inputs_v1"]
        references.update(_state(False, reason))
        references["reference_occurrences"][0].update(_state(False, reason),
            army_magic_14_raw_u32=None, native_army_identity_valid=None,
            resolution=selected_resolution(19, 19, "army:19", fallback=False))
        cleanup = unknown["monthly_first_removal_cleanup_inputs_v1"]
        cleanup.update(status="unavailable", ready=False, unavailable_reason=reason,
            candidate_found=None, candidate_stored_index=None, argument_army_id=None,
            cleanup_resolved_army_id=None, cleanup_used_fallback=None,
            selected_bucket_index=None, selected_bucket_rows=None)
        unknown[FAMILY].update(_state(False, "earliest_current_pending_resolution_unavailable"),
            selection_ready=False, selection_branch=None, roster_ready=False,
            roster_count_raw_i32=None, occurrences=[], mappers=[], count_inputs=[])
        value = query("unknown-initial-current-candidate-preserves-unavailable", unknown)
        self.assertFalse(value["initial_current_seed_ready"])
        self.assertEqual(value["occurrences"], [])

        for nullable in (False, True):
            legacy = candidate_mapper_packet()
            if nullable:
                legacy[FAMILY] = None
            else:
                del legacy[FAMILY]
            value = query("optional-null" if nullable else "legacy-absent", legacy)
            self.assertFalse(value["initial_current_seed_ready"])
            self.assertEqual(value["missing_inputs"], [FAMILY])


if __name__ == "__main__":
    unittest.main()
