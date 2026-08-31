#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Zhongguo 361 phase-two central serial dispatcher.

This package owns orchestration only.  It calls each domain's documented
public adapter, freezes one post-B1 subject, and never edits domain runtimes.
Generated source is static-ready evidence, not CK3/MCP live evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_phase2_central_runtime.py\n"
READINESS = "static-ready"

LANGUAGES = (
    ("english", "l_english"),
    ("french", "l_french"),
    ("german", "l_german"),
    ("japanese", "l_japanese"),
    ("korean", "l_korean"),
    ("polish", "l_polish"),
    ("russian", "l_russian"),
    ("simp_chinese", "l_simp_chinese"),
    ("spanish", "l_spanish"),
)

STAGES = (
    (1, "career_hc", "zg361_career_hc_open_portfolio_effect"),
    (2, "compensation", "zg361_comp_portfolio_open_next_effect"),
    (3, "feedback_promotion_pip", "zg361_pp_manager_portfolio_adapter_effect"),
    (4, "incident_x", "zg361_ip_open_x_case_effect"),
    (5, "incident_y", "zg361_ip_open_y_case_effect"),
    (6, "incident_z", "zg361_ip_open_z_case_effect"),
    (7, "metrics_delivery", "zg361_p3_open_portfolio_effect"),
    (8, "credit_project", "zg361_cp_open_portfolio_effect"),
    (9, "career_learning", "zg361_cl_dispatch_direct_reports_effect"),
    (10, "manager_governance", "zg361_mg_dispatch_subordinate_managers_effect"),
    (11, "workforce_endgame", "zg361_we_open_portfolio_effect"),
)


def incident_stage(stage: int, domain: str, terminal_state: int) -> str:
    return f"""
# Stage {stage}: one incident domain only.  The all-domain portfolio ABI is
# intentionally not used, so X/Y/Z can never flood the player together.
zg361_p2c_stage_{stage:02d}_{domain}_effect = {{
    if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                has_variable = zg361_ip_{domain}_final_owner
                has_variable = zg361_ip_{domain}_final_subject
                has_variable = zg361_ip_{domain}_final_cycle
                has_variable = zg361_ip_{domain}_final_case
                has_variable = zg361_ip_{domain}_final_state
                var:zg361_ip_{domain}_final_owner = root
                var:zg361_ip_{domain}_final_subject = this
                var:zg361_ip_{domain}_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_ip_{domain}_final_state = {terminal_state}
                var:zg361_case_{domain}_active = 0
                var:zg361_ip_{domain}_final_case = var:zg361_case_{domain}_case_serial
            }}
        }}
        zg361_p2c_record_stage_effect = {{ STATUS = 2 STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }}
    }}
    else_if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                has_variable = zg361_case_{domain}_owner
                has_variable = zg361_case_{domain}_subject
                has_variable = zg361_case_{domain}_cycle_serial
                has_variable = zg361_case_{domain}_case_serial
                has_variable = zg361_case_{domain}_active
                var:zg361_case_{domain}_owner = root
                var:zg361_case_{domain}_subject = this
                var:zg361_case_{domain}_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_case_{domain}_active = 1
            }}
        }}
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = {{ DAYS = 2 }}
    }}
    else_if = {{
        limit = {{ var:zg361_p2c_stage_status = 0 }}
        zg361_ip_open_{domain}_case_effect = {{ SUBJECT = var:zg361_p2c_subject }}
        if = {{
            limit = {{
                var:zg361_p2c_subject = {{
                    has_variable = zg361_case_{domain}_owner
                    has_variable = zg361_case_{domain}_subject
                    has_variable = zg361_case_{domain}_cycle_serial
                    has_variable = zg361_case_{domain}_active
                    var:zg361_case_{domain}_owner = root
                    var:zg361_case_{domain}_subject = this
                    var:zg361_case_{domain}_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_{domain}_active = 1
                }}
            }}
            set_variable = {{ name = zg361_p2c_stage_status value = 1 }}
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = {{ DAYS = 2 }}
        }}
        else = {{ zg361_p2c_record_red_effect = {{ CODE = {400 + stage} STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }} }}
    }}
    else = {{ zg361_p2c_record_red_effect = {{ CODE = {450 + stage} STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }} }}
}}
"""


