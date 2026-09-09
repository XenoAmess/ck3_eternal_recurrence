#!/usr/bin/env python3
"""Source-reviewed death-notification manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_DEATH_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "death_management.1000": {
        # Vanilla spouse-death notification. The three authored options are
        # mutually exclusive like/neutral/dislike projections. R176 observed
        # only authored option 2 because the deceased spouse was neutral; it
        # records the ordinary spouse memory/stress effect and terminates.
        "date_raw": 53159208,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "surviving_consort": 29037,
        },
        "unique_character_scope_excludes": {
            "dead_character": (29037,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "surviving_consort": "character",
            "dead_character": "character",
            "deceased_character_stress": "value",
            "realm": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "surviving_consort",
            "dead_character",
            "deceased_character_stress",
            "realm",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "option_variants": (
            {
                "saved_scope_name_sets": ((
                    "new_memory",
                    "surviving_consort",
                    "dead_character",
                    "deceased_character_stress",
                    "realm",
                    "like",
                ),),
                "saved_scope_count": 6,
                "boolean_scopes": ("like",),
                "option_count": 1,
                "snapshot_option_count": 3,
                "native_option_indices": (0,),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "saved_scope_name_sets": ((
                    "new_memory",
                    "surviving_consort",
                    "dead_character",
                    "deceased_character_stress",
                    "realm",
                    "dislike",
                ),),
                "saved_scope_count": 6,
                "boolean_scopes": ("dislike",),
                "option_count": 1,
                "snapshot_option_count": 3,
                "native_option_indices": (2,),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
        # The notification is dispatched per deceased spouse. A later spouse
        # can die in the same long observation window, so validate each typed
        # occurrence instead of imposing a campaign-global one-shot bound.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "death_management.1001": {
        # Vanilla child-death notification.  CK3 1.19.0.6 authors four
        # mutually exclusive options: the first three require an adult child
        # and split on ROOT's opinion of that child, while option 4 is the only
        # route for a minor. R248 observed the minor-child/native-3 shape;
        # R352 observed an adult child with opinion >= 40 and therefore only
        # native 0. death_management.0001 dynamically carries the dying
        # character into dead_character, then .0002 dispatches .1001 only from
        # a parent for whom that character is a child, so bind the exact typed
        # third-party role instead of one historical child's numeric ID. Both
        # observed routes record the deceased child for a possible mental
        # break and impose the source-authored stress effect; neither frame
        # exposes a less disruptive alternative.
        "date_raw": 53201424,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "dead_character": (32904,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "dead_character": "character",
            "deceased_character_stress": "value",
            "realm": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "dead_character",
            "deceased_character_stress",
            "realm",
        ),),
        "saved_scope_count": 4,
        "option_count": 1,
        "snapshot_option_count": 4,
        "native_option_indices": (3,),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": ({
            "option_count": 1,
            "snapshot_option_count": 4,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
        # The dispatch is per deceased child, not campaign-global. Validate
        # every independently typed child-death notice in the product window.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "death_management.1008": {
        # Vanilla death-of-primary-heir's-spouse notification. The source has
        # one acknowledgement-only option and performs no option effect. R364
        # observed ROOT as the parent of the surviving primary-heir spouse;
        # bind those aliases and the dynamic deceased third party exactly.
        "date_raw": 53362704,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "parent_of_spouse_of_dead_character": 32904,
        },
        "unique_character_scope_excludes": {
            "surviving_consort": (32904,),
            "dead_character": (32904,),
            "spouse_of_dead_character": (32904,),
        },
        "character_scope_matches_any": {
            "surviving_consort": ("spouse_of_dead_character",),
            "spouse_of_dead_character": ("surviving_consort",),
        },
        "character_scope_differs_from": {
            "dead_character": ("spouse_of_dead_character",),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "surviving_consort": "character",
            "dead_character": "character",
            "spouse_of_dead_character": "character",
            "parent_of_spouse_of_dead_character": "character",
            "deceased_character_stress": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "surviving_consort",
            "dead_character",
            "spouse_of_dead_character",
            "parent_of_spouse_of_dead_character",
            "deceased_character_stress",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # Dispatch is per deceased child's spouse, not campaign-global.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
