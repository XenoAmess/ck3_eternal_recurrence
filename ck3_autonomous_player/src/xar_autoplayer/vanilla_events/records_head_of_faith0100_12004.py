"""Exact .4 stock head-of-faith notice; the observed distinct-HoF shape."""
from typing import Final
from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL

EVENT_KEY: Final = "head_of_faith.0100"
EVENT_PATH: Final = "events/religion_events/head_of_faith_events.txt"
EVENT_SHA256: Final = "3B3817EB662206FB58FB67CEF76DEE5F70CC577F857BDFEB8705D9F1C92E5CBF"
HEAD_OF_FAITH0100_12004_RECORD: Final = {
    "contract": {
        "date_policy": "product-observation-window", "root_character_id": PLAYER_SENTINEL,
        "scope_types": {"old_faith": "faith", "old_rite": "rite", "hof": "character"},
        "saved_scope_name_sets": (("old_faith", "old_rite", "hof"),), "saved_scope_count": 3,
        "unique_character_scope_excludes": {"hof": (PLAYER_SENTINEL,)},
        "option_count": 2, "snapshot_option_count": 2, "native_option_indices": (0, 1),
        "selected_option_number": 1, "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "analysis": {
        "exact_build": {"game_version": "1.20.0.4", "steam_build_id": 25734779,
                        "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.4"]},
        "source_sha256": {
            EVENT_PATH: EVENT_SHA256,
            "common/on_action/religion_on_actions.txt": "EF9367DDF5F89C912B895743F8B72441E88AF3A5B03A5C1A9EDDEA0E5681EE2D",
            "common/opinion_modifiers/00_opinion_modifiers.txt": "E921CBFEC164E8B36CD3BFBDFCBC05B8152EC17CBF5B49E440D3A71D09AFDDB4",
            "localization/simp_chinese/event_localization/religion_events/head_of_faith_events_l_simp_chinese.yml": "E42CD7D53DF2F21B88CF1381A49123FC37F3B491C2C787FEC7B5FA452763E92F",
        },
        "definition_lines": "896-956",
        "definition_block_sha256": "65A94E735754C85B47C2C419E68B5E02C4BD975F6CE367D59A8B03B44FD08AE6",
        "definition_block_hash_convention": "key token through closing brace; original CRLF retained; following newline excluded",
        "caller_lines": "common/on_action/religion_on_actions.txt:590-594",
        "caller_semantics": "on_rite_created immediately raises .0100 if faith.religious_head exists; separate from next-day faith_creation.1021",
        "trigger_lines": "909-911", "event_type": "character_event",
        "immediate_effect": "music and save current faith.religious_head as hof; no religious identity mutation",
        "option_semantics": {
            "0": "reverse_add_opinion: hof toward root gets repentant_opinion with authored opinion25; component decays monthly0.1, no fixed duration authored",
            "1": "root gains wishes_to_schism_caliphate_flag and a tooltip; later schism eligibility may use it; no immediate schism",
        },
        "option_lines": {"0": "918-935", "1": "937-955"},
        "authored_option_name_aliases": ["head_of_faith.0100.a", "head_of_faith.0100.b"],
        "selected_choice_effect_profile": {
            "schema": "xar.ck3.vanilla-event-choice-effect", "schema_version": 1,
            "selected_native_option_index": 0,
            "completeness": "all-authored-options-and-common-after-source-reviewed",
            "selected_option_effects": [{"domain": "character_opinion", "source": "reverse_add_opinion",
                                         "observer_scope": "hof", "target_scope": "root",
                                         "modifier": "repentant_opinion", "authored_opinion": 25,
                                         "monthly_change": 0.1, "decaying": True}],
            "common_after_effects": [], "observable_postcondition": None,
            "material_evidence_boundary": "component is source-defined; no independent total-opinion pre/post observation",
        },
        "native_ai_weights": {"0": {"base": 100, "hof_opinion_multiplier": 5},
                              "1": {"base": 100, "ai_vengefulness": 1, "ai_zeal": 1, "hof_opinion_multiplier": -2}},
        "native_ai_boundary": "authored factors only; no sampled runtime weight or native-equivalent optimum",
        "after_effect": None, "follow_up_event": None,
        "religion_boundary": "neither option writes tenets, doctrines, Rite or Faith; no direct resource/stress effect or explicit reschedule",
        "scope_boundary": "observed old_faith/old_rite opaque; typed hof differs from player; other scope or self-HoF shapes not admitted",
        "automatic_selection": False, "readiness": "source-reviewed-with-product-live-primitive",
        "deployment_boundary": "framework knowledge only; frozen runtime007 unchanged and did not serve this addition",
    },
    "observations": {"exemplars": [{
        "kind": "product-live-primitive", "source_repository": "ck3_mod_more_tenant_slots",
        "machine_id": "bf-202609141645-5434332d4d", "observed_at_utc": "2026-10-15T15:42:03.353126+00:00",
        "artifact": "artifacts/bugfix-20261015/r22-hof0100-candidate-001/proof.json",
        "artifact_sha256": "717793AB32CBC5624D17B46A9B0ADE0D850272274C06875E5F1158C7A88B1618",
        "product_report": "docs/native-main-r22-2026-10-16.md",
        "selected_native_option_index": 0, "postcondition_verified": True,
        "boundary": "actual old instance1 gone; no observed opinion delta, whole-case or later-time credit",
    }]},
}
HEAD_OF_FAITH0100_12004_SOURCE: Final = {
    "namespace": "head_of_faith",
    "definition": {"relative_path": EVENT_PATH, "line": 896, "file_sha256": EVENT_SHA256},
    "caller_candidate_resolution": "external-definition-file",
    "caller_candidates": [{"relative_path": "common/on_action/religion_on_actions.txt", "line": 593, "column": 20,
                           "file_sha256": "EF9367DDF5F89C912B895743F8B72441E88AF3A5B03A5C1A9EDDEA0E5681EE2D",
                           "kind": "exact-token-lexical-candidate"}],
}
