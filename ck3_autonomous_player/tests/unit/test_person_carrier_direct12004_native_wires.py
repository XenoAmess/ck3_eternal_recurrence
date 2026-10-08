"""One FIRST-only consumer of the NEW eight bounded production-reader wires.

Root must first build/run the new native fixture and set the wire directory.
This test does not launch a producer or claim registered-MCP/live readiness.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from xar_autoplayer.bridge.battle_person_carrier_direct_12004 import (
    FIELD_NAME, emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004,
    normalize_carrier_direct_12004,
)


def test_first_new_carrier_direct_production_reader_wires():
    directory = Path(os.environ["CK3_PERSON_CARRIER_DIRECT_12004_WIRE_DIR"])
    expectations = (
        ("absent-carrier", True, "none", 0),
        ("wrong-magic", True, "none", 0),
        ("mapped-empty", True, "mapped_row", 0),
        ("mapped-nonempty-signed-prowess", True, "mapped_row", 1),
        ("fallback-initialized", True, "static_default_5d71200", 1),
        ("fallback-guard-zero", False, "static_default_5d71200", None),
        ("raw-partial-values", False, "mapped_row", None),
        ("negative-rank-undemanded-count", True, "static_default_5d71200", 0),
    )
    leaves = {}
    requests = {}
    for basename, ready, selection, occurrence in expectations:
        raw = json.loads((directory / (basename + ".json")).read_text(encoding="utf-8"))
        leaf = normalize_carrier_direct_12004(raw)
        leaves[basename] = leaf
        assert leaf["ready"] is ready
        assert leaf["selection"] == selection
        assert leaf["source_occurrence_count"] == occurrence
        assert leaf["character_id"] == 0xAB007485
        section = {"character_id": leaf["character_id"], FIELD_NAME: raw}
        if ready:
            emitted = emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004(section)
            assert len(emitted) == occurrence
            for request in emitted:
                assert request.weight_q64 == 100000
                assert request.definition_identity == leaf["selected_pc_identity"]
                assert request.row_count == 1
            requests[basename] = emitted
        else:
            try:
                emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004(section)
            except ValueError as exc:
                assert leaf["reason"] in str(exc)
            else:
                raise AssertionError("A partial numeric source produced a complete request")

    signed = requests["mapped-nonempty-signed-prowess"][0].base_property_block
    assert signed["keys_u16"] == [0x22A, 0xFFFF, 0x22A, 0]
    assert signed["values_q64"] == [-100000, -(1 << 63), 0, (1 << 63) - 1]
    assert signed["keys_count"] == 4
    default = requests["fallback-initialized"][0].base_property_block
    assert default["keys_u16"] == [0x22A]
    assert default["values_q64"] == [-250000]
    pending = leaves["fallback-guard-zero"]
    assert pending["default_guard_raw"] == 0
    assert pending["selected_pc_count_i32"] == 1
    assert pending["properties"]["values_q64"] == [-250000]
    partial = leaves["raw-partial-values"]
    assert partial["properties"]["keys_u16"] == [0x22A, 0xFFFF, 0x22A, 0]
    assert partial["properties"]["values_q64"] is None
    negative = leaves["negative-rank-undemanded-count"]
    assert negative["rank_i32"] == -1
    assert negative["row_count_i32"] is None
    assert negative["selected_pc_count_i32"] == 0
