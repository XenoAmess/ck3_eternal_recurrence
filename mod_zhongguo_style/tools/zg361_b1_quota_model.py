#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic B1 quota/calibration reference model.

This module is deliberately independent from the CK3 generator and runtime.  It
models only the deterministic A-route primitives named below; it is not a claim
that all nine mechanisms or their B/C routes are product-complete.  Generators,
static tests, and fixtures can reuse these immutable transitions without
claiming that CK3 scripts implement them yet.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
import hashlib
import json
from types import MappingProxyType
from typing import Iterable, Sequence


READINESS = "python-l0-reference-only"
CK3_IMPLEMENTED = False


class RedCode(str, Enum):
    """Stable categories for reference-model failures."""

    INVALID_INPUT = "invalid_input"
    DUPLICATE_INPUT = "duplicate_input"
    DUPLICATE_OPERATION = "duplicate_operation"
    STALE_OPERATION = "stale_operation"
    ILLEGAL_STATE = "illegal_state"
    INSUFFICIENT_SLOT = "insufficient_slot"
    DEBT_NOT_DUE = "debt_not_due"
    THRESHOLD_NOT_MET = "threshold_not_met"
    CONSERVATION = "conservation"


class QuotaModelError(ValueError):
    """Base class for all typed RED outcomes."""

    code = RedCode.INVALID_INPUT

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.context = MappingProxyType(dict(sorted(context.items())))


class InvalidInputError(QuotaModelError):
    code = RedCode.INVALID_INPUT


class DuplicateInputError(QuotaModelError):
    code = RedCode.DUPLICATE_INPUT


class DuplicateOperationError(QuotaModelError):
    code = RedCode.DUPLICATE_OPERATION


class StaleOperationError(QuotaModelError):
    code = RedCode.STALE_OPERATION


class IllegalStateError(QuotaModelError):
    code = RedCode.ILLEGAL_STATE


class InsufficientSlotError(QuotaModelError):
    code = RedCode.INSUFFICIENT_SLOT


class DebtNotDueError(QuotaModelError):
    code = RedCode.DEBT_NOT_DUE


class ThresholdNotMetError(QuotaModelError):
    code = RedCode.THRESHOLD_NOT_MET


class ConservationError(QuotaModelError):
    code = RedCode.CONSERVATION


def _require_identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidInputError(f"{field} must be a non-empty string", field=field)
    return value


