"""Reusable CK3 1.19.0.6 records for TGP dynastic-cycle events."""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle_events.0020": {
        # Both exact-build yearly pools can select this instability event again
        # after its ten-year event cooldown.  The third authored option adds no
        # scripted resource, control, dread, modifier, or relationship effect;
        # it is the least invasive continuation after the unavoidable immediate.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "marshal": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "my_situation": "situation",
            "my_movement": "situation_participant_group",
            "marshal": "character",
            "peasant_county": "landed_title",
        },
        "saved_scope_name_sets": ((
            "my_situation",
            "my_movement",
            "marshal",
            "peasant_county",
        ),),
        "saved_scope_count": 4,
        "scope_variants": ({
            # The null-safe top participant lookup can legitimately omit the
            # movement while the dynastic-cycle situation still exists.
            "saved_scope_names": (
                "my_situation",
                "marshal",
                "peasant_county",
            ),
            "saved_scope_count": 3,
            "scope_types": {
                "my_situation": "situation",
                "marshal": "character",
                "peasant_county": "landed_title",
            },
        },),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
            {
                "option_count": 2,
                "snapshot_option_counts": (3,),
                "native_option_indices": (1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
            {
                # Native 0 appears only with the intimidation lifestyle focus.
                "option_count": 3,
                "snapshot_option_counts": (3,),
                "native_option_indices": (0, 1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle_events.0020": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_dynastic_cycle_flavor_events.txt": (
                "2260A2AC3F568B3135588E12E4C817846A03AA4BDB16A71C4828490D45F696F3"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "415-572",
        "caller_semantics": (
            "TGP and general yearly random-event pools; event-local cooldown "
            "is ten years and therefore the event is repeatable"
        ),
        "trigger_boundary": (
            "adult celestial ruler during dynastic-cycle instability with at "
            "least one held county at or above low control"
        ),
        "immediate_effect": (
            "saves cycle/movement/marshal/county scopes, ensures the marshal is "
            "at court, and applies an unavoidable major county-control loss"
        ),
        "option_semantics": {
            0: (
                "intimidation-focus only; gains dread, adds a ten-year executed-"
                "peasants county modifier, and restores medium county control"
            ),
            1: (
                "pays major treasury or gold to the marshal and restores medium "
                "county control"
            ),
            2: (
                "no scripted gameplay effect beyond the declared lazy/diligent "
                "stress impact"
            ),
        },
        "after_effect": None,
        "safe_option_rationale": (
            "native2 avoids the native0 dread/modifier mutation and the native1 "
            "treasury-or-gold transfer; the immediate control loss is unavoidable"
        ),
    },
}


VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle_events.0020": {
        "exemplars": [{
            "run": "R372",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "tgp-dynastic-cycle-0020-red-report.json"
            ),
            "artifact_sha256": (
                "D4503D4EE7FC2A4AB8C22F91BCAA7D1E5642293D034E2AD96848E9E19BEF89AB"
            ),
            "park_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-7.json"
            ),
            "park_artifact_sha256": (
                "D5D27D04B2F211AEE353C6896029285988AAC54E123122B2B7AB8FB609F31274"
            ),
            "date_raw": 53450184,
            "event_instance_id": 777,
            "root_character_id": 32904,
            "saved_character_ids": {"marshal": 36528},
            "saved_scope_raw_types": {
                "my_situation": 60,
                "my_movement": 61,
                "marshal": 4,
                "peasant_county": 5,
            },
            "rendered_native_option_indices": [1, 2],
            "selection_attempted": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS",
    "VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS",
    "VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS",
]
