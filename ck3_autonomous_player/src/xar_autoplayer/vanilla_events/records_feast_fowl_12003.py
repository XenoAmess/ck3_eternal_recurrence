"""The actual .3 host live-fowl event and its sole modifier continuation."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_EVENT_PATH: Final = "events/activities/feast_activity/main_events/feast_main_live_fowl_events.txt"
_MODIFIER_PATH: Final = "common/modifiers/00_activity_feast_modifiers.txt"
_SOURCES: Final = {
    _EVENT_PATH: "159C17409D07B6F6D8307D58522FBF066F90E895B25DC64BD97AEE77D7202C56",
    _MODIFIER_PATH: "4B6A39429FAF60B50D2D20A32687E4E1148CA7660235C0C2A01F3A51EC0CABEE",
    "common/scripted_triggers/00_feast_activity_triggers.txt":
    "B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA",
    "common/script_values/00_basic_values.txt":
    "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
}

FEAST_FOWL_12003_RECORDS: Final = {
    "feast_main_live_fowl.0003": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "character_scopes": {"host": PLAYER_SENTINEL},
            "scope_types": {
                "activity": "activity", "host": "character", "province": "province",
                "fowl_dinner_target": "character", "fowl_bird_chaser": "character",
            },
            "saved_scope_name_sets": ((
                "activity", "host", "province", "fowl_dinner_target", "fowl_bird_chaser",
            ),),
            "saved_scope_count": 5,
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
            "definition_lines": "233-319",
            "definition_block_sha256":
            "E54265F7CE985EDD3FE79CCAFFD4C888979E0FB00F9E9D6DB1E411D9B42F62DA",
            "definition_block_hash_convention": "SourceTree key token through closing brace; original CRLF retained; following newline excluded",
            "event_type": "activity_event",
            "caller_semantics": (
                "feast_main_live_fowl.0001 selects the dinner target and bird chaser; "
                "its activity-host dispatch triggers .0003 unless the host is the existing bird killer"
            ),
            "caller_lines": f"{_EVENT_PATH}:75-82,100-133",
            "trigger_semantics": "root lacks feast_raucous_entertainment_modifier",
            "immediate_effect_lines": "275-277",
            "immediate_effect": "music only, executed before the option is selected",
            "option_lines": "285-299",
            "option_semantics": {"0": "sole route adds root feast_raucous_entertainment_modifier for five years"},
            "authored_option_name_aliases": ["feast_main_live_fowl.0003.a"],
            "native_ai_weights": {"0": "sole authored option; no ai_chance block"},
            "localization_sources": {
                "localization/english/event_localization/activities/feast_main_live_fowl_l_english.yml":
                "0D79FC7B21EEB15D7F6293C89F1B5C2B61C4EC899A30E7B4331264550929B784",
                "localization/simp_chinese/event_localization/activities/feast_main_live_fowl_l_simp_chinese.yml":
                "EAA2026FB80142322746A45363AEA7A0D886D24827168A1BB8908B893084C8AA",
            },
            "after_effect": "queues feast_main_live_fowl.9000 in ten days and adds a good activity log with score25, character=root, target=fowl_dinner_target",
            "follow_up_event": "feast_main_live_fowl.9000",
            "scope_boundary": (
                "only the actual root=host five-scope route; target/chaser IDs are dynamic, "
                "activity/province typed identities remain opaque, and sibling/killer variants are not admitted"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [{
                    "domain": "player_character_modifier", "source": "add_character_modifier",
                    "modifier_key": "feast_raucous_entertainment_modifier", "duration_years": 5,
                    "authored_modifier_values": {"health": 0.5, "stress_gain_mult": -0.2},
                }],
                "common_after_effects": [{
                    "domain": "scheduled_event", "source": "trigger_event",
                    "event_key": "feast_main_live_fowl.9000", "delay_days": 10,
                }, {
                    "domain": "activity_log", "source": "add_activity_log_entry",
                    "log_key": "feast_live_fowl_log", "tags": ["good"], "score": 25,
                    "character_scope": "root", "target_scope": "fowl_dinner_target",
                }],
                "observable_postcondition": None,
                "source_anchors": [f"{_EVENT_PATH}:285-318", f"{_MODIFIER_PATH}:125-129"],
                "source_sha256": _SOURCES,
                "material_evidence_boundary": (
                    "nonempty modifier and after effects; show_as_tooltip killer dread is not executed; "
                    "existing gold/prestige/stress-point comparators cannot verify modifier application; "
                    "independent existing campaign-root health pre/post can observe actual material separately"
                ),
            },
            "selected_choice_campaign_utility_profile": {
                "schema": "xar.ck3.vanilla-event-campaign-utility",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "objective_id": "continue_started_feast_live_fowl_host_event",
                "comparison_kind": "sole_legal_route",
                "selected_rank": 1, "rank_count": 1,
                "selected_utility": {
                    "material_direction": "source_defined_beneficial_root_modifier",
                    "resource_cost": "none_authored",
                    "outcome_variance": "source_defined_modifier_and_delayed_chain",
                    "timeline_value": "required_to_continue_started_feast",
                },
                "alternatives": [], "cross_event_numeric_score": None,
                "calibration_status": "not_calibrated",
                "decision_scope": "bounded_timeline_continuation",
                "source_sha256": _SOURCES,
                "readiness": "static-ready", "new_live_evidence": False,
            },
            "readiness": "static-ready", "new_live_evidence": False,
            "material_evidence_boundary": "no material or M2 credit from ACK, modal advance or authored modifier values; actual independent evidence is required",
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": (
                    "artifacts/g2-maintainer-2026-10-02/resume-12003/"
                    "m7-robert/feast2001-following-normal30-242-actual-01/turn-001/natural-event/result.json"
                ),
                "artifact_sha256": "0E85C592E8E0209FFC7E7DE6F2A631E4A58F0E1908DC3C9BD87B3FBFFECDC339",
                "checkpoint_sha256": "64B99D070E6AF7E3A640496734C1C85CD292C35ECAD16455C1407A8422B15E9D",
                "event_instance_id": 12, "root_character_id": 29829,
                "fowl_dinner_target_character_id": 37636,
                "fowl_bird_chaser_character_id": 36907,
                "date_raw": 53222136, "selection_attempted": False,
                "boundary": "real natural modal with available native typed presentation; original registry miss; no selected or independent material result",
            }],
        },
    },
}
