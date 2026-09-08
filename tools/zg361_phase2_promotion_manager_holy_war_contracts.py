#!/usr/bin/env python3
"""Source-reviewed great-holy-war notification interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_HOLY_WAR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "great_holy_war.0011": {
        # CK3 1.19.0.6 fires this flavor notice for every player after the
        # hidden awakening event has already unlocked the religion's GHW
        # variable. All five authored options are effect-free and share only
        # an after-tooltip. R342 observed the hostile-faith projection where
        # authored option 4/native 3 is the sole visible acknowledgement.
        # Keep faith opaque and bind only the war-notice data required by the
        # project's explicitly allowed holy-war exception.
        "date_raw": 53223552,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "ghw_first_sponsor": (29037,),
            "background_temple_scope": (29037,),
        },
        "character_scope_matches_any": {
            "ghw_first_sponsor": ("background_temple_scope",),
            "background_temple_scope": ("ghw_first_sponsor",),
        },
        "scope_types": {
            "awakening_faith": "faith",
            "ghw_first_sponsor": "character",
            "background_temple_scope": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "awakening_faith",
            "ghw_first_sponsor",
            "background_temple_scope",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "snapshot_option_count": 5,
        "native_option_indices": (3,),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
}
