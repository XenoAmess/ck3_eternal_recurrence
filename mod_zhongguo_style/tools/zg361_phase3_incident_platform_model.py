#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 kernel for phase-three incident/debt/platform mechanics.

Scope is exactly mechanisms 192--228 (domains X, Y and Z).  The module is a
pure Python executable specification.  It proves command semantics,
conservation, atomic prechecks and provenance; it does not claim CK3 script,
GUI, MCP, fixture-live or production-live readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Final, Iterable, Mapping, Sequence, TypeVar


READINESS: Final[str] = "python-l0-only"
CK3_WIRING: Final[str] = "not-implemented"


class RedCode(str, Enum):
    INVALID_TYPE = "invalid-type"
    INVALID_VALUE = "invalid-value"
    DUPLICATE_ID = "duplicate-id"
    ILLEGAL_STATE = "illegal-state"
    RESOURCE_EXHAUSTED = "resource-exhausted"
    INVARIANT_BREACH = "invariant-breach"
    PERMISSION_DENIED = "permission-denied"
    CONFLICT = "conflict"


class ModelRed(ValueError):
    """Typed RED: code and field are stable, detail is explanatory only."""

    def __init__(self, code: RedCode, field_name: str, detail: str) -> None:
        self.code = RedCode(code)
        self.field_name = field_name
        self.detail = detail
        super().__init__(f"{self.code.value}:{field_name}:{detail}")


class NoOpCode(str, Enum):
    STALE_TOKEN = "stale-token"
    DUPLICATE_ACTION = "duplicate-action"


def _text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be str")
    if not value.strip():
        raise ModelRed(RedCode.INVALID_VALUE, name, "must be non-empty")
    return value


