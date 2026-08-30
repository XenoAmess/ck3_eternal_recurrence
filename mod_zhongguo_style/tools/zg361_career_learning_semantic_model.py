#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic semantic model for Career/Learning mechanisms 312-333.

This is the L0 authority for the business objects projected by
``gen_361_career_learning_runtime.py``.  It deliberately models more than a
policy receipt: vacancies, offers, trials, release duties, learning ledgers,
mentor relationships and succession drills all own an identity, ACL,
resources, deadlines and a named consumer.

Passing this model is not CK3-live evidence.  It proves deterministic domain
semantics, conservation, stale/duplicate behavior and negative paths only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Final


HONEST_READINESS: Final[str] = "python-l0-model"
EXPECTED_IDS: Final[tuple[int, ...]] = tuple(range(312, 334))


class Route(IntEnum):
    A = 1
    B = 2
    C = 3


class ResultCode(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    STALE = "stale"
    RESOLVED = "resolved"


class SemanticError(ValueError):
    """A typed invalid command; no mutation is allowed before it is raised."""


@dataclass(frozen=True, slots=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        if not self.owner_id or not self.subject_id:
            raise SemanticError("owner and subject identities must be non-empty")
        if self.owner_id == self.subject_id:
            raise SemanticError("owner and subject must be distinct")
        if (
            isinstance(self.cycle_serial, bool)
            or not isinstance(self.cycle_serial, int)
            or self.cycle_serial < 1
        ):
            raise SemanticError("cycle_serial must be an integer >= 1")
        if (
            isinstance(self.case_serial, bool)
            or not isinstance(self.case_serial, int)
            or self.case_serial < 1
        ):
            raise SemanticError("case_serial must be an integer >= 1")


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


class ObjectKind(str, Enum):
    VACANCY = "vacancy"
    REFERENCE = "reference"
    TRANSFER_OFFER = "transfer-offer"
    TRIAL_ASSIGNMENT = "trial-assignment"
    PAY_MAPPING = "pay-mapping"
    APPLICATION_ACL = "application-acl"
    APPLICATION_QUOTA = "application-quota"
    RELEASE_OBLIGATION = "release-obligation"
    EXIT_SIGNAL = "exit-signal"
    ALUMNI_RELATION = "alumni-relation"
    RETURNEE_CASE = "returnee-case"
    LEARNING_BUDGET = "learning-budget"
    LEARNING_PROGRESS = "learning-progress"
    COMPETENCE_ASSESSMENT = "competence-assessment"
    CONFERENCE_ADOPTION = "conference-adoption"
    TEACHING_ATTRIBUTION = "teaching-attribution"
    COMMUNITY_ARTIFACT = "community-artifact"
    MENTOR_MATCH = "mentor-match"
    RESKILL_CASE = "reskill-case"
    PROTECTED_TIME_LOAN = "protected-time-loan"
    SUCCESSION_DRILL = "succession-drill"
    TRAINING_COMMITMENT = "training-commitment"


@dataclass(frozen=True, slots=True)
class MechanismSpec:
    mechanism_id: int
    kind: ObjectKind
    consumer_key: str
    state_a: str
    state_b: str
    deadlines: tuple[tuple[Route, int], ...] = ()
    charges: tuple[tuple[Route, int, int], ...] = ()

    def deadline_for(self, route: Route) -> int | None:
        return dict(self.deadlines).get(route)

    def charge_for(self, route: Route) -> tuple[int, int]:
        for candidate, treasury, personal in self.charges:
            if candidate is route:
                return treasury, personal
        return 0, 0


def _spec(
    mechanism_id: int,
    kind: ObjectKind,
    consumer: str,
    state_a: str,
    state_b: str,
    *,
    deadlines: dict[Route, int] | None = None,
    charges: dict[Route, tuple[int, int]] | None = None,
) -> MechanismSpec:
    return MechanismSpec(
        mechanism_id,
        kind,
        consumer,
        state_a,
        state_b,
        tuple(sorted((deadlines or {}).items(), key=lambda row: int(row[0]))),
        tuple(
            (route, amount[0], amount[1])
            for route, amount in sorted((charges or {}).items(), key=lambda row: int(row[0]))
        ),
    )


SPECS: Final[dict[int, MechanismSpec]] = {
    312: _spec(312, ObjectKind.VACANCY, "consume_vacancy", "public-open", "phantom-audited", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}),
    313: _spec(313, ObjectKind.REFERENCE, "consume_reference", "facts-frozen", "retaliation-audited", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}),
    314: _spec(314, ObjectKind.TRANSFER_OFFER, "consume_transfer_offer", "accepted-funded", "declined-no-penalty", deadlines={Route.A: 190, Route.C: 30}, charges={Route.A: (15, 5)}),
    315: _spec(315, ObjectKind.TRIAL_ASSIGNMENT, "consume_trial_assignment", "trial-active", "returned-to-source", deadlines={Route.A: 90, Route.B: 90, Route.C: 30}),
    316: _spec(316, ObjectKind.PAY_MAPPING, "consume_pay_mapping", "phased-protection", "immediate-cut", deadlines={Route.A: 90, Route.C: 365}),
    317: _spec(317, ObjectKind.APPLICATION_ACL, "consume_application_acl", "confidential", "leak-audited", deadlines={Route.B: 7, Route.C: 7}),
    318: _spec(318, ObjectKind.APPLICATION_QUOTA, "consume_application_quota", "slot-consumed", "timeout-refunded", deadlines={Route.B: 14, Route.C: 14}),
    319: _spec(319, ObjectKind.RELEASE_OBLIGATION, "consume_release_obligation", "released", "counteroffer-pending", deadlines={Route.A: 30, Route.B: 90, Route.C: 45}),
    320: _spec(320, ObjectKind.EXIT_SIGNAL, "consume_exit_signal", "threshold-audited", "reclassification-preserved", deadlines={Route.A: 180, Route.B: 180, Route.C: 180}),
    321: _spec(321, ObjectKind.ALUMNI_RELATION, "consume_alumni_relation", "consented-contact", "no-contact", deadlines={Route.A: 365, Route.C: 30}, charges={Route.A: (4, 2)}),
    322: _spec(322, ObjectKind.RETURNEE_CASE, "consume_returnee_case", "history-linked", "wipe-blocked", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}),
    323: _spec(323, ObjectKind.LEARNING_BUDGET, "consume_learning_budget", "money-and-time-funded", "certificate-only", deadlines={Route.A: 365, Route.B: 365, Route.C: 365}, charges={Route.A: (8, 2), Route.B: (8, 2)}),
    324: _spec(324, ObjectKind.LEARNING_PROGRESS, "consume_learning_progress", "outcome-proved", "completion-only", deadlines={Route.A: 90, Route.B: 90, Route.C: 90}),
    325: _spec(325, ObjectKind.COMPETENCE_ASSESSMENT, "consume_competence_assessment", "valid-practical-test", "invalid-test-audited", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}),
    326: _spec(326, ObjectKind.CONFERENCE_ADOPTION, "consume_conference_adoption", "artifact-adopted", "exposure-only", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}, charges={Route.A: (9, 3), Route.B: (9, 3)}),
    327: _spec(327, ObjectKind.TEACHING_ATTRIBUTION, "consume_teaching_attribution", "application-attributed", "attendance-only", deadlines={Route.A: 30, Route.B: 30, Route.C: 30}),
    328: _spec(328, ObjectKind.COMMUNITY_ARTIFACT, "consume_community_artifact", "maintained-adopted", "abandoned", deadlines={Route.A: 90, Route.B: 90, Route.C: 90}),
    329: _spec(329, ObjectKind.MENTOR_MATCH, "consume_mentor_match", "mentor-active", "rematched-once", deadlines={Route.A: 190, Route.B: 190, Route.C: 190}),
    330: _spec(330, ObjectKind.RESKILL_CASE, "consume_reskill_case", "reskill-active", "external-hire-fairness-debt", deadlines={Route.A: 90, Route.B: 30, Route.C: 180}, charges={Route.A: (15, 5), Route.B: (15, 5)}),
    331: _spec(331, ObjectKind.PROTECTED_TIME_LOAN, "consume_protected_time_loan", "crisis-loan-due", "late-repayment-debt", deadlines={Route.A: 365, Route.B: 365, Route.C: 365}),
    332: _spec(332, ObjectKind.SUCCESSION_DRILL, "consume_succession_drill", "safe-success", "safe-gap", deadlines={Route.A: 90, Route.B: 90, Route.C: 30}),
    333: _spec(333, ObjectKind.TRAINING_COMMITMENT, "consume_training_commitment", "bound-service", "early-exit-recovery", deadlines={Route.A: 360, Route.B: 90}, charges={Route.A: (18, 6), Route.B: (18, 6), Route.C: (18, 6)}),
}


