#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic semantic model for the native B2 CK3 runtime.

This module deliberately owns only #014-017, #069-081 and #358-359.  The
feedback/PIP package remains authoritative for #146-156/#181-191.  The model
does not raise live readiness; it exists to make stable identity, route-C
non-creation, replay, stale deadlines and downstream consumers executable in
L0 instead of describing them with source-text assertions alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Mapping

from zg361_b2_runtime_data import CaseIdentity, PolicyRoute


REFERENCE_ONLY: Final = True
NATIVE_B2_IDS: Final[tuple[int, ...]] = (
    tuple(range(14, 18)) + tuple(range(69, 82)) + (358, 359)
)
DELEGATED_FEEDBACK_PIP_IDS: Final[tuple[int, ...]] = (
    tuple(range(146, 157)) + tuple(range(181, 192))
)


@dataclass(frozen=True)
class SemanticResult:
    applied: bool
    code: str


@dataclass
class NativeBusinessCase:
    mechanism_id: int
    identity: CaseIdentity
    route: PolicyRoute
    state: str
    revision: int = 1
    consumed: bool = False
    consumer_receipt: tuple[int, CaseIdentity] | None = None

    def token(self) -> tuple[int, CaseIdentity, str, int]:
        return (self.mechanism_id, self.identity, self.state, self.revision)


@dataclass(frozen=True)
class PolicyDebt:
    mechanism_id: int
    identity: CaseIdentity
    due_cycle: int


@dataclass
class NativeCaseBook:
    """Common A/B/C, identity, duplicate and stale contract for all 19 IDs."""

    cases: dict[tuple[int, CaseIdentity], NativeBusinessCase] = field(
        default_factory=dict
    )
    debts: dict[tuple[int, CaseIdentity], PolicyDebt] = field(default_factory=dict)

    def open(
        self,
        mechanism_id: int,
        identity: CaseIdentity,
        route: PolicyRoute,
        *,
        initial_state: str,
    ) -> SemanticResult:
        if mechanism_id not in NATIVE_B2_IDS:
            return SemanticResult(False, "foreign-owner")
        key = (mechanism_id, identity)
        route = PolicyRoute(route)
        if key in self.cases or key in self.debts:
            return SemanticResult(False, "duplicate")
        if route == PolicyRoute.C:
            self.debts[key] = PolicyDebt(
                mechanism_id, identity, identity.cycle_serial + 1
            )
            return SemanticResult(True, "policy-debt-only")
        self.cases[key] = NativeBusinessCase(
            mechanism_id, identity, route, initial_state
        )
        return SemanticResult(True, "business-case-open")

    def consume(
        self,
        token: tuple[int, CaseIdentity, str, int],
        *,
        new_state: str,
    ) -> SemanticResult:
        mechanism_id, identity, expected_state, expected_revision = token
        case = self.cases.get((mechanism_id, identity))
        if case is None:
            return SemanticResult(False, "missing-case")
        if case.consumed:
            return SemanticResult(False, "duplicate-consumer")
        if case.state != expected_state or case.revision != expected_revision:
            return SemanticResult(False, "stale")
        case.state = new_state
        case.revision += 1
        case.consumed = True
        case.consumer_receipt = (mechanism_id, identity)
        return SemanticResult(True, "consumed")

    def consume_debt(self, *, current_cycle: int) -> tuple[PolicyDebt, ...]:
        due = tuple(
            debt
            for debt in self.debts.values()
            if current_cycle >= debt.due_cycle
        )
        for debt in due:
            del self.debts[(debt.mechanism_id, debt.identity)]
        return due


@dataclass
class FormalSettlementGate:
    """#069 pre-resource-write gate; it never performs the settlement itself."""

    book: NativeCaseBook
    decisions: dict[CaseIdentity, bool] = field(default_factory=dict)

    def authorize(
        self, identity: CaseIdentity, route: PolicyRoute
    ) -> SemanticResult:
        if identity in self.decisions:
            return SemanticResult(False, "duplicate-gate")
        opened = self.book.open(69, identity, route, initial_state="PREPARED")
        if not opened.applied:
            return opened
        allowed = PolicyRoute(route) != PolicyRoute.C
        self.decisions[identity] = allowed
        return SemanticResult(True, "settlement-allowed" if allowed else "blocked")


