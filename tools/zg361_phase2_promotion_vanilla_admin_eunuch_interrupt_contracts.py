#!/usr/bin/env python3
"""Exact vanilla administrative-eunuch story interrupts."""

from __future__ import annotations

from typing import Final


VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_story_cycle_admin_eunuch.8010": {
        # CK3 1.19.0.6 death transition for an administrative-eunuch story.
        # The first two options replace the deceased eunuch with the saved
        # student or rival. The third option only clears the liege modifier
        # and ends this story, making it the bounded terminal route.
        "date_raw": 53316816,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "student": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("student", "rival"),
            "student": ("eunuch", "rival"),
            "rival": ("eunuch", "student"),
        },
        "scope_types": {
            "story": "story",
            "eunuch": "character",
            "emperor": "character",
            "admin_title": "landed_title",
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "story",
            "eunuch",
            "emperor",
            "admin_title",
            "student",
            "rival",
        ),),
        "saved_scope_count": 6,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS"]
