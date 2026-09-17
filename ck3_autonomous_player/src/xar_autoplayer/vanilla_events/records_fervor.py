"""Exact-build event-continuity record for the fervor scandal notice.

This module does not expose or implement a general religion policy.  It only
binds the exact forced ``fervor.1002`` window observed in R860 to the
source-reviewed terminal option with the smallest persistent side effects.
"""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_FERVOR_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "fervor.1002": {
        # The sinful-priest and faith-fervor changes have already happened in
        # fervor.1001.  Authored option 3 only applies bounded personality
        # stress; unlike options 1 and 2 it changes no resource, opinion, or
        # relationship state.  Bind the complete R860 projection so this does
        # not become a generic religion-event or lowest-index policy.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "sinful_theocrat": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "sinful_theocrat": "character",
            "scandal_type": "flag",
            "dummy_servant_gender": "character",
            "dummy_clergy_gender": "character",
            "scoped_primary_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sinful_theocrat",
            "scandal_type",
            "dummy_servant_gender",
            "dummy_clergy_gender",
            "scoped_primary_title",
        ),),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_FERVOR_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "fervor.1002": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/religion_events/fervor_events.txt": (
                "06807E780BFF670DD8319B9A54270952990DD146BC5B069420DFDE3E784B3F63"
            ),
            "common/on_action/religion_on_actions.txt": (
                "52D172C10A8164B007382F9DF79A48DE462CF6B390438158FD37C9B34DF8F75C"
            ),
            "common/script_values/00_basic_values.txt": (
                "9268A54F0E425D409D9D0F20D884E0A3D0A89DF85A0B6644D56133C0C4CB0096"
            ),
            "common/script_values/00_stress_values.txt": (
                "104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395"
            ),
        },
        "monthly_faith_dispatch_lines": "576-585",
        "fervor_pulse_lines": "898-910",
        "hidden_caller_definition_lines": "57-627",
        "recipient_dispatch_lines": ("543-556", "570-614"),
        "definition_lines": "633-966",
        "immediate_effect_lines": "849-899",
        "option_lines": "901-965",
        "caller_semantics": (
            "the monthly faith pulse can select hidden event fervor.1001 when a "
            "reformed faith has no recent_fervor_event cooldown and has a valid "
            "sinful theocrat. That hidden event applies the theocrat piety-level "
            "and faith-fervor losses, then sends fervor.1002 to qualifying players"
        ),
        "trigger_boundary": (
            "the player is a same-faith recipient other than sinful_theocrat; "
            "ordinary-theocrat notices additionally require a source-authored "
            "personal relationship such as court chaplain, spouse, vassal, liege, "
            "friend, lover, rival, or close family"
        ),
        "immediate_effect": (
            "show_as_tooltip repeats the piety-level and faith-fervor changes that "
            "already occurred in fervor.1001; it does not apply those changes again"
        ),
        "scope_boundary": (
            "R860 observed sinful_theocrat, opaque scandal_type, the two dummy "
            "gender character scopes, and scoped_primary_title. Other scope shapes "
            "remain fail-closed rather than generalizing religion state"
        ),
        "option_semantics": {
            0: (
                "gains 100 piety, gives sinful_theocrat 30 negative opinion of "
                "ROOT, can create a rivalry when scandal_type is vengeful, and "
                "applies trait-dependent stress"
            ),
            1: (
                "loses 150 prestige and 100 piety, gives sinful_theocrat 30 "
                "positive opinion of ROOT, and applies trait-dependent stress"
            ),
            2: (
                "changes no piety, prestige, opinion, or relationship; it applies "
                "minor base stress with the authored personality adjustments"
            ),
        },
        "native_ai_weights": {
            0: "no explicit ai_chance block",
            1: "no explicit ai_chance block",
            2: "no explicit ai_chance block",
        },
        "selected_choice_effect_profile": {
            "schema": "xar.ck3.vanilla-event-choice-effect",
            "schema_version": 1,
            "selected_native_option_index": 2,
            "completeness": "selected-option-and-common-after-source-reviewed",
            "selected_option_effects": [{
                "domain": "stress",
                "subject": "root",
                "operation": "stress_impact",
                "authored_value_key": "minor_stress_impact_gain",
                "authored_base_points": 20,
                "trait_adjustments": {
                    "just": "medium_stress_impact_gain",
                    "brave": "minor_stress_impact_gain",
                    "impatient": "minor_stress_impact_gain",
                    "wrathful": "minor_stress_impact_gain",
                },
                "runtime_delta_exact": False,
                "runtime_delta_reason": (
                    "character stress-impact adjustments and the stress ceiling "
                    "are not observed"
                ),
            }],
            "common_after_effects": [],
            "observable_postcondition": {
                "metric": "played_character.stress_points",
                "expected_relation": "non_decreasing",
                "material_change_required_for_evidence": True,
            },
            "source_anchors": [
                "events/religion_events/fervor_events.txt:954-965",
                "common/script_values/00_stress_values.txt:27-28",
            ],
            "source_sha256": {
                "events/religion_events/fervor_events.txt": (
                    "06807E780BFF670DD8319B9A54270952990DD146BC5B069420DFDE3E784B3F63"
                ),
                "common/script_values/00_stress_values.txt": (
                    "104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395"
                ),
            },
        },
        "selected_choice_campaign_utility_profile": {
            "schema": "xar.ck3.vanilla-event-campaign-utility",
            "schema_version": 1,
            "selected_native_option_index": 2,
            "objective_id": (
                "resolve_fervor_scandal_without_resource_or_relationship_commitment"
            ),
            "comparison_kind": "source_reviewed_ordinal",
            "selected_rank": 1,
            "rank_count": 3,
            "selected_utility": {
                "material_direction": "bounded_stress_cost",
                "outcome_variance": "bounded",
                "persistent_state_risk": "none_authored",
                "timeline_value": "required_to_continue",
            },
            "alternatives": [{
                "native_option_index": 0,
                "reason": "negative opinion and conditional rivalry",
            }, {
                "native_option_index": 1,
                "reason": "fixed prestige and piety costs",
            }],
            "cross_event_numeric_score": None,
            "calibration_status": "not_calibrated",
            "decision_scope": "bounded_timeline_continuation",
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "fervor.1001 sets the faith-level recent_fervor_event variable for "
            "1460 days. After it expires, the monthly pulse may produce another "
            "qualifying scandal; fervor.1002 has no one-shot occurrence ceiling"
        ),
        "safe_option_rationale": (
            "authored option 3/native 2 is the only terminal route with no "
            "resource, opinion, or relationship mutation. Its declared downside "
            "is bounded personality stress, so this is a conservative timeline "
            "continuation rather than a general religion decision"
        ),
        "domain_boundary": (
            "exact-key forced-event continuity only; no faith, doctrine, tenet, "
            "fervor, conversion, reform, or holy-order policy is exposed"
        ),
    },
}


