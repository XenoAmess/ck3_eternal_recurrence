"""Source contract cases for owned six-stage observations, authored for Root.

These leaves are declared synthetic inputs to the Python parser. They do not
claim native-hook, registered MCP, or live qualification.
"""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_person_six_stage_capture_12004 import (
    FIELD_NAME, QUERY_SCHEMA, SCHEMA, SOURCE_RETURN_RVA,
    emit_captured_person_six_stage_occurrence_requests_12004 as emit_stage,
    emit_captured_person_six_stage_requests_12004 as emit,
    normalize_person_six_stage_capture_12004 as normalize,
    normalize_person_six_stage_query_12004 as normalize_query,
    select_person_six_stage_capture_12004 as select_capture,
)
from xar_autoplayer.bridge.version_identity import CK3_12004


CHARACTER_ID = 29829
DATE_RAW = 53288784
WIDE_VALUE = 2**63 - 9
NATIVE_REVISION = 23


def _absent_pc(*, complete=True):
    return {
        "ready": complete,
        "reason": None if complete else "native_append_unobserved",
        "admitted": False if complete else None,
        "identity": None,
        "count_i32": None,
        "properties": None,
        "weight_q100000": None,
    }


def _called_pc(index, kind, weight):
    return {
        "ready": True,
        "reason": None,
        "admitted": True,
        "identity": hex(0x100000 + 0x100 * index + (0 if kind == "first" else 0x40)),
        "count_i32": 3,
        "properties": {
            "keys_u16": [129, 97, 129],
            "values_q64": [str(WIDE_VALUE), "0", str(-WIDE_VALUE)],
        },
        "weight_q100000": weight,
    }


