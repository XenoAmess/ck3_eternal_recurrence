#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the F032-036 and AK345-354 manager/governance CK3 runtime.

This generator intentionally owns an isolated callable adapter.  It does not
edit the B1/B2 products, the scoreboard, the shared case kernel, or any central
effect/event/interaction file.  Runtime claims therefore stop at static-ready
until the adapter is wired and exercised through the MCP-first CK3 fixture.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_manager_governance_runtime.py\n"
READINESS = "static-ready"


@dataclass(frozen=True)
class MechanismBinding:
    mechanism_id: int
    domain: str
    operation: str
    effect: str
    case_state: int
    consumer: str


BINDINGS: tuple[MechanismBinding, ...] = (
    MechanismBinding(32, "F", "manager.score_frozen_team", "zg361_mg_m032_score_manager_effect", 1, "zg361_mg_manager_score"),
    MechanismBinding(33, "F", "manager.explain_profile_decision", "zg361_mg_m033_reason_code_effect", 2, "zg361_mg_reason_total"),
    MechanismBinding(34, "F", "manager.freeze_nine_box", "zg361_mg_m034_freeze_nine_box_effect", 3, "zg361_mg_nine_box_code"),
    MechanismBinding(35, "F", "manager.freeze_distribution_mode", "zg361_mg_m035_freeze_distribution_effect", 1, "zg361_mg_distribution_conserved"),
    MechanismBinding(36, "F", "manager.compile_decade_report", "zg361_mg_m036_append_decade_log_effect", 4, "zg361_mg_previous_manager_score"),
    MechanismBinding(345, "AK", "policy.freeze_next_cycle_calendar", "zg361_mg_m345_freeze_calendar_effect", 1, "zg361_mg_calendar_effective_cycle"),
    MechanismBinding(346, "AK", "policy.consume_material_offcycle_signal", "zg361_mg_m346_consume_offcycle_signal_effect", 1, "zg361_mg_offcycle_consumed"),
    MechanismBinding(347, "AK", "policy.consume_override_point", "zg361_mg_m347_consume_override_effect", 2, "zg361_mg_override_quota_neutral"),
    MechanismBinding(348, "AK", "policy.expire_or_renew_exception", "zg361_mg_m348_bind_exception_effect", 2, "zg361_mg_exception_state"),
    MechanismBinding(349, "AK", "policy.run_reproducible_audit", "zg361_mg_m349_run_audit_effect", 3, "zg361_mg_audit_settled"),
    MechanismBinding(350, "AK", "policy.version_benchmark", "zg361_mg_m350_version_benchmark_effect", 3, "zg361_mg_benchmark_new_version"),
    MechanismBinding(351, "AK", "policy.measure_regional_pilot", "zg361_mg_m351_measure_pilot_effect", 4, "zg361_mg_pilot_result_ready"),
    MechanismBinding(352, "AK", "policy.map_immutable_history", "zg361_mg_m352_map_history_effect", 4, "zg361_mg_history_mapping_version"),
    MechanismBinding(353, "AK", "policy.charge_admin_capacity", "zg361_mg_m353_charge_admin_capacity_effect", 5, "zg361_mg_manager_score_delta"),
    MechanismBinding(354, "AK", "policy.recompute_fairness_metrics", "zg361_mg_m354_audit_fairness_effect", 5, "zg361_mg_fairness_gaming"),
)
TARGET_IDS = tuple(row.mechanism_id for row in BINDINGS)


def validate_bindings() -> None:
    expected = (*range(32, 37), *range(345, 355))
    if TARGET_IDS != expected:
        raise ValueError(f"manager/governance coverage drift: {TARGET_IDS!r}")
    if len({row.operation for row in BINDINGS}) != len(BINDINGS):
        raise ValueError("operation keys must be unique")
    if {row.domain for row in BINDINGS} != {"F", "AK"}:
        raise ValueError("only F and AK are owned")
    if READINESS != "static-ready":
        raise ValueError("this generator must not claim live readiness")


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def receipt_call(domain: str, mechanism_id: int, state: int) -> str:
    prefix = domain.lower()
    return f"""zg361_case_kernel_record_operation_effect = {{
			OWNER_VAR = zg361_case_{prefix}_owner
			SUBJECT_VAR = zg361_case_{prefix}_subject
			CYCLE_VAR = zg361_case_{prefix}_cycle_serial
			CASE_VAR = zg361_case_{prefix}_case_serial
			STATE_VAR = zg361_case_{prefix}_state
			REVISION_VAR = zg361_case_{prefix}_revision
			ACTIVE_VAR = zg361_case_{prefix}_active
			TIMELINE_VAR = zg361_case_{prefix}_timeline_serial
			FEEDBACK_VAR = zg361_case_{prefix}_feedback_revision
			LAST_OPERATION_VAR = zg361_case_{prefix}_last_operation
			LAST_CHOICE_VAR = zg361_case_{prefix}_last_choice
			RECEIPT_OWNER_VAR = zg361_mg_m{mechanism_id:03d}_receipt_owner
			RECEIPT_SUBJECT_VAR = zg361_mg_m{mechanism_id:03d}_receipt_subject
			RECEIPT_CYCLE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_cycle
			RECEIPT_CASE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_case
			RECEIPT_STATE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_state
			RECEIPT_CHOICE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_choice
			TICKET_OWNER = var:zg361_case_{prefix}_owner
			TICKET_SUBJECT = this
			TICKET_CYCLE = var:zg361_case_{prefix}_cycle_serial
			TICKET_CASE = var:zg361_case_{prefix}_case_serial
			TICKET_STATE = {state}
			CHOICE = 1
			OPERATION_ID = {mechanism_id}
		}}"""


def transition_call(domain: str, stage: int) -> str:
    prefix = domain.lower()
    return f"""zg361_case_{prefix}_advance_{stage:02d}_effect = {{
			TICKET_OWNER = var:zg361_case_{prefix}_owner
			TICKET_SUBJECT = this
			TICKET_CYCLE = var:zg361_case_{prefix}_cycle_serial
			TICKET_CASE = var:zg361_case_{prefix}_case_serial
		}}"""


def receipt_current(domain: str, mechanism_id: int, state: int) -> str:
    prefix = domain.lower()
    return f"""zg361_case_kernel_receipt_is_current_trigger = {{
			RECEIPT_OWNER_VAR = zg361_mg_m{mechanism_id:03d}_receipt_owner
			RECEIPT_SUBJECT_VAR = zg361_mg_m{mechanism_id:03d}_receipt_subject
			RECEIPT_CYCLE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_cycle
			RECEIPT_CASE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_case
			RECEIPT_STATE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_state
			RECEIPT_CHOICE_VAR = zg361_mg_m{mechanism_id:03d}_receipt_choice
			EXPECTED_OWNER = var:zg361_case_{prefix}_owner
			EXPECTED_SUBJECT = this
			EXPECTED_CYCLE = var:zg361_case_{prefix}_cycle_serial
			EXPECTED_CASE = var:zg361_case_{prefix}_case_serial
			EXPECTED_STATE = {state}
			EXPECTED_CHOICE = 1
		}}"""


def receipt_not_current(domain: str, mechanism_id: int, state: int) -> str:
    return "NOT = {\n\t\t\t" + receipt_current(domain, mechanism_id, state).replace("\n", "\n\t\t\t") + "\n\t\t}"


