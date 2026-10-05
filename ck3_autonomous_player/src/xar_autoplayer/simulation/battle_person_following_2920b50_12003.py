"""Pure list then own accolade-attribute requests after all-vector preflight."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_trait_numeric_inputs_12003 import native_wrap32_12003

FAMILIES_FOLLOWING_2920B50_12003 = ("list_1c8_50", "own_1b0_570")


def following_rank_selection_12003(attribute):
    rank = attribute["rank_raw_i32"]
    if rank is None:
        return None, None
    index = native_wrap32_12003(rank - 1)
    count = attribute["ranked_count_raw"]
    if index >= 0 and count is None:
        return index, None
    if index < 0 or index >= count:
        guard = attribute["ranked_default_init_guard_raw"]
        if guard is None:
            return index, None
        return index, "uninitialized_default_5d68fb0" if guard in {0, -1} else "initialized_default_5d68fb0"
    return index, "indexed_ranked_row"


def _occurrences(leaf, family):
    return leaf[family]["rows"] if family == "list_1c8_50" else [leaf[family]["occurrence"]]


def emit_following_2920b50_attribute_requests_12003(
    leaf, family, occurrence_index, attribute_index, *, actual_leaf=None,
):
    occurrence = _occurrences(leaf, family)[occurrence_index]
    if occurrence["admitted"] is False or occurrence["preflight_all_valid"] is False:
        return ()
    if not occurrence["preflight_ready"] or occurrence["preflight_all_valid"] is not True:
        raise ValueError("Required native input unavailable: entire attribute preflight")
    item = occurrence["attributes"][attribute_index]
    if not item["ready"]:
        raise ValueError("Required native input unavailable: ranked attribute PC")
    raw = leaf if actual_leaf is None else actual_leaf
    actual = _occurrences(raw, family)[occurrence_index]["attributes"][attribute_index]
    ordinal = FAMILIES_FOLLOWING_2920B50_12003.index(family)
    return (NativeWeightedContributionRequest12003(
        ordinal, f"2920b50_{family}_attribute{attribute_index}", occurrence_index, 1,
        item["pc"]["property_identity"], actual["pc"]["property_block"], 100000,
    ),)


def emit_following_2920b50_family_requests_12003(leaf, family, *, actual_leaf=None):
    if family not in FAMILIES_FOLLOWING_2920B50_12003:
        raise ValueError("Unknown following2920B50 family")
    if not leaf[family]["ready"]:
        raise ValueError("Required native input unavailable: following_2920b50." + family)
    return tuple(request for i, occurrence in enumerate(_occurrences(leaf, family))
                 if occurrence["admitted"] and occurrence["preflight_all_valid"]
                 for j in range(len(occurrence["attributes"]))
                 for request in emit_following_2920b50_attribute_requests_12003(
                     leaf, family, i, j, actual_leaf=actual_leaf))


def emit_following_2920b50_requests_12003(leaf, *, actual_leaf=None):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: following_2920b50")
    return tuple(request for family in FAMILIES_FOLLOWING_2920B50_12003
                 for request in emit_following_2920b50_family_requests_12003(leaf, family, actual_leaf=actual_leaf))
