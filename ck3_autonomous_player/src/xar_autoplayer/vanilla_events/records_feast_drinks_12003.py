"""The observed feast_default.6231 host route with two visible drink choices."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/main_events/feast_default_events.txt"
_ACTIVITY_VALUES: Final = "common/script_values/00_activity_values.txt"
_DYNAMIC_VALUES: Final = "common/script_values/01_dynamic_values.txt"
_MODIFIERS: Final = "common/modifiers/00_activity_feast_modifiers.txt"
_SOURCES: Final = {
    _EVENT_PATH: "D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1",
    _ACTIVITY_VALUES: "0B5C2DA145CF0D2311ABA8525C7DECFC865D0539B81ACDF3974ED74A68B37C92",
    _DYNAMIC_VALUES: "023165E7D27D106A34F34D7726D938EFA8D5DCE25650EA3256E0B5EA3F73CC2A",
    "common/script_values/00_basic_values.txt":
    "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
    "common/script_values/00_stress_values.txt":
    "821A0B77244FC5EE2D87D339CB24DBEF00787B83D44EC2DF9215FC1A93AEC2D4",
    "common/script_values/07_ep3_values.txt":
    "B4B46E562BAA20F8AA7FBAC91B3D8B95F6A59D053EAF6B5F28CA9D091F85C776",
    _MODIFIERS: "4B6A39429FAF60B50D2D20A32687E4E1148CA7660235C0C2A01F3A51EC0CABEE",
    "common/scripted_triggers/00_feast_activity_triggers.txt":
    "B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA",
}

FEAST_DRINKS_12003_RECORDS: Final = {
    "feast_default.6231": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "character_scopes": {"host": PLAYER_SENTINEL},
            "scope_types": {
                "activity": "activity", "host": "character",
                "province": "province", "drunk_guest": "character",
            },
            "saved_scope_name_sets": (("activity", "host", "province", "drunk_guest"),),
            "saved_scope_count": 4,
            "option_count": 2,
            "snapshot_option_count": 4,
            "native_option_indices": (0, 1),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "occurrence_policy": "repeatable-within-product-observation-window",
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598,
            },
            "source_sha256": _SOURCES,
            "definition_lines": "10935-11098",
            "definition_block_sha256":
            "F2DD92D63941723EE6E0B4AB8E7382DC7810DFE9F26369975C56C99F5D207D62",
            "definition_hash_convention": "key token through final brace; excludes following newline",
            "event_type": "activity_event",
            "trigger_semantics": "root drinks alcohol; more than two other drinking attendees; six-month cooldown",
            "immediate_effect_lines": "10961-10977",
            "immediate_effect": "select another drinking attendee, preferring the honorary guest, and save drunk_guest",
            "option_semantics": {
                "0": "buy more wine: dynamic medium gold cost, guest opinions, ten-year prestige modifier, conditional stress/fulfillment",
                "1": "dynamic minor gold gain, prestige -75, conditional just/generous stress/fulfillment",
                "2": "reveler-gated prestige +150 and ten-year modifier; hidden in the observed frame",
                "3": "wine-cellar-gated influence +30; hidden in the observed frame",
            },
            "option_lines": {"0": "10979-11039", "1": "11041-11055", "2": "11057-11074", "3": "11076-11097"},
            "localization_sources": {
                "localization/english/event_localization/activities/feast_default_events_l_english.yml":
                "F93DFC48CE2D0D45947AFB0E918855B6CBC2CBBBEEC7578FE3E894BDD82F3004",
                "localization/simp_chinese/event_localization/activities/feast_default_events_l_simp_chinese.yml":
                "EA35C5F94BC872B0C5F3D1496ED78030C7FEDED6EAAEF6F49C90C03C288BF6FA",
            },
            "native_ai_weights": {
                "0": "base50 + ai_energy*0.5 + ai_honor*0.25 + ai_compassion*0.25",
                "1": "base50 + ai_greed*0.5",
                "2": "base500; hidden in the observed frame",
                "3": "base50; ambitious adds50; hidden in the observed frame",
            },
            "native_ai_boundary": "current personality values and final aggregate ranking were not observed",
            "after_effect": None,
            "follow_up_event": None,
            "scope_boundary": "observed player host with four scopes; activity/province identities remain opaque",
            "dynamic_gold_boundary": (
                "activity_medium_gold_value binds medium_gold_value: income*6, optional treasury quarter factor, "
                "min50/max300 times era factor, rounded up to a multiple of5; current numeric cost is unavailable"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [
                    {"domain": "player_gold", "source": "remove_short_term_gold",
                     "direction": "decrease", "value_source": "activity_medium_gold_value",
                     "authored_amount": None, "amount_boundary": "dynamic; native affordability is the enabled result"},
                    {"domain": "attendee_opinion", "source": "add_opinion",
                     "modifier": "pleased_opinion", "authored_opinion": 10,
                     "target": "root", "subjects": "other eligible alive, nonimprisoned AI attendees"},
                    {"domain": "attendee_opinion", "source": "add_opinion",
                     "modifier": "grateful_opinion", "authored_opinion": 20,
                     "target": "root", "subjects": "eligible drunkard attendees; conditional"},
                    {"domain": "player_character_modifier", "source": "add_character_modifier",
                     "modifier": "feast_bought_more_drink_modifier", "authored_years": 10,
                     "authored_monthly_prestige": 0.5},
                    {"domain": "player_stress_and_fulfillment", "source": "stress_and_fulfillment_impact",
                     "conditional_trait_inputs": {"greedy": 40, "drunkard": -30},
                     "actual_result": None},
                ],
                "common_after_effects": [],
                "observable_postcondition": {
                    "metric": "played_character_gold.raw",
                    "expected_relation": "strictly_decreasing",
                    "material_change_required_for_evidence": True,
                },
                "source_anchors": [
                    f"{_EVENT_PATH}:10979-11098", f"{_ACTIVITY_VALUES}:876-878",
                    f"{_DYNAMIC_VALUES}:93-111", f"{_MODIFIERS}:109-112",
                ],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": (
                    "independent gold debit verifies the expense only; guest opinions, modifier application, "
                    "attendance and conditional stress require their own observations"
                ),
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_started_feast_and_improve_guest_relations",
                "comparison_kind": "source_reviewed_ordinal",
                "selected_rank": 1, "rank_count": 2,
                "selected_utility": {
                    "material_direction": "expense_for_source_defined_guest_relations",
                    "resource_cost": "dynamic_medium_gold_native_affordability_enabled",
                    "outcome_variance": "eligible_guest_set_and_conditional_stress_unobserved",
                    "timeline_value": "continue_started_feast",
                    "reason": "current campaign objective favors guest relations and prestige modifier over the cash alternative",
                },
                "alternatives": [{
                    "native_option_index": 1, "rank": 2,
                    "resource_tradeoff": "dynamic minor gold increase and fixed prestige -75",
                    "boundary": "just/generous stress and runtime gold amount unobserved; preferable for a treasury-first objective",
                }],
                "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated",
                "decision_scope": "observed_two_rendered_choices_for_player_host",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "no live selection or M2 credit; hidden choices are outside this profile",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": (
                    "artifacts/g2-maintainer-2026-10-02/resume-12003/"
                    "m7-murchad/formal-v16-background-next-01/turn-004/result.json"
                ),
                "artifact_sha256": "15B567D0793671E16B025779E4D9C6567B54E56E74E4B8725BAFE0C0C1A48366",
                "event_instance_id": 16, "root_character_id": 31853,
                "date_raw": 53330832, "selection_attempted": False,
                "calculated_event_id": 4796231, "runtime_stats_ordinal": 7457,
                "snapshot_authored_option_count": 4, "rendered_native_option_indices": [0, 1],
                "drunk_guest_character_id": 16843458,
                "boundary": "typed query available but knowledge not registered; no choice or material result",
            }],
        },
    },
}
