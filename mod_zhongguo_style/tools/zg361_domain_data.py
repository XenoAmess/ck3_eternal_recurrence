#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authoritative phase-two domain graphs and 361-item runtime-plan compiler.

This module is deliberately stricter than the legacy policy-card projection.
The cards remain configuration; this file binds every numbered mechanism to a
shared domain object, a legal lifecycle hook, a typed operation, an explicit
deadline contract, resource candidates, visible feedback, and executable
acceptance claims.  The resulting plan is not itself a CK3 implementation and
must never inflate ``domain_runtime`` readiness in the public manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Iterable

from zg361_mechanism_data import Mechanism


RUNTIME_PLAN_SCHEMA: Final[int] = 1
STALE_GUARD: Final[tuple[str, ...]] = (
    "owner",
    "subject",
    "cycle_serial",
    "case_serial",
    "expected_state",
)

PERMISSION_BOUNDARY: Final[dict[str, str]] = {
    "player_manager": "landed celestial duke-or-higher manager",
    "ai_manager": (
        "owner-authorized second AI exception: landed celestial duke-or-higher "
        "manager, background path only"
    ),
    "subject": "the assessed official bound to the frozen case",
    "count_baron": "subject-only; never a manager, calibrator, PIP owner, or allocator",
}


@dataclass(frozen=True)
class DomainSpec:
    code: str
    first_id: int
    last_id: int
    name_cn: str
    object_type: str
    phase: int
    operation_key: str
    states: tuple[str, ...]
    hooks: tuple[str, ...]
    resources: tuple[str, ...]
    invariant: str
    feedback_surface: str
    cleanup_rule: str
    owner_scope: str = "frozen_reviewing_manager"
    subject_scope: str = "frozen_assessed_official"

    @property
    def ids(self) -> range:
        return range(self.first_id, self.last_id + 1)

    @property
    def transitions(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(
            (self.states[index], self.states[index + 1], self.hooks[index])
            for index in range(len(self.states) - 1)
        )

    @property
    def terminal_states(self) -> tuple[str, ...]:
        return (self.states[-1],)

    def manifest_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "id_range": [self.first_id, self.last_id],
            "name_cn": self.name_cn,
            "object_type": self.object_type,
            "phase": self.phase,
            "operation_key": self.operation_key,
            "owner_scope": self.owner_scope,
            "subject_scope": self.subject_scope,
            "states": list(self.states),
            "entry_state": self.states[0],
            "terminal_states": list(self.terminal_states),
            "transitions": [
                {"from": old, "to": new, "hook": hook}
                for old, new, hook in self.transitions
            ],
            "resources": list(self.resources),
            "invariant": self.invariant,
            "feedback_surface": self.feedback_surface,
            "cleanup_rule": self.cleanup_rule,
            "permissions": dict(PERMISSION_BOUNDARY),
        }


def _domain(
    code: str,
    first_id: int,
    last_id: int,
    name_cn: str,
    object_type: str,
    phase: int,
    operation_key: str,
    states: str,
    hooks: str,
    resources: str,
    invariant: str,
    feedback_surface: str,
    cleanup_rule: str = "retain immutable closed case; clear only active scheduler handles",
) -> DomainSpec:
    return DomainSpec(
        code=code,
        first_id=first_id,
        last_id=last_id,
        name_cn=name_cn,
        object_type=object_type,
        phase=phase,
        operation_key=operation_key,
        states=tuple(states.split()),
        hooks=tuple(hooks.split()),
        resources=tuple(resources.split()) if resources else (),
        invariant=invariant,
        feedback_surface=feedback_surface,
        cleanup_rule=cleanup_rule,
    )