def _leaf():
    stages = []
    for index in range(6):
        raw = index + 1
        stages.append({
            "index": index,
            "observed": True,
            "raw_count_i32": raw,
            "first_append_observed": True,
            "second_append_observed": True,
            "first_pc": _called_pc(index, "first", raw * 100000),
            "second_pc": _called_pc(index, "second", (raw + 2) * 100000),
        })
    return {
        "schema": SCHEMA,
        "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "configured": True,
        "capture_observed": True,
        "capture_complete": True,
        "ready": True,
        "raw_counts_ready": True,
        "reason": None,
        "capture_sequence": 17,
        "capture_date_raw": DATE_RAW,
        "character_id": CHARACTER_ID,
        "capture_thread_id": 4242,
        "query_thread_id": 4242,
        "character_identity": "0x12345000",
        "context_identity": "0x22345010",
        "source_return_rva": hex(SOURCE_RETURN_RVA),
        "stages": stages,
        "historical_capture": True,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def _section(leaf=None):
    return {"character_id": CHARACTER_ID, FIELD_NAME: _leaf() if leaf is None else leaf}


def _query(*leaves):
    return {
        "schema": QUERY_SCHEMA,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "character_captures": list(leaves) if leaves else [_leaf()],
    }


def _normalize_query(sidecar, character_ids=None):
    return normalize_query(
        sidecar, expected_snapshot_revision=NATIVE_REVISION,
        expected_observed_date_raw=DATE_RAW,
        expected_character_ids=[CHARACTER_ID] if character_ids is None else character_ids,
    )


def _skip(stage, kind):
    stage[kind + "_append_observed"] = False
    stage[kind + "_pc"] = _absent_pc()


def test_natural_order_signed_values_and_historical_provenance():
    raw = _leaf()
    original = deepcopy(raw)
    normalized = normalize(raw)
    requests = emit(_section(raw))
    assert normalized["stages"][0]["first_pc"]["properties"]["values_q64"] == [
        WIDE_VALUE, 0, -WIDE_VALUE,
    ]
    assert [request["source_ordinal"] for request in requests] == list(range(12))
    assert [(request["stage_index"], request["append_kind"]) for request in requests] == [
        (index, kind) for index in range(6) for kind in ("first", "second")
    ]
    for request in requests:
        assert request["capture_sequence"] == 17
        assert request["capture_date_raw"] == DATE_RAW
        assert request["capture_thread_id"] == request["query_thread_id"] == 4242
        assert request["character_id"] == CHARACTER_ID
        assert request["character_identity"] == raw["character_identity"]
        assert request["context_identity"] == raw["context_identity"]
        pc = raw["stages"][request["stage_index"]][request["append_kind"] + "_pc"]
        assert request["source_pc_identity"] == pc["identity"]
        assert int(request["source_return_rva"], 16) == SOURCE_RETURN_RVA
        assert request["native_append_observed"] is True
        assert request["historical_capture"] is True
        assert request["actual_model_write_performed"] is False
        assert request["full_helper_ready"] is False
        assert request["property_block"] == {
            "keys_count": 3, "keys_u16": [129, 97, 129],
            "values_q64": [WIDE_VALUE, 0, -WIDE_VALUE],
        }
    assert raw == original
    query = _normalize_query(_query(raw))
    assert query["snapshot_revision"] == NATIVE_REVISION
    assert query["observed_date_raw"] == DATE_RAW
    assert query["character_captures"] == [normalized]
    assert emit(select_capture(query, CHARACTER_ID)) == requests


def test_negative_counts_and_native_wrapped_second_weight_are_not_recomputed():
    raw = _leaf()
    first, second = raw["stages"][:2]
    first["raw_count_i32"] = -7
    first["first_pc"]["weight_q100000"] = -700000
    first["second_pc"]["weight_q100000"] = -500000
    second["raw_count_i32"] = 2**31 - 1
    second["first_pc"]["weight_q100000"] = (2**31 - 1) * 100000
    second["second_pc"]["weight_q100000"] = -(2**31) * 100000
    requests = emit(_section(raw))
    assert [request["weight_q100000"] for request in requests[:4]] == [
        -700000, -500000, 214748364700000, -214748364800000,
    ]
    assert [request["raw_count_i32"] for request in requests[:4]] == [
        -7, -7, 2147483647, 2147483647,
    ]
    assert "loaded_offset_i32" not in normalize(raw)["stages"][1]
    assert "second_count_i32" not in normalize(raw)["stages"][1]


def test_completed_native_skips_keep_zero_and_append_ordinals_distinct():
    raw = _leaf()
    zero = raw["stages"][0]
    zero["raw_count_i32"] = 0
    _skip(zero, "first")
    _skip(zero, "second")
    _skip(raw["stages"][2], "first")
    normalized = normalize(raw)
    assert normalized["stages"][0]["observed"] is True
    assert normalized["stages"][0]["raw_count_i32"] == 0
    assert normalized["stages"][0]["first_pc"]["count_i32"] is None
    assert normalized["stages"][0]["first_pc"]["admitted"] is False
    assert normalized["stages"][0]["first_pc"]["weight_q100000"] is None
    assert emit_stage(_section(raw), 0) == ()
    requests = emit(_section(raw))
    assert [request["source_ordinal"] for request in requests] == [2, 3, 5, 6, 7, 8, 9, 10, 11]
    assert requests[2]["append_kind"] == "second"
    assert len(emit_stage(_section(raw), 2)) == 1


def test_partial_capture_does_not_turn_absent_call_into_known_zero():
    raw = _leaf()
    raw.update(capture_complete=False, raw_counts_ready=False, ready=False, query_thread_id=None,
               reason="native_six_stage_capture_incomplete")
    for stage in raw["stages"][1:]:
        stage.update(observed=False, raw_count_i32=None,
                     first_append_observed=False, second_append_observed=False,
                     first_pc=_absent_pc(complete=False), second_pc=_absent_pc(complete=False))
    normalized = normalize(raw)
    missing = normalized["stages"][1]
    assert missing["raw_count_i32"] is None
    assert missing["first_pc"]["admitted"] is None
    assert missing["first_pc"]["ready"] is False
    assert missing["first_pc"]["weight_q100000"] is None
    assert normalized["capture_thread_id"] == 4242
    assert normalized["query_thread_id"] is None
    with pytest.raises(ValueError, match="unavailable"):
        emit(_section(raw))
    with pytest.raises(ValueError, match="unavailable"):
        emit_stage(_section(raw), 0)
    raw["stages"][1]["first_pc"] = _absent_pc()
    with pytest.raises(ValueError, match="incomplete capture"):
        normalize(raw)


def test_completed_capture_unread_pc_preserves_other_independent_stage():
    raw = _leaf()
    raw.update(ready=False, reason="native_six_stage_pc_partial")
    unread = raw["stages"][0]["first_pc"]
    unread.update(ready=False, reason="pc_values_unread")
    unread["properties"]["values_q64"] = None
    normalized = normalize(raw)
    assert normalized["capture_complete"] is True
    assert normalized["raw_counts_ready"] is True
    assert normalized["stages"][0]["first_append_observed"] is True
    assert normalized["stages"][0]["first_pc"]["admitted"] is True
    assert normalized["stages"][0]["first_pc"]["properties"]["values_q64"] is None
    with pytest.raises(ValueError, match="unavailable"):
        emit(_section(raw))
    with pytest.raises(ValueError, match="unavailable"):
        emit_stage(_section(raw), 0)
    assert [request["source_ordinal"] for request in emit_stage(_section(raw), 1)] == [2, 3]


def test_owned_python_projection_survives_source_list_mutation():
    raw = _leaf()
    normalized = normalize(raw)
    requests = emit(_section(raw))
    raw["stages"][0]["first_pc"]["properties"]["keys_u16"][0] = 1
    raw["stages"][0]["first_pc"]["properties"]["values_q64"][0] = "2"
    raw["stages"][0]["raw_count_i32"] = 99
    assert normalized["stages"][0]["first_pc"]["properties"]["keys_u16"] == [129, 97, 129]
    assert normalized["stages"][0]["first_pc"]["properties"]["values_q64"][0] == WIDE_VALUE
    assert requests[0]["property_block"]["keys_u16"] == [129, 97, 129]
    assert requests[0]["property_block"]["values_q64"][0] == WIDE_VALUE
    assert requests[0]["raw_count_i32"] == 1


def test_optional_leaf_and_full_generation_character_join():
    assert normalize(None) is None
    with pytest.raises(ValueError, match="unavailable"):
        emit({"character_id": CHARACTER_ID})
    with pytest.raises(ValueError, match="unavailable"):
        emit({"character_id": CHARACTER_ID, FIELD_NAME: None})
    other_generation = _section()
    other_generation["character_id"] = CHARACTER_ID + 2**24
    with pytest.raises(ValueError, match="full CharacterID"):
        emit(other_generation)
    query = _query()
    with pytest.raises(ValueError, match="full CharacterID order"):
        _normalize_query(query, [CHARACTER_ID + 2**24])
    second = _leaf()
    second["character_id"] = CHARACTER_ID + 2**24
    second["character_identity"] = "0x12346000"
    ordered = _query(_leaf(), second)
    _normalize_query(ordered, [CHARACTER_ID, CHARACTER_ID + 2**24])
    ordered["character_captures"].reverse()
    with pytest.raises(ValueError, match="full CharacterID order"):
        _normalize_query(ordered, [CHARACTER_ID, CHARACTER_ID + 2**24])
    with pytest.raises(ValueError, match="unavailable"):
        select_capture(query, CHARACTER_ID + 2**24)


def test_unobserved_capture_and_actual_source_attribution():
    raw = _leaf()
    raw.update(capture_observed=False, capture_complete=False, raw_counts_ready=False,
               ready=False, reason="native_six_stage_unobserved", capture_sequence=0,
               capture_date_raw=None, character_identity=None, context_identity=None,
               capture_thread_id=None, query_thread_id=None,
               source_return_rva=None)
    for stage in raw["stages"]:
        stage.update(observed=False, raw_count_i32=None,
                     first_append_observed=False, second_append_observed=False,
                     first_pc=_absent_pc(complete=False), second_pc=_absent_pc(complete=False))
    assert normalize(raw)["capture_observed"] is False
    assert _normalize_query(_query(raw))["character_captures"][0]["character_id"] == CHARACTER_ID
    with pytest.raises(ValueError, match="unavailable"):
        emit(_section(raw))
    wrong_caller = _leaf()
    wrong_caller["source_return_rva"] = "0x291ebef"
    with pytest.raises(ValueError, match="actual six-stage callback caller"):
        normalize(wrong_caller)
    other_thread = _leaf()
    other_thread["query_thread_id"] = 4243
    with pytest.raises(ValueError, match="same-thread query proof"):
        normalize(other_thread)
    reordered = _leaf()
    reordered["stages"][0], reordered["stages"][1] = reordered["stages"][1], reordered["stages"][0]
    with pytest.raises(ValueError, match="physical six-stage order"):
        normalize(reordered)
    overclaim = _leaf()
    overclaim["full_helper_ready"] = True
    with pytest.raises(ValueError, match="historical observation scope"):
        normalize(overclaim)
    for field in ("snapshot_revision", "observed_date_raw"):
        other_frame = _query()
        other_frame[field] += 1
        with pytest.raises(ValueError, match="requested snapshot frame"):
            _normalize_query(other_frame)
