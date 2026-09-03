#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B2 delivery, appeal, justice, and first PIP CK3 slice.

The generated runtime deliberately reuses the hand-written result-case
settlement and receipt-based refund effects.  It adds case-bound consumers
around those proven writes; it does not duplicate the money/merit ledger.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from zg361_b2_runtime_data import B2_BINDINGS, validate_b2_bindings


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_b2_runtime.py\n"
CORE_IDS = (
    tuple(range(14, 18))
    + tuple(range(69, 82))
    + (358, 359)
)
DELEGATED_IDS = tuple(range(146, 157)) + tuple(range(181, 192))
WIRED_IDS = CORE_IDS
# This generator owns only the native delivery/appeal/justice slice.  The
# feedback/PIP runtime is authoritative for #146-156/#181-191; retaining that
# range here as a negative guard is intentional, but claiming or rendering it
# here would create two lifecycle owners for the same mechanisms.
SEMANTIC_IDS = CORE_IDS
INTERFACE_IDS = (69,)

LEGACY_EFFECT_FILENAME = "zg361_b2_runtime_effects.txt"
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# A future shard above the principled ceiling must name both the engineering
# reason and a concrete CK3 live artifact.  The current layout needs none.
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}


def _policy_effect_names(mechanism_id: int) -> tuple[str, ...]:
    key = f"{mechanism_id:03d}"
    return (
        f"zg361_b2_m{key}_resolve_policy_effect",
        f"zg361_b2_m{key}_post_policy_debt_effect",
        f"zg361_b2_m{key}_open_business_object_effect",
        f"zg361_b2_m{key}_consume_business_object_effect",
    )


# B2 is intentionally emitted as small purpose-oriented files.  These groups
# are semantic ownership boundaries, not arbitrary byte ranges: the policy
# lifecycle for a mechanism stays beside the domain operations it governs.
# The target is 1-10 effects per file and the hard ceiling is 20.
EFFECT_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "zg361_b2_014_appeal_lifecycle_effects.txt",
        _policy_effect_names(14)
        + (
            "zg361_b2_on_appeal_filed_effect",
            "zg361_b2_on_appeal_upheld_effect",
            "zg361_b2_on_appeal_expired_effect",
            "zg361_b2_on_appeal_corrected_effect",
        ),
    ),
    (
        "zg361_b2_015_pip_open_effects.txt",
        _policy_effect_names(15)
        + (
            "zg361_b2_clear_pip_case_tuple_effect",
            "zg361_b2_assign_pip_independent_reviewer_effect",
            "zg361_b2_m015_open_pip_effect",
        ),
    ),
    (
        "zg361_b2_015_pip_response_effects.txt",
        (
            "zg361_b2_accept_pip_effect",
            "zg361_b2_negotiate_pip_effect",
            "zg361_b2_refuse_pip_effect",
        ),
    ),
    (
        "zg361_b2_016_pip_support_effects.txt",
        _policy_effect_names(16)
        + (
            "zg361_b2_m016_commit_support_effect",
            "zg361_b2_release_pip_support_effect",
            "zg361_b2_publish_pip_performance_evidence_effect",
            "zg361_b2_record_pip_midpoint_effect",
        ),
    ),
    (
        "zg361_b2_017_pip_settlement_effects.txt",
        _policy_effect_names(17)
        + (
            "zg361_b2_schedule_pip_deadline_effect",
            "zg361_b2_resolve_pip_due_effect",
            "zg361_b2_settle_pip_outcome_effect",
            "zg361_b2_m017_open_disposition_effect",
        ),
    ),
    (
        "zg361_b2_017_pip_workforce_handoff_effects.txt",
        (
            "zg361_b2_publish_workforce_pip_settlement_effect",
            "zg361_b2_replay_workforce_probation_fact_handoff_effect",
        ),
    ),
    (
        "zg361_b2_069_delivery_effects.txt",
        _policy_effect_names(69)
        + (
            "zg361_b2_pre_notice_settlement_gate_effect",
            "zg361_b2_on_result_frozen_effect",
            "zg361_b2_on_notice_delivered_effect",
            "zg361_b2_m069_record_delivery_effect",
        ),
    ),
    (
        "zg361_b2_070_observation_effects.txt",
        _policy_effect_names(70) + ("zg361_b2_m070_open_observation_effect",),
    ),
    (
        "zg361_b2_071_escalation_effects.txt",
        _policy_effect_names(71)
        + (
            "zg361_b2_m071_open_escalation_effect",
            "zg361_b2_publish_evidence_escalation_effect",
        ),
    ),
    (
        "zg361_b2_072_access_audit_effects.txt",
        _policy_effect_names(72)
        + (
            "zg361_b2_m072_lock_pre_delivery_access_effect",
            "zg361_b2_record_case_access_effect",
            "zg361_b2_m072_close_access_log_effect",
        ),
    ),
    (
        "zg361_b2_073_reporting_effects.txt",
        _policy_effect_names(73)
        + (
            "zg361_b2_publish_anonymous_report_effect",
            "zg361_b2_defer_escalation_effect",
            "zg361_b2_m073_triage_report_effect",
        ),
    ),
    (
        "zg361_b2_074_redundancy_effects.txt",
        _policy_effect_names(74)
        + (
            "zg361_b2_m074_open_redundancy_offer_effect",
            "zg361_b2_m074_accept_redundancy_effect",
            "zg361_b2_m074_reject_redundancy_effect",
        ),
    ),
    (
        "zg361_b2_075_exit_offer_effects.txt",
        _policy_effect_names(75)
        + (
            "zg361_b2_m075_open_exit_offer_effect",
            "zg361_b2_m075_accept_exit_offer_effect",
            "zg361_b2_m075_reject_exit_offer_effect",
        ),
    ),
    (
        "zg361_b2_076_liability_effects.txt",
        _policy_effect_names(76) + ("zg361_b2_m076_allocate_liability_effect",),
    ),
    (
        "zg361_b2_077_reviewer_effects.txt",
        _policy_effect_names(77)
        + (
            "zg361_b2_m077_assign_reviewer_effect",
            "zg361_b2_m077_subject_recusal_effect",
            "zg361_b2_m077_owner_recusal_effect",
            "zg361_b2_m077_pick_replacement_effect",
        ),
    ),
    (
        "zg361_b2_078_fairness_effects.txt",
        _policy_effect_names(78)
        + (
            "zg361_b2_m078_update_fairness_effect",
            "zg361_b2_m078_record_cohort_sample_effect",
            "zg361_b2_m078_apply_resolved_sample_effect",
        ),
    ),
    (
        "zg361_b2_079_skip_level_effects.txt",
        _policy_effect_names(79)
        + (
            "zg361_b2_m079_open_skip_level_effect",
            "zg361_b2_m079_release_seat_effect",
        ),
    ),
    (
        "zg361_b2_080_metric_defect_effects.txt",
        _policy_effect_names(80) + ("zg361_b2_m080_open_metric_defect_effect",),
    ),
    (
        "zg361_b2_081_projection_access_effects.txt",
        _policy_effect_names(81)
        + (
            "zg361_b2_m081_project_case_access_effect",
            "zg361_b2_m081_publish_case_projection_effect",
        ),
    ),
    (
        "zg361_b2_358_non_aggravation_effects.txt",
        _policy_effect_names(358)
        + (
            "zg361_b2_m358_publish_workforce_receipt_effect",
            "zg361_b2_m358_freeze_non_aggravation_effect",
            "zg361_b2_m358_apply_disclosed_aggravation_effect",
            "zg361_b2_m358_close_non_aggravation_effect",
            "zg361_b2_m358_open_separate_case_effect",
        ),
    ),
    (
        "zg361_b2_358_separate_adverse_action_effects.txt",
        (
            "zg361_b2_prepare_adverse_action_effect",
            "zg361_b2_finish_adverse_action_effect",
            "zg361_b2_cancel_blocked_action_effect",
            "zg361_b2_deliver_separate_case_effect",
            "zg361_b2_execute_pending_adverse_action_effect",
        ),
    ),
    (
        "zg361_b2_359_quota_return_effects.txt",
        _policy_effect_names(359)
        + (
            "zg361_b2_m359_publish_workforce_receipt_effect",
            "zg361_b2_m359_open_quota_return_effect",
            "zg361_b2_m359_return_pp_nomination_slot_effect",
            "zg361_b2_m359_post_next_cycle_debt_effect",
            "zg361_b2_m359_open_boundary_review_effect",
        ),
    ),
    (
        "zg361_b2_359_boundary_redelivery_effects.txt",
        (
            "zg361_b2_prepare_boundary_redelivery_effect",
            "zg361_b2_deliver_boundary_notice_effect",
            "zg361_b2_contest_boundary_notice_effect",
            "zg361_b2_apply_boundary_redelivery_effect",
            "zg361_b2_apply_due_quota_debt_effect",
        ),
    ),
    (
        "zg361_b2_collective_receipt_handoff_effects.txt",
        ("zg361_b2_submit_completed_al_receipts_effect",),
    ),
    (
        "zg361_b2_debt_consumers_effects.txt",
        (
            "zg361_b2_consume_pip_performance_evidence_effect",
            "zg361_b2_consume_management_debt_effect",
            "zg361_b2_consume_due_policy_debts_effect",
        ),
    ),
)

# One subject can pass through more than one terminal PIP over a long game.
# These fields describe exactly one current PIP case and therefore must never
# leak from a completed/refused case into the next one.  Prospective
# ``pip_performance_evidence_*`` is deliberately excluded: it is a separately
# conserved next-cycle receipt and has its own consumer.
PIP_CASE_TUPLE_FIELDS = (
    "zg361_b2_pip_owner",
    "zg361_b2_pip_subject",
    "zg361_b2_pip_cycle",
    "zg361_b2_pip_case",
    "zg361_b2_pip_state",
    "zg361_b2_pip_task_kind",
    "zg361_b2_pip_task_controllable",
    "zg361_b2_pip_policy_route",
    "zg361_b2_pip_progress_source_kind",
    "zg361_b2_pip_progress_baseline_owner",
    "zg361_b2_pip_progress_baseline_subject",
    "zg361_b2_pip_progress_baseline_cycle",
    "zg361_b2_pip_progress_baseline_case",
    "zg361_b2_pip_progress_baseline_task_kind",
    "zg361_b2_pip_progress_baseline_value",
    "zg361_b2_pip_progress_target_value",
    "zg361_b2_pip_progress_baseline_year",
    "zg361_b2_pip_progress_baseline_status",
    "zg361_b2_pip_progress_baseline_red_code",
    "zg361_b2_pip_independent_reviewer",
    "zg361_b2_pip_reviewer_assignment_owner",
    "zg361_b2_pip_reviewer_assignment_subject",
    "zg361_b2_pip_reviewer_assignment_cycle",
    "zg361_b2_pip_reviewer_assignment_case",
    "zg361_b2_pip_reviewer_assignment_source",
    "zg361_b2_pip_reviewer_assignment_status",
    "zg361_b2_pip_reviewer_assignment_red_code",
    "zg361_b2_pip_reviewer_assignment_receipt",
    "zg361_b2_m015_receipt_serial",
    "zg361_b2_pip_subject_response",
    "zg361_b2_pip_subject_response_case",
    "zg361_b2_pip_subject_response_author",
    "zg361_b2_pip_goal_revision_used",
    "zg361_b2_pip_refusal_receipt",
    "zg361_b2_pip_high_pressure",
    "zg361_b2_pip_refusal_major_evidence",
    "zg361_b2_pip_support_reserved",
    "zg361_b2_pip_support_absent",
    "zg361_b2_pip_support_hours",
    "zg361_b2_pip_support_attention",
    "zg361_b2_pip_support_mentor",
    "zg361_b2_pip_support_budget_owner",
    "zg361_b2_pip_support_budget_allocated",
    "zg361_b2_pip_support_budget_spent",
    "zg361_b2_m016_receipt_serial",
    "zg361_b2_pip_support_released",
    "zg361_b2_pip_support_withheld",
    "zg361_b2_pip_support_atomic_shortfall",
    "zg361_b2_pip_support_budget_unchanged",
    "zg361_b2_pip_midpoint_receipt",
    "zg361_b2_pip_midpoint_resource_delivery_valid",
    "zg361_b2_pip_midpoint_progress_status",
    "zg361_b2_pip_midpoint_progress_red_code",
    "zg361_b2_pip_midpoint_progress_source_kind",
    "zg361_b2_pip_midpoint_progress_owner",
    "zg361_b2_pip_midpoint_progress_subject",
    "zg361_b2_pip_midpoint_progress_cycle",
    "zg361_b2_pip_midpoint_progress_case",
    "zg361_b2_pip_midpoint_progress_task_kind",
    "zg361_b2_pip_midpoint_progress_current_value",
    "zg361_b2_pip_midpoint_progress_delta",
    "zg361_b2_pip_midpoint_progress_met",
    "zg361_b2_pip_midpoint_progress_year",
    "zg361_b2_pip_midpoint_state",
    "zg361_b2_pip_outcome_code",
    "zg361_b2_pip_settlement_receipt",
    "zg361_b2_pip_outcome_result_cycle",
    "zg361_b2_pip_outcome_result_case",
    "zg361_b2_pip_outcome_result_grade",
    "zg361_b2_pip_stability_days_observed",
    "zg361_b2_pip_independent_review_status",
    "zg361_b2_pip_independent_review_red_code",
    "zg361_b2_pip_independent_review_reviewer",
    "zg361_b2_pip_independent_review_owner",
    "zg361_b2_pip_independent_review_subject",
    "zg361_b2_pip_independent_review_cycle",
    "zg361_b2_pip_independent_review_case",
    "zg361_b2_pip_independent_review_result_owner",
    "zg361_b2_pip_independent_review_result_cycle",
    "zg361_b2_pip_independent_review_result_case",
    "zg361_b2_pip_independent_review_result_grade",
    "zg361_b2_pip_independent_review_progress_delta",
    "zg361_b2_pip_independent_review_progress_met",
    "zg361_b2_pip_independent_review_conclusion",
    "zg361_b2_pip_independent_review_receipt",
    "zg361_b2_pip_independent_review_year",
    "zg361_b2_pip_graduation_receipt",
    "zg361_b2_pip_failure_receipt",
    "zg361_b2_pip_no_support_liability",
)


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def validate_wired_scope() -> None:
    validate_b2_bindings()
    available = {binding.mechanism_id for binding in B2_BINDINGS}
    if len(WIRED_IDS) != 19 or len(set(WIRED_IDS)) != 19:
        raise ValueError("B2 CK3 slice must contain exactly nineteen IDs")
    if not set(WIRED_IDS) <= available:
        raise ValueError("B2 CK3 slice contains an unknown binding")
    if INTERFACE_IDS != (69,):
        raise ValueError("069 is the only pre-existing interface in this slice")
    if SEMANTIC_IDS != CORE_IDS:
        raise ValueError("B2 semantic ownership must remain the nineteen native IDs")
    if set(SEMANTIC_IDS) & set(DELEGATED_IDS):
        raise ValueError("B2 must not duplicate feedback/PIP delegated IDs")


def render_pip_case_tuple_reset() -> str:
    """Render the single reset owner for one case-bound PIP projection."""

    removals = "".join(
        f"\tremove_variable = {field}\n" for field in PIP_CASE_TUPLE_FIELDS
    )
    return f'''# ---------------------------------------------------------------------------
# Current PIP tuple reset.  It runs before every new #015 identity is written
# and again on route C, so a paused native read sees either all eight identity
# fields for one case or none of them.  In particular a previous subject
# response author remains absent until this subject answers the new case.
# ---------------------------------------------------------------------------

zg361_b2_clear_pip_case_tuple_effect = {{
{removals}}}

'''


def render_policy_object_kernel() -> str:
    """Render the shared per-mechanism A/B/C identity and receipt kernel.

    The older B2 slice had useful domain effects, but those effects never read
    the frozen ``zg361_mechanism_NNN_choice`` policy.  Consequently route C
    still created cases and route B was indistinguishable from route A.  This
    kernel is deliberately small: it binds every native B2 row to the result
    owner/subject/cycle/case, prevents replay, and gives C a separate deferred
    debt receipt without manufacturing a business object.
    """

    sections: list[str] = [r'''
# ---------------------------------------------------------------------------
# Native B2 A/B/C identity kernel.  T/W #146-156/#181-191 are authoritative
# in zg361_feedback_promotion_pip_runtime and are not duplicated here.
# ---------------------------------------------------------------------------

zg361_b2_consume_due_policy_debts_effect = {
''']
    for mechanism_id in CORE_IDS:
        key = f"{mechanism_id:03d}"
        sections.append(f'''\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_b2_m{key}_policy_debt_active = 1
\t\t\thas_variable = zg361_b2_m{key}_policy_debt_due_cycle
\t\t\tvar:zg361_result_cycle_serial >= var:zg361_b2_m{key}_policy_debt_due_cycle
\t\t\thas_variable = zg361_b2_m{key}_policy_debt_owner
\t\t}}
\t\tvar:zg361_b2_m{key}_policy_debt_owner = {{
\t\t\tchange_variable = {{ name = zg361_b2_management_debt add = 1 }}
\t\t}}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_active value = 0 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_audit_state value = 3 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_consumed_cycle value = var:zg361_result_cycle_serial }}
\t}}
''')
    sections.append("}\n")

    for mechanism_id in CORE_IDS:
        key = f"{mechanism_id:03d}"
        pip_owned = mechanism_id in (15, 16, 17)
        object_owner = "var:zg361_b2_pip_owner" if pip_owned else "var:zg361_b2_case_owner"
        object_cycle = "var:zg361_b2_pip_cycle" if pip_owned else "var:zg361_b2_case_cycle"
        object_case = "var:zg361_b2_pip_case" if pip_owned else "var:zg361_b2_case_serial"
        object_state = "var:zg361_b2_pip_state" if pip_owned else "var:zg361_b2_notice_state"
        policy_owner = "var:zg361_b2_pip_owner" if pip_owned else "var:zg361_b2_case_owner"
        workforce_receipt_publish = (
            f"\n\t\tzg361_b2_m{key}_publish_workforce_receipt_effect = yes"
            if mechanism_id in (358, 359)
            else ""
        )
        sections.append(f'''
zg361_b2_m{key}_resolve_policy_effect = {{
\tset_variable = {{ name = zg361_b2_m{key}_route value = 1 }}
\tif = {{
\t\tlimit = {{ {policy_owner} = {{ has_variable = zg361_mechanism_{key}_choice }} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_route value = {policy_owner}.var:zg361_mechanism_{key}_choice }}
\t}}
}}

zg361_b2_m{key}_post_policy_debt_effect = {{
\tzg361_b2_m{key}_resolve_policy_effect = yes
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_b2_m{key}_route = 3
\t\t\tOR = {{
\t\t\t\tNOT = {{ has_variable = zg361_b2_m{key}_policy_debt_receipt_case }}
\t\t\t\tNOT = {{ var:zg361_b2_m{key}_policy_debt_receipt_case = var:zg361_b2_case_serial }}
\t\t\t}}
\t\t\tNOT = {{ var:zg361_b2_m{key}_policy_debt_active = 1 }}
\t\t}}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_owner value = var:zg361_b2_case_owner }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_subject value = this }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_cycle value = var:zg361_b2_case_cycle }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_receipt_case value = var:zg361_b2_case_serial }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_expected_state value = var:zg361_b2_notice_state }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_due_cycle value = {{ value = var:zg361_b2_case_cycle add = 1 }} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_active value = 1 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_policy_debt_audit_state value = 1 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_visible_revision value = var:zg361_b2_case_feedback_revision }}
\t}}
}}

zg361_b2_m{key}_open_business_object_effect = {{
\tzg361_b2_m{key}_resolve_policy_effect = yes
\tif = {{
\t\tlimit = {{ var:zg361_b2_m{key}_route = 3 }}
\t\tzg361_b2_m{key}_post_policy_debt_effect = yes
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tOR = {{
\t\t\t\tNOT = {{ has_variable = zg361_b2_m{key}_object_receipt_case }}
\t\t\t\tNOT = {{ var:zg361_b2_m{key}_object_receipt_case = {object_case} }}
\t\t\t}}
\t\t\tNOT = {{ var:zg361_b2_m{key}_object_active = 1 }}
\t\t}}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_owner value = {object_owner} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_subject value = this }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_cycle value = {object_cycle} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_receipt_case value = {object_case} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_state value = {object_state} }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_route value = var:zg361_b2_m{key}_route }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_active value = 1 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_consumed value = 0 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_visible_revision value = var:zg361_b2_case_feedback_revision }}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_b2_m{key}_route = 2 }}
\t\t\tset_variable = {{ name = zg361_b2_m{key}_procedural_risk value = 1 }}
\t\t}}
\t}}
}}

zg361_b2_m{key}_consume_business_object_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_b2_m{key}_object_active = 1
\t\t\tvar:zg361_b2_m{key}_object_consumed = 0
\t\t\tvar:zg361_b2_m{key}_object_owner = {object_owner}
\t\t\tvar:zg361_b2_m{key}_object_subject = this
\t\t\tvar:zg361_b2_m{key}_object_cycle = {object_cycle}
\t\t\tvar:zg361_b2_m{key}_object_receipt_case = {object_case}
\t\t}}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_consumed value = 1 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_object_active value = 0 }}
\t\tset_variable = {{ name = zg361_b2_m{key}_consumer_revision value = var:zg361_b2_case_feedback_revision }}
\t\tset_variable = {{ name = zg361_b2_m{key}_consumer_receipt_case value = {object_case} }}{workforce_receipt_publish}
\t}}
}}
''')
    return "".join(sections)


FAIRNESS_DIMENSIONS = (
    ("newcomer", "veteran", "has_character_flag = zg361_newcomer_this_cycle"),
    (
        "transfer",
        "local",
        "has_variable = zg361_b1_reorg_transfer_detected\n\t\t\tvar:zg361_b1_reorg_transfer_detected = 1",
    ),
    ("kin", "nonkin", "is_close_family_of = scope:zg361_b2_fairness_owner"),
    ("faction", "nonfaction", "exists = joined_faction"),
    ("landed", "unlanded", "is_landed = yes"),
    ("governor", "nongovernor", "is_governor = yes"),
)


def render_fairness_kernel() -> str:
    """Render #078 cohort denominators and resolved-appeal numerators.

    Every result contributes at most one sample to its frozen manager/cycle.
    Appeal outcomes update only the matching sample.  Cross-multiplied rates
    avoid division and small groups are explicitly marked, never auto-graded.
    """

    sample_dimensions: list[str] = []
    outcome_dimensions: list[str] = []
    anomaly_dimensions: list[str] = []
    counter_initializers: list[str] = []
    for positive, negative, trigger in FAIRNESS_DIMENSIONS:
        for suffix in ("n", "bottom_n", "corrected_n"):
            for group in (positive, negative):
                variable = f"zg361_b2_fairness_{group}_{suffix}"
                counter_initializers.append(
                    f'''\t\t\tif = {{\n\t\t\t\tlimit = {{ NOT = {{ has_variable = {variable} }} }}\n\t\t\t\tset_variable = {{ name = {variable} value = 0 }}\n\t\t\t}}\n'''
                )
        sample_dimensions.append(
            f'''		if = {{
			limit = {{ scope:zg361_b2_fairness_subject = {{ {trigger} }} }}
			change_variable = {{ name = zg361_b2_fairness_{positive}_n add = 1 }}
			scope:zg361_b2_fairness_subject = {{ set_variable = {{ name = zg361_b2_m078_group_{positive} value = 1 }} }}
			if = {{
				limit = {{ scope:zg361_b2_fairness_subject.var:zg361_result_grade = 1 }}
				change_variable = {{ name = zg361_b2_fairness_{positive}_bottom_n add = 1 }}
			}}
		}}
		else = {{
			change_variable = {{ name = zg361_b2_fairness_{negative}_n add = 1 }}
			scope:zg361_b2_fairness_subject = {{ set_variable = {{ name = zg361_b2_m078_group_{positive} value = 2 }} }}
			if = {{
				limit = {{ scope:zg361_b2_fairness_subject.var:zg361_result_grade = 1 }}
				change_variable = {{ name = zg361_b2_fairness_{negative}_bottom_n add = 1 }}
			}}
		}}
'''
        )
        outcome_dimensions.append(
            f'''		if = {{
			limit = {{
				scope:zg361_b2_fairness_subject.var:zg361_b2_appeal_state = 3
				scope:zg361_b2_fairness_subject.var:zg361_b2_m078_group_{positive} = 1
			}}
			change_variable = {{ name = zg361_b2_fairness_{positive}_corrected_n add = 1 }}
		}}
		else_if = {{
			limit = {{
				scope:zg361_b2_fairness_subject.var:zg361_b2_appeal_state = 3
				scope:zg361_b2_fairness_subject.var:zg361_b2_m078_group_{positive} = 2
			}}
			change_variable = {{ name = zg361_b2_fairness_{negative}_corrected_n add = 1 }}
		}}
'''
        )
        anomaly_dimensions.append(
            f'''		if = {{
			limit = {{
				var:zg361_b2_fairness_{positive}_n >= 3
				var:zg361_b2_fairness_{negative}_n >= 3
			}}
			set_variable = {{ name = zg361_b2_fairness_{positive}_rate_cross value = {{ value = var:zg361_b2_fairness_{positive}_corrected_n multiply = var:zg361_b2_fairness_{negative}_n }} }}
			set_variable = {{ name = zg361_b2_fairness_{negative}_rate_cross value = {{ value = var:zg361_b2_fairness_{negative}_corrected_n multiply = var:zg361_b2_fairness_{positive}_n }} }}
			if = {{
				limit = {{ NOT = {{ var:zg361_b2_fairness_{positive}_rate_cross = var:zg361_b2_fairness_{negative}_rate_cross }} }}
				set_variable = {{ name = zg361_b2_fairness_anomaly_open value = 1 }}
				set_variable = {{ name = zg361_b2_fairness_anomaly_dimension value = {len(anomaly_dimensions) + 1} }}
			}}
		}}
		else = {{ set_variable = {{ name = zg361_b2_fairness_small_sample value = 1 }} }}
'''
        )

    return r'''
# ---------------------------------------------------------------------------
# #078 full-cohort fairness samples.  These counters are diagnostics only:
# neither baseline nor appeal resolution contains a grade write.
# ---------------------------------------------------------------------------

zg361_b2_m078_record_cohort_sample_effect = {
	zg361_b2_m078_resolve_policy_effect = yes
	if = {
		limit = {
			var:zg361_b2_m078_route != 3
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			OR = {
				NOT = { has_variable = zg361_b2_m078_sample_receipt_case }
				NOT = { var:zg361_b2_m078_sample_receipt_case = var:zg361_b2_case_serial }
			}
		}
		save_temporary_scope_as = zg361_b2_fairness_subject
		var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_fairness_owner }
		set_variable = { name = zg361_b2_m078_sample_receipt_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m078_sample_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m078_state value = 1 }
		scope:zg361_b2_fairness_owner = {
			if = { limit = { NOT = { has_variable = zg361_b2_fairness_total_n } } set_variable = { name = zg361_b2_fairness_total_n value = 0 } }
			if = { limit = { NOT = { has_variable = zg361_b2_fairness_bottom_n } } set_variable = { name = zg361_b2_fairness_bottom_n value = 0 } }
			if = { limit = { NOT = { has_variable = zg361_b2_fairness_reviewed_n } } set_variable = { name = zg361_b2_fairness_reviewed_n value = 0 } }
			if = { limit = { NOT = { has_variable = zg361_b2_fairness_corrected_n } } set_variable = { name = zg361_b2_fairness_corrected_n value = 0 } }
''' + "".join(counter_initializers) + r'''
			change_variable = { name = zg361_b2_fairness_total_n add = 1 }
			if = {
				limit = { scope:zg361_b2_fairness_subject.var:zg361_result_grade = 1 }
				change_variable = { name = zg361_b2_fairness_bottom_n add = 1 }
			}
''' + "".join(sample_dimensions) + r'''			set_variable = { name = zg361_b2_fairness_dimension_n value = 6 }
			scope:zg361_b2_fairness_subject = {
				set_variable = { name = zg361_b2_m078_denominator_snapshot value = scope:zg361_b2_fairness_owner.var:zg361_b2_fairness_total_n }
			}
		}
	}
}

zg361_b2_m078_apply_resolved_sample_effect = {
	if = {
		limit = {
			var:zg361_b2_m078_object_active = 1
			var:zg361_b2_m078_sample_receipt_case = var:zg361_b2_case_serial
			OR = {
				NOT = { has_variable = zg361_b2_m078_outcome_receipt_case }
				NOT = { var:zg361_b2_m078_outcome_receipt_case = var:zg361_b2_case_serial }
			}
		}
		save_temporary_scope_as = zg361_b2_fairness_subject
		var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_fairness_owner }
		scope:zg361_b2_fairness_owner = {
			change_variable = { name = zg361_b2_fairness_reviewed_n add = 1 }
			if = {
				limit = { scope:zg361_b2_fairness_subject.var:zg361_b2_appeal_state = 3 }
				change_variable = { name = zg361_b2_fairness_corrected_n add = 1 }
			}
''' + "".join(outcome_dimensions) + r'''			set_variable = { name = zg361_b2_fairness_small_sample value = 0 }
			set_variable = { name = zg361_b2_fairness_anomaly_open value = 0 }
''' + "".join(anomaly_dimensions) + r'''			if = {
				limit = { var:zg361_b2_fairness_anomaly_open = 1 }
				set_variable = { name = zg361_b2_fairness_explanation_task value = scope:zg361_b2_fairness_subject.var:zg361_b2_case_serial }
				if = {
					limit = { scope:zg361_b2_fairness_subject.var:zg361_b2_m078_route = 2 }
					set_variable = { name = zg361_b2_fairness_auto_adjustment_attempted value = 1 }
					set_variable = { name = zg361_b2_fairness_no_direct_grade_write value = 1 }
					change_variable = { name = zg361_b2_management_debt add = 1 }
				}
			}
		}
		set_variable = { name = zg361_b2_m078_state value = 3 }
		set_variable = { name = zg361_b2_m078_receipt_serial value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m078_outcome_receipt_case value = var:zg361_b2_case_serial }
		zg361_b2_m078_consume_business_object_effect = yes
	}
}
'''