DOMAIN_SPECS: Final[tuple[DomainSpec, ...]] = (
    _domain("A", 1, 6, "目标、证据与评分", "review_case", 1, "apply_review_control", "case_open goals_locked midcycle_rebased evidence_frozen rated", "cycle_open targets_locked evidence_open evidence_frozen", "capacity_hours", "goal versions and frozen evidence never rewrite an older cycle; used hours equal booked hours", "review dossier and KPI evidence tab"),
    _domain("B", 7, 13, "互评与校准政治", "calibration_round", 1, "apply_calibration_control", "invited sealed evaluator_adjusted calibrated published", "peer_invites_open peer_feedback_sealed precalibration calibration_complete", "quota_slot review_weight", "review weights sum to the frozen denominator and rating swaps are quota-neutral", "calibration dashboard"),
    _domain("C", 14, 18, "申诉、PIP 与退出", "appeal_pip_case", 1, "apply_appeal_pip_control", "result_served case_open supported reviewed resolved", "result_delivered appeal_or_pip_opened pip_support_committed pip_check_due", "penalty_receipt pip_capacity treasury_gold personal_gold", "refunds never exceed settled receipts; PIP support and manager capacity balance", "appeal and PIP casebook"),
    _domain("D", 19, 25, "晋升包、薪酬与 HC", "career_allocation", 2, "apply_career_allocation", "eligible packet_open panel_complete resources_reserved settled", "evidence_frozen promotion_packet_open promotion_panel_complete career_resources_settled", "promotion_slot hc_slot treasury_gold personal_gold", "promotion, title, authority, cash and HC remain separately reserved and settled", "career and promotion panel"),
    _domain("E", 26, 31, "贡献、抢功与指标异化", "contribution_case", 3, "apply_contribution_control", "project_registered contribution_signed claim_open audited attributed", "project_registered contribution_signed claim_open contribution_audited", "contribution_share sponsor_credit", "signed contribution shares conserve the project total and audit reversals net to zero", "contribution timeline and credit arbitration"),
    _domain("F", 32, 36, "管理者与制度反馈", "manager_review", 1, "apply_manager_review", "snapshot_ready manager_scored reason_coded nine_boxed reported", "cycle_closed manager_score_due manager_reason_due nine_box_due", "manager_capacity", "manager ratings consume only the previous-cycle team snapshot and never recurse in-cycle", "manager reason panel and long report"),
    _domain("G", 37, 47, "强制分布配额工程", "quota_book", 1, "apply_quota_control", "cohort_draft cohort_locked quota_computed adjusted published", "cycle_open cohort_locked quota_computed calibration_complete", "quota_slot", "top, middle and bottom slots sum exactly to the locked cohort; debt has owner, sign and due cycle", "quota ledger and denominator panel"),
    _domain("H", 48, 53, "互评微观博弈", "peer_feedback_round", 1, "apply_peer_feedback_control", "invited submitted sealed audited applied", "peer_invites_open peer_feedback_submitted peer_feedback_sealed peer_feedback_audited", "peer_invite_slot capacity_hours", "invitation slots, reviewer hours and anonymous sample counts reconcile", "peer feedback summary"),
    _domain("I", 54, 61, "汇报与可见度", "report_packet", 3, "apply_report_packet_control", "result_ready packet_built signed routed resolved", "result_ready report_packet_built report_packet_signed report_packet_routed", "capacity_hours contribution_share", "reporting hours displace delivery capacity and signed attribution shares conserve the result", "report packet and visibility timeline"),
    _domain("J", 62, 68, "矩阵、换老板与重组", "matrix_handoff", 3, "apply_matrix_handoff", "contract_open weights_locked handoff_open dual_signed mapped", "matrix_contract_open matrix_weights_locked manager_handoff_open manager_handoff_signed", "manager_weight", "active manager weights sum to 100 percent and historical case ownership never drifts", "matrix handoff ledger"),
    _domain("K", 69, 81, "送达、申诉正义与裁员", "notice_justice_case", 1, "apply_notice_justice_control", "notice_prepared delivered appeal_open reviewed resolved observation_closed", "result_frozen result_delivered appeal_opened appeal_resolved anti_retaliation_due", "penalty_receipt appeal_slot", "service and review timelines are immutable; correction refunds only original receipts", "notice, appeal and anti-retaliation casebook"),
    _domain("L", 82, 91, "薪酬、奖金与长期激励", "compensation_award", 2, "apply_compensation_award", "formula_locked funds_reserved granted held settled", "result_frozen compensation_formula_locked compensation_funds_reserved compensation_granted", "treasury_gold personal_gold award_budget", "same-currency debits equal credits plus refunds; earmarked awards cannot bypass budget", "award statement and payment receipts"),
    _domain("M", 92, 97, "职级与双通道", "career_track", 2, "apply_career_track", "track_selected eligible calibrated changed reviewed", "career_track_selected career_eligibility_due career_calibration_due career_change_due", "promotion_slot", "career level, title, authority and pay are distinct records and consume explicit slots", "career track review"),
    _domain("N", 98, 105, "HC 生命周期", "hc_slot", 2, "apply_hc_lifecycle", "requested decided recruiting occupied closed", "hc_requested hc_decision_due hc_recruiting hc_occupied", "hc_slot treasury_gold", "authorized HC equals vacant plus reserved plus occupied plus frozen or reclaimed slots", "HC board"),
    _domain("O", 106, 113, "人才盘点与继任", "succession_plan", 2, "apply_succession_control", "role_identified pool_ready readiness_scored trialed resolved handed_off", "critical_role_identified candidate_pool_ready readiness_scored acting_trial_due succession_resolved", "succession_slot capacity_hours", "high-potential, critical-talent and successor evidence remain separate; each role has one readiness ledger", "succession ladder"),
    _domain("P", 114, 120, "内部流动与新人落地", "mobility_onboarding", 2, "apply_mobility_onboarding", "applied accepted release_due transferred protected quality_written_back", "mobility_applied mobility_accepted release_due transfer_complete protection_due", "transfer_slot capacity_hours", "one active transfer per person; old reviews persist and release may be delayed only once", "internal mobility and onboarding panel"),
    _domain("Q", 121, 128, "管理者绩效文化", "manager_certification", 2, "apply_manager_certification", "trial scorecard feedback successor_test resolved", "manager_trial_open manager_scorecard_due subordinate_feedback_due successor_test_due", "manager_capacity", "only eligible celestial duke-or-higher managers own cases; high KPI cannot erase retaliation or attrition", "manager certification panel"),
    _domain("R", 129, 134, "项目制与系统纠偏", "project_governance", 3, "apply_project_governance", "proposed routed executing reviewed resolved observed", "project_proposed project_routed project_execution_due project_review_due project_resolved", "project_slot capacity_hours", "one accountable owner per shared metric; stopping a project does not itself equal failure", "project card and postmortem"),
    _domain("S", 135, 145, "预校准与影子档位", "shadow_calibration", 1, "apply_shadow_calibration", "shadowed precalibrated anchors_frozen exception_open final_pending finalized", "pending_grades precalibration anchors_frozen calibration_exception_open calibration_complete", "quota_slot dissent_vote", "rounding, quota debt and reopened cases use symmetric add-and-return rules", "shadow-rating dashboard"),
    _domain("T", 146, 156, "反馈谈判与承诺债", "feedback_commitment", 1, "apply_feedback_commitment", "result_locked feedback_held receipt_recorded actions_open resolved", "result_frozen feedback_meeting_due feedback_receipt_due feedback_actions_open", "commitment_capacity capacity_hours", "every promise has owner, deadline, resource and breach debt; receipt never implies agreement", "feedback minutes and commitment timeline"),
    _domain("U", 157, 168, "晋升提名与预审", "promotion_nomination", 2, "apply_promotion_nomination", "eligible nominated slot_reserved prescreened resolved", "promotion_eligible nomination_open nomination_slot_reserved prescreen_due", "nomination_slot promotion_slot", "nomination slots conserve across self, manager and withdrawn packets", "promotion nomination queue"),
    _domain("V", 169, 180, "晋升答辩与评委政治", "promotion_panel", 2, "apply_promotion_panel", "panel_formed recused blind_reviewed defended voted resolved", "promotion_panel_formed panel_recusal_due blind_review_due defense_due panel_vote_due", "panel_vote capacity_hours", "votes, vetoes, recusal and defense time remain reproducible from the frozen panel", "promotion panel record"),
    _domain("W", 181, 191, "PIP 启动、毕业与复发", "pip_case", 2, "apply_pip_lifecycle", "triaged evidence_met acknowledged executing midpoint resolved", "pip_triaged pip_evidence_due pip_ack_due pip_execution_due pip_midpoint_due", "pip_capacity treasury_gold personal_gold exit_cost", "manager caseload, support budget, frozen goals and exit cost settle once", "PIP task and outcome page"),
    _domain("X", 192, 204, "值守、故障与救火", "incident_case", 3, "apply_incident_control", "on_call alerted classified commanded timeline_frozen reviewed actions_open resolved", "on_call_open incident_alerted incident_classified incident_commanded incident_timeline_frozen incident_review_due incident_actions_open", "capacity_hours treasury_gold personal_gold contribution_share", "on-call relief and pay reconcile; prevention and response credit cannot double count", "incident report"),
    _domain("Y", 205, 216, "技术债与维护劳动", "debt_item", 3, "apply_debt_control", "registered owned funded worked accepted closed", "debt_registered debt_owned debt_funded debt_work_due debt_acceptance_due", "debt_point treasury_gold capacity_hours", "ending debt equals opening plus additions and interest minus accepted repayment", "technical debt ledger"),
    _domain("Z", 217, 228, "中台、共享官署与内部开源", "platform_service", 3, "apply_platform_control", "proposed adopted migrating dual_running valued settled", "platform_proposed platform_adopted platform_migration_due platform_dual_run platform_value_due", "platform_cost_share treasury_gold contribution_share", "cost shares sum to total and founder, contributor and maintainer credit remain separate", "platform service page"),
    _domain("AA", 229, 241, "数据口径与实验", "metric_experiment", 3, "apply_metric_experiment", "defined reconciled preregistered running frozen interpreted closed", "metric_defined metric_reconciled experiment_preregistered experiment_running experiment_frozen experiment_interpreted", "sample_slot capacity_hours", "numerator, denominator, window and version remain immutable; guardrails and primary metrics settle separately", "metric dictionary and experiment report"),
    _domain("AB", 242, 253, "加班、会议与在线表演", "capacity_period", 3, "apply_capacity_control", "planned requested decided executed compensated normalized resolved", "capacity_planned capacity_request_open capacity_decided capacity_executed compensation_due capacity_normalized", "capacity_hours treasury_gold personal_gold", "hours equal output plus meetings plus learning plus on-call plus leave; compensation uses exactly one route", "workload board"),
    _domain("AC", 254, 265, "外包、派遣与借调", "external_contract", 3, "apply_external_contract", "requested typed sourced active delivered resolved handed_off", "external_need_open contract_type_locked supplier_selected contract_active delivery_due contract_resolved", "hc_slot treasury_gold capacity_hours", "formal and shadow HC stay separate; SLA liability and individual liability do not merge", "supplier and external workforce record"),
    _domain("AD", 266, 277, "招聘、面试与 Offer", "recruitment_funnel", 3, "apply_recruitment_control", "requested voted calibrated offered decided probation quality_written_back", "requisition_open interview_votes_due interview_calibration_due offer_due offer_decided probation_due", "hc_slot offer_budget capacity_hours", "HC and offer budget reserve before offer; interviewer judgement settles against later quality", "recruitment funnel"),
    _domain("AE", 278, 289, "薪酬透明与发放纪律", "pay_statement", 2, "apply_pay_statement", "payable due decided corrected appealed closed", "payable_generated pay_due pay_decision_due pay_correction_due pay_appeal_due", "treasury_gold personal_gold pay_receipt", "payable equals paid plus owed minus returned; every correction and backpay has one receipt", "personal pay statement"),
    _domain("AF", 290, 300, "长期激励与流动性", "lti_grant", 2, "apply_lti_control", "nominated granted cliff_reached vesting exit_classified settled", "lti_nominated lti_granted cliff_due vesting_due exit_classification_due", "lti_share treasury_gold", "granted shares equal unvested plus vested plus forfeited plus repurchased", "long-term incentive statement"),
    _domain("AG", 301, 311, "业务周期与重组折算", "reorg_case", 3, "apply_reorg_control", "frozen split quiet_period mapped normalized closed", "reorg_facts_frozen responsibility_split quiet_period_due old_case_mapping_due normalization_due", "manager_weight capacity_hours", "split weights, hours and goal totals conserve; strategy changes never rewrite old goals", "reorganization before-and-after ledger"),
    _domain("AH", 312, 322, "内部市场、离职与回流", "internal_market_case", 3, "apply_internal_market", "posted applied trialed release_decided moved alumni closed", "internal_role_posted confidential_application trial_due release_decision_due move_complete alumni_due", "mobility_slot treasury_gold", "one active market case per person; old performance persists and one counteroffer exhausts retention", "internal market and alumni record"),
    _domain("AI", 323, 333, "学习、训练与知识扩散", "learning_plan", 3, "apply_learning_control", "budgeted enrolled completed applied measured spread", "learning_budgeted learning_enrolled learning_complete application_due outcome_due", "treasury_gold capacity_hours", "learning budget and protected hours reconcile; certificates never directly buy a rating", "learning and knowledge-diffusion record"),
    _domain("AJ", 334, 344, "需求入口与交付价值", "demand_item", 3, "apply_delivery_control", "entered defined estimated in_wip changed delivered adopted valued", "demand_entered definition_locked estimate_locked wip_open change_requested delivery_due adoption_due", "wip_slot capacity_hours", "WIP limit holds and scope, time and quality changes carry explicit tax; launch, adoption and value settle separately", "demand and value board"),
    _domain("AK", 345, 354, "制度运营与审计", "policy_version", 1, "apply_policy_governance", "drafted piloted effective exception_audited measured migrated", "policy_drafted policy_piloted policy_effective policy_exception_due policy_measurement_due", "exception_slot capacity_hours", "exceptions expire automatically and old records map explicitly across policy versions", "policy health and audit page"),
    _domain("AL", 355, 361, "制度极限与终局", "constitution_case", 4, "apply_constitution_control", "facts_frozen quota_applied appeal_returned collective_action chartered reported", "multi_cycle_facts_frozen quota_applied appeal_quota_returned manager_collective_action constitution_chartered", "quota_slot appeal_slot manager_vote", "old cases never rewrite; successful appeals return quota and the charter changes future defaults only", "361 constitution and ten-year report"),
)


