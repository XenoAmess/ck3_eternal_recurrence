"""Exact .3 populist ultimatum recognition and review-only consequences."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


EVENT_KEY: Final = "faction_demand.1001"
SAVED_SCOPE_TYPES: Final = {
    "faction": "faction", "peasant_county": "landed_title",
    "faction_target": "character", "target_title": "landed_title",
    "peasant_leader": "character", "new_title": "landed_title",
    "faction_leader": "character",
}
SOURCE_HASHES: Final = {
    "events/factions/faction_demands.txt": "EB17720CA9D48ACFB8CC24E5F61EDC62FD2D4D2D599561C92854FC762104ECCD",
    "common/scripted_effects/00_faction_effects.txt": "C7F853B9C8CF836CFC6B635C58BFA3C31A686528E99F5628E320A1D97A5EFC70",
}
FACTION_DEMAND1001_12003_RECORDS: Final = {
    EVENT_KEY: {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "character_scopes": {"faction_target": PLAYER_SENTINEL},
            "character_scope_differs_from": {"peasant_leader": (PLAYER_SENTINEL,)},
            "scope_types": SAVED_SCOPE_TYPES,
            "saved_scope_name_sets": (tuple(SAVED_SCOPE_TYPES),),
            "saved_scope_count": 7,
            "option_count": 2, "snapshot_option_count": 4,
            "native_option_indices": (2, 3),
            "native_to_api_option_numbers": {"2": 3, "3": 4},
            "selected_option_number": None, "selected_native_option_index": None,
            "selection_deferred": True,
            "handling_policy": "readonly_populist_ultimatum_comparison",
            "occurrence_policy": "repeatable-within-product-observation-window",
        },
        "analysis": {
            "exact_build": {"game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598},
            "source_sha256": SOURCE_HASHES,
            "definition_lines": "846-1428",
            "definition_block_sha256": "007FB21DA53133CA77D219D17ED54A2B2422EAAAA51EE605BFE67DC1BFE9603D",
            "authored_option_count": 4,
            "reviewed_native_option_indices": (2, 3),
            "readiness": "static-ready", "new_live_evidence": False,
            "native_ai_tree": "docs/ck3-native-ai/ck3-1.20.0.3-faction-demand1001-populist.md",
            "option_semantics": {
                "2": {"native_option_index": 2, "api_option_number": 3,
                    "source_lines": "1190-1215",
                    "prestige_level_delta": -1,
                    "dread": {"condition": "current_dread_gt_zero", "script_delta": -20,
                        "observed_net_delta": None},
                    "effect": "successful_popular_revolt_outcome_effect",
                    "ordinary_branch": "member counties expand to target realm de-jure duchy counties and qualifying held duchies; independent kingdom groups with conditional kingdom usurpation",
                    "state_faith_branch": "ruler and held-title transfer branches; ordinary title sets do not predict this branch",
                    "stress_effect": "none_explicit_in_reviewed_native2_or_common_after",
                    "guaranteed_fixed_gold_delta": None},
                "3": {"native_option_index": 3, "api_option_number": 4,
                    "source_lines": "1337-1358", "effect": "faction_start_war",
                    "title_scope": "target_title", "war_execution_authorized": True,
                    "actual_war_id": None, "exact_cb_key": None,
                    "stress_effect": "none_explicit_in_reviewed_native3_or_common_after"},
            },
            "common_after": "remove faction_targets_player variable only if faction remains and owns it; does not end a war",
            "selection_boundary": "Owner authorization on 2026-10-03 removes all nonwar-only constraints and authorizes combat research and war execution. This read-only review does not select or submit an option; action readiness remains independent of authorization.",
            "material_evidence_boundary": "Source semantics and fixture binding are not title transfer, war execution, or G2 credit.",
        },
        "observations": {"exemplars": [{
            "kind": "closed-production-red",
            "artifact": "artifacts/g2-maintainer-2026-10-02/resume-12003/m2-events/actual-v32-faction-demand1001-blocker-01/actual-typed-context.json",
            "event_instance_id": 23, "root_character_id": 29829,
            "date_raw": 53236608, "native_revision": 64,
            "selection_attempted": False,
            "boundary": "Original actual event had seven saved roles and native2/3 presentation; saved title/faction identities were unavailable.",
        }]},
    },
}
