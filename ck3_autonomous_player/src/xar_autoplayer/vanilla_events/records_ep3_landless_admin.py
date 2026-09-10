"""Reusable CK3 1.19.0.6 records for EP3 landless-admin events."""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_landless_admin.1000": {
        # The event always selects or creates one available high-skill adult.
        # Bind that role and the complete three-option projection without
        # retaining any campaign identity or date in the reusable contract.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "proposed_councillor": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "proposed_councillor": "character",
        },
        "saved_scope_name_sets": (("proposed_councillor",),),
        "saved_scope_count": 1,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_landless_admin.1000": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/ep3/ep3_landless_admin_events.txt": (
                "AB7F5179D120578BADAA307605CC9F5FA2B3E6845A43F773954D230DD67BE993"
            ),
            "common/on_action/ep3_on_actions.txt": (
                "107D8695BFE25DAF20E058D5EB34579FDB586A172E81D30E052A4662D8E90EA1"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/scripted_triggers/00_available_for_events_triggers.txt": (
                "5566A89A7D93BFB80DCF5A2F065BE0F058BE13E0B84470D1182B82D8D6384A44"
            ),
            "localization/simp_chinese/dlc/ep3/"
            "ep3_landless_admin_l_simp_chinese.yml": (
                "AEBDEDB774D20329390B44EF9376BF90B1CEEAB5307C5D04415B02B56E066D98"
            ),
        },
        "definition_lines": "17-212",
        "trigger_lines": "41-44",
        "trigger_helper_lines": "78-112, 767-781, 881-886",
        "immediate_lines": "59-88",
        "option_lines": "90-211",
        "caller_lines": {
            "common/on_action/yearly_on_actions.txt": (
                "2522-2524, 2552, 2557, 2933-2936, 3662"
            ),
            "common/on_action/ep3_on_actions.txt": "1-7, 69",
        },
        "caller_semantics": (
            "random_yearly_playable_pulse can select either the general yearly "
            "pool or ep3_yearly_events_admin, never both during one annual "
            "pulse; both contain this event. The EP3 "
            "pool first requires administrative government and passes a fifty "
            "percent chance_to_happen. Event-local trigger then requires an "
            "available landless-administrative character"
        ),
        "frequency_boundary": (
            "the outer playable pulse runs once per character-year at a random "
            "date, but weighted pool selection, event filtering and the event's "
            "five-year cooldown prevent annual guaranteed delivery"
        ),
        "scope_boundary": (
            "immediate saves exactly proposed_councillor, selecting an available "
            "healthy high-skill AI adult from the local pool when possible or "
            "creating a local-faith, local-culture administrator otherwise"
        ),
        "domain_boundary": (
            "this is a non-religious administrative event; faith is only an "
            "opaque generated-character attribute and female-chance input"
        ),
        "option_semantics": {
            0: (
                "guarantees recruitment, transfers medium gold to the proposed "
                "councillor, and can give medium stress to greedy, avaricious "
                "or arrogant roots"
            ),
            1: (
                "runs a stewardship duel: success recruits for free, the middle "
                "result recruits for minor gold and an obligation hook, and "
                "failure leaves the candidate out and applies minus fifteen "
                "opinion; greedy roots can gain minor stress"
            ),
            2: (
                "declines the candidate without recruitment, gold, duel, hook "
                "or opinion mutation; generous roots can gain medium stress"
            ),
        },
        "after_effect": None,
        "repeatability": (
            "the event defines a five-year cooldown and no campaign one-shot "
            "flag, so later eligible yearly pulses may select it again"
        ),
        "safe_option_rationale": (
            "native2 is the only deterministic terminal route that avoids gold "
            "transfer, a stochastic duel, court membership, hook and opinion "
            "mutation; its only authored cost is the declared generous stress "
            "impact"
        ),
    },
}


VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_landless_admin.1000": {
        "exemplars": [{
            "run": "R375",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-ep3-landless-admin-1000-red-freeze.json"
            ),
            "artifact_sha256": (
                "F74447FE01DDB9BC890C757578DBA477373167EA0DA862BB987D26A61904DFA1"
            ),
            "park_artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "hot-recovery-park-4.json"
            ),
            "park_artifact_sha256": (
                "C382B9DD4C8ABC45664B68BAFEACF63B9AB718D2E8D0433DB558F0BACAAC9E01"
            ),
            "date_raw": 53619912,
            "event_instance_id": 1062,
            "root_character_id": 32904,
            "saved_character_ids": {
                "proposed_councillor": 33643335,
            },
            "saved_scope_raw_types": {
                "proposed_councillor": 4,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selection_attempted": False,
            "snapshot_option_count": 3,
            "snapshot_id": "native:720",
            "native_revision": 720,
            "revision": 721,
            "query_sequence": 22,
            "connection_generation": 1,
            "bridge_pid": 180544,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS",
    "VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS",
    "VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS",
]
