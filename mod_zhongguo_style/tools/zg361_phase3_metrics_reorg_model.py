#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python L0 executable model for 361 metrics, reorg and demand delivery.

The model covers AA(229-241), AG(301-311), and AJ(334-344).  It is an
implementation-oriented specification only: passing its tests is not CK3
script wiring, fixture-live evidence, a playable GUI, or production readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Mapping


READINESS: Final[str] = "python-l0-only"
SHARE_TOTAL_BPS: Final[int] = 10_000


class RedCode(str, Enum):
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    NOT_FOUND = "not_found"
    STATE_CONFLICT = "state_conflict"
    COMMAND_COLLISION = "command_collision"
    PROVENANCE_CONFLICT = "provenance_conflict"
    OWNER_CONFLICT = "owner_conflict"
    SIGNATURE_REQUIRED = "signature_required"
    SHARE_IMBALANCE = "share_imbalance"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    SAMPLE_SLOT_EXHAUSTED = "sample_slot_exhausted"
    EMERGENCY_SLOT_EXHAUSTED = "emergency_slot_exhausted"
    WIP_LIMIT_EXCEEDED = "wip_limit_exceeded"
    QUIET_PERIOD_VIOLATION = "quiet_period_violation"
    INVARIANT_BROKEN = "invariant_broken"


