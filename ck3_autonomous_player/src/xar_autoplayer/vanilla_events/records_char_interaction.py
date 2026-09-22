"""Exact-build, portable contracts for character-interaction letters."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_CHAR_INTERACTION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "char_interaction.0232": {
        # Source option .a calls ROOT into the rebel's imprisonment war;
        # option .b only changes rebel opinion. R0088 showed both options.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "unique_character_scope_excludes": {
            "actor": (PLAYER_SENTINEL,),
            "recipient": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "imprisoner": ("actor",),
            "imprisonment_target": ("recipient",),
        },
        "scope_types": {
            "actor": "character",
            "recipient": "character",
            "secondary_actor": "character",
            "secondary_recipient": "character",
            "intermediary": "character",
            "hook": "boolean",
            "imprisoner": "character",
            "imprisonment_target": "character",
            "war_for_imprisonment_flavour": "boolean",
        },
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "hook",
            "imprisoner",
            "imprisonment_target",
            "war_for_imprisonment_flavour",
        ),),
        "saved_scope_count": 9,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_CHAR_INTERACTION_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "char_interaction.0232": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/interaction_events/character_interaction_events.txt": (
                "D238E0A3442F41C35AF35157D47A754CB200B72AB2A0184BAEFC86E63347A150"
            ),
            "common/scripted_effects/00_interaction_effects.txt": (
                "7B426465FCED71A6D6AA96B34C8924B91990D0BE144FE4BFAA57681BB7FA6EA5"
            ),
        },
        "definition_lines": "1677-1784",
        "caller_lines": "895, 1362, 1528",
        "caller_boundary": (
            "imprisonment/retraction refusals start refused_liege_demand_war "
            "and notify every player vassal of the liege; which exact caller "
            "produced R0088 remains unknown"
        ),
        "option_semantics": {
            0: (
                "possibly leave a TGP house bloc, remove ROOT from the "
                "defender side, then call and add ROOT to the rebel attack "
                "in refused_liege_demand_war; give rebel positive opinion"
            ),
            1: (
                "give rebel sided_with_tyrant_opinion toward ROOT; no "
                "war participation effect"
            ),
        },
        "safe_option_rationale": (
            "For the R0088 two-option standard-feudal projection, native 1 "
            "avoids an unbounded war commitment while accepting the "
            "source-authored rebel-opinion cost. This is bounded "
            "continuation, not a claim of strategic optimality."
        ),
        "material_result_boundary": (
            "Event closure and next-turn consumption do not prove the "
            "opinion delta; a separate opinion/war-state readback is needed"
        ),
    },
}


VANILLA_CHAR_INTERACTION_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "char_interaction.0232": {
        "exemplars": [{
            "run": "R0088",
            "kind": "natural-production-generic-fallback-red",
            "artifact": (
                "g2-first-1066-r0088-warhold-red-20260922/"
                "evidence-addendum-char-interaction-0232.json"
            ),
            "artifact_sha256": (
                "4FF8060EE30197096BD311FE4D64AFE7DA83F3EF4EB03419CB7AA7896A505B15"
            ),
            "date_raw": 53349960,
            "event_instance_id": 19,
            "root_character_id": 36403,
            "saved_character_ids": {
                "actor": 38609,
                "recipient": 39146,
                "imprisoner": 38609,
                "imprisonment_target": 39146,
            },
            "rendered_native_option_indices": [0, 1],
            "generic_selected_native_option_index": 0,
            "source_reviewed_selected_native_option_index": 1,
            "postcondition_verified": False,
        }],
    },
}


__all__ = [
    "VANILLA_CHAR_INTERACTION_ANALYSIS",
    "VANILLA_CHAR_INTERACTION_OBSERVATIONS",
    "VANILLA_CHAR_INTERACTION_TIMELINE_CONTRACTS",
]
