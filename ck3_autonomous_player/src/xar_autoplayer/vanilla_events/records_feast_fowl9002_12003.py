"""The actual .3 host live-fowl farewell and its sole source-defined option."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/main_events/feast_main_live_fowl_events.txt"
_STRESS_PATH: Final = "common/script_values/00_stress_values.txt"
_SOURCES: Final = {
    _EVENT_PATH: "159C17409D07B6F6D8307D58522FBF066F90E895B25DC64BD97AEE77D7202C56",
    _STRESS_PATH: "821A0B77244FC5EE2D87D339CB24DBEF00787B83D44EC2DF9215FC1A93AEC2D4",
}

FEAST_FOWL9002_12003_RECORDS: Final = {
    "feast_main_live_fowl.9002": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "character_scopes": {
                "host": PLAYER_SENTINEL, "host_saying_goodbye": PLAYER_SENTINEL,
            },
            "scope_types": {
                "activity": "activity", "host": "character", "province": "province",
                "fowl_dinner_target": "character", "fowl_bird_chaser": "character",
                "host_saying_goodbye": "character",
            },
            "saved_scope_name_sets": ((
                "activity", "host", "province", "fowl_dinner_target", "fowl_bird_chaser",
                "host_saying_goodbye",
            ),),
            "saved_scope_count": 6,
            "option_count": 1, "snapshot_option_count": 1,
            "native_option_indices": (0,),
            "selected_option_number": 1, "selected_native_option_index": 0,
            "occurrence_policy": "repeatable-within-product-observation-window",
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598,
            },
            "source_sha256": _SOURCES,
            "definition_lines": "652-683",
            "definition_block_sha256":
            "01129EB3EAA7A318B5625FD4E2FFB0A91D37F8A439058174EFA305268F7CAD1D",
            "definition_block_hash_convention": "SourceTree key token through closing brace; original CRLF retained; following newline excluded",
            "event_type": "activity_event",
            "caller_semantics": "direct .9000 activity-host dispatch after saving host_saying_goodbye; only those caller excerpts are reviewed",
            "caller_lines": f"{_EVENT_PATH}:527-541,605-608",
            "trigger_semantics": "no event or option trigger in the reviewed .9002 block",
            "immediate_effect": None,
            "option_lines": "676-681",
            "option_semantics": {"0": "sole stress_and_fulfillment_impact call with base minor_stress_loss=-10"},
            "authored_option_name_aliases": ["feast_main_live_fowl.9002.a"],
            "native_ai_weights": {"0": "sole authored option; no ai_chance block"},
            "localization_sources": {
                "localization/english/event_localization/activities/feast_main_live_fowl_l_english.yml":
                "0D79FC7B21EEB15D7F6293C89F1B5C2B61C4EC899A30E7B4331264550929B784",
                "localization/simp_chinese/event_localization/activities/feast_main_live_fowl_l_simp_chinese.yml":
                "EAA2026FB80142322746A45363AEA7A0D886D24827168A1BB8908B893084C8AA",
            },
            "after_effect": None,
            "scope_boundary": "only the actual root=host=host_saying_goodbye six-scope route; target/chaser IDs are dynamic and activity/province identities remain opaque",
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect", "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [{
                    "domain": "player_character_stress_and_fulfillment",
                    "source": "stress_and_fulfillment_impact",
                    "base_script_value": "minor_stress_loss", "authored_base": -10,
                    "engine_effect_boundary": "native effect; routing, modifiers, scale and clamp are not closed by the authored call",
                }],
                "common_after_effects": [], "observable_postcondition": None,
                "source_anchors": [f"{_EVENT_PATH}:676-681", f"{_STRESS_PATH}:13"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": "nonempty source effect; current played stress is zero and the icon magnitude is unavailable; no guaranteed -10 delta, fulfillment observation or material result follows from source or modal advance",
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility", "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_started_feast_live_fowl_host_farewell",
                "comparison_kind": "sole_legal_route", "selected_rank": 1, "rank_count": 1,
                "selected_utility": {
                    "material_direction": "source_defined_stress_and_fulfillment_impact",
                    "resource_cost": "none_authored",
                    "outcome_variance": "engine_routing_and_clamp_not_closed",
                    "timeline_value": "required_to_continue_started_feast",
                },
                "alternatives": [], "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated", "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES, "readiness": "static-ready", "new_live_evidence": False,
            },
            "source_review_receipt_sha256": "EED31AA2C40C6BE803B9AE13F3D8C90C9BC8AC807F7854AD80BA83BC70D18ABF",
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "no live, material, M2 or terminal Feast credit from source effect, sole-option ACK or modal advance",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": "artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/ewan0801-following-normal30-b594-v22-actual-01/turn-002/natural-event/003-ck3_query_vanilla_event_knowledge_v1-service-receipt.json",
                "artifact_sha256": "E6DE8DBD234F8649297CA55005C1DFEDA09D35B275E4E01E4EBE0849A573C638",
                "typed_context_sha256": "5537F69FEBF56AEA11E0AD6074EA8B0939966EF32F4850295703AFBCD803335D",
                "snapshot_sha256": "676BF2EA1AF6132AE59259F7A10FA8E70EB0FA8EB1D6F5AADC66BBB0C160C296",
                "event_instance_id": 15, "root_character_id": 29829,
                "fowl_dinner_target_character_id": 37636, "fowl_bird_chaser_character_id": 36907,
                "host_saying_goodbye_character_id": 29829, "date_raw": 53222376,
                "selection_attempted": False,
                "boundary": "real natural modal with available native typed presentation and not_registered knowledge; no selected or independent material result",
            }],
        },
    },
}
