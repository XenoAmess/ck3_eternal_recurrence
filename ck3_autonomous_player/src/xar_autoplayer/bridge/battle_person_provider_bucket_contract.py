"""Current held-component provider bucket source at CK3 1.20.0.3 caller291C5B2.

Every selected branch returns from the out-of-line C70C/C70F block to C595 or
C59C, then continues at C5B7 to the independent government/qualifier stages.
The held Character1B0+2F8 input supplies this one current source stage; its
future refresh timing and the full person/forecast pipeline are not supplied.
"""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _string,
)


_FIELD = "provider_bucket_291c5b2"
_MAGIC = 0x4744624F
_BUCKET = "provider_bucket_11f8"
_FALLBACK = "native_fallback_5d1e0b0"
_SELECTED = (
    "selected_definition_identity", "selected_magic_raw", "admitted",
    "property_identity", "property_block",
)


def _undemanded(result: dict, keys: tuple[str, ...], field: str) -> None:
    if any(result[key] is not None for key in keys):
        raise ValueError(field + " contains undemanded native operands")


def normalize_provider_bucket_291c5b2(value: object, field: str = _FIELD) -> dict | None:
    """Retain held signed words, demand-dependent nulls and actual PC identity."""
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", "provider_present", "provider_identity",
        "carrier_present", "key_2f8_raw", "denominator_5c68ce8_raw",
        "bucket_index_raw", "provider_count_1204_raw", "provider_array_present",
        "selection", *_SELECTED, "reason",
    })
    status, ready, reason = _availability(raw, field)
    result = {
        "status": status, "ready": ready, "reason": reason,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
    }
    for key in ("provider_present", "carrier_present", "provider_array_present", "admitted"):
        result[key] = _boolean(raw[key], field + "." + key, optional=True)
    for key in ("provider_identity", "selected_definition_identity", "property_identity", "selection"):
        result[key] = _string(raw[key], field + "." + key, optional=True)
    for key in ("key_2f8_raw", "denominator_5c68ce8_raw", "bucket_index_raw", "provider_count_1204_raw"):
        result[key] = _number(raw[key], field + "." + key, 32)
    result["selected_magic_raw"] = _number(
        raw["selected_magic_raw"], field + ".selected_magic_raw", 32, unsigned=True)
    if result["selection"] not in {None, _BUCKET, _FALLBACK}:
        raise ValueError(field + ".selection is invalid")

    provider, carrier = result["provider_present"], result["carrier_present"]
    key, denominator, index = (result["key_2f8_raw"], result["denominator_5c68ce8_raw"],
                                result["bucket_index_raw"])
    if provider is not True:
        # 08FD4E0 would initialize an actual-null slot before this stage. The
        # read-only collector neither invokes it nor invents its return value.
        _undemanded(result, (
            "provider_identity", "carrier_present", "key_2f8_raw", "denominator_5c68ce8_raw",
            "bucket_index_raw", "provider_count_1204_raw", "provider_array_present",
            "selection", *_SELECTED,
        ), field)
    else:
        if result["provider_identity"] is None:
            raise ValueError(field + " loaded provider lacks actual identity")
        if carrier is not True:
            _undemanded(result, ("key_2f8_raw", "denominator_5c68ce8_raw"), field)
        elif key is None:
            _undemanded(result, ("denominator_5c68ce8_raw",), field)
        expected_index = 0 if carrier is False else None
        if carrier is True and key is not None and denominator is not None:
            from ..simulation.battle_trait_numeric_inputs_12003 import native_scratch_factor_multiplier_12003
            expected_index = native_scratch_factor_multiplier_12003(key, denominator)
        if index != expected_index:
            raise ValueError(field + ".bucket_index_raw disagrees with consumed signed low32 numeric result")

    count, array = result["provider_count_1204_raw"], result["provider_array_present"]
    expected_selection = None
    if index is None:
        _undemanded(result, ("provider_count_1204_raw", "provider_array_present"), field)
    elif index < 0:
        _undemanded(result, ("provider_count_1204_raw", "provider_array_present"), field)
        expected_selection = _FALLBACK
    elif count is None:
        _undemanded(result, ("provider_array_present",), field)
    elif index >= count:
        # Signed negative counts are actual comparison misses, not new gates.
        _undemanded(result, ("provider_array_present",), field)
        expected_selection = _FALLBACK
    else:
        expected_selection = _BUCKET
    if result["selection"] != expected_selection:
        raise ValueError(field + ".selection disagrees with native signed bucket/count gates")
    if expected_selection is None or (expected_selection == _BUCKET and array is not True):
        _undemanded(result, _SELECTED, field)

    identity, magic = result["selected_definition_identity"], result["selected_magic_raw"]
    if identity is None:
        _undemanded(result, ("selected_magic_raw", "admitted", "property_identity", "property_block"), field)
    admitted = magic == _MAGIC if magic is not None else None
    if result["admitted"] != admitted:
        raise ValueError(field + ".admitted disagrees with selected definition magic")
    if admitted is not True:
        _undemanded(result, ("property_identity", "property_block"), field)

    complete = (
        provider is True and index is not None and expected_selection is not None
        and identity is not None and admitted is not None
        and (admitted is False or (
            result["property_identity"] is not None
            and _properties_ready(result["property_block"])
            and result["property_block"]["reason"] is None
        )) and reason is None
    )
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed provider bucket operands")
    return result


def emit_provider_bucket_requests_from_current_source_inputs_12003(section: dict | None) -> tuple:
    """Emit this current source stage before government; no whole-tail claim."""
    value = None if section is None else section.get(_FIELD)
    branch = normalize_provider_bucket_291c5b2(value)
    if branch is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    actor = _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32)
    if actor != branch["character_id"]:
        raise ValueError(_FIELD + " character disagrees with source actor")
    if not branch["ready"]:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if not branch["admitted"]:
        return ()
    from ..simulation.battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    return (NativeWeightedContributionRequest12003(
        source_ordinal=0, source_name="291c5b2_provider_bucket40",
        first_row_index=branch["bucket_index_raw"] if branch["selection"] == _BUCKET else 0,
        row_count=1, definition_identity=branch["property_identity"],
        base_property_block=value["property_block"], weight_q64=100000,
    ),)
