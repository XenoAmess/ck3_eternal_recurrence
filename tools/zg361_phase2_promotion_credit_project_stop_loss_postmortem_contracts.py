#!/usr/bin/env python3
"""Exact credit/project R-domain stop-loss/postmortem contracts."""

from __future__ import annotations

from typing import Final

from zg361_phase2_promotion_credit_project_governance_contracts import (
    CREDIT_PROJECT_R_CHARACTER_SCOPES,
    CREDIT_PROJECT_R_SAVED_SCOPE_NAMES,
)


CREDIT_PROJECT_STOP_LOSS_POSTMORTEM_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361cp.132": {
        # R238 reached stop-loss judgment with the capacity retained by .66B.
        # Route A releases all remaining capacity, closes the project, records
        # evidence 80, no avoidable delay and judgment 1. Route B performs the
        # same release with weaker evidence/delay, while C opens debt. Choose A
        # to settle deterministically and advance R 4 -> 5.
        "date_raw": 53187624,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": CREDIT_PROJECT_R_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in CREDIT_PROJECT_R_SAVED_SCOPE_NAMES
            if name not in CREDIT_PROJECT_R_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (CREDIT_PROJECT_R_SAVED_SCOPE_NAMES,),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
