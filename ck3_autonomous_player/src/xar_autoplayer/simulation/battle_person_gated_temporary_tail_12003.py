"""Pure numeric composition of the source-closed C7A7..C9D8 segment."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_trait_materialized_prefix_12003 import _fold_property_request
from .battle_trait_numeric_inputs_12003 import native_wrap32_12003

FAMILIES_291C7A7 = ("prefix_1398", "delta_prefix_1420_14a8", "list")


def selected_temporary_operand_12003(leaf: dict) -> int | None:
    ec, reference = leaf["selected_ec_raw"], leaf["selector_global_raw"]
    if ec is None or reference is None:
        return None
    return leaf["selected_f8_raw"] if ec == reference else leaf["selected_e8_raw"]


def literal_named_source_value_12003(source: dict) -> int | None:
    if source["tree_present"] is not False:
        return None
    flag = source["fixed_flag_u8"]
    if flag is None:
        return None
    return 0 if flag == 0 else source["raw_fixed_q64"]


def fresh_temporary_rank_12003(refresh: dict) -> tuple[int | None, int | None]:
    raw = literal_named_source_value_12003(refresh["source"])
    minimum = refresh["minimum_q64"]
    if raw is None or minimum is None:
        return None, None
    if raw < minimum:
        clamped = minimum
    else:
        maximum = refresh["maximum_q64"]
        if maximum is None:
            return None, None
        clamped = maximum if raw > maximum else raw
    count, thresholds = refresh["threshold_count"], refresh["thresholds_consumed_q64"]
    if count is None:
        return clamped, None
    if count <= 0:
        return clamped, count
    if thresholds is None:
        return clamped, None
    for index, threshold in enumerate(thresholds):
        if clamped <= threshold:
            return clamped, index
    return clamped, count if len(thresholds) == count else None


def temporary_delta_12003(selected: int, fresh_rank: int) -> tuple[int, int]:
    delta = native_wrap32_12003(selected - fresh_rank)
    return delta, native_wrap32_12003(-delta if delta < 0 else delta)


def compose_gated_temporary_prefix_12003(prefix: dict, weight_q64: int | None) -> dict:
    """Fold each admitted Def40 in prefix order, retaining keys at weight zero."""
    if not prefix["ready"]:
        raise ValueError("Required native input unavailable: temporary prefix")
    count, header = prefix["native_prefix_count"], prefix["header_count"]
    keys, values, updates = [], [], []
    if count is not None and header is not None and 0 < count <= header:
        for row in prefix["rows"]:
            if row["admitted"]:
                block = row["property_block"]
                n = block["keys_count"]
                if n:
                    if weight_q64 is None:
                        raise ValueError("Required native input unavailable: temporary inner weight")
                    _fold_property_request(keys, values, tuple(block["keys_u16"][:n]),
                                           tuple(block["values_q64"][:n]), weight_q64, {}, updates)
    return {"keys_count": len(keys), "values_count": len(values),
            "keys_u16": keys, "values_q64": values, "reason": None}


def emit_gated_temporary_tail_family_requests_12003(leaf: dict, family: str, *, actual_leaf: dict | None = None) -> tuple:
    if family not in FAMILIES_291C7A7:
        raise ValueError("Unknown gated temporary tail family")
    branch = leaf[family]
    if not branch["ready"]:
        raise ValueError("Required native input unavailable: gated_temporary_tail_291c7a7." + family)
    if family != "list":
        if leaf["temporary_admitted"] is not True:
            return ()
        if family == "prefix_1398":
            ordinal, name, block = 0, "291c86e_prefix_1398_temporary", compose_gated_temporary_prefix_12003(branch, 100000)
        else:
            ordinal, name = 1, "291c89d_delta_prefix_temporary"
            block = compose_gated_temporary_prefix_12003(branch["prefix"], branch["weight_source"]["value_q64"])
        # B3D0 always invokes its outer writer, including initialized empty PCs.
        return (NativeWeightedContributionRequest12003(ordinal, name, 0, 1,
                "modeled_temporary:" + family, block, 100000),)
    if branch["selection"] not in {"current_A20", "related_BE0"}:
        return ()
    actual = branch if actual_leaf is None else actual_leaf["list"]
    name = "291c913_current_a20" if branch["selection"] == "current_A20" else "291c9c3_related_be0"
    return tuple(NativeWeightedContributionRequest12003(2, name, row["native_index"], 1,
                 row["property_identity"], actual["rows"][row["native_index"]]["property_block"], 100000)
                 for row in branch["rows"])


def emit_gated_temporary_tail_requests_12003(leaf: dict, *, actual_leaf: dict | None = None) -> tuple:
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: gated_temporary_tail_291c7a7")
    return tuple(request for family in FAMILIES_291C7A7
                 for request in emit_gated_temporary_tail_family_requests_12003(leaf, family, actual_leaf=actual_leaf))
