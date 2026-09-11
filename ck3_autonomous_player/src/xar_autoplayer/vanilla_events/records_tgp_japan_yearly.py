"""Exact-build record for the TGP Japanese shrine yearly event."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_TGP_JAPAN_YEARLY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_japan_yearly_events.1030": {
        # The source authors five options, but the cynical-only fifth route was
        # absent from the R463 played-character projection. The first route is
        # an unconditional, terminal health choice and requires no saved scope.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_names": (),
        "saved_scope_count": 0,
        "option_count": 4,
        "snapshot_option_count": 5,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_TGP_JAPAN_YEARLY_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_japan_yearly_events.1030": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/dlc/tgp/tgp_japan_yearly_events_ariana.txt": (
                "B9F5799465E9B83B16C97086BC74F43ECD3949680AE1A78C081ED44ECD9B5FD6"
            ),
            "common/on_action/dlc/tgp/tgp_japan_yearly_on_actions.txt": (
                "40D68D6306D3E180E40EFBC80D5879DA825AB111F7EC0870682AB414F2AD5FE4"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "926-1089",
        "caller_lines": (
            "tgp_japan_yearly_on_actions.txt:1-50 (weighted candidate at 24); "
            "yearly_on_actions.txt:2552-2563 (TGP yearly pool at 2558)"
        ),
        "caller_semantics": (
            "the yearly character pulse may select the TGP Japanese pool for an "
            "eligible Japanese character; that pool has a 50-percent chance to "
            "draw one weighted event and lists .1030 at weight 100"
        ),
        "trigger_boundary": (
            "the pool requires the TGP DLC plus Japanese heritage, a Japanese "
            "capital, or Japanese government; .1030 additionally requires an "
            "available adult and has a 15-year event cooldown"
        ),
        "scope_boundary": (
            "R463 publishes the played character as root and no saved scopes; "
            "the portable contract binds only that empty scope frame"
        ),
        "immediate_effect": None,
        "option_semantics": {
            0: (
                "adds tgp_shrine_health_modifier for five years, always reduces "
                "minor stress, and has a 25-percent wound improvement roll when wounded"
            ),
            1: "adds tgp_shrine_heir_modifier for five years with trait-based stress",
            2: "adds tgp_shrine_wealth_modifier for five years with trait-based stress",
            3: (
                "adds tgp_shrine_piety_modifier for five years, minor piety, and "
                "trait-based stress"
            ),
            4: (
                "cynical-only route that grants minor prestige and reduces medium stress"
            ),
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": "the event owns a 15-year cooldown and no one-shot flag",
        "safe_option_rationale": (
            "authored option 1/native 0 is unconditional and terminal. It gives "
            "the player a five-year health modifier, cannot spend resources or "
            "start a follow-up, and may improve an existing wound. This narrow "
            "effect comparison does not inspect faith, doctrine, tenet, fervor, "
            "conversion, or other deferred religion-domain state"
        ),
    },
}


VANILLA_TGP_JAPAN_YEARLY_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_japan_yearly_events.1030": {
        "exemplars": [{
            "run": "R463",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p1-stage10-source-r349-r462-r463-20260912/"
                "r463-tgp-japan-yearly-1030-red-freeze.json"
            ),
            "artifact_sha256": (
                "07BC6B2AA7A4AD2AC5AE4422CE9B129118C1940123DD187E2A3BC8AE2AE5A4C6"
            ),
            "date_raw": 53219640,
            "event_instance_id": 343,
            "root_character_id": 32904,
            "saved_scope_count": 0,
            "rendered_native_option_indices": [0, 1, 2, 3],
            "snapshot_option_count": 5,
            "selection_attempted": False,
            "connection_generation": 1,
            "ck3_pid": 113420,
            "snapshot_id": "native:44",
            "revision": 45,
            "retained_red": True,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }, {
            "run": "R465",
            "kind": "selection-postcondition-live-green-with-source-exhaustion",
            "artifact": (
                "_runtime/p1-stage10-r463-partial-r464-r465-20260912/"
                "live-artifacts/terminal-stages-red.json"
            ),
            "artifact_sha256": (
                "665CC017AA69346C352D3EBC36A6A1F49721F763EADE2348BDEFC9DEEFCA814F"
            ),
            "date_raw": 53219640,
            "event_instance_id": 343,
            "root_character_id": 32904,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "selection_postcondition": "event_instance_advanced",
            "ending_event_instance_id": None,
            "starting_snapshot_id": "native:3",
            "starting_revision": 4,
            "ending_snapshot_id": "native:4",
            "ending_revision": 5,
            "connection_generation": 1,
            "ck3_pid": 134852,
            "selection_result": "GREEN",
            "source_route_result": "RED",
            "source_route_reason": "fixed_10_day_window_exhausted_without_zg361cl.390",
            "source_route_absolute_end_date_raw": 53219880,
            "last_observed_date_raw": 53219928,
            "stage10_source_receipt_emitted": False,
            "retained_red": True,
            "process_restart_required": True,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "VANILLA_TGP_JAPAN_YEARLY_ANALYSIS",
    "VANILLA_TGP_JAPAN_YEARLY_OBSERVATIONS",
    "VANILLA_TGP_JAPAN_YEARLY_TIMELINE_CONTRACTS",
]