@dataclass(frozen=True)
class ReviewerCandidate:
    reviewer_id: str
    peer_manager: bool = True
    conflicts_with: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ReviewerConclusion:
    reviewer_id: str
    identity: CaseIdentity
    evidence_revision: int
    outcome: str


@dataclass
class ReviewerRotation:
    identity: CaseIdentity
    candidates: tuple[ReviewerCandidate, ...]
    route: PolicyRoute
    reviewer_id: str | None = None
    independent: bool = False
    subject_recusal_used: bool = False
    owner_recusal_used: bool = False
    recused: set[str] = field(default_factory=set)
    conclusion: ReviewerConclusion | None = None

    def _next_candidate(self) -> ReviewerCandidate | None:
        for candidate in self.candidates:
            if (
                candidate.peer_manager
                and candidate.reviewer_id not in self.recused
                and candidate.reviewer_id
                not in {self.identity.owner_id, self.identity.subject_id}
            ):
                return candidate
        return None

    def assign(self) -> SemanticResult:
        if self.reviewer_id is not None:
            return SemanticResult(False, "duplicate-assignment")
        if self.route == PolicyRoute.C:
            return SemanticResult(False, "route-c-no-review-case")
        if self.route == PolicyRoute.B:
            self.reviewer_id = self.identity.owner_id
            self.independent = False
            return SemanticResult(True, "self-correction-disclosed")
        candidate = self._next_candidate()
        if candidate is None:
            self.reviewer_id = self.identity.owner_id
            return SemanticResult(True, "fallback-disclosed")
        self.reviewer_id = candidate.reviewer_id
        self.independent = True
        return SemanticResult(True, "independent-assigned")

    def recuse(self, *, party_id: str, reason: str) -> SemanticResult:
        if not reason or self.route != PolicyRoute.A or not self.reviewer_id:
            return SemanticResult(False, "recusal-not-authorized")
        if party_id == self.identity.subject_id:
            if self.subject_recusal_used:
                return SemanticResult(False, "subject-token-used")
        elif party_id == self.identity.owner_id:
            if self.owner_recusal_used:
                return SemanticResult(False, "owner-token-used")
        else:
            return SemanticResult(False, "not-a-party")
        current = next(
            (
                candidate
                for candidate in self.candidates
                if candidate.reviewer_id == self.reviewer_id
            ),
            None,
        )
        if current is None or party_id not in current.conflicts_with:
            return SemanticResult(False, "reason-not-grounded")
        if party_id == self.identity.subject_id:
            self.subject_recusal_used = True
        else:
            self.owner_recusal_used = True
        self.recused.add(self.reviewer_id)
        replacement = self._next_candidate()
        self.reviewer_id = (
            replacement.reviewer_id if replacement else self.identity.owner_id
        )
        self.independent = replacement is not None
        return SemanticResult(True, "replaced" if replacement else "fallback-disclosed")

    def conclude(
        self, *, evidence_revision: int, outcome: str
    ) -> SemanticResult:
        if self.conclusion is not None:
            return SemanticResult(False, "duplicate-conclusion")
        if not self.reviewer_id or evidence_revision < 1 or not outcome:
            return SemanticResult(False, "incomplete-conclusion")
        self.conclusion = ReviewerConclusion(
            self.reviewer_id, self.identity, evidence_revision, outcome
        )
        return SemanticResult(True, "concluded")


FAIRNESS_DIMENSIONS: Final[tuple[str, ...]] = (
    "newcomer",
    "transfer",
    "kin",
    "faction",
    "landed",
    "governor",
)


@dataclass(frozen=True)
class FairnessSample:
    identity: CaseIdentity
    groups: tuple[tuple[str, bool], ...]
    bottom: bool


