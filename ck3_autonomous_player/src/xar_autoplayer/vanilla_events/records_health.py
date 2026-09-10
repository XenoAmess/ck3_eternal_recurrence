"""Exact-build analysis and observations for reviewed health events."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


VANILLA_HEALTH_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "health.1006": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/health_events.txt": (
                "8CAB7F230E09A37C15F7C088383D40752D970918D44D86762FDD068EE168EFEB"
            ),
            "common/scripted_effects/20_health_effects.txt": (
                "6D7DEF1245D899DE4DEBC42136815BC7F4D14F6A467A8320355507AD03528F12"
            ),
            "common/on_action/health_on_actions.txt": (
                "253988DA3E14BE7CC9B86CAB2A3C15843B0CB8B273B2B4BC391EB287AEF0C94C"
            ),
            "events/travel_events/travel_events_filippa.txt": (
                "F4984713B39DC4436A495DAE8D2264D6A6E179D0DBEAD0897124B97805D20AE7"
            ),
            "localization/english/event_localization/health_events_l_english.yml": (
                "043216116C522B5D108315A3730DA12C5D7B2EDDB8CF60D67D0967AF4AFE23D0"
            ),
            "localization/simp_chinese/event_localization/"
            "health_events_l_simp_chinese.yml": (
                "AFDC39A947F036A140288CC565EDE0B2CC29B1DCD27AF191A7CC0F91A026A0E4"
            ),
        },
        "definition_lines": "2135-2334",
        "trigger_lines": "2194-2196",
        "immediate_effect_lines": "2215-2219",
        "option_lines": "2221-2333",
        "disease_outbreak_pool_entry_line": "353",
        "contract_disease_notify_lines": "627-691",
        "find_physician_effect_lines": "2093-2107",
        "travel_caller_lines": "8622-8674",
        "caller_semantics": (
            "consumption can enter from the disease outbreak pulse, delayed "
            "contract_disease_notify_effect, or a reviewed travel event tail. "
            "The outbreak pool gives it weight one hundred inside a random "
            "disease pulse; the other callers are explicit delayed events"
        ),
        "trigger_boundary": (
            "ROOT must pass can_contract_disease_trigger for consumption. The "
            "R416 shape also inherits epidemic and disease_type from the "
            "contagion path"
        ),
        "immediate_effect": (
            "saves any available court physician, then applies consumption via "
            "contract_disease_effect before presenting the modal. That helper "
            "saves sick_character and disease_type and can create new_memory"
        ),
        "option_semantics": {
            0: (
                "when no physician exists, ROOT is playable, and ROOT is not "
                "travelling, sets thirty-day already_sick, sets the bounded "
                "searching_for_physician flag, and schedules health.3001 after "
                "the configured court-physician search delay"
            ),
            1: (
                "acknowledges the diagnosis when a physician exists but the "
                "liege chooses treatment; it has no authored effect"
            ),
            2: "cancels an eligible ROOT-owned travel plan and goes home",
            3: "uses the physician's safe disease treatment",
            4: "uses the physician's risky disease treatment",
            5: "uses mystic treatment when the physician is a mystic",
            6: (
                "continues without treatment; it only emits the no-treatment "
                "tooltip when a usable physician exists"
            ),
        },
        "native_ai_weights": {
            0: "base 5",
            1: "base 1",
            2: "base 1",
            3: "base 10",
            4: "base 1",
            5: "base 0.5, reduced to zero when AI zeal is nonnegative",
            6: "base 0",
        },
        "after_effect": None,
        "source_projection_boundary": (
            "the portable contract admits the two observed projections only: "
            "no physician with native 0/6, or a non-mystic available physician "
            "with native 3/4/6. Travel, liege-treatment, and mystic rows remain "
            "source-known but unadmitted until observed"
        ),
        "safe_option_rationale": (
            "for the R416 no-physician projection, authored option 1/native 0 "
            "is the only route that opens treatment recovery. R97 already "
            "showed that authored option 7/native 6 can be followed by the "
            "played owner's illness death within roughly twenty-seven days. "
            "For the retained physician projection, authored option 4/native 3 "
            "remains the conservative treatment route"
        ),
    },
}


VANILLA_HEALTH_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "health.1006": {
        "exemplars": [{
            "run": "R97",
            "kind": "legacy-live-binding",
            "review_kind": "source-correlated-historical-live",
            "date_raw": 53168904,
            "event_instance_id": 27,
            "root_character_id": 29037,
            "saved_character_ids": {
                "physician": 56656,
                "sick_character": 29037,
            },
            "saved_scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "physician": "character",
                "sick_character": "character",
                "new_memory": "character_memory",
            },
            "rendered_native_option_indices": [3, 4, 6],
            "selected_option_number": 7,
            "selected_native_option_index": 6,
            "selection_postcondition_verified": True,
            "downstream_played_owner_death_after_rough_days": 27,
        }, {
            "run": "R416",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-05.json"
            ),
            "artifact_sha256": (
                "0BFAB9EF8D38AE9C74F783FE3E4B3672222E5289F760D21074BD04D5683692AA"
            ),
            "date_raw": 53864592,
            "event_instance_id": 1084,
            "root_character_id": 32904,
            "snapshot_id": "native:1025",
            "revision": 1026,
            "native_revision": 1025,
            "saved_character_ids": {"sick_character": 32904},
            "saved_scope_raw_types": {
                "epidemic": 50,
                "disease_type": 3,
                "sick_character": 4,
                "new_memory": 34,
            },
            "rendered_native_option_indices": [0, 6],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_id": 174656,
            "connection_generation": 1,
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
    "VANILLA_HEALTH_ANALYSIS",
    "VANILLA_HEALTH_OBSERVATIONS",
]
