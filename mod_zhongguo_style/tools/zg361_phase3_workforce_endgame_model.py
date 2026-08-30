#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Python L0 model for the 361 workforce/endgame slice.

The model covers AB 242-253, AC 254-265, AD 266-277, and AL 355-356/
360-361.  It is an executable reference contract only: no CK3 script, GUI,
fixture-live, or production-runtime claim is made here.
"""

from __future__ import annotations

import copy
import inspect
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum, IntEnum
from typing import Callable, Final, Mapping, Sequence


READINESS: Final[str] = "python-l0-only"
BASIS_POINTS: Final[int] = 10_000


class RedCode(str, Enum):
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    STATE_CONFLICT = "state_conflict"
    COMMAND_COLLISION = "command_collision"
    DUPLICATE = "duplicate"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    HOURS_IMBALANCE = "hours_imbalance"
    HC_IMBALANCE = "hc_imbalance"
    BUDGET_IMBALANCE = "budget_imbalance"
    PROVENANCE_INVALID = "provenance_invalid"
    DEADLINE_INVALID = "deadline_invalid"
    INVARIANT_BROKEN = "invariant_broken"


class DomainRed(ValueError):
    """Stable, typed rejection raised before the live snapshot is replaced."""

    def __init__(self, code: RedCode, message: str, **context: object) -> None:
        super().__init__(message)
        self.code = code
        self.context = dict(sorted(context.items()))


def _identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainRed(
            RedCode.INVALID_VALUE,
            f"{field_name} must be a non-empty string",
            field=field_name,
        )
    return value


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DomainRed(
            RedCode.INVALID_VALUE,
            f"{field_name} must be an integer >= {minimum}",
            field=field_name,
            value=value,
        )
    return value


def _signed_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DomainRed(
            RedCode.INVALID_VALUE,
            f"{field_name} must be an integer",
            field=field_name,
            value=value,
        )
    return value


def _unique_identifiers(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    result = tuple(_identifier(value, field_name) for value in values)
    if len(set(result)) != len(result):
        raise DomainRed(RedCode.DUPLICATE, f"{field_name} contains a duplicate")
    return result


def _stable_payload(value: object) -> object:
    """Return a deterministic, hashable payload shape for replay collision checks."""

    if isinstance(value, Enum):
        return (type(value).__name__, value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return (
            type(value).__name__,
            tuple((item.name, _stable_payload(getattr(value, item.name))) for item in fields(value)),
        )
    if isinstance(value, Mapping):
        items = tuple(
            (_stable_payload(key), _stable_payload(item))
            for key, item in value.items()
        )
        return tuple(sorted(items, key=repr))
    if isinstance(value, (tuple, list, set, frozenset)):
        items = tuple(_stable_payload(item) for item in value)
        return tuple(sorted(items, key=repr)) if isinstance(value, (set, frozenset)) else items
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return repr(value)


class ActionStatus(str, Enum):
    APPLIED = "applied"
    STALE_NOOP = "stale_noop"
    IDEMPOTENT_NOOP = "idempotent_noop"


@dataclass(frozen=True)
class ActionResult:
    status: ActionStatus
    mechanism_id: int
    previous_revision: int
    current_revision: int

    @property
    def applied(self) -> bool:
        return self.status is ActionStatus.APPLIED


class Rank(IntEnum):
    BARON = 1
    COUNT = 2
    DUKE = 3
    KING = 4
    EMPEROR = 5


@dataclass(frozen=True)
class ActorRecord:
    actor_id: str
    rank: Rank
    landed: bool = True
    celestial_government: bool = True
    reviewable: bool = True
    is_top_celestial_liege: bool = False

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        if not isinstance(self.rank, Rank):
            raise DomainRed(RedCode.INVALID_TYPE, "rank must be Rank")
        if any(
            not isinstance(value, bool)
            for value in (
                self.landed,
                self.celestial_government,
                self.reviewable,
                self.is_top_celestial_liege,
            )
        ):
            raise DomainRed(RedCode.INVALID_TYPE, "actor flags must be bool")

    @property
    def can_manage(self) -> bool:
        return (
            self.rank >= Rank.DUKE
            and self.landed
            and self.celestial_government
        )


@dataclass(frozen=True)
class CommandToken:
    model_id: str
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    expected_revision: int
    actor_id: str
    command_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "model_id",
            "owner_id",
            "subject_id",
            "actor_id",
            "command_id",
        ):
            _identifier(getattr(self, field_name), field_name)
        _integer(self.cycle_serial, "cycle_serial", minimum=1)
        _integer(self.case_serial, "case_serial", minimum=1)
        _integer(self.expected_revision, "expected_revision")

    @property
    def identity_fingerprint(self) -> tuple[object, ...]:
        return (
            self.model_id,
            self.owner_id,
            self.subject_id,
            self.cycle_serial,
            self.case_serial,
            self.actor_id,
        )


@dataclass(frozen=True)
class AppliedCommand:
    mechanism_id: int
    identity_fingerprint: tuple[object, ...]
    payload_fingerprint: tuple[object, ...]


@dataclass(frozen=True)
class MechanismBinding:
    mechanism_id: int
    domain: str
    title_cn: str
    operation_key: str
    object_type: str
    trigger_hook: str
    behaviors: tuple[str, ...]
    conservation_rule: str


def _binding(
    mechanism_id: int,
    domain: str,
    title_cn: str,
    trigger_hook: str,
    behavior: str,
    conservation_rule: str,
) -> MechanismBinding:
    operation_key = {
        "AB": "apply_capacity_control",
        "AC": "apply_external_contract",
        "AD": "apply_recruitment_control",
        "AL": "apply_constitution_control",
    }[domain]
    object_type = {
        "AB": "capacity_period",
        "AC": "external_contract",
        "AD": "recruitment_funnel",
        "AL": "constitution_case",
    }[domain]
    return MechanismBinding(
        mechanism_id,
        domain,
        title_cn,
        operation_key,
        object_type,
        trigger_hook,
        (behavior,),
        conservation_rule,
    )


MECHANISM_BINDINGS: Final[dict[int, MechanismBinding]] = {
    242: _binding(242, "AB", "在场时长 / 真实成果双账", "capacity_planned", "record_presence_output_242", "presence and accepted output remain separate"),
    243: _binding(243, "AB", "非工作时段回复规则", "capacity_planned", "record_after_hours_reply_243", "only the frozen on-call rule consumes response hours"),
    244: _binding(244, "AB", "“自愿奋斗”与隐性强制", "capacity_request_open", "record_voluntary_effort_244", "refusal without a frozen duty cannot lower grade"),
    245: _binding(245, "AB", "审批加班 / 影子加班", "capacity_request_open", "record_overtime_245", "every overtime hour has approval or shadow provenance"),
    246: _binding(246, "AB", "加班金币 / 调休 / 目标减免", "capacity_decided", "settle_overtime_246", "one overtime receipt settles through exactly one route"),
    247: _binding(247, "AB", "战时冲刺的起止令", "capacity_decided", "open_sprint_247", "a sprint has a bounded start, end, goal, and roster"),
    248: _binding(248, "AB", "长期缺编反噬经理", "capacity_executed", "record_understaffing_248", "persistent overload creates manager cost rather than free output"),
    249: _binding(249, "AB", "会议工时预算", "capacity_executed", "record_meeting_249", "meeting attendee-hours consume the frozen budget"),
    250: _binding(250, "AB", "出席人数 / 决策贡献分离", "compensation_due", "record_meeting_contribution_250", "attendance never creates contribution without evidence"),
    251: _binding(251, "AB", "拒绝无效会议的政治成本", "compensation_due", "record_meeting_refusal_251", "saved time and political cost are both visible"),
    252: _binding(252, "AB", "休假与缺勤的目标归一化", "capacity_normalized", "normalize_leave_252", "leave hours and replacement credit cannot be counted twice"),
    253: _binding(253, "AB", "低绩效后的躺平反应", "capacity_normalized", "record_recovery_response_253", "minimum duty is distinct from misconduct and appeal repair"),
    254: _binding(254, "AC", "外包绕 HC", "external_need_open", "open_external_contract_254", "formal HC and shadow HC remain separate"),
    255: _binding(255, "AC", "正式 HC / 外包总成本比较", "external_need_open", "compare_workforce_tco_255", "selection uses full frozen TCO rather than purchase price"),
    256: _binding(256, "AC", "外部团队独立绩效池", "contract_type_locked", "evaluate_supplier_pool_256", "external ratings never fill the formal 361 cohort"),
    257: _binding(257, "AC", "外包转正式的有限通道", "contract_type_locked", "convert_external_worker_257", "conversion consumes one formal HC and releases one shadow HC"),
    258: _binding(258, "AC", "权限差导致的绩效校正", "supplier_selected", "freeze_controllable_scope_258", "access correction is bounded and never writes a formal grade"),
    259: _binding(259, "AC", "供应商 SLA 与个体责任分开", "supplier_selected", "allocate_sla_responsibility_259", "responsibility shares total exactly 10000 bp"),
    260: _binding(260, "AC", "人力补位 / 结果承包二种合同", "contract_active", "lock_contract_type_260", "contract type freezes who owns change and delay"),
    261: _binding(261, "AC", "多层转包与真实执行者披露", "contract_active", "disclose_executor_chain_261", "provenance is acyclic and ends at the real executor"),
    262: _binding(262, "AC", "借调人员双线评价", "delivery_due", "open_secondment_review_262", "home and host weights total 100 and cost is booked once"),
    263: _binding(263, "AC", "借调结束的返岗权", "delivery_due", "resolve_secondment_return_263", "one bounded return decision preserves prior identity"),
    264: _binding(264, "AC", "供应商退出的知识移交", "contract_resolved", "accept_knowledge_handoff_264", "holdback settles only after accepted handoff provenance"),
    265: _binding(265, "AC", "外包招聘舞弊与管理连责", "contract_resolved", "audit_external_fraud_265", "recovery and liability are evidence-bound and net-zero"),
    266: _binding(266, "AD", "招人门槛 / 空岗紧急度", "requisition_open", "open_requisition_266", "one requisition reserves exactly one formal HC"),
    267: _binding(267, "AD", "面试官先独立投票", "requisition_open", "seal_interview_votes_267", "each interviewer seals one evidence-backed vote"),
    268: _binding(268, "AD", "面试官手松手紧校准", "interview_votes_due", "calibrate_interviewers_268", "calibration preserves every raw vote"),
    269: _binding(269, "AD", "面试判断的延迟回写", "interview_votes_due", "write_back_hire_quality_269", "quality provenance updates interviewer credit, not old cases"),
    270: _binding(270, "AD", "误招 / 漏招成本偏好", "interview_calibration_due", "set_hiring_risk_policy_270", "risk policy changes threshold without rewriting votes"),
    271: _binding(271, "AD", "内推奖励与利益回避", "interview_calibration_due", "register_referral_271", "referrer is recused and reward remains conditional"),
    272: _binding(272, "AD", "Offer 职级特批", "offer_due", "issue_offer_272", "level exception has approval and immutable promise"),
    273: _binding(273, "AD", "候选人归属与“抢简历”", "offer_due", "assign_candidate_owner_273", "a candidate has one owner with transfer provenance"),
    274: _binding(274, "AD", "反 Offer 竞价上限", "offer_decided", "resolve_counteroffer_274", "one capped bid settles reserved HC and budget once"),
    275: _binding(275, "AD", "Offer 拒绝与 HC 保留期", "offer_decided", "handle_offer_refusal_275", "refusal hold expires once and returns HC/budget"),
    276: _binding(276, "AD", "离职人才回聘", "probation_due", "register_rehire_276", "old history is retained without automatic pass or wipe"),
    277: _binding(277, "AD", "PIP 退出不自动补 HC", "probation_due", "record_pip_exit_277", "exit alone never creates or returns an HC slot"),
    355: _binding(355, "AL", "高绩效目标棘轮", "multi_cycle_facts_frozen", "apply_target_ratchet_355", "old targets freeze and only repeatable excess supports a bounded ratchet"),
    356: _binding(356, "AL", "好消息雪藏与截止日套利", "multi_cycle_facts_frozen", "settle_outcome_timing_356", "one outcome is credited once by actual completion provenance"),
    360: _binding(360, "AL", "经理集体拒绝“硬背 C”", "manager_collective_action", "resolve_collective_action_360", "approved exceptions plus forced C slots conserve each cohort quota"),
    361: _binding(361, "AL", "《三六一绩效宪章》", "constitution_chartered", "adopt_charter_361", "versioned charter defaults affect future cycles only"),
}


EXPECTED_MECHANISM_IDS: Final[frozenset[int]] = frozenset(
    (*range(242, 278), 355, 356, 360, 361)
)


class WorkCategory(str, Enum):
    OUTPUT = "output"
    MEETING = "meeting"
    LEARNING = "learning"
    ON_CALL = "on_call"
    LEAVE = "leave"


class OvertimeKind(str, Enum):
    APPROVED = "approved"
    RETROACTIVE = "retroactive"
    SHADOW = "shadow"


class CompensationRoute(str, Enum):
    GOLD = "gold"
    TIME_OFF = "time_off"
    TARGET_RELIEF = "target_relief"


class ContractType(str, Enum):
    STAFF_AUGMENTATION = "staff_augmentation"
    OUTCOME = "outcome"


class ContractStatus(str, Enum):
    ACTIVE = "active"
    PENDING_CONVERSION = "pending_conversion"
    CONVERTED = "converted"
    HANDED_OFF = "handed_off"


class Vote(str, Enum):
    HIRE = "hire"
    HOLD = "hold"
    REJECT = "reject"


class RequisitionStatus(str, Enum):
    OPEN = "open"
    OFFERED = "offered"
    HIRED = "hired"
    REFUSED_HOLD = "refused_hold"
    CLOSED = "closed"


class RatchetMode(str, Enum):
    HOLD = "hold"
    LIMITED = "limited"
    PEAK = "peak"


class CharterPriority(str, Enum):
    FORCED_COMPETITION = "forced_competition"
    EVIDENCE_FAIRNESS = "evidence_fairness"
    LONG_TERM_INNOVATION = "long_term_innovation"
    ORGANIZATIONAL_WARMTH = "organizational_warmth"


class DeliveryHorizon(str, Enum):
    IMMEDIATE = "immediate"
    LONG_TERM = "long_term"


@dataclass
class BudgetLedger:
    total: int
    available: int
    reserved: int = 0
    paid: int = 0

    def validate(self) -> None:
        for field_name in ("total", "available", "reserved", "paid"):
            _integer(getattr(self, field_name), f"gold_{field_name}")
        if self.available + self.reserved + self.paid != self.total:
            raise DomainRed(RedCode.BUDGET_IMBALANCE, "gold ledger does not conserve")


@dataclass
class OvertimeRecord:
    overtime_id: str
    hours: int
    kind: OvertimeKind
    provenance_id: str
    approved_by: str | None
    compensation_id: str | None = None


@dataclass(frozen=True)
class CompensationReceipt:
    compensation_id: str
    overtime_id: str
    route: CompensationRoute
    amount: int


@dataclass
class MeetingRecord:
    meeting_id: str
    duration_hours: int
    attendees: tuple[str, ...]
    agenda_id: str
    decision_owner_id: str
    decision_id: str | None
    contributors: tuple[str, ...] = ()
    contributions_sealed: bool = False


@dataclass
class CapacityPeriod:
    period_id: str
    planned_hours: int
    meeting_budget_hours: int
    work_hours: dict[WorkCategory, int] = field(
        default_factory=lambda: {category: 0 for category in WorkCategory}
    )
    presence_hours: int = 0
    delivered_value: int = 0
    visibility_score: int = 0
    burnout_load: int = 0
    overtime: dict[str, OvertimeRecord] = field(default_factory=dict)
    compensations: dict[str, CompensationReceipt] = field(default_factory=dict)
    meetings: dict[str, MeetingRecord] = field(default_factory=dict)
    presence_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    after_hours_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    voluntary_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    sprint_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    understaffing_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    refusal_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    leave_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    recovery_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    future_time_off_hours: int = 0
    target_relief_hours: int = 0
    manager_score_cost: int = 0
    political_cost: int = 0

    @property
    def accounted_hours(self) -> int:
        return sum(self.work_hours.values())

    @property
    def overtime_capacity(self) -> int:
        return sum(item.hours for item in self.overtime.values())

    @property
    def authorized_hours(self) -> int:
        return self.planned_hours + self.overtime_capacity

    @property
    def unallocated_hours(self) -> int:
        return self.authorized_hours - self.accounted_hours

    @property
    def meeting_hours_used(self) -> int:
        return sum(
            item.duration_hours * len(item.attendees)
            for item in self.meetings.values()
        )

    def validate(self) -> None:
        _identifier(self.period_id, "period_id")
        _integer(self.planned_hours, "planned_hours", minimum=1)
        _integer(self.meeting_budget_hours, "meeting_budget_hours")
        for category in WorkCategory:
            _integer(self.work_hours.get(category), f"work_hours_{category.value}")
        if set(self.work_hours) != set(WorkCategory):
            raise DomainRed(RedCode.HOURS_IMBALANCE, "work categories are incomplete")
        if self.accounted_hours > self.authorized_hours:
            raise DomainRed(RedCode.HOURS_IMBALANCE, "recorded work exceeds capacity")
        if self.meeting_hours_used > self.meeting_budget_hours:
            raise DomainRed(RedCode.HOURS_IMBALANCE, "meeting budget exceeded")
        if any(
            not isinstance(meeting.contributions_sealed, bool)
            for meeting in self.meetings.values()
        ):
            raise DomainRed(RedCode.INVALID_TYPE, "meeting sealed flag must be bool")
        if len(set(self.compensations)) != len(self.compensations):
            raise DomainRed(RedCode.DUPLICATE, "compensation ids are duplicated")
        compensated_overtime = {
            receipt.overtime_id for receipt in self.compensations.values()
        }
        if len(compensated_overtime) != len(self.compensations):
            raise DomainRed(RedCode.DUPLICATE, "overtime was compensated twice")
        for receipt in self.compensations.values():
            if receipt.overtime_id not in self.overtime:
                raise DomainRed(RedCode.NOT_FOUND, "compensation lost overtime source")
            if self.overtime[receipt.overtime_id].compensation_id != receipt.compensation_id:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "overtime receipt link broke")


@dataclass
class ExternalContract:
    contract_id: str
    vendor_id: str
    contract_type: ContractType
    original_shadow_hc_units: int
    active_shadow_hc_units: int
    reserved_gold: int
    start_cycle: int
    sunset_cycle: int
    status: ContractStatus = ContractStatus.ACTIVE
    type_locked: bool = False
    ownership_ref: str | None = None
    change_rule_ref: str | None = None
    tco_by_route: dict[str, int] = field(default_factory=dict)
    selected_route: str | None = None
    supplier_scores: tuple[int, int, int] | None = None
    supplier_decision: str | None = None
    controllable_adjustment: int = 0
    access_evidence_ids: tuple[str, ...] = ()
    scope_frozen: bool = False
    responsibility_bps: dict[str, int] = field(default_factory=dict)
    responsibility_by_incident: dict[str, dict[str, int]] = field(default_factory=dict)
    executor_chain: tuple[str, ...] = ()
    actual_executor_id: str | None = None
    converted_official_id: str | None = None
    conversion_effective_cycle: int | None = None
    conversion_hc_reserved: bool = False
    recruitment_ref: str | None = None
    handoff_artifact_ids: tuple[str, ...] = ()
    handoff_accepted_by: str | None = None
    paid_gold: int = 0
    fraud_recovery_gold: int = 0
    liability_bps: dict[str, int] = field(default_factory=dict)

    def validate(self) -> None:
        _identifier(self.contract_id, "contract_id")
        _identifier(self.vendor_id, "vendor_id")
        if not isinstance(self.contract_type, ContractType):
            raise DomainRed(RedCode.INVALID_TYPE, "contract_type is invalid")
        if not isinstance(self.status, ContractStatus):
            raise DomainRed(RedCode.INVALID_TYPE, "contract status is invalid")
        if not isinstance(self.type_locked, bool):
            raise DomainRed(RedCode.INVALID_TYPE, "type_locked must be bool")
        if self.type_locked:
            _identifier(self.ownership_ref, "ownership_ref")
            _identifier(self.change_rule_ref, "change_rule_ref")
        if not isinstance(self.scope_frozen, bool):
            raise DomainRed(RedCode.INVALID_TYPE, "scope_frozen must be bool")
        if not isinstance(self.conversion_hc_reserved, bool):
            raise DomainRed(RedCode.INVALID_TYPE, "conversion_hc_reserved must be bool")
        _integer(self.original_shadow_hc_units, "original_shadow_hc_units", minimum=1)
        _integer(self.active_shadow_hc_units, "active_shadow_hc_units")
        if self.active_shadow_hc_units > self.original_shadow_hc_units:
            raise DomainRed(RedCode.HC_IMBALANCE, "contract gained shadow HC")
        _integer(self.reserved_gold, "reserved_gold")
        _integer(self.start_cycle, "contract_start_cycle", minimum=1)
        _integer(self.sunset_cycle, "contract_sunset_cycle", minimum=1)
        if self.sunset_cycle <= self.start_cycle:
            raise DomainRed(RedCode.DEADLINE_INVALID, "contract sunset is not future")
        _integer(self.paid_gold, "paid_gold")
        _integer(self.fraud_recovery_gold, "fraud_recovery_gold")
        if self.fraud_recovery_gold > self.paid_gold:
            raise DomainRed(RedCode.BUDGET_IMBALANCE, "fraud recovery exceeded payment")
        if self.supplier_scores is not None:
            if len(self.supplier_scores) != 3 or any(
                isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100
                for score in self.supplier_scores
            ):
                raise DomainRed(RedCode.INVALID_VALUE, "supplier scores are invalid")
        if self.responsibility_bps and sum(self.responsibility_bps.values()) != BASIS_POINTS:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "SLA responsibility does not sum to 10000")
        for incident_id, shares in self.responsibility_by_incident.items():
            _identifier(incident_id, "sla_incident_id")
            if not shares or sum(shares.values()) != BASIS_POINTS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "incident responsibility is invalid")
        if self.responsibility_by_incident:
            latest = next(reversed(self.responsibility_by_incident.values()))
            if latest != self.responsibility_bps:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "latest SLA responsibility diverged")
        if self.liability_bps and sum(self.liability_bps.values()) != BASIS_POINTS:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "fraud liability does not sum to 10000")
        if self.executor_chain:
            if len(set(self.executor_chain)) != len(self.executor_chain):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "executor chain contains a cycle")
            if self.actual_executor_id != self.executor_chain[-1]:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "executor chain lost real executor")
        if self.conversion_hc_reserved:
            _identifier(self.converted_official_id, "conversion_official_id")
            _identifier(self.recruitment_ref, "recruitment_ref")
            _integer(self.conversion_effective_cycle, "conversion_effective_cycle", minimum=1)


@dataclass
class SecondmentRecord:
    secondment_id: str
    official_id: str
    home_manager_id: str
    host_manager_id: str
    home_weight: int
    host_weight: int
    return_right: str
    start_cycle: int
    due_cycle: int
    resolved_choice: str | None = None
    extension_count: int = 0
    extension_receipts: tuple[tuple[int, int], ...] = ()


@dataclass
class Requisition:
    requisition_id: str
    role_id: str
    threshold: int
    urgency: int
    status: RequisitionStatus = RequisitionStatus.OPEN
    hc_reservation_active: bool = True
    independent_votes: dict[str, Vote] = field(default_factory=dict)
    vote_evidence: dict[str, str] = field(default_factory=dict)
    calibrated_scores: dict[str, int] = field(default_factory=dict)
    calibration_snapshot_id: str | None = None
    raw_votes_frozen: tuple[tuple[str, Vote], ...] = ()
    risk_policy: str | None = None
    policy_version_id: str | None = None
    candidate_id: str | None = None
    candidate_owner_id: str | None = None
    owner_history: tuple[str, ...] = ()
    allocation_ref: str | None = None
    scout_credit_bps: int = 0
    hiring_credit_bps: int = 0
    referral_id: str | None = None
    referrer_id: str | None = None
    referral_reward_gold: int = 0
    referral_gold_reserved: int = 0
    offer_id: str | None = None
    offered_level: int | None = None
    promised_level: int | None = None
    offer_gold_reserved: int = 0
    level_approver_id: str | None = None
    premium_end_cycle: int | None = None
    counteroffer_used: bool = False
    counteroffer_gold: int = 0
    hold_until_cycle: int | None = None
    refusal_reason: str | None = None
    hire_quality: str | None = None
    quality_evidence_ids: tuple[str, ...] = ()
    interviewer_credit: dict[str, int] = field(default_factory=dict)
    threshold_policy_frozen: bool = False
    referral_reward_paid: bool = False
    quality_written_back: bool = False

    def validate(self) -> None:
        _identifier(self.requisition_id, "requisition_id")
        _identifier(self.role_id, "role_id")
        _integer(self.threshold, "threshold")
        _integer(self.urgency, "urgency")
        if not isinstance(self.status, RequisitionStatus):
            raise DomainRed(RedCode.INVALID_TYPE, "requisition status is invalid")
        if any(not isinstance(vote, Vote) for vote in self.independent_votes.values()):
            raise DomainRed(RedCode.INVALID_TYPE, "interview vote is invalid")
        if self.raw_votes_frozen and dict(self.raw_votes_frozen) != self.independent_votes:
            raise DomainRed(RedCode.PROVENANCE_INVALID, "raw interview votes were rewritten")
        if self.calibrated_scores:
            _identifier(self.calibration_snapshot_id, "calibration_snapshot_id")
        if self.threshold_policy_frozen:
            _identifier(self.policy_version_id, "policy_version_id")
        if self.candidate_owner_id is not None:
            _identifier(self.allocation_ref, "allocation_ref")
            if self.scout_credit_bps + self.hiring_credit_bps != BASIS_POINTS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "candidate allocation credit diverged")
        if self.status is RequisitionStatus.HIRED and self.hc_reservation_active:
            raise DomainRed(RedCode.HC_IMBALANCE, "hired requisition still reserves HC")
        if (
            self.offer_gold_reserved < 0
            or self.referral_gold_reserved < 0
            or self.counteroffer_gold < 0
        ):
            raise DomainRed(RedCode.BUDGET_IMBALANCE, "offer gold cannot be negative")
        if self.referrer_id is not None and self.referrer_id in self.independent_votes:
            raise DomainRed(RedCode.PROVENANCE_INVALID, "referrer was not recused")


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    owner_id: str
    subject_id: str
    cycle_serial: int
    final_grade: str
    provenance_hash: str

    def validate(self) -> None:
        _identifier(self.case_id, "historical_case_id")
        _identifier(self.owner_id, "historical_owner_id")
        _identifier(self.subject_id, "historical_subject_id")
        _integer(self.cycle_serial, "historical_cycle_serial", minimum=1)
        _identifier(self.final_grade, "historical_final_grade")
        _identifier(self.provenance_hash, "historical_provenance_hash")


@dataclass(frozen=True)
class TargetRatchetRecord:
    ratchet_id: str
    official_id: str
    prior_cycle: int
    replicability_ref: str
    prior_target: int
    prior_actual: int
    repeatable_excess: int
    windfall_excess: int
    mode: RatchetMode
    cap_bps: int
    new_target: int
    added_resource_gold: int
    authority_ref: str | None
    underproduction_risk: int


@dataclass(frozen=True)
class OutcomeTimingRecord:
    outcome_id: str
    actual_value: int
    actual_completion_cycle: int
    report_cycle: int
    credited_cycle: int
    reported_value_by_cycle: tuple[tuple[int, int], ...]
    withheld_value: int
    evidence_timestamp_ids: tuple[str, ...]
    governance_delay_cost: int
    integrity_penalty: int


@dataclass(frozen=True)
class CollectiveActionRecord:
    collective_id: str
    quota_by_cohort: tuple[tuple[str, int], ...]
    forced_by_cohort: tuple[tuple[str, tuple[str, ...]], ...]
    exception_by_cohort: tuple[tuple[str, tuple[str, ...]], ...]
    agenda_by_cohort: tuple[tuple[str, tuple[str, ...]], ...]
    evidence_by_cohort: tuple[tuple[str, str], ...]
    exception_approval_by_cohort: tuple[tuple[str, str | None], ...]
    manager_score_cost_by_id: tuple[tuple[str, int], ...]
    effective_cycle: int | None


@dataclass(frozen=True)
class PolicyDefaults:
    delivery_horizon: DeliveryHorizon
    quota_default: str
    appeal_default: str
    bonus_default: str
    hc_default: str
    manager_accountability_default: str
    transparency_default: str

    def validate(self) -> None:
        if not isinstance(self.delivery_horizon, DeliveryHorizon):
            raise DomainRed(RedCode.INVALID_TYPE, "delivery horizon is invalid")
        for field_name in (
            "quota_default",
            "appeal_default",
            "bonus_default",
            "hc_default",
            "manager_accountability_default",
            "transparency_default",
        ):
            _identifier(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class CharterVersion:
    charter_id: str
    version: int
    adopter_id: str
    priority_order: tuple[CharterPriority, ...]
    defaults: PolicyDefaults
    completed_cycle_ids: tuple[int, ...]
    long_run_report_id: str
    adopted_day: int
    effective_cycle: int
    amendment_due_cycle: int
    previous_charter_id: str | None
    visible_costs: tuple[str, ...]


@dataclass
class Phase3WorkforceEndgameModel:
    model_id: str
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    actors: dict[str, ActorRecord]
    gold: BudgetLedger
    formal_hc_total: int
    formal_hc_available: int
    formal_hc_reserved: int
    formal_hc_filled: int
    formal_hc_vacant: int
    shadow_hc_total: int
    shadow_hc_available: int
    shadow_hc_active: int
    capacity: CapacityPeriod
    baseline_defaults: PolicyDefaults
    formal_hc_occupants: dict[str, int] = field(default_factory=dict)
    historical_cases: tuple[HistoricalCase, ...] = ()
    revision: int = 0
    applied_commands: dict[str, AppliedCommand] = field(default_factory=dict)
    mechanism_receipts: list[int] = field(default_factory=list)
    external_contracts: dict[str, ExternalContract] = field(default_factory=dict)
    secondments: dict[str, SecondmentRecord] = field(default_factory=dict)
    requisitions: dict[str, Requisition] = field(default_factory=dict)
    target_ratchets: dict[str, TargetRatchetRecord] = field(default_factory=dict)
    outcome_timings: dict[str, OutcomeTimingRecord] = field(default_factory=dict)
    collective_actions: dict[str, CollectiveActionRecord] = field(default_factory=dict)
    charters: list[CharterVersion] = field(default_factory=list)
    future_reforms: dict[int, dict[str, str]] = field(default_factory=dict)
    gold_credits: dict[str, int] = field(default_factory=dict)
    interviewer_credit: dict[str, int] = field(default_factory=dict)
    interviewer_quality_outcomes: dict[str, str] = field(default_factory=dict)
    referral_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    rehire_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    pip_exit_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    external_audit_receipts: dict[str, tuple[object, ...]] = field(default_factory=dict)
    fraud_recovery_total: int = 0
    manager_score_cost: dict[str, int] = field(default_factory=dict)
    trust_delta: int = 0

    def __post_init__(self) -> None:
        self.historical_cases = tuple(self.historical_cases)
        self._validate()

    @property
    def exact_mechanism_ids_touched(self) -> frozenset[int]:
        return frozenset(self.mechanism_receipts)

    def can_handle_own_assessment(self, actor_id: str, subject_id: str) -> bool:
        actor = self.actors.get(actor_id)
        return bool(
            actor is not None
            and actor.reviewable
            and actor.actor_id == subject_id
            and subject_id == self.subject_id
        )

    def command(
        self,
        command_id: str,
        *,
        actor_id: str | None = None,
        expected_revision: int | None = None,
    ) -> CommandToken:
        return CommandToken(
            model_id=self.model_id,
            owner_id=self.owner_id,
            subject_id=self.subject_id,
            cycle_serial=self.cycle_serial,
            case_serial=self.case_serial,
            expected_revision=self.revision if expected_revision is None else expected_revision,
            actor_id=self.owner_id if actor_id is None else actor_id,
            command_id=_identifier(command_id, "command_id"),
        )

    def defaults_for_cycle(self, cycle_serial: int) -> PolicyDefaults:
        cycle = _integer(cycle_serial, "cycle_serial", minimum=1)
        eligible = [item for item in self.charters if item.effective_cycle <= cycle]
        if not eligible:
            return self.baseline_defaults
        return max(eligible, key=lambda item: (item.effective_cycle, item.version)).defaults

    def _validate(self) -> None:
        _identifier(self.model_id, "model_id")
        _identifier(self.owner_id, "owner_id")
        _identifier(self.subject_id, "subject_id")
        _integer(self.cycle_serial, "cycle_serial", minimum=1)
        _integer(self.case_serial, "case_serial", minimum=1)
        _integer(self.revision, "revision")
        if not isinstance(self.gold, BudgetLedger):
            raise DomainRed(RedCode.INVALID_TYPE, "gold must be BudgetLedger")
        self.gold.validate()
        for payee_id, amount in self.gold_credits.items():
            _identifier(payee_id, "gold_payee_id")
            _integer(amount, "gold_credit")
        if sum(self.gold_credits.values()) != self.gold.paid:
            raise DomainRed(RedCode.BUDGET_IMBALANCE, "payer debit and payee credits diverged")
        if set(self.actors) != {actor.actor_id for actor in self.actors.values()}:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "actor registry keys are stale")
        owner = self.actors.get(self.owner_id)
        subject = self.actors.get(self.subject_id)
        if owner is None or not owner.can_manage:
            raise DomainRed(RedCode.PERMISSION_DENIED, "model owner lacks management authority")
        if subject is None or not subject.reviewable:
            raise DomainRed(RedCode.PERMISSION_DENIED, "model subject is not reviewable")
        for field_name in (
            "formal_hc_total",
            "formal_hc_available",
            "formal_hc_reserved",
            "formal_hc_filled",
            "formal_hc_vacant",
            "shadow_hc_total",
            "shadow_hc_available",
            "shadow_hc_active",
        ):
            _integer(getattr(self, field_name), field_name)
        if (
            self.formal_hc_available
            + self.formal_hc_reserved
            + self.formal_hc_filled
            + self.formal_hc_vacant
            != self.formal_hc_total
        ):
            raise DomainRed(RedCode.HC_IMBALANCE, "formal HC does not conserve")
        for occupant_id, slots in self.formal_hc_occupants.items():
            if occupant_id not in self.actors:
                raise DomainRed(RedCode.NOT_FOUND, "formal HC occupant is not a real actor")
            _integer(slots, "formal_hc_occupant_slots", minimum=1)
        if sum(self.formal_hc_occupants.values()) != self.formal_hc_filled:
            raise DomainRed(RedCode.HC_IMBALANCE, "filled HC lost occupant identity")
        if self.shadow_hc_available + self.shadow_hc_active != self.shadow_hc_total:
            raise DomainRed(RedCode.HC_IMBALANCE, "shadow HC does not conserve")
        if not isinstance(self.capacity, CapacityPeriod):
            raise DomainRed(RedCode.INVALID_TYPE, "capacity must be CapacityPeriod")
        self.capacity.validate()
        if not isinstance(self.baseline_defaults, PolicyDefaults):
            raise DomainRed(RedCode.INVALID_TYPE, "baseline defaults are invalid")
        self.baseline_defaults.validate()
        for contract in self.external_contracts.values():
            if not isinstance(contract, ExternalContract):
                raise DomainRed(RedCode.INVALID_TYPE, "external contract is invalid")
            contract.validate()
        if sum(
            contract.active_shadow_hc_units
            for contract in self.external_contracts.values()
        ) != self.shadow_hc_active:
            raise DomainRed(RedCode.HC_IMBALANCE, "active contracts and shadow HC diverged")
        reserved_contract_gold = sum(
            contract.reserved_gold for contract in self.external_contracts.values()
        )
        for secondment in self.secondments.values():
            if secondment.home_weight + secondment.host_weight != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "secondment weights must total 100")
            if secondment.home_manager_id == secondment.host_manager_id:
                raise DomainRed(RedCode.INVALID_VALUE, "secondment requires two managers")
            _identifier(secondment.secondment_id, "secondment_id")
            _identifier(secondment.official_id, "secondment_official_id")
            _integer(secondment.start_cycle, "secondment_start_cycle", minimum=1)
            _integer(secondment.due_cycle, "secondment_due_cycle", minimum=1)
            if secondment.due_cycle <= secondment.start_cycle:
                raise DomainRed(RedCode.DEADLINE_INVALID, "secondment due cycle is invalid")
            _integer(secondment.extension_count, "secondment_extension_count")
            if secondment.extension_count != len(secondment.extension_receipts):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "secondment extension receipts diverged")
        for requisition in self.requisitions.values():
            if not isinstance(requisition, Requisition):
                raise DomainRed(RedCode.INVALID_TYPE, "requisition is invalid")
            requisition.validate()
        active_requisition_reservations = sum(
            1 for item in self.requisitions.values() if item.hc_reservation_active
        )
        active_conversion_reservations = sum(
            1 for item in self.external_contracts.values() if item.conversion_hc_reserved
        )
        if active_requisition_reservations + active_conversion_reservations != self.formal_hc_reserved:
            raise DomainRed(RedCode.HC_IMBALANCE, "requisition reservations and HC diverged")
        active_roles = [
            item.role_id
            for item in self.requisitions.values()
            if item.status is not RequisitionStatus.CLOSED
        ]
        if len(active_roles) != len(set(active_roles)):
            raise DomainRed(RedCode.STATE_CONFLICT, "role has multiple active requisitions")
        active_candidates = [
            item.candidate_id
            for item in self.requisitions.values()
            if item.candidate_id is not None and item.status is not RequisitionStatus.CLOSED
        ]
        if len(active_candidates) != len(set(active_candidates)):
            raise DomainRed(RedCode.STATE_CONFLICT, "candidate has multiple active requisitions")
        reserved_offer_gold = sum(
            item.offer_gold_reserved + item.referral_gold_reserved
            for item in self.requisitions.values()
        )
        reserved_ratchet_gold = sum(
            item.added_resource_gold for item in self.target_ratchets.values()
        )
        if reserved_contract_gold + reserved_offer_gold + reserved_ratchet_gold != self.gold.reserved:
            raise DomainRed(RedCode.BUDGET_IMBALANCE, "object reservations and gold diverged")
        for command_id, receipt in self.applied_commands.items():
            _identifier(command_id, "applied_command_id")
            if not isinstance(receipt, AppliedCommand):
                raise DomainRed(RedCode.INVALID_TYPE, "applied command receipt is invalid")
        if any(item not in EXPECTED_MECHANISM_IDS for item in self.mechanism_receipts):
            raise DomainRed(RedCode.INVARIANT_BROKEN, "mechanism receipt escaped scope")
        if len({item.case_id for item in self.historical_cases}) != len(
            self.historical_cases
        ):
            raise DomainRed(RedCode.DUPLICATE, "historical case ids are duplicated")
        for historical_case in self.historical_cases:
            historical_case.validate()
        ratchet_fact_keys: set[tuple[str, int]] = set()
        for key, ratchet in self.target_ratchets.items():
            if key != ratchet.ratchet_id or ratchet.official_id not in self.actors:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "ratchet identity is invalid")
            fact_key = (ratchet.official_id, ratchet.prior_cycle)
            if fact_key in ratchet_fact_keys:
                raise DomainRed(RedCode.DUPLICATE, "ratchet facts were consumed twice")
            ratchet_fact_keys.add(fact_key)
            if ratchet.prior_cycle >= self.cycle_serial:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "ratchet uses an unclosed cycle")
            _identifier(ratchet.replicability_ref, "replicability_ref")
            if ratchet.repeatable_excess + ratchet.windfall_excess != max(
                0, ratchet.prior_actual - ratchet.prior_target
            ):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "ratchet excess changed")
        used_outcome_timestamps: set[str] = set()
        for key, outcome in self.outcome_timings.items():
            if key != outcome.outcome_id:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "outcome identity is invalid")
            if outcome.actual_completion_cycle > outcome.report_cycle:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "outcome chronology is invalid")
            if sum(dict(outcome.reported_value_by_cycle).values()) != outcome.actual_value:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "outcome value does not conserve")
            timestamps = set(outcome.evidence_timestamp_ids)
            if used_outcome_timestamps.intersection(timestamps):
                raise DomainRed(RedCode.DUPLICATE, "outcome timestamp was consumed twice")
            used_outcome_timestamps.update(timestamps)
        previous: CharterVersion | None = None
        for charter in self.charters:
            if not isinstance(charter.defaults, PolicyDefaults):
                raise DomainRed(RedCode.INVALID_TYPE, "charter defaults are invalid")
            charter.defaults.validate()
            _identifier(charter.charter_id, "charter_id")
            _identifier(charter.adopter_id, "charter_adopter_id")
            _identifier(charter.long_run_report_id, "long_run_report_id")
            _integer(charter.version, "charter_version", minimum=1)
            _integer(charter.adopted_day, "charter_adopted_day", minimum=1)
            _integer(charter.effective_cycle, "charter_effective_cycle", minimum=1)
            _integer(charter.amendment_due_cycle, "charter_amendment_due_cycle", minimum=1)
            if (
                len(charter.completed_cycle_ids) < 3
                or len(set(charter.completed_cycle_ids)) != len(charter.completed_cycle_ids)
                or any(
                    isinstance(cycle, bool) or not isinstance(cycle, int) or cycle < 1
                    for cycle in charter.completed_cycle_ids
                )
            ):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "charter cycle evidence is invalid")
            if charter.amendment_due_cycle <= charter.effective_cycle:
                raise DomainRed(RedCode.DEADLINE_INVALID, "charter amendment deadline is invalid")
            if len(charter.priority_order) != len(CharterPriority) or set(
                charter.priority_order
            ) != set(CharterPriority):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "charter priorities are incomplete")
            if not charter.visible_costs:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "charter must expose a cost")
            if previous is None:
                if charter.version != 1 or charter.previous_charter_id is not None:
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "first charter provenance is invalid")
            else:
                if (
                    charter.version != previous.version + 1
                    or charter.previous_charter_id != previous.charter_id
                    or charter.completed_cycle_ids != previous.completed_cycle_ids
                    or charter.long_run_report_id != previous.long_run_report_id
                    or charter.adopted_day <= previous.adopted_day
                    or charter.effective_cycle <= previous.effective_cycle
                ):
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "charter amendment rewrote history")
            previous = charter

    def _assert_manager(self, actor_id: str) -> None:
        actor = self.actors.get(actor_id)
        if actor is None or not actor.can_manage:
            raise DomainRed(
                RedCode.PERMISSION_DENIED,
                "only a landed celestial duke-or-higher may manage",
                actor_id=actor_id,
            )

    def _preflight(
        self,
        token: object,
        mechanism_id: int,
        payload_fingerprint: tuple[object, ...],
    ) -> ActionResult | None:
        if not isinstance(token, CommandToken):
            raise DomainRed(RedCode.INVALID_TYPE, "command must be CommandToken")
        _identifier(token.command_id, "command_id")
        applied = self.applied_commands.get(token.command_id)
        if applied is not None:
            if (
                applied.mechanism_id == mechanism_id
                and applied.identity_fingerprint == token.identity_fingerprint
                and applied.payload_fingerprint == payload_fingerprint
            ):
                return ActionResult(
                    ActionStatus.IDEMPOTENT_NOOP,
                    mechanism_id,
                    self.revision,
                    self.revision,
                )
            raise DomainRed(
                RedCode.COMMAND_COLLISION,
                "command id was used for a different operation",
                command_id=token.command_id,
            )
        if (
            token.model_id != self.model_id
            or token.owner_id != self.owner_id
            or token.subject_id != self.subject_id
            or token.cycle_serial != self.cycle_serial
            or token.case_serial != self.case_serial
            or token.expected_revision != self.revision
        ):
            return ActionResult(
                ActionStatus.STALE_NOOP,
                mechanism_id,
                self.revision,
                self.revision,
            )
        self._assert_manager(token.actor_id)
        return None

    def _atomic(
        self,
        token: object,
        mechanism_id: int,
        mutation: Callable[["Phase3WorkforceEndgameModel"], None],
    ) -> ActionResult:
        try:
            closure_payload = inspect.getclosurevars(mutation).nonlocals
            payload_fingerprint = tuple(
                sorted(
                    (name, _stable_payload(value))
                    for name, value in closure_payload.items()
                    if name != "token"
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise DomainRed(RedCode.INVALID_TYPE, "command payload is not normalizable") from exc
        noop = self._preflight(token, mechanism_id, payload_fingerprint)
        if noop is not None:
            return noop
        if not isinstance(token, CommandToken):
            raise DomainRed(RedCode.INVALID_TYPE, "command must be CommandToken")
        before_revision = self.revision
        candidate = copy.deepcopy(self)
        try:
            mutation(candidate)
            candidate.revision += 1
            candidate.applied_commands[token.command_id] = AppliedCommand(
                mechanism_id,
                token.identity_fingerprint,
                payload_fingerprint,
            )
            candidate.mechanism_receipts.append(mechanism_id)
            candidate._validate()
        except DomainRed:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise DomainRed(RedCode.INVALID_TYPE, "command payload has an invalid shape") from exc
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return ActionResult(
            ActionStatus.APPLIED,
            mechanism_id,
            before_revision,
            self.revision,
        )

    def _reserve_gold(self, amount: int) -> None:
        value = _integer(amount, "gold_amount")
        if value > self.gold.available:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "insufficient available gold")
        self.gold.available -= value
        self.gold.reserved += value

    def _credit_gold(self, recipient_id: str, amount: int) -> None:
        recipient = _identifier(recipient_id, "gold_recipient_id")
        value = _integer(amount, "gold_amount")
        self.gold_credits[recipient] = self.gold_credits.get(recipient, 0) + value

    def _pay_available_gold(self, amount: int, recipient_id: str) -> None:
        value = _integer(amount, "gold_amount")
        if value > self.gold.available:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "insufficient available gold")
        self.gold.available -= value
        self.gold.paid += value
        self._credit_gold(recipient_id, value)

    def _settle_reserved_gold(self, amount: int, recipient_id: str) -> None:
        value = _integer(amount, "gold_amount")
        if value > self.gold.reserved:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "insufficient reserved gold")
        self.gold.reserved -= value
        self.gold.paid += value
        self._credit_gold(recipient_id, value)

    def _release_reserved_gold(self, amount: int) -> None:
        value = _integer(amount, "gold_amount")
        if value > self.gold.reserved:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "insufficient reserved gold")
        self.gold.reserved -= value
        self.gold.available += value

    def _recover_paid_gold(self, amount: int, source_id: str) -> None:
        value = _integer(amount, "gold_amount")
        if value > self.gold.paid:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "recovery exceeds paid gold")
        source = _identifier(source_id, "recovery_source_id")
        source_balance = self.gold_credits.get(source, 0)
        if value > source_balance:
            raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "recovery exceeds source credit")
        self.gold.paid -= value
        self.gold.available += value
        self.gold_credits[source] = source_balance - value
        self.fraud_recovery_total += value

    def _contract(self, contract_id: str) -> ExternalContract:
        key = _identifier(contract_id, "contract_id")
        contract = self.external_contracts.get(key)
        if contract is None:
            raise DomainRed(RedCode.NOT_FOUND, "external contract not found")
        return contract

    def _requisition(self, requisition_id: str) -> Requisition:
        key = _identifier(requisition_id, "requisition_id")
        requisition = self.requisitions.get(key)
        if requisition is None:
            raise DomainRed(RedCode.NOT_FOUND, "requisition not found")
        return requisition

    # AB / 242-253 -----------------------------------------------------

    def record_presence_output_242(
        self,
        token: object,
        *,
        record_id: str,
        presence_hours: int,
        output_hours: int,
        delivered_value: int,
        reward_presence: bool,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(record_id, "record_id")
            present = _integer(presence_hours, "presence_hours")
            output = _integer(output_hours, "output_hours")
            value = _integer(delivered_value, "delivered_value")
            if not isinstance(reward_presence, bool):
                raise DomainRed(RedCode.INVALID_TYPE, "reward_presence must be bool")
            if key in candidate.capacity.presence_receipts:
                raise DomainRed(RedCode.DUPLICATE, "presence receipt already exists")
            if output > present:
                raise DomainRed(RedCode.HOURS_IMBALANCE, "output hours exceed presence")
            candidate.capacity.presence_hours += present
            candidate.capacity.work_hours[WorkCategory.OUTPUT] += output
            candidate.capacity.delivered_value += value
            if reward_presence:
                candidate.capacity.visibility_score += present
                candidate.capacity.burnout_load += max(1, present // 8)
            candidate.capacity.presence_receipts[key] = (
                present,
                output,
                value,
                reward_presence,
            )

        return self._atomic(token, 242, mutate)

    def record_after_hours_reply_243(
        self,
        token: object,
        *,
        message_id: str,
        hours: int,
        urgency: str,
        on_call: bool,
        mandatory_for_all: bool,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(message_id, "message_id")
            used = _integer(hours, "hours")
            level = _identifier(urgency, "urgency")
            if level not in {"normal", "urgent", "critical"}:
                raise DomainRed(RedCode.INVALID_VALUE, "unknown urgency")
            if not isinstance(on_call, bool) or not isinstance(mandatory_for_all, bool):
                raise DomainRed(RedCode.INVALID_TYPE, "on-call flags must be bool")
            if key in candidate.capacity.after_hours_receipts:
                raise DomainRed(RedCode.DUPLICATE, "after-hours receipt already exists")
            if level == "critical" and not (on_call or mandatory_for_all):
                raise DomainRed(
                    RedCode.STATE_CONFLICT,
                    "critical response lacks a frozen duty route",
                )
            if used and not (on_call or mandatory_for_all):
                raise DomainRed(
                    RedCode.STATE_CONFLICT,
                    "response hours lack a frozen on-call route",
                )
            if on_call or mandatory_for_all:
                candidate.capacity.work_hours[WorkCategory.ON_CALL] += used
            if mandatory_for_all:
                candidate.capacity.burnout_load += used
            candidate.capacity.after_hours_receipts[key] = (
                used,
                level,
                on_call,
                mandatory_for_all,
            )

        return self._atomic(token, 243, mutate)

    def record_voluntary_effort_244(
        self,
        token: object,
        *,
        request_id: str,
        voluntary: bool,
        written_reward_id: str | None,
        refused: bool,
        frozen_duty_id: str | None,
        completed: bool = False,
        reward_gold: int = 0,
        reward_recipient_id: str | None = None,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(request_id, "request_id")
            if any(
                not isinstance(value, bool)
                for value in (voluntary, refused, completed)
            ):
                raise DomainRed(RedCode.INVALID_TYPE, "voluntary/refused/completed must be bool")
            reward = _integer(reward_gold, "reward_gold")
            if key in candidate.capacity.voluntary_receipts:
                raise DomainRed(RedCode.DUPLICATE, "voluntary-effort receipt exists")
            if written_reward_id is not None:
                _identifier(written_reward_id, "written_reward_id")
            if frozen_duty_id is not None:
                _identifier(frozen_duty_id, "frozen_duty_id")
            if voluntary and refused:
                raise DomainRed(RedCode.INVALID_VALUE, "voluntary effort cannot be refused")
            if reward:
                if not voluntary or not completed or written_reward_id is None:
                    raise DomainRed(
                        RedCode.PROVENANCE_INVALID,
                        "voluntary reward lacks acceptance/completion/written terms",
                    )
                recipient = (
                    candidate.subject_id
                    if reward_recipient_id is None
                    else _identifier(reward_recipient_id, "reward_recipient_id")
                )
                if recipient not in candidate.actors:
                    raise DomainRed(RedCode.NOT_FOUND, "reward recipient is not a real actor")
                candidate._pay_available_gold(reward, recipient)
            else:
                recipient = None
            grade_penalty = 0
            if refused and frozen_duty_id is not None:
                grade_penalty = 1
            if not voluntary and not refused:
                candidate.capacity.manager_score_cost += 1
                candidate.capacity.burnout_load += 1
            candidate.capacity.voluntary_receipts[key] = (
                voluntary,
                written_reward_id,
                refused,
                frozen_duty_id,
                grade_penalty,
                completed,
                reward,
                recipient,
            )

        return self._atomic(token, 244, mutate)

    def record_overtime_245(
        self,
        token: object,
        *,
        overtime_id: str,
        hours: int,
        kind: OvertimeKind,
        provenance_id: str,
        approved_by: str | None,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(overtime_id, "overtime_id")
            used = _integer(hours, "hours", minimum=1)
            provenance = _identifier(provenance_id, "provenance_id")
            if not isinstance(kind, OvertimeKind):
                raise DomainRed(RedCode.INVALID_TYPE, "kind must be OvertimeKind")
            if key in candidate.capacity.overtime:
                raise DomainRed(RedCode.DUPLICATE, "overtime receipt already exists")
            if kind is OvertimeKind.SHADOW:
                if approved_by is not None:
                    raise DomainRed(RedCode.INVALID_VALUE, "shadow overtime has no approver")
                candidate.capacity.manager_score_cost += 1
            else:
                _identifier(approved_by, "approved_by")
            candidate.capacity.overtime[key] = OvertimeRecord(
                key,
                used,
                kind,
                provenance,
                approved_by,
            )
            candidate.capacity.work_hours[WorkCategory.OUTPUT] += used
            candidate.capacity.burnout_load += used

        return self._atomic(token, 245, mutate)

    def settle_overtime_246(
        self,
        token: object,
        *,
        compensation_id: str,
        overtime_id: str,
        route: CompensationRoute,
        gold_per_hour: int = 2,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(compensation_id, "compensation_id")
            overtime_key = _identifier(overtime_id, "overtime_id")
            if not isinstance(route, CompensationRoute):
                raise DomainRed(RedCode.INVALID_TYPE, "route must be CompensationRoute")
            if key in candidate.capacity.compensations:
                raise DomainRed(RedCode.DUPLICATE, "compensation receipt exists")
            overtime = candidate.capacity.overtime.get(overtime_key)
            if overtime is None:
                raise DomainRed(RedCode.NOT_FOUND, "overtime receipt not found")
            if overtime.compensation_id is not None:
                raise DomainRed(RedCode.DUPLICATE, "overtime was already compensated")
            if route is CompensationRoute.GOLD:
                rate = _integer(gold_per_hour, "gold_per_hour", minimum=1)
                amount = overtime.hours * rate
                candidate._pay_available_gold(amount, candidate.subject_id)
            elif route is CompensationRoute.TIME_OFF:
                amount = overtime.hours
                candidate.capacity.future_time_off_hours += amount
            else:
                amount = overtime.hours
                candidate.capacity.target_relief_hours += amount
            overtime.compensation_id = key
            candidate.capacity.compensations[key] = CompensationReceipt(
                key,
                overtime_key,
                route,
                amount,
            )

        return self._atomic(token, 246, mutate)

    def open_sprint_247(
        self,
        token: object,
        *,
        sprint_id: str,
        start_day: int,
        end_day: int,
        goal_id: str,
        member_ids: Sequence[str],
        renewal_approver_id: str | None = None,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(sprint_id, "sprint_id")
            start = _integer(start_day, "start_day", minimum=1)
            end = _integer(end_day, "end_day", minimum=1)
            goal = _identifier(goal_id, "goal_id")
            members = _unique_identifiers(tuple(member_ids), "member_id")
            if not members or end <= start or end - start > 30:
                raise DomainRed(RedCode.DEADLINE_INVALID, "sprint window is invalid")
            if any(member not in candidate.actors for member in members):
                raise DomainRed(RedCode.NOT_FOUND, "sprint member is not a real actor")
            if key in candidate.capacity.sprint_receipts:
                raise DomainRed(RedCode.DUPLICATE, "sprint already exists")
            if renewal_approver_id is not None:
                _identifier(renewal_approver_id, "renewal_approver_id")
            candidate.capacity.sprint_receipts[key] = (
                start,
                end,
                goal,
                members,
                renewal_approver_id,
            )
            candidate.capacity.burnout_load += len(members)

        return self._atomic(token, 247, mutate)

    def record_understaffing_248(
        self,
        token: object,
        *,
        vacancy_id: str,
        overloaded_cycles: int,
        mitigation_route: str,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(vacancy_id, "vacancy_id")
            cycles = _integer(overloaded_cycles, "overloaded_cycles", minimum=1)
            route = _identifier(mitigation_route, "mitigation_route")
            if route not in {"overtime", "reduce_scope", "request_hc", "automate"}:
                raise DomainRed(RedCode.INVALID_VALUE, "unknown understaffing route")
            if key in candidate.capacity.understaffing_receipts:
                raise DomainRed(RedCode.DUPLICATE, "understaffing receipt exists")
            manager_cost = cycles if route == "overtime" and cycles > 1 else 0
            candidate.capacity.manager_score_cost += manager_cost
            candidate.capacity.burnout_load += cycles if route == "overtime" else 0
            candidate.capacity.understaffing_receipts[key] = (
                cycles,
                route,
                manager_cost,
            )

        return self._atomic(token, 248, mutate)

    def record_meeting_249(
        self,
        token: object,
        *,
        meeting_id: str,
        duration_hours: int,
        attendee_ids: Sequence[str],
        agenda_id: str,
        decision_owner_id: str,
        decision_id: str | None,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(meeting_id, "meeting_id")
            duration = _integer(duration_hours, "duration_hours", minimum=1)
            attendees = _unique_identifiers(tuple(attendee_ids), "attendee_id")
            agenda = _identifier(agenda_id, "agenda_id")
            owner = _identifier(decision_owner_id, "decision_owner_id")
            if not attendees or owner not in attendees:
                raise DomainRed(RedCode.INVALID_VALUE, "meeting owner must attend")
            if any(attendee not in candidate.actors for attendee in attendees):
                raise DomainRed(RedCode.NOT_FOUND, "meeting attendee is not a real actor")
            candidate._assert_manager(owner)
            if decision_id is not None:
                _identifier(decision_id, "decision_id")
            if key in candidate.capacity.meetings:
                raise DomainRed(RedCode.DUPLICATE, "meeting already exists")
            attendee_hours = duration * len(attendees)
            if (
                candidate.capacity.meeting_hours_used + attendee_hours
                > candidate.capacity.meeting_budget_hours
            ):
                raise DomainRed(RedCode.HOURS_IMBALANCE, "meeting budget exceeded")
            candidate.capacity.meetings[key] = MeetingRecord(
                key,
                duration,
                attendees,
                agenda,
                owner,
                decision_id,
            )
            candidate.capacity.work_hours[WorkCategory.MEETING] += attendee_hours

        return self._atomic(token, 249, mutate)

    def record_meeting_contribution_250(
        self,
        token: object,
        *,
        meeting_id: str,
        evidence_by_contributor: Mapping[str, str],
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            meeting = candidate.capacity.meetings.get(
                _identifier(meeting_id, "meeting_id")
            )
            if meeting is None:
                raise DomainRed(RedCode.NOT_FOUND, "meeting not found")
            if meeting.contributions_sealed:
                raise DomainRed(RedCode.DUPLICATE, "meeting contributions are sealed")
            contributors = _unique_identifiers(
                tuple(evidence_by_contributor), "contributor_id"
            )
            if not set(contributors).issubset(meeting.attendees):
                raise DomainRed(RedCode.INVALID_VALUE, "contributor did not attend")
            for evidence_id in evidence_by_contributor.values():
                _identifier(evidence_id, "contribution_evidence_id")
            meeting.contributors = contributors
            meeting.contributions_sealed = True

        return self._atomic(token, 250, mutate)

    def record_meeting_refusal_251(
        self,
        token: object,
        *,
        refusal_id: str,
        meeting_id: str,
        refusing_subject_id: str,
        representative_id: str | None,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(refusal_id, "refusal_id")
            subject = _identifier(refusing_subject_id, "refusing_subject_id")
            meeting = candidate.capacity.meetings.get(
                _identifier(meeting_id, "meeting_id")
            )
            if meeting is None:
                raise DomainRed(RedCode.NOT_FOUND, "meeting not found")
            if key in candidate.capacity.refusal_receipts:
                raise DomainRed(RedCode.DUPLICATE, "meeting refusal exists")
            if subject not in meeting.attendees or subject in meeting.contributors:
                raise DomainRed(RedCode.STATE_CONFLICT, "subject cannot refuse this meeting")
            if subject == meeting.decision_owner_id:
                raise DomainRed(RedCode.STATE_CONFLICT, "decision owner must transfer ownership first")
            if representative_id is not None:
                representative = _identifier(representative_id, "representative_id")
                if representative == subject:
                    raise DomainRed(RedCode.INVALID_VALUE, "representative must differ")
                if representative not in candidate.actors:
                    raise DomainRed(RedCode.NOT_FOUND, "representative is not a real actor")
                if representative not in meeting.attendees:
                    raise DomainRed(
                        RedCode.STATE_CONFLICT,
                        "representative must already be budgeted as an attendee",
                    )
            else:
                representative = None
            meeting.attendees = tuple(item for item in meeting.attendees if item != subject)
            candidate.capacity.work_hours[WorkCategory.MEETING] -= meeting.duration_hours
            political_cost = 0 if representative is not None else 1
            candidate.capacity.political_cost += political_cost
            candidate.capacity.refusal_receipts[key] = (
                meeting.meeting_id,
                subject,
                representative,
                meeting.duration_hours,
                political_cost,
            )

        return self._atomic(token, 251, mutate)

    def normalize_leave_252(
        self,
        token: object,
        *,
        leave_id: str,
        leave_hours: int,
        original_target: int,
        replacement_credit_bps: int,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(leave_id, "leave_id")
            hours = _integer(leave_hours, "leave_hours", minimum=1)
            target = _integer(original_target, "original_target")
            replacement = _integer(
                replacement_credit_bps,
                "replacement_credit_bps",
            )
            if replacement > BASIS_POINTS:
                raise DomainRed(RedCode.INVALID_VALUE, "replacement credit exceeds 100%")
            if key in candidate.capacity.leave_receipts:
                raise DomainRed(RedCode.DUPLICATE, "leave receipt exists")
            if hours > candidate.capacity.planned_hours:
                raise DomainRed(RedCode.HOURS_IMBALANCE, "leave exceeds planned period")
            normalized_target = (
                target * (candidate.capacity.planned_hours - hours)
                // candidate.capacity.planned_hours
            )
            candidate.capacity.work_hours[WorkCategory.LEAVE] += hours
            candidate.capacity.leave_receipts[key] = (
                hours,
                target,
                normalized_target,
                replacement,
            )

        return self._atomic(token, 252, mutate)

    def record_recovery_response_253(
        self,
        token: object,
        *,
        response_id: str,
        response: str,
        minimum_duty_met: bool,
        appeal_upheld: bool,
    ) -> ActionResult:
        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(response_id, "response_id")
            route = _identifier(response, "response")
            if route not in {"recover", "minimum_duty", "transfer", "protest"}:
                raise DomainRed(RedCode.INVALID_VALUE, "unknown recovery response")
            if any(
                not isinstance(value, bool)
                for value in (minimum_duty_met, appeal_upheld)
            ):
                raise DomainRed(RedCode.INVALID_TYPE, "recovery flags must be bool")
            if key in candidate.capacity.recovery_receipts:
                raise DomainRed(RedCode.DUPLICATE, "recovery response exists")
            misconduct = route == "minimum_duty" and not minimum_duty_met
            trust_repair = 2 if appeal_upheld else 0
            if appeal_upheld:
                candidate.capacity.manager_score_cost += 1
                candidate.trust_delta += trust_repair
            candidate.capacity.recovery_receipts[key] = (
                route,
                minimum_duty_met,
                misconduct,
                appeal_upheld,
                trust_repair,
            )

        return self._atomic(token, 253, mutate)

    # AC / 254-265 -----------------------------------------------------

    def open_external_contract_254(
        self,
        token: object,
        *,
        contract_id: str,
        vendor_id: str,
        contract_type: ContractType,
        shadow_hc_units: int,
        budget_gold: int,
        sunset_cycle: int,
    ) -> ActionResult:
        """Reserve procurement gold and shadow HC without minting formal HC."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(contract_id, "contract_id")
            vendor = _identifier(vendor_id, "vendor_id")
            units = _integer(shadow_hc_units, "shadow_hc_units", minimum=1)
            budget = _integer(budget_gold, "budget_gold", minimum=1)
            sunset = _integer(sunset_cycle, "sunset_cycle", minimum=1)
            if not isinstance(contract_type, ContractType):
                raise DomainRed(RedCode.INVALID_TYPE, "contract_type must be ContractType")
            if key in candidate.external_contracts:
                raise DomainRed(RedCode.DUPLICATE, "external contract already exists")
            if sunset <= candidate.cycle_serial:
                raise DomainRed(RedCode.DEADLINE_INVALID, "contract sunset must be future")
            if units > candidate.shadow_hc_available:
                raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "insufficient shadow HC")
            candidate._reserve_gold(budget)
            candidate.shadow_hc_available -= units
            candidate.shadow_hc_active += units
            candidate.external_contracts[key] = ExternalContract(
                contract_id=key,
                vendor_id=vendor,
                contract_type=contract_type,
                original_shadow_hc_units=units,
                active_shadow_hc_units=units,
                reserved_gold=budget,
                start_cycle=candidate.cycle_serial,
                sunset_cycle=sunset,
            )

        return self._atomic(token, 254, mutate)

    def compare_workforce_tco_255(
        self,
        token: object,
        *,
        contract_id: str,
        tco_by_route: Mapping[str, int],
        selected_route: str,
    ) -> ActionResult:
        """Freeze a like-for-like formal/external/mixed total-cost comparison."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            routes = {str(key): value for key, value in tco_by_route.items()}
            if set(routes) != {"formal", "external", "mixed"}:
                raise DomainRed(RedCode.INVALID_VALUE, "TCO routes must be formal/external/mixed")
            for route, cost in routes.items():
                _identifier(route, "tco_route")
                _integer(cost, "tco_cost")
            selected = _identifier(selected_route, "selected_route")
            if contract.tco_by_route:
                raise DomainRed(RedCode.DUPLICATE, "TCO comparison is already frozen")
            expected = min(routes, key=lambda route: (routes[route], route))
            if selected != expected:
                raise DomainRed(RedCode.STATE_CONFLICT, "selected route is not minimum full TCO")
            contract.tco_by_route = routes
            contract.selected_route = selected

        return self._atomic(token, 255, mutate)

    def evaluate_supplier_pool_256(
        self,
        token: object,
        *,
        contract_id: str,
        delivery_score: int,
        quality_score: int,
        sla_score: int,
        decision: str,
    ) -> ActionResult:
        """Evaluate vendor delivery in an external-only pool."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            scores = tuple(
                _integer(value, name)
                for value, name in (
                    (delivery_score, "delivery_score"),
                    (quality_score, "quality_score"),
                    (sla_score, "sla_score"),
                )
            )
            if any(score > 100 for score in scores):
                raise DomainRed(RedCode.INVALID_VALUE, "supplier score exceeds 100")
            route = _identifier(decision, "supplier_decision")
            if route not in {"renew", "remediate", "replace"}:
                raise DomainRed(RedCode.INVALID_VALUE, "supplier decision is invalid")
            if not contract.type_locked or not contract.executor_chain:
                raise DomainRed(RedCode.STATE_CONFLICT, "supplier provenance is incomplete")
            if contract.supplier_scores is not None:
                raise DomainRed(RedCode.DUPLICATE, "supplier evaluation already exists")
            contract.supplier_scores = scores
            contract.supplier_decision = route

        return self._atomic(token, 256, mutate)

    def convert_external_worker_257(
        self,
        token: object,
        *,
        contract_id: str,
        official_id: str,
        effective_cycle: int,
        recruitment_ref: str,
    ) -> ActionResult:
        """Consume one legal formal HC and enter the person next cycle only."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            official = _identifier(official_id, "official_id")
            cycle = _integer(effective_cycle, "effective_cycle", minimum=1)
            _identifier(recruitment_ref, "recruitment_ref")
            if official not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "conversion candidate is not a real actor")
            if cycle <= candidate.cycle_serial:
                raise DomainRed(RedCode.STATE_CONFLICT, "conversion cannot alter current cohort")
            if contract.converted_official_id is not None:
                raise DomainRed(RedCode.DUPLICATE, "contract already converted a worker")
            if contract.supplier_scores is None or contract.active_shadow_hc_units < 1:
                raise DomainRed(RedCode.STATE_CONFLICT, "conversion lacks verified delivery")
            if candidate.formal_hc_available < 1:
                raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "no formal HC is available")
            pending_or_filled = set(candidate.formal_hc_occupants)
            pending_or_filled.update(
                item.converted_official_id
                for item in candidate.external_contracts.values()
                if item.conversion_hc_reserved and item.converted_official_id is not None
            )
            pending_or_filled.update(
                item.candidate_id
                for item in candidate.requisitions.values()
                if item.candidate_id is not None and item.status is not RequisitionStatus.CLOSED
            )
            if official in pending_or_filled:
                raise DomainRed(RedCode.STATE_CONFLICT, "official already has formal or pending HC")
            candidate.formal_hc_available -= 1
            candidate.formal_hc_reserved += 1
            contract.converted_official_id = official
            contract.conversion_effective_cycle = cycle
            contract.conversion_hc_reserved = True
            contract.recruitment_ref = recruitment_ref
            contract.status = ContractStatus.PENDING_CONVERSION

        return self._atomic(token, 257, mutate)

    def settle_external_conversion_257(
        self,
        token: object,
        *,
        contract_id: str,
    ) -> ActionResult:
        """Settle a #257 reservation only in its authoritative effective cycle."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            if not contract.conversion_hc_reserved:
                raise DomainRed(RedCode.STATE_CONFLICT, "contract has no pending conversion")
            if contract.conversion_effective_cycle is None or candidate.cycle_serial < contract.conversion_effective_cycle:
                raise DomainRed(RedCode.DEADLINE_INVALID, "conversion is not effective yet")
            official = contract.converted_official_id
            if official is None or official in candidate.formal_hc_occupants:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "conversion identity is invalid")
            if contract.active_shadow_hc_units < 1:
                raise DomainRed(RedCode.HC_IMBALANCE, "conversion lost shadow HC")
            candidate.formal_hc_reserved -= 1
            candidate.formal_hc_filled += 1
            candidate.formal_hc_occupants[official] = 1
            candidate.shadow_hc_active -= 1
            candidate.shadow_hc_available += 1
            contract.active_shadow_hc_units -= 1
            contract.conversion_hc_reserved = False
            contract.status = ContractStatus.CONVERTED

        return self._atomic(token, 257, mutate)

    def freeze_controllable_scope_258(
        self,
        token: object,
        *,
        contract_id: str,
        missing_access_ids: Sequence[str],
        target_adjustment: int,
    ) -> ActionResult:
        """Freeze access limits and bounded target adjustment without a grade write."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            missing = _unique_identifiers(tuple(missing_access_ids), "access_id")
            adjustment = _integer(target_adjustment, "target_adjustment")
            if adjustment > 100:
                raise DomainRed(RedCode.INVALID_VALUE, "target adjustment exceeds 100")
            if contract.scope_frozen:
                raise DomainRed(RedCode.DUPLICATE, "controllable scope is already frozen")
            if adjustment and not missing:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "adjustment lacks missing access")
            contract.access_evidence_ids = missing
            contract.controllable_adjustment = adjustment
            contract.scope_frozen = True

        return self._atomic(token, 258, mutate)

    def allocate_sla_responsibility_259(
        self,
        token: object,
        *,
        contract_id: str,
        incident_id: str,
        responsibility_bps: Mapping[str, int],
    ) -> ActionResult:
        """Allocate one incident across contract/change/vendor/executor layers."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            _identifier(incident_id, "incident_id")
            shares = dict(responsibility_bps)
            allowed = {"contract", "client_change", "vendor_management", "executor"}
            if not shares or not set(shares).issubset(allowed):
                raise DomainRed(RedCode.INVALID_VALUE, "responsibility layer is invalid")
            for layer, share in shares.items():
                _identifier(layer, "responsibility_layer")
                _integer(share, "responsibility_bps")
            if sum(shares.values()) != BASIS_POINTS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "responsibility must total 10000 bp")
            if incident_id in contract.responsibility_by_incident:
                raise DomainRed(RedCode.DUPLICATE, "SLA incident was already allocated")
            contract.responsibility_by_incident[incident_id] = shares
            contract.responsibility_bps = shares

        return self._atomic(token, 259, mutate)

    def lock_contract_type_260(
        self,
        token: object,
        *,
        contract_id: str,
        contract_type: ContractType,
        ownership_ref: str,
        change_rule_ref: str,
    ) -> ActionResult:
        """Freeze labor versus outcome terms before activation/delivery."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            if not isinstance(contract_type, ContractType):
                raise DomainRed(RedCode.INVALID_TYPE, "contract_type must be ContractType")
            _identifier(ownership_ref, "ownership_ref")
            _identifier(change_rule_ref, "change_rule_ref")
            if contract.type_locked:
                raise DomainRed(RedCode.DUPLICATE, "contract type is already frozen")
            if contract.supplier_scores is not None or contract.paid_gold:
                raise DomainRed(RedCode.STATE_CONFLICT, "contract type cannot change after delivery")
            if contract.contract_type is not contract_type:
                raise DomainRed(RedCode.STATE_CONFLICT, "contract type differs from opened terms")
            contract.type_locked = True
            contract.ownership_ref = ownership_ref
            contract.change_rule_ref = change_rule_ref

        return self._atomic(token, 260, mutate)

    def disclose_executor_chain_261(
        self,
        token: object,
        *,
        contract_id: str,
        executor_chain: Sequence[str],
        actual_executor_id: str,
    ) -> ActionResult:
        """Freeze an acyclic subcontract chain ending at the real executor."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            chain = _unique_identifiers(tuple(executor_chain), "executor_id")
            actual = _identifier(actual_executor_id, "actual_executor_id")
            if not chain or chain[0] != contract.vendor_id or chain[-1] != actual:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "executor chain endpoints are invalid")
            if contract.executor_chain:
                raise DomainRed(RedCode.DUPLICATE, "executor chain is already frozen")
            if not contract.type_locked:
                raise DomainRed(RedCode.STATE_CONFLICT, "contract type must be frozen first")
            contract.executor_chain = chain
            contract.actual_executor_id = actual

        return self._atomic(token, 261, mutate)

    def open_secondment_review_262(
        self,
        token: object,
        *,
        secondment_id: str,
        official_id: str,
        home_manager_id: str,
        host_manager_id: str,
        home_weight: int,
        host_weight: int,
        due_cycle: int,
        return_right: str,
    ) -> ActionResult:
        """Freeze dual-line weights and a bounded return term at start."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(secondment_id, "secondment_id")
            official = _identifier(official_id, "official_id")
            home = _identifier(home_manager_id, "home_manager_id")
            host = _identifier(host_manager_id, "host_manager_id")
            home_share = _integer(home_weight, "home_weight")
            host_share = _integer(host_weight, "host_weight")
            due = _integer(due_cycle, "due_cycle", minimum=1)
            right = _identifier(return_right, "return_right")
            if key in candidate.secondments:
                raise DomainRed(RedCode.DUPLICATE, "secondment already exists")
            if official not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "seconded official not found")
            if home not in candidate.actors or host not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "secondment manager not found")
            candidate._assert_manager(home)
            candidate._assert_manager(host)
            if home == host or home_share + host_share != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "secondment weights must total 100")
            if due <= candidate.cycle_serial:
                raise DomainRed(RedCode.DEADLINE_INVALID, "secondment due cycle must be future")
            if right not in {"original_role", "equivalent_role", "permanent_option"}:
                raise DomainRed(RedCode.INVALID_VALUE, "return right is invalid")
            candidate.secondments[key] = SecondmentRecord(
                key,
                official,
                home,
                host,
                home_share,
                host_share,
                right,
                candidate.cycle_serial,
                due,
            )

        return self._atomic(token, 262, mutate)

    def resolve_secondment_return_263(
        self,
        token: object,
        *,
        secondment_id: str,
        choice: str,
        as_of_cycle: int,
        extension_due_cycle: int | None = None,
    ) -> ActionResult:
        """Make one due return/extension/permanent decision without cloning HC."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(secondment_id, "secondment_id")
            record = candidate.secondments.get(key)
            if record is None:
                raise DomainRed(RedCode.NOT_FOUND, "secondment not found")
            route = _identifier(choice, "secondment_choice")
            current = _integer(as_of_cycle, "as_of_cycle", minimum=1)
            if current != candidate.cycle_serial:
                raise DomainRed(RedCode.STATE_CONFLICT, "secondment clock is not authoritative")
            if record.resolved_choice is not None:
                raise DomainRed(RedCode.DUPLICATE, "secondment choice already resolved")
            if current < record.due_cycle:
                raise DomainRed(RedCode.DEADLINE_INVALID, "secondment is not due")
            if route not in {"return", "extend", "permanent"}:
                raise DomainRed(RedCode.INVALID_VALUE, "secondment choice is invalid")
            if route == "extend":
                if record.extension_count >= 1:
                    raise DomainRed(RedCode.DUPLICATE, "secondment extension is one-shot")
                extension = _integer(extension_due_cycle, "extension_due_cycle", minimum=1)
                if extension <= current:
                    raise DomainRed(RedCode.DEADLINE_INVALID, "extension must be future")
                previous_due = record.due_cycle
                record.due_cycle = extension
                record.extension_count += 1
                record.extension_receipts = record.extension_receipts + (
                    (previous_due, extension),
                )
                return
            elif route == "permanent":
                if record.official_id not in candidate.formal_hc_occupants:
                    if candidate.formal_hc_available < 1:
                        raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "permanent transfer lacks HC")
                    candidate.formal_hc_available -= 1
                    candidate.formal_hc_filled += 1
                    candidate.formal_hc_occupants[record.official_id] = 1
            record.resolved_choice = route

        return self._atomic(token, 263, mutate)

    def accept_knowledge_handoff_264(
        self,
        token: object,
        *,
        contract_id: str,
        artifact_ids: Sequence[str],
        accepted_by: str,
        as_of_cycle: int,
        early_exit_waiver_ref: str | None = None,
    ) -> ActionResult:
        """Release final payment and shadow capacity only after accepted artifacts."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            contract = candidate._contract(contract_id)
            artifacts = _unique_identifiers(tuple(artifact_ids), "handoff_artifact_id")
            accepter = _identifier(accepted_by, "accepted_by")
            candidate._assert_manager(accepter)
            current = _integer(as_of_cycle, "as_of_cycle", minimum=1)
            required_artifacts = {"documentation", "shadowing", "practical_acceptance"}
            if not required_artifacts.issubset(artifacts):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "handoff milestones are incomplete")
            if current != candidate.cycle_serial:
                raise DomainRed(RedCode.STATE_CONFLICT, "handoff clock is not authoritative")
            if current < contract.sunset_cycle:
                _identifier(early_exit_waiver_ref, "early_exit_waiver_ref")
            if contract.handoff_artifact_ids or contract.paid_gold:
                raise DomainRed(RedCode.DUPLICATE, "handoff already settled")
            if contract.conversion_hc_reserved:
                raise DomainRed(RedCode.STATE_CONFLICT, "pending conversion must settle before handoff")
            if contract.supplier_scores is None:
                raise DomainRed(RedCode.STATE_CONFLICT, "delivery was not evaluated")
            payment = contract.reserved_gold
            candidate._settle_reserved_gold(payment, contract.vendor_id)
            contract.reserved_gold = 0
            contract.paid_gold = payment
            candidate.shadow_hc_active -= contract.active_shadow_hc_units
            candidate.shadow_hc_available += contract.active_shadow_hc_units
            contract.active_shadow_hc_units = 0
            contract.handoff_artifact_ids = artifacts
            contract.handoff_accepted_by = accepter
            contract.status = ContractStatus.HANDED_OFF

        return self._atomic(token, 264, mutate)

    def audit_external_fraud_265(
        self,
        token: object,
        *,
        audit_id: str,
        contract_id: str,
        evidence_ids: Sequence[str],
        liability_bps: Mapping[str, int],
        recovery_gold: int,
        duty_evidence_by_actor: Mapping[str, str],
    ) -> ActionResult:
        """Recover only proven vendor proceeds and freeze manager liability shares."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            audit = _identifier(audit_id, "audit_id")
            contract = candidate._contract(contract_id)
            evidence = _unique_identifiers(tuple(evidence_ids), "fraud_evidence_id")
            shares = dict(liability_bps)
            duty_evidence = dict(duty_evidence_by_actor)
            recovery = _integer(recovery_gold, "recovery_gold")
            if audit in candidate.external_audit_receipts:
                raise DomainRed(RedCode.DUPLICATE, "fraud audit already exists")
            if not evidence or not shares:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "fraud audit lacks evidence/liability")
            for actor_id, share in shares.items():
                _identifier(actor_id, "liable_actor_id")
                _integer(share, "liability_bps")
                if actor_id != contract.vendor_id:
                    actor = candidate.actors.get(actor_id)
                    if actor is None or not actor.can_manage:
                        raise DomainRed(RedCode.PERMISSION_DENIED, "liable manager is not authorized")
                    _identifier(duty_evidence.get(actor_id), "manager_duty_evidence_id")
            if set(duty_evidence) != set(shares) - {contract.vendor_id}:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "manager duty evidence population diverged")
            if sum(shares.values()) != BASIS_POINTS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "liability must total 10000 bp")
            if recovery > contract.paid_gold - contract.fraud_recovery_gold:
                raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "recovery exceeds unsettled proceeds")
            candidate._recover_paid_gold(recovery, contract.vendor_id)
            contract.fraud_recovery_gold += recovery
            contract.liability_bps = shares
            candidate.external_audit_receipts[audit] = (
                contract.contract_id,
                evidence,
                tuple(sorted(shares.items())),
                tuple(sorted(duty_evidence.items())),
                recovery,
            )

        return self._atomic(token, 265, mutate)

    # AD / 266-277 -----------------------------------------------------

    def open_requisition_266(
        self,
        token: object,
        *,
        requisition_id: str,
        role_id: str,
        threshold: int,
        urgency: int,
    ) -> ActionResult:
        """Open one real vacancy and reserve exactly one formal HC slot."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(requisition_id, "requisition_id")
            role = _identifier(role_id, "role_id")
            bar = _integer(threshold, "threshold")
            urgent = _integer(urgency, "urgency")
            if bar > 100 or urgent > 100:
                raise DomainRed(RedCode.INVALID_VALUE, "threshold/urgency exceeds 100")
            if key in candidate.requisitions:
                raise DomainRed(RedCode.DUPLICATE, "requisition already exists")
            if any(
                item.role_id == role and item.status is not RequisitionStatus.CLOSED
                for item in candidate.requisitions.values()
            ):
                raise DomainRed(RedCode.STATE_CONFLICT, "role already has an active requisition")
            if candidate.formal_hc_available < 1:
                raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "no formal HC is available")
            candidate.formal_hc_available -= 1
            candidate.formal_hc_reserved += 1
            candidate.requisitions[key] = Requisition(key, role, bar, urgent)

        return self._atomic(token, 266, mutate)

    def seal_interview_votes_267(
        self,
        token: object,
        *,
        requisition_id: str,
        candidate_id: str,
        votes: Mapping[str, Vote],
        evidence_by_interviewer: Mapping[str, str],
    ) -> ActionResult:
        """Seal independent votes and evidence before any calibration."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            candidate_key = _identifier(candidate_id, "candidate_id")
            sealed = dict(votes)
            evidence = dict(evidence_by_interviewer)
            if requisition.status is not RequisitionStatus.OPEN:
                raise DomainRed(RedCode.STATE_CONFLICT, "requisition is not open")
            if candidate_key not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "candidate is not a real actor")
            if requisition.independent_votes:
                raise DomainRed(RedCode.DUPLICATE, "interview votes are already sealed")
            if not sealed or set(sealed) != set(evidence):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "each vote needs one evidence source")
            if requisition.candidate_id not in {None, candidate_key}:
                raise DomainRed(RedCode.STATE_CONFLICT, "requisition candidate changed")
            if requisition.referrer_id in sealed:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "referrer must be recused")
            for interviewer_id, vote in sealed.items():
                interviewer = candidate.actors.get(_identifier(interviewer_id, "interviewer_id"))
                if interviewer is None or not interviewer.can_manage:
                    raise DomainRed(RedCode.PERMISSION_DENIED, "interviewer lacks authority")
                if not isinstance(vote, Vote):
                    raise DomainRed(RedCode.INVALID_TYPE, "vote must be Vote")
                _identifier(evidence[interviewer_id], "vote_evidence_id")
            requisition.candidate_id = candidate_key
            requisition.independent_votes = sealed
            requisition.vote_evidence = evidence
            requisition.raw_votes_frozen = tuple(sorted(sealed.items()))

        return self._atomic(token, 267, mutate)

    def calibrate_interviewers_268(
        self,
        token: object,
        *,
        requisition_id: str,
        normalized_adjustments: Mapping[str, int],
        calibration_snapshot_id: str,
    ) -> ActionResult:
        """Apply bounded interviewer adjustments while preserving raw votes."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            _identifier(calibration_snapshot_id, "calibration_snapshot_id")
            adjustments = dict(normalized_adjustments)
            if not requisition.raw_votes_frozen:
                raise DomainRed(RedCode.STATE_CONFLICT, "raw votes are not sealed")
            if requisition.calibrated_scores:
                raise DomainRed(RedCode.DUPLICATE, "interviewer calibration already exists")
            if set(adjustments) != set(requisition.independent_votes):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "calibration population changed")
            for interviewer_id, adjustment in adjustments.items():
                _identifier(interviewer_id, "interviewer_id")
                value = _signed_integer(adjustment, "normalized_adjustment")
                if not -20 <= value <= 20:
                    raise DomainRed(RedCode.INVALID_VALUE, "calibration adjustment exceeds cap")
            requisition.calibrated_scores = adjustments
            requisition.calibration_snapshot_id = calibration_snapshot_id

        return self._atomic(token, 268, mutate)

    def write_back_hire_quality_269(
        self,
        token: object,
        *,
        requisition_id: str,
        outcome_id: str,
        quality: str,
        evidence_ids: Sequence[str],
        attribution_bps: Mapping[str, int],
        observed_cycle: int,
    ) -> ActionResult:
        """Settle a delayed hire outcome once; never rewrite the sealed votes."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            outcome = _identifier(outcome_id, "outcome_id")
            result = _identifier(quality, "quality")
            evidence = _unique_identifiers(tuple(evidence_ids), "quality_evidence_id")
            shares = dict(attribution_bps)
            observed = _integer(observed_cycle, "observed_cycle", minimum=1)
            if requisition.status is not RequisitionStatus.HIRED:
                raise DomainRed(RedCode.STATE_CONFLICT, "quality writeback requires a hire")
            if requisition.quality_written_back:
                raise DomainRed(RedCode.DUPLICATE, "hire quality is already final")
            if observed <= candidate.cycle_serial:
                raise DomainRed(RedCode.DEADLINE_INVALID, "quality outcome is not delayed")
            if outcome in candidate.interviewer_quality_outcomes:
                raise DomainRed(RedCode.DUPLICATE, "quality outcome was already written back")
            if result not in {"pass", "mismatch", "attrition", "excluded"}:
                raise DomainRed(RedCode.INVALID_VALUE, "hire quality is invalid")
            if not evidence:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "quality writeback lacks evidence")
            if result == "excluded":
                if shares:
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "excluded outcome cannot assign blame")
            else:
                if not shares or not set(shares).issubset(requisition.independent_votes):
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "attribution escaped frozen interviewers")
                for share in shares.values():
                    _integer(share, "attribution_bps")
                if sum(shares.values()) != BASIS_POINTS:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "attribution must total 10000 bp")
            direction = 1 if result == "pass" else -1
            for interviewer_id, share in shares.items():
                delta = direction * share
                candidate.interviewer_credit[interviewer_id] = (
                    candidate.interviewer_credit.get(interviewer_id, 0) + delta
                )
                requisition.interviewer_credit[interviewer_id] = (
                    requisition.interviewer_credit.get(interviewer_id, 0) + delta
                )
            if result == "pass" and requisition.referral_gold_reserved:
                reward = requisition.referral_gold_reserved
                if requisition.referrer_id is None:
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "referral reward lost referrer")
                candidate._settle_reserved_gold(reward, requisition.referrer_id)
                requisition.referral_gold_reserved = 0
                requisition.referral_reward_paid = True
            elif result != "pass" and requisition.referral_gold_reserved:
                reward = requisition.referral_gold_reserved
                candidate._release_reserved_gold(reward)
                requisition.referral_gold_reserved = 0
            requisition.hire_quality = result
            requisition.quality_evidence_ids = evidence
            requisition.quality_written_back = True
            candidate.interviewer_quality_outcomes[outcome] = requisition.requisition_id

        return self._atomic(token, 269, mutate)

    def set_hiring_risk_policy_270(
        self,
        token: object,
        *,
        requisition_id: str,
        role_class: str,
        policy: str,
        threshold: int,
        policy_version_id: str,
    ) -> ActionResult:
        """Freeze the vacancy risk preference before an offer result exists."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            role = _identifier(role_class, "role_class")
            route = _identifier(policy, "risk_policy")
            bar = _integer(threshold, "threshold")
            _identifier(policy_version_id, "policy_version_id")
            if role not in {"critical", "growth", "routine"}:
                raise DomainRed(RedCode.INVALID_VALUE, "role class is invalid")
            if route not in {"conservative", "open", "balanced"} or bar > 100:
                raise DomainRed(RedCode.INVALID_VALUE, "risk policy is invalid")
            if requisition.threshold_policy_frozen or requisition.status is not RequisitionStatus.OPEN:
                raise DomainRed(RedCode.STATE_CONFLICT, "threshold cannot change after result")
            requisition.risk_policy = f"{role}:{route}"
            requisition.threshold = bar
            requisition.threshold_policy_frozen = True
            requisition.policy_version_id = policy_version_id

        return self._atomic(token, 270, mutate)

    def register_referral_271(
        self,
        token: object,
        *,
        requisition_id: str,
        referral_id: str,
        candidate_id: str,
        referrer_id: str,
        relationship_ref: str,
        reward_gold: int,
    ) -> ActionResult:
        """Reserve a conditional reward and enforce final-vote recusal."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            referral = _identifier(referral_id, "referral_id")
            referred = _identifier(candidate_id, "candidate_id")
            referrer = _identifier(referrer_id, "referrer_id")
            relationship = _identifier(relationship_ref, "relationship_ref")
            reward = _integer(reward_gold, "reward_gold")
            if referral in candidate.referral_receipts or requisition.referral_id is not None:
                raise DomainRed(RedCode.DUPLICATE, "referral already exists")
            if (
                requisition.status is not RequisitionStatus.OPEN
                or requisition.raw_votes_frozen
                or requisition.quality_written_back
            ):
                raise DomainRed(RedCode.STATE_CONFLICT, "referral must be frozen before voting")
            if referrer == referred:
                raise DomainRed(RedCode.INVALID_VALUE, "candidate cannot refer self")
            if referred not in candidate.actors or referrer not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "referral identity not found")
            if requisition.candidate_id not in {None, referred}:
                raise DomainRed(RedCode.STATE_CONFLICT, "referral candidate changed")
            if referrer in requisition.independent_votes:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "referrer already cast a vote")
            if reward:
                candidate._reserve_gold(reward)
            requisition.candidate_id = referred
            requisition.referral_id = referral
            requisition.referrer_id = referrer
            requisition.referral_reward_gold = reward
            requisition.referral_gold_reserved = reward
            candidate.referral_receipts[referral] = (
                requisition.requisition_id,
                referred,
                referrer,
                relationship,
                reward,
            )

        return self._atomic(token, 271, mutate)

    def issue_offer_272(
        self,
        token: object,
        *,
        requisition_id: str,
        offer_id: str,
        requested_level: int,
        band_min: int,
        band_max: int,
        signing_gold: int,
        exception_approver_id: str | None = None,
        premium_end_cycle: int | None = None,
    ) -> ActionResult:
        """Freeze one level/price promise; out-of-band terms require approval."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            offer = _identifier(offer_id, "offer_id")
            level = _integer(requested_level, "requested_level", minimum=1)
            low = _integer(band_min, "band_min", minimum=1)
            high = _integer(band_max, "band_max", minimum=1)
            gold = _integer(signing_gold, "signing_gold")
            if low > high:
                raise DomainRed(RedCode.INVALID_VALUE, "offer band is inverted")
            if requisition.offer_id is not None:
                raise DomainRed(RedCode.DUPLICATE, "offer already exists")
            if requisition.candidate_id is None or requisition.candidate_owner_id is None:
                raise DomainRed(RedCode.STATE_CONFLICT, "candidate ownership is not frozen")
            if not requisition.raw_votes_frozen or not requisition.calibrated_scores:
                raise DomainRed(RedCode.STATE_CONFLICT, "offer lacks interview provenance")
            approver: str | None = None
            if not low <= level <= high:
                approver = _identifier(exception_approver_id, "exception_approver_id")
                candidate._assert_manager(approver)
            if premium_end_cycle is not None:
                premium_end = _integer(premium_end_cycle, "premium_end_cycle", minimum=1)
                if premium_end <= candidate.cycle_serial:
                    raise DomainRed(RedCode.DEADLINE_INVALID, "premium expiry must be future")
            else:
                premium_end = None
            if gold:
                candidate._reserve_gold(gold)
            requisition.offer_id = offer
            requisition.offered_level = level
            requisition.promised_level = level
            requisition.offer_gold_reserved = gold
            requisition.level_approver_id = approver
            requisition.premium_end_cycle = premium_end
            requisition.status = RequisitionStatus.OFFERED

        return self._atomic(token, 272, mutate)

    def assign_candidate_owner_273(
        self,
        token: object,
        *,
        requisition_id: str,
        candidate_id: str,
        owner_id: str,
        allocation_ref: str,
        scout_credit_bps: int,
        hiring_credit_bps: int,
    ) -> ActionResult:
        """Bind a real candidate to one owner with conserved sourcing credit."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            person = _identifier(candidate_id, "candidate_id")
            owner = _identifier(owner_id, "candidate_owner_id")
            _identifier(allocation_ref, "allocation_ref")
            scout = _integer(scout_credit_bps, "scout_credit_bps")
            hiring = _integer(hiring_credit_bps, "hiring_credit_bps")
            if person not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "candidate is not a real actor")
            if person in candidate.formal_hc_occupants or any(
                contract.conversion_hc_reserved
                and contract.converted_official_id == person
                for contract in candidate.external_contracts.values()
            ):
                raise DomainRed(RedCode.STATE_CONFLICT, "candidate already has formal or pending HC")
            candidate._assert_manager(owner)
            if scout + hiring != BASIS_POINTS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "candidate credit must total 10000 bp")
            if requisition.candidate_id not in {None, person}:
                raise DomainRed(RedCode.STATE_CONFLICT, "candidate identity changed")
            if requisition.candidate_owner_id is not None:
                raise DomainRed(RedCode.DUPLICATE, "candidate owner is already frozen")
            for other in candidate.requisitions.values():
                if (
                    other.requisition_id != requisition.requisition_id
                    and other.candidate_id == person
                    and other.status is not RequisitionStatus.CLOSED
                ):
                    raise DomainRed(RedCode.STATE_CONFLICT, "candidate has another active offer/hire")
            requisition.candidate_id = person
            requisition.candidate_owner_id = owner
            requisition.owner_history = (owner,)
            requisition.allocation_ref = allocation_ref
            requisition.scout_credit_bps = scout
            requisition.hiring_credit_bps = hiring

        return self._atomic(token, 273, mutate)

    def resolve_counteroffer_274(
        self,
        token: object,
        *,
        requisition_id: str,
        competitor_terms_ref: str,
        additional_gold: int,
        fairness_cap_gold: int,
    ) -> ActionResult:
        """Make one capped counteroffer, then settle offer gold and the HC slot."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            _identifier(competitor_terms_ref, "competitor_terms_ref")
            increment = _integer(additional_gold, "additional_gold")
            cap = _integer(fairness_cap_gold, "fairness_cap_gold")
            if requisition.status is not RequisitionStatus.OFFERED:
                raise DomainRed(RedCode.STATE_CONFLICT, "counteroffer requires an open offer")
            if requisition.counteroffer_used:
                raise DomainRed(RedCode.DUPLICATE, "counteroffer is one-shot")
            if increment > cap:
                raise DomainRed(RedCode.INVALID_VALUE, "counteroffer exceeds fairness cap")
            if increment:
                candidate._reserve_gold(increment)
                requisition.offer_gold_reserved += increment
            settlement = requisition.offer_gold_reserved
            if requisition.candidate_id is None:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "offer lost candidate")
            candidate._settle_reserved_gold(settlement, requisition.candidate_id)
            requisition.offer_gold_reserved = 0
            requisition.counteroffer_gold = increment
            requisition.counteroffer_used = True
            candidate.formal_hc_reserved -= 1
            candidate.formal_hc_filled += 1
            candidate.formal_hc_occupants[requisition.candidate_id] = (
                candidate.formal_hc_occupants.get(requisition.candidate_id, 0) + 1
            )
            requisition.hc_reservation_active = False
            requisition.status = RequisitionStatus.HIRED

        return self._atomic(token, 274, mutate)

    def handle_offer_refusal_275(
        self,
        token: object,
        *,
        requisition_id: str,
        as_of_cycle: int,
        hold_until_cycle: int | None = None,
        refusal_reason: str | None = None,
        runner_up_id: str | None = None,
    ) -> ActionResult:
        """Hold, then reopen/release the same HC slot; a hold is never consumption."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            requisition = candidate._requisition(requisition_id)
            current = _integer(as_of_cycle, "as_of_cycle", minimum=1)
            if current != candidate.cycle_serial:
                raise DomainRed(RedCode.STATE_CONFLICT, "HC hold clock is not authoritative")
            if requisition.status is RequisitionStatus.OFFERED:
                due = _integer(hold_until_cycle, "hold_until_cycle", minimum=1)
                reason = _identifier(refusal_reason, "refusal_reason")
                if due <= current:
                    raise DomainRed(RedCode.DEADLINE_INVALID, "HC hold must end in the future")
                release = requisition.offer_gold_reserved + requisition.referral_gold_reserved
                if release:
                    candidate._release_reserved_gold(release)
                requisition.offer_gold_reserved = 0
                requisition.referral_gold_reserved = 0
                requisition.hold_until_cycle = due
                requisition.refusal_reason = reason
                requisition.status = RequisitionStatus.REFUSED_HOLD
                return
            if requisition.status is not RequisitionStatus.REFUSED_HOLD:
                raise DomainRed(RedCode.STATE_CONFLICT, "requisition has no refused HC hold")
            if requisition.hold_until_cycle is None:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "HC hold lost deadline")
            if current < requisition.hold_until_cycle:
                raise DomainRed(RedCode.DEADLINE_INVALID, "HC hold is not due")
            if runner_up_id is not None:
                runner_up = _identifier(runner_up_id, "runner_up_id")
                if runner_up not in candidate.actors:
                    raise DomainRed(RedCode.NOT_FOUND, "runner-up is not a real actor")
                requisition.candidate_id = runner_up
                requisition.candidate_owner_id = None
                requisition.owner_history = ()
                requisition.referral_id = None
                requisition.referrer_id = None
                requisition.referral_reward_gold = 0
                requisition.offer_id = None
                requisition.offered_level = None
                requisition.promised_level = None
                requisition.level_approver_id = None
                requisition.premium_end_cycle = None
                requisition.counteroffer_used = False
                requisition.counteroffer_gold = 0
                requisition.hold_until_cycle = None
                requisition.independent_votes = {}
                requisition.vote_evidence = {}
                requisition.raw_votes_frozen = ()
                requisition.calibrated_scores = {}
                requisition.status = RequisitionStatus.OPEN
            else:
                candidate.formal_hc_reserved -= 1
                candidate.formal_hc_available += 1
                requisition.hc_reservation_active = False
                requisition.status = RequisitionStatus.CLOSED

        return self._atomic(token, 275, mutate)

    def register_rehire_276(
        self,
        token: object,
        *,
        rehire_id: str,
        official_id: str,
        historical_case_ids: Sequence[str],
        growth_evidence_ids: Sequence[str],
        new_cycle: int,
        retain_misconduct: bool,
    ) -> ActionResult:
        """Create a gap-only rehire review while keeping old cases immutable."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(rehire_id, "rehire_id")
            official = _identifier(official_id, "official_id")
            cases = _unique_identifiers(tuple(historical_case_ids), "historical_case_id")
            evidence = _unique_identifiers(tuple(growth_evidence_ids), "growth_evidence_id")
            cycle = _integer(new_cycle, "new_cycle", minimum=1)
            if not isinstance(retain_misconduct, bool):
                raise DomainRed(RedCode.INVALID_TYPE, "retain_misconduct must be bool")
            if key in candidate.rehire_receipts:
                raise DomainRed(RedCode.DUPLICATE, "rehire review already exists")
            if official not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "alumni identity not found")
            history = {item.case_id: item for item in candidate.historical_cases}
            if not cases or any(case_id not in history for case_id in cases):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "rehire lost historical case")
            if any(history[case_id].subject_id != official for case_id in cases):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "historical case belongs to another person")
            if not evidence or cycle <= candidate.cycle_serial:
                raise DomainRed(RedCode.STATE_CONFLICT, "rehire needs new evidence and a future cohort")
            if not retain_misconduct:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "rehire cannot wipe misconduct history")
            candidate.rehire_receipts[key] = (
                official,
                cases,
                tuple(history[case_id].provenance_hash for case_id in cases),
                evidence,
                cycle,
                retain_misconduct,
            )

        return self._atomic(token, 276, mutate)

    def record_pip_exit_277(
        self,
        token: object,
        *,
        exit_id: str,
        pip_case_id: str,
        displaced_subject_id: str,
        former_hc_slot_id: str,
        remaining_work_hours: int,
        workload_provenance_id: str,
        backfill_route: str,
    ) -> ActionResult:
        """Record displaced work; do not mint, consume, or return HC automatically."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(exit_id, "exit_id")
            pip_case = _identifier(pip_case_id, "pip_case_id")
            subject = _identifier(displaced_subject_id, "displaced_subject_id")
            slot = _identifier(former_hc_slot_id, "former_hc_slot_id")
            hours = _integer(remaining_work_hours, "remaining_work_hours")
            provenance = _identifier(workload_provenance_id, "workload_provenance_id")
            route = _identifier(backfill_route, "backfill_route")
            if route not in {"release", "reallocate", "request_backfill"}:
                raise DomainRed(RedCode.INVALID_VALUE, "backfill route is invalid")
            if key in candidate.pip_exit_receipts:
                raise DomainRed(RedCode.DUPLICATE, "PIP exit already exists")
            if subject not in candidate.actors:
                raise DomainRed(RedCode.NOT_FOUND, "PIP subject not found")
            if candidate.formal_hc_filled < 1:
                raise DomainRed(RedCode.RESOURCE_EXHAUSTED, "PIP exit has no occupied HC")
            occupied_slots = candidate.formal_hc_occupants.get(subject, 0)
            if occupied_slots < 1:
                raise DomainRed(RedCode.STATE_CONFLICT, "PIP subject does not occupy the HC slot")
            candidate.formal_hc_filled -= 1
            candidate.formal_hc_vacant += 1
            if occupied_slots == 1:
                del candidate.formal_hc_occupants[subject]
            else:
                candidate.formal_hc_occupants[subject] = occupied_slots - 1
            candidate.pip_exit_receipts[key] = (
                pip_case,
                subject,
                slot,
                hours,
                provenance,
                route,
                candidate.formal_hc_total,
                candidate.formal_hc_available,
                candidate.formal_hc_reserved,
                candidate.formal_hc_filled,
                candidate.formal_hc_vacant,
            )

        return self._atomic(token, 277, mutate)

    # AL / 355-356, 360-361 -------------------------------------------

    def apply_target_ratchet_355(
        self,
        token: object,
        *,
        ratchet_id: str,
        official_id: str,
        prior_cycle: int,
        replicability_ref: str,
        prior_target: int,
        prior_actual: int,
        repeatable_excess: int,
        windfall_excess: int,
        mode: RatchetMode,
        cap_bps: int,
        added_resource_gold: int,
        authority_ref: str | None,
    ) -> ActionResult:
        """Compute a deterministic future target without rewriting the prior cycle."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(ratchet_id, "ratchet_id")
            official = _identifier(official_id, "official_id")
            prior = _integer(prior_cycle, "prior_cycle", minimum=1)
            replicability = _identifier(replicability_ref, "replicability_ref")
            target = _integer(prior_target, "prior_target", minimum=1)
            actual = _integer(prior_actual, "prior_actual")
            repeatable = _integer(repeatable_excess, "repeatable_excess")
            windfall = _integer(windfall_excess, "windfall_excess")
            cap = _integer(cap_bps, "cap_bps")
            resource = _integer(added_resource_gold, "added_resource_gold")
            if not isinstance(mode, RatchetMode):
                raise DomainRed(RedCode.INVALID_TYPE, "mode must be RatchetMode")
            if key in candidate.target_ratchets:
                raise DomainRed(RedCode.DUPLICATE, "target ratchet already exists")
            if official not in candidate.actors or prior >= candidate.cycle_serial:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "ratchet lacks a closed official cycle")
            if any(
                item.official_id == official and item.prior_cycle == prior
                for item in candidate.target_ratchets.values()
            ):
                raise DomainRed(RedCode.DUPLICATE, "official cycle already has a ratchet")
            if repeatable + windfall != max(0, actual - target):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "excess decomposition is invalid")
            if cap > BASIS_POINTS:
                raise DomainRed(RedCode.INVALID_VALUE, "ratchet cap exceeds 100%")
            if mode is RatchetMode.HOLD:
                new_target = target
            elif mode is RatchetMode.LIMITED:
                new_target = target + min(repeatable, target * cap // BASIS_POINTS)
            else:
                new_target = max(target, actual)
            if resource:
                _identifier(authority_ref, "authority_ref")
                candidate._reserve_gold(resource)
            risk = max(0, new_target - target - resource)
            candidate.target_ratchets[key] = TargetRatchetRecord(
                key,
                official,
                prior,
                replicability,
                target,
                actual,
                repeatable,
                windfall,
                mode,
                cap,
                new_target,
                resource,
                authority_ref,
                risk,
            )

        return self._atomic(token, 355, mutate)

    def settle_outcome_timing_356(
        self,
        token: object,
        *,
        outcome_id: str,
        actual_value: int,
        actual_completion_cycle: int,
        report_cycle: int,
        reported_value_by_cycle: Mapping[int, int],
        evidence_timestamp_ids: Sequence[str],
    ) -> ActionResult:
        """Credit an outcome wholly to its evidenced completion cycle exactly once."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(outcome_id, "outcome_id")
            value = _integer(actual_value, "actual_value", minimum=1)
            completion = _integer(actual_completion_cycle, "actual_completion_cycle", minimum=1)
            report = _integer(report_cycle, "report_cycle", minimum=1)
            evidence = _unique_identifiers(tuple(evidence_timestamp_ids), "timestamp_evidence_id")
            allocation = dict(reported_value_by_cycle)
            if key in candidate.outcome_timings:
                raise DomainRed(RedCode.DUPLICATE, "outcome timing already settled")
            if report < completion or not evidence:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "outcome timing lacks valid provenance")
            if report > candidate.cycle_serial:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "outcome timing uses future evidence")
            used_timestamps = {
                timestamp
                for item in candidate.outcome_timings.values()
                for timestamp in item.evidence_timestamp_ids
            }
            if used_timestamps.intersection(evidence):
                raise DomainRed(RedCode.DUPLICATE, "timestamp evidence was already consumed")
            for cycle, amount in allocation.items():
                _integer(cycle, "reported_cycle", minimum=1)
                _integer(amount, "reported_value")
            if allocation != {completion: value}:
                raise DomainRed(
                    RedCode.INVARIANT_BROKEN,
                    "reported value must equal actual and stay in completion cycle",
                )
            withheld = value if report > completion else 0
            delay = report - completion
            candidate.outcome_timings[key] = OutcomeTimingRecord(
                key,
                value,
                completion,
                report,
                completion,
                tuple(sorted(allocation.items())),
                withheld,
                evidence,
                delay,
                1 if withheld else 0,
            )

        return self._atomic(token, 356, mutate)

    def resolve_collective_action_360(
        self,
        token: object,
        *,
        collective_id: str,
        authoritative_members_by_cohort: Mapping[str, Sequence[str]],
        agenda_by_cohort: Mapping[str, Sequence[str]],
        c_quota_by_cohort: Mapping[str, int],
        forced_c_by_cohort: Mapping[str, Sequence[str]],
        approved_exceptions_by_cohort: Mapping[str, Sequence[str]],
        exception_approver_by_cohort: Mapping[str, str | None],
        manager_by_cohort: Mapping[str, str],
        evidence_by_cohort: Mapping[str, str],
        reform_effective_cycle: int | None,
    ) -> ActionResult:
        """Conserve every frozen cohort while making all-meet evidence complete."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(collective_id, "collective_id")
            if key in candidate.collective_actions:
                raise DomainRed(RedCode.DUPLICATE, "collective action already exists")
            cohort_ids = set(authoritative_members_by_cohort)
            companions = (
                agenda_by_cohort,
                c_quota_by_cohort,
                forced_c_by_cohort,
                approved_exceptions_by_cohort,
                exception_approver_by_cohort,
                manager_by_cohort,
                evidence_by_cohort,
            )
            if not cohort_ids or any(set(mapping) != cohort_ids for mapping in companions):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "collective cohort maps are incomplete")
            frozen_quota: list[tuple[str, int]] = []
            frozen_forced: list[tuple[str, tuple[str, ...]]] = []
            frozen_exceptions: list[tuple[str, tuple[str, ...]]] = []
            frozen_agendas: list[tuple[str, tuple[str, ...]]] = []
            frozen_evidence: list[tuple[str, str]] = []
            frozen_approvals: list[tuple[str, str | None]] = []
            manager_costs: dict[str, int] = {}
            for cohort_id in sorted(cohort_ids):
                _identifier(cohort_id, "cohort_id")
                members = _unique_identifiers(
                    tuple(authoritative_members_by_cohort[cohort_id]),
                    "cohort_member_id",
                )
                agenda = _unique_identifiers(
                    tuple(agenda_by_cohort[cohort_id]),
                    "agenda_member_id",
                )
                forced = _unique_identifiers(
                    tuple(forced_c_by_cohort[cohort_id]),
                    "forced_c_member_id",
                )
                exceptions = _unique_identifiers(
                    tuple(approved_exceptions_by_cohort[cohort_id]),
                    "exception_member_id",
                )
                quota = _integer(c_quota_by_cohort[cohort_id], "c_quota")
                manager = _identifier(manager_by_cohort[cohort_id], "cohort_manager_id")
                evidence = _identifier(evidence_by_cohort[cohort_id], "collective_evidence_id")
                candidate._assert_manager(manager)
                if any(member not in candidate.actors for member in members):
                    raise DomainRed(RedCode.NOT_FOUND, "cohort member is not a real actor")
                if set(agenda) != set(members) or len(agenda) != len(members):
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "agenda is not the full frozen cohort")
                if not set(forced).issubset(members) or not set(exceptions).issubset(members):
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "quota settlement escaped cohort")
                if set(forced) & set(exceptions):
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "forced and exception sets overlap")
                if len(forced) + len(exceptions) != quota:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "forced C plus exceptions must equal quota")
                approver_value = exception_approver_by_cohort[cohort_id]
                if exceptions:
                    approver = _identifier(approver_value, "exception_approver_id")
                    candidate._assert_manager(approver)
                    if candidate.actors[approver].rank <= candidate.actors[manager].rank:
                        raise DomainRed(RedCode.PERMISSION_DENIED, "exception lacks superior approval")
                elif approver_value is not None:
                    raise DomainRed(RedCode.PROVENANCE_INVALID, "approval exists without exception")
                else:
                    approver = None
                if exceptions:
                    manager_costs[manager] = manager_costs.get(manager, 0) + len(exceptions)
                frozen_quota.append((cohort_id, quota))
                frozen_forced.append((cohort_id, forced))
                frozen_exceptions.append((cohort_id, exceptions))
                frozen_agendas.append((cohort_id, agenda))
                frozen_evidence.append((cohort_id, evidence))
                frozen_approvals.append((cohort_id, approver))
            if reform_effective_cycle is not None:
                effective = _integer(reform_effective_cycle, "reform_effective_cycle", minimum=1)
                if effective <= candidate.cycle_serial:
                    raise DomainRed(RedCode.STATE_CONFLICT, "collective reform cannot rewrite current cycle")
                candidate.future_reforms.setdefault(effective, {})[key] = "collective_quota_review"
            else:
                effective = None
            for manager, cost in manager_costs.items():
                candidate.manager_score_cost[manager] = (
                    candidate.manager_score_cost.get(manager, 0) + cost
                )
            candidate.trust_delta -= sum(manager_costs.values())
            candidate.collective_actions[key] = CollectiveActionRecord(
                key,
                tuple(frozen_quota),
                tuple(frozen_forced),
                tuple(frozen_exceptions),
                tuple(frozen_agendas),
                tuple(frozen_evidence),
                tuple(frozen_approvals),
                tuple(sorted(manager_costs.items())),
                effective,
            )

        return self._atomic(token, 360, mutate)

    def adopt_charter_361(
        self,
        token: object,
        *,
        charter_id: str,
        priority_order: Sequence[CharterPriority],
        defaults: PolicyDefaults,
        completed_cycle_ids: Sequence[int],
        long_run_report_id: str,
        adopted_day: int,
        effective_cycle: int,
        amendment_due_cycle: int,
        visible_costs: Sequence[str],
    ) -> ActionResult:
        """Append a versioned charter whose defaults affect future cycles only."""

        def mutate(candidate: Phase3WorkforceEndgameModel) -> None:
            key = _identifier(charter_id, "charter_id")
            actor = candidate.actors.get(token.actor_id) if isinstance(token, CommandToken) else None
            if actor is None or not actor.is_top_celestial_liege:
                raise DomainRed(RedCode.PERMISSION_DENIED, "charter requires the top celestial liege")
            priorities = tuple(priority_order)
            cycles = tuple(_integer(item, "completed_cycle_id", minimum=1) for item in completed_cycle_ids)
            report = _identifier(long_run_report_id, "long_run_report_id")
            day = _integer(adopted_day, "adopted_day", minimum=1)
            effective = _integer(effective_cycle, "effective_cycle", minimum=1)
            amendment_due = _integer(amendment_due_cycle, "amendment_due_cycle", minimum=1)
            costs = _unique_identifiers(tuple(visible_costs), "visible_cost")
            if not isinstance(defaults, PolicyDefaults):
                raise DomainRed(RedCode.INVALID_TYPE, "defaults must be PolicyDefaults")
            if len(priorities) != len(CharterPriority) or set(priorities) != set(CharterPriority):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "priority order must be an exact permutation")
            if len(cycles) < 3 or len(set(cycles)) != len(cycles):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "charter needs three unique completed cycles")
            if any(cycle > candidate.cycle_serial for cycle in cycles):
                raise DomainRed(RedCode.PROVENANCE_INVALID, "charter cites a future completed cycle")
            if effective <= candidate.cycle_serial or amendment_due <= effective:
                raise DomainRed(RedCode.DEADLINE_INVALID, "charter deadlines are invalid")
            if defaults.delivery_horizon is not DeliveryHorizon.LONG_TERM:
                raise DomainRed(RedCode.STATE_CONFLICT, "reference charter requires long-term delivery")
            competition_index = priorities.index(CharterPriority.FORCED_COMPETITION)
            noncompetition_priorities = (
                CharterPriority.EVIDENCE_FAIRNESS,
                CharterPriority.LONG_TERM_INNOVATION,
                CharterPriority.ORGANIZATIONAL_WARMTH,
            )
            if sum(
                priorities.index(priority) < competition_index
                for priority in noncompetition_priorities
            ) < 2:
                raise DomainRed(
                    RedCode.STATE_CONFLICT,
                    "at least two non-competition priorities must precede competition",
                )
            if not costs:
                raise DomainRed(RedCode.PROVENANCE_INVALID, "charter must expose a cost")
            if any(item.charter_id == key for item in candidate.charters):
                raise DomainRed(RedCode.DUPLICATE, "charter id already exists")
            previous = candidate.charters[-1] if candidate.charters else None
            if previous is not None:
                if cycles != previous.completed_cycle_ids or report != previous.long_run_report_id:
                    raise DomainRed(
                        RedCode.PROVENANCE_INVALID,
                        "amendment cannot rewrite charter evidence",
                    )
                if day <= previous.adopted_day or effective <= previous.effective_cycle:
                    raise DomainRed(RedCode.DEADLINE_INVALID, "charter amendment is not monotonic")
            candidate.charters.append(
                CharterVersion(
                    key,
                    1 if previous is None else previous.version + 1,
                    token.actor_id,
                    priorities,
                    defaults,
                    cycles,
                    report,
                    day,
                    effective,
                    amendment_due,
                    None if previous is None else previous.charter_id,
                    costs,
                )
            )

        return self._atomic(token, 361, mutate)


if set(MECHANISM_BINDINGS) != set(EXPECTED_MECHANISM_IDS):
    raise RuntimeError("workforce/endgame mechanism mapping is incomplete")
for _mechanism_id, _binding_record in MECHANISM_BINDINGS.items():
    for _behavior in _binding_record.behaviors:
        if not hasattr(Phase3WorkforceEndgameModel, _behavior):
            raise RuntimeError(
                f"mechanism {_mechanism_id} has no callable behavior {_behavior}"
            )


__all__ = [
    "ActionResult",
    "ActionStatus",
    "ActorRecord",
    "BudgetLedger",
    "CapacityPeriod",
    "CharterPriority",
    "CommandToken",
    "CompensationRoute",
    "ContractType",
    "DeliveryHorizon",
    "DomainRed",
    "EXPECTED_MECHANISM_IDS",
    "HistoricalCase",
    "MECHANISM_BINDINGS",
    "OvertimeKind",
    "Phase3WorkforceEndgameModel",
    "PolicyDefaults",
    "READINESS",
    "Rank",
    "RatchetMode",
    "RedCode",
    "Vote",
    "WorkCategory",
]
