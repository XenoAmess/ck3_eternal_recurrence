"""Pure-original CK3 manager timeline event records, batch A."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


# Migrated from tools/zg361_phase2_promotion_manager_befriend_contracts.py
_LEGACY_MANAGER_BEFRIEND_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "befriend_outcome.0002": {
        # CK3 1.19.0.6 target-side befriend outcome.  The source saves exactly
        # one outcome flag: scheme_successful for success or scheme_failed for
        # failure.  Those branches expose different first options, so bind
        # the flag and complete rendered projection as a pair.  Authored
        # option 3 (native 2) is the terminal gentle rejection in both cases;
        # it avoids creating a durable friendship and avoids the harsher
        # authored option 4 rejection.
        "date_raw": 53164584,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "target": 29037,
        },
        "unique_character_scope_excludes": {
            "owner": (29037,),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "scheme_successful": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "scheme_successful",
        ),),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 2, 3),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": ({
            # R164 critical-success projection.
            "scope_types": {
                "scheme": "scheme",
                "owner": "character",
                "artifact": "artifact",
                "scheme_successful": "flag",
            },
            "saved_scope_name_sets": ((
                "scheme",
                "owner",
                "artifact",
                "target",
                "scheme_successful",
            ),),
            "saved_scope_count": 5,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (0, 2, 3),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }, {
            # R202 failure projection.  Authored option 1 is hidden; options
            # 2/3/4 remain visible as native indices 1/2/3.
            "scope_types": {
                "scheme": "scheme",
                "owner": "character",
                "artifact": "artifact",
                "scheme_failed": "flag",
            },
            "saved_scope_name_sets": ((
                "scheme",
                "owner",
                "artifact",
                "target",
                "scheme_failed",
            ),),
            "saved_scope_count": 5,
            "option_count": 3,
            "snapshot_option_count": 4,
            "native_option_indices": (1, 2, 3),
            "selected_option_number": 3,
            "selected_native_option_index": 2,
        }),
        # R339 observed both source-authored outcomes in one long manager
        # recovery: critical success at 53217360, then failure at 53227704,
        # with distinct scheme owners and the exact reviewed projections.
        "max_occurrences": 2,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_birth_contracts.py
_BIRTH_BOOLEAN_SCOPES = (
    "is_bastard",
    "is_child_of_concubine",
    "matrilineal",
)


_LEGACY_MANAGER_BIRTH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "birth.3035": {
        # CK3 1.19.0.6 parent-side sickly-child recovery notice. birth.3034
        # has already removed sickly from scope:child before it notifies the
        # parents; this window only repeats that result as a tooltip and its
        # sole option is inert. R283 observed the played parent as root with
        # one distinct child scope and native option index 0.
        "date_raw": 53208048,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (32904,),
        },
        "scope_types": {
            "child": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("child",),),
        "saved_scope_count": 1,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.3032": {
        # CK3 1.19.0.6 father-side sickly-child notice. The mother-side event
        # has already assigned sickly before this window; immediate only
        # repeats that fact as a tooltip and the sole option is inert. R191
        # observed it inheriting the same complete non-twin birth frame.
        "date_raw": 53176080,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "father": 29037,
            "real_father": 29037,
        },
        "unique_character_scope_excludes": {
            "child": (29037,),
            "mother": (29037,),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother"),
            "mother": ("father", "real_father", "child"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.1003": {
        # CK3 1.19.0.6 father-side regular birth notice. Birth and the child's
        # default name already exist before this window. Its sole non-twin
        # option is inert except for one hard-coded historical-character case
        # that cannot match the bound player. R189 observed the seven-scope
        # non-twin frame with the played father also bound as real_father.
        "date_raw": 53175528,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "father": 29037,
            "real_father": 29037,
        },
        "unique_character_scope_excludes": {
            "child": (29037,),
            "mother": (29037,),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother"),
            "mother": ("father", "real_father", "child"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "birth.1010": {
        # CK3 1.19.0.6 dynasty-host naming notice. The birth and default name
        # already exist before this window; its sole authored option has no
        # gameplay effect. Bind every complete eight-scope frame before
        # dismissing the acknowledgement; the runner never operates the name
        # widget. The source dispatches one notice for each independently born
        # eligible dynasty child and has no campaign-global one-shot gate, so
        # validate every occurrence in the product observation window.
        "date_raw": 53154408,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (29037,),
            "father": (29037,),
            "real_father": (29037,),
            "mother": (29037,),
            "spouse_of_mother": (29037,),
        },
        "character_scope_matches_any": {
            "father": ("real_father", "spouse_of_mother"),
            "real_father": ("father", "spouse_of_mother"),
            "spouse_of_mother": ("father", "real_father"),
        },
        "character_scope_differs_from": {
            "child": ("father", "real_father", "mother", "spouse_of_mother"),
            "mother": ("father", "real_father", "spouse_of_mother"),
        },
        "scope_types": {
            "child": "character",
            "father": "character",
            "real_father": "character",
            "mother": "character",
            "spouse_of_mother": "character",
        },
        "boolean_scopes": _BIRTH_BOOLEAN_SCOPES,
        "saved_scope_name_sets": ((
            "child",
            "father",
            "real_father",
            "mother",
            *_BIRTH_BOOLEAN_SCOPES,
            "spouse_of_mother",
        ),),
        "saved_scope_count": 8,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
        "scope_variants": ({
            # R341 observed the source-authored secret-birth frame with no
            # resolvable assumed father: pregnancy_maintainance_effect carries
            # new_secret, father remains an unavailable weak character, and
            # birth.1010 cannot synthesize spouse_of_mother because neither a
            # primary spouse nor an assumed child father exists. The sole
            # option is still the same inert naming acknowledgement.
            "saved_scope_names": (
                "child",
                "father",
                "real_father",
                "mother",
                *_BIRTH_BOOLEAN_SCOPES,
                "new_secret",
            ),
            "character_scopes": {},
            "unavailable_character_scopes": ("father",),
            "unique_character_scope_excludes": {
                "child": (29037,),
                "real_father": (29037,),
                "mother": (29037,),
            },
            "character_scope_matches_any": {},
            "character_scope_differs_from": {
                "child": ("real_father", "mother"),
                "mother": ("real_father", "child"),
            },
            "scope_types": {
                "child": "character",
                "father": "character",
                "real_father": "character",
                "mother": "character",
                "new_secret": "secret",
            },
            "saved_scope_count": 8,
        },),
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_chancellor_contracts.py
_LEGACY_MANAGER_CHANCELLOR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "chancellor_task.1002": {
        # CK3 1.19.0.6 chancellor bad-side-effect notice. Immediate has
        # already frozen the current councillor and a distinct truce holder.
        # The sole authored option is unavoidable and only cancels that
        # target's one-way truce against the played root. R284 observed the
        # exact three-character frame and native option index 0.
        "date_raw": 53209248,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "councillor_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "councillor": (32904,),
            "target": (32904,),
        },
        "character_scope_differs_from": {
            "councillor": ("target",),
            "target": ("councillor",),
        },
        "scope_types": {
            "councillor": "character",
            "councillor_liege": "character",
            "target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "target",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}


MANAGER_HOLY_WAR_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "great_holy_war.0011": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "source_sha256": {
            "events/religion_events/great_holy_war_events.txt": (
                "E431A0E2FDFF5E49FB572B7184DE9B498F982B95AED875334AD1432D0F88CBA7"
            ),
            "common/on_action/religion_on_actions.txt": (
                "52D172C10A8164B007382F9DF79A48DE462CF6B390438158FD37C9B34DF8F75C"
            ),
            "common/character_interactions/00_test_interactions.txt": (
                "D57865B72018B1E024B6DCB5CF319091DA25B27AE390F7EF8F8769C4458151BB"
            ),
        },
        "definition_lines": "1138-1396",
        "production_caller": (
            "on_faith_monthly -> great_holy_war.0010 -> every_player -> "
            "great_holy_war.0011"
        ),
        "caller_semantics": (
            "each newly eligible faith/religion unlock can broadcast another "
            "notice; great_holy_war.0011 has no event-local once or cooldown guard"
        ),
        "debug_caller": (
            "00_test_interactions.txt also broadcasts the event, but its "
            "interaction is debug_only and is not a production caller"
        ),
        "option_semantics": {
            0: "same awakening faith; Christian acknowledgement; no gameplay effect",
            1: "same awakening faith; Muslim acknowledgement; no gameplay effect",
            2: "same awakening faith; other-religion acknowledgement; no gameplay effect",
            3: "different hostile faith; warning acknowledgement; no gameplay effect",
            4: "different non-hostile faith; neutral acknowledgement; no gameplay effect",
        },
        "after_effect": "custom tooltip only; no gameplay state mutation",
        "safe_option_rationale": (
            "the five mutually exclusive projections are acknowledgements; the "
            "current reviewed live projection renders only native option 3"
        ),
        "scope_boundary": (
            "faith identity stays opaque; the campaign-neutral contract binds "
            "ROOT through $player and admits only the GHW notice relationships "
            "required by the authorized holy-war exception; campaign dates and "
            "numeric identities remain observation-only"
        ),
    },
}


MANAGER_HOLY_WAR_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "great_holy_war.0011": {
        "legacy_contract_binding": {
            "kind": "legacy-live-binding",
            "date_raw": 53223552,
            "root_character_id": 29037,
            "unique_character_scope_excludes": {
                "ghw_first_sponsor": [29037],
                "background_temple_scope": [29037],
            },
        },
        "exemplars": [
            {
                "run": "R342",
                "kind": "pre-selection-live-red",
                "binding_kind": "legacy-live-binding",
                "evidence": "docs/phase2-promo/r342-great-holy-war-notice-2026-09-08.md",
                "report_sha256": (
                    "D6ECB1FC51396B30555F298FA1BC891EE7D4806F0ABFACEF54C41ACDAFF9207D"
                ),
                "date_raw": 53223552,
                "event_instance_id": 346,
                "root_character_id": 32904,
                "saved_character_ids": {
                    "ghw_first_sponsor": 32201,
                    "background_temple_scope": 32201,
                },
                "rendered_native_option_indices": [3],
                "selection_attempted": False,
            },
            {
                "run": "R372",
                "kind": "repeat-occurrence-live-red",
                "binding_kind": "legacy-live-binding",
                "artifact": (
                    "_runtime/p2r372-post-bound-continuation-live/"
                    "great-holy-war-0011-occurrence-bound-report.json"
                ),
                "artifact_sha256": (
                    "CCA408ED129ACF96769413D23ABEA69BA82CA251BA685F69796A3EA3E50B9E0C"
                ),
                "park_artifact": (
                    "_runtime/p2r372-post-bound-continuation-live/"
                    "hot-recovery-park-6.json"
                ),
                "park_artifact_sha256": (
                    "60C00A7986B1767E4D33A628D604238EA597A66E4E41E65DF1A2955F3AF157D7"
                ),
                "date_raw": 53437416,
                "event_instance_id": 670,
                "root_character_id": 32904,
                "saved_character_ids": {
                    "ghw_first_sponsor": 36145,
                    "background_temple_scope": 36145,
                },
                "rendered_native_option_indices": [3],
                "selection_attempted": False,
                "prior_same_run_occurrence": {
                    "date_raw": 53392944,
                    "event_instance_id": 606,
                    "ghw_first_sponsor": 16840827,
                    "selected_native_option_index": 3,
                    "result": "GREEN",
                },
            },
        ],
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_council_claim_contracts.py
_LEGACY_MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "court_chaplain_task.0313": {
        # CK3 1.19.0.6 notifies the duchy holder after another ruler has
        # already accepted a fabricated duchy claim and paid its cost. This
        # is a political council-task result, not faith conversion. Immediate
        # only repeats the already-granted claim as a tooltip; the sole option
        # applies the holder's fixed opinion modifier toward the claimant and
        # has no follow-up. R343 observed this exact seven-scope projection.
        "date_raw": 53227008,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "duchy_holder": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "councillor_liege": (29037,),
            "county_holder": (29037,),
        },
        "character_scope_differs_from": {
            "councillor": (
                "councillor_liege",
                "county_holder",
                "duchy_holder",
            ),
            "councillor_liege": ("county_holder", "duchy_holder"),
            "county_holder": ("duchy_holder",),
        },
        "scope_types": {
            "councillor": "character",
            "councillor_liege": "character",
            "province": "province",
            "county": "landed_title",
            "county_holder": "character",
            "duchy": "landed_title",
            "duchy_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "province",
            "county",
            "county_holder",
            "duchy",
            "duchy_holder",
        ),),
        "saved_scope_count": 7,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_court_contracts.py
_LEGACY_MANAGER_COURT_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "major_decisions.2011": {
        # R348 exact university-scholar arrival prompt. Vanilla immediate has
        # already created and employed the skilled courtier. Native option 0
        # keeps that courtier; native option 1 sends them back to the pool and
        # terminates without scheduling a follow-up event. Bind the observed
        # dynamic non-player courtier and exact two-option projection before
        # taking that minimal opt-out route.
        "date_raw": 53215344,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "new_courtier": (32904,),
        },
        "scope_types": {
            "new_courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("new_courtier",),),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "court_yearly.6030": {
        # R336 exact royal-court mockery prompt. Vanilla authors six
        # personality-gated responses, but this root exposes only authored
        # option F at native index 0. Its immediate effect has already set the
        # event cooldown; the sole visible route schedules no follow-up event.
        # Bind the selected non-player courtier and the exact 0-of-6 rendered
        # projection before acknowledging the unavoidable branch.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "6030_courtier": (32904,),
        },
        "scope_types": {
            "6030_courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("6030_courtier",),),
        "saved_scope_count": 1,
        "option_count": 1,
        "snapshot_option_count": 6,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "court_yearly.6040": {
        # R366 exact scrounger prompt. Native option 0 is unavailable because
        # its authored scrounger-eligibility/root-capacity conjunction is false
        # in this projection; the native window does not expose which operand.
        # Native 1 spends gold and schedules the 6041 follow-up; native 2 is
        # terminal, removes the selected scrounger and reduces player stress.
        # Bind the source-selected non-player character, the shared-trait
        # helper scopes and the exact native 1/2 projection before choosing
        # the no-follow-up route. Vanilla uses a 20-year cooldown rather than
        # a lifetime flag, so a long product run may legitimately see it again.
        "date_raw": 53361816,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "scrounger": (32904,),
        },
        "scope_types": {
            "scrounger": "character",
            "has_shared_trait": "flag",
        },
        "boolean_scopes": ("shared_trait_flag_applied",),
        "saved_scope_name_sets": ((
            "scrounger",
            "shared_trait_flag_applied",
            "has_shared_trait",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_death_contracts.py
_LEGACY_MANAGER_DEATH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "death_management.1000": {
        # Vanilla spouse-death notification. The three authored options are
        # mutually exclusive like/neutral/dislike projections. R176 observed
        # only authored option 2 because the deceased spouse was neutral; it
        # records the ordinary spouse memory/stress effect and terminates.
        "date_raw": 53159208,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "surviving_consort": 29037,
        },
        "unique_character_scope_excludes": {
            "dead_character": (29037,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "surviving_consort": "character",
            "dead_character": "character",
            "deceased_character_stress": "value",
            "realm": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "surviving_consort",
            "dead_character",
            "deceased_character_stress",
            "realm",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "option_variants": (
            {
                "saved_scope_name_sets": ((
                    "new_memory",
                    "surviving_consort",
                    "dead_character",
                    "deceased_character_stress",
                    "realm",
                    "like",
                ),),
                "saved_scope_count": 6,
                "boolean_scopes": ("like",),
                "option_count": 1,
                "snapshot_option_count": 3,
                "native_option_indices": (0,),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "saved_scope_name_sets": ((
                    "new_memory",
                    "surviving_consort",
                    "dead_character",
                    "deceased_character_stress",
                    "realm",
                    "dislike",
                ),),
                "saved_scope_count": 6,
                "boolean_scopes": ("dislike",),
                "option_count": 1,
                "snapshot_option_count": 3,
                "native_option_indices": (2,),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
        # The notification is dispatched per deceased spouse. A later spouse
        # can die in the same long observation window, so validate each typed
        # occurrence instead of imposing a campaign-global one-shot bound.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "death_management.1001": {
        # Vanilla child-death notification.  CK3 1.19.0.6 authors four
        # mutually exclusive options: the first three require an adult child
        # and split on ROOT's opinion of that child, while option 4 is the only
        # route for a minor. R248 observed the minor-child/native-3 shape;
        # R352 observed an adult child with opinion >= 40 and therefore only
        # native 0. death_management.0001 dynamically carries the dying
        # character into dead_character, then .0002 dispatches .1001 only from
        # a parent for whom that character is a child, so bind the exact typed
        # third-party role instead of one historical child's numeric ID. Both
        # observed routes record the deceased child for a possible mental
        # break and impose the source-authored stress effect; neither frame
        # exposes a less disruptive alternative.
        "date_raw": 53201424,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "dead_character": (32904,),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "dead_character": "character",
            "deceased_character_stress": "value",
            "realm": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "dead_character",
            "deceased_character_stress",
            "realm",
        ),),
        "saved_scope_count": 4,
        "option_count": 1,
        "snapshot_option_count": 4,
        "native_option_indices": (3,),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": ({
            "option_count": 1,
            "snapshot_option_count": 4,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
        # The dispatch is per deceased child, not campaign-global. Validate
        # every independently typed child-death notice in the product window.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "death_management.1008": {
        # Vanilla death-of-primary-heir's-spouse notification. The source has
        # one acknowledgement-only option and performs no option effect. R364
        # observed ROOT as the parent of the surviving primary-heir spouse;
        # bind those aliases and the dynamic deceased third party exactly.
        "date_raw": 53362704,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "parent_of_spouse_of_dead_character": 32904,
        },
        "unique_character_scope_excludes": {
            "surviving_consort": (32904,),
            "dead_character": (32904,),
            "spouse_of_dead_character": (32904,),
        },
        "character_scope_matches_any": {
            "surviving_consort": ("spouse_of_dead_character",),
            "spouse_of_dead_character": ("surviving_consort",),
        },
        "character_scope_differs_from": {
            "dead_character": ("spouse_of_dead_character",),
        },
        "scope_types": {
            "new_memory": "character_memory",
            "surviving_consort": "character",
            "dead_character": "character",
            "spouse_of_dead_character": "character",
            "parent_of_spouse_of_dead_character": "character",
            "deceased_character_stress": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "new_memory",
            "surviving_consort",
            "dead_character",
            "spouse_of_dead_character",
            "parent_of_spouse_of_dead_character",
            "deceased_character_stress",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # Dispatch is per deceased child's spouse, not campaign-global.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_debate_contracts.py
_LEGACY_MANAGER_DEBATE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "debate_event.5110": {
        # CK3 1.19.0.6 imperial-debate result delivered to the top liege.
        # Immediate has already calculated the winner. Option 1 overturns it
        # and costs legitimacy; option 2 confirms the calculated winner, so
        # option 2 is the bounded least-disruptive terminal route.
        "date_raw": 53163240,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "host": (29037,),
            "debate_opponent": (29037,),
            "debate_contender": (29037,),
            "debate_loser": (29037,),
            "debate_winner": (29037,),
        },
        "character_scope_matches_any": {
            "host": (
                "debate_opponent",
                "debate_contender",
                "debate_loser",
            ),
            "debate_opponent": ("host",),
            "debate_contender": ("host",),
            "debate_loser": ("host",),
        },
        "character_scope_differs_from": {
            "debate_winner": ("debate_loser",),
        },
        "scope_types": {
            "activity": "activity",
            "host": "character",
            "province": "province",
            "debate_opponent": "character",
            "debate_contender": "character",
            "debate_loser": "character",
            "debate_winner": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "activity",
            "host",
            "province",
            "debate_opponent",
            "debate_contender",
            "debate_loser",
            "debate_winner",
        ),),
        "saved_scope_count": 7,
        "scope_variants": ({
            # A regular result has no upset marker. The host is one of the
            # two event-window participants: debate_event.5110 immediately
            # rebinds debate_contender from host and set_opponent_scope_effect
            # rebinds debate_opponent from host for a top-liege recipient.
            # The calculated winner and loser instead come from the activity's
            # durable debate_contender/challenged_movement_leader variables,
            # so they need not include this delivery-window host.  R194 saw
            # host=winner while R288 saw host distinct from both outcomes.
            "saved_scope_names": (
                "activity",
                "host",
                "province",
                "debate_opponent",
                "debate_contender",
                "debate_loser",
                "debate_winner",
            ),
            "saved_scope_count": 7,
            "scope_types": {
                "activity": "activity",
                "host": "character",
                "province": "province",
                "debate_opponent": "character",
                "debate_contender": "character",
                "debate_loser": "character",
                "debate_winner": "character",
            },
            "character_scope_matches_any": {
                "host": ("debate_opponent", "debate_contender"),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
            },
        }, {
            # debate_determine_outcome_effect saves this character scope only
            # when the score produces an upset. The event runs that effect in
            # the host/contender scope, so the marker equals the host.  As in
            # the regular variant, the activity's durable outcome pair may be
            # distinct from that delivery-window host.
            "saved_scope_names": (
                "activity",
                "host",
                "province",
                "debate_opponent",
                "debate_contender",
                "debate_winner",
                "debate_loser",
                "debate_unexpected_win",
            ),
            "saved_scope_count": 8,
            "scope_types": {
                "activity": "activity",
                "host": "character",
                "province": "province",
                "debate_opponent": "character",
                "debate_contender": "character",
                "debate_loser": "character",
                "debate_winner": "character",
                "debate_unexpected_win": "character",
            },
            "unique_character_scope_excludes": {
                "host": (29037,),
                "debate_opponent": (29037,),
                "debate_contender": (29037,),
                "debate_loser": (29037,),
                "debate_winner": (29037,),
                "debate_unexpected_win": (29037,),
            },
            "character_scope_matches_any": {
                "host": ("debate_winner", "debate_loser"),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
                "debate_unexpected_win": ("host",),
            },
        }, {
            # If the activity's previously saved challenged leader has died,
            # set_opponent_scope_effect calls set_debate_target_effect again.
            # The favor-debate branch then exposes both the empowered movement
            # and its replacement leader in this same event window.  The
            # replacement is the calculated winner in the observed upset,
            # while host/contender/opponent/loser/upset-marker are one actor.
            "saved_scope_names": (
                "activity",
                "host",
                "province",
                "debate_contender",
                "current_empowered_movement",
                "challenged_movement_leader",
                "debate_opponent",
                "debate_loser",
                "debate_winner",
                "debate_unexpected_win",
            ),
            "saved_scope_count": 10,
            "scope_types": {
                "activity": "activity",
                "host": "character",
                "province": "province",
                "debate_contender": "character",
                "current_empowered_movement": "situation_participant_group",
                "challenged_movement_leader": "character",
                "debate_opponent": "character",
                "debate_loser": "character",
                "debate_winner": "character",
                "debate_unexpected_win": "character",
            },
            "unique_character_scope_excludes": {
                "host": (29037,),
                "debate_opponent": (29037,),
                "debate_contender": (29037,),
                "challenged_movement_leader": (29037,),
                "debate_loser": (29037,),
                "debate_winner": (29037,),
                "debate_unexpected_win": (29037,),
            },
            "character_scope_matches_any": {
                "host": (
                    "debate_opponent",
                    "debate_contender",
                    "debate_loser",
                    "debate_unexpected_win",
                ),
                "debate_opponent": ("host",),
                "debate_contender": ("host",),
                "debate_loser": ("host",),
                "debate_unexpected_win": ("host",),
                "challenged_movement_leader": ("debate_winner",),
                "debate_winner": ("challenged_movement_leader",),
            },
        },),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        # This event is source-bounded to once per debate activity, not once
        # per campaign. R285/R327/R355 observed four independent activities
        # delivering it during one bounded product timeline. Keep the exact
        # identity and option checks on every delivery, while the runner's
        # existing product observation horizon bounds total progression.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_health_aging_contracts.py
_LEGACY_MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "health.7000": {
        # Vanilla onset of infirmity.  Exact CK3 1.19.0.6 source and the R117
        # native event context both expose one unavoidable acknowledgement:
        # no saved scopes, one rendered/native option, and an infirm trait
        # indicator.  There is no alternate branch to optimize.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7200": {
        # Vanilla yearly-health onset of withering mind.  The event has no
        # saved scopes and exposes one mandatory acknowledgement whose sole
        # scripted effect adds the indicated withering_mind trait.  There is
        # no alternative branch to prefer; bind the complete one-option frame
        # before acknowledging it.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7400": {
        # Vanilla yearly-health onset of faltering heart. The event has no
        # saved scopes and one unavoidable acknowledgement whose sole effect
        # adds the indicated trait. Bind the complete R103 one-option frame.
        "date_raw": 53190360,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7500": {
        # Vanilla yearly-health onset of fragile bones. Like health.7200, the
        # event has no saved scopes and one unavoidable acknowledgement. Its
        # sole scripted effect adds fragile_bones, so there is no alternative
        # branch to optimize; bind the complete one-option frame first.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}


# Migrated from tools/zg361_phase2_promotion_manager_health_contracts.py
_LEGACY_MANAGER_HEALTH_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "health.7100": {
        # CK3 1.19.0.6 infirm-health pulse. Immediate only freezes the
        # one-time flag; the sole authored option necessarily adds depressed_1.
        # R320 observed the exact played manager, empty saved-scope frame and
        # one enabled acknowledgement. No alternative branch exists, so bind
        # that complete shape and continue the character-bound product path.
        "date_raw": 53160264,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "health.2201": {
        # Vanilla disease notice for someone whose health matters to root.
        # This exact live projection exposes authored options 6 and 7 because
        # root may choose treatment but no court physician is available.
        # Option 6 begins the find-physician flow. Authored option 7 has no
        # scripted effect, so it is the bounded route that avoids a follow-up
        # hiring/search chain while leaving the already-contracted disease
        # untouched. Bind the cared-for third party, root's court ownership,
        # disease flag, background province, and exact rendered projection.
        "date_raw": 53156832,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "health_court_owner": 29037,
        },
        "unique_character_scope_excludes": {
            "sick_character": (29037,),
        },
        "scope_types": {
            "sick_character": "character",
            "disease_type": "flag",
            "background_terrain_scope": "province",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sick_character",
            "disease_type",
            "health_court_owner",
            "background_terrain_scope",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (5, 6),
        "selected_option_number": 7,
        "selected_native_option_index": 6,
        "scope_variants": ({
            # R368 received the same no-physician projection from vanilla's
            # epidemic-aware disease-contraction path. That caller legally
            # retains the originating epidemic, although health.2201 does
            # not consult it when rendering native options 5/6. Keep the
            # exact five-scope shape coupled to that unchanged projection.
            "saved_scope_names": (
                "epidemic",
                "disease_type",
                "sick_character",
                "health_court_owner",
                "background_terrain_scope",
            ),
            "saved_scope_count": 5,
            "scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "sick_character": "character",
                "background_terrain_scope": "province",
            },
        },),
        "option_variants": ({
            # When a physician is available and root controls the patient's
            # treatment, vanilla exposes safe/risky/deny/self-pick.  The
            # epidemic and physician scopes are then retained as well.  Safe
            # treatment is the least disruptive survival-preserving route;
            # the later treatment-result cards already have exact contracts.
            "saved_scope_name_sets": ((
                "epidemic",
                "disease_type",
                "physician",
                "sick_character",
                "health_court_owner",
                "background_terrain_scope",
            ),),
            "saved_scope_count": 6,
            "unique_character_scope_excludes": {
                "sick_character": (29037,),
                "physician": (29037,),
            },
            "scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "physician": "character",
                "sick_character": "character",
                "background_terrain_scope": "province",
            },
            "option_count": 4,
            "snapshot_option_counts": (4, 7),
            "native_option_indices": (0, 1, 3, 4),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "health.2202": {
        # CK3 1.19.0.6 recovery notice for a character important to root.
        # Disease removal is performed before the modal opens; its sole
        # authored option only acknowledges the result (apart from clearing a
        # marriage-bed modifier for recovered STDs). This exact smallpox path
        # retains the originating epidemic and physician alongside the cared-
        # for third party and disease flag.
        "date_raw": 53342400,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "physician": (29037,),
            "sick_character": (29037,),
        },
        "character_scope_differs_from": {
            "physician": ("sick_character",),
            "sick_character": ("physician",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "physician": "character",
            "sick_character": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "disease_type",
            "physician",
            "sick_character",
        ),),
        "saved_scope_count": 4,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "health.1110": {
        # CK3 1.19.0.6 played-character smallpox recovery. Recovery, immunity
        # and treatment cleanup are already applied before the modal opens;
        # the one authored option is only an acknowledgement. This treatment
        # path carries the epidemic, disease, physician and player-patient
        # scopes unchanged from health.1010.
        "date_raw": 53344008,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "sick_character": 29037,
        },
        "unique_character_scope_excludes": {
            "physician": (29037,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "physician": "character",
            "sick_character": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "disease_type",
            "physician",
            "sick_character",
        ),),
        "saved_scope_count": 4,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "health.1112": {
        # CK3 1.19.0.6 played-character measles recovery. Disease removal,
        # permanent measles immunity and treatment cleanup are all applied in
        # immediate before this modal opens. The only authored option merely
        # exposes those completed effects in a tooltip; the event's closing
        # 5-percent blindness roll is unconditional and cannot be avoided by
        # another route. Bind the exact epidemic treatment carry before the
        # acknowledgement.
        "date_raw": 53333688,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "sick_character": 32904,
        },
        "unique_character_scope_excludes": {
            "physician": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "physician": "character",
            "sick_character": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "disease_type",
            "physician",
            "sick_character",
        ),),
        "saved_scope_count": 4,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "health.1001": {
        # Vanilla generic-illness diagnosis. The disease is applied in the
        # immediate block before the window opens, so no visible option can
        # avoid that state change. The physician-present projection exposes
        # authored treatment options 4/5 plus authored option 7; safe
        # treatment (native 3) is the least disruptive survival-preserving
        # route. R196 captured the exact no-physician projection: only the
        # sick character and disease flag are saved, and native options 0/6
        # are visible. Native 0 starts the delayed health.3001 physician-search
        # flow; choose it instead of native 6's no-treatment route to preserve
        # the character-bound Phase2 acceptance path.
        "date_raw": 53175480,
        "root_character_id": 29037,
        "character_scopes": {
            "sick_character": 29037,
        },
        "unique_character_scope_excludes": {
            "physician": (29037,),
        },
        "scope_types": {
            "disease_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "physician",
            "sick_character",
            "disease_type",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 7,
        "native_option_indices": (3, 4, 6),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": ({
            "saved_scope_name_sets": ((
                "sick_character",
                "disease_type",
            ),),
            "saved_scope_count": 2,
            "unique_character_scope_excludes": {},
            "option_count": 2,
            "snapshot_option_count": 7,
            "native_option_indices": (0, 6),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
        },),
    },
    "health.1015": {
        # CK3 1.19.0.6 played-character measles contraction through an
        # epidemic. Disease application and measles immunity happen before
        # the modal opens. This physician-present frame exposes safe, risky,
        # and no-treatment routes; native 3 is the survival-preserving safe
        # treatment and intentionally continues to the existing .3103/.3104
        # treatment-result contracts. Epidemic immunity makes a second
        # occurrence unreachable for this frozen played character.
        "date_raw": 53331888,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "sick_character": 32904,
        },
        "unique_character_scope_excludes": {
            "physician": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "physician": "character",
            "sick_character": "character",
            "new_memory": "character_memory",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "disease_type",
            "physician",
            "sick_character",
            "new_memory",
        ),),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 8,
        "native_option_indices": (3, 4, 6),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "health.3001": {
        # Exact delayed physician-search result opened by a no-physician
        # diagnosis route. Vanilla authored five branches, but the reviewed
        # frames have only the high-skill candidate, low-skill candidate, and
        # decline branches visible (native 1/2/4). R416 proved that health.1006
        # legally carries epidemic/new_memory into this same projection; keep
        # that six-scope source shape as an explicit variant. Native 1 hires
        # the high-skill candidate and is the strongest source-authored route
        # for preserving the sick acceptance owner; native 4 leaves that owner
        # untreated.
        "date_raw": 53176968,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "sick_character": 32904,
            "high_skill_option": 49718,
            "low_skill_option": 36369,
        },
        "character_scope_differs_from": {
            "high_skill_option": ("sick_character", "low_skill_option"),
            "low_skill_option": ("sick_character", "high_skill_option"),
        },
        "scope_types": {
            "disease_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sick_character",
            "disease_type",
            "high_skill_option",
            "low_skill_option",
        ),),
        "saved_scope_count": 4,
        "scope_variants": ({
            "scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "new_memory": "character_memory",
            },
            "saved_scope_names": (
                "epidemic",
                "disease_type",
                "sick_character",
                "new_memory",
                "high_skill_option",
                "low_skill_option",
            ),
            "saved_scope_count": 6,
        },),
        "option_count": 3,
        "snapshot_option_count": 5,
        "native_option_indices": (1, 2, 4),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "health.3101": {
        # R198 exact treatment picker opened immediately after health.3001
        # hired the high-skill candidate. Vanilla authors safe, risky, mystic,
        # and no-treatment branches; the physician is not a mystic here, so
        # native 2 is hidden and the rendered projection is 0/1/3. The
        # physician alias must resolve to the exact high-skill candidate from
        # the preceding search. Select native 0's safe treatment to preserve
        # the sick acceptance owner without the risky branch's harsher range.
        "date_raw": 53177016,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "sick_character": 32904,
            "high_skill_option": 49718,
            "low_skill_option": 36369,
            "physician": 49718,
        },
        "character_scope_matches_any": {
            "physician": ("high_skill_option",),
        },
        "character_scope_differs_from": {
            "high_skill_option": ("sick_character", "low_skill_option"),
            "low_skill_option": ("sick_character", "high_skill_option"),
        },
        "scope_types": {
            "disease_type": "flag",
            "background_terrain_scope": "province",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sick_character",
            "disease_type",
            "high_skill_option",
            "low_skill_option",
            "physician",
            "background_terrain_scope",
        ),),
        "saved_scope_count": 6,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 3),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "health.3103": {
        # R199 exact safe-treatment success result opened by health.3101.
        # Vanilla applies treatment modifiers and informs relatives in the
        # immediate block before this window is presented; its sole authored
        # option is only an acknowledgement. The hired physician, preceding
        # high-skill candidate, and result portrait must remain one character,
        # while the patient and treatment picker both remain the played root.
        "date_raw": 53177016,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "sick_character": 32904,
            "high_skill_option": 49718,
            "low_skill_option": 36369,
            "physician": 49718,
            "treatment_picker": 32904,
            "portrait": 49718,
        },
        "character_scope_matches_any": {
            "physician": ("high_skill_option", "portrait"),
            "high_skill_option": ("physician", "portrait"),
            "portrait": ("physician", "high_skill_option"),
        },
        "character_scope_differs_from": {
            "high_skill_option": ("sick_character", "low_skill_option"),
            "low_skill_option": ("sick_character", "high_skill_option"),
        },
        "scope_types": {
            "disease_type": "flag",
            "background_terrain_scope": "province",
            "treatment": "flag",
            "outcome": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "sick_character",
            "disease_type",
            "high_skill_option",
            "low_skill_option",
            "physician",
            "background_terrain_scope",
            "treatment_picker",
            "treatment",
            "outcome",
            "portrait",
        ),),
        "saved_scope_count": 10,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            # R332 entered the same safe-treatment success from an existing
            # physician path, so the prior recruitment event's high/low
            # candidate scopes were absent. The result event still authors
            # only one acknowledgement. Bind the exact eight-scope carry,
            # including physician == portrait and both player aliases.
            "saved_scope_names": (
                "physician",
                "sick_character",
                "disease_type",
                "treatment_picker",
                "treatment",
                "outcome",
                "portrait",
                "background_terrain_scope",
            ),
            "character_scopes": {
                "sick_character": 32904,
                "treatment_picker": 32904,
            },
            "unique_character_scope_excludes": {
                "physician": (32904,),
                "portrait": (32904,),
            },
            "character_scope_matches_any": {
                "physician": ("portrait",),
                "portrait": ("physician",),
            },
            "character_scope_differs_from": {
                "physician": ("sick_character", "treatment_picker"),
                "portrait": ("sick_character", "treatment_picker"),
            },
            "scope_types": {
                "physician": "character",
                "disease_type": "flag",
                "treatment": "flag",
                "outcome": "flag",
                "portrait": "character",
                "background_terrain_scope": "province",
            },
            "saved_scope_count": 8,
        },),
    },
    "health.3104": {
        # Vanilla safe-treatment failure opened immediately by health.1001's
        # conservative treatment branch. The treatment outcome and modifiers
        # are applied in immediate before this result window; option 1 is the
        # only acknowledgement without imprisonment or execution of the
        # physician. Bind the complete R103 live scope and option shape before
        # dismissing it.
        "date_raw": 53175480,
        "root_character_id": 29037,
        "character_scopes": {
            "sick_character": 29037,
            "treatment_picker": 29037,
        },
        "unique_character_scope_excludes": {
            "physician": (29037,),
        },
        "character_scope_matches_any": {
            "physician": ("portrait",),
        },
        "scope_types": {
            "disease_type": "flag",
            "treatment": "flag",
            "outcome": "flag",
            "background_terrain_scope": "province",
        },
        "boolean_scopes": (),
        "saved_scope_count": 8,
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "option_variants": ({
            # R369 entered the same failure result from the epidemic-aware
            # measles treatment path. Vanilla retained epidemic/new_memory,
            # while the punishment options were not available, leaving only
            # native option 0. Couple that exact ten-scope carry to the
            # one-button projection so neither shape is admitted separately.
            "option_count": 1,
            "snapshot_option_count": 3,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "saved_scope_name_sets": ((
                "epidemic",
                "disease_type",
                "physician",
                "sick_character",
                "new_memory",
                "treatment_picker",
                "treatment",
                "outcome",
                "portrait",
                "background_terrain_scope",
            ),),
            "saved_scope_count": 10,
            "scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "physician": "character",
                "sick_character": "character",
                "new_memory": "character_memory",
                "treatment_picker": "character",
                "treatment": "flag",
                "outcome": "flag",
                "portrait": "character",
                "background_terrain_scope": "province",
            },
        },),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "health.1101": {
        # Vanilla recovery from generic illness. The immediate block has
        # already removed the ill trait and treatment state; the sole option
        # only exposes that completed removal as a tooltip. Bind the complete
        # R103 recovery payload before acknowledging it.
        "date_raw": 53183712,
        "root_character_id": 29037,
        "character_scopes": {
            "sick_character": 29037,
        },
        "unique_character_scope_excludes": {
            "physician": (29037,),
        },
        "scope_types": {
            "disease_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "physician",
            "sick_character",
            "disease_type",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            # R200 exact manager-recovery frame after the newly hired court
            # physician ceased to be retained in this recovery notification.
            # The illness has already been removed in immediate; the same
            # single acknowledgement remains safe to submit. Accept this only
            # for the exact two-scope projection and explicitly clear the
            # physician uniqueness requirement inherited from the base frame.
            "saved_scope_names": (
                "sick_character",
                "disease_type",
            ),
            "scope_types": {
                "disease_type": "flag",
            },
            "unique_character_scope_excludes": {},
            "saved_scope_count": 2,
        },),
    },
    "health.1006": {
        # Vanilla consumption diagnosis. The disease is applied in immediate,
        # so the option only controls treatment. Without a physician, start the
        # source-authored physician search instead of taking no treatment. The
        # retained R97 physician projection still selects safe treatment.
        "date_raw": 53168904,
        "root_character_id": 29037,
        "character_scopes": {
            "sick_character": 29037,
        },
        "unique_character_scope_excludes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "new_memory": "character_memory",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "disease_type",
            "sick_character",
            "new_memory",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 7,
        "native_option_indices": (0, 6),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "scope_variants": ({
            "unique_character_scope_excludes": {
                "physician": (29037,),
            },
            "scope_types": {
                "epidemic": "epidemic",
                "disease_type": "flag",
                "physician": "character",
                "new_memory": "character_memory",
            },
            "saved_scope_names": (
                "epidemic",
                "disease_type",
                "physician",
                "sick_character",
                "new_memory",
            ),
            "saved_scope_count": 5,
        },),
        "option_variants": ({
            "option_count": 3,
            "snapshot_option_count": 7,
            "native_option_indices": (3, 4, 6),
            "selected_option_number": 4,
            "selected_native_option_index": 3,
        },),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.0110": {
        # Exact-build R334/R375 post-epidemic recovery prompt. The epidemic
        # scope is always inherited from the caller. new_preferred_capital is
        # saved only when the immediate block finds an eligible formerly
        # infected duchy capital, so both exact scope sets are source-valid.
        # The observed projection hides native 0; native 2 avoids treasury or
        # gold spending and relocation while applying the weaker recovery.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
        },
        "optional_scope_types": {
            "new_preferred_capital": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            ("epidemic",),
            ("epidemic", "new_preferred_capital"),
        ),
        "saved_scope_counts": (1, 2),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.5001": {
        # R337 exact minor-epidemic supply request. Both authored routes are
        # terminal: native 0 spends minor gold, gains legitimacy, installs the
        # positive supplies modifier and improves the messenger's opinion;
        # native 1 installs the negative plight-ignored modifier. Bind both
        # epidemic aliases, the affected county and the two source-selected
        # character scopes before taking the source-authored relief route.
        "date_raw": 53225904,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "courtier": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "epidemic_county": "landed_title",
            "province_owner": "character",
            "courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "epidemic_county",
            "province_owner",
            "courtier",
        ),),
        "saved_scope_count": 5,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "epidemic_events.1020": {
        # R366 exact miasma-flower proposal. Both authored routes terminate
        # immediately. Native 0 spends only minor treasury, gains legitimacy
        # and installs the positive county modifier; native 1 loses legitimacy
        # and can add trait-dependent stress. Bind both epidemic aliases, the
        # selected province/county and the non-player proposer before taking
        # the deterministic positive route. The vanilla five-year cooldown
        # permits a later recurrence, so this contract is deliberately not
        # capped to the first product-window occurrence.
        "date_raw": 53359632,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "miasma_courtier": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_province": "province",
            "epidemic_scope": "epidemic",
            "epidemic_county": "landed_title",
            "miasma_courtier": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_province",
            "epidemic_scope",
            "epidemic_county",
            "miasma_courtier",
        ),),
        "saved_scope_count": 5,
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.1050": {
        # R293 exact plague-cult warning. Vanilla has already selected the
        # active epidemic and court chaplain before the window opens. Native
        # option 0 deterministically suppresses the cult and reduces epidemic
        # travel danger; native option 1 can fail into the cult modifier, and
        # native option 2 always creates it. Bind the two epidemic scopes, the
        # live chaplain, and the complete 0/1/2 projection before choosing the
        # deterministic containment branch.
        "date_raw": 53243952,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "chaplain": 29889,
        },
        "unique_character_scope_excludes": {
            "chaplain": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "chaplain",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}


# The 34 records below predate the portable event registry and originally
# carried exact dates and character IDs from one acceptance campaign.  Keep
# those values as observation evidence, but publish only player-relative
# contracts so another save, operator, or machine can reuse them.
_MANAGER_A_LEGACY_GROUPS: Final[
    tuple[tuple[str, dict[str, dict[str, object]]], ...]
] = (
    ("befriend", _LEGACY_MANAGER_BEFRIEND_TIMELINE_CONTRACTS),
    ("birth", _LEGACY_MANAGER_BIRTH_TIMELINE_CONTRACTS),
    ("chancellor", _LEGACY_MANAGER_CHANCELLOR_TIMELINE_CONTRACTS),
    ("council_claim", _LEGACY_MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS),
    ("court", _LEGACY_MANAGER_COURT_TIMELINE_CONTRACTS),
    ("death", _LEGACY_MANAGER_DEATH_TIMELINE_CONTRACTS),
    ("debate", _LEGACY_MANAGER_DEBATE_TIMELINE_CONTRACTS),
    ("health_aging", _LEGACY_MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS),
    ("health", _LEGACY_MANAGER_HEALTH_TIMELINE_CONTRACTS),
)

_LEGACY_BINDING_KEYS: Final = (
    "date_raw",
    "date_raw_range",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)


def _clone_record_value(value: object) -> object:
    """Clone the JSON-shaped record without changing tuple/list semantics."""

    if isinstance(value, dict):
        return {str(key): _clone_record_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_clone_record_value(item) for item in value)
    if isinstance(value, list):
        return [_clone_record_value(item) for item in value]
    return value


def _legacy_binding_fields(contract: dict[str, object]) -> dict[str, object]:
    """Extract the removed campaign binding verbatim for migration review."""

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


def _neutralize_contract_value(value: object, legacy_root: object) -> object:
    """Remove one campaign's dates/IDs while preserving role relations."""

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

    neutral: dict[str, object] = {}
    for key, item in value.items():
        if key in {"date_raw", "date_raw_range"}:
            continue
        if key == "root_character_id":
            neutral[key] = PLAYER_SENTINEL
            continue
        if key == "character_scopes":
            if not isinstance(item, dict):
                raise TypeError("character_scopes must be a dictionary")
            neutral[key] = {
                str(scope_name): PLAYER_SENTINEL
                for scope_name, character_id in item.items()
                if character_id in {legacy_root, PLAYER_SENTINEL}
            }
            continue
        if key == "unique_character_scope_excludes":
            if not isinstance(item, dict):
                raise TypeError(
                    "unique_character_scope_excludes must be a dictionary"
                )
            exclusions: dict[str, tuple[object, ...]] = {}
            for scope_name, raw_ids in item.items():
                if not isinstance(raw_ids, (tuple, list)):
                    raise TypeError(
                        "unique character scope exclusions must be a sequence"
                    )
                portable_ids = tuple(
                    PLAYER_SENTINEL
                    for character_id in raw_ids
                    if character_id in {legacy_root, PLAYER_SENTINEL}
                )
                if portable_ids:
                    exclusions[str(scope_name)] = portable_ids
            neutral[key] = exclusions
            continue
        neutral[str(key)] = _neutralize_contract_value(item, legacy_root)
    return neutral


