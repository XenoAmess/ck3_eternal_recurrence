"""Reusable CK3 1.19.0.6 records for vanilla faction-demand events.

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


VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "faction_demand.2001": {
        # Refusal preserves the current title/law/roster state and hands the
        # source-authored claimant war to the dedicated war OODA loop.  Leader
        # and claimant may alias because the source explicitly authors that
        # variant; both remain distinct from the player faction target.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "faction_target": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "faction_leader": (PLAYER_SENTINEL,),
            "faction_claimant": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "faction": "faction",
            "faction_leader": "character",
            "faction_target": "character",
            "faction_claimant": "character",
            "faction_targeted_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "faction",
            "faction_leader",
            "faction_target",
            "faction_claimant",
            "faction_targeted_title",
        ),),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "disabled_native_option_indices": (1,),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_FACTION_DEMAND_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "faction_demand.2001": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/factions/faction_demands.txt": (
                "B06241E67B6692F51FCFC6021E4DBE085C9E25A50B9CD08957CBCC9E25AEBEA9"
            ),
            "common/factions/00_factions.txt": (
                "0A47171476811DD16EBD44A7335EAEBD17376FD87E41290F72B5C6785365B276"
            ),
            "common/factions/_factions.info": (
                "FB47457AABE7C7DF78555B4DFBA74B8932DAE468C45EBB2D1381CADDC2B7E019"
            ),
            "common/defines/00_defines.txt": (
                "C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807"
            ),
            "common/scripted_modifiers/00_faction_modifiers.txt": (
                "CD3DAA9DA33C3DFD15934CA30C1B2D7381E0B3968337BF52A7CBC2F9F2237102"
            ),
            "common/script_values/00_faction_values.txt": (
                "4EE4098080B8C4536E74B047801F8715DD5EB0BCDCBAC04A8E3BF563D6555932"
            ),
            "common/on_action/faction_on_actions.txt": (
                "A4E3EDA2F31CB08D29DEAE1A1CDBD89256973A81FC1A1D4DF00D9CF5BBCB68FB"
            ),
            "common/scripted_effects/00_faction_effects.txt": (
                "C8E0B3C57665F775973BC8559166CD1F6414471CA25017800777C3C6466DC5D3"
            ),
            "common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt": (
                "DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83"
            ),
            "common/scripted_effects/00_war_effects.txt": (
                "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"
            ),
            "common/casus_belli_types/00_civil_war.txt": (
                "CFF84009E58F5D6386A6D7501CFF084CB206A542E7D0CFA221ED2CC050A9DA68"
            ),
        },
        "definition_lines": "2039-2277",
        "claimant_faction_lines": "887-1175",
        "demand_dispatch_lines": "992-1026",
        "monthly_faction_abi_lines": "136-143",
        "faction_demand_define_lines": "1084-1089",
        "accepted_on_action_lines": "1-105",
        "rejected_effect_lines": "2021-2035",
        "accept_legitimacy_effect_lines": "372-378",
        "claimant_war_win_effect_lines": "1276-1544",
        "claimant_war_victory_lines": "1091-1127",
        "caller_semantics": (
            "an active claimant faction saves itself, its leader, target, "
            "claimant, and targeted title when pressing its demand, then queues "
            "this letter on the faction target after five days"
        ),
        "frequency_boundary": (
            "faction ai_demand_chance is checked once per month after the "
            "faction reaches the source-defined power and discontent gates; "
            "MAX_DEMAND_DELAY_DAYS guarantees a later update after at most "
            "ninety eligible days, while the event itself defines no daily "
            "pulse, cooldown, or campaign occurrence ceiling"
        ),
        "trigger_boundary": (
            "the delayed letter requires the saved faction still to exist; "
            "the source explicitly supports either a separate claimant or the "
            "faction leader as claimant, while both roles remain distinct from "
            "the player faction target"
        ),
        "immediate_effect": (
            "aliases ROOT as faction_target for localization and stores the "
            "saved faction_claimant in ROOT's claimant_faction_sent_demand "
            "variable until the event after block removes it"
        ),
        "option_semantics": {
            0: (
                "accepts the faction demand: fires on_faction_demand_accepted, "
                "applies medium_dread_loss and the conditional minor legitimacy "
                "loss, notifies faction members, builds the affected title list, "
                "and runs the claimant-faction war-win common outcome immediately; "
                "that outcome performs the claimant title/vassal transfer and its "
                "source-authored opinion, hook, roster, prisoner, and related "
                "succession side effects"
            ),
            1: (
                "offers co-emperorship only when its law, diarchy, and identity "
                "triggers allow it; the displayed consequences are random between "
                "the counter-offer acceptance flow and the same faction-war "
                "rejection flow, and the actual answer is delegated to "
                "faction_demand.2006. It is shown but disabled in the R374 frame"
            ),
            2: (
                "fires on_faction_demand_rejected and the claimant rejection "
                "effect, which starts the source-authored claimant faction war and "
                "spawns the faction member county armies, then notifies the leader "
                "through faction_demand.2003"
            ),
        },
        "after_effect": (
            "removes ROOT's temporary claimant_faction_sent_demand variable"
        ),
        "war_ooda_boundary": (
            "native option 2 intentionally does not predict or resolve the war; "
            "after the source starts it, campaign observation and all subsequent "
            "military choices belong to the reusable war OODA capabilities"
        ),
        "religion_scope_boundary": (
            "the claimant civil-war victory tail can apply Mandala decree piety "
            "effects, but that is a conditional war-resolution side effect; this "
            "record does not infer or expand a general faith or religion policy"
        ),
        "repeatability": (
            "a particular faction is destroyed or resolved by its outcome, but "
            "other claimant factions and later faction cycles can issue this event; "
            "there is no event-global one-shot flag"
        ),
        "safe_option_rationale": (
            "native option 2 preserves the player's current title, law, and roster "
            "instead of immediately applying the accept-side claimant transfer and "
            "dread/legitimacy losses; unlike the currently disabled bribe, it is "
            "available and deterministic at the event boundary, and delegates its "
            "source-authored war to the dedicated war OODA loop"
        ),
    },
}


VANILLA_FACTION_DEMAND_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "faction_demand.2001": {
        "exemplars": [{
            "run": "R374",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "faction-demand-2001-red-report.json"
            ),
            "artifact_sha256": (
                "AC7EF0A37844A7F0B252917DAB0922B77721F0CAE6FB2A7416BC0F4420BCF9CA"
            ),
            "park_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "hot-recovery-park-8.json"
            ),
            "park_artifact_sha256": (
                "89B4F2F8F6ADD2243C0CAD803766EB6B82491D0EF8E3C3BCCC6B55E5BC41B561"
            ),
            "driver_state_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "driver-state-park-8-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "FDFD7C0B2AB7DF6DC936B9FC01D611F1F5425BA6E571CBB74942BF08A68A9F28"
            ),
            "date_raw": 53595360,
            "event_instance_id": 1050,
            "root_character_id": 32904,
            "saved_character_ids": {
                "faction_leader": 50355542,
                "faction_target": 32904,
                "faction_claimant": 39232,
            },
            "saved_scope_raw_types": {
                "faction": 25,
                "faction_leader": 4,
                "faction_target": 4,
                "faction_claimant": 4,
                "faction_targeted_title": 5,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "disabled_native_option_indices": [1],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 51852,
            "snapshot_id": "native:1847",
            "revision": 1848,
            "remaining_game_days": 1689,
            "process_restart_required": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_FACTION_DEMAND_ANALYSIS",
    "VANILLA_FACTION_DEMAND_OBSERVATIONS",
    "VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS",
]
