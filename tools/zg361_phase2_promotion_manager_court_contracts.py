#!/usr/bin/env python3
"""Source-reviewed royal-court manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_COURT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "court_yearly.6030": {
        # R336 exact royal-court mockery prompt. Vanilla authors six
        # personality-gated responses, but this root exposes only authored
        # option F at native index 0. Its immediate effect has already set the
        # event cooldown; the sole visible route schedules no follow-up event.
        # Bind the selected non-player courtier and the exact 0-of-6 rendered
        # projection before acknowledging the unavoidable branch.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "6030_courtier": (32904,),
        },
        "scope_types": {
            "6030_courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("6030_courtier",),),
        "saved_scope_count": 1,
        "option_count": 1,
        "snapshot_option_count": 6,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}
