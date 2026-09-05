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
        # The authoritative L/AE/AF portfolio contains 4 + 5 + 5 stages and
        # refreshes this same player card once per pending stage.
        "max_occurrences": 14,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
