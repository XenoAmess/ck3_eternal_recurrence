"""Source-ordered owner runs and one inner-composed PC for following2921020."""
from __future__ import annotations

from dataclasses import replace

from .battle_context_preparation_branch_291e210_12003 import (
    NativePreparationSourceRow12003, NativePreparationSourceSpan12003,
    NativeWeightedContributionRequest12003, emit_291e210_contribution_requests_12003,
)
from .battle_trait_materialized_prefix_12003 import _fold_property_request

INCOMING_STAGE_FOLLOWING_2921020_12003 = "post2921350_pre291CDA8"
FRONTIER_FOLLOWING_2921020_12003 = "post2921020_pre291CDB3"


def composed_following_2921020_12003(leaf):
    if not leaf["composite_ready"]:
        raise ValueError("Required native input unavailable: following_2921020 composite PCs")
    keys, values, updates = [], [], []
    for name in ("base_pc", "tier_pc"):
        block = leaf[name]["property_block"]
        count = block["keys_count"]
        if count:
            _fold_property_request(keys, values, tuple(block["keys_u16"][:count]),
                tuple(block["values_q64"][:count]), 100000, {"source": name}, updates)
    return {"keys_count": len(keys), "values_count": len(values),
            "keys_u16": keys, "values_q64": values, "reason": None}


def emit_following_2921020_owner_requests_12003(leaf, *, actual_leaf=None):
    if leaf["admitted"] is False:
        return ()
    if leaf["tier_selection"] != "direct_rank_0_2" or leaf["owner_matches"] is None:
        raise ValueError("Required native input unavailable: following_2921020 getter/owner")
    if leaf["owner_matches"] is False:
        return ()
    if leaf["owner_header_ready"] is not True:
        raise ValueError("Required native input unavailable: following_2921020 owner header")
    raw = leaf if actual_leaf is None else actual_leaf
    blocks = {row["definition_identity"]: row["properties"] for row in raw["owner_definition_blocks"]}
    header = leaf["owner_weighted_header"]
    rows = tuple(NativePreparationSourceRow12003(
        row["definition_identity"], row["weight_q64"], blocks.get(row["definition_identity"]))
        for row in (header["rows"] or []))
    span = NativePreparationSourceSpan12003(header["count"], rows)
    empty = NativePreparationSourceSpan12003(0, ())
    return tuple(replace(row, source_ordinal=0, source_name="2921020_owner_weighted28")
                 for row in emit_291e210_contribution_requests_12003(span, empty, empty, False))


def emit_following_2921020_composite_requests_12003(leaf):
    if leaf["admitted"] is False:
        return ()
    block = composed_following_2921020_12003(leaf)
    if block["keys_count"] == 0:
        return ()
    return (NativeWeightedContributionRequest12003(1, "2921020_composite", 0, 1,
        "modeled_temporary:2921020:" + leaf["object_identity"], block, 100000),)


def emit_following_2921020_requests_12003(leaf, *, actual_leaf=None):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: following_2921020")
    return (emit_following_2921020_owner_requests_12003(leaf, actual_leaf=actual_leaf)
            + emit_following_2921020_composite_requests_12003(leaf))
