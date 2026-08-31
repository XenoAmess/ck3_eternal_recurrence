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

# These are insertion contracts, not generator-owned files.  The shared KPI
# and rank effects are intentionally left to their current owners; tests pin
# each unique anchor so the package can be merged without inventing a ninth
# KPI component or silently replacing another package's dirty work.
SHARED_HOOK_CONTRACT: dict[str, tuple[str, str]] = {
    "organization_component": (
        "common/script_values/zg361_values.txt",
        "zg361_kpi_organization_evidence_value",
    ),
    "organization_settlement": (
        "common/scripted_effects/zg361_effects.txt",
        "zg361_b2_consume_management_debt_effect = yes",
    ),
    "distribution_settlement": (
        "common/scripted_effects/zg361_effects.txt",
        "set_variable = { name = zg361_bottom_slots value = zg361_bottom_slots_value }",
    ),
}

# One canonical due guard is injected byte-for-byte into the component-8 value
# and its post-write settler.  Active B1 advances b1_cycle_serial before KPI
# computation while legacy/no-B1 advances review_serial after computation.
ORGANIZATION_DUE_GUARD = """\t\t\thas_variable = zg361_mg_organization_input_source_cycle
\t\t\thas_variable = zg361_mg_organization_input_due_cycle
\t\t\tvar:zg361_mg_organization_input_due_cycle = { value = var:zg361_mg_organization_input_source_cycle add = 1 }
\t\t\tOR = {
\t\t\t\tAND = {
\t\t\t\t\thas_variable = zg361_b1_cycle_serial
\t\t\t\t\tvar:zg361_b1_cycle_serial >= var:zg361_mg_organization_input_due_cycle
\t\t\t\t}
\t\t\t\tAND = {
\t\t\t\t\tNOT = { has_variable = zg361_b1_cycle_serial }
\t\t\t\t\thas_variable = zg361_review_serial
\t\t\t\t\tvar:zg361_review_serial >= var:zg361_mg_organization_input_source_cycle
\t\t\t\t}
\t\t\t}"""

DISTRIBUTION_DUE_GUARD = """\t\t\thas_variable = zg361_mg_distribution_policy_source_cycle
\t\t\thas_variable = zg361_mg_distribution_policy_due_cycle
\t\t\tvar:zg361_mg_distribution_policy_due_cycle = { value = var:zg361_mg_distribution_policy_source_cycle add = 1 }
\t\t\tOR = {
\t\t\t\tAND = {
\t\t\t\t\thas_variable = zg361_b1_cycle_serial
\t\t\t\t\tvar:zg361_b1_cycle_serial >= var:zg361_mg_distribution_policy_due_cycle
\t\t\t\t}
\t\t\t\tAND = {
\t\t\t\t\tNOT = { has_variable = zg361_b1_cycle_serial }
\t\t\t\t\thas_variable = zg361_review_serial
\t\t\t\t\tvar:zg361_review_serial >= var:zg361_mg_distribution_policy_source_cycle
\t\t\t\t}
\t\t\t}"""


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
Q_PROJECTION_IDS = tuple(range(121, 129))
COLLECTIVE_COST_ORDINALS = (1, 2, 3)

# Numeric facts that can change the business result of one manager/governance
# operation.  The generated CK3 adapter folds presence + value into a frozen
# scalar fingerprint.  Resource balances that the operation itself mutates are
# deliberately excluded: their reserve/settle receipts are the authority.
INPUT_FINGERPRINT_VARS: dict[int, tuple[str, ...]] = {
    32: (
        "zg361_mg_snapshot_source_serial",
        "zg361_mg_team_snapshot_revision",
        "zg361_mg_team_targets",
        "zg361_mg_team_jingcha",
        "zg361_mg_team_calibration",
        "zg361_mg_team_pip_success",
        "zg361_mg_team_appeal_overturn",
        "zg361_mg_team_retention",
        "zg361_mg_team_hc_efficiency",
        "zg361_mg_refusal_match",
    ),
    33: (
        "zg361_mg_manager_score",
        "zg361_mg_team_targets",
        "zg361_mg_team_calibration",
        "zg361_mg_team_pip_success",
        "zg361_mg_team_appeal_overturn",
        "zg361_mg_team_hc_efficiency",
    ),
    34: (
        "zg361_mg_manager_score",
        "zg361_mg_previous_manager_score",
        "zg361_mg_previous_manager_score_serial",
        "zg361_result_kpi_frozen",
        "zg361_result_cycle_serial",
        "zg361_result_evidence_growth",
        "zg361_result_evidence_capability",
    ),
    35: (
        "zg361_mg_snapshot_source_serial",
        "zg361_mg_snapshot_current_serial",
        "zg361_mg_team_n",
        "zg361_mg_team_bottom_n",
        "zg361_ratio_override",
    ),
    36: (
        "zg361_mg_team_top_n",
        "zg361_mg_team_middle_n",
        "zg361_mg_team_bottom_n",
        "zg361_mg_team_appeal_overturn",
        "zg361_mg_team_pip_success",
        "zg361_mg_team_hc_efficiency",
        "zg361_mg_manager_score",
        "zg361_mg_reason_total",
        "zg361_mg_nine_box_code",
    ),
    345: (),
    346: (
        "zg361_mg_offcycle_pending",
        "zg361_mg_offcycle_input_status",
        "zg361_mg_offcycle_input_revision",
        "zg361_mg_offcycle_source_cycle",
        "zg361_mg_offcycle_source_case",
        "zg361_mg_offcycle_materiality",
        "zg361_mg_offcycle_signal_serial",
        "zg361_mg_offcycle_action",
        "zg361_mg_offcycle_recorded_year",
    ),
    347: (
        "zg361_mg_team_n",
        "zg361_mg_override_pending",
        "zg361_mg_override_input_status",
        "zg361_mg_override_input_revision",
        "zg361_mg_override_source_cycle",
        "zg361_mg_override_source_beneficiary_case",
        "zg361_mg_override_source_bearer_case",
        "zg361_mg_override_pending_reason",
    ),
    348: (),
    349: ("zg361_mg_team_n", "zg361_mg_team_bottom_n"),
    350: (
        "zg361_mg_manager_score",
        "zg361_mg_team_top_n",
        "zg361_mg_team_n",
        "zg361_mg_calendar_effective_cycle",
    ),
    351: ("zg361_mg_team_n",),
    352: (
        "zg361_mg_benchmark_history_score_available",
        "zg361_mg_benchmark_history_value",
        "zg361_mg_benchmark_history_formula",
        "zg361_mg_benchmark_history_version",
        "zg361_mg_benchmark_new_version",
        "zg361_mg_benchmark_top_threshold",
    ),
    353: (
        "zg361_mg_team_n",
        "zg361_mg_team_appeal_overturn",
        "zg361_mg_team_calibration",
        "zg361_mg_calendar_final_n",
        "zg361_mg_offcycle_consumed",
    ),
    354: (
        "zg361_mg_fairness_input_status",
        "zg361_mg_fairness_input_revision",
        "zg361_mg_fairness_input_source_cycle",
        "zg361_mg_fairness_input_source_case",
        "zg361_mg_fairness_input_delivered",
        "zg361_mg_fairness_input_appeals",
        "zg361_mg_fairness_input_overturns",
        "zg361_mg_fairness_input_exits",
        "zg361_mg_fairness_input_healthy_exits",
        "zg361_mg_history_mapping_version",
        "zg361_mg_fairness_remediation_status",
        "zg361_mg_fairness_remediation_revision",
        "zg361_mg_fairness_remediation_plan_id",
    ),
}

# Some inputs are opaque character references.  Their producer-owned numeric
# revision is folded above; the opaque scope itself contributes a presence bit.
# Raw values can be folded directly.
INPUT_FINGERPRINT_OPAQUE_VARS: dict[int, tuple[str, ...]] = {
    mechanism_id: () for mechanism_id in TARGET_IDS
}
INPUT_FINGERPRINT_OPAQUE_VARS[347] = (
    "zg361_mg_override_source_owner",
    "zg361_mg_override_source_subject",
    "zg361_mg_override_pending_beneficiary",
    "zg361_mg_override_pending_bearer",
)
INPUT_FINGERPRINT_OPAQUE_VARS[346] = (
    "zg361_mg_offcycle_source_owner",
    "zg361_mg_offcycle_source_subject",
)
INPUT_FINGERPRINT_OPAQUE_VARS[354] = (
    "zg361_mg_fairness_input_source_owner",
    "zg361_mg_fairness_input_source_subject",
    "zg361_mg_fairness_remediation_owner",
    "zg361_mg_fairness_remediation_subject",
)
INPUT_FINGERPRINT_RAW_VALUES: dict[int, tuple[str, ...]] = {
    mechanism_id: () for mechanism_id in TARGET_IDS
}
INPUT_FINGERPRINT_RAW_VALUES[35] = (
    "zg361_mg_distribution_source_mode_value",
    "zg361_mg_distribution_source_kind_value",
)
INPUT_FINGERPRINT_RAW_VALUES[36] = ("current_year",)
INPUT_FINGERPRINT_RAW_VALUES[348] = ("current_year",)

