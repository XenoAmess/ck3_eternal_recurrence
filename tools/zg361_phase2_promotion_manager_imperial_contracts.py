#!/usr/bin/env python3
"""Source-reviewed imperial manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_IMPERIAL_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_emperor_yearly.8000": {
        # Options 1-3 each move manpower from one random governor county: that
        # county loses ten percent development (rounded up), receives the
        # lighter ten-year sacrifice modifier, and its governor loses 20
        # opinion of root. Option 4 instead removes two development from the
        # player's capital and applies the strictly heavier waning modifier.
        # Choose option 1 to preserve the acceptance owner's capital. Bind the
        # complete authored random frame: the source guarantees three distinct
        # governors, but deliberately does not guarantee their identities.
        "date_raw": 53150712,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suggestor": (29037,),
            "governor_1": (29037,),
            "governor_2": (29037,),
            "governor_3": (29037,),
        },
        "character_scope_differs_from": {
            "governor_1": ("governor_2", "governor_3"),
            "governor_2": ("governor_1", "governor_3"),
            "governor_3": ("governor_1", "governor_2"),
        },
        "scope_types": {
            "suggestor": "character",
            "minimum_development": "value",
            "governor_1": "character",
            "county_1": "landed_title",
            "governor_2": "character",
            "county_2": "landed_title",
            "governor_3": "character",
            "county_3": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "suggestor",
            "minimum_development",
            "governor_1",
            "county_1",
            "governor_2",
            "county_2",
            "governor_3",
            "county_3",
        ),),
        "saved_scope_count": 8,
        "option_count": 4,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            # R335 exact source-authored partial selection. The event trigger
            # guarantees three governors somewhere in the realm, but the
            # developed_governors list used by immediate can contain only two
            # eligible distinct entries. Vanilla's three-iteration while then
            # saves only pairs 1/2; option C (native 2) is hidden. Preserve the
            # same native-0 route, which still avoids damaging root's capital.
            "saved_scope_names": (
                "suggestor",
                "minimum_development",
                "governor_1",
                "county_1",
                "governor_2",
                "county_2",
            ),
            "unique_character_scope_excludes": {
                "suggestor": (29037,),
                "governor_1": (29037,),
                "governor_2": (29037,),
            },
            "character_scope_differs_from": {
                "governor_1": ("governor_2",),
                "governor_2": ("governor_1",),
            },
            "scope_types": {
                "suggestor": "character",
                "minimum_development": "value",
                "governor_1": "character",
                "county_1": "landed_title",
                "governor_2": "character",
                "county_2": "landed_title",
            },
            "saved_scope_count": 6,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (0, 1, 3),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
    },
}