PROFILE_RESOURCES: Final[dict[str, tuple[str, ...]]] = {
    "assessment": ("capacity_hours",),
    "calibration": ("quota_slot", "review_weight", "dissent_vote"),
    "pip": ("pip_capacity", "treasury_gold", "personal_gold", "exit_cost"),
    "promotion": ("promotion_slot", "nomination_slot", "panel_vote"),
    "compensation": ("treasury_gold", "personal_gold", "award_budget", "pay_receipt"),
    "hc": ("hc_slot", "offer_budget"),
    "incident": ("capacity_hours", "contribution_share"),
    "technology": ("debt_point", "capacity_hours"),
    "platform": ("platform_cost_share", "contribution_share"),
    "data": ("sample_slot", "capacity_hours"),
    "workload": ("capacity_hours", "treasury_gold", "personal_gold"),
    "external": ("hc_slot", "treasury_gold", "capacity_hours"),
    "organization": ("manager_capacity", "manager_weight", "mobility_slot"),
    "learning": ("treasury_gold", "capacity_hours"),
    "delivery": ("wip_slot", "capacity_hours"),
    "governance": ("capacity_hours", "exception_slot", "appeal_slot"),
    "endgame": ("quota_slot", "appeal_slot", "manager_vote"),
}


def validate_domain_graphs(domains: Iterable[DomainSpec] = DOMAIN_SPECS) -> None:
    rows = tuple(domains)
    if len(rows) != 38:
        raise ValueError(f"domain graph must contain exactly 38 domains, got {len(rows)}")
    if len({row.code for row in rows}) != len(rows):
        raise ValueError("domain codes must be unique")
    covered: list[int] = []
    operation_keys: set[str] = set()
    for row in rows:
        if row.first_id > row.last_id:
            raise ValueError(f"domain {row.code} has a reversed id range")
        covered.extend(row.ids)
        if len(row.states) < 2 or len(row.hooks) != len(row.states) - 1:
            raise ValueError(f"domain {row.code} states/hooks do not form one graph")
        if len(set(row.states)) != len(row.states) or len(set(row.hooks)) != len(row.hooks):
            raise ValueError(f"domain {row.code} repeats a state or hook")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row.operation_key):
            raise ValueError(f"domain {row.code} has an unsafe operation key")
        if row.operation_key in operation_keys:
            raise ValueError(f"operation key {row.operation_key} is not domain-unique")
        operation_keys.add(row.operation_key)
        if not row.invariant or not row.feedback_surface or not row.cleanup_rule:
            raise ValueError(f"domain {row.code} lacks invariant/feedback/cleanup")
    if covered != list(range(1, 362)):
        raise ValueError("domain id ranges must cover exactly 001..361 without gaps")


