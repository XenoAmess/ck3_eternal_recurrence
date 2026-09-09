#!/usr/bin/env python3
"""Source-reviewed disease and treatment manager interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_HEALTH_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
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
    "health.3001": {
        # R197 exact delayed physician-search result opened by health.1001's
        # no-physician route. Vanilla authored five branches, but this frame
        # has only the high-skill candidate, low-skill candidate, and decline
        # branches visible (native 1/2/4). Both candidate aliases are exact
        # live character scopes. Native 1 hires the high-skill candidate and
        # is the strongest source-authored route for preserving the sick
        # acceptance owner; native 4 would leave that owner untreated.
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
        # Vanilla consumption diagnosis.  The disease is applied in immediate
        # before the window opens, so no option can avoid that state change.
        # This live frame exposes authored treatment options 4/5 plus authored
        # option 7.  R97 proved that declining treatment lets the played owner
        # die within 27 days and invalidates the character-bound Phase2 path.
        # Authored option 4 is the conservative physician treatment and is the
        # least disruptive branch that preserves a viable acceptance owner.
        "date_raw": 53168904,
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
            "new_memory": "character_memory",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 3,
        "snapshot_option_count": 7,
        "native_option_indices": (3, 4, 6),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "epidemic_events.0110": {
        # R334 exact post-epidemic recovery prompt. The event authored three
        # branches, but the capital-relocation branch (native 0) is absent
        # from the rendered projection; only recovery spending (native 1)
        # and neglect (native 2) are enabled. Native 1 spends campaign gold;
        # native 2 neither relocates the capital nor starts a follow-up chain,
        # and only applies weaker county recovery plus a possible miniscule
        # legitimacy loss. Bind both engine-owned scopes and the exact 1/2
        # projection before taking that bounded, non-religious route.
        "date_raw": 53208120,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "new_preferred_capital": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "new_preferred_capital",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
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
