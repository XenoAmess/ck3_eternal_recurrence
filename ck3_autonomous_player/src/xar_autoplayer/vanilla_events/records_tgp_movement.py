"""Reusable CK3 1.19.0.6 event records for TGP movement events.

The timeline contract deliberately contains no campaign-specific character IDs or
dates.  Concrete live evidence belongs in the observation metadata below and is
not a second source of universal contract values.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_movement_events.0030": {
        # Both choices are terminal and beneficial.  Native 1 changes only
        # the player's influence; native 0 also changes another ruler's merit
        # and advances a friendship, so native 1 is the narrower recovery.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "other_ruler": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "other_ruler": "character",
        },
        "saved_scope_name_sets": (("my_movement", "other_ruler"),),
        "saved_scope_count": 2,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "tgp_movement_events.0110": {
        # Book construction publishes helper scopes into the event context.
        # Bind their exact source-shaped aliases and choose the second route,
        # which keeps the unavoidable artifact while avoiding friend progress.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "root_scope": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "other_ruler": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "owner": ("other_ruler",),
            "author": ("other_ruler",),
            "skill_base": ("other_ruler",),
        },
        "character_scope_differs_from": {
            "other_ruler": ("root_scope",),
        },
        "scope_types": {
            "root_scope": "character",
            "my_movement": "situation_participant_group",
            "other_ruler": "character",
            "owner": "character",
            "author": "character",
            "random_quality_bonus": "value",
            "quality": "value",
            "wealth": "value",
            "newly_created_artifact": "artifact",
            "skill_base": "character",
            "book_content_quality": "value",
        },
        "saved_scope_name_sets": ((
            "root_scope",
            "my_movement",
            "other_ruler",
            "owner",
            "author",
            "random_quality_bonus",
            "quality",
            "wealth",
            "newly_created_artifact",
            "skill_base",
            "book_content_quality",
        ),),
        "saved_scope_count": 11,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "tgp_movement_events.0160": {
        # The yearly TGP movement pulse may select this event again after its
        # ten-year event cooldown.  Bind recurrence to the caller's bounded
        # observation window instead of freezing one campaign occurrence.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "rival": "character",
            "rival_movement": "situation_participant_group",
        },
        "saved_scope_name_sets": ((
            "my_movement",
            "rival",
            "rival_movement",
        ),),
        "saved_scope_count": 3,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        # Native 0 can create a mutual fifteen-year scheme block and native 1
        # pays gold before creating it.  Native 2 preserves both resources and
        # strategic freedom; its authored effect is minor intrigue lifestyle XP
        # with the declared ambitious stress impact.
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_MOVEMENT_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "tgp_movement_events.0030": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "localization/simp_chinese/dlc/tgp/"
            "tgp_movement_events_l_simp_chinese.yml": (
                "A2ADDB9940D72F79E57BC266EA62A11CB3D0C5318E79D5F93CB8F5EE01B3943F"
            ),
        },
        "definition_lines": "649-734",
        "trigger_boundary": (
            "root is an available adult with TGP, celestial government and "
            "a dynastic-cycle participant group; at least one other eligible "
            "ruler must be in the same movement"
        ),
        "caller_semantics": (
            "yearly random-event pools; the event has a five-year cooldown"
        ),
        "immediate_effect": (
            "saves root's dynastic-cycle participant group as my_movement, "
            "then selects an eligible other ruler with extra weight for a "
            "potential friend, family member, friend, lover, or disciple"
        ),
        "option_semantics": {
            0: (
                "grants medium merit to root and other_ruler, then progresses "
                "root toward friendship with other_ruler"
            ),
            1: "grants major influence to root and has no other authored effect",
        },
        "native_ai_semantics": (
            "both options have base weight one hundred; gregarious or generous "
            "doubles native 0, while deceitful, callous, or arrogant doubles "
            "native 1"
        ),
        "after_effect": None,
        "safe_option_rationale": (
            "native1 is terminal and changes only the player's influence; it "
            "does not change another ruler's merit or create friendship state"
        ),
    },
    "tgp_movement_events.0110": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/scripted_effects/00_ep1_artifact_creation_effects.txt": (
                "712B4D4BE351A7C2DCEC0292E9BB4DF8462080E87A0BB42A3F7D7DC0CB73CE4B"
            ),
            "common/scripted_effects/01_ep1_court_artifact_creation_effects.txt": (
                "DBABE31B564910AED332829B85EDAC8E7770B0F7FA73342A54EDB3335604933E"
            ),
            "common/scripted_effects/00_relation_effects.txt": (
                "745099651760EB450DEC4D5439C73D44F4DEA19BF246A522297C42AE889A47F5"
            ),
        },
        "definition_lines": "2407-2530",
        "valid_ruler_trigger_lines": "2408-2426",
        "event_trigger_lines": "2436-2442",
        "immediate_effect_lines": "2444-2490",
        "option_lines": "2492-2525",
        "after_effect_lines": "2527-2529",
        "tgp_yearly_pool_lines": "1-45",
        "general_yearly_pool_entry_line": "3752",
        "artifact_book_effect_lines": "3700-6418",
        "artifact_quality_effect_lines": "8-522",
        "artifact_wealth_effect_lines": "524-643",
        "book_content_quality_effect_lines": "3288-3681",
        "friend_progress_effect_lines": "31-167",
        "caller_semantics": (
            "the event is a weighted candidate in both the TGP China yearly "
            "group and the general on_yearly_events group. The TGP group has a "
            "fifty-percent event chance and gives this event weight one hundred; "
            "the general group has a twenty-five-percent event chance and gives "
            "it weight two hundred"
        ),
        "frequency_boundary": (
            "both callers are yearly weighted pools whose exact probability "
            "depends on other valid candidates. The event declares a five-year "
            "cooldown and is not a daily poll"
        ),
        "trigger_boundary": (
            "ROOT must be an available adult with TGP, celestial government, "
            "and a dynastic-cycle participant group. Another non-ROOT, healthy "
            "adult celestial ruler with learning at least decent, nonnegative "
            "opinion, and a compatible decided movement must exist"
        ),
        "immediate_effect": (
            "saves ROOT as root_scope and ROOT's movement as my_movement, picks "
            "other_ruler with extra weight for friendly or family relations, "
            "then creates a book owned and authored by that ruler. It fixes the "
            "book rarity to masterwork after creation"
        ),
        "source_scope_boundary": (
            "the generic book builder aliases other_ruler as owner and author, "
            "publishes random_quality_bonus, quality, wealth, and the created "
            "artifact, then aliases author as skill_base and publishes "
            "book_content_quality. R416 observed all eleven resulting scopes"
        ),
        "option_semantics": {
            0: (
                "grants medium XP for ROOT's appropriate lifestyle and calls "
                "progress_towards_friend_effect with other_ruler. That effect "
                "can create potential_friend or upgrade it to friend"
            ),
            1: (
                "grants medium_prestige_gain to ROOT and does not progress a "
                "relationship"
            ),
        },
        "native_ai_weights": {
            0: "base 100, doubled when ROOT is gregarious or diligent",
            1: "base 100, doubled when ROOT is arrogant or lazy",
        },
        "after_effect": (
            "transfers newly_created_artifact to ROOT for either option; the "
            "masterwork book is therefore an unavoidable event effect"
        ),
        "follow_up_event": None,
        "safe_option_rationale": (
            "authored option 2/native 1 keeps the unavoidable masterwork book "
            "and adds prestige while avoiding native 0's potential-friend or "
            "friend state change"
        ),
    },
    "tgp_movement_events.0160": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "localization/simp_chinese/dlc/tgp/"
            "tgp_movement_events_l_simp_chinese.yml": (
                "A2ADDB9940D72F79E57BC266EA62A11CB3D0C5318E79D5F93CB8F5EE01B3943F"
            ),
        },
        "definition_lines": "3526-3699",
        "caller_semantics": (
            "yearly random-event pools; event-local cooldown is ten years"
        ),
        "option_semantics": {
            0: "diplomacy duel; success creates a mutual fifteen-year scheme block",
            1: "pays medium gold and creates the mutual fifteen-year scheme block",
            2: "minor intrigue lifestyle XP; no gold payment or scheme block",
        },
        "after_effect": None,
        "safe_option_rationale": (
            "native2 avoids the stochastic or guaranteed fifteen-year scheme "
            "restriction and avoids the native1 gold transfer"
        ),
    },
}


VANILLA_TGP_MOVEMENT_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "tgp_movement_events.0030": {
        "exemplars": [{
            "run": "R414",
            "kind": "pre-selection-live-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/"
                "terminal-stages-red-attempt-04.json"
            ),
            "artifact_sha256": (
                "CC9AD4AE45201F1AA3693626975DAADBEE395F448A76BB9E3DCD303A350AB013"
            ),
            "date_raw": 53733456,
            "event_instance_id": 1072,
            "root_character_id": 32904,
            "saved_character_ids": {"other_ruler": 33621094},
            "saved_scope_raw_types": {
                "my_movement": 61,
                "other_ruler": 4,
            },
            "rendered_native_option_indices": [0, 1],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 202268,
            "snapshot_id": "native:1287",
            "revision": 1288,
            "process_restart_required": False,
            "retained_red": True,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
    "tgp_movement_events.0110": {
        "exemplars": [{
            "run": "R416",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r416-20260911/live-artifacts/"
                "terminal-stages-red-attempt-03.json"
            ),
            "artifact_sha256": (
                "7F2523869BEAFBC279D9ACDE65CB48661CCD1773D6CE40EB366E5EC5C9CB109A"
            ),
            "date_raw": 53814264,
            "event_instance_id": 1079,
            "root_character_id": 32904,
            "snapshot_id": "native:396",
            "revision": 397,
            "native_revision": 396,
            "saved_character_ids": {
                "root_scope": 32904,
                "other_ruler": 16837319,
                "owner": 16837319,
                "author": 16837319,
                "skill_base": 16837319,
            },
            "saved_scope_raw_types": {
                "root_scope": 4,
                "my_movement": 61,
                "other_ruler": 4,
                "owner": 4,
                "author": 4,
                "random_quality_bonus": 1,
                "quality": 1,
                "wealth": 1,
                "newly_created_artifact": 31,
                "skill_base": 4,
                "book_content_quality": 1,
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
        }],
    },
    "tgp_movement_events.0160": {
        "exemplars": [{
            "run": "R372",
            "kind": "paused-live-exemplar",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-4.json"
            ),
            "artifact_sha256": (
                "3D0BBB7C7AFCE08003329DF248301BAD4216D8BE47FBE4F24703A4E89E5D0E68"
            ),
            "date_raw": 53436720,
            "event_instance_id": 668,
            "root_character_id": 32904,
            "saved_character_ids": {"rival": 37625},
            "saved_scope_raw_types": {
                "my_movement": 61,
                "rival": 4,
                "rival_movement": 61,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selection_attempted": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_TGP_MOVEMENT_ANALYSIS",
    "VANILLA_TGP_MOVEMENT_OBSERVATIONS",
    "VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS",
]
