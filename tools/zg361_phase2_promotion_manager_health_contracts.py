#!/usr/bin/env python3
"""Source-reviewed health manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_HEALTH_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "health.2201": {
        # Vanilla disease notice for someone whose health matters to root.
        # This exact live projection exposes authored options 6 and 7 because
        # root may choose treatment but no court physician is available.
        # Option 6 begins the find-physician flow. Authored option 7 has no
        # scripted effect, so it is the bounded route that avoids a follow-up
        # hiring/search chain while leaving the already-contracted disease
        # untouched. Bind the cared-for third party, root's court ownership,
        # disease flag, background province, and exact rendered projection.
        "date_raw": 53156832,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "health_court_owner": 29037,
        },
        "unique_character_scope_excludes": {
            "sick_character": (29037,),
        },
        "scope_types": {
            "sick_character": "character",
            "disease_type": "flag",
            "background_terrain_scope": "province",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sick_character",
            "disease_type",
            "health_court_owner",
            "background_terrain_scope",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (5, 6),
        "selected_option_number": 7,
        "selected_native_option_index": 6,
    },
}
