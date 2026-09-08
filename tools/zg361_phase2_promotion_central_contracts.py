#!/usr/bin/env python3
"""Exact live contracts for Phase-2 central orchestration interrupts."""

from __future__ import annotations


CENTRAL_TIMELINE_CONTRACTS: dict[str, dict[str, object]] = {
    "zg361p2c.2": {
        # The central layer's sole player-visible terminal summary.  It reads
        # only the frozen cycle/case values; every other live saved scope is
        # inherited from upstream product windows and is intentionally not a
        # dependency.  The sole option clears summary_pending.
        "date_raw": 53159664,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {
            "zg361_p2c_summary_cycle": "value",
            "zg361_p2c_summary_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # R340 observed one summary for the inherited Central completion and
        # a second after the next product cycle at 53217456. The current
        # three-cycle source route must acknowledge both, while the sole
        # authored option remains the exact summary_pending clear operation.
        "max_occurrences": 2,
    },
}
