#!/usr/bin/env python3
"""Exact vanilla historical-character interrupts observed on the timeline."""

from __future__ import annotations

from typing import Final


VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "historical_char_creation_events.1": {
        # CK3 1.19.0.6 historical-character arrival shown to the player who
        # holds the character's origin county.  The first option switches the
        # played character, while the second recruits the historical figure
        # and creates an obligation hook.  In R372 the third option only
        # grants minor prestige: no explorer scope exists and the player is
        # human, so neither landless-adventurer branch is reachable.
        # `major` is a distinct historical character retained by the vanilla
        # pulse context; the four background scopes are authored immediately
        # before the window is rendered.  Other exact vanilla scope shapes
        # must be reviewed as separate variants when they are observed.
        "date_raw": 53436024,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "historical_character": (32904,),
            "major": (32904,),
        },
        "character_scope_differs_from": {
            "historical_character": ("major",),
            "major": ("historical_character",),
        },
        "scope_types": {
            "birth_location": "landed_title",
            "historical_character": "character",
            "major": "character",
            "county_scope": "landed_title",
            "background_terrain_scope": "landed_title",
            "background_market_scope": "province",
            "background_university_scope": "province",
            "holy_site_scope": "province",
        },
        "saved_scope_name_sets": ((
            "birth_location",
            "historical_character",
            "major",
            "county_scope",
            "background_terrain_scope",
            "background_market_scope",
            "background_university_scope",
            "holy_site_scope",
        ),),
        "saved_scope_count": 8,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS"]
