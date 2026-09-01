#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic B1 quota/calibration reference model.

This module is deliberately independent from the CK3 generator and runtime.  It
models deterministic quota/calibration primitives plus explicit A/B/C reference
objects for #135-#145.  Generators, static tests, and fixtures can reuse these
immutable transitions without claiming that CK3 scripts implement them yet.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
import hashlib
import json
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence


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
    # A D+0 member who later leaves remains in the frozen review denominator.
    # Explicit route C may still pass EXCLUDE; gray-route C charging is modeled
    # separately and can never alter this denominator.
    leaver: EligibilityTreatment = EligibilityTreatment.INCLUDE
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


# ---------------------------------------------------------------------------
# Numbered B1 semantic reference objects (#135-#145)
# ---------------------------------------------------------------------------


class PolicyRoute(str, Enum):
    """The three product choices used by one numbered mechanism."""

    A = "a"
    B = "b"
    C = "c"


@dataclass(frozen=True, slots=True)
class CaseIdentity:
    """Five-field authority identity carried by every numbered transition.

    ``state`` is deliberately part of the identity.  A delayed consumer with
    the right owner/subject/cycle/case but an old state is still stale.
    """

    owner_id: str
    subject_id: str
    cycle: int
    case_serial: int
    state: str

    def __post_init__(self) -> None:
        _require_identifier(self.owner_id, "owner_id")
        _require_identifier(self.subject_id, "subject_id")
        _require_int(self.cycle, "cycle", minimum=1)
        _require_int(self.case_serial, "case_serial", minimum=1)
        _require_identifier(self.state, "state")

    @property
    def stable_key(self) -> tuple[str, str, int, int]:
        return (self.owner_id, self.subject_id, self.cycle, self.case_serial)

    def advanced(self, state: str) -> CaseIdentity:
        return replace(self, state=_require_identifier(state, "state"))


@dataclass(frozen=True, slots=True)
class PolicyDecisionReceipt:
    mechanism_id: int
    identity: CaseIdentity
    route: PolicyRoute
    operation_id: str
    business_object_created: bool
    policy_debt_delta: int

    def __post_init__(self) -> None:
        _require_int(self.mechanism_id, "mechanism_id", minimum=1)
        if not isinstance(self.identity, CaseIdentity):
            raise InvalidInputError("policy decision requires a CaseIdentity")
        if not isinstance(self.route, PolicyRoute):
            raise InvalidInputError("policy decision has an invalid route")
        _require_identifier(self.operation_id, "operation_id")
        if not isinstance(self.business_object_created, bool):
            raise InvalidInputError("business_object_created must be bool")
        _require_int(self.policy_debt_delta, "policy_debt_delta")
        if self.route is PolicyRoute.C:
            if self.business_object_created or self.policy_debt_delta != 1:
                raise ConservationError(
                    "route C must create no business object and add exactly one debt"
                )
        elif not self.business_object_created or self.policy_debt_delta != 0:
            raise ConservationError(
                "route A/B must create one business object without policy debt"
            )

    @property
    def decision_key(self) -> tuple[int, str, str, int, int]:
        return (self.mechanism_id, *self.identity.stable_key)


@dataclass(frozen=True, slots=True)
class PolicyDecisionLedger:
    policy_debt: int = 0
    receipts: tuple[PolicyDecisionReceipt, ...] = ()

    def __post_init__(self) -> None:
        _require_int(self.policy_debt, "policy_debt")
        receipts = tuple(self.receipts)
        if any(not isinstance(item, PolicyDecisionReceipt) for item in receipts):
            raise InvalidInputError("policy decision ledger contains an invalid receipt")
        operations = tuple(item.operation_id for item in receipts)
        decisions = tuple(item.decision_key for item in receipts)
        if len(set(operations)) != len(operations):
            raise ConservationError("policy decision operation ids must be unique")
        if len(set(decisions)) != len(decisions):
            raise ConservationError("one numbered case cannot choose twice")
        if sum(item.policy_debt_delta for item in receipts) != self.policy_debt:
            raise ConservationError("policy debt does not equal its decision receipts")
        object.__setattr__(self, "receipts", receipts)


@dataclass(frozen=True, slots=True)
class PolicyOpenResult:
    receipt: PolicyDecisionReceipt
    ledger: PolicyDecisionLedger
    business_object: object | None

    def __post_init__(self) -> None:
        if not isinstance(self.receipt, PolicyDecisionReceipt) or not isinstance(
            self.ledger, PolicyDecisionLedger
        ):
            raise InvalidInputError("invalid policy-open result")
        if self.receipt not in self.ledger.receipts:
            raise ConservationError("policy-open result lost its decision receipt")
        if self.receipt.business_object_created != (self.business_object is not None):
            raise ConservationError("policy receipt contradicts its business object")


def _record_policy_decision(
    ledger: PolicyDecisionLedger,
    *,
    mechanism_id: int,
    identity: CaseIdentity,
    route: PolicyRoute,
    operation_id: str,
    business_object: object | None,
) -> PolicyOpenResult:
    if not isinstance(ledger, PolicyDecisionLedger):
        raise InvalidInputError("ledger must be PolicyDecisionLedger")
    if not isinstance(identity, CaseIdentity) or not isinstance(route, PolicyRoute):
        raise InvalidInputError("invalid policy identity or route")
    if identity.state != "policy_open":
        raise StaleOperationError("numbered mechanism must open from policy_open")
    mechanism = _require_int(mechanism_id, "mechanism_id", minimum=1)
    op_id = _require_identifier(operation_id, "operation_id")
    if any(item.operation_id == op_id for item in ledger.receipts):
        raise DuplicateOperationError("policy decision operation was already applied")
    decision_key = (mechanism, *identity.stable_key)
    if any(item.decision_key == decision_key for item in ledger.receipts):
        raise DuplicateOperationError("numbered policy case already chose a route")
    if route is PolicyRoute.C and business_object is not None:
        raise ConservationError("route C cannot smuggle in a business object")
    if route is not PolicyRoute.C and business_object is None:
        raise ConservationError("route A/B must produce a business object")
    delta = 1 if route is PolicyRoute.C else 0
    receipt = PolicyDecisionReceipt(
        mechanism_id=mechanism,
        identity=identity,
        route=route,
        operation_id=op_id,
        business_object_created=business_object is not None,
        policy_debt_delta=delta,
    )
    updated = replace(
        ledger,
        policy_debt=ledger.policy_debt + delta,
        receipts=ledger.receipts + (receipt,),
    )
    return PolicyOpenResult(receipt, updated, business_object)


def _case_preflight(
    actual: CaseIdentity,
    expected: CaseIdentity,
    applied_operations: frozenset[str],
    operation_id: str,
) -> str:
    if not isinstance(actual, CaseIdentity) or not isinstance(expected, CaseIdentity):
        raise InvalidInputError("transition requires exact case identities")
    op_id = _require_identifier(operation_id, "operation_id")
    if op_id in applied_operations:
        raise DuplicateOperationError("case transition operation was already applied")
    if actual != expected:
        raise StaleOperationError(
            "case transition targets a stale five-field identity",
            actual=actual,
            expected=expected,
        )
    return op_id


def _route_c_result(
    ledger: PolicyDecisionLedger,
    *,
    mechanism_id: int,
    identity: CaseIdentity,
    route: PolicyRoute,
    operation_id: str,
) -> PolicyOpenResult | None:
    if route is not PolicyRoute.C:
        return None
    return _record_policy_decision(
        ledger,
        mechanism_id=mechanism_id,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=None,
    )