def render_effect_source() -> str:
    return render_pip_case_tuple_reset() + r'''
# ZhongGuo 361 B2 — delivery, appeal justice and first PIP product runtime.
#
# State is stored on the assessed official.  Every timed event freezes owner,
# subject, cycle, case and expected state.  Existing zg361_effects.txt remains
# the only implementation of 3.25 settlement and receipt-bounded refund.

# ---------------------------------------------------------------------------
# Result freeze and delivery adapters: #069, #072, #081.
# ---------------------------------------------------------------------------

# Shared-hook ABI for #069.  The hand-written settlement effect must call this
# after formal delivery has been proved but before any treasury/gold/merit or
# salary-cut write.  It may proceed only when the returned variable is one.
# This generator deliberately does not edit the shared file; until that caller
# lands, #069 route C remains an explicit cross-package RED rather than a false
# claim that an after-settlement adapter prevented the payment.
zg361_b2_pre_notice_settlement_gate_effect = {
	set_variable = { name = zg361_b2_m069_settlement_allowed value = 0 }
	zg361_b2_m069_resolve_policy_effect = yes
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_notice_state = 1
			var:zg361_b2_m069_route != 3
			var:zg361_b2_m069_object_active = 1
		}
		set_variable = { name = zg361_b2_m069_settlement_allowed value = 1 }
		set_variable = { name = zg361_b2_m069_pre_settlement_gate_seen value = var:zg361_b2_case_serial }
	}
	else_if = {
		limit = { var:zg361_b2_m069_route = 3 }
		zg361_b2_m069_post_policy_debt_effect = yes
		set_variable = { name = zg361_b2_m069_settlement_blocked_case value = var:zg361_b2_case_serial }
		debug_log = "ZG361B2: route-C formal-result settlement blocked before resource writes"
	}
	else = { debug_log = "ZG361B2: stale formal-result settlement gate denied" }
}

zg361_b2_on_result_frozen_effect = {
	if = {
		limit = {
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
		}
		# Consume prior-cycle C receipts before replacing the subject's current
		# case identity.  A debt is charged to its frozen owner, never the new one.
		zg361_b2_consume_due_policy_debts_effect = yes
		# A skip-level remand is consumed only by the next real result from the
		# same direct manager.  This is the downstream consumer; the skip-level
		# reviewer never writes a grade in the old case.
		if = {
			limit = {
				var:zg361_b2_m079_remand_active = 1
				var:zg361_b2_m079_remand_owner = var:zg361_result_case_owner
				var:zg361_result_cycle_serial > var:zg361_b2_m079_remand_cycle
			}
			set_variable = { name = zg361_b2_m079_remand_active value = 0 }
			set_variable = { name = zg361_b2_m079_remand_consumer_case value = var:zg361_result_case_serial }
			set_variable = { name = zg361_b2_m079_manager_rework_completed value = 1 }
		}
		# Repaired/suppressed defect tickets are likewise checked against a later
		# metric version.  Repetition after suppression assigns liability to the
		# frozen suppressor and does not rewrite the old evidence.
		if = {
			limit = {
				OR = {
					var:zg361_b2_m080_state = 3
					var:zg361_b2_m080_state = 4
				}
				var:zg361_b2_m080_owner = var:zg361_result_case_owner
				var:zg361_result_cycle_serial > var:zg361_b2_m080_cycle
			}
			set_variable = { name = zg361_b2_m080_consumer_case value = var:zg361_result_case_serial }
			if = {
				limit = { var:zg361_b2_m080_metric_repaired = 1 }
				set_variable = { name = zg361_b2_m080_repair_verified value = 1 }
			}
			else_if = {
				limit = {
					var:zg361_b2_m080_suppressed = 1
					var:zg361_result_grade_reason = var:zg361_b2_m080_defect_type
				}
				set_variable = { name = zg361_b2_m080_repeated_after_suppression value = 1 }
				var:zg361_b2_m080_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			}
			set_variable = { name = zg361_b2_m080_state value = 5 }
		}
		# A later, freshly frozen result by the same owner is the only automatic
		# source of "new fact" for a pending retaliation observation.  Merely
		# reusing the appealed result never authorizes a harsher action.
		if = {
			limit = {
				has_variable = zg361_b2_retaliation_state
				var:zg361_b2_retaliation_state = 1
				has_variable = zg361_b2_retaliation_subject
				var:zg361_b2_retaliation_subject = this
				has_variable = zg361_b2_retaliation_owner
				var:zg361_b2_retaliation_owner = var:zg361_result_case_owner
				has_variable = zg361_b2_retaliation_cycle
				var:zg361_result_cycle_serial > var:zg361_b2_retaliation_cycle
			}
			set_variable = { name = zg361_b2_retaliation_new_fact value = 1 }
			set_variable = { name = zg361_b2_retaliation_new_fact_cycle value = var:zg361_result_cycle_serial }
		}
		set_variable = { name = zg361_b2_case_owner value = var:zg361_result_case_owner }
		set_variable = { name = zg361_b2_case_subject value = this }
		set_variable = { name = zg361_b2_case_cycle value = var:zg361_result_cycle_serial }
		set_variable = { name = zg361_b2_case_serial value = var:zg361_result_case_serial }
		set_variable = { name = zg361_b2_notice_state value = 1 } # prepared
		set_variable = { name = zg361_b2_notice_reason value = var:zg361_result_grade_reason }
		set_variable = { name = zg361_b2_delivery_year value = 0 }
		set_variable = { name = zg361_b2_appeal_state value = 0 }
		set_variable = { name = zg361_b2_case_feedback_revision value = 1 }

		# A new result case resets its own B2 rows, but a one-year retaliation
		# observation and an active PIP have their own immutable identities.  The
		# latter must survive a later result freeze until its D+365 settlement and
		# exact capacity release have closed.
		set_variable = { name = zg361_b2_m014_state value = 0 }
		if = {
			limit = {
				NOT = { var:zg361_b2_m015_object_active = 1 }
				NOT = { var:zg361_b2_m016_object_active = 1 }
				NOT = { var:zg361_b2_m017_object_active = 1 }
				NOT = {
					OR = {
						var:zg361_b2_pip_state = 1
						var:zg361_b2_pip_state = 2
						var:zg361_b2_pip_state = 4
					}
				}
			}
			set_variable = { name = zg361_b2_m015_state value = 0 }
			set_variable = { name = zg361_b2_m016_state value = 0 }
			set_variable = { name = zg361_b2_m017_state value = 0 }
		}
		set_variable = { name = zg361_b2_m069_state value = 0 }
		set_variable = { name = zg361_b2_m069_receipt_serial value = 0 }
		set_variable = { name = zg361_b2_m071_state value = 0 }
		set_variable = { name = zg361_b2_m073_state value = 0 }
		set_variable = { name = zg361_b2_m074_state value = 0 }
		set_variable = { name = zg361_b2_m075_state value = 0 }
		set_variable = { name = zg361_b2_m076_state value = 0 }
		set_variable = { name = zg361_b2_m077_state value = 0 }
		set_variable = { name = zg361_b2_m078_state value = 0 }
		set_variable = { name = zg361_b2_m079_state value = 0 }
		set_variable = { name = zg361_b2_m080_state value = 0 }
		set_variable = { name = zg361_b2_m358_state value = 0 }
		set_variable = { name = zg361_b2_m359_state value = 0 }

		zg361_b2_m069_open_business_object_effect = yes
		zg361_b2_m072_open_business_object_effect = yes
		zg361_b2_m081_open_business_object_effect = yes
		if = {
			limit = { var:zg361_b2_m069_object_active = 1 }
			set_variable = { name = zg361_b2_m069_state value = 1 }
		}
		if = {
			limit = { var:zg361_b2_m072_object_active = 1 }
			zg361_b2_m072_lock_pre_delivery_access_effect = yes
		}
		if = {
			limit = { var:zg361_b2_m081_object_active = 1 }
			zg361_b2_m081_project_case_access_effect = yes
		}
		zg361_b2_m078_record_cohort_sample_effect = yes
		debug_log = "ZG361B2: result-bound justice case prepared"
	}
}

zg361_b2_m072_lock_pre_delivery_access_effect = {
	set_variable = { name = zg361_b2_m072_state value = 1 }
	set_variable = { name = zg361_b2_m072_acl_version value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m072_pre_delivery_reads value = 0 }
	set_variable = { name = zg361_b2_m072_headstart_days value = 0 }
	set_variable = { name = zg361_b2_m072_receipt_serial value = var:zg361_b2_case_serial }
}

# The existing personal-statement decision is the real read entry point.  A
# pre-delivery attempt is logged once and remains summary-only; a delivered
# case records one lawful subject read without minting a second consequence.
zg361_b2_record_case_access_effect = {
	if = {
		limit = {
			var:zg361_b2_m072_object_active = 1
			var:zg361_b2_m072_route = 2
			var:zg361_b2_case_subject = this
			var:zg361_b2_m072_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_notice_state = 1
			var:zg361_b2_m072_pre_delivery_reads = 0
		}
		set_variable = { name = zg361_b2_m072_pre_delivery_reads value = 1 }
		set_variable = { name = zg361_b2_m072_reader value = this }
		set_variable = { name = zg361_b2_m072_source value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m072_read_year value = current_year }
		set_variable = { name = zg361_b2_m072_state value = 2 }
		set_variable = { name = zg361_b2_m081_omitted_before_delivery value = 1 }
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_leak_deadline_owner }
		save_scope_as = zg361_b2_leak_deadline_subject
		save_scope_value_as = { name = zg361_b2_leak_deadline_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_leak_deadline_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_leak_deadline_state value = var:zg361_b2_m072_state }
		trigger_event = { id = zg361b2.121 days = 30 }
	}
	else_if = {
		limit = {
			var:zg361_b2_m072_object_active = 1
			var:zg361_b2_m072_route = 1
			var:zg361_b2_case_subject = this
			var:zg361_b2_notice_state = 1
		}
		set_variable = { name = zg361_b2_m072_last_denied_reader value = this }
		set_variable = { name = zg361_b2_m072_last_denied_year value = current_year }
		set_variable = { name = zg361_b2_m072_acl_enforced value = 1 }
	}
	else_if = {
		limit = {
			var:zg361_b2_m081_object_active = 1
			var:zg361_b2_case_subject = this
			var:zg361_b2_m081_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_notice_state >= 3
		}
		set_variable = { name = zg361_b2_m081_subject_read_receipt value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m081_last_read_year value = current_year }
	}
}

zg361_b2_m081_project_case_access_effect = {
	set_variable = { name = zg361_b2_m081_state value = 1 }
	set_variable = { name = zg361_b2_m081_access_level value = 1 } # subject summary
	set_variable = { name = zg361_b2_m081_visible_fields value = 4 }
	set_variable = { name = zg361_b2_m081_acl_subject_level value = 1 }
	set_variable = { name = zg361_b2_m081_acl_manager_level value = 2 }
	set_variable = { name = zg361_b2_m081_acl_central_level value = 3 }
	set_variable = { name = zg361_b2_m081_direct_grade_writer value = var:zg361_b2_case_owner }
	if = {
		limit = { var:zg361_b2_m081_route = 2 }
		set_variable = { name = zg361_b2_m081_summary_compressed value = 1 }
		set_variable = { name = zg361_b2_m081_omitted_fields value = 4 }
	}
	set_variable = { name = zg361_b2_m081_correction_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_m081_receipt_serial value = var:zg361_b2_case_serial }
}

zg361_b2_on_notice_delivered_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_case_owner
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			has_variable = zg361_b2_case_subject
			var:zg361_b2_case_subject = this
			has_variable = zg361_b2_case_cycle
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			has_variable = zg361_b2_case_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			has_variable = zg361_b2_notice_state
			var:zg361_b2_notice_state = 1
			var:zg361_result_case_state = 3
			var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
		}
		if = {
			limit = { var:zg361_b2_m069_object_active = 1 }
			zg361_b2_m069_record_delivery_effect = yes
			zg361_b2_m069_consume_business_object_effect = yes
		}
		else = {
			# The shared settlement currently calls this adapter after posting.
			# Keep the violation visible until the shared pre-settlement gate lands.
			set_variable = { name = zg361_b2_m069_c_post_settlement_violation value = 1 }
			zg361_b2_m069_post_policy_debt_effect = yes
		}
		if = {
			limit = { var:zg361_b2_m072_object_active = 1 }
			zg361_b2_m072_close_access_log_effect = yes
		}
		if = {
			limit = { var:zg361_b2_m081_object_active = 1 }
			zg361_b2_m081_publish_case_projection_effect = yes
		}
		zg361_b2_m015_open_pip_effect = yes
		debug_log = "ZG361B2: delivered result consumed by justice runtime"
	}
	else = { debug_log = "ZG361B2: stale delivered-result adapter ignored" }
}

zg361_b2_m069_record_delivery_effect = {
	set_variable = { name = zg361_b2_notice_state value = 3 } # delivered/appeal open
	set_variable = { name = zg361_b2_delivery_year value = current_year }
	set_variable = { name = zg361_b2_delivery_method value = var:zg361_result_delivery_method }
	set_variable = { name = zg361_b2_m069_state value = 3 }
	set_variable = { name = zg361_b2_m069_receipt_serial value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m069_appeal_clock_open value = 1 }
	if = {
		limit = { var:zg361_b2_m069_route = 2 }
		set_variable = { name = zg361_b2_m069_aggregate_publication_shortcut value = 1 }
		set_variable = { name = zg361_b2_m069_individual_reason_unseen_risk value = 1 }
		var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
	}
	if = {
		limit = {
			has_variable = zg361_result_delivery_witness
			var:zg361_result_delivery_witness_receipt = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_m069_witness value = var:zg361_result_delivery_witness }
		set_variable = { name = zg361_b2_m069_witness_receipt value = var:zg361_result_delivery_witness_receipt }
	}
}

zg361_b2_m072_close_access_log_effect = {
	if = {
		limit = { var:zg361_b2_m072_pre_delivery_reads > 0 }
		set_variable = { name = zg361_b2_m072_headstart_days value = 7 }
		set_variable = { name = zg361_b2_m072_investigation_result value = 0 }
	}
	else = {
		set_variable = { name = zg361_b2_m072_state value = 3 }
		set_variable = { name = zg361_b2_m072_investigation_result value = 0 }
		zg361_b2_m072_consume_business_object_effect = yes
	}
}

zg361_b2_m081_publish_case_projection_effect = {
	set_variable = { name = zg361_b2_m081_state value = 3 }
	if = {
		limit = { var:zg361_b2_m081_route = 1 }
		set_variable = { name = zg361_b2_m081_access_level value = 3 }
		set_variable = { name = zg361_b2_m081_visible_fields value = 8 }
		set_variable = { name = zg361_b2_m081_raw_evidence_preserved value = 1 }
	}
	else = {
		set_variable = { name = zg361_b2_m081_access_level value = 1 }
		set_variable = { name = zg361_b2_m081_visible_fields value = 4 }
		set_variable = { name = zg361_b2_m081_compression_appeal_evidence value = 1 }
	}
	zg361_b2_m081_consume_business_object_effect = yes
}

# ---------------------------------------------------------------------------
# #015–#017: bounded PIP opened only after the existing settlement receipt.
# ---------------------------------------------------------------------------

# Freeze one real, non-manager-authored reviewer at case creation.  The
# superior-of-owner route is preferred; a same-level manager in the superior's
# cohort and then an eligible manager vassal are deterministic fallbacks.  All
# routes exclude both frozen parties and observable close/personal conflicts.
# No abstract review seat and no manager choice can satisfy this producer.
zg361_b2_assign_pip_independent_reviewer_effect = {
	set_variable = { name = zg361_b2_pip_reviewer_assignment_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_pip_reviewer_assignment_subject value = this }
	set_variable = { name = zg361_b2_pip_reviewer_assignment_cycle value = var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_pip_reviewer_assignment_case value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_pip_reviewer_assignment_status value = 0 }
	set_variable = { name = zg361_b2_pip_reviewer_assignment_red_code value = 2 } # no eligible real reviewer
	remove_variable = zg361_b2_pip_independent_reviewer
	remove_variable = zg361_b2_pip_reviewer_assignment_source
	remove_variable = zg361_b2_pip_reviewer_assignment_receipt
	save_temporary_scope_as = zg361_b2_pip_review_subject
	var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_pip_review_owner }
	if = {
		limit = {
			scope:zg361_b2_pip_review_owner = {
				exists = liege
				liege = {
					zg361_is_celestial_liege_trigger = yes
					is_available = yes
					is_imprisoned = no
					NOT = { this = scope:zg361_b2_pip_review_owner }
					NOT = { this = scope:zg361_b2_pip_review_subject }
					NOT = { is_close_family_of = scope:zg361_b2_pip_review_owner }
					NOT = { is_close_family_of = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_friend = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_lover = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_rival = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_friend = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_lover = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_rival = scope:zg361_b2_pip_review_subject }
				}
			}
		}
		scope:zg361_b2_pip_review_owner = { liege = { save_scope_as = zg361_b2_pip_review_candidate } }
		set_variable = { name = zg361_b2_pip_reviewer_assignment_source value = 1 } # owner's superior
	}
	if = {
		limit = {
			NOT = { exists = scope:zg361_b2_pip_review_candidate }
			scope:zg361_b2_pip_review_owner = { exists = liege }
		}
		scope:zg361_b2_pip_review_owner = {
			liege = {
				ordered_vassal = {
					limit = {
						zg361_is_celestial_liege_trigger = yes
						is_available = yes
						is_imprisoned = no
						NOT = { this = scope:zg361_b2_pip_review_owner }
						NOT = { this = scope:zg361_b2_pip_review_subject }
						NOT = { is_close_family_of = scope:zg361_b2_pip_review_owner }
						NOT = { is_close_family_of = scope:zg361_b2_pip_review_subject }
						NOT = { has_relation_friend = scope:zg361_b2_pip_review_owner }
						NOT = { has_relation_lover = scope:zg361_b2_pip_review_owner }
						NOT = { has_relation_rival = scope:zg361_b2_pip_review_owner }
						NOT = { has_relation_friend = scope:zg361_b2_pip_review_subject }
						NOT = { has_relation_lover = scope:zg361_b2_pip_review_subject }
						NOT = { has_relation_rival = scope:zg361_b2_pip_review_subject }
					}
					order_by = stewardship
					position = 0
					save_scope_as = zg361_b2_pip_review_candidate
				}
			}
		}
		if = {
			limit = { exists = scope:zg361_b2_pip_review_candidate }
			set_variable = { name = zg361_b2_pip_reviewer_assignment_source value = 2 } # peer manager
		}
	}
	if = {
		limit = { NOT = { exists = scope:zg361_b2_pip_review_candidate } }
		scope:zg361_b2_pip_review_owner = {
			ordered_vassal = {
				limit = {
					zg361_is_celestial_liege_trigger = yes
					is_available = yes
					is_imprisoned = no
					NOT = { this = scope:zg361_b2_pip_review_owner }
					NOT = { this = scope:zg361_b2_pip_review_subject }
					NOT = { is_close_family_of = scope:zg361_b2_pip_review_owner }
					NOT = { is_close_family_of = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_friend = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_lover = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_rival = scope:zg361_b2_pip_review_owner }
					NOT = { has_relation_friend = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_lover = scope:zg361_b2_pip_review_subject }
					NOT = { has_relation_rival = scope:zg361_b2_pip_review_subject }
				}
				order_by = stewardship
				position = 0
				save_scope_as = zg361_b2_pip_review_candidate
			}
		}
		if = {
			limit = { exists = scope:zg361_b2_pip_review_candidate }
			set_variable = { name = zg361_b2_pip_reviewer_assignment_source value = 3 } # eligible subordinate manager
		}
	}
	if = {
		limit = { exists = scope:zg361_b2_pip_review_candidate }
		set_variable = { name = zg361_b2_pip_independent_reviewer value = scope:zg361_b2_pip_review_candidate }
		set_variable = { name = zg361_b2_pip_reviewer_assignment_status value = 1 }
		set_variable = { name = zg361_b2_pip_reviewer_assignment_red_code value = 0 }
		set_variable = { name = zg361_b2_pip_reviewer_assignment_receipt value = var:zg361_b2_case_serial }
	}
}

zg361_b2_m015_open_pip_effect = {
	# #182 and every later PP projection consume this frozen gate.  Presence of
	# an evidence field is not evidence: forced-distribution 3.25 with a healthy
	# absolute result therefore does not silently become a PIP.
	set_variable = { name = zg361_b2_pip_gate_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_pip_gate_subject value = this }
	set_variable = { name = zg361_b2_pip_gate_cycle value = var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_pip_gate_case value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_pip_gate_threshold value = 3 }
	set_variable = { name = zg361_b2_pip_gate_component_count value = 0 }
	set_variable = { name = zg361_b2_pip_gate_evidence_complete value = 0 }
	set_variable = { name = zg361_b2_pip_gate_status value = 0 } # typed RED until the frozen facts exist
	if = {
		limit = {
			has_variable = zg361_result_absolute_grade
			has_variable = zg361_result_kpi_frozen
			has_variable = zg361_result_evidence_governance
			has_variable = zg361_result_evidence_capability
			has_variable = zg361_result_evidence_growth
			has_variable = zg361_result_evidence_superior
			has_variable = zg361_result_evidence_values
			has_variable = zg361_result_evidence_collaboration
			has_variable = zg361_result_evidence_jingcha
			has_variable = zg361_result_evidence_organization
		}
		set_variable = { name = zg361_b2_pip_gate_evidence_complete value = 1 }
		if = { limit = { var:zg361_result_absolute_grade = 1 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_kpi_frozen < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_governance < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_capability < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_growth < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_superior < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_values < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_collaboration < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_jingcha < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		if = { limit = { var:zg361_result_evidence_organization < 0 } change_variable = { name = zg361_b2_pip_gate_component_count add = 1 } }
		set_variable = { name = zg361_b2_pip_gate_status value = 2 } # evidence complete, below threshold
		if = {
			limit = {
				var:zg361_result_grade = 1
				var:zg361_b2_pip_gate_component_count >= var:zg361_b2_pip_gate_threshold
			}
			set_variable = { name = zg361_b2_pip_gate_status value = 1 }
		}
	}
	if = {
		limit = {
			var:zg361_b2_pip_gate_status = 1
			NOT = { var:zg361_b2_m015_object_active = 1 }
			NOT = { var:zg361_b2_m016_object_active = 1 }
			NOT = { var:zg361_b2_m017_object_active = 1 }
			NOT = {
				OR = {
					var:zg361_b2_pip_state = 1
					var:zg361_b2_pip_state = 2
					var:zg361_b2_pip_state = 4
				}
			}
		}
		# A terminal earlier case may still have response/support/outcome fields.
		# Clear the whole case-bound tuple before writing this new identity; the
		# next response author must remain absent until the subject answers.
		zg361_b2_clear_pip_case_tuple_effect = yes
		set_variable = { name = zg361_b2_pip_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_pip_subject value = this }
		set_variable = { name = zg361_b2_pip_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_pip_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_pip_state value = 0 } # provisional until policy/object gate
		zg361_b2_m015_open_business_object_effect = yes
		if = {
			limit = { var:zg361_b2_m015_object_active = 1 }
		set_variable = { name = zg361_b2_pip_state value = 1 } # acknowledgement pending
		set_variable = { name = zg361_b2_pip_task_kind value = 3 } # collaboration/default
		set_variable = { name = zg361_b2_pip_progress_baseline_task_kind value = 3 }
		set_variable = { name = zg361_b2_pip_progress_source_kind value = 3 } # collaboration component
		if = {
			limit = { is_governor = yes }
			set_variable = { name = zg361_b2_pip_task_kind value = 1 } # governance, subject-controllable
			set_variable = { name = zg361_b2_pip_progress_baseline_task_kind value = 1 }
			set_variable = { name = zg361_b2_pip_progress_source_kind value = 1 } # governance component
		}
		else_if = {
			limit = { highest_held_title_tier >= tier_county }
			set_variable = { name = zg361_b2_pip_task_kind value = 2 } # local capability
			set_variable = { name = zg361_b2_pip_progress_baseline_task_kind value = 2 }
			set_variable = { name = zg361_b2_pip_progress_source_kind value = 2 } # capability component
		}
		set_variable = { name = zg361_b2_pip_task_controllable value = 1 }
		set_variable = { name = zg361_b2_pip_policy_route value = var:zg361_b2_m015_route }
		# #016 task progress is a real, subject-scoped observation mapped to one
		# official KPI component: governor→governance, county+→capability and
		# barony/default→collaboration. Manager policy never writes either endpoint.
		set_variable = { name = zg361_b2_pip_progress_baseline_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_pip_progress_baseline_subject value = this }
		set_variable = { name = zg361_b2_pip_progress_baseline_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_pip_progress_baseline_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_pip_progress_baseline_status value = 0 }
		set_variable = { name = zg361_b2_pip_progress_baseline_red_code value = 1 }
		if = {
			limit = {
				exists = liege
				liege = var:zg361_b2_case_owner
			}
			set_variable = { name = zg361_b2_pip_progress_baseline_value value = zg361_kpi_collaboration_evidence_value }
			set_variable = { name = zg361_b2_pip_progress_target_value value = { value = zg361_kpi_collaboration_evidence_value add = 1 } }
			if = {
				limit = { is_governor = yes }
				set_variable = { name = zg361_b2_pip_progress_baseline_value value = zg361_kpi_governance_evidence_value }
				set_variable = { name = zg361_b2_pip_progress_target_value value = { value = zg361_kpi_governance_evidence_value add = 1 } }
			}
			else_if = {
				limit = { highest_held_title_tier >= tier_county }
				set_variable = { name = zg361_b2_pip_progress_baseline_value value = zg361_kpi_capability_evidence_value }
				set_variable = { name = zg361_b2_pip_progress_target_value value = { value = zg361_kpi_capability_evidence_value add = 1 } }
			}
			set_variable = { name = zg361_b2_pip_progress_baseline_year value = current_year }
			set_variable = { name = zg361_b2_pip_progress_baseline_status value = 1 }
			set_variable = { name = zg361_b2_pip_progress_baseline_red_code value = 0 }
		}
		zg361_b2_assign_pip_independent_reviewer_effect = yes
		set_variable = { name = zg361_b2_pip_support_reserved value = 0 }
		set_variable = { name = zg361_b2_pip_support_absent value = 0 }
		set_variable = { name = zg361_b2_pip_support_budget_allocated value = 0 }
		set_variable = { name = zg361_b2_pip_support_budget_spent value = 0 }
		remove_variable = zg361_b2_pip_support_mentor
		if = {
			limit = { var:zg361_b2_m015_route = 2 }
			set_variable = { name = zg361_b2_pip_high_pressure value = 1 }
			set_variable = { name = zg361_b2_pip_refusal_major_evidence value = 1 }
			add_stress = minor_stress_gain
		}
		set_variable = { name = zg361_b2_pip_refusal_receipt value = 0 }
		set_variable = { name = zg361_b2_pip_subject_response value = 0 }
		set_variable = { name = zg361_b2_pip_subject_response_case value = 0 }
		set_variable = { name = zg361_b2_pip_goal_revision_used value = 0 }
		set_variable = { name = zg361_b2_m015_state value = 1 }
		set_variable = { name = zg361_b2_m015_receipt_serial value = var:zg361_b2_pip_case }
		add_character_modifier = { modifier = zg361_pip years = 1 }
		if = {
			limit = { is_ai = yes }
			zg361_b2_accept_pip_effect = yes
		}
		else = {
			var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_pip_prompt_owner }
			save_scope_as = zg361_b2_pip_prompt_subject
			save_scope_value_as = { name = zg361_b2_pip_prompt_cycle value = var:zg361_b2_pip_cycle }
			save_scope_value_as = { name = zg361_b2_pip_prompt_case value = var:zg361_b2_pip_case }
			save_scope_value_as = { name = zg361_b2_pip_prompt_state value = var:zg361_b2_pip_state }
			trigger_event = { id = zg361b2.40 days = 2 }
		}
		}
		else = {
			# Route C records only its bounded policy debt; it cannot leave a
			# provisional or stale partial tuple for PP/provider to mistake for
			# a real case.
			zg361_b2_clear_pip_case_tuple_effect = yes
		}
	}
	else_if = {
		limit = { var:zg361_b2_pip_gate_status = 1 }
		set_variable = { name = zg361_b2_pip_gate_status value = 3 } # qualified but another PIP is active
	}
}

zg361_b2_accept_pip_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_owner = var:zg361_b2_m015_object_owner
			var:zg361_b2_pip_cycle = var:zg361_b2_m015_object_cycle
			var:zg361_b2_pip_case = var:zg361_b2_m015_object_receipt_case
			var:zg361_b2_pip_state = 1
			var:zg361_b2_m015_receipt_serial = var:zg361_b2_pip_case
			var:zg361_b2_pip_subject_response = 0
		}
		set_variable = { name = zg361_b2_pip_subject_response value = 1 }
		set_variable = { name = zg361_b2_pip_subject_response_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_subject_response_author value = this }
		set_variable = { name = zg361_b2_pip_state value = 2 } # executing
		set_variable = { name = zg361_b2_m015_state value = 2 }
		zg361_b2_m016_commit_support_effect = yes
		zg361_b2_schedule_pip_deadline_effect = yes
	}
}

zg361_b2_negotiate_pip_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_owner = var:zg361_b2_m015_object_owner
			var:zg361_b2_pip_cycle = var:zg361_b2_m015_object_cycle
			var:zg361_b2_pip_case = var:zg361_b2_m015_object_receipt_case
			var:zg361_b2_pip_state = 1
			var:zg361_b2_m015_receipt_serial = var:zg361_b2_pip_case
			var:zg361_b2_pip_subject_response = 0
		}
		set_variable = { name = zg361_b2_pip_subject_response value = 2 }
		set_variable = { name = zg361_b2_pip_subject_response_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_subject_response_author value = this }
		set_variable = { name = zg361_b2_pip_goal_revision_used value = 1 }
		set_variable = { name = zg361_b2_pip_state value = 2 }
		set_variable = { name = zg361_b2_m015_state value = 2 }
		zg361_b2_m016_commit_support_effect = yes
		zg361_b2_schedule_pip_deadline_effect = yes
	}
}

zg361_b2_refuse_pip_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_owner = var:zg361_b2_m015_object_owner
			var:zg361_b2_pip_cycle = var:zg361_b2_m015_object_cycle
			var:zg361_b2_pip_case = var:zg361_b2_m015_object_receipt_case
			var:zg361_b2_pip_state = 1
			var:zg361_b2_pip_refusal_receipt = 0
			var:zg361_b2_pip_subject_response = 0
		}
		set_variable = { name = zg361_b2_pip_subject_response value = 3 }
		set_variable = { name = zg361_b2_pip_subject_response_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_subject_response_author value = this }
		set_variable = { name = zg361_b2_pip_refusal_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_state value = 5 } # refused terminal
		set_variable = { name = zg361_b2_m015_state value = 5 }
		set_variable = { name = zg361_b2_pip_performance_evidence_delta value = -15 }
		zg361_b2_publish_pip_performance_evidence_effect = yes
		remove_character_modifier = zg361_pip
		zg361_b2_m015_consume_business_object_effect = yes
		# Refusal is next-cycle evidence only; it does not settle another current penalty.
		debug_log = "ZG361B2: PIP refusal recorded without current-cycle double penalty"
	}
}

zg361_b2_m016_commit_support_effect = {
	zg361_b2_m016_open_business_object_effect = yes
	save_temporary_scope_as = zg361_b2_support_subject
	var:zg361_b2_pip_owner = { save_temporary_scope_as = zg361_b2_support_owner }
	set_variable = { name = zg361_b2_pip_support_reserved value = 0 }
	# A support package is atomic: one real mentor, one capacity slot and the
	# exact public budget must all exist before any of them is consumed.
	if = {
		limit = {
			var:zg361_b2_m016_object_active = 1
			var:zg361_b2_m016_route = 1
		}
		scope:zg361_b2_support_owner = {
			ordered_vassal = {
				limit = {
					is_alive = yes
					NOT = { this = scope:zg361_b2_support_owner }
					NOT = { this = scope:zg361_b2_support_subject }
				}
				order_by = learning
				position = 0
				save_scope_as = zg361_b2_support_mentor
			}
		}
		if = {
			limit = {
				exists = scope:zg361_b2_support_mentor
				scope:zg361_b2_support_owner = {
					government_has_flag = government_has_treasury
					treasury >= 25
				}
			}
			scope:zg361_b2_support_owner = {
		if = {
			limit = { NOT = { has_variable = zg361_b2_pip_capacity_used } }
			set_variable = { name = zg361_b2_pip_capacity_used value = 0 }
		}
		if = {
			limit = { var:zg361_b2_pip_capacity_used < 2 }
			change_variable = { name = zg361_b2_pip_capacity_used add = 1 }
			remove_treasury = 25
			scope:zg361_b2_support_subject = {
				set_variable = { name = zg361_b2_pip_support_reserved value = 1 }
				set_variable = { name = zg361_b2_pip_support_hours value = 12 }
				set_variable = { name = zg361_b2_pip_support_attention value = 1 }
				set_variable = { name = zg361_b2_pip_support_mentor value = scope:zg361_b2_support_mentor }
				set_variable = { name = zg361_b2_pip_support_budget_owner value = scope:zg361_b2_support_owner }
				set_variable = { name = zg361_b2_pip_support_budget_allocated value = 25 }
				set_variable = { name = zg361_b2_pip_support_budget_spent value = 25 }
				set_variable = { name = zg361_b2_pip_support_absent value = 0 }
				set_variable = { name = zg361_b2_m016_state value = 2 }
				set_variable = { name = zg361_b2_m016_receipt_serial value = var:zg361_b2_pip_case }
			}
		}
			}
		}
	}
	if = {
		limit = {
			var:zg361_b2_m016_object_active = 1
			var:zg361_b2_pip_support_reserved = 0
		}
		set_variable = { name = zg361_b2_pip_support_hours value = 0 }
		set_variable = { name = zg361_b2_pip_support_attention value = 0 }
		set_variable = { name = zg361_b2_pip_support_absent value = 1 }
		set_variable = { name = zg361_b2_m016_state value = 1 }
		set_variable = { name = zg361_b2_m016_receipt_serial value = var:zg361_b2_pip_case }
		if = {
			limit = { var:zg361_b2_m016_route = 2 }
			set_variable = { name = zg361_b2_pip_support_withheld value = 1 }
			set_variable = { name = zg361_b2_pip_support_budget_unchanged value = 1 }
		}
		else = {
			set_variable = { name = zg361_b2_pip_support_atomic_shortfall value = 1 }
		}
	}
}

zg361_b2_release_pip_support_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_support_reserved = 1
			var:zg361_b2_m016_receipt_serial = var:zg361_b2_pip_case
		}
		var:zg361_b2_pip_owner = {
			if = {
				limit = { has_variable = zg361_b2_pip_capacity_used var:zg361_b2_pip_capacity_used >= 1 }
				change_variable = { name = zg361_b2_pip_capacity_used add = -1 }
			}
		}
		set_variable = { name = zg361_b2_pip_support_reserved value = 0 }
		set_variable = { name = zg361_b2_pip_support_released value = 1 }
	}
}

zg361_b2_publish_pip_performance_evidence_effect = {
	if = {
		limit = {
			OR = {
				NOT = { has_variable = zg361_b2_pip_performance_evidence_status }
				NOT = { var:zg361_b2_pip_performance_evidence_status = 1 }
			}
			OR = {
				var:zg361_b2_pip_performance_evidence_delta = 10
				var:zg361_b2_pip_performance_evidence_delta = -10
				var:zg361_b2_pip_performance_evidence_delta = -15
			}
		}
		set_variable = { name = zg361_b2_pip_performance_evidence_owner value = var:zg361_b2_pip_owner }
		set_variable = { name = zg361_b2_pip_performance_evidence_subject value = this }
		set_variable = { name = zg361_b2_pip_performance_evidence_source_cycle value = var:zg361_b2_pip_cycle }
		set_variable = { name = zg361_b2_pip_performance_evidence_source_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_performance_evidence_due_cycle value = var:zg361_b2_pip_cycle }
		change_variable = { name = zg361_b2_pip_performance_evidence_due_cycle add = 1 }
		set_variable = { name = zg361_b2_pip_performance_evidence_status value = 1 }
	}
	else = { debug_log = "ZG361B2: pending PIP performance evidence conserved; duplicate publish ignored" }
}

zg361_b2_record_pip_midpoint_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_state = 2
			OR = {
				NOT = { has_variable = zg361_b2_pip_midpoint_receipt }
				NOT = { var:zg361_b2_pip_midpoint_receipt = var:zg361_b2_pip_case }
			}
		}
		set_variable = { name = zg361_b2_pip_midpoint_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_midpoint_resource_delivery_valid value = 0 }
		if = {
			limit = {
				var:zg361_b2_pip_support_reserved = 1
				var:zg361_b2_pip_support_budget_spent = 25
				var:zg361_b2_pip_support_hours = 12
			}
			set_variable = { name = zg361_b2_pip_midpoint_resource_delivery_valid value = 1 }
		}
		# Fail closed until the immutable baseline provenance matches this exact
		# PIP.  The producer then re-evaluates the subject's real eight-component
		# KPI and records current-baseline; support delivery is a separate fact and
		# can never manufacture this delta.
		set_variable = { name = zg361_b2_pip_midpoint_progress_status value = 0 }
		set_variable = { name = zg361_b2_pip_midpoint_progress_red_code value = 1 }
		if = {
			limit = {
				has_variable = zg361_b2_pip_progress_source_kind
				has_variable = zg361_b2_pip_progress_baseline_owner
				has_variable = zg361_b2_pip_progress_baseline_subject
				has_variable = zg361_b2_pip_progress_baseline_cycle
				has_variable = zg361_b2_pip_progress_baseline_case
				has_variable = zg361_b2_pip_progress_baseline_task_kind
				has_variable = zg361_b2_pip_progress_baseline_value
				has_variable = zg361_b2_pip_progress_target_value
				has_variable = zg361_b2_pip_progress_baseline_status
				has_variable = zg361_b2_pip_progress_baseline_red_code
				var:zg361_b2_pip_progress_source_kind = var:zg361_b2_pip_progress_baseline_task_kind
				var:zg361_b2_pip_progress_source_kind >= 1
				var:zg361_b2_pip_progress_source_kind <= 3
				var:zg361_b2_pip_progress_baseline_owner = var:zg361_b2_pip_owner
				var:zg361_b2_pip_progress_baseline_subject = this
				var:zg361_b2_pip_progress_baseline_cycle = var:zg361_b2_pip_cycle
				var:zg361_b2_pip_progress_baseline_case = var:zg361_b2_pip_case
				var:zg361_b2_pip_progress_baseline_task_kind = var:zg361_b2_pip_task_kind
				var:zg361_b2_pip_progress_baseline_status = 1
				var:zg361_b2_pip_progress_baseline_red_code = 0
				exists = liege
				liege = var:zg361_b2_pip_owner
			}
			set_variable = { name = zg361_b2_pip_midpoint_progress_source_kind value = var:zg361_b2_pip_progress_source_kind }
			set_variable = { name = zg361_b2_pip_midpoint_progress_owner value = var:zg361_b2_pip_owner }
			set_variable = { name = zg361_b2_pip_midpoint_progress_subject value = this }
			set_variable = { name = zg361_b2_pip_midpoint_progress_cycle value = var:zg361_b2_pip_cycle }
			set_variable = { name = zg361_b2_pip_midpoint_progress_case value = var:zg361_b2_pip_case }
			set_variable = { name = zg361_b2_pip_midpoint_progress_task_kind value = var:zg361_b2_pip_task_kind }
			set_variable = { name = zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_collaboration_evidence_value }
			if = {
				limit = { var:zg361_b2_pip_progress_source_kind = 1 }
				set_variable = { name = zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_governance_evidence_value }
			}
			else_if = {
				limit = { var:zg361_b2_pip_progress_source_kind = 2 }
				set_variable = { name = zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_capability_evidence_value }
			}
			set_variable = {
				name = zg361_b2_pip_midpoint_progress_delta
				value = { value = var:zg361_b2_pip_midpoint_progress_current_value subtract = var:zg361_b2_pip_progress_baseline_value }
			}
			set_variable = { name = zg361_b2_pip_midpoint_progress_met value = 0 }
			if = {
				limit = { var:zg361_b2_pip_midpoint_progress_current_value >= var:zg361_b2_pip_progress_target_value }
				set_variable = { name = zg361_b2_pip_midpoint_progress_met value = 1 }
			}
			set_variable = { name = zg361_b2_pip_midpoint_progress_year value = current_year }
			set_variable = { name = zg361_b2_pip_midpoint_progress_status value = 1 }
			set_variable = { name = zg361_b2_pip_midpoint_progress_red_code value = 0 }
		}
		set_variable = { name = zg361_b2_pip_midpoint_state value = 2 }
	}
}

zg361_b2_schedule_pip_deadline_effect = {
	var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_pip_deadline_owner }
	save_scope_as = zg361_b2_pip_deadline_subject
	save_scope_value_as = { name = zg361_b2_pip_deadline_cycle value = var:zg361_b2_pip_cycle }
	save_scope_value_as = { name = zg361_b2_pip_deadline_case value = var:zg361_b2_pip_case }
	save_scope_value_as = { name = zg361_b2_pip_deadline_state value = var:zg361_b2_pip_state }
	trigger_event = { id = zg361b2.99 days = 180 }
	trigger_event = { id = zg361b2.100 days = 365 }
}

zg361_b2_resolve_pip_due_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_state = 2
			OR = {
				NOT = { has_variable = zg361_b2_pip_settlement_receipt }
				NOT = { var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case }
			}
		}
		remove_variable = zg361_b2_pip_outcome_code
		set_variable = { name = zg361_b2_pip_independent_review_status value = 0 }
		set_variable = { name = zg361_b2_pip_independent_review_red_code value = 2 } # assignment missing
		# Existence gates are deliberately nested. CK3 trigger blocks do not
		# promise short-circuit evaluation, so no provenance value is read before
		# its complete assignment tuple is known to exist.
		if = {
			limit = {
				has_variable = zg361_b2_pip_independent_reviewer
				has_variable = zg361_b2_pip_reviewer_assignment_owner
				has_variable = zg361_b2_pip_reviewer_assignment_subject
				has_variable = zg361_b2_pip_reviewer_assignment_cycle
				has_variable = zg361_b2_pip_reviewer_assignment_case
				has_variable = zg361_b2_pip_reviewer_assignment_source
				has_variable = zg361_b2_pip_reviewer_assignment_status
				has_variable = zg361_b2_pip_reviewer_assignment_red_code
				has_variable = zg361_b2_pip_reviewer_assignment_receipt
			}
			set_variable = { name = zg361_b2_pip_independent_review_red_code value = 3 } # assignment provenance mismatch
			if = {
				limit = {
					var:zg361_b2_pip_reviewer_assignment_owner = var:zg361_b2_pip_owner
					var:zg361_b2_pip_reviewer_assignment_subject = this
					var:zg361_b2_pip_reviewer_assignment_cycle = var:zg361_b2_pip_cycle
					var:zg361_b2_pip_reviewer_assignment_case = var:zg361_b2_pip_case
					var:zg361_b2_pip_reviewer_assignment_status = 1
					var:zg361_b2_pip_reviewer_assignment_red_code = 0
					var:zg361_b2_pip_reviewer_assignment_receipt = var:zg361_b2_pip_case
					var:zg361_b2_pip_reviewer_assignment_source >= 1
					var:zg361_b2_pip_reviewer_assignment_source <= 3
					var:zg361_b2_pip_independent_reviewer = {
						zg361_is_celestial_liege_trigger = yes
						is_available = yes
						is_imprisoned = no
						NOT = { this = root }
						NOT = { this = root.var:zg361_b2_pip_owner }
						NOT = { is_close_family_of = root }
						NOT = { is_close_family_of = root.var:zg361_b2_pip_owner }
						NOT = { has_relation_friend = root }
						NOT = { has_relation_lover = root }
						NOT = { has_relation_rival = root }
						NOT = { has_relation_friend = root.var:zg361_b2_pip_owner }
						NOT = { has_relation_lover = root.var:zg361_b2_pip_owner }
						NOT = { has_relation_rival = root.var:zg361_b2_pip_owner }
					}
				}
				set_variable = { name = zg361_b2_pip_independent_review_red_code value = 4 } # midpoint provenance missing
				if = {
					limit = {
						has_variable = zg361_b2_pip_midpoint_receipt
						has_variable = zg361_b2_pip_midpoint_progress_status
						has_variable = zg361_b2_pip_midpoint_progress_red_code
						has_variable = zg361_b2_pip_midpoint_progress_owner
						has_variable = zg361_b2_pip_midpoint_progress_subject
						has_variable = zg361_b2_pip_midpoint_progress_cycle
						has_variable = zg361_b2_pip_midpoint_progress_case
						has_variable = zg361_b2_pip_midpoint_progress_task_kind
						has_variable = zg361_b2_pip_midpoint_progress_delta
						has_variable = zg361_b2_pip_midpoint_progress_met
					}
					set_variable = { name = zg361_b2_pip_independent_review_red_code value = 5 } # midpoint provenance mismatch
					if = {
						limit = {
							var:zg361_b2_pip_midpoint_receipt = var:zg361_b2_pip_case
							var:zg361_b2_pip_midpoint_progress_status = 1
							var:zg361_b2_pip_midpoint_progress_red_code = 0
							var:zg361_b2_pip_midpoint_progress_owner = var:zg361_b2_pip_owner
							var:zg361_b2_pip_midpoint_progress_subject = this
							var:zg361_b2_pip_midpoint_progress_cycle = var:zg361_b2_pip_cycle
							var:zg361_b2_pip_midpoint_progress_case = var:zg361_b2_pip_case
							var:zg361_b2_pip_midpoint_progress_task_kind = var:zg361_b2_pip_task_kind
						}
						set_variable = { name = zg361_b2_pip_independent_review_red_code value = 6 } # later result missing
						if = {
							limit = {
								has_variable = zg361_result_case_owner
								has_variable = zg361_result_cycle_serial
								has_variable = zg361_result_case_serial
								has_variable = zg361_result_case_state
								has_variable = zg361_result_grade
								has_variable = zg361_last_grade
							}
							set_variable = { name = zg361_b2_pip_independent_review_red_code value = 7 } # later result provenance mismatch
							if = {
								limit = {
									var:zg361_result_case_owner = var:zg361_b2_pip_owner
									var:zg361_result_cycle_serial > var:zg361_b2_pip_cycle
									var:zg361_result_case_serial > 0
									var:zg361_result_case_state >= 3
									var:zg361_result_grade = var:zg361_last_grade
									var:zg361_result_grade >= 1
									var:zg361_result_grade <= 3
								}
								# The conclusion is executed in the independently assigned
								# character's scope. That character signs both its own latest
								# review receipt and the subject's immutable conclusion tuple.
								var:zg361_b2_pip_independent_reviewer = {
									set_variable = { name = zg361_b2_last_pip_review_subject value = root }
									set_variable = { name = zg361_b2_last_pip_review_owner value = root.var:zg361_b2_pip_owner }
									set_variable = { name = zg361_b2_last_pip_review_cycle value = root.var:zg361_b2_pip_cycle }
									set_variable = { name = zg361_b2_last_pip_review_case value = root.var:zg361_b2_pip_case }
									set_variable = { name = zg361_b2_last_pip_review_result_case value = root.var:zg361_result_case_serial }
									root = {
										set_variable = { name = zg361_b2_pip_independent_review_reviewer value = var:zg361_b2_pip_independent_reviewer }
										set_variable = { name = zg361_b2_pip_independent_review_owner value = var:zg361_b2_pip_owner }
										set_variable = { name = zg361_b2_pip_independent_review_subject value = this }
										set_variable = { name = zg361_b2_pip_independent_review_cycle value = var:zg361_b2_pip_cycle }
										set_variable = { name = zg361_b2_pip_independent_review_case value = var:zg361_b2_pip_case }
										set_variable = { name = zg361_b2_pip_independent_review_result_owner value = var:zg361_result_case_owner }
										set_variable = { name = zg361_b2_pip_independent_review_result_cycle value = var:zg361_result_cycle_serial }
										set_variable = { name = zg361_b2_pip_independent_review_result_case value = var:zg361_result_case_serial }
										set_variable = { name = zg361_b2_pip_independent_review_result_grade value = var:zg361_result_grade }
										set_variable = { name = zg361_b2_pip_independent_review_progress_delta value = var:zg361_b2_pip_midpoint_progress_delta }
										set_variable = { name = zg361_b2_pip_independent_review_progress_met value = var:zg361_b2_pip_midpoint_progress_met }
										set_variable = { name = zg361_b2_pip_independent_review_conclusion value = 2 }
										set_variable = { name = zg361_b2_pip_independent_review_status value = 2 } # completed, failure upheld
										set_variable = { name = zg361_b2_pip_outcome_code value = 2 }
										if = {
											limit = {
												var:zg361_b2_pip_midpoint_progress_met = 1
												var:zg361_result_grade >= 2
											}
											set_variable = { name = zg361_b2_pip_independent_review_conclusion value = 1 }
											set_variable = { name = zg361_b2_pip_independent_review_status value = 1 } # completed, graduation approved
											set_variable = { name = zg361_b2_pip_outcome_code value = 1 }
										}
										set_variable = { name = zg361_b2_pip_independent_review_red_code value = 0 }
										set_variable = { name = zg361_b2_pip_independent_review_receipt value = var:zg361_b2_pip_case }
										set_variable = { name = zg361_b2_pip_independent_review_year value = current_year }
									}
								}
								# D+1 remains the terminal commit boundary. It reads the
								# already-signed conclusion and cannot manufacture a reviewer.
								var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_terminal_settlement_owner }
								save_scope_as = zg361_b2_terminal_settlement_subject
								save_scope_value_as = { name = zg361_b2_terminal_settlement_cycle value = var:zg361_b2_pip_cycle }
								save_scope_value_as = { name = zg361_b2_terminal_settlement_case value = var:zg361_b2_pip_case }
								save_scope_value_as = { name = zg361_b2_terminal_settlement_state value = var:zg361_b2_pip_state }
								trigger_event = { id = zg361b2.101 days = 1 }
							}
						}
					}
				}
			}
		}
	}
	else = { debug_log = "ZG361B2: duplicate or stale PIP settlement ignored" }
}

# The only graduation/failure writer.  PP may project this receipt but never
# calls it and never releases capacity or signs for the assessed official.
# B2 owns the PIP lifecycle.  A future Workforce #277 consumer may copy this
# one-slot source only after a real D+365 settlement.  The five-tuple is the
# immutable PIP object; the four truth fields are derived from that object and
# the settlement receipt rather than caller-supplied values.
zg361_b2_publish_workforce_pip_settlement_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_pip_owner
			has_variable = zg361_b2_pip_subject
			has_variable = zg361_b2_pip_cycle
			has_variable = zg361_b2_pip_case
			has_variable = zg361_b2_pip_state
			has_variable = zg361_b2_pip_policy_route
			has_variable = zg361_b2_pip_task_kind
			has_variable = zg361_b2_pip_settlement_receipt
			has_variable = zg361_b2_pip_outcome_code
			has_variable = zg361_b2_pip_outcome_result_cycle
			has_variable = zg361_b2_pip_outcome_result_case
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_case > 0
			var:zg361_b2_pip_cycle > 0
			OR = {
				var:zg361_b2_pip_policy_route = 1
				var:zg361_b2_pip_policy_route = 2
			}
			var:zg361_b2_pip_task_kind > 0
			var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
			OR = {
				var:zg361_b2_pip_outcome_code = 1
				var:zg361_b2_pip_outcome_code = 2
			}
			has_variable = zg361_b2_pip_outcome_result_grade
			var:zg361_b2_pip_outcome_result_cycle > 0
			var:zg361_b2_pip_outcome_result_case > 0
			OR = {
				AND = {
					var:zg361_b2_pip_state = 3
					var:zg361_b2_pip_outcome_code = 1
					var:zg361_b2_pip_outcome_result_grade >= 2
					var:zg361_b2_pip_outcome_result_grade <= 3
				}
				AND = {
					var:zg361_b2_pip_state = 4
					var:zg361_b2_pip_outcome_code = 2
					var:zg361_b2_pip_outcome_result_grade = 1
				}
			}
			trigger_if = {
				limit = { has_variable = zg361_b2_workforce_pip_pending }
				OR = {
					var:zg361_b2_workforce_pip_pending = 0
					AND = {
						has_variable = zg361_b2_workforce_pip_consumed
						var:zg361_b2_workforce_pip_consumed = 1
					}
				}
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = zg361_b2_workforce_pip_pending value = 1 }
		set_variable = { name = zg361_b2_workforce_pip_consumed value = 0 }
		set_variable = { name = zg361_b2_workforce_pip_owner value = var:zg361_b2_pip_owner }
		set_variable = { name = zg361_b2_workforce_pip_subject value = this }
		set_variable = { name = zg361_b2_workforce_pip_cycle value = var:zg361_b2_pip_cycle }
		set_variable = { name = zg361_b2_workforce_pip_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_workforce_pip_state value = var:zg361_b2_pip_state }
		set_variable = { name = zg361_b2_workforce_pip_case_id value = { value = var:zg361_b2_pip_case multiply = 1000 add = 15 } }
		set_variable = {
			name = zg361_b2_workforce_pip_case_hash
			value = {
				value = var:zg361_b2_pip_case
				multiply = 100000
				add = { value = var:zg361_b2_pip_cycle multiply = 1000 }
				add = { value = var:zg361_b2_pip_policy_route multiply = 100 }
				add = { value = var:zg361_b2_pip_task_kind multiply = 10 }
				add = var:zg361_b2_pip_state
			}
		}
		set_variable = { name = zg361_b2_workforce_pip_closure_receipt_id value = { value = var:zg361_b2_pip_settlement_receipt multiply = 1000 add = 17 } }
		set_variable = {
			name = zg361_b2_workforce_pip_closure_receipt_hash
			value = {
				# Repeat the immutable case formula directly.  Reading the case hash
				# written just above would be another unsupported same-chain read.
				value = var:zg361_b2_pip_case
				multiply = 100000
				add = { value = var:zg361_b2_pip_cycle multiply = 1000 }
				add = { value = var:zg361_b2_pip_policy_route multiply = 100 }
				add = { value = var:zg361_b2_pip_task_kind multiply = 10 }
				add = var:zg361_b2_pip_state
				add = { value = var:zg361_b2_pip_outcome_result_case multiply = 100000 }
				add = { value = var:zg361_b2_pip_outcome_result_cycle multiply = 1000 }
				add = { value = var:zg361_b2_pip_outcome_code multiply = 100 }
				add = { value = var:zg361_b2_pip_state multiply = 10 }
				add = 17
			}
		}
		debug_log = "ZG361B2: real PIP settlement published for Workforce #277"
	}
	else = { debug_log = "ZG361B2: unconsumed Workforce #277 PIP settlement conserved" }
	# CK3 does not provide a reliable read-after-write boundary inside one effect
	# chain.  Freeze only the long-lived PIP identity (which predates this
	# settlement), then defer every source read until the B2 writes have committed.
	if = {
		limit = {
			has_variable = zg361_b2_pip_owner
			has_variable = zg361_b2_pip_subject
			has_variable = zg361_b2_pip_cycle
			has_variable = zg361_b2_pip_case
			var:zg361_b2_pip_subject = this
		}
		var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_probation_handoff_owner }
		save_scope_as = zg361_b2_probation_handoff_subject
		save_scope_value_as = { name = zg361_b2_probation_handoff_cycle value = var:zg361_b2_pip_cycle }
		save_scope_value_as = { name = zg361_b2_probation_handoff_case value = var:zg361_b2_pip_case }
		trigger_event = { id = zg361b2.103 days = 1 }
	}
}

# Cross-package handoff for the probation outcome fact.  The external ROOT is
# irrelevant: current scope is proven to be the real PIP subject and OWNER is
# taken from B2's frozen PIP object.  A missing probation slot is an ordinary
# no-op, which keeps non-Workforce B2 cases and the still-unwired result/bps
# producer fail-closed without emitting a false collision.
zg361_b2_replay_workforce_probation_fact_handoff_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_pip_owner
			has_variable = zg361_b2_pip_subject
			has_variable = zg361_b2_pip_cycle
			has_variable = zg361_b2_pip_case
			has_variable = zg361_b2_pip_state
			has_variable = zg361_b2_pip_policy_route
			has_variable = zg361_b2_pip_task_kind
			has_variable = zg361_b2_pip_settlement_receipt
			has_variable = zg361_b2_pip_outcome_code
			has_variable = zg361_b2_pip_outcome_result_cycle
			has_variable = zg361_b2_pip_outcome_result_case
			has_variable = zg361_b2_pip_outcome_result_grade
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
			OR = {
				AND = {
					var:zg361_b2_pip_state = 3
					var:zg361_b2_pip_outcome_code = 1
					var:zg361_b2_pip_outcome_result_grade >= 2
					var:zg361_b2_pip_outcome_result_grade <= 3
				}
				AND = {
					var:zg361_b2_pip_state = 4
					var:zg361_b2_pip_outcome_code = 2
					var:zg361_b2_pip_outcome_result_grade = 1
				}
			}
			has_variable = zg361_b2_workforce_pip_pending
			has_variable = zg361_b2_workforce_pip_consumed
			has_variable = zg361_b2_workforce_pip_owner
			has_variable = zg361_b2_workforce_pip_subject
			has_variable = zg361_b2_workforce_pip_cycle
			has_variable = zg361_b2_workforce_pip_case
			has_variable = zg361_b2_workforce_pip_state
			has_variable = zg361_b2_workforce_pip_case_id
			has_variable = zg361_b2_workforce_pip_case_hash
			has_variable = zg361_b2_workforce_pip_closure_receipt_id
			has_variable = zg361_b2_workforce_pip_closure_receipt_hash
			var:zg361_b2_workforce_pip_pending = 1
			var:zg361_b2_workforce_pip_consumed = 0
			var:zg361_b2_workforce_pip_owner = var:zg361_b2_pip_owner
			var:zg361_b2_workforce_pip_subject = this
			var:zg361_b2_workforce_pip_cycle = var:zg361_b2_pip_cycle
			var:zg361_b2_workforce_pip_case = var:zg361_b2_pip_case
			var:zg361_b2_workforce_pip_state = var:zg361_b2_pip_state
			var:zg361_b2_workforce_pip_case_id > 0
			var:zg361_b2_workforce_pip_case_hash > 0
			var:zg361_b2_workforce_pip_closure_receipt_id > 0
			var:zg361_b2_workforce_pip_closure_receipt_hash > 0
			has_variable = zg361_workforce_probation_fact_state
			has_variable = zg361_workforce_probation_fact_owner
			has_variable = zg361_workforce_probation_fact_subject
			var:zg361_workforce_probation_fact_owner = var:zg361_b2_pip_owner
			var:zg361_workforce_probation_fact_subject = this
			OR = {
				AND = {
					var:zg361_workforce_probation_fact_state = 2
					var:zg361_workforce_probation_fact_awaiting_pip = 1
					var:zg361_workforce_probation_fact_source_result_cycle = var:zg361_b2_pip_cycle
				}
				AND = {
					var:zg361_workforce_probation_fact_state >= 3
					var:zg361_workforce_probation_fact_source_kind = 2
					var:zg361_workforce_probation_fact_source_pip_owner = var:zg361_b2_pip_owner
					var:zg361_workforce_probation_fact_source_pip_subject = this
					var:zg361_workforce_probation_fact_source_pip_cycle = var:zg361_b2_pip_cycle
					var:zg361_workforce_probation_fact_source_pip_case = var:zg361_b2_pip_case
					var:zg361_workforce_probation_fact_source_pip_state = var:zg361_b2_pip_state
					var:zg361_workforce_probation_fact_source_pip_policy_route = var:zg361_b2_pip_policy_route
					var:zg361_workforce_probation_fact_source_pip_task_kind = var:zg361_b2_pip_task_kind
					var:zg361_workforce_probation_fact_source_pip_settlement_receipt = var:zg361_b2_pip_settlement_receipt
					var:zg361_workforce_probation_fact_source_pip_outcome_code = var:zg361_b2_pip_outcome_code
					var:zg361_workforce_probation_fact_source_pip_result_cycle = var:zg361_b2_pip_outcome_result_cycle
					var:zg361_workforce_probation_fact_source_pip_result_case = var:zg361_b2_pip_outcome_result_case
					var:zg361_workforce_probation_fact_source_pip_result_grade = var:zg361_b2_pip_outcome_result_grade
					var:zg361_workforce_probation_fact_source_pip_case_receipt_id = var:zg361_b2_workforce_pip_case_id
					var:zg361_workforce_probation_fact_source_pip_case_receipt_hash = var:zg361_b2_workforce_pip_case_hash
					var:zg361_workforce_probation_fact_source_pip_closure_receipt_id = var:zg361_b2_workforce_pip_closure_receipt_id
					var:zg361_workforce_probation_fact_source_pip_closure_receipt_hash = var:zg361_b2_workforce_pip_closure_receipt_hash
				}
			}
		}
		zg361_workforce_probation_fact_publish_from_pip_settlement_effect = {
			OWNER = var:zg361_b2_pip_owner
		}
		# Do not read adapter_status in this same effect chain.  The adapter writes
		# its own typed ACK/RED, while this B2 source remains independently
		# conserved until its real Workforce consumer acknowledges it.
		debug_log = "ZG361B2: real probation fact handoff offered"
	}
}

zg361_b2_settle_pip_outcome_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_state = 2
			var:zg361_b2_m015_object_owner = var:zg361_b2_pip_owner
			var:zg361_b2_m015_object_cycle = var:zg361_b2_pip_cycle
			var:zg361_b2_m015_object_receipt_case = var:zg361_b2_pip_case
			trigger_if = {
				limit = {
					has_variable = zg361_b2_pip_independent_review_reviewer
					has_variable = zg361_b2_pip_independent_review_owner
					has_variable = zg361_b2_pip_independent_review_subject
					has_variable = zg361_b2_pip_independent_review_cycle
					has_variable = zg361_b2_pip_independent_review_case
					has_variable = zg361_b2_pip_independent_review_result_owner
					has_variable = zg361_b2_pip_independent_review_result_cycle
					has_variable = zg361_b2_pip_independent_review_result_case
					has_variable = zg361_b2_pip_independent_review_result_grade
					has_variable = zg361_b2_pip_independent_review_conclusion
					has_variable = zg361_b2_pip_independent_review_status
					has_variable = zg361_b2_pip_independent_review_red_code
					has_variable = zg361_b2_pip_independent_review_receipt
					has_variable = zg361_b2_pip_outcome_code
				}
				var:zg361_b2_pip_independent_review_reviewer = var:zg361_b2_pip_independent_reviewer
				var:zg361_b2_pip_independent_review_owner = var:zg361_b2_pip_owner
				var:zg361_b2_pip_independent_review_subject = this
				var:zg361_b2_pip_independent_review_cycle = var:zg361_b2_pip_cycle
				var:zg361_b2_pip_independent_review_case = var:zg361_b2_pip_case
				var:zg361_b2_pip_independent_review_result_owner = var:zg361_b2_pip_owner
				var:zg361_b2_pip_independent_review_result_cycle > var:zg361_b2_pip_cycle
				var:zg361_b2_pip_independent_review_result_case > 0
				var:zg361_b2_pip_independent_review_result_grade >= 1
				var:zg361_b2_pip_independent_review_result_grade <= 3
				var:zg361_b2_pip_independent_review_red_code = 0
				var:zg361_b2_pip_independent_review_receipt = var:zg361_b2_pip_case
				OR = {
					AND = {
						var:zg361_b2_pip_outcome_code = 1
						var:zg361_b2_pip_independent_review_conclusion = 1
						var:zg361_b2_pip_independent_review_status = 1
					}
					AND = {
						var:zg361_b2_pip_outcome_code = 2
						var:zg361_b2_pip_independent_review_conclusion = 2
						var:zg361_b2_pip_independent_review_status = 2
					}
				}
			}
			trigger_else = { always = no }
			OR = {
				NOT = { has_variable = zg361_b2_pip_settlement_receipt }
				NOT = { var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case }
			}
		}
		# This identity predates the terminal writes below.  Event .102 will read
		# the committed state/settlement/result tuple and publish the B2 source.
		var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_source_publish_owner }
		save_scope_as = zg361_b2_source_publish_subject
		save_scope_value_as = { name = zg361_b2_source_publish_cycle value = var:zg361_b2_pip_cycle }
		save_scope_value_as = { name = zg361_b2_source_publish_case value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_settlement_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_outcome_result_cycle value = var:zg361_b2_pip_independent_review_result_cycle }
		set_variable = { name = zg361_b2_pip_outcome_result_case value = var:zg361_b2_pip_independent_review_result_case }
		set_variable = { name = zg361_b2_pip_outcome_result_grade value = var:zg361_b2_pip_independent_review_result_grade }
		set_variable = { name = zg361_b2_pip_stability_days_observed value = 365 }
		remove_character_modifier = zg361_pip
		if = {
			limit = { var:zg361_b2_pip_outcome_code = 1 }
			set_variable = { name = zg361_b2_pip_state value = 3 } # graduated
		set_variable = { name = zg361_b2_m015_state value = 3 }
		set_variable = { name = zg361_b2_m016_state value = 3 }
		set_variable = { name = zg361_b2_pip_graduation_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_performance_evidence_delta value = 10 }
		if = {
			limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 1 }
			change_variable = { name = zg361_streak_bottom add = -1 }
		}
		zg361_b2_release_pip_support_effect = yes
		zg361_b2_m015_consume_business_object_effect = yes
		zg361_b2_m016_consume_business_object_effect = yes
		}
		else = {
		set_variable = { name = zg361_b2_pip_state value = 4 } # failed/timeout
		set_variable = { name = zg361_b2_m015_state value = 4 }
		set_variable = { name = zg361_b2_m016_state value = 4 }
		set_variable = { name = zg361_b2_pip_failure_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_performance_evidence_delta value = -10 }
		if = {
			limit = { var:zg361_b2_pip_support_absent = 1 }
			set_variable = { name = zg361_b2_pip_no_support_liability value = 1 }
			var:zg361_b2_pip_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
		zg361_b2_release_pip_support_effect = yes
		zg361_b2_m015_consume_business_object_effect = yes
		zg361_b2_m016_consume_business_object_effect = yes
		zg361_b2_m017_open_disposition_effect = yes
		}
		trigger_event = { id = zg361b2.102 days = 1 }
		zg361_b2_publish_pip_performance_evidence_effect = yes
	}
}

zg361_b2_m017_open_disposition_effect = {
	zg361_b2_m017_open_business_object_effect = yes
	if = {
		limit = {
			var:zg361_b2_m017_object_active = 1
			var:zg361_b2_pip_state = 4
			var:zg361_b2_m017_state = 0
		}
		set_variable = { name = zg361_b2_m017_state value = 1 }
		set_variable = { name = zg361_b2_m017_receipt_serial value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_m017_frozen_bottom_streak value = var:zg361_streak_bottom }
		if = {
			limit = { var:zg361_b2_m017_route = 1 var:zg361_streak_bottom < 2 }
			set_variable = { name = zg361_b2_m017_first_low_restricted value = 1 }
		}
		else = { set_variable = { name = zg361_b2_m017_first_low_restricted value = 0 } }
		if = {
			limit = { var:zg361_b2_m017_route = 2 }
			set_variable = { name = zg361_b2_m017_expedited_evidence value = var:zg361_b2_pip_case }
			set_variable = { name = zg361_b2_m017_expedited_risk value = 1 }
		}
		zg361_b2_m074_open_redundancy_offer_effect = yes
		if = {
			limit = { is_ai = yes }
			if = {
				limit = {
					age >= 60
					var:zg361_b2_m074_redundancy_eligible = 1
				}
				zg361_b2_m074_accept_redundancy_effect = yes
			}
			else_if = {
				limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 3 }
				zg361_b2_m074_reject_redundancy_effect = yes
				zg361_ai_elimination_effect = yes
			}
			else = {
				zg361_b2_m074_reject_redundancy_effect = yes
				zg361_eliminate_extend_effect = yes
			}
			set_variable = { name = zg361_b2_m017_state value = 3 }
			set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
			zg361_b2_m017_consume_business_object_effect = yes
		}
		else = {
			var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_disposition_owner }
			save_scope_as = zg361_b2_disposition_subject
			save_scope_value_as = { name = zg361_b2_disposition_cycle value = var:zg361_b2_pip_cycle }
			save_scope_value_as = { name = zg361_b2_disposition_case value = var:zg361_b2_pip_case }
			save_scope_value_as = { name = zg361_b2_disposition_state value = var:zg361_b2_m017_state }
			trigger_event = { id = zg361b2.110 days = 1 }
		}
	}
}

# ---------------------------------------------------------------------------
# #014/#070/#077/#358 appeal opening and target-bound observation.
# ---------------------------------------------------------------------------

zg361_b2_on_appeal_filed_effect = {
	zg361_b2_m014_open_business_object_effect = yes
	if = {
		limit = {
			var:zg361_b2_m014_object_active = 1
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_notice_state = 3
			var:zg361_result_case_state = 3
			var:zg361_result_appeal_open = 1
			var:zg361_b2_m014_state = 0
		}
		set_variable = { name = zg361_b2_appeal_state value = 1 }
		set_variable = { name = zg361_b2_appeal_reason value = 1 }
		if = {
			limit = { has_variable = zg361_result_objection_recorded }
			set_variable = { name = zg361_b2_appeal_reason value = 2 }
		}
		else_if = {
			limit = { var:zg361_b2_m072_headstart_days > 0 }
			set_variable = { name = zg361_b2_appeal_reason value = 3 }
		}
		else_if = {
			limit = { var:zg361_result_grade_reason = 5 }
			set_variable = { name = zg361_b2_appeal_reason value = 4 }
		}
		set_variable = { name = zg361_b2_appeal_evidence_revision value = var:zg361_b2_case_feedback_revision }
		set_variable = { name = zg361_b2_m014_headstart_days value = var:zg361_b2_m072_headstart_days }
		set_variable = { name = zg361_b2_m014_state value = 1 }
		set_variable = { name = zg361_b2_m014_receipt_serial value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m014_review_mode value = var:zg361_b2_m014_route }
		if = {
			limit = { var:zg361_b2_m014_route = 2 }
			set_variable = { name = zg361_b2_m014_original_owner_conflict value = 1 }
			set_variable = { name = zg361_b2_m014_fast_review_risk value = 1 }
		}
		zg361_b2_m070_open_business_object_effect = yes
		zg361_b2_m077_open_business_object_effect = yes
		zg361_b2_m358_open_business_object_effect = yes
		zg361_b2_m070_open_observation_effect = yes
		zg361_b2_m077_assign_reviewer_effect = yes
		zg361_b2_m358_freeze_non_aggravation_effect = yes
		debug_log = "ZG361B2: target-bound appeal case opened"
	}
	else_if = {
		limit = { var:zg361_b2_m014_route = 3 }
		debug_log = "ZG361B2: enhanced appeal dossier deferred; core receipt appeal remains available"
	}
	else = { debug_log = "ZG361B2: duplicate or stale appeal filing ignored" }
}

zg361_b2_m070_open_observation_effect = {
	if = {
		limit = { var:zg361_b2_m070_object_active = 1 }
	set_variable = { name = zg361_b2_retaliation_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_retaliation_subject value = this }
	set_variable = { name = zg361_b2_retaliation_cycle value = var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_retaliation_case value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_retaliation_state value = 1 }
	set_variable = { name = zg361_b2_retaliation_new_fact value = 0 }
	set_variable = { name = zg361_b2_retaliation_suspended_n value = 0 }
	set_variable = { name = zg361_b2_m070_state value = 1 }
	set_variable = { name = zg361_b2_m070_receipt_serial value = var:zg361_b2_case_serial }
	if = {
		limit = { var:zg361_b2_m070_route = 2 }
		set_variable = { name = zg361_b2_m070_immediate_action_risk value = 1 }
		set_variable = { name = zg361_b2_m070_reason_reversal_weight value = 2 }
	}
	var:zg361_b2_retaliation_owner = { save_scope_as = zg361_b2_retaliation_deadline_owner }
	save_scope_as = zg361_b2_retaliation_deadline_subject
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_cycle value = var:zg361_b2_retaliation_cycle }
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_case value = var:zg361_b2_retaliation_case }
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_state value = var:zg361_b2_retaliation_state }
	trigger_event = { id = zg361b2.120 days = 365 }
	}
}

zg361_b2_m077_assign_reviewer_effect = {
	if = {
		limit = { var:zg361_b2_m077_object_active = 1 }
	set_variable = { name = zg361_b2_m077_state value = 1 }
	set_variable = { name = zg361_b2_m077_independent value = 0 }
	save_temporary_scope_as = zg361_b2_review_subject
	var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_review_owner }
	if = {
		limit = { var:zg361_b2_m077_route = 1 }
		var:zg361_b2_case_owner = {
		if = {
			limit = { exists = liege }
			liege = {
				ordered_vassal = {
					limit = {
						is_alive = yes
						is_landed = yes
						NOT = { this = scope:zg361_b2_review_owner }
						NOT = { this = scope:zg361_b2_review_subject }
						NOT = { is_close_family_of = scope:zg361_b2_review_owner }
						NOT = { is_close_family_of = scope:zg361_b2_review_subject }
					}
					order_by = stewardship
					position = 0
					save_scope_as = zg361_b2_independent_reviewer
				}
			}
		}
	}
	}
	if = {
		limit = { exists = scope:zg361_b2_independent_reviewer }
		set_variable = { name = zg361_b2_m077_reviewer value = scope:zg361_b2_independent_reviewer }
		set_variable = { name = zg361_b2_m077_independent value = 1 }
	}
	else = {
		set_variable = { name = zg361_b2_m077_reviewer value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m077_self_correction value = 1 }
		set_variable = { name = zg361_b2_m077_independence_disclosed value = 1 }
	}
	set_variable = { name = zg361_b2_m077_recusal_subject_used value = 0 }
	set_variable = { name = zg361_b2_m077_recusal_owner_used value = 0 }
	# The core appeal resolves in the same effect stack, so a later UI-only
	# recusal would be decorative.  Consume each side's token synchronously when
	# the selected reviewer has an observable friend/lover/rival conflict.
	if = {
		limit = {
			var:zg361_b2_m077_independent = 1
			var:zg361_b2_m077_reviewer = {
				OR = {
					has_relation_friend = scope:zg361_b2_review_subject
					has_relation_lover = scope:zg361_b2_review_subject
					has_relation_rival = scope:zg361_b2_review_subject
				}
			}
		}
		set_variable = { name = zg361_b2_m077_subject_conflict_reason value = 1 }
		zg361_b2_m077_subject_recusal_effect = yes
	}
	if = {
		limit = {
			var:zg361_b2_m077_independent = 1
			var:zg361_b2_m077_reviewer = {
				OR = {
					has_relation_friend = scope:zg361_b2_review_owner
					has_relation_lover = scope:zg361_b2_review_owner
					has_relation_rival = scope:zg361_b2_review_owner
				}
			}
		}
		set_variable = { name = zg361_b2_m077_owner_conflict_reason value = 2 }
		zg361_b2_m077_owner_recusal_effect = yes
	}
	set_variable = { name = zg361_b2_m077_quality_bonus value = 0 }
	if = {
		limit = { var:zg361_b2_m077_independent = 1 }
		set_variable = { name = zg361_b2_m077_quality_bonus value = 10 }
		set_variable = { name = zg361_b2_m077_review_time_cost value = 30 }
	}
	set_variable = { name = zg361_b2_m077_receipt_serial value = var:zg361_b2_case_serial }
	}
}

# Each side owns one reason-bound recusal token.  The replacement search is
# deterministic and excludes the frozen parties and the reviewer just removed.
zg361_b2_m077_subject_recusal_effect = {
	if = {
		limit = {
			var:zg361_b2_m077_object_active = 1
			var:zg361_b2_m077_route = 1
			var:zg361_b2_m077_recusal_subject_used = 0
			has_variable = zg361_b2_m077_subject_conflict_reason
			var:zg361_b2_m077_subject_conflict_reason >= 1
			has_variable = zg361_b2_m077_reviewer
		}
		set_variable = { name = zg361_b2_m077_recused_reviewer value = var:zg361_b2_m077_reviewer }
		set_variable = { name = zg361_b2_m077_recusal_subject_used value = 1 }
		set_variable = { name = zg361_b2_m077_recusal_reason_frozen value = var:zg361_b2_m077_subject_conflict_reason }
		zg361_b2_m077_pick_replacement_effect = yes
	}
}

zg361_b2_m077_owner_recusal_effect = {
	if = {
		limit = {
			var:zg361_b2_m077_object_active = 1
			var:zg361_b2_m077_route = 1
			var:zg361_b2_m077_recusal_owner_used = 0
			has_variable = zg361_b2_m077_owner_conflict_reason
			var:zg361_b2_m077_owner_conflict_reason >= 1
			has_variable = zg361_b2_m077_reviewer
		}
		set_variable = { name = zg361_b2_m077_recused_reviewer value = var:zg361_b2_m077_reviewer }
		set_variable = { name = zg361_b2_m077_recusal_owner_used value = 1 }
		set_variable = { name = zg361_b2_m077_recusal_reason_frozen value = var:zg361_b2_m077_owner_conflict_reason }
		zg361_b2_m077_pick_replacement_effect = yes
	}
}

zg361_b2_m077_pick_replacement_effect = {
	save_temporary_scope_as = zg361_b2_recusal_subject
	var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_recusal_owner }
	var:zg361_b2_case_owner = {
		if = {
			limit = { exists = liege }
			liege = {
				ordered_vassal = {
					limit = {
						is_alive = yes
						is_landed = yes
						NOT = { this = scope:zg361_b2_recusal_owner }
						NOT = { this = scope:zg361_b2_recusal_subject }
						NOT = { this = scope:zg361_b2_recusal_subject.var:zg361_b2_m077_recused_reviewer }
						NOT = { is_close_family_of = scope:zg361_b2_recusal_owner }
						NOT = { is_close_family_of = scope:zg361_b2_recusal_subject }
					}
					order_by = stewardship
					position = 0
					save_scope_as = zg361_b2_replacement_reviewer
				}
			}
		}
	}
	if = {
		limit = { exists = scope:zg361_b2_replacement_reviewer }
		set_variable = { name = zg361_b2_m077_reviewer value = scope:zg361_b2_replacement_reviewer }
	}
	else = {
		set_variable = { name = zg361_b2_m077_replacement_unavailable value = 1 }
		set_variable = { name = zg361_b2_m077_reviewer value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m077_independent value = 0 }
		set_variable = { name = zg361_b2_m077_self_correction value = 1 }
		set_variable = { name = zg361_b2_m077_independence_disclosed value = 1 }
	}
}

# #358/#359 export receipts are consequences of their real business consumers.
# They are not generic policy-choice receipts: C never creates either export,
# an expired/open appeal cannot mint #358, and an unreturned quota cannot mint
# #359.  The downstream Workforce adapter only reads these immutable sources.
zg361_b2_m358_publish_workforce_receipt_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_case_owner
			has_variable = zg361_b2_case_subject
			has_variable = zg361_b2_case_cycle
			has_variable = zg361_b2_case_serial
			has_variable = zg361_b2_m358_route
			has_variable = zg361_b2_m358_state
			has_variable = zg361_b2_m358_receipt_serial
			has_variable = zg361_b2_m358_object_owner
			has_variable = zg361_b2_m358_object_subject
			has_variable = zg361_b2_m358_object_cycle
			has_variable = zg361_b2_m358_object_receipt_case
			has_variable = zg361_b2_m358_object_consumed
			has_variable = zg361_b2_m358_consumer_receipt_case
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
			has_variable = zg361_result_appeal_outcome
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_case_serial > 0
			var:zg361_b2_m358_route != 3
			var:zg361_b2_m358_state = 3
			var:zg361_b2_m358_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_m358_object_owner = var:zg361_b2_case_owner
			var:zg361_b2_m358_object_subject = this
			var:zg361_b2_m358_object_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m358_object_receipt_case = var:zg361_b2_case_serial
			var:zg361_b2_m358_object_consumed = 1
			var:zg361_b2_m358_consumer_receipt_case = var:zg361_b2_case_serial
			OR = {
				AND = {
					var:zg361_result_case_state = 4
					var:zg361_result_appeal_outcome = 2
				}
				AND = {
					has_variable = zg361_result_refund_posted_serial
					var:zg361_result_case_state = 5
					var:zg361_result_appeal_outcome = 1
					var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
				}
			}
		}
		set_variable = { name = zg361_b2_m358_external_receipt_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m358_external_receipt_subject value = this }
		set_variable = { name = zg361_b2_m358_external_receipt_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m358_external_receipt_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m358_external_receipt_state value = 3 }
		set_variable = { name = zg361_b2_m358_external_receipt_route value = var:zg361_b2_m358_route }
		set_variable = { name = zg361_b2_m358_external_appeal_outcome value = var:zg361_result_appeal_outcome }
		set_variable = { name = zg361_b2_m358_external_receipt_id value = { value = var:zg361_b2_case_serial multiply = 1000 add = 358 } }
		set_variable = { name = zg361_b2_m358_external_receipt_hash value = { value = var:zg361_b2_case_serial multiply = 10000 add = { value = var:zg361_b2_m358_route multiply = 1000 } add = 358 } }
	}
}

zg361_b2_m359_publish_workforce_receipt_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_case_owner
			has_variable = zg361_b2_case_subject
			has_variable = zg361_b2_case_cycle
			has_variable = zg361_b2_case_serial
			has_variable = zg361_b2_m359_route
			has_variable = zg361_b2_m359_state
			has_variable = zg361_b2_m359_return_route
			has_variable = zg361_b2_m359_receipt_serial
			has_variable = zg361_b2_m359_object_owner
			has_variable = zg361_b2_m359_object_subject
			has_variable = zg361_b2_m359_object_cycle
			has_variable = zg361_b2_m359_object_receipt_case
			has_variable = zg361_b2_m359_object_consumed
			has_variable = zg361_b2_m359_consumer_receipt_case
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
			has_variable = zg361_result_appeal_outcome
			has_variable = zg361_result_refund_posted_serial
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_case_serial > 0
			var:zg361_result_case_state = 5
			var:zg361_result_appeal_outcome = 1
			var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
			var:zg361_b2_m359_route != 3
			var:zg361_b2_m359_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_m359_object_owner = var:zg361_b2_case_owner
			var:zg361_b2_m359_object_subject = this
			var:zg361_b2_m359_object_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m359_object_receipt_case = var:zg361_b2_case_serial
			var:zg361_b2_m359_object_consumed = 1
			var:zg361_b2_m359_consumer_receipt_case = var:zg361_b2_case_serial
			OR = {
				AND = {
					has_variable = zg361_b2_m359_reserved_consumed
					has_variable = zg361_b2_m359_pp_nomination_owner
					has_variable = zg361_b2_m359_pp_nomination_cycle
					has_variable = zg361_b2_m359_pp_nomination_case
					has_variable = zg361_b2_m359_pp_nomination_amount
					has_variable = zg361_b2_m359_pp_nomination_status_before
					has_variable = zg361_b2_m359_pp_nomination_status_after
					var:zg361_b2_m359_state = 2
					var:zg361_b2_m359_return_route = 1
					var:zg361_b2_m359_reserved_consumed = 1
					var:zg361_b2_m359_pp_nomination_owner = var:zg361_b2_case_owner
					var:zg361_b2_m359_pp_nomination_cycle = var:zg361_b2_case_cycle
					var:zg361_b2_m359_pp_nomination_case > 0
					var:zg361_b2_m359_pp_nomination_amount = 1
					OR = {
						var:zg361_b2_m359_pp_nomination_status_before = 1
						var:zg361_b2_m359_pp_nomination_status_before = 2
					}
					var:zg361_b2_m359_pp_nomination_status_after = 3
				}
				AND = {
					var:zg361_b2_m359_state = 3
					var:zg361_b2_m359_return_route = 2
					has_variable = zg361_b2_m359_redelivery_receipt
					var:zg361_b2_m359_redelivery_receipt > 0
				}
				AND = {
					has_variable = zg361_b2_m359_debt_added
					var:zg361_b2_m359_state = 2
					var:zg361_b2_m359_return_route = 3
					var:zg361_b2_m359_debt_added = 1
				}
			}
		}
		set_variable = { name = zg361_b2_m359_external_receipt_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m359_external_receipt_subject value = this }
		set_variable = { name = zg361_b2_m359_external_receipt_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m359_external_receipt_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m359_external_receipt_state value = var:zg361_b2_m359_state }
		set_variable = { name = zg361_b2_m359_external_receipt_route value = var:zg361_b2_m359_route }
		set_variable = { name = zg361_b2_m359_external_return_route value = var:zg361_b2_m359_return_route }
		set_variable = { name = zg361_b2_m359_external_receipt_id value = { value = var:zg361_b2_case_serial multiply = 1000 add = 359 } }
		set_variable = { name = zg361_b2_m359_external_receipt_hash value = { value = var:zg361_b2_case_serial multiply = 10000 add = { value = var:zg361_b2_m359_return_route multiply = 1000 } add = 359 } }
	}
}

# Public source adapter for the central Workforce wait.  It maps three
# independently completed source objects into the current AL envelope; no
# caller can supply receipt ids/hashes, and no route-C policy debt qualifies.
zg361_b2_submit_completed_al_receipts_effect = {
	set_variable = { name = zg361_b2_workforce_adapter_status value = 5 }
	remove_variable = zg361_b2_workforce_adapter_blocked_reason
	if = {
		limit = {
			$TICKET_SUBJECT$ = this
			has_variable = zg361_b2_case_owner
			has_variable = zg361_b2_case_subject
			has_variable = zg361_b2_case_cycle
			has_variable = zg361_b2_case_serial
			var:zg361_b2_case_owner = $TICKET_OWNER$
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_cycle = $TICKET_CYCLE$
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
			has_variable = zg361_result_appeal_outcome
			has_variable = zg361_result_refund_posted_serial
			var:zg361_result_case_owner = $TICKET_OWNER$
			var:zg361_result_cycle_serial = $TICKET_CYCLE$
			var:zg361_result_case_serial = var:zg361_b2_case_serial
			var:zg361_result_case_state = 5
			var:zg361_result_appeal_outcome = 1
			var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
			has_variable = zg361_b1_result_adapter_result_owner
			has_variable = zg361_b1_result_adapter_result_subject
			has_variable = zg361_b1_result_adapter_result_cycle
			has_variable = zg361_b1_result_adapter_result_case
			has_variable = zg361_b1_result_adapter_b1_owner
			has_variable = zg361_b1_result_adapter_b1_subject
			has_variable = zg361_b1_result_adapter_b1_cycle
			has_variable = zg361_b1_result_adapter_b1_case
			has_variable = zg361_b1_result_adapter_b1_state
			var:zg361_b1_result_adapter_result_owner = $TICKET_OWNER$
			var:zg361_b1_result_adapter_result_subject = this
			var:zg361_b1_result_adapter_result_cycle = $TICKET_CYCLE$
			var:zg361_b1_result_adapter_result_case = var:zg361_b2_case_serial
			var:zg361_b1_result_adapter_b1_owner = $TICKET_OWNER$
			var:zg361_b1_result_adapter_b1_subject = this
			var:zg361_b1_result_adapter_b1_cycle = $TICKET_CYCLE$
			var:zg361_b1_result_adapter_b1_state = 8
			has_variable = zg361_b1_m357_external_receipt_owner
			has_variable = zg361_b1_m357_external_receipt_subject
			has_variable = zg361_b1_m357_external_receipt_cycle
			has_variable = zg361_b1_m357_external_receipt_case
			has_variable = zg361_b1_m357_external_receipt_state
			has_variable = zg361_b1_m357_external_result_case
			has_variable = zg361_b1_m357_external_receipt_id
			has_variable = zg361_b1_m357_external_receipt_hash
			var:zg361_b1_m357_external_receipt_owner = $TICKET_OWNER$
			var:zg361_b1_m357_external_receipt_subject = this
			var:zg361_b1_m357_external_receipt_cycle = $TICKET_CYCLE$
			var:zg361_b1_m357_external_receipt_case = var:zg361_b1_result_adapter_b1_case
			var:zg361_b1_m357_external_receipt_state = 8
			var:zg361_b1_m357_external_result_case = var:zg361_b2_case_serial
			var:zg361_b1_m357_external_receipt_id > 0
			var:zg361_b1_m357_external_receipt_hash > 0
			has_variable = zg361_b2_m358_external_receipt_owner
			has_variable = zg361_b2_m358_external_receipt_subject
			has_variable = zg361_b2_m358_external_receipt_cycle
			has_variable = zg361_b2_m358_external_receipt_case
			has_variable = zg361_b2_m358_external_receipt_state
			has_variable = zg361_b2_m358_external_receipt_route
			has_variable = zg361_b2_m358_external_receipt_id
			has_variable = zg361_b2_m358_external_receipt_hash
			var:zg361_b2_m358_external_receipt_owner = $TICKET_OWNER$
			var:zg361_b2_m358_external_receipt_subject = this
			var:zg361_b2_m358_external_receipt_cycle = $TICKET_CYCLE$
			var:zg361_b2_m358_external_receipt_case = var:zg361_b2_case_serial
			var:zg361_b2_m358_external_receipt_state = 3
			var:zg361_b2_m358_external_receipt_route != 3
			var:zg361_b2_m358_external_receipt_id > 0
			var:zg361_b2_m358_external_receipt_hash > 0
			has_variable = zg361_b2_m359_external_receipt_owner
			has_variable = zg361_b2_m359_external_receipt_subject
			has_variable = zg361_b2_m359_external_receipt_cycle
			has_variable = zg361_b2_m359_external_receipt_case
			has_variable = zg361_b2_m359_external_receipt_state
			has_variable = zg361_b2_m359_external_receipt_route
			has_variable = zg361_b2_m359_external_return_route
			has_variable = zg361_b2_m359_external_receipt_id
			has_variable = zg361_b2_m359_external_receipt_hash
			var:zg361_b2_m359_external_receipt_owner = $TICKET_OWNER$
			var:zg361_b2_m359_external_receipt_subject = this
			var:zg361_b2_m359_external_receipt_cycle = $TICKET_CYCLE$
			var:zg361_b2_m359_external_receipt_case = var:zg361_b2_case_serial
			OR = {
				var:zg361_b2_m359_external_receipt_state = 2
				var:zg361_b2_m359_external_receipt_state = 3
			}
			var:zg361_b2_m359_external_receipt_route != 3
			var:zg361_b2_m359_external_receipt_id > 0
			var:zg361_b2_m359_external_receipt_hash > 0
			NOT = { var:zg361_b1_m357_external_receipt_id = var:zg361_b2_m358_external_receipt_id }
			NOT = { var:zg361_b1_m357_external_receipt_id = var:zg361_b2_m359_external_receipt_id }
			NOT = { var:zg361_b2_m358_external_receipt_id = var:zg361_b2_m359_external_receipt_id }
			NOT = { var:zg361_b1_m357_external_receipt_hash = var:zg361_b2_m358_external_receipt_hash }
			NOT = { var:zg361_b1_m357_external_receipt_hash = var:zg361_b2_m359_external_receipt_hash }
			NOT = { var:zg361_b2_m358_external_receipt_hash = var:zg361_b2_m359_external_receipt_hash }
		}
		zg361_we_submit_al_357_359_receipts_effect = {
			TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
			TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
			M357_OWNER = $TICKET_OWNER$ M357_SUBJECT = $TICKET_SUBJECT$
			M357_CYCLE = $TICKET_CYCLE$ M357_CASE = $TICKET_CASE$ M357_STATE = 2
			M357_RECEIPT_ID = var:zg361_b1_m357_external_receipt_id
			M357_RECEIPT_HASH = var:zg361_b1_m357_external_receipt_hash
			M358_OWNER = $TICKET_OWNER$ M358_SUBJECT = $TICKET_SUBJECT$
			M358_CYCLE = $TICKET_CYCLE$ M358_CASE = $TICKET_CASE$ M358_STATE = 3
			M358_RECEIPT_ID = var:zg361_b2_m358_external_receipt_id
			M358_RECEIPT_HASH = var:zg361_b2_m358_external_receipt_hash
			M359_OWNER = $TICKET_OWNER$ M359_SUBJECT = $TICKET_SUBJECT$
			M359_CYCLE = $TICKET_CYCLE$ M359_CASE = $TICKET_CASE$ M359_STATE = 3
			M359_RECEIPT_ID = var:zg361_b2_m359_external_receipt_id
			M359_RECEIPT_HASH = var:zg361_b2_m359_external_receipt_hash
		}
		if = {
			limit = {
				has_variable = zg361_we_adapter_status
				var:zg361_we_adapter_status = 1
			}
			set_variable = { name = zg361_b2_workforce_adapter_status value = 1 }
			set_variable = { name = zg361_b2_workforce_adapter_case value = $TICKET_CASE$ }
		}
		else_if = {
			limit = {
				has_variable = zg361_we_adapter_status
				var:zg361_we_adapter_status = 2
			}
			set_variable = { name = zg361_b2_workforce_adapter_status value = 2 }
		}
		else = {
			set_variable = { name = zg361_b2_workforce_adapter_status value = 4 }
			set_variable = { name = zg361_b2_workforce_adapter_blocked_reason value = 357359 }
		}
	}
}

zg361_b2_m358_freeze_non_aggravation_effect = {
	if = {
		limit = { var:zg361_b2_m358_object_active = 1 }
	set_variable = { name = zg361_b2_m358_state value = 1 }
	set_variable = { name = zg361_b2_m358_original_grade value = var:zg361_result_grade }
	set_variable = { name = zg361_b2_m358_original_treasury value = var:zg361_result_treasury_paid }
	set_variable = { name = zg361_b2_m358_original_gold value = var:zg361_result_gold_paid }
	set_variable = { name = zg361_b2_m358_original_merit value = var:zg361_result_merit_paid }
	set_variable = { name = zg361_b2_m358_original_salary value = var:zg361_result_salary_cut_active }
	set_variable = { name = zg361_b2_m358_aggravated value = 0 }
	set_variable = { name = zg361_b2_m358_receipt_serial value = var:zg361_b2_case_serial }
	if = {
		limit = { var:zg361_b2_m358_route = 2 }
		set_variable = { name = zg361_b2_m358_same_case_aggravation_permitted value = 1 }
		set_variable = { name = zg361_b2_m358_retaliation_risk value = 1 }
	}
	}
}

# ---------------------------------------------------------------------------
# Appeal outcomes, responsibility/fairness consumers, and public escalation.
# ---------------------------------------------------------------------------

zg361_b2_on_appeal_upheld_effect = {
	if = {
		limit = {
			var:zg361_b2_m014_state = 1
			var:zg361_b2_m014_receipt_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_m014_state value = 4 }
		set_variable = { name = zg361_b2_appeal_state value = 4 }
		set_variable = { name = zg361_b2_m014_outcome value = 2 }
		set_variable = { name = zg361_result_appeal_open value = 0 }
		set_variable = { name = zg361_result_case_state value = 4 }
		set_variable = { name = zg361_result_appeal_outcome value = 2 }
		set_variable = { name = zg361_b2_m077_state value = 4 }
		set_variable = { name = zg361_b2_m077_conclusion value = 2 }
		set_variable = { name = zg361_b2_m077_conclusion_evidence_revision value = var:zg361_b2_appeal_evidence_revision }
		set_variable = { name = zg361_b2_m077_conclusion_receipt value = var:zg361_b2_case_serial }
		if = {
			limit = { has_variable = zg361_b2_m077_reviewer }
			var:zg361_b2_m077_reviewer = {
				set_variable = { name = zg361_b2_reviewer_last_case value = root.var:zg361_b2_case_serial }
			}
		}
		zg361_b2_m078_open_business_object_effect = yes
		zg361_b2_m071_open_business_object_effect = yes
		zg361_b2_m078_update_fairness_effect = yes
		zg361_b2_m358_apply_disclosed_aggravation_effect = yes
		zg361_b2_m358_close_non_aggravation_effect = yes
		zg361_b2_m071_open_escalation_effect = yes
		zg361_b2_m014_consume_business_object_effect = yes
		zg361_b2_m077_consume_business_object_effect = yes
	}
}

zg361_b2_on_appeal_expired_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_m069_receipt_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_notice_state value = 4 }
		set_variable = { name = zg361_b2_m069_state value = 4 }
		set_variable = { name = zg361_b2_m069_appeal_clock_open value = 0 }
		if = {
			limit = { var:zg361_b2_m014_state = 1 }
			set_variable = { name = zg361_b2_m014_state value = 5 }
			set_variable = { name = zg361_b2_appeal_state value = 5 }
			zg361_b2_m014_consume_business_object_effect = yes
			zg361_b2_m077_consume_business_object_effect = yes
			zg361_b2_m358_consume_business_object_effect = yes
		}
		# Existing AI-manager elimination resumes only after the ninety-day
		# appeal window really closes; the settlement-day D+2 shortcut is gated.
		if = {
			limit = {
				is_ai = no
				has_variable = zg361_streak_bottom
				var:zg361_streak_bottom >= 2
				var:zg361_result_case_owner = liege
				var:zg361_result_case_owner = { is_ai = yes is_alive = yes }
			}
			trigger_event = { id = zg361.6 days = 1 }
		}
	}
}

zg361_b2_on_appeal_corrected_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_result_case_state = 5
			var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_notice_state value = 5 }
		set_variable = { name = zg361_b2_appeal_state value = 3 }
		set_variable = { name = zg361_b2_m014_state value = 3 }
		set_variable = { name = zg361_b2_m014_outcome value = 1 }
		set_variable = { name = zg361_b2_m077_state value = 3 }
		set_variable = { name = zg361_b2_m077_conclusion value = 1 }
		set_variable = { name = zg361_b2_m077_conclusion_evidence_revision value = var:zg361_b2_appeal_evidence_revision }
		set_variable = { name = zg361_b2_m077_conclusion_receipt value = var:zg361_b2_case_serial }
		if = {
			limit = { has_variable = zg361_b2_m077_reviewer }
			var:zg361_b2_m077_reviewer = {
				set_variable = { name = zg361_b2_reviewer_last_case value = root.var:zg361_b2_case_serial }
			}
		}
		zg361_b2_m076_open_business_object_effect = yes
		zg361_b2_m078_open_business_object_effect = yes
		zg361_b2_m359_open_business_object_effect = yes
		zg361_b2_m076_allocate_liability_effect = yes
		zg361_b2_m078_update_fairness_effect = yes
		zg361_b2_m358_close_non_aggravation_effect = yes
		zg361_b2_m359_open_quota_return_effect = yes
		zg361_b2_m014_consume_business_object_effect = yes
		zg361_b2_m077_consume_business_object_effect = yes
		debug_log = "ZG361B2: appeal correction consumed actual refund receipt"
	}
}

zg361_b2_m076_allocate_liability_effect = {
	if = {
		limit = { var:zg361_b2_m076_object_active = 1 }
	save_temporary_scope_as = zg361_b2_liability_subject
	set_variable = { name = zg361_b2_m076_state value = 3 }
	set_variable = { name = zg361_b2_m076_direct_share value = 50 }
	set_variable = { name = zg361_b2_m076_superior_share value = 25 }
	set_variable = { name = zg361_b2_m076_system_share value = 25 }
	if = {
		limit = { var:zg361_b2_m076_route = 2 }
		set_variable = { name = zg361_b2_m076_direct_share value = 100 }
		set_variable = { name = zg361_b2_m076_superior_share value = 0 }
		set_variable = { name = zg361_b2_m076_system_share value = 0 }
		set_variable = { name = zg361_b2_m076_scapegoat_risk value = 1 }
		set_variable = { name = zg361_b2_m076_unresolved_system_defect value = 1 }
	}
	set_variable = { name = zg361_b2_m076_share_total value = 100 }
	set_variable = { name = zg361_b2_m076_receipt_serial value = var:zg361_b2_case_serial }
	var:zg361_b2_case_owner = {
		change_variable = { name = zg361_b2_management_debt add = 1 }
		set_variable = { name = zg361_b2_management_debt_source_case value = scope:zg361_b2_liability_subject.var:zg361_b2_case_serial }
		if = {
			limit = { scope:zg361_b2_liability_subject.var:zg361_b2_m076_route = 1 exists = liege }
			liege = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
	}
	zg361_b2_m076_consume_business_object_effect = yes
	}
}

zg361_b2_m078_update_fairness_effect = {
	zg361_b2_m078_apply_resolved_sample_effect = yes
}

zg361_b2_m358_apply_disclosed_aggravation_effect = {
	if = {
		limit = {
			var:zg361_b2_m358_object_active = 1
			var:zg361_b2_m358_state = 1
			var:zg361_b2_m358_route = 2
			var:zg361_b2_m358_receipt_serial = var:zg361_b2_case_serial
			OR = {
				NOT = { has_variable = zg361_b2_m358_aggravation_receipt }
				NOT = { var:zg361_b2_m358_aggravation_receipt = var:zg361_b2_case_serial }
			}
		}
		set_variable = { name = zg361_b2_m358_aggravation_gold_before value = gold }
		remove_short_term_gold = 10
		set_variable = {
			name = zg361_b2_m358_extra_gold_paid
			value = { value = var:zg361_b2_m358_aggravation_gold_before subtract = gold }
		}
		change_variable = { name = zg361_result_gold_paid add = var:zg361_b2_m358_extra_gold_paid }
		set_variable = { name = zg361_b2_m358_aggravation_receipt value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m358_aggravation_disclosed value = 1 }
		var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		remove_variable = zg361_b2_m358_aggravation_gold_before
	}
}

zg361_b2_m358_close_non_aggravation_effect = {
	if = {
		limit = {
			var:zg361_b2_m358_object_active = 1
			var:zg361_b2_m358_state = 1
			var:zg361_b2_m358_receipt_serial = var:zg361_b2_case_serial
			OR = {
				var:zg361_b2_m358_route = 2
				AND = {
			var:zg361_result_grade >= var:zg361_b2_m358_original_grade
			var:zg361_result_treasury_paid <= var:zg361_b2_m358_original_treasury
			var:zg361_result_gold_paid <= var:zg361_b2_m358_original_gold
			var:zg361_result_merit_paid <= var:zg361_b2_m358_original_merit
				}
			}
		}
		set_variable = { name = zg361_b2_m358_state value = 3 }
		set_variable = { name = zg361_b2_m358_aggravated value = 0 }
		if = {
			limit = {
				var:zg361_b2_m358_route = 2
				OR = {
					var:zg361_result_grade < var:zg361_b2_m358_original_grade
					var:zg361_result_treasury_paid > var:zg361_b2_m358_original_treasury
					var:zg361_result_gold_paid > var:zg361_b2_m358_original_gold
					var:zg361_result_merit_paid > var:zg361_b2_m358_original_merit
				}
			}
			set_variable = { name = zg361_b2_m358_aggravated value = 1 }
			set_variable = { name = zg361_b2_m358_aggravation_disclosed value = 1 }
			set_variable = { name = zg361_b2_m358_retaliation_risk value = 1 }
		}
		zg361_b2_m358_consume_business_object_effect = yes
	}
	else_if = {
		limit = { var:zg361_b2_m358_object_active = 1 }
		set_variable = { name = zg361_b2_m358_state value = 4 }
		set_variable = { name = zg361_b2_m358_aggravated value = 1 }
		debug_log = "ZG361B2: non-aggravation invariant failed"
	}
}

zg361_b2_m071_open_escalation_effect = {
	if = {
		limit = { var:zg361_b2_m071_object_active = 1 }
	set_variable = { name = zg361_b2_m071_state value = 1 }
	set_variable = { name = zg361_b2_m071_receipt_serial value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m071_private_route_exhausted value = 1 }
	set_variable = { name = zg361_b2_m071_formal_appeal_exhausted value = 1 }
	if = {
		limit = { is_ai = no }
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_escalation_owner }
		save_scope_as = zg361_b2_escalation_subject
		save_scope_value_as = { name = zg361_b2_escalation_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_escalation_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_escalation_state value = var:zg361_b2_m071_state }
		trigger_event = { id = zg361b2.50 days = 1 }
		if = {
			limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 2 }
			zg361_b2_m075_open_exit_offer_effect = yes
			if = {
				limit = { var:zg361_b2_m075_object_active = 1 var:zg361_b2_m075_state = 1 }
				var:zg361_b2_case_owner = { save_scope_as = zg361_b2_exit_offer_owner }
				save_scope_as = zg361_b2_exit_offer_subject
				save_scope_value_as = { name = zg361_b2_exit_offer_cycle value = var:zg361_b2_case_cycle }
				save_scope_value_as = { name = zg361_b2_exit_offer_case value = var:zg361_b2_case_serial }
				save_scope_value_as = { name = zg361_b2_exit_offer_state value = var:zg361_b2_m014_state }
				trigger_event = { id = zg361b2.60 days = 2 }
			}
		}
	}
	else = {
		if = {
			limit = { var:zg361_b2_m071_route = 2 }
			zg361_b2_publish_evidence_escalation_effect = yes
		}
		else = {
			set_variable = { name = zg361_b2_m071_state value = 4 }
			zg361_b2_m071_consume_business_object_effect = yes
		}
	}
	}
}

zg361_b2_publish_evidence_escalation_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 2 }
		set_variable = { name = zg361_b2_m071_evidence_strength value = 1 }
		if = {
			limit = { var:zg361_b2_m081_visible_fields >= 8 }
			set_variable = { name = zg361_b2_m071_evidence_strength value = 2 }
		}
		set_variable = { name = zg361_b2_m071_publication_identity value = this }
		set_variable = {
			name = zg361_b2_m071_evidence_hash
			value = {
				value = var:zg361_b2_case_serial
				multiply = 10
				add = var:zg361_b2_appeal_evidence_revision
			}
		}
		set_variable = { name = zg361_b2_m071_factcheck_state value = 1 }
		if = {
			limit = { var:zg361_b2_m071_route = 2 }
			set_variable = { name = zg361_b2_m071_immediate_publication value = 1 }
			set_variable = { name = zg361_b2_m071_mutual_reputation_cost value = 1 }
			var:zg361_b2_case_owner = { add_prestige = { value = 0 subtract = 25 } }
		}
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_factcheck_owner }
		save_scope_as = zg361_b2_factcheck_subject
		save_scope_value_as = { name = zg361_b2_factcheck_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_factcheck_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_factcheck_state value = var:zg361_b2_m071_factcheck_state }
		trigger_event = { id = zg361b2.141 days = 30 }
		add_prestige = { value = 0 subtract = 50 }
		zg361_b2_m079_open_skip_level_effect = yes
		zg361_b2_m080_open_metric_defect_effect = yes
	}
}

zg361_b2_publish_anonymous_report_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 3 }
		zg361_b2_m073_open_business_object_effect = yes
		zg361_b2_m073_triage_report_effect = yes
		zg361_b2_m071_consume_business_object_effect = yes
	}
}

zg361_b2_defer_escalation_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 4 }
		set_variable = { name = zg361_b2_m071_policy_debt value = 1 }
		zg361_b2_m071_consume_business_object_effect = yes
	}
}

zg361_b2_m073_triage_report_effect = {
	if = {
		limit = { var:zg361_b2_m073_object_active = 1 }
	set_variable = { name = zg361_b2_m073_state value = 2 }
	set_variable = { name = zg361_b2_m073_receipt_serial value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m073_provenance value = this }
	set_variable = {
		name = zg361_b2_m073_material_hash
		value = {
			value = var:zg361_b2_case_serial
			multiply = 10
			add = var:zg361_b2_appeal_reason
		}
	}
	set_variable = { name = zg361_b2_m073_truth_finding value = 0 }
	if = {
		limit = { var:zg361_b2_m073_route = 2 }
		set_variable = { name = zg361_b2_m073_blanket_sanction value = 1 }
		set_variable = { name = zg361_b2_m073_protected value = 0 }
		set_variable = { name = zg361_b2_m073_state value = 4 }
		if = {
			limit = { var:zg361_b2_m071_evidence_strength >= 2 }
			set_variable = { name = zg361_b2_m073_suppressed_genuine_lead value = 1 }
			var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
		add_prestige = { value = 0 subtract = 50 }
	}
	else_if = {
		limit = {
			var:zg361_b2_m071_evidence_strength >= 2
		}
		set_variable = { name = zg361_b2_m073_public_interest value = 1 }
		set_variable = { name = zg361_b2_m073_truth_finding value = 1 }
		set_variable = { name = zg361_b2_m073_protected value = 1 }
		set_variable = { name = zg361_b2_m073_state value = 3 }
		zg361_b2_m080_open_metric_defect_effect = yes
	}
	else = {
		set_variable = { name = zg361_b2_m073_malicious value = 1 }
		set_variable = { name = zg361_b2_m073_truth_finding value = 2 }
		set_variable = { name = zg361_b2_m073_state value = 4 }
		add_prestige = { value = 0 subtract = 50 }
	}
	zg361_b2_m073_consume_business_object_effect = yes
	}
}

# ---------------------------------------------------------------------------
# #074 honest redundancy and #075 voluntary exit. Both transfer only from an
# actually funded owner treasury and release HC only after an actual exit.
# ---------------------------------------------------------------------------

zg361_b2_m074_open_redundancy_offer_effect = {
	zg361_b2_m074_open_business_object_effect = yes
	if = {
		limit = { var:zg361_b2_m074_object_active = 1 var:zg361_b2_m074_state = 0 }
		set_variable = { name = zg361_b2_m074_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m074_subject value = this }
		set_variable = { name = zg361_b2_m074_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m074_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m074_state value = 1 }
		set_variable = { name = zg361_b2_m074_reason value = 1 } # organizational redundancy
		set_variable = { name = zg361_b2_m074_offer_gold value = 50 }
		set_variable = { name = zg361_b2_m074_redundancy_eligible value = 0 }
		set_variable = { name = zg361_b2_m074_treasury_paid value = 0 }
		set_variable = { name = zg361_b2_m074_personal_received value = 0 }
		set_variable = { name = zg361_b2_m074_actual_exit value = 0 }
		set_variable = { name = zg361_b2_m074_hc_released value = 0 }
		set_variable = { name = zg361_b2_m074_receipt_serial value = var:zg361_b2_case_serial }
		if = {
			limit = { var:zg361_b2_m074_route = 2 }
			set_variable = { name = zg361_b2_m074_reason value = 2 } # disguised performance exit
			set_variable = { name = zg361_b2_m074_offer_gold value = 0 }
			set_variable = { name = zg361_b2_m074_redundancy_eligible value = 1 }
			set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
			set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
		}
		if = {
			limit = {
				var:zg361_b2_m074_owner = {
					government_has_flag = government_has_treasury
					treasury >= 50
				}
			}
			set_variable = { name = zg361_b2_m074_redundancy_eligible value = 1 }
		}
	}
}

zg361_b2_m074_accept_redundancy_effect = {
	if = {
		limit = {
			var:zg361_b2_m074_owner = var:zg361_b2_case_owner
			var:zg361_b2_m074_subject = this
			var:zg361_b2_m074_object_active = 1
			var:zg361_b2_m074_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m074_case = var:zg361_b2_case_serial
			var:zg361_b2_m074_state = 1
			var:zg361_b2_m074_redundancy_eligible = 1
			var:zg361_b2_m074_receipt_serial = var:zg361_b2_m074_case
			OR = {
				var:zg361_b2_m074_route = 2
				var:zg361_b2_m074_owner = {
					government_has_flag = government_has_treasury
					treasury >= 50
				}
			}
		}
		if = {
			limit = { var:zg361_b2_m074_route = 1 }
			var:zg361_b2_m074_owner = { remove_treasury = 50 }
			add_gold = 50
			set_variable = { name = zg361_b2_m074_treasury_paid value = 50 }
			set_variable = { name = zg361_b2_m074_personal_received value = 50 }
			set_variable = { name = zg361_b2_m074_neutral_record value = 1 }
		}
		else = {
			set_variable = { name = zg361_b2_m074_treasury_paid value = 0 }
			set_variable = { name = zg361_b2_m074_personal_received value = 0 }
			set_variable = { name = zg361_b2_m074_unfunded_disguised_exit value = 1 }
		}
		set_variable = { name = zg361_b2_m074_actual_exit value = 1 }
		set_variable = { name = zg361_b2_m074_hc_released value = 1 }
		set_variable = { name = zg361_b2_m074_state value = 3 }
		var:zg361_b2_m074_owner = { save_scope_as = zg361_b2_redundancy_audit_owner }
		save_scope_as = zg361_b2_redundancy_audit_subject
		save_scope_value_as = { name = zg361_b2_redundancy_audit_cycle value = var:zg361_b2_m074_cycle }
		save_scope_value_as = { name = zg361_b2_redundancy_audit_case value = var:zg361_b2_m074_case }
		save_scope_value_as = { name = zg361_b2_redundancy_audit_state value = var:zg361_b2_m074_state }
		trigger_event = { id = zg361b2.171 days = 30 }
		force_step_down_landed_titles = yes
	}
}

zg361_b2_m074_reject_redundancy_effect = {
	if = {
		limit = { var:zg361_b2_m074_state = 1 }
		set_variable = { name = zg361_b2_m074_state value = 5 }
		set_variable = { name = zg361_b2_m074_redundancy_eligible value = 0 }
		zg361_b2_m074_consume_business_object_effect = yes
	}
}

zg361_b2_m075_open_exit_offer_effect = {
	zg361_b2_m075_open_business_object_effect = yes
	if = {
		limit = { var:zg361_b2_m075_object_active = 1 var:zg361_b2_m075_state = 0 }
		set_variable = { name = zg361_b2_m075_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m075_subject value = this }
		set_variable = { name = zg361_b2_m075_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m075_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m075_state value = 1 }
		set_variable = { name = zg361_b2_m075_offer_gold value = 50 }
		if = {
			limit = { var:zg361_b2_m075_route = 2 }
			set_variable = { name = zg361_b2_m075_offer_gold value = 0 }
			set_variable = { name = zg361_b2_m075_coercion_evidence value = 1 }
			set_variable = { name = zg361_b2_m075_reclassification_due value = 1 }
		}
		set_variable = { name = zg361_b2_m075_receipt_serial value = var:zg361_b2_case_serial }
		var:zg361_b2_m075_owner = { save_scope_as = zg361_b2_exit_deadline_owner }
		save_scope_as = zg361_b2_exit_deadline_subject
		save_scope_value_as = { name = zg361_b2_exit_deadline_cycle value = var:zg361_b2_m075_cycle }
		save_scope_value_as = { name = zg361_b2_exit_deadline_case value = var:zg361_b2_m075_case }
		save_scope_value_as = { name = zg361_b2_exit_deadline_state value = var:zg361_b2_m075_state }
		trigger_event = { id = zg361b2.61 days = 30 }
	}
}

zg361_b2_m075_accept_exit_offer_effect = {
	if = {
		limit = {
			var:zg361_b2_m075_owner = var:zg361_b2_case_owner
			var:zg361_b2_m075_subject = this
			var:zg361_b2_m075_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m075_case = var:zg361_b2_case_serial
			var:zg361_b2_m075_state = 1
			var:zg361_b2_m075_object_active = 1
			var:zg361_b2_m075_receipt_serial = var:zg361_b2_case_serial
			OR = {
				var:zg361_b2_m075_route = 2
				var:zg361_b2_case_owner = {
					government_has_flag = government_has_treasury
					treasury >= 50
				}
			}
		}
		if = {
			limit = { var:zg361_b2_m075_route = 1 }
			var:zg361_b2_case_owner = { remove_treasury = 50 }
			add_gold = 50
			set_variable = { name = zg361_b2_m075_treasury_paid value = 50 }
			set_variable = { name = zg361_b2_m075_personal_received value = 50 }
		}
		else = {
			set_variable = { name = zg361_b2_m075_treasury_paid value = 0 }
			set_variable = { name = zg361_b2_m075_personal_received value = 0 }
			set_variable = { name = zg361_b2_m075_procedural_redundancy value = 1 }
			var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
		set_variable = { name = zg361_b2_m075_state value = 3 }
		set_variable = { name = zg361_b2_m075_neutral_record value = 1 }
		set_variable = { name = zg361_b2_m075_actual_exit value = 1 }
		set_variable = { name = zg361_b2_m075_hc_released value = 1 }
		zg361_b2_m075_consume_business_object_effect = yes
		force_step_down_landed_titles = yes
	}
}

zg361_b2_m075_reject_exit_offer_effect = {
	if = {
		limit = { var:zg361_b2_m075_state = 1 }
		set_variable = { name = zg361_b2_m075_state value = 4 }
		set_variable = { name = zg361_b2_m075_refused_without_transfer value = 1 }
		zg361_b2_m075_consume_business_object_effect = yes
		# Refusal moves to ordinary PIP/appeal and transfers no resource.
	}
}

# ---------------------------------------------------------------------------
# #079/#080: skip-level investigation and a target-bound metric-defect ticket.
# ---------------------------------------------------------------------------

zg361_b2_m079_open_skip_level_effect = {
	zg361_b2_m079_open_business_object_effect = yes
	if = {
		limit = { var:zg361_b2_m079_object_active = 1 var:zg361_b2_m079_state = 0 }
		set_variable = { name = zg361_b2_m079_state value = 1 }
		set_variable = { name = zg361_b2_m079_receipt_serial value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m079_evidence_task value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m079_direct_grade_write_allowed value = 0 }
		if = {
			limit = { var:zg361_b2_m079_route = 2 }
			set_variable = { name = zg361_b2_m079_instant_promise_attempted value = 1 }
			set_variable = { name = zg361_b2_m079_overreach_risk value = 1 }
		}
		var:zg361_b2_case_owner = {
			if = {
				limit = { exists = liege liege = { is_alive = yes } }
				liege = { save_temporary_scope_as = zg361_b2_skip_level_reviewer }
			}
		}
		if = {
			limit = { exists = scope:zg361_b2_skip_level_reviewer }
			set_variable = { name = zg361_b2_m079_reviewer value = scope:zg361_b2_skip_level_reviewer }
			set_variable = { name = zg361_b2_m079_seat_reserved value = 0 }
			save_temporary_scope_as = zg361_b2_skip_subject
			scope:zg361_b2_skip_level_reviewer = {
				if = {
					limit = { NOT = { has_variable = zg361_b2_skip_seats_used } }
					set_variable = { name = zg361_b2_skip_seats_used value = 0 }
				}
				if = {
					limit = { var:zg361_b2_skip_seats_used < 2 }
					change_variable = { name = zg361_b2_skip_seats_used add = 1 }
					scope:zg361_b2_skip_subject = { set_variable = { name = zg361_b2_m079_seat_reserved value = 1 } }
				}
			}
			if = {
				limit = { var:zg361_b2_m079_seat_reserved = 1 }
				scope:zg361_b2_skip_level_reviewer = { save_scope_as = zg361_b2_skip_deadline_owner }
				save_scope_as = zg361_b2_skip_deadline_subject
				save_scope_value_as = { name = zg361_b2_skip_deadline_cycle value = var:zg361_b2_case_cycle }
				save_scope_value_as = { name = zg361_b2_skip_deadline_case value = var:zg361_b2_case_serial }
				save_scope_value_as = { name = zg361_b2_skip_deadline_state value = var:zg361_b2_m079_state }
				trigger_event = { id = zg361b2.140 days = 30 }
			}
			else = {
				set_variable = { name = zg361_b2_m079_state value = 4 }
				set_variable = { name = zg361_b2_m079_capacity_denied value = 1 }
				zg361_b2_m079_consume_business_object_effect = yes
			}
		}
		else = {
			set_variable = { name = zg361_b2_m079_state value = 4 }
			set_variable = { name = zg361_b2_m079_reviewer_unavailable value = 1 }
			zg361_b2_m079_consume_business_object_effect = yes
		}
	}
}

zg361_b2_m079_release_seat_effect = {
	if = {
		limit = {
			var:zg361_b2_m079_seat_reserved = 1
			has_variable = zg361_b2_m079_reviewer
		}
		var:zg361_b2_m079_reviewer = {
			if = {
				limit = { has_variable = zg361_b2_skip_seats_used var:zg361_b2_skip_seats_used >= 1 }
				change_variable = { name = zg361_b2_skip_seats_used add = -1 }
			}
		}
		set_variable = { name = zg361_b2_m079_seat_reserved value = 0 }
		set_variable = { name = zg361_b2_m079_seat_released value = 1 }
	}
}

zg361_b2_m080_open_metric_defect_effect = {
	zg361_b2_m080_open_business_object_effect = yes
	if = {
		limit = { var:zg361_b2_m080_object_active = 1 var:zg361_b2_m080_state = 0 }
		set_variable = { name = zg361_b2_m080_state value = 1 }
		set_variable = { name = zg361_b2_m080_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m080_subject value = this }
		set_variable = { name = zg361_b2_m080_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m080_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m080_metric_version value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m080_defect_id value = { value = var:zg361_b2_case_serial multiply = 10 add = var:zg361_b2_appeal_reason } }
		set_variable = { name = zg361_b2_m080_defect_type value = var:zg361_b2_appeal_reason }
		set_variable = { name = zg361_b2_m080_evidence_hash value = { value = var:zg361_b2_case_serial multiply = 100 add = var:zg361_b2_appeal_evidence_revision } }
		set_variable = { name = zg361_b2_m080_evidence_preserved value = 1 }
		if = {
			limit = { var:zg361_b2_m080_route = 2 }
			set_variable = { name = zg361_b2_m080_suppression_attempted value = 1 }
		}
		set_variable = { name = zg361_b2_m080_receipt_serial value = var:zg361_b2_case_serial }
		var:zg361_b2_m080_owner = { save_scope_as = zg361_b2_metric_deadline_owner }
		save_scope_as = zg361_b2_metric_deadline_subject
		save_scope_value_as = { name = zg361_b2_metric_deadline_cycle value = var:zg361_b2_m080_cycle }
		save_scope_value_as = { name = zg361_b2_metric_deadline_case value = var:zg361_b2_m080_case }
		save_scope_value_as = { name = zg361_b2_metric_deadline_state value = var:zg361_b2_m080_state }
		trigger_event = { id = zg361b2.150 days = 90 }
	}
}

# ---------------------------------------------------------------------------
# #070/#074/#358 adverse-action gate.  Core disposition effects call prepare,
# execute only when allowed, then call finish.  A new fact creates and serves a
# distinct misconduct notice instead of aggravating the appealed case.
# ---------------------------------------------------------------------------

zg361_b2_prepare_adverse_action_effect = {
	set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
	if = {
		limit = {
			has_variable = zg361_b2_separate_action_authorized
			var:zg361_b2_separate_action_authorized = 1
		}
		set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
	}
	else_if = {
		# The base result itself grants a ninety-day appeal window.  No D+2
		# elimination may outrun that window even before the subject files.
		limit = {
			has_variable = zg361_result_appeal_open
			var:zg361_result_appeal_open = 1
			has_variable = zg361_result_case_state
			var:zg361_result_case_state = 3
			NOT = { has_variable = zg361_b2_retaliation_state }
		}
		set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
		set_variable = { name = zg361_b2_m074_state value = 2 }
		set_variable = { name = zg361_b2_m074_reason value = 4 } # appeal window pending
		set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
		set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
		debug_log = "ZG361B2: adverse action held until base appeal window closes"
	}
	else_if = {
		limit = {
			has_variable = zg361_b2_retaliation_state
			var:zg361_b2_retaliation_state = 1
			var:zg361_b2_retaliation_subject = this
		}
		if = {
			limit = { var:zg361_b2_retaliation_new_fact = 1 }
			set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
			set_variable = { name = zg361_b2_m070_finding value = 2 } # new fact, separate case
			set_variable = { name = zg361_b2_m074_state value = 3 }
			set_variable = { name = zg361_b2_m074_reason value = 1 }
			zg361_b2_m358_open_separate_case_effect = yes
			if = {
				limit = { is_ai = yes }
				zg361_b2_deliver_separate_case_effect = yes
				set_variable = { name = zg361_b2_separate_action_authorized value = 1 }
				set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
			}
		}
		else = {
			if = {
				limit = { var:zg361_b2_m070_route = 2 }
				# Expedient policy really permits the action, but freezes an
				# explicit retaliation finding and a heavier manager liability.
				set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
				set_variable = { name = zg361_b2_m070_finding value = 3 }
				set_variable = { name = zg361_b2_m070_retaliation_action_executed value = var:zg361_b2_pending_adverse_action }
				set_variable = { name = zg361_b2_m070_retaliation_receipt value = var:zg361_b2_retaliation_case }
				set_variable = { name = zg361_b2_m074_state value = 4 }
				set_variable = { name = zg361_b2_m074_reason value = 2 }
				set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
				set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
				var:zg361_b2_retaliation_owner = { change_variable = { name = zg361_b2_management_debt add = 2 } }
				debug_log = "ZG361B2: expedient post-appeal retaliation executed and disclosed"
			}
			else = {
				set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
				change_variable = { name = zg361_b2_retaliation_suspended_n add = 1 }
				set_variable = { name = zg361_b2_m070_finding value = 1 } # pending independent review
				set_variable = { name = zg361_b2_m074_state value = 2 }
				set_variable = { name = zg361_b2_m074_reason value = 2 }
				set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
				set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
				var:zg361_b2_retaliation_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
				debug_log = "ZG361B2: unsupported post-appeal adverse action suspended"
			}
		}
	}
	else = {
		set_variable = { name = zg361_b2_m074_state value = 1 }
		set_variable = { name = zg361_b2_m074_reason value = 3 }
	}
	set_variable = { name = zg361_b2_m074_receipt_serial value = var:zg361_result_case_serial }
}

zg361_b2_finish_adverse_action_effect = {
	remove_variable = zg361_b2_pending_adverse_action
	remove_variable = zg361_b2_adverse_action_allowed
	remove_variable = zg361_b2_separate_action_authorized
}

zg361_b2_cancel_blocked_action_effect = {
	remove_variable = zg361_b2_adverse_action_allowed
	if = {
		limit = { NOT = { has_variable = zg361_b2_separate_notice_state } }
		remove_variable = zg361_b2_pending_adverse_action
	}
}

zg361_b2_m358_open_separate_case_effect = {
	if = {
		limit = { var:zg361_b2_m358_state >= 1 }
		set_variable = { name = zg361_b2_m358_separate_case value = { value = var:zg361_b2_case_serial add = 100000 } }
		set_variable = { name = zg361_b2_separate_notice_owner value = var:zg361_b2_retaliation_owner }
		set_variable = { name = zg361_b2_separate_notice_subject value = this }
		set_variable = { name = zg361_b2_separate_notice_cycle value = var:zg361_b2_retaliation_cycle }
		set_variable = { name = zg361_b2_separate_notice_case value = var:zg361_b2_m358_separate_case }
		set_variable = { name = zg361_b2_separate_notice_state value = 1 }
		set_variable = { name = zg361_b2_m358_state value = 2 }
		if = {
			limit = { is_ai = no }
			var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_prompt_owner }
			save_scope_as = zg361_b2_separate_prompt_subject
			save_scope_value_as = { name = zg361_b2_separate_prompt_cycle value = var:zg361_b2_separate_notice_cycle }
			save_scope_value_as = { name = zg361_b2_separate_prompt_case value = var:zg361_b2_separate_notice_case }
			save_scope_value_as = { name = zg361_b2_separate_prompt_state value = var:zg361_b2_separate_notice_state }
			trigger_event = { id = zg361b2.160 days = 1 }
		}
	}
}

zg361_b2_deliver_separate_case_effect = {
	if = {
		limit = {
			OR = {
				var:zg361_b2_separate_notice_state = 1
				var:zg361_b2_separate_notice_state = 2
			}
		}
		set_variable = { name = zg361_b2_separate_notice_state value = 3 }
		set_variable = { name = zg361_b2_separate_delivery_receipt value = var:zg361_b2_separate_notice_case }
		set_variable = { name = zg361_b2_separate_appeal_open value = 1 }
		var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_deadline_owner }
		save_scope_as = zg361_b2_separate_deadline_subject
		save_scope_value_as = { name = zg361_b2_separate_deadline_cycle value = var:zg361_b2_separate_notice_cycle }
		save_scope_value_as = { name = zg361_b2_separate_deadline_case value = var:zg361_b2_separate_notice_case }
		save_scope_value_as = { name = zg361_b2_separate_deadline_state value = var:zg361_b2_separate_notice_state }
		trigger_event = { id = zg361b2.162 days = 90 }
	}
}

zg361_b2_execute_pending_adverse_action_effect = {
	if = {
		limit = {
			var:zg361_b2_separate_notice_state = 3
			var:zg361_b2_separate_delivery_receipt = var:zg361_b2_separate_notice_case
			has_variable = zg361_b2_pending_adverse_action
		}
		set_variable = { name = zg361_b2_separate_action_authorized value = 1 }
		if = { limit = { var:zg361_b2_pending_adverse_action = 1 } zg361_eliminate_purge_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 2 } zg361_eliminate_stepdown_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 3 } zg361_eliminate_demote_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 4 } zg361_eliminate_extend_effect = yes }
		if = {
			limit = { var:zg361_b2_m017_object_active = 1 var:zg361_b2_m017_state = 2 }
			set_variable = { name = zg361_b2_m017_state value = 3 }
			set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
			zg361_b2_m017_consume_business_object_effect = yes
		}
	}
}

# ---------------------------------------------------------------------------
# #359 quota return: an exact PP #157 nomination receipt,
# boundary review/redelivery, or next-cycle debt.
# ---------------------------------------------------------------------------

zg361_b2_m359_open_quota_return_effect = {
	if = {
		limit = { var:zg361_b2_m359_object_active = 1 var:zg361_b2_m359_state = 0 }
		set_variable = { name = zg361_b2_m359_state value = 1 }
		set_variable = { name = zg361_b2_m359_receipt_serial value = var:zg361_b2_case_serial }
		if = {
			limit = {
				var:zg361_b2_m359_route = 1
				var:zg361_b2_case_owner = { is_ai = no zg361_is_celestial_liege_trigger = yes }
			}
			var:zg361_b2_case_owner = { save_scope_as = zg361_b2_quota_return_owner }
			save_scope_as = zg361_b2_quota_return_subject
			save_scope_value_as = { name = zg361_b2_quota_return_cycle value = var:zg361_b2_case_cycle }
			save_scope_value_as = { name = zg361_b2_quota_return_case value = var:zg361_b2_case_serial }
			save_scope_value_as = { name = zg361_b2_quota_return_state value = var:zg361_b2_m359_state }
			var:zg361_b2_case_owner = { trigger_event = { id = zg361b2.130 days = 1 } }
		}
		else_if = {
			limit = { var:zg361_b2_m359_route = 2 }
			set_variable = { name = zg361_b2_m359_hidden_rebalance value = 1 }
			set_variable = { name = zg361_b2_m359_audit_diff_preserved value = 1 }
			zg361_b2_m359_open_boundary_review_effect = yes
		}
		else_if = {
			limit = {
				var:zg361_b2_m359_route = 1
				var:zg361_b2_case_owner = { is_ai = yes }
			}
			zg361_b2_m359_return_pp_nomination_slot_effect = yes
			if = {
				limit = { NOT = { var:zg361_b2_m359_refund_applied = 1 } }
				zg361_b2_m359_post_next_cycle_debt_effect = yes
			}
		}
		else = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

zg361_b2_m359_return_pp_nomination_slot_effect = {
	remove_variable = zg361_case_kernel_applied
	set_variable = { name = zg361_b2_m359_refund_applied value = 0 }
	if = {
		limit = {
			has_variable = zg361_b2_case_owner
			has_variable = zg361_b2_case_subject
			has_variable = zg361_b2_case_cycle
			has_variable = zg361_b2_case_serial
			has_variable = zg361_b2_m359_route
			has_variable = zg361_b2_m359_object_owner
			has_variable = zg361_b2_m359_object_subject
			has_variable = zg361_b2_m359_object_cycle
			has_variable = zg361_b2_m359_object_receipt_case
			var:zg361_b2_m359_object_active = 1
			var:zg361_b2_m359_state = 1
			var:zg361_b2_m359_route = 1
			var:zg361_b2_m359_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_case_subject = this
			var:zg361_b2_m359_object_owner = var:zg361_b2_case_owner
			var:zg361_b2_m359_object_subject = this
			var:zg361_b2_m359_object_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m359_object_receipt_case = var:zg361_b2_case_serial
			has_variable = zg361_pp_m157_packet_candidate
			has_variable = zg361_pp_m157_nomination_slot_owner
			has_variable = zg361_pp_m157_nomination_slot_cycle
			has_variable = zg361_pp_m157_nomination_slot_case
			has_variable = zg361_pp_m157_nomination_slot_amount
			has_variable = zg361_pp_m157_nomination_slot_status
			has_variable = zg361_case_u_owner
			has_variable = zg361_case_u_subject
			has_variable = zg361_case_u_cycle_serial
			has_variable = zg361_case_u_case_serial
			has_variable = zg361_case_u_state
			has_variable = zg361_case_u_revision
			has_variable = zg361_case_u_active
			has_variable = zg361_pp_u_nomination_slot_available
			has_variable = zg361_pp_u_nomination_slot_reserved
			has_variable = zg361_pp_u_nomination_slot_settled
			var:zg361_pp_m157_packet_candidate = this
			var:zg361_case_u_owner = var:zg361_b2_case_owner
			var:zg361_case_u_subject = this
			var:zg361_case_u_cycle_serial = var:zg361_b2_case_cycle
			var:zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner
			var:zg361_pp_m157_nomination_slot_cycle = var:zg361_case_u_cycle_serial
			var:zg361_pp_m157_nomination_slot_case = var:zg361_case_u_case_serial
			var:zg361_pp_m157_nomination_slot_amount = 1
			OR = {
				AND = {
					var:zg361_pp_m157_nomination_slot_status = 1
					var:zg361_pp_u_nomination_slot_reserved >= var:zg361_pp_m157_nomination_slot_amount
				}
				AND = {
					var:zg361_pp_m157_nomination_slot_status = 2
					var:zg361_pp_u_nomination_slot_settled >= var:zg361_pp_m157_nomination_slot_amount
				}
			}
		}
		set_variable = { name = zg361_b2_m359_pp_nomination_owner value = var:zg361_pp_m157_nomination_slot_owner }
		set_variable = { name = zg361_b2_m359_pp_nomination_cycle value = var:zg361_pp_m157_nomination_slot_cycle }
		set_variable = { name = zg361_b2_m359_pp_nomination_case value = var:zg361_pp_m157_nomination_slot_case }
		set_variable = { name = zg361_b2_m359_pp_nomination_amount value = var:zg361_pp_m157_nomination_slot_amount }
		set_variable = { name = zg361_b2_m359_pp_nomination_status_before value = var:zg361_pp_m157_nomination_slot_status }
		zg361_case_kernel_refund_transaction_effect = {
			OWNER_VAR = zg361_case_u_owner
			SUBJECT_VAR = zg361_case_u_subject
			CYCLE_VAR = zg361_case_u_cycle_serial
			CASE_VAR = zg361_case_u_case_serial
			STATE_VAR = zg361_case_u_state
			ACTIVE_VAR = zg361_case_u_active
			REVISION_VAR = zg361_case_u_revision
			AVAILABLE_VAR = zg361_pp_u_nomination_slot_available
			RESERVED_VAR = zg361_pp_u_nomination_slot_reserved
			SETTLED_VAR = zg361_pp_u_nomination_slot_settled
			RECEIPT_AMOUNT_VAR = zg361_pp_m157_nomination_slot_amount
			RECEIPT_STATUS_VAR = zg361_pp_m157_nomination_slot_status
			TICKET_OWNER = var:zg361_pp_m157_nomination_slot_owner
			TICKET_SUBJECT = this
			TICKET_CYCLE = var:zg361_pp_m157_nomination_slot_cycle
			TICKET_CASE = var:zg361_pp_m157_nomination_slot_case
			TICKET_STATE = var:zg361_case_u_state
		}
		if = {
			limit = { var:zg361_case_kernel_applied = 1 }
			set_variable = { name = zg361_b2_m359_refund_applied value = 1 }
			set_variable = { name = zg361_b2_m359_pp_nomination_status_after value = var:zg361_pp_m157_nomination_slot_status }
			set_variable = { name = zg361_b2_m359_state value = 2 }
			set_variable = { name = zg361_b2_m359_return_route value = 1 }
			set_variable = { name = zg361_b2_m359_reserved_consumed value = 1 }
			zg361_b2_m359_consume_business_object_effect = yes
		}
	}
}

zg361_b2_m359_post_next_cycle_debt_effect = {
	if = {
		limit = {
			var:zg361_b2_m359_object_active = 1
			var:zg361_b2_m359_state = 1
			var:zg361_b2_m359_receipt_serial = var:zg361_b2_case_serial
		}
		save_temporary_scope_as = zg361_b2_quota_debt_subject
		set_variable = { name = zg361_b2_m359_state value = 2 }
		set_variable = { name = zg361_b2_m359_return_route value = 3 }
		set_variable = { name = zg361_b2_m359_debt_added value = 1 }
		var:zg361_b2_case_owner = {
			change_variable = { name = zg361_b2_quota_debt add = 1 }
			set_variable = { name = zg361_b2_quota_debt_due_cycle value = { value = scope:zg361_b2_quota_debt_subject.var:zg361_b2_case_cycle add = 1 } }
			set_variable = { name = zg361_b2_quota_debt_source_case value = scope:zg361_b2_quota_debt_subject.var:zg361_b2_case_serial }
		}
		zg361_b2_m359_consume_business_object_effect = yes
	}
}

zg361_b2_m359_open_boundary_review_effect = {
	if = {
		limit = {
			var:zg361_b2_m359_object_active = 1
			var:zg361_b2_m359_state = 1
			var:zg361_b2_m359_receipt_serial = var:zg361_b2_case_serial
		}
		save_temporary_scope_as = zg361_b2_corrected_subject
		var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_boundary_owner }
		var:zg361_b2_case_owner = {
			ordered_vassal = {
				limit = {
					NOT = { this = scope:zg361_b2_corrected_subject }
					has_variable = zg361_result_case_owner
					var:zg361_result_case_owner = scope:zg361_b2_boundary_owner
					has_variable = zg361_result_cycle_serial
					var:zg361_result_cycle_serial = scope:zg361_b2_corrected_subject.var:zg361_b2_case_cycle
					has_variable = zg361_result_grade
					var:zg361_result_grade = 2
				}
				order_by = var:zg361_result_rank_frozen
				position = 0
				save_scope_as = zg361_b2_boundary_subject
			}
		}
		if = {
			limit = { exists = scope:zg361_b2_boundary_subject }
			set_variable = { name = zg361_b2_m359_state value = 2 }
			set_variable = { name = zg361_b2_m359_return_route value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_subject value = scope:zg361_b2_boundary_subject }
			set_variable = { name = zg361_b2_m359_corrected_grade_before value = 1 }
			set_variable = { name = zg361_b2_m359_corrected_grade_after value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_grade_before value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_grade_after value = 1 }
			scope:zg361_b2_boundary_subject = { zg361_b2_prepare_boundary_redelivery_effect = yes }
		}
		else = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

zg361_b2_prepare_boundary_redelivery_effect = {
	set_variable = { name = zg361_b2_redelivery_source_subject value = scope:zg361_b2_corrected_subject }
	set_variable = { name = zg361_b2_redelivery_owner value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_redelivery_subject value = this }
	set_variable = { name = zg361_b2_redelivery_cycle value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_redelivery_case value = { value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_serial add = 200000 } }
	set_variable = { name = zg361_b2_redelivery_state value = 1 }
	set_variable = { name = zg361_b2_redelivery_contested value = 0 }
	set_variable = { name = zg361_b2_redelivery_receipt value = 0 }
	if = {
		limit = { is_ai = yes }
		set_variable = { name = zg361_b2_redelivery_method value = 4 }
		zg361_b2_deliver_boundary_notice_effect = yes
	}
	else = {
		var:zg361_b2_redelivery_owner = { save_scope_as = zg361_b2_redelivery_prompt_owner }
		save_scope_as = zg361_b2_redelivery_prompt_subject
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_cycle value = var:zg361_b2_redelivery_cycle }
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_case value = var:zg361_b2_redelivery_case }
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_state value = var:zg361_b2_redelivery_state }
		trigger_event = { id = zg361b2.131 days = 1 }
	}
}

zg361_b2_deliver_boundary_notice_effect = {
	if = {
		limit = {
			OR = {
				var:zg361_b2_redelivery_state = 1
				var:zg361_b2_redelivery_state = 2
			}
		}
		set_variable = { name = zg361_b2_redelivery_state value = 3 }
		set_variable = { name = zg361_b2_redelivery_receipt value = var:zg361_b2_redelivery_case }
		zg361_b2_apply_boundary_redelivery_effect = yes
	}
}

zg361_b2_contest_boundary_notice_effect = {
	if = {
		limit = {
			var:zg361_b2_redelivery_state = 3
			var:zg361_b2_redelivery_receipt = var:zg361_b2_redelivery_case
		}
		set_variable = { name = zg361_b2_redelivery_contested value = 1 }
		set_variable = { name = zg361_b2_redelivery_state value = 4 }
		set_variable = { name = zg361_result_objection_recorded value = 1 }
		zg361_b2_on_appeal_filed_effect = yes
	}
}

zg361_b2_apply_boundary_redelivery_effect = {
	if = {
		limit = {
			var:zg361_b2_redelivery_state = 3
			var:zg361_b2_redelivery_receipt = var:zg361_b2_redelivery_case
			var:zg361_result_case_owner = var:zg361_b2_redelivery_owner
			var:zg361_result_cycle_serial = var:zg361_b2_redelivery_cycle
			var:zg361_result_grade = 2
			var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
		}
		remove_character_modifier = zg361_grade_35
		set_variable = { name = zg361_b2_redelivery_original_result_case value = var:zg361_result_case_serial }
		set_variable = { name = zg361_result_case_serial value = var:zg361_b2_redelivery_case }
		set_variable = { name = zg361_last_grade value = 1 }
		set_variable = { name = zg361_result_grade value = 1 }
		set_variable = { name = zg361_result_grade_reason value = 9 }
		set_variable = { name = zg361_result_case_state value = 3 }
		set_variable = { name = zg361_result_delivery_method value = var:zg361_b2_redelivery_method }
		set_variable = { name = zg361_result_delivered_year value = current_year }
		set_variable = { name = zg361_result_settlement_posted_serial value = 0 }
		set_variable = { name = zg361_result_refund_posted_serial value = 0 }
		set_variable = { name = zg361_result_treasury_paid value = 0 }
		set_variable = { name = zg361_result_gold_paid value = 0 }
		set_variable = { name = zg361_result_merit_paid value = 0 }
		set_variable = { name = zg361_result_treasury_refunded value = 0 }
		set_variable = { name = zg361_result_gold_refunded value = 0 }
		set_variable = { name = zg361_result_merit_refunded value = 0 }
		set_variable = { name = zg361_result_salary_cut_active value = 0 }
		set_variable = { name = zg361_result_appeal_open value = 0 }
		save_temporary_scope_as = zg361_b2_adjusted_boundary_subject
		var:zg361_b2_redelivery_owner = {
			if = {
				limit = {
					has_variable = zg361_review_serial
					var:zg361_review_serial = scope:zg361_b2_adjusted_boundary_subject.var:zg361_b2_redelivery_cycle
					has_variable = zg361_last_35_n
					var:zg361_last_35_n >= 1
				}
				change_variable = { name = zg361_last_35_n add = -1 }
				change_variable = { name = zg361_last_325_n add = 1 }
			}
			set_variable = { name = zg361_b2_scoreboard_redelivery_dirty value = 1 }
		}
		var:zg361_b2_redelivery_source_subject = {
			set_variable = { name = zg361_b2_m359_state value = 3 }
			set_variable = { name = zg361_b2_m359_redelivery_subject value = scope:zg361_b2_adjusted_boundary_subject }
			set_variable = { name = zg361_b2_m359_redelivery_receipt value = scope:zg361_b2_adjusted_boundary_subject.var:zg361_b2_redelivery_case }
			zg361_b2_m359_consume_business_object_effect = yes
		}
		# Reuse the proven product settlement and appeal/refund chain.  The
		# redelivery receipt authorizes this reset once; all actual money/merit
		# writes and the new D+90 appeal timer remain owned by the core effect.
		zg361_b2_on_result_frozen_effect = yes
		zg361_settle_delivered_325_effect = yes
	}
}

zg361_b2_apply_due_quota_debt_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_quota_debt
			var:zg361_b2_quota_debt >= 1
			has_variable = zg361_b2_quota_debt_due_cycle
			var:zg361_review_serial >= var:zg361_b2_quota_debt_due_cycle
			trigger_if = {
				limit = { has_variable = zg361_b2_quota_debt_consumed_cycle }
				NOT = { var:zg361_b2_quota_debt_consumed_cycle = var:zg361_review_serial }
			}
			trigger_else = { always = yes }
		}
		change_variable = { name = zg361_bottom_slots add = var:zg361_b2_quota_debt }
		set_variable = { name = zg361_b2_quota_debt_consumed_slots value = var:zg361_b2_quota_debt }
		set_variable = { name = zg361_b2_quota_debt value = 0 }
		set_variable = { name = zg361_b2_quota_debt_consumed_cycle value = var:zg361_review_serial }
		debug_log = "ZG361B2: next-cycle quota debt consumed once"
	}
}

# Management responsibility and metric-risk debts are consumed by the next
# real KPI computation of that manager, never by the appealed subject's case.
zg361_b2_consume_pip_performance_evidence_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_performance_evidence_status = 1
			var:zg361_b2_pip_performance_evidence_subject = this
			has_variable = zg361_b2_pip_performance_evidence_source_cycle
			has_variable = zg361_b2_pip_performance_evidence_due_cycle
			# The KPI hook runs before either cycle path publishes its new serial.
			# Active B1 therefore consumes against its prospective frozen serial;
			# legacy/no-B1 consumes when the previous serial reaches source_cycle.
			OR = {
				AND = {
					root = {
						has_character_flag = zg361_b1_cycle_active
						has_variable = zg361_b1_cycle_serial
					}
					root.var:zg361_b1_cycle_serial >= var:zg361_b2_pip_performance_evidence_due_cycle
				}
				AND = {
					root = {
						NOT = { has_character_flag = zg361_b1_cycle_active }
						has_variable = zg361_review_serial
					}
					root.var:zg361_review_serial >= var:zg361_b2_pip_performance_evidence_source_cycle
				}
			}
			OR = {
				var:zg361_b2_pip_performance_evidence_delta = 10
				var:zg361_b2_pip_performance_evidence_delta = -10
				var:zg361_b2_pip_performance_evidence_delta = -15
			}
		}
		change_variable = { name = zg361_evidence_growth add = var:zg361_b2_pip_performance_evidence_delta }
		change_variable = { name = zg361_kpi add = var:zg361_b2_pip_performance_evidence_delta }
		set_variable = { name = zg361_b2_pip_performance_evidence_status value = 2 }
		# Legacy records the producer's due cycle. Active B1 records the actual
		# frozen serial that admitted this compute (including a safe catch-up).
		set_variable = { name = zg361_b2_pip_performance_evidence_consumed_cycle value = var:zg361_b2_pip_performance_evidence_due_cycle }
		if = {
			limit = {
				root = {
					has_character_flag = zg361_b1_cycle_active
					has_variable = zg361_b1_cycle_serial
				}
				root.var:zg361_b1_cycle_serial >= var:zg361_b2_pip_performance_evidence_due_cycle
			}
			set_variable = { name = zg361_b2_pip_performance_evidence_consumed_cycle value = root.var:zg361_b1_cycle_serial }
		}
		set_variable = { name = zg361_b2_pip_performance_evidence_consumed_case value = var:zg361_b2_pip_performance_evidence_source_case }
		debug_log = "ZG361B2: terminal PIP evidence consumed once by a later KPI computation"
	}
}

zg361_b2_consume_management_debt_effect = {
	if = {
		limit = { has_variable = zg361_b2_management_debt var:zg361_b2_management_debt >= 1 }
		set_variable = { name = zg361_b2_management_debt_applied value = { value = var:zg361_b2_management_debt multiply = 10 max = 30 } }
		change_variable = { name = zg361_evidence_organization subtract = var:zg361_b2_management_debt_applied }
		change_variable = { name = zg361_kpi subtract = var:zg361_b2_management_debt_applied }
		set_variable = { name = zg361_b2_management_debt value = 0 }
		set_variable = { name = zg361_b2_management_debt_consumed_year value = current_year }
	}
}
''' + render_policy_object_kernel() + render_fairness_kernel()


