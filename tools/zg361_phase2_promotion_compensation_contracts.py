#!/usr/bin/env python3
"""Exact live contracts for Phase-2 compensation portfolio interrupts."""

from __future__ import annotations


COMPENSATION_TIMELINE_CONTRACTS: dict[str, dict[str, object]] = {
    "zg361comp.1": {
        # Player-only compensation portfolio card.  The currently selected
        # domain/stage lives on the player, not in inherited event scopes.
        # All three authored routes are visible; route 1 is the generator's
        # evidence-consistent execution path and refreshes the next card.
        "date_raw": 53157552,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": 3,
        # The event owns 14 stages × 3 authored branches.  CK3's active-event
        # header reports all 42 slots, while the exact window-context query
        # exposes only the three branches for the current stage.  R108 proved
        # this 42/3 shape on the retained product-only session.
        "snapshot_option_count": 42,
        "option_variants": tuple(
            {
                "option_count": 3,
                "native_option_indices": tuple(
                    range(stage_index * 3, stage_index * 3 + 3)
                ),
                "selected_option_number": stage_index * 3 + 1,
                "selected_native_option_index": stage_index * 3,
            }
            for stage_index in range(14)
        ),
        # The authoritative L/AE/AF portfolio contains 4 + 5 + 5 stages and
        # refreshes this same player card once per pending stage.
        "max_occurrences": 14,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
