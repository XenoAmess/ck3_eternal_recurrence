#!/usr/bin/env python3
"""Source-reviewed royal-court manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_COURT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "major_decisions.2011": {
        # R348 exact university-scholar arrival prompt. Vanilla immediate has
        # already created and employed the skilled courtier. Native option 0
        # keeps that courtier; native option 1 sends them back to the pool and
        # terminates without scheduling a follow-up event. Bind the observed
        # dynamic non-player courtier and exact two-option projection before
        # taking that minimal opt-out route.
        "date_raw": 53215344,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "new_courtier": (32904,),
        },
        "scope_types": {
            "new_courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("new_courtier",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
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
    "court_yearly.6040": {
        # R366 exact scrounger prompt. Native option 0 is unavailable because
        # its authored scrounger-eligibility/root-capacity conjunction is false
        # in this projection; the native window does not expose which operand.
        # Native 1 spends gold and schedules the 6041 follow-up; native 2 is
        # terminal, removes the selected scrounger and reduces player stress.
        # Bind the source-selected non-player character, the shared-trait
        # helper scopes and the exact native 1/2 projection before choosing
        # the no-follow-up route. Vanilla uses a 20-year cooldown rather than
        # a lifetime flag, so a long product run may legitimately see it again.
        "date_raw": 53361816,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "scrounger": (32904,),
        },
        "scope_types": {
            "scrounger": "character",
            "has_shared_trait": "flag",
        },
        "boolean_scopes": ("shared_trait_flag_applied",),
        "saved_scope_name_sets": ((
            "scrounger",
            "shared_trait_flag_applied",
            "has_shared_trait",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
