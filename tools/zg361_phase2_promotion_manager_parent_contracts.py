#!/usr/bin/env python3
"""Source-reviewed parent-support manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_PARENT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "parent.1005": {
        # CK3 1.19.0.6 learning-support offer.  Route A grants +3 learning for
        # five years but also increments the parent's meddling ledger, which
        # can schedule another random parent event.  Route B terminates after
        # one deterministic -15 opinion from the parent and creates no follow-
        # up ticket, modifier or meddling state, so it is the bounded route.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "parent": 29613,
        },
        "unique_character_scope_excludes": {
            "parent": (32904,),
        },
        "scope_types": {
            "parent": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("parent",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}
