"""Small, honest source model for the first v0.4 361 runtime slice.

This module is deliberately CK3-independent.  It specifies the four mechanisms
in the first vertical slice and models the delivery/settlement invariants that
the eventual Paradox-script runtime must preserve.  Passing these model tests
means ``static-ready`` only; it is not fixture or live-game evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Final, Iterable


HONEST_DOMAIN_RUNTIME: Final = "partial"
HONEST_PLAYER_VISIBLE_LOOP: Final = "partial"
HONEST_RUNTIME_EVIDENCE: Final = "static-ready"


class TitleRank(IntEnum):
    """Only the ordering needed by the 361 permission contract."""

    BARON = 0
    COUNT = 1
    DUKE = 2
    KING = 3
    EMPEROR = 4


class ActorRoute(str, Enum):
    PLAYER = "player"
    AI = "ai"


@dataclass(frozen=True)
class PermissionContract:
    """The owner's explicit AI exception, without widening rank permissions."""

    player_manager: str
    ai_manager: str
    subject: str
    count_baron: str

    def can_manage(
        self,
        *,
        route: ActorRoute,
        title_rank: TitleRank,
        is_celestial: bool,
        is_landed: bool = True,
    ) -> bool:
        # Both routes use the same domain boundary.  AI differs only by using a
        # background decision path instead of the player-visible case UI.
        if route not in (ActorRoute.PLAYER, ActorRoute.AI):
            return False
        return is_landed and is_celestial and title_rank >= TitleRank.DUKE

    @staticmethod
    def can_act_on_subject_case(*, actor_id: str, subject_id: str) -> bool:
        """A subject may acknowledge/refuse/appeal only their own frozen case."""

        return bool(actor_id) and actor_id == subject_id


PHASE2_PERMISSION_CONTRACT: Final = PermissionContract(
    player_manager=(
        "Only an in-office landed celestial duke-or-above may own a cohort and "
        "use the player-visible review/calibration/notice path."
    ),
    ai_manager=(
        "The owner-authorized AI exception is limited to an in-office landed "
        "celestial duke-or-above reviewing direct officials in the background."
    ),
    subject=(
        "A direct assessed official may read, acknowledge, refuse, or appeal "
        "only that official's own frozen case."
    ),
    count_baron=(
        "Counts and barons are subject-only: they cannot own a cohort, impose "
        "quota C, calibrate another official, settle another case, or start PIP."
    ),
)


@dataclass(frozen=True)
class MechanismRuntimeSpec:
    """Minimal source-of-truth row for one partial runtime mechanism."""

    mechanism_id: str
    title: str
    domain: str
    object_type: str
    owner_binding: str
    subject_binding: str
    cycle_binding: str
    case_binding: str
    hook: str
    states: tuple[str, ...]
    feedback: tuple[str, ...]
    permissions: PermissionContract = PHASE2_PERMISSION_CONTRACT
    domain_runtime: str = HONEST_DOMAIN_RUNTIME
    player_visible_loop: str = HONEST_PLAYER_VISIBLE_LOOP
    runtime_evidence: str = HONEST_RUNTIME_EVIDENCE