# A C route intentionally makes the upstream product unavailable.  These
# guards keep an old A/B value from a previous case out of both the downstream
# calculation and its requested-input fingerprint.
INPUT_FINGERPRINT_GUARDS: dict[tuple[int, str], str] = {
    (33, "zg361_mg_manager_score"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_mg_manager_score"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_mg_previous_manager_score"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_mg_previous_manager_score_serial"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_result_kpi_frozen"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_result_cycle_serial"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_result_evidence_growth"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (34, "zg361_result_evidence_capability"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (36, "zg361_mg_manager_score"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (36, "zg361_mg_reason_total"): "has_variable = zg361_mg_m033_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m033_receipt_choice = 3 }",
    (36, "zg361_mg_nine_box_code"): "has_variable = zg361_mg_m034_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m034_receipt_choice = 3 }",
    (350, "zg361_mg_manager_score"): "has_variable = zg361_mg_m032_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m032_receipt_choice = 3 }",
    (350, "zg361_mg_calendar_effective_cycle"): "has_variable = zg361_mg_m345_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m345_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_history_value"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_history_score_available"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_history_formula"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_history_version"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_new_version"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (352, "zg361_mg_benchmark_top_threshold"): "has_variable = zg361_mg_m350_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m350_receipt_choice = 3 }",
    (353, "zg361_mg_calendar_final_n"): "has_variable = zg361_mg_m345_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m345_receipt_choice = 3 }",
    (353, "zg361_mg_offcycle_consumed"): "has_variable = zg361_mg_m346_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m346_receipt_choice = 3 }",
    (354, "zg361_mg_history_mapping_version"): "has_variable = zg361_mg_m352_receipt_choice\n\t\t\tNOT = { var:zg361_mg_m352_receipt_choice = 3 }",
}


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
    if Q_PROJECTION_IDS != tuple(range(121, 129)):
        raise ValueError("manager-certification projection coverage drift")
    if COLLECTIVE_COST_ORDINALS != (1, 2, 3):
        raise ValueError("collective-cost cohort coverage drift")
    if set(INPUT_FINGERPRINT_VARS) != set(TARGET_IDS):
        raise ValueError("manager input-fingerprint coverage drift")
    if set(INPUT_FINGERPRINT_OPAQUE_VARS) != set(TARGET_IDS):
        raise ValueError("manager opaque input-fingerprint coverage drift")
    if set(INPUT_FINGERPRINT_RAW_VALUES) != set(TARGET_IDS):
        raise ValueError("manager raw input-fingerprint coverage drift")
    if set(SHARED_HOOK_CONTRACT) != {
        "organization_component",
        "organization_settlement",
        "distribution_settlement",
    }:
        raise ValueError("manager shared-hook contract coverage drift")
    known_fields = {
        (mechanism_id, variable)
        for mechanism_id, variables in INPUT_FINGERPRINT_VARS.items()
        for variable in variables
    }
    if not set(INPUT_FINGERPRINT_GUARDS) <= known_fields:
        raise ValueError("input-fingerprint guard names an unknown field")


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
			CHOICE = var:zg361_mg_m{mechanism_id:03d}_route
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
			EXPECTED_CHOICE = var:zg361_mg_m{mechanism_id:03d}_route
		}}"""


def receipt_not_current(domain: str, mechanism_id: int, state: int) -> str:
    return (
        f"NOT = {{ has_variable = zg361_mg_m{mechanism_id:03d}_replay_route_conflict }}\n\t\t"
        + "NOT = {\n\t\t\t"
        + receipt_current(domain, mechanism_id, state).replace("\n", "\n\t\t\t")
        + "\n\t\t}"
    )


def input_fingerprint_prelude(mechanism_id: int) -> str:
    """Render a deterministic CK3 checksum of the operation's requested facts."""

    stem = f"zg361_mg_m{mechanism_id:03d}"
    lines = [
        f"set_variable = {{ name = {stem}_requested_input_fingerprint value = {mechanism_id * 1009} }}",
    ]
    ordinal = 0
    for variable in INPUT_FINGERPRINT_VARS[mechanism_id]:
        ordinal += 1
        presence_code = 1000 + ordinal * 37
        value_coefficient = 101 + ordinal * 53
        guard = INPUT_FINGERPRINT_GUARDS.get((mechanism_id, variable))
        guard_text = ""
        if guard:
            guard_text = "\n\t\t" + guard.replace("\n", "\n\t\t")
        lines.extend(
            (
                "if = {",
                f"\tlimit = {{\n\t\thas_variable = {variable}{guard_text}\n\t}}",
                f"\tchange_variable = {{ name = {stem}_requested_input_fingerprint add = {presence_code} }}",
                f"\tchange_variable = {{ name = {stem}_requested_input_fingerprint add = {{ value = var:{variable} multiply = {value_coefficient} }} }}",
                "}",
            )
        )
    for raw_value in INPUT_FINGERPRINT_RAW_VALUES[mechanism_id]:
        ordinal += 1
        value_coefficient = 101 + ordinal * 53
        lines.append(
            f"change_variable = {{ name = {stem}_requested_input_fingerprint add = {{ value = {raw_value} multiply = {value_coefficient} }} }}"
        )
    for variable in INPUT_FINGERPRINT_OPAQUE_VARS[mechanism_id]:
        ordinal += 1
        presence_code = 1000 + ordinal * 37
        lines.extend(
            (
                "if = {",
                f"\tlimit = {{ has_variable = {variable} }}",
                f"\tchange_variable = {{ name = {stem}_requested_input_fingerprint add = {presence_code} }}",
                "}",
            )
        )
    return "\n\t".join(lines)


def route_prelude(domain: str, mechanism_id: int) -> str:
    """Freeze an A/B/C route to the exact case identity before any mutation."""

    prefix = domain.lower()
    return f"""remove_variable = zg361_mg_m{mechanism_id:03d}_replay_route_conflict
	set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_requested_route value = 1 }}
	if = {{
		limit = {{ has_variable = zg361_mechanism_{mechanism_id:03d}_choice }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_requested_route value = var:zg361_mechanism_{mechanism_id:03d}_choice }}
	}}
	if = {{
		limit = {{ OR = {{ var:zg361_mg_m{mechanism_id:03d}_requested_route < 1 var:zg361_mg_m{mechanism_id:03d}_requested_route > 3 }} }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_requested_route value = 1 }}
	}}
	{input_fingerprint_prelude(mechanism_id)}
	if = {{
		limit = {{
			has_variable = zg361_mg_m{mechanism_id:03d}_route
			has_variable = zg361_mg_m{mechanism_id:03d}_route_cycle
			has_variable = zg361_mg_m{mechanism_id:03d}_route_case
			OR = {{
				var:zg361_case_{prefix}_cycle_serial < var:zg361_mg_m{mechanism_id:03d}_route_cycle
				AND = {{
					var:zg361_case_{prefix}_cycle_serial = var:zg361_mg_m{mechanism_id:03d}_route_cycle
					var:zg361_case_{prefix}_case_serial < var:zg361_mg_m{mechanism_id:03d}_route_case
				}}
				AND = {{
					var:zg361_case_{prefix}_cycle_serial = var:zg361_mg_m{mechanism_id:03d}_route_cycle
					var:zg361_case_{prefix}_case_serial = var:zg361_mg_m{mechanism_id:03d}_route_case
					NOT = {{ var:zg361_case_{prefix}_owner = var:zg361_mg_m{mechanism_id:03d}_route_owner }}
				}}
			}}
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_replay_route_conflict value = 1 }}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {mechanism_id} }}
	}}
	if = {{
		limit = {{
			NOT = {{ has_variable = zg361_mg_m{mechanism_id:03d}_replay_route_conflict }}
			OR = {{
				NOT = {{ has_variable = zg361_mg_m{mechanism_id:03d}_route }}
				NOT = {{ var:zg361_mg_m{mechanism_id:03d}_route_owner = var:zg361_case_{prefix}_owner }}
				NOT = {{ var:zg361_mg_m{mechanism_id:03d}_route_subject = this }}
				NOT = {{ var:zg361_mg_m{mechanism_id:03d}_route_cycle = var:zg361_case_{prefix}_cycle_serial }}
				NOT = {{ var:zg361_mg_m{mechanism_id:03d}_route_case = var:zg361_case_{prefix}_case_serial }}
			}}
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_route value = var:zg361_mg_m{mechanism_id:03d}_requested_route }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_route_owner value = var:zg361_case_{prefix}_owner }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_route_subject value = this }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_route_cycle value = var:zg361_case_{prefix}_cycle_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_route_case value = var:zg361_case_{prefix}_case_serial }}
	}}
	if = {{
		limit = {{
			var:zg361_mg_m{mechanism_id:03d}_route_owner = var:zg361_case_{prefix}_owner
			var:zg361_mg_m{mechanism_id:03d}_route_subject = this
			var:zg361_mg_m{mechanism_id:03d}_route_cycle = var:zg361_case_{prefix}_cycle_serial
			var:zg361_mg_m{mechanism_id:03d}_route_case = var:zg361_case_{prefix}_case_serial
			NOT = {{ var:zg361_mg_m{mechanism_id:03d}_requested_route = var:zg361_mg_m{mechanism_id:03d}_route }}
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_replay_route_conflict value = 1 }}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {mechanism_id} }}
	}}
	if = {{
		limit = {{
			NOT = {{ has_variable = zg361_mg_m{mechanism_id:03d}_replay_route_conflict }}
			var:zg361_mg_m{mechanism_id:03d}_route_owner = var:zg361_case_{prefix}_owner
			var:zg361_mg_m{mechanism_id:03d}_route_subject = this
			var:zg361_mg_m{mechanism_id:03d}_route_cycle = var:zg361_case_{prefix}_cycle_serial
			var:zg361_mg_m{mechanism_id:03d}_route_case = var:zg361_case_{prefix}_case_serial
			OR = {{
				AND = {{
					var:zg361_mg_m{mechanism_id:03d}_route = 3
					has_variable = zg361_mg_m{mechanism_id:03d}_debt_input_fingerprint
					var:zg361_mg_m{mechanism_id:03d}_debt_owner = var:zg361_case_{prefix}_owner
					var:zg361_mg_m{mechanism_id:03d}_debt_subject = this
					var:zg361_mg_m{mechanism_id:03d}_debt_cycle = var:zg361_case_{prefix}_cycle_serial
					var:zg361_mg_m{mechanism_id:03d}_debt_case = var:zg361_case_{prefix}_case_serial
					NOT = {{ var:zg361_mg_m{mechanism_id:03d}_requested_input_fingerprint = var:zg361_mg_m{mechanism_id:03d}_debt_input_fingerprint }}
				}}
				AND = {{
					NOT = {{ var:zg361_mg_m{mechanism_id:03d}_route = 3 }}
					has_variable = zg361_mg_m{mechanism_id:03d}_object_input_fingerprint
					var:zg361_mg_m{mechanism_id:03d}_object_owner = var:zg361_case_{prefix}_owner
					var:zg361_mg_m{mechanism_id:03d}_object_subject = this
					var:zg361_mg_m{mechanism_id:03d}_object_cycle = var:zg361_case_{prefix}_cycle_serial
					var:zg361_mg_m{mechanism_id:03d}_object_case = var:zg361_case_{prefix}_case_serial
					NOT = {{ var:zg361_mg_m{mechanism_id:03d}_requested_input_fingerprint = var:zg361_mg_m{mechanism_id:03d}_object_input_fingerprint }}
				}}
			}}
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_replay_route_conflict value = 1 }}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {mechanism_id} }}
	}}"""


def c_route_receipt(domain: str, mechanism_id: int, state: int) -> str:
    """C route: no domain object, one debt + next-cycle review + receipt."""

    prefix = domain.lower()
    return f"""if = {{
		limit = {{
			var:zg361_mg_m{mechanism_id:03d}_route = 3
			var:zg361_case_{prefix}_state = {state}
			var:zg361_case_{prefix}_active = 1
			var:zg361_case_{prefix}_subject = this
			{receipt_not_current(domain, mechanism_id, state)}
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_policy_debt value = 1 }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_status value = 1 }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_owner value = var:zg361_case_{prefix}_owner }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_subject value = this }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_cycle value = var:zg361_case_{prefix}_cycle_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_case value = var:zg361_case_{prefix}_case_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_state value = var:zg361_case_{prefix}_state }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_revision value = var:zg361_case_{prefix}_revision }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_input_fingerprint value = var:zg361_mg_m{mechanism_id:03d}_requested_input_fingerprint }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_next_review_serial value = {{ value = var:zg361_case_{prefix}_cycle_serial add = 1 }} }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_business_object_created value = 0 }}
		{receipt_call(domain, mechanism_id, state)}
	}}"""


def f_c_route_followup(mechanism_id: int, state: int, event_id: int | None) -> str:
    """Advance a completed F route-C receipt through the normal case chain."""

    deferred_projection = ""
    if mechanism_id == 36:
        deferred_projection = """\t\tset_variable = { name = zg361_mg_report_manager_score value = 0 }
		set_variable = { name = zg361_mg_report_reason_total value = 0 }
		set_variable = { name = zg361_mg_report_nine_box_code value = 0 }
		set_variable = { name = zg361_mg_report_score_available value = 0 }
		set_variable = { name = zg361_mg_report_reason_available value = 0 }
		set_variable = { name = zg361_mg_report_nine_box_available value = 0 }
"""
    schedule = ""
    if event_id is not None:
        schedule = f"""if = {{
			limit = {{ var:zg361_case_f_state = {state + 1} }}
			zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.{event_id} DAYS = 1 }}
		}}"""
    else:
        schedule = """if = {
			limit = { var:zg361_case_f_state = 5 var:zg361_case_f_active = 0 }
			if = { limit = { is_ai = no } zg361_mg_schedule_f_ticket_effect = { EVENT = zg361mg.120 DAYS = 1 } }
			else = { debug_log = "ZG361MG: eligible AI deferred manager report completed silently" }
		}"""
    return f"""if = {{
		limit = {{
			var:zg361_mg_m{mechanism_id:03d}_route = 3
			var:zg361_case_f_state = {state}
			var:zg361_case_f_active = 1
			{receipt_current("F", mechanism_id, state)}
		}}
{deferred_projection}		{transition_call("F", state)}
		{schedule}
	}}"""


def business_object_prelude(domain: str, mechanism_id: int, kind_code: int) -> str:
    """Freeze a stable owner-inclusive object identity for A/B only."""

    prefix = domain.lower()
    return f"""set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_business_object_created value = 1 }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_owner value = var:zg361_case_{prefix}_owner }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_subject value = this }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_cycle value = var:zg361_case_{prefix}_cycle_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_case value = var:zg361_case_{prefix}_case_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_state value = var:zg361_case_{prefix}_state }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_revision value = var:zg361_case_{prefix}_revision }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_route value = var:zg361_mg_m{mechanism_id:03d}_route }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_kind value = {kind_code} }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_input_fingerprint value = var:zg361_mg_m{mechanism_id:03d}_requested_input_fingerprint }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_object_id value = {{ value = var:zg361_case_{prefix}_case_serial multiply = 1000 add = {mechanism_id} }} }}"""


def render_policy_debt_consumer() -> str:
    blocks = []
    for mechanism_id in TARGET_IDS:
        blocks.append(
            f"""if = {{
		limit = {{
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_status
			var:zg361_mg_m{mechanism_id:03d}_debt_status = 1
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_owner
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_subject
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_cycle
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_case
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_state
			has_variable = zg361_mg_m{mechanism_id:03d}_debt_revision
			has_variable = zg361_mg_m{mechanism_id:03d}_next_review_serial
			root.var:zg361_review_serial >= var:zg361_mg_m{mechanism_id:03d}_next_review_serial
			var:zg361_mg_m{mechanism_id:03d}_debt_subject = this
		}}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_status value = 2 }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_settled_cycle value = root.var:zg361_review_serial }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_settled_by_owner value = root }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_manager_score_delta value = -3 }}
		set_variable = {{ name = zg361_mg_m{mechanism_id:03d}_debt_remediation_code value = 1 }}
		change_variable = {{ name = zg361_mg_manager_score_delta add = -3 }}
		set_variable = {{ name = zg361_mg_manager_score_delta_due_cycle value = root.var:zg361_review_serial }}
	}}"""
        )
    joined = "\n\t".join(blocks)
    return f"""# Route-C debt is a real next-cycle object: one exact pending entry is
# consumed once.  Its original owner remains frozen; settled_by_owner records
# the current direct superior without rewriting the source identity.
zg361_mg_consume_due_policy_debts_effect = {{
	{joined}
}}"""


def render_q_projection_adapter() -> str:
    blocks = []
    for mechanism_id in Q_PROJECTION_IDS:
        expected_state = 1 + (mechanism_id - 121) // 2
        blocks.append(
            f"""if = {{
		limit = {{
			has_variable = zg361_mg_q{mechanism_id:03d}_projected
			var:zg361_mg_q{mechanism_id:03d}_owner = var:zg361_ch_m{mechanism_id:03d}_receipt_owner
			var:zg361_mg_q{mechanism_id:03d}_subject = this
			var:zg361_mg_q{mechanism_id:03d}_cycle = var:zg361_ch_m{mechanism_id:03d}_receipt_cycle
			var:zg361_mg_q{mechanism_id:03d}_case = var:zg361_ch_m{mechanism_id:03d}_receipt_case
			var:zg361_mg_q{mechanism_id:03d}_state = var:zg361_ch_m{mechanism_id:03d}_receipt_state
			OR = {{
				NOT = {{ var:zg361_mg_q{mechanism_id:03d}_route = var:zg361_ch_m{mechanism_id:03d}_receipt_route }}
				NOT = {{ var:zg361_mg_q{mechanism_id:03d}_value = var:zg361_ch_m{mechanism_id:03d}_value }}
			}}
		}}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {mechanism_id} }}
	}}
	else_if = {{
		limit = {{
			has_variable = zg361_mg_q{mechanism_id:03d}_projected
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_owner
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_cycle
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_case
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_state
			OR = {{
				var:zg361_ch_m{mechanism_id:03d}_receipt_cycle < var:zg361_mg_q{mechanism_id:03d}_cycle
				AND = {{
					var:zg361_ch_m{mechanism_id:03d}_receipt_cycle = var:zg361_mg_q{mechanism_id:03d}_cycle
					var:zg361_ch_m{mechanism_id:03d}_receipt_case < var:zg361_mg_q{mechanism_id:03d}_case
				}}
				AND = {{
					var:zg361_ch_m{mechanism_id:03d}_receipt_cycle = var:zg361_mg_q{mechanism_id:03d}_cycle
					var:zg361_ch_m{mechanism_id:03d}_receipt_case = var:zg361_mg_q{mechanism_id:03d}_case
					var:zg361_ch_m{mechanism_id:03d}_receipt_state < var:zg361_mg_q{mechanism_id:03d}_state
				}}
				AND = {{
					var:zg361_ch_m{mechanism_id:03d}_receipt_cycle = var:zg361_mg_q{mechanism_id:03d}_cycle
					var:zg361_ch_m{mechanism_id:03d}_receipt_case = var:zg361_mg_q{mechanism_id:03d}_case
					var:zg361_ch_m{mechanism_id:03d}_receipt_state = var:zg361_mg_q{mechanism_id:03d}_state
					NOT = {{ var:zg361_ch_m{mechanism_id:03d}_receipt_owner = var:zg361_mg_q{mechanism_id:03d}_owner }}
				}}
			}}
		}}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {mechanism_id} }}
	}}
	else_if = {{
		limit = {{
			has_variable = zg361_ch_m{mechanism_id:03d}_consumed
			var:zg361_ch_m{mechanism_id:03d}_consumed = 1
			has_variable = zg361_ch_m{mechanism_id:03d}_business_consumed
			var:zg361_ch_m{mechanism_id:03d}_business_consumed = 1
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_owner
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_subject
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_cycle
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_case
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_state
			has_variable = zg361_ch_m{mechanism_id:03d}_receipt_route
			has_variable = zg361_ch_m{mechanism_id:03d}_value
			var:zg361_ch_m{mechanism_id:03d}_receipt_subject = this
			var:zg361_ch_m{mechanism_id:03d}_receipt_state = {expected_state}
			OR = {{
				AND = {{ var:zg361_ch_m{mechanism_id:03d}_receipt_route = 1 var:zg361_ch_m{mechanism_id:03d}_value = 1 }}
				AND = {{ var:zg361_ch_m{mechanism_id:03d}_receipt_route = 2 var:zg361_ch_m{mechanism_id:03d}_value = -1 }}
				AND = {{ var:zg361_ch_m{mechanism_id:03d}_receipt_route = 3 var:zg361_ch_m{mechanism_id:03d}_value = 0 }}
			}}
			trigger_if = {{
				limit = {{ has_variable = zg361_mg_q{mechanism_id:03d}_projected }}
				OR = {{
					var:zg361_ch_m{mechanism_id:03d}_receipt_cycle > var:zg361_mg_q{mechanism_id:03d}_cycle
					AND = {{
						var:zg361_ch_m{mechanism_id:03d}_receipt_cycle = var:zg361_mg_q{mechanism_id:03d}_cycle
						var:zg361_ch_m{mechanism_id:03d}_receipt_case > var:zg361_mg_q{mechanism_id:03d}_case
					}}
					AND = {{
						var:zg361_ch_m{mechanism_id:03d}_receipt_cycle = var:zg361_mg_q{mechanism_id:03d}_cycle
						var:zg361_ch_m{mechanism_id:03d}_receipt_case = var:zg361_mg_q{mechanism_id:03d}_case
						var:zg361_ch_m{mechanism_id:03d}_receipt_state > var:zg361_mg_q{mechanism_id:03d}_state
					}}
				}}
			}}
			trigger_else = {{ always = yes }}
		}}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_projected value = 1 }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_source value = 1 }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_owner value = var:zg361_ch_m{mechanism_id:03d}_receipt_owner }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_subject value = this }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_cycle value = var:zg361_ch_m{mechanism_id:03d}_receipt_cycle }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_case value = var:zg361_ch_m{mechanism_id:03d}_receipt_case }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_state value = var:zg361_ch_m{mechanism_id:03d}_receipt_state }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_route value = var:zg361_ch_m{mechanism_id:03d}_receipt_route }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_value value = var:zg361_ch_m{mechanism_id:03d}_value }}
		set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_present value = 0 }}
		if = {{
			limit = {{
				OR = {{ var:zg361_ch_m{mechanism_id:03d}_receipt_route = 1 var:zg361_ch_m{mechanism_id:03d}_receipt_route = 2 }}
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_id
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_owner
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_subject
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_cycle
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_case
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_state
				has_variable = zg361_ch_m{mechanism_id:03d}_manager_object_revision
				var:zg361_ch_m{mechanism_id:03d}_manager_object_owner = var:zg361_ch_m{mechanism_id:03d}_receipt_owner
				var:zg361_ch_m{mechanism_id:03d}_manager_object_subject = this
				var:zg361_ch_m{mechanism_id:03d}_manager_object_cycle = var:zg361_ch_m{mechanism_id:03d}_receipt_cycle
				var:zg361_ch_m{mechanism_id:03d}_manager_object_case = var:zg361_ch_m{mechanism_id:03d}_receipt_case
				var:zg361_ch_m{mechanism_id:03d}_manager_object_state = var:zg361_ch_m{mechanism_id:03d}_receipt_state
				var:zg361_ch_m{mechanism_id:03d}_manager_object_route = var:zg361_ch_m{mechanism_id:03d}_receipt_route
			}}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_present value = 1 }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_id value = var:zg361_ch_m{mechanism_id:03d}_manager_object_id }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_owner value = var:zg361_ch_m{mechanism_id:03d}_manager_object_owner }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_subject value = var:zg361_ch_m{mechanism_id:03d}_manager_object_subject }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_cycle value = var:zg361_ch_m{mechanism_id:03d}_manager_object_cycle }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_case value = var:zg361_ch_m{mechanism_id:03d}_manager_object_case }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_state value = var:zg361_ch_m{mechanism_id:03d}_manager_object_state }}
			set_variable = {{ name = zg361_mg_q{mechanism_id:03d}_authoritative_object_revision value = var:zg361_ch_m{mechanism_id:03d}_manager_object_revision }}
		}}
	}}"""
        )
    joined = "\n\t".join(blocks)
    return f"""# Read-only Q121-128 adapter.  career_hc remains the only case/object
# authority; this projection never opens, advances or settles a Q case.
zg361_mg_project_career_hc_q_receipts_effect = {{
	{joined}
}}"""


def render_values() -> bytes:
    """Render package-owned inputs consumed by the shared eight-KPI core."""

    body = r'''
# Freeze the only real distribution producers into F035's input fingerprint.
# mode 0 is typed unavailable; kind 1/2 means decision override/game rule.
zg361_mg_distribution_source_mode_value = {
	value = 0
	if = { limit = { has_variable = zg361_ratio_override var:zg361_ratio_override = 10 } add = 1 }
	else_if = { limit = { has_variable = zg361_ratio_override var:zg361_ratio_override = 5 } add = 2 }
	else_if = { limit = { has_variable = zg361_ratio_override var:zg361_ratio_override = 0 } add = 3 }
	else_if = { limit = { NOT = { has_variable = zg361_ratio_override } has_game_rule = zg361_ratio_strict } add = 1 }
	else_if = { limit = { NOT = { has_variable = zg361_ratio_override } has_game_rule = zg361_ratio_relaxed } add = 2 }
	else_if = { limit = { NOT = { has_variable = zg361_ratio_override } has_game_rule = zg361_ratio_off } add = 3 }
}

zg361_mg_distribution_source_kind_value = {
	value = 0
	if = {
		limit = {
			has_variable = zg361_ratio_override
			OR = { var:zg361_ratio_override = 10 var:zg361_ratio_override = 5 var:zg361_ratio_override = 0 }
		}
		add = 1
	}
	else_if = {
		limit = {
			NOT = { has_variable = zg361_ratio_override }
			OR = {
				has_game_rule = zg361_ratio_strict
				has_game_rule = zg361_ratio_relaxed
				has_game_rule = zg361_ratio_off
			}
		}
		add = 2
	}
}

# F032 is folded into official component 8 (organization) on the next review.
# This value is deliberately not referenced as a ninth addend by zg361_kpi_value.
zg361_mg_due_organization_kpi_value = {
	value = 0
	if = {
		limit = {
			has_variable = zg361_mg_organization_input_status
			var:zg361_mg_organization_input_status = 1
			has_variable = zg361_mg_organization_input_owner
			has_variable = zg361_mg_organization_input_subject
			has_variable = zg361_mg_organization_input_value
			var:zg361_mg_organization_input_owner = liege
			var:zg361_mg_organization_input_subject = this
$ORGANIZATION_DUE_GUARD$
		}
		add = var:zg361_mg_organization_input_value
	}
}

# Exact 10/5/0 next-cycle policy.  Relaxed mode intentionally has no minimum
# slot; strict mode keeps the core cohort>=5 minimum of one.
zg361_mg_effective_bottom_slots_value = {
	value = 0
	if = {
		limit = {
			has_variable = zg361_mg_distribution_policy_applied_this_rank
			var:zg361_mg_distribution_policy_applied_this_rank = 1
			var:zg361_mg_distribution_effective_mode = 2
		}
		add = {
			value = var:zg361_cohort_n
			multiply = 0.05
			floor = yes
		}
	}
	else_if = {
		limit = {
			has_variable = zg361_mg_distribution_policy_applied_this_rank
			var:zg361_mg_distribution_policy_applied_this_rank = 1
			var:zg361_mg_distribution_effective_mode = 1
		}
		add = {
			value = var:zg361_cohort_n
			multiply = 0.10
			floor = yes
		}
		if = {
			limit = { var:zg361_cohort_n >= 5 }
			min = 1
		}
	}
}
'''
    return generated(body.replace("$ORGANIZATION_DUE_GUARD$", ORGANIZATION_DUE_GUARD))


def render_shared_hook_adapters() -> str:
    """Effects called by the three root-owned shared insertion points."""

    body = r'''# Called immediately after the official KPI/debt write.  The input was
# already read by component 8, so this only settles the exact source once.
zg361_mg_settle_due_organization_kpi_effect = {
	if = {
		limit = {
			has_variable = zg361_mg_organization_input_status
			var:zg361_mg_organization_input_status = 1
			has_variable = zg361_mg_organization_input_owner
			has_variable = zg361_mg_organization_input_subject
			has_variable = zg361_mg_organization_input_value
			var:zg361_mg_organization_input_owner = liege
			var:zg361_mg_organization_input_subject = this
$ORGANIZATION_DUE_GUARD$
		}
		set_variable = { name = zg361_mg_organization_input_status value = 2 }
		set_variable = { name = zg361_mg_organization_settled_by_owner value = liege }
		set_variable = { name = zg361_mg_organization_settled_cycle value = var:zg361_mg_organization_input_due_cycle }
		if = { limit = { has_variable = zg361_b1_cycle_serial } set_variable = { name = zg361_mg_organization_settled_cycle value = var:zg361_b1_cycle_serial } }
		set_variable = { name = zg361_mg_organization_settled_value value = var:zg361_mg_organization_input_value }
		set_variable = { name = zg361_mg_organization_settlement_receipt value = var:zg361_mg_organization_input_source_case }
	}
}

# Consume an F035 policy only at its declared next review.  A retained old
# effective mode cannot leak because the selector below requires this cycle.
zg361_mg_apply_due_distribution_policy_effect = {
	if = {
		limit = {
			has_variable = zg361_mg_distribution_policy_status
			var:zg361_mg_distribution_policy_status = 1
			has_variable = zg361_mg_distribution_policy_owner
			var:zg361_mg_distribution_policy_owner = this
$DISTRIBUTION_DUE_GUARD$
			has_variable = zg361_mg_distribution_policy_mode
			var:zg361_mg_distribution_policy_mode >= 1
			var:zg361_mg_distribution_policy_mode <= 3
		}
		set_variable = { name = zg361_mg_distribution_effective_mode value = var:zg361_mg_distribution_policy_mode }
		set_variable = { name = zg361_mg_distribution_effective_cycle value = var:zg361_mg_distribution_policy_due_cycle }
		if = { limit = { has_variable = zg361_b1_cycle_serial } set_variable = { name = zg361_mg_distribution_effective_cycle value = var:zg361_b1_cycle_serial } }
		set_variable = { name = zg361_mg_distribution_effective_source_cycle value = var:zg361_mg_distribution_policy_source_cycle }
		set_variable = { name = zg361_mg_distribution_effective_source_case value = var:zg361_mg_distribution_policy_source_case }
		set_variable = { name = zg361_mg_distribution_effective_input_revision value = var:zg361_mg_distribution_policy_input_revision }
		set_variable = { name = zg361_mg_distribution_policy_applied_this_rank value = 1 }
		set_variable = { name = zg361_mg_distribution_policy_status value = 2 }
		set_variable = { name = zg361_mg_distribution_policy_settled_cycle value = var:zg361_mg_distribution_effective_cycle }
		set_variable = { name = zg361_mg_distribution_policy_settlement_receipt value = var:zg361_mg_distribution_policy_source_case }
	}
}

# Replacement for the one core bottom-slot assignment.  It preserves the core
# value unless a fully bound F035 policy was consumed for this exact cycle.
zg361_mg_set_bottom_slots_effect = {
	set_variable = { name = zg361_mg_distribution_policy_applied_this_rank value = 0 }
	zg361_mg_apply_due_distribution_policy_effect = yes
	set_variable = { name = zg361_bottom_slots value = zg361_bottom_slots_value }
	if = {
		limit = { var:zg361_mg_distribution_policy_applied_this_rank = 1 }
		set_variable = { name = zg361_bottom_slots value = zg361_mg_effective_bottom_slots_value }
	}
	remove_variable = zg361_mg_distribution_policy_applied_this_rank
}'''
    return body.replace("$ORGANIZATION_DUE_GUARD$", ORGANIZATION_DUE_GUARD).replace(
        "$DISTRIBUTION_DUE_GUARD$", DISTRIBUTION_DUE_GUARD
    )


def collective_cost_receipt_guard(ordinal: int) -> str:
    """Exact replay identity for one already-applied #360 manager cost."""

    base = f"zg361_we_al_external_collective_{ordinal}"
    required = (
        "status", "id", "hash", "owner", "al_subject", "al_cycle", "al_case",
        "settlement_id", "settlement_hash", "cohort_id", "ordinal", "manager",
        "mg_cycle", "mg_case", "mg_snapshot_source_serial",
        "mg_snapshot_revision", "b1_cycle", "b1_case", "b1_source_id",
        "b1_source_hash", "route", "quota",
        "exception_count", "cost", "score_before", "score_after", "score_delta",
    )
    lines = [f"has_variable = zg361_mg_m360_cost_receipt_{field}" for field in required]
    lines += [
        "var:zg361_mg_m360_cost_receipt_status = 1",
        f"var:zg361_mg_m360_cost_receipt_id = {{ value = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id multiply = 1000 add = 360 }}",
        (
            "var:zg361_mg_m360_cost_receipt_hash = { value = "
            "var:zg361_mg_m360_cost_receipt_id multiply = 100 add = { value = "
            "scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route "
            f"multiply = 10 }} add = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }}"
        ),
        "var:zg361_mg_m360_cost_receipt_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_mg_m360_cost_receipt_al_subject = scope:zg361_we_m360_cost_subject",
        "var:zg361_mg_m360_cost_receipt_al_cycle = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_cycle",
        "var:zg361_mg_m360_cost_receipt_al_case = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_case",
        "var:zg361_mg_m360_cost_receipt_settlement_id = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_settlement_id",
        "var:zg361_mg_m360_cost_receipt_settlement_hash = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_settlement_hash",
        f"var:zg361_mg_m360_cost_receipt_cohort_id = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id",
        f"var:zg361_mg_m360_cost_receipt_ordinal = {ordinal}",
        "var:zg361_mg_m360_cost_receipt_manager = this",
        f"var:zg361_mg_m360_cost_receipt_mg_cycle = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle",
        f"var:zg361_mg_m360_cost_receipt_mg_case = scope:zg361_we_m360_cost_subject.var:{base}_mg_case",
        f"var:zg361_mg_m360_cost_receipt_mg_snapshot_source_serial = scope:zg361_we_m360_cost_subject.var:{base}_mg_snapshot_source_serial",
        "var:zg361_mg_m360_cost_receipt_mg_snapshot_revision = var:zg361_mg_team_snapshot_revision",
        f"var:zg361_mg_m360_cost_receipt_b1_cycle = scope:zg361_we_m360_cost_subject.var:{base}_b1_cycle",
        f"var:zg361_mg_m360_cost_receipt_b1_case = scope:zg361_we_m360_cost_subject.var:{base}_b1_case",
        "var:zg361_mg_m360_cost_receipt_b1_source_id = var:zg361_b1_m360_source_id",
        "var:zg361_mg_m360_cost_receipt_b1_source_hash = var:zg361_b1_m360_source_hash",
        "var:zg361_mg_m360_cost_receipt_route = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route",
        f"var:zg361_mg_m360_cost_receipt_quota = scope:zg361_we_m360_cost_subject.var:{base}_quota",
        f"var:zg361_mg_m360_cost_receipt_exception_count = scope:zg361_we_m360_cost_subject.var:{base}_exception_count",
        f"var:zg361_mg_m360_cost_receipt_cost = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost",
        (
            "var:zg361_mg_m360_cost_receipt_score_after = { value = "
            "var:zg361_mg_m360_cost_receipt_score_before subtract = "
            f"scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }}"
        ),
        (
            "var:zg361_mg_m360_cost_receipt_score_delta = { value = 0 subtract = "
            f"scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }}"
        ),
    ]
    return "\n\t".join(lines)


def collective_cost_source_guard(ordinal: int) -> str:
    """Validate sealed AL input against the manager's frozen MG/B1 source."""

    base = f"zg361_we_al_external_collective_{ordinal}"
    subject_required = (
        "submission_owner", "submission_subject", "submission_cycle",
        "submission_case", "submission_state", "submission_active",
        "submission_sealed", "submission_consumed", "settlement_id",
        "settlement_hash", "route", "settled",
    )
    cohort_required = (
        "cohort_id", "manager", "member_count", "member_hash", "agenda_count",
        "agenda_hash", "quota", "all_meet_evidence_id", "forced_count",
        "exception_count", "approver", "manager_cost", "partition_verified",
        "approval_verified", "mg_cycle", "mg_case", "mg_snapshot_source_serial",
        "b1_cycle", "b1_case",
    )
    subject_lines = [
        *(f"has_variable = zg361_we_al_external_collective_{field}" for field in subject_required),
        *(f"has_variable = {base}_{field}" for field in cohort_required),
        "var:zg361_we_al_external_collective_submission_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_we_al_external_collective_submission_subject = this",
        "var:zg361_we_al_external_collective_submission_state = 4",
        "var:zg361_we_al_external_collective_submission_active = 1",
        "var:zg361_we_al_external_collective_submission_sealed = 1",
        "var:zg361_we_al_external_collective_submission_consumed = 0",
        "var:zg361_we_al_external_collective_settled = 0",
        "var:zg361_we_al_external_collective_settlement_id > 0",
        "var:zg361_we_al_external_collective_settlement_hash > 0",
        "var:zg361_we_al_external_collective_route >= 1",
        "var:zg361_we_al_external_collective_route <= 2",
        f"var:{base}_manager = root",
        f"var:{base}_cohort_id = {{ value = var:zg361_we_al_external_collective_settlement_id multiply = 10 add = {ordinal} }}",
        f"var:{base}_member_count >= 1",
        f"var:{base}_member_count = var:{base}_agenda_count",
        f"var:{base}_member_hash = var:{base}_agenda_hash",
        f"var:{base}_member_hash > 0",
        f"var:{base}_quota >= 1",
        f"var:{base}_quota <= 6",
        f"var:{base}_quota <= var:{base}_member_count",
        f"var:{base}_all_meet_evidence_id > 0",
        f"var:{base}_partition_verified = 1",
        f"var:{base}_mg_cycle > 0",
        f"var:{base}_mg_case > 0",
        f"var:{base}_mg_snapshot_source_serial > 0",
        f"var:{base}_b1_cycle > 0",
        f"var:{base}_b1_case > 0",
        (
            "OR = { "
            "AND = { var:zg361_we_al_external_collective_route = 1 "
            f"var:{base}_forced_count = 0 var:{base}_exception_count = var:{base}_quota "
            f"var:{base}_manager_cost = var:{base}_quota "
            f"var:{base}_approver = scope:zg361_we_m360_cost_owner var:{base}_approval_verified = 1 }} "
            "AND = { var:zg361_we_al_external_collective_route = 2 "
            f"var:{base}_forced_count = var:{base}_quota var:{base}_exception_count = 0 "
            f"var:{base}_manager_cost = 0 var:{base}_approver = 0 var:{base}_approval_verified = 0 }} }}"
        ),
    ]
    manager_lines = [
        "exists = scope:zg361_we_m360_cost_owner",
        "exists = scope:zg361_we_m360_cost_subject",
        "zg361_is_celestial_liege_trigger = yes",
        "liege = scope:zg361_we_m360_cost_owner",
        "scope:zg361_we_m360_cost_owner = { zg361_is_celestial_liege_trigger = yes }",
        "scope:zg361_we_m360_cost_subject = {",
        *(f"\t{line}" for line in subject_lines),
        "}",
        "has_variable = zg361_case_f_owner",
        "has_variable = zg361_case_f_subject",
        "has_variable = zg361_case_f_cycle_serial",
        "has_variable = zg361_case_f_case_serial",
        "has_variable = zg361_case_f_state",
        "has_variable = zg361_case_f_active",
        "var:zg361_case_f_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_case_f_subject = this",
        f"var:zg361_case_f_cycle_serial = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle",
        f"var:zg361_case_f_case_serial = scope:zg361_we_m360_cost_subject.var:{base}_mg_case",
        "var:zg361_case_f_state = 5",
        "var:zg361_case_f_active = 0",
        "has_variable = zg361_mg_team_snapshot_status",
        "has_variable = zg361_mg_team_snapshot_owner",
        "has_variable = zg361_mg_team_snapshot_subject",
        "has_variable = zg361_mg_team_snapshot_cycle",
        "has_variable = zg361_mg_team_snapshot_case",
        "has_variable = zg361_mg_team_snapshot_revision",
        "has_variable = zg361_mg_snapshot_source_serial",
        "has_variable = zg361_mg_team_snapshot_b1_available",
        "has_variable = zg361_mg_team_snapshot_b1_manager",
        "has_variable = zg361_mg_team_snapshot_b1_cycle",
        "has_variable = zg361_mg_team_snapshot_b1_case",
        "has_variable = zg361_mg_team_snapshot_b1_id",
        "has_variable = zg361_mg_team_snapshot_b1_hash",
        "var:zg361_mg_team_snapshot_status = 1",
        "var:zg361_mg_team_snapshot_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_mg_team_snapshot_subject = this",
        f"var:zg361_mg_team_snapshot_cycle = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle",
        f"var:zg361_mg_team_snapshot_case = scope:zg361_we_m360_cost_subject.var:{base}_mg_case",
        f"var:zg361_mg_snapshot_source_serial = scope:zg361_we_m360_cost_subject.var:{base}_mg_snapshot_source_serial",
        f"var:zg361_review_serial = scope:zg361_we_m360_cost_subject.var:{base}_mg_snapshot_source_serial",
        "var:zg361_mg_team_snapshot_b1_available = 1",
        "var:zg361_mg_team_snapshot_b1_manager = this",
        f"var:zg361_mg_team_snapshot_b1_cycle = scope:zg361_we_m360_cost_subject.var:{base}_b1_cycle",
        f"var:zg361_mg_team_snapshot_b1_case = scope:zg361_we_m360_cost_subject.var:{base}_b1_case",
        "has_variable = zg361_b1_m360_source_available",
        "has_variable = zg361_b1_m360_source_status",
        "has_variable = zg361_b1_m360_source_sealed",
        "has_variable = zg361_b1_m360_source_id",
        "has_variable = zg361_b1_m360_source_hash",
        "has_variable = zg361_b1_m360_source_manager",
        "has_variable = zg361_b1_m360_source_cycle",
        "has_variable = zg361_b1_m360_source_case",
        "has_variable = zg361_b1_m360_source_state",
        "has_variable = zg361_b1_m360_source_member_count",
        "has_variable = zg361_b1_m360_source_member_hash",
        "has_variable = zg361_b1_m360_source_agenda_count",
        "has_variable = zg361_b1_m360_source_agenda_hash",
        "has_variable = zg361_b1_m360_source_quota",
        "has_variable = zg361_b1_m360_source_all_meet_receipt_serial",
        "has_variable = zg361_b1_m360_source_forced_count",
        "var:zg361_b1_m360_source_available = 1",
        "var:zg361_b1_m360_source_status = 1",
        "var:zg361_b1_m360_source_sealed = 1",
        "var:zg361_b1_m360_source_id > 0",
        "var:zg361_b1_m360_source_hash > 0",
        "var:zg361_b1_m360_source_id = var:zg361_mg_team_snapshot_b1_id",
        "var:zg361_b1_m360_source_hash = var:zg361_mg_team_snapshot_b1_hash",
        "var:zg361_b1_m360_source_manager = this",
        f"var:zg361_b1_m360_source_cycle = scope:zg361_we_m360_cost_subject.var:{base}_b1_cycle",
        f"var:zg361_b1_m360_source_case = scope:zg361_we_m360_cost_subject.var:{base}_b1_case",
        "var:zg361_b1_m360_source_state = 8",
        f"var:zg361_b1_m360_source_member_count = scope:zg361_we_m360_cost_subject.var:{base}_member_count",
        f"var:zg361_b1_m360_source_member_hash = scope:zg361_we_m360_cost_subject.var:{base}_member_hash",
        f"var:zg361_b1_m360_source_agenda_count = scope:zg361_we_m360_cost_subject.var:{base}_agenda_count",
        f"var:zg361_b1_m360_source_agenda_hash = scope:zg361_we_m360_cost_subject.var:{base}_agenda_hash",
        f"var:zg361_b1_m360_source_quota = scope:zg361_we_m360_cost_subject.var:{base}_quota",
        f"var:zg361_b1_m360_source_all_meet_receipt_serial = scope:zg361_we_m360_cost_subject.var:{base}_all_meet_evidence_id",
        "var:zg361_b1_m360_source_forced_count = var:zg361_b1_m360_source_quota",
        "has_variable = zg361_mg_m036_receipt_owner",
        "has_variable = zg361_mg_m036_receipt_subject",
        "has_variable = zg361_mg_m036_receipt_cycle",
        "has_variable = zg361_mg_m036_receipt_case",
        "has_variable = zg361_mg_m036_receipt_state",
        "has_variable = zg361_mg_m036_receipt_choice",
        "var:zg361_mg_m036_receipt_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_mg_m036_receipt_subject = this",
        f"var:zg361_mg_m036_receipt_cycle = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle",
        f"var:zg361_mg_m036_receipt_case = scope:zg361_we_m360_cost_subject.var:{base}_mg_case",
        "var:zg361_mg_m036_receipt_state = 4",
        "OR = { var:zg361_mg_m036_receipt_choice = 1 var:zg361_mg_m036_receipt_choice = 2 }",
        "has_variable = zg361_mg_m036_object_owner",
        "has_variable = zg361_mg_m036_object_subject",
        "has_variable = zg361_mg_m036_object_cycle",
        "has_variable = zg361_mg_m036_object_case",
        "has_variable = zg361_mg_m036_object_state",
        "var:zg361_mg_m036_object_owner = scope:zg361_we_m360_cost_owner",
        "var:zg361_mg_m036_object_subject = this",
        f"var:zg361_mg_m036_object_cycle = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle",
        f"var:zg361_mg_m036_object_case = scope:zg361_we_m360_cost_subject.var:{base}_mg_case",
        "var:zg361_mg_m036_object_state = 4",
    ]
    return "\n\t".join(manager_lines)


def collective_cost_new_receipt_guard(ordinal: int) -> str:
    """A new receipt may only supersede an older AL case for this manager."""

    base = f"zg361_we_al_external_collective_{ordinal}"
    return f"""OR = {{
	NOT = {{ has_variable = zg361_mg_m360_cost_receipt_status }}
	AND = {{
		has_variable = zg361_mg_m360_cost_receipt_status
		var:zg361_mg_m360_cost_receipt_status = 1
		has_variable = zg361_mg_m360_cost_receipt_al_cycle
		has_variable = zg361_mg_m360_cost_receipt_al_case
		has_variable = zg361_mg_m360_cost_receipt_id
		OR = {{
			var:zg361_mg_m360_cost_receipt_al_cycle < scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_cycle
			AND = {{
				var:zg361_mg_m360_cost_receipt_al_cycle = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_cycle
				var:zg361_mg_m360_cost_receipt_al_case < scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_case
			}}
		}}
		NOT = {{ var:zg361_mg_m360_cost_receipt_id = {{ value = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id multiply = 1000 add = 360 }} }}
	}}
}}"""


def render_collective_cost_triggers() -> bytes:
    """Preflight all three managers before Workforce mutates any resource."""

    blocks: list[str] = []
    for ordinal in COLLECTIVE_COST_ORDINALS:
        base = f"zg361_we_al_external_collective_{ordinal}"
        receipt = collective_cost_receipt_guard(ordinal)
        blocks.append(
            f"""# Manager-scope preflight for #360 cohort {ordinal}.  Route B is a
# validated zero-cost N/A and deliberately needs no manager-score variable.
zg361_mg_m360_collective_cost_c{ordinal}_receipt_is_current_trigger = {{
	{receipt}
}}

zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger = {{
	{collective_cost_source_guard(ordinal)}
	OR = {{
		AND = {{
			scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route = 2
			scope:zg361_we_m360_cost_subject.var:{base}_manager_cost = 0
		}}
		AND = {{
			scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route = 1
			scope:zg361_we_m360_cost_subject.var:{base}_manager_cost > 0
			has_variable = zg361_mg_report_score_available
			var:zg361_mg_report_score_available = 1
			has_variable = zg361_mg_report_manager_score
			has_variable = zg361_mg_manager_score
			OR = {{
				zg361_mg_m360_collective_cost_c{ordinal}_receipt_is_current_trigger = yes
				AND = {{
					{collective_cost_new_receipt_guard(ordinal).replace(chr(10), chr(10) + chr(9) * 5)}
					var:zg361_mg_manager_score = var:zg361_mg_report_manager_score
					var:zg361_mg_manager_score >= scope:zg361_we_m360_cost_subject.var:{base}_manager_cost
				}}
			}}
		}}
	}}
}}"""
        )
    return generated("\n\n".join(blocks))


def render_collective_cost_effects() -> str:
    """Apply one real A-route score cost or return replay/N/A/typed RED."""

    blocks: list[str] = []
    for ordinal in COLLECTIVE_COST_ORDINALS:
        base = f"zg361_we_al_external_collective_{ordinal}"
        collision = f"""has_variable = zg361_mg_m360_cost_receipt_status
			var:zg361_mg_m360_cost_receipt_status = 1
			OR = {{
				AND = {{
					has_variable = zg361_mg_m360_cost_receipt_id
					var:zg361_mg_m360_cost_receipt_id = {{ value = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id multiply = 1000 add = 360 }}
				}}
				AND = {{
					has_variable = zg361_mg_m360_cost_receipt_settlement_id
					has_variable = zg361_mg_m360_cost_receipt_cohort_id
					var:zg361_mg_m360_cost_receipt_settlement_id = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_settlement_id
					var:zg361_mg_m360_cost_receipt_cohort_id = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id
				}}
			}}"""
        writes = [
            "set_variable = { name = zg361_mg_m360_cost_receipt_owner value = scope:zg361_we_m360_cost_owner }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_al_subject value = scope:zg361_we_m360_cost_subject }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_al_cycle value = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_cycle }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_al_case value = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_submission_case }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_settlement_id value = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_settlement_id }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_settlement_hash value = scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_settlement_hash }",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_cohort_id value = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_ordinal value = {ordinal} }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_manager value = this }",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_mg_cycle value = scope:zg361_we_m360_cost_subject.var:{base}_mg_cycle }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_mg_case value = scope:zg361_we_m360_cost_subject.var:{base}_mg_case }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_mg_snapshot_source_serial value = scope:zg361_we_m360_cost_subject.var:{base}_mg_snapshot_source_serial }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_mg_snapshot_revision value = var:zg361_mg_team_snapshot_revision }",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_b1_cycle value = scope:zg361_we_m360_cost_subject.var:{base}_b1_cycle }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_b1_case value = scope:zg361_we_m360_cost_subject.var:{base}_b1_case }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_b1_source_id value = var:zg361_b1_m360_source_id }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_b1_source_hash value = var:zg361_b1_m360_source_hash }",
            "set_variable = { name = zg361_mg_m360_cost_receipt_route value = 1 }",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_quota value = scope:zg361_we_m360_cost_subject.var:{base}_quota }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_exception_count value = scope:zg361_we_m360_cost_subject.var:{base}_exception_count }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_cost value = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_id value = {{ value = scope:zg361_we_m360_cost_subject.var:{base}_cohort_id multiply = 1000 add = 360 }} }}",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_hash value = {{ value = var:zg361_mg_m360_cost_receipt_id multiply = 100 add = 10 add = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }} }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_score_before value = var:zg361_mg_manager_score }",
            f"change_variable = {{ name = zg361_mg_manager_score add = {{ value = 0 subtract = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }} }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_score_after value = var:zg361_mg_manager_score }",
            f"set_variable = {{ name = zg361_mg_m360_cost_receipt_score_delta value = {{ value = 0 subtract = scope:zg361_we_m360_cost_subject.var:{base}_manager_cost }} }}",
            "set_variable = { name = zg361_mg_m360_cost_receipt_status value = 1 }",
            "set_variable = { name = zg361_mg_m360_collective_cost_last_result value = 1 }",
        ]
        blocks.append(
            f"""zg361_mg_m360_apply_collective_cost_c{ordinal}_effect = {{
	zg361_mg_clear_red_effect = yes
	remove_variable = zg361_mg_m360_collective_cost_last_result
	set_variable = {{ name = zg361_mg_m360_collective_cost_last_ordinal value = {ordinal} }}
	if = {{
		limit = {{
			zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger = yes
			scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route = 2
		}}
		# Route B has no approved exception and therefore no cost receipt.
		set_variable = {{ name = zg361_mg_m360_collective_cost_last_result value = 3 }}
		debug_log = "ZG361MG: mechanism 360 cohort {ordinal} manager cost is N/A on route B"
	}}
	else_if = {{
		limit = {{
			zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger = yes
			zg361_mg_m360_collective_cost_c{ordinal}_receipt_is_current_trigger = yes
		}}
		set_variable = {{ name = zg361_mg_m360_collective_cost_last_result value = 2 }}
		debug_log = "ZG361MG: mechanism 360 cohort {ordinal} exact manager-cost replay"
	}}
	else_if = {{
		limit = {{
			zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger = yes
			scope:zg361_we_m360_cost_subject.var:zg361_we_al_external_collective_route = 1
		}}
		{chr(10).join(writes).replace(chr(10), chr(10) + chr(9) * 2)}
		debug_log = "ZG361MG: mechanism 360 cohort {ordinal} real manager score cost applied"
	}}
	else_if = {{
		limit = {{
			{collision}
		}}
		set_variable = {{ name = zg361_mg_m360_collective_cost_last_result value = 4 }}
		zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = 360 }}
	}}
	else = {{
		set_variable = {{ name = zg361_mg_m360_collective_cost_last_result value = 4 }}
		zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 360 }}
	}}
}}"""
        )
    return "\n\n".join(blocks)


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

