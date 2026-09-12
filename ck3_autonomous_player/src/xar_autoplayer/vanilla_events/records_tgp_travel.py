"""Exact-build record for TGP Chinese travel events."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_TGP_TRAVEL_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_travel_events.0030": {
        # The event frame carries the active travel plan and the province
        # selected by the immediate block. Native option 0 delays the journey
        # and starts a stochastic learning duel; native option 1 only applies
        # the authored medium stress reduction, so it is the bounded terminal
        # continuation for an unexpected timeline interrupt.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "travel_plan": "travel_plan",
            "poem_province": "province",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("travel_plan", "poem_province"),),
        "saved_scope_count": 2,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_TRAVEL_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_travel_events.0030": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/travel_events/tgp_travel_events.txt": (
                "42B8B1E56C029054FBC4E0B3964511A980D9B5053C47BFF980CD3F5F3924DB37"
            ),
            "common/on_action/travel_on_actions.txt": (
                "7E433A0D6969E09CFED1D9DC50FB5276D944354024D6D2E045B314355F41040C"
            ),
        },
        "definition_lines": "311-496",
        "caller_lines": (
            "travel_on_actions.txt:715-951 "
            "(travel_events_on_action; weighted candidate at 934)"
        ),
        "caller_semantics": (
            "the general travel-event on_action first applies its no-event gate, "
            "then includes .0030 as a weight-100 candidate in the travel pool"
        ),
        "trigger_boundary": (
            "the event requires the TGP DLC, celestial government, an available "
            "travelling adult, a valid land location and a nearby special-building "
            "province; it owns a ten-year cooldown"
        ),
        "scope_boundary": (
            "R555 publishes the played character as root, the caller-owned "
            "travel_plan scope and the immediate block's poem_province scope"
        ),
        "immediate_effect": (
            "chooses one nearby special-building province and saves it as "
            "poem_province before the modal is shown"
        ),
        "option_semantics": {
            0: (
                "delays the current travel plan by five days and runs a medium "
                "learning duel whose success can grant lifestyle or traveler XP, "
                "the traveler trait and trait-dependent stress changes"
            ),
            1: "applies only the authored medium stress reduction",
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": "the event owns a ten-year cooldown and no one-shot flag",
        "safe_option_rationale": (
            "authored option 2/native 1 is unconditional and terminal. It avoids "
            "the five-day travel delay, stochastic duel and trait/XP mutation, "
            "and spends no resources"
        ),
    },
}


VANILLA_TGP_TRAVEL_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_travel_events.0030": {
        "exemplars": [{
            "run": "R555",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2-capture-r553-r560-471ded2-20260912/capture/"
                "cell/manager-stage10/stage10-player-subject.json"
            ),
            "artifact_sha256": (
                "C6AC0B6EE128AB6C9FA6209E090C92F936546908D97D03CA53FB4BDD1191680C"
            ),
            "date_raw": 53155992,
            "event_instance_id": 21,
            "root_character_id": 27181,
            "saved_scope_names": ["travel_plan", "poem_province"],
            "saved_scope_count": 2,
            "rendered_native_option_indices": [0, 1],
            "snapshot_option_count": 2,
            "selection_attempted": False,
            "connection_generation": 1,
            "ck3_pid": 196812,
            "snapshot_id": "native:19",
            "revision": 33,
            "retained_red": True,
            "process_restart_required": True,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "VANILLA_TGP_TRAVEL_ANALYSIS",
    "VANILLA_TGP_TRAVEL_OBSERVATIONS",
    "VANILLA_TGP_TRAVEL_TIMELINE_CONTRACTS",
]
