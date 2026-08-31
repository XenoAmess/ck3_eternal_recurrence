#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic semantic oracle for manager/governance mechanisms.

Owned business semantics: F032-036 and AK345-354.  Q121-128 remain owned by
the career/HC runtime; this model consumes their frozen receipts through a
read-only projection instead of creating a second manager case.

This is an L0 reference model.  It proves stable identities, A/B/C route
effects, idempotence, conservation, deadlines and audit consumers.  It does
not claim CK3 or MCP-live evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import hashlib
import math
import random
from typing import Any, Final, Iterable, Mapping, Sequence


READINESS: Final[str] = "python-l0-only"
MCP_EVIDENCE: Final[str] = "none"
OWNED_IDS: Final[tuple[int, ...]] = (*range(32, 37), *range(345, 355))
Q_PROJECTION_IDS: Final[tuple[int, ...]] = tuple(range(121, 129))
Q_EXPECTED_STATE: Final[dict[int, int]] = {
    121: 1, 122: 1, 123: 2, 124: 2, 125: 3, 126: 3, 127: 4, 128: 4,
}
Q_REQUIRED_FIELDS: Final[dict[int, frozenset[str]]] = {
    121: frozenset({"trial_team_size", "mentor_id", "skip_reviewer_id", "due_cycle", "outcome"}),
    122: frozenset({"result_score", "talent_score", "process_score", "weights", "final_score"}),
    123: frozenset({"sample_count", "six_dimensions", "credibility_total", "consensus"}),
    124: frozenset({"successor_id", "trial_due", "handover_status", "promotion_released", "liability_owner"}),
    125: frozenset({"incident_id", "budget", "manager_hours", "delegate_id", "delegate_hours", "outcome"}),
    126: frozenset({"performance_band", "values_band", "quadrant", "disposition"}),
    127: frozenset({"report_count", "span_limit", "delegate_count", "evidence_coverage", "distortion"}),
    128: frozenset({"pressure", "collaboration", "risk_reporting", "review_trust", "regretted_attrition", "effective_cycle"}),
}
TEAM_METRIC_NAMES: Final[tuple[str, ...]] = (
    "targets",
    "jingcha",
    "calibration",
    "pip_success",
    "appeal_overturn",
    "retention",
    "hc_efficiency",
)
ANNUAL_METRIC_NAMES: Final[tuple[str, ...]] = (
    "top",
    "middle",
    "bottom",
    "appeal_overturns",
    "pip_successes",
    "promotions",
    "exits",
    "bonus_in",
    "bonus_out",
    "hc_efficiency",
)
OFFICIAL_KPI_COMPONENT_NAMES: Final[tuple[str, ...]] = (
    "governance",
    "capability",
    "growth",
    "superior",
    "values",
    "collaboration",
    "jingcha",
    "organization",
)
ORGANIZATION_COMPONENT_INDEX: Final[int] = 7
GAME_RULE_DISTRIBUTION_MODES: Final[dict[str, str]] = {
    "zg361_ratio_strict": "strict",
    "zg361_ratio_relaxed": "relaxed",
    "zg361_ratio_off": "off",
}
RATIO_OVERRIDE_DISTRIBUTION_MODES: Final[dict[int, str]] = {
    10: "strict",
    5: "relaxed",
    0: "off",
}


class Choice(IntEnum):
    A = 1
    B = 2
    C = 3


class RedCode(str, Enum):
    INVALID = "invalid"
    STALE = "stale"
    INVARIANT = "invariant"
    RESOURCE = "resource"
    MISSING = "missing"
    PERMISSION = "permission"


class PendingInputKind(str, Enum):
    OFFCYCLE = "offcycle"
    OVERRIDE = "override"
    FAIRNESS = "fairness"


class ModelRed(ValueError):
    def __init__(self, code: RedCode, field_name: str, message: str) -> None:
        super().__init__(f"{code.value}:{field_name}:{message}")
        self.code = code
        self.field_name = field_name


