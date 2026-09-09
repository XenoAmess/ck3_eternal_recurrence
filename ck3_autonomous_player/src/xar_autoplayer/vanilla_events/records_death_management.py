"""Reusable CK3 1.19.0.6 records for vanilla death-management events.

Campaign identities and dates are retained only as observations.  The
timeline contract can therefore be reused by the CK3 player, other mods, and
read-only MCP consumers on another operator or machine.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "death_management.1007": {
        # Exact no-killer heir-death notification observed in R374.  Keep the
        # three inherited typed scopes exact: killer/known_killer variants or
        # a missing new_memory must remain RED until independently observed.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "dead_character": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "dead_character": "character",
            "deceased_character_stress": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "dead_character",
            "deceased_character_stress",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_DEATH_MANAGEMENT_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "death_management.1007": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/death_events/death_management_events.txt": (
                "31591A2F2D3A61E65853CC43B9BEF4B001FEB75EA1502861D2FB9AC054AB1FB7"
            ),
            "common/script_values/00_stress_values.txt": (
                "104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395"
            ),
            "common/on_action/death.txt": (
                "F9D596E05A84C42E7370B63874B5172CECB574190541AD67606C68C387F5A041"
            ),
            "common/character_memory_types/_character_memories.info": (
                "644F0D24A17F21AB1686E05A1753244A5BFBBC4686631F16914803FBDCF7C5CF"
            ),
            "common/scripted_effects/00_death_management_effects.txt": (
                "921F06A614CA254EEAD3F57B4EB57F569F0B16B90369575A020461CE1877C397"
            ),
            "common/scripted_triggers/00_death_management_triggers.txt": (
                "13067098532F4F96E41F0EBCE4917F08C900957313E864F6734C6652E29951E5"
            ),
        },
        "on_death_entry_lines": ("1-5", "2156-2162"),
        "close_family_memory_lines": "966-984",
        "character_memory_abi_lines": "58-70",
        "death_blocker_effect_lines": "1-18",
        "death_blocker_trigger_lines": "1-20",
        "death_dispatch_0001_lines": ("5-13", "94-100", "340-364", "527-578"),
        "death_dispatch_0002_lines": ("582-606", "608-706"),
        "heir_family_dispatch_lines": "690-696",
        "definition_lines": "1948-2057",
        "trigger_lines": "2004-2006",
        "immediate_lines": "2008-2036",
        "option_lines": "2038-2044",
        "after_lines": "2046-2056",
        "minor_stress_impact_gain_line": "27",
        "caller_semantics": (
            "on_death creates a relative_died character memory for each close "
            "family member and create_character_memory saves it as new_memory; "
            "death_management.0001 saves the dying character as dead_character, "
            "collects interested recipients, calculates each recipient's "
            "deceased_character_stress, and queues death_management.0002; the "
            "latter dispatches death_management.1007 when the recipient is a "
            "close or extended family member in the deceased heir's title-holder "
            "list. This line 695 dispatch is the only exact-build event caller; "
            "the FP2 occurrence reuses localization only"
        ),
        "duplicate_blocker_boundary": (
            "the source-authored three-day blocker suppresses a duplicate notice "
            "for the same recipient and deceased character; it is not a campaign "
            "occurrence ceiling"
        ),
        "trigger_boundary": (
            "the notification itself requires ROOT to have a current player_heir; "
            "the observed strict frame is the no-killer shape"
        ),
        "immediate_effect": (
            "plays the death music cue; only when a killer scope exists and the "
            "murder is public or known by ROOT does it save the known_killer "
            "boolean value. Neither killer nor known_killer exists in the "
            "observed strict shape"
        ),
        "option_semantics": {
            0: (
                "the sole acknowledgement applies stress_impact with the "
                "minor_stress_impact_gain baseline, exactly twenty before "
                "trait-dependent stress-impact adjustments; it defines no "
                "additional scripted option effect. The inherited "
                "deceased_character_stress value is not read by this event, "
                "and unlike death_management.1001 this event does not save the "
                "deceased character for a mental-break follow-up"
            ),
        },
        "after_effect": (
            "display-only custom tooltip: the killed tooltip when known_killer "
            "exists, otherwise the ordinary heir-death tooltip; it mutates no "
            "game state"
        ),
        "strict_shape_boundary": (
            "killer/known_killer scopes and missing new_memory are intentionally "
            "not generalized from source possibilities; either future live "
            "variant must remain RED for exact-build review"
        ),
        "repeatability": (
            "the chain is dispatched independently for each qualifying heir "
            "death and defines no campaign-global one-shot flag or cooldown; "
            "generic stress-threshold consequences are resolved by the common "
            "stress system rather than authored as this event's follow-up"
        ),
        "safe_option_rationale": (
            "the source renders one option only, so authored option 1/native 0 "
            "is the sole terminal route and carries the unavoidable authored "
            "stress impact"
        ),
    },
}


VANILLA_DEATH_MANAGEMENT_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "death_management.1007": {
        "exemplars": [{
            "run": "R374",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "death-management-1007-red-report.json"
            ),
            "artifact_sha256": (
                "B69243825168B01F11C0CBDEBC321C277E3AC22CEEC2F50650ABB9C0994D1D64"
            ),
            "park_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "hot-recovery-park-7.json"
            ),
            "park_artifact_sha256": (
                "A2E63CF1EBB67ADB0987F9360B023E1F0F4659242EE048D51A8CA1219674DEE6"
            ),
            "driver_state_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "driver-state-park-7-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "8702894C65AAF57E0D943C7BAA2FC4D613E4D8C5BDDFC2E4C70DB165C774A5C6"
            ),
            "date_raw": 53590464,
            "event_instance_id": 1046,
            "root_character_id": 32904,
            "saved_character_ids": {
                "dead_character": 39246,
            },
            "saved_scope_raw_types": {
                "new_memory": 34,
                "dead_character": 4,
                "deceased_character_stress": 1,
            },
            "rendered_native_option_indices": [0],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 51852,
            "snapshot_id": "native:1779",
            "revision": 1780,
            "remaining_game_days": 1893,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_DEATH_MANAGEMENT_ANALYSIS",
    "VANILLA_DEATH_MANAGEMENT_OBSERVATIONS",
    "VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS",
]