def _require_int(value: object, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InvalidInputError(
            f"{field} must be an integer >= {minimum}", field=field, value=value
        )
    return value


def _require_signed_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidInputError(f"{field} must be an integer", field=field, value=value)
    return value


def _as_fraction(value: object, field: str) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidInputError(
            f"{field} must use an exact int, str, or Fraction", field=field
        )
    try:
        result = Fraction(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise InvalidInputError(f"{field} is not an exact fraction", field=field) from exc
    return result


def _stable_pool_id(
    cycle: int,
    common_superior_id: str,
    function_id: str,
    source_team_ids: tuple[str, ...],
) -> str:
    """Return a delimiter-safe ID for one canonically ordered pool identity."""

    payload = json.dumps(
        [cycle, common_superior_id, function_id, source_team_ids],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"b1-pool-{hashlib.sha256(payload).hexdigest()}"


class RatingBand(str, Enum):
    TOP = "3.75"
    MIDDLE = "3.5"
    BOTTOM = "3.25"

    @property
    def ck3_grade_code(self) -> int:
        return {
            RatingBand.TOP: 3,
            RatingBand.MIDDLE: 2,
            RatingBand.BOTTOM: 1,
        }[self]


BAND_ORDER = (RatingBand.TOP, RatingBand.MIDDLE, RatingBand.BOTTOM)
DEFAULT_WEIGHTS = MappingProxyType(
    {
        RatingBand.TOP: Fraction(3, 10),
        RatingBand.MIDDLE: Fraction(6, 10),
        RatingBand.BOTTOM: Fraction(1, 10),
    }
)
MINIMUM_FORCED_COHORT = 3


@dataclass(frozen=True, slots=True)
class QuotaCounts:
    top: int = 0
    middle: int = 0
    bottom: int = 0

    def __post_init__(self) -> None:
        _require_int(self.top, "top")
        _require_int(self.middle, "middle")
        _require_int(self.bottom, "bottom")

    @property
    def total(self) -> int:
        return self.top + self.middle + self.bottom

    def __getitem__(self, band: RatingBand) -> int:
        if band is RatingBand.TOP:
            return self.top
        if band is RatingBand.MIDDLE:
            return self.middle
        if band is RatingBand.BOTTOM:
            return self.bottom
        raise InvalidInputError("unknown rating band", band=band)

    def with_delta(self, band: RatingBand, delta: int) -> QuotaCounts:
        _require_signed_int(delta, "delta")
        values = {
            RatingBand.TOP: self.top,
            RatingBand.MIDDLE: self.middle,
            RatingBand.BOTTOM: self.bottom,
        }
        if not isinstance(band, RatingBand):
            raise InvalidInputError("unknown rating band", band=band)
        values[band] += delta
        if values[band] < 0:
            raise InsufficientSlotError(
                "quota adjustment would make a band negative",
                band=band.value,
                available=self[band],
                delta=delta,
            )
        return QuotaCounts(
            top=values[RatingBand.TOP],
            middle=values[RatingBand.MIDDLE],
            bottom=values[RatingBand.BOTTOM],
        )

    def as_dict(self) -> dict[str, int]:
        return {
            RatingBand.TOP.value: self.top,
            RatingBand.MIDDLE.value: self.middle,
            RatingBand.BOTTOM.value: self.bottom,
        }


@dataclass(frozen=True, slots=True)
class BandRounding:
    band: RatingBand
    raw: Fraction
    floor_slots: int
    remainder: Fraction
    awarded_remainder_slot: bool
    rounded_slots: int

    def __post_init__(self) -> None:
        if not isinstance(self.band, RatingBand):
            raise InvalidInputError("band rounding has an invalid band")
        raw = _as_fraction(self.raw, "raw")
        remainder = _as_fraction(self.remainder, "remainder")
        _require_int(self.floor_slots, "floor_slots")
        _require_int(self.rounded_slots, "rounded_slots")
        if not isinstance(self.awarded_remainder_slot, bool):
            raise InvalidInputError("awarded_remainder_slot must be bool")
        if raw < 0 or self.floor_slots != raw.numerator // raw.denominator:
            raise ConservationError("band rounding floor does not match raw target")
        if remainder != raw - self.floor_slots or not 0 <= remainder < 1:
            raise ConservationError("band rounding remainder does not match raw target")
        if self.rounded_slots != self.floor_slots + int(self.awarded_remainder_slot):
            raise ConservationError("band rounded slots do not match remainder award")
        object.__setattr__(self, "raw", raw)
        object.__setattr__(self, "remainder", remainder)


@dataclass(frozen=True, slots=True)
class QuotaComputation:
    cohort_size: int
    bands: tuple[BandRounding, ...]
    rounded_counts: QuotaCounts
    effective_counts: QuotaCounts
    forced_distribution: bool

    def __post_init__(self) -> None:
        _require_int(self.cohort_size, "cohort_size")
        bands = tuple(self.bands)
        if any(not isinstance(item, BandRounding) for item in bands):
            raise InvalidInputError("bands must contain BandRounding values")
        if tuple(item.band for item in bands) != BAND_ORDER:
            raise ConservationError("quota computation must contain canonical bands once")
        if not isinstance(self.rounded_counts, QuotaCounts) or not isinstance(
            self.effective_counts, QuotaCounts
        ):
            raise InvalidInputError("quota computation counts must be QuotaCounts")
        if not isinstance(self.forced_distribution, bool):
            raise InvalidInputError("forced_distribution must be bool")
        reconstructed = QuotaCounts(
            top=bands[0].rounded_slots,
            middle=bands[1].rounded_slots,
            bottom=bands[2].rounded_slots,
        )
        if reconstructed != self.rounded_counts or reconstructed.total != self.cohort_size:
            raise ConservationError("rounded quota computation does not conserve cohort")
        if self.effective_counts.total != self.cohort_size:
            raise ConservationError("effective quota computation does not conserve cohort")
        if self.forced_distribution != (self.cohort_size >= MINIMUM_FORCED_COHORT):
            raise ConservationError("forced-distribution flag contradicts cohort size")
        if self.forced_distribution and self.effective_counts != self.rounded_counts:
            raise ConservationError("forced cohort must use rounded counts")
        if not self.forced_distribution and self.effective_counts != QuotaCounts(
            middle=self.cohort_size
        ):
            raise ConservationError("small cohort must settle entirely in the middle band")
        object.__setattr__(self, "bands", bands)

    def band(self, band: RatingBand) -> BandRounding:
        for item in self.bands:
            if item.band is band:
                return item
        raise InvalidInputError("unknown rating band", band=band)

    def as_dict(self) -> dict[str, object]:
        return {
            "cohort_size": self.cohort_size,
            "forced_distribution": self.forced_distribution,
            "rounded": self.rounded_counts.as_dict(),
            "effective": self.effective_counts.as_dict(),
            "bands": {
                item.band.value: {
                    "raw": str(item.raw),
                    "floor": item.floor_slots,
                    "remainder": str(item.remainder),
                    "awarded_remainder_slot": item.awarded_remainder_slot,
                    "rounded": item.rounded_slots,
                }
                for item in self.bands
            },
        }


def compute_quota(cohort_size: int) -> QuotaComputation:
    """Compute exact 30/60/10 quotas with a stable largest-remainder tie break.

    Ties are resolved in ``TOP, MIDDLE, BOTTOM`` order.  Cohorts smaller than
    three retain their exact raw/rounded audit fields but use the existing
    product rule that every assessed person settles in the middle band.
    """

    size = _require_int(cohort_size, "cohort_size")
    raw = {band: size * DEFAULT_WEIGHTS[band] for band in BAND_ORDER}
    floors = {band: raw[band].numerator // raw[band].denominator for band in BAND_ORDER}
    remainders = {band: raw[band] - floors[band] for band in BAND_ORDER}
    slots_left = size - sum(floors.values())
    if slots_left < 0 or slots_left > len(BAND_ORDER):
        raise ConservationError("largest-remainder slot count is impossible")
    remainder_order = sorted(
        BAND_ORDER,
        key=lambda band: (-remainders[band], BAND_ORDER.index(band)),
    )
    awarded = frozenset(remainder_order[:slots_left])
    rounded = {
        band: floors[band] + (1 if band in awarded else 0) for band in BAND_ORDER
    }
    rounded_counts = QuotaCounts(
        top=rounded[RatingBand.TOP],
        middle=rounded[RatingBand.MIDDLE],
        bottom=rounded[RatingBand.BOTTOM],
    )
    if rounded_counts.total != size:
        raise ConservationError(
            "rounded bands do not sum to the cohort", expected=size, actual=rounded_counts.total
        )
    forced = size >= MINIMUM_FORCED_COHORT
    effective = rounded_counts if forced else QuotaCounts(middle=size)
    bands = tuple(
        BandRounding(
            band=band,
            raw=raw[band],
            floor_slots=floors[band],
            remainder=remainders[band],
            awarded_remainder_slot=band in awarded,
            rounded_slots=rounded[band],
        )
        for band in BAND_ORDER
    )
    return QuotaComputation(
        cohort_size=size,
        bands=bands,
        rounded_counts=rounded_counts,
        effective_counts=effective,
        forced_distribution=forced,
    )


class EligibilityTreatment(str, Enum):
    INCLUDE = "include"
    PROTECT_FROM_BOTTOM = "protect_from_bottom"
    EXCLUDE = "exclude"


@dataclass(frozen=True, slots=True)
class EligibilityPolicy:
    newcomer: EligibilityTreatment = EligibilityTreatment.PROTECT_FROM_BOTTOM
    leaver: EligibilityTreatment = EligibilityTreatment.EXCLUDE
    transferred_in: EligibilityTreatment = EligibilityTreatment.INCLUDE
    long_leave: EligibilityTreatment = EligibilityTreatment.EXCLUDE

    def __post_init__(self) -> None:
        if not isinstance(self.newcomer, EligibilityTreatment):
            raise InvalidInputError("invalid newcomer treatment")
        if not isinstance(self.leaver, EligibilityTreatment):
            raise InvalidInputError("invalid leaver treatment")
        if not isinstance(self.transferred_in, EligibilityTreatment):
            raise InvalidInputError("invalid transferred-in treatment")
        if not isinstance(self.long_leave, EligibilityTreatment):
            raise InvalidInputError("invalid long-leave treatment")


@dataclass(frozen=True, slots=True)
class CohortMember:
    member_id: str
    team_id: str
    common_superior_id: str
    newcomer: bool = False
    leaver: bool = False
    transferred_in: bool = False
    long_leave: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.member_id, "member_id")
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        if any(
            not isinstance(value, bool)
            for value in (
                self.newcomer,
                self.leaver,
                self.transferred_in,
                self.long_leave,
            )
        ):
            raise InvalidInputError("cohort member status flags must be bool")


@dataclass(frozen=True, slots=True)
class TeamCohort:
    team_id: str
    manager_id: str
    common_superior_id: str
    cycle: int
    members: tuple[CohortMember, ...]
    function_id: str = "default"

    def __post_init__(self) -> None:
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.manager_id, "manager_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_identifier(self.function_id, "function_id")
        _require_int(self.cycle, "cycle")
        object.__setattr__(self, "members", tuple(self.members))
        seen: set[str] = set()
        for member in self.members:
            if not isinstance(member, CohortMember):
                raise InvalidInputError("members must contain CohortMember values")
            if member.member_id in seen:
                raise DuplicateInputError(
                    "member appears twice in one team cohort", member_id=member.member_id
                )
            seen.add(member.member_id)
            if member.team_id != self.team_id:
                raise InvalidInputError(
                    "member team does not match cohort",
                    member_id=member.member_id,
                    expected=self.team_id,
                    actual=member.team_id,
                )
            if member.common_superior_id != self.common_superior_id:
                raise InvalidInputError(
                    "member common superior does not match cohort",
                    member_id=member.member_id,
                )


@dataclass(frozen=True, slots=True)
class MemberEligibility:
    member: CohortMember
    quota_eligible: bool
    bottom_eligible: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.member, CohortMember):
            raise InvalidInputError("member eligibility requires CohortMember")
        if not isinstance(self.quota_eligible, bool) or not isinstance(
            self.bottom_eligible, bool
        ):
            raise InvalidInputError("eligibility flags must be bool")
        if self.bottom_eligible and not self.quota_eligible:
            raise ConservationError("bottom eligibility requires quota eligibility")
        reasons = tuple(self.reasons)
        for reason in reasons:
            _require_identifier(reason, "eligibility_reason")
        object.__setattr__(self, "reasons", reasons)


@dataclass(frozen=True, slots=True)
class LockedCohort:
    team_id: str
    manager_id: str
    common_superior_id: str
    cycle: int
    function_id: str
    records: tuple[MemberEligibility, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.manager_id, "manager_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_identifier(self.function_id, "function_id")
        _require_int(self.cycle, "cycle")
        records = tuple(self.records)
        if any(not isinstance(item, MemberEligibility) for item in records):
            raise InvalidInputError("locked cohort records are invalid")
        if len({item.member.member_id for item in records}) != len(records):
            raise ConservationError("locked cohort contains a duplicate member")
        if any(
            item.member.team_id != self.team_id
            or item.member.common_superior_id != self.common_superior_id
            for item in records
        ):
            raise ConservationError("locked cohort member ownership changed")
        object.__setattr__(self, "records", records)

    @property
    def included_members(self) -> tuple[CohortMember, ...]:
        return tuple(record.member for record in self.records if record.quota_eligible)

    @property
    def bottom_eligible_members(self) -> tuple[CohortMember, ...]:
        return tuple(record.member for record in self.records if record.bottom_eligible)

    @property
    def excluded_members(self) -> tuple[CohortMember, ...]:
        return tuple(record.member for record in self.records if not record.quota_eligible)

    @property
    def quota(self) -> QuotaComputation:
        return compute_quota(len(self.included_members))


def lock_cohort(
    cohort: TeamCohort, policy: EligibilityPolicy = EligibilityPolicy()
) -> LockedCohort:
    if not isinstance(cohort, TeamCohort) or not isinstance(policy, EligibilityPolicy):
        raise InvalidInputError("lock_cohort requires TeamCohort and EligibilityPolicy")
    records: list[MemberEligibility] = []
    for member in sorted(cohort.members, key=lambda item: item.member_id):
        treatments: list[tuple[str, EligibilityTreatment]] = []
        if member.newcomer:
            treatments.append(("newcomer", policy.newcomer))
        if member.leaver:
            treatments.append(("leaver", policy.leaver))
        if member.transferred_in:
            treatments.append(("transferred_in", policy.transferred_in))
        if member.long_leave:
            treatments.append(("long_leave", policy.long_leave))
        excluded = any(value is EligibilityTreatment.EXCLUDE for _, value in treatments)
        protected = any(
            value is EligibilityTreatment.PROTECT_FROM_BOTTOM for _, value in treatments
        )
        records.append(
            MemberEligibility(
                member=member,
                quota_eligible=not excluded,
                bottom_eligible=not excluded and not protected,
                reasons=tuple(f"{name}:{value.value}" for name, value in treatments),
            )
        )
    return LockedCohort(
        team_id=cohort.team_id,
        manager_id=cohort.manager_id,
        common_superior_id=cohort.common_superior_id,
        cycle=cohort.cycle,
        function_id=cohort.function_id,
        records=tuple(records),
    )


@dataclass(frozen=True, slots=True)
class RosterChangeReceipt:
    change_id: str
    member_id: str
    before: CohortMember | None
    after: CohortMember
    reason: str
    actor_id: str
    approver_id: str
    changed_at: str

    def __post_init__(self) -> None:
        _require_identifier(self.change_id, "change_id")
        _require_identifier(self.member_id, "member_id")
        _require_identifier(self.reason, "reason")
        _require_identifier(self.actor_id, "actor_id")
        _require_identifier(self.approver_id, "approver_id")
        _require_identifier(self.changed_at, "changed_at")
        if self.before is not None and not isinstance(self.before, CohortMember):
            raise InvalidInputError("roster receipt before must be CohortMember or None")
        if not isinstance(self.after, CohortMember):
            raise InvalidInputError("roster receipt after must be CohortMember")
        if self.after.member_id != self.member_id or (
            self.before is not None and self.before.member_id != self.member_id
        ):
            raise ConservationError("roster receipt member identity changed")
        if self.before is None and not (
            self.after.newcomer or self.after.transferred_in
        ):
            raise ConservationError(
                "a post-lock roster addition must be marked join or transfer-in"
            )
        if self.before is not None and (
            self.before.team_id != self.after.team_id
            or self.before.common_superior_id != self.after.common_superior_id
        ):
            raise ConservationError("roster receipt changed member ownership")
        if self.before == self.after:
            raise ConservationError("roster receipt must record a real change")


@dataclass(frozen=True, slots=True)
class RosterAuditState:
    original: LockedCohort
    current: LockedCohort
    policy: EligibilityPolicy
    version: int = 0
    change_receipts: tuple[RosterChangeReceipt, ...] = ()
    calibration_reopen_required: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.original, LockedCohort) or not isinstance(
            self.current, LockedCohort
        ):
            raise InvalidInputError("roster audit requires locked cohort snapshots")
        if not isinstance(self.policy, EligibilityPolicy):
            raise InvalidInputError("roster audit requires EligibilityPolicy")
        _require_int(self.version, "version")
        receipts = tuple(self.change_receipts)
        if any(not isinstance(item, RosterChangeReceipt) for item in receipts):
            raise InvalidInputError("change_receipts must contain RosterChangeReceipt values")
        if self.version != len(receipts):
            raise ConservationError("roster audit version must equal receipt count")
        if self.calibration_reopen_required != bool(receipts):
            raise ConservationError("roster audit change must require calibration reopen")
        identity = (
            self.original.team_id,
            self.original.manager_id,
            self.original.common_superior_id,
            self.original.cycle,
            self.original.function_id,
        )
        current_identity = (
            self.current.team_id,
            self.current.manager_id,
            self.current.common_superior_id,
            self.current.cycle,
            self.current.function_id,
        )
        if identity != current_identity:
            raise ConservationError("roster audit changed cohort ownership or cycle")
        replay_members = {
            record.member.member_id: record.member for record in self.original.records
        }
        change_ids: set[str] = set()
        for receipt in receipts:
            if receipt.change_id in change_ids:
                raise ConservationError("roster audit contains a duplicate change receipt")
            change_ids.add(receipt.change_id)
            if receipt.before is None:
                if receipt.member_id in replay_members:
                    raise ConservationError("roster join receipt reused an existing member")
            elif replay_members.get(receipt.member_id) != receipt.before:
                raise ConservationError("roster receipt before-image is stale")
            replay_members[receipt.member_id] = receipt.after
        current_members = {
            record.member.member_id: record.member for record in self.current.records
        }
        if replay_members != current_members:
            raise ConservationError("roster receipts do not reconstruct current membership")
        original_cohort = TeamCohort(
            team_id=self.original.team_id,
            manager_id=self.original.manager_id,
            common_superior_id=self.original.common_superior_id,
            cycle=self.original.cycle,
            members=tuple(record.member for record in self.original.records),
            function_id=self.original.function_id,
        )
        current_cohort = TeamCohort(
            team_id=self.current.team_id,
            manager_id=self.current.manager_id,
            common_superior_id=self.current.common_superior_id,
            cycle=self.current.cycle,
            members=tuple(current_members.values()),
            function_id=self.current.function_id,
        )
        if lock_cohort(original_cohort, self.policy) != self.original:
            raise ConservationError("original roster eligibility contradicts frozen policy")
        if lock_cohort(current_cohort, self.policy) != self.current:
            raise ConservationError("current roster eligibility contradicts frozen policy")
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        if len(operations) != self.version:
            raise ConservationError("roster operations do not match receipt version")
        object.__setattr__(self, "change_receipts", receipts)
        object.__setattr__(self, "applied_operations", operations)


def open_roster_audit(
    cohort: TeamCohort, policy: EligibilityPolicy = EligibilityPolicy()
) -> RosterAuditState:
    locked = lock_cohort(cohort, policy)
    return RosterAuditState(original=locked, current=locked, policy=policy)


def apply_roster_change(
    state: RosterAuditState,
    updated_member: CohortMember,
    *,
    change_id: str,
    reason: str,
    actor_id: str,
    approver_id: str,
    changed_at: str,
    operation_id: str,
    expected_version: int,
) -> RosterAuditState:
    if not isinstance(state, RosterAuditState) or not isinstance(
        updated_member, CohortMember
    ):
        raise InvalidInputError("invalid roster change arguments")
    op_id = _require_identifier(operation_id, "operation_id")
    change = _require_identifier(change_id, "change_id")
    expected = _require_int(expected_version, "expected_version")
    if op_id in state.applied_operations or any(
        item.change_id == change for item in state.change_receipts
    ):
        raise DuplicateOperationError("roster change was already recorded")
    if expected != state.version:
        raise StaleOperationError("roster change targets a stale lock version")
    records_by_id = {record.member.member_id: record for record in state.current.records}
    old_record = records_by_id.get(updated_member.member_id)
    before = old_record.member if old_record is not None else None
    if updated_member.team_id != state.current.team_id or (
        updated_member.common_superior_id != state.current.common_superior_id
    ):
        raise InvalidInputError("roster status change cannot rewrite member ownership")
    if before is None and not (updated_member.newcomer or updated_member.transferred_in):
        raise InvalidInputError(
            "a new post-lock member must be marked newcomer or transferred-in"
        )
    receipt = RosterChangeReceipt(
        change_id=change,
        member_id=updated_member.member_id,
        before=before,
        after=updated_member,
        reason=reason,
        actor_id=actor_id,
        approver_id=approver_id,
        changed_at=changed_at,
    )
    members = tuple(
        updated_member if record.member.member_id == updated_member.member_id else record.member
        for record in state.current.records
    )
    if before is None:
        members += (updated_member,)
    cohort = TeamCohort(
        team_id=state.current.team_id,
        manager_id=state.current.manager_id,
        common_superior_id=state.current.common_superior_id,
        cycle=state.current.cycle,
        members=members,
        function_id=state.current.function_id,
    )
    return replace(
        state,
        current=lock_cohort(cohort, state.policy),
        version=state.version + 1,
        change_receipts=state.change_receipts + (receipt,),
        calibration_reopen_required=True,
        applied_operations=state.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class CommonSuperiorPool:
    pool_id: str
    common_superior_id: str
    function_id: str
    cycle: int
    source_team_ids: tuple[str, ...]
    records: tuple[MemberEligibility, ...]
    quota: QuotaComputation

    def __post_init__(self) -> None:
        _require_identifier(self.pool_id, "pool_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_identifier(self.function_id, "function_id")
        _require_int(self.cycle, "cycle")
        teams = tuple(self.source_team_ids)
        records = tuple(self.records)
        if len(teams) < 2 or len(set(teams)) != len(teams):
            raise ConservationError("common-superior pool requires at least two unique teams")
        if any(not isinstance(item, MemberEligibility) for item in records):
            raise InvalidInputError("common-superior pool records are invalid")
        if len({item.member.member_id for item in records}) != len(records):
            raise ConservationError("common-superior pool contains a duplicate member")
        if any(
            item.member.common_superior_id != self.common_superior_id
            or item.member.team_id not in teams
            for item in records
        ):
            raise ConservationError("common-superior pool member escaped source teams")
        if not isinstance(self.quota, QuotaComputation) or self.quota.cohort_size != sum(
            item.quota_eligible for item in records
        ):
            raise ConservationError("common-superior pool quota denominator is inconsistent")
        object.__setattr__(self, "source_team_ids", teams)
        object.__setattr__(self, "records", records)

    @property
    def included_members(self) -> tuple[CohortMember, ...]:
        return tuple(record.member for record in self.records if record.quota_eligible)


def pool_by_common_superior(
    cohorts: Iterable[TeamCohort],
    policy: EligibilityPolicy = EligibilityPolicy(),
    *,
    small_sample_threshold: int = 5,
) -> tuple[CommonSuperiorPool, ...]:
    """Pool explicitly selected small teams by cycle, function, and common superior."""

    values = tuple(cohorts)
    if not values:
        raise InvalidInputError("at least one team cohort is required")
    if not isinstance(policy, EligibilityPolicy):
        raise InvalidInputError("invalid eligibility policy")
    threshold = _require_int(
        small_sample_threshold, "small_sample_threshold", minimum=2
    )
    grouped: dict[tuple[int, str, str], list[LockedCohort]] = {}
    team_keys: set[tuple[int, str]] = set()
    member_keys: set[tuple[int, str]] = set()
    for cohort in values:
        if not isinstance(cohort, TeamCohort):
            raise InvalidInputError("cohorts must contain TeamCohort values")
        team_key = (cohort.cycle, cohort.team_id)
        if team_key in team_keys:
            raise DuplicateInputError(
                "team cohort appears twice", cycle=cohort.cycle, team_id=cohort.team_id
            )
        team_keys.add(team_key)
        for member in cohort.members:
            member_key = (cohort.cycle, member.member_id)
            if member_key in member_keys:
                raise DuplicateInputError(
                    "member appears in two team cohorts in one cycle",
                    cycle=cohort.cycle,
                    member_id=member.member_id,
                )
            member_keys.add(member_key)
        locked = lock_cohort(cohort, policy)
        if len(locked.included_members) >= threshold:
            raise InvalidInputError(
                "common-superior pooling accepts only teams below the frozen "
                "small-sample threshold",
                team_id=cohort.team_id,
                cohort_size=len(locked.included_members),
                threshold=threshold,
            )
        grouped.setdefault(
            (cohort.cycle, cohort.common_superior_id, cohort.function_id), []
        ).append(locked)

    pools: list[CommonSuperiorPool] = []
    for (cycle, superior_id, function_id), locked_cohorts in sorted(grouped.items()):
        if len(locked_cohorts) < 2:
            raise InvalidInputError(
                "small-sample pooling requires at least two teams in one frozen group",
                cycle=cycle,
                common_superior_id=superior_id,
                function_id=function_id,
            )
        records: list[MemberEligibility] = []
        seen_members: set[str] = set()
        team_ids = tuple(sorted(item.team_id for item in locked_cohorts))
        for locked in locked_cohorts:
            for record in locked.records:
                member_id = record.member.member_id
                if member_id in seen_members:
                    raise DuplicateInputError(
                        "member appears in two teams in one common-superior pool",
                        member_id=member_id,
                        cycle=cycle,
                        common_superior_id=superior_id,
                    )
                seen_members.add(member_id)
                records.append(record)
        ordered_records = tuple(sorted(records, key=lambda item: item.member.member_id))
        included_count = sum(record.quota_eligible for record in ordered_records)
        pool_id = _stable_pool_id(cycle, superior_id, function_id, team_ids)
        pools.append(
            CommonSuperiorPool(
                pool_id=pool_id,
                common_superior_id=superior_id,
                function_id=function_id,
                cycle=cycle,
                source_team_ids=team_ids,
                records=ordered_records,
                quota=compute_quota(included_count),
            )
        )
    return tuple(pools)


@dataclass(frozen=True, slots=True)
class QuotaBook:
    team_id: str
    common_superior_id: str
    cycle: int
    counts: QuotaCounts
    version: int = 0
    applied_operations: frozenset[str] = frozenset()
    settled_debt_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_int(self.cycle, "cycle")
        _require_int(self.version, "version")
        if not isinstance(self.counts, QuotaCounts):
            raise InvalidInputError("counts must be QuotaCounts")
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        debt_ids = frozenset(self.settled_debt_ids)
        for debt_id in debt_ids:
            _require_identifier(debt_id, "debt_id")
        object.__setattr__(self, "applied_operations", operations)
        object.__setattr__(self, "settled_debt_ids", debt_ids)


@dataclass(frozen=True, slots=True)
class SlotTrade:
    operation_id: str
    donor_team_id: str
    receiver_team_id: str
    common_superior_id: str
    cycle: int
    band: RatingBand
    expected_donor_version: int
    expected_receiver_version: int
    slots: int = 1

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.donor_team_id, "donor_team_id")
        _require_identifier(self.receiver_team_id, "receiver_team_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_int(self.cycle, "cycle")
        _require_int(self.expected_donor_version, "expected_donor_version")
        _require_int(self.expected_receiver_version, "expected_receiver_version")
        if self.donor_team_id == self.receiver_team_id:
            raise InvalidInputError("a bilateral trade requires two distinct teams")
        if self.band not in (RatingBand.TOP, RatingBand.BOTTOM):
            raise InvalidInputError("only a top or bottom slot can be traded")
        _require_int(self.slots, "slots", minimum=1)
        if self.slots != 1:
            raise InvalidInputError("a B1 bilateral trade must move exactly one slot")


@dataclass(frozen=True, slots=True)
class TradeResult:
    donor_before: QuotaBook
    receiver_before: QuotaBook
    donor: QuotaBook
    receiver: QuotaBook
    trade: SlotTrade

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, QuotaBook)
            for value in (self.donor_before, self.receiver_before, self.donor, self.receiver)
        ) or not isinstance(self.trade, SlotTrade):
            raise InvalidInputError("trade result contains invalid snapshots")
        if (
            self.donor_before.team_id != self.donor.team_id
            or self.receiver_before.team_id != self.receiver.team_id
        ):
            raise ConservationError("trade result changed a team identity")
        if (
            self.donor_before.team_id != self.trade.donor_team_id
            or self.receiver_before.team_id != self.trade.receiver_team_id
            or self.donor_before.common_superior_id != self.trade.common_superior_id
            or self.receiver_before.common_superior_id != self.trade.common_superior_id
            or self.donor_before.cycle != self.trade.cycle
            or self.receiver_before.cycle != self.trade.cycle
        ):
            raise ConservationError("trade result snapshots do not match trade endpoints")
        if (
            self.donor_before.version != self.trade.expected_donor_version
            or self.receiver_before.version != self.trade.expected_receiver_version
        ):
            raise ConservationError("trade result before-images do not match expected versions")
        if (
            self.donor.counts.total != self.donor_before.counts.total
            or self.receiver.counts.total != self.receiver_before.counts.total
        ):
            raise ConservationError("trade result changed a team cohort size")
        expected_donor = self.donor_before.counts.with_delta(
            self.trade.band, -1
        ).with_delta(RatingBand.MIDDLE, 1)
        expected_receiver = self.receiver_before.counts.with_delta(
            RatingBand.MIDDLE, -1
        ).with_delta(self.trade.band, 1)
        if self.donor.counts != expected_donor or self.receiver.counts != expected_receiver:
            raise ConservationError("trade result does not contain the exact one-slot exchange")
        if (
            self.donor.version != self.donor_before.version + 1
            or self.receiver.version != self.receiver_before.version + 1
        ):
            raise ConservationError("trade result must advance both book versions exactly once")
        if (
            self.donor.applied_operations
            != self.donor_before.applied_operations | frozenset({self.trade.operation_id})
            or self.receiver.applied_operations
            != self.receiver_before.applied_operations | frozenset({self.trade.operation_id})
        ):
            raise ConservationError("trade result operation receipts are inconsistent")
        if (
            self.donor.settled_debt_ids != self.donor_before.settled_debt_ids
            or self.receiver.settled_debt_ids != self.receiver_before.settled_debt_ids
        ):
            raise ConservationError("trade result changed unrelated debt receipts")
        for band in BAND_ORDER:
            before = self.donor_before.counts[band] + self.receiver_before.counts[band]
            after = self.donor.counts[band] + self.receiver.counts[band]
            if before != after:
                raise ConservationError("trade result changed combined band counts")
        if (
            self.trade.operation_id not in self.donor.applied_operations
            or self.trade.operation_id not in self.receiver.applied_operations
        ):
            raise ConservationError("trade result did not record operation on both books")


def apply_bilateral_slot_trade(
    donor: QuotaBook, receiver: QuotaBook, trade: SlotTrade
) -> TradeResult:
    """Move one top/bottom slot and the opposite middle slot bilaterally."""

    if not all(
        isinstance(value, expected)
        for value, expected in (
            (donor, QuotaBook),
            (receiver, QuotaBook),
            (trade, SlotTrade),
        )
    ):
        raise InvalidInputError("invalid bilateral trade arguments")
    if (
        trade.operation_id in donor.applied_operations
        or trade.operation_id in receiver.applied_operations
    ):
        raise DuplicateOperationError(
            "trade operation was already applied", operation_id=trade.operation_id
        )
    if donor.team_id != trade.donor_team_id or receiver.team_id != trade.receiver_team_id:
        raise InvalidInputError("trade endpoints do not match quota books")
    if donor.common_superior_id != receiver.common_superior_id:
        raise InvalidInputError("bilateral trade requires one common superior")
    if donor.common_superior_id != trade.common_superior_id:
        raise InvalidInputError("trade common superior does not match quota books")
    if donor.cycle != trade.cycle or receiver.cycle != trade.cycle:
        raise StaleOperationError("trade cycle does not match both quota books")
    if (
        donor.version != trade.expected_donor_version
        or receiver.version != trade.expected_receiver_version
    ):
        raise StaleOperationError(
            "trade version is stale",
            donor_version=donor.version,
            receiver_version=receiver.version,
        )
    if donor.counts[trade.band] < 1:
        raise InsufficientSlotError("donor has no requested slot", band=trade.band.value)
    if receiver.counts[RatingBand.MIDDLE] < 1:
        raise InsufficientSlotError("receiver has no middle slot to exchange")

    donor_counts = donor.counts.with_delta(trade.band, -1).with_delta(
        RatingBand.MIDDLE, 1
    )
    receiver_counts = receiver.counts.with_delta(RatingBand.MIDDLE, -1).with_delta(
        trade.band, 1
    )
    for band in BAND_ORDER:
        before = donor.counts[band] + receiver.counts[band]
        after = donor_counts[band] + receiver_counts[band]
        if before != after:
            raise ConservationError(
                "bilateral trade changed the combined band count", band=band.value
            )
    if donor_counts.total != donor.counts.total or receiver_counts.total != receiver.counts.total:
        raise ConservationError("bilateral trade changed a team cohort size")

    operation_set = frozenset({trade.operation_id})
    return TradeResult(
        donor_before=donor,
        receiver_before=receiver,
        donor=replace(
            donor,
            counts=donor_counts,
            version=donor.version + 1,
            applied_operations=donor.applied_operations | operation_set,
        ),
        receiver=replace(
            receiver,
            counts=receiver_counts,
            version=receiver.version + 1,
            applied_operations=receiver.applied_operations | operation_set,
        ),
        trade=trade,
    )


class DebtKind(str, Enum):
    TOP_BORROWED = "top_borrowed"
    BOTTOM_BORROWED = "bottom_borrowed"


class DebtState(str, Enum):
    OPEN = "open"
    SETTLED = "settled"


@dataclass(frozen=True, slots=True)
class QuotaDebt:
    debt_id: str
    team_id: str
    common_superior_id: str
    kind: DebtKind
    created_cycle: int
    due_cycle: int
    source_trade_id: str
    creditor_team_id: str
    creditor_manager_id: str
    debtor_manager_id: str
    approver_id: str
    liability_id: str
    slots: int = 1
    state: DebtState = DebtState.OPEN
    settlement_operation_id: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.debt_id, "debt_id")
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.common_superior_id, "common_superior_id")
        _require_identifier(self.source_trade_id, "source_trade_id")
        _require_identifier(self.creditor_team_id, "creditor_team_id")
        _require_identifier(self.creditor_manager_id, "creditor_manager_id")
        _require_identifier(self.debtor_manager_id, "debtor_manager_id")
        _require_identifier(self.approver_id, "approver_id")
        _require_identifier(self.liability_id, "liability_id")
        _require_int(self.created_cycle, "created_cycle")
        _require_int(self.due_cycle, "due_cycle")
        if not isinstance(self.kind, DebtKind) or not isinstance(self.state, DebtState):
            raise InvalidInputError("invalid quota debt kind or state")
        if self.due_cycle != self.created_cycle + 1:
            raise InvalidInputError("quota debt must be due exactly one cycle after creation")
        if self.creditor_team_id == self.team_id:
            raise InvalidInputError("quota debt requires distinct creditor and debtor teams")
        if self.creditor_manager_id == self.debtor_manager_id:
            raise InvalidInputError("quota debt requires distinct manager parties")
        _require_int(self.slots, "slots", minimum=1)
        if self.slots != 1:
            raise InvalidInputError("B1 quota debt must contain exactly one slot")
        if self.state is DebtState.OPEN and self.settlement_operation_id is not None:
            raise InvalidInputError("open debt cannot have a settlement operation")
        if self.state is DebtState.SETTLED:
            _require_identifier(self.settlement_operation_id, "settlement_operation_id")