@dataclass
class FairnessDashboard:
    samples: dict[CaseIdentity, FairnessSample] = field(default_factory=dict)
    outcomes: dict[CaseIdentity, bool] = field(default_factory=dict)

    def record(
        self,
        identity: CaseIdentity,
        *,
        route: PolicyRoute,
        groups: Mapping[str, bool],
        bottom: bool,
    ) -> SemanticResult:
        if PolicyRoute(route) == PolicyRoute.C:
            return SemanticResult(False, "route-c-no-aggregation")
        if identity in self.samples:
            return SemanticResult(False, "duplicate-sample")
        if set(groups) != set(FAIRNESS_DIMENSIONS):
            return SemanticResult(False, "incomplete-dimensions")
        self.samples[identity] = FairnessSample(
            identity, tuple(sorted(groups.items())), bool(bottom)
        )
        return SemanticResult(True, "sample-recorded")

    def resolve(self, identity: CaseIdentity, *, corrected: bool) -> SemanticResult:
        if identity not in self.samples:
            return SemanticResult(False, "missing-denominator")
        if identity in self.outcomes:
            return SemanticResult(False, "duplicate-outcome")
        self.outcomes[identity] = bool(corrected)
        return SemanticResult(True, "outcome-recorded")

    def group_counts(self, dimension: str) -> tuple[tuple[int, int], tuple[int, int]]:
        if dimension not in FAIRNESS_DIMENSIONS:
            raise ValueError("unknown fairness dimension")
        positive_n = negative_n = positive_corrected = negative_corrected = 0
        for identity, sample in self.samples.items():
            membership = dict(sample.groups)[dimension]
            if membership:
                positive_n += 1
                positive_corrected += int(self.outcomes.get(identity, False))
            else:
                negative_n += 1
                negative_corrected += int(self.outcomes.get(identity, False))
        return (
            (positive_n, positive_corrected),
            (negative_n, negative_corrected),
        )

    def anomalies(self, *, minimum_group_size: int = 3) -> tuple[str, ...]:
        result: list[str] = []
        for dimension in FAIRNESS_DIMENSIONS:
            (positive_n, positive_corrected), (
                negative_n,
                negative_corrected,
            ) = self.group_counts(dimension)
            if min(positive_n, negative_n) < minimum_group_size:
                continue
            if positive_corrected * negative_n != negative_corrected * positive_n:
                result.append(dimension)
        return tuple(result)


class SkipLevelState(str, Enum):
    OPEN = "OPEN"
    REMANDED = "REMANDED"
    CLOSED = "CLOSED"
    CONSUMED = "CONSUMED"


@dataclass
class SkipLevelSeatPool:
    capacity: int
    reservations: set[CaseIdentity] = field(default_factory=set)

    def reserve(self, identity: CaseIdentity) -> bool:
        if identity in self.reservations or len(self.reservations) >= self.capacity:
            return False
        self.reservations.add(identity)
        return True

    def release(self, identity: CaseIdentity) -> bool:
        if identity not in self.reservations:
            return False
        self.reservations.remove(identity)
        return True


@dataclass
class SkipLevelCase:
    identity: CaseIdentity
    route: PolicyRoute
    reviewer_id: str
    state: SkipLevelState = SkipLevelState.OPEN
    evidence_revision: int = 1
    remand_consumer_case: int | None = None
    direct_grade_write: bool = False

    def resolve(
        self, *, evidence_strength: int, seats: SkipLevelSeatPool
    ) -> SemanticResult:
        if self.state != SkipLevelState.OPEN:
            return SemanticResult(False, "duplicate-or-stale")
        seats.release(self.identity)
        if evidence_strength >= 2:
            self.state = SkipLevelState.REMANDED
            self.evidence_revision += 1
            return SemanticResult(True, "remanded-to-direct-manager")
        self.state = SkipLevelState.CLOSED
        return SemanticResult(True, "closed-no-finding")

    def consume_next_result(self, next_identity: CaseIdentity) -> SemanticResult:
        if self.state != SkipLevelState.REMANDED:
            return SemanticResult(False, "no-active-remand")
        if (
            next_identity.owner_id != self.identity.owner_id
            or next_identity.subject_id != self.identity.subject_id
            or next_identity.cycle_serial <= self.identity.cycle_serial
        ):
            return SemanticResult(False, "wrong-remand-consumer")
        self.state = SkipLevelState.CONSUMED
        self.remand_consumer_case = next_identity.case_serial
        return SemanticResult(True, "consumed-by-next-direct-result")


