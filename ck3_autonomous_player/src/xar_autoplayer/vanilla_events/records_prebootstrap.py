"""Normalized vanilla-event contracts observed before product bootstrap.

The timeline contracts contain only the event identity constraints needed to
recognize and drain each exact vanilla window.  Save provenance belongs to the
separate observation metadata and is not part of the reusable event contract.
"""

from __future__ import annotations

from typing import Final


PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "spymaster_task.0381": {
        "date_raw": 53148768,
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "character_to_hook": (29037, 32904),
        },
        "boolean_scopes": (),
        "option_count": 2,
        "native_option_indices": (0, 1),
        # Option 1 spends gold and fabricates a hook. Option 2 only grants the
        # selected third party a decaying opinion modifier toward root.
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "spymaster_task.0399": {
        "date_raw": 53148768,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": ("no_secrets_here",),
        "option_count": 2,
        "native_option_indices": (0, 1),
        # Option 1 changes the councillor task. Option 2 leaves the current
        # Find Secrets task running.
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}


PREBOOTSTRAP_VANILLA_OBSERVATION_METADATA: Final[
    dict[str, dict[str, object]]
] = {
    "spymaster_task.0381": {
        "source_save_sha256s": (
            "bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733",
        ),
    },
    "spymaster_task.0399": {
        "source_save_sha256s": (
            "233e70536d736c32efb9bbd20ef4bab9e0be8f96ee13524707b9ee31e319dc9c",
            "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9",
        ),
    },
}


__all__ = (
    "PREBOOTSTRAP_VANILLA_OBSERVATION_METADATA",
    "PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS",
)