@dataclass(frozen=True, slots=True)
class DebtSettlement:
    book: QuotaBook
    debt: QuotaDebt
    overdue_cycles: int

    def __post_init__(self) -> None:
        if not isinstance(self.book, QuotaBook) or not isinstance(self.debt, QuotaDebt):
            raise InvalidInputError("debt settlement contains invalid snapshots")
        _require_int(self.overdue_cycles, "overdue_cycles")
        if self.debt.state is not DebtState.SETTLED:
            raise ConservationError("debt settlement must close its debt")
        if (
            self.book.team_id != self.debt.team_id
            or self.book.common_superior_id != self.debt.common_superior_id
        ):
            raise ConservationError("debt settlement book does not belong to debtor")
        if self.debt.debt_id not in self.book.settled_debt_ids:
            raise ConservationError("debt settlement book did not record debt id")
        if (
            self.debt.settlement_operation_id is None
            or self.debt.settlement_operation_id not in self.book.applied_operations
        ):
            raise ConservationError("debt settlement operation receipt is missing")
        if self.book.cycle != self.debt.due_cycle + self.overdue_cycles:
            raise ConservationError("debt settlement overdue count is inconsistent")


@dataclass(frozen=True, slots=True)
class TradeDebtTerms:
    debt_id: str
    creditor_manager_id: str
    debtor_manager_id: str
    approver_id: str
    liability_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.debt_id, "debt_id")
        _require_identifier(self.creditor_manager_id, "creditor_manager_id")
        _require_identifier(self.debtor_manager_id, "debtor_manager_id")
        _require_identifier(self.approver_id, "approver_id")
        _require_identifier(self.liability_id, "liability_id")
        if self.creditor_manager_id == self.debtor_manager_id:
            raise InvalidInputError("trade debt requires distinct manager parties")


