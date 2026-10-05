"""Two source-closed sparse current-person tail families on exact CK3 1.20.0.3.

Government +870/+A30 and the later carrier +630 rows retain their native call
order. Intervening and subsequent unknown stages are not represented here, so
the combined stream is not a complete tail or a prepared-context baseline.
"""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)


FAMILIES_291C5B7_291CC49 = ("government_870_a30", "carrier_weighted630")
_FIELD = "tail_direct_291c5b7_291cc49"
_GOVERNMENT_MAGIC = 0x4744624F
_SUBCARRIER_MAGIC = 0x5362436F
_GOVERNMENT_SELECTIONS = {
    "character_death_1d0_88", "character_land_1c0_3f8",
    "native_government_fallback",
}
_WEIGHTED_SELECTIONS = {"registry_full_id_8", "native_fallback"}


def _selection(value: object, field: str, allowed: set[str]) -> str | None:
    result = _string(value, field, optional=True)
    if result is not None and result not in allowed:
        raise ValueError(field + " is invalid")
    return result


def _pc_ready(block: dict | None) -> bool:
    return _properties_ready(block) and block["reason"] is None


def _undemanded(result: dict, keys: tuple[str, ...], field: str) -> None:
    if any(result[key] is not None for key in keys):
        raise ValueError(field + " contains undemanded native operands")


