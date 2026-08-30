#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 model for Zhongguo 361 manager and talent mechanisms.

Exact scope: 032-036, 312-333 and 345-354.  This is a pure-Python semantic
reference model.  It proves typed commands, frozen identities, deterministic
state transitions and conservation rules; it does *not* claim CK3 wiring,
MCP evidence, GUI readiness or live gameplay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import math
import random
from types import MappingProxyType
from typing import Any, Callable, Final, Iterable, Mapping, Sequence, TypeVar


READINESS: Final[str] = "python-l0-only"
CK3_IMPLEMENTED: Final[bool] = False
MCP_EVIDENCE: Final[str] = "none"


MECHANISM_TITLES: Final[dict[int, str]] = {
    32: "manager team performance",
    33: "manager profile reason codes",
    34: "performance potential nine-box",
    35: "distribution mode rule",
    36: "ten-year system report",
    312: "internal role posting",
    313: "standardized manager reference",
    314: "cross-region transfer package",
    315: "transfer trial and bilateral exit",
    316: "transfer pay-band mapping",
    317: "confidential internal application",
    318: "application frequency and slot fee",
    319: "one counteroffer then release",
    320: "exit interview aggregate signal",
    321: "alumni pool and return relationship",
    322: "returnee old record and new evidence",
    323: "learning budget allocation",
    324: "completion application outcome stages",
    325: "certificate and practical test",
    326: "external conference exposure",
    327: "internal teaching attribution",
    328: "professional community contribution",
    329: "cross-team mentor matching",
    330: "declining-business reskilling",
    331: "protected learning time",
    332: "succession disaster-recovery drill",
    333: "high-cost training service commitment",
    345: "annual semiannual quarterly cycle",
    346: "off-cycle material signal",
    347: "manager override budget",
    348: "policy exception expiry",
    349: "audit sampling cost",
    350: "rating inflation benchmark drift",
    351: "regional policy pilot",
    352: "policy-version history mapping",
    353: "performance administration cost",
    354: "fairness metric gaming audit",
}

MECHANISM_DOMAINS: Final[dict[int, str]] = {
    **{mechanism_id: "F" for mechanism_id in range(32, 37)},
    **{mechanism_id: "AH" for mechanism_id in range(312, 323)},
    **{mechanism_id: "AI" for mechanism_id in range(323, 334)},
    **{mechanism_id: "AK" for mechanism_id in range(345, 355)},
}

MECHANISM_OPERATIONS: Final[dict[int, str]] = {
    32: "manager.score_frozen_team",
    33: "manager.explain_profile_decision",
    34: "manager.freeze_nine_box",
    35: "manager.freeze_distribution_mode",
    36: "manager.compile_decade_report",
    312: "market.publish_real_vacancy",
    313: "market.freeze_structured_reference",
    314: "market.offer_relocation_package",
    315: "market.run_bilateral_trial",
    316: "market.freeze_pay_mapping",
    317: "market.project_stage_acl",
    318: "market.consume_application_slot",
    319: "market.counteroffer_then_release",
    320: "market.aggregate_exit_voice",
    321: "market.maintain_alumni_relationship",
    322: "market.open_returnee_case",
    323: "learning.allocate_dual_budget",
    324: "learning.advance_three_stages",
    325: "learning.assess_practical_competence",
    326: "learning.settle_conference_adoption",
    327: "learning.attribute_teaching_impact",
    328: "learning.settle_community_adoption",
    329: "learning.match_cross_team_mentor",
    330: "learning.settle_reskill_route",
    331: "learning.borrow_protected_time",
    332: "learning.run_safe_succession_drill",
    333: "learning.settle_training_commitment",
    345: "policy.freeze_next_cycle_calendar",
    346: "policy.consume_material_offcycle_signal",
    347: "policy.consume_override_point",
    348: "policy.expire_or_renew_exception",
    349: "policy.run_reproducible_audit",
    350: "policy.version_benchmark",
    351: "policy.measure_regional_pilot",
    352: "policy.map_immutable_history",
    353: "policy.charge_admin_capacity",
    354: "policy.recompute_fairness_metrics",
}

EXPECTED_MECHANISM_IDS: Final[frozenset[int]] = frozenset(
    (*range(32, 37), *range(312, 334), *range(345, 355))
)


class RedCode(str, Enum):
    INVALID_TYPE = "invalid-type"
    INVALID_VALUE = "invalid-value"
    DUPLICATE_ID = "duplicate-id"
    PERMISSION_DENIED = "permission-denied"
    ILLEGAL_TRANSITION = "illegal-transition"
    INVARIANT_BREACH = "invariant-breach"
    RESOURCE_EXHAUSTED = "resource-exhausted"
    PRIVACY_BREACH = "privacy-breach"
    CONFLICT = "conflict"
    DEADLINE_NOT_DUE = "deadline-not-due"


class ModelRed(ValueError):
    """Stable typed RED; callers never classify errors by prose."""

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


def _int(
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
    if not math.isfinite(result):
        raise ModelRed(RedCode.INVALID_VALUE, name, "must be finite")
    if minimum is not None and result < minimum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be <= {maximum}")
    return result


def _unique(name: str, values: Iterable[str], *, allow_empty: bool = False) -> tuple[str, ...]:
    result = tuple(_text(name, value) for value in values)
    if not allow_empty and not result:
        raise ModelRed(RedCode.INVALID_VALUE, name, "must not be empty")
    if len(result) != len(set(result)):
        raise ModelRed(RedCode.DUPLICATE_ID, name, "must be unique")
    return result


def _shares_100(name: str, values: Mapping[str, int]) -> dict[str, int]:
    result = {
        _text(f"{name}.key", key): _int(f"{name}.{key}", value, minimum=0, maximum=100)
        for key, value in values.items()
    }
    if not result or sum(result.values()) != 100:
        raise ModelRed(RedCode.INVARIANT_BREACH, name, "shares must sum to 100")
    return result


@dataclass(frozen=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        _text("owner_id", self.owner_id)
        _text("subject_id", self.subject_id)
        _int("cycle_serial", self.cycle_serial, minimum=1)
        _int("case_serial", self.case_serial, minimum=1)


@dataclass(frozen=True)
class CaseToken:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    expected_state: str


@dataclass(frozen=True)
class MutationOutcome:
    mechanism_id: int
    applied: bool
    code: str
    previous_state: str
    current_state: str


PlanT = TypeVar("PlanT")


@dataclass
class GuardedCase:
    """Frozen identity plus atomic precheck/commit and stale/idempotent guards."""

    identity: CaseIdentity
    state: str
    _applied_actions: set[str] = field(default_factory=set, init=False, repr=False)

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
        allowed_states: Iterable[str],
        precheck: Callable[[], PlanT],
        commit: Callable[[PlanT], None],
        *,
        next_state: str | None = None,
    ) -> MutationOutcome:
        if mechanism_id not in EXPECTED_MECHANISM_IDS:
            raise ModelRed(RedCode.INVALID_VALUE, "mechanism_id", "outside owned scope")
        action_serial = _text("action_serial", action_serial)
        previous = self.state
        if action_serial in self._applied_actions:
            return MutationOutcome(
                mechanism_id, False, NoOpCode.DUPLICATE_ACTION.value, previous, self.state
            )
        if token != self.token():
            return MutationOutcome(
                mechanism_id, False, NoOpCode.STALE_TOKEN.value, previous, self.state
            )
        allowed = frozenset(_text("allowed_state", value) for value in allowed_states)
        if self.state not in allowed:
            raise ModelRed(
                RedCode.ILLEGAL_TRANSITION,
                "state",
                f"{self.state} not in {sorted(allowed)}",
            )
        plan = precheck()  # must be read-only; any RED leaves the aggregate untouched
        commit(plan)
        self._applied_actions.add(action_serial)
        if next_state is not None:
            self.state = _text("next_state", next_state)
        return MutationOutcome(mechanism_id, True, "applied", previous, self.state)


class TitleRank(IntEnum):
    BARON = 0
    COUNT = 1
    DUKE = 2
    KING = 3
    EMPEROR = 4


@dataclass(frozen=True)
class Actor:
    actor_id: str
    rank: TitleRank
    landed: bool
    celestial: bool
    is_ai: bool = False

    def __post_init__(self) -> None:
        _text("actor_id", self.actor_id)
        if not isinstance(self.rank, TitleRank):
            raise ModelRed(RedCode.INVALID_TYPE, "rank", "must be TitleRank")
        if not isinstance(self.landed, bool) or not isinstance(self.celestial, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "landed/celestial", "must be bool")
        if not isinstance(self.is_ai, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "is_ai", "must be bool")

    @property
    def eligible_manager(self) -> bool:
        return self.landed and self.celestial and self.rank >= TitleRank.DUKE

    @property
    def assessed_only(self) -> bool:
        return self.rank <= TitleRank.COUNT


def authorize_manager(actor: Actor, *, channel: str) -> None:
    if not actor.eligible_manager:
        raise ModelRed(
            RedCode.PERMISSION_DENIED,
            "actor",
            "only landed celestial dukes or higher may manage",
        )
    channel = _text("channel", channel)
    if actor.is_ai and channel != "background":
        raise ModelRed(
            RedCode.PERMISSION_DENIED,
            "channel",
            "the second AI exception is background-only",
        )
    if not actor.is_ai and channel not in {"visible", "background"}:
        raise ModelRed(RedCode.PERMISSION_DENIED, "channel", "invalid player channel")


def authorize_self_response(actor: Actor, subject_id: str) -> None:
    if actor.actor_id != _text("subject_id", subject_id):
        raise ModelRed(RedCode.PERMISSION_DENIED, "actor", "only the subject may respond")
    if not actor.celestial:
        raise ModelRed(RedCode.PERMISSION_DENIED, "actor", "subject is outside celestial system")


@dataclass(frozen=True)
class GoldChargePlan:
    receipt_id: str
    total: int
    treasury_share: int
    manager_share: int


@dataclass
class DualPayerLedger:
    """Every organizational expense also costs the responsible manager gold."""

    treasury_gold: int
    manager_gold: int
    receipts: dict[str, GoldChargePlan] = field(default_factory=dict)
    refunds: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _int("treasury_gold", self.treasury_gold, minimum=0)
        _int("manager_gold", self.manager_gold, minimum=0)

    def plan_charge(
        self, receipt_id: str, *, total: int, treasury_share: int
    ) -> GoldChargePlan:
        receipt_id = _text("receipt_id", receipt_id)
        total = _int("total", total, minimum=2)
        treasury_share = _int("treasury_share", treasury_share, minimum=1)
        manager_share = total - treasury_share
        if manager_share < 1:
            raise ModelRed(
                RedCode.INVARIANT_BREACH,
                "manager_share",
                "both payers must pay a positive amount",
            )
        if receipt_id in self.receipts:
            raise ModelRed(RedCode.DUPLICATE_ID, "receipt_id", "already charged")
        if self.treasury_gold < treasury_share or self.manager_gold < manager_share:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "gold", "atomic dual-payer precheck failed")
        return GoldChargePlan(receipt_id, total, treasury_share, manager_share)

    def commit_charge(self, plan: GoldChargePlan) -> None:
        if plan.receipt_id in self.receipts:
            raise ModelRed(RedCode.DUPLICATE_ID, "receipt_id", "already charged")
        self.treasury_gold -= plan.treasury_share
        self.manager_gold -= plan.manager_share
        self.receipts[plan.receipt_id] = plan

    def refund_exact(self, receipt_id: str, amount: int) -> tuple[int, int]:
        receipt_id = _text("receipt_id", receipt_id)
        amount = _int("amount", amount, minimum=0)
        if receipt_id not in self.receipts:
            raise ModelRed(RedCode.INVALID_VALUE, "receipt_id", "unknown receipt")
        plan = self.receipts[receipt_id]
        already = self.refunds.get(receipt_id, 0)
        if amount + already > plan.total:
            raise ModelRed(RedCode.INVARIANT_BREACH, "refund", "exceeds original receipt")
        treasury = amount * plan.treasury_share // plan.total
        manager = amount - treasury
        self.treasury_gold += treasury
        self.manager_gold += manager
        self.refunds[receipt_id] = already + amount
        return treasury, manager


