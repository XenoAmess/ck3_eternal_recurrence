"""Reusable CK3 1.19.0.6 records for vanilla vassal interactions.

Campaign-specific identities and dates stay in the observations table.  The
timeline contract is therefore safe to reuse from another save, operator, or
machine through the read-only vanilla-event knowledge query.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "vassal_interaction.0040": {
        # The claim interaction has already resolved when this letter is
        # displayed. Its sole event option only shows that prior effect as a
        # tooltip, so it is safe to acknowledge after matching the exact live
        # scope and option projection.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "recipient": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "actor": (PLAYER_SENTINEL,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {
            "target": "landed_title",
            "county_in_title": "province",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "target",
            "county_in_title",
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # The current actor/target pair cannot repeat after receiving its
        # claim, but other actors and eligible titles can emit this event.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_VASSAL_INTERACTION_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "vassal_interaction.0040": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/interaction_events/vassal_interaction_events.txt": (
                "97C706C9EC1CF5B3A6520C27A6683B68EB94D89EF9DBAD3D745C3ED4386ED247"
            ),
            "common/character_interactions/00_vassal_interactions.txt": (
                "1249CAC40138D48210A07245746C4A6683C5F58F3141C04A20DB2C00B6375BF8"
            ),
            "common/scripted_effects/00_interaction_effects.txt": (
                "7B426465FCED71A6D6AA96B34C8924B91990D0BE144FE4BFAA57681BB7FA6EA5"
            ),
        },
        "definition_lines": "1416-1433",
        "interaction_definition_lines": "2903-3418",
        "caller_semantics": (
            "vassal_claim_liege_title_interaction is auto-accepted; its "
            "on_auto_accept block selects a qualifying de-jure county, saves "
            "county_in_title, and sends this letter to the recipient"
        ),
        "caller_line_boundaries": {
            "on_auto_accept": "3180-3200",
            "on_accept": "3202-3222",
            "auto_accept_and_ai_frequency": "3224-3236",
            "ai_policy": "3238-3417",
        },
        "eligibility_boundary": (
            "the actor is an adult vassal of the recipient, targets an "
            "eligible recipient title, controls the legitimacy-dependent "
            "de-jure share, and does not already hold a claim on that target"
        ),
        "frequency_boundary": (
            "the event has no event cooldown or one-shot flag; the source "
            "interaction is auto-accepted and gives AI frequency values of "
            "48 for counts, 24 for dukes/kings/emperors, and 0 for barons and "
            "hegemons"
        ),
        "interaction_effect_lines": "4233-4244",
        "interaction_effect": (
            "on interaction acceptance the actor receives an unpressed claim "
            "on target and the recipient receives claimed_my_title_opinion "
            "minus fifty toward the actor"
        ),
        "event_immediate_effect": None,
        "option_semantics": {
            0: (
                "acknowledgement-only; show_as_tooltip displays the actor's "
                "unpressed claim but does not execute that effect again"
            ),
        },
        "after_effect": None,
        "repeatability": (
            "the resolved actor/target pair is then blocked by the existing "
            "claim, but the event definition has no occurrence ceiling and "
            "other qualifying actors or titles can deliver it again"
        ),
        "safe_option_rationale": (
            "native option 0 is the only rendered and source-authored option; "
            "the material claim and opinion changes belong to the already "
            "resolved interaction, while dismissal has no gameplay effect"
        ),
    },
}


VANILLA_VASSAL_INTERACTION_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "vassal_interaction.0040": {
        "exemplars": [{
            "run": "R374",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "vassal-interaction-0040-red-report.json"
            ),
            "artifact_sha256": (
                "E6E1D565AA74A004B5F995457D4DB52AF5E6829430B2DCB14B16A69F4B7FB529"
            ),
            "park_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "hot-recovery-park-5.json"
            ),
            "park_artifact_sha256": (
                "D1CA6DA488048CF7F77A81F53290F57AF4BA36D15ABCD6E502A9B080B2627293"
            ),
            "driver_state_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "driver-state-park-5-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "D0137F8780BEB0E6A18A4A4E25ABE9E1436FD683A4473CC025CE6258B22FA1E1"
            ),
            "date_raw": 53582544,
            "event_instance_id": 1038,
            "root_character_id": 32904,
            "saved_character_ids": {
                "actor": 39232,
                "recipient": 32904,
            },
            "unavailable_character_scopes": [
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
            ],
            "saved_scope_raw_types": {
                "actor": 4,
                "recipient": 4,
                "secondary_actor": 4,
                "secondary_recipient": 4,
                "intermediary": 4,
                "target": 5,
                "county_in_title": 8,
            },
            "rendered_native_option_indices": [0],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 51852,
            "snapshot_id": "native:1655",
            "revision": 1656,
            "remaining_game_days": 2223,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_VASSAL_INTERACTION_ANALYSIS",
    "VANILLA_VASSAL_INTERACTION_OBSERVATIONS",
    "VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS",
]
