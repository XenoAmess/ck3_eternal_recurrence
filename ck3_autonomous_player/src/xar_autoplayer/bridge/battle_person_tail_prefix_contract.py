"""Current-person2753860 and2922530 receipts, without a complete-tail claim."""
from __future__ import annotations


def emit_helper_2922070_requests_from_current_source_inputs_12003(section):
    """Forward the required intervening helper to its dedicated observed leaf."""
    from .battle_person_helper_2922070_contract import (
        emit_helper_2922070_requests_from_current_source_inputs_12003 as emit,
    )
    return emit(section)

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)

_FIELD = "tail_prefix_2753860_2922530"
_MAGIC = 0x4744624F
_275_WORDS = (
    "first_key_158_raw", "land_field_1f8_raw", "owner_key_1e0_raw",
    "owner_id_160_raw", "character_id_18_raw", "initial_relation_key_c8_raw",
    "last_character_id_18_raw",
)
_275_BYTES = ("caller_gate_218_raw", "caller_gate_218_recheck_raw", "government_mode_80c_raw")
_275_STRINGS = (
    "first_selection", "first_identity", "definition_identity",
    "definition_pointer_260_identity", "government_selection", "government_identity",
    "predicate_pointer_selection", "predicate_pointer_identity", "owner_selection",
    "owner_identity", "initial_relation_selection", "initial_relation_identity",
    "property_identity",
)
_275_BOOLS = ("caller_admitted", "character_land_present", "predicate_admitted", "owner_admitted")


def _pc_ready(block: dict | None) -> bool:
    return _properties_ready(block) and block["reason"] is None