@dataclass(frozen=True, slots=True)
class TradeWithDebtResult:
    trade_result: TradeResult
    debt: QuotaDebt

    def __post_init__(self) -> None:
        if not isinstance(self.trade_result, TradeResult) or not isinstance(
            self.debt, QuotaDebt
        ):
            raise InvalidInputError("trade-with-debt result contains invalid snapshots")
        trade = self.trade_result.trade
        expected_kind = (
            DebtKind.TOP_BORROWED
            if trade.band is RatingBand.TOP
            else DebtKind.BOTTOM_BORROWED
        )
        if (
            self.debt.source_trade_id != trade.operation_id
            or self.debt.team_id != trade.receiver_team_id
            or self.debt.creditor_team_id != trade.donor_team_id
            or self.debt.common_superior_id != trade.common_superior_id
            or self.debt.created_cycle != trade.cycle
            or self.debt.due_cycle != trade.cycle + 1
            or self.debt.kind is not expected_kind
            or self.debt.state is not DebtState.OPEN
        ):
            raise ConservationError("trade-generated debt lost its bilateral responsibility")


def apply_bilateral_slot_trade_with_debt(
    donor: QuotaBook,
    receiver: QuotaBook,
    trade: SlotTrade,
    terms: TradeDebtTerms,
) -> TradeWithDebtResult:
    """Atomically apply a one-slot trade and create its next-cycle liability."""

    if not isinstance(terms, TradeDebtTerms):
        raise InvalidInputError("terms must be TradeDebtTerms")
    result = apply_bilateral_slot_trade(donor, receiver, trade)
    kind = (
        DebtKind.TOP_BORROWED
        if trade.band is RatingBand.TOP
        else DebtKind.BOTTOM_BORROWED
    )
    debt = QuotaDebt(
        debt_id=terms.debt_id,
        team_id=receiver.team_id,
        common_superior_id=receiver.common_superior_id,
        kind=kind,
        created_cycle=trade.cycle,
        due_cycle=trade.cycle + 1,
        source_trade_id=trade.operation_id,
        creditor_team_id=donor.team_id,
        creditor_manager_id=terms.creditor_manager_id,
        debtor_manager_id=terms.debtor_manager_id,
        approver_id=terms.approver_id,
        liability_id=terms.liability_id,
    )
    return TradeWithDebtResult(trade_result=result, debt=debt)


def settle_due_debt(
    book: QuotaBook,
    debt: QuotaDebt,
    *,
    cycle: int,
    operation_id: str,
    expected_book_version: int,
) -> DebtSettlement:
    if not isinstance(book, QuotaBook) or not isinstance(debt, QuotaDebt):
        raise InvalidInputError("invalid debt settlement arguments")
    current_cycle = _require_int(cycle, "cycle")
    op_id = _require_identifier(operation_id, "operation_id")
    expected_version = _require_int(expected_book_version, "expected_book_version")
    if (
        debt.state is DebtState.SETTLED
        or debt.debt_id in book.settled_debt_ids
        or op_id in book.applied_operations
    ):
        raise DuplicateOperationError("quota debt was already settled", debt_id=debt.debt_id)
    if book.team_id != debt.team_id or book.common_superior_id != debt.common_superior_id:
        raise InvalidInputError("quota debt owner does not match the quota book")
    if current_cycle < debt.due_cycle:
        raise DebtNotDueError("quota debt is not due yet", due_cycle=debt.due_cycle)
    if book.cycle != current_cycle:
        raise StaleOperationError(
            "quota debt settlement does not match the current quota-book snapshot",
            due_cycle=debt.due_cycle,
            current_cycle=current_cycle,
            book_cycle=book.cycle,
        )
    if book.version != expected_version:
        raise StaleOperationError("quota book version is stale", version=book.version)

    if debt.kind is DebtKind.TOP_BORROWED:
        counts = book.counts.with_delta(RatingBand.TOP, -1).with_delta(
            RatingBand.MIDDLE, 1
        )
    else:
        counts = book.counts.with_delta(RatingBand.BOTTOM, -1).with_delta(
            RatingBand.MIDDLE, 1
        )
    if counts.total != book.counts.total:
        raise ConservationError("quota debt settlement changed cohort size")
    settled_book = replace(
        book,
        counts=counts,
        version=book.version + 1,
        applied_operations=book.applied_operations | frozenset({op_id}),
        settled_debt_ids=book.settled_debt_ids | frozenset({debt.debt_id}),
    )
    settled_debt = replace(
        debt,
        state=DebtState.SETTLED,
        settlement_operation_id=op_id,
    )
    return DebtSettlement(
        book=settled_book,
        debt=settled_debt,
        overdue_cycles=current_cycle - debt.due_cycle,
    )


