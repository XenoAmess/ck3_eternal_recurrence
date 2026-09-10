"""Reusable CK3 1.19.0.6 records for reviewed BP1 yearly events."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "bp1_yearly.1040": {
        # The seduction row is source-authored but can be hidden.  Bind the
        # rendered native-index projection observed at the paused window, then
        # choose the terminal refusal which creates no relation or scheme.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "new_friend": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "new_friend": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("new_friend",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "bp1_yearly.4000": {
        # The dead-participant projection exposes the deterministic grief row
        # and the diplomacy-duel poem row.  Bind that exact live shape and take
        # the deterministic branch rather than speculating on the duel result.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "family_memory_participant": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "family_memory": "character_memory",
            "family_memory_participant": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "family_memory",
            "family_memory_participant",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "snapshot_option_count": 5,
        "native_option_indices": (1, 3),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_BP1_YEARLY_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "bp1_yearly.1040": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/dlc/bp1/bp1_yearly_events_claudia.txt": (
                "F79A3224CFB74804BD489D626E121A883CB0217895D136BB61B9A96880EA3EE4"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/opinion_modifiers/00_opinion_modifiers.txt": (
                "9784F704B8DE847294451BEC6E6D1345B5CA4109219A9B4264E4AE8FDB1AE555"
            ),
        },
        "definition_lines": "2467-2845",
        "trigger_lines": "2499-2548",
        "weight_multiplier_lines": "2550-2566",
        "immediate_effect_lines": "2568-2686",
        "option_lines": "2688-2838",
        "after_effect_lines": "2839-2844",
        "random_yearly_playable_pulse_lines": "2522-2563",
        "on_yearly_events_lines": "2933-3842",
        "on_yearly_pool_entry_line": "3354",
        "opinion_modifier_lines": "135-139",
        "caller_semantics": (
            "random_yearly_playable_pulse runs once at an independently random "
            "point each year for each playable character. Its weighted group "
            "selects on_yearly_events with weight six; that group has a "
            "twenty-five-percent chance to choose a valid weighted candidate, "
            "where this event has weight one hundred"
        ),
        "frequency_boundary": (
            "the exact annual probability varies with all valid weighted groups "
            "and candidates. This event is a yearly-pulse candidate, not a daily "
            "poll, and declares a twenty-year cooldown"
        ),
        "trigger_boundary": (
            "Friends and Foes must be active; ROOT must be an available healthy "
            "adult, neither tribal nor nomadic, not at war, and must have a "
            "capital plus an eligible potential friend, friend, or high-opinion "
            "courtier. Single-gender realm laws add a same-sex requirement"
        ),
        "immediate_effect": (
            "chooses and saves exactly one eligible new_friend, then temporarily "
            "adds is_naked to ROOT and that character for the bathhouse scene"
        ),
        "scope_boundary": (
            "the source-authored immediate always publishes one non-ROOT "
            "new_friend character when the event fires"
        ),
        "option_semantics": {
            0: (
                "creates a friend relation when one does not exist, otherwise "
                "upgrades the existing friend to best_friend; shy, disloyal, and "
                "paranoid traits can add stress"
            ),
            1: (
                "when the sexuality, family, and can-start-scheme triggers pass, "
                "starts a seduce scheme against new_friend and adds the authored "
                "success modifier; the row is absent from the R416 projection"
            ),
            2: (
                "creates no relation or scheme. new_friend receives a minus-thirty "
                "disappointed_opinion toward ROOT; the exact modifier is decaying "
                "with monthly_change 0.1 and is stackable. ROOT can gain major "
                "stress when gregarious, trusting, compassionate, or loyal"
            ),
        },
        "native_ai_weights": {
            0: (
                "base 100; plus 75 when gregarious, minus 75 when paranoid, and "
                "minus 50 when disloyal"
            ),
            1: "base 100; minus 25 when shy and minus 50 when chaste",
            2: (
                "base 100; minus 75 for each of gregarious, trusting, "
                "compassionate, and loyal; plus 50 for each of arrogant, shy, "
                "and reclusive"
            ),
        },
        "after_effect": (
            "removes the temporary is_naked flag from ROOT and new_friend for "
            "every option"
        ),
        "follow_up_event": None,
        "repeatability": (
            "the event's twenty-year cooldown bounds recurrence within a long "
            "product observation window"
        ),
        "safe_option_rationale": (
            "authored option 3/native 2 is the only currently rendered route "
            "that creates neither a durable friend or best-friend relation nor a "
            "seduce scheme. It accepts the source-defined minus-thirty decaying "
            "opinion and listed trait-dependent stress"
        ),
    },
    "bp1_yearly.4000": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/dlc/bp1/bp1_yearly_oltner.txt": (
                "2D8DAB35EF9630F3A0206CE8F3DEC91AAE0442D80434A66955D7B3B7134A1CC6"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/on_action/yearly_groups_on_actions.txt": (
                "D916E482A780F26CC1B1B27B582B675F90945AB808EB461A54A906EAAD0147C5"
            ),
            "localization/english/dlc/bp1/"
            "dlc_bp1_oltner_yearly_events_l_english.yml": (
                "14718DDCABE8FE5AA53BE00C1FEEA6788842E21E0D417764A3B04EA08CE9F4D2"
            ),
            "localization/simp_chinese/dlc/bp1/"
            "dlc_bp1_oltner_yearly_events_l_simp_chinese.yml": (
                "A922EB18E96A803CF7F216CB9D974F5B9160D1E9D8CABBF0D398C6D70F122CB9"
            ),
        },
        "definition_lines": "22-292",
        "trigger_lines": "95-107",
        "immediate_effect_lines": "109-132",
        "option_lines": "134-291",
        "on_yearly_pool_entry_line": "3377",
        "yearly_group_pool_entry_line": "227",
        "caller_semantics": (
            "the event is a weight-one-hundred candidate in both reviewed yearly "
            "event pools. When selected, it reflects on one appropriate family "
            "memory after the event's own trigger and five-year cooldown pass"
        ),
        "frequency_boundary": (
            "the exact annual probability depends on the surrounding valid groups "
            "and candidates. The event itself declares a five-year cooldown"
        ),
        "trigger_boundary": (
            "Friends and Foes must be active; ROOT must have a house and positive "
            "stress, must be neither callous nor sadistic, and must own at least "
            "one appropriate family memory"
        ),
        "immediate_effect": (
            "randomly saves one appropriate memory as family_memory, then saves one "
            "non-rival participant from ROOT's house as family_memory_participant"
        ),
        "scope_boundary": (
            "R416 proves a distinct dead family_memory_participant plus the opaque "
            "character_memory scope. The alive-participant and family_first option "
            "projections remain source-known but are not admitted by this contract"
        ),
        "option_semantics": {
            0: (
                "requires family_first, grants minor dynasty prestige, and applies "
                "minor stress loss; this row was not rendered in R416"
            ),
            1: (
                "requires the participant to be dead and applies a deterministic "
                "minor stress gain with no other authored effect"
            ),
            2: (
                "requires the participant to be alive and applies minuscule stress "
                "loss; this row was not rendered in R416"
            ),
            3: (
                "requires the participant to be dead and runs a diplomacy-10 duel. "
                "Success triggers bp1_yearly.4001, reduces stress, and gives close "
                "family opinion; failure triggers the same follow-up and adds medium "
                "stress. Several traits add further stress to choosing the row"
            ),
            4: (
                "requires the participant to be alive, pays that character minor "
                "gold, progresses friendship, grants grateful opinion, and usually "
                "reduces stress; this row was not rendered in R416"
            ),
        },
        "native_ai_weights": {
            0: "base 1000",
            1: "base 100",
            2: "base 100",
            3: "base 100, reduced to zero for shy or cynical AI",
            4: (
                "base 25, reduced to zero below major_gold_value or for greedy, "
                "honest, or arbitrary AI"
            ),
        },
        "after_effect": None,
        "follow_up_event": (
            "only authored option 4/native 3 triggers bp1_yearly.4001 after its "
            "diplomacy duel; the selected native 1 branch has no follow-up"
        ),
        "repeatability": "the event declares a five-year cooldown",
        "safe_option_rationale": (
            "authored option 2/native 1 is the only rendered route with a fully "
            "deterministic source effect. It accepts minor stress gain and avoids "
            "native 3's diplomacy duel, possible medium stress gain, and follow-up"
        ),
    },
}


VANILLA_BP1_YEARLY_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "bp1_yearly.1040": {
        "exemplars": [{
            "run": "R416",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-02.json"
            ),
            "artifact_sha256": (
                "1D965717FBA5B1FEA8654060091431BA23086BEF22375B1A44AEC67DDBE1F22C"
            ),
            "date_raw": 53804184,
            "event_instance_id": 1078,
            "root_character_id": 32904,
            "snapshot_id": "native:270",
            "revision": 271,
            "native_revision": 270,
            "saved_character_ids": {
                "new_friend": 50387675,
            },
            "saved_scope_raw_types": {
                "new_friend": 4,
            },
            "rendered_native_option_indices": [0, 2],
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
        }, {
            "run": "R416-retry-03",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-03.json"
            ),
            "artifact_sha256": (
                "7F2523869BEAFBC279D9ACDE65CB48661CCD1773D6CE40EB366E5EC5C9CB109A"
            ),
            "date_raw": 53804184,
            "event_instance_id": 1078,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:271",
            "starting_revision": 272,
            "ending_snapshot_id": "native:272",
            "ending_revision": 273,
            "selected_option_number": 3,
            "selected_native_option_index": 2,
            "postcondition_verified": True,
            "next_event_definition_key": "tgp_movement_events.0110",
            "next_event_instance_id": 1079,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
    "bp1_yearly.4000": {
        "exemplars": [{
            "run": "R416-retry-10",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-10.json"
            ),
            "artifact_sha256": (
                "F05201BCDD0D441F199C56D65D8BF8CF59E1B1F7570226101985BA4E2A29D62F"
            ),
            "date_raw": 53902032,
            "event_instance_id": 1090,
            "root_character_id": 32904,
            "snapshot_id": "native:1498",
            "revision": 1499,
            "native_revision": 1498,
            "saved_character_ids": {
                "family_memory_participant": 67046,
            },
            "saved_scope_raw_types": {
                "family_memory": 34,
                "family_memory_participant": 4,
            },
            "rendered_native_option_indices": [1, 3],
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
        }, {
            "run": "R416-retry-11",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-11.json"
            ),
            "artifact_sha256": (
                "E4DC093D890449A3F9FAE85FD40BE733FBDDBB7322CF31EBBA314E2F0E57D51F"
            ),
            "date_raw": 53902032,
            "event_instance_id": 1090,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1499",
            "starting_revision": 1500,
            "ending_snapshot_id": "native:1500",
            "ending_revision": 1501,
            "selected_option_number": 2,
            "selected_native_option_index": 1,
            "postcondition_verified": True,
            "next_event_definition_key": "health.2202",
            "next_event_instance_id": 1091,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_BP1_YEARLY_ANALYSIS",
    "VANILLA_BP1_YEARLY_OBSERVATIONS",
    "VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS",
]