def _relation(value: object, field: str, index: int) -> dict:
    raw = _dict(value, field, {"native_index", "character_identity", "magic_1c_raw",
        "character_id_18_raw", "accepted", "next_selection", "next_key_c8_raw",
        "next_identity", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "magic_1c_raw": _number(raw["magic_1c_raw"], field + ".magic_1c_raw", 32, unsigned=True),
              "accepted": _boolean(raw["accepted"], field + ".accepted", optional=True)}
    for key in ("character_id_18_raw", "next_key_c8_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("character_identity", "next_selection", "next_identity", "reason"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    if result["native_index"] != index:
        raise ValueError(field + " relation index disagrees with native order")
    magic, word = result["magic_1c_raw"], result["character_id_18_raw"]
    admitted = (None if magic is None else False if magic != 0x43686172
                else word != -1 if word is not None else None)
    if result["accepted"] != admitted:
        raise ValueError(field + " relation admission disagrees with Character magic/ID")
    return result


def _helper_275(value: object, field: str) -> dict:
    raw = _dict(value, field, {"status", "ready", *_275_WORDS, *_275_BYTES,
        *_275_STRINGS, *_275_BOOLS, "relation_rows", "property_block", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    for key in _275_WORDS:
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in _275_BYTES:
        result[key] = _number(raw[key], field + "." + key, 8, unsigned=True)
    for key in _275_STRINGS:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _275_BOOLS:
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    rows = raw["relation_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".relation_rows must be a list or null")
        rows = [_relation(row, f"{field}.relation_rows[{i}]", i) for i, row in enumerate(rows)]
    result["relation_rows"] = rows
    gate = result["caller_gate_218_raw"]
    caller = gate != 0 if gate is not None else None
    if result["caller_admitted"] != caller:
        raise ValueError(field + " caller admission disagrees with BYTE218")
    land, sentinel = result["character_land_present"], result["land_field_1f8_raw"]
    pointer_a, pointer_b = result["definition_pointer_260_identity"], result["predicate_pointer_identity"]
    predicate = (False if land is False or sentinel == -1 else
                 pointer_a == pointer_b if land is True and sentinel is not None
                 and pointer_a is not None and pointer_b is not None else None)
    if caller is True and result["predicate_admitted"] != predicate:
        raise ValueError(field + " pointer predicate disagrees with current operands")
    mode = result["government_mode_80c_raw"]
    if result["predicate_pointer_selection"] is not None:
        expected = "government_800" if mode == 2 else "native_default_5d26d50"
        if mode is None or result["predicate_pointer_selection"] != expected:
            raise ValueError(field + " predicate pointer selection disagrees with government BYTE80C")
    owner, actor, final_id = (result[key] for key in (
        "owner_id_160_raw", "character_id_18_raw", "last_character_id_18_raw"))
    owner_admission = (True if owner is not None and actor is not None and owner == actor
                       else owner == final_id if owner is not None and final_id is not None else None)
    if predicate is True and result["owner_admitted"] != owner_admission:
        raise ValueError(field + " owner admission disagrees with direct/final Character ID")
    if result["owner_admitted"] is not True and (
            result["property_identity"] is not None or result["property_block"] is not None):
        raise ValueError(field + " contains an undemanded property block")
    complete = (reason is None and result["first_key_158_raw"] is not None
                and result["first_selection"] is not None and result["first_identity"] is not None
                and caller is not None)
    if complete and caller:
        complete = (result["caller_gate_218_recheck_raw"] not in {None, 0}
                    and result["definition_identity"] is not None
                    and pointer_a is not None and predicate is not None)
        if complete and predicate:
            complete = (result["owner_selection"] is not None and result["owner_identity"] is not None
                        and owner is not None and actor is not None and owner_admission is not None)
            if complete and owner_admission:
                complete = result["property_identity"] is not None and _pc_ready(result["property_block"])
    if ready != complete:
        raise ValueError(field + " availability disagrees with demanded2753860 operands")
    return result


def _signed32(value: int) -> int:
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)


def _row_2530(value: object, field: str, index: int, admission: bool | None) -> dict:
    raw = _dict(value, field, {"native_index", "admitted", "definition_identity",
        "count_214_raw", "requested_index_228_raw", "selected_index_raw", "table_identity",
        "property_identity", "property_block", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    for key in ("count_214_raw", "requested_index_228_raw", "selected_index_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("definition_identity", "table_identity", "property_identity", "reason"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    if result["native_index"] != index or result["admitted"] != admission:
        raise ValueError(field + " row order/admission disagrees with native call site")
    count, requested, selected = (result[key] for key in (
        "count_214_raw", "requested_index_228_raw", "selected_index_raw"))
    if count is not None and requested is not None:
        actual = 0 if requested < 0 else min(requested, _signed32(count - 1))
        if selected != actual:
            raise ValueError(field + " signed index disagrees with native clamp")
    if admission is not True and any(result[key] is not None for key in (
            "definition_identity", "count_214_raw", "requested_index_228_raw",
            "selected_index_raw", "table_identity", "property_identity", "property_block")):
        raise ValueError(field + " contains undemanded index/PC operands")
    return result


def _helper_2530(value: object, field: str) -> dict:
    raw = _dict(value, field, {"status", "ready", "first_key_158_raw", "first_selection",
        "first_identity", "definition_identity", "definition_magic_38_raw", "admitted",
        "type_280_raw", "owner_id_160_raw", "character_id_18_raw", "rows", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
              "definition_magic_38_raw": _number(raw["definition_magic_38_raw"], field + ".definition_magic_38_raw", 32, unsigned=True),
              "type_280_raw": _number(raw["type_280_raw"], field + ".type_280_raw", 8, unsigned=True)}
    for key in ("first_key_158_raw", "owner_id_160_raw", "character_id_18_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    for key in ("first_selection", "first_identity", "definition_identity"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    magic = result["definition_magic_38_raw"]
    admission = magic == _MAGIC if magic is not None else None
    if result["admitted"] != admission:
        raise ValueError(field + " definition admission disagrees with magic38")
    type_byte, owner, actor = (result[key] for key in (
        "type_280_raw", "owner_id_160_raw", "character_id_18_raw"))
    expected = (type_byte < 3 if type_byte is not None else None, True,
                owner == actor if owner is not None and actor is not None else None)
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list) or len(rows) not in {0, 3}:
            raise ValueError(field + ".rows must retain three call ordinals or whole skip")
        rows = [_row_2530(row, f"{field}.rows[{i}]", i, expected[i]) for i, row in enumerate(rows)]
    result["rows"] = rows
    complete = (reason is None and result["first_selection"] is not None
                and result["first_identity"] is not None and result["definition_identity"] is not None
                and admission is not None and rows is not None)
    if complete and admission is False:
        complete = rows == []
    elif complete:
        complete = len(rows) == 3 and all(row["admitted"] is not None and row["reason"] is None
            and (not row["admitted"] or (all(row[key] is not None for key in (
                "definition_identity", "count_214_raw", "requested_index_228_raw",
                "selected_index_raw", "table_identity", "property_identity"))
                and _pc_ready(row["property_block"]))) for row in rows)
    if ready != complete:
        raise ValueError(field + " availability disagrees with demanded2922530 operands")
    return result


def normalize_tail_prefix_2753860_2922530(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {"status", "ready", "character_id", "helper_2753860", "helper_2922530", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "character_id": _integer(raw["character_id"], field + ".character_id", 32),
              "helper_2753860": _helper_275(raw["helper_2753860"], field + ".helper_2753860"),
              "helper_2922530": _helper_2530(raw["helper_2922530"], field + ".helper_2922530")}
    if ready != (result["helper_2753860"]["ready"] and result["helper_2922530"]["ready"]):
        raise ValueError(field + " availability disagrees with independent helpers")
    return result


def _current(section: dict | None) -> tuple[dict, dict]:
    raw = None if section is None else section.get(_FIELD)
    current = normalize_tail_prefix_2753860_2922530(raw)
    if current is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    actor = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32)
    if actor != current["character_id"]:
        raise ValueError(_FIELD + " character disagrees with source actor")
    return current, raw


def _request(ordinal: int, name: str, identity: str, block: object):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return NativeWeightedContributionRequest12003(source_ordinal=ordinal, source_name=name,
        first_row_index=ordinal, row_count=1, definition_identity=identity,
        base_property_block=block, weight_q64=100000)


def emit_helper_2753860_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    helper, raw = _current(section)
    current = helper["helper_2753860"]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: helper_2753860")
    if current["owner_admitted"] is not True:
        return ()
    return (_request(0, "2753860_definition40", current["property_identity"],
                     raw["helper_2753860"]["property_block"]),)


def emit_helper_2922530_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    helper, raw = _current(section)
    current = helper["helper_2922530"]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: helper_2922530")
    names = ("2922530_d60", "2922530_f20", "2922530_10e0")
    return tuple(_request(row["native_index"], names[row["native_index"]],
                         row["property_identity"], raw["helper_2922530"]["rows"][row["native_index"]]["property_block"])
                 for row in current["rows"] if row["admitted"])


def emit_tail_prefix_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Emit275 then2530 with an explicitly remaining2922070 implementation gap."""
    helper, _ = _current(section)
    if not helper["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    return (emit_helper_2753860_requests_from_current_source_inputs_12003(section)
            + emit_helper_2922530_requests_from_current_source_inputs_12003(section))
