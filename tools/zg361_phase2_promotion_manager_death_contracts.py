#!/usr/bin/env python3
"""Source-reviewed death-notification manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_DEATH_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "death_management.1000": {
        # Vanilla spouse-death notification. The three authored options are
        # mutually exclusive like/neutral/dislike projections. R176 observed
        # only authored option 2 because the deceased spouse was neutral; it
        # records the ordinary spouse memory/stress effect and terminates.
        "date_raw": 53159208,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "surviving_consort": 29037,
        },
        "unique_character_scope_excludes": {
            "dead_character": (29037,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "surviving_consort": "character",
            "dead_character": "character",
            "deceased_character_stress": "value",
            "realm": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "surviving_consort",
            "dead_character",
            "deceased_character_stress",
            "realm",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}
