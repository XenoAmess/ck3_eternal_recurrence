#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B1 cross-cycle performance-season kernel.

The generated CK3 files are intentionally isolated from the legacy settlement
effect.  Existing rewards, penalties and scoreboard publication remain the
single settlement implementation; this kernel supplies persistent rosters,
timed stages, peer records, shadow ratings and a common-superior quota barrier.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from zg361_b1_runtime_data import B1_BINDINGS, validate_b1_bindings


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_b1_runtime.py\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def render_peer_slot_consumer(slot: int) -> str:
    """Render one sealed peer slot without relying on dynamic variable names."""

    reciprocal_checks = "\n".join(
        f'''\t\t\t\t\tAND = {{
\t\t\t\t\t\thas_variable = zg361_b1_peer_slot_{other}_evaluator
\t\t\t\t\t\thas_variable = zg361_b1_peer_slot_{other}_raw
\t\t\t\t\t\ttrigger_if = {{
\t\t\t\t\t\t\tlimit = {{
\t\t\t\t\t\t\t\thas_variable = zg361_b1_peer_slot_{other}_evaluator
\t\t\t\t\t\t\t\thas_variable = zg361_b1_peer_slot_{other}_raw
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\tvar:zg361_b1_peer_slot_{other}_raw > 0
\t\t\t\t\t\t\tvar:zg361_b1_peer_slot_{other}_evaluator = scope:zg361_b1_peer_subject
\t\t\t\t\t\t}}
\t\t\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t\t\t}}'''
        for other in (1, 2, 3)
    )
    return f'''zg361_b1_consume_peer_slot_{slot}_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = zg361_b1_case_owner
\t\t\thas_variable = zg361_b1_case_subject
\t\t\thas_variable = zg361_b1_cycle_serial
\t\t\thas_variable = zg361_b1_case_serial
\t\t\thas_variable = zg361_b1_case_state
\t\t\thas_variable = zg361_b1_case_active
\t\t\tvar:zg361_b1_peer_slot_{slot}_filled = 1
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_evaluator
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_subject
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_cycle
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_id
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_kind
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_owner
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_cycle
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_case
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_attacker
\t\t\thas_variable = zg361_b1_peer_slot_{slot}_common_task_defender
\t\t\tvar:zg361_b1_case_owner = root
\t\t\tvar:zg361_b1_case_subject = this
\t\t\tvar:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
\t\t\tvar:zg361_b1_case_serial = root.var:zg361_b1_case_serial
\t\t\tvar:zg361_b1_case_state = 3
\t\t\tvar:zg361_b1_case_active = 1
\t\t\tvar:zg361_b1_roster_included = 1
\t\t\tvar:zg361_b1_peer_slot_{slot}_subject = this
\t\t\tvar:zg361_b1_peer_slot_{slot}_cycle = var:zg361_b1_cycle_serial
\t\t\tvar:zg361_b1_peer_slot_{slot}_common_task_kind = 1
\t\t\tvar:zg361_b1_peer_slot_{slot}_common_task_owner = root
\t\t\tvar:zg361_b1_peer_slot_{slot}_common_task_cycle = var:zg361_b1_cycle_serial
\t\t\tvar:zg361_b1_peer_slot_{slot}_common_task_case = var:zg361_b1_case_serial
\t\t}}
\t\tsave_scope_as = zg361_b1_peer_subject
\t\tset_variable = {{ name = zg361_b1_peer_slot_{slot}_reciprocal value = 0 }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = zg361_b1_peer_slot_{slot}_evaluator
\t\t\t\tvar:zg361_b1_peer_slot_{slot}_raw > 0
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{
\t\t\t\t\t\tOR = {{
{reciprocal_checks}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\tset_variable = {{ name = zg361_b1_peer_slot_{slot}_reciprocal value = 1 }}
\t\t\t\tset_variable = {{ name = zg361_b1_peer_reciprocity_risk value = 1 }}
\t\t\t\tset_variable = {{
\t\t\t\t\tname = zg361_b1_peer_slot_{slot}_weight
\t\t\t\t\tvalue = {{ value = var:zg361_b1_peer_slot_{slot}_weight multiply = 0.5 floor = yes min = 10 }}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_b1_peer_slot_{slot}_adjusted value = var:zg361_b1_peer_slot_{slot}_raw }}
\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{
\t\t\tif = {{
\t\t\t\tlimit = {{ NOT = {{ has_variable = zg361_b1_evaluator_profile_id }} }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_profile_id value = scope:zg361_b1_peer_subject.var:zg361_b1_case_serial }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_n value = 0 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_sum value = 0 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_sum_squares value = 0 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_mean value = 0 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_variance value = 0 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_overturn_n value = 0 }}
\t\t\t}}
\t\t\tchange_variable = {{ name = zg361_b1_evaluator_history_n add = 1 }}
\t\t\tchange_variable = {{ name = zg361_b1_evaluator_history_sum add = scope:zg361_b1_peer_subject.var:zg361_b1_peer_slot_{slot}_raw }}
\t\t\tset_variable = {{
\t\t\t\tname = zg361_b1_evaluator_history_current_square
\t\t\t\tvalue = {{ value = scope:zg361_b1_peer_subject.var:zg361_b1_peer_slot_{slot}_raw multiply = scope:zg361_b1_peer_subject.var:zg361_b1_peer_slot_{slot}_raw }}
\t\t\t}}
\t\t\tchange_variable = {{ name = zg361_b1_evaluator_history_sum_squares add = var:zg361_b1_evaluator_history_current_square }}
\t\t\tset_variable = {{ name = zg361_b1_evaluator_history_mean value = {{ value = var:zg361_b1_evaluator_history_sum divide = var:zg361_b1_evaluator_history_n }} }}
\t\t\tset_variable = {{
\t\t\t\tname = zg361_b1_evaluator_history_variance
\t\t\t\tvalue = {{
\t\t\t\t\tvalue = var:zg361_b1_evaluator_history_sum_squares
\t\t\t\t\tdivide = var:zg361_b1_evaluator_history_n
\t\t\t\t\tsubtract = {{ value = var:zg361_b1_evaluator_history_mean multiply = var:zg361_b1_evaluator_history_mean }}
\t\t\t\t\tmin = 0
\t\t\t\t}}
\t\t\t}}
\t\t\tset_variable = {{ name = zg361_b1_evaluator_statistics_cycle value = scope:zg361_b1_peer_subject.var:zg361_b1_cycle_serial }}
\t\t\tscope:zg361_b1_peer_subject = {{
\t\t\t\tset_variable = {{
\t\t\t\t\tname = zg361_b1_peer_slot_{slot}_adjusted
\t\t\t\t\tvalue = {{ value = var:zg361_b1_peer_slot_{slot}_raw subtract = {{ value = prev.var:zg361_b1_evaluator_history_mean multiply = 0.2 }} max = 10 min = -15 }}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\tchange_variable = {{ name = zg361_b1_peer_n add = 1 }}
\t\tchange_variable = {{ name = zg361_b1_peer_raw_sum add = var:zg361_b1_peer_slot_{slot}_raw }}
\t\tchange_variable = {{ name = zg361_b1_peer_adjusted_sum add = var:zg361_b1_peer_slot_{slot}_adjusted }}
\t\tchange_variable = {{ name = zg361_b1_peer_credit_total add = var:zg361_b1_peer_slot_{slot}_weight }}
\t\tset_variable = {{
\t\t\tname = zg361_b1_peer_slot_{slot}_weighted
\t\t\tvalue = {{ value = var:zg361_b1_peer_slot_{slot}_adjusted multiply = var:zg361_b1_peer_slot_{slot}_weight }}
\t\t}}
\t\tchange_variable = {{ name = zg361_b1_peer_weighted_sum add = var:zg361_b1_peer_slot_{slot}_weighted }}
\t\tset_variable = {{
\t\t\tname = zg361_b1_peer_slot_{slot}_square
\t\t\tvalue = {{ value = var:zg361_b1_peer_slot_{slot}_raw multiply = var:zg361_b1_peer_slot_{slot}_raw }}
\t\t}}
\t\tchange_variable = {{ name = zg361_b1_peer_sum_squares add = var:zg361_b1_peer_slot_{slot}_square }}
\t\tset_variable = {{ name = zg361_b1_peer_slot_{slot}_sealed_serial value = var:zg361_b1_case_serial }}
\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{
\t\t\tif = {{
\t\t\t\tlimit = {{ NOT = {{ has_variable = zg361_b1_evaluator_credit }} }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_credit value = 100 }}
\t\t\t\tset_variable = {{ name = zg361_b1_evaluator_sample_n value = 0 }}
\t\t\t}}
\t\t\tchange_variable = {{ name = zg361_b1_evaluator_sample_n add = 1 }}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_b1_peer_slot_{slot}_raw >= 0 }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_b1_evidence_late >= 0 }}
\t\t\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{ change_variable = {{ name = zg361_b1_evaluator_credit add = 2 }} }}
\t\t\t}}
\t\t\telse = {{ var:zg361_b1_peer_slot_{slot}_evaluator = {{ change_variable = {{ name = zg361_b1_evaluator_credit add = -5 }} }} }}
\t\t}}
\t\telse = {{
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_b1_evidence_late < 0 }}
\t\t\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{ change_variable = {{ name = zg361_b1_evaluator_credit add = 2 }} }}
\t\t\t}}
\t\t\telse = {{ var:zg361_b1_peer_slot_{slot}_evaluator = {{ change_variable = {{ name = zg361_b1_evaluator_credit add = -5 }} }} }}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_b1_peer_slot_{slot}_reciprocal = 1 }}
\t\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{ change_variable = {{ name = zg361_b1_evaluator_credit add = -3 }} }}
\t\t}}
\t\tvar:zg361_b1_peer_slot_{slot}_evaluator = {{
\t\t\tset_variable = {{
\t\t\t\tname = zg361_b1_evaluator_credit
\t\t\t\tvalue = {{ value = var:zg361_b1_evaluator_credit max = 125 min = 25 }}
\t\t\t}}
\t\t}}
\t}}
}}'''


def render_appeal_slot_consumer(slot: int) -> str:
    """Render one idempotent appeal-overturn evaluator-credit consumer."""

    return f'''zg361_b1_apply_appeal_credit_slot_{slot}_effect = {{
	if = {{
		limit = {{
			var:zg361_b1_result_adapter_peer_slot_{slot}_filled = 1
			has_variable = zg361_b1_result_adapter_peer_slot_{slot}_evaluator
			has_variable = zg361_b1_result_adapter_peer_slot_{slot}_subject
			has_variable = zg361_b1_result_adapter_peer_slot_{slot}_cycle
			has_variable = zg361_b1_result_adapter_peer_slot_{slot}_raw
			has_variable = zg361_b1_result_adapter_peer_slot_{slot}_sealed_serial
			var:zg361_b1_result_adapter_peer_slot_{slot}_subject = this
			var:zg361_b1_result_adapter_peer_slot_{slot}_cycle = var:zg361_b1_result_adapter_b1_cycle
			var:zg361_b1_result_adapter_peer_slot_{slot}_sealed_serial = var:zg361_b1_result_adapter_b1_case
		}}
		set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_appeal_credit_delta value = 0 }}
		if = {{
			limit = {{ var:zg361_b1_result_adapter_peer_slot_{slot}_raw < 0 }}
			var:zg361_b1_result_adapter_peer_slot_{slot}_evaluator = {{
				if = {{ limit = {{ NOT = {{ has_variable = zg361_b1_evaluator_credit }} }} set_variable = {{ name = zg361_b1_evaluator_credit value = 100 }} }}
				if = {{ limit = {{ NOT = {{ has_variable = zg361_b1_evaluator_overturn_n }} }} set_variable = {{ name = zg361_b1_evaluator_overturn_n value = 0 }} }}
				change_variable = {{ name = zg361_b1_evaluator_overturn_n add = 1 }}
				change_variable = {{ name = zg361_b1_evaluator_credit add = -5 }}
				if = {{
					limit = {{ has_variable = zg361_b1_evaluator_history_n var:zg361_b1_evaluator_history_n >= 1 }}
					set_variable = {{ name = zg361_b1_evaluator_overturn_rate value = {{ value = var:zg361_b1_evaluator_overturn_n divide = var:zg361_b1_evaluator_history_n }} }}
				}}
				set_variable = {{ name = zg361_b1_evaluator_overturn_last_subject value = prev }}
				set_variable = {{ name = zg361_b1_evaluator_overturn_last_cycle value = prev.var:zg361_b1_result_adapter_b1_cycle }}
				set_variable = {{ name = zg361_b1_evaluator_overturn_last_case value = prev.var:zg361_b1_result_adapter_b1_case }}
				set_variable = {{ name = zg361_b1_evaluator_credit value = {{ value = var:zg361_b1_evaluator_credit max = 125 min = 25 }} }}
			}}
			set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_appeal_credit_delta value = -5 }}
		}}
		else_if = {{
			limit = {{ var:zg361_b1_result_adapter_m008_mode = 1 }}
			var:zg361_b1_result_adapter_peer_slot_{slot}_evaluator = {{
				if = {{ limit = {{ NOT = {{ has_variable = zg361_b1_evaluator_credit }} }} set_variable = {{ name = zg361_b1_evaluator_credit value = 100 }} }}
				change_variable = {{ name = zg361_b1_evaluator_credit add = 2 }}
				set_variable = {{ name = zg361_b1_evaluator_credit value = {{ value = var:zg361_b1_evaluator_credit max = 125 min = 25 }} }}
			}}
			set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_appeal_credit_delta value = 2 }}
		}}
		set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_appeal_credit_receipt value = var:zg361_result_case_serial }}
	}}
}}'''


def render_result_adapter_peer_slots() -> str:
    """Freeze the published peer identities independently of the next cycle."""

    return "\n".join(
        f'''						set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_filled value = 0 }}
						if = {{
							limit = {{
								var:zg361_b1_peer_slot_{slot}_filled = 1
								has_variable = zg361_b1_peer_slot_{slot}_evaluator
								has_variable = zg361_b1_peer_slot_{slot}_subject
								has_variable = zg361_b1_peer_slot_{slot}_cycle
								has_variable = zg361_b1_peer_slot_{slot}_raw
								has_variable = zg361_b1_peer_slot_{slot}_sealed_serial
							}}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_filled value = 1 }}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_evaluator value = var:zg361_b1_peer_slot_{slot}_evaluator }}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_subject value = var:zg361_b1_peer_slot_{slot}_subject }}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_cycle value = var:zg361_b1_peer_slot_{slot}_cycle }}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_raw value = var:zg361_b1_peer_slot_{slot}_raw }}
							set_variable = {{ name = zg361_b1_result_adapter_peer_slot_{slot}_sealed_serial value = var:zg361_b1_peer_slot_{slot}_sealed_serial }}
						}}'''
        for slot in (1, 2, 3)
    )


def render_policy_freeze_blocks() -> str:
    """Render frozen 001-013 modes and one-shot DEFER debt receipts."""

    blocks: list[str] = []
    for mechanism_id in range(1, 14):
        key = f"{mechanism_id:03d}"
        blocks.append(
            f'''\tset_variable = {{ name = zg361_b1_m{key}_mode value = 1 }}
\tif = {{
\t\tlimit = {{ has_variable = zg361_mechanism_{key}_choice }}
\t\tset_variable = {{ name = zg361_b1_m{key}_mode value = var:zg361_mechanism_{key}_choice }}
\t}}
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_b1_m{key}_mode = 3
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = zg361_b1_m{key}_policy_debt_serial }}
\t\t\t\tNOT = {{ var:zg361_b1_m{key}_policy_debt_serial = var:zg361_b1_case_serial }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = zg361_b1_m{key}_policy_debt_serial value = var:zg361_b1_case_serial }}
\t\tchange_variable = {{ name = zg361_b1_policy_debt_cycle_n add = 1 }}
\t\tchange_variable = {{ name = zg361_b1_policy_debt_open_n add = 1 }}
\t\tset_variable = {{ name = zg361_b1_policy_debt_due_year value = {{ value = current_year add = 1 }} }}
\t}}'''
        )
    return "\n".join(blocks)


def render_stage_s_policy_freeze_blocks() -> str:
    """Render the frozen A/B/C routes for the stage-S review mechanisms.

    Mechanism 139 owns a persistent cross-cycle debt and is intentionally not
    part of this list.  The other ten choices are immutable for the lifetime of
    the manager case; route C creates one policy-debt receipt but no domain
    object for the corresponding mechanism.
    """

    blocks: list[str] = []
    for mechanism_id in (135, 136, 137, 138, 140, 141, 142, 143, 144, 145):
        key = f"{mechanism_id:03d}"
        blocks.append(
            f'''\tset_variable = {{ name = zg361_b1_m{key}_mode value = 1 }}
\tif = {{
\t\tlimit = {{ has_variable = zg361_mechanism_{key}_choice }}
\t\tset_variable = {{ name = zg361_b1_m{key}_mode value = var:zg361_mechanism_{key}_choice }}
\t}}
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_b1_m{key}_mode = 3
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = zg361_b1_m{key}_policy_debt_serial }}
\t\t\t\tNOT = {{ var:zg361_b1_m{key}_policy_debt_serial = var:zg361_b1_case_serial }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = zg361_b1_m{key}_policy_debt_serial value = var:zg361_b1_case_serial }}
\t\tchange_variable = {{ name = zg361_b1_policy_debt_cycle_n add = 1 }}
\t\tchange_variable = {{ name = zg361_b1_policy_debt_open_n add = 1 }}
\t\tset_variable = {{ name = zg361_b1_policy_debt_due_year value = {{ value = current_year add = 1 }} }}
\t}}
\telse = {{ remove_variable = zg361_b1_m{key}_policy_debt_serial }}'''
        )
    return "\n".join(blocks)


def render_effects() -> bytes:
    bindings = "\n".join(
        f"# {row.mechanism_id:03d} {row.stage} {row.scope}: "
        f"{row.meaningful_write} -> {row.consumer}"
        for row in B1_BINDINGS
    )
    peer_slot_consumers = "\n\n".join(
        render_peer_slot_consumer(slot) for slot in (1, 2, 3)
    )
    appeal_slot_consumers = "\n\n".join(
        render_appeal_slot_consumer(slot) for slot in (1, 2, 3)
    )
    body = r'''
# ZhongGuo 361 B1 — persistent performance season and pooled quota kernel
# State: 1 targets, 2 midcycle, 3 peer/evidence, 4 facts, 5 shadow,
#        6 quota ready, 7 calibration, 8 published.

# Freeze one of four role/function families.  The same taxonomy is consumed by
# subject scorecards and by the common-superior small-team pool, so a team can
# never become "same function" merely because both managers are governors.
zg361_b1_classify_function_effect = {
	set_variable = { name = zg361_b1_function_code value = 4 } # management/fallback
	if = {
		limit = {
			OR = {
				vassal_contract_has_flag = celestial_military_appointment
				has_council_position = councillor_marshal
			}
		}
		set_variable = { name = zg361_b1_function_code value = 2 } # military
	}
	else_if = {
		limit = { has_council_position = councillor_steward }
		set_variable = { name = zg361_b1_function_code value = 3 } # finance
	}
	else_if = {
		limit = { is_governor = yes }
		set_variable = { name = zg361_b1_function_code value = 1 } # local governance
	}
}

# Policy choices are copied to cycle-owned variables before any subject case is
# opened.  Choice C is DEFER for 001-013: it creates no domain object and adds
# exactly one manager policy debt for the next review, rather than masquerading
# as a conservative business route.
zg361_b1_freeze_001_013_policy_effect = {
	set_variable = { name = zg361_b1_policy_debt_cycle_n value = 0 }
	if = {
		limit = { NOT = { has_variable = zg361_b1_policy_debt_open_n } }
		set_variable = { name = zg361_b1_policy_debt_open_n value = 0 }
	}
	set_variable = { name = zg361_b1_policy_next_review_serial value = { value = var:zg361_b1_cycle_serial add = 1 } }
__POLICY_FREEZE_BLOCKS__
}

# Stage-S choices are frozen beside the manager case.  No downstream effect
# reads the mutable policy-card variables again, which keeps delayed deadlines,
# transfers and publication tied to the route that opened the case.
zg361_b1_freeze_135_145_policy_effect = {
__STAGE_S_POLICY_FREEZE_BLOCKS__
}

# Manager liabilities are only consumed when that manager later appears as a
# subject in a real superior-owned review.  The bounded malus feeds the same
# calibration score used by both local and common-pool quota ranking.
zg361_b1_consume_manager_liabilities_as_subject_effect = {
	set_variable = { name = zg361_b1_manager_liability_adjustment value = 0 }
	set_variable = { name = zg361_b1_manager_liability_consumed_n value = 0 }
	if = {
		limit = {
			has_variable = zg361_b1_policy_debt_open_n
			has_variable = zg361_b1_policy_debt_due_year
			var:zg361_b1_policy_debt_open_n >= 1
			var:zg361_b1_policy_debt_due_year <= current_year
		}
		set_variable = { name = zg361_b1_manager_liability_consumed_n value = var:zg361_b1_policy_debt_open_n }
		change_variable = { name = zg361_b1_manager_liability_adjustment add = { value = var:zg361_b1_policy_debt_open_n multiply = -2 } }
		set_variable = { name = zg361_b1_policy_debt_open_n value = 0 }
		set_variable = { name = zg361_b1_policy_debt_settled_year value = current_year }
	}
	if = {
		limit = {
			has_variable = zg361_b1_feedback_debt_open_n
			has_variable = zg361_b1_feedback_debt_due_year
			var:zg361_b1_feedback_debt_open_n >= 1
			var:zg361_b1_feedback_debt_due_year <= current_year
		}
		change_variable = { name = zg361_b1_manager_liability_consumed_n add = var:zg361_b1_feedback_debt_open_n }
		change_variable = { name = zg361_b1_manager_liability_adjustment add = { value = var:zg361_b1_feedback_debt_open_n multiply = -5 } }
		set_variable = { name = zg361_b1_feedback_debt_open_n value = 0 }
		set_variable = { name = zg361_b1_feedback_debt_settled_year value = current_year }
	}
	if = {
		limit = {
			has_variable = zg361_b1_protection_debt_state
			has_variable = zg361_b1_protection_debt_due_year
			var:zg361_b1_protection_debt_state = 1
			var:zg361_b1_protection_debt_due_year <= current_year
		}
		change_variable = { name = zg361_b1_manager_liability_consumed_n add = 1 }
		change_variable = { name = zg361_b1_manager_liability_adjustment add = -5 }
		set_variable = { name = zg361_b1_protection_debt_state value = 2 }
		set_variable = { name = zg361_b1_protection_debt_settled_year value = current_year }
	}
	if = {
		limit = {
			has_variable = zg361_b1_dissent_judgment_balance
			has_variable = zg361_b1_dissent_judgment_due_year
			var:zg361_b1_dissent_judgment_balance < 0
			var:zg361_b1_dissent_judgment_due_year <= current_year
		}
		set_variable = { name = zg361_b1_dissent_judgment_liability value = { value = var:zg361_b1_dissent_judgment_balance multiply = 2 min = -6 } }
		change_variable = { name = zg361_b1_manager_liability_consumed_n add = { value = var:zg361_b1_dissent_judgment_balance multiply = -1 } }
		change_variable = { name = zg361_b1_manager_liability_adjustment add = var:zg361_b1_dissent_judgment_liability }
		set_variable = { name = zg361_b1_dissent_judgment_balance value = 0 }
		set_variable = { name = zg361_b1_dissent_judgment_settled_year value = current_year }
	}
	set_variable = {
		name = zg361_b1_manager_liability_adjustment
		value = { value = var:zg361_b1_manager_liability_adjustment max = 0 min = -20 }
	}
}

zg361_b1_initialize_subject_case_effect = {
	set_variable = { name = zg361_b1_case_owner value = root }
	set_variable = { name = zg361_b1_case_subject value = this }
	set_variable = { name = zg361_b1_cycle_serial value = root.var:zg361_b1_cycle_serial }
	set_variable = { name = zg361_b1_case_serial value = root.var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_case_state value = 1 }
	set_variable = { name = zg361_b1_case_active value = 1 }
	set_variable = { name = zg361_b1_case_revision value = 1 }
	set_variable = { name = zg361_b1_case_timeline_serial value = 1 }
	set_variable = { name = zg361_b1_case_feedback_revision value = 1 }
	set_variable = { name = zg361_b1_case_last_operation value = 0 }
	set_variable = { name = zg361_b1_case_last_choice value = 0 }
	set_variable = { name = zg361_b1_case_last_hook value = 0 }
	set_variable = { name = zg361_b1_case_open_year value = current_year }
	# Completion receipts are case-local.  Clear the previous cycle before an
	# A/B route can create a new object; C keeps only its manager policy debt.
	remove_variable = zg361_b1_m001_receipt_serial
	remove_variable = zg361_b1_m002_receipt_serial
	remove_variable = zg361_b1_m003_receipt_serial
	remove_variable = zg361_b1_m004_receipt_serial
	remove_variable = zg361_b1_m005_receipt_serial
	remove_variable = zg361_b1_m006_receipt_serial
	remove_variable = zg361_b1_m007_receipt_serial
	remove_variable = zg361_b1_m008_receipt_serial
	remove_variable = zg361_b1_m009_receipt_serial
	remove_variable = zg361_b1_m010_receipt_serial
	remove_variable = zg361_b1_m011_receipt_serial
	remove_variable = zg361_b1_m012_receipt_serial
	remove_variable = zg361_b1_m013_receipt_serial
	remove_variable = zg361_b1_m135_receipt_serial
	remove_variable = zg361_b1_m137_receipt_serial
	remove_variable = zg361_b1_m138_receipt_serial
	remove_variable = zg361_b1_m140_receipt_serial
	remove_variable = zg361_b1_m142_receipt_serial
	remove_variable = zg361_b1_m143_receipt_serial
	remove_variable = zg361_b1_m144_receipt_serial
	remove_variable = zg361_b1_m145_receipt_serial
	set_variable = { name = zg361_b1_previous_band_order value = 0 }
	if = {
		limit = { has_variable = zg361_b1_band_order }
		set_variable = { name = zg361_b1_previous_band_order value = var:zg361_b1_band_order }
	}
	set_variable = { name = zg361_b1_previous_band_order_use_mode value = 0 }
	if = {
		limit = { has_variable = zg361_b1_band_order_use_mode }
		set_variable = { name = zg361_b1_previous_band_order_use_mode value = var:zg361_b1_band_order_use_mode }
	}
	set_variable = { name = zg361_b1_previous_band_opportunity_weight value = 0 }
	if = {
		limit = { has_variable = zg361_b1_band_opportunity_weight }
		set_variable = { name = zg361_b1_previous_band_opportunity_weight value = var:zg361_b1_band_opportunity_weight }
	}
	set_variable = { name = zg361_b1_previous_band_self_appeal_evidence value = 0 }
	if = {
		limit = { has_variable = zg361_b1_band_self_appeal_evidence }
		set_variable = { name = zg361_b1_previous_band_self_appeal_evidence value = var:zg361_b1_band_self_appeal_evidence }
	}
	set_variable = { name = zg361_b1_previous_band_object_available value = 0 }
	if = {
		limit = {
			var:zg361_b1_band_order_object_available = 1
			var:zg361_b1_band_order_object_subject = this
			var:zg361_b1_band_order_object_state = 1
		}
		set_variable = { name = zg361_b1_previous_band_object_available value = 1 }
		set_variable = { name = zg361_b1_previous_band_object_id value = var:zg361_b1_band_order_object_id }
		set_variable = { name = zg361_b1_previous_band_object_owner value = var:zg361_b1_band_order_object_owner }
		set_variable = { name = zg361_b1_previous_band_object_subject value = this }
		set_variable = { name = zg361_b1_previous_band_object_cycle value = var:zg361_b1_band_order_object_cycle }
		set_variable = { name = zg361_b1_previous_band_object_case value = var:zg361_b1_band_order_object_case }
		set_variable = { name = zg361_b1_previous_band_object_state value = 1 }
	}
	set_variable = { name = zg361_b1_previous_final_grade value = 0 }
	if = {
		limit = { has_variable = zg361_b1_final_grade }
		set_variable = { name = zg361_b1_previous_final_grade value = var:zg361_b1_final_grade }
	}
	set_variable = { name = zg361_b1_roster_included value = 1 }
	set_variable = { name = zg361_b1_roster_amendment value = 0 }
	set_variable = { name = zg361_b1_roster_lock_version value = 1 }
	set_variable = { name = zg361_b1_roster_change_version value = 0 }
	set_variable = { name = zg361_b1_roster_change_before value = 1 }
	set_variable = { name = zg361_b1_roster_change_after value = 1 }
	set_variable = { name = zg361_b1_roster_change_reason value = 0 }
	set_variable = { name = zg361_b1_roster_change_year value = 0 }
	set_variable = { name = zg361_b1_roster_reopen_required value = 0 }
	remove_variable = zg361_b1_roster_change_actor
	remove_variable = zg361_b1_roster_change_approver
	set_variable = { name = zg361_b1_leaver_route value = 0 }
	set_variable = { name = zg361_b1_goal_available value = 1 }
	set_variable = { name = zg361_b1_goal_contract_id value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_goal_version value = 1 }
	set_variable = { name = zg361_b1_goal_direction value = 1 }
	set_variable = { name = zg361_b1_goal_strength value = 100 }
	set_variable = { name = zg361_b1_goal_weight value = 20 }
	set_variable = { name = zg361_b1_goal_grade_cap value = 3 }
	set_variable = { name = zg361_b1_goal_deadline_year value = current_year }
	set_variable = { name = zg361_b1_goal_baseline value = zg361_kpi_value }
	set_variable = { name = zg361_b1_goal_target value = { value = var:zg361_b1_goal_baseline add = 10 } }
	set_variable = { name = zg361_b1_goal_completion_delta value = 0 }
	set_variable = { name = zg361_b1_goal_score_adjustment value = 0 }
	set_variable = { name = zg361_b1_role_scorecard_available value = 1 }
	set_variable = { name = zg361_b1_role_scorecard_version value = 1 }
	set_variable = { name = zg361_b1_role_scorecard_id value = var:zg361_b1_case_serial }
	zg361_b1_classify_function_effect = yes
	set_variable = { name = zg361_b1_role_code value = var:zg361_b1_function_code }
	set_variable = { name = zg361_b1_role_weight_governance value = 15 }
	set_variable = { name = zg361_b1_role_weight_capability value = 15 }
	set_variable = { name = zg361_b1_role_weight_growth value = 15 }
	set_variable = { name = zg361_b1_role_weight_superior value = 10 }
	set_variable = { name = zg361_b1_role_weight_values value = 15 }
	set_variable = { name = zg361_b1_role_weight_collaboration value = 10 }
	set_variable = { name = zg361_b1_role_weight_jingcha value = 10 }
	set_variable = { name = zg361_b1_role_weight_organization value = 10 }
	if = {
		limit = { var:zg361_b1_role_code = 1 }
		set_variable = { name = zg361_b1_role_weight_governance value = 30 }
		set_variable = { name = zg361_b1_role_weight_capability value = 10 }
		set_variable = { name = zg361_b1_role_weight_growth value = 10 }
		set_variable = { name = zg361_b1_role_weight_values value = 10 }
	}
	else_if = {
		limit = { var:zg361_b1_role_code = 2 }
		set_variable = { name = zg361_b1_role_weight_capability value = 30 }
		set_variable = { name = zg361_b1_role_weight_governance value = 10 }
		set_variable = { name = zg361_b1_role_weight_values value = 20 }
		set_variable = { name = zg361_b1_role_weight_growth value = 10 }
		set_variable = { name = zg361_b1_role_weight_collaboration value = 5 }
		set_variable = { name = zg361_b1_role_weight_organization value = 5 }
	}
	else_if = {
		limit = { var:zg361_b1_role_code = 3 }
		set_variable = { name = zg361_b1_role_weight_growth value = 25 }
		set_variable = { name = zg361_b1_role_weight_governance value = 20 }
		set_variable = { name = zg361_b1_role_weight_capability value = 10 }
		set_variable = { name = zg361_b1_role_weight_superior value = 5 }
		set_variable = { name = zg361_b1_role_weight_collaboration value = 5 }
	}
	else = {
		set_variable = { name = zg361_b1_role_weight_superior value = 20 }
		set_variable = { name = zg361_b1_role_weight_collaboration value = 20 }
		set_variable = { name = zg361_b1_role_weight_capability value = 10 }
		set_variable = { name = zg361_b1_role_weight_governance value = 10 }
		set_variable = { name = zg361_b1_role_weight_growth value = 10 }
		set_variable = { name = zg361_b1_role_weight_values value = 10 }
	}
	set_variable = { name = zg361_b1_role_weighted_score value = 0 }
	set_variable = { name = zg361_b1_role_score_adjustment value = 0 }
	set_variable = { name = zg361_b1_role_bias_risk value = 0 }
	set_variable = { name = zg361_b1_next_role_code value = var:zg361_b1_role_code }
	set_variable = { name = zg361_b1_baseline_available value = 1 }
	set_variable = { name = zg361_b1_baseline_id value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_baseline_raw value = 0 }
	if = {
		limit = { government_has_flag = government_has_merit }
		set_variable = { name = zg361_b1_baseline_raw value = merit_level }
	}
	set_variable = { name = zg361_b1_baseline_adjusted value = var:zg361_b1_baseline_raw }
	set_variable = { name = zg361_b1_baseline_source value = 1 }
	set_variable = { name = zg361_b1_baseline_start_development value = capital_county.development_level }
	set_variable = { name = zg361_b1_baseline_start_control value = capital_county.county_control }
	set_variable = { name = zg361_b1_baseline_start_gold value = gold }
	set_variable = { name = zg361_b1_baseline_start_war value = 0 }
	if = {
		limit = { is_at_war = yes }
		set_variable = { name = zg361_b1_baseline_start_war value = 1 }
	}
	set_variable = { name = zg361_b1_baseline_start_resources value = domain_size }
	set_variable = { name = zg361_b1_baseline_end_development value = 0 }
	set_variable = { name = zg361_b1_baseline_end_control value = 0 }
	set_variable = { name = zg361_b1_baseline_end_gold value = 0 }
	set_variable = { name = zg361_b1_baseline_end_war value = 0 }
	set_variable = { name = zg361_b1_baseline_end_resources value = 0 }
	set_variable = { name = zg361_b1_baseline_state_delta value = 0 }
	set_variable = { name = zg361_b1_baseline_bias_risk value = 0 }
	set_variable = { name = zg361_b1_difficulty_reason value = 5 }
	set_variable = { name = zg361_b1_difficulty_cap value = 5 }
	set_variable = { name = zg361_b1_difficulty_adjustment value = 0 }
	if = {
		limit = { is_at_war = yes }
		set_variable = { name = zg361_b1_difficulty_reason value = 1 }
		set_variable = { name = zg361_b1_difficulty_adjustment value = 5 }
	}
	else_if = {
		limit = { is_governor = yes }
		set_variable = { name = zg361_b1_difficulty_reason value = 2 }
		set_variable = { name = zg361_b1_difficulty_adjustment value = 2 }
	}
	set_variable = { name = zg361_b1_difficulty_improvement value = 0 }
	set_variable = { name = zg361_b1_difficulty_score_adjustment value = 0 }
	zg361_b1_consume_manager_liabilities_as_subject_effect = yes
	set_variable = { name = zg361_b1_target_rebased value = 0 }
	set_variable = { name = zg361_b1_checkin_available value = 1 }
	remove_variable = zg361_b1_checkin_id
	set_variable = { name = zg361_b1_checkin_planned_year value = current_year }
	set_variable = { name = zg361_b1_checkin_completed_year value = 0 }
	set_variable = { name = zg361_b1_crisis_id value = 0 }
	set_variable = { name = zg361_b1_crisis_type value = 0 }
	set_variable = { name = zg361_b1_rebaseline_used value = 0 }
	set_variable = { name = zg361_b1_goal_old_version value = 0 }
	set_variable = { name = zg361_b1_goal_new_version value = 0 }
	set_variable = { name = zg361_b1_goal_old_target value = 0 }
	set_variable = { name = zg361_b1_goal_new_target value = 0 }
	set_variable = { name = zg361_b1_support_obligation value = 0 }
	set_variable = { name = zg361_b1_catchup_plan value = 0 }
	set_variable = { name = zg361_b1_midcycle_warning value = 0 }
	set_variable = { name = zg361_b1_feedback_ack value = 0 }
	set_variable = { name = zg361_b1_feedback_objection value = 0 }
	set_variable = { name = zg361_b1_opportunity_grant value = 0 }
	set_variable = { name = zg361_b1_opportunity_project_available value = 0 }
	set_variable = { name = zg361_b1_opportunity_project_state value = 0 }
	set_variable = { name = zg361_b1_opportunity_evidence_adjustment value = 0 }
	remove_variable = zg361_b1_opportunity_project_owner
	remove_variable = zg361_b1_opportunity_project_subject
	set_variable = { name = zg361_b1_self_review_available value = 1 }
	remove_variable = zg361_b1_self_review_id
	remove_variable = zg361_b1_self_evidence_id
	remove_variable = zg361_b1_self_evidence_category
	remove_variable = zg361_b1_self_submitted_year
	set_variable = { name = zg361_b1_self_band value = 0 }
	set_variable = { name = zg361_b1_self_manager_response value = 0 }
	set_variable = { name = zg361_b1_self_submitted value = 0 }
	set_variable = { name = zg361_b1_self_score value = 0 }
	set_variable = { name = zg361_b1_self_choice value = 0 }
	set_variable = { name = zg361_b1_self_gap value = 0 }
	set_variable = { name = zg361_b1_self_visibility_adjustment value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_filled value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_filled value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_filled value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_raw value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_raw value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_raw value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_weight value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_weight value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_weight value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_submitted_year value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_submitted_year value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_submitted_year value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_reciprocal value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_reciprocal value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_reciprocal value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_sealed_serial value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_sealed_serial value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_sealed_serial value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_performance value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_performance value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_performance value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_collaboration value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_collaboration value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_collaboration value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_values value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_values value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_values value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_adjusted value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_adjusted value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_adjusted value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_example_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_example_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_example_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_common_task_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_common_task_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_common_task_id value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_common_task_kind value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_common_task_kind value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_common_task_kind value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_common_task_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_common_task_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_common_task_cycle value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_common_task_case value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_common_task_case value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_common_task_case value = 0 }
	remove_variable = zg361_b1_peer_slot_1_common_task_owner
	remove_variable = zg361_b1_peer_slot_2_common_task_owner
	remove_variable = zg361_b1_peer_slot_3_common_task_owner
	remove_variable = zg361_b1_peer_slot_1_common_task_attacker
	remove_variable = zg361_b1_peer_slot_2_common_task_attacker
	remove_variable = zg361_b1_peer_slot_3_common_task_attacker
	remove_variable = zg361_b1_peer_slot_1_common_task_defender
	remove_variable = zg361_b1_peer_slot_2_common_task_defender
	remove_variable = zg361_b1_peer_slot_3_common_task_defender
	remove_variable = zg361_b1_peer_slot_1_evaluator
	remove_variable = zg361_b1_peer_slot_2_evaluator
	remove_variable = zg361_b1_peer_slot_3_evaluator
	remove_variable = zg361_b1_peer_slot_1_subject
	remove_variable = zg361_b1_peer_slot_2_subject
	remove_variable = zg361_b1_peer_slot_3_subject
	set_variable = { name = zg361_b1_peer_used value = 0 }
	set_variable = { name = zg361_b1_peer_cap value = 3 }
	set_variable = { name = zg361_b1_peer_fatigue value = 0 }
	set_variable = { name = zg361_b1_peer_over_cap value = 0 }
	set_variable = { name = zg361_b1_peer_submission_weight value = 100 }
	set_variable = { name = zg361_b1_peer_n value = 0 }
	set_variable = { name = zg361_b1_peer_raw_sum value = 0 }
	set_variable = { name = zg361_b1_peer_weighted_sum value = 0 }
	set_variable = { name = zg361_b1_peer_credit_total value = 0 }
	set_variable = { name = zg361_b1_peer_sum_squares value = 0 }
	set_variable = { name = zg361_b1_peer_adjusted_sum value = 0 }
	set_variable = { name = zg361_b1_peer_mean value = 0 }
	set_variable = { name = zg361_b1_peer_variance value = 0 }
	set_variable = { name = zg361_b1_peer_normalized_score value = 0 }
	set_variable = { name = zg361_b1_peer_shape value = 0 }
	set_variable = { name = zg361_b1_peer_reciprocity_risk value = 0 }
	set_variable = { name = zg361_b1_peer_calibration_adjustment value = 0 }
	set_variable = { name = zg361_b1_peer_sealed value = 0 }
	set_variable = { name = zg361_b1_peer_timely_n value = 0 }
	set_variable = { name = zg361_b1_peer_author_count value = 0 }
	set_variable = { name = zg361_b1_peer_anonymous_threshold value = 3 }
	set_variable = { name = zg361_b1_peer_public_summary_available value = 0 }
	set_variable = { name = zg361_b1_peer_manager_only value = 1 }
	set_variable = { name = zg361_b1_peer_total_weight_cap value = 15 }
	set_variable = { name = zg361_b1_peer_effective_weight_percent value = 0 }
	if = {
		limit = { NOT = { has_variable = zg361_b1_evaluator_credit } }
		set_variable = { name = zg361_b1_evaluator_credit value = 100 }
		set_variable = { name = zg361_b1_evaluator_sample_n value = 0 }
	}
	set_variable = { name = zg361_b1_evidence_early value = zg361_kpi_value }
	set_variable = { name = zg361_b1_evidence_mid value = 0 }
	set_variable = { name = zg361_b1_evidence_late value = 0 }
	set_variable = { name = zg361_b1_evidence_early_weight value = 20 }
	set_variable = { name = zg361_b1_evidence_mid_weight value = 30 }
	set_variable = { name = zg361_b1_evidence_late_weight value = 50 }
	set_variable = { name = zg361_b1_evidence_early_weighted value = 0 }
	set_variable = { name = zg361_b1_evidence_mid_weighted value = 0 }
	set_variable = { name = zg361_b1_evidence_late_weighted value = 0 }
	set_variable = { name = zg361_b1_evidence_window_score value = 0 }
	set_variable = { name = zg361_b1_evidence_window_adjustment value = 0 }
	set_variable = { name = zg361_b1_evidence_late_frozen value = 0 }
	set_variable = { name = zg361_b1_evidence_sheet_available value = 0 }
	remove_variable = zg361_b1_evidence_sheet_id
	set_variable = { name = zg361_b1_evidence_incomplete value = 0 }
	set_variable = { name = zg361_b1_evidence_sum_check value = 0 }
	set_variable = { name = zg361_b1_evidence_governance value = 0 }
	set_variable = { name = zg361_b1_evidence_capability value = 0 }
	set_variable = { name = zg361_b1_evidence_growth value = 0 }
	set_variable = { name = zg361_b1_evidence_superior value = 0 }
	set_variable = { name = zg361_b1_evidence_values value = 0 }
	set_variable = { name = zg361_b1_evidence_collaboration value = 0 }
	set_variable = { name = zg361_b1_evidence_jingcha value = 0 }
	set_variable = { name = zg361_b1_evidence_organization value = 0 }
	set_variable = { name = zg361_b1_fact_sheet_serial value = 0 }
	set_variable = { name = zg361_b1_fact_closed_year value = 0 }
	set_variable = { name = zg361_b1_shadow_grade value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_delta value = 0 }
	set_variable = { name = zg361_b1_shadow_response_state value = 0 }
	set_variable = { name = zg361_b1_shadow_notice_year value = 0 }
	set_variable = { name = zg361_b1_shadow_response_year value = 0 }
	set_variable = { name = zg361_b1_shadow_object_available value = 0 }
	remove_variable = zg361_b1_shadow_object_id
	remove_variable = zg361_b1_shadow_object_owner
	remove_variable = zg361_b1_shadow_object_subject
	set_variable = { name = zg361_b1_shadow_object_cycle value = 0 }
	set_variable = { name = zg361_b1_shadow_object_case value = 0 }
	set_variable = { name = zg361_b1_shadow_object_state value = 0 }
	set_variable = { name = zg361_b1_shadow_object_nonfinal value = 0 }
	set_variable = { name = zg361_b1_shadow_deadline_year value = 0 }
	set_variable = { name = zg361_b1_shadow_gap_mask value = 0 }
	set_variable = { name = zg361_b1_shadow_gap_magnitude value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_object_available value = 0 }
	remove_variable = zg361_b1_shadow_evidence_object_id
	remove_variable = zg361_b1_shadow_evidence_object_owner
	remove_variable = zg361_b1_shadow_evidence_object_subject
	set_variable = { name = zg361_b1_shadow_evidence_object_cycle value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_object_case value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_object_state value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_revision value = 0 }
	set_variable = { name = zg361_b1_shadow_new_evidence value = 0 }
	set_variable = { name = zg361_b1_shadow_new_evidence_baseline_score value = 0 }
	set_variable = { name = zg361_b1_shadow_new_evidence_observed_score value = 0 }
	set_variable = { name = zg361_b1_shadow_new_evidence_source value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_consumed value = 0 }
	set_variable = { name = zg361_b1_shadow_reveal_state value = 0 }
	set_variable = { name = zg361_b1_shadow_final_drop value = 0 }
	set_variable = { name = zg361_b1_shadow_drop_explained value = 0 }
	set_variable = { name = zg361_b1_calibration_score value = 0 }
	set_variable = { name = zg361_b1_calibration_score_before_shadow value = 0 }
	set_variable = { name = zg361_b1_quota_snapshot value = 0 }
	set_variable = { name = zg361_b1_forced_down value = 0 }
	set_variable = { name = zg361_b1_final_grade value = 0 }
	set_variable = { name = zg361_b1_final_reason value = 0 }
	set_variable = { name = zg361_b1_feedback_debt value = 0 }
	set_variable = { name = zg361_b1_feedback_debt_appeal_weight value = 0 }
	set_variable = { name = zg361_b1_feedback_debt_self_safe_evidence value = 0 }
	set_variable = { name = zg361_b1_band_order value = 0 }
	set_variable = { name = zg361_b1_band_order_use_mode value = 0 }
	set_variable = { name = zg361_b1_band_opportunity_weight value = 0 }
	set_variable = { name = zg361_b1_band_order_object_available value = 0 }
	set_variable = { name = zg361_b1_band_order_object_state value = 0 }
	remove_variable = zg361_b1_band_order_object_owner
	remove_variable = zg361_b1_band_order_object_subject
	set_variable = { name = zg361_b1_band_public_order_available value = 0 }
	set_variable = { name = zg361_b1_band_private_order_available value = 0 }
	set_variable = { name = zg361_b1_band_self_appeal_evidence value = 0 }
	set_variable = { name = zg361_b1_band_bonus_adjustment value = 0 }
	set_variable = { name = zg361_b1_coaching_priority value = 0 }
	set_variable = { name = zg361_b1_band_order_blackbox_risk value = 0 }
	set_variable = { name = zg361_b1_conflict_case_state value = 0 }
	set_variable = { name = zg361_b1_recusal_active value = 0 }
	set_variable = { name = zg361_b1_recusal_relation value = 0 }
	set_variable = { name = zg361_b1_recusal_replacement_kind value = 0 }
	set_variable = { name = zg361_b1_recusal_pre_grade value = 0 }
	set_variable = { name = zg361_b1_recusal_post_recommendation value = 0 }
	set_variable = { name = zg361_b1_recusal_review_state value = 0 }
	set_variable = { name = zg361_b1_recusal_review_base_score value = 0 }
	set_variable = { name = zg361_b1_recusal_review_score value = 0 }
	set_variable = { name = zg361_b1_recusal_review_recommended_grade value = 0 }
	set_variable = { name = zg361_b1_recusal_review_pre_grade value = 0 }
	set_variable = { name = zg361_b1_recusal_review_post_grade value = 0 }
	set_variable = { name = zg361_b1_recusal_review_applied value = 0 }
	set_variable = { name = zg361_b1_recusal_review_quota_blocked value = 0 }
	set_variable = { name = zg361_b1_recusal_review_actor_kind value = 0 }
	set_variable = { name = zg361_b1_recusal_review_receipt_state value = 0 }
	set_variable = { name = zg361_b1_appeal_risk value = 0 }
	set_variable = { name = zg361_b1_grade_write_acl_frozen value = 0 }
	set_variable = { name = zg361_b1_grade_write_authority value = 1 }
	set_variable = { name = zg361_b1_grade_write_denied_n value = 0 }
	set_variable = { name = zg361_b1_recusal_post_grade value = 0 }
	set_variable = { name = zg361_b1_recusal_lock_match value = 0 }
	set_variable = { name = zg361_b1_grade_write_reviewer value = root }
	remove_variable = zg361_b1_conflict_case_id
	remove_variable = zg361_b1_recusal_actor
	remove_variable = zg361_b1_recusal_reviewer
	remove_variable = zg361_b1_recusal_review_actor
	remove_variable = zg361_b1_recusal_review_partner
	remove_variable = zg361_b1_recusal_review_receipt_owner
	remove_variable = zg361_b1_recusal_review_receipt_subject
	remove_variable = zg361_b1_recusal_review_receipt_cycle
	remove_variable = zg361_b1_recusal_review_receipt_case
	remove_variable = zg361_b1_bottom_protected
	remove_variable = zg361_b1_bottom_carrier
	set_variable = { name = zg361_b1_disclosure_policy_available value = 1 }
	set_variable = { name = zg361_b1_disclosure_policy_id value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_disclosure_self_mode value = 3 }
	set_variable = { name = zg361_b1_disclosure_team_mode value = 2 }
	set_variable = { name = zg361_b1_disclosure_evaluator_identity_mode value = 1 }
	set_variable = { name = zg361_b1_disclosure_blackbox_risk value = 0 }
	# Consume independent #142/#143 next-cycle evidence objects before current
	# case initialization clears any per-cycle projection fields.  The full
	# five-tuple prevents one mechanism or one manager from consuming the other.
	set_variable = { name = zg361_b1_pending_carried_adjustment value = 0 }
	if = {
		limit = {
			has_variable = zg361_b1_pending_next_cycle_object_owner
			has_variable = zg361_b1_pending_next_cycle_object_subject
			has_variable = zg361_b1_pending_next_cycle_object_cycle
			has_variable = zg361_b1_pending_next_cycle_object_case
			has_variable = zg361_b1_pending_next_cycle_object_state
			var:zg361_b1_pending_next_cycle_object_available = 1
			var:zg361_b1_pending_next_cycle_object_owner = root
			var:zg361_b1_pending_next_cycle_object_subject = this
			var:zg361_b1_pending_next_cycle_object_state = 1
			var:zg361_b1_pending_next_cycle_object_cycle = root.var:zg361_b1_cycle_serial
			var:zg361_b1_pending_next_cycle_due = var:zg361_b1_pending_next_cycle_object_cycle
		}
		set_variable = { name = zg361_b1_pending_carried_adjustment value = var:zg361_b1_pending_next_cycle_delta }
		set_variable = { name = zg361_b1_pending_next_cycle_object_state value = 2 }
		set_variable = { name = zg361_b1_pending_next_cycle_consumed_cycle value = root.var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_pending_next_cycle_consumption_receipt_case value = var:zg361_b1_pending_next_cycle_object_case }
	}
	set_variable = { name = zg361_b1_reopen_carried_adjustment value = 0 }
	if = {
		limit = {
			has_variable = zg361_b1_reopen_next_cycle_object_owner
			has_variable = zg361_b1_reopen_next_cycle_object_subject
			has_variable = zg361_b1_reopen_next_cycle_object_cycle
			has_variable = zg361_b1_reopen_next_cycle_object_case
			has_variable = zg361_b1_reopen_next_cycle_object_state
			var:zg361_b1_reopen_next_cycle_object_available = 1
			var:zg361_b1_reopen_next_cycle_object_owner = root
			var:zg361_b1_reopen_next_cycle_object_subject = this
			var:zg361_b1_reopen_next_cycle_object_state = 1
			var:zg361_b1_reopen_next_cycle_object_cycle = root.var:zg361_b1_cycle_serial
			var:zg361_b1_reopen_next_cycle_due = var:zg361_b1_reopen_next_cycle_object_cycle
		}
		set_variable = { name = zg361_b1_reopen_carried_adjustment value = var:zg361_b1_reopen_next_cycle_delta }
		set_variable = { name = zg361_b1_reopen_next_cycle_object_state value = 2 }
		set_variable = { name = zg361_b1_reopen_next_cycle_consumed_cycle value = root.var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_reopen_next_cycle_consumption_receipt_case value = var:zg361_b1_reopen_next_cycle_object_case }
	}
	set_variable = { name = zg361_b1_reopen_serial value = 0 }
	set_variable = { name = zg361_b1_pending_milestone value = 0 }
	set_variable = { name = zg361_b1_pending_state value = 0 }
	set_variable = { name = zg361_b1_pending_object_available value = 0 }
	set_variable = { name = zg361_b1_pending_object_state value = 0 }
	remove_variable = zg361_b1_pending_object_owner
	remove_variable = zg361_b1_pending_object_subject
	set_variable = { name = zg361_b1_pending_hold_serial value = 0 }
	set_variable = { name = zg361_b1_pending_resolution value = 0 }
	set_variable = { name = zg361_b1_pending_reward_paid value = 0 }
	set_variable = { name = zg361_b1_pending_reward_due value = 0 }
	set_variable = { name = zg361_b1_pending_observation_recorded value = 0 }
	set_variable = { name = zg361_b1_pending_observed_score value = 0 }
	set_variable = { name = zg361_b1_pending_target_score value = 0 }
	remove_variable = zg361_b1_pending_open_date
	set_variable = { name = zg361_b1_pending_deadline_days value = 0 }
	remove_variable = zg361_b1_pending_fallback_subject
	remove_variable = zg361_b1_pending_reserved_for_subject
	set_variable = { name = zg361_b1_pending_reservation_state value = 0 }
	set_variable = { name = zg361_b1_pending_partial_publish_state value = 0 }
	set_variable = { name = zg361_b1_pending_provisional_revision value = 0 }
	set_variable = { name = zg361_b1_pending_provisional_status value = 0 }
	set_variable = { name = zg361_b1_pending_provisional_grade value = 0 }
	set_variable = { name = zg361_b1_pending_provisional_held_band value = 0 }
	set_variable = { name = zg361_b1_pending_provisional_fallback_band value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_available value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_marker value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_milestone value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_deadline_cycle value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_current_final_unchanged value = 0 }
	set_variable = { name = zg361_b1_pending_self_safe_next_cycle_evidence value = 0 }
	set_variable = { name = zg361_b1_pending_projection_route value = 0 }
	set_variable = { name = zg361_b1_pending_late_to_next_cycle value = 0 }
	set_variable = { name = zg361_b1_pending_deferred_projection_state value = 0 }
	# #143 owns two distinct subject-local projection objects.  They deliberately
	# do not reuse the batch/probe or next-cycle business tuples: the projection
	# tuple binds exactly one published subject/cycle while its visible payload
	# remains limited to result/reason (A) or evidence/target-cycle (B).
	set_variable = { name = zg361_b1_reopen_self_a_available value = 0 }
	remove_variable = zg361_b1_reopen_self_a_owner
	remove_variable = zg361_b1_reopen_self_a_subject
	set_variable = { name = zg361_b1_reopen_self_a_cycle value = 0 }
	set_variable = { name = zg361_b1_reopen_self_a_case value = 0 }
	set_variable = { name = zg361_b1_reopen_self_a_state value = 0 }
	set_variable = { name = zg361_b1_reopen_self_a_result value = 0 }
	set_variable = { name = zg361_b1_reopen_self_a_reason value = 0 }
	set_variable = { name = zg361_b1_reopen_self_b_available value = 0 }
	remove_variable = zg361_b1_reopen_self_b_owner
	remove_variable = zg361_b1_reopen_self_b_subject
	set_variable = { name = zg361_b1_reopen_self_b_cycle value = 0 }
	set_variable = { name = zg361_b1_reopen_self_b_case value = 0 }
	set_variable = { name = zg361_b1_reopen_self_b_state value = 0 }
	set_variable = { name = zg361_b1_reopen_self_b_next_cycle_evidence value = 0 }
	set_variable = { name = zg361_b1_reopen_self_b_target_cycle value = 0 }
	set_variable = { name = zg361_b1_reopen_observation_recorded value = 0 }
	set_variable = { name = zg361_b1_reopen_observed_score value = 0 }
	set_variable = { name = zg361_b1_post_cutoff_event_id value = 0 }
	set_variable = { name = zg361_b1_post_cutoff_event_sign value = 0 }
	set_variable = { name = zg361_b1_post_cutoff_event_magnitude value = 0 }
	set_variable = { name = zg361_b1_post_cutoff_event_state value = 0 }
	set_variable = { name = zg361_b1_post_cutoff_visible_notice value = 0 }
	set_variable = { name = zg361_b1_attention_seat value = 0 }
	set_variable = { name = zg361_b1_attention_bound value = 0 }
	set_variable = { name = zg361_b1_attention_consumed value = 0 }
	set_variable = { name = zg361_b1_attention_displaced value = 0 }
	set_variable = { name = zg361_b1_agenda_order value = 0 }
	set_variable = { name = zg361_b1_agenda_mode value = 0 }
	set_variable = { name = zg361_b1_agenda_remaining_top value = 0 }
	set_variable = { name = zg361_b1_agenda_remaining_middle value = 0 }
	set_variable = { name = zg361_b1_agenda_remaining_bottom value = 0 }
	set_variable = { name = zg361_b1_agenda_tail_pressure value = 0 }
	set_variable = { name = zg361_b1_must_review_state value = 0 }
	set_variable = { name = zg361_b1_must_review_object_available value = 0 }
	set_variable = { name = zg361_b1_must_review_object_state value = 0 }
	remove_variable = zg361_b1_must_review_object_owner
	remove_variable = zg361_b1_must_review_object_subject
	set_variable = { name = zg361_b1_must_review_judgment_result value = 0 }
	set_variable = { name = zg361_b1_must_review_direction value = 0 }
	set_variable = { name = zg361_b1_must_review_attention_consumed value = 0 }
	set_variable = { name = zg361_b1_must_review_swap_executed value = 0 }
	set_variable = { name = zg361_b1_must_review_subject_before value = 0 }
	set_variable = { name = zg361_b1_must_review_subject_after value = 0 }
	set_variable = { name = zg361_b1_must_review_conservation_valid value = 0 }
	remove_variable = zg361_b1_must_review_superior
	remove_variable = zg361_b1_must_review_manager
	remove_variable = zg361_b1_must_review_subject
	remove_variable = zg361_b1_must_review_swap_peer
	set_variable = { name = zg361_b1_dissent_state value = 0 }
	set_variable = { name = zg361_b1_dissent_object_available value = 0 }
	set_variable = { name = zg361_b1_dissent_object_state value = 0 }
	remove_variable = zg361_b1_dissent_object_owner
	remove_variable = zg361_b1_dissent_object_subject
	set_variable = { name = zg361_b1_consensus_object_available value = 0 }
	set_variable = { name = zg361_b1_consensus_state value = 0 }
	remove_variable = zg361_b1_consensus_owner
	remove_variable = zg361_b1_consensus_subject
	set_variable = { name = zg361_b1_dissent_reason_fact value = 0 }
	set_variable = { name = zg361_b1_dissent_recommendation value = 0 }
	set_variable = { name = zg361_b1_dissent_final_result value = 0 }
	set_variable = { name = zg361_b1_dissent_credit_delta value = 0 }
	set_variable = { name = zg361_b1_dissent_procedural_risk value = 0 }
	set_variable = { name = zg361_b1_dissent_self_safe_evidence value = 0 }
	remove_variable = zg361_b1_dissent_manager
	remove_variable = zg361_b1_dissent_subject
	remove_variable = zg361_b1_dissent_reviewer
	set_variable = { name = zg361_b1_huddle_assignment_available value = 0 }
	set_variable = { name = zg361_b1_huddle_assignment_state value = 0 }
	remove_variable = zg361_b1_huddle_assignment_owner
	remove_variable = zg361_b1_huddle_assignment_subject
	set_variable = { name = zg361_b1_agenda_item_object_available value = 0 }
	set_variable = { name = zg361_b1_agenda_item_state value = 0 }
	remove_variable = zg361_b1_agenda_item_owner
	remove_variable = zg361_b1_agenda_item_subject
	set_variable = { name = zg361_b1_agenda_item_cycle value = 0 }
	set_variable = { name = zg361_b1_agenda_item_case value = 0 }
	set_variable = { name = zg361_b1_agenda_strategic_flag value = 0 }
	set_variable = { name = zg361_b1_agenda_strategic_reason value = 0 }
	set_variable = { name = zg361_b1_reopen_object_available value = 0 }
	set_variable = { name = zg361_b1_reopen_object_state value = 0 }
	remove_variable = zg361_b1_reopen_object_owner
	remove_variable = zg361_b1_reopen_object_subject
	set_variable = { name = zg361_b1_reorg_object_available value = 0 }
	remove_variable = zg361_b1_reorg_object_owner
	remove_variable = zg361_b1_reorg_object_subject
	remove_variable = zg361_b1_reorg_object_cycle
	remove_variable = zg361_b1_reorg_object_case
	set_variable = { name = zg361_b1_reorg_object_state value = 0 }
	remove_variable = zg361_b1_reorg_quota_owner
	set_variable = { name = zg361_b1_reorg_route value = 0 }
	set_variable = { name = zg361_b1_reorg_service_days value = 0 }
	remove_variable = zg361_b1_reorg_old_manager
	remove_variable = zg361_b1_reorg_new_manager
	set_variable = { name = zg361_b1_late_evidence_delta value = 0 }
	set_variable = { name = zg361_b1_late_evidence_magnitude value = 0 }
	set_variable = { name = zg361_b1_newcomer_route value = 0 }
	set_variable = { name = zg361_b1_peer_use_mode value = root.var:zg361_b1_peer_use_mode }
	if = {
		limit = { var:zg361_b1_peer_use_mode = 0 }
		set_variable = { name = zg361_b1_peer_cap value = 0 }
	}
	remove_variable = zg361_pending_grade
	remove_variable = zg361_rank

	# Frozen policy cards select real B1 routes. Unconfigured managers use A.
	# C is a defer route: the manager debt was created once at cycle open, while
	# the subject receives no goal/check-in/scorecard/baseline/self/peer object.
	if = {
		limit = { root.var:zg361_b1_m002_mode = 2 }
		set_variable = { name = zg361_b1_goal_direction value = 2 }
		set_variable = { name = zg361_b1_goal_strength value = 120 }
		change_variable = { name = zg361_b1_goal_weight add = 10 }
		set_variable = { name = zg361_b1_goal_target value = { value = var:zg361_b1_goal_baseline add = 20 } }
	}
	else_if = {
		limit = { root.var:zg361_b1_m002_mode = 3 }
		set_variable = { name = zg361_b1_goal_available value = 0 }
		remove_variable = zg361_b1_goal_contract_id
		set_variable = { name = zg361_b1_goal_weight value = 0 }
		set_variable = { name = zg361_b1_goal_grade_cap value = 0 }
	}
	if = {
		limit = { root.var:zg361_b1_m003_mode = 3 }
		set_variable = { name = zg361_b1_checkin_available value = 0 }
		remove_variable = zg361_b1_checkin_id
		set_variable = { name = zg361_b1_support_obligation value = 0 }
	}
	if = {
		limit = { root.var:zg361_b1_m004_mode = 3 }
		set_variable = { name = zg361_b1_self_review_available value = 0 }
		remove_variable = zg361_b1_self_review_id
		remove_variable = zg361_b1_self_evidence_id
	}
	if = {
		limit = { root.var:zg361_b1_m005_mode = 2 }
		set_variable = { name = zg361_b1_role_bias_risk value = 1 }
		# B uses one common result scale; the frozen role remains visible but its
		# differentiated vector is replaced with an explicit near-equal 100-point
		# vector and a role-bias audit marker.
		set_variable = { name = zg361_b1_role_weight_governance value = 13 }
		set_variable = { name = zg361_b1_role_weight_capability value = 13 }
		set_variable = { name = zg361_b1_role_weight_growth value = 13 }
		set_variable = { name = zg361_b1_role_weight_superior value = 13 }
		set_variable = { name = zg361_b1_role_weight_values value = 12 }
		set_variable = { name = zg361_b1_role_weight_collaboration value = 12 }
		set_variable = { name = zg361_b1_role_weight_jingcha value = 12 }
		set_variable = { name = zg361_b1_role_weight_organization value = 12 }
	}
	else_if = {
		limit = { root.var:zg361_b1_m005_mode = 3 }
		set_variable = { name = zg361_b1_role_scorecard_available value = 0 }
		remove_variable = zg361_b1_role_scorecard_id
	}
	if = {
		limit = { root.var:zg361_b1_m006_mode = 2 }
		set_variable = { name = zg361_b1_difficulty_adjustment value = 0 }
		set_variable = { name = zg361_b1_difficulty_reason value = 6 }
		set_variable = { name = zg361_b1_baseline_bias_risk value = 1 }
	}
	else_if = {
		limit = { root.var:zg361_b1_m006_mode = 3 }
		set_variable = { name = zg361_b1_baseline_available value = 0 }
		remove_variable = zg361_b1_baseline_id
		set_variable = { name = zg361_b1_difficulty_adjustment value = 0 }
	}
	if = {
		limit = { root.var:zg361_b1_m007_mode = 2 }
		set_variable = { name = zg361_b1_peer_total_weight_cap value = 15 }
	}
	else_if = {
		limit = { root.var:zg361_b1_m007_mode = 3 }
		set_variable = { name = zg361_b1_peer_cap value = 0 }
	}
	if = {
		limit = { root.var:zg361_b1_m008_mode = 3 }
		set_variable = { name = zg361_b1_peer_use_mode value = 0 }
	}
	if = {
		limit = { root.var:zg361_b1_m013_mode = 2 }
		set_variable = { name = zg361_b1_disclosure_self_mode value = 1 }
		set_variable = { name = zg361_b1_disclosure_team_mode value = 0 }
		set_variable = { name = zg361_b1_disclosure_blackbox_risk value = 1 }
	}
	else_if = {
		limit = { root.var:zg361_b1_m013_mode = 3 }
		set_variable = { name = zg361_b1_disclosure_policy_available value = 0 }
		remove_variable = zg361_b1_disclosure_policy_id
		set_variable = { name = zg361_b1_disclosure_self_mode value = 0 }
		set_variable = { name = zg361_b1_disclosure_team_mode value = 0 }
		set_variable = { name = zg361_b1_disclosure_evaluator_identity_mode value = 0 }
	}
	if = {
		limit = { root = { has_variable = zg361_mechanism_047_choice var:zg361_mechanism_047_choice = 2 } }
		set_variable = { name = zg361_b1_evidence_early_weight value = 10 }
		set_variable = { name = zg361_b1_evidence_mid_weight value = 20 }
		set_variable = { name = zg361_b1_evidence_late_weight value = 70 }
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_prev_merit_level }
			root = { has_character_flag = zg361_review_baseline_initialized }
		}
		add_character_flag = zg361_newcomer_this_cycle
		set_variable = { name = zg361_b1_newcomer_route value = 1 }
	}
	else = { remove_character_flag = zg361_newcomer_this_cycle }
	# Route choice must run after newcomer detection; applying it against the
	# initialization value 0 would make every configured route a silent no-op.
	if = {
		limit = {
			var:zg361_b1_newcomer_route = 1
			root = { has_variable = zg361_mechanism_041_choice }
		}
		if = {
			limit = { root.var:zg361_mechanism_041_choice = 2 }
			set_variable = { name = zg361_b1_newcomer_route value = 3 }
			remove_character_flag = zg361_newcomer_this_cycle
		}
		else_if = {
			limit = { root.var:zg361_mechanism_041_choice = 3 }
			set_variable = { name = zg361_b1_newcomer_route value = 2 }
		}
	}

	if = { limit = { root.var:zg361_b1_m002_mode != 3 } set_variable = { name = zg361_b1_m002_receipt_serial value = var:zg361_b1_case_serial } }
	if = { limit = { root.var:zg361_b1_m005_mode != 3 } set_variable = { name = zg361_b1_m005_receipt_serial value = var:zg361_b1_case_serial } }
	if = { limit = { root.var:zg361_b1_m006_mode != 3 } set_variable = { name = zg361_b1_m006_receipt_serial value = var:zg361_b1_case_serial } }
	set_variable = { name = zg361_b1_m041_receipt_serial value = var:zg361_b1_case_serial }

	# Minimal shared-kernel integration. B1 keeps its established variable names,
	# while this one typed roster-lock receipt proves the five-field helper call
	# contract without delegating B1 stage ownership to the generic kernel.
	zg361_case_kernel_record_operation_effect = {
		OWNER_VAR = zg361_b1_case_owner
		SUBJECT_VAR = zg361_b1_case_subject
		CYCLE_VAR = zg361_b1_cycle_serial
		CASE_VAR = zg361_b1_case_serial
		STATE_VAR = zg361_b1_case_state
		ACTIVE_VAR = zg361_b1_case_active
		RECEIPT_OWNER_VAR = zg361_b1_roster_lock_receipt_owner
		RECEIPT_SUBJECT_VAR = zg361_b1_roster_lock_receipt_subject
		RECEIPT_CYCLE_VAR = zg361_b1_roster_lock_receipt_cycle
		RECEIPT_CASE_VAR = zg361_b1_roster_lock_receipt_case
		RECEIPT_STATE_VAR = zg361_b1_roster_lock_receipt_state
		RECEIPT_CHOICE_VAR = zg361_b1_roster_lock_receipt_choice
		LAST_OPERATION_VAR = zg361_b1_case_last_operation
		LAST_CHOICE_VAR = zg361_b1_case_last_choice
		REVISION_VAR = zg361_b1_case_revision
		TIMELINE_VAR = zg361_b1_case_timeline_serial
		FEEDBACK_VAR = zg361_b1_case_feedback_revision
		TICKET_OWNER = root
		TICKET_SUBJECT = this
		TICKET_CYCLE = root.var:zg361_b1_cycle_serial
		TICKET_CASE = root.var:zg361_b1_case_serial
		TICKET_STATE = 1
		OPERATION_ID = 39
		CHOICE = 1
	}
}

zg361_b1_open_cycle_effect = {
	if = {
		limit = {
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			NOT = { has_character_flag = zg361_b1_cycle_active }
			NOT = { has_character_flag = zg361_review_in_progress }
			trigger_if = {
				limit = { has_variable = zg361_b1_cycle_open_year }
				NOT = { var:zg361_b1_cycle_open_year = current_year }
			}
			trigger_else = { always = yes }
		}
		add_character_flag = zg361_b1_cycle_active
		if = {
			limit = { NOT = { has_variable = zg361_b1_cycle_serial } }
			set_variable = { name = zg361_b1_cycle_serial value = 0 }
		}
		if = {
			limit = { NOT = { has_variable = zg361_b1_case_serial } }
			set_variable = { name = zg361_b1_case_serial value = 0 }
		}
		change_variable = { name = zg361_b1_cycle_serial add = 1 }
		change_variable = { name = zg361_b1_case_serial add = 1 }
		set_variable = { name = zg361_b1_cycle_state value = 1 }
		set_variable = { name = zg361_b1_cycle_open_year value = current_year }
		remove_variable = zg361_b1_m009_receipt_serial
		remove_variable = zg361_b1_m010_receipt_serial
		remove_variable = zg361_b1_m011_receipt_serial
		remove_variable = zg361_b1_m013_receipt_serial
		set_variable = { name = zg361_b1_bank_posted_serial value = 0 }
		zg361_b1_classify_function_effect = yes
		set_variable = { name = zg361_b1_quota_function_code value = var:zg361_b1_function_code }
		zg361_b1_freeze_001_013_policy_effect = yes
		zg361_b1_freeze_135_145_policy_effect = yes
		set_variable = { name = zg361_b1_roster_amendment_n value = 0 }
		set_variable = { name = zg361_b1_roster_audit_version value = 1 }
		set_variable = { name = zg361_b1_roster_reopen_required value = 0 }
		set_variable = { name = zg361_b1_quota_built_serial value = 0 }
		set_variable = { name = zg361_b1_quota_book_version value = 0 }
		set_variable = { name = zg361_b1_quota_pool_membership value = 0 }
		set_variable = { name = zg361_b1_quota_trade_applied value = 0 }
		set_variable = { name = zg361_b1_must_review_manager_link_available value = 0 }
		set_variable = { name = zg361_b1_must_review_manager_link_state value = 0 }
		remove_variable = zg361_b1_must_review_manager_link_subject
		remove_variable = zg361_b1_must_review_manager_link_peer
		remove_variable = zg361_b1_consensus_link_subject
		set_variable = { name = zg361_b1_skip_level_return_count value = 0 }
		set_variable = { name = zg361_b1_oversight_return_status value = 0 }
		set_variable = { name = zg361_b1_publication_blocked value = 0 }
		remove_variable = zg361_b1_calibration_id
		set_variable = { name = zg361_b1_calibration_state value = 0 }
		remove_variable = zg361_b1_forced_bottom_case_id
		remove_variable = zg361_b1_bottom_protected_subject
		remove_variable = zg361_b1_bottom_carrier_subject
		remove_variable = zg361_b1_oversight_case_id
		remove_variable = zg361_b1_oversight_owner
		remove_variable = zg361_b1_oversight_reviewer
		set_variable = { name = zg361_b1_calibration_finalized value = 0 }
		set_variable = { name = zg361_b1_closure_state value = 0 }
		set_variable = { name = zg361_b1_rewards_issued value = 0 }
		set_variable = { name = zg361_b1_pending_rewards_committed value = 0 }
		set_variable = { name = zg361_b1_pending_reward_book_version value = 0 }
		set_variable = { name = zg361_b1_pending_reward_expected_n value = 0 }
		set_variable = { name = zg361_b1_pending_rewards_paid_n value = 0 }
		set_variable = { name = zg361_b1_peer_used value = 0 }
		set_variable = { name = zg361_b1_peer_cap value = 3 }
		set_variable = { name = zg361_b1_peer_fatigue value = 0 }
		set_variable = { name = zg361_b1_peer_use_mode value = 1 }
		set_variable = { name = zg361_b1_allow_rebase value = 1 }
		if = {
			limit = { has_variable = zg361_mechanism_003_choice }
			if = {
				limit = { var:zg361_mechanism_003_choice != 1 }
				set_variable = { name = zg361_b1_allow_rebase value = 0 }
			}
		}
		if = {
			limit = { has_variable = zg361_mechanism_053_choice }
			if = {
				limit = { var:zg361_mechanism_053_choice = 2 }
				set_variable = { name = zg361_b1_peer_use_mode value = 2 }
			}
			else_if = {
				limit = { var:zg361_mechanism_053_choice = 3 }
				set_variable = { name = zg361_b1_peer_use_mode value = 0 }
			}
		}
		set_variable = { name = zg361_b1_m053_receipt_serial value = var:zg361_b1_case_serial }
		if = {
			limit = { has_variable_list = zg361_b1_subjects }
			clear_variable_list = zg361_b1_subjects
		}
		every_vassal = {
			limit = { zg361_is_reviewable_vassal_trigger = yes }
			add_to_list = zg361_b1_subject_candidates
		}
		set_variable = {
			name = zg361_b1_subject_n
			value = { value = list_size:zg361_b1_subject_candidates max = 80 }
		}
		# Stable round-robin start advances by one frozen roster position each
		# cycle. Unlike a simple forward/reverse flip, every position eventually
		# reaches the bounded attention window.
		if = {
			limit = { NOT = { has_variable = zg361_b1_agenda_rotation_start } }
			set_variable = { name = zg361_b1_agenda_rotation_start value = 1 }
		}
		else = { change_variable = { name = zg361_b1_agenda_rotation_start add = 1 } }
		if = {
			limit = {
				var:zg361_b1_subject_n >= 1
				var:zg361_b1_agenda_rotation_start > var:zg361_b1_subject_n
			}
			set_variable = { name = zg361_b1_agenda_rotation_start value = 1 }
		}
		set_variable = { name = zg361_b1_roster_order_cursor value = 0 }
		ordered_in_list = {
			list = zg361_b1_subject_candidates
			order_by = primary_title.tier
			max = { value = list_size:zg361_b1_subject_candidates max = 80 }
			zg361_b1_initialize_subject_case_effect = yes
			root = { change_variable = { name = zg361_b1_roster_order_cursor add = 1 } }
			set_variable = { name = zg361_b1_roster_frozen_order value = root.var:zg361_b1_roster_order_cursor }
			save_temporary_scope_as = zg361_b1_subject_to_store
			root = {
				add_to_variable_list = {
					name = zg361_b1_subjects
					target = scope:zg361_b1_subject_to_store
				}
			}
		}

		if = {
			limit = { var:zg361_b1_subject_n >= 1 }
			zg361_b1_register_common_superior_bank_effect = yes
			save_scope_as = zg361_b1_ticket_owner
			save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
			save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
			save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
			trigger_event = { id = zg361b1.100 days = 180 }
			debug_log = "ZG361B1: performance season opened"
		}
		else = {
			set_variable = { name = zg361_b1_cycle_state value = 8 }
			remove_character_flag = zg361_b1_cycle_active
			debug_log = "ZG361B1: empty roster closed without settlement"
		}
	}
	else = { debug_log = "ZG361B1: cycle open ignored while another case is active" }
}

zg361_b1_midcycle_dispatcher_effect = {
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
			}
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 1
				}
				# Snapshot the formula without consuming one-shot evidence. The final
				# D+300 compute remains the sole consumer of a skipped-Jingcha penalty.
				set_variable = { name = zg361_b1_evidence_mid value = zg361_kpi_value }
				set_variable = { name = zg361_b1_self_score value = var:zg361_b1_evidence_mid }
				if = {
					limit = { var:zg361_b1_checkin_available = 1 }
					set_variable = { name = zg361_b1_checkin_id value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_checkin_completed_year value = current_year }
					if = {
						limit = { var:zg361_b1_evidence_mid <= 0 }
						set_variable = { name = zg361_b1_midcycle_warning value = 1 }
					}
					if = {
						limit = {
							root = { is_at_war = yes var:zg361_b1_allow_rebase = 1 var:zg361_b1_m003_mode = 1 }
							var:zg361_b1_target_rebased = 0
						}
						root = {
							random_character_war = { save_temporary_scope_as = zg361_b1_midcycle_crisis_war }
						}
						if = {
							limit = {
								exists = scope:zg361_b1_midcycle_crisis_war
								trigger_if = {
									limit = { has_variable = zg361_b1_last_rebaseline_war }
									NOT = { var:zg361_b1_last_rebaseline_war = scope:zg361_b1_midcycle_crisis_war }
								}
								trigger_else = { always = yes }
							}
							set_variable = { name = zg361_b1_crisis_war value = scope:zg361_b1_midcycle_crisis_war }
							set_variable = { name = zg361_b1_last_rebaseline_war value = scope:zg361_b1_midcycle_crisis_war }
							set_variable = { name = zg361_b1_crisis_id value = var:zg361_b1_case_serial }
							set_variable = { name = zg361_b1_crisis_type value = 1 }
							set_variable = { name = zg361_b1_goal_old_version value = var:zg361_b1_goal_version }
							set_variable = { name = zg361_b1_goal_old_target value = var:zg361_b1_goal_target }
							set_variable = { name = zg361_b1_target_rebased value = 1 }
							set_variable = { name = zg361_b1_rebaseline_used value = 1 }
							change_variable = { name = zg361_b1_goal_version add = 1 }
							set_variable = { name = zg361_b1_goal_new_version value = var:zg361_b1_goal_version }
							set_variable = { name = zg361_b1_goal_new_target value = { value = var:zg361_b1_goal_target subtract = 5 } }
							set_variable = { name = zg361_b1_goal_target value = var:zg361_b1_goal_new_target }
							set_variable = { name = zg361_b1_support_obligation value = 1 }
						}
					}
					else_if = {
						limit = { root.var:zg361_b1_m003_mode = 2 }
						set_variable = { name = zg361_b1_catchup_plan value = 1 }
						set_variable = { name = zg361_b1_support_obligation value = 0 }
					}
					set_variable = { name = zg361_b1_m003_receipt_serial value = var:zg361_b1_case_serial }
				}
				# #145 is an opportunity/coaching order only.  Its frozen weight is
				# consumed in the next cycle and is never read by a grade, bonus or
				# reward writer.  Only the formal middle band can carry an order.
				set_variable = { name = zg361_b1_opportunity_grant value = 0 }
				if = {
					limit = {
						var:zg361_b1_previous_band_object_available = 1
						has_variable = zg361_b1_previous_band_object_id
						has_variable = zg361_b1_previous_band_object_owner
						has_variable = zg361_b1_previous_band_object_subject
						has_variable = zg361_b1_previous_band_object_cycle
						has_variable = zg361_b1_previous_band_object_case
						has_variable = zg361_b1_previous_band_object_state
						var:zg361_b1_previous_band_object_owner = var:zg361_b1_case_owner
						var:zg361_b1_previous_band_object_subject = this
						var:zg361_b1_previous_band_object_state = 1
						var:zg361_b1_previous_band_object_case = var:zg361_b1_previous_band_object_id
						var:zg361_b1_previous_band_object_cycle < var:zg361_b1_cycle_serial
						var:zg361_b1_previous_final_grade = 2
						var:zg361_b1_previous_band_order >= 1
						var:zg361_b1_previous_band_opportunity_weight >= 2
					}
					set_variable = { name = zg361_b1_opportunity_grant value = var:zg361_b1_previous_band_opportunity_weight }
					set_variable = { name = zg361_b1_opportunity_project_available value = 1 }
					set_variable = { name = zg361_b1_opportunity_project_id value = var:zg361_b1_previous_band_object_id }
					set_variable = { name = zg361_b1_opportunity_project_owner value = var:zg361_b1_case_owner }
					set_variable = { name = zg361_b1_opportunity_project_subject value = this }
					set_variable = { name = zg361_b1_opportunity_project_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_opportunity_project_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_opportunity_project_state value = 1 }
					set_variable = { name = zg361_b1_opportunity_project_baseline value = var:zg361_b1_evidence_mid }
					set_variable = { name = zg361_b1_opportunity_project_budget value = var:zg361_b1_previous_band_opportunity_weight }
					set_variable = { name = zg361_b1_previous_band_object_state value = 2 }
					set_variable = { name = zg361_b1_previous_band_object_consumed_cycle value = var:zg361_b1_cycle_serial }
					if = {
						limit = { var:zg361_b1_previous_band_order_use_mode = 1 }
						set_variable = { name = zg361_b1_coaching_priority value = var:zg361_b1_previous_band_order }
					}
					else_if = {
						limit = { var:zg361_b1_previous_band_order_use_mode = 2 }
						set_variable = { name = zg361_b1_band_order_blackbox_risk value = 1 }
						set_variable = { name = zg361_b1_band_self_appeal_evidence value = var:zg361_b1_previous_band_self_appeal_evidence }
					}
				}
				set_variable = { name = zg361_b1_case_state value = 2 }
				set_variable = { name = zg361_b1_m046_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	set_variable = { name = zg361_b1_cycle_state value = 2 }
}

zg361_b1_finalize_self_review_effect = {
	set_variable = { name = zg361_b1_self_submitted value = 1 }
	set_variable = { name = zg361_b1_self_review_id value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_self_evidence_id value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_self_evidence_category value = 1 }
	set_variable = { name = zg361_b1_self_submitted_year value = current_year }
	set_variable = {
		name = zg361_b1_self_gap
		value = { value = var:zg361_b1_self_score subtract = var:zg361_b1_evidence_mid max = 15 min = -15 }
	}
	set_variable = { name = zg361_b1_self_band value = 2 }
	if = {
		limit = { var:zg361_b1_self_score >= 50 }
		set_variable = { name = zg361_b1_self_band value = 3 }
	}
	else_if = {
		limit = { var:zg361_b1_self_score < 0 }
		set_variable = { name = zg361_b1_self_band value = 1 }
	}
	set_variable = { name = zg361_b1_self_manager_response value = 1 }
	if = {
		limit = { var:zg361_b1_self_gap >= 10 }
		set_variable = { name = zg361_b1_self_manager_response value = 2 }
	}
	else_if = {
		limit = { var:zg361_b1_self_gap <= -10 }
		set_variable = { name = zg361_b1_self_manager_response value = 3 }
	}
	set_variable = { name = zg361_b1_m004_receipt_serial value = var:zg361_b1_case_serial }
}

zg361_b1_record_self_honest_effect = {
	set_variable = { name = zg361_b1_self_choice value = 1 }
	set_variable = { name = zg361_b1_self_score value = var:zg361_b1_evidence_mid }
	zg361_b1_finalize_self_review_effect = yes
}

zg361_b1_record_self_exaggerated_effect = {
	set_variable = { name = zg361_b1_self_choice value = 2 }
	set_variable = {
		name = zg361_b1_self_score
		value = { value = var:zg361_b1_evidence_mid add = 15 max = 100 min = -100 }
	}
	zg361_b1_finalize_self_review_effect = yes
}

zg361_b1_record_self_conservative_effect = {
	set_variable = { name = zg361_b1_self_choice value = 3 }
	set_variable = {
		name = zg361_b1_self_score
		value = { value = var:zg361_b1_evidence_mid subtract = 15 max = 100 min = -100 }
	}
	zg361_b1_finalize_self_review_effect = yes
}

zg361_b1_submit_self_honest_ticket_effect = {
	if = {
		limit = {
			exists = scope:zg361_b1_self_ticket_owner
			exists = scope:zg361_b1_self_ticket_subject
			has_variable = zg361_b1_case_owner
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_cycle_serial
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_state
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
		}
		if = {
			limit = {
				this = scope:zg361_b1_self_ticket_subject
				var:zg361_b1_case_owner = scope:zg361_b1_self_ticket_owner
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_self_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_self_ticket_case
				var:zg361_b1_case_state = scope:zg361_b1_self_ticket_state
				var:zg361_b1_case_state = 3
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_self_review_available = 1
				var:zg361_b1_self_submitted = 0
			}
			zg361_b1_record_self_honest_effect = yes
		}
		else = { debug_log = "ZG361B1: stale honest self-review ticket ignored" }
	}
	else = { debug_log = "ZG361B1: incomplete honest self-review ticket ignored" }
}

zg361_b1_submit_self_exaggerated_ticket_effect = {
	if = {
		limit = {
			exists = scope:zg361_b1_self_ticket_owner
			exists = scope:zg361_b1_self_ticket_subject
			has_variable = zg361_b1_case_owner
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_cycle_serial
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_state
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
		}
		if = {
			limit = {
				this = scope:zg361_b1_self_ticket_subject
				var:zg361_b1_case_owner = scope:zg361_b1_self_ticket_owner
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_self_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_self_ticket_case
				var:zg361_b1_case_state = scope:zg361_b1_self_ticket_state
				var:zg361_b1_case_state = 3
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_self_review_available = 1
				var:zg361_b1_self_submitted = 0
			}
			zg361_b1_record_self_exaggerated_effect = yes
		}
		else = { debug_log = "ZG361B1: stale exaggerated self-review ticket ignored" }
	}
	else = { debug_log = "ZG361B1: incomplete exaggerated self-review ticket ignored" }
}

zg361_b1_submit_self_conservative_ticket_effect = {
	if = {
		limit = {
			exists = scope:zg361_b1_self_ticket_owner
			exists = scope:zg361_b1_self_ticket_subject
			has_variable = zg361_b1_case_owner
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_cycle_serial
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_state
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
		}
		if = {
			limit = {
				this = scope:zg361_b1_self_ticket_subject
				var:zg361_b1_case_owner = scope:zg361_b1_self_ticket_owner
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_self_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_self_ticket_case
				var:zg361_b1_case_state = scope:zg361_b1_self_ticket_state
				var:zg361_b1_case_state = 3
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_self_review_available = 1
				var:zg361_b1_self_submitted = 0
			}
			zg361_b1_record_self_conservative_effect = yes
		}
		else = { debug_log = "ZG361B1: stale conservative self-review ticket ignored" }
	}
	else = { debug_log = "ZG361B1: incomplete conservative self-review ticket ignored" }
}

zg361_b1_peer_window_dispatcher_effect = {
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = { has_variable = zg361_b1_case_owner }
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_state = 2
				}
				set_variable = { name = zg361_b1_case_state value = 3 }
				if = {
					limit = { root.var:zg361_b1_m007_mode != 3 }
					set_variable = { name = zg361_b1_m007_receipt_serial value = var:zg361_b1_case_serial }
				}
				set_variable = { name = zg361_b1_m048_receipt_serial value = var:zg361_b1_case_serial }
				if = {
					limit = { var:zg361_b1_self_review_available = 1 }
					if = {
						limit = { is_ai = yes }
						zg361_b1_record_self_honest_effect = yes
					}
					else = {
						var:zg361_b1_case_owner = { save_scope_as = zg361_b1_self_ticket_owner }
						save_scope_as = zg361_b1_self_ticket_subject
						save_scope_value_as = { name = zg361_b1_self_ticket_cycle value = var:zg361_b1_cycle_serial }
						save_scope_value_as = { name = zg361_b1_self_ticket_case value = var:zg361_b1_case_serial }
						save_scope_value_as = { name = zg361_b1_self_ticket_state value = var:zg361_b1_case_state }
						trigger_event = { id = zg361b1.200 days = 1 }
					}
				}
			}
		}
	}
	set_variable = { name = zg361_b1_cycle_state value = 3 }
}

zg361_b1_prepare_facts_effect = {
	# Departures and legal late arrivals/backfills are reconciled before the
	# legacy review builds its live cohort, so the same amended list reaches the
	# facts sheet and the exact quota denominator.
	zg361_b1_audit_locked_roster_additions_effect = yes
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
				has_variable = zg361_b1_case_active
				has_variable = zg361_b1_roster_included
			}
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 3
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
				}
				# A missing player response is closed honestly at the evidence deadline.
				# A stale visible event can no longer alter the sealed case afterwards.
				if = {
					limit = { var:zg361_b1_self_review_available = 1 var:zg361_b1_self_submitted = 0 }
					zg361_b1_record_self_honest_effect = yes
				}
				set_variable = { name = zg361_b1_evidence_late value = zg361_kpi_value }
				if = {
					limit = {
						var:zg361_b1_opportunity_project_available = 1
						var:zg361_b1_opportunity_project_owner = root
						var:zg361_b1_opportunity_project_subject = this
						var:zg361_b1_opportunity_project_cycle = var:zg361_b1_cycle_serial
						var:zg361_b1_opportunity_project_case = var:zg361_b1_case_serial
						var:zg361_b1_opportunity_project_state = 1
					}
					set_variable = { name = zg361_b1_opportunity_project_observed value = var:zg361_b1_evidence_late }
					set_variable = { name = zg361_b1_opportunity_project_improvement value = { value = var:zg361_b1_opportunity_project_observed subtract = var:zg361_b1_opportunity_project_baseline } }
					set_variable = { name = zg361_b1_opportunity_project_outcome value = 2 }
					set_variable = { name = zg361_b1_opportunity_evidence_adjustment value = 0 }
					if = {
						limit = { var:zg361_b1_opportunity_project_improvement >= 1 }
						set_variable = { name = zg361_b1_opportunity_project_outcome value = 1 }
						set_variable = { name = zg361_b1_opportunity_evidence_adjustment value = { value = var:zg361_b1_opportunity_project_budget subtract = 1 max = 2 min = 1 } }
					}
					set_variable = { name = zg361_b1_opportunity_project_state value = 2 }
					set_variable = { name = zg361_b1_opportunity_project_resolved_year value = current_year }
				}
				set_variable = { name = zg361_b1_evidence_early_weighted value = { value = var:zg361_b1_evidence_early multiply = var:zg361_b1_evidence_early_weight } }
				set_variable = { name = zg361_b1_evidence_mid_weighted value = { value = var:zg361_b1_evidence_mid multiply = var:zg361_b1_evidence_mid_weight } }
				set_variable = { name = zg361_b1_evidence_late_weighted value = { value = var:zg361_b1_evidence_late multiply = var:zg361_b1_evidence_late_weight } }
				set_variable = {
					name = zg361_b1_evidence_window_score
					value = {
						value = var:zg361_b1_evidence_early_weighted
						add = var:zg361_b1_evidence_mid_weighted
						add = var:zg361_b1_evidence_late_weighted
						divide = 100
					}
				}
				set_variable = {
					name = zg361_b1_evidence_window_adjustment
					value = { value = var:zg361_b1_evidence_window_score subtract = var:zg361_b1_evidence_late multiply = 0.2 round = yes max = 5 min = -5 }
				}
				if = {
					limit = { var:zg361_b1_goal_available = 1 }
					set_variable = { name = zg361_b1_goal_completion_delta value = { value = var:zg361_b1_evidence_late subtract = var:zg361_b1_goal_target } }
					set_variable = {
						name = zg361_b1_goal_score_adjustment
						value = { value = var:zg361_b1_goal_completion_delta multiply = var:zg361_b1_goal_weight divide = 100 max = 5 min = -5 }
					}
				}
				set_variable = { name = zg361_b1_difficulty_improvement value = { value = var:zg361_b1_evidence_late subtract = var:zg361_b1_evidence_early } }
				set_variable = { name = zg361_b1_difficulty_score_adjustment value = { value = var:zg361_b1_difficulty_adjustment max = var:zg361_b1_difficulty_cap min = -5 } }
				set_variable = { name = zg361_b1_peer_n value = 0 }
				set_variable = { name = zg361_b1_peer_raw_sum value = 0 }
				set_variable = { name = zg361_b1_peer_weighted_sum value = 0 }
				set_variable = { name = zg361_b1_peer_credit_total value = 0 }
				set_variable = { name = zg361_b1_peer_sum_squares value = 0 }
				set_variable = { name = zg361_b1_peer_adjusted_sum value = 0 }
				set_variable = { name = zg361_b1_peer_mean value = 0 }
				set_variable = { name = zg361_b1_peer_variance value = 0 }
				set_variable = { name = zg361_b1_peer_normalized_score value = 0 }
				set_variable = { name = zg361_b1_peer_shape value = 0 }
				set_variable = { name = zg361_b1_peer_reciprocity_risk value = 0 }
				zg361_b1_consume_peer_slot_1_effect = yes
				zg361_b1_consume_peer_slot_2_effect = yes
				zg361_b1_consume_peer_slot_3_effect = yes
				if = {
					limit = { var:zg361_b1_peer_n >= 1 }
					set_variable = {
						name = zg361_b1_peer_mean
						value = { value = var:zg361_b1_peer_raw_sum divide = var:zg361_b1_peer_n max = 10 min = -15 }
					}
					set_variable = {
						name = zg361_b1_peer_variance
						value = {
							value = var:zg361_b1_peer_sum_squares
							divide = var:zg361_b1_peer_n
							subtract = { value = var:zg361_b1_peer_mean multiply = var:zg361_b1_peer_mean }
							min = 0
						}
					}
					if = {
						limit = { var:zg361_b1_peer_credit_total >= 1 }
						set_variable = {
							name = zg361_b1_peer_normalized_score
							value = { value = var:zg361_b1_peer_weighted_sum divide = var:zg361_b1_peer_credit_total max = 10 min = -15 }
						}
					}
					if = {
						limit = { var:zg361_b1_peer_variance >= 100 }
						set_variable = { name = zg361_b1_peer_shape value = 4 }
					}
					else_if = {
						limit = { var:zg361_b1_peer_mean >= 5 }
						set_variable = { name = zg361_b1_peer_shape value = 1 }
					}
					else_if = {
						limit = { var:zg361_b1_peer_mean <= -5 }
						set_variable = { name = zg361_b1_peer_shape value = 3 }
					}
					else = { set_variable = { name = zg361_b1_peer_shape value = 2 } }
				}
				set_variable = { name = zg361_b1_peer_sealed value = 1 }
				set_variable = { name = zg361_b1_peer_author_count value = var:zg361_b1_peer_n }
				set_variable = { name = zg361_b1_peer_effective_weight_percent value = { value = var:zg361_b1_peer_author_count multiply = 5 max = var:zg361_b1_peer_total_weight_cap } }
				set_variable = { name = zg361_b1_peer_public_summary_available value = 0 }
				set_variable = { name = zg361_b1_peer_manager_only value = 1 }
				if = {
					limit = { var:zg361_b1_peer_author_count >= var:zg361_b1_peer_anonymous_threshold }
					set_variable = { name = zg361_b1_peer_public_summary_available value = 1 }
					set_variable = { name = zg361_b1_peer_manager_only value = 0 }
				}
				set_variable = { name = zg361_b1_evidence_late_frozen value = 1 }
				if = {
					limit = { root.var:zg361_b1_m008_mode != 3 var:zg361_b1_peer_use_mode != 0 }
					set_variable = { name = zg361_b1_m008_receipt_serial value = var:zg361_b1_case_serial }
				}
				set_variable = { name = zg361_b1_m049_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m050_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m052_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
}

# The legacy review has now computed the authoritative eight components and
# pending grade.  Freeze route-specific facts and the bounded goal/role/window
# interpretation before shadow response can change calibration only.
zg361_b1_finalize_subject_facts_effect = {
	set_variable = { name = zg361_b1_fact_total value = var:zg361_kpi }
	set_variable = { name = zg361_b1_evidence_sheet_available value = 0 }
	set_variable = { name = zg361_b1_evidence_incomplete value = 0 }
	if = {
		limit = { root.var:zg361_b1_m001_mode = 1 }
		set_variable = { name = zg361_b1_evidence_sheet_available value = 1 }
		set_variable = { name = zg361_b1_evidence_sheet_id value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_evidence_governance value = var:zg361_evidence_governance }
		set_variable = { name = zg361_b1_evidence_capability value = var:zg361_evidence_capability }
		set_variable = { name = zg361_b1_evidence_growth value = var:zg361_evidence_growth }
		set_variable = { name = zg361_b1_evidence_superior value = var:zg361_evidence_superior }
		set_variable = { name = zg361_b1_evidence_values value = var:zg361_evidence_values }
		set_variable = { name = zg361_b1_evidence_collaboration value = var:zg361_evidence_collaboration }
		set_variable = { name = zg361_b1_evidence_jingcha value = var:zg361_evidence_jingcha }
		set_variable = { name = zg361_b1_evidence_organization value = var:zg361_evidence_organization }
		set_variable = {
			name = zg361_b1_evidence_sum_check
			value = {
				value = var:zg361_b1_evidence_governance
				add = var:zg361_b1_evidence_capability
				add = var:zg361_b1_evidence_growth
				add = var:zg361_b1_evidence_superior
				add = var:zg361_b1_evidence_values
				add = var:zg361_b1_evidence_collaboration
				add = var:zg361_b1_evidence_jingcha
				add = var:zg361_b1_evidence_organization
			}
		}
		set_variable = { name = zg361_b1_evidence_sum_matches_kpi value = 0 }
		if = {
			limit = { var:zg361_b1_evidence_sum_check = var:zg361_kpi }
			set_variable = { name = zg361_b1_evidence_sum_matches_kpi value = 1 }
		}
	}
	else_if = {
		limit = { root.var:zg361_b1_m001_mode = 2 }
		set_variable = { name = zg361_b1_evidence_sheet_available value = 1 }
		set_variable = { name = zg361_b1_evidence_sheet_id value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_evidence_incomplete value = 1 }
		set_variable = { name = zg361_b1_evidence_sum_check value = var:zg361_kpi }
	}
	else = { remove_variable = zg361_b1_evidence_sheet_id }
	if = {
		limit = { var:zg361_b1_goal_available = 1 }
		set_variable = { name = zg361_b1_goal_completion_delta value = { value = var:zg361_kpi subtract = var:zg361_b1_goal_target } }
		set_variable = { name = zg361_b1_goal_score_adjustment value = { value = var:zg361_b1_goal_completion_delta multiply = var:zg361_b1_goal_weight divide = 100 max = 5 min = -5 } }
	}
	if = {
		limit = { var:zg361_b1_role_scorecard_available = 1 }
		set_variable = {
			name = zg361_b1_role_weighted_score
			value = {
				value = { value = var:zg361_evidence_governance multiply = var:zg361_b1_role_weight_governance }
				add = { value = var:zg361_evidence_capability multiply = var:zg361_b1_role_weight_capability }
				add = { value = var:zg361_evidence_growth multiply = var:zg361_b1_role_weight_growth }
				add = { value = var:zg361_evidence_superior multiply = var:zg361_b1_role_weight_superior }
				add = { value = var:zg361_evidence_values multiply = var:zg361_b1_role_weight_values }
				add = { value = var:zg361_evidence_collaboration multiply = var:zg361_b1_role_weight_collaboration }
				add = { value = var:zg361_evidence_jingcha multiply = var:zg361_b1_role_weight_jingcha }
				add = { value = var:zg361_evidence_organization multiply = var:zg361_b1_role_weight_organization }
				divide = 100
			}
		}
		set_variable = { name = zg361_b1_role_score_adjustment value = { value = var:zg361_b1_role_weighted_score multiply = 0.2 round = yes max = 5 min = -5 } }
	}
	set_variable = { name = zg361_b1_difficulty_improvement value = { value = var:zg361_kpi subtract = var:zg361_b1_evidence_early } }
	set_variable = { name = zg361_b1_difficulty_score_adjustment value = 0 }
	if = {
		limit = { var:zg361_b1_baseline_available = 1 }
		set_variable = { name = zg361_b1_baseline_end_development value = capital_county.development_level }
		set_variable = { name = zg361_b1_baseline_end_control value = capital_county.county_control }
		set_variable = { name = zg361_b1_baseline_end_gold value = gold }
		set_variable = { name = zg361_b1_baseline_end_war value = 0 }
		if = {
			limit = { is_at_war = yes }
			set_variable = { name = zg361_b1_baseline_end_war value = 1 }
		}
		set_variable = { name = zg361_b1_baseline_end_resources value = domain_size }
		set_variable = {
			name = zg361_b1_baseline_state_delta
			value = {
				value = var:zg361_b1_baseline_end_development
				subtract = var:zg361_b1_baseline_start_development
				add = { value = var:zg361_b1_baseline_end_control subtract = var:zg361_b1_baseline_start_control multiply = 0.1 }
				add = { value = var:zg361_b1_baseline_end_gold subtract = var:zg361_b1_baseline_start_gold multiply = 0.01 }
				add = { value = var:zg361_b1_baseline_start_war subtract = var:zg361_b1_baseline_end_war multiply = 2 }
				add = { value = var:zg361_b1_baseline_end_resources subtract = var:zg361_b1_baseline_start_resources multiply = 2 }
			}
		}
		if = {
			limit = { root.var:zg361_b1_m006_mode = 1 }
			set_variable = { name = zg361_b1_difficulty_score_adjustment value = { value = var:zg361_b1_baseline_state_delta round = yes max = var:zg361_b1_difficulty_cap min = -5 } }
		}
	}
	if = {
		limit = { root.var:zg361_b1_m001_mode != 3 }
		set_variable = { name = zg361_b1_m001_receipt_serial value = var:zg361_b1_case_serial }
	}
}

zg361_b1_record_shadow_accept_effect = {
	if = {
		limit = {
			var:zg361_b1_shadow_object_available = 1
			var:zg361_b1_shadow_object_owner = var:zg361_b1_case_owner
			var:zg361_b1_shadow_object_subject = this
			var:zg361_b1_shadow_object_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_shadow_object_case = var:zg361_b1_case_serial
			var:zg361_b1_shadow_object_state = 1
			var:zg361_b1_shadow_reveal_state = 1
			var:zg361_b1_shadow_response_state = 0
		}
		set_variable = { name = zg361_b1_shadow_response_state value = 1 }
		set_variable = { name = zg361_b1_shadow_evidence_delta value = 0 }
		set_variable = { name = zg361_b1_shadow_response_year value = current_year }
	}
}

zg361_b1_record_shadow_supplement_effect = {
	if = {
		limit = {
			var:zg361_b1_shadow_object_available = 1
			var:zg361_b1_shadow_object_owner = var:zg361_b1_case_owner
			var:zg361_b1_shadow_object_subject = this
			var:zg361_b1_shadow_object_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_shadow_object_case = var:zg361_b1_case_serial
			var:zg361_b1_shadow_object_state = 1
			var:zg361_b1_shadow_reveal_state = 1
			var:zg361_b1_shadow_response_state = 0
		}
		set_variable = { name = zg361_b1_shadow_response_state value = 2 }
		set_variable = { name = zg361_b1_shadow_new_evidence_observed_score value = zg361_kpi_value }
		set_variable = {
			name = zg361_b1_shadow_evidence_delta
			value = { value = var:zg361_b1_shadow_new_evidence_observed_score subtract = var:zg361_b1_shadow_new_evidence_baseline_score max = 10 min = -10 }
		}
		set_variable = { name = zg361_b1_shadow_response_year value = current_year }
		# A zero delta is an acknowledged response, not a fabricated evidence
		# packet and therefore cannot wash away an unexplained downgrade debt.
		if = {
			limit = { NOT = { var:zg361_b1_shadow_evidence_delta = 0 } }
			set_variable = { name = zg361_b1_shadow_evidence_object_available value = 1 }
			set_variable = {
				name = zg361_b1_shadow_evidence_object_id
				value = { value = var:zg361_b1_case_serial multiply = 100 add = 1 }
			}
			set_variable = { name = zg361_b1_shadow_evidence_object_owner value = var:zg361_b1_case_owner }
			set_variable = { name = zg361_b1_shadow_evidence_object_subject value = this }
			set_variable = { name = zg361_b1_shadow_evidence_object_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_shadow_evidence_object_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_shadow_evidence_object_state value = 2 }
			set_variable = { name = zg361_b1_shadow_evidence_revision value = 1 }
			set_variable = { name = zg361_b1_shadow_new_evidence value = 1 }
			set_variable = { name = zg361_b1_shadow_new_evidence_source value = 1 }
			set_variable = { name = zg361_b1_shadow_new_evidence_year value = current_year }
			set_variable = { name = zg361_b1_shadow_evidence_consumed value = 1 }
			# Supplementary evidence is a bounded calibration input. It never writes
			# zg361_kpi, zg361_absolute_grade or the already frozen shadow grade.
			set_variable = {
				name = zg361_b1_calibration_score
				value = { value = var:zg361_b1_calibration_score add = var:zg361_b1_shadow_evidence_delta }
			}
		}
	}
}

zg361_b1_submit_shadow_accept_ticket_effect = {
	if = {
		limit = {
			exists = scope:zg361_b1_shadow_ticket_owner
			exists = scope:zg361_b1_shadow_ticket_subject
			has_variable = zg361_b1_case_owner
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_cycle_serial
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_state
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
		}
		if = {
			limit = {
				this = scope:zg361_b1_shadow_ticket_subject
				var:zg361_b1_case_owner = scope:zg361_b1_shadow_ticket_owner
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_shadow_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_shadow_ticket_case
				var:zg361_b1_case_state = scope:zg361_b1_shadow_ticket_state
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_shadow_object_available = 1
				var:zg361_b1_shadow_object_owner = scope:zg361_b1_shadow_ticket_owner
				var:zg361_b1_shadow_object_subject = this
				var:zg361_b1_shadow_object_cycle = scope:zg361_b1_shadow_ticket_cycle
				var:zg361_b1_shadow_object_case = scope:zg361_b1_shadow_ticket_case
				var:zg361_b1_shadow_object_state = 1
				var:zg361_b1_shadow_reveal_state = 1
				var:zg361_b1_shadow_response_state = 0
			}
			zg361_b1_record_shadow_accept_effect = yes
		}
		else = { debug_log = "ZG361B1: stale shadow-accept ticket ignored" }
	}
	else = { debug_log = "ZG361B1: incomplete shadow-accept ticket ignored" }
}

zg361_b1_submit_shadow_supplement_ticket_effect = {
	if = {
		limit = {
			exists = scope:zg361_b1_shadow_ticket_owner
			exists = scope:zg361_b1_shadow_ticket_subject
			has_variable = zg361_b1_case_owner
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_cycle_serial
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_state
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
		}
		if = {
			limit = {
				this = scope:zg361_b1_shadow_ticket_subject
				var:zg361_b1_case_owner = scope:zg361_b1_shadow_ticket_owner
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_shadow_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_shadow_ticket_case
				var:zg361_b1_case_state = scope:zg361_b1_shadow_ticket_state
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_shadow_object_available = 1
				var:zg361_b1_shadow_object_owner = scope:zg361_b1_shadow_ticket_owner
				var:zg361_b1_shadow_object_subject = this
				var:zg361_b1_shadow_object_cycle = scope:zg361_b1_shadow_ticket_cycle
				var:zg361_b1_shadow_object_case = scope:zg361_b1_shadow_ticket_case
				var:zg361_b1_shadow_object_state = 1
				var:zg361_b1_shadow_reveal_state = 1
				var:zg361_b1_shadow_response_state = 0
			}
			zg361_b1_record_shadow_supplement_effect = yes
		}
		else = { debug_log = "ZG361B1: stale shadow-supplement ticket ignored" }
	}
	else = { debug_log = "ZG361B1: incomplete shadow-supplement ticket ignored" }
}

# Freeze an identity-blind order, then a named order whose only permitted
# difference is a visible relationship-risk adjustment.  The quota consumer
# remains the blind calibration score; a material rank delta creates a manager
# audit instead of silently changing the hard facts.
zg361_b1_freeze_blind_named_diff_effect = {
	set_variable = { name = zg361_b1_blind_named_n value = 0 }
	set_variable = { name = zg361_b1_blind_bias_audit_n value = 0 }
	save_temporary_scope_as = zg361_b1_blind_named_manager
	# This is an event-target list, not a persistent variable list.  Seed it
	# with the real manager character so the zero-candidate path still has a
	# loader-visible object setter.  Both business passes exclude the anchor.
	add_to_list = zg361_b1_blind_named_candidates
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
				has_variable = zg361_b1_case_active
				var:zg361_b1_case_owner = scope:zg361_b1_blind_named_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_blind_named_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_blind_named_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
			}
			set_variable = { name = zg361_b1_blind_token value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_roster_frozen_order } }
			set_variable = { name = zg361_b1_blind_score value = var:zg361_b1_calibration_score }
			set_variable = { name = zg361_b1_named_relationship_adjustment value = 0 }
			if = {
				limit = { OR = { is_close_family_of = root has_relation_friend = root has_relation_lover = root } }
				set_variable = { name = zg361_b1_named_relationship_adjustment value = 5 }
			}
			else_if = {
				limit = { OR = { has_relation_rival = root has_relation_nemesis = root } }
				set_variable = { name = zg361_b1_named_relationship_adjustment value = -5 }
			}
			set_variable = { name = zg361_b1_named_score value = { value = var:zg361_b1_blind_score add = var:zg361_b1_named_relationship_adjustment } }
			add_to_list = zg361_b1_blind_named_candidates
			root = { change_variable = { name = zg361_b1_blind_named_n add = 1 } }
		}
	}
	set_variable = { name = zg361_b1_blind_rank_cursor value = 0 }
	ordered_in_list = {
		list = zg361_b1_blind_named_candidates
		order_by = var:zg361_b1_blind_score
		max = { value = var:zg361_b1_blind_named_n max = 80 }
		limit = { NOT = { this = scope:zg361_b1_blind_named_manager } }
		root = { change_variable = { name = zg361_b1_blind_rank_cursor add = 1 } }
		set_variable = { name = zg361_b1_blind_rank value = root.var:zg361_b1_blind_rank_cursor }
	}
	set_variable = { name = zg361_b1_named_rank_cursor value = 0 }
	ordered_in_list = {
		list = zg361_b1_blind_named_candidates
		order_by = var:zg361_b1_named_score
		max = { value = var:zg361_b1_blind_named_n max = 80 }
		limit = { NOT = { this = scope:zg361_b1_blind_named_manager } }
		root = { change_variable = { name = zg361_b1_named_rank_cursor add = 1 } }
		set_variable = { name = zg361_b1_named_rank value = root.var:zg361_b1_named_rank_cursor }
		set_variable = { name = zg361_b1_blind_named_rank_delta value = { value = var:zg361_b1_named_rank subtract = var:zg361_b1_blind_rank } }
		set_variable = { name = zg361_b1_blind_named_rank_magnitude value = var:zg361_b1_blind_named_rank_delta }
		if = {
			limit = { var:zg361_b1_blind_named_rank_magnitude < 0 }
			set_variable = { name = zg361_b1_blind_named_rank_magnitude value = { value = 0 subtract = var:zg361_b1_blind_named_rank_magnitude } }
		}
		set_variable = { name = zg361_b1_blind_named_audit value = 0 }
		if = {
			limit = { var:zg361_b1_blind_named_rank_magnitude >= 2 }
			set_variable = { name = zg361_b1_blind_named_audit value = 1 }
			root = { change_variable = { name = zg361_b1_blind_bias_audit_n add = 1 } }
		}
		set_variable = { name = zg361_b1_m044_receipt_serial value = var:zg361_b1_case_serial }
	}
	scope:zg361_b1_blind_named_manager = {
		remove_from_list = zg361_b1_blind_named_candidates
	}
}

zg361_b1_open_shadow_effect = {
	if = {
		limit = { var:zg361_b1_cycle_state = 3 }
		set_variable = { name = zg361_b1_cycle_state value = 4 }
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = { has_variable = zg361_b1_case_owner }
				if = {
					limit = {
						var:zg361_b1_case_owner = root
						var:zg361_b1_case_state = 3
						has_variable = zg361_pending_grade
					}
					zg361_b1_finalize_subject_facts_effect = yes
					set_variable = { name = zg361_b1_case_state value = 4 }
					set_variable = { name = zg361_b1_fact_sheet_serial value = 0 }
					if = {
						limit = { var:zg361_b1_evidence_sheet_available = 1 }
						set_variable = { name = zg361_b1_fact_sheet_serial value = var:zg361_b1_evidence_sheet_id }
					}
					set_variable = { name = zg361_b1_fact_closed_year value = current_year }
					set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_shadow_grade value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_shadow_response_state value = 0 }
					set_variable = { name = zg361_b1_shadow_evidence_delta value = 0 }
					set_variable = { name = zg361_b1_shadow_object_available value = 0 }
					set_variable = { name = zg361_b1_shadow_reveal_state value = 0 }
					set_variable = { name = zg361_b1_shadow_gap_mask value = 0 }
					set_variable = {
						name = zg361_b1_shadow_gap_magnitude
						value = { value = var:zg361_b1_evidence_late subtract = var:zg361_b1_evidence_mid }
					}
					if = {
						limit = { var:zg361_b1_shadow_gap_magnitude < 0 }
						set_variable = { name = zg361_b1_shadow_gap_magnitude value = { value = 0 subtract = var:zg361_b1_shadow_gap_magnitude } }
					}
					if = {
						limit = { NOT = { var:zg361_b1_shadow_grade = var:zg361_absolute_grade } }
						change_variable = { name = zg361_b1_shadow_gap_mask add = 1 }
					}
					if = {
						limit = { var:zg361_b1_shadow_gap_magnitude >= 1 }
						change_variable = { name = zg361_b1_shadow_gap_mask add = 2 }
					}
					set_variable = { name = zg361_b1_self_visibility_adjustment value = 0 }
					if = {
						limit = { var:zg361_b1_self_gap > 0 }
						set_variable = { name = zg361_b1_self_visibility_adjustment value = { value = var:zg361_b1_self_gap multiply = -0.2 round = yes max = 0 min = -3 } }
					}
					else_if = {
						limit = { var:zg361_b1_self_gap < 0 }
						set_variable = { name = zg361_b1_self_visibility_adjustment value = { value = var:zg361_b1_self_gap multiply = 0.1 round = yes max = 0 min = -2 } }
					}
					set_variable = { name = zg361_b1_peer_calibration_adjustment value = 0 }
					if = {
						limit = { var:zg361_b1_peer_use_mode = 2 }
						set_variable = {
							name = zg361_b1_peer_calibration_adjustment
							value = { value = var:zg361_b1_peer_normalized_score multiply = var:zg361_b1_peer_effective_weight_percent divide = 100 round = yes max = 2 min = -3 }
						}
						if = {
							limit = { var:zg361_b1_peer_shape = 4 }
							change_variable = { name = zg361_b1_peer_calibration_adjustment add = -2 }
						}
						if = {
							limit = { var:zg361_b1_peer_reciprocity_risk = 1 }
							change_variable = { name = zg361_b1_peer_calibration_adjustment add = -2 }
						}
						set_variable = {
							name = zg361_b1_peer_calibration_adjustment
							value = { value = var:zg361_b1_peer_calibration_adjustment max = 2 min = -5 }
						}
					}
					set_variable = {
						name = zg361_b1_calibration_score
						value = {
							value = var:zg361_kpi
							add = var:zg361_b1_self_visibility_adjustment
							add = var:zg361_b1_peer_calibration_adjustment
							add = var:zg361_b1_goal_score_adjustment
							add = var:zg361_b1_role_score_adjustment
							add = var:zg361_b1_evidence_window_adjustment
							add = var:zg361_b1_difficulty_score_adjustment
							add = var:zg361_b1_manager_liability_adjustment
							add = var:zg361_b1_pending_carried_adjustment
							add = var:zg361_b1_reopen_carried_adjustment
							add = var:zg361_b1_opportunity_evidence_adjustment
						}
					}
					set_variable = { name = zg361_b1_calibration_score_before_shadow value = var:zg361_b1_calibration_score }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = {
						limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
						set_variable = { name = zg361_b1_forced_down value = 1 }
					}
					set_variable = { name = zg361_b1_case_state value = 5 }
					set_variable = { name = zg361_b1_m039_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m040_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m042_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m044_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m047_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m357_receipt_serial value = var:zg361_b1_case_serial }
					# #135 A creates a real non-final response object; B freezes the
					# same comparison but withholds it until final publication; C creates
					# no shadow business object at all.
					if = {
						limit = { root.var:zg361_b1_m135_mode != 3 }
						set_variable = { name = zg361_b1_shadow_object_available value = 1 }
						set_variable = { name = zg361_b1_shadow_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 35 } }
						set_variable = { name = zg361_b1_shadow_object_owner value = root }
						set_variable = { name = zg361_b1_shadow_object_subject value = this }
						set_variable = { name = zg361_b1_shadow_object_cycle value = var:zg361_b1_cycle_serial }
						set_variable = { name = zg361_b1_shadow_object_case value = var:zg361_b1_case_serial }
						set_variable = { name = zg361_b1_shadow_object_state value = 1 }
						set_variable = { name = zg361_b1_shadow_object_nonfinal value = 1 }
						set_variable = { name = zg361_b1_shadow_new_evidence_baseline_score value = var:zg361_b1_evidence_late }
						set_variable = { name = zg361_b1_shadow_notice_year value = current_year }
						set_variable = { name = zg361_b1_shadow_deadline_year value = current_year }
						set_variable = { name = zg361_b1_shadow_deadline_days value = 30 }
						set_variable = { name = zg361_b1_m135_receipt_serial value = var:zg361_b1_shadow_object_case }
						if = {
							limit = { root.var:zg361_b1_m135_mode = 1 }
							set_variable = { name = zg361_b1_shadow_reveal_state value = 1 }
							if = {
								limit = { is_ai = yes }
								zg361_b1_record_shadow_accept_effect = yes
							}
							else = {
								var:zg361_b1_case_owner = { save_scope_as = zg361_b1_shadow_ticket_owner }
								save_scope_as = zg361_b1_shadow_ticket_subject
								save_scope_value_as = { name = zg361_b1_shadow_ticket_cycle value = var:zg361_b1_cycle_serial }
								save_scope_value_as = { name = zg361_b1_shadow_ticket_case value = var:zg361_b1_case_serial }
								save_scope_value_as = { name = zg361_b1_shadow_ticket_state value = var:zg361_b1_case_state }
								trigger_event = { id = zg361b1.201 days = 1 }
							}
						}
					}
				}
			}
		}
		zg361_b1_freeze_blind_named_diff_effect = yes
		set_variable = { name = zg361_b1_cycle_state value = 5 }
		save_scope_as = zg361_b1_ticket_owner
		save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.103 days = 30 }
		debug_log = "ZG361B1: facts frozen and shadow response opened"
	}
}

zg361_b1_register_common_superior_bank_effect = {
	if = {
		limit = { exists = liege }
		save_temporary_scope_as = zg361_b1_registering_manager
		liege = {
			if = {
				limit = { zg361_is_celestial_liege_trigger = yes }
				save_temporary_scope_as = zg361_b1_bank_owner
				if = {
					limit = {
						trigger_if = {
							limit = { has_variable = zg361_b1_bank_season }
							NOT = { var:zg361_b1_bank_season = current_year }
						}
						trigger_else = { always = yes }
					}
					if = {
						limit = { has_variable_list = zg361_b1_expected_managers }
						clear_variable_list = zg361_b1_expected_managers
					}
					if = {
						limit = { has_variable_list = zg361_b1_ready_managers }
						clear_variable_list = zg361_b1_ready_managers
					}
					set_variable = { name = zg361_b1_bank_season value = current_year }
					if = {
						limit = { NOT = { has_variable = zg361_b1_bank_case_serial } }
						set_variable = { name = zg361_b1_bank_case_serial value = 0 }
					}
					change_variable = { name = zg361_b1_bank_case_serial add = 1 }
					set_variable = { name = zg361_b1_bank_state value = 1 }
					set_variable = { name = zg361_b1_bank_m136_mode value = 1 }
					set_variable = { name = zg361_b1_bank_m138_mode value = 1 }
					set_variable = { name = zg361_b1_bank_m141_mode value = 1 }
					if = { limit = { has_variable = zg361_mechanism_136_choice } set_variable = { name = zg361_b1_bank_m136_mode value = var:zg361_mechanism_136_choice } }
					if = { limit = { has_variable = zg361_mechanism_138_choice } set_variable = { name = zg361_b1_bank_m138_mode value = var:zg361_mechanism_138_choice } }
					if = { limit = { has_variable = zg361_mechanism_141_choice } set_variable = { name = zg361_b1_bank_m141_mode value = var:zg361_mechanism_141_choice } }
					set_variable = { name = zg361_b1_huddle_host_object_available value = 0 }
					set_variable = { name = zg361_b1_huddle_host_attendee_n value = 0 }
					set_variable = { name = zg361_b1_must_review_host_object_available value = 0 }
					set_variable = { name = zg361_b1_must_review_count value = 0 }
					set_variable = { name = zg361_b1_expected_manager_n value = 0 }
					set_variable = { name = zg361_b1_ready_manager_n value = 0 }
					set_variable = { name = zg361_b1_pool_n value = 0 }
					every_vassal = {
						limit = {
							zg361_is_celestial_liege_trigger = yes
							any_vassal = {
								count >= 1
								zg361_is_reviewable_vassal_trigger = yes
							}
						}
						save_temporary_scope_as = zg361_b1_expected_manager
						scope:zg361_b1_bank_owner = {
							add_to_variable_list = {
								name = zg361_b1_expected_managers
								target = scope:zg361_b1_expected_manager
							}
							change_variable = { name = zg361_b1_expected_manager_n add = 1 }
						}
						# Reset ROOT through a one-day character event before calling
						# the manager-owned cycle effect. Direct nested calls would retain
						# the first manager as ROOT and corrupt sibling case ownership.
						trigger_event = { id = zg361b1.90 days = 1 }
					}
					save_scope_as = zg361_b1_bank_ticket_owner
					save_scope_value_as = { name = zg361_b1_bank_ticket_season value = var:zg361_b1_bank_season }
					save_scope_value_as = { name = zg361_b1_bank_ticket_case value = var:zg361_b1_bank_case_serial }
					save_scope_value_as = { name = zg361_b1_bank_ticket_state value = var:zg361_b1_bank_state }
					trigger_event = { id = zg361b1.110 days = 335 }
				}
				scope:zg361_b1_registering_manager = {
					set_variable = { name = zg361_b1_bank_superior value = scope:zg361_b1_bank_owner }
					set_variable = { name = zg361_b1_bank_season value = scope:zg361_b1_bank_owner.var:zg361_b1_bank_season }
				}
			}
		}
	}
}

# Exact 30/60/10 largest-remainder allocator. Raw values are stored as integer
# numerators over the frozen denominator 10, so CK3 never depends on binary
# floating-point ties. Stable tie priority is TOP, MIDDLE, BOTTOM.
zg361_b1_compute_exact_quota_effect = {
	# ROUNDING_SCOPE is mandatory: 1 = this manager's local book, 2 = the
	# common-superior pooled book.  A ruler can own both roles, so their durable
	# five-tuples and rotation cursors must never share singleton storage.
	remove_variable = zg361_b1_m138_receipt_serial
	set_variable = { name = zg361_b1_quota_rounding_work_scope value = $ROUNDING_SCOPE$ }
	set_variable = { name = zg361_b1_quota_rounding_work_route value = 3 }
	if = {
		limit = { var:zg361_b1_quota_rounding_work_scope = 1 has_variable = zg361_b1_m138_mode }
		set_variable = { name = zg361_b1_quota_rounding_work_route value = var:zg361_b1_m138_mode }
		set_variable = { name = zg361_b1_quota_rounding_local_object_available value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_local_state value = 0 }
		remove_variable = zg361_b1_quota_rounding_local_owner
		remove_variable = zg361_b1_quota_rounding_local_subject
		set_variable = { name = zg361_b1_quota_rounding_local_cycle value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_local_case value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_local_blackbox_risk value = 0 }
		if = {
			limit = { var:zg361_b1_quota_rounding_work_route != 3 }
			set_variable = { name = zg361_b1_quota_rounding_local_object_available value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_local_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 38 } }
			set_variable = { name = zg361_b1_quota_rounding_local_owner value = this }
			set_variable = { name = zg361_b1_quota_rounding_local_subject value = this }
			set_variable = { name = zg361_b1_quota_rounding_local_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_quota_rounding_local_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_quota_rounding_local_state value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_local_route value = var:zg361_b1_quota_rounding_work_route }
			set_variable = { name = zg361_b1_quota_rounding_local_team_n value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_local_team_1 value = this }
			set_variable = { name = zg361_b1_quota_rounding_local_remainder_team value = this }
			set_variable = { name = zg361_b1_quota_rounding_local_rotation_advance value = 1 }
			if = {
				limit = {
					has_variable = zg361_b1_quota_rounding_local_rotation_cycle
					var:zg361_b1_quota_rounding_local_rotation_cycle = var:zg361_b1_cycle_serial
					var:zg361_b1_quota_rounding_local_rotation_case = var:zg361_b1_case_serial
				}
				set_variable = { name = zg361_b1_quota_rounding_local_rotation_advance value = 0 }
			}
			if = {
				limit = { var:zg361_b1_quota_rounding_local_rotation_advance = 1 }
				if = { limit = { NOT = { has_variable = zg361_b1_quota_rounding_local_rotation_cursor } } set_variable = { name = zg361_b1_quota_rounding_local_rotation_cursor value = 1 } }
				else = { change_variable = { name = zg361_b1_quota_rounding_local_rotation_cursor add = 1 } }
				if = { limit = { var:zg361_b1_quota_rounding_local_rotation_cursor > 2 } set_variable = { name = zg361_b1_quota_rounding_local_rotation_cursor value = 1 } }
				set_variable = { name = zg361_b1_quota_rounding_local_rotation_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_quota_rounding_local_rotation_case value = var:zg361_b1_case_serial }
			}
			if = { limit = { var:zg361_b1_quota_rounding_work_route = 2 } set_variable = { name = zg361_b1_quota_rounding_local_chair value = this } set_variable = { name = zg361_b1_quota_rounding_local_blackbox_risk value = 1 } }
		}
	}
	else_if = {
		limit = { var:zg361_b1_quota_rounding_work_scope = 2 has_variable = zg361_b1_bank_m138_mode }
		set_variable = { name = zg361_b1_quota_rounding_work_route value = var:zg361_b1_bank_m138_mode }
		set_variable = { name = zg361_b1_quota_rounding_bank_object_available value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_bank_state value = 0 }
		remove_variable = zg361_b1_quota_rounding_bank_owner
		remove_variable = zg361_b1_quota_rounding_bank_subject
		set_variable = { name = zg361_b1_quota_rounding_bank_cycle value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_bank_case value = 0 }
		set_variable = { name = zg361_b1_quota_rounding_bank_blackbox_risk value = 0 }
		if = {
			limit = { var:zg361_b1_quota_rounding_work_route != 3 }
			set_variable = { name = zg361_b1_quota_rounding_bank_object_available value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_bank_object_id value = { value = var:zg361_b1_bank_case_serial multiply = 100 add = 38 } }
			set_variable = { name = zg361_b1_quota_rounding_bank_owner value = this }
			set_variable = { name = zg361_b1_quota_rounding_bank_subject value = this }
			set_variable = { name = zg361_b1_quota_rounding_bank_cycle value = var:zg361_b1_bank_season }
			set_variable = { name = zg361_b1_quota_rounding_bank_case value = var:zg361_b1_bank_case_serial }
			set_variable = { name = zg361_b1_quota_rounding_bank_state value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_bank_route value = var:zg361_b1_quota_rounding_work_route }
			set_variable = { name = zg361_b1_quota_rounding_bank_team_n value = 1 }
			set_variable = { name = zg361_b1_quota_rounding_bank_team_1 value = this }
			set_variable = { name = zg361_b1_quota_rounding_bank_remainder_team value = this }
			set_variable = { name = zg361_b1_quota_rounding_bank_rotation_advance value = 1 }
			if = {
				limit = {
					has_variable = zg361_b1_quota_rounding_bank_rotation_cycle
					var:zg361_b1_quota_rounding_bank_rotation_cycle = var:zg361_b1_bank_season
					var:zg361_b1_quota_rounding_bank_rotation_case = var:zg361_b1_bank_case_serial
				}
				set_variable = { name = zg361_b1_quota_rounding_bank_rotation_advance value = 0 }
			}
			if = {
				limit = { var:zg361_b1_quota_rounding_bank_rotation_advance = 1 }
				if = { limit = { NOT = { has_variable = zg361_b1_quota_rounding_bank_rotation_cursor } } set_variable = { name = zg361_b1_quota_rounding_bank_rotation_cursor value = 1 } }
				else = { change_variable = { name = zg361_b1_quota_rounding_bank_rotation_cursor add = 1 } }
				if = { limit = { var:zg361_b1_quota_rounding_bank_rotation_cursor > 2 } set_variable = { name = zg361_b1_quota_rounding_bank_rotation_cursor value = 1 } }
				set_variable = { name = zg361_b1_quota_rounding_bank_rotation_cycle value = var:zg361_b1_bank_season }
				set_variable = { name = zg361_b1_quota_rounding_bank_rotation_case value = var:zg361_b1_bank_case_serial }
			}
			if = { limit = { var:zg361_b1_quota_rounding_work_route = 2 } set_variable = { name = zg361_b1_quota_rounding_bank_chair value = this } set_variable = { name = zg361_b1_quota_rounding_bank_blackbox_risk value = 1 } }
		}
	}
	set_variable = { name = zg361_b1_quota_cohort_size value = $COHORT_SIZE$ }
	set_variable = { name = zg361_b1_quota_denominator value = 10 }
	set_variable = { name = zg361_b1_quota_top_raw_numerator value = { value = var:zg361_b1_quota_cohort_size multiply = 3 } }
	set_variable = { name = zg361_b1_quota_middle_raw_numerator value = { value = var:zg361_b1_quota_cohort_size multiply = 6 } }
	set_variable = { name = zg361_b1_quota_bottom_raw_numerator value = var:zg361_b1_quota_cohort_size }
	set_variable = { name = zg361_b1_quota_top_floor value = { value = var:zg361_b1_quota_top_raw_numerator divide = 10 floor = yes } }
	set_variable = { name = zg361_b1_quota_middle_floor value = { value = var:zg361_b1_quota_middle_raw_numerator divide = 10 floor = yes } }
	set_variable = { name = zg361_b1_quota_bottom_floor value = { value = var:zg361_b1_quota_bottom_raw_numerator divide = 10 floor = yes } }
	set_variable = {
		name = zg361_b1_quota_top_remainder
		value = { value = var:zg361_b1_quota_top_raw_numerator subtract = { value = var:zg361_b1_quota_top_floor multiply = 10 } }
	}
	set_variable = {
		name = zg361_b1_quota_middle_remainder
		value = { value = var:zg361_b1_quota_middle_raw_numerator subtract = { value = var:zg361_b1_quota_middle_floor multiply = 10 } }
	}
	set_variable = {
		name = zg361_b1_quota_bottom_remainder
		value = { value = var:zg361_b1_quota_bottom_raw_numerator subtract = { value = var:zg361_b1_quota_bottom_floor multiply = 10 } }
	}
	set_variable = {
		name = zg361_b1_quota_remainder_slots
		value = {
			value = var:zg361_b1_quota_cohort_size
			subtract = var:zg361_b1_quota_top_floor
			subtract = var:zg361_b1_quota_middle_floor
			subtract = var:zg361_b1_quota_bottom_floor
		}
	}
	set_variable = { name = zg361_b1_quota_top_award value = 0 }
	set_variable = { name = zg361_b1_quota_middle_award value = 0 }
	set_variable = { name = zg361_b1_quota_bottom_award value = 0 }
	# First remainder slot: >= implements the frozen TOP-first tie break.
	if = {
		limit = { var:zg361_b1_quota_remainder_slots >= 1 }
		if = {
			limit = {
				var:zg361_b1_quota_top_remainder >= var:zg361_b1_quota_middle_remainder
				var:zg361_b1_quota_top_remainder >= var:zg361_b1_quota_bottom_remainder
			}
			set_variable = { name = zg361_b1_quota_top_award value = 1 }
			set_variable = { name = zg361_b1_quota_top_remainder_cursor value = -1 }
			set_variable = { name = zg361_b1_quota_middle_remainder_cursor value = var:zg361_b1_quota_middle_remainder }
			set_variable = { name = zg361_b1_quota_bottom_remainder_cursor value = var:zg361_b1_quota_bottom_remainder }
		}
		else_if = {
			limit = { var:zg361_b1_quota_middle_remainder >= var:zg361_b1_quota_bottom_remainder }
			set_variable = { name = zg361_b1_quota_middle_award value = 1 }
			set_variable = { name = zg361_b1_quota_top_remainder_cursor value = var:zg361_b1_quota_top_remainder }
			set_variable = { name = zg361_b1_quota_middle_remainder_cursor value = -1 }
			set_variable = { name = zg361_b1_quota_bottom_remainder_cursor value = var:zg361_b1_quota_bottom_remainder }
		}
		else = {
			set_variable = { name = zg361_b1_quota_bottom_award value = 1 }
			set_variable = { name = zg361_b1_quota_top_remainder_cursor value = var:zg361_b1_quota_top_remainder }
			set_variable = { name = zg361_b1_quota_middle_remainder_cursor value = var:zg361_b1_quota_middle_remainder }
			set_variable = { name = zg361_b1_quota_bottom_remainder_cursor value = -1 }
		}
	}
	# Second slot repeats the same stable ordering after masking the winner.
	if = {
		limit = { var:zg361_b1_quota_remainder_slots >= 2 }
		if = {
			limit = {
				var:zg361_b1_quota_top_remainder_cursor >= var:zg361_b1_quota_middle_remainder_cursor
				var:zg361_b1_quota_top_remainder_cursor >= var:zg361_b1_quota_bottom_remainder_cursor
			}
			set_variable = { name = zg361_b1_quota_top_award value = 1 }
		}
		else_if = {
			limit = { var:zg361_b1_quota_middle_remainder_cursor >= var:zg361_b1_quota_bottom_remainder_cursor }
			set_variable = { name = zg361_b1_quota_middle_award value = 1 }
		}
		else = { set_variable = { name = zg361_b1_quota_bottom_award value = 1 } }
	}
	# A/B may decide which real team owns the indivisible remainder receipt, but
	# neither route is allowed to rewrite the exact 3/6/1 band counts.  Team
	# identity is attached by the local/common-superior caller below.
	set_variable = { name = zg361_b1_quota_top_rounded value = { value = var:zg361_b1_quota_top_floor add = var:zg361_b1_quota_top_award } }
	set_variable = { name = zg361_b1_quota_middle_rounded value = { value = var:zg361_b1_quota_middle_floor add = var:zg361_b1_quota_middle_award } }
	set_variable = { name = zg361_b1_quota_bottom_rounded value = { value = var:zg361_b1_quota_bottom_floor add = var:zg361_b1_quota_bottom_award } }
	set_variable = { name = zg361_b1_quota_top_slots value = var:zg361_b1_quota_top_rounded }
	set_variable = { name = zg361_b1_quota_middle_slots value = var:zg361_b1_quota_middle_rounded }
	set_variable = { name = zg361_b1_quota_bottom_slots value = var:zg361_b1_quota_bottom_rounded }
	set_variable = { name = zg361_b1_quota_forced_distribution value = 1 }
	if = {
		limit = { var:zg361_b1_quota_cohort_size < 3 }
		set_variable = { name = zg361_b1_quota_top_slots value = 0 }
		set_variable = { name = zg361_b1_quota_middle_slots value = var:zg361_b1_quota_cohort_size }
		set_variable = { name = zg361_b1_quota_bottom_slots value = 0 }
		set_variable = { name = zg361_b1_quota_forced_distribution value = 0 }
	}
	set_variable = {
		name = zg361_b1_quota_conservation_check
		value = { value = var:zg361_b1_quota_top_slots add = var:zg361_b1_quota_middle_slots add = var:zg361_b1_quota_bottom_slots }
	}
	if = {
		limit = { var:zg361_b1_quota_rounding_work_scope = 1 }
		set_variable = { name = zg361_b1_quota_rounding_local_method value = var:zg361_b1_quota_rounding_work_route }
	}
	else_if = {
		limit = { var:zg361_b1_quota_rounding_work_scope = 2 }
		set_variable = { name = zg361_b1_quota_rounding_bank_method value = var:zg361_b1_quota_rounding_work_route }
	}
	# Reference vectors: 0=0/0/0, 1=0/1/0, 2=0/2/0, 3=1/2/0,
	# 4=1/3/0, 7=2/4/1, 14=4/9/1, 23=7/14/2.
}

# Compare the frozen variable list with current ownership immediately before
# quota calculation. A departure is excluded once and leaves a reconstructible
# before/after/reason/actor/approver receipt; the quota candidate filters below
# consume zg361_b1_roster_included, so this is not a write-only audit field.
zg361_b1_audit_frozen_roster_effect = {
	if = {
		limit = {
			zg361_is_celestial_liege_trigger = yes
			OR = { var:zg361_b1_cycle_state = 3 var:zg361_b1_cycle_state = 5 var:zg361_b1_cycle_state = 6 }
		}
		save_temporary_scope_as = zg361_b1_roster_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_b1_roster_included
					var:zg361_b1_case_owner = scope:zg361_b1_roster_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_roster_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_roster_manager.var:zg361_b1_case_serial
					OR = { var:zg361_b1_case_state = 3 var:zg361_b1_case_state = 5 }
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					OR = {
						is_alive = no
						is_landed = no
						AND = {
							NOT = { liege = scope:zg361_b1_roster_manager }
							scope:zg361_b1_roster_manager.var:zg361_b1_m140_mode != 1
						}
					}
				}
				set_variable = { name = zg361_b1_roster_change_before value = 1 }
				set_variable = { name = zg361_b1_roster_change_after value = 0 }
				set_variable = { name = zg361_b1_roster_change_reason value = 1 }
				if = {
					limit = { is_alive = no }
					set_variable = { name = zg361_b1_roster_change_reason value = 1 }
				}
				else_if = {
					limit = { is_landed = no }
					set_variable = { name = zg361_b1_roster_change_reason value = 2 }
				}
				else = { set_variable = { name = zg361_b1_roster_change_reason value = 3 } }
				set_variable = { name = zg361_b1_roster_change_actor value = scope:zg361_b1_roster_manager }
				set_variable = { name = zg361_b1_roster_change_approver value = scope:zg361_b1_roster_manager }
				set_variable = { name = zg361_b1_roster_change_year value = current_year }
				change_variable = { name = zg361_b1_roster_change_version add = 1 }
				set_variable = { name = zg361_b1_roster_amendment value = 1 }
				set_variable = { name = zg361_b1_roster_reopen_required value = 1 }
				set_variable = { name = zg361_b1_roster_included value = 0 }
				set_variable = { name = zg361_b1_leaver_route value = 1 }
				scope:zg361_b1_roster_manager = {
					change_variable = { name = zg361_b1_roster_amendment_n add = 1 }
					change_variable = { name = zg361_b1_roster_audit_version add = 1 }
					set_variable = { name = zg361_b1_roster_reopen_required value = 1 }
				}
			}
		}
		set_variable = { name = zg361_b1_roster_audited_serial value = var:zg361_b1_case_serial }
	}
}

# After the D+0 list is locked, compare it with the live direct-vassal roster at
# the facts boundary.  A legal new arrival receives a full five-field case and
# a reconstructible amendment; a prior departure creates a backfill vacancy,
# otherwise the arrival is an explicit late join.  Both routes enter the real
# denominator and force quota reconstruction.
zg361_b1_audit_locked_roster_additions_effect = {
	zg361_b1_audit_frozen_roster_effect = yes
	set_variable = { name = zg361_b1_roster_backfill_needed value = var:zg361_b1_roster_amendment_n }
	save_temporary_scope_as = zg361_b1_roster_add_manager
	every_vassal = {
		limit = { zg361_is_reviewable_vassal_trigger = yes }
		save_temporary_scope_as = zg361_b1_roster_add_subject
		if = {
			limit = {
				scope:zg361_b1_roster_add_manager = {
					OR = { var:zg361_b1_subject_n < 80 var:zg361_b1_roster_backfill_needed >= 1 }
					trigger_if = {
						limit = { has_variable_list = zg361_b1_subjects }
						NOT = {
							is_target_in_variable_list = {
								name = zg361_b1_subjects
								target = scope:zg361_b1_roster_add_subject
							}
						}
					}
					trigger_else = { always = yes }
				}
			}
			# A character may already own an active old-manager case.  Freeze that
			# namespace before any B-route initialization; A keeps the old quota
			# owner, B opens one new-manager segment, and C creates no reorg object.
			set_variable = { name = zg361_b1_reorg_transfer_detected value = 0 }
			set_variable = { name = zg361_b1_reorg_replay_detected value = 0 }
			set_variable = { name = zg361_b1_reorg_should_add value = 1 }
			if = {
				limit = {
					has_variable = zg361_b1_reorg_archive_case
					has_variable = zg361_b1_reorg_new_manager
					var:zg361_b1_reorg_new_manager = scope:zg361_b1_roster_add_manager
					var:zg361_b1_reorg_object_available = 1
					var:zg361_b1_reorg_object_subject = this
					var:zg361_b1_reorg_object_state = 2
					OR = {
						AND = {
							var:zg361_b1_reorg_route = 1
							var:zg361_b1_reorg_archive_case = var:zg361_b1_case_serial
							var:zg361_b1_reorg_archive_subject = this
							var:zg361_b1_reorg_object_owner = var:zg361_b1_reorg_archive_owner
							var:zg361_b1_reorg_object_cycle = var:zg361_b1_reorg_archive_cycle
							var:zg361_b1_reorg_object_case = var:zg361_b1_reorg_archive_case
						}
						AND = {
							var:zg361_b1_reorg_route = 2
							var:zg361_b1_reorg_object_owner = scope:zg361_b1_roster_add_manager
							var:zg361_b1_reorg_object_cycle = var:zg361_b1_cycle_serial
							var:zg361_b1_reorg_object_case = var:zg361_b1_case_serial
						}
					}
				}
				set_variable = { name = zg361_b1_reorg_replay_detected value = 1 }
				set_variable = { name = zg361_b1_reorg_should_add value = 0 }
			}
			if = {
				limit = {
					var:zg361_b1_reorg_replay_detected = 0
					scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode != 3
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					var:zg361_b1_case_subject = this
					var:zg361_b1_case_active = 1
					OR = { var:zg361_b1_case_state = 3 var:zg361_b1_case_state = 5 }
					NOT = { var:zg361_b1_case_owner = scope:zg361_b1_roster_add_manager }
					trigger_if = {
						limit = { has_variable = zg361_b1_reorg_archive_case }
						NOT = { var:zg361_b1_reorg_archive_case = var:zg361_b1_case_serial }
					}
					trigger_else = { always = yes }
				}
				set_variable = { name = zg361_b1_reorg_transfer_detected value = 1 }
				set_variable = { name = zg361_b1_reorg_archive_owner value = var:zg361_b1_case_owner }
				set_variable = { name = zg361_b1_reorg_archive_subject value = this }
				set_variable = { name = zg361_b1_reorg_archive_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_reorg_archive_case value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_reorg_archive_state value = var:zg361_b1_case_state }
				set_variable = { name = zg361_b1_reorg_archive_evidence_early value = var:zg361_b1_evidence_early }
				set_variable = { name = zg361_b1_reorg_archive_evidence_mid value = var:zg361_b1_evidence_mid }
				set_variable = { name = zg361_b1_reorg_archive_evidence_late value = var:zg361_b1_evidence_late }
				set_variable = { name = zg361_b1_reorg_archive_quota_grade value = 0 }
				if = {
					limit = { has_variable = zg361_pending_grade }
					set_variable = { name = zg361_b1_reorg_archive_quota_grade value = var:zg361_pending_grade }
				}
				set_variable = { name = zg361_b1_reorg_old_manager value = var:zg361_b1_case_owner }
				set_variable = { name = zg361_b1_reorg_new_manager value = scope:zg361_b1_roster_add_manager }
				# The transfer is first observed at the facts boundary; exact tenure is
				# unknowable from script state, so never manufacture 300/65-day claims.
				set_variable = { name = zg361_b1_reorg_service_days value = 0 }
				set_variable = { name = zg361_b1_reorg_service_days_observed value = 0 }
				set_variable = { name = zg361_b1_reorg_observation_year value = current_year }
			}
			if = {
				limit = {
					var:zg361_b1_reorg_transfer_detected = 1
					scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode = 1
				}
				set_variable = { name = zg361_b1_reorg_should_add value = 0 }
				set_variable = { name = zg361_b1_reorg_object_available value = 1 }
				set_variable = { name = zg361_b1_reorg_route value = 1 }
				set_variable = { name = zg361_b1_reorg_object_owner value = var:zg361_b1_reorg_archive_owner }
				set_variable = { name = zg361_b1_reorg_object_subject value = this }
				set_variable = { name = zg361_b1_reorg_object_cycle value = var:zg361_b1_reorg_archive_cycle }
				set_variable = { name = zg361_b1_reorg_object_case value = var:zg361_b1_reorg_archive_case }
				set_variable = { name = zg361_b1_reorg_object_state value = 2 }
				set_variable = { name = zg361_b1_reorg_quota_owner value = var:zg361_b1_reorg_archive_owner }
				set_variable = { name = zg361_b1_reorg_new_evidence_segment_start value = zg361_kpi_value }
				set_variable = { name = zg361_b1_reorg_new_evidence_segment_end value = zg361_kpi_value }
				set_variable = { name = zg361_b1_reorg_old_evidence_hash value = { value = var:zg361_b1_reorg_archive_evidence_early multiply = 10000 add = { value = var:zg361_b1_reorg_archive_evidence_mid multiply = 100 } add = var:zg361_b1_reorg_archive_evidence_late } }
				set_variable = { name = zg361_b1_reorg_new_evidence_hash value = zg361_kpi_value }
				set_variable = { name = zg361_b1_reorg_new_observation_n value = 1 }
				set_variable = { name = zg361_b1_reorg_new_evidence_segment_available value = 0 }
				set_variable = { name = zg361_b1_reorg_allocation_occupied_slots value = 1 }
				set_variable = { name = zg361_b1_reorg_allocation_evidence_count value = 3 }
				set_variable = { name = zg361_b1_reorg_allocation_receipt_state value = 1 }
				set_variable = { name = zg361_b1_roster_included value = 1 }
				var:zg361_b1_reorg_archive_owner = { set_variable = { name = zg361_b1_roster_reopen_required value = 1 } }
				set_variable = { name = zg361_b1_m140_receipt_serial value = var:zg361_b1_reorg_object_case }
			}
			if = {
				limit = { var:zg361_b1_reorg_should_add = 1 }
				zg361_b1_initialize_subject_case_effect = yes
				set_variable = { name = zg361_b1_case_state value = 3 }
				set_variable = { name = zg361_b1_roster_change_before value = 0 }
				set_variable = { name = zg361_b1_roster_change_after value = 1 }
				set_variable = { name = zg361_b1_roster_change_reason value = 4 }
				set_variable = { name = zg361_b1_roster_change_actor value = scope:zg361_b1_roster_add_manager }
				set_variable = { name = zg361_b1_roster_change_approver value = scope:zg361_b1_roster_add_manager }
				set_variable = { name = zg361_b1_roster_change_year value = current_year }
				set_variable = { name = zg361_b1_roster_change_version value = 1 }
				set_variable = { name = zg361_b1_roster_amendment value = 1 }
				set_variable = { name = zg361_b1_roster_reopen_required value = 1 }
				set_variable = { name = zg361_b1_late_join_route value = 1 }
				set_variable = { name = zg361_b1_backfill_route value = 0 }
				set_variable = { name = zg361_b1_evidence_early_available value = 0 }
				set_variable = { name = zg361_b1_evidence_mid_available value = 1 }
				set_variable = { name = zg361_b1_evidence_early value = 0 }
				set_variable = { name = zg361_b1_evidence_mid value = zg361_kpi_value }
				set_variable = { name = zg361_b1_self_score value = var:zg361_b1_evidence_mid }
				add_character_flag = zg361_newcomer_this_cycle
				set_variable = { name = zg361_b1_newcomer_route value = 1 }
				if = {
					limit = {
						var:zg361_b1_reorg_transfer_detected = 1
						scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode = 2
					}
					set_variable = { name = zg361_b1_reorg_object_available value = 1 }
					set_variable = { name = zg361_b1_reorg_route value = 2 }
					set_variable = { name = zg361_b1_reorg_old_manager value = var:zg361_b1_reorg_archive_owner }
					set_variable = { name = zg361_b1_reorg_new_manager value = scope:zg361_b1_roster_add_manager }
					set_variable = { name = zg361_b1_reorg_service_days value = 0 }
					set_variable = { name = zg361_b1_reorg_service_days_observed value = 0 }
					set_variable = { name = zg361_b1_reorg_observation_year value = current_year }
					set_variable = { name = zg361_b1_reorg_object_owner value = scope:zg361_b1_roster_add_manager }
					set_variable = { name = zg361_b1_reorg_object_subject value = this }
					set_variable = { name = zg361_b1_reorg_object_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_reorg_object_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_reorg_object_state value = 2 }
					set_variable = { name = zg361_b1_reorg_quota_owner value = scope:zg361_b1_roster_add_manager }
					set_variable = { name = zg361_b1_reorg_new_evidence_segment_start value = var:zg361_b1_evidence_mid }
					set_variable = { name = zg361_b1_reorg_new_evidence_segment_end value = var:zg361_b1_evidence_mid }
					set_variable = { name = zg361_b1_reorg_old_evidence_hash value = { value = var:zg361_b1_reorg_archive_evidence_early multiply = 10000 add = { value = var:zg361_b1_reorg_archive_evidence_mid multiply = 100 } add = var:zg361_b1_reorg_archive_evidence_late } }
					set_variable = { name = zg361_b1_reorg_new_evidence_hash value = var:zg361_b1_evidence_mid }
					set_variable = { name = zg361_b1_reorg_new_observation_n value = 1 }
					set_variable = { name = zg361_b1_reorg_new_evidence_segment_available value = 0 }
					set_variable = { name = zg361_b1_reorg_allocation_occupied_slots value = 1 }
					set_variable = { name = zg361_b1_reorg_allocation_evidence_count value = 3 }
					set_variable = { name = zg361_b1_reorg_allocation_receipt_state value = 1 }
					set_variable = { name = zg361_b1_m140_receipt_serial value = var:zg361_b1_reorg_object_case }
				}
				if = {
					limit = { scope:zg361_b1_roster_add_manager.var:zg361_b1_roster_backfill_needed >= 1 }
					set_variable = { name = zg361_b1_roster_change_reason value = 5 }
					set_variable = { name = zg361_b1_late_join_route value = 0 }
					set_variable = { name = zg361_b1_backfill_route value = 1 }
					scope:zg361_b1_roster_add_manager = { change_variable = { name = zg361_b1_roster_backfill_needed add = -1 } }
				}
				scope:zg361_b1_roster_add_manager = {
					if = {
						limit = { scope:zg361_b1_roster_add_subject.var:zg361_b1_backfill_route = 0 }
						change_variable = { name = zg361_b1_subject_n add = 1 }
					}
					change_variable = { name = zg361_b1_roster_amendment_n add = 1 }
					change_variable = { name = zg361_b1_roster_audit_version add = 1 }
					set_variable = { name = zg361_b1_roster_reopen_required value = 1 }
					add_to_variable_list = { name = zg361_b1_subjects target = scope:zg361_b1_roster_add_subject }
				}
				set_variable = { name = zg361_b1_roster_frozen_order value = scope:zg361_b1_roster_add_manager.var:zg361_b1_subject_n }
			}
		}
	}
	set_variable = { name = zg361_b1_roster_additions_audited_serial value = var:zg361_b1_case_serial }
}

zg361_b1_rebuild_local_quota_effect = {
	zg361_b1_audit_frozen_roster_effect = yes
	set_variable = { name = zg361_b1_local_candidate_n value = 0 }
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
				has_variable = zg361_b1_case_active
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				has_variable = zg361_pending_grade
				has_variable = zg361_b1_calibration_score
				var:zg361_b1_roster_included = 1
				OR = {
					NOT = { has_variable = zg361_b1_reorg_quota_owner }
					var:zg361_b1_reorg_quota_owner = root
				}
			}
			add_to_list = zg361_b1_local_candidates
			root = { change_variable = { name = zg361_b1_local_candidate_n add = 1 } }
		}
	}
	zg361_b1_compute_exact_quota_effect = { COHORT_SIZE = var:zg361_b1_local_candidate_n ROUNDING_SCOPE = 1 }
	if = {
		limit = { var:zg361_b1_quota_rounding_local_object_available = 1 }
		set_variable = { name = zg361_b1_quota_rounding_local_team_n value = 1 }
		set_variable = { name = zg361_b1_quota_rounding_local_team_1 value = this }
		set_variable = { name = zg361_b1_quota_rounding_local_remainder_team value = this }
		set_variable = { name = zg361_b1_quota_rounding_local_affected_team value = this }
		set_variable = { name = zg361_b1_quota_rounding_local_operation_seal value = { value = var:zg361_b1_cycle_serial multiply = 100000 add = var:zg361_b1_case_serial } }
		set_variable = { name = zg361_b1_quota_rounding_local_state value = 2 }
	}
	if = {
		limit = { var:zg361_b1_m138_mode != 3 var:zg361_b1_quota_rounding_local_object_available = 1 }
		set_variable = { name = zg361_b1_m138_receipt_serial value = var:zg361_b1_quota_rounding_local_case }
	}
	set_variable = { name = zg361_b1_local_top_slots value = var:zg361_b1_quota_top_slots }
	set_variable = { name = zg361_b1_local_middle_slots value = var:zg361_b1_quota_middle_slots }
	set_variable = { name = zg361_b1_local_bottom_slots value = var:zg361_b1_quota_bottom_slots }
	set_variable = { name = zg361_b1_quota_built_serial value = var:zg361_b1_case_serial }
	if = {
		limit = { var:zg361_b1_local_candidate_n >= 1 }
		set_variable = { name = zg361_b1_local_rank_cursor value = 0 }
		ordered_in_list = {
			list = zg361_b1_local_candidates
			order_by = var:zg361_b1_calibration_score
			max = list_size:zg361_b1_local_candidates
			root = { change_variable = { name = zg361_b1_local_rank_cursor add = 1 } }
			set_variable = { name = zg361_rank value = root.var:zg361_b1_local_rank_cursor }
			set_variable = { name = zg361_b1_local_rank value = root.var:zg361_b1_local_rank_cursor }
			set_variable = { name = zg361_pending_grade value = 2 }
			set_variable = { name = zg361_b1_newcomer_forced_bottom value = 0 }
		}
		set_variable = { name = zg361_b1_local_bottom_candidate_n value = 0 }
		set_variable = { name = zg361_b1_local_bottom_assigned value = 0 }
		set_variable = { name = zg361_b1_newcomer_bottom_exception value = 0 }
		every_in_list = {
			list = zg361_b1_local_candidates
			limit = { NOT = { has_character_flag = zg361_newcomer_this_cycle } }
			add_to_list = zg361_b1_local_bottom_candidates
			root = { change_variable = { name = zg361_b1_local_bottom_candidate_n add = 1 } }
		}
		set_variable = { name = zg361_b1_local_bottom_cursor value = 0 }
		if = {
			limit = {
				var:zg361_b1_local_bottom_slots >= 1
				var:zg361_b1_local_bottom_candidate_n >= 1
			}
			ordered_in_list = {
				list = zg361_b1_local_bottom_candidates
				order_by = var:zg361_b1_local_rank
				max = list_size:zg361_b1_local_bottom_candidates
				if = {
					limit = { root.var:zg361_b1_local_bottom_assigned < root.var:zg361_b1_local_bottom_slots }
					set_variable = { name = zg361_pending_grade value = 1 }
					root = { change_variable = { name = zg361_b1_local_bottom_assigned add = 1 } }
				}
				root = { change_variable = { name = zg361_b1_local_bottom_cursor add = 1 } }
			}
		}
		# Prefer protecting every newcomer, but quota conservation wins when the
		# frozen roster has fewer bottom-eligible incumbents than bottom slots.
		# The explicit exception receipt makes that otherwise-impossible case
		# visible instead of silently shrinking the exact LR bottom count.
		if = {
			limit = { var:zg361_b1_local_bottom_assigned < var:zg361_b1_local_bottom_slots }
			set_variable = { name = zg361_b1_newcomer_bottom_exception value = 1 }
			ordered_in_list = {
				list = zg361_b1_local_candidates
				order_by = var:zg361_b1_local_rank
				max = list_size:zg361_b1_local_candidates
				limit = { var:zg361_pending_grade = 2 }
				if = {
					limit = { root.var:zg361_b1_local_bottom_assigned < root.var:zg361_b1_local_bottom_slots }
					set_variable = { name = zg361_pending_grade value = 1 }
					set_variable = { name = zg361_b1_newcomer_forced_bottom value = 1 }
					root = { change_variable = { name = zg361_b1_local_bottom_assigned add = 1 } }
				}
			}
		}
		# Assign TOP only after BOTTOM is frozen. This prevents newcomer protection
		# from overwriting a TOP without promoting a replacement.
		set_variable = { name = zg361_b1_local_top_assigned value = 0 }
		if = {
			limit = { var:zg361_b1_local_top_slots >= 1 }
			ordered_in_list = {
				list = zg361_b1_local_candidates
				order_by = var:zg361_b1_calibration_score
				max = list_size:zg361_b1_local_candidates
				limit = { var:zg361_pending_grade = 2 }
				if = {
					limit = { root.var:zg361_b1_local_top_assigned < root.var:zg361_b1_local_top_slots }
					set_variable = { name = zg361_pending_grade value = 3 }
					root = { change_variable = { name = zg361_b1_local_top_assigned add = 1 } }
				}
			}
		}
		every_in_list = {
			list = zg361_b1_local_candidates
			set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
			set_variable = {
				name = zg361_b1_shadow_to_quota_delta
				value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade }
			}
			set_variable = { name = zg361_b1_forced_down value = 0 }
			if = {
				limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
				set_variable = { name = zg361_b1_forced_down value = 1 }
			}
		}
		# Recount the actual writes instead of claiming nominal targets. Under the
		# frozen roster/newcomer policy these equal the pre-shadow counts; the
		# explicit recount also keeps an old/malformed save honest.
		set_variable = { name = zg361_pending_375_n value = 0 }
		set_variable = { name = zg361_pending_35_n value = 0 }
		set_variable = { name = zg361_pending_325_n value = 0 }
		every_in_list = {
			list = zg361_b1_local_candidates
			if = {
				limit = { var:zg361_pending_grade = 3 }
				root = { change_variable = { name = zg361_pending_375_n add = 1 } }
			}
			else_if = {
				limit = { var:zg361_pending_grade = 1 }
				root = { change_variable = { name = zg361_pending_325_n add = 1 } }
			}
			else = { root = { change_variable = { name = zg361_pending_35_n add = 1 } } }
		}
		set_variable = { name = zg361_top_cut value = var:zg361_b1_local_top_slots }
		set_variable = { name = zg361_top_cut_next value = { value = var:zg361_b1_local_top_slots add = 1 } }
		set_variable = { name = zg361_bottom_slots value = var:zg361_b1_local_bottom_slots }
		change_variable = { name = zg361_b1_quota_book_version add = 1 }
		if = {
			limit = { var:zg361_b1_roster_reopen_required = 1 }
			set_variable = { name = zg361_b1_quota_roster_amendment_version value = var:zg361_b1_roster_audit_version }
			set_variable = { name = zg361_b1_quota_rebuilt_for_roster value = 1 }
			set_variable = { name = zg361_b1_roster_reopen_required value = 0 }
		}
		debug_log = "ZG361B1: local quota reranked by bounded post-shadow calibration score"
	}
}

# Consume one open responsibility debt only when its exact due cycle has
# arrived. The grade write is guarded by owner/subject/cycle/case/state and the
# debt state flips to settled, so replaying either the quota close or deadline
# cannot repay twice.
zg361_b1_settle_due_debt_effect = {
	save_temporary_scope_as = zg361_b1_debt_manager
	if = {
		limit = {
			zg361_is_celestial_liege_trigger = yes
			has_variable = zg361_b1_quota_debt_state
			has_variable = zg361_b1_quota_debt_due_cycle
			has_variable = zg361_b1_quota_debt_kind
			has_variable = zg361_b1_quota_debt_creditor
			has_variable = zg361_b1_quota_debt_source_trade
			has_variable = zg361_b1_quota_debt_liability
			var:zg361_b1_quota_debt_state = 1
			var:zg361_b1_cycle_serial >= var:zg361_b1_quota_debt_due_cycle
			var:zg361_b1_quota_debt_creditor = {
				has_variable = zg361_b1_quota_credit_state
				has_variable = zg361_b1_quota_credit_creditor
				has_variable = zg361_b1_quota_credit_debtor
				has_variable = zg361_b1_quota_credit_due_cycle
				has_variable = zg361_b1_quota_credit_source_trade
				has_variable = zg361_b1_quota_credit_liability
				var:zg361_b1_quota_credit_state = 1
				var:zg361_b1_quota_credit_creditor = this
				var:zg361_b1_quota_credit_debtor = scope:zg361_b1_debt_manager
				var:zg361_b1_quota_credit_due_cycle = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_due_cycle
				var:zg361_b1_quota_credit_source_trade = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_source_trade
				var:zg361_b1_quota_credit_liability = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_liability
			}
		}
		set_variable = { name = zg361_b1_quota_debt_settlement_found value = 0 }
		set_variable = { name = zg361_b1_quota_debt_before_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_quota_debt_before_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_quota_debt_before_bottom value = var:zg361_pending_325_n }
		if = {
			limit = { var:zg361_b1_quota_debt_kind = 3 var:zg361_pending_375_n >= 1 }
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
				max = 1
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_pending_grade
					var:zg361_b1_case_owner = scope:zg361_b1_debt_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_debt_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_debt_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_pending_grade = 3
				}
				set_variable = { name = zg361_pending_grade value = 2 }
				set_variable = { name = zg361_b1_quota_snapshot value = 2 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_absolute_grade > 2 }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
				scope:zg361_b1_debt_manager = { set_variable = { name = zg361_b1_quota_debt_settlement_found value = 1 } }
			}
			if = {
				limit = { var:zg361_b1_quota_debt_settlement_found = 1 }
				change_variable = { name = zg361_pending_375_n add = -1 }
				change_variable = { name = zg361_pending_35_n add = 1 }
			}
		}
		else_if = {
			limit = { var:zg361_b1_quota_debt_kind = 1 var:zg361_pending_325_n >= 1 }
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = var:zg361_b1_calibration_score
				max = 1
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_pending_grade
					var:zg361_b1_case_owner = scope:zg361_b1_debt_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_debt_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_debt_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_pending_grade = 1
				}
				set_variable = { name = zg361_pending_grade value = 2 }
				set_variable = { name = zg361_b1_quota_snapshot value = 2 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_absolute_grade > 2 }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
				scope:zg361_b1_debt_manager = { set_variable = { name = zg361_b1_quota_debt_settlement_found value = 1 } }
			}
			if = {
				limit = { var:zg361_b1_quota_debt_settlement_found = 1 }
				change_variable = { name = zg361_pending_325_n add = -1 }
				change_variable = { name = zg361_pending_35_n add = 1 }
			}
		}
		if = {
			limit = { var:zg361_b1_quota_debt_settlement_found = 1 }
			set_variable = { name = zg361_b1_quota_debt_after_top value = var:zg361_pending_375_n }
			set_variable = { name = zg361_b1_quota_debt_after_middle value = var:zg361_pending_35_n }
			set_variable = { name = zg361_b1_quota_debt_after_bottom value = var:zg361_pending_325_n }
			set_variable = { name = zg361_b1_quota_debt_state value = 2 }
			set_variable = { name = zg361_b1_quota_debt_settled_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_quota_debt_settlement_serial value = var:zg361_b1_case_serial }
			change_variable = { name = zg361_b1_quota_book_version add = 1 }
			if = {
				limit = { has_variable = zg361_b1_quota_debt_creditor }
				var:zg361_b1_quota_debt_creditor = {
					if = {
						limit = {
							has_variable = zg361_b1_quota_credit_state
							has_variable = zg361_b1_quota_credit_creditor
							has_variable = zg361_b1_quota_credit_debtor
							has_variable = zg361_b1_quota_credit_due_cycle
							has_variable = zg361_b1_quota_credit_source_trade
							has_variable = zg361_b1_quota_credit_liability
							var:zg361_b1_quota_credit_state = 1
							var:zg361_b1_quota_credit_creditor = this
							var:zg361_b1_quota_credit_debtor = scope:zg361_b1_debt_manager
							var:zg361_b1_quota_credit_due_cycle = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_due_cycle
							var:zg361_b1_quota_credit_source_trade = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_source_trade
							var:zg361_b1_quota_credit_liability = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_liability
						}
						set_variable = { name = zg361_b1_quota_credit_state value = 2 }
						set_variable = { name = zg361_b1_quota_credit_settled_cycle value = scope:zg361_b1_debt_manager.var:zg361_b1_cycle_serial }
					}
				}
			}
			set_variable = { name = zg361_b1_m139_receipt_serial value = var:zg361_b1_case_serial }
			debug_log = "ZG361B1: one-shot quota responsibility debt settled"
		}
	}
}

# Execute one TOP-for-MIDDLE exchange inside the unique 3+4 pool. Both books
# advance once, both parties retain the same operation receipt, and the
# receiver receives one liability due at created_cycle + 1.
zg361_b1_execute_unique_pool_trade_effect = {
	if = {
		limit = {
			var:zg361_b1_unique_pool_active = 1
			var:zg361_b1_unique_pool_trade_used = 0
			has_variable = zg361_mechanism_037_choice
			has_variable = zg361_mechanism_139_choice
			var:zg361_mechanism_037_choice = 1
			var:zg361_mechanism_139_choice = 1
			scope:zg361_b1_pool_four_manager = {
				var:zg361_b1_quota_pool_membership = 1
				var:zg361_b1_bank_superior = root
				var:zg361_pending_375_n >= 1
				trigger_if = {
					limit = { has_variable = zg361_b1_quota_credit_state }
					NOT = { var:zg361_b1_quota_credit_state = 1 }
				}
				trigger_else = { always = yes }
			}
			scope:zg361_b1_pool_three_manager = {
				var:zg361_b1_quota_pool_membership = 1
				var:zg361_b1_bank_superior = root
				var:zg361_pending_35_n >= 1
				trigger_if = {
					limit = { has_variable = zg361_b1_quota_debt_state }
					NOT = { var:zg361_b1_quota_debt_state = 1 }
				}
				trigger_else = { always = yes }
			}
		}
		set_variable = { name = zg361_b1_unique_pool_trade_candidate_n value = 0 }
		scope:zg361_b1_pool_four_manager = {
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
				max = 1
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					var:zg361_b1_case_owner = scope:zg361_b1_pool_four_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_pool_four_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_pool_four_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_pending_grade = 3
				}
				save_temporary_scope_as = zg361_b1_trade_donor_subject
				root = { change_variable = { name = zg361_b1_unique_pool_trade_candidate_n add = 1 } }
			}
		}
		scope:zg361_b1_pool_three_manager = {
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = var:zg361_b1_calibration_score
				max = 1
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					var:zg361_b1_case_owner = scope:zg361_b1_pool_three_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_pool_three_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_pool_three_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_pending_grade = 2
				}
				save_temporary_scope_as = zg361_b1_trade_receiver_subject
				root = { change_variable = { name = zg361_b1_unique_pool_trade_candidate_n add = 1 } }
			}
		}
		if = {
			limit = { var:zg361_b1_unique_pool_trade_candidate_n = 2 }
			scope:zg361_b1_trade_donor_subject = {
				set_variable = { name = zg361_pending_grade value = 2 }
				set_variable = { name = zg361_b1_quota_snapshot value = 2 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_absolute_grade > 2 }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
			}
			scope:zg361_b1_trade_receiver_subject = {
				set_variable = { name = zg361_pending_grade value = 3 }
				set_variable = { name = zg361_b1_quota_snapshot value = 3 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 3 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_absolute_grade > 3 }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
			}
			change_variable = { name = zg361_b1_unique_pool_trade_serial add = 1 }
			set_variable = { name = zg361_b1_unique_pool_trade_used value = 1 }
			scope:zg361_b1_pool_four_manager = {
				change_variable = { name = zg361_pending_375_n add = -1 }
				change_variable = { name = zg361_pending_35_n add = 1 }
				change_variable = { name = zg361_b1_quota_book_version add = 1 }
				set_variable = { name = zg361_b1_quota_trade_applied value = 1 }
				set_variable = { name = zg361_b1_quota_trade_slots value = 1 }
				set_variable = { name = zg361_b1_quota_trade_band value = 3 }
				set_variable = { name = zg361_b1_quota_trade_counterparty value = scope:zg361_b1_pool_three_manager }
				set_variable = { name = zg361_b1_quota_trade_operation_serial value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_quota_credit_state value = 1 }
				set_variable = { name = zg361_b1_quota_credit_creditor value = this }
				set_variable = { name = zg361_b1_quota_credit_debtor value = scope:zg361_b1_pool_three_manager }
				set_variable = { name = zg361_b1_quota_credit_due_cycle value = { value = var:zg361_b1_cycle_serial add = 1 } }
				set_variable = { name = zg361_b1_quota_credit_source_trade value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_quota_credit_liability value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_m037_receipt_serial value = var:zg361_b1_case_serial }
			}
			scope:zg361_b1_pool_three_manager = {
				change_variable = { name = zg361_pending_375_n add = 1 }
				change_variable = { name = zg361_pending_35_n add = -1 }
				change_variable = { name = zg361_b1_quota_book_version add = 1 }
				set_variable = { name = zg361_b1_quota_trade_applied value = 1 }
				set_variable = { name = zg361_b1_quota_trade_slots value = 1 }
				set_variable = { name = zg361_b1_quota_trade_band value = 3 }
				set_variable = { name = zg361_b1_quota_trade_counterparty value = scope:zg361_b1_pool_four_manager }
				set_variable = { name = zg361_b1_quota_trade_operation_serial value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_quota_debt_state value = 1 }
				set_variable = { name = zg361_b1_quota_debt_kind value = 3 }
				set_variable = { name = zg361_b1_quota_debt_slots value = 1 }
				set_variable = { name = zg361_b1_quota_debt_created_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_quota_debt_due_cycle value = { value = var:zg361_b1_cycle_serial add = 1 } }
				set_variable = { name = zg361_b1_quota_debt_source_trade value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_quota_debt_creditor value = scope:zg361_b1_pool_four_manager }
				set_variable = { name = zg361_b1_quota_debt_debtor value = this }
				set_variable = { name = zg361_b1_quota_debt_approver value = root }
				set_variable = { name = zg361_b1_quota_debt_liability value = root.var:zg361_b1_unique_pool_trade_serial }
				set_variable = { name = zg361_b1_m037_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m139_receipt_serial value = var:zg361_b1_case_serial }
			}
			debug_log = "ZG361B1: exact one-slot bilateral trade and next-cycle liability recorded"
		}
	}
}

zg361_b1_submit_quota_book_effect = {
	zg361_b1_rebuild_local_quota_effect = yes
	if = {
		limit = { has_variable = zg361_b1_bank_superior }
		save_temporary_scope_as = zg361_b1_ready_manager
		var:zg361_b1_bank_superior = {
			if = {
				limit = {
					is_alive = yes
					has_variable = zg361_b1_bank_state
					var:zg361_b1_bank_state = 1
					has_variable = zg361_b1_bank_season
					var:zg361_b1_bank_season = scope:zg361_b1_ready_manager.var:zg361_b1_bank_season
				}
				if = {
					limit = {
						trigger_if = {
							limit = { has_variable_list = zg361_b1_ready_managers }
							NOT = {
								is_target_in_variable_list = {
									name = zg361_b1_ready_managers
									target = scope:zg361_b1_ready_manager
								}
							}
						}
						trigger_else = { always = yes }
					}
					add_to_variable_list = {
						name = zg361_b1_ready_managers
						target = scope:zg361_b1_ready_manager
					}
					change_variable = { name = zg361_b1_ready_manager_n add = 1 }
					change_variable = { name = zg361_b1_pool_n add = scope:zg361_b1_ready_manager.var:zg361_cohort_n }
					scope:zg361_b1_ready_manager = {
						set_variable = { name = zg361_b1_bank_ready_order value = root.var:zg361_b1_ready_manager_n }
						set_variable = { name = zg361_b1_bank_posted_serial value = var:zg361_b1_case_serial }
					}
				}
				if = {
					limit = { var:zg361_b1_ready_manager_n >= var:zg361_b1_expected_manager_n }
					save_scope_as = zg361_b1_bank_ticket_owner
					save_scope_value_as = { name = zg361_b1_bank_ticket_season value = var:zg361_b1_bank_season }
					save_scope_value_as = { name = zg361_b1_bank_ticket_case value = var:zg361_b1_bank_case_serial }
					save_scope_value_as = { name = zg361_b1_bank_ticket_state value = var:zg361_b1_bank_state }
					trigger_event = { id = zg361b1.110 days = 1 }
				}
			}
			else = { scope:zg361_b1_ready_manager = { zg361_b1_apply_local_quota_effect = yes } }
		}
	}
	else = { zg361_b1_apply_local_quota_effect = yes }
}

# #136 freezes one real 3-4 manager pre-huddle on the common-superior bank.
# A records only a boundary recommendation; B freezes each attendee's complete
# preallocation and its rubber-stamp risk.  No manager alias can occupy two
# seats because the input is the unique ready-manager list.
zg361_b1_prepare_bank_huddle_effect = {
	remove_variable = zg361_b1_m136_receipt_serial
	set_variable = { name = zg361_b1_huddle_host_object_available value = 0 }
	set_variable = { name = zg361_b1_huddle_host_state value = 0 }
	remove_variable = zg361_b1_huddle_host_owner
	remove_variable = zg361_b1_huddle_host_subject
	remove_variable = zg361_b1_huddle_host_id
	set_variable = { name = zg361_b1_huddle_host_cycle value = 0 }
	set_variable = { name = zg361_b1_huddle_host_case value = 0 }
	set_variable = { name = zg361_b1_huddle_host_attendee_n value = 0 }
	remove_variable = zg361_b1_huddle_host_manager_1
	remove_variable = zg361_b1_huddle_host_manager_2
	remove_variable = zg361_b1_huddle_host_manager_3
	remove_variable = zg361_b1_huddle_host_manager_4
	if = {
		limit = { has_variable_list = zg361_b1_ready_managers }
		every_in_list = {
			list = zg361_b1_ready_managers
			set_variable = { name = zg361_b1_huddle_attendee_attending value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_route value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_state value = 0 }
			remove_variable = zg361_b1_huddle_attendee_owner
			remove_variable = zg361_b1_huddle_attendee_subject
			remove_variable = zg361_b1_huddle_attendee_id
			set_variable = { name = zg361_b1_huddle_attendee_cycle value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_case value = 0 }
		}
	}
	if = {
		limit = {
			var:zg361_b1_bank_m136_mode != 3
			var:zg361_b1_ready_manager_n >= 3
		}
		set_variable = { name = zg361_b1_huddle_host_object_available value = 1 }
		set_variable = { name = zg361_b1_huddle_host_id value = { value = var:zg361_b1_bank_case_serial multiply = 100 add = 36 } }
		set_variable = { name = zg361_b1_huddle_host_owner value = this }
		set_variable = { name = zg361_b1_huddle_host_subject value = this }
		set_variable = { name = zg361_b1_huddle_host_cycle value = var:zg361_b1_bank_season }
		set_variable = { name = zg361_b1_huddle_host_case value = var:zg361_b1_bank_case_serial }
		set_variable = { name = zg361_b1_huddle_host_frozen_year value = current_year }
		set_variable = { name = zg361_b1_huddle_host_fact_standard value = 8 }
		set_variable = { name = zg361_b1_huddle_host_quota_standard value = 361 }
		set_variable = { name = zg361_b1_huddle_host_state value = 1 }
		set_variable = { name = zg361_b1_huddle_host_ack_n value = 0 }
		set_variable = { name = zg361_b1_huddle_host_minutes_budget value = 30 }
		set_variable = { name = zg361_b1_huddle_host_standard_snapshot_hash value = { value = var:zg361_b1_bank_case_serial multiply = 1000 add = var:zg361_b1_ready_manager_n } }
		ordered_in_list = {
			list = zg361_b1_ready_managers
			order_by = { value = var:zg361_b1_bank_ready_order multiply = -1 }
			max = 4
			root = { change_variable = { name = zg361_b1_huddle_host_attendee_n add = 1 } }
			set_variable = { name = zg361_b1_huddle_attendee_attending value = 1 }
			save_temporary_scope_as = zg361_b1_huddle_manager
			if = { limit = { root.var:zg361_b1_huddle_host_attendee_n = 1 } root = { set_variable = { name = zg361_b1_huddle_host_manager_1 value = scope:zg361_b1_huddle_manager } } }
			else_if = { limit = { root.var:zg361_b1_huddle_host_attendee_n = 2 } root = { set_variable = { name = zg361_b1_huddle_host_manager_2 value = scope:zg361_b1_huddle_manager } } }
			else_if = { limit = { root.var:zg361_b1_huddle_host_attendee_n = 3 } root = { set_variable = { name = zg361_b1_huddle_host_manager_3 value = scope:zg361_b1_huddle_manager } } }
			else_if = { limit = { root.var:zg361_b1_huddle_host_attendee_n = 4 } root = { set_variable = { name = zg361_b1_huddle_host_manager_4 value = scope:zg361_b1_huddle_manager } } }
			set_variable = { name = zg361_b1_huddle_attendee_id value = root.var:zg361_b1_huddle_host_id }
			set_variable = { name = zg361_b1_huddle_attendee_seat value = root.var:zg361_b1_huddle_host_attendee_n }
			set_variable = { name = zg361_b1_huddle_attendee_route value = root.var:zg361_b1_bank_m136_mode }
			set_variable = { name = zg361_b1_huddle_attendee_owner value = root }
			set_variable = { name = zg361_b1_huddle_attendee_subject value = this }
			set_variable = { name = zg361_b1_huddle_attendee_cycle value = root.var:zg361_b1_huddle_host_cycle }
			set_variable = { name = zg361_b1_huddle_attendee_case value = root.var:zg361_b1_huddle_host_case }
			set_variable = { name = zg361_b1_huddle_attendee_state value = 1 }
			set_variable = { name = zg361_b1_huddle_attendee_minutes_budget value = 30 }
			set_variable = { name = zg361_b1_huddle_attendee_minutes_consumed value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_ack_posted value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_diff_n value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_boundary_case_n value = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_suggestion_grade value = 0 }
			if = {
				limit = { root.var:zg361_b1_bank_m136_mode = 1 }
				ordered_in_list = {
					variable = zg361_b1_subjects
					order_by = { value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order }
					max = 1
					limit = {
						var:zg361_b1_case_owner = scope:zg361_b1_huddle_manager
						var:zg361_b1_case_state = 5
						var:zg361_b1_case_active = 1
						var:zg361_b1_roster_included = 1
						var:zg361_pending_grade = 2
					}
					set_variable = { name = zg361_b1_huddle_attendee_boundary_recommendation value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_huddle_assignment_available value = 1 }
					set_variable = { name = zg361_b1_huddle_assignment_owner value = scope:zg361_b1_huddle_manager }
					set_variable = { name = zg361_b1_huddle_assignment_subject value = this }
					set_variable = { name = zg361_b1_huddle_assignment_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_huddle_assignment_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_huddle_assignment_state value = 1 }
					set_variable = { name = zg361_b1_huddle_suggested_grade value = var:zg361_pending_grade }
					save_temporary_scope_as = zg361_b1_huddle_boundary_subject_scope
					scope:zg361_b1_huddle_manager = {
						set_variable = { name = zg361_b1_huddle_attendee_boundary_subject value = scope:zg361_b1_huddle_boundary_subject_scope }
						set_variable = { name = zg361_b1_huddle_attendee_boundary_case_n value = 1 }
						set_variable = { name = zg361_b1_huddle_attendee_suggestion_grade value = 2 }
					}
				}
			}
			else = {
				set_variable = { name = zg361_b1_huddle_attendee_preallocation_top value = var:zg361_pending_375_n }
				set_variable = { name = zg361_b1_huddle_attendee_preallocation_middle value = var:zg361_pending_35_n }
				set_variable = { name = zg361_b1_huddle_attendee_preallocation_bottom value = var:zg361_pending_325_n }
				set_variable = { name = zg361_b1_huddle_attendee_preallocation_total value = { value = var:zg361_pending_375_n add = var:zg361_pending_35_n add = var:zg361_pending_325_n } }
				set_variable = { name = zg361_b1_huddle_attendee_rubber_stamp_risk value = 1 }
				save_temporary_scope_as = zg361_b1_huddle_prealloc_manager
				every_in_list = {
					variable = zg361_b1_subjects
					limit = {
						var:zg361_b1_case_owner = scope:zg361_b1_huddle_prealloc_manager
						var:zg361_b1_case_subject = this
						var:zg361_b1_cycle_serial = scope:zg361_b1_huddle_prealloc_manager.var:zg361_b1_cycle_serial
						var:zg361_b1_case_serial = scope:zg361_b1_huddle_prealloc_manager.var:zg361_b1_case_serial
						var:zg361_b1_case_state = 5
						var:zg361_b1_case_active = 1
						var:zg361_b1_roster_included = 1
					}
					set_variable = { name = zg361_b1_huddle_assignment_available value = 1 }
					set_variable = { name = zg361_b1_huddle_assignment_owner value = scope:zg361_b1_huddle_prealloc_manager }
					set_variable = { name = zg361_b1_huddle_assignment_subject value = this }
					set_variable = { name = zg361_b1_huddle_assignment_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_huddle_assignment_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_huddle_assignment_state value = 1 }
					set_variable = { name = zg361_b1_huddle_suggested_grade value = var:zg361_pending_grade }
				}
			}
		}
		set_variable = { name = zg361_b1_dissent_review_attention_budget value = var:zg361_b1_huddle_host_attendee_n }
		set_variable = { name = zg361_b1_m136_receipt_serial value = var:zg361_b1_huddle_host_case }
	}
}

# #141 selects at most one real grandchild boundary case. A writes only a
# must-review agenda marker and consumes the direct manager's attention later;
# B allows that direct manager to execute one conserved MIDDLE<->TOP peer swap.
# The common superior never writes a grade.
zg361_b1_prepare_bank_must_review_effect = {
	set_variable = { name = zg361_b1_must_review_host_object_available value = 0 }
	set_variable = { name = zg361_b1_must_review_host_state value = 0 }
	set_variable = { name = zg361_b1_must_review_count value = 0 }
	if = {
		limit = { var:zg361_b1_bank_m141_mode != 3 var:zg361_b1_ready_manager_n >= 1 }
		ordered_in_list = {
			list = zg361_b1_ready_managers
			order_by = { value = var:zg361_b1_bank_ready_order multiply = -1 }
			max = { value = var:zg361_b1_ready_manager_n max = 80 }
			if = {
				limit = { root.var:zg361_b1_must_review_count = 0 }
				save_temporary_scope_as = zg361_b1_must_review_manager
				ordered_in_list = {
					variable = zg361_b1_subjects
					order_by = { value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order }
					max = 1
					limit = {
						var:zg361_b1_case_owner = scope:zg361_b1_must_review_manager
						var:zg361_b1_case_subject = this
						var:zg361_b1_case_state = 5
						var:zg361_b1_case_active = 1
						var:zg361_b1_roster_included = 1
						var:zg361_pending_grade = 2
						var:zg361_b1_fact_sheet_serial >= 1
						trigger_if = {
							limit = { root.var:zg361_b1_bank_m141_mode = 2 }
							scope:zg361_b1_must_review_manager = {
								any_in_list = {
									variable = zg361_b1_subjects
									var:zg361_b1_case_owner = scope:zg361_b1_must_review_manager
									var:zg361_b1_case_state = 5
									var:zg361_b1_case_active = 1
									var:zg361_b1_roster_included = 1
									var:zg361_pending_grade = 3
								}
							}
						}
						trigger_else = { always = yes }
					}
					save_temporary_scope_as = zg361_b1_must_review_subject
					if = {
						limit = { root.var:zg361_b1_bank_m141_mode = 2 }
						scope:zg361_b1_must_review_manager = {
							ordered_in_list = {
								variable = zg361_b1_subjects
								order_by = { value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order }
								max = 1
								limit = {
									var:zg361_b1_case_owner = scope:zg361_b1_must_review_manager
									var:zg361_b1_case_subject = this
									var:zg361_b1_case_state = 5
									var:zg361_b1_case_active = 1
									var:zg361_b1_roster_included = 1
									var:zg361_pending_grade = 3
									NOT = { this = scope:zg361_b1_must_review_subject }
								}
								save_temporary_scope_as = zg361_b1_must_review_frozen_peer
							}
						}
					}
					# Both A and B create one real must-review case.  The superior may
					# force agenda/attention, but any B-route grade movement is executed
					# later by the direct manager inside the manager's sole quota book.
					set_variable = { name = zg361_b1_must_review_object_available value = 1 }
					set_variable = { name = zg361_b1_must_review_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 41 } }
					set_variable = { name = zg361_b1_must_review_object_owner value = scope:zg361_b1_must_review_manager }
					set_variable = { name = zg361_b1_must_review_object_subject value = this }
					set_variable = { name = zg361_b1_must_review_object_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_must_review_object_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_must_review_object_state value = 1 }
					set_variable = { name = zg361_b1_must_review_state value = 1 }
					set_variable = { name = zg361_b1_must_review_route value = root.var:zg361_b1_bank_m141_mode }
					set_variable = { name = zg361_b1_must_review_superior value = root }
					set_variable = { name = zg361_b1_must_review_manager value = scope:zg361_b1_must_review_manager }
					set_variable = { name = zg361_b1_must_review_subject value = this }
					set_variable = { name = zg361_b1_must_review_reason_fact value = var:zg361_b1_fact_sheet_serial }
					set_variable = { name = zg361_b1_must_review_recommendation value = 3 }
					set_variable = { name = zg361_b1_must_review_direction value = 1 }
					set_variable = { name = zg361_b1_must_review_override_blocked value = 1 }
					set_variable = { name = zg361_b1_must_review_book_version_before value = scope:zg361_b1_must_review_manager.var:zg361_b1_quota_book_version }
					if = { limit = { root.var:zg361_b1_bank_m141_mode = 2 exists = scope:zg361_b1_must_review_frozen_peer } set_variable = { name = zg361_b1_must_review_swap_peer value = scope:zg361_b1_must_review_frozen_peer } }
					scope:zg361_b1_must_review_manager = {
						set_variable = { name = zg361_b1_must_review_manager_link_available value = 1 }
						set_variable = { name = zg361_b1_must_review_manager_link_state value = 1 }
						set_variable = { name = zg361_b1_must_review_manager_link_subject value = scope:zg361_b1_must_review_subject }
						set_variable = { name = zg361_b1_must_review_manager_link_route value = root.var:zg361_b1_bank_m141_mode }
						set_variable = { name = zg361_b1_must_review_manager_link_cycle value = var:zg361_b1_cycle_serial }
						set_variable = { name = zg361_b1_must_review_manager_link_case value = var:zg361_b1_case_serial }
						set_variable = { name = zg361_b1_must_review_manager_link_book_version_before value = var:zg361_b1_quota_book_version }
						if = { limit = { root.var:zg361_b1_bank_m141_mode = 2 exists = scope:zg361_b1_must_review_frozen_peer } set_variable = { name = zg361_b1_must_review_manager_link_peer value = scope:zg361_b1_must_review_frozen_peer } }
					}
					root = {
						set_variable = { name = zg361_b1_must_review_host_object_available value = 1 }
						set_variable = { name = zg361_b1_must_review_host_object_id value = scope:zg361_b1_must_review_subject.var:zg361_b1_must_review_object_id }
						set_variable = { name = zg361_b1_must_review_host_owner value = scope:zg361_b1_must_review_manager }
						set_variable = { name = zg361_b1_must_review_host_subject value = scope:zg361_b1_must_review_subject }
						set_variable = { name = zg361_b1_must_review_host_cycle value = scope:zg361_b1_must_review_subject.var:zg361_b1_cycle_serial }
						set_variable = { name = zg361_b1_must_review_host_case value = scope:zg361_b1_must_review_subject.var:zg361_b1_case_serial }
						set_variable = { name = zg361_b1_must_review_host_state value = 1 }
						set_variable = { name = zg361_b1_must_review_host_reason_fact value = scope:zg361_b1_must_review_subject.var:zg361_b1_fact_sheet_serial }
						change_variable = { name = zg361_b1_must_review_count add = 1 }
					}
				}
			}
		}
		if = {
			limit = { var:zg361_b1_must_review_count = 1 }
			set_variable = { name = zg361_b1_m141_receipt_serial value = var:zg361_b1_bank_case_serial }
		}
	}
}

zg361_b1_close_common_superior_bank_legacy_unused_effect = {
	set_variable = { name = zg361_b1_bank_state value = 2 }
	set_variable = { name = zg361_b1_pool_cursor value = 0 }
	set_variable = { name = zg361_b1_pool_n value = 0 }
	every_in_list = {
		variable = zg361_b1_ready_managers
		save_temporary_scope_as = zg361_b1_pool_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					var:zg361_b1_case_owner = scope:zg361_b1_pool_manager
					var:zg361_b1_case_state = 5
					has_variable = zg361_pending_grade
					has_variable = zg361_b1_calibration_score
				}
				add_to_list = zg361_b1_pool_candidates
				root = { change_variable = { name = zg361_b1_pool_n add = 1 } }
			}
		}
	}
	set_variable = { name = zg361_b1_pool_top_slots value = 0 }
	set_variable = { name = zg361_b1_pool_bottom_slots value = 0 }
	if = {
		limit = { var:zg361_b1_pool_n >= 1 }
	set_variable = {
		name = zg361_b1_pool_top_slots
		value = { value = var:zg361_b1_pool_n multiply = 0.3 round = yes min = 1 }
	}
	set_variable = { name = zg361_b1_pool_bottom_slots value = 0 }
	if = {
		limit = { var:zg361_b1_pool_n >= 5 }
		set_variable = {
			name = zg361_b1_pool_bottom_slots
			value = { value = var:zg361_b1_pool_n multiply = 0.1 floor = yes min = 1 }
		}
	}
	ordered_in_list = {
		list = zg361_b1_pool_candidates
		order_by = var:zg361_b1_calibration_score
		max = { value = list_size:zg361_b1_pool_candidates max = 80 }
		root = { change_variable = { name = zg361_b1_pool_cursor add = 1 } }
		set_variable = { name = zg361_rank value = root.var:zg361_b1_pool_cursor }
		set_variable = { name = zg361_b1_pool_rank value = root.var:zg361_b1_pool_cursor }
		set_variable = { name = zg361_pending_grade value = 2 }
		if = {
			limit = { var:zg361_b1_pool_rank <= root.var:zg361_b1_pool_top_slots }
			set_variable = { name = zg361_pending_grade value = 3 }
		}
		set_variable = { name = zg361_last_reviewer value = var:zg361_b1_case_owner }
		set_variable = { name = zg361_last_review_serial value = var:zg361_b1_cycle_serial }
	}
	set_variable = { name = zg361_b1_pool_bottom_candidate_n value = 0 }
	every_in_list = {
		list = zg361_b1_pool_candidates
		limit = { NOT = { has_character_flag = zg361_newcomer_this_cycle } }
		add_to_list = zg361_b1_pool_bottom_candidates
		root = { change_variable = { name = zg361_b1_pool_bottom_candidate_n add = 1 } }
	}
	set_variable = { name = zg361_b1_pool_bottom_cursor value = 0 }
	if = {
		limit = {
			var:zg361_b1_pool_bottom_slots >= 1
			var:zg361_b1_pool_bottom_candidate_n >= 1
		}
		ordered_in_list = {
			list = zg361_b1_pool_bottom_candidates
			order_by = var:zg361_b1_pool_rank
			max = { value = list_size:zg361_b1_pool_bottom_candidates max = 80 }
			if = {
				limit = { root.var:zg361_b1_pool_bottom_cursor < root.var:zg361_b1_pool_bottom_slots }
				set_variable = { name = zg361_pending_grade value = 1 }
			}
			root = { change_variable = { name = zg361_b1_pool_bottom_cursor add = 1 } }
		}
	}
	every_in_list = {
		list = zg361_b1_pool_candidates
		set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
		set_variable = {
			name = zg361_b1_shadow_to_quota_delta
			value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade }
		}
		set_variable = { name = zg361_b1_forced_down value = 0 }
		if = {
			limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
			set_variable = { name = zg361_b1_forced_down value = 1 }
		}
	}
	}
	every_in_list = {
		variable = zg361_b1_ready_managers
		set_variable = { name = zg361_pending_375_n value = 0 }
		set_variable = { name = zg361_pending_35_n value = 0 }
		set_variable = { name = zg361_pending_325_n value = 0 }
		set_variable = { name = zg361_top_cut value = root.var:zg361_b1_pool_top_slots }
		set_variable = { name = zg361_top_cut_next value = { value = root.var:zg361_b1_pool_top_slots add = 1 } }
		set_variable = { name = zg361_bottom_slots value = root.var:zg361_b1_pool_bottom_slots }
		save_temporary_scope_as = zg361_b1_allocated_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					var:zg361_b1_case_owner = scope:zg361_b1_allocated_manager
					var:zg361_b1_case_state = 5
					has_variable = zg361_pending_grade
				}
				if = {
					limit = { var:zg361_pending_grade = 3 }
					scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_375_n add = 1 } }
				}
				else_if = {
					limit = { var:zg361_pending_grade = 1 }
					scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_325_n add = 1 } }
				}
				else = { scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_35_n add = 1 } } }
			}
		}
		set_variable = { name = zg361_b1_cycle_state value = 6 }
		set_variable = { name = zg361_b1_m037_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m038_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m139_receipt_serial value = var:zg361_b1_case_serial }
		# This loop is owned by the common superior, so ROOT is still the
		# superior. Cross one committed event boundary to reset ROOT to this
		# manager before touching manager-owned subject lists or settlement.
		save_scope_as = zg361_b1_ticket_owner
		save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.111 days = 1 }
	}
	debug_log = "ZG361B1: common-superior quota bank closed once"
}

zg361_b1_close_common_superior_bank_effect = {
	if = {
		limit = { var:zg361_b1_bank_state = 1 }
		set_variable = { name = zg361_b1_bank_state value = 2 }
		zg361_b1_prepare_bank_huddle_effect = yes
		set_variable = { name = zg361_b1_unique_pool_active value = 0 }
		set_variable = { name = zg361_b1_unique_pool_three_n value = 0 }
		set_variable = { name = zg361_b1_unique_pool_four_n value = 0 }
		set_variable = { name = zg361_b1_unique_pool_trade_used value = 0 }
		if = {
			limit = { NOT = { has_variable = zg361_b1_unique_pool_trade_serial } }
			set_variable = { name = zg361_b1_unique_pool_trade_serial value = 0 }
		}
		every_in_list = {
			variable = zg361_b1_ready_managers
			set_variable = { name = zg361_b1_quota_pool_membership value = 0 }
			if = {
				limit = { var:zg361_b1_local_candidate_n = 3 }
				save_temporary_scope_as = zg361_b1_pool_three_manager
				root = { change_variable = { name = zg361_b1_unique_pool_three_n add = 1 } }
			}
			else_if = {
				limit = { var:zg361_b1_local_candidate_n = 4 }
				save_temporary_scope_as = zg361_b1_pool_four_manager
				root = { change_variable = { name = zg361_b1_unique_pool_four_n add = 1 } }
			}
		}
		# A pool exists only when the frozen bank contains one unambiguous 3-team
		# and one unambiguous 4-team and both carry the same function code. The
		# bank owner is their already-frozen common superior.
		if = {
			limit = {
				var:zg361_b1_unique_pool_three_n = 1
				var:zg361_b1_unique_pool_four_n = 1
				scope:zg361_b1_pool_three_manager.var:zg361_b1_quota_function_code = scope:zg361_b1_pool_four_manager.var:zg361_b1_quota_function_code
			}
			set_variable = { name = zg361_b1_unique_pool_active value = 1 }
			set_variable = { name = zg361_b1_unique_pool_n value = 0 }
			scope:zg361_b1_pool_three_manager = {
				set_variable = { name = zg361_b1_quota_pool_membership value = 1 }
				set_variable = { name = zg361_b1_quota_pool_team_n value = 2 }
				set_variable = { name = zg361_b1_quota_pool_source_size value = 3 }
				save_temporary_scope_as = zg361_b1_unique_pool_manager
					every_in_list = {
						variable = zg361_b1_subjects
						if = {
							limit = {
								has_variable = zg361_b1_case_owner
								has_variable = zg361_b1_case_subject
								has_variable = zg361_b1_cycle_serial
								has_variable = zg361_b1_case_serial
								has_variable = zg361_b1_case_state
								has_variable = zg361_b1_case_active
								var:zg361_b1_case_owner = scope:zg361_b1_unique_pool_manager
								var:zg361_b1_case_subject = this
								var:zg361_b1_cycle_serial = scope:zg361_b1_unique_pool_manager.var:zg361_b1_cycle_serial
								var:zg361_b1_case_serial = scope:zg361_b1_unique_pool_manager.var:zg361_b1_case_serial
								var:zg361_b1_case_state = 5
								var:zg361_b1_case_active = 1
							var:zg361_b1_roster_included = 1
							has_variable = zg361_pending_grade
							has_variable = zg361_b1_calibration_score
						}
						set_variable = { name = zg361_b1_quota_pool_subject_source_size value = 3 }
						add_to_list = zg361_b1_unique_pool_candidates
						root = { change_variable = { name = zg361_b1_unique_pool_n add = 1 } }
					}
				}
			}
			scope:zg361_b1_pool_four_manager = {
				set_variable = { name = zg361_b1_quota_pool_membership value = 1 }
				set_variable = { name = zg361_b1_quota_pool_team_n value = 2 }
				set_variable = { name = zg361_b1_quota_pool_source_size value = 4 }
				save_temporary_scope_as = zg361_b1_unique_pool_manager
					every_in_list = {
						variable = zg361_b1_subjects
						if = {
							limit = {
								has_variable = zg361_b1_case_owner
								has_variable = zg361_b1_case_subject
								has_variable = zg361_b1_cycle_serial
								has_variable = zg361_b1_case_serial
								has_variable = zg361_b1_case_state
								has_variable = zg361_b1_case_active
								var:zg361_b1_case_owner = scope:zg361_b1_unique_pool_manager
								var:zg361_b1_case_subject = this
								var:zg361_b1_cycle_serial = scope:zg361_b1_unique_pool_manager.var:zg361_b1_cycle_serial
								var:zg361_b1_case_serial = scope:zg361_b1_unique_pool_manager.var:zg361_b1_case_serial
								var:zg361_b1_case_state = 5
								var:zg361_b1_case_active = 1
							var:zg361_b1_roster_included = 1
							has_variable = zg361_pending_grade
							has_variable = zg361_b1_calibration_score
						}
						set_variable = { name = zg361_b1_quota_pool_subject_source_size value = 4 }
						add_to_list = zg361_b1_unique_pool_candidates
						root = { change_variable = { name = zg361_b1_unique_pool_n add = 1 } }
					}
				}
			}
			if = {
				limit = { var:zg361_b1_unique_pool_n = 7 }
				zg361_b1_compute_exact_quota_effect = { COHORT_SIZE = var:zg361_b1_unique_pool_n ROUNDING_SCOPE = 2 }
				if = {
					limit = { var:zg361_b1_bank_m138_mode != 3 var:zg361_b1_quota_rounding_bank_object_available = 1 }
					set_variable = { name = zg361_b1_quota_rounding_bank_team_n value = 2 }
					set_variable = { name = zg361_b1_quota_rounding_bank_team_1 value = scope:zg361_b1_pool_three_manager }
					set_variable = { name = zg361_b1_quota_rounding_bank_team_2 value = scope:zg361_b1_pool_four_manager }
					set_variable = { name = zg361_b1_quota_rounding_bank_remainder_team value = scope:zg361_b1_pool_three_manager }
					set_variable = { name = zg361_b1_quota_rounding_bank_affected_team value = scope:zg361_b1_pool_four_manager }
					if = {
						limit = { var:zg361_b1_quota_rounding_bank_route = 1 var:zg361_b1_quota_rounding_bank_rotation_cursor = 2 }
						set_variable = { name = zg361_b1_quota_rounding_bank_remainder_team value = scope:zg361_b1_pool_four_manager }
						set_variable = { name = zg361_b1_quota_rounding_bank_affected_team value = scope:zg361_b1_pool_three_manager }
					}
					else_if = {
						limit = { var:zg361_b1_quota_rounding_bank_route = 2 }
						# Chair discretion changes only the team receipt, never 7/14/2.
						set_variable = { name = zg361_b1_quota_rounding_bank_chair value = this }
						set_variable = { name = zg361_b1_quota_rounding_bank_remainder_team value = scope:zg361_b1_pool_four_manager }
						set_variable = { name = zg361_b1_quota_rounding_bank_affected_team value = scope:zg361_b1_pool_three_manager }
					}
					set_variable = { name = zg361_b1_quota_rounding_bank_operation_seal value = { value = var:zg361_b1_bank_season multiply = 100000 add = var:zg361_b1_bank_case_serial } }
					set_variable = { name = zg361_b1_quota_rounding_bank_state value = 2 }
					set_variable = { name = zg361_b1_m138_receipt_serial value = var:zg361_b1_quota_rounding_bank_case }
					var:zg361_b1_quota_rounding_bank_remainder_team = {
						set_variable = { name = zg361_b1_quota_rounding_remainder_credit value = 1 }
						set_variable = { name = zg361_b1_quota_rounding_receipt_owner value = root }
					}
					var:zg361_b1_quota_rounding_bank_affected_team = {
						set_variable = { name = zg361_b1_quota_rounding_affected_receipt value = 1 }
						set_variable = { name = zg361_b1_quota_rounding_receipt_owner value = root }
					}
				}
				set_variable = { name = zg361_b1_unique_pool_top_slots value = var:zg361_b1_quota_top_slots }
				set_variable = { name = zg361_b1_unique_pool_middle_slots value = var:zg361_b1_quota_middle_slots }
				set_variable = { name = zg361_b1_unique_pool_bottom_slots value = var:zg361_b1_quota_bottom_slots }
				every_in_list = {
					list = zg361_b1_unique_pool_candidates
					set_variable = { name = zg361_b1_quota_rounding_team_priority value = 0 }
					if = {
						limit = {
							root.var:zg361_b1_quota_rounding_bank_object_available = 1
							var:zg361_b1_case_owner = root.var:zg361_b1_quota_rounding_bank_remainder_team
						}
						set_variable = { name = zg361_b1_quota_rounding_team_priority value = 1 }
					}
					set_variable = {
						name = zg361_b1_quota_pool_tie_key
						value = {
							value = var:zg361_b1_calibration_score multiply = 10000
							add = { value = var:zg361_b1_quota_rounding_team_priority multiply = 1000 }
							add = { value = var:zg361_b1_quota_pool_subject_source_size multiply = 100 }
							subtract = var:zg361_b1_roster_frozen_order
						}
					}
				}
				if = { limit = { var:zg361_b1_quota_rounding_bank_object_available = 1 } set_variable = { name = zg361_b1_quota_rounding_bank_tie_consumer_active value = 1 } }
				set_variable = { name = zg361_b1_unique_pool_cursor value = 0 }
				ordered_in_list = {
					list = zg361_b1_unique_pool_candidates
					order_by = var:zg361_b1_quota_pool_tie_key
					max = 7
					root = { change_variable = { name = zg361_b1_unique_pool_cursor add = 1 } }
					set_variable = { name = zg361_rank value = root.var:zg361_b1_unique_pool_cursor }
					set_variable = { name = zg361_b1_pool_rank value = root.var:zg361_b1_unique_pool_cursor }
					set_variable = { name = zg361_pending_grade value = 2 }
					set_variable = { name = zg361_b1_newcomer_forced_bottom value = 0 }
				}
				set_variable = { name = zg361_b1_unique_pool_bottom_candidate_n value = 0 }
				set_variable = { name = zg361_b1_unique_pool_bottom_assigned value = 0 }
				set_variable = { name = zg361_b1_unique_pool_newcomer_bottom_exception value = 0 }
				every_in_list = {
					list = zg361_b1_unique_pool_candidates
					limit = { NOT = { has_character_flag = zg361_newcomer_this_cycle } }
					add_to_list = zg361_b1_unique_pool_bottom_candidates
					root = { change_variable = { name = zg361_b1_unique_pool_bottom_candidate_n add = 1 } }
				}
				set_variable = { name = zg361_b1_unique_pool_bottom_cursor value = 0 }
				if = {
					limit = {
						var:zg361_b1_unique_pool_bottom_slots >= 1
						var:zg361_b1_unique_pool_bottom_candidate_n >= 1
					}
					ordered_in_list = {
						list = zg361_b1_unique_pool_bottom_candidates
						order_by = var:zg361_b1_pool_rank
						max = 7
						if = {
							limit = { root.var:zg361_b1_unique_pool_bottom_assigned < root.var:zg361_b1_unique_pool_bottom_slots }
							set_variable = { name = zg361_pending_grade value = 1 }
							root = { change_variable = { name = zg361_b1_unique_pool_bottom_assigned add = 1 } }
						}
						root = { change_variable = { name = zg361_b1_unique_pool_bottom_cursor add = 1 } }
					}
				}
				if = {
					limit = { var:zg361_b1_unique_pool_bottom_assigned < var:zg361_b1_unique_pool_bottom_slots }
					set_variable = { name = zg361_b1_unique_pool_newcomer_bottom_exception value = 1 }
					ordered_in_list = {
						list = zg361_b1_unique_pool_candidates
						order_by = var:zg361_b1_pool_rank
						max = 7
						limit = { var:zg361_pending_grade = 2 }
						if = {
							limit = { root.var:zg361_b1_unique_pool_bottom_assigned < root.var:zg361_b1_unique_pool_bottom_slots }
							set_variable = { name = zg361_pending_grade value = 1 }
							set_variable = { name = zg361_b1_newcomer_forced_bottom value = 1 }
							root = { change_variable = { name = zg361_b1_unique_pool_bottom_assigned add = 1 } }
						}
					}
				}
				set_variable = { name = zg361_b1_unique_pool_top_assigned value = 0 }
				if = {
					limit = { var:zg361_b1_unique_pool_top_slots >= 1 }
					ordered_in_list = {
						list = zg361_b1_unique_pool_candidates
						order_by = var:zg361_b1_quota_pool_tie_key
						max = 7
						limit = { var:zg361_pending_grade = 2 }
						if = {
							limit = { root.var:zg361_b1_unique_pool_top_assigned < root.var:zg361_b1_unique_pool_top_slots }
							set_variable = { name = zg361_pending_grade value = 3 }
							root = { change_variable = { name = zg361_b1_unique_pool_top_assigned add = 1 } }
						}
					}
				}
				every_in_list = {
					list = zg361_b1_unique_pool_candidates
					set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = {
						limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
						set_variable = { name = zg361_b1_forced_down value = 1 }
					}
				}
				every_in_list = {
					list = zg361_b1_ready_managers
					limit = { var:zg361_b1_quota_pool_membership = 1 }
					set_variable = { name = zg361_pending_375_n value = 0 }
					set_variable = { name = zg361_pending_35_n value = 0 }
					set_variable = { name = zg361_pending_325_n value = 0 }
					set_variable = { name = zg361_b1_quota_pool_n value = root.var:zg361_b1_unique_pool_n }
					set_variable = { name = zg361_b1_quota_pool_top_slots value = root.var:zg361_b1_unique_pool_top_slots }
					set_variable = { name = zg361_b1_quota_pool_middle_slots value = root.var:zg361_b1_unique_pool_middle_slots }
					set_variable = { name = zg361_b1_quota_pool_bottom_slots value = root.var:zg361_b1_unique_pool_bottom_slots }
					# Copy the exact allocator before-image into both pooled books.  The
					# common superior owns the calculation variables, while the frozen
					# manager books are the later audit/scoreboard consumers.
					set_variable = { name = zg361_b1_quota_pool_top_raw_numerator value = root.var:zg361_b1_quota_top_raw_numerator }
					set_variable = { name = zg361_b1_quota_pool_middle_raw_numerator value = root.var:zg361_b1_quota_middle_raw_numerator }
					set_variable = { name = zg361_b1_quota_pool_bottom_raw_numerator value = root.var:zg361_b1_quota_bottom_raw_numerator }
					set_variable = { name = zg361_b1_quota_pool_top_floor value = root.var:zg361_b1_quota_top_floor }
					set_variable = { name = zg361_b1_quota_pool_middle_floor value = root.var:zg361_b1_quota_middle_floor }
					set_variable = { name = zg361_b1_quota_pool_bottom_floor value = root.var:zg361_b1_quota_bottom_floor }
					set_variable = { name = zg361_b1_quota_pool_top_remainder value = root.var:zg361_b1_quota_top_remainder }
					set_variable = { name = zg361_b1_quota_pool_middle_remainder value = root.var:zg361_b1_quota_middle_remainder }
					set_variable = { name = zg361_b1_quota_pool_bottom_remainder value = root.var:zg361_b1_quota_bottom_remainder }
					set_variable = { name = zg361_b1_quota_pool_top_award value = root.var:zg361_b1_quota_top_award }
					set_variable = { name = zg361_b1_quota_pool_middle_award value = root.var:zg361_b1_quota_middle_award }
					set_variable = { name = zg361_b1_quota_pool_bottom_award value = root.var:zg361_b1_quota_bottom_award }
					set_variable = { name = zg361_b1_quota_pool_rounding_method value = root.var:zg361_b1_quota_rounding_bank_method }
					set_variable = { name = zg361_b1_quota_pool_conservation_check value = root.var:zg361_b1_quota_conservation_check }
					set_variable = { name = zg361_b1_quota_pool_newcomer_bottom_exception value = root.var:zg361_b1_unique_pool_newcomer_bottom_exception }
					save_temporary_scope_as = zg361_b1_allocated_manager
						every_in_list = {
							variable = zg361_b1_subjects
							if = {
								limit = {
									has_variable = zg361_b1_case_owner
									has_variable = zg361_b1_case_subject
									has_variable = zg361_b1_cycle_serial
									has_variable = zg361_b1_case_serial
									has_variable = zg361_b1_case_state
									has_variable = zg361_b1_case_active
									var:zg361_b1_case_owner = scope:zg361_b1_allocated_manager
									var:zg361_b1_case_subject = this
									var:zg361_b1_cycle_serial = scope:zg361_b1_allocated_manager.var:zg361_b1_cycle_serial
									var:zg361_b1_case_serial = scope:zg361_b1_allocated_manager.var:zg361_b1_case_serial
									var:zg361_b1_case_state = 5
									var:zg361_b1_case_active = 1
								var:zg361_b1_roster_included = 1
								has_variable = zg361_pending_grade
							}
							if = { limit = { var:zg361_pending_grade = 3 } scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_375_n add = 1 } } }
							else_if = { limit = { var:zg361_pending_grade = 1 } scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_325_n add = 1 } } }
							else = { scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_35_n add = 1 } } }
						}
					}
					change_variable = { name = zg361_b1_quota_book_version add = 1 }
					zg361_b1_settle_due_debt_effect = yes
				}
				zg361_b1_execute_unique_pool_trade_effect = yes
			}
			else = {
				# Any count drift makes the supposed pair non-unique; both managers keep
				# their already-built local books and no pooled receipt is claimed.
				set_variable = { name = zg361_b1_unique_pool_active value = 0 }
				scope:zg361_b1_pool_three_manager = { set_variable = { name = zg361_b1_quota_pool_membership value = 0 } }
				scope:zg361_b1_pool_four_manager = { set_variable = { name = zg361_b1_quota_pool_membership value = 0 } }
			}
		}
		# #141 freezes only now, after every local or pooled book has reached its
		# final pre-calibration bands.  Opening before the 3+4 pool could strand a
		# subject that is no longer MIDDLE or lose the required TOP peer.
		zg361_b1_prepare_bank_must_review_effect = yes
		every_in_list = {
			variable = zg361_b1_ready_managers
			if = {
				limit = { var:zg361_b1_quota_pool_membership = 0 }
				zg361_b1_settle_due_debt_effect = yes
			}
			set_variable = { name = zg361_b1_cycle_state value = 6 }
			set_variable = { name = zg361_b1_m037_receipt_serial value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_m038_receipt_serial value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_m139_receipt_serial value = var:zg361_b1_case_serial }
			save_scope_as = zg361_b1_ticket_owner
			save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
			save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
			save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
			trigger_event = { id = zg361b1.111 days = 1 }
		}
		debug_log = "ZG361B1: exact quota bank closed with at most one unique same-function 3+4 pool"
	}
}

zg361_b1_apply_local_quota_effect = {
	set_variable = { name = zg361_b1_cycle_state value = 6 }
	zg361_b1_settle_due_debt_effect = yes
	set_variable = { name = zg361_b1_m038_receipt_serial value = var:zg361_b1_case_serial }
	zg361_b1_open_calibration_effect = yes
}

zg361_b1_rerank_frozen_quota_book_effect = {
	save_temporary_scope_as = zg361_b1_rerank_manager
	set_variable = { name = zg361_b1_rerank_n value = 0 }
	set_variable = { name = zg361_b1_rerank_fixed_top value = 0 }
	set_variable = { name = zg361_b1_rerank_fixed_middle value = 0 }
	set_variable = { name = zg361_b1_rerank_fixed_bottom value = 0 }
	every_in_list = {
		variable = zg361_b1_subjects
		limit = {
			var:zg361_b1_case_owner = root
			var:zg361_b1_case_subject = this
			var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
			var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
			var:zg361_b1_case_state = 7
			var:zg361_b1_case_active = 1
			var:zg361_b1_roster_included = 1
			var:zg361_b1_recusal_active = 1
			has_variable = zg361_pending_grade
		}
		if = { limit = { var:zg361_pending_grade = 3 } root = { change_variable = { name = zg361_b1_rerank_fixed_top add = 1 } } }
		else_if = { limit = { var:zg361_pending_grade = 1 } root = { change_variable = { name = zg361_b1_rerank_fixed_bottom add = 1 } } }
		else = { root = { change_variable = { name = zg361_b1_rerank_fixed_middle add = 1 } } }
	}
	set_variable = { name = zg361_b1_rerank_target_top value = { value = var:zg361_pending_375_n subtract = var:zg361_b1_rerank_fixed_top min = 0 } }
	set_variable = { name = zg361_b1_rerank_target_middle value = { value = var:zg361_pending_35_n subtract = var:zg361_b1_rerank_fixed_middle min = 0 } }
	set_variable = { name = zg361_b1_rerank_target_bottom value = { value = var:zg361_pending_325_n subtract = var:zg361_b1_rerank_fixed_bottom min = 0 } }
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					var:zg361_b1_case_owner = scope:zg361_b1_rerank_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_rerank_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_rerank_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0
					has_variable = zg361_pending_grade
					has_variable = zg361_b1_calibration_score
				}
			add_to_list = zg361_b1_rerank_candidates
			root = { change_variable = { name = zg361_b1_rerank_n add = 1 } }
		}
	}
	set_variable = { name = zg361_b1_rerank_cursor value = 0 }
	ordered_in_list = {
		list = zg361_b1_rerank_candidates
		order_by = var:zg361_b1_calibration_score
		max = { value = var:zg361_b1_rerank_n max = 80 }
		root = { change_variable = { name = zg361_b1_rerank_cursor add = 1 } }
		set_variable = { name = zg361_rank value = root.var:zg361_b1_rerank_cursor }
		set_variable = { name = zg361_b1_rerank_order value = root.var:zg361_b1_rerank_cursor }
		set_variable = { name = zg361_pending_grade value = 2 }
		set_variable = { name = zg361_b1_newcomer_forced_bottom value = 0 }
	}
	set_variable = { name = zg361_b1_rerank_bottom_candidate_n value = 0 }
	set_variable = { name = zg361_b1_rerank_bottom_assigned value = 0 }
	set_variable = { name = zg361_b1_rerank_newcomer_bottom_exception value = 0 }
	every_in_list = {
		list = zg361_b1_rerank_candidates
		limit = { NOT = { has_character_flag = zg361_newcomer_this_cycle } }
		add_to_list = zg361_b1_rerank_bottom_candidates
		root = { change_variable = { name = zg361_b1_rerank_bottom_candidate_n add = 1 } }
	}
	set_variable = { name = zg361_b1_rerank_bottom_cursor value = 0 }
	if = {
		limit = { var:zg361_b1_rerank_target_bottom >= 1 var:zg361_b1_rerank_bottom_candidate_n >= 1 }
		ordered_in_list = {
			list = zg361_b1_rerank_bottom_candidates
			order_by = var:zg361_rank
			max = { value = var:zg361_b1_rerank_bottom_candidate_n max = 80 }
			if = {
				limit = { root.var:zg361_b1_rerank_bottom_assigned < root.var:zg361_b1_rerank_target_bottom }
				set_variable = { name = zg361_pending_grade value = 1 }
				root = { change_variable = { name = zg361_b1_rerank_bottom_assigned add = 1 } }
			}
			root = { change_variable = { name = zg361_b1_rerank_bottom_cursor add = 1 } }
		}
	}
	if = {
		limit = { var:zg361_b1_rerank_bottom_assigned < var:zg361_b1_rerank_target_bottom }
		set_variable = { name = zg361_b1_rerank_newcomer_bottom_exception value = 1 }
		ordered_in_list = {
			list = zg361_b1_rerank_candidates
			order_by = var:zg361_rank
			max = { value = var:zg361_b1_rerank_n max = 80 }
			limit = { var:zg361_pending_grade = 2 }
			if = {
				limit = { root.var:zg361_b1_rerank_bottom_assigned < root.var:zg361_b1_rerank_target_bottom }
				set_variable = { name = zg361_pending_grade value = 1 }
				set_variable = { name = zg361_b1_newcomer_forced_bottom value = 1 }
				root = { change_variable = { name = zg361_b1_rerank_bottom_assigned add = 1 } }
			}
		}
	}
	set_variable = { name = zg361_b1_rerank_top_assigned value = 0 }
	if = {
		limit = { var:zg361_b1_rerank_target_top >= 1 }
		ordered_in_list = {
			list = zg361_b1_rerank_candidates
			order_by = var:zg361_b1_calibration_score
			max = { value = var:zg361_b1_rerank_n max = 80 }
			limit = { var:zg361_pending_grade = 2 }
			if = {
				limit = { root.var:zg361_b1_rerank_top_assigned < root.var:zg361_b1_rerank_target_top }
				set_variable = { name = zg361_pending_grade value = 3 }
				root = { change_variable = { name = zg361_b1_rerank_top_assigned add = 1 } }
			}
		}
	}
	every_in_list = {
		list = zg361_b1_rerank_candidates
		set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
		set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade } }
		set_variable = { name = zg361_b1_forced_down value = 0 }
		if = {
			limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
			set_variable = { name = zg361_b1_forced_down value = 1 }
		}
	}
	change_variable = { name = zg361_b1_quota_book_version add = 1 }
}

zg361_b1_build_agenda_and_attention_effect = {
	if = {
		limit = { has_variable_list = zg361_b1_agenda_subjects }
		clear_variable_list = zg361_b1_agenda_subjects
	}
	if = {
		limit = { has_variable_list = zg361_b1_processing_subjects }
		clear_variable_list = zg361_b1_processing_subjects
	}
	set_variable = { name = zg361_b1_agenda_old_hash value = 0 }
	if = { limit = { has_variable = zg361_b1_agenda_hash } set_variable = { name = zg361_b1_agenda_old_hash value = var:zg361_b1_agenda_hash } }
	set_variable = { name = zg361_b1_agenda_version value = { value = var:zg361_b1_agenda_version add = 1 } }
	set_variable = { name = zg361_b1_agenda_n value = 0 }
	set_variable = { name = zg361_b1_processing_n value = 0 }
	set_variable = { name = zg361_b1_agenda_mode value = var:zg361_b1_m137_mode }
	set_variable = { name = zg361_b1_agenda_header_object_available value = 0 }
	set_variable = { name = zg361_b1_agenda_header_state value = 0 }
	remove_variable = zg361_b1_agenda_header_owner
	remove_variable = zg361_b1_agenda_header_subject
	set_variable = { name = zg361_b1_agenda_header_cycle value = 0 }
	set_variable = { name = zg361_b1_agenda_header_case value = 0 }
	set_variable = { name = zg361_b1_agenda_chair_bias_risk value = 0 }
	if = {
		limit = { var:zg361_b1_m137_mode != 3 }
		set_variable = { name = zg361_b1_agenda_header_object_available value = 1 }
		set_variable = { name = zg361_b1_agenda_header_owner value = this }
		set_variable = { name = zg361_b1_agenda_header_subject value = this }
		set_variable = { name = zg361_b1_agenda_header_cycle value = var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_agenda_header_case value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_agenda_header_state value = 1 }
		set_variable = { name = zg361_b1_agenda_chair value = this }
		set_variable = { name = zg361_b1_agenda_frozen_year value = current_year }
		if = { limit = { var:zg361_b1_m137_mode = 2 } set_variable = { name = zg361_b1_agenda_chair_bias_risk value = 1 } }
	}
	save_temporary_scope_as = zg361_b1_agenda_manager
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
				has_variable = zg361_b1_case_active
				var:zg361_b1_case_owner = scope:zg361_b1_agenda_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_agenda_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_agenda_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				has_variable = zg361_pending_grade
			}
			set_variable = { name = zg361_b1_agenda_sort_key value = { value = var:zg361_rank multiply = -1 } }
			if = {
				limit = { var:zg361_b1_must_review_state = 1 }
				set_variable = { name = zg361_b1_agenda_sort_key value = 100000 }
			}
			else_if = {
				limit = { scope:zg361_b1_agenda_manager.var:zg361_b1_agenda_mode = 1 }
				set_variable = {
					name = zg361_b1_agenda_rotation_distance
					value = { value = var:zg361_b1_roster_frozen_order subtract = scope:zg361_b1_agenda_manager.var:zg361_b1_agenda_rotation_start }
				}
				if = {
					limit = { var:zg361_b1_agenda_rotation_distance < 0 }
					change_variable = { name = zg361_b1_agenda_rotation_distance add = scope:zg361_b1_agenda_manager.var:zg361_b1_subject_n }
				}
				set_variable = {
					name = zg361_b1_agenda_sort_key
					value = { value = 1000 subtract = var:zg361_b1_agenda_rotation_distance }
				}
			}
			else_if = {
				limit = { scope:zg361_b1_agenda_manager.var:zg361_b1_agenda_mode = 2 }
				set_variable = { name = zg361_b1_agenda_strategic_flag value = 0 }
				set_variable = { name = zg361_b1_agenda_strategic_reason value = 0 }
				if = {
					limit = { OR = { var:zg361_b1_role_code >= 3 has_relation_friend = scope:zg361_b1_agenda_manager } }
					set_variable = { name = zg361_b1_agenda_strategic_flag value = 1 }
					set_variable = { name = zg361_b1_agenda_strategic_reason value = var:zg361_b1_role_code }
					if = { limit = { has_relation_friend = scope:zg361_b1_agenda_manager } set_variable = { name = zg361_b1_agenda_strategic_reason value = 5 } }
				}
				set_variable = {
					name = zg361_b1_agenda_sort_key
					value = { value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order }
				}
				if = { limit = { var:zg361_b1_agenda_strategic_flag = 1 } change_variable = { name = zg361_b1_agenda_sort_key add = 1000000 } }
			}
			set_variable = { name = zg361_b1_late_evidence_delta value = { value = var:zg361_b1_evidence_late subtract = var:zg361_b1_evidence_mid } }
			set_variable = { name = zg361_b1_agenda_review_duration_minutes value = 0 }
			set_variable = { name = zg361_b1_late_evidence_magnitude value = var:zg361_b1_late_evidence_delta }
			if = {
				limit = { var:zg361_b1_late_evidence_magnitude < 0 }
				set_variable = { name = zg361_b1_late_evidence_magnitude value = { value = var:zg361_b1_late_evidence_magnitude multiply = -1 } }
			}
			add_to_list = zg361_b1_agenda_candidates
			root = {
				change_variable = { name = zg361_b1_processing_n add = 1 }
				if = { limit = { var:zg361_b1_m137_mode != 3 } change_variable = { name = zg361_b1_agenda_n add = 1 } }
			}
		}
	}
	set_variable = { name = zg361_b1_agenda_cursor value = 0 }
	set_variable = { name = zg361_b1_agenda_remaining_top_cursor value = var:zg361_pending_375_n }
	set_variable = { name = zg361_b1_agenda_remaining_middle_cursor value = var:zg361_pending_35_n }
	set_variable = { name = zg361_b1_agenda_remaining_bottom_cursor value = var:zg361_pending_325_n }
	set_variable = { name = zg361_b1_agenda_hash value = { value = var:zg361_b1_case_serial multiply = 1000 } }
	ordered_in_list = {
		list = zg361_b1_agenda_candidates
		order_by = var:zg361_b1_agenda_sort_key
		max = { value = var:zg361_b1_processing_n max = 80 }
		root = { change_variable = { name = zg361_b1_agenda_cursor add = 1 } }
		set_variable = { name = zg361_b1_processing_order value = root.var:zg361_b1_agenda_cursor }
		save_temporary_scope_as = zg361_b1_agenda_subject_to_store
		root = {
			add_to_variable_list = { name = zg361_b1_processing_subjects target = scope:zg361_b1_agenda_subject_to_store }
			change_variable = { name = zg361_b1_agenda_hash add = { value = scope:zg361_b1_agenda_subject_to_store.var:zg361_b1_roster_frozen_order multiply = var:zg361_b1_agenda_cursor } }
		}
		if = {
			limit = { root.var:zg361_b1_m137_mode != 3 }
			set_variable = { name = zg361_b1_agenda_item_object_available value = 1 }
			set_variable = { name = zg361_b1_agenda_item_owner value = root }
			set_variable = { name = zg361_b1_agenda_item_subject value = this }
			set_variable = { name = zg361_b1_agenda_item_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_agenda_item_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_agenda_item_state value = 1 }
			set_variable = { name = zg361_b1_agenda_order value = root.var:zg361_b1_agenda_cursor }
			set_variable = { name = zg361_b1_agenda_item_mode value = root.var:zg361_b1_agenda_mode }
			set_variable = { name = zg361_b1_agenda_item_version value = root.var:zg361_b1_agenda_version }
			set_variable = { name = zg361_b1_agenda_remaining_top value = root.var:zg361_b1_agenda_remaining_top_cursor }
			set_variable = { name = zg361_b1_agenda_remaining_middle value = root.var:zg361_b1_agenda_remaining_middle_cursor }
			set_variable = { name = zg361_b1_agenda_remaining_bottom value = root.var:zg361_b1_agenda_remaining_bottom_cursor }
			if = { limit = { var:zg361_pending_grade = 3 } root = { change_variable = { name = zg361_b1_agenda_remaining_top_cursor add = -1 } } }
			else_if = { limit = { var:zg361_pending_grade = 1 } root = { change_variable = { name = zg361_b1_agenda_remaining_bottom_cursor add = -1 } } }
			else = { root = { change_variable = { name = zg361_b1_agenda_remaining_middle_cursor add = -1 } } }
			set_variable = { name = zg361_b1_agenda_tail_pressure value = 0 }
			if = { limit = { var:zg361_b1_agenda_order > 3 } set_variable = { name = zg361_b1_agenda_tail_pressure value = 1 } }
			set_variable = { name = zg361_b1_m137_receipt_serial value = var:zg361_b1_agenda_item_case }
			root = { add_to_variable_list = { name = zg361_b1_agenda_subjects target = scope:zg361_b1_agenda_subject_to_store } }
		}
	}
	set_variable = { name = zg361_b1_agenda_new_hash value = var:zg361_b1_agenda_hash }
	set_variable = { name = zg361_b1_agenda_rebuild_reason value = 0 }
	if = { limit = { var:zg361_b1_agenda_version > 1 NOT = { var:zg361_b1_agenda_old_hash = var:zg361_b1_agenda_new_hash } } set_variable = { name = zg361_b1_agenda_rebuild_reason value = 1 } }
	# Three ten-minute seats are frozen. Choice B deliberately leaves seat 3
	# unconsumed, then replaces it with agenda item 4 and pays real overtime.
	set_variable = { name = zg361_b1_attention_total_seats value = { value = var:zg361_b1_processing_n max = 3 } }
	set_variable = { name = zg361_b1_attention_total_minutes value = { value = var:zg361_b1_attention_total_seats multiply = 10 } }
	set_variable = { name = zg361_b1_attention_spent_minutes value = 0 }
	set_variable = { name = zg361_b1_attention_overtime_minutes value = 0 }
	set_variable = { name = zg361_b1_attention_patience_cost value = 0 }
	set_variable = { name = zg361_b1_attention_political_cost value = 0 }
	set_variable = { name = zg361_b1_attention_overtime_enabled value = 0 }
	if = {
		limit = {
			has_variable = zg361_mechanism_043_choice
			var:zg361_mechanism_043_choice = 2
			var:zg361_b1_processing_n >= 4
		}
		set_variable = { name = zg361_b1_attention_overtime_enabled value = 1 }
	}
	set_variable = { name = zg361_b1_attention_cursor value = 0 }
	every_in_list = {
		variable = zg361_b1_processing_subjects
		root = { change_variable = { name = zg361_b1_attention_cursor add = 1 } }
		set_variable = { name = zg361_b1_attention_frozen_grade value = var:zg361_pending_grade }
		if = {
			limit = { root.var:zg361_b1_attention_cursor <= root.var:zg361_b1_attention_total_seats }
			set_variable = { name = zg361_b1_attention_seat value = root.var:zg361_b1_attention_cursor }
			set_variable = { name = zg361_b1_attention_bound value = 1 }
			set_variable = { name = zg361_b1_attention_evidence_serial value = var:zg361_b1_fact_sheet_serial }
			set_variable = { name = zg361_b1_attention_owner value = root }
			if = {
				limit = { root.var:zg361_b1_attention_overtime_enabled = 1 root.var:zg361_b1_attention_cursor = 3 }
				set_variable = { name = zg361_b1_attention_consumed value = 0 }
				save_temporary_scope_as = zg361_b1_attention_displaced_subject_scope
				root = { set_variable = { name = zg361_b1_attention_displaced_subject value = scope:zg361_b1_attention_displaced_subject_scope } }
			}
			else = {
				set_variable = { name = zg361_b1_attention_consumed value = 1 }
				set_variable = { name = zg361_b1_attention_minutes_used value = 10 }
				set_variable = { name = zg361_b1_agenda_review_duration_minutes value = 10 }
				set_variable = { name = zg361_b1_pending_candidate value = 1 }
				root = { change_variable = { name = zg361_b1_attention_spent_minutes add = 10 } }
				if = {
					limit = { var:zg361_b1_must_review_state = 1 }
					set_variable = { name = zg361_b1_must_review_attention_consumed value = 1 }
					root = {
						set_variable = { name = zg361_b1_must_review_agenda_consumed value = 1 }
						set_variable = { name = zg361_b1_must_review_attention_debit value = 1 }
					}
				}
			}
		}
		else_if = {
			limit = { root.var:zg361_b1_attention_overtime_enabled = 1 root.var:zg361_b1_attention_cursor = 4 }
			save_temporary_scope_as = zg361_b1_attention_favored_subject_scope
			root = { set_variable = { name = zg361_b1_attention_favored_subject value = scope:zg361_b1_attention_favored_subject_scope } }
		}
	}
	if = {
		limit = {
			var:zg361_b1_attention_overtime_enabled = 1
			has_variable = zg361_b1_attention_displaced_subject
			has_variable = zg361_b1_attention_favored_subject
		}
		var:zg361_b1_attention_displaced_subject = {
			set_variable = { name = zg361_b1_attention_bound value = 0 }
			set_variable = { name = zg361_b1_attention_displaced value = 1 }
		}
		var:zg361_b1_attention_favored_subject = {
			set_variable = { name = zg361_b1_attention_seat value = 3 }
			set_variable = { name = zg361_b1_attention_bound value = 1 }
			set_variable = { name = zg361_b1_attention_consumed value = 1 }
			set_variable = { name = zg361_b1_attention_minutes_used value = 20 }
			set_variable = { name = zg361_b1_agenda_review_duration_minutes value = 20 }
			set_variable = { name = zg361_b1_attention_evidence_serial value = var:zg361_b1_fact_sheet_serial }
			set_variable = { name = zg361_b1_attention_owner value = root }
			set_variable = { name = zg361_b1_pending_candidate value = 1 }
		}
		change_variable = { name = zg361_b1_attention_spent_minutes add = 20 }
		set_variable = { name = zg361_b1_attention_overtime_minutes value = 10 }
		set_variable = { name = zg361_b1_attention_patience_cost value = 10 }
		set_variable = { name = zg361_b1_attention_political_cost value = 25 }
		add_prestige = -25
		add_stress = 10
	}
	set_variable = {
		name = zg361_b1_attention_remaining_minutes
		value = { value = var:zg361_b1_attention_total_minutes subtract = var:zg361_b1_attention_spent_minutes min = 0 }
	}
	set_variable = { name = zg361_b1_m043_receipt_serial value = var:zg361_b1_case_serial }
}

zg361_b1_finalize_agenda_audit_effect = {
	set_variable = { name = zg361_b1_agenda_reviewed_n value = 0 }
	set_variable = { name = zg361_b1_agenda_changed_n value = 0 }
	set_variable = { name = zg361_b1_agenda_review_minutes value = 0 }
	set_variable = { name = zg361_b1_agenda_skipped_n value = 0 }
	if = {
		limit = {
			var:zg361_b1_m137_mode != 3
			var:zg361_b1_agenda_header_object_available = 1
			var:zg361_b1_agenda_header_owner = this
			var:zg361_b1_agenda_header_subject = this
			var:zg361_b1_agenda_header_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_agenda_header_case = var:zg361_b1_case_serial
			var:zg361_b1_agenda_header_state = 1
		}
		save_temporary_scope_as = zg361_b1_agenda_finalize_manager
		every_in_list = {
			variable = zg361_b1_agenda_subjects
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_agenda_finalize_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_agenda_finalize_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_agenda_finalize_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_agenda_item_object_available = 1
				var:zg361_b1_agenda_item_owner = scope:zg361_b1_agenda_finalize_manager
				var:zg361_b1_agenda_item_subject = this
				var:zg361_b1_agenda_item_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_agenda_item_case = var:zg361_b1_case_serial
				var:zg361_b1_agenda_item_state = 1
			}
			if = {
				limit = { var:zg361_b1_attention_consumed = 1 }
				set_variable = { name = zg361_b1_agenda_final_grade value = var:zg361_pending_grade }
				set_variable = { name = zg361_b1_agenda_grade_changed value = 0 }
				if = {
					limit = { NOT = { var:zg361_b1_agenda_final_grade = var:zg361_b1_attention_frozen_grade } }
					set_variable = { name = zg361_b1_agenda_grade_changed value = 1 }
					scope:zg361_b1_agenda_finalize_manager = { change_variable = { name = zg361_b1_agenda_changed_n add = 1 } }
				}
				set_variable = { name = zg361_b1_agenda_item_state value = 2 }
				scope:zg361_b1_agenda_finalize_manager = {
					change_variable = { name = zg361_b1_agenda_reviewed_n add = 1 }
					change_variable = { name = zg361_b1_agenda_review_minutes add = prev.var:zg361_b1_agenda_review_duration_minutes }
				}
			}
			else = {
				set_variable = { name = zg361_b1_agenda_item_state value = 3 }
				set_variable = { name = zg361_b1_agenda_skipped value = 1 }
				scope:zg361_b1_agenda_finalize_manager = { change_variable = { name = zg361_b1_agenda_skipped_n add = 1 } }
			}
		}
		set_variable = { name = zg361_b1_agenda_header_state value = 2 }
		set_variable = { name = zg361_b1_agenda_closed_case value = var:zg361_b1_case_serial }
	}
}

zg361_b1_finalize_huddle_diff_effect = {
	if = {
		limit = {
			var:zg361_b1_huddle_attendee_attending = 1
			var:zg361_b1_huddle_attendee_state = 1
			var:zg361_b1_huddle_attendee_route != 3
			has_variable = zg361_b1_huddle_attendee_owner
			var:zg361_b1_huddle_attendee_subject = this
			var:zg361_b1_huddle_attendee_owner = {
				var:zg361_b1_huddle_host_object_available = 1
				var:zg361_b1_huddle_host_owner = this
				var:zg361_b1_huddle_host_subject = this
				var:zg361_b1_huddle_host_cycle = prev.var:zg361_b1_huddle_attendee_cycle
				var:zg361_b1_huddle_host_case = prev.var:zg361_b1_huddle_attendee_case
				var:zg361_b1_huddle_host_id = prev.var:zg361_b1_huddle_attendee_id
				var:zg361_b1_huddle_host_state = 1
			}
		}
		set_variable = { name = zg361_b1_huddle_attendee_diff_n value = 0 }
		set_variable = { name = zg361_b1_huddle_attendee_formal_hash value = { value = var:zg361_b1_case_serial multiply = 1000 } }
		save_temporary_scope_as = zg361_b1_huddle_finalize_manager
		every_in_list = {
			variable = zg361_b1_processing_subjects
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_huddle_finalize_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_huddle_finalize_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_huddle_finalize_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_huddle_assignment_available = 1
				var:zg361_b1_huddle_assignment_owner = scope:zg361_b1_huddle_finalize_manager
				var:zg361_b1_huddle_assignment_subject = this
				var:zg361_b1_huddle_assignment_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_huddle_assignment_case = var:zg361_b1_case_serial
				var:zg361_b1_huddle_assignment_state = 1
			}
			set_variable = { name = zg361_b1_huddle_formal_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_huddle_grade_diff value = { value = var:zg361_b1_huddle_formal_grade subtract = var:zg361_b1_huddle_suggested_grade } }
			set_variable = { name = zg361_b1_huddle_assignment_state value = 2 }
			if = {
				limit = { NOT = { var:zg361_b1_huddle_grade_diff = 0 } }
				scope:zg361_b1_huddle_finalize_manager = { change_variable = { name = zg361_b1_huddle_attendee_diff_n add = 1 } }
			}
			save_temporary_scope_as = zg361_b1_huddle_hash_subject
			scope:zg361_b1_huddle_finalize_manager = {
				change_variable = { name = zg361_b1_huddle_attendee_formal_hash add = { value = scope:zg361_b1_huddle_hash_subject.var:zg361_b1_roster_frozen_order multiply = scope:zg361_b1_huddle_hash_subject.var:zg361_pending_grade } }
			}
		}
		set_variable = { name = zg361_b1_huddle_attendee_minutes_consumed value = var:zg361_b1_huddle_attendee_minutes_budget }
		set_variable = { name = zg361_b1_huddle_attendee_state value = 2 }
		set_variable = { name = zg361_b1_huddle_attendee_consumed_case value = var:zg361_b1_case_serial }
		if = {
			limit = { var:zg361_b1_huddle_attendee_ack_posted = 0 }
			set_variable = { name = zg361_b1_huddle_attendee_ack_posted value = 1 }
			var:zg361_b1_huddle_attendee_owner = {
				if = {
					limit = {
						var:zg361_b1_huddle_host_object_available = 1
						var:zg361_b1_huddle_host_state = 1
						var:zg361_b1_huddle_host_id = prev.var:zg361_b1_huddle_attendee_id
					}
					change_variable = { name = zg361_b1_huddle_host_ack_n add = 1 }
					if = {
						limit = { var:zg361_b1_huddle_host_ack_n = var:zg361_b1_huddle_host_attendee_n }
						set_variable = { name = zg361_b1_huddle_host_state value = 2 }
						set_variable = { name = zg361_b1_huddle_host_closed_year value = current_year }
					}
				}
			}
		}
	}
}

zg361_b1_consume_must_review_effect = {
	set_variable = { name = zg361_b1_must_review_swap_executed value = 0 }
	set_variable = { name = zg361_b1_must_review_swap_candidate_n value = 0 }
	set_variable = { name = zg361_b1_must_review_conservation_valid value = 0 }
	if = {
		limit = {
			var:zg361_b1_must_review_manager_link_available = 1
			var:zg361_b1_must_review_manager_link_state = 1
			has_variable = zg361_b1_must_review_manager_link_subject
			var:zg361_b1_must_review_manager_link_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_must_review_manager_link_case = var:zg361_b1_case_serial
		}
		var:zg361_b1_must_review_manager_link_subject = {
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_recusal_active = 0
					var:zg361_b1_must_review_object_available = 1
					var:zg361_b1_must_review_object_owner = root
					var:zg361_b1_must_review_object_subject = this
					var:zg361_b1_must_review_object_cycle = var:zg361_b1_cycle_serial
					var:zg361_b1_must_review_object_case = var:zg361_b1_case_serial
					var:zg361_b1_must_review_object_state = 1
					var:zg361_b1_must_review_state = 1
					var:zg361_b1_must_review_manager = root
					var:zg361_b1_must_review_subject = this
					var:zg361_b1_must_review_attention_consumed = 1
					var:zg361_b1_must_review_reason_fact >= 1
				}
				set_variable = { name = zg361_b1_must_review_consumer_open value = 1 }
				save_temporary_scope_as = zg361_b1_must_review_swap_subject
				if = {
					limit = {
						var:zg361_b1_must_review_route = 2
						var:zg361_pending_grade = 2
						has_variable = zg361_b1_must_review_swap_peer
						var:zg361_b1_must_review_swap_peer = root.var:zg361_b1_must_review_manager_link_peer
					}
					root = {
						if = {
							limit = {
								has_variable = zg361_b1_must_review_manager_link_peer
							}
							var:zg361_b1_must_review_manager_link_peer = {
								if = {
									limit = {
										var:zg361_b1_case_owner = root
										var:zg361_b1_case_subject = this
										var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
										var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
										var:zg361_b1_case_state = 7
										var:zg361_b1_case_active = 1
										var:zg361_b1_roster_included = 1
										var:zg361_b1_recusal_active = 0
										var:zg361_pending_grade = 3
										NOT = { this = scope:zg361_b1_must_review_swap_subject }
									}
									save_temporary_scope_as = zg361_b1_must_review_swap_peer
									root = { change_variable = { name = zg361_b1_must_review_swap_candidate_n add = 1 } }
								}
							}
						}
					}
				}
			}
		}
	}
	if = {
		limit = {
			var:zg361_b1_must_review_swap_candidate_n = 1
			exists = scope:zg361_b1_must_review_swap_subject
			exists = scope:zg361_b1_must_review_swap_peer
		}
		set_variable = { name = zg361_b1_must_review_before_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_must_review_before_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_must_review_before_bottom value = var:zg361_pending_325_n }
		set_variable = { name = zg361_b1_must_review_book_version_before value = var:zg361_b1_quota_book_version }
		scope:zg361_b1_must_review_swap_subject = {
			set_variable = { name = zg361_b1_must_review_subject_before value = 2 }
			set_variable = { name = zg361_b1_must_review_subject_after value = 3 }
			set_variable = { name = zg361_pending_grade value = 3 }
			set_variable = { name = zg361_b1_quota_snapshot value = 3 }
			set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 3 subtract = var:zg361_b1_shadow_grade } }
			set_variable = { name = zg361_b1_must_review_swap_peer value = scope:zg361_b1_must_review_swap_peer }
			set_variable = { name = zg361_b1_must_review_swap_executed value = 1 }
		}
		scope:zg361_b1_must_review_swap_peer = {
			set_variable = { name = zg361_b1_must_review_peer_before value = 3 }
			set_variable = { name = zg361_b1_must_review_peer_after value = 2 }
			set_variable = { name = zg361_pending_grade value = 2 }
			set_variable = { name = zg361_b1_quota_snapshot value = 2 }
			set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
			set_variable = { name = zg361_b1_must_review_swap_subject value = scope:zg361_b1_must_review_swap_subject }
			set_variable = { name = zg361_b1_must_review_peer_audit value = 1 }
		}
		set_variable = { name = zg361_b1_must_review_after_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_must_review_after_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_must_review_after_bottom value = var:zg361_pending_325_n }
		if = {
			limit = {
				var:zg361_b1_must_review_before_top = var:zg361_b1_must_review_after_top
				var:zg361_b1_must_review_before_middle = var:zg361_b1_must_review_after_middle
				var:zg361_b1_must_review_before_bottom = var:zg361_b1_must_review_after_bottom
			}
			set_variable = { name = zg361_b1_must_review_conservation_valid value = 1 }
			set_variable = { name = zg361_b1_must_review_swap_executed value = 1 }
			change_variable = { name = zg361_b1_quota_book_version add = 1 }
			set_variable = { name = zg361_b1_must_review_book_version_after value = var:zg361_b1_quota_book_version }
			set_variable = { name = zg361_b1_must_review_manager_link_state value = 2 }
			scope:zg361_b1_must_review_swap_subject = { set_variable = { name = zg361_b1_must_review_book_version_after value = root.var:zg361_b1_quota_book_version } }
		}
	}
	else_if = {
		limit = {
			var:zg361_b1_must_review_manager_link_available = 1
			var:zg361_b1_must_review_manager_link_state = 1
			var:zg361_b1_must_review_manager_link_route = 2
		}
		set_variable = { name = zg361_b1_must_review_manager_link_state value = 3 }
		set_variable = { name = zg361_b1_must_review_cancel_reason value = 1 }
		if = {
			limit = { has_variable = zg361_b1_must_review_manager_link_subject }
			var:zg361_b1_must_review_manager_link_subject = {
				if = {
					limit = {
						var:zg361_b1_must_review_object_available = 1
						var:zg361_b1_must_review_object_owner = root
						var:zg361_b1_must_review_object_subject = this
						var:zg361_b1_must_review_object_state = 1
					}
					set_variable = { name = zg361_b1_must_review_object_state value = 3 }
					set_variable = { name = zg361_b1_must_review_state value = 3 }
					set_variable = { name = zg361_b1_must_review_cancel_reason value = 1 }
				}
			}
		}
	}
}

# #144 consumes a real pre-huddle seat.  Route A freezes one named dissent with
# a non-zero fact reason and an independent superior reviewer; route B freezes
# only a consensus record and never manufactures a minority identity.
zg361_b1_record_named_dissent_effect = {
	set_variable = { name = zg361_b1_consensus_object_available value = 0 }
	if = {
		limit = {
			var:zg361_b1_m144_mode = 1
			var:zg361_b1_huddle_attendee_attending = 1
			var:zg361_b1_dissent_used = 0
			var:zg361_b1_calibration_attention >= 1
			has_variable = zg361_b1_bank_superior
			NOT = { var:zg361_b1_bank_superior = this }
			var:zg361_b1_huddle_attendee_owner = var:zg361_b1_bank_superior
			var:zg361_b1_huddle_attendee_subject = this
			var:zg361_b1_huddle_attendee_state = 1
			var:zg361_b1_bank_superior = {
				var:zg361_b1_huddle_host_object_available = 1
				var:zg361_b1_huddle_host_owner = this
				var:zg361_b1_huddle_host_subject = this
				var:zg361_b1_huddle_host_cycle = prev.var:zg361_b1_huddle_attendee_cycle
				var:zg361_b1_huddle_host_case = prev.var:zg361_b1_huddle_attendee_case
				var:zg361_b1_huddle_host_id = prev.var:zg361_b1_huddle_attendee_id
				var:zg361_b1_huddle_host_state = 1
				var:zg361_b1_dissent_review_attention_budget >= 1
			}
		}
		set_variable = { name = zg361_b1_dissent_candidate_n value = 0 }
		ordered_in_list = {
			variable = zg361_b1_processing_subjects
			order_by = var:zg361_b1_calibration_score
			max = 1
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_recusal_active = 0
				var:zg361_b1_fact_sheet_serial >= 1
				var:zg361_pending_grade = 2
				NOT = { this = root.var:zg361_b1_bank_superior }
			}
			save_temporary_scope_as = zg361_b1_dissent_subject_scope
			set_variable = { name = zg361_b1_dissent_object_available value = 1 }
			set_variable = { name = zg361_b1_dissent_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 44 } }
			set_variable = { name = zg361_b1_dissent_object_owner value = root }
			set_variable = { name = zg361_b1_dissent_object_subject value = this }
			set_variable = { name = zg361_b1_dissent_object_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_dissent_object_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_dissent_object_state value = 1 }
			set_variable = { name = zg361_b1_dissent_state value = 1 }
			set_variable = { name = zg361_b1_dissent_manager value = root }
			set_variable = { name = zg361_b1_dissent_subject value = this }
			set_variable = { name = zg361_b1_dissent_reason_fact value = var:zg361_b1_fact_sheet_serial }
			set_variable = { name = zg361_b1_dissent_timestamp_year value = current_year }
			set_variable = { name = zg361_b1_dissent_recommendation value = 3 }
			set_variable = { name = zg361_b1_dissent_original_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_dissent_reviewer value = root.var:zg361_b1_bank_superior }
			set_variable = { name = zg361_b1_dissent_attention_debit value = 1 }
			set_variable = { name = zg361_b1_dissent_attention_reserved value = 1 }
			set_variable = { name = zg361_b1_dissent_review_attention_receipt_id value = { value = var:zg361_b1_dissent_object_id multiply = 10 add = 1 } }
			var:zg361_b1_dissent_reviewer = { change_variable = { name = zg361_b1_dissent_review_attention_budget add = -1 } }
			set_variable = { name = zg361_b1_m144_receipt_serial value = var:zg361_b1_case_serial }
			root = {
				set_variable = { name = zg361_b1_dissent_subject value = scope:zg361_b1_dissent_subject_scope }
				set_variable = { name = zg361_b1_dissent_reason_fact value = scope:zg361_b1_dissent_subject_scope.var:zg361_b1_fact_sheet_serial }
				set_variable = { name = zg361_b1_dissent_used value = 1 }
				change_variable = { name = zg361_b1_calibration_attention add = -1 }
				change_variable = { name = zg361_b1_dissent_candidate_n add = 1 }
			}
		}
	}
	else_if = {
		limit = {
			var:zg361_b1_m144_mode = 2
			var:zg361_b1_huddle_attendee_attending = 1
			has_variable = zg361_b1_bank_superior
			var:zg361_b1_huddle_attendee_owner = var:zg361_b1_bank_superior
			var:zg361_b1_huddle_attendee_subject = this
			var:zg361_b1_huddle_attendee_state = 1
			var:zg361_b1_bank_superior = {
				var:zg361_b1_huddle_host_object_available = 1
				var:zg361_b1_huddle_host_owner = this
				var:zg361_b1_huddle_host_subject = this
				var:zg361_b1_huddle_host_cycle = prev.var:zg361_b1_huddle_attendee_cycle
				var:zg361_b1_huddle_host_case = prev.var:zg361_b1_huddle_attendee_case
				var:zg361_b1_huddle_host_id = prev.var:zg361_b1_huddle_attendee_id
				var:zg361_b1_huddle_host_state = 1
			}
		}
		set_variable = { name = zg361_b1_consensus_candidate_n value = 0 }
		var:zg361_b1_bank_superior = { save_temporary_scope_as = zg361_b1_consensus_bank }
		ordered_in_list = {
			variable = zg361_b1_processing_subjects
			order_by = var:zg361_b1_calibration_score
			max = 1
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_pending_grade = 2
			}
			save_temporary_scope_as = zg361_b1_consensus_subject_scope
			set_variable = { name = zg361_b1_consensus_object_available value = 1 }
			set_variable = { name = zg361_b1_consensus_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 44 } }
			set_variable = { name = zg361_b1_consensus_owner value = root }
			set_variable = { name = zg361_b1_consensus_subject value = this }
			set_variable = { name = zg361_b1_consensus_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_consensus_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_consensus_state value = 1 }
			set_variable = { name = zg361_b1_consensus_huddle_id value = root.var:zg361_b1_huddle_attendee_id }
			set_variable = { name = zg361_b1_consensus_final_band value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_consensus_final_vote value = 1 }
			set_variable = { name = zg361_b1_consensus_named_dissent_n value = 0 }
			set_variable = { name = zg361_b1_consensus_manager_count value = scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_attendee_n }
			if = { limit = { scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_attendee_n >= 1 } set_variable = { name = zg361_b1_consensus_manager_1 value = scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_manager_1 } }
			if = { limit = { scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_attendee_n >= 2 } set_variable = { name = zg361_b1_consensus_manager_2 value = scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_manager_2 } }
			if = { limit = { scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_attendee_n >= 3 } set_variable = { name = zg361_b1_consensus_manager_3 value = scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_manager_3 } }
			if = { limit = { scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_attendee_n >= 4 } set_variable = { name = zg361_b1_consensus_manager_4 value = scope:zg361_b1_consensus_bank.var:zg361_b1_huddle_host_manager_4 } }
			set_variable = { name = zg361_b1_m144_receipt_serial value = var:zg361_b1_case_serial }
			root = {
				set_variable = { name = zg361_b1_consensus_link_subject value = scope:zg361_b1_consensus_subject_scope }
				change_variable = { name = zg361_b1_consensus_candidate_n add = 1 }
			}
		}
	}
}

zg361_b1_finalize_named_dissent_effect = {
	if = {
		limit = { var:zg361_b1_m144_mode = 1 var:zg361_b1_dissent_used = 1 }
		set_variable = { name = zg361_b1_dissent_finalized_n value = 0 }
		save_temporary_scope_as = zg361_b1_dissent_finalize_manager
		every_in_list = {
			variable = zg361_b1_processing_subjects
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_dissent_finalize_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_dissent_finalize_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_dissent_finalize_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_dissent_object_available = 1
				var:zg361_b1_dissent_object_owner = scope:zg361_b1_dissent_finalize_manager
				var:zg361_b1_dissent_object_subject = this
				var:zg361_b1_dissent_object_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_dissent_object_case = var:zg361_b1_case_serial
				var:zg361_b1_dissent_object_state = 1
				var:zg361_b1_dissent_state = 1
				var:zg361_b1_dissent_manager = scope:zg361_b1_dissent_finalize_manager
				var:zg361_b1_dissent_subject = this
				var:zg361_b1_dissent_reason_fact >= 1
				var:zg361_b1_dissent_attention_debit = 1
				has_variable = zg361_b1_dissent_reviewer
				NOT = { var:zg361_b1_dissent_reviewer = scope:zg361_b1_dissent_finalize_manager }
				NOT = { var:zg361_b1_dissent_reviewer = this }
				var:zg361_b1_dissent_reviewer = { is_alive = yes }
			}
			set_variable = { name = zg361_b1_dissent_reviewed_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_dissent_state value = 2 }
			set_variable = { name = zg361_b1_dissent_object_state value = 2 }
			set_variable = { name = zg361_b1_dissent_final_result value = 2 }
			set_variable = { name = zg361_b1_dissent_credit_delta value = -1 }
			set_variable = { name = zg361_b1_dissent_procedural_risk value = 1 }
			if = {
				limit = {
					var:zg361_b1_dissent_reviewed_grade = var:zg361_b1_dissent_recommendation
					NOT = { var:zg361_b1_dissent_reviewed_grade = var:zg361_b1_dissent_original_grade }
				}
				set_variable = { name = zg361_b1_dissent_final_result value = 1 }
				set_variable = { name = zg361_b1_dissent_credit_delta value = 1 }
				set_variable = { name = zg361_b1_dissent_procedural_risk value = 0 }
			}
			set_variable = { name = zg361_b1_dissent_self_safe_evidence value = 1 }
			set_variable = { name = zg361_b1_dissent_review_attention_consumed value = 1 }
			set_variable = { name = zg361_b1_dissent_review_attention_receipt_reviewer value = var:zg361_b1_dissent_reviewer }
			var:zg361_b1_dissent_reviewer = {
				if = { limit = { NOT = { has_variable = zg361_b1_dissent_review_attention_used } } set_variable = { name = zg361_b1_dissent_review_attention_used value = 0 } }
				if = { limit = { NOT = { has_variable = zg361_b1_dissent_review_receipt_n } } set_variable = { name = zg361_b1_dissent_review_receipt_n value = 0 } }
				change_variable = { name = zg361_b1_dissent_review_attention_used add = 1 }
				change_variable = { name = zg361_b1_dissent_review_receipt_n add = 1 }
			}
			scope:zg361_b1_dissent_finalize_manager = {
				change_variable = { name = zg361_b1_dissent_finalized_n add = 1 }
				if = { limit = { NOT = { has_variable = zg361_b1_dissent_judgment_credit } } set_variable = { name = zg361_b1_dissent_judgment_credit value = 0 } }
				if = { limit = { NOT = { has_variable = zg361_b1_dissent_judgment_balance } } set_variable = { name = zg361_b1_dissent_judgment_balance value = 0 } }
				if = { limit = { NOT = { has_variable = zg361_b1_evaluator_credit } } set_variable = { name = zg361_b1_evaluator_credit value = 100 } }
				set_variable = { name = zg361_b1_dissent_evaluator_credit_before value = var:zg361_b1_evaluator_credit }
				change_variable = { name = zg361_b1_dissent_judgment_credit add = prev.var:zg361_b1_dissent_credit_delta }
				change_variable = { name = zg361_b1_dissent_judgment_balance add = prev.var:zg361_b1_dissent_credit_delta }
				change_variable = { name = zg361_b1_evaluator_credit add = prev.var:zg361_b1_dissent_credit_delta }
				set_variable = { name = zg361_b1_evaluator_credit value = { value = var:zg361_b1_evaluator_credit max = 125 min = 25 } }
				set_variable = { name = zg361_b1_dissent_evaluator_credit_after value = var:zg361_b1_evaluator_credit }
				set_variable = { name = zg361_b1_dissent_judgment_due_year value = { value = current_year add = 1 } }
			}
		}
		if = {
			limit = { var:zg361_b1_dissent_finalized_n = 0 has_variable = zg361_b1_dissent_subject }
			var:zg361_b1_dissent_subject = {
				if = {
					limit = {
						var:zg361_b1_dissent_object_available = 1
						var:zg361_b1_dissent_object_owner = root
						var:zg361_b1_dissent_object_subject = this
						var:zg361_b1_dissent_object_cycle = root.var:zg361_b1_cycle_serial
						var:zg361_b1_dissent_object_case = root.var:zg361_b1_case_serial
						var:zg361_b1_dissent_object_state = 1
					}
					set_variable = { name = zg361_b1_dissent_object_state value = 3 }
					set_variable = { name = zg361_b1_dissent_state value = 3 }
					set_variable = { name = zg361_b1_dissent_cancel_reason value = 1 }
					set_variable = { name = zg361_b1_dissent_review_attention_consumed value = 0 }
				}
			}
		}
	}
	else_if = {
		limit = { var:zg361_b1_m144_mode = 2 var:zg361_b1_consensus_candidate_n = 1 has_variable = zg361_b1_consensus_link_subject }
		var:zg361_b1_consensus_link_subject = {
			if = {
				limit = {
					var:zg361_b1_consensus_object_available = 1
					var:zg361_b1_consensus_owner = root
					var:zg361_b1_consensus_subject = this
					var:zg361_b1_consensus_cycle = root.var:zg361_b1_cycle_serial
					var:zg361_b1_consensus_case = root.var:zg361_b1_case_serial
					var:zg361_b1_consensus_state = 1
				}
				set_variable = { name = zg361_b1_consensus_final_band value = var:zg361_pending_grade }
				set_variable = { name = zg361_b1_consensus_state value = 2 }
				set_variable = { name = zg361_b1_consensus_sealed value = 1 }
				set_variable = { name = zg361_b1_consensus_sealed_case value = var:zg361_b1_case_serial }
			}
		}
	}
}

zg361_b1_open_pending_slots_effect = {
	set_variable = { name = zg361_b1_pending_open_n value = 0 }
	if = { limit = { has_variable_list = zg361_b1_pending_watch_subjects } clear_variable_list = zg361_b1_pending_watch_subjects }
	set_variable = { name = zg361_b1_pending_hold_cursor value = 0 }
	set_variable = { name = zg361_b1_pending_free_top value = var:zg361_pending_375_n }
	set_variable = { name = zg361_b1_pending_free_middle value = var:zg361_pending_35_n }
	set_variable = { name = zg361_b1_pending_free_bottom value = var:zg361_pending_325_n }
	set_variable = { name = zg361_b1_pending_fallback_middle_available value = var:zg361_pending_35_n }
	set_variable = { name = zg361_b1_pending_committed_top value = 0 }
	set_variable = { name = zg361_b1_pending_committed_middle value = 0 }
	set_variable = { name = zg361_b1_pending_committed_bottom value = 0 }
	set_variable = { name = zg361_b1_pending_partial_publish_available value = 0 }
	if = {
		limit = { var:zg361_b1_m142_mode = 1 }
		save_temporary_scope_as = zg361_b1_pending_manager
		every_in_list = {
			variable = zg361_b1_processing_subjects
			if = {
				limit = {
						has_variable = zg361_b1_case_owner
						has_variable = zg361_b1_case_subject
						has_variable = zg361_b1_cycle_serial
						has_variable = zg361_b1_case_serial
						has_variable = zg361_b1_case_state
						has_variable = zg361_b1_case_active
						var:zg361_b1_case_owner = scope:zg361_b1_pending_manager
						var:zg361_b1_case_subject = this
						var:zg361_b1_cycle_serial = scope:zg361_b1_pending_manager.var:zg361_b1_cycle_serial
						var:zg361_b1_case_serial = scope:zg361_b1_pending_manager.var:zg361_b1_case_serial
						var:zg361_b1_case_state = 7
						var:zg361_b1_case_active = 1
						var:zg361_b1_pending_state = 0
						var:zg361_b1_attention_consumed = 1
						var:zg361_b1_recusal_active = 0
						var:zg361_pending_grade = 3
						scope:zg361_b1_pending_manager.var:zg361_b1_pending_free_top >= 1
						scope:zg361_b1_pending_manager.var:zg361_b1_pending_fallback_middle_available >= 1
						scope:zg361_b1_pending_manager = {
							any_in_list = {
								variable = zg361_b1_processing_subjects
								var:zg361_b1_case_owner = scope:zg361_b1_pending_manager
								var:zg361_b1_case_state = 7
								var:zg361_b1_case_active = 1
								var:zg361_b1_roster_included = 1
								var:zg361_b1_recusal_active = 0
								var:zg361_b1_pending_reservation_state = 0
								var:zg361_pending_grade = 2
							}
						}
				}
				save_temporary_scope_as = zg361_b1_pending_top_subject
				scope:zg361_b1_pending_manager = {
					ordered_in_list = {
						variable = zg361_b1_processing_subjects
						order_by = var:zg361_b1_calibration_score
						max = 1
						limit = {
							var:zg361_b1_case_owner = scope:zg361_b1_pending_manager
							var:zg361_b1_case_state = 7
							var:zg361_b1_case_active = 1
							var:zg361_b1_roster_included = 1
							var:zg361_b1_recusal_active = 0
							var:zg361_b1_pending_reservation_state = 0
							var:zg361_pending_grade = 2
						}
							set_variable = { name = zg361_b1_pending_reservation_state value = 1 }
							set_variable = { name = zg361_b1_pending_reserved_for_subject value = scope:zg361_b1_pending_top_subject }
							save_temporary_scope_as = zg361_b1_pending_fallback_scope
							scope:zg361_b1_pending_top_subject = { set_variable = { name = zg361_b1_pending_fallback_subject value = scope:zg361_b1_pending_fallback_scope } }
					}
				}
				scope:zg361_b1_pending_manager = {
					change_variable = { name = zg361_b1_pending_hold_cursor add = 1 }
					change_variable = { name = zg361_b1_pending_open_n add = 1 }
					add_to_variable_list = { name = zg361_b1_pending_watch_subjects target = scope:zg361_b1_pending_top_subject }
					change_variable = { name = zg361_b1_pending_free_top add = -1 }
					change_variable = { name = zg361_b1_pending_fallback_middle_available add = -1 }
					set_variable = { name = zg361_b1_pending_slot_used value = var:zg361_b1_pending_hold_cursor }
				}
				set_variable = { name = zg361_b1_pending_object_available value = 1 }
				set_variable = { name = zg361_b1_pending_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_processing_order } }
				set_variable = { name = zg361_b1_pending_object_owner value = scope:zg361_b1_pending_manager }
				set_variable = { name = zg361_b1_pending_object_subject value = this }
				set_variable = { name = zg361_b1_pending_object_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_pending_object_case value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_pending_object_state value = 1 }
				set_variable = { name = zg361_b1_pending_state value = 1 }
				set_variable = { name = zg361_b1_pending_hold_serial value = scope:zg361_b1_pending_manager.var:zg361_b1_pending_hold_cursor }
				set_variable = { name = zg361_b1_pending_held_band value = 3 }
				set_variable = { name = zg361_b1_pending_fallback_band value = 2 }
				set_variable = { name = zg361_b1_pending_milestone value = 1 }
				set_variable = { name = zg361_b1_pending_verifier value = scope:zg361_b1_pending_manager }
				# CK3 stores current_date as a typed date variable (vanilla
				# travel_start_events).  Date-plus-days assignment has no frozen
				# exact-build syntax contract yet, so persist the exact open date and
				# the independently scheduled 30-day duration for strict providers.
				set_variable = { name = zg361_b1_pending_open_date value = current_date }
				set_variable = { name = zg361_b1_pending_deadline_days value = 30 }
				set_variable = { name = zg361_b1_pending_deadline_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_pending_deadline_year value = current_year }
				set_variable = { name = zg361_b1_pending_baseline_score value = var:zg361_b1_evidence_late }
				set_variable = { name = zg361_b1_pending_target_score value = { value = var:zg361_b1_evidence_late add = 1 max = 100 } }
				set_variable = { name = zg361_b1_pending_observation_recorded value = 0 }
				set_variable = { name = zg361_b1_pending_observed_score value = 0 }
				set_variable = { name = zg361_b1_pending_frozen_reward value = 25 }
				set_variable = { name = zg361_b1_pending_reward_due value = 0 }
				set_variable = { name = zg361_b1_pending_reward_paid value = 0 }
				set_variable = { name = zg361_b1_pending_deadline_pending value = 0 }
				zg361_case_kernel_schedule_deadline_effect = {
					OWNER_VAR = zg361_b1_case_owner
					SUBJECT_VAR = zg361_b1_case_subject
					CYCLE_VAR = zg361_b1_cycle_serial
					CASE_VAR = zg361_b1_case_serial
					STATE_VAR = zg361_b1_case_state
					ACTIVE_VAR = zg361_b1_case_active
					DEADLINE_OWNER_VAR = zg361_b1_pending_deadline_owner
					DEADLINE_SUBJECT_VAR = zg361_b1_pending_deadline_subject
					DEADLINE_CYCLE_VAR = zg361_b1_pending_deadline_ticket_cycle
					DEADLINE_CASE_VAR = zg361_b1_pending_deadline_ticket_case
					DEADLINE_STATE_VAR = zg361_b1_pending_deadline_ticket_state
					DEADLINE_DAYS_VAR = zg361_b1_pending_deadline_days
					DEADLINE_PENDING_VAR = zg361_b1_pending_deadline_pending
					DEADLINE_EXPIRED_VAR = zg361_b1_pending_deadline_expired
					TICKET_OWNER = scope:zg361_b1_pending_manager
					TICKET_SUBJECT = this
					TICKET_CYCLE = var:zg361_b1_cycle_serial
					TICKET_CASE = var:zg361_b1_case_serial
					TICKET_STATE = 7
					DAYS = 30
					EVENT = zg361b1.121
				}
				set_variable = { name = zg361_b1_m142_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	else_if = {
		limit = { var:zg361_b1_m142_mode = 2 }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_attention_consumed = 1
				var:zg361_b1_pending_state = 0
			}
			# Route B is not a pending slot.  It owns only this independent
			# next-cycle evidence tuple and therefore cannot hold a band or reward.
			set_variable = { name = zg361_b1_pending_deferred_projection_state value = 1 }
			set_variable = { name = zg361_b1_pending_late_to_next_cycle value = 1 }
			set_variable = { name = zg361_b1_pending_current_final_unchanged value = 1 }
			set_variable = { name = zg361_b1_pending_deferred_evidence_id value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_processing_order } }
			set_variable = { name = zg361_b1_pending_next_cycle_object_available value = 1 }
			set_variable = { name = zg361_b1_pending_next_cycle_object_id value = var:zg361_b1_pending_deferred_evidence_id }
			set_variable = { name = zg361_b1_pending_next_cycle_object_owner value = root }
			set_variable = { name = zg361_b1_pending_next_cycle_object_subject value = this }
			set_variable = { name = zg361_b1_pending_next_cycle_object_cycle value = { value = var:zg361_b1_cycle_serial add = 1 } }
			set_variable = { name = zg361_b1_pending_next_cycle_object_case value = var:zg361_b1_pending_deferred_evidence_id }
			set_variable = { name = zg361_b1_pending_next_cycle_object_state value = 1 }
			set_variable = { name = zg361_b1_pending_next_cycle_due value = var:zg361_b1_pending_next_cycle_object_cycle }
			set_variable = { name = zg361_b1_pending_next_cycle_delta value = { value = var:zg361_b1_evidence_late subtract = var:zg361_b1_evidence_mid max = 2 min = -2 } }
			set_variable = { name = zg361_b1_m142_receipt_serial value = var:zg361_b1_pending_next_cycle_object_case }
		}
	}
	if = {
		limit = { var:zg361_b1_m142_mode = 1 var:zg361_b1_pending_open_n >= 1 }
		save_scope_as = zg361_b1_pending_watch_owner
		save_scope_value_as = { name = zg361_b1_pending_watch_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_pending_watch_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_pending_watch_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.125 days = 31 }
	}
	if = {
		limit = { var:zg361_b1_m142_mode != 3 }
		set_variable = { name = zg361_b1_pending_partial_publish_available value = 1 }
		set_variable = { name = zg361_b1_pending_partial_publish_revision value = { value = var:zg361_b1_quota_book_version multiply = 100 add = var:zg361_b1_pending_open_n } }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 var:zg361_b1_case_active = 1 }
			set_variable = { name = zg361_b1_pending_projection_route value = root.var:zg361_b1_m142_mode }
			set_variable = { name = zg361_b1_pending_self_safe_available value = 1 }
			set_variable = { name = zg361_b1_pending_partial_publish_state value = 1 }
			set_variable = { name = zg361_b1_pending_partial_final_unchanged value = 1 }
			set_variable = { name = zg361_b1_pending_provisional_revision value = root.var:zg361_b1_pending_partial_publish_revision }
			set_variable = { name = zg361_b1_pending_provisional_status value = 1 }
			set_variable = { name = zg361_b1_pending_provisional_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_pending_provisional_held_band value = 0 }
			set_variable = { name = zg361_b1_pending_provisional_fallback_band value = 0 }
			if = {
				limit = { var:zg361_b1_pending_state = 1 }
				set_variable = { name = zg361_b1_pending_partial_publish_state value = 2 }
				set_variable = { name = zg361_b1_pending_provisional_status value = 2 }
				set_variable = { name = zg361_b1_pending_provisional_grade value = 0 }
				# Manager/audit projection may read held/fallback; the received/self
				# projection remains restricted to marker/milestone/deadline below.
				set_variable = { name = zg361_b1_pending_provisional_held_band value = var:zg361_b1_pending_held_band }
				set_variable = { name = zg361_b1_pending_provisional_fallback_band value = var:zg361_b1_pending_fallback_band }
				# Self-safe projection allowlist: marker/milestone/deadline only.
				set_variable = { name = zg361_b1_pending_self_safe_marker value = 1 }
				set_variable = { name = zg361_b1_pending_self_safe_milestone value = var:zg361_b1_pending_milestone }
				set_variable = { name = zg361_b1_pending_self_safe_deadline_cycle value = var:zg361_b1_pending_deadline_cycle }
			}
			else_if = {
				limit = {
					var:zg361_b1_pending_deferred_projection_state = 1
					var:zg361_b1_pending_next_cycle_object_available = 1
					var:zg361_b1_pending_next_cycle_object_owner = root
					var:zg361_b1_pending_next_cycle_object_subject = this
					var:zg361_b1_pending_next_cycle_object_state = 1
				}
				# Route B exposes exactly two self-safe facts: this final result was
				# not changed, and one bounded evidence object is queued next cycle.
				set_variable = { name = zg361_b1_pending_self_safe_current_final_unchanged value = 1 }
				set_variable = { name = zg361_b1_pending_self_safe_next_cycle_evidence value = 1 }
			}
		}
		zg361_b1_verify_frozen_quota_conservation_effect = yes
		set_variable = { name = zg361_b1_pending_partial_conservation_valid value = var:zg361_b1_quota_conservation_valid }
	}
	if = {
		limit = { var:zg361_b1_pending_open_n = 0 }
		zg361_b1_prepare_reopen_gate_effect = yes
	}
}

zg361_b1_resolve_pending_subject_effect = {
	save_temporary_scope_as = zg361_b1_pending_subject
	if = {
		limit = {
			var:zg361_b1_pending_state = 1
			has_variable = zg361_b1_pending_verifier
			var:zg361_b1_pending_verifier = var:zg361_b1_case_owner
			var:zg361_b1_case_state = 7
			var:zg361_b1_case_active = 1
			var:zg361_b1_recusal_active = 0
		}
		set_variable = { name = zg361_b1_pending_resolution_applied value = 0 }
		set_variable = { name = zg361_b1_pending_resolution value = 2 }
		if = {
			limit = {
				var:zg361_b1_pending_observation_recorded = 1
				var:zg361_b1_pending_observed_score >= var:zg361_b1_pending_target_score
			}
			set_variable = { name = zg361_b1_pending_resolution value = 1 }
		}
		if = {
			limit = {
				var:zg361_b1_pending_resolution = 1
				has_variable = zg361_b1_pending_fallback_subject
				var:zg361_b1_pending_fallback_subject = {
					var:zg361_b1_pending_reservation_state = 1
					has_variable = zg361_b1_pending_reserved_for_subject
					var:zg361_b1_pending_reserved_for_subject = scope:zg361_b1_pending_subject
					var:zg361_b1_case_owner = scope:zg361_b1_pending_subject.var:zg361_b1_case_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_pending_subject.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_pending_subject.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_pending_grade = 2
				}
			}
			set_variable = { name = zg361_b1_pending_state value = 2 }
			set_variable = { name = zg361_b1_pending_object_state value = 2 }
			set_variable = { name = zg361_b1_pending_final_band value = var:zg361_b1_pending_held_band }
			set_variable = { name = zg361_b1_pending_reward_due value = var:zg361_b1_pending_frozen_reward }
			set_variable = { name = zg361_b1_pending_reward_paid value = 0 }
			set_variable = { name = zg361_b1_pending_resolution_applied value = 1 }
			var:zg361_b1_pending_fallback_subject = {
				set_variable = { name = zg361_b1_pending_reservation_state value = 2 }
				remove_variable = zg361_b1_pending_reserved_for_subject
			}
			var:zg361_b1_case_owner = {
				change_variable = { name = zg361_b1_pending_committed_top add = 1 }
				change_variable = { name = zg361_b1_pending_fallback_middle_available add = 1 }
			}
		}
		else = {
			if = {
				limit = {
					has_variable = zg361_b1_pending_fallback_subject
					var:zg361_b1_pending_fallback_subject = {
						var:zg361_b1_pending_reservation_state = 1
						has_variable = zg361_b1_pending_reserved_for_subject
						var:zg361_b1_pending_reserved_for_subject = scope:zg361_b1_pending_subject
						var:zg361_b1_case_owner = scope:zg361_b1_pending_subject.var:zg361_b1_case_owner
						var:zg361_b1_cycle_serial = scope:zg361_b1_pending_subject.var:zg361_b1_cycle_serial
						var:zg361_b1_case_serial = scope:zg361_b1_pending_subject.var:zg361_b1_case_serial
						var:zg361_b1_case_state = 7
						var:zg361_pending_grade = 2
					}
				}
				# Atomic quota-neutral fallback: failed held TOP becomes MIDDLE and
				# its uniquely reserved MIDDLE peer becomes TOP in the same effect.
				var:zg361_b1_pending_fallback_subject = {
					set_variable = { name = zg361_pending_grade value = 3 }
					set_variable = { name = zg361_b1_quota_snapshot value = 3 }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 3 subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_pending_reservation_state value = 3 }
					set_variable = { name = zg361_b1_pending_fallback_promoted value = 1 }
					remove_variable = zg361_b1_pending_reserved_for_subject
				}
				set_variable = { name = zg361_b1_pending_state value = 3 }
				set_variable = { name = zg361_b1_pending_object_state value = 3 }
				set_variable = { name = zg361_b1_pending_final_band value = var:zg361_b1_pending_fallback_band }
				set_variable = { name = zg361_b1_pending_reward_due value = 0 }
				set_variable = { name = zg361_b1_pending_reward_paid value = 0 }
				set_variable = { name = zg361_pending_grade value = 2 }
				set_variable = { name = zg361_b1_quota_snapshot value = 2 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_absolute_grade > 2 }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
				set_variable = { name = zg361_b1_pending_resolution_applied value = 1 }
				var:zg361_b1_case_owner = {
					change_variable = { name = zg361_b1_pending_committed_middle add = 1 }
					change_variable = { name = zg361_b1_pending_committed_top add = 1 }
				}
			}
			else = { debug_log = "ZG361B1: pending fallback reservation invariant failed; no ledger write" }
		}
		if = {
			limit = { var:zg361_b1_pending_resolution_applied = 1 }
			set_variable = { name = zg361_b1_pending_resolved_cycle value = var:zg361_b1_cycle_serial }
			var:zg361_b1_case_owner = {
				change_variable = { name = zg361_b1_pending_reward_book_version add = 1 }
				if = {
					limit = { scope:zg361_b1_pending_subject = { NOT = { var:zg361_b1_pending_resolution = 1 } } }
					change_variable = { name = zg361_b1_quota_book_version add = 1 }
				}
				change_variable = { name = zg361_b1_pending_open_n add = -1 }
				if = {
					limit = { var:zg361_b1_pending_open_n = 0 }
					save_scope_as = zg361_b1_pending_continue_owner
					scope:zg361_b1_pending_subject = { save_scope_as = zg361_b1_pending_continue_subject }
					save_scope_value_as = { name = zg361_b1_pending_continue_cycle value = var:zg361_b1_cycle_serial }
					save_scope_value_as = { name = zg361_b1_pending_continue_case value = var:zg361_b1_case_serial }
					save_scope_value_as = { name = zg361_b1_pending_continue_state value = var:zg361_b1_cycle_state }
					trigger_event = { id = zg361b1.123 days = 1 }
				}
			}
		}
	}
}

zg361_b1_verify_frozen_quota_conservation_effect = {
	set_variable = { name = zg361_b1_quota_conservation_valid value = 0 }
	set_variable = { name = zg361_b1_quota_recount_top value = 0 }
	set_variable = { name = zg361_b1_quota_recount_middle value = 0 }
	set_variable = { name = zg361_b1_quota_recount_bottom value = 0 }
	every_in_list = {
		variable = zg361_b1_processing_subjects
		limit = {
			var:zg361_b1_case_owner = root
			var:zg361_b1_case_state = 7
			var:zg361_b1_case_active = 1
			var:zg361_b1_roster_included = 1
		}
		if = { limit = { var:zg361_pending_grade = 3 } root = { change_variable = { name = zg361_b1_quota_recount_top add = 1 } } }
		else_if = { limit = { var:zg361_pending_grade = 1 } root = { change_variable = { name = zg361_b1_quota_recount_bottom add = 1 } } }
		else = { root = { change_variable = { name = zg361_b1_quota_recount_middle add = 1 } } }
	}
	if = {
		limit = {
			var:zg361_b1_quota_recount_top = var:zg361_pending_375_n
			var:zg361_b1_quota_recount_middle = var:zg361_pending_35_n
			var:zg361_b1_quota_recount_bottom = var:zg361_pending_325_n
		}
		set_variable = { name = zg361_b1_quota_conservation_valid value = 1 }
	}
}

zg361_b1_prepare_reopen_gate_effect = {
	zg361_b1_verify_frozen_quota_conservation_effect = yes
	if = {
		limit = {
			var:zg361_b1_closure_state = 0
			var:zg361_b1_pending_open_n = 0
			var:zg361_b1_calibration_finalized = 0
			var:zg361_b1_quota_conservation_valid = 1
		}
		zg361_b1_finalize_agenda_audit_effect = yes
		zg361_b1_finalize_huddle_diff_effect = yes
		zg361_b1_finalize_named_dissent_effect = yes
		set_variable = { name = zg361_b1_closure_state value = 1 }
		set_variable = { name = zg361_b1_reopen_count value = 0 }
		# The authoritative seal is the case-scoped quota-book revision.  The
		# weighted assignment checksum remains an audit/display before-image only;
		# it is deliberately not trusted as an injective identity hash.
		set_variable = {
			name = zg361_b1_sealed_board_hash
			value = { value = var:zg361_b1_case_serial multiply = 100000 add = var:zg361_b1_quota_book_version }
		}
		set_variable = { name = zg361_b1_sealed_board_checksum value = { value = var:zg361_b1_case_serial multiply = 10000 } }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
				}
				set_variable = { name = zg361_b1_reopen_sealed_grade value = var:zg361_pending_grade }
				save_temporary_scope_as = zg361_b1_hash_subject
				root = {
					change_variable = {
						name = zg361_b1_sealed_board_checksum
						add = { value = scope:zg361_b1_hash_subject.var:zg361_b1_agenda_order multiply = scope:zg361_b1_hash_subject.var:zg361_pending_grade }
					}
				}
			}
		}
		set_variable = {
			name = zg361_b1_reward_snapshot_hash
			value = { value = var:zg361_b1_sealed_board_hash multiply = 1000 add = var:zg361_b1_pending_reward_book_version }
		}
		set_variable = { name = zg361_b1_reward_snapshot_checksum value = 0 }
		set_variable = { name = zg361_b1_pending_reward_expected_n value = 0 }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
				}
				save_temporary_scope_as = zg361_b1_reward_hash_subject
				root = { change_variable = { name = zg361_b1_reward_snapshot_checksum add = scope:zg361_b1_reward_hash_subject.var:zg361_b1_pending_reward_due } }
				if = {
					limit = {
						var:zg361_b1_pending_state = 2
						var:zg361_b1_pending_reward_due = 25
						var:zg361_b1_pending_reward_paid = 0
					}
					root = { change_variable = { name = zg361_b1_pending_reward_expected_n add = 1 } }
				}
			}
		}
		set_variable = { name = zg361_b1_reopen_candidate_n value = 0 }
		set_variable = { name = zg361_b1_reopen_pending_n value = 0 }
		set_variable = { name = zg361_b1_reopen_processed_n value = 0 }
		set_variable = { name = zg361_b1_reopen_cancelled_n value = 0 }
		set_variable = { name = zg361_b1_reopen_batch_object_available value = 0 }
		set_variable = { name = zg361_b1_reopen_batch_state value = 0 }
		if = {
			limit = { var:zg361_b1_m143_mode != 3 }
			set_variable = { name = zg361_b1_reopen_batch_object_available value = 1 }
			set_variable = { name = zg361_b1_reopen_batch_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 43 } }
			set_variable = { name = zg361_b1_reopen_batch_owner value = this }
			set_variable = { name = zg361_b1_reopen_batch_subject value = this }
			set_variable = { name = zg361_b1_reopen_batch_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_reopen_batch_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_reopen_batch_state value = 1 }
			set_variable = { name = zg361_b1_reopen_batch_route value = var:zg361_b1_m143_mode }
			set_variable = { name = zg361_b1_reopen_batch_result value = 0 }
			every_in_list = {
				variable = zg361_b1_processing_subjects
				if = {
					limit = {
						var:zg361_b1_case_owner = root
						var:zg361_b1_case_subject = this
						var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
						var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
						var:zg361_b1_case_state = 7
						var:zg361_b1_case_active = 1
						var:zg361_b1_roster_included = 1
						var:zg361_b1_recusal_active = 0
					}
					set_variable = { name = zg361_b1_reopen_object_available value = 1 }
					set_variable = { name = zg361_b1_reopen_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_processing_order } }
					set_variable = { name = zg361_b1_reopen_object_owner value = root }
					set_variable = { name = zg361_b1_reopen_object_subject value = this }
					set_variable = { name = zg361_b1_reopen_object_cycle value = var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_reopen_object_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_reopen_object_state value = 1 }
					set_variable = { name = zg361_b1_reopen_route value = root.var:zg361_b1_m143_mode }
					set_variable = { name = zg361_b1_reopen_observation_recorded value = 0 }
					set_variable = { name = zg361_b1_reopen_baseline_score value = zg361_kpi_value }
					save_scope_as = zg361_b1_reopen_ticket_subject
					root = {
						change_variable = { name = zg361_b1_reopen_candidate_n add = 1 }
						change_variable = { name = zg361_b1_reopen_pending_n add = 1 }
						save_scope_as = zg361_b1_reopen_ticket_owner
						save_scope_value_as = { name = zg361_b1_reopen_ticket_cycle value = var:zg361_b1_cycle_serial }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_case value = var:zg361_b1_case_serial }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_state value = var:zg361_b1_cycle_state }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_object value = scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_object_id }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_route value = scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_route }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_hash value = var:zg361_b1_sealed_board_hash }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_reward_hash value = var:zg361_b1_reward_snapshot_hash }
						save_scope_value_as = { name = zg361_b1_reopen_ticket_book_version value = var:zg361_b1_quota_book_version }
						trigger_event = { id = zg361b1.122 days = 30 }
					}
				}
			}
			set_variable = { name = zg361_b1_reopen_batch_expected_n value = var:zg361_b1_reopen_candidate_n }
			if = { limit = { var:zg361_b1_reopen_pending_n = 0 } zg361_b1_resolve_reopen_batch_effect = yes }
		}
		else = { zg361_b1_finish_calibration_effect = yes }
	}
}

zg361_b1_materialize_reopen_a_self_safe_effect = {
	if = {
		limit = {
			var:zg361_b1_m143_mode = 1
			var:zg361_b1_reopen_batch_object_available = 1
			var:zg361_b1_reopen_batch_owner = this
			var:zg361_b1_reopen_batch_subject = this
			var:zg361_b1_reopen_batch_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_reopen_batch_case = var:zg361_b1_case_serial
			var:zg361_b1_reopen_batch_state = 2
			OR = {
				var:zg361_b1_reopen_batch_result = 1
				var:zg361_b1_reopen_batch_result = 2
			}
		}
		save_temporary_scope_as = zg361_b1_reopen_projection_manager
		every_in_list = {
			variable = zg361_b1_processing_subjects
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_reopen_projection_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_reopen_projection_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_reopen_projection_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_reopen_object_available = 1
				has_variable = zg361_b1_reopen_object_id
				var:zg361_b1_reopen_object_owner = scope:zg361_b1_reopen_projection_manager
				var:zg361_b1_reopen_object_subject = this
				var:zg361_b1_reopen_object_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_reopen_object_case = var:zg361_b1_case_serial
				OR = {
					var:zg361_b1_reopen_object_state = 2
					var:zg361_b1_reopen_object_state = 3
				}
			}
			set_variable = { name = zg361_b1_reopen_self_a_available value = 1 }
			set_variable = { name = zg361_b1_reopen_self_a_owner value = scope:zg361_b1_reopen_projection_manager }
			set_variable = { name = zg361_b1_reopen_self_a_subject value = this }
			set_variable = { name = zg361_b1_reopen_self_a_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_reopen_self_a_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_reopen_self_a_state value = 2 }
			# 1=reopened self; 2=no qualifying observation anywhere; 3=another
			# cohort member won the unique reopen.  Reason 1/2 preserves the
			# selected observation's sign; 3/4 are bounded non-identity reasons.
			set_variable = { name = zg361_b1_reopen_self_a_result value = 2 }
			set_variable = { name = zg361_b1_reopen_self_a_reason value = 3 }
			if = {
				limit = {
					scope:zg361_b1_reopen_projection_manager.var:zg361_b1_reopen_batch_result = 1
					scope:zg361_b1_reopen_projection_manager = { has_variable = zg361_b1_reopen_receipt_subject }
					this = scope:zg361_b1_reopen_projection_manager.var:zg361_b1_reopen_receipt_subject
				}
				set_variable = { name = zg361_b1_reopen_self_a_result value = 1 }
				set_variable = { name = zg361_b1_reopen_self_a_reason value = 1 }
				if = {
					limit = { scope:zg361_b1_reopen_projection_manager.var:zg361_b1_reopen_polarity < 0 }
					set_variable = { name = zg361_b1_reopen_self_a_reason value = 2 }
				}
			}
			else_if = {
				limit = { scope:zg361_b1_reopen_projection_manager.var:zg361_b1_reopen_batch_result = 1 }
				set_variable = { name = zg361_b1_reopen_self_a_result value = 3 }
				set_variable = { name = zg361_b1_reopen_self_a_reason value = 4 }
			}
		}
	}
}

zg361_b1_resolve_reopen_batch_effect = {
	if = {
		limit = {
			var:zg361_b1_closure_state = 1
			var:zg361_b1_reopen_pending_n = 0
			var:zg361_b1_reopen_processed_n = var:zg361_b1_reopen_batch_expected_n
			var:zg361_b1_reopen_batch_object_available = 1
			var:zg361_b1_reopen_batch_owner = this
			var:zg361_b1_reopen_batch_subject = this
			var:zg361_b1_reopen_batch_cycle = var:zg361_b1_cycle_serial
			var:zg361_b1_reopen_batch_case = var:zg361_b1_case_serial
			var:zg361_b1_reopen_batch_state = 1
		}
		set_variable = { name = zg361_b1_reopen_batch_candidate_n value = 0 }
		if = {
			limit = { var:zg361_b1_m143_mode = 1 }
			ordered_in_list = {
				variable = zg361_b1_processing_subjects
				order_by = var:zg361_b1_reopen_stable_order_key
				max = 1
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_reopen_object_state = 2
					var:zg361_b1_reopen_observation_recorded = 1
					var:zg361_b1_reopen_late_evidence_magnitude >= 10
				}
				save_temporary_scope_as = zg361_b1_reopen_ticket_subject
				root = { change_variable = { name = zg361_b1_reopen_batch_candidate_n add = 1 } }
			}
		}
		if = { limit = { var:zg361_b1_reopen_batch_candidate_n = 1 } zg361_b1_apply_symmetric_reopen_effect = yes }
		else = {
			set_variable = { name = zg361_b1_reopen_batch_state value = 2 }
			set_variable = { name = zg361_b1_reopen_batch_no_qualifying value = 0 }
			if = {
				limit = { var:zg361_b1_m143_mode = 1 }
				set_variable = { name = zg361_b1_reopen_batch_result value = 2 }
				set_variable = { name = zg361_b1_reopen_batch_no_qualifying value = 1 }
			}
			else_if = {
				limit = { var:zg361_b1_m143_mode = 2 }
				set_variable = { name = zg361_b1_reopen_batch_result value = 3 }
			}
			set_variable = { name = zg361_b1_reopen_batch_result_expected_n value = var:zg361_b1_reopen_batch_expected_n }
			set_variable = { name = zg361_b1_reopen_batch_result_processed_n value = var:zg361_b1_reopen_processed_n }
			set_variable = { name = zg361_b1_reopen_batch_result_cancelled_n value = var:zg361_b1_reopen_cancelled_n }
			set_variable = { name = zg361_b1_m143_receipt_serial value = var:zg361_b1_reopen_batch_case }
			zg361_b1_materialize_reopen_a_self_safe_effect = yes
			zg361_b1_finish_calibration_effect = yes
		}
	}
}

zg361_b1_apply_symmetric_reopen_effect = {
	if = {
		limit = {
			var:zg361_b1_closure_state = 1
			var:zg361_b1_reopen_count = 0
			var:zg361_b1_rewards_issued = 0
			var:zg361_b1_pending_rewards_committed = 0
			scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_observation_recorded = 1
			scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_late_evidence_magnitude >= 10
		}
		set_variable = { name = zg361_b1_reopen_source_board_hash value = var:zg361_b1_sealed_board_hash }
		set_variable = { name = zg361_b1_reopen_source_board_checksum value = var:zg361_b1_sealed_board_checksum }
		set_variable = { name = zg361_b1_reopen_source_book_version value = var:zg361_b1_quota_book_version }
		set_variable = { name = zg361_b1_reopen_source_reward_hash value = var:zg361_b1_reward_snapshot_hash }
		set_variable = { name = zg361_b1_reopen_magnitude value = scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_late_evidence_magnitude }
		set_variable = { name = zg361_b1_reopen_receipt_subject value = scope:zg361_b1_reopen_ticket_subject }
		set_variable = { name = zg361_b1_reopen_subject_old_grade value = scope:zg361_b1_reopen_ticket_subject.var:zg361_pending_grade }
		set_variable = { name = zg361_b1_reopen_subject_calibration_before value = scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_calibration_score }
		set_variable = { name = zg361_b1_reopen_polarity value = 1 }
		set_variable = { name = zg361_b1_closure_state value = 2 }
		set_variable = { name = zg361_b1_reopen_count value = 1 }
		set_variable = { name = zg361_b1_reopen_used value = 1 }
		set_variable = { name = zg361_b1_reopen_batch_state value = 2 }
		set_variable = { name = zg361_b1_reopen_batch_result value = 1 }
		set_variable = { name = zg361_b1_m143_receipt_serial value = var:zg361_b1_reopen_batch_case }
		if = {
			limit = { scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_reopen_late_evidence_delta < 0 }
			set_variable = { name = zg361_b1_reopen_polarity value = -1 }
			scope:zg361_b1_reopen_ticket_subject = { change_variable = { name = zg361_b1_calibration_score add = -2 } }
		}
		else = { scope:zg361_b1_reopen_ticket_subject = { change_variable = { name = zg361_b1_calibration_score add = 2 } } }
		zg361_b1_rerank_frozen_quota_book_effect = yes
		set_variable = { name = zg361_b1_reopen_subject_new_grade value = scope:zg361_b1_reopen_ticket_subject.var:zg361_pending_grade }
		set_variable = { name = zg361_b1_reopen_subject_calibration_after value = scope:zg361_b1_reopen_ticket_subject.var:zg361_b1_calibration_score }
		set_variable = { name = zg361_b1_reopen_recomputed_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_reopen_recomputed_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_reopen_recomputed_bottom value = var:zg361_pending_325_n }
		set_variable = {
			name = zg361_b1_reopen_new_board_hash
			value = { value = var:zg361_b1_case_serial multiply = 100000 add = var:zg361_b1_quota_book_version }
		}
		set_variable = { name = zg361_b1_reopen_new_board_checksum value = { value = var:zg361_b1_case_serial multiply = 10000 } }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
				}
				save_temporary_scope_as = zg361_b1_reopen_hash_subject
				root = {
					change_variable = {
						name = zg361_b1_reopen_new_board_checksum
						add = { value = scope:zg361_b1_reopen_hash_subject.var:zg361_b1_agenda_order multiply = scope:zg361_b1_reopen_hash_subject.var:zg361_pending_grade }
					}
				}
			}
		}
		set_variable = { name = zg361_b1_sealed_board_hash value = var:zg361_b1_reopen_new_board_hash }
		set_variable = { name = zg361_b1_sealed_board_checksum value = var:zg361_b1_reopen_new_board_checksum }
		set_variable = { name = zg361_b1_reopen_new_book_version value = var:zg361_b1_quota_book_version }
		set_variable = {
			name = zg361_b1_reward_snapshot_hash
			value = { value = var:zg361_b1_reopen_new_board_hash multiply = 1000 add = var:zg361_b1_pending_reward_book_version }
		}
		set_variable = { name = zg361_b1_reward_snapshot_checksum value = 0 }
		every_in_list = {
			variable = zg361_b1_processing_subjects
			if = {
				limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 }
				save_temporary_scope_as = zg361_b1_reopen_reward_subject
				root = { change_variable = { name = zg361_b1_reward_snapshot_checksum add = scope:zg361_b1_reopen_reward_subject.var:zg361_b1_pending_reward_due } }
			}
		}
		set_variable = { name = zg361_b1_reopen_new_reward_hash value = var:zg361_b1_reward_snapshot_hash }
		set_variable = { name = zg361_b1_reopen_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_closure_state value = 3 }
		set_variable = { name = zg361_b1_m143_receipt_serial value = var:zg361_b1_reopen_batch_case }
		zg361_b1_materialize_reopen_a_self_safe_effect = yes
		debug_log = "ZG361B1: symmetric positive/negative late evidence reopened and resealed once"
	}
	zg361_b1_finish_calibration_effect = yes
}

zg361_b1_pay_frozen_pending_rewards_effect = {
	if = {
		limit = {
			var:zg361_b1_pending_rewards_committed = 1
			var:zg361_b1_finalization_board_hash = var:zg361_b1_sealed_board_hash
			var:zg361_b1_finalization_reward_hash = var:zg361_b1_reward_snapshot_hash
		}
		save_temporary_scope_as = zg361_b1_pending_reward_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					var:zg361_b1_case_owner = scope:zg361_b1_pending_reward_manager
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_pending_reward_manager.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:zg361_b1_pending_reward_manager.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_pending_state = 2
					var:zg361_b1_pending_reward_due = 25
					var:zg361_b1_pending_reward_paid = 0
				}
				add_prestige = 25
				set_variable = { name = zg361_b1_pending_reward_paid value = var:zg361_b1_pending_reward_due }
				set_variable = { name = zg361_b1_pending_reward_due value = 0 }
				set_variable = { name = zg361_b1_pending_reward_board_hash value = scope:zg361_b1_pending_reward_manager.var:zg361_b1_finalization_board_hash }
				set_variable = { name = zg361_b1_pending_reward_snapshot_hash value = scope:zg361_b1_pending_reward_manager.var:zg361_b1_finalization_reward_hash }
				set_variable = { name = zg361_b1_pending_reward_receipt_serial value = var:zg361_b1_case_serial }
				scope:zg361_b1_pending_reward_manager = { change_variable = { name = zg361_b1_pending_rewards_paid_n add = 1 } }
			}
		}
	}
}

zg361_b1_finish_calibration_effect = {
	if = {
		limit = {
			OR = { var:zg361_b1_closure_state = 1 var:zg361_b1_closure_state = 3 }
			var:zg361_b1_pending_open_n = 0
			var:zg361_b1_rewards_issued = 0
			var:zg361_b1_calibration_finalized = 0
		}
		zg361_b1_freeze_band_order_effect = yes
		set_variable = { name = zg361_b1_finalization_board_hash value = var:zg361_b1_sealed_board_hash }
		set_variable = { name = zg361_b1_finalization_reward_hash value = var:zg361_b1_reward_snapshot_hash }
		set_variable = { name = zg361_b1_pending_rewards_committed value = 1 }
		zg361_b1_pay_frozen_pending_rewards_effect = yes
		if = {
			limit = { var:zg361_b1_pending_rewards_paid_n = var:zg361_b1_pending_reward_expected_n }
			set_variable = { name = zg361_b1_calibration_finalized value = 1 }
			# Settlement is the only post-recusal commit path.  The legacy player
			# calibration event exposes independent promote/demote writers that do
			# not understand the frozen conflict ACL, so B1 closes directly through
			# the same deterministic settlement effect for AI and players.
			zg361_apply_pending_grades_effect = yes
		}
		else = { debug_log = "ZG361B1: frozen pending reward ledger incomplete; publication withheld" }
	}
}

zg361_b1_freeze_conflict_recusals_effect = {
	set_variable = { name = zg361_b1_conflict_case_n value = 0 }
	set_variable = { name = zg361_b1_recusal_n value = 0 }
	save_temporary_scope_as = zg361_b1_conflict_manager
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_conflict_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
			}
			set_variable = { name = zg361_b1_grade_write_acl_frozen value = 1 }
			set_variable = { name = zg361_b1_grade_write_authority value = 1 }
			set_variable = { name = zg361_b1_grade_write_reviewer value = scope:zg361_b1_conflict_manager }
		}
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
				has_variable = zg361_b1_case_active
				var:zg361_b1_case_owner = scope:zg361_b1_conflict_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_conflict_case_state = 0
				root.var:zg361_b1_m012_mode != 3
				OR = {
					is_close_family_of = root
					has_relation_friend = root
					has_relation_lover = root
					has_relation_rival = root
					has_relation_nemesis = root
				}
			}
			set_variable = { name = zg361_b1_conflict_case_state value = 1 }
			set_variable = { name = zg361_b1_conflict_case_id value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_roster_frozen_order } }
			set_variable = { name = zg361_b1_recusal_relation value = 1 }
			if = { limit = { has_relation_friend = root } set_variable = { name = zg361_b1_recusal_relation value = 2 } }
			else_if = { limit = { has_relation_lover = root } set_variable = { name = zg361_b1_recusal_relation value = 3 } }
			else_if = { limit = { has_relation_rival = root } set_variable = { name = zg361_b1_recusal_relation value = 4 } }
			else_if = { limit = { has_relation_nemesis = root } set_variable = { name = zg361_b1_recusal_relation value = 5 } }
			set_variable = { name = zg361_b1_recusal_pre_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_recusal_post_recommendation value = 0 }
			set_variable = { name = zg361_b1_recusal_actor value = scope:zg361_b1_conflict_manager }
			if = {
				limit = { root.var:zg361_b1_m012_mode = 1 }
				set_variable = { name = zg361_b1_recusal_active value = 1 }
				set_variable = { name = zg361_b1_recusal_replacement_kind value = 2 }
				set_variable = { name = zg361_b1_grade_write_authority value = 3 }
				remove_variable = zg361_b1_grade_write_reviewer
				if = {
					limit = {
						root = {
							has_variable = zg361_b1_bank_superior
							NOT = { var:zg361_b1_bank_superior = this }
						}
						NOT = { this = root.var:zg361_b1_bank_superior }
					}
					set_variable = { name = zg361_b1_recusal_replacement_kind value = 1 }
					set_variable = { name = zg361_b1_recusal_reviewer value = root.var:zg361_b1_bank_superior }
					set_variable = { name = zg361_b1_grade_write_authority value = 2 }
					set_variable = { name = zg361_b1_grade_write_reviewer value = root.var:zg361_b1_bank_superior }
				}
				root = { change_variable = { name = zg361_b1_recusal_n add = 1 } }
			}
			else_if = {
				limit = { root.var:zg361_b1_m012_mode = 2 }
				set_variable = { name = zg361_b1_recusal_active value = 0 }
				set_variable = { name = zg361_b1_appeal_risk value = 1 }
				if = {
					limit = { root = { NOT = { has_variable = zg361_b1_feedback_debt_open_n } } }
					root = { set_variable = { name = zg361_b1_feedback_debt_open_n value = 0 } }
				}
				root = {
					change_variable = { name = zg361_b1_feedback_debt_open_n add = 1 }
					set_variable = { name = zg361_b1_feedback_debt_due_year value = { value = current_year add = 1 } }
				}
			}
			root = { change_variable = { name = zg361_b1_conflict_case_n add = 1 } }
			set_variable = { name = zg361_b1_m012_receipt_serial value = var:zg361_b1_case_serial }
		}
	}
}

# A recused manager never writes the conflicted subject again.  A named
# superior, when distinct from both manager and subject, or the abstract review
# seat for a small cohort instead recomputes the recommendation from the frozen
# identity-blind score.  A changed recommendation is applied only as a two-sided
# quota-neutral swap with one unrecused case peer; otherwise the independent
# recommendation is frozen with an explicit quota-blocked result.  The five
# receipt fields make replay and stale cases no-ops.
zg361_b1_apply_recusal_replacement_reviews_effect = {
	save_temporary_scope_as = zg361_b1_recusal_review_manager
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				var:zg361_b1_case_owner = scope:zg361_b1_recusal_review_manager
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_conflict_case_state = 1
				var:zg361_b1_recusal_active = 1
				var:zg361_b1_grade_write_acl_frozen = 1
				has_variable = zg361_pending_grade
				has_variable = zg361_b1_blind_score
				scope:zg361_b1_recusal_review_manager.var:zg361_b1_m012_mode = 1
				OR = {
					AND = {
						var:zg361_b1_grade_write_authority = 2
						var:zg361_b1_recusal_replacement_kind = 1
						has_variable = zg361_b1_recusal_reviewer
						has_variable = zg361_b1_grade_write_reviewer
						var:zg361_b1_grade_write_reviewer = var:zg361_b1_recusal_reviewer
						NOT = { var:zg361_b1_grade_write_reviewer = scope:zg361_b1_recusal_review_manager }
						NOT = { var:zg361_b1_grade_write_reviewer = this }
						NOT = { var:zg361_b1_grade_write_reviewer = var:zg361_b1_recusal_actor }
					}
					AND = {
						var:zg361_b1_grade_write_authority = 3
						var:zg361_b1_recusal_replacement_kind = 2
						NOT = { has_variable = zg361_b1_grade_write_reviewer }
						NOT = { has_variable = zg361_b1_recusal_reviewer }
					}
				}
				NOT = {
					AND = {
						has_variable = zg361_b1_recusal_review_receipt_owner
						has_variable = zg361_b1_recusal_review_receipt_subject
						has_variable = zg361_b1_recusal_review_receipt_cycle
						has_variable = zg361_b1_recusal_review_receipt_case
						has_variable = zg361_b1_recusal_review_receipt_state
						var:zg361_b1_recusal_review_receipt_owner = scope:zg361_b1_recusal_review_manager
						var:zg361_b1_recusal_review_receipt_subject = this
						var:zg361_b1_recusal_review_receipt_cycle = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial
						var:zg361_b1_recusal_review_receipt_case = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial
						var:zg361_b1_recusal_review_receipt_state = 2
					}
				}
			}
			set_variable = { name = zg361_b1_recusal_review_state value = 1 }
			set_variable = { name = zg361_b1_recusal_review_base_score value = var:zg361_b1_blind_score }
			set_variable = { name = zg361_b1_recusal_review_score value = var:zg361_b1_recusal_review_base_score }
			set_variable = { name = zg361_b1_recusal_review_pre_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_recusal_review_recommended_grade value = 2 }
			if = {
				limit = { var:zg361_b1_recusal_review_score >= 50 }
				set_variable = { name = zg361_b1_recusal_review_recommended_grade value = 3 }
			}
			else_if = {
				limit = { var:zg361_b1_recusal_review_score < 0 }
				set_variable = { name = zg361_b1_recusal_review_recommended_grade value = 1 }
			}
			set_variable = { name = zg361_b1_recusal_post_recommendation value = var:zg361_b1_recusal_review_recommended_grade }
			set_variable = { name = zg361_b1_recusal_review_applied value = 0 }
			set_variable = { name = zg361_b1_recusal_review_quota_blocked value = 0 }
			set_variable = { name = zg361_b1_recusal_review_actor_kind value = var:zg361_b1_grade_write_authority }
			if = {
				limit = { var:zg361_b1_grade_write_authority = 2 }
				set_variable = { name = zg361_b1_recusal_review_actor value = var:zg361_b1_grade_write_reviewer }
			}
			else = { remove_variable = zg361_b1_recusal_review_actor }
			save_temporary_scope_as = zg361_b1_recusal_review_subject
			scope:zg361_b1_recusal_review_manager = {
				set_variable = { name = zg361_b1_recusal_review_partner_n value = 0 }
			}
			if = {
				limit = { var:zg361_b1_recusal_review_recommended_grade > var:zg361_b1_recusal_review_pre_grade }
				scope:zg361_b1_recusal_review_manager = {
					ordered_in_list = {
						variable = zg361_b1_subjects
						order_by = var:zg361_b1_calibration_score
						max = 1
						limit = {
							var:zg361_b1_case_owner = scope:zg361_b1_recusal_review_manager
							var:zg361_b1_case_subject = this
							var:zg361_b1_cycle_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial
							var:zg361_b1_case_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial
							var:zg361_b1_case_state = 5
							var:zg361_b1_case_active = 1
							var:zg361_b1_roster_included = 1
							var:zg361_b1_grade_write_acl_frozen = 1
							var:zg361_b1_recusal_active = 0
							var:zg361_pending_grade = scope:zg361_b1_recusal_review_subject.var:zg361_b1_recusal_review_recommended_grade
						}
						save_temporary_scope_as = zg361_b1_recusal_review_partner
						root = { change_variable = { name = zg361_b1_recusal_review_partner_n add = 1 } }
					}
				}
			}
			else_if = {
				limit = { var:zg361_b1_recusal_review_recommended_grade < var:zg361_b1_recusal_review_pre_grade }
				scope:zg361_b1_recusal_review_manager = {
					ordered_in_list = {
						variable = zg361_b1_subjects
						order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
						max = 1
						limit = {
							var:zg361_b1_case_owner = scope:zg361_b1_recusal_review_manager
							var:zg361_b1_case_subject = this
							var:zg361_b1_cycle_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial
							var:zg361_b1_case_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial
							var:zg361_b1_case_state = 5
							var:zg361_b1_case_active = 1
							var:zg361_b1_roster_included = 1
							var:zg361_b1_grade_write_acl_frozen = 1
							var:zg361_b1_recusal_active = 0
							var:zg361_pending_grade = scope:zg361_b1_recusal_review_subject.var:zg361_b1_recusal_review_recommended_grade
						}
						save_temporary_scope_as = zg361_b1_recusal_review_partner
						root = { change_variable = { name = zg361_b1_recusal_review_partner_n add = 1 } }
					}
				}
			}
			if = {
				limit = { var:zg361_b1_recusal_review_recommended_grade = var:zg361_b1_recusal_review_pre_grade }
				set_variable = { name = zg361_b1_recusal_review_applied value = 1 }
				set_variable = { name = zg361_b1_recusal_review_state value = 2 }
			}
			else_if = {
				limit = { scope:zg361_b1_recusal_review_manager.var:zg361_b1_recusal_review_partner_n = 1 }
				scope:zg361_b1_recusal_review_partner = {
					set_variable = { name = zg361_b1_recusal_partner_swap_subject value = scope:zg361_b1_recusal_review_subject }
					set_variable = { name = zg361_b1_recusal_partner_swap_case value = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_recusal_partner_swap_pre_grade value = var:zg361_pending_grade }
					set_variable = { name = zg361_pending_grade value = scope:zg361_b1_recusal_review_subject.var:zg361_b1_recusal_review_pre_grade }
					set_variable = { name = zg361_b1_recusal_partner_swap_post_grade value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = {
						limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
						set_variable = { name = zg361_b1_forced_down value = 1 }
					}
				}
				set_variable = { name = zg361_b1_recusal_review_partner value = scope:zg361_b1_recusal_review_partner }
				set_variable = { name = zg361_pending_grade value = var:zg361_b1_recusal_review_recommended_grade }
				set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = var:zg361_pending_grade subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_forced_down value = 0 }
				if = {
					limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
					set_variable = { name = zg361_b1_forced_down value = 1 }
				}
				set_variable = { name = zg361_b1_recusal_review_applied value = 1 }
				set_variable = { name = zg361_b1_recusal_review_state value = 2 }
				scope:zg361_b1_recusal_review_manager = { change_variable = { name = zg361_b1_quota_book_version add = 1 } }
			}
			else = {
				set_variable = { name = zg361_b1_recusal_review_quota_blocked value = 1 }
				set_variable = { name = zg361_b1_recusal_review_state value = 3 }
			}
			set_variable = { name = zg361_b1_recusal_review_post_grade value = var:zg361_pending_grade }
			set_variable = { name = zg361_b1_recusal_review_receipt_owner value = scope:zg361_b1_recusal_review_manager }
			set_variable = { name = zg361_b1_recusal_review_receipt_subject value = this }
			set_variable = { name = zg361_b1_recusal_review_receipt_cycle value = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_recusal_review_receipt_case value = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_recusal_review_receipt_state value = 2 }
		}
	}
}

# A calibration action is a two-sided write or no write.  It is authorized only
# for the current five-field case, consumes one attention seat, excludes every
# recused subject, and advances the quota-book revision once.
zg361_b1_apply_atomic_calibration_swap_effect = {
	if = {
		limit = {
			var:zg361_b1_m009_mode != 3
			var:zg361_b1_cycle_state = 7
			trigger_if = {
				limit = { has_variable = zg361_b1_m009_receipt_serial }
				NOT = { var:zg361_b1_m009_receipt_serial = var:zg361_b1_case_serial }
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = zg361_b1_calibration_id value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_calibration_state value = 1 }
		set_variable = { name = zg361_b1_calibration_route value = var:zg361_b1_m009_mode }
		set_variable = { name = zg361_b1_calibration_quick_close value = 0 }
		set_variable = { name = zg361_b1_calibration_quick_close_blocked value = 0 }
		set_variable = { name = zg361_b1_calibration_assignment_n value = 0 }
		set_variable = { name = zg361_b1_calibration_one_grade_check value = 0 }
		set_variable = { name = zg361_b1_calibration_remaining_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_calibration_remaining_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_calibration_remaining_bottom value = var:zg361_pending_325_n }
		set_variable = { name = zg361_b1_calibration_before_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_calibration_before_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_calibration_before_bottom value = var:zg361_pending_325_n }
		set_variable = { name = zg361_b1_calibration_swap_candidate_n value = 0 }
		if = {
			limit = { var:zg361_b1_m009_mode = 1 var:zg361_b1_calibration_attention >= 1 var:zg361_b1_calibration_swap_used = 0 }
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = var:zg361_b1_calibration_score
				max = 1
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0
					var:zg361_pending_grade = 3
				}
				save_temporary_scope_as = zg361_b1_calibration_demote_subject
				root = { change_variable = { name = zg361_b1_calibration_swap_candidate_n add = 1 } }
			}
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
				max = 1
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0
					var:zg361_pending_grade = 2
				}
				save_temporary_scope_as = zg361_b1_calibration_promote_subject
				root = { change_variable = { name = zg361_b1_calibration_swap_candidate_n add = 1 } }
			}
			if = {
				limit = {
					var:zg361_b1_calibration_swap_candidate_n = 2
					scope:zg361_b1_calibration_promote_subject.var:zg361_b1_calibration_score > scope:zg361_b1_calibration_demote_subject.var:zg361_b1_calibration_score
				}
				scope:zg361_b1_calibration_demote_subject = {
					set_variable = { name = zg361_pending_grade value = 2 }
					set_variable = { name = zg361_b1_quota_snapshot value = 2 }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = { limit = { var:zg361_absolute_grade > 2 } set_variable = { name = zg361_b1_forced_down value = 1 } }
					set_variable = { name = zg361_b1_calibration_swap_before value = 3 }
					set_variable = { name = zg361_b1_calibration_swap_after value = 2 }
				}
				scope:zg361_b1_calibration_promote_subject = {
					set_variable = { name = zg361_pending_grade value = 3 }
					set_variable = { name = zg361_b1_quota_snapshot value = 3 }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 3 subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					set_variable = { name = zg361_b1_calibration_swap_before value = 2 }
					set_variable = { name = zg361_b1_calibration_swap_after value = 3 }
				}
				set_variable = { name = zg361_b1_calibration_swap_subject_a value = scope:zg361_b1_calibration_demote_subject }
				set_variable = { name = zg361_b1_calibration_swap_subject_b value = scope:zg361_b1_calibration_promote_subject }
				set_variable = { name = zg361_b1_calibration_swap_reason value = 1 }
				set_variable = { name = zg361_b1_calibration_swap_attention_before value = var:zg361_b1_calibration_attention }
				change_variable = { name = zg361_b1_calibration_attention add = -1 }
				set_variable = { name = zg361_b1_calibration_swap_attention_after value = var:zg361_b1_calibration_attention }
				set_variable = { name = zg361_b1_calibration_swap_used value = 1 }
				change_variable = { name = zg361_b1_quota_book_version add = 1 }
				set_variable = { name = zg361_b1_calibration_swap_book_version value = var:zg361_b1_quota_book_version }
			}
		}
		else_if = {
			limit = { var:zg361_b1_m009_mode = 2 }
			set_variable = { name = zg361_b1_calibration_quick_close value = 1 }
			every_in_list = {
				variable = zg361_b1_subjects
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_pending_grade
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
				}
				root = { change_variable = { name = zg361_b1_calibration_assignment_n add = 1 } }
			}
			set_variable = {
				name = zg361_b1_calibration_assignment_sum
				value = {
					value = var:zg361_pending_375_n
					add = var:zg361_pending_35_n
					add = var:zg361_pending_325_n
				}
			}
			if = {
				limit = { var:zg361_b1_calibration_assignment_n = var:zg361_b1_calibration_assignment_sum }
				set_variable = { name = zg361_b1_calibration_one_grade_check value = 1 }
				set_variable = { name = zg361_b1_calibration_remaining_top value = 0 }
				set_variable = { name = zg361_b1_calibration_remaining_middle value = 0 }
				set_variable = { name = zg361_b1_calibration_remaining_bottom value = 0 }
			}
			else = {
				set_variable = { name = zg361_b1_calibration_quick_close_blocked value = 1 }
				set_variable = { name = zg361_b1_publication_blocked value = 1 }
			}
		}
		set_variable = { name = zg361_b1_calibration_after_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_calibration_after_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_calibration_after_bottom value = var:zg361_pending_325_n }
		if = {
			limit = { var:zg361_b1_calibration_quick_close_blocked = 0 }
			set_variable = { name = zg361_b1_calibration_state value = 2 }
			set_variable = { name = zg361_b1_m009_receipt_serial value = var:zg361_b1_case_serial }
		}
	}
}

zg361_b1_apply_bottom_protection_effect = {
	if = {
		limit = {
			var:zg361_b1_m010_mode = 1
			var:zg361_b1_bottom_protection_used = 0
			var:zg361_pending_325_n >= 1
			trigger_if = {
				limit = { has_variable = zg361_b1_m010_receipt_serial }
				NOT = { var:zg361_b1_m010_receipt_serial = var:zg361_b1_case_serial }
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = zg361_b1_bottom_fail_n value = 0 }
		every_in_list = {
			variable = zg361_b1_subjects
			limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 5 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1 }
			if = { limit = { var:zg361_b1_evidence_late < 0 } root = { change_variable = { name = zg361_b1_bottom_fail_n add = 1 } } }
		}
		if = {
			limit = { var:zg361_b1_bottom_fail_n = 0 }
			set_variable = { name = zg361_b1_bottom_protection_candidate_n value = 0 }
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = var:zg361_b1_peer_normalized_score
				max = 1
				limit = {
					var:zg361_b1_case_owner = root var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0 var:zg361_pending_grade = 1 var:zg361_b1_peer_normalized_score >= 5
				}
				save_temporary_scope_as = zg361_b1_bottom_protected_subject
				root = { change_variable = { name = zg361_b1_bottom_protection_candidate_n add = 1 } }
			}
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
				max = 1
				limit = {
					var:zg361_b1_case_owner = root var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0 var:zg361_pending_grade = 2
					NOT = { has_character_flag = zg361_newcomer_this_cycle }
				}
				save_temporary_scope_as = zg361_b1_bottom_carrier_subject
				root = { change_variable = { name = zg361_b1_bottom_protection_candidate_n add = 1 } }
			}
			if = {
				limit = { var:zg361_b1_bottom_protection_candidate_n = 2 }
				scope:zg361_b1_bottom_protected_subject = {
					set_variable = { name = zg361_pending_grade value = 2 }
					set_variable = { name = zg361_b1_quota_snapshot value = 2 }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = { limit = { var:zg361_absolute_grade > 2 } set_variable = { name = zg361_b1_forced_down value = 1 } }
					set_variable = { name = zg361_b1_bottom_protected value = 1 }
				}
				scope:zg361_b1_bottom_carrier_subject = {
					set_variable = { name = zg361_pending_grade value = 1 }
					set_variable = { name = zg361_b1_quota_snapshot value = 1 }
					set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 1 subtract = var:zg361_b1_shadow_grade } }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = { limit = { var:zg361_absolute_grade > 1 } set_variable = { name = zg361_b1_forced_down value = 1 } }
					set_variable = { name = zg361_b1_bottom_carrier value = 1 }
					set_variable = { name = zg361_b1_appeal_risk value = 1 }
				}
				set_variable = { name = zg361_b1_forced_bottom_case_id value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_bottom_protected_subject value = scope:zg361_b1_bottom_protected_subject }
				set_variable = { name = zg361_b1_bottom_carrier_subject value = scope:zg361_b1_bottom_carrier_subject }
				set_variable = { name = zg361_b1_bottom_protection_cost value = 25 }
				add_prestige = -25
				set_variable = { name = zg361_b1_protection_debt_state value = 1 }
				set_variable = { name = zg361_b1_protection_debt_created_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_protection_debt_due_year value = { value = current_year add = 1 } }
				set_variable = { name = zg361_b1_bottom_protection_used value = 1 }
				change_variable = { name = zg361_b1_quota_book_version add = 1 }
				set_variable = { name = zg361_b1_m010_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	else_if = {
		limit = {
			var:zg361_b1_m010_mode = 2
			var:zg361_b1_bottom_protection_used = 0
			var:zg361_pending_325_n >= 1
			trigger_if = {
				limit = { has_variable = zg361_b1_m010_receipt_serial }
				NOT = { var:zg361_b1_m010_receipt_serial = var:zg361_b1_case_serial }
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = zg361_b1_bottom_edge_fail_n value = 0 }
		set_variable = { name = zg361_b1_bottom_edge_candidate_n value = 0 }
		set_variable = { name = zg361_b1_bottom_edge_blocked_newcomer_protection value = 0 }
		every_in_list = {
			variable = zg361_b1_subjects
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 5
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
			}
			if = { limit = { var:zg361_b1_evidence_late < 0 } root = { change_variable = { name = zg361_b1_bottom_edge_fail_n add = 1 } } }
		}
		if = {
			limit = { var:zg361_b1_bottom_edge_fail_n = 0 }
			ordered_in_list = {
				variable = zg361_b1_subjects
				order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
				max = 1
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 5
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_b1_recusal_active = 0
					var:zg361_pending_grade = 1
					NOT = { has_character_flag = zg361_newcomer_this_cycle }
				}
				save_temporary_scope_as = zg361_b1_bottom_edge_subject
				root = { change_variable = { name = zg361_b1_bottom_edge_candidate_n add = 1 } }
			}
			if = {
				limit = { var:zg361_b1_bottom_edge_candidate_n = 1 }
				set_variable = { name = zg361_b1_forced_bottom_case_id value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_bottom_carrier_subject value = scope:zg361_b1_bottom_edge_subject }
				set_variable = { name = zg361_b1_bottom_edge_route value = 2 }
				set_variable = { name = zg361_b1_bottom_protection_used value = 1 }
				set_variable = { name = zg361_b1_m010_receipt_serial value = var:zg361_b1_case_serial }
				scope:zg361_b1_bottom_edge_subject = {
					set_variable = { name = zg361_b1_bottom_carrier value = 1 }
					set_variable = { name = zg361_b1_appeal_risk value = 1 }
					set_variable = { name = zg361_b1_resentment_risk value = 1 }
					set_variable = { name = zg361_b1_attrition_risk value = 1 }
					set_variable = { name = zg361_b1_bottom_edge_risk_receipt value = var:zg361_b1_case_serial }
				}
			}
			else = {
				# Never bypass an already-frozen newcomer protection just to create
				# the B-route risk object.  The exact base quota remains untouched.
				set_variable = { name = zg361_b1_bottom_edge_blocked_newcomer_protection value = 1 }
				set_variable = { name = zg361_b1_m010_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
}

zg361_b1_prepare_skip_level_return_effect = {
	set_variable = { name = zg361_b1_oversight_issue_n value = 0 }
	change_variable = { name = zg361_b1_oversight_issue_n add = var:zg361_b1_roster_amendment_n }
	change_variable = { name = zg361_b1_oversight_issue_n add = var:zg361_b1_recusal_n }
	change_variable = { name = zg361_b1_oversight_issue_n add = var:zg361_b1_blind_bias_audit_n }
	every_in_list = {
		variable = zg361_b1_subjects
		limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1 }
		if = {
			limit = { var:zg361_b1_peer_author_count < var:zg361_b1_peer_anonymous_threshold }
			root = { change_variable = { name = zg361_b1_oversight_issue_n add = 1 } }
		}
	}
	if = {
		limit = {
			var:zg361_b1_m011_mode = 1
			var:zg361_b1_skip_level_return_count = 0
			var:zg361_b1_oversight_issue_n >= 1
			has_variable = zg361_b1_bank_superior
		}
		set_variable = { name = zg361_b1_oversight_case_id value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_oversight_owner value = this }
		set_variable = { name = zg361_b1_oversight_reviewer value = var:zg361_b1_bank_superior }
		set_variable = { name = zg361_b1_oversight_cycle value = var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_oversight_return_status value = 1 }
		set_variable = { name = zg361_b1_oversight_return_reason value = 1 }
		set_variable = { name = zg361_b1_skip_level_return_used value = 1 }
		set_variable = { name = zg361_b1_skip_level_return_count value = 1 }
		set_variable = { name = zg361_b1_publication_blocked value = 1 }
		set_variable = { name = zg361_b1_cycle_state value = 6 }
		set_variable = { name = zg361_b1_m011_receipt_serial value = var:zg361_b1_case_serial }
		save_scope_as = zg361_b1_oversight_ticket_owner
		save_scope_value_as = { name = zg361_b1_oversight_ticket_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_oversight_ticket_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_oversight_ticket_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.124 days = 1 }
	}
	else_if = {
		limit = {
			var:zg361_b1_m011_mode = 2
			has_variable = zg361_b1_bank_superior
			trigger_if = {
				limit = { has_variable = zg361_b1_m011_receipt_serial }
				NOT = { var:zg361_b1_m011_receipt_serial = var:zg361_b1_case_serial }
			}
			trigger_else = { always = yes }
		}
		# The skip-level seat requests one visible boundary override, but the
		# manager's single quota book remains the only writer/owner.  This avoids
		# manufacturing a second imperial review serial while still preserving the
		# deliberately improper B-route result and its audit trail.
		set_variable = { name = zg361_b1_oversight_case_id value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_oversight_owner value = this }
		set_variable = { name = zg361_b1_oversight_reviewer value = var:zg361_b1_bank_superior }
		set_variable = { name = zg361_b1_oversight_cycle value = var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_oversight_route value = 2 }
		set_variable = { name = zg361_b1_oversight_improper_route_risk value = 1 }
		set_variable = { name = zg361_b1_oversight_override_executed value = 0 }
		set_variable = { name = zg361_b1_oversight_override_candidate_n value = 0 }
		set_variable = { name = zg361_b1_oversight_before_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_oversight_before_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_oversight_before_bottom value = var:zg361_pending_325_n }
		ordered_in_list = {
			variable = zg361_b1_subjects
			order_by = var:zg361_b1_calibration_score
			max = 1
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_recusal_active = 0
				var:zg361_pending_grade = 3
			}
			save_temporary_scope_as = zg361_b1_oversight_demote_subject
			root = { change_variable = { name = zg361_b1_oversight_override_candidate_n add = 1 } }
		}
		ordered_in_list = {
			variable = zg361_b1_subjects
			order_by = { value = var:zg361_b1_calibration_score multiply = -1 }
			max = 1
			limit = {
				var:zg361_b1_case_owner = root
				var:zg361_b1_case_subject = this
				var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
				var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_recusal_active = 0
				var:zg361_pending_grade = 2
			}
			save_temporary_scope_as = zg361_b1_oversight_promote_subject
			root = { change_variable = { name = zg361_b1_oversight_override_candidate_n add = 1 } }
		}
		if = {
			limit = { var:zg361_b1_oversight_override_candidate_n = 2 }
			scope:zg361_b1_oversight_demote_subject = {
				set_variable = { name = zg361_pending_grade value = 2 }
				set_variable = { name = zg361_b1_quota_snapshot value = 2 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 2 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_skip_level_before_grade value = 3 }
				set_variable = { name = zg361_b1_skip_level_after_grade value = 2 }
				set_variable = { name = zg361_b1_skip_level_reviewer value = root.var:zg361_b1_bank_superior }
				set_variable = { name = zg361_b1_skip_level_book_owner value = root }
				set_variable = { name = zg361_b1_skip_level_procedural_risk value = 1 }
				set_variable = { name = zg361_b1_skip_level_receipt_serial value = var:zg361_b1_case_serial }
			}
			scope:zg361_b1_oversight_promote_subject = {
				set_variable = { name = zg361_pending_grade value = 3 }
				set_variable = { name = zg361_b1_quota_snapshot value = 3 }
				set_variable = { name = zg361_b1_shadow_to_quota_delta value = { value = 3 subtract = var:zg361_b1_shadow_grade } }
				set_variable = { name = zg361_b1_skip_level_before_grade value = 2 }
				set_variable = { name = zg361_b1_skip_level_after_grade value = 3 }
				set_variable = { name = zg361_b1_skip_level_reviewer value = root.var:zg361_b1_bank_superior }
				set_variable = { name = zg361_b1_skip_level_book_owner value = root }
				set_variable = { name = zg361_b1_skip_level_procedural_risk value = 1 }
				set_variable = { name = zg361_b1_skip_level_receipt_serial value = var:zg361_b1_case_serial }
			}
			set_variable = { name = zg361_b1_oversight_changed_subject_a value = scope:zg361_b1_oversight_demote_subject }
			set_variable = { name = zg361_b1_oversight_changed_subject_b value = scope:zg361_b1_oversight_promote_subject }
			set_variable = { name = zg361_b1_oversight_override_executed value = 1 }
			change_variable = { name = zg361_b1_quota_book_version add = 1 }
		}
		set_variable = { name = zg361_b1_oversight_after_top value = var:zg361_pending_375_n }
		set_variable = { name = zg361_b1_oversight_after_middle value = var:zg361_pending_35_n }
		set_variable = { name = zg361_b1_oversight_after_bottom value = var:zg361_pending_325_n }
		set_variable = { name = zg361_b1_m011_receipt_serial value = var:zg361_b1_case_serial }
	}
}

zg361_b1_freeze_band_order_effect = {
	# #145 is frozen with the manager case at D+0.  Never re-read the live card
	# here: changing a policy after case creation must not rewrite this cohort's
	# private/public order route.
	set_variable = { name = zg361_b1_band_order_mode value = var:zg361_b1_m145_mode }
	set_variable = { name = zg361_b1_band_order_batch_available value = 0 }
	set_variable = { name = zg361_b1_band_order_batch_state value = 0 }
	set_variable = { name = zg361_b1_band_order_batch_result value = 0 }
	set_variable = { name = zg361_b1_band_opportunity_capacity value = 0 }
	set_variable = { name = zg361_b1_band_coaching_capacity value = 0 }
	# Clear every current subject first.  A former MIDDLE who moved to TOP or
	# BOTTOM must not retain last cycle's order, appeal, blackbox or opportunity.
	set_variable = { name = zg361_b1_band_middle_n value = 0 }
	every_in_list = {
		variable = zg361_b1_subjects
		limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 var:zg361_b1_case_active = 1 }
		set_variable = { name = zg361_b1_band_order value = 0 }
		set_variable = { name = zg361_b1_band_order_object_available value = 0 }
		set_variable = { name = zg361_b1_band_order_object_state value = 0 }
		remove_variable = zg361_b1_band_order_object_owner
		remove_variable = zg361_b1_band_order_object_subject
		set_variable = { name = zg361_b1_band_order_use_mode value = 0 }
		set_variable = { name = zg361_b1_band_opportunity_weight value = 0 }
		set_variable = { name = zg361_b1_band_public_order_available value = 0 }
		set_variable = { name = zg361_b1_band_private_order_available value = 0 }
		set_variable = { name = zg361_b1_band_self_public_coaching_priority value = 0 }
		set_variable = { name = zg361_b1_band_self_public_opportunity value = 0 }
		set_variable = { name = zg361_b1_band_self_public_within_middle_order value = 0 }
		set_variable = { name = zg361_b1_band_self_public_opportunity_capacity value = 0 }
		set_variable = { name = zg361_b1_band_self_public_opportunity_selected value = 0 }
		set_variable = { name = zg361_b1_band_self_public_coaching_selected value = 0 }
		set_variable = { name = zg361_b1_band_self_private_opportunity_selected value = 0 }
		set_variable = { name = zg361_b1_band_self_appeal_evidence value = 0 }
		set_variable = { name = zg361_b1_band_order_blackbox_risk value = 0 }
		set_variable = { name = zg361_b1_band_formal_band value = 0 }
		if = { limit = { var:zg361_b1_roster_included = 1 var:zg361_pending_grade = 2 } root = { change_variable = { name = zg361_b1_band_middle_n add = 1 } } }
	}
	if = {
		limit = { var:zg361_b1_band_order_mode != 3 }
		set_variable = { name = zg361_b1_band_order_batch_available value = 1 }
		set_variable = { name = zg361_b1_band_order_batch_id value = { value = var:zg361_b1_case_serial multiply = 100 add = 45 } }
		set_variable = { name = zg361_b1_band_order_batch_owner value = this }
		set_variable = { name = zg361_b1_band_order_batch_subject value = this }
		set_variable = { name = zg361_b1_band_order_batch_cycle value = var:zg361_b1_cycle_serial }
		set_variable = { name = zg361_b1_band_order_batch_case value = var:zg361_b1_band_order_batch_id }
		set_variable = { name = zg361_b1_band_order_batch_state value = 1 }
		set_variable = { name = zg361_b1_band_order_batch_result value = 2 }
		set_variable = { name = zg361_b1_band_order_batch_middle_n value = var:zg361_b1_band_middle_n }
		if = {
			limit = { var:zg361_b1_band_middle_n >= 2 }
			set_variable = { name = zg361_b1_band_order_batch_result value = 1 }
			set_variable = { name = zg361_b1_band_opportunity_capacity value = 1 }
			if = { limit = { var:zg361_b1_band_middle_n >= 3 } set_variable = { name = zg361_b1_band_opportunity_capacity value = 2 } }
			if = { limit = { var:zg361_b1_band_order_mode = 1 } set_variable = { name = zg361_b1_band_coaching_capacity value = var:zg361_b1_band_opportunity_capacity } }
		}
		else = {
			set_variable = { name = zg361_b1_band_order_batch_state value = 3 }
			set_variable = { name = zg361_b1_band_order_batch_receipt_case value = var:zg361_b1_band_order_batch_case }
			set_variable = { name = zg361_b1_m145_receipt_serial value = var:zg361_b1_band_order_batch_case }
		}
	}
	if = {
		limit = { var:zg361_b1_band_order_mode != 3 var:zg361_b1_band_middle_n >= 2 }
		every_in_list = {
			variable = zg361_b1_subjects
			limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1 var:zg361_pending_grade = 2 }
			set_variable = {
				name = zg361_b1_band_order_sort_key
				value = {
					value = var:zg361_b1_calibration_score multiply = 1000000
					subtract = { value = var:zg361_b1_roster_frozen_order multiply = 1000 }
					subtract = var:zg361_b1_case_serial
				}
			}
		}
		set_variable = { name = zg361_b1_band_cursor value = 0 }
		ordered_in_list = {
			variable = zg361_b1_subjects
			order_by = var:zg361_b1_band_order_sort_key
			max = { value = list_size:zg361_b1_subjects max = 80 }
			limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 var:zg361_b1_case_active = 1 var:zg361_b1_roster_included = 1 var:zg361_pending_grade = 2 }
			root = { change_variable = { name = zg361_b1_band_cursor add = 1 } }
			set_variable = { name = zg361_b1_band_order_object_available value = 1 }
			set_variable = { name = zg361_b1_band_order_object_id value = { value = var:zg361_b1_case_serial multiply = 100 add = var:zg361_b1_processing_order } }
			set_variable = { name = zg361_b1_band_order_object_owner value = root }
			set_variable = { name = zg361_b1_band_order_object_subject value = this }
			set_variable = { name = zg361_b1_band_order_object_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_band_order_object_case value = var:zg361_b1_band_order_object_id }
			set_variable = { name = zg361_b1_band_order_object_state value = 1 }
			set_variable = { name = zg361_b1_band_formal_band value = 2 }
			set_variable = { name = zg361_b1_band_order value = root.var:zg361_b1_band_cursor }
			set_variable = { name = zg361_b1_band_order_use_mode value = root.var:zg361_b1_band_order_mode }
			set_variable = { name = zg361_b1_band_opportunity_weight value = 0 }
			# Opportunity is finite and strictly smaller than the MIDDLE cohort.
			# With two peers only rank 1 receives it; with three or more ranks 1/2 do.
			if = {
				limit = { var:zg361_b1_band_order = 1 }
				set_variable = { name = zg361_b1_band_opportunity_weight value = 3 }
			}
			else_if = {
				limit = { root.var:zg361_b1_band_middle_n >= 3 var:zg361_b1_band_order = 2 }
				set_variable = { name = zg361_b1_band_opportunity_weight value = 2 }
			}
			if = {
				limit = { root.var:zg361_b1_band_order_mode = 1 }
				set_variable = { name = zg361_b1_band_public_order_available value = 1 }
				set_variable = { name = zg361_b1_band_self_public_coaching_priority value = var:zg361_b1_band_order }
				set_variable = { name = zg361_b1_band_self_public_within_middle_order value = var:zg361_b1_band_order }
				set_variable = { name = zg361_b1_band_self_public_opportunity_capacity value = root.var:zg361_b1_band_opportunity_capacity }
				if = {
					limit = { var:zg361_b1_band_opportunity_weight >= 2 }
					set_variable = { name = zg361_b1_band_self_public_opportunity value = 1 }
					set_variable = { name = zg361_b1_band_self_public_opportunity_selected value = 1 }
					set_variable = { name = zg361_b1_band_self_public_coaching_selected value = 1 }
				}
			}
			else = {
				set_variable = { name = zg361_b1_band_private_order_available value = 1 }
				set_variable = { name = zg361_b1_band_order_blackbox_risk value = 1 }
				if = { limit = { var:zg361_b1_band_opportunity_weight >= 2 } set_variable = { name = zg361_b1_band_self_private_opportunity_selected value = 1 } }
				# Every affected MIDDLE subject receives self-safe appeal evidence,
				# including ranks outside the finite opportunity budget.
				set_variable = { name = zg361_b1_band_self_appeal_evidence value = 1 }
			}
			set_variable = { name = zg361_b1_m145_receipt_serial value = var:zg361_b1_band_order_object_case }
		}
		set_variable = { name = zg361_b1_band_order_batch_state value = 2 }
		set_variable = { name = zg361_b1_band_order_batch_consumed_n value = var:zg361_b1_band_cursor }
		set_variable = { name = zg361_b1_band_order_batch_receipt_case value = var:zg361_b1_band_order_batch_case }
	}
}

zg361_b1_open_calibration_effect = {
	if = {
		limit = { var:zg361_b1_cycle_state = 6 var:zg361_b1_calibration_finalized = 0 }
		set_variable = { name = zg361_b1_cycle_state value = 7 }
		set_variable = { name = zg361_b1_calibration_attention value = 3 }
		set_variable = { name = zg361_b1_agenda_version value = 0 }
		set_variable = { name = zg361_b1_skip_level_return_used value = 0 }
		set_variable = { name = zg361_b1_dissent_used value = 0 }
		set_variable = { name = zg361_b1_pending_slot_used value = 0 }
		set_variable = { name = zg361_b1_reopen_used value = 0 }
		set_variable = { name = zg361_b1_closure_state value = 0 }
		set_variable = { name = zg361_b1_rewards_issued value = 0 }
		set_variable = { name = zg361_b1_pending_rewards_committed value = 0 }
		set_variable = { name = zg361_b1_pending_reward_book_version value = 0 }
		set_variable = { name = zg361_b1_pending_reward_expected_n value = 0 }
		set_variable = { name = zg361_b1_pending_rewards_paid_n value = 0 }
		set_variable = { name = zg361_b1_calibration_swap_used value = 0 }
		set_variable = { name = zg361_b1_bottom_protection_used value = 0 }
		set_variable = { name = zg361_b1_calibration_quick_close_blocked value = 0 }
		zg361_b1_freeze_conflict_recusals_effect = yes
		zg361_b1_apply_recusal_replacement_reviews_effect = yes
		zg361_b1_apply_atomic_calibration_swap_effect = yes
		if = {
			limit = { var:zg361_b1_calibration_quick_close_blocked = 0 }
			zg361_b1_apply_bottom_protection_effect = yes
			every_in_list = {
				variable = zg361_b1_subjects
				if = {
					limit = {
						has_variable = zg361_b1_case_owner
						has_variable = zg361_b1_case_subject
						has_variable = zg361_b1_cycle_serial
						has_variable = zg361_b1_case_serial
						has_variable = zg361_b1_case_state
						has_variable = zg361_b1_case_active
						var:zg361_b1_case_owner = root
						var:zg361_b1_case_subject = this
						var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
						var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
						var:zg361_b1_case_state = 5
						var:zg361_b1_case_active = 1
				}
				set_variable = { name = zg361_b1_case_state value = 7 }
			}
		}
			zg361_b1_prepare_skip_level_return_effect = yes
			if = {
				limit = { var:zg361_b1_oversight_return_status = 0 }
				zg361_b1_build_agenda_and_attention_effect = yes
				zg361_b1_consume_must_review_effect = yes
				zg361_b1_record_named_dissent_effect = yes
				zg361_b1_open_pending_slots_effect = yes
			}
		}
		else = {
			set_variable = { name = zg361_b1_cycle_state value = 6 }
			debug_log = "ZG361B1: B quick-close assignment/quota mismatch; calibration withheld"
		}
	}
}

zg361_b1_mark_published_effect = {
	if = {
		limit = { has_character_flag = zg361_b1_cycle_active }
		set_variable = { name = zg361_b1_cycle_state value = 8 }
		set_variable = { name = zg361_b1_rewards_issued value = 1 }
		set_variable = { name = zg361_b1_closure_state value = 4 }
		if = {
			limit = { var:zg361_b1_m013_mode != 3 }
			set_variable = { name = zg361_b1_m013_receipt_serial value = var:zg361_b1_case_serial }
		}
		set_variable = { name = zg361_b1_m045_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m051_receipt_serial value = var:zg361_b1_case_serial }
			every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
				}
					set_variable = { name = zg361_b1_case_state value = 8 }
					set_variable = { name = zg361_b1_case_active value = 0 }
					if = {
						limit = { has_variable = zg361_last_grade }
						set_variable = { name = zg361_b1_final_grade value = var:zg361_last_grade }
					}
					# #141 closes the superior recommendation only after the direct
					# manager's final band is published.  A miss/hit is observable and
					# adjusts manager judgment credit exactly once; neither route writes
					# a final grade here.
					if = {
						limit = {
							var:zg361_b1_must_review_state = 1
							var:zg361_b1_must_review_manager = root
							var:zg361_b1_must_review_subject = this
							var:zg361_b1_must_review_attention_consumed = 1
						}
						set_variable = { name = zg361_b1_must_review_judgment_result value = 2 }
						set_variable = { name = zg361_b1_must_review_credit_delta value = -1 }
						if = {
							limit = { var:zg361_b1_final_grade = var:zg361_b1_must_review_recommendation }
							set_variable = { name = zg361_b1_must_review_judgment_result value = 1 }
							set_variable = { name = zg361_b1_must_review_credit_delta value = 1 }
						}
						set_variable = { name = zg361_b1_must_review_state value = 2 }
						set_variable = { name = zg361_b1_must_review_object_state value = 2 }
						if = {
							limit = { var:zg361_b1_must_review_route = 1 }
							set_variable = { name = zg361_b1_must_review_book_version_after value = root.var:zg361_b1_quota_book_version }
						}
						root = {
							if = {
								limit = {
									var:zg361_b1_must_review_manager_link_available = 1
									var:zg361_b1_must_review_manager_link_subject = prev
									var:zg361_b1_must_review_manager_link_cycle = prev.var:zg361_b1_cycle_serial
									var:zg361_b1_must_review_manager_link_case = prev.var:zg361_b1_case_serial
								}
								set_variable = { name = zg361_b1_must_review_manager_link_state value = 2 }
								set_variable = { name = zg361_b1_must_review_manager_link_book_version_after value = var:zg361_b1_quota_book_version }
							}
							if = {
								limit = { NOT = { has_variable = zg361_b1_must_review_judgment_credit } }
								set_variable = { name = zg361_b1_must_review_judgment_credit value = 0 }
							}
							if = { limit = { NOT = { has_variable = zg361_b1_evaluator_credit } } set_variable = { name = zg361_b1_evaluator_credit value = 100 } }
							set_variable = { name = zg361_b1_must_review_evaluator_credit_before value = var:zg361_b1_evaluator_credit }
							change_variable = { name = zg361_b1_must_review_judgment_credit add = prev.var:zg361_b1_must_review_credit_delta }
							change_variable = { name = zg361_b1_evaluator_credit add = prev.var:zg361_b1_must_review_credit_delta }
							set_variable = { name = zg361_b1_evaluator_credit value = { value = var:zg361_b1_evaluator_credit max = 125 min = 25 } }
							set_variable = { name = zg361_b1_must_review_evaluator_credit_after value = var:zg361_b1_evaluator_credit }
							set_variable = { name = zg361_b1_must_review_closed_case value = prev.var:zg361_b1_case_serial }
						}
						if = {
							limit = { has_variable = zg361_b1_must_review_superior }
							var:zg361_b1_must_review_superior = {
								if = {
									limit = {
										var:zg361_b1_must_review_host_object_available = 1
										var:zg361_b1_must_review_host_owner = prev.var:zg361_b1_case_owner
										var:zg361_b1_must_review_host_subject = prev
										var:zg361_b1_must_review_host_cycle = prev.var:zg361_b1_cycle_serial
										var:zg361_b1_must_review_host_case = prev.var:zg361_b1_case_serial
										var:zg361_b1_must_review_host_state = 1
									}
									set_variable = { name = zg361_b1_must_review_host_state value = 2 }
								}
							}
						}
					}
					if = {
						limit = {
							has_variable = zg361_result_case_owner
							has_variable = zg361_result_cycle_serial
							has_variable = zg361_result_case_serial
							has_variable = zg361_result_grade
							var:zg361_result_case_owner = var:zg361_b1_case_owner
						}
						# Generic result cases use a per-subject serial namespace.  Freeze an
						# explicit two-tuple adapter while both cases are synchronously live;
						# later appeal hooks must match every field, never compare the two
						# unrelated serials directly.
						set_variable = { name = zg361_b1_result_adapter_result_owner value = var:zg361_result_case_owner }
						set_variable = { name = zg361_b1_result_adapter_result_subject value = this }
						set_variable = { name = zg361_b1_result_adapter_result_cycle value = var:zg361_result_cycle_serial }
						set_variable = { name = zg361_b1_result_adapter_result_case value = var:zg361_result_case_serial }
						set_variable = { name = zg361_b1_result_adapter_b1_owner value = var:zg361_b1_case_owner }
						set_variable = { name = zg361_b1_result_adapter_b1_subject value = this }
						set_variable = { name = zg361_b1_result_adapter_b1_cycle value = var:zg361_b1_cycle_serial }
						set_variable = { name = zg361_b1_result_adapter_b1_case value = var:zg361_b1_case_serial }
						set_variable = { name = zg361_b1_result_adapter_b1_state value = 8 }
						set_variable = { name = zg361_b1_result_adapter_original_grade value = var:zg361_result_grade }
						set_variable = { name = zg361_b1_result_adapter_m008_mode value = root.var:zg361_b1_m008_mode }
						set_variable = { name = zg361_b1_result_adapter_m008_receipt value = 0 }
						if = {
							limit = { has_variable = zg361_b1_m008_receipt_serial }
							set_variable = { name = zg361_b1_result_adapter_m008_receipt value = var:zg361_b1_m008_receipt_serial }
						}
						set_variable = { name = zg361_b1_result_adapter_peer_sealed value = var:zg361_b1_peer_sealed }
						set_variable = { name = zg361_b1_peer_appeal_overturn_processed value = 0 }
__RESULT_ADAPTER_PEER_SLOTS__
					}
					if = {
						limit = { has_variable = zg361_result_grade_reason }
						set_variable = { name = zg361_b1_final_reason value = var:zg361_result_grade_reason }
					}
					# #357's external receipt is minted only after the real B1
					# facts->quota operation and the linked final result both exist.
					# The Workforce bridge may later consume this immutable source
					# tuple, but cannot create it or substitute a readiness flag.
					if = {
						limit = {
							has_variable = zg361_b1_m357_receipt_serial
							var:zg361_b1_m357_receipt_serial = var:zg361_b1_case_serial
							has_variable = zg361_result_case_serial
							has_variable = zg361_b1_result_adapter_result_owner
							has_variable = zg361_b1_result_adapter_result_subject
							has_variable = zg361_b1_result_adapter_result_cycle
							has_variable = zg361_b1_result_adapter_result_case
							has_variable = zg361_b1_result_adapter_b1_owner
							has_variable = zg361_b1_result_adapter_b1_subject
							has_variable = zg361_b1_result_adapter_b1_cycle
							has_variable = zg361_b1_result_adapter_b1_case
							has_variable = zg361_b1_result_adapter_b1_state
							has_variable = zg361_b1_absolute_grade
							has_variable = zg361_b1_final_grade
							has_variable = zg361_b1_final_reason
							has_variable = zg361_b1_forced_down
							var:zg361_b1_result_adapter_result_owner = var:zg361_b1_case_owner
							var:zg361_b1_result_adapter_result_subject = this
							var:zg361_b1_result_adapter_result_cycle = var:zg361_b1_cycle_serial
							var:zg361_b1_result_adapter_result_case = var:zg361_result_case_serial
							var:zg361_b1_result_adapter_b1_owner = var:zg361_b1_case_owner
							var:zg361_b1_result_adapter_b1_subject = this
							var:zg361_b1_result_adapter_b1_cycle = var:zg361_b1_cycle_serial
							var:zg361_b1_result_adapter_b1_case = var:zg361_b1_case_serial
							var:zg361_b1_result_adapter_b1_state = 8
						}
						set_variable = { name = zg361_b1_m357_external_receipt_owner value = var:zg361_b1_case_owner }
						set_variable = { name = zg361_b1_m357_external_receipt_subject value = this }
						set_variable = { name = zg361_b1_m357_external_receipt_cycle value = var:zg361_b1_cycle_serial }
						set_variable = { name = zg361_b1_m357_external_receipt_case value = var:zg361_b1_case_serial }
						set_variable = { name = zg361_b1_m357_external_receipt_state value = 8 }
						set_variable = { name = zg361_b1_m357_external_result_case value = var:zg361_result_case_serial }
						set_variable = { name = zg361_b1_m357_external_absolute_grade value = var:zg361_b1_absolute_grade }
						set_variable = { name = zg361_b1_m357_external_final_grade value = var:zg361_b1_final_grade }
						set_variable = { name = zg361_b1_m357_external_final_reason value = var:zg361_b1_final_reason }
						set_variable = { name = zg361_b1_m357_external_forced_down value = var:zg361_b1_forced_down }
						set_variable = { name = zg361_b1_m357_external_receipt_id value = { value = var:zg361_b1_case_serial multiply = 1000 add = 357 } }
						set_variable = { name = zg361_b1_m357_external_receipt_hash value = { value = var:zg361_result_case_serial multiply = 10000 add = { value = var:zg361_b1_final_reason multiply = 1000 } add = 357 } }
					}
					if = {
						limit = { var:zg361_b1_recusal_active = 1 has_variable = zg361_last_grade }
						set_variable = { name = zg361_b1_recusal_post_grade value = var:zg361_last_grade }
						set_variable = { name = zg361_b1_recusal_lock_match value = 0 }
						if = {
							limit = { var:zg361_last_grade = var:zg361_pending_grade }
							set_variable = { name = zg361_b1_recusal_lock_match value = 1 }
						}
					}
					# #135 B reveals the frozen shadow only together with the final result.
					if = {
						limit = { root.var:zg361_b1_m135_mode = 2 var:zg361_b1_shadow_object_available = 1 }
						set_variable = { name = zg361_b1_shadow_reveal_state value = 2 }
					}
					if = {
						limit = { root.var:zg361_b1_m135_mode != 3 var:zg361_b1_shadow_object_available = 1 var:zg361_b1_shadow_object_state = 1 }
						set_variable = { name = zg361_b1_shadow_object_state value = 2 }
						set_variable = { name = zg361_b1_shadow_object_nonfinal value = 0 }
					}
					set_variable = { name = zg361_b1_shadow_final_drop value = 0 }
					if = {
						limit = {
							root.var:zg361_b1_m135_mode != 3
							var:zg361_b1_shadow_object_available = 1
							var:zg361_b1_final_grade < var:zg361_b1_shadow_grade
						}
						set_variable = { name = zg361_b1_shadow_final_drop value = { value = var:zg361_b1_shadow_grade subtract = var:zg361_b1_final_grade } }
						set_variable = { name = zg361_b1_shadow_drop_explained value = 0 }
						if = {
							limit = { var:zg361_b1_shadow_new_evidence = 1 var:zg361_b1_shadow_evidence_delta < 0 }
							set_variable = { name = zg361_b1_shadow_drop_explained value = 1 }
						}
						if = {
							limit = { var:zg361_b1_shadow_drop_explained = 0 }
							set_variable = { name = zg361_b1_feedback_debt value = 1 }
							set_variable = { name = zg361_b1_feedback_debt_appeal_weight value = { value = var:zg361_b1_shadow_final_drop multiply = 2 max = 6 } }
							set_variable = { name = zg361_b1_feedback_debt_self_safe_evidence value = 1 }
							var:zg361_b1_case_owner = {
								if = {
									limit = { NOT = { has_variable = zg361_b1_feedback_debt_open_n } }
									set_variable = { name = zg361_b1_feedback_debt_open_n value = 0 }
								}
								change_variable = { name = zg361_b1_feedback_debt_open_n add = 1 }
								set_variable = { name = zg361_b1_feedback_debt_due_year value = { value = current_year add = 1 } }
								set_variable = { name = zg361_b1_feedback_debt_source_case value = prev.var:zg361_b1_case_serial }
							}
						}
					}
			}
		}
		remove_character_flag = zg361_b1_cycle_active
		debug_log = "ZG361B1: performance season published"
	}
}

# Public adapter called only by the generic successful appeal-regrade effect.
# The frozen result<->B1 link, five-field B1 receipt and 1->2 direction guard
# make stale or repeated hooks no-op.  Only a negative peer opinion was itself
# overturned; a non-negative A-route opinion may gain corroboration credit.
zg361_b1_on_appeal_corrected_effect = {
	if = {
		limit = {
			has_variable = zg361_b1_result_adapter_result_owner
			has_variable = zg361_b1_result_adapter_result_subject
			has_variable = zg361_b1_result_adapter_result_cycle
			has_variable = zg361_b1_result_adapter_result_case
			has_variable = zg361_b1_result_adapter_b1_owner
			has_variable = zg361_b1_result_adapter_b1_subject
			has_variable = zg361_b1_result_adapter_b1_cycle
			has_variable = zg361_b1_result_adapter_b1_case
			has_variable = zg361_b1_result_adapter_b1_state
			has_variable = zg361_b1_result_adapter_original_grade
			has_variable = zg361_b1_result_adapter_m008_mode
			has_variable = zg361_b1_result_adapter_m008_receipt
			has_variable = zg361_b1_result_adapter_peer_sealed
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
			has_variable = zg361_result_grade
			has_variable = zg361_result_appeal_outcome
			has_variable = zg361_result_refund_posted_serial
			var:zg361_b1_result_adapter_b1_subject = this
			var:zg361_b1_result_adapter_b1_state = 8
			var:zg361_b1_result_adapter_result_owner = var:zg361_result_case_owner
			var:zg361_b1_result_adapter_result_subject = this
			var:zg361_b1_result_adapter_result_cycle = var:zg361_result_cycle_serial
			var:zg361_b1_result_adapter_result_case = var:zg361_result_case_serial
			var:zg361_b1_result_adapter_original_grade = 1
			var:zg361_result_case_state = 5
			var:zg361_result_grade = 2
			var:zg361_result_appeal_outcome = 1
			var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
			var:zg361_b1_result_adapter_peer_sealed = 1
			var:zg361_b1_result_adapter_m008_receipt = var:zg361_b1_result_adapter_b1_case
			var:zg361_b1_result_adapter_m008_mode != 3
			trigger_if = {
				limit = {
					has_variable = zg361_b1_peer_appeal_receipt_owner
					has_variable = zg361_b1_peer_appeal_receipt_subject
					has_variable = zg361_b1_peer_appeal_receipt_cycle
					has_variable = zg361_b1_peer_appeal_receipt_case
					has_variable = zg361_b1_peer_appeal_receipt_state
					has_variable = zg361_b1_peer_appeal_overturn_receipt
				}
				NOT = {
					AND = {
						var:zg361_b1_peer_appeal_receipt_owner = var:zg361_b1_result_adapter_b1_owner
						var:zg361_b1_peer_appeal_receipt_subject = this
						var:zg361_b1_peer_appeal_receipt_cycle = var:zg361_b1_result_adapter_b1_cycle
						var:zg361_b1_peer_appeal_receipt_case = var:zg361_b1_result_adapter_b1_case
						var:zg361_b1_peer_appeal_receipt_state = var:zg361_b1_result_adapter_b1_state
						var:zg361_b1_peer_appeal_overturn_receipt = var:zg361_result_case_serial
					}
				}
			}
			trigger_else = { always = yes }
		}
		zg361_b1_apply_appeal_credit_slot_1_effect = yes
		zg361_b1_apply_appeal_credit_slot_2_effect = yes
		zg361_b1_apply_appeal_credit_slot_3_effect = yes
		set_variable = { name = zg361_b1_peer_appeal_overturn_processed value = 1 }
		set_variable = { name = zg361_b1_peer_appeal_receipt_owner value = var:zg361_b1_result_adapter_b1_owner }
		set_variable = { name = zg361_b1_peer_appeal_receipt_subject value = this }
		set_variable = { name = zg361_b1_peer_appeal_receipt_cycle value = var:zg361_b1_result_adapter_b1_cycle }
		set_variable = { name = zg361_b1_peer_appeal_receipt_case value = var:zg361_b1_result_adapter_b1_case }
		set_variable = { name = zg361_b1_peer_appeal_receipt_state value = var:zg361_b1_result_adapter_b1_state }
		set_variable = { name = zg361_b1_peer_appeal_overturn_receipt value = var:zg361_result_case_serial }
	}
}

# A peer record is accepted only when both officials are registered
# participants on the same side of one live war.  The evidence tuple is minted
# on that real war scope and copied into the sealed slot; a cohort/case serial
# is never used as a synthetic "common task" substitute.
zg361_b1_prepare_shared_war_peer_task_effect = {
	set_variable = { name = zg361_b1_peer_common_task_found value = 0 }
	set_variable = { name = zg361_b1_peer_common_task_kind value = 0 }
	set_variable = { name = zg361_b1_peer_common_task_serial value = 0 }
	remove_variable = zg361_b1_peer_common_task_owner
	remove_variable = zg361_b1_peer_common_task_attacker
	remove_variable = zg361_b1_peer_common_task_defender
	if = {
		limit = {
			zg361_b1_peer_submission_actor_trigger = yes
			has_variable = zg361_b1_case_subject
			has_variable = zg361_b1_case_serial
			has_variable = zg361_b1_case_active
			has_variable = zg361_b1_roster_included
			has_variable = zg361_b1_peer_use_mode
			NOT = { this = scope:recipient }
			var:zg361_b1_case_subject = this
			var:zg361_b1_case_active = 1
			var:zg361_b1_roster_included = 1
			var:zg361_b1_peer_use_mode != 0
			var:zg361_b1_case_owner = {
				is_target_in_variable_list = {
					name = zg361_b1_subjects
					target = scope:recipient
				}
			}
			scope:recipient = {
				zg361_b1_peer_submission_recipient_trigger = yes
				has_variable = zg361_b1_case_subject
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_active
				has_variable = zg361_b1_roster_included
				var:zg361_b1_case_subject = this
				var:zg361_b1_case_serial = scope:actor.var:zg361_b1_case_serial
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				NOT = {
					OR = {
						AND = {
							var:zg361_b1_peer_slot_1_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_1_evaluator }
								var:zg361_b1_peer_slot_1_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_2_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_2_evaluator }
								var:zg361_b1_peer_slot_2_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_3_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_3_evaluator }
								var:zg361_b1_peer_slot_3_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
					}
				}
			}
		}
		random_character_war = {
			limit = {
				OR = {
					AND = {
						scope:actor = { is_attacker_in_war = prev }
						scope:recipient = { is_attacker_in_war = prev }
					}
					AND = {
						scope:actor = { is_defender_in_war = prev }
						scope:recipient = { is_defender_in_war = prev }
					}
				}
			}
			save_temporary_scope_as = zg361_b1_peer_common_war
			scope:actor = { set_variable = { name = zg361_b1_peer_common_task_found value = 1 } }
		}
		if = {
			limit = { var:zg361_b1_peer_common_task_found = 1 exists = scope:zg361_b1_peer_common_war }
			scope:zg361_b1_peer_common_war = {
				if = {
					limit = { NOT = { has_variable = zg361_b1_peer_task_serial_cursor } }
					set_variable = { name = zg361_b1_peer_task_serial_cursor value = 0 }
				}
				if = {
					limit = {
						trigger_if = {
							limit = {
								has_variable = zg361_b1_peer_task_owner
								has_variable = zg361_b1_peer_task_cycle
								has_variable = zg361_b1_peer_task_case
							}
							OR = {
								NOT = { var:zg361_b1_peer_task_owner = scope:actor.var:zg361_b1_case_owner }
								NOT = { var:zg361_b1_peer_task_cycle = scope:actor.var:zg361_b1_cycle_serial }
								NOT = { var:zg361_b1_peer_task_case = scope:actor.var:zg361_b1_case_serial }
							}
						}
						trigger_else = { always = yes }
					}
					change_variable = { name = zg361_b1_peer_task_serial_cursor add = 1 }
					set_variable = { name = zg361_b1_peer_task_owner value = scope:actor.var:zg361_b1_case_owner }
					set_variable = { name = zg361_b1_peer_task_cycle value = scope:actor.var:zg361_b1_cycle_serial }
					set_variable = { name = zg361_b1_peer_task_case value = scope:actor.var:zg361_b1_case_serial }
				}
			}
			set_variable = { name = zg361_b1_peer_common_task_kind value = 1 }
			set_variable = { name = zg361_b1_peer_common_task_serial value = scope:zg361_b1_peer_common_war.var:zg361_b1_peer_task_serial_cursor }
			set_variable = { name = zg361_b1_peer_common_task_owner value = var:zg361_b1_case_owner }
			set_variable = { name = zg361_b1_peer_common_task_cycle value = var:zg361_b1_cycle_serial }
			set_variable = { name = zg361_b1_peer_common_task_case value = var:zg361_b1_case_serial }
			set_variable = { name = zg361_b1_peer_common_task_attacker value = scope:zg361_b1_peer_common_war.primary_attacker }
			set_variable = { name = zg361_b1_peer_common_task_defender value = scope:zg361_b1_peer_common_war.primary_defender }
		}
	}
}

zg361_b1_submit_peer_recommendation_effect = {
	zg361_b1_submit_peer_positive_effect = yes
}

zg361_b1_submit_peer_positive_effect = {
	zg361_b1_prepare_shared_war_peer_task_effect = yes
	if = {
		limit = {
			trigger_if = {
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_b1_roster_included
					has_variable = zg361_b1_peer_used
					has_variable = zg361_b1_peer_cap
					has_variable = zg361_b1_peer_fatigue
					has_variable = zg361_b1_peer_use_mode
					scope:recipient = {
						has_variable = zg361_b1_case_owner
						has_variable = zg361_b1_case_subject
						has_variable = zg361_b1_cycle_serial
						has_variable = zg361_b1_case_serial
						has_variable = zg361_b1_case_state
						has_variable = zg361_b1_case_active
						has_variable = zg361_b1_roster_included
						has_variable = zg361_b1_peer_slot_1_filled
						has_variable = zg361_b1_peer_slot_2_filled
						has_variable = zg361_b1_peer_slot_3_filled
					}
				}
				NOT = { this = scope:recipient }
				var:zg361_b1_case_subject = this
				var:zg361_b1_case_state = 3
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_peer_use_mode != 0
				var:zg361_b1_peer_common_task_found = 1
				var:zg361_b1_peer_common_task_kind = 1
				var:zg361_b1_peer_used < var:zg361_b1_peer_cap
				var:zg361_b1_case_owner = {
					trigger_if = {
						limit = { has_variable_list = zg361_b1_subjects }
						is_target_in_variable_list = {
							name = zg361_b1_subjects
							target = scope:recipient
						}
					}
					trigger_else = { always = no }
				}
				scope:recipient = {
					var:zg361_b1_case_owner = scope:actor.var:zg361_b1_case_owner
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:actor.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:actor.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 3
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					OR = {
						var:zg361_b1_peer_slot_1_filled = 0
						var:zg361_b1_peer_slot_2_filled = 0
						var:zg361_b1_peer_slot_3_filled = 0
					}
					NOT = {
						OR = {
						AND = {
							var:zg361_b1_peer_slot_1_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_1_evaluator }
								var:zg361_b1_peer_slot_1_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_2_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_2_evaluator }
								var:zg361_b1_peer_slot_2_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_3_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_3_evaluator }
								var:zg361_b1_peer_slot_3_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						}
					}
				}
			}
			trigger_else = { always = no }
		}
		if = {
			limit = { NOT = { has_variable = zg361_b1_evaluator_credit } }
			set_variable = { name = zg361_b1_evaluator_credit value = 100 }
			set_variable = { name = zg361_b1_evaluator_sample_n value = 0 }
		}
		set_variable = {
			name = zg361_b1_peer_submission_weight
			value = {
				value = var:zg361_b1_evaluator_credit
				subtract = var:zg361_b1_peer_fatigue
				max = 100
				min = 25
			}
		}
		if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_1_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_1_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_1_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_1_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_1_raw value = 10 }
				set_variable = { name = zg361_b1_peer_slot_1_performance value = 10 }
				set_variable = { name = zg361_b1_peer_slot_1_collaboration value = 10 }
				set_variable = { name = zg361_b1_peer_slot_1_values value = 10 }
				set_variable = { name = zg361_b1_peer_slot_1_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 1 } }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_1_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_1_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_1_submitted_year value = current_year }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_2_filled = 0 }
				scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_2_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_2_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_2_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_2_raw value = 10 }
				set_variable = { name = zg361_b1_peer_slot_2_performance value = 10 }
				set_variable = { name = zg361_b1_peer_slot_2_collaboration value = 10 }
				set_variable = { name = zg361_b1_peer_slot_2_values value = 10 }
				set_variable = { name = zg361_b1_peer_slot_2_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 2 } }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_2_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_2_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_2_submitted_year value = current_year }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_3_filled = 0 }
				scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_3_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_3_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_3_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_3_raw value = 10 }
				set_variable = { name = zg361_b1_peer_slot_3_performance value = 10 }
				set_variable = { name = zg361_b1_peer_slot_3_collaboration value = 10 }
				set_variable = { name = zg361_b1_peer_slot_3_values value = 10 }
				set_variable = { name = zg361_b1_peer_slot_3_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 3 } }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_3_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_3_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_3_submitted_year value = current_year }
			}
		}
		change_variable = { name = zg361_b1_peer_used add = 1 }
		change_variable = { name = zg361_b1_peer_fatigue add = 15 }
		set_variable = {
			name = zg361_b1_peer_fatigue
			value = { value = var:zg361_b1_peer_fatigue max = 60 }
		}
		scope:recipient = {
			change_variable = { name = zg361_b1_peer_n add = 1 }
			change_variable = { name = zg361_b1_peer_raw_sum add = 10 }
			change_variable = { name = zg361_b1_peer_timely_n add = 1 }
		}
		debug_log = "ZG361B1: sealed positive peer record submitted"
	}
	else = {
		if = {
			limit = {
				trigger_if = {
					limit = {
						has_variable = zg361_b1_peer_used
						has_variable = zg361_b1_peer_cap
					}
					var:zg361_b1_peer_used >= var:zg361_b1_peer_cap
				}
				trigger_else = { always = no }
			}
			change_variable = { name = zg361_b1_peer_over_cap add = 1 }
		}
	}
}

zg361_b1_submit_peer_negative_effect = {
	zg361_b1_prepare_shared_war_peer_task_effect = yes
	if = {
		limit = {
			trigger_if = {
				limit = {
					has_variable = zg361_b1_case_owner
					has_variable = zg361_b1_case_subject
					has_variable = zg361_b1_cycle_serial
					has_variable = zg361_b1_case_serial
					has_variable = zg361_b1_case_state
					has_variable = zg361_b1_case_active
					has_variable = zg361_b1_roster_included
					has_variable = zg361_b1_peer_used
					has_variable = zg361_b1_peer_cap
					has_variable = zg361_b1_peer_fatigue
					has_variable = zg361_b1_peer_use_mode
					scope:recipient = {
						has_variable = zg361_b1_case_owner
						has_variable = zg361_b1_case_subject
						has_variable = zg361_b1_cycle_serial
						has_variable = zg361_b1_case_serial
						has_variable = zg361_b1_case_state
						has_variable = zg361_b1_case_active
						has_variable = zg361_b1_roster_included
						has_variable = zg361_b1_peer_slot_1_filled
						has_variable = zg361_b1_peer_slot_2_filled
						has_variable = zg361_b1_peer_slot_3_filled
					}
				}
				NOT = { this = scope:recipient }
				var:zg361_b1_case_subject = this
				var:zg361_b1_case_state = 3
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
				var:zg361_b1_peer_use_mode != 0
				var:zg361_b1_peer_common_task_found = 1
				var:zg361_b1_peer_common_task_kind = 1
				var:zg361_b1_peer_used < var:zg361_b1_peer_cap
				var:zg361_b1_case_owner = {
					trigger_if = {
						limit = { has_variable_list = zg361_b1_subjects }
						is_target_in_variable_list = {
							name = zg361_b1_subjects
							target = scope:recipient
						}
					}
					trigger_else = { always = no }
				}
				scope:recipient = {
					var:zg361_b1_case_owner = scope:actor.var:zg361_b1_case_owner
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:actor.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = scope:actor.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 3
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					OR = {
						var:zg361_b1_peer_slot_1_filled = 0
						var:zg361_b1_peer_slot_2_filled = 0
						var:zg361_b1_peer_slot_3_filled = 0
					}
					NOT = {
						OR = {
						AND = {
							var:zg361_b1_peer_slot_1_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_1_evaluator }
								var:zg361_b1_peer_slot_1_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_2_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_2_evaluator }
								var:zg361_b1_peer_slot_2_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						AND = {
							var:zg361_b1_peer_slot_3_filled = 1
							trigger_if = {
								limit = { has_variable = zg361_b1_peer_slot_3_evaluator }
								var:zg361_b1_peer_slot_3_evaluator = scope:actor
							}
							trigger_else = { always = no }
						}
						}
					}
				}
			}
			trigger_else = { always = no }
		}
		if = {
			limit = { NOT = { has_variable = zg361_b1_evaluator_credit } }
			set_variable = { name = zg361_b1_evaluator_credit value = 100 }
			set_variable = { name = zg361_b1_evaluator_sample_n value = 0 }
		}
		set_variable = {
			name = zg361_b1_peer_submission_weight
			value = {
				value = var:zg361_b1_evaluator_credit
				subtract = var:zg361_b1_peer_fatigue
				max = 100
				min = 25
			}
		}
		if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_1_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_1_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_1_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_1_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_1_raw value = -15 }
				set_variable = { name = zg361_b1_peer_slot_1_performance value = -15 }
				set_variable = { name = zg361_b1_peer_slot_1_collaboration value = -15 }
				set_variable = { name = zg361_b1_peer_slot_1_values value = -15 }
				set_variable = { name = zg361_b1_peer_slot_1_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 1 } }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_1_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_1_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_1_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_1_submitted_year value = current_year }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_2_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_2_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_2_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_2_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_2_raw value = -15 }
				set_variable = { name = zg361_b1_peer_slot_2_performance value = -15 }
				set_variable = { name = zg361_b1_peer_slot_2_collaboration value = -15 }
				set_variable = { name = zg361_b1_peer_slot_2_values value = -15 }
				set_variable = { name = zg361_b1_peer_slot_2_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 2 } }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_2_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_2_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_2_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_2_submitted_year value = current_year }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_3_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_3_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_3_subject value = scope:recipient }
				set_variable = { name = zg361_b1_peer_slot_3_cycle value = var:zg361_b1_cycle_serial }
				set_variable = { name = zg361_b1_peer_slot_3_raw value = -15 }
				set_variable = { name = zg361_b1_peer_slot_3_performance value = -15 }
				set_variable = { name = zg361_b1_peer_slot_3_collaboration value = -15 }
				set_variable = { name = zg361_b1_peer_slot_3_values value = -15 }
				set_variable = { name = zg361_b1_peer_slot_3_example_id value = { value = var:zg361_b1_case_serial multiply = 10 add = 3 } }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_id value = scope:actor.var:zg361_b1_peer_common_task_serial }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_kind value = scope:actor.var:zg361_b1_peer_common_task_kind }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_owner value = scope:actor.var:zg361_b1_peer_common_task_owner }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_cycle value = scope:actor.var:zg361_b1_peer_common_task_cycle }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_case value = scope:actor.var:zg361_b1_peer_common_task_case }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_attacker value = scope:actor.var:zg361_b1_peer_common_task_attacker }
				set_variable = { name = zg361_b1_peer_slot_3_common_task_defender value = scope:actor.var:zg361_b1_peer_common_task_defender }
				set_variable = { name = zg361_b1_peer_slot_3_invitation_source value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_anonymous value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_contribution_weight value = 5 }
				set_variable = { name = zg361_b1_peer_slot_3_weight value = scope:actor.var:zg361_b1_peer_submission_weight }
				set_variable = { name = zg361_b1_peer_slot_3_submitted_year value = current_year }
			}
		}
		change_variable = { name = zg361_b1_peer_used add = 1 }
		change_variable = { name = zg361_b1_peer_fatigue add = 15 }
		set_variable = {
			name = zg361_b1_peer_fatigue
			value = { value = var:zg361_b1_peer_fatigue max = 60 }
		}
		scope:recipient = {
			change_variable = { name = zg361_b1_peer_n add = 1 }
			change_variable = { name = zg361_b1_peer_raw_sum add = -15 }
			change_variable = { name = zg361_b1_peer_timely_n add = 1 }
		}
		debug_log = "ZG361B1: sealed negative peer record submitted"
	}
	else = {
		if = {
			limit = {
				trigger_if = {
					limit = {
						has_variable = zg361_b1_peer_used
						has_variable = zg361_b1_peer_cap
					}
					var:zg361_b1_peer_used >= var:zg361_b1_peer_cap
				}
				trigger_else = { always = no }
			}
			change_variable = { name = zg361_b1_peer_over_cap add = 1 }
		}
	}
}
'''
    body = body.replace("__POLICY_FREEZE_BLOCKS__", render_policy_freeze_blocks())
    body = body.replace(
        "__STAGE_S_POLICY_FREEZE_BLOCKS__", render_stage_s_policy_freeze_blocks()
    )
    body = body.replace(
        "__RESULT_ADAPTER_PEER_SLOTS__", render_result_adapter_peer_slots()
    )
    return generated(
        bindings
        + "\n\n"
        + body
        + "\n\n"
        + peer_slot_consumers
        + "\n\n"
        + appeal_slot_consumers
    )


def render_events() -> bytes:
    return generated(r'''
namespace = zg361b1

# Player subject: one sealed self-review response. Each option revalidates the
# owner/subject/cycle/case/state ticket before writing the subject-owned case.
zg361b1.200 = {
	type = character_event
	theme = vassal
	title = zg361b1.200.t
	desc = zg361b1.200.desc

	option = {
		name = zg361b1.200.a
		zg361_b1_submit_self_honest_ticket_effect = yes
	}
	option = {
		name = zg361b1.200.b
		zg361_b1_submit_self_exaggerated_ticket_effect = yes
	}
	option = {
		name = zg361b1.200.c
		zg361_b1_submit_self_conservative_ticket_effect = yes
	}
}

# Player subject: accept the non-final shadow grade or add one bounded evidence
# packet. Neither route mutates the already frozen KPI/absolute-grade facts.
zg361b1.201 = {
	type = character_event
	theme = vassal
	title = zg361b1.201.t
	desc = zg361b1.201.desc

	option = {
		name = zg361b1.201.a
		zg361_b1_submit_shadow_accept_ticket_effect = yes
	}
	option = {
		name = zg361b1.201.b
		zg361_b1_submit_shadow_supplement_ticket_effect = yes
	}
}

# Common-superior season synchronization. The delayed character event resets
# ROOT to each sibling manager; the cycle-open guard makes replays harmless.
zg361b1.90 = {
	type = character_event
	hidden = yes
	immediate = { zg361_b1_open_cycle_effect = yes }
}

# D+180: check-in and one evidence-backed target reset.
zg361b1.100 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_ticket_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_cycle_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 1
				}
				zg361_b1_midcycle_dispatcher_effect = yes
				save_scope_as = zg361_b1_ticket_owner
				save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
				save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
				save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
				trigger_event = { id = zg361b1.101 days = 60 }
			}
			else = { debug_log = "ZG361B1: stale midcycle ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete midcycle ticket ignored" }
	}
}

# D+240: open the bounded three-slot peer/self-evidence window.
zg361b1.101 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 2
				}
				zg361_b1_peer_window_dispatcher_effect = yes
				save_scope_as = zg361_b1_ticket_owner
				save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
				save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
				save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
				trigger_event = { id = zg361b1.102 days = 60 }
			}
			else = { debug_log = "ZG361B1: stale peer-window ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete peer-window ticket ignored" }
	}
}

# D+300: seal peer records, then enter the existing ranking engine. The engine
# opens a real shadow window instead of settling immediately when B1 is active.
zg361b1.102 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 3
				}
				zg361_b1_prepare_facts_effect = yes
				zg361_run_review_effect = yes
			}
			else = { debug_log = "ZG361B1: stale facts ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete facts ticket ignored" }
	}
}

# D+330: close shadow evidence and post the manager's quota book.
zg361b1.103 = {
	type = character_event
	hidden = yes
	immediate = {
		# Save the event-root character as a real object scope before writing the
		# list. CK3 1.19.0.6 does not count a flag: enum as a setter for a list
		# later consumed as character scopes. Keep this object anchor alive through
		# the list read, then restore both membership and container existence.
		save_temporary_scope_as = zg361_b1_subjects_event_loader_anchor
		remove_character_flag = zg361_b1_subjects_event_loader_had_list
		if = {
			limit = { has_variable_list = zg361_b1_subjects }
			add_character_flag = zg361_b1_subjects_event_loader_had_list
		}
		add_to_variable_list = { name = zg361_b1_subjects target = scope:zg361_b1_subjects_event_loader_anchor }
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 5
				}
				every_in_list = {
					variable = zg361_b1_subjects
					limit = { NOT = { this = scope:zg361_b1_subjects_event_loader_anchor } }
					if = {
						limit = {
							has_variable = zg361_b1_case_owner
							var:zg361_b1_case_owner = root
							var:zg361_b1_case_state = 5
							var:zg361_b1_shadow_response_state = 0
						}
						zg361_b1_record_shadow_accept_effect = yes
					}
				}
				remove_list_variable = { name = zg361_b1_subjects target = scope:zg361_b1_subjects_event_loader_anchor }
				if = {
					limit = { NOT = { has_character_flag = zg361_b1_subjects_event_loader_had_list } }
					clear_variable_list = zg361_b1_subjects
				}
				remove_character_flag = zg361_b1_subjects_event_loader_had_list
				set_variable = { name = zg361_b1_cycle_state value = 6 }
				zg361_b1_submit_quota_book_effect = yes
			}
			else = {
				remove_list_variable = { name = zg361_b1_subjects target = scope:zg361_b1_subjects_event_loader_anchor }
				if = {
					limit = { NOT = { has_character_flag = zg361_b1_subjects_event_loader_had_list } }
					clear_variable_list = zg361_b1_subjects
				}
				remove_character_flag = zg361_b1_subjects_event_loader_had_list
				debug_log = "ZG361B1: stale shadow-close ticket ignored"
			}
		}
		else = {
			remove_list_variable = { name = zg361_b1_subjects target = scope:zg361_b1_subjects_event_loader_anchor }
			if = {
				limit = { NOT = { has_character_flag = zg361_b1_subjects_event_loader_had_list } }
				clear_variable_list = zg361_b1_subjects
			}
			remove_character_flag = zg361_b1_subjects_event_loader_had_list
			debug_log = "ZG361B1: incomplete shadow-close ticket ignored"
		}
	}
}

# Common-superior close: either all expected managers are ready, or the frozen
# deadline expires. Both routes share owner/season/case/state and close once.
zg361b1.110 = {
	type = character_event
	hidden = yes
	immediate = {
		# Use a real character scope for the loader-visible write. A character flag
		# preserves the pre-anchor branch decision; the object anchor is removed
		# before the close effect, so no manager iterator can consume the superior.
		save_temporary_scope_as = zg361_b1_ready_managers_event_loader_anchor
		remove_character_flag = zg361_b1_ready_managers_event_loader_had_list
		if = {
			limit = { has_variable_list = zg361_b1_ready_managers }
			add_character_flag = zg361_b1_ready_managers_event_loader_had_list
		}
		add_to_variable_list = { name = zg361_b1_ready_managers target = scope:zg361_b1_ready_managers_event_loader_anchor }
		if = {
			limit = {
				exists = scope:zg361_b1_bank_ticket_owner
				has_variable = zg361_b1_bank_season
				has_variable = zg361_b1_bank_case_serial
				has_variable = zg361_b1_bank_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_bank_ticket_owner
					var:zg361_b1_bank_season = scope:zg361_b1_bank_ticket_season
					var:zg361_b1_bank_case_serial = scope:zg361_b1_bank_ticket_case
					var:zg361_b1_bank_state = scope:zg361_b1_bank_ticket_state
					var:zg361_b1_bank_state = 1
				}
				if = {
					limit = {
						has_character_flag = zg361_b1_ready_managers_event_loader_had_list
						has_variable_list = zg361_b1_ready_managers
					}
					remove_list_variable = { name = zg361_b1_ready_managers target = scope:zg361_b1_ready_managers_event_loader_anchor }
					remove_character_flag = zg361_b1_ready_managers_event_loader_had_list
					zg361_b1_close_common_superior_bank_effect = yes
				}
				else = {
					remove_list_variable = { name = zg361_b1_ready_managers target = scope:zg361_b1_ready_managers_event_loader_anchor }
					if = {
						limit = { NOT = { has_character_flag = zg361_b1_ready_managers_event_loader_had_list } }
						clear_variable_list = zg361_b1_ready_managers
					}
					remove_character_flag = zg361_b1_ready_managers_event_loader_had_list
					# A deadline may legitimately outlive every expected manager.
					# Close the bank without evaluating an unset ready list.
					set_variable = { name = zg361_b1_bank_state value = 2 }
					debug_log = "ZG361B1: common-superior bank closed with no ready managers"
				}
			}
			else = {
				remove_list_variable = { name = zg361_b1_ready_managers target = scope:zg361_b1_ready_managers_event_loader_anchor }
				if = {
					limit = { NOT = { has_character_flag = zg361_b1_ready_managers_event_loader_had_list } }
					clear_variable_list = zg361_b1_ready_managers
				}
				remove_character_flag = zg361_b1_ready_managers_event_loader_had_list
				debug_log = "ZG361B1: stale common-superior bank ticket ignored"
			}
		}
		else = {
			remove_list_variable = { name = zg361_b1_ready_managers target = scope:zg361_b1_ready_managers_event_loader_anchor }
			if = {
				limit = { NOT = { has_character_flag = zg361_b1_ready_managers_event_loader_had_list } }
				clear_variable_list = zg361_b1_ready_managers
			}
			remove_character_flag = zg361_b1_ready_managers_event_loader_had_list
			debug_log = "ZG361B1: incomplete common-superior bank ticket ignored"
		}
	}
}

# Common-superior allocation has just written manager-owned receipts, but the
# closing event's ROOT is the superior. Reset ROOT to the allocated manager and
# validate its immutable case token before entering calibration/settlement.
zg361b1.111 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_ticket_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_cycle_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 6
				}
				zg361_b1_open_calibration_effect = yes
			}
			else = { debug_log = "ZG361B1: stale manager-calibration ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete manager-calibration ticket ignored" }
	}
}

# Per-subject pending deadline. The shared kernel consumes the frozen
# owner/subject/cycle/case/state ticket before the domain resolver can write.
zg361b1.121 = {
	type = character_event
	hidden = yes
	immediate = {
		zg361_case_kernel_expire_deadline_effect = {
			OWNER_VAR = zg361_b1_case_owner
			SUBJECT_VAR = zg361_b1_case_subject
			CYCLE_VAR = zg361_b1_cycle_serial
			CASE_VAR = zg361_b1_case_serial
			STATE_VAR = zg361_b1_case_state
			ACTIVE_VAR = zg361_b1_case_active
			DEADLINE_OWNER_VAR = zg361_b1_pending_deadline_owner
			DEADLINE_SUBJECT_VAR = zg361_b1_pending_deadline_subject
			DEADLINE_CYCLE_VAR = zg361_b1_pending_deadline_ticket_cycle
			DEADLINE_CASE_VAR = zg361_b1_pending_deadline_ticket_case
			DEADLINE_STATE_VAR = zg361_b1_pending_deadline_ticket_state
			DEADLINE_PENDING_VAR = zg361_b1_pending_deadline_pending
			DEADLINE_EXPIRED_VAR = zg361_b1_pending_deadline_expired
			REVISION_VAR = zg361_b1_case_revision
			TIMELINE_VAR = zg361_b1_case_timeline_serial
			FEEDBACK_VAR = zg361_b1_case_feedback_revision
		}
		if = {
			limit = {
				has_variable = zg361_case_kernel_applied
				var:zg361_case_kernel_applied = 1
				var:zg361_b1_case_subject = this
				var:zg361_b1_pending_object_available = 1
				var:zg361_b1_pending_object_owner = var:zg361_b1_case_owner
				var:zg361_b1_pending_object_subject = this
				var:zg361_b1_pending_object_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_pending_object_case = var:zg361_b1_case_serial
				var:zg361_b1_pending_object_state = 1
				var:zg361_b1_pending_state = 1
				var:zg361_b1_case_state = 7
				var:zg361_b1_case_active = 1
				var:zg361_b1_roster_included = 1
			}
			# Observe a fresh live KPI only after the independent 30-day deadline;
			# facts/evidence_late remains immutable and is merely the frozen target
			# before-image. This makes success/failure depend on new gameplay state.
			set_variable = { name = zg361_b1_pending_observed_score value = zg361_kpi_value }
			set_variable = { name = zg361_b1_pending_observation_recorded value = 1 }
			set_variable = { name = zg361_b1_pending_observation_year value = current_year }
			set_variable = { name = zg361_b1_pending_observation_serial value = var:zg361_b1_case_revision }
			zg361_b1_resolve_pending_subject_effect = yes
		}
		else = { debug_log = "ZG361B1: stale pending milestone ticket ignored" }
	}
}

# Sealed-board late-evidence batch.  Every live subject gets one immutable
# owner/subject/cycle/case/state object and one fresh observation. Route A waits
# for the entire batch and may reopen at most the single largest qualifying
# delta; route B only creates a visible next-cycle object. Route C schedules no
# event. A duplicate/stale callback cannot decrement the barrier twice.
zg361b1.122 = {
	type = character_event
	hidden = yes
	immediate = {
		set_variable = { name = zg361_b1_reopen_callback_consumed value = 0 }
		if = {
			limit = {
				exists = scope:zg361_b1_reopen_ticket_owner
				exists = scope:zg361_b1_reopen_ticket_subject
				this = scope:zg361_b1_reopen_ticket_owner
				var:zg361_b1_cycle_serial = scope:zg361_b1_reopen_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_reopen_ticket_case
				var:zg361_b1_cycle_state = scope:zg361_b1_reopen_ticket_state
				var:zg361_b1_cycle_state = 7
				var:zg361_b1_closure_state = 1
				var:zg361_b1_reopen_pending_n >= 1
				var:zg361_b1_sealed_board_hash = scope:zg361_b1_reopen_ticket_hash
				var:zg361_b1_reward_snapshot_hash = scope:zg361_b1_reopen_ticket_reward_hash
				var:zg361_b1_quota_book_version = scope:zg361_b1_reopen_ticket_book_version
				var:zg361_b1_reopen_batch_object_available = 1
				var:zg361_b1_reopen_batch_owner = this
				var:zg361_b1_reopen_batch_subject = this
				var:zg361_b1_reopen_batch_cycle = var:zg361_b1_cycle_serial
				var:zg361_b1_reopen_batch_case = var:zg361_b1_case_serial
				var:zg361_b1_reopen_batch_state = 1
			}
			if = {
				limit = {
				scope:zg361_b1_reopen_ticket_subject = {
					is_alive = yes
					var:zg361_b1_case_owner = scope:zg361_b1_reopen_ticket_owner
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_reopen_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_reopen_ticket_case
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					var:zg361_pending_grade = var:zg361_b1_reopen_sealed_grade
					var:zg361_b1_reopen_object_available = 1
					var:zg361_b1_reopen_object_id = scope:zg361_b1_reopen_ticket_object
					var:zg361_b1_reopen_object_owner = scope:zg361_b1_reopen_ticket_owner
					var:zg361_b1_reopen_object_subject = this
					var:zg361_b1_reopen_object_cycle = scope:zg361_b1_reopen_ticket_cycle
					var:zg361_b1_reopen_object_case = scope:zg361_b1_reopen_ticket_case
					var:zg361_b1_reopen_object_state = 1
					var:zg361_b1_reopen_route = scope:zg361_b1_reopen_ticket_route
				}
				}
				scope:zg361_b1_reopen_ticket_subject = {
				# This post-seal observation is new gameplay state. The frozen facts
				# score is retained as the before-image and is never rewritten.
				set_variable = { name = zg361_b1_reopen_observed_score value = zg361_kpi_value }
				set_variable = {
					name = zg361_b1_reopen_late_evidence_delta
					value = { value = var:zg361_b1_reopen_observed_score subtract = var:zg361_b1_reopen_baseline_score }
				}
				set_variable = { name = zg361_b1_reopen_late_evidence_magnitude value = var:zg361_b1_reopen_late_evidence_delta }
				if = {
					limit = { var:zg361_b1_reopen_late_evidence_magnitude < 0 }
					set_variable = { name = zg361_b1_reopen_late_evidence_magnitude value = { value = var:zg361_b1_reopen_late_evidence_magnitude multiply = -1 } }
				}
				set_variable = { name = zg361_b1_reopen_observation_recorded value = 1 }
				set_variable = { name = zg361_b1_reopen_observation_year value = current_year }
				set_variable = { name = zg361_b1_reopen_observation_serial value = var:zg361_b1_case_revision }
				set_variable = {
					name = zg361_b1_reopen_stable_order_key
					value = {
						value = var:zg361_b1_reopen_late_evidence_magnitude multiply = 1000000
						subtract = { value = var:zg361_b1_roster_frozen_order multiply = 1000 }
						subtract = var:zg361_b1_reopen_object_case
					}
				}
				set_variable = { name = zg361_b1_reopen_object_state value = 2 }
				if = {
					limit = { var:zg361_b1_reopen_route = 2 }
					set_variable = { name = zg361_b1_post_cutoff_event_id value = var:zg361_b1_reopen_object_id }
					set_variable = { name = zg361_b1_post_cutoff_event_owner value = var:zg361_b1_reopen_object_owner }
					set_variable = { name = zg361_b1_post_cutoff_event_subject value = this }
					set_variable = { name = zg361_b1_post_cutoff_event_cycle value = var:zg361_b1_reopen_object_cycle }
					set_variable = { name = zg361_b1_post_cutoff_event_case value = var:zg361_b1_reopen_object_case }
					set_variable = { name = zg361_b1_post_cutoff_event_state value = 1 }
					set_variable = { name = zg361_b1_post_cutoff_event_sign value = 0 }
					if = { limit = { var:zg361_b1_reopen_late_evidence_delta > 0 } set_variable = { name = zg361_b1_post_cutoff_event_sign value = 1 } }
					else_if = { limit = { var:zg361_b1_reopen_late_evidence_delta < 0 } set_variable = { name = zg361_b1_post_cutoff_event_sign value = -1 } }
					set_variable = { name = zg361_b1_post_cutoff_event_magnitude value = var:zg361_b1_reopen_late_evidence_magnitude }
					set_variable = { name = zg361_b1_post_cutoff_visible_notice value = 1 }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_available value = 1 }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_id value = var:zg361_b1_reopen_object_id }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_owner value = var:zg361_b1_reopen_object_owner }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_subject value = this }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_cycle value = { value = var:zg361_b1_reopen_object_cycle add = 1 } }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_case value = var:zg361_b1_reopen_object_id }
					set_variable = { name = zg361_b1_reopen_next_cycle_object_state value = 1 }
					set_variable = { name = zg361_b1_reopen_next_cycle_due value = var:zg361_b1_reopen_next_cycle_object_cycle }
					set_variable = { name = zg361_b1_reopen_next_cycle_delta value = { value = var:zg361_b1_reopen_late_evidence_delta max = 2 min = -2 } }
					# A separate terminal projection tuple binds the visible promise to
					# this published subject/cycle.  The business object above remains
					# NEXT_OPEN and is consumed only by next-cycle evidence ingestion.
					set_variable = { name = zg361_b1_reopen_self_b_available value = 1 }
					set_variable = { name = zg361_b1_reopen_self_b_owner value = var:zg361_b1_reopen_object_owner }
					set_variable = { name = zg361_b1_reopen_self_b_subject value = this }
					set_variable = { name = zg361_b1_reopen_self_b_cycle value = var:zg361_b1_reopen_object_cycle }
					set_variable = { name = zg361_b1_reopen_self_b_case value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_reopen_self_b_state value = 2 }
					set_variable = { name = zg361_b1_reopen_self_b_next_cycle_evidence value = 1 }
					set_variable = { name = zg361_b1_reopen_self_b_target_cycle value = var:zg361_b1_reopen_next_cycle_object_cycle }
				}
				}
				change_variable = { name = zg361_b1_reopen_pending_n add = -1 }
				change_variable = { name = zg361_b1_reopen_processed_n add = 1 }
				set_variable = { name = zg361_b1_reopen_callback_consumed value = 1 }
			}
			else_if = {
				# A dead, transferred or otherwise invalid subject still consumes its
				# one open batch object.  This is a cancellation, never a fake review.
				limit = {
					scope:zg361_b1_reopen_ticket_subject = {
						var:zg361_b1_reopen_object_available = 1
						var:zg361_b1_reopen_object_id = scope:zg361_b1_reopen_ticket_object
						var:zg361_b1_reopen_object_owner = scope:zg361_b1_reopen_ticket_owner
						var:zg361_b1_reopen_object_subject = this
						var:zg361_b1_reopen_object_cycle = scope:zg361_b1_reopen_ticket_cycle
						var:zg361_b1_reopen_object_case = scope:zg361_b1_reopen_ticket_case
						var:zg361_b1_reopen_object_state = 1
					}
				}
				scope:zg361_b1_reopen_ticket_subject = {
					set_variable = { name = zg361_b1_reopen_object_state value = 3 }
					set_variable = { name = zg361_b1_reopen_cancel_reason value = 1 }
			}
				change_variable = { name = zg361_b1_reopen_pending_n add = -1 }
				change_variable = { name = zg361_b1_reopen_processed_n add = 1 }
				change_variable = { name = zg361_b1_reopen_cancelled_n add = 1 }
				set_variable = { name = zg361_b1_reopen_callback_consumed value = 1 }
			}
			if = {
				limit = { var:zg361_b1_reopen_callback_consumed = 1 var:zg361_b1_reopen_pending_n = 0 }
				zg361_b1_resolve_reopen_batch_effect = yes
			}
		}
		else = { debug_log = "ZG361B1: stale post-seal batch ticket ignored" }
	}
}

# The last independently scheduled subject returns control to the owning
# manager. No one subject can advance another manager's calibration round.
zg361b1.123 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_pending_continue_owner
				exists = scope:zg361_b1_pending_continue_subject
				this = scope:zg361_b1_pending_continue_owner
				var:zg361_b1_cycle_serial = scope:zg361_b1_pending_continue_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_pending_continue_case
				var:zg361_b1_cycle_state = scope:zg361_b1_pending_continue_state
				var:zg361_b1_cycle_state = 7
				var:zg361_b1_pending_open_n = 0
				scope:zg361_b1_pending_continue_subject = {
					var:zg361_b1_case_owner = scope:zg361_b1_pending_continue_owner
					var:zg361_b1_case_subject = this
					var:zg361_b1_cycle_serial = scope:zg361_b1_pending_continue_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_pending_continue_case
					var:zg361_b1_case_state = 7
					var:zg361_b1_case_active = 1
					var:zg361_b1_roster_included = 1
					OR = { var:zg361_b1_pending_state = 2 var:zg361_b1_pending_state = 3 }
				}
			}
			zg361_b1_prepare_reopen_gate_effect = yes
		}
		else = { debug_log = "ZG361B1: stale pending continuation ticket ignored" }
	}
}

# A true skip-level reviewer returns only the manager-owned procedure.  This
# manager-rooted continuation never enters a subject scope and contains no
# pending/final grade write.
zg361b1.124 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_oversight_ticket_owner
				this = scope:zg361_b1_oversight_ticket_owner
				var:zg361_b1_cycle_serial = scope:zg361_b1_oversight_ticket_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_oversight_ticket_case
				var:zg361_b1_cycle_state = scope:zg361_b1_oversight_ticket_state
				var:zg361_b1_cycle_state = 6
				var:zg361_b1_oversight_return_status = 1
				var:zg361_b1_skip_level_return_count = 1
				var:zg361_b1_publication_blocked = 1
			}
			set_variable = { name = zg361_b1_oversight_return_status value = 2 }
			set_variable = { name = zg361_b1_oversight_reopen_year value = current_year }
			set_variable = { name = zg361_b1_publication_blocked value = 0 }
			set_variable = { name = zg361_b1_cycle_state value = 7 }
			zg361_b1_build_agenda_and_attention_effect = yes
			zg361_b1_consume_must_review_effect = yes
			zg361_b1_record_named_dissent_effect = yes
			zg361_b1_open_pending_slots_effect = yes
		}
		else = { debug_log = "ZG361B1: stale skip-level return ticket ignored" }
	}
}

# Manager-owned D+31 watchdog for #142.  Subject-rooted delayed events may be
# discarded when the subject dies; this independent owner ticket cancels each
# still-open five-tuple exactly once, releases its reserved peer, and advances
# the barrier without pretending an observation occurred.
zg361b1.125 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_pending_watch_owner
				this = scope:zg361_b1_pending_watch_owner
				var:zg361_b1_cycle_serial = scope:zg361_b1_pending_watch_cycle
				var:zg361_b1_case_serial = scope:zg361_b1_pending_watch_case
				var:zg361_b1_cycle_state = scope:zg361_b1_pending_watch_state
				var:zg361_b1_cycle_state = 7
				var:zg361_b1_pending_open_n >= 1
			}
			set_variable = { name = zg361_b1_pending_watchdog_cancelled_n value = 0 }
			every_in_list = {
				variable = zg361_b1_pending_watch_subjects
				limit = {
					var:zg361_b1_pending_object_available = 1
					var:zg361_b1_pending_object_owner = root
					var:zg361_b1_pending_object_subject = this
					var:zg361_b1_pending_object_cycle = scope:zg361_b1_pending_watch_cycle
					var:zg361_b1_pending_object_case = scope:zg361_b1_pending_watch_case
					var:zg361_b1_pending_object_state = 1
					var:zg361_b1_pending_state = 1
				}
				save_temporary_scope_as = zg361_b1_pending_watch_subject
				if = {
					limit = { has_variable = zg361_b1_pending_fallback_subject }
					var:zg361_b1_pending_fallback_subject = {
						if = {
							limit = {
								var:zg361_b1_pending_reservation_state = 1
								var:zg361_b1_pending_reserved_for_subject = scope:zg361_b1_pending_watch_subject
							}
							set_variable = { name = zg361_b1_pending_reservation_state value = 4 }
							remove_variable = zg361_b1_pending_reserved_for_subject
						}
					}
				}
				set_variable = { name = zg361_b1_pending_object_state value = 5 }
				set_variable = { name = zg361_b1_pending_state value = 5 }
				set_variable = { name = zg361_b1_pending_cancel_reason value = 1 }
				set_variable = { name = zg361_b1_pending_observation_recorded value = 0 }
				root = {
					change_variable = { name = zg361_b1_pending_open_n add = -1 }
					change_variable = { name = zg361_b1_pending_watchdog_cancelled_n add = 1 }
					change_variable = { name = zg361_b1_pending_fallback_middle_available add = 1 }
				}
			}
			if = {
				limit = { var:zg361_b1_pending_open_n > 0 }
				set_variable = { name = zg361_b1_pending_watchdog_orphan_n value = var:zg361_b1_pending_open_n }
				set_variable = { name = zg361_b1_pending_open_n value = 0 }
			}
			zg361_b1_prepare_reopen_gate_effect = yes
		}
		else = { debug_log = "ZG361B1: stale pending watchdog ticket ignored" }
	}
}
''')


def render_english_localization() -> bytes:
    return localized(r'''
l_english:
 zg361b1.200.t:0 "Sealed Self-Review"
 zg361b1.200.desc:0 "The evidence window is closing. Your statement will be sealed beside the mid-cycle record. It may explain visibility, but it cannot rewrite the hard facts."
 zg361b1.200.a:0 "State the record as it stands."
 zg361b1.200.b:0 "Present the strongest possible account."
 zg361b1.200.c:0 "Understate my own contribution."
 zg361b1.201.t:0 "Non-Final Shadow Grade"
 zg361b1.201.desc:0 "Your manager has opened a non-final shadow band code of #high [ROOT.MakeScope.Var('zg361_b1_shadow_grade').GetValue|0]#!. Frozen gap magnitude: [ROOT.MakeScope.Var('zg361_b1_shadow_gap_magnitude').GetValue|0]; response window: [ROOT.MakeScope.Var('zg361_b1_shadow_deadline_days').GetValue|0] days. It grants no reward and occupies no final quota yet. You may accept it or submit one bounded, non-zero evidence packet; the frozen KPI will not change."
 zg361b1.201.a:0 "Accept the shadow record."
 zg361b1.201.b:0 "Submit supplementary evidence."
 zg361_scoreboard_detail_field_self_choice:0 "Self-Review Choice Code (1 Honest / 2 Exaggerated / 3 Conservative)"
 zg361_scoreboard_detail_field_self_score:0 "Self-Review Score"
 zg361_scoreboard_detail_field_self_gap:0 "Self-to-Facts Gap"
 zg361_scoreboard_detail_field_self_submitted_year:0 "Self-Review Submission Year"
 zg361_scoreboard_detail_field_shadow_grade:0 "Pre-Quota Shadow Rating"
 zg361_scoreboard_detail_field_shadow_response:0 "Shadow Response Code (1 Accept / 2 Supplement)"
 zg361_scoreboard_detail_field_shadow_delta:0 "Supplementary Calibration Delta"
 zg361_scoreboard_detail_field_shadow_response_year:0 "Shadow Response Year"
 zg361_scoreboard_detail_field_peer_n:0 "Sealed Peer Review Count"
 zg361_scoreboard_detail_field_peer_mean:0 "Peer Raw Mean"
 zg361_scoreboard_detail_field_peer_variance:0 "Peer Score Variance"
 zg361_scoreboard_detail_field_peer_normalized_score:0 "Credit-Weighted Peer Score"
 zg361_scoreboard_detail_field_peer_shape:0 "Peer Distribution Shape Code"
 zg361_scoreboard_detail_field_peer_reciprocity_risk:0 "Positive Reciprocity Risk"
 zg361_scoreboard_detail_field_peer_timely_n:0 "Timely Peer Review Count"
 zg361_scoreboard_detail_field_peer_credit_total:0 "Aggregate Peer Credit Weight"
 zg361_scoreboard_detail_field_evaluator_credit:0 "Cross-Cycle Evaluator Credit"
 zg361_scoreboard_detail_field_evaluator_sample_n:0 "Cross-Cycle Evaluation Sample Count"
 zg361_scoreboard_detail_field_peer_use_mode:0 "Peer Evidence Use Mode Code"
 zg361_scoreboard_detail_field_peer_fatigue:0 "Peer Submission Fatigue"
 zg361_scoreboard_detail_field_calibration_score:0 "Post-Shadow Calibration Score"
 zg361_scoreboard_detail_field_calibration_score_before_shadow:0 "Calibration Score Before Shadow Response"
 zg361_scoreboard_detail_field_shadow_to_quota_delta:0 "Shadow-to-Quota Rating Delta"
 zg361_scoreboard_detail_field_quota_snapshot:0 "Frozen Quota Rating"
 zg361_scoreboard_detail_field_forced_down:0 "Forced Below Absolute Band"
 zg361_scoreboard_detail_field_b1_case_owner:0 "B1 Case Owner"
 zg361_scoreboard_detail_field_b1_cycle_serial:0 "B1 Cycle Serial"
 zg361_scoreboard_detail_field_b1_case_serial:0 "B1 Case Serial"
 zg361_scoreboard_detail_field_b1_case_state:0 "B1 Case State Code"
 zg361_scoreboard_detail_field_b1_fact_sheet_serial:0 "B1 Fact Sheet Serial"
 zg361_scoreboard_detail_field_b1_peer_sealed:0 "B1 Peer Evidence Sealed"
 zg361_scoreboard_detail_field_b1_self_receipt_serial:0 "B1 Self-Review Receipt Serial"
 zg361_scoreboard_detail_field_b1_peer_receipt_serial:0 "B1 Peer-Seal Receipt Serial"
 zg361_scoreboard_detail_field_b1_shadow_receipt_serial:0 "B1 Shadow-Open Receipt Serial"
 zg361_scoreboard_detail_field_b1_band_receipt_serial:0 "B1 Band-Order Receipt Serial"
 zg361_scoreboard_detail_field_b1_141_must_review_marker:0 "#141 Superior Review Required"
 zg361_scoreboard_detail_field_b1_141_agenda_reason:0 "#141 Frozen Agenda Reason"
 zg361_scoreboard_detail_field_b1_141_review_outcome:0 "#141 Review Outcome (1 Aligned / 2 Diverged)"
 zg361_scoreboard_detail_field_b1_142_pending_marker:0 "#142 Pending Review Marker"
 zg361_scoreboard_detail_field_b1_142_milestone:0 "#142 Pending Milestone"
 zg361_scoreboard_detail_field_b1_142_deadline_cycle:0 "#142 Pending Deadline Cycle"
 zg361_scoreboard_detail_field_b1_142_current_final_unchanged:0 "#142 Current Result Unchanged"
 zg361_scoreboard_detail_field_b1_142_next_cycle_evidence:0 "#142 Evidence Queued for Next Cycle"
 zg361_scoreboard_detail_field_b1_143_reopen_result:0 "#143 Reopen Result (1 Self / 2 None / 3 Another)"
 zg361_scoreboard_detail_field_b1_143_reason_code:0 "#143 Reopen Reason Code"
 zg361_scoreboard_detail_field_b1_143_next_cycle_evidence:0 "#143 Evidence Queued for Next Cycle"
 zg361_scoreboard_detail_field_b1_143_target_cycle:0 "#143 Evidence Target Cycle"
 zg361_scoreboard_detail_field_b1_144_dissent_marker:0 "#144 Named Dissent Recorded"
 zg361_scoreboard_detail_field_b1_144_fact_reason:0 "#144 Dissent Fact Reason"
 zg361_scoreboard_detail_field_b1_144_review_outcome:0 "#144 Dissent Review Outcome"
 zg361_scoreboard_detail_field_b1_144_consensus_marker:0 "#144 Consensus Sealed"
 zg361_scoreboard_detail_field_b1_145_formal_band:0 "#145 Formal Rating Band"
 zg361_scoreboard_detail_field_b1_145_within_middle_order:0 "#145 Position Within Middle Band"
 zg361_scoreboard_detail_field_b1_145_opportunity_capacity:0 "#145 Opportunity Capacity"
 zg361_scoreboard_detail_field_b1_145_opportunity_selected:0 "#145 Opportunity Selected"
 zg361_scoreboard_detail_field_b1_145_coaching_selected:0 "#145 Coaching Selected"
 zg361_scoreboard_detail_field_b1_145_own_opportunity_selected:0 "#145 Own Opportunity Selected"
 zg361_scoreboard_detail_field_b1_145_appeal_evidence_available:0 "#145 Appeal Evidence Available"
 zg361_scoreboard_detail_field_b1_145_blackbox_audit:0 "#145 Black-Box Audit Marker"
''')


def render_simp_chinese_localization() -> bytes:
    return localized(r'''
l_simp_chinese:
 zg361b1.200.t:0 "封存自评"
 zg361b1.200.desc:0 "证据窗口将闭。你的陈述会与期中记录一同封存：它可以说明成果为何未被看见，却不能改写已经发生的硬事实。"
 zg361b1.200.a:0 "据实陈述，不增不减。"
 zg361b1.200.b:0 "把最耀眼的一面写进案卷。"
 zg361b1.200.c:0 "收敛锋芒，保守自陈。"
 zg361b1.201.t:0 "非最终影子档"
 zg361b1.201.desc:0 "直属上司给出的非最终影子档代码是 #high [ROOT.MakeScope.Var('zg361_b1_shadow_grade').GetValue|0]#!；冻结差距幅度为 [ROOT.MakeScope.Var('zg361_b1_shadow_gap_magnitude').GetValue|0]，回应窗口为 [ROOT.MakeScope.Var('zg361_b1_shadow_deadline_days').GetValue|0] 天。此档尚不发放奖惩，也不占用最终配额。你可以接受，或补交一份有界且非零的新证据；已经封存的事实 KPI 不会改变。"
 zg361b1.201.a:0 "接受这份影子记录。"
 zg361b1.201.b:0 "补交证据，交由校准复核。"
 zg361_scoreboard_detail_field_self_choice:0 "自评选择码（1 诚实 / 2 夸大 / 3 保守）"
 zg361_scoreboard_detail_field_self_score:0 "自评分"
 zg361_scoreboard_detail_field_self_gap:0 "自评与事实差"
 zg361_scoreboard_detail_field_self_submitted_year:0 "自评提交年份"
 zg361_scoreboard_detail_field_shadow_grade:0 "配额前影子档"
 zg361_scoreboard_detail_field_shadow_response:0 "影子档反馈码（1 接受 / 2 补证）"
 zg361_scoreboard_detail_field_shadow_delta:0 "补证校准增量"
 zg361_scoreboard_detail_field_shadow_response_year:0 "影子档反馈年份"
 zg361_scoreboard_detail_field_peer_n:0 "封存互评数"
 zg361_scoreboard_detail_field_peer_mean:0 "互评原始均值"
 zg361_scoreboard_detail_field_peer_variance:0 "互评分方差"
 zg361_scoreboard_detail_field_peer_normalized_score:0 "按信用加权互评分"
 zg361_scoreboard_detail_field_peer_shape:0 "互评分布形态码"
 zg361_scoreboard_detail_field_peer_reciprocity_risk:0 "正向互惠风险"
 zg361_scoreboard_detail_field_peer_timely_n:0 "按时互评数"
 zg361_scoreboard_detail_field_peer_credit_total:0 "互评信用权重合计"
 zg361_scoreboard_detail_field_evaluator_credit:0 "跨周期评价者信用"
 zg361_scoreboard_detail_field_evaluator_sample_n:0 "跨周期评价样本数"
 zg361_scoreboard_detail_field_peer_use_mode:0 "互评证据使用模式码"
 zg361_scoreboard_detail_field_peer_fatigue:0 "互评提交疲劳"
 zg361_scoreboard_detail_field_calibration_score:0 "影子档反馈后校准分"
 zg361_scoreboard_detail_field_calibration_score_before_shadow:0 "影子档反馈前校准分"
 zg361_scoreboard_detail_field_shadow_to_quota_delta:0 "影子档到配额档变化"
 zg361_scoreboard_detail_field_quota_snapshot:0 "冻结配额档"
 zg361_scoreboard_detail_field_forced_down:0 "是否被压低至事实绝对档以下"
 zg361_scoreboard_detail_field_b1_case_owner:0 "B1 案卷所有者"
 zg361_scoreboard_detail_field_b1_cycle_serial:0 "B1 轮次序号"
 zg361_scoreboard_detail_field_b1_case_serial:0 "B1 案卷序号"
 zg361_scoreboard_detail_field_b1_case_state:0 "B1 案卷状态码"
 zg361_scoreboard_detail_field_b1_fact_sheet_serial:0 "B1 事实表序号"
 zg361_scoreboard_detail_field_b1_peer_sealed:0 "B1 互评证据是否封存"
 zg361_scoreboard_detail_field_b1_self_receipt_serial:0 "B1 自评收据序号"
 zg361_scoreboard_detail_field_b1_peer_receipt_serial:0 "B1 互评封存收据序号"
 zg361_scoreboard_detail_field_b1_shadow_receipt_serial:0 "B1 影子档开启收据序号"
 zg361_scoreboard_detail_field_b1_band_receipt_serial:0 "B1 排档收据序号"
 zg361_scoreboard_detail_field_b1_141_must_review_marker:0 "#141 上级复核必经项"
 zg361_scoreboard_detail_field_b1_141_agenda_reason:0 "#141 冻结议题理由"
 zg361_scoreboard_detail_field_b1_141_review_outcome:0 "#141 复核结果（1 一致 / 2 分歧）"
 zg361_scoreboard_detail_field_b1_142_pending_marker:0 "#142 待定评审标记"
 zg361_scoreboard_detail_field_b1_142_milestone:0 "#142 待定里程碑"
 zg361_scoreboard_detail_field_b1_142_deadline_cycle:0 "#142 待定截止轮次"
 zg361_scoreboard_detail_field_b1_142_current_final_unchanged:0 "#142 本轮终评未改动"
 zg361_scoreboard_detail_field_b1_142_next_cycle_evidence:0 "#142 证据已排入下轮"
 zg361_scoreboard_detail_field_b1_143_reopen_result:0 "#143 重开结果（1 本人 / 2 无人 / 3 他人）"
 zg361_scoreboard_detail_field_b1_143_reason_code:0 "#143 重开理由码"
 zg361_scoreboard_detail_field_b1_143_next_cycle_evidence:0 "#143 证据已排入下轮"
 zg361_scoreboard_detail_field_b1_143_target_cycle:0 "#143 证据目标轮次"
 zg361_scoreboard_detail_field_b1_144_dissent_marker:0 "#144 具名异议已记录"
 zg361_scoreboard_detail_field_b1_144_fact_reason:0 "#144 异议事实理由"
 zg361_scoreboard_detail_field_b1_144_review_outcome:0 "#144 异议复核结果"
 zg361_scoreboard_detail_field_b1_144_consensus_marker:0 "#144 共识已封存"
 zg361_scoreboard_detail_field_b1_145_formal_band:0 "#145 正式绩效档位"
 zg361_scoreboard_detail_field_b1_145_within_middle_order:0 "#145 中档内部次序"
 zg361_scoreboard_detail_field_b1_145_opportunity_capacity:0 "#145 机会名额"
 zg361_scoreboard_detail_field_b1_145_opportunity_selected:0 "#145 已获机会名额"
 zg361_scoreboard_detail_field_b1_145_coaching_selected:0 "#145 已入辅导名单"
 zg361_scoreboard_detail_field_b1_145_own_opportunity_selected:0 "#145 本人是否获机会"
 zg361_scoreboard_detail_field_b1_145_appeal_evidence_available:0 "#145 申诉证据可用"
 zg361_scoreboard_detail_field_b1_145_blackbox_audit:0 "#145 黑箱审计标记"
''')


def render_english_placeholder_localization(language: str) -> bytes:
    english = render_english_localization().decode("utf-8-sig")
    return localized(english.replace("l_english:", f"l_{language}:", 1))


def outputs() -> dict[Path, bytes]:
    validate_b1_bindings()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_b1_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_b1_runtime_events.txt": render_events(),
        MOD_ROOT / "localization" / "english" / "zg361_b1_l_english.yml": render_english_localization(),
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_b1_l_simp_chinese.yml": render_simp_chinese_localization(),
    }
    for language in (
        "french",
        "german",
        "japanese",
        "korean",
        "polish",
        "russian",
        "spanish",
    ):
        rendered[
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_b1_l_{language}.yml"
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
            print("RED: stale B1 generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: B1 generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} B1 runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
