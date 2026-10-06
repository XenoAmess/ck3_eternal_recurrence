"""ONE registered whole-service compound. Authoring status: FIRST_NOTRUN.

SDK registration and backend data are fixtures; the production registered
callable, service, whole Army normalizer and DATA builder remain real.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT / "src"))
sys.path.insert(0, str(_PROJECT / "tests" / "unit"))

from xar_autoplayer.bridge.mcp_server import create_server
from test_scoped_ordered_refill_service import row as strength_row

_FAMILY = "current_detachment_data_inputs_v1"
_SERVICE = "same_input_current_detachment_data_prefix_v1"
_DATE = 0x0000009B000007D0
_GREATER = 0x000000A0000007E8
_SMALLER = 0x000000A0FFFFFFF0
_SENTINEL = 0xFFFFFFFF029C77F8 - (1 << 64)
_IMAGE = 0x140000000
_VTABLE = _IMAGE + 0x44DEFA8
_CALLBACK = _IMAGE + 0x8863D0
_REGI = 0x52656769
_PROV = 0x50726F76
_INVALID = 0xFFFFFFFF


def _id(value: int) -> str:
    return f"native:{value}"


def _state(ready: bool = True, reason: str | None = None) -> dict:
    return {"status": "available" if ready else "unavailable", "ready": ready,
            "unavailable_reason": reason}


def _resolution(requested: int | None, address: int | None, *, fallback=False, actual=None) -> dict:
    ready = address is not None
    actual = requested if actual is None else actual
    return {**_state(ready), "requested_full_id_u32": requested,
        "registry_loaded": True if ready else None, "registry_capacity_u32": 100000 if ready else None,
        "registry_index_u32": requested & 0xFFFFFF if requested is not None else None,
        "indexed_identity": None if fallback or not ready else _id(address),
        "indexed_full_id_u32": None if fallback or not ready else requested,
        "selection": ("native_fallback" if fallback else "registry_full_id") if ready else None,
        "used_fallback": fallback if ready else None, "object_identity": _id(address) if ready else None,
        "selected_full_id_u32": actual if ready else None}


def _association(requested: int, count: int) -> dict:
    offset = requested & 255
    return {**_state(), "requested_full_id_u32": requested,
        "arrg_resolution": _resolution(requested, 0x800000 + offset * 0x100,
            fallback=requested == _INVALID, actual=77 if requested == _INVALID else requested),
        "army_full_id_140_u32": 12, "army_resolution": _resolution(12, 0xA00000),
        "unit_full_id_124_u32": 11, "unit_resolution": _resolution(11, 0xB00000 + offset * 0x100),
        "character_full_id_174_u32": 29829, "character_resolution": _resolution(29829, 0xC00000),
        "context_pointer_identity": _id(0xD00318), "context_count_0c_raw_u32": count & _INVALID}


def _owner(requested: int, *, origin_valid=True) -> dict:
    return {**_state(), "requested_full_id_u32": requested,
        "resolution": _resolution(requested, 0xE00000 + (requested & 255) * 0x100),
        "state_138_raw_i32": 0, "definition_identity": _id(0xF00000), "definition_magic_38_raw_u32": 0,
        "origin_identity": _id(0x910000 + (requested & 255) * 0x100),
        "origin_magic_85c_raw_u32": _PROV if origin_valid else 0}


def _date(association: int, owner: int, output: int | None, *, origin_valid=True, capital_valid=False) -> dict:
    return {**_state(output is not None), "association_full_id_u32": association, "owner_full_id_u32": owner,
        "unit_identity": _association(association, 1)["unit_resolution"]["object_identity"],
        "source_origin_identity": _owner(owner)["origin_identity"],
        "source_origin_magic_85c_raw_u32": _PROV if origin_valid else 0,
        "capital_origin_identity": _id(0x940000),
        "capital_origin_magic_85c_raw_u32": _PROV if capital_valid else 0,
        "output_date_raw64": output, "basis": "current_input_native2C54340_or_equal_entry_copy"}


def _chunk(index: int, address: int, maximum: int, current: int, owner: int, ordinal: int,
           association: int, *, date=0x1111222200000001) -> dict:
    return {**_state(), "native_index": index, "chunk_identity": _id(address),
        "maximum_00_raw_i32": maximum, "current_04_raw_i32": current, "owner_08_raw_u32": owner,
        "ordinal_0c_raw_i32": ordinal, "association_10_raw_u32": association,
        "flag_14_raw_u8": 1, "date_1c_raw64": date}


def _data(index: int, physical: int | None, ordinal: int, chunk_index: int | None,
          *, fallback=False, invalid=False) -> dict:
    requested = 0xAA000003 if fallback else 0x01000001 + index
    selected = (physical - 0x18 - 0x24 * ordinal) if physical is not None else 0x203000
    return {**_state(), "native_index": index, "record_identity": _id(0x100000 + 16 * index),
        "raw_regi_full_id_u32": requested, "data_ordinal_raw_i32": ordinal,
        "held_fallback_regi_identity": _id(0x200FE8),
        "resolution": _resolution(requested, selected, fallback=fallback, actual=0xBB000777 if fallback else requested),
        "magic_14_raw_u32": 0x12345678 if invalid else _REGI, "identity_valid": not invalid,
        "physical_chunk_present": None if invalid else physical != 0,
        "physical_chunk_index": chunk_index}


def _pending(count=1, capacity=8, *, target=_CALLBACK) -> dict:
    records = [{**_state(), "native_index": index, "record_identity": _id(0x600000 + 16 * index),
        "vtable_identity": _id(_VTABLE), "slot0_target_identity": _id(target),
        "owner_08_raw_u32": 0x55000035 if count == 1 else 0x33000011,
        "ordinal_0c_raw_i32": 13 if count == 1 else 4} for index in range(count)]
    return {**_state(), "header_identity": _id(0x920468), "buffer_identity": _id(0x600000),
        "capacity_08_raw_i32": capacity, "count_0c_raw_i32": count,
        "allocator_identity": _id(0x700000), "records": records}


def _incoming(chunks: list, occurrences: list) -> dict:
    return {**_state(), "native_index": 0, "arrg_identity": _id(0x900000), "arrg_full_id_u32": 101,
        "army_full_id_140_u32": 12, "unit_full_id_124_u32": 11,
        "army_resolution": _resolution(12, 0xA00000), "unit_resolution": _resolution(11, 0xB00000),
        "passed_province_identity": _id(0x910000), "data_pointer_identity": _id(0x100000),
        "data_count_raw_i32": len(occurrences), "captured_cursor_identity": _id(0x100000),
        "captured_end_identity": _id(0x100000 + 16 * len(occurrences)), "data_ready": True,
        "character_full_id_148_u32": _INVALID, "character_resolution": _resolution(None, None),
        "character_pointer_1b8_present": None, "character_pointer_1b8_identity": None,
        "data_occurrences": occurrences, "physical_chunks": chunks, "association_inputs": [],
        "owner_inputs": [], "date_inputs": [], "pending": _pending()}


def _family(incoming: dict) -> dict:
    # Two roster occurrences reference the same standalone seed; the second
    # occurrence never inherits the first occurrence's simulated mutations.
    candidates = [{**_state(), "native_index": index, "raw_full_id_u32": 101,
        "resolution": _resolution(101, 0x900000), "magic_14_raw_u32": 0x41725267,
        "incoming_valid": True, "incoming_index": 0} for index in range(2)]
    return {**_state(), "schema_version": 1, "source": "native_current_detachment_data_inputs",
        "stage": "observed_current_incoming_2633ff0_seed", "selection_ready": True, "roster_ready": True,
        "current_date_storage_raw64": _DATE, "primary_receiver_identity": _id(0x920000),
        "canonical_pending_vtable_identity": _id(_VTABLE), "ready_pending_callback_identity": _id(_CALLBACK),
        "candidate_occurrences": candidates, "incoming": [incoming]}


def _whole() -> dict:
    chunks = [_chunk(0, 0x200000, 10, 12, 0x03000010, 91, 0x04000001),
        _chunk(1, 0x200400, 9, 3, 0x03000020, -7, 0x04000002),
        _chunk(2, 0x201000, 9, -4, 0x03000030, 5, 0x04000003, date=0x1122334400000005),
        _chunk(3, 0x201C00, -5, -2, 0x03000040, 17, 0x04000004)]
    rows = [_data(0, 0x200000, 0, 0), _data(1, 0x200000, 0, 0),
        _data(2, 0x200400, 1, 1), _data(3, 0x201000, 0, 2, fallback=True),
        _data(4, None, 4, None, invalid=True), _data(5, 0x201C00, 3, 3)]
    rows[1]["raw_regi_full_id_u32"] = rows[0]["raw_regi_full_id_u32"]
    rows[1]["resolution"] = deepcopy(rows[0]["resolution"])
    incoming = _incoming(chunks, rows)
    incoming["association_inputs"] = [_association(0x04000001, 2), _association(0x04000002, -2),
        _association(0x04000003, 0), _association(0x04000004, 3), _association(_INVALID, 0)]
    incoming["owner_inputs"] = [_owner(0x03000010, origin_valid=False), _owner(0x03000020),
        _owner(0x03000030), _owner(0x03000040)]
    incoming["date_inputs"] = [_date(0x04000001, 0x03000010, _DATE, origin_valid=False),
        _date(0x04000002, 0x03000020, _GREATER), _date(0x04000004, 0x03000040, _SMALLER)]
    return _family(incoming)


def _growth(count: int, *, target=_CALLBACK) -> dict:
    incoming = _incoming([_chunk(0, 0x200000, 10, 12, 0x03000020, -7, 0x04000002)],
                         [_data(0, 0x200000, 0, 0)])
    incoming.update(association_inputs=[_association(0x04000002, -1), _association(_INVALID, 0)],
        owner_inputs=[_owner(0x03000020)], date_inputs=[_date(0x04000002, 0x03000020, _GREATER)],
        pending=_pending(count, count, target=target))
    return _family(incoming)


class _Driver:
    def __init__(self, source: dict) -> None:
        self.source, self.calls = source, []

    def take_snapshot(self) -> dict:
        return {"paused": True, "revision": 42, "native_revision": 7, "date_raw": 10000,
            "snapshot_id": "offline-current-DATA-FIRST", "backend_id": "pure-memory-fixture",
            "player_armies": [{"army_id": self.source["army_id"]}], "active_wars": [],
            "diagnostics": {"hello": {"game_version": "1.20.0.3"}}}

    def capabilities(self) -> dict:
        return {"action_steps": ["query-army-strengths-v1"]}

    def execute_step(self, step: str, *, expected_revision=None) -> dict:
        self.calls.append((step, expected_revision))
        return {"status": "available", "army_strengths": [deepcopy(self.source)],
                "native_readiness": {"current_strength": True, "full_monthly": False}}


class _Registration:
    def __init__(self, *args, **kwargs) -> None:
        self.tools = {}

    def tool(self, **kwargs):
        def register(function):
            self.tools[function.__name__] = function
            return function
        return register

    def resource(self, *args, **kwargs):
        return lambda function: function


def query_with_fake_driver(row: dict) -> tuple[dict, list]:
    """FIRST native-wire consumer: real registered/service path, fixture backend."""
    package, sdk_server, sdk_types = ModuleType("mcp"), ModuleType("mcp.server"), ModuleType("mcp.types")
    package.__path__ = []
    sdk_server.MCPServer = _Registration
    sdk_types.ToolAnnotations = lambda **kwargs: SimpleNamespace(**kwargs)
    driver = _Driver(row)
    with patch.dict(sys.modules, {"mcp": package, "mcp.server": sdk_server, "mcp.types": sdk_types}):
        registered = create_server(driver).tools["ck3_query_army_strengths"]
        if registered.__module__ != "xar_autoplayer.bridge.mcp_server":
            raise AssertionError("Expected the real registered army query callable")
        returned = registered([row["army_id"]], expected_revision=42)
    return returned, driver.calls


class CurrentDetachmentDataServiceCompoundTests(unittest.TestCase):
    def test_current_detachment_data_service_compound(self):
        outputs = {}
        def query(name: str, family: dict | None, *, absent=False) -> dict:
            source = strength_row(maximum=120)
            source["monthly_caller_effect_inputs_v1"] = {"status": "available", "ready": True,
                "unavailable_reason": None, "army_byte_22_raw": 0, "current_date_storage_raw64": _DATE,
                "unit_actor_character_id": 29829, "war_counter_rows": [], "manager_army_id_list_2a5a8": []}
            if not absent:
                source[_FAMILY] = family
            before = deepcopy(source)
            returned, calls = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"], {"current_strength": True, "full_monthly": False})
            self.assertEqual(returned["army_strengths"][0]["current_soldiers"], 160)
            value = returned[_SERVICE][0]["projection"]
            self.assertEqual(value["subject_army_id"], 11)
            self.assertEqual(value["native_writes_executed"], 0)
            for row in [value, *value["incoming"]]:
                for flag in ("actual_detachment", "future_drain", "lifecycle", "fullmonthly",
                    "future_drain_ready", "full_army_lifecycle_ready", "full_monthly_ready", "live"):
                    self.assertFalse(row[flag])
                self.assertIsNone(row["actual_post_stage"])
            outputs[name] = {"raw_whole_service_source": before, "returned_service": returned}
            if destination := os.environ.get("XAR_CURRENT_DETACHMENT_DATA_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return value

        value = query("whole6-ordered-alias-equal-greater-rawnegative-fallback-invalid", _whole())
        self.assertTrue(value["ready"])
        self.assertEqual([row["incoming_index"] for row in value["candidate_occurrences"]], [0, 0])
        self.assertEqual(len(value["incoming"]), 1)
        prefix = value["incoming"][0]
        self.assertEqual(prefix["completed_data_occurrence_count"], 6)
        self.assertEqual(prefix["terminal_cursor_identity"], _id(0x100060))
        self.assertEqual([row["predicate"] for row in prefix["occurrences"]], [True, False, True, False, None, True])
        self.assertTrue(prefix["occurrences"][1]["setter_pair_cleared"])
        self.assertEqual(prefix["occurrences"][0]["date_branch"], "both_origins_nonProv_copy_entry_qword")
        self.assertFalse(prefix["occurrences"][0]["date_greater"])
        self.assertFalse(prefix["occurrences"][5]["date_greater"])
        self.assertEqual([[row["maximum_00_raw_i32"], row["current_04_raw_i32"], row["date_1c_raw64"]]
            for row in prefix["physical_chunks"]], [[0, 0, _SENTINEL], [9, 3, _GREATER],
                [9, -4, 0x1122334400000005], [-5, -5, _SENTINEL]])
        self.assertTrue(all(row["association_10_raw_u32"] == _INVALID and row["flag_14_raw_u8"] == 0
                            for row in prefix["physical_chunks"]))
        pending = prefix["conditional_pending"]
        self.assertEqual(pending["conditional_count_0c_raw_i32"], 2)
        self.assertEqual([(row["owner_08_raw_u32"], row["ordinal_0c_raw_i32"])
            for row in pending["conditional_records"]], [(0x55000035, 13), (0x03000020, -7)])
        kinds = [row["kind"] for row in prefix["effects"]]
        self.assertLess(kinds.index("pending_record_init_owner"), kinds.index("pending_record_raw_owner"))

        positive = query("positive-oldcount-nonempty-growth-ready", _growth(2))["incoming"][0]
        self.assertTrue(positive["data_prefix_ready"])
        event = positive["conditional_pending"]["events"][0]
        self.assertEqual([event["new_count"], event["new_capacity"], event["allocation_bytes"]], [3, 3, 48])
        self.assertEqual([item["source_noop_ready"] for item in event["old_record_callbacks"]], [True, True])
        self.assertEqual(event["header_write_order"], ["capacity8", "buffer0", "countC"])
        self.assertEqual([(row["owner_08_raw_u32"], row["ordinal_0c_raw_i32"])
            for row in positive["conditional_pending"]["conditional_records"]],
            [(0x33000011, 4), (0x33000011, 4), (0x03000020, -7)])
        self.assertIsNone(positive["conditional_pending"]["actual_buffer_after_identity"])

        other_table = _growth(2)
        other_table["incoming"][0]["pending"]["records"][0]["vtable_identity"] = _id(_IMAGE + 0x1234)
        self.assertTrue(query("different-vtable-same-source-slot0-target-ready", other_table)["incoming"][0]["data_prefix_ready"])

        unknown = _growth(2)
        unknown["incoming"][0]["pending"]["records"][0]["vtable_identity"] = _id(_IMAGE + 0x5678)
        unknown["incoming"][0]["pending"]["records"][0]["slot0_target_identity"] = _id(_IMAGE + 0x123450)
        partial = query("different-selected-callback-target-partial", unknown)["incoming"][0]
        self.assertFalse(partial["data_prefix_ready"])
        self.assertEqual(partial["completed_data_occurrence_count"], 0)
        self.assertEqual(partial["physical_chunks"][0]["current_04_raw_i32"], 10)
        self.assertEqual(partial["physical_chunks"][0]["date_1c_raw64"], _GREATER)
        self.assertEqual(partial["physical_chunks"][0]["association_10_raw_u32"], 0x04000002)
        self.assertIn("selected_old_pending_record_slot0[0]_source", partial["missing_inputs"])

        zero_source = _growth(0)
        zero_source["ready_pending_callback_identity"] = None
        zero = query("zero-oldcount-growth-no-unused-callback-gate", zero_source)["incoming"][0]
        self.assertTrue(zero["data_prefix_ready"])
        self.assertEqual(zero["conditional_pending"]["events"][0]["old_record_callbacks"], [])
        self.assertEqual(zero["conditional_pending"]["conditional_count_0c_raw_i32"], 1)

        negative = _family(_incoming([], []))
        negative["incoming"][0].update(data_count_raw_i32=-1, captured_end_identity=_id(0xFFFF0),
            data_ready=False, **_state(False))
        partial = query("negative-DATA-endpoint-not-empty-ready", negative)["incoming"][0]
        self.assertFalse(partial["data_prefix_ready"])
        self.assertEqual(partial["terminal_cursor_identity"], _id(0x100000))
        self.assertEqual(partial["data_count_raw_i32"], -1)

        missing_date = _whole()
        seed = missing_date["incoming"][0]
        seed["date_inputs"][1].update(output_date_raw64=None, **_state(False))
        partial = query("missing-selected-computed-date-keeps-earlier-alias-effects", missing_date)["incoming"][0]
        self.assertEqual(partial["completed_data_occurrence_count"], 2)
        self.assertFalse(partial["data_prefix_ready"])
        self.assertEqual(partial["physical_chunks"][0]["maximum_00_raw_i32"], 0)
        self.assertEqual(partial["physical_chunks"][1]["date_1c_raw64"], _SENTINEL)

        no_branch = _family(_incoming([], []))
        no_branch.update(current_date_storage_raw64=None, primary_receiver_identity=None,
            canonical_pending_vtable_identity=None, ready_pending_callback_identity=None)
        no_branch["incoming"][0]["pending"] = {**_state(False), "header_identity": None,
            "buffer_identity": None, "capacity_08_raw_i32": None, "count_0c_raw_i32": None,
            "allocator_identity": None, "records": []}
        seed = no_branch["incoming"][0]
        seed.update(character_full_id_148_u32=29829, character_resolution=_resolution(29829, 0xC00000),
            character_pointer_1b8_present=True, character_pointer_1b8_identity=_id(0xC10000))
        suffix = query("zero-DATA-unused-inputs-independent-selected-suffix", no_branch)["incoming"][0]
        self.assertTrue(suffix["data_prefix_ready"])
        self.assertFalse(suffix["whole_conditional_caller_ready"])
        self.assertEqual(suffix["Character_suffix"]["branch"], "selected_character_inner_effects_partial")
        for name, nullable in (("old-schema-absent", False), ("old-schema-null", True)):
            absent = query(name, None, absent=not nullable)
            self.assertFalse(absent["ready"])
            self.assertEqual(absent["missing_inputs"], [_FAMILY])


if __name__ == "__main__":
    unittest.main()
