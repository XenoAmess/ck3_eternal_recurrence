"""Strict actual325B080 full-ID-address and literal declaration raw inputs."""
from __future__ import annotations

from .battle_context_source_inputs_contract import _availability, _boolean, _dict, _integer, _number, _string
from ..simulation.battle_person_diac_literal_numeric_12003 import (
    emit_diac_literal_numeric_requests_12003, emit_diac_literal_numeric_row_requests_12003,
)


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _array(value, field, bits, unsigned=False):
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(field + " must be a list or null")
    return [_integer(item, f"{field}[{i}]", bits, unsigned=unsigned) for i, item in enumerate(value)]


def _properties(value, field):
    if value is None:
        return None
    raw = _dict(value, field, {"keys_count", "values_count", "keys_u16", "values_q64"})
    return {"keys_count": _number(raw["keys_count"], field + ".keys_count", 32),
        "values_count": _number(raw["values_count"], field + ".values_count", 32),
        "keys_u16": _array(raw["keys_u16"], field + ".keys_u16", 16, True),
        "values_q64": _array(raw["values_q64"], field + ".values_q64", 64)}


def _properties_ready(properties):
    if properties is None:
        return False
    count, values = properties["keys_count"], properties["values_count"]
    return (count is not None and count >= 0 and count == values
            and properties["keys_u16"] is not None and properties["values_q64"] is not None
            and len(properties["keys_u16"]) == count and len(properties["values_q64"]) == count)


def _metadata(value, field, index, keys):
    raw = _dict(value, field, {"native_index", "key_u16", "selection", "metadata_identity", "byte_ba_raw", "byte_b8_raw"})
    out = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "key_u16": _integer(raw["key_u16"], field + ".key_u16", 16, unsigned=True),
        "selection": _string(raw["selection"], field + ".selection", optional=True),
        "metadata_identity": _string(raw["metadata_identity"], field + ".metadata_identity", optional=True),
        "byte_ba_raw": _number(raw["byte_ba_raw"], field + ".byte_ba_raw", 8, unsigned=True),
        "byte_b8_raw": _number(raw["byte_b8_raw"], field + ".byte_b8_raw", 8, unsigned=True)}
    if out["native_index"] != index or keys is not None and (index >= len(keys) or out["key_u16"] != keys[index]):
        raise ValueError(field + " physical per-key metadata order disagrees")
    selection = "static_5451f40" if out["key_u16"] == 65535 else "provider_50_c8"
    if out["selection"] != selection:
        raise ValueError(field + " actual metadata mapper selection disagrees")
    if out["byte_ba_raw"] != 0 and out["byte_b8_raw"] is not None:
        raise ValueError(field + " BA branch skips the B8 read")
    return out


def _row(value, field, index):
    raw, out = _start(value, field, {"native_index", "declaration_identity", "scale_gate_280_raw",
        "properties", "metadata_provider_loaded", "metadata_rows"})
    out["native_index"] = _integer(raw["native_index"], field + ".native_index", 32)
    out["declaration_identity"] = _string(raw["declaration_identity"], field + ".declaration_identity", optional=True)
    out["scale_gate_280_raw"] = _number(raw["scale_gate_280_raw"], field + ".scale_gate_280_raw", 32, unsigned=True)
    out["metadata_provider_loaded"] = _boolean(raw["metadata_provider_loaded"], field + ".metadata_provider_loaded", optional=True)
    out["properties"] = _properties(raw["properties"], field + ".properties")
    if out["native_index"] != index or not isinstance(raw["metadata_rows"], list):
        raise ValueError(field + " physical declaration/metadata order invalid")
    keys = None if out["properties"] is None else out["properties"]["keys_u16"]
    out["metadata_rows"] = [_metadata(row, f"{field}.metadata_rows[{i}]", i, keys)
                            for i, row in enumerate(raw["metadata_rows"])]
    gate = out["scale_gate_280_raw"]
    if gate is not None and gate != 0:
        if (out["properties"] is not None or out["metadata_provider_loaded"] is not None or out["metadata_rows"]
            or out["reason"] != "dynamic_scale_9d7060"):
            raise ValueError(field + " dynamic scale keeps PC/provider/metadata undemanded")
    if out["metadata_provider_loaded"] is not True and out["metadata_rows"]:
        raise ValueError(field + " unavailable metadata provider cannot publish flag reads")
    if gate == 0 and out["metadata_provider_loaded"] is False and out["reason"] != "metadata_provider_c85860_unavailable":
        raise ValueError(field + " null actual metadata provider retains precise unavailable input")
    metadata = out["metadata_rows"]
    complete = (out["declaration_identity"] is not None and gate == 0 and out["metadata_provider_loaded"] is True
        and _properties_ready(out["properties"]) and len(metadata) == out["properties"]["keys_count"]
        and all(row["metadata_identity"] is not None and row["byte_ba_raw"] is not None
                and (row["byte_ba_raw"] != 0 or row["byte_b8_raw"] is not None) for row in metadata)
        and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " literal declaration numeric readiness disagrees")
    return out


def normalize_diac_literal_numeric_inputs_12003(value):
    field = "diac_literal_numeric_inputs_12003"
    raw, out = _start(value, field, {"scope_character_full_id", "scope_id_address_identity",
        "definition_block_identity", "declaration_count_raw", "declaration_array_present", "declarations"})
    out["scope_character_full_id"] = _number(raw["scope_character_full_id"], field + ".scope_character_full_id", 32)
    for key in ("scope_id_address_identity", "definition_block_identity"):
        out[key] = _string(raw[key], field + "." + key, optional=True)
    out["declaration_count_raw"] = _number(raw["declaration_count_raw"], field + ".declaration_count_raw", 32)
    out["declaration_array_present"] = _boolean(raw["declaration_array_present"], field + ".declaration_array_present", optional=True)
    if not isinstance(raw["declarations"], list):
        raise ValueError(field + ".declarations must be an ordered list")
    out["declarations"] = [_row(row, f"{field}.declarations[{i}]", i) for i, row in enumerate(raw["declarations"])]
    count = out["declaration_count_raw"]
    complete = (out["scope_character_full_id"] is not None and out["scope_id_address_identity"] is not None
        and out["definition_block_identity"] is not None and count is not None and count >= 0
        and out["declaration_array_present"] is not None and (count == 0 or out["declaration_array_present"])
        and len(out["declarations"]) == count and all(row["ready"] for row in out["declarations"])
        and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " whole literal producer readiness disagrees")
    return out
