"""Reusable CK3 1.19.0.6 record for the yearly forbidden-love event.

The contract is source-shaped and campaign-neutral.  R414 contributes the
first paused native observation; its date, process, event-instance, and
character identities remain evidence metadata only.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_YEARLY_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        # The event always saves two different relatives and their lover
        # secret.  Authored option 4 is trigger-gated and was hidden in R414;
        # retain the three rendered native rows and choose the protective,
        # terminal first option.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (PLAYER_SENTINEL,),
            "relative": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "child": ("relative",),
            "relative": ("child",),
        },
        "scope_types": {
            "child": "character",
            "relative": "character",
            "secret": "secret",
        },
        "saved_scope_name_sets": (("child", "relative", "secret"),),
        "saved_scope_count": 3,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_YEARLY_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/yearly_events/yearly_events.txt": (
                "FBBD29C7C9ECDCB84342EF4F00E92358412781B27E0686DCC220592996FEF0E5"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "766-1103",
        "trigger_lines": "789-798",
        "weight_multiplier_lines": "800-829",
        "immediate_effect_lines": "831-956",
        "option_lines": "958-1102",
        "yearly_pulse_lines": "2522-2563",
        "yearly_pool_lines": "2933-2941",
        "caller_semantics": (
            "code invokes random_yearly_playable_pulse once per playable "
            "character at an independently random point each year; that pulse "
            "can choose on_yearly_events with group weight six, whose inner "
            "twenty-five-percent random-event pool assigns this event weight ten"
        ),
        "frequency_boundary": (
            "the exact annual probability varies with valid outer groups and "
            "inner candidates. The event is a yearly-pulse candidate, has no "
            "daily poll, and defines no cooldown or one-shot flag"
        ),
        "trigger_boundary": (
            "ROOT must have an eligible child who in turn has an eligible close "
            "or extended family member for the forbidden-love pairing"
        ),
        "weight_boundary": (
            "base event weight is one half, rises for eligible lustful or deviant "
            "children, and receives an additional five for a human ROOT"
        ),
        "immediate_effect": (
            "selects the child and relative, establishes their lover relation "
            "when permitted, saves the matching lover secret, and reveals that "
            "secret privately to ROOT before any player option is chosen"
        ),
        "scope_boundary": (
            "child and relative are distinct non-ROOT characters; secret is a "
            "generic secret scope whose stable identity is not exposed by the "
            "current bridge. Campaign identities do not enter the contract"
        ),
        "option_semantics": {
            0: (
                "protects both characters: each gains fifty grateful opinion of "
                "ROOT, child gains the protection modifier for fifteen years, "
                "and relative gains it too when ROOT is their liege; zealous or "
                "vengeful ROOT can take minor stress"
            ),
            1: (
                "gains minor piety and publicly exposes the lover secret; cynical "
                "or lustful ROOT can take minor stress"
            ),
            2: (
                "gains minor dread, attempts source-defined imprisonment for each "
                "eligible participant, then exposes the lover secret; lustful, "
                "forgiving, or compassionate ROOT can take minor stress"
            ),
            3: (
                "is trigger-gated by approval and cheating predicates; it can "
                "establish lover relations with ROOT, performs two sex effects, "
                "creates a threesome memory, and has chaste or zealous stress"
            ),
        },
        "native_ai_boundary": (
            "the four options define no explicit ai_chance blocks in the exact "
            "source. This record therefore does not infer a hidden native utility "
            "ranking; its selection is the bounded product continuation policy"
        ),
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "the definition has no cooldown or one-shot flag, so another eligible "
            "yearly pulse may select it later"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is terminal and avoids public exposure, "
            "imprisonment attempts, dread/piety policy changes, and the sexual "
            "effects of the gated fourth option. Its bounded downside is only the "
            "declared minor stress for zealous or vengeful ROOT"
        ),
    },
}


VANILLA_YEARLY_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        "exemplars": [{
            "run": "R414",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/"
                "live-artifacts/terminal-stages-red.json"
            ),
            "artifact_sha256": (
                "7C41E07DA8BD1ACA6F3DB14EF208E35030A63EEAD99D86B7179638FB1A328279"
            ),
            "date_raw": 53639352,
            "event_instance_id": 1064,
            "root_character_id": 32904,
            "saved_character_ids": {
                "child": 37804,
                "relative": 33606148,
            },
            "saved_scope_raw_types": {
                "child": 4,
                "relative": 4,
                "secret": 7,
            },
            "snapshot_option_count": 4,
            "rendered_native_option_indices": [0, 1, 2],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_YEARLY_ANALYSIS",
    "VANILLA_YEARLY_OBSERVATIONS",
    "VANILLA_YEARLY_TIMELINE_CONTRACTS",
]
