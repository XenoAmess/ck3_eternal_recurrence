"""The observed .3 education notification's tooltip-only acknowledgement."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_PATH: Final = "events/education_and_childhood/coming_of_age_events.txt"
_SHA: Final = "FB2C0E3D52B9F625EBD128195C3BF622D656C49EF1ABA91FB13C93569998A4BA"
_HELPER_PATH: Final = "common/scripted_effects/00_education_effects.txt"
_HELPER_SHA: Final = "B3FD20ED647FBB4F3BD9AF337C605788C96B152E0823F2C7A17817AA23A7CA67"

COMING_AGE1002_12003_RECORDS: Final = {
    "coming_of_age.1002": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "scope_types": {"educated_child": "character"},
            "saved_scope_name_sets": (("educated_child",),),
            "saved_scope_count": 1,
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
            "source_sha256": {_PATH: _SHA, _HELPER_PATH: _HELPER_SHA},
            "definition_lines": "2368-2412",
            "definition_block_sha256": "ABB8FF82070F20995AE2EC4FB93913B9A3A4CBEC8D7BD4B56513F38897ACD7F7",
            "event_type": "character_event",
            "authored_option_count": 1,
            "immediate_effect": None,
            "after_effect": None,
            "option_lines": "2399-2411",
            "option_semantics": {
                "0": {
                    "name": "coming_of_age.1001.a",
                    "native_option_index": 0,
                    "api_option_number": 1,
                    "effects_empty": True,
                    "executed_option_effects": [],
                    "tooltip_only": "education trait display, ending ward relation and conditional return_to_court",
                },
            },
            "native_ai_weights": {"0": None},
            "native_ai_weight_boundary": "No authored ai_chance. No numerical engine default is inferred.",
            "direct_dependency": {
                "key": "display_correct_education_trait_gain_tooltip_effect",
                "definition_lines": "1344-1661",
                "block_sha256": "96E417EFE1D06143645057896D8D67835A908947A3ECD4015C755A273F688E9D",
                "semantics": "has_trait checks select show_as_tooltip add_trait_force_tooltip display; no selected-choice trait production",
            },
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_PATH}:2368-2412", f"{_HELPER_PATH}:1344-1661"],
                "source_sha256": {_PATH: _SHA, _HELPER_PATH: _HELPER_SHA},
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_current_coming_of_age_notification",
                "comparison_kind": "sole_legal_route",
                "selected_rank": 1,
                "rank_count": 1,
                "selected_utility": {
                    "material_direction": "tooltip_only_acknowledgement",
                    "resource_cost": "none_authored_in_selected_option_or_common_after",
                    "outcome_variance": "no_executed_option_or_common_after_effect",
                    "timeline_value": "continue_current_notification",
                },
                "alternatives": [],
                "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "readiness": "static-ready",
                "new_live_evidence": False,
            },
            "readiness": "static-ready",
            "new_live_evidence": False,
            "material_evidence_boundary": "Dismissal advances the notification only; education, ward or travel results are tooltip descriptions and do not give selected-choice M2 material credit.",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": "artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/v28-marriage21-following-normal7-01/turn-004/natural-event/result.json",
                "event_instance_id": 22,
                "root_character_id": 29829,
                "educated_child_character_id": 38822,
                "date_raw": 53234568,
                "native_revision": 152,
                "selection_attempted": False,
                "boundary": "Actual typed root/educated_child and sole native0 projection; notification has not yet been consumed by this delivery.",
            }],
        },
    },
}
