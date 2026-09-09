"""Vanilla CK3 timeline interrupt records formerly embedded in the ZG361 runner."""

from __future__ import annotations

from typing import Final


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


EMBEDDED_VANILLA_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "ep3_governor_yearly.8120": {
        # Independent vanilla flood/storm event.  The disaster county loses
        # control/development in immediate regardless of the choice.  Option
        # 1 adds a random stewardship duel and governance/modifier outcome;
        # option 2 spends treasury/gold and adds a county modifier.  Option 3
        # avoids both and is confined to minor piety, a fixed character
        # modifier and trait-dependent stress, so it is the least disruptive
        # route for the promotion-source lineage.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {"disaster_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "bp1_yearly.5725": {
        # Vanilla Khutulun matchmaking invitation.  Exact CK3 1.19.0.6 source
        # gives option 1 a seven-day follow-up chain, while option 2 ends the
        # encounter immediately with only matchmaker opinion/stress effects.
        # Bind both generated character scopes and select the terminal branch
        # so this unrelated yearly story cannot occupy the Phase-2 timeline.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "matchmaker_courtier": 31003,
            "khutulun": 16779972,
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "bp1_yearly.9007": {
        # Independent vanilla doppelganger encounter.  Visible option 1 adds
        # the generated character to court and creates a follow-up story;
        # authored option 2 (murder) is hidden for this non-sadistic frame.
        # Visible option 2 maps to native index 2 and only dismisses the
        # temporary character, avoiding the durable court/story mutation.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "bp1_yearly_9007_doppelganger": 16779978,
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "culture_notification.1111": {
        # CK3 1.19.0.6 culture divergence notification. Its two authored
        # options are mutually exclusive founder/non-founder acknowledgements;
        # both contain only the same custom tooltip and no gameplay effect.
        # R135 observed the played manager as a non-founder, so exactly one
        # rendered button mapped to native option index 1. Bind the complete
        # five-scope frame before dismissing that acknowledgement.
        "date_raw": 53148048,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "founder": 35761,
        },
        "scope_types": {
            "parent_culture_1": "culture",
            "new_culture": "culture",
            "parent_1": "culture",
            "ethos": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "intrigue_scheming.1202": {
        # CK3 1.19.0.6 hired-spy follow-up. The temporary spy is created in
        # immediate. Option 1 removes that generated courtier and grants only
        # minor intrigue-lifestyle XP; options 2/3 respectively retain the
        # spy with a decade-long county modifier or kill them for dread/XP.
        # R316 observed the exact root, quarter value, generated spy and dense
        # three-option frame. Take the terminal, least-durable option 1.
        "date_raw": 53156712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "hired_spy": (29037, 32904),
        },
        "scope_types": {
            "quarter": "value",
            "hired_spy": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("quarter", "hired_spy"),),
        "saved_scope_count": 2,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "chancellor_task.1102": {
        # CK3 1.19.0.6 chancellor side effect. The immediate block has already
        # selected one current truce target; its sole authored option cancels
        # that one-way truce. There is no acknowledgement-only alternative,
        # so bind the exact manager root, three typed scopes and one-button
        # shape before selecting the only route needed to continue the line.
        "date_raw": 53151120,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "target": (29037,),
        },
        "scope_types": {
            "councillor": "character",
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
    "tgp_movement_events.0070": {
        # CK3 1.19.0.6 celestial-government study event. Option 2 mutates the
        # selected councillor's skill by two points; option 3 mutates both the
        # played ruler and councillor. Option 1 has no player resource or skill
        # mutation and confines the unrelated event to friendship progress and
        # trait-dependent stress, making it the least invasive authored route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "councillor": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "councillor": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "councillor",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0080": {
        # CK3 1.19.0.6 celestial family-subsidy request.  The played manager
        # is not in the conservative movement in R288, so native option 0 is
        # hidden and the three rendered choices map exactly to 1/2/3.  The
        # first two visible routes transfer family gold and either install a
        # durable estate modifier or mutate movement influence/power.  Native
        # option 3 ends the event without those estate or movement mutations,
        # confining the result to authored friendship/stress and conditional
        # opinion/resource effects.  Bind the generated family member and the
        # complete hidden-option projection before taking that terminal route.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "root_scope": 29037,
        },
        "unique_character_scope_excludes": {
            "family_member": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "family_member": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "root_scope",
            "my_movement",
            "family_member",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0050": {
        # CK3 1.19.0.6 merit elder invitation. R154 had no old_elder scope,
        # so authored option 2 was hidden and the two rendered buttons mapped
        # to native indices 0/2. Option 0 installs a new elder relation and
        # changes merit; native option 2 is terminal and only grants the
        # source-authored lifestyle XP plus trait-dependent stress relief.
        # Bind the movement group, generated elder and complete two-of-three
        # option projection before taking that least invasive route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "new_elder": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "new_elder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "new_elder",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0060": {
        # CK3 1.19.0.6 celestial movement-rival event. R331 exposed native
        # options 1/2/3 while the intrigue-focus-only option 0 was hidden.
        # Native option 1 starts or strengthens a hostile scheme and reduces
        # the rival movement; option 3 enters a faith-dependent branch. Native
        # option 2 only grants the player's own movement a medium power gain,
        # so it is the narrow non-religious, non-hostile continuation route.
        # Bind both movement groups and the generated rival before selecting.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival": (32904,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "rival_movement": "situation_participant_group",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "rival_movement",
            "rival",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0150": {
        # CK3 1.19.0.6 Shinto-monk visit. The diplomat-only alliance route is
        # hidden in the R152 manager frame, leaving authored native options
        # 1/2/3. Option 1 installs a durable conversion discount and penalizes
        # zealot vassal opinion; option 2 runs a random conversion duel.
        # Option 3 has no RNG or follow-up event: it welcomes the monk, grants
        # medium diplomacy XP or prestige, and gives the sending ruler a small
        # opinion increase. Bind both generated characters and select that
        # deterministic, least invasive route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "other_ruler": (29037,),
            "monk": (29037,),
        },
        "character_scope_differs_from": {
            "other_ruler": ("monk",),
            "monk": ("other_ruler",),
        },
        "scope_types": {
            "other_ruler": "character",
            "monk": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "other_ruler",
            "monk",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "ep3_decisions_event.2001": {
        # CK3 1.19.0.6 administrative-vassal confirmation request.  Option 1
        # begins the multi-event confirmation ceremony; option 2 terminates
        # the request immediately through the authored refusal effect.  The
        # refusal can change only this unrelated administrator relationship
        # and trait-dependent stress, while avoiding a new blocking event
        # chain during the bounded Phase-2 observation window. R163 observed
        # the complete two-character/two-option letter frame. R329 then
        # reached a second independent request on the bounded three-cycle
        # endgame lineage. R345 then observed three distinct confirmation
        # vassals at 53204640, 53226000, and 53246304 in one replay. The
        # decision is once per requesting vassal, not once per receiving
        # liege, so validate every independent request in the product window.
        "date_raw": 53157888,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "confirmation_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "confirmation_vassal": (29037,),
        },
        "scope_types": {
            "confirmation_vassal": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "confirmation_vassal",
            "confirmation_liege",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "adultery.0002": {
        # CK3 1.19.0.6 spouse-suspicion event. Confrontation opens a new event
        # chain, investigation runs a duel, and spying mutates the spymaster's
        # council task. Authored option 4 does nothing and is the only bounded
        # terminal route without those state changes. The hidden yearly picker
        # suppresses only the selected partner for five years; it has no
        # campaign-global one-shot gate, so validate every occurrence.
        "date_raw": 53169888,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "spouse": 29037,
        },
        "unique_character_scope_excludes": {
            "lover_spouse": (29037,),
        },
        "scope_types": {
            "lover_spouse": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "spouse",
            "lover_spouse",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 3,
                "native_option_indices": (0, 2, 3),
                "snapshot_option_counts": (3, 4),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                # Native option 1 requires sufficient intrigue and option 2 a
                # valid spymaster task.  When both triggers fail CK3 renders
                # only confrontation plus the unconditional terminal route.
                "option_count": 2,
                "native_option_indices": (0, 3),
                "snapshot_option_counts": (2, 4),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "health.1010": {
        # CK3 1.19.0.6 smallpox contraction event. The immediate block has
        # already applied the disease before the modal opens. Native options
        # 0/1/2 depend on physician/travel ownership, option 5 additionally
        # requires a mystic, and options 3/4 start treatment resolution.
        # Native option 6 is the unconditional terminal route and starts no
        # follow-up treatment chain. Bind the complete live projection and
        # all source-created typed scopes before selecting it.
        "date_raw": 53340528,
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
        "snapshot_option_count": 7,
        "native_option_indices": (3, 4, 6),
        "selected_option_number": 7,
        "selected_native_option_index": 6,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "stress_threshold.2202": {
        # CK3 1.19.0.6 response to another character's boiling-anger mental
        # break. R147 observed the played manager as the yelled-at root and
        # no pre-existing rival scope, so authored option 1 was hidden and the
        # sole rendered button mapped to native option index 1. The immediate
        # block is inert without rival; this remaining route only reduces the
        # player's stress. Bind both typed character scopes and the complete
        # one-of-two option shape before selecting that source-authored route.
        "date_raw": 53148288,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "character_to_yell_at": 29037,
        },
        "unique_character_scope_excludes": {
            "stress_character": (29037,),
        },
        "scope_types": {
            "stress_character": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "stress_character",
            "character_to_yell_at",
        ),),
        "saved_scope_count": 2,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "stress_threshold.1721": {
        # CK3 1.19.0.6 impostor-syndrome mental break. Immediate has selected
        # two coping routes plus the unconditional push-through fallback. The
        # first live projection offers inappetetic (native7), confider (native9),
        # and stress gain (native12). Confider is the least destructive route:
        # it lowers stress and may strengthen the selected friend relation.
        # A later no-confidant projection offers inappetetic (native7), drunkard
        # (native10), and stress gain (native12). Its live indicators show that
        # inappetetic is already owned, and native7 always advances starvation;
        # native10 is the narrowest deterministic route because it lowers stress
        # and adds drunkard instead of escalating starvation or gaining stress.
        "date_raw": 53387208,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "stress_character": 32904,
        },
        "unique_character_scope_excludes": {
            "deceased_character": (32904,),
            "confidant": (32904,),
        },
        "character_scope_differs_from": {
            "deceased_character": ("confidant",),
            "confidant": ("deceased_character",),
        },
        "scope_types": {
            "deceased_character": "character",
            "confidant": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "stress_character",
            "deceased_character",
            "confidant",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 14,
        "native_option_indices": (7, 9, 12),
        "selected_option_number": 10,
        "selected_native_option_index": 9,
        "scope_variants": (
            {
                "saved_scope_names": (
                    "stress_character",
                    "deceased_character",
                ),
                "saved_scope_count": 2,
                "character_scopes": {
                    "stress_character": 32904,
                },
                "unique_character_scope_excludes": {
                    "deceased_character": (32904,),
                },
                "character_scope_differs_from": {
                    "deceased_character": ("stress_character",),
                },
                "scope_types": {
                    "deceased_character": "character",
                },
                # Couple the no-confidant shape to its exact rendered choices;
                # do not admit a scope/option Cartesian product.
                "option_count": 3,
                "snapshot_option_count": 14,
                "native_option_indices": (7, 10, 12),
                "selected_option_number": 11,
                "selected_native_option_index": 10,
                "option_variants": (),
            },
        ),
        # A later stress threshold may legally choose this event again. Its
        # ten-year personality flags rotate description text; they do not gate
        # the event, and the ordinary 5/8-year recheck is not a hard minimum.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "stress_threshold_special.1001": {
        # CK3 1.19.0.6 grief mental break after a recorded close death. The
        # immediate block exposes at most two coping routes plus the mutually
        # exclusive frozen-grief/lunatic fallback. This live frame offers
        # drunkard, confider and frozen grief. Confider is the only constructive
        # route when present: it reduces stress, records mutual trust with the
        # surviving spouse and avoids substance abuse or an unbounded grief
        # modifier. A later source-defined frame had no valid confidant and
        # exposed drunkard, inappetetic and frozen grief. Inappetetic has no
        # immediate health loss; unlike permanent frozen grief, its dangerous
        # starvation effect requires a later explicit reuse of that coping
        # route, so it is the least harmful deterministic terminal path there.
        # A second no-confidant frame exposed depressed, drunkard and frozen
        # grief. Drunkard has the smallest direct health penalty (-0.15 versus
        # -0.5 for either alternative), so that exact projection selects it.
        "date_raw": 53343408,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "stress_character": 29037,
        },
        "unique_character_scope_excludes": {
            "deceased_character": (29037,),
            "confidant": (29037,),
        },
        "character_scope_differs_from": {
            "deceased_character": ("confidant",),
            "confidant": ("deceased_character",),
        },
        "scope_types": {
            "stress_character": "character",
            "deceased_character": "character",
            "confidant": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "stress_character",
            "deceased_character",
            "confidant",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 9,
        "native_option_indices": (1, 6, 7),
        "selected_option_number": 7,
        "selected_native_option_index": 6,
        "option_variants": (
            {
                "option_count": 3,
                "native_option_indices": (1, 6, 7),
                "snapshot_option_counts": (9,),
                "selected_option_number": 7,
                "selected_native_option_index": 6,
            },
            {
                "option_count": 3,
                "native_option_indices": (1, 4, 7),
                "snapshot_option_counts": (9,),
                "selected_option_number": 5,
                "selected_native_option_index": 4,
                # Couple the no-confidant scope shape to this exact authored
                # option projection; do not admit Cartesian cross-variants.
                "saved_scope_name_sets": ((
                    "stress_character",
                    "deceased_character",
                ),),
                "unique_character_scope_excludes": {
                    "deceased_character": (29037,),
                },
                "character_scope_differs_from": {
                    "deceased_character": ("stress_character",),
                },
                "scope_types": {
                    "stress_character": "character",
                    "deceased_character": "character",
                },
                "saved_scope_count": 2,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 7),
                "snapshot_option_counts": (9,),
                "selected_option_number": 2,
                "selected_native_option_index": 1,
                # This later frame is also a no-confidant projection. Keep
                # its two-scope shape inside the exact option variant so it
                # cannot combine with the constructive confidant route.
                "saved_scope_name_sets": ((
                    "stress_character",
                    "deceased_character",
                ),),
                "unique_character_scope_excludes": {
                    "deceased_character": (29037,),
                },
                "character_scope_differs_from": {
                    "deceased_character": ("stress_character",),
                },
                "scope_types": {
                    "stress_character": "character",
                    "deceased_character": "character",
                },
                "saved_scope_count": 2,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep1_flavor.0021": {
        # CK3 1.19.0.6 royal-court language quarrel. Route A applies mutual
        # dislike/cultural loss and adds a random diplomacy duel; route C
        # applies the same negative court/culture effects plus a ten-year
        # character modifier. Route B has no random duel or durable modifier
        # and confines the unrelated event to positive court opinions,
        # friendship progress, cultural acceptance and trait-dependent stress.
        # Bind the rival title, the generated rival/nitpicker relationship and
        # all three rendered options before taking that non-random route.
        "date_raw": 53215344,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival_monarch": (32904,),
            "nitpicker": (32904,),
        },
        "character_scope_differs_from": {
            "rival_monarch": ("nitpicker",),
            "nitpicker": ("rival_monarch",),
        },
        "scope_types": {
            "rival_realm": "landed_title",
            "rival_monarch": "character",
            "nitpicker": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "rival_realm",
            "rival_monarch",
            "nitpicker",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep1_flavor.2040": {
        # CK3 1.19.0.6 exotic-arms delivery. The R183 frame has no eligible
        # player artifact to trade, so authored option 1 is hidden and the
        # rendered buttons map to native indices 1/2. Authored option 2 spends
        # major gold and transfers the generated blade; authored option 3 is
        # the terminal refusal and adds no gameplay effect. Bind the complete
        # exact frame, including the source-defined holder/owner and generated
        # merchant lineage, before selecting that least-disruptive terminal
        # route. R286 proved the R183 holder and merchant IDs were allocator
        # output, while their relationships stayed exact. R330 observed the
        # source-authored poor-quality branch: its artifact helper additionally
        # saves the boolean ``exotic_blade_quality``. R350 exercised the other
        # source-authored artifact branch: the weapon/armor helpers save the
        # mutually exclusive flags ``weapon_type`` and ``armor_type``.
        "date_raw": 53174184,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "exotic_arms_target": 32904,
        },
        "character_scope_matches_any": {
            "exotic_blade_holder": ("owner",),
            "owner": ("exotic_blade_holder",),
        },
        "character_scope_differs_from": {
            "exotic_blade_holder": (
                "exotic_arms_target", "foreign_merchant",
            ),
            "foreign_merchant": (
                "exotic_blade_holder", "exotic_arms_target", "owner",
            ),
        },
        "scope_types": {
            "exotic_blade_holder": "character",
            "exotic_arms_target": "character",
            "owner": "character",
            "random_quality_bonus": "value",
            "quality": "value",
            "wealth": "value",
            "newly_created_artifact": "artifact",
            "merchant_county": "landed_title",
            "foreign_merchant": "character",
            "exotic_blade": "artifact",
        },
        "optional_scope_types": {
            "weapon_type": "flag",
            "armor_type": "flag",
            "exotic_blade_quality": "boolean",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "owner",
                "weapon_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "exotic_blade_quality",
                "owner",
                "weapon_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "owner",
                "armor_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "exotic_blade_quality",
                "owner",
                "armor_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
        ),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "epidemic_events.1100": {
        # CK3 1.19.0.6 outbreak notification. Its immediate block has already
        # recorded the notified epidemic and installed county-side outbreak
        # effects before the modal opens. In R151 the manager had no court
        # physician, so the rendered buttons mapped to native indices 0/2; in
        # R289 the manager had a physician and they mapped to 0/1 instead.
        # Native options 1/2 both start a later physician/health event chain;
        # option 0 only applies the source-authored -2 governor trait XP when
        # eligible. Select option 0 as the smallest unrelated mutation, after
        # binding all three typed saved scopes and either exact mutually
        # exclusive physician-dependent option projection. Vanilla invokes
        # this once for each newly encountered epidemic and only suppresses
        # repeat notices for the same epidemic, so multiple independently
        # typed deliveries are valid inside the product observation window.
        "date_raw": 53148360,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "province": "province",
            "infected_county": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "province",
            "infected_county",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (0, 1),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 2,
                "native_option_indices": (0, 2),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.1060": {
        # CK3 1.19.0.6 plague-scapegoat response. The immediate block has
        # already created the plague-witch-hunt story before the modal opens.
        # Native option 0 is hidden unless the player has very high piety. In
        # the observed manager frame the complete rendered projection is
        # therefore native options 1/2. Both install a ten-year county
        # modifier, but option 1 permits rampant witch trials while option 2
        # explicitly slows them and starts no additional event. Bind the two
        # epidemic aliases plus the source-created story before selecting the
        # deterministic option 2 route.
        "date_raw": 53225568,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "story_scope": "story",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "story_scope",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "faction_demand.0101": {
        # CK3 1.19.0.6 liberty-faction ultimatum. Native option 0 lowers the
        # current realm-authority law, legitimacy, dread and prestige before
        # destroying the faction. Native option 1 is an optional co-emperor
        # counter-offer with a random accept/refuse branch. Native option 2
        # preserves the current law and title state while starting the
        # source-authored faction war. Keep that war on the gameplay surface
        # instead of mutating the promotion-source prerequisites, and bind
        # both exact source-defined option projections before refusing.
        "date_raw": 53297760,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "faction_target": 32904,
        },
        "unique_character_scope_excludes": {
            "faction_leader": (32904,),
        },
        "scope_types": {
            "faction": "faction",
            "faction_leader": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "faction",
            "faction_leader",
            "faction_target",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
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
    "faction_demand.1001": {
        # CK3 1.19.0.6 populist ultimatum. Native option 0 (culture/faith
        # conversion) may be visible when the 30-percent realm thresholds and
        # non-State-Faith gate pass; native option 1 is a distinct State Faith
        # route. Native option 2 immediately grants independence/transfers
        # titles, while native option 3 refuses and starts the faction war.
        # Conversion and immediate surrender both destroy invariants used by
        # this bounded manager observation. Refusal preserves the current
        # titles and roster while handing the war to the existing gameplay
        # state surface. Bind either observed rendered-option projection and
        # either exact source-authored saved-scope shape before refusing.
        # Each newly formed populist faction can issue its own demand, so the
        # event is repeatable across independent faction lifecycles.
        "date_raw": 53229048,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "faction_target": 32904,
        },
        "unique_character_scope_excludes": {
            "peasant_leader": (32904,),
        },
        "scope_types": {
            "faction": "faction",
            "peasant_county": "landed_title",
            "target_title": "landed_title",
            "peasant_leader": "character",
        },
        "optional_scope_types": {
            "new_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "faction",
                "peasant_county",
                "faction_target",
                "target_title",
                "peasant_leader",
            ),
            (
                "faction",
                "peasant_county",
                "faction_target",
                "target_title",
                "peasant_leader",
                "new_title",
            ),
        ),
        "option_count": 2,
        "snapshot_option_count": 4,
        "native_option_indices": (2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "char_interaction.0240": {
        # CK3 1.19.0.6 auto-accepted pardon letter. The pardon interaction is
        # already resolved before this event and the sole option has no effect.
        # Bind the dynamic non-player actor, played recipient, hook flag, and
        # exact three unavailable generic interaction roles before dismissal.
        "date_raw": 53366952,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": ("hook",),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
            "hook",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # Different pardon requests can resolve during one long observation.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "char_interaction.0251": {
        # CK3 1.19.0.6 AI-vassal contract-lowering notification. The actor has
        # already applied its most-desired lower obligation, blocked further
        # contract modification, and consumed the hook in immediate. Its sole
        # option is acknowledgement-only. Bind the dynamic non-player actor,
        # played recipient, and exact three unavailable generic interaction
        # roles before dismissing the letter.
        "date_raw": 53363856,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        # Each AI vassal/hook use can independently produce this letter.
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "char_interaction.0370": {
        # CK3 1.19.0.6 cease-paying-tribute notification. Its immediate block
        # has already ended the actor's tributary relation before this letter
        # opens. The retaliation route (native option 1) is hidden in the
        # observed frame because can_retaliate_trigger is false; that same
        # condition also makes the optional legitimacy loss in native option
        # 0 inert. Bind the sender/recipient and the exact three unavailable
        # generic interaction slots before acknowledging the sole rendered
        # no-op option.
        "date_raw": 53229720,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "physician_epidemic_events.1040": {
        # CK3 1.19.0.6 royal-alms proposal during a major epidemic. Native
        # option 0 installs a ten-year modifier across infected counties and
        # runs a disease-dependent five-percent infection roll against the
        # player. Native option 1 refuses with only minor piety loss and
        # trait-dependent stress, adding no modifier, RNG disease effect or
        # follow-up event. Bind both epidemic aliases and the generated court
        # physician before taking that deterministic terminal route.
        "date_raw": 53237808,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "physician": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "physician": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "physician",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
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
        "date_raw": 53254032,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "merchant": (32904,),
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
        "max_occurrences": 1,
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
        # block has already employed and upgraded the dynamic eunuch and
        # granted the starting influence bonus before the modal is shown.
        # Native option 0 additionally replaces/grants the chief-eunuch court
        # position and changes opinion; native option 1 has no effect. Bind
        # the generated story lineage and choose the terminal no-op route so
        # this incidental story does not mutate the manager's court roster.
        "date_raw": 53219664,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("eunuch",),
        },
        "scope_types": {
            "eunuch": "character",
            "origin": "landed_title",
            "story": "story",
            "liege": "character",
            "candidate": "character",
            "modifier_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "eunuch",
            "origin",
            "story",
            "liege",
            "candidate",
            "modifier_type",
        ),),
        "saved_scope_count": 6,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
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
    "tgp_dynastic_cycle_events.0040": {
        # Independent vanilla Silk Road investment event.  Options 1 and 2
        # spend treasury/gold and add a long modifier or fascination progress;
        # option 3 only retains its vanilla trait-dependent stress impact.
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
        "selected_option_number": 3,
        "selected_native_option_index": 2,
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


__all__ = ["EMBEDDED_VANILLA_TIMELINE_CONTRACTS"]