def render_effects() -> bytes:
    bindings = "\n".join(
        f"# {row.mechanism_id:03d} {row.operation}: {row.effect} -> {row.consumer}"
        for row in BINDINGS
    )
    body = f'''
# ZhongGuo 361 manager/governance runtime — F032-036 + AK345-354 only.
# Callable integration seam: zg361_mg_dispatch_subordinate_managers_effect.
# Static-ready only: no MCP/CK3 live claim is made by generated source.
{bindings}

# Stable typed RED codes: 1 permission, 2 stale, 3 duplicate, 4 invariant,
# 5 resource exhausted, 6 insufficient frozen history.
zg361_mg_set_red_effect = {{
	set_variable = {{ name = zg361_mg_last_red_code value = $CODE$ }}
	set_variable = {{ name = zg361_mg_last_red_mechanism value = $MECHANISM$ }}
	debug_log = "ZG361MG: typed RED $CODE$ on mechanism $MECHANISM$"
}}

zg361_mg_clear_red_effect = {{
	remove_variable = zg361_mg_last_red_code
	remove_variable = zg361_mg_last_red_mechanism
}}

# The existing Jingcha is free/default-mandatory.  This compatibility adapter
# mirrors its refusal path with the exact owner requirement: opinion -25 and a
# next-review -50 marker.  Central callers remain outside this isolated file.
zg361_mg_refuse_jingcha_exact_effect = {{
	if = {{
		limit = {{
			has_variable = zg361_jingcha_pending
			has_variable = zg361_jingcha_mandate_superior
			has_variable = zg361_jingcha_mandate_year
		}}
		save_scope_as = zg361_mg_refusing_manager
		var:zg361_jingcha_mandate_superior = {{
			# Replace the legacy default -20 instance instead of stacking a second
			# modifier on it.  The resulting relation is exactly -25.
			remove_opinion = {{ modifier = zg361_refused_jingcha target = scope:zg361_mg_refusing_manager }}
			add_opinion = {{
				modifier = zg361_refused_jingcha
				target = scope:zg361_mg_refusing_manager
				opinion = -25
			}}
		}}
		set_variable = {{ name = zg361_mg_refusal_opinion_exact_superior value = var:zg361_jingcha_mandate_superior }}
		set_variable = {{ name = zg361_mg_refusal_opinion_exact_year value = var:zg361_jingcha_mandate_year }}
		if = {{
			limit = {{ has_variable = zg361_jingcha_mandate_reviewer }}
			set_variable = {{ name = zg361_skipped_jingcha_superior value = var:zg361_jingcha_mandate_reviewer }}
			set_variable = {{ name = zg361_skipped_jingcha_year value = var:zg361_jingcha_mandate_year }}
			set_variable = {{ name = zg361_mg_refusal_kpi_delta value = -50 }}
		}}
		zg361_clear_jingcha_mandate_effect = yes
		debug_log = "ZG361MG: exact Jingcha refusal recorded (-25 opinion, -50 next review)"
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 32 }} }}
}}

# Only celestial landed dukes or higher enter this dispatcher.  It intentionally
# has no is_ai=no gate: the owner-authorized second AI exception is background
# only, while visible report events below remain player-only.
zg361_mg_dispatch_subordinate_managers_effect = {{
	if = {{
		limit = {{
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			has_variable = zg361_review_serial
		}}
		every_vassal = {{
			limit = {{
				zg361_is_celestial_liege_trigger = yes
				liege = root
				has_variable = zg361_review_serial
				var:zg361_review_serial < root.var:zg361_review_serial
			}}
			zg361_mg_open_manager_governance_cases_effect = yes
		}}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 1 MECHANISM = 32 }} }}
}}

zg361_mg_schedule_f_ticket_effect = {{
	save_scope_as = zg361_mg_f_ticket_subject
	var:zg361_case_f_owner = {{ save_scope_as = zg361_mg_f_ticket_owner }}
	save_scope_value_as = {{ name = zg361_mg_f_ticket_cycle value = var:zg361_case_f_cycle_serial }}
	save_scope_value_as = {{ name = zg361_mg_f_ticket_case value = var:zg361_case_f_case_serial }}
	save_scope_value_as = {{ name = zg361_mg_f_ticket_state value = var:zg361_case_f_state }}
	trigger_event = {{ id = $EVENT$ days = $DAYS$ }}
}}

zg361_mg_schedule_ak_ticket_effect = {{
	save_scope_as = zg361_mg_ak_ticket_subject
	var:zg361_case_ak_owner = {{ save_scope_as = zg361_mg_ak_ticket_owner }}
	save_scope_value_as = {{ name = zg361_mg_ak_ticket_cycle value = var:zg361_case_ak_cycle_serial }}
	save_scope_value_as = {{ name = zg361_mg_ak_ticket_case value = var:zg361_case_ak_case_serial }}
	save_scope_value_as = {{ name = zg361_mg_ak_ticket_state value = var:zg361_case_ak_state }}
	trigger_event = {{ id = $EVENT$ days = $DAYS$ }}
}}

# Current scope = manager subject, ROOT = its direct superior.  Counts/barons
# fail the celestial-duke trigger and remain assessed-only through the core B1
# roster; the manager is itself assessed by this superior-owned F/AK case.
zg361_mg_open_manager_governance_cases_effect = {{
	if = {{
		limit = {{
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			liege = root
			root = {{
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
			}}
			has_variable = zg361_review_serial
			var:zg361_review_serial < root.var:zg361_review_serial
		}}
		zg361_mg_clear_red_effect = yes
		zg361_case_f_open_effect = yes
		if = {{
			limit = {{ var:zg361_case_kernel_applied = 1 }}
			zg361_mg_freeze_team_snapshot_effect = yes
			zg361_mg_m035_freeze_distribution_effect = yes
			zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.100 DAYS = 1 }}
		}}
		zg361_case_ak_open_effect = yes
		if = {{
			limit = {{ var:zg361_case_kernel_applied = 1 }}
			set_variable = {{ name = zg361_mg_admin_capacity_available value = 100 }}
			set_variable = {{ name = zg361_mg_admin_capacity_reserved value = 0 }}
			set_variable = {{ name = zg361_mg_admin_capacity_settled value = 0 }}
			set_variable = {{ name = zg361_mg_policy_source_serial value = var:zg361_review_serial }}
			zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.200 DAYS = 1 }}
		}}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 1 MECHANISM = 32 }} }}
}}

# Freeze exactly seven aggregate team facts from a strictly earlier manager
# cycle.  No grandchild character ID is projected into the superior's roster.
zg361_mg_freeze_team_snapshot_effect = {{
	set_variable = {{ name = zg361_mg_snapshot_source_serial value = var:zg361_review_serial }}
	set_variable = {{ name = zg361_mg_snapshot_current_serial value = root.var:zg361_review_serial }}
	set_variable = {{ name = zg361_mg_team_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_top_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_middle_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_bottom_n value = 0 }}
	if = {{ limit = {{ has_variable = zg361_scoreboard_managed_n }} set_variable = {{ name = zg361_mg_team_n value = var:zg361_scoreboard_managed_n }} }}
	if = {{ limit = {{ has_variable = zg361_scoreboard_managed_375_n }} set_variable = {{ name = zg361_mg_team_top_n value = var:zg361_scoreboard_managed_375_n }} }}
	if = {{ limit = {{ has_variable = zg361_scoreboard_managed_35_n }} set_variable = {{ name = zg361_mg_team_middle_n value = var:zg361_scoreboard_managed_35_n }} }}
	if = {{ limit = {{ has_variable = zg361_scoreboard_managed_325_n }} set_variable = {{ name = zg361_mg_team_bottom_n value = var:zg361_scoreboard_managed_325_n }} }}
	set_variable = {{
		name = zg361_mg_team_targets
		value = {{
			value = var:zg361_mg_team_top_n multiply = 20
			add = {{ value = var:zg361_mg_team_middle_n multiply = 5 }}
			subtract = {{ value = var:zg361_mg_team_bottom_n multiply = 25 }}
		}}
	}}
	set_variable = {{ name = zg361_mg_team_jingcha value = 10 }}
	set_variable = {{ name = zg361_mg_refusal_match value = 0 }}
	if = {{
		limit = {{
			has_variable = zg361_skipped_jingcha_superior
			has_variable = zg361_skipped_jingcha_year
			var:zg361_skipped_jingcha_superior = root
		}}
		set_variable = {{ name = zg361_mg_team_jingcha value = -50 }}
		set_variable = {{ name = zg361_mg_snapshot_mandate_year value = var:zg361_skipped_jingcha_year }}
		set_variable = {{ name = zg361_mg_refusal_match value = 1 }}
	}}
	else_if = {{
		limit = {{
			has_variable = zg361_result_evidence_jingcha
			var:zg361_result_evidence_jingcha = -50
			has_variable = zg361_result_case_owner
			var:zg361_result_case_owner = root
		}}
		set_variable = {{ name = zg361_mg_team_jingcha value = -50 }}
		set_variable = {{ name = zg361_mg_snapshot_mandate_year value = current_year }}
		set_variable = {{ name = zg361_mg_refusal_match value = 1 }}
	}}
	set_variable = {{ name = zg361_mg_team_calibration value = 0 }}
	set_variable = {{ name = zg361_mg_team_pip_success value = 0 }}
	set_variable = {{ name = zg361_mg_team_appeal_overturn value = 0 }}
	set_variable = {{ name = zg361_mg_team_retention value = 0 }}
	set_variable = {{ name = zg361_mg_team_hc_efficiency value = 0 }}
	save_scope_as = zg361_mg_snapshot_manager
	every_vassal = {{
		limit = {{
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			var:zg361_result_case_owner = scope:zg361_mg_snapshot_manager
			var:zg361_result_cycle_serial = scope:zg361_mg_snapshot_manager.var:zg361_review_serial
		}}
		scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_retention add = 2 }} }}
		if = {{
			limit = {{ has_variable = zg361_result_grade_reason var:zg361_result_grade_reason > 0 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_calibration add = -5 }} }}
		}}
		if = {{
			limit = {{ has_variable = zg361_result_regrade_delta var:zg361_result_regrade_delta > 0 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_appeal_overturn add = -5 }} }}
		}}
		if = {{
			limit = {{ has_variable = zg361_b2_m016_outcome var:zg361_b2_m016_outcome = 1 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_pip_success add = 5 }} }}
		}}
	}}
	set_variable = {{
		name = zg361_mg_team_hc_efficiency
		value = {{ value = var:zg361_mg_team_top_n subtract = var:zg361_mg_team_bottom_n multiply = 3 }}
	}}
	if = {{
		limit = {{ has_variable = zg361_mg_manager_score_delta }}
		change_variable = {{ name = zg361_mg_team_hc_efficiency add = var:zg361_mg_manager_score_delta }}
	}}
	set_variable = {{ name = zg361_mg_snapshot_grandchild_id_count value = 0 }}
}}

# 035 — strict/relaxed/off/mixed distribution semantics are frozen before the
# manager score.  Counts must conserve the frozen cohort exactly.
zg361_mg_m035_freeze_distribution_effect = {{
	if = {{
		limit = {{
			var:zg361_case_f_state = 1
			var:zg361_case_f_active = 1
			var:zg361_mg_snapshot_source_serial < var:zg361_mg_snapshot_current_serial
			{receipt_not_current("F", 35, 1)}
		}}
		set_variable = {{ name = zg361_mg_distribution_mode value = 1 }}
		if = {{
			limit = {{ has_variable = zg361_mechanism_035_choice }}
			set_variable = {{ name = zg361_mg_distribution_mode value = var:zg361_mechanism_035_choice }}
		}}
		set_variable = {{ name = zg361_mg_distribution_top_slots value = {{ value = var:zg361_mg_team_n multiply = 0.30 floor = yes }} }}
		set_variable = {{ name = zg361_mg_distribution_bottom_slots value = {{ value = var:zg361_mg_team_n multiply = 0.10 floor = yes }} }}
		if = {{
			limit = {{ var:zg361_mg_distribution_mode = 2 }}
			set_variable = {{ name = zg361_mg_distribution_bottom_slots value = {{ value = var:zg361_mg_team_n multiply = 0.05 floor = yes }} }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_distribution_mode = 3 }}
			set_variable = {{ name = zg361_mg_distribution_bottom_slots value = 0 }}
		}}
		if = {{
			limit = {{
				var:zg361_mg_team_n >= 5
				OR = {{ var:zg361_mg_distribution_mode = 1 var:zg361_mg_distribution_mode = 2 var:zg361_mg_distribution_mode = 4 }}
				var:zg361_mg_distribution_bottom_slots < 1
			}}
			set_variable = {{ name = zg361_mg_distribution_bottom_slots value = 1 }}
		}}
		set_variable = {{
			name = zg361_mg_distribution_middle_slots
			value = {{ value = var:zg361_mg_team_n subtract = var:zg361_mg_distribution_top_slots subtract = var:zg361_mg_distribution_bottom_slots }}
		}}
		set_variable = {{ name = zg361_mg_distribution_bottom_consequence value = 1 }}
		if = {{
			limit = {{ var:zg361_mg_distribution_mode = 4 var:zg361_mg_team_bottom_n = 0 }}
			set_variable = {{ name = zg361_mg_distribution_bottom_consequence value = 2 }}
		}}
		set_variable = {{
			name = zg361_mg_distribution_conserved
			value = {{ value = var:zg361_mg_distribution_top_slots add = var:zg361_mg_distribution_middle_slots add = var:zg361_mg_distribution_bottom_slots }}
		}}
		{receipt_call("F", 35, 1)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 35 }} }}
}}

# 032 — the superior consumes only the previous aggregate team snapshot.  A
# matching Jingcha refusal contributes exactly -50 once and is never inherited
# by a new superior.  The core KPI consumer retains ownership of removing its
# own skipped_jingcha marker.
zg361_mg_m032_score_manager_effect = {{
	if = {{
		limit = {{
			var:zg361_case_f_state = 1
			var:zg361_case_f_active = 1
			var:zg361_case_f_subject = this
			var:zg361_mg_snapshot_source_serial < var:zg361_case_f_cycle_serial
			{receipt_current("F", 35, 1)}
			var:zg361_mg_distribution_conserved = var:zg361_mg_team_n
			{receipt_not_current("F", 32, 1)}
			has_variable = zg361_mg_team_targets
			has_variable = zg361_mg_team_jingcha
			has_variable = zg361_mg_team_calibration
			has_variable = zg361_mg_team_pip_success
			has_variable = zg361_mg_team_appeal_overturn
			has_variable = zg361_mg_team_retention
			has_variable = zg361_mg_team_hc_efficiency
		}}
		set_variable = {{
			name = zg361_mg_manager_score
			value = {{
				value = var:zg361_mg_team_targets
				add = var:zg361_mg_team_jingcha
				add = var:zg361_mg_team_calibration
				add = var:zg361_mg_team_pip_success
				add = var:zg361_mg_team_appeal_overturn
				add = var:zg361_mg_team_retention
				add = var:zg361_mg_team_hc_efficiency
			}}
		}}
		if = {{
			limit = {{
				var:zg361_mg_refusal_match = 1
				trigger_if = {{
					limit = {{ has_variable = zg361_mg_refusal_score_consumed_cycle }}
					NOT = {{ var:zg361_mg_refusal_score_consumed_cycle = var:zg361_case_f_cycle_serial }}
				}}
				trigger_else = {{ always = yes }}
			}}
			set_variable = {{ name = zg361_mg_refusal_score_consumed_cycle value = var:zg361_case_f_cycle_serial }}
			set_variable = {{ name = zg361_mg_refusal_score_consumed_delta value = -50 }}
			set_variable = {{ name = zg361_mg_refusal_opinion_exact_match value = 0 }}
			if = {{
				limit = {{ has_variable = zg361_mg_refusal_opinion_exact_superior has_variable = zg361_mg_refusal_opinion_exact_year }}
				if = {{
					limit = {{ var:zg361_mg_refusal_opinion_exact_superior = root var:zg361_mg_refusal_opinion_exact_year = var:zg361_mg_snapshot_mandate_year }}
					set_variable = {{ name = zg361_mg_refusal_opinion_exact_match value = 1 }}
				}}
			}}
			if = {{
				limit = {{ var:zg361_mg_refusal_opinion_exact_match = 0 }}
				save_scope_as = zg361_mg_refusal_subject
				var:zg361_case_f_owner = {{
					# Compatibility for a save that went through the legacy -20 caller:
					# remove that instance, then install exactly one -25 instance.
					remove_opinion = {{ modifier = zg361_refused_jingcha target = scope:zg361_mg_refusal_subject }}
					add_opinion = {{ modifier = zg361_refused_jingcha target = scope:zg361_mg_refusal_subject opinion = -25 }}
				}}
				set_variable = {{ name = zg361_mg_refusal_opinion_exact_superior value = var:zg361_case_f_owner }}
				set_variable = {{ name = zg361_mg_refusal_opinion_exact_year value = var:zg361_mg_snapshot_mandate_year }}
			}}
			set_variable = {{ name = zg361_mg_refusal_opinion_normalized_cycle value = var:zg361_case_f_cycle_serial }}
		}}
		{receipt_call("F", 32, 1)}
		{transition_call("F", 1)}
		if = {{
			limit = {{ var:zg361_case_f_state = 2 }}
			zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.101 DAYS = 1 }}
		}}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 32 }} }}
}}

# 033 — profile weighting produces five bounded, reproducible reason codes.
# Relationship pressure is one explicit code and raises appeal risk; it never
# rewrites frozen KPI evidence.
zg361_mg_m033_reason_code_effect = {{
	if = {{
		limit = {{
			var:zg361_case_f_state = 2
			var:zg361_case_f_active = 1
			has_variable = zg361_mg_manager_score
			{receipt_not_current("F", 33, 2)}
		}}
		set_variable = {{ name = zg361_mg_profile_code value = 1 }}
		if = {{ limit = {{ has_variable = zg361_mechanism_033_choice }} set_variable = {{ name = zg361_mg_profile_code value = var:zg361_mechanism_033_choice }} }}
		set_variable = {{ name = zg361_mg_reason_calibration value = {{ value = var:zg361_mg_team_calibration multiply = 3 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_appeal value = {{ value = var:zg361_mg_team_appeal_overturn multiply = 2 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_pip value = {{ value = var:zg361_mg_team_pip_success multiply = 2 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_delivery value = {{ value = var:zg361_mg_team_targets max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_hc value = {{ value = var:zg361_mg_team_hc_efficiency multiply = 2 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_relationship_once value = 0 }}
		set_variable = {{ name = zg361_mg_reason_appeal_risk value = 0 }}
		if = {{
			limit = {{ var:zg361_mg_profile_code = 2 }}
			set_variable = {{ name = zg361_mg_reason_relationship_once value = 5 }}
			set_variable = {{ name = zg361_mg_reason_appeal_risk value = 5 }}
		}}
		set_variable = {{
			name = zg361_mg_reason_total
			value = {{ value = var:zg361_mg_reason_calibration add = var:zg361_mg_reason_appeal add = var:zg361_mg_reason_pip add = var:zg361_mg_reason_delivery add = var:zg361_mg_reason_hc add = var:zg361_mg_reason_relationship_once }}
		}}
		set_variable = {{ name = zg361_mg_reason_weight_version value = 1 }}
		{receipt_call("F", 33, 2)}
		{transition_call("F", 2)}
		if = {{ limit = {{ var:zg361_case_f_state = 3 }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.102 DAYS = 1 }} }}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 33 }} }}
}}

# 034 — read-only performance/potential classification.  No KPI, grade, gold,
# treasury, HC, or capacity variable is mutated by this effect.  A manager's
# first review is explicitly unclassified (code 0) but still advances the case;
# otherwise one missing historical sample would deadlock every later review.
zg361_mg_m034_freeze_nine_box_effect = {{
	if = {{
		limit = {{
			var:zg361_case_f_state = 3
			var:zg361_case_f_active = 1
			has_variable = zg361_mg_manager_score
			{receipt_not_current("F", 34, 3)}
		}}
		set_variable = {{ name = zg361_mg_history_score_1 value = var:zg361_mg_manager_score }}
		set_variable = {{ name = zg361_mg_history_count value = 1 }}
		set_variable = {{ name = zg361_mg_history_selected value = 0 }}
		set_variable = {{ name = zg361_mg_nine_box_ready value = 0 }}
		set_variable = {{ name = zg361_mg_nine_box_status value = 6 }}
		set_variable = {{ name = zg361_mg_nine_box_code value = 0 }}
		if = {{
			limit = {{ has_variable = zg361_mg_previous_manager_score has_variable = zg361_mg_previous_manager_score_serial }}
			if = {{
				limit = {{ var:zg361_mg_previous_manager_score_serial < var:zg361_case_f_cycle_serial }}
				set_variable = {{ name = zg361_mg_history_score_2 value = var:zg361_mg_previous_manager_score }}
				set_variable = {{ name = zg361_mg_history_selected value = 1 }}
			}}
		}}
		if = {{
			limit = {{ var:zg361_mg_history_selected = 0 has_variable = zg361_result_kpi_frozen has_variable = zg361_result_cycle_serial }}
			if = {{
				limit = {{ var:zg361_result_cycle_serial < var:zg361_case_f_cycle_serial }}
				set_variable = {{ name = zg361_mg_history_score_2 value = var:zg361_result_kpi_frozen }}
				set_variable = {{ name = zg361_mg_history_selected value = 1 }}
			}}
		}}
		if = {{
			limit = {{ var:zg361_mg_history_selected = 1 }}
			set_variable = {{ name = zg361_mg_history_count value = 2 }}
			set_variable = {{ name = zg361_mg_performance_axis value = 2 }}
			set_variable = {{ name = zg361_mg_performance_mean value = {{ value = var:zg361_mg_history_score_1 add = var:zg361_mg_history_score_2 divide = 2 }} }}
			if = {{ limit = {{ var:zg361_mg_performance_mean < 40 }} set_variable = {{ name = zg361_mg_performance_axis value = 1 }} }}
			else_if = {{ limit = {{ var:zg361_mg_performance_mean >= 75 }} set_variable = {{ name = zg361_mg_performance_axis value = 3 }} }}
			set_variable = {{ name = zg361_mg_potential_growth value = 50 }}
			set_variable = {{ name = zg361_mg_potential_fit value = 50 }}
			set_variable = {{ name = zg361_mg_potential_raw value = 50 }}
			if = {{ limit = {{ has_variable = zg361_result_evidence_growth }} set_variable = {{ name = zg361_mg_potential_growth value = {{ value = var:zg361_result_evidence_growth add = 50 max = 100 min = 0 }} }} }}
			if = {{ limit = {{ has_variable = zg361_result_evidence_capability }} set_variable = {{ name = zg361_mg_potential_fit value = {{ value = var:zg361_result_evidence_capability add = 50 max = 100 min = 0 }} }} }}
			set_variable = {{ name = zg361_mg_potential_mean value = {{ value = var:zg361_mg_potential_growth add = var:zg361_mg_potential_fit add = var:zg361_mg_potential_raw divide = 3 }} }}
			set_variable = {{ name = zg361_mg_potential_axis value = 2 }}
			if = {{ limit = {{ var:zg361_mg_potential_mean < 40 }} set_variable = {{ name = zg361_mg_potential_axis value = 1 }} }}
			else_if = {{ limit = {{ var:zg361_mg_potential_mean >= 75 }} set_variable = {{ name = zg361_mg_potential_axis value = 3 }} }}
			set_variable = {{ name = zg361_mg_nine_box_code value = {{ value = var:zg361_mg_performance_axis subtract = 1 multiply = 3 add = var:zg361_mg_potential_axis }} }}
			set_variable = {{ name = zg361_mg_nine_box_ready value = 1 }}
			set_variable = {{ name = zg361_mg_nine_box_status value = 0 }}
		}}
		else = {{ zg361_mg_set_red_effect = {{ CODE = 6 MECHANISM = 34 }} }}
		set_variable = {{ name = zg361_mg_nine_box_frozen_cycle value = var:zg361_case_f_cycle_serial }}
		{receipt_call("F", 34, 3)}
		{transition_call("F", 3)}
		if = {{ limit = {{ var:zg361_case_f_state = 4 }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.103 DAYS = 1 }} }}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 6 MECHANISM = 34 }} }}
}}

zg361_mg_reset_decade_log_effect = {{
	set_variable = {{ name = zg361_mg_decade_log_count value = 0 }}
	set_variable = {{ name = zg361_mg_decade_grade_top value = 0 }}
	set_variable = {{ name = zg361_mg_decade_grade_middle value = 0 }}
	set_variable = {{ name = zg361_mg_decade_grade_bottom value = 0 }}
	set_variable = {{ name = zg361_mg_decade_appeal_overturns value = 0 }}
	set_variable = {{ name = zg361_mg_decade_pip_successes value = 0 }}
	set_variable = {{ name = zg361_mg_decade_promotions value = 0 }}
	set_variable = {{ name = zg361_mg_decade_exits value = 0 }}
	set_variable = {{ name = zg361_mg_decade_bonus_in value = 0 }}
	set_variable = {{ name = zg361_mg_decade_bonus_out value = 0 }}
	set_variable = {{ name = zg361_mg_decade_hc_efficiency value = 0 }}
	set_variable = {{ name = zg361_mg_decade_talent_outflow value = 0 }}
	set_variable = {{ name = zg361_mg_decade_governance_score value = 0 }}
	set_variable = {{ name = zg361_mg_decade_manager_reputation value = 0 }}
	set_variable = {{ name = zg361_mg_decade_report_ready value = 0 }}
}}

# 036 — ten unique consecutive annual logs, segmented by the superior owner.
zg361_mg_m036_append_decade_log_effect = {{
	if = {{
		limit = {{
			var:zg361_case_f_state = 4
			var:zg361_case_f_active = 1
			{receipt_not_current("F", 36, 4)}
		}}
		set_variable = {{ name = zg361_mg_expected_log_year value = current_year }}
		if = {{ limit = {{ has_variable = zg361_mg_decade_last_year }} set_variable = {{ name = zg361_mg_expected_log_year value = {{ value = var:zg361_mg_decade_last_year add = 1 }} }} }}
		if = {{
			limit = {{
				OR = {{
					NOT = {{ has_variable = zg361_mg_decade_owner }}
					NOT = {{ var:zg361_mg_decade_owner = var:zg361_case_f_owner }}
					AND = {{ has_variable = zg361_mg_decade_last_year NOT = {{ var:zg361_mg_expected_log_year = current_year }} }}
					AND = {{ has_variable = zg361_mg_decade_log_count var:zg361_mg_decade_log_count >= 10 }}
				}}
			}}
			zg361_mg_reset_decade_log_effect = yes
			set_variable = {{ name = zg361_mg_decade_owner value = var:zg361_case_f_owner }}
			set_variable = {{ name = zg361_mg_decade_start_year value = current_year }}
		}}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_decade_log_count }} }} zg361_mg_reset_decade_log_effect = yes }}
		change_variable = {{ name = zg361_mg_decade_log_count add = 1 }}
		set_variable = {{ name = zg361_mg_decade_last_year value = current_year }}
		change_variable = {{ name = zg361_mg_decade_grade_top add = var:zg361_mg_team_top_n }}
		change_variable = {{ name = zg361_mg_decade_grade_middle add = var:zg361_mg_team_middle_n }}
		change_variable = {{ name = zg361_mg_decade_grade_bottom add = var:zg361_mg_team_bottom_n }}
		change_variable = {{ name = zg361_mg_decade_appeal_overturns add = {{ value = 0 subtract = var:zg361_mg_team_appeal_overturn divide = 5 }} }}
		change_variable = {{ name = zg361_mg_decade_pip_successes add = {{ value = var:zg361_mg_team_pip_success divide = 5 }} }}
		change_variable = {{ name = zg361_mg_decade_hc_efficiency add = var:zg361_mg_team_hc_efficiency }}
		change_variable = {{ name = zg361_mg_decade_governance_score add = var:zg361_mg_manager_score }}
		change_variable = {{ name = zg361_mg_decade_manager_reputation add = var:zg361_mg_reason_total }}
		set_variable = {{ name = zg361_mg_decade_bonus_net value = {{ value = var:zg361_mg_decade_bonus_in subtract = var:zg361_mg_decade_bonus_out }} }}
		if = {{
			limit = {{ var:zg361_mg_decade_log_count = 10 }}
			set_variable = {{ name = zg361_mg_decade_report_ready value = 1 }}
			set_variable = {{ name = zg361_mg_decade_report_end_year value = current_year }}
		}}
		set_variable = {{ name = zg361_mg_previous_manager_score value = var:zg361_mg_manager_score }}
		set_variable = {{ name = zg361_mg_previous_manager_score_serial value = var:zg361_case_f_cycle_serial }}
		{receipt_call("F", 36, 4)}
		{transition_call("F", 4)}
		if = {{
			limit = {{ var:zg361_case_f_state = 5 var:zg361_case_f_active = 0 }}
			if = {{ limit = {{ is_ai = no }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.120 DAYS = 1 }} }}
			else = {{ debug_log = "ZG361MG: eligible AI manager report projected silently" }}
		}}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 36 }} }}
}}

# 345 — calendar changes begin only in the next complete review cycle.
zg361_mg_m345_freeze_calendar_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 1 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 345, 1)} }}
		set_variable = {{ name = zg361_mg_calendar_frequency value = 1 }}
		if = {{ limit = {{ has_variable = zg361_mechanism_345_choice }} set_variable = {{ name = zg361_mg_calendar_frequency value = var:zg361_mechanism_345_choice }} }}
		set_variable = {{ name = zg361_mg_calendar_effective_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		set_variable = {{ name = zg361_mg_calendar_final_n value = 1 }}
		set_variable = {{ name = zg361_mg_calendar_checkin_n value = 1 }}
		set_variable = {{ name = zg361_mg_calendar_admin_hours value = 20 }}
		if = {{ limit = {{ var:zg361_mg_calendar_frequency = 2 }} set_variable = {{ name = zg361_mg_calendar_final_n value = 2 }} set_variable = {{ name = zg361_mg_calendar_checkin_n value = 0 }} set_variable = {{ name = zg361_mg_calendar_admin_hours value = 36 }} }}
		else_if = {{ limit = {{ var:zg361_mg_calendar_frequency = 3 }} set_variable = {{ name = zg361_mg_calendar_final_n value = 4 }} set_variable = {{ name = zg361_mg_calendar_checkin_n value = 0 }} set_variable = {{ name = zg361_mg_calendar_admin_hours value = 72 }} }}
		set_variable = {{ name = zg361_mg_calendar_player_ai_batch value = 1 }}
		{receipt_call("AK", 345, 1)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 345 }} }}
}}

# External consumers may freeze one material signal.  The stage consumer below
# consumes it once without rerunning the cohort.
zg361_mg_record_offcycle_signal_effect = {{
	if = {{
		limit = {{
			zg361_is_celestial_liege_trigger = yes
			NOT = {{ has_variable = zg361_mg_offcycle_pending }}
			$MATERIALITY$ >= 50
		}}
		set_variable = {{ name = zg361_mg_offcycle_pending value = 1 }}
		set_variable = {{ name = zg361_mg_offcycle_materiality value = $MATERIALITY$ }}
		set_variable = {{ name = zg361_mg_offcycle_signal_serial value = $SIGNAL_SERIAL$ }}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 346 }} }}
}}

zg361_mg_m346_consume_offcycle_signal_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 1 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 346, 1)} }}
		set_variable = {{ name = zg361_mg_offcycle_consumed value = 0 }}
		set_variable = {{ name = zg361_mg_offcycle_cohort_reruns value = 0 }}
		if = {{
			limit = {{ has_variable = zg361_mg_offcycle_pending var:zg361_mg_offcycle_pending = 1 has_variable = zg361_mg_offcycle_materiality var:zg361_mg_offcycle_materiality >= 50 }}
			set_variable = {{ name = zg361_mg_offcycle_action value = 1 }}
			if = {{ limit = {{ has_variable = zg361_mechanism_346_choice }} set_variable = {{ name = zg361_mg_offcycle_action value = var:zg361_mechanism_346_choice }} }}
			set_variable = {{ name = zg361_mg_offcycle_consumed value = 1 }}
			set_variable = {{ name = zg361_mg_offcycle_consumed_cycle value = var:zg361_case_ak_cycle_serial }}
			remove_variable = zg361_mg_offcycle_pending
		}}
		{receipt_call("AK", 346, 1)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 346 }} }}
}}

zg361_mg_ak_stage_1_effect = {{
	zg361_mg_m345_freeze_calendar_effect = yes
	zg361_mg_m346_consume_offcycle_signal_effect = yes
	if = {{
		limit = {{ {receipt_current("AK", 345, 1)} {receipt_current("AK", 346, 1)} }}
		{transition_call("AK", 1)}
		if = {{ limit = {{ var:zg361_case_ak_state = 2 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.201 DAYS = 30 }} }}
	}}
}}

# 347 — one bounded override records beneficiary, bearer and reason while the
# frozen ranking multiset and quota counts remain unchanged.
zg361_mg_m347_consume_override_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 2 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 347, 2)} }}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_override_budget }} }} set_variable = {{ name = zg361_mg_override_budget value = 3 }} set_variable = {{ name = zg361_mg_override_used value = 0 }} }}
		set_variable = {{ name = zg361_mg_override_applied value = 0 }}
		set_variable = {{ name = zg361_mg_override_quota_before value = var:zg361_mg_team_n }}
		if = {{
			limit = {{
				has_variable = zg361_mg_override_beneficiary
				has_variable = zg361_mg_override_bearer
				has_variable = zg361_mg_override_reason
				NOT = {{ var:zg361_mg_override_beneficiary = var:zg361_mg_override_bearer }}
				var:zg361_mg_override_used < var:zg361_mg_override_budget
			}}
			change_variable = {{ name = zg361_mg_override_used add = 1 }}
			set_variable = {{ name = zg361_mg_override_applied value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_override_quota_after value = var:zg361_mg_team_n }}
		set_variable = {{ name = zg361_mg_override_quota_neutral value = 1 }}
		if = {{ limit = {{ NOT = {{ var:zg361_mg_override_quota_before = var:zg361_mg_override_quota_after }} }} set_variable = {{ name = zg361_mg_override_quota_neutral value = 0 }} }}
		{receipt_call("AK", 347, 2)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 347 }} }}
}}

# 348 — the exception token binds owner/subject/cycle/case/state/expiry.  Its
# independent due event can renew only with new evidence; stale copies no-op.
zg361_mg_m348_bind_exception_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 2 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 348, 2)} }}
		set_variable = {{ name = zg361_mg_exception_owner value = var:zg361_case_ak_owner }}
		set_variable = {{ name = zg361_mg_exception_subject value = this }}
		set_variable = {{ name = zg361_mg_exception_cycle value = var:zg361_case_ak_cycle_serial }}
		set_variable = {{ name = zg361_mg_exception_case value = var:zg361_case_ak_case_serial }}
		set_variable = {{ name = zg361_mg_exception_state value = 1 }}
		set_variable = {{ name = zg361_mg_exception_expiry_year value = {{ value = current_year add = 1 }} }}
		set_variable = {{ name = zg361_mg_exception_pending value = 1 }}
		set_variable = {{ name = zg361_mg_exception_new_evidence value = 0 }}
		save_scope_as = zg361_mg_exception_ticket_subject
		var:zg361_case_ak_owner = {{ save_scope_as = zg361_mg_exception_ticket_owner }}
		save_scope_value_as = {{ name = zg361_mg_exception_ticket_cycle value = var:zg361_case_ak_cycle_serial }}
		save_scope_value_as = {{ name = zg361_mg_exception_ticket_case value = var:zg361_case_ak_case_serial }}
		save_scope_value_as = {{ name = zg361_mg_exception_ticket_state value = 1 }}
		save_scope_value_as = {{ name = zg361_mg_exception_ticket_expiry value = var:zg361_mg_exception_expiry_year }}
		trigger_event = {{ id = zg361mg.250 days = 365 }}
		{receipt_call("AK", 348, 2)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 348 }} }}
}}

zg361_mg_ak_stage_2_effect = {{
	zg361_mg_m347_consume_override_effect = yes
	zg361_mg_m348_bind_exception_effect = yes
	if = {{
		limit = {{ {receipt_current("AK", 347, 2)} {receipt_current("AK", 348, 2)} var:zg361_mg_override_quota_neutral = 1 }}
		{transition_call("AK", 2)}
		if = {{ limit = {{ var:zg361_case_ak_state = 3 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.202 DAYS = 30 }} }}
	}}
}}

# 349 uses administrative capacity, not gold.  Therefore no treasury/personal
# charge is applicable in this 15-ID slice.  Capacity follows reserve -> settle
# and has an explicit guarded refund path.
zg361_mg_m349_run_audit_effect = {{
	if = {{
		limit = {{
			var:zg361_case_ak_state = 3
			var:zg361_case_ak_active = 1
			has_variable = zg361_mg_admin_capacity_available
			{receipt_not_current("AK", 349, 3)}
		}}
		set_variable = {{ name = zg361_mg_audit_population value = {{ value = var:zg361_mg_team_n max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_rate value = 20 }}
		if = {{ limit = {{ has_variable = zg361_mechanism_349_choice var:zg361_mechanism_349_choice = 2 }} set_variable = {{ name = zg361_mg_audit_rate value = 10 }} }}
		set_variable = {{ name = zg361_mg_audit_effective_rate value = {{ value = var:zg361_mg_audit_rate subtract = 5 max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_sample_n value = {{ value = var:zg361_mg_audit_population multiply = var:zg361_mg_audit_effective_rate divide = 100 floor = yes max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_seed value = {{ value = var:zg361_case_ak_cycle_serial multiply = 1000 add = var:zg361_case_ak_case_serial }} }}
		set_variable = {{ name = zg361_mg_audit_high_risk_n value = {{ value = var:zg361_mg_team_bottom_n max = 1 min = var:zg361_mg_audit_sample_n }} }}
		set_variable = {{ name = zg361_mg_audit_selection_fingerprint value = {{ value = var:zg361_mg_audit_seed add = var:zg361_mg_audit_high_risk_n multiply = 31 add = var:zg361_mg_audit_sample_n }} }}
		set_variable = {{ name = zg361_mg_m349_audit_hours value = {{ value = var:zg361_mg_audit_sample_n multiply = 2 }} }}
		if = {{
			limit = {{ var:zg361_mg_admin_capacity_available >= var:zg361_mg_m349_audit_hours }}
			zg361_case_kernel_reserve_transaction_effect = {{
				OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision
				AVAILABLE_VAR = zg361_mg_admin_capacity_available RESERVED_VAR = zg361_mg_admin_capacity_reserved
				RECEIPT_AMOUNT_VAR = zg361_mg_m349_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m349_capacity_status RECEIPT_OWNER_VAR = zg361_mg_m349_capacity_owner RECEIPT_CYCLE_VAR = zg361_mg_m349_capacity_cycle RECEIPT_CASE_VAR = zg361_mg_m349_capacity_case
				TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 3 AMOUNT = var:zg361_mg_m349_audit_hours
			}}
			if = {{
				limit = {{ var:zg361_case_kernel_applied = 1 }}
				zg361_case_kernel_settle_transaction_effect = {{
					OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision
					RESERVED_VAR = zg361_mg_admin_capacity_reserved SETTLED_VAR = zg361_mg_admin_capacity_settled RECEIPT_AMOUNT_VAR = zg361_mg_m349_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m349_capacity_status
					TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 3
				}}
				set_variable = {{ name = zg361_mg_audit_findings value = {{ value = var:zg361_mg_team_bottom_n min = var:zg361_mg_audit_sample_n }} }}
				set_variable = {{ name = zg361_mg_audit_clean value = {{ value = var:zg361_mg_audit_sample_n subtract = var:zg361_mg_audit_findings }} }}
				set_variable = {{ name = zg361_mg_audit_settled value = 1 }}
				if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_policy_trust }} }} set_variable = {{ name = zg361_mg_policy_trust value = 0 }} }}
				change_variable = {{ name = zg361_mg_policy_trust add = var:zg361_mg_audit_clean }}
				{receipt_call("AK", 349, 3)}
			}}
		}}
		else = {{ zg361_mg_set_red_effect = {{ CODE = 5 MECHANISM = 349 }} }}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 349 }} }}
}}

zg361_mg_refund_audit_capacity_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 3 var:zg361_case_ak_active = 1 has_variable = zg361_mg_m349_capacity_status var:zg361_mg_m349_capacity_status = 2 }}
		zg361_case_kernel_refund_transaction_effect = {{
			OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision
			AVAILABLE_VAR = zg361_mg_admin_capacity_available RESERVED_VAR = zg361_mg_admin_capacity_reserved SETTLED_VAR = zg361_mg_admin_capacity_settled RECEIPT_AMOUNT_VAR = zg361_mg_m349_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m349_capacity_status
			TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 3
		}}
		set_variable = {{ name = zg361_mg_audit_refunded value = 1 }}
	}}
	else = {{ debug_log = "ZG361MG: stale or duplicate audit refund ignored" }}
}}

# 350 — old thresholds and history remain immutable; only a future benchmark
# version and explanation code are appended.
zg361_mg_m350_version_benchmark_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 3 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 350, 3)} }}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_benchmark_old_version }} }} set_variable = {{ name = zg361_mg_benchmark_old_version value = 1 }} }}
		set_variable = {{ name = zg361_mg_benchmark_history_value value = var:zg361_mg_manager_score }}
		set_variable = {{ name = zg361_mg_benchmark_history_formula value = 1 }}
		set_variable = {{ name = zg361_mg_benchmark_history_version value = var:zg361_mg_benchmark_old_version }}
		set_variable = {{ name = zg361_mg_benchmark_new_version value = {{ value = var:zg361_mg_benchmark_old_version add = 1 }} }}
		set_variable = {{ name = zg361_mg_benchmark_effective_cycle value = var:zg361_mg_calendar_effective_cycle }}
		set_variable = {{ name = zg361_mg_benchmark_top_threshold value = 75 }}
		set_variable = {{ name = zg361_mg_benchmark_middle_threshold value = 40 }}
		set_variable = {{ name = zg361_mg_benchmark_explanation_code value = 35001 }}
		{receipt_call("AK", 350, 3)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 350 }} }}
}}

zg361_mg_ak_stage_3_effect = {{
	zg361_mg_m349_run_audit_effect = yes
	zg361_mg_m350_version_benchmark_effect = yes
	if = {{
		limit = {{ {receipt_current("AK", 349, 3)} {receipt_current("AK", 350, 3)} var:zg361_mg_audit_settled = 1 }}
		{transition_call("AK", 3)}
		if = {{ limit = {{ var:zg361_case_ak_state = 4 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.203 DAYS = 180 }} }}
	}}
}}

# 351 — deterministic first/second ordered direct regions become disjoint pilot
# and control cells.  Differences are computed only when both frozen outcomes
# and all preregistered metrics exist.
zg361_mg_m351_measure_pilot_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 4 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 351, 4)} }}
		set_variable = {{ name = zg361_mg_pilot_metric_n value = 3 }}
		set_variable = {{ name = zg361_mg_pilot_region_cursor value = 0 }}
		set_variable = {{ name = zg361_mg_pilot_result_ready value = 0 }}
		ordered_vassal = {{
			limit = {{ zg361_is_reviewable_vassal_trigger = yes has_variable = zg361_result_kpi_frozen }}
			order_by = age
			max = 2
			root = {{ change_variable = {{ name = zg361_mg_pilot_region_cursor add = 1 }} }}
			if = {{
				limit = {{ root.var:zg361_mg_pilot_region_cursor = 1 }}
				save_temporary_scope_as = zg361_mg_pilot_region_candidate
				root = {{ set_variable = {{ name = zg361_mg_pilot_region value = scope:zg361_mg_pilot_region_candidate }} set_variable = {{ name = zg361_mg_pilot_outcome value = scope:zg361_mg_pilot_region_candidate.var:zg361_result_kpi_frozen }} }}
			}}
			else = {{
				save_temporary_scope_as = zg361_mg_control_region_candidate
				root = {{ set_variable = {{ name = zg361_mg_control_region value = scope:zg361_mg_control_region_candidate }} set_variable = {{ name = zg361_mg_control_outcome value = scope:zg361_mg_control_region_candidate.var:zg361_result_kpi_frozen }} }}
			}}
		}}
		if = {{
			limit = {{ has_variable = zg361_mg_pilot_region has_variable = zg361_mg_control_region NOT = {{ var:zg361_mg_pilot_region = var:zg361_mg_control_region }} has_variable = zg361_mg_pilot_outcome has_variable = zg361_mg_control_outcome }}
			set_variable = {{ name = zg361_mg_pilot_difference value = {{ value = var:zg361_mg_pilot_outcome subtract = var:zg361_mg_control_outcome }} }}
			set_variable = {{ name = zg361_mg_pilot_result_ready value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_pilot_end_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		{receipt_call("AK", 351, 4)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 351 }} }}
}}

# 352 — original value/formula/policy version are separate immutable fields;
# comparable mapping or a new-series break never overwrites them.
zg361_mg_m352_map_history_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 4 var:zg361_case_ak_active = 1 has_variable = zg361_mg_benchmark_history_value {receipt_not_current("AK", 352, 4)} }}
		set_variable = {{ name = zg361_mg_history_original_value value = var:zg361_mg_benchmark_history_value }}
		set_variable = {{ name = zg361_mg_history_original_formula value = var:zg361_mg_benchmark_history_formula }}
		set_variable = {{ name = zg361_mg_history_original_policy_version value = var:zg361_mg_benchmark_history_version }}
		set_variable = {{ name = zg361_mg_history_mapping_version value = var:zg361_mg_benchmark_new_version }}
		set_variable = {{ name = zg361_mg_history_new_series value = 0 }}
		if = {{
			limit = {{ has_variable = zg361_mechanism_352_choice var:zg361_mechanism_352_choice = 3 }}
			set_variable = {{ name = zg361_mg_history_new_series value = 1 }}
			remove_variable = zg361_mg_history_mapped_value
		}}
		else = {{ set_variable = {{ name = zg361_mg_history_mapped_value value = var:zg361_mg_history_original_value }} }}
		{receipt_call("AK", 352, 4)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 352 }} }}
}}

zg361_mg_ak_stage_4_effect = {{
	zg361_mg_m351_measure_pilot_effect = yes
	zg361_mg_m352_map_history_effect = yes
	if = {{
		# A realm with fewer than two eligible regions records an unavailable
		# pilot result, but does not permanently deadlock the policy case.
		limit = {{ {receipt_current("AK", 351, 4)} {receipt_current("AK", 352, 4)} }}
		{transition_call("AK", 4)}
		if = {{ limit = {{ var:zg361_case_ak_state = 5 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.204 DAYS = 180 }} }}
	}}
}}

# 353 — forms + meetings + appeals + calibration + interruptions are charged
# once against governance capacity.  Error/overturn rebound feeds the next F032
# manager score; it never mutates the already frozen current KPI.
zg361_mg_m353_charge_admin_capacity_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 5 var:zg361_case_ak_active = 1 has_variable = zg361_mg_admin_capacity_available {receipt_not_current("AK", 353, 5)} }}
		set_variable = {{ name = zg361_mg_admin_form_hours value = var:zg361_mg_team_n }}
		set_variable = {{ name = zg361_mg_admin_meeting_hours value = var:zg361_mg_calendar_final_n }}
		set_variable = {{ name = zg361_mg_admin_appeal_hours value = {{ value = 0 subtract = var:zg361_mg_team_appeal_overturn divide = 5 multiply = 3 max = 0 }} }}
		set_variable = {{ name = zg361_mg_admin_calibration_hours value = {{ value = 0 subtract = var:zg361_mg_team_calibration divide = 5 multiply = 2 max = 0 }} }}
		set_variable = {{ name = zg361_mg_admin_interruption_hours value = {{ value = var:zg361_mg_offcycle_consumed multiply = 2 }} }}
		set_variable = {{ name = zg361_mg_m353_admin_hours value = {{ value = var:zg361_mg_admin_form_hours add = var:zg361_mg_admin_meeting_hours add = var:zg361_mg_admin_appeal_hours add = var:zg361_mg_admin_calibration_hours add = var:zg361_mg_admin_interruption_hours }} }}
		if = {{
			limit = {{ var:zg361_mg_admin_capacity_available >= var:zg361_mg_m353_admin_hours }}
			zg361_case_kernel_reserve_transaction_effect = {{
				OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision
				AVAILABLE_VAR = zg361_mg_admin_capacity_available RESERVED_VAR = zg361_mg_admin_capacity_reserved RECEIPT_AMOUNT_VAR = zg361_mg_m353_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m353_capacity_status RECEIPT_OWNER_VAR = zg361_mg_m353_capacity_owner RECEIPT_CYCLE_VAR = zg361_mg_m353_capacity_cycle RECEIPT_CASE_VAR = zg361_mg_m353_capacity_case
				TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 5 AMOUNT = var:zg361_mg_m353_admin_hours
			}}
			if = {{
				limit = {{ var:zg361_case_kernel_applied = 1 }}
				zg361_case_kernel_settle_transaction_effect = {{ OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision RESERVED_VAR = zg361_mg_admin_capacity_reserved SETTLED_VAR = zg361_mg_admin_capacity_settled RECEIPT_AMOUNT_VAR = zg361_mg_m353_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m353_capacity_status TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 5 }}
				set_variable = {{ name = zg361_mg_admin_capacity_lost value = var:zg361_mg_m353_admin_hours }}
				set_variable = {{ name = zg361_mg_admin_capacity_remaining value = var:zg361_mg_admin_capacity_available }}
				set_variable = {{ name = zg361_mg_manager_score_delta value = {{ value = 0 subtract = var:zg361_mg_admin_appeal_hours subtract = var:zg361_mg_admin_calibration_hours }} }}
				{receipt_call("AK", 353, 5)}
			}}
		}}
		else = {{ zg361_mg_set_red_effect = {{ CODE = 5 MECHANISM = 353 }} }}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 353 }} }}
}}

zg361_mg_refund_admin_capacity_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 5 var:zg361_case_ak_active = 1 has_variable = zg361_mg_m353_capacity_status var:zg361_mg_m353_capacity_status = 2 }}
		zg361_case_kernel_refund_transaction_effect = {{ OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision AVAILABLE_VAR = zg361_mg_admin_capacity_available RESERVED_VAR = zg361_mg_admin_capacity_reserved SETTLED_VAR = zg361_mg_admin_capacity_settled RECEIPT_AMOUNT_VAR = zg361_mg_m353_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m353_capacity_status TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 5 }}
		set_variable = {{ name = zg361_mg_admin_capacity_refunded value = 1 }}
	}}
	else = {{ debug_log = "ZG361MG: stale or duplicate admin-capacity refund ignored" }}
}}

# 354 — fairness is recomputed from raw delivered/appeal/overturn/exit counts.
# Long-term trust is awarded only when disclosure and remediation are both true.
zg361_mg_m354_audit_fairness_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 5 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 354, 5)} }}
		set_variable = {{ name = zg361_mg_fairness_delivered value = {{ value = var:zg361_mg_team_n max = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_appeals value = {{ value = 0 subtract = var:zg361_mg_team_appeal_overturn divide = 5 max = 0 }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_overturns value = var:zg361_mg_fairness_raw_appeals }}
		set_variable = {{ name = zg361_mg_fairness_raw_exits value = {{ value = var:zg361_mg_team_n subtract = {{ value = var:zg361_mg_team_retention divide = 2 }} max = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_healthy_exits value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_raw_appeal_rate value = {{ value = var:zg361_mg_fairness_raw_appeals divide = var:zg361_mg_fairness_delivered }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_overturn_rate value = 0 }}
		if = {{ limit = {{ var:zg361_mg_fairness_raw_appeals > 0 }} set_variable = {{ name = zg361_mg_fairness_raw_overturn_rate value = {{ value = var:zg361_mg_fairness_raw_overturns divide = var:zg361_mg_fairness_raw_appeals }} }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_healthy_exit_rate value = {{ value = var:zg361_mg_fairness_raw_healthy_exits divide = var:zg361_mg_fairness_raw_exits }} }}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_fairness_reported_appeal_rate }} }} set_variable = {{ name = zg361_mg_fairness_reported_appeal_rate value = var:zg361_mg_fairness_raw_appeal_rate }} }}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_fairness_reported_overturn_rate }} }} set_variable = {{ name = zg361_mg_fairness_reported_overturn_rate value = var:zg361_mg_fairness_raw_overturn_rate }} }}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_fairness_reported_healthy_exit_rate }} }} set_variable = {{ name = zg361_mg_fairness_reported_healthy_exit_rate value = var:zg361_mg_fairness_raw_healthy_exit_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gap_appeal value = {{ value = var:zg361_mg_fairness_reported_appeal_rate subtract = var:zg361_mg_fairness_raw_appeal_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gap_overturn value = {{ value = var:zg361_mg_fairness_reported_overturn_rate subtract = var:zg361_mg_fairness_raw_overturn_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gap_exit value = {{ value = var:zg361_mg_fairness_reported_healthy_exit_rate subtract = var:zg361_mg_fairness_raw_healthy_exit_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gaming value = 0 }}
		if = {{ limit = {{ OR = {{ NOT = {{ var:zg361_mg_fairness_gap_appeal = 0 }} NOT = {{ var:zg361_mg_fairness_gap_overturn = 0 }} NOT = {{ var:zg361_mg_fairness_gap_exit = 0 }} }} }} set_variable = {{ name = zg361_mg_fairness_gaming value = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_trust_delta value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_history_mapping_version value = var:zg361_mg_history_mapping_version }}
		if = {{ limit = {{ has_variable = zg361_mg_fairness_self_disclosed var:zg361_mg_fairness_self_disclosed = 1 has_variable = zg361_mg_fairness_remediation_completed var:zg361_mg_fairness_remediation_completed = 1 }} set_variable = {{ name = zg361_mg_fairness_trust_delta value = 5 }} change_variable = {{ name = zg361_mg_policy_trust add = 5 }} }}
		{receipt_call("AK", 354, 5)}
	}}
	else = {{ zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 354 }} }}
}}

zg361_mg_ak_stage_5_effect = {{
	zg361_mg_m353_charge_admin_capacity_effect = yes
	zg361_mg_m354_audit_fairness_effect = yes
	if = {{
		limit = {{ {receipt_current("AK", 353, 5)} {receipt_current("AK", 354, 5)} }}
		{transition_call("AK", 5)}
		if = {{
			limit = {{ var:zg361_case_ak_state = 6 var:zg361_case_ak_active = 0 }}
			if = {{ limit = {{ is_ai = no }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.220 DAYS = 1 }} }}
			else = {{ debug_log = "ZG361MG: eligible AI policy governance completed silently" }}
		}}
	}}
}}

# Exception deadline resolution is independent of the now-closed AK case.  The
# exact owner/subject/cycle/case/state/expiry token prevents old events from
# expiring or renewing a successor policy.
zg361_mg_resolve_exception_due_effect = {{
	if = {{
		limit = {{
			var:zg361_mg_exception_pending = 1
			var:zg361_mg_exception_state = 1
			var:zg361_mg_exception_owner = scope:zg361_mg_exception_ticket_owner
			var:zg361_mg_exception_subject = scope:zg361_mg_exception_ticket_subject
			var:zg361_mg_exception_cycle = scope:zg361_mg_exception_ticket_cycle
			var:zg361_mg_exception_case = scope:zg361_mg_exception_ticket_case
			var:zg361_mg_exception_state = scope:zg361_mg_exception_ticket_state
			var:zg361_mg_exception_expiry_year = scope:zg361_mg_exception_ticket_expiry
		}}
		if = {{
			limit = {{ var:zg361_mg_exception_new_evidence = 1 }}
			set_variable = {{ name = zg361_mg_exception_expiry_year value = {{ value = current_year add = 1 }} }}
			change_variable = {{ name = zg361_mg_exception_renewal_count add = 1 }}
			set_variable = {{ name = zg361_mg_exception_new_evidence value = 0 }}
		}}
		else = {{
			set_variable = {{ name = zg361_mg_exception_state value = 2 }}
			set_variable = {{ name = zg361_mg_exception_pending value = 0 }}
			set_variable = {{ name = zg361_mg_exception_default_restored value = 1 }}
		}}
	}}
	else = {{ debug_log = "ZG361MG: stale policy-exception deadline ignored" }}
}}
'''
    return generated(body)


