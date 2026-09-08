#!/usr/bin/env python3
"""Exact vanilla intrigue-temptation interrupt on the promotion timeline."""

from __future__ import annotations

from typing import Final


VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "intrigue_temptation.3020": {
        # CK3 1.19.0.6 common intrigue-lifestyle event. Authored option A
        # scans rulers and their families, then immediately starts the
        # multi-card 3021/3022 romantic-candidate chain. Authored option B is
        # terminal and only adds intrigue_picky_about_partners for five years.
        # R322 observed this exact root/quarter/two-option frame within the
        # product timeline, 48 in-game hours after the last clean observation.
        # Take terminal native1 so the unrelated story cannot occupy the
        # promotion-source timeline.
        "date_raw": 53170824,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {
            "quarter": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("quarter",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}
