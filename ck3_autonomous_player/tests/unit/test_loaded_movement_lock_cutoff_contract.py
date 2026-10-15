"""Loaded movement operand authority; no Halt/executor qualification.

Base movement shape comes from a real offline Attach+serializer fixture using
synthetic bytes. Compiled wire SHA256: 1816893fdd0ed0cc49414123a6a9a89ee37557a44c09bcbdc708a4cd4f63f1d2
"""
import copy
import json
import pytest
from xar_autoplayer.bridge.war_contract import _normalize_current_movement_progress

_BASE = json.loads(r'''{"status":"available","source":"native_current_route_edge","unit_state_raw":null,"accumulated_movement_weight_raw":null,"cached_edge_speed_raw":null,"current_edge_movement_rate_raw":null,"native_army_movement_admission":null,"first_route_edge_weight_cost_raw":null,"first_edge_arrival_provider_byte_e_u8":null,"first_route_target_province_type_tag_u32":null,"current_province_type_tag_u32":null,"unit_kind_18_raw_i32":null,"current_province_definition_byte_1b_u8":null,"first_route_target_province_definition_byte_1b_u8":null,"loaded_disembark_penalty_days_rule_i32":null,"normalized_edge_progress":{"raw":60000,"scale":100000},"loaded_movement_lock_cutoff":{"raw":60000,"scale":100000},"first_route_edge_remaining_duration":null,"unavailable_reason":null,"committed_route_timeline":{"status":"unavailable","source":"native_committed_route","native_duration_scale":100000,"committed_route_province_ids":null,"native_route_prefix_remaining_days_q100000":null,"native_full_route_remaining_days_q100000":null,"projected_route_arrival_date_raws":null,"unavailable_reason":"committed_route_timeline_unavailable"}}''')

def _normalize(value):
    return _normalize_current_movement_progress(value, name="current_movement_progress")

@pytest.mark.parametrize("progress", [59999, 60000, 60001])
def test_nondefault_loaded_cutoff_keeps_below_equal_above_without_inference(progress):
    value = copy.deepcopy(_BASE)
    value["normalized_edge_progress"] = {"raw": progress, "scale": 100000}
    actual = _normalize(value)
    assert actual == value
    assert actual["loaded_movement_lock_cutoff"] == {"raw": 60000, "scale": 100000}
    assert "locked" not in actual and "can_halt" not in actual

@pytest.mark.parametrize("raw", [-(2**63), -7, 0, 2**63 - 1])
def test_loaded_cutoff_preserves_signed_raw_without_clamping(raw):
    value = copy.deepcopy(_BASE)
    value["loaded_movement_lock_cutoff"] = {"raw": raw, "scale": 100000}
    assert _normalize(value) == value

def test_null_and_old_shape_are_distinct_without_readiness_changes():
    value = copy.deepcopy(_BASE)
    value["loaded_movement_lock_cutoff"] = None
    assert _normalize(value) == value
    value.pop("loaded_movement_lock_cutoff")
    assert _normalize(value) == value
    assert "loaded_movement_lock_cutoff" not in _normalize(value)

@pytest.mark.parametrize("bad", [True, False, 60000, "60000", [], {},
    {"raw": True, "scale": 100000}, {"raw": 60000.0, "scale": 100000},
    {"raw": -(2**63)-1, "scale": 100000}, {"raw": 2**63, "scale": 100000},
    {"raw": 60000, "scale": 99999}, {"raw": 60000, "scale": 100000.0},
    {"raw": 60000, "scale": True}, {"raw": 60000, "scale": 100000, "extra": 0}])
def test_loaded_cutoff_rejects_bad_scalar_width_scale_or_shape(bad):
    value = copy.deepcopy(_BASE)
    value["loaded_movement_lock_cutoff"] = bad
    with pytest.raises(ValueError):
        _normalize(value)