{render_policy_debt_consumer()}

{render_q_projection_adapter()}

{render_shared_hook_adapters()}

# MG-owned side of #360.  Workforce owns the collective business object and
# realm-trust transaction; this bridge owns only validation and the real
# per-manager score mutation/receipt.
{render_collective_cost_effects()}

# The existing Jingcha is free/default-mandatory.  Its explicit player-refusal
# option calls this product effect directly.  Freeze the mandate business token
# before lifecycle cleanup, then apply exactly one -25 opinion instance and one
# eligible-reviewer -50 next-review reason.
zg361_mg_refuse_jingcha_exact_effect = {{
	if = {{
		limit = {{
			has_variable = zg361_jingcha_pending
			has_variable = zg361_jingcha_mandate_superior
			has_variable = zg361_jingcha_mandate_year
		}}
		save_scope_as = zg361_mg_refusing_manager
		set_variable = {{ name = zg361_mg_refusal_owner value = var:zg361_jingcha_mandate_superior }}
		set_variable = {{ name = zg361_mg_refusal_subject value = this }}
		set_variable = {{ name = zg361_mg_refusal_cycle value = var:zg361_jingcha_mandate_year }}
		set_variable = {{ name = zg361_mg_refusal_case value = {{ value = var:zg361_jingcha_mandate_year multiply = 1000 add = 32 }} }}
		if = {{ limit = {{ has_variable = zg361_b1_cycle_serial }} set_variable = {{ name = zg361_mg_refusal_cycle value = var:zg361_b1_cycle_serial }} }}
		if = {{ limit = {{ has_variable = zg361_b1_case_serial }} set_variable = {{ name = zg361_mg_refusal_case value = var:zg361_b1_case_serial }} }}
		set_variable = {{ name = zg361_mg_refusal_state value = 1 }}
		set_variable = {{ name = zg361_mg_refusal_revision value = 1 }}
		set_variable = {{ name = zg361_mg_refusal_operation value = 32 }}
		set_variable = {{ name = zg361_mg_refusal_mandate_year value = var:zg361_jingcha_mandate_year }}
		set_variable = {{ name = zg361_mg_refusal_opinion_delta value = -25 }}
		set_variable = {{ name = zg361_mg_refusal_kpi_delta value = 0 }}
		set_variable = {{ name = zg361_mg_refusal_reviewer_eligible value = 0 }}
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
			set_variable = {{ name = zg361_mg_refusal_reviewer_eligible value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_refusal_status value = 1 }}
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
		zg361_mg_consume_due_policy_debts_effect = yes
		zg361_mg_project_career_hc_q_receipts_effect = yes
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

# Exact replay of the same F case reuses the frozen snapshot; it never consumes
# a subordinate result/PIP/exit producer twice.
zg361_mg_freeze_team_snapshot_effect = {{
	if = {{
		limit = {{
			trigger_if = {{
				limit = {{ has_variable = zg361_mg_team_snapshot_status }}
				OR = {{
					NOT = {{ var:zg361_mg_team_snapshot_status = 1 }}
					NOT = {{ var:zg361_mg_team_snapshot_owner = var:zg361_case_f_owner }}
					NOT = {{ var:zg361_mg_team_snapshot_subject = this }}
					NOT = {{ var:zg361_mg_team_snapshot_cycle = var:zg361_case_f_cycle_serial }}
					NOT = {{ var:zg361_mg_team_snapshot_case = var:zg361_case_f_case_serial }}
				}}
			}}
			trigger_else = {{ always = yes }}
		}}
		zg361_mg_build_team_snapshot_effect = yes
	}}
}}

# Freeze seven score aggregates plus auditable raw counters from a strictly
# earlier manager cycle.  No grandchild ID is copied into the superior roster.
zg361_mg_build_team_snapshot_effect = {{
	if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_team_snapshot_revision }} }} set_variable = {{ name = zg361_mg_team_snapshot_revision value = 0 }} }}
	change_variable = {{ name = zg361_mg_team_snapshot_revision add = 1 }}
	set_variable = {{ name = zg361_mg_snapshot_source_serial value = var:zg361_review_serial }}
	set_variable = {{ name = zg361_mg_snapshot_current_serial value = root.var:zg361_review_serial }}
	# Freeze the exact published B1 cohort source that can later authorize a
	# #360 manager-cost receipt.  A later B1 cycle cannot be substituted for
	# the cohort that this manager review actually scored.
	set_variable = {{ name = zg361_mg_team_snapshot_b1_available value = 0 }}
	remove_variable = zg361_mg_team_snapshot_b1_manager
	remove_variable = zg361_mg_team_snapshot_b1_cycle
	remove_variable = zg361_mg_team_snapshot_b1_case
	remove_variable = zg361_mg_team_snapshot_b1_id
	remove_variable = zg361_mg_team_snapshot_b1_hash
	if = {{
		limit = {{
			has_variable = zg361_b1_m360_source_available
			var:zg361_b1_m360_source_available = 1
			has_variable = zg361_b1_m360_source_status
			var:zg361_b1_m360_source_status = 1
			has_variable = zg361_b1_m360_source_sealed
			var:zg361_b1_m360_source_sealed = 1
			has_variable = zg361_b1_m360_source_id
			var:zg361_b1_m360_source_id > 0
			has_variable = zg361_b1_m360_source_hash
			var:zg361_b1_m360_source_hash > 0
			has_variable = zg361_b1_m360_source_manager
			var:zg361_b1_m360_source_manager = this
			has_variable = zg361_b1_m360_source_cycle
			has_variable = zg361_b1_m360_source_case
			has_variable = zg361_b1_m360_source_state
			var:zg361_b1_m360_source_state = 8
		}}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_available value = 1 }}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_manager value = var:zg361_b1_m360_source_manager }}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_cycle value = var:zg361_b1_m360_source_cycle }}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_case value = var:zg361_b1_m360_source_case }}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_id value = var:zg361_b1_m360_source_id }}
		set_variable = {{ name = zg361_mg_team_snapshot_b1_hash value = var:zg361_b1_m360_source_hash }}
	}}
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
	set_variable = {{ name = zg361_mg_team_delivered_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_appeal_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_overturn_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_exit_n value = 0 }}
	set_variable = {{ name = zg361_mg_team_healthy_exit_n value = 0 }}
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
			limit = {{ has_variable = zg361_result_delivery_method var:zg361_result_delivery_method > 0 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_delivered_n add = 1 }} }}
		}}
		if = {{
			limit = {{ has_variable = zg361_result_grade_reason var:zg361_result_grade_reason >= 1 var:zg361_result_grade_reason <= 4 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_calibration add = -5 }} }}
		}}
		if = {{
			limit = {{ has_variable = zg361_result_appeal_outcome var:zg361_result_appeal_outcome >= 1 var:zg361_result_appeal_outcome <= 2 }}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_appeal_n add = 1 }} }}
			if = {{
				limit = {{ var:zg361_result_appeal_outcome = 1 }}
				scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_overturn_n add = 1 }} change_variable = {{ name = zg361_mg_team_appeal_overturn add = -5 }} }}
			}}
		}}
		if = {{
			limit = {{
				has_variable = zg361_b2_pip_owner
				has_variable = zg361_b2_pip_cycle
				has_variable = zg361_b2_pip_case
				has_variable = zg361_b2_pip_state
				has_variable = zg361_b2_pip_graduation_receipt
				var:zg361_b2_pip_owner = scope:zg361_mg_snapshot_manager
				var:zg361_b2_pip_cycle = scope:zg361_mg_snapshot_manager.var:zg361_review_serial
				var:zg361_b2_pip_state = 3
				var:zg361_b2_pip_graduation_receipt = var:zg361_b2_pip_case
			}}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_pip_success add = 5 }} }}
		}}
		if = {{
			limit = {{
				has_variable = zg361_b2_m075_owner
				has_variable = zg361_b2_m075_cycle
				has_variable = zg361_b2_m075_case
				has_variable = zg361_b2_m075_state
				has_variable = zg361_b2_m075_actual_exit
				var:zg361_b2_m075_owner = scope:zg361_mg_snapshot_manager
				var:zg361_b2_m075_cycle = scope:zg361_mg_snapshot_manager.var:zg361_review_serial
				var:zg361_b2_m075_state = 3
				var:zg361_b2_m075_actual_exit = 1
			}}
			scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_exit_n add = 1 }} change_variable = {{ name = zg361_mg_team_retention add = -2 }} }}
			if = {{
				limit = {{ has_variable = zg361_b2_m075_neutral_record var:zg361_b2_m075_neutral_record = 1 }}
				scope:zg361_mg_snapshot_manager = {{ change_variable = {{ name = zg361_mg_team_healthy_exit_n add = 1 }} }}
			}}
		}}
	}}
	set_variable = {{
		name = zg361_mg_team_hc_efficiency
		value = {{ value = var:zg361_mg_team_top_n subtract = var:zg361_mg_team_bottom_n multiply = 3 }}
	}}
	if = {{
		limit = {{
			has_variable = zg361_mg_manager_score_delta
			has_variable = zg361_mg_manager_score_delta_due_cycle
			var:zg361_mg_manager_score_delta_due_cycle <= root.var:zg361_review_serial
		}}
		change_variable = {{ name = zg361_mg_team_hc_efficiency add = var:zg361_mg_manager_score_delta }}
		set_variable = {{ name = zg361_mg_manager_score_delta_consumed_cycle value = root.var:zg361_review_serial }}
		remove_variable = zg361_mg_manager_score_delta
		remove_variable = zg361_mg_manager_score_delta_due_cycle
	}}
	set_variable = {{ name = zg361_mg_snapshot_grandchild_id_count value = 0 }}
	set_variable = {{ name = zg361_mg_team_snapshot_status value = 1 }}
	set_variable = {{ name = zg361_mg_team_snapshot_owner value = var:zg361_case_f_owner }}
	set_variable = {{ name = zg361_mg_team_snapshot_subject value = this }}
	set_variable = {{ name = zg361_mg_team_snapshot_cycle value = var:zg361_case_f_cycle_serial }}
	set_variable = {{ name = zg361_mg_team_snapshot_case value = var:zg361_case_f_case_serial }}
	set_variable = {{ name = zg361_mg_team_snapshot_source_cycle value = var:zg361_review_serial }}
	set_variable = {{ name = zg361_mg_fairness_input_status value = 1 }}
	set_variable = {{ name = zg361_mg_fairness_input_revision value = var:zg361_mg_team_snapshot_revision }}
	set_variable = {{ name = zg361_mg_fairness_input_source_owner value = root }}
	set_variable = {{ name = zg361_mg_fairness_input_source_subject value = this }}
	set_variable = {{ name = zg361_mg_fairness_input_source_cycle value = var:zg361_review_serial }}
	set_variable = {{ name = zg361_mg_fairness_input_source_case value = var:zg361_case_f_case_serial }}
	set_variable = {{ name = zg361_mg_fairness_input_delivered value = var:zg361_mg_team_delivered_n }}
	set_variable = {{ name = zg361_mg_fairness_input_appeals value = var:zg361_mg_team_appeal_n }}
	set_variable = {{ name = zg361_mg_fairness_input_overturns value = var:zg361_mg_team_overturn_n }}
	set_variable = {{ name = zg361_mg_fairness_input_exits value = var:zg361_mg_team_exit_n }}
	set_variable = {{ name = zg361_mg_fairness_input_healthy_exits value = var:zg361_mg_team_healthy_exit_n }}
	zg361_mg_produce_offcycle_signal_effect = yes
	zg361_mg_produce_override_pair_effect = yes
}}

