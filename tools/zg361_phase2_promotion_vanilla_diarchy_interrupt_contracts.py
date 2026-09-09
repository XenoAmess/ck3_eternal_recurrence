#!/usr/bin/env python3
"""Exact vanilla diarchy interrupts observed on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_DIARCHY_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "diarchy.8042": {
        # CK3 1.19.0.6 co-emperor scapegoat-result letter. The interaction
        # applies its actual consequences before dispatch; this event only
        # shows the result as a tooltip. Because root is the recipient, only
        # authored option A is rendered and its body is empty. Bind the exact
        # interaction carry, including unavailable optional participant
        # identities and all four result flags, before acknowledging it.
        "date_raw": 53366952,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
        },
        "character_scope_differs_from": {
            "actor": ("recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {
            "actor": "character",
            "recipient": "character",
        },
        "boolean_scopes": (
            "diplomacy_small",
            "diplomacy_large",
            "intrigue_small",
            "intrigue_large",
        ),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "diplomacy_small",
            "diplomacy_large",
            "intrigue_small",
            "intrigue_large",
        ),),
        "saved_scope_count": 9,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["VANILLA_DIARCHY_TIMELINE_CONTRACTS"]