def render_effects() -> bytes:
    """Render the frozen historical monolith for semantic validation only.

    The monolith remains deliberately available as an in-memory reference.  It
    is not a product output after the purpose split.
    """

    return generated(render_effect_source())


def _top_level_effect_blocks(source: str) -> tuple[tuple[str, str], ...]:
    matches = tuple(
        re.finditer(
            r"(?m)^(zg361_b2_[a-z0-9_]+_effect)\s*=\s*\{",
            source,
        )
    )
    blocks: list[tuple[str, str]] = []
    for match in matches:
        opening = source.index("{", match.start(), match.end())
        depth = 0
        quoted = False
        escaped = False
        commented = False
        for index in range(opening, len(source)):
            char = source[index]
            if commented:
                if char == "\n":
                    commented = False
                continue
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == "#":
                commented = True
            elif char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(
                        (match.group(1), source[match.start() : index + 1])
                    )
                    break
        else:
            raise ValueError(f"unterminated B2 effect block: {match.group(1)}")
    return tuple(blocks)


def render_effect_parts() -> dict[str, bytes]:
    """Render the 25 purpose shards without changing any effect block bytes."""

    historical_blocks = _top_level_effect_blocks(render_effect_source())
    historical_names = tuple(name for name, _block in historical_blocks)
    block_by_name = dict(historical_blocks)
    configured_names = tuple(
        name for _filename, names in EFFECT_GROUPS for name in names
    )

    if len(EFFECT_GROUPS) != 25:
        raise ValueError("B2 runtime must remain split into exactly 25 purpose files")
    if len(historical_names) != 152 or len(set(historical_names)) != 152:
        raise ValueError("B2 historical render must contain 152 unique effects")
    if len(configured_names) != 152 or len(set(configured_names)) != 152:
        raise ValueError("B2 purpose map must contain 152 unique effects")
    if set(configured_names) != set(historical_names):
        missing = sorted(set(historical_names) - set(configured_names))
        extra = sorted(set(configured_names) - set(historical_names))
        raise ValueError(f"B2 purpose map mismatch: missing={missing}, extra={extra}")

    rendered: dict[str, bytes] = {}
    for filename, names in EFFECT_GROUPS:
        if not names:
            raise ValueError(
                f"B2 purpose file must contain at least one effect: {filename}"
            )
        if len(names) > EFFECT_HARD_MAX:
            exception = EFFECT_HARD_LIMIT_EXCEPTIONS.get(filename)
            if (
                exception is None
                or len(exception) != 2
                or not exception[0].strip()
                or not exception[1].strip()
            ):
                raise ValueError(
                    f"B2 purpose file exceeds {EFFECT_HARD_MAX} effects without "
                    f"a reason and CK3 live-evidence reference: {filename}"
                )
        body = "\n\n".join(block_by_name[name] for name in names)
        rendered[filename] = generated(
            f"# B2 purpose shard: {filename}\n\n{body}"
        )
    exception_files = set(EFFECT_HARD_LIMIT_EXCEPTIONS)
    oversized_files = {
        filename
        for filename, names in EFFECT_GROUPS
        if len(names) > EFFECT_HARD_MAX
    }
    if exception_files != oversized_files:
        raise ValueError(
            "B2 hard-limit exceptions must exactly match oversized shards: "
            f"exceptions={sorted(exception_files)}, oversized={sorted(oversized_files)}"
        )
    return rendered


