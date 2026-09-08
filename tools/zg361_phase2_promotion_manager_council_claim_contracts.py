#!/usr/bin/env python3
"""Source-reviewed council claim-fabrication notification contracts."""

from __future__ import annotations

from typing import Final


MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "court_chaplain_task.0313": {
        # CK3 1.19.0.6 notifies the duchy holder after another ruler has
        # already accepted a fabricated duchy claim and paid its cost. This
        # is a political council-task result, not faith conversion. Immediate
        # only repeats the already-granted claim as a tooltip; the sole option
        # applies the holder's fixed opinion modifier toward the claimant and
        # has no follow-up. R343 observed this exact seven-scope projection.
        "date_raw": 53227008,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "duchy_holder": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "councillor_liege": (29037,),
            "county_holder": (29037,),
        },
        "character_scope_differs_from": {
            "councillor": (
                "councillor_liege",
                "county_holder",
                "duchy_holder",
            ),
            "councillor_liege": ("county_holder", "duchy_holder"),
            "county_holder": ("duchy_holder",),
        },
        "scope_types": {
            "councillor": "character",
            "councillor_liege": "character",
            "province": "province",
            "county": "landed_title",
            "county_holder": "character",
            "duchy": "landed_title",
            "duchy_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "province",
            "county",
            "county_holder",
            "duchy",
            "duchy_holder",
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}
