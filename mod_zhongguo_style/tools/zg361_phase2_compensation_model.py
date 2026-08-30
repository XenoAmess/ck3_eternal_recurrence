#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 model for the phase-two 361 compensation domains.

This module models L (082-091), AE (278-289), and AF (290-300).  It is a
Python specification and test oracle only: it does not claim CK3 wiring,
fixture-live evidence, or a player-visible loop.

Money is represented as non-negative integer minor units.  Every real cash
outflow is split between the organization treasury and the responsible
manager's personal gold, balance-checked before mutation, and journaled with a
receipt.  Long-term units are not cash: their grant is conserved in the unit
ledger and the dual cash debit happens when a buyback is actually settled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Iterable, Mapping, Sequence


HONEST_RUNTIME_EVIDENCE: Final = "python-l0-model"
HONEST_CK3_RUNTIME: Final = "not-wired"
FULL_BPS: Final = 10_000


@dataclass(frozen=True)
class MechanismBehavior:
    mechanism_id: int
    domain: str
    title: str
    behavior: str


_BEHAVIOR_ROWS = (
    (82, "L", "Total Reward Formula", "total_reward_quote"),
    (83, "L", "Realm, Team, and Individual Bonus Multipliers", "three_factor_bonus"),
    (84, "L", "Deferred Bonus and Vesting", "grant_bonus"),
    (85, "L", "Retention Incentive Cliff", "retention_cliff_gap"),
    (86, "L", "Bonus Holdback and Clawback", "hold_and_clawback_bonus"),
    (87, "L", "Pay Bands and Position Within Band", "pay_band_position"),
    (88, "L", "Market Raises Versus Performance Raises", "allocate_raise_pool"),
    (89, "L", "Decoupling Rank, Appointment, Authority, and Cash", "career_package"),
    (90, "L", "Spot Awards", "pay_spot_award"),
    (91, "L", "Separate Tenure and Performance Awards", "separate_award_accounts"),
    (278, "AE", "Annual Total-Compensation Reconciliation", "pay_statement"),
    (279, "AE", "Contract Status of an Extra Month's Salary", "extra_month_contract"),
    (280, "AE", "Midyear Entry, Transfer, and Exit Proration", "prorate_award"),
    (281, "AE", "Bonus Payment Date and Deferral Credibility", "defer_statement"),
    (282, "AE", "Raise Effective Date and Retroactive True-Up", "apply_backpay"),
    (283, "AE", "Deadline for a Dry Promotion", "dry_promotion_commitment"),
    (284, "AE", "Pay-Buffer Slope After Demotion", "demotion_pay_schedule"),
    (285, "AE", "Second Calibration of Raises Within a Rating", "allocate_raise_pool"),
    (286, "AE", "Above-Band Freeze and Below-Band Catch-Up", "band_correction"),
    (287, "AE", "Pay Secrecy, Public Bands, or Anonymous Distribution", "pay_visibility"),
    (288, "AE", "Repairing New-Hire Pay Inversion", "repair_pay_inversion"),
    (289, "AE", "Separate Pay Appeals from Rating Appeals", "compensation_appeal"),
    (290, "AF", "Long-Term Award Nomination Pool", "select_lti_nominations"),
    (291, "AF", "Fixed Shares Versus Fixed Grant Value", "grant_units"),
    (292, "AF", "High-Risk Options Versus Restricted Units", "risk_award_choice"),
    (293, "AF", "Voluntary Bonus Conversion into Long-Term Units", "convert_bonus_to_units"),
    (294, "AF", "Grant Price, Current Valuation, and Liquid Value", "valuation_columns"),
    (295, "AF", "Length of the Initial Vesting Cliff", "lti_cliff"),
    (296, "AF", "Monthly, Quarterly, or Annual Vesting", "lti_cadence"),
    (297, "AF", "Separate Service and Performance Vesting", "lti_tracks"),
    (298, "AF", "Organization and Individual Vesting Gates", "lti_double_gate"),
    (299, "AF", "Good-Leaver and Bad-Leaver Classification", "classify_lti_leaver"),
    (300, "AF", "Buyback Window and Liquidity Queue", "settle_repurchase"),
)

MECHANISM_BEHAVIORS: Final[dict[int, MechanismBehavior]] = {
    row[0]: MechanismBehavior(*row) for row in _BEHAVIOR_ROWS
}


class CompensationRed(RuntimeError):
    """Base class for typed, deterministic domain failures."""

    code = "COMPENSATION_RED"

    def __init__(self, message: str) -> None:
        super().__init__(f"{self.code}: {message}")


class InvalidInputRed(CompensationRed):
    code = "INVALID_INPUT_RED"


class InsufficientFundsRed(CompensationRed):
    code = "INSUFFICIENT_FUNDS_RED"


class IdempotencyConflictRed(CompensationRed):
    code = "IDEMPOTENCY_CONFLICT_RED"


class FutureSerialRed(CompensationRed):
    code = "FUTURE_SERIAL_RED"


class FormulaLockedRed(CompensationRed):
    code = "FORMULA_LOCKED_RED"


class StateTransitionRed(CompensationRed):
    code = "STATE_TRANSITION_RED"


class ReceiptLimitRed(CompensationRed):
    code = "RECEIPT_LIMIT_RED"


class ConservationRed(CompensationRed):
    code = "CONSERVATION_RED"


class AppealTrackRed(CompensationRed):
    code = "APPEAL_TRACK_RED"


class QueueOrderRed(CompensationRed):
    code = "QUEUE_ORDER_RED"


class Disposition(str, Enum):
    APPLIED = "applied"
    IDEMPOTENT_NOOP = "idempotent-noop"
    STALE_NOOP = "stale-noop"


@dataclass(frozen=True)
class OperationResult:
    disposition: Disposition
    value: int = 0
    receipt_id: str | None = None
    detail: str = ""

    def as_idempotent(self) -> "OperationResult":
        return OperationResult(
            Disposition.IDEMPOTENT_NOOP,
            value=self.value,
            receipt_id=self.receipt_id,
            detail=self.detail,
        )


class IdempotencyClock:
    """Exact-serial guard with repeat-safe operation keys."""

    def __init__(self, case_serial: int) -> None:
        if case_serial < 1:
            raise InvalidInputRed("case serial must be positive")
        self.case_serial = case_serial
        self._history: dict[str, tuple[tuple[object, ...], OperationResult]] = {}

    def advance(self, new_serial: int) -> None:
        if new_serial <= self.case_serial:
            raise InvalidInputRed("case serial must advance monotonically")
        self.case_serial = new_serial

    def guard(
        self,
        operation_key: str,
        case_serial: int,
        fingerprint: tuple[object, ...],
    ) -> OperationResult | None:
        if not operation_key:
            raise InvalidInputRed("operation key is required")
        previous = self._history.get(operation_key)
        if previous is not None:
            old_fingerprint, old_result = previous
            if old_fingerprint != fingerprint:
                raise IdempotencyConflictRed(
                    f"operation {operation_key!r} was replayed with different inputs"
                )
            return old_result.as_idempotent()
        if case_serial < self.case_serial:
            return OperationResult(Disposition.STALE_NOOP, detail="stale case serial")
        if case_serial > self.case_serial:
            raise FutureSerialRed(
                f"operation serial {case_serial} is ahead of active {self.case_serial}"
            )
        return None

    def commit(
        self,
        operation_key: str,
        fingerprint: tuple[object, ...],
        result: OperationResult,
    ) -> OperationResult:
        self._history[operation_key] = (fingerprint, result)
        return result


