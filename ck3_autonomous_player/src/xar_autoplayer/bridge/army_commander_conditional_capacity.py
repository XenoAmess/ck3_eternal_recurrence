"""Optional exact-.4 supply capacity with a candidate aggregate held unchanged.

This is an independent read of the candidate's current aggregate. It does
not assign that candidate or assert that an assignment preserves the input.
"""

from __future__ import annotations


CONDITIONAL_SUPPLY_CAPACITY_V1_KEY = "conditional_supply_capacity_v1"
CONDITIONAL_SUPPLY_CAPACITY_V1_SCHEMA = (
    "xar.ck3.commander-conditional-supply-capacity.12004.v1"
)
CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE = {
    "game_version": "1.20.0.4",
    "executable_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
    "capacity_rva": 0x2C53BF0,
    "loaded_full_rva": 0x5C68C70,
    "additive_modifier_id": 467,
    "multiplicative_modifier_id": 468,
}
_RAW_FIELDS = (
    "loaded_full_raw", "additive_modifier_raw",
    "multiplicative_modifier_raw", "conditional_capacity_raw",
)
_FIELDS = {
    "schema", "status", "source_character_id", "scale", *_RAW_FIELDS,
    "assignment_applied", "assumption", "unavailable_reason", "provenance",
}
_MASK64 = (1 << 64) - 1


def _wrap64(value: int) -> int:
    return ((value + (1 << 63)) & _MASK64) - (1 << 63)


def _trunc_scale(value: int) -> int:
    magnitude = abs(value) // 100000
    return -magnitude if value < 0 else magnitude


def _native_fixed_mul(left: int, right: int) -> int:
    """Reproduce the signed native fast/slow multiply, including each wrap."""
    if all(((value + 0xB504F333) & _MASK64) <= 0x16A09E666
           for value in (left, right)):
        return _trunc_scale(_wrap64(left * right))
    maximum, minimum = max(left, right), min(left, right)
    quotient = _trunc_scale(maximum)
    remainder = _wrap64(maximum - _wrap64(quotient * 100000))
    return _wrap64(
        _trunc_scale(_wrap64(remainder * minimum))
        + _wrap64(quotient * minimum)
    )


def parse_conditional_capacity_raw64(value: object, name: str = "raw") -> int | None:
    """Parse canonical signed64 decimal strings or null; reject JSON numbers."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"native conditional capacity {name} must be a signed64 decimal string or null")
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"native conditional capacity {name} must be a signed64 decimal string or null") from error
    if not -(1 << 63) <= parsed < (1 << 63) or str(parsed) != value:
        raise ValueError(f"native conditional capacity {name} must be a canonical signed64 decimal string or null")
    return parsed


def normalize_candidate_conditional_supply_capacity_v1(
    value: object,
    *,
    expected_character_id: object,
    expected_candidates_schema: object,
) -> dict[str, object] | None:
    """Validate the optional native leaf without changing candidate legality."""
    if value is None:
        return None
    if expected_candidates_schema != "ck3_12004_army_commander_candidates_v1":
        raise ValueError("native conditional supply capacity requires actual .4 candidates")
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("native conditional supply capacity fields are malformed")
    if (
        value["schema"] != CONDITIONAL_SUPPLY_CAPACITY_V1_SCHEMA
        or value["status"] not in ("available", "unavailable")
        or type(value["scale"]) is not int
        or value["scale"] != 100000
        or value["assignment_applied"] is not False
        or value["assumption"] != "candidate_aggregate_unchanged_after_assignment"
    ):
        raise ValueError("native conditional supply capacity schema/status/assumption is malformed")
    provenance = value["provenance"]
    if (
        not isinstance(provenance, dict)
        or set(provenance) != set(CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE)
        or any(type(provenance[name]) is not type(expected) or provenance[name] != expected
               for name, expected in CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE.items())
    ):
        raise ValueError("native conditional supply capacity exact-build provenance disagrees")
    source_id = value["source_character_id"]
    for identity in (expected_character_id, source_id):
        if identity is not None and (
            type(identity) is not int or not 0 <= identity <= (1 << 31) - 1
        ):
            raise ValueError("native conditional supply capacity requires a full native int32 candidate ID or null")
    if type(source_id) is not type(expected_character_id) or source_id != expected_character_id:
        raise ValueError("native conditional supply capacity source candidate disagrees")
    raw = {name: parse_conditional_capacity_raw64(value[name], name) for name in _RAW_FIELDS}
    if value["status"] == "available":
        if source_id is None or any(amount is None for amount in raw.values()):
            raise ValueError("available native conditional supply capacity requires candidate identity and all raw inputs")
        if value["unavailable_reason"] is not None:
            raise ValueError("available native conditional supply capacity requires a null reason")
        left = _wrap64(raw["loaded_full_raw"] + raw["additive_modifier_raw"])
        right = _wrap64(100000 + raw["multiplicative_modifier_raw"])
        if raw["conditional_capacity_raw"] != _native_fixed_mul(left, right):
            raise ValueError("native conditional supply capacity derived value disagrees with the native formula")
    else:
        if raw["conditional_capacity_raw"] is not None:
            raise ValueError("unavailable native conditional supply capacity must retain a null derived value")
        reason = value["unavailable_reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("unavailable native conditional supply capacity requires a concrete reason")
    return {**value, "provenance": dict(provenance)}
