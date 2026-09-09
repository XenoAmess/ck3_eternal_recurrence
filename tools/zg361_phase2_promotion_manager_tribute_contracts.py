#!/usr/bin/env python3
"""Source-reviewed tribute-mission manager interrupt contracts."""

from __future__ import annotations

from typing import Final


_RESOURCE_TRIBUTE_TYPES = ("gold", "herd")


def _resource_reward_scope_variant(resource_type: str) -> dict[str, object]:
    resource_scopes = tuple(
        f"{size}_{resource_type}_tribute"
        for size in ("small", "adequate", "excessive")
    )
    return {
        "saved_scope_names": (
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            *resource_scopes,
            "tribute_mission_target",
            "tributary_scope",
            "overlord_scope",
            "receiving_character",
            "opinion_of_tributary",
            "tribute_reward_type_treasury",
            "saved_innovation",
            "decided_on_treasury_reward",
        ),
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "tributary_scope": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": resource_scopes,
        "saved_scope_count": 16,
    }


MANAGER_TRIBUTE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tribute_mission.1002": {
        # CK3 1.19.0.6 human-tribute receipt. R136 observed a concubine
        # tribute: authored option 3 was hidden, leaving native indices
        # 0/1/3. R354 observed the source-defined eunuch branch: authored
        # option 2 was hidden, leaving 0/2/3. The final authored option
        # declines either character and changes no product state. The event
        # still advances to its vanilla reward decision, which must be
        # reviewed under its own exact contract when observed. Tribute
        # missions can recur for the same receiving ruler, so this receipt
        # event has no lifecycle occurrence ceiling inside one product
        # observation window either.
        "date_raw": 53150160,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "tribute_mission_target": 29037,
            "overlord_scope": 29037,
            "receiving_character": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "tributary_scope": (29037,),
            "concubine_character": (29037,),
            "human_tribute": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
            "secondary_recipient": (
                "concubine_character",
                "human_tribute",
            ),
            "concubine_character": (
                "secondary_recipient",
                "human_tribute",
            ),
            "human_tribute": (
                "secondary_recipient",
                "concubine_character",
            ),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {
            "opinion_of_tributary": "value",
            "tribute_reward_type_treasury": "value",
            "saved_innovation": "culture_innovation",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "tribute_mission_target",
            "tributary_scope",
            "overlord_scope",
            "receiving_character",
            "opinion_of_tributary",
            "concubine_character",
            "human_tribute",
            "tribute_reward_type_treasury",
            "saved_innovation",
        ),),
        "scope_variants": (
            {
                "saved_scope_names": (
                    "actor",
                    "recipient",
                    "secondary_actor",
                    "secondary_recipient",
                    "intermediary",
                    "tribute_mission_target",
                    "tributary_scope",
                    "overlord_scope",
                    "receiving_character",
                    "opinion_of_tributary",
                    "concubine_character",
                    "human_tribute",
                    "tribute_reward_type_treasury",
                    "saved_innovation",
                ),
                "native_option_indices": (0, 1, 3),
            },
            {
                "saved_scope_names": (
                    "actor",
                    "recipient",
                    "secondary_actor",
                    "secondary_recipient",
                    "intermediary",
                    "tribute_mission_target",
                    "tributary_scope",
                    "overlord_scope",
                    "receiving_character",
                    "opinion_of_tributary",
                    "eunuch_character",
                    "human_tribute",
                    "tribute_reward_type_treasury",
                    "saved_innovation",
                ),
                "unique_character_scope_excludes": {
                    "actor": (29037,),
                    "secondary_recipient": (29037,),
                    "tributary_scope": (29037,),
                    "eunuch_character": (29037,),
                    "human_tribute": (29037,),
                },
                "character_scope_matches_any": {
                    "tributary_scope": ("actor",),
                    "secondary_recipient": (
                        "eunuch_character",
                        "human_tribute",
                    ),
                    "eunuch_character": (
                        "secondary_recipient",
                        "human_tribute",
                    ),
                    "human_tribute": (
                        "secondary_recipient",
                        "eunuch_character",
                    ),
                },
                "native_option_indices": (0, 2, 3),
            },
        ),
        "saved_scope_count": 14,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "tribute_mission.1005": {
        # Reward decision after either a human-tribute route or the direct
        # non-human tribute route. Native option 4 (monk) is hidden in the
        # reviewed frames. Native option 5 grants generic legitimacy to the
        # AI tributary without a player resource cost. Tribute missions can
        # recur for the same receiving ruler, so the event has no lifecycle
        # occurrence ceiling inside one product-observation window.
        "date_raw": 53150184,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "tribute_mission_target": 29037,
            "overlord_scope": 29037,
            "receiving_character": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "tributary_scope": (29037,),
            "human_tribute": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
            "secondary_recipient": (
                "concubine_character",
                "human_tribute",
            ),
            "human_tribute": (
                "secondary_recipient",
                "concubine_character",
            ),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {
            "opinion_of_tributary": "value",
            "tribute_reward_type_treasury": "value",
            "saved_innovation": "culture_innovation",
            "decided_on_treasury_reward": "flag",
        },
        "optional_scope_types": {
            "concubine_character": "character",
            "rejected_concubine": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "concubine_character",
                "human_tribute",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "rejected_concubine",
                "decided_on_treasury_reward",
            ),
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "human_tribute",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "decided_on_treasury_reward",
            ),
        ),
        "scope_variants": ({
            # Direct non-human route without interaction option booleans.
            "saved_scope_names": (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "decided_on_treasury_reward",
            ),
            "unique_character_scope_excludes": {
                "actor": (29037,),
                "secondary_recipient": (29037,),
                "tributary_scope": (29037,),
            },
            "character_scope_matches_any": {
                "tributary_scope": ("actor",),
            },
            "saved_scope_count": 13,
        },) + tuple(
            # Character-interaction routes retain all three typed option
            # booleans. R188 observed gold; herd is its exact source sibling.
            _resource_reward_scope_variant(resource_type)
            for resource_type in _RESOURCE_TRIBUTE_TYPES
        ),
        "option_count": 6,
        "snapshot_option_count": 7,
        "native_option_indices": (0, 1, 2, 3, 5, 6),
        "selected_option_number": 6,
        "selected_native_option_index": 5,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