def render_events() -> bytes:
    return generated(r'''
namespace = zg361b2

# #015 acknowledgement. Visible events are player-only; AI subjects take the
# same effects silently at the call site.
zg361b2.40 = {
	type = character_event
	theme = vassal
	title = zg361b2.40.t
	desc = zg361b2.40.desc
	trigger = {
		is_ai = no
		has_game_rule = zg361_on
		exists = scope:zg361_b2_pip_prompt_owner
		exists = scope:zg361_b2_pip_prompt_subject
		this = scope:zg361_b2_pip_prompt_subject
		var:zg361_b2_pip_owner = scope:zg361_b2_pip_prompt_owner
		var:zg361_b2_pip_subject = scope:zg361_b2_pip_prompt_subject
		var:zg361_b2_pip_cycle = scope:zg361_b2_pip_prompt_cycle
		var:zg361_b2_pip_case = scope:zg361_b2_pip_prompt_case
		var:zg361_b2_pip_state = scope:zg361_b2_pip_prompt_state
		var:zg361_b2_pip_state = 1
	}
	option = { name = zg361b2.40.a zg361_b2_accept_pip_effect = yes }
	option = { name = zg361b2.40.b zg361_b2_negotiate_pip_effect = yes }
	option = { name = zg361b2.40.c zg361_b2_refuse_pip_effect = yes }
}

# #071/#073 escalation after an upheld appeal.
zg361b2.50 = {
	type = character_event
	theme = vassal
	title = zg361b2.50.t
	desc = zg361b2.50.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_escalation_owner
		exists = scope:zg361_b2_escalation_subject
		this = scope:zg361_b2_escalation_subject
		var:zg361_b2_case_owner = scope:zg361_b2_escalation_owner
		var:zg361_b2_case_subject = scope:zg361_b2_escalation_subject
		var:zg361_b2_case_cycle = scope:zg361_b2_escalation_cycle
		var:zg361_b2_case_serial = scope:zg361_b2_escalation_case
		var:zg361_b2_m071_state = scope:zg361_b2_escalation_state
		var:zg361_b2_m071_state = 1
	}
	option = { name = zg361b2.50.a zg361_b2_publish_evidence_escalation_effect = yes }
	option = { name = zg361b2.50.b zg361_b2_publish_anonymous_report_effect = yes }
	option = { name = zg361b2.50.c zg361_b2_defer_escalation_effect = yes }
}

# #075 voluntary exit; the option is absent unless the frozen owner can fund
# the exact fifty-treasury / fifty-personal-gold transfer.
zg361b2.60 = {
	type = character_event
	theme = vassal
	title = zg361b2.60.t
	desc = zg361b2.60.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_exit_offer_owner
		exists = scope:zg361_b2_exit_offer_subject
		this = scope:zg361_b2_exit_offer_subject
		var:zg361_b2_case_owner = scope:zg361_b2_exit_offer_owner
		var:zg361_b2_case_subject = scope:zg361_b2_exit_offer_subject
		var:zg361_b2_case_cycle = scope:zg361_b2_exit_offer_cycle
		var:zg361_b2_case_serial = scope:zg361_b2_exit_offer_case
		var:zg361_b2_m014_state = scope:zg361_b2_exit_offer_state
		var:zg361_b2_m014_state = 4
		var:zg361_b2_m075_object_active = 1
		var:zg361_b2_m075_state = 1
	}
	immediate = { zg361_b2_m075_open_exit_offer_effect = yes }
	option = {
		name = zg361b2.60.a
		trigger = {
			var:zg361_b2_case_owner = {
				government_has_flag = government_has_treasury
				treasury >= 50
			}
		}
		zg361_workforce_normal_exit_fact_begin_from_m075_offer_effect = yes
	}
	option = { name = zg361b2.60.b zg361_b2_m075_reject_exit_offer_effect = yes }
}

zg361b2.61 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_exit_deadline_owner
				exists = scope:zg361_b2_exit_deadline_subject
				this = scope:zg361_b2_exit_deadline_subject
				var:zg361_b2_m075_owner = scope:zg361_b2_exit_deadline_owner
				var:zg361_b2_m075_subject = scope:zg361_b2_exit_deadline_subject
				var:zg361_b2_m075_cycle = scope:zg361_b2_exit_deadline_cycle
				var:zg361_b2_m075_case = scope:zg361_b2_exit_deadline_case
				var:zg361_b2_m075_state = scope:zg361_b2_exit_deadline_state
				var:zg361_b2_m075_state = 1
			}
			set_variable = { name = zg361_b2_m075_state value = 5 }
			set_variable = { name = zg361_b2_m075_expired value = 1 }
			zg361_b2_m075_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale voluntary-exit D+30 ticket ignored" }
	}
}

# #016 D+180 support/progress receipt. The event records real delivery facts
# and the exact native KPI delta; missing/mismatched provenance stays RED.
zg361b2.99 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_pip_deadline_owner
				exists = scope:zg361_b2_pip_deadline_subject
				this = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_pip_deadline_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_pip_deadline_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_pip_deadline_case
				var:zg361_b2_pip_state = scope:zg361_b2_pip_deadline_state
				var:zg361_b2_pip_state = 2
			}
			zg361_b2_record_pip_midpoint_effect = yes
		}
		else = { debug_log = "ZG361B2: stale PIP D+180 ticket ignored" }
	}
}

# #015–017 D+365 independent outcome. Every component of the immutable ticket
# must match before the frozen reviewer may sign a conclusion.
zg361b2.100 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_pip_deadline_owner
				exists = scope:zg361_b2_pip_deadline_subject
				this = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_pip_deadline_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_pip_deadline_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_pip_deadline_case
				var:zg361_b2_pip_state = scope:zg361_b2_pip_deadline_state
				var:zg361_b2_pip_state = 2
			}
			zg361_b2_resolve_pip_due_effect = yes
		}
		else = { debug_log = "ZG361B2: stale PIP D+365 ticket ignored" }
	}
}

# Commit boundary 1: outcome_code was selected by .100/resolve on the previous
# day.  This event binds the exact active PIP ticket before the terminal writer.
zg361b2.101 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_terminal_settlement_owner
				exists = scope:zg361_b2_terminal_settlement_subject
				this = scope:zg361_b2_terminal_settlement_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_terminal_settlement_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_terminal_settlement_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_terminal_settlement_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_terminal_settlement_case
				var:zg361_b2_pip_state = scope:zg361_b2_terminal_settlement_state
				var:zg361_b2_pip_state = 2
			}
			zg361_b2_settle_pip_outcome_effect = yes
		}
		else = { debug_log = "ZG361B2: stale terminal settlement ticket ignored" }
	}
}

# Commit boundary 2: the terminal writer ran on the previous day.  Only this
# exact ticket may publish the immutable Workforce B2 source.
zg361b2.102 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_source_publish_owner
				exists = scope:zg361_b2_source_publish_subject
				this = scope:zg361_b2_source_publish_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_source_publish_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_source_publish_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_source_publish_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_source_publish_case
			}
			zg361_b2_publish_workforce_pip_settlement_effect = yes
		}
		else = { debug_log = "ZG361B2: stale Workforce source publication ticket ignored" }
	}
}

# Commit boundary 3: the source publisher has completed.  The first event
# offers the real source to probation; the second is one bounded, actually
# reachable replay over that same conserved source.  Neither republishes B2.
zg361b2.103 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_probation_handoff_owner
				exists = scope:zg361_b2_probation_handoff_subject
				this = scope:zg361_b2_probation_handoff_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_probation_handoff_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_probation_handoff_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_probation_handoff_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_probation_handoff_case
			}
			zg361_b2_replay_workforce_probation_fact_handoff_effect = yes
			var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_probation_replay_owner }
			save_scope_as = zg361_b2_probation_replay_subject
			save_scope_value_as = { name = zg361_b2_probation_replay_cycle value = var:zg361_b2_pip_cycle }
			save_scope_value_as = { name = zg361_b2_probation_replay_case value = var:zg361_b2_pip_case }
			trigger_event = { id = zg361b2.104 days = 1 }
		}
		else = { debug_log = "ZG361B2: stale probation handoff ticket ignored" }
	}
}

zg361b2.104 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_probation_replay_owner
				exists = scope:zg361_b2_probation_replay_subject
				this = scope:zg361_b2_probation_replay_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_probation_replay_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_probation_replay_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_probation_replay_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_probation_replay_case
			}
			zg361_b2_replay_workforce_probation_fact_handoff_effect = yes
		}
		else = { debug_log = "ZG361B2: stale probation handoff replay ignored" }
	}
}

# #017 bounded post-PIP disposition; any active appeal observation still passes
# through the common adverse-action gate in the four core disposition effects.
zg361b2.110 = {
	type = character_event
	theme = vassal
	title = zg361b2.110.t
	desc = zg361b2.110.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_disposition_owner
		exists = scope:zg361_b2_disposition_subject
		this = scope:zg361_b2_disposition_subject
		var:zg361_b2_pip_owner = scope:zg361_b2_disposition_owner
		var:zg361_b2_pip_subject = scope:zg361_b2_disposition_subject
		var:zg361_b2_pip_cycle = scope:zg361_b2_disposition_cycle
		var:zg361_b2_pip_case = scope:zg361_b2_disposition_case
		var:zg361_b2_m017_state = scope:zg361_b2_disposition_state
		var:zg361_b2_m017_state = 1
	}
	option = {
		name = zg361b2.110.a
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_extend_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = {
			set_variable = { name = zg361_b2_m017_state value = 3 }
			set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
			zg361_b2_m017_consume_business_object_effect = yes
		}
	}
	option = {
		name = zg361b2.110.b
		trigger = {
			OR = {
				var:zg361_b2_m017_expedited_evidence = var:zg361_b2_pip_case
				AND = {
					var:zg361_b2_m017_first_low_restricted = 0
					has_variable = zg361_streak_bottom
					var:zg361_streak_bottom >= 2
				}
			}
		}
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_demote_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = {
			set_variable = { name = zg361_b2_m017_state value = 3 }
			set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
			zg361_b2_m017_consume_business_object_effect = yes
		}
	}
	option = {
		name = zg361b2.110.c
		trigger = {
			var:zg361_b2_m017_first_low_restricted = 0
			has_variable = zg361_streak_bottom
			var:zg361_streak_bottom >= 3
		}
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_stepdown_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = {
			set_variable = { name = zg361_b2_m017_state value = 3 }
			set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
			zg361_b2_m017_consume_business_object_effect = yes
		}
	}
	option = {
		name = zg361b2.110.d
		trigger = {
			var:zg361_b2_m017_first_low_restricted = 0
			var:zg361_b2_m074_state = 1
			var:zg361_b2_m074_redundancy_eligible = 1
			OR = {
				var:zg361_b2_m074_route = 2
				var:zg361_b2_m074_owner = {
					government_has_flag = government_has_treasury
					treasury >= 50
				}
			}
		}
		zg361_b2_m074_accept_redundancy_effect = yes
		set_variable = { name = zg361_b2_m017_state value = 3 }
		set_variable = { name = zg361_b2_m017_disposition_receipt value = var:zg361_b2_pip_case }
		zg361_b2_m017_consume_business_object_effect = yes
	}
}

# #070 target-bound one-year anti-retaliation observation.
zg361b2.120 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_retaliation_deadline_owner
				exists = scope:zg361_b2_retaliation_deadline_subject
				this = scope:zg361_b2_retaliation_deadline_subject
				var:zg361_b2_retaliation_owner = scope:zg361_b2_retaliation_deadline_owner
				var:zg361_b2_retaliation_subject = scope:zg361_b2_retaliation_deadline_subject
				var:zg361_b2_retaliation_cycle = scope:zg361_b2_retaliation_deadline_cycle
				var:zg361_b2_retaliation_case = scope:zg361_b2_retaliation_deadline_case
				var:zg361_b2_retaliation_state = scope:zg361_b2_retaliation_deadline_state
				var:zg361_b2_retaliation_state = 1
			}
			set_variable = { name = zg361_b2_retaliation_state value = 4 }
			set_variable = { name = zg361_b2_m070_state value = 4 }
			set_variable = { name = zg361_b2_m070_observed_years value = 1 }
			zg361_b2_m070_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale retaliation D+365 ticket ignored" }
	}
}

# #072 a logged pre-delivery read receives one target-bound D+30 source finding.
zg361b2.121 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_leak_deadline_owner
				exists = scope:zg361_b2_leak_deadline_subject
				this = scope:zg361_b2_leak_deadline_subject
				var:zg361_b2_case_owner = scope:zg361_b2_leak_deadline_owner
				var:zg361_b2_case_subject = scope:zg361_b2_leak_deadline_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_leak_deadline_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_leak_deadline_case
				var:zg361_b2_m072_state = scope:zg361_b2_leak_deadline_state
				var:zg361_b2_m072_state = 2
				var:zg361_b2_m072_receipt_serial = var:zg361_b2_case_serial
			}
			set_variable = { name = zg361_b2_m072_state value = 3 }
			set_variable = { name = zg361_b2_m072_investigation_result value = 1 }
			set_variable = { name = zg361_b2_m072_source_finding value = var:zg361_b2_m072_source }
			var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			zg361_b2_m072_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale pre-delivery access D+30 ticket ignored" }
	}
}

# #359 player-manager quota return decision. Counts and barons can be the saved
# subject, but only an eligible celestial manager can ever receive this GUI.
zg361b2.130 = {
	type = character_event
	theme = realm
	title = zg361b2.130.t
	desc = zg361b2.130.desc
	trigger = {
		is_ai = no
		zg361_is_celestial_liege_trigger = yes
		exists = scope:zg361_b2_quota_return_owner
		exists = scope:zg361_b2_quota_return_subject
		this = scope:zg361_b2_quota_return_owner
		scope:zg361_b2_quota_return_subject = {
			var:zg361_b2_case_owner = scope:zg361_b2_quota_return_owner
			var:zg361_b2_case_subject = scope:zg361_b2_quota_return_subject
			var:zg361_b2_case_cycle = scope:zg361_b2_quota_return_cycle
			var:zg361_b2_case_serial = scope:zg361_b2_quota_return_case
			var:zg361_b2_m359_state = scope:zg361_b2_quota_return_state
			var:zg361_b2_m359_state = 1
			var:zg361_b2_m359_object_active = 1
			var:zg361_b2_m359_route = 1
		}
	}
	option = {
		name = zg361b2.130.a
		trigger = {
			scope:zg361_b2_quota_return_subject = {
				has_variable = zg361_pp_m157_packet_candidate
				has_variable = zg361_pp_m157_nomination_slot_owner
				has_variable = zg361_pp_m157_nomination_slot_cycle
				has_variable = zg361_pp_m157_nomination_slot_case
				has_variable = zg361_pp_m157_nomination_slot_amount
				has_variable = zg361_pp_m157_nomination_slot_status
				has_variable = zg361_case_u_owner
				has_variable = zg361_case_u_subject
				has_variable = zg361_case_u_cycle_serial
				has_variable = zg361_case_u_case_serial
				has_variable = zg361_case_u_state
				has_variable = zg361_case_u_revision
				has_variable = zg361_case_u_active
				var:zg361_case_u_active = 1
				has_variable = zg361_pp_u_nomination_slot_available
				has_variable = zg361_pp_u_nomination_slot_reserved
				has_variable = zg361_pp_u_nomination_slot_settled
				var:zg361_pp_m157_packet_candidate = this
				var:zg361_case_u_owner = scope:zg361_b2_quota_return_owner
				var:zg361_case_u_subject = this
				var:zg361_case_u_cycle_serial = var:zg361_b2_case_cycle
				var:zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner
				var:zg361_pp_m157_nomination_slot_cycle = var:zg361_case_u_cycle_serial
				var:zg361_pp_m157_nomination_slot_case = var:zg361_case_u_case_serial
				var:zg361_pp_m157_nomination_slot_amount = 1
				OR = {
					AND = {
						var:zg361_pp_m157_nomination_slot_status = 1
						var:zg361_pp_u_nomination_slot_reserved >= var:zg361_pp_m157_nomination_slot_amount
					}
					AND = {
						var:zg361_pp_m157_nomination_slot_status = 2
						var:zg361_pp_u_nomination_slot_settled >= var:zg361_pp_m157_nomination_slot_amount
					}
				}
			}
		}
		scope:zg361_b2_quota_return_subject = {
			zg361_b2_m359_return_pp_nomination_slot_effect = yes
			if = {
				limit = { NOT = { var:zg361_b2_m359_refund_applied = 1 } }
				zg361_b2_m359_post_next_cycle_debt_effect = yes
			}
		}
	}
	option = {
		name = zg361b2.130.b
		scope:zg361_b2_quota_return_subject = { zg361_b2_m359_open_boundary_review_effect = yes }
	}
	option = {
		name = zg361b2.130.c
		scope:zg361_b2_quota_return_subject = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

# #359 fresh boundary notice. Refusal freezes a distinct D+7 witness ticket.
zg361b2.131 = {
	type = character_event
	theme = vassal
	title = zg361b2.131.t
	desc = zg361b2.131.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_redelivery_prompt_owner
		exists = scope:zg361_b2_redelivery_prompt_subject
		this = scope:zg361_b2_redelivery_prompt_subject
		var:zg361_b2_redelivery_owner = scope:zg361_b2_redelivery_prompt_owner
		var:zg361_b2_redelivery_subject = scope:zg361_b2_redelivery_prompt_subject
		var:zg361_b2_redelivery_cycle = scope:zg361_b2_redelivery_prompt_cycle
		var:zg361_b2_redelivery_case = scope:zg361_b2_redelivery_prompt_case
		var:zg361_b2_redelivery_state = scope:zg361_b2_redelivery_prompt_state
		var:zg361_b2_redelivery_state = 1
	}
	option = {
		name = zg361b2.131.a
		set_variable = { name = zg361_b2_redelivery_method value = 1 }
		zg361_b2_deliver_boundary_notice_effect = yes
	}
	option = {
		name = zg361b2.131.b
		set_variable = { name = zg361_b2_redelivery_method value = 2 }
		set_variable = { name = zg361_result_objection_recorded value = 1 }
		zg361_b2_deliver_boundary_notice_effect = yes
		zg361_b2_contest_boundary_notice_effect = yes
	}
	option = {
		name = zg361b2.131.c
		set_variable = { name = zg361_b2_redelivery_state value = 2 }
		set_variable = { name = zg361_b2_redelivery_method value = 3 }
		var:zg361_b2_redelivery_owner = {
			if = {
				limit = { exists = liege liege = { is_alive = yes } }
				liege = { save_scope_as = zg361_b2_redelivery_witness }
			}
			else = { save_scope_as = zg361_b2_redelivery_witness }
		}
		set_variable = { name = zg361_b2_redelivery_witness_identity value = scope:zg361_b2_redelivery_witness }
		var:zg361_b2_redelivery_owner = { save_scope_as = zg361_b2_redelivery_witness_owner }
		save_scope_as = zg361_b2_redelivery_witness_subject
		save_scope_value_as = { name = zg361_b2_redelivery_witness_cycle value = var:zg361_b2_redelivery_cycle }
		save_scope_value_as = { name = zg361_b2_redelivery_witness_case value = var:zg361_b2_redelivery_case }
		save_scope_value_as = { name = zg361_b2_redelivery_witness_state value = var:zg361_b2_redelivery_state }
		trigger_event = { id = zg361b2.132 days = 7 }
	}
}

zg361b2.132 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_redelivery_witness_owner
				exists = scope:zg361_b2_redelivery_witness_subject
				exists = scope:zg361_b2_redelivery_witness
				this = scope:zg361_b2_redelivery_witness_subject
				var:zg361_b2_redelivery_owner = scope:zg361_b2_redelivery_witness_owner
				var:zg361_b2_redelivery_subject = scope:zg361_b2_redelivery_witness_subject
				var:zg361_b2_redelivery_cycle = scope:zg361_b2_redelivery_witness_cycle
				var:zg361_b2_redelivery_case = scope:zg361_b2_redelivery_witness_case
				var:zg361_b2_redelivery_state = scope:zg361_b2_redelivery_witness_state
				var:zg361_b2_redelivery_state = 2
				var:zg361_b2_redelivery_witness_identity = scope:zg361_b2_redelivery_witness
			}
			set_variable = { name = zg361_b2_redelivery_witness_receipt value = var:zg361_b2_redelivery_case }
			set_variable = { name = zg361_result_delivery_witness value = scope:zg361_b2_redelivery_witness }
			set_variable = { name = zg361_result_delivery_witness_receipt value = var:zg361_result_case_serial }
			zg361_b2_deliver_boundary_notice_effect = yes
		}
		else = { debug_log = "ZG361B2: stale boundary D+7 witness ticket ignored" }
	}
}

# #079 D+30 independent skip-level result.
zg361b2.140 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_skip_deadline_owner
				exists = scope:zg361_b2_skip_deadline_subject
				this = scope:zg361_b2_skip_deadline_subject
				var:zg361_b2_m079_reviewer = scope:zg361_b2_skip_deadline_owner
				var:zg361_b2_case_subject = scope:zg361_b2_skip_deadline_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_skip_deadline_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_skip_deadline_case
				var:zg361_b2_m079_state = scope:zg361_b2_skip_deadline_state
				var:zg361_b2_m079_state = 1
				var:zg361_b2_m079_object_active = 1
				var:zg361_b2_m079_receipt_serial = var:zg361_b2_case_serial
			}
			zg361_b2_m079_release_seat_effect = yes
			if = {
				limit = { var:zg361_b2_m071_evidence_strength >= 2 }
				set_variable = { name = zg361_b2_m079_state value = 3 }
				set_variable = { name = zg361_b2_m079_investigation_result value = 1 }
				set_variable = { name = zg361_b2_m079_manager_rework_required value = 1 }
				set_variable = { name = zg361_b2_m079_remand_owner value = var:zg361_b2_case_owner }
				set_variable = { name = zg361_b2_m079_remand_cycle value = var:zg361_b2_case_cycle }
				set_variable = { name = zg361_b2_m079_remand_case value = var:zg361_b2_case_serial }
				set_variable = { name = zg361_b2_m079_remand_active value = 1 }
				change_variable = { name = zg361_b2_case_feedback_revision add = 1 }
				set_variable = { name = zg361_b2_m079_evidence_revision value = var:zg361_b2_case_feedback_revision }
				# A skip-level reviewer can remand evidence, never write this
				# subject's pending/final grade or transfer a promised resource.
				set_variable = { name = zg361_b2_m079_no_direct_grade_write value = 1 }
				if = {
					limit = { var:zg361_b2_m079_route = 2 }
					set_variable = { name = zg361_b2_m079_unauthorized_promise_reversed value = 1 }
					var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
				}
			}
			else = {
				set_variable = { name = zg361_b2_m079_state value = 4 }
				set_variable = { name = zg361_b2_m079_investigation_result value = 2 }
			}
			set_variable = { name = zg361_b2_m079_outcome_receipt value = var:zg361_b2_case_serial }
			zg361_b2_m079_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale skip-level D+30 ticket ignored" }
	}
}

# #071 one public packet creates exactly one D+30 fact-check result.
zg361b2.141 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_factcheck_owner
				exists = scope:zg361_b2_factcheck_subject
				this = scope:zg361_b2_factcheck_subject
				var:zg361_b2_case_owner = scope:zg361_b2_factcheck_owner
				var:zg361_b2_case_subject = scope:zg361_b2_factcheck_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_factcheck_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_factcheck_case
				var:zg361_b2_m071_factcheck_state = scope:zg361_b2_factcheck_state
				var:zg361_b2_m071_factcheck_state = 1
			}
			if = {
				limit = { var:zg361_b2_m071_evidence_strength >= 2 }
				set_variable = { name = zg361_b2_m071_factcheck_state value = 3 }
				set_variable = { name = zg361_b2_m071_factcheck_outcome value = 1 }
				add_prestige = 25
			}
			else = {
				set_variable = { name = zg361_b2_m071_factcheck_state value = 4 }
				set_variable = { name = zg361_b2_m071_factcheck_outcome value = 2 }
				add_prestige = { value = 0 subtract = 25 }
			}
			zg361_b2_m071_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale public fact-check D+30 ticket ignored" }
	}
}

# #080 D+90 metric defect review writes a repair or an accepted-risk debt.
zg361b2.150 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_metric_deadline_owner
				exists = scope:zg361_b2_metric_deadline_subject
				this = scope:zg361_b2_metric_deadline_subject
				var:zg361_b2_m080_owner = scope:zg361_b2_metric_deadline_owner
				var:zg361_b2_m080_subject = scope:zg361_b2_metric_deadline_subject
				var:zg361_b2_m080_cycle = scope:zg361_b2_metric_deadline_cycle
				var:zg361_b2_m080_case = scope:zg361_b2_metric_deadline_case
				var:zg361_b2_m080_state = scope:zg361_b2_metric_deadline_state
				var:zg361_b2_m080_state = 1
				var:zg361_b2_m080_object_active = 1
				var:zg361_b2_m080_receipt_serial = var:zg361_b2_case_serial
			}
			if = {
				limit = { var:zg361_b2_m080_route = 2 }
				set_variable = { name = zg361_b2_m080_state value = 4 }
				set_variable = { name = zg361_b2_m080_suppressed value = 1 }
				set_variable = { name = zg361_b2_m080_evidence_preserved value = 1 }
				set_variable = { name = zg361_b2_m080_suppression_owner value = var:zg361_b2_m080_owner }
				var:zg361_b2_m080_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			}
			else_if = {
				limit = {
					var:zg361_b2_m080_route = 1
					OR = {
						var:zg361_b2_m073_protected = 1
						var:zg361_b2_case_owner = { has_variable = zg361_b2_fairness_anomaly_open }
					}
				}
				set_variable = { name = zg361_b2_m080_state value = 3 }
				set_variable = { name = zg361_b2_m080_metric_repaired value = 1 }
				change_variable = { name = zg361_b2_m080_metric_version add = 1 }
				set_variable = { name = zg361_b2_m080_subject_contribution value = 1 }
			}
			else = {
				set_variable = { name = zg361_b2_m080_state value = 4 }
				set_variable = { name = zg361_b2_m080_accepted_risk value = 1 }
				set_variable = { name = zg361_b2_m080_accepted_risk_reason value = 1 }
			}
			set_variable = { name = zg361_b2_m080_outcome_receipt value = var:zg361_b2_m080_defect_id }
			zg361_b2_m080_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale metric D+90 ticket ignored" }
	}
}

# #358 separately served new-fact action; refusal creates a D+7 witnessed
# delivery, while an objection holds execution through the D+90 review.
zg361b2.160 = {
	type = character_event
	theme = vassal
	title = zg361b2.160.t
	desc = zg361b2.160.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_separate_prompt_owner
		exists = scope:zg361_b2_separate_prompt_subject
		this = scope:zg361_b2_separate_prompt_subject
		var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_prompt_owner
		var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_prompt_subject
		var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_prompt_cycle
		var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_prompt_case
		var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_prompt_state
		var:zg361_b2_separate_notice_state = 1
	}
	option = {
		name = zg361b2.160.a
		set_variable = { name = zg361_b2_separate_delivery_method value = 1 }
		zg361_b2_deliver_separate_case_effect = yes
		zg361_b2_execute_pending_adverse_action_effect = yes
	}
	option = {
		name = zg361b2.160.b
		set_variable = { name = zg361_b2_separate_delivery_method value = 2 }
		set_variable = { name = zg361_b2_separate_objection value = 1 }
		zg361_b2_deliver_separate_case_effect = yes
	}
	option = {
		name = zg361b2.160.c
		set_variable = { name = zg361_b2_separate_notice_state value = 2 }
		set_variable = { name = zg361_b2_separate_delivery_method value = 3 }
		var:zg361_b2_separate_notice_owner = {
			if = {
				limit = { exists = liege liege = { is_alive = yes } }
				liege = { save_scope_as = zg361_b2_separate_witness }
			}
			else = { save_scope_as = zg361_b2_separate_witness }
		}
		set_variable = { name = zg361_b2_separate_witness_identity value = scope:zg361_b2_separate_witness }
		var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_witness_owner }
		save_scope_as = zg361_b2_separate_witness_subject
		save_scope_value_as = { name = zg361_b2_separate_witness_cycle value = var:zg361_b2_separate_notice_cycle }
		save_scope_value_as = { name = zg361_b2_separate_witness_case value = var:zg361_b2_separate_notice_case }
		save_scope_value_as = { name = zg361_b2_separate_witness_state value = var:zg361_b2_separate_notice_state }
		trigger_event = { id = zg361b2.161 days = 7 }
	}
}

zg361b2.161 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_separate_witness_owner
				exists = scope:zg361_b2_separate_witness_subject
				exists = scope:zg361_b2_separate_witness
				this = scope:zg361_b2_separate_witness_subject
				var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_witness_owner
				var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_witness_subject
				var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_witness_cycle
				var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_witness_case
				var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_witness_state
				var:zg361_b2_separate_notice_state = 2
				var:zg361_b2_separate_witness_identity = scope:zg361_b2_separate_witness
			}
			set_variable = { name = zg361_b2_separate_witness_receipt value = var:zg361_b2_separate_notice_case }
			zg361_b2_deliver_separate_case_effect = yes
			zg361_b2_execute_pending_adverse_action_effect = yes
		}
		else = { debug_log = "ZG361B2: stale separate-case D+7 witness ticket ignored" }
	}
}

zg361b2.162 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_separate_deadline_owner
				exists = scope:zg361_b2_separate_deadline_subject
				this = scope:zg361_b2_separate_deadline_subject
				var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_deadline_owner
				var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_deadline_subject
				var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_deadline_cycle
				var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_deadline_case
				var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_deadline_state
				var:zg361_b2_separate_notice_state = 3
			}
			set_variable = { name = zg361_b2_separate_appeal_open value = 0 }
			set_variable = { name = zg361_b2_separate_notice_state value = 4 }
			if = {
				limit = { has_variable = zg361_b2_separate_objection }
				set_variable = { name = zg361_b2_separate_review_outcome value = 2 }
				remove_variable = zg361_b2_pending_adverse_action
				if = {
					limit = { var:zg361_b2_m017_object_active = 1 var:zg361_b2_m017_state = 2 }
					set_variable = { name = zg361_b2_m017_state value = 4 }
					set_variable = { name = zg361_b2_m017_disposition_cancelled value = var:zg361_b2_pip_case }
					zg361_b2_m017_consume_business_object_effect = yes
				}
			}
			else = { set_variable = { name = zg361_b2_separate_review_outcome value = 1 } }
		}
		else = { debug_log = "ZG361B2: stale separate-case D+90 ticket ignored" }
	}
}

# #074 D+30 conservation audit: exit and HC release are accepted only beside
# the exact public-treasury debit and personal-gold credit.
zg361b2.171 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_redundancy_audit_owner
				exists = scope:zg361_b2_redundancy_audit_subject
				this = scope:zg361_b2_redundancy_audit_subject
				var:zg361_b2_m074_owner = scope:zg361_b2_redundancy_audit_owner
				var:zg361_b2_m074_subject = scope:zg361_b2_redundancy_audit_subject
				var:zg361_b2_m074_cycle = scope:zg361_b2_redundancy_audit_cycle
				var:zg361_b2_m074_case = scope:zg361_b2_redundancy_audit_case
				var:zg361_b2_m074_state = scope:zg361_b2_redundancy_audit_state
				var:zg361_b2_m074_state = 3
			}
			if = {
				limit = {
					var:zg361_b2_m074_treasury_paid = 50
					var:zg361_b2_m074_personal_received = 50
					var:zg361_b2_m074_actual_exit = 1
					var:zg361_b2_m074_hc_released = 1
				}
				set_variable = { name = zg361_b2_m074_state value = 4 }
				set_variable = { name = zg361_b2_m074_audit_receipt value = var:zg361_b2_m074_case }
			}
			else = {
				set_variable = { name = zg361_b2_m074_state value = 6 }
				set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
				var:zg361_b2_m074_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			}
			zg361_b2_m074_consume_business_object_effect = yes
		}
		else = { debug_log = "ZG361B2: stale redundancy D+30 audit ticket ignored" }
	}
}
''')


