"""Pure unit requests in provider192 then 2920850 physical occurrence order."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003

FAMILIES_PROVIDER192_AND2920850_12003 = ("provider_192", "list_168", "list_180")


def _request(ordinal, occurrence, slot, descriptor, identity, block):
    tag = "provider192_inline40" if ordinal == 0 else (
        f"2920850_{FAMILIES_PROVIDER192_AND2920850_12003[ordinal]}_slot{slot}"
        + (f"_descriptor{descriptor}" if descriptor is not None else "")
    )
    return NativeWeightedContributionRequest12003(ordinal, tag, occurrence, 1, identity, block, 100000)


def _mapped_requests(leaf, raw, family, occurrence, nested, descriptor=None):
    ordinal = FAMILIES_PROVIDER192_AND2920850_12003.index(family)
    mapped = leaf[family]["rows"][occurrence]["nested_rows"][nested]["mapped_family"]
    actual = raw[family]["rows"][occurrence]["nested_rows"][nested]["mapped_family"]
    indices = range(len(mapped["rows"])) if descriptor is None else (descriptor,)
    return tuple(
        _request(ordinal, occurrence, nested + 4, i, mapped["rows"][i]["property_identity"],
                 actual["rows"][i]["property_block"])
        for i in indices if mapped["rows"][i]["admitted"]
    )


def emit_provider192_and2920850_descriptor_requests_12003(
    leaf, family, occurrence_index, nested_index, descriptor_index, *, actual_leaf=None,
):
    raw = leaf if actual_leaf is None else actual_leaf
    return _mapped_requests(leaf, raw, family, occurrence_index, nested_index, descriptor_index)


def emit_provider192_and2920850_slot_requests_12003(
    leaf, family, occurrence_index, slot_index, *, actual_leaf=None,
):
    raw = leaf if actual_leaf is None else actual_leaf
    ordinal = FAMILIES_PROVIDER192_AND2920850_12003.index(family)
    if slot_index < 4:
        item = leaf[family]["rows"][occurrence_index]["direct_rows"][slot_index]["pc"]
        block = raw[family]["rows"][occurrence_index]["direct_rows"][slot_index]["pc"]["property_block"]
        return (_request(ordinal, occurrence_index, slot_index, None, item["property_identity"], block),)
    return _mapped_requests(leaf, raw, family, occurrence_index, slot_index - 4)


def emit_provider192_and2920850_family_requests_12003(leaf, family, *, actual_leaf=None):
    if family not in FAMILIES_PROVIDER192_AND2920850_12003:
        raise ValueError("Unknown provider192/2920850 family")
    current = leaf[family]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: provider192_and2920850." + family)
    raw = leaf if actual_leaf is None else actual_leaf
    if family == "provider_192":
        if not current["admitted"]:
            return ()
        return (_request(0, 0, 0, None, current["pc"]["property_identity"],
                         raw[family]["pc"]["property_block"]),)
    return tuple(request for i in range(len(current["rows"])) for slot in range(8)
                 for request in emit_provider192_and2920850_slot_requests_12003(
                     leaf, family, i, slot, actual_leaf=raw))


def emit_provider192_and2920850_requests_12003(leaf, *, actual_leaf=None):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: provider192_and2920850")
    return tuple(request for family in FAMILIES_PROVIDER192_AND2920850_12003
                 for request in emit_provider192_and2920850_family_requests_12003(
                     leaf, family, actual_leaf=actual_leaf))