PHASE2_RUNTIME_SPECS: Final[dict[str, MechanismRuntimeSpec]] = {
    "001": MechanismRuntimeSpec(
        mechanism_id="001",
        title="KPI itemized evidence sheet",
        domain="A",
        object_type="review_case",
        owner_binding="frozen_reviewing_manager",
        subject_binding="frozen_direct_assessed_official",
        cycle_binding="review_cycle_serial",
        case_binding="evidence_sheet_case_serial",
        hook="review_evidence_freeze",
        states=("EVIDENCE_OPEN", "EVIDENCE_FROZEN"),
        feedback=(
            "scoreboard_kpi_evidence_detail",
            "personal_notice_kpi_breakdown",
            "appeal_evidence_reference",
        ),
    ),
    "018": MechanismRuntimeSpec(
        mechanism_id="018",
        title="Personal notice and four-consequence settlement statement",
        domain="C",
        object_type="notice_case",
        owner_binding="frozen_reviewing_manager",
        subject_binding="frozen_direct_assessed_official",
        cycle_binding="review_cycle_serial",
        case_binding="notice_case_serial",
        hook="notice_delivered",
        states=(
            "PREPARED",
            "REFUSED_PENDING_WITNESS",
            "DELIVERED_SETTLED",
            "APPEAL_CLOSED",
            "CORRECTED",
        ),
        feedback=(
            "reopenable_personal_settlement_statement",
            "itemized_penalty_and_refund_receipts",
            "remaining_salary_withholding_status",
        ),
    ),
    "069": MechanismRuntimeSpec(
        mechanism_id="069",
        title="Formal service and appeal clock",
        domain="K",
        object_type="notice_case",
        owner_binding="frozen_reviewing_manager",
        subject_binding="frozen_direct_assessed_official",
        cycle_binding="review_cycle_serial",
        case_binding="notice_case_serial",
        hook="review_result_frozen",
        states=(
            "PREPARED",
            "REFUSED_PENDING_WITNESS",
            "DELIVERED_SETTLED",
            "APPEAL_CLOSED",
            "CORRECTED",
        ),
        feedback=(
            "notice_service_timeline",
            "refusal_witness_record",
            "appeal_deadline_and_outcome",
        ),
    ),
    "357": MechanismRuntimeSpec(
        mechanism_id="357",
        title="Freeze facts before applying the 361 quota",
        domain="AL",
        object_type="calibration_case",
        owner_binding="frozen_reviewing_manager",
        subject_binding="frozen_direct_assessed_official",
        cycle_binding="review_cycle_serial",
        case_binding="calibration_case_serial",
        hook="kpi_evidence_frozen_before_quota",
        states=(
            "FACTS_OPEN",
            "ABSOLUTE_GRADE_FROZEN",
            "QUOTA_APPLIED",
            "FINAL_GRADE_FROZEN",
        ),
        feedback=(
            "absolute_and_final_grade_comparison",
            "quota_or_calibration_reason_code",
            "newcomer_protection_marker",
        ),
    ),
}


def validate_runtime_specs(
    specs: dict[str, MechanismRuntimeSpec] = PHASE2_RUNTIME_SPECS,
) -> None:
    """Reject accidental readiness inflation or an underspecified source row."""

    if set(specs) != {"001", "018", "069", "357"}:
        raise ValueError("phase-two first slice must contain exactly 001/018/069/357")
    for key, spec in specs.items():
        if key != spec.mechanism_id:
            raise ValueError(f"runtime spec key/id mismatch: {key}/{spec.mechanism_id}")
        if (
            spec.domain_runtime != HONEST_DOMAIN_RUNTIME
            or spec.player_visible_loop != HONEST_PLAYER_VISIBLE_LOOP
            or spec.runtime_evidence != HONEST_RUNTIME_EVIDENCE
        ):
            raise ValueError(f"mechanism {key} overstates runtime readiness")
        bindings = (
            spec.owner_binding,
            spec.subject_binding,
            spec.cycle_binding,
            spec.case_binding,
            spec.hook,
        )
        if not all(bindings) or not spec.states or not spec.feedback:
            raise ValueError(f"mechanism {key} has an incomplete runtime contract")


class Grade(IntEnum):
    BOTTOM_325 = 1
    NORMAL_35 = 2
    TOP_375 = 3

    @property
    def label(self) -> str:
        return {
            Grade.BOTTOM_325: "3.25",
            Grade.NORMAL_35: "3.5",
            Grade.TOP_375: "3.75",
        }[self]


KPI_COMPONENT_KEYS: Final[tuple[str, ...]] = (
    "governance",
    "capability",
    "growth",
    "superior",
    "values",
    "collaboration",
    "jingcha",
    "organization",
)


@dataclass(frozen=True)
class KpiBreakdown:
    """The eight values frozen by mechanism 001 in one review tick."""

    governance: int = 0
    capability: int = 0
    growth: int = 0
    superior: int = 0
    values: int = 0
    collaboration: int = 0
    jingcha: int = 0
    organization: int = 0

    def __post_init__(self) -> None:
        for key, value in self.as_dict().items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"KPI component {key} must be an integer")

    def as_dict(self) -> dict[str, int]:
        return {key: getattr(self, key) for key in KPI_COMPONENT_KEYS}

    @property
    def total(self) -> int:
        return sum(self.as_dict().values())

    @property
    def absolute_grade(self) -> Grade:
        return absolute_grade_for_kpi(self.total)


def absolute_grade_for_kpi(total: int) -> Grade:
    """Freeze facts before quota: >=50 top, >=0 normal, otherwise bottom."""

    if isinstance(total, bool) or not isinstance(total, int):
        raise TypeError("KPI total must be an integer")
    if total >= 50:
        return Grade.TOP_375
    if total >= 0:
        return Grade.NORMAL_35
    return Grade.BOTTOM_325


