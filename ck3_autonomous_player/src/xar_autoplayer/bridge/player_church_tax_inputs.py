"""Native income-selected direct church tax inputs; shares are fractions."""

from __future__ import annotations

from .religion_context_addon_schema import religion_context_addon_schema

from collections.abc import Mapping


def normalize_player_church_tax_inputs_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Preserve native full IDs, current allocations and literal rules text."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "income_context_character_id",
        "income_context_faith_id", "actual_lessee_character_id",
        "lease_liege_character_id", "top_lease_liege_direct_character_id",
        "lease_liege_share_raw", "top_lease_liege_direct_share_raw",
        "remaining_before_ruler_share_raw", "effective_ruler_tax_share_raw",
        "native_configured_ruler_tax_ceiling_raw", "income_rules_text",
        "raw_scale", "share_unit", "scope",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != religion_context_addon_schema("ck3_12003_player_church_tax_inputs_v1", current_context)
            or value["read_only"] is not True or type(value["available"]) is not bool
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or value["share_unit"] != "fraction"
            or value["scope"] != "income-selected-direct-ruler-tax-rule"):
        raise ValueError("native church tax inputs schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native church tax inputs differ from the current context")
    role_keys = (
        "income_context_character_id", "actual_lessee_character_id",
        "lease_liege_character_id", "top_lease_liege_direct_character_id",
    )
    for key in role_keys:
        if value[key] is not None and (type(value[key]) is not int
                or not -(1 << 31) <= value[key] < (1 << 31)):
            raise ValueError(f"native church tax full character ID is malformed: {key}")
    faith = value["income_context_faith_id"]
    if faith is not None and (type(faith) is not int or not 0 <= faith <= 0xFFFFFFFF):
        raise ValueError("native church tax income-context faith reference is malformed")
    raw_keys = (
        "lease_liege_share_raw", "top_lease_liege_direct_share_raw",
        "remaining_before_ruler_share_raw", "effective_ruler_tax_share_raw",
        "native_configured_ruler_tax_ceiling_raw",
    )
    for key in raw_keys:
        if value[key] is not None and (type(value[key]) is not int
                or not -(1 << 63) <= value[key] < (1 << 63)):
            raise ValueError(f"native church tax signed raw is malformed: {key}")
    if value["income_rules_text"] is not None and not isinstance(value["income_rules_text"], str):
        raise ValueError("native church tax literal rule text is malformed")
    if value["available"]:
        observed = (*role_keys, "income_context_faith_id", *raw_keys, "income_rules_text")
        if (value["unavailable_reason"] is not None
                or any(value[key] is None for key in observed)):
            raise ValueError("available native church tax inputs lost actual values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native church tax inputs lost their native read reason")
    return dict(value)
