#!/usr/bin/env python3
"""Exact CK3 1.19.0.6 contracts for observed seduce outcome notices."""

from __future__ import annotations

from typing import Final


VANILLA_SEDUCE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "seduce_outcome.4900": {
        # R328 observed the target liege's mandatory notification after an
        # unrelated courtier's failed seduction. CK3 1.19.0.6 authors exactly
        # one option; it applies the already-determined publicised-crime
        # outcome and offers no alternative branch. Bind the complete saved
        # scope set before acknowledging that sole terminal option.
        "date_raw": 53215752,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "owner": 30320,
            "target": 37337,
            "target_liege": 32904,
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "ignore_cheating_error_check": "boolean",
            "discovery_chance": "value",
            "scheme_discovered": "boolean",
            "target_liege": "character",
        },
        "boolean_scopes": (
            "ignore_cheating_error_check",
            "scheme_discovered",
        ),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "ignore_cheating_error_check",
            "discovery_chance",
            "scheme_discovered",
            "target_liege",
        ),),
        "saved_scope_count": 8,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}


__all__ = ["VANILLA_SEDUCE_TIMELINE_CONTRACTS"]