def render_events() -> bytes:
    return generated(r'''
namespace = zg361mg

# F032-036 delayed stage tickets.  Every event binds owner, subject, cycle,
# case and expected state; stale copies are strict no-ops.
zg361mg.100 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_mg_f_ticket_owner
				exists = scope:zg361_mg_f_ticket_subject
				this = scope:zg361_mg_f_ticket_subject
				var:zg361_case_f_owner = scope:zg361_mg_f_ticket_owner
				var:zg361_case_f_subject = scope:zg361_mg_f_ticket_subject
				var:zg361_case_f_cycle_serial = scope:zg361_mg_f_ticket_cycle
				var:zg361_case_f_case_serial = scope:zg361_mg_f_ticket_case
				var:zg361_case_f_state = scope:zg361_mg_f_ticket_state
				var:zg361_case_f_state = 1
			}
			zg361_mg_m032_score_manager_effect = yes
		}
		else = { debug_log = "ZG361MG: stale F032 ticket ignored" }
	}
}

zg361mg.101 = {
	type = character_event hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_mg_f_ticket_owner exists = scope:zg361_mg_f_ticket_subject this = scope:zg361_mg_f_ticket_subject var:zg361_case_f_owner = scope:zg361_mg_f_ticket_owner var:zg361_case_f_subject = scope:zg361_mg_f_ticket_subject var:zg361_case_f_cycle_serial = scope:zg361_mg_f_ticket_cycle var:zg361_case_f_case_serial = scope:zg361_mg_f_ticket_case var:zg361_case_f_state = scope:zg361_mg_f_ticket_state var:zg361_case_f_state = 2 }
			zg361_mg_m033_reason_code_effect = yes
		}
		else = { debug_log = "ZG361MG: stale F033 ticket ignored" }
	}
}

zg361mg.102 = {
	type = character_event hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_mg_f_ticket_owner exists = scope:zg361_mg_f_ticket_subject this = scope:zg361_mg_f_ticket_subject var:zg361_case_f_owner = scope:zg361_mg_f_ticket_owner var:zg361_case_f_subject = scope:zg361_mg_f_ticket_subject var:zg361_case_f_cycle_serial = scope:zg361_mg_f_ticket_cycle var:zg361_case_f_case_serial = scope:zg361_mg_f_ticket_case var:zg361_case_f_state = scope:zg361_mg_f_ticket_state var:zg361_case_f_state = 3 }
			zg361_mg_m034_freeze_nine_box_effect = yes
		}
		else = { debug_log = "ZG361MG: stale F034 ticket ignored" }
	}
}

zg361mg.103 = {
	type = character_event hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_mg_f_ticket_owner exists = scope:zg361_mg_f_ticket_subject this = scope:zg361_mg_f_ticket_subject var:zg361_case_f_owner = scope:zg361_mg_f_ticket_owner var:zg361_case_f_subject = scope:zg361_mg_f_ticket_subject var:zg361_case_f_cycle_serial = scope:zg361_mg_f_ticket_cycle var:zg361_case_f_case_serial = scope:zg361_mg_f_ticket_case var:zg361_case_f_state = scope:zg361_mg_f_ticket_state var:zg361_case_f_state = 4 }
			zg361_mg_m036_append_decade_log_effect = yes
		}
		else = { debug_log = "ZG361MG: stale F036 ticket ignored" }
	}
}

# Player-visible manager result.  The score is in the event body, rather than
# forcing the player to infer it from a grade or a separate scoreboard tab.
zg361mg.120 = {
	type = character_event
	theme = vassal
	title = zg361mg.120.t
	desc = zg361mg.120.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_mg_f_ticket_owner
		exists = scope:zg361_mg_f_ticket_subject
		this = scope:zg361_mg_f_ticket_subject
		var:zg361_case_f_owner = scope:zg361_mg_f_ticket_owner
		var:zg361_case_f_cycle_serial = scope:zg361_mg_f_ticket_cycle
		var:zg361_case_f_case_serial = scope:zg361_mg_f_ticket_case
		var:zg361_case_f_state = 5
		var:zg361_case_f_active = 0
	}
	option = { name = zg361mg.120.a }
}

# AK345-354 five-stage tickets.
zg361mg.200 = {
	type = character_event hidden = yes
	immediate = {
		if = { limit = { exists = scope:zg361_mg_ak_ticket_owner exists = scope:zg361_mg_ak_ticket_subject this = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner var:zg361_case_ak_subject = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case var:zg361_case_ak_state = scope:zg361_mg_ak_ticket_state var:zg361_case_ak_state = 1 } zg361_mg_ak_stage_1_effect = yes }
		else = { debug_log = "ZG361MG: stale AK drafted ticket ignored" }
	}
}

zg361mg.201 = {
	type = character_event hidden = yes
	immediate = {
		if = { limit = { exists = scope:zg361_mg_ak_ticket_owner exists = scope:zg361_mg_ak_ticket_subject this = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner var:zg361_case_ak_subject = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case var:zg361_case_ak_state = scope:zg361_mg_ak_ticket_state var:zg361_case_ak_state = 2 } zg361_mg_ak_stage_2_effect = yes }
		else = { debug_log = "ZG361MG: stale AK piloted ticket ignored" }
	}
}

zg361mg.202 = {
	type = character_event hidden = yes
	immediate = {
		if = { limit = { exists = scope:zg361_mg_ak_ticket_owner exists = scope:zg361_mg_ak_ticket_subject this = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner var:zg361_case_ak_subject = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case var:zg361_case_ak_state = scope:zg361_mg_ak_ticket_state var:zg361_case_ak_state = 3 } zg361_mg_ak_stage_3_effect = yes }
		else = { debug_log = "ZG361MG: stale AK effective ticket ignored" }
	}
}

zg361mg.203 = {
	type = character_event hidden = yes
	immediate = {
		if = { limit = { exists = scope:zg361_mg_ak_ticket_owner exists = scope:zg361_mg_ak_ticket_subject this = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner var:zg361_case_ak_subject = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case var:zg361_case_ak_state = scope:zg361_mg_ak_ticket_state var:zg361_case_ak_state = 4 } zg361_mg_ak_stage_4_effect = yes }
		else = { debug_log = "ZG361MG: stale AK exception-audited ticket ignored" }
	}
}

zg361mg.204 = {
	type = character_event hidden = yes
	immediate = {
		if = { limit = { exists = scope:zg361_mg_ak_ticket_owner exists = scope:zg361_mg_ak_ticket_subject this = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner var:zg361_case_ak_subject = scope:zg361_mg_ak_ticket_subject var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case var:zg361_case_ak_state = scope:zg361_mg_ak_ticket_state var:zg361_case_ak_state = 5 } zg361_mg_ak_stage_5_effect = yes }
		else = { debug_log = "ZG361MG: stale AK measured ticket ignored" }
	}
}

zg361mg.220 = {
	type = character_event
	theme = stewardship
	title = zg361mg.220.t
	desc = zg361mg.220.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_mg_ak_ticket_owner
		exists = scope:zg361_mg_ak_ticket_subject
		this = scope:zg361_mg_ak_ticket_subject
		var:zg361_case_ak_owner = scope:zg361_mg_ak_ticket_owner
		var:zg361_case_ak_cycle_serial = scope:zg361_mg_ak_ticket_cycle
		var:zg361_case_ak_case_serial = scope:zg361_mg_ak_ticket_case
		var:zg361_case_ak_state = 6
		var:zg361_case_ak_active = 0
	}
	option = { name = zg361mg.220.a }
}

zg361mg.250 = {
	type = character_event hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_mg_exception_ticket_owner
				exists = scope:zg361_mg_exception_ticket_subject
				this = scope:zg361_mg_exception_ticket_subject
				has_variable = zg361_mg_exception_pending
				var:zg361_mg_exception_pending = 1
				var:zg361_mg_exception_owner = scope:zg361_mg_exception_ticket_owner
				var:zg361_mg_exception_subject = scope:zg361_mg_exception_ticket_subject
				var:zg361_mg_exception_cycle = scope:zg361_mg_exception_ticket_cycle
				var:zg361_mg_exception_case = scope:zg361_mg_exception_ticket_case
				var:zg361_mg_exception_state = scope:zg361_mg_exception_ticket_state
				var:zg361_mg_exception_expiry_year = scope:zg361_mg_exception_ticket_expiry
			}
			zg361_mg_resolve_exception_due_effect = yes
		}
		else = { debug_log = "ZG361MG: stale policy-exception deadline ignored" }
	}
}
''')


