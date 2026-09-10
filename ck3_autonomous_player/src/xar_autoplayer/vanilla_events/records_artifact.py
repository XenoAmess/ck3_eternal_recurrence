"""Reusable CK3 1.19.0.6 event records for artifact events."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_ARTIFACT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "artifact.4040": {
        # The expert always adds a martial modifier to the selected artifact.
        # Accept the bounded favor-hook or minor-gold cost rather than discard
        # the only positive route.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "helpful": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "this_artifact": "artifact",
            "helpful": "character",
        },
        "saved_scope_name_sets": (("this_artifact", "helpful"),),
        "saved_scope_count": 2,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_ARTIFACT_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "artifact.4040": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/artifacts/artifact_events.txt": (
                "32D30D9E2BCCB953B8760A5129754155BDBEC829D696BCB5ADDA43393B8B82A7"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "localization/english/event_localization/artifact_events_l_english.yml": (
                "49D9F28ECE0AFF971474A47CE6D71B65E1575FBD23F1D4D22C3B512651D9D10B"
            ),
            "localization/simp_chinese/event_localization/"
            "artifact_events_l_simp_chinese.yml": (
                "479FF00978C954D2B0CDC8D33776B49007FAB8EA46C613C51024D4B47B0BF9CC"
            ),
        },
        "relevant_courtier_trigger_lines": "3046-3063",
        "definition_lines": "3066-3292",
        "trigger_lines": "3085-3104",
        "immediate_effect_lines": "3114-3149",
        "option_lines": "3151-3291",
        "on_yearly_pool_entry_line": "3275",
        "caller_semantics": (
            "the event is a weight-eighty candidate in on_yearly_events. That "
            "group is reached from the random yearly playable pulse and has a "
            "twenty-five-percent event chance before valid-candidate weighting"
        ),
        "frequency_boundary": (
            "the exact annual probability depends on every other valid yearly "
            "candidate. The event declares a thirty-year cooldown and is not a "
            "daily poll"
        ),
        "trigger_boundary": (
            "ROOT owns an uncursed, not-recently-improved armor or primary "
            "weapon and has an eligible courtier, guest, or knight with prowess "
            "at least twenty or one of the listed martial education, lifestyle, "
            "terrain, berserker, varangian, or reaver traits"
        ),
        "immediate_effect": (
            "chooses one eligible armor or primary weapon as this_artifact, "
            "then chooses one eligible courtier or guest when possible and "
            "otherwise an eligible knight as helpful"
        ),
        "scope_boundary": (
            "the event publishes exactly one artifact and one non-ROOT helpful "
            "character in the observed source shape"
        ),
        "option_semantics": {
            0: (
                "sets artifact_improved_var on this_artifact for one hundred "
                "years. helpful gains a favor hook over ROOT when legal; "
                "otherwise ROOT pays helpful minor_gold_value. The artifact "
                "then always gains one source-selected martial modifier: raid "
                "speed, heavy-cavalry toughness, heavy-infantry toughness, "
                "knight effectiveness, or prowess"
            ),
            1: "refuses the offer and has no authored effect",
        },
        "native_ai_weights": {
            0: "base 150",
            1: "base 50, plus 50 when ROOT is arrogant",
        },
        "after_effect": None,
        "follow_up_event": None,
        "safe_option_rationale": (
            "authored option 1/native 0 is the only positive route and always "
            "improves the selected martial artifact. Its exact cost is bounded "
            "to a favor hook held by helpful or minor gold; native 1 discards "
            "the upgrade without compensation"
        ),
    },
}


VANILLA_ARTIFACT_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "artifact.4040": {
        "exemplars": [{
            "run": "R416",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-04.json"
            ),
            "artifact_sha256": (
                "CFD57E5C381D35EE6E1DE166D9FF656A1E6D6F4FC7D3194BCC74393EB3B4EE6A"
            ),
            "date_raw": 53832072,
            "event_instance_id": 1081,
            "root_character_id": 32904,
            "snapshot_id": "native:625",
            "revision": 626,
            "native_revision": 625,
            "saved_character_ids": {"helpful": 79104},
            "saved_scope_raw_types": {
                "this_artifact": 31,
                "helpful": 4,
            },
            "rendered_native_option_indices": [0, 1],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_id": 174656,
            "connection_generation": 1,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }, {
            "run": "R416-retry-05",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-05.json"
            ),
            "artifact_sha256": (
                "0BFAB9EF8D38AE9C74F783FE3E4B3672222E5289F760D21074BD04D5683692AA"
            ),
            "date_raw": 53832072,
            "event_instance_id": 1081,
            "root_character_id": 32904,
            "starting_snapshot_id": "native:626",
            "starting_revision": 627,
            "ending_snapshot_id": "native:627",
            "ending_revision": 628,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 174656,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_ARTIFACT_ANALYSIS",
    "VANILLA_ARTIFACT_OBSERVATIONS",
    "VANILLA_ARTIFACT_TIMELINE_CONTRACTS",
]
