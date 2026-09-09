#!/usr/bin/env python3
"""Source-reviewed prison-notification manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_PRISON_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "prison_notification.2002": {
        # CK3 1.19.0.6 full popup sent when a player's heir or spouse is
        # released. The release itself and its memory happen before this
        # notification; its only authored option is an empty acknowledgement.
        "date_raw": 53390784,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "this_player": 32904,
        },
        "unique_character_scope_excludes": {
            "imprisoner": (32904,),
            "prisoner": (32904,),
        },
        "character_scope_matches_any": {
            "bg_override_char": ("imprisoner",),
        },
        "character_scope_differs_from": {
            "imprisoner": ("prisoner",),
            "prisoner": ("imprisoner",),
        },
        "scope_types": {
            "imprisoner": "character",
            "new_memory": "character_memory",
            "prisoner": "character",
            "bg_override_char": "character",
            "this_player": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "imprisoner",
            "new_memory",
            "prisoner",
            "bg_override_char",
            "this_player",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # A player's different heirs or spouses can be imprisoned and released
        # repeatedly during one long campaign observation window.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
