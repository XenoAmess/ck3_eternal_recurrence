#!/usr/bin/env python3
"""Source-reviewed TGP military-aid manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_interaction_event.0010": {
        # Request-military-aid letter received by the player.  Exact 1.19.0.6
        # source (tgp_interaction_events.txt:110-237) authors three options;
        # the live R295 frame hides option A because its war-join trigger is
        # false, leaving native indices 1 and 2.  Option B is the AI-default
        # bounded resolution: it assigns the already-saved joining governor
        # and sends the response to the requester.  Option C opens another
        # interaction window, so it is unsuitable for a modal-drain client.
        "date_raw": 53245584,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
            "joining_governor": (32904,),
        },
        "character_scope_differs_from": {
            "actor": ("joining_governor",),
            "joining_governor": ("actor",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {},
        "boolean_scopes": ("hook", "dominant_family"),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "hook",
            "dominant_family",
            "joining_governor",
        ),),
        "saved_scope_count": 8,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 2,
    },
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