class MetricDefectState(str, Enum):
    OPEN = "OPEN"
    REPAIRED = "REPAIRED"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    SUPPRESSED = "SUPPRESSED"
    VERIFIED = "VERIFIED"
    REPEATED = "REPEATED"


@dataclass
class MetricDefectCase:
    identity: CaseIdentity
    route: PolicyRoute
    defect_id: str
    defect_type: int
    evidence_hash: str
    state: MetricDefectState = MetricDefectState.OPEN
    consumer_case: int | None = None

    def resolve(self, *, supported: bool) -> SemanticResult:
        if self.state != MetricDefectState.OPEN:
            return SemanticResult(False, "duplicate-resolution")
        if self.route == PolicyRoute.C:
            return SemanticResult(False, "route-c-no-ticket")
        if self.route == PolicyRoute.B:
            self.state = MetricDefectState.SUPPRESSED
            return SemanticResult(True, "suppressed-evidence-preserved")
        self.state = (
            MetricDefectState.REPAIRED if supported else MetricDefectState.ACCEPTED_RISK
        )
        return SemanticResult(True, self.state.value.lower())

    def consume_later(
        self, next_identity: CaseIdentity, *, repeated_defect_type: int | None
    ) -> SemanticResult:
        if self.state not in {
            MetricDefectState.REPAIRED,
            MetricDefectState.ACCEPTED_RISK,
            MetricDefectState.SUPPRESSED,
        }:
            return SemanticResult(False, "not-consumable")
        if (
            next_identity.owner_id != self.identity.owner_id
            or next_identity.subject_id != self.identity.subject_id
            or next_identity.cycle_serial <= self.identity.cycle_serial
        ):
            return SemanticResult(False, "wrong-consumer")
        self.consumer_case = next_identity.case_serial
        if (
            self.state == MetricDefectState.SUPPRESSED
            and repeated_defect_type == self.defect_type
        ):
            self.state = MetricDefectState.REPEATED
            return SemanticResult(True, "suppression-liability")
        self.state = MetricDefectState.VERIFIED
        return SemanticResult(True, "later-version-verified")


class AccessRole(str, Enum):
    SUBJECT = "subject"
    DIRECT_MANAGER = "direct_manager"
    SKIP_LEVEL = "skip_level"
    CENTRAL_REVIEW = "central_review"


@dataclass(frozen=True)
class AccessReceipt:
    actor_id: str
    role: AccessRole
    visible_fields: int
    raw_evidence: bool


@dataclass
class InformationAccessLedger:
    identity: CaseIdentity
    direct_grade_writer: str
    receipts: list[AccessReceipt] = field(default_factory=list)

    def read(
        self, *, actor_id: str, role: AccessRole, route: PolicyRoute
    ) -> AccessReceipt | None:
        role = AccessRole(role)
        if role == AccessRole.SUBJECT and actor_id != self.identity.subject_id:
            return None
        if role == AccessRole.DIRECT_MANAGER and actor_id != self.identity.owner_id:
            return None
        raw = role in {AccessRole.DIRECT_MANAGER, AccessRole.CENTRAL_REVIEW}
        if PolicyRoute(route) == PolicyRoute.B and role != AccessRole.CENTRAL_REVIEW:
            raw = False
        visible = 8 if raw else 4
        receipt = AccessReceipt(actor_id, role, visible, raw)
        self.receipts.append(receipt)
        return receipt

    def can_write_grade(self, actor_id: str) -> bool:
        return actor_id == self.direct_grade_writer == self.identity.owner_id
