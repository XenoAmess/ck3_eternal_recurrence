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
            # two authored participants and may be either calculated winner
            # or loser. R194 observed host/opponent/contender/winner=29501
            # and loser=28667; the earlier live frame observed host=loser.
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
                "host": ("debate_winner", "debate_loser"),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
            },
        }, {
            # debate_determine_outcome_effect saves this character scope only
            # when the score produces an upset. The event runs that effect in
            # the host/contender scope, so the marker equals the host; the host
            # is then exactly one of the calculated winner or loser.
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
        # R285 observed two independently delivered result windows in one
        # fresh client at 53203368 and 53211192.  Keep the bound finite: the
        # two live-observed deliveries are allowed and a third still stops.
        "max_occurrences": 2,
    },
}