class FinalGradeReason(str, Enum):
    ABSOLUTE_BAND = "absolute_band"
    QUOTA_C = "quota_c"
    QUOTA_PROMOTION = "quota_promotion"
    QUOTA_OTHER_ADJUSTMENT = "quota_other_adjustment"
    CALIBRATION_PROMOTION = "calibration_promotion"
    CALIBRATION_DEMOTION = "calibration_demotion"
    NEWCOMER_PROTECTION = "newcomer_protection"
    SMALL_COHORT_NEUTRAL = "small_cohort_neutral"


@dataclass(frozen=True)
class FinalGradeDecision:
    absolute_grade: Grade
    quota_grade: Grade
    final_grade: Grade
    reason: FinalGradeReason

    @property
    def forced_down(self) -> bool:
        return self.final_grade < self.absolute_grade


def resolve_final_grade(
    *,
    absolute_grade: Grade,
    quota_grade: Grade,
    calibrated_grade: Grade | None = None,
    newcomer_protected: bool = False,
    small_cohort_neutral: bool = False,
) -> FinalGradeDecision:
    """Explain the final grade without rewriting the frozen absolute facts.

    ``quota_grade`` is the initial relative-distribution proposal.  A newcomer
    protection consumes a proposed C and raises this subject to 3.5; the cohort
    allocator remains responsible for assigning the C slot to another eligible
    subject.  Calibration is a later, explicit reason and may not demote a
    protected newcomer to C.
    """

    absolute_grade = Grade(absolute_grade)
    quota_grade = Grade(quota_grade)
    grade = quota_grade

    if small_cohort_neutral:
        if quota_grade != Grade.NORMAL_35:
            raise ValueError("small-cohort neutralization requires final proposal 3.5")
        if calibrated_grade is not None or newcomer_protected:
            raise ValueError("small cohorts cannot calibrate or consume newcomer C protection")
        return FinalGradeDecision(
            absolute_grade=absolute_grade,
            quota_grade=quota_grade,
            final_grade=Grade.NORMAL_35,
            reason=(
                FinalGradeReason.ABSOLUTE_BAND
                if absolute_grade == Grade.NORMAL_35
                else FinalGradeReason.SMALL_COHORT_NEUTRAL
            ),
        )

    if grade == absolute_grade:
        reason = FinalGradeReason.ABSOLUTE_BAND
    elif grade == Grade.BOTTOM_325 and absolute_grade > Grade.BOTTOM_325:
        reason = FinalGradeReason.QUOTA_C
    elif grade > absolute_grade:
        reason = FinalGradeReason.QUOTA_PROMOTION
    else:
        reason = FinalGradeReason.QUOTA_OTHER_ADJUSTMENT

    if newcomer_protected:
        if quota_grade != Grade.BOTTOM_325:
            raise ValueError("newcomer protection requires a proposed quota C")
        grade = Grade.NORMAL_35
        reason = FinalGradeReason.NEWCOMER_PROTECTION

    if calibrated_grade is not None:
        calibrated_grade = Grade(calibrated_grade)
        if newcomer_protected and calibrated_grade == Grade.BOTTOM_325:
            raise ValueError("calibration cannot bypass newcomer C protection")
        if calibrated_grade > grade:
            reason = FinalGradeReason.CALIBRATION_PROMOTION
        elif calibrated_grade < grade:
            reason = FinalGradeReason.CALIBRATION_DEMOTION
        grade = calibrated_grade

    return FinalGradeDecision(
        absolute_grade=absolute_grade,
        quota_grade=quota_grade,
        final_grade=grade,
        reason=reason,
    )


class NoticeState(str, Enum):
    PREPARED = "PREPARED"
    REFUSED_PENDING_WITNESS = "REFUSED_PENDING_WITNESS"
    DELIVERED_SETTLED = "DELIVERED_SETTLED"
    APPEAL_CLOSED = "APPEAL_CLOSED"
    CORRECTED = "CORRECTED"


@dataclass(frozen=True)
class CaseToken:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    expected_state: NoticeState


@dataclass(frozen=True)
class ActionResult:
    applied: bool
    code: str
    previous_state: NoticeState
    current_state: NoticeState


@dataclass
class Receipt:
    """One penalty transaction.  Counts expose accidental double application."""

    receipt_id: str
    resource: str
    amount: int
    settled: bool = False
    refunded: bool = False
    settlement_count: int = 0
    refund_count: int = 0

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.resource:
            raise ValueError("receipt id and resource are required")
        if isinstance(self.amount, bool) or not isinstance(self.amount, int) or self.amount < 0:
            raise ValueError("receipt amount must be a non-negative integer")

    def settle_once(self) -> bool:
        if self.settled:
            return False
        self.settled = True
        self.settlement_count = 1
        return True

    def refund_once(self) -> bool:
        if not self.settled or self.refunded:
            return False
        self.refunded = True
        self.refund_count = 1
        return True