def _neutralize_contract(contract: dict[str, object]) -> dict[str, object]:
    legacy_root = contract.get("root_character_id")
    if legacy_root == PLAYER_SENTINEL:
        cloned = _clone_record_value(contract)
        if not isinstance(cloned, dict):  # pragma: no cover - mapping input guard
            raise TypeError("cloned manager-A contract must be a dictionary")
        return cloned
    if legacy_root not in {29037, 32904}:
        raise ValueError(f"unexpected manager-A legacy root: {legacy_root!r}")
    neutral = _neutralize_contract_value(contract, legacy_root)
    if not isinstance(neutral, dict):  # pragma: no cover - mapping input guard
        raise TypeError("neutralized manager-A contract must be a dictionary")
    neutral.setdefault("date_policy", "product-observation-window")
    return neutral


def _neutralize_group(
    contracts: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {
        event_key: _neutralize_contract(contract)
        for event_key, contract in contracts.items()
    }


MANAGER_VANILLA_OBSERVATIONS_A: Final[dict[str, dict[str, object]]] = {
    event_key: {
        "exemplars": [{
            "run": "legacy-migrated",
            "kind": "legacy-live-binding",
            "review_kind": "migration-only",
            **_legacy_binding_fields(contract),
        }],
    }
    for _source_name, contracts in _MANAGER_A_LEGACY_GROUPS
    for event_key, contract in contracts.items()
    if contract.get("root_character_id") in {29037, 32904}
    and event_key not in {"health.1006", "health.3001"}
}

MANAGER_BEFRIEND_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_BEFRIEND_TIMELINE_CONTRACTS
)
MANAGER_BIRTH_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_BIRTH_TIMELINE_CONTRACTS
)
MANAGER_CHANCELLOR_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_CHANCELLOR_TIMELINE_CONTRACTS
)
MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS
)
MANAGER_COURT_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_COURT_TIMELINE_CONTRACTS
)
MANAGER_DEATH_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_DEATH_TIMELINE_CONTRACTS
)
MANAGER_DEBATE_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_DEBATE_TIMELINE_CONTRACTS
)
MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS
)
MANAGER_HEALTH_TIMELINE_CONTRACTS: Final = _neutralize_group(
    _LEGACY_MANAGER_HEALTH_TIMELINE_CONTRACTS
)


