#!/usr/bin/env python3
"""Source-reviewed TGP treasury-ministry manager interrupt contracts."""

from __future__ import annotations

from typing import Final


_TREASURY_PREFERENCE_SCOPES = (
    "ministry_budget",
    "military_budget",
    "hegemon_budget",
    "meritocratic_salary_budget",
    "meritocratic_military_budget",
)


MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_china_ministry.0100": {
        # CK3 1.19.0.6 treasury-budget renewal for the top liege. Option 1
        # opens the picker and option 3 enacts the steward's preference.
        # Option 2 preserves the current allocation and terminates. The event
        # source saves exactly one preference scope on root; bind each authored
        # celestial/meritocratic name instead of accepting arbitrary scopes.
        "date_raw": 53163168,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "treasury_ruler": 29037,
            "salary_budget": 29037,
        },
        "unique_character_scope_excludes": {"steward": (29037,)},
        "scope_types": {"steward": "character"},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "treasury_ruler",
            "steward",
            "salary_budget",
        ),),
        "saved_scope_count": 3,
        "scope_variants": tuple({
            "saved_scope_names": (
                "treasury_ruler",
                "steward",
                preference_scope,
            ),
            "saved_scope_count": 3,
            "character_scopes": {
                "treasury_ruler": 29037,
                preference_scope: 29037,
            },
            "scope_types": {"steward": "character"},
            "unique_character_scope_excludes": {"steward": (29037,)},
        } for preference_scope in _TREASURY_PREFERENCE_SCOPES),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # yearly_on_actions delivers this event every year and the source
        # admits another player renewal after 96 months, or earlier when the
        # treasury capacity/deficit branches require it.  It is therefore a
        # renewable budget prompt, not a once-per-observation interrupt.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
