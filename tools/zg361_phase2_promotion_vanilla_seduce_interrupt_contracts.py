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
            "target_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "owner": (32904,),
            "target": (32904,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "target_liege"),
            "target": ("owner", "target_liege"),
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
    "seduce_outcome.3901": {
        # CK3 1.19.0.6 target-liege discovery event. seduce_outcome.2900
        # sends this event to target.liege after the seduction succeeds and
        # discovery is important to that liege. Its only authored option
        # applies seduce_outcome_success_discovered_effect to the target, so
        # there is no inert alternative. R355 observed the played liege as
        # root with the exact inherited scheme stack plus the capital and the
        # immediate block's dummy servant. The servant is a valid character
        # scope whose bridge identity is intentionally unavailable. Each
        # independent discovered seduction may send this notification, so it
        # is repeatable inside the bounded product observation window.
        "date_raw": 53248656,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "target_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "owner": (32904,),
            "target": (32904,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "target_liege"),
            "target": ("owner", "target_liege"),
        },
        "unavailable_character_scopes": ("dummy_servant_gender",),
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "ignore_cheating_error_check": "boolean",
            "scheme_successful": "boolean",
            "discovery_chance": "value",
            "scheme_discovered": "boolean",
            "target_liege": "character",
            "capital": "landed_title",
            "dummy_servant_gender": "character",
        },
        "boolean_scopes": (
            "ignore_cheating_error_check",
            "scheme_successful",
            "scheme_discovered",
        ),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "ignore_cheating_error_check",
            "scheme_successful",
            "discovery_chance",
            "scheme_discovered",
            "target_liege",
            "capital",
            "dummy_servant_gender",
        ),),
        "saved_scope_count": 11,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


__all__ = ["VANILLA_SEDUCE_TIMELINE_CONTRACTS"]
