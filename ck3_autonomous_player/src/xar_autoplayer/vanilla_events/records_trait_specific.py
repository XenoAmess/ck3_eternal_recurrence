"""Reusable CK3 1.19.0.6 records for vanilla trait-specific events.

Campaign identities and dates are retained only as observations.  The
timeline contract can therefore be reused by the CK3 player, other mods, and
read-only MCP consumers on another operator or machine.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "trait_specific.4001": {
        # Every source-authored immediate branch produces witch.  An existing
        # courtier also produces old_courtier, while only the generated branch
        # produces created_witch and can additionally produce witch_secret.
        # Bind each exact shape before choosing the source-authored refusal,
        # which only grants piety and does not start native option 0's scheme.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "witch": (PLAYER_SENTINEL,),
        },
        "optional_unique_character_scope_excludes": {
            "created_witch": (PLAYER_SENTINEL,),
        },
        "optional_character_scope_matches_any": {
            "created_witch": ("witch",),
        },
        "scope_types": {
            "witch": "character",
        },
        "optional_scope_types": {
            "created_witch": "character",
            "witch_secret": "secret",
            "old_courtier": "boolean",
        },
        "boolean_scopes": (),
        "boolean_scope_name_sets": ((), ("old_courtier",)),
        "saved_scope_name_sets": (
            ("witch",),
            ("old_courtier", "witch"),
            ("created_witch", "witch"),
            ("created_witch", "witch_secret", "witch"),
        ),
        "saved_scope_counts": (1, 2, 3),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "trait_specific.8001": {
        # The event has no immediate or after effect and saves no scopes.  The
        # second option is a deterministic minor-gold gain; the first starts a
        # learning duel that can add a trait, a ten-year modifier, or nothing.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {},
        "saved_scope_name_sets": ((),),
        "saved_scope_count": 0,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TRAIT_SPECIFIC_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "trait_specific.4001": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/trait_specific_events/trait_specific_events.txt": (
                "A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/on_action/_on_actions.info": (
                "2BFBBF903D55A2417C988CAF1479EF0FF91719C55128CE6357BCA3D2C8E9B25F"
            ),
            "common/scripted_triggers/00_available_for_events_triggers.txt": (
                "5566A89A7D93BFB80DCF5A2F065BE0F058BE13E0B84470D1182B82D8D6384A44"
            ),
            "common/scripted_triggers/00_crime_triggers.txt": (
                "879A7E089411A5A36F84CC7E19F93B033622A92161584A248330E809D23A2ABD"
            ),
            "common/scripted_effects/00_witch_effects.txt": (
                "A7AAC7FDEDE0448309CC5B861E5B7FA60748650FE1D2D4DAF0D3D3D9E1593F56"
            ),
            "common/scripted_effects/00_secret_effects.txt": (
                "6148F1C0F0AA1EEA6FC68BB9908C6B59EAC3A50C23183405CDB1BFB4C338BEA8"
            ),
            "common/modifiers/00_event_modifiers.txt": (
                "546ADC3AF9413031228928C0621829791F843D7E93450C9EEC2C5E2CEC18187E"
            ),
            "common/schemes/scheme_types/convert_to_witchcraft_scheme.txt": (
                "4E01D8D6ECFCFEEA3A02E95FFFB81DE1DD575D4A0F9594B8C698989A7B975418"
            ),
            "events/witch_events.txt": (
                "E9DD1797228A8D9DE342232EB3AB6F16C46914178A313F793749F1DCA36FFA79"
            ),
            "common/script_values/00_basic_values.txt": (
                "9268A54F0E425D409D9D0F20D884E0A3D0A89DF85A0B6644D56133C0C4CB0096"
            ),
        },
        "definition_lines": "584-717",
        "random_yearly_playable_pulse_lines": "2522-2563",
        "on_yearly_events_lines": "2933-3842",
        "on_yearly_pool_entry_line": "3019",
        "on_action_abi_line": "15",
        "availability_trigger_lines": "767-781",
        "witch_trigger_lines": "6-15",
        "create_witch_effect_lines": "162-208",
        "witch_secret_effect_lines": "116-179",
        "focused_reading_modifier_lines": "437-440",
        "conversion_scheme_lines": ("1-22", "299-364"),
        "conversion_outcome_event_lines": "353-490",
        "piety_value_lines": ("1121", "1154"),
        "caller_semantics": (
            "random_yearly_playable_pulse runs once at an independently random "
            "point each year for each playable character; after its validity "
            "trigger, on_yearly_events has group weight six, then a twenty-five "
            "percent chance to choose from its valid weighted pool where this "
            "event has weight fifty"
        ),
        "frequency_boundary": (
            "the exact per-year probability is not constant because the outer "
            "DLC/on-action groups and inner event candidates are filtered and "
            "weighted at runtime; this is a yearly-pulse candidate, not a daily "
            "event, and the event defines no cooldown or one-shot flag"
        ),
        "trigger_boundary": (
            "root is not already a witch; a non-landless-adventurer root must "
            "also not be travelling. Event weight is reduced by an extreme "
            "special-content trait or zealous and increased by learning and by "
            "already having a witch courtier or guest"
        ),
        "immediate_effect": (
            "selects an existing witch courtier/guest when possible and brings "
            "a guest to court; otherwise selects a witch pool character near "
            "the capital and adds that character as a courtier; if neither "
            "exists, creates a same-culture, same-faith witch at the capital, "
            "may make sexuality compatible with root, gives the witch trait or "
            "witch secret according to faith criminality, saves created_witch, "
            "aliases it as witch, and adds it as root's courtier"
        ),
        "source_scope_variants": (
            "the existing-courtier branch saves boolean old_courtier plus "
            "character witch; the pool-character branch saves only witch; "
            "the generated branch saves character created_witch and aliases "
            "it as witch, with witch_secret additionally present when the "
            "creation effect uses the secret path"
        ),
        "generated_witch_side_effects": (
            "the generated character can receive secret_witch instead of the "
            "witch trait when witchcraft is shunned or criminal; either path "
            "has an independent ten-percent chance to replace an eligible "
            "legend opening chapter and emit its interface toast"
        ),
        "option_semantics": {
            0: (
                "adds focused_reading_modifier for five years, granting learning "
                "plus one, and has witch start the secret convert_to_witchcraft "
                "scheme against root; that scheme uses learning, has a two-month "
                "cooldown and later resolves discovery/success into the witch.2002 "
                "player choice chain"
            ),
            1: (
                "adds medium_piety_gain, whose exact-build value is one hundred; "
                "it does not start the conversion scheme or add the reading modifier"
            ),
        },
        "conversion_outcome_boundary": (
            "native option 0 does not instantly convert root: if its scheme later "
            "reaches the player-only witch.2002 outcome, discovery can first reveal "
            "the owner's witch secret to root. The later accept choice gives root "
            "the witch secret or trait, can lose one hundred piety where witchcraft "
            "is not accepted, triggers witch.2003 for the owner, and has zealous/"
            "craven stress impacts. The later refusal gains one hundred piety, "
            "triggers witch.2004 for the owner, and when discovered applies the "
            "source-authored disappointed-opinion reversal plus ambitious stress. "
            "A third, discovery-only exposure choice gains one hundred piety, "
            "applies the hate-opinion reversal, displays exposure of the owner's "
            "witch secret, triggers witch.2005, and has craven/compassionate/"
            "trusting stress impacts; these are downstream player choices, not "
            "automatic direct effects of trait_specific.4001 native option 0"
        ),
        "after_effect": None,
        "repeatability": (
            "the event defines no cooldown, one-shot flag, or occurrence ceiling; "
            "a root that remains non-witch can qualify in a later yearly pulse"
        ),
        "safe_option_rationale": (
            "native option 1 is the only route that avoids starting a secret "
            "conversion scheme against the player and avoids the five-year "
            "modifier; its complete direct event effect is the source-defined "
            "gain of one hundred piety"
        ),
        "religion_scope_boundary": (
            "the reusable decision records the exact piety gain and the observed "
            "witch-secret creation fact only; religion is owner-deferred and no "
            "general faith, doctrine, conversion, or religious policy is inferred"
        ),
    },
    "trait_specific.8001": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/trait_specific_events/trait_specific_events.txt": (
                "A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "1148-1226",
        "on_yearly_pool_entry_line": "3029",
        "caller_semantics": (
            "the general yearly event pool lists this event at weight one "
            "hundred after the outer yearly playable pulse and pool gates"
        ),
        "trigger_boundary": (
            "root is not a landless adventurer and does not already have the "
            "lifestyle_herbalist trait; learning increases event weight"
        ),
        "immediate_effect": None,
        "option_semantics": {
            0: (
                "runs a learning duel against average skill: one outcome adds "
                "lifestyle_herbalist, one adds seeker_of_knowledge for ten years, "
                "and one has no scripted gameplay effect; result toasts are UI"
            ),
            1: "adds the source-defined minor_gold_value to root",
        },
        "selected_choice_effect_profile": {
            "schema": "xar.ck3.vanilla-event-choice-effect",
            "schema_version": 1,
            "selected_native_option_index": 1,
            "completeness": "selected-option-and-common-after-source-reviewed",
            "selected_option_effects": [{
                "domain": "currency",
                "subject": "root",
                "operation": "add_gold",
                "authored_value_key": "minor_gold_value",
                "authored_minimum_whole": 15,
                "runtime_delta_exact": False,
                "runtime_delta_reason": (
                    "minor_gold_value depends on monthly income, treasury and era"
                ),
            }],
            "common_after_effects": [],
            "observable_postcondition": {
                "metric": "played_character_gold.raw",
                "expected_relation": "strictly_increasing",
                "scale": 100000,
                "material_change_required_for_evidence": True,
            },
            "source_anchors": [
                "events/trait_specific_events/trait_specific_events.txt:1221-1225",
                "common/script_values/01_dynamic_values.txt:53-70",
                "common/script_values/00_basic_values.txt:49-64",
            ],
            "source_sha256": {
                "events/trait_specific_events/trait_specific_events.txt": (
                    "A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7"
                ),
                "common/script_values/01_dynamic_values.txt": (
                    "049303EFF8ABFDFCADCC31D27E2633A26A2E877E4E2980D4A42C53D6B76D7064"
                ),
                "common/script_values/00_basic_values.txt": (
                    "9268A54F0E425D409D9D0F20D884E0A3D0A89DF85A0B6644D56133C0C4CB0096"
                ),
            },
        },
        "after_effect": None,
        "repeatability": (
            "the event defines no cooldown or one-shot flag; choosing native1 "
            "does not add herbalist, so a later yearly pool can select it again"
        ),
        "safe_option_rationale": (
            "native1 is deterministic positive gold and avoids native0's random "
            "trait or ten-year modifier mutation"
        ),
    },
}


VANILLA_TRAIT_SPECIFIC_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "trait_specific.4001": {
        "exemplars": [{
            "run": "R374",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "trait-specific-4001-red-report.json"
            ),
            "artifact_sha256": (
                "9FDF93D053E001C73D9DC469DDE37BC44C3DA8F1872AC3E587C10241EA27FB51"
            ),
            "park_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "hot-recovery-park-6.json"
            ),
            "park_artifact_sha256": (
                "A94103B7788591FFD3379BEB418E6EC7DE675AA0FC4BB252DDB658086BED6A49"
            ),
            "driver_state_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "driver-state-park-6-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "750EEEB9AC789F075CCA2C9F5AC2E2619D3F6DABE9E12744FE26D25E3C1292ED"
            ),
            "date_raw": 53583192,
            "event_instance_id": 1040,
            "root_character_id": 32904,
            "saved_character_ids": {
                "created_witch": 94245,
                "witch": 94245,
            },
            "saved_scope_raw_types": {
                "created_witch": 4,
                "witch_secret": 7,
                "witch": 4,
            },
            "rendered_native_option_indices": [0, 1],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 51852,
            "snapshot_id": "native:1669",
            "revision": 1670,
            "remaining_game_days": 2196,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }, {
            "run": "R414",
            "kind": "scope-variant-pre-selection-live-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/"
                "terminal-stages-red-attempt-03.json"
            ),
            "artifact_sha256": (
                "ADD23E60298C513E31B8E663CF2362B4579CFFE81FDF35F9A77822498A2EDBFB"
            ),
            "date_raw": 53681976,
            "event_instance_id": 1067,
            "root_character_id": 32904,
            "saved_character_ids": {
                "witch": 94245,
            },
            "saved_scope_raw_types": {
                "old_courtier": 2,
                "witch": 4,
            },
            "rendered_native_option_indices": [0, 1],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 202268,
            "snapshot_id": "native:660",
            "revision": 661,
            "process_restart_required": False,
            "retained_red": True,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
    "trait_specific.8001": {
        "exemplars": [{
            "run": "R414-attempt-06",
            "kind": "pre-selection-live-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/"
                "terminal-stages-red-attempt-06.json"
            ),
            "artifact_sha256": (
                "BEEB7C1C2FE0A30FA056ABCED1C28EA83BD0739DC0D1225BE4CA1C3C738700E6"
            ),
            "date_raw": 53783472,
            "event_instance_id": 1075,
            "root_character_id": 32904,
            "saved_scope_raw_types": {},
            "rendered_native_option_indices": [0, 1],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 202268,
            "snapshot_id": "native:1913",
            "revision": 1914,
            "process_restart_required": False,
            "retained_red": True,
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
    "VANILLA_TRAIT_SPECIFIC_ANALYSIS",
    "VANILLA_TRAIT_SPECIFIC_OBSERVATIONS",
    "VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS",
]
