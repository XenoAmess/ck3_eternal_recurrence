"""Readonly same-query middle-helper receipts; pure native contribution order."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)

FAMILIES_291F260 = ("rank_138", "rank_118", "rank_158", "rank_178")
FAMILIES_291FB10 = ("preferred", "list_218", "list_248")
_FIELD = "middle_helpers_291f260_291fb10"
_WEIGHT_KEYS = (45, 44, 46, 47)


def _pc_ready(pc: dict | None) -> bool:
    return _properties_ready(pc) and pc["reason"] is None


def _strings(raw: dict, result: dict, field: str, keys: tuple[str, ...]):
    for key in keys:
        result[key] = _string(raw[key], field + "." + key, optional=True)


def _words(raw: dict, result: dict, field: str, keys: tuple[str, ...], bits=32, unsigned=False):
    for key in keys:
        result[key] = _number(raw[key], field + "." + key, bits, unsigned=unsigned)


def _bools(raw: dict, result: dict, field: str, keys: tuple[str, ...]):
    for key in keys:
        result[key] = _boolean(raw[key], field + "." + key, optional=True)


def _list(value: object, field: str, normalize) -> list | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(field + " must be a list or null")
    return [normalize(item, f"{field}[{i}]", i) for i, item in enumerate(value)]


def _wrap(value: int) -> int:
    raw = value & ((1 << 64) - 1)
    return raw - (1 << 64) if raw & (1 << 63) else raw


def _rank_expected(row: dict, component: bool | None) -> int | None:
    if component is False:
        if any(row[key] is not None for key in (
            "score_q64", "override_raw", "threshold_count",
            "threshold_array_present", "thresholds_consumed_q64",
        )):
            raise ValueError("null rank component contains undemanded threshold operands")
        return 0
    if component is None:
        return None
    score, override, count, rows = (row[key] for key in (
        "score_q64", "override_raw", "threshold_count", "thresholds_consumed_q64"))
    if score is None or override is None or count is None or rows is None:
        return None
    if count <= 0:
        if rows or row["threshold_array_present"] is not None:
            raise ValueError("nonpositive threshold count contains undemanded thresholds")
        rank = 0
    else:
        if len(rows) > count:
            raise ValueError("threshold prefix exceeds native count")
        rank, stopped = 0, False
        for index, value in enumerate(rows):
            if score < value:
                if index != len(rows) - 1:
                    raise ValueError("threshold prefix continues after native stopping point")
                stopped = True
                break
            rank += 1
        if row["threshold_array_present"] is not True or (not stopped and len(rows) != count):
            return None
    return min(rank, override) if override >= 0 else rank


def _lookup_expected(row: dict) -> tuple[bool, int | None] | None:
    count, probes = row["weight_keys_count_raw"], row["weight_key_probes"]
    if count is None or count < 0 or probes is None:
        return None
    cursor = 0

    def read(index):
        nonlocal cursor
        if cursor >= len(probes):
            return None
        probe = probes[cursor]
        cursor += 1
        if probe["native_index"] != index:
            raise ValueError("weight key probe disagrees with native lookup order")
        return probe["key_u16"]

    lower, remaining = 0, count
    while remaining > 0:
        half = remaining // 2
        key = read(lower + half)
        if key is None:
            return None
        if key < row["weight_key_u16"]:
            lower += remaining - half
        remaining = half
    found = False
    if lower != count:
        key = read(lower)
        if key is None:
            return None
        found = key == row["weight_key_u16"]
    if cursor != len(probes):
        raise ValueError("weight key receipt contains unused lookup probes")
    return found, lower if found else None


def _rank_family(value: object, field: str, index: int, component: bool | None) -> dict:
    i32 = ("override_raw", "threshold_count", "rank_raw", "manager_count_raw",
           "definition_gate_raw", "weight_default_guard_raw", "weight_keys_count_raw", "weight_native_index")
    i64 = ("score_q64", "weight_value_q64", "weight_q64")
    strings = ("definition_selection", "definition_identity", "weight_source_selection",
               "weight_source_identity", "property_identity")
    bools = ("threshold_array_present", "admitted", "weight_carrier_present", "weight_owner_matches", "weight_found")
    raw = _dict(value, field, {
        "status", "ready", "native_index", *i32, *i64, *strings, *bools,
        "thresholds_consumed_q64", "weight_key_u16", "weight_key_probes", "property_block", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "weight_key_u16": _integer(raw["weight_key_u16"], field + ".weight_key_u16", 16, unsigned=True),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    if result["native_index"] != index or result["weight_key_u16"] != _WEIGHT_KEYS[index]:
        raise ValueError(field + " disagrees with native family order/key")
    _words(raw, result, field, i32)
    _words(raw, result, field, i64, 64)
    _strings(raw, result, field, strings)
    _bools(raw, result, field, bools)
    result["thresholds_consumed_q64"] = _list(
        raw["thresholds_consumed_q64"], field + ".thresholds_consumed_q64",
        lambda item, name, _: _integer(item, name, 64))

    def probe(value, name, _):
        p = _dict(value, name, {"native_index", "key_u16"})
        return {"native_index": _integer(p["native_index"], name + ".native_index", 32),
                "key_u16": _integer(p["key_u16"], name + ".key_u16", 16, unsigned=True)}

    result["weight_key_probes"] = _list(raw["weight_key_probes"], field + ".weight_key_probes", probe)
    if result["definition_selection"] not in {None, "manager_rank_index", "native_rank_fallback"}:
        raise ValueError(field + ".definition_selection is invalid")
    if result["weight_source_selection"] not in {None, "exact_owner_carrier_10", "inline_weight_default_5d67b90"}:
        raise ValueError(field + ".weight_source_selection is invalid")
    gate = result["definition_gate_raw"]
    if result["admitted"] != (gate != 0 if gate is not None else None):
        raise ValueError(field + ".admitted disagrees with signed32 nonzero")
    expected_rank = _rank_expected(result, component)
    if expected_rank is not None and result["rank_raw"] != expected_rank:
        raise ValueError(field + ".rank_raw disagrees with consumed native thresholds")
    selection_ready = (expected_rank is not None and result["definition_selection"] is not None
                       and result["definition_identity"] is not None and gate is not None)
    if result["definition_selection"] is not None and result["rank_raw"] is not None:
        rank, count = result["rank_raw"], result["manager_count_raw"]
        expected = (None if rank >= 0 and count is None else
                    "manager_rank_index" if rank >= 0 and rank < count else "native_rank_fallback")
        if expected is not None and expected != result["definition_selection"]:
            raise ValueError(field + ".definition_selection disagrees with rank/count")
    weight_ready = False
    if result["admitted"] is not True:
        if any(result[key] is not None for key in (
            "weight_carrier_present", "weight_owner_matches", "weight_source_selection", "weight_source_identity",
            "weight_default_guard_raw", "weight_keys_count_raw", "weight_key_probes", "weight_found",
            "weight_native_index", "weight_value_q64", "weight_q64", "property_identity", "property_block",
        )):
            raise ValueError(field + " contains undemanded weight or definition PC operands")
    else:
        lookup = _lookup_expected(result)
        if lookup is not None:
            found, native_index = lookup
            if result["weight_found"] != found or result["weight_native_index"] != native_index:
                raise ValueError(field + " weight selection disagrees with native lower-bound lookup")
            if not found and result["weight_value_q64"] is not None:
                raise ValueError(field + " absent weight key contains an undemanded value")
            value = result["weight_value_q64"]
            if not found or value is not None:
                if result["weight_q64"] != _wrap(100000 + (value or 0)):
                    raise ValueError(field + " weight disagrees with signed64 addition")
                weight_ready = result["weight_source_selection"] is not None and result["weight_source_identity"] is not None
        if result["weight_source_selection"] == "exact_owner_carrier_10":
            weight_ready = weight_ready and result["weight_carrier_present"] is True and result["weight_owner_matches"] is True
        elif result["weight_source_selection"] == "inline_weight_default_5d67b90":
            weight_ready = weight_ready and result["weight_default_guard_raw"] not in {None, 0, -1}
    complete = (selection_ready and (result["admitted"] is False or (
        weight_ready and result["property_identity"] is not None and _pc_ready(result["property_block"])
    )) and reason is None)
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed rank family operands")
    return result


def _helper_260(value: object, field: str) -> dict:
    raw = _dict(value, field, {"status", "ready", "component_present", "families", "reason"})
    status, ready, reason = _availability(raw, field)
    component = _boolean(raw["component_present"], field + ".component_present", optional=True)
    if not isinstance(raw["families"], list) or len(raw["families"]) != 4:
        raise ValueError(field + ".families must contain four ordered native families")
    families = _list(raw["families"], field + ".families",
                     lambda item, name, i: _rank_family(item, name, i, component))
    if families is None or len(families) != 4:
        raise ValueError(field + ".families must contain four ordered native families")
    if ready != all(row["ready"] for row in families):
        raise ValueError(field + " availability disagrees with the four native families")
    return {"status": status, "ready": ready, "component_present": component, "families": families, "reason": reason}


def _modifier(value: object, field: str, index: int) -> dict:
    raw = _dict(value, field, {"native_index", "modifier_identity", "token_u8", "modifier_count_u8",
                             "base_selection", "property_identity", "gate_raw", "admitted", "property_block", "reason"})
    result = {"native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "property_block": _properties(raw["property_block"], field + ".property_block")}
    if result["native_index"] != index:
        raise ValueError(field + ".native_index disagrees with stored order")
    _strings(raw, result, field, ("modifier_identity", "base_selection", "property_identity", "reason"))
    _words(raw, result, field, ("token_u8", "modifier_count_u8"), 8, True)
    _words(raw, result, field, ("gate_raw",))
    _bools(raw, result, field, ("admitted",))
    gate = result["gate_raw"]
    if result["admitted"] != (gate != 0 if gate is not None else None):
        raise ValueError(field + ".admitted disagrees with signed32 nonzero")
    token, count, selected = result["token_u8"], result["modifier_count_u8"], result["base_selection"]
    expected = None if token is None or count is None else (
        "token_indexed" if count > token else "native_modifier_fallback")
    if selected is not None and selected != expected:
        raise ValueError(field + ".base_selection disagrees with native u8 predicate")
    if result["admitted"] is not True and result["property_block"] is not None:
        raise ValueError(field + " contains an undemanded modifier PC")
    return result


def _context(value: object, field: str, index: int) -> dict:
    i32 = ("requested_full_id_raw", "full_id_raw", "owner_full_id_raw", "character_full_id_raw", "modifier_count")
    strings = ("selection", "context_identity", "terminal_property_identity")
    bools = ("admitted", "owner_matches", "modifier_array_present", "token_array_present")
    raw = _dict(value, field, {"status", "ready", "native_index", *i32, *strings, *bools,
                             "magic_raw", "modifier_rows", "terminal_property_block", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "native_index": _integer(raw["native_index"], field + ".native_index", 32),
              "magic_raw": _number(raw["magic_raw"], field + ".magic_raw", 32, unsigned=True),
              "terminal_property_block": _properties(raw["terminal_property_block"], field + ".terminal_property_block"),
              "modifier_rows": _list(raw["modifier_rows"], field + ".modifier_rows", _modifier)}
    if result["native_index"] != index:
        raise ValueError(field + ".native_index disagrees with stored context order")
    _words(raw, result, field, i32)
    _strings(raw, result, field, strings)
    _bools(raw, result, field, bools)
    if result["selection"] not in {None, "land_1c0", "land_1c8", "native_subc_fallback", "registry_full_id_8"}:
        raise ValueError(field + ".selection is invalid")
    magic, full_id = result["magic_raw"], result["full_id_raw"]
    admitted = None if magic is None else False if magic != 0x5362436F else (full_id != -1 if full_id is not None else None)
    if result["admitted"] != admitted:
        raise ValueError(field + ".admitted disagrees with native SubC predicate")
    owner, character = result["owner_full_id_raw"], result["character_full_id_raw"]
    if result["owner_matches"] != (owner == character if owner is not None and character is not None else None):
        raise ValueError(field + ".owner_matches disagrees with exact full-ID equality")
    if admitted is False:
        if any(result[key] is not None for key in (*bools[1:], "owner_full_id_raw", "character_full_id_raw",
                                                  "modifier_count", "terminal_property_identity", "terminal_property_block")):
            raise ValueError(field + " rejected SubC contains undemanded gather operands")
        consumed = result["modifier_rows"] == []
    else:
        count, rows = result["modifier_count"], result["modifier_rows"]
        consumed = (admitted is True and result["owner_matches"] is not None and count is not None and rows is not None
                    and len(rows) == max(0, count) and result["terminal_property_identity"] is not None
                    and _pc_ready(result["terminal_property_block"]))
        if consumed and count > 0:
            consumed = result["modifier_array_present"] is True and result["token_array_present"] is True and all(
                row["modifier_identity"] is not None and row["base_selection"] is not None
                and row["property_identity"] is not None and row["admitted"] is not None and row["reason"] is None
                and (not row["admitted"] or _pc_ready(row["property_block"])) for row in rows)
    complete = consumed and result["selection"] is not None and result["context_identity"] is not None and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed SubC gather operands")
    return result


def _context_family(value: object, field: str, family: str) -> dict:
    raw = _dict(value, field, {"status", "ready", "header_selection", "count", "array_present", "rows", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "header_selection": _string(raw["header_selection"], field + ".header_selection", optional=True),
              "count": _number(raw["count"], field + ".count", 32),
              "array_present": _boolean(raw["array_present"], field + ".array_present", optional=True),
              "rows": _list(raw["rows"], field + ".rows", _context)}
    count, rows = result["count"], result["rows"]
    complete = (count is not None and count >= 0 and rows is not None and len(rows) == count
                and result["header_selection"] is not None and all(row["ready"] for row in rows) and reason is None)
    if family == "preferred":
        complete = complete and count == 1 and result["array_present"] is None
    else:
        complete = complete and result["array_present"] is not None
    if ready != complete:
        raise ValueError(field + " availability disagrees with ordered context family")
    return result


def _helper_fb10(value: object, field: str) -> dict:
    raw = _dict(value, field, {"status", "ready", "land_present", *FAMILIES_291FB10, "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "land_present": _boolean(raw["land_present"], field + ".land_present", optional=True)}
    for family in FAMILIES_291FB10:
        result[family] = _context_family(raw[family], field + "." + family, family)
    if ready != (result["land_present"] is not None and all(result[family]["ready"] for family in FAMILIES_291FB10)):
        raise ValueError(field + " availability disagrees with three context families")
    return result


def normalize_middle_helpers_291f260_291fb10(value: object, field: str = _FIELD) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, field, {"status", "ready", "character_id", "helper_291f260", "helper_291fb10", "reason"})
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason,
              "character_id": _integer(raw["character_id"], field + ".character_id", 32),
              "helper_291f260": _helper_260(raw["helper_291f260"], field + ".helper_291f260"),
              "helper_291fb10": _helper_fb10(raw["helper_291fb10"], field + ".helper_291fb10")}
    if ready != (result["helper_291f260"]["ready"] and result["helper_291fb10"]["ready"]):
        raise ValueError(field + " availability disagrees with the two middle helpers")
    return result


def _current(section: dict | None) -> tuple[dict, dict]:
    value = None if section is None else section.get(_FIELD)
    helper = normalize_middle_helpers_291f260_291fb10(value)
    if helper is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if helper["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return helper, value


def _request(ordinal, name, index, count, identity, block, weight):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return NativeWeightedContributionRequest12003(
        source_ordinal=ordinal, source_name=name, first_row_index=index, row_count=count,
        definition_identity=identity, base_property_block=block, weight_q64=weight)


def emit_helper_291f260_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    if family not in FAMILIES_291F260:
        raise ValueError("Unknown helper291F260 family")
    helper, raw = _current(section)
    index = FAMILIES_291F260.index(family)
    row = helper["helper_291f260"]["families"][index]
    if not row["ready"]:
        raise ValueError("Required native input unavailable: helper_291f260." + family)
    if not row["admitted"]:
        return ()
    return (_request(index, "291f260_" + family, 0, 1, row["property_identity"],
                     raw["helper_291f260"]["families"][index]["property_block"], row["weight_q64"]),)


def emit_helper_291f260_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    helper, _ = _current(section)
    if not helper["helper_291f260"]["ready"]:
        raise ValueError("Required native input unavailable: helper_291f260")
    return tuple(request for family in FAMILIES_291F260
                 for request in emit_helper_291f260_family_requests_from_current_source_inputs_12003(section, family))


def _gather_context(context: dict, actual: dict) -> tuple:
    if context["admitted"] is not True:
        return ()
    gathered = [(context["native_index"], row["native_index"], row["property_identity"],
                 actual["modifier_rows"][row["native_index"]]["property_block"])
                for row in context["modifier_rows"] if row["admitted"]]
    gathered.append((context["native_index"], None, context["terminal_property_identity"],
                     actual["terminal_property_block"]))
    return tuple(gathered)


def observe_helper_291fb10_context_gather_from_current_source_inputs_12003(
    section: dict | None, family: str, native_index: int,
) -> tuple:
    """Expose one available context even when another context read failed."""
    if family not in FAMILIES_291FB10:
        raise ValueError("Unknown helper291FB10 context family")
    index = _integer(native_index, "native_index", 32)
    helper, raw = _current(section)
    rows = helper["helper_291fb10"][family]["rows"]
    if rows is None or not 0 <= index < len(rows) or not rows[index]["ready"]:
        raise ValueError("Required native input unavailable: helper_291fb10 context")
    return _gather_context(rows[index], raw["helper_291fb10"][family]["rows"][index])


def observe_helper_291fb10_family_gather_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    """Expose one complete raw PC gather; global grouping requires all families.

    Returned tuples retain (context index, modifier index or None for terminal,
    actual PC identity, actual property block). They are not native appends.
    """
    if family not in FAMILIES_291FB10:
        raise ValueError("Unknown helper291FB10 context family")
    helper, raw = _current(section)
    current = helper["helper_291fb10"][family]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: helper_291fb10." + family)
    return tuple(row for context in current["rows"]
                 for row in _gather_context(context, raw["helper_291fb10"][family]["rows"][context["native_index"]]))


def emit_helper_291fb10_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Group complete PC pointers globally, reverse last-occurrence order."""
    helper, _ = _current(section)
    if not helper["helper_291fb10"]["ready"]:
        raise ValueError("Required native input unavailable: helper_291fb10")
    gathered = tuple(row for family in FAMILIES_291FB10
                     for row in observe_helper_291fb10_family_gather_from_current_source_inputs_12003(section, family))
    counts = {}
    for _, _, identity, _ in gathered:
        counts[identity] = counts.get(identity, 0) + 1
    emitted, requests = set(), []
    for index in range(len(gathered) - 1, -1, -1):
        _, _, identity, block = gathered[index]
        if identity not in emitted:
            emitted.add(identity)
            requests.append(_request(0, "291fb10_reverse_last_occurrence", index,
                                     counts[identity], identity, block, counts[identity] * 100000))
    return tuple(requests)


def emit_middle_helpers_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Return the two helper request sets; intervening caller stages stay separate.

    The concatenation orders these two selected helpers relative to one another,
    and does not claim a contiguous or complete current-person stage sequence.
    """
    helper, _ = _current(section)
    if not helper["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    return (emit_helper_291f260_requests_from_current_source_inputs_12003(section)
            + emit_helper_291fb10_requests_from_current_source_inputs_12003(section))
