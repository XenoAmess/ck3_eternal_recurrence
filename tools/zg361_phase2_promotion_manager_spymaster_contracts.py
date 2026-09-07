#!/usr/bin/env python3
"""Source-reviewed Find Secrets manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_SPYMASTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "spymaster_task.0381": {
        # Independent vanilla Find Secrets hook opportunity. Option 1 spends
        # gold and fabricates a hook; option 2 only grants the one typed third
        # party a decaying opinion modifier toward root. The same exact event
        # can recur on this seed. The second council-task delivery moved by
        # ten days between R35 and R57 while every semantic field stayed
        # exact. R99 then observed a third delivery at date_raw 53157024 after
        # two fully validated drains in the same PID. Vanilla task progress/
        # random discovery controls delivery; neither selected effect checks
        # the calendar. Use this run's existing product observation window,
        # independently of the three-occurrence cap.
        "date_raw": (53148768, 53152656),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "max_occurrences": 3,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "unique_character_scope_excludes": {
            "character_to_hook": (29037, 32904),
        },
        "boolean_scopes": ("having_find_secrets_event",),
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0399": {
        # Vanilla Find Secrets "found nothing" delivery. The event's
        # immediate random_list saves exactly one of two boolean scopes:
        # secrets_to_be_found when the Spymaster suspects a secret remains,
        # or no_secrets_here otherwise. R60/R69 observed the two legitimate
        # branches with every character identity and option shape unchanged.
        # The task cadence also controls the delivery date, so bind it to the
        # same per-run product observation window as the other Find Secrets
        # notifications instead of freezing one RNG tick.
        "date_raw": (53148768, 53152896),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": (),
        "boolean_scope_name_sets": (
            ("no_secrets_here",),
            ("secrets_to_be_found",),
        ),
        "saved_scope_name_sets": (
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "no_secrets_here",
            ),
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "secrets_to_be_found",
            ),
        ),
        "option_count": 2,
        # Option 1 changes the councillor task. Option 2 preserves the current
        # task and is the already-proven minimal side-effect path.
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0342": {
        # Vanilla Find Secrets discovery notification. The secret and its
        # participants are already fixed when the window opens; there is one
        # authored acknowledgement, which reveals that exact secret to root.
        # R61 observed the same exact one-option/scope identity later in the
        # continuing Find Secrets task. The notification date is selected by
        # the vanilla discovery cadence, not by the revealed-secret contract.
        "date_raw": (53152896, 53157024),
        "date_raw_range": (53152896, 53157024),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
            "active_councillor": 27963,
            "secret_holder": 27051,
        },
        "scope_types": {"secret_to_reveal": "secret"},
        "boolean_scopes": ("having_find_secrets_event",),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0346": {
        # Vanilla Find Secrets lover-secret notification. Like .0342, the
        # discovery is already fixed when the window opens and exposes one
        # acknowledgement, which reveals that exact secret to root.
        # R62 delivered the same exact scope/option identity one day later;
        # bind the observed Find Secrets cadence without changing semantics.
        "date_raw": (53152896, 53152920),
        "date_raw_range": (53152896, 53152920),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
            "active_councillor": 27963,
            "secret_holder": 27051,
            "lover": 45267,
        },
        "scope_types": {"secret_to_reveal": "secret"},
        "boolean_scopes": ("having_find_secrets_event",),
        "saved_scope_count": 8,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0359": {
        # Vanilla fallback for a discovered secret not covered by a more
        # specific flavor event. The secret already exists before the window;
        # its sole option reveals that exact secret to root. R195 observed the
        # complete ten-scope task frame and the only authored option. R201
        # then delivered two independently exact instances in the same client
        # at dates 53178192 and 53178912. Permit those two task outcomes while
        # retaining a finite third-occurrence boundary.
        "date_raw": 53168112,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
            "target": (29037,),
            "secret_holder": (29037,),
        },
        "character_scope_matches_any": {
            "owner": ("councillor", "active_councillor"),
            "councillor": ("owner", "active_councillor"),
            "active_councillor": ("owner", "councillor"),
            "target": ("target_character",),
            "target_character": ("target",),
        },
        "character_scope_differs_from": {
            "owner": ("target", "secret_holder"),
            "target": ("owner", "secret_holder"),
            "secret_holder": ("owner", "target"),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "target_character": "character",
            "councillor": "character",
            "active_councillor": "character",
            "secret_holder": "character",
            "secret_to_reveal": "secret",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "councillor_liege",
            "target_character",
            "councillor",
            "active_councillor",
            "secret_holder",
            "secret_to_reveal",
        ),),
        "saved_scope_count": 10,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 2,
    },
}