@dataclass(frozen=True, slots=True)
class AgendaEntry:
    subject_id: str
    rank: int
    strategic: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.subject_id, "subject_id")
        _require_int(self.rank, "rank", minimum=1)
        if not isinstance(self.strategic, bool):
            raise InvalidInputError("strategic must be bool")


class AgendaMode(str, Enum):
    TOP_FIRST = "top_first"
    BOTTOM_FIRST = "bottom_first"
    STRATEGIC_FIRST = "strategic_first"
    STABLE_RANDOM = "stable_random"


@dataclass(frozen=True, slots=True)
class AgendaPlan:
    subject_ids: tuple[str, ...]
    authoritative_cohort_ids: tuple[str, ...]
    mode: AgendaMode
    seed: str

    def __post_init__(self) -> None:
        subjects = tuple(self.subject_ids)
        authority = tuple(self.authoritative_cohort_ids)
        if not isinstance(self.mode, AgendaMode):
            raise InvalidInputError("agenda plan has an invalid mode")
        _require_identifier(self.seed, "seed")
        for subject_id in subjects:
            _require_identifier(subject_id, "subject_id")
        for subject_id in authority:
            _require_identifier(subject_id, "authoritative_cohort_id")
        if len(set(subjects)) != len(subjects) or len(set(authority)) != len(authority):
            raise ConservationError("agenda plan contains duplicate subjects")
        if set(subjects) != set(authority):
            raise ConservationError("agenda plan does not equal its authoritative cohort")
        object.__setattr__(self, "subject_ids", subjects)
        object.__setattr__(self, "authoritative_cohort_ids", authority)


def build_agenda(
    entries: Iterable[AgendaEntry],
    mode: AgendaMode,
    *,
    authoritative_cohort_ids: Iterable[str],
    seed: str = "zg361-b1",
) -> AgendaPlan:
    values = tuple(entries)
    if not isinstance(mode, AgendaMode):
        raise InvalidInputError("invalid agenda mode")
    _require_identifier(seed, "seed")
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    for entry in values:
        if not isinstance(entry, AgendaEntry):
            raise InvalidInputError("agenda entries must be AgendaEntry values")
        if entry.subject_id in seen_ids or entry.rank in seen_ranks:
            raise DuplicateInputError("agenda subjects and ranks must both be unique")
        seen_ids.add(entry.subject_id)
        seen_ranks.add(entry.rank)
    authority = tuple(authoritative_cohort_ids)
    for subject_id in authority:
        _require_identifier(subject_id, "authoritative_cohort_id")
    if len(set(authority)) != len(authority):
        raise DuplicateInputError("authoritative cohort contains a duplicate subject")
    if seen_ids != set(authority):
        raise ConservationError(
            "agenda must contain every authoritative cohort subject exactly once",
            agenda_count=len(seen_ids),
            cohort_count=len(authority),
        )
    if mode is AgendaMode.TOP_FIRST:
        ordered = sorted(values, key=lambda item: (item.rank, item.subject_id))
    elif mode is AgendaMode.BOTTOM_FIRST:
        ordered = sorted(values, key=lambda item: (-item.rank, item.subject_id))
    elif mode is AgendaMode.STRATEGIC_FIRST:
        ordered = sorted(
            values, key=lambda item: (not item.strategic, item.rank, item.subject_id)
        )
    else:
        ordered = sorted(
            values,
            key=lambda item: (
                hashlib.sha256(f"{seed}\0{item.subject_id}".encode("utf-8")).digest(),
                item.subject_id,
            ),
        )
    return AgendaPlan(
        subject_ids=tuple(item.subject_id for item in ordered),
        authoritative_cohort_ids=authority,
        mode=mode,
        seed=seed,
    )


@dataclass(frozen=True, slots=True)
class FrozenCandidateGrade:
    subject_id: str
    band: RatingBand

    def __post_init__(self) -> None:
        _require_identifier(self.subject_id, "subject_id")
        if not isinstance(self.band, RatingBand):
            raise InvalidInputError("frozen candidate has an invalid rating band")


@dataclass(frozen=True, slots=True)
class AttentionSeat:
    seat_id: str
    owner_manager_id: str
    subject_id: str | None = None
    evidence_id: str | None = None
    consumed: bool = False
    minutes_used: int = 0

    def __post_init__(self) -> None:
        _require_identifier(self.seat_id, "seat_id")
        _require_identifier(self.owner_manager_id, "owner_manager_id")
        if (self.subject_id is None) != (self.evidence_id is None):
            raise ConservationError("attention seat must bind subject and evidence together")
        if self.subject_id is not None:
            _require_identifier(self.subject_id, "subject_id")
            _require_identifier(self.evidence_id, "evidence_id")
        if not isinstance(self.consumed, bool):
            raise InvalidInputError("consumed must be bool")
        _require_int(self.minutes_used, "minutes_used")
        if self.consumed and (self.subject_id is None or self.minutes_used < 1):
            raise ConservationError("a consumed attention seat must be bound and use time")
        if not self.consumed and self.minutes_used != 0:
            raise ConservationError("an unconsumed attention seat cannot use time")


@dataclass(frozen=True, slots=True)
class AttentionOvertimeReceipt:
    operation_id: str
    manager_id: str
    favored_subject_id: str
    displaced_subject_id: str
    evidence_id: str
    overtime_minutes: int
    patience_cost: int
    political_cost: int

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.manager_id, "manager_id")
        _require_identifier(self.favored_subject_id, "favored_subject_id")
        _require_identifier(self.displaced_subject_id, "displaced_subject_id")
        _require_identifier(self.evidence_id, "evidence_id")
        _require_int(self.overtime_minutes, "overtime_minutes", minimum=1)
        _require_int(self.patience_cost, "patience_cost", minimum=1)
        _require_int(self.political_cost, "political_cost", minimum=1)
        if self.favored_subject_id == self.displaced_subject_id:
            raise ConservationError("overtime must displace a different candidate")


@dataclass(frozen=True, slots=True)
class AttentionSeatLedger:
    meeting_id: str
    review_serial: int
    candidate_ids: tuple[str, ...]
    frozen_grades: tuple[FrozenCandidateGrade, ...]
    seats: tuple[AttentionSeat, ...]
    total_minutes: int
    spent_minutes: int = 0
    overtime_minutes: int = 0
    patience_cost: int = 0
    political_cost: int = 0
    overtime_receipts: tuple[AttentionOvertimeReceipt, ...] = ()
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_identifier(self.meeting_id, "meeting_id")
        _require_int(self.review_serial, "review_serial")
        _require_int(self.total_minutes, "total_minutes")
        _require_int(self.spent_minutes, "spent_minutes")
        _require_int(self.overtime_minutes, "overtime_minutes")
        _require_int(self.patience_cost, "patience_cost")
        _require_int(self.political_cost, "political_cost")
        candidate_ids = tuple(self.candidate_ids)
        frozen_grades = tuple(self.frozen_grades)
        seats = tuple(self.seats)
        for candidate_id in candidate_ids:
            _require_identifier(candidate_id, "candidate_id")
        if len(set(candidate_ids)) != len(candidate_ids):
            raise DuplicateInputError("attention candidate list contains a duplicate")
        if any(not isinstance(item, FrozenCandidateGrade) for item in frozen_grades):
            raise InvalidInputError("frozen_grades must contain FrozenCandidateGrade values")
        if {item.subject_id for item in frozen_grades} != set(candidate_ids) or len(
            frozen_grades
        ) != len(candidate_ids):
            raise ConservationError("every attention candidate needs exactly one frozen grade")
        if not seats:
            raise InvalidInputError("at least one attention seat is required")
        if any(not isinstance(seat, AttentionSeat) for seat in seats):
            raise InvalidInputError("seats must contain AttentionSeat values")
        if len({seat.seat_id for seat in seats}) != len(seats):
            raise DuplicateInputError("attention seat ids must be unique")
        bound_subjects = tuple(seat.subject_id for seat in seats if seat.subject_id is not None)
        if len(set(bound_subjects)) != len(bound_subjects):
            raise ConservationError("one candidate cannot occupy two attention seats")
        if any(subject_id not in candidate_ids for subject_id in bound_subjects):
            raise ConservationError("attention seat is bound outside the frozen candidates")
        actual_spent = sum(seat.minutes_used for seat in seats)
        if actual_spent != self.spent_minutes:
            raise ConservationError(
                "attention minutes do not conserve",
                recorded=self.spent_minutes,
                actual=actual_spent,
                total=self.total_minutes,
            )
        if self.overtime_minutes != max(0, self.spent_minutes - self.total_minutes):
            raise ConservationError("attention overtime does not match budget overrun")
        receipts = tuple(self.overtime_receipts)
        if any(not isinstance(item, AttentionOvertimeReceipt) for item in receipts):
            raise InvalidInputError("overtime_receipts contain an invalid value")
        if sum(item.overtime_minutes for item in receipts) != self.overtime_minutes:
            raise ConservationError("overtime receipts do not conserve overtime minutes")
        if sum(item.patience_cost for item in receipts) != self.patience_cost:
            raise ConservationError("overtime receipts do not conserve patience cost")
        if sum(item.political_cost for item in receipts) != self.political_cost:
            raise ConservationError("overtime receipts do not conserve political cost")
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        receipt_operations = tuple(item.operation_id for item in receipts)
        if len(set(receipt_operations)) != len(receipt_operations):
            raise ConservationError("overtime receipts reused an operation id")
        if any(operation_id not in operations for operation_id in receipt_operations):
            raise ConservationError("overtime receipt operation is missing from ledger")
        if any(
            item.favored_subject_id not in candidate_ids
            or item.displaced_subject_id not in candidate_ids
            for item in receipts
        ):
            raise ConservationError("overtime receipt escaped frozen candidates")
        object.__setattr__(self, "candidate_ids", candidate_ids)
        object.__setattr__(self, "frozen_grades", frozen_grades)
        object.__setattr__(self, "seats", seats)
        object.__setattr__(self, "overtime_receipts", receipts)
        object.__setattr__(self, "applied_operations", operations)

    @property
    def total_seats(self) -> int:
        return len(self.seats)

    @property
    def remaining_minutes(self) -> int:
        return max(0, self.total_minutes - self.spent_minutes)

    def seat(self, seat_id: str) -> AttentionSeat:
        for seat in self.seats:
            if seat.seat_id == seat_id:
                return seat
        raise InvalidInputError("unknown attention seat", seat_id=seat_id)


def open_attention_seat_ledger(
    *,
    meeting_id: str,
    review_serial: int,
    candidate_grades: Sequence[FrozenCandidateGrade],
    seat_owner_ids: Sequence[str],
    total_minutes: int,
) -> AttentionSeatLedger:
    owners = tuple(seat_owner_ids)
    if not owners:
        raise InvalidInputError("at least one attention seat owner is required")
    seats = tuple(
        AttentionSeat(seat_id=f"seat-{index}", owner_manager_id=owner_id)
        for index, owner_id in enumerate(owners, start=1)
    )
    grades = tuple(candidate_grades)
    return AttentionSeatLedger(
        meeting_id=meeting_id,
        review_serial=review_serial,
        candidate_ids=tuple(item.subject_id for item in grades),
        frozen_grades=grades,
        seats=seats,
        total_minutes=total_minutes,
    )


