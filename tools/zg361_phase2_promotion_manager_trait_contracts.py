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
    "trait_specific_ongoing.3009": {
        # CK3 1.19.0.6 depressed-character exhaustion notice. Immediate has
        # already installed the ten-year recurrence flag and five-year
        # exhausted modifier; the sole native option is empty, so native0 is
        # the unavoidable acknowledgement. The ten-year flag can expire
        # during this bounded multi-decade observation, making recurrence
        # source-legal even though one frozen occurrence has no saved scopes.
        "date_raw": 53380728,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((),),
        "saved_scope_count": 0,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "trait_specific_ongoing.3015": {
        # CK3 1.19.0.6 depressed-character criticism event. Immediate sets a
        # ten-year recurrence flag and resolves one unsympathetic councillor,
        # powerful vassal, liege, spouse, or close-family courtier. Native0
        # adds stress and rolls a five-year modifier; native2 loses prestige
        # and can add stress. Native1 only applies -15 opinion from the saved
        # critic, so it is the bounded low-impact continuation route. R365
        # observed the exact one-scope, three-option projection. Source file
        # SHA-256: 34A53CF4AA0B2AE955211024D5C0AF3753A05A4C3529CFE553BA5711C37F50BD.
        "date_raw": 53313672,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "unsympathetic": (32904,),
        },
        "scope_types": {
            "unsympathetic": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("unsympathetic",),),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["MANAGER_TRAIT_TIMELINE_CONTRACTS"]