@dataclass(frozen=True, order=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    state: int = 1
    revision: int = 1

    def __post_init__(self) -> None:
        if not self.owner_id or not self.subject_id:
            raise ModelRed(RedCode.INVALID, "identity", "owner and subject required")
        if self.owner_id == self.subject_id:
            raise ModelRed(RedCode.INVARIANT, "identity", "direct superior must own manager case")
        if self.cycle_serial < 1 or self.case_serial < 1 or self.state < 1 or self.revision < 1:
            raise ModelRed(RedCode.INVALID, "identity", "positive serials/state/revision required")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class BusinessObject:
    object_id: str
    mechanism_id: int
    route: Choice
    identity: CaseIdentity
    kind: str
    fields: tuple[tuple[str, Any], ...]
    content_hash: str

    def get(self, name: str) -> Any:
        return dict(self.fields)[name]


@dataclass(frozen=True)
class Outcome:
    applied: bool
    route: Choice
    business: BusinessObject | None
    policy_debt_created: bool = False
    duplicate: bool = False


@dataclass(frozen=True)
class PolicyDebtSettlement:
    """One next-cycle consumer receipt for a route-C governance debt."""

    mechanism_id: int
    source_identity: CaseIdentity
    due_cycle: int
    settled_cycle: int
    settled_by_owner_id: str
    remediation_code: str
    manager_score_delta: int


@dataclass(frozen=True)
class AuthoritativeManagerObject:
    """Career/HC-owned Q business object supplied to the read-only adapter."""

    object_id: str
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    state: int
    revision: int
    route: Choice


@dataclass(frozen=True)
class ManagerCertificationReceipt:
    mechanism_id: int
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    state: int
    revision: int
    route: Choice
    consumed: bool
    value: int
    fields: Mapping[str, Any]
    authoritative_object: AuthoritativeManagerObject | None = None


def _integer(name: str, value: Any, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelRed(RedCode.INVALID, name, "integer required")
    if minimum is not None and value < minimum:
        raise ModelRed(RedCode.INVALID, name, f"minimum {minimum}")
    if maximum is not None and value > maximum:
        raise ModelRed(RedCode.INVALID, name, f"maximum {maximum}")
    return value


def _number(name: str, value: Any, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelRed(RedCode.INVALID, name, "number required")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ModelRed(RedCode.INVALID, name, f"minimum {minimum}")
    if maximum is not None and result > maximum:
        raise ModelRed(RedCode.INVALID, name, f"maximum {maximum}")
    return result


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelRed(RedCode.INVALID, name, "non-empty text required")
    return value.strip()


def _unique(name: str, values: Iterable[str], *, minimum: int = 1) -> tuple[str, ...]:
    result = tuple(_text(name, value) for value in values)
    if len(result) < minimum or len(set(result)) != len(result):
        raise ModelRed(RedCode.INVARIANT, name, "unique values required")
    return result


@dataclass(frozen=True)
class PendingManagerOrganizationScore:
    """F032 score awaiting its one official component-8 consumer."""

    source_identity: CaseIdentity
    due_cycle: int
    score: int
    input_revision: int
    component_number: int = 8

    def __post_init__(self) -> None:
        _integer("due_cycle", self.due_cycle, minimum=self.source_identity.cycle_serial + 1)
        _integer("score", self.score)
        _integer("input_revision", self.input_revision, minimum=1)
        if self.component_number != ORGANIZATION_COMPONENT_INDEX + 1:
            raise ModelRed(RedCode.INVARIANT, "component_number", "manager score belongs to organization component 8")


@dataclass(frozen=True)
class ManagerOrganizationSettlement:
    source_identity: CaseIdentity
    due_cycle: int
    settled_cycle: int
    settled_by_owner_id: str
    input_revision: int
    score: int
    components_before: tuple[int, ...]
    components_after: tuple[int, ...]

    @property
    def official_kpi_before(self) -> int:
        return sum(self.components_before)

    @property
    def official_kpi_after(self) -> int:
        return sum(self.components_after)


@dataclass(frozen=True)
class OffcyclePendingInput:
    """Producer-owned material team signal for AK346."""

    source_identity: CaseIdentity
    input_revision: int
    signal_id: str
    signal_type: str
    materiality: int
    evidence_ids: tuple[str, ...]
    kind: PendingInputKind = field(default=PendingInputKind.OFFCYCLE, init=False)

    def __post_init__(self) -> None:
        _integer("input_revision", self.input_revision, minimum=1)
        _text("signal_id", self.signal_id)
        if _text("signal_type", self.signal_type) not in {"achievement", "misconduct", "goal-change"}:
            raise ModelRed(RedCode.INVALID, "signal_type", "known material signal type required")
        _integer("materiality", self.materiality, minimum=50, maximum=100)
        _unique("evidence_ids", self.evidence_ids)


@dataclass(frozen=True)
class OverridePendingInput:
    """Actual paired grade reasons awaiting the AK347 override book."""

    source_identity: CaseIdentity
    input_revision: int
    beneficiary_id: str
    bearer_id: str
    beneficiary_grade_reason: int
    bearer_grade_reason: int
    beneficiary_result_case: int
    bearer_result_case: int
    kind: PendingInputKind = field(default=PendingInputKind.OVERRIDE, init=False)

    def __post_init__(self) -> None:
        _integer("input_revision", self.input_revision, minimum=1)
        beneficiary = _text("beneficiary_id", self.beneficiary_id)
        bearer = _text("bearer_id", self.bearer_id)
        if beneficiary == bearer:
            raise ModelRed(RedCode.INVARIANT, "override_pair", "beneficiary and bearer must differ")
        if _integer("beneficiary_grade_reason", self.beneficiary_grade_reason) not in {2, 4}:
            raise ModelRed(RedCode.INVALID, "beneficiary_grade_reason", "actual lift/rescue result reason required")
        if _integer("bearer_grade_reason", self.bearer_grade_reason) not in {1, 3}:
            raise ModelRed(RedCode.INVALID, "bearer_grade_reason", "actual push result reason required")
        _integer("beneficiary_result_case", self.beneficiary_result_case, minimum=1)
        _integer("bearer_result_case", self.bearer_result_case, minimum=1)


@dataclass(frozen=True)
class FairnessPendingInput:
    """Actual frozen delivery/appeal/exit counters awaiting AK354."""

    source_identity: CaseIdentity
    input_revision: int
    delivered: int
    appeals: int
    overturns: int
    exits: int
    healthy_exits: int
    kind: PendingInputKind = field(default=PendingInputKind.FAIRNESS, init=False)

    def __post_init__(self) -> None:
        _integer("input_revision", self.input_revision, minimum=1)
        delivered = _integer("delivered", self.delivered, minimum=0)
        appeals = _integer("appeals", self.appeals, minimum=0, maximum=delivered)
        _integer("overturns", self.overturns, minimum=0, maximum=appeals)
        exits = _integer("exits", self.exits, minimum=0)
        _integer("healthy_exits", self.healthy_exits, minimum=0, maximum=exits)


GovernancePendingInput = OffcyclePendingInput | OverridePendingInput | FairnessPendingInput
PENDING_INPUT_CONSUMERS: Final[dict[PendingInputKind, int]] = {
    PendingInputKind.OFFCYCLE: 346,
    PendingInputKind.OVERRIDE: 347,
    PendingInputKind.FAIRNESS: 354,
}


@dataclass(frozen=True)
class PendingInputConsumptionReceipt:
    kind: PendingInputKind
    source_identity: CaseIdentity
    input_revision: int
    consumer_identity: CaseIdentity
    consumer_mechanism_id: int
    payload_hash: str


def _distribution_snapshot(
    *,
    mode: str,
    cohort: int,
    rule_source: str,
    producer_value: int | str,
    review_serial: int,
) -> dict[str, Any]:
    """Freeze the actual three-mode quota inputs used by the rank consumer."""

    if mode not in {"strict", "relaxed", "off"}:
        raise ModelRed(RedCode.INVALID, "mode", "strict/relaxed/off required")
    size = _integer("cohort", cohort, minimum=0)
    source = _text("rule_source", rule_source)
    serial = _integer("review_serial", review_serial, minimum=1)
    top = 0 if size == 0 else min(size, max(1, math.floor(size * 0.30 + 0.5)))
    bottom = math.floor(size * {"strict": 0.10, "relaxed": 0.05, "off": 0.0}[mode])
    if size >= 5 and mode == "strict":
        bottom = max(1, bottom)
    bottom = min(bottom, max(0, size - top))
    middle = size - top - bottom
    frozen = {
        "mode": mode,
        "rule_source": source,
        "producer_value": producer_value,
        "review_serial": serial,
        "cohort": size,
        "top": top,
        "middle": middle,
        "bottom": bottom,
        "bottom_consequence": "none" if mode == "off" else "normal",
    }
    frozen["snapshot_hash"] = hashlib.sha256(repr(_freeze(frozen)).encode("utf-8")).hexdigest()
    return frozen


def compute_distribution_snapshot(
    *,
    ratio_override: int | None,
    game_rule: str,
    cohort: int,
    review_serial: int,
) -> dict[str, Any]:
    """Freeze the real producer precedence: liege override, then game rule."""

    if ratio_override is not None:
        override = _integer("ratio_override", ratio_override)
        if override not in RATIO_OVERRIDE_DISTRIBUTION_MODES:
            raise ModelRed(RedCode.INVALID, "ratio_override", "actual override must be 10/5/0")
        return _distribution_snapshot(
            mode=RATIO_OVERRIDE_DISTRIBUTION_MODES[override],
            cohort=cohort,
            rule_source="liege-override",
            producer_value=override,
            review_serial=review_serial,
        )
    rule = _text("game_rule", game_rule)
    if rule not in GAME_RULE_DISTRIBUTION_MODES:
        raise ModelRed(RedCode.INVALID, "game_rule", "actual strict/relaxed/off game rule required")
    return _distribution_snapshot(
        mode=GAME_RULE_DISTRIBUTION_MODES[rule],
        cohort=cohort,
        rule_source="game-rule",
        producer_value=rule,
        review_serial=review_serial,
    )


@dataclass
class GovernanceLedger:
    """Stable append-only manager/governance ledger."""

    records: dict[tuple[int, CaseIdentity], BusinessObject] = field(default_factory=dict)
    routes: dict[tuple[int, CaseIdentity], Choice] = field(default_factory=dict)
    operation_fingerprints: dict[tuple[int, CaseIdentity], str] = field(default_factory=dict)
    policy_debts: dict[tuple[int, CaseIdentity], int] = field(default_factory=dict)
    policy_debt_settlements: dict[tuple[int, CaseIdentity], PolicyDebtSettlement] = field(default_factory=dict)
    latest_cases: dict[tuple[int, str], CaseIdentity] = field(default_factory=dict)
    manager_score_adjustments: dict[str, int] = field(default_factory=dict)
    manager_scores: dict[CaseIdentity, int] = field(default_factory=dict)
    manager_organization_pending: dict[CaseIdentity, PendingManagerOrganizationScore] = field(default_factory=dict)
    manager_organization_settlements: dict[CaseIdentity, ManagerOrganizationSettlement] = field(default_factory=dict)
    pending_inputs: dict[tuple[PendingInputKind, CaseIdentity, int], GovernancePendingInput] = field(default_factory=dict)
    pending_input_receipts: dict[tuple[PendingInputKind, CaseIdentity, int], PendingInputConsumptionReceipt] = field(default_factory=dict)
    signal_ids: set[str] = field(default_factory=set)
    jingcha_consumed: set[tuple[str, int]] = field(default_factory=set)
    q_projections: dict[tuple[int, str, str, int, int, int], tuple[tuple[str, Any], ...]] = field(default_factory=dict)
    q_projection_heads: dict[tuple[int, str], tuple[str, int, int, int]] = field(default_factory=dict)

    def apply(self, mechanism_id: int, route: Choice | int, identity: CaseIdentity, **facts: Any) -> Outcome:
        if mechanism_id not in OWNED_IDS:
            raise ModelRed(RedCode.INVALID, "mechanism_id", "outside owned manager/governance slice")
        try:
            selected = Choice(route)
        except (TypeError, ValueError) as exc:
            raise ModelRed(RedCode.INVALID, "route", "A/B/C required") from exc
        key = (mechanism_id, identity)
        fingerprint_payload = (int(selected), ()) if selected is Choice.C else (int(selected), facts)
        operation_fingerprint = hashlib.sha256(
            repr(_freeze(fingerprint_payload)).encode("utf-8")
        ).hexdigest()
        head_key = (mechanism_id, identity.subject_id)
        latest = self.latest_cases.get(head_key)
        if latest is not None and (
            identity.cycle_serial,
            identity.case_serial,
            identity.state,
            identity.revision,
        ) == (
            latest.cycle_serial,
            latest.case_serial,
            latest.state,
            latest.revision,
        ) and identity.owner_id != latest.owner_id:
            raise ModelRed(RedCode.PERMISSION, "owner_id", "same case token cannot change owner")
        if latest is not None and (
            identity.cycle_serial,
            identity.case_serial,
            identity.state,
            identity.revision,
        ) < (
            latest.cycle_serial,
            latest.case_serial,
            latest.state,
            latest.revision,
        ):
            raise ModelRed(RedCode.STALE, "identity", "older case token cannot mutate successor state")
        if key in self.routes:
            if (
                self.routes[key] is not selected
                or self.operation_fingerprints.get(key) != operation_fingerprint
            ):
                raise ModelRed(
                    RedCode.STALE,
                    "duplicate",
                    "same case identity cannot change route or frozen inputs",
                )
            return Outcome(False, self.routes[key], self.records.get(key), duplicate=True)

        # C is deliberately a no-business-object route.  It records one visible
        # governance debt and a frozen next-review deadline, then becomes
        # idempotent under the same five-tuple.
        if selected is Choice.C:
            self.routes[key] = selected
            self.operation_fingerprints[key] = operation_fingerprint
            self.policy_debts[key] = identity.cycle_serial + 1
            self.latest_cases[head_key] = identity
            return Outcome(True, selected, None, policy_debt_created=True)

        builder = getattr(self, f"_m{mechanism_id:03d}")
        kind, fields = builder(selected, identity, facts)
        object_id = self._object_id(mechanism_id, identity)
        content_hash = hashlib.sha256(repr(_freeze(fields)).encode("utf-8")).hexdigest()
        business = BusinessObject(
            object_id,
            mechanism_id,
            selected,
            identity,
            kind,
            tuple(sorted((name, _freeze(value)) for name, value in fields.items())),
            content_hash,
        )
        self.routes[key] = selected
        self.operation_fingerprints[key] = operation_fingerprint
        self.records[key] = business
        self.latest_cases[head_key] = identity
        if mechanism_id == 32:
            self.manager_scores[identity] = int(fields["score"])
            self.manager_score_adjustments[identity.subject_id] = 0
            self.manager_organization_pending[identity] = PendingManagerOrganizationScore(
                source_identity=identity,
                due_cycle=identity.cycle_serial + 1,
                score=int(fields["score"]),
                input_revision=identity.revision,
            )
        if mechanism_id == 346:
            self.signal_ids.add(str(fields["signal_id"]))
        return Outcome(True, selected, business)

    @staticmethod
    def _object_id(mechanism_id: int, identity: CaseIdentity) -> str:
        payload = repr(
            (
                mechanism_id,
                identity.owner_id,
                identity.subject_id,
                identity.cycle_serial,
                identity.case_serial,
            )
        ).encode("utf-8")
        return f"mg-{mechanism_id:03d}-{hashlib.sha256(payload).hexdigest()[:16]}"

    def consume_policy_debt(
        self,
        mechanism_id: int,
        source_identity: CaseIdentity,
        *,
        current_cycle: int,
        settled_by_owner_id: str,
        current_direct_liege_id: str,
        remediation_code: str,
    ) -> PolicyDebtSettlement | None:
        """Settle an exact route-C debt once, no earlier than its frozen due cycle.

        The source owner remains part of the immutable debt identity even when a
        later direct superior performs the settlement.  This prevents a liege
        change from silently rewriting who owned the deferred decision.
        """

        if mechanism_id not in OWNED_IDS:
            raise ModelRed(RedCode.INVALID, "mechanism_id", "outside owned manager/governance slice")
        key = (mechanism_id, source_identity)
        due_cycle = self.policy_debts.get(key)
        if due_cycle is None:
            raise ModelRed(RedCode.MISSING, "policy_debt", "exact route-C debt does not exist")
        settled_cycle = _integer("current_cycle", current_cycle, minimum=1)
        if settled_cycle < due_cycle:
            raise ModelRed(RedCode.STALE, "current_cycle", "policy debt is not due")
        settlement_owner = _text("settled_by_owner_id", settled_by_owner_id)
        if settlement_owner != _text("current_direct_liege_id", current_direct_liege_id):
            raise ModelRed(RedCode.PERMISSION, "settled_by_owner_id", "current direct superior must settle debt")
        if settlement_owner == source_identity.subject_id:
            raise ModelRed(RedCode.INVARIANT, "settled_by_owner_id", "manager cannot settle own policy debt")
        settlement = PolicyDebtSettlement(
            mechanism_id=mechanism_id,
            source_identity=source_identity,
            due_cycle=due_cycle,
            settled_cycle=settled_cycle,
            settled_by_owner_id=settlement_owner,
            remediation_code=_text("remediation_code", remediation_code),
            manager_score_delta=-3,
        )
        prior = self.policy_debt_settlements.get(key)
        if prior is not None:
            if prior == settlement:
                return None
            raise ModelRed(RedCode.STALE, "settlement", "settled debt cannot be rewritten")
        self.policy_debt_settlements[key] = settlement
        self.manager_score_adjustments[source_identity.subject_id] = (
            self.manager_score_adjustments.get(source_identity.subject_id, 0)
            + settlement.manager_score_delta
        )
        return settlement

    def consume_manager_organization_score(
        self,
        source_identity: CaseIdentity,
        *,
        current_cycle: int,
        settled_by_owner_id: str,
        current_direct_liege_id: str,
        official_components: Sequence[int],
    ) -> ManagerOrganizationSettlement | None:
        """Settle F032 once into organization, preserving exactly eight KPI components."""

        components = tuple(_integer("official_component", value) for value in official_components)
        if len(components) != len(OFFICIAL_KPI_COMPONENT_NAMES):
            raise ModelRed(RedCode.INVARIANT, "official_components", "official KPI must contain exactly eight components")
        cycle = _integer("current_cycle", current_cycle, minimum=1)
        settlement_owner = _text("settled_by_owner_id", settled_by_owner_id)
        if settlement_owner != _text("current_direct_liege_id", current_direct_liege_id):
            raise ModelRed(RedCode.PERMISSION, "settled_by_owner_id", "current direct superior must settle manager score")
        if settlement_owner == source_identity.subject_id:
            raise ModelRed(RedCode.INVARIANT, "settled_by_owner_id", "manager cannot settle own organization evidence")
        prior = self.manager_organization_settlements.get(source_identity)
        if prior is not None:
            if (
                cycle == prior.settled_cycle
                and settlement_owner == prior.settled_by_owner_id
                and components == prior.components_before
            ):
                return None
            raise ModelRed(RedCode.STALE, "manager_score_settlement", "settled organization evidence cannot be rewritten")
        pending = self.manager_organization_pending.get(source_identity)
        if pending is None:
            raise ModelRed(RedCode.MISSING, "manager_score_pending", "exact F032 score does not exist")
        if cycle < pending.due_cycle:
            raise ModelRed(RedCode.STALE, "current_cycle", "manager score is not due until next cycle")
        updated = list(components)
        updated[ORGANIZATION_COMPONENT_INDEX] += pending.score
        settlement = ManagerOrganizationSettlement(
            source_identity=source_identity,
            due_cycle=pending.due_cycle,
            settled_cycle=cycle,
            settled_by_owner_id=settlement_owner,
            input_revision=pending.input_revision,
            score=pending.score,
            components_before=components,
            components_after=tuple(updated),
        )
        self.manager_organization_settlements[source_identity] = settlement
        del self.manager_organization_pending[source_identity]
        return settlement

    @staticmethod
    def _pending_input_key(pending: GovernancePendingInput) -> tuple[PendingInputKind, CaseIdentity, int]:
        return pending.kind, pending.source_identity, pending.input_revision

    @staticmethod
    def _pending_input_hash(pending: GovernancePendingInput) -> str:
        return hashlib.sha256(repr(pending).encode("utf-8")).hexdigest()

    def publish_pending_input(self, pending: GovernancePendingInput) -> bool:
        """Publish one producer-owned typed input revision without fabricating defaults."""

        if not isinstance(pending, (OffcyclePendingInput, OverridePendingInput, FairnessPendingInput)):
            raise ModelRed(RedCode.INVALID, "pending", "typed offcycle/override/fairness input required")
        key = self._pending_input_key(pending)
        prior_receipt = self.pending_input_receipts.get(key)
        if prior_receipt is not None:
            if prior_receipt.payload_hash == self._pending_input_hash(pending):
                return False
            raise ModelRed(RedCode.STALE, "pending", "consumed input revision cannot be rewritten")
        prior = self.pending_inputs.get(key)
        if prior is not None:
            if prior == pending:
                return False
            raise ModelRed(RedCode.STALE, "pending", "published input revision cannot be rewritten")
        self.pending_inputs[key] = pending
        return True

    def consume_pending_input(
        self,
        pending: GovernancePendingInput,
        *,
        consumer_mechanism_id: int,
        consumer_identity: CaseIdentity,
    ) -> PendingInputConsumptionReceipt | None:
        """Consume an exact typed producer revision once and leave an immutable receipt."""

        if not isinstance(pending, (OffcyclePendingInput, OverridePendingInput, FairnessPendingInput)):
            raise ModelRed(RedCode.INVALID, "pending", "typed offcycle/override/fairness input required")
        expected_consumer = PENDING_INPUT_CONSUMERS[pending.kind]
        if consumer_mechanism_id != expected_consumer:
            raise ModelRed(RedCode.INVARIANT, "consumer_mechanism_id", f"{pending.kind.value} input belongs to {expected_consumer}")
        if consumer_identity.subject_id != pending.source_identity.subject_id:
            raise ModelRed(RedCode.INVARIANT, "consumer_identity", "producer and consumer subjects must match")
        if consumer_identity.cycle_serial < pending.source_identity.cycle_serial:
            raise ModelRed(RedCode.STALE, "consumer_identity", "consumer cannot predate its producer")
        key = self._pending_input_key(pending)
        payload_hash = self._pending_input_hash(pending)
        receipt = PendingInputConsumptionReceipt(
            kind=pending.kind,
            source_identity=pending.source_identity,
            input_revision=pending.input_revision,
            consumer_identity=consumer_identity,
            consumer_mechanism_id=consumer_mechanism_id,
            payload_hash=payload_hash,
        )
        prior_receipt = self.pending_input_receipts.get(key)
        if prior_receipt is not None:
            if prior_receipt == receipt:
                return None
            raise ModelRed(RedCode.STALE, "pending_receipt", "consumed input cannot be settled twice")
        published = self.pending_inputs.get(key)
        if published is None:
            raise ModelRed(RedCode.MISSING, "pending", "exact input revision was not published")
        if published != pending:
            raise ModelRed(RedCode.STALE, "pending", "consumer payload differs from producer revision")
        self.pending_input_receipts[key] = receipt
        del self.pending_inputs[key]
        return receipt

    def project_manager_certification(self, receipt: ManagerCertificationReceipt) -> bool:
        """Consume a Q121-128 receipt without owning or mutating its case."""

        if receipt.mechanism_id not in Q_PROJECTION_IDS:
            raise ModelRed(RedCode.INVALID, "mechanism_id", "Q121-128 receipt required")
        if not receipt.consumed:
            raise ModelRed(RedCode.MISSING, "consumed", "career/HC consumer must settle first")
        if (
            receipt.owner_id == receipt.subject_id
            or receipt.cycle_serial < 1
            or receipt.case_serial < 1
            or receipt.state < 1
            or receipt.revision < 1
        ):
            raise ModelRed(RedCode.INVARIANT, "identity", "invalid career receipt identity")
        if receipt.state != Q_EXPECTED_STATE[receipt.mechanism_id]:
            raise ModelRed(RedCode.STALE, "state", "career receipt is from the wrong stage")
        try:
            route = Choice(receipt.route)
        except (TypeError, ValueError) as exc:
            raise ModelRed(RedCode.INVALID, "route", "career receipt route must be A/B/C") from exc
        expected_value = {Choice.A: 1, Choice.B: -1, Choice.C: 0}[route]
        if receipt.value != expected_value:
            raise ModelRed(RedCode.INVARIANT, "value", "career receipt value must match frozen route")
        expected_fields = frozenset({"policy_debt_due"}) if route is Choice.C else Q_REQUIRED_FIELDS[receipt.mechanism_id]
        if frozenset(receipt.fields) != expected_fields:
            raise ModelRed(RedCode.INVARIANT, "fields", "receipt must match the per-ID projection schema exactly")
        authoritative = receipt.authoritative_object
        if route is Choice.C:
            if authoritative is not None:
                raise ModelRed(RedCode.INVARIANT, "authoritative_object", "route C must not fabricate a Q business object")
        else:
            if not isinstance(authoritative, AuthoritativeManagerObject):
                raise ModelRed(RedCode.MISSING, "authoritative_object", "A/B projection requires the Career/HC object")
            try:
                object_route = Choice(authoritative.route)
            except (TypeError, ValueError) as exc:
                raise ModelRed(RedCode.INVALID, "authoritative_object.route", "A/B object route required") from exc
            object_identity = (
                _text("authoritative_object.object_id", authoritative.object_id),
                _text("authoritative_object.owner_id", authoritative.owner_id),
                _text("authoritative_object.subject_id", authoritative.subject_id),
                _integer("authoritative_object.cycle_serial", authoritative.cycle_serial, minimum=1),
                _integer("authoritative_object.case_serial", authoritative.case_serial, minimum=1),
                _integer("authoritative_object.state", authoritative.state, minimum=1),
                _integer("authoritative_object.revision", authoritative.revision, minimum=1),
                object_route,
            )
            expected_object_identity = (
                authoritative.object_id,
                receipt.owner_id,
                receipt.subject_id,
                receipt.cycle_serial,
                receipt.case_serial,
                receipt.state,
                receipt.revision,
                route,
            )
            if object_identity != expected_object_identity:
                raise ModelRed(
                    RedCode.STALE,
                    "authoritative_object",
                    "Career/HC object identity must exactly match its receipt",
                )
        self._validate_q_projection(receipt, route)
        key = (
            receipt.mechanism_id,
            receipt.owner_id,
            receipt.subject_id,
            receipt.cycle_serial,
            receipt.case_serial,
            receipt.state,
        )
        fields = {
            "owner_id": receipt.owner_id,
            "subject_id": receipt.subject_id,
            "state": receipt.state,
            "revision": receipt.revision,
            "route": int(route),
            "value": _integer("value", receipt.value),
            "source": "career-hc-authoritative",
            "authoritative_object_present": authoritative is not None,
            **dict(receipt.fields),
        }
        if authoritative is not None:
            fields["authoritative_object"] = (
                authoritative.object_id,
                authoritative.owner_id,
                authoritative.subject_id,
                authoritative.cycle_serial,
                authoritative.case_serial,
                authoritative.state,
                authoritative.revision,
                int(authoritative.route),
            )
        frozen_fields = tuple(sorted((name, _freeze(value)) for name, value in fields.items()))
        if route is Choice.C:
            due = _integer("policy_debt_due", receipt.fields["policy_debt_due"], minimum=1)
            if due != receipt.cycle_serial + 1:
                raise ModelRed(RedCode.INVARIANT, "policy_debt_due", "career debt is due next cycle")
        head_key = (receipt.mechanism_id, receipt.subject_id)
        head = self.q_projection_heads.get(head_key)
        incoming_order = (receipt.cycle_serial, receipt.case_serial, receipt.state)
        if head is not None:
            head_owner, head_cycle, head_case, head_state = head
            head_order = (head_cycle, head_case, head_state)
            if incoming_order < head_order:
                raise ModelRed(RedCode.STALE, "projection", "older career receipt cannot replace successor")
            if incoming_order == head_order and receipt.owner_id != head_owner:
                raise ModelRed(RedCode.PERMISSION, "owner_id", "same career case token cannot change owner")
        if key in self.q_projections:
            if self.q_projections[key] != frozen_fields:
                raise ModelRed(RedCode.STALE, "projection", "same authoritative receipt identity changed")
            return False
        self.q_projections[key] = frozen_fields
        self.q_projection_heads[head_key] = (
            receipt.owner_id,
            receipt.cycle_serial,
            receipt.case_serial,
            receipt.state,
        )
        return True

    @staticmethod
    def _validate_q_projection(receipt: ManagerCertificationReceipt, route: Choice) -> None:
        fields = receipt.fields
        if route is Choice.C:
            due = _integer("policy_debt_due", fields["policy_debt_due"], minimum=1)
            if due != receipt.cycle_serial + 1:
                raise ModelRed(RedCode.INVARIANT, "policy_debt_due", "career debt is due next cycle")
            return
        mechanism_id = receipt.mechanism_id
        if mechanism_id == 121:
            if _integer("trial_team_size", fields["trial_team_size"], minimum=1) != 3:
                raise ModelRed(RedCode.INVARIANT, "trial_team_size", "manager trial uses exactly three reports")
            mentor = _text("mentor_id", fields["mentor_id"])
            skip = _text("skip_reviewer_id", fields["skip_reviewer_id"])
            if len({mentor, skip, receipt.subject_id}) != 3:
                raise ModelRed(RedCode.INVARIANT, "reviewers", "mentor, skip reviewer and manager must be distinct")
            if _integer("due_cycle", fields["due_cycle"], minimum=1) != receipt.cycle_serial + 1:
                raise ModelRed(RedCode.INVARIANT, "due_cycle", "trial closes next cycle")
            if _text("outcome", fields["outcome"]) not in {"passed", "failed", "pending"}:
                raise ModelRed(RedCode.INVALID, "outcome", "known trial outcome required")
        elif mechanism_id == 122:
            result = _integer("result_score", fields["result_score"], minimum=0, maximum=100)
            talent = _integer("talent_score", fields["talent_score"], minimum=0, maximum=100)
            process = _integer("process_score", fields["process_score"], minimum=0, maximum=100)
            weights = tuple(_integer("weight", value, minimum=0, maximum=100) for value in fields["weights"])
            if weights != (40, 30, 30):
                raise ModelRed(RedCode.INVARIANT, "weights", "manager score uses frozen 40/30/30 weights")
            expected = round((result * weights[0] + talent * weights[1] + process * weights[2]) / 100)
            if _integer("final_score", fields["final_score"], minimum=0, maximum=100) != expected:
                raise ModelRed(RedCode.INVARIANT, "final_score", "4-3-3 score must be reproducible")
        elif mechanism_id == 123:
            sample = _integer("sample_count", fields["sample_count"], minimum=1)
            dimensions = tuple(_integer("dimension", value, minimum=0, maximum=100) for value in fields["six_dimensions"])
            if len(dimensions) != 6:
                raise ModelRed(RedCode.INVARIANT, "six_dimensions", "exactly six dimensions required")
            credibility = _integer("credibility_total", fields["credibility_total"], minimum=0, maximum=sample * 100)
            if credibility == 0 or _text("consensus", fields["consensus"]) not in {"positive", "mixed", "negative"}:
                raise ModelRed(RedCode.INVALID, "survey", "credible bounded consensus required")
        elif mechanism_id == 124:
            successor = _text("successor_id", fields["successor_id"])
            if successor == receipt.subject_id:
                raise ModelRed(RedCode.INVARIANT, "successor_id", "manager cannot be own successor")
            _integer("trial_due", fields["trial_due"], minimum=receipt.cycle_serial + 1)
            if _text("handover_status", fields["handover_status"]) not in {"pending", "accepted", "failed"}:
                raise ModelRed(RedCode.INVALID, "handover_status", "known handover state required")
            if not isinstance(fields["promotion_released"], bool):
                raise ModelRed(RedCode.INVALID, "promotion_released", "boolean required")
            if fields["handover_status"] != "accepted" and fields["promotion_released"]:
                raise ModelRed(RedCode.INVARIANT, "promotion_released", "promotion waits for accepted handover")
            _text("liability_owner", fields["liability_owner"])
        elif mechanism_id == 125:
            _text("incident_id", fields["incident_id"])
            budget = _integer("budget", fields["budget"], minimum=1)
            manager_hours = _integer("manager_hours", fields["manager_hours"], minimum=0, maximum=budget)
            delegate_hours = _integer("delegate_hours", fields["delegate_hours"], minimum=0, maximum=budget)
            if manager_hours + delegate_hours > budget:
                raise ModelRed(RedCode.INVARIANT, "hours", "crisis hours cannot exceed budget")
            if _text("delegate_id", fields["delegate_id"]) == receipt.subject_id:
                raise ModelRed(RedCode.INVARIANT, "delegate_id", "delegate must be distinct")
            _text("outcome", fields["outcome"])
        elif mechanism_id == 126:
            performance = _text("performance_band", fields["performance_band"])
            values = _text("values_band", fields["values_band"])
            if performance not in {"high", "low"} or values not in {"high", "low"}:
                raise ModelRed(RedCode.INVALID, "band", "four-quadrant high/low bands required")
            if _text("quadrant", fields["quadrant"]) != f"{performance}-{values}":
                raise ModelRed(RedCode.INVARIANT, "quadrant", "quadrant must derive from frozen bands")
            _text("disposition", fields["disposition"])
        elif mechanism_id == 127:
            reports = _integer("report_count", fields["report_count"], minimum=0)
            limit = _integer("span_limit", fields["span_limit"], minimum=1)
            delegates = _integer("delegate_count", fields["delegate_count"], minimum=0, maximum=reports)
            coverage = _integer("evidence_coverage", fields["evidence_coverage"], minimum=0, maximum=100)
            if not isinstance(fields["distortion"], bool):
                raise ModelRed(RedCode.INVALID, "distortion", "boolean required")
            expected_distortion = coverage < 100 or (reports > limit and delegates < reports - limit)
            if fields["distortion"] is not expected_distortion:
                raise ModelRed(RedCode.INVARIANT, "distortion", "distortion must derive from span and evidence coverage")
        elif mechanism_id == 128:
            for name in ("pressure", "collaboration", "risk_reporting", "review_trust"):
                _integer(name, fields[name], minimum=0, maximum=100)
            _integer("regretted_attrition", fields["regretted_attrition"], minimum=0)
            if _integer("effective_cycle", fields["effective_cycle"], minimum=1) != receipt.cycle_serial + 1:
                raise ModelRed(RedCode.INVARIANT, "effective_cycle", "climate policy starts next cycle")

    def _m032(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        source = _integer("source_team_serial", facts.get("source_team_serial"), minimum=1)
        if source >= identity.cycle_serial:
            raise ModelRed(RedCode.STALE, "source_team_serial", "must be strictly prior")
        snapshot_id = _text("snapshot_id", facts.get("snapshot_id"))
        if _text("direct_liege_id", facts.get("direct_liege_id")) != identity.owner_id:
            raise ModelRed(RedCode.PERMISSION, "direct_liege_id", "direct superior must own manager review")
        raw_metrics = facts.get("metrics")
        if not isinstance(raw_metrics, Mapping) or set(raw_metrics) != set(TEAM_METRIC_NAMES):
            raise ModelRed(RedCode.MISSING, "metrics", "exactly seven named frozen aggregates required")
        metrics = {name: _integer(name, raw_metrics[name]) for name in TEAM_METRIC_NAMES}
        if facts.get("grandchild_ids"):
            raise ModelRed(RedCode.INVARIANT, "grandchild_ids", "only aggregate team facts may cross the level")
        refusal = 0
        mandate_year = facts.get("mandate_year")
        saved_superior = facts.get("saved_superior")
        refusal_key = (identity.subject_id, _integer("mandate_year", mandate_year, minimum=1)) if mandate_year is not None else None
        if saved_superior == identity.owner_id and refusal_key is not None and refusal_key not in self.jingcha_consumed:
            refusal = -50
            self.jingcha_consumed.add(refusal_key)
        if route is Choice.A:
            components = metrics
            score = sum(metrics.values()) + refusal
            mode = "seven-factor"
        else:
            # B may be punitive, but still consumes only frozen aggregates.
            components = {
                name: value * (2 if name in {"targets", "jingcha", "appeal_overturn", "retention"} and value < 0 else 1)
                for name, value in metrics.items()
            }
            score = sum(components.values()) + refusal
            mode = "aggregate-punitive"
        debt_delta = self.manager_score_adjustments.get(identity.subject_id, 0)
        score += debt_delta
        return "manager-review", {
            "snapshot_id": snapshot_id,
            "source_team_serial": source,
            "current_serial": identity.cycle_serial,
            "components": components,
            "score": score,
            "jingcha_delta": refusal,
            "mode": mode,
            "policy_debt_delta": debt_delta,
            "grandchild_id_count": 0,
        }

    def _m033(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        profile = _text("profile", facts.get("profile"))
        profile_weights = {
            "data": {"calibration": 100, "appeal": 100, "pip": 90, "delivery": 120, "hc": 90},
            "delivery": {"calibration": 80, "appeal": 80, "pip": 100, "delivery": 140, "hc": 100},
            "political": {"calibration": 110, "appeal": 130, "pip": 80, "delivery": 90, "hc": 90},
            "talent": {"calibration": 90, "appeal": 100, "pip": 130, "delivery": 80, "hc": 120},
            "compliance": {"calibration": 140, "appeal": 120, "pip": 90, "delivery": 80, "hc": 70},
        }
        if profile not in profile_weights:
            raise ModelRed(RedCode.INVALID, "profile", "known stable manager profile required")
        version = _integer("weight_version", facts.get("weight_version"), minimum=1)
        raw = facts.get("reason_inputs")
        if not isinstance(raw, Mapping) or set(raw) != {"calibration", "appeal", "pip", "delivery", "hc"}:
            raise ModelRed(RedCode.MISSING, "reason_inputs", "five named inputs required")
        triggers = {name: _integer(name, value) for name, value in raw.items()}
        reasons = {
            name: max(-25, min(25, round(value * profile_weights[profile][name] / 100)))
            for name, value in triggers.items()
        }
        override = 0
        appeal_risk = 0
        before = _integer("before", facts.get("before", 2), minimum=1, maximum=3)
        after = before
        if route is Choice.B:
            override = max(-1, min(1, _integer("relationship_override", facts.get("relationship_override", 0))))
            after = max(1, min(3, before + override))
            appeal_risk = 10 if override else 0
        return "manager-profile", {
            "profile": profile,
            "weight_version": version,
            "reason_codes": reasons,
            "trigger_facts": triggers,
            "profile_weights": profile_weights[profile],
            "reason_total": sum(reasons.values()),
            "hard_evidence_cap": 25,
            "before_band": before,
            "after_band": after,
            "relationship_override": override,
            "appeal_risk": appeal_risk,
        }

    def _m034(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        history = tuple(_integer("history", value) for value in facts.get("history", ()))
        potential = _integer("potential", facts.get("potential"), minimum=0, maximum=100)
        if route is Choice.A:
            if not history:
                raise ModelRed(RedCode.MISSING, "history", "A requires the current frozen cycle")
            if len(history) == 1:
                return "nine-box-snapshot", {
                    "history": history,
                    "performance_axis": 0,
                    "potential_axis": 0,
                    "box": 0,
                    "recommendation": "unclassified",
                    "ready": False,
                    "status": "insufficient-frozen-history",
                    "expires_cycle": None,
                    "short_sight_risk": 0,
                    "grade_delta": 0,
                    "kpi_delta": 0,
                    "resource_delta": 0,
                }
            performance = round(sum(history) / len(history))
            expires = None
            risk = 0
        else:
            if len(history) != 1:
                raise ModelRed(RedCode.MISSING, "history", "B quick tag consumes current frozen cycle only")
            performance = history[0]
            expires = identity.cycle_serial + 1
            risk = 1
        p_axis = 1 if performance < 40 else 3 if performance >= 75 else 2
        q_axis = 1 if potential < 40 else 3 if potential >= 75 else 2
        recommendation = {
            (3, 3): "key-talent",
            (1, 3): "mentor-and-grow",
            (2, 2): "retain",
            (1, 2): "role-transfer",
        }.get((p_axis, q_axis), "develop-or-exit")
        return "nine-box-snapshot", {
            "history": history,
            "performance_axis": p_axis,
            "potential_axis": q_axis,
            "box": (p_axis - 1) * 3 + q_axis,
            "recommendation": recommendation,
            "ready": True,
            "status": "classified",
            "expires_cycle": expires,
            "short_sight_risk": risk,
            "grade_delta": 0,
            "kpi_delta": 0,
            "resource_delta": 0,
        }

    def _m035(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        cohort = _integer("cohort", facts.get("cohort"), minimum=0)
        if route is Choice.A:
            snapshot = compute_distribution_snapshot(
                ratio_override=facts.get("ratio_override"),
                game_rule=facts.get("game_rule"),
                cohort=cohort,
                review_serial=identity.cycle_serial,
            )
        else:
            snapshot = _distribution_snapshot(
                mode="strict",
                cohort=cohort,
                rule_source="mechanism-035-route-b",
                producer_value=10,
                review_serial=identity.cycle_serial,
            )
        if min(snapshot["top"], snapshot["middle"], snapshot["bottom"]) < 0 or snapshot["top"] + snapshot["middle"] + snapshot["bottom"] != cohort:
            raise ModelRed(RedCode.INVARIANT, "quota", "3/6/1 slots must conserve cohort")
        return "distribution-snapshot", {
            **snapshot,
            "frozen_cycle": identity.cycle_serial,
            "effective_cycle": identity.cycle_serial + 1,
        }

    def _m036(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        eligible = facts.get("government_eligible")
        if not isinstance(eligible, bool):
            raise ModelRed(RedCode.INVALID, "government_eligible", "boolean eligibility snapshot required")
        if not eligible:
            raise ModelRed(RedCode.PERMISSION, "government_eligible", "eligible celestial manager required")
        generated_day = _integer("generated_day", facts.get("generated_day"), minimum=0)
        logs = tuple(facts.get("logs", ()))
        if route is Choice.B:
            current = facts.get("current_snapshot")
            if not isinstance(current, Mapping) or not current:
                raise ModelRed(RedCode.MISSING, "current_snapshot", "B needs one frozen current snapshot")
            return "current-highlight", {
                "snapshot": dict(current),
                "generated_day": generated_day,
                "is_ten_year_report": False,
                "causal_warning": 1,
                "history_rows": 0,
            }
        if len(logs) != 10:
            raise ModelRed(RedCode.MISSING, "logs", "A requires exactly ten annual logs")
        expected_keys = {"owner_id", "year", "annual_id", *ANNUAL_METRIC_NAMES}
        if any(set(log) != expected_keys for log in logs):
            raise ModelRed(RedCode.INVARIANT, "logs", "exact annual metric schema required")
        owners = {str(log["owner_id"]) for log in logs}
        years = sorted(_integer("year", log["year"], minimum=1) for log in logs)
        if owners != {identity.owner_id} or len(set(years)) != 10 or years != list(range(years[0], years[0] + 10)):
            raise ModelRed(RedCode.INVARIANT, "logs", "one owner and ten consecutive unique years required")
        totals = {
            name: sum(_integer(name, log[name]) for log in logs)
            for name in ANNUAL_METRIC_NAMES
        }
        annual_ids = _unique("annual_id", (str(log["annual_id"]) for log in logs), minimum=10)
        return "ten-year-report", {
            "annual_ids": annual_ids,
            "start_year": years[0],
            "end_year": years[-1],
            "totals": totals,
            "averages": {name: totals[name] / 10 for name in ANNUAL_METRIC_NAMES},
            "bonus_net": totals.get("bonus_in", 0) - totals.get("bonus_out", 0),
            "generated_day": generated_day,
            "is_ten_year_report": True,
        }

    def _m345(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        effective = _integer("effective_cycle", facts.get("effective_cycle"), minimum=1)
        if effective != identity.cycle_serial + 1:
            raise ModelRed(RedCode.STALE, "effective_cycle", "calendar starts in exactly the next complete cycle")
        if route is Choice.A:
            return "policy-calendar", {
                "frequency": "annual",
                "review_days": (330,),
                "checkin_days": (180,),
                "review_instances": 1,
                "ai_batches": 1,
                "feedback_delay_days": 30,
                "admin_hours": 20,
                "event_interrupts": 2,
                "short_term_bias": 0,
                "fatigue": 0,
                "effective_cycle": effective,
            }
        return "policy-calendar", {
            "frequency": "quarterly",
            "review_days": (90, 180, 270, 360),
            "checkin_days": (),
            "review_instances": 4,
            "ai_batches": 4,
            "feedback_delay_days": 7,
            "admin_hours": 72,
            "event_interrupts": 8,
            "short_term_bias": 25,
            "fatigue": 30,
            "effective_cycle": effective,
        }

    def _m346(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        materiality = _integer("materiality", facts.get("materiality"), minimum=0, maximum=100)
        if materiality < 50:
            raise ModelRed(RedCode.INVALID, "materiality", "ordinary fluctuations create no object")
        signal_id = _text("signal_id", facts.get("signal_id"))
        if signal_id in self.signal_ids:
            raise ModelRed(RedCode.STALE, "signal_id", "material signal was already consumed by another case")
        if _text("official_id", facts.get("official_id")) != identity.subject_id:
            raise ModelRed(RedCode.INVARIANT, "official_id", "signal subject must match case subject")
        signal_type = _text("signal_type", facts.get("signal_type"))
        if signal_type not in {"achievement", "misconduct", "goal-change"}:
            raise ModelRed(RedCode.INVALID, "signal_type", "known material signal type required")
        evidence_ids = _unique("evidence_ids", facts.get("evidence_ids", ()))
        recorded_day = _integer("recorded_day", facts.get("recorded_day"), minimum=0)
        original_board_version = _text("original_board_version", facts.get("original_board_version"))
        action = _text("action", facts.get("action"))
        if action not in {"reward", "investigate", "adjust-goal"}:
            raise ModelRed(RedCode.INVALID, "action", "one bounded action required")
        return "offcycle-signal", {
            "signal_id": signal_id,
            "official_id": identity.subject_id,
            "signal_type": signal_type,
            "evidence_ids": evidence_ids,
            "recorded_day": recorded_day,
            "materiality": materiality,
            "action": action,
            "consumed_cycle": identity.cycle_serial + 1,
            "consumed_once": True,
            "cohort_reruns": 0 if route is Choice.A else 1,
            "original_board_preserved": True,
            "original_board_version": original_board_version,
            "rerank_version": None if route is Choice.A else f"{original_board_version}-rerank",
            "disruption": 0 if route is Choice.A else 20,
            "recency_bias": 0 if route is Choice.A else 15,
        }

    def _m347(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        order = _unique("algorithmic_order", facts.get("algorithmic_order", ()), minimum=2)
        operations = tuple(facts.get("operations", ()))
        budget = 2 if route is Choice.A else len(operations)
        if len(operations) > budget:
            raise ModelRed(RedCode.RESOURCE, "override_budget", "override budget exhausted")
        final = list(order)
        audit: list[tuple[str, str, str]] = []
        for beneficiary, bearer, reason in operations:
            beneficiary = _text("beneficiary", beneficiary)
            bearer = _text("bearer", bearer)
            reason = _text("reason", reason)
            if beneficiary == bearer or beneficiary not in final or bearer not in final:
                raise ModelRed(RedCode.INVARIANT, "override", "distinct ranked beneficiary/bearer required")
            left, right = final.index(beneficiary), final.index(bearer)
            final[left], final[right] = final[right], final[left]
            audit.append((beneficiary, bearer, reason))
        if sorted(final) != sorted(order):
            raise ModelRed(RedCode.INVARIANT, "quota", "override must conserve members")
        return "override-book", {
            "algorithmic_order": order,
            "final_order": tuple(final),
            "budget": budget,
            "used": len(operations),
            "audit": tuple(audit),
            "uncapped": route is Choice.B,
            "appeal_risk": len(operations) * 5 if route is Choice.B else 0,
            "next_budget": max(0, 2 - sum(1 for value in facts.get("overturned", ()) if value)),
        }

    def _m348(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        exception_id = _text("exception_id", facts.get("exception_id"))
        new_evidence = bool(facts.get("new_evidence", False))
        if route is Choice.B:
            return "policy-exception", {
                "exception_id": exception_id,
                "expiry_day": None,
                "grandfathered": True,
                "privilege_accumulation": 1,
                "fairness_risk": 10,
                "history_preserved": True,
            }
        granted = _integer("granted_day", facts.get("granted_day"), minimum=0)
        due = granted + 365
        resolved_day = _integer("resolved_day", facts.get("resolved_day"), minimum=due)
        return "policy-exception", {
            "exception_id": exception_id,
            "granted_day": granted,
            "expiry_day": resolved_day + 365 if new_evidence else due,
            "resolved_day": resolved_day,
            "renewed": new_evidence,
            "default_restored": not new_evidence,
            "jingcha_batch_id": _text("jingcha_batch_id", facts.get("jingcha_batch_id")),
            "history_preserved": True,
        }

    def _m349(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        risks_raw = facts.get("risks")
        if not isinstance(risks_raw, Mapping) or not risks_raw:
            raise ModelRed(RedCode.MISSING, "risks", "non-empty audit population required")
        risks = {str(key): _integer(f"risk.{key}", value, minimum=0, maximum=100) for key, value in risks_raw.items()}
        seed = _integer("seed", facts.get("seed"))
        transparency = _integer("transparency", facts.get("transparency", 0), minimum=0, maximum=90)
        base_rate = 20 if route is Choice.A else 5
        rate = max(1, base_rate - transparency)
        count = max(1, math.ceil(len(risks) * rate / 100))
        ordered = sorted(risks, key=lambda key: (-risks[key], key))
        selected: list[str] = []
        if route is Choice.A:
            selected.append(ordered[0])
        remainder = [key for key in ordered if key not in selected]
        randomizer = random.Random(seed)
        selected.extend(randomizer.sample(remainder, count - len(selected)))
        findings = sum(risks[key] >= 70 for key in selected)
        clean = len(selected) - findings
        available = _integer("capacity", facts.get("capacity"), minimum=0)
        hours = len(selected) * 2
        if hours > available:
            raise ModelRed(RedCode.RESOURCE, "capacity", "audit hours unavailable")
        return "audit-run", {
            "population": tuple(sorted(risks)),
            "sample": tuple(selected),
            "seed": seed,
            "sample_rate": rate,
            "method": "risk-plus-random" if route is Choice.A else "low-random",
            "hours": hours,
            "capacity_remaining": available - hours,
            "findings": findings,
            "clean": clean,
            "trust_delta": clean if route is Choice.A else 0,
            "severe_penalty_risk": route is Choice.B,
            "closed": True,
            "settled": True,
        }

    def _m350(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        old = _text("old_version", facts.get("old_version"))
        new = _text("new_version", facts.get("new_version"))
        if old == new:
            raise ModelRed(RedCode.INVALID, "new_version", "version must change")
        history = tuple(facts.get("history", ()))
        if len(history) < 3:
            raise ModelRed(RedCode.MISSING, "history", "three comparable years required")
        frozen = tuple(_freeze(row) for row in history)
        old_threshold = _integer("old_threshold", facts.get("old_threshold"), minimum=0)
        if route is Choice.A:
            difficulty = _integer("strategy_difficulty", facts.get("strategy_difficulty", 0), minimum=0)
            new_threshold = old_threshold + difficulty
            risk = 0
            explanation = "strategy-adjusted"
        else:
            top_growth = _integer("top_growth", facts.get("top_growth", 0), minimum=0)
            new_threshold = old_threshold + top_growth
            risk = top_growth
            explanation = "automatic-ratchet"
        return "benchmark-version", {
            "old_version": old,
            "new_version": new,
            "effective_cycle": identity.cycle_serial + 1,
            "old_threshold": old_threshold,
            "new_threshold": new_threshold,
            "history": frozen,
            "history_rewritten": False,
            "explanation": explanation,
            "ratchet_risk": risk,
        }

    def _m351(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        metrics = _unique("metrics", facts.get("metrics", ()))
        outcomes = facts.get("outcomes")
        if not isinstance(outcomes, Mapping):
            raise ModelRed(RedCode.MISSING, "outcomes", "regional outcomes required")
        end_cycle = _integer("end_cycle", facts.get("end_cycle"), minimum=identity.cycle_serial + 1)
        if route is Choice.B:
            regions = _unique("regions", facts.get("regions", ()))
            if set(outcomes) != set(regions):
                raise ModelRed(RedCode.INVARIANT, "outcomes", "all realm regions required")
            for region, values in outcomes.items():
                if not isinstance(values, Mapping) or set(values) != set(metrics):
                    raise ModelRed(RedCode.INVARIANT, f"outcomes.{region}", "all preregistered metrics required")
            return "realm-rollout", {
                "regions": regions,
                "metrics": metrics,
                "outcomes": dict(outcomes),
                "control_regions": (),
                "causal_comparison": False,
                "migration_risk": 20,
                "effective_cycle": end_cycle,
            }
        pilots = _unique("pilots", facts.get("pilots", ()), minimum=2)
        controls = _unique("controls", facts.get("controls", ()), minimum=2)
        if set(pilots) & set(controls):
            raise ModelRed(RedCode.INVARIANT, "regions", "pilot/control must be disjoint")
        if set(outcomes) != set(pilots) | set(controls):
            raise ModelRed(RedCode.INVARIANT, "outcomes", "all frozen regions required")
        for region, values in outcomes.items():
            if not isinstance(values, Mapping) or set(values) != set(metrics):
                raise ModelRed(RedCode.INVARIANT, f"outcomes.{region}", "all preregistered metrics required")
        difference = {
            metric: sum(_number(metric, outcomes[region][metric]) for region in pilots) / len(pilots)
            - sum(_number(metric, outcomes[region][metric]) for region in controls) / len(controls)
            for metric in metrics
        }
        return "regional-pilot", {
            "pilots": pilots,
            "controls": controls,
            "metrics": metrics,
            "outcomes": dict(outcomes),
            "difference": difference,
            "causal_comparison": True,
            "end_cycle": end_cycle,
        }

    def _m352(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        records = tuple(facts.get("records", ()))
        if not records:
            raise ModelRed(RedCode.MISSING, "records", "history records required")
        originals: dict[str, tuple[Any, Any, Any]] = {}
        for record in records:
            record_id = _text("record_id", record.get("record_id"))
            if record_id in originals:
                raise ModelRed(RedCode.INVARIANT, "record_id", "unique historical records required")
            originals[record_id] = (
                record.get("original_value"),
                _text("original_formula", record.get("original_formula")),
                _text("original_policy_version", record.get("original_policy_version")),
            )
        mapping_version = _text("mapping_version", facts.get("mapping_version"))
        factor = _number("factor", facts.get("factor", 1), minimum=0)
        mapped = {record_id: values[0] * factor for record_id, values in originals.items()}
        return "history-mapping", {
            "originals": originals,
            "mapped": mapped,
            "mapping_version": mapping_version,
            "mode": "comparable-layer" if route is Choice.A else "latest-formula-recompute",
            "original_archive_preserved": True,
            "consumer_refs": ("appeal", "promotion", "decade-report"),
            "contamination_risk": route is Choice.B,
        }

    def _m353(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        components = {
            name: _integer(name, facts.get(name), minimum=0)
            for name in ("form_hours", "meeting_hours", "appeal_hours", "calibration_hours", "interruption_hours")
        }
        total = sum(components.values())
        available = _integer("available_hours", facts.get("available_hours"), minimum=0)
        if total > available:
            raise ModelRed(RedCode.RESOURCE, "available_hours", "administration exceeds governance capacity")
        error = _integer("error_rate", facts.get("error_rate", 0), minimum=0, maximum=100)
        overturn = _integer("overturn_rate", facts.get("overturn_rate", 0), minimum=0, maximum=100)
        if route is Choice.A:
            simplified = tuple(sorted(str(value) for value in facts.get("simplified", ())))
            visible_total = total
            hidden_loss = 0
            score_delta = -(error + overturn)
        else:
            simplified = ()
            visible_total = 0
            hidden_loss = total
            score_delta = -(total + error + overturn)
        return "admin-capacity-report", {
            "components": components,
            "actual_total": total,
            "reported_total": visible_total,
            "hidden_capacity_loss": hidden_loss,
            "capacity_remaining": available - total,
            "simplified_processes": simplified,
            "error_rate": error,
            "overturn_rate": overturn,
            "next_manager_score_delta": score_delta,
        }

    def _m354(self, route: Choice, identity: CaseIdentity, facts: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        delivered = _integer("delivered", facts.get("delivered"), minimum=0)
        appeals = _integer("appeals", facts.get("appeals"), minimum=0, maximum=delivered)
        overturns = _integer("overturns", facts.get("overturns"), minimum=0, maximum=appeals)
        exits = _integer("exits", facts.get("exits"), minimum=0)
        healthy = _integer("healthy_exits", facts.get("healthy_exits"), minimum=0, maximum=exits)
        raw = (
            appeals / delivered if delivered else 0.0,
            overturns / appeals if appeals else 0.0,
            healthy / exits if exits else 0.0,
        )
        if route is Choice.A:
            reported = tuple(_number("reported", value, minimum=0, maximum=1) for value in facts.get("reported", raw))
        else:
            # B targets the pretty numbers while retaining the raw audit trail.
            reported = (max(0.0, raw[0] / 2), max(0.0, raw[1] / 2), min(1.0, raw[2] + 0.25))
        gap = tuple(round(reported[index] - raw[index], 6) for index in range(3))
        gaming = any(abs(value) > 1e-9 for value in gap)
        suppression = raw[0] > reported[0] or raw[1] > reported[1]
        reclassification = raw[2] < reported[2]
        return "fairness-meta-audit", {
            "raw_counts": {
                "delivered": delivered,
                "appeals": appeals,
                "overturns": overturns,
                "exits": exits,
                "healthy_exits": healthy,
            },
            "raw": raw,
            "reported": reported,
            "gap": gap,
            "suppression_flag": suppression,
            "reclassification_flag": reclassification,
            "gaming": gaming,
            "raw_archive_preserved": True,
            # Trust requires a separately produced and consumed remediation
            # receipt; raw audit inputs cannot self-award it.
            "long_term_trust_delta": 0,
        }


def assert_contract() -> None:
    if READINESS != "python-l0-only" or MCP_EVIDENCE != "none":
        raise AssertionError("semantic oracle must not claim live readiness")
    if OWNED_IDS != (*range(32, 37), *range(345, 355)):
        raise AssertionError("owned manager/governance IDs drifted")
    if Q_PROJECTION_IDS != tuple(range(121, 129)):
        raise AssertionError("manager-certification projection drifted")
    if len(OFFICIAL_KPI_COMPONENT_NAMES) != 8 or OFFICIAL_KPI_COMPONENT_NAMES[ORGANIZATION_COMPONENT_INDEX] != "organization":
        raise AssertionError("manager evidence must remain inside official organization component 8")
    if set(PENDING_INPUT_CONSUMERS.values()) != {346, 347, 354}:
        raise AssertionError("typed producer/consumer map drifted")


assert_contract()
