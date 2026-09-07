#!/usr/bin/env python3
"""Source-reviewed random-nickname manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_NICKNAME_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "lifestyle_nicknames.1000": {
        # CK3 1.19.0.6 random-nickname notification. The nickname is already
        # assigned by assign_random_nickname_effect before this event opens.
        # R193 observed the bad-nickname, free and capable projection: among
        # six authored options only option B (native index 1) is visible. It
        # is therefore the sole route out of this unrelated vanilla window.
        # Bind the complete inherited nickname frame rather than treating the
        # event namespace as a general allowlist.
        "date_raw": 53158896,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "possible_conqueror": 29037,
            "nickname_root_scope": 29037,
            "nickname_getter": 29037,
        },
        "unique_character_scope_excludes": {
            "informer": (29037,),
        },
        "scope_types": {
            "informer": "character",
        },
        "boolean_scopes": (
            "toggle_null_result",
            "had_nick_the_mad",
        ),
        "saved_scope_name_sets": ((
            "possible_conqueror",
            "toggle_null_result",
            "nickname_root_scope",
            "had_nick_the_mad",
            "nickname_getter",
            "informer",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "snapshot_option_count": 6,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}
