#!/usr/bin/env python3
"""Source-reviewed trait-specific manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_TRAIT_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "trait_specific_ongoing.2001": {
        # CK3 1.19.0.6 possessed-character vision. Immediate sets the
        # one-life occurrence flag and resolves a same-faith clergy witness.
        # Native options 0 and 1 respectively run a learning duel or schedule
        # a delayed witch-knowledge event. Native option 2 only relieves
        # stress and terminates the window, so it is the bounded source-capture
        # route. R346 observed this exact one-scope, three-option projection.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "clergy": (29037,),
        },
        "scope_types": {
            "clergy": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("clergy",),),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
}


__all__ = ["MANAGER_TRAIT_TIMELINE_CONTRACTS"]
