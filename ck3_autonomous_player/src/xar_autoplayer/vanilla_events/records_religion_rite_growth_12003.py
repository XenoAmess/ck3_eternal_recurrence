"""Current actual Rite-growth notice: keep the player's Rite and gain fulfillment."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/religion_events/rite_growth_events.txt"
_SOURCES: Final = {
    _EVENT_PATH: "D09C0EB94E1A81C0D456F55C049004D7EF1EBE38464A1274CF151D0214418895",
    "common/script_values/00_basic_values.txt":
    "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
    "common/scripted_effects/00_religion_effects.txt":
    "5BF6B0DF3316F72F711507C310A349D508A3B83AEF99373EA6440DE20E4E4931",
    "common/scripted_triggers/00_religious_triggers.txt":
    "E9D0B56130464EABDCD670FA6CF814534D11C99DA1E8B3FC1E69E9C3E36D2BB2",
    "common/script_values/02_religion_values.txt":
    "9E55618B00B463589AF310BD17511B4F260FEA4D3ACB43E512E209CFC1517DED",
    "common/opinion_modifiers/00_opinion_modifiers.txt":
    "E921CBFEC164E8B36CD3BFBDFCBC05B8152EC17CBF5B49E440D3A71D09AFDDB4",
    "common/on_action/religion_on_actions.txt":
    "EF9367DDF5F89C912B895743F8B72441E88AF3A5B03A5C1A9EDDEA0E5681EE2D",
}

RELIGION_RITE_GROWTH_12003_RECORDS: Final = {
    "rite_growth.0010": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "scope_types": {
                "origin_faith": "faith", "source_rite": "rite", "founder": "character",
                "bg_override_char": "character", "rite_growth_target_share": "value",
                "new_rite": "rite", "differing_doctrine": "doctrine",
            },
            "saved_scope_name_sets": ((
                "origin_faith", "source_rite", "founder", "bg_override_char",
                "rite_growth_target_share", "new_rite", "differing_doctrine",
            ),),
            "saved_scope_count": 7,
            "option_count": 3,
            "snapshot_option_count": 3,
            "native_option_indices": (0, 1, 2),
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
            "definition_lines": "73-413",
            "definition_block_sha256":
            "ECDB6AD5179B47CFFC2114A3030A1CCE5F9231ECEC29CED3DC4B64A961AB4E42",
            "definition_block_hash_convention": "SourceTree key token through closing brace; following newline excluded; raw and LF identical",
            "event_type": "character_event",
            "major_event": True,
            "caller_semantics": "faith-scoped rite_growth.0001 resolves source Rite and founder, then triggers the founding major event",
            "caller_lines": f"{_EVENT_PATH}:14-68",
            "immediate_effect_lines": "138-324",
            "immediate_effect": (
                "founding recipient creates and converts to the new Rite, applies source-defined "
                "county/court changes and schedules spread; this is before player option selection"
            ),
            "major_recipient_boundary": "actual player29829 differs from founder36108; founding immediate is not a selected player gain or proof that the player converted",
            "option_semantics": {
                "0": "change_spiritual_fulfillment=5; keeps current Rite; no resource payment or founder-opinion change authored",
                "1": "set_character_rite_with_conversion=new_rite, founder opinion toward root+30, ten-year conversion flag and county/court cascade",
                "2": "medium piety base100 and founder opinion toward root-15; keeps current Rite",
            },
            "option_lines": {"0": "326-332", "1": "334-399", "2": "401-412"},
            "authored_option_name_aliases": ["rite_growth.0010.a", "rite_growth.0010.b", "rite_growth.0010.c"],
            "native_ai_weights": {"0": {"base": 100}, "1": {"base": 0}, "2": {"base": 0}},
            "native_ai_boundary": "authored weights reviewed; no personality factors; runtime engine weighting and major-recipient sampling not claimed",
            "localization_sources": {
                "localization/english/event_localization/religion_events/rite_growth_events_l_english.yml":
                "40999E6130BC6520C6F4E1D1761C0F79151DCB2BA5CE3629013B1CBF07DA29EC",
                "localization/simp_chinese/event_localization/religion_events/rite_growth_events_l_simp_chinese.yml":
                "F2D34186C7CFD00EDC9EADFF98AE1296C165DA01AFC50C89782A8B4B3CCBF5CF",
            },
            "after_effect": None,
            "follow_up_event": None,
            "pre_selection_scheduled_event": "rite_growth.0011 is scheduled by founding immediate, not the selected player option",
            "scope_boundary": "only actual seven-scope three-enabled-option shape; dynamic founder IDs are not fixed and non-character generic scope identities remain opaque",
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [{
                    "domain": "player_spiritual_fulfillment", "source": "change_spiritual_fulfillment",
                    "direction": "increase", "authored_base_value": 5,
                    "actual_value_boundary": "native modifiers and clamping may affect the result; use independent actual pre/post values",
                }],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_EVENT_PATH}:73-413", f"{_EVENT_PATH}:326-332"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": "existing generic comparator lacks fulfillment; existing player-religion query can independently observe its signed raw value, including valid zero; ACK/source base/old-instance advance are not material",
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_robert_campaign_with_current_rite_and_fulfillment",
                "comparison_kind": "source_reviewed_ordinal",
                "selected_rank": 1, "rank_count": 3,
                "selected_utility": {
                    "material_direction": "source_defined_fulfillment_benefit",
                    "resource_cost": "none_authored",
                    "religious_identity": "current_rite_preserved",
                    "founder_opinion_cost": "none_authored",
                    "timeline_value": "continue_actual_campaign",
                },
                "alternatives": [{
                    "native_option_index": 1, "authored_ai_base": 0,
                    "source_tradeoff": "Rite conversion with county/court cascade and founder opinion+30; complete current doctrine/conversion quality not evaluated",
                }, {
                    "native_option_index": 2, "authored_ai_base": 0,
                    "source_tradeoff": "piety base100 with founder contempt-15; avoid hostility under the current Robert objective",
                }],
                "cross_event_numeric_score": None, "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "actual independent fulfillment evidence remains pending; three source options alone do not grant a multi-option M2 sample",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": "artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/fowl3-chancellor-following-normal30-b03-actual-01/turn-003/result.json",
                "artifact_sha256": "BDF5FAF7BD3758B95E99DC40B4A527F750282C825401BEB397F17D86783D54FE",
                "event_instance_id": 13, "root_character_id": 29829,
                "founder_character_id": 36108, "date_raw": 53222280,
                "selection_attempted": False,
                "boundary": "actual natural major notice with available three-option presentation; original registry miss; no selected or independent fulfillment result",
            }],
        },
    },
}