class DomainRed(ValueError):
    def __init__(self, code: RedCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ActionStatus(str, Enum):
    APPLIED = "applied"
    STALE_NOOP = "stale_noop"
    IDEMPOTENT_NOOP = "idempotent_noop"


@dataclass(frozen=True)
class CommandToken:
    model_id: str
    owner_id: str
    cycle_serial: int
    case_serial: int
    expected_revision: int
    command_id: str


@dataclass(frozen=True)
class CommandReceipt:
    command_id: str
    mechanism_id: int
    parent_revision: int
    committed_revision: int


@dataclass(frozen=True)
class ActionResult:
    status: ActionStatus
    mechanism_id: int
    previous_revision: int
    current_revision: int

    @property
    def applied(self) -> bool:
        return self.status is ActionStatus.APPLIED


@dataclass(frozen=True)
class MechanismBinding:
    mechanism_id: int
    domain: str
    title_cn: str
    behaviors: tuple[str, ...]


def _binding(mid: int, domain: str, title: str, *behaviors: str) -> MechanismBinding:
    return MechanismBinding(mid, domain, title, tuple(behaviors))


MECHANISM_BINDINGS: Final[dict[int, MechanismBinding]] = {
    229: _binding(229, "AA", "指标字典与口径 owner", "define_metric_229"),
    230: _binding(230, "AA", "多数据源对账", "reconcile_sources_230"),
    231: _binding(231, "AA", "业务指标分母变更", "change_denominator_231"),
    232: _binding(232, "AA", "缺失数据与人工回填", "backfill_missing_data_232"),
    233: _binding(233, "AA", "看板访问权不对称", "set_metric_access_233"),
    234: _binding(234, "AA", "领先指标与滞后结果分账", "record_signals_234"),
    235: _binding(235, "AA", "主指标与护栏指标", "evaluate_guardrail_235"),
    236: _binding(236, "AA", "KPI 达标悬崖", "lock_scoring_policy_236"),
    237: _binding(237, "AA", "时间窗挑选与‘截最美一段’", "audit_time_window_237"),
    238: _binding(238, "AA", "虚荣指标与最终价值", "settle_vanity_value_238"),
    239: _binding(239, "AA", "失败实验的学习收益", "settle_failed_experiment_239"),
    240: _binding(240, "AA", "实验污染与多团队抢样本", "allocate_sample_240"),
    241: _binding(241, "AA", "长尾效果归属期", "set_long_tail_attribution_241"),
    301: _binding(301, "AG", "核心业务光环折算", "normalize_halo_301"),
    302: _binding(302, "AG", "衰退业务的逆风责任", "evaluate_decline_302"),
    303: _binding(303, "AG", "孵化团队的限期分布保护", "grant_incubation_303"),
    304: _binding(304, "AG", "项目归属与职能归属双家长", "lock_dual_parent_304"),
    305: _binding(305, "AG", "校准前重组静默期", "apply_reorg_305"),
    306: _binding(306, "AG", "双帽临时负责人容量拆分", "assign_double_hat_306"),
    307: _binding(307, "AG", "利润中心 / 成本中心记分卡", "configure_scorecard_307"),
    308: _binding(308, "AG", "管理岗与专业岗比例", "rebalance_hc_308"),
    309: _binding(309, "AG", "边远团队的可见度折损", "visit_remote_team_309"),
    310: _binding(310, "AG", "并入团队的旧档映射", "map_legacy_ratings_310"),
    311: _binding(311, "AG", "战略转向不得倒改旧目标", "pivot_strategy_311"),
    334: _binding(334, "AJ", "统一需求入口与来源标签", "submit_demand_334"),
    335: _binding(335, "AJ", "紧急插单预算", "mark_emergency_335"),
    336: _binding(336, "AJ", "需求准入完成定义", "admit_demand_336"),
    337: _binding(337, "AJ", "需求变更税", "change_demand_337"),
    338: _binding(338, "AJ", "范围—期限—质量三角签字", "sign_delivery_triangle_338"),
    339: _binding(339, "AJ", "估算校准而非只奖准时", "calibrate_estimate_339"),
    340: _binding(340, "AJ", "在制品上限（WIP）", "start_work_340"),
    341: _binding(341, "AJ", "跨周期未完工债", "carryover_demand_341"),
    342: _binding(342, "AJ", "阻塞时间归因", "record_blocker_342"),
    343: _binding(343, "AJ", "提出、执行、验收三方签收", "accept_delivery_343"),
    344: _binding(344, "AJ", "上线 / 采用 / 价值三阶段结算", "settle_value_stage_344"),
}

EXPECTED_MECHANISM_IDS: Final[frozenset[int]] = frozenset(
    (*range(229, 242), *range(301, 312), *range(334, 345))
)


class ReconcileRoute(str, Enum):
    AUTHORITY = "authority"
    JOINT = "joint"
    DEFER = "defer"


class AccessLevel(str, Enum):
    ALL = "all"
    MANAGER = "manager"
    ROLE_LAYERED = "role_layered"


class ScoringPolicy(str, Enum):
    CLIFF = "cliff"
    CONTINUOUS = "continuous"
    HYBRID = "hybrid"


class SampleConflictRoute(str, Enum):
    QUEUE = "queue"
    PARTITION = "partition"
    ACCEPT_CONTAMINATION = "accept_contamination"


class CenterType(str, Enum):
    PROFIT = "profit"
    COST = "cost"


class DemandSource(str, Enum):
    SUPERIOR = "superior"
    TERRITORY = "territory"
    INCIDENT = "incident"
    PEER = "peer"
    SELF_NOMINATED = "self_nominated"


class AdmissionRoute(str, Enum):
    RETURN = "return"
    EXPLORATION = "exploration"
    COMMITMENT = "commitment"
    FORCED_COMMITMENT = "forced_commitment"


class ChangeRoute(str, Enum):
    EXTEND = "extend"
    REMOVE_EQUAL_SCOPE = "remove_equal_scope"
    ADD_CAPACITY = "add_capacity"
    OWNER_ERROR = "owner_error"
    DISASTER_WAIVER = "disaster_waiver"


class TriangleTradeoff(str, Enum):
    CUT_SCOPE = "cut_scope"
    EXTEND_TIME = "extend_time"
    ADD_HC = "add_hc"
    LOWER_QUALITY = "lower_quality"


class CarryoverRoute(str, Enum):
    CARRY = "carry"
    SPLIT_ACCEPTED = "split_accepted"
    CANCEL = "cancel"


class AcceptanceOutcome(str, Enum):
    ACCEPTED = "accepted"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"


class ValueStage(str, Enum):
    LAUNCH = "launch"
    ADOPTION = "adoption"
    VALUE = "value"


class DeliveryStatus(str, Enum):
    IN_WIP = "in_wip"
    CARRIED = "carried"
    CANCELLED = "cancelled"
    ACCEPTED = "accepted"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    VALUED = "valued"


@dataclass
class MetricDefinition:
    metric_id: str
    owner_id: str
    definition: str
    source: str
    frequency: str
    scope: str
    denominator: int
    version: int
    provenance_id: str
    old_versions: list[dict[str, object]] = field(default_factory=list)
    scoring_policy: ScoringPolicy | None = None
    access_level: AccessLevel = AccessLevel.ALL
    query_channel: bool = True


@dataclass(frozen=True)
class SampleAllocation:
    experiment_id: str
    samples: tuple[str, ...]
    route: SampleConflictRoute
    active: bool
    contaminated: bool
    provenance_id: str


@dataclass
class Demand:
    demand_id: str
    object_owner_id: str
    object_cycle_serial: int
    object_case_serial: int
    object_version: int
    deadline_cycle: int
    source: DemandSource
    source_owner_id: str
    proposer_id: str
    executor_id: str
    beneficiary_id: str
    provenance_id: str
    queue_sequence: int
    benefit: str | None = None
    acceptance: str | None = None
    boundary: str | None = None
    dependencies: tuple[str, ...] = ()
    estimated_hours: int = 0
    admitted: bool = False
    admission_route: AdmissionRoute | None = None
    forced_owner_liability: bool = False
    emergency: bool = False
    emergency_tradeoff: str | None = None
    disaster_waiver_used: bool = False
    change_tax_hours: int = 0
    triangle_tradeoff: TriangleTradeoff | None = None
    triangle_approver_id: str | None = None
    quality_liability_id: str | None = None
    actual_hours: int | None = None
    estimate_error: int | None = None
    estimate_reason: str | None = None
    active: bool = False
    wip_exception_owner_id: str | None = None
    hidden_wip_penalty: int = 0
    carryover_hours: int = 0
    accepted_hours: int = 0
    blocker: dict[str, object] | None = None
    signatures: dict[str, str] = field(default_factory=dict)
    acceptance_outcome: AcceptanceOutcome | None = None
    value_credits: dict[ValueStage, int] = field(default_factory=dict)


@dataclass
class Delivery:
    delivery_id: str
    demand_id: str
    owner_id: str
    executor_id: str
    beneficiary_id: str
    cycle_serial: int
    case_serial: int
    deadline_cycle: int
    version: int
    status: DeliveryStatus
    reserved_hours: int
    carryover_hours: int = 0
    accepted_hours: int = 0
    maturity: int = 0


@dataclass
class MetricsReorgModel:
    model_id: str
    owner_id: str
    cycle_serial: int
    case_serial: int
    capacity_hours_total: int
    next_cycle_capacity_total: int
    sample_slot_total: int
    emergency_slot_total: int
    wip_limit: int
    management_capacity_total: int
    total_hc: int
    revision: int = 0
    receipts: dict[str, CommandReceipt] = field(default_factory=dict)
    applied_mechanism_ids: set[int] = field(default_factory=set)
    provenance_index: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, MetricDefinition] = field(default_factory=dict)
    reconciliations: dict[str, dict[str, object]] = field(default_factory=dict)
    backfills: dict[str, dict[str, object]] = field(default_factory=dict)
    signal_records: dict[str, dict[str, object]] = field(default_factory=dict)
    guardrails: dict[str, dict[str, object]] = field(default_factory=dict)
    window_audits: dict[str, dict[str, object]] = field(default_factory=dict)
    value_settlements: dict[str, dict[str, object]] = field(default_factory=dict)
    experiments: dict[str, dict[str, object]] = field(default_factory=dict)
    sample_allocations: dict[str, SampleAllocation] = field(default_factory=dict)
    long_tail_attributions: dict[str, dict[str, object]] = field(default_factory=dict)
    halo_records: dict[str, dict[str, object]] = field(default_factory=dict)
    decline_records: dict[str, dict[str, object]] = field(default_factory=dict)
    incubations: dict[str, dict[str, object]] = field(default_factory=dict)
    dual_parent_records: dict[str, dict[str, object]] = field(default_factory=dict)
    reorg_records: dict[str, dict[str, object]] = field(default_factory=dict)
    double_hat_records: dict[str, dict[str, object]] = field(default_factory=dict)
    scorecards: dict[str, dict[str, object]] = field(default_factory=dict)
    manager_hc: int = 0
    expert_hc: int = 0
    remote_visits: dict[str, dict[str, object]] = field(default_factory=dict)
    management_capacity_used: int = 0
    legacy_maps: dict[str, dict[str, object]] = field(default_factory=dict)
    pivots: dict[str, dict[str, object]] = field(default_factory=dict)
    demands: dict[str, Demand] = field(default_factory=dict)
    deliveries: dict[str, Delivery] = field(default_factory=dict)
    capacity_hours_reserved: int = 0
    next_cycle_capacity_reserved: int = 0
    emergency_slots_used: int = 0

    def __post_init__(self) -> None:
        self._text(self.model_id, "model_id")
        self._text(self.owner_id, "owner_id")
        for label in (
            "cycle_serial",
            "case_serial",
            "capacity_hours_total",
            "next_cycle_capacity_total",
            "sample_slot_total",
            "emergency_slot_total",
            "wip_limit",
            "management_capacity_total",
            "total_hc",
        ):
            self._integer(getattr(self, label), label, minimum=1)
        if self.manager_hc == 0 and self.expert_hc == 0:
            self.manager_hc = self.total_hc // 4
            self.expert_hc = self.total_hc - self.manager_hc
        if self.manager_hc + self.expert_hc != self.total_hc:
            raise DomainRed(RedCode.INVALID_VALUE, "initial HC must conserve")

    @staticmethod
    def _text(value: object, label: str) -> str:
        if not isinstance(value, str):
            raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be a string")
        if not value.strip():
            raise DomainRed(RedCode.INVALID_VALUE, f"{label} must be non-empty")
        return value

    @staticmethod
    def _integer(
        value: object, label: str, *, minimum: int | None = 0
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be an integer")
        if minimum is not None and value < minimum:
            raise DomainRed(RedCode.INVALID_VALUE, f"{label} must be >= {minimum}")
        return value

    @staticmethod
    def _boolean(value: object, label: str) -> bool:
        if type(value) is not bool:
            raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be bool")
        return value

    @staticmethod
    def _enum(value: object, enum_type: type[Enum], label: str) -> Enum:
        try:
            return enum_type(value)
        except (TypeError, ValueError) as exc:
            raise DomainRed(RedCode.INVALID_VALUE, f"invalid {label}: {value!r}") from exc

    def command(self, command_id: str) -> CommandToken:
        self._text(command_id, "command_id")
        return CommandToken(
            self.model_id,
            self.owner_id,
            self.cycle_serial,
            self.case_serial,
            self.revision,
            command_id,
        )

    def _gate(self, command: object, mechanism_id: int) -> ActionResult | None:
        if not isinstance(command, CommandToken):
            raise DomainRed(RedCode.INVALID_TYPE, "command must be CommandToken")
        self._text(command.command_id, "command_id")
        prior = self.receipts.get(command.command_id)
        if prior is not None:
            if prior.mechanism_id != mechanism_id:
                raise DomainRed(RedCode.COMMAND_COLLISION, "command id reused by another mechanism")
            return ActionResult(
                ActionStatus.IDEMPOTENT_NOOP,
                mechanism_id,
                self.revision,
                self.revision,
            )
        if (
            command.model_id != self.model_id
            or command.owner_id != self.owner_id
            or command.cycle_serial != self.cycle_serial
            or command.case_serial != self.case_serial
            or command.expected_revision != self.revision
        ):
            return ActionResult(
                ActionStatus.STALE_NOOP,
                mechanism_id,
                self.revision,
                self.revision,
            )
        return None

    def _commit(self, command: CommandToken, mechanism_id: int) -> ActionResult:
        previous = self.revision
        self.revision += 1
        self.receipts[command.command_id] = CommandReceipt(
            command.command_id, mechanism_id, previous, self.revision
        )
        self.applied_mechanism_ids.add(mechanism_id)
        self.assert_invariants()
        return ActionResult(ActionStatus.APPLIED, mechanism_id, previous, self.revision)

    def _check_provenance(self, provenance_id: object, entity_id: str) -> str:
        provenance_id = self._text(provenance_id, "provenance_id")
        prior = self.provenance_index.get(provenance_id)
        if prior is not None and prior != entity_id:
            raise DomainRed(RedCode.PROVENANCE_CONFLICT, "provenance id already bound")
        return provenance_id

    def _register_provenance(self, provenance_id: str, entity_id: str) -> None:
        self.provenance_index[provenance_id] = entity_id

    def _metric(self, metric_id: object) -> MetricDefinition:
        metric_id = self._text(metric_id, "metric_id")
        metric = self.metrics.get(metric_id)
        if metric is None:
            raise DomainRed(RedCode.NOT_FOUND, f"unknown metric {metric_id}")
        return metric

    def _demand(self, demand_id: object) -> Demand:
        demand_id = self._text(demand_id, "demand_id")
        demand = self.demands.get(demand_id)
        if demand is None:
            raise DomainRed(RedCode.NOT_FOUND, f"unknown demand {demand_id}")
        return demand

    def _delivery(self, demand_id: object) -> Delivery:
        demand_id = self._text(demand_id, "demand_id")
        delivery = self.deliveries.get(demand_id)
        if delivery is None:
            raise DomainRed(RedCode.NOT_FOUND, f"demand {demand_id} has no delivery object")
        return delivery

    @staticmethod
    def _touch_demand(demand: Demand) -> None:
        demand.object_version += 1

    @staticmethod
    def _touch_delivery(delivery: Delivery) -> None:
        delivery.version += 1

    @property
    def active_sample_slots(self) -> int:
        return sum(row.active for row in self.sample_allocations.values())

    @property
    def active_wip(self) -> int:
        return sum(demand.active for demand in self.demands.values())

    @property
    def wip_exception_count(self) -> int:
        return sum(
            demand.active
            and (
                demand.wip_exception_owner_id is not None
                or demand.hidden_wip_penalty > 0
            )
            for demand in self.demands.values()
        )

    def define_metric_229(
        self,
        command: CommandToken,
        *,
        metric_id: str,
        owner_id: str,
        definition: str,
        source: str,
        frequency: str,
        scope: str,
        denominator: int,
        provenance_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 229)
        if gate:
            return gate
        metric_id = self._text(metric_id, "metric_id")
        owner_id = self._text(owner_id, "owner_id")
        fields = tuple(
            self._text(value, label)
            for value, label in (
                (definition, "definition"),
                (source, "source"),
                (frequency, "frequency"),
                (scope, "scope"),
            )
        )
        denominator = self._integer(denominator, "denominator", minimum=1)
        provenance_id = self._check_provenance(provenance_id, f"metric:{metric_id}")
        if metric_id in self.metrics:
            raise DomainRed(RedCode.OWNER_CONFLICT, "metric already has a definition owner")
        self.metrics[metric_id] = MetricDefinition(
            metric_id, owner_id, *fields, denominator, 1, provenance_id
        )
        self._register_provenance(provenance_id, f"metric:{metric_id}")
        return self._commit(command, 229)

    def reconcile_sources_230(
        self,
        command: CommandToken,
        *,
        reconciliation_id: str,
        metric_id: str,
        source_values: Mapping[str, int],
        route: ReconcileRoute,
        authority_source: str | None,
        provenance_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 230)
        if gate:
            return gate
        reconciliation_id = self._text(reconciliation_id, "reconciliation_id")
        self._metric(metric_id)
        if reconciliation_id in self.reconciliations:
            raise DomainRed(RedCode.STATE_CONFLICT, "reconciliation already exists")
        if not isinstance(source_values, Mapping) or len(source_values) < 2:
            raise DomainRed(RedCode.INVALID_TYPE, "at least two source values are required")
        values = {
            self._text(source, "source"): self._integer(value, "source value")
            for source, value in source_values.items()
        }
        route = self._enum(route, ReconcileRoute, "reconciliation route")
        if route is ReconcileRoute.AUTHORITY:
            authority_source = self._text(authority_source, "authority_source")
            if authority_source not in values:
                raise DomainRed(RedCode.INVALID_VALUE, "authority source is absent")
            resolved = values[authority_source]
        elif route is ReconcileRoute.JOINT:
            if authority_source is not None:
                raise DomainRed(RedCode.INVALID_VALUE, "joint route has no sole authority")
            resolved = sum(values.values()) // len(values)
        else:
            if authority_source is not None:
                raise DomainRed(RedCode.INVALID_VALUE, "deferred route has no chosen source")
            resolved = None
        provenance_id = self._check_provenance(
            provenance_id, f"reconciliation:{reconciliation_id}"
        )
        self.reconciliations[reconciliation_id] = {
            "metric_id": metric_id,
            "source_values": values,
            "route": route,
            "authority_source": authority_source,
            "resolved_value": resolved,
            "settlement_delayed": resolved is None,
            "provenance_id": provenance_id,
        }
        self._register_provenance(provenance_id, f"reconciliation:{reconciliation_id}")
        return self._commit(command, 230)

    def change_denominator_231(
        self,
        command: CommandToken,
        *,
        metric_id: str,
        new_denominator: int,
        reason: str,
        effective_cycle: int,
    ) -> ActionResult:
        gate = self._gate(command, 231)
        if gate:
            return gate
        metric = self._metric(metric_id)
        new_denominator = self._integer(new_denominator, "new_denominator", minimum=1)
        reason = self._text(reason, "reason")
        effective_cycle = self._integer(
            effective_cycle, "effective_cycle", minimum=self.cycle_serial + 1
        )
        if new_denominator == metric.denominator:
            raise DomainRed(RedCode.INVALID_VALUE, "denominator did not change")
        old_row = {
            "version": metric.version,
            "denominator": metric.denominator,
            "effective_before": effective_cycle,
            "awards_rewritten": False,
        }
        metric.old_versions.append(old_row)
        metric.denominator = new_denominator
        metric.version += 1
        metric.old_versions[-1]["change_reason"] = reason
        return self._commit(command, 231)

    def backfill_missing_data_232(
        self,
        command: CommandToken,
        *,
        backfill_id: str,
        metric_id: str,
        value: int,
        method: str,
        filler_id: str,
        approver_id: str,
        provenance_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 232)
        if gate:
            return gate
        backfill_id = self._text(backfill_id, "backfill_id")
        self._metric(metric_id)
        value = self._integer(value, "value")
        method = self._text(method, "method")
        filler_id = self._text(filler_id, "filler_id")
        approver_id = self._text(approver_id, "approver_id")
        if filler_id == approver_id:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "backfill requires two signers")
        if backfill_id in self.backfills:
            raise DomainRed(RedCode.STATE_CONFLICT, "backfill already exists")
        provenance_id = self._check_provenance(provenance_id, f"backfill:{backfill_id}")
        self.backfills[backfill_id] = {
            "metric_id": metric_id,
            "value": value,
            "method": method,
            "signatures": (filler_id, approver_id),
            "deviation_accountability": ("method", filler_id, approver_id),
            "business_owner_automatically_penalized": False,
            "provenance_id": provenance_id,
        }
        self._register_provenance(provenance_id, f"backfill:{backfill_id}")
        return self._commit(command, 232)

    def set_metric_access_233(
        self,
        command: CommandToken,
        *,
        metric_id: str,
        access_level: AccessLevel,
        subject_has_access: bool,
        query_channel: bool,
    ) -> ActionResult:
        gate = self._gate(command, 233)
        if gate:
            return gate
        metric = self._metric(metric_id)
        access_level = self._enum(access_level, AccessLevel, "access level")
        subject_has_access = self._boolean(subject_has_access, "subject_has_access")
        query_channel = self._boolean(query_channel, "query_channel")
        if not subject_has_access and not query_channel:
            target_adjustment = True
            anomaly_accountability = False
        else:
            target_adjustment = False
            anomaly_accountability = subject_has_access
        metric.access_level = access_level
        metric.query_channel = query_channel
        self.signal_records[f"access:{metric_id}"] = {
            "subject_has_access": subject_has_access,
            "target_adjustment": target_adjustment,
            "subject_accountable_for_unseen_anomaly": anomaly_accountability,
        }
        return self._commit(command, 233)

    def record_signals_234(
        self,
        command: CommandToken,
        *,
        signal_id: str,
        metric_id: str,
        leading_value: int,
        lagging_value: int | None,
    ) -> ActionResult:
        gate = self._gate(command, 234)
        if gate:
            return gate
        signal_id = self._text(signal_id, "signal_id")
        self._metric(metric_id)
        leading_value = self._integer(
            leading_value, "leading_value", minimum=None
        )
        if lagging_value is not None:
            lagging_value = self._integer(
                lagging_value, "lagging_value", minimum=None
            )
        if signal_id in self.signal_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "signal record exists")
        self.signal_records[signal_id] = {
            "metric_id": metric_id,
            "leading_value": leading_value,
            "lagging_value": lagging_value,
            "recognition": "provisional" if lagging_value is None else "settled",
            "conflict_requires_calibration": (
                lagging_value is not None and (leading_value > 0) != (lagging_value > 0)
            ),
        }
        return self._commit(command, 234)

    def evaluate_guardrail_235(
        self,
        command: CommandToken,
        *,
        assessment_id: str,
        primary_value: int,
        guardrail_value: int,
        guardrail_floor: int,
        crisis_override: bool,
        override_approver_id: str | None,
    ) -> ActionResult:
        gate = self._gate(command, 235)
        if gate:
            return gate
        assessment_id = self._text(assessment_id, "assessment_id")
        primary_value = self._integer(primary_value, "primary_value")
        guardrail_value = self._integer(guardrail_value, "guardrail_value")
        guardrail_floor = self._integer(guardrail_floor, "guardrail_floor")
        crisis_override = self._boolean(crisis_override, "crisis_override")
        breached = guardrail_value < guardrail_floor
        if crisis_override:
            override_approver_id = self._text(
                override_approver_id, "override_approver_id"
            )
        elif override_approver_id is not None:
            raise DomainRed(RedCode.INVALID_VALUE, "non-crisis assessment has no override")
        if assessment_id in self.guardrails:
            raise DomainRed(RedCode.STATE_CONFLICT, "guardrail assessment exists")
        self.guardrails[assessment_id] = {
            "primary_value": primary_value,
            "guardrail_value": guardrail_value,
            "breached": breached,
            "full_top_credit": not breached or crisis_override,
            "delayed_liability_owner": override_approver_id if crisis_override else None,
        }
        return self._commit(command, 235)

    def lock_scoring_policy_236(
        self,
        command: CommandToken,
        *,
        metric_id: str,
        policy: ScoringPolicy,
        threshold: int,
    ) -> ActionResult:
        gate = self._gate(command, 236)
        if gate:
            return gate
        metric = self._metric(metric_id)
        policy = self._enum(policy, ScoringPolicy, "scoring policy")
        threshold = self._integer(threshold, "threshold", minimum=1)
        if metric.scoring_policy is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "scoring policy already frozen")
        metric.scoring_policy = policy
        self.signal_records[f"scoring:{metric_id}"] = {
            "threshold": threshold,
            "frozen_cycle": self.cycle_serial,
            "year_end_mutable": False,
        }
        return self._commit(command, 236)

    def audit_time_window_237(
        self,
        command: CommandToken,
        *,
        audit_id: str,
        frozen_start: int,
        frozen_end: int,
        claimed_start: int,
        claimed_end: int,
        full_period_value: int,
        claimed_value: int,
    ) -> ActionResult:
        gate = self._gate(command, 237)
        if gate:
            return gate
        audit_id = self._text(audit_id, "audit_id")
        values = {
            label: self._integer(value, label)
            for label, value in (
                ("frozen_start", frozen_start),
                ("frozen_end", frozen_end),
                ("claimed_start", claimed_start),
                ("claimed_end", claimed_end),
                ("full_period_value", full_period_value),
                ("claimed_value", claimed_value),
            )
        }
        if values["frozen_start"] >= values["frozen_end"] or values[
            "claimed_start"
        ] >= values["claimed_end"]:
            raise DomainRed(RedCode.INVALID_VALUE, "time window is invalid")
        if audit_id in self.window_audits:
            raise DomainRed(RedCode.STATE_CONFLICT, "window audit exists")
        cherry_picked = (
            values["claimed_start"] != values["frozen_start"]
            or values["claimed_end"] != values["frozen_end"]
        )
        self.window_audits[audit_id] = {
            **values,
            "cherry_picked": cherry_picked,
            "settled_value": values["full_period_value"],
            "integrity_penalty": cherry_picked
            and values["claimed_value"] > values["full_period_value"],
        }
        return self._commit(command, 237)

    def settle_vanity_value_238(
        self,
        command: CommandToken,
        *,
        settlement_id: str,
        vanity_value: int,
        adoption_value: int,
        governance_value: int,
        provisional_credit: int,
    ) -> ActionResult:
        gate = self._gate(command, 238)
        if gate:
            return gate
        settlement_id = self._text(settlement_id, "settlement_id")
        values = tuple(
            self._integer(value, label)
            for value, label in (
                (vanity_value, "vanity_value"),
                (adoption_value, "adoption_value"),
                (governance_value, "governance_value"),
                (provisional_credit, "provisional_credit"),
            )
        )
        if settlement_id in self.value_settlements:
            raise DomainRed(RedCode.STATE_CONFLICT, "value settlement exists")
        _vanity, adoption, governance, credit = values
        realized = adoption > 0 or governance > 0
        self.value_settlements[settlement_id] = {
            "vanity_value": values[0],
            "adoption_value": adoption,
            "governance_value": governance,
            "realized_value": realized,
            "credit_kept": credit if realized else 0,
            "credit_clawback": 0 if realized else credit,
        }
        return self._commit(command, 238)

    def settle_failed_experiment_239(
        self,
        command: CommandToken,
        *,
        experiment_id: str,
        hypothesis: str,
        preregistered: bool,
        stopped_on_evidence: bool,
        reusable_conclusion: bool,
    ) -> ActionResult:
        gate = self._gate(command, 239)
        if gate:
            return gate
        experiment_id = self._text(experiment_id, "experiment_id")
        hypothesis = self._text(hypothesis, "hypothesis")
        flags = tuple(
            self._boolean(value, label)
            for value, label in (
                (preregistered, "preregistered"),
                (stopped_on_evidence, "stopped_on_evidence"),
                (reusable_conclusion, "reusable_conclusion"),
            )
        )
        if experiment_id in self.experiments:
            raise DomainRed(RedCode.STATE_CONFLICT, "experiment outcome exists")
        learning_credit = 20 if all(flags) else 0
        self.experiments[experiment_id] = {
            "hypothesis": hypothesis,
            "main_goal_succeeded": False,
            "learning_credit": learning_credit,
            "success_kpi_credit": 0,
            "quality_negative_result": all(flags),
        }
        return self._commit(command, 239)

    def allocate_sample_240(
        self,
        command: CommandToken,
        *,
        experiment_id: str,
        samples: tuple[str, ...],
        route: SampleConflictRoute,
        provenance_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 240)
        if gate:
            return gate
        experiment_id = self._text(experiment_id, "experiment_id")
        if experiment_id in self.sample_allocations:
            raise DomainRed(RedCode.STATE_CONFLICT, "sample allocation exists")
        if not isinstance(samples, tuple) or not samples:
            raise DomainRed(RedCode.INVALID_TYPE, "samples must be a non-empty tuple")
        sample_rows = tuple(self._text(row, "sample") for row in samples)
        if len(sample_rows) != len(set(sample_rows)):
            raise DomainRed(RedCode.INVALID_VALUE, "samples must be unique")
        route = self._enum(route, SampleConflictRoute, "sample conflict route")
        occupied = {
            sample
            for allocation in self.sample_allocations.values()
            if allocation.active
            for sample in allocation.samples
        }
        overlap = bool(occupied.intersection(sample_rows))
        if route is SampleConflictRoute.PARTITION and overlap:
            raise DomainRed(RedCode.INVALID_VALUE, "partitioned samples cannot overlap")
        active = not (route is SampleConflictRoute.QUEUE and overlap)
        contaminated = route is SampleConflictRoute.ACCEPT_CONTAMINATION and overlap
        if active and self.active_sample_slots >= self.sample_slot_total:
            raise DomainRed(RedCode.SAMPLE_SLOT_EXHAUSTED, "no experiment window remains")
        provenance_id = self._check_provenance(
            provenance_id, f"sample:{experiment_id}"
        )
        self.sample_allocations[experiment_id] = SampleAllocation(
            experiment_id, sample_rows, route, active, contaminated, provenance_id
        )
        self._register_provenance(provenance_id, f"sample:{experiment_id}")
        return self._commit(command, 240)

    def set_long_tail_attribution_241(
        self,
        command: CommandToken,
        *,
        attribution_id: str,
        project_id: str,
        start_cycle: int,
        end_cycle: int,
        shares: Mapping[str, int],
    ) -> ActionResult:
        gate = self._gate(command, 241)
        if gate:
            return gate
        attribution_id = self._text(attribution_id, "attribution_id")
        project_id = self._text(project_id, "project_id")
        start_cycle = self._integer(start_cycle, "start_cycle", minimum=self.cycle_serial)
        end_cycle = self._integer(end_cycle, "end_cycle", minimum=start_cycle + 1)
        if not isinstance(shares, Mapping) or len(shares) < 2:
            raise DomainRed(RedCode.INVALID_TYPE, "attribution shares need at least two roles")
        candidate = {
            self._text(actor, "attribution actor"): self._integer(
                share, "attribution share"
            )
            for actor, share in shares.items()
        }
        if sum(candidate.values()) != SHARE_TOTAL_BPS:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "long-tail shares must total 10000")
        if attribution_id in self.long_tail_attributions:
            raise DomainRed(RedCode.STATE_CONFLICT, "attribution window exists")
        self.long_tail_attributions[attribution_id] = {
            "project_id": project_id,
            "start_cycle": start_cycle,
            "end_cycle": end_cycle,
            "benefit_shares": candidate,
            "delayed_cost_shares": dict(candidate),
        }
        return self._commit(command, 241)

    def normalize_halo_301(
        self,
        command: CommandToken,
        *,
        record_id: str,
        raw_outcome: int,
        strategic_tailwind: int,
        resource_advantage: int,
        scale_difficulty: int,
        evidence_strength: int,
    ) -> ActionResult:
        gate = self._gate(command, 301)
        if gate:
            return gate
        record_id = self._text(record_id, "record_id")
        raw_outcome = self._integer(raw_outcome, "raw_outcome")
        strategic_tailwind = self._integer(strategic_tailwind, "strategic_tailwind")
        resource_advantage = self._integer(resource_advantage, "resource_advantage")
        scale_difficulty = self._integer(scale_difficulty, "scale_difficulty")
        evidence_strength = self._integer(evidence_strength, "evidence_strength")
        if record_id in self.halo_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "halo record exists")
        requested_adjustment = scale_difficulty - strategic_tailwind - resource_advantage
        cap = 20 if evidence_strength >= 60 else 5
        adjustment = max(-cap, min(cap, requested_adjustment))
        self.halo_records[record_id] = {
            "raw_outcome": raw_outcome,
            "personal_increment": raw_outcome + adjustment,
            "adjustment": adjustment,
            "adjustment_cap": cap,
        }
        return self._commit(command, 301)

    def evaluate_decline_302(
        self,
        command: CommandToken,
        *,
        record_id: str,
        expected_decline: int,
        actual_decline: int,
        action: str,
        disclosed: bool,
    ) -> ActionResult:
        gate = self._gate(command, 302)
        if gate:
            return gate
        record_id = self._text(record_id, "record_id")
        expected_decline = self._integer(expected_decline, "expected_decline")
        actual_decline = self._integer(actual_decline, "actual_decline")
        action = self._text(action, "action")
        disclosed = self._boolean(disclosed, "disclosed")
        if record_id in self.decline_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "decline record exists")
        self.decline_records[record_id] = {
            "action": action,
            "decline_avoided": expected_decline - actual_decline,
            "high_quality_defense": actual_decline < expected_decline,
            "integrity_penalty": not disclosed,
            "permanent_headwind_immunity": False,
        }
        return self._commit(command, 302)

    def grant_incubation_303(
        self,
        command: CommandToken,
        *,
        team_id: str,
        start_cycle: int,
        end_cycle: int,
        exit_route: str,
        milestone_evidence: bool,
    ) -> ActionResult:
        gate = self._gate(command, 303)
        if gate:
            return gate
        team_id = self._text(team_id, "team_id")
        start_cycle = self._integer(start_cycle, "start_cycle", minimum=self.cycle_serial)
        end_cycle = self._integer(end_cycle, "end_cycle", minimum=start_cycle + 1)
        exit_route = self._text(exit_route, "exit_route")
        milestone_evidence = self._boolean(milestone_evidence, "milestone_evidence")
        if end_cycle - start_cycle > 2:
            raise DomainRed(RedCode.INVALID_VALUE, "incubation protection lasts at most two cycles")
        if exit_route not in {"graduate", "pivot", "close"}:
            raise DomainRed(RedCode.INVALID_VALUE, "incubation needs a terminal route")
        if team_id in self.incubations:
            raise DomainRed(RedCode.STATE_CONFLICT, "incubation exists")
        self.incubations[team_id] = {
            "start_cycle": start_cycle,
            "end_cycle": end_cycle,
            "exit_route": exit_route,
            "milestone_evidence": milestone_evidence,
            "protected_from_mature_absolute_comparison": True,
            "permanent_c_immunity": False,
        }
        return self._commit(command, 303)

    def lock_dual_parent_304(
        self,
        command: CommandToken,
        *,
        subject_id: str,
        manager_weights: Mapping[str, int],
        goal_shares: Mapping[str, int],
        final_owner_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 304)
        if gate:
            return gate
        subject_id = self._text(subject_id, "subject_id")
        final_owner_id = self._text(final_owner_id, "final_owner_id")
        if subject_id in self.dual_parent_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "dual-parent contract exists")
        if not isinstance(manager_weights, Mapping) or not isinstance(goal_shares, Mapping):
            raise DomainRed(RedCode.INVALID_TYPE, "dual-parent inputs must be mappings")
        weights = {
            self._text(actor, "manager"): self._integer(weight, "manager weight", minimum=1)
            for actor, weight in manager_weights.items()
        }
        goals = {
            self._text(actor, "goal owner"): self._integer(share, "goal share", minimum=0)
            for actor, share in goal_shares.items()
        }
        if len(weights) != 2 or sum(weights.values()) != 100:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "manager weights must total 100")
        if set(weights) != set(goals) or sum(goals.values()) != 100:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "goal capacity must total 100 once")
        if final_owner_id not in weights:
            raise DomainRed(RedCode.OWNER_CONFLICT, "final owner must be one parent")
        self.dual_parent_records[subject_id] = {
            "manager_weights": weights,
            "goal_shares": goals,
            "final_owner_id": final_owner_id,
        }
        return self._commit(command, 304)

    def apply_reorg_305(
        self,
        command: CommandToken,
        *,
        reorg_id: str,
        days_to_evidence_cutoff: int,
        crisis_reason: str | None,
        superior_signer_id: str | None,
        moved_subjects: tuple[str, ...],
    ) -> ActionResult:
        gate = self._gate(command, 305)
        if gate:
            return gate
        reorg_id = self._text(reorg_id, "reorg_id")
        days_to_evidence_cutoff = self._integer(
            days_to_evidence_cutoff, "days_to_evidence_cutoff"
        )
        if not isinstance(moved_subjects, tuple) or not moved_subjects:
            raise DomainRed(RedCode.INVALID_TYPE, "moved_subjects must be non-empty tuple")
        subjects = tuple(self._text(row, "moved subject") for row in moved_subjects)
        in_quiet_period = days_to_evidence_cutoff <= 30
        if in_quiet_period:
            if not crisis_reason or not superior_signer_id:
                raise DomainRed(
                    RedCode.QUIET_PERIOD_VIOLATION,
                    "quiet-period reorg requires crisis reason and superior signature",
                )
            crisis_reason = self._text(crisis_reason, "crisis_reason")
            superior_signer_id = self._text(superior_signer_id, "superior_signer_id")
        elif crisis_reason is not None or superior_signer_id is not None:
            raise DomainRed(RedCode.INVALID_VALUE, "normal reorg does not use crisis override")
        if reorg_id in self.reorg_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "reorg exists")
        self.reorg_records[reorg_id] = {
            "moved_subjects": subjects,
            "quiet_period": in_quiet_period,
            "crisis_reason": crisis_reason,
            "superior_signer_id": superior_signer_id,
            "old_cohort_frozen": in_quiet_period,
            "management_penalty": False,
        }
        return self._commit(command, 305)

    def assign_double_hat_306(
        self,
        command: CommandToken,
        *,
        actor_id: str,
        group_weights: Mapping[str, int],
        expires_cycle: int,
        appointing_owner_id: str,
        support: str,
    ) -> ActionResult:
        gate = self._gate(command, 306)
        if gate:
            return gate
        actor_id = self._text(actor_id, "actor_id")
        appointing_owner_id = self._text(appointing_owner_id, "appointing_owner_id")
        support = self._text(support, "support")
        expires_cycle = self._integer(
            expires_cycle, "expires_cycle", minimum=self.cycle_serial + 1
        )
        if actor_id in self.double_hat_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "double-hat assignment exists")
        if not isinstance(group_weights, Mapping) or len(group_weights) != 2:
            raise DomainRed(RedCode.INVALID_TYPE, "double-hat needs two group weights")
        weights = {
            self._text(group, "group"): self._integer(weight, "group weight", minimum=1)
            for group, weight in group_weights.items()
        }
        if sum(weights.values()) != 100:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "double-hat capacity must total 100")
        if support not in {"allowance", "target_reduction", "deputy"}:
            raise DomainRed(RedCode.INVALID_VALUE, "invalid double-hat support")
        self.double_hat_records[actor_id] = {
            "group_weights": weights,
            "expires_cycle": expires_cycle,
            "appointing_owner_id": appointing_owner_id,
            "support": support,
            "two_full_targets": False,
        }
        return self._commit(command, 306)

    def configure_scorecard_307(
        self,
        command: CommandToken,
        *,
        team_id: str,
        center_type: CenterType,
        metric_keys: tuple[str, ...],
    ) -> ActionResult:
        gate = self._gate(command, 307)
        if gate:
            return gate
        team_id = self._text(team_id, "team_id")
        center_type = self._enum(center_type, CenterType, "center_type")
        if not isinstance(metric_keys, tuple):
            raise DomainRed(RedCode.INVALID_TYPE, "metric_keys must be tuple")
        metrics = tuple(self._text(row, "scorecard metric") for row in metric_keys)
        required = (
            {"revenue", "quality"}
            if center_type is CenterType.PROFIT
            else {"savings", "stability", "internal_value"}
        )
        if not required.issubset(metrics):
            raise DomainRed(RedCode.INVALID_VALUE, "scorecard lacks center-specific metrics")
        if team_id in self.scorecards:
            raise DomainRed(RedCode.STATE_CONFLICT, "scorecard exists")
        self.scorecards[team_id] = {
            "center_type": center_type,
            "metrics": metrics,
            "forced_common_metric": False,
        }
        return self._commit(command, 307)

    def rebalance_hc_308(
        self, command: CommandToken, *, manager_hc: int, expert_hc: int
    ) -> ActionResult:
        gate = self._gate(command, 308)
        if gate:
            return gate
        manager_hc = self._integer(manager_hc, "manager_hc", minimum=1)
        expert_hc = self._integer(expert_hc, "expert_hc", minimum=1)
        if manager_hc + expert_hc != self.total_hc:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "manager/expert HC must conserve")
        self.manager_hc = manager_hc
        self.expert_hc = expert_hc
        self.scorecards["hc-structure"] = {
            "manager_hc": manager_hc,
            "expert_hc": expert_hc,
            "reporting_tax": manager_hc * 2,
            "management_span": (self.total_hc + manager_hc - 1) // manager_hc,
        }
        return self._commit(command, 308)

    def visit_remote_team_309(
        self,
        command: CommandToken,
        *,
        team_id: str,
        manager_hours: int,
        visibility_gain: int,
    ) -> ActionResult:
        gate = self._gate(command, 309)
        if gate:
            return gate
        team_id = self._text(team_id, "team_id")
        manager_hours = self._integer(manager_hours, "manager_hours", minimum=1)
        visibility_gain = self._integer(visibility_gain, "visibility_gain", minimum=1)
        if team_id in self.remote_visits:
            raise DomainRed(RedCode.STATE_CONFLICT, "remote visit exists")
        if self.management_capacity_used + manager_hours > self.management_capacity_total:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "management capacity exceeded")
        self.management_capacity_used += manager_hours
        self.remote_visits[team_id] = {
            "manager_hours": manager_hours,
            "visibility_gain": visibility_gain,
            "delivery_output_created": 0,
        }
        return self._commit(command, 309)

    def map_legacy_ratings_310(
        self,
        command: CommandToken,
        *,
        team_id: str,
        old_ratings: Mapping[str, str],
        mapping_route: str,
        historical_owner_id: str,
        mapped_owner_id: str,
        bridge_signers: tuple[str, str],
    ) -> ActionResult:
        gate = self._gate(command, 310)
        if gate:
            return gate
        team_id = self._text(team_id, "team_id")
        mapping_route = self._text(mapping_route, "mapping_route")
        historical_owner_id = self._text(historical_owner_id, "historical_owner_id")
        mapped_owner_id = self._text(mapped_owner_id, "mapped_owner_id")
        if mapping_route not in {"equivalence", "context_only", "common_baseline"}:
            raise DomainRed(RedCode.INVALID_VALUE, "invalid legacy mapping route")
        if not isinstance(old_ratings, Mapping) or not old_ratings:
            raise DomainRed(RedCode.INVALID_TYPE, "old_ratings must be non-empty mapping")
        ratings = {
            self._text(actor, "legacy actor"): self._text(rating, "legacy rating")
            for actor, rating in old_ratings.items()
        }
        if historical_owner_id == mapped_owner_id:
            raise DomainRed(RedCode.INVALID_VALUE, "legacy bridge requires old and new owners")
        if not isinstance(bridge_signers, tuple) or len(bridge_signers) != 2:
            raise DomainRed(RedCode.INVALID_TYPE, "legacy bridge requires two signatures")
        signers = tuple(self._text(row, "bridge signer") for row in bridge_signers)
        if set(signers) != {historical_owner_id, mapped_owner_id}:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "legacy bridge signatures do not match owners")
        if team_id in self.legacy_maps:
            raise DomainRed(RedCode.STATE_CONFLICT, "legacy map exists")
        self.legacy_maps[team_id] = {
            "old_ratings": ratings,
            "mapping_route": mapping_route,
            "historical_context_only": True,
            "current_quota_slots_consumed": 0,
            "mapping_version": 1,
            "historical_owner_id": historical_owner_id,
            "mapped_owner_id": mapped_owner_id,
            "bridge_signers": signers,
        }
        return self._commit(command, 310)

    def pivot_strategy_311(
        self,
        command: CommandToken,
        *,
        pivot_id: str,
        old_goal_id: str,
        old_goal_completed: int,
        new_goal_id: str,
        effective_day: int,
    ) -> ActionResult:
        gate = self._gate(command, 311)
        if gate:
            return gate
        pivot_id = self._text(pivot_id, "pivot_id")
        old_goal_id = self._text(old_goal_id, "old_goal_id")
        new_goal_id = self._text(new_goal_id, "new_goal_id")
        old_goal_completed = self._integer(old_goal_completed, "old_goal_completed")
        effective_day = self._integer(effective_day, "effective_day", minimum=1)
        if old_goal_id == new_goal_id:
            raise DomainRed(RedCode.INVALID_VALUE, "pivot requires a new goal")
        if pivot_id in self.pivots:
            raise DomainRed(RedCode.STATE_CONFLICT, "pivot exists")
        self.pivots[pivot_id] = {
            "old_goal_id": old_goal_id,
            "old_goal_completed": old_goal_completed,
            "old_goal_rewritten": False,
            "new_goal_id": new_goal_id,
            "effective_day": effective_day,
        }
        return self._commit(command, 311)

    def submit_demand_334(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        source: DemandSource,
        source_owner_id: str,
        proposer_id: str,
        executor_id: str,
        beneficiary_id: str,
        deadline_cycle: int,
        provenance_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 334)
        if gate:
            return gate
        demand_id = self._text(demand_id, "demand_id")
        source = self._enum(source, DemandSource, "demand source")
        source_owner_id = self._text(source_owner_id, "source_owner_id")
        proposer_id = self._text(proposer_id, "proposer_id")
        executor_id = self._text(executor_id, "executor_id")
        beneficiary_id = self._text(beneficiary_id, "beneficiary_id")
        deadline_cycle = self._integer(
            deadline_cycle, "deadline_cycle", minimum=self.cycle_serial
        )
        if len({proposer_id, executor_id, beneficiary_id}) != 3:
            raise DomainRed(
                RedCode.SIGNATURE_REQUIRED,
                "demand must freeze three distinct delivery roles",
            )
        if demand_id in self.demands:
            raise DomainRed(RedCode.STATE_CONFLICT, "demand already entered")
        provenance_id = self._check_provenance(provenance_id, f"demand:{demand_id}")
        self.demands[demand_id] = Demand(
            demand_id=demand_id,
            object_owner_id=self.owner_id,
            object_cycle_serial=self.cycle_serial,
            object_case_serial=self.case_serial,
            object_version=1,
            deadline_cycle=deadline_cycle,
            source=source,
            source_owner_id=source_owner_id,
            proposer_id=proposer_id,
            executor_id=executor_id,
            beneficiary_id=beneficiary_id,
            provenance_id=provenance_id,
            queue_sequence=len(self.demands),
        )
        self._register_provenance(provenance_id, f"demand:{demand_id}")
        return self._commit(command, 334)

    def mark_emergency_335(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        overflow_tradeoff: str | None,
    ) -> ActionResult:
        gate = self._gate(command, 335)
        if gate:
            return gate
        demand = self._demand(demand_id)
        if demand.emergency:
            raise DomainRed(RedCode.STATE_CONFLICT, "demand already marked emergency")
        if self.emergency_slots_used < self.emergency_slot_total:
            if overflow_tradeoff is not None:
                raise DomainRed(RedCode.INVALID_VALUE, "unused emergency slot needs no tradeoff")
            tradeoff = "reserved_slot"
            consumes_slot = True
        else:
            overflow_tradeoff = self._text(overflow_tradeoff, "overflow_tradeoff")
            if overflow_tradeoff not in {"delay_old", "add_capacity", "sponsor_liability"}:
                raise DomainRed(RedCode.EMERGENCY_SLOT_EXHAUSTED, "overflow needs explicit tradeoff")
            tradeoff = overflow_tradeoff
            consumes_slot = False
        demand.emergency = True
        demand.emergency_tradeoff = tradeoff
        if consumes_slot:
            self.emergency_slots_used += 1
        self._touch_demand(demand)
        return self._commit(command, 335)

    def admit_demand_336(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        benefit: str | None,
        acceptance: str | None,
        boundary: str | None,
        dependencies: tuple[str, ...],
        estimated_hours: int,
        route: AdmissionRoute,
        forcing_owner_id: str | None,
    ) -> ActionResult:
        gate = self._gate(command, 336)
        if gate:
            return gate
        demand = self._demand(demand_id)
        if demand.admitted:
            raise DomainRed(RedCode.STATE_CONFLICT, "demand already admitted")
        route = self._enum(route, AdmissionRoute, "admission route")
        estimated_hours = self._integer(estimated_hours, "estimated_hours", minimum=1)
        if not isinstance(dependencies, tuple):
            raise DomainRed(RedCode.INVALID_TYPE, "dependencies must be tuple")
        dependency_rows = tuple(self._text(row, "dependency") for row in dependencies)
        complete = all(
            isinstance(value, str) and bool(value.strip())
            for value in (benefit, acceptance, boundary)
        )
        if route is AdmissionRoute.RETURN:
            if complete:
                raise DomainRed(RedCode.INVALID_VALUE, "complete demand need not be returned")
            forcing_owner_id = None
            admitted = False
        elif route is AdmissionRoute.EXPLORATION:
            if complete:
                raise DomainRed(RedCode.INVALID_VALUE, "complete demand should be committed")
            if estimated_hours > 10:
                raise DomainRed(RedCode.CAPACITY_EXCEEDED, "exploration intake is capped at ten hours")
            forcing_owner_id = None
            admitted = True
        elif route is AdmissionRoute.FORCED_COMMITMENT:
            forcing_owner_id = self._text(forcing_owner_id, "forcing_owner_id")
            admitted = True
        else:
            if not complete:
                raise DomainRed(
                    RedCode.INVALID_VALUE,
                    "ordinary commitment requires benefit, acceptance and boundary",
                )
            if forcing_owner_id is not None:
                raise DomainRed(
                    RedCode.INVALID_VALUE, "ordinary commitment has no forcing owner"
                )
            admitted = True
        demand.benefit = benefit
        demand.acceptance = acceptance
        demand.boundary = boundary
        demand.dependencies = dependency_rows
        demand.estimated_hours = estimated_hours
        demand.admitted = admitted
        demand.admission_route = route
        demand.forced_owner_liability = route is AdmissionRoute.FORCED_COMMITMENT
        self._touch_demand(demand)
        return self._commit(command, 336)

    def change_demand_337(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        route: ChangeRoute,
        tax_hours: int,
        approver_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 337)
        if gate:
            return gate
        demand = self._demand(demand_id)
        route = self._enum(route, ChangeRoute, "change route")
        tax_hours = self._integer(tax_hours, "tax_hours")
        approver_id = self._text(approver_id, "approver_id")
        if not demand.admitted:
            raise DomainRed(RedCode.STATE_CONFLICT, "only admitted demand can change")
        if route is ChangeRoute.DISASTER_WAIVER:
            if demand.disaster_waiver_used:
                raise DomainRed(RedCode.STATE_CONFLICT, "disaster waiver already consumed")
            if tax_hours != 0:
                raise DomainRed(RedCode.INVALID_VALUE, "disaster waiver has no change tax")
        elif tax_hours <= 0:
            raise DomainRed(RedCode.INVALID_VALUE, "ordinary demand change must pay tax")
        additional_reservation = tax_hours if demand.active else 0
        if (
            self.capacity_hours_reserved + additional_reservation
            > self.capacity_hours_total
        ):
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "change capacity unavailable")
        demand.change_tax_hours += tax_hours
        demand.disaster_waiver_used = demand.disaster_waiver_used or (
            route is ChangeRoute.DISASTER_WAIVER
        )
        demand.signatures["change_approver"] = approver_id
        self.capacity_hours_reserved += additional_reservation
        if route is ChangeRoute.EXTEND:
            demand.deadline_cycle += 1
        self._touch_demand(demand)
        if demand_id in self.deliveries:
            delivery = self.deliveries[demand_id]
            delivery.deadline_cycle = demand.deadline_cycle
            delivery.reserved_hours += additional_reservation
            self._touch_delivery(delivery)
        return self._commit(command, 337)

    def sign_delivery_triangle_338(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        tradeoff: TriangleTradeoff,
        approver_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 338)
        if gate:
            return gate
        demand = self._demand(demand_id)
        tradeoff = self._enum(tradeoff, TriangleTradeoff, "triangle tradeoff")
        approver_id = self._text(approver_id, "approver_id")
        if not demand.admitted:
            raise DomainRed(RedCode.STATE_CONFLICT, "triangle requires admitted demand")
        if demand.triangle_tradeoff is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "delivery triangle already signed")
        demand.triangle_tradeoff = tradeoff
        demand.triangle_approver_id = approver_id
        demand.quality_liability_id = (
            approver_id if tradeoff is TriangleTradeoff.LOWER_QUALITY else None
        )
        if tradeoff is TriangleTradeoff.EXTEND_TIME:
            demand.deadline_cycle += 1
        self._touch_demand(demand)
        return self._commit(command, 338)

    def calibrate_estimate_339(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        actual_hours: int,
        complexity_miss: bool,
        external_blocking_hours: int,
    ) -> ActionResult:
        gate = self._gate(command, 339)
        if gate:
            return gate
        demand = self._demand(demand_id)
        actual_hours = self._integer(actual_hours, "actual_hours", minimum=1)
        complexity_miss = self._boolean(complexity_miss, "complexity_miss")
        external_blocking_hours = self._integer(
            external_blocking_hours, "external_blocking_hours"
        )
        if not demand.admitted or demand.actual_hours is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "estimate cannot be calibrated")
        normalized_actual = max(0, actual_hours - external_blocking_hours)
        error = normalized_actual - demand.estimated_hours
        if error > 0 and complexity_miss:
            reason = "complexity_miss"
        elif error > 0:
            reason = "unexplained_overrun"
        elif error < -(demand.estimated_hours // 3):
            reason = "probable_padding"
        else:
            reason = "calibrated"
        demand.actual_hours = actual_hours
        demand.estimate_error = error
        demand.estimate_reason = reason
        self._touch_demand(demand)
        return self._commit(command, 339)

    def start_work_340(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        exception_owner_id: str | None,
        hidden_extra_wip: bool,
    ) -> ActionResult:
        gate = self._gate(command, 340)
        if gate:
            return gate
        demand = self._demand(demand_id)
        hidden_extra_wip = self._boolean(hidden_extra_wip, "hidden_extra_wip")
        if not demand.admitted or demand.active:
            raise DomainRed(RedCode.STATE_CONFLICT, "demand cannot enter WIP")
        exceeds = self.active_wip >= self.wip_limit
        if exceeds:
            if hidden_extra_wip:
                exception_owner_id = None
                penalty = 2
            else:
                exception_owner_id = self._text(exception_owner_id, "exception_owner_id")
                penalty = 0
        else:
            if exception_owner_id is not None or hidden_extra_wip:
                raise DomainRed(RedCode.INVALID_VALUE, "unused WIP capacity needs no exception")
            penalty = 0
        demand_capacity = demand.estimated_hours + demand.change_tax_hours
        if self.capacity_hours_reserved + demand_capacity > self.capacity_hours_total:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "delivery capacity exceeded")
        if demand_id in self.deliveries:
            raise DomainRed(RedCode.STATE_CONFLICT, "delivery object already exists")
        demand.active = True
        demand.wip_exception_owner_id = exception_owner_id
        demand.hidden_wip_penalty = penalty
        self.capacity_hours_reserved += demand_capacity
        self.deliveries[demand_id] = Delivery(
            delivery_id=f"delivery:{demand_id}",
            demand_id=demand_id,
            owner_id=demand.object_owner_id,
            executor_id=demand.executor_id,
            beneficiary_id=demand.beneficiary_id,
            cycle_serial=demand.object_cycle_serial,
            case_serial=demand.object_case_serial,
            deadline_cycle=demand.deadline_cycle,
            version=1,
            status=DeliveryStatus.IN_WIP,
            reserved_hours=demand_capacity,
        )
        self._touch_demand(demand)
        return self._commit(command, 340)

    def carryover_demand_341(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        unfinished_hours: int,
        accepted_hours: int,
        route: CarryoverRoute,
    ) -> ActionResult:
        gate = self._gate(command, 341)
        if gate:
            return gate
        demand = self._demand(demand_id)
        delivery = self._delivery(demand_id)
        if delivery.status is not DeliveryStatus.IN_WIP:
            raise DomainRed(RedCode.STATE_CONFLICT, "carryover requires active WIP")
        unfinished_hours = self._integer(unfinished_hours, "unfinished_hours")
        accepted_hours = self._integer(accepted_hours, "accepted_hours")
        route = self._enum(route, CarryoverRoute, "carryover route")
        if not demand.active:
            raise DomainRed(RedCode.STATE_CONFLICT, "only WIP can carry over")
        if unfinished_hours + accepted_hours > demand.estimated_hours + demand.change_tax_hours:
            raise DomainRed(RedCode.INVALID_VALUE, "carryover exceeds demand ledger")
        reserve = unfinished_hours if route in (CarryoverRoute.CARRY, CarryoverRoute.SPLIT_ACCEPTED) else 0
        if self.next_cycle_capacity_reserved + reserve > self.next_cycle_capacity_total:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "next-cycle capacity exceeded")
        self.next_cycle_capacity_reserved += reserve
        demand.carryover_hours = reserve
        demand.accepted_hours = accepted_hours
        demand.active = False
        self.capacity_hours_reserved -= demand.estimated_hours + demand.change_tax_hours
        if route is CarryoverRoute.CANCEL:
            demand.admitted = False
            delivery.status = DeliveryStatus.CANCELLED
        else:
            delivery.status = DeliveryStatus.CARRIED
        delivery.reserved_hours = 0
        delivery.carryover_hours = reserve
        delivery.accepted_hours = accepted_hours
        self._touch_delivery(delivery)
        self._touch_demand(demand)
        return self._commit(command, 341)

    def record_blocker_342(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        blocker_owner_id: str,
        blocked_since_day: int,
        escalated_day: int | None,
    ) -> ActionResult:
        gate = self._gate(command, 342)
        if gate:
            return gate
        demand = self._demand(demand_id)
        delivery = self._delivery(demand_id)
        if delivery.status is not DeliveryStatus.IN_WIP:
            raise DomainRed(RedCode.STATE_CONFLICT, "blocker requires active WIP")
        blocker_owner_id = self._text(blocker_owner_id, "blocker_owner_id")
        blocked_since_day = self._integer(blocked_since_day, "blocked_since_day", minimum=1)
        if escalated_day is not None:
            escalated_day = self._integer(
                escalated_day, "escalated_day", minimum=blocked_since_day
            )
        if demand.blocker is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "blocker already frozen")
        demand.blocker = {
            "owner_id": blocker_owner_id,
            "blocked_since_day": blocked_since_day,
            "escalated_day": escalated_day,
            "executor_low_output_penalty": False,
            "executor_shared_responsibility": escalated_day is None,
            "blocker_collaboration_penalty": True,
        }
        self._touch_demand(demand)
        self._touch_delivery(delivery)
        return self._commit(command, 342)

    def accept_delivery_343(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        proposer_signer_id: str,
        executor_signer_id: str,
        beneficiary_signer_id: str,
        outcome: AcceptanceOutcome,
    ) -> ActionResult:
        gate = self._gate(command, 343)
        if gate:
            return gate
        demand = self._demand(demand_id)
        signers = {
            "proposer": self._text(proposer_signer_id, "proposer_signer_id"),
            "executor": self._text(executor_signer_id, "executor_signer_id"),
            "beneficiary": self._text(beneficiary_signer_id, "beneficiary_signer_id"),
        }
        outcome = self._enum(outcome, AcceptanceOutcome, "acceptance outcome")
        if len(set(signers.values())) != 3:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "delivery requires three distinct roles")
        if signers["proposer"] != demand.proposer_id:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "proposer signature does not match intake")
        if signers["executor"] != demand.executor_id:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "executor signature does not match intake")
        if signers["beneficiary"] != demand.beneficiary_id:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "beneficiary signature does not match intake")
        if demand.acceptance_outcome is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "delivery already accepted or rejected")
        delivery = self._delivery(demand_id)
        if delivery.status is DeliveryStatus.CANCELLED or delivery.accepted_hours <= 0:
            raise DomainRed(RedCode.STATE_CONFLICT, "delivery has no accepted work to sign")
        demand.signatures.update(signers)
        demand.acceptance_outcome = outcome
        delivery.status = {
            AcceptanceOutcome.ACCEPTED: DeliveryStatus.ACCEPTED,
            AcceptanceOutcome.CONDITIONAL: DeliveryStatus.CONDITIONAL,
            AcceptanceOutcome.REJECTED: DeliveryStatus.REJECTED,
        }[outcome]
        self._touch_delivery(delivery)
        self._touch_demand(demand)
        return self._commit(command, 343)

    def settle_value_stage_344(
        self,
        command: CommandToken,
        *,
        demand_id: str,
        stage: ValueStage,
        credit_basis_points: int,
    ) -> ActionResult:
        gate = self._gate(command, 344)
        if gate:
            return gate
        demand = self._demand(demand_id)
        delivery = self._delivery(demand_id)
        stage = self._enum(stage, ValueStage, "value stage")
        credit_basis_points = self._integer(
            credit_basis_points, "credit_basis_points", minimum=1
        )
        if demand.acceptance_outcome not in (
            AcceptanceOutcome.ACCEPTED,
            AcceptanceOutcome.CONDITIONAL,
        ):
            raise DomainRed(RedCode.STATE_CONFLICT, "unaccepted delivery cannot settle value")
        if stage in demand.value_credits:
            raise DomainRed(RedCode.STATE_CONFLICT, "value stage already settled")
        prerequisites = {
            ValueStage.LAUNCH: set(),
            ValueStage.ADOPTION: {ValueStage.LAUNCH},
            ValueStage.VALUE: {ValueStage.LAUNCH, ValueStage.ADOPTION},
        }[stage]
        if not prerequisites.issubset(demand.value_credits):
            raise DomainRed(RedCode.STATE_CONFLICT, "value stages must settle in order")
        if sum(demand.value_credits.values()) + credit_basis_points > SHARE_TOTAL_BPS:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "staged value credit exceeds 10000")
        demand.value_credits[stage] = credit_basis_points
        delivery.maturity = {
            ValueStage.LAUNCH: 1,
            ValueStage.ADOPTION: 2,
            ValueStage.VALUE: 3,
        }[stage]
        if stage is ValueStage.VALUE:
            delivery.status = DeliveryStatus.VALUED
        self._touch_delivery(delivery)
        self._touch_demand(demand)
        return self._commit(command, 344)

    def assert_invariants(self) -> None:
        if set(MECHANISM_BINDINGS) != EXPECTED_MECHANISM_IDS:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "mechanism coverage drifted")
        if not 0 <= self.active_sample_slots <= self.sample_slot_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "sample slots do not conserve")
        if not 0 <= self.emergency_slots_used <= self.emergency_slot_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "emergency slots do not conserve")
        if not 0 <= self.capacity_hours_reserved <= self.capacity_hours_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "current capacity does not conserve")
        if not 0 <= self.next_cycle_capacity_reserved <= self.next_cycle_capacity_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "next capacity does not conserve")
        if self.active_wip > self.wip_limit + self.wip_exception_count:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "WIP exceeds signed exceptions")
        for demand_id, demand in self.demands.items():
            if (
                demand.object_owner_id != self.owner_id
                or demand.object_cycle_serial != self.cycle_serial
                or demand.object_case_serial != self.case_serial
                or demand.object_version < 1
                or demand.deadline_cycle < demand.object_cycle_serial
            ):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "demand identity/version drifted")
            if len({demand.proposer_id, demand.executor_id, demand.beneficiary_id}) != 3:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "demand roles are not distinct")
            delivery = self.deliveries.get(demand_id)
            if demand.active and delivery is None:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "active demand lacks delivery object")
        for demand_id, delivery in self.deliveries.items():
            demand = self.demands.get(demand_id)
            if demand is None or delivery.demand_id != demand_id:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "orphan delivery object")
            if (
                delivery.owner_id != demand.object_owner_id
                or delivery.executor_id != demand.executor_id
                or delivery.beneficiary_id != demand.beneficiary_id
                or delivery.cycle_serial != demand.object_cycle_serial
                or delivery.case_serial != demand.object_case_serial
                or delivery.version < 1
                or delivery.maturity not in (0, 1, 2, 3)
            ):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "delivery identity/version drifted")
            if delivery.status is DeliveryStatus.IN_WIP:
                if not demand.active or delivery.reserved_hours <= 0:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "WIP delivery lost reservation")
            elif delivery.reserved_hours != 0:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "terminal delivery retained capacity")
            if delivery.maturity != len(demand.value_credits):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "delivery value maturity skipped a stage")
        if self.manager_hc + self.expert_hc != self.total_hc:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "HC structure drifted")
        if not 0 <= self.management_capacity_used <= self.management_capacity_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "management capacity does not conserve")
        for record in self.dual_parent_records.values():
            if sum(record["manager_weights"].values()) != 100 or sum(
                record["goal_shares"].values()
            ) != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "dual-parent weights drifted")
        for record in self.double_hat_records.values():
            if sum(record["group_weights"].values()) != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "double-hat weights drifted")
        for record in self.long_tail_attributions.values():
            if sum(record["benefit_shares"].values()) != SHARE_TOTAL_BPS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "long-tail benefits drifted")
            if record["benefit_shares"] != record["delayed_cost_shares"]:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "long-tail costs lost provenance")
        for demand in self.demands.values():
            if sum(demand.value_credits.values()) > SHARE_TOTAL_BPS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "demand value credit oversettled")
        ordered = sorted(self.receipts.values(), key=lambda row: row.committed_revision)
        for index, receipt in enumerate(ordered):
            if receipt.parent_revision != index or receipt.committed_revision != index + 1:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "command provenance chain broke")


def validate_model_contract() -> None:
    if set(MECHANISM_BINDINGS) != EXPECTED_MECHANISM_IDS:
        raise ValueError("metrics/reorg model must cover the exact requested IDs")
    for mid, binding in MECHANISM_BINDINGS.items():
        if binding.mechanism_id != mid or not binding.behaviors:
            raise ValueError(f"invalid binding for {mid}")
        for behavior in binding.behaviors:
            if not callable(getattr(MetricsReorgModel, behavior, None)):
                raise ValueError(f"mechanism {mid} has no behavior {behavior}")


validate_model_contract()
