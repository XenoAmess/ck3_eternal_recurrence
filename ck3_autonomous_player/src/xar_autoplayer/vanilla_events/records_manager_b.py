"""Pure-original manager interrupt records, batch B.

The source-reviewed records remain exactly represented by their Python values
here so runtime consumers can move away from acceptance-tool modules.
Product-authored annual-summary and elimination records intentionally do not
belong to this vanilla batch.
"""

from __future__ import annotations

from typing import Final


# Migrated from tools/zg361_phase2_promotion_manager_imperial_contracts.py.
MANAGER_IMPERIAL_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "ep3_emperor_yearly.8010": {
        # R338 exact fake-letter prompt. Immediate creates the liar and puts
        # them under the selected governor's house arrest; the engine helper
        # carries the same character again as new_target. Authored option A
        # only pays tiny gold to the governor and improves their opinion.
        # The other routes add a new courtier/hook, transfer influence and
        # imprison the liar under root, or execute them. Choose native 0 as
        # the smallest terminal mutation after binding the alias identity.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "governor": (32904,),
            "liar": (32904,),
            "new_target": (32904,),
        },
        "character_scope_matches_any": {
            "liar": ("new_target",),
            "new_target": ("liar",),
        },
        "character_scope_differs_from": {
            "governor": ("liar", "new_target"),
            "liar": ("governor",),
            "new_target": ("governor",),
        },
        "scope_types": {
            "governor": "character",
            "liar": "character",
            "new_target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "governor",
            "liar",
            "new_target",
        ),),
        "saved_scope_count": 3,
        "option_count": 4,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_emperor_yearly.8000": {
        # Options 1-3 each move manpower from one random governor county: that
        # county loses ten percent development (rounded up), receives the
        # lighter ten-year sacrifice modifier, and its governor loses 20
        # opinion of root. Option 4 instead removes two development from the
        # player's capital and applies the strictly heavier waning modifier.
        # Choose option 1 to preserve the acceptance owner's capital. Bind the
        # complete authored random frame: the source guarantees three distinct
        # governors, but deliberately does not guarantee their identities.
        # Vanilla applies a ten-year event cooldown rather than a campaign-wide
        # one-shot flag, so later eligible deliveries remain independently
        # valid and must be checked against the same exact frame contract.
        "date_raw": 53150712,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suggestor": (29037,),
            "governor_1": (29037,),
            "governor_2": (29037,),
            "governor_3": (29037,),
        },
        "character_scope_differs_from": {
            "governor_1": ("governor_2", "governor_3"),
            "governor_2": ("governor_1", "governor_3"),
            "governor_3": ("governor_1", "governor_2"),
        },
        "scope_types": {
            "suggestor": "character",
            "minimum_development": "value",
            "governor_1": "character",
            "county_1": "landed_title",
            "governor_2": "character",
            "county_2": "landed_title",
            "governor_3": "character",
            "county_3": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "suggestor",
            "minimum_development",
            "governor_1",
            "county_1",
            "governor_2",
            "county_2",
            "governor_3",
            "county_3",
        ),),
        "saved_scope_count": 8,
        "option_count": 4,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
        "scope_variants": ({
            # R335 exact source-authored partial selection. The event trigger
            # guarantees three governors somewhere in the realm, but the
            # developed_governors list used by immediate can contain only two
            # eligible distinct entries. Vanilla's three-iteration while then
            # saves only pairs 1/2; option C (native 2) is hidden. Preserve the
            # same native-0 route, which still avoids damaging root's capital.
            "saved_scope_names": (
                "suggestor",
                "minimum_development",
                "governor_1",
                "county_1",
                "governor_2",
                "county_2",
            ),
            "unique_character_scope_excludes": {
                "suggestor": (29037,),
                "governor_1": (29037,),
                "governor_2": (29037,),
            },
            "character_scope_differs_from": {
                "governor_1": ("governor_2",),
                "governor_2": ("governor_1",),
            },
            "scope_types": {
                "suggestor": "character",
                "minimum_development": "value",
                "governor_1": "character",
                "county_1": "landed_title",
                "governor_2": "character",
                "county_2": "landed_title",
            },
            "saved_scope_count": 6,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (0, 1, 3),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_nickname_contracts.py.
MANAGER_NICKNAME_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "lifestyle_nicknames.1000": {
        # CK3 1.19.0.6 random-nickname notification. The nickname is already
        # assigned by assign_random_nickname_effect before this event opens.
        # R193 observed the bad-nickname, free and capable projection: among
        # six authored options only option B (native index 1) is visible. It
        # is therefore the sole route out of this unrelated vanilla window.
        # Bind the complete inherited nickname frame rather than treating the
        # event namespace as a general allowlist.
        "date_raw": 53158896,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "possible_conqueror": 29037,
            "nickname_root_scope": 29037,
            "nickname_getter": 29037,
        },
        "unique_character_scope_excludes": {
            "informer": (29037,),
        },
        "scope_types": {
            "informer": "character",
        },
        "boolean_scopes": (
            "toggle_null_result",
            "had_nick_the_mad",
        ),
        "saved_scope_name_sets": ((
            "possible_conqueror",
            "toggle_null_result",
            "nickname_root_scope",
            "had_nick_the_mad",
            "nickname_getter",
            "informer",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "snapshot_option_count": 6,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_parent_contracts.py.
MANAGER_PARENT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "parent.1005": {
        # CK3 1.19.0.6 learning-support offer.  Route A grants +3 learning for
        # five years but also increments the parent's meddling ledger, which
        # can schedule another random parent event.  Route B terminates after
        # one deterministic -15 opinion from the parent and creates no follow-
        # up ticket, modifier or meddling state, so it is the bounded route.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "parent": 29613,
        },
        "unique_character_scope_excludes": {
            "parent": (32904,),
        },
        "scope_types": {
            "parent": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("parent",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_prison_contracts.py.
MANAGER_PRISON_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "prison_notification.2002": {
        # CK3 1.19.0.6 full popup sent when a player's heir or spouse is
        # released. The release itself and its memory happen before this
        # notification; its only authored option is an empty acknowledgement.
        "date_raw": 53390784,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "this_player": 32904,
        },
        "unique_character_scope_excludes": {
            "imprisoner": (32904,),
            "prisoner": (32904,),
        },
        "character_scope_matches_any": {
            "bg_override_char": ("imprisoner",),
        },
        "character_scope_differs_from": {
            "imprisoner": ("prisoner",),
            "prisoner": ("imprisoner",),
        },
        "scope_types": {
            "imprisoner": "character",
            "new_memory": "character_memory",
            "prisoner": "character",
            "bg_override_char": "character",
            "this_player": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "imprisoner",
            "new_memory",
            "prisoner",
            "bg_override_char",
            "this_player",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # A player's different heirs or spouses can be imprisoned and released
        # repeatedly during one long campaign observation window.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_spymaster_contracts.py.
MANAGER_SPYMASTER_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "spymaster_task.3001": {
        # CK3 1.19.0.6 Find Secrets side effect. Option 1 preserves the
        # current Spymaster task and confines the outcome to authored
        # prestige/opinion plus the target's notification. Option 2 stops the
        # task and would mutate the continuing product timeline. R319 observed
        # the exact manager, councillor and target tuple with both buttons.
        "date_raw": 53161632,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "target_character",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "spymaster_task.0381": {
        # Independent vanilla Find Secrets hook opportunity. Option 1 spends
        # gold and fabricates a hook; option 2 only grants the one typed third
        # party a decaying opinion modifier toward root. The same exact event
        # can recur on this seed. The second council-task delivery moved by
        # ten days between R35 and R57 while every semantic field stayed
        # exact. R99 then observed a third delivery at date_raw 53157024 after
        # two fully validated drains in the same PID. Vanilla task progress/
        # random discovery controls delivery; neither selected effect checks
        # the calendar. Use this run's existing product observation window,
        # independently of the three-occurrence cap.
        "date_raw": (53148768, 53152656),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "max_occurrences": 3,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "unique_character_scope_excludes": {
            "character_to_hook": (29037, 32904),
        },
        "boolean_scopes": ("having_find_secrets_event",),
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0399": {
        # Vanilla Find Secrets "found nothing" delivery. The event's
        # immediate random_list saves exactly one of two boolean scopes:
        # secrets_to_be_found when the Spymaster suspects a secret remains,
        # or no_secrets_here otherwise. R60/R69 observed the two legitimate
        # branches with every character identity and option shape unchanged.
        # The task cadence also controls the delivery date, so bind it to the
        # same per-run product observation window as the other Find Secrets
        # notifications instead of freezing one RNG tick.
        "date_raw": (53148768, 53152896),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": (),
        "boolean_scope_name_sets": (
            ("no_secrets_here",),
            ("secrets_to_be_found",),
        ),
        "saved_scope_name_sets": (
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "no_secrets_here",
            ),
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "secrets_to_be_found",
            ),
        ),
        "option_count": 2,
        # Option 1 changes the councillor task. Option 2 preserves the current
        # task and is the already-proven minimal side-effect path.
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0342": {
        # Vanilla Find Secrets discovery notification. The secret and its
        # participants are already fixed when the window opens; there is one
        # authored acknowledgement, which reveals that exact secret to root.
        # R61 observed the same exact one-option/scope identity later in the
        # continuing Find Secrets task. The notification date is selected by
        # the vanilla discovery cadence, not by the revealed-secret contract.
        "date_raw": (53152896, 53157024),
        "date_raw_range": (53152896, 53157024),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
            "active_councillor": 27963,
            "secret_holder": 27051,
        },
        "scope_types": {"secret_to_reveal": "secret"},
        "boolean_scopes": ("having_find_secrets_event",),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0344": {
        # Vanilla Find Secrets murder-secret notification. The secret holder
        # and murder victim are fixed before the window opens. When no murder
        # scheme targets the holder, native option 0 is the sole rendered
        # acknowledgement and only reveals the secret. When such a scheme
        # exists, native option 1 is exclusive, becomes the sole rendered
        # button and additionally advances that already-running scheme. R357
        # observed the latter projection, so bind both source-defined shapes
        # while selecting the only authored button available in either one.
        "date_raw": 53269008,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
            "target": (29037,),
            "secret_holder": (29037,),
        },
        "character_scope_matches_any": {
            "owner": ("councillor", "active_councillor"),
            "councillor": ("owner", "active_councillor"),
            "active_councillor": ("owner", "councillor"),
            "target": ("target_character",),
            "target_character": ("target",),
        },
        "character_scope_differs_from": {
            "owner": ("target", "secret_holder"),
            "target": ("owner",),
            "secret_holder": ("owner", "murder_target"),
            "murder_target": ("secret_holder",),
        },
        "scope_types": {
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "target_character": "character",
            "councillor": "character",
            "active_councillor": "character",
            "secret_holder": "character",
            "secret_to_reveal": "secret",
            "murder_target": "character",
        },
        "optional_scope_types": {"scheme": "scheme"},
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "owner",
                "artifact",
                "target",
                "councillor_liege",
                "target_character",
                "councillor",
                "active_councillor",
                "secret_holder",
                "secret_to_reveal",
                "murder_target",
            ),
            (
                "scheme",
                "owner",
                "artifact",
                "target",
                "councillor_liege",
                "target_character",
                "councillor",
                "active_councillor",
                "secret_holder",
                "secret_to_reveal",
                "murder_target",
            ),
        ),
        "saved_scope_counts": (10, 11),
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "option_variants": (
            {
                "option_count": 1,
                "native_option_indices": (0,),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 1,
                "native_option_indices": (1,),
                "selected_option_number": 2,
                "selected_native_option_index": 1,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "spymaster_task.0346": {
        # Vanilla Find Secrets lover-secret notification. Like .0342, the
        # discovery is already fixed when the window opens and exposes one
        # acknowledgement, which reveals that exact secret to root.
        # R62 carried the upstream having_find_secrets_event boolean, while
        # R357 retained the complete scheme/task container without that
        # transient value. Bind both exact source-produced frames and reject
        # every unreviewed mix; each discovered lover secret is independent.
        "date_raw": (53152896, 53152920),
        "date_raw_range": (53152896, 53152920),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
            "target": (29037,),
            "secret_holder": (29037,),
            "lover": (29037,),
        },
        "character_scope_matches_any": {
            "owner": ("councillor", "active_councillor"),
            "councillor": ("owner", "active_councillor"),
            "active_councillor": ("owner", "councillor"),
            "target": ("target_character",),
            "target_character": ("target",),
        },
        "character_scope_differs_from": {
            "owner": ("target", "secret_holder", "lover"),
            "target": ("owner",),
            "secret_holder": ("owner", "lover"),
            "lover": ("owner", "secret_holder"),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "target_character": "character",
            "councillor": "character",
            "active_councillor": "character",
            "secret_holder": "character",
            "secret_to_reveal": "secret",
            "lover": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "councillor_liege",
            "target_character",
            "councillor",
            "active_councillor",
            "secret_holder",
            "secret_to_reveal",
            "lover",
        ),),
        "saved_scope_count": 11,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
        "scope_variants": ({
            "saved_scope_names": (
                "councillor",
                "councillor_liege",
                "target_character",
                "active_councillor",
                "secret_holder",
                "secret_to_reveal",
                "lover",
                "having_find_secrets_event",
            ),
            "character_scopes": {
                "councillor_liege": 29037,
            },
            "unique_character_scope_excludes": {
                "councillor": (29037,),
                "target_character": (29037,),
                "active_councillor": (29037,),
                "secret_holder": (29037,),
                "lover": (29037,),
            },
            "character_scope_matches_any": {
                "councillor": ("active_councillor",),
                "active_councillor": ("councillor",),
            },
            "character_scope_differs_from": {
                "councillor": ("target_character", "secret_holder", "lover"),
                "secret_holder": ("councillor", "lover"),
                "lover": ("councillor", "secret_holder"),
            },
            "scope_types": {
                "councillor": "character",
                "councillor_liege": "character",
                "target_character": "character",
                "active_councillor": "character",
                "secret_holder": "character",
                "secret_to_reveal": "secret",
                "lover": "character",
            },
            "boolean_scopes": ("having_find_secrets_event",),
            "saved_scope_count": 8,
        },),
    },
    "spymaster_task.0359": {
        # Vanilla fallback for a discovered secret not covered by a more
        # specific flavor event. The secret already exists before the window;
        # its sole option reveals that exact secret to root. R195 observed the
        # complete ten-scope task frame and the only authored option. R201
        # then delivered two independently exact instances in the same client
        # at dates 53178192 and 53178912, and R355 delivered another exact
        # instance at date 53239344. Vanilla selects this fallback afresh from
        # task_find_secrets_reveal_selection whenever a completed Find Secrets
        # outcome is not covered by a more specific event. It is repeatable per
        # task outcome, not campaign-global; retain the bounded product window
        # while validating every delivered instance independently.
        "date_raw": 53168112,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
            "target": (29037,),
            "secret_holder": (29037,),
        },
        "character_scope_matches_any": {
            "owner": ("councillor", "active_councillor"),
            "councillor": ("owner", "active_councillor"),
            "active_councillor": ("owner", "councillor"),
            "target": ("target_character",),
            "target_character": ("target",),
        },
        "character_scope_differs_from": {
            # Find Secrets searches the target court, including secrets owned
            # by the target character. The secret holder may therefore equal
            # target/target_character; only the active spymaster must remain
            # a different party in the reviewed task frame.
            "owner": ("target", "secret_holder"),
            "target": ("owner",),
            "secret_holder": ("owner",),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "target_character": "character",
            "councillor": "character",
            "active_councillor": "character",
            "secret_holder": "character",
            "secret_to_reveal": "secret",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "councillor_liege",
            "target_character",
            "councillor",
            "active_councillor",
            "secret_holder",
            "secret_to_reveal",
        ),),
        "saved_scope_count": 10,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_tgp_interaction_contracts.py.
MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_interaction_event.0010": {
        # Request-military-aid letter received by the player.  Exact 1.19.0.6
        # source (tgp_interaction_events.txt:110-237) authors three options;
        # the live R295 frame hides option A because its war-join trigger is
        # false, leaving native indices 1 and 2; R355 observes the source-
        # authored sibling with all three options visible. Option B is the
        # AI-default bounded resolution in both projections: it assigns the
        # already-saved joining governor and sends the response to the
        # requester. Option C opens another interaction window, so it is
        # unsuitable for a modal-drain client. The source interaction has a
        # 30-day interaction cooldown and a one-year AI request cooldown, not
        # a whole-campaign occurrence limit; independent governors can send
        # further requests inside the bounded product timeline.
        "date_raw": 53245584,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
            "joining_governor": (32904,),
        },
        "character_scope_differs_from": {
            "actor": ("joining_governor",),
            "joining_governor": ("actor",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {},
        "boolean_scopes": ("hook", "dominant_family"),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "hook",
            "dominant_family",
            "joining_governor",
        ),),
        "saved_scope_count": 8,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "option_variants": ({
            "option_count": 2,
            "native_option_indices": (1, 2),
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        }, {
            "option_count": 3,
            "native_option_indices": (0, 1, 2),
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        }),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "tgp_interaction_event.0015": {
        # Notification sent after another governor has already been added to
        # the recipient's wars. Immediate and option only show tooltips; the
        # one authored option adds no further gameplay mutation. The source
        # interaction is repeatable across independent actor/recipient pairs;
        # R177 observed two exact occurrences in one bounded reconnect.
        "date_raw": 53156904,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "governor_at_war": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "governor_joining": (29037,),
        },
        "character_scope_matches_any": {
            "secondary_recipient": ("governor_joining",),
            "governor_joining": ("secondary_recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "governor_at_war",
            "governor_joining",
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 2,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_tgp_ministry_contracts.py.
_TREASURY_PREFERENCE_SCOPES = (
    "ministry_budget",
    "military_budget",
    "hegemon_budget",
    "meritocratic_salary_budget",
    "meritocratic_military_budget",
)


MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_china_ministry.0100": {
        # CK3 1.19.0.6 treasury-budget renewal for the top liege. Option 1
        # opens the picker and option 3 enacts the steward's preference.
        # Option 2 preserves the current allocation and terminates. The event
        # source saves exactly one preference scope on root; bind each authored
        # celestial/meritocratic name instead of accepting arbitrary scopes.
        "date_raw": 53163168,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "treasury_ruler": 29037,
            "salary_budget": 29037,
        },
        "unique_character_scope_excludes": {"steward": (29037,)},
        "scope_types": {"steward": "character"},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "treasury_ruler",
            "steward",
            "salary_budget",
        ),),
        "saved_scope_count": 3,
        "scope_variants": tuple({
            "saved_scope_names": (
                "treasury_ruler",
                "steward",
                preference_scope,
            ),
            "saved_scope_count": 3,
            "character_scopes": {
                "treasury_ruler": 29037,
                preference_scope: 29037,
            },
            "scope_types": {"steward": "character"},
            "unique_character_scope_excludes": {"steward": (29037,)},
        } for preference_scope in _TREASURY_PREFERENCE_SCOPES),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # yearly_on_actions delivers this event every year and the source
        # admits another player renewal after 96 months, or earlier when the
        # treasury capacity/deficit branches require it.  It is therefore a
        # renewable budget prompt, not a once-per-observation interrupt.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_tgp_petition_contracts.py.