# 035 — freeze only the real ratio override/game-rule producer.  A/B publish a
# fully bound next-cycle policy; C publishes no distribution object.
zg361_mg_m035_freeze_distribution_effect = {{
	{route_prelude("F", 35)}
	{c_route_receipt("F", 35, 1)}
	if = {{
		limit = {{
			var:zg361_case_f_state = 1
			var:zg361_case_f_active = 1
			var:zg361_mg_snapshot_source_serial < var:zg361_mg_snapshot_current_serial
			{receipt_not_current("F", 35, 1)}
		}}
		{business_object_prelude("F", 35, 3501)}
		set_variable = {{ name = zg361_mg_distribution_policy_available value = 0 }}
		remove_variable = zg361_mg_distribution_mode
		remove_variable = zg361_mg_distribution_rule_source
		# source 1 = the manager's 10/5/0 decision override; source 2 = the
		# exact game rule; source 3 = mechanism route B forced strict.
		if = {{
			limit = {{
				var:zg361_mg_m035_route = 1
				has_variable = zg361_ratio_override
				var:zg361_ratio_override = 10
			}}
			set_variable = {{ name = zg361_mg_distribution_mode value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 1 has_variable = zg361_ratio_override var:zg361_ratio_override = 5 }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 2 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 1 has_variable = zg361_ratio_override var:zg361_ratio_override = 0 }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 3 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 1 NOT = {{ has_variable = zg361_ratio_override }} has_game_rule = zg361_ratio_strict }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 2 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 1 NOT = {{ has_variable = zg361_ratio_override }} has_game_rule = zg361_ratio_relaxed }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 2 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 2 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 1 NOT = {{ has_variable = zg361_ratio_override }} has_game_rule = zg361_ratio_off }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 3 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 2 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_m035_route = 2 }}
			set_variable = {{ name = zg361_mg_distribution_mode value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_rule_source value = 3 }}
			set_variable = {{ name = zg361_mg_distribution_policy_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_distribution_review_serial value = var:zg361_case_f_cycle_serial }}
		set_variable = {{ name = zg361_mg_distribution_top_slots value = {{ value = var:zg361_mg_team_n multiply = 0.30 floor = yes }} }}
		set_variable = {{ name = zg361_mg_distribution_bottom_slots value = 0 }}
		if = {{
			limit = {{ var:zg361_mg_distribution_policy_available = 1 var:zg361_mg_distribution_mode = 1 }}
			set_variable = {{ name = zg361_mg_distribution_bottom_slots value = {{ value = var:zg361_mg_team_n multiply = 0.10 floor = yes }} }}
			if = {{ limit = {{ var:zg361_mg_team_n >= 5 }} set_variable = {{ name = zg361_mg_distribution_bottom_slots value = {{ value = var:zg361_mg_distribution_bottom_slots max = 1 }} }} }}
		}}
		else_if = {{
			limit = {{ var:zg361_mg_distribution_policy_available = 1 var:zg361_mg_distribution_mode = 2 }}
			set_variable = {{ name = zg361_mg_distribution_bottom_slots value = {{ value = var:zg361_mg_team_n multiply = 0.05 floor = yes }} }}
		}}
		set_variable = {{
			name = zg361_mg_distribution_middle_slots
			value = {{ value = var:zg361_mg_team_n subtract = var:zg361_mg_distribution_top_slots subtract = var:zg361_mg_distribution_bottom_slots }}
		}}
		set_variable = {{ name = zg361_mg_distribution_bottom_consequence value = 1 }}
		if = {{ limit = {{ var:zg361_mg_distribution_mode = 3 }} set_variable = {{ name = zg361_mg_distribution_bottom_consequence value = 0 }} }}
		set_variable = {{
			name = zg361_mg_distribution_conserved
			value = {{ value = var:zg361_mg_distribution_top_slots add = var:zg361_mg_distribution_middle_slots add = var:zg361_mg_distribution_bottom_slots }}
		}}
		if = {{
			limit = {{ var:zg361_mg_distribution_policy_available = 1 }}
			set_variable = {{ name = zg361_mg_distribution_policy_status value = 1 }}
			set_variable = {{ name = zg361_mg_distribution_policy_owner value = this }}
			set_variable = {{ name = zg361_mg_distribution_policy_subject value = this }}
			set_variable = {{ name = zg361_mg_distribution_policy_source_reviewer value = var:zg361_case_f_owner }}
			set_variable = {{ name = zg361_mg_distribution_policy_source_cycle value = var:zg361_case_f_cycle_serial }}
			set_variable = {{ name = zg361_mg_distribution_policy_source_case value = var:zg361_case_f_case_serial }}
			set_variable = {{ name = zg361_mg_distribution_policy_source_revision value = var:zg361_case_f_revision }}
			set_variable = {{ name = zg361_mg_distribution_policy_input_revision value = var:zg361_mg_team_snapshot_revision }}
			set_variable = {{ name = zg361_mg_distribution_policy_mode value = var:zg361_mg_distribution_mode }}
			set_variable = {{ name = zg361_mg_distribution_policy_rule_source value = var:zg361_mg_distribution_rule_source }}
			set_variable = {{ name = zg361_mg_distribution_policy_due_cycle value = {{ value = var:zg361_case_f_cycle_serial add = 1 }} }}
		}}
		{receipt_call("F", 35, 1)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m035_route = 3 }} {receipt_not_current("F", 35, 1)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 35 }} }}
}}

