#!/usr/bin/env python3
"""Exact vanilla accolade interrupts observed on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_ACCOLADE_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "ep2_accolade_events.0300": {
        # CK3 1.19.0.6 Master of Revels training result. This root-only frame
        # has no heir trainee and authors exactly one unavoidable option. It
        # grants lifestyle_reveler to new_reveler (root), may reduce stress,
        # and does not dispatch a follow-up event. Bind the acclaimed knight
        # and root trainee before taking that sole terminal route.
        "date_raw": 53380128,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "new_reveler": 32904,
        },
        "unique_character_scope_excludes": {
            "master_of_revels": (32904,),
        },
        "character_scope_differs_from": {
            "master_of_revels": ("new_reveler",),
            "new_reveler": ("master_of_revels",),
        },
        "scope_types": {
            "master_of_revels": "character",
            "new_reveler": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "master_of_revels",
            "new_reveler",
        ),),
        "saved_scope_count": 2,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["VANILLA_ACCOLADE_TIMELINE_CONTRACTS"]
