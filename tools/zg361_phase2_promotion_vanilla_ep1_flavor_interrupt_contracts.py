#!/usr/bin/env python3
"""Exact CK3 1.19.0.6 contracts for observed EP1 flavor events."""

from __future__ import annotations

from typing import Final


VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep1_flavor.1000": {
        # CK3 1.19.0.6 visiting-eunuch offer. Immediate may create a suitable
        # eunuch and selects a neighboring court for an unhired visitor.
        # Native options 0 and 1 hire or negotiate with gameplay/resource
        # consequences. Native option 2 declines, moves the visitor to the
        # already-selected pool court, and terminates without a follow-up.
        # R347b observed this exact three-scope, three-option projection.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "eunuch_target": (29037,),
        },
        "scope_types": {
            "eunuch_target_culture": "culture",
            "eunuch_target": "character",
            "new_court": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "eunuch_target_culture",
            "eunuch_target",
            "new_court",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
}


__all__ = ["VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS"]
