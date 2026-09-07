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
    "secret_owner": 28093,
    "secret_target": 32904,
    "secret_exposer": 28093,
    "siphoned_treasury_victim": 32904,
    "embezzler": 28093,
    "victim": 32904,
    "exposed_secret_target": 32904,
    "local_secret_owner": 28093,
    "liege": 32904,
}


VANILLA_SECRET_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "secrets.0122": {
        # CK3 1.19.0.6 embezzlement exposure. R231 rendered authored options
        # B/C only: B imprisons the embezzler, while C forgives them with a
        # 20-opinion effect and trait-dependent stress. Select authored C as
        # the terminal route with the smallest unrelated realm mutation.
        "date_raw": 53187480,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _VANILLA_SECRET_0122_CHARACTER_SCOPES,
        "scope_types": {
            "secret": "secret",
            "embezzlement_stake": "value",
            "embezzlement_stake_half": "value",
            "secret_owner_is_vassal": "flag",
        },
        "saved_scope_name_sets": (_VANILLA_SECRET_0122_SAVED_SCOPE_NAMES,),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
}