@dataclass
class PolicyDebtBook:
    records: dict[tuple[int, str, int], int] = field(default_factory=dict)
    actions: set[str] = field(default_factory=set)

    def defer(
        self,
        mechanism_id: int,
        manager: Actor,
        subject_id: str,
        cycle_serial: int,
        action_serial: str,
        *,
        channel: str,
    ) -> MutationOutcome:
        if mechanism_id not in EXPECTED_MECHANISM_IDS:
            raise ModelRed(RedCode.INVALID_VALUE, "mechanism_id", "outside owned scope")
        authorize_manager(manager, channel=channel)
        _text("subject_id", subject_id)
        cycle_serial = _int("cycle_serial", cycle_serial, minimum=1)
        action_serial = _text("action_serial", action_serial)
        if action_serial in self.actions:
            return MutationOutcome(mechanism_id, False, NoOpCode.DUPLICATE_ACTION.value, "none", "none")
        key = (mechanism_id, manager.actor_id, cycle_serial)
        if key in self.records:
            return MutationOutcome(mechanism_id, False, NoOpCode.DUPLICATE_ACTION.value, "none", "none")
        self.records[key] = cycle_serial + 1
        self.actions.add(action_serial)
        return MutationOutcome(mechanism_id, True, "policy-debt", "none", "none")


@dataclass
class JingchaRefusal:
    manager_id: str
    superior_id: str
    mandate_year: int
    superior_opinion_delta: int = -25
    next_review_kpi_delta: int = -50
    consumed: bool = False


@dataclass
class JingchaMandate:
    manager_id: str
    superior_id: str
    mandate_year: int
    resolved: bool = False
    held: bool = False

    def resolve(self, manager: Actor, *, hold: bool) -> JingchaRefusal | None:
        authorize_manager(manager, channel="background" if manager.is_ai else "visible")
        if manager.actor_id != self.manager_id:
            raise ModelRed(RedCode.PERMISSION_DENIED, "manager", "mandate belongs to another manager")
        if self.resolved:
            raise ModelRed(RedCode.DUPLICATE_ID, "mandate", "already resolved")
        if not isinstance(hold, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "hold", "must be bool")
        if manager.is_ai and not hold:
            raise ModelRed(
                RedCode.PERMISSION_DENIED,
                "hold",
                "eligible AI silently holds the mandatory free Jingcha",
            )
        self.resolved = True
        self.held = bool(hold)
        if hold:
            return None  # Jingcha itself is free: no ledger transaction exists.
        return JingchaRefusal(self.manager_id, self.superior_id, self.mandate_year)


TEAM_METRICS: Final[tuple[str, ...]] = (
    "targets",
    "jingcha",
    "calibration",
    "pip_success",
    "appeal_overturn",
    "retention",
    "hc_efficiency",
)


@dataclass(frozen=True)
class FrozenTeamSnapshot:
    manager_id: str
    superior_id: str
    source_team_serial: int
    current_review_serial: int
    mandate_year: int
    metrics: Mapping[str, int]
    grandchild_subject_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("manager_id", self.manager_id)
        _text("superior_id", self.superior_id)
        _int("source_team_serial", self.source_team_serial, minimum=1)
        _int("current_review_serial", self.current_review_serial, minimum=1)
        _int("mandate_year", self.mandate_year, minimum=1)
        if set(self.metrics) != set(TEAM_METRICS):
            raise ModelRed(RedCode.INVARIANT_BREACH, "metrics", "must contain exactly seven team metrics")
        for key, value in self.metrics.items():
            _int(f"metrics.{key}", value, minimum=-100, maximum=100)
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        _unique("grandchild_subject_ids", self.grandchild_subject_ids, allow_empty=True)


class DistributionMode(str, Enum):
    STRICT = "strict"
    RELAXED = "relaxed"
    OFF = "off"
    MIXED = "mixed"


@dataclass(frozen=True)
class DistributionResult:
    mode: DistributionMode
    cohort_size: int
    top_slots: int
    middle_slots: int
    bottom_slots: int
    bottom_consequence: str
    frozen_review_serial: int


PROFILE_WEIGHTS: Final[dict[str, dict[str, int]]] = {
    "data": {"calibration": 3, "appeal": 1, "pip": 1, "bonus": 1, "hc": 2},
    "protector": {"calibration": 1, "appeal": 3, "pip": -1, "bonus": 2, "hc": 1},
    "political": {"calibration": 2, "appeal": -1, "pip": 1, "bonus": 3, "hc": 2},
    "benevolent": {"calibration": 1, "appeal": 2, "pip": 2, "bonus": 1, "hc": 1},
    "cruel": {"calibration": 2, "appeal": -2, "pip": 3, "bonus": -1, "hc": 1},
}


@dataclass(frozen=True)
class AnnualSystemLog:
    owner_id: str
    year: int
    grade_top: int
    grade_middle: int
    grade_bottom: int
    appeal_overturns: int
    pip_successes: int
    promotions: int
    exits: int
    bonus_in: int
    bonus_out: int
    hc_efficiency: int
    talent_outflow: int = 0
    governance_score: int = 0
    manager_reputation: int = 0

    def __post_init__(self) -> None:
        _text("owner_id", self.owner_id)
        _int("year", self.year, minimum=1)
        for name, value in self.__dict__.items():
            if name not in {"owner_id", "year"}:
                _int(name, value, minimum=0)


