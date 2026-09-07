#!/usr/bin/env python3
"""Source-reviewed health manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_HEALTH_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
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
        "saved_scope_count": 3,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
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
}