# 032 — the superior consumes only the previous aggregate team snapshot.  A
# matching Jingcha refusal contributes exactly -50 once and is never inherited
# by a new superior.  The core KPI consumer retains ownership of removing its
# own skipped_jingcha marker.
zg361_mg_m032_score_manager_effect = {{
	{route_prelude("F", 32)}
	{c_route_receipt("F", 32, 1)}
	{f_c_route_followup(32, 1, 101)}
	if = {{
		limit = {{
			var:zg361_case_f_state = 1
			var:zg361_case_f_active = 1
			var:zg361_case_f_subject = this
			var:zg361_mg_snapshot_source_serial < var:zg361_case_f_cycle_serial
			{receipt_current("F", 35, 1)}
			OR = {{
				var:zg361_mg_m035_receipt_choice = 3
				AND = {{
					var:zg361_mg_distribution_policy_available = 1
					var:zg361_mg_distribution_conserved = var:zg361_mg_team_n
				}}
			}}
			{receipt_not_current("F", 32, 1)}
			has_variable = zg361_mg_team_targets
			has_variable = zg361_mg_team_jingcha
			has_variable = zg361_mg_team_calibration
			has_variable = zg361_mg_team_pip_success
			has_variable = zg361_mg_team_appeal_overturn
			has_variable = zg361_mg_team_retention
			has_variable = zg361_mg_team_hc_efficiency
		}}
		{business_object_prelude("F", 32, 3201)}
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
		set_variable = {{ name = zg361_mg_manager_score_mode value = 1 }}
		if = {{
			limit = {{ var:zg361_mg_m032_route = 2 }}
			# Fast punitive route consumes aggregate facts only.  It doubles the
			# appeal/retention penalties without importing any grandchild ID.
			set_variable = {{ name = zg361_mg_manager_score_mode value = 2 }}
			set_variable = {{
				name = zg361_mg_manager_score
				value = {{
					value = var:zg361_mg_team_targets
					add = var:zg361_mg_team_jingcha
					add = var:zg361_mg_team_appeal_overturn
					add = var:zg361_mg_team_appeal_overturn
					add = var:zg361_mg_team_retention
					add = var:zg361_mg_team_retention
				}}
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
					limit = {{ var:zg361_mg_refusal_opinion_exact_superior = var:zg361_case_f_owner var:zg361_mg_refusal_opinion_exact_year = var:zg361_mg_snapshot_mandate_year }}
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
		# Producer for the next official KPI write.  The shared hook adds this
		# value inside organization (component 8), then settles this exact token.
		set_variable = {{ name = zg361_mg_organization_input_status value = 1 }}
		set_variable = {{ name = zg361_mg_organization_input_owner value = var:zg361_case_f_owner }}
		set_variable = {{ name = zg361_mg_organization_input_subject value = this }}
		set_variable = {{ name = zg361_mg_organization_input_source_cycle value = var:zg361_case_f_cycle_serial }}
		set_variable = {{ name = zg361_mg_organization_input_source_case value = var:zg361_case_f_case_serial }}
		set_variable = {{ name = zg361_mg_organization_input_source_revision value = var:zg361_case_f_revision }}
		set_variable = {{ name = zg361_mg_organization_input_revision value = var:zg361_mg_team_snapshot_revision }}
		set_variable = {{ name = zg361_mg_organization_input_component value = 8 }}
		set_variable = {{ name = zg361_mg_organization_input_value value = var:zg361_mg_manager_score }}
		set_variable = {{ name = zg361_mg_organization_input_due_cycle value = {{ value = var:zg361_case_f_cycle_serial add = 1 }} }}
		{receipt_call("F", 32, 1)}
		{transition_call("F", 1)}
		if = {{
			limit = {{ var:zg361_case_f_state = 2 }}
			zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.101 DAYS = 1 }}
		}}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m032_route = 3 }} {receipt_not_current("F", 32, 1)} }} zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 32 }} }}
}}

# 033 — profile weighting produces five bounded, reproducible reason codes.
# Relationship pressure is one explicit code and raises appeal risk; it never
# rewrites frozen KPI evidence.
zg361_mg_m033_reason_code_effect = {{
	{route_prelude("F", 33)}
	{c_route_receipt("F", 33, 2)}
	{f_c_route_followup(33, 2, 102)}
	if = {{
		limit = {{
			var:zg361_case_f_state = 2
			var:zg361_case_f_active = 1
			OR = {{
				var:zg361_mg_m032_receipt_choice = 3
				has_variable = zg361_mg_manager_score
			}}
			{receipt_not_current("F", 33, 2)}
		}}
		{business_object_prelude("F", 33, 3301)}
		set_variable = {{ name = zg361_mg_reason_score_basis value = 0 }}
		set_variable = {{ name = zg361_mg_reason_score_available value = 0 }}
		if = {{
			limit = {{
				NOT = {{ var:zg361_mg_m032_receipt_choice = 3 }}
				has_variable = zg361_mg_manager_score
			}}
			set_variable = {{ name = zg361_mg_reason_score_basis value = var:zg361_mg_manager_score }}
			set_variable = {{ name = zg361_mg_reason_score_available value = 1 }}
		}}
		# A freezes a deterministic evidence profile; B is the one bounded
		# relationship override and preserves before/after plus appeal risk.
		set_variable = {{ name = zg361_mg_profile_code value = 1 }}
		if = {{ limit = {{ var:zg361_mg_team_targets >= 25 }} set_variable = {{ name = zg361_mg_profile_code value = 2 }} }}
		else_if = {{ limit = {{ var:zg361_mg_team_appeal_overturn < 0 }} set_variable = {{ name = zg361_mg_profile_code value = 3 }} }}
		else_if = {{ limit = {{ var:zg361_mg_team_pip_success > 0 }} set_variable = {{ name = zg361_mg_profile_code value = 4 }} }}
		else_if = {{ limit = {{ var:zg361_mg_team_hc_efficiency > 0 }} set_variable = {{ name = zg361_mg_profile_code value = 5 }} }}
		# The frozen profile changes the evidence contribution; it is not a
		# decorative label.  Weights are percentages and remain visible.
		set_variable = {{ name = zg361_mg_profile_weight_calibration value = 100 }}
		set_variable = {{ name = zg361_mg_profile_weight_appeal value = 100 }}
		set_variable = {{ name = zg361_mg_profile_weight_pip value = 90 }}
		set_variable = {{ name = zg361_mg_profile_weight_delivery value = 120 }}
		set_variable = {{ name = zg361_mg_profile_weight_hc value = 90 }}
		if = {{ limit = {{ var:zg361_mg_profile_code = 2 }} set_variable = {{ name = zg361_mg_profile_weight_calibration value = 80 }} set_variable = {{ name = zg361_mg_profile_weight_appeal value = 80 }} set_variable = {{ name = zg361_mg_profile_weight_pip value = 100 }} set_variable = {{ name = zg361_mg_profile_weight_delivery value = 140 }} set_variable = {{ name = zg361_mg_profile_weight_hc value = 100 }} }}
		else_if = {{ limit = {{ var:zg361_mg_profile_code = 3 }} set_variable = {{ name = zg361_mg_profile_weight_calibration value = 110 }} set_variable = {{ name = zg361_mg_profile_weight_appeal value = 130 }} set_variable = {{ name = zg361_mg_profile_weight_pip value = 80 }} set_variable = {{ name = zg361_mg_profile_weight_delivery value = 90 }} set_variable = {{ name = zg361_mg_profile_weight_hc value = 90 }} }}
		else_if = {{ limit = {{ var:zg361_mg_profile_code = 4 }} set_variable = {{ name = zg361_mg_profile_weight_calibration value = 90 }} set_variable = {{ name = zg361_mg_profile_weight_appeal value = 100 }} set_variable = {{ name = zg361_mg_profile_weight_pip value = 130 }} set_variable = {{ name = zg361_mg_profile_weight_delivery value = 80 }} set_variable = {{ name = zg361_mg_profile_weight_hc value = 120 }} }}
		else_if = {{ limit = {{ var:zg361_mg_profile_code = 5 }} set_variable = {{ name = zg361_mg_profile_weight_calibration value = 140 }} set_variable = {{ name = zg361_mg_profile_weight_appeal value = 120 }} set_variable = {{ name = zg361_mg_profile_weight_pip value = 90 }} set_variable = {{ name = zg361_mg_profile_weight_delivery value = 80 }} set_variable = {{ name = zg361_mg_profile_weight_hc value = 70 }} }}
		set_variable = {{ name = zg361_mg_reason_calibration value = {{ value = var:zg361_mg_team_calibration multiply = var:zg361_mg_profile_weight_calibration divide = 100 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_appeal value = {{ value = var:zg361_mg_team_appeal_overturn multiply = var:zg361_mg_profile_weight_appeal divide = 100 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_pip value = {{ value = var:zg361_mg_team_pip_success multiply = var:zg361_mg_profile_weight_pip divide = 100 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_delivery value = {{ value = var:zg361_mg_team_targets multiply = var:zg361_mg_profile_weight_delivery divide = 100 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_hc value = {{ value = var:zg361_mg_team_hc_efficiency multiply = var:zg361_mg_profile_weight_hc divide = 100 max = 25 min = -25 }} }}
		set_variable = {{ name = zg361_mg_reason_relationship_once value = 0 }}
		set_variable = {{ name = zg361_mg_reason_appeal_risk value = 0 }}
		set_variable = {{ name = zg361_mg_reason_before_band value = 2 }}
		if = {{ limit = {{ var:zg361_mg_reason_score_basis < 40 }} set_variable = {{ name = zg361_mg_reason_before_band value = 1 }} }}
		else_if = {{ limit = {{ var:zg361_mg_reason_score_basis >= 75 }} set_variable = {{ name = zg361_mg_reason_before_band value = 3 }} }}
		set_variable = {{ name = zg361_mg_reason_after_band value = var:zg361_mg_reason_before_band }}
		if = {{
			limit = {{ var:zg361_mg_m033_route = 2 }}
			set_variable = {{ name = zg361_mg_reason_relationship_once value = 5 }}
			set_variable = {{ name = zg361_mg_reason_appeal_risk value = 10 }}
			set_variable = {{ name = zg361_mg_reason_after_band value = {{ value = var:zg361_mg_reason_before_band add = 1 max = 3 }} }}
		}}
		set_variable = {{
			name = zg361_mg_reason_total
			value = {{ value = var:zg361_mg_reason_calibration add = var:zg361_mg_reason_appeal add = var:zg361_mg_reason_pip add = var:zg361_mg_reason_delivery add = var:zg361_mg_reason_hc add = var:zg361_mg_reason_relationship_once }}
		}}
		set_variable = {{ name = zg361_mg_reason_weight_version value = var:zg361_case_f_cycle_serial }}
		set_variable = {{ name = zg361_mg_reason_hard_evidence_preserved value = 1 }}
		{receipt_call("F", 33, 2)}
		{transition_call("F", 2)}
		if = {{ limit = {{ var:zg361_case_f_state = 3 }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.102 DAYS = 1 }} }}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m033_route = 3 }} {receipt_not_current("F", 33, 2)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 33 }} }}
}}

# 034 — read-only performance/potential classification.  No KPI, grade, gold,
# treasury, HC, or capacity variable is mutated by this effect.  A manager's
# first review is explicitly unclassified (code 0) but still advances the case;
# otherwise one missing historical sample would deadlock every later review.
zg361_mg_m034_freeze_nine_box_effect = {{
	{route_prelude("F", 34)}
	{c_route_receipt("F", 34, 3)}
	{f_c_route_followup(34, 3, 103)}
	if = {{
		limit = {{
			var:zg361_case_f_state = 3
			var:zg361_case_f_active = 1
			OR = {{
				var:zg361_mg_m032_receipt_choice = 3
				has_variable = zg361_mg_manager_score
			}}
			{receipt_not_current("F", 34, 3)}
		}}
		{business_object_prelude("F", 34, 3401)}
		set_variable = {{ name = zg361_mg_nine_box_score_basis value = 0 }}
		set_variable = {{ name = zg361_mg_nine_box_score_source_available value = 0 }}
		if = {{
			limit = {{
				NOT = {{ var:zg361_mg_m032_receipt_choice = 3 }}
				has_variable = zg361_mg_manager_score
			}}
			set_variable = {{ name = zg361_mg_nine_box_score_basis value = var:zg361_mg_manager_score }}
			set_variable = {{ name = zg361_mg_nine_box_score_source_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_history_score_1 value = var:zg361_mg_nine_box_score_basis }}
		set_variable = {{ name = zg361_mg_history_count value = 1 }}
		set_variable = {{ name = zg361_mg_history_selected value = 0 }}
		set_variable = {{ name = zg361_mg_nine_box_ready value = 0 }}
		set_variable = {{ name = zg361_mg_nine_box_status value = 6 }}
		set_variable = {{ name = zg361_mg_nine_box_code value = 0 }}
		if = {{
			limit = {{ var:zg361_mg_m034_route = 1 var:zg361_mg_nine_box_score_source_available = 1 has_variable = zg361_mg_previous_manager_score has_variable = zg361_mg_previous_manager_score_serial }}
			if = {{
				limit = {{ var:zg361_mg_previous_manager_score_serial < var:zg361_case_f_cycle_serial }}
				set_variable = {{ name = zg361_mg_history_score_2 value = var:zg361_mg_previous_manager_score }}
				set_variable = {{ name = zg361_mg_history_selected value = 1 }}
			}}
		}}
		if = {{
			limit = {{ var:zg361_mg_m034_route = 1 var:zg361_mg_nine_box_score_source_available = 1 var:zg361_mg_history_selected = 0 has_variable = zg361_result_kpi_frozen has_variable = zg361_result_cycle_serial }}
			if = {{
				limit = {{ var:zg361_result_cycle_serial < var:zg361_case_f_cycle_serial }}
				set_variable = {{ name = zg361_mg_history_score_2 value = var:zg361_result_kpi_frozen }}
				set_variable = {{ name = zg361_mg_history_selected value = 1 }}
			}}
		}}
		if = {{
			limit = {{ var:zg361_mg_m034_route = 2 var:zg361_mg_nine_box_score_source_available = 1 }}
			set_variable = {{ name = zg361_mg_history_score_2 value = var:zg361_mg_history_score_1 }}
			set_variable = {{ name = zg361_mg_history_selected value = 1 }}
			set_variable = {{ name = zg361_mg_nine_box_short_sight_risk value = 1 }}
			set_variable = {{ name = zg361_mg_nine_box_expires_cycle value = {{ value = var:zg361_case_f_cycle_serial add = 1 }} }}
		}}
		if = {{
			limit = {{ var:zg361_mg_history_selected = 1 }}
			set_variable = {{ name = zg361_mg_history_count value = 2 }}
			if = {{ limit = {{ var:zg361_mg_m034_route = 2 }} set_variable = {{ name = zg361_mg_history_count value = 1 }} }}
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
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m034_route = 3 }} {receipt_not_current("F", 34, 3)} }} zg361_mg_set_red_effect = {{ CODE = 6 MECHANISM = 34 }} }}
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
	{route_prelude("F", 36)}
	{c_route_receipt("F", 36, 4)}
	{f_c_route_followup(36, 4, None)}
	if = {{
		limit = {{
			var:zg361_case_f_state = 4
			var:zg361_case_f_active = 1
			{receipt_not_current("F", 36, 4)}
		}}
		{business_object_prelude("F", 36, 3601)}
		set_variable = {{ name = zg361_mg_report_manager_score value = 0 }}
		set_variable = {{ name = zg361_mg_report_reason_total value = 0 }}
		set_variable = {{ name = zg361_mg_report_nine_box_code value = 0 }}
		set_variable = {{ name = zg361_mg_report_score_available value = 0 }}
		set_variable = {{ name = zg361_mg_report_reason_available value = 0 }}
		set_variable = {{ name = zg361_mg_report_nine_box_available value = 0 }}
		if = {{ limit = {{ NOT = {{ var:zg361_mg_m032_receipt_choice = 3 }} has_variable = zg361_mg_manager_score }} set_variable = {{ name = zg361_mg_report_manager_score value = var:zg361_mg_manager_score }} set_variable = {{ name = zg361_mg_report_score_available value = 1 }} }}
		if = {{ limit = {{ NOT = {{ var:zg361_mg_m033_receipt_choice = 3 }} has_variable = zg361_mg_reason_total }} set_variable = {{ name = zg361_mg_report_reason_total value = var:zg361_mg_reason_total }} set_variable = {{ name = zg361_mg_report_reason_available value = 1 }} }}
		if = {{ limit = {{ NOT = {{ var:zg361_mg_m034_receipt_choice = 3 }} has_variable = zg361_mg_nine_box_code }} set_variable = {{ name = zg361_mg_report_nine_box_code value = var:zg361_mg_nine_box_code }} set_variable = {{ name = zg361_mg_report_nine_box_available value = 1 }} }}
		if = {{
			limit = {{ var:zg361_mg_m036_route = 2 }}
			set_variable = {{ name = zg361_mg_decade_highlight_only value = 1 }}
			set_variable = {{ name = zg361_mg_decade_history_rows value = 0 }}
			set_variable = {{ name = zg361_mg_decade_causal_warning value = 1 }}
			set_variable = {{ name = zg361_mg_decade_highlight_top value = var:zg361_mg_team_top_n }}
			set_variable = {{ name = zg361_mg_decade_highlight_bottom value = var:zg361_mg_team_bottom_n }}
			{receipt_call("F", 36, 4)}
			{transition_call("F", 4)}
			if = {{
				limit = {{ var:zg361_case_f_state = 5 var:zg361_case_f_active = 0 }}
				if = {{ limit = {{ is_ai = no }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.120 DAYS = 1 }} }}
				else = {{ debug_log = "ZG361MG: eligible AI manager highlight projected silently" }}
			}}
		}}
		else = {{
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
		change_variable = {{ name = zg361_mg_decade_governance_score add = var:zg361_mg_report_manager_score }}
		change_variable = {{ name = zg361_mg_decade_manager_reputation add = var:zg361_mg_report_reason_total }}
		set_variable = {{ name = zg361_mg_decade_bonus_net value = {{ value = var:zg361_mg_decade_bonus_in subtract = var:zg361_mg_decade_bonus_out }} }}
		if = {{
			limit = {{ var:zg361_mg_decade_log_count = 10 }}
			set_variable = {{ name = zg361_mg_decade_report_ready value = 1 }}
			set_variable = {{ name = zg361_mg_decade_report_end_year value = current_year }}
		}}
		if = {{
			limit = {{ var:zg361_mg_report_score_available = 1 }}
			set_variable = {{ name = zg361_mg_previous_manager_score value = var:zg361_mg_report_manager_score }}
			set_variable = {{ name = zg361_mg_previous_manager_score_serial value = var:zg361_case_f_cycle_serial }}
		}}
		{receipt_call("F", 36, 4)}
		{transition_call("F", 4)}
		if = {{
			limit = {{ var:zg361_case_f_state = 5 var:zg361_case_f_active = 0 }}
			if = {{ limit = {{ is_ai = no }} zg361_mg_schedule_f_ticket_effect = {{ EVENT = zg361mg.120 DAYS = 1 }} }}
			else = {{ debug_log = "ZG361MG: eligible AI manager report projected silently" }}
		}}
		}}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m036_route = 3 }} {receipt_not_current("F", 36, 4)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 36 }} }}
}}

