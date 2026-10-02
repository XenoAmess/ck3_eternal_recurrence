"""Current source-bound feast.7002 host arrival and its sole prestige choice."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/feast_events.txt"
_VALUES_PATH: Final = "common/script_values/00_basic_values.txt"
_SOURCES: Final = {
    _EVENT_PATH: "F5820211444E7DBAF0A318ADF65BEBF4CA581D3A4E9F381ADD63D3BF02AAF77E",
    _VALUES_PATH: "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
    "common/activities/activity_types/feast.txt":
    "FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598",
}

FEAST_ARRIVAL_12003_RECORDS: Final = {
    "feast.7002": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "character_scopes": {"host": PLAYER_SENTINEL},
            "scope_types": {"activity": "activity", "host": "character", "province": "province"},
            "saved_scope_name_sets": (("activity", "host", "province"),),
            "saved_scope_count": 3,
            "option_count": 1,
            "snapshot_option_count": 1,
            "native_option_indices": (0,),
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
            "definition_lines": "1139-1278",
            "definition_block_sha256":
            "61700971D916E2D17EB8DD7632362D76850A83C3974B8D1B0BDE8CE6CD3BF8C8",
            "event_type": "activity_event",
            "caller_semantics": "Feast on_enter_passive_state directly triggers feast.7002",
            "caller_lines": "common/activities/activity_types/feast.txt:4980-4982",
            "immediate_effect_lines": "1212-1255",
            "immediate_effect": (
                "plays banquet music and saves center_portrait only if a qualifying "
                "honorary guest or adult attending character exists"
            ),
            "option_lines": "1257-1277",
            "option_semantics": {"0": "sole arrival choice; add_prestige = miniscule_prestige_gain"},
            "authored_option_name_aliases": ["feast.7002.a.bad", "feast.7002.a.good"],
            "localization_sources": {
                "localization/english/event_localization/activities/feast_events_l_english.yml":
                "167F119A424BF17525205359BCCE2ED20BDCB3CAB3C1965717D27F331344F5A1",
                "localization/simp_chinese/event_localization/activities/feast_events_l_simp_chinese.yml":
                "A33E34631EAB35D5B05BE34DE123D39E173C76866616267467C5049682B3AE7C",
            },
            "native_ai_weights": {"0": "sole authored option; no ai_chance block"},
            "after_effect": None,
            "follow_up_event": None,
            "scope_boundary": (
                "observed host route without conditional center_portrait; host and "
                "root are the player, while activity/province payloads remain opaque"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [{
                    "domain": "player_prestige", "source": "add_prestige",
                    "direction": "increase", "value_source": "miniscule_prestige_gain",
                    "authored_base_value": 35,
                }],
                "common_after_effects": [],
                "observable_postcondition": {
                    "metric": "played_character_prestige.raw",
                    "expected_relation": "strictly_increasing",
                    "material_change_required_for_evidence": True,
                },
                "source_anchors": [f"{_EVENT_PATH}:1257-1278", f"{_VALUES_PATH}:1000", f"{_VALUES_PATH}:1033"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": "stock base 35 is source expectation; report the actual independent raw delta",
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_feast_arrival_with_sole_prestige_gain",
                "comparison_kind": "sole_legal_route",
                "selected_rank": 1, "rank_count": 1,
                "selected_utility": {
                    "material_direction": "benefit", "resource_cost": "none_authored",
                    "outcome_variance": "source_defined_prestige_gain",
                    "timeline_value": "required_to_continue",
                },
                "alternatives": [], "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready",
            "new_live_evidence": False,
            "material_evidence_boundary": "a sole option is not a multi-option M2 event; new live evidence remains pending",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": (
                    "artifacts/g2-maintainer-2026-10-02/resume-12003/"
                    "m7-murchad/formal-v11-next-01/turn-001/natural-event/result.json"
                ),
                "artifact_sha256": "6BFCA789834A112813C18B157E2701CAED3823ABB68E04F1327B0D426CE16B5F",
                "checkpoint_sha256": "F85E9447704C20E133C65DD9A21E074F31A6F281010DBDC9CC9FAA1A98F49B1F",
                "event_instance_id": 14, "root_character_id": 31853,
                "date_raw": 53328600, "selection_attempted": False,
                "saved_activity_id": 587202561, "saved_province_id": 45,
                "boundary": "offline saved identities; original event context unavailable; no live choice/material result",
            }],
        },
    },
}
