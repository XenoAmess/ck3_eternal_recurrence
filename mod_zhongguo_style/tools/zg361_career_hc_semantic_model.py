#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executable reference model for the Career/HC CK3 projection.

The older phase-two model proves the individual policy ideas.  This module
models the *runtime projection* shared by the generated D/M/N/O/P/Q script:

* every operation is bound to owner, subject, cycle, case and object revision;
* A and B create typed vacancy/HC/candidate/incumbent/succession/backfill
  objects and invoke a named downstream consumer;
* C records bounded debt and cannot fabricate a successful object or spend a
  resource;
* duplicate and stale operations are deterministic no-ops; and
* every capacity and dual-payment transition conserves its opening total.

Passing this model is Python L0 evidence only.  It is not CK3 or MCP live
evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from types import MappingProxyType
from typing import Final, Mapping


READINESS: Final[str] = "python-l0-reference-only"
CK3_LIVE: Final[bool] = False


class SemanticError(ValueError):
    """Typed RED result for malformed or non-conserving operations."""


class Route(IntEnum):
    EVIDENCE = 1
    POLITICAL = 2
    DEFER = 3


class ResultCode(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate-operation"
    STALE = "stale-operation"


class ObjectKind(str, Enum):
    CANDIDATE = "candidate"
    VACANCY = "vacancy"
    COMPENSATION = "compensation"
    HC_SLOT = "hc-slot"
    INCUMBENT = "incumbent"
    SUCCESSION = "succession"
    BACKFILL = "backfill"
    MANAGER = "manager"


class CapacityState(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    FROZEN = "frozen"
    RECLAIMED = "reclaimed"


@dataclass(frozen=True, slots=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        for name in ("owner_id", "subject_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise SemanticError(f"{name} must be a non-empty string")
        for name in ("cycle_serial", "case_serial"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise SemanticError(f"{name} must be an integer >= 1")


@dataclass(frozen=True, slots=True)
class OperationToken:
    identity: CaseIdentity
    mechanism_id: int
    expected_revision: int


@dataclass(frozen=True, slots=True)
class OperationResult:
    mechanism_id: int
    applied: bool
    code: ResultCode
    revision: int


@dataclass(frozen=True, slots=True)
class MechanismSpec:
    mechanism_id: int
    domain: str
    object_kinds: tuple[ObjectKind, ...]
    a_state: str
    b_state: str
    consumer_key: str

    def __post_init__(self) -> None:
        if self.domain not in {"d", "m", "n", "o", "p", "q"}:
            raise SemanticError(f"invalid domain for {self.mechanism_id}")
        if not self.object_kinds:
            raise SemanticError(f"mechanism {self.mechanism_id} has no business object")
        if len(set(self.object_kinds)) != len(self.object_kinds):
            raise SemanticError(f"mechanism {self.mechanism_id} repeats an object kind")
        if not self.a_state or not self.b_state or not self.consumer_key:
            raise SemanticError(f"mechanism {self.mechanism_id} has an empty semantic field")


def _spec(
    mechanism_id: int,
    domain: str,
    kinds: tuple[ObjectKind, ...],
    a_state: str,
    b_state: str,
) -> MechanismSpec:
    return MechanismSpec(
        mechanism_id,
        domain,
        kinds,
        a_state,
        b_state,
        f"zg361_career_hc_m{mechanism_id:03d}_business_consumer_effect",
    )


# This table is also consumed by the CK3 generator.  State names are frozen
# audit vocabulary, not UI prose and not generic A/B labels.
_SPECS = (
    _spec(19, "d", (ObjectKind.CANDIDATE,), "eligible", "sponsor-bypassed"),
    _spec(20, "d", (ObjectKind.CANDIDATE, ObjectKind.VACANCY), "panel-packet", "sponsor-packet"),
    _spec(21, "d", (ObjectKind.COMPENSATION, ObjectKind.CANDIDATE), "matrix-paid", "cash-concentrated"),
    _spec(22, "d", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "budget-reserved", "politically-frozen"),
    _spec(23, "d", (ObjectKind.HC_SLOT,), "defended-free", "emergency-borrowed"),
    _spec(24, "d", (ObjectKind.VACANCY, ObjectKind.CANDIDATE, ObjectKind.BACKFILL), "transfer-scheduled", "mobility-blocked"),
    _spec(25, "d", (ObjectKind.VACANCY, ObjectKind.CANDIDATE, ObjectKind.COMPENSATION), "written-offer", "oral-counteroffer"),
    _spec(92, "m", (ObjectKind.CANDIDATE, ObjectKind.MANAGER), "tracks-separated", "star-made-manager"),
    _spec(93, "m", (ObjectKind.INCUMBENT, ObjectKind.CANDIDATE), "returned-to-expert", "forced-or-demoted"),
    _spec(94, "m", (ObjectKind.CANDIDATE, ObjectKind.COMPENSATION), "bounded-micro-level", "empty-half-title"),
    _spec(95, "m", (ObjectKind.INCUMBENT, ObjectKind.MANAGER), "annual-review", "authority-stripped"),
    _spec(96, "m", (ObjectKind.CANDIDATE, ObjectKind.HC_SLOT), "exception-reserved", "sponsor-exception"),
    _spec(97, "m", (ObjectKind.CANDIDATE, ObjectKind.HC_SLOT), "cross-team-winner", "local-volume-winner"),
    _spec(98, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "typed-slot", "fungible-slot"),
    _spec(99, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "carried-once", "year-end-reclaimed"),
    _spec(100, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "critical-exception", "patronage-freeze"),
    _spec(101, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT, ObjectKind.CANDIDATE), "pipeline-occupied", "senior-occupied"),
    _spec(102, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "zero-base-reserved", "annual-reclaimed"),
    _spec(103, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT), "hoard-reclaimed", "fake-candidate-frozen"),
    _spec(104, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT, ObjectKind.CANDIDATE, ObjectKind.COMPENSATION), "mixed-source-occupied", "mature-only-occupied"),
    _spec(105, "n", (ObjectKind.VACANCY, ObjectKind.HC_SLOT, ObjectKind.BACKFILL), "backfill-owned", "release-blocked"),
    _spec(106, "o", (ObjectKind.INCUMBENT, ObjectKind.SUCCESSION), "role-person-separated", "favorite-conflated"),
    _spec(107, "o", (ObjectKind.CANDIDATE, ObjectKind.SUCCESSION), "readiness-evidenced", "crown-prince-ready"),
    _spec(108, "o", (ObjectKind.CANDIDATE, ObjectKind.SUCCESSION, ObjectKind.HC_SLOT), "acting-authority-funded", "responsibility-only"),
    _spec(109, "o", (ObjectKind.CANDIDATE, ObjectKind.SUCCESSION), "need-to-know", "public-high-potential"),
    _spec(110, "o", (ObjectKind.CANDIDATE, ObjectKind.SUCCESSION), "performance-frozen-first", "potential-overrode-grade"),
    _spec(111, "o", (ObjectKind.INCUMBENT, ObjectKind.VACANCY, ObjectKind.BACKFILL), "attrition-classified", "healthy-washed"),
    _spec(112, "o", (ObjectKind.CANDIDATE, ObjectKind.COMPENSATION, ObjectKind.SUCCESSION), "one-funded-promise", "reactive-counteroffer"),
    _spec(113, "o", (ObjectKind.INCUMBENT, ObjectKind.SUCCESSION), "knowledge-replicated", "hero-dependency"),
    _spec(114, "p", (ObjectKind.CANDIDATE, ObjectKind.BACKFILL, ObjectKind.COMPENSATION), "export-credited", "talent-blocked"),
    _spec(115, "p", (ObjectKind.VACANCY, ObjectKind.CANDIDATE), "anonymous-finalist", "preapproval-exposed"),
    _spec(116, "p", (ObjectKind.VACANCY, ObjectKind.CANDIDATE, ObjectKind.BACKFILL), "release-90-days", "single-extension-150-days"),
    _spec(117, "p", (ObjectKind.CANDIDATE,), "ramp-protected-once", "full-ranked-immediately"),
    _spec(118, "p", (ObjectKind.CANDIDATE, ObjectKind.VACANCY), "probation-separated", "newcomer-used-as-bottom"),
    _spec(119, "p", (ObjectKind.CANDIDATE, ObjectKind.COMPENSATION, ObjectKind.VACANCY), "quality-written-back", "speed-rewarded"),
    _spec(120, "p", (ObjectKind.CANDIDATE, ObjectKind.INCUMBENT), "mentor-milestones-settled", "unfunded-mentoring"),
    _spec(121, "q", (ObjectKind.CANDIDATE, ObjectKind.MANAGER, ObjectKind.HC_SLOT), "small-team-trial", "large-team-immediate"),
    _spec(122, "q", (ObjectKind.MANAGER,), "weights-40-30-30", "hard-results-80"),
    _spec(123, "q", (ObjectKind.MANAGER, ObjectKind.CANDIDATE), "six-factor-credible", "single-anonymous-vote"),
    _spec(
        124,
        "q",
        (
            ObjectKind.MANAGER,
            ObjectKind.VACANCY,
            ObjectKind.HC_SLOT,
            ObjectKind.CANDIDATE,
            ObjectKind.INCUMBENT,
            ObjectKind.SUCCESSION,
            ObjectKind.BACKFILL,
        ),
        "successor-before-promotion",
        "promotion-before-successor",
    ),
    _spec(125, "q", (ObjectKind.MANAGER, ObjectKind.SUCCESSION), "delegated-crisis", "hero-firefighting"),
    _spec(126, "q", (ObjectKind.MANAGER, ObjectKind.CANDIDATE), "four-quadrant-action", "performance-only"),
    _spec(127, "q", (ObjectKind.MANAGER, ObjectKind.HC_SLOT, ObjectKind.VACANCY), "layered-span", "flat-distorted-span"),
    _spec(128, "q", (ObjectKind.MANAGER,), "next-cycle-policy", "rigid-quota-retained"),
)

SEMANTIC_SPECS: Final[Mapping[int, MechanismSpec]] = MappingProxyType(
    {row.mechanism_id: row for row in _SPECS}
)
EXPECTED_IDS: Final[tuple[int, ...]] = tuple((*range(19, 26), *range(92, 129)))
DUAL_PAYMENT_IDS: Final[frozenset[int]] = frozenset({21, 25, 101, 104, 112, 114, 119})
HC_DEST_A: Final[Mapping[int, CapacityState]] = MappingProxyType(
    {
        98: CapacityState.RESERVED,
        99: CapacityState.RESERVED,
        100: CapacityState.RESERVED,
        101: CapacityState.OCCUPIED,
        102: CapacityState.RESERVED,
        103: CapacityState.RECLAIMED,
        104: CapacityState.OCCUPIED,
        105: CapacityState.RESERVED,
    }
)
HC_DEST_B: Final[Mapping[int, CapacityState]] = MappingProxyType(
    {
        98: CapacityState.FROZEN,
        99: CapacityState.RECLAIMED,
        100: CapacityState.FROZEN,
        101: CapacityState.OCCUPIED,
        102: CapacityState.RECLAIMED,
        103: CapacityState.FROZEN,
        104: CapacityState.OCCUPIED,
        105: CapacityState.FROZEN,
    }
)


def validate_specs() -> None:
    if tuple(sorted(SEMANTIC_SPECS)) != EXPECTED_IDS:
        raise SemanticError("semantic registry does not cover the frozen 44 IDs")
    consumers = [row.consumer_key for row in SEMANTIC_SPECS.values()]
    if len(consumers) != len(set(consumers)):
        raise SemanticError("semantic consumer keys must be unique")
    for mechanism_id, row in SEMANTIC_SPECS.items():
        if mechanism_id != row.mechanism_id:
            raise SemanticError("semantic registry key mismatch")


@dataclass(slots=True)
class CapacityLedger:
    authorized: int
    available: int | None = None
    reserved: int = 0
    occupied: int = 0
    frozen: int = 0
    reclaimed: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.authorized, bool) or not isinstance(self.authorized, int) or self.authorized < 0:
            raise SemanticError("authorized capacity must be an integer >= 0")
        if self.available is None:
            self.available = self.authorized
        self.assert_conserved()

    def value(self, state: CapacityState) -> int:
        return int(getattr(self, state.value))

    def move(self, source: CapacityState, destination: CapacityState, units: int = 1) -> None:
        if source == destination:
            raise SemanticError("capacity source and destination must differ")
        if isinstance(units, bool) or not isinstance(units, int) or units < 1:
            raise SemanticError("capacity units must be an integer >= 1")
        if self.value(source) < units:
            raise SemanticError(f"insufficient {source.value} capacity")
        setattr(self, source.value, self.value(source) - units)
        setattr(self, destination.value, self.value(destination) + units)
        self.assert_conserved()

    def assert_conserved(self) -> None:
        values = (self.available, self.reserved, self.occupied, self.frozen, self.reclaimed)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
            raise SemanticError("capacity partition contains an invalid value")
        if sum(int(value) for value in values) != self.authorized:
            raise SemanticError("capacity partition does not conserve its opening total")

    def snapshot(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.authorized,
            int(self.available),
            self.reserved,
            self.occupied,
            self.frozen,
            self.reclaimed,
        )


@dataclass(slots=True)
class DualResourceLedger:
    opening_treasury: int = 100
    opening_personal: int = 100
    treasury_available: int = field(init=False)
    personal_available: int = field(init=False)
    treasury_paid: dict[str, int] = field(default_factory=dict)
    personal_paid: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("opening_treasury", "opening_personal"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SemanticError(f"{name} must be an integer >= 0")
        self.treasury_available = self.opening_treasury
        self.personal_available = self.opening_personal

    def pay(self, operation_id: str, recipient_id: str, amount: int = 5) -> None:
        if not operation_id or not recipient_id:
            raise SemanticError("payment identity must be non-empty")
        if operation_id in self.treasury_paid or operation_id in self.personal_paid:
            raise SemanticError("payment operation is single-use")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 1:
            raise SemanticError("payment amount must be an integer >= 1")
        if self.treasury_available < amount or self.personal_available < amount:
            raise SemanticError("dual payment is not fully funded")
        self.treasury_available -= amount
        self.personal_available -= amount
        self.treasury_paid[operation_id] = amount
        self.personal_paid[operation_id] = amount
        self.assert_conserved()

    def assert_conserved(self) -> None:
        if self.opening_treasury != self.treasury_available + sum(self.treasury_paid.values()):
            raise SemanticError("treasury payment ledger is not conserved")
        if self.opening_personal != self.personal_available + sum(self.personal_paid.values()):
            raise SemanticError("personal payment ledger is not conserved")
        if set(self.treasury_paid) != set(self.personal_paid):
            raise SemanticError("dual payment journals diverged")

    def snapshot(self) -> tuple[int, int, int, int]:
        return (
            self.treasury_available,
            self.personal_available,
            sum(self.treasury_paid.values()),
            sum(self.personal_paid.values()),
        )


@dataclass(slots=True)
class SemanticObject:
    object_id: str
    kind: ObjectKind
    identity: CaseIdentity
    person_id: str
    state: str
    route: Route
    consumer_key: str
    object_revision: int = 1
    incumbent_id: str | None = None
    candidate_id: str | None = None


@dataclass(slots=True)
class OperationRecord:
    mechanism_id: int
    identity: CaseIdentity
    state: str = "open"
    route: Route | None = None
    consumer_key: str | None = None
    revision: int = 0


@dataclass(slots=True)
class CareerHcSemanticRuntime:
    """One frozen 44-operation portfolio with typed downstream objects."""

    identity: CaseIdentity
    records: dict[int, OperationRecord] = field(init=False)
    objects: dict[str, SemanticObject] = field(default_factory=dict)
    applied_serials: set[str] = field(default_factory=set)
    debts: dict[int, int] = field(default_factory=dict)
    audit: list[tuple[int, Route, str]] = field(default_factory=list)
    capacities: dict[str, CapacityLedger] = field(init=False)
    resources: DualResourceLedger = field(default_factory=DualResourceLedger)
    hc_slots: dict[int, CapacityState] = field(init=False)
    promotion_candidate_id: str | None = None
    promotion_slot_owner_id: str | None = None
    succession_candidate_id: str | None = None
    succession_incumbent_id: str | None = None
    backfill_owner_id: str | None = None
    release_days: int | None = None
    manager_successor_accepted: bool = False
    next_cycle_policy: str | None = None
    q_vacancy_id: str | None = None
    q_hc_slot_id: str | None = None
    q_candidate_id: str | None = None
    q_incumbent_id: str | None = None
    q_succession_id: str | None = None
    q_backfill_id: str | None = None
    q_score_components: tuple[int, int, int] | None = None
    q_score_weights: tuple[int, int, int] | None = None
    q_survey_factors: int = 0
    q_survey_credibility: int = 0
    q_crisis_manager_hours: int = 0
    q_crisis_delegated_hours: int = 0
    q_values_quadrant: str | None = None
    q_span_snapshot: int | None = None
    q_climate_snapshot: tuple[int, int, int, int, int] | None = None
    q_policy_effective_cycle: int | None = None

    def __post_init__(self) -> None:
        validate_specs()
        self.records = {
            mechanism_id: OperationRecord(mechanism_id, self.identity)
            for mechanism_id in EXPECTED_IDS
        }
        self.capacities = {
            "d_hc": CapacityLedger(2),
            "promotion": CapacityLedger(1),
            "hc": CapacityLedger(8),
            "acting": CapacityLedger(1),
            "attrition": CapacityLedger(1),
            "backfill": CapacityLedger(1),
            "mentor_hours": CapacityLedger(12),
            "manager_team": CapacityLedger(3),
            "manager_hc": CapacityLedger(4),
            "crisis_hours": CapacityLedger(100),
        }
        self.hc_slots = {mechanism_id: CapacityState.AVAILABLE for mechanism_id in range(98, 106)}
        self.assert_conserved()

    def token(self, mechanism_id: int) -> OperationToken:
        record = self._record(mechanism_id)
        return OperationToken(self.identity, mechanism_id, record.revision)

    def apply(
        self,
        token: OperationToken,
        operation_serial: str,
        route: Route,
    ) -> OperationResult:
        if not isinstance(operation_serial, str) or not operation_serial.strip():
            raise SemanticError("operation_serial must be non-empty")
        try:
            route = Route(route)
        except (TypeError, ValueError) as exc:
            raise SemanticError("route must be A, B or C") from exc
        if operation_serial in self.applied_serials:
            record = self._record(token.mechanism_id)
            return OperationResult(token.mechanism_id, False, ResultCode.DUPLICATE, record.revision)
        record = self._record(token.mechanism_id)
        if (
            token.identity != self.identity
            or token.mechanism_id != record.mechanism_id
            or token.expected_revision != record.revision
            or record.revision != 0
        ):
            return OperationResult(token.mechanism_id, False, ResultCode.STALE, record.revision)

        spec = SEMANTIC_SPECS[token.mechanism_id]
        if route is Route.DEFER:
            self.debts[token.mechanism_id] = self.debts.get(token.mechanism_id, 0) + 1
            terminal_state = "deferred-with-debt"
        else:
            self._apply_business(spec, route, operation_serial)
            terminal_state = spec.a_state if route is Route.EVIDENCE else spec.b_state
            for kind in spec.object_kinds:
                object_id = f"{kind.value}:{spec.mechanism_id:03d}"
                if object_id in self.objects:
                    raise SemanticError("typed business object ID was duplicated")
                self.objects[object_id] = SemanticObject(
                    object_id=object_id,
                    kind=kind,
                    identity=self.identity,
                    person_id=self._object_person_id(spec.mechanism_id, kind),
                    state=terminal_state,
                    route=route,
                    consumer_key=spec.consumer_key,
                    incumbent_id=(
                        self.q_incumbent_id
                        if spec.mechanism_id == 124 and kind is ObjectKind.SUCCESSION
                        else None
                    ),
                    candidate_id=(
                        self.q_candidate_id
                        if spec.mechanism_id == 124 and kind is ObjectKind.SUCCESSION
                        else None
                    ),
                )

        record.state = terminal_state
        record.route = route
        record.consumer_key = spec.consumer_key
        record.revision += 1
        self.applied_serials.add(operation_serial)
        self.audit.append((spec.mechanism_id, route, spec.consumer_key))
        self.assert_conserved()
        return OperationResult(spec.mechanism_id, True, ResultCode.APPLIED, record.revision)

    def _record(self, mechanism_id: int) -> OperationRecord:
        if isinstance(mechanism_id, bool) or not isinstance(mechanism_id, int):
            raise SemanticError("mechanism_id must be an integer")
        try:
            return self.records[mechanism_id]
        except KeyError as exc:
            raise SemanticError(f"mechanism {mechanism_id} is outside the Career/HC slice") from exc

    def _move_if_available(
        self,
        ledger_name: str,
        destination: CapacityState,
        units: int = 1,
    ) -> bool:
        ledger = self.capacities[ledger_name]
        if ledger.value(CapacityState.AVAILABLE) < units:
            return False
        ledger.move(CapacityState.AVAILABLE, destination, units)
        return True

    def _object_person_id(self, mechanism_id: int, kind: ObjectKind) -> str:
        """Resolve the real person role behind a typed object.

        Q124 intentionally distinguishes the assessed incumbent from the
        successor candidate.  Non-person ledger objects remain anchored to
        the assessed manager, but never masquerade as the candidate.
        """

        if mechanism_id == 124 and kind is ObjectKind.CANDIDATE:
            if self.q_candidate_id is None:
                raise SemanticError("Q124 candidate was not frozen before object publication")
            return self.q_candidate_id
        if mechanism_id == 124 and kind is ObjectKind.INCUMBENT:
            if self.q_incumbent_id is None:
                raise SemanticError("Q124 incumbent was not frozen before object publication")
            return self.q_incumbent_id
        return self.identity.subject_id

    def _apply_business(self, spec: MechanismSpec, route: Route, operation_serial: str) -> None:
        mechanism_id = spec.mechanism_id
        evidence = route is Route.EVIDENCE

        if mechanism_id in DUAL_PAYMENT_IDS:
            self.resources.pay(operation_serial, self.identity.subject_id)

        if mechanism_id == 19:
            self.promotion_candidate_id = self.identity.subject_id
            if not evidence:
                self.debts[19] = self.debts.get(19, 0) + 1
        elif mechanism_id == 20:
            self.promotion_candidate_id = self.identity.subject_id
            if not evidence:
                self.debts[20] = self.debts.get(20, 0) + 1
        elif mechanism_id == 22:
            destination = CapacityState.RESERVED if evidence else CapacityState.FROZEN
            self.capacities["d_hc"].move(CapacityState.AVAILABLE, destination)
        elif mechanism_id == 23:
            if not evidence:
                self.debts[23] = self.debts.get(23, 0) + 1
        elif mechanism_id == 24:
            destination = CapacityState.RESERVED if evidence else CapacityState.FROZEN
            self.capacities["d_hc"].move(CapacityState.AVAILABLE, destination)
            self.backfill_owner_id = self.identity.owner_id if evidence else None
        elif mechanism_id == 25:
            d_hc = self.capacities["d_hc"]
            if d_hc.reserved:
                d_hc.move(CapacityState.RESERVED, CapacityState.OCCUPIED)
            if not evidence:
                self.debts[25] = self.debts.get(25, 0) + 1
        elif mechanism_id in {92, 93, 94, 95}:
            if not evidence:
                self.debts[mechanism_id] = self.debts.get(mechanism_id, 0) + 1
        elif mechanism_id == 96:
            self._move_if_available("promotion", CapacityState.RESERVED)
            self.promotion_slot_owner_id = self.identity.subject_id
            if not evidence:
                self.debts[96] = self.debts.get(96, 0) + 1
        elif mechanism_id == 97:
            promotion = self.capacities["promotion"]
            if promotion.reserved:
                promotion.move(CapacityState.RESERVED, CapacityState.OCCUPIED)
            elif promotion.available:
                promotion.move(CapacityState.AVAILABLE, CapacityState.OCCUPIED)
            self.promotion_slot_owner_id = self.identity.subject_id
            if not evidence:
                self.debts[97] = self.debts.get(97, 0) + 1
        elif 98 <= mechanism_id <= 105:
            destination = HC_DEST_A[mechanism_id] if evidence else HC_DEST_B[mechanism_id]
            if self.hc_slots[mechanism_id] is not CapacityState.AVAILABLE:
                raise SemanticError("HC slot operation is not single-use")
            self.capacities["hc"].move(CapacityState.AVAILABLE, destination)
            self.hc_slots[mechanism_id] = destination
            if mechanism_id == 105 and evidence:
                self.backfill_owner_id = self.identity.owner_id
            if not evidence and mechanism_id in {98, 100, 103, 105}:
                self.debts[mechanism_id] = self.debts.get(mechanism_id, 0) + 1
        elif mechanism_id == 106:
            self.succession_incumbent_id = self.identity.owner_id
            self.succession_candidate_id = self.identity.subject_id
            if not evidence:
                self.debts[106] = self.debts.get(106, 0) + 1
        elif mechanism_id == 107:
            self.succession_candidate_id = self.identity.subject_id
            if not evidence:
                self.debts[107] = self.debts.get(107, 0) + 1
        elif mechanism_id == 108:
            if evidence:
                self.capacities["acting"].move(CapacityState.AVAILABLE, CapacityState.RESERVED)
            else:
                self.debts[108] = self.debts.get(108, 0) + 1
        elif mechanism_id in {109, 110}:
            if not evidence:
                self.debts[mechanism_id] = self.debts.get(mechanism_id, 0) + 1
        elif mechanism_id == 111:
            self.capacities["attrition"].move(CapacityState.AVAILABLE, CapacityState.RECLAIMED)
            self.backfill_owner_id = self.identity.owner_id
            if not evidence:
                self.debts[111] = self.debts.get(111, 0) + 1
        elif mechanism_id == 112:
            if not evidence:
                self.debts[112] = self.debts.get(112, 0) + 1
        elif mechanism_id == 113:
            if not evidence:
                self.debts[113] = self.debts.get(113, 0) + 1
        elif mechanism_id == 114:
            destination = CapacityState.RESERVED if evidence else CapacityState.FROZEN
            self.capacities["backfill"].move(CapacityState.AVAILABLE, destination)
            self.backfill_owner_id = self.identity.owner_id if evidence else None
            if not evidence:
                self.debts[114] = self.debts.get(114, 0) + 1
        elif mechanism_id == 115:
            if not evidence:
                self.debts[115] = self.debts.get(115, 0) + 1
        elif mechanism_id == 116:
            self.release_days = 90 if evidence else 150
            if not evidence:
                self.debts[116] = self.debts.get(116, 0) + 1
        elif mechanism_id in {117, 118}:
            if not evidence:
                self.debts[mechanism_id] = self.debts.get(mechanism_id, 0) + 1
        elif mechanism_id == 119:
            backfill = self.capacities["backfill"]
            if evidence and backfill.reserved:
                backfill.move(CapacityState.RESERVED, CapacityState.OCCUPIED)
            if not evidence:
                self.debts[119] = self.debts.get(119, 0) + 1
        elif mechanism_id == 120:
            if evidence:
                self.capacities["mentor_hours"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED, 6
                )
            else:
                self.debts[120] = self.debts.get(120, 0) + 1
        elif mechanism_id == 121:
            if evidence:
                self.capacities["manager_team"].move(
                    CapacityState.AVAILABLE, CapacityState.RESERVED
                )
                self.capacities["manager_hc"].move(
                    CapacityState.AVAILABLE, CapacityState.RESERVED
                )
            else:
                self.capacities["manager_team"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED, 3
                )
                self.capacities["manager_hc"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED, 3
                )
                self.debts[121] = self.debts.get(121, 0) + 1
            self.succession_candidate_id = self.identity.subject_id
        elif mechanism_id == 122:
            self.q_score_components = (70, 70, 70) if evidence else (90, 35, 20)
            self.q_score_weights = (40, 30, 30)
            if not evidence:
                self.debts[122] = self.debts.get(122, 0) + 1
        elif mechanism_id == 123:
            self.q_survey_factors = 6 if evidence else 1
            self.q_survey_credibility = 100 if evidence else 25
            if not evidence:
                self.debts[123] = self.debts.get(123, 0) + 1
        elif mechanism_id == 124:
            self.q_vacancy_id = f"vacancy:{self.identity.case_serial}:124"
            self.q_hc_slot_id = f"hc:{self.identity.case_serial}:124"
            self.q_candidate_id = (
                f"{self.identity.subject_id}:successor:"
                f"{self.identity.cycle_serial}:{self.identity.case_serial}"
            )
            self.q_incumbent_id = self.identity.subject_id
            self.q_succession_id = f"succession:{self.identity.case_serial}:124"
            self.q_backfill_id = f"backfill:{self.identity.case_serial}:124"
            manager_team = self.capacities["manager_team"]
            if evidence and manager_team.reserved:
                manager_team.move(CapacityState.RESERVED, CapacityState.OCCUPIED)
                self.manager_successor_accepted = True
                self._move_if_available("manager_hc", CapacityState.RESERVED)
            elif not evidence:
                self._move_if_available("manager_hc", CapacityState.FROZEN)
                self.debts[124] = self.debts.get(124, 0) + 1
        elif mechanism_id == 125:
            if evidence:
                self.capacities["crisis_hours"].move(
                    CapacityState.AVAILABLE, CapacityState.RESERVED, 60
                )
                self.capacities["crisis_hours"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED, 40
                )
                self.q_crisis_manager_hours = 40
                self.q_crisis_delegated_hours = 60
                self.manager_successor_accepted = True
            else:
                self.capacities["crisis_hours"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED, 100
                )
                self.q_crisis_manager_hours = 100
                self.q_crisis_delegated_hours = 0
                self.debts[125] = self.debts.get(125, 0) + 1
        elif mechanism_id == 126:
            self.q_values_quadrant = "double-high" if evidence else "wild-dog"
            if not evidence:
                self.debts[126] = self.debts.get(126, 0) + 1
        elif mechanism_id == 127:
            if evidence:
                if self.capacities["manager_hc"].available < 1:
                    raise SemanticError("Q127 cannot create a management layer without HC")
                self._move_if_available("manager_team", CapacityState.OCCUPIED)
                self.capacities["manager_hc"].move(
                    CapacityState.AVAILABLE, CapacityState.OCCUPIED
                )
            self.q_span_snapshot = 8
            if not evidence:
                self.debts[127] = self.debts.get(127, 0) + 1
        elif mechanism_id == 128:
            self.next_cycle_policy = "evidence-adjusted" if evidence else "rigid-quota"
            self.q_climate_snapshot = (70, 55, 45, 60, 20)
            self.q_policy_effective_cycle = self.identity.cycle_serial + 1
            if not evidence:
                self.debts[128] = self.debts.get(128, 0) + 1

    def assert_conserved(self) -> None:
        for ledger in self.capacities.values():
            ledger.assert_conserved()
        self.resources.assert_conserved()
        hc_counts = {state: 0 for state in CapacityState}
        for state in self.hc_slots.values():
            hc_counts[state] += 1
        hc = self.capacities["hc"]
        if any(hc_counts[state] != hc.value(state) for state in CapacityState):
            raise SemanticError("per-slot HC states diverged from the HC partition")
        for object_record in self.objects.values():
            if object_record.identity != self.identity:
                raise SemanticError("typed object escaped its frozen case identity")
            spec = SEMANTIC_SPECS[int(object_record.object_id.rsplit(":", 1)[1])]
            if object_record.consumer_key != spec.consumer_key:
                raise SemanticError("typed object was not written by its authoritative consumer")

    def snapshot(self) -> tuple[object, ...]:
        """Stable state snapshot used to prove stale/duplicate no-mutation."""

        return (
            tuple(
                (mid, row.state, row.route, row.consumer_key, row.revision)
                for mid, row in sorted(self.records.items())
            ),
            tuple(
                (key, value.kind, value.state, value.route, value.consumer_key)
                for key, value in sorted(self.objects.items())
            ),
            tuple((key, ledger.snapshot()) for key, ledger in sorted(self.capacities.items())),
            self.resources.snapshot(),
            tuple(sorted(self.hc_slots.items())),
            tuple(sorted(self.debts.items())),
            tuple(self.audit),
            self.promotion_candidate_id,
            self.promotion_slot_owner_id,
            self.succession_candidate_id,
            self.succession_incumbent_id,
            self.backfill_owner_id,
            self.release_days,
            self.manager_successor_accepted,
            self.next_cycle_policy,
            self.q_vacancy_id,
            self.q_hc_slot_id,
            self.q_candidate_id,
            self.q_incumbent_id,
            self.q_succession_id,
            self.q_backfill_id,
            self.q_score_components,
            self.q_score_weights,
            self.q_survey_factors,
            self.q_survey_credibility,
            self.q_crisis_manager_hours,
            self.q_crisis_delegated_hours,
            self.q_values_quadrant,
            self.q_span_snapshot,
            self.q_climate_snapshot,
            self.q_policy_effective_cycle,
        )


validate_specs()
