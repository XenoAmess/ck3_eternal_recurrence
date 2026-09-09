#!/usr/bin/env python3
"""Exact vanilla dynastic-cycle interrupts observed on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle.0091": {
        # CK3 1.19.0.6 transition notice sent to the current China holder when
        # the dynastic-cycle situation enters Instability. The immediate block
        # has already notified other relevant players; its sole option is an
        # empty acknowledgement. A later dynastic cycle can enter Instability
        # again, so recurrence is bounded by the observation window rather
        # than by one frozen campaign occurrence.
        "date_raw": 53436024,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
        ),),
        "saved_scope_count": 2,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
