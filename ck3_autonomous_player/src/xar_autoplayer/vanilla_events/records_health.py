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
    "health.3001": {
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
            "localization/english/event_localization/health_events_l_english.yml": (
                "043216116C522B5D108315A3730DA12C5D7B2EDDB8CF60D67D0967AF4AFE23D0"
            ),
            "localization/simp_chinese/event_localization/"
            "health_events_l_simp_chinese.yml": (
                "AFDC39A947F036A140288CC565EDE0B2CC29B1DCD27AF191A7CC0F91A026A0E4"
            ),
        },
        "definition_lines": "6667-7276",
        "trigger_lines": "6701-6703",
        "immediate_effect_lines": "6705-7075",
        "option_lines": "7077-7257",
        "after_effect_lines": "7259-7275",
        "set_physician_effect_lines": "1308-1408",
        "caller_semantics": (
            "the event is scheduled by source-authored physician-search routes. "
            "The R416 caller is health.1006 native 0, which retained epidemic, "
            "disease_type, sick_character, and new_memory until this event opened"
        ),
        "trigger_boundary": "ROOT must still have a capital province",
        "immediate_effect": (
            "for a player ROOT, searches or generates an excellent candidate only "
            "for a learned ruler, always searches or generates distinct high- and "
            "low-skill candidates, and optionally finds a mystic candidate"
        ),
        "scope_boundary": (
            "the reviewed base shape has disease_type, sick_character, and the two "
            "candidate characters. The R416 health.1006 path legally retains "
            "epidemic and new_memory as an exact six-scope variant; those inherited "
            "scopes do not change the rendered option projection"
        ),
        "option_semantics": {
            0: (
                "hires the excellent candidate for the high physician cost; visible "
                "only when excellent_skill_option exists"
            ),
            1: (
                "hires the high-skill candidate for the high physician cost and "
                "appoints that character as court physician"
            ),
            2: (
                "hires the low-skill candidate for the low physician cost and "
                "appoints that character as court physician"
            ),
            3: (
                "hires the optional mystic candidate for the low physician cost, "
                "also paying medium_piety_loss"
            ),
            4: "declines every candidate and recruits no court physician",
        },
        "native_ai_weights": {
            0: "base 500, zero when short-term gold is below medium_gold_value",
            1: "base 100, zero when short-term gold is below medium_gold_value",
            2: "base 100",
            3: (
                "base 30, zero below minor_gold_value, then modified by AI zeal"
            ),
            4: "base 1",
        },
        "after_effect": (
            "if ROOT is seeking epidemic treatment and now has a court physician, "
            "saves that physician and schedules physician_epidemic_events.1020 in "
            "three days; always removes health_3001_hire_physician_decision_text"
        ),
        "follow_up_event": (
            "set_court_physician_effect schedules health.3101 for a treatable ROOT "
            "without recent treatment, using the configured ruler treatment delay"
        ),
        "safe_option_rationale": (
            "in the observed native 1/2/4 projection, authored option 2/native 1 "
            "appoints the high-skill candidate and opens the reviewed treatment "
            "path. Native 2 hires the lower-skill candidate, while native 4 leaves "
            "the already sick player untreated"
        ),
    },
    "health.3101": {
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
            "localization/english/event_localization/health_events_l_english.yml": (
                "043216116C522B5D108315A3730DA12C5D7B2EDDB8CF60D67D0967AF4AFE23D0"
            ),
            "localization/simp_chinese/event_localization/"
            "health_events_l_simp_chinese.yml": (
                "AFDC39A947F036A140288CC565EDE0B2CC29B1DCD27AF191A7CC0F91A026A0E4"
            ),
        },
        "definition_lines": "7314-7524",
        "trigger_lines": "7471-7474",
        "immediate_effect_lines": "7480-7486",
        "option_lines": "7488-7523",
        "safe_treatment_effect_lines": "1581-1713",
        "risky_treatment_effect_lines": "1716-1897",
        "mystic_treatment_effect_lines": "1899-2087",
        "no_treatment_effect_lines": "2089-2091",
        "caller_semantics": (
            "a newly appointed physician schedules this event for a treatable "
            "player without recent treatment. The R416 delivery follows "
            "health.1006 native 0 and health.3001 native 1 in the same event frame"
        ),
        "trigger_boundary": (
            "ROOT must still have a treatable disease and an available court physician"
        ),
        "immediate_effect": (
            "re-saves the available court physician, saves ROOT's worst disease as "
            "disease_type, and saves the physician's location as "
            "background_terrain_scope when available"
        ),
        "scope_boundary": (
            "the reviewed base shape carries the sick player, disease, high and low "
            "recruitment candidates, the physician matching the high-skill candidate, "
            "and the physician location. R416 legally retains epidemic and new_memory "
            "as an exact eight-scope variant without changing options"
        ),
        "option_semantics": {
            0: (
                "runs safe_disease_treatment_effect. Its result is still stochastic: "
                "the source weights ordinary success against failure and permits a "
                "hostile physician to fail deliberately"
            ),
            1: (
                "runs risky_disease_treatment_effect, whose source-authored outcome "
                "range includes stronger successes and harsher failures"
            ),
            2: (
                "runs mystic_disease_treatment_effect and is visible only when the "
                "physician has a mystic lifestyle trait"
            ),
            3: "runs no_disease_treatment_effect and provides no treatment",
        },
        "native_ai_weights": {
            0: "base 10",
            1: "base 1",
            2: "base 0.5, reduced to zero when AI zeal is nonnegative",
            3: "base 0",
        },
        "after_effect": None,
        "follow_up_event": (
            "safe treatment schedules health.3103 on success or health.3104 on "
            "failure; the exact branch remains random and must be observed"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is the source-labelled safe treatment. It "
            "does not guarantee success, but it avoids the risky route's harsher "
            "outcome range and native 3's certain absence of treatment"
        ),
    },
    "health.3102": {
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
            "localization/english/event_localization/health_events_l_english.yml": (
                "043216116C522B5D108315A3730DA12C5D7B2EDDB8CF60D67D0967AF4AFE23D0"
            ),
            "localization/simp_chinese/event_localization/"
            "health_events_l_simp_chinese.yml": (
                "AFDC39A947F036A140288CC565EDE0B2CC29B1DCD27AF191A7CC0F91A026A0E4"
            ),
        },
        "definition_lines": "7527-7708",
        "trigger_lines": "7624-7630",
        "immediate_effect_lines": "7636-7642",
        "option_lines": "7645-7707",
        "safe_treatment_effect_lines": "1581-1713",
        "set_physician_effect_lines": "1308-1408",
        "decide_treatment_picker_effect_lines": "3546-3564",
        "liege_picks_treatment_effect_lines": "3566-3578",
        "caller_semantics": (
            "when a newly appointed physician iterates sick courtiers or guests, "
            "decide_who_picks_disease_treatment_effect schedules health.3102 for "
            "the liege when the native responsibility trigger selects that liege. "
            "R416 opened this window for courtier 88187 after the player's own "
            "successful treatment result was acknowledged"
        ),
        "trigger_boundary": (
            "sick_character must remain alive with a treatable disease and ROOT's "
            "court physician must remain available"
        ),
        "immediate_effect": (
            "re-saves ROOT's court physician, updates sick_character's worst disease "
            "as disease_type, and saves the patient's location as the background"
        ),
        "scope_boundary": (
            "the exact R416 projection retains epidemic/new_memory and the preceding "
            "high/low recruitment candidates. ROOT is the played liege, the patient "
            "is a distinct third party, and physician matches high_skill_option"
        ),
        "option_semantics": {
            0: "uses the physician's safe disease treatment on sick_character",
            1: "uses the physician's risky disease treatment on sick_character",
            2: (
                "uses mystic treatment when the physician has a mystic lifestyle "
                "trait; this row was not rendered in R416"
            ),
            3: "denies treatment to sick_character",
            4: (
                "lets sick_character decide and schedules that character's own "
                "health.3101 treatment window after five to ten days"
            ),
        },
        "native_ai_weights": {
            0: "base 10",
            1: "base 1",
            2: "base 0.5, reduced to zero when AI zeal is nonnegative",
            3: "base 1",
            4: "base 0",
        },
        "after_effect": None,
        "safe_option_rationale": (
            "authored option 1/native 0 is the source-labelled safe treatment for "
            "the sick courtier. It avoids the risky result range, explicit denial, "
            "and a delayed second choice window while preserving the patient identity"
        ),
    },
    "health.3103": {
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
            "localization/english/event_localization/health_events_l_english.yml": (
                "043216116C522B5D108315A3730DA12C5D7B2EDDB8CF60D67D0967AF4AFE23D0"
            ),
            "localization/simp_chinese/event_localization/"
            "health_events_l_simp_chinese.yml": (
                "AFDC39A947F036A140288CC565EDE0B2CC29B1DCD27AF191A7CC0F91A026A0E4"
            ),
        },
        "definition_lines": "7712-7797",
        "trigger_lines": None,
        "immediate_effect_lines": "7774-7781",
        "option_lines": "7783-7785",
        "after_effect_lines": "7787-7796",
        "disease_treatment_results_effect_lines": "2746-3128",
        "inform_liege_effect_lines": "3940-4030",
        "caller_semantics": (
            "safe_disease_treatment_effect schedules this result when its weighted "
            "outcome is success. R416 reached it immediately after health.3101 "
            "authored option 1/native 0 in the same event frame"
        ),
        "trigger_boundary": "the event defines no trigger block of its own",
        "immediate_effect": (
            "applies the source-authored safe-treatment success modifiers, schedules "
            "the later return visit, informs a responsible liege when applicable, "
            "saves treatment/outcome, saves the physician as portrait when distinct "
            "from the patient, and refreshes the physician-location background"
        ),
        "scope_boundary": (
            "the reviewed recruitment shape keeps the sick player, high/low "
            "candidates, appointed physician, treatment picker, disease, result, "
            "portrait, and background. R332 proves an existing-physician eight-scope "
            "variant; R416 additionally proves the exact twelve-scope consumption "
            "variant retaining epidemic and new_memory"
        ),
        "option_semantics": {
            0: (
                "the only authored option acknowledges a success whose treatment "
                "effects were already applied in immediate; it has no authored body"
            ),
        },
        "native_ai_weights": {0: "sole authored acknowledgement; no ai_chance block"},
        "after_effect": (
            "when the global tutorial completion variable exists, adds "
            "force_court_positions_tutorial to ROOT"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is the sole visible and enabled row. Because "
            "the success effects already ran before rendering, dismissal only closes "
            "the result window"
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
        }, {
            "run": "R416-retry-06",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-06.json"
            ),
            "artifact_sha256": (
                "0A19C4E378730320173A6F34A99C3724D043432E6529D8496715CA920C30569B"
            ),
            "date_raw": 53864592,
            "event_instance_id": 1084,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1026",
            "starting_revision": 1027,
            "ending_snapshot_id": "native:1027",
            "ending_revision": 1028,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
    "health.3001": {
        "exemplars": [{
            "run": "R197",
            "kind": "legacy-live-binding",
            "review_kind": "source-correlated-historical-live",
            "date_raw": 53176968,
            "root_character_id": 32904,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 49718,
                "low_skill_option": 36369,
            },
            "rendered_native_option_indices": [1, 2, 4],
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        }, {
            "run": "R416-retry-06",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-06.json"
            ),
            "artifact_sha256": (
                "0A19C4E378730320173A6F34A99C3724D043432E6529D8496715CA920C30569B"
            ),
            "date_raw": 53864784,
            "event_instance_id": 1085,
            "root_character_id": 32904,
            "snapshot_id": "native:1031",
            "revision": 1032,
            "native_revision": 1031,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 33648496,
                "low_skill_option": 16889335,
            },
            "saved_scope_raw_types": {
                "epidemic": 50,
                "disease_type": 3,
                "sick_character": 4,
                "new_memory": 34,
                "high_skill_option": 4,
                "low_skill_option": 4,
            },
            "rendered_native_option_indices": [1, 2, 4],
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
            "run": "R416-retry-07",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-07.json"
            ),
            "artifact_sha256": (
                "EDBE88226F5CB6C31632359164BC050E9ACD7B84687864EE7A368B7125B9F799"
            ),
            "date_raw": 53864784,
            "event_instance_id": 1085,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1032",
            "starting_revision": 1033,
            "ending_snapshot_id": "native:1033",
            "ending_revision": 1034,
            "selected_option_number": 2,
            "selected_native_option_index": 1,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
    "health.3101": {
        "exemplars": [{
            "run": "R198",
            "kind": "legacy-live-binding",
            "review_kind": "source-correlated-historical-live",
            "date_raw": 53177016,
            "root_character_id": 32904,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 49718,
                "low_skill_option": 36369,
                "physician": 49718,
            },
            "rendered_native_option_indices": [0, 1, 3],
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        }, {
            "run": "R416-retry-07",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-07.json"
            ),
            "artifact_sha256": (
                "EDBE88226F5CB6C31632359164BC050E9ACD7B84687864EE7A368B7125B9F799"
            ),
            "date_raw": 53864832,
            "event_instance_id": 1086,
            "root_character_id": 32904,
            "snapshot_id": "native:1035",
            "revision": 1036,
            "native_revision": 1035,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 33648496,
                "low_skill_option": 16889335,
                "physician": 33648496,
            },
            "saved_scope_raw_types": {
                "epidemic": 50,
                "disease_type": 3,
                "sick_character": 4,
                "new_memory": 34,
                "high_skill_option": 4,
                "low_skill_option": 4,
                "physician": 4,
                "background_terrain_scope": 8,
            },
            "rendered_native_option_indices": [0, 1, 3],
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
            "run": "R416-retry-08",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-08.json"
            ),
            "artifact_sha256": (
                "450A3848A536FF28CFB470A7E3690341831805F4B17178C66B82DB8257905654"
            ),
            "date_raw": 53864832,
            "event_instance_id": 1086,
            "ending_event_instance_id": 1087,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1036",
            "starting_revision": 1037,
            "ending_snapshot_id": "native:1037",
            "ending_revision": 1038,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "observed_result_event": "health.3103",
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
    "health.3102": {
        "exemplars": [{
            "run": "R416-retry-09",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-09.json"
            ),
            "artifact_sha256": (
                "5E630E4EF04B137F132627470B27D67BA8B4148C5B9F171D5117227A9FF49DFC"
            ),
            "date_raw": 53865048,
            "event_instance_id": 1088,
            "root_character_id": 32904,
            "snapshot_id": "native:1044",
            "revision": 1045,
            "native_revision": 1044,
            "saved_character_ids": {
                "sick_character": 88187,
                "high_skill_option": 33648496,
                "low_skill_option": 16889335,
                "physician": 33648496,
            },
            "saved_scope_raw_types": {
                "epidemic": 50,
                "disease_type": 3,
                "sick_character": 4,
                "new_memory": 34,
                "high_skill_option": 4,
                "low_skill_option": 4,
                "physician": 4,
                "background_terrain_scope": 8,
            },
            "rendered_native_option_indices": [0, 1, 3, 4],
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
            "run": "R416-retry-10",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-10.json"
            ),
            "artifact_sha256": (
                "F05201BCDD0D441F199C56D65D8BF8CF59E1B1F7570226101985BA4E2A29D62F"
            ),
            "date_raw": 53865048,
            "event_instance_id": 1088,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1045",
            "starting_revision": 1046,
            "ending_snapshot_id": "native:1046",
            "ending_revision": 1047,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "next_event_definition_key": "ep3_emperor_yearly.2240",
            "next_event_instance_id": 1089,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
    "health.3103": {
        "exemplars": [{
            "run": "R199",
            "kind": "legacy-live-binding",
            "review_kind": "source-correlated-historical-live",
            "date_raw": 53177016,
            "root_character_id": 32904,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 49718,
                "low_skill_option": 36369,
                "physician": 49718,
                "treatment_picker": 32904,
                "portrait": 49718,
            },
            "rendered_native_option_indices": [0],
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        }, {
            "run": "R416-retry-08",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-08.json"
            ),
            "artifact_sha256": (
                "450A3848A536FF28CFB470A7E3690341831805F4B17178C66B82DB8257905654"
            ),
            "date_raw": 53864832,
            "event_instance_id": 1087,
            "root_character_id": 32904,
            "snapshot_id": "native:1037",
            "revision": 1038,
            "native_revision": 1037,
            "saved_character_ids": {
                "sick_character": 32904,
                "high_skill_option": 33648496,
                "low_skill_option": 16889335,
                "physician": 33648496,
                "treatment_picker": 32904,
                "portrait": 33648496,
            },
            "saved_scope_raw_types": {
                "epidemic": 50,
                "disease_type": 3,
                "sick_character": 4,
                "new_memory": 34,
                "high_skill_option": 4,
                "low_skill_option": 4,
                "physician": 4,
                "background_terrain_scope": 8,
                "treatment_picker": 4,
                "treatment": 3,
                "outcome": 3,
                "portrait": 4,
            },
            "rendered_native_option_indices": [0],
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
            "run": "R416-retry-09",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-09.json"
            ),
            "artifact_sha256": (
                "5E630E4EF04B137F132627470B27D67BA8B4148C5B9F171D5117227A9FF49DFC"
            ),
            "date_raw": 53864832,
            "event_instance_id": 1087,
            "ending_event_instance_id": None,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:1038",
            "starting_revision": 1039,
            "ending_snapshot_id": "native:1039",
            "ending_revision": 1040,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "VANILLA_HEALTH_ANALYSIS",
    "VANILLA_HEALTH_OBSERVATIONS",
]