@dataclass(slots=True)
class AccessControl:
    viewers: set[str]
    leaked: bool = False

    def can_view(self, actor_id: str) -> bool:
        return actor_id in self.viewers


@dataclass(slots=True)
class Deadline:
    mechanism_id: int
    identity: CaseIdentity
    route: Route
    due_day: int
    pending: bool = True
    resolved: bool = False


@dataclass(slots=True)
class GovernanceDebt:
    mechanism_id: int
    identity: CaseIdentity
    due_cycle: int
    due_day: int | None
    settled: bool = False


@dataclass(frozen=True, slots=True)
class RedundancyEvidence:
    subject_id: str
    reason_code: int
    treasury_paid: int
    personal_received: int
    actual_exit: bool
    hc_released: bool
    state: int

    def exempts_training_recovery(self, expected_subject: str) -> bool:
        return (
            self.subject_id == expected_subject
            and self.reason_code == 1
            and self.treasury_paid == 50
            and self.personal_received == 50
            and self.actual_exit
            and self.hc_released
            and self.state in {3, 4}
        )


@dataclass(slots=True)
class SemanticObject:
    mechanism_id: int
    object_id: str
    kind: ObjectKind
    identity: CaseIdentity
    route: Route
    state: str
    consumer_key: str
    acl: AccessControl
    relations: dict[str, str]
    facts: dict[str, int | str | bool]
    consumed: bool = False
    consumer_revision: int = 0