def render_effects() -> str:
    incidents = "".join(
        incident_stage(stage, domain, terminal)
        for stage, domain, terminal in ((4, "x", 8), (5, "y", 6), (6, "z", 6))
    )
    return HEADER + r'''# Zhongguo 361 phase-two central runtime: serial adapters only.
# Status: 0 unopened, 1 running, 2 success, 3 not-applicable,
# 4 typed RED, 5 external dependency.  Managers are celestial dukes+;
# counts/barons remain valid assessed subjects but can never be ROOT.

zg361_p2c_mark_lane_busy_effect = {
    set_variable = { name = zg361_p2c_stage_status value = 1 }
    if = { limit = { is_ai = no } set_variable = { name = zg361_p2c_ui_lane_busy value = 1 } }
    else = { set_variable = { name = zg361_p2c_ui_lane_busy value = 0 } }
}

# Every delayed poll carries manager + central case + cycle + stage + ticket.
# Scheduling a newer ticket makes every older delayed copy a strict no-op.
zg361_p2c_schedule_pump_effect = {
    if = {
        limit = { var:zg361_p2c_active = 1 }
        if = { limit = { NOT = { has_variable = zg361_p2c_ticket_serial } } set_variable = { name = zg361_p2c_ticket_serial value = 0 } }
        change_variable = { name = zg361_p2c_ticket_serial add = 1 }
        save_scope_as = zg361_p2c_ticket_manager
        save_scope_value_as = { name = zg361_p2c_ticket_cycle value = var:zg361_p2c_cycle }
        save_scope_value_as = { name = zg361_p2c_ticket_case value = var:zg361_p2c_case_serial }
        save_scope_value_as = { name = zg361_p2c_ticket_stage value = var:zg361_p2c_stage }
        save_scope_value_as = { name = zg361_p2c_ticket_identity value = var:zg361_p2c_ticket_serial }
        trigger_event = { id = zg361p2c.1 days = $DAYS$ }
    }
}

zg361_p2c_queue_summary_effect = {
    if = {
        limit = { is_ai = no NOT = { has_variable = zg361_p2c_summary_pending } }
        set_variable = { name = zg361_p2c_summary_pending value = 1 }
        save_scope_value_as = { name = zg361_p2c_summary_cycle value = var:zg361_p2c_cycle }
        save_scope_value_as = { name = zg361_p2c_summary_case value = var:zg361_p2c_case_serial }
        trigger_event = { id = zg361p2c.2 days = 1 }
    }
    else_if = { limit = { is_ai = yes } debug_log = "ZG361P2C: eligible AI central portfolio completed silently" }
}

zg361_p2c_record_stage_effect = {
    set_variable = { name = $STAGE_VAR$ value = $STATUS$ }
    set_variable = { name = zg361_p2c_stage_status value = $STATUS$ }
    if = { limit = { var:zg361_p2c_stage_status = 2 } change_variable = { name = zg361_p2c_success_n add = 1 } }
    else_if = { limit = { var:zg361_p2c_stage_status = 3 } change_variable = { name = zg361_p2c_na_n add = 1 } }
    else_if = { limit = { var:zg361_p2c_stage_status = 4 } change_variable = { name = zg361_p2c_red_n add = 1 } }
    change_variable = { name = zg361_p2c_stage add = 1 }
    set_variable = { name = zg361_p2c_stage_status value = 0 }
    set_variable = { name = zg361_p2c_wait_reason value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    zg361_p2c_schedule_pump_effect = { DAYS = 2 }
}

zg361_p2c_record_red_effect = {
    set_variable = { name = zg361_p2c_last_red_code value = $CODE$ }
    zg361_p2c_record_stage_effect = { STATUS = 4 STAGE_VAR = $STAGE_VAR$ }
}

zg361_p2c_mark_external_wait_effect = {
    if = {
        limit = { NOT = { var:zg361_p2c_wait_reason = $REASON$ } }
        change_variable = { name = zg361_p2c_external_n add = 1 }
    }
    set_variable = { name = $STAGE_VAR$ value = 5 }
    set_variable = { name = zg361_p2c_stage_status value = 5 }
    set_variable = { name = zg361_p2c_wait_reason value = $REASON$ }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    zg361_p2c_schedule_pump_effect = { DAYS = 2 }
}

# A frozen primary subject dying, changing direct manager, or changing its
# owner/cycle/case tuple aborts the central case.  It never silently substitutes
# another official and never writes into a new B1 season.
zg361_p2c_abort_stale_effect = {
    set_variable = { name = zg361_p2c_last_red_code value = $CODE$ }
    set_variable = { name = zg361_p2c_stage_status value = 4 }
    change_variable = { name = zg361_p2c_red_n add = 1 }
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 4 }
    set_variable = { name = zg361_p2c_completed_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: frozen central tuple became stale; typed RED"
}

zg361_p2c_finish_effect = {
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 2 }
    if = { limit = { var:zg361_p2c_red_n > 0 } set_variable = { name = zg361_p2c_terminal_state value = 4 } }
    set_variable = { name = zg361_p2c_completed_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: serial phase-two portfolio reached a terminal summary"
}

# A package-level dependency may make further progress impossible without a
# public domain seam.  Suspend honestly: no central completed-cycle marker and
# no repeated poll, but one summary records terminal_state=external.
zg361_p2c_suspend_external_effect = {
    if = { limit = { NOT = { var:zg361_p2c_wait_reason = $REASON$ } } change_variable = { name = zg361_p2c_external_n add = 1 } }
    set_variable = { name = $STAGE_VAR$ value = 5 }
    set_variable = { name = zg361_p2c_stage_status value = 5 }
    set_variable = { name = zg361_p2c_wait_reason value = $REASON$ }
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 5 }
    set_variable = { name = zg361_p2c_suspended_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: central portfolio suspended on an external domain dependency"
}

# Hook 1: called only after B1 is published and review_in_progress is cleared.
# It freezes one deterministic current-result subject and merely queues D+2;
# no domain adapter is opened inside the publication stack.
zg361_p2c_on_review_published_effect = {
    # A newer B1 publication may arrive while an older central portfolio is
    # still active.  Terminate the old immutable tuple first; never overwrite
    # its case/stage/ticket in place.
    if = {
        limit = {
            has_variable = zg361_p2c_active
            var:zg361_p2c_active = 1
            has_variable = zg361_p2c_cycle
            has_variable = zg361_review_serial
            NOT = { var:zg361_p2c_cycle = var:zg361_review_serial }
        }
        set_variable = { name = zg361_p2c_previous_aborted_cycle value = var:zg361_p2c_cycle }
        set_variable = { name = zg361_p2c_deferred_reinit_cycle value = var:zg361_review_serial }
        set_variable = { name = zg361_p2c_deferred_reinit_b1_case value = var:zg361_b1_case_serial }
        set_variable = { name = zg361_p2c_deferred_reinit value = 1 }
        zg361_p2c_abort_stale_effect = { CODE = 9101 }
        trigger_event = { id = zg361p2c.3 days = 2 }
    }
    if = {
        limit = {
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            has_variable = zg361_b1_cycle_serial
            has_variable = zg361_b1_case_serial
            has_variable = zg361_b1_cycle_state
            has_variable = zg361_b1_closure_state
            var:zg361_b1_cycle_serial = var:zg361_review_serial
            var:zg361_b1_cycle_state = 8
            var:zg361_b1_closure_state = 4
            # Publication closure has exactly one proof route selected by the
            # explicit M013 mode.  A stale/current receipt can never satisfy
            # route C, and policy debt can never substitute for route A/B.
            OR = {
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode != 3
                    has_variable = zg361_b1_m013_receipt_serial
                    var:zg361_b1_m013_receipt_serial = var:zg361_b1_case_serial
                }
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode = 3
                    has_variable = zg361_b1_m013_policy_debt_serial
                    var:zg361_b1_m013_policy_debt_serial = var:zg361_b1_case_serial
                }
            }
            NOT = { has_character_flag = zg361_review_in_progress }
            NOT = { has_variable = zg361_p2c_deferred_reinit }
            trigger_if = {
                limit = { has_variable = zg361_p2c_active }
                var:zg361_p2c_active = 0
            }
            trigger_else = { always = yes }
            trigger_if = {
                limit = { has_variable = zg361_p2c_started_cycle }
                NOT = { var:zg361_p2c_started_cycle = var:zg361_review_serial }
            }
            trigger_else = { always = yes }
            trigger_if = {
                limit = { has_variable = zg361_p2c_completed_cycle }
                NOT = { var:zg361_p2c_completed_cycle = var:zg361_review_serial }
            }
            trigger_else = { always = yes }
            any_vassal = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                has_variable = zg361_b1_case_owner
                has_variable = zg361_b1_case_subject
                has_variable = zg361_b1_cycle_serial
                has_variable = zg361_b1_case_serial
                has_variable = zg361_b1_case_state
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
                var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
                var:zg361_b1_case_state = 8
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
            }
        }
        if = { limit = { NOT = { has_variable = zg361_p2c_case_cursor } } set_variable = { name = zg361_p2c_case_cursor value = 0 } }
        if = { limit = { var:zg361_p2c_case_cursor >= 999999 } set_variable = { name = zg361_p2c_case_cursor value = 0 } }
        change_variable = { name = zg361_p2c_case_cursor add = 1 }
        ordered_vassal = {
            limit = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
                var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
                var:zg361_b1_case_state = 8
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
            }
            order_by = stewardship
            position = 0
            save_temporary_scope_as = zg361_p2c_selected_subject
            root = {
                set_variable = { name = zg361_p2c_started_cycle value = var:zg361_review_serial }
                set_variable = { name = zg361_p2c_active value = 1 }
                set_variable = { name = zg361_p2c_case_serial value = var:zg361_p2c_case_cursor }
                set_variable = { name = zg361_p2c_b1_owner value = this }
                set_variable = { name = zg361_p2c_b1_cycle value = var:zg361_b1_cycle_serial }
                set_variable = { name = zg361_p2c_b1_case value = var:zg361_b1_case_serial }
                set_variable = { name = zg361_p2c_cycle value = var:zg361_review_serial }
                set_variable = { name = zg361_p2c_subject value = scope:zg361_p2c_selected_subject }
                set_variable = { name = zg361_p2c_result_owner value = this }
                set_variable = { name = zg361_p2c_result_subject value = scope:zg361_p2c_selected_subject }
                set_variable = { name = zg361_p2c_result_cycle value = scope:zg361_p2c_selected_subject.var:zg361_result_cycle_serial }
                set_variable = { name = zg361_p2c_result_case value = scope:zg361_p2c_selected_subject.var:zg361_result_case_serial }
                set_variable = { name = zg361_p2c_result_state_at_publish value = scope:zg361_p2c_selected_subject.var:zg361_result_case_state }
                set_variable = { name = zg361_p2c_result_grade_at_publish value = scope:zg361_p2c_selected_subject.var:zg361_result_grade }
                set_variable = { name = zg361_p2c_stage value = 1 }
                set_variable = { name = zg361_p2c_stage_status value = 0 }
                set_variable = { name = zg361_p2c_wait_reason value = 0 }
                set_variable = { name = zg361_p2c_ticket_serial value = 0 }
                set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
                set_variable = { name = zg361_p2c_success_n value = 0 }
                set_variable = { name = zg361_p2c_na_n value = 0 }
                set_variable = { name = zg361_p2c_red_n value = 0 }
                set_variable = { name = zg361_p2c_external_n value = 0 }
                remove_variable = zg361_p2c_last_red_code
                remove_variable = zg361_p2c_summary_pending
                if = { limit = { has_variable_list = zg361_p2c_mg_subjects } clear_variable_list = zg361_p2c_mg_subjects }
                set_variable = { name = zg361_p2c_mg_expected value = 0 }
                set_variable = { name = zg361_p2c_mg_completed value = 0 }
                set_variable = { name = zg361_p2c_mg_invalid value = 0 }
                set_variable = { name = zg361_p2c_last_noop_code value = 0 }
                zg361_p2c_schedule_pump_effect = { DAYS = 2 }
            }
        }
        debug_log = "ZG361P2C: post-publication central tuple frozen; first pump D+2"
    }
    else_if = {
        limit = {
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            OR = {
                AND = { has_variable = zg361_p2c_started_cycle var:zg361_p2c_started_cycle = var:zg361_review_serial }
                AND = { has_variable = zg361_p2c_completed_cycle var:zg361_p2c_completed_cycle = var:zg361_review_serial }
            }
        }
        set_variable = { name = zg361_p2c_last_noop_code value = 1 }
        debug_log = "ZG361P2C: duplicate publication hook ignored"
    }
    else = { debug_log = "ZG361P2C: unauthorized or incomplete publication hook ignored" }
}

# Hook 2: called in subject scope only after the 3.25 settlement receipt and B2
# delivery hook.  It can only invalidate/reschedule the exact waiting central
# ticket; it cannot initialize a case or change the frozen subject.
zg361_p2c_on_result_delivered_effect = {
    if = {
        limit = {
            has_variable = zg361_result_case_owner
            has_variable = zg361_result_cycle_serial
            has_variable = zg361_result_case_serial
            has_variable = zg361_result_case_state
            var:zg361_result_case_state = 3
        }
        save_temporary_scope_as = zg361_p2c_delivered_subject
        var:zg361_result_case_owner = {
            if = {
                limit = {
                    zg361_is_celestial_liege_trigger = yes
                    has_variable = zg361_p2c_active
                    var:zg361_p2c_active = 1
                    has_variable = zg361_p2c_subject
                    has_variable = zg361_p2c_cycle
                    has_variable = zg361_p2c_result_case
                    var:zg361_p2c_subject = scope:zg361_p2c_delivered_subject
                    var:zg361_p2c_cycle = scope:zg361_p2c_delivered_subject.var:zg361_result_cycle_serial
                    var:zg361_p2c_result_case = scope:zg361_p2c_delivered_subject.var:zg361_result_case_serial
                    OR = { var:zg361_p2c_stage = 2 var:zg361_p2c_stage = 7 }
                    var:zg361_p2c_wait_reason = 325
                }
                set_variable = { name = zg361_p2c_stage_status value = 0 }
                set_variable = { name = zg361_p2c_wait_reason value = 0 }
                zg361_p2c_schedule_pump_effect = { DAYS = 1 }
                debug_log = "ZG361P2C: exact delivered 3.25 woke its waiting central case"
            }
        }
    }
}

# The next three domain ABIs are manager-scoped and select their own first
# eligible subject.  Preflight the exact deterministic selection before the
# call, so eligibility drift can produce a central RED without ever opening an
# orphan case on somebody other than the frozen primary.
zg361_p2c_call_career_hc_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    remove_variable = zg361_p2c_adapter_candidate
    ordered_vassal = {
        limit = {
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            trigger_if = { limit = { has_variable = zg361_ch_portfolio_cycle } NOT = { var:zg361_ch_portfolio_cycle = root.var:zg361_review_serial } }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_d_active } var:zg361_case_d_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_m_active } var:zg361_case_m_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_n_active } var:zg361_case_n_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_o_active } var:zg361_case_o_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_p_active } var:zg361_case_p_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_q_active } var:zg361_case_q_active = 0 }
            trigger_else = { always = yes }
        }
        order_by = stewardship
        position = 0
        save_temporary_scope_as = zg361_p2c_preflight_candidate
        root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
    }
    if = {
        limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
        zg361_career_hc_open_portfolio_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
}

zg361_p2c_call_compensation_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    if = {
        limit = {
            has_variable = zg361_comp_portfolio_subject
            var:zg361_comp_portfolio_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
        }
        zg361_comp_portfolio_open_next_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
    else_if = {
        limit = {
            OR = {
                NOT = { has_variable = zg361_comp_portfolio_domain }
                var:zg361_comp_portfolio_domain = 1
            }
            NOT = { has_variable = zg361_comp_portfolio_subject }
        }
        remove_variable = zg361_p2c_adapter_candidate
        ordered_vassal = {
            limit = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
                var:zg361_result_case_state >= 3
                OR = { var:zg361_result_grade = 1 var:zg361_result_grade = 2 var:zg361_result_grade = 3 }
            }
            order_by = stewardship
            position = 0
            save_temporary_scope_as = zg361_p2c_preflight_candidate
            root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
        }
        if = {
            limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
            zg361_comp_portfolio_open_next_effect = yes
            set_variable = { name = zg361_p2c_adapter_called value = 1 }
        }
    }
}

zg361_p2c_call_pp_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    remove_variable = zg361_p2c_adapter_candidate
    ordered_vassal = {
        limit = { zg361_is_reviewable_vassal_trigger = yes liege = root }
        order_by = stewardship
        position = 0
        save_temporary_scope_as = zg361_p2c_preflight_candidate
        root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
    }
    if = {
        limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
        zg361_pp_manager_portfolio_adapter_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
}

# Stage 1: Career/HC owns the same deterministic primary subject later consumed
# by Workforce.  Completion requires both manager and subject terminal markers.
zg361_p2c_stage_01_career_hc_effect = {
    if = {
        limit = {
            var:zg361_ch_manager_portfolio_completed_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_subject = {
                var:zg361_ch_portfolio_closed = 1
                var:zg361_ch_portfolio_owner = root
                var:zg361_ch_portfolio_subject = this
                var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_01_status }
    }
    else_if = {
        limit = {
            has_variable = zg361_ch_manager_portfolio_active
            var:zg361_ch_manager_portfolio_active = 1
            var:zg361_p2c_subject = {
                var:zg361_ch_portfolio_owner = root
                var:zg361_ch_portfolio_subject = this
                var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        zg361_p2c_call_career_hc_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                var:zg361_ch_portfolio_applied = 1
                var:zg361_ch_manager_portfolio_active = 1
                var:zg361_p2c_subject = {
                    var:zg361_ch_portfolio_owner = root
                    var:zg361_ch_portfolio_subject = this
                    var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 101 STAGE_VAR = zg361_p2c_stage_01_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 151 STAGE_VAR = zg361_p2c_stage_01_status } }
}

# Stage 2: compensation consumes the exact delivered result.  Its public
# open-next adapter is intentionally called again after each domain ACK.
zg361_p2c_stage_02_compensation_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                OR = { var:zg361_result_case_state = 1 var:zg361_result_case_state = 2 }
            }
        }
        zg361_p2c_mark_external_wait_effect = { REASON = 325 STAGE_VAR = zg361_p2c_stage_02_status }
    }
    else_if = {
        limit = {
            var:zg361_comp_portfolio_completed_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
            var:zg361_comp_portfolio_result_state >= 3
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_02_status }
    }
    else_if = {
        limit = {
            has_character_flag = zg361_comp_portfolio_active
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                var:zg361_result_case_state >= 3
            }
        }
        zg361_p2c_call_compensation_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                OR = {
                    has_character_flag = zg361_comp_portfolio_active
                    AND = { has_variable = zg361_comp_portfolio_completed_cycle var:zg361_comp_portfolio_completed_cycle = var:zg361_p2c_cycle }
                }
                var:zg361_comp_portfolio_result_owner = root
                var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
                var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
                var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 202 STAGE_VAR = zg361_p2c_stage_02_status } }
    }
    else = { zg361_p2c_abort_stale_effect = { CODE = 252 } }
}

# Stage 3: T -> U -> V -> W -> complete.  Each central pump can call the
# public adapter only once, and it waits while the package owns its queue lock.
zg361_p2c_stage_03_feedback_promotion_pip_effect = {
    if = {
        limit = {
            var:zg361_pp_portfolio_complete_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_subject = {
                var:zg361_pp_t_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_u_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_v_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_w_portfolio_done_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_03_status }
    }
    else_if = {
        limit = { has_variable = zg361_pp_portfolio_queue_active var:zg361_pp_portfolio_queue_active = 1 }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else = {
        zg361_p2c_call_pp_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                OR = {
                    AND = { has_variable = zg361_pp_portfolio_complete_cycle var:zg361_pp_portfolio_complete_cycle = var:zg361_p2c_cycle }
                    AND = { has_variable = zg361_pp_portfolio_queue_active var:zg361_pp_portfolio_queue_active = 1 }
                }
                var:zg361_p2c_subject = {
                    OR = {
                        AND = { has_variable = zg361_pp_t_portfolio_done_cycle var:zg361_pp_t_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_t_active var:zg361_case_t_active = 1 var:zg361_case_t_owner = root var:zg361_case_t_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_u_portfolio_done_cycle var:zg361_pp_u_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_u_active var:zg361_case_u_active = 1 var:zg361_case_u_owner = root var:zg361_case_u_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_v_portfolio_done_cycle var:zg361_pp_v_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_v_active var:zg361_case_v_active = 1 var:zg361_case_v_owner = root var:zg361_case_v_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_w_portfolio_done_cycle var:zg361_pp_w_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_w_active var:zg361_case_w_active = 1 var:zg361_case_w_owner = root var:zg361_case_w_cycle_serial = root.var:zg361_p2c_cycle }
                    }
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 303 STAGE_VAR = zg361_p2c_stage_03_status } }
    }
}
''' + incidents + r'''
# Stage 7: P3 is gated by the same exact delivered result as compensation.
zg361_p2c_stage_07_metrics_delivery_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                OR = { var:zg361_result_case_state = 1 var:zg361_result_case_state = 2 }
            }
        }
        zg361_p2c_mark_external_wait_effect = { REASON = 325 STAGE_VAR = zg361_p2c_stage_07_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_closed = 1
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_owner = root
                var:zg361_p3_portfolio_result_subject = this
                var:zg361_p3_portfolio_result_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
                var:zg361_p3_final_owner = root
                var:zg361_p3_final_subject = this
                var:zg361_p3_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_final_conservation_ok = 1
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_07_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_aa_active = 1 var:zg361_case_ag_active = 1 var:zg361_case_aj_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # AA -> AG -> AJ use D+1 edges.  During the bounded edge gap no case is
        # active, but the frozen portfolio tuple is still authoritative.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_closed = 0
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_owner = root
                var:zg361_p3_portfolio_result_subject = this
                var:zg361_p3_portfolio_result_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status != 1
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                var:zg361_result_case_state >= 3
            }
        }
        zg361_p3_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_p3_portfolio_owner = root
                    var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
                    var:zg361_case_aa_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 707 STAGE_VAR = zg361_p2c_stage_07_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 757 STAGE_VAR = zg361_p2c_stage_07_status } }
}

# Stage 8: a distinct cross reviewer is mandatory.  A one-subject realm whose
# manager has no eligible celestial superior is honestly N/A, never bypassed.
zg361_p2c_stage_08_credit_project_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_closed = 1
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_cp_final_owner = root
                var:zg361_cp_final_subject = this
                var:zg361_cp_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_cp_final_conservation_ok = 1
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_08_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status = 0
            NOR = {
                any_vassal = { zg361_is_reviewable_vassal_trigger = yes NOT = { this = root.var:zg361_p2c_subject } }
                liege = { zg361_is_celestial_liege_trigger = yes }
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_08_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_e_active = 1 var:zg361_case_i_active = 1 var:zg361_case_j_active = 1 var:zg361_case_r_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # E -> I -> J -> R also crosses D+1 edges.  Keep polling the exact
        # frozen subject portfolio instead of converting a healthy gap to RED.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_closed = 0
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        zg361_cp_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_case_e_owner = root
                    var:zg361_case_e_subject = this
                    var:zg361_case_e_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_e_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 808 STAGE_VAR = zg361_p2c_stage_08_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 858 STAGE_VAR = zg361_p2c_stage_08_status } }
}

# Stage 9: dispatches all current direct reports once, then waits for exact
# expected/completed counters.  A player digest must be ACKed before advancing.
zg361_p2c_stage_09_career_learning_effect = {
    if = {
        limit = {
            has_variable = zg361_p2c_cl_partial_open
            var:zg361_p2c_cl_partial_open = 1
            var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
            var:zg361_cl_portfolio_ah_completed >= var:zg361_cl_portfolio_ah_expected
            var:zg361_cl_portfolio_ai_completed >= var:zg361_cl_portfolio_ai_expected
            trigger_if = { limit = { is_ai = no } NOT = { has_variable = zg361_cl_digest_pending } }
            trigger_else = { always = yes }
        }
        zg361_p2c_record_red_effect = { CODE = 910 STAGE_VAR = zg361_p2c_stage_09_status }
    }
    else_if = {
        limit = {
            var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_cl_frozen_count > 0
            var:zg361_cl_portfolio_ah_expected = var:zg361_p2c_cl_frozen_count
            var:zg361_cl_portfolio_ai_expected = var:zg361_p2c_cl_frozen_count
            var:zg361_cl_portfolio_ah_completed >= var:zg361_cl_portfolio_ah_expected
            var:zg361_cl_portfolio_ai_completed >= var:zg361_cl_portfolio_ai_expected
            trigger_if = { limit = { is_ai = no } NOT = { has_variable = zg361_cl_digest_pending } }
            trigger_else = { always = yes }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_09_status }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        if = { limit = { has_variable_list = zg361_p2c_cl_subjects } clear_variable_list = zg361_p2c_cl_subjects }
        set_variable = { name = zg361_p2c_cl_frozen_count value = 0 }
        remove_variable = zg361_p2c_cl_partial_open
        every_vassal = {
            limit = { zg361_is_reviewable_vassal_trigger = yes liege = root }
            save_temporary_scope_as = zg361_p2c_cl_subject_to_store
            root = {
                add_to_variable_list = { name = zg361_p2c_cl_subjects target = scope:zg361_p2c_cl_subject_to_store }
                change_variable = { name = zg361_p2c_cl_frozen_count add = 1 }
            }
        }
        zg361_cl_dispatch_direct_reports_effect = yes
        if = {
            limit = {
                var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
                var:zg361_p2c_cl_frozen_count > 0
                var:zg361_cl_portfolio_ah_expected = var:zg361_p2c_cl_frozen_count
                var:zg361_cl_portfolio_ai_expected = var:zg361_p2c_cl_frozen_count
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = {
            # Some reports may already own live AH/AI cases.  Let those exact
            # cases close before recording the partial-open RED, so no player
            # window or delayed ticket is orphaned by the central layer.
            set_variable = { name = zg361_p2c_cl_partial_open value = 1 }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
    else = {
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
}

# Stage 10 freezes only subordinate celestial managers whose own review serial
# strictly lags the owner.  Counts/barons never enter this manager cohort.
zg361_p2c_stage_10_manager_governance_effect = {
    if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        if = { limit = { has_variable_list = zg361_p2c_mg_subjects } clear_variable_list = zg361_p2c_mg_subjects }
        set_variable = { name = zg361_p2c_mg_expected value = 0 }
        every_vassal = {
            limit = {
                zg361_is_celestial_liege_trigger = yes
                liege = root
                has_variable = zg361_review_serial
                var:zg361_review_serial < root.var:zg361_p2c_cycle
            }
            save_temporary_scope_as = zg361_p2c_mg_subject_to_store
            root = {
                add_to_variable_list = { name = zg361_p2c_mg_subjects target = scope:zg361_p2c_mg_subject_to_store }
                change_variable = { name = zg361_p2c_mg_expected add = 1 }
            }
        }
        if = {
            limit = { var:zg361_p2c_mg_expected = 0 }
            zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else = {
            zg361_mg_dispatch_subordinate_managers_effect = yes
            set_variable = { name = zg361_p2c_mg_started value = 0 }
            set_variable = { name = zg361_p2c_mg_active value = 0 }
            every_in_list = {
                variable = zg361_p2c_mg_subjects
                if = {
                    limit = {
                        has_variable = zg361_case_f_owner
                        has_variable = zg361_case_f_subject
                        has_variable = zg361_case_f_cycle_serial
                        has_variable = zg361_case_f_active
                        has_variable = zg361_case_ak_owner
                        has_variable = zg361_case_ak_subject
                        has_variable = zg361_case_ak_cycle_serial
                        has_variable = zg361_case_ak_active
                        var:zg361_case_f_owner = root
                        var:zg361_case_f_subject = this
                        var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                        var:zg361_case_ak_owner = root
                        var:zg361_case_ak_subject = this
                        var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    }
                    root = { change_variable = { name = zg361_p2c_mg_started add = 1 } }
                }
                if = {
                    limit = {
                        OR = {
                            AND = { has_variable = zg361_case_f_owner var:zg361_case_f_owner = root has_variable = zg361_case_f_cycle_serial var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_f_active var:zg361_case_f_active = 1 }
                            AND = { has_variable = zg361_case_ak_owner var:zg361_case_ak_owner = root has_variable = zg361_case_ak_cycle_serial var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_ak_active var:zg361_case_ak_active = 1 }
                        }
                    }
                    root = { change_variable = { name = zg361_p2c_mg_active add = 1 } }
                }
            }
            set_variable = { name = zg361_p2c_mg_open_failed value = 0 }
            if = {
                limit = { var:zg361_p2c_mg_started < var:zg361_p2c_mg_expected }
                set_variable = { name = zg361_p2c_mg_open_failed value = 1 }
            }
            set_variable = { name = zg361_p2c_stage_status value = 1 }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
    else = {
        set_variable = { name = zg361_p2c_mg_completed value = 0 }
        set_variable = { name = zg361_p2c_mg_invalid value = 0 }
        set_variable = { name = zg361_p2c_mg_started value = 0 }
        set_variable = { name = zg361_p2c_mg_active value = 0 }
        every_in_list = {
            variable = zg361_p2c_mg_subjects
            if = {
                limit = {
                    has_variable = zg361_case_f_owner
                    has_variable = zg361_case_f_subject
                    has_variable = zg361_case_f_cycle_serial
                    has_variable = zg361_case_f_active
                    has_variable = zg361_case_ak_owner
                    has_variable = zg361_case_ak_subject
                    has_variable = zg361_case_ak_cycle_serial
                    has_variable = zg361_case_ak_active
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_subject = this
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_subject = this
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                }
                root = { change_variable = { name = zg361_p2c_mg_started add = 1 } }
            }
            if = {
                limit = {
                    OR = {
                        AND = { has_variable = zg361_case_f_owner var:zg361_case_f_owner = root has_variable = zg361_case_f_cycle_serial var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_f_active var:zg361_case_f_active = 1 }
                        AND = { has_variable = zg361_case_ak_owner var:zg361_case_ak_owner = root has_variable = zg361_case_ak_cycle_serial var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_ak_active var:zg361_case_ak_active = 1 }
                    }
                }
                root = { change_variable = { name = zg361_p2c_mg_active add = 1 } }
            }
            if = {
                limit = {
                    is_alive = yes
                    liege = root
                    zg361_is_celestial_liege_trigger = yes
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_subject = this
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_f_state = 5
                    var:zg361_case_f_active = 0
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_subject = this
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_state = 6
                    var:zg361_case_ak_active = 0
                }
                root = { change_variable = { name = zg361_p2c_mg_completed add = 1 } }
            }
            else_if = {
                limit = { OR = { is_alive = no NOT = { liege = root } NOT = { zg361_is_celestial_liege_trigger = yes } } }
                root = { change_variable = { name = zg361_p2c_mg_invalid add = 1 } }
            }
            else_if = {
                limit = {
                    has_variable = zg361_case_f_owner
                    has_variable = zg361_case_f_cycle_serial
                    has_variable = zg361_case_f_state
                    has_variable = zg361_case_f_active
                    has_variable = zg361_case_ak_owner
                    has_variable = zg361_case_ak_cycle_serial
                    has_variable = zg361_case_ak_state
                    has_variable = zg361_case_ak_active
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_f_active = 0
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_active = 0
                    OR = { var:zg361_case_f_state != 5 var:zg361_case_ak_state != 6 }
                }
                root = { change_variable = { name = zg361_p2c_mg_invalid add = 1 } }
            }
        }
        if = {
            limit = { var:zg361_p2c_mg_invalid > 0 }
            zg361_p2c_record_red_effect = { CODE = 1010 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else_if = {
            limit = {
                var:zg361_p2c_mg_open_failed = 1
                var:zg361_p2c_mg_active = 0
            }
            zg361_p2c_record_red_effect = { CODE = 1011 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else_if = {
            limit = {
                var:zg361_p2c_mg_open_failed = 0
                var:zg361_p2c_mg_started >= var:zg361_p2c_mg_expected
                var:zg361_p2c_mg_completed >= var:zg361_p2c_mg_expected
            }
            zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else = {
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
}

# The Workforce seam is written once here; mutually exclusive start/resume
# branches below call this wrapper, preserving one public opener per pump.
zg361_p2c_call_workforce_adapter_effect = {
    zg361_we_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
}

# Stage 11: ordinary assessed counts/barons are valid initial Workforce
# subjects.  Only the domain's later #360/#361 resume guard may require a
# manager subject.  status 5 is a real external wait, never completion.
zg361_p2c_stage_11_workforce_endgame_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 1
                var:zg361_we_portfolio_status = 6
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_final_conservation_ok = 1
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_11_status }
    }
    else_if = {
        # Workforce owns the non-manager close: 38 ordinary operations settle,
        # manager-only #360/#361 write no receipt, AL is closed, and status 7 is
        # N/A rather than business success.
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 1
                var:zg361_we_portfolio_status = 7
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_portfolio_terminal_na = 1
                var:zg361_we_portfolio_terminal_reason = 360361
                var:zg361_we_portfolio_terminal_owned_operations = 38
                var:zg361_we_portfolio_terminal_skipped_manager_only = 2
                var:zg361_we_portfolio_terminal_success = 0
                var:zg361_we_final_conservation_ok = 1
                var:zg361_case_al_active = 0
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_11_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_status = 5
                var:zg361_we_awaiting_al_357_359 = 1
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        # The only automatic resume attempt consumes source receipts minted by
        # the real B1 facts/quota close and B2 appeal/quota-return consumers.
        # It cannot manufacture ids/hashes and route-C debts remain waiting.
        if = {
            limit = {
                var:zg361_p2c_subject = { zg361_is_celestial_liege_trigger = yes }
            }
            var:zg361_p2c_subject = {
                zg361_b2_submit_completed_al_receipts_effect = {
                    TICKET_OWNER = root TICKET_SUBJECT = this
                    TICKET_CYCLE = root.var:zg361_p2c_cycle
                    TICKET_CASE = var:zg361_case_al_case_serial
                }
            }
        }
        # If exact external receipts already advanced AL to 4/5, call the public
        # resume seam once.  Otherwise remain external and keep the UI lane free.
        if = {
            limit = {
                var:zg361_p2c_subject = { zg361_is_celestial_liege_trigger = yes }
                var:zg361_p2c_subject = {
                    var:zg361_we_al_external_stage_receipts_verified = 1
                    var:zg361_we_al_external_receipt_owner = root
                    var:zg361_we_al_external_receipt_subject = this
                    var:zg361_we_al_external_receipt_cycle = root.var:zg361_p2c_cycle
                    var:zg361_we_al_external_receipt_case = var:zg361_case_al_case_serial
                    var:zg361_we_al_external_receipt_count = 3
                    var:zg361_we_al_external_last_operation = 359
                    OR = { var:zg361_case_al_state = 4 var:zg361_case_al_state = 5 }
                }
            }
            zg361_p2c_call_workforce_adapter_effect = yes
            set_variable = { name = zg361_p2c_stage_status value = 1 }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else_if = {
            # #360/#361 are manager-only by contract.  Without a Workforce
            # public N/A-close seam, a count/baron cannot legally close AL.
            # Suspend the central case as an external blocker: no success,
            # no completed-cycle marker, and no permanent D+2 retry loop.
            limit = {
                var:zg361_p2c_subject = { NOT = { zg361_is_celestial_liege_trigger = yes } }
            }
            zg361_p2c_suspend_external_effect = { REASON = 360361 STAGE_VAR = zg361_p2c_stage_11_status }
        }
        else = { zg361_p2c_mark_external_wait_effect = { REASON = 357359 STAGE_VAR = zg361_p2c_stage_11_status } }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_ab_active = 1 var:zg361_case_ac_active = 1 var:zg361_case_ad_active = 1 var:zg361_case_al_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # AB -> AC -> AD -> AL has the same D+1 transition gap semantics.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 0
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                NOT = { var:zg361_we_portfolio_status = 5 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status = 0
            var:zg361_p2c_subject = {
                has_variable = zg361_ch_hc_authorized
                has_variable = zg361_ch_hc_available
                has_variable = zg361_ch_hc_reserved
                has_variable = zg361_ch_hc_occupied
                has_variable = zg361_ch_hc_frozen
                has_variable = zg361_ch_hc_reclaimed
            }
        }
        zg361_p2c_call_workforce_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_case_ab_owner = root
                    var:zg361_case_ab_subject = this
                    var:zg361_case_ab_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ab_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 1111 STAGE_VAR = zg361_p2c_stage_11_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 1161 STAGE_VAR = zg361_p2c_stage_11_status } }
}

# One entry point and one else-if chain: a single pump can dispatch at most one
# stage, and each stage body calls at most one public adapter/domain opener.
zg361_p2c_pump_effect = {
    if = {
        limit = {
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_p2c_active
            var:zg361_p2c_active = 1
            has_variable = zg361_p2c_case_serial
            has_variable = zg361_p2c_b1_cycle
            has_variable = zg361_p2c_b1_case
            has_variable = zg361_p2c_cycle
            has_variable = zg361_p2c_subject
            has_variable = zg361_p2c_result_case
            has_variable = zg361_review_serial
            has_variable = zg361_b1_cycle_serial
            has_variable = zg361_b1_case_serial
            has_variable = zg361_b1_closure_state
            var:zg361_review_serial = var:zg361_p2c_cycle
            var:zg361_b1_cycle_serial = var:zg361_p2c_b1_cycle
            var:zg361_b1_case_serial = var:zg361_p2c_b1_case
            var:zg361_b1_closure_state = 4
            var:zg361_p2c_subject = {
                is_alive = yes
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_p2c_b1_cycle
                var:zg361_b1_case_serial = root.var:zg361_p2c_b1_case
                var:zg361_b1_case_state = 8
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
            }
        }
        if = { limit = { var:zg361_p2c_stage = 1 } zg361_p2c_stage_01_career_hc_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 2 } zg361_p2c_stage_02_compensation_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 3 } zg361_p2c_stage_03_feedback_promotion_pip_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 4 } zg361_p2c_stage_04_x_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 5 } zg361_p2c_stage_05_y_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 6 } zg361_p2c_stage_06_z_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 7 } zg361_p2c_stage_07_metrics_delivery_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 8 } zg361_p2c_stage_08_credit_project_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 9 } zg361_p2c_stage_09_career_learning_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 10 } zg361_p2c_stage_10_manager_governance_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 11 } zg361_p2c_stage_11_workforce_endgame_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage >= 12 } zg361_p2c_finish_effect = yes }
        else = { zg361_p2c_abort_stale_effect = { CODE = 9002 } }
    }
    else_if = {
        limit = { has_variable = zg361_p2c_active var:zg361_p2c_active = 1 }
        zg361_p2c_abort_stale_effect = { CODE = 9001 }
    }
    else = { debug_log = "ZG361P2C: inactive central pump ignored" }
}
'''


