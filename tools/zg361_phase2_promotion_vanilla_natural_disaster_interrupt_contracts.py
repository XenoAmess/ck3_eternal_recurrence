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

_NATURAL_DISASTER_8001_SCOPE_TYPES: Final = {
    "situation": "situation",
    "situation_sub_region": "situation_sub_region",
    "situation_participant_group": "situation_participant_group",
    "disaster_province": "province",
    "great_project": "great_project",
    "epicenter_county": "landed_title",
}

_NATURAL_DISASTER_8001_RIVER_SAVED_SCOPE_NAMES: Final = (
    *_NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES,
    "river_region",
)


VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "natural_disaster.8001": {
        # CK3 1.19.0.6 warning-phase join event.  Its sole authored option
        # invokes only natural_disaster_warning_tooltip_effect, so native0 is
        # the unavoidable acknowledgement and adds no option-side mutation.
        # R247 observed the eight-scope earthquake shape. R355 observed the
        # exact flood sibling, where natural_disaster_save_base_scopes_effect
        # adds river_region from the situation variable. Independent warning
        # situations may legitimately send this event again, so recurrence is
        # bounded by the product observation window rather than a whole-run
        # occurrence count.
        "date_raw": 53204688,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "ruler": 32904,
            "disaster_province_ruler": 32904,
        },
        "scope_types": _NATURAL_DISASTER_8001_SCOPE_TYPES,
        "saved_scope_name_sets": (
            _NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES,
        ),
        "saved_scope_count": 8,
        "scope_variants": ({
            "saved_scope_names": (
                _NATURAL_DISASTER_8001_RIVER_SAVED_SCOPE_NAMES
            ),
            "saved_scope_count": 9,
            "scope_types": {
                **_NATURAL_DISASTER_8001_SCOPE_TYPES,
                "river_region": "geographical_region",
            },
        },),
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "natural_disaster.7021": {
        # CK3 1.19.0.6 flood-warning pulse selected by
        # natural_disaster_warning_events. Native option 0 adds stress and
        # enters manage-from-home power sharing; native option 1 opens the
        # isolation decision. Both are hidden once their gates fail. Native
        # option 2 only renders the warning tooltip, while the event's common
        # after block records that the first warning was received. R355 shows
        # the exact first-warning projection with native options (0, 2), so
        # choose terminal native2 and bind the complete flood scope stack.
        "date_raw": 53255112,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "epicenter_county": "landed_title",
            "river_region": "geographical_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
            "epicenter_county",
            "river_region",
        ),),
        "saved_scope_count": 4,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "natural_disaster.6901": {
        # CK3 1.19.0.6 recovery-phase start notice for each independent
        # affected ruler. natural_disaster_save_base_scopes_effect has already
        # published the exact flood context before the situation dispatches
        # this event. Its sole authored option is empty, so native0 is the
        # unavoidable terminal acknowledgement. Independent disasters may
        # legitimately deliver the event again within the bounded timeline.
        "date_raw": 53256312,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "epicenter_county": "landed_title",
            "river_region": "geographical_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
            "epicenter_county",
            "river_region",
        ),),
        "saved_scope_count": 4,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "travel_danger_events.3002": {
        # CK3 1.19.0.6 avalanche follow-up letter to the province owner. Route
        # A applies the four-year avalanche_impact province penalty; route B
        # spends minor gold but leaves the province unchanged. Prefer B so a
        # random travel consequence does not distort the long manager-cycle
        # observation. The traveler, optional travel leader, and news bearer
        # are dynamically selected for each avalanche and therefore bind by
        # native type, not one frozen campaign identity.
        "date_raw": 53373936,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "travel_plan": "travel_plan",
            "travel_leader": "character",
            "avalanche_traveler": "character",
            "avalanche_location": "province",
            "news_bearer": "character",
        },
        "saved_scope_name_sets": ((
            "travel_plan",
            "travel_leader",
            "avalanche_traveler",
            "avalanche_location",
            "news_bearer",
        ),),
        "saved_scope_count": 5,
        "scope_variants": ({
            # .3001 saves travel_leader through ?=, so an otherwise valid
            # travel plan without a leader legally carries only four scopes.
            "saved_scope_names": (
                "travel_plan",
                "avalanche_traveler",
                "avalanche_location",
                "news_bearer",
            ),
            "saved_scope_count": 4,
            "scope_types": {
                "travel_plan": "travel_plan",
                "avalanche_traveler": "character",
                "avalanche_location": "province",
                "news_bearer": "character",
            },
        },),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # Independent avalanches can notify the same province owner again.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