@dataclass
class NoticeCase:
    """Reference state machine shared by mechanisms 018 and 069.

    Refusal changes the service method, never the frozen result.  Witness
    service must therefore enter the same settlement state as acknowledgement.
    Every mutation is guarded by owner/subject/cycle/case/expected-state.
    """

    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    receipts: list[Receipt] = field(default_factory=list)
    state: NoticeState = NoticeState.PREPARED
    delivery_method: str | None = None
    appeal_outcome: str | None = None

    def __post_init__(self) -> None:
        if not self.owner_id or not self.subject_id:
            raise ValueError("notice owner and subject are required")
        if self.cycle_serial < 1 or self.case_serial < 1:
            raise ValueError("cycle and case serials must be positive")
        receipt_ids = [receipt.receipt_id for receipt in self.receipts]
        if len(receipt_ids) != len(set(receipt_ids)):
            raise ValueError("receipt ids must be unique within a notice case")

    def token(self) -> CaseToken:
        return CaseToken(
            owner_id=self.owner_id,
            subject_id=self.subject_id,
            cycle_serial=self.cycle_serial,
            case_serial=self.case_serial,
            expected_state=self.state,
        )

    def _guard(self, token: CaseToken) -> bool:
        return token == self.token()

    def _result(
        self,
        *,
        applied: bool,
        code: str,
        previous_state: NoticeState,
    ) -> ActionResult:
        return ActionResult(applied, code, previous_state, self.state)

    def _stale(self, previous_state: NoticeState) -> ActionResult:
        return self._result(
            applied=False,
            code="stale-token",
            previous_state=previous_state,
        )

    def _illegal(self, previous_state: NoticeState) -> ActionResult:
        return self._result(
            applied=False,
            code="illegal-transition",
            previous_state=previous_state,
        )

    def refuse_delivery(self, token: CaseToken) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._stale(previous)
        if self.state != NoticeState.PREPARED:
            return self._illegal(previous)
        self.state = NoticeState.REFUSED_PENDING_WITNESS
        self.delivery_method = "refused_pending_witness"
        return self._result(applied=True, code="refusal-recorded", previous_state=previous)

    def acknowledge_delivery(
        self,
        token: CaseToken,
        *,
        with_objection: bool = False,
    ) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._stale(previous)
        if self.state != NoticeState.PREPARED:
            return self._illegal(previous)
        self.delivery_method = "acknowledged_with_objection" if with_objection else "acknowledged"
        self._settle_receipts_once()
        self.state = NoticeState.DELIVERED_SETTLED
        return self._result(applied=True, code="delivered-settled", previous_state=previous)

    def witness_delivery(self, token: CaseToken) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._stale(previous)
        if self.state != NoticeState.REFUSED_PENDING_WITNESS:
            return self._illegal(previous)
        self.delivery_method = "witness_after_refusal"
        self._settle_receipts_once()
        self.state = NoticeState.DELIVERED_SETTLED
        return self._result(applied=True, code="witness-delivered-settled", previous_state=previous)

    def close_appeal(self, token: CaseToken) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._stale(previous)
        if self.state != NoticeState.DELIVERED_SETTLED:
            return self._illegal(previous)
        self.appeal_outcome = "closed_without_correction"
        self.state = NoticeState.APPEAL_CLOSED
        return self._result(applied=True, code="appeal-closed", previous_state=previous)

    def correct(self, token: CaseToken) -> ActionResult:
        previous = self.state
        if not self._guard(token):
            return self._stale(previous)
        if self.state != NoticeState.DELIVERED_SETTLED:
            return self._illegal(previous)
        self._refund_receipts_once()
        self.appeal_outcome = "corrected_and_refunded"
        self.state = NoticeState.CORRECTED
        return self._result(applied=True, code="corrected", previous_state=previous)

    def _settle_receipts_once(self) -> None:
        for receipt in self.receipts:
            receipt.settle_once()

    def _refund_receipts_once(self) -> None:
        for receipt in self.receipts:
            receipt.refund_once()

    @property
    def witness_required(self) -> bool:
        return self.state == NoticeState.REFUSED_PENDING_WITNESS


def make_receipts(rows: Iterable[tuple[str, str, int]]) -> list[Receipt]:
    """Convenience constructor used by deterministic tests and future generators."""

    return [Receipt(receipt_id, resource, amount) for receipt_id, resource, amount in rows]


validate_runtime_specs()
