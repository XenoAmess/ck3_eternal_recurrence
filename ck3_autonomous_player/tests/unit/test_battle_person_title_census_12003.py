from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_terminal_transition_contract import _normalize_context_branch_inputs
from xar_autoplayer.simulation.battle_person_title_census_12003 import (
    compute_seven_group_census_from_native_inputs_12003,
)


def _branch():
    rows = []
    for i, requested in enumerate((0, 0, 0x1000002, 0x1000003, 0x1000004, 0x1000005, 0x2000002)):
        rows.append({
            "native_row_index": i, "requested_full_title_id_raw_i32": requested,
            "resolution": "fallback" if i == 6 else "matched",
            "resolved_full_title_id_raw_i32": -1 if i == 6 else requested,
            "qualifier_1d8_raw_u8": 9 if i == 3 else 0,
            "qualifier_130_raw_u8": None if i == 3 else (4 if i == 4 else 0),
            "qualifier_12c_raw_i32": None if i in (3, 4) else (0 if i == 5 else -1),
            "government_bit14": None if i in (3, 4, 5) else True,
            "template_tier_raw_i32": None if i in (3, 4, 5) else (6 if i == 2 else (2 if i == 6 else 0)),
        })
    empty = {"count": 0, "keys_u16": [], "values_q64": []}
    return {
        "status": "available", "ready": True, "character_id": 29829,
        "flag14": False, "selected_index": None, "selected_property_block": None,
        "group_counts": [2, 0, 1, 0, 0, 0, 1],
        "group_property_blocks": [empty, None, empty, None, None, None, empty],
        "unavailable_reason": None,
        "census_inputs": {
            "status": "available", "ready": True, "character_id": 29829,
            "scratch_present": True, "model_present": True,
            "model_owner_present": True, "model_owner_full_character_id_raw_i32": 29829,
            "model_owner_matches_character": True, "model_magic_raw_u32": 0x43684D64,
            "header_source": "landed", "title_count_raw_i32": len(rows),
            "title_occurrences": rows, "unavailable_reason": None,
        },
    }


def test_current_raw_title_census_normalizer_to_kernel():
    sample = _branch()
    prior = deepcopy(sample)
    normalized = _normalize_context_branch_inputs(sample, "branch")
    result = compute_seven_group_census_from_native_inputs_12003(normalized)
    assert result.calculation_ready and result.group_counts == (2, 0, 1, 0, 0, 0, 1)
    assert result.row_admissions == (True, True, True, False, False, False, True)
    assert result.ledger["requested_full_title_ids_in_native_order"][:2] == (0, 0)
    assert result.ledger["resolution_in_native_order"][-1] == "fallback"
    assert result.ledger["matched_model_refresh_admitted"] is True
    assert sample == prior and not result.native_write_performed
    assert not result.full_native_callback_ready and not result.entry_refresh_ready
    assert result.actual_game_days_advanced == 0 and not result.ledger["stage_start_context_supplied"]
    # Current summaries do not act as primitive inputs or a previous stage.
    sample["group_counts"] = [-99] * 7
    sample["group_property_blocks"] = [None] * 7
    assert compute_seven_group_census_from_native_inputs_12003(
        _normalize_context_branch_inputs(sample, "branch")).group_counts == result.group_counts

    for family in ("owner_mismatch", "owner_absent", "model_absent", "scratch_absent", "wrong_magic"):
        sample = _branch()
        raw = sample["census_inputs"]
        if family == "owner_mismatch":
            raw.update(model_owner_full_character_id_raw_i32=-2147483648,
                       model_owner_matches_character=False, model_magic_raw_u32=None)
        elif family == "wrong_magic":
            raw["model_magic_raw_u32"] = 0
        else:
            raw.update(model_owner_present=None if family != "owner_absent" else False,
                       model_owner_full_character_id_raw_i32=None, model_magic_raw_u32=None,
                       model_owner_matches_character=None if family != "owner_absent" else False)
            if family == "model_absent": raw["model_present"] = False
            if family == "scratch_absent": raw.update(scratch_present=False, model_present=None)
        result = compute_seven_group_census_from_native_inputs_12003(_normalize_context_branch_inputs(sample, "branch"))
        assert result.calculation_ready and result.ledger["matched_model_refresh_admitted"] is False

    sample = _branch()
    sample["census_inputs"].update(header_source="static", title_count_raw_i32=0, title_occurrences=[])
    assert compute_seven_group_census_from_native_inputs_12003(
        _normalize_context_branch_inputs(sample, "branch")).group_counts == (0,) * 7
    sample = _branch()
    sample["census_inputs"]["title_occurrences"][0].update(government_bit14=False, template_tier_raw_i32=None)
    assert compute_seven_group_census_from_native_inputs_12003(
        _normalize_context_branch_inputs(sample, "branch")).group_counts == (1, 0, 1, 0, 0, 0, 1)

    for gap in ("unresolved", "government", "tier", "negative_count", "outside"):
        sample = _branch()
        raw = sample["census_inputs"]
        row = raw["title_occurrences"][0]
        if gap != "outside":
            raw.update(status="partial", ready=False, unavailable_reason="actual_operand_missing")
        if gap == "unresolved":
            row.update(resolution="unavailable", resolved_full_title_id_raw_i32=None,
                       qualifier_1d8_raw_u8=None, qualifier_130_raw_u8=None,
                       qualifier_12c_raw_i32=None, government_bit14=None, template_tier_raw_i32=None)
        elif gap == "government": row.update(government_bit14=None, template_tier_raw_i32=None)
        elif gap == "tier": row["template_tier_raw_i32"] = None
        elif gap == "outside": row["template_tier_raw_i32"] = 7
        else: raw.update(title_count_raw_i32=-1, title_occurrences=None)
        result = compute_seven_group_census_from_native_inputs_12003(_normalize_context_branch_inputs(sample, "branch"))
        assert not result.calculation_ready and result.group_counts == (None,) * 7 and result.missing_inputs

    for bad in ("byte_width", "id_width", "row_order", "actor_join", "missing_ready_operand"):
        sample = _branch()
        raw = sample["census_inputs"]
        if bad == "byte_width": raw["title_occurrences"][0]["qualifier_1d8_raw_u8"] = 256
        elif bad == "id_width": raw["title_occurrences"][0]["requested_full_title_id_raw_i32"] = 2**31
        elif bad == "row_order": raw["title_occurrences"].reverse()
        elif bad == "actor_join": raw["character_id"] = 30000
        else: raw["title_occurrences"][0]["government_bit14"] = None
        with pytest.raises(ValueError): _normalize_context_branch_inputs(sample, "branch")
    sample = _branch()
    del sample["census_inputs"]
    assert "census_inputs" not in _normalize_context_branch_inputs(sample, "branch")
    assert not compute_seven_group_census_from_native_inputs_12003(sample).calculation_ready
    sample["census_inputs"] = None
    assert _normalize_context_branch_inputs(sample, "branch")["census_inputs"] is None
