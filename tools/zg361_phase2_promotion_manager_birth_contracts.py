#!/usr/bin/env python3
"""Source-reviewed birth-notice manager interrupt contracts."""

from __future__ import annotations

from typing import Final


_BIRTH_BOOLEAN_SCOPES = (
    "is_bastard",
    "is_child_of_concubine",
    "matrilineal",
)


MANAGER_BIRTH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "birth.3035": {
        # CK3 1.19.0.6 parent-side sickly-child recovery notice. birth.3034
        # has already removed sickly from scope:child before it notifies the
        # parents; this window only repeats that result as a tooltip and its
        # sole option is inert. R283 observed the played parent as root with
        # one distinct child scope and native option index 0.
        "date_raw": 53208048,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (32904,),
        },
        "scope_types": {
            "child": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("child",),),
        "saved_scope_count": 1,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.3032": {
        # CK3 1.19.0.6 father-side sickly-child notice. The mother-side event
        # has already assigned sickly before this window; immediate only
        # repeats that fact as a tooltip and the sole option is inert. R191
        # observed it inheriting the same complete non-twin birth frame.
        "date_raw": 53176080,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "father": 29037,
            "real_father": 29037,
        },
        "unique_character_scope_excludes": {
            "child": (29037,),
            "mother": (29037,),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother"),
            "mother": ("father", "real_father", "child"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.1003": {
        # CK3 1.19.0.6 father-side regular birth notice. Birth and the child's
        # default name already exist before this window. Its sole non-twin
        # option is inert except for one hard-coded historical-character case
        # that cannot match the bound player. R189 observed the seven-scope
        # non-twin frame with the played father also bound as real_father.
        "date_raw": 53175528,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "father": 29037,
            "real_father": 29037,
        },
        "unique_character_scope_excludes": {
            "child": (29037,),
            "mother": (29037,),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother"),
            "mother": ("father", "real_father", "child"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.1010": {
        # CK3 1.19.0.6 dynasty-host naming notice. The birth and default name
        # already exist before this window; its sole authored option has no
        # gameplay effect. Bind every complete eight-scope frame before
        # dismissing the acknowledgement; the runner never operates the name
        # widget. R180 observed two occurrences in one bounded timeline.
        "date_raw": 53154408,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (29037,),
            "father": (29037,),
            "real_father": (29037,),
            "mother": (29037,),
            "spouse_of_mother": (29037,),
        },
        "character_scope_matches_any": {
            "father": ("real_father", "spouse_of_mother"),
            "real_father": ("father", "spouse_of_mother"),
            "spouse_of_mother": ("father", "real_father"),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother", "spouse_of_mother"),
            "mother": ("father", "real_father", "spouse_of_mother"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
            "spouse_of_mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
            "spouse_of_mother",
        ),),
        "saved_scope_count": 8,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 2,
    },
}