def render_events() -> str:
    return HEADER + r'''namespace = zg361p2c

# Exact delayed poll.  Old tickets never mutate a newer central case.
zg361p2c.1 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                exists = scope:zg361_p2c_ticket_manager
                this = scope:zg361_p2c_ticket_manager
                has_variable = zg361_p2c_active
                var:zg361_p2c_active = 1
                var:zg361_p2c_cycle = scope:zg361_p2c_ticket_cycle
                var:zg361_p2c_case_serial = scope:zg361_p2c_ticket_case
                var:zg361_p2c_stage = scope:zg361_p2c_ticket_stage
                var:zg361_p2c_ticket_serial = scope:zg361_p2c_ticket_identity
            }
            zg361_p2c_pump_effect = yes
        }
        else = { debug_log = "ZG361P2C: stale or replayed central poll ignored" }
    }
}

# The only central visible event.  Domain packages retain their own bounded
# cards; the central layer emits one terminal aggregate and nothing per stage.
zg361p2c.2 = {
    type = character_event
    title = zg361_p2c_summary_title
    desc = zg361_p2c_summary_desc
    theme = stewardship
    trigger = {
        is_ai = no
        has_variable = zg361_p2c_summary_pending
        var:zg361_p2c_cycle = scope:zg361_p2c_summary_cycle
        var:zg361_p2c_case_serial = scope:zg361_p2c_summary_case
    }
    option = {
        name = zg361_p2c_summary_ack
        remove_variable = zg361_p2c_summary_pending
    }
}

# A new B1 season that collides with an old active central case is initialized
# only after the old typed-RED summary had one full day to be acknowledged.
zg361p2c.3 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                has_variable = zg361_p2c_deferred_reinit
                var:zg361_p2c_deferred_reinit = 1
                has_variable = zg361_review_serial
                has_variable = zg361_b1_case_serial
                var:zg361_review_serial = var:zg361_p2c_deferred_reinit_cycle
                var:zg361_b1_case_serial = var:zg361_p2c_deferred_reinit_b1_case
            }
            remove_variable = zg361_p2c_deferred_reinit
            zg361_p2c_on_review_published_effect = yes
        }
        else = { debug_log = "ZG361P2C: stale deferred central reinitialization ignored" }
    }
}
'''