def _integer(
    name: str,
    value: object,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be int, not bool")
    if minimum is not None and value < minimum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be <= {maximum}")
    return value


def _number(
    name: str,
    value: object,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be numeric, not bool")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be <= {maximum}")
    return result


def _boolean(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be bool")
    return value


def _unique(name: str, values: Iterable[str], *, allow_empty: bool = False) -> tuple[str, ...]:
    result = tuple(_text(name, value) for value in values)
    if not allow_empty and not result:
        raise ModelRed(RedCode.INVALID_VALUE, name, "must not be empty")
    if len(result) != len(set(result)):
        raise ModelRed(RedCode.DUPLICATE_ID, name, "must be unique")
    return result


def _shares(name: str, values: Mapping[str, int]) -> dict[str, int]:
    normalized = {
        _text(f"{name}.key", key): _integer(
            f"{name}.{key}", value, minimum=0, maximum=100
        )
        for key, value in values.items()
    }
    if not normalized or sum(normalized.values()) != 100:
        raise ModelRed(RedCode.INVARIANT_BREACH, name, "shares must sum to 100")
    return normalized


@dataclass(frozen=True)
class Behavior:
    mechanism_id: int
    domain: str
    title_cn: str
    behavior_key: str
    invariant_key: str
    readiness: str = READINESS
    ck3_wiring: str = CK3_WIRING


def _behavior(
    mechanism_id: int,
    domain: str,
    title_cn: str,
    behavior_key: str,
    invariant_key: str,
) -> Behavior:
    return Behavior(mechanism_id, domain, title_cn, behavior_key, invariant_key)


BEHAVIORS: Final[dict[int, Behavior]] = {
    192: _behavior(192, "X", "急务值守轮盘", "incident_on_call_rotation", "one_active_responder"),
    193: _behavior(193, "X", "值守津贴 / 调休二选一", "incident_on_call_compensation", "verified_hours_and_money_conserve"),
    194: _behavior(194, "X", "值守对项目目标的等量减免", "workload_on_call_target_relief", "relief_not_above_incident_hours"),
    195: _behavior(195, "X", "假警报与告警质量", "incident_alert_quality", "false_alerts_not_above_total"),
    196: _behavior(196, "X", "事故等级申报博弈", "incident_severity_reporting", "corrected_severity_from_frozen_facts"),
    197: _behavior(197, "X", "事故指挥官与技术救火者分功", "incident_command_responder_credit", "credit_shares_100"),
    198: _behavior(198, "X", "“纵火者拿救火奖”识别", "incident_arsonist_credit_netting", "gross_minus_root_penalty_once"),
    199: _behavior(199, "X", "未发生事故的预防功", "incident_prevention_credit", "bounded_delayed_credit_once"),
    200: _behavior(200, "X", "紧急处置临时授权", "incident_temporary_authority", "scoped_time_bound_authority"),
    201: _behavior(201, "X", "不可改写的事故时间线", "incident_immutable_timeline", "append_only_monotonic_timeline"),
    202: _behavior(202, "X", "复盘行动项 owner", "incident_postmortem_actions", "owner_acceptor_due_and_once"),
    203: _behavior(203, "X", "重复事故升级到管理责任", "incident_repeat_management_liability", "same_key_one_level_once"),
    204: _behavior(204, "X", "可靠性预算与停止上线", "incident_reliability_budget", "budget_floor_zero"),
    205: _behavior(205, "Y", "重复运维（toil）比例上限", "maintenance_toil_cap", "hours_partition"),
    206: _behavior(206, "Y", "积弊本金与利息账", "maintenance_debt_ledger", "debt_balance_provenance"),
    207: _behavior(207, "Y", "固定还债预算", "maintenance_debt_budget", "capacity_conservation"),
    208: _behavior(208, "Y", "渐进修补 / 全面重做", "maintenance_repair_rewrite", "one_route_with_history"),
    209: _behavior(209, "Y", "旧系统危险津贴", "maintenance_hazard_pay", "treasury_recipient_equality"),
    210: _behavior(210, "Y", "维护 owner 轮换", "maintenance_owner_rotation", "one_owner_atomic_rotation"),
    211: _behavior(211, "Y", "文档与操作手册功劳", "learning_runbook_validation", "non_author_validation_once"),
    212: _behavior(212, "Y", "自动化“做完就看不见”悖论", "maintenance_automation_credit", "observed_savings_once"),
    213: _behavior(213, "Y", "审阅与质量把关贡献", "maintenance_review_credit", "validated_findings_not_comment_count"),
    214: _behavior(214, "Y", "覆盖率数字与真实质量", "maintenance_coverage_quality", "coverage_not_sole_score"),
    215: _behavior(215, "Y", "退役旧制度也算交付", "maintenance_legacy_retirement", "hc_release_after_close_once"),
    216: _behavior(216, "Y", "离岗交接完整度", "mobility_handover_completeness", "four_categories_or_waiver"),
    217: _behavior(217, "Z", "共享平台强制采用 / 自愿采用", "platform_adoption_policy", "one_adoption_state_per_team"),
    218: _behavior(218, "Z", "内部客户满意与战略底座双评分", "platform_dual_score", "customer_and_foundation_separate"),
    219: _behavior(219, "Z", "采用数量 / 使用深度 / 节省成本", "platform_adoption_value_metrics", "outcome_and_countermetric"),
    220: _behavior(220, "Z", "共享成本展示与内部结算", "platform_cost_showback_chargeback", "cost_allocation_conservation"),
    221: _behavior(221, "Z", "迁移成本谁来付", "platform_migration_cost_allocation", "three_party_shares_100"),
    222: _behavior(222, "Z", "新旧双跑过渡期", "platform_dual_run_migration", "dual_run_capacity_and_exit_once"),
    223: _behavior(223, "Z", "重复造轮子扫描", "platform_duplicate_scan", "scan_before_proposal"),
    224: _behavior(224, "Z", "重复方案合并赛", "platform_solution_merger", "one_winner_shared_rubric"),
    225: _behavior(225, "Z", "“不是我造的不用”与合法分叉", "platform_legitimate_fork", "approved_difference_and_budget"),
    226: _behavior(226, "Z", "内部开源贡献归因", "platform_inner_source_attribution", "accepted_submission_once"),
    227: _behavior(227, "Z", "创始人、贡献者与维护者分账", "platform_role_credit_split", "role_credit_separate"),
    228: _behavior(228, "Z", "中台事故的爆炸半径责任", "platform_blast_radius_liability", "liability_shares_100_once"),
}

EXPECTED_IDS: Final[frozenset[int]] = frozenset(range(192, 229))


def validate_behavior_registry() -> None:
    if set(BEHAVIORS) != EXPECTED_IDS:
        raise ModelRed(RedCode.INVARIANT_BREACH, "BEHAVIORS", "must be exactly 192..228")
    keys = [row.behavior_key for row in BEHAVIORS.values()]
    if len(keys) != len(set(keys)):
        raise ModelRed(RedCode.DUPLICATE_ID, "behavior_key", "must be unique")
    for mechanism_id, row in BEHAVIORS.items():
        expected_domain = "X" if mechanism_id <= 204 else "Y" if mechanism_id <= 216 else "Z"
        if row.mechanism_id != mechanism_id or row.domain != expected_domain:
            raise ModelRed(RedCode.INVARIANT_BREACH, "behavior", f"bad mapping for {mechanism_id}")
        if row.readiness != READINESS or row.ck3_wiring != CK3_WIRING:
            raise ModelRed(RedCode.INVARIANT_BREACH, "readiness", "readiness inflation")


@dataclass(frozen=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        _text("owner_id", self.owner_id)
        _text("subject_id", self.subject_id)
        _integer("cycle_serial", self.cycle_serial, minimum=1)
        _integer("case_serial", self.case_serial, minimum=1)


@dataclass(frozen=True)
class CaseToken:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    expected_state: str


@dataclass(frozen=True)
class SourceRef:
    source_type: str
    source_id: str
    frozen_version: int

    def __post_init__(self) -> None:
        _text("source_type", self.source_type)
        _text("source_id", self.source_id)
        _integer("frozen_version", self.frozen_version, minimum=1)


@dataclass(frozen=True)
class ProvenanceReceipt:
    receipt_serial: int
    mechanism_id: int
    action_serial: str
    actor_id: str
    before_state: str
    after_state: str
    sources: tuple[SourceRef, ...]
    result_ids: tuple[str, ...]
    payload_sha256: str


@dataclass(frozen=True)
class ActionOutcome:
    mechanism_id: int
    applied: bool
    code: str
    previous_state: str
    current_state: str
    receipt_serial: int | None = None


Prepared = TypeVar("Prepared")


@dataclass
class AtomicCase:
    """Five-field guard plus prepare-then-commit and immutable provenance."""

    identity: CaseIdentity
    state: str
    provenance: list[ProvenanceReceipt] = field(default_factory=list, init=False)
    _actions: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        _text("state", self.state)

    def token(self) -> CaseToken:
        return CaseToken(
            self.identity.owner_id,
            self.identity.subject_id,
            self.identity.cycle_serial,
            self.identity.case_serial,
            self.state,
        )

    def apply(
        self,
        mechanism_id: int,
        token: CaseToken,
        action_serial: str,
        *,
        sources: Iterable[SourceRef],
        prepare: Callable[[], Prepared],
        commit: Callable[[Prepared], Sequence[str]],
        next_state: str | None = None,
    ) -> ActionOutcome:
        mechanism_id = _integer("mechanism_id", mechanism_id)
        if mechanism_id not in EXPECTED_IDS:
            raise ModelRed(RedCode.INVALID_VALUE, "mechanism_id", "outside 192..228")
        action_serial = _text("action_serial", action_serial)
        previous = self.state
        if action_serial in self._actions:
            return ActionOutcome(
                mechanism_id,
                False,
                NoOpCode.DUPLICATE_ACTION.value,
                previous,
                self.state,
            )
        if token != self.token():
            return ActionOutcome(
                mechanism_id,
                False,
                NoOpCode.STALE_TOKEN.value,
                previous,
                self.state,
            )
        frozen_sources = tuple(sources)
        if not frozen_sources:
            raise ModelRed(RedCode.INVALID_VALUE, "sources", "provenance is mandatory")
        if len(frozen_sources) != len(set(frozen_sources)):
            raise ModelRed(RedCode.DUPLICATE_ID, "sources", "duplicate provenance source")

        # All fallible validation and normalization happens here.  A RED from
        # prepare must leave state, resources, actions and provenance untouched.
        prepared = prepare()
        target_state = self.state if next_state is None else _text("next_state", next_state)
        result_ids = tuple(_text("result_id", value) for value in commit(prepared))
        if not result_ids:
            raise ModelRed(RedCode.INVARIANT_BREACH, "result_ids", "commit must identify output")
        if len(result_ids) != len(set(result_ids)):
            raise ModelRed(RedCode.DUPLICATE_ID, "result_ids", "commit output duplicated")
        self.state = target_state
        self._actions.add(action_serial)
        payload = json.dumps(prepared, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        receipt = ProvenanceReceipt(
            len(self.provenance) + 1,
            mechanism_id,
            action_serial,
            self.identity.owner_id,
            previous,
            self.state,
            frozen_sources,
            result_ids,
            hashlib.sha256(payload).hexdigest(),
        )
        self.provenance.append(receipt)
        return ActionOutcome(
            mechanism_id,
            True,
            "applied",
            previous,
            self.state,
            receipt.receipt_serial,
        )


@dataclass
class CapacityLedger:
    opening_hours: int
    allocations: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.opening_hours = _integer("opening_hours", self.opening_hours, minimum=0)

    @property
    def used_hours(self) -> int:
        return sum(self.allocations.values())

    @property
    def available_hours(self) -> int:
        return self.opening_hours - self.used_hours

    def prepare_allocate(self, allocation_id: str, hours: int) -> tuple[str, int]:
        allocation_id = _text("allocation_id", allocation_id)
        hours = _integer("hours", hours, minimum=0)
        if allocation_id in self.allocations:
            raise ModelRed(RedCode.DUPLICATE_ID, "allocation_id", allocation_id)
        if hours > self.available_hours:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "capacity", "insufficient hours")
        return allocation_id, hours

    def commit_allocate(self, prepared: tuple[str, int]) -> None:
        allocation_id, hours = prepared
        self.allocations[allocation_id] = hours
        self.assert_conserved()

    def assert_conserved(self) -> None:
        if self.used_hours < 0 or self.available_hours < 0 or self.used_hours + self.available_hours != self.opening_hours:
            raise ModelRed(RedCode.INVARIANT_BREACH, "capacity", "hours do not conserve")


@dataclass
class MoneyLedger:
    opening_gold: int
    available_gold: int = field(init=False)
    credits: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.opening_gold = _integer("opening_gold", self.opening_gold, minimum=0)
        self.available_gold = self.opening_gold

    @property
    def spent_gold(self) -> int:
        return sum(self.credits.values())

    def prepare_pay(self, recipient_id: str, amount: int) -> tuple[str, int]:
        recipient_id = _text("recipient_id", recipient_id)
        amount = _integer("amount", amount, minimum=0)
        if amount > self.available_gold:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "treasury", "insufficient gold")
        return recipient_id, amount

    def commit_pay(self, prepared: tuple[str, int]) -> None:
        recipient_id, amount = prepared
        self.available_gold -= amount
        self.credits[recipient_id] = self.credits.get(recipient_id, 0) + amount
        self.assert_conserved()

    def assert_conserved(self) -> None:
        if self.opening_gold != self.available_gold + self.spent_gold:
            raise ModelRed(RedCode.INVARIANT_BREACH, "money", "treasury debit != recipient credit")


validate_behavior_registry()


class IncidentState(str, Enum):
    ON_CALL = "on-call"
    ALERTED = "alerted"
    CLASSIFIED = "classified"
    COMMANDED = "commanded"
    TIMELINE_FROZEN = "timeline-frozen"
    REVIEWED = "reviewed"
    ACTIONS_OPEN = "actions-open"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class TimelineNode:
    node_id: str
    minute: int
    author_id: str
    kind: str
    content: str

    def __post_init__(self) -> None:
        _text("node_id", self.node_id)
        _integer("minute", self.minute, minimum=0)
        _text("author_id", self.author_id)
        if self.kind not in {"detected", "escalated", "command", "action", "recovered"}:
            raise ModelRed(RedCode.INVALID_VALUE, "kind", self.kind)
        _text("content", self.content)


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    commander_id: str
    grantor_id: str
    start_minute: int
    end_minute: int
    scopes: frozenset[str]

    def __post_init__(self) -> None:
        _text("grant_id", self.grant_id)
        _text("commander_id", self.commander_id)
        _text("grantor_id", self.grantor_id)
        _integer("start_minute", self.start_minute, minimum=0)
        _integer("end_minute", self.end_minute, minimum=0)
        if self.end_minute <= self.start_minute:
            raise ModelRed(RedCode.INVALID_VALUE, "end_minute", "must be after start")
        if not self.scopes:
            raise ModelRed(RedCode.INVALID_VALUE, "scopes", "at least one authority scope")
        for scope in self.scopes:
            _text("scope", scope)

    def permits(self, minute: int, scope: str) -> bool:
        minute = _integer("minute", minute, minimum=0)
        scope = _text("scope", scope)
        return self.start_minute <= minute <= self.end_minute and scope in self.scopes


@dataclass
class PostmortemAction:
    action_id: str
    owner_id: str
    supporter_ids: tuple[str, ...]
    due_day: int
    acceptor_id: str
    risk_rank: int
    closed: bool = False
    evidence_id: str | None = None
    overdue_assigned: bool = False

    def __post_init__(self) -> None:
        _text("action_id", self.action_id)
        _text("owner_id", self.owner_id)
        self.supporter_ids = _unique("supporter_ids", self.supporter_ids, allow_empty=True)
        _integer("due_day", self.due_day, minimum=1)
        _text("acceptor_id", self.acceptor_id)
        _integer("risk_rank", self.risk_rank, minimum=1)


@dataclass
class ReliabilityBudget:
    opening: int
    remaining: int = field(init=False)
    consumed_by_incident: dict[str, int] = field(default_factory=dict)
    frozen_projects: set[str] = field(default_factory=set)
    override_owner: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.opening = _integer("opening", self.opening, minimum=0)
        self.remaining = self.opening

    def prepare_consume(self, incident_id: str, amount: int) -> tuple[str, int, int]:
        incident_id = _text("incident_id", incident_id)
        amount = _integer("amount", amount, minimum=0)
        if incident_id in self.consumed_by_incident:
            raise ModelRed(RedCode.DUPLICATE_ID, "incident_id", "budget already consumed")
        return incident_id, amount, max(0, self.remaining - amount)

    def commit_consume(self, prepared: tuple[str, int, int]) -> None:
        incident_id, amount, remaining = prepared
        self.consumed_by_incident[incident_id] = amount
        self.remaining = remaining


@dataclass
class IncidentCase(AtomicCase):
    """Domain X executable incident lifecycle, mechanisms 192--204."""

    capacity: CapacityLedger = field(default_factory=lambda: CapacityLedger(100))
    treasury: MoneyLedger = field(default_factory=lambda: MoneyLedger(100))
    reliability: ReliabilityBudget = field(default_factory=lambda: ReliabilityBudget(10))
    rotation: tuple[str, ...] = ()
    on_call_id: str | None = None
    rotation_cursor: int = 0
    swaps: list[tuple[str, str, str]] = field(default_factory=list)
    hero_fatigue: dict[str, int] = field(default_factory=dict)
    compensated_shifts: set[str] = field(default_factory=set)
    time_off_hours: dict[str, int] = field(default_factory=dict)
    target_relief: dict[str, int] = field(default_factory=dict)
    alert_snapshot: dict[str, object] = field(default_factory=dict)
    alert_versions: list[dict[str, object]] = field(default_factory=list)
    reported_severity: int | None = None
    corrected_severity: int | None = None
    severity_integrity: str | None = None
    authority: AuthorityGrant | None = None
    authority_commands: list[tuple[int, str, str]] = field(default_factory=list)
    timeline: tuple[TimelineNode, ...] = ()
    timeline_sha256: str | None = None
    incident_credit: dict[str, int] = field(default_factory=dict)
    role_nodes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    net_firefighting_credits: dict[str, int] = field(default_factory=dict)
    prevention_credit: dict[str, int] = field(default_factory=dict)
    postmortem_actions: dict[str, PostmortemAction] = field(default_factory=dict)
    repeat_liability: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.state != IncidentState.ON_CALL.value:
            raise ModelRed(RedCode.INVALID_VALUE, "state", "incident begins on-call")

    def configure_rotation(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        members: Iterable[str],
        on_call_id: str,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            frozen = _unique("members", members)
            current = _text("on_call_id", on_call_id)
            if current not in frozen:
                raise ModelRed(RedCode.INVALID_VALUE, "on_call_id", "must be in rotation")
            return {"members": frozen, "on_call": current, "cursor": frozen.index(current)}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.rotation = data["members"]  # type: ignore[assignment]
            self.on_call_id = data["on_call"]  # type: ignore[assignment]
            self.rotation_cursor = data["cursor"]  # type: ignore[assignment]
            return (f"rotation:{self.identity.case_serial}",)

        return self.apply(192, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def swap_on_call(
        self,
        *,
        incoming_id: str,
        reason: str,
    ) -> None:
        incoming_id = _text("incoming_id", incoming_id)
        reason = _text("reason", reason)
        if not self.rotation or self.on_call_id is None or incoming_id not in self.rotation:
            raise ModelRed(RedCode.INVALID_VALUE, "incoming_id", "not an eligible rotation member")
        outgoing = self.on_call_id
        self.on_call_id = incoming_id
        self.rotation_cursor = self.rotation.index(incoming_id)
        self.swaps.append((outgoing, incoming_id, reason))

    def record_fixed_hero_cycle(self) -> None:
        if self.on_call_id is None:
            raise ModelRed(RedCode.ILLEGAL_STATE, "on_call_id", "rotation not configured")
        self.hero_fatigue[self.on_call_id] = self.hero_fatigue.get(self.on_call_id, 0) + 1

    def record_alert(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        source_id: str,
        owner_id: str,
        total: int,
        false_alerts: int,
        misses: int,
        version: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            total_value = _integer("total", total, minimum=1)
            false_value = _integer("false_alerts", false_alerts, minimum=0)
            misses_value = _integer("misses", misses, minimum=0)
            if false_value > total_value:
                raise ModelRed(RedCode.INVARIANT_BREACH, "false_alerts", "cannot exceed total")
            return {
                "source_id": _text("source_id", source_id),
                "owner_id": _text("owner_id", owner_id),
                "total": total_value,
                "false": false_value,
                "misses": misses_value,
                "version": _integer("version", version, minimum=1),
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.alert_snapshot = data.copy()
            self.alert_versions.append(data.copy())
            return (f"alert:{data['source_id']}:v{data['version']}",)

        return self.apply(
            195,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.ALERTED.value,
        )

    def classify_severity(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        reported: int,
        loss: int,
        scope: int,
        recovery_hours: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            reported_value = _integer("reported", reported, minimum=1, maximum=4)
            loss_value = _integer("loss", loss, minimum=0, maximum=100)
            scope_value = _integer("scope", scope, minimum=0, maximum=100)
            recovery = _integer("recovery_hours", recovery_hours, minimum=0)
            if loss_value >= 75 or scope_value >= 75 or recovery >= 72:
                corrected = 4
            elif loss_value >= 50 or scope_value >= 50 or recovery >= 24:
                corrected = 3
            elif loss_value >= 20 or scope_value >= 20 or recovery >= 8:
                corrected = 2
            else:
                corrected = 1
            integrity = "underreported" if reported_value < corrected else "overreported" if reported_value > corrected else "matched"
            return {"reported": reported_value, "corrected": corrected, "integrity": integrity}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.reported_severity = data["reported"]  # type: ignore[assignment]
            self.corrected_severity = data["corrected"]  # type: ignore[assignment]
            self.severity_integrity = data["integrity"]  # type: ignore[assignment]
            return (f"severity:{self.identity.case_serial}",)

        return self.apply(
            196,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.CLASSIFIED.value,
        )

    def grant_temporary_authority(
        self,
        token: CaseToken,
        action_serial: str,
        grant: AuthorityGrant,
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> AuthorityGrant:
            if self.authority is not None:
                raise ModelRed(RedCode.DUPLICATE_ID, "authority", "already granted")
            return grant

        def commit(data: AuthorityGrant) -> Sequence[str]:
            self.authority = data
            return (data.grant_id,)

        return self.apply(
            200,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.COMMANDED.value,
        )

    def execute_authority_command(self, *, minute: int, scope: str, command_id: str) -> None:
        command_id = _text("command_id", command_id)
        if self.authority is None or not self.authority.permits(minute, scope):
            raise ModelRed(RedCode.PERMISSION_DENIED, "authority", "outside time/scope")
        if command_id in {row[2] for row in self.authority_commands}:
            raise ModelRed(RedCode.DUPLICATE_ID, "command_id", command_id)
        self.authority_commands.append((minute, scope, command_id))

    def freeze_timeline(
        self,
        token: CaseToken,
        action_serial: str,
        nodes: Sequence[TimelineNode],
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            frozen = tuple(nodes)
            if not frozen:
                raise ModelRed(RedCode.INVALID_VALUE, "nodes", "timeline cannot be empty")
            if len({node.node_id for node in frozen}) != len(frozen):
                raise ModelRed(RedCode.DUPLICATE_ID, "node_id", "timeline node duplicated")
            minutes = [node.minute for node in frozen]
            if minutes != sorted(minutes):
                raise ModelRed(RedCode.INVARIANT_BREACH, "minute", "timeline must be monotonic")
            canonical = [
                (node.node_id, node.minute, node.author_id, node.kind, node.content)
                for node in frozen
            ]
            digest = hashlib.sha256(
                json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            return {"nodes": frozen, "digest": digest}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.timeline = data["nodes"]  # type: ignore[assignment]
            self.timeline_sha256 = data["digest"]  # type: ignore[assignment]
            return (f"timeline:{self.timeline_sha256}",)

        return self.apply(
            201,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.TIMELINE_FROZEN.value,
        )

    def allocate_incident_credit(
        self,
        token: CaseToken,
        action_serial: str,
        shares: Mapping[str, int],
        role_nodes: Mapping[str, Iterable[str]],
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            normalized = _shares("incident_credit", shares)
            timeline_ids = {node.node_id for node in self.timeline}
            normalized_nodes = {
                _text("role_id", actor): _unique("role_nodes", nodes)
                for actor, nodes in role_nodes.items()
            }
            if set(normalized_nodes) != set(normalized):
                raise ModelRed(RedCode.INVARIANT_BREACH, "role_nodes", "each credited actor needs nodes")
            if any(not set(nodes).issubset(timeline_ids) for nodes in normalized_nodes.values()):
                raise ModelRed(RedCode.INVALID_VALUE, "role_nodes", "unknown timeline node")
            return {"shares": normalized, "nodes": normalized_nodes}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.incident_credit = data["shares"]  # type: ignore[assignment]
            self.role_nodes = data["nodes"]  # type: ignore[assignment]
            return (f"credit:{self.identity.case_serial}",)

        return self.apply(197, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def net_firefighting_credit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        actor_id: str,
        gross_credit: int,
        root_penalty: int,
        negligent: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            actor = _text("actor_id", actor_id)
            gross = _integer("gross_credit", gross_credit, minimum=0)
            penalty = _integer("root_penalty", root_penalty, minimum=0)
            negligence = _boolean("negligent", negligent)
            if actor in self.net_firefighting_credits:
                raise ModelRed(RedCode.DUPLICATE_ID, "actor_id", "already netted")
            if not negligence and penalty:
                raise ModelRed(RedCode.INVARIANT_BREACH, "root_penalty", "normal failure cannot be arson")
            return {"actor": actor, "net": gross - penalty}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.net_firefighting_credits[data["actor"]] = data["net"]  # type: ignore[index]
            return (f"net-credit:{data['actor']}",)

        return self.apply(198, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def award_prevention_credit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        hazard_id: str,
        protection_id: str,
        observation_days: int,
        incident_occurred: bool,
        proposed_credit: int,
        cap: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            hazard = _text("hazard_id", hazard_id)
            protection = _text("protection_id", protection_id)
            _integer("observation_days", observation_days, minimum=1)
            happened = _boolean("incident_occurred", incident_occurred)
            proposed = _integer("proposed_credit", proposed_credit, minimum=0)
            cap_value = _integer("cap", cap, minimum=0)
            if hazard in self.prevention_credit:
                raise ModelRed(RedCode.DUPLICATE_ID, "hazard_id", "already observed")
            return {"hazard": hazard, "protection": protection, "credit": 0 if happened else min(proposed, cap_value)}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.prevention_credit[data["hazard"]] = data["credit"]  # type: ignore[index]
            return (f"prevention:{data['hazard']}",)

        return self.apply(199, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def compensate_on_call(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        shift_id: str,
        worker_id: str,
        verified_hours: int,
        gold_hours: int,
        time_off_hours: int,
        gold_per_hour: int,
        annual_hour_cap: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            shift = _text("shift_id", shift_id)
            worker = _text("worker_id", worker_id)
            verified = _integer("verified_hours", verified_hours, minimum=0)
            gold_equiv = _integer("gold_hours", gold_hours, minimum=0)
            leave = _integer("time_off_hours", time_off_hours, minimum=0)
            cap = _integer("annual_hour_cap", annual_hour_cap, minimum=0)
            rate = _integer("gold_per_hour", gold_per_hour, minimum=0)
            if shift in self.compensated_shifts:
                raise ModelRed(RedCode.DUPLICATE_ID, "shift_id", "already compensated")
            if gold_equiv + leave > min(verified, cap):
                raise ModelRed(RedCode.INVARIANT_BREACH, "compensated_hours", "exceeds verified/cap")
            payment = self.treasury.prepare_pay(worker, gold_equiv * rate)
            return {"shift": shift, "worker": worker, "leave": leave, "payment": payment}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.treasury.commit_pay(data["payment"])  # type: ignore[arg-type]
            worker = data["worker"]  # type: ignore[assignment]
            self.time_off_hours[worker] = self.time_off_hours.get(worker, 0) + data["leave"]  # type: ignore[operator]
            self.compensated_shifts.add(data["shift"])  # type: ignore[arg-type]
            return (f"compensation:{data['shift']}",)

        return self.apply(193, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def grant_target_relief(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        worker_id: str,
        incident_hours: int,
        relief_hours: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            worker = _text("worker_id", worker_id)
            incident = _integer("incident_hours", incident_hours, minimum=0)
            relief = _integer("relief_hours", relief_hours, minimum=0)
            if relief > incident:
                raise ModelRed(RedCode.INVARIANT_BREACH, "relief_hours", "exceeds incident work")
            if worker in self.target_relief:
                raise ModelRed(RedCode.DUPLICATE_ID, "worker_id", "relief already recorded")
            return {"worker": worker, "relief": relief}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.target_relief[data["worker"]] = data["relief"]  # type: ignore[index]
            return (f"relief:{data['worker']}",)

        return self.apply(194, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def open_postmortem_actions(
        self,
        token: CaseToken,
        action_serial: str,
        actions: Sequence[PostmortemAction],
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, PostmortemAction]:
            if not actions:
                raise ModelRed(RedCode.INVALID_VALUE, "actions", "at least one action")
            normalized = {action.action_id: action for action in actions}
            if len(normalized) != len(actions):
                raise ModelRed(RedCode.DUPLICATE_ID, "action_id", "duplicated")
            if any(action.owner_id == action.acceptor_id for action in actions):
                raise ModelRed(RedCode.CONFLICT, "acceptor_id", "owner cannot self-accept")
            if set(normalized).intersection(self.postmortem_actions):
                raise ModelRed(RedCode.DUPLICATE_ID, "action_id", "already exists")
            return normalized

        def commit(data: dict[str, PostmortemAction]) -> Sequence[str]:
            self.postmortem_actions.update(data)
            return tuple(f"postmortem:{action_id}" for action_id in sorted(data))

        return self.apply(
            202,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.ACTIONS_OPEN.value,
        )

    def close_postmortem_action(self, action_id: str, evidence_id: str) -> None:
        action_id = _text("action_id", action_id)
        evidence_id = _text("evidence_id", evidence_id)
        try:
            action = self.postmortem_actions[action_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "action_id", "unknown") from exc
        if action.closed:
            raise ModelRed(RedCode.DUPLICATE_ID, "action_id", "already credited")
        action.closed = True
        action.evidence_id = evidence_id

    def assign_repeat_liability(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        repeat_id: str,
        previous_similarity_key: str,
        current_similarity_key: str,
        prior_action_status: str,
        resource_denier_id: str | None,
        line_worker_id: str,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, str]:
            repeat = _text("repeat_id", repeat_id)
            previous = _text("previous_similarity_key", previous_similarity_key)
            current = _text("current_similarity_key", current_similarity_key)
            status = _text("prior_action_status", prior_action_status)
            worker = _text("line_worker_id", line_worker_id)
            if previous != current:
                raise ModelRed(RedCode.INVALID_VALUE, "similarity_key", "new root cause is not a repeat")
            if repeat in self.repeat_liability:
                raise ModelRed(RedCode.DUPLICATE_ID, "repeat_id", "already escalated")
            responsible = _text("resource_denier_id", resource_denier_id) if status == "resource-refused" else self.identity.owner_id
            if status == "resource-refused" and responsible == worker:
                raise ModelRed(RedCode.INVARIANT_BREACH, "responsible", "cannot dump denied-resource liability on line worker")
            return {"repeat": repeat, "responsible": responsible}

        def commit(data: dict[str, str]) -> Sequence[str]:
            self.repeat_liability[data["repeat"]] = data["responsible"]
            return (f"repeat-liability:{data['repeat']}",)

        return self.apply(203, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def consume_reliability_budget(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        incident_id: str,
        amount: int,
        projects_to_freeze: Iterable[str],
        override_signer_id: str | None,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            budget_plan = self.reliability.prepare_consume(incident_id, amount)
            projects = _unique("projects_to_freeze", projects_to_freeze, allow_empty=True)
            if budget_plan[2] == 0 and not projects and override_signer_id is None:
                raise ModelRed(RedCode.INVARIANT_BREACH, "projects", "zero budget must freeze or be signed over")
            signer = None if override_signer_id is None else _text("override_signer_id", override_signer_id)
            return {"budget": budget_plan, "projects": projects, "signer": signer}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.reliability.commit_consume(data["budget"])  # type: ignore[arg-type]
            if data["signer"] is None:
                self.reliability.frozen_projects.update(data["projects"])  # type: ignore[arg-type]
            else:
                for project_id in data["projects"]:  # type: ignore[union-attr]
                    self.reliability.override_owner[project_id] = data["signer"]  # type: ignore[index]
            return (f"reliability:{incident_id}",)

        return self.apply(
            204,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=IncidentState.RESOLVED.value,
        )


class MaintenanceState(str, Enum):
    REGISTERED = "registered"
    OWNED = "owned"
    FUNDED = "funded"
    WORKED = "worked"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class RepairRoute(str, Enum):
    INCREMENTAL = "incremental"
    REWRITE = "rewrite"
    MAINTAIN_TO_RETIRE = "maintain-to-retire"


@dataclass
class DebtItem:
    debt_id: str
    original_owner_id: str
    current_owner_id: str
    created_day: int
    principal: int
    interest: int = 0
    risk: int = 0
    visible: bool = True
    repaid: int = 0

    def __post_init__(self) -> None:
        _text("debt_id", self.debt_id)
        _text("original_owner_id", self.original_owner_id)
        _text("current_owner_id", self.current_owner_id)
        _integer("created_day", self.created_day, minimum=1)
        _integer("principal", self.principal, minimum=0)
        _integer("interest", self.interest, minimum=0)
        _integer("risk", self.risk, minimum=0)
        _integer("repaid", self.repaid, minimum=0)
        if self.repaid > self.principal + self.interest:
            raise ModelRed(RedCode.INVARIANT_BREACH, "repaid", "exceeds debt")

    @property
    def outstanding(self) -> int:
        return self.principal + self.interest - self.repaid


@dataclass(frozen=True)
class RunbookVersion:
    runbook_id: str
    version: int
    author_id: str
    validator_id: str
    task_id: str
    completed: bool
    duration_minutes: int
    errors: int

    def __post_init__(self) -> None:
        _text("runbook_id", self.runbook_id)
        _integer("version", self.version, minimum=1)
        _text("author_id", self.author_id)
        _text("validator_id", self.validator_id)
        _text("task_id", self.task_id)
        _boolean("completed", self.completed)
        _integer("duration_minutes", self.duration_minutes, minimum=0)
        _integer("errors", self.errors, minimum=0)
        if self.author_id == self.validator_id:
            raise ModelRed(RedCode.CONFLICT, "validator_id", "author cannot self-validate")


@dataclass(frozen=True)
class HandoverItem:
    category: str
    item_id: str
    accepted: bool
    waived_reason: str | None = None

    def __post_init__(self) -> None:
        if self.category not in {"assets", "risks", "contacts", "open-items"}:
            raise ModelRed(RedCode.INVALID_VALUE, "category", self.category)
        _text("item_id", self.item_id)
        _boolean("accepted", self.accepted)
        if not self.accepted and self.waived_reason is None:
            raise ModelRed(RedCode.INVALID_VALUE, "waived_reason", "unaccepted item needs explicit waiver")
        if self.waived_reason is not None:
            _text("waived_reason", self.waived_reason)


@dataclass
class MaintenanceCase(AtomicCase):
    """Domain Y executable debt/maintenance lifecycle, mechanisms 205--216."""

    capacity: CapacityLedger = field(default_factory=lambda: CapacityLedger(100))
    treasury: MoneyLedger = field(default_factory=lambda: MoneyLedger(100))
    toil_snapshot: dict[str, object] = field(default_factory=dict)
    debts: dict[str, DebtItem] = field(default_factory=dict)
    debt_budget: dict[str, int] = field(default_factory=dict)
    debt_work_used: int = 0
    repair_route: RepairRoute | None = None
    route_history: list[tuple[int, RepairRoute]] = field(default_factory=list)
    hazard_pay_end_day: dict[str, int] = field(default_factory=dict)
    maintenance_owner_id: str | None = None
    owner_history: list[str] = field(default_factory=list)
    knowledge_concentration: int = 0
    runbooks: dict[tuple[str, int], RunbookVersion] = field(default_factory=dict)
    automation_credit: dict[str, int] = field(default_factory=dict)
    review_records: dict[str, dict[str, int]] = field(default_factory=dict)
    quality_records: dict[str, dict[str, object]] = field(default_factory=dict)
    retired_services: set[str] = field(default_factory=set)
    released_hc: set[str] = field(default_factory=set)
    handovers: dict[str, tuple[HandoverItem, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.state != MaintenanceState.REGISTERED.value:
            raise ModelRed(RedCode.INVALID_VALUE, "state", "maintenance begins registered")

    def freeze_toil(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        total_hours: int,
        toil_hours: int,
        remedy: str | None,
        cap_percent: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            total = _integer("total_hours", total_hours, minimum=1)
            toil = _integer("toil_hours", toil_hours, minimum=0, maximum=total)
            cap = _integer("cap_percent", cap_percent, minimum=0, maximum=100)
            share = toil * 100 / total
            normalized_remedy = None if remedy is None else _text("remedy", remedy)
            if share > cap and normalized_remedy not in {"automate", "stop-intake", "reinforce"}:
                raise ModelRed(RedCode.INVALID_VALUE, "remedy", "over-cap toil needs exactly one remedy")
            return {
                "total": total,
                "toil": toil,
                "delivery": total - toil,
                "share": share,
                "cap": cap,
                "remedy": normalized_remedy,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.toil_snapshot = data.copy()
            return (f"toil:{self.identity.cycle_serial}",)

        return self.apply(205, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def register_debt(
        self,
        token: CaseToken,
        action_serial: str,
        debt: DebtItem,
        *,
        elapsed_cycles: int,
        interest_percent: int,
        hidden: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            if debt.debt_id in self.debts:
                raise ModelRed(RedCode.DUPLICATE_ID, "debt_id", debt.debt_id)
            cycles = _integer("elapsed_cycles", elapsed_cycles, minimum=0)
            rate = _integer("interest_percent", interest_percent, minimum=0, maximum=100)
            hidden_value = _boolean("hidden", hidden)
            interest = debt.principal * rate * cycles // 100
            return {"debt": debt, "interest": interest, "visible": not hidden_value}

        def commit(data: dict[str, object]) -> Sequence[str]:
            item = data["debt"]  # type: ignore[assignment]
            item.interest += data["interest"]  # type: ignore[operator]
            item.visible = data["visible"]  # type: ignore[assignment]
            self.debts[item.debt_id] = item
            return (item.debt_id,)

        return self.apply(
            206,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=MaintenanceState.OWNED.value,
        )

    def freeze_debt_budget(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        debt_hours: int,
        business_hours: int,
        remaining_hours: int,
        approved_diversion_hours: int,
        approver_id: str | None,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            debt = _integer("debt_hours", debt_hours, minimum=0)
            business = _integer("business_hours", business_hours, minimum=0)
            remaining = _integer("remaining_hours", remaining_hours, minimum=0)
            diversion = _integer("approved_diversion_hours", approved_diversion_hours, minimum=0)
            if debt + business + remaining != self.capacity.opening_hours:
                raise ModelRed(RedCode.INVARIANT_BREACH, "hours", "debt+business+remaining != total")
            if diversion > debt:
                raise ModelRed(RedCode.INVARIANT_BREACH, "approved_diversion_hours", "exceeds debt budget")
            approver = None if diversion == 0 else _text("approver_id", approver_id)
            final_debt = debt - diversion
            final_business = business + diversion
            plans = (
                self.capacity.prepare_allocate("debt-budget", final_debt),
                self.capacity.prepare_allocate("business-budget", final_business),
            )
            return {
                "debt": final_debt,
                "business": final_business,
                "remaining": remaining,
                "approver": approver,
                "plans": plans,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            for plan in data["plans"]:  # type: ignore[union-attr]
                self.capacity.commit_allocate(plan)
            self.debt_budget = {
                "debt": data["debt"],  # type: ignore[dict-item]
                "business": data["business"],  # type: ignore[dict-item]
                "remaining": data["remaining"],  # type: ignore[dict-item]
            }
            return (f"debt-budget:{self.identity.cycle_serial}",)

        return self.apply(
            207,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=MaintenanceState.FUNDED.value,
        )

    def repay_debt(self, debt_id: str, *, work_hours: int) -> None:
        """Apply already-frozen debt capacity; debt and work fall by the same amount."""

        debt_id = _text("debt_id", debt_id)
        work = _integer("work_hours", work_hours, minimum=0)
        try:
            debt = self.debts[debt_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "debt_id", "unknown") from exc
        budget = self.debt_budget.get("debt")
        if budget is None:
            raise ModelRed(RedCode.ILLEGAL_STATE, "debt_budget", "must freeze budget first")
        if self.debt_work_used + work > budget:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "debt_budget", "repayment exceeds frozen work")
        if work > debt.outstanding:
            raise ModelRed(RedCode.INVARIANT_BREACH, "work_hours", "cannot repay beyond balance")
        debt.repaid += work
        self.debt_work_used += work

    def choose_repair_route(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        route: RepairRoute,
        route_version: int,
        work_hours: int,
        exit_condition: str,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            selected = RepairRoute(route)
            version = _integer("route_version", route_version, minimum=1)
            hours = _integer("work_hours", work_hours, minimum=0)
            exit_rule = _text("exit_condition", exit_condition)
            if any(existing_version == version for existing_version, _ in self.route_history):
                raise ModelRed(RedCode.DUPLICATE_ID, "route_version", "already exists")
            allocation = self.capacity.prepare_allocate(f"repair-route-v{version}", hours)
            return {"route": selected, "version": version, "exit": exit_rule, "allocation": allocation}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.capacity.commit_allocate(data["allocation"])  # type: ignore[arg-type]
            self.repair_route = data["route"]  # type: ignore[assignment]
            self.route_history.append((data["version"], data["route"]))  # type: ignore[arg-type]
            return (f"repair-route:v{data['version']}",)

        return self.apply(
            208,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=MaintenanceState.WORKED.value,
        )

    def pay_hazard_allowance(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        worker_id: str,
        amount: int,
        cap: int,
        end_day: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            worker = _text("worker_id", worker_id)
            amount_value = _integer("amount", amount, minimum=0)
            cap_value = _integer("cap", cap, minimum=0)
            if amount_value > cap_value:
                raise ModelRed(RedCode.INVARIANT_BREACH, "amount", "exceeds frozen cap")
            if worker in self.hazard_pay_end_day:
                raise ModelRed(RedCode.DUPLICATE_ID, "worker_id", "allowance already active")
            payment = self.treasury.prepare_pay(worker, amount_value)
            return {"worker": worker, "end_day": _integer("end_day", end_day, minimum=1), "payment": payment}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.treasury.commit_pay(data["payment"])  # type: ignore[arg-type]
            self.hazard_pay_end_day[data["worker"]] = data["end_day"]  # type: ignore[index]
            return (f"hazard-pay:{data['worker']}",)

        return self.apply(209, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def rotate_maintenance_owner(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        incoming_owner_id: str,
        handover_complete: bool,
        practical_verified: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> str:
            incoming = _text("incoming_owner_id", incoming_owner_id)
            if not _boolean("handover_complete", handover_complete) or not _boolean("practical_verified", practical_verified):
                raise ModelRed(RedCode.PERMISSION_DENIED, "rotation", "handover and practical test required")
            if incoming == self.maintenance_owner_id:
                raise ModelRed(RedCode.INVALID_VALUE, "incoming_owner_id", "must change owner")
            return incoming

        def commit(incoming: str) -> Sequence[str]:
            if self.maintenance_owner_id is not None:
                self.owner_history.append(self.maintenance_owner_id)
            self.maintenance_owner_id = incoming
            return (f"maintenance-owner:{incoming}",)

        return self.apply(210, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def validate_runbook(
        self,
        token: CaseToken,
        action_serial: str,
        runbook: RunbookVersion,
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> RunbookVersion:
            key = (runbook.runbook_id, runbook.version)
            if key in self.runbooks:
                raise ModelRed(RedCode.DUPLICATE_ID, "runbook", "version already credited")
            if not runbook.completed:
                raise ModelRed(RedCode.PERMISSION_DENIED, "completed", "practical task not completed")
            return runbook

        def commit(data: RunbookVersion) -> Sequence[str]:
            self.runbooks[(data.runbook_id, data.version)] = data
            return (f"runbook:{data.runbook_id}:v{data.version}",)

        return self.apply(211, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def settle_automation_credit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        automation_id: str,
        baseline_hours: int,
        observed_hours: int,
        observation_complete: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            automation = _text("automation_id", automation_id)
            baseline = _integer("baseline_hours", baseline_hours, minimum=0)
            observed = _integer("observed_hours", observed_hours, minimum=0)
            if not _boolean("observation_complete", observation_complete):
                raise ModelRed(RedCode.PERMISSION_DENIED, "observation_complete", "not due")
            if automation in self.automation_credit:
                raise ModelRed(RedCode.DUPLICATE_ID, "automation_id", "already settled")
            return {"automation": automation, "savings": max(0, baseline - observed)}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.automation_credit[data["automation"]] = data["savings"]  # type: ignore[index]
            return (f"automation:{data['automation']}",)

        return self.apply(212, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def record_review_credit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        review_id: str,
        reviewer_id: str,
        review_hours: int,
        blocking_hours: int,
        validated_catches: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            review = _text("review_id", review_id)
            if review in self.review_records:
                raise ModelRed(RedCode.DUPLICATE_ID, "review_id", "already recorded")
            _text("reviewer_id", reviewer_id)
            return {
                "review_hours": _integer("review_hours", review_hours, minimum=0),
                "blocking_hours": _integer("blocking_hours", blocking_hours, minimum=0),
                "quality_credit": _integer("validated_catches", validated_catches, minimum=0),
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.review_records[review_id] = data  # type: ignore[assignment]
            return (f"review:{review_id}",)

        return self.apply(213, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def record_quality_scope(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        scope_id: str,
        coverage_percent: int,
        risk_scenarios: Iterable[str],
        critical_miss: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            scope = _text("scope_id", scope_id)
            coverage = _integer("coverage_percent", coverage_percent, minimum=0, maximum=100)
            scenarios = _unique("risk_scenarios", risk_scenarios)
            miss = _boolean("critical_miss", critical_miss)
            if scope in self.quality_records:
                raise ModelRed(RedCode.DUPLICATE_ID, "scope_id", "already frozen")
            # Coverage contributes at most half; risk selection and misses
            # remain independently visible and can reverse a vanity score.
            score = min(50, coverage // 2) + min(50, len(scenarios) * 10)
            if miss:
                score = max(0, score - 40)
            return {"scope": scope, "coverage": coverage, "risks": scenarios, "critical_miss": miss, "score": score}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.quality_records[data["scope"]] = data  # type: ignore[index]
            return (f"quality:{data['scope']}",)

        return self.apply(214, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def retire_legacy_service(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        service_id: str,
        users: Iterable[str],
        migrated_users: Iterable[str],
        upheld_appeals: Iterable[str],
        hc_slot_id: str,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            service = _text("service_id", service_id)
            all_users = set(_unique("users", users, allow_empty=True))
            migrated = set(_unique("migrated_users", migrated_users, allow_empty=True))
            appeals = set(_unique("upheld_appeals", upheld_appeals, allow_empty=True))
            if service in self.retired_services:
                raise ModelRed(RedCode.DUPLICATE_ID, "service_id", "already retired")
            if not migrated.issubset(all_users) or not appeals.issubset(all_users):
                raise ModelRed(RedCode.INVARIANT_BREACH, "users", "unknown migration/appeal user")
            if appeals - migrated:
                raise ModelRed(RedCode.PERMISSION_DENIED, "upheld_appeals", "approved user remains unmigrated")
            if all_users - migrated:
                raise ModelRed(RedCode.PERMISSION_DENIED, "migrated_users", "users remain")
            slot = _text("hc_slot_id", hc_slot_id)
            if slot in self.released_hc:
                raise ModelRed(RedCode.DUPLICATE_ID, "hc_slot_id", "already released")
            return {"service": service, "slot": slot}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.retired_services.add(data["service"])  # type: ignore[arg-type]
            self.released_hc.add(data["slot"])  # type: ignore[arg-type]
            return (f"retired:{data['service']}", f"released-hc:{data['slot']}")

        return self.apply(215, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def complete_handover(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        handover_id: str,
        items: Sequence[HandoverItem],
        delay_days: int,
        maximum_delay_days: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            handover = _text("handover_id", handover_id)
            if handover in self.handovers:
                raise ModelRed(RedCode.DUPLICATE_ID, "handover_id", "already completed")
            frozen = tuple(items)
            categories = {item.category for item in frozen}
            if categories != {"assets", "risks", "contacts", "open-items"}:
                raise ModelRed(RedCode.INVARIANT_BREACH, "categories", "all four categories required")
            delay = _integer("delay_days", delay_days, minimum=0)
            maximum = _integer("maximum_delay_days", maximum_delay_days, minimum=0)
            if delay > maximum:
                raise ModelRed(RedCode.PERMISSION_DENIED, "delay_days", "manager cannot block indefinitely")
            return {"handover": handover, "items": frozen}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.handovers[data["handover"]] = data["items"]  # type: ignore[index]
            return (f"handover:{data['handover']}",)

        return self.apply(
            216,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=MaintenanceState.CLOSED.value,
        )


class PlatformState(str, Enum):
    PROPOSED = "proposed"
    ADOPTED = "adopted"
    MIGRATING = "migrating"
    DUAL_RUNNING = "dual-running"
    VALUED = "valued"
    SETTLED = "settled"


class AdoptionState(str, Enum):
    NOT_PILOTED = "not-piloted"
    PILOT = "pilot"
    ADOPTED = "adopted"
    APPROVED_EXCEPTION = "approved-exception"


@dataclass(frozen=True)
class AdoptionDecision:
    team_id: str
    state: AdoptionState
    pilot_id: str | None = None
    exception_reason: str | None = None
    migration_loss: int = 0

    def __post_init__(self) -> None:
        _text("team_id", self.team_id)
        AdoptionState(self.state)
        if self.pilot_id is not None:
            _text("pilot_id", self.pilot_id)
        if self.exception_reason is not None:
            _text("exception_reason", self.exception_reason)
        _integer("migration_loss", self.migration_loss, minimum=0)
        if self.state == AdoptionState.ADOPTED and self.pilot_id is None:
            raise ModelRed(RedCode.INVALID_VALUE, "pilot_id", "voluntary adoption requires successful pilot")
        if self.state == AdoptionState.APPROVED_EXCEPTION and self.exception_reason is None:
            raise ModelRed(RedCode.INVALID_VALUE, "exception_reason", "approved exception needs reason")


@dataclass(frozen=True)
class PlatformMetric:
    team_id: str
    depth: int
    saving: int
    saving_confirmed: bool

    def __post_init__(self) -> None:
        _text("team_id", self.team_id)
        _integer("depth", self.depth, minimum=0, maximum=100)
        _integer("saving", self.saving, minimum=0)
        _boolean("saving_confirmed", self.saving_confirmed)
        if self.saving > 0 and not self.saving_confirmed:
            raise ModelRed(RedCode.PERMISSION_DENIED, "saving_confirmed", "user confirmation required")


@dataclass
class DualRunRecord:
    team_id: str
    old_active: bool
    new_active: bool
    exit_day: int
    maintenance_hours: int
    old_closed: bool = False

    def __post_init__(self) -> None:
        _text("team_id", self.team_id)
        _boolean("old_active", self.old_active)
        _boolean("new_active", self.new_active)
        if not (self.old_active and self.new_active):
            raise ModelRed(RedCode.INVALID_VALUE, "dual_run", "both routes must be active")
        _integer("exit_day", self.exit_day, minimum=1)
        _integer("maintenance_hours", self.maintenance_hours, minimum=0)


@dataclass(frozen=True)
class DuplicateScan:
    proposal_id: str
    matched_asset_ids: tuple[str, ...]
    decision: str
    difference_reason: str | None = None
    approved_by: str | None = None

    def __post_init__(self) -> None:
        _text("proposal_id", self.proposal_id)
        object.__setattr__(
            self,
            "matched_asset_ids",
            _unique("matched_asset_ids", self.matched_asset_ids, allow_empty=True),
        )
        if self.decision not in {"reuse", "contribute", "build"}:
            raise ModelRed(RedCode.INVALID_VALUE, "decision", self.decision)
        if self.matched_asset_ids and self.decision == "build":
            if self.difference_reason is None or self.approved_by is None:
                raise ModelRed(RedCode.PERMISSION_DENIED, "build", "difference and approval required")
        if self.difference_reason is not None:
            _text("difference_reason", self.difference_reason)
        if self.approved_by is not None:
            _text("approved_by", self.approved_by)


@dataclass
class InnerSourceSubmission:
    submission_id: str
    contributor_id: str
    maintainer_id: str
    content_id: str
    accepted: bool
    review_reason: str
    settled: bool = False

    def __post_init__(self) -> None:
        for name in ("submission_id", "contributor_id", "maintainer_id", "content_id", "review_reason"):
            _text(name, getattr(self, name))
        _boolean("accepted", self.accepted)


@dataclass
class PlatformCase(AtomicCase):
    """Domain Z executable platform lifecycle, mechanisms 217--228."""

    central_treasury: MoneyLedger = field(default_factory=lambda: MoneyLedger(100))
    team_treasuries: dict[str, MoneyLedger] = field(default_factory=dict)
    platform_capacity: CapacityLedger = field(default_factory=lambda: CapacityLedger(100))
    user_capacity: CapacityLedger = field(default_factory=lambda: CapacityLedger(100))
    reform_capacity: CapacityLedger = field(default_factory=lambda: CapacityLedger(100))
    adoption: dict[str, AdoptionDecision] = field(default_factory=dict)
    customer_score: float | None = None
    foundation_score: float | None = None
    customer_weights: dict[str, int] = field(default_factory=dict)
    dual_score_floors: tuple[float, float] | None = None
    full_high_eligible: bool = False
    metrics: dict[str, PlatformMetric] = field(default_factory=dict)
    outcome_metric: str | None = None
    counter_metric: str | None = None
    charged_cycles: set[int] = field(default_factory=set)
    showback: dict[str, int] = field(default_factory=dict)
    migration_shares: dict[str, int] = field(default_factory=dict)
    migration_hours: dict[str, int] = field(default_factory=dict)
    dual_runs: dict[str, DualRunRecord] = field(default_factory=dict)
    duplicate_scans: dict[str, DuplicateScan] = field(default_factory=dict)
    merger_winner: str | None = None
    merger_loser: str | None = None
    merger_contributions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    forks: dict[str, dict[str, object]] = field(default_factory=dict)
    submissions: dict[str, InnerSourceSubmission] = field(default_factory=dict)
    contributor_credit: dict[str, int] = field(default_factory=dict)
    maintainer_credit: dict[str, int] = field(default_factory=dict)
    role_credit: dict[str, dict[str, int]] = field(default_factory=dict)
    founder_halo: dict[str, int] = field(default_factory=dict)
    blast_liability: dict[str, dict[str, int]] = field(default_factory=dict)
    allocated_losses: dict[str, dict[str, int]] = field(default_factory=dict)
    blast_affected_teams: dict[str, tuple[str, ...]] = field(default_factory=dict)
    degraded_teams: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.state != PlatformState.PROPOSED.value:
            raise ModelRed(RedCode.INVALID_VALUE, "state", "platform begins proposed")

    def decide_adoption(
        self,
        token: CaseToken,
        action_serial: str,
        decisions: Sequence[AdoptionDecision],
        *,
        mandatory_interface_only: bool,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, AdoptionDecision]:
            _boolean("mandatory_interface_only", mandatory_interface_only)
            normalized = {item.team_id: item for item in decisions}
            if not normalized or len(normalized) != len(decisions):
                raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "one adoption state per team")
            if set(normalized).intersection(self.adoption):
                raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "already decided")
            return normalized

        def commit(data: dict[str, AdoptionDecision]) -> Sequence[str]:
            self.adoption.update(data)
            return tuple(f"adoption:{team_id}" for team_id in sorted(data))

        return self.apply(
            217,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=PlatformState.ADOPTED.value,
        )

    def freeze_dual_score(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        customer_scores: Mapping[str, float],
        customer_weights: Mapping[str, int],
        foundation_score: float,
        customer_floor: float,
        foundation_floor: float,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            weights = _shares("customer_weights", customer_weights)
            if set(weights) != set(customer_scores):
                raise ModelRed(RedCode.INVARIANT_BREACH, "customer_scores", "weights/scores mismatch")
            scores = {
                team_id: _number("customer_score", score, minimum=0, maximum=100)
                for team_id, score in customer_scores.items()
            }
            foundation = _number("foundation_score", foundation_score, minimum=0, maximum=100)
            customer = sum(scores[team] * weights[team] for team in scores) / 100
            return {
                "weights": weights,
                "customer": customer,
                "foundation": foundation,
                "customer_floor": _number("customer_floor", customer_floor, minimum=0, maximum=100),
                "foundation_floor": _number("foundation_floor", foundation_floor, minimum=0, maximum=100),
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.customer_weights = data["weights"]  # type: ignore[assignment]
            self.customer_score = data["customer"]  # type: ignore[assignment]
            self.foundation_score = data["foundation"]  # type: ignore[assignment]
            self.dual_score_floors = (
                data["customer_floor"],
                data["foundation_floor"],
            )  # type: ignore[assignment]
            self.full_high_eligible = bool(
                data["customer"] >= data["customer_floor"]  # type: ignore[operator]
                and data["foundation"] >= data["foundation_floor"]  # type: ignore[operator]
            )
            return (f"dual-score:{self.identity.cycle_serial}",)

        return self.apply(218, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def freeze_value_metrics(
        self,
        token: CaseToken,
        action_serial: str,
        metrics: Sequence[PlatformMetric],
        *,
        outcome_metric: str,
        counter_metric: str,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            normalized = {metric.team_id: metric for metric in metrics}
            if not normalized or len(normalized) != len(metrics):
                raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "one metric per adopted team")
            if not set(normalized).issubset(self.adoption):
                raise ModelRed(RedCode.INVALID_VALUE, "team_id", "metric for unknown team")
            return {
                "metrics": normalized,
                "outcome": _text("outcome_metric", outcome_metric),
                "counter": _text("counter_metric", counter_metric),
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.metrics = data["metrics"]  # type: ignore[assignment]
            self.outcome_metric = data["outcome"]  # type: ignore[assignment]
            self.counter_metric = data["counter"]  # type: ignore[assignment]
            return (f"value-metrics:{self.identity.cycle_serial}",)

        return self.apply(219, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def charge_platform_cost(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        total_cost: int,
        central_share: int,
        team_charges: Mapping[str, int],
        cycle_serial: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            total = _integer("total_cost", total_cost, minimum=0)
            central = _integer("central_share", central_share, minimum=0)
            cycle = _integer("cycle_serial", cycle_serial, minimum=1)
            if cycle != self.identity.cycle_serial:
                raise ModelRed(RedCode.INVARIANT_BREACH, "cycle_serial", "case cycle mismatch")
            if cycle in self.charged_cycles:
                raise ModelRed(RedCode.DUPLICATE_ID, "cycle_serial", "already charged")
            charges = {
                _text("team_id", team): _integer("team_charge", amount, minimum=0)
                for team, amount in team_charges.items()
            }
            if central + sum(charges.values()) != total:
                raise ModelRed(RedCode.INVARIANT_BREACH, "cost", "central+teams != total")
            missing = set(charges) - set(self.team_treasuries)
            if missing:
                raise ModelRed(RedCode.INVALID_VALUE, "team_treasuries", f"missing={sorted(missing)}")
            central_payment = self.central_treasury.prepare_pay("platform", central)
            team_payments = {
                team: self.team_treasuries[team].prepare_pay("platform", amount)
                for team, amount in charges.items()
            }
            return {
                "cycle": cycle,
                "total": total,
                "central": central,
                "charges": charges,
                "central_payment": central_payment,
                "team_payments": team_payments,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.central_treasury.commit_pay(data["central_payment"])  # type: ignore[arg-type]
            for team, payment in data["team_payments"].items():  # type: ignore[union-attr]
                self.team_treasuries[team].commit_pay(payment)
            self.charged_cycles.add(data["cycle"])  # type: ignore[arg-type]
            self.showback = {"central": data["central"], **data["charges"]}  # type: ignore[dict-item]
            return (f"platform-cost:{data['cycle']}",)

        return self.apply(220, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def allocate_migration_cost(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        total_hours: int,
        shares: Mapping[str, int],
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            total = _integer("total_hours", total_hours, minimum=0)
            normalized = _shares("migration_shares", shares)
            if set(normalized) != {"platform", "users", "reform"}:
                raise ModelRed(RedCode.INVARIANT_BREACH, "migration_shares", "platform/users/reform required")
            hours = {
                key: total * share // 100
                for key, share in normalized.items()
            }
            hours["reform"] += total - sum(hours.values())
            plans = {
                "platform": self.platform_capacity.prepare_allocate("migration-platform", hours["platform"]),
                "users": self.user_capacity.prepare_allocate("migration-users", hours["users"]),
                "reform": self.reform_capacity.prepare_allocate("migration-reform", hours["reform"]),
            }
            return {"shares": normalized, "hours": hours, "plans": plans, "total": total}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.platform_capacity.commit_allocate(data["plans"]["platform"])  # type: ignore[index]
            self.user_capacity.commit_allocate(data["plans"]["users"])  # type: ignore[index]
            self.reform_capacity.commit_allocate(data["plans"]["reform"])  # type: ignore[index]
            self.migration_shares = data["shares"]  # type: ignore[assignment]
            self.migration_hours = data["hours"]  # type: ignore[assignment]
            return (f"migration-cost:{self.identity.case_serial}",)

        return self.apply(
            221,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=PlatformState.MIGRATING.value,
        )

    def start_dual_run(
        self,
        token: CaseToken,
        action_serial: str,
        records: Sequence[DualRunRecord],
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            normalized = {record.team_id: record for record in records}
            if not normalized or len(normalized) != len(records):
                raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "dual-run team duplicated")
            if set(normalized).intersection(self.dual_runs):
                raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "dual-run already active")
            total_hours = sum(record.maintenance_hours for record in records)
            allocation = self.user_capacity.prepare_allocate("dual-run-maintenance", total_hours)
            return {"records": normalized, "allocation": allocation}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.user_capacity.commit_allocate(data["allocation"])  # type: ignore[arg-type]
            self.dual_runs.update(data["records"])  # type: ignore[arg-type]
            return tuple(f"dual-run:{team}" for team in sorted(data["records"]))  # type: ignore[arg-type]

        return self.apply(
            222,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=PlatformState.DUAL_RUNNING.value,
        )

    def close_old_route(self, team_id: str, *, current_day: int) -> None:
        team_id = _text("team_id", team_id)
        current_day = _integer("current_day", current_day, minimum=1)
        try:
            record = self.dual_runs[team_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "team_id", "not dual-running") from exc
        if record.old_closed:
            raise ModelRed(RedCode.DUPLICATE_ID, "team_id", "old route already closed")
        if current_day < record.exit_day:
            raise ModelRed(RedCode.PERMISSION_DENIED, "current_day", "exit not due")
        record.old_active = False
        record.old_closed = True

    def record_duplicate_scan(
        self,
        token: CaseToken,
        action_serial: str,
        scan: DuplicateScan,
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> DuplicateScan:
            if scan.proposal_id in self.duplicate_scans:
                raise ModelRed(RedCode.DUPLICATE_ID, "proposal_id", "already scanned")
            return scan

        def commit(data: DuplicateScan) -> Sequence[str]:
            self.duplicate_scans[data.proposal_id] = data
            return (f"scan:{data.proposal_id}",)

        return self.apply(223, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def merge_solutions(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        solution_a: str,
        solution_b: str,
        sample_id: str,
        rubric_id: str,
        scores: Mapping[str, int],
        contributions: Mapping[str, Iterable[str]],
        reconstruction_hours: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            a = _text("solution_a", solution_a)
            b = _text("solution_b", solution_b)
            if a == b:
                raise ModelRed(RedCode.INVALID_VALUE, "solutions", "must differ")
            _text("sample_id", sample_id)
            _text("rubric_id", rubric_id)
            if set(scores) != {a, b}:
                raise ModelRed(RedCode.INVARIANT_BREACH, "scores", "both solutions required")
            normalized_scores = {
                key: _integer("score", value, minimum=0, maximum=100)
                for key, value in scores.items()
            }
            if normalized_scores[a] == normalized_scores[b]:
                raise ModelRed(RedCode.CONFLICT, "scores", "one winner required")
            winner = max(normalized_scores, key=normalized_scores.get)  # type: ignore[arg-type]
            loser = b if winner == a else a
            normalized_contributions = {
                key: _unique("contributions", values, allow_empty=True)
                for key, values in contributions.items()
            }
            if set(normalized_contributions) != {a, b}:
                raise ModelRed(RedCode.INVARIANT_BREACH, "contributions", "both histories required")
            allocation = self.platform_capacity.prepare_allocate(
                "solution-merger", _integer("reconstruction_hours", reconstruction_hours, minimum=0)
            )
            return {
                "winner": winner,
                "loser": loser,
                "contributions": normalized_contributions,
                "allocation": allocation,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.platform_capacity.commit_allocate(data["allocation"])  # type: ignore[arg-type]
            self.merger_winner = data["winner"]  # type: ignore[assignment]
            self.merger_loser = data["loser"]  # type: ignore[assignment]
            self.merger_contributions = data["contributions"]  # type: ignore[assignment]
            return (f"merger:{data['winner']}",)

        return self.apply(224, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def create_fork(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        fork_id: str,
        source_platform_id: str,
        upstream_request_id: str | None,
        hard_difference: str | None,
        approved_by: str | None,
        owner_id: str,
        maintenance_hours: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            fork = _text("fork_id", fork_id)
            if fork in self.forks:
                raise ModelRed(RedCode.DUPLICATE_ID, "fork_id", "already exists")
            source = _text("source_platform_id", source_platform_id)
            request = _text("upstream_request_id", upstream_request_id)
            difference = _text("hard_difference", hard_difference)
            approver = _text("approved_by", approved_by)
            owner = _text("owner_id", owner_id)
            allocation = self.user_capacity.prepare_allocate(
                f"fork:{fork}", _integer("maintenance_hours", maintenance_hours, minimum=1)
            )
            return {
                "fork": fork,
                "source": source,
                "request": request,
                "difference": difference,
                "approver": approver,
                "owner": owner,
                "allocation": allocation,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.user_capacity.commit_allocate(data["allocation"])  # type: ignore[arg-type]
            self.forks[data["fork"]] = data  # type: ignore[index]
            return (f"fork:{data['fork']}",)

        return self.apply(225, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def settle_inner_source(
        self,
        token: CaseToken,
        action_serial: str,
        submission: InnerSourceSubmission,
        *,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> InnerSourceSubmission:
            if submission.submission_id in self.submissions or submission.settled:
                raise ModelRed(RedCode.DUPLICATE_ID, "submission_id", "already settled")
            return submission

        def commit(data: InnerSourceSubmission) -> Sequence[str]:
            data.settled = True
            self.submissions[data.submission_id] = data
            if data.accepted:
                self.contributor_credit[data.contributor_id] = self.contributor_credit.get(data.contributor_id, 0) + 1
                self.maintainer_credit[data.maintainer_id] = self.maintainer_credit.get(data.maintainer_id, 0) + 1
            return (f"submission:{data.submission_id}",)

        return self.apply(226, token, action_serial, sources=sources, prepare=prepare, commit=commit)

    def freeze_role_credit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        asset_id: str,
        shares: Mapping[str, int],
        founder_id: str,
        cycle_serial: int,
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            asset = _text("asset_id", asset_id)
            if asset in self.role_credit:
                raise ModelRed(RedCode.DUPLICATE_ID, "asset_id", "already frozen")
            normalized = _shares("role_credit", shares)
            if set(normalized) != {"founder", "contributors", "maintainers"}:
                raise ModelRed(RedCode.INVARIANT_BREACH, "role_credit", "three roles required")
            founder = _text("founder_id", founder_id)
            cycle = _integer("cycle_serial", cycle_serial, minimum=1)
            previous_halo = self.founder_halo.get(founder, 100)
            halo = max(0, previous_halo - max(0, cycle - self.identity.cycle_serial))
            return {"asset": asset, "shares": normalized, "founder": founder, "halo": halo}

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.role_credit[data["asset"]] = data["shares"]  # type: ignore[index]
            self.founder_halo[data["founder"]] = data["halo"]  # type: ignore[index]
            return (f"role-credit:{data['asset']}",)

        return self.apply(
            227,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=PlatformState.VALUED.value,
        )

    def allocate_blast_liability(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        incident_id: str,
        affected_teams: Iterable[str],
        total_loss: int,
        liability_shares: Mapping[str, int],
        degraded_teams: Iterable[str],
        sources: Iterable[SourceRef],
    ) -> ActionOutcome:
        def prepare() -> dict[str, object]:
            incident = _text("incident_id", incident_id)
            if incident in self.blast_liability:
                raise ModelRed(RedCode.DUPLICATE_ID, "incident_id", "already allocated")
            teams = _unique("affected_teams", affected_teams)
            degraded = set(_unique("degraded_teams", degraded_teams, allow_empty=True))
            if not degraded.issubset(teams):
                raise ModelRed(RedCode.INVARIANT_BREACH, "degraded_teams", "must be affected")
            loss = _integer("total_loss", total_loss, minimum=0)
            shares = _shares("liability_shares", liability_shares)
            losses = {party: loss * share // 100 for party, share in shares.items()}
            remainder = loss - sum(losses.values())
            first_party = sorted(losses)[0]
            losses[first_party] += remainder
            return {
                "incident": incident,
                "teams": teams,
                "degraded": tuple(sorted(degraded)),
                "shares": shares,
                "losses": losses,
                "loss": loss,
            }

        def commit(data: dict[str, object]) -> Sequence[str]:
            self.blast_liability[data["incident"]] = data["shares"]  # type: ignore[index]
            self.allocated_losses[data["incident"]] = data["losses"]  # type: ignore[index]
            self.blast_affected_teams[data["incident"]] = data["teams"]  # type: ignore[index]
            self.degraded_teams[data["incident"]] = data["degraded"]  # type: ignore[index]
            return (f"blast-liability:{data['incident']}",)

        return self.apply(
            228,
            token,
            action_serial,
            sources=sources,
            prepare=prepare,
            commit=commit,
            next_state=PlatformState.SETTLED.value,
        )


def validate_model() -> None:
    validate_behavior_registry()


validate_model()
