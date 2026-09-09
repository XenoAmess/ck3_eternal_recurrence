"""Reusable CK3 1.19.0.6 event records for TGP movement events.

The timeline contract deliberately contains no campaign-specific character IDs or
dates.  Concrete live evidence belongs in the observation metadata below and is
not a second source of universal contract values.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_movement_events.0160": {
        # The yearly TGP movement pulse may select this event again after its
        # ten-year event cooldown.  Bind recurrence to the caller's bounded
        # observation window instead of freezing one campaign occurrence.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival": [PLAYER_SENTINEL],
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "rival": "character",
            "rival_movement": "situation_participant_group",
        },
        "saved_scope_name_sets": [[
            "my_movement",
            "rival",
            "rival_movement",
        ]],
        "saved_scope_count": 3,
        "boolean_scopes": [],
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": [0, 1, 2],
        # Native 0 can create a mutual fifteen-year scheme block and native 1
        # pays gold before creating it.  Native 2 preserves both resources and
        # strategic freedom; its authored effect is minor intrigue lifestyle XP
        # with the declared ambitious stress impact.
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_MOVEMENT_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "tgp_movement_events.0160": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "localization/simp_chinese/dlc/tgp/"
            "tgp_movement_events_l_simp_chinese.yml": (
                "A2ADDB9940D72F79E57BC266EA62A11CB3D0C5318E79D5F93CB8F5EE01B3943F"
            ),
        },
        "definition_lines": "3526-3699",
        "caller_semantics": (
            "yearly random-event pools; event-local cooldown is ten years"
        ),
        "option_semantics": {
            0: "diplomacy duel; success creates a mutual fifteen-year scheme block",
            1: "pays medium gold and creates the mutual fifteen-year scheme block",
            2: "minor intrigue lifestyle XP; no gold payment or scheme block",
        },
        "after_effect": None,
        "safe_option_rationale": (
            "native2 avoids the stochastic or guaranteed fifteen-year scheme "
            "restriction and avoids the native1 gold transfer"
        ),
    },
}


VANILLA_TGP_MOVEMENT_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "tgp_movement_events.0160": {
        "exemplars": [{
            "run": "R372",
            "kind": "paused-live-exemplar",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-4.json"
            ),
            "artifact_sha256": (
                "3D0BBB7C7AFCE08003329DF248301BAD4216D8BE47FBE4F24703A4E89E5D0E68"
            ),
            "date_raw": 53436720,
            "event_instance_id": 668,
            "root_character_id": 32904,
            "saved_character_ids": {"rival": 37625},
            "saved_scope_raw_types": {
                "my_movement": 61,
                "rival": 4,
                "rival_movement": 61,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selection_attempted": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_TGP_MOVEMENT_ANALYSIS",
    "VANILLA_TGP_MOVEMENT_OBSERVATIONS",
    "VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS",
]
