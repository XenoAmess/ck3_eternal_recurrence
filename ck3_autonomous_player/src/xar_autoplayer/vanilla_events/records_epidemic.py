"""Reusable CK3 1.19.0.6 records for vanilla epidemic story events."""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_EPIDEMIC_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "epidemic_events.1064": {
        # The current high-piety projection exposes the learning-duel route.
        # Even its failure is narrower than the unconditional third route,
        # while the second route permanently removes county development.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "story": "story",
            "story_scope": "story",
            "epidemic_scope": "epidemic",
            "trait_blamed": "trait",
            "witch_trial_county": "landed_title",
        },
        "saved_scope_name_sets": ((
            "story",
            "story_scope",
            "epidemic_scope",
            "trait_blamed",
            "witch_trial_county",
        ),),
        "saved_scope_count": 5,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_EPIDEMIC_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "epidemic_events.0110": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/ce1/epidemic_events.txt": (
                "FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E"
            ),
            "common/scripted_effects/06_dlc_ce1_epidemics_effects.txt": (
                "0E27972D9F66348E462130F1EF0351BB18A4C646DB6E23DB237D79068E65DE98"
            ),
            "common/epidemics/00_epidemics.txt": (
                "090607AC30E86817A709A6A8F5F2B5FC785AF11C352873B823CF2C3AA5A77E7F"
            ),
            "common/script_values/06_ce1_epidemics_values.txt": (
                "D462C424C6E2BDDDC042E91D3B1B95F1EF6C39DFCEC252FD69E5FCB5B79FA837"
            ),
            "localization/simp_chinese/dlc/ce1/"
            "ce1_epidemic_events_l_simp_chinese.yml": (
                "09544A655713B856D5ADD0DF35F7276D6F2EA246CF1EEE224D4C5D8807103A79"
            ),
        },
        "definition_lines": "151-413",
        "trigger_lines": "169-188",
        "immediate_lines": "190-259",
        "option_lines": "261-408",
        "after_lines": "410-412",
        "direct_caller_lines": "854-885",
        "epidemic_caller_lines": (
            "314",
            "771",
            "1146",
            "1563",
            "1944",
            "2278",
            "2697",
        ),
        "direct_caller": (
            "all seven vanilla epidemic types invoke "
            "plague_recovery_event_effect from on_province_recovered; it "
            "records the recovered county on county.holder.liege, records "
            "that liege on scope:epidemic, then schedules "
            "epidemic_events.0110 after one day for each alive unflagged "
            "liege and applies a ten-day notification flag"
        ),
        "trigger_boundary": (
            "the event requires epidemic, no currently infected sub-realm "
            "county, no already chosen preferred capital, a nonempty "
            "formerly_infected_counties list, and no two-year recovery "
            "cooldown unless the epidemic is apocalyptic bubonic plague"
        ),
        "scope_boundary": (
            "epidemic is always inherited; new_preferred_capital is optional "
            "because immediate saves it only for a kingdom-or-higher ruler "
            "when an eligible formerly infected non-capital duchy capital is "
            "found. R334 observed both scopes and R375 observed epidemic only"
        ),
        "immediate_effect": (
            "sets the two-year recovery cooldown and, when eligible, chooses "
            "a development-weighted duchy capital, saves it as "
            "new_preferred_capital and marks it chosen for two years"
        ),
        "option_semantics": {
            0: (
                "shown only to a human with new_preferred_capital and a "
                "major-or-worse epidemic; spends recovery plus minor treasury "
                "or gold, transfers the county if needed, moves the capital, "
                "and applies the strongest capital-specific recovery"
            ),
            1: (
                "spends epidemic_fromdust_value for apocalyptic or major "
                "recovery, or half that value for a smaller epidemic, then "
                "applies the corresponding strong, medium or minor five-year "
                "county recovery modifier"
            ),
            2: (
                "spends nothing and applies minor recovery for major-or-worse "
                "epidemics or tiny recovery otherwise; when legitimacy exists "
                "it also applies miniscule_legitimacy_loss"
            ),
        },
        "after_effect": "clears the formerly_infected_counties variable list",
        "repeatability": (
            "the seven independent epidemic recovery callers and this event "
            "define no one-shot flag; ordinary recurrence is gated for two "
            "years, while apocalyptic bubonic plague bypasses that cooldown"
        ),
        "safe_option_rationale": (
            "authored option 3/native 2 avoids every treasury or gold cost, "
            "capital move and title transfer; the accepted weaker recovery "
            "and possible miniscule legitimacy loss are bounded and terminal"
        ),
        "unreviewed_projection_boundary": (
            "source permits native tuple (0, 1, 2) when the optional capital "
            "exists and the epidemic is major or worse, but the reusable live "
            "contract admits only the R334/R368/R375-observed tuple (1, 2); "
            "the full projection remains RED until independently observed"
        ),
    },
    "epidemic_events.1064": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/dlc/ce1/epidemic_events.txt": (
                "FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E"
            ),
            "common/on_action/story_cycles/"
            "story_cycle_witch_trial_on_actions.txt": (
                "D8BAFD1F582D4A34E61AFB03CFE5384F9912E1B101614C3E441BA348DAB5992E"
            ),
            "common/story_cycles/ce1_story_cycle_plague_witch_hunt.txt": (
                "AD113CD4280B4A3BEBBD43433E5130321624D6159307EC65525872408917B83E"
            ),
            "common/on_action/ce1_on_actions.txt": (
                "96B42FA1A542836171A2A608B7155A8A80D30B0D8F8D9742EBE8AFF231B85E16"
            ),
            "common/epidemics/00_epidemics.txt": (
                "090607AC30E86817A709A6A8F5F2B5FC785AF11C352873B823CF2C3AA5A77E7F"
            ),
            "common/modifiers/06_ce1_modifiers.txt": (
                "63FEB33C8C5BF825E3D186E841D07235C98D6AED27C47375E495EA832255C52B"
            ),
        },
        "definition_lines": "2738-2914",
        "direct_caller": (
            "ongoing_witch_hunt_events; seven equal-weight entries after the "
            "event-local triggers and cooldowns filter invalid candidates"
        ),
        "frequency_boundary": (
            "the witch-hunt story evaluates its player-event group every "
            "365-600 days with a 50 percent chance; the separate one-day group "
            "only ends the story when its owner becomes unlanded, so this "
            "character event is not a daily event"
        ),
        "story_entry_boundary": (
            "epidemic_events.1060 can create the story from the monthly epidemic "
            "pool, whose chance_of_no_event is 95; the entry event itself has a "
            "fifteen-year cooldown"
        ),
        "trigger_boundary": (
            "the story blames a trait and the ruler has at least one sub-realm "
            "county at development three or above containing the story epidemic"
        ),
        "immediate_effect": (
            "selects one qualifying infected county and saves it as "
            "witch_trial_county without mutating game state"
        ),
        "option_semantics": {
            "0": (
                "high-piety learning duel; success grants medium piety and minor "
                "legitimacy, while failure loses miniscule legitimacy and applies "
                "witch_trials_obstructed to infected counties for ten years"
            ),
            "1": (
                "permanently removes two development and removes one hundred "
                "control from the selected witch_trial_county"
            ),
            "2": (
                "applies witch_trials_obstructed to every infected sub-realm "
                "county for fifteen years, loses miniscule legitimacy, and can "
                "add minor trusting/lazy stress"
            ),
        },
        "modifier_semantics": (
            "witch_trials_obstructed gives county opinion minus twenty-five and "
            "development growth factor minus seventy-five percent"
        ),
        "after_effect": None,
        "repeatability": (
            "the event has a five-year cooldown and no one-shot flag, so a "
            "continuing or later witch-hunt story can select it again"
        ),
        "safe_option_rationale": (
            "in the observed high-piety projection native0 avoids native1's "
            "permanent development loss; even native0 failure applies the same "
            "county modifier as native2 for ten rather than fifteen years, with "
            "the same legitimacy loss and no additional stress"
        ),
        "unreviewed_projection_boundary": (
            "when high piety is absent the valid native tuple is (1, 2), but "
            "neither remaining route globally dominates the other; that shape is "
            "not admitted by this minimal live-backed contract"
        ),
    },
}


