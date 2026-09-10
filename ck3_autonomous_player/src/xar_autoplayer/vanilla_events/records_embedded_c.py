"""Third shard of the portable vanilla CK3 timeline interrupt records."""

from __future__ import annotations

from typing import Final

from .registry import PLAYER_SENTINEL


_LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_dynastic_cycle_events.0040": {
        # Independent vanilla Silk Road investment event.  Authored option 1
        # is visible only during the dynastic-cycle stability-advancement
        # phase.  R406 source/live review observed the ordinary two-choice
        # projection (native indices 1/2); the earlier full projection remains
        # valid in advancement.  Options 1 and 2 spend treasury/gold and add a
        # long modifier or fascination progress; authored option 3 only retains
        # its vanilla trait-dependent stress impact in either projection.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"steward": 31003},
        "scope_types": {
            "my_situation": "situation",
            "silk_road_situation": "situation",
            "my_movement": "situation_participant_group",
        },
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
            {
                "option_count": 3,
                "snapshot_option_count": 3,
                "native_option_indices": (0, 1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
            {
                "option_count": 2,
                "snapshot_option_count": 3,
                "native_option_indices": (1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
    },
    "tgp_china_yearly.0010": {
        # Independent vanilla charlatan-poet event.  Authored option 4 is
        # hidden in this frame.  Option 1 changes merit/dread and option 2
        # recruits the generated character with a five-year modifier; the
        # final rendered option only grants minor Confucian education XP (or
        # trait-dependent stress) and disposes of the temporary character.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # The event creates this temporary character in its immediate block.
        # R26/R47 observed different valid IDs (16780004/16780149), while the
        # exact name/type/count/option shape remained stable.
        "unique_character_scope_excludes": {
            "starving_lowborn": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0005": {
        # Independent vanilla grieving-child event.  Option 1 changes court,
        # guardian, prestige and influence state; option 2 adds merit and can
        # perturb the promotion source under test.  Visible option 3 maps to
        # native index 2 and only grants minor Confucian XP (or stress when
        # absent) while disposing of the temporary child.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # Vanilla creates/selects every role in immediate, so their numeric
        # identities can legitimately change when the seed is reinstalled.
        # R50 and R56 retained the exact role/type/count/option shape with
        # different IDs.  Bind the source-defined relationships instead of
        # treating allocator output as product drift.
        "unique_character_scope_excludes": {
            "grieving_child": (29037,),
            "orphan_mother": (29037,),
            "orphan_father": (29037,),
            "parent": (29037,),
            "guardian": (29037,),
            "messenger": (29037,),
        },
        "character_scope_matches_any": {
            "parent": ("orphan_mother", "orphan_father"),
        },
        "boolean_scopes": (),
        "saved_scope_count": 6,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0015": {
        # Independent vanilla merchant-dispute event.  Authored option 4 is
        # hidden in this frame.  Options 1 and 2 change merit and/or treasury;
        # the final rendered option only grants minor Confucian education XP
        # (or trait-dependent stress), while hidden/after cleanup removes both
        # temporary merchants.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # Both merchants are created in this event's immediate block. Their
        # allocator IDs legitimately change on each seed reinstall; the
        # stable source contract is two distinct non-player Characters.
        "unique_character_scope_excludes": {
            "market_vendor": (29037,),
            "traveling_merchant": (29037,),
        },
        "character_scope_differs_from": {
            "market_vendor": ("traveling_merchant",),
            "traveling_merchant": ("market_vendor",),
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0020": {
        # Independent vanilla unpaid-tax event.  Neither branch is a no-op.
        # Option 1 lowers control in the typed county and grants the liege
        # treasury/opinion (plus trait-dependent stress); option 2 instead
        # costs the player major influence and installs a five-year county
        # modifier.  Select the first bounded branch without the long modifier.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # The event immediate reads root.liege at delivery time and chooses a
        # current councillor from that liege.  Both character IDs therefore
        # legitimately change as the seed timeline advances; the stable
        # source contract is two distinct non-player Character roles.
        "unique_character_scope_excludes": {
            "tax_official": (29037,),
            "tax_liege": (29037,),
        },
        "character_scope_differs_from": {
            "tax_official": ("tax_liege",),
            "tax_liege": ("tax_official",),
        },
        "scope_types": {"taxless_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_emperor_yearly.2200": {
        # Independent vanilla emperor-yearly embezzlement offer.  Option 1
        # grants gold but installs a ten-year embezzling flag, lowers
        # governance by four, and can force the disloyal trait.  Refusal has
        # no authored mutation beyond trait-dependent stress, so take it.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"liege": 32904},
        "scope_types": {
            "governorship": "landed_title",
            "capital": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "ep3_emperor_yearly.2240": {
        # Independent vanilla scholar encounter.  Option 1 starts a learning
        # duel with influence consequences and option 2 mutates dread,
        # influence and gold.  Authored option 3 is the explicit opt-out and
        # only applies a fixed minor stress loss.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"the_scholar": 56656},
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep1_flavor.1200": {
        # Independent vanilla learned-eunuch event.  The first three branches
        # pay gold and install a fifteen-year player modifier.  Refusal keeps
        # player resources/skills unchanged and confines the mutation to the
        # typed event character's opinion/potential rivalry plus stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"eunuch_target": 16780004},
        "scope_types": {"eunuch_target_culture": "culture"},
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.3060": {
        # Independent vanilla imperial-succession event.  Authored option 1
        # is hidden in this frame; rendered option 3 maps to native index 3
        # and has no scripted effect, unlike the political support/detractor
        # branches.
        "date_raw": (53148048, 53149416, 53152368, 53156640),
        # This independent vanilla succession notice has now appeared from
        # early through late in the same bounded product observation.  Bind
        # only its date to that run's finite window; every identity, type,
        # scope-count and option-shape check remains exact.
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "previous_holder": 32904,
            "new_holder": 36354,
            "emperor": 36354,
            "root_scope": 29037,
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "nf_gov_type": "government_type",
            "emp_location": "province",
        },
        "boolean_scopes": (),
        "saved_scope_count": 8,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8130": {
        # Independent vanilla arbitrary-tax event.  Option 4 avoids the
        # modifier, treasury, influence and governance mutations in the first
        # three branches; only its trait-dependent stress impact remains.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8160": {
        # Independent vanilla equitable-access event.  The first two branches
        # alter treasury/influence/governance/cultural acceptance, dread,
        # relationships, county modifiers or court membership.  Authored
        # option 3 is an empty dismissal; the common after block disposes of
        # the event-created administrator.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 31003,
            "culture": 29037,
        },
        # `create_character` allocates a fresh administrator every time this
        # event opens.  Bind its event-local relationship, never a historical
        # allocator ID from one prior run.
        "unique_character_scope_excludes": {
            "administrator": (29037,),
        },
        "character_scope_differs_from": {
            "administrator": ("councillor",),
        },
        "scope_types": {"minority_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8170": {
        # Independent vanilla local-defense event.  Options 1-3 spend treasury,
        # alter governance or enter martial/diplomacy duels with broader
        # modifier/truce/influence outcomes.  Refusal confines the mutation to
        # the typed marshal's -15 opinion toward root plus trait-dependent
        # stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor": 29037,
            "marshal": 29575,
            "raider": 32922,
        },
        "scope_types": {"raid_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "chancellor_task.1104": {
        # Vanilla foreign-affairs success letter. The active chancellor has
        # already selected a neighboring ruler in .1103; this one-option
        # continuation only grants that neighbor a temporary positive opinion
        # of root. Bind source-defined role aliases instead of allocator IDs.
        "date_raw": 53149872,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "chancellor": (29037,),
            "active_councillor": (29037,),
            "neighbor": (29037,),
        },
        "character_scope_matches_any": {
            "chancellor": ("councillor",),
            "active_councillor": ("councillor",),
        },
        "character_scope_differs_from": {
            "neighbor": ("councillor", "chancellor", "active_councillor"),
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "bp1_yearly.9006": {
        # Friends & Foes narrow-yearly event. Immediate selects exactly one
        # unrelated courtier/vassal who shares a sinful trait with root. The
        # first option creates or advances friendship and also changes piety
        # and stress; option 2 changes only root's piety/stress and therefore
        # is the bounded minimum-external-side-effect path for this capture.
        # R72's frozen seed is not craven, so the conditional animal helper is
        # absent and the complete live frame contains only the courtier.
        "date_raw": 53147520,
        "date_raw_range": (53147520, 53147520),
        "date_policy": "product-observation-window",
        "max_occurrences": 2,
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "bp1_yearly_9006_sinful_courtier": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "yearly.5050": {
        # Vanilla yearly "slighted spouse" event. The immediate block saves
        # exactly the accusing spouse and the allegedly slighting courtier.
        # Option 1 removes the courtier and can schedule a delayed follow-up;
        # option 3 always starts a duel and schedules .5051 or .5052. Option 2
        # only adjusts prestige/opinion and ends the branch, so it is the
        # bounded minimum-disruption route for a long product observation.
        # The event carries a 7200-day cooldown, hence at most two instances
        # can occur in the 10190-day manager-recovery window.
        "date_raw": 53147520,
        "date_raw_range": (53147520, 53147520),
        "date_policy": "product-observation-window",
        "max_occurrences": 2,
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "slighting_courtier": (29037,),
            "scoped_spouse": (29037,),
        },
        "character_scope_differs_from": {
            "slighting_courtier": ("scoped_spouse",),
            "scoped_spouse": ("slighting_courtier",),
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 3,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "yearly.1040": {
        # Vanilla yearly "suspicious letter" event. R85 froze the good-
        # surprise branch as one third-party Character plus two opaque flag
        # values. Option 1 changes that character's opinion once and enters
        # the immediate, one-option .1041 disclosure. Option 2 adds a duel and
        # may schedule .1044; option 3 is known-good here and always schedules
        # .1044, adding a later resource/relationship outcome. Bind the exact
        # live shape and choose the shorter deterministic continuation.
        "date_raw": (53147520,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suspicious": (29037,),
        },
        "scope_types": {
            "suspicious_type": "flag",
            "surprise_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "yearly.1041": {
        # Source-direct continuation of yearly.1040 option 1. The event adds
        # no new scope, has one unavoidable acknowledgement, and on the R85
        # good-surprise branch only renders the already-frozen surprise.
        "date_raw": (53147520,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suspicious": (29037,),
        },
        "scope_types": {
            "suspicious_type": "flag",
            "surprise_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_governor_yearly.8080": {
        # Roads to Power annual governor event.  The event creates exactly
        # one temporary magistrate.  Option 1 punishes the magistrate by
        # changing only root's governance and ten-year bureaucracy modifier;
        # unlike the alternatives it neither kills/recruits the character nor
        # embezzles gold, so it is the minimum external-side-effect path.
        "date_raw": 53147520,
        "date_raw_range": (53147520, 53147520),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "magistrate": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 4,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "sway_ongoing.1002": {
        # Vanilla ongoing-sway compliment letter. The no-friend branch
        # randomizes three distinct compliment flags from the first twelve
        # authored options, so their concrete native indices are deliberately
        # dynamic. The thirteenth authored option is always available and has
        # no option effect; only the event-wide after block clears the
        # temporary compliment flags. Select that bounded fallback while
        # binding the exact scheme owner/target frame and source-defined
        # three-random-plus-final option shape.
        "date_raw": 53149920,
        "date_raw_range": (53149920, 53149920),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
            "compliment_receiver": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 4,
        "snapshot_option_count": 13,
        "native_option_prefix_range": (0, 11),
        "native_option_suffix": (12,),
        "selected_option_number": 13,
        "selected_native_option_index": 12,
    },
    "sway_ongoing.5011": {
        # Vanilla ongoing-sway visit opening. Option 1 starts a multi-event
        # delayed exploration chain; option 2 only grants a minor stress loss
        # to the player and ends this branch. Bind the exact live scheme,
        # owner, target, artifact and target-capital frame, then choose the
        # bounded no-follow-up path so unrelated sway gameplay cannot consume
        # the promotion observation window.
        "date_raw": 53149200,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
            "capital": "province",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "sway_outcome.1001": {
        # Vanilla successful-sway outcome reached by the same exact scheme.
        # Option 1 starts a diplomacy duel with random prestige and opinion
        # results; option 2 deterministically applies the smaller opinion
        # gain (plus any authored conditional piety) and ends the scheme.
        # Bind the live owner/target and boolean success marker so this does
        # not become a generic handler for unrelated outcome windows.
        "date_raw": 53153952,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": ("scheme_successful",),
        "saved_scope_count": 5,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "tgp_interaction_event.0016": {
        # Roads to Power military-aid order sent to the joining governor.
        # The interaction has already joined root to the recipient's wars
        # before this letter opens. The event immediate only adds a custom
        # tooltip and its single option has no scripted effect, so the sole
        # acknowledgement is the exact bounded path. Generic interaction
        # slots may retain typed weak Character scopes; bind their unavailable
        # identity explicitly instead of inventing character IDs.  Recipient
        # is selected dynamically by each interaction, then source line 6658
        # saves that same Character as governor_at_war.  Freeze that authored
        # role alias, not one allocator-specific historical ID.
        "date_raw": 53159976,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "actor": 30987,
            "secondary_recipient": 29037,
            "governor_joining": 29037,
        },
        "unique_character_scope_excludes": {
            "recipient": (29037, 30987),
            "governor_at_war": (29037, 30987),
        },
        "character_scope_matches_any": {
            "recipient": ("governor_at_war",),
            "governor_at_war": ("recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "boolean_scopes": (),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "tgp_interaction_event.0030": {
        # Vanilla elder-break notification. The disciple/elder relationship
        # changes in immediate before the letter is rendered; its sole option
        # is empty. Bind the R103 interaction payload, including weak generic
        # interaction slots, the old/new elder identities and the authored
        # actor/new-disciple alias before acknowledging it.
        "date_raw": 53177256,
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "old_elder": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "new_disciple": (29037,),
            "new_elder": (29037,),
        },
        "character_scope_matches_any": {
            "actor": ("new_disciple",),
            "new_disciple": ("actor",),
        },
        "character_scope_differs_from": {
            "actor": ("new_elder",),
            "new_elder": ("actor",),
        },
        # R103 exposed the generic interaction payload.  R108 reached the
        # same empty acknowledgement through a dynastic-cycle activity and
        # exposed the activity candidates instead.  Bind both exact name
        # sets while retaining the shared actor/elder identity constraints.
        "saved_scope_name_sets": (
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "prestige",
                "gift",
                "gift_significant",
                "offer_hook",
                "offer_hook_strong",
                "influence",
                "piety",
                "hook",
                "actors_movement",
                "new_disciple",
                "old_elder",
                "new_elder",
            ),
            (
                "activity",
                "host",
                "province",
                "elder_candidate",
                "rival_candidate",
                "my_movement",
                "new_disciple",
                "old_elder",
                "new_elder",
                "actor",
                "recipient",
            ),
        ),
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "scheme_critical_moments.1134": {
        # Vanilla slander target-reaction notice. Its immediate block has
        # already applied the influence/modifier outcome before the window is
        # rendered; the sole option is empty and the after block only clears
        # a temporary nickname flag. Bind the exact live scheme payload and
        # acknowledge the only branch so the product timeline can continue.
        "date_raw": 53189328,
        "root_character_id": 29037,
        "character_scopes": {"target": 29037},
        "unique_character_scope_excludes": {"owner": (29037,)},
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
            "follow_up_event": "flag",
            "discovery_chance": "value",
        },
        # The event source writes scheme_successful whenever this branch
        # opens, while scheme_discovered is conditional on the live scheme
        # outcome. R102 observed both flags; R103 observed only success.
        "boolean_scopes": (),
        "boolean_scope_name_sets": (
            ("scheme_successful",),
            ("scheme_discovered", "scheme_successful"),
        ),
        "saved_scope_name_sets": (
            (
                "scheme",
                "owner",
                "artifact",
                "target",
                "follow_up_event",
                "discovery_chance",
                "scheme_successful",
            ),
            (
                "scheme",
                "owner",
                "artifact",
                "target",
                "follow_up_event",
                "discovery_chance",
                "scheme_discovered",
                "scheme_successful",
            ),
        ),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "realm_maintenance.2001": {
        # Vanilla title-inheritance notice. The transfer has already happened
        # before this window opens and there is only one acknowledgement.
        # Preserve the full observed title/government and character-role shape
        # so the runner cannot mistake a different one-option event for it.
        "date_raw": 53199000,
        "root_character_id": 29037,
        "character_scopes": {
            "new_holder": 29037,
            "new_minister": 29037,
            "title_holder": 29037,
        },
        "unique_character_scope_excludes": {
            "previous_holder": (29037,),
            "councillor_liege": (29037,),
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "capital_county": "landed_title",
            "nf_gov_type": "government_type",
        },
        "boolean_scopes": (),
        "saved_scope_count": 9,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "sway_outcome.2001": {
        # Vanilla diplomatic-misunderstanding outcome for the seed's existing
        # sway scheme.  The event has one unavoidable acknowledgement: the
        # typed target loses 10 opinion of the played owner and the already
        # failed sway scheme ends.  Bind the complete live scope/option shape
        # before accepting that bounded outcome.
        "date_raw": 53153952,
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}


_LEGACY_BINDING_KEYS: Final = (
    "date_raw",
    "date_raw_range",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)


def _clone_record_value(value: object) -> object:
    """Clone one JSON-shaped value without changing sequence semantics."""

    if isinstance(value, dict):
        return {
            str(key): _clone_record_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(_clone_record_value(item) for item in value)
    if isinstance(value, list):
        return [_clone_record_value(item) for item in value]
    return value


def _legacy_binding_fields(contract: dict[str, object]) -> dict[str, object]:
    """Retain every removed live binding verbatim as migration evidence."""

    binding = {
        key: _clone_record_value(contract[key])
        for key in _LEGACY_BINDING_KEYS
        if key in contract
    }
    for variant_key in ("scope_variants", "option_variants"):
        variants: list[dict[str, object]] = []
        for index, raw_variant in enumerate(contract.get(variant_key, ())):
            if not isinstance(raw_variant, dict):
                raise TypeError(f"{variant_key}[{index}] must be a dictionary")
            variant_binding = {
                key: _clone_record_value(raw_variant[key])
                for key in _LEGACY_BINDING_KEYS
                if key in raw_variant
            }
            if variant_binding:
                variants.append({"variant_index": index, **variant_binding})
        if variants:
            binding[f"{variant_key}_bindings"] = tuple(variants)
    return binding


def _append_relation(
    relations: dict[str, list[str]],
    scope_name: str,
    related_name: str,
) -> None:
    values = relations.setdefault(scope_name, [])
    if related_name != scope_name and related_name not in values:
        values.append(related_name)


def _portable_character_bindings(
    contract: dict[str, object],
    legacy_root: object,
) -> dict[str, object]:
    """Replace allocator IDs with player-relative role/alias constraints."""

    raw_scopes = contract.get("character_scopes", {})
    raw_excludes = contract.get("unique_character_scope_excludes", {})
    if not isinstance(raw_scopes, dict):
        raise TypeError("character_scopes must be a dictionary")
    if not isinstance(raw_excludes, dict):
        raise TypeError("unique_character_scope_excludes must be a dictionary")

    identities: dict[object, list[str]] = {}
    player_scopes: dict[str, object] = {}
    excludes: dict[str, list[object]] = {}
    for raw_name, identity in raw_scopes.items():
        name = str(raw_name)
        identities.setdefault(identity, []).append(name)
        if identity in {legacy_root, PLAYER_SENTINEL}:
            player_scopes[name] = PLAYER_SENTINEL
        else:
            excludes.setdefault(name, []).append(PLAYER_SENTINEL)

    matches: dict[str, list[str]] = {
        str(name): [str(related) for related in related_names]
        for name, related_names in dict(
            contract.get("character_scope_matches_any", {})
        ).items()
    }
    differs: dict[str, list[str]] = {
        str(name): [str(related) for related in related_names]
        for name, related_names in dict(
            contract.get("character_scope_differs_from", {})
        ).items()
    }

    # A repeated non-player numeric ID was an implicit role alias in the old
    # capture. Publish that relation explicitly, never the allocator output.
    for identity, names in identities.items():
        if identity in {legacy_root, PLAYER_SENTINEL} or len(names) < 2:
            continue
        for name in names:
            for related_name in names:
                _append_relation(matches, name, related_name)

    # Translate exclusions of a known captured role into role-to-role
    # inequalities. Unknown historical identities remain observation-only.
    for raw_name, raw_identities in raw_excludes.items():
        name = str(raw_name)
        if not isinstance(raw_identities, (tuple, list)):
            raise TypeError(
                "unique character scope exclusions must be a sequence"
            )
        for identity in raw_identities:
            if identity in {legacy_root, PLAYER_SENTINEL}:
                values = excludes.setdefault(name, [])
                if PLAYER_SENTINEL not in values:
                    values.append(PLAYER_SENTINEL)
                continue
            for related_name in identities.get(identity, ()):
                _append_relation(differs, name, related_name)
                _append_relation(differs, related_name, name)

    result: dict[str, object] = {"character_scopes": player_scopes}
    if excludes:
        result["unique_character_scope_excludes"] = {
            name: tuple(values) for name, values in excludes.items()
        }
    if matches:
        result["character_scope_matches_any"] = {
            name: tuple(values) for name, values in matches.items()
        }
    if differs:
        result["character_scope_differs_from"] = {
            name: tuple(values) for name, values in differs.items()
        }
    return result


def _neutralize_contract_value(value: object, legacy_root: object) -> object:
    """Remove campaign dates and IDs from nested variant contracts."""

    if isinstance(value, tuple):
        return tuple(
            _neutralize_contract_value(item, legacy_root) for item in value
        )
    if isinstance(value, list):
        return [
            _neutralize_contract_value(item, legacy_root) for item in value
        ]
    if not isinstance(value, dict):
        return value

    binding_keys = {
        "date_raw",
        "date_raw_range",
        "root_character_id",
        "character_scopes",
        "unique_character_scope_excludes",
        "character_scope_matches_any",
        "character_scope_differs_from",
    }
    if binding_keys.isdisjoint(value):
        return {
            str(key): _neutralize_contract_value(item, legacy_root)
            for key, item in value.items()
        }

    character_fields = _portable_character_bindings(value, legacy_root)
    neutral: dict[str, object] = {}
    for key, item in value.items():
        if key in binding_keys:
            continue
        neutral[str(key)] = _neutralize_contract_value(item, legacy_root)
    if "root_character_id" in value:
        neutral["root_character_id"] = PLAYER_SENTINEL
    neutral.update(character_fields)
    return neutral


def _neutralize_contract(contract: dict[str, object]) -> dict[str, object]:
    legacy_root = contract.get("root_character_id")
    if legacy_root != 29037:
        raise ValueError(f"unexpected embedded-C legacy root: {legacy_root!r}")
    neutral = _neutralize_contract_value(contract, legacy_root)
    if not isinstance(neutral, dict):  # pragma: no cover - mapping guard
        raise TypeError("neutralized embedded-C contract must be a dictionary")
    neutral.setdefault("date_policy", "product-observation-window")
    return neutral


EMBEDDED_C_VANILLA_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    event_key: {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            **_legacy_binding_fields(contract),
        }],
    }
    for event_key, contract in (
        _LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS.items()
    )
}


EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    event_key: _neutralize_contract(contract)
    for event_key, contract in (
        _LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS.items()
    )
}


__all__ = [
    "EMBEDDED_C_VANILLA_OBSERVATIONS",
    "EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS",
]
