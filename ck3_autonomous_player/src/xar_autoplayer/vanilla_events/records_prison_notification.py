"""Source-bound acknowledgement contracts for natural prisoner notifications."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


_EVENT_SOURCE_SHA256: Final = (
    "56023FBADC5F56C98293B1FB4AB7D846AD957F115B2E329422A0DCAD283B6C7F"
)
_ON_ACTION_SOURCE_SHA256: Final = (
    "D9CEBF10ED0E2E5ECC33E18BC71768F634E5F5504B690C5EDE6B095ACC1A2ECD"
)
_SOURCE_HASHES: Final = {
    "events/prison_events/prison_notification_events.txt": _EVENT_SOURCE_SHA256,
    "common/on_action/prison_on_actions.txt": _ON_ACTION_SOURCE_SHA256,
}

_BASE_CONTRACT: Final = {
    "date_policy": "product-observation-window",
    "root_character_id": PLAYER_SENTINEL,
    "character_scopes": {
        "prisoner": PLAYER_SENTINEL,
        "this_player": PLAYER_SENTINEL,
    },
    "character_scope_matches_any": {
        "bg_override_char": ("imprisoner",),
    },
    "character_scope_differs_from": {
        "imprisoner": ("prisoner",),
    },
    "scope_types": {
        "prisoner": "character",
        "imprisoner": "character",
        "bg_override_char": "character",
        "this_player": "character",
    },
    "saved_scope_name_sets": ((
        "prisoner", "imprisoner", "bg_override_char", "this_player",
    ),),
    "saved_scope_count": 4,
    "boolean_scopes": (),
    "option_count": 1,
    "snapshot_option_count": 1,
    "native_option_indices": (0,),
    "selected_option_number": 1,
    "selected_native_option_index": 0,
    "occurrence_policy": "repeatable-within-product-observation-window",
}


VANILLA_PRISON_NOTIFICATION_TIMELINE_CONTRACTS: Final = {
    "prison_notification.0001": dict(_BASE_CONTRACT),
    "prison_notification.2001": dict(_BASE_CONTRACT),
}

VANILLA_PRISON_NOTIFICATION_ANALYSIS: Final = {
    key: {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
        },
        "source_sha256": dict(_SOURCE_HASHES),
        "definition_lines": (
            "6-97" if key.endswith(".0001") else "269-323"
        ),
        "caller_lines": (
            "common/on_action/prison_on_actions.txt:7-239"
            if key.endswith(".0001")
            else "common/on_action/prison_on_actions.txt:254-343"
        ),
        "caller_semantics": (
            "on_imprison delivers the notice to the already-imprisoned root"
            if key.endswith(".0001")
            else "on_release_from_prison delivers the notice to the already-released root"
        ),
        "option_semantics": {0: "empty acknowledgement; no authored option effect"},
        "safe_option_rationale": (
            "the exact-build sole native 0 option only closes the notice; "
            "the imprisonment or release happened before the event and "
            "requires a separate paused material readback"
        ),
        "unreviewed_boundary": (
            "different source, root/role projection, or option shape blocks; "
            "event disappearance is not prison-state evidence"
        ),
    }
    for key in VANILLA_PRISON_NOTIFICATION_TIMELINE_CONTRACTS
}

VANILLA_PRISON_NOTIFICATION_OBSERVATIONS: Final = {
    "prison_notification.0001": {
        "exemplars": [{
            "run": "R0109",
            "kind": "natural-notice-acknowledgement-material-unverified",
            "artifact": (
                ".task-tmp/RUN-001/century-h1120-continuation/"
                "R0109-evidence-manifest.json"
            ),
            "artifact_sha256": (
                "2B874A64581273A6555B6F6F85757357E1F3A4028788DF49D3FF1870F7724E97"
            ),
            "event_instance_id": 24,
            "root_character_id": 36403,
            "selection_postcondition": "event_instance_advanced",
            "formal_next_turn_consumed": True,
            "material_imprisonment_verified": False,
            "retained_red": True,
        }],
    },
    "prison_notification.2001": {
        "exemplars": [{
            "run": "R0109",
            "kind": "natural-notice-acknowledgement-material-unverified",
            "artifact": (
                ".task-tmp/RUN-001/century-h1120-continuation/"
                "R0109-evidence-manifest.json"
            ),
            "artifact_sha256": (
                "2B874A64581273A6555B6F6F85757357E1F3A4028788DF49D3FF1870F7724E97"
            ),
            "event_instance_id": 25,
            "root_character_id": 36403,
            "selection_postcondition": "event_instance_advanced",
            "formal_next_turn_consumed": True,
            "material_release_verified": False,
            "retained_red": True,
        }],
    },
}

__all__ = [
    "VANILLA_PRISON_NOTIFICATION_ANALYSIS",
    "VANILLA_PRISON_NOTIFICATION_OBSERVATIONS",
    "VANILLA_PRISON_NOTIFICATION_TIMELINE_CONTRACTS",
]
