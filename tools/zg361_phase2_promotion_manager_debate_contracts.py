#!/usr/bin/env python3
"""Source-reviewed imperial-debate manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_DEBATE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "debate_event.5110": {
        # CK3 1.19.0.6 imperial-debate result delivered to the top liege.
        # Immediate has already calculated the winner. Option 1 overturns it
        # and costs legitimacy; option 2 confirms the calculated winner, so
        # option 2 is the bounded least-disruptive terminal route.
        "date_raw": 53163240,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "host": (29037,),
            "debate_opponent": (29037,),
            "debate_contender": (29037,),
            "debate_loser": (29037,),
            "debate_winner": (29037,),
        },
        "character_scope_matches_any": {
            "host": (
                "debate_opponent",
                "debate_contender",
                "debate_loser",
            ),
            "debate_opponent": ("host",),
            "debate_contender": ("host",),
            "debate_loser": ("host",),
        },
        "character_scope_differs_from": {
            "debate_winner": ("debate_loser",),
        },
        "scope_types": {
            "activity": "activity",
            "host": "character",
            "province": "province",
            "debate_opponent": "character",
            "debate_contender": "character",
            "debate_loser": "character",
            "debate_winner": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "activity",
            "host",
            "province",
            "debate_opponent",
            "debate_contender",
            "debate_loser",
            "debate_winner",
        ),),
        "saved_scope_count": 7,
        "scope_variants": ({
            # A regular result has no upset marker. The host is one of the
            # two event-window participants: debate_event.5110 immediately
            # rebinds debate_contender from host and set_opponent_scope_effect
            # rebinds debate_opponent from host for a top-liege recipient.
            # The calculated winner and loser instead come from the activity's
            # durable debate_contender/challenged_movement_leader variables,
            # so they need not include this delivery-window host.  R194 saw
            # host=winner while R288 saw host distinct from both outcomes.
            "saved_scope_names": (
                "activity",
                "host",
                "province",
                "debate_opponent",
                "debate_contender",
                "debate_loser",
                "debate_winner",
            ),
            "saved_scope_count": 7,
            "scope_types": {
                "activity": "activity",
                "host": "character",
                "province": "province",
                "debate_opponent": "character",
                "debate_contender": "character",
                "debate_loser": "character",
                "debate_winner": "character",
            },
            "character_scope_matches_any": {
                "host": ("debate_opponent", "debate_contender"),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
            },
        }, {
            # debate_determine_outcome_effect saves this character scope only
            # when the score produces an upset. The event runs that effect in
            # the host/contender scope, so the marker equals the host.  As in
            # the regular variant, the activity's durable outcome pair may be
            # distinct from that delivery-window host.
            "saved_scope_names": (
                "activity",
                "host",
                "province",
                "debate_opponent",
                "debate_contender",
                "debate_winner",
                "debate_loser",
                "debate_unexpected_win",
            ),
            "saved_scope_count": 8,
            "scope_types": {
                "activity": "activity",
                "host": "character",
                "province": "province",
                "debate_opponent": "character",
                "debate_contender": "character",
                "debate_loser": "character",
                "debate_winner": "character",
                "debate_unexpected_win": "character",
            },
            "unique_character_scope_excludes": {
                "host": (29037,),
                "debate_opponent": (29037,),
                "debate_contender": (29037,),
                "debate_loser": (29037,),
                "debate_winner": (29037,),
                "debate_unexpected_win": (29037,),
            },
            "character_scope_matches_any": {
                "host": ("debate_winner", "debate_loser"),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
                "debate_unexpected_win": ("host",),
            },
        },),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # R285 observed two independently delivered result windows; R327 then
        # reached a third at 53215920 while Central remained active.  Keep the
        # bound finite at the three deliveries now observed on this lineage.
        "max_occurrences": 3,
    },
}
