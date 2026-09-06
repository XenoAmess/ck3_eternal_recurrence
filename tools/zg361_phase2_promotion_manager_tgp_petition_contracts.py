#!/usr/bin/env python3
"""Source-reviewed TGP movement-petition manager interrupt contracts."""

from __future__ import annotations

from typing import Final


_LAW_DIRECTION_SCOPES = (
    "increase_law",
    "decrease_law",
    "increase_army_law",
    "decrease_army_law",
)

_PROVINCE_TYPE_SCOPES = (
    "province_metropolitan",
    "province_industrial",
    "province_military",
    "province_protectorate",
)

_PROVINCE_MEMBER_SHAPES = (
    ("other_movement_member",),
    ("house_movement_member", "other_movement_member"),
    (
        "other_movement_member",
        "house_movement_member",
        "disciple_movement_member",
    ),
)


def _province_petition_scope_variant(
    province_scope: str, member_scopes: tuple[str, ...]
) -> dict[str, object]:
    """Return one exact source-authored province-petition scope shape."""

    character_scopes = (*member_scopes, "province_change_recipient")
    return {
        "saved_scope_names": (
            "petitioner",
            "actors_movement",
            "hegemon",
            "petition_recipient",
            province_scope,
            *character_scopes,
        ),
        "saved_scope_count": 5 + len(character_scopes),
        "scope_types": {
            "petitioner": "character",
            "actors_movement": "situation_participant_group",
            **{name: "character" for name in character_scopes},
        },
        "boolean_scopes": (province_scope,),
        "unique_character_scope_excludes": {
            "petitioner": (29037,),
            **{name: (29037,) for name in character_scopes},
        },
        "character_scope_matches_any": {
            "province_change_recipient": member_scopes,
        },
    }


MANAGER_TGP_PETITION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_decision_events.0101": {
        # CK3 1.19.0.6 movement-petition decision delivered to the played
        # hegemon. Option 1 applies the request and option 2 opens a follow-up
        # chain. Authored option 3 refuses, clears the petition variables, and
        # does not mutate the Phase-2 state machine, so it is the bounded route
        # for this unrelated interruption.
        "date_raw": 53156928,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "hegemon": 29037,
            "petition_recipient": 29037,
        },
        "unique_character_scope_excludes": {
            "petitioner": (29037,),
            "other_movement_member": (29037,),
            "province_change_recipient": (29037,),
        },
        "character_scope_matches_any": {
            "other_movement_member": ("province_change_recipient",),
            "province_change_recipient": ("other_movement_member",),
        },
        "scope_types": {
            "petitioner": "character",
            "actors_movement": "situation_participant_group",
            "other_movement_member": "character",
            "province_change_recipient": "character",
        },
        "boolean_scopes": ("province_metropolitan",),
        "saved_scope_name_sets": ((
            "petitioner",
            "actors_movement",
            "hegemon",
            "petition_recipient",
            "province_metropolitan",
            "other_movement_member",
            "province_change_recipient",
        ),),
        "saved_scope_count": 7,
        "scope_variants": tuple({
            # The exact-build law decision saves one boolean direction scope
            # and no province/member recipients. R164/R166 observed two of
            # these source-authored siblings; all four have the same shape.
            "saved_scope_names": (
                "petitioner",
                "actors_movement",
                "hegemon",
                "petition_recipient",
                direction_scope,
            ),
            "saved_scope_count": 5,
            "scope_types": {
                "petitioner": "character",
                "actors_movement": "situation_participant_group",
            },
            "boolean_scopes": (direction_scope,),
            "unique_character_scope_excludes": {"petitioner": (29037,)},
            "character_scope_matches_any": {},
        } for direction_scope in _LAW_DIRECTION_SCOPES) + tuple(
            # Exact-build source .0100 exposes four province-type branches.
            # R175/R185 observed house/other recipient selection and R186
            # observed the industrial sibling. Enumerate the source-authored
            # cross product while retaining exact names and recipient identity.
            _province_petition_scope_variant(province_scope, member_scopes)
            for province_scope in _PROVINCE_TYPE_SCOPES
            for member_scopes in _PROVINCE_MEMBER_SHAPES
        ),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        # R163/R164 observed two independent movement petitions in one bounded
        # natural-cycle wait. Keep the allowance evidence-bound.
        "max_occurrences": 2,
    },
}