_NON_PROVINCE_BOOLEAN_SCOPES = (
    "increase_law",
    "decrease_law",
    "increase_army_law",
    "decrease_army_law",
    "hold_examinations",
    "increase_budget_salary",
    "increase_budget_ministry",
    "increase_budget_military",
    "increase_retirement_law",
    "decrease_retirement_law",
)

_PROVINCE_TYPE_SCOPES = (
    "province_metropolitan",
    "province_industrial",
    "province_military",
    "province_protectorate",
)

_PROVINCE_MEMBER_SHAPES = (
    ("other_movement_member",),
    ("house_movement_member", "other_movement_member"),
    ("disciple_movement_member", "other_movement_member"),
    (
        "other_movement_member",
        "house_movement_member",
        "disciple_movement_member",
    ),
)


def _province_petition_scope_variant(
    province_scope: str, member_scopes: tuple[str, ...]
) -> dict[str, object]:
    """Return one exact source-authored province-petition scope shape."""

    character_scopes = (*member_scopes, "province_change_recipient")
    return {
        "saved_scope_names": (
            "petitioner",
            "actors_movement",
            "hegemon",
            "petition_recipient",
            province_scope,
            *character_scopes,
        ),
        "saved_scope_count": 5 + len(character_scopes),
        "scope_types": {
            "petitioner": "character",
            "actors_movement": "situation_participant_group",
            **{name: "character" for name in character_scopes},
        },
        "boolean_scopes": (province_scope,),
        "unique_character_scope_excludes": {
            "petitioner": (29037,),
            **{name: (29037,) for name in character_scopes},
        },
        "character_scope_matches_any": {
            # .0100 option A writes the petitioner's own scope into
            # ``province_change``; options B-D write one of the selected
            # movement members. .0101 then materializes that exact stored
            # value as ``province_change_recipient``. Bind the complete
            # authored alias set rather than requiring a movement member.
            "province_change_recipient": ("petitioner", *member_scopes),
        },
    }