@dataclass(slots=True)
class DualLedger:
    opening_treasury: int = 500
    opening_personal: int = 200
    treasury: int = field(init=False)
    personal: int = field(init=False)
    payments: dict[int, tuple[int, int]] = field(default_factory=dict)
    recoveries: dict[int, tuple[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.opening_treasury < 0 or self.opening_personal < 0:
            raise SemanticError("opening funds must be non-negative")
        self.treasury = self.opening_treasury
        self.personal = self.opening_personal

    def precheck(self, mechanism_id: int, treasury: int, personal: int) -> None:
        if mechanism_id in self.payments:
            raise SemanticError("dual payment is single-use")
        if treasury > self.treasury or personal > self.personal:
            raise SemanticError("dual payment is not fully funded")

    def pay(self, mechanism_id: int, treasury: int, personal: int) -> None:
        if treasury == 0 and personal == 0:
            return
        self.precheck(mechanism_id, treasury, personal)
        self.treasury -= treasury
        self.personal -= personal
        self.payments[mechanism_id] = (treasury, personal)
        self.assert_conserved()

    def recover(self, mechanism_id: int, treasury: int, personal: int) -> None:
        if mechanism_id not in self.payments or mechanism_id in self.recoveries:
            raise SemanticError("recovery requires one unsettled original payment")
        paid_treasury, paid_personal = self.payments[mechanism_id]
        if treasury > paid_treasury or personal > paid_personal:
            raise SemanticError("recovery cannot exceed the original split")
        self.treasury += treasury
        self.personal += personal
        self.recoveries[mechanism_id] = (treasury, personal)
        self.assert_conserved()

    def assert_conserved(self) -> None:
        paid_t = sum(row[0] for row in self.payments.values())
        paid_p = sum(row[1] for row in self.payments.values())
        recovered_t = sum(row[0] for row in self.recoveries.values())
        recovered_p = sum(row[1] for row in self.recoveries.values())
        if self.opening_treasury != self.treasury + paid_t - recovered_t:
            raise SemanticError("treasury ledger is not conserved")
        if self.opening_personal != self.personal + paid_p - recovered_p:
            raise SemanticError("personal ledger is not conserved")


@dataclass(slots=True)
class CapacityLedger:
    opening: dict[str, int] = field(
        default_factory=lambda: {
            "hc": 2,
            "application_slots": 2,
            "learning_gold": 40,
            "protected_hours": 20,
            "teaching_hours": 40,
            "community_hours": 10,
            "mentor_hours": 12,
            "succession_slots": 1,
        }
    )
    available: dict[str, int] = field(init=False)
    used: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.opening.values()):
            raise SemanticError("opening capacities must be non-negative")
        self.available = dict(self.opening)
        self.used = {key: 0 for key in self.opening}

    def consume(self, key: str, amount: int) -> None:
        if key not in self.available or amount < 1:
            raise SemanticError("unknown capacity or invalid amount")
        if self.available[key] < amount:
            raise SemanticError(f"insufficient {key}")
        self.available[key] -= amount
        self.used[key] += amount
        self.assert_conserved()

    def release(self, key: str, amount: int) -> None:
        if key not in self.used or amount < 1 or self.used[key] < amount:
            raise SemanticError("cannot release unconsumed capacity")
        self.used[key] -= amount
        self.available[key] += amount
        self.assert_conserved()

    def assert_conserved(self) -> None:
        for key, opening in self.opening.items():
            if opening != self.available[key] + self.used[key]:
                raise SemanticError(f"{key} capacity is not conserved")


@dataclass(slots=True)
class OperationRecord:
    revision: int = 0
    route: Route | None = None
    state: str = "open"
    consumer_key: str | None = None


@dataclass(slots=True)
class CareerLearningRuntime:
    identity: CaseIdentity
    now_day: int = 100
    mentor_id: str = "external-mentor"
    real_crisis: bool = True
    records: dict[int, OperationRecord] = field(init=False)
    objects: dict[int, SemanticObject] = field(default_factory=dict)
    deadlines: dict[int, Deadline] = field(default_factory=dict)
    debts: dict[int, GovernanceDebt] = field(default_factory=dict)
    applied_serials: set[str] = field(default_factory=set)
    ledger: DualLedger = field(default_factory=DualLedger)
    capacity: CapacityLedger = field(default_factory=CapacityLedger)
    audit: list[tuple[int, Route, str]] = field(default_factory=list)
    market_trust: int = 0
    manager_score: int = 0
    performance_credit: int = 0

    def __post_init__(self) -> None:
        validate_specs()
        if not self.mentor_id or self.mentor_id in {self.identity.owner_id, self.identity.subject_id}:
            raise SemanticError("mentor must be a distinct real character identity")
        if not isinstance(self.real_crisis, bool):
            raise SemanticError("real_crisis must be bool")
        self.records = {mechanism_id: OperationRecord() for mechanism_id in EXPECTED_IDS}

    def token(self, mechanism_id: int) -> OperationToken:
        if mechanism_id not in self.records:
            raise SemanticError("mechanism outside Career/Learning slice")
        return OperationToken(self.identity, mechanism_id, self.records[mechanism_id].revision)

    def apply(
        self,
        token: OperationToken,
        operation_serial: str,
        route: Route,
    ) -> OperationResult:
        if not isinstance(operation_serial, str) or not operation_serial.strip():
            raise SemanticError("operation_serial must be non-empty")
        if token.mechanism_id not in self.records:
            raise SemanticError("mechanism outside Career/Learning slice")
        if operation_serial in self.applied_serials:
            record = self.records[token.mechanism_id]
            return OperationResult(token.mechanism_id, False, ResultCode.DUPLICATE, record.revision)
        record = self.records[token.mechanism_id]
        if token != self.token(token.mechanism_id) or record.revision != 0:
            return OperationResult(token.mechanism_id, False, ResultCode.STALE, record.revision)
        try:
            route = Route(route)
        except (TypeError, ValueError) as exc:
            raise SemanticError("route must be A, B or C") from exc

        spec = SPECS[token.mechanism_id]
        if spec.mechanism_id == 331 and route in {Route.A, Route.B} and not self.real_crisis:
            raise SemanticError("protected time may be borrowed only for a real crisis")
        treasury, personal = spec.charge_for(route)
        if treasury or personal:
            self.ledger.precheck(spec.mechanism_id, treasury, personal)
        self._precheck_capacity(spec.mechanism_id, route)

        if route is Route.C:
            due_days = spec.deadline_for(route)
            self.debts[spec.mechanism_id] = GovernanceDebt(
                spec.mechanism_id,
                self.identity,
                self.identity.cycle_serial + 1,
                self.now_day + due_days if due_days is not None else None,
            )
            if due_days is not None:
                self.deadlines[spec.mechanism_id] = Deadline(
                    spec.mechanism_id,
                    self.identity,
                    route,
                    self.now_day + due_days,
                )
            terminal_state = "deferred-with-debt"
            if treasury or personal:
                self.ledger.pay(spec.mechanism_id, treasury, personal)
        else:
            if treasury or personal:
                self.ledger.pay(spec.mechanism_id, treasury, personal)
            obj = self._make_object(spec, route)
            self.objects[spec.mechanism_id] = obj
            self._consume(obj)
            terminal_state = obj.state
            due_days = spec.deadline_for(route)
            if due_days is not None:
                self.deadlines[spec.mechanism_id] = Deadline(
                    spec.mechanism_id,
                    self.identity,
                    route,
                    self.now_day + due_days,
                )

        record.revision = 1
        record.route = route
        record.state = terminal_state
        record.consumer_key = spec.consumer_key
        self.applied_serials.add(operation_serial)
        self.audit.append((spec.mechanism_id, route, spec.consumer_key))
        self.assert_invariants()
        return OperationResult(spec.mechanism_id, True, ResultCode.APPLIED, 1)

    def resolve_deadline(
        self,
        mechanism_id: int,
        *,
        now_day: int,
        identity: CaseIdentity,
        redundancy_evidence: RedundancyEvidence | None = None,
    ) -> OperationResult:
        if mechanism_id not in self.deadlines:
            raise SemanticError("mechanism has no deadline object")
        deadline = self.deadlines[mechanism_id]
        record = self.records[mechanism_id]
        if identity != deadline.identity:
            return OperationResult(mechanism_id, False, ResultCode.STALE, record.revision)
        if deadline.resolved or not deadline.pending:
            return OperationResult(mechanism_id, False, ResultCode.DUPLICATE, record.revision)
        if now_day < deadline.due_day:
            raise SemanticError("deadline cannot resolve early")
        deadline.pending = False
        deadline.resolved = True
        route = deadline.route
        if route is Route.C:
            self.debts[mechanism_id].settled = False
            self.manager_score -= 1
        else:
            obj = self.objects[mechanism_id]
            obj.facts["deadline_resolved"] = True
            obj.state = f"{obj.state}:resolved"
            if mechanism_id == 333 and route is Route.B:
                if redundancy_evidence is not None and redundancy_evidence.exempts_training_recovery(
                    self.identity.subject_id
                ):
                    obj.facts["organization_layoff_exempt"] = True
                    obj.facts["outstanding"] = 0
                else:
                    self.ledger.recover(333, 13, 5)
                    obj.facts["recovered"] = 18
            if mechanism_id == 331 and route is Route.B:
                self.manager_score -= 10
        self.assert_invariants()
        return OperationResult(mechanism_id, True, ResultCode.RESOLVED, record.revision)

    def hire_vacancy(self, candidate_id: str) -> None:
        vacancy = self.objects.get(312)
        if vacancy is None or vacancy.kind is not ObjectKind.VACANCY:
            raise SemanticError("a vacancy object is required")
        if vacancy.facts.get("hire_count", 0) != 0:
            raise SemanticError("one vacancy can hire only once")
        if not candidate_id:
            raise SemanticError("candidate identity must be non-empty")
        vacancy.facts["hire_count"] = 1
        vacancy.relations["occupant"] = candidate_id
        if self.capacity.used["hc"]:
            vacancy.state = "filled"

    def _precheck_capacity(self, mechanism_id: int, route: Route) -> None:
        requirements: dict[int, tuple[str, int] | None] = {
            312: ("hc", 1) if route is Route.A else None,
            318: ("application_slots", 1) if route is Route.A else None,
            323: ("learning_gold", 10) if route in {Route.A, Route.B} else None,
            327: ("teaching_hours", 8) if route in {Route.A, Route.B} else None,
            328: ("community_hours", 6) if route in {Route.A, Route.B} else None,
            329: ("mentor_hours", 6) if route in {Route.A, Route.B} else None,
            331: ("protected_hours", 4) if route in {Route.A, Route.B} else None,
            332: ("succession_slots", 1) if route in {Route.A, Route.B} else None,
        }
        requirement = requirements.get(mechanism_id)
        if requirement is not None:
            key, amount = requirement
            if self.capacity.available[key] < amount:
                raise SemanticError(f"insufficient {key}")
        if mechanism_id == 323 and route is Route.A and self.capacity.available["protected_hours"] < 5:
            raise SemanticError("insufficient protected_hours")

    def _acl(self, mechanism_id: int, route: Route) -> AccessControl:
        owner = self.identity.owner_id
        subject = self.identity.subject_id
        viewers = {owner, subject}
        leaked = False
        if mechanism_id == 312:
            viewers.add("all-eligible" if route is Route.A else "manager-circle")
        elif mechanism_id == 313:
            viewers.add("target-manager" if route is Route.A else "private-contact")
        elif mechanism_id == 317:
            viewers.add("final-interviewer")
            if route is Route.B:
                viewers.add("source-manager")
                leaked = True
        elif mechanism_id == 320:
            viewers.discard(subject)
            viewers.add("aggregate-auditor")
        elif mechanism_id == 329:
            viewers.add(self.mentor_id)
        return AccessControl(viewers, leaked)

    def _make_object(self, spec: MechanismSpec, route: Route) -> SemanticObject:
        owner = self.identity.owner_id
        subject = self.identity.subject_id
        relations: dict[str, str] = {"owner": owner, "subject": subject}
        facts: dict[str, int | str | bool] = {"route": int(route), "created_day": self.now_day}
        state = spec.state_a if route is Route.A else spec.state_b
        mid = spec.mechanism_id

        if mid == 312:
            facts.update(legal_hc=route is Route.A, pay_band=4, goal_version=1, hire_count=0)
            relations["reporting_manager"] = owner
        elif mid == 313:
            facts.update(achievement_refs=2, risk_refs=1, pip_ref=1, handover_ref=1, immutable=True, retaliation=route is Route.B)
            relations["source_manager"] = owner
        elif mid == 314:
            facts.update(lump_sum=10 if route is Route.A else 0, allowance=6 if route is Route.A else 0, family_support=4 if route is Route.A else 0, performance_delta=0)
            relations["offered_official"] = subject
        elif mid == 315:
            facts.update(trial_days=90, source_share=40, target_share=60, failed_is_low_grade=False)
            relations.update(source_official=subject, target_manager=owner)
        elif mid == 316:
            facts.update(professional_base=30, historical_paid_immutable=True, step_1=38 if route is Route.A else 35, step_3=35)
            relations["mapped_official"] = subject
        elif mid == 317:
            facts.update(stage="initial" if route is Route.A else "leaked", access_log_rows=1, retaliation_audit=route is Route.B)
        elif mid == 318:
            facts.update(formal_limit=2, used=1 if route is Route.A else 0, timeout_refunded=route is Route.B)
        elif mid == 319:
            facts.update(counteroffer_count=1, release_days=30, promise_days=90, promise_fulfilled=route is Route.A)
            relations.update(releasing_manager=owner, released_official=subject)
        elif mid == 320:
            facts.update(named=1, anonymous=1, declined=1, same_issue=2, original_reason_preserved=True, reclassified=route is Route.B)
        elif mid == 321:
            facts.update(consent=route is Route.A, maintenance_count=1 if route is Route.A else 0, humiliation_history_immutable=True)
            relations["alumnus"] = subject
        elif mid == 322:
            facts.update(old_case_links=2, old_misconduct_links=1, external_evidence_links=1, history_wipe_blocked=route is Route.B, new_cohort=1)
            relations["returnee"] = subject
        elif mid == 323:
            facts.update(gold_allocated=10, hours_allocated=5 if route is Route.A else 0, completion_credit=0, certificate_only=route is Route.B)
            relations["learner"] = subject
        elif mid == 324:
            facts.update(completion=True, application=route is Route.A, outcome=route is Route.A, observed_delta=12 if route is Route.A else 0)
            relations["learner"] = subject
        elif mid == 325:
            facts.update(certificate=True, practical_score=30, threshold=60, test_valid=route is Route.A, owner_audit=route is Route.B, automatic_low_grade=False)
            relations["training_owner"] = owner
        elif mid == 326:
            facts.update(days_away=4, artifact_adopted=route is Route.A, adopted_value=6 if route is Route.A else 0, exposure=2, opportunity_cost=4)
            relations["delegate"] = subject
        elif mid == 327:
            facts.update(teaching_hours=8, attendees=2, applying_attendees=1 if route is Route.A else 0, teacher_share=60, applicator_share=40)
            relations.update(teacher=subject, application_owner=owner)
        elif mid == 328:
            facts.update(artifacts=2, maintainers=1 if route is Route.A else 0, contribution_hours=6, adopting_teams=2 if route is Route.A else 0)
            relations["maintainer"] = subject
        elif mid == 329:
            facts.update(active_mentor_count=1, committed_hours=6, rematch_used=route is Route.B, deadline_unchanged=True)
            relations.update(mentor=self.mentor_id, mentee=subject)
        elif mid == 330:
            facts.update(training_days=90, assessment=50, threshold=70, role_identity_conserved=True, fairness_debt=route is Route.B, failed_is_low_grade=False)
            relations.update(affected_official=subject, target_role_owner=owner)
        elif mid == 331:
            facts.update(total_capacity=100, protected=10, borrowed=4, delivery=94, real_crisis=True, repaid=route is Route.A)
            relations["borrower"] = owner
        elif mid == 332:
            facts.update(safe_simulation=True, readiness_before=40, readiness_after=50 if route is Route.A else 42, success=route is Route.A, veto_used=route is Route.B, real_incident=False, automatic_low_grade=False)
            relations.update(incumbent=owner, candidate=subject)
        elif mid == 333:
            facts.update(training_cost=24, service_days=360, monthly_reduction=2, outstanding=0 if route is Route.A else 18, application=route is Route.A, performance_credit=1 if route is Route.A else 0)
            relations["bound_official"] = subject
        else:  # pragma: no cover - registry validation makes this unreachable
            raise SemanticError("missing business object builder")

        return SemanticObject(
            mechanism_id=mid,
            object_id=f"{spec.kind.value}:{self.identity.case_serial}:{mid}",
            kind=spec.kind,
            identity=self.identity,
            route=route,
            state=state,
            consumer_key=spec.consumer_key,
            acl=self._acl(mid, route),
            relations=relations,
            facts=facts,
        )

    def _consume(self, obj: SemanticObject) -> None:
        mid = obj.mechanism_id
        route = obj.route
        if obj.consumed:
            raise SemanticError("consumer is single-use")
        if mid == 312:
            if route is Route.A:
                self.capacity.consume("hc", 1)
            else:
                self.market_trust -= 2
        elif mid == 313 and route is Route.B:
            self.manager_score -= 2
        elif mid == 317 and route is Route.B:
            self.manager_score -= 2
        elif mid == 318 and route is Route.A:
            self.capacity.consume("application_slots", 1)
        elif mid == 319 and route is Route.B:
            self.manager_score -= 2
        elif mid == 321 and route is Route.B:
            self.market_trust -= 1
        elif mid == 323:
            self.capacity.consume("learning_gold", 10)
            if route is Route.A:
                self.capacity.consume("protected_hours", 5)
        elif mid == 324 and route is Route.A:
            self.performance_credit += 12
        elif mid == 325 and route is Route.B:
            self.manager_score -= 1
        elif mid == 326 and route is Route.A:
            self.performance_credit += 6
        elif mid == 327:
            self.capacity.consume("teaching_hours", 8)
            if route is Route.A:
                self.performance_credit += 6
        elif mid == 328:
            self.capacity.consume("community_hours", 6)
            if route is Route.A:
                self.performance_credit += 2
        elif mid == 329:
            self.capacity.consume("mentor_hours", 6)
            if route is Route.A:
                self.performance_credit += 1
        elif mid == 330 and route is Route.B:
            self.manager_score -= 1
        elif mid == 331:
            self.capacity.consume("protected_hours", 4)
            if route is Route.B:
                self.manager_score -= 1
        elif mid == 332:
            self.capacity.consume("succession_slots", 1)
        elif mid == 333 and route is Route.A:
            self.performance_credit += 1
        obj.consumed = True
        obj.consumer_revision += 1

    def assert_invariants(self) -> None:
        self.ledger.assert_conserved()
        self.capacity.assert_conserved()
        for mechanism_id, obj in self.objects.items():
            spec = SPECS[mechanism_id]
            if obj.identity != self.identity or obj.consumer_key != spec.consumer_key:
                raise SemanticError("object escaped its frozen identity/consumer")
            if not obj.consumed or obj.consumer_revision != 1:
                raise SemanticError("business object must be consumed exactly once")
            if obj.relations.get("owner") != self.identity.owner_id:
                raise SemanticError("object owner relation drifted")
            if obj.relations.get("subject") != self.identity.subject_id:
                raise SemanticError("object subject relation drifted")
        for mechanism_id, deadline in self.deadlines.items():
            if deadline.identity != self.identity or deadline.mechanism_id != mechanism_id:
                raise SemanticError("deadline escaped its frozen identity")
        for mechanism_id, debt in self.debts.items():
            if debt.identity != self.identity or debt.due_cycle != self.identity.cycle_serial + 1:
                raise SemanticError("governance debt identity/due cycle drifted")

    def snapshot(self) -> tuple[object, ...]:
        return (
            tuple((mid, row.revision, row.route, row.state, row.consumer_key) for mid, row in sorted(self.records.items())),
            tuple((mid, obj.object_id, obj.state, obj.route, tuple(sorted(obj.acl.viewers)), obj.acl.leaked, tuple(sorted(obj.relations.items())), tuple(sorted(obj.facts.items())), obj.consumer_revision) for mid, obj in sorted(self.objects.items())),
            tuple((mid, row.route, row.due_day, row.pending, row.resolved) for mid, row in sorted(self.deadlines.items())),
            tuple((mid, row.due_cycle, row.due_day, row.settled) for mid, row in sorted(self.debts.items())),
            self.ledger.treasury,
            self.ledger.personal,
            tuple(sorted(self.ledger.payments.items())),
            tuple(sorted(self.ledger.recoveries.items())),
            tuple(sorted(self.capacity.available.items())),
            tuple(sorted(self.capacity.used.items())),
            tuple(self.audit),
            self.market_trust,
            self.manager_score,
            self.performance_credit,
        )


def validate_specs() -> None:
    if tuple(SPECS) != EXPECTED_IDS:
        raise SemanticError("career/learning registry must cover 312-333 exactly")
    if len({row.kind for row in SPECS.values()}) != len(EXPECTED_IDS):
        raise SemanticError("each mechanism must own a distinct object kind")
    if len({row.consumer_key for row in SPECS.values()}) != len(EXPECTED_IDS):
        raise SemanticError("each mechanism must own a distinct consumer")
    for mechanism_id, row in SPECS.items():
        if mechanism_id != row.mechanism_id:
            raise SemanticError("registry key mismatch")
        if not row.state_a or not row.state_b or row.state_a == row.state_b:
            raise SemanticError("A/B must have distinct terminal business states")
        for route, days in row.deadlines:
            if not isinstance(route, Route) or days < 1:
                raise SemanticError("deadline route/days invalid")
        for route, treasury, personal in row.charges:
            if not isinstance(route, Route) or treasury < 0 or personal < 0:
                raise SemanticError("charge route/amount invalid")


validate_specs()