def render_english_localization() -> bytes:
    return localized(r'''
l_english:
 zg361b2.40.t:0 "A Measured Recovery Plan"
 zg361b2.40.desc:0 "The notice is settled. Its recovery plan now asks for one controllable task and records the support promised beside it. Refusal is evidence for a later review, not another punishment today."
 zg361b2.40.a:0 "Accept the plan and its support."
 zg361b2.40.b:0 "Revise the goal once, then begin."
 zg361b2.40.c:0 "Refuse, and let only the next cycle judge it."
 zg361b2.50.t:0 "After the Appeal"
 zg361b2.50.desc:0 "The ruling stands, yet the pattern behind it may deserve a wider record. You may publish the evidence, file a protected report, or leave a policy debt for another day."
 zg361b2.50.a:0 "Publish the bounded evidence packet."
 zg361b2.50.b:0 "File a protected anonymous report."
 zg361b2.50.c:0 "Defer escalation and record the debt."
 zg361b2.60.t:0 "A Neutral Departure"
 zg361b2.60.desc:0 "A voluntary exit is offered without changing the appeal ruling. If accepted, fifty from the public treasury becomes exactly fifty personal gold; an unfunded promise cannot be signed."
 zg361b2.60.a:0 "Accept the funded neutral exit."
 zg361b2.60.b:0 "Remain under the ordinary process."
 zg361b2.110.t:0 "PIP Disposition"
 zg361b2.110.desc:0 "The bounded recovery period has closed without graduation. Choose one recorded disposition; any live appeal safeguard still applies."
 zg361b2.110.a:0 "Extend support for one final cycle."
 zg361b2.110.b:0 "Demote, but retain the official."
 zg361b2.110.c:0 "Offer an orderly retirement."
 zg361b2.110.d:0 "Accept a funded, neutral redundancy exit."
 zg361b2.130.t:0 "Return the Corrected Quota"
 zg361b2.130.desc:0 "A corrected appeal releases one bottom-slot obligation. Consume a reserve, reopen the boundary with fresh notice and appeal, or post the obligation to the next real review."
 zg361b2.130.a:0 "Return the exact PP #157 nomination-slot receipt."
 zg361b2.130.b:0 "Reopen and re-serve the boundary case."
 zg361b2.130.c:0 "Post one slot to the next cycle."
 zg361b2.131.t:0 "Fresh Boundary Notice"
 zg361b2.131.desc:0 "A corrected case has moved the quota boundary. This is a new notice with its own receipt and ninety-day challenge window; it does not borrow the old appeal."
 zg361b2.131.a:0 "Acknowledge the new notice."
 zg361b2.131.b:0 "Acknowledge and contest it."
 zg361b2.131.c:0 "Refuse signature; require witnessed delivery."
 zg361b2.160.t:0 "Separate Misconduct Notice"
 zg361b2.160.desc:0 "A later fact cannot be folded into the appealed result. It arrives as a separate notice, with a separate receipt and its own challenge window."
 zg361b2.160.a:0 "Acknowledge the separate notice."
 zg361b2.160.b:0 "Acknowledge and object."
 zg361b2.160.c:0 "Refuse signature; require a witness."
 zg361b2.statement.prepared:0 "B2 case: prepared; detailed evidence remains locked before delivery."
 zg361b2.statement.delivered:0 "B2 case: delivered with a bounded receipt and appeal deadline."
 zg361b2.statement.appeal:0 "B2 appeal: target-bound review is active."
 zg361b2.statement.corrected:0 "B2 appeal: corrected; actual posted receipts were reversed once."
 zg361b2.statement.pip:0 "B2 recovery plan: active with a bounded support commitment."
 zg361b2.statement.retaliation:0 "B2 safeguard: one-year target-bound adverse-action observation is active."
''')


