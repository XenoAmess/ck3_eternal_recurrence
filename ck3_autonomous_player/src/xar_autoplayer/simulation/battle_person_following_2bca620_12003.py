"""Minimum source-closed nonnegative balance classifier and provider request."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003


def following_2bca620_balance_classification_12003(balance):
    if balance is None:
        return None, None
    return ("nonnegative_balance_minus_one", -1) if balance >= 0 else ("negative_balance_income_unobserved", None)


def following_2bca620_provider_selection_12003(index, count):
    if index is None or count is None:
        return None
    if index != -1:
        raise ValueError("Minimum following2BCA620 implements only classifier index-1")
    return "provider_1690_equality_sentinel" if index == count else "global_fallback_5d1e0b0"


def emit_following_2bca620_requests_12003(leaf, *, actual_leaf=None):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: following_2bca620")
    provider = leaf["provider_selection"]
    if not provider["admitted"]:
        return ()
    raw = leaf if actual_leaf is None else actual_leaf
    return (NativeWeightedContributionRequest12003(
        0, "following_2bca620_inline40", 0, 1, provider["pc"]["property_identity"],
        raw["provider_selection"]["pc"]["property_block"], 100000,
    ),)
