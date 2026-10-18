"""Strict optional first-edge native county condition on an existing preview."""
from __future__ import annotations

from .army_county_predicate_trace_contract import normalize_county_predicate_trace_v1
from .army_origin_adjacency_contract import normalize_origin_adjacency_v1

_I32 = ("subject_army_id", "requested_target_province_id", "source_province_id",
        "target_province_id", "native_carmy_id", "actor_character_id", "mode")
_U8 = ("army_1d4_raw", "source_definition_1b_u8", "target_definition_1b_u8")
_OPTIONAL_BOOL = ("source_county_present", "target_county_present",
                  "county_objects_differ", "native_condition_passes")
_FLAGS = ("inputs_observation_ready", "native_condition_called",
          "identity_before_after_match", "internal_subpredicates_observed",
          "actual_loss_observed")
_IDENTITIES = ("source_county_identity", "target_county_identity")
_KEYS = {"schema_version", "source", "input_basis", "predicate_rva", "status",
         "unavailable_reason", "target_county_magic_3e0_u32", *_I32, *_U8,
         *_OPTIONAL_BOOL, *_FLAGS, *_IDENTITIES}


def normalize_county_entry_preview_condition_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if (not isinstance(value, dict) or not _KEYS <= set(value)
            or not set(value) <= _KEYS | {"predicate_trace_v1", "origin_adjacency_v1"}):
        raise ValueError("county preview condition schema is malformed")
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["source"] != "native_preview_first_edge_county_entry_condition"
            or value["input_basis"] != "current_unit_and_preview_first_remaining_province"
            or type(value["predicate_rva"]) is not int or value["predicate_rva"] != 0x24E2230):
        raise ValueError("county preview condition source/basis/version is malformed")
    for keys, low, high in ((_I32, -(1 << 31), 1 << 31), (_U8, 0, 256),
            (("target_county_magic_3e0_u32",), 0, 1 << 32)):
        for key in keys:
            x = value[key]
            if x is not None and (type(x) is not int or not low <= x < high):
                raise ValueError(f"county preview condition {key} has invalid integer width")
    for key in _OPTIONAL_BOOL:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"county preview condition {key} must be bool or null")
    for key in _FLAGS:
        if type(value[key]) is not bool:
            raise ValueError(f"county preview condition {key} must be bool")
    if value["actual_loss_observed"]:
        raise ValueError("county preview does not observe actual loss")
    for key in _IDENTITIES:
        x = value[key]
        if x is not None:
            if (not isinstance(x, str) or not x.startswith("native:")
                    or not x[7:].isascii() or not x[7:].isdecimal()
                    or not 0 < int(x[7:]) < 1 << 64
                    or str(int(x[7:])) != x[7:]):
                raise ValueError("county pointer identity must be canonical opaque native identity")
    ready = value["inputs_observation_ready"]
    available = (ready and value["native_condition_called"]
                 and value["identity_before_after_match"])
    if available:
        if (value["status"] != "available" or value["unavailable_reason"] is not None
                or type(value["native_condition_passes"]) is not bool):
            raise ValueError("available county preview requires a returned native bool")
    else:
        if (value["status"] != "unavailable"
                or not isinstance(value["unavailable_reason"], str)
                or not value["unavailable_reason"]
                or value["native_condition_passes"] is not None
                or value["identity_before_after_match"]):
            raise ValueError("unavailable county preview requires reason and unknown native result")
    if ready:
        required = (*_I32, *_U8, "source_county_present", "target_county_present",
                    "county_objects_differ")
        if any(value[key] is None for key in required):
            raise ValueError("ready county preview requires complete actual gate inputs")
        if value["mode"] != (1 if value["army_1d4_raw"] == 0 else 0):
            raise ValueError("county preview mode disagrees with raw Army1D4")
        for role in ("source", "target"):
            if value[f"{role}_county_present"] != (value[f"{role}_county_identity"] is not None):
                raise ValueError("county presence disagrees with actual pointer identity")
        if value["county_objects_differ"] != (value["source_county_identity"] != value["target_county_identity"]):
            raise ValueError("county pointer comparison disagrees with identities")
        if value["target_county_present"] != (value["target_county_magic_3e0_u32"] is not None):
            raise ValueError("target county magic availability disagrees with pointer presence")
    if value["native_condition_passes"] is True:
        if not (value["source_definition_1b_u8"] and value["target_definition_1b_u8"]
                and value["source_county_present"] and value["target_county_present"]
                and value["county_objects_differ"]
                and value["target_county_magic_3e0_u32"] == 0x436F4461):
            raise ValueError("native true contradicts source-proven common gates")
    result = dict(value)
    if "origin_adjacency_v1" in value:
        result["origin_adjacency_v1"] = normalize_origin_adjacency_v1(
            value["origin_adjacency_v1"], expected_source_province_id=value["source_province_id"])
    trace = None
    if "predicate_trace_v1" in value:
        trace = normalize_county_predicate_trace_v1(value["predicate_trace_v1"], parent=value)
        result["predicate_trace_v1"] = trace
    observed_P = bool(trace and trace["status"] == "available" and
                      any(stage["call_count"] == 1 for stage in trace["stages"]))
    if value["internal_subpredicates_observed"] is not observed_P:
        raise ValueError("county preview partial internal observation flag differs from actual P trace")
    return result


def normalize_county_entry_condition_in_route_preview(preview: dict[str, object]) -> dict[str, object]:
    if "county_entry_condition_v1" not in preview:
        return preview
    family = normalize_county_entry_preview_condition_v1(preview["county_entry_condition_v1"])
    if family is None:
        return {**preview, "county_entry_condition_v1": None}
    route = preview.get("route_province_ids")
    if not isinstance(route, list):
        raise ValueError("county preview requires actual preview route")
    first = 1 if route and route[0] == preview.get("origin_province_id") else 0
    expected = route[first] if first < len(route) else None
    for key, actual in (("subject_army_id", preview.get("army_id")),
                        ("requested_target_province_id", preview.get("target_province_id")),
                        ("source_province_id", preview.get("origin_province_id")),
                        ("target_province_id", expected)):
        if family[key] != actual:
            raise ValueError(f"county preview {key} disagrees with actual first-edge context")
    if expected is None and family["status"] == "available":
        raise ValueError("county preview without a remaining edge cannot be available")
    return {**preview, "county_entry_condition_v1": family}