VANILLA_EPIDEMIC_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "epidemic_events.0110": {
        "exemplars": [{
            "run": "R334",
            "kind": "pre-selection-live-red",
            "artifact": "_runtime/p2r334endgamesource/report.json",
            "artifact_sha256": (
                "5AD7971BDCC91E97682179242D73445155075C3324261BE169DBC0BA09934E4C"
            ),
            "date_raw": 53208120,
            "event_instance_id": 206,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
                "new_preferred_capital": 5,
            },
            "rendered_native_option_indices": [1, 2],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 204224,
        }, {
            "run": "R368",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p2r368-p3-rehire-guard-live/report.json"
            ),
            "artifact_sha256": (
                "C63C02464DDE0473C3A7943A803D122107C19E36733BBB446FBC6D25AFA724A4"
            ),
            "date_raw": 53343552,
            "event_instance_id": 439,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
                "new_preferred_capital": 5,
            },
            "rendered_native_option_indices": [1, 2],
            "selected_option_number": 3,
            "selected_native_option_index": 2,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 201320,
            "process_restart_required": False,
        }, {
            "run": "R375",
            "kind": "scope-variant-pre-selection-live-red",
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-epidemic-events-0110-red-freeze.json"
            ),
            "artifact_sha256": (
                "1CD3DEC1ED7DB6F3C7DBE8D485DC2B38753F1D7E1D90BD9E8FA99A8ADADC7448"
            ),
            "park_artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "hot-recovery-park-2.json"
            ),
            "park_artifact_sha256": (
                "D2B3CAEF5C3E1F59756DDBF1246251CBDCCF4FDE2DF7C74F256CE574EDA8DC73"
            ),
            "date_raw": 53611320,
            "event_instance_id": 1059,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
            },
            "rendered_native_option_indices": [1, 2],
            "selection_attempted": False,
            "paused": True,
            "connection_generation": 1,
            "bridge_pid": 180544,
            "process_restart_required": False,
        }, {
            "run": "R375",
            "kind": "same-process-hot-recovery-green",
            "production_live_ordinal": 16,
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-live-016-epidemic-events-0110-green.json"
            ),
            "artifact_sha256": (
                "1C96D13A88D9F96575CA6DD78E5E02C0483ECB1ADC09505949868EC387994EEF"
            ),
            "date_raw": 53611320,
            "event_instance_id": 1059,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
            },
            "rendered_native_option_indices": [1, 2],
            "context_query_driver_command_index": 360,
            "selection_driver_command_index": 361,
            "selected_option_number": 3,
            "selected_native_option_index": 2,
            "postcondition_verified": True,
            "starting_snapshot_id": "native:432",
            "ending_snapshot_id": "native:433",
            "ending_revision": 434,
            "connection_generation": 1,
            "bridge_pid": 180544,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
    "epidemic_events.1064": {
        "exemplars": [{
            "run": "R372",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "epidemic-events-1064-red-report.json"
            ),
            "artifact_sha256": (
                "198AF299C3D45D0F5979D61843FD7A6D9B0E0BE76814178C63D578BB78A2AE17"
            ),
            "park_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-11.json"
            ),
            "park_artifact_sha256": (
                "D1AAA5BC7EF52304DBC2155B7E16679346BD4D2EF66728A970A5F4B3BC0AE607"
            ),
            "driver_state_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "driver-state-park-11-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "556C21FE0ED6EB2A4B8EFB1BB54A16ED9E25161A323FA1291A00572ED12484F4"
            ),
            "date_raw": 53486160,
            "event_instance_id": 867,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "story": 17,
                "story_scope": 17,
                "epidemic_scope": 50,
                "trait_blamed": 45,
                "witch_trial_county": 5,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selection_attempted": False,
            "connection_generation": 1,
            "bridge_pid": 28772,
        }, {
            "run": "R372",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "driver-state-park-12-snapshot.json"
            ),
            "artifact_sha256": (
                "9779F9DC345E08F550312B4FB77C45B711BBC6DB91B9591E027CB6601D322940"
            ),
            "event_instance_id": 867,
            "driver_command_index": 2553,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "postcondition_verified": True,
            "connection_generation": 1,
            "bridge_pid": 28772,
            "process_restart_required": False,
        }],
    },
    "epidemic_events.5009": {
        "exemplars": [{
            "run": "R372",
            "kind": "repeat-occurrence-pre-selection-live-red",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "epidemic-events-5009-repeat-red-report.json"
            ),
            "artifact_sha256": (
                "E2CDBE9E37EA73DDFE30AD212618B20852C7CB04D9609A972F49C885D99F4802"
            ),
            "park_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-12.json"
            ),
            "park_artifact_sha256": (
                "CB31FB25CE0E25AB59059123C215F5B9AAB635A4E22A496F146A14ECCFADE175"
            ),
            "driver_state_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "driver-state-park-12-snapshot.json"
            ),
            "driver_state_artifact_sha256": (
                "9779F9DC345E08F550312B4FB77C45B711BBC6DB91B9591E027CB6601D322940"
            ),
            "date_raw": 53487408,
            "event_instance_id": 871,
            "root_character_id": 32904,
            "saved_character_ids": {
                "merchant": 16826033,
                "owner": 16826033,
                "creator": 16826033,
            },
            "rendered_native_option_indices": [1, 2, 3],
            "selection_attempted": False,
            "prior_green_occurrence": {
                "date_raw": 53397816,
                "event_instance_id": 612,
                "selected_option_number": 4,
                "selected_native_option_index": 3,
                "postcondition_verified": True,
            },
            "elapsed_days_since_prior_occurrence": 3733,
            "connection_generation": 1,
            "bridge_pid": 28772,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_EPIDEMIC_ANALYSIS",
    "VANILLA_EPIDEMIC_OBSERVATIONS",
    "VANILLA_EPIDEMIC_TIMELINE_CONTRACTS",
]
