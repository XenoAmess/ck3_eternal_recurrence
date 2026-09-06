#!/usr/bin/env python3
"""Source-reviewed TGP military-aid manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_interaction_event.0015": {
        # Notification sent after another governor has already been added to
        # the recipient's wars. Immediate and option only show tooltips; the
        # one authored option adds no further gameplay mutation. The source
        # interaction is repeatable across independent actor/recipient pairs;
        # R177 observed two exact occurrences in one bounded reconnect.
        "date_raw": 53156904,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "governor_at_war": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "governor_joining": (29037,),
        },
        "character_scope_matches_any": {
            "secondary_recipient": ("governor_joining",),
            "governor_joining": ("secondary_recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "governor_at_war",
            "governor_joining",
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 2,
    },
}
