"""Canonical records for source-reviewed vanilla event-contract shards."""

from __future__ import annotations

# Reusable contracts bind the active player through ``$player`` and contain no
# campaign date or character identity. The legacy live bindings removed from
# migrated contracts are retained separately below as observations.

from typing import Final

from .registry import PLAYER_SENTINEL


# Migrated from tools/zg361_phase2_promotion_vanilla_accolade_interrupt_contracts.py.
VANILLA_ACCOLADE_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "ep2_accolade_events.0300": {
        # CK3 1.19.0.6 Master of Revels training result. This root-only frame
        # has no heir trainee and authors exactly one unavoidable option. It
        # grants lifestyle_reveler to new_reveler (root), may reduce stress,
        # and does not dispatch a follow-up event. Bind the acclaimed knight
        # and root trainee before taking that sole terminal route.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "new_reveler": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "master_of_revels": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "master_of_revels": ("new_reveler",),
            "new_reveler": ("master_of_revels",),
        },
        "scope_types": {
            "master_of_revels": "character",
            "new_reveler": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "master_of_revels",
            "new_reveler",
        ),),
        "saved_scope_count": 2,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_admin_eunuch_interrupt_contracts.py.
VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_story_cycle_admin_eunuch.8010": {
        # CK3 1.19.0.6 death transition for an administrative-eunuch story.
        # The first two options replace the deceased eunuch with the saved
        # student or rival. The third option only clears the liege modifier
        # and ends this story, making it the bounded terminal route.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "emperor": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "eunuch": (PLAYER_SENTINEL,),
            "student": (PLAYER_SENTINEL,),
            "rival": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "eunuch": ("student", "rival"),
            "student": ("eunuch", "rival"),
            "rival": ("eunuch", "student"),
        },
        "scope_types": {
            "story": "story",
            "eunuch": "character",
            "emperor": "character",
            "admin_title": "landed_title",
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "story",
            "eunuch",
            "emperor",
            "admin_title",
            "student",
            "rival",
        ),),
        "saved_scope_count": 6,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_diarchy_interrupt_contracts.py.
VANILLA_DIARCHY_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "diarchy.8042": {
        # CK3 1.19.0.6 co-emperor scapegoat-result letter. The interaction
        # applies its actual consequences before dispatch; this event only
        # shows the result as a tooltip. Because root is the recipient, only
        # authored option A is rendered and its body is empty. Bind the exact
        # interaction carry, including unavailable optional participant
        # identities and all four result flags, before acknowledging it.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "recipient": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "actor": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "actor": ("recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {
            "actor": "character",
            "recipient": "character",
        },
        "boolean_scopes": (
            "diplomacy_small",
            "diplomacy_large",
            "intrigue_small",
            "intrigue_large",
        ),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "diplomacy_small",
            "diplomacy_large",
            "intrigue_small",
            "intrigue_large",
        ),),
        "saved_scope_count": 9,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_dynastic_cycle_interrupt_contracts.py.
VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle.0091": {
        # CK3 1.19.0.6 transition notice sent to the current China holder when
        # the dynastic-cycle situation enters Instability. The immediate block
        # has already notified other relevant players; its sole option is an
        # empty acknowledgement. A later dynastic cycle can enter Instability
        # again, so recurrence is bounded by the observation window rather
        # than by one frozen campaign occurrence.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
        ),),
        "saved_scope_count": 2,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_ep1_flavor_interrupt_contracts.py.
VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep1_flavor.1000": {
        # CK3 1.19.0.6 visiting-eunuch offer. Immediate may create a suitable
        # eunuch and selects a neighboring court for an unhired visitor.
        # Native options 0 and 1 hire or negotiate with gameplay/resource
        # consequences. Native option 2 declines, moves the visitor to the
        # already-selected pool court, and terminates without a follow-up.
        # R347b observed this exact three-scope, three-option projection.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "eunuch_target": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "eunuch_target_culture": "culture",
            "eunuch_target": "character",
            "new_court": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "eunuch_target_culture",
            "eunuch_target",
            "new_court",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts.py.
VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_emperor_yearly.2170": {
        # CK3 1.19.0.6 low-control county response. Both authored routes
        # install a 50-year county modifier, so there is no inert dismissal.
        # Route B additionally installs a 25-year character flag that raises
        # governor efficiency by five points. Route A avoids that persistent
        # cross-system character state and only adds influence when the
        # current government exposes that resource. R287 observed the exact
        # one-title/two-option frame on the switched manager lineage.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "our_county": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("our_county",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_emperor_yearly.2211": {
        # CK3 1.19.0.6 response to a vassal's claimed appointment prophecy.
        # Authored option A is hidden in the R250 frame, leaving B/D/C at
        # native indices 1/2/3. R355 has A and D hidden, leaving B/C at 1/3.
        # Those are the two exact vanilla projections for the observed ruler:
        # A/B depend on personality/superstition, while D additionally admits
        # a faith mismatch with the requesting vassal. B creates a favor hook
        # (or grants influence), D installs a 25-year modifier, and both A/B
        # alter appointment investment. Authored option C is the bounded
        # terminal route: it only transfers minor influence in opposite
        # directions and schedules no follow-up event, hook, modifier, or
        # appointment mutation. The .2210 caller saves its dynamic root as
        # vassal before sending .2211 to the liege, so bind that source
        # relation instead of one seed ID. Since independent vassals enter
        # .2210 through the vanilla yearly pool and own its cooldown, multiple
        # requests to the same liege remain valid within the product window.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "vassal": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "potential_title": "landed_title",
            "liege": "character",
            "vassal": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "potential_title",
            "liege",
            "vassal",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 3,
                "native_option_indices": (1, 2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 2,
                "native_option_indices": (1, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_powerful_families.8012": {
        # CK3 1.19.0.6 response to a powerful family's offer to enter the
        # liege's losing war. The .8010 caller binds the offering character,
        # liege, and selected war, then installs a 15-year liege-wide flag.
        # Native0 accepts and adds the offering family to the war; native1
        # declines, grants only minor influence to that family, and schedules
        # no follow-up. R366 observed this exact three-scope/two-option frame.
        # Source SHA-256:
        # CA19D38CD1C45783E32CF59E21A212642EA407B2DDD8EDE2467DF50ED9F7BC7A.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "generous_family": (PLAYER_SENTINEL,),
        },
        "scope_types": {
            "generous_family": "character",
            "liege": "character",
            "war": "war",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("generous_family", "liege", "war"),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_historical_character_interrupt_contracts.py.
VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "historical_char_creation_events.1": {
        # CK3 1.19.0.6 historical-character arrival shown to the player who
        # holds the character's origin county.  The first option switches the
        # played character, while the second recruits the historical figure
        # and creates an obligation hook.  In R372 the third option only
        # grants minor prestige: no explorer scope exists and the player is
        # human, so neither landless-adventurer branch is reachable.
        # `major` is a distinct historical character retained by the vanilla
        # pulse context; the four background scopes are authored immediately
        # before the window is rendered.  Other exact vanilla scope shapes
        # must be reviewed as separate variants when they are observed.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "historical_character": (PLAYER_SENTINEL,),
            "major": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "historical_character": ("major",),
            "major": ("historical_character",),
        },
        "scope_types": {
            "birth_location": "landed_title",
            "historical_character": "character",
            "major": "character",
            "county_scope": "landed_title",
            "background_terrain_scope": "landed_title",
            "background_market_scope": "province",
            "background_university_scope": "province",
            "holy_site_scope": "province",
        },
        "saved_scope_name_sets": ((
            "birth_location",
            "historical_character",
            "major",
            "county_scope",
            "background_terrain_scope",
            "background_market_scope",
            "background_university_scope",
            "holy_site_scope",
        ),),
        "saved_scope_count": 8,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_intrigue_temptation_interrupt_contracts.py.
VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "intrigue_temptation.3020": {
        # CK3 1.19.0.6 common intrigue-lifestyle event. Authored option A
        # scans rulers and their families, then immediately starts the
        # multi-card 3021/3022 romantic-candidate chain. Authored option B is
        # terminal and only adds intrigue_picky_about_partners for five years.
        # R322 observed this exact root/quarter/two-option frame within the
        # product timeline, 48 in-game hours after the last clean observation.
        # Take terminal native1 so the unrelated story cannot occupy the
        # promotion-source timeline.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "quarter": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("quarter",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_natural_disaster_interrupt_contracts.py.
_NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES: Final = (
    "situation",
    "situation_sub_region",
    "situation_participant_group",
    "ruler",
    "disaster_province",
    "disaster_province_ruler",
    "great_project",
    "epicenter_county",
)

_NATURAL_DISASTER_8001_SCOPE_TYPES: Final = {
    "situation": "situation",
    "situation_sub_region": "situation_sub_region",
    "situation_participant_group": "situation_participant_group",
    "disaster_province": "province",
    "great_project": "great_project",
    "epicenter_county": "landed_title",
}

_NATURAL_DISASTER_8001_RIVER_SAVED_SCOPE_NAMES: Final = (
    *_NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES,
    "river_region",
)


VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "natural_disaster.8001": {
        # CK3 1.19.0.6 warning-phase join event.  Its sole authored option
        # invokes only natural_disaster_warning_tooltip_effect, so native0 is
        # the unavoidable acknowledgement and adds no option-side mutation.
        # R247 observed the eight-scope earthquake shape. R355 observed the
        # exact flood sibling, where natural_disaster_save_base_scopes_effect
        # adds river_region from the situation variable. Independent warning
        # situations may legitimately send this event again, so recurrence is
        # bounded by the product observation window rather than a whole-run
        # occurrence count.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "ruler": PLAYER_SENTINEL,
            "disaster_province_ruler": PLAYER_SENTINEL,
        },
        "scope_types": _NATURAL_DISASTER_8001_SCOPE_TYPES,
        "saved_scope_name_sets": (
            _NATURAL_DISASTER_8001_SAVED_SCOPE_NAMES,
        ),
        "saved_scope_count": 8,
        "scope_variants": ({
            "saved_scope_names": (
                _NATURAL_DISASTER_8001_RIVER_SAVED_SCOPE_NAMES
            ),
            "saved_scope_count": 9,
            "scope_types": {
                **_NATURAL_DISASTER_8001_SCOPE_TYPES,
                "river_region": "geographical_region",
            },
        },),
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "natural_disaster.7021": {
        # CK3 1.19.0.6 flood-warning pulse selected by
        # natural_disaster_warning_events. Native option 0 adds stress and
        # enters manage-from-home power sharing; native option 1 opens the
        # isolation decision. Both are hidden once their gates fail. Native
        # option 2 only renders the warning tooltip, while the event's common
        # after block records that the first warning was received. R355 shows
        # the exact first-warning projection with native options (0, 2), so
        # choose terminal native2 and bind the complete flood scope stack.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "epicenter_county": "landed_title",
            "river_region": "geographical_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
            "epicenter_county",
            "river_region",
        ),),
        "saved_scope_count": 4,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "natural_disaster.7031": {
        # CK3 1.19.0.6 great-storm flood warning. This is source-identical to
        # .7021 apart from presentation: native0 enters manage-from-home
        # power sharing, native1 opens the isolation decision, and native2
        # only renders the warning tooltip. The first two routes are
        # trigger-dependent, so preserve every source-valid projection and
        # always choose terminal native2. R374 observed the exact four-scope
        # (0, 2) projection before any selection was attempted.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "epicenter_county": "landed_title",
            "river_region": "geographical_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
            "epicenter_county",
            "river_region",
        ),),
        "saved_scope_count": 4,
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
            {
                "option_count": 1,
                "native_option_indices": (2,),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
            {
                "option_count": 2,
                "native_option_indices": (0, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "natural_disaster.6901": {
        # CK3 1.19.0.6 recovery-phase start notice for each independent
        # affected ruler. natural_disaster_save_base_scopes_effect has already
        # published the exact flood context before the situation dispatches
        # this event. Its sole authored option is empty, so native0 is the
        # unavoidable terminal acknowledgement. Independent disasters may
        # legitimately deliver the event again within the bounded timeline.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "situation": "situation",
            "situation_sub_region": "situation_sub_region",
            "epicenter_county": "landed_title",
            "river_region": "geographical_region",
        },
        "saved_scope_name_sets": ((
            "situation",
            "situation_sub_region",
            "epicenter_county",
            "river_region",
        ),),
        "saved_scope_count": 4,
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "travel_danger_events.3002": {
        # CK3 1.19.0.6 avalanche follow-up letter to the province owner. Route
        # A applies the four-year avalanche_impact province penalty; route B
        # spends minor gold but leaves the province unchanged. Prefer B so a
        # random travel consequence does not distort the long manager-cycle
        # observation. The traveler, optional travel leader, and news bearer
        # are dynamically selected for each avalanche and therefore bind by
        # native type, not one frozen campaign identity.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "travel_plan": "travel_plan",
            "travel_leader": "character",
            "avalanche_traveler": "character",
            "avalanche_location": "province",
            "news_bearer": "character",
        },
        "saved_scope_name_sets": ((
            "travel_plan",
            "travel_leader",
            "avalanche_traveler",
            "avalanche_location",
            "news_bearer",
        ),),
        "saved_scope_count": 5,
        "scope_variants": ({
            # .3001 saves travel_leader through ?=, so an otherwise valid
            # travel plan without a leader legally carries only four scopes.
            "saved_scope_names": (
                "travel_plan",
                "avalanche_traveler",
                "avalanche_location",
                "news_bearer",
            ),
            "saved_scope_count": 4,
            "scope_types": {
                "travel_plan": "travel_plan",
                "avalanche_traveler": "character",
                "avalanche_location": "province",
                "news_bearer": "character",
            },
        },),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # Independent avalanches can notify the same province owner again.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_secret_interrupt_contracts.py.
_VANILLA_SECRET_0122_SAVED_SCOPE_NAMES: Final = (
    "secret_owner",
    "secret_target",
    "secret_exposer",
    "secret",
    "siphoned_treasury_victim",
    "embezzlement_stake",
    "embezzlement_stake_half",
    "embezzler",
    "victim",
    "exposed_secret_target",
    "local_secret_owner",
    "secret_owner_is_vassal",
    "liege",
)

_VANILLA_SECRET_0122_CHARACTER_SCOPES: Final = {
    "secret_target": PLAYER_SENTINEL,
    "siphoned_treasury_victim": PLAYER_SENTINEL,
    "victim": PLAYER_SENTINEL,
    "exposed_secret_target": PLAYER_SENTINEL,
    "liege": PLAYER_SENTINEL,
}


VANILLA_SECRET_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "secrets.0108": {
        # CK3 1.19.0.6 notification that two cared-about characters were
        # exposed as lovers. In this exact frame neither imprisonment option
        # is legal, so authored option A is the sole rendered route and has no
        # option-body effect. Independent exposed secrets can notify the
        # player repeatedly; validate every delivery without a global cap.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {"event_root": PLAYER_SENTINEL},
        "unique_character_scope_excludes": {
            name: (PLAYER_SENTINEL,)
            for name in (
                "secret_owner",
                "secret_target",
                "secret_exposer",
                "target",
                "owner",
                "local_secret_owner",
                "sex_partner",
                "adulterer_check",
                "primary_character",
                "secondary_character",
                "left_portrait",
                "right_portrait",
            )
        },
        "character_scope_matches_any": {
            "secret_exposer": ("secret_owner",),
            "owner": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
            "adulterer_check": ("secret_owner",),
            "primary_character": ("secret_owner",),
            "left_portrait": ("secret_owner",),
            "target": ("secret_target",),
            "sex_partner": ("secret_target",),
            "secondary_character": ("secret_target",),
            "right_portrait": ("secret_target",),
        },
        "character_scope_differs_from": {
            "secret_owner": ("secret_target",),
            "secret_target": ("secret_owner",),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_target": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "target": "character",
            "owner": "character",
            "local_secret_owner": "character",
            "sex_partner": "character",
            "adulterer_check": "character",
            "targets_secret": "secret",
            "event_root": "character",
            "primary_character": "character",
            "secondary_character": "character",
            "lover_reaction": "flag",
            "left_portrait": "character",
            "right_portrait": "character",
        },
        "saved_scope_name_sets": ((
            "secret_owner", "secret_target", "secret_exposer", "secret",
            "target", "owner", "local_secret_owner", "sex_partner",
            "adulterer_check", "targets_secret", "event_root",
            "primary_character", "secondary_character", "lover_reaction",
            "left_portrait", "right_portrait",
        ),),
        "boolean_scopes": (),
        "saved_scope_count": 16,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            # R369 observed exposure by a third party. Vanilla creates an
            # infidelity-confrontation story before dispatching the general
            # notification, so that story remains in the event scope. The
            # third-party exposer owns the left portrait, while target and
            # owner become the primary/right and secondary/lower-right pairs.
            "saved_scope_names": (
                "secret_owner", "secret_target", "secret_exposer", "secret",
                "target", "owner", "infidelity_story", "targets_secret",
                "event_root", "primary_character", "secondary_character",
                "lover_reaction", "left_portrait", "right_portrait",
                "lower_right_portrait",
            ),
            "unique_character_scope_excludes": {
                name: (PLAYER_SENTINEL,)
                for name in (
                    "secret_owner", "secret_target", "secret_exposer",
                    "target", "owner", "primary_character",
                    "secondary_character", "left_portrait",
                    "right_portrait", "lower_right_portrait",
                )
            },
            "character_scope_matches_any": {
                "owner": ("secret_owner",),
                "target": ("secret_target",),
                "primary_character": ("secret_owner", "secret_target"),
                "secondary_character": ("secret_owner", "secret_target"),
                "left_portrait": ("secret_exposer",),
                "right_portrait": ("primary_character",),
                "lower_right_portrait": ("secondary_character",),
            },
            "character_scope_differs_from": {
                "secret_owner": ("secret_target", "secret_exposer"),
                "secret_target": ("secret_owner", "secret_exposer"),
                "secret_exposer": ("secret_owner", "secret_target"),
                "primary_character": ("secondary_character",),
                "secondary_character": ("primary_character",),
            },
            "scope_types": {
                "secret_owner": "character",
                "secret_target": "character",
                "secret_exposer": "character",
                "secret": "secret",
                "target": "character",
                "owner": "character",
                "infidelity_story": "story",
                "targets_secret": "secret",
                "event_root": "character",
                "primary_character": "character",
                "secondary_character": "character",
                "lover_reaction": "flag",
                "left_portrait": "character",
                "right_portrait": "character",
                "lower_right_portrait": "character",
            },
            "saved_scope_count": 15,
        },),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "secrets.0112": {
        # CK3 1.19.0.6 notification that a cared-about character was exposed
        # as an illegitimate child or parent. In the reviewed non-consort
        # frame the only rendered route is authored option A, whose option
        # body is empty; the secret type applied gameplay consequences before
        # dispatching this notification. Independent secrets can produce it any
        # number of times, so each delivery is revalidated without a cap.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            name: (PLAYER_SENTINEL,)
            for name in (
                "secret_owner",
                "secret_target",
                "secret_exposer",
                "owner",
                "child",
                "mother",
                "real_father",
                "local_secret_owner",
                "target",
            )
        },
        "character_scope_matches_any": {
            "owner": ("secret_owner",),
            "mother": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
            "child": ("secret_target",),
            "target": ("secret_target",),
            "real_father": ("secret_exposer",),
        },
        "character_scope_differs_from": {
            "secret_owner": ("secret_target", "secret_exposer"),
            "secret_target": ("secret_owner", "secret_exposer"),
            "secret_exposer": ("secret_owner", "secret_target"),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_target": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "owner": "character",
            "child": "character",
            "mother": "character",
            "real_father": "character",
            "local_secret_owner": "character",
            "lover_secret_to_expose": "secret",
            "target": "character",
        },
        "saved_scope_name_sets": ((
            "secret_owner",
            "secret_target",
            "secret_exposer",
            "secret",
            "owner",
            "child",
            "mother",
            "real_father",
            "local_secret_owner",
            "lover_secret_to_expose",
            "target",
        ),),
        "boolean_scopes": (),
        "saved_scope_count": 11,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            # R370 observed the same bastardy notification after vanilla's
            # adultery-consequence chain had retained its working character
            # scopes.  The notification itself still renders only authored
            # option A; preserve the exact extra shape and its authored alias
            # relationships instead of weakening the original 11-scope case.
            "saved_scope_names": (
                "secret_owner", "secret_target", "secret_exposer", "secret",
                "owner", "child", "mother", "real_father",
                "local_secret_owner", "sex_partner", "adulterer_check",
                "adultery_spouse", "this_character", "fornicator_check",
                "sex_partner_spouse", "target",
            ),
            "unique_character_scope_excludes": {
                name: (PLAYER_SENTINEL,)
                for name in (
                    "secret_owner", "secret_target", "secret_exposer",
                    "owner", "child", "mother", "real_father",
                    "local_secret_owner", "target",
                )
            },
            "character_scope_matches_any": {
                "owner": ("secret_owner",),
                "mother": ("secret_owner",),
                "local_secret_owner": ("secret_owner",),
                "fornicator_check": ("secret_owner",),
                "child": ("secret_target",),
                "target": ("secret_target",),
                "real_father": ("secret_exposer",),
                "sex_partner": ("secret_exposer",),
                "adulterer_check": ("secret_exposer",),
                "adultery_spouse": ("secret_exposer",),
                "this_character": ("secret_exposer",),
            },
            "character_scope_differs_from": {
                "secret_owner": ("secret_target", "secret_exposer"),
                "secret_target": ("secret_owner", "secret_exposer"),
                "secret_exposer": ("secret_owner", "secret_target"),
                # Vanilla's every_spouse loop explicitly excludes the
                # current sex_character; a spouse also cannot be itself.
                "sex_partner_spouse": ("secret_owner", "sex_partner"),
            },
            "scope_types": {
                "secret_owner": "character",
                "secret_target": "character",
                "secret_exposer": "character",
                "secret": "secret",
                "owner": "character",
                "child": "character",
                "mother": "character",
                "real_father": "character",
                "local_secret_owner": "character",
                "sex_partner": "character",
                "adulterer_check": "character",
                "adultery_spouse": "character",
                "this_character": "character",
                "fornicator_check": "character",
                "sex_partner_spouse": "character",
                "target": "character",
            },
            "saved_scope_count": 16,
        },),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "secrets.0122": {
        # CK3 1.19.0.6 embezzlement exposure. R231 and R290 prove that the
        # embezzler is the current secret owner rather than one stable seed
        # character. The secret type saves ``embezzler`` from secret_owner,
        # while secret_exposed_owner_effects_effect saves
        # ``local_secret_owner`` from the same source. Bind those authored
        # aliases instead of either incidental character ID. R231 rendered
        # authored options B/C only: B imprisons the embezzler, while C
        # forgives them with a 20-opinion effect and trait-dependent stress.
        # Select authored C as the terminal route with the smallest unrelated
        # realm mutation. Each independently exposed siphoned-treasury secret
        # can notify its victim through 0121 -> 0122; vanilla has no global
        # one-shot gate, so validate every later delivery with this same frame.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": _VANILLA_SECRET_0122_CHARACTER_SCOPES,
        "unique_character_scope_excludes": {
            "secret_owner": (PLAYER_SENTINEL,),
            "secret_exposer": (),
            "embezzler": (PLAYER_SENTINEL,),
            "local_secret_owner": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "embezzler": ("secret_owner",),
            "local_secret_owner": ("secret_owner",),
        },
        "scope_types": {
            "secret_owner": "character",
            "secret_exposer": "character",
            "secret": "secret",
            "embezzlement_stake": "value",
            "embezzlement_stake_half": "value",
            "embezzler": "character",
            "local_secret_owner": "character",
            "secret_owner_is_vassal": "flag",
        },
        "saved_scope_name_sets": (_VANILLA_SECRET_0122_SAVED_SCOPE_NAMES,),
        "boolean_scopes": (),
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_vanilla_seduce_interrupt_contracts.py.
VANILLA_SEDUCE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "seduce_outcome.4900": {
        # R328 observed the target liege's mandatory notification after an
        # unrelated courtier's failed seduction. CK3 1.19.0.6 authors exactly
        # one option; it applies the already-determined publicised-crime
        # outcome and offers no alternative branch. Bind the complete saved
        # scope set before acknowledging that sole terminal option.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "target_liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "owner": (PLAYER_SENTINEL,),
            "target": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "target_liege"),
            "target": ("owner", "target_liege"),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "ignore_cheating_error_check": "boolean",
            "discovery_chance": "value",
            "scheme_discovered": "boolean",
            "target_liege": "character",
        },
        "boolean_scopes": (
            "ignore_cheating_error_check",
            "scheme_discovered",
        ),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "ignore_cheating_error_check",
            "discovery_chance",
            "scheme_discovered",
            "target_liege",
        ),),
        "saved_scope_count": 8,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "seduce_outcome.3901": {
        # CK3 1.19.0.6 target-liege discovery event. seduce_outcome.2900
        # sends this event to target.liege after the seduction succeeds and
        # discovery is important to that liege. Its only authored option
        # applies seduce_outcome_success_discovered_effect to the target, so
        # there is no inert alternative. R355 observed the played liege as
        # root with the exact inherited scheme stack plus the capital and the
        # immediate block's dummy servant. The servant is a valid character
        # scope whose bridge identity is intentionally unavailable. Each
        # independent discovered seduction may send this notification, so it
        # is repeatable inside the bounded product observation window.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "target_liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "owner": (PLAYER_SENTINEL,),
            "target": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "target_liege"),
            "target": ("owner", "target_liege"),
        },
        "unavailable_character_scopes": ("dummy_servant_gender",),
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "ignore_cheating_error_check": "boolean",
            "scheme_successful": "boolean",
            "discovery_chance": "value",
            "scheme_discovered": "boolean",
            "target_liege": "character",
            "capital": "landed_title",
            "dummy_servant_gender": "character",
        },
        "boolean_scopes": (
            "ignore_cheating_error_check",
            "scheme_successful",
            "scheme_discovered",
        ),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "ignore_cheating_error_check",
            "scheme_successful",
            "discovery_chance",
            "scheme_discovered",
            "target_liege",
            "capital",
            "dummy_servant_gender",
        ),),
        "saved_scope_count": 11,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