@dataclass
class ManagerReviewCase(GuardedCase):
    manager: Actor = field(default_factory=lambda: Actor("manager", TitleRank.DUKE, True, True))
    superior: Actor = field(default_factory=lambda: Actor("superior", TitleRank.KING, True, True))
    distribution: DistributionResult | None = None
    team_breakdown: dict[str, int] = field(default_factory=dict)
    score: int | None = None
    reason_codes: tuple[tuple[str, int], ...] = ()
    appeal_risk: int = 0
    nine_box: dict[str, str | int] | None = None
    report: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        authorize_manager(self.superior, channel="background" if self.superior.is_ai else "visible")
        if not self.manager.eligible_manager:
            raise ModelRed(RedCode.PERMISSION_DENIED, "manager", "manager review subject must be a manager")
        if self.identity.owner_id != self.superior.actor_id or self.identity.subject_id != self.manager.actor_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "identity", "superior must assess the manager")

    def freeze_distribution(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        mode: DistributionMode,
        scores: Sequence[int],
        absolute_threshold: int,
    ) -> MutationOutcome:
        def precheck() -> DistributionResult:
            if not isinstance(mode, DistributionMode):
                raise ModelRed(RedCode.INVALID_TYPE, "mode", "must be DistributionMode")
            values = tuple(_int("score", score) for score in scores)
            if not values:
                raise ModelRed(RedCode.INVALID_VALUE, "scores", "empty cohort")
            threshold = _int("absolute_threshold", absolute_threshold)
            n = len(values)
            if mode is DistributionMode.OFF:
                bottom = 0
            elif mode is DistributionMode.RELAXED:
                bottom = math.floor(n * 0.05)
                if n >= 5:
                    bottom = max(1, bottom)
            else:
                bottom = math.floor(n * 0.10)
                if n >= 5:
                    bottom = max(1, bottom)
            top = math.floor(n * 0.30)
            middle = n - top - bottom
            consequence = (
                "lightened"
                if mode is DistributionMode.MIXED and all(value >= threshold for value in values)
                else "full"
            )
            return DistributionResult(
                mode, n, top, middle, bottom, consequence, self.identity.cycle_serial
            )

        return self.apply(
            35,
            token,
            action_serial,
            {"SNAPSHOT_READY"},
            precheck,
            lambda plan: setattr(self, "distribution", plan),
        )

    def score_frozen_team(
        self,
        token: CaseToken,
        action_serial: str,
        snapshot: FrozenTeamSnapshot,
        *,
        refusal: JingchaRefusal | None = None,
        route: str = "evidence",
    ) -> MutationOutcome:
        def precheck() -> tuple[dict[str, int], int, bool]:
            if snapshot.manager_id != self.manager.actor_id or snapshot.superior_id != self.superior.actor_id:
                raise ModelRed(RedCode.INVARIANT_BREACH, "snapshot", "owner/subject mismatch")
            if snapshot.source_team_serial >= snapshot.current_review_serial:
                raise ModelRed(RedCode.INVARIANT_BREACH, "source_team_serial", "same-cycle recursion")
            if snapshot.current_review_serial != self.identity.cycle_serial:
                raise ModelRed(RedCode.INVARIANT_BREACH, "current_review_serial", "wrong cycle")
            if snapshot.grandchild_subject_ids:
                raise ModelRed(
                    RedCode.INVARIANT_BREACH,
                    "grandchild_subject_ids",
                    "only aggregate team facts may reach the superior list",
                )
            route_value = _text("route", route)
            breakdown = dict(snapshot.metrics)
            if route_value == "expedient":
                allowed = {"targets", "jingcha", "retention"}
                breakdown = {key: value for key, value in breakdown.items() if key in allowed}
            elif route_value != "evidence":
                raise ModelRed(RedCode.INVALID_VALUE, "route", "unknown route")
            consume = False
            if refusal is not None:
                if (
                    refusal.manager_id == self.manager.actor_id
                    and refusal.superior_id == self.superior.actor_id
                    and refusal.mandate_year == snapshot.mandate_year
                    and not refusal.consumed
                ):
                    breakdown["jingcha_refusal"] = refusal.next_review_kpi_delta
                    consume = True
            return breakdown, sum(breakdown.values()), consume

        def commit(plan: tuple[dict[str, int], int, bool]) -> None:
            breakdown, score, consume = plan
            self.team_breakdown = breakdown
            self.score = score
            if consume and refusal is not None:
                refusal.consumed = True

        return self.apply(
            32,
            token,
            action_serial,
            {"SNAPSHOT_READY"},
            precheck,
            commit,
            next_state="MANAGER_SCORED",
        )

    def explain_profile(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        profile: str,
        evidence: Mapping[str, int],
        evidence_cap: int,
        relationship_override: int = 0,
    ) -> MutationOutcome:
        def precheck() -> tuple[tuple[tuple[str, int], ...], int]:
            profile_value = _text("profile", profile)
            if profile_value not in PROFILE_WEIGHTS:
                raise ModelRed(RedCode.INVALID_VALUE, "profile", "unknown profile")
            cap = _int("evidence_cap", evidence_cap, minimum=0)
            if set(evidence) != set(PROFILE_WEIGHTS[profile_value]):
                raise ModelRed(RedCode.INVARIANT_BREACH, "evidence", "five domains required")
            codes: list[tuple[str, int]] = []
            for key in sorted(evidence):
                fact = _int(f"evidence.{key}", evidence[key], minimum=-100, maximum=100)
                weighted = fact * PROFILE_WEIGHTS[profile_value][key]
                bounded = max(-cap, min(cap, weighted))
                codes.append((f"{profile_value}:{key}", bounded))
            override = _int("relationship_override", relationship_override, minimum=-cap, maximum=cap)
            if override:
                codes.append(("relationship_override_once", override))
            return tuple(codes), abs(override)

        def commit(plan: tuple[tuple[tuple[str, int], ...], int]) -> None:
            self.reason_codes, override_risk = plan
            self.appeal_risk += override_risk

        return self.apply(
            33,
            token,
            action_serial,
            {"MANAGER_SCORED"},
            precheck,
            commit,
            next_state="REASON_CODED",
        )

    def freeze_nine_box(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        performance_history: Sequence[int],
        growth: int,
        fit: int,
        potential: int,
    ) -> MutationOutcome:
        def precheck() -> dict[str, str | int]:
            history = tuple(_int("performance_history", value, minimum=0, maximum=100) for value in performance_history)
            if len(history) < 2:
                raise ModelRed(RedCode.INVALID_VALUE, "performance_history", "two frozen cycles required")
            p_axis = 1 if sum(history) / len(history) < 40 else 3 if sum(history) / len(history) >= 75 else 2
            potential_axis = round(
                (
                    _int("growth", growth, minimum=0, maximum=100)
                    + _int("fit", fit, minimum=0, maximum=100)
                    + _int("potential", potential, minimum=0, maximum=100)
                )
                / 3
            )
            q_axis = 1 if potential_axis < 40 else 3 if potential_axis >= 75 else 2
            labels = {
                (3, 3): "star",
                (1, 3): "high-potential-newcomer",
                (2, 2): "steady-contributor",
                (1, 2): "misfit-talent",
            }
            return {
                "performance_axis": p_axis,
                "potential_axis": q_axis,
                "label": labels.get((p_axis, q_axis), f"box-{p_axis}-{q_axis}"),
                "history_serials": len(history),
            }

        return self.apply(
            34,
            token,
            action_serial,
            {"REASON_CODED"},
            precheck,
            lambda plan: setattr(self, "nine_box", plan),
            next_state="NINE_BOXED",
        )

    def compile_decade_report(
        self,
        token: CaseToken,
        action_serial: str,
        logs: Sequence[AnnualSystemLog],
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            frozen = tuple(logs)
            if len(frozen) != 10:
                raise ModelRed(RedCode.INVALID_VALUE, "logs", "exactly ten annual logs required")
            if any(log.owner_id != self.superior.actor_id for log in frozen):
                raise ModelRed(RedCode.INVARIANT_BREACH, "owner", "owner segments may not mix")
            years = sorted(log.year for log in frozen)
            if len(set(years)) != 10 or years != list(range(years[0], years[0] + 10)):
                raise ModelRed(RedCode.INVARIANT_BREACH, "year", "ten unique consecutive years required")
            totals: dict[str, int] = {}
            for field_name in (
                "grade_top",
                "grade_middle",
                "grade_bottom",
                "appeal_overturns",
                "pip_successes",
                "promotions",
                "exits",
                "hc_efficiency",
                "talent_outflow",
                "governance_score",
                "manager_reputation",
            ):
                totals[field_name] = sum(getattr(log, field_name) for log in frozen)
            totals["bonus_net"] = sum(log.bonus_in - log.bonus_out for log in frozen)
            return {"owner_id": self.superior.actor_id, "years": tuple(years), "totals": totals}

        return self.apply(
            36,
            token,
            action_serial,
            {"NINE_BOXED"},
            precheck,
            lambda plan: setattr(self, "report", plan),
            next_state="REPORTED",
        )


class PostingScope(str, Enum):
    ALL_ELIGIBLE = "all-eligible"
    MANAGER_CIRCLE = "manager-circle"
    INTERNAL_THEN_EXTERNAL = "internal-then-external"


@dataclass(frozen=True)
class VacancyPosting:
    vacancy_id: str
    legal_hc_id: str | None
    reporting_manager_id: str
    pay_band: str
    goal_summary: str
    close_day: int
    scope: PostingScope
    eligible_ids: tuple[str, ...]
    manager_circle_ids: tuple[str, ...]
    internal_only_until_day: int | None = None

    def __post_init__(self) -> None:
        _text("vacancy_id", self.vacancy_id)
        if self.legal_hc_id is not None:
            _text("legal_hc_id", self.legal_hc_id)
        _text("reporting_manager_id", self.reporting_manager_id)
        _text("pay_band", self.pay_band)
        _text("goal_summary", self.goal_summary)
        _int("close_day", self.close_day, minimum=1)
        if not isinstance(self.scope, PostingScope):
            raise ModelRed(RedCode.INVALID_TYPE, "scope", "must be PostingScope")
        _unique("eligible_ids", self.eligible_ids)
        _unique("manager_circle_ids", self.manager_circle_ids, allow_empty=True)
        if self.scope is PostingScope.INTERNAL_THEN_EXTERNAL:
            if self.internal_only_until_day is None:
                raise ModelRed(RedCode.INVALID_VALUE, "internal_only_until_day", "required")
            _int("internal_only_until_day", self.internal_only_until_day, minimum=1)
            if self.internal_only_until_day >= self.close_day:
                raise ModelRed(RedCode.INVALID_VALUE, "internal_only_until_day", "must precede close")

    def visible_to(self, viewer_id: str, day: int) -> bool:
        viewer_id = _text("viewer_id", viewer_id)
        _int("day", day, minimum=1)
        if self.scope is PostingScope.MANAGER_CIRCLE:
            return viewer_id in self.manager_circle_ids
        return viewer_id in self.eligible_ids


@dataclass(frozen=True)
class ReferenceLetter:
    letter_id: str
    source_manager_id: str
    achievements: tuple[str, ...]
    risks: tuple[str, ...]
    active_pip_ref: str | None
    handover_status: str
    omitted_material_facts: tuple[str, ...] = ()
    retaliatory: bool = False
    private_contact: bool = False

    def __post_init__(self) -> None:
        _text("letter_id", self.letter_id)
        _text("source_manager_id", self.source_manager_id)
        _unique("achievements", self.achievements, allow_empty=True)
        _unique("risks", self.risks, allow_empty=True)
        if self.active_pip_ref is not None:
            _text("active_pip_ref", self.active_pip_ref)
        _text("handover_status", self.handover_status)
        _unique("omitted_material_facts", self.omitted_material_facts, allow_empty=True)


@dataclass(frozen=True)
class TrialTerms:
    start_day: int
    end_day: int
    source_credit_share: int
    target_credit_share: int
    employee_exit: str
    source_manager_exit: str
    target_manager_exit: str

    def __post_init__(self) -> None:
        _int("start_day", self.start_day, minimum=1)
        _int("end_day", self.end_day, minimum=self.start_day + 1)
        _int("source_credit_share", self.source_credit_share, minimum=0, maximum=100)
        _int("target_credit_share", self.target_credit_share, minimum=0, maximum=100)
        if self.source_credit_share + self.target_credit_share != 100:
            raise ModelRed(RedCode.INVARIANT_BREACH, "credit_shares", "must sum to 100")
        _text("employee_exit", self.employee_exit)
        _text("source_manager_exit", self.source_manager_exit)
        _text("target_manager_exit", self.target_manager_exit)


@dataclass(frozen=True)
class PayMapping:
    source_band: str
    target_band: str
    professional_base: int
    source_allowance: int
    target_allowance: int
    method: str
    effective_day: int
    schedule: tuple[int, ...]

    def __post_init__(self) -> None:
        _text("source_band", self.source_band)
        _text("target_band", self.target_band)
        _int("professional_base", self.professional_base, minimum=0)
        _int("source_allowance", self.source_allowance, minimum=0)
        _int("target_allowance", self.target_allowance, minimum=0)
        if self.method not in {"protect", "step", "immediate"}:
            raise ModelRed(RedCode.INVALID_VALUE, "method", "unknown pay mapping")
        _int("effective_day", self.effective_day, minimum=1)
        tuple(_int("schedule", value, minimum=0) for value in self.schedule)
        if self.method == "step" and not self.schedule:
            raise ModelRed(RedCode.INVALID_VALUE, "schedule", "step mapping needs schedule")


@dataclass
class InternalMarketCase(GuardedCase):
    owner: Actor = field(default_factory=lambda: Actor("manager", TitleRank.DUKE, True, True))
    subject: Actor = field(default_factory=lambda: Actor("official", TitleRank.COUNT, True, True))
    posting: VacancyPosting | None = None
    market_trust_delta: int = 0
    reference: ReferenceLetter | None = None
    manager_consequences: list[str] = field(default_factory=list)
    relocation_receipt: str | None = None
    relocation_response: str | None = None
    relocation_package: dict[str, Any] | None = None
    performance_delta: int = 0
    trial: TrialTerms | None = None
    trial_result: str | None = None
    pay_mapping: PayMapping | None = None
    historical_payments: tuple[int, ...] = ()
    disclosure_log: list[tuple[str, str]] = field(default_factory=list)
    retaliation_audit: bool = False
    counteroffer_count: int = 0
    release_deadline: int | None = None
    released_day: int | None = None
    counteroffer_terms: tuple[str, ...] = ()
    commitment_due_day: int | None = None
    commitment_settled: bool = False
    manager_talent_delta: int = 0
    application_quota: ApplicationQuota | None = None
    exit_interview_book: ExitInterviewBook | None = None
    alumni_network: AlumniNetwork | None = None
    returnee_registry: ReturneeRegistry | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        authorize_manager(self.owner, channel="background" if self.owner.is_ai else "visible")
        if self.identity.owner_id != self.owner.actor_id or self.identity.subject_id != self.subject.actor_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "identity", "market owner/subject mismatch")
        if not self.subject.celestial:
            raise ModelRed(RedCode.PERMISSION_DENIED, "subject", "not reviewable")

    def publish_role(
        self, token: CaseToken, action_serial: str, posting: VacancyPosting
    ) -> MutationOutcome:
        def precheck() -> tuple[VacancyPosting, int]:
            if posting.reporting_manager_id != self.owner.actor_id:
                raise ModelRed(RedCode.INVARIANT_BREACH, "reporting_manager_id", "wrong owner")
            trust = -2 if posting.legal_hc_id is None else 0
            return posting, trust

        def commit(plan: tuple[VacancyPosting, int]) -> None:
            self.posting, trust = plan
            self.market_trust_delta += trust

        return self.apply(312, token, action_serial, {"POSTED"}, precheck, commit, next_state="APPLIED")

    def hire_once(self, character_id: str) -> None:
        _text("character_id", character_id)
        if self.posting is None or self.posting.legal_hc_id is None:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "legal_hc_id", "formal hire needs legal HC")
        if hasattr(self, "_hire_result"):
            raise ModelRed(RedCode.DUPLICATE_ID, "hire", "vacancy already filled")
        self._hire_result = character_id

    def freeze_reference(
        self, token: CaseToken, action_serial: str, letter: ReferenceLetter
    ) -> MutationOutcome:
        def precheck() -> tuple[ReferenceLetter, tuple[str, ...]]:
            if letter.source_manager_id != self.owner.actor_id:
                raise ModelRed(RedCode.PERMISSION_DENIED, "source_manager_id", "wrong source manager")
            consequences: list[str] = []
            if letter.omitted_material_facts:
                consequences.append("performance-whitewash-audit")
            if letter.retaliatory or letter.private_contact:
                consequences.append("anti-retaliation-audit")
            return letter, tuple(consequences)

        def commit(plan: tuple[ReferenceLetter, tuple[str, ...]]) -> None:
            self.reference = plan[0]
            self.manager_consequences.extend(plan[1])

        return self.apply(313, token, action_serial, {"POSTED"}, precheck, commit, next_state="APPLIED")

    def offer_relocation(
        self,
        token: CaseToken,
        action_serial: str,
        subject_actor: Actor,
        ledger: DualPayerLedger,
        *,
        accept: bool,
        total_cost: int,
        treasury_share: int,
        receipt_id: str,
        distance_class: str = "cross-region",
        lump_sum_gold: int = 0,
        temporary_allowance_gold: int = 0,
        allowance_end_day: int | None = None,
        family_support_gold: int = 0,
    ) -> MutationOutcome:
        def precheck() -> tuple[GoldChargePlan | None, dict[str, Any]]:
            authorize_self_response(subject_actor, self.subject.actor_id)
            if self.relocation_response is not None:
                raise ModelRed(RedCode.DUPLICATE_ID, "response", "already answered")
            if not isinstance(accept, bool):
                raise ModelRed(RedCode.INVALID_TYPE, "accept", "must be bool")
            distance = _text("distance_class", distance_class)
            lump = _int("lump_sum_gold", lump_sum_gold, minimum=0)
            allowance = _int("temporary_allowance_gold", temporary_allowance_gold, minimum=0)
            family = _int("family_support_gold", family_support_gold, minimum=0)
            if lump + allowance + family != total_cost:
                raise ModelRed(
                    RedCode.INVARIANT_BREACH,
                    "relocation_breakdown",
                    "lump sum + allowance + family support must equal total",
                )
            if allowance:
                if allowance_end_day is None:
                    raise ModelRed(RedCode.INVALID_VALUE, "allowance_end_day", "allowance needs expiry")
                _int("allowance_end_day", allowance_end_day, minimum=1)
            charge = (
                ledger.plan_charge(receipt_id, total=total_cost, treasury_share=treasury_share)
                if accept
                else None
            )
            return charge, {
                "distance_class": distance,
                "lump_sum_gold": lump,
                "temporary_allowance_gold": allowance,
                "allowance_end_day": allowance_end_day,
                "family_support_gold": family,
            }

        def commit(plan: tuple[GoldChargePlan | None, dict[str, Any]]) -> None:
            charge, package = plan
            self.relocation_response = "accepted" if accept else "declined"
            self.relocation_package = package
            if charge is not None:
                ledger.commit_charge(charge)
                self.relocation_receipt = charge.receipt_id

        return self.apply(314, token, action_serial, {"APPLIED"}, precheck, commit, next_state="TRIALED")

    def begin_trial(
        self, token: CaseToken, action_serial: str, terms: TrialTerms
    ) -> MutationOutcome:
        return self.apply(
            315,
            token,
            action_serial,
            {"APPLIED"},
            lambda: terms,
            lambda plan: setattr(self, "trial", plan),
            next_state="TRIALED",
        )

    def finish_trial(self, *, success: bool, reason: str) -> None:
        if self.trial is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "trial", "not started")
        if self.trial_result is not None:
            raise ModelRed(RedCode.DUPLICATE_ID, "trial_result", "already final")
        if not isinstance(success, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "success", "must be bool")
        self.trial_result = "moved" if success else f"returned:{_text('reason', reason)}"
        # A failed transfer trial is development evidence, never an automatic 3.25.

    def freeze_pay_mapping(
        self, token: CaseToken, action_serial: str, mapping: PayMapping
    ) -> MutationOutcome:
        history_before = self.historical_payments

        def commit(plan: PayMapping) -> None:
            self.pay_mapping = plan
            if self.historical_payments != history_before:
                raise ModelRed(RedCode.INVARIANT_BREACH, "historical_payments", "retroactive mutation")

        return self.apply(316, token, action_serial, {"TRIALED"}, lambda: mapping, commit, next_state="RELEASE_DECIDED")

    def project_application_acl(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        stage: str,
        viewers: Sequence[str],
        leaked_to_source: bool = False,
        rating_changed_without_new_evidence: bool = False,
    ) -> MutationOutcome:
        def precheck() -> tuple[str, tuple[str, ...], bool]:
            stage_value = _text("stage", stage)
            if stage_value not in {"screen", "final", "hired"}:
                raise ModelRed(RedCode.INVALID_VALUE, "stage", "unknown stage")
            viewer_ids = _unique("viewers", viewers)
            allowed = {self.subject.actor_id}
            if stage_value in {"final", "hired"}:
                allowed.add(self.owner.actor_id)
            if not leaked_to_source and not set(viewer_ids).issubset(allowed):
                raise ModelRed(RedCode.PRIVACY_BREACH, "viewers", "stage ACL violation")
            retaliation = leaked_to_source and rating_changed_without_new_evidence
            return stage_value, viewer_ids, retaliation

        def commit(plan: tuple[str, tuple[str, ...], bool]) -> None:
            stage_value, viewers_value, retaliation = plan
            self.disclosure_log.extend((stage_value, viewer) for viewer in viewers_value)
            self.retaliation_audit = self.retaliation_audit or retaliation

        return self.apply(317, token, action_serial, {"TRIALED"}, precheck, commit, next_state="RELEASE_DECIDED")

    def consume_application_slot(
        self,
        token: CaseToken,
        action_serial: str,
        quota: ApplicationQuota,
        *,
        application_id: str,
        exploratory: bool = False,
        withdraw: bool = False,
        manager_timeout: bool = False,
    ) -> MutationOutcome:
        def precheck() -> ApplicationQuota:
            clone = ApplicationQuota(
                quota.formal_limit,
                quota.used,
                quota.exploratory_talks,
                dict(quota.applications),
            )
            clone.submit(application_id, exploratory=exploratory)
            if withdraw:
                clone.withdraw(application_id)
            if manager_timeout:
                clone.protect_from_manager_delay(application_id)
            return clone

        def commit(plan: ApplicationQuota) -> None:
            quota.used = plan.used
            quota.exploratory_talks = plan.exploratory_talks
            quota.applications = plan.applications
            self.application_quota = quota

        return self.apply(318, token, action_serial, {"APPLIED"}, precheck, commit)

    def make_counteroffer(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        employee_accepts: bool,
        handover_deadline: int,
        promised_terms: Sequence[str] = (),
        commitment_due_day: int | None = None,
    ) -> MutationOutcome:
        def precheck() -> tuple[int, int | None, tuple[str, ...], int | None]:
            if self.counteroffer_count >= 1:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "counteroffer", "one offer maximum")
            due = _int("handover_deadline", handover_deadline, minimum=1)
            if not isinstance(employee_accepts, bool):
                raise ModelRed(RedCode.INVALID_TYPE, "employee_accepts", "must be bool")
            terms = _unique("promised_terms", promised_terms, allow_empty=True)
            promise_due: int | None = None
            if employee_accepts:
                if not terms or commitment_due_day is None:
                    raise ModelRed(
                        RedCode.INVALID_VALUE,
                        "promised_terms",
                        "an accepted counteroffer needs deliverable terms and a due day",
                    )
                promise_due = _int("commitment_due_day", commitment_due_day, minimum=1)
            return 1, None if employee_accepts else due, terms, promise_due

        def commit(plan: tuple[int, int | None, tuple[str, ...], int | None]) -> None:
            self.counteroffer_count += plan[0]
            self.release_deadline = plan[1]
            self.counteroffer_terms = plan[2]
            self.commitment_due_day = plan[3]

        return self.apply(319, token, action_serial, {"RELEASE_DECIDED"}, precheck, commit, next_state="MOVED")

    def settle_release(self, *, day: int) -> int:
        day = _int("day", day, minimum=1)
        if self.release_deadline is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "release_deadline", "not owed")
        if self.released_day is not None:
            return self.manager_talent_delta
        self.released_day = day
        if day > self.release_deadline:
            self.manager_talent_delta -= 20
        return self.manager_talent_delta

    def settle_counteroffer_commitment(self, *, day: int, fulfilled: bool) -> int:
        day = _int("day", day, minimum=1)
        if self.commitment_due_day is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "commitment", "no accepted counteroffer")
        if not isinstance(fulfilled, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "fulfilled", "must be bool")
        if self.commitment_settled:
            return self.manager_talent_delta
        self.commitment_settled = True
        if not fulfilled or day > self.commitment_due_day:
            self.manager_talent_delta -= 20
        return self.manager_talent_delta

    def aggregate_exit_voice(
        self,
        token: CaseToken,
        action_serial: str,
        book: ExitInterviewBook,
        interviews: Sequence[ExitInterview],
    ) -> MutationOutcome:
        def precheck() -> ExitInterviewBook:
            clone = ExitInterviewBook(book.minimum_sample)
            clone.interviews = dict(book.interviews)
            clone.original_issues = dict(book.original_issues)
            clone.reclassification_log = list(book.reclassification_log)
            for interview in interviews:
                clone.add(interview)
            return clone

        def commit(plan: ExitInterviewBook) -> None:
            book.interviews = plan.interviews
            book.original_issues = plan.original_issues
            book.reclassification_log = plan.reclassification_log
            self.exit_interview_book = book

        return self.apply(320, token, action_serial, {"MOVED"}, precheck, commit, next_state="ALUMNI")

    def maintain_alumni_relationship(
        self,
        token: CaseToken,
        action_serial: str,
        network: AlumniNetwork,
        record: AlumniRecord,
        ledger: DualPayerLedger,
        *,
        cycle_serial: int,
        total_cost: int,
        treasury_share: int,
    ) -> MutationOutcome:
        def precheck() -> tuple[GoldChargePlan, tuple[str, int]]:
            _text("character_id", record.character_id)
            if record.character_id in network.records:
                raise ModelRed(RedCode.DUPLICATE_ID, "character_id", "already in alumni pool")
            if not record.consent:
                raise ModelRed(RedCode.PERMISSION_DENIED, "consent", "contact refused")
            cycle = _int("cycle_serial", cycle_serial, minimum=1)
            charge = ledger.plan_charge(
                f"alumni:{record.character_id}:{cycle}",
                total=total_cost,
                treasury_share=treasury_share,
            )
            return charge, (record.character_id, cycle)

        def commit(plan: tuple[GoldChargePlan, tuple[str, int]]) -> None:
            charge, maintenance_key = plan
            ledger.commit_charge(charge)
            network.add(record)
            network.maintenance_receipts.add(maintenance_key)
            self.alumni_network = network

        return self.apply(321, token, action_serial, {"MOVED"}, precheck, commit, next_state="ALUMNI")

    def open_returnee_case(
        self,
        token: CaseToken,
        action_serial: str,
        registry: ReturneeRegistry,
        returnee: ReturneeCase,
    ) -> MutationOutcome:
        def precheck() -> ReturneeCase:
            if returnee.character_id in registry.cases:
                raise ModelRed(RedCode.CONFLICT, "character_id", "one active returnee flow")
            _unique("old_case_ids", returnee.old_case_ids)
            _text("new_cohort_id", returnee.new_cohort_id)
            return returnee

        def commit(plan: ReturneeCase) -> None:
            registry.open(plan)
            self.returnee_registry = registry

        return self.apply(322, token, action_serial, {"ALUMNI"}, precheck, commit, next_state="CLOSED")