def render_localization(language: str, header: str) -> str:
    chinese = language == "simp_chinese"
    if chinese:
        title = "二期绩效流水线：终于跑完了"
        desc = (
            "公示后的二期案卷已经串行收口。成功域：#high "
            "[ROOT.MakeScope.Var('zg361_p2c_success_n').GetValue|0]#!；不适用："
            "[ROOT.MakeScope.Var('zg361_p2c_na_n').GetValue|0]；RED："
            "[ROOT.MakeScope.Var('zg361_p2c_red_n').GetValue|0]；曾等待外部依赖："
            "[ROOT.MakeScope.Var('zg361_p2c_external_n').GetValue|0]。好消息是没有九个部门同时弹窗，"
            "坏消息是它们确实都留下了表格。"
        )
        ack = "很好，把这摞表从我桌上拿走。"
    else:
        title = "Phase-Two Performance Pipeline: Finally Closed"
        desc = (
            "The post-publication phase-two portfolio has closed serially. Successful domains: #high "
            "[ROOT.MakeScope.Var('zg361_p2c_success_n').GetValue|0]#!; not applicable: "
            "[ROOT.MakeScope.Var('zg361_p2c_na_n').GetValue|0]; RED: "
            "[ROOT.MakeScope.Var('zg361_p2c_red_n').GetValue|0]; external waits encountered: "
            "[ROOT.MakeScope.Var('zg361_p2c_external_n').GetValue|0]. The good news is that nine teams did not "
            "open nine windows at once. The bad news is that every team still produced a spreadsheet."
        )
        ack = "Excellent. Remove this stack from my desk."
    return f'{header}:\n # GENERATED FILE — edit tools/gen_361_phase2_central_runtime.py\n zg361_p2c_summary_title:0 "{title}"\n zg361_p2c_summary_desc:0 "{desc}"\n zg361_p2c_summary_ack:0 "{ack}"\n'


