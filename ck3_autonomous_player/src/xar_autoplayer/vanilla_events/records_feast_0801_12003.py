"""Current actual pleasing-atmosphere feast: mingle with compatible attendees."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/feast_events_ewan.txt"
_SOURCES: Final = {
    _EVENT_PATH: "6B040A05457D879EC733CD887A06CAFDC427F196E1B9E95B8C111778CF5C34E6",
    "common/opinion_modifiers/00_opinion_modifiers.txt":
    "E921CBFEC164E8B36CD3BFBDFCBC05B8152EC17CBF5B49E440D3A71D09AFDDB4",
    "common/script_values/00_basic_values.txt":
    "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
    "common/script_values/00_stress_values.txt":
    "821A0B77244FC5EE2D87D339CB24DBEF00787B83D44EC2DF9215FC1A93AEC2D4",
}

FEAST_0801_12003_RECORDS: Final = {
    "feast_events_ewan.0801": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "scope_types": {
                "activity": "activity", "host": "character", "province": "province",
                "fellow_guest_1": "character", "fellow_guest_2": "character",
            },
            "saved_scope_name_sets": ((
                "activity", "host", "province", "fellow_guest_1", "fellow_guest_2",
            ),),
            "saved_scope_count": 5,
            "character_scopes": {"host": PLAYER_SENTINEL},
            "option_count": 3,
            "snapshot_option_count": 3,
            "native_option_indices": (0, 1, 2),
            "selected_option_number": 2,
            "selected_native_option_index": 1,
            "occurrence_policy": "repeatable-within-product-observation-window",
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598,
            },
            "source_sha256": _SOURCES,
            "definition_lines": "1516-1866",
            "definition_block_sha256":
            "511C54E289BD36EB746377F99633FCF6982C6C8B42CA14ACEA7FEEB7607D5EE2",
            "definition_block_hash_convention": "frozen complete .0801 raw-token-block bytes in source-effects/feast_events_ewan-0801.raw-token-block.txt",
            "event_type": "activity_event",
            "trigger": "reduce_stress_intent; murder activity excludes the host",
            "cooldown": "one year",
            "immediate_effect": (
                "save two distinct random nonroot attending characters sharing at least "
                "one trait with root; scopes are portrait witnesses, not the full beneficiary set"
            ),
            "event_weight": {"base": 1, "modifiers": [
                {"add": 0.25, "has_trait": "gregarious"},
                {"add": 0.25, "has_trait": "lifestyle_reveler"},
            ]},
            "option_semantics": {
                "0": "stress_and_fulfillment_impact: massive_stress_impact_loss base, major_stress_impact_gain for reclusive",
                "1": "every nonroot attending character sharing at least one trait receives friendliness_opinion toward root with authored opinion20; minor stress impact loss and gregarious miniscule loss",
                "2": "minor_prestige_gain plus gregarious/arrogant miniscule stress impact loss and shy/humble medium stress impact gain",
            },
            "authored_option_name_aliases": [
                "feast_events_ewan.0801.a", "feast_events_ewan.0801.b", "feast_events_ewan.0801.c",
            ],
            "native_ai_weights": {
                "0": {"base": 100, "ai_value_modifier": {"ai_rationality": 0.5, "ai_boldness": -0.5}},
                "1": {"base": 1, "ai_value_modifier": {"ai_sociability": 0.5, "ai_boldness": -0.25}},
                "2": {"base": 1, "ai_value_modifier": {"ai_boldness": 0.5, "ai_energy": 0.5}},
            },
            "native_ai_boundary": "complete authored weights and personality inputs reviewed; final engine sampling and current personality numeric scores are not claimed",
            "direct_value_definitions": {
                "massive_stress_impact_loss": -100,
                "major_stress_impact_gain": 80,
                "minor_stress_impact_loss": -15,
                "miniscule_stress_impact_loss": -5,
                "medium_stress_impact_gain": 40,
                "minor_prestige_gain": 75,
            },
            "friendliness_modifier_definition": {
                "monthly_change": 0.1, "decaying": True, "stacking": True,
                "duration": "not explicitly authored in event or modifier; native default not inferred",
            },
            "selected_option_trigger": "activity has an attending character sharing at least one trait with root; current native shown/enabled is the final legality result",
            "localization_sources": {
                "localization/english/event_localization/activities/feast_events_ewan_l_english.yml":
                "BCC885B94BF4BDB4380B3F59B42DEB044FAF356888948E7F3128EC5DFC7A5C7A",
                "localization/simp_chinese/event_localization/activities/feast_events_ewan_l_simp_chinese.yml":
                "2FC54F5649EC82AE233E99CAAB96CAC6E0E0EE69B8AC02FEDE744CE4D03D96DF",
            },
            "after_effect": None,
            "follow_up_event": None,
            "scope_boundary": "only the actual five-scope three-enabled-option host projection; guest identities are dynamic and activity/province remain opaque",
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 1,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [{
                    "domain": "attendee_opinion_toward_player",
                    "source": "activity.every_attending_character.add_opinion",
                    "condition": "attendee differs from root and shares at least one trait",
                    "modifier": "friendliness_opinion", "authored_opinion": 20,
                    "cardinality": "once per qualifying attendee, not per trait or only the two portraits",
                    "actual_value_boundary": "total beneficiaries and final total-opinion delta require independent actual reads; existing modifier state can affect final change",
                }, {
                    "domain": "player_stress_and_fulfillment_impact",
                    "source": "stress_and_fulfillment_impact",
                    "authored_base": "minor_stress_impact_loss",
                    "trait_contribution": {"gregarious": "miniscule_stress_impact_loss"},
                    "actual_value_boundary": "native impact handling, modifiers and clamping determine actual stress/fulfillment; current stress0 cannot prove a decrease",
                }],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_EVENT_PATH}:1516-1866", f"{_EVENT_PATH}:1798-1844"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": "generic material comparator has no selected target-opinion profile; existing independent guest-opinion reads can verify total-opinion change without claiming a new generic observer or exact20 beforehand",
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 1,
                "objective_id": "improve_compatible_feast_attendee_relations_and_continue_robert_campaign",
                "comparison_kind": "source_reviewed_ordinal",
                "selected_rank": 1, "rank_count": 3,
                "selected_utility": {
                    "relationship_direction": "source_defined_attendee_friendliness_toward_player",
                    "resource_cost": "none_authored",
                    "stress_direction": "source_defined_loss_with_current_zero_clamp_boundary",
                    "timeline_value": "continue_actual_campaign",
                },
                "alternatives": [{
                    "native_option_index": 0, "authored_ai_base": 100,
                    "source_tradeoff": "larger stress loss with reclusive gain contribution; current stress0 makes extra relief of low immediate value",
                }, {
                    "native_option_index": 2, "authored_ai_base": 1,
                    "source_tradeoff": "prestige alternative with shy/humble stress gains; not selected solely to obtain an easy material sample",
                }],
                "cross_event_numeric_score": None, "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "source relationship benefit is not an observed +20 or M2 material credit; actual independent comparison remains pending",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": "artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/rite0010-following-normal30-6443-actual-01/turn-002/natural-event/002-ck3_query_current_event_window_context_v1-service-receipt.json",
                "artifact_sha256": "124CD1F98D8C3E156DE5BABB8F9D7E58065753CB3E4640B47C8A01DAA49AA82F",
                "event_instance_id": 14, "root_character_id": 29829,
                "date_raw": 53222304, "selection_attempted": False,
                "boundary": "current natural activity card with native31/public5, five scopes and three visible enabled options; registry miss, no selected benefit observed",
            }],
        },
    },
}