@dataclass(frozen=True, slots=True)
class ShadowRatingCase:
    identity: CaseIdentity
    route: PolicyRoute
    shadow_object_id: int
    shadow_band: RatingBand
    notice_day: int
    deadline_day: int
    gap_ids: tuple[str, ...]
    gap_magnitude: int
    disclosed: bool
    accepted_evidence_ids: tuple[str, ...] = ()
    evidence_object_id: int | None = None
    evidence_revision: int = 0
    evidence_delta: int = 0
    response_code: int = 0
    response_day: int | None = None
    new_evidence: bool = False
    final_band: RatingBand | None = None
    final_explanation: str | None = None
    final_drop: int = 0
    drop_explained: bool = False
    quota_committed: bool = False
    reward_issued: bool = False
    feedback_debt_delta: int = 0
    appeal_weight_delta: int = 0
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "shadow_window_open",
            "shadow_finalized",
        ):
            raise InvalidInputError("shadow case has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("shadow business case only supports route A/B")
        expected_object_id = self.identity.case_serial * 100 + 35
        if self.shadow_object_id != expected_object_id:
            raise ConservationError("shadow object id escaped its case identity")
        if not isinstance(self.shadow_band, RatingBand):
            raise InvalidInputError("shadow case has an invalid band")
        _require_int(self.notice_day, "notice_day", minimum=1)
        _require_int(self.deadline_day, "deadline_day", minimum=1)
        if self.notice_day >= self.deadline_day:
            raise ConservationError("shadow notice must precede its evidence deadline")
        _require_int(self.gap_magnitude, "gap_magnitude")
        gaps = tuple(self.gap_ids)
        evidence = tuple(self.accepted_evidence_ids)
        for item in gaps:
            _require_identifier(item, "gap_id")
        for item in evidence:
            _require_identifier(item, "evidence_id")
        if len(set(gaps)) != len(gaps) or len(set(evidence)) != len(evidence):
            raise DuplicateInputError("shadow gaps/evidence must be unique")
        revision = _require_int(self.evidence_revision, "evidence_revision")
        delta = _require_signed_int(self.evidence_delta, "evidence_delta")
        response_code = _require_int(self.response_code, "response_code")
        if revision not in (0, 1) or response_code not in (0, 2):
            raise ConservationError("shadow supplement supports exactly revision 0 -> 1")
        if not -10 <= delta <= 10:
            raise ConservationError("shadow supplementary evidence delta must be bounded")
        if revision == 0:
            if (
                evidence
                or self.evidence_object_id is not None
                or delta
                or response_code
                or self.response_day is not None
                or self.new_evidence
            ):
                raise ConservationError("revision zero cannot contain supplementary evidence")
        else:
            if (
                len(evidence) != 1
                or self.evidence_object_id != self.identity.case_serial * 100 + 1
                or response_code != 2
                or not self.new_evidence
            ):
                raise ConservationError("revision one lost its evidence-object receipt")
            _require_int(self.response_day, "response_day", minimum=1)
            if not self.notice_day <= self.response_day <= self.deadline_day:  # type: ignore[operator]
                raise ConservationError("shadow evidence response escaped its open window")
        if self.disclosed != (self.route is PolicyRoute.A):
            raise ConservationError("only route A discloses the shadow band before final")
        if self.route is PolicyRoute.B and revision:
            raise ConservationError("undisclosed route B cannot contain a response revision")
        if self.identity.state == "shadow_window_open":
            if self.final_band is not None or self.final_explanation is not None:
                raise ConservationError("open shadow window cannot contain a final result")
            if self.quota_committed or self.reward_issued:
                raise ConservationError("shadow grade cannot consume quota or reward")
            if self.final_drop or self.drop_explained:
                raise ConservationError("open shadow window cannot contain drop analysis")
        else:
            if not isinstance(self.final_band, RatingBand):
                raise ConservationError("finalized shadow case requires a final band")
            _require_identifier(self.final_explanation, "final_explanation")
            if not self.quota_committed or self.reward_issued:
                raise ConservationError(
                    "finalization commits one quota slot but does not issue reward early"
                )
            expected_drop = max(
                0, self.shadow_band.ck3_grade_code - self.final_band.ck3_grade_code
            )
            if self.final_drop != expected_drop:
                raise ConservationError("shadow final-drop magnitude is inconsistent")
            if self.drop_explained != (expected_drop > 0 and self.new_evidence):
                raise ConservationError("shadow drop explanation contradicts evidence revision")
        _require_int(self.feedback_debt_delta, "feedback_debt_delta")
        _require_int(self.appeal_weight_delta, "appeal_weight_delta")
        unexplained_drop = self.final_drop > 0 and not self.new_evidence
        expected_debt = int(unexplained_drop)
        expected_appeal = min(self.final_drop * 2, 6) if unexplained_drop else 0
        if (
            self.feedback_debt_delta != expected_debt
            or self.appeal_weight_delta != expected_appeal
        ):
            raise ConservationError("shadow feedback debt contradicts final drop evidence")
        object.__setattr__(self, "gap_ids", gaps)
        object.__setattr__(self, "accepted_evidence_ids", evidence)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_shadow_rating_case(
    ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    shadow_band: RatingBand,
    notice_day: int,
    deadline_day: int,
    gap_ids: Sequence[str],
    gap_magnitude: int,
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        ledger,
        mechanism_id=135,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    case = ShadowRatingCase(
        identity=identity.advanced("shadow_window_open"),
        route=route,
        shadow_object_id=identity.case_serial * 100 + 35,
        shadow_band=shadow_band,
        notice_day=notice_day,
        deadline_day=deadline_day,
        gap_ids=tuple(gap_ids),
        gap_magnitude=gap_magnitude,
        disclosed=route is PolicyRoute.A,
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        ledger,
        mechanism_id=135,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def submit_shadow_evidence(
    case: ShadowRatingCase,
    *,
    evidence_id: str,
    submitted_day: int,
    evidence_delta: int,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> ShadowRatingCase:
    if not isinstance(case, ShadowRatingCase):
        raise InvalidInputError("case must be ShadowRatingCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    evidence = _require_identifier(evidence_id, "evidence_id")
    day = _require_int(submitted_day, "submitted_day", minimum=1)
    if case.route is not PolicyRoute.A or not case.disclosed:
        raise IllegalStateError("an undisclosed shadow grade cannot solicit supplement")
    if day > case.deadline_day:
        raise StaleOperationError("post-deadline evidence belongs to a later cycle")
    if evidence in case.accepted_evidence_ids:
        raise DuplicateInputError("shadow evidence was already attached")
    if case.evidence_revision != 0:
        raise DuplicateOperationError("shadow supplement already consumed its one revision")
    delta = _require_signed_int(evidence_delta, "evidence_delta")
    if not -10 <= delta <= 10:
        raise ConservationError("shadow supplementary evidence delta must be within -10..10")
    return replace(
        case,
        accepted_evidence_ids=case.accepted_evidence_ids + (evidence,),
        evidence_object_id=case.identity.case_serial * 100 + 1,
        evidence_revision=1,
        evidence_delta=delta,
        response_code=2,
        response_day=day,
        new_evidence=True,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


def finalize_shadow_rating(
    case: ShadowRatingCase,
    *,
    final_band: RatingBand,
    explanation: str,
    current_day: int,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> ShadowRatingCase:
    if not isinstance(case, ShadowRatingCase):
        raise InvalidInputError("case must be ShadowRatingCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    if case.identity.state != "shadow_window_open":
        raise IllegalStateError("shadow case is not open")
    if not isinstance(final_band, RatingBand):
        raise InvalidInputError("final_band must be RatingBand")
    reason = _require_identifier(explanation, "explanation")
    day = _require_int(current_day, "current_day", minimum=1)
    if day < case.deadline_day:
        raise IllegalStateError("shadow evidence window is still open")
    drop = max(0, case.shadow_band.ck3_grade_code - final_band.ck3_grade_code)
    unexplained_drop = drop > 0 and not case.new_evidence
    return replace(
        case,
        identity=case.identity.advanced("shadow_finalized"),
        final_band=final_band,
        final_explanation=reason,
        final_drop=drop,
        drop_explained=drop > 0 and case.new_evidence,
        quota_committed=True,
        reward_issued=False,
        feedback_debt_delta=int(unexplained_drop),
        appeal_weight_delta=min(drop * 2, 6) if unexplained_drop else 0,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class BandAssignment:
    subject_id: str
    band: RatingBand

    def __post_init__(self) -> None:
        _require_identifier(self.subject_id, "subject_id")
        if not isinstance(self.band, RatingBand):
            raise InvalidInputError("band assignment has an invalid band")


class GrayLeaverQuotaSource(str, Enum):
    NATURAL_BOTTOM = "natural_bottom"
    SWAPPED_BOTTOM = "swapped_bottom"
    NO_EXISTING_BOTTOM = "no_existing_bottom"


@dataclass(frozen=True, slots=True)
class GrayLeaverResult:
    operation_id: str
    leaver_id: str
    source: GrayLeaverQuotaSource
    before: tuple[BandAssignment, ...]
    after: tuple[BandAssignment, ...]
    carrier_id: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id")
        _require_identifier(self.leaver_id, "leaver_id")
        if not isinstance(self.source, GrayLeaverQuotaSource):
            raise InvalidInputError("gray leaver source is invalid")
        before = tuple(self.before)
        after = tuple(self.after)
        if any(not isinstance(item, BandAssignment) for item in before + after):
            raise InvalidInputError("gray leaver assignments are invalid")
        before_ids = tuple(item.subject_id for item in before)
        after_ids = tuple(item.subject_id for item in after)
        if len(set(before_ids)) != len(before_ids) or set(before_ids) != set(after_ids):
            raise ConservationError("gray leaver operation changed cohort identity")
        if self.leaver_id not in set(before_ids):
            raise InvalidInputError("gray leaver is not in the frozen cohort")
        before_counts = {band: sum(item.band is band for item in before) for band in BAND_ORDER}
        after_counts = {band: sum(item.band is band for item in after) for band in BAND_ORDER}
        if before_counts != after_counts:
            raise ConservationError("gray leaver operation changed quota counts")
        before_by_id = {item.subject_id: item.band for item in before}
        after_by_id = {item.subject_id: item.band for item in after}
        if self.source is GrayLeaverQuotaSource.NO_EXISTING_BOTTOM:
            if before != after or self.carrier_id is not None:
                raise ConservationError("blocked gray leaver operation must be a no-op")
            if before_counts[RatingBand.BOTTOM] != 0:
                raise ConservationError("blocked gray leaver ignored an existing bottom slot")
        else:
            if after_by_id[self.leaver_id] is not RatingBand.BOTTOM:
                raise ConservationError("gray leaver did not occupy the existing bottom slot")
            if self.source is GrayLeaverQuotaSource.NATURAL_BOTTOM:
                if before != after or self.carrier_id is not None:
                    raise ConservationError("natural bottom must not manufacture a swap")
            else:
                if self.carrier_id is None:
                    raise ConservationError("swapped gray leaver requires the old C carrier")
                _require_identifier(self.carrier_id, "carrier_id")
                if self.carrier_id == self.leaver_id:
                    raise ConservationError("gray leaver cannot be its own carrier")
                if before_by_id[self.leaver_id] is RatingBand.BOTTOM:
                    raise ConservationError("a natural bottom cannot claim a swap")
                if before_by_id.get(self.carrier_id) is not RatingBand.BOTTOM:
                    raise ConservationError("gray leaver carrier was not the existing bottom")
                if after_by_id.get(self.carrier_id) is not before_by_id[self.leaver_id]:
                    raise ConservationError("gray leaver swap did not preserve the honest grade")
                changed = {
                    subject_id
                    for subject_id in before_ids
                    if before_by_id[subject_id] is not after_by_id[subject_id]
                }
                if changed != {self.leaver_id, self.carrier_id}:
                    raise ConservationError("gray leaver swap was not atomic")
        object.__setattr__(self, "before", before)
        object.__setattr__(self, "after", after)


def charge_gray_leaver_to_existing_bottom(
    assignments: tuple[BandAssignment, ...],
    leaver_id: str,
    *,
    operation_id: str,
    prior: GrayLeaverResult | None = None,
) -> GrayLeaverResult:
    """Atomically swap one frozen leaver into an existing C, or block.

    ``prior`` models the persisted CK3 receipt: exact replay returns the same
    result, while a changed roster/operation cannot be smuggled through it.
    """

    _require_identifier(leaver_id, "leaver_id")
    _require_identifier(operation_id, "operation_id")
    frozen = tuple(assignments)
    if any(not isinstance(item, BandAssignment) for item in frozen):
        raise InvalidInputError("assignments must contain BandAssignment values")
    ids = tuple(item.subject_id for item in frozen)
    if len(set(ids)) != len(ids):
        raise DuplicateInputError("a subject appears twice in the quota book")
    if leaver_id not in set(ids):
        raise InvalidInputError("gray leaver is not in the frozen quota book")
    if prior is not None:
        if not isinstance(prior, GrayLeaverResult):
            raise InvalidInputError("prior gray leaver receipt is invalid")
        if (
            prior.operation_id != operation_id
            or prior.leaver_id != leaver_id
            or prior.after != frozen
        ):
            raise StaleOperationError("gray leaver replay does not match its receipt")
        return prior

    by_id = {item.subject_id: item.band for item in frozen}
    bottom_ids = sorted(
        item.subject_id for item in frozen if item.band is RatingBand.BOTTOM
    )
    if not bottom_ids:
        return GrayLeaverResult(
            operation_id=operation_id,
            leaver_id=leaver_id,
            source=GrayLeaverQuotaSource.NO_EXISTING_BOTTOM,
            before=frozen,
            after=frozen,
        )
    if by_id[leaver_id] is RatingBand.BOTTOM:
        return GrayLeaverResult(
            operation_id=operation_id,
            leaver_id=leaver_id,
            source=GrayLeaverQuotaSource.NATURAL_BOTTOM,
            before=frozen,
            after=frozen,
        )

    carrier_id = bottom_ids[0]
    leaver_band = by_id[leaver_id]
    after = tuple(
        BandAssignment(
            item.subject_id,
            (
                RatingBand.BOTTOM
                if item.subject_id == leaver_id
                else leaver_band
                if item.subject_id == carrier_id
                else item.band
            ),
        )
        for item in frozen
    )
    return GrayLeaverResult(
        operation_id=operation_id,
        leaver_id=leaver_id,
        source=GrayLeaverQuotaSource.SWAPPED_BOTTOM,
        before=frozen,
        after=after,
        carrier_id=carrier_id,
    )


@dataclass(frozen=True, slots=True)
class PrecalibrationDiff:
    subject_id: str
    suggested_band: RatingBand
    formal_band: RatingBand

    def __post_init__(self) -> None:
        _require_identifier(self.subject_id, "subject_id")
        if not isinstance(self.suggested_band, RatingBand) or not isinstance(
            self.formal_band, RatingBand
        ):
            raise InvalidInputError("precalibration diff has an invalid band")


@dataclass(frozen=True, slots=True)
class PrecalibrationMeeting:
    identity: CaseIdentity
    route: PolicyRoute
    manager_ids: tuple[str, ...]
    cohort_ids: tuple[str, ...]
    boundary_case_ids: tuple[str, ...]
    standard_snapshot: str
    minutes: int
    suggested_assignments: tuple[BandAssignment, ...]
    black_box_risk: bool
    formal_assignments: tuple[BandAssignment, ...] = ()
    diffs: tuple[PrecalibrationDiff, ...] = ()
    consumed_minutes: int = 0
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "precalibration_open",
            "precalibration_consumed",
        ):
            raise InvalidInputError("precalibration has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("precalibration business case only supports A/B")
        managers = tuple(self.manager_ids)
        cohort = tuple(self.cohort_ids)
        boundary = tuple(self.boundary_case_ids)
        suggestions = tuple(self.suggested_assignments)
        formal = tuple(self.formal_assignments)
        diffs = tuple(self.diffs)
        for values, field in (
            (managers, "manager_id"),
            (cohort, "cohort_id"),
            (boundary, "boundary_case_id"),
        ):
            for value in values:
                _require_identifier(value, field)
            if len(set(values)) != len(values):
                raise DuplicateInputError(f"{field} values must be unique")
        if not 3 <= len(managers) <= 4:
            raise ConservationError("a real precalibration huddle needs 3-4 managers")
        if not cohort or not boundary or not set(boundary).issubset(set(cohort)):
            raise ConservationError("precalibration boundary cases must be in the cohort")
        _require_identifier(self.standard_snapshot, "standard_snapshot")
        _require_int(self.minutes, "minutes", minimum=1)
        if any(not isinstance(item, BandAssignment) for item in suggestions + formal):
            raise InvalidInputError("precalibration assignments are invalid")
        suggested_ids = tuple(item.subject_id for item in suggestions)
        if len(set(suggested_ids)) != len(suggested_ids):
            raise DuplicateInputError("precalibration suggested one subject twice")
        expected_suggestions = set(boundary) if self.route is PolicyRoute.A else set(cohort)
        if set(suggested_ids) != expected_suggestions:
            raise ConservationError(
                "route A may suggest only boundaries; route B preallocates the full cohort"
            )
        if self.black_box_risk != (self.route is PolicyRoute.B):
            raise ConservationError("only route B carries preallocation black-box risk")
        if self.identity.state == "precalibration_open":
            if formal or diffs or self.consumed_minutes:
                raise ConservationError("open precalibration cannot contain formal outcomes")
        else:
            if {item.subject_id for item in formal} != set(cohort):
                raise ConservationError("formal calibration must cover the whole cohort")
            if self.consumed_minutes != self.minutes:
                raise ConservationError("precalibration attention minutes did not conserve")
        if any(not isinstance(item, PrecalibrationDiff) for item in diffs):
            raise InvalidInputError("precalibration diffs are invalid")
        object.__setattr__(self, "manager_ids", managers)
        object.__setattr__(self, "cohort_ids", cohort)
        object.__setattr__(self, "boundary_case_ids", boundary)
        object.__setattr__(self, "suggested_assignments", suggestions)
        object.__setattr__(self, "formal_assignments", formal)
        object.__setattr__(self, "diffs", diffs)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_precalibration_meeting(
    ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    manager_ids: Sequence[str],
    cohort_ids: Sequence[str],
    boundary_case_ids: Sequence[str],
    standard_snapshot: str,
    minutes: int,
    suggested_assignments: Sequence[BandAssignment],
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        ledger,
        mechanism_id=136,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    meeting = PrecalibrationMeeting(
        identity=identity.advanced("precalibration_open"),
        route=route,
        manager_ids=tuple(manager_ids),
        cohort_ids=tuple(cohort_ids),
        boundary_case_ids=tuple(boundary_case_ids),
        standard_snapshot=standard_snapshot,
        minutes=minutes,
        suggested_assignments=tuple(suggested_assignments),
        black_box_risk=route is PolicyRoute.B,
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        ledger,
        mechanism_id=136,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=meeting,
    )


def consume_precalibration_meeting(
    meeting: PrecalibrationMeeting,
    *,
    formal_assignments: Sequence[BandAssignment],
    operation_id: str,
    expected_identity: CaseIdentity,
) -> PrecalibrationMeeting:
    if not isinstance(meeting, PrecalibrationMeeting):
        raise InvalidInputError("meeting must be PrecalibrationMeeting")
    op_id = _case_preflight(
        meeting.identity, expected_identity, meeting.applied_operations, operation_id
    )
    formal = tuple(formal_assignments)
    if len({item.subject_id for item in formal}) != len(formal):
        raise DuplicateInputError("formal calibration assigned one subject twice")
    if {item.subject_id for item in formal} != set(meeting.cohort_ids):
        raise ConservationError("formal calibration must cover the frozen cohort")
    baseline = {item.subject_id: item.band for item in meeting.suggested_assignments}
    diffs = tuple(
        PrecalibrationDiff(item.subject_id, baseline[item.subject_id], item.band)
        for item in formal
        if item.subject_id in baseline and baseline[item.subject_id] is not item.band
    )
    return replace(
        meeting,
        identity=meeting.identity.advanced("precalibration_consumed"),
        formal_assignments=formal,
        diffs=diffs,
        consumed_minutes=meeting.minutes,
        applied_operations=meeting.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class AgendaResolution:
    subject_id: str
    band: RatingBand
    attention_cost: int
    position: int
    late_segment_pressure: bool

    def __post_init__(self) -> None:
        _require_identifier(self.subject_id, "subject_id")
        if not isinstance(self.band, RatingBand):
            raise InvalidInputError("agenda resolution has an invalid band")
        _require_int(self.attention_cost, "attention_cost", minimum=1)
        _require_int(self.position, "position", minimum=1)
        if not isinstance(self.late_segment_pressure, bool):
            raise InvalidInputError("late_segment_pressure must be bool")


@dataclass(frozen=True, slots=True)
class AgendaCalibrationCase:
    identity: CaseIdentity
    route: PolicyRoute
    plan: AgendaPlan
    attention: AttentionLedger
    initial_quota: QuotaCounts
    remaining_quota: QuotaCounts
    resolutions: tuple[AgendaResolution, ...] = ()
    chair_bias_visible: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "agenda_frozen",
            "agenda_consumed",
        ):
            raise InvalidInputError("agenda calibration has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("agenda calibration only supports route A/B")
        if not isinstance(self.plan, AgendaPlan) or not isinstance(
            self.attention, AttentionLedger
        ):
            raise InvalidInputError("agenda calibration has invalid plan/attention")
        if not isinstance(self.initial_quota, QuotaCounts) or not isinstance(
            self.remaining_quota, QuotaCounts
        ):
            raise InvalidInputError("agenda calibration has invalid quota")
        resolutions = tuple(self.resolutions)
        if any(not isinstance(item, AgendaResolution) for item in resolutions):
            raise InvalidInputError("agenda resolutions are invalid")
        if tuple(item.subject_id for item in resolutions) != self.plan.subject_ids[
            : len(resolutions)
        ]:
            raise ConservationError("agenda resolutions escaped the frozen order")
        if self.attention.cursor != len(resolutions):
            raise ConservationError("attention cursor and agenda resolutions diverged")
        if self.remaining_quota.total != len(self.plan.subject_ids) - len(resolutions):
            raise ConservationError("remaining quota does not match unresolved subjects")
        used = QuotaCounts(
            top=sum(item.band is RatingBand.TOP for item in resolutions),
            middle=sum(item.band is RatingBand.MIDDLE for item in resolutions),
            bottom=sum(item.band is RatingBand.BOTTOM for item in resolutions),
        )
        for band in BAND_ORDER:
            if used[band] + self.remaining_quota[band] != self.initial_quota[band]:
                raise ConservationError("agenda band quota did not conserve")
        if self.chair_bias_visible != (self.route is PolicyRoute.B):
            raise ConservationError("only route B exposes chair anchoring risk")
        if self.identity.state == "agenda_consumed" and self.remaining_quota.total != 0:
            raise ConservationError("consumed agenda still owns quota")
        object.__setattr__(self, "resolutions", resolutions)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_agenda_calibration_case(
    ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    entries: Sequence[AgendaEntry],
    authoritative_cohort_ids: Sequence[str],
    quota: QuotaCounts,
    attention_minutes: int,
    seed: str,
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        ledger,
        mechanism_id=137,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    mode = AgendaMode.STABLE_RANDOM if route is PolicyRoute.A else AgendaMode.STRATEGIC_FIRST
    plan = build_agenda(
        entries,
        mode,
        authoritative_cohort_ids=authoritative_cohort_ids,
        seed=seed,
    )
    if quota.total != len(plan.subject_ids):
        raise ConservationError("agenda quota must equal the frozen cohort size")
    case = AgendaCalibrationCase(
        identity=identity.advanced("agenda_frozen"),
        route=route,
        plan=plan,
        attention=AttentionLedger(
            round_id=f"agenda-{identity.case_serial}",
            review_serial=identity.cycle,
            agenda=plan.subject_ids,
            total=attention_minutes,
        ),
        initial_quota=quota,
        remaining_quota=quota,
        chair_bias_visible=route is PolicyRoute.B,
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        ledger,
        mechanism_id=137,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def consume_agenda_subject(
    case: AgendaCalibrationCase,
    *,
    subject_id: str,
    band: RatingBand,
    attention_cost: int,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> AgendaCalibrationCase:
    if not isinstance(case, AgendaCalibrationCase):
        raise InvalidInputError("case must be AgendaCalibrationCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    if not isinstance(band, RatingBand):
        raise InvalidInputError("band must be RatingBand")
    if case.remaining_quota[band] < 1:
        raise InsufficientSlotError("agenda resolution exhausted this band")
    updated_attention = spend_attention(
        case.attention,
        subject_id=subject_id,
        cost=attention_cost,
        operation_id=op_id,
        expected_review_serial=case.identity.cycle,
    )
    position = len(case.resolutions) + 1
    resolution = AgendaResolution(
        subject_id=subject_id,
        band=band,
        attention_cost=attention_cost,
        position=position,
        late_segment_pressure=(
            case.route is PolicyRoute.B
            and position > (len(case.plan.subject_ids) + 1) // 2
        ),
    )
    remaining = case.remaining_quota.with_delta(band, -1)
    finished = remaining.total == 0
    return replace(
        case,
        identity=case.identity.advanced(
            "agenda_consumed" if finished else "agenda_frozen"
        ),
        attention=updated_attention,
        remaining_quota=remaining,
        resolutions=case.resolutions + (resolution,),
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class QuotaRoundingCase:
    identity: CaseIdentity
    route: PolicyRoute
    computation: QuotaComputation
    team_ids: tuple[str, ...]
    remainder_team_id: str
    rotation_cycle: int
    method: str
    chair_id: str | None = None
    black_box_risk: bool = False
    published_book: QuotaBook | None = None
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "quota_rounded",
            "quota_published",
        ):
            raise InvalidInputError("quota rounding has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B) or not isinstance(
            self.computation, QuotaComputation
        ):
            raise InvalidInputError("quota rounding has invalid route/computation")
        teams = tuple(self.team_ids)
        for team_id in teams:
            _require_identifier(team_id, "team_id")
        if not teams or len(set(teams)) != len(teams):
            raise DuplicateInputError("quota rounding team ids must be nonempty and unique")
        if self.remainder_team_id not in teams:
            raise ConservationError("remainder beneficiary must be a frozen team")
        _require_int(self.rotation_cycle, "rotation_cycle", minimum=1)
        _require_identifier(self.method, "method")
        if self.route is PolicyRoute.A:
            if self.method != "largest_remainder_rotation" or self.chair_id is not None:
                raise ConservationError("route A must freeze non-discretionary rounding")
        else:
            _require_identifier(self.chair_id, "chair_id")
            if self.method != "chair_discretion" or not self.black_box_risk:
                raise ConservationError("route B must disclose chair discretion risk")
        if self.black_box_risk != (self.route is PolicyRoute.B):
            raise ConservationError("quota rounding risk flag contradicts route")
        if self.identity.state == "quota_rounded" and self.published_book is not None:
            raise ConservationError("unpublished rounding cannot contain a quota book")
        if self.identity.state == "quota_published":
            if not isinstance(self.published_book, QuotaBook):
                raise ConservationError("published rounding requires a quota book")
            if self.published_book.counts != self.computation.effective_counts:
                raise ConservationError("published quota differs from rounded counts")
        object.__setattr__(self, "team_ids", teams)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_quota_rounding_case(
    ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    cohort_size: int,
    team_ids: Sequence[str],
    rotation_cycle: int,
    operation_id: str,
    chair_id: str | None = None,
    discretionary_team_id: str | None = None,
) -> PolicyOpenResult:
    declined = _route_c_result(
        ledger,
        mechanism_id=138,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    teams = tuple(team_ids)
    cycle = _require_int(rotation_cycle, "rotation_cycle", minimum=1)
    if route is PolicyRoute.A:
        beneficiary = teams[(cycle - 1) % len(teams)] if teams else ""
        method = "largest_remainder_rotation"
        chair = None
    else:
        beneficiary = _require_identifier(
            discretionary_team_id, "discretionary_team_id"
        )
        method = "chair_discretion"
        chair = _require_identifier(chair_id, "chair_id")
    case = QuotaRoundingCase(
        identity=identity.advanced("quota_rounded"),
        route=route,
        computation=compute_quota(cohort_size),
        team_ids=teams,
        remainder_team_id=beneficiary,
        rotation_cycle=cycle,
        method=method,
        chair_id=chair,
        black_box_risk=route is PolicyRoute.B,
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        ledger,
        mechanism_id=138,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def publish_rounded_quota(
    case: QuotaRoundingCase,
    *,
    team_id: str,
    common_superior_id: str,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> QuotaRoundingCase:
    if not isinstance(case, QuotaRoundingCase):
        raise InvalidInputError("case must be QuotaRoundingCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    book = QuotaBook(
        team_id=team_id,
        common_superior_id=common_superior_id,
        cycle=case.identity.cycle,
        counts=case.computation.effective_counts,
    )
    return replace(
        case,
        identity=case.identity.advanced("quota_published"),
        published_book=book,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class EvidenceSegment:
    team_id: str
    manager_id: str
    start_day: int
    end_day: int
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.team_id, "team_id")
        _require_identifier(self.manager_id, "manager_id")
        _require_int(self.start_day, "start_day", minimum=1)
        _require_int(self.end_day, "end_day", minimum=1)
        if self.start_day > self.end_day:
            raise ConservationError("evidence segment ends before it starts")
        evidence = tuple(self.evidence_ids)
        for evidence_id in evidence:
            _require_identifier(evidence_id, "evidence_id")
        if not evidence or len(set(evidence)) != len(evidence):
            raise DuplicateInputError("evidence segment ids must be nonempty and unique")
        object.__setattr__(self, "evidence_ids", evidence)


@dataclass(frozen=True, slots=True)
class ReorganizationAllocationReceipt:
    identity: CaseIdentity
    quota_owner_team_id: str
    occupied_slots: int
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity):
            raise InvalidInputError("reorganization receipt requires a CaseIdentity")
        _require_identifier(self.quota_owner_team_id, "quota_owner_team_id")
        if self.occupied_slots != 1:
            raise ConservationError("one reorganized subject must occupy exactly one slot")
        evidence = tuple(self.evidence_ids)
        for evidence_id in evidence:
            _require_identifier(evidence_id, "evidence_id")
        if len(set(evidence)) != len(evidence):
            raise ConservationError("reorganization evidence was duplicated or deleted")
        object.__setattr__(self, "evidence_ids", evidence)


@dataclass(frozen=True, slots=True)
class ReorganizationOwnershipCase:
    identity: CaseIdentity
    route: PolicyRoute
    old_manager_id: str
    new_manager_id: str
    old_team_id: str
    new_team_id: str
    old_service_days: int
    new_service_days: int
    ownership_freeze_day: int
    quota_owner_team_id: str
    evidence_segments: tuple[EvidenceSegment, ...]
    allocation_receipt: ReorganizationAllocationReceipt | None = None
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "reorg_frozen",
            "reorg_allocated",
        ):
            raise InvalidInputError("reorganization has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("reorganization business case only supports A/B")
        for value, field in (
            (self.old_manager_id, "old_manager_id"),
            (self.new_manager_id, "new_manager_id"),
            (self.old_team_id, "old_team_id"),
            (self.new_team_id, "new_team_id"),
            (self.quota_owner_team_id, "quota_owner_team_id"),
        ):
            _require_identifier(value, field)
        if self.old_manager_id == self.new_manager_id or self.old_team_id == self.new_team_id:
            raise ConservationError("reorganization needs distinct old/new owners")
        _require_int(self.old_service_days, "old_service_days")
        _require_int(self.new_service_days, "new_service_days")
        _require_int(self.ownership_freeze_day, "ownership_freeze_day", minimum=1)
        segments = tuple(self.evidence_segments)
        if any(not isinstance(item, EvidenceSegment) for item in segments):
            raise InvalidInputError("reorganization evidence segments are invalid")
        if {item.team_id for item in segments} != {self.old_team_id, self.new_team_id}:
            raise ConservationError("old and new team evidence must coexist")
        all_evidence = tuple(
            evidence_id for segment in segments for evidence_id in segment.evidence_ids
        )
        if len(set(all_evidence)) != len(all_evidence):
            raise ConservationError("one evidence item cannot appear in two segments")
        expected_owner = (
            self.old_team_id
            if self.route is PolicyRoute.A
            and self.old_service_days >= self.new_service_days
            else self.new_team_id
        )
        if self.quota_owner_team_id != expected_owner:
            raise ConservationError("quota owner contradicts the frozen route rule")
        if self.identity.state == "reorg_frozen" and self.allocation_receipt is not None:
            raise ConservationError("unallocated reorganization has a receipt")
        if self.identity.state == "reorg_allocated":
            if not isinstance(self.allocation_receipt, ReorganizationAllocationReceipt):
                raise ConservationError("allocated reorganization requires a receipt")
            if self.allocation_receipt.quota_owner_team_id != self.quota_owner_team_id:
                raise ConservationError("allocation receipt changed frozen quota owner")
            if set(self.allocation_receipt.evidence_ids) != set(all_evidence):
                raise ConservationError("allocation receipt did not preserve all evidence")
        object.__setattr__(self, "evidence_segments", segments)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_reorganization_ownership_case(
    ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    old_manager_id: str,
    new_manager_id: str,
    old_team_id: str,
    new_team_id: str,
    old_service_days: int,
    new_service_days: int,
    ownership_freeze_day: int,
    evidence_segments: Sequence[EvidenceSegment],
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        ledger,
        mechanism_id=140,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    owner = (
        old_team_id
        if route is PolicyRoute.A and old_service_days >= new_service_days
        else new_team_id
    )
    case = ReorganizationOwnershipCase(
        identity=identity.advanced("reorg_frozen"),
        route=route,
        old_manager_id=old_manager_id,
        new_manager_id=new_manager_id,
        old_team_id=old_team_id,
        new_team_id=new_team_id,
        old_service_days=old_service_days,
        new_service_days=new_service_days,
        ownership_freeze_day=ownership_freeze_day,
        quota_owner_team_id=owner,
        evidence_segments=tuple(evidence_segments),
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        ledger,
        mechanism_id=140,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def allocate_reorganized_subject(
    case: ReorganizationOwnershipCase,
    *,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> ReorganizationOwnershipCase:
    if not isinstance(case, ReorganizationOwnershipCase):
        raise InvalidInputError("case must be ReorganizationOwnershipCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    evidence = tuple(
        evidence_id
        for segment in case.evidence_segments
        for evidence_id in segment.evidence_ids
    )
    receipt = ReorganizationAllocationReceipt(
        identity=case.identity,
        quota_owner_team_id=case.quota_owner_team_id,
        occupied_slots=1,
        evidence_ids=evidence,
    )
    return replace(
        case,
        identity=case.identity.advanced("reorg_allocated"),
        allocation_receipt=receipt,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class ExecutiveMustReviewCase:
    identity: CaseIdentity
    route: PolicyRoute
    executive_id: str
    direct_manager_id: str
    reason: str
    intervention_kind: str
    attention_quota: int
    attention_consumed: int = 0
    direct_manager_band: RatingBand | None = None
    final_band: RatingBand | None = None
    judgment_credit_delta: int = 0
    judgment_result: str | None = None
    override_blocked: bool = False
    swap_peer_id: str | None = None
    subject_band_before: RatingBand | None = None
    subject_band_after: RatingBand | None = None
    peer_band_before: RatingBand | None = None
    peer_band_after: RatingBand | None = None
    band_counts_before: QuotaCounts | None = None
    band_counts_after: QuotaCounts | None = None
    book_version_before: int | None = None
    book_version_after: int | None = None
    conservation_valid: bool = False
    swap_executed: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "must_review_open",
            "must_review_resolved",
        ):
            raise InvalidInputError("must-review has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("must-review business case only supports A/B")
        _require_identifier(self.executive_id, "executive_id")
        _require_identifier(self.direct_manager_id, "direct_manager_id")
        _require_identifier(self.reason, "reason")
        _require_identifier(self.intervention_kind, "intervention_kind")
        if self.executive_id == self.direct_manager_id:
            raise ConservationError("executive and direct manager must be distinct")
        if self.identity.owner_id != self.direct_manager_id:
            raise ConservationError("must-review case must remain direct-manager-owned")
        if self.identity.subject_id == self.swap_peer_id:
            raise ConservationError("must-review subject cannot swap with itself")
        if self.attention_quota != 1:
            raise ConservationError("every must-review case consumes one review attention")
        _require_int(self.attention_consumed, "attention_consumed")
        _require_signed_int(self.judgment_credit_delta, "judgment_credit_delta")
        if self.identity.state == "must_review_open":
            if (
                self.attention_consumed
                or self.final_band is not None
                or self.judgment_result is not None
                or self.swap_executed
                or self.conservation_valid
                or any(
                    value is not None
                    for value in (
                        self.swap_peer_id,
                        self.subject_band_before,
                        self.subject_band_after,
                        self.peer_band_before,
                        self.peer_band_after,
                        self.band_counts_before,
                        self.band_counts_after,
                        self.book_version_before,
                        self.book_version_after,
                    )
                )
            ):
                raise ConservationError("open must-review cannot contain a resolution")
        else:
            if not isinstance(self.direct_manager_band, RatingBand) or not isinstance(
                self.final_band, RatingBand
            ):
                raise ConservationError("resolved must-review requires direct/final bands")
            if self.attention_consumed != self.attention_quota:
                raise ConservationError("must-review attention did not conserve")
            if self.judgment_result not in ("hit", "miss"):
                raise ConservationError("must-review publication needs hit/miss judgment")
            expected_credit = 1 if self.judgment_result == "hit" else -1
            if self.judgment_credit_delta != expected_credit:
                raise ConservationError("manager judgment credit contradicts publication")
            if self.override_blocked != (self.route is PolicyRoute.B):
                raise ConservationError("route B must record its blocked override")
            if self.route is PolicyRoute.A:
                if self.final_band is not self.direct_manager_band:
                    raise ConservationError("route A executive review cannot write a grade")
                if self.swap_executed or self.conservation_valid or any(
                    value is not None
                    for value in (
                        self.swap_peer_id,
                        self.subject_band_before,
                        self.subject_band_after,
                        self.peer_band_before,
                        self.peer_band_after,
                        self.band_counts_before,
                        self.band_counts_after,
                        self.book_version_before,
                        self.book_version_after,
                    )
                ):
                    raise ConservationError("route A cannot smuggle in a grade swap")
            else:
                _require_identifier(self.swap_peer_id, "swap_peer_id")
                if (
                    self.direct_manager_band is not RatingBand.MIDDLE
                    or self.subject_band_before is not RatingBand.MIDDLE
                    or self.subject_band_after is not RatingBand.TOP
                    or self.peer_band_before is not RatingBand.TOP
                    or self.peer_band_after is not RatingBand.MIDDLE
                    or self.final_band is not RatingBand.TOP
                ):
                    raise ConservationError(
                        "route B must perform the exact manager-owned 3.5/3.75 swap"
                    )
                if not isinstance(self.band_counts_before, QuotaCounts) or not isinstance(
                    self.band_counts_after, QuotaCounts
                ) or self.band_counts_before != self.band_counts_after:
                    raise ConservationError("must-review swap changed the band distribution")
                before_version = _require_int(
                    self.book_version_before, "book_version_before"
                )
                after_version = _require_int(self.book_version_after, "book_version_after")
                if after_version != before_version + 1:
                    raise ConservationError("must-review swap must advance its book once")
                if not self.swap_executed or not self.conservation_valid:
                    raise ConservationError("must-review swap lacks an atomic conservation receipt")
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


@dataclass(frozen=True, slots=True)
class ExecutiveReviewRegistry:
    cases: tuple[ExecutiveMustReviewCase, ...] = ()

    def __post_init__(self) -> None:
        cases = tuple(self.cases)
        if any(not isinstance(item, ExecutiveMustReviewCase) for item in cases):
            raise InvalidInputError("executive review registry has an invalid case")
        keys = tuple((item.executive_id, item.identity.cycle) for item in cases)
        if len(set(keys)) != len(keys):
            raise ConservationError("one executive may use must-review once per cycle")
        object.__setattr__(self, "cases", cases)


@dataclass(frozen=True, slots=True)
class ExecutiveReviewOpenResult:
    policy: PolicyOpenResult
    registry: ExecutiveReviewRegistry

    def __post_init__(self) -> None:
        if not isinstance(self.policy, PolicyOpenResult) or not isinstance(
            self.registry, ExecutiveReviewRegistry
        ):
            raise InvalidInputError("invalid executive review open result")
        if self.policy.business_object is None:
            if self.policy.receipt.route is not PolicyRoute.C:
                raise ConservationError("only C may omit an executive review case")
        elif self.policy.business_object not in self.registry.cases:
            raise ConservationError("executive review registry lost its new case")


def open_executive_must_review(
    policy_ledger: PolicyDecisionLedger,
    registry: ExecutiveReviewRegistry,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    executive_id: str,
    direct_manager_id: str,
    reason: str,
    intervention_kind: str,
    operation_id: str,
) -> ExecutiveReviewOpenResult:
    if not isinstance(registry, ExecutiveReviewRegistry):
        raise InvalidInputError("registry must be ExecutiveReviewRegistry")
    declined = _route_c_result(
        policy_ledger,
        mechanism_id=141,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return ExecutiveReviewOpenResult(declined, registry)
    executive = _require_identifier(executive_id, "executive_id")
    if any(
        item.executive_id == executive and item.identity.cycle == identity.cycle
        for item in registry.cases
    ):
        raise InsufficientSlotError("executive must-review allowance is already consumed")
    case = ExecutiveMustReviewCase(
        identity=identity.advanced("must_review_open"),
        route=route,
        executive_id=executive,
        direct_manager_id=direct_manager_id,
        reason=reason,
        intervention_kind=intervention_kind,
        attention_quota=1,
        applied_operations=frozenset({operation_id}),
    )
    policy = _record_policy_decision(
        policy_ledger,
        mechanism_id=141,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )
    return ExecutiveReviewOpenResult(policy, replace(registry, cases=registry.cases + (case,)))


def resolve_executive_must_review(
    case: ExecutiveMustReviewCase,
    *,
    direct_manager_band: RatingBand,
    intervention_supported: bool,
    operation_id: str,
    expected_identity: CaseIdentity,
    swap_peer_id: str | None = None,
    swap_peer_band: RatingBand | None = None,
    manager_band_counts: QuotaCounts | None = None,
    expected_book_version: int | None = None,
) -> ExecutiveMustReviewCase:
    if not isinstance(case, ExecutiveMustReviewCase):
        raise InvalidInputError("case must be ExecutiveMustReviewCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    if not isinstance(direct_manager_band, RatingBand) or not isinstance(
        intervention_supported, bool
    ):
        raise InvalidInputError("invalid must-review resolution")
    if case.route is PolicyRoute.A:
        if any(
            value is not None
            for value in (
                swap_peer_id,
                swap_peer_band,
                manager_band_counts,
                expected_book_version,
            )
        ):
            raise ConservationError("route A cannot accept a grade-swap payload")
        final_band = direct_manager_band
        peer = None
        subject_before = None
        subject_after = None
        peer_before = None
        peer_after = None
        counts_before = None
        counts_after = None
        version_before = None
        version_after = None
        conserved = False
        swapped = False
    else:
        peer = _require_identifier(swap_peer_id, "swap_peer_id")
        if peer == case.identity.subject_id:
            raise ConservationError("must-review subject cannot swap with itself")
        if direct_manager_band is not RatingBand.MIDDLE or swap_peer_band is not RatingBand.TOP:
            raise InsufficientSlotError(
                "manager-owned must-review swap needs one 3.5 subject and one 3.75 peer"
            )
        if not isinstance(manager_band_counts, QuotaCounts):
            raise InvalidInputError("manager_band_counts must be QuotaCounts")
        if manager_band_counts.middle < 1 or manager_band_counts.top < 1:
            raise InsufficientSlotError("must-review swap has no conserved top/middle pair")
        version_before = _require_int(expected_book_version, "expected_book_version")
        final_band = RatingBand.TOP
        subject_before = RatingBand.MIDDLE
        subject_after = RatingBand.TOP
        peer_before = RatingBand.TOP
        peer_after = RatingBand.MIDDLE
        counts_before = manager_band_counts
        counts_after = manager_band_counts
        version_after = version_before + 1
        conserved = True
        swapped = True
    return replace(
        case,
        identity=case.identity.advanced("must_review_resolved"),
        attention_consumed=case.attention_quota,
        direct_manager_band=direct_manager_band,
        final_band=final_band,
        judgment_credit_delta=1 if intervention_supported else -1,
        judgment_result="hit" if intervention_supported else "miss",
        override_blocked=case.route is PolicyRoute.B,
        swap_peer_id=peer,
        subject_band_before=subject_before,
        subject_band_after=subject_after,
        peer_band_before=peer_before,
        peer_band_after=peer_after,
        band_counts_before=counts_before,
        band_counts_after=counts_after,
        book_version_before=version_before,
        book_version_after=version_after,
        conservation_valid=conserved,
        swap_executed=swapped,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class PendingMilestoneCase:
    identity: CaseIdentity
    route: PolicyRoute
    hold_id: str
    milestone_id: str
    verifier_id: str
    deadline_cycle: int
    held_band: RatingBand
    fallback_band: RatingBand
    frozen_reward: Fraction
    quota_held: bool
    disclosed_fields: tuple[str, ...]
    deferred_evidence_cycle: int | None = None
    final_band: RatingBand | None = None
    reward_released: Fraction = Fraction(0)
    deferred_evidence_id: str | None = None
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "pending_milestone_open",
            "pending_milestone_resolved",
            "pending_evidence_deferred",
            "pending_evidence_consumed",
        ):
            raise InvalidInputError("pending milestone has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B):
            raise InvalidInputError("pending milestone business case only supports A/B")
        for value, field in (
            (self.hold_id, "hold_id"),
            (self.milestone_id, "milestone_id"),
            (self.verifier_id, "verifier_id"),
        ):
            _require_identifier(value, field)
        _require_int(self.deadline_cycle, "deadline_cycle", minimum=1)
        if not isinstance(self.held_band, RatingBand) or not isinstance(
            self.fallback_band, RatingBand
        ):
            raise InvalidInputError("pending milestone has invalid bands")
        if self.held_band is self.fallback_band:
            raise ConservationError("held and fallback bands must differ")
        frozen_reward = _as_fraction(self.frozen_reward, "frozen_reward")
        released = _as_fraction(self.reward_released, "reward_released")
        if frozen_reward < 0 or released < 0 or released > frozen_reward:
            raise ConservationError("pending reward escaped its frozen amount")
        disclosed = tuple(self.disclosed_fields)
        for field in disclosed:
            _require_identifier(field, "disclosed_field")
        if len(set(disclosed)) != len(disclosed):
            raise DuplicateInputError("pending disclosure contains a duplicate field")
        if self.route is PolicyRoute.A:
            if disclosed != ("pending_marker", "milestone_id", "deadline_cycle"):
                raise ConservationError(
                    "route A may partially disclose status/milestone/deadline only"
                )
            if self.identity.state == "pending_milestone_open" and not self.quota_held:
                raise ConservationError("route A must hold exactly one quota slot")
            if self.deferred_evidence_cycle is not None or self.deferred_evidence_id is not None:
                raise ConservationError("route A cannot masquerade as next-cycle evidence")
            if self.identity.state == "pending_milestone_resolved":
                if self.quota_held or not isinstance(self.final_band, RatingBand):
                    raise ConservationError("resolved pending slot must release its hold")
            elif self.final_band is not None or released:
                raise ConservationError("open pending slot cannot have final reward/band")
        else:
            if disclosed != ("current_final_unchanged", "next_cycle_evidence"):
                raise ConservationError("route B disclosure must describe next-cycle deferral")
            if self.quota_held or frozen_reward or released or self.final_band is not None:
                raise ConservationError("route B cannot hold quota/reward or rewrite this round")
            if self.deferred_evidence_cycle != self.identity.cycle + 1:
                raise ConservationError("route B evidence must target exactly the next cycle")
            if self.identity.state == "pending_evidence_deferred":
                if self.deferred_evidence_id is not None:
                    raise ConservationError("unconsumed deferred evidence already has an id")
            elif self.identity.state == "pending_evidence_consumed":
                _require_identifier(self.deferred_evidence_id, "deferred_evidence_id")
            else:
                raise ConservationError("route B has an impossible pending state")
        object.__setattr__(self, "frozen_reward", frozen_reward)
        object.__setattr__(self, "reward_released", released)
        object.__setattr__(self, "disclosed_fields", disclosed)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))

    @property
    def public_snapshot(self) -> Mapping[str, object]:
        """Return the explicit disclosure projection, never the private hold record.

        The case object deliberately retains the held band and frozen reward for
        settlement.  UI/query consumers must use this projection: route A may
        expose only the pending marker, milestone, and deadline while the case
        is unresolved, and route B exposes only its unchanged-final/deferred
        evidence notice.  In particular, neither route can accidentally project
        ``held_band`` or ``frozen_reward``.
        """

        values: dict[str, object] = {
            "pending_marker": self.identity.state == "pending_milestone_open",
            "milestone_id": self.milestone_id,
            "deadline_cycle": self.deadline_cycle,
            "current_final_unchanged": True,
            "next_cycle_evidence": self.deferred_evidence_cycle,
        }
        return MappingProxyType({field: values[field] for field in self.disclosed_fields})


@dataclass(frozen=True, slots=True)
class PendingMilestoneOpenResult:
    policy: PolicyOpenResult
    slot_ledger: PendingSlotLedger

    def __post_init__(self) -> None:
        if not isinstance(self.policy, PolicyOpenResult) or not isinstance(
            self.slot_ledger, PendingSlotLedger
        ):
            raise InvalidInputError("invalid pending milestone open result")
        case = self.policy.business_object
        if isinstance(case, PendingMilestoneCase) and case.route is PolicyRoute.A:
            if sum(item.hold_id == case.hold_id for item in self.slot_ledger.pending_slots) != 1:
                raise ConservationError("route A pending case lost its held quota slot")


@dataclass(frozen=True, slots=True)
class PendingMilestoneResolutionResult:
    case: PendingMilestoneCase
    slot_ledger: PendingSlotLedger

    def __post_init__(self) -> None:
        if not isinstance(self.case, PendingMilestoneCase) or not isinstance(
            self.slot_ledger, PendingSlotLedger
        ):
            raise InvalidInputError("invalid pending milestone resolution")
        if self.case.route is PolicyRoute.A:
            matching = tuple(
                item for item in self.slot_ledger.resolved if item.hold_id == self.case.hold_id
            )
            if len(matching) != 1 or matching[0].final_band is not self.case.final_band:
                raise ConservationError("pending case and quota ledger resolution diverged")


def open_pending_milestone_case(
    policy_ledger: PolicyDecisionLedger,
    slot_ledger: PendingSlotLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    hold_id: str,
    milestone_id: str,
    verifier_id: str,
    deadline_cycle: int,
    held_band: RatingBand,
    fallback_band: RatingBand,
    frozen_reward: Fraction,
    operation_id: str,
) -> PendingMilestoneOpenResult:
    if not isinstance(slot_ledger, PendingSlotLedger):
        raise InvalidInputError("slot_ledger must be PendingSlotLedger")
    declined = _route_c_result(
        policy_ledger,
        mechanism_id=142,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return PendingMilestoneOpenResult(declined, slot_ledger)
    if route is PolicyRoute.A:
        updated_slots = hold_pending_slot(
            slot_ledger,
            hold_id=hold_id,
            subject_id=identity.subject_id,
            band=held_band,
            fallback_band=fallback_band,
            milestone_id=milestone_id,
            verifier_id=verifier_id,
            deadline_cycle=deadline_cycle,
            frozen_reward=frozen_reward,
            operation_id=operation_id,
            expected_review_serial=identity.cycle,
        )
        case = PendingMilestoneCase(
            identity=identity.advanced("pending_milestone_open"),
            route=route,
            hold_id=hold_id,
            milestone_id=milestone_id,
            verifier_id=verifier_id,
            deadline_cycle=deadline_cycle,
            held_band=held_band,
            fallback_band=fallback_band,
            frozen_reward=frozen_reward,
            quota_held=True,
            disclosed_fields=("pending_marker", "milestone_id", "deadline_cycle"),
            applied_operations=frozenset({operation_id}),
        )
    else:
        updated_slots = slot_ledger
        case = PendingMilestoneCase(
            identity=identity.advanced("pending_evidence_deferred"),
            route=route,
            hold_id=hold_id,
            milestone_id=milestone_id,
            verifier_id=verifier_id,
            deadline_cycle=deadline_cycle,
            held_band=held_band,
            fallback_band=fallback_band,
            frozen_reward=Fraction(0),
            quota_held=False,
            disclosed_fields=("current_final_unchanged", "next_cycle_evidence"),
            deferred_evidence_cycle=identity.cycle + 1,
            applied_operations=frozenset({operation_id}),
        )
    policy = _record_policy_decision(
        policy_ledger,
        mechanism_id=142,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )
    return PendingMilestoneOpenResult(policy, updated_slots)


def resolve_pending_milestone_case(
    case: PendingMilestoneCase,
    slot_ledger: PendingSlotLedger,
    *,
    current_cycle: int,
    resolution: PendingResolution,
    operation_id: str,
    expected_identity: CaseIdentity,
    deferred_evidence_id: str | None = None,
) -> PendingMilestoneResolutionResult:
    if not isinstance(case, PendingMilestoneCase) or not isinstance(
        slot_ledger, PendingSlotLedger
    ):
        raise InvalidInputError("invalid pending milestone case/ledger")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    cycle = _require_int(current_cycle, "current_cycle", minimum=1)
    if case.route is PolicyRoute.A:
        updated_slots = resolve_pending_slot(
            slot_ledger,
            hold_id=case.hold_id,
            subject_id=case.identity.subject_id,
            verifier_id=case.verifier_id,
            current_cycle=cycle,
            resolution=resolution,
            operation_id=op_id,
            expected_review_serial=case.identity.cycle,
        )
        record = next(
            item for item in updated_slots.resolved if item.hold_id == case.hold_id
        )
        updated_case = replace(
            case,
            identity=case.identity.advanced("pending_milestone_resolved"),
            quota_held=False,
            final_band=record.final_band,
            reward_released=(
                case.frozen_reward
                if resolution is PendingResolution.SUCCESS
                else Fraction(0)
            ),
            applied_operations=case.applied_operations | frozenset({op_id}),
        )
    else:
        if cycle < case.deferred_evidence_cycle:  # type: ignore[operator]
            raise IllegalStateError("deferred evidence is not yet in its target cycle")
        evidence_id = _require_identifier(deferred_evidence_id, "deferred_evidence_id")
        updated_slots = slot_ledger
        updated_case = replace(
            case,
            identity=case.identity.advanced("pending_evidence_consumed"),
            deferred_evidence_id=evidence_id,
            applied_operations=case.applied_operations | frozenset({op_id}),
        )
    return PendingMilestoneResolutionResult(updated_case, updated_slots)


@dataclass(frozen=True, slots=True)
class PostCutoffCase:
    identity: CaseIdentity
    route: PolicyRoute
    evidence: LateEvidence
    target_cycle: int
    board: ClosedCalibrationRound
    deferred_evidence_id: str | None = None
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "post_cutoff_reopened",
            "post_cutoff_resealed",
            "post_cutoff_deferred",
            "post_cutoff_deferred_consumed",
        ):
            raise InvalidInputError("post-cutoff case has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B) or not isinstance(
            self.evidence, LateEvidence
        ) or not isinstance(self.board, ClosedCalibrationRound):
            raise InvalidInputError("invalid post-cutoff case")
        _require_int(self.target_cycle, "target_cycle", minimum=1)
        if self.route is PolicyRoute.A:
            if self.target_cycle != self.identity.cycle:
                raise ConservationError("route A reopens the current cycle")
            if self.identity.state == "post_cutoff_reopened" and self.board.phase is not ClosurePhase.REOPENED:
                raise ConservationError("route A case lost its reopened board")
            if self.identity.state == "post_cutoff_resealed" and self.board.phase is not ClosurePhase.RESEALED:
                raise ConservationError("route A case lost its resealed board")
            if self.deferred_evidence_id is not None:
                raise ConservationError("route A cannot claim deferred evidence")
        else:
            if self.target_cycle != self.identity.cycle + 1:
                raise ConservationError("route B must defer to exactly the next cycle")
            if self.board.reopen_count != 0:
                raise ConservationError("route B cannot reopen or rewrite the old board")
            if self.identity.state == "post_cutoff_deferred" and self.deferred_evidence_id is not None:
                raise ConservationError("unconsumed post-cutoff evidence already has an id")
            if self.identity.state == "post_cutoff_deferred_consumed":
                _require_identifier(self.deferred_evidence_id, "deferred_evidence_id")
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_post_cutoff_case(
    policy_ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    board: ClosedCalibrationRound,
    evidence: LateEvidence,
    reopen_policy: SymmetricReopenPolicy,
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        policy_ledger,
        mechanism_id=143,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    if route is PolicyRoute.A:
        updated_board = request_symmetric_reopen(
            board,
            evidence,
            reopen_policy,
            operation_id=operation_id,
            expected_review_serial=board.review_serial,
            expected_board_cycle_id=board.sealed_board_cycle_id,
            expected_board_hash=board.board_hash,
        )
        case = PostCutoffCase(
            identity=identity.advanced("post_cutoff_reopened"),
            route=route,
            evidence=evidence,
            target_cycle=identity.cycle,
            board=updated_board,
            applied_operations=frozenset({operation_id}),
        )
    else:
        case = PostCutoffCase(
            identity=identity.advanced("post_cutoff_deferred"),
            route=route,
            evidence=evidence,
            target_cycle=identity.cycle + 1,
            board=board,
            applied_operations=frozenset({operation_id}),
        )
    return _record_policy_decision(
        policy_ledger,
        mechanism_id=143,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def consume_post_cutoff_case(
    case: PostCutoffCase,
    *,
    operation_id: str,
    expected_identity: CaseIdentity,
    current_cycle: int,
    receipt: BoardRecalculationReceipt | None = None,
    deferred_evidence_id: str | None = None,
) -> PostCutoffCase:
    if not isinstance(case, PostCutoffCase):
        raise InvalidInputError("case must be PostCutoffCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    cycle = _require_int(current_cycle, "current_cycle", minimum=1)
    if case.route is PolicyRoute.A:
        if not isinstance(receipt, BoardRecalculationReceipt):
            raise InvalidInputError("route A post-cutoff consumer needs a receipt")
        board = reseal_reopened_round(
            case.board,
            receipt=receipt,
            operation_id=op_id,
            expected_review_serial=case.board.review_serial,
            expected_board_hash=case.board.board_hash,
        )
        return replace(
            case,
            identity=case.identity.advanced("post_cutoff_resealed"),
            board=board,
            applied_operations=case.applied_operations | frozenset({op_id}),
        )
    if cycle < case.target_cycle:
        raise IllegalStateError("post-cutoff evidence has not reached its next cycle")
    evidence_id = _require_identifier(deferred_evidence_id, "deferred_evidence_id")
    return replace(
        case,
        identity=case.identity.advanced("post_cutoff_deferred_consumed"),
        deferred_evidence_id=evidence_id,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class DissentRecord:
    identity: CaseIdentity
    manager_id: str
    subject_id: str
    reason: str
    timestamp: int
    advocated_band: RatingBand
    attention_consumed: int = 0
    original_band: RatingBand | None = None
    formal_band: RatingBand | None = None
    independent_reviewer_id: str | None = None
    review_attention_receipt_id: str | None = None
    validation_outcome: str | None = None
    credit_delta: int = 0
    procedural_risk: bool = False
    self_safe_evidence: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "dissent_open",
            "dissent_validated",
        ):
            raise InvalidInputError("dissent has an invalid identity state")
        _require_identifier(self.manager_id, "manager_id")
        _require_identifier(self.subject_id, "subject_id")
        _require_identifier(self.reason, "reason")
        _require_int(self.timestamp, "timestamp", minimum=1)
        if not isinstance(self.advocated_band, RatingBand):
            raise InvalidInputError("dissent has an invalid advocated band")
        _require_int(self.attention_consumed, "attention_consumed")
        _require_signed_int(self.credit_delta, "credit_delta")
        if self.identity.subject_id != self.subject_id:
            raise ConservationError("dissent subject escaped its five-field identity")
        if self.identity.state == "dissent_open":
            if (
                self.attention_consumed
                or self.validation_outcome is not None
                or self.independent_reviewer_id is not None
                or self.review_attention_receipt_id is not None
                or self.procedural_risk
                or self.self_safe_evidence
            ):
                raise ConservationError("open dissent cannot contain validation")
        else:
            if not isinstance(self.original_band, RatingBand) or not isinstance(
                self.formal_band, RatingBand
            ):
                raise ConservationError("validated dissent requires old/new bands")
            if self.attention_consumed != 1:
                raise ConservationError("dissent must consume one independent review attention")
            reviewer = _require_identifier(
                self.independent_reviewer_id, "independent_reviewer_id"
            )
            if reviewer in (self.manager_id, self.subject_id):
                raise ConservationError("dissent reviewer must be independent")
            _require_identifier(
                self.review_attention_receipt_id, "review_attention_receipt_id"
            )
            if self.validation_outcome not in ("aligned_overturn", "not_validated"):
                raise ConservationError("dissent validation outcome is invalid")
            expected_credit = 1 if self.validation_outcome == "aligned_overturn" else -1
            if self.credit_delta != expected_credit:
                raise ConservationError("dissent credit contradicts its validation")
            if self.procedural_risk != (self.validation_outcome == "not_validated"):
                raise ConservationError("dissent procedural risk contradicts review outcome")
            if not self.self_safe_evidence:
                raise ConservationError("reviewed dissent needs affected-self safe evidence")
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


@dataclass(frozen=True, slots=True)
class ConsensusRecord:
    identity: CaseIdentity
    manager_ids: tuple[str, ...]
    subject_id: str
    final_band: RatingBand
    sealed: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "consensus_open",
            "consensus_sealed",
        ):
            raise InvalidInputError("consensus has an invalid identity state")
        managers = tuple(self.manager_ids)
        for manager_id in managers:
            _require_identifier(manager_id, "manager_id")
        if not managers or len(set(managers)) != len(managers):
            raise DuplicateInputError("consensus manager ids must be nonempty and unique")
        _require_identifier(self.subject_id, "subject_id")
        if not isinstance(self.final_band, RatingBand):
            raise InvalidInputError("consensus has an invalid final band")
        if self.identity.subject_id != self.subject_id:
            raise ConservationError("consensus subject escaped its five-field identity")
        if self.sealed != (self.identity.state == "consensus_sealed"):
            raise ConservationError("consensus seal flag contradicts identity state")
        object.__setattr__(self, "manager_ids", managers)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


@dataclass(frozen=True, slots=True)
class DissentRegistry:
    dissent_records: tuple[DissentRecord, ...] = ()
    consensus_records: tuple[ConsensusRecord, ...] = ()

    def __post_init__(self) -> None:
        dissent = tuple(self.dissent_records)
        consensus = tuple(self.consensus_records)
        if any(not isinstance(item, DissentRecord) for item in dissent) or any(
            not isinstance(item, ConsensusRecord) for item in consensus
        ):
            raise InvalidInputError("dissent registry has an invalid record")
        votes = tuple((item.manager_id, item.identity.stable_key) for item in dissent)
        if len(set(votes)) != len(votes):
            raise ConservationError("one manager may dissent once per boundary case")
        object.__setattr__(self, "dissent_records", dissent)
        object.__setattr__(self, "consensus_records", consensus)


@dataclass(frozen=True, slots=True)
class DissentOpenResult:
    policy: PolicyOpenResult
    registry: DissentRegistry

    def __post_init__(self) -> None:
        if not isinstance(self.policy, PolicyOpenResult) or not isinstance(
            self.registry, DissentRegistry
        ):
            raise InvalidInputError("invalid dissent open result")
        obj = self.policy.business_object
        if isinstance(obj, DissentRecord) and obj not in self.registry.dissent_records:
            raise ConservationError("dissent registry lost the new dissent")
        if isinstance(obj, ConsensusRecord) and obj not in self.registry.consensus_records:
            raise ConservationError("dissent registry lost the consensus")


def open_dissent_case(
    policy_ledger: PolicyDecisionLedger,
    registry: DissentRegistry,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    manager_id: str,
    reason: str,
    timestamp: int,
    advocated_band: RatingBand,
    consensus_manager_ids: Sequence[str],
    consensus_band: RatingBand,
    operation_id: str,
) -> DissentOpenResult:
    if not isinstance(registry, DissentRegistry):
        raise InvalidInputError("registry must be DissentRegistry")
    declined = _route_c_result(
        policy_ledger,
        mechanism_id=144,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return DissentOpenResult(declined, registry)
    if route is PolicyRoute.A:
        manager = _require_identifier(manager_id, "manager_id")
        if any(
            item.manager_id == manager and item.identity.stable_key == identity.stable_key
            for item in registry.dissent_records
        ):
            raise DuplicateOperationError("manager already dissented on this boundary case")
        obj: object = DissentRecord(
            identity=identity.advanced("dissent_open"),
            manager_id=manager,
            subject_id=identity.subject_id,
            reason=reason,
            timestamp=timestamp,
            advocated_band=advocated_band,
            applied_operations=frozenset({operation_id}),
        )
        updated_registry = replace(
            registry, dissent_records=registry.dissent_records + (obj,)
        )
    else:
        obj = ConsensusRecord(
            identity=identity.advanced("consensus_open"),
            manager_ids=tuple(consensus_manager_ids),
            subject_id=identity.subject_id,
            final_band=consensus_band,
            applied_operations=frozenset({operation_id}),
        )
        updated_registry = replace(
            registry, consensus_records=registry.consensus_records + (obj,)
        )
    policy = _record_policy_decision(
        policy_ledger,
        mechanism_id=144,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=obj,
    )
    return DissentOpenResult(policy, updated_registry)


def validate_dissent(
    dissent: DissentRecord,
    *,
    original_band: RatingBand,
    formal_band: RatingBand,
    independent_reviewer_id: str,
    review_attention_receipt_id: str,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> DissentRecord:
    if not isinstance(dissent, DissentRecord):
        raise InvalidInputError("dissent must be DissentRecord")
    op_id = _case_preflight(
        dissent.identity, expected_identity, dissent.applied_operations, operation_id
    )
    if not isinstance(original_band, RatingBand) or not isinstance(formal_band, RatingBand):
        raise InvalidInputError("dissent validation requires valid bands")
    reviewer = _require_identifier(independent_reviewer_id, "independent_reviewer_id")
    if reviewer in (dissent.manager_id, dissent.subject_id):
        raise ConservationError("dissent reviewer must differ from manager and subject")
    receipt = _require_identifier(
        review_attention_receipt_id, "review_attention_receipt_id"
    )
    aligned = formal_band is dissent.advocated_band and formal_band is not original_band
    return replace(
        dissent,
        identity=dissent.identity.advanced("dissent_validated"),
        attention_consumed=1,
        original_band=original_band,
        formal_band=formal_band,
        independent_reviewer_id=reviewer,
        review_attention_receipt_id=receipt,
        validation_outcome="aligned_overturn" if aligned else "not_validated",
        credit_delta=1 if aligned else -1,
        procedural_risk=not aligned,
        self_safe_evidence=True,
        applied_operations=dissent.applied_operations | frozenset({op_id}),
    )


def seal_consensus(
    consensus: ConsensusRecord,
    *,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> ConsensusRecord:
    if not isinstance(consensus, ConsensusRecord):
        raise InvalidInputError("consensus must be ConsensusRecord")
    op_id = _case_preflight(
        consensus.identity, expected_identity, consensus.applied_operations, operation_id
    )
    return replace(
        consensus,
        identity=consensus.identity.advanced("consensus_sealed"),
        sealed=True,
        applied_operations=consensus.applied_operations | frozenset({op_id}),
    )


@dataclass(frozen=True, slots=True)
class ShadowBandOrderCase:
    identity: CaseIdentity
    route: PolicyRoute
    formal_band: RatingBand
    ordered_subject_ids: tuple[str, ...]
    disclosed: bool
    allowed_uses: tuple[str, ...]
    opportunity_reads_order: bool
    official_bands: tuple[BandAssignment, ...]
    coaching_subject_ids: tuple[str, ...] = ()
    opportunity_subject_ids: tuple[str, ...] = ()
    appeal_evidence_subject_ids: tuple[str, ...] = ()
    black_box_audit: bool = False
    applied_operations: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CaseIdentity) or self.identity.state not in (
            "shadow_band_frozen",
            "shadow_band_consumed",
        ):
            raise InvalidInputError("shadow-band order has an invalid identity state")
        if self.route not in (PolicyRoute.A, PolicyRoute.B) or not isinstance(
            self.formal_band, RatingBand
        ):
            raise InvalidInputError("invalid shadow-band route/band")
        subjects = tuple(self.ordered_subject_ids)
        uses = tuple(self.allowed_uses)
        official = tuple(self.official_bands)
        coaching = tuple(self.coaching_subject_ids)
        opportunities = tuple(self.opportunity_subject_ids)
        appeal_evidence = tuple(self.appeal_evidence_subject_ids)
        for subject_id in subjects:
            _require_identifier(subject_id, "subject_id")
        for use in uses:
            _require_identifier(use, "allowed_use")
        if len(subjects) < 2 or len(set(subjects)) != len(subjects):
            raise DuplicateInputError(
                "shadow-band ranking needs at least two unique same-band subjects"
            )
        if self.formal_band is not RatingBand.MIDDLE:
            raise ConservationError("shadow-band order may rank only formal 3.5 subjects")
        if any(not isinstance(item, BandAssignment) for item in official):
            raise InvalidInputError("official shadow-band assignments are invalid")
        if tuple(item.subject_id for item in official) != subjects or any(
            item.band is not self.formal_band for item in official
        ):
            raise ConservationError("shadow order may contain one formal band only")
        if self.disclosed != (self.route is PolicyRoute.A):
            raise ConservationError("only route A discloses shadow order")
        if not self.opportunity_reads_order:
            raise ConservationError("shadow order must have one bounded opportunity consumer")
        expected_uses = (
            ("coaching", "opportunity")
            if self.route is PolicyRoute.A
            else ("private_opportunity", "appeal_evidence")
        )
        if uses != expected_uses:
            raise ConservationError("shadow-order consumers contradict the selected route")
        for selected, field in (
            (coaching, "coaching"),
            (opportunities, "opportunity"),
            (appeal_evidence, "appeal evidence"),
        ):
            if not set(selected).issubset(set(subjects)) or len(set(selected)) != len(
                selected
            ):
                raise ConservationError(f"shadow {field} escaped its 3.5 cohort")
        if self.identity.state == "shadow_band_frozen":
            if coaching or opportunities or appeal_evidence or self.black_box_audit:
                raise ConservationError("frozen shadow order cannot contain outcomes")
        else:
            if self.black_box_audit != (self.route is PolicyRoute.B):
                raise ConservationError("private rank consumer must create a black-box audit")
            if not opportunities or len(opportunities) >= len(subjects):
                raise ConservationError(
                    "shadow rank must allocate a finite, differentiating opportunity"
                )
            if self.route is PolicyRoute.A:
                if not coaching or len(coaching) >= len(subjects) or appeal_evidence:
                    raise ConservationError(
                        "public rank needs finite coaching and no black-box appeal evidence"
                    )
            elif coaching or set(appeal_evidence) != set(subjects):
                raise ConservationError(
                    "private rank needs no coaching and affected-self appeal evidence"
                )
            if any(item.band is not self.formal_band for item in official):
                raise ConservationError("shadow consumer rewrote an official band")
        object.__setattr__(self, "ordered_subject_ids", subjects)
        object.__setattr__(self, "allowed_uses", uses)
        object.__setattr__(self, "official_bands", official)
        object.__setattr__(self, "coaching_subject_ids", coaching)
        object.__setattr__(self, "opportunity_subject_ids", opportunities)
        object.__setattr__(self, "appeal_evidence_subject_ids", appeal_evidence)
        object.__setattr__(self, "applied_operations", frozenset(self.applied_operations))


def open_shadow_band_order_case(
    policy_ledger: PolicyDecisionLedger,
    *,
    identity: CaseIdentity,
    route: PolicyRoute,
    formal_band: RatingBand,
    ordered_subject_ids: Sequence[str],
    operation_id: str,
) -> PolicyOpenResult:
    declined = _route_c_result(
        policy_ledger,
        mechanism_id=145,
        identity=identity,
        route=route,
        operation_id=operation_id,
    )
    if declined is not None:
        return declined
    subjects = tuple(ordered_subject_ids)
    case = ShadowBandOrderCase(
        identity=identity.advanced("shadow_band_frozen"),
        route=route,
        formal_band=formal_band,
        ordered_subject_ids=subjects,
        disclosed=route is PolicyRoute.A,
        allowed_uses=("coaching", "opportunity")
        if route is PolicyRoute.A
        else ("private_opportunity", "appeal_evidence"),
        opportunity_reads_order=True,
        official_bands=tuple(BandAssignment(subject_id, formal_band) for subject_id in subjects),
        applied_operations=frozenset({operation_id}),
    )
    return _record_policy_decision(
        policy_ledger,
        mechanism_id=145,
        identity=identity,
        route=route,
        operation_id=operation_id,
        business_object=case,
    )


def consume_shadow_band_order(
    case: ShadowBandOrderCase,
    *,
    coaching_count: int,
    opportunity_count: int,
    operation_id: str,
    expected_identity: CaseIdentity,
) -> ShadowBandOrderCase:
    if not isinstance(case, ShadowBandOrderCase):
        raise InvalidInputError("case must be ShadowBandOrderCase")
    op_id = _case_preflight(
        case.identity, expected_identity, case.applied_operations, operation_id
    )
    coaching = _require_int(coaching_count, "coaching_count")
    opportunity = _require_int(opportunity_count, "opportunity_count", minimum=1)
    subjects = case.ordered_subject_ids
    if opportunity >= len(subjects):
        raise ConservationError("opportunity capacity must differentiate the 3.5 cohort")
    if case.route is PolicyRoute.A:
        if coaching < 1 or coaching >= len(subjects):
            raise ConservationError("public coaching capacity must be finite and nonzero")
    elif coaching:
        raise ConservationError("private rank cannot project a public coaching consumer")
    return replace(
        case,
        identity=case.identity.advanced("shadow_band_consumed"),
        coaching_subject_ids=subjects[:coaching],
        opportunity_subject_ids=subjects[:opportunity],
        appeal_evidence_subject_ids=(subjects if case.route is PolicyRoute.B else ()),
        black_box_audit=case.route is PolicyRoute.B,
        applied_operations=case.applied_operations | frozenset({op_id}),
    )


__all__ = [
    "AgendaCalibrationCase",
    "AgendaEntry",
    "AgendaMode",
    "AgendaPlan",
    "AgendaResolution",
    "AttentionLedger",
    "AttentionOvertimeReceipt",
    "AttentionSeat",
    "AttentionSeatLedger",
    "BAND_ORDER",
    "BandRounding",
    "BandAssignment",
    "BoardRecalculationReceipt",
    "CaseIdentity",
    "ClosedCalibrationRound",
    "ClosurePhase",
    "CohortMember",
    "CK3_IMPLEMENTED",
    "CommonSuperiorPool",
    "ConservationError",
    "ConsensusRecord",
    "DebtKind",
    "DebtNotDueError",
    "DebtSettlement",
    "DebtState",
    "DEFAULT_WEIGHTS",
    "DuplicateInputError",
    "DuplicateOperationError",
    "DissentOpenResult",
    "DissentRecord",
    "DissentRegistry",
    "EligibilityPolicy",
    "EligibilityTreatment",
    "EvidencePolarity",
    "EvidenceSegment",
    "ExecutiveMustReviewCase",
    "ExecutiveReviewOpenResult",
    "ExecutiveReviewRegistry",
    "FrozenCandidateGrade",
    "GrayLeaverQuotaSource",
    "GrayLeaverResult",
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
    "PendingMilestoneCase",
    "PendingMilestoneOpenResult",
    "PendingMilestoneResolutionResult",
    "PolicyDecisionLedger",
    "PolicyDecisionReceipt",
    "PolicyOpenResult",
    "PolicyRoute",
    "PostCutoffCase",
    "PrecalibrationDiff",
    "PrecalibrationMeeting",
    "QuotaBook",
    "QuotaComputation",
    "QuotaCounts",
    "QuotaDebt",
    "QuotaRoundingCase",
    "QuotaModelError",
    "RatingBand",
    "READINESS",
    "RedCode",
    "RosterAuditState",
    "RosterChangeReceipt",
    "ReorganizationAllocationReceipt",
    "ReorganizationOwnershipCase",
    "ShadowBandOrderCase",
    "ShadowRatingCase",
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
    "allocate_reorganized_subject",
    "bind_attention_seat",
    "build_agenda",
    "charge_gray_leaver_to_existing_bottom",
    "compute_quota",
    "consume_attention_seat",
    "consume_agenda_subject",
    "consume_post_cutoff_case",
    "consume_precalibration_meeting",
    "consume_shadow_band_order",
    "hold_pending_slot",
    "issue_rewards",
    "lock_cohort",
    "open_attention_seat_ledger",
    "open_agenda_calibration_case",
    "open_dissent_case",
    "open_executive_must_review",
    "open_pending_milestone_case",
    "open_pending_slot_ledger",
    "open_post_cutoff_case",
    "open_precalibration_meeting",
    "open_quota_rounding_case",
    "open_reorganization_ownership_case",
    "open_roster_audit",
    "open_shadow_band_order_case",
    "open_shadow_rating_case",
    "pool_by_common_superior",
    "request_symmetric_reopen",
    "resolve_executive_must_review",
    "resolve_pending_milestone_case",
    "reseal_reopened_round",
    "resolve_pending_slot",
    "settle_due_debt",
    "seal_consensus",
    "spend_attention",
    "submit_shadow_evidence",
    "finalize_shadow_rating",
    "publish_rounded_quota",
    "transfer_attention_seat",
    "use_overtime_attention",
    "validate_dissent",
]
