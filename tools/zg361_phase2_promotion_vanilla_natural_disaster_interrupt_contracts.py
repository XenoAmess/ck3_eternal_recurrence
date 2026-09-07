#!/usr/bin/env python3
"""Exact vanilla natural-disaster interrupts observed on the promotion timeline."""

from __future__ import annotations

from typing import Final


_NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES: Final = (
    "situation",
    "situation_sub_region",
    "situation_participant_group",
    "ruler",
    "disaster_province",
    "disaster_province_ruler",
    "great_project",
    "epicenter_county",
)


VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "natural_disaster.8001": {
        # CK3 1.19.0.6 warning-phase join event.  Its sole authored option
        # invokes only natural_disaster_warning_tooltip_effect, so native0 is
        # the unavoidable acknowledgement and adds no option-side mutation.
        # R247 supplies one exact live occurrence.  Keep the occurrence cap at
        # that evidence boundary; any later disaster needs an independently
        # exact frame before the retained path may acknowledge it.
        "date_raw": 53204688,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "ruler": 32904,
            "disaster_province_ruler": 32904,
        },
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "situation_participant_group": "situation_participant_group",
            "disaster_province": "province",
            "great_project": "great_project",
            "epicenter_county": "landed_title",
        },
        "saved_scope_name_sets": (
            _NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES,
        ),
        "saved_scope_count": 8,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}
