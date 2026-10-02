"""The actual .3 ordinary feast opening's tooltip-only timeline continuation."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/feast_events.txt"
_ACTIVITY_PATH: Final = "common/activities/activity_types/feast.txt"
_SOURCES: Final = {
    _EVENT_PATH: "F5820211444E7DBAF0A318ADF65BEBF4CA581D3A4E9F381ADD63D3BF02AAF77E",
    _ACTIVITY_PATH: "FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598",
}

FEAST_START_12003_RECORDS: Final = {
    "feast.2001": {
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
            "definition_lines": "601-927",
            "definition_block_sha256":
            "9E52F6C1F72317CC91B79271CAA6079D4354D073FA906F7BED39DD5A219AEE47",
            "definition_block_hash_convention": "exact source bytes with original newlines",
            "event_type": "activity_event",
            "caller_semantics": (
                "meal on_phase_active triggers feast.2001 when a non-host attendee exists; "
                "the event trigger requires root to equal the activity host"
            ),
            "caller_lines": f"{_ACTIVITY_PATH}:4425-4442",
            "immediate_effect_lines": "722-807",
            "immediate_effect": (
                "music, conditional portrait/scope capture and list initialization happen "
                "before selection; they are not selected-choice gains"
            ),
            "option_lines": "809-816",
            "option_semantics": {"0": "ordinary exclusive opening; custom tooltip only"},
            "authored_option_name_aliases": ["feast.2001.a"],
            "native_ai_weights": {"0": "ordinary exclusive option has no ai_chance block"},
            "after_effect": None,
            "follow_up_event": None,
            "scope_boundary": (
                "only the actual ordinary three-scope root=host variant with sole native 0; "
                "other authored native 1-4 variants are not admitted; backdown native 4 "
                "has no independent murder guard, but ordinary native 0 is exclusive; "
                "activity/province typed identities remain opaque"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_EVENT_PATH}:601-927", f"{_EVENT_PATH}:809-816"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": (
                    "ordinary native 0 advances the modal; no selected-choice material "
                    "gain is authored, and pre-selection immediate effects earn no credit"
                ),
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_ordinary_feast_opening",
                "comparison_kind": "sole_legal_route",
                "selected_rank": 1, "rank_count": 1,
                "selected_utility": {
                    "material_direction": "neutral", "resource_cost": "none_authored",
                    "outcome_variance": "no_authored_selected_choice_game_effect",
                    "timeline_value": "required_to_continue",
                },
                "alternatives": [], "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "timeline continuation only; no M2 selected-choice material credit",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": (
                    "artifacts/g2-maintainer-2026-10-02/resume-12003/"
                    "m7-murchad/formal-v14-next-02/turn-006/result.json"
                ),
                "artifact_sha256": "70CDE800708C356F3560F1B7A482650A1A91BCA38EB4FE2F18DAC768DF5A5888",
                "checkpoint_sha256": "F5849B3A9A17D0D1E9006A06B96479535665DBAB963075121B6A5EFF62E5EBF0",
                "event_instance_id": 15, "root_character_id": 31853,
                "date_raw": 53330784, "selection_attempted": False,
                "boundary": "actual ordinary source-bound modal; original not_registered RED; no selection/material result",
            }],
        },
    },
}