# Migrated from tools/zg361_phase2_promotion_manager_holy_war_contracts.py
MANAGER_HOLY_WAR_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "great_holy_war.0011": {
        # CK3 1.19.0.6 fires this flavor notice for every player after the
        # hidden awakening event has already unlocked the religion's GHW
        # variable. All five authored options are effect-free and share only
        # an after-tooltip. R342 observed the hostile-faith projection where
        # authored option 4/native 3 is the sole visible acknowledgement.
        # Keep faith opaque and bind only the war-notice data required by the
        # project's explicitly allowed holy-war exception.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "ghw_first_sponsor": (PLAYER_SENTINEL,),
            "background_temple_scope": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "ghw_first_sponsor": ("background_temple_scope",),
            "background_temple_scope": ("ghw_first_sponsor",),
        },
        "scope_types": {
            "awakening_faith": "faith",
            "ghw_first_sponsor": "character",
            "background_temple_scope": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "awakening_faith",
            "ghw_first_sponsor",
            "background_temple_scope",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "snapshot_option_count": 5,
        "native_option_indices": (3,),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


def _aggregate_contract_groups(
    *groups: tuple[str, dict[str, dict[str, object]]],
) -> dict[str, dict[str, object]]:
    """Combine disjoint source groups and reject every duplicate key."""

    combined: dict[str, dict[str, object]] = {}
    for source_name, contracts in groups:
        duplicates = sorted(set(combined).intersection(contracts))
        if duplicates:
            joined = ", ".join(duplicates)
            raise ValueError(
                f"duplicate vanilla event contract key(s) from {source_name}: {joined}"
            )
        combined.update(contracts)
    return combined


MANAGER_VANILLA_TIMELINE_CONTRACTS_A: Final[
    dict[str, dict[str, object]]
] = _aggregate_contract_groups(
    ("befriend", MANAGER_BEFRIEND_TIMELINE_CONTRACTS),
    ("birth", MANAGER_BIRTH_TIMELINE_CONTRACTS),
    ("chancellor", MANAGER_CHANCELLOR_TIMELINE_CONTRACTS),
    ("council_claim", MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS),
    ("court", MANAGER_COURT_TIMELINE_CONTRACTS),
    ("death", MANAGER_DEATH_TIMELINE_CONTRACTS),
    ("debate", MANAGER_DEBATE_TIMELINE_CONTRACTS),
    ("health_aging", MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS),
    ("health", MANAGER_HEALTH_TIMELINE_CONTRACTS),
    ("holy_war", MANAGER_HOLY_WAR_TIMELINE_CONTRACTS),
)


__all__ = [
    "MANAGER_BEFRIEND_TIMELINE_CONTRACTS",
    "MANAGER_BIRTH_TIMELINE_CONTRACTS",
    "MANAGER_CHANCELLOR_TIMELINE_CONTRACTS",
    "MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS",
    "MANAGER_COURT_TIMELINE_CONTRACTS",
    "MANAGER_DEATH_TIMELINE_CONTRACTS",
    "MANAGER_DEBATE_TIMELINE_CONTRACTS",
    "MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS",
    "MANAGER_HEALTH_TIMELINE_CONTRACTS",
    "MANAGER_HOLY_WAR_ANALYSIS",
    "MANAGER_HOLY_WAR_OBSERVATIONS",
    "MANAGER_HOLY_WAR_TIMELINE_CONTRACTS",
    "MANAGER_VANILLA_OBSERVATIONS_A",
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_A",
]