def render_simp_chinese_localization() -> bytes:
    return localized(r'''
l_simp_chinese:
 zg361b2.40.t:0 "有界改进计划"
 zg361b2.40.desc:0 "结果已经送达。改进计划只要求一项本人可控制的任务，并把上级承诺的支持一并记入案卷。拒绝只会成为下一轮证据，不会在今天再罚一次。"
 zg361b2.40.a:0 "接受计划及配套支持。"
 zg361b2.40.b:0 "修改一次目标，然后开始执行。"
 zg361b2.40.c:0 "拒绝，并只让下一轮评价此事。"
 zg361b2.50.t:0 "申诉之后"
 zg361b2.50.desc:0 "裁决已经作出，但背后的模式也许值得留下更广的记录。你可以公开有界证据、提交受保护报告，或把政策债留待以后处理。"
 zg361b2.50.a:0 "公开这份有界证据包。"
 zg361b2.50.b:0 "匿名提交受保护报告。"
 zg361b2.50.c:0 "暂不升级，但记下一笔政策债。"
 zg361b2.60.t:0 "中性离任"
 zg361b2.60.desc:0 "你可以在不改变申诉裁决的前提下自愿离任。若接受，地方国库的五十会精确转成个人五十金币；没有资金的承诺不能签字。"
 zg361b2.60.a:0 "接受已有资金保障的中性离任。"
 zg361b2.60.b:0 "留下，继续走普通程序。"
 zg361b2.110.t:0 "改进期处置"
 zg361b2.110.desc:0 "有界改进期结束，但尚未达成毕业条件。请选择一项留痕处置；仍在生效的申诉保护不会因此消失。"
 zg361b2.110.a:0 "再延长一个周期的支持。"
 zg361b2.110.b:0 "降岗留用。"
 zg361b2.110.c:0 "安排有序致仕。"
 zg361b2.110.d:0 "接受已有资金保障的中性裁撤离任。"
 zg361b2.130.t:0 "回流改判后的配额"
 zg361b2.130.desc:0 "一次申诉改判释放了一个末档义务。你可以消耗预留名额、重新划定边界并重新送达，或把义务记到下一次真实考核。"
 zg361b2.130.a:0 "按 PP #157 的原始回执退回这一格提名名额。"
 zg361b2.130.b:0 "重开边界案并重新送达。"
 zg361b2.130.c:0 "把一个名额记入下一周期。"
 zg361b2.131.t:0 "新的边界通知"
 zg361b2.131.desc:0 "申诉改判移动了配额边界。这是一份有独立收据和九十日异议窗口的新通知，不会借用旧申诉。"
 zg361b2.131.a:0 "签收新的通知。"
 zg361b2.131.b:0 "签收但提出异议。"
 zg361b2.131.c:0 "拒绝签字，要求见证送达。"
 zg361b2.160.t:0 "独立失当通知"
 zg361b2.160.desc:0 "后续新事实不能塞回正在申诉的结果。它必须作为独立通知送达，并拥有独立收据与异议窗口。"
 zg361b2.160.a:0 "签收独立通知。"
 zg361b2.160.b:0 "签收但提出异议。"
 zg361b2.160.c:0 "拒绝签字，要求见证。"
 zg361b2.statement.prepared:0 "B2 案卷：已准备；正式送达前，详细证据仍受访问控制。"
 zg361b2.statement.delivered:0 "B2 案卷：已送达，并冻结有界收据与申诉期限。"
 zg361b2.statement.appeal:0 "B2 申诉：绑定对象的复核正在进行。"
 zg361b2.statement.corrected:0 "B2 申诉：已改判；实际入账的扣款只反冲一次。"
 zg361b2.statement.pip:0 "B2 改进计划：执行中，并已记录有界支持承诺。"
 zg361b2.statement.retaliation:0 "B2 保护：为期一年的绑定对象不利行动观察正在生效。"
''')