@dataclass
class ApplicationQuota:
    formal_limit: int = 2
    used: int = 0
    exploratory_talks: int = 0
    applications: dict[str, str] = field(default_factory=dict)

    def submit(self, application_id: str, *, exploratory: bool = False) -> None:
        application_id = _text("application_id", application_id)
        if application_id in self.applications:
            raise ModelRed(RedCode.DUPLICATE_ID, "application_id", "already exists")
        if exploratory:
            self.exploratory_talks += 1
            self.applications[application_id] = "exploratory"
            return
        if self.used >= self.formal_limit:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "formal_slots", "limit reached")
        self.used += 1
        self.applications[application_id] = "submitted"

    def withdraw(self, application_id: str) -> None:
        if self.applications.get(application_id) != "submitted":
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "application", "not submitted")
        self.applications[application_id] = "withdrawn"  # the consumed slot stays consumed

    def protect_from_manager_delay(self, application_id: str) -> None:
        if self.applications.get(application_id) != "submitted":
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "application", "not pending")
        self.applications[application_id] = "manager-timeout"
        self.used -= 1


@dataclass(frozen=True)
class ExitInterview:
    interview_id: str
    leaver_id: str
    manager_id: str
    role_id: str
    response_mode: str
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        _text("interview_id", self.interview_id)
        _text("leaver_id", self.leaver_id)
        _text("manager_id", self.manager_id)
        _text("role_id", self.role_id)
        if self.response_mode not in {"named", "anonymous", "declined"}:
            raise ModelRed(RedCode.INVALID_VALUE, "response_mode", "unknown mode")
        _unique("issues", self.issues, allow_empty=True)


