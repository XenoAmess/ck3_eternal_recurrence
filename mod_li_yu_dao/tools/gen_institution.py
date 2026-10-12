"""Generate a consented headship charter with revalidated runtime authorization.

gen_runtime owns the production runtime projection. Executable runtime guards
are not historical native admission or live/lifecycle acceptance evidence.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parents[1]
HEADER='# GENERATED FILE: edit tools/gen_institution.py; regenerate through gen_runtime.py.\n'

def build_outputs(catalogue=None):
    if catalogue is None:
        import content_data as catalogue
    outputs={}
    def script(path,text): outputs[path]=(HEADER+text.strip()+'\n').encode('utf-8-sig')
    owned='OR = { '+' '.join(f'this = rite:{r.script_id}' for r in catalogue.RITES)+' }'
    script('common/scripted_triggers/lyd_i3b_institution_triggers.txt',r'''
# Legacy interface name: this is runtime authorization, not a proof receipt.
# Never infer this conjunction from primitive-only evidence or a fixture flag.
lyd_i3b_native_admitted_trigger = {
    lyd_i3b_actor_trigger = yes
    lyd_i3b_event_context_trigger = yes
    this = scope:lyd_i3b_actor
    lyd_i3b_ready_trigger = { ACTOR = scope:lyd_i3b_actor }
}
lyd_i3b_owned_rite_trigger = { @OWNED@ }
lyd_i3b_supported_rite_trigger = {
    OR = { lyd_i3b_owned_rite_trigger = yes this = rite:jingxue this = rite:daoxue }
}
lyd_i3b_compatible_rite_trigger = {
    lyd_i3b_supported_rite_trigger = yes
    rite_has_doctrine = doctrine_no_head
    rite_has_doctrine = doctrine_theocracy_lay_clergy
    NOR = {
        rite_has_doctrine = doctrine_temporal_head
        rite_has_doctrine = doctrine_spiritual_head
        rite_has_doctrine = doctrine_clerical_succession_spiritual_appointment
        rite_has_doctrine = doctrine_clerical_succession_spiritual_fixed_appointment
    }
}
lyd_i3b_elector_trigger = { is_alive = yes is_adult = yes is_imprisoned = no NOT = { has_trait = incapable } learning >= 15 }
# Faith ROOT. All its actual rites must belong to the fixed 36-rite catalogue;
# a detached Faith need not contain every catalogue rite.
lyd_i3b_only_owned_rites_faith_trigger = {
    religion = religion:confucianism_religion
    exists = main_rite
    main_rite = { lyd_i3b_owned_rite_trigger = yes }
    NOT = { any_faith_rite = { NOT = { lyd_i3b_owned_rite_trigger = yes } } }
}
# Faith ROOT. Vanilla Confucianism keeps its original Faith and main rite.
# All actual rites, including Jingxue/Daoxue, enter the same consented roster.
lyd_i3b_supported_faith_trigger = {
    OR = {
        lyd_i3b_only_owned_rites_faith_trigger = yes
        AND = {
            this = faith:confucian_faith
            religion = religion:confucianism_religion
            exists = main_rite
            main_rite = { lyd_i3b_supported_rite_trigger = yes }
            NOT = { any_faith_rite = { NOT = { lyd_i3b_supported_rite_trigger = yes } } }
        }
    }
}
# Character ROOT. No title office or existing challenger can supply a mandate.
# is_head_of_faith is a native Title trigger, used only inside any_held_title.
lyd_i3b_no_other_office_trigger = {
    NOT = { any_held_title = {
        OR = {
            is_head_of_faith = yes
            pam_title_is_antipope_office_trigger = yes
            has_variable = lyd_c3_owned_claim_title
        }
    } }
    pam_is_antipope_trigger = no
    pam_is_antipope_sponsor_trigger = no
    NOT = { has_variable = lyd_c3_claim_title }
}
# Faith ROOT. Include native challengers with no LYD metadata.
lyd_i3b_headless_faith_trigger = {
    lyd_i3b_supported_faith_trigger = yes
    has_doctrine = doctrine_no_head
    NOT = { exists = religious_head_title }
    NOT = { exists = religious_head }
    NOT = { any_religious_head_challenger = { always = yes } }
}
# Character ROOT. Detached admission comes from the actual current main HoR,
# never an owned variable, political sponsor, or a rite of the same script type.
lyd_i3b_detached_authority_trigger = {
    NOT = { faith = faith:lyd_common_faith }
    faith = { lyd_i3b_only_owned_rites_faith_trigger = yes }
    rite = faith.main_rite
    exists = rite.head_of_rite
    trigger_if = { limit = { exists = rite.head_of_rite }
        this = rite.head_of_rite
    }
    trigger_else = { always = no }
}
# Only I3b permits untouched vanilla Confucian players to initiate. The common
# C3 school actor gate remains unchanged for every other mechanism and for the
# legacy/detached routes; no admission flag or new rite is imposed on mode 2.
lyd_i3b_player_actor_trigger = {
    OR = {
        lyd_c3_player_actor_trigger = yes
        AND = {
            is_ai = no
            is_alive = yes
            is_adult = yes
            is_landed = yes
            NOT = { has_trait = incapable }
            religion = religion:confucianism_religion
            faith = faith:confucian_faith
            rite = { lyd_i3b_supported_rite_trigger = yes }
        }
    }
}
lyd_i3b_actor_trigger = {
    lyd_i3b_player_actor_trigger = yes
    lyd_i3b_no_other_office_trigger = yes
    OR = {
        AND = { faith = faith:lyd_common_faith rite = faith.main_rite }
        lyd_i3b_detached_authority_trigger = yes
        AND = { faith = faith:confucian_faith rite = { lyd_i3b_supported_rite_trigger = yes } }
    }
    highest_held_title_tier >= tier_duchy
    save_temporary_scope_as = lyd_i3b_actor_check
    rite = { rite_has_allowed_gender_for_clergy = scope:lyd_i3b_actor_check }
}
# Revalidate the captured authority mode at every nomination/ballot callback.
# The existing common-Faith scholar route remains separate from detached HoR.
lyd_i3b_captured_authority_trigger = {
    OR = {
        AND = { var:lyd_i3b_authority_mode = 0 faith = faith:lyd_common_faith }
        AND = {
            var:lyd_i3b_authority_mode = 2
            faith = faith:confucian_faith
            rite = var:lyd_i3b_actor_rite
            rite = { lyd_i3b_supported_rite_trigger = yes }
        }
        AND = {
            var:lyd_i3b_authority_mode = 1
            lyd_i3b_detached_authority_trigger = yes
            exists = var:lyd_i3b_required_native_hor
            trigger_if = { limit = { has_variable = lyd_i3b_required_native_hor exists = var:lyd_i3b_main.head_of_rite }
                this = var:lyd_i3b_required_native_hor
                var:lyd_i3b_main.head_of_rite = var:lyd_i3b_required_native_hor
            }
            trigger_else = { always = no }
        }
    }
}
# Receipt variables survive cleanup; only detached enactment requires the actual
# same native HoR afterward. This does not call an invented HoR setter.
lyd_i3b_native_authority_postcondition_trigger = {
    OR = {
        var:lyd_i3b_result_authority_mode = 0
        AND = {
            var:lyd_i3b_result_authority_mode = 2
            faith = faith:confucian_faith
            rite = var:lyd_i3b_actor_rite
            faith.main_rite = var:lyd_i3b_main
        }
        AND = {
            var:lyd_i3b_result_authority_mode = 1
            exists = var:lyd_i3b_result_native_hor
            trigger_if = { limit = { has_variable = lyd_i3b_result_native_hor exists = var:lyd_i3b_main.head_of_rite }
                this = var:lyd_i3b_result_native_hor
                var:lyd_i3b_main.head_of_rite = var:lyd_i3b_result_native_hor
            }
            trigger_else = { always = no }
        }
    }
}
# Withdrawal is available to the living human initiator after identity drift.
# This does not authorize nominations, ballots or enactment.
lyd_i3b_cancel_actor_trigger = {
    is_ai = no
    is_alive = yes
    has_variable = lyd_i3b_active
    has_variable = lyd_i3b_phase
}
lyd_i3b_result_actor_trigger = {
    is_ai = no
    is_alive = yes
    has_variable = lyd_i3b_result_code
    has_variable = lyd_i3b_result_serial
}
lyd_i3b_can_begin_trigger = {
    lyd_i3b_actor_trigger = yes
    NOT = { has_variable = lyd_i3b_active }
    NOT = { has_variable = lyd_c2_active }
    NOT = { has_variable = lyd_c3_active }
    faith = {
        lyd_i3b_headless_faith_trigger = yes
        NOT = { any_faith_rite = { NOT = { lyd_i3b_compatible_rite_trigger = yes } } }
        NOT = { any_faith_rite = { OR = { has_variable = lyd_c2_proposal_owner has_variable = lyd_c3_proposal_owner has_variable = lyd_i3b_owner } } }
    }
}
# Character ROOT, immutable absolute ACTOR parameter. Revalidate the full roster.
lyd_i3b_current_trigger = {
    lyd_i3b_actor_trigger = yes
    lyd_i3b_captured_authority_trigger = yes
    has_variable = lyd_i3b_active
    faith = var:lyd_i3b_faith
    rite = var:lyd_i3b_actor_rite
    faith.main_rite = var:lyd_i3b_main
    NOT = { has_variable = lyd_c2_active }
    NOT = { has_variable = lyd_c3_active }
    faith = {
        lyd_i3b_headless_faith_trigger = yes
        NOT = { any_faith_rite = { NOT = { lyd_i3b_compatible_rite_trigger = yes var:lyd_i3b_owner = $ACTOR$ var:lyd_i3b_serial = $ACTOR$.var:lyd_i3b_serial } } }
        NOT = { any_faith_character = {
            is_alive = yes
            NOT = { var:lyd_i3b_member_owner = $ACTOR$ var:lyd_i3b_member_serial = $ACTOR$.var:lyd_i3b_serial }
        } }
    }
    NOT = { any_in_list = {
        variable = lyd_i3b_rites
        save_temporary_scope_as = lyd_i3b_checked_rite
        NOT = {
            faith = $ACTOR$.var:lyd_i3b_faith
            lyd_i3b_compatible_rite_trigger = yes
            var:lyd_i3b_owner = $ACTOR$
            var:lyd_i3b_serial = $ACTOR$.var:lyd_i3b_serial
            rite_counties = var:lyd_i3b_counties
            NOT = { has_variable = lyd_c2_proposal_owner }
            NOT = { has_variable = lyd_c3_proposal_owner }
            trigger_if = {
                limit = { var:lyd_i3b_dormant = 1 }
                rite_counties = 0
                $ACTOR$.var:lyd_i3b_faith = { NOT = { any_faith_character = { is_alive = yes rite = scope:lyd_i3b_checked_rite } } }
            }
            trigger_else = {
                var:lyd_i3b_total > 0
                trigger_if = { limit = { exists = var:lyd_i3b_delegate }
                    var:lyd_i3b_delegate = { lyd_i3b_elector_trigger = yes rite = scope:lyd_i3b_checked_rite faith = $ACTOR$.var:lyd_i3b_faith }
                }
            }
        }
    } }
    NOT = { any_in_list = {
        variable = lyd_i3b_members
        NOT = {
            is_alive = yes faith = $ACTOR$.var:lyd_i3b_faith rite = var:lyd_i3b_member_rite
            var:lyd_i3b_member_owner = $ACTOR$ var:lyd_i3b_member_serial = $ACTOR$.var:lyd_i3b_serial
            trigger_if = { limit = { var:lyd_i3b_was_elector = 1 } lyd_i3b_elector_trigger = yes }
            trigger_else = { NOT = { lyd_i3b_elector_trigger = yes } }
            trigger_if = { limit = { var:lyd_i3b_was_player = 1 } is_ai = no }
            trigger_else = { is_ai = yes }
        }
    } }
}
# Popup identity is never refreshed inside a callback.
lyd_i3b_event_context_trigger = {
    exists = scope:lyd_i3b_actor
    scope:lyd_i3b_actor = {
        lyd_i3b_current_trigger = { ACTOR = scope:lyd_i3b_actor }
        var:lyd_i3b_serial = scope:lyd_i3b_event_serial
        var:lyd_i3b_nonce = scope:lyd_i3b_event_nonce
        var:lyd_i3b_phase = scope:lyd_i3b_event_phase
    }
}
lyd_i3b_cancel_context_trigger = {
    exists = scope:lyd_i3b_actor
    this = scope:lyd_i3b_actor
    lyd_i3b_cancel_actor_trigger = yes
    var:lyd_i3b_serial = scope:lyd_i3b_event_serial
    var:lyd_i3b_nonce = scope:lyd_i3b_event_nonce
    var:lyd_i3b_phase = scope:lyd_i3b_event_phase
}
lyd_i3b_representatives_ready_trigger = {
    NOT = { any_in_list = {
        variable = lyd_i3b_rites
        var:lyd_i3b_dormant = 0
        NOT = { exists = var:lyd_i3b_delegate var:lyd_i3b_total > 0 }
    } }
}
lyd_i3b_can_seal_trigger = {
    lyd_i3b_current_trigger = { ACTOR = $ACTOR$ }
    var:lyd_i3b_phase = 1
    lyd_i3b_representatives_ready_trigger = yes
}
lyd_i3b_nomination_target_trigger = {
    lyd_i3b_elector_trigger = yes
    faith = $ACTOR$.faith
    var:lyd_i3b_member_owner = $ACTOR$
    var:lyd_i3b_member_serial = $ACTOR$.var:lyd_i3b_serial
    rite = { var:lyd_i3b_dormant = 0 NOT = { has_variable = lyd_i3b_delegate } }
}
lyd_i3b_ballot_trigger = {
    lyd_i3b_event_context_trigger = yes
    scope:lyd_i3b_actor = { var:lyd_i3b_phase = 2 }
    lyd_i3b_elector_trigger = yes
    var:lyd_i3b_member_owner = scope:lyd_i3b_actor
    var:lyd_i3b_member_serial = scope:lyd_i3b_event_serial
    var:lyd_i3b_was_elector = 1
    var:lyd_i3b_vote = -1
}
lyd_i3b_ready_trigger = {
    lyd_i3b_current_trigger = { ACTOR = $ACTOR$ }
    var:lyd_i3b_phase = 2
    NOT = { any_in_list = {
        variable = lyd_i3b_rites
        var:lyd_i3b_dormant = 0
        NOT = { AND = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 var:lyd_i3b_signed = 1 exists = var:lyd_i3b_delegate } }
    } }
    NOT = { any_in_list = { variable = lyd_i3b_members var:lyd_i3b_was_player = 1 NOT = { var:lyd_i3b_player_yes = 1 } } }
    NOT = { any_in_list = { variable = lyd_i3b_political_titles NOT = { holder = $ACTOR$ } } }
}
'''.replace('@OWNED@',owned))
    script('common/script_values/lyd_i3b_institution_values.txt',r'''
lyd_i3b_quorum_value = { value = var:lyd_i3b_yes multiply = 3 subtract = { value = var:lyd_i3b_total multiply = 2 } }
''')
    terms=['lyd_i3b_show_terms_effect = {','    hidden_effect = { save_scope_as = lyd_i3b_progress_actor }',
           '    custom_tooltip = lyd_i3b_doctrine_clause_tt',
           '    custom_tooltip = lyd_i3b_npc_support_tt',
           '    every_in_list = { variable = lyd_i3b_rites']
    for rite in catalogue.RITES:
        terms.append(f'        if = {{ limit = {{ this = rite:{rite.script_id} }} custom_tooltip = lyd_i3b_term_{rite.slug}_tt }}')
    for vanilla in ('jingxue','daoxue'):
        terms.append(f'        if = {{ limit = {{ this = rite:{vanilla} }} custom_tooltip = lyd_i3b_term_{vanilla}_tt }}')
    # Display only captured fields from this actor's round. Missing or foreign
    # records are unknown, never zero. Scope aliases do not alter proposal state.
    terms.append(r'''
        hidden_effect = { save_scope_as = lyd_i3b_progress_rite }
        if = { limit = {
            scope:lyd_i3b_progress_actor = { has_variable = lyd_i3b_active has_variable = lyd_i3b_serial }
            has_variable = lyd_i3b_owner has_variable = lyd_i3b_serial
            has_variable = lyd_i3b_yes has_variable = lyd_i3b_total
            has_variable = lyd_i3b_signed has_variable = lyd_i3b_dormant
        }
            if = { limit = {
                var:lyd_i3b_owner = scope:lyd_i3b_progress_actor
                var:lyd_i3b_serial = scope:lyd_i3b_progress_actor.var:lyd_i3b_serial
            }
                custom_tooltip = lyd_i3b_progress_count_tt
                if = { limit = { var:lyd_i3b_dormant = 1 }
                    custom_tooltip = lyd_i3b_progress_dormant_tt
                }
                else = {
                    if = { limit = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 }
                        custom_tooltip = lyd_i3b_progress_quorum_tt
                    }
                    else = { custom_tooltip = lyd_i3b_progress_no_quorum_tt }
                    if = { limit = { exists = var:lyd_i3b_delegate }
                        var:lyd_i3b_delegate = { hidden_effect = { save_scope_as = lyd_i3b_progress_delegate } }
                        custom_tooltip = lyd_i3b_progress_delegate_tt
                    }
                    else = { custom_tooltip = lyd_i3b_progress_no_delegate_tt }
                    if = { limit = { var:lyd_i3b_signed = 1 }
                        custom_tooltip = lyd_i3b_progress_signed_tt
                    }
                    else_if = { limit = { var:lyd_i3b_signed = 0 }
                        custom_tooltip = lyd_i3b_progress_unsigned_tt
                    }
                    else = { custom_tooltip = lyd_i3b_progress_unknown_tt }
                }
            }
            else = { custom_tooltip = lyd_i3b_progress_unknown_tt }
        }
        else = { custom_tooltip = lyd_i3b_progress_unknown_tt }
''')
    terms += ['    }','}']
    script('common/scripted_effects/lyd_i3b_terms_effects.txt','\n'.join(terms))
    script('common/scripted_effects/lyd_i3b_setup_effects.txt',r'''
lyd_i3b_bind_event_effect = {
    save_scope_as = lyd_i3b_actor
    # Decision effect tooltips do not materialize the preceding round writes.
    # Bind numeric event scope values only from a complete existing round.
    if = { limit = {
        has_variable = lyd_i3b_serial
        has_variable = lyd_i3b_nonce
        has_variable = lyd_i3b_phase
    }
        save_scope_value_as = { name = lyd_i3b_event_serial value = var:lyd_i3b_serial }
        save_scope_value_as = { name = lyd_i3b_event_nonce value = var:lyd_i3b_nonce }
        save_scope_value_as = { name = lyd_i3b_event_phase value = var:lyd_i3b_phase }
    }
}
lyd_i3b_begin_effect = {
    if = { limit = { lyd_i3b_can_begin_trigger = yes }
        save_scope_as = lyd_i3b_actor
        if = { limit = { NOT = { has_variable = lyd_i3b_serial } } set_variable = { name = lyd_i3b_serial value = 0 } }
        if = { limit = { NOT = { has_variable = lyd_i3b_nonce } } set_variable = { name = lyd_i3b_nonce value = 0 } }
        change_variable = { name = lyd_i3b_serial add = 1 }
        change_variable = { name = lyd_i3b_nonce add = 1 }
        set_variable = { name = lyd_i3b_active value = 1 days = 365 }
        set_variable = { name = lyd_i3b_phase value = 1 }
        set_variable = { name = lyd_i3b_faith value = faith }
        set_variable = { name = lyd_i3b_main value = faith.main_rite }
        set_variable = { name = lyd_i3b_actor_rite value = rite }
        remove_variable = lyd_i3b_required_native_hor
        if = { limit = { faith = faith:lyd_common_faith }
            set_variable = { name = lyd_i3b_authority_mode value = 0 }
        }
        else_if = { limit = { faith = faith:confucian_faith }
            set_variable = { name = lyd_i3b_authority_mode value = 2 }
        }
        else = {
            set_variable = { name = lyd_i3b_authority_mode value = 1 }
            set_variable = { name = lyd_i3b_required_native_hor value = rite.head_of_rite }
        }
        clear_variable_list = lyd_i3b_rites
        clear_variable_list = lyd_i3b_members
        clear_variable_list = lyd_i3b_political_titles
        every_held_title = { save_scope_as = lyd_i3b_title scope:lyd_i3b_actor = { add_to_variable_list = { name = lyd_i3b_political_titles target = scope:lyd_i3b_title } } }
        faith = {
            every_faith_rite = {
                save_scope_as = lyd_i3b_rite
                # Keep ownership through the scheduled day-365 cleanup; approval
                # still expires at day 365 via the actor's active field.
                set_variable = { name = lyd_i3b_owner value = scope:lyd_i3b_actor days = 366 }
                set_variable = { name = lyd_i3b_serial value = scope:lyd_i3b_actor.var:lyd_i3b_serial }
                set_variable = { name = lyd_i3b_counties value = rite_counties }
                set_variable = { name = lyd_i3b_members_total value = 0 }
                set_variable = { name = lyd_i3b_total value = 0 }
                set_variable = { name = lyd_i3b_yes value = 0 }
                set_variable = { name = lyd_i3b_signed value = 0 }
                set_variable = { name = lyd_i3b_dormant value = 0 }
                remove_variable = lyd_i3b_delegate
                remove_variable = lyd_i3b_signature_requested
                scope:lyd_i3b_actor = { add_to_variable_list = { name = lyd_i3b_rites target = scope:lyd_i3b_rite } }
            }
            every_faith_character = {
                limit = { is_alive = yes }
                save_scope_as = lyd_i3b_member
                set_variable = { name = lyd_i3b_member_owner value = scope:lyd_i3b_actor }
                set_variable = { name = lyd_i3b_member_serial value = scope:lyd_i3b_actor.var:lyd_i3b_serial }
                set_variable = { name = lyd_i3b_member_rite value = rite }
                set_variable = { name = lyd_i3b_was_elector value = 0 }
                set_variable = { name = lyd_i3b_was_player value = 0 }
                set_variable = { name = lyd_i3b_player_yes value = 0 }
                set_variable = { name = lyd_i3b_vote value = -1 }
                if = { limit = { lyd_i3b_elector_trigger = yes } set_variable = { name = lyd_i3b_was_elector value = 1 } rite = { change_variable = { name = lyd_i3b_total add = 1 } } }
                if = { limit = { is_ai = no } set_variable = { name = lyd_i3b_was_player value = 1 } }
                rite = { change_variable = { name = lyd_i3b_members_total add = 1 } }
                scope:lyd_i3b_actor = { add_to_variable_list = { name = lyd_i3b_members target = scope:lyd_i3b_member } }
            }
        }
        every_in_list = { variable = lyd_i3b_rites if = { limit = { rite_counties = 0 var:lyd_i3b_members_total = 0 } set_variable = { name = lyd_i3b_dormant value = 1 } } }
        lyd_i3b_bind_event_effect = yes
        trigger_event = lyd.430
        trigger_event = { id = lyd.439 days = 365 }
    }
}
# Automatic delivery opens a scoped nomination event; it grants no mandate.
lyd_i3b_nominate_effect = {
    if = { limit = {
        scope:actor = { lyd_i3b_current_trigger = { ACTOR = scope:actor } var:lyd_i3b_phase = 1 }
        scope:recipient = { lyd_i3b_nomination_target_trigger = { ACTOR = scope:actor } }
    }
        scope:actor = { lyd_i3b_bind_event_effect = yes }
        scope:recipient = { save_scope_as = lyd_i3b_nominee rite = { save_scope_as = lyd_i3b_ballot_rite } trigger_event = lyd.410 }
    }
}
lyd_i3b_accept_nomination_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes
        scope:lyd_i3b_actor = { var:lyd_i3b_phase = 1 }
        this = scope:lyd_i3b_nominee
        lyd_i3b_elector_trigger = yes
        rite = scope:lyd_i3b_ballot_rite
        scope:lyd_i3b_ballot_rite = { var:lyd_i3b_dormant = 0 NOT = { has_variable = lyd_i3b_delegate } }
    }
        scope:lyd_i3b_ballot_rite = { set_variable = { name = lyd_i3b_delegate value = scope:lyd_i3b_nominee } }
    }
}
lyd_i3b_nominate_self_effect = {
    if = { limit = {
        lyd_i3b_current_trigger = { ACTOR = root } lyd_i3b_elector_trigger = yes var:lyd_i3b_phase = 1
        rite = { NOT = { has_variable = lyd_i3b_delegate } var:lyd_i3b_dormant = 0 }
    }
        lyd_i3b_bind_event_effect = yes
        save_scope_as = lyd_i3b_nominee
        rite = { save_scope_as = lyd_i3b_ballot_rite }
        trigger_event = lyd.410
    }
}
lyd_i3b_seal_effect = {
    if = { limit = {
        lyd_i3b_can_seal_trigger = { ACTOR = root }
    }
        set_variable = { name = lyd_i3b_phase value = 2 }
        change_variable = { name = lyd_i3b_nonce add = 1 }
        lyd_i3b_bind_event_effect = yes
        every_in_list = { variable = lyd_i3b_members
            if = { limit = { var:lyd_i3b_was_elector = 1 } trigger_event = lyd.411 }
            if = { limit = { var:lyd_i3b_was_player = 1 } trigger_event = lyd.412 }
        }
        trigger_event = lyd.430
    }
}
''')
    script('common/scripted_effects/lyd_i3b_response_effects.txt',r'''
lyd_i3b_vote_effect = {
    if = { limit = { lyd_i3b_ballot_trigger = yes }
        set_variable = { name = lyd_i3b_vote value = $YES$ }
        if = { limit = { var:lyd_i3b_vote = 1 }
            rite = { change_variable = { name = lyd_i3b_yes add = 1 } }
            scope:lyd_i3b_actor = { lyd_i3b_request_signatures_effect = yes }
        }
    }
}
lyd_i3b_player_yes_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes is_ai = no is_alive = yes
        scope:lyd_i3b_actor = { var:lyd_i3b_phase = 2 }
        var:lyd_i3b_member_owner = scope:lyd_i3b_actor var:lyd_i3b_member_serial = scope:lyd_i3b_event_serial
        var:lyd_i3b_was_player = 1 var:lyd_i3b_player_yes = 0
    } set_variable = { name = lyd_i3b_player_yes value = 1 } }
}
lyd_i3b_sign_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes lyd_i3b_elector_trigger = yes
        scope:lyd_i3b_actor = { var:lyd_i3b_phase = 2 }
        rite = scope:lyd_i3b_ballot_rite
        this = scope:lyd_i3b_ballot_rite.var:lyd_i3b_delegate
        scope:lyd_i3b_ballot_rite = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 var:lyd_i3b_signed = 0 }
    } scope:lyd_i3b_ballot_rite = { set_variable = { name = lyd_i3b_signed value = 1 } } }
}
lyd_i3b_request_signatures_effect = {
    # ROOT can still be an NPC ballot recipient. Capture the current actor scope
    # before comparing rite ownership; never use the recipient ROOT as ACTOR.
    save_scope_as = lyd_i3b_signature_actor
    if = { limit = { lyd_i3b_current_trigger = { ACTOR = scope:lyd_i3b_signature_actor } var:lyd_i3b_phase = 2 }
        lyd_i3b_bind_event_effect = yes
        every_in_list = { variable = lyd_i3b_rites
            limit = { var:lyd_i3b_dormant = 0 var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 var:lyd_i3b_signed = 0 NOT = { has_variable = lyd_i3b_signature_requested } }
            set_variable = { name = lyd_i3b_signature_requested value = 1 }
            save_scope_as = lyd_i3b_ballot_rite
            var:lyd_i3b_delegate = { trigger_event = lyd.413 }
        }
    }
}
lyd_i3b_defer_signature_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes
        this = scope:lyd_i3b_ballot_rite.var:lyd_i3b_delegate
    } scope:lyd_i3b_ballot_rite = { remove_variable = lyd_i3b_signature_requested } }
}
lyd_i3b_player_no_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes is_ai = no is_alive = yes
        scope:lyd_i3b_actor = { var:lyd_i3b_phase = 2 }
        var:lyd_i3b_member_owner = scope:lyd_i3b_actor var:lyd_i3b_member_serial = scope:lyd_i3b_event_serial
        var:lyd_i3b_was_player = 1 var:lyd_i3b_player_yes = 0
    }
        scope:lyd_i3b_actor = { lyd_i3b_close_effect = yes debug_log = "LYD_I3B_REJECTED" }
    }
}
lyd_i3b_sign_no_effect = {
    if = { limit = {
        lyd_i3b_event_context_trigger = yes
        scope:lyd_i3b_actor = { var:lyd_i3b_phase = 2 }
        this = scope:lyd_i3b_ballot_rite.var:lyd_i3b_delegate
        scope:lyd_i3b_ballot_rite = { var:lyd_i3b_signed = 0 }
    } scope:lyd_i3b_actor = { lyd_i3b_close_effect = yes debug_log = "LYD_I3B_REPRESENTATIVE_REFUSED" } }
}
lyd_i3b_cancel_event_effect = {
    if = { limit = { lyd_i3b_cancel_context_trigger = yes }
        lyd_i3b_close_effect = yes debug_log = "LYD_I3B_CANCELLED"
    }
}
lyd_i3b_close_effect = {
    save_scope_as = lyd_i3b_closing_actor
    every_in_list = { variable = lyd_i3b_rites
        if = { limit = { var:lyd_i3b_owner = scope:lyd_i3b_closing_actor var:lyd_i3b_serial = scope:lyd_i3b_closing_actor.var:lyd_i3b_serial }
            remove_variable = lyd_i3b_owner remove_variable = lyd_i3b_delegate remove_variable = lyd_i3b_signed
            remove_variable = lyd_i3b_serial remove_variable = lyd_i3b_yes remove_variable = lyd_i3b_total
            remove_variable = lyd_i3b_dormant remove_variable = lyd_i3b_counties remove_variable = lyd_i3b_members_total remove_variable = lyd_i3b_signature_requested
        }
    }
    every_in_list = { variable = lyd_i3b_members
        if = { limit = { var:lyd_i3b_member_owner = scope:lyd_i3b_closing_actor var:lyd_i3b_member_serial = scope:lyd_i3b_closing_actor.var:lyd_i3b_serial }
            remove_variable = lyd_i3b_member_owner remove_variable = lyd_i3b_member_serial remove_variable = lyd_i3b_member_rite
            remove_variable = lyd_i3b_was_elector remove_variable = lyd_i3b_was_player remove_variable = lyd_i3b_player_yes remove_variable = lyd_i3b_vote
        }
    }
    remove_variable = lyd_i3b_active remove_variable = lyd_i3b_phase
    remove_variable = lyd_i3b_authority_mode remove_variable = lyd_i3b_required_native_hor
    clear_variable_list = lyd_i3b_rites clear_variable_list = lyd_i3b_members clear_variable_list = lyd_i3b_political_titles
    # Actor serial and nonce are intentionally monotone and survive cleanup.
}
''')
    script('common/scripted_effects/lyd_i3b_commit_effects.txt',r'''
# Only this authorized commit calls the factory; pending proposals never do.
lyd_i3b_capture_authority_receipt_effect = {
    set_variable = { name = lyd_i3b_result_authority_mode value = var:lyd_i3b_authority_mode }
    remove_variable = lyd_i3b_result_native_hor
    if = { limit = { var:lyd_i3b_authority_mode = 1 }
        set_variable = { name = lyd_i3b_result_native_hor value = var:lyd_i3b_required_native_hor }
    }
}
lyd_i3b_commit_effect = {
    if = { limit = {
        lyd_i3b_actor_trigger = yes
        lyd_i3b_event_context_trigger = yes
        this = scope:lyd_i3b_actor
        lyd_i3b_ready_trigger = { ACTOR = scope:lyd_i3b_actor }
        lyd_i3b_native_admitted_trigger = yes
    }
        # Serial and nonce bind the result event to this exact attempted round.
        set_variable = { name = lyd_i3b_result_serial value = var:lyd_i3b_serial }
        set_variable = { name = lyd_i3b_result_nonce value = var:lyd_i3b_nonce }
        set_variable = { name = lyd_i3b_result_code value = 0 }
        remove_variable = lyd_i3b_result_head_title
        lyd_i3b_capture_authority_receipt_effect = yes
        # The shared factory must observe law95 on the empty, unbound office
        # before it changes this Faith or any captured rite or grants a holder.
        set_variable = { name = lyd_c3_head_creation_authorized value = 1 }
        lyd_c3_create_owned_temporal_head_effect = yes
        remove_variable = lyd_c3_head_creation_authorized
        if = { limit = {
            faith = var:lyd_i3b_faith rite = var:lyd_i3b_actor_rite faith.main_rite = var:lyd_i3b_main
            faith.religious_head = this faith = { lyd_c3_owned_current_head_trigger = yes }
            lyd_i3b_native_authority_postcondition_trigger = yes
            NOT = { any_in_list = { variable = lyd_i3b_rites NOT = { rite_has_doctrine = doctrine_temporal_head faith = scope:lyd_i3b_actor.var:lyd_i3b_faith } } }
            NOT = { any_in_list = { variable = lyd_i3b_political_titles NOT = { holder = scope:lyd_i3b_actor } } }
        }
            faith = { set_variable = { name = lyd_c3_recognized_leader value = scope:lyd_i3b_actor } }
            set_variable = { name = lyd_c3_office_faith value = faith }
            set_variable = { name = lyd_i3b_result_code value = 1 }
            set_variable = { name = lyd_i3b_result_head_title value = faith.religious_head_title }
            debug_log = "LYD_I3B_NATIVE_POSTCONDITION_PASS"
        }
        else = {
            # First failed class, retaining the real partial native state.
            if = { limit = { NOT = { faith = var:lyd_i3b_faith rite = var:lyd_i3b_actor_rite faith.main_rite = var:lyd_i3b_main } }
                set_variable = { name = lyd_i3b_result_code value = 2 }
            }
            else_if = { limit = { NOT = { faith.religious_head = this faith = { lyd_c3_owned_current_head_trigger = yes } } }
                set_variable = { name = lyd_i3b_result_code value = 3 }
            }
            else_if = { limit = { any_in_list = { variable = lyd_i3b_rites NOT = { rite_has_doctrine = doctrine_temporal_head faith = scope:lyd_i3b_actor.var:lyd_i3b_faith } } }
                set_variable = { name = lyd_i3b_result_code value = 4 }
            }
            else_if = { limit = { any_in_list = { variable = lyd_i3b_political_titles NOT = { holder = scope:lyd_i3b_actor } } }
                set_variable = { name = lyd_i3b_result_code value = 5 }
            }
            else_if = { limit = { NOT = { lyd_i3b_native_authority_postcondition_trigger = yes } }
                set_variable = { name = lyd_i3b_result_code value = 7 }
            }
            else = { set_variable = { name = lyd_i3b_result_code value = 6 } }
            debug_log = "LYD_I3B_NATIVE_POSTCONDITION_FAIL" debug_log_scopes = yes
        }
        # Preserve real partial native state; no fake rollback, success charge or political reassignment.
        lyd_i3b_close_effect = yes
        lyd_i3b_show_result_effect = yes
    }
}
lyd_i3b_show_result_effect = {
    if = { limit = { lyd_i3b_result_actor_trigger = yes }
        save_scope_as = lyd_i3b_actor
        save_scope_value_as = { name = lyd_i3b_result_event_serial value = var:lyd_i3b_result_serial }
        save_scope_value_as = { name = lyd_i3b_result_event_nonce value = var:lyd_i3b_result_nonce }
        if = { limit = { var:lyd_i3b_result_code = 1 } trigger_event = lyd.431 }
        else = { trigger_event = lyd.432 }
    }
}
''')
    # Display the existing predicates separately; the complete execution gate
    # remains below them and is checked again by the decision's effect.
    begin_requirements = (
        ('player', 'is_ai = no'),
        ('alive', 'is_alive = yes'),
        ('adult', 'is_adult = yes'),
        ('landed', 'is_landed = yes'),
        ('capable', 'NOT = { has_trait = incapable }'),
        ('confucian', 'religion = religion:confucianism_religion'),
        ('joined', 'OR = { has_character_flag = lyd_enabled AND = { faith = faith:confucian_faith rite = { lyd_i3b_supported_rite_trigger = yes } } }'),
        ('new_rite', 'OR = { lyd_member_rite_trigger = yes AND = { faith = faith:confucian_faith rite = { lyd_i3b_supported_rite_trigger = yes } } }'),
        ('authority', '''OR = {
            AND = { faith = faith:lyd_common_faith rite = faith.main_rite }
            lyd_i3b_detached_authority_trigger = yes
            AND = { faith = faith:confucian_faith rite = { lyd_i3b_supported_rite_trigger = yes } }
        }'''),
        ('duchy', 'highest_held_title_tier >= tier_duchy'),
        ('gender', 'save_temporary_scope_as = lyd_i3b_actor_check rite = { rite_has_allowed_gender_for_clergy = scope:lyd_i3b_actor_check }'),
        ('offices', 'NOT = { any_held_title = { OR = { is_head_of_faith = yes pam_title_is_antipope_office_trigger = yes has_variable = lyd_c3_owned_claim_title } } }'),
        ('challenger', 'pam_is_antipope_trigger = no'),
        ('sponsor', 'pam_is_antipope_sponsor_trigger = no'),
        ('claim', 'NOT = { has_variable = lyd_c3_claim_title }'),
        ('own_round', 'NOT = { has_variable = lyd_i3b_active }'),
        ('c2_round', 'NOT = { has_variable = lyd_c2_active }'),
        ('c3_round', 'NOT = { has_variable = lyd_c3_active }'),
        ('supported_faith', 'faith = { lyd_i3b_supported_faith_trigger = yes }'),
        ('faith_doctrine', 'faith = { has_doctrine = doctrine_no_head }'),
        ('head_title', 'faith = { NOT = { exists = religious_head_title } }'),
        ('head', 'faith = { NOT = { exists = religious_head } }'),
        ('faith_challengers', 'faith = { NOT = { any_religious_head_challenger = { always = yes } } }'),
        ('compatible_rites', 'faith = { NOT = { any_faith_rite = { NOT = { lyd_i3b_compatible_rite_trigger = yes } } } }'),
        ('rite_rounds', 'faith = { NOT = { any_faith_rite = { OR = { has_variable = lyd_c2_proposal_owner has_variable = lyd_c3_proposal_owner has_variable = lyd_i3b_owner } } } }'),
    )
    nomination_requirements = (
        ('current', 'lyd_i3b_current_trigger = { ACTOR = root }'),
        ('alive', 'is_alive = yes'),
        ('adult', 'is_adult = yes'),
        ('free', 'is_imprisoned = no'),
        ('capable', 'NOT = { has_trait = incapable }'),
        ('learning', 'learning >= 15'),
        ('phase', 'var:lyd_i3b_phase = 1'),
        ('active_rite', 'rite = { var:lyd_i3b_dormant = 0 }'),
        ('delegate', 'rite = { NOT = { has_variable = lyd_i3b_delegate } }'),
    )
    decisions=[]
    for suffix,actor,gate,tooltip,effect in (
        ('begin','lyd_i3b_actor_trigger = yes','lyd_i3b_can_begin_trigger = yes','lyd_i3b_begin_valid_tt','lyd_i3b_begin_effect = yes'),
        ('nominate_self','lyd_i3b_actor_trigger = yes','lyd_i3b_current_trigger = { ACTOR = root } lyd_i3b_elector_trigger = yes var:lyd_i3b_phase = 1 rite = { NOT = { has_variable = lyd_i3b_delegate } var:lyd_i3b_dormant = 0 }','lyd_i3b_nominate_valid_tt','lyd_i3b_nominate_self_effect = yes'),
        ('seal','lyd_i3b_actor_trigger = yes','lyd_i3b_can_seal_trigger = { ACTOR = root }','lyd_i3b_seal_valid_tt','lyd_i3b_seal_effect = yes'),
        ('review','lyd_i3b_actor_trigger = yes','lyd_i3b_current_trigger = { ACTOR = root }','lyd_i3b_current_valid_tt','lyd_i3b_bind_event_effect = yes lyd_i3b_request_signatures_effect = yes trigger_event = lyd.430'),
        ('cancel','lyd_i3b_cancel_actor_trigger = yes','lyd_i3b_cancel_actor_trigger = yes','lyd_i3b_cancel_valid_tt','lyd_i3b_close_effect = yes'),
        ('result_review','lyd_i3b_result_actor_trigger = yes','lyd_i3b_result_actor_trigger = yes','lyd_i3b_result_valid_tt','lyd_i3b_show_result_effect = yes'),
    ):
        name=f'lyd_i3b_{suffix}_decision'
        shown=actor
        if suffix in ('nominate_self','seal'):
            shown+=' has_variable = lyd_i3b_active var:lyd_i3b_phase = 1'
        elif suffix=='review':
            shown+=' has_variable = lyd_i3b_active'
        elif suffix=='begin':
            # Eligibility belongs in is_valid; a blocked human school member
            # can still inspect the real institution terms and prerequisites.
            shown='is_ai = no religion = religion:confucianism_religion rite = { lyd_i3b_supported_rite_trigger = yes } NOT = { has_variable = lyd_i3b_active }'
        description='lyd_i3b_result_review_desc' if suffix=='result_review' else 'lyd_i3b_terms_desc'
        requirements = begin_requirements if suffix == 'begin' else nomination_requirements if suffix == 'nominate_self' else None
        if requirements is None:
            validity = f'custom_description = {{ text = {tooltip} subject = root {gate} }}'
        else:
            prefix = 'begin' if suffix == 'begin' else 'nominate'
            validity = '\n        '.join(
                f'custom_description = {{ text = lyd_i3b_{prefix}_{key}_tt subject = root {condition} }}'
                for key, condition in requirements
            ) + f'\n        custom_description = {{ text = lyd_i3b_{prefix}_complete_tt subject = root {gate} }}'
        decisions.append(f'''{name} = {{
    picture = {{ reference = "gfx/interface/illustrations/decisions/decision_personal_religious.dds" }}
    decision_group_type = religious ai_check_interval = 0
    desc = {description} selection_tooltip = {description} confirm_text = {name}
    is_shown = {{ {shown} }}
    is_valid = {{ {validity} }}
    effect = {{ hidden_effect = {{ if = {{ limit = {{ {actor} {gate} }} {effect} }} }} }}
    ai_will_do = {{ base = 0 }}
}}''')
    script('common/decisions/lyd_i3b_institution_decisions.txt','\n'.join(decisions))
    script('common/character_interactions/lyd_i3b_nomination_interactions.txt',r'''
lyd_i3b_nominate_interaction = {
    category = interaction_category_religion common_interaction = yes
    desc = lyd_i3b_terms_desc auto_accept = yes
    is_shown = { scope:actor = { lyd_i3b_actor_trigger = yes has_variable = lyd_i3b_active var:lyd_i3b_phase = 1 } scope:recipient = { faith = scope:actor.faith lyd_i3b_elector_trigger = yes } }
    is_valid_showing_failures_only = {
        scope:actor = { custom_description = { text = lyd_i3b_nomination_actor_valid_tt subject = scope:actor lyd_i3b_current_trigger = { ACTOR = scope:actor } var:lyd_i3b_phase = 1 } }
        scope:recipient = { custom_description = { text = lyd_i3b_nomination_target_valid_tt subject = scope:recipient lyd_i3b_nomination_target_trigger = { ACTOR = scope:actor } } }
    }
    on_auto_accept = { hidden_effect = { lyd_i3b_nominate_effect = yes } }
    ai_will_do = { base = 0 }
}
''')
    events=['namespace = lyd']
    def npc_chance(support):
        # The initiator is also the first headship candidate. Opinion is read
        # from the NPC option recipient toward that candidate, not in reverse.
        # Stock syntax: 00_marriage_interactions opinion/value; religious event
        # ai_chance modifier/factor. Positive factors keep both choices possible.
        friendly, hostile, learned, unlearned = ('1.5', '0.5', '1.25', '0.8') if support else ('0.75', '1.5', '0.9', '1.1')
        modifiers = ((friendly, 'opinion = { target = scope:lyd_i3b_actor value >= 50 }'),
                     (hostile, 'opinion = { target = scope:lyd_i3b_actor value <= -50 }'),
                     (learned, 'scope:lyd_i3b_actor = { learning >= 20 }'),
                     (unlearned, 'scope:lyd_i3b_actor = { learning < 10 }'))
        return f'ai_chance = {{ base = {60 if support else 40}\n' + ''.join(
            f'''            modifier = {{ factor = {factor}
                trigger_if = {{ limit = {{ exists = scope:lyd_i3b_actor }} {condition} }}
                trigger_else = {{ always = no }}
            }}\n''' for factor, condition in modifiers) + '        }'
    def event(id,title,gate,options):
        if id in (410,411,413):
            options=options.replace('ai_chance = { base = 60 }',npc_chance(True)).replace('ai_chance = { base = 40 }',npc_chance(False))
        # Read-only effect tooltip enumerates the exact captured rite objects.
        options=options.replace('option = { name =','option = { scope:lyd_i3b_actor = { lyd_i3b_show_terms_effect = yes } name =')
        events.append(f'''lyd.{id} = {{ type = character_event title = {title} desc = lyd_i3b_terms_desc theme = faith trigger = {{ {gate} }} {options} }}''')
    event(410,'lyd_i3b_nomination_t','lyd_i3b_event_context_trigger = yes this = scope:lyd_i3b_nominee',
          'option = { name = lyd_i3b_yes custom_tooltip = lyd_i3b_nomination_choice_tt hidden_effect = { lyd_i3b_accept_nomination_effect = yes } ai_chance = { base = 60 } } option = { name = lyd_i3b_no ai_chance = { base = 40 } }')
    event(411,'lyd_i3b_ballot_t','lyd_i3b_ballot_trigger = yes',
          'option = { name = lyd_i3b_yes custom_tooltip = lyd_i3b_ballot_choice_tt hidden_effect = { lyd_i3b_vote_effect = { YES = 1 } } ai_chance = { base = 60 } } option = { name = lyd_i3b_no custom_tooltip = lyd_i3b_ballot_no_choice_tt hidden_effect = { lyd_i3b_vote_effect = { YES = 0 } } ai_chance = { base = 40 } }')
    event(412,'lyd_i3b_player_t','lyd_i3b_event_context_trigger = yes is_ai = no is_alive = yes var:lyd_i3b_was_player = 1',
          'option = { name = lyd_i3b_yes custom_tooltip = lyd_i3b_player_choice_tt hidden_effect = { lyd_i3b_player_yes_effect = yes } } option = { name = lyd_i3b_no custom_tooltip = lyd_i3b_refuse_choice_tt hidden_effect = { lyd_i3b_player_no_effect = yes } }')
    event(413,'lyd_i3b_sign_t','lyd_i3b_event_context_trigger = yes this = scope:lyd_i3b_ballot_rite.var:lyd_i3b_delegate',
          'option = { name = lyd_i3b_sign trigger = { custom_description = { text = lyd_i3b_quorum_valid_tt subject = root scope:lyd_i3b_ballot_rite = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 } } } custom_tooltip = lyd_i3b_sign_choice_tt hidden_effect = { lyd_i3b_sign_effect = yes } ai_chance = { base = 60 } } option = { name = lyd_i3b_wait custom_tooltip = lyd_i3b_defer_choice_tt hidden_effect = { lyd_i3b_defer_signature_effect = yes } ai_chance = { base = 0 } } option = { name = lyd_i3b_no custom_tooltip = lyd_i3b_refuse_choice_tt hidden_effect = { lyd_i3b_sign_no_effect = yes } ai_chance = { base = 40 } }')
    event(430,'lyd_i3b_review_t','lyd_i3b_event_context_trigger = yes this = scope:lyd_i3b_actor',
          'option = { name = lyd_i3b_confirm trigger = { lyd_i3b_ready_trigger = { ACTOR = root } lyd_i3b_native_admitted_trigger = yes } custom_tooltip = lyd_i3b_commit_valid_tt custom_tooltip = lyd_i3b_commit_choice_tt hidden_effect = { lyd_i3b_commit_effect = yes } } option = { name = lyd_i3b_pending trigger = { NOT = { lyd_i3b_native_admitted_trigger = yes } } custom_tooltip = lyd_i3b_native_closed_tt } option = { name = lyd_i3b_wait } option = { name = lyd_i3b_cancel custom_tooltip = lyd_i3b_cancel_choice_tt hidden_effect = { lyd_i3b_cancel_event_effect = yes } }')
    # Result events intentionally use the persistent attempt receipt, not current
    # proposal guards (native enactment has changed doctrine and closed the round).
    result_identity = 'this = scope:lyd_i3b_actor var:lyd_i3b_result_serial = scope:lyd_i3b_result_event_serial var:lyd_i3b_result_nonce = scope:lyd_i3b_result_event_nonce'
    events.append(f'''lyd.431 = {{ type = character_event title = lyd_i3b_result_success_t desc = lyd_i3b_result_success_desc theme = faith
    trigger = {{ {result_identity} var:lyd_i3b_result_code = 1 }}
    option = {{ name = lyd_i3b_result_ack custom_tooltip = lyd_i3b_zero_fee_tt }}
}}''')
    events.append(f'''lyd.432 = {{ type = character_event title = lyd_i3b_result_failure_t desc = lyd_i3b_result_failure_desc theme = faith
    trigger = {{ {result_identity} var:lyd_i3b_result_code > 1 }}
    option = {{ name = lyd_i3b_result_ack custom_tooltip = lyd_i3b_zero_fee_tt
        if = {{ limit = {{ var:lyd_i3b_result_code = 2 }} custom_tooltip = lyd_i3b_result_identity_failed_tt }}
        if = {{ limit = {{ var:lyd_i3b_result_code = 3 }} custom_tooltip = lyd_i3b_result_factory_failed_tt }}
        if = {{ limit = {{ var:lyd_i3b_result_code = 4 }} custom_tooltip = lyd_i3b_result_rites_failed_tt }}
        if = {{ limit = {{ var:lyd_i3b_result_code = 5 }} custom_tooltip = lyd_i3b_result_political_failed_tt }}
        if = {{ limit = {{ var:lyd_i3b_result_code = 6 }} custom_tooltip = lyd_i3b_result_unclassified_tt }}
        if = {{ limit = {{ var:lyd_i3b_result_code = 7 }} custom_tooltip = lyd_i3b_result_native_hor_failed_tt }}
    }}
}}''')
    events.append('''lyd.439 = { type = character_event hidden = yes immediate = { hidden_effect = {
        # Phase/nomination nonce may legitimately change after start; expiration
        # checks original serial plus active status, never rewrites event context.
        if = { limit = { var:lyd_i3b_serial = scope:lyd_i3b_event_serial has_variable = lyd_i3b_phase }
            lyd_i3b_close_effect = yes debug_log = "LYD_I3B_EXPIRED"
        }
    } } }''')
    script('events/lyd_i3b_institution_events.txt','\n'.join(events))
    loc={
        'lyd_i3b_begin_decision':('议建共同体宗主制度','Propose a Communion Headship'),
        'lyd_i3b_nominate_self_decision':('明确提名自己参与本派代表推举','Offer Myself for Our School’s Nomination'),
        'lyd_i3b_seal_decision':('封定制度条款，征询诸儒','Seal the Terms and Seek Mandates'),
        'lyd_i3b_review_decision':('复核宗主制度议案','Review the Headship Proposal'),
        'lyd_i3b_cancel_decision':('撤回宗主制度议案','Withdraw the Headship Proposal'),
        'lyd_i3b_result_review_decision':('查阅上次宗主制度实施回执','Read the Last Headship Attempt Receipt'),
        'lyd_i3b_result_review_desc':('查看本人上次已保存的制度实施结果与失败类别；不会重试实施、收费或改动原生对象。','Read my last saved headship attempt result and failure class, without retrying enactment, charging fees or changing native objects.'),
        'lyd_i3b_nominate_interaction':('提名本派制度议案代表','Nominate a School Representative'),
        'lyd_i3b_terms_desc':('原版儒家的经学、道学及本模组新礼仪玩家均可发起建立真实宗主，不必改信或成为经学、道学的派领袖。议案保持原信仰、经学、道学、主礼仪及各派信条，但建立的是整个当前儒家信仰的世俗宗主制度：完整礼仪名单均由无宗主改为世俗宗主，原版经学、道学不豁免。首任候选人为发起者。每个活跃派（包括实际存在的经学、道学）须分别取得三分之二合格学者授权和提名代表签署；所有存活玩家须另行明确同意。休眠礼仪不贡献赞成票，但制度变化列入条款。旧独立共宗仍由主礼仪玩家发起，分离共同体仍须由实际主礼仪领袖发起。现有宗主、争议宗主或其他议案会阻止本轮；名单或资格改变须撤回重议。不得转移旧政治头衔或重写其继承。真实后置检查通过才确认成功。',
                                'Players of vanilla Jingxue, Daoxue or a new LYD rite within vanilla Confucianism may propose a real Head of Faith without converting or becoming the Jingxue/Daoxue rite head. The original Faith, Jingxue, Daoxue, main rite and all tenets remain. This establishes temporal headship for the entire current Faith: every captured rite replaces no head with temporal head, including vanilla rites without an opt-out. The initiator is the first candidate. Each active school, including actual Jingxue and Daoxue, needs its own two-thirds scholarly mandate and nominated representative signature; every living human separately consents. Dormant rites contribute no affirmative votes but their institution changes remain terms. Legacy Communion initiation still requires the main rite; detached communities still require their actual native main-rite head. Existing heads, challengers or competing proposals block the round. Roster or eligibility changes require withdrawal and a new round. Existing political titles and their succession must not be reassigned. Success requires actual postconditions.'),
        'lyd_i3b_nomination_t':('受议推举，尚非宗主','A Nomination, Not a Headship'),
        'lyd_i3b_ballot_t':('本派的制度授权','Our School’s Institutional Mandate'),
        'lyd_i3b_player_t':('我的共同体制度同意','My Consent to the Institution'),
        'lyd_i3b_sign_t':('依本派授权签署','Sign under Our School’s Mandate'),
        'lyd_i3b_review_t':('完整名单与制度条款','The Complete Roster and Terms'),
        'lyd_i3b_yes':('我明确赞成所示条款','I expressly support these terms'),
        'lyd_i3b_no':('我拒绝','I refuse'),
        'lyd_i3b_sign':('以授权代表身份签署','Sign as the mandated representative'),
        'lyd_i3b_wait':('待诸方答复','Await the parties'),
        'lyd_i3b_cancel':('撤回本轮','Withdraw this round'),
        'lyd_i3b_confirm':('按已重核授权实施','Enact the revalidated terms'),
        'lyd_i3b_pending':('本轮制度实施条件尚未齐备','This round is not ready for enactment'),
        'lyd_i3b_begin_valid_tt':('须为符合教士性别要求、在世成年且有公国以上头衔的儒家玩家，可属原版经学、道学或本模组新礼仪。原版儒家可直接发起，保留原信仰与主礼仪，并纳入全部实际礼仪（含经学、道学）的独立授权。旧独立共宗须属主礼仪；分离共同体还须本人为实际主礼仪领袖。信仰和全部礼仪须无宗主且教士制度兼容；不得已有宗主、争议宗主、其他职位或待办议案。','Requires a living adult Confucian player of vanilla Jingxue, Daoxue or a new LYD rite, with at least a duchy and permitted clergy gender. Vanilla Confucianism may initiate directly, preserving Faith and main rite while including every actual rite, including Jingxue and Daoxue, in independent authorization. Legacy Communion initiators must belong to the main rite; detached communities additionally require the actual native main-rite head. The Faith and all rites must be headless with compatible clergy, with no existing head, challenger, other office or pending proposal.'),
        'lyd_i3b_nominate_valid_tt':('本人须在世、成年、自由、非无能且实际学识至少15；学识不足仍可发起议案，但不能自提名。先撤回本轮，再合法培养或招揽同信仰、同礼仪的合格学者，实际达标后重议。践礼修身给予学识生活方式经验，不保证直接增加学识属性。','I must be living, adult, free, capable and have actual Learning of at least 15. Lower Learning does not prevent initiation, but prevents self-nomination. Withdraw first, then lawfully develop or recruit an eligible scholar of the same Faith and rite and start a new proposal. Cultivation grants Learning lifestyle experience, not a guaranteed direct Learning increase.'),
        'lyd_i3b_seal_valid_tt':('本轮草案与名单须仍有效；每个活跃派都须有已接受提名的合格学者代表与正数学者名额。缺代表须先推举。活跃派若无合格学者，请先撤回本轮，再通过正常教育、生活方式或实际可用的招揽、改信与转派途径，准备在世、成年、自由、非无能、同信仰同礼仪且实际学识至少15的人选，随后重新发起；仅招入宫廷或获得生活方式经验不等于达标。有信众但无学者的派不算休眠，不能补假票，各活跃派仍各需三分之二授权及代表签署。','The draft and roster must remain valid. Every active school needs an accepted eligible representative and a positive scholarly electorate. Nominate missing representatives first. If an active school has no eligible scholars, withdraw first. Use normal education, lifestyles or actually available recruitment, conversion and rite-adoption routes to prepare a living, adult, free, capable candidate of the same Faith and rite with actual Learning of at least 15, then initiate again. Court recruitment or lifestyle experience alone does not establish eligibility. A school with followers but no scholars is not dormant; no votes are invented, and each active school still needs its own two-thirds mandate and representative signature.'),
        'lyd_i3b_current_valid_tt':('发起者、共同体、主礼仪、完整名单、资格与本轮占用须仍与议案一致；失效后请撤回重议。','The initiator, Communion, main rite, full roster, eligibility and this round’s locks must still match. Withdraw and restart an invalid proposal.'),
        'lyd_i3b_cancel_valid_tt':('须为仍存活的玩家原发起者，且本人仍有本轮议案；转派、转信或失去发起资格仍可撤回。','Requires the living human initiator’s own active round. Withdrawal remains available after affiliation, faith or initiation eligibility changes.'),
        'lyd_i3b_result_valid_tt':('须为仍存活的玩家，且本人有已保存的制度实施回执。','Requires a living human player with a saved headship attempt receipt.'),
        'lyd_i3b_nomination_actor_valid_tt':('发起者的本轮草案、名单与资格须仍有效，且尚未封定。','The initiator’s draft, roster and eligibility must remain valid and the terms must be unsealed.'),
        'lyd_i3b_nomination_target_valid_tt':('候选人须为同共同体、本轮名册中的合格学者；其派须活跃、尚无已接受提名的代表。学者代表不等于现任原生派领袖。','The nominee must be a qualified scholar of this Communion on this round’s roster, in an active school without an accepted representative. This scholar mandate does not appoint a native Head of Rite.'),
        'lyd_i3b_quorum_valid_tt':('本派合格学者人数须为正数，且本派至少三分之二已明确赞成。','This school must have eligible scholars and at least two-thirds must expressly support the terms.'),
        'lyd_i3b_commit_valid_tt':('完整名单须重核通过；各活跃派各自达到三分之二并获代表签署，所有存活玩家另行同意，旧政治头衔仍归原主，且本次实施的身份与授权重核通过。','Requires a revalidated full roster, each active school’s own two-thirds and representative signature, separate consent from every living human, unchanged ownership of captured political titles, and revalidated identity and authorization for this attempt.'),
        'lyd_i3b_native_closed_tt':('本轮尚未满足实施条件：须重核完整名单、各派学者授权、代表签署与所有存活玩家的同意；身份或条款变化后须撤回重议。','This round does not yet meet its enactment conditions: recheck the complete roster, each school’s scholarly mandate, representative signatures and every living human’s consent. Withdraw and restart after identity or terms change.'),
        'lyd_i3b_nomination_choice_tt':('接受本派学者代表提名；这一步不投票、不签署，也不授予原生派领袖或宗主职位。','Accept the scholarly nomination only. This casts no vote or signature and grants no native Head of Rite or Head of Faith office.'),
        'lyd_i3b_ballot_choice_tt':('记下本人的一张赞成票；只计入本人所属派的授权。','Record my single affirmative ballot for my own school’s mandate.'),
        'lyd_i3b_ballot_no_choice_tt':('记下本人的一张反对票，不增加本派赞成票。','Record my single negative ballot without adding to my school’s affirmative votes.'),
        'lyd_i3b_player_choice_tt':('记下本人对本轮完整制度条款的明确玩家同意，与学者票分开。','Record my express human consent to this round’s complete terms, separately from scholarly ballots.'),
        'lyd_i3b_sign_choice_tt':('仅按本派已经达到的授权签署，不代替其他派或其他玩家同意。','Sign under my school’s existing mandate, without replacing another school’s mandate or another human’s consent.'),
        'lyd_i3b_defer_choice_tt':('暂不签署；本派可在之后重新收到签署请求。','Defer signing; this school may receive another signature request later.'),
        'lyd_i3b_refuse_choice_tt':('拒绝本轮条款，并撤回本轮议案；不实施制度变更。','Refuse the terms and close this proposal without enacting institutional changes.'),
        'lyd_i3b_cancel_choice_tt':('仅清理本人本轮匹配的占用与名册；旧弹窗不能清理新轮。','Clear only my matching locks and roster for this round; an old popup cannot close a newer round.'),
        'lyd_i3b_commit_choice_tt':('在执行前再次重核全部授权；真实原生后置检查通过才承认成功。未通过则保留实际部分状态，保存回执并显示失败。','Recheck every authorization before enactment. Recognize success only after real native postconditions pass. Otherwise retain actual partial state, save a receipt and show failure.'),
        'lyd_i3b_result_success_t':('宗主制度实施后置检查通过','Headship Attempt Postconditions Passed'),
        'lyd_i3b_result_success_desc':('本轮实际原生后置检查通过，并保存了本轮序号、共同体、主礼仪及真实办公头衔的回执。本轮审批已关闭；可用“查阅上次宗主制度实施回执”重看。该结果不证明政治全图的其他属性均不变。','This attempt passed its actual native postconditions. A receipt preserves its serial, Communion, main rite and real office title. The proposal is closed; use Read the Last Headship Attempt Receipt to revisit it. This result does not prove every other property of the political graph stayed unchanged.'),
        'lyd_i3b_result_failure_t':('宗主制度实施未获成功确认','Headship Attempt Failed Its Postconditions'),
        'lyd_i3b_result_failure_desc':('本轮原生后置检查未通过，不承认实施成功，也不收取费用。已保留真实的部分教义或头衔状态，没有伪造回滚；审批已关闭，保存本轮序号、共同体、主礼仪及失败类别。请先保存并独立读回实际状态，再作恢复决定；可用“查阅上次宗主制度实施回执”重新查看，此入口不会重试或修改原生对象。','This attempt failed its native postconditions. Success is not recognized and no fee is charged. Actual partial doctrine or title state is retained without an invented rollback. The proposal is closed and its serial, Communion, main rite and failure class are saved. Save and independently read back the actual state before deciding recovery. Read the Last Headship Attempt Receipt reopens this result without retrying or changing native objects.'),
        'lyd_i3b_result_ack':('知悉并保留回执','Acknowledge and Keep the Receipt'),
        'lyd_i3b_zero_fee_tt':('本轮制度流程费用为零。','This institutional flow charges no fee.'),
        'lyd_i3b_result_identity_failed_tt':('失败类别 2：共同体或主礼仪身份与本轮条款不一致。','Failure class 2: Communion or main-rite identity differs from this attempt’s terms.'),
        'lyd_i3b_result_factory_failed_tt':('失败类别 3：真实宗主办公头衔、归属或持有人后置检查未通过。','Failure class 3: the real head office title, ownership or holder failed its postcondition.'),
        'lyd_i3b_result_rites_failed_tt':('失败类别 4：捕获的完整礼仪名单未全部处于目标教义及共同体。','Failure class 4: the complete captured rite list does not share the target doctrine and Communion.'),
        'lyd_i3b_result_political_failed_tt':('失败类别 5：至少一项捕获的旧政治头衔已不再归原发起者。','Failure class 5: at least one captured pre-existing political title no longer belongs to the initiator.'),
        'lyd_i3b_result_native_hor_failed_tt':('实施后独立共同体的实际主礼仪领袖与本轮授权人不一致；保留真实原生状态，不补写领袖或宣告成功。','The detached Communion’s actual native main-rite head no longer matches this round’s authorized initiator after enactment. The real native state is retained without assigning a replacement or claiming success.'),
        'lyd_i3b_result_unclassified_tt':('失败类别 6：未分类后置失败，须独立读回实际对象后调查。','Failure class 6: unclassified postcondition failure; independently read back the actual objects before investigation.'),
        'lyd_i3b_doctrine_clause_tt':('制度条款：当前整个信仰及以下完整礼仪名单均由“无宗主”改为“世俗宗主”，原版经学、道学不豁免；不改信条、主礼仪或信众归属。首任候选：[lyd_i3b_actor.GetTitledFirstName]。休眠礼仪同列条款，但不贡献赞成票。',
                                     'Institution terms: the current Faith and complete following rite list replace no head with temporal head. Vanilla Jingxue/Daoxue do not opt out. Tenets, main rite and followers stay unchanged. First candidate: [lyd_i3b_actor.GetTitledFirstName]. Dormant rites are terms but contribute no affirmative votes.'),
    }
    loc.update({
        'lyd_i3b_npc_support_tt':('NPC的中性赞成／反对权重为60／40。对首任宗主候选（发起者）的好感至少50会提高支持，至多-50会降低支持；候选学识至少20会提高支持，不足10会降低支持。各项仅有限加权，赞成与反对始终都有可能；不替代玩家选择。本轮学者票不可改投；若要改善关系或培养候选后重议，请先撤回。各派进度为本轮捕获记录，名单与资格仍须完整重核，所有玩家同意另行要求。','Neutral NPC support/refusal weights are 60/40. Opinion of the first headship candidate (the initiator) of at least 50 raises support; at most -50 lowers it. Candidate Learning of at least 20 raises support; below 10 lowers it. These are finite weights: support and refusal remain possible and never replace human choices. Scholarly ballots cannot be recast this round; withdraw before improving relations or developing the candidate for a new round. School progress shows captured round records, subject to full roster and eligibility revalidation; every human must still consent separately.'),
        'lyd_i3b_progress_count_tt':('[lyd_i3b_progress_rite.GetName]：赞成 [lyd_i3b_progress_rite.MakeScope.Var(\'lyd_i3b_yes\').GetValue|0] ／合格学者 [lyd_i3b_progress_rite.MakeScope.Var(\'lyd_i3b_total\').GetValue|0]。','[lyd_i3b_progress_rite.GetName]: affirmative ballots [lyd_i3b_progress_rite.MakeScope.Var(\'lyd_i3b_yes\').GetValue|0] / eligible scholars [lyd_i3b_progress_rite.MakeScope.Var(\'lyd_i3b_total\').GetValue|0].'),
        'lyd_i3b_progress_dormant_tt':('本轮休眠礼仪：列入制度条款，但不贡献赞成票或代替活跃派授权。','Dormant this round: included in the institution terms, without affirmative votes or a mandate for an active school.'),
        'lyd_i3b_progress_quorum_tt':('本派已达到三分之二学者授权。','This school has reached its two-thirds scholarly mandate.'),
        'lyd_i3b_progress_no_quorum_tt':('本派尚未达到三分之二学者授权；合格学者为零也不能通过。','This school has not reached its two-thirds scholarly mandate; zero eligible scholars cannot pass.'),
        'lyd_i3b_progress_delegate_tt':('本派已接受提名的代表：[lyd_i3b_progress_delegate.GetTitledFirstName]。','Accepted representative: [lyd_i3b_progress_delegate.GetTitledFirstName].'),
        'lyd_i3b_progress_no_delegate_tt':('本派尚无已接受提名的代表。','This school has no accepted representative yet.'),
        'lyd_i3b_progress_signed_tt':('代表已签署本轮。','The representative has signed this round.'),
        'lyd_i3b_progress_unsigned_tt':('代表尚未签署本轮。','The representative has not signed this round.'),
        'lyd_i3b_progress_unknown_tt':('[lyd_i3b_progress_rite.GetName]：无法读取匹配本人本轮的完整进度记录；不按零票或已通过处理。','[lyd_i3b_progress_rite.GetName]: complete progress for my matching round is unavailable; this is neither zero ballots nor approval.'),
        'lyd_i3b_begin_complete_tt':('上述创设条件须全部满足。','All initiation conditions above must be met.'),
        'lyd_i3b_nominate_complete_tt':('上述提名条件须全部满足。','All nomination conditions above must be met.'),
        'lyd_i3b_begin_player_tt':('本人为玩家。','I am a human player.'),
        'lyd_i3b_begin_alive_tt':('本人在世。','I am alive.'),
        'lyd_i3b_begin_adult_tt':('本人已成年。','I am an adult.'),
        'lyd_i3b_begin_landed_tt':('本人有领地。','I am landed.'),
        'lyd_i3b_begin_capable_tt':('本人没有无能特质。','I do not have the Incapable trait.'),
        'lyd_i3b_begin_confucian_tt':('本人属于儒家宗教。','I belong to the Confucian religion.'),
        'lyd_i3b_begin_joined_tt':('本人属于原版儒家的受支持礼仪；旧共宗或分离共同体路线仍须先启用学派玩法。','I follow a supported rite of vanilla Confucianism; legacy or detached Communion routes still require school admission.'),
        'lyd_i3b_begin_new_rite_tt':('本人采用原版儒家的经学、道学或本模组新礼仪；其他路线须采用本模组新礼仪。','I follow Jingxue, Daoxue or a new mod rite within vanilla Confucianism; other routes require a new mod rite.'),
        'lyd_i3b_begin_authority_tt':('发起路线符合当前信仰：原版儒家经学、道学或新礼仪玩家可直接发起；旧独立共宗须属主礼仪；分离共同体须本人为实际主礼仪领袖。','My initiation route matches my Faith: a vanilla Confucian player of Jingxue, Daoxue or a new mod rite may initiate directly; legacy Communion requires its main rite; a detached Communion requires its actual main-rite head.'),
        'lyd_i3b_begin_duchy_tt':('本人最高头衔至少为公国。','My highest title is at least a duchy.'),
        'lyd_i3b_begin_gender_tt':('本人的性别符合当前礼仪的教士要求。','My gender is permitted for clergy by my current rite.'),
        'lyd_i3b_begin_offices_tt':('本人未持有宗主、争议宗主或本模组争统办公头衔。','I hold no headship, challenger or mod claim-office title.'),
        'lyd_i3b_begin_challenger_tt':('本人不是现任争议宗主。','I am not a current religious-head challenger.'),
        'lyd_i3b_begin_sponsor_tt':('本人不是现任争议宗主的赞助者。','I do not sponsor a current religious-head challenger.'),
        'lyd_i3b_begin_claim_tt':('本人没有尚未处理的争统头衔记录。','I have no outstanding mod claim-title record.'),
        'lyd_i3b_begin_own_round_tt':('本人没有正在进行的宗主制度议案。','I have no active headship proposal.'),
        'lyd_i3b_begin_c2_round_tt':('本人没有正在进行的分离共同体议案。','I have no active detached-Communion proposal.'),
        'lyd_i3b_begin_c3_round_tt':('本人没有正在进行的争统议案。','I have no active challenger proposal.'),
        'lyd_i3b_begin_supported_faith_tt':('当前信仰及其完整礼仪名单属于支持范围。','My Faith and its complete rite roster are supported.'),
        'lyd_i3b_begin_faith_doctrine_tt':('当前信仰采用无宗主制度。','My Faith has the No Head doctrine.'),
        'lyd_i3b_begin_head_title_tt':('当前信仰不存在宗主办公头衔（即使空缺也不允许）。','My Faith has no head-office title, including an unheld one.'),
        'lyd_i3b_begin_head_tt':('当前信仰不存在宗主。','My Faith has no religious head.'),
        'lyd_i3b_begin_faith_challengers_tt':('当前信仰不存在争议宗主。','My Faith has no religious-head challengers.'),
        'lyd_i3b_begin_compatible_rites_tt':('全部实际礼仪均兼容：无宗主、世俗教士，且没有世俗或属灵宗主及属灵任命教士制度。','Every actual rite is compatible: no head and lay clergy, with no temporal or spiritual head or spiritual clergy appointments.'),
        'lyd_i3b_begin_rite_rounds_tt':('全部实际礼仪均未被其他分离、争统或宗主议案占用。','No actual rite is locked by another detachment, challenger or headship proposal.'),
        'lyd_i3b_nominate_current_tt':('本轮草案、完整名单与资格仍有效；若已改变，请撤回重议。','This draft, complete roster and eligibility remain valid; withdraw and restart after changes.'),
        'lyd_i3b_nominate_alive_tt':('本人在世。','I am alive.'),
        'lyd_i3b_nominate_adult_tt':('本人已成年。','I am an adult.'),
        'lyd_i3b_nominate_free_tt':('本人未被囚禁。','I am not imprisoned.'),
        'lyd_i3b_nominate_capable_tt':('本人没有无能特质。','I do not have the Incapable trait.'),
        'lyd_i3b_nominate_learning_tt':('本人实际学识至少15；不足时不能自提名。先撤回，再合法培养或招揽同信仰同礼仪学者后重议；践礼修身的生活方式经验不保证直接增加学识。','My actual Learning is at least 15. Otherwise I cannot nominate myself: withdraw, lawfully develop or recruit a scholar of the same Faith and rite, then restart. Cultivation lifestyle experience does not guarantee a direct Learning increase.'),
        'lyd_i3b_nominate_phase_tt':('本轮仍在推举代表阶段，尚未封定。','This round is still in its unsealed nomination phase.'),
        'lyd_i3b_nominate_active_rite_tt':('本人所属礼仪为本轮活跃派。','My rite is active in this round.'),
        'lyd_i3b_nominate_delegate_tt':('本派尚无已接受提名的代表。','My school has no accepted representative yet.'),
    })
    for rite in catalogue.RITES:
        loc[f'lyd_i3b_term_{rite.slug}_tt']=(f'{rite.name_zh}：无宗主 → 世俗宗主。',f'{rite.name_en}: no head → temporal head.')
    loc['lyd_i3b_term_jingxue_tt']=('经学（原版）：无宗主 → 世俗宗主；保留原信条。','Jingxue (vanilla): no head → temporal head; original tenets retained.')
    loc['lyd_i3b_term_daoxue_tt']=('道学（原版）：无宗主 → 世俗宗主；保留原信条。','Daoxue (vanilla): no head → temporal head; original tenets retained.')
    for language,column in (('simp_chinese',0),('english',1)):
        lines=[f'l_{language}:',' # GENERATED FILE: edit tools/gen_institution.py; regenerate through gen_runtime.py.']
        for key,text in loc.items(): lines.append(f' {key}:0 "{text[column]}"')
        outputs[f'localization/{language}/lyd_i3b_institution_l_{language}.yml']=('\n'.join(lines)+'\n').encode('utf-8-sig')
    return outputs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=SOURCE)
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    outputs=build_outputs()
    mismatches=[]
    for relative,data in outputs.items():
        target=a.output_dir/relative
        if a.check:
            if not target.is_file() or target.read_bytes()!=data:mismatches.append(relative)
        else:
            if a.output_dir.resolve()==SOURCE.resolve():
                raise ValueError('Production runtime is owned by gen_runtime; use it to generate the complete projection')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
    if mismatches:
        print('Institution generated bytes differ: '+', '.join(mismatches));return 1
    print(f'Institution {"verified" if a.check else "generated externally"}: {len(outputs)} files; runtime authorization guarded; live acceptance NOT_RUN')
    return 0

if __name__=='__main__':raise SystemExit(main())