def _require_nonnegative(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidInputRed(f"{name} must be a non-negative integer")


def _require_positive(name: str, value: int) -> None:
    _require_nonnegative(name, value)
    if value == 0:
        raise InvalidInputRed(f"{name} must be positive")


def multiply_bps(amount: int, *factors_bps: int) -> int:
    """Apply basis-point factors with one final deterministic half-up round."""

    _require_nonnegative("amount", amount)
    numerator = amount
    denominator = 1
    for factor in factors_bps:
        _require_nonnegative("factor_bps", factor)
        numerator *= factor
        denominator *= FULL_BPS
    return (numerator + denominator // 2) // denominator


@dataclass(frozen=True)
class FundingSplit:
    """Configurable, explicit dual-payer split; neither payer may be omitted."""

    treasury_bps: int = 7_000
    manager_bps: int = 3_000

    def __post_init__(self) -> None:
        if self.treasury_bps + self.manager_bps != FULL_BPS:
            raise InvalidInputRed("funding split must total 10000 bps")
        if self.treasury_bps <= 0 or self.manager_bps <= 0:
            raise InvalidInputRed("treasury and manager shares must both be positive")

    def allocate(self, amount: int) -> tuple[int, int]:
        _require_positive("cash amount", amount)
        if amount < 2:
            raise InvalidInputRed("a dual-funded cash payment needs at least two units")
        treasury = (amount * self.treasury_bps + FULL_BPS // 2) // FULL_BPS
        treasury = max(1, min(amount - 1, treasury))
        return treasury, amount - treasury


@dataclass
class WalletBook:
    treasury_gold: int
    manager_gold: int
    recipient_gold: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative("treasury_gold", self.treasury_gold)
        _require_nonnegative("manager_gold", self.manager_gold)
        _require_nonnegative("recipient_gold", self.recipient_gold)


class ReceiptKind(str, Enum):
    RESERVE = "reserve"
    SETTLEMENT = "settlement"
    PAYMENT = "payment"
    REFUND = "refund"
    RETURN = "return"


@dataclass
class Receipt:
    receipt_id: str
    kind: ReceiptKind
    operation_key: str
    case_serial: int
    gross: int
    treasury_debit: int = 0
    manager_debit: int = 0
    recipient_credit: int = 0
    treasury_credit: int = 0
    manager_credit: int = 0
    recipient_debit: int = 0
    source_receipt_id: str | None = None
    funded_treasury: int = 0
    funded_manager: int = 0
    settled_gross: int = 0
    refunded_gross: int = 0
    returned_gross: int = 0
    returned_treasury: int = 0
    returned_manager: int = 0

    @property
    def reservation_available(self) -> int:
        return self.gross - self.settled_gross - self.refunded_gross

    @property
    def return_available(self) -> int:
        return self.recipient_credit - self.returned_gross


def _take_from_split(amount: int, left_a: int, left_b: int) -> tuple[int, int]:
    """Take ``amount`` from a two-part conserved pool without overdrawing it."""

    _require_nonnegative("left_a", left_a)
    _require_nonnegative("left_b", left_b)
    if amount < 0 or amount > left_a + left_b:
        raise ReceiptLimitRed("requested amount exceeds receipt balance")
    if amount == 0:
        return 0, 0
    total = left_a + left_b
    take_a = (amount * left_a + total // 2) // total
    take_a = min(left_a, max(0, take_a))
    take_b = amount - take_a
    if take_b > left_b:
        take_b = left_b
        take_a = amount - take_b
    if take_a > left_a:
        raise ConservationRed("split allocation overdraw")
    return take_a, take_b


class TransactionJournal:
    """Atomic dual-payer reserve/payment/refund/return journal."""

    def __init__(
        self,
        wallets: WalletBook,
        split: FundingSplit,
        case_serial: int,
    ) -> None:
        self.wallets = wallets
        self.split = split
        self.clock = IdempotencyClock(case_serial)
        self.receipts: dict[str, Receipt] = {}
        self._receipt_counter = 0

    def advance(self, new_serial: int) -> None:
        self.clock.advance(new_serial)

    def _next_receipt_id(self, kind: ReceiptKind) -> str:
        self._receipt_counter += 1
        return f"{kind.value}:{self.clock.case_serial}:{self._receipt_counter}"

    def _precheck_payers(self, treasury: int, manager: int) -> None:
        if self.wallets.treasury_gold < treasury:
            raise InsufficientFundsRed("organization treasury cannot fund its share")
        if self.wallets.manager_gold < manager:
            raise InsufficientFundsRed("responsible manager cannot fund the personal share")

    def reserve(self, amount: int, *, operation_key: str, case_serial: int) -> OperationResult:
        treasury, manager = self.split.allocate(amount)
        fingerprint = ("reserve", amount, treasury, manager)
        guarded = self.clock.guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        self._precheck_payers(treasury, manager)
        receipt_id = self._next_receipt_id(ReceiptKind.RESERVE)
        receipt = Receipt(
            receipt_id=receipt_id,
            kind=ReceiptKind.RESERVE,
            operation_key=operation_key,
            case_serial=case_serial,
            gross=amount,
            treasury_debit=treasury,
            manager_debit=manager,
            funded_treasury=treasury,
            funded_manager=manager,
        )
        # Both balances are checked before either is changed: this is the
        # model's atomic commit boundary.
        self.wallets.treasury_gold -= treasury
        self.wallets.manager_gold -= manager
        self.receipts[receipt_id] = receipt
        return self.clock.commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount, receipt_id),
        )

    def settle_reserved(
        self,
        reserve_receipt_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        _require_positive("settlement amount", amount)
        reserve = self.receipts.get(reserve_receipt_id)
        if reserve is None or reserve.kind is not ReceiptKind.RESERVE:
            raise StateTransitionRed("settlement requires a reserve receipt")
        fingerprint = ("settle", reserve_receipt_id, amount)
        guarded = self.clock.guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if amount > reserve.reservation_available:
            raise ReceiptLimitRed("settlement exceeds remaining reservation")
        left_treasury = (
            reserve.funded_treasury
            - sum(
                r.funded_treasury
                for r in self.receipts.values()
                if r.kind is ReceiptKind.SETTLEMENT
                and r.source_receipt_id == reserve_receipt_id
            )
            - sum(
                r.treasury_credit
                for r in self.receipts.values()
                if r.kind is ReceiptKind.REFUND
                and r.source_receipt_id == reserve_receipt_id
            )
        )
        left_manager = (
            reserve.funded_manager
            - sum(
                r.funded_manager
                for r in self.receipts.values()
                if r.kind is ReceiptKind.SETTLEMENT
                and r.source_receipt_id == reserve_receipt_id
            )
            - sum(
                r.manager_credit
                for r in self.receipts.values()
                if r.kind is ReceiptKind.REFUND
                and r.source_receipt_id == reserve_receipt_id
            )
        )
        funded_treasury, funded_manager = _take_from_split(
            amount, left_treasury, left_manager
        )
        receipt_id = self._next_receipt_id(ReceiptKind.SETTLEMENT)
        self.wallets.recipient_gold += amount
        reserve.settled_gross += amount
        self.receipts[receipt_id] = Receipt(
            receipt_id=receipt_id,
            kind=ReceiptKind.SETTLEMENT,
            operation_key=operation_key,
            case_serial=case_serial,
            gross=amount,
            recipient_credit=amount,
            source_receipt_id=reserve_receipt_id,
            funded_treasury=funded_treasury,
            funded_manager=funded_manager,
        )
        return self.clock.commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount, receipt_id),
        )

    def pay(self, amount: int, *, operation_key: str, case_serial: int) -> OperationResult:
        treasury, manager = self.split.allocate(amount)
        fingerprint = ("pay", amount, treasury, manager)
        guarded = self.clock.guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        self._precheck_payers(treasury, manager)
        receipt_id = self._next_receipt_id(ReceiptKind.PAYMENT)
        self.wallets.treasury_gold -= treasury
        self.wallets.manager_gold -= manager
        self.wallets.recipient_gold += amount
        self.receipts[receipt_id] = Receipt(
            receipt_id=receipt_id,
            kind=ReceiptKind.PAYMENT,
            operation_key=operation_key,
            case_serial=case_serial,
            gross=amount,
            treasury_debit=treasury,
            manager_debit=manager,
            recipient_credit=amount,
            funded_treasury=treasury,
            funded_manager=manager,
        )
        return self.clock.commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount, receipt_id),
        )

    def refund_reservation(
        self,
        reserve_receipt_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        _require_positive("refund amount", amount)
        reserve = self.receipts.get(reserve_receipt_id)
        if reserve is None or reserve.kind is not ReceiptKind.RESERVE:
            raise StateTransitionRed("refund requires a reserve receipt")
        fingerprint = ("refund", reserve_receipt_id, amount)
        guarded = self.clock.guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if amount > reserve.reservation_available:
            raise ReceiptLimitRed("refund exceeds unused original reservation")
        remaining_total = reserve.reservation_available
        settled_treasury = sum(
            r.funded_treasury
            for r in self.receipts.values()
            if r.kind is ReceiptKind.SETTLEMENT and r.source_receipt_id == reserve_receipt_id
        )
        settled_manager = sum(
            r.funded_manager
            for r in self.receipts.values()
            if r.kind is ReceiptKind.SETTLEMENT and r.source_receipt_id == reserve_receipt_id
        )
        refunded_treasury = sum(
            r.treasury_credit
            for r in self.receipts.values()
            if r.kind is ReceiptKind.REFUND and r.source_receipt_id == reserve_receipt_id
        )
        refunded_manager = sum(
            r.manager_credit
            for r in self.receipts.values()
            if r.kind is ReceiptKind.REFUND and r.source_receipt_id == reserve_receipt_id
        )
        left_treasury = reserve.funded_treasury - settled_treasury - refunded_treasury
        left_manager = reserve.funded_manager - settled_manager - refunded_manager
        if left_treasury + left_manager != remaining_total:
            raise ConservationRed("reservation payer split drifted")
        treasury, manager = _take_from_split(amount, left_treasury, left_manager)
        receipt_id = self._next_receipt_id(ReceiptKind.REFUND)
        self.wallets.treasury_gold += treasury
        self.wallets.manager_gold += manager
        reserve.refunded_gross += amount
        self.receipts[receipt_id] = Receipt(
            receipt_id=receipt_id,
            kind=ReceiptKind.REFUND,
            operation_key=operation_key,
            case_serial=case_serial,
            gross=amount,
            treasury_credit=treasury,
            manager_credit=manager,
            source_receipt_id=reserve_receipt_id,
        )
        return self.clock.commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount, receipt_id),
        )

    def return_paid(
        self,
        payment_receipt_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        _require_positive("returned amount", amount)
        source = self.receipts.get(payment_receipt_id)
        if source is None or source.kind not in (ReceiptKind.PAYMENT, ReceiptKind.SETTLEMENT):
            raise StateTransitionRed("return requires a payment or settlement receipt")
        fingerprint = ("return", payment_receipt_id, amount)
        guarded = self.clock.guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if amount > source.return_available:
            raise ReceiptLimitRed("return exceeds the original payment receipt")
        if self.wallets.recipient_gold < amount:
            raise InsufficientFundsRed("recipient cannot return the requested amount")
        left_treasury = source.funded_treasury - source.returned_treasury
        left_manager = source.funded_manager - source.returned_manager
        treasury, manager = _take_from_split(amount, left_treasury, left_manager)
        receipt_id = self._next_receipt_id(ReceiptKind.RETURN)
        self.wallets.recipient_gold -= amount
        self.wallets.treasury_gold += treasury
        self.wallets.manager_gold += manager
        source.returned_gross += amount
        source.returned_treasury += treasury
        source.returned_manager += manager
        self.receipts[receipt_id] = Receipt(
            receipt_id=receipt_id,
            kind=ReceiptKind.RETURN,
            operation_key=operation_key,
            case_serial=case_serial,
            gross=amount,
            treasury_credit=treasury,
            manager_credit=manager,
            recipient_debit=amount,
            source_receipt_id=payment_receipt_id,
        )
        return self.clock.commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount, receipt_id),
        )

    def assert_conserved(self) -> None:
        for receipt in self.receipts.values():
            if receipt.kind is ReceiptKind.RESERVE:
                if receipt.gross != receipt.treasury_debit + receipt.manager_debit:
                    raise ConservationRed("reserve receipt debit does not equal gross")
                if receipt.reservation_available < 0:
                    raise ConservationRed("reserve receipt was over-consumed")
            elif receipt.kind is ReceiptKind.PAYMENT:
                if receipt.gross != receipt.treasury_debit + receipt.manager_debit:
                    raise ConservationRed("payment debit does not equal gross")
                if receipt.gross != receipt.recipient_credit:
                    raise ConservationRed("payment credit does not equal gross")
            elif receipt.kind is ReceiptKind.SETTLEMENT:
                if receipt.gross != receipt.funded_treasury + receipt.funded_manager:
                    raise ConservationRed("settlement funding does not equal gross")
                if receipt.gross != receipt.recipient_credit:
                    raise ConservationRed("settlement credit does not equal gross")
            elif receipt.kind in (ReceiptKind.REFUND, ReceiptKind.RETURN):
                if receipt.gross != receipt.treasury_credit + receipt.manager_credit:
                    raise ConservationRed("refund/return credits do not equal gross")