def _attention_preflight(
    ledger: AttentionSeatLedger, operation_id: str, expected_review_serial: int
) -> str:
    if not isinstance(ledger, AttentionSeatLedger):
        raise InvalidInputError("ledger must be AttentionSeatLedger")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    if op_id in ledger.applied_operations:
        raise DuplicateOperationError("attention-seat operation was already applied")
    if serial != ledger.review_serial:
        raise StaleOperationError("attention-seat operation targets a stale review serial")
    return op_id


def _replace_attention_seat(
    ledger: AttentionSeatLedger, updated_seat: AttentionSeat, operation_id: str
) -> AttentionSeatLedger:
    seats = tuple(
        updated_seat if seat.seat_id == updated_seat.seat_id else seat
        for seat in ledger.seats
    )
    return replace(
        ledger,
        seats=seats,
        spent_minutes=sum(seat.minutes_used for seat in seats),
        applied_operations=ledger.applied_operations | frozenset({operation_id}),
    )


def bind_attention_seat(
    ledger: AttentionSeatLedger,
    *,
    seat_id: str,
    owner_manager_id: str,
    subject_id: str,
    evidence_id: str,
    operation_id: str,
    expected_review_serial: int,
) -> AttentionSeatLedger:
    op_id = _attention_preflight(ledger, operation_id, expected_review_serial)
    owner = _require_identifier(owner_manager_id, "owner_manager_id")
    subject = _require_identifier(subject_id, "subject_id")
    evidence = _require_identifier(evidence_id, "evidence_id")
    if subject not in ledger.candidate_ids:
        raise InvalidInputError("attention subject is not a frozen candidate")
    if any(seat.subject_id == subject for seat in ledger.seats):
        raise DuplicateInputError("candidate already owns an attention seat", subject_id=subject)
    seat = ledger.seat(_require_identifier(seat_id, "seat_id"))
    if seat.owner_manager_id != owner:
        raise StaleOperationError("attention seat owner no longer matches")
    if seat.subject_id is not None or seat.consumed:
        raise IllegalStateError("attention seat is already bound or consumed")
    return _replace_attention_seat(
        ledger,
        replace(seat, subject_id=subject, evidence_id=evidence),
        op_id,
    )


def transfer_attention_seat(
    ledger: AttentionSeatLedger,
    *,
    seat_id: str,
    from_manager_id: str,
    to_manager_id: str,
    operation_id: str,
    expected_review_serial: int,
) -> AttentionSeatLedger:
    op_id = _attention_preflight(ledger, operation_id, expected_review_serial)
    source = _require_identifier(from_manager_id, "from_manager_id")
    target = _require_identifier(to_manager_id, "to_manager_id")
    if source == target:
        raise InvalidInputError("attention-seat transfer requires distinct managers")
    seat = ledger.seat(_require_identifier(seat_id, "seat_id"))
    if seat.owner_manager_id != source:
        raise StaleOperationError("attention seat owner no longer matches transfer source")
    if seat.consumed:
        raise IllegalStateError("a consumed attention seat cannot be transferred")
    before_count = ledger.total_seats
    updated = _replace_attention_seat(
        ledger, replace(seat, owner_manager_id=target), op_id
    )
    if updated.total_seats != before_count:
        raise ConservationError("attention-seat transfer changed total seats")
    return updated


def consume_attention_seat(
    ledger: AttentionSeatLedger,
    *,
    seat_id: str,
    owner_manager_id: str,
    subject_id: str,
    minutes: int,
    operation_id: str,
    expected_review_serial: int,
) -> AttentionSeatLedger:
    op_id = _attention_preflight(ledger, operation_id, expected_review_serial)
    owner = _require_identifier(owner_manager_id, "owner_manager_id")
    subject = _require_identifier(subject_id, "subject_id")
    used = _require_int(minutes, "minutes", minimum=1)
    seat = ledger.seat(_require_identifier(seat_id, "seat_id"))
    if seat.owner_manager_id != owner or seat.subject_id != subject:
        raise StaleOperationError("attention-seat binding no longer matches")
    if seat.consumed:
        raise DuplicateOperationError("attention seat was already consumed")
    if seat.evidence_id is None:
        raise IllegalStateError("attention seat must bind written evidence before use")
    if used > ledger.remaining_minutes:
        raise IllegalStateError(
            "attention time budget is exhausted",
            remaining=ledger.remaining_minutes,
            requested=used,
        )
    return _replace_attention_seat(
        ledger,
        replace(seat, consumed=True, minutes_used=used),
        op_id,
    )