# 345 — calendar changes begin only in the next complete review cycle.
zg361_mg_m345_freeze_calendar_effect = {{
	{route_prelude("AK", 345)}
	{c_route_receipt("AK", 345, 1)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 1 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 345, 1)} }}
		{business_object_prelude("AK", 345, 34501)}
		set_variable = {{ name = zg361_mg_calendar_frequency value = 1 }}
		if = {{ limit = {{ var:zg361_mg_m345_route = 2 }} set_variable = {{ name = zg361_mg_calendar_frequency value = 3 }} }}
		set_variable = {{ name = zg361_mg_calendar_effective_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		set_variable = {{ name = zg361_mg_calendar_final_n value = 1 }}
		set_variable = {{ name = zg361_mg_calendar_checkin_n value = 1 }}
		set_variable = {{ name = zg361_mg_calendar_admin_hours value = 20 }}
		set_variable = {{ name = zg361_mg_calendar_feedback_delay_days value = 30 }}
		set_variable = {{ name = zg361_mg_calendar_event_interrupts value = 2 }}
		set_variable = {{ name = zg361_mg_calendar_short_term_bias value = 0 }}
		set_variable = {{ name = zg361_mg_calendar_fatigue value = 0 }}
		set_variable = {{ name = zg361_mg_calendar_player_batch_n value = 1 }}
		set_variable = {{ name = zg361_mg_calendar_ai_batch_n value = 1 }}
		if = {{ limit = {{ var:zg361_mg_calendar_frequency = 3 }} set_variable = {{ name = zg361_mg_calendar_final_n value = 4 }} set_variable = {{ name = zg361_mg_calendar_checkin_n value = 0 }} set_variable = {{ name = zg361_mg_calendar_admin_hours value = 72 }} set_variable = {{ name = zg361_mg_calendar_feedback_delay_days value = 7 }} set_variable = {{ name = zg361_mg_calendar_event_interrupts value = 8 }} set_variable = {{ name = zg361_mg_calendar_short_term_bias value = 25 }} set_variable = {{ name = zg361_mg_calendar_fatigue value = 30 }} set_variable = {{ name = zg361_mg_calendar_player_batch_n value = 4 }} set_variable = {{ name = zg361_mg_calendar_ai_batch_n value = 4 }} }}
		set_variable = {{ name = zg361_mg_calendar_player_ai_batch value = 1 }}
		{receipt_call("AK", 345, 1)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m345_route = 3 }} {receipt_not_current("AK", 345, 1)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 345 }} }}
}}

# The frozen team snapshot is the only producer.  It emits at most one actual
# material signal, with appeal overturn > PIP graduation > calibration change.
zg361_mg_produce_offcycle_signal_effect = {{
	if = {{
		limit = {{
			zg361_is_celestial_liege_trigger = yes
			OR = {{
				NOT = {{ has_variable = zg361_mg_offcycle_input_status }}
				NOT = {{ var:zg361_mg_offcycle_input_status = 1 }}
			}}
			OR = {{
				var:zg361_mg_team_overturn_n > 0
				var:zg361_mg_team_pip_success > 0
				var:zg361_mg_team_calibration < 0
			}}
		}}
		set_variable = {{ name = zg361_mg_offcycle_pending value = 1 }}
		set_variable = {{ name = zg361_mg_offcycle_input_status value = 1 }}
		set_variable = {{ name = zg361_mg_offcycle_input_revision value = var:zg361_mg_team_snapshot_revision }}
		set_variable = {{ name = zg361_mg_offcycle_source_owner value = root }}
		set_variable = {{ name = zg361_mg_offcycle_source_subject value = this }}
		set_variable = {{ name = zg361_mg_offcycle_source_cycle value = var:zg361_review_serial }}
		set_variable = {{ name = zg361_mg_offcycle_source_case value = var:zg361_case_f_case_serial }}
		set_variable = {{ name = zg361_mg_offcycle_materiality value = 50 }}
		set_variable = {{ name = zg361_mg_offcycle_action value = 3 }}
		if = {{ limit = {{ var:zg361_mg_team_pip_success > 0 }} set_variable = {{ name = zg361_mg_offcycle_materiality value = 75 }} set_variable = {{ name = zg361_mg_offcycle_action value = 2 }} }}
		if = {{ limit = {{ var:zg361_mg_team_overturn_n > 0 }} set_variable = {{ name = zg361_mg_offcycle_materiality value = 100 }} set_variable = {{ name = zg361_mg_offcycle_action value = 1 }} }}
		set_variable = {{ name = zg361_mg_offcycle_signal_serial value = var:zg361_mg_team_snapshot_revision }}
		set_variable = {{ name = zg361_mg_offcycle_recorded_year value = current_year }}
	}}
}}

zg361_mg_m346_consume_offcycle_signal_effect = {{
	{route_prelude("AK", 346)}
	{c_route_receipt("AK", 346, 1)}
	if = {{
		limit = {{ var:zg361_mg_m346_route = 3 {receipt_current("AK", 346, 1)} has_variable = zg361_mg_offcycle_input_status var:zg361_mg_offcycle_input_status = 1 }}
		set_variable = {{ name = zg361_mg_offcycle_input_status value = 3 }}
		set_variable = {{ name = zg361_mg_offcycle_pending value = 0 }}
		set_variable = {{ name = zg361_mg_offcycle_discarded_cycle value = var:zg361_case_ak_cycle_serial }}
	}}
	if = {{
		limit = {{ var:zg361_case_ak_state = 1 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 346, 1)} }}
		{business_object_prelude("AK", 346, 34601)}
		set_variable = {{ name = zg361_mg_offcycle_consumed value = 0 }}
		set_variable = {{ name = zg361_mg_offcycle_cohort_reruns value = 0 }}
		set_variable = {{ name = zg361_mg_offcycle_original_board_preserved value = 1 }}
		set_variable = {{ name = zg361_mg_offcycle_disruption value = 0 }}
		set_variable = {{ name = zg361_mg_offcycle_recency_bias value = 0 }}
		if = {{ limit = {{ var:zg361_mg_m346_route = 2 }} set_variable = {{ name = zg361_mg_offcycle_cohort_reruns value = 1 }} set_variable = {{ name = zg361_mg_offcycle_disruption value = 20 }} set_variable = {{ name = zg361_mg_offcycle_recency_bias value = 15 }} }}
		if = {{
			limit = {{
				has_variable = zg361_mg_offcycle_input_status
				var:zg361_mg_offcycle_input_status = 1
				has_variable = zg361_mg_offcycle_pending
				var:zg361_mg_offcycle_pending = 1
				has_variable = zg361_mg_offcycle_source_owner
				has_variable = zg361_mg_offcycle_source_subject
				var:zg361_mg_offcycle_source_owner = var:zg361_case_ak_owner
				var:zg361_mg_offcycle_source_subject = this
				has_variable = zg361_mg_offcycle_materiality
				var:zg361_mg_offcycle_materiality >= 50
			}}
			set_variable = {{ name = zg361_mg_offcycle_consumed value = 1 }}
			set_variable = {{ name = zg361_mg_offcycle_consumed_cycle value = var:zg361_case_ak_cycle_serial }}
			set_variable = {{ name = zg361_mg_offcycle_consumed_source_cycle value = var:zg361_mg_offcycle_source_cycle }}
			set_variable = {{ name = zg361_mg_offcycle_consumed_source_case value = var:zg361_mg_offcycle_source_case }}
			set_variable = {{ name = zg361_mg_offcycle_consumed_input_revision value = var:zg361_mg_offcycle_input_revision }}
			set_variable = {{ name = zg361_mg_offcycle_settlement_receipt value = var:zg361_mg_offcycle_source_case }}
			set_variable = {{ name = zg361_mg_offcycle_input_status value = 2 }}
			set_variable = {{ name = zg361_mg_offcycle_pending value = 0 }}
		}}
		{receipt_call("AK", 346, 1)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m346_route = 3 }} {receipt_not_current("AK", 346, 1)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 346 }} }}
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

# Reconstruct one real calibration swap from the frozen result producer.  The
# beneficiary was lifted (reason 2/4); the bearer was pushed (reason 1/3).
zg361_mg_produce_override_pair_effect = {{
	if = {{
		limit = {{
			OR = {{
				NOT = {{ has_variable = zg361_mg_override_input_status }}
				NOT = {{ var:zg361_mg_override_input_status = 1 }}
			}}
		}}
		remove_variable = zg361_mg_override_pending_beneficiary
		remove_variable = zg361_mg_override_pending_bearer
		remove_variable = zg361_mg_override_source_beneficiary_case
		remove_variable = zg361_mg_override_source_bearer_case
		save_scope_as = zg361_mg_override_manager
		ordered_vassal = {{
			limit = {{
				has_variable = zg361_result_case_owner
				has_variable = zg361_result_cycle_serial
				has_variable = zg361_result_case_serial
				has_variable = zg361_result_grade_reason
				var:zg361_result_case_owner = scope:zg361_mg_override_manager
				var:zg361_result_cycle_serial = scope:zg361_mg_override_manager.var:zg361_review_serial
				OR = {{ var:zg361_result_grade_reason = 2 var:zg361_result_grade_reason = 4 }}
			}}
			order_by = age
			position = 0
			save_temporary_scope_as = zg361_mg_override_beneficiary_candidate
			scope:zg361_mg_override_manager = {{
				set_variable = {{ name = zg361_mg_override_pending_beneficiary value = scope:zg361_mg_override_beneficiary_candidate }}
				set_variable = {{ name = zg361_mg_override_source_beneficiary_case value = scope:zg361_mg_override_beneficiary_candidate.var:zg361_result_case_serial }}
				set_variable = {{ name = zg361_mg_override_beneficiary_reason value = scope:zg361_mg_override_beneficiary_candidate.var:zg361_result_grade_reason }}
			}}
		}}
		ordered_vassal = {{
			limit = {{
				has_variable = zg361_result_case_owner
				has_variable = zg361_result_cycle_serial
				has_variable = zg361_result_case_serial
				has_variable = zg361_result_grade_reason
				var:zg361_result_case_owner = scope:zg361_mg_override_manager
				var:zg361_result_cycle_serial = scope:zg361_mg_override_manager.var:zg361_review_serial
				OR = {{ var:zg361_result_grade_reason = 1 var:zg361_result_grade_reason = 3 }}
			}}
			order_by = age
			position = 0
			save_temporary_scope_as = zg361_mg_override_bearer_candidate
			scope:zg361_mg_override_manager = {{
				set_variable = {{ name = zg361_mg_override_pending_bearer value = scope:zg361_mg_override_bearer_candidate }}
				set_variable = {{ name = zg361_mg_override_source_bearer_case value = scope:zg361_mg_override_bearer_candidate.var:zg361_result_case_serial }}
				set_variable = {{ name = zg361_mg_override_bearer_reason value = scope:zg361_mg_override_bearer_candidate.var:zg361_result_grade_reason }}
			}}
		}}
		if = {{
			limit = {{
				has_variable = zg361_mg_override_pending_beneficiary
				has_variable = zg361_mg_override_pending_bearer
				NOT = {{ var:zg361_mg_override_pending_beneficiary = var:zg361_mg_override_pending_bearer }}
			}}
			set_variable = {{ name = zg361_mg_override_pending value = 1 }}
			set_variable = {{ name = zg361_mg_override_input_status value = 1 }}
			set_variable = {{ name = zg361_mg_override_input_revision value = var:zg361_mg_team_snapshot_revision }}
			set_variable = {{ name = zg361_mg_override_source_owner value = root }}
			set_variable = {{ name = zg361_mg_override_source_subject value = this }}
			set_variable = {{ name = zg361_mg_override_source_cycle value = var:zg361_review_serial }}
			set_variable = {{ name = zg361_mg_override_pending_reason value = {{ value = var:zg361_mg_override_beneficiary_reason multiply = 10 add = var:zg361_mg_override_bearer_reason }} }}
		}}
	}}
}}

# 347 — one bounded override records beneficiary, bearer and reason while the
# frozen ranking multiset and quota counts remain unchanged.
zg361_mg_m347_consume_override_effect = {{
	{route_prelude("AK", 347)}
	{c_route_receipt("AK", 347, 2)}
	if = {{
		limit = {{ var:zg361_mg_m347_route = 3 {receipt_current("AK", 347, 2)} has_variable = zg361_mg_override_input_status var:zg361_mg_override_input_status = 1 }}
		set_variable = {{ name = zg361_mg_override_input_status value = 3 }}
		set_variable = {{ name = zg361_mg_override_pending value = 0 }}
		set_variable = {{ name = zg361_mg_override_discarded_cycle value = var:zg361_case_ak_cycle_serial }}
	}}
	if = {{
		limit = {{ var:zg361_case_ak_state = 2 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 347, 2)} }}
		{business_object_prelude("AK", 347, 34701)}
		set_variable = {{ name = zg361_mg_override_budget value = 2 }}
		if = {{ limit = {{ var:zg361_mg_m347_route = 2 }} set_variable = {{ name = zg361_mg_override_budget value = 999 }} }}
		set_variable = {{ name = zg361_mg_override_used value = 0 }}
		set_variable = {{ name = zg361_mg_override_uncapped value = 0 }}
		set_variable = {{ name = zg361_mg_override_appeal_risk value = 0 }}
		if = {{ limit = {{ var:zg361_mg_m347_route = 2 }} set_variable = {{ name = zg361_mg_override_uncapped value = 1 }} set_variable = {{ name = zg361_mg_override_appeal_risk value = 10 }} }}
		set_variable = {{ name = zg361_mg_override_applied value = 0 }}
		set_variable = {{ name = zg361_mg_override_quota_before value = var:zg361_mg_team_n }}
		if = {{
			limit = {{
				has_variable = zg361_mg_override_input_status
				var:zg361_mg_override_input_status = 1
				has_variable = zg361_mg_override_pending
				var:zg361_mg_override_pending = 1
				has_variable = zg361_mg_override_source_owner
				has_variable = zg361_mg_override_source_subject
				var:zg361_mg_override_source_owner = var:zg361_case_ak_owner
				var:zg361_mg_override_source_subject = this
				has_variable = zg361_mg_override_pending_beneficiary
				has_variable = zg361_mg_override_pending_bearer
				has_variable = zg361_mg_override_pending_reason
				NOT = {{ var:zg361_mg_override_pending_beneficiary = var:zg361_mg_override_pending_bearer }}
				var:zg361_mg_override_used < var:zg361_mg_override_budget
			}}
			change_variable = {{ name = zg361_mg_override_used add = 1 }}
			set_variable = {{ name = zg361_mg_override_applied value = 1 }}
			set_variable = {{ name = zg361_mg_override_beneficiary value = var:zg361_mg_override_pending_beneficiary }}
			set_variable = {{ name = zg361_mg_override_bearer value = var:zg361_mg_override_pending_bearer }}
			set_variable = {{ name = zg361_mg_override_reason value = var:zg361_mg_override_pending_reason }}
			set_variable = {{ name = zg361_mg_override_consumed_source_cycle value = var:zg361_mg_override_source_cycle }}
			set_variable = {{ name = zg361_mg_override_consumed_beneficiary_case value = var:zg361_mg_override_source_beneficiary_case }}
			set_variable = {{ name = zg361_mg_override_consumed_bearer_case value = var:zg361_mg_override_source_bearer_case }}
			set_variable = {{ name = zg361_mg_override_consumed_input_revision value = var:zg361_mg_override_input_revision }}
			set_variable = {{ name = zg361_mg_override_settlement_receipt value = var:zg361_case_ak_case_serial }}
			set_variable = {{ name = zg361_mg_override_input_status value = 2 }}
			set_variable = {{ name = zg361_mg_override_pending value = 0 }}
		}}
		set_variable = {{ name = zg361_mg_override_quota_after value = var:zg361_mg_team_n }}
		set_variable = {{ name = zg361_mg_override_quota_neutral value = 1 }}
		if = {{ limit = {{ NOT = {{ var:zg361_mg_override_quota_before = var:zg361_mg_override_quota_after }} }} set_variable = {{ name = zg361_mg_override_quota_neutral value = 0 }} }}
		set_variable = {{ name = zg361_mg_override_algorithmic_version value = var:zg361_case_ak_cycle_serial }}
		set_variable = {{ name = zg361_mg_override_final_version value = {{ value = var:zg361_case_ak_cycle_serial multiply = 100 add = var:zg361_mg_override_used }} }}
		set_variable = {{ name = zg361_mg_override_outcome_pending value = var:zg361_mg_override_applied }}
		{receipt_call("AK", 347, 2)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m347_route = 3 }} {receipt_not_current("AK", 347, 2)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 347 }} }}
}}

