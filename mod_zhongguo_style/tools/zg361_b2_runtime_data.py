#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executable, CK3-independent reference kernel for the ZhongGuo B2 batch.

The binding table freezes the exact forty new B2 mechanisms plus the two
existing interfaces (018/069) that B2 must eventually close.  The state
machines below model the hard invariants shared by those mechanisms:

* direct acknowledgement or objection, refusal, and D+7 witnessed service;
* a target-bound appeal clock and idempotent penalty/refund receipts;
* appeal non-aggravation, anti-retaliation observation, and quota return;
* feedback receipt/commitment semantics; and
* PIP support, midpoint, graduation, relapse, transfer, and exit.

This file is a deterministic Python reference model only.  It does not render
Paradox script, does not claim that any numbered mechanism exists in CK3, and
must not change ``domain_runtime`` or ``player_visible_loop`` readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Final, Iterable, Mapping


REFERENCE_ONLY: Final = True
CK3_IMPLEMENTED: Final = False
READINESS_CHANGE: Final = "none"
RUNTIME_EVIDENCE: Final = "python-reference-only"
WITNESS_DELAY_DAYS: Final = 7
APPEAL_WINDOW_DAYS: Final = 90
RETALIATION_WINDOW_DAYS: Final = 365
STALE_GUARD: Final[tuple[str, ...]] = (
    "owner",
    "subject",
    "cycle_serial",
    "case_serial",
    "expected_state",
)

B2_NEW_IDS: Final[tuple[int, ...]] = (
    tuple(range(14, 18))
    + tuple(range(70, 82))
    + tuple(range(146, 157))
    + tuple(range(181, 192))
    + (358, 359)
)
B2_INTERFACE_IDS: Final[tuple[int, ...]] = (18, 69)
B2_IDS: Final[tuple[int, ...]] = (
    tuple(range(14, 19))
    + tuple(range(69, 82))
    + tuple(range(146, 157))
    + tuple(range(181, 192))
    + (358, 359)
)


class PolicyRoute(str, Enum):
    A = "a"
    B = "b"
    C = "c"


@dataclass(frozen=True)
class RouteContract:
    route: PolicyRoute
    mode: str
    operation: str
    from_state: str
    to_state: str
    meaningful_write: str
    mutates_business_case: bool
    defer_days: int = 0


@dataclass(frozen=True)
class DeadlineContract:
    kind: str
    anchor: str
    days: int
    target_binding: str
    expected_state: str
    stale_guard: tuple[str, ...] = STALE_GUARD


@dataclass(frozen=True)
class TransactionContract:
    resources: tuple[str, ...]
    conservation: str
    no_transfer_reason: str = ""


@dataclass(frozen=True)
class ReceiptContract:
    keys: tuple[str, ...]
    uniqueness_scope: tuple[str, ...]
    replay: str
    refund_rule: str


@dataclass(frozen=True)
class DomainBinding:
    object_type: str
    operation_key: str
    owner_binding: str
    subject_binding: str
    cycle_binding: str
    case_binding: str
    state_binding: str


@dataclass(frozen=True)
class B2Binding:
    mechanism_id: int
    title: str
    domain: str
    object_type: str
    operation_key: str
    owner_binding: str
    subject_binding: str
    cycle_binding: str
    case_binding: str
    state_binding: str
    hook: str
    from_state: str
    to_state: str
    meaningful_write: str
    consumer: str
    routes: tuple[RouteContract, ...]
    deadlines: tuple[DeadlineContract, ...]
    transaction: TransactionContract
    receipt: ReceiptContract
    feedback: tuple[str, ...]
    batch_role: str
    runtime_evidence: str = RUNTIME_EVIDENCE
    readiness_change: str = READINESS_CHANGE


_DOMAINS: Final[dict[str, DomainBinding]] = {
    "C": DomainBinding(
        "appeal_pip_case",
        "apply_appeal_pip_control",
        "frozen_reviewing_manager",
        "frozen_assessed_official",
        "review_cycle_serial",
        "appeal_pip_case_serial",
        "appeal_pip_case_state",
    ),
    "K": DomainBinding(
        "notice_justice_case",
        "apply_notice_justice_control",
        "frozen_reviewing_manager",
        "frozen_assessed_official",
        "review_cycle_serial",
        "notice_justice_case_serial",
        "notice_justice_case_state",
    ),
    "T": DomainBinding(
        "feedback_commitment",
        "apply_feedback_commitment",
        "frozen_reviewing_manager",
        "frozen_assessed_official",
        "review_cycle_serial",
        "feedback_commitment_serial",
        "feedback_commitment_state",
    ),
    "W": DomainBinding(
        "pip_case",
        "apply_pip_lifecycle",
        "frozen_reviewing_manager",
        "frozen_assessed_official",
        "review_cycle_serial",
        "pip_case_serial",
        "pip_case_state",
    ),
    "AL": DomainBinding(
        "constitution_case",
        "apply_constitution_control",
        "frozen_reviewing_manager",
        "frozen_assessed_official",
        "review_cycle_serial",
        "constitution_case_serial",
        "constitution_case_state",
    ),
}


def _deadline(
    kind: str,
    anchor: str,
    days: int,
    expected_state: str,
    target_binding: str = "frozen_assessed_official",
) -> DeadlineContract:
    return DeadlineContract(kind, anchor, days, target_binding, expected_state)


def _routes(
    domain: DomainBinding,
    old: str,
    new: str,
    a_write: str,
    b_write: str,
    c_days: int,
) -> tuple[RouteContract, ...]:
    return (
        RouteContract(
            PolicyRoute.A,
            "evidence_led",
            domain.operation_key,
            old,
            new,
            a_write,
            True,
        ),
        RouteContract(
            PolicyRoute.B,
            "expedient",
            domain.operation_key,
            old,
            new,
            b_write,
            True,
        ),
        RouteContract(
            PolicyRoute.C,
            "deferred",
            "policy.defer",
            old,
            old,
            "leave the bound business case unchanged and post one policy-debt receipt",
            False,
            c_days,
        ),
    )


def _b(
    mechanism_id: int,
    title: str,
    domain_code: str,
    hook: str,
    old: str,
    new: str,
    meaningful_write: str,
    consumer: str,
    a_write: str,
    b_write: str,
    c_days: int,
    deadlines: tuple[DeadlineContract, ...],
    resources: tuple[str, ...],
    conservation: str,
    feedback: tuple[str, ...],
    no_transfer_reason: str = "",
) -> B2Binding:
    domain = _DOMAINS[domain_code]
    return B2Binding(
        mechanism_id=mechanism_id,
        title=title,
        domain=domain_code,
        object_type=domain.object_type,
        operation_key=domain.operation_key,
        owner_binding=domain.owner_binding,
        subject_binding=domain.subject_binding,
        cycle_binding=domain.cycle_binding,
        case_binding=domain.case_binding,
        state_binding=domain.state_binding,
        hook=hook,
        from_state=old,
        to_state=new,
        meaningful_write=meaningful_write,
        consumer=consumer,
        routes=_routes(domain, old, new, a_write, b_write, c_days),
        deadlines=deadlines,
        transaction=TransactionContract(resources, conservation, no_transfer_reason),
        receipt=ReceiptContract(
            keys=tuple(
                f"zg361_b2_m{mechanism_id:03d}_{route.value}_receipt_serial"
                for route in PolicyRoute
            ),
            uniqueness_scope=STALE_GUARD[:-1],
            replay="same identity, route and operation receipt is a no-op",
            refund_rule="refund is bounded by the settled source receipt and posts once",
        ),
        feedback=feedback,
        batch_role=(
            "interface-only"
            if mechanism_id in B2_INTERFACE_IDS
            else "new-mechanism"
        ),
    )


_SYNC = lambda hook, state: (_deadline("hook_sync", hook, 0, state),)