_VANILLA_SHARD_GROUPS: Final[
    tuple[dict[str, dict[str, object]], ...]
] = (
    VANILLA_ACCOLADE_TIMELINE_CONTRACTS,
    VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS,
    VANILLA_DIARCHY_TIMELINE_CONTRACTS,
    VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
    VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS,
    VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS,
    VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS,
    VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS,
    VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS,
    VANILLA_SECRET_TIMELINE_CONTRACTS,
    VANILLA_SEDUCE_TIMELINE_CONTRACTS,
)


def _aggregate_vanilla_shards(
    groups: tuple[dict[str, dict[str, object]], ...],
) -> dict[str, dict[str, object]]:
    aggregate: dict[str, dict[str, object]] = {}
    for group in groups:
        duplicate_keys = set(aggregate).intersection(group)
        if duplicate_keys:
            raise AssertionError(
                "duplicate vanilla shard event keys: "
                f"{sorted(duplicate_keys)}"
            )
        aggregate.update(group)
    return aggregate


VANILLA_SHARD_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = (
    _aggregate_vanilla_shards(_VANILLA_SHARD_GROUPS)
)


# The shared observation aggregator imports this package during serial
# integration. Keeping the evidence next to the contracts makes the removed
# values reviewable without constraining a future game, operator, or machine.
VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle.0091": {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "date_raw": 53436024,
            "root_character_id": 32904,
        }],
    },
    "ep3_emperor_yearly.2170": {
        "exemplars": [{
            "run": "R287",
            "kind": "legacy-live-binding",
            "date_raw": 53205336,
            "root_character_id": 32904,
        }],
    },
    "ep3_emperor_yearly.2211": {
        "exemplars": [{
            "run": "R250",
            "kind": "legacy-live-binding",
            "date_raw": 53206512,
            "root_character_id": 32904,
            "saved_character_ids": {"liege": 32904},
        }],
    },
    "ep3_powerful_families.8012": {
        "exemplars": [{
            "run": "R366",
            "kind": "legacy-live-binding",
            "date_raw": 53328600,
            "root_character_id": 32904,
            "saved_character_ids": {"liege": 32904},
        }],
    },
    "historical_char_creation_events.1": {
        "exemplars": [{
            "run": "R372",
            "kind": "legacy-live-binding",
            "date_raw": 53436024,
            "root_character_id": 32904,
        }],
    },
    "intrigue_temptation.3020": {
        "exemplars": [{
            "run": "R322",
            "kind": "legacy-live-binding",
            "date_raw": 53170824,
            "root_character_id": 29037,
        }],
    },
    "natural_disaster.8001": {
        "exemplars": [{
            "run": "R247",
            "kind": "legacy-live-binding",
            "date_raw": 53204688,
            "root_character_id": 32904,
            "saved_character_ids": {
                "ruler": 32904,
                "disaster_province_ruler": 32904,
            },
        }],
    },
    "natural_disaster.7021": {
        "exemplars": [{
            "run": "R355",
            "kind": "legacy-live-binding",
            "date_raw": 53255112,
            "root_character_id": 32904,
        }],
    },
    "natural_disaster.6901": {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "date_raw": 53256312,
            "root_character_id": 32904,
        }],
    },
    "travel_danger_events.3002": {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "date_raw": 53373936,
            "root_character_id": 32904,
        }],
    },
}