def use_overtime_attention(
    ledger: AttentionSeatLedger,
    *,
    manager_id: str,
    favored_subject_id: str,
    displaced_subject_id: str,
    evidence_id: str,
    minutes: int,
    patience_cost: int,
    political_cost: int,
    operation_id: str,
    expected_review_serial: int,
) -> AttentionSeatLedger:
    """Replace one unconsumed seat, recording the displaced candidate and costs."""

    op_id = _attention_preflight(ledger, operation_id, expected_review_serial)
    manager = _require_identifier(manager_id, "manager_id")
    favored = _require_identifier(favored_subject_id, "favored_subject_id")
    displaced = _require_identifier(displaced_subject_id, "displaced_subject_id")
    evidence = _require_identifier(evidence_id, "evidence_id")
    used = _require_int(minutes, "minutes", minimum=1)
    patience = _require_int(patience_cost, "patience_cost", minimum=1)
    politics = _require_int(political_cost, "political_cost", minimum=1)
    if favored == displaced or favored not in ledger.candidate_ids:
        raise InvalidInputError("overtime favored/displaced candidates are invalid")
    if any(seat.subject_id == favored for seat in ledger.seats):
        raise DuplicateInputError("favored candidate already has an attention seat")
    displaced_seats = tuple(
        seat for seat in ledger.seats if seat.subject_id == displaced
    )
    if len(displaced_seats) != 1:
        raise InvalidInputError("overtime must identify one currently seated candidate")
    seat = displaced_seats[0]
    if seat.owner_manager_id != manager:
        raise StaleOperationError("overtime seat owner no longer matches")
    if seat.consumed:
        raise IllegalStateError("overtime cannot displace an already consumed seat")
    if used <= ledger.remaining_minutes:
        raise InvalidInputError("overtime operation must exceed the remaining time budget")
    overtime = used - ledger.remaining_minutes
    updated_seat = replace(
        seat,
        subject_id=favored,
        evidence_id=evidence,
        consumed=True,
        minutes_used=used,
    )
    seats = tuple(
        updated_seat if item.seat_id == updated_seat.seat_id else item
        for item in ledger.seats
    )
    receipt = AttentionOvertimeReceipt(
        operation_id=op_id,
        manager_id=manager,
        favored_subject_id=favored,
        displaced_subject_id=displaced,
        evidence_id=evidence,
        overtime_minutes=overtime,
        patience_cost=patience,
        political_cost=politics,
    )
    return replace(
        ledger,
        seats=seats,
        spent_minutes=sum(item.minutes_used for item in seats),
        overtime_minutes=ledger.overtime_minutes + overtime,
        patience_cost=ledger.patience_cost + patience,
        political_cost=ledger.political_cost + politics,
        overtime_receipts=ledger.overtime_receipts + (receipt,),
        applied_operations=ledger.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class AttentionLedger:
    round_id: str
    review_serial: int
    agenda: tuple[str, ...]
    total: int
    spent: int = 0
    cursor: int = 0
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_identifier(self.round_id, "round_id")
        _require_int(self.review_serial, "review_serial")
        _require_int(self.total, "total")
        _require_int(self.spent, "spent")
        _require_int(self.cursor, "cursor")
        agenda = tuple(self.agenda)
        if any(not isinstance(item, str) or not item.strip() for item in agenda):
            raise InvalidInputError("agenda must contain non-empty subject ids")
        if len(set(agenda)) != len(agenda):
            raise DuplicateInputError("agenda contains a duplicate subject")
        if self.spent > self.total:
            raise ConservationError("attention spent exceeds total")
        if self.cursor > len(agenda):
            raise ConservationError("agenda cursor exceeds agenda size")
        if self.spent < self.cursor:
            raise ConservationError("each discussed agenda item must spend attention")
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        object.__setattr__(self, "agenda", agenda)
        object.__setattr__(self, "applied_operations", operations)

    @property
    def remaining(self) -> int:
        return self.total - self.spent

    @property
    def discussed(self) -> tuple[str, ...]:
        return self.agenda[: self.cursor]


def spend_attention(
    ledger: AttentionLedger,
    *,
    subject_id: str,
    cost: int,
    operation_id: str,
    expected_review_serial: int,
) -> AttentionLedger:
    if not isinstance(ledger, AttentionLedger):
        raise InvalidInputError("ledger must be AttentionLedger")
    subject = _require_identifier(subject_id, "subject_id")
    op_id = _require_identifier(operation_id, "operation_id")
    units = _require_int(cost, "cost", minimum=1)
    serial = _require_int(expected_review_serial, "expected_review_serial")
    if op_id in ledger.applied_operations:
        raise DuplicateOperationError("attention operation was already applied")
    if serial != ledger.review_serial:
        raise StaleOperationError("attention operation targets a stale review serial")
    if ledger.cursor >= len(ledger.agenda):
        raise IllegalStateError("the calibration agenda is exhausted")
    expected_subject = ledger.agenda[ledger.cursor]
    if subject != expected_subject:
        raise IllegalStateError(
            "attention must follow the frozen agenda",
            expected_subject=expected_subject,
            actual_subject=subject,
        )
    if units > ledger.remaining:
        raise IllegalStateError(
            "attention budget is exhausted", remaining=ledger.remaining, requested=units
        )
    updated = replace(
        ledger,
        spent=ledger.spent + units,
        cursor=ledger.cursor + 1,
        applied_operations=ledger.applied_operations | frozenset({op_id}),
    )
    if updated.spent + updated.remaining != updated.total:
        raise ConservationError("attention budget did not conserve")
    return updated


@dataclass(frozen=True, slots=True)
class PendingSlot:
    hold_id: str
    subject_id: str
    band: RatingBand
    fallback_band: RatingBand
    milestone_id: str
    verifier_id: str
    deadline_cycle: int
    frozen_reward: Fraction

    def __post_init__(self) -> None:
        _require_identifier(self.hold_id, "hold_id")
        _require_identifier(self.subject_id, "subject_id")
        _require_identifier(self.milestone_id, "milestone_id")
        _require_identifier(self.verifier_id, "verifier_id")
        _require_int(self.deadline_cycle, "deadline_cycle", minimum=1)
        if not isinstance(self.band, RatingBand) or not isinstance(
            self.fallback_band, RatingBand
        ):
            raise InvalidInputError("pending slot has an invalid rating band")
        if self.fallback_band is RatingBand.TOP:
            raise InvalidInputError("failed or timed-out milestone cannot resolve to TOP")
        reward = _as_fraction(self.frozen_reward, "frozen_reward")
        if reward < 0:
            raise InvalidInputError("frozen pending reward cannot be negative")
        object.__setattr__(self, "frozen_reward", reward)


class PendingResolution(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class PendingResolutionRecord:
    hold_id: str
    subject_id: str
    milestone_id: str
    verifier_id: str
    held_band: RatingBand
    fallback_band: RatingBand
    deadline_cycle: int
    resolution: PendingResolution
    resolved_cycle: int
    final_band: RatingBand
    frozen_reward: Fraction

    def __post_init__(self) -> None:
        _require_identifier(self.hold_id, "hold_id")
        _require_identifier(self.subject_id, "subject_id")
        _require_identifier(self.milestone_id, "milestone_id")
        _require_identifier(self.verifier_id, "verifier_id")
        _require_int(self.deadline_cycle, "deadline_cycle", minimum=1)
        _require_int(self.resolved_cycle, "resolved_cycle", minimum=1)
        if not isinstance(self.resolution, PendingResolution) or any(
            not isinstance(value, RatingBand)
            for value in (self.held_band, self.fallback_band, self.final_band)
        ):
            raise InvalidInputError("invalid pending resolution record")
        if self.fallback_band is RatingBand.TOP:
            raise ConservationError("pending fallback cannot be TOP")
        expected_band = (
            self.held_band
            if self.resolution is PendingResolution.SUCCESS
            else self.fallback_band
        )
        if self.final_band is not expected_band:
            raise ConservationError("pending resolution changed its frozen band contract")
        if self.resolution is PendingResolution.TIMEOUT:
            if self.resolved_cycle < self.deadline_cycle:
                raise ConservationError("pending timeout predates its deadline")
        elif self.resolved_cycle > self.deadline_cycle:
            raise ConservationError("late pending result must be recorded as timeout")
        reward = _as_fraction(self.frozen_reward, "frozen_reward")
        if reward < 0:
            raise InvalidInputError("resolved frozen reward cannot be negative")
        if self.resolution is not PendingResolution.SUCCESS and self.final_band is RatingBand.TOP:
            raise ConservationError("failed or timed-out milestone resolved to TOP")
        object.__setattr__(self, "frozen_reward", reward)


@dataclass(frozen=True, slots=True)
class PendingSlotLedger:
    round_id: str
    review_serial: int
    quota: QuotaCounts
    free: QuotaCounts
    committed: QuotaCounts
    pending_slots: tuple[PendingSlot, ...] = ()
    resolved: tuple[PendingResolutionRecord, ...] = ()
    applied_operations: frozenset[str] = frozenset()
    used_hold_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_identifier(self.round_id, "round_id")
        _require_int(self.review_serial, "review_serial")
        if not all(
            isinstance(value, QuotaCounts) for value in (self.quota, self.free, self.committed)
        ):
            raise InvalidInputError("quota/free/committed must be QuotaCounts")
        pending_slots = tuple(self.pending_slots)
        resolved = tuple(self.resolved)
        if any(not isinstance(item, PendingSlot) for item in pending_slots):
            raise InvalidInputError("pending_slots must contain PendingSlot values")
        if any(not isinstance(item, PendingResolutionRecord) for item in resolved):
            raise InvalidInputError("resolved must contain PendingResolutionRecord values")
        pending_ids = tuple(item.hold_id for item in pending_slots)
        resolved_ids = tuple(item.hold_id for item in resolved)
        pending_subjects = tuple(item.subject_id for item in pending_slots)
        resolved_subjects = tuple(item.subject_id for item in resolved)
        if (
            len(set(pending_ids)) != len(pending_ids)
            or len(set(resolved_ids)) != len(resolved_ids)
        ):
            raise ConservationError("pending/resolved hold ids must be unique")
        if set(pending_ids) & set(resolved_ids):
            raise ConservationError("one hold cannot be both pending and resolved")
        all_subjects = pending_subjects + resolved_subjects
        if len(set(all_subjects)) != len(all_subjects):
            raise ConservationError("one subject cannot occupy two pending contracts")
        for band in BAND_ORDER:
            held = sum(item.band is band for item in pending_slots)
            actual = self.free[band] + self.committed[band] + held
            if actual != self.quota[band]:
                raise ConservationError(
                    "pending-slot ledger does not conserve a rating band",
                    band=band.value,
                    expected=self.quota[band],
                    actual=actual,
                )
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        hold_ids = frozenset(self.used_hold_ids)
        for hold_id in hold_ids:
            _require_identifier(hold_id, "hold_id")
        if set(pending_ids) | set(resolved_ids) != set(hold_ids):
            raise ConservationError("used hold ids must exactly equal pending/resolved receipts")
        object.__setattr__(self, "pending_slots", pending_slots)
        object.__setattr__(self, "resolved", resolved)
        object.__setattr__(self, "applied_operations", operations)
        object.__setattr__(self, "used_hold_ids", hold_ids)


def open_pending_slot_ledger(
    *, round_id: str, review_serial: int, quota: QuotaCounts
) -> PendingSlotLedger:
    return PendingSlotLedger(
        round_id=round_id,
        review_serial=review_serial,
        quota=quota,
        free=quota,
        committed=QuotaCounts(),
    )


def hold_pending_slot(
    ledger: PendingSlotLedger,
    *,
    hold_id: str,
    subject_id: str,
    band: RatingBand,
    fallback_band: RatingBand,
    milestone_id: str,
    verifier_id: str,
    deadline_cycle: int,
    frozen_reward: Fraction,
    operation_id: str,
    expected_review_serial: int,
) -> PendingSlotLedger:
    if not isinstance(ledger, PendingSlotLedger):
        raise InvalidInputError("ledger must be PendingSlotLedger")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    if op_id in ledger.applied_operations:
        raise DuplicateOperationError("pending-slot hold was already applied")
    if serial != ledger.review_serial:
        raise StaleOperationError("pending-slot hold targets a stale review serial")
    hold = _require_identifier(hold_id, "hold_id")
    if hold in ledger.used_hold_ids:
        raise DuplicateOperationError("pending-slot hold id was already used", hold_id=hold)
    if not isinstance(band, RatingBand):
        raise InvalidInputError("invalid pending-slot rating band")
    subject = _require_identifier(subject_id, "subject_id")
    if any(
        item.subject_id == subject
        for item in ledger.pending_slots + ledger.resolved
    ):
        raise DuplicateOperationError(
            "subject already has a pending-slot contract", subject_id=subject
        )
    if ledger.free[band] < 1:
        raise InsufficientSlotError("no free slot is available to hold", band=band.value)
    pending = PendingSlot(
        hold_id=hold,
        subject_id=subject,
        band=band,
        fallback_band=fallback_band,
        milestone_id=milestone_id,
        verifier_id=verifier_id,
        deadline_cycle=deadline_cycle,
        frozen_reward=frozen_reward,
    )
    return replace(
        ledger,
        free=ledger.free.with_delta(band, -1),
        pending_slots=ledger.pending_slots + (pending,),
        applied_operations=ledger.applied_operations | frozenset({op_id}),
        used_hold_ids=ledger.used_hold_ids | frozenset({hold}),
    )


def resolve_pending_slot(
    ledger: PendingSlotLedger,
    *,
    hold_id: str,
    subject_id: str,
    verifier_id: str,
    current_cycle: int,
    resolution: PendingResolution,
    operation_id: str,
    expected_review_serial: int,
) -> PendingSlotLedger:
    if not isinstance(ledger, PendingSlotLedger):
        raise InvalidInputError("ledger must be PendingSlotLedger")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    if op_id in ledger.applied_operations:
        raise DuplicateOperationError("pending-slot resolution was already applied")
    if serial != ledger.review_serial:
        raise StaleOperationError("pending-slot resolution targets a stale review serial")
    hold = _require_identifier(hold_id, "hold_id")
    subject = _require_identifier(subject_id, "subject_id")
    verifier = _require_identifier(verifier_id, "verifier_id")
    cycle = _require_int(current_cycle, "current_cycle", minimum=1)
    if not isinstance(resolution, PendingResolution):
        raise InvalidInputError("invalid pending-slot resolution")
    if any(item.hold_id == hold for item in ledger.resolved):
        raise DuplicateOperationError("pending slot was already resolved", hold_id=hold)
    pending = next((item for item in ledger.pending_slots if item.hold_id == hold), None)
    if pending is None:
        raise IllegalStateError("there is no pending slot with this hold id")
    if pending.subject_id != subject or pending.verifier_id != verifier:
        raise StaleOperationError("pending-slot identity no longer matches")
    if resolution is PendingResolution.TIMEOUT:
        if cycle < pending.deadline_cycle:
            raise IllegalStateError("pending milestone has not reached its timeout")
    elif cycle > pending.deadline_cycle:
        raise StaleOperationError("late success/failure must resolve as TIMEOUT")
    band = pending.band
    final_band = band if resolution is PendingResolution.SUCCESS else pending.fallback_band
    free = ledger.free
    committed = ledger.committed
    if resolution is PendingResolution.SUCCESS:
        committed = committed.with_delta(band, 1)
    else:
        free = free.with_delta(band, 1)
        if free[final_band] < 1:
            raise InsufficientSlotError(
                "fallback band has no free slot", band=final_band.value
            )
        free = free.with_delta(final_band, -1)
        committed = committed.with_delta(final_band, 1)
    record = PendingResolutionRecord(
        hold_id=hold,
        subject_id=subject,
        milestone_id=pending.milestone_id,
        verifier_id=verifier,
        held_band=pending.band,
        fallback_band=pending.fallback_band,
        deadline_cycle=pending.deadline_cycle,
        resolution=resolution,
        resolved_cycle=cycle,
        final_band=final_band,
        frozen_reward=pending.frozen_reward,
    )
    return replace(
        ledger,
        free=free,
        committed=committed,
        pending_slots=tuple(item for item in ledger.pending_slots if item.hold_id != hold),
        resolved=ledger.resolved + (record,),
        applied_operations=ledger.applied_operations | frozenset({op_id}),
    )


class EvidencePolarity(str, Enum):
    SUCCESS = "success"
    INCIDENT = "incident"


@dataclass(frozen=True, slots=True)
class LateEvidence:
    evidence_id: str
    polarity: EvidencePolarity
    magnitude: Fraction

    def __post_init__(self) -> None:
        _require_identifier(self.evidence_id, "evidence_id")
        if not isinstance(self.polarity, EvidencePolarity):
            raise InvalidInputError("invalid late-evidence polarity")
        magnitude = _as_fraction(self.magnitude, "magnitude")
        if magnitude <= 0:
            raise InvalidInputError("late-evidence magnitude must be positive")
        object.__setattr__(self, "magnitude", magnitude)


@dataclass(frozen=True, slots=True)
class SymmetricReopenPolicy:
    threshold: Fraction

    def __post_init__(self) -> None:
        threshold = _as_fraction(self.threshold, "threshold")
        if threshold <= 0:
            raise InvalidInputError("reopen threshold must be positive")
        object.__setattr__(self, "threshold", threshold)


class ClosurePhase(str, Enum):
    SEALED = "sealed"
    REOPENED = "reopened"
    RESEALED = "resealed"
    REWARDS_ISSUED = "rewards_issued"


@dataclass(frozen=True, slots=True)
class BoardRecalculationReceipt:
    receipt_id: str
    source_board_hash: str
    evidence_id: str
    recomputed_board_hash: str
    recomputed_quota: QuotaCounts
    reward_snapshot_hash: str

    def __post_init__(self) -> None:
        _require_identifier(self.receipt_id, "receipt_id")
        _require_identifier(self.source_board_hash, "source_board_hash")
        _require_identifier(self.evidence_id, "evidence_id")
        _require_identifier(self.recomputed_board_hash, "recomputed_board_hash")
        _require_identifier(self.reward_snapshot_hash, "reward_snapshot_hash")
        if not isinstance(self.recomputed_quota, QuotaCounts):
            raise InvalidInputError("recomputed_quota must be QuotaCounts")


@dataclass(frozen=True, slots=True)
class ClosedCalibrationRound:
    round_id: str
    review_serial: int
    quota: QuotaCounts
    sealed_board_cycle_id: str
    board_hash: str
    reward_snapshot_hash: str
    phase: ClosurePhase = ClosurePhase.SEALED
    reopen_count: int = 0
    accepted_evidence: LateEvidence | None = None
    recalculation_receipt: BoardRecalculationReceipt | None = None
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_identifier(self.round_id, "round_id")
        _require_identifier(self.sealed_board_cycle_id, "sealed_board_cycle_id")
        _require_identifier(self.board_hash, "board_hash")
        _require_identifier(self.reward_snapshot_hash, "reward_snapshot_hash")
        _require_int(self.review_serial, "review_serial")
        _require_int(self.reopen_count, "reopen_count")
        if not isinstance(self.quota, QuotaCounts) or not isinstance(self.phase, ClosurePhase):
            raise InvalidInputError("invalid closed calibration round")
        if self.reopen_count > 1:
            raise ConservationError("a B1 round may reopen at most once")
        if self.phase in (ClosurePhase.REOPENED, ClosurePhase.RESEALED) and (
            self.reopen_count != 1
        ):
            raise ConservationError("reopened/resealed phase requires exactly one reopen")
        if self.phase is ClosurePhase.SEALED and self.reopen_count != 0:
            raise ConservationError("initial sealed phase cannot already contain a reopen")
        if self.reopen_count == 0 and self.accepted_evidence is not None:
            raise ConservationError("unreopened round cannot retain accepted late evidence")
        if self.reopen_count == 1 and not isinstance(self.accepted_evidence, LateEvidence):
            raise ConservationError("reopened round must retain its accepted late evidence")
        if self.phase is ClosurePhase.REOPENED and self.recalculation_receipt is not None:
            raise ConservationError("unresealed round cannot contain a recalculation receipt")
        if self.phase is ClosurePhase.RESEALED and not isinstance(
            self.recalculation_receipt, BoardRecalculationReceipt
        ):
            raise ConservationError("resealed round requires a board recalculation receipt")
        if self.phase is ClosurePhase.REWARDS_ISSUED:
            if self.reopen_count == 0 and (
                self.accepted_evidence is not None
                or self.recalculation_receipt is not None
            ):
                raise ConservationError("initial reward snapshot cannot claim a reopen")
            if self.reopen_count == 1 and not isinstance(
                self.recalculation_receipt, BoardRecalculationReceipt
            ):
                raise ConservationError("reopened reward snapshot requires recalculation")
        if self.recalculation_receipt is not None:
            if self.reopen_count != 1:
                raise ConservationError("board recalculation requires one accepted reopen")
            if self.recalculation_receipt.recomputed_board_hash != self.board_hash:
                raise ConservationError("current board hash must match recalculation receipt")
            if self.recalculation_receipt.reward_snapshot_hash != self.reward_snapshot_hash:
                raise ConservationError("current reward snapshot must match recalculation receipt")
            if self.recalculation_receipt.recomputed_quota != self.quota:
                raise ConservationError("current quota must match recalculation receipt")
            if (
                self.accepted_evidence is None
                or self.recalculation_receipt.evidence_id
                != self.accepted_evidence.evidence_id
            ):
                raise ConservationError("recalculation receipt lost accepted evidence")
        operations = frozenset(self.applied_operations)
        for operation_id in operations:
            _require_identifier(operation_id, "operation_id")
        object.__setattr__(self, "applied_operations", operations)


def request_symmetric_reopen(
    snapshot: ClosedCalibrationRound,
    evidence: LateEvidence,
    policy: SymmetricReopenPolicy,
    *,
    operation_id: str,
    expected_review_serial: int,
    expected_board_cycle_id: str,
    expected_board_hash: str,
) -> ClosedCalibrationRound:
    if not isinstance(snapshot, ClosedCalibrationRound):
        raise InvalidInputError("snapshot must be ClosedCalibrationRound")
    if not isinstance(evidence, LateEvidence) or not isinstance(policy, SymmetricReopenPolicy):
        raise InvalidInputError("invalid symmetric-reopen evidence or policy")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    cycle_id = _require_identifier(expected_board_cycle_id, "expected_board_cycle_id")
    board_hash = _require_identifier(expected_board_hash, "expected_board_hash")
    if op_id in snapshot.applied_operations:
        raise DuplicateOperationError("reopen operation was already applied")
    if serial != snapshot.review_serial:
        raise StaleOperationError("reopen operation targets a stale review serial")
    if cycle_id != snapshot.sealed_board_cycle_id or board_hash != snapshot.board_hash:
        raise StaleOperationError("reopen operation targets a stale sealed board")
    if snapshot.reopen_count >= 1:
        raise DuplicateOperationError("a B1 round cannot reopen twice")
    if snapshot.phase is not ClosurePhase.SEALED:
        raise IllegalStateError("only a sealed, unpaid round may reopen")
    if evidence.magnitude < policy.threshold:
        raise ThresholdNotMetError(
            "late evidence does not meet the symmetric reopen threshold",
            magnitude=str(evidence.magnitude),
            threshold=str(policy.threshold),
        )
    return replace(
        snapshot,
        phase=ClosurePhase.REOPENED,
        reopen_count=1,
        accepted_evidence=evidence,
        applied_operations=snapshot.applied_operations | frozenset({op_id}),
    )


def reseal_reopened_round(
    snapshot: ClosedCalibrationRound,
    *,
    receipt: BoardRecalculationReceipt,
    operation_id: str,
    expected_review_serial: int,
    expected_board_hash: str,
) -> ClosedCalibrationRound:
    if not isinstance(snapshot, ClosedCalibrationRound):
        raise InvalidInputError("snapshot must be ClosedCalibrationRound")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    old_hash = _require_identifier(expected_board_hash, "expected_board_hash")
    if op_id in snapshot.applied_operations:
        raise DuplicateOperationError("reseal operation was already applied")
    if serial != snapshot.review_serial:
        raise StaleOperationError("reseal operation targets a stale review serial")
    if old_hash != snapshot.board_hash:
        raise StaleOperationError("reseal operation targets a stale board hash")
    if snapshot.phase in (ClosurePhase.RESEALED, ClosurePhase.REWARDS_ISSUED):
        raise DuplicateOperationError("reopened board was already resealed")
    if snapshot.phase is not ClosurePhase.REOPENED:
        raise IllegalStateError("only a reopened round can be resealed")
    if not isinstance(receipt, BoardRecalculationReceipt):
        raise InvalidInputError("receipt must be BoardRecalculationReceipt")
    if snapshot.accepted_evidence is None:
        raise ConservationError("reopened round lost accepted evidence")
    if receipt.source_board_hash != snapshot.board_hash:
        raise StaleOperationError("recalculation receipt used a stale source board")
    if receipt.evidence_id != snapshot.accepted_evidence.evidence_id:
        raise StaleOperationError("recalculation receipt used different late evidence")
    if receipt.recomputed_quota.total != snapshot.quota.total:
        raise ConservationError("recalculation changed the cohort size")
    if receipt.recomputed_quota != snapshot.quota:
        raise ConservationError("recalculation changed frozen 30/60/10 quota counts")
    return replace(
        snapshot,
        phase=ClosurePhase.RESEALED,
        quota=receipt.recomputed_quota,
        board_hash=receipt.recomputed_board_hash,
        reward_snapshot_hash=receipt.reward_snapshot_hash,
        recalculation_receipt=receipt,
        applied_operations=snapshot.applied_operations | frozenset({op_id}),
    )


def issue_rewards(
    snapshot: ClosedCalibrationRound,
    *,
    operation_id: str,
    expected_review_serial: int,
    expected_board_hash: str,
    expected_reward_snapshot_hash: str,
) -> ClosedCalibrationRound:
    if not isinstance(snapshot, ClosedCalibrationRound):
        raise InvalidInputError("snapshot must be ClosedCalibrationRound")
    op_id = _require_identifier(operation_id, "operation_id")
    serial = _require_int(expected_review_serial, "expected_review_serial")
    board_hash = _require_identifier(expected_board_hash, "expected_board_hash")
    reward_hash = _require_identifier(
        expected_reward_snapshot_hash, "expected_reward_snapshot_hash"
    )
    if op_id in snapshot.applied_operations:
        raise DuplicateOperationError("reward operation was already applied")
    if serial != snapshot.review_serial:
        raise StaleOperationError("reward operation targets a stale review serial")
    if board_hash != snapshot.board_hash or reward_hash != snapshot.reward_snapshot_hash:
        raise StaleOperationError("reward operation targets a stale board/reward snapshot")
    if snapshot.phase is ClosurePhase.REWARDS_ISSUED:
        raise DuplicateOperationError("rewards were already issued")
    if snapshot.phase not in (ClosurePhase.SEALED, ClosurePhase.RESEALED):
        raise IllegalStateError("rewards require a sealed round")
    return replace(
        snapshot,
        phase=ClosurePhase.REWARDS_ISSUED,
        applied_operations=snapshot.applied_operations | frozenset({op_id}),
    )


__all__ = [
    "AgendaEntry",
    "AgendaMode",
    "AgendaPlan",
    "AttentionLedger",
    "AttentionOvertimeReceipt",
    "AttentionSeat",
    "AttentionSeatLedger",
    "BAND_ORDER",
    "BandRounding",
    "BoardRecalculationReceipt",
    "ClosedCalibrationRound",
    "ClosurePhase",
    "CohortMember",
    "CK3_IMPLEMENTED",
    "CommonSuperiorPool",
    "ConservationError",
    "DebtKind",
    "DebtNotDueError",
    "DebtSettlement",
    "DebtState",
    "DEFAULT_WEIGHTS",
    "DuplicateInputError",
    "DuplicateOperationError",
    "EligibilityPolicy",
    "EligibilityTreatment",
    "EvidencePolarity",
    "FrozenCandidateGrade",
    "IllegalStateError",
    "InsufficientSlotError",
    "InvalidInputError",
    "LateEvidence",
    "LockedCohort",
    "MemberEligibility",
    "MINIMUM_FORCED_COHORT",
    "PendingResolution",
    "PendingResolutionRecord",
    "PendingSlot",
    "PendingSlotLedger",
    "QuotaBook",
    "QuotaComputation",
    "QuotaCounts",
    "QuotaDebt",
    "QuotaModelError",
    "RatingBand",
    "READINESS",
    "RedCode",
    "RosterAuditState",
    "RosterChangeReceipt",
    "SlotTrade",
    "StaleOperationError",
    "SymmetricReopenPolicy",
    "TeamCohort",
    "ThresholdNotMetError",
    "TradeResult",
    "apply_bilateral_slot_trade",
    "TradeDebtTerms",
    "TradeWithDebtResult",
    "apply_bilateral_slot_trade_with_debt",
    "apply_roster_change",
    "bind_attention_seat",
    "build_agenda",
    "compute_quota",
    "consume_attention_seat",
    "hold_pending_slot",
    "issue_rewards",
    "lock_cohort",
    "open_attention_seat_ledger",
    "open_pending_slot_ledger",
    "open_roster_audit",
    "pool_by_common_superior",
    "request_symmetric_reopen",
    "reseal_reopened_round",
    "resolve_pending_slot",
    "settle_due_debt",
    "spend_attention",
    "transfer_attention_seat",
    "use_overtime_attention",
]