def _government(value: object, field: str) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "land_present", "government_selection",
        "government_identity", "government_magic_raw", "admitted",
        "property_870_identity", "property_870", "second_land_present",
        "subcarrier_magic_raw", "subcarrier_full_id_raw",
        "additional_a30_admitted", "property_a30_identity", "property_a30",
        "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {"status": status, "ready": ready, "reason": reason}
    for key in ("land_present", "admitted", "second_land_present",
                "additional_a30_admitted"):
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    for key in ("government_identity", "property_870_identity", "property_a30_identity"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    result["government_selection"] = _selection(
        raw["government_selection"], field + ".government_selection", _GOVERNMENT_SELECTIONS)
    for key in ("government_magic_raw", "subcarrier_magic_raw"):
        result[key] = _number(raw[key], field + "." + key, 32, unsigned=True)
    result["subcarrier_full_id_raw"] = _number(
        raw["subcarrier_full_id_raw"], field + ".subcarrier_full_id_raw", 32)
    for key in ("property_870", "property_a30"):
        result[key] = _properties(raw[key], field + "." + key)

    land, magic = result["land_present"], result["government_magic_raw"]
    admitted = (False if land is False else
                magic == _GOVERNMENT_MAGIC if land is True and magic is not None else None)
    if result["admitted"] != admitted:
        raise ValueError(field + ".admitted disagrees with native land/magic gate")
    if land is not True:
        _undemanded(result, (
            "government_selection", "government_identity", "government_magic_raw",
        ), field)
    if result["government_identity"] is not None and result["government_selection"] is None:
        raise ValueError(field + " selected government lacks source selection")
    if magic is not None and result["government_identity"] is None:
        raise ValueError(field + " government magic lacks selected identity")
    if admitted is not True:
        _undemanded(result, (
            "property_870_identity", "property_870", "second_land_present",
            "subcarrier_magic_raw", "subcarrier_full_id_raw",
            "additional_a30_admitted", "property_a30_identity", "property_a30",
        ), field)
    else:
        second_land = result["second_land_present"]
        submagic, subid = result["subcarrier_magic_raw"], result["subcarrier_full_id_raw"]
        additional = (False if second_land is False else None)
        if second_land is True and submagic is not None:
            additional = (True if submagic != _SUBCARRIER_MAGIC else
                          subid == -1 if subid is not None else None)
        if result["additional_a30_admitted"] != additional:
            raise ValueError(field + ".additional_a30_admitted disagrees with native subcarrier gate")
        if second_land is not True:
            _undemanded(result, ("subcarrier_magic_raw", "subcarrier_full_id_raw"), field)
        if submagic != _SUBCARRIER_MAGIC:
            _undemanded(result, ("subcarrier_full_id_raw",), field)
        if additional is not True:
            _undemanded(result, ("property_a30_identity", "property_a30"), field)

    complete = admitted is False
    if admitted is True:
        complete = (
            result["property_870_identity"] is not None and _pc_ready(result["property_870"])
            and result["additional_a30_admitted"] is not None
            and (not result["additional_a30_admitted"] or (
                result["property_a30_identity"] is not None and _pc_ready(result["property_a30"])
            ))
        )
    complete = complete and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed government operands")
    return result


def _weighted_row(value: object, field: str, index: int) -> dict:
    raw = _dict(value, field, {
        "native_index", "property_identity", "property_block", "weight_q64", "reason",
    })
    result = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "property_identity": _string(raw["property_identity"], field + ".property_identity", optional=True),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
        "weight_q64": _number(raw["weight_q64"], field + ".weight_q64", 64),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    if result["native_index"] != index:
        raise ValueError(field + ".native_index disagrees with stored native row order")
    if (result["property_identity"] is None) != (result["property_block"] is None):
        raise ValueError(field + " PC identity and block disagree")
    complete = result["weight_q64"] is not None and _pc_ready(result["property_block"])
    if (result["reason"] is None) != complete:
        raise ValueError(field + " availability disagrees with consumed row operands")
    return result


def _weighted(value: object, field: str) -> dict:
    raw = _dict(value, field, {
        "status", "ready", "carrier_present", "key_274_raw", "selection",
        "selected_identity", "count_63c", "array_present", "rows", "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {
        "status": status, "ready": ready, "reason": reason,
        "carrier_present": _boolean(raw["carrier_present"], field + ".carrier_present", optional=True),
        "key_274_raw": _number(raw["key_274_raw"], field + ".key_274_raw", 32),
        "selection": _selection(raw["selection"], field + ".selection", _WEIGHTED_SELECTIONS),
        "selected_identity": _string(raw["selected_identity"], field + ".selected_identity", optional=True),
        "count_63c": _number(raw["count_63c"], field + ".count_63c", 32),
        "array_present": _boolean(raw["array_present"], field + ".array_present", optional=True),
    }
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        rows = [_weighted_row(item, f"{field}.rows[{i}]", i) for i, item in enumerate(rows)]
    result["rows"] = rows

    carrier, key = result["carrier_present"], result["key_274_raw"]
    skipped = carrier is False or (carrier is True and key == -1)
    if carrier is not True:
        _undemanded(result, ("key_274_raw",), field)
    if carrier is not True or key is None or key == -1:
        _undemanded(result, ("selection", "selected_identity", "count_63c", "array_present"), field)
        if rows != ([] if skipped else None):
            raise ValueError(field + " skipped/unobserved carrier rows disagree")
    else:
        identity, count, array = result["selected_identity"], result["count_63c"], result["array_present"]
        if identity is not None and result["selection"] is None:
            raise ValueError(field + " selected carrier lacks source selection")
        if identity is None:
            _undemanded(result, ("count_63c", "array_present"), field)
        if count is None or count <= 0:
            _undemanded(result, ("array_present",), field)
            if rows != ([] if count == 0 else None):
                raise ValueError(field + " native zero/unavailable count rows disagree")
        elif array is not True:
            if rows is not None:
                raise ValueError(field + " unavailable current array contains rows")
        elif rows is None or len(rows) != count:
            raise ValueError(field + ".rows disagree with native count_63c")

    count = result["count_63c"]
    selected = result["selection"] is not None and result["selected_identity"] is not None
    complete = skipped or (selected and count == 0)
    if selected and count is not None and count > 0 and result["array_present"] is True and rows is not None:
        complete = all(row["reason"] is None for row in rows)
    complete = complete and reason is None
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed weighted operands")
    return result


def normalize_tail_direct_291c5b7_291cc49(value: object, field: str = _FIELD) -> dict | None:
    """Retain independent readiness, exact native words and unused null fields."""
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", *FAMILIES_291C5B7_291CC49, "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {
        "status": status, "ready": ready, "reason": reason,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "government_870_a30": _government(raw["government_870_a30"], field + ".government_870_a30"),
        "carrier_weighted630": _weighted(raw["carrier_weighted630"], field + ".carrier_weighted630"),
    }
    if ready != all(result[family]["ready"] for family in FAMILIES_291C5B7_291CC49):
        raise ValueError(field + " availability disagrees with the two independent families")
    return result


def _current(section: dict | None) -> tuple[dict, dict]:
    value = None if section is None else section.get(_FIELD)
    current = normalize_tail_direct_291c5b7_291cc49(value)
    if current is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    actor = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32)
    if current["character_id"] != actor:
        raise ValueError(_FIELD + " character disagrees with source actor")
    return current, value


def _request(ordinal: int, name: str, index: int, identity: str, block: object, weight: int):
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return NativeWeightedContributionRequest12003(
        source_ordinal=ordinal, source_name=name, first_row_index=index,
        row_count=1, definition_identity=identity, base_property_block=block,
        weight_q64=weight,
    )


def _requests(current: dict, raw: dict, family: str) -> tuple:
    branch, actual = current[family], raw[family]
    if family == "carrier_weighted630":
        return tuple(_request(
            2, "291cc49_carrier_weighted630", row["native_index"], row["property_identity"],
            actual["rows"][row["native_index"]]["property_block"], row["weight_q64"],
        ) for row in branch["rows"])
    if not branch["admitted"]:
        return ()
    requests = [_request(
        0, "291c5e4_government870", 0, branch["property_870_identity"], actual["property_870"], 100000,
    )]
    if branch["additional_a30_admitted"]:
        requests.append(_request(
            1, "291c61b_governmenta30", 0, branch["property_a30_identity"], actual["property_a30"], 100000,
        ))
    return tuple(requests)


def emit_tail_direct_family_requests_from_current_source_inputs_12003(section: dict | None, family: str) -> tuple:
    """Emit one available family without requiring the other sparse tail family."""
    if family not in FAMILIES_291C5B7_291CC49:
        raise ValueError("Unknown tail direct family")
    current, raw = _current(section)
    if not current[family]["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD + "." + family)
    return _requests(current, raw, family)


def emit_tail_direct_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Emit sparse government then weighted rows; this is not the complete tail."""
    current, raw = _current(section)
    if not current["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    return tuple(request for family in FAMILIES_291C5B7_291CC49
                 for request in _requests(current, raw, family))
