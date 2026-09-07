#!/usr/bin/env python3
"""Source-reviewed befriend-outcome manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_BEFRIEND_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "befriend_outcome.0002": {
        # CK3 1.19.0.6 target-side befriend outcome.  The source saves exactly
        # one outcome flag: scheme_successful for success or scheme_failed for
        # failure.  Those branches expose different first options, so bind
        # the flag and complete rendered projection as a pair.  Authored
        # option 3 (native 2) is the terminal gentle rejection in both cases;
        # it avoids creating a durable friendship and avoids the harsher
        # authored option 4 rejection.
        "date_raw": 53164584,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "target": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "scheme_successful": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "scheme_successful",
        ),),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 2, 3),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": ({
            # R164 critical-success projection.
            "scope_types": {
                "scheme": "scheme",
                "owner": "character",
                "artifact": "artifact",
                "scheme_successful": "flag",
            },
            "saved_scope_name_sets": ((
                "scheme",
                "owner",
                "artifact",
                "target",
                "scheme_successful",
            ),),
            "saved_scope_count": 5,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (0, 2, 3),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }, {
            # R202 failure projection.  Authored option 1 is hidden; options
            # 2/3/4 remain visible as native indices 1/2/3.
            "scope_types": {
                "scheme": "scheme",
                "owner": "character",
                "artifact": "artifact",
                "scheme_failed": "flag",
            },
            "saved_scope_name_sets": ((
                "scheme",
                "owner",
                "artifact",
                "target",
                "scheme_failed",
            ),),
            "saved_scope_count": 5,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (1, 2, 3),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }),
        "max_occurrences": 1,
    },
}
