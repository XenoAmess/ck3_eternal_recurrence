"""Exact .4 stock rite announcement; only the observed founder contract."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


EVENT_KEY: Final = "faith_creation.1021"
EVENT_PATH: Final = "events/religion_events/faith_creation_events.txt"
EVENT_SHA256: Final = "419C04B9CA889E96E572B894EC346AE6119AF2FD6EB9BE4833D6659EDFBA923E"
_SCOPES: Final = {
    "old_faith": "faith", "old_rite": "rite", "new_faith": "faith",
    "new_rite": "rite", "founder": "character", "source_rite": "rite",
    "differing_tenet": "tenet",
}
_SOURCES: Final = {
    EVENT_PATH: EVENT_SHA256,
    "common/on_action/religion_on_actions.txt":
        "EF9367DDF5F89C912B895743F8B72441E88AF3A5B03A5C1A9EDDEA0E5681EE2D",
    "common/script_values/00_basic_values.txt":
        "C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF",
    "common/script_values/pam_values.txt":
        "458D1BD882E8854005E3158339FCA343177CFF13EAC7F83CB5877A8A37171965",
    "localization/simp_chinese/event_localization/religion_events/faith_creation_events_l_simp_chinese.yml":
        "111E9942C97B241B01D4E1599C0394729DB88DB72FAA3CCACACAC0EF06E567FF",
    "gui/event_window_widgets/event_window_widget_rite_founder.gui":
        "C1BAA2D2D422222F88F6CABFABCEF19625D5C3902015F07D56A9EAADC85A7C97",
}

FAITH_CREATION1021_12004_RECORD: Final = {
    "contract": {
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {"founder": PLAYER_SENTINEL},
        "scope_types": _SCOPES,
        "saved_scope_name_sets": (tuple(_SCOPES),),
        "saved_scope_count": 7,
        "scope_variants": ({
            "saved_scope_names": (*_SCOPES, "converted_ruler_capital"),
            "saved_scope_count": 8,
            "scope_types": {**_SCOPES, "converted_ruler_capital": "landed_title"},
        },),
        "option_count": 2,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "analysis": {
        "exact_build": {"game_version": "1.20.0.4", "steam_build_id": 25734779,
                        "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.4"]},
        "source_sha256": _SOURCES,
        "definition_lines": "1273-1382",
        "definition_block_sha256": "DC10BF5F40558169CCFB0B8A38B4699C1B2F2F7338FD544B780945242FC01919",
        "definition_block_hash_convention": "key token through closing brace, original CRLF retained, following newline excluded",
        "event_type": "character_event",
        "caller_lines": f"{EVENT_PATH}:1244-1269; common/on_action/religion_on_actions.txt:718-721",
        "caller_semantics": "on_rite_created dispatches .1020; it saves created new_rite and source_rite, then schedules .1021 one day later for same-faith players",
        "trigger_lines": "1345-1350",
        "immediate_effect": "music only; no rite mutation or event scheduling",
        "option_semantics": {
            "0": "founder only: spiritual fulfillment authored base+5 and piety base+50",
            "1": "founder only: prestige base+150 and piety base-50",
            "2": "observer only: spiritual fulfillment authored base+5",
            "3": "observer only: piety base+50",
        },
        "option_lines": {"0": "1356-1361", "1": "1363-1368", "2": "1371-1375", "3": "1377-1381"},
        "authored_option_name_aliases": ["faith_creation.1021.a.founder", "faith_creation.1021.b.founder",
                                         "faith_creation.1021.a", "faith_creation.1021.b"],
        "selected_choice_effect_profile": {
            "schema": "xar.ck3.vanilla-event-choice-effect", "schema_version": 1,
            "selected_native_option_index": 0,
            "completeness": "all-authored-options-and-common-after-source-reviewed",
            "selected_option_effects": [
                {"domain": "player_spiritual_fulfillment", "source": "change_spiritual_fulfillment", "authored_base_value": 5},
                {"domain": "player_piety", "source": "add_piety", "authored_base_value": 50},
            ],
            "common_after_effects": [],
            "observable_postcondition": None,
            "material_evidence_boundary": "authored bases are not observed deltas; modifiers/clamping and independent actual values remain separate",
        },
        "after_effect": None,
        "follow_up_event": None,
        "presentation_boundary": "four authored options; founder shows native0/1 with observed seven scopes or eight including converted_ruler_capital; observer native2/3 and other saved-scope variants remain source-only",
        "inherited_optional_scope_source": {
            "name": "converted_ruler_capital", "type": "landed_title",
            "relative_path": "events/religion_events/faith_conversion_events.txt",
            "file_sha256": "690962331397AF4F0A0A4B9D92BF4B6F6C320F400E7C65C34716E8CBAD488EC0",
            "save_scope_lines": "15-17",
            "caller_order": "on_rite_created lists faith_conversion.0001 before faith_creation.1020; actual R22 context contains the inherited scope",
            "identity_boundary": "actual title identity is observation only, not a contract constant; opaque differing_tenet remains opaque",
        },
        "widget_boundary": "body uses saved new_rite.GetName; widget uses founder.GetRite, the founder current rite; do not equate their identities",
        "queue_boundary": "saved creation announcements can accumulate before their due date; instance ID is not queue length; modal drainage does not prove msg_rite_updated nonrecurrence",
        "update_message_boundary": "on_rite_updated sends msg_rite_updated via a separate interface-message chain",
        "native_ai_weights": "no authored ai_chance; no runtime/native-equivalent preference claim",
        "automatic_selection": False,
        "readiness": "source-reviewed-with-product-live-primitive",
        "deployment_boundary": "current framework knowledge only; frozen runtime007 unchanged and did not serve this addition",
    },
    "observations": {
        "exemplars": [{
            "kind": "product-live-primitive",
            "machine_id": "bf-202609141645-5434332d4d",
            "observed_at_utc": "2026-10-15T10:10:39.954493+00:00",
            "source_repository": "ck3_mod_more_tenant_slots",
            "artifact": "artifacts/bugfix-20261015/queued-event-diagnosis/r20-001/report.json",
            "artifact_sha256": "4C0657FEFCC57554616E95C4E52BC41D1BC40C0055E9FFDF6B3770E07A79C152",
            "rendered_native_option_indices": [0, 1], "authored_option_count": 4,
            "selected_native_option_index": 0, "postcondition_verified": True,
            "occurrence_count": 3, "terminal_active_event": None,
            "boundary": "three founder occurrences independently advanced; no observer, material reward, later-time nonrecurrence or product business credit",
        }, {
            "kind": "product-live-primitive",
            "machine_id": "bf-202609141645-5434332d4d",
            "source_repository": "ck3_mod_more_tenant_slots",
            "artifact": "docs/evidence/native-main-r22.json",
            "event_context_original": "R0022/root-evidence/r22-event2-paused-context.results.json",
            "event_context_sha256": "FB5A13EBF77945A2C049D21059DEE871F14DB66B1B1E83E5AEA2C0EB8C46E5B1",
            "selection_original": "R0022/root-evidence/r22-event2-select-resume.results.json",
            "selection_sha256": "5C2EE9F25D4D8D791B84415A04847B3ECA7DB04CB252BB6BFE60A776C56C50E5",
            "saved_scope_variant": "converted_ruler_capital", "saved_scope_count": 8,
            "selected_native_option_index": 0, "postcondition_verified": True,
            "boundary": "extra capital scope observed; no generic automation, opaque tenet identity or host-GREEN credit",
        }],
    },
}

FAITH_CREATION1021_12004_SOURCE: Final = {
    "namespace": "faith_creation",
    "definition": {"relative_path": EVENT_PATH, "line": 1273, "file_sha256": EVENT_SHA256},
    "caller_candidate_resolution": "same-definition-file-only",
    "caller_candidates": [{"relative_path": EVENT_PATH, "line": 1265, "column": 10,
                           "file_sha256": EVENT_SHA256, "kind": "exact-token-lexical-candidate"}],
}