VANILLA_FERVOR_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "fervor.1002": {
        "exemplars": [{
            "run": "R860",
            "kind": "production-degraded-choice-b1",
            "date_raw": 53223216,
            "event_instance_id": 4,
            "root_character_id": 31853,
            "snapshot_id": "native:63",
            "revision": 64,
            "native_revision": 63,
            "saved_character_ids": {
                "sinful_theocrat": 56125,
                "dummy_servant_gender": 1,
                "dummy_clergy_gender": 1,
            },
            "saved_scope_raw_types": {
                "sinful_theocrat": 4,
                "scandal_type": 3,
                "dummy_servant_gender": 4,
                "dummy_clergy_gender": 4,
                "scoped_primary_title": 5,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "ending_event_instance_id": None,
            "formal_report_sha256": (
                "4BA536C7AF000F3BDA030025A8C3BB2E1B1898C11CA9A87310012191F4CE38F2"
            ),
            "driver_state_sha256": (
                "33A16D8C75090F0B3A9CCAAD6E328CA99E0F8C5B3F38D62E5A21F4AF15D5F3F8"
            ),
            "source_reviewed_option_live_pending": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "VANILLA_FERVOR_ANALYSIS",
    "VANILLA_FERVOR_OBSERVATIONS",
    "VANILLA_FERVOR_TIMELINE_CONTRACTS",
]