ENGLISH_LOC = r'''
l_english:
 zg361mg.120.t:0 "Your Manager Performance Record"
 zg361mg.120.desc:0 "Your direct superior has closed the manager review. Manager score: #high [ROOT.MakeScope.Var('zg361_mg_manager_score').GetValue|0]#!. Frozen source cycle: [ROOT.MakeScope.Var('zg361_mg_snapshot_source_serial').GetValue|0]; current review cycle: [ROOT.MakeScope.Var('zg361_case_f_cycle_serial').GetValue|0]. Profile reason total: [ROOT.MakeScope.Var('zg361_mg_reason_total').GetValue|0]. Nine-box code: [ROOT.MakeScope.Var('zg361_mg_nine_box_code').GetValue|0] (0 means that a second frozen history does not yet exist). A Jingcha refusal, when present, is shown in the frozen breakdown as exactly -50 and is consumed only once."
 zg361mg.120.a:0 "I have read the score and its reasons."
 zg361mg.220.t:0 "Performance-System Operations Report"
 zg361mg.220.desc:0 "The policy cycle has migrated. Remaining governance capacity: #high [ROOT.MakeScope.Var('zg361_mg_admin_capacity_remaining').GetValue|0]#!. Audit sample: [ROOT.MakeScope.Var('zg361_mg_audit_sample_n').GetValue|0]; deterministic fingerprint: [ROOT.MakeScope.Var('zg361_mg_audit_selection_fingerprint').GetValue|0]. Fairness-gaming flag: [ROOT.MakeScope.Var('zg361_mg_fairness_gaming').GetValue|0]."
 zg361mg.220.a:0 "Archive the receipts."
'''