def render_spec() -> str:
    return """# 361 二期中央串行调度层：CK3 runtime 合同

Readiness: `static-ready`

MCP evidence: `none`

CK3 live evidence: `none`

## 1. 权限和冻结身份

- 中央 ROOT 必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在世、有地、公爵及以上。
- 伯爵和男爵可以作为直属受评 subject，但永远不能成为中央 manager。
- B1 公示后，从本轮已冻结结果 cohort 里按 `stewardship / position = 0` 冻结一个 primary subject。
- 中央案固定 `manager + B1 cycle/case + review cycle + subject + result case`；死亡、调任、换 owner/cycle/case 都 typed RED，绝不换人续跑。

## 2. 两阶段 hook

1. `zg361_apply_pending_grades_effect` 先完成榜单、`zg361_b1_mark_published_effect`、清除 `zg361_review_in_progress`，随后只调用 `zg361_p2c_on_review_published_effect`。它只初始化并排 D+2 pump，不开领域。
2. `zg361_settle_delivered_325_effect` 先写 state 3、settlement receipt，并调用 `zg361_b2_on_notice_delivered_effect`，随后调用 `zg361_p2c_on_result_delivered_effect`。它仅用 exact owner/subject/cycle/result-case 唤醒正在等待的 Compensation/P3。

B1 open、D+180、事实冻结以及未送达的 3.25 都不是二期入口。
M013 公示闭合证明按显式 mode 严格互斥：route A/B 必须同时满足 `m013_mode` 存在且 `mode!=3`、`receipt_serial=current case`；合法 route C 必须同时满足 `mode=3`、`policy_debt_serial=current case`。`mode=3` 即使遗留或伪造了本轮 receipt 也不能走 A/B，`mode!=3` 即使存在本轮 policy debt 也不能走 C；缺失 mode 同样不能初始化中央案。延期披露不会丢掉合法 route C 的二期链。

## 3. 串行顺序

| Stage | 领域 | Public ABI | 中央终态 |
|---:|---|---|---|
| 1 | Career/HC | `zg361_career_hc_open_portfolio_effect` | manager completed cycle + 同一 subject closed |
| 2 | Compensation/LTI | `zg361_comp_portfolio_open_next_effect` | exact result snapshot + completed cycle；每域 ACK 后重复 pump |
| 3 | Feedback/Promotion/PIP | `zg361_pp_manager_portfolio_adapter_effect` | T→U→V→W→complete，五次单 adapter pump |
| 4–6 | Incident X/Y/Z | 三个 public domain opener | 严格 X→Y→Z；禁止 all-domain opener |
| 7 | Metrics/Delivery | `zg361_p3_open_portfolio_effect` | 同 result case、closed、conservation OK |
| 8 | Credit/Project | `zg361_cp_open_portfolio_effect` | closed + conservation OK；无 distinct reviewer 为 N/A |
| 9 | Career/Learning | `zg361_cl_dispatch_direct_reports_effect` | expected/completed 全齐；玩家 digest 已 ACK |
| 10 | Manager/Governance | `zg361_mg_dispatch_subordinate_managers_effect` | 冻结 strict-lag manager cohort 全部 F/AK terminal；空集 N/A |
| 11 | Workforce/Endgame | `zg361_we_open_portfolio_effect` | success 只认 closed=1/status=6；非 manager 的 closed=1/status=7 为 N/A；status=5 是 357–359 外部等待 |

每次中央 pump 的 `if/else_if` 只进入一个 stage；每个 stage 每次最多调用一个 public adapter/domain opener。玩家与 AI 走同一业务 ABI 和同一顺序，差异仅是玩家 UI lane 与最终摘要；AI 后台静默。

## 4. UI、等待与 replay

- 公示后 D+2 才开首域；领域 terminal 后再 D+2 才进下一域，给 D+1 完成卡留出 ACK 时间。
- PP 的 queue lock、Compensation 的 active flag、Career/Learning 的 digest pending 都是中央真实等待条件。
- Career/HC、Compensation、PP 的 manager-only ABI 会先按各自同一筛选器预选；只有候选仍等于 frozen primary 才调用，防止资格漂移在别人身上留下 active orphan。
- Career/Learning 冻结直属 cohort/count，AH/AI expected 必须各自等于该 count；partial open 等已开案终态后记 RED。Manager/Governance 同样核对 frozen cohort 的 exact F/AK started/active/terminal，failed open 不会无限轮询。
- delayed poll 带 `manager + cycle + central case + stage + ticket serial`；新 ticket 使旧事件 strict no-op。
- 新一轮 B1 公示若撞上旧中央案，会先把旧 immutable tuple 记为 typed RED，给旧摘要 D+1 ACK 窗口，再在 D+2 精确初始化新案；禁止原地覆盖或清掉旧摘要。
- P3、Credit/Project 与 Workforce 的 D+1 域切换空档只轮询同一 portfolio tuple，不会误判 RED。
- 3.25 state 1/2 以及 Workforce status 5 都记录 external wait，绝不伪装 success。manager 的 status 5 会先调用
  `zg361_b2_submit_completed_al_receipts_effect`：它只读取 B1 #357 与 B2 #358/#359 已由真实 consumer 发布的来源票据，中央不能
  传入 receipt ID/hash；strict bridge 验证成功后才调用既有 resume seam。
- 最终每名玩家 manager 只收到一张中央聚合摘要；AI 不收到中央可见事件。

## 5. 已知外部依赖

- Workforce 357–359 的 B1/B2 真实来源、产品 adapter 与中央调用已经接线；但同案 receipt 尚未到达（例如没有已裁决申诉、
  翻案后尚未完成配额回流，或走 policy route C）时，本中央案仍会诚实停在 stage 11/status 5，不会生成完成标记。
- Workforce runtime 的初始 AB/AC/AD 必须允许普通 assessed count/baron；只有 #360/#361 resume 才可追加 manager 条件。中央层已经按此权限合同调用 public seam，但不修改该并发领域文件。
- 普通 count/baron 的 N/A-close seam 必须冻结 `terminal_na=1/reason=360361/owned_operations=38/skipped_manager_only=2/success=0`、`final_conservation_ok=1`、清 AL active 并写 closed=1/status=7；中央据此把 stage 11 记为 N/A。旧 runtime 若没有该 seam，中央仍以 `terminal_state=5` 外部阻点暂停：不调用无权限 ABI、不写 completed-cycle、不伪造 Workforce success，也不每两日永久重试。
- 所有结论目前只是生成可复现、静态语法/结构测试证据；尚未经过 MCP-first CK3 paused snapshot、存读档或多轮实机验收。

## 6. 测试口径

`tools/test_zg361_phase2_central_runtime.py` 静态证明：两处 hook 顺序、M013 两套公示证明的 mode 互斥与混用反例、D+2 初始化、exact 3.25 wake、单 opener、PP/Incident 顺序、权限边界、stale ticket、CP N/A、CL digest、MG strict lag、Workforce 来源 adapter→verified→resume 顺序与 status 5 等待、AI/玩家共同业务路径、BOM 与生成可复现。它不构成 fixture-live 或 production-live 证据。
"""


def outputs() -> dict[Path, str]:
    rendered = {
        MOD_ROOT / "common/scripted_effects/zg361_phase2_central_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events/zg361_phase2_central_runtime_events.txt": render_events(),
        MOD_ROOT / "docs/361-phase2-central-runtime-spec.md": render_spec(),
    }
    for language, header in LANGUAGES:
        rendered[MOD_ROOT / f"localization/{language}/zg361_phase2_central_l_{language}.yml"] = render_localization(language, header)
    return rendered


def write_or_check(check: bool) -> int:
    stale: list[str] = []
    for path, content in outputs().items():
        payload = BOM + content.replace("\r\n", "\n").encode("utf-8")
        if check:
            if not path.exists() or path.read_bytes() != payload:
                stale.append(path.relative_to(MOD_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    if stale:
        print("stale generated phase-two central files:")
        for item in stale:
            print(f"  {item}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_or_check(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
