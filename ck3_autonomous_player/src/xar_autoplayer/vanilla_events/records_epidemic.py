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
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_EPIDEMIC_ANALYSIS",
    "VANILLA_EPIDEMIC_OBSERVATIONS",
    "VANILLA_EPIDEMIC_TIMELINE_CONTRACTS",
]