@dataclass
class ExitInterviewBook:
    minimum_sample: int
    interviews: dict[str, ExitInterview] = field(default_factory=dict)
    original_issues: dict[str, tuple[str, ...]] = field(default_factory=dict)
    reclassification_log: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = field(default_factory=list)

    def __post_init__(self) -> None:
        _int("minimum_sample", self.minimum_sample, minimum=2)

    def add(self, interview: ExitInterview) -> None:
        if interview.interview_id in self.interviews:
            raise ModelRed(RedCode.DUPLICATE_ID, "interview_id", "already aggregated")
        self.interviews[interview.interview_id] = interview
        self.original_issues[interview.interview_id] = interview.issues

    def reclassify(self, interview_id: str, new_issues: Sequence[str]) -> None:
        if interview_id not in self.interviews:
            raise ModelRed(RedCode.INVALID_VALUE, "interview_id", "unknown")
        new_value = _unique("new_issues", new_issues, allow_empty=True)
        self.reclassification_log.append((interview_id, self.original_issues[interview_id], new_value))

    def audit_issues(self, manager_id: str) -> frozenset[str]:
        counts: dict[str, int] = {}
        for interview in self.interviews.values():
            if interview.manager_id != manager_id or interview.response_mode == "declined":
                continue
            for issue in self.original_issues[interview.interview_id]:
                counts[issue] = counts.get(issue, 0) + 1
        return frozenset(issue for issue, count in counts.items() if count >= self.minimum_sample)

    def public_rows(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        rows = []
        for interview in self.interviews.values():
            identity = "anonymous" if interview.response_mode == "anonymous" else interview.leaver_id
            rows.append((identity, interview.issues))
        return tuple(rows)


@dataclass(frozen=True)
class AlumniRecord:
    character_id: str
    consent: bool
    contact_policy: str
    skill_tags: tuple[str, ...]
    humiliation_history: bool = False


@dataclass
class AlumniNetwork:
    records: dict[str, AlumniRecord] = field(default_factory=dict)
    maintenance_receipts: set[tuple[str, int]] = field(default_factory=set)
    leads: set[str] = field(default_factory=set)
    talent_reputation: int = 0

    def add(self, record: AlumniRecord) -> None:
        _text("character_id", record.character_id)
        if record.character_id in self.records:
            raise ModelRed(RedCode.DUPLICATE_ID, "character_id", "already in alumni pool")
        self.records[record.character_id] = record
        if record.humiliation_history:
            self.talent_reputation -= 10

    def maintain(
        self,
        character_id: str,
        cycle_serial: int,
        ledger: DualPayerLedger,
        *,
        total_cost: int,
        treasury_share: int,
    ) -> None:
        record = self.records.get(character_id)
        if record is None:
            raise ModelRed(RedCode.INVALID_VALUE, "character_id", "unknown alumnus")
        if not record.consent:
            raise ModelRed(RedCode.PERMISSION_DENIED, "consent", "contact refused")
        key = (character_id, _int("cycle_serial", cycle_serial, minimum=1))
        if key in self.maintenance_receipts:
            return
        plan = ledger.plan_charge(
            f"alumni:{character_id}:{cycle_serial}", total=total_cost, treasury_share=treasury_share
        )
        ledger.commit_charge(plan)
        self.maintenance_receipts.add(key)

    def add_lead(self, lead_id: str) -> None:
        lead_id = _text("lead_id", lead_id)
        if lead_id in self.leads:
            return
        self.leads.add(lead_id)

    def delete_contact_projection(self, character_id: str) -> None:
        # UI contact projection may disappear, but humiliation/reputation evidence is immutable.
        if character_id not in self.records:
            raise ModelRed(RedCode.INVALID_VALUE, "character_id", "unknown")


@dataclass(frozen=True)
class ReturneeCase:
    character_id: str
    old_case_ids: tuple[str, ...]
    exit_reason: str
    old_misconduct_refs: tuple[str, ...]
    external_evidence_ids: tuple[str, ...]
    new_cycle_id: int
    new_cohort_id: str
    history_wipe_attempt: bool = False


@dataclass
class ReturneeRegistry:
    cases: dict[str, ReturneeCase] = field(default_factory=dict)

    def open(self, case: ReturneeCase) -> None:
        _text("character_id", case.character_id)
        _unique("old_case_ids", case.old_case_ids)
        _text("exit_reason", case.exit_reason)
        _unique("old_misconduct_refs", case.old_misconduct_refs, allow_empty=True)
        _unique("external_evidence_ids", case.external_evidence_ids, allow_empty=True)
        _int("new_cycle_id", case.new_cycle_id, minimum=1)
        _text("new_cohort_id", case.new_cohort_id)
        if case.character_id in self.cases:
            raise ModelRed(RedCode.CONFLICT, "character_id", "one active returnee flow")
        self.cases[case.character_id] = case


@dataclass
class LearningBudget:
    treasury_pool: int
    protected_time_pool: int
    allocated_gold: int = 0
    allocated_time: int = 0
    allocations: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        _int("treasury_pool", self.treasury_pool, minimum=0)
        _int("protected_time_pool", self.protected_time_pool, minimum=0)

    def plan_allocate(
        self,
        allocation_id: str,
        *,
        gold: int,
        hours: int,
        ledger: DualPayerLedger,
        manager_share: int,
    ) -> tuple[str, int, int, GoldChargePlan]:
        allocation_id = _text("allocation_id", allocation_id)
        if allocation_id in self.allocations:
            raise ModelRed(RedCode.DUPLICATE_ID, "allocation_id", "already allocated")
        gold = _int("gold", gold, minimum=2)
        hours = _int("hours", hours, minimum=1)
        if self.allocated_gold + gold > self.treasury_pool:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "treasury_pool", "learning gold exceeded")
        if self.allocated_time + hours > self.protected_time_pool:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "protected_time_pool", "learning time exceeded")
        charge = ledger.plan_charge(
            f"learning:{allocation_id}", total=gold, treasury_share=gold - manager_share
        )
        return allocation_id, gold, hours, charge

    def commit_allocate(
        self, plan: tuple[str, int, int, GoldChargePlan], ledger: DualPayerLedger
    ) -> None:
        allocation_id, gold, hours, charge = plan
        ledger.commit_charge(charge)
        self.allocated_gold += gold
        self.allocated_time += hours
        self.allocations.add(allocation_id)


@dataclass
class ProtectedLearningTime:
    total_capacity: int
    protected_hours: int
    used_learning_hours: int = 0
    borrowed_hours: int = 0
    repayment_due_cycle: int | None = None
    repaid_hours: int = 0
    consecutive_diversions: int = 0
    manager_score_delta: int = 0

    def __post_init__(self) -> None:
        _int("total_capacity", self.total_capacity, minimum=1)
        _int("protected_hours", self.protected_hours, minimum=0, maximum=self.total_capacity)

    @property
    def delivery_hours(self) -> int:
        return self.total_capacity - self.protected_hours + self.borrowed_hours - self.repaid_hours

    def use_for_learning(self, hours: int) -> None:
        hours = _int("hours", hours, minimum=1)
        if self.used_learning_hours + hours > self.protected_hours - self.borrowed_hours:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "learning_hours", "protected pool exceeded")
        self.used_learning_hours += hours

    def borrow_for_crisis(self, hours: int, *, current_cycle: int, real_crisis: bool) -> None:
        hours = _int("hours", hours, minimum=1)
        current_cycle = _int("current_cycle", current_cycle, minimum=1)
        if not real_crisis:
            raise ModelRed(RedCode.PERMISSION_DENIED, "crisis", "borrowing requires a real crisis")
        if self.borrowed_hours + hours > self.protected_hours:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "borrowed_hours", "protected pool exceeded")
        self.borrowed_hours += hours
        self.repayment_due_cycle = current_cycle + 1

    def repay(self, hours: int, *, cycle: int) -> None:
        hours = _int("hours", hours, minimum=1)
        cycle = _int("cycle", cycle, minimum=1)
        if self.repaid_hours + hours > self.borrowed_hours:
            raise ModelRed(RedCode.INVARIANT_BREACH, "repaid_hours", "repay exceeds debt")
        self.repaid_hours += hours
        if self.repayment_due_cycle is not None and cycle > self.repayment_due_cycle:
            self.manager_score_delta -= 10


@dataclass
class TrainingContract:
    contract_id: str
    cost_receipt_id: str
    training_cost: int
    completion_day: int
    service_end_day: int
    monthly_reduction: int
    ledger: DualPayerLedger
    recovered: bool = False
    application_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("contract_id", self.contract_id)
        _text("cost_receipt_id", self.cost_receipt_id)
        _int("training_cost", self.training_cost, minimum=2)
        _int("completion_day", self.completion_day, minimum=1)
        _int("service_end_day", self.service_end_day, minimum=self.completion_day + 1)
        _int("monthly_reduction", self.monthly_reduction, minimum=1)

    def outstanding(self, day: int) -> int:
        day = _int("day", day, minimum=self.completion_day)
        months = max(0, (day - self.completion_day) // 30)
        return max(0, self.training_cost - months * self.monthly_reduction)

    def settle_exit(self, *, day: int, reason: str, employee_gold: int) -> tuple[int, int]:
        if self.recovered:
            return employee_gold, 0
        reason = _text("reason", reason)
        employee_gold = _int("employee_gold", employee_gold, minimum=0)
        amount = 0 if reason in {"organization-layoff", "completed-service"} else self.outstanding(day)
        if amount > employee_gold:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "employee_gold", "cannot recover atomically")
        self.ledger.refund_exact(self.cost_receipt_id, amount)
        self.recovered = True
        return employee_gold - amount, amount