CHINESE_LOC = r'''
l_simp_chinese:
 zg361mg.120.t:0 "你的管理者绩效案卷"
 zg361mg.120.desc:0 "直属上司已经完成对你的管理者考核。你的管理绩效分是：#high [ROOT.MakeScope.Var('zg361_mg_manager_score').GetValue|0]#!。团队事实来源轮次：[ROOT.MakeScope.Var('zg361_mg_snapshot_source_serial').GetValue|0]；本次上级考核轮次：[ROOT.MakeScope.Var('zg361_case_f_cycle_serial').GetValue|0]。画像理由合计：[ROOT.MakeScope.Var('zg361_mg_reason_total').GetValue|0]；九宫格编码：[ROOT.MakeScope.Var('zg361_mg_nine_box_code').GetValue|0]（0 表示尚缺第二轮冻结历史，不会伪造分类）。若你拒办京察，案卷会明确列出一次性的 -50，而不是让你猜自己到底为什么被打低。"
 zg361mg.120.a:0 "分数和理由都写明白了，我已阅。"
 zg361mg.220.t:0 "绩效制度运营报告"
 zg361mg.220.desc:0 "本轮制度运营已经迁移归档。剩余治理工时：#high [ROOT.MakeScope.Var('zg361_mg_admin_capacity_remaining').GetValue|0]#!；审计样本数：[ROOT.MakeScope.Var('zg361_mg_audit_sample_n').GetValue|0]；可复算抽样指纹：[ROOT.MakeScope.Var('zg361_mg_audit_selection_fingerprint').GetValue|0]；公平指标刷数标记：[ROOT.MakeScope.Var('zg361_mg_fairness_gaming').GetValue|0]。"
 zg361mg.220.a:0 "收好收据，下轮再校准。"
'''


def render_english_localization() -> bytes:
    return localized(ENGLISH_LOC)


def render_simp_chinese_localization() -> bytes:
    return localized(CHINESE_LOC)


def render_english_placeholder_localization(language: str) -> bytes:
    return localized(ENGLISH_LOC.replace("l_english:", f"l_{language}:", 1))


def outputs() -> dict[Path, bytes]:
    validate_bindings()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_manager_governance_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_manager_governance_runtime_events.txt": render_events(),
        MOD_ROOT / "localization" / "english" / "zg361_manager_governance_l_english.yml": render_english_localization(),
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_manager_governance_l_simp_chinese.yml": render_simp_chinese_localization(),
    }
    for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_manager_governance_l_{language}.yml"
        ] = render_english_placeholder_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    if args.check:
        if stale:
            print("RED: stale manager/governance generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: manager/governance generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} manager/governance runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
