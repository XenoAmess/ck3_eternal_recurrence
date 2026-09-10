"""Reusable CK3 1.19.0.6 records for the TGP treasury renewal prompt.

The contract is source-shaped and campaign-neutral.  R374 freezes a visible
identity-only RED, while R375 freezes the later native MCP selection GREEN.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


_TREASURY_PREFERENCE_SCOPES: Final = (
    "salary_budget",
    "ministry_budget",
    "military_budget",
    "hegemon_budget",
    "meritocratic_salary_budget",
    "meritocratic_military_budget",
)


VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_china_ministry.0100": {
        # The yearly caller always saves treasury_ruler.  A source-selected
        # steward and one preference alias are conditional: a realm can have
        # no suitable steward, and the non-celestial preference list can have
        # no eligible entry.  Admit only those authored combinations.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "treasury_ruler": PLAYER_SENTINEL,
        },
        "optional_character_scopes": {
            name: PLAYER_SENTINEL for name in _TREASURY_PREFERENCE_SCOPES
        },
        "optional_unique_character_scope_excludes": {
            "steward": (PLAYER_SENTINEL,),
        },
        "optional_scope_types": {
            "steward": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            ("treasury_ruler",),
            ("treasury_ruler", "steward"),
        ) + tuple(
            ("treasury_ruler", "steward", preference_scope)
            for preference_scope in _TREASURY_PREFERENCE_SCOPES
        ),
        "saved_scope_counts": (1, 2, 3),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "option_variants": ({
            # Without a steward, authored option C is hidden.  Retaining the
            # current allocation remains native 1 in either projection.
            "option_count": 2,
            "snapshot_option_count": 3,
            "native_option_indices": (0, 1),
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        },),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_TREASURY_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "tgp_china_ministry.0100": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_china_ministry_events.txt": (
                "87358436D60431BC80DA0376DD1BB2C47696EFCDE813148C69883768439980EE"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "common/scripted_effects/10_dlc_tgp_scripted_effects.txt": (
                "AEF36B884DC5E315DD5C655BC96012FF9FA8BB46BB0AF2C18FA878C890907747"
            ),
            "common/scripted_triggers/10_tgp_triggers.txt": (
                "8294C1D72ECC909428ABFBA27D6F10B127D796D2BEE350D1BB95024F36D60C99"
            ),
            "localization/simp_chinese/dlc/tgp/"
            "tgp_ministry_events_l_simp_chinese.yml": (
                "6AD38C15CAE1CD3EAC713EDBC1566C7D42D8CE3B94291139F976C439020F8210"
            ),
        },
        "definition_lines": "509-830",
        "yearly_caller_lines": "838-962",
        "preference_trigger_lines": "692-770",
        "budget_template_effect_lines": "3355-3545",
        "localization_lines": "26-36",
        "caller_semantics": (
            "yearly_playable_pulse directly triggers this event for a playable "
            "top liege with a treasury; the event trigger additionally keeps "
            "a human ruler out while travelling"
        ),
        "frequency_boundary": (
            "the caller runs once per year, not daily. A human renewal becomes "
            "eligible after ninety-six months without a new budget, or earlier "
            "when new capacity reaches at least 1.3 times current capacity or "
            "monthly treasury balance falls below minus fifty"
        ),
        "trigger_boundary": (
            "ROOT must still be the top liege and have a treasury; a human ROOT "
            "must not be travelling"
        ),
        "immediate_effect": (
            "saves ROOT as treasury_ruler, optionally selects a steward from "
            "council positions or vassals, and optionally saves one of six "
            "source-authored preference aliases on ROOT"
        ),
        "scope_boundary": (
            "the portable contract admits only treasury_ruler, optional steward, "
            "and at most one exact celestial or meritocratic preference alias. "
            "R374 did not publish a trustworthy native saved-scope frame, so no "
            "campaign identities or exact live scope set are claimed"
        ),
        "option_semantics": {
            0: (
                "for a human player, opens tgp_china_ministry.0101 to choose a "
                "specific budget; it is therefore a non-terminal second prompt"
            ),
            1: (
                "keeps the existing allocation and enacts the current treasury "
                "budgets without costs; it opens no scripted follow-up event"
            ),
            2: (
                "shown only when steward exists; enacts that character's saved "
                "preference or the relevant balanced fallback, changing budget "
                "allocation laws through the source template effects"
            ),
        },
        "after_effect": None,
        "repeatability": (
            "the yearly caller and renewable time/capacity/deficit conditions "
            "allow later independent prompts; no campaign-global one-shot flag "
            "or event cooldown is defined"
        ),
        "safe_option_rationale": (
            "authored option 2/native 1 is the bounded terminal route: it keeps "
            "the current allocations, avoids option 0's additional picker, and "
            "avoids option 2's source-authored allocation-law changes"
        ),
    },
}


VANILLA_TGP_TREASURY_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "tgp_china_ministry.0100": {
        "exemplars": [{
            "run": "R374",
            "kind": "foreground-ui-identity-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "park9-post-selection-ck3-screen.png"
            ),
            "artifact_sha256": (
                "B2E57E4B90EC82EBA96500B7D0B1F963A6EE46F521E4E5250C1A3BE113C7047B"
            ),
            "visible_title_text": "宋国库",
            "visible_option_texts": [
                "好吧。我们来制定新预算。",
                "维持原有分配方案。",
                "这件事我相信你的判断。",
            ],
            "rendered_option_count": 3,
            "identity_basis": (
                "the foreground title and all three option strings exactly match "
                "the frozen Simplified Chinese localization for .0100"
            ),
            "current_event_context_status": "unavailable",
            "current_event_context_unavailable_reason": (
                "the native service retained paused=false and active_event=null "
                "after the preceding selection, so no event instance, date, root, "
                "saved-scope set, or option-state projection is frozen here"
            ),
            "selection_attempted": False,
        }, {
            "run": "R375",
            "kind": "production-live-primitive",
            "production_live_ordinal": 14,
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-live-014-tgp-china-ministry-0100-green.json"
            ),
            "artifact_sha256": (
                "6C1407AF00D2E767FA201DA2411619D5724C86951BB5CEFF006DAB50ABC6C779"
            ),
            "date_raw": 53609928,
            "event_instance_id": 1057,
            "root_character_id": 32904,
            "bridge_pid": 180544,
            "connection_generation": 1,
            "context_query_driver_command_index": 291,
            "selection_driver_command_index": 292,
            "context_snapshot_id": "native:356",
            "context_native_revision": 356,
            "saved_character_ids": {
                "treasury_ruler": 32904,
                "steward": 38076,
                "military_budget": 32904,
            },
            "saved_scope_raw_types": {
                "treasury_ruler": 4,
                "steward": 4,
                "military_budget": 4,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selected_option_number": 2,
            "selected_native_option_index": 1,
            "postcondition_verified": True,
            "ending_snapshot_id": "native:357",
            "ending_revision": 358,
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
    "VANILLA_TGP_TREASURY_ANALYSIS",
    "VANILLA_TGP_TREASURY_OBSERVATIONS",
    "VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS",
]
