#!/usr/bin/env python3
"""Exact vanilla Roads-to-Power emperor interrupts on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_emperor_yearly.2211": {
        # CK3 1.19.0.6 response to a vassal's claimed appointment prophecy.
        # Authored option A is hidden in the R250 frame, leaving B/D/C at
        # native indices 1/2/3.  B creates a favor hook (or grants influence),
        # D installs a 25-year modifier, and both A/B alter appointment
        # investment.  Authored option C is the bounded terminal route: it
        # only transfers minor influence in opposite directions and schedules
        # no follow-up event, hook, modifier, or appointment mutation.
        "date_raw": 53206512,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "liege": 32904,
            "vassal": 27275,
        },
        "scope_types": {
            "potential_title": "landed_title",
            "liege": "character",
            "vassal": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "potential_title",
            "liege",
            "vassal",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
}