MANAGER_TGP_PETITION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_decision_events.0101": {
        # CK3 1.19.0.6 movement-petition decision delivered to the played
        # hegemon. Option 1 applies the request and option 2 opens a follow-up
        # chain. Authored option 3 refuses, clears the petition variables, and
        # does not mutate the Phase-2 state machine, so it is the bounded route
        # for this unrelated interruption.
        "date_raw": 53156928,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "hegemon": 29037,
            "petition_recipient": 29037,
        },
        "unique_character_scope_excludes": {
            "petitioner": (29037,),
            "other_movement_member": (29037,),
            "province_change_recipient": (29037,),
        },
        "character_scope_matches_any": {
            "other_movement_member": ("province_change_recipient",),
            "province_change_recipient": ("other_movement_member",),
        },
        "scope_types": {
            "petitioner": "character",
            "actors_movement": "situation_participant_group",
            "other_movement_member": "character",
            "province_change_recipient": "character",
        },
        "boolean_scopes": ("province_metropolitan",),
        "saved_scope_name_sets": ((
            "petitioner",
            "actors_movement",
            "hegemon",
            "petition_recipient",
            "province_metropolitan",
            "other_movement_member",
            "province_change_recipient",
        ),),
        "saved_scope_count": 7,
        "scope_variants": tuple({
            # Exact-build law, examination, budget and retirement decisions
            # save one boolean branch scope and no province/member recipients.
            # R164/R166 observed two law siblings, R291 observed the
            # hold_examinations sibling, and R355 observed
            # increase_budget_ministry with the same five-scope shape. The
            # remaining names are the exact selectable-item values from the
            # same CK3 1.19.0.6 movement-petition decision view.
            "saved_scope_names": (
                "petitioner",
                "actors_movement",
                "hegemon",
                "petition_recipient",
                direction_scope,
            ),
            "saved_scope_count": 5,
            "scope_types": {
                "petitioner": "character",
                "actors_movement": "situation_participant_group",
            },
            "boolean_scopes": (direction_scope,),
            "unique_character_scope_excludes": {"petitioner": (29037,)},
            "character_scope_matches_any": {},
        } for direction_scope in _NON_PROVINCE_BOOLEAN_SCOPES) + tuple(
            # Exact-build source .0100 exposes four province-type branches.
            # R175/R185 observed house/other recipient selection, R186
            # observed the industrial sibling, and R289 observed both option
            # A's petitioner-self recipient and the independently valid
            # disciple+other/no-house participant shape. Enumerate the
            # source-authored cross product while retaining exact names and
            # recipient identity.
            _province_petition_scope_variant(province_scope, member_scopes)
            for province_scope in _PROVINCE_TYPE_SCOPES
            for member_scopes in _PROVINCE_MEMBER_SHAPES
        ),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        # Each independent character may make another movement petition; the
        # vanilla source has no whole-product two-occurrence cap. Keep every
        # delivery exact while bounding the run by the product window.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_trait_contracts.py.