@dataclass(frozen=True)
class TotalRewardQuote:
    fixed_pay: int
    role_allowance: int
    performance_bonus: int
    spot_award: int
    deferred_award: int

    def __post_init__(self) -> None:
        for name, value in self.components.items():
            _require_nonnegative(name, value)

    @property
    def components(self) -> dict[str, int]:
        return {
            "fixed_pay": self.fixed_pay,
            "role_allowance": self.role_allowance,
            "performance_bonus": self.performance_bonus,
            "spot_award": self.spot_award,
            "deferred_award": self.deferred_award,
        }

    @property
    def total(self) -> int:
        return sum(self.components.values())


def total_reward_quote(**components: int) -> TotalRewardQuote:
    return TotalRewardQuote(**components)


def three_factor_bonus(
    base: int,
    *,
    realm_bps: int,
    team_bps: int,
    individual_bps: int,
) -> int:
    return multiply_bps(base, realm_bps, team_bps, individual_bps)


@dataclass(frozen=True)
class BonusFormula:
    base: int
    realm_bps: int
    team_bps: int
    individual_bps: int
    immediate_bps: int = 7_000
    deferred_bps: int = 2_000
    holdback_bps: int = 1_000
    version: int = 1

    def __post_init__(self) -> None:
        _require_positive("bonus base", self.base)
        for name in ("realm_bps", "team_bps", "individual_bps"):
            _require_nonnegative(name, getattr(self, name))
        if self.immediate_bps + self.deferred_bps + self.holdback_bps != FULL_BPS:
            raise InvalidInputRed("bonus grant buckets must total 10000 bps")
        if self.version < 1:
            raise InvalidInputRed("formula version must be positive")

    @property
    def total(self) -> int:
        return three_factor_bonus(
            self.base,
            realm_bps=self.realm_bps,
            team_bps=self.team_bps,
            individual_bps=self.individual_bps,
        )

    def buckets(self) -> tuple[int, int, int]:
        immediate = multiply_bps(self.total, self.immediate_bps)
        deferred = multiply_bps(self.total, self.deferred_bps)
        held = self.total - immediate - deferred
        if held < 0:
            raise ConservationRed("rounded bonus buckets exceed award")
        return immediate, deferred, held