B2_BINDINGS: Final[tuple[B2Binding, ...]] = (
    _b(14, "绩效申诉案卷", "C", "result_delivered", "result_served", "case_open",
       "reason-coded appeal, frozen evidence, reviewer and correction receipt", "appeal casebook and corrected scoreboard",
       "open independent two-stage review and correct only from matched receipts", "record owner fast-review outcome and procedural-conflict risk", 30,
       (_deadline("appeal_filing", "delivered_day", 90, "case_open"),), ("penalty_receipt", "treasury_gold", "personal_gold", "merit"),
       "each refund is <= its matched settled receipt", ("appeal reason/evidence timeline", "itemized correction statement", "scoreboard diff")),
    _b(15, "PIP 改进任务书", "C", "result_delivered", "result_served", "case_open",
       "controllable task, milestone, response and exactly-one terminal outcome", "PIP task page and next-cycle evidence",
       "open one negotiable task with measurable milestones", "record one refusal reason without duplicating the original sanction", 30,
       (_deadline("pip_completion", "pip_start_day", 365, "case_open"),), ("pip_capacity",),
       "one active case consumes one bounded manager-capacity reservation", ("task and milestone sheet", "success/failure/timeout/refusal outcome")),
    _b(16, "PIP 支持预算与“只给指标不给资源”", "C", "appeal_or_pip_opened", "case_open", "supported",
       "support package, mentor, hours, budget owner and no-support liability", "PIP support panel and manager next-cycle reason",
       "reserve funded support with a frozen completion cap", "leave budget unchanged and post no-support liability only on failure", 90,
       (_deadline("support_expiry", "pip_deadline", 0, "supported"),), ("pip_capacity", "treasury_gold"),
       "opening support = reserved + remaining + recovered; debits equal posted support receipts", ("support package and balance", "no-support appeal reason")),
    _b(17, "末位处置阶梯", "C", "pip_support_committed", "supported", "reviewed",
       "streak level, legal disposition, vacancy/replacement and one terminal result", "disposition panel and later personnel state",
       "advance only through the evidence-backed staged ladder", "attempt the aggressive legal route and no-op when native legality fails", 30,
       (_deadline("disposition_review", "pip_deadline", 0, "reviewed"),), ("pip_capacity", "exit_cost"),
       "one case has one terminal disposition and releases each reservation once", ("legal options and reasons", "unique disposition outcome")),
    _b(18, "个人告身与四重后果清算单", "C", "pip_check_due", "reviewed", "resolved",
       "frozen result statement and itemized treasury/gold/merit/salary/PIP status", "reopenable personal settlement statement",
       "project the immutable detailed statement from actual receipts", "project one compact statement and expose snapshot-risk markers", 30,
       (_deadline("salary_modifier_expiry", "delivered_day", 365, "resolved"),), ("treasury_gold", "personal_gold", "merit", "penalty_receipt"),
       "actual penalties settle once; refunds never exceed actual paid amounts", ("frozen KPI/rank/owner/reason", "paid/refunded/withholding rows")),

    _b(69, "正式送达与申诉时钟", "K", "result_frozen", "notice_prepared", "delivered",
       "delivery method/day/witness and target-bound appeal deadline", "notice and appeal timeline",
       "deliver directly or by D+7 witness and start the same appeal window", "record aggregate-publication shortcut and its procedural liability", 30,
       (_deadline("witness_service", "refusal_day", 7, "REFUSED_PENDING_WITNESS"), _deadline("appeal_expiry", "delivered_day", 90, "APPEAL_OPEN")),
       ("penalty_receipt", "appeal_slot"), "no consequence settles before delivery; each settles once afterward",
       ("receipt/objection/refusal status", "witness identity", "appeal days remaining")),
    _b(70, "申诉后的反报复观察期", "K", "result_frozen", "notice_prepared", "delivered",
       "appeal-bound observation, adverse actions, post-appeal facts and independent findings", "anti-retaliation observation page",
       "open one-year observation and suspend unsupported adverse action for review", "record immediate adverse action and escalating review risk", 90,
       (_deadline("anti_retaliation_close", "appeal_filed_day", 365, "OBSERVATION_OPEN"),), ("appeal_slot",),
       "each action and independent finding posts once", ("observation dates", "new-fact comparison", "retaliation/normal finding")),
    _b(71, "内部论坛长文与公开升级", "K", "result_frozen", "notice_prepared", "delivered",
       "exhaustion status, publication identity, evidence hash, fact-check and reputation effects", "escalation and fact-check case",
       "allow evidence-bound escalation only after private and formal routes close", "publish immediately with symmetric reputation and trust cost", 180,
       (_deadline("public_claim_factcheck", "published_day", 30, "delivered"),), ("appeal_slot",),
       "one escalation creates at most one fact-check case", ("exhausted-route status", "fact versus emotion projection", "reputation effects")),
    _b(72, "提前泄露绩效档位", "K", "result_delivered", "delivered", "appeal_open",
       "authorized access log, leak source/recipient/day and investigation result", "access audit and leak investigation",
       "enforce uniform-delivery ACL and log every pre-delivery read", "grant the recipient a measured head start and trace only the actual source", 90,
       (_deadline("leak_investigation", "leak_day", 30, "appeal_open"),), ("appeal_slot",),
       "access logs are append-only and a leak benefit applies only to its recipient", ("pre-delivery access log", "head-start days", "source finding")),
    _b(73, "恶意泄密与善意吹哨分流", "K", "result_delivered", "delivered", "appeal_open",
       "material hash, provenance, truth/public-interest/malice findings and protection", "whistleblower triage and audit",
       "protect verified public-interest evidence and open one targeted audit", "punish all leaks while preserving the suppressed genuine lead", 90,
       (_deadline("whistleblower_audit", "report_day", 90, "appeal_open"),), ("appeal_slot",),
       "one verified report opens one audit; punishment binds actual malicious conduct", ("truth/public-interest/malice split", "protection or specific falsification")),
    _b(74, "诚实裁撤与“洗成绩裁人”", "K", "result_delivered", "delivered", "appeal_open",
       "organizational redundancy reason, neutral record, compensation, actual exit and HC release", "redundancy statement and responsibility case",
       "pay a transparent package only on actual organizational exit", "record disguised-performance exit and preserve reversal liability", 90,
       (_deadline("redundancy_payment", "exit_effective_day", 30, "appeal_open"),), ("treasury_gold", "personal_gold", "hc_slot"),
       "payer treasury decrease equals recipient gold increase; HC releases after exit only", ("organization-versus-performance reason", "payment and HC receipt", "reversal liability")),
    _b(75, "保履历自愿离开包", "K", "appeal_opened", "appeal_open", "reviewed",
       "offer amount/deadline, free acceptance or refusal, actual exit, neutral record and HC", "voluntary-exit offer and result",
       "settle a freely accepted written package on actual exit", "record coercive no-compensation threat and reclassification debt", 180,
       (_deadline("exit_offer_expiry", "offer_day", 30, "reviewed"),), ("treasury_gold", "personal_gold", "hc_slot"),
       "acceptance transfers equal gold once; refusal changes no balance, record or HC", ("offer and refusal path", "payment/exit/HC status", "coercion reclassification")),
    _b(76, "程序失败的多级责任", "K", "appeal_opened", "appeal_open", "reviewed",
       "evidence-backed responsibility shares totaling 100 and next-cycle manager reasons", "liability allocation and reassessment order",
       "allocate non-overlapping multi-level responsibility and return rating to lawful owner", "close on one responsible party while retaining unresolved systemic defects", 90,
       (_deadline("liability_writeback", "appeal_resolved_day", 365, "reviewed"),), ("appeal_slot",),
       "non-zero responsibility shares sum exactly to 100 without duplicate attribution", ("responsibility table", "next-cycle reason links", "lawful reassessment owner")),
    _b(77, "独立复核人轮换", "K", "appeal_resolved", "reviewed", "resolved",
       "eligible reviewer, conflict checks, one recusal token per side and quality history", "independent-review panel",
       "select a conflict-free reviewer with bounded for-cause recusals", "let the original panel self-correct and expose lower credibility", 90,
       (_deadline("independent_review", "review_assigned_day", 90, "resolved"),), ("appeal_slot",),
       "each side consumes at most one successful recusal token; conclusion posts once", ("reviewer conflict matrix", "recusal token status", "independence/quality result")),
    _b(78, "分布公平性仪表盘", "K", "appeal_resolved", "reviewed", "resolved",
       "group numerators/denominators, sample threshold and one explanation/opportunity audit", "fairness dashboard",
       "flag stable anomalies for one human explanation without changing grades", "auto-adjust while preserving original band and an appeal route", 180,
       (_deadline("fairness_explanation", "anomaly_day", 90, "resolved"),), (),
       "visible group counts reconcile to included subjects", ("count/denominator/percentage", "small-sample warning", "audit task"),
       "aggregation and audit create no conserved-resource transfer"),
    _b(79, "隔级接待日", "K", "appeal_resolved", "reviewed", "resolved",
       "two-seat booking, issue evidence and lawful-chain investigation task", "skip-level office-hours panel",
       "reserve at most two seats and open evidence-bound investigation only", "record a pending promise and audit any direct grand-subject override", 180,
       (_deadline("office_hours_cycle", "cycle_open_day", 365, "resolved"),), ("appeal_slot", "capacity_hours"),
       "booked plus remaining seats equals two; no direct grade or unfunded grant", ("seat availability", "issue and manager", "investigation/pending promise")),
    _b(80, "公开指标缺陷单", "K", "anti_retaliation_due", "resolved", "observation_closed",
       "defect owner/evidence/decision/deadline, metric version and later responsibility", "public metric-defect ledger",
       "open one versioned defect and verify repair or accepted risk", "suppress without deleting evidence and preserve later blast-chain liability", 90,
       (_deadline("metric_defect_due", "ticket_open_day", 90, "observation_closed"),), (),
       "one defect has one current state and one contribution receipt", ("ticket owner/state/deadline", "metric version/verification", "later responsibility chain"),
       "metric versioning and responsibility records transfer no conserved resource"),
    _b(81, "绩效信息层级压缩", "K", "anti_retaliation_due", "resolved", "observation_closed",
       "field-level ACL, summary version, access level/log and lawful correction owner", "casebook access projection",
       "project least-privilege views while keeping central review read-only", "serve a compressed summary and retain omitted-field distortion trace", 180,
       _SYNC("anti_retaliation_due", "observation_closed"), ("appeal_slot",),
       "access consumes only authorized review capacity and never transfers rating ownership", ("field ACL", "access log", "omitted-field and correction-owner marker")),

    _b(146, "直白档位 / 委婉话术制度", "T", "result_frozen", "result_locked", "feedback_held",
       "delivery style/order with invariant rating, evidence, consequence and understanding", "feedback session and appeal clock",
       "state the same frozen rating plainly and record understanding", "use indirect wording but retain the exact rating and misunderstanding debt", 90,
       (_deadline("feedback_meeting", "result_frozen_day", 30, "feedback_held"),), ("capacity_hours",),
       "meeting hours settle once; narrative style never changes rating or consequence", ("delivery style", "frozen rating/evidence", "understanding gap")),
    _b(147, "强制“一扬一抑”反馈模板", "T", "result_frozen", "result_locked", "feedback_held",
       "evidence-linked praise/critique statements, boilerplate count and manager credit", "feedback statement page",
       "allow evidence to determine polarity counts", "force both polarities and mark unsupported boilerplate", 180,
       (_deadline("feedback_meeting", "result_frozen_day", 30, "feedback_held"),), ("capacity_hours",),
       "one statement can earn feedback credit once and only with frozen evidence", ("statement/polarity/evidence rows", "boilerplate warning")),
    _b(148, "先讲证据还是先报结果", "T", "result_frozen", "result_locked", "feedback_held",
       "immutable evidence/rating snapshots, ordered steps, fact acknowledgements and disputes", "feedback minutes and appeal evidence",
       "complete every evidence step before announcing the rating", "announce rating first but retain identical evidence and disputes", 90,
       (_deadline("feedback_meeting", "result_frozen_day", 30, "feedback_held"),), ("capacity_hours",),
       "both orders consume one session and preserve the same snapshot hashes", ("current step", "fact acknowledgements/disputes", "closed timestamp")),
    _b(149, "绩效结果谈判包", "T", "feedback_meeting_due", "feedback_held", "receipt_recorded",
       "lower-rating bargain terms with unique owners, deadlines and fulfillment", "personal result bargain page",
       "write enforceable future terms while preserving the current lower rating", "record unwritten assurance without marking debt fulfilled or closing appeal", 180,
       (_deadline("bargain_term_due", "bargain_signed_day", 180, "receipt_recorded"),), ("treasury_gold", "personal_gold"),
       "any gold term transfers equal amounts once; no term pre-books a future rating", ("accepted terms and owners", "fulfillment status", "appeal remains available")),
    _b(150, "“这次先委屈你”的补偿承诺", "T", "feedback_meeting_due", "feedback_held", "receipt_recorded",
       "sacrifice case, written promise owner/kind/deadline/status and betrayal record", "settlement statement and promise timeline",
       "open a written non-rating compensation obligation", "record oral assurance and expose that it is not fulfilled debt", 90,
       (_deadline("compensation_promise_due", "promise_day", 365, "receipt_recorded"),), ("treasury_gold", "personal_gold"),
       "cash promise debits equal credits once; breach posts once after due day", ("team-sacrifice marker", "written terms", "fulfilled/breached outcome")),
    _b(151, "签收不等于认同", "T", "feedback_meeting_due", "feedback_held", "receipt_recorded",
       "one delivery receipt status, objection/dispute, witness and appeal eligibility", "receipt row and appeal case",
       "record receipt separately from agreement and keep objection/refusal appeal open", "coerce receipt into agreement while preserving the suppressed intent as procedural debt", 90,
       (_deadline("feedback_refusal_witness", "refusal_day", 7, "receipt_recorded"), _deadline("appeal_expiry", "delivered_day", 90, "receipt_recorded")),
       ("capacity_hours",), "one delivery has one mutually exclusive receipt; witness does not imply agreement",
       ("received/agreed/disputed split", "witness", "appeal eligibility")),
    _b(152, "反馈可行动性评分", "T", "feedback_receipt_due", "receipt_recorded", "actions_open",
       "specificity/controllability/deadline/resource scores and manager sample count", "manager feedback scorecard",
       "score once on a frozen four-part actionability scale", "record compliance sentiment without promoting vague advice to full score", 90,
       (_deadline("actionability_writeback", "feedback_received_day", 365, "actions_open"),), ("capacity_hours",),
       "each recipient rates each feedback record once", ("four component scores", "sample count", "coaching threshold")),
    _b(153, "反馈后行动项闭环", "T", "feedback_receipt_due", "receipt_recorded", "actions_open",
       "unique action owner, current/original due date, status, close evidence and credit cycle", "feedback action timeline",
       "open and evidence-close a bounded action with one later credit cycle", "allow change/cancel but retain history and visible reason", 90,
       (_deadline("feedback_action_due", "action_open_day", 90, "actions_open"),), ("capacity_hours",),
       "one action has one owner/current deadline and one terminal receipt", ("owner/due/status", "reschedule history", "close evidence")),
    _b(154, "录音式完整纪要 / 摘要纪要", "T", "feedback_receipt_due", "receipt_recorded", "actions_open",
       "minutes mode, participants, evidence refs, append-only corrections and field ACL", "minutes and appeal projection",
       "retain complete append-only minutes with participant corrections", "retain result/evidence references in a compressed record", 180,
       (_deadline("minutes_correction", "minutes_delivered_day", 7, "actions_open"),), ("capacity_hours",),
       "corrections append and never delete; minutes create no new evidence identity", ("retention mode", "confirmation/corrections", "access scope")),
    _b(155, "公开表扬与私下批评边界", "T", "feedback_actions_open", "actions_open", "resolved",
       "public praise/team results, private sensitive feedback and one shaming consequence", "team announcement and private feedback",
       "publish only approved achievements while keeping sensitive case material private", "name bottom performers publicly and apply consequence only to actual names", 180,
       _SYNC("feedback_actions_open", "resolved"), (), "one publication receipt prevents duplicate relationship/climate consequences",
       ("approved public fields", "private sensitive rows", "boundary violation consequence"),
       "publication changes projections and relationships, not a conserved resource"),
    _b(156, "团队结果说明会", "T", "feedback_actions_open", "actions_open", "resolved",
       "one briefing per team/cycle with rule, common issues, resources and attendees", "team briefing and policy dashboard",
       "brief once after publication without private appeal or peer text", "skip briefing after delivery and post one information-vacuum risk", 90,
       (_deadline("team_briefing", "scoreboard_published_day", 30, "resolved"),), ("capacity_hours",),
       "one team/cycle consumes one briefing receipt", ("distribution rule", "common issues/resource plan", "completed or rumor-risk status")),

    _b(181, "能力、意愿、错岗三分诊", "W", "pip_triaged", "triaged", "evidence_met",
       "single primary triage category, evidence, reviewer, disposition and misdiagnosis", "PIP triage page",
       "classify evidence and route role mismatch without rewriting the current rating", "assume unwillingness and expose evidence/appeal risk", 90,
       (_deadline("pip_triage", "pip_candidate_day", 30, "evidence_met"),), ("pip_capacity",),
       "one case has one primary category at a time", ("category/evidence", "matching disposition", "misdiagnosis outcome")),
    _b(182, "PIP 启动证据门槛", "W", "pip_triaged", "triaged", "evidence_met",
       "threshold rule, severe/prior/low-rating evidence and eligibility", "PIP start gate",
       "start only when a frozen evidence combination meets threshold", "auto-start once from 3.25 and post false-positive risk", 90,
       (_deadline("pip_evidence", "triage_day", 30, "evidence_met"),), ("pip_capacity",),
       "one candidate creates at most one formal PIP and red-line misconduct routes elsewhere", ("met threshold evidence", "eligible/insufficient reason", "false-positive risk")),
    _b(183, "PIP 目标双签与拒签理由", "W", "pip_triaged", "triaged", "evidence_met",
       "frozen goals/resources/deadlines, one revision, dual signatures or refusal reason", "PIP goal and acknowledgement page",
       "start time only after dual signature or independent confirmation", "preserve refusal reason and independent reasonableness review", 90,
       (_deadline("pip_acknowledgement", "goals_delivered_day", 30, "evidence_met"),), ("pip_capacity",),
       "one subject revision and one acknowledgement receipt; refusal itself is not failure", ("goal/resources/deadline rows", "signature/revision/refusal status")),
    _b(184, "经理的 PIP 承载量", "W", "pip_evidence_due", "evidence_met", "acknowledged",
       "active case IDs, limit, mentor/stagger/support allocations and overload liability", "manager PIP capacity panel",
       "reserve bounded manager hours or add mentor/staggered capacity", "overbook and allocate resulting failure liability partly to manager", 90,
       (_deadline("pip_capacity_release", "pip_end_day", 0, "acknowledged"),), ("pip_capacity",),
       "case support reservations sum <= available manager/superior capacity and release once", ("active/limit count", "per-case hours", "overload liability")),
    _b(185, "PIP 中期检查", "W", "pip_evidence_due", "evidence_met", "acknowledged",
       "one midpoint date/progress/resource-delivery/goal-validity/correction/outcome", "PIP timeline",
       "run one midpoint and allow at most one evidenced correction", "omit midpoint and expose that no later correction/resource claim is valid", 90,
       (_deadline("pip_midpoint", "pip_start_day", 180, "acknowledged"),), ("pip_capacity",),
       "one case posts one midpoint receipt and one correction maximum", ("midpoint date/progress", "resource delivery", "continue/correct/end outcome")),
    _b(186, "PIP 目标膨胀锁", "W", "pip_ack_due", "acknowledged", "executing",
       "baseline/current workload, append-only changes, replacement/extension/review and violation", "PIP goal-change ledger",
       "allow added work only with equal replacement, extension or emergency approval", "apply overload and post a goal-creep violation without banning all later change", 90,
       (_deadline("goal_change_review", "change_requested_day", 7, "executing"),), ("pip_capacity",),
       "current work may exceed baseline only under one frozen compensation route", ("old/new workload", "replacement/extension/review", "creep finding")),
    _b(187, "PIP 毕业标准", "W", "pip_ack_due", "acknowledged", "executing",
       "milestone statuses, key set, stability end, independent review and one extension", "PIP graduation page",
       "graduate only after every key milestone and stability window", "let manager extend while recording opaque-veto appeal weight", 90,
       (_deadline("pip_stability", "last_key_milestone_day", 90, "executing"),), ("pip_capacity",),
       "graduation closes escalation and releases capacity once; it never writes 3.75", ("graduation checklist", "stability countdown", "review/extension reason")),
    _b(188, "毕业后的复发观察期", "W", "pip_execution_due", "executing", "midpoint",
       "one-cycle observation, relapse identity/category and escalation status", "subject observation marker",
       "observe exactly one cycle and escalate only the same problem category", "apply a long-lived label and record its overbreadth appeal risk", 90,
       (_deadline("relapse_observation", "graduation_cycle", 365, "midpoint"),), ("pip_capacity",),
       "observation marker expires once; new issue opens a separate case", ("start/end cycle", "same/new/external category", "escalation result")),
    _b(189, "二次 PIP / 调岗 / 退出三岔口", "W", "pip_execution_due", "executing", "midpoint",
       "support sufficiency, role mismatch, real vacancy, exclusive disposition and costs", "PIP terminal decision and team page",
       "choose one eligible second-case/transfer/exit route", "force exit while posting vacancy/handover/replacement cost", 90,
       (_deadline("pip_terminal_choice", "pip_failed_day", 30, "midpoint"),), ("pip_capacity", "exit_cost", "treasury_gold"),
       "one terminal case chooses one route; capacity and exit costs settle once", ("three-route eligibility/cost", "new case/vacancy/exit outcome")),
    _b(190, "PIP 随转岗披露的最小范围", "W", "pip_midpoint_due", "midpoint", "resolved",
       "recipient-only goal/support/completion snapshot, subject statement and excluded private IDs", "transfer disclosure package",
       "disclose minimum necessary fields to the actual receiving manager", "apply a coarse label and record stigma risk without fabricated detail", 90,
       (_deadline("transfer_decision", "disclosure_day", 30, "resolved"),), ("pip_capacity",),
       "disclosure changes ACL only and never rewrites old ratings or expands after refusal", ("minimum transfer packet", "subject statement", "excluded private fields")),
    _b(191, "PIP 退出后的团队成本单", "W", "pip_midpoint_due", "midpoint", "resolved",
       "vacancy days, handover gaps, overtime, recruitment payment and net outcome", "team exit-cost statement and manager scorecard",
       "post one net cost statement backed by actual expense receipts", "report gross saving while retaining hidden vacancy/handover liabilities", 90,
       (_deadline("exit_cost_close", "exit_day", 30, "resolved"),), ("treasury_gold", "personal_gold", "exit_cost"),
       "actual recruitment expense equals treasury debit; one exit has one statement", ("vacancy/handover/overtime", "recruitment receipt", "gross versus net result")),

    _b(358, "申诉不加重原则", "AL", "appeal_quota_returned", "appeal_returned", "collective_action",
       "original/reviewed band and sanction vectors, aggravation flag and separate misconduct case", "appeal comparison and settlement statements",
       "forbid worse review outcome and route new misconduct through a separately served case", "allow and explicitly flag same-case aggravation with retaliation risk", 90,
       (_deadline("appeal_review", "appeal_filed_day", 90, "collective_action"),), ("appeal_slot", "penalty_receipt"),
       "original appeal and separate misconduct case each settle at most once", ("before/after sanction comparison", "non-aggravation flag", "separate-case delivery")),
    _b(359, "翻案后的配额回流与连环送达", "AL", "appeal_quota_returned", "appeal_returned", "collective_action",
       "quota return route, reserved slot/boundary/debt, version diff and redelivery", "quota ledger, revised scoreboard and new notice",
       "use reserve, boundary review or next-cycle debt and redeliver every harmed boundary case", "hide boundary downgrade while preserving audit diff and later cure liability", 90,
       (_deadline("redelivery_appeal", "redelivered_day", 90, "collective_action"), _deadline("quota_debt_due", "next_cycle_open", 0, "collective_action")),
       ("quota_slot", "appeal_slot"), "corrected counts, consumed reserve or next-cycle debt reconcile; each appeal returns once",
       ("quota-return route", "versioned scoreboard diff", "redelivery and fresh appeal deadline")),
)


