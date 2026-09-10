"""Reusable CK3 1.19.0.6 record for the pay-homage liege event.

Only the source-reviewed shape observed in R384 is admitted by the timeline
contract.  Campaign identities and dates remain observation-only so other
operators and machines can consume the same record through the read-only MCP.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "pay_homage.0101": {
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "homage_liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "homage_vassal": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "opinion_of_petitioner": "value",
        },
        "boolean_scopes": (
            "pay_homage_submission",
            "pay_homage_hook",
            "pay_homage_contract",
            "pay_homage_gold",
        ),
        "saved_scope_name_sets": ((
            "pay_homage_submission",
            "pay_homage_hook",
            "pay_homage_contract",
            "pay_homage_gold",
            "homage_vassal",
            "homage_liege",
            "opinion_of_petitioner",
        ),),
        "saved_scope_count": 7,
        # The native snapshot reports all three source-authored options, while
        # the current-event query publishes only the sole shown Smooth option.
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_PAY_HOMAGE_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "pay_homage.0101": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/decisions_events/pay_homage_events.txt": (
                "391EC1D01719AE94B902E8AC3B0FBE7D49F52F0896CD7A3846E28032F2AADDEB"
            ),
            "common/decisions/30_court_decisions.txt": (
                "7D366988081A0E6CBD9E583FF767AEBC71F6CC599F80B1D0784964CE8646E089"
            ),
            "common/on_action/dlc/ep1/ep1_pay_homage_on_actions.txt": (
                "6E3FF78C8633CE50809303F4A253076A248B35BF4794653ED67C6647659AC1C2"
            ),
            (
                "localization/simp_chinese/event_localization/activities/"
                "pay_homage_events_l_simp_chinese.yml"
            ): (
                "2C78E6A600FF2F0AD0C78D4DDA927B189B2E7C85FD29FC1B7DD941BC82BA527B"
            ),
            (
                "localization/english/event_localization/activities/"
                "pay_homage_events_l_english.yml"
            ): (
                "EEBF7C730FA2E09B3390320D0B9F3276455D7FC6EE7B6C16E282F371847392A2"
            ),
        },
        "definition_lines": "686-1052",
        "decision_definition_lines": "2-390",
        "on_action_definition_lines": "1-265",
        "reward_effect_lines": "269-511",
        "downstream_event_lines": "1055-1280",
        "caller_semantics": (
            "pay_homage_decision records the liege and homage type, starts a "
            "travel plan whose arrival event is pay_homage.9999, and "
            "pay_homage_start establishes the vassal, liege, contract, and "
            "optional infatuation scopes; arrival either auto-accepts for an "
            "eligible AI vassal before a player liege or routes through "
            "pay_homage.0001, whose acceptance triggers pay_homage.0101"
        ),
        "eligibility_boundary": (
            "the liege event requires the homage vassal to remain alive and "
            "not imprisoned; the earlier decision and travel chain owns the "
            "remaining eligibility checks"
        ),
        "frequency_boundary": (
            "this is decision/travel driven rather than a periodic event; AI "
            "decision checks use a 45-day interval for county through empire "
            "tiers and pay_homage_start applies a two-year liege-side anti-spam "
            "cooldown, while the same vassal cannot pay the same liege again"
        ),
        "event_immediate_effect": (
            "a 2/2/2/2/50 random list may set one faux-pas scope from language, "
            "prowess, infatuation, or delivery conditions, then the event "
            "saves the liege's opinion of the petitioner"
        ),
        "option_semantics": {
            0: (
                "Smooth is shown only when all four faux-pas scopes are absent; "
                "its body only previews a minor prestige gain for the vassal"
            ),
            1: (
                "Brush Off is shown when any faux-pas scope exists; it previews "
                "a minor prestige loss and may add liege stress, without the "
                "mocked flag used by the harsher branch"
            ),
            2: (
                "Insult is shown when any faux-pas scope exists; it sets the "
                "mocked flag, applies an insult opinion penalty, and previews "
                "larger prestige and legitimacy losses"
            ),
        },
        "after_effect": (
            "every option runs pay_homage_liege_reward_effect and triggers "
            "pay_homage.0201 for the vassal; that downstream event applies the "
            "vassal reward and clears the temporary variables"
        ),
        "repeatability": (
            "the event can recur for other eligible vassal-liege pairs after "
            "their decision and travel chain, but not repeatedly for the same "
            "vassal and unchanged liege"
        ),
        "safe_option_policy": {
            "no_faux_pas": 0,
            "faux_pas": 1,
            "default_forbidden": 2,
        },
        "safe_option_rationale": (
            "R384 exposes only native option 0 because no faux-pas scope is "
            "present; it is therefore both the sole legal option and the least "
            "harmful source-authored resolution. Future faux-pas variants must "
            "remain RED until their distinct scope projection is observed."
        ),
        "religion_boundary": (
            "faith participates only in the earlier optional infatuation "
            "candidate selection; this event's option triggers and effects do "
            "not query religion, so the reusable contract treats infatuation "
            "only as an opaque faux-pas presence bit"
        ),
    },
}


VANILLA_PAY_HOMAGE_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "pay_homage.0101": {
        "exemplars": [{
            "run": "R384",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r383-b1-replay-live/"
                "r384-pay-homage-0101-red-report.json"
            ),
            "artifact_sha256": (
                "AC3E7F8616020056D9E8AF652BE091617110E2F1C30A9B3B3FF39BE87491C5AC"
            ),
            "park_artifact": (
                "_runtime/p2r383-b1-replay-live/"
                "r384-pay-homage-0101-red-park.json"
            ),
            "park_artifact_sha256": (
                "7C0567D6F37DB922D31A2AF8AE69405BC4CA8AAA5C835DADB8FC92A801C7AA89"
            ),
            "driver_state_artifact": (
                "_runtime/p2r383-b1-replay-live/"
                "r384-pay-homage-0101-driver-state.json"
            ),
            "driver_state_artifact_sha256": (
                "62515E9392CBCBDE98688A00213DF98E3E5250C97AC3F54DA70392A05CC83D94"
            ),
            "date_raw": 53590944,
            "event_instance_id": 1046,
            "root_character_id": 32904,
            "saved_character_ids": {
                "homage_liege": 32904,
                "homage_vassal": 50338971,
            },
            "saved_scope_raw_types": {
                "pay_homage_submission": 2,
                "pay_homage_hook": 2,
                "pay_homage_contract": 2,
                "pay_homage_gold": 2,
                "homage_vassal": 4,
                "homage_liege": 4,
                "opinion_of_petitioner": 1,
            },
            "snapshot_option_count": 3,
            "rendered_native_option_indices": [0],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 38864,
            "snapshot_id": "native:125",
            "revision": 126,
            "remaining_game_days": 149,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_PAY_HOMAGE_ANALYSIS",
    "VANILLA_PAY_HOMAGE_OBSERVATIONS",
    "VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS",
]