class BonusState(str, Enum):
    FORMULA_LOCKED = "formula-locked"
    FUNDS_RESERVED = "funds-reserved"
    GRANTED = "granted"
    CLOSED = "closed"


@dataclass
class BonusAward:
    award_id: str
    formula: BonusFormula
    state: BonusState = BonusState.FORMULA_LOCKED
    reserve_receipt_id: str | None = None
    immediate_owed: int = 0
    deferred_owed: int = 0
    held: int = 0
    paid_gross: int = 0
    returned: int = 0
    forfeited: int = 0
    payment_receipts: list[str] = field(default_factory=list)

    @property
    def paid_net(self) -> int:
        return self.paid_gross - self.returned

    def assert_conserved(self) -> None:
        if self.state in (BonusState.GRANTED, BonusState.CLOSED):
            accounted = (
                self.immediate_owed
                + self.deferred_owed
                + self.held
                + self.paid_net
                + self.forfeited
            )
            if accounted != self.formula.total:
                raise ConservationRed(
                    f"bonus {self.award_id} accounts for {accounted}, expected {self.formula.total}"
                )
        if min(
            self.immediate_owed,
            self.deferred_owed,
            self.held,
            self.paid_net,
            self.forfeited,
        ) < 0:
            raise ConservationRed("bonus bucket became negative")


@dataclass
class PayStatement:
    statement_id: str
    components: dict[str, int]
    due_day: int
    performance_grade: int
    payable: int = 0
    paid: int = 0
    owed: int = 0
    returned: int = 0
    delay_count: int = 0
    credibility: int = 100
    payment_receipts: list[str] = field(default_factory=list)
    corrections: list[tuple[str, int]] = field(default_factory=list)
    appeals: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.due_day < 0:
            raise InvalidInputRed("due day must be non-negative")
        for key, amount in self.components.items():
            _require_nonnegative(f"component {key}", amount)
        if self.payable == 0 and self.paid == 0 and self.owed == 0:
            self.payable = sum(self.components.values())
            self.owed = self.payable
        self.assert_conserved()

    def assert_conserved(self) -> None:
        if self.payable != self.paid + self.owed - self.returned:
            raise ConservationRed(
                "payable must equal paid + owed - returned"
            )
        if min(self.payable, self.paid, self.owed, self.returned) < 0:
            raise ConservationRed("pay statement amount became negative")

    def annual_reconciliation(self) -> dict[str, int]:
        return {
            "promised": self.payable,
            "paid": self.paid,
            "owed": self.owed,
            "returned": self.returned,
            "difference": self.owed - self.returned,
        }