MANAGER_TRAIT_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "trait_specific_ongoing.2001": {
        # CK3 1.19.0.6 possessed-character vision. Immediate sets the
        # one-life occurrence flag and resolves a same-faith clergy witness.
        # Native options 0 and 1 respectively run a learning duel or schedule
        # a delayed witch-knowledge event. Native option 2 only relieves
        # stress and terminates the window, so it is the bounded source-capture
        # route. R346 observed this exact one-scope, three-option projection.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "clergy": (29037,),
        },
        "scope_types": {
            "clergy": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("clergy",),),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "trait_specific_ongoing.3009": {
        # CK3 1.19.0.6 depressed-character exhaustion notice. Immediate has
        # already installed the ten-year recurrence flag and five-year
        # exhausted modifier; the sole native option is empty, so native0 is
        # the unavoidable acknowledgement. The ten-year flag can expire
        # during this bounded multi-decade observation, making recurrence
        # source-legal even though one frozen occurrence has no saved scopes.
        "date_raw": 53380728,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "saved_scope_name_sets": ((),),
        "saved_scope_count": 0,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "trait_specific_ongoing.3015": {
        # CK3 1.19.0.6 depressed-character criticism event. Immediate sets a
        # ten-year recurrence flag and resolves one unsympathetic councillor,
        # powerful vassal, liege, spouse, or close-family courtier. Native0
        # adds stress and rolls a five-year modifier; native2 loses prestige
        # and can add stress. Native1 only applies -15 opinion from the saved
        # critic, so it is the bounded low-impact continuation route. R365
        # observed the exact one-scope, three-option projection. Source file
        # SHA-256: 34A53CF4AA0B2AE955211024D5C0AF3753A05A4C3529CFE553BA5711C37F50BD.
        "date_raw": 53313672,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "unsympathetic": (32904,),
        },
        "scope_types": {
            "unsympathetic": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("unsympathetic",),),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_tribute_contracts.py.
_RESOURCE_TRIBUTE_TYPES = ("gold", "herd")


def _resource_reward_scope_variant(resource_type: str) -> dict[str, object]:
    resource_scopes = tuple(
        f"{size}_{resource_type}_tribute"
        for size in ("small", "adequate", "excessive")
    )
    return {
        "saved_scope_names": (
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            *resource_scopes,
            "tribute_mission_target",
            "tributary_scope",
            "overlord_scope",
            "receiving_character",
            "opinion_of_tributary",
            "tribute_reward_type_treasury",
            "saved_innovation",
            "decided_on_treasury_reward",
        ),
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "tributary_scope": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": resource_scopes,
        "saved_scope_count": 16,
    }


MANAGER_TRIBUTE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "tribute_mission.1002": {
        # CK3 1.19.0.6 human-tribute receipt. R136 observed a concubine
        # tribute: authored option 3 was hidden, leaving native indices
        # 0/1/3. R354 observed the source-defined eunuch branch: authored
        # option 2 was hidden, leaving 0/2/3. The final authored option
        # declines either character and changes no product state. The event
        # still advances to its vanilla reward decision, which must be
        # reviewed under its own exact contract when observed. Tribute
        # missions can recur for the same receiving ruler, so this receipt
        # event has no lifecycle occurrence ceiling inside one product
        # observation window either.
        "date_raw": 53150160,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "tribute_mission_target": 29037,
            "overlord_scope": 29037,
            "receiving_character": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "tributary_scope": (29037,),
            "concubine_character": (29037,),
            "human_tribute": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
            "secondary_recipient": (
                "concubine_character",
                "human_tribute",
            ),
            "concubine_character": (
                "secondary_recipient",
                "human_tribute",
            ),
            "human_tribute": (
                "secondary_recipient",
                "concubine_character",
            ),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {
            "opinion_of_tributary": "value",
            "tribute_reward_type_treasury": "value",
            "saved_innovation": "culture_innovation",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "tribute_mission_target",
            "tributary_scope",
            "overlord_scope",
            "receiving_character",
            "opinion_of_tributary",
            "concubine_character",
            "human_tribute",
            "tribute_reward_type_treasury",
            "saved_innovation",
        ),),
        "scope_variants": (
            {
                "saved_scope_names": (
                    "actor",
                    "recipient",
                    "secondary_actor",
                    "secondary_recipient",
                    "intermediary",
                    "tribute_mission_target",
                    "tributary_scope",
                    "overlord_scope",
                    "receiving_character",
                    "opinion_of_tributary",
                    "concubine_character",
                    "human_tribute",
                    "tribute_reward_type_treasury",
                    "saved_innovation",
                ),
                "native_option_indices": (0, 1, 3),
            },
            {
                "saved_scope_names": (
                    "actor",
                    "recipient",
                    "secondary_actor",
                    "secondary_recipient",
                    "intermediary",
                    "tribute_mission_target",
                    "tributary_scope",
                    "overlord_scope",
                    "receiving_character",
                    "opinion_of_tributary",
                    "eunuch_character",
                    "human_tribute",
                    "tribute_reward_type_treasury",
                    "saved_innovation",
                ),
                "unique_character_scope_excludes": {
                    "actor": (29037,),
                    "secondary_recipient": (29037,),
                    "tributary_scope": (29037,),
                    "eunuch_character": (29037,),
                    "human_tribute": (29037,),
                },
                "character_scope_matches_any": {
                    "tributary_scope": ("actor",),
                    "secondary_recipient": (
                        "eunuch_character",
                        "human_tribute",
                    ),
                    "eunuch_character": (
                        "secondary_recipient",
                        "human_tribute",
                    ),
                    "human_tribute": (
                        "secondary_recipient",
                        "eunuch_character",
                    ),
                },
                "native_option_indices": (0, 2, 3),
            },
        ),
        "saved_scope_count": 14,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "tribute_mission.1005": {
        # Reward decision after either a human-tribute route or the direct
        # non-human tribute route. Native option 4 (monk) is hidden in the
        # reviewed frames. Native option 5 grants generic legitimacy to the
        # AI tributary without a player resource cost. Tribute missions can
        # recur for the same receiving ruler, so the event has no lifecycle
        # occurrence ceiling inside one product-observation window.
        "date_raw": 53150184,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "tribute_mission_target": 29037,
            "overlord_scope": 29037,
            "receiving_character": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "secondary_recipient": (29037,),
            "tributary_scope": (29037,),
            "human_tribute": (29037,),
        },
        "character_scope_matches_any": {
            "tributary_scope": ("actor",),
            "secondary_recipient": (
                "concubine_character",
                "human_tribute",
            ),
            "human_tribute": (
                "secondary_recipient",
                "concubine_character",
            ),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "scope_types": {
            "opinion_of_tributary": "value",
            "tribute_reward_type_treasury": "value",
            "saved_innovation": "culture_innovation",
            "decided_on_treasury_reward": "flag",
        },
        "optional_scope_types": {
            "concubine_character": "character",
            "rejected_concubine": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "concubine_character",
                "human_tribute",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "rejected_concubine",
                "decided_on_treasury_reward",
            ),
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "human_tribute",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "decided_on_treasury_reward",
            ),
        ),
        "scope_variants": ({
            # Direct non-human route without interaction option booleans.
            "saved_scope_names": (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "tribute_mission_target",
                "tributary_scope",
                "overlord_scope",
                "receiving_character",
                "opinion_of_tributary",
                "tribute_reward_type_treasury",
                "saved_innovation",
                "decided_on_treasury_reward",
            ),
            "unique_character_scope_excludes": {
                "actor": (29037,),
                "secondary_recipient": (29037,),
                "tributary_scope": (29037,),
            },
            "character_scope_matches_any": {
                "tributary_scope": ("actor",),
            },
            "saved_scope_count": 13,
        },) + tuple(
            # Character-interaction routes retain all three typed option
            # booleans. R188 observed gold; herd is its exact source sibling.
            _resource_reward_scope_variant(resource_type)
            for resource_type in _RESOURCE_TRIBUTE_TYPES
        ),
        "option_count": 6,
        "snapshot_option_count": 7,
        "native_option_indices": (0, 1, 2, 3, 5, 6),
        "selected_option_number": 6,
        "selected_native_option_index": 5,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