def validate_b2_bindings(bindings: Iterable[B2Binding] = B2_BINDINGS) -> None:
    rows = tuple(bindings)
    ids = tuple(row.mechanism_id for row in rows)
    if ids != B2_IDS:
        raise ValueError("B2 bindings must cover the exact 42 rows in canonical order")
    if len(set(ids)) != 42 or set(B2_NEW_IDS) & set(B2_INTERFACE_IDS):
        raise ValueError("B2 new and interface mechanism IDs must be unique and disjoint")
    if set(B2_NEW_IDS) | set(B2_INTERFACE_IDS) != set(B2_IDS):
        raise ValueError("B2 must contain exactly forty new IDs plus 018/069")
    if sum(row.batch_role == "new-mechanism" for row in rows) != 40:
        raise ValueError("B2 completion numerator contains exactly forty new mechanisms")
    if {
        row.mechanism_id
        for row in rows
        if row.batch_role == "interface-only"
    } != set(B2_INTERFACE_IDS):
        raise ValueError("018/069 must remain interface-only rows, never new completion")
    receipt_keys: set[str] = set()
    for row in rows:
        identity = (
            row.owner_binding,
            row.subject_binding,
            row.cycle_binding,
            row.case_binding,
            row.state_binding,
        )
        if not all(identity) or not row.hook or not row.meaningful_write or not row.consumer:
            raise ValueError(f"mechanism {row.mechanism_id:03d} has an incomplete binding")
        if tuple(route.route for route in row.routes) != tuple(PolicyRoute):
            raise ValueError(f"mechanism {row.mechanism_id:03d} must freeze A/B/C routes")
        a_route, b_route, c_route = row.routes
        if not a_route.mutates_business_case or not b_route.mutates_business_case:
            raise ValueError(f"mechanism {row.mechanism_id:03d} A/B must post a business write")
        if (
            c_route.operation != "policy.defer"
            or c_route.mutates_business_case
            or c_route.from_state != c_route.to_state
            or c_route.defer_days <= 0
        ):
            raise ValueError(f"mechanism {row.mechanism_id:03d} C must be a bounded no-case-write defer")
        if not row.deadlines:
            raise ValueError(f"mechanism {row.mechanism_id:03d} lacks a deadline contract")
        for deadline in row.deadlines:
            if deadline.days < 0 or deadline.stale_guard != STALE_GUARD:
                raise ValueError(f"mechanism {row.mechanism_id:03d} has an invalid deadline")
            if not deadline.target_binding or not deadline.expected_state:
                raise ValueError(f"mechanism {row.mechanism_id:03d} deadline is not target-bound")
        if not row.transaction.conservation:
            raise ValueError(f"mechanism {row.mechanism_id:03d} lacks a transaction invariant")
        if not row.transaction.resources and not row.transaction.no_transfer_reason:
            raise ValueError(f"mechanism {row.mechanism_id:03d} must explain no-transfer routes")
        if len(row.receipt.keys) != 3 or not row.receipt.replay or not row.receipt.refund_rule:
            raise ValueError(f"mechanism {row.mechanism_id:03d} has an incomplete receipt contract")
        if receipt_keys.intersection(row.receipt.keys):
            raise ValueError("B2 operation receipt keys must be globally unique")
        receipt_keys.update(row.receipt.keys)
        if not row.feedback:
            raise ValueError(f"mechanism {row.mechanism_id:03d} lacks visible feedback")
        if row.runtime_evidence != RUNTIME_EVIDENCE or row.readiness_change != READINESS_CHANGE:
            raise ValueError(f"mechanism {row.mechanism_id:03d} overstates runtime readiness")