def domain_for_id(
    mechanism_id: int,
    domains: Iterable[DomainSpec] = DOMAIN_SPECS,
) -> DomainSpec:
    for domain in domains:
        if mechanism_id in domain.ids:
            return domain
    raise KeyError(f"mechanism {mechanism_id:03d} has no domain")


def _transition_for(mechanism: Mechanism, domain: DomainSpec) -> tuple[str, str, str]:
    offset = mechanism.id - domain.first_id
    count = domain.last_id - domain.first_id + 1
    index = min((offset * len(domain.transitions)) // count, len(domain.transitions) - 1)
    return domain.transitions[index]


def _deadline(choice: str, mechanism: Mechanism) -> dict[str, object]:
    if choice != "c":
        return {
            "kind": "none",
            "reason": "the bound lifecycle hook completes this route synchronously",
        }
    days = {"P0": 30, "P1": 90, "P2": 180}[mechanism.priority]
    return {
        "kind": "scheduled_event",
        "days": days,
        "on_due": "audit_deferred_policy_debt",
        "stale_guard": list(STALE_GUARD),
    }


def _transactions(
    mechanism: Mechanism,
    domain: DomainSpec,
    choice: str,
) -> tuple[list[dict[str, object]], str | None]:
    candidates = tuple(
        resource
        for resource in PROFILE_RESOURCES[mechanism.profile]
        if resource in domain.resources
    )
    if choice == "c":
        return [], "defer records policy debt but reserves or settles no domain resource"
    if not candidates:
        return [], "this route changes the bound case and feedback only; no conserved resource applies"

    # Compensation is intentionally dual-entry: organizational treasury and
    # the assessed official's personal pay are separate accounts.  Other
    # profiles use the first applicable conserved resource for this operation;
    # the domain invariant still governs every resource in the shared object.
    selected = candidates
    if mechanism.profile != "compensation":
        selected = candidates[:1]
    timing = "reserve_before_operation" if choice == "a" else "settle_at_operation"
    credit_suffix = "reserved" if choice == "a" else "consumed"
    transactions = []
    for currency in selected:
        transactions.append(
            {
                "debit_account": f"{domain.code.lower()}_{currency}_available",
                "credit_account": f"{domain.code.lower()}_{currency}_{credit_suffix}",
                "currency": currency,
                "amount": {
                    "kind": "bounded_parameter",
                    "key": f"mechanism_{mechanism.id:03d}_{choice}_{currency}_amount",
                    "minimum": 0,
                },
                "timing": timing,
                "receipt_key": f"zg361_rt_{mechanism.id:03d}_{choice}_{currency}",
                "refund_policy": "refund_unsettled_reservation_or_reverse_exact_receipt",
            }
        )
    return transactions, None


def build_runtime_plans(
    mechanisms: Iterable[Mechanism],
    domains: Iterable[DomainSpec] = DOMAIN_SPECS,
) -> list[dict[str, object]]:
    mechanism_rows = tuple(mechanisms)
    domain_rows = tuple(domains)
    plans: list[dict[str, object]] = []
    signature_owner: dict[tuple[object, ...], int] = {}
    for mechanism in mechanism_rows:
        domain = domain_for_id(mechanism.id, domain_rows)
        if mechanism.group_code != domain.code:
            raise ValueError(
                f"mechanism {mechanism.id:03d} group {mechanism.group_code} != domain {domain.code}"
            )
        old_state, new_state, hook = _transition_for(mechanism, domain)
        choices: dict[str, object] = {}
        for choice, mode in (("a", "evidence_led"), ("b", "expedient"), ("c", "deferred")):
            transactions, no_resource_reason = _transactions(
                mechanism, domain, choice
            )
            feedback = list(
                dict.fromkeys(
                    (
                        domain.feedback_surface,
                        *mechanism.acceptance_contract.visible_feedback,
                    )
                )
            )
            acceptance: dict[str, object] = {
                "pre_state": old_state,
                "action": f"{domain.operation_key}:{mode}:{mechanism.acceptance_contract.semantic_family}",
                "post_state": new_state,
                "resource_invariant": domain.invariant,
                "stale_negative": (
                    "owner, subject, cycle_serial, case_serial or expected_state mismatch must no-op"
                ),
                "idempotence_negative": "the same receipt/action serial may mutate the case at most once",
                "visible_feedback": feedback,
            }
            if no_resource_reason is not None:
                acceptance["no_conserved_resource_reason"] = no_resource_reason
            choices[choice] = {
                "parameters": {
                    "mode": mode,
                    "semantic_family": mechanism.acceptance_contract.semantic_family,
                    "priority": mechanism.priority,
                },
                "allowed_from_states": [old_state],
                "to_state": new_state,
                "deadline": _deadline(choice, mechanism),
                "transactions": transactions,
                "gameplay_effects": [
                    {
                        "op": domain.operation_key,
                        "variant": mechanism.acceptance_contract.semantic_family,
                        "mode": mode,
                    }
                ],
                "visible_feedback": feedback,
                "ai_score_terms": [
                    {"profile": mechanism.profile, "route": choice},
                    {"respect_permission_boundary": True},
                ],
                "acceptance": acceptance,
            }
        plan: dict[str, object] = {
            "id": mechanism.id,
            "domain": domain.code,
            "operation_key": domain.operation_key,
            "semantic_family": mechanism.acceptance_contract.semantic_family,
            "actor_role": "eligible_manager",
            "object_type": domain.object_type,
            "owner_scope": domain.owner_scope,
            "subject_scope": domain.subject_scope,
            "cycle_scope": "review_cycle_serial",
            "case_scope": f"{domain.object_type}_serial",
            "trigger_hook": hook,
            "applicability": [
                "landed",
                "celestial_government",
                "duke_or_higher_manager",
                "direct_assessed_subject",
            ],
            "prerequisites": list(mechanism.acceptance_contract.required_state),
            "conflicts": [],
            "choices": choices,
            "acceptance_contract": mechanism.acceptance_contract.manifest_payload(),
            "implementation_state": "runtime-contract-complete; ck3-domain-runtime-not-yet-claimed",
        }
        signature = (
            domain.code,
            domain.operation_key,
            plan["semantic_family"],
            hook,
            old_state,
            new_state,
            tuple(domain.resources),
            tuple(mechanism.acceptance_contract.visible_feedback),
        )
        if signature in signature_owner:
            plan["alias_of"] = signature_owner[signature]
        else:
            signature_owner[signature] = mechanism.id
        plans.append(plan)
    validate_runtime_coverage(mechanism_rows, domain_rows, plans)
    return plans


def validate_runtime_coverage(
    mechanisms: Iterable[Mechanism],
    domains: Iterable[DomainSpec],
    plans: Iterable[dict[str, object]],
) -> None:
    mechanism_rows = tuple(mechanisms)
    domain_rows = tuple(domains)
    plan_rows = tuple(plans)
    validate_domain_graphs(domain_rows)
    if [row.id for row in mechanism_rows] != list(range(1, 362)):
        raise ValueError("runtime planning requires the exact 001..361 mechanism catalogue")
    if [int(row["id"]) for row in plan_rows] != list(range(1, 362)):
        raise ValueError("runtime plans must cover exactly 001..361")
    operation_keys = {domain.operation_key for domain in domain_rows}
    by_id = {int(row["id"]): row for row in plan_rows}
    for mechanism in mechanism_rows:
        row = by_id[mechanism.id]
        domain = domain_for_id(mechanism.id, domain_rows)
        if row["domain"] != domain.code or row["object_type"] != domain.object_type:
            raise ValueError(f"runtime plan {mechanism.id:03d} is bound to the wrong domain")
        if row["operation_key"] not in operation_keys:
            raise ValueError(f"runtime plan {mechanism.id:03d} uses a non-whitelisted operation")
        if row["actor_role"] != "eligible_manager":
            raise ValueError(f"runtime plan {mechanism.id:03d} widens the actor boundary")
        choices = row["choices"]
        if not isinstance(choices, dict) or tuple(choices) != ("a", "b", "c"):
            raise ValueError(f"runtime plan {mechanism.id:03d} lacks A/B/C routes")
        legal = {(old, new, hook) for old, new, hook in domain.transitions}
        for choice_name, raw_choice in choices.items():
            if not isinstance(raw_choice, dict):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} is not an object")
            old_states = raw_choice.get("allowed_from_states")
            if not isinstance(old_states, list) or len(old_states) != 1:
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} lacks one source state")
            transition = (old_states[0], raw_choice.get("to_state"), row["trigger_hook"])
            if transition not in legal:
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} uses an illegal transition")
            effects = raw_choice.get("gameplay_effects")
            if not isinstance(effects, list) or not effects:
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} lacks a typed operation")
            if any(effect.get("op") not in operation_keys for effect in effects):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} bypasses the operation whitelist")
            if not raw_choice.get("visible_feedback"):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} lacks visible feedback")
            deadline = raw_choice.get("deadline")
            if not isinstance(deadline, dict) or deadline.get("kind") not in {"none", "scheduled_event"}:
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} has an invalid deadline")
            if deadline["kind"] == "scheduled_event" and tuple(deadline.get("stale_guard", ())) != STALE_GUARD:
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} has an incomplete stale guard")
            transactions = raw_choice.get("transactions")
            if not isinstance(transactions, list):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} transactions must be a list")
            acceptance = raw_choice.get("acceptance")
            if not isinstance(acceptance, dict):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} lacks acceptance")
            required_acceptance = {
                "pre_state",
                "action",
                "post_state",
                "resource_invariant",
                "stale_negative",
                "idempotence_negative",
                "visible_feedback",
            }
            if not required_acceptance.issubset(acceptance):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} acceptance is incomplete")
            if not transactions and not acceptance.get("no_conserved_resource_reason"):
                raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} hides an empty transaction list")
            for transaction in transactions:
                required_transaction = {
                    "debit_account",
                    "credit_account",
                    "currency",
                    "amount",
                    "timing",
                    "receipt_key",
                    "refund_policy",
                }
                if set(transaction) != required_transaction:
                    raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} transaction is incomplete")
                if transaction["currency"] not in domain.resources:
                    raise ValueError(f"runtime plan {mechanism.id:03d}/{choice_name} uses a foreign resource")
        alias = row.get("alias_of")
        if alias is not None and (not isinstance(alias, int) or alias >= mechanism.id):
            raise ValueError(f"runtime plan {mechanism.id:03d} has an invalid alias target")


validate_domain_graphs()
