#!/usr/bin/env python3
"""Source-reviewed chancellor-task manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_CHANCELLOR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "chancellor_task.1002": {
        # CK3 1.19.0.6 chancellor bad-side-effect notice. Immediate has
        # already frozen the current councillor and a distinct truce holder.
        # The sole authored option is unavoidable and only cancels that
        # target's one-way truce against the played root. R284 observed the
        # exact three-character frame and native option index 0.
        "date_raw": 53209248,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "councillor_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "councillor": (32904,),
            "target": (32904,),
        },
        "character_scope_differs_from": {
            "councillor": ("target",),
            "target": ("councillor",),
        },
        "scope_types": {
            "councillor": "character",
            "councillor_liege": "character",
            "target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "target",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}