# Package B retains every campaign-specific field removed from the reusable
# contracts. These exemplars are evidence only; they must never be used as
# portable matching constraints by a different campaign, operator, or host.
VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B: Final[
    dict[str, dict[str, object]]
] = {
    "ep2_accolade_events.0300": {
        "exemplars": [{
            "run": "R368",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53380128,
            "root_character_id": 32904,
            "character_scopes": {"new_reveler": 32904},
            "unique_character_scope_excludes": {
                "master_of_revels": (32904,),
            },
        }],
    },
    "ep3_story_cycle_admin_eunuch.8010": {
        "exemplars": [{
            "run": "R369",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53316816,
            "root_character_id": 32904,
            "character_scopes": {"emperor": 32904},
            "unique_character_scope_excludes": {
                "eunuch": (32904,),
                "student": (32904,),
                "rival": (32904,),
            },
        }],
    },
    "diarchy.8042": {
        "exemplars": [{
            "run": "R368",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53366952,
            "root_character_id": 32904,
            "character_scopes": {"recipient": 32904},
            "unique_character_scope_excludes": {"actor": (32904,)},
        }],
    },
    "ep1_flavor.1000": {
        "exemplars": [{
            "run": "R347b",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53205336,
            "root_character_id": 29037,
            "character_scopes": {},
            "unique_character_scope_excludes": {
                "eunuch_target": (29037,),
            },
        }],
    },
    "secrets.0108": {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53358504,
            "root_character_id": 32904,
            "character_scopes": {"event_root": 32904},
            "unique_character_scope_excludes": {
                name: (32904,)
                for name in (
                    "secret_owner", "secret_target", "secret_exposer",
                    "target", "owner", "local_secret_owner", "sex_partner",
                    "adulterer_check", "primary_character",
                    "secondary_character", "left_portrait", "right_portrait",
                )
            },
            "scope_variant_bindings": [{
                "index": 0,
                "unique_character_scope_excludes": {
                    name: (32904,)
                    for name in (
                        "secret_owner", "secret_target", "secret_exposer",
                        "target", "owner", "primary_character",
                        "secondary_character", "left_portrait",
                        "right_portrait", "lower_right_portrait",
                    )
                },
            }],
        }],
    },
    "secrets.0112": {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53358504,
            "root_character_id": 32904,
            "character_scopes": {},
            "unique_character_scope_excludes": {
                name: (32904,)
                for name in (
                    "secret_owner", "secret_target", "secret_exposer",
                    "owner", "child", "mother", "real_father",
                    "local_secret_owner", "target",
                )
            },
            "scope_variant_bindings": [{
                "index": 0,
                "unique_character_scope_excludes": {
                    name: (32904,)
                    for name in (
                        "secret_owner", "secret_target", "secret_exposer",
                        "owner", "child", "mother", "real_father",
                        "local_secret_owner", "target",
                    )
                },
            }],
        }],
    },
    "secrets.0122": {
        "exemplars": [{
            "run": "R231",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53187480,
            "root_character_id": 32904,
            "character_scopes": {
                "secret_target": 32904,
                "siphoned_treasury_victim": 32904,
                "victim": 32904,
                "exposed_secret_target": 32904,
                "liege": 32904,
            },
            "unique_character_scope_excludes": {
                "secret_owner": (32904,),
                "secret_exposer": (),
                "embezzler": (32904,),
                "local_secret_owner": (32904,),
            },
        }],
    },
    "seduce_outcome.4900": {
        "exemplars": [{
            "run": "R328",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53215752,
            "root_character_id": 32904,
            "character_scopes": {"target_liege": 32904},
            "unique_character_scope_excludes": {
                "owner": (32904,),
                "target": (32904,),
            },
        }],
    },
    "seduce_outcome.3901": {
        "exemplars": [{
            "run": "R355",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            "date_raw": 53248656,
            "root_character_id": 32904,
            "character_scopes": {"target_liege": 32904},
            "unique_character_scope_excludes": {
                "owner": (32904,),
                "target": (32904,),
            },
        }],
    },
}


__all__ = [
    "VANILLA_ACCOLADE_TIMELINE_CONTRACTS",
    "VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS",
    "VANILLA_DIARCHY_TIMELINE_CONTRACTS",
    "VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS",
    "VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS",
    "VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS",
    "VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS",
    "VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS",
    "VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS",
    "VANILLA_SECRET_TIMELINE_CONTRACTS",
    "VANILLA_SEDUCE_TIMELINE_CONTRACTS",
    "VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A",
    "VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B",
    "VANILLA_SHARD_TIMELINE_CONTRACTS",
]