@dataclass
class LearningCase(GuardedCase):
    owner: Actor = field(default_factory=lambda: Actor("manager", TitleRank.DUKE, True, True))
    subject: Actor = field(default_factory=lambda: Actor("official", TitleRank.COUNT, True, True))
    data: dict[str, Any] = field(default_factory=dict)
    performance_delta: int = 0
    manager_consequences: list[str] = field(default_factory=list)
    training_contract: TrainingContract | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        authorize_manager(self.owner, channel="background" if self.owner.is_ai else "visible")
        if self.identity.owner_id != self.owner.actor_id or self.identity.subject_id != self.subject.actor_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "identity", "learning owner/subject mismatch")

    def allocate_budget(
        self,
        token: CaseToken,
        action_serial: str,
        budget: LearningBudget,
        ledger: DualPayerLedger,
        *,
        allocation_id: str,
        target_group: str,
        gold: int,
        hours: int,
        manager_share: int,
    ) -> MutationOutcome:
        def precheck() -> tuple[str, tuple[str, int, int, GoldChargePlan]]:
            target = _text("target_group", target_group)
            if target not in {"gap", "high-potential", "manager", "foundation"}:
                raise ModelRed(RedCode.INVALID_VALUE, "target_group", "unknown learning group")
            return target, budget.plan_allocate(
                allocation_id,
                gold=gold,
                hours=hours,
                ledger=ledger,
                manager_share=manager_share,
            )

        def commit(plan: tuple[str, tuple[str, int, int, GoldChargePlan]]) -> None:
            target, allocation = plan
            budget.commit_allocate(allocation, ledger)
            self.data["target_group"] = target
            self.data["allocation_id"] = allocation_id
            self.data["completion_is_performance"] = False

        return self.apply(323, token, action_serial, {"BUDGETED"}, precheck, commit, next_state="ENROLLED")

    def advance_learning_stages(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        completion_evidence: str,
        application_evidence: str | None,
        observed_delta: int | None,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            completion = _text("completion_evidence", completion_evidence)
            application = None if application_evidence is None else _text("application_evidence", application_evidence)
            if observed_delta is not None and application is None:
                raise ModelRed(RedCode.INVARIANT_BREACH, "observed_delta", "outcome requires application")
            delta = 0 if observed_delta is None else _int("observed_delta", observed_delta)
            return {
                "completion": completion,
                "application": application,
                "outcome": delta if observed_delta is not None else None,
                "performance_credit": delta if application is not None else 0,
            }

        def commit(plan: dict[str, Any]) -> None:
            self.data["three_stages"] = plan
            self.performance_delta += plan["performance_credit"]

        return self.apply(324, token, action_serial, {"BUDGETED"}, precheck, commit, next_state="MEASURED")

    def assess_competence(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        certificate_passed: bool,
        practical_score: int,
        practical_threshold: int,
        test_valid: bool,
        existing_evidence: Sequence[str] = (),
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            if not isinstance(certificate_passed, bool) or not isinstance(test_valid, bool):
                raise ModelRed(RedCode.INVALID_TYPE, "certificate/test_valid", "must be bool")
            score = _int("practical_score", practical_score, minimum=0, maximum=100)
            threshold = _int("practical_threshold", practical_threshold, minimum=1, maximum=100)
            existing = _unique("existing_evidence", existing_evidence, allow_empty=True)
            exempt = bool(existing)
            competent = certificate_passed and (exempt or (test_valid and score >= threshold))
            return {"certificate": certificate_passed, "practical": score, "exempt": exempt, "competent": competent, "test_valid": test_valid}

        def commit(plan: dict[str, Any]) -> None:
            self.data["competence"] = plan
            if not plan["test_valid"]:
                self.manager_consequences.append("training-owner-test-invalid")

        return self.apply(325, token, action_serial, {"BUDGETED"}, precheck, commit, next_state="ENROLLED")

    def settle_conference(
        self,
        token: CaseToken,
        action_serial: str,
        ledger: DualPayerLedger,
        *,
        receipt_id: str,
        total_cost: int,
        treasury_share: int,
        days_away: int,
        artifact_id: str | None,
        adopted_value: int,
    ) -> MutationOutcome:
        def precheck() -> tuple[GoldChargePlan, dict[str, Any]]:
            away = _int("days_away", days_away, minimum=1)
            artifact = None if artifact_id is None else _text("artifact_id", artifact_id)
            value = _int("adopted_value", adopted_value, minimum=0)
            if value and artifact is None:
                raise ModelRed(RedCode.INVARIANT_BREACH, "adopted_value", "adoption needs artifact")
            charge = ledger.plan_charge(receipt_id, total=total_cost, treasury_share=treasury_share)
            return charge, {
                "days_away": away,
                "artifact": artifact,
                "adopted_value": value,
                "reputation_gain": 2,
                "delivery_opportunity_cost": away,
                "attrition_risk": 1,
            }

        def commit(plan: tuple[GoldChargePlan, dict[str, Any]]) -> None:
            charge, data = plan
            ledger.commit_charge(charge)
            self.data["conference"] = data
            self.performance_delta += data["adopted_value"]

        return self.apply(326, token, action_serial, {"ENROLLED"}, precheck, commit, next_state="COMPLETED")

    def attribute_teaching(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        teaching_hours: int,
        available_hours: int,
        attendees: Sequence[str],
        applying_attendees: Sequence[str],
        shares: Mapping[str, int],
        downstream_value: int,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            hours = _int("teaching_hours", teaching_hours, minimum=1)
            capacity = _int("available_hours", available_hours, minimum=hours)
            attendee_ids = _unique("attendees", attendees)
            applying = _unique("applying_attendees", applying_attendees, allow_empty=True)
            if not set(applying).issubset(attendee_ids):
                raise ModelRed(RedCode.INVARIANT_BREACH, "applying_attendees", "must have attended")
            share_map = _shares_100("shares", shares)
            value = _int("downstream_value", downstream_value, minimum=0)
            if value and not applying:
                raise ModelRed(RedCode.INVARIANT_BREACH, "downstream_value", "requires application")
            return {"hours": hours, "remaining": capacity - hours, "attendees": attendee_ids, "applying": applying, "shares": share_map, "impact": value}

        def commit(plan: dict[str, Any]) -> None:
            self.data["teaching"] = plan
            self.performance_delta += plan["impact"] * plan["shares"].get("teacher", 0) // 100

        return self.apply(327, token, action_serial, {"ENROLLED"}, precheck, commit, next_state="COMPLETED")

    def settle_community(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        artifacts: Sequence[str],
        maintainers: Sequence[str],
        contribution_hours: Mapping[str, int],
        available_hours: Mapping[str, int],
        adopting_teams: Sequence[str],
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            artifact_ids = _unique("artifacts", artifacts)
            maintainer_ids = _unique("maintainers", maintainers)
            adopters = _unique("adopting_teams", adopting_teams, allow_empty=True)
            hours = {key: _int(f"hours.{key}", value, minimum=0) for key, value in contribution_hours.items()}
            for member, used in hours.items():
                if used > _int(f"available_hours.{member}", available_hours.get(member, -1), minimum=0):
                    raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "contribution_hours", member)
            return {"artifacts": artifact_ids, "maintainers": maintainer_ids, "adopters": adopters, "hours": hours, "impact": len(adopters)}

        def commit(plan: dict[str, Any]) -> None:
            self.data["community"] = plan
            self.performance_delta += plan["impact"]

        return self.apply(328, token, action_serial, {"COMPLETED"}, precheck, commit, next_state="APPLIED")

    def match_mentor(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        mentor_id: str,
        goal_ids: Sequence[str],
        committed_hours: int,
        end_day: int,
        rematch_from: str | None = None,
        application_evidence: Sequence[str] = (),
        capacity_payment: int = 0,
        favor_debt: bool = False,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            mentor = _text("mentor_id", mentor_id)
            goals = _unique("goal_ids", goal_ids)
            hours = _int("committed_hours", committed_hours, minimum=1)
            due = _int("end_day", end_day, minimum=1)
            applications = _unique("application_evidence", application_evidence, allow_empty=True)
            payment = _int("capacity_payment", capacity_payment, minimum=0)
            if not isinstance(favor_debt, bool):
                raise ModelRed(RedCode.INVALID_TYPE, "favor_debt", "must be bool")
            if payment == 0 and not favor_debt:
                raise ModelRed(
                    RedCode.INVARIANT_BREACH,
                    "mentor_resource",
                    "beneficiary must pay capacity or explicit favor debt",
                )
            if rematch_from is not None:
                _text("rematch_from", rematch_from)
                if self.data.get("mentor_rematch_used"):
                    raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "rematch", "only one rematch")
                old_end = self.data.get("mentor_end_day")
                if old_end is not None and due != old_end:
                    raise ModelRed(RedCode.INVARIANT_BREACH, "end_day", "rematch cannot reset deadline")
            return {
                "mentor": mentor,
                "goals": goals,
                "hours": hours,
                "end_day": due,
                "applications": applications,
                "credit": len(applications),
                "capacity_payment": payment,
                "favor_debt": favor_debt,
            }

        def commit(plan: dict[str, Any]) -> None:
            self.data["mentorship"] = plan
            self.data["mentor_end_day"] = plan["end_day"]
            if rematch_from is not None:
                self.data["mentor_rematch_used"] = True

        return self.apply(329, token, action_serial, {"COMPLETED"}, precheck, commit, next_state="APPLIED")

    def rematch_mentor(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        old_mentor_id: str,
        new_mentor_id: str,
        conflict_reason: str,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            current = self.data.get("mentorship")
            if current is None or current["mentor"] != _text("old_mentor_id", old_mentor_id):
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "mentor", "old mentor mismatch")
            if self.data.get("mentor_rematch_used"):
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "rematch", "only one rematch")
            replacement = dict(current)
            replacement["mentor"] = _text("new_mentor_id", new_mentor_id)
            replacement["conflict_reason"] = _text("conflict_reason", conflict_reason)
            return replacement

        def commit(plan: dict[str, Any]) -> None:
            self.data["mentorship"] = plan
            self.data["mentor_rematch_used"] = True

        return self.apply(329, token, action_serial, {"APPLIED"}, precheck, commit)

    def settle_reskill(
        self,
        token: CaseToken,
        action_serial: str,
        ledger: DualPayerLedger,
        *,
        route: str,
        receipt_id: str,
        total_cost: int,
        treasury_share: int,
        assessment_score: int,
        threshold: int,
        affected_character_ids: Sequence[str] = (),
        target_role_ids: Sequence[str] = (),
        training_days: int = 1,
    ) -> MutationOutcome:
        def precheck() -> tuple[GoldChargePlan, dict[str, Any]]:
            route_value = _text("route", route)
            if route_value not in {"reskill", "external-hire"}:
                raise ModelRed(RedCode.INVALID_VALUE, "route", "unknown route")
            score = _int("assessment_score", assessment_score, minimum=0, maximum=100)
            floor = _int("threshold", threshold, minimum=1, maximum=100)
            people = _unique("affected_character_ids", affected_character_ids)
            roles = _unique("target_role_ids", target_role_ids)
            days = _int("training_days", training_days, minimum=1)
            charge = ledger.plan_charge(receipt_id, total=total_cost, treasury_share=treasury_share)
            return charge, {
                "route": route_value,
                "placed": score >= floor,
                "failed_is_low_grade": False,
                "affected_character_ids": people,
                "target_role_ids": roles,
                "training_days": days,
                "fairness_debt": 0 if route_value == "reskill" else len(people),
            }

        def commit(plan: tuple[GoldChargePlan, dict[str, Any]]) -> None:
            charge, data = plan
            ledger.commit_charge(charge)
            self.data["reskill"] = data

        return self.apply(330, token, action_serial, {"APPLIED"}, precheck, commit, next_state="MEASURED")

    def settle_protected_time(
        self,
        token: CaseToken,
        action_serial: str,
        capacity: ProtectedLearningTime,
        *,
        borrow_hours: int,
        current_cycle: int,
        real_crisis: bool,
    ) -> MutationOutcome:
        def precheck() -> tuple[int, int, bool]:
            hours = _int("borrow_hours", borrow_hours, minimum=1)
            cycle = _int("current_cycle", current_cycle, minimum=1)
            if not real_crisis:
                raise ModelRed(RedCode.PERMISSION_DENIED, "real_crisis", "protected time cannot be silently diverted")
            if capacity.borrowed_hours + hours > capacity.protected_hours:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "borrow_hours", "exceeds protected pool")
            return hours, cycle, real_crisis

        def commit(plan: tuple[int, int, bool]) -> None:
            hours, cycle, crisis = plan
            capacity.borrow_for_crisis(hours, current_cycle=cycle, real_crisis=crisis)
            self.data["learning_debt_due"] = capacity.repayment_due_cycle

        return self.apply(331, token, action_serial, {"APPLIED"}, precheck, commit, next_state="MEASURED")

    def run_succession_drill(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        readiness_before: int,
        success: bool,
        emergency_veto_uses: int,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            before = _int("readiness_before", readiness_before, minimum=0, maximum=100)
            if not isinstance(success, bool):
                raise ModelRed(RedCode.INVALID_TYPE, "success", "must be bool")
            veto = _int("emergency_veto_uses", emergency_veto_uses, minimum=0, maximum=1)
            after = min(100, before + (10 if success else 2))
            return {"safe_simulation": True, "veto_uses": veto, "readiness_before": before, "readiness_after": after, "development_gap": None if success else "drill-gap", "real_incident": False, "low_grade": False}

        return self.apply(
            332,
            token,
            action_serial,
            {"MEASURED"},
            precheck,
            lambda plan: self.data.__setitem__("succession_drill", plan),
            next_state="SPREAD",
        )

    def open_training_commitment(
        self,
        token: CaseToken,
        action_serial: str,
        ledger: DualPayerLedger,
        *,
        contract_id: str,
        receipt_id: str,
        cost: int,
        treasury_share: int,
        completion_day: int,
        service_end_day: int,
        monthly_reduction: int,
        application_evidence: Sequence[str] = (),
    ) -> MutationOutcome:
        def precheck() -> tuple[GoldChargePlan, TrainingContract]:
            charge = ledger.plan_charge(receipt_id, total=cost, treasury_share=treasury_share)
            contract = TrainingContract(
                _text("contract_id", contract_id),
                receipt_id,
                cost,
                completion_day,
                service_end_day,
                monthly_reduction,
                ledger,
                application_evidence=_unique("application_evidence", application_evidence, allow_empty=True),
            )
            return charge, contract

        def commit(plan: tuple[GoldChargePlan, TrainingContract]) -> None:
            charge, contract = plan
            ledger.commit_charge(charge)
            self.training_contract = contract
            self.data["training_performance_credit"] = len(contract.application_evidence)

        return self.apply(333, token, action_serial, {"MEASURED"}, precheck, commit, next_state="SPREAD")


class CycleFrequency(str, Enum):
    ANNUAL = "annual"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"


@dataclass(frozen=True)
class PolicyCalendar:
    frequency: CycleFrequency
    effective_cycle: int
    final_review_days: tuple[int, ...]
    checkin_days: tuple[int, ...]
    admin_hours: int
    event_interrupts: int

    def __post_init__(self) -> None:
        if not isinstance(self.frequency, CycleFrequency):
            raise ModelRed(RedCode.INVALID_TYPE, "frequency", "must be CycleFrequency")
        _int("effective_cycle", self.effective_cycle, minimum=1)
        tuple(_int("final_review_days", day, minimum=1, maximum=365) for day in self.final_review_days)
        tuple(_int("checkin_days", day, minimum=1, maximum=365) for day in self.checkin_days)
        _int("admin_hours", self.admin_hours, minimum=0)
        _int("event_interrupts", self.event_interrupts, minimum=0)
        expected = {CycleFrequency.ANNUAL: 1, CycleFrequency.SEMIANNUAL: 2, CycleFrequency.QUARTERLY: 4}[self.frequency]
        if len(self.final_review_days) != expected:
            raise ModelRed(RedCode.INVARIANT_BREACH, "final_review_days", "frequency mismatch")
        if self.frequency is CycleFrequency.ANNUAL and len(self.checkin_days) != 1:
            raise ModelRed(RedCode.INVARIANT_BREACH, "checkin_days", "annual route needs one light check-in")
        if self.event_interrupts > expected:
            raise ModelRed(RedCode.INVARIANT_BREACH, "event_interrupts", "AI/player work must batch per cycle")


@dataclass
class OverrideBook:
    algorithmic_order: tuple[str, ...]
    budget_points: int
    used_points: int = 0
    final_order: list[str] = field(init=False)
    entries: list[tuple[str, str, str]] = field(default_factory=list)
    next_cycle_budget: int = field(init=False)

    def __post_init__(self) -> None:
        self.algorithmic_order = _unique("algorithmic_order", self.algorithmic_order)
        self.budget_points = _int("budget_points", self.budget_points, minimum=0)
        self.final_order = list(self.algorithmic_order)
        self.next_cycle_budget = self.budget_points

    def override(self, beneficiary: str, bearer: str, reason: str) -> None:
        beneficiary = _text("beneficiary", beneficiary)
        bearer = _text("bearer", bearer)
        reason = _text("reason", reason)
        if beneficiary == bearer or beneficiary not in self.final_order or bearer not in self.final_order:
            raise ModelRed(RedCode.INVARIANT_BREACH, "override_pair", "two listed distinct officials required")
        if self.used_points >= self.budget_points:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "override_budget", "exhausted")
        i, j = self.final_order.index(beneficiary), self.final_order.index(bearer)
        self.final_order[i], self.final_order[j] = self.final_order[j], self.final_order[i]
        self.entries.append((beneficiary, bearer, reason))
        self.used_points += 1

    def write_back(self, *, appeal_overturned: bool, later_success: bool) -> None:
        if appeal_overturned:
            self.next_cycle_budget = max(0, self.next_cycle_budget - 1)
        elif later_success:
            self.next_cycle_budget += 1


@dataclass(frozen=True)
class PolicyExceptionToken:
    owner_id: str
    cycle_serial: int
    case_serial: int
    exception_id: str
    expected_state: str
    expiry_day: int


@dataclass
class PolicyException:
    owner_id: str
    cycle_serial: int
    case_serial: int
    exception_id: str
    exception_type: str
    beneficiary_id: str
    expiry_day: int
    state: str = "ACTIVE"
    cleanup_entries: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _text("owner_id", self.owner_id)
        _int("cycle_serial", self.cycle_serial, minimum=1)
        _int("case_serial", self.case_serial, minimum=1)
        _text("exception_id", self.exception_id)
        _text("exception_type", self.exception_type)
        _text("beneficiary_id", self.beneficiary_id)
        _int("expiry_day", self.expiry_day, minimum=1)

    def token(self) -> PolicyExceptionToken:
        return PolicyExceptionToken(
            self.owner_id,
            self.cycle_serial,
            self.case_serial,
            self.exception_id,
            self.state,
            self.expiry_day,
        )

    def due(
        self,
        token: PolicyExceptionToken,
        *,
        day: int,
        new_fact_ids: Sequence[str] = (),
        renewed_expiry_day: int | None = None,
    ) -> str:
        if token != self.token():
            return NoOpCode.STALE_TOKEN.value
        day = _int("day", day, minimum=1)
        if day < self.expiry_day:
            raise ModelRed(RedCode.DEADLINE_NOT_DUE, "day", "exception not due")
        if self.state != "ACTIVE":
            return NoOpCode.DUPLICATE_ACTION.value
        facts = _unique("new_fact_ids", new_fact_ids, allow_empty=True)
        if facts:
            if renewed_expiry_day is None:
                raise ModelRed(RedCode.INVALID_VALUE, "renewed_expiry_day", "renewal needs a new date")
            renewed = _int("renewed_expiry_day", renewed_expiry_day, minimum=day + 1)
            self.expiry_day = renewed
            self.cleanup_entries.append(f"renewed:{','.join(facts)}")
            return "renewed"
        self.state = "EXPIRED"
        self.cleanup_entries.append("restore-default")
        return "expired"


@dataclass(frozen=True)
class HistoricalRecord:
    record_id: str
    original_value: float
    original_formula: str
    policy_version: str

    def __post_init__(self) -> None:
        _text("record_id", self.record_id)
        _number("original_value", self.original_value)
        _text("original_formula", self.original_formula)
        _text("policy_version", self.policy_version)


@dataclass
class PolicyCase(GuardedCase):
    owner: Actor = field(default_factory=lambda: Actor("manager", TitleRank.DUKE, True, True))
    data: dict[str, Any] = field(default_factory=dict)
    manager_score_delta: int = 0
    trust_delta: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        authorize_manager(self.owner, channel="background" if self.owner.is_ai else "visible")
        if self.identity.owner_id != self.owner.actor_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "identity", "policy owner mismatch")

    def freeze_calendar(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        frequency: CycleFrequency,
        effective_cycle: int,
    ) -> MutationOutcome:
        def precheck() -> PolicyCalendar:
            effective = _int("effective_cycle", effective_cycle, minimum=self.identity.cycle_serial + 1)
            if frequency is CycleFrequency.ANNUAL:
                return PolicyCalendar(frequency, effective, (330,), (180,), 20, 1)
            if frequency is CycleFrequency.SEMIANNUAL:
                return PolicyCalendar(frequency, effective, (180, 360), (), 36, 2)
            if frequency is CycleFrequency.QUARTERLY:
                return PolicyCalendar(frequency, effective, (90, 180, 270, 360), (), 72, 4)
            raise ModelRed(RedCode.INVALID_TYPE, "frequency", "unknown frequency")

        return self.apply(
            345,
            token,
            action_serial,
            {"DRAFTED"},
            precheck,
            lambda plan: self.data.__setitem__("calendar", plan),
            next_state="PILOTED",
        )

    def record_offcycle_signal(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        signal_id: str,
        materiality: int,
        action: str,
        threshold: int = 50,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            signal = _text("signal_id", signal_id)
            score = _int("materiality", materiality, minimum=0, maximum=100)
            floor = _int("threshold", threshold, minimum=1, maximum=100)
            if score < floor:
                raise ModelRed(RedCode.INVALID_VALUE, "materiality", "ordinary fluctuation creates no case")
            action_value = _text("action", action)
            if action_value not in {"reward", "investigate", "adjust-goal"}:
                raise ModelRed(RedCode.INVALID_VALUE, "action", "exactly one bounded action required")
            return {"signal_id": signal, "materiality": score, "action": action_value, "consumed": False, "cohort_reruns": 0}

        return self.apply(
            346,
            token,
            action_serial,
            {"DRAFTED"},
            precheck,
            lambda plan: self.data.__setitem__("offcycle_signal", plan),
            next_state="PILOTED",
        )

    def consume_offcycle_signal(self, cycle_serial: int) -> bool:
        signal = self.data.get("offcycle_signal")
        if signal is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "offcycle_signal", "missing")
        _int("cycle_serial", cycle_serial, minimum=1)
        if signal["consumed"]:
            return False
        signal["consumed"] = True
        signal["consumed_cycle"] = cycle_serial
        return True

    def apply_override_book(
        self,
        token: CaseToken,
        action_serial: str,
        book: OverrideBook,
        operations: Sequence[tuple[str, str, str]],
    ) -> MutationOutcome:
        def precheck() -> OverrideBook:
            clone = OverrideBook(book.algorithmic_order, book.budget_points)
            clone.used_points = book.used_points
            clone.final_order = list(book.final_order)
            clone.entries = list(book.entries)
            clone.next_cycle_budget = book.next_cycle_budget
            for beneficiary, bearer, reason in operations:
                clone.override(beneficiary, bearer, reason)
            if sorted(clone.final_order) != sorted(clone.algorithmic_order):
                raise ModelRed(RedCode.INVARIANT_BREACH, "quota", "override must be neutral")
            return clone

        def commit(plan: OverrideBook) -> None:
            book.used_points = plan.used_points
            book.final_order = plan.final_order
            book.entries = plan.entries

        return self.apply(347, token, action_serial, {"PILOTED"}, precheck, commit, next_state="EFFECTIVE")

    def bind_exception(
        self,
        token: CaseToken,
        action_serial: str,
        exception: PolicyException,
    ) -> MutationOutcome:
        def precheck() -> PolicyException:
            if exception.owner_id != self.owner.actor_id or exception.cycle_serial != self.identity.cycle_serial:
                raise ModelRed(RedCode.INVARIANT_BREACH, "exception", "owner/cycle mismatch")
            return exception

        return self.apply(
            348,
            token,
            action_serial,
            {"PILOTED"},
            precheck,
            lambda plan: self.data.__setitem__("exception", plan),
            next_state="EFFECTIVE",
        )

    def run_audit(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        case_risks: Mapping[str, int],
        sample_rate_percent: int,
        seed: int,
        transparency_credit: int = 0,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            if not case_risks:
                raise ModelRed(RedCode.INVALID_VALUE, "case_risks", "empty population")
            risks = {case_id: _int(f"risk.{case_id}", value, minimum=0, maximum=100) for case_id, value in case_risks.items()}
            rate = _int("sample_rate_percent", sample_rate_percent, minimum=1, maximum=100)
            credit = _int("transparency_credit", transparency_credit, minimum=0, maximum=90)
            effective_rate = max(1, rate - credit)
            sample_n = max(1, math.ceil(len(risks) * effective_rate / 100))
            ordered = sorted(risks, key=lambda key: (-risks[key], key))
            high_risk_n = min(max(1, sample_n // 2), len(ordered))
            selected = ordered[:high_risk_n]
            remainder = [key for key in ordered if key not in selected]
            rng = random.Random(_int("seed", seed))
            selected.extend(rng.sample(remainder, sample_n - len(selected)))
            findings = sum(1 for key in selected if risks[key] >= 70)
            clean = len(selected) - findings
            return {"population": tuple(sorted(risks)), "sample": tuple(selected), "seed": seed, "hours": len(selected) * 2, "findings": findings, "clean": clean, "closed": True, "settled": True}

        def commit(plan: dict[str, Any]) -> None:
            self.data["audit"] = plan
            self.trust_delta += plan["clean"]

        return self.apply(349, token, action_serial, {"EFFECTIVE"}, precheck, commit, next_state="AUDITED")

    def version_benchmark(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        old_version: str,
        new_version: str,
        effective_cycle: int,
        thresholds: Mapping[str, int],
        historical_records: Sequence[HistoricalRecord],
        explanation: str,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            old = _text("old_version", old_version)
            new = _text("new_version", new_version)
            if old == new:
                raise ModelRed(RedCode.INVALID_VALUE, "new_version", "must change")
            effective = _int("effective_cycle", effective_cycle, minimum=self.identity.cycle_serial + 1)
            frozen_thresholds = {key: _int(f"thresholds.{key}", value) for key, value in thresholds.items()}
            if not frozen_thresholds:
                raise ModelRed(RedCode.INVALID_VALUE, "thresholds", "empty")
            records = tuple(historical_records)
            snapshot = tuple((record.record_id, record.original_value, record.policy_version) for record in records)
            return {"old": old, "new": new, "effective_cycle": effective, "thresholds": frozen_thresholds, "explanation": _text("explanation", explanation), "history": snapshot}

        return self.apply(
            350,
            token,
            action_serial,
            {"EFFECTIVE"},
            precheck,
            lambda plan: self.data.__setitem__("benchmark", plan),
            next_state="AUDITED",
        )

    def measure_pilot(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        pilot_regions: Sequence[str],
        control_regions: Sequence[str],
        metrics: Sequence[str],
        outcomes: Mapping[str, Mapping[str, int]],
        end_cycle: int,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            pilots = _unique("pilot_regions", pilot_regions)
            controls = _unique("control_regions", control_regions)
            if set(pilots) & set(controls):
                raise ModelRed(RedCode.CONFLICT, "regions", "pilot and control must be disjoint")
            metric_ids = _unique("metrics", metrics)
            end = _int("end_cycle", end_cycle, minimum=self.identity.cycle_serial + 1)
            expected_regions = set(pilots) | set(controls)
            if set(outcomes) != expected_regions:
                raise ModelRed(RedCode.INVARIANT_BREACH, "outcomes", "all frozen regions required")
            normalized: dict[str, dict[str, int]] = {}
            for region, values in outcomes.items():
                if set(values) != set(metric_ids):
                    raise ModelRed(RedCode.INVARIANT_BREACH, "outcomes", "all preregistered metrics required")
                normalized[region] = {key: _int(f"outcome.{key}", value) for key, value in values.items()}
            differences = {
                metric: sum(normalized[region][metric] for region in pilots) / len(pilots)
                - sum(normalized[region][metric] for region in controls) / len(controls)
                for metric in metric_ids
            }
            return {"pilots": pilots, "controls": controls, "metrics": metric_ids, "outcomes": normalized, "differences": differences, "end_cycle": end}

        return self.apply(
            351,
            token,
            action_serial,
            {"AUDITED"},
            precheck,
            lambda plan: self.data.__setitem__("pilot", plan),
            next_state="MEASURED",
        )

    def map_history(
        self,
        token: CaseToken,
        action_serial: str,
        records: Sequence[HistoricalRecord],
        *,
        mapping_version: str,
        multiplier: float | None,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            frozen = tuple(records)
            ids = _unique("record_ids", (record.record_id for record in frozen))
            version = _text("mapping_version", mapping_version)
            original = {record.record_id: (record.original_value, record.original_formula, record.policy_version) for record in frozen}
            if multiplier is None:
                mapped = {record.record_id: None for record in frozen}
                new_series = f"series:{version}"
            else:
                factor = _number("multiplier", multiplier, minimum=0)
                mapped = {record.record_id: record.original_value * factor for record in frozen}
                new_series = None
            return {"ids": ids, "original": original, "mapped": mapped, "mapping_version": version, "new_series": new_series}

        return self.apply(
            352,
            token,
            action_serial,
            {"AUDITED"},
            precheck,
            lambda plan: self.data.__setitem__("history_mapping", plan),
            next_state="MEASURED",
        )

    def charge_admin_capacity(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        available_hours: int,
        form_hours: int,
        meeting_hours: int,
        appeal_hours: int,
        calibration_hours: int,
        interruption_hours: int,
        error_rate_delta: int,
        overturn_rate_delta: int,
    ) -> MutationOutcome:
        def precheck() -> dict[str, int]:
            capacity = _int("available_hours", available_hours, minimum=0)
            components = {
                "forms": _int("form_hours", form_hours, minimum=0),
                "meetings": _int("meeting_hours", meeting_hours, minimum=0),
                "appeals": _int("appeal_hours", appeal_hours, minimum=0),
                "calibration": _int("calibration_hours", calibration_hours, minimum=0),
                "interruptions": _int("interruption_hours", interruption_hours, minimum=0),
            }
            total = sum(components.values())
            if total > capacity:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "available_hours", "admin cost exceeds capacity")
            return {
                **components,
                "total": total,
                "delivery_capacity_lost": total,
                "remaining": capacity - total,
                "error_rate_delta": _int("error_rate_delta", error_rate_delta),
                "overturn_rate_delta": _int("overturn_rate_delta", overturn_rate_delta),
            }

        def commit(plan: dict[str, int]) -> None:
            self.data["admin_cost"] = plan
            self.manager_score_delta -= max(0, plan["error_rate_delta"] + plan["overturn_rate_delta"])

        return self.apply(353, token, action_serial, {"MEASURED"}, precheck, commit, next_state="MIGRATED")

    def audit_fairness_metrics(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        delivered_results: int,
        raw_appeals: int,
        raw_overturns: int,
        raw_exits: int,
        raw_healthy_exits: int,
        reported_appeal_rate: float,
        reported_overturn_rate: float,
        reported_healthy_exit_rate: float,
        self_disclosed: bool,
        remediation_completed: bool,
    ) -> MutationOutcome:
        def precheck() -> dict[str, Any]:
            if not isinstance(self_disclosed, bool) or not isinstance(remediation_completed, bool):
                raise ModelRed(
                    RedCode.INVALID_TYPE,
                    "self_disclosed/remediation_completed",
                    "must be bool",
                )
            delivered = _int("delivered_results", delivered_results, minimum=1)
            appeals = _int("raw_appeals", raw_appeals, minimum=0, maximum=delivered)
            overturns = _int("raw_overturns", raw_overturns, minimum=0, maximum=appeals)
            exits = _int("raw_exits", raw_exits, minimum=1)
            healthy = _int("raw_healthy_exits", raw_healthy_exits, minimum=0, maximum=exits)
            reported = (
                _number("reported_appeal_rate", reported_appeal_rate, minimum=0, maximum=1),
                _number("reported_overturn_rate", reported_overturn_rate, minimum=0, maximum=1),
                _number("reported_healthy_exit_rate", reported_healthy_exit_rate, minimum=0, maximum=1),
            )
            raw = (
                appeals / delivered,
                overturns / appeals if appeals else 0.0,
                healthy / exits,
            )
            gap = tuple(round(reported[index] - raw[index], 6) for index in range(3))
            gaming = any(abs(value) > 1e-9 for value in gap)
            trust = 5 if self_disclosed and remediation_completed else 0
            return {"reported": reported, "raw": raw, "gap": gap, "gaming": gaming, "self_disclosed": bool(self_disclosed), "remediation_completed": bool(remediation_completed), "trust": trust}

        def commit(plan: dict[str, Any]) -> None:
            self.data["fairness_audit"] = plan
            self.trust_delta += plan["trust"]

        return self.apply(354, token, action_serial, {"MEASURED"}, precheck, commit, next_state="MIGRATED")


def assert_model_contract() -> None:
    """Fail import-time-independent validation of exact owned scope and honesty."""

    if set(MECHANISM_TITLES) != EXPECTED_MECHANISM_IDS:
        raise ModelRed(RedCode.INVARIANT_BREACH, "MECHANISM_TITLES", "coverage drift")
    if set(MECHANISM_DOMAINS) != EXPECTED_MECHANISM_IDS:
        raise ModelRed(RedCode.INVARIANT_BREACH, "MECHANISM_DOMAINS", "coverage drift")
    if set(MECHANISM_OPERATIONS) != EXPECTED_MECHANISM_IDS:
        raise ModelRed(RedCode.INVARIANT_BREACH, "MECHANISM_OPERATIONS", "coverage drift")
    if len(set(MECHANISM_OPERATIONS.values())) != len(MECHANISM_OPERATIONS):
        raise ModelRed(RedCode.INVARIANT_BREACH, "MECHANISM_OPERATIONS", "operations must be explicit per ID")
    if READINESS != "python-l0-only" or CK3_IMPLEMENTED or MCP_EVIDENCE != "none":
        raise ModelRed(RedCode.INVARIANT_BREACH, "readiness", "L0 must not claim live evidence")


assert_model_contract()