# 348 — the exception token binds owner/subject/cycle/case/state/expiry.  Its
# independent due event can renew only with new evidence; stale copies no-op.
zg361_mg_m348_bind_exception_effect = {{
	{route_prelude("AK", 348)}
	{c_route_receipt("AK", 348, 2)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 2 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 348, 2)} }}
		{business_object_prelude("AK", 348, 34801)}
		set_variable = {{ name = zg361_mg_exception_owner value = var:zg361_case_ak_owner }}
		set_variable = {{ name = zg361_mg_exception_subject value = this }}
		set_variable = {{ name = zg361_mg_exception_cycle value = var:zg361_case_ak_cycle_serial }}
		set_variable = {{ name = zg361_mg_exception_case value = var:zg361_case_ak_case_serial }}
		set_variable = {{ name = zg361_mg_exception_state value = 1 }}
		set_variable = {{ name = zg361_mg_exception_grandfathered value = 0 }}
		set_variable = {{ name = zg361_mg_exception_history_preserved value = 1 }}
		set_variable = {{ name = zg361_mg_exception_expiry_year value = {{ value = current_year add = 1 }} }}
		set_variable = {{ name = zg361_mg_exception_pending value = 1 }}
		set_variable = {{ name = zg361_mg_exception_new_evidence value = 0 }}
		if = {{
			limit = {{ var:zg361_mg_m348_route = 2 }}
			set_variable = {{ name = zg361_mg_exception_grandfathered value = 1 }}
			set_variable = {{ name = zg361_mg_exception_pending value = 0 }}
			remove_variable = zg361_mg_exception_expiry_year
		}}
		else = {{
			save_scope_as = zg361_mg_exception_ticket_subject
			var:zg361_case_ak_owner = {{ save_scope_as = zg361_mg_exception_ticket_owner }}
			save_scope_value_as = {{ name = zg361_mg_exception_ticket_cycle value = var:zg361_case_ak_cycle_serial }}
			save_scope_value_as = {{ name = zg361_mg_exception_ticket_case value = var:zg361_case_ak_case_serial }}
			save_scope_value_as = {{ name = zg361_mg_exception_ticket_state value = 1 }}
			save_scope_value_as = {{ name = zg361_mg_exception_ticket_expiry value = var:zg361_mg_exception_expiry_year }}
			trigger_event = {{ id = zg361mg.250 days = 365 }}
		}}
		{receipt_call("AK", 348, 2)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m348_route = 3 }} {receipt_not_current("AK", 348, 2)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 348 }} }}
}}

zg361_mg_ak_stage_2_effect = {{
	zg361_mg_m347_consume_override_effect = yes
	zg361_mg_m348_bind_exception_effect = yes
	if = {{
		limit = {{
			{receipt_current("AK", 347, 2)}
			{receipt_current("AK", 348, 2)}
			OR = {{
				var:zg361_mg_m347_receipt_choice = 3
				var:zg361_mg_override_quota_neutral = 1
			}}
		}}
		{transition_call("AK", 2)}
		if = {{ limit = {{ var:zg361_case_ak_state = 3 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.202 DAYS = 30 }} }}
	}}
}}

# 349 uses administrative capacity, not gold.  Therefore no treasury/personal
# charge is applicable in this 15-ID slice.  Capacity follows reserve -> settle
# and has an explicit guarded refund path.
zg361_mg_m349_run_audit_effect = {{
	{route_prelude("AK", 349)}
	{c_route_receipt("AK", 349, 3)}
	if = {{
		limit = {{
			var:zg361_case_ak_state = 3
			var:zg361_case_ak_active = 1
			has_variable = zg361_mg_admin_capacity_available
			{receipt_not_current("AK", 349, 3)}
		}}
		{business_object_prelude("AK", 349, 34901)}
		set_variable = {{ name = zg361_mg_audit_population value = {{ value = var:zg361_mg_team_n max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_rate value = 20 }}
		if = {{ limit = {{ var:zg361_mg_m349_route = 2 }} set_variable = {{ name = zg361_mg_audit_rate value = 5 }} }}
		set_variable = {{ name = zg361_mg_audit_effective_rate value = {{ value = var:zg361_mg_audit_rate subtract = 5 max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_sample_n value = {{ value = var:zg361_mg_audit_population multiply = var:zg361_mg_audit_effective_rate divide = 100 floor = yes max = 1 }} }}
		set_variable = {{ name = zg361_mg_audit_seed value = {{ value = var:zg361_case_ak_cycle_serial multiply = 1000 add = var:zg361_case_ak_case_serial }} }}
		set_variable = {{ name = zg361_mg_audit_high_risk_n value = {{ value = var:zg361_mg_team_bottom_n max = 1 min = var:zg361_mg_audit_sample_n }} }}
		if = {{ limit = {{ var:zg361_mg_m349_route = 2 }} set_variable = {{ name = zg361_mg_audit_high_risk_n value = 0 }} }}
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
				set_variable = {{ name = zg361_mg_audit_closed value = 1 }}
				set_variable = {{ name = zg361_mg_audit_method value = 1 }}
				set_variable = {{ name = zg361_mg_audit_severe_penalty_risk value = 0 }}
				if = {{ limit = {{ var:zg361_mg_m349_route = 2 }} set_variable = {{ name = zg361_mg_audit_method value = 2 }} set_variable = {{ name = zg361_mg_audit_severe_penalty_risk value = 1 }} }}
				if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_policy_trust }} }} set_variable = {{ name = zg361_mg_policy_trust value = 0 }} }}
				if = {{ limit = {{ var:zg361_mg_m349_route = 1 }} change_variable = {{ name = zg361_mg_policy_trust add = var:zg361_mg_audit_clean }} }}
				# A completed reproducible audit is the sole remediation producer.
				if = {{
					limit = {{
						var:zg361_mg_m349_route = 1
						has_variable = zg361_mg_fairness_remediation_status
						var:zg361_mg_fairness_remediation_status = 1
						has_variable = zg361_mg_fairness_remediation_owner
						has_variable = zg361_mg_fairness_remediation_subject
						var:zg361_mg_fairness_remediation_owner = var:zg361_case_ak_owner
						var:zg361_mg_fairness_remediation_subject = this
						has_variable = zg361_mg_fairness_remediation_due_cycle
						var:zg361_mg_fairness_remediation_due_cycle <= var:zg361_case_ak_cycle_serial
					}}
					set_variable = {{ name = zg361_mg_fairness_remediation_status value = 2 }}
					set_variable = {{ name = zg361_mg_fairness_remediation_completed_cycle value = var:zg361_case_ak_cycle_serial }}
					set_variable = {{ name = zg361_mg_fairness_remediation_completed_case value = var:zg361_case_ak_case_serial }}
					set_variable = {{ name = zg361_mg_fairness_remediation_completed_revision value = var:zg361_mg_fairness_remediation_revision }}
					set_variable = {{ name = zg361_mg_fairness_remediation_completion_receipt value = var:zg361_mg_fairness_remediation_plan_id }}
				}}
				{receipt_call("AK", 349, 3)}
			}}
		}}
		else = {{ zg361_mg_set_red_effect = {{ CODE = 5 MECHANISM = 349 }} }}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m349_route = 3 }} {receipt_not_current("AK", 349, 3)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 349 }} }}
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
	{route_prelude("AK", 350)}
	{c_route_receipt("AK", 350, 3)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 3 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 350, 3)} }}
		{business_object_prelude("AK", 350, 35001)}
		set_variable = {{ name = zg361_mg_benchmark_score_basis value = 0 }}
		set_variable = {{ name = zg361_mg_benchmark_history_score_available value = 0 }}
		if = {{
			limit = {{
				has_variable = zg361_mg_m032_receipt_choice
				NOT = {{ var:zg361_mg_m032_receipt_choice = 3 }}
				has_variable = zg361_mg_manager_score
			}}
			set_variable = {{ name = zg361_mg_benchmark_score_basis value = var:zg361_mg_manager_score }}
			set_variable = {{ name = zg361_mg_benchmark_history_score_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_benchmark_effective_cycle_basis value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		set_variable = {{ name = zg361_mg_benchmark_calendar_source_available value = 0 }}
		if = {{
			limit = {{
				has_variable = zg361_mg_m345_receipt_choice
				NOT = {{ var:zg361_mg_m345_receipt_choice = 3 }}
				has_variable = zg361_mg_calendar_effective_cycle
			}}
			set_variable = {{ name = zg361_mg_benchmark_effective_cycle_basis value = var:zg361_mg_calendar_effective_cycle }}
			set_variable = {{ name = zg361_mg_benchmark_calendar_source_available value = 1 }}
		}}
		if = {{ limit = {{ NOT = {{ has_variable = zg361_mg_benchmark_old_version }} }} set_variable = {{ name = zg361_mg_benchmark_old_version value = 1 }} }}
		set_variable = {{ name = zg361_mg_benchmark_history_value value = var:zg361_mg_benchmark_score_basis }}
		set_variable = {{ name = zg361_mg_benchmark_history_formula value = 1 }}
		set_variable = {{ name = zg361_mg_benchmark_history_version value = var:zg361_mg_benchmark_old_version }}
		set_variable = {{ name = zg361_mg_benchmark_new_version value = {{ value = var:zg361_mg_benchmark_old_version add = 1 }} }}
		set_variable = {{ name = zg361_mg_benchmark_effective_cycle value = var:zg361_mg_benchmark_effective_cycle_basis }}
		set_variable = {{ name = zg361_mg_benchmark_top_threshold value = 75 }}
		set_variable = {{ name = zg361_mg_benchmark_middle_threshold value = 40 }}
		set_variable = {{ name = zg361_mg_benchmark_inflation_index value = {{ value = var:zg361_mg_team_top_n multiply = 100 divide = {{ value = var:zg361_mg_team_n max = 1 }} }} }}
		set_variable = {{ name = zg361_mg_benchmark_ratchet_risk value = 0 }}
		set_variable = {{ name = zg361_mg_benchmark_explanation_code value = 35001 }}
		if = {{
			limit = {{ var:zg361_mg_m350_route = 2 }}
			set_variable = {{ name = zg361_mg_benchmark_top_growth value = {{ value = var:zg361_mg_benchmark_inflation_index subtract = 30 max = 0 }} }}
			change_variable = {{ name = zg361_mg_benchmark_top_threshold add = var:zg361_mg_benchmark_top_growth }}
			change_variable = {{ name = zg361_mg_benchmark_middle_threshold add = var:zg361_mg_benchmark_top_growth }}
			set_variable = {{ name = zg361_mg_benchmark_ratchet_risk value = var:zg361_mg_benchmark_top_growth }}
			set_variable = {{ name = zg361_mg_benchmark_explanation_code value = 35002 }}
		}}
		set_variable = {{ name = zg361_mg_benchmark_history_rewritten value = 0 }}
		{receipt_call("AK", 350, 3)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m350_route = 3 }} {receipt_not_current("AK", 350, 3)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 350 }} }}
}}

zg361_mg_ak_stage_3_effect = {{
	zg361_mg_m349_run_audit_effect = yes
	zg361_mg_m350_version_benchmark_effect = yes
	if = {{
		limit = {{
			{receipt_current("AK", 349, 3)}
			{receipt_current("AK", 350, 3)}
			OR = {{
				var:zg361_mg_m349_receipt_choice = 3
				var:zg361_mg_audit_settled = 1
			}}
		}}
		{transition_call("AK", 3)}
		if = {{ limit = {{ var:zg361_case_ak_state = 4 }} zg361_mg_schedule_ak_ticket_effect = {{ EVENT = zg361mg.203 DAYS = 180 }} }}
	}}
}}

# 351 — deterministic first/second ordered direct regions become disjoint pilot
# and control cells.  Differences are computed only when both frozen outcomes
# and all preregistered metrics exist.
zg361_mg_m351_measure_pilot_effect = {{
	{route_prelude("AK", 351)}
	{c_route_receipt("AK", 351, 4)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 4 var:zg361_case_ak_active = 1 {receipt_not_current("AK", 351, 4)} }}
		{business_object_prelude("AK", 351, 35101)}
		set_variable = {{ name = zg361_mg_pilot_metric_n value = 3 }}
		set_variable = {{ name = zg361_mg_pilot_result_ready value = 0 }}
		set_variable = {{ name = zg361_mg_pilot_preregistered value = 1 }}
		set_variable = {{ name = zg361_mg_pilot_decision_threshold value = 5 }}
		save_scope_as = zg361_mg_pilot_manager
		if = {{
			limit = {{ var:zg361_mg_m351_route = 1 }}
			ordered_vassal = {{
				limit = {{ zg361_is_reviewable_vassal_trigger = yes has_variable = zg361_result_kpi_frozen }}
				order_by = age
				position = 0
				save_temporary_scope_as = zg361_mg_pilot_region_candidate
				scope:zg361_mg_pilot_manager = {{ set_variable = {{ name = zg361_mg_pilot_region value = scope:zg361_mg_pilot_region_candidate }} set_variable = {{ name = zg361_mg_pilot_outcome value = scope:zg361_mg_pilot_region_candidate.var:zg361_result_kpi_frozen }} }}
			}}
			ordered_vassal = {{
				limit = {{ zg361_is_reviewable_vassal_trigger = yes has_variable = zg361_result_kpi_frozen }}
				order_by = age
				position = 1
				save_temporary_scope_as = zg361_mg_control_region_candidate
				scope:zg361_mg_pilot_manager = {{ set_variable = {{ name = zg361_mg_control_region value = scope:zg361_mg_control_region_candidate }} set_variable = {{ name = zg361_mg_control_outcome value = scope:zg361_mg_control_region_candidate.var:zg361_result_kpi_frozen }} }}
			}}
		}}
		else = {{
			set_variable = {{ name = zg361_mg_pilot_full_realm_rollout value = 1 }}
			set_variable = {{ name = zg361_mg_pilot_causal_comparison value = 0 }}
			set_variable = {{ name = zg361_mg_pilot_migration_risk value = 20 }}
			set_variable = {{ name = zg361_mg_pilot_region_n value = 0 }}
			every_vassal = {{ limit = {{ zg361_is_reviewable_vassal_trigger = yes }} scope:zg361_mg_pilot_manager = {{ change_variable = {{ name = zg361_mg_pilot_region_n add = 1 }} }} }}
			set_variable = {{ name = zg361_mg_pilot_result_ready value = 1 }}
		}}
		if = {{
			limit = {{ has_variable = zg361_mg_pilot_region has_variable = zg361_mg_control_region NOT = {{ var:zg361_mg_pilot_region = var:zg361_mg_control_region }} has_variable = zg361_mg_pilot_outcome has_variable = zg361_mg_control_outcome }}
			set_variable = {{ name = zg361_mg_pilot_difference value = {{ value = var:zg361_mg_pilot_outcome subtract = var:zg361_mg_control_outcome }} }}
			set_variable = {{ name = zg361_mg_pilot_result_ready value = 1 }}
			set_variable = {{ name = zg361_mg_pilot_causal_comparison value = 1 }}
			set_variable = {{ name = zg361_mg_pilot_decision value = 2 }}
			if = {{ limit = {{ var:zg361_mg_pilot_difference >= var:zg361_mg_pilot_decision_threshold }} set_variable = {{ name = zg361_mg_pilot_decision value = 1 }} }}
		}}
		set_variable = {{ name = zg361_mg_pilot_end_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		{receipt_call("AK", 351, 4)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m351_route = 3 }} {receipt_not_current("AK", 351, 4)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 351 }} }}
}}

