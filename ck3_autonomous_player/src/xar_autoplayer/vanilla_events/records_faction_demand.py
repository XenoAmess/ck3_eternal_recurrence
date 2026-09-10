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
    "faction_demand.0099": {
        # An affected vassal is only being asked whether to join the already
        # active populist war.  Authored option 3 (native 2) takes no side, so
        # it avoids conversion and avoids adding the player to either army.
        # Option 1 is conditional; bind both exact rendered projections while
        # retaining the source-authored three-slot snapshot shape.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "faction_target": (PLAYER_SENTINEL,),
            "peasant_leader": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "faction": "faction",
            "peasant_county": "landed_title",
            "faction_target": "character",
            "target_title": "landed_title",
            "peasant_leader": "character",
            "populist_war": "war",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "faction",
            "peasant_county",
            "faction_target",
            "target_title",
            "peasant_leader",
            "populist_war",
        ),),
        "saved_scope_count": 6,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": ({
            "option_count": 2,
            "snapshot_option_count": 3,
            "native_option_indices": (1, 2),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }, {
            "option_count": 3,
            "snapshot_option_count": 3,
            "native_option_indices": (0, 1, 2),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "faction_demand.1101": {
        # Accepting is the bounded product route: it avoids immediately
        # starting a peasant war and leaves any later faction lifecycle to a
        # fresh observation.  The two title scopes intentionally remain typed
        # but identity-free because the bridge does not yet publish portable
        # landed-title identities.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "peasant_leader": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "faction": "faction",
            "peasant_county": "landed_title",
            "peasant_leader": "character",
            "new_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "faction",
            "peasant_county",
            "peasant_leader",
            "new_title",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
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
    "faction_demand.0099": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/factions/faction_demands.txt": (
                "B06241E67B6692F51FCFC6021E4DBE085C9E25A50B9CD08957CBCC9E25AEBEA9"
            ),
        },
        "definition_lines": "1466-1765",
        "caller_lines": "1382-1393",
        "caller_semantics": (
            "after a populist demand is refused and its war starts, every "
            "affected vassal receives this letter and chooses a side"
        ),
        "trigger_boundary": (
            "the saved faction and peasant leader must still exist, and the "
            "leader must remain a member of that faction"
        ),
        "immediate_effect": (
            "saves the faction's already-active war as populist_war"
        ),
        "option_semantics": {
            0: (
                "conditionally adopts the peasant leader's culture and faith, "
                "pays the authored prestige/piety-level penalties, and joins "
                "the attacking side"
            ),
            1: "joins the defending side alongside the current liege",
            2: "takes no side and applies no scripted state mutation",
        },
        "after_effect": None,
        "war_ooda_boundary": (
            "native option 2 leaves the already-active populist war to its "
            "existing participants and creates no new military commitment for "
            "the player"
        ),
        "religion_scope_boundary": (
            "faith only gates and supplies the explicitly rejected conversion "
            "route; selecting no side does not inspect or change faith policy"
        ),
        "repeatability": (
            "each affected vassal receives its own occurrence, and later "
            "populist wars can generate new occurrences"
        ),
        "safe_option_rationale": (
            "native option 2 is the source-authored no-op route: it avoids "
            "culture/faith conversion and avoids joining either war side"
        ),
    },
    "faction_demand.1101": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/factions/faction_demands.txt": (
                "B06241E67B6692F51FCFC6021E4DBE085C9E25A50B9CD08957CBCC9E25AEBEA9"
            ),
            "common/factions/00_peasant_faction_new.txt": (
                "3B54AA8E610EC8F767B86F33F75A7D90A64FA199B0AC1AE37D59A476B4EC04E2"
            ),
            "common/factions/_factions.info": (
                "FB47457AABE7C7DF78555B4DFBA74B8932DAE468C45EBB2D1381CADDC2B7E019"
            ),
            "common/defines/00_defines.txt": (
                "C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807"
            ),
            "common/scripted_effects/00_faction_effects.txt": (
                "C8E0B3C57665F775973BC8559166CD1F6414471CA25017800777C3C6466DC5D3"
            ),
            "common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt": (
                "DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83"
            ),
            "common/script_values/00_faction_values.txt": (
                "4EE4098080B8C4536E74B047801F8715DD5EB0BCDCBAC04A8E3BF563D6555932"
            ),
            "common/script_values/00_legitimacy_values.txt": (
                "13E43166356B5DD99358F435330B03CB9BE95AB5913280318B01681186E23A2E"
            ),
            "common/casus_belli_types/00_peasant_war_new.txt": (
                "3429D8884AA45F09291B807B6931D7FCAA629458ECCEE59AE2EA682D69F46AAF"
            ),
        },
        "definition_lines": "1816-1925",
        "peasant_faction_lines": "1-105, 107-162, 362-620, 626-732",
        "demand_dispatch_lines": "69-105",
        "monthly_faction_abi_lines": "136-143",
        "faction_demand_define_lines": "1084-1088",
        "enforced_effect_lines": "1617-1751",
        "leader_setup_effect_lines": "2023-2117",
        "army_spawn_effect_lines": "2119-2144",
        "accept_legitimacy_effect_lines": "372-378",
        "faction_war_legitimacy_effect_lines": "288-354",
        "legitimacy_value_lines": "171-188",
        "peasant_war_lines": "1-240",
        "caller_semantics": (
            "an eligible peasant faction saves itself, creates or reuses its "
            "peasant leader and temporary duchy title, then synchronously "
            "triggers this letter on the faction target"
        ),
        "frequency_boundary": (
            "peasant-faction ai_demand_chance is checked once per month after "
            "the source-defined discontent gate; it is normally enabled by any "
            "county member but suppressed while the target hosts a coronation. "
            "MAX_DEMAND_DELAY_DAYS guarantees a later update after at most "
            "ninety eligible days, while the event defines no daily pulse, "
            "cooldown, or campaign occurrence ceiling"
        ),
        "trigger_boundary": (
            "the letter remains valid only while the saved faction and peasant "
            "leader exist and the leader is still joined to that faction"
        ),
        "immediate_effect": None,
        "option_semantics": {
            0: (
                "accepts the demand, applying the conditional minor legitimacy "
                "loss of fifty. For a top-liege target it removes seventy-five "
                "county control, applies peasant_war_lost_county_modifier for "
                "ten years, cleans revolt modifiers, and destroys the faction; "
                "a Dynastic Cycle demand against a lower liege instead promotes "
                "the counties and leader into an escalated faction against the "
                "top liege"
            ),
            1: (
                "immediately starts the source-authored peasant war, removes "
                "twenty-five control from every member county, and spawns its "
                "county armies under the peasant leader; the peasant-war "
                "declaration separately applies the conditional medium "
                "legitimacy loss of one hundred"
            ),
        },
        "after_effect": None,
        "war_ooda_boundary": (
            "the selected native option 0 does not start a war at this event "
            "boundary; if a later escalated faction or another source starts "
            "one, campaign observation and military choices belong to the "
            "reusable war OODA capabilities"
        ),
        "religion_scope_boundary": (
            "leader setup copies the peasant county's faith and a refused war "
            "can later evaluate culture-faith struggle catalysts and Mandala "
            "effects; those are source-authored setup or war side effects, not "
            "a general faith-policy input for this event choice"
        ),
        "repeatability": (
            "acceptance destroys or escalates the current faction and refusal "
            "starts its war, but later peasant factions can independently press "
            "the same demand because there is no event-global one-shot flag"
        ),
        "safe_option_rationale": (
            "native option 0 is the bounded product route in the observed frame: "
            "it avoids native1's immediate peasant war, army spawn, twenty-five "
            "control loss, and additional one-hundred legitimacy loss. Its "
            "source-authored enforcement or escalation remains explicit rather "
            "than being mistaken for a universally cost-free choice"
        ),
    },
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
    "faction_demand.0099": {
        "exemplars": [{
            "run": "R406",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p1-terminal-stages-mcp-20260911/live-artifacts/"
                "terminal-stages-red.json"
            ),
            "artifact_sha256": (
                "0566A837947FE94EE0F90F09435F8F8AFABC7E55462732368578B6A6C2ACC085"
            ),
            "date_raw": 54001392,
            "event_instance_id": 2152,
            "root_character_id": 33596113,
            "saved_character_ids": {
                "faction_target": 16863885,
                "peasant_leader": 117494968,
            },
            "saved_scope_raw_types": {
                "faction": 25,
                "peasant_county": 5,
                "faction_target": 4,
                "target_title": 5,
                "peasant_leader": 4,
                "populist_war": 16,
            },
            "rendered_native_option_indices": [1, 2],
            "enabled_native_option_indices": [1, 2],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 30984,
            "snapshot_id": "native:175",
            "revision": 176,
            "process_restart_required": False,
        }],
    },
    "faction_demand.1101": {
        "exemplars": [{
            "run": "R374",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "faction-demand-1101-red-report.json"
            ),
            "artifact_sha256": (
                "BA39B64ACC3224E8F1F5D5C04719A04106430D7F2F2551DEC52CCEC514FC3AA6"
            ),
            "park_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "hot-recovery-park-9.json"
            ),
            "park_artifact_sha256": (
                "4E3B59B3EB6328939D2008BD2DD4138546C0224F76D62297D19415138DF577E6"
            ),
            "driver_state_artifact": (
                "_runtime/p2r374-active-boundary-continuation-live/"
                "driver-state-park-9-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "78C84C846ED9D2F05AF153EC9302C4C3A85C645FD0B33316CD212B10E342C494"
            ),
            "date_raw": 53607792,
            "event_instance_id": 1055,
            "root_character_id": 32904,
            "saved_character_ids": {
                "peasant_leader": 33633057,
            },
            "saved_scope_raw_types": {
                "faction": 25,
                "peasant_county": 5,
                "peasant_leader": 4,
                "new_title": 5,
            },
            "rendered_native_option_indices": [0, 1],
            "enabled_native_option_indices": [0, 1],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 51852,
            "snapshot_id": "native:2057",
            "revision": 2058,
            "remaining_game_days": 1171,
            "process_restart_required": False,
        }],
    },
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