def _aggregate_manager_vanilla_timeline_contracts_b(
    tables: tuple[dict[str, dict[str, object]], ...],
) -> dict[str, dict[str, object]]:
    aggregate: dict[str, dict[str, object]] = {}
    for table in tables:
        for event_definition_key, contract in table.items():
            if event_definition_key in aggregate:
                raise ValueError(
                    "duplicate manager vanilla event contract: "
                    f"{event_definition_key}"
                )
            aggregate[event_definition_key] = contract
    return aggregate


MANAGER_VANILLA_TIMELINE_CONTRACTS_B: Final[
    dict[str, dict[str, object]]
] = _aggregate_manager_vanilla_timeline_contracts_b((
    MANAGER_IMPERIAL_TIMELINE_CONTRACTS,
    MANAGER_NICKNAME_TIMELINE_CONTRACTS,
    MANAGER_PARENT_TIMELINE_CONTRACTS,
    MANAGER_PRISON_TIMELINE_CONTRACTS,
    MANAGER_SPYMASTER_TIMELINE_CONTRACTS,
    MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS,
    MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
    MANAGER_TGP_PETITION_TIMELINE_CONTRACTS,
    MANAGER_TRAIT_TIMELINE_CONTRACTS,
    MANAGER_TRIBUTE_TIMELINE_CONTRACTS,
))


__all__ = [
    "MANAGER_IMPERIAL_TIMELINE_CONTRACTS",
    "MANAGER_NICKNAME_TIMELINE_CONTRACTS",
    "MANAGER_PARENT_TIMELINE_CONTRACTS",
    "MANAGER_PRISON_TIMELINE_CONTRACTS",
    "MANAGER_SPYMASTER_TIMELINE_CONTRACTS",
    "MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS",
    "MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS",
    "MANAGER_TGP_PETITION_TIMELINE_CONTRACTS",
    "MANAGER_TRAIT_TIMELINE_CONTRACTS",
    "MANAGER_TRIBUTE_TIMELINE_CONTRACTS",
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_B",
]
