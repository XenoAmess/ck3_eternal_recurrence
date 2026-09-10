"""First shard of the portable vanilla CK3 timeline interrupt records."""

from __future__ import annotations

from typing import Final

from .registry import PLAYER_SENTINEL


EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
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
        # inappetetic is already owned, so native10 avoids advancing starvation.
        # R375 proves that the same two-scope shape may instead offer confider
        # (native9); that route lowers stress and remains safe without a retained
        # confidant scope because its optional friend effect may simply be absent.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {
            "stress_character": PLAYER_SENTINEL,
        },
        "unique_character_scope_excludes": {
            "deceased_character": (PLAYER_SENTINEL,),
            "confidant": (PLAYER_SENTINEL,),
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
                    "stress_character": PLAYER_SENTINEL,
                },
                "unique_character_scope_excludes": {
                    "deceased_character": (PLAYER_SENTINEL,),
                },
                "character_scope_differs_from": {
                    "deceased_character": ("stress_character",),
                },
                "scope_types": {
                    "deceased_character": "character",
                },
                # Couple the no-confidant shape to both source-valid live
                # projections; do not admit a scope/option Cartesian product.
                "option_count": 3,
                "snapshot_option_count": 14,
                "native_option_indices": (7, 10, 12),
                "selected_option_number": 11,
                "selected_native_option_index": 10,
                "option_variants": ({
                    # R375 can offer confider even without a retained
                    # confidant scope. Its option trigger depends on the
                    # immediate flag; the friend relation is optional.
                    "option_count": 3,
                    "snapshot_option_count": 14,
                    "native_option_indices": (7, 9, 12),
                    "selected_option_number": 10,
                    "selected_native_option_index": 9,
                },),
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
}


__all__ = ["EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS"]