class Band(IntEnum):
    BOTTOM_325 = 1
    NORMAL_35 = 2
    TOP_375 = 3


@dataclass(frozen=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        if not self.owner_id or not self.subject_id:
            raise ValueError("case owner and subject are required")
        if self.cycle_serial < 1 or self.case_serial < 1:
            raise ValueError("cycle and case serials must be positive")

    @property
    def key(self) -> str:
        return f"{self.owner_id}:{self.subject_id}:{self.cycle_serial}:{self.case_serial}"


@dataclass(frozen=True)
class StateToken:
    identity: CaseIdentity
    expected_state: str


@dataclass(frozen=True)
class DeadlineToken:
    identity: CaseIdentity
    expected_state: str
    kind: str
    target_id: str
    due_day: int

    def __post_init__(self) -> None:
        if not self.kind or not self.target_id or self.due_day < 0:
            raise ValueError("deadline kind, target and non-negative day are required")


@dataclass(frozen=True)
class ActionResult:
    applied: bool
    code: str
    previous_state: str
    current_state: str


class Currency(str, Enum):
    GOLD = "gold"
    MERIT = "merit"


class Account(str, Enum):
    TREASURY = "treasury"
    PERSONAL_GOLD = "personal_gold"
    GOLD_SINK = "gold_sink"
    MERIT = "merit"
    MERIT_SINK = "merit_sink"


ACCOUNT_CURRENCY: Final[dict[Account, Currency]] = {
    Account.TREASURY: Currency.GOLD,
    Account.PERSONAL_GOLD: Currency.GOLD,
    Account.GOLD_SINK: Currency.GOLD,
    Account.MERIT: Currency.MERIT,
    Account.MERIT_SINK: Currency.MERIT,
}


@dataclass
class ConservationLedger:
    """Small account ledger used by penalties, refunds, promises, and exit cost."""

    balances: dict[Account, int]
    _initial_totals: dict[Currency, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        normalized: dict[Account, int] = {account: 0 for account in Account}
        for raw_account, amount in self.balances.items():
            account = Account(raw_account)
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise ValueError("ledger balances must be non-negative integers")
            normalized[account] = amount
        self.balances = normalized
        self._initial_totals = {currency: self.total(currency) for currency in Currency}

    def total(self, currency: Currency) -> int:
        return sum(
            amount
            for account, amount in self.balances.items()
            if ACCOUNT_CURRENCY[account] == currency
        )

    def move(
        self,
        source: Account,
        destination: Account,
        requested: int,
        *,
        allow_partial: bool,
    ) -> int | None:
        source = Account(source)
        destination = Account(destination)
        if ACCOUNT_CURRENCY[source] != ACCOUNT_CURRENCY[destination]:
            raise ValueError("ledger transfer currency mismatch")
        if isinstance(requested, bool) or not isinstance(requested, int) or requested < 0:
            raise ValueError("ledger transfer amount must be a non-negative integer")
        available = self.balances[source]
        if not allow_partial and available < requested:
            return None
        actual = min(available, requested) if allow_partial else requested
        self.balances[source] -= actual
        self.balances[destination] += actual
        self.assert_conserved()
        return actual

    def assert_conserved(self) -> None:
        for currency, initial in self._initial_totals.items():
            if self.total(currency) != initial:
                raise AssertionError(f"{currency.value} is not conserved")


def penalty_sink(source: Account) -> Account:
    source = Account(source)
    if source in (Account.TREASURY, Account.PERSONAL_GOLD):
        return Account.GOLD_SINK
    if source == Account.MERIT:
        return Account.MERIT_SINK
    raise ValueError("penalty source must be treasury, personal gold, or merit")


@dataclass
class LedgerReceipt:
    receipt_id: str
    source: Account
    destination: Account
    requested: int
    allow_partial: bool = False
    settled_amount: int = 0
    refunded_amount: int = 0
    settlement_count: int = 0
    refund_count: int = 0

    def __post_init__(self) -> None:
        self.source = Account(self.source)
        self.destination = Account(self.destination)
        if not self.receipt_id:
            raise ValueError("receipt id is required")
        if isinstance(self.requested, bool) or not isinstance(self.requested, int) or self.requested < 0:
            raise ValueError("receipt amount must be a non-negative integer")
        if ACCOUNT_CURRENCY[self.source] != ACCOUNT_CURRENCY[self.destination]:
            raise ValueError("receipt source and destination currency must match")

    def settle_once(self, ledger: ConservationLedger) -> bool:
        if self.settlement_count:
            return False
        actual = ledger.move(
            self.source,
            self.destination,
            self.requested,
            allow_partial=self.allow_partial,
        )
        if actual is None:
            return False
        self.settled_amount = actual
        self.settlement_count = 1
        return True

    def refund_once(
        self,
        ledger: ConservationLedger,
        amount: int | None = None,
    ) -> bool:
        if self.settlement_count != 1 or self.refund_count:
            return False
        maximum = self.settled_amount - self.refunded_amount
        refundable = maximum if amount is None else amount
        if (
            isinstance(refundable, bool)
            or not isinstance(refundable, int)
            or not 0 <= refundable <= maximum
        ):
            raise ValueError("refund must be bounded by the unsettled receipt amount")
        actual = ledger.move(
            self.destination,
            self.source,
            refundable,
            allow_partial=False,
        )
        if actual is None:
            raise AssertionError("settled receipt destination cannot fund its refund")
        self.refunded_amount += actual
        self.refund_count = 1
        return True

    @property
    def refund_bounded(self) -> bool:
        return 0 <= self.refunded_amount <= self.settled_amount <= self.requested


def make_penalty_receipts(
    rows: Iterable[tuple[str, Account, int]],
) -> list[LedgerReceipt]:
    return [
        LedgerReceipt(receipt_id, source, penalty_sink(source), amount, allow_partial=True)
        for receipt_id, source, amount in rows
    ]


@dataclass(frozen=True)
class SanctionVector:
    treasury: int = 0
    personal_gold: int = 0
    merit: int = 0
    salary_cut_percent: int = 0
    pip: int = 0

    def __post_init__(self) -> None:
        for value in (
            self.treasury,
            self.personal_gold,
            self.merit,
            self.salary_cut_percent,
            self.pip,
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("sanction components must be non-negative integers")

    def no_worse_than(self, other: "SanctionVector") -> bool:
        return all(
            mine <= original
            for mine, original in zip(
                (
                    self.treasury,
                    self.personal_gold,
                    self.merit,
                    self.salary_cut_percent,
                    self.pip,
                ),
                (
                    other.treasury,
                    other.personal_gold,
                    other.merit,
                    other.salary_cut_percent,
                    other.pip,
                ),
            )
        )


class NoticeState(str, Enum):
    PREPARED = "PREPARED"
    REFUSED_PENDING_WITNESS = "REFUSED_PENDING_WITNESS"
    APPEAL_OPEN = "APPEAL_OPEN"
    APPEAL_UNDER_REVIEW = "APPEAL_UNDER_REVIEW"
    CLOSED_UPHELD = "CLOSED_UPHELD"
    CORRECTED = "CORRECTED"


@dataclass
class NoticeJusticeCase:
    identity: CaseIdentity
    ledger: ConservationLedger
    receipts: list[LedgerReceipt]
    original_band: Band = Band.BOTTOM_325
    original_sanctions: SanctionVector = SanctionVector(50, 25, 60, 25, 1)
    state: NoticeState = NoticeState.PREPARED
    delivery_method: str | None = None
    delivery_day: int | None = None
    witness_id: str | None = None
    objection_recorded: bool = False
    appeal_reason: str | None = None
    appeal_outcome: str | None = None
    reviewed_band: Band | None = None
    reviewed_sanctions: SanctionVector | None = None
    aggravation_flag: bool = False
    linked_new_misconduct_case_id: str | None = None
    salary_withholding_active: bool = False
    witness_deadline: DeadlineToken | None = None
    appeal_deadline: DeadlineToken | None = None
    policy_debt_count: int = 0

    def __post_init__(self) -> None:
        ids = [receipt.receipt_id for receipt in self.receipts]
        if len(ids) != len(set(ids)):
            raise ValueError("receipt ids must be unique within the notice case")
        if any(receipt.allow_partial is False for receipt in self.receipts):
            raise ValueError("notice penalty receipts must settle actual available amounts")

    def token(self) -> StateToken:
        return StateToken(self.identity, self.state.value)

    def _guard(self, token: StateToken) -> bool:
        return token == self.token()

    def _result(self, applied: bool, code: str, previous: NoticeState) -> ActionResult:
        return ActionResult(applied, code, previous.value, self.state.value)

    def acknowledge(
        self,
        token: StateToken,
        *,
        actor_id: str,
        today: int,
        with_objection: bool = False,
    ) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._result(False, "stale-token", previous)
        if actor_id != self.identity.subject_id:
            return self._result(False, "wrong-subject", previous)
        if self.state != NoticeState.PREPARED:
            return self._result(False, "illegal-transition", previous)
        self.delivery_method = "acknowledged_with_objection" if with_objection else "acknowledged"
        self.objection_recorded = with_objection
        self._deliver(today)
        return self._result(True, "delivered", previous)

    def refuse(self, token: StateToken, *, actor_id: str, today: int) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._result(False, "stale-token", previous)
        if actor_id != self.identity.subject_id:
            return self._result(False, "wrong-subject", previous)
        if self.state != NoticeState.PREPARED:
            return self._result(False, "illegal-transition", previous)
        self.state = NoticeState.REFUSED_PENDING_WITNESS
        self.delivery_method = "refused_pending_witness"
        self.witness_deadline = DeadlineToken(
            self.identity,
            self.state.value,
            "witness_service",
            self.identity.subject_id,
            today + WITNESS_DELAY_DAYS,
        )
        return self._result(True, "refusal-recorded", previous)

    def run_witness_deadline(
        self,
        deadline: DeadlineToken,
        *,
        today: int,
        witness_id: str,
    ) -> ActionResult:
        previous = self.state
        if deadline != self.witness_deadline or deadline.target_id != self.identity.subject_id:
            return self._result(False, "stale-target-bound-deadline", previous)
        if deadline.identity != self.identity or deadline.expected_state != self.state.value:
            return self._result(False, "stale-target-bound-deadline", previous)
        if self.state != NoticeState.REFUSED_PENDING_WITNESS:
            return self._result(False, "illegal-transition", previous)
        if today < deadline.due_day:
            return self._result(False, "not-due", previous)
        if not witness_id or witness_id in (self.identity.owner_id, self.identity.subject_id):
            return self._result(False, "invalid-witness", previous)
        self.delivery_method = "witness_after_refusal"
        self.witness_id = witness_id
        self._deliver(today)
        return self._result(True, "witness-delivered", previous)

    def _deliver(self, today: int) -> None:
        for receipt in self.receipts:
            if not receipt.settle_once(self.ledger):
                raise AssertionError("fresh notice receipt must settle exactly once")
        self.delivery_day = today
        self.salary_withholding_active = self.original_sanctions.salary_cut_percent > 0
        self.state = NoticeState.APPEAL_OPEN
        self.appeal_deadline = DeadlineToken(
            self.identity,
            self.state.value,
            "appeal_expiry",
            self.identity.subject_id,
            today + APPEAL_WINDOW_DAYS,
        )

    def submit_appeal(
        self,
        token: StateToken,
        *,
        actor_id: str,
        target_manager_id: str,
        today: int,
        reason: str,
    ) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._result(False, "stale-token", previous)
        if actor_id != self.identity.subject_id or target_manager_id != self.identity.owner_id:
            return self._result(False, "wrong-appeal-party", previous)
        if self.state != NoticeState.APPEAL_OPEN or self.appeal_deadline is None:
            return self._result(False, "illegal-transition", previous)
        if today > self.appeal_deadline.due_day:
            return self._result(False, "appeal-expired", previous)
        if not reason:
            return self._result(False, "missing-reason", previous)
        self.appeal_reason = reason
        self.state = NoticeState.APPEAL_UNDER_REVIEW
        return self._result(True, "appeal-opened", previous)

    def expire_appeal(self, deadline: DeadlineToken, *, today: int) -> ActionResult:
        previous = self.state
        if deadline != self.appeal_deadline or deadline.target_id != self.identity.subject_id:
            return self._result(False, "stale-target-bound-deadline", previous)
        if deadline.identity != self.identity or deadline.expected_state != self.state.value:
            return self._result(False, "stale-target-bound-deadline", previous)
        if self.state != NoticeState.APPEAL_OPEN:
            return self._result(False, "illegal-transition", previous)
        if today < deadline.due_day:
            return self._result(False, "not-due", previous)
        self.state = NoticeState.CLOSED_UPHELD
        self.appeal_outcome = "expired_upheld"
        return self._result(True, "appeal-closed", previous)

    def resolve_appeal(
        self,
        token: StateToken,
        *,
        route: PolicyRoute,
        reviewed_band: Band,
        reviewed_sanctions: SanctionVector,
        new_misconduct_case_id: str | None = None,
    ) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._result(False, "stale-token", previous)
        if self.state != NoticeState.APPEAL_UNDER_REVIEW:
            return self._result(False, "illegal-transition", previous)
        if route == PolicyRoute.C:
            if self.policy_debt_count:
                return self._result(False, "duplicate-policy-debt", previous)
            self.policy_debt_count = 1
            return self._result(True, "policy-deferred", previous)
        reviewed_band = Band(reviewed_band)
        if route == PolicyRoute.A and (
            reviewed_band < self.original_band
            or not reviewed_sanctions.no_worse_than(self.original_sanctions)
        ):
            raise ValueError("route A appeal review may not aggravate the original case")
        self.aggravation_flag = reviewed_band < self.original_band or not reviewed_sanctions.no_worse_than(
            self.original_sanctions
        )
        self.reviewed_band = reviewed_band
        self.reviewed_sanctions = reviewed_sanctions
        if new_misconduct_case_id:
            if new_misconduct_case_id == str(self.identity.case_serial):
                raise ValueError("new misconduct must use a separate case identity")
            self.linked_new_misconduct_case_id = new_misconduct_case_id
        corrected = (
            reviewed_band > self.original_band
            or reviewed_sanctions != self.original_sanctions
        ) and not self.aggravation_flag
        if corrected:
            for receipt in self.receipts:
                retained = {
                    Account.TREASURY: reviewed_sanctions.treasury,
                    Account.PERSONAL_GOLD: reviewed_sanctions.personal_gold,
                    Account.MERIT: reviewed_sanctions.merit,
                }.get(receipt.source, receipt.settled_amount)
                refund = max(0, receipt.settled_amount - min(receipt.settled_amount, retained))
                receipt.refund_once(self.ledger, refund)
            self.salary_withholding_active = reviewed_sanctions.salary_cut_percent > 0
            self.state = NoticeState.CORRECTED
            self.appeal_outcome = "corrected_and_refunded"
            return self._result(True, "appeal-corrected", previous)
        self.state = NoticeState.CLOSED_UPHELD
        self.appeal_outcome = "aggravated" if self.aggravation_flag else "upheld"
        return self._result(True, self.appeal_outcome, previous)


@dataclass(frozen=True)
class PolicyDebtRecord:
    mechanism_id: int
    identity: CaseIdentity
    posted_day: int
    due_day: int
    receipt_key: str


@dataclass
class PolicyDebtBook:
    """Idempotent sink for route C; it never owns or mutates a business case."""

    records: dict[tuple[int, CaseIdentity], PolicyDebtRecord] = field(default_factory=dict)

    def post_once(
        self,
        binding: B2Binding,
        identity: CaseIdentity,
        *,
        today: int,
    ) -> bool:
        route = binding.routes[2]
        if route.route != PolicyRoute.C or route.mutates_business_case:
            raise ValueError("policy debt can only consume a route-C contract")
        key = (binding.mechanism_id, identity)
        if key in self.records:
            return False
        self.records[key] = PolicyDebtRecord(
            binding.mechanism_id,
            identity,
            today,
            today + route.defer_days,
            binding.receipt.keys[2],
        )
        return True


class RetaliationFinding(str, Enum):
    PENDING_INDEPENDENT_REVIEW = "PENDING_INDEPENDENT_REVIEW"
    NORMAL_MANAGEMENT = "NORMAL_MANAGEMENT"
    RETALIATION = "RETALIATION"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"


@dataclass
class AdverseActionRecord:
    action_id: str
    action_day: int
    reason: str
    new_fact_ids: tuple[str, ...]
    new_fact_days: tuple[int, ...]
    finding: RetaliationFinding
    suspended: bool
    independent_reviewer_id: str | None = None


@dataclass(frozen=True)
class RetaliationResult:
    applied: bool
    code: str
    finding: RetaliationFinding
    suspended: bool


@dataclass
class RetaliationObservation:
    identity: CaseIdentity
    appeal_id: str
    filed_day: int
    manager_id: str
    end_day: int = field(init=False)
    actions: dict[str, AdverseActionRecord] = field(default_factory=dict)
    closed: bool = False

    def __post_init__(self) -> None:
        if not self.appeal_id or not self.manager_id or self.manager_id != self.identity.owner_id:
            raise ValueError("observation must bind the appealed manager and appeal id")
        if self.filed_day < 0:
            raise ValueError("appeal filed day must be non-negative")
        self.end_day = self.filed_day + RETALIATION_WINDOW_DAYS

    def record_adverse_action(
        self,
        *,
        action_id: str,
        manager_id: str,
        subject_id: str,
        action_day: int,
        reason: str,
        new_facts: Mapping[str, int] | None = None,
    ) -> RetaliationResult:
        if action_id in self.actions:
            prior = self.actions[action_id]
            return RetaliationResult(False, "duplicate-action", prior.finding, prior.suspended)
        if manager_id != self.manager_id or subject_id != self.identity.subject_id:
            return RetaliationResult(False, "wrong-observation-party", RetaliationFinding.OUTSIDE_WINDOW, False)
        if not action_id or not reason:
            raise ValueError("adverse action id and reason are required")
        facts = dict(new_facts or {})
        in_window = self.filed_day <= action_day < self.end_day and not self.closed
        valid_new_facts = bool(facts) and all(
            self.filed_day < fact_day <= action_day for fact_day in facts.values()
        )
        if not in_window:
            finding = RetaliationFinding.OUTSIDE_WINDOW
            suspended = False
            code = "ordinary-rule"
        elif valid_new_facts:
            finding = RetaliationFinding.NORMAL_MANAGEMENT
            suspended = False
            code = "post-appeal-facts-supported"
        else:
            finding = RetaliationFinding.PENDING_INDEPENDENT_REVIEW
            suspended = True
            code = "suspended-for-independent-review"
        self.actions[action_id] = AdverseActionRecord(
            action_id,
            action_day,
            reason,
            tuple(facts),
            tuple(facts.values()),
            finding,
            suspended,
        )
        return RetaliationResult(True, code, finding, suspended)

    def resolve_action(
        self,
        action_id: str,
        *,
        reviewer_id: str,
        retaliation_confirmed: bool,
    ) -> RetaliationResult:
        if action_id not in self.actions:
            return RetaliationResult(False, "unknown-action", RetaliationFinding.OUTSIDE_WINDOW, False)
        record = self.actions[action_id]
        if record.finding != RetaliationFinding.PENDING_INDEPENDENT_REVIEW:
            return RetaliationResult(False, "not-pending", record.finding, record.suspended)
        if not reviewer_id or reviewer_id in (self.manager_id, self.identity.subject_id):
            return RetaliationResult(False, "reviewer-not-independent", record.finding, record.suspended)
        record.independent_reviewer_id = reviewer_id
        record.finding = (
            RetaliationFinding.RETALIATION
            if retaliation_confirmed
            else RetaliationFinding.NORMAL_MANAGEMENT
        )
        record.suspended = retaliation_confirmed
        return RetaliationResult(True, "independent-review-posted", record.finding, record.suspended)

    def close(self, *, today: int) -> bool:
        if self.closed or today < self.end_day:
            return False
        self.closed = True
        return True


class FeedbackState(str, Enum):
    RESULT_LOCKED = "RESULT_LOCKED"
    FEEDBACK_HELD = "FEEDBACK_HELD"
    RECEIPT_RECORDED = "RECEIPT_RECORDED"
    ACTIONS_OPEN = "ACTIONS_OPEN"
    RESOLVED = "RESOLVED"


class FeedbackReceiptStatus(str, Enum):
    RECEIVED = "RECEIVED"
    RECEIVED_WITH_OBJECTION = "RECEIVED_WITH_OBJECTION"
    REFUSED_WITNESSED = "REFUSED_WITNESSED"


class ObligationStatus(str, Enum):
    OPEN = "OPEN"
    FULFILLED = "FULFILLED"
    BREACHED = "BREACHED"
    CANCELLED = "CANCELLED"


@dataclass
class FeedbackObligation:
    obligation_id: str
    owner_id: str
    beneficiary_id: str
    due_day: int
    resource: str
    receipt: LedgerReceipt | None = None
    status: ObligationStatus = ObligationStatus.OPEN
    close_evidence: str | None = None
    breach_count: int = 0

    def __post_init__(self) -> None:
        if not self.obligation_id or not self.owner_id or not self.beneficiary_id or not self.resource:
            raise ValueError("obligation identity, parties and resource are required")
        if self.due_day < 0:
            raise ValueError("obligation due day must be non-negative")

    def fulfill(self, *, evidence: str, ledger: ConservationLedger | None = None) -> bool:
        if self.status != ObligationStatus.OPEN or not evidence:
            return False
        if self.receipt is not None:
            if ledger is None or not self.receipt.settle_once(ledger):
                return False
        self.close_evidence = evidence
        self.status = ObligationStatus.FULFILLED
        return True

    def expire(self, *, today: int) -> bool:
        if self.status != ObligationStatus.OPEN or today <= self.due_day:
            return False
        self.status = ObligationStatus.BREACHED
        self.breach_count = 1
        return True


@dataclass
class FeedbackCommitmentCase:
    identity: CaseIdentity
    frozen_band: Band
    frozen_evidence_hash: str
    state: FeedbackState = FeedbackState.RESULT_LOCKED
    delivery_style: str | None = None
    step_order: tuple[str, ...] = ()
    subject_understood_band: Band | None = None
    understanding_gap: bool = False
    receipt_status: FeedbackReceiptStatus | None = None
    receipt_agrees: bool = False
    receipt_witness_id: str | None = None
    appeal_eligible: bool = True
    obligations: dict[str, FeedbackObligation] = field(default_factory=dict)

    def token(self) -> StateToken:
        return StateToken(self.identity, self.state.value)

    def _result(self, applied: bool, code: str, previous: FeedbackState) -> ActionResult:
        return ActionResult(applied, code, previous.value, self.state.value)

    def hold_meeting(
        self,
        token: StateToken,
        *,
        delivery_style: str,
        step_order: tuple[str, ...],
        disclosed_band: Band,
        evidence_hash: str,
        understood_band: Band,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != FeedbackState.RESULT_LOCKED:
            return self._result(False, "illegal-transition", previous)
        if Band(disclosed_band) != self.frozen_band or evidence_hash != self.frozen_evidence_hash:
            return self._result(False, "frozen-result-mismatch", previous)
        if set(step_order) != {"evidence", "result"} or len(step_order) != 2:
            return self._result(False, "invalid-step-order", previous)
        self.delivery_style = delivery_style
        self.step_order = step_order
        self.subject_understood_band = Band(understood_band)
        self.understanding_gap = self.subject_understood_band != self.frozen_band
        self.state = FeedbackState.FEEDBACK_HELD
        return self._result(True, "feedback-held", previous)

    def record_receipt(
        self,
        token: StateToken,
        *,
        actor_id: str,
        status: FeedbackReceiptStatus,
        agrees: bool,
        witness_id: str | None = None,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != FeedbackState.FEEDBACK_HELD:
            return self._result(False, "illegal-transition", previous)
        if actor_id != self.identity.subject_id:
            return self._result(False, "wrong-subject", previous)
        status = FeedbackReceiptStatus(status)
        if status == FeedbackReceiptStatus.RECEIVED_WITH_OBJECTION and agrees:
            return self._result(False, "objection-cannot-equal-agreement", previous)
        if status == FeedbackReceiptStatus.REFUSED_WITNESSED:
            if not witness_id or witness_id in (self.identity.owner_id, self.identity.subject_id):
                return self._result(False, "invalid-witness", previous)
            agrees = False
        self.receipt_status = status
        self.receipt_agrees = agrees
        self.receipt_witness_id = witness_id
        self.appeal_eligible = not agrees or status != FeedbackReceiptStatus.RECEIVED
        self.state = FeedbackState.RECEIPT_RECORDED
        return self._result(True, "receipt-recorded", previous)

    def open_actions(self, token: StateToken) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != FeedbackState.RECEIPT_RECORDED:
            return self._result(False, "illegal-transition", previous)
        self.state = FeedbackState.ACTIONS_OPEN
        return self._result(True, "actions-open", previous)

    def add_obligation(self, token: StateToken, obligation: FeedbackObligation) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != FeedbackState.ACTIONS_OPEN:
            return self._result(False, "illegal-transition", previous)
        if obligation.obligation_id in self.obligations:
            return self._result(False, "duplicate-obligation", previous)
        self.obligations[obligation.obligation_id] = obligation
        return self._result(True, "obligation-opened", previous)

    def close(self, token: StateToken) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != FeedbackState.ACTIONS_OPEN:
            return self._result(False, "illegal-transition", previous)
        if any(item.status == ObligationStatus.OPEN for item in self.obligations.values()):
            return self._result(False, "open-obligations", previous)
        self.state = FeedbackState.RESOLVED
        return self._result(True, "feedback-resolved", previous)


@dataclass
class CapacityPool:
    total: int
    reservations: dict[str, int] = field(default_factory=dict)
    released: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if isinstance(self.total, bool) or not isinstance(self.total, int) or self.total < 0:
            raise ValueError("capacity total must be a non-negative integer")

    @property
    def used(self) -> int:
        return sum(self.reservations.values())

    @property
    def remaining(self) -> int:
        return self.total - self.used

    def can_reserve(self, key: str, amount: int) -> bool:
        return bool(key) and key not in self.reservations and key not in self.released and 0 <= amount <= self.remaining

    def reserve(self, key: str, amount: int) -> bool:
        if not self.can_reserve(key, amount):
            return False
        self.reservations[key] = amount
        return True

    def release(self, key: str) -> bool:
        if key not in self.reservations:
            return False
        del self.reservations[key]
        self.released.add(key)
        return True


class PipCategory(str, Enum):
    CAPABILITY = "CAPABILITY"
    WILL = "WILL"
    ROLE_MISMATCH = "ROLE_MISMATCH"
    MISCONDUCT = "MISCONDUCT"


class PipState(str, Enum):
    TRIAGED = "TRIAGED"
    EVIDENCE_MET = "EVIDENCE_MET"
    ACK_PENDING = "ACK_PENDING"
    EXECUTING = "EXECUTING"
    MIDPOINT = "MIDPOINT"
    GRADUATED = "GRADUATED"
    FAILED = "FAILED"
    RELAPSE_OBSERVATION = "RELAPSE_OBSERVATION"
    RELAPSED = "RELAPSED"
    OBSERVATION_CLOSED = "OBSERVATION_CLOSED"
    SECOND_PIP = "SECOND_PIP"
    TRANSFERRED = "TRANSFERRED"
    EXITED = "EXITED"
    DISCIPLINE_ROUTED = "DISCIPLINE_ROUTED"


class PipDisposition(str, Enum):
    SECOND_PIP = "SECOND_PIP"
    TRANSFER = "TRANSFER"
    EXIT = "EXIT"


@dataclass(frozen=True)
class PipGoal:
    goal_id: str
    controllable: bool
    required_resource: str
    deadline_day: int
    key_milestone: bool = True

    def __post_init__(self) -> None:
        if not self.goal_id or not self.required_resource or self.deadline_day < 0:
            raise ValueError("PIP goal identity, resource and deadline are required")


@dataclass(frozen=True)
class TransferDisclosure:
    recipient_manager_id: str
    vacancy_id: str
    goal_snapshot: tuple[str, ...]
    support_hours: int
    completion_snapshot: str
    subject_statement: str
    excluded_private_ids: tuple[str, ...]


@dataclass(frozen=True)
class ExitCostStatement:
    exit_day: int
    vacancy_start_day: int
    handover_gaps: tuple[str, ...]
    colleague_overtime: int
    recruitment_gold_cost: int
    receipt_id: str


@dataclass
class PipCase:
    identity: CaseIdentity
    category: PipCategory
    evidence_ids: tuple[str, ...]
    state: PipState = PipState.TRIAGED
    threshold_eligible: bool = False
    goals: tuple[PipGoal, ...] = ()
    revision_used: bool = False
    refusal_reason: str | None = None
    manager_signed: bool = False
    subject_signed: bool = False
    independent_confirmed: bool = False
    start_day: int | None = None
    midpoint_day: int | None = None
    end_day: int | None = None
    support_hours: int = 0
    mentor_id: str | None = None
    support_receipt: LedgerReceipt | None = None
    support_absent: bool = False
    no_support_liability: bool = False
    midpoint_count: int = 0
    midpoint_progress: int | None = None
    midpoint_resources_delivered: bool | None = None
    midpoint_correction: str | None = None
    baseline_workload: int = 0
    current_workload: int = 0
    goal_change_history: list[tuple[int, int, str]] = field(default_factory=list)
    goal_creep_violation: bool = False
    graduation_status: str | None = None
    relapse_end_cycle: int | None = None
    relapse_event_ids: set[str] = field(default_factory=set)
    separate_issue_ids: set[str] = field(default_factory=set)
    terminal_disposition: PipDisposition | None = None
    second_case_id: str | None = None
    transfer_disclosure: TransferDisclosure | None = None
    exit_cost_statement: ExitCostStatement | None = None
    _capacity_pool: CapacityPool | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.category = PipCategory(self.category)
        if not self.evidence_ids:
            raise ValueError("PIP triage requires frozen evidence")

    def token(self) -> StateToken:
        return StateToken(self.identity, self.state.value)

    def _result(self, applied: bool, code: str, previous: PipState) -> ActionResult:
        return ActionResult(applied, code, previous.value, self.state.value)

    def qualify(
        self,
        token: StateToken,
        *,
        severe_failure: bool,
        prior_feedback_count: int,
        low_rating_cycles: int,
        red_line_misconduct: bool = False,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.TRIAGED:
            return self._result(False, "illegal-transition", previous)
        if red_line_misconduct:
            self.state = PipState.DISCIPLINE_ROUTED
            return self._result(True, "routed-to-discipline", previous)
        self.threshold_eligible = severe_failure or (
            prior_feedback_count >= 1 and low_rating_cycles >= 1
        )
        if not self.threshold_eligible:
            return self._result(False, "evidence-threshold-not-met", previous)
        self.state = PipState.EVIDENCE_MET
        return self._result(True, "evidence-threshold-met", previous)

    def freeze_goals(
        self,
        token: StateToken,
        goals: Iterable[PipGoal],
        *,
        baseline_workload: int,
        use_subject_revision: bool = False,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.EVIDENCE_MET:
            return self._result(False, "illegal-transition", previous)
        frozen = tuple(goals)
        if not frozen or len({goal.goal_id for goal in frozen}) != len(frozen):
            return self._result(False, "invalid-goals", previous)
        if baseline_workload < 0:
            raise ValueError("baseline workload must be non-negative")
        self.goals = frozen
        self.revision_used = use_subject_revision
        self.baseline_workload = baseline_workload
        self.current_workload = baseline_workload
        self.state = PipState.ACK_PENDING
        return self._result(True, "goals-frozen", previous)

    def record_refusal(self, token: StateToken, *, reason: str) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.ACK_PENDING or not reason:
            return self._result(False, "illegal-or-empty-refusal", previous)
        if self.refusal_reason is not None:
            return self._result(False, "duplicate-refusal", previous)
        self.refusal_reason = reason
        return self._result(True, "refusal-recorded-not-failure", previous)

    def start_execution(
        self,
        token: StateToken,
        *,
        manager_signed: bool,
        subject_signed: bool,
        independent_confirmed: bool,
        start_day: int,
        end_day: int,
        capacity_pool: CapacityPool,
        support_hours: int,
        mentor_id: str | None = None,
        support_receipt: LedgerReceipt | None = None,
        ledger: ConservationLedger | None = None,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.ACK_PENDING:
            return self._result(False, "illegal-transition", previous)
        if not manager_signed or not (subject_signed or independent_confirmed):
            return self._result(False, "acknowledgement-incomplete", previous)
        if end_day - start_day < 2 or support_hours < 0:
            return self._result(False, "invalid-schedule-or-support", previous)
        if not capacity_pool.can_reserve(self.identity.key, support_hours):
            return self._result(False, "capacity-unavailable", previous)
        if support_receipt is not None:
            if ledger is None or support_receipt.settlement_count:
                return self._result(False, "invalid-support-receipt", previous)
            if (
                not support_receipt.allow_partial
                and ledger.balances[support_receipt.source] < support_receipt.requested
            ):
                return self._result(False, "support-budget-unavailable", previous)
        if not capacity_pool.reserve(self.identity.key, support_hours):
            raise AssertionError("prechecked PIP capacity reservation failed")
        if support_receipt is not None and not support_receipt.settle_once(ledger):
            capacity_pool.release(self.identity.key)
            raise AssertionError("prechecked support receipt settlement failed")
        self.manager_signed = manager_signed
        self.subject_signed = subject_signed
        self.independent_confirmed = independent_confirmed
        self.start_day = start_day
        self.end_day = end_day
        self.midpoint_day = start_day + (end_day - start_day) // 2
        self.support_hours = support_hours
        self.mentor_id = mentor_id
        self.support_receipt = support_receipt
        self.support_absent = support_hours == 0 and mentor_id is None
        self.no_support_liability = False
        self._capacity_pool = capacity_pool
        self.state = PipState.EXECUTING
        return self._result(True, "pip-executing", previous)

    def request_goal_change(
        self,
        token: StateToken,
        *,
        route: PolicyRoute,
        today: int,
        new_workload: int,
        replaced_workload: int = 0,
        deadline_extension_days: int = 0,
        emergency_approved: bool = False,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state not in (PipState.EXECUTING, PipState.MIDPOINT):
            return self._result(False, "illegal-transition", previous)
        if min(new_workload, replaced_workload, deadline_extension_days) < 0:
            raise ValueError("workload and extension values must be non-negative")
        compensated = (
            new_workload <= self.baseline_workload
            or replaced_workload >= new_workload - self.baseline_workload
            or deadline_extension_days > 0
            or emergency_approved
        )
        if route == PolicyRoute.C:
            return self._result(False, "policy-deferred-no-goal-change", previous)
        if route == PolicyRoute.A and not compensated:
            return self._result(False, "goal-creep-locked", previous)
        if route == PolicyRoute.B and not compensated:
            self.goal_creep_violation = True
        if deadline_extension_days and self.end_day is not None:
            self.end_day += deadline_extension_days
        self.current_workload = new_workload
        self.goal_change_history.append(
            (today, new_workload, "compensated" if compensated else "goal-creep")
        )
        return self._result(True, "goal-change-recorded", previous)

    def run_midpoint(
        self,
        token: StateToken,
        *,
        today: int,
        progress_percent: int,
        resources_delivered: bool,
        correction: str | None = None,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.EXECUTING or self.midpoint_day is None or self.end_day is None:
            return self._result(False, "illegal-transition", previous)
        if today < self.midpoint_day:
            return self._result(False, "not-due", previous)
        if today >= self.end_day or not 0 <= progress_percent <= 100:
            return self._result(False, "invalid-midpoint", previous)
        self.midpoint_count = 1
        self.midpoint_progress = progress_percent
        self.midpoint_resources_delivered = resources_delivered
        self.midpoint_correction = correction
        self.state = PipState.MIDPOINT
        return self._result(True, "midpoint-recorded", previous)

    def resolve_due(
        self,
        token: StateToken,
        *,
        today: int,
        completed_goal_ids: Iterable[str],
        stability_end_day: int,
        independent_review: bool,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state not in (PipState.EXECUTING, PipState.MIDPOINT) or self.end_day is None:
            return self._result(False, "illegal-transition", previous)
        if today < self.end_day:
            return self._result(False, "not-due", previous)
        completed = set(completed_goal_ids)
        keys = {goal.goal_id for goal in self.goals if goal.key_milestone}
        graduate = keys <= completed and stability_end_day <= today and independent_review
        self.state = PipState.GRADUATED if graduate else PipState.FAILED
        self.graduation_status = "graduated" if graduate else "failed"
        self.no_support_liability = self.support_absent and not graduate
        self._release_capacity()
        return self._result(True, self.graduation_status, previous)

    def _release_capacity(self) -> None:
        if self._capacity_pool is not None:
            self._capacity_pool.release(self.identity.key)

    def open_relapse_observation(self, token: StateToken) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.GRADUATED:
            return self._result(False, "illegal-transition", previous)
        self.relapse_end_cycle = self.identity.cycle_serial + 1
        self.state = PipState.RELAPSE_OBSERVATION
        return self._result(True, "relapse-observation-open", previous)

    def record_relapse(
        self,
        token: StateToken,
        *,
        event_id: str,
        current_cycle: int,
        category: PipCategory,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.RELAPSE_OBSERVATION or self.relapse_end_cycle is None:
            return self._result(False, "illegal-transition", previous)
        if current_cycle > self.relapse_end_cycle:
            self.state = PipState.OBSERVATION_CLOSED
            return self._result(False, "observation-expired", previous)
        if event_id in self.relapse_event_ids or event_id in self.separate_issue_ids:
            return self._result(False, "duplicate-event", previous)
        if PipCategory(category) != self.category:
            self.separate_issue_ids.add(event_id)
            return self._result(True, "separate-new-issue-required", previous)
        self.relapse_event_ids.add(event_id)
        self.state = PipState.RELAPSED
        return self._result(True, "same-category-relapse", previous)

    def close_relapse_observation(self, token: StateToken, *, current_cycle: int) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state != PipState.RELAPSE_OBSERVATION or self.relapse_end_cycle is None:
            return self._result(False, "illegal-transition", previous)
        if current_cycle <= self.relapse_end_cycle:
            return self._result(False, "not-due", previous)
        self.state = PipState.OBSERVATION_CLOSED
        return self._result(True, "observation-closed", previous)

    def choose_terminal(
        self,
        token: StateToken,
        *,
        disposition: PipDisposition,
        today: int,
        second_case_id: str | None = None,
        recipient_manager_id: str | None = None,
        vacancy_id: str | None = None,
        subject_statement: str = "",
        excluded_private_ids: tuple[str, ...] = (),
        exit_receipt: LedgerReceipt | None = None,
        ledger: ConservationLedger | None = None,
        handover_gaps: tuple[str, ...] = (),
        colleague_overtime: int = 0,
    ) -> ActionResult:
        previous = self.state
        if token != self.token():
            return self._result(False, "stale-token", previous)
        if self.state not in (PipState.FAILED, PipState.RELAPSED):
            return self._result(False, "illegal-transition", previous)
        disposition = PipDisposition(disposition)
        if disposition == PipDisposition.SECOND_PIP:
            if not second_case_id or second_case_id == str(self.identity.case_serial):
                return self._result(False, "new-pip-case-required", previous)
            self.second_case_id = second_case_id
            self.state = PipState.SECOND_PIP
        elif disposition == PipDisposition.TRANSFER:
            if not recipient_manager_id or not vacancy_id:
                return self._result(False, "real-vacancy-and-recipient-required", previous)
            self.transfer_disclosure = TransferDisclosure(
                recipient_manager_id,
                vacancy_id,
                tuple(goal.goal_id for goal in self.goals),
                self.support_hours,
                self.graduation_status or "failed",
                subject_statement,
                tuple(excluded_private_ids),
            )
            self.state = PipState.TRANSFERRED
        else:
            if self.exit_cost_statement is not None:
                return self._result(False, "duplicate-exit", previous)
            if exit_receipt is None or ledger is None or not exit_receipt.settle_once(ledger):
                return self._result(False, "exit-cost-unfunded", previous)
            self.exit_cost_statement = ExitCostStatement(
                today,
                today,
                tuple(handover_gaps),
                colleague_overtime,
                exit_receipt.settled_amount,
                exit_receipt.receipt_id,
            )
            self.state = PipState.EXITED
        self.terminal_disposition = disposition
        return self._result(True, disposition.value.lower(), previous)


class QuotaReturnRoute(str, Enum):
    RESERVED_SLOT = "RESERVED_SLOT"
    BOUNDARY_REVIEW = "BOUNDARY_REVIEW"
    NEXT_CYCLE_DEBT = "NEXT_CYCLE_DEBT"
    HIDDEN_REBALANCE = "HIDDEN_REBALANCE"


@dataclass(frozen=True)
class RedeliveryNotice:
    redelivery_id: str
    target_id: str
    delivered_day: int
    appeal_deadline: DeadlineToken


@dataclass(frozen=True)
class QuotaReturnReceipt:
    appeal_id: str
    route: QuotaReturnRoute
    before_counts: tuple[tuple[Band, int], ...]
    after_counts: tuple[tuple[Band, int], ...]
    reserved_consumed: int
    debt_added: int
    affected_official_id: str | None
    audit_diff: bool
    redelivery: RedeliveryNotice | None


@dataclass(frozen=True)
class QuotaReturnResult:
    applied: bool
    code: str
    receipt: QuotaReturnReceipt | None


@dataclass
class QuotaReturnBook:
    owner_id: str
    cycle_serial: int
    case_serial: int
    counts: dict[Band, int]
    reserved_slots: dict[Band, int] = field(default_factory=dict)
    manager_debt: dict[str, int] = field(default_factory=dict)
    receipts: dict[str, QuotaReturnReceipt] = field(default_factory=dict)
    cure_redeliveries: dict[str, RedeliveryNotice] = field(default_factory=dict)
    consumed_debt: set[tuple[str, int]] = field(default_factory=set)
    _cohort_size: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.owner_id or self.cycle_serial < 1 or self.case_serial < 1:
            raise ValueError("quota book owner/cycle/case are required")
        self.counts = {band: int(self.counts.get(band, 0)) for band in Band}
        self.reserved_slots = {band: int(self.reserved_slots.get(band, 0)) for band in Band}
        if any(value < 0 for value in (*self.counts.values(), *self.reserved_slots.values())):
            raise ValueError("quota counts and reserves must be non-negative")
        self._cohort_size = sum(self.counts.values())

    def apply_return(
        self,
        *,
        appeal_id: str,
        corrected_subject_id: str,
        from_band: Band,
        to_band: Band,
        route: QuotaReturnRoute,
        manager_id: str,
        today: int,
        affected_official_id: str | None = None,
    ) -> QuotaReturnResult:
        if appeal_id in self.receipts:
            return QuotaReturnResult(False, "duplicate-appeal-return", self.receipts[appeal_id])
        if not appeal_id or not corrected_subject_id or manager_id != self.owner_id:
            return QuotaReturnResult(False, "wrong-quota-return-party", None)
        from_band = Band(from_band)
        to_band = Band(to_band)
        route = QuotaReturnRoute(route)
        if from_band == to_band or self.counts[from_band] < 1:
            return QuotaReturnResult(False, "invalid-band-return", None)
        if route == QuotaReturnRoute.RESERVED_SLOT and self.reserved_slots[to_band] < 1:
            return QuotaReturnResult(False, "reserved-slot-unavailable", None)
        if route in (QuotaReturnRoute.BOUNDARY_REVIEW, QuotaReturnRoute.HIDDEN_REBALANCE):
            if not affected_official_id or affected_official_id == corrected_subject_id:
                return QuotaReturnResult(False, "distinct-boundary-official-required", None)

        before = dict(self.counts)
        self.counts[from_band] -= 1
        self.counts[to_band] += 1
        reserved_consumed = 0
        debt_added = 0
        redelivery: RedeliveryNotice | None = None
        audit_diff = route == QuotaReturnRoute.HIDDEN_REBALANCE

        if route == QuotaReturnRoute.RESERVED_SLOT:
            self.reserved_slots[to_band] -= 1
            reserved_consumed = 1
        elif route in (QuotaReturnRoute.BOUNDARY_REVIEW, QuotaReturnRoute.HIDDEN_REBALANCE):
            self.counts[to_band] -= 1
            self.counts[from_band] += 1
            if route == QuotaReturnRoute.BOUNDARY_REVIEW:
                redelivery_identity = CaseIdentity(
                    self.owner_id,
                    affected_official_id or "",
                    self.cycle_serial,
                    self.case_serial + 100_000 + len(self.receipts),
                )
                deadline = DeadlineToken(
                    redelivery_identity,
                    NoticeState.APPEAL_OPEN.value,
                    "redelivery_appeal_expiry",
                    affected_official_id or "",
                    today + APPEAL_WINDOW_DAYS,
                )
                redelivery = RedeliveryNotice(
                    f"redelivery:{appeal_id}",
                    affected_official_id or "",
                    today,
                    deadline,
                )
        else:
            self.manager_debt[manager_id] = self.manager_debt.get(manager_id, 0) + 1
            debt_added = 1

        if sum(self.counts.values()) != self._cohort_size:
            raise AssertionError("quota return changed cohort size")
        receipt = QuotaReturnReceipt(
            appeal_id,
            route,
            tuple(sorted(before.items(), key=lambda pair: pair[0].value)),
            tuple(sorted(self.counts.items(), key=lambda pair: pair[0].value)),
            reserved_consumed,
            debt_added,
            affected_official_id,
            audit_diff,
            redelivery,
        )
        if route == QuotaReturnRoute.RESERVED_SLOT and reserved_consumed != 1:
            raise AssertionError("reserved-slot return did not consume one reserve")
        if route == QuotaReturnRoute.BOUNDARY_REVIEW and self.counts != before:
            raise AssertionError("boundary return must preserve per-band counts")
        if route == QuotaReturnRoute.NEXT_CYCLE_DEBT and debt_added != 1:
            raise AssertionError("debt return must add exactly one next-cycle debt")
        self.receipts[appeal_id] = receipt
        return QuotaReturnResult(True, route.value.lower(), receipt)

    def cure_hidden_rebalance(
        self,
        *,
        appeal_id: str,
        today: int,
    ) -> RedeliveryNotice | None:
        """Audit cure for route B: disclose and redeliver the harmed case once."""

        if appeal_id in self.cure_redeliveries:
            return None
        receipt = self.receipts.get(appeal_id)
        if (
            receipt is None
            or receipt.route != QuotaReturnRoute.HIDDEN_REBALANCE
            or not receipt.affected_official_id
        ):
            return None
        target = receipt.affected_official_id
        redelivery_identity = CaseIdentity(
            self.owner_id,
            target,
            self.cycle_serial,
            self.case_serial + 200_000 + len(self.cure_redeliveries),
        )
        notice = RedeliveryNotice(
            f"audit-cure-redelivery:{appeal_id}",
            target,
            today,
            DeadlineToken(
                redelivery_identity,
                NoticeState.APPEAL_OPEN.value,
                "audit_cure_appeal_expiry",
                target,
                today + APPEAL_WINDOW_DAYS,
            ),
        )
        self.cure_redeliveries[appeal_id] = notice
        return notice

    def consume_next_cycle_debt(self, *, manager_id: str, current_cycle: int) -> bool:
        key = (manager_id, current_cycle)
        if current_cycle != self.cycle_serial + 1 or key in self.consumed_debt:
            return False
        if self.manager_debt.get(manager_id, 0) < 1:
            return False
        self.manager_debt[manager_id] -= 1
        self.consumed_debt.add(key)
        return True


validate_b2_bindings()
