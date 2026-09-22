"""Exact-build contracts for physician epidemic events in ordinary campaigns."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_PHYSICIAN_EPIDEMIC_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "physician_epidemic_events.1000": {
        # R0089's whole_of_body-gated native 0 was not materialized. Native 1
        # grants epidemic resistance with known zealot/rival/stress costs;
        # native 2 grants piety/opinion but no resistance. Only this exact
        # source-reviewed [1, 2] projection is admitted.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "unique_character_scope_excludes": {
            "physician": (PLAYER_SENTINEL,),
            "zealous_courtier": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "physician": ("zealous_courtier",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "physician": "character",
            "zealous_courtier": "character",
        },
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "physician",
            "zealous_courtier",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_PHYSICIAN_EPIDEMIC_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "physician_epidemic_events.1000": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/ce1/physician_epidemic_events.txt": (
                "51ADEEA52F9A93406156ABAFA6608B0425003F63098F0CB033A5CB515C90F493"
            ),
            "common/on_action/ce1_on_actions.txt": (
                "96B42FA1A542836171A2A608B7155A8A80D30B0D8F8D9742EBE8AFF231B85E16"
            ),
            "common/modifiers/06_ce1_modifiers.txt": (
                "63FEB33C8C5BF825E3D186E841D07235C98D6AED27C47375E495EA832255C52B"
            ),
        },
        "definition_lines": "8-171",
        "caller_lines": "35",
        "caller_boundary": (
            "epidemic_ongoing_events stochastic pool, weight 100 with "
            "chance_of_no_event 95; major nearby epidemic, superstitious "
            "physician and anti-superstitious opponent required"
        ),
        "option_semantics": {
            0: (
                "whole_of_body-gated; five-year +10 epidemic resistance "
                "without heretical opinion cost"
            ),
            1: (
                "five-year +10 epidemic resistance and -10 zealot opinion; "
                "progress opposing courtier/physician rivalry and apply "
                "trait-dependent stress impact"
            ),
            2: (
                "give opponent relieved_opinion +20 and player medium piety, "
                "with different trait-dependent stress; no resistance"
            ),
        },
        "safe_option_rationale": (
            "For the R0089 four-scope/native [1,2] projection, native 1 "
            "prioritizes player epidemic resistance during an active major "
            "outbreak while accepting known opinion/rivalry/stress costs. "
            "It is bounded continuation, not a native-AI-equivalence claim."
        ),
        "material_result_boundary": (
            "R0089 old instance disappearance does not independently prove "
            "the five-year modifier, opinion or rivalry effect"
        ),
    },
}


VANILLA_PHYSICIAN_EPIDEMIC_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "physician_epidemic_events.1000": {
        "exemplars": [{
            "run": "R0089",
            "kind": "natural-production-generic-fallback-red",
            "artifact": (
                "g2-first-1066-r0089-physician1000-red-20260922/"
                "evidence-manifest.json"
            ),
            "artifact_sha256": (
                "79661336F22CEEA10A21FA41B84654BA86087EF44492CD1FFABE64ABD4E3C9FC"
            ),
            "date_raw": 53350560,
            "event_instance_id": 21,
            "root_character_id": 36403,
            "saved_character_ids": {
                "physician": 50397184,
                "zealous_courtier": 33594572,
            },
            "rendered_native_option_indices": [1, 2],
            "generic_selected_native_option_index": 1,
            "source_reviewed_selected_native_option_index": 1,
            "old_event_disappeared_next_frame": True,
            "material_effect_verified": False,
        }],
    },
}


__all__ = [
    "VANILLA_PHYSICIAN_EPIDEMIC_ANALYSIS",
    "VANILLA_PHYSICIAN_EPIDEMIC_OBSERVATIONS",
    "VANILLA_PHYSICIAN_EPIDEMIC_TIMELINE_CONTRACTS",
]