def render_english_placeholder_localization(language: str) -> bytes:
    english = render_english_localization().decode("utf-8-sig")
    return localized(english.replace("l_english:", f"l_{language}:", 1))


def outputs() -> dict[Path, bytes]:
    validate_wired_scope()
    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    rendered = {
        effects_dir / filename: payload
        for filename, payload in render_effect_parts().items()
    }
    rendered.update({
        MOD_ROOT / "events" / "zg361_b2_runtime_events.txt": render_events(),
        MOD_ROOT / "localization" / "english" / "zg361_b2_l_english.yml": render_english_localization(),
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_b2_l_simp_chinese.yml": render_simp_chinese_localization(),
    })
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
            / f"zg361_b2_l_{language}.yml"
        ] = render_english_placeholder_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    legacy_effect_path = (
        MOD_ROOT / "common" / "scripted_effects" / LEGACY_EFFECT_FILENAME
    )
    if args.check:
        if stale or legacy_effect_path.exists():
            print("RED: stale B2 generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            if legacy_effect_path.exists():
                print(f"{legacy_effect_path.relative_to(MOD_ROOT)} (legacy monolith)")
            return 1
        print("GREEN: B2 generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    if legacy_effect_path.exists():
        legacy_effect_path.unlink()
    print(f"GREEN: generated {len(rendered)} B2 runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