# 352 — original value/formula/policy version are separate immutable fields;
# comparable mapping or a new-series break never overwrites them.
zg361_mg_m352_map_history_effect = {{
	{route_prelude("AK", 352)}
	{c_route_receipt("AK", 352, 4)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 4 var:zg361_case_ak_active = 1 {receipt_current("AK", 350, 3)} {receipt_not_current("AK", 352, 4)} }}
		{business_object_prelude("AK", 352, 35201)}
		set_variable = {{ name = zg361_mg_history_source_available value = 0 }}
		set_variable = {{ name = zg361_mg_history_source_deferred value = 0 }}
		if = {{ limit = {{ var:zg361_mg_m350_receipt_choice = 3 }} set_variable = {{ name = zg361_mg_history_source_deferred value = 1 }} }}
		set_variable = {{ name = zg361_mg_history_original_value value = 0 }}
		set_variable = {{ name = zg361_mg_history_original_formula value = 0 }}
		set_variable = {{ name = zg361_mg_history_original_policy_version value = 0 }}
		set_variable = {{ name = zg361_mg_history_mapping_version value = var:zg361_case_ak_cycle_serial }}
		set_variable = {{ name = zg361_mg_history_new_series value = 1 }}
		set_variable = {{ name = zg361_mg_history_original_archive_preserved value = 0 }}
		set_variable = {{ name = zg361_mg_history_mapping_mode value = 0 }}
		set_variable = {{ name = zg361_mg_history_mapped_value value = 0 }}
		set_variable = {{ name = zg361_mg_history_contamination_risk value = 0 }}
		if = {{
			limit = {{
				NOT = {{ var:zg361_mg_m350_receipt_choice = 3 }}
				has_variable = zg361_mg_benchmark_history_score_available
				var:zg361_mg_benchmark_history_score_available = 1
				has_variable = zg361_mg_benchmark_history_value
				has_variable = zg361_mg_benchmark_history_formula
				has_variable = zg361_mg_benchmark_history_version
				has_variable = zg361_mg_benchmark_new_version
			}}
			set_variable = {{ name = zg361_mg_history_source_available value = 1 }}
			set_variable = {{ name = zg361_mg_history_original_value value = var:zg361_mg_benchmark_history_value }}
			set_variable = {{ name = zg361_mg_history_original_formula value = var:zg361_mg_benchmark_history_formula }}
			set_variable = {{ name = zg361_mg_history_original_policy_version value = var:zg361_mg_benchmark_history_version }}
			set_variable = {{ name = zg361_mg_history_mapping_version value = var:zg361_mg_benchmark_new_version }}
			set_variable = {{ name = zg361_mg_history_new_series value = 0 }}
			set_variable = {{ name = zg361_mg_history_original_archive_preserved value = 1 }}
			set_variable = {{ name = zg361_mg_history_mapping_mode value = 1 }}
			set_variable = {{ name = zg361_mg_history_mapped_value value = var:zg361_mg_history_original_value }}
		}}
		if = {{
			limit = {{ var:zg361_mg_m352_route = 2 var:zg361_mg_history_source_available = 1 }}
			set_variable = {{ name = zg361_mg_history_mapping_mode value = 2 }}
			set_variable = {{ name = zg361_mg_history_latest_formula_value value = {{ value = var:zg361_mg_history_original_value add = var:zg361_mg_benchmark_top_threshold subtract = 75 }} }}
			set_variable = {{ name = zg361_mg_history_mapped_value value = var:zg361_mg_history_latest_formula_value }}
			set_variable = {{ name = zg361_mg_history_audit_diff value = {{ value = var:zg361_mg_history_mapped_value subtract = var:zg361_mg_history_original_value }} }}
			set_variable = {{ name = zg361_mg_history_contamination_risk value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_history_appeal_ref value = var:zg361_mg_m352_object_id }}
		set_variable = {{ name = zg361_mg_history_promotion_ref value = var:zg361_mg_m352_object_id }}
		set_variable = {{ name = zg361_mg_history_decade_ref value = var:zg361_mg_m352_object_id }}
		{receipt_call("AK", 352, 4)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m352_route = 3 }} {receipt_not_current("AK", 352, 4)} }} zg361_mg_set_red_effect = {{ CODE = 4 MECHANISM = 352 }} }}
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
	{route_prelude("AK", 353)}
	{c_route_receipt("AK", 353, 5)}
	if = {{
		limit = {{ var:zg361_case_ak_state = 5 var:zg361_case_ak_active = 1 has_variable = zg361_mg_admin_capacity_available {receipt_not_current("AK", 353, 5)} }}
		{business_object_prelude("AK", 353, 35301)}
		set_variable = {{ name = zg361_mg_admin_calendar_basis value = 0 }}
		set_variable = {{ name = zg361_mg_admin_calendar_source_available value = 0 }}
		if = {{
			limit = {{
				has_variable = zg361_mg_m345_receipt_choice
				NOT = {{ var:zg361_mg_m345_receipt_choice = 3 }}
				has_variable = zg361_mg_calendar_final_n
			}}
			set_variable = {{ name = zg361_mg_admin_calendar_basis value = var:zg361_mg_calendar_final_n }}
			set_variable = {{ name = zg361_mg_admin_calendar_source_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_admin_offcycle_basis value = 0 }}
		set_variable = {{ name = zg361_mg_admin_offcycle_source_available value = 0 }}
		if = {{
			limit = {{
				has_variable = zg361_mg_m346_receipt_choice
				NOT = {{ var:zg361_mg_m346_receipt_choice = 3 }}
				has_variable = zg361_mg_offcycle_consumed
			}}
			set_variable = {{ name = zg361_mg_admin_offcycle_basis value = var:zg361_mg_offcycle_consumed }}
			set_variable = {{ name = zg361_mg_admin_offcycle_source_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_admin_form_hours value = var:zg361_mg_team_n }}
		set_variable = {{ name = zg361_mg_admin_meeting_hours value = var:zg361_mg_admin_calendar_basis }}
		set_variable = {{ name = zg361_mg_admin_appeal_hours value = {{ value = 0 subtract = var:zg361_mg_team_appeal_overturn divide = 5 multiply = 3 max = 0 }} }}
		set_variable = {{ name = zg361_mg_admin_calibration_hours value = {{ value = 0 subtract = var:zg361_mg_team_calibration divide = 5 multiply = 2 max = 0 }} }}
		set_variable = {{ name = zg361_mg_admin_interruption_hours value = {{ value = var:zg361_mg_admin_offcycle_basis multiply = 2 }} }}
		set_variable = {{ name = zg361_mg_admin_reported_hours value = 0 }}
		set_variable = {{ name = zg361_mg_admin_hidden_capacity_loss value = 0 }}
		set_variable = {{ name = zg361_mg_admin_control_extra_hours value = 0 }}
		if = {{ limit = {{ var:zg361_mg_m353_route = 2 }} set_variable = {{ name = zg361_mg_admin_control_extra_hours value = 5 }} change_variable = {{ name = zg361_mg_admin_meeting_hours add = 5 }} }}
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
				set_variable = {{ name = zg361_mg_manager_score_delta_due_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
				set_variable = {{ name = zg361_mg_admin_reported_hours value = var:zg361_mg_m353_admin_hours }}
				set_variable = {{ name = zg361_mg_admin_next_cycle_saving value = 5 }}
				if = {{ limit = {{ var:zg361_mg_m353_route = 2 }} set_variable = {{ name = zg361_mg_admin_reported_hours value = 0 }} set_variable = {{ name = zg361_mg_admin_hidden_capacity_loss value = var:zg361_mg_m353_admin_hours }} set_variable = {{ name = zg361_mg_admin_next_cycle_saving value = 0 }} change_variable = {{ name = zg361_mg_manager_score_delta add = {{ value = 0 subtract = var:zg361_mg_m353_admin_hours }} }} }}
				{receipt_call("AK", 353, 5)}
			}}
		}}
		else = {{ zg361_mg_set_red_effect = {{ CODE = 5 MECHANISM = 353 }} }}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m353_route = 3 }} {receipt_not_current("AK", 353, 5)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 353 }} }}
}}

zg361_mg_refund_admin_capacity_effect = {{
	if = {{
		limit = {{ var:zg361_case_ak_state = 5 var:zg361_case_ak_active = 1 has_variable = zg361_mg_m353_capacity_status var:zg361_mg_m353_capacity_status = 2 }}
		zg361_case_kernel_refund_transaction_effect = {{ OWNER_VAR = zg361_case_ak_owner SUBJECT_VAR = zg361_case_ak_subject CYCLE_VAR = zg361_case_ak_cycle_serial CASE_VAR = zg361_case_ak_case_serial STATE_VAR = zg361_case_ak_state ACTIVE_VAR = zg361_case_ak_active REVISION_VAR = zg361_case_ak_revision AVAILABLE_VAR = zg361_mg_admin_capacity_available RESERVED_VAR = zg361_mg_admin_capacity_reserved SETTLED_VAR = zg361_mg_admin_capacity_settled RECEIPT_AMOUNT_VAR = zg361_mg_m353_capacity_amount RECEIPT_STATUS_VAR = zg361_mg_m353_capacity_status TICKET_OWNER = var:zg361_case_ak_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ak_cycle_serial TICKET_CASE = var:zg361_case_ak_case_serial TICKET_STATE = 5 }}
		set_variable = {{ name = zg361_mg_admin_capacity_refunded value = 1 }}
	}}
	else = {{ debug_log = "ZG361MG: stale or duplicate admin-capacity refund ignored" }}
}}

# 354 — consume the snapshot's real raw counts exactly once.  Zero is a valid
# count; separate denominators guard division without rewriting source facts.
zg361_mg_m354_audit_fairness_effect = {{
	{route_prelude("AK", 354)}
	{c_route_receipt("AK", 354, 5)}
	if = {{
		limit = {{ var:zg361_mg_m354_route = 3 {receipt_current("AK", 354, 5)} has_variable = zg361_mg_fairness_input_status var:zg361_mg_fairness_input_status = 1 }}
		set_variable = {{ name = zg361_mg_fairness_input_status value = 3 }}
		set_variable = {{ name = zg361_mg_fairness_input_discarded_cycle value = var:zg361_case_ak_cycle_serial }}
	}}
	if = {{
		limit = {{
			var:zg361_case_ak_state = 5
			var:zg361_case_ak_active = 1
			{receipt_not_current("AK", 354, 5)}
			has_variable = zg361_mg_fairness_input_status
			var:zg361_mg_fairness_input_status = 1
			has_variable = zg361_mg_fairness_input_source_owner
			has_variable = zg361_mg_fairness_input_source_subject
			var:zg361_mg_fairness_input_source_owner = var:zg361_case_ak_owner
			var:zg361_mg_fairness_input_source_subject = this
			has_variable = zg361_mg_fairness_input_revision
			has_variable = zg361_mg_fairness_input_delivered
			has_variable = zg361_mg_fairness_input_appeals
			has_variable = zg361_mg_fairness_input_overturns
			has_variable = zg361_mg_fairness_input_exits
			has_variable = zg361_mg_fairness_input_healthy_exits
		}}
		{business_object_prelude("AK", 354, 35401)}
		set_variable = {{ name = zg361_mg_fairness_history_mapping_basis value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_history_mapping_available value = 0 }}
		if = {{
			limit = {{
				has_variable = zg361_mg_m352_receipt_choice
				NOT = {{ var:zg361_mg_m352_receipt_choice = 3 }}
				has_variable = zg361_mg_history_mapping_version
			}}
			set_variable = {{ name = zg361_mg_fairness_history_mapping_basis value = var:zg361_mg_history_mapping_version }}
			set_variable = {{ name = zg361_mg_fairness_history_mapping_available value = 1 }}
		}}
		set_variable = {{ name = zg361_mg_fairness_delivered value = var:zg361_mg_fairness_input_delivered }}
		set_variable = {{ name = zg361_mg_fairness_raw_appeals value = var:zg361_mg_fairness_input_appeals }}
		set_variable = {{ name = zg361_mg_fairness_raw_overturns value = var:zg361_mg_fairness_input_overturns }}
		set_variable = {{ name = zg361_mg_fairness_raw_exits value = var:zg361_mg_fairness_input_exits }}
		set_variable = {{ name = zg361_mg_fairness_raw_healthy_exits value = var:zg361_mg_fairness_input_healthy_exits }}
		set_variable = {{ name = zg361_mg_fairness_delivery_denominator value = {{ value = var:zg361_mg_fairness_delivered max = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_exit_denominator value = {{ value = var:zg361_mg_fairness_raw_exits max = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_appeal_rate value = {{ value = var:zg361_mg_fairness_raw_appeals divide = var:zg361_mg_fairness_delivery_denominator }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_overturn_rate value = 0 }}
		if = {{ limit = {{ var:zg361_mg_fairness_raw_appeals > 0 }} set_variable = {{ name = zg361_mg_fairness_raw_overturn_rate value = {{ value = var:zg361_mg_fairness_raw_overturns divide = var:zg361_mg_fairness_raw_appeals }} }} }}
		set_variable = {{ name = zg361_mg_fairness_raw_healthy_exit_rate value = {{ value = var:zg361_mg_fairness_raw_healthy_exits divide = var:zg361_mg_fairness_exit_denominator }} }}
		set_variable = {{ name = zg361_mg_fairness_reported_appeal_rate value = var:zg361_mg_fairness_raw_appeal_rate }}
		set_variable = {{ name = zg361_mg_fairness_reported_overturn_rate value = var:zg361_mg_fairness_raw_overturn_rate }}
		set_variable = {{ name = zg361_mg_fairness_reported_healthy_exit_rate value = var:zg361_mg_fairness_raw_healthy_exit_rate }}
		if = {{
			limit = {{ var:zg361_mg_m354_route = 2 }}
			set_variable = {{ name = zg361_mg_fairness_reported_appeal_rate value = {{ value = var:zg361_mg_fairness_raw_appeal_rate divide = 2 }} }}
			set_variable = {{ name = zg361_mg_fairness_reported_overturn_rate value = {{ value = var:zg361_mg_fairness_raw_overturn_rate divide = 2 }} }}
			set_variable = {{ name = zg361_mg_fairness_reported_healthy_exit_rate value = {{ value = var:zg361_mg_fairness_raw_healthy_exit_rate add = 0.25 min = 1 }} }}
		}}
		set_variable = {{ name = zg361_mg_fairness_gap_appeal value = {{ value = var:zg361_mg_fairness_reported_appeal_rate subtract = var:zg361_mg_fairness_raw_appeal_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gap_overturn value = {{ value = var:zg361_mg_fairness_reported_overturn_rate subtract = var:zg361_mg_fairness_raw_overturn_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gap_exit value = {{ value = var:zg361_mg_fairness_reported_healthy_exit_rate subtract = var:zg361_mg_fairness_raw_healthy_exit_rate }} }}
		set_variable = {{ name = zg361_mg_fairness_gaming value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_suppression_flag value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_reclassification_flag value = 0 }}
		if = {{ limit = {{ var:zg361_mg_fairness_gap_appeal < 0 }} set_variable = {{ name = zg361_mg_fairness_suppression_flag value = 1 }} }}
		if = {{ limit = {{ var:zg361_mg_fairness_gap_overturn < 0 }} set_variable = {{ name = zg361_mg_fairness_suppression_flag value = 1 }} }}
		if = {{ limit = {{ var:zg361_mg_fairness_gap_exit > 0 }} set_variable = {{ name = zg361_mg_fairness_reclassification_flag value = 1 }} }}
		if = {{ limit = {{ OR = {{ NOT = {{ var:zg361_mg_fairness_gap_appeal = 0 }} NOT = {{ var:zg361_mg_fairness_gap_overturn = 0 }} NOT = {{ var:zg361_mg_fairness_gap_exit = 0 }} }} }} set_variable = {{ name = zg361_mg_fairness_gaming value = 1 }} }}
		set_variable = {{ name = zg361_mg_fairness_trust_delta value = 0 }}
		set_variable = {{ name = zg361_mg_fairness_history_mapping_version value = var:zg361_mg_fairness_history_mapping_basis }}
		# Route A may reward only an earlier plan that M349 actually completed.
		if = {{
			limit = {{
				var:zg361_mg_m354_route = 1
				has_variable = zg361_mg_fairness_remediation_status
				var:zg361_mg_fairness_remediation_status = 2
				has_variable = zg361_mg_fairness_remediation_owner
				has_variable = zg361_mg_fairness_remediation_subject
				var:zg361_mg_fairness_remediation_owner = var:zg361_case_ak_owner
				var:zg361_mg_fairness_remediation_subject = this
				has_variable = zg361_mg_fairness_remediation_completion_receipt
				var:zg361_mg_fairness_remediation_completion_receipt = var:zg361_mg_fairness_remediation_plan_id
			}}
			set_variable = {{ name = zg361_mg_fairness_trust_delta value = 5 }}
			change_variable = {{ name = zg361_mg_policy_trust add = 5 }}
			set_variable = {{ name = zg361_mg_fairness_trust_settled_cycle value = var:zg361_case_ak_cycle_serial }}
			set_variable = {{ name = zg361_mg_fairness_remediation_status value = 3 }}
			set_variable = {{ name = zg361_mg_fairness_remediation_reward_receipt value = var:zg361_mg_fairness_remediation_plan_id }}
		}}
		# Route B's observable mismatch creates the next-cycle remediation plan;
		# no unsupported external self-disclosure/remediation knobs are read.
		if = {{
			limit = {{ var:zg361_mg_m354_route = 2 var:zg361_mg_fairness_gaming = 1 }}
			set_variable = {{ name = zg361_mg_fairness_remediation_status value = 1 }}
			set_variable = {{ name = zg361_mg_fairness_remediation_revision value = var:zg361_mg_fairness_input_revision }}
			set_variable = {{ name = zg361_mg_fairness_remediation_plan_id value = {{ value = var:zg361_case_ak_case_serial multiply = 1000 add = 354 }} }}
			set_variable = {{ name = zg361_mg_fairness_remediation_owner value = var:zg361_case_ak_owner }}
			set_variable = {{ name = zg361_mg_fairness_remediation_subject value = this }}
			set_variable = {{ name = zg361_mg_fairness_remediation_source_cycle value = var:zg361_case_ak_cycle_serial }}
			set_variable = {{ name = zg361_mg_fairness_remediation_source_case value = var:zg361_case_ak_case_serial }}
			set_variable = {{ name = zg361_mg_fairness_remediation_due_cycle value = {{ value = var:zg361_case_ak_cycle_serial add = 1 }} }}
		}}
		set_variable = {{ name = zg361_mg_fairness_input_status value = 2 }}
		set_variable = {{ name = zg361_mg_fairness_consumed_source_cycle value = var:zg361_mg_fairness_input_source_cycle }}
		set_variable = {{ name = zg361_mg_fairness_consumed_source_case value = var:zg361_mg_fairness_input_source_case }}
		set_variable = {{ name = zg361_mg_fairness_consumed_input_revision value = var:zg361_mg_fairness_input_revision }}
		set_variable = {{ name = zg361_mg_fairness_settlement_receipt value = var:zg361_case_ak_case_serial }}
		{receipt_call("AK", 354, 5)}
	}}
	else_if = {{ limit = {{ NOT = {{ var:zg361_mg_m354_route = 3 }} {receipt_not_current("AK", 354, 5)} }} zg361_mg_set_red_effect = {{ CODE = 3 MECHANISM = 354 }} }}
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
 zg361mg.120.desc:0 "Your direct superior has closed the manager review. Manager score: #high [ROOT.MakeScope.Var('zg361_mg_report_manager_score').GetValue|0]#! (available: [ROOT.MakeScope.Var('zg361_mg_report_score_available').GetValue|0]). Frozen source cycle: [ROOT.MakeScope.Var('zg361_mg_snapshot_source_serial').GetValue|0]; current review cycle: [ROOT.MakeScope.Var('zg361_case_f_cycle_serial').GetValue|0]. Profile reason total: [ROOT.MakeScope.Var('zg361_mg_report_reason_total').GetValue|0] (available: [ROOT.MakeScope.Var('zg361_mg_report_reason_available').GetValue|0]). Nine-box code: [ROOT.MakeScope.Var('zg361_mg_report_nine_box_code').GetValue|0] (available: [ROOT.MakeScope.Var('zg361_mg_report_nine_box_available').GetValue|0]; 0 means deferred or that a second frozen history does not yet exist). A Jingcha refusal, when present, is shown in the frozen breakdown as exactly -50 and is consumed only once."
 zg361mg.120.a:0 "I have read the score and its reasons."
 zg361mg.220.t:0 "Performance-System Operations Report"
 zg361mg.220.desc:0 "The policy cycle has migrated. Remaining governance capacity: #high [ROOT.MakeScope.Var('zg361_mg_admin_capacity_remaining').GetValue|0]#!. Audit sample: [ROOT.MakeScope.Var('zg361_mg_audit_sample_n').GetValue|0]; deterministic fingerprint: [ROOT.MakeScope.Var('zg361_mg_audit_selection_fingerprint').GetValue|0]. Fairness-gaming flag: [ROOT.MakeScope.Var('zg361_mg_fairness_gaming').GetValue|0]."
 zg361mg.220.a:0 "Archive the receipts."
'''


CHINESE_LOC = r'''
l_simp_chinese:
 zg361mg.120.t:0 "你的管理者绩效案卷"
 zg361mg.120.desc:0 "直属上司已经完成对你的管理者考核。你的管理绩效分是：#high [ROOT.MakeScope.Var('zg361_mg_report_manager_score').GetValue|0]#!（可用标记：[ROOT.MakeScope.Var('zg361_mg_report_score_available').GetValue|0]）。团队事实来源轮次：[ROOT.MakeScope.Var('zg361_mg_snapshot_source_serial').GetValue|0]；本次上级考核轮次：[ROOT.MakeScope.Var('zg361_case_f_cycle_serial').GetValue|0]。画像理由合计：[ROOT.MakeScope.Var('zg361_mg_report_reason_total').GetValue|0]（可用标记：[ROOT.MakeScope.Var('zg361_mg_report_reason_available').GetValue|0]）；九宫格编码：[ROOT.MakeScope.Var('zg361_mg_report_nine_box_code').GetValue|0]（可用标记：[ROOT.MakeScope.Var('zg361_mg_report_nine_box_available').GetValue|0]；0 表示该项延期或尚缺第二轮冻结历史，不会拿旧案卷冒充）。若你拒办京察，案卷会明确列出一次性的 -50，而不是让你猜自己到底为什么被打低。"
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
        MOD_ROOT / "common" / "scripted_triggers" / "zg361_manager_governance_runtime_triggers.txt": render_collective_cost_triggers(),
        MOD_ROOT / "common" / "script_values" / "zg361_manager_governance_runtime_values.txt": render_values(),
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
