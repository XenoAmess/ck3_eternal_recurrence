"""Reusable CK3 1.19.0.6 record for the Majesty ideas handoff.

The record is source-shaped and campaign-neutral.  R390 contributes the first
paused native observation, but none of its process, date, event-instance, or
character identities participate in the portable decision contract.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_DIPLOMACY_MAJESTY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "diplomacy_majesty.4033": {
        # The exact-build source has only one direct caller: option B of .4030
        # retargets ROOT to the chosen recipient while preserving the original
        # thinker.  The quarterly pulse value remains in that inherited event
        # context.  The sole authored acknowledgement has no trigger and is
        # therefore always the only rendered, enabled route once .4033 opens.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "event_target": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "thinker": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "thinker": ("event_target",),
        },
        "scope_types": {
            "quarter": "value",
            "thinker": "character",
            "event_target": "character",
        },
        "saved_scope_name_sets": (("quarter", "thinker", "event_target"),),
        "saved_scope_count": 3,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_DIPLOMACY_MAJESTY_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "diplomacy_majesty.4033": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/lifestyles/statecraft_lifestyle/"
            "diplomacy_majesty_events.txt": (
                "C3FB744B621E6E4C9F62919AB8B006C6EBB716AEF233CC923D2B9318802F8516"
            ),
            "common/on_action/lifestyles/diplomacy_lifestyle_on_actions.txt": (
                "A7A85C90D27E2D5B4E221338277B60EA3560BAEBEACD971AEAEB7711CB97E390"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/modifiers/00_diplomacy_lifestyle_modifiers.txt": (
                "F60F1B1DC82728304CDC68684AF6ED829587C73D2B42D0A5247EAA59635EA4B1"
            ),
            "localization/english/event_localization/lifestyle/statecraft/"
            "diplomacy_majesty_events_l_english.yml": (
                "C324AC167F63FF1FA1B7B7F733DB137DF630E2369827D909A0510EBB445CEB08"
            ),
            "localization/simp_chinese/event_localization/lifestyle/statecraft/"
            "diplomacy_majesty_events_l_simp_chinese.yml": (
                "9EBA356E98F54A79AF19FF55EC47040ADFFC29753FC2F5C15BC351FC49676426"
            ),
        },
        "definition_lines": "968-1008",
        "trigger_lines": "983-987",
        "option_lines": "989-1007",
        "direct_caller_lines": "870-901 (direct trigger at 886)",
        "lifestyle_pool_lines": "5-29, 33-66, 95 and 125-132",
        "caller_semantics": (
            "the quarterly diplomacy lifestyle pulse enters an ongoing event "
            "pool with a ten-percent chance, documented by the exact source as "
            "roughly one lifestyle event every eighteen months. The common "
            "pool can select diplomacy_majesty.4030; its option B changes ROOT "
            "to the selected event_target and directly triggers .4033 while "
            "the original .4030 ROOT remains saved as thinker"
        ),
        "frequency_boundary": (
            ".4033 has no independent daily pulse. It is a direct consequence "
            "of choosing .4030 option B; .4030 sets a five-year event flag and "
            "the recipient gains the five-year basic-strategy modifier that "
            "also makes that recipient ineligible as another .4030 target"
        ),
        "trigger_boundary": "the inherited thinker must still be alive",
        "scope_boundary": (
            "ROOT is the .4030 event_target and thinker is the original .4030 "
            "ROOT. The observed quarter value is inherited from the quarterly "
            "lifestyle pulse; no campaign identity is part of the contract"
        ),
        "immediate_effect": None,
        "option_semantics": {
            0: (
                "the recipient gains diplomacy_majesty_4030_basic_strategy_modifier "
                "for five years (diplomacy plus one and martial plus one), gains "
                "twenty-five pleased opinion of thinker, and establishes the "
                "potential-friend relation when it does not already exist"
            ),
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "the acknowledgement has no one-shot flag of its own; recurrence is "
            "bounded by the upstream .4030 five-year flag and target-modifier "
            "eligibility rules"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is unconditional, terminal, and the only "
            "available route. Its complete scripted effect set is beneficial: "
            "a five-year skill modifier, positive opinion, and a potential-friend "
            "relation, with no resource cost, stress, imprisonment, injury, death, "
            "war, title transfer, or follow-up event"
        ),
    },
}


VANILLA_DIPLOMACY_MAJESTY_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "diplomacy_majesty.4033": {
        "exemplars": [{
            "run": "R390",
            "kind": "retained-live-contract-red",
            "artifact": (
                "_runtime/p2r390-t0-critical-continuation-live/"
                "r390-diplomacy-majesty-4033-red-state.json"
            ),
            "artifact_sha256": (
                "37513F94AFE1672408B86FE719607C972E9D2F5C66DEC4D9AE2BFAA861244945"
            ),
            "date_raw": 53589168,
            "event_instance_id": 1089,
            "root_character_id": 32904,
            "saved_character_ids": {
                "thinker": 16853479,
                "event_target": 32904,
            },
            "saved_scope_raw_types": {
                "quarter": 1,
                "thinker": 4,
                "event_target": 4,
            },
            "rendered_native_option_indices": [0],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_DIPLOMACY_MAJESTY_ANALYSIS",
    "VANILLA_DIPLOMACY_MAJESTY_OBSERVATIONS",
    "VANILLA_DIPLOMACY_MAJESTY_TIMELINE_CONTRACTS",
]