class CompensationKernel:
    """Stateful bonus/pay kernel sharing one atomic transaction journal."""

    def __init__(
        self,
        *,
        treasury_gold: int,
        manager_gold: int,
        recipient_gold: int = 0,
        split: FundingSplit | None = None,
        case_serial: int = 1,
    ) -> None:
        self.wallets = WalletBook(treasury_gold, manager_gold, recipient_gold)
        self.split = split or FundingSplit()
        self.clock = IdempotencyClock(case_serial)
        self.journal = TransactionJournal(self.wallets, self.split, case_serial)
        self.bonuses: dict[str, BonusAward] = {}
        self.statements: dict[str, PayStatement] = {}
        self.lti_grants: dict[str, LTIGrant] = {}
        self.repurchase_queue: list[RepurchaseRequest] = []

    @property
    def case_serial(self) -> int:
        return self.clock.case_serial

    def advance_case_serial(self, new_serial: int) -> None:
        self.clock.advance(new_serial)
        self.journal.advance(new_serial)

    def _guard(
        self,
        operation_key: str,
        case_serial: int,
        fingerprint: tuple[object, ...],
    ) -> OperationResult | None:
        return self.clock.guard(operation_key, case_serial, fingerprint)

    def _commit(
        self,
        operation_key: str,
        fingerprint: tuple[object, ...],
        result: OperationResult,
    ) -> OperationResult:
        return self.clock.commit(operation_key, fingerprint, result)

    def lock_bonus_formula(
        self,
        award_id: str,
        formula: BonusFormula,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        fingerprint = ("lock-formula", award_id, formula)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if award_id in self.bonuses:
            if self.bonuses[award_id].formula != formula:
                raise FormulaLockedRed("a locked bonus formula cannot be rewritten")
            raise IdempotencyConflictRed("same formula needs the original operation key")
        self.bonuses[award_id] = BonusAward(award_id, formula)
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, formula.total),
        )

    def reserve_bonus(
        self,
        award_id: str,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        fingerprint = ("reserve-bonus", award_id, award.formula.total)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if award.state is not BonusState.FORMULA_LOCKED:
            raise StateTransitionRed("bonus can only reserve after formula lock")
        journal_result = self.journal.reserve(
            award.formula.total,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        award.reserve_receipt_id = journal_result.receipt_id
        award.state = BonusState.FUNDS_RESERVED
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(
                Disposition.APPLIED, award.formula.total, journal_result.receipt_id
            ),
        )

    def grant_bonus(
        self,
        award_id: str,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        fingerprint = ("grant-bonus", award_id, award.formula.buckets())
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if award.state is not BonusState.FUNDS_RESERVED:
            raise StateTransitionRed("bonus grant requires reserved funds")
        award.immediate_owed, award.deferred_owed, award.held = award.formula.buckets()
        award.state = BonusState.GRANTED
        award.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, award.formula.total),
        )

    def hold_bonus(
        self,
        award_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        _require_positive("hold amount", amount)
        fingerprint = ("hold-bonus", award_id, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if award.state is not BonusState.GRANTED or amount > award.immediate_owed:
            raise StateTransitionRed("holdback must come from unpaid immediate bonus")
        award.immediate_owed -= amount
        award.held += amount
        award.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount),
        )

    def settle_bonus(
        self,
        award_id: str,
        bucket: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        _require_positive("bonus settlement", amount)
        fingerprint = ("settle-bonus", award_id, bucket, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        bucket_field = {
            "immediate": "immediate_owed",
            "deferred": "deferred_owed",
            "held": "held",
        }.get(bucket)
        if award.state is not BonusState.GRANTED or bucket_field is None:
            raise StateTransitionRed("unknown or unavailable bonus settlement bucket")
        available = getattr(award, bucket_field)
        if amount > available:
            raise StateTransitionRed("bonus settlement exceeds bucket")
        assert award.reserve_receipt_id is not None
        journal_result = self.journal.settle_reserved(
            award.reserve_receipt_id,
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        setattr(award, bucket_field, available - amount)
        award.paid_gross += amount
        assert journal_result.receipt_id is not None
        award.payment_receipts.append(journal_result.receipt_id)
        award.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(
                Disposition.APPLIED, amount, journal_result.receipt_id
            ),
        )

    def forfeit_bonus(
        self,
        award_id: str,
        bucket: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        _require_positive("forfeit amount", amount)
        fingerprint = ("forfeit-bonus", award_id, bucket, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        bucket_field = {
            "immediate": "immediate_owed",
            "deferred": "deferred_owed",
            "held": "held",
        }.get(bucket)
        if award.state is not BonusState.GRANTED or bucket_field is None:
            raise StateTransitionRed("unknown bonus forfeiture bucket")
        available = getattr(award, bucket_field)
        if amount > available:
            raise StateTransitionRed("forfeiture exceeds bonus bucket")
        assert award.reserve_receipt_id is not None
        journal_result = self.journal.refund_reservation(
            award.reserve_receipt_id,
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        setattr(award, bucket_field, available - amount)
        award.forfeited += amount
        award.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(
                Disposition.APPLIED, amount, journal_result.receipt_id
            ),
        )

    def clawback_bonus(
        self,
        award_id: str,
        payment_receipt_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        award = self._bonus(award_id)
        _require_positive("clawback amount", amount)
        fingerprint = ("clawback", award_id, payment_receipt_id, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if payment_receipt_id not in award.payment_receipts:
            raise StateTransitionRed("receipt does not belong to this bonus")
        journal_result = self.journal.return_paid(
            payment_receipt_id,
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        award.returned += amount
        award.forfeited += amount
        award.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(
                Disposition.APPLIED, amount, journal_result.receipt_id
            ),
        )

    def pay_spot_award(
        self,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        fingerprint = ("spot-award", amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        paid = self.journal.pay(
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        return self._commit(operation_key, fingerprint, paid)

    def create_pay_statement(
        self,
        statement_id: str,
        components: Mapping[str, int],
        *,
        due_day: int,
        performance_grade: int,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        normalized = tuple(sorted(components.items()))
        fingerprint = (
            "create-statement",
            statement_id,
            normalized,
            due_day,
            performance_grade,
        )
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if statement_id in self.statements:
            raise StateTransitionRed("pay statement already exists")
        statement = PayStatement(
            statement_id,
            dict(normalized),
            due_day,
            performance_grade,
        )
        self.statements[statement_id] = statement
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, statement.payable),
        )

    def pay_statement(
        self,
        statement_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        _require_positive("statement payment", amount)
        fingerprint = ("pay-statement", statement_id, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if amount > statement.owed:
            raise StateTransitionRed("payment exceeds statement amount owed")
        paid = self.journal.pay(
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        statement.paid += amount
        statement.owed -= amount
        assert paid.receipt_id is not None
        statement.payment_receipts.append(paid.receipt_id)
        statement.assert_conserved()
        return self._commit(operation_key, fingerprint, paid)

    def return_statement_payment(
        self,
        statement_id: str,
        payment_receipt_id: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        fingerprint = ("return-statement", statement_id, payment_receipt_id, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if payment_receipt_id not in statement.payment_receipts:
            raise StateTransitionRed("receipt does not belong to this pay statement")
        returned = self.journal.return_paid(
            payment_receipt_id,
            amount,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        statement.returned += amount
        statement.owed += amount
        statement.assert_conserved()
        return self._commit(operation_key, fingerprint, returned)

    def defer_statement(
        self,
        statement_id: str,
        new_due_day: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        fingerprint = ("defer", statement_id, new_due_day)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if new_due_day <= statement.due_day or statement.owed == 0:
            raise StateTransitionRed("deferral needs a later date and an unpaid balance")
        statement.due_day = new_due_day
        statement.delay_count += 1
        statement.credibility = max(0, statement.credibility - 15 * statement.delay_count)
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, statement.owed),
        )

    def apply_backpay(
        self,
        statement_id: str,
        amount: int,
        *,
        reason: str,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        _require_positive("backpay", amount)
        if not reason:
            raise InvalidInputRed("backpay needs a reason code")
        fingerprint = ("backpay", statement_id, amount, reason)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        statement.payable += amount
        statement.owed += amount
        statement.corrections.append((reason, amount))
        statement.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount),
        )

    def cancel_unpaid_obligation(
        self,
        statement_id: str,
        amount: int,
        *,
        reason: str,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        _require_positive("correction", amount)
        fingerprint = ("cancel-unpaid", statement_id, amount, reason)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if amount > statement.owed:
            raise StateTransitionRed("negative correction exceeds unpaid obligation")
        statement.payable -= amount
        statement.owed -= amount
        statement.corrections.append((reason, -amount))
        statement.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount),
        )

    def open_appeal(
        self,
        statement_id: str,
        track: str,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        fingerprint = ("open-appeal", statement_id, track)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if track not in ("compensation", "performance"):
            raise AppealTrackRed("appeal must choose compensation or performance")
        if track in statement.appeals:
            raise StateTransitionRed("appeal track already opened")
        statement.appeals[track] = "open"
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, detail=track),
        )

    def resolve_compensation_appeal(
        self,
        statement_id: str,
        correction: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        statement = self._statement(statement_id)
        _require_nonnegative("appeal correction", correction)
        fingerprint = ("resolve-pay-appeal", statement_id, correction)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if statement.appeals.get("compensation") != "open":
            raise AppealTrackRed("only an open compensation appeal may change pay")
        frozen_grade = statement.performance_grade
        statement.payable += correction
        statement.owed += correction
        statement.corrections.append(("compensation_appeal", correction))
        statement.appeals["compensation"] = "upheld" if correction else "denied"
        if statement.performance_grade != frozen_grade:
            raise ConservationRed("compensation appeal changed performance grade")
        statement.assert_conserved()
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, correction),
        )

    def create_lti_grant(
        self,
        grant: "LTIGrant",
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        fingerprint = ("create-lti",) + grant.fingerprint()
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if grant.grant_id in self.lti_grants:
            raise StateTransitionRed("LTI grant already exists")
        grant.assert_conserved()
        self.lti_grants[grant.grant_id] = grant
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, grant.total_units),
        )

    def vest_lti(
        self,
        grant_id: str,
        *,
        as_of_day: int,
        service_active: bool,
        performance_met: bool,
        organization_met: bool,
        individual_met: bool,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        grant = self._grant(grant_id)
        fingerprint = (
            "vest-lti",
            grant_id,
            as_of_day,
            service_active,
            performance_met,
            organization_met,
            individual_met,
        )
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        units = grant.vest(
            as_of_day=as_of_day,
            service_active=service_active,
            performance_met=performance_met,
            organization_met=organization_met,
            individual_met=individual_met,
        )
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, units),
        )

    def classify_lti_leaver(
        self,
        grant_id: str,
        classification: "LeaverClass",
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        grant = self._grant(grant_id)
        fingerprint = ("lti-leaver", grant_id, classification.value)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        forfeited = grant.classify_leaver(classification)
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, forfeited),
        )

    def forfeit_lti(
        self,
        grant_id: str,
        track: str,
        amount: int,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        grant = self._grant(grant_id)
        _require_positive("LTI forfeiture", amount)
        fingerprint = ("forfeit-lti", grant_id, track, amount)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        grant.forfeit(track, amount)
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, amount),
        )

    def request_repurchase(
        self,
        grant_id: str,
        units: int,
        price_per_unit: int,
        *,
        window_open: bool,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        grant = self._grant(grant_id)
        _require_positive("repurchase units", units)
        _require_positive("repurchase price", price_per_unit)
        fingerprint = (
            "request-repurchase",
            grant_id,
            units,
            price_per_unit,
            window_open,
        )
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        if not window_open:
            raise StateTransitionRed("repurchase window is closed")
        if units > grant.vested_units:
            raise StateTransitionRed("repurchase request exceeds vested units")
        already_queued = sum(
            request.units
            for request in self.repurchase_queue
            if request.grant_id == grant_id and request.state == "queued"
        )
        if units + already_queued > grant.vested_units:
            raise StateTransitionRed("queued repurchases exceed vested units")
        request_id = f"repurchase:{len(self.repurchase_queue) + 1}"
        self.repurchase_queue.append(
            RepurchaseRequest(request_id, grant_id, units, price_per_unit)
        )
        return self._commit(
            operation_key,
            fingerprint,
            OperationResult(Disposition.APPLIED, units, detail=request_id),
        )

    def settle_repurchase(
        self,
        request_id: str,
        *,
        operation_key: str,
        case_serial: int,
    ) -> OperationResult:
        request = self._request(request_id)
        fingerprint = ("settle-repurchase", request_id, request.units, request.price_per_unit)
        guarded = self._guard(operation_key, case_serial, fingerprint)
        if guarded is not None:
            return guarded
        head = next((item for item in self.repurchase_queue if item.state == "queued"), None)
        if head is None or head.request_id != request_id:
            raise QueueOrderRed("repurchase queue must settle FIFO")
        grant = self._grant(request.grant_id)
        if request.units > grant.vested_units:
            raise StateTransitionRed("vested units changed before repurchase")
        cash = request.units * request.price_per_unit
        paid = self.journal.pay(
            cash,
            operation_key=f"journal:{operation_key}",
            case_serial=case_serial,
        )
        grant.vested_units -= request.units
        grant.repurchased_units += request.units
        grant.assert_conserved()
        request.state = "settled"
        request.payment_receipt_id = paid.receipt_id
        return self._commit(operation_key, fingerprint, paid)

    def _bonus(self, award_id: str) -> BonusAward:
        try:
            return self.bonuses[award_id]
        except KeyError as exc:
            raise StateTransitionRed(f"unknown bonus {award_id}") from exc

    def _statement(self, statement_id: str) -> PayStatement:
        try:
            return self.statements[statement_id]
        except KeyError as exc:
            raise StateTransitionRed(f"unknown pay statement {statement_id}") from exc

    def _grant(self, grant_id: str) -> "LTIGrant":
        try:
            return self.lti_grants[grant_id]
        except KeyError as exc:
            raise StateTransitionRed(f"unknown LTI grant {grant_id}") from exc

    def _request(self, request_id: str) -> "RepurchaseRequest":
        try:
            return next(item for item in self.repurchase_queue if item.request_id == request_id)
        except StopIteration as exc:
            raise StateTransitionRed(f"unknown repurchase request {request_id}") from exc


def retention_cliff_gap(last_vest_day: int, next_grant_day: int | None) -> int | None:
    if last_vest_day < 0:
        raise InvalidInputRed("last vest day must be non-negative")
    if next_grant_day is None:
        return None
    if next_grant_day < 0:
        raise InvalidInputRed("next grant day must be non-negative")
    return max(0, next_grant_day - last_vest_day)


def pay_band_position(salary: int, band_min: int, band_max: int) -> int:
    _require_nonnegative("salary", salary)
    _require_nonnegative("band_min", band_min)
    _require_positive("band_max", band_max)
    if band_min >= band_max:
        raise InvalidInputRed("pay band maximum must exceed minimum")
    return ((salary - band_min) * FULL_BPS) // (band_max - band_min)


@dataclass(frozen=True)
class RaiseCandidate:
    candidate_id: str
    rating: int
    requested: int
    market_need: int = 0
    merit: int = 0
    fairness_debt: int = 0
    scarcity: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative("requested raise", self.requested)
        for name in ("market_need", "merit", "fairness_debt", "scarcity"):
            _require_nonnegative(name, getattr(self, name))

    @property
    def score(self) -> int:
        return self.fairness_debt * 4 + self.market_need * 3 + self.merit * 2 + self.scarcity


def allocate_raise_pool(
    candidates: Sequence[RaiseCandidate], pool: int
) -> dict[str, int]:
    _require_nonnegative("raise pool", pool)
    if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
        raise InvalidInputRed("raise candidate IDs must be unique")
    allocations = {candidate.candidate_id: 0 for candidate in candidates}
    remaining = pool
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.candidate_id)):
        grant = min(candidate.requested, remaining)
        allocations[candidate.candidate_id] = grant
        remaining -= grant
    if sum(allocations.values()) > pool:
        raise ConservationRed("raise allocation exceeded the pool")
    return allocations


@dataclass(frozen=True)
class CareerPackage:
    grade_level: int
    appointment: str | None
    authority: int
    cash_raise: int

    def __post_init__(self) -> None:
        _require_nonnegative("grade level", self.grade_level)
        _require_nonnegative("authority", self.authority)
        _require_nonnegative("cash raise", self.cash_raise)


def separate_award_accounts(tenure_award: int, performance_award: int) -> dict[str, int]:
    _require_nonnegative("tenure award", tenure_award)
    _require_nonnegative("performance award", performance_award)
    return {
        "tenure": tenure_award,
        "performance": performance_award,
        "total": tenure_award + performance_award,
    }


class ExtraMonthKind(str, Enum):
    FIXED = "fixed"
    PERFORMANCE = "performance"
    DISCRETIONARY = "discretionary"


@dataclass(frozen=True)
class ExtraMonthContract:
    amount: int
    kind: ExtraMonthKind
    locked_cycle: int

    def __post_init__(self) -> None:
        _require_nonnegative("extra month amount", self.amount)
        _require_positive("locked cycle", self.locked_cycle)

    def earned(self, *, performance_met: bool, discretion_granted: bool) -> int:
        if self.kind is ExtraMonthKind.FIXED:
            return self.amount
        if self.kind is ExtraMonthKind.PERFORMANCE:
            return self.amount if performance_met else 0
        return self.amount if discretion_granted else 0

    def reclassify(self, kind: ExtraMonthKind) -> "ExtraMonthContract":
        if kind is not self.kind:
            raise FormulaLockedRed("extra-month contract cannot be renamed after lock")
        return self


class ProrationRule(str, Enum):
    SERVICE_MONTHS = "service-months"
    MILESTONE = "milestone"
    FULL_CYCLE = "full-cycle"


def prorate_award(
    amount: int,
    *,
    rule: ProrationRule,
    service_months: int,
    milestone_bps: int = 0,
) -> int:
    _require_nonnegative("award amount", amount)
    if not 0 <= service_months <= 12:
        raise InvalidInputRed("service months must be between 0 and 12")
    if not 0 <= milestone_bps <= FULL_BPS:
        raise InvalidInputRed("milestone completion must be 0..10000 bps")
    if rule is ProrationRule.SERVICE_MONTHS:
        return (amount * service_months + 6) // 12
    if rule is ProrationRule.MILESTONE:
        return multiply_bps(amount, milestone_bps)
    return amount if service_months == 12 else 0


@dataclass(frozen=True)
class DryPromotionCommitment:
    responsibility_cycle: int
    cash_due_cycle: int
    cash_raise: int

    def __post_init__(self) -> None:
        _require_positive("responsibility cycle", self.responsibility_cycle)
        if self.cash_due_cycle < self.responsibility_cycle:
            raise InvalidInputRed("cash due cycle cannot precede responsibility")
        _require_nonnegative("cash raise", self.cash_raise)

    def overdue(self, current_cycle: int, paid: bool) -> bool:
        return not paid and current_cycle > self.cash_due_cycle


def demotion_pay_schedule(
    current_pay: int,
    target_pay: int,
    *,
    steps: int,
    preserve_professional_pay: bool = False,
) -> tuple[int, ...]:
    _require_nonnegative("current pay", current_pay)
    _require_nonnegative("target pay", target_pay)
    if target_pay > current_pay or steps < 1:
        raise InvalidInputRed("demotion schedule needs lower target and positive steps")
    if preserve_professional_pay:
        return (current_pay,)
    reduction = current_pay - target_pay
    schedule = tuple(current_pay - (reduction * step // steps) for step in range(1, steps + 1))
    return schedule[:-1] + (target_pay,)


@dataclass(frozen=True)
class BandCorrection:
    fixed_raise: int
    one_time_bonus: int
    exception_expires_cycle: int | None


def band_correction(
    salary: int,
    band_min: int,
    band_max: int,
    *,
    current_cycle: int,
    allow_temporary_exception: bool = False,
) -> BandCorrection:
    position = pay_band_position(salary, band_min, band_max)
    if position < 0:
        return BandCorrection(band_min - salary, 0, None)
    if position > FULL_BPS:
        expiry = current_cycle + 1 if allow_temporary_exception else None
        return BandCorrection(0, max(0, salary - band_max), expiry)
    return BandCorrection(0, 0, None)


class PayVisibility(str, Enum):
    SECRET = "secret"
    BAND = "band"
    ANONYMOUS = "anonymous"


def pay_visibility(
    mode: PayVisibility,
    *,
    own_salary: int,
    band_min: int,
    band_max: int,
    anonymous_distribution: Sequence[int] = (),
) -> dict[str, object]:
    result: dict[str, object] = {"own_salary": own_salary}
    if mode in (PayVisibility.BAND, PayVisibility.ANONYMOUS):
        result["band"] = (band_min, band_max)
        result["position_bps"] = pay_band_position(own_salary, band_min, band_max)
    if mode is PayVisibility.ANONYMOUS:
        result["anonymous_distribution"] = tuple(sorted(anonymous_distribution))
    return result


def repair_pay_inversion(
    incumbent_salary: int,
    newcomer_salary: int,
    *,
    scarce_allowance: int = 0,
) -> int:
    _require_nonnegative("incumbent salary", incumbent_salary)
    _require_nonnegative("newcomer salary", newcomer_salary)
    _require_nonnegative("scarce allowance", scarce_allowance)
    explained_newcomer = max(0, newcomer_salary - scarce_allowance)
    return max(0, explained_newcomer - incumbent_salary)


@dataclass(frozen=True)
class LTINomination:
    candidate_id: str
    requested_units: int
    consecutive_performance: int
    critical_role: int
    potential: int
    retention_risk: int
    rating: int

    def __post_init__(self) -> None:
        _require_nonnegative("requested units", self.requested_units)

    @property
    def score(self) -> int:
        return (
            self.consecutive_performance * 4
            + self.critical_role * 3
            + self.potential * 2
            + self.retention_risk
        )


def select_lti_nominations(
    nominations: Sequence[LTINomination], unit_pool: int
) -> dict[str, int]:
    _require_nonnegative("LTI unit pool", unit_pool)
    selected = {nomination.candidate_id: 0 for nomination in nominations}
    remaining = unit_pool
    for nomination in sorted(nominations, key=lambda item: (-item.score, item.candidate_id)):
        # A top rating makes a candidate eligible, never automatically entitled.
        if nomination.rating < 350:
            continue
        units = min(nomination.requested_units, remaining)
        selected[nomination.candidate_id] = units
        remaining -= units
    if sum(selected.values()) > unit_pool:
        raise ConservationRed("LTI nomination pool was over-allocated")
    return selected


class GrantMeasure(str, Enum):
    FIXED_UNITS = "fixed-units"
    FIXED_VALUE = "fixed-value"


def grant_units(
    mode: GrantMeasure,
    *,
    fixed_units: int = 0,
    grant_value: int = 0,
    grant_price: int = 1,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    _require_positive("grant price", grant_price)
    _require_nonnegative("fixed units", fixed_units)
    _require_nonnegative("grant value", grant_value)
    units = fixed_units if mode is GrantMeasure.FIXED_UNITS else grant_value // grant_price
    units = max(minimum, units)
    if maximum is not None:
        _require_nonnegative("maximum units", maximum)
        units = min(units, maximum)
    return units


class RiskAward(str, Enum):
    OPTION = "option"
    RESTRICTED_UNIT = "restricted-unit"
    CASH = "cash"


@dataclass(frozen=True)
class RiskAwardChoice:
    kind: RiskAward
    units: int
    cash: int
    can_expire_worthless: bool


def risk_award_choice(kind: RiskAward, *, units: int, cash_alternative: int) -> RiskAwardChoice:
    _require_nonnegative("units", units)
    _require_nonnegative("cash alternative", cash_alternative)
    if kind is RiskAward.CASH:
        return RiskAwardChoice(kind, 0, cash_alternative, False)
    return RiskAwardChoice(kind, units, 0, kind is RiskAward.OPTION)


@dataclass(frozen=True)
class BonusConversion:
    cash_remaining: int
    converted_cash: int
    units: int


def convert_bonus_to_units(
    cash_bonus: int,
    conversion_bps: int,
    unit_price: int,
    *,
    voluntary: bool,
) -> BonusConversion:
    _require_nonnegative("cash bonus", cash_bonus)
    if not 0 <= conversion_bps <= FULL_BPS:
        raise InvalidInputRed("conversion bps must be 0..10000")
    _require_positive("unit price", unit_price)
    if conversion_bps and not voluntary:
        raise StateTransitionRed("cash-to-LTI conversion must be voluntary")
    converted = multiply_bps(cash_bonus, conversion_bps)
    return BonusConversion(cash_bonus - converted, converted, converted // unit_price)


@dataclass(frozen=True)
class ValuationColumns:
    grant_value: int
    current_value: int
    liquid_value: int


def valuation_columns(
    units: int,
    *,
    grant_price: int,
    current_price: int,
    liquidity_bps: int,
) -> ValuationColumns:
    for name, value in (
        ("units", units),
        ("grant price", grant_price),
        ("current price", current_price),
    ):
        _require_nonnegative(name, value)
    if not 0 <= liquidity_bps <= FULL_BPS:
        raise InvalidInputRed("liquidity bps must be 0..10000")
    return ValuationColumns(
        units * grant_price,
        units * current_price,
        multiply_bps(units * current_price, liquidity_bps),
    )


class LTIState(str, Enum):
    GRANTED = "granted"
    CLIFF = "cliff"
    VESTING = "vesting"
    LEAVER = "leaver"
    CLOSED = "closed"


class LeaverClass(str, Enum):
    GOOD = "good"
    BAD = "bad"


@dataclass
class LTIGrant:
    grant_id: str
    total_units: int
    grant_day: int
    cliff_days: int
    cadence_days: int
    vesting_periods: int
    service_bps: int = 5_000
    performance_bps: int = 5_000
    unvested_service: int = 0
    unvested_performance: int = 0
    vested_units: int = 0
    forfeited_units: int = 0
    repurchased_units: int = 0
    state: LTIState = LTIState.GRANTED

    def __post_init__(self) -> None:
        _require_positive("total LTI units", self.total_units)
        _require_nonnegative("grant day", self.grant_day)
        _require_nonnegative("cliff days", self.cliff_days)
        _require_positive("cadence days", self.cadence_days)
        _require_positive("vesting periods", self.vesting_periods)
        if self.service_bps + self.performance_bps != FULL_BPS:
            raise InvalidInputRed("service and performance tracks must total 10000 bps")
        if self.unvested_service == self.unvested_performance == 0:
            self.unvested_service = multiply_bps(self.total_units, self.service_bps)
            self.unvested_performance = self.total_units - self.unvested_service
        self.assert_conserved()

    def fingerprint(self) -> tuple[object, ...]:
        return (
            self.grant_id,
            self.total_units,
            self.grant_day,
            self.cliff_days,
            self.cadence_days,
            self.vesting_periods,
            self.service_bps,
            self.performance_bps,
        )

    @property
    def unvested_units(self) -> int:
        return self.unvested_service + self.unvested_performance

    def assert_conserved(self) -> None:
        accounted = (
            self.unvested_units
            + self.vested_units
            + self.forfeited_units
            + self.repurchased_units
        )
        if accounted != self.total_units:
            raise ConservationRed(
                f"LTI {self.grant_id} accounts for {accounted}, expected {self.total_units}"
            )
        if min(
            self.unvested_service,
            self.unvested_performance,
            self.vested_units,
            self.forfeited_units,
            self.repurchased_units,
        ) < 0:
            raise ConservationRed("LTI bucket became negative")

    def vest(
        self,
        *,
        as_of_day: int,
        service_active: bool,
        performance_met: bool,
        organization_met: bool,
        individual_met: bool,
    ) -> int:
        cliff_day = self.grant_day + self.cliff_days
        if as_of_day < cliff_day or self.state in (LTIState.LEAVER, LTIState.CLOSED):
            self.state = LTIState.CLIFF if as_of_day < cliff_day else self.state
            return 0
        elapsed_periods = 1 + (as_of_day - cliff_day) // self.cadence_days
        elapsed_periods = min(self.vesting_periods, elapsed_periods)
        original_service = multiply_bps(self.total_units, self.service_bps)
        original_performance = self.total_units - original_service
        service_target = original_service * elapsed_periods // self.vesting_periods
        performance_target = original_performance * elapsed_periods // self.vesting_periods
        already_vested_or_disposed_service = original_service - self.unvested_service
        already_vested_or_disposed_performance = original_performance - self.unvested_performance
        vest_service = (
            max(0, service_target - already_vested_or_disposed_service)
            if service_active
            else 0
        )
        double_gate = organization_met and individual_met
        vest_performance = (
            max(0, performance_target - already_vested_or_disposed_performance)
            if service_active and performance_met and double_gate
            else 0
        )
        vest_service = min(vest_service, self.unvested_service)
        vest_performance = min(vest_performance, self.unvested_performance)
        vested = vest_service + vest_performance
        self.unvested_service -= vest_service
        self.unvested_performance -= vest_performance
        self.vested_units += vested
        self.state = LTIState.CLOSED if self.unvested_units == 0 else LTIState.VESTING
        self.assert_conserved()
        return vested

    def classify_leaver(self, classification: LeaverClass) -> int:
        if self.state is LTIState.LEAVER:
            raise StateTransitionRed("leaver classification is already frozen")
        if classification is LeaverClass.GOOD:
            # Good leavers preserve the service portion already promised by
            # the frozen contract; only the still-contingent performance track
            # lapses.  This is deliberately different from a bad-leaver wipe.
            preserved_service = self.unvested_service
            self.unvested_service = 0
            self.vested_units += preserved_service
            forfeited = self.unvested_performance
            self.unvested_performance = 0
        else:
            forfeited = self.unvested_units
            self.unvested_service = 0
            self.unvested_performance = 0
        self.forfeited_units += forfeited
        self.state = LTIState.LEAVER
        self.assert_conserved()
        return forfeited

    def forfeit(self, track: str, amount: int) -> None:
        _require_positive("LTI forfeiture", amount)
        field_name = {
            "service": "unvested_service",
            "performance": "unvested_performance",
        }.get(track)
        if field_name is None:
            raise StateTransitionRed("LTI forfeiture needs service or performance track")
        available = getattr(self, field_name)
        if amount > available:
            raise StateTransitionRed("LTI forfeiture exceeds the unvested track")
        setattr(self, field_name, available - amount)
        self.forfeited_units += amount
        self.assert_conserved()


@dataclass
class RepurchaseRequest:
    request_id: str
    grant_id: str
    units: int
    price_per_unit: int
    state: str = "queued"
    payment_receipt_id: str | None = None


def validate_mechanism_coverage() -> None:
    expected = set(range(82, 92)) | set(range(278, 301))
    if set(MECHANISM_BEHAVIORS) != expected:
        raise ConservationRed("compensation mechanism map is not exact")
    if len({row.behavior for row in MECHANISM_BEHAVIORS.values()}) < 25:
        raise ConservationRed("mechanism behavior map collapsed too many semantics")


validate_mechanism_coverage()
