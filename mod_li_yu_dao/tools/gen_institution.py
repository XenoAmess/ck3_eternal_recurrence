"""Generate the consented headship charter extension; no native execution.

No release admission: native doctrine/factory conjunction defaults closed.
gen_runtime owns the production runtime projection; native enactment stays closed.
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
lyd_i3b_native_admitted_trigger = { always = no }
lyd_i3b_owned_rite_trigger = { @OWNED@ }
lyd_i3b_compatible_rite_trigger = {
    lyd_i3b_owned_rite_trigger = yes
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
lyd_i3b_actor_trigger = {
    lyd_c3_player_actor_trigger = yes
    faith = faith:lyd_common_faith
    rite = faith.main_rite
    highest_held_title_tier >= tier_duchy
    save_temporary_scope_as = lyd_i3b_actor_check
    rite = { rite_has_allowed_gender_for_clergy = scope:lyd_i3b_actor_check }
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
        NOT = { exists = religious_head_title }
        NOT = { exists = religious_head }
        NOT = { any_faith_rite = { NOT = { lyd_i3b_compatible_rite_trigger = yes } } }
        NOT = { any_faith_rite = { OR = { has_variable = lyd_c2_proposal_owner has_variable = lyd_c3_proposal_owner has_variable = lyd_i3b_owner } } }
    }
}
# Character ROOT, immutable absolute ACTOR parameter. Revalidate the full roster.
lyd_i3b_current_trigger = {
    lyd_i3b_actor_trigger = yes
    has_variable = lyd_i3b_active
    faith = var:lyd_i3b_faith
    rite = var:lyd_i3b_main
    faith.main_rite = var:lyd_i3b_main
    NOT = { has_variable = lyd_c2_active }
    NOT = { has_variable = lyd_c3_active }
    faith = {
        NOT = { exists = religious_head_title }
        NOT = { exists = religious_head }
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
        NOT = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 var:lyd_i3b_signed = 1 exists = var:lyd_i3b_delegate }
    } }
    NOT = { any_in_list = { variable = lyd_i3b_members var:lyd_i3b_was_player = 1 NOT = { var:lyd_i3b_player_yes = 1 } } }
    NOT = { any_in_list = { variable = lyd_i3b_political_titles NOT = { holder = $ACTOR$ } } }
}
'''.replace('@OWNED@',owned))
    script('common/script_values/lyd_i3b_institution_values.txt',r'''
lyd_i3b_quorum_value = { value = var:lyd_i3b_yes multiply = 3 subtract = { value = var:lyd_i3b_total multiply = 2 } }
''')
    terms=['lyd_i3b_show_terms_effect = {','    custom_tooltip = lyd_i3b_doctrine_clause_tt',
           '    every_in_list = { variable = lyd_i3b_rites']
    for rite in catalogue.RITES:
        terms.append(f'        if = {{ limit = {{ this = rite:{rite.script_id} }} custom_tooltip = lyd_i3b_term_{rite.slug}_tt }}')
    terms += ['    }','}']
    script('common/scripted_effects/lyd_i3b_terms_effects.txt','\n'.join(terms))
    script('common/scripted_effects/lyd_i3b_setup_effects.txt',r'''
lyd_i3b_bind_event_effect = {
    save_scope_as = lyd_i3b_actor
    save_scope_value_as = { name = lyd_i3b_event_serial value = var:lyd_i3b_serial }
    save_scope_value_as = { name = lyd_i3b_event_nonce value = var:lyd_i3b_nonce }
    save_scope_value_as = { name = lyd_i3b_event_phase value = var:lyd_i3b_phase }
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
    clear_variable_list = lyd_i3b_rites clear_variable_list = lyd_i3b_members clear_variable_list = lyd_i3b_political_titles
    # Actor serial and nonce are intentionally monotone and survive cleanup.
}
''')
    script('common/scripted_effects/lyd_i3b_commit_effects.txt',r'''
# Only this effect changes native doctrine; pending proposals never call it.
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
        # Every currently captured rite, including dormant templates, is a signed term.
        var:lyd_i3b_faith = { remove_doctrine = doctrine_no_head add_doctrine = doctrine_temporal_head }
        every_in_list = { variable = lyd_i3b_rites
            if = { limit = { rite_has_doctrine = doctrine_no_head } change_rite_doctrine = doctrine_temporal_head }
        }
        set_variable = { name = lyd_c3_head_creation_authorized value = 1 }
        lyd_c3_create_owned_temporal_head_effect = yes
        remove_variable = lyd_c3_head_creation_authorized
        if = { limit = {
            faith = var:lyd_i3b_faith rite = var:lyd_i3b_main faith.main_rite = var:lyd_i3b_main
            faith.religious_head = this faith = { lyd_c3_owned_current_head_trigger = yes }
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
            if = { limit = { NOT = { faith = var:lyd_i3b_faith rite = var:lyd_i3b_main faith.main_rite = var:lyd_i3b_main } }
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
            shown+=' NOT = { has_variable = lyd_i3b_active }'
        description='lyd_i3b_result_review_desc' if suffix=='result_review' else 'lyd_i3b_terms_desc'
        decisions.append(f'''{name} = {{
    picture = {{ reference = "gfx/interface/illustrations/decisions/decision_personal_religious.dds" }}
    decision_group_type = religious ai_check_interval = 0
    desc = {description} selection_tooltip = {description} confirm_text = {name}
    is_shown = {{ {shown} }}
    is_valid = {{ custom_description = {{ text = {tooltip} subject = root {gate} }} }}
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
    def event(id,title,gate,options):
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
          'option = { name = lyd_i3b_confirm trigger = { custom_description = { text = lyd_i3b_commit_valid_tt subject = root lyd_i3b_ready_trigger = { ACTOR = root } lyd_i3b_native_admitted_trigger = yes } } custom_tooltip = lyd_i3b_commit_choice_tt hidden_effect = { lyd_i3b_commit_effect = yes } } option = { name = lyd_i3b_pending trigger = { custom_description = { text = lyd_i3b_native_closed_tt subject = root NOT = { lyd_i3b_native_admitted_trigger = yes } } } } option = { name = lyd_i3b_wait } option = { name = lyd_i3b_cancel custom_tooltip = lyd_i3b_cancel_choice_tt hidden_effect = { lyd_i3b_cancel_event_effect = yes } }')
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
        'lyd_i3b_terms_desc':('本轮拟由无宗主改为世俗宗主，首任候选人为发起者；仅替换儒家共宗及本轮完整礼仪名单的宗主教义，不改信条、主礼仪、政治领属、政体或土地。活跃派须各得三分之二合格学者授权、明确提名的代表签署；所有存活玩家须另行同意。无信众且无伯爵领的休眠模板不作赞成票，但其教义变更仍列入条款。任何新礼仪、名单、人选、宗主教义、教士兼容条件或归属变动均须重议。原生制度实施尚待独立核验。',
                                'These terms replace no-head with temporal-head for this Confucian Communion and its complete captured rite list, naming the initiator as the first candidate. Tenets, main rite, political allegiance, governments and land are unchanged. Every active school requires its own two-thirds scholarly mandate and a nominated representative signature; every living human player separately consents. Empty templates count as no affirmative votes, but their doctrine changes remain explicit terms. Any roster, representative, head doctrine, clergy compatibility or affiliation change requires a new round. Native enactment awaits separate verification.'),
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
        'lyd_i3b_pending':('原生制度实施尚待核验','Native enactment awaits verification'),
        'lyd_i3b_begin_valid_tt':('须为合格的主礼仪玩家发起者；共同体与全部礼仪均无宗主且教士制度兼容，没有其他议案占用。','Requires an eligible main-rite player initiator, compatible headless Communion and rites, and no competing proposal locks.'),
        'lyd_i3b_nominate_valid_tt':('本轮草案与名单须仍有效；本人须为本派合格学者，且本派活跃、尚无已接受提名的代表。','The draft and roster must remain valid; I must be a qualified scholar of an active school without an accepted representative.'),
        'lyd_i3b_seal_valid_tt':('本轮草案与名单须仍有效；每个活跃派都须有已接受提名的合格学者代表与正数学者名额。缺代表须先推举；活跃派若无合格学者，须先实际补足资格，再撤回重议，不能算作休眠或补假票。','The draft and roster must remain valid. Every active school needs an accepted qualified representative and at least one eligible scholar. Nominate missing representatives first. An active school with no eligible scholars must acquire real qualifications, then withdraw and restart; it cannot count as dormant or receive invented votes.'),
        'lyd_i3b_current_valid_tt':('发起者、共同体、主礼仪、完整名单、资格与本轮占用须仍与议案一致；失效后请撤回重议。','The initiator, Communion, main rite, full roster, eligibility and this round’s locks must still match. Withdraw and restart an invalid proposal.'),
        'lyd_i3b_cancel_valid_tt':('须为仍存活的玩家原发起者，且本人仍有本轮议案；转派、转信或失去发起资格仍可撤回。','Requires the living human initiator’s own active round. Withdrawal remains available after affiliation, faith or initiation eligibility changes.'),
        'lyd_i3b_result_valid_tt':('须为仍存活的玩家，且本人有已保存的制度实施回执。','Requires a living human player with a saved headship attempt receipt.'),
        'lyd_i3b_nomination_actor_valid_tt':('发起者的本轮草案、名单与资格须仍有效，且尚未封定。','The initiator’s draft, roster and eligibility must remain valid and the terms must be unsealed.'),
        'lyd_i3b_nomination_target_valid_tt':('候选人须为同共同体、本轮名册中的合格学者；其派须活跃、尚无已接受提名的代表。学者代表不等于现任原生派领袖。','The nominee must be a qualified scholar of this Communion on this round’s roster, in an active school without an accepted representative. This scholar mandate does not appoint a native Head of Rite.'),
        'lyd_i3b_quorum_valid_tt':('本派合格学者人数须为正数，且本派至少三分之二已明确赞成。','This school must have eligible scholars and at least two-thirds must expressly support the terms.'),
        'lyd_i3b_commit_valid_tt':('完整名单须重核通过；各活跃派各自达到三分之二并获代表签署，所有存活玩家另行同意，旧政治头衔仍归原主，且原生实施门禁已独立获准。','Requires a revalidated full roster, each active school’s own two-thirds and representative signature, separate consent from every living human, unchanged ownership of captured political titles, and independently admitted native enactment.'),
        'lyd_i3b_native_closed_tt':('原生制度实施门禁关闭，尚无本流程实机批准。','Native enactment is closed; this formal flow has no live admission.'),
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
        'lyd_i3b_result_unclassified_tt':('失败类别 6：未分类后置失败，须独立读回实际对象后调查。','Failure class 6: unclassified postcondition failure; independently read back the actual objects before investigation.'),
        'lyd_i3b_doctrine_clause_tt':('本轮教义条款：仅将以下已捕获礼仪的“无宗主”替换为“世俗宗主”；主礼仪与儒家共宗同步。首任候选：[lyd_i3b_actor.GetTitledFirstName]。这份名单包括休眠模板，休眠模板不贡献赞成票。',
                                    'Doctrine terms: replace no head with temporal head only for the following captured rites, including the main rite and its Confucian Communion. First candidate: [lyd_i3b_actor.GetTitledFirstName]. Dormant templates are explicit terms and contribute no affirmative votes.'),
    }
    for rite in catalogue.RITES:
        loc[f'lyd_i3b_term_{rite.slug}_tt']=(f'{rite.name_zh}：无宗主 → 世俗宗主。',f'{rite.name_en}: no head → temporal head.')
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
    print(f'Institution {"verified" if a.check else "generated externally"}: {len(outputs)} files; native enactment CLOSED')
    return 0

if __name__=='__main__':raise SystemExit(main())
