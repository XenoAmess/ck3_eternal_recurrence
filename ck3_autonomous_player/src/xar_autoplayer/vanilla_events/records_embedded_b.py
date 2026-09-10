"""Second shard of the portable vanilla CK3 timeline interrupt records."""

from __future__ import annotations

from typing import Final

from .registry import PLAYER_SENTINEL


def _optional_scope_name_sets(
    required: tuple[str, ...], optional: tuple[str, ...]
) -> tuple[tuple[str, ...], ...]:
    """Expand one finite optional-scope envelope to exact name sets."""

    return tuple(
        required
        + tuple(
            name
            for index, name in enumerate(optional)
            if mask & (1 << index)
        )
        for mask in range(1 << len(optional))
    )


EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "epidemic_events.5007": {
        # CK3 1.19.0.6 plague-yearly accusation against a court herbalist.
        # Native option 0 is visible only when root has a related lifestyle
        # trait. Native option 1 brands the herbalist a witch and imprisons
        # them; native option 2 only applies the authored opinion/stress and
        # possible potential-friend relation, making it the least invasive
        # available route in either exact projection. Bind the independently
        # selected accuser and herbalist before taking that terminal route.
        "date_raw": 53270256,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "herbalist": (32904,),
            "accuser": (32904,),
        },
        "character_scope_differs_from": {
            "herbalist": ("accuser",),
            "accuser": ("herbalist",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "herbalist": "character",
            "accuser": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "herbalist",
            "accuser",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (1, 2),
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
    "epidemic_events.5009": {
        # CK3 1.19.0.6 plague-market herbal-sachet offer. Native routes 0/1
        # transfer the generated artifact, spend gold and install long-lived
        # modifiers; native 2 still installs the protection modifier. Native
        # 3 buys nothing and only applies trait-dependent stress before the
        # merchant cleanup shared by every route. Bind the generated artifact
        # metadata and merchant/owner/creator identity before selecting it.
        # R372 then observed a second legal delivery after the source-defined
        # ten-year cooldown, so this reusable contract is repeatable rather
        # than bound to the original campaign date or player ID.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "merchant": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "owner": ("merchant",),
            "creator": ("merchant",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "merchant": "character",
            "flower_species": "flag",
            "owner": "character",
            "creator": "character",
            "random_quality_bonus": "value",
            "quality": "value",
            "wealth": "value",
            "location": "province",
            "newly_created_artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "merchant",
            "flower_species",
            "owner",
            "creator",
            "random_quality_bonus",
            "quality",
            "wealth",
            "location",
            "newly_created_artifact",
        ),),
        "saved_scope_count": 11,
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
                "option_count": 4,
                "native_option_indices": (0, 1, 2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "learn_language_outcome.1001": {
        # CK3 1.19.0.6 response after another character successfully learns
        # the player's language. Both routes alter mutual opinion/progress;
        # native 0 creates positive respect/friend progress, while native 1
        # creates insult/rival progress plus player prestige. Neither starts
        # a follow-up event, so take the non-hostile positive response after
        # binding the completed scheme, dynamic owner and played target.
        "date_raw": 53257296,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "target": 32904,
        },
        "unique_character_scope_excludes": {
            "owner": (32904,),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
        },
        "boolean_scopes": ("scheme_successful",),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "scheme_successful",
        ),),
        "saved_scope_count": 5,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "hostile_scheme_discovery.2001": {
        # CK3 1.19.0.6 notification that a hostile scheme at another
        # character in the player's court has gained a discovery breach.
        # The sole authored option exposes that already-discovered scheme and
        # notifies its dynamic owner; there is no acknowledgement-only or
        # alternate route. Bind the source-authored scheme/owner/target/
        # spymaster frame, the generic artifact slot and discovery value
        # before selecting that required route. The dynamic characters must
        # remain distinct non-player parties in this observed lineage.
        "date_raw": 53216088,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "owner": (32904,),
            "target": (32904,),
            "spymaster": (32904,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "spymaster"),
            "target": ("owner", "spymaster"),
            "spymaster": ("owner", "target"),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "spymaster": "character",
            "discovery_chance": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "spymaster",
            "discovery_chance",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.1001": {
        # CK3 1.19.0.6 administrative-eunuch story opener. Its immediate
        # block has already employed and upgraded the dynamic eunuch, granted
        # the starting influence bonus and, for a generated-family lineage,
        # created the parent/family/title scopes before the modal is shown.
        # Native option 0 additionally replaces/grants the chief-eunuch court
        # position and changes opinion; native option 1 has no effect. Bind
        # either the legacy six-scope frame or R374's exact generated-family
        # twenty-scope frame and choose the terminal no-op route. The source
        # has a ten-year cooldown rather than a campaign one-shot gate.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "liege": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "eunuch": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "candidate": ("eunuch",),
        },
        "optional_character_scope_matches_any": {
            "eunuch_father": ("parent",),
            "family_head": ("parent",),
            "new_noble_family_holder": ("family_head",),
            "government_giver": ("family_head",),
            "noble_family_head": ("family_head",),
        },
        "scope_types": {
            "eunuch": "character",
            "origin": "landed_title",
            "story": "story",
            "liege": "character",
            "candidate": "character",
            "modifier_type": "flag",
        },
        "optional_scope_types": {
            "origin_liege": "character",
            "parent_min_age": "value",
            "parent_max_age": "value",
            "parent": "character",
            "eunuch_father": "character",
            "count": "value",
            "min_age": "value",
            "max_age": "value",
            "newly_created_character": "character",
            "family_head": "character",
            "new_noble_family_holder": "character",
            "government_giver": "character",
            "new_title": "landed_title",
            "noble_family_head": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "eunuch",
                "origin",
                "story",
                "liege",
                "candidate",
                "modifier_type",
            ),
            (
                "origin_liege",
                "origin",
                "eunuch",
                "parent_min_age",
                "parent_max_age",
                "parent",
                "eunuch_father",
                "count",
                "min_age",
                "max_age",
                "newly_created_character",
                "story",
                "family_head",
                "new_noble_family_holder",
                "government_giver",
                "new_title",
                "noble_family_head",
                "liege",
                "candidate",
                "modifier_type",
            ),
        ),
        "saved_scope_counts": (6, 20),
        "option_count": 2,
        "snapshot_option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (0, 1),
                "selected_option_number": 2,
                "selected_native_option_index": 1,
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
    "ep3_story_cycle_admin_eunuch.2050": {
        # CK3 1.19.0.6 eunuch-story boon proposal. The immediate block has
        # already selected the boon and any associated target. Option 1
        # applies that external boon and upgrades the story; option 2 only
        # applies the authored story downgrade/stress result. Bind the exact
        # R295 no-target frame and the source-authored target branch shapes,
        # then choose option 2 so the incidental story cannot mutate taxes,
        # succession, hooks or imprisonment state.
        "date_raw": 53245848,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "boon_victim": (32904,),
            "boon_target": (32904,),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "eunuch_boon": "flag",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "boon_faction": "faction",
            "boon_victim": "character",
            "boon_title": "landed_title",
            "boon_target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + boon_branch
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "eunuch_boon",
                ),
                ("protege", "student", "rival"),
            )
            for boon_branch in (
                (),
                ("boon_victim",),
                ("boon_faction", "boon_victim"),
                ("boon_title", "boon_victim", "boon_target"),
            )
        ),
        "saved_scope_counts": (5, 6, 7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2051": {
        # CK3 1.19.0.6 eunuch-story secret proposal. The immediate block may
        # already reveal the selected secret to the eunuch. Native option 0
        # also reveals it to the player, upgrades the eunuch story and harms
        # the dynamic owner's opinion. Native option 1 does not reveal the
        # secret to the player or start a follow-up event; it only applies the
        # authored downgrade/opinion/stress result. The native immediate block
        # saves secret_target only when the selected secret has one. The
        # shared story frame independently carries protege/student/rival when
        # those roles exist. Bind their finite optional envelope before
        # choosing that narrower route.
        "date_raw": 53223312,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "secret_owner": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "secret_target": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("secret_owner",),
            "secret_owner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "secret": "secret",
            "secret_owner": "character",
        },
        "optional_scope_types": {
            "secret_target": "character",
            "protege": "character",
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "secret",
                "secret_owner",
            ),
            ("protege", "student", "rival", "secret_target"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2052": {
        # CK3 1.19.0.6 hostile-scheme proposal. Native option 0 exposes the
        # selected scheme, upgrades the eunuch story and upsets its owner.
        # Native option 1 leaves the hostile scheme untouched and applies only
        # the authored story downgrade/opinion/stress result. Choose that
        # narrower terminal route after binding the exact combinations of the
        # story's optional protege/student/rival roles and the scheme's
        # optional defender target.
        # Prove the owner is neither player nor eunuch, and any target is also
        # neither player nor eunuch, before selecting it. The event has no
        # cooldown or one-shot flag and remains eligible while the story and
        # a qualifying hostile scheme both exist, so validate every delivery
        # independently inside the bounded product observation window.
        "date_raw": 53236512,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "scheme_owner": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
            "scheme_target": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("scheme_owner",),
            "scheme_owner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "scheme_target": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "scheme": "scheme",
            "scheme_owner": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "scheme_target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "scheme",
                "scheme_owner",
            ),
            ("protege", "student", "rival", "scheme_target"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2060": {
        # CK3 1.19.0.6 court-position demand from the story eunuch. Native
        # option 0 assigns the generated position and can remove its existing
        # holder. Native option 1 refuses the demand and applies only the
        # authored story downgrade, opinion and stress result. The shared
        # story effect independently carries protege/student/rival when they
        # exist, while the position generator independently saves old_holder.
        # Bind the finite optional envelope and choose the refusing route.
        "date_raw": 53225016,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("eunuch",),
            "eunuch": ("candidate",),
        },
        "optional_character_scope_differs_from": {
            "old_holder": ("candidate",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "candidate": "character",
            "liege": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "old_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "candidate",
                "liege",
            ),
            ("protege", "student", "rival", "old_holder"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2061": {
        # CK3 1.19.0.6 family court-position demand. The immediate block moves
        # a dynamic close family member to the player's court and runs the
        # same position generator as .2060. Native option 0 appoints that
        # person and can remove an old holder. Native option 1 refuses, then
        # returns the person to the eunuch's house head or the pool. Bind the
        # exact family/candidate alias and finite shared-story envelope before
        # taking that narrower refusal route.
        "date_raw": 53239872,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "positioner": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("positioner",),
            "positioner": ("candidate",),
        },
        "character_scope_differs_from": {
            "eunuch": ("positioner",),
            "positioner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "old_holder": ("candidate",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "positioner": "character",
            "candidate": "character",
            "liege": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "old_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "positioner",
                "candidate",
                "liege",
            ),
            ("protege", "student", "rival", "old_holder"),
        ),
        "saved_scope_counts": (7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2040": {
        # CK3 1.19.0.6 eunuch council-seat demand. The immediate block has
        # already bound the player as petition liege, the eunuch as petition
        # vassal and, only when the selected seat is occupied, its incumbent
        # as second_party. Native option 0 fires that incumbent, installs and
        # protects the eunuch, and upgrades the story. Native option 1 keeps
        # the council roster intact and only applies the authored downgrade,
        # opinion and stress. Bind the finite shared-story/incumbent envelope
        # before taking the narrower refusal route.
        "date_raw": 53258328,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "petition_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "petition_vassal": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "second_party": (32904,),
        },
        "character_scope_matches_any": {
            "eunuch": ("petition_vassal",),
            "petition_vassal": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "second_party": ("eunuch", "petition_vassal"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "petition_liege": "character",
            "petition_vassal": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "second_party": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "petition_liege",
                "petition_vassal",
            ),
            ("protege", "student", "rival", "second_party"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2041": {
        # CK3 1.19.0.6 eunuch-family council-seat petition. The immediate
        # block has already selected/recruited the family candidate and saved
        # both the candidate and any incumbent councillor. Native option 0
        # fires the incumbent, assigns the family candidate, blocks firing
        # them and upgrades the eunuch story. Native option 1 leaves the
        # council roster intact and applies only the authored downgrade plus
        # opinion/stress. Bind the candidate alias and incumbent before taking
        # that narrower refusal route. Vanilla applies a five-year event
        # cooldown rather than a campaign-global one-shot gate, so validate
        # every occurrence inside the product observation window.
        "date_raw": 53239224,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "petition_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "councillor": (32904,),
            "petition_vassal": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "protege": (32904,),
            "student": (32904,),
            "rival": (32904,),
            "second_party": (32904,),
        },
        "character_scope_matches_any": {
            "councillor": ("petition_vassal",),
            "petition_vassal": ("councillor",),
        },
        "character_scope_differs_from": {
            "councillor": ("eunuch",),
            "petition_vassal": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "second_party": ("councillor", "petition_vassal"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "petition_liege": "character",
            "councillor": "character",
            "petition_vassal": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "second_party": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "petition_liege",
                "councillor",
                "petition_vassal",
            ),
            ("protege", "student", "rival", "second_party"),
        ),
        "saved_scope_counts": (7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2021": {
        # CK3 1.19.0.6 eunuch-family governorship request. Native option 0
        # transfers a title or changes its appointment investment, mutates
        # the title heir's opinion and adds a five-year family-boon flag.
        # Native option 1 performs none of those roster/title changes and has
        # no follow-up event; it only applies the story downgrade plus
        # opinion/stress. Bind the selected family member, title and explicit
        # non-root heir before taking that narrower refusal route.
        "date_raw": 53227128,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "governor": (32904,),
            "title_heir": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("governor", "title_heir"),
            "governor": ("eunuch", "title_heir"),
            "title_heir": ("eunuch", "governor"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "governor": "character",
            "title": "landed_title",
            "title_heir": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "story",
            "emperor",
            "eunuch",
            "admin_title",
            "governor",
            "title",
            "title_heir",
        ),),
        "saved_scope_count": 7,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.3010": {
        # CK3 1.19.0.6 eunuch-rival story node. The immediate block creates
        # or recruits the dynamic rival, stores it on the story and installs
        # the rivalry before the modal opens. Its sole option contains only
        # show_as_tooltip for that already-applied relation. Bind the complete
        # source-authored frame before acknowledging it. The origin helper
        # chooses either a neighboring top-liege realm owner or root as its
        # origin_liege; only its character type is visible through this bridge.
        # The shared story frame can independently retain protege/student.
        "date_raw": 53229168,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("rival",),
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "origin_liege": "character",
            "origin": "landed_title",
            "rival": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "origin_liege",
                "origin",
                "rival",
            ),
            ("protege", "student"),
        ),
        "saved_scope_counts": (7, 8, 9),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.3001": {
        # CK3 1.19.0.6 eunuch-student node. Before the modal opens, the
        # immediate block has already selected/created and recruited the
        # student, installed the mentor relation, granted two skill points and
        # stored the student on the story. The sole authored option is empty.
        # The origin helper runs only when a new student must be created. In
        # that branch origin_liege is either the eunuch-scope fallback or a
        # dynamic neighboring top-liege owner, and origin accompanies it.
        # Bind the exact create/existing-student frames, then acknowledge the
        # already-applied result.
        "date_raw": 53243184,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "student": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
            "origin_liege": (32904,),
        },
        "character_scope_differs_from": {
            "student": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "student": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "rival": "character",
            "origin_liege": "character",
            "origin": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + origin_names
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "student",
                ),
                ("protege", "rival"),
            )
            for origin_names in ((), ("origin_liege", "origin"))
        ),
        "saved_scope_counts": (5, 6, 7, 8, 9),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.5010": {
        # CK3 1.19.0.6 upset-family node. Its immediate block has already
        # selected a dynamic family rival, installed the eunuch rivalry and
        # stored that character in the story's upset-courtiers list. Native
        # option 0 adds only authored opinion/stress; native option 1 also
        # downgrades the eunuch story. Choose option 0 to avoid that extra
        # durable story mutation after binding both non-player parties.
        "date_raw": 53230152,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("rival",),
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "rival": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            ("story", "emperor", "eunuch", "admin_title", "rival"),
            ("protege", "student"),
        ),
        "saved_scope_counts": (5, 6, 7),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.4000": {
        # CK3 1.19.0.6 spouse-accusation node. In the observed source shape,
        # native option 1 is hidden because the player does not already know a
        # qualifying lover secret, leaving native options 0 and 2 rendered.
        # Native option 2 imprisons both the spouse and alleged cuckolder and
        # adds tyranny. Choose native option 0's intrigue investigation: it may
        # reveal the actual secret (or report innocence/failure), but avoids
        # the unconditional double imprisonment and tyranny mutation. Bind the
        # complete seven-scope core frame, plus the story effect's optional
        # protege/student roles, and the authored hidden-option gap first.
        "date_raw": 53232552,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
            "spouse": (32904,),
            "cuckolder": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("spouse", "cuckolder"),
            "spouse": ("eunuch", "cuckolder"),
            "cuckolder": ("eunuch", "spouse"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "rival": "character",
            "spouse": "character",
            "cuckolder": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "rival",
                "spouse",
                "cuckolder",
            ),
            ("protege", "student"),
        ),
        "saved_scope_counts": (7, 8, 9),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.4010": {
        # CK3 1.19.0.6 seduction/murder-plot node. Its immediate block has
        # already selected the spouse and eunuch-family seducer and may already
        # have installed their lover relation or placed them in a murder
        # scheme. Native option 0 runs an intrigue duel, while native option 1
        # imprisons all three characters and adds major tyranny. Native option
        # 2 only applies the authored prestige/stress cost. Bind both immediate
        # had-sex aliases, the generated memory/secret and the full story frame
        # before taking that narrow terminal route.
        "date_raw": 53243328,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "spouse": (32904,),
            "seducer": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "protege": (32904,),
            "student": (32904,),
            "rival": (32904,),
            "had_sex_root_character": (32904,),
            "had_sex_with_effect_partner": (32904,),
        },
        "optional_character_scope_matches_any": {
            "had_sex_root_character": ("seducer",),
            "had_sex_with_effect_partner": ("spouse",),
        },
        "character_scope_differs_from": {
            "eunuch": ("spouse", "seducer"),
            "spouse": ("eunuch", "seducer"),
            "seducer": ("eunuch", "spouse"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "spouse": "character",
            "seducer": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "had_sex_root_character": "character",
            "had_sex_with_effect_partner": "character",
            "new_memory": "character_memory",
            "secret": "secret",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + random_branch
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "spouse",
                    "seducer",
                ),
                ("protege", "student", "rival"),
            )
            for random_branch in (
                (),
                (
                    "had_sex_root_character",
                    "had_sex_with_effect_partner",
                    "new_memory",
                    "secret",
                ),
            )
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10, 11, 12, 13),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.5020": {
        # CK3 1.19.0.6 puppet-heir node. The immediate block has already made
        # the selected close-family puppet a friend of the eunuch and stored
        # it on the story. The sole option then grants the ten-year puppet
        # modifier and increases that character's appointment investment.
        # There is no decline route, so acknowledge only the exact source-
        # authored frame while proving the puppet is not the current heir.
        "date_raw": 53235120,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "current_heir": (32904,),
            "puppet": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "current_heir": ("puppet",),
            "puppet": ("current_heir",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "current_heir": "character",
            "puppet": "character",
        },
        "optional_scope_types": {
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "current_heir",
                "puppet",
            ),
            ("student", "rival"),
        ),
        "saved_scope_counts": (6, 7, 8),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.8030": {
        # CK3 1.19.0.6 eunuch-moved terminal. Native option 0 pays for and
        # recruits the departed eunuch; options 1/2 replace the story's eunuch
        # with a valid student/rival. Native option 3 clears both character
        # modifiers and ends the incidental story, with no follow-up event.
        # The shared save-scopes effect may retain protege/student/rival, while
        # the two replacement buttons are independently conditional.
        "date_raw": 53341752,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "emperor": 29037,
        },
        "unique_character_scope_excludes": {
            "eunuch": (29037,),
            "background_throne_room_scope": (29037,),
        },
        "optional_unique_character_scope_excludes": {
            "protege": (29037,),
            "student": (29037,),
            "rival": (29037,),
        },
        "scope_types": {
            "story": "story",
            "eunuch": "character",
            "emperor": "character",
            "admin_title": "landed_title",
            "background_throne_room_scope": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "eunuch",
                "emperor",
                "admin_title",
                "background_throne_room_scope",
            ),
            ("protege", "student", "rival"),
        ),
        "saved_scope_counts": (5, 6, 7, 8),
        "option_count": 4,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (0, 3),
                "snapshot_option_counts": (2, 4),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 3),
                "snapshot_option_counts": (3, 4),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 2, 3),
                "snapshot_option_counts": (3, 4),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "max_occurrences": 1,
    },
    "ep3_interactions_events.0630": {
        # Vanilla governor-removal letter with one option. IMPORTANT: that
        # option executes governor_resignation_title_transfer_effect; it is
        # not a no-op acknowledgement of a previously completed title change.
        # Selecting it removes the played manager's governor position and
        # invalidates the stable manager/direct-vassal roster required by this
        # acceptance scenario.  Recognize the exact frame, preserve it paused,
        # and classify the scenario as invalid instead of mutating gameplay or
        # reporting a product RED.
        "handling_policy": "scenario-invalidating-fail-closed",
        "scenario_invalidation_reason_code": (
            "governor_resignation_title_transfer_breaks_manager_roster"
        ),
        "scenario_invalidation_reason": (
            "the event's only enabled option executes "
            "governor_resignation_title_transfer_effect and removes the "
            "played manager's governor position/direct-vassal roster"
        ),
        "invalidated_precondition": (
            "stable_player_manager_governor_position_and_direct_vassal_roster"
        ),
        # Three generic interaction slots retain their names/type after the
        # referenced characters have gone stale; bind that exact degraded
        # identity shape instead of fabricating character IDs.
        "date_raw": (53147256, 53151600),
        # Two live runs delivered the same single-option interaction
        # letter on different ticks while every semantic field stayed exact.
        "date_raw_range": (53147256, 53151600),
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
        },
        # ``actor`` is the live governor-removal interaction initiator.  The
        # exact source uses it as sender and title-transfer owner, but does
        # not freeze one historical character.  R94 observed 32904 and the
        # later R97 retained lineage observed 36354 after realm turnover.
        # Bind the source invariant (one non-player actor) instead of the
        # first run's incidental ID.
        "unique_character_scope_excludes": {
            "actor": (29037,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {"force_retirement_treasury_cost": "value"},
        "boolean_scopes": ("hook",),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_admin_events.0002": {
        # Vanilla new-governorship notice.  The first two branches install a
        # three-year development modifier or a free-inspection flag; authored
        # option 3 is the bounded acknowledgement with only minuscule stress
        # loss.
        "date_raw": 53147280,
        "root_character_id": 29037,
        "character_scopes": {
            "new_holder": 29037,
        },
        # Both identities come from the title's live previous holder (source
        # line 282), so realm turnover changes the character while preserving
        # the alias.  R97 also arrived through appointment succession and
        # retained two additional typed title scopes that were absent in the
        # earlier transfer shape.
        "unique_character_scope_excludes": {
            "previous_holder": (29037,),
            "previous_governor": (29037,),
        },
        "character_scope_matches_any": {
            "previous_holder": ("previous_governor",),
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "nf_gov_type": "government_type",
            "governor_title": "landed_title",
        },
        "optional_scope_types": {
            "county_title": "landed_title",
            "appointment_succession": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
                "nf_gov_type",
                "governor_title",
                "previous_governor",
            ),
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
                "county_title",
                "nf_gov_type",
                "governor_title",
                "previous_governor",
                "appointment_succession",
            ),
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
                "nf_gov_type",
                "governor_title",
                "previous_governor",
                "appointment_succession",
            ),
        ),
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8060": {
        # Independent vanilla yearly governor event observed after the PIP
        # response on this immutable timeline.  Option 4 performs no scripted
        # resource, modifier, duel or follow-up-event mutation; only its
        # vanilla trait-dependent stress impact remains.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8010": {
        # Independent vanilla governor bargain.  Accept/reverse can exchange
        # hooks, candidacies, influence or gold (the reverse branch also runs
        # an intrigue/diplomacy duel).  Refusal confines the mutation to the
        # typed requesting governor's -10 opinion plus trait-dependent stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor": 29347,
            "their_title_receiver": 30938,
            "title_receiver": 29067,
        },
        "scope_types": {
            "their_title": "landed_title",
            "title": "landed_title",
            "governor_request": "flag",
            "governor_offer": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 7,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8100": {
        # Independent vanilla yearly governor event observed on the same
        # immutable date as .8060 in a different run.  Authored option 3 is
        # hidden for this root, so the three rendered buttons map to native
        # indices 0, 1 and 3.  The final rendered option only retains its
        # vanilla trait-dependent stress impact; the others also mutate
        # appointment investment, influence or a rival relationship.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "target_family_member": 31647,
        },
        # Vanilla chooses both roles with random_* selectors when the event
        # fires.  R28/R49 observed 28598/62537 and 27181/36175 respectively,
        # while the exact role names, types, fixed root-family target and
        # authored option shape remained stable.
        "unique_character_scope_excludes": {
            "governor": (29037, 31647),
            "neighboring_promoted_char": (29037, 31647),
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8110": {
        # Independent vanilla pugnacious-peers event.  No empty branch exists:
        # option 1 spends influence and starts a random duel; option 4 changes
        # influence, merit and both opinions.  Option 2 is the bounded branch,
        # applying only symmetric +/-15 opinion modifiers involving the two
        # typed non-player governors plus trait-dependent stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor_1": 28598,
            "governor_2": 27181,
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 4,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
}


__all__ = ["EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS"]
