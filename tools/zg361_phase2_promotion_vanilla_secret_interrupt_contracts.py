#!/usr/bin/env python3
"""Exact vanilla secret interrupts observed on the promotion timeline."""

from __future__ import annotations

from typing import Final


_VANILLA_SECRET_0122_SAVED_SCOPE_NAMES: Final = (
    "secret_owner",
    "secret_target",
    "secret_exposer",
    "secret",
    "siphoned_treasury_victim",
    "embezzlement_stake",
    "embezzlement_stake_half",
    "embezzler",
    "victim",
    "exposed_secret_target",
    "local_secret_owner",
    "secret_owner_is_vassal",
    "liege",
)

_VANILLA_SECRET_0122_CHARACTER_SCOPES: Final = {
    "secret_target": 32904,
    "siphoned_treasury_victim": 32904,
    "victim": 32904,
    "exposed_secret_target": 32904,
    "liege": 32904,
}


VANILLA_SECRET_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "secrets.0108": {
        # CK3 1.19.0.6 notification that two cared-about characters were
        # exposed as lovers. In this exact frame neither imprisonment option
        # is legal, so authored option A is the sole rendered route and has no
        # option-body effect. Independent exposed secrets can notify the
        # player repeatedly; validate every delivery without a global cap.
        "date_raw": 53358504,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {"event_root": 32904},
        "unique_character_scope_excludes": {
            name: (32904,)
            for name in (
                "secret_owner",
                "secret_target",
                "secret_exposer",
                "target",
                "owner",
                "local_secret_owner",
                "sex_partner",
                "adulterer_check",
                "primary_character",
                "secondary_character",
                "left_portrait",
                "right_portrait",
            )
        },
        "character_scope_matches_any": {
            "secret_exposer": ("secret_owner",),
            "owner": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
            "adulterer_check": ("secret_owner",),
            "primary_character": ("secret_owner",),
            "left_portrait": ("secret_owner",),
            "target": ("secret_target",),
            "sex_partner": ("secret_target",),
            "secondary_character": ("secret_target",),
            "right_portrait": ("secret_target",),
        },
        "character_scope_differs_from": {
            "secret_owner": ("secret_target",),
            "secret_target": ("secret_owner",),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_target": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "target": "character",
            "owner": "character",
            "local_secret_owner": "character",
            "sex_partner": "character",
            "adulterer_check": "character",
            "targets_secret": "secret",
            "event_root": "character",
            "primary_character": "character",
            "secondary_character": "character",
            "lover_reaction": "flag",
            "left_portrait": "character",
            "right_portrait": "character",
        },
        "saved_scope_name_sets": ((
            "secret_owner", "secret_target", "secret_exposer", "secret",
            "target", "owner", "local_secret_owner", "sex_partner",
            "adulterer_check", "targets_secret", "event_root",
            "primary_character", "secondary_character", "lover_reaction",
            "left_portrait", "right_portrait",
        ),),
        "boolean_scopes": (),
        "saved_scope_count": 16,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "secrets.0112": {
        # CK3 1.19.0.6 notification that a cared-about character was exposed
        # as an illegitimate child or parent. In the reviewed non-consort
        # frame the only rendered route is authored option A, whose option
        # body is empty; the secret type applied gameplay consequences before
        # dispatching this notification. Independent secrets can produce it any
        # number of times, so each delivery is revalidated without a cap.
        "date_raw": 53358504,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            name: (32904,)
            for name in (
                "secret_owner",
                "secret_target",
                "secret_exposer",
                "owner",
                "child",
                "mother",
                "real_father",
                "local_secret_owner",
                "target",
            )
        },
        "character_scope_matches_any": {
            "owner": ("secret_owner",),
            "mother": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
            "child": ("secret_target",),
            "target": ("secret_target",),
            "real_father": ("secret_exposer",),
        },
        "character_scope_differs_from": {
            "secret_owner": ("secret_target", "secret_exposer"),
            "secret_target": ("secret_owner", "secret_exposer"),
            "secret_exposer": ("secret_owner", "secret_target"),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_target": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "owner": "character",
            "child": "character",
            "mother": "character",
            "real_father": "character",
            "local_secret_owner": "character",
            "lover_secret_to_expose": "secret",
            "target": "character",
        },
        "saved_scope_name_sets": ((
            "secret_owner",
            "secret_target",
            "secret_exposer",
            "secret",
            "owner",
            "child",
            "mother",
            "real_father",
            "local_secret_owner",
            "lover_secret_to_expose",
            "target",
        ),),
        "boolean_scopes": (),
        "saved_scope_count": 11,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "secrets.0122": {
        # CK3 1.19.0.6 embezzlement exposure. R231 and R290 prove that the
        # embezzler is the current secret owner rather than one stable seed
        # character. The secret type saves ``embezzler`` from secret_owner,
        # while secret_exposed_owner_effects_effect saves
        # ``local_secret_owner`` from the same source. Bind those authored
        # aliases instead of either incidental character ID. R231 rendered
        # authored options B/C only: B imprisons the embezzler, while C
        # forgives them with a 20-opinion effect and trait-dependent stress.
        # Select authored C as the terminal route with the smallest unrelated
        # realm mutation. Each independently exposed siphoned-treasury secret
        # can notify its victim through 0121 -> 0122; vanilla has no global
        # one-shot gate, so validate every later delivery with this same frame.
        "date_raw": 53187480,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _VANILLA_SECRET_0122_CHARACTER_SCOPES,
        "unique_character_scope_excludes": {
            "secret_owner": (32904,),
            "secret_exposer": (),
            "embezzler": (32904,),
            "local_secret_owner": (32904,),
        },
        "character_scope_matches_any": {
            "embezzler": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "embezzlement_stake": "value",
            "embezzlement_stake_half": "value",
            "embezzler": "character",
            "local_secret_owner": "character",
            "secret_owner_is_vassal": "flag",
        },
        "saved_scope_name_sets": (_VANILLA_SECRET_0122_SAVED_SCOPE_NAMES,),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}
