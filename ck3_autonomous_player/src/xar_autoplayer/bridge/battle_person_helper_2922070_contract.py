"""Current-person2922070 raw collection and ordered unit BA0 requests."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _numbers,
    _properties, _properties_ready, _string,
)

_FIELD = "helper_2922070"
_MASK = 0x1000000400
_MAGIC = 0x4744624F
_STRINGS = ("selection", "object_identity", "holder_identity", "reason")


def _record(value: object, field: str, *, words=(), strings=(), booleans=(),
            required_words=(), required_strings=(), required_booleans=(),
            bytes_=(), unsigned_words=(), wide=(), extra=()) -> dict:
    fields = {*words, *strings, *booleans, *required_words, *required_strings,
              *required_booleans, *bytes_, *unsigned_words, *wide, *extra}
    raw = _dict(value, field, fields)
    result = {}
    for key in words:
        result[key] = _number(raw[key], field + "." + key, 32)
    for keys, bits in ((bytes_, 8), (unsigned_words, 32), (wide, 64)):
        for key in keys:
            result[key] = _number(raw[key], field + "." + key, bits, unsigned=True)
    for key in strings:
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in booleans:
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    for key in required_words:
        result[key] = _integer(raw[key], field + "." + key, 32)
    for key in required_strings:
        result[key] = _string(raw[key], field + "." + key)
    for key in required_booleans:
        result[key] = _boolean(raw[key], field + "." + key)
    for key in extra:
        result[key] = raw[key]
    return result


def _list(value: object, field: str, parser, *, optional=True) -> list | None:
    if value is None and optional:
        return None
    if not isinstance(value, list):
        raise ValueError(field + " must be a list" + (" or null" if optional else ""))
    result = [parser(row, f"{field}[{i}]") for i, row in enumerate(value)]
    for i, row in enumerate(result):
        if row["native_index"] != i:
            raise ValueError(field + " disagrees with native occurrence order")
    return result


def _edge(value: object, field: str) -> dict:
    return _record(value, field, words=("requested_id_raw", "holder_id_18_raw"),
                   strings=_STRINGS, required_words=("native_index",))


def _walk(value: object, field: str) -> dict:
    row = _record(value, field, words=("count_c_raw",),
                  strings=("header_selection", "reason"), booleans=("array_present",),
                  required_words=("native_index",), required_strings=("character_identity",),
                  extra=("edges",))
    row["edges"] = _list(row["edges"], field + ".edges", _edge, optional=False)
    return row


def _character(value: object, field: str) -> dict:
    row = _record(value, field,
        words=("input_id_raw", "character_id_18_raw", "first_key_158_raw", "owner_id_160_raw"),
        strings=("selection", "character_identity", "first_selection", "first_identity",
                 "owner_selection", "owner_identity", "government_selection", "government_identity",
                 "top_character_identity", "top_government_selection", "top_government_identity", "reason"),
        booleans=("admitted",), required_words=("native_index",),
        required_booleans=("include_self",),
        wide=("government_mask_40_raw", "top_government_mask_40_raw"))
    if row["include_self"]:
        expected = True
    elif row["first_key_158_raw"] == -1:
        expected = False
    elif row["owner_id_160_raw"] is not None and row["character_id_18_raw"] is not None:
        expected = row["owner_id_160_raw"] == row["character_id_18_raw"]
        if expected:
            first, top = row["government_mask_40_raw"], row["top_government_mask_40_raw"]
            expected = (None if first is None else False if first & _MASK != _MASK
                        else None if top is None else top & _MASK == _MASK)
    else:
        expected = None
    if row["admitted"] != expected:
        raise ValueError(field + " filter admission disagrees with actual operands")
    return row


def _key(value: object, field: str) -> dict:
    return _record(value, field, words=("requested_id_raw",), bytes_=("gate_32_raw",),
                   strings=("selection", "object_identity", "reason"),
                   required_words=("native_index",))


def _membership(value: object, field: str) -> dict:
    row = _record(value, field,
        words=("first_key_158_raw", "count_c_raw", "first_id_10_raw"),
        strings=("first_selection", "first_identity", "header_selection", "reason"),
        booleans=("array_present", "admitted", "appended"),
        required_words=("native_index", "character_index"), extra=("scans",))
    row["scans"] = _list(row["scans"], field + ".scans", _key, optional=False)
    scans = row["scans"]
    if any(scan["gate_32_raw"] not in {None, 0} for scan in scans[:-1]):
        raise ValueError(field + " continued after the first native membership match")
    if row["admitted"] is True and (
            not scans or scans[-1]["gate_32_raw"] in {None, 0}):
        raise ValueError(field + " admission lacks the first nonzero BYTE32")
    if row["admitted"] is False and any(scan["gate_32_raw"] not in {None, 0} for scan in scans):
        raise ValueError(field + " rejects an actual membership match")
    return row


def _row(value: object, field: str) -> dict:
    row = _record(value, field,
        words=("selected_id_10_raw", "count_214_raw", "requested_index_228_raw", "selected_index_raw"),
        strings=("selection", "source_identity", "definition_identity", "table_identity",
                 "property_identity", "reason"), booleans=("admitted",),
        required_words=("native_index", "input_index", "requested_id_raw"),
        bytes_=("type_280_raw",), unsigned_words=("definition_magic_38_raw",),
        extra=("property_block",))
    row["property_block"] = _properties(row["property_block"], field + ".property_block")
    byte, magic = row["type_280_raw"], row["definition_magic_38_raw"]
    expected = None if byte is None else False if byte != 2 else magic == _MAGIC if magic is not None else None
    if row["admitted"] != expected:
        raise ValueError(field + " row admission disagrees with BYTE280/magic38")
    count, requested = row["count_214_raw"], row["requested_index_228_raw"]
    if count is not None and requested is not None:
        last = (count - 1 + (1 << 31)) % (1 << 32) - (1 << 31)
        expected_index = 0 if requested < 0 else min(requested, last)
        if row["selected_index_raw"] != expected_index:
            raise ValueError(field + " index disagrees with native signed clamp")
    if byte is not None and byte != 2 and any(row[key] is not None for key in (
            "definition_identity", "definition_magic_38_raw", "count_214_raw", "requested_index_228_raw",
            "selected_index_raw", "table_identity", "property_identity", "property_block")):
        raise ValueError(field + " contains undemanded definition/index/PC fields")
    if expected is not True and any(row[key] is not None for key in (
            "count_214_raw", "requested_index_228_raw", "selected_index_raw",
            "table_identity", "property_identity", "property_block")):
        raise ValueError(field + " contains an undemanded PC")
    return row


def _row_ready(row: dict) -> bool:
    return (row["reason"] is None and row["admitted"] is not None and
            (row["admitted"] is False or
             (all(row[key] is not None for key in (
                 "definition_identity", "definition_magic_38_raw", "count_214_raw",
                 "requested_index_228_raw", "selected_index_raw", "table_identity", "property_identity"))
              and _properties_ready(row["property_block"]) and row["property_block"]["reason"] is None)))


def _collection_ready(branch: dict) -> bool:
    walks, characters, order, members, ids, rows = (branch[key] for key in (
        "walk_nodes", "characters", "character_order", "membership_rows", "output_ids", "rows"))
    if any(value is None for value in (walks, characters, order, members, ids, rows)):
        return False
    if not walks or not characters or not characters[-1]["include_self"]:
        return False
    if any(node["reason"] is not None or node["count_c_raw"] is None or
           node["count_c_raw"] < 0 or node["array_present"] is None or
           len(node["edges"]) != node["count_c_raw"] or
           any(edge["reason"] is not None or edge["selection"] is None or
               edge["object_identity"] is None or edge["holder_identity"] is None or
               edge["holder_id_18_raw"] is None for edge in node["edges"]) for node in walks):
        return False
    if any(row["reason"] is not None or row["character_identity"] is None or row["admitted"] is None
           for row in characters):
        return False
    retained = [i for i, row in enumerate(characters) if row["admitted"]]
    if len(retained) > 1:
        if any(characters[i]["character_id_18_raw"] is None for i in retained):
            return False
        retained.sort(key=lambda i: characters[i]["character_id_18_raw"] & 0xFFFFFFFF)
        retained = [i for pos, i in enumerate(retained) if pos == 0 or
                    characters[i]["character_identity"] != characters[retained[pos-1]]["character_identity"]]
    if order != retained or len(members) != len(order):
        return False
    appended = []
    for i, row in enumerate(members):
        if (row["reason"] is not None or row["character_index"] != order[i] or
                any(row[key] is None for key in (
                    "first_key_158_raw", "first_selection", "first_identity", "header_selection",
                    "count_c_raw", "array_present", "admitted")) or row["count_c_raw"] < 0):
            return False
        if any(scan["reason"] is not None or any(scan[key] is None for key in (
                "requested_id_raw", "selection", "object_identity", "gate_32_raw"))
               for scan in row["scans"]):
            return False
        if row["admitted"]:
            if row["first_id_10_raw"] is None or len(row["scans"]) > row["count_c_raw"]:
                return False
            actual_append = row["first_id_10_raw"] not in appended
            if row["appended"] != actual_append:
                return False
            if actual_append:
                appended.append(row["first_id_10_raw"])
        elif len(row["scans"]) != row["count_c_raw"]:
            return False
    if ids != appended or len(rows) != len(ids):
        return False
    if sorted(row["input_index"] for row in rows) != list(range(len(ids))):
        return False
    if any(row["requested_id_raw"] != ids[row["input_index"]] or
           row["selection"] is None or row["source_identity"] is None for row in rows):
        return False
    if len(rows) > 1:
        if any(row["selected_id_10_raw"] is None for row in rows):
            return False
        expected = sorted(rows, key=lambda row: (row["selected_id_10_raw"] & 0xFFFFFFFF, row["input_index"]))
        if rows != expected:
            return False
    return True


def normalize_helper_2922070(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    branch = _record(value, field,
        words=("subject_id_8_raw",), strings=("government_selection", "government_identity",
            "subject_identity", "reason"), booleans=("character_land_present", "admitted"),
        bytes_=("government_mode_4d6_raw",), unsigned_words=("subject_magic_c_raw",),
        required_words=("character_id",), required_booleans=("ready", "gate_ready", "collection_ready", "rows_ready"),
        required_strings=("status",), extra=("walk_nodes", "characters", "character_order",
            "membership_rows", "output_ids", "rows"))
    status, ready, reason = _availability(branch, field)
    branch.update(status=status, ready=ready, reason=reason)
    for key, parser in (("walk_nodes", _walk), ("characters", _character),
                        ("membership_rows", _membership), ("rows", _row)):
        branch[key] = _list(branch[key], field + "." + key, parser)
    for key in ("character_order", "output_ids"):
        branch[key] = _numbers(branch[key], field + "." + key, 32)
    mode, land, magic, word = (branch[key] for key in (
        "government_mode_4d6_raw", "character_land_present", "subject_magic_c_raw", "subject_id_8_raw"))
    admission = (None if mode is None else False if mode != 5 else
                 False if land is False else None if land is None or magic is None else
                 True if magic != 0x5362436F else None if word is None else word == -1)
    if branch["admitted"] != admission or branch["gate_ready"] != (admission is not None):
        raise ValueError(field + " whole-helper gate disagrees with current operands")
    if magic is not None and magic != 0x5362436F and word is not None:
        raise ValueError(field + " contains an undemanded subject ID8")
    collection = _collection_ready(branch) if admission is True else False
    rows_ready = collection and all(_row_ready(row) for row in branch["rows"])
    if branch["collection_ready"] != collection or branch["rows_ready"] != rows_ready:
        raise ValueError(field + " family readiness disagrees with raw collection/rows")
    complete = admission is not None and (admission is False or collection and rows_ready) and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with demanded2922070 sources")
    return branch


def emit_helper_2922070_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Preserve native BA0 occurrence order and original PC dictionaries."""
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    raw = None if section is None else section.get(_FIELD)
    branch = normalize_helper_2922070(raw)
    if branch is None or not branch["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    actor = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32)
    if actor != branch["character_id"]:
        raise ValueError(_FIELD + " character disagrees with source actor")
    if branch["admitted"] is False:
        return ()
    return tuple(NativeWeightedContributionRequest12003(
        source_ordinal=row["native_index"], source_name="2922070_ba0",
        first_row_index=row["native_index"], row_count=1,
        definition_identity=row["property_identity"],
        base_property_block=raw["rows"][row["native_index"]]["property_block"], weight_q64=100000)
        for row in branch["rows"] if row["admitted"])
