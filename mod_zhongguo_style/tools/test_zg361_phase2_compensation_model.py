#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 tests for the phase-two 361 compensation model."""

from __future__ import annotations

import copy
import unittest

from zg361_phase2_compensation_model import (
    AppealTrackRed,
    BandCorrection,
    BonusFormula,
    BonusState,
    CareerPackage,
    CompensationKernel,
    CompensationRouteLedger,
    ConservationRed,
    DecisionIdentity,
    Disposition,
    DryPromotionCommitment,
    ExtraMonthContract,
    ExtraMonthKind,
    FormulaLockedRed,
    FundingSplit,
    FundingAction,
    FutureSerialRed,
    GrantMeasure,
    IdempotencyConflictRed,
    InsufficientFundsRed,
    InvalidInputRed,
    LTIGrant,
    LTINomination,
    LeaverClass,
    MECHANISM_BEHAVIORS,
    MECHANISM_EXPECTED_STATES,
    MECHANISM_ROUTE_OUTCOMES,
    NO_OBJECT_ROUTE3_IDS,
    PayVisibility,
    ProrationRule,
    QueueOrderRed,
    RaiseCandidate,
    ReceiptKind,
    ReceiptLimitRed,
    RiskAward,
    StateTransitionRed,
    TransactionJournal,
    WalletBook,
    allocate_raise_pool,
    band_correction,
    convert_bonus_to_units,
    demotion_pay_schedule,
    grant_units,
    pay_band_position,
    pay_visibility,
    prorate_award,
    repair_pay_inversion,
    retention_cliff_gap,
    risk_award_choice,
    select_lti_nominations,
    separate_award_accounts,
    three_factor_bonus,
    total_reward_quote,
    valuation_columns,
    validate_mechanism_coverage,
)


class CompensationMechanismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel = CompensationKernel(
            treasury_gold=20_000,
            manager_gold=10_000,
            split=FundingSplit(7_000, 3_000),
        )

    def _grant_bonus(self, award_id: str = "bonus-1") -> None:
        formula = BonusFormula(
            base=1_000,
            realm_bps=10_000,
            team_bps=10_000,
            individual_bps=10_000,
        )
        self.kernel.lock_bonus_formula(
            award_id, formula, operation_key=f"{award_id}:lock", case_serial=1
        )
        self.kernel.reserve_bonus(
            award_id, operation_key=f"{award_id}:reserve", case_serial=1
        )
        self.kernel.grant_bonus(
            award_id, operation_key=f"{award_id}:grant", case_serial=1
        )

    def _create_statement(self, statement_id: str = "pay-1") -> None:
        self.kernel.create_pay_statement(
            statement_id,
            {"fixed": 80, "performance": 20},
            due_day=30,
            performance_grade=350,
            operation_key=f"{statement_id}:create",
            case_serial=1,
        )

    @staticmethod
    def _route_kwargs(outcome: object) -> dict[str, int]:
        return {"gross_override": 20} if getattr(outcome, "dynamic_gross") else {}

    def _create_lti(
        self,
        grant_id: str = "lti-1",
        *,
        cliff_days: int = 365,
        cadence_days: int = 90,
        periods: int = 4,
    ) -> LTIGrant:
        grant = LTIGrant(
            grant_id=grant_id,
            total_units=1_000,
            grant_day=0,
            cliff_days=cliff_days,
            cadence_days=cadence_days,
            vesting_periods=periods,
        )
        self.kernel.create_lti_grant(
            grant, operation_key=f"{grant_id}:create", case_serial=1
        )
        return grant

    def test_exact_33_item_behavior_map(self) -> None:
        validate_mechanism_coverage()
        self.assertEqual(
            set(MECHANISM_BEHAVIORS),
            set(range(82, 92)) | set(range(278, 301)),
        )
        self.assertEqual(
            {row.domain for row in MECHANISM_BEHAVIORS.values()}, {"L", "AE", "AF"}
        )

    def test_all_33_ids_have_three_distinct_executable_route_contracts(self) -> None:
        self.assertEqual(set(MECHANISM_ROUTE_OUTCOMES), set(MECHANISM_BEHAVIORS))
        for mechanism_id, outcomes in MECHANISM_ROUTE_OUTCOMES.items():
            with self.subTest(mechanism_id=mechanism_id):
                self.assertEqual(len(outcomes), 3)
                self.assertEqual(len({item.consequence_code for item in outcomes}), 3)
                for outcome in outcomes:
                    if outcome.materializes_object:
                        self.assertTrue(outcome.resource_values)
                    else:
                        self.assertEqual(outcome.resource_values, ())

    def test_no_object_route_c_set_is_exact_and_shared_with_ck3_generator(self) -> None:
        self.assertEqual(
            NO_OBJECT_ROUTE3_IDS,
            {84, 88, 90, 282, 283, 285, 288, 293, 300},
        )

    def test_financial_route_matrix_is_explicit_not_receipt_only(self) -> None:
        expected = {
            84: (FundingAction.RESERVE, FundingAction.RESERVE, FundingAction.NONE),
            90: (FundingAction.PAYMENT, FundingAction.PAYMENT, FundingAction.NONE),
            281: (
                FundingAction.PAYMENT,
                FundingAction.DEFERRED_PAYMENT,
                FundingAction.DEFERRED_PAYMENT,
            ),
            282: (FundingAction.PAYMENT, FundingAction.OBLIGATION, FundingAction.NONE),
            283: (FundingAction.OBLIGATION, FundingAction.OBLIGATION, FundingAction.NONE),
            285: (FundingAction.OBLIGATION, FundingAction.OBLIGATION, FundingAction.NONE),
            286: (FundingAction.OBLIGATION, FundingAction.OBLIGATION, FundingAction.NONE),
            288: (FundingAction.OBLIGATION, FundingAction.OBLIGATION, FundingAction.NONE),
            289: (FundingAction.PAYMENT, FundingAction.OBLIGATION, FundingAction.NONE),
            292: (FundingAction.NONE, FundingAction.NONE, FundingAction.PAYMENT),
            293: (FundingAction.PAYMENT, FundingAction.PAYMENT, FundingAction.NONE),
            300: (
                FundingAction.PAYMENT,
                FundingAction.DEFERRED_PAYMENT,
                FundingAction.NONE,
            ),
        }
        actual = {
            mechanism_id: tuple(route.funding_action for route in outcomes)
            for mechanism_id, outcomes in MECHANISM_ROUTE_OUTCOMES.items()
            if any(route.funding_action is not FundingAction.NONE for route in outcomes)
        }
        self.assertEqual(actual, expected)

    def test_stage_routes_reconcile_quote_bonus_spot_and_conversion_resources(self) -> None:
        for route in range(3):
            quote = dict(MECHANISM_ROUTE_OUTCOMES[82][route].resource_values)["total_reward"]
            bonus = dict(MECHANISM_ROUTE_OUTCOMES[83][route].resource_values)["computed_bonus"]
            spot_outcome = MECHANISM_ROUTE_OUTCOMES[90][route]
            spot = (
                dict(spot_outcome.resource_values)["spot_paid"]
                if spot_outcome.materializes_object
                else 0
            )
            self.assertEqual(quote, 15 + bonus + spot)
            grant = MECHANISM_ROUTE_OUTCOMES[84][route]
            if grant.materializes_object:
                self.assertEqual(grant.gross, bonus)
            else:
                self.assertEqual(bonus, 0)
            award_accounts = dict(
                MECHANISM_ROUTE_OUTCOMES[91][route].resource_values
            )["award_total"]
            self.assertEqual(award_accounts, spot)

        converted = dict(MECHANISM_ROUTE_OUTCOMES[293][0].resource_values)
        self.assertEqual(converted["conversion_units"] + MECHANISM_ROUTE_OUTCOMES[293][0].gross, 10)
        self.assertEqual(MECHANISM_ROUTE_OUTCOMES[293][1].gross, 10)
        self.assertFalse(MECHANISM_ROUTE_OUTCOMES[293][2].materializes_object)

    def test_all_99_routes_freeze_identity_or_explicitly_record_no_object(self) -> None:
        for mechanism_id, outcomes in MECHANISM_ROUTE_OUTCOMES.items():
            identity = DecisionIdentity(
                "manager", "subject", 7, 1, MECHANISM_EXPECTED_STATES[mechanism_id]
            )
            for route, outcome in enumerate(outcomes, 1):
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    ledger = CompensationRouteLedger(
                        treasury_gold=10_000, manager_gold=10_000
                    )
                    result = ledger.apply(
                        mechanism_id,
                        route,
                        identity,
                        operation_key=f"m{mechanism_id:03d}:r{route}",
                        **self._route_kwargs(outcome),
                    )
                    self.assertEqual(result.disposition, Disposition.APPLIED)
                    if outcome.materializes_object:
                        obj = ledger.objects[result.detail]
                        self.assertEqual(obj.identity, identity)
                        self.assertEqual(obj.route, route)
                        self.assertEqual(obj.consequence_code, outcome.consequence_code)
                        self.assertEqual(obj.resource_values, outcome.resource_values)
                        self.assertTrue(obj.visible)
                        for resource, value in outcome.resource_values:
                            self.assertEqual(ledger.resource_totals[resource], value)
                    else:
                        self.assertEqual(ledger.objects, {})
                        self.assertTrue(result.detail.endswith(":no-object"))

    def test_route_object_duplicate_stale_and_changed_replay_are_bounded(self) -> None:
        identity = DecisionIdentity("manager", "subject", 7, 1, 4)
        ledger = CompensationRouteLedger(treasury_gold=100, manager_gold=100)
        first = ledger.apply(90, 1, identity, operation_key="spot-route")
        frozen_wallets = copy.deepcopy(ledger.wallets)
        repeated = ledger.apply(90, 1, identity, operation_key="spot-route")
        self.assertEqual(first.disposition, Disposition.APPLIED)
        self.assertEqual(repeated.disposition, Disposition.IDEMPOTENT_NOOP)
        self.assertEqual(ledger.wallets, frozen_wallets)
        frozen_resources = copy.deepcopy(ledger.resource_totals)
        frozen_obligations = copy.deepcopy(ledger.obligations)
        with self.assertRaises(IdempotencyConflictRed):
            ledger.apply(90, 2, identity, operation_key="spot-route")
        self.assertEqual(ledger.resource_totals, frozen_resources)
        self.assertEqual(ledger.obligations, frozen_obligations)

        for mechanism_id in MECHANISM_ROUTE_OUTCOMES:
            stale_ledger = CompensationRouteLedger(
                treasury_gold=100, manager_gold=100, case_serial=1
            )
            stale_ledger.advance_case_serial(2)
            stale = stale_ledger.apply(
                mechanism_id,
                1,
                DecisionIdentity(
                    "manager", "subject", 7, 1, MECHANISM_EXPECTED_STATES[mechanism_id]
                ),
                operation_key=f"stale:{mechanism_id}",
                **self._route_kwargs(MECHANISM_ROUTE_OUTCOMES[mechanism_id][0]),
            )
            self.assertEqual(stale.disposition, Disposition.STALE_NOOP)
            self.assertEqual(stale_ledger.objects, {})
            self.assertEqual(stale_ledger.journal.receipts, {})
            self.assertEqual(stale_ledger.resource_totals, {})
            self.assertEqual(stale_ledger.obligations, {})

    def test_every_id_rejects_a_valid_case_serial_in_the_wrong_stage(self) -> None:
        for mechanism_id, expected_state in MECHANISM_EXPECTED_STATES.items():
            wrong_state = 1 if expected_state != 1 else 2
            ledger = CompensationRouteLedger(treasury_gold=100, manager_gold=100)
            with self.subTest(mechanism_id=mechanism_id):
                with self.assertRaises(StateTransitionRed):
                    ledger.apply(
                        mechanism_id,
                        1,
                        DecisionIdentity("manager", "subject", 7, 1, wrong_state),
                        operation_key=f"wrong-state:{mechanism_id}",
                    )
                self.assertEqual(ledger.objects, {})
                self.assertEqual(ledger.resource_totals, {})
                self.assertEqual(ledger.journal.receipts, {})

    def test_all_cash_routes_freeze_two_real_payers_and_pending_debt_settles_atomically(self) -> None:
        for mechanism_id, outcomes in MECHANISM_ROUTE_OUTCOMES.items():
            identity = DecisionIdentity(
                "manager", "subject", 7, 1, MECHANISM_EXPECTED_STATES[mechanism_id]
            )
            for route, outcome in enumerate(outcomes, 1):
                if outcome.funding_action is FundingAction.NONE:
                    continue
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    ledger = CompensationRouteLedger(
                        treasury_gold=1_000, manager_gold=1_000
                    )
                    result = ledger.apply(
                        mechanism_id,
                        route,
                        identity,
                        operation_key=f"financial:{mechanism_id}:{route}",
                        **self._route_kwargs(outcome),
                    )
                    obj = ledger.objects[result.detail]
                    self.assertGreaterEqual(obj.frozen_treasury, 1)
                    self.assertGreaterEqual(obj.frozen_manager, 1)
                    expected_gross = 20 if outcome.dynamic_gross else outcome.gross
                    self.assertEqual(
                        obj.frozen_treasury + obj.frozen_manager, obj.frozen_gross
                    )
                    self.assertEqual(obj.frozen_gross, expected_gross)
                    if outcome.funding_action in (
                        FundingAction.OBLIGATION,
                        FundingAction.DEFERRED_PAYMENT,
                    ):
                        self.assertEqual(ledger.wallets, WalletBook(1_000, 1_000, 0))
                        self.assertEqual(ledger.obligations[result.detail], expected_gross)
                        if outcome.funding_action is FundingAction.OBLIGATION:
                            paid = ledger.settle_obligation(
                                result.detail,
                                operation_key=f"settle:{mechanism_id}:{route}",
                            )
                        else:
                            paid = ledger.settle_deferred_payment(
                                result.detail,
                                operation_key=f"settle:{mechanism_id}:{route}",
                            )
                        self.assertEqual(paid.disposition, Disposition.APPLIED)
                        self.assertEqual(ledger.obligations[result.detail], 0)
                        self.assertEqual(ledger.wallets.recipient_gold, expected_gross)
                        settled_wallets = copy.deepcopy(ledger.wallets)
                        if outcome.funding_action is FundingAction.OBLIGATION:
                            repeated = ledger.settle_obligation(
                                result.detail,
                                operation_key=f"settle:{mechanism_id}:{route}",
                            )
                            changed_call = ledger.settle_obligation
                        else:
                            repeated = ledger.settle_deferred_payment(
                                result.detail,
                                operation_key=f"settle:{mechanism_id}:{route}",
                            )
                            changed_call = ledger.settle_deferred_payment
                        self.assertEqual(repeated.disposition, Disposition.IDEMPOTENT_NOOP)
                        self.assertEqual(ledger.wallets, settled_wallets)
                        with self.assertRaises(IdempotencyConflictRed):
                            changed_call(
                                result.detail,
                                operation_key=f"changed:{mechanism_id}:{route}",
                            )
                        self.assertEqual(ledger.wallets, settled_wallets)
                    elif outcome.funding_action is FundingAction.PAYMENT:
                        self.assertEqual(ledger.wallets.recipient_gold, expected_gross)
                    else:
                        self.assertEqual(outcome.funding_action, FundingAction.RESERVE)
                        self.assertEqual(ledger.wallets.recipient_gold, 0)
                    ledger.journal.assert_conserved()

    def test_deferred_consumer_is_atomic_when_personal_payer_becomes_short(self) -> None:
        ledger = CompensationRouteLedger(treasury_gold=100, manager_gold=100)
        result = ledger.apply(
            300,
            2,
            DecisionIdentity("manager", "subject", 7, 1, 5),
            operation_key="buyback:queue",
        )
        ledger.wallets.manager_gold = 0
        before = copy.deepcopy(ledger.wallets)
        with self.assertRaises(InsufficientFundsRed):
            ledger.settle_deferred_payment(result.detail, operation_key="buyback:due")
        self.assertEqual(ledger.wallets, before)
        self.assertEqual(ledger.obligations[result.detail], 10)
        self.assertEqual(ledger.journal.receipts, {})

    def test_statement_due_route_requires_and_freezes_the_runtime_amount(self) -> None:
        identity = DecisionIdentity("manager", "subject", 7, 1, 2)
        ledger = CompensationRouteLedger(treasury_gold=100, manager_gold=100)
        with self.assertRaises(InvalidInputRed):
            ledger.apply(281, 2, identity, operation_key="statement:defer")
        self.assertEqual(ledger.objects, {})
        first = ledger.apply(
            281,
            2,
            identity,
            operation_key="statement:defer",
            gross_override=23,
        )
        obj = ledger.objects[first.detail]
        self.assertEqual(
            (obj.frozen_gross, obj.frozen_treasury, obj.frozen_manager),
            (23, 16, 7),
        )
        repeated = ledger.apply(
            281,
            2,
            identity,
            operation_key="statement:defer",
            gross_override=23,
        )
        self.assertEqual(repeated.disposition, Disposition.IDEMPOTENT_NOOP)
        with self.assertRaises(IdempotencyConflictRed):
            ledger.apply(
                281,
                2,
                identity,
                operation_key="statement:defer",
                gross_override=24,
            )

    def test_every_immediate_cash_route_is_atomic_when_either_payer_is_short(self) -> None:
        for mechanism_id, outcomes in MECHANISM_ROUTE_OUTCOMES.items():
            identity = DecisionIdentity(
                "manager", "subject", 7, 1, MECHANISM_EXPECTED_STATES[mechanism_id]
            )
            for route, outcome in enumerate(outcomes, 1):
                if outcome.funding_action not in (
                    FundingAction.RESERVE,
                    FundingAction.PAYMENT,
                ):
                    continue
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    expected_gross = 20 if outcome.dynamic_gross else outcome.gross
                    ledger = CompensationRouteLedger(
                        treasury_gold=expected_gross,
                        manager_gold=0,
                    )
                    before = copy.deepcopy(ledger.wallets)
                    with self.assertRaises(InsufficientFundsRed):
                        ledger.apply(
                            mechanism_id,
                            route,
                            identity,
                            operation_key=f"negative:{mechanism_id}:{route}",
                            **self._route_kwargs(outcome),
                        )
                    self.assertEqual(ledger.wallets, before)
                    self.assertEqual(ledger.objects, {})
                    self.assertEqual(ledger.journal.receipts, {})

    def test_bonus_route_reserve_has_exact_settlement_and_refund_consumers(self) -> None:
        ledger = CompensationRouteLedger(treasury_gold=100, manager_gold=100)
        result = ledger.apply(
            84,
            1,
            DecisionIdentity("manager", "subject", 7, 1, 1),
            operation_key="bonus:reserve",
        )
        obj = ledger.objects[result.detail]
        self.assertEqual(
            (obj.frozen_gross, obj.frozen_treasury, obj.frozen_manager),
            (20, 14, 6),
        )
        ledger.settle_reservation(result.detail, 14, operation_key="bonus:settle")
        ledger.refund_reservation(result.detail, 6, operation_key="bonus:refund")
        self.assertEqual((obj.settled, obj.refunded), (14, 6))
        self.assertEqual(ledger.wallets.recipient_gold, 14)
        self.assertEqual(
            ledger.wallets.treasury_gold
            + ledger.wallets.manager_gold
            + ledger.wallets.recipient_gold,
            200,
        )
        ledger.journal.assert_conserved()

    def test_082_total_reward_formula_keeps_components_visible(self) -> None:
        quote = total_reward_quote(
            fixed_pay=100,
            role_allowance=20,
            performance_bonus=30,
            spot_award=5,
            deferred_award=15,
        )
        self.assertEqual(quote.total, 170)
        self.assertEqual(quote.components["deferred_award"], 15)
        self.assertEqual(MECHANISM_BEHAVIORS[82].behavior, "total_reward_quote")

    def test_083_three_level_bonus_multiplies_all_three_frozen_factors(self) -> None:
        self.assertEqual(
            three_factor_bonus(
                1_000, realm_bps=8_000, team_bps=12_000, individual_bps=11_000
            ),
            1_056,
        )

    def test_084_bonus_formula_reserve_grant_and_deferred_bucket(self) -> None:
        self._grant_bonus()
        award = self.kernel.bonuses["bonus-1"]
        self.assertEqual(award.state, BonusState.GRANTED)
        self.assertEqual(
            (award.immediate_owed, award.deferred_owed, award.held),
            (700, 200, 100),
        )
        award.assert_conserved()

    def test_085_refresh_gap_is_explicit_instead_of_an_oral_promise(self) -> None:
        self.assertEqual(retention_cliff_gap(1_000, 1_090), 90)
        self.assertEqual(retention_cliff_gap(1_000, 900), 0)
        self.assertIsNone(retention_cliff_gap(1_000, None))

    def test_086_holdback_and_clawback_are_receipt_bounded(self) -> None:
        self._grant_bonus()
        self.kernel.hold_bonus(
            "bonus-1", 50, operation_key="bonus:hold", case_serial=1
        )
        paid = self.kernel.settle_bonus(
            "bonus-1", "immediate", 100, operation_key="bonus:pay", case_serial=1
        )
        self.kernel.clawback_bonus(
            "bonus-1",
            paid.receipt_id or "",
            40,
            operation_key="bonus:clawback",
            case_serial=1,
        )
        award = self.kernel.bonuses["bonus-1"]
        self.assertEqual((award.held, award.returned, award.forfeited), (150, 40, 40))
        award.assert_conserved()
        with self.assertRaises(ReceiptLimitRed):
            self.kernel.journal.return_paid(
                paid.receipt_id or "",
                61,
                operation_key="bonus:too-much",
                case_serial=1,
            )

    def test_087_pay_band_position_distinguishes_below_inside_and_above(self) -> None:
        self.assertLess(pay_band_position(80, 100, 200), 0)
        self.assertEqual(pay_band_position(150, 100, 200), 5_000)
        self.assertGreater(pay_band_position(220, 100, 200), 10_000)

    def test_088_market_merit_and_fairness_compete_for_one_conserved_pool(self) -> None:
        allocations = allocate_raise_pool(
            (
                RaiseCandidate("market", 350, 70, market_need=10),
                RaiseCandidate("merit", 375, 70, merit=10),
                RaiseCandidate("fairness", 350, 70, fairness_debt=10),
            ),
            100,
        )
        self.assertEqual(sum(allocations.values()), 100)
        self.assertEqual(allocations["fairness"], 70)

    def test_089_grade_appointment_authority_and_cash_do_not_impersonate_each_other(self) -> None:
        package = CareerPackage(grade_level=4, appointment=None, authority=2, cash_raise=0)
        self.assertEqual(package.grade_level, 4)
        self.assertIsNone(package.appointment)
        self.assertEqual(package.cash_raise, 0)

    def test_090_spot_award_uses_dual_funded_cash_receipt(self) -> None:
        before = copy.deepcopy(self.kernel.wallets)
        result = self.kernel.pay_spot_award(
            100, operation_key="spot:1", case_serial=1
        )
        receipt = self.kernel.journal.receipts[result.receipt_id or ""]
        self.assertEqual(receipt.kind, ReceiptKind.PAYMENT)
        self.assertEqual(
            (before.treasury_gold - self.kernel.wallets.treasury_gold,
             before.manager_gold - self.kernel.wallets.manager_gold),
            (70, 30),
        )
        self.assertEqual(self.kernel.wallets.recipient_gold, 100)

    def test_091_tenure_and_performance_awards_stay_separate(self) -> None:
        accounts = separate_award_accounts(40, 60)
        self.assertEqual(accounts, {"tenure": 40, "performance": 60, "total": 100})

    def test_278_statement_reconciles_payable_paid_owed_and_returned(self) -> None:
        self._create_statement()
        paid = self.kernel.pay_statement(
            "pay-1", 60, operation_key="pay:60", case_serial=1
        )
        self.kernel.return_statement_payment(
            "pay-1",
            paid.receipt_id or "",
            10,
            operation_key="pay:return10",
            case_serial=1,
        )
        statement = self.kernel.statements["pay-1"]
        self.assertEqual((statement.payable, statement.paid, statement.owed, statement.returned), (100, 60, 50, 10))
        self.assertEqual(statement.payable, statement.paid + statement.owed - statement.returned)

    def test_279_extra_month_contract_cannot_be_renamed_at_year_end(self) -> None:
        contract = ExtraMonthContract(100, ExtraMonthKind.FIXED, 1)
        self.assertEqual(contract.earned(performance_met=False, discretion_granted=False), 100)
        with self.assertRaises(FormulaLockedRed):
            contract.reclassify(ExtraMonthKind.DISCRETIONARY)

    def test_280_midyear_proration_rule_is_deterministic(self) -> None:
        self.assertEqual(
            prorate_award(1_200, rule=ProrationRule.SERVICE_MONTHS, service_months=6),
            600,
        )
        self.assertEqual(
            prorate_award(
                1_200,
                rule=ProrationRule.MILESTONE,
                service_months=6,
                milestone_bps=7_500,
            ),
            900,
        )
        self.assertEqual(
            prorate_award(1_200, rule=ProrationRule.FULL_CYCLE, service_months=11),
            0,
        )

    def test_281_each_payment_deferral_has_a_date_and_increasing_credit_cost(self) -> None:
        self._create_statement()
        self.kernel.defer_statement(
            "pay-1", 60, operation_key="defer:1", case_serial=1
        )
        self.kernel.defer_statement(
            "pay-1", 90, operation_key="defer:2", case_serial=1
        )
        statement = self.kernel.statements["pay-1"]
        self.assertEqual((statement.due_day, statement.delay_count), (90, 2))
        self.assertLess(statement.credibility, 70)

    def test_282_late_raise_creates_backpay_without_erasing_original_date(self) -> None:
        self._create_statement()
        self.kernel.apply_backpay(
            "pay-1",
            25,
            reason="raise_effective_cycle_start",
            operation_key="backpay:1",
            case_serial=1,
        )
        statement = self.kernel.statements["pay-1"]
        self.assertEqual((statement.payable, statement.owed), (125, 125))
        self.assertIn(("raise_effective_cycle_start", 25), statement.corrections)

    def test_283_dry_promotion_has_a_cash_deadline(self) -> None:
        commitment = DryPromotionCommitment(2, 3, 40)
        self.assertFalse(commitment.overdue(3, paid=False))
        self.assertTrue(commitment.overdue(4, paid=False))
        self.assertFalse(commitment.overdue(4, paid=True))

    def test_284_demotion_buffer_is_a_frozen_slope(self) -> None:
        self.assertEqual(demotion_pay_schedule(100, 60, steps=2), (80, 60))
        self.assertEqual(
            demotion_pay_schedule(100, 60, steps=2, preserve_professional_pay=True),
            (100,),
        )

    def test_285_same_rating_raise_calibration_uses_reasons_not_grade_rewrite(self) -> None:
        candidates = (
            RaiseCandidate("low-band", 375, 50, fairness_debt=10),
            RaiseCandidate("scarce", 375, 50, scarcity=10),
        )
        allocations = allocate_raise_pool(candidates, 60)
        self.assertEqual({item.rating for item in candidates}, {375})
        self.assertEqual(sum(allocations.values()), 60)
        self.assertGreater(allocations["low-band"], allocations["scarce"])

    def test_286_band_correction_catches_up_low_pay_and_freezes_high_pay(self) -> None:
        low = band_correction(80, 100, 200, current_cycle=4)
        high = band_correction(
            220, 100, 200, current_cycle=4, allow_temporary_exception=True
        )
        self.assertEqual(low, BandCorrection(20, 0, None))
        self.assertEqual(high, BandCorrection(0, 20, 5))

    def test_287_visibility_modes_never_publish_named_peer_pay(self) -> None:
        secret = pay_visibility(
            PayVisibility.SECRET, own_salary=150, band_min=100, band_max=200
        )
        anonymous = pay_visibility(
            PayVisibility.ANONYMOUS,
            own_salary=150,
            band_min=100,
            band_max=200,
            anonymous_distribution=(180, 120, 150),
        )
        self.assertEqual(secret, {"own_salary": 150})
        self.assertEqual(anonymous["anonymous_distribution"], (120, 150, 180))

    def test_288_new_hire_inversion_repair_excludes_expiring_scarcity_allowance(self) -> None:
        self.assertEqual(repair_pay_inversion(100, 140, scarce_allowance=15), 25)
        self.assertEqual(repair_pay_inversion(150, 140, scarce_allowance=0), 0)

    def test_289_compensation_appeal_changes_money_but_not_performance_grade(self) -> None:
        self._create_statement()
        self.kernel.open_appeal(
            "pay-1", "compensation", operation_key="appeal:open", case_serial=1
        )
        self.kernel.resolve_compensation_appeal(
            "pay-1", 30, operation_key="appeal:resolve", case_serial=1
        )
        statement = self.kernel.statements["pay-1"]
        self.assertEqual((statement.payable, statement.performance_grade), (130, 350))
        with self.assertRaises(AppealTrackRed):
            self.kernel.resolve_compensation_appeal(
                "pay-1", 1, operation_key="appeal:wrong-track", case_serial=1
            )

    def test_290_top_rating_is_eligibility_not_an_automatic_lti_grant(self) -> None:
        selected = select_lti_nominations(
            (
                LTINomination("critical", 80, 3, 5, 4, 5, 375),
                LTINomination("also-375", 80, 3, 1, 1, 1, 375),
                LTINomination("real-350", 80, 9, 9, 9, 9, 350),
            ),
            80,
        )
        self.assertEqual(
            selected, {"critical": 80, "also-375": 0, "real-350": 0}
        )

    def test_291_fixed_units_and_fixed_value_freeze_different_price_risk(self) -> None:
        self.assertEqual(
            grant_units(GrantMeasure.FIXED_UNITS, fixed_units=100, grant_price=7), 100
        )
        self.assertEqual(
            grant_units(GrantMeasure.FIXED_VALUE, grant_value=700, grant_price=7), 100
        )
        self.assertEqual(
            grant_units(GrantMeasure.FIXED_VALUE, grant_value=700, grant_price=14), 50
        )

    def test_292_risk_choice_distinguishes_option_rsu_and_cash(self) -> None:
        option = risk_award_choice(RiskAward.OPTION, units=100, cash_alternative=30)
        rsu = risk_award_choice(RiskAward.RESTRICTED_UNIT, units=100, cash_alternative=30)
        cash = risk_award_choice(RiskAward.CASH, units=100, cash_alternative=30)
        self.assertTrue(option.can_expire_worthless)
        self.assertFalse(rsu.can_expire_worthless)
        self.assertEqual((cash.units, cash.cash), (0, 30))

    def test_293_bonus_conversion_is_voluntary_and_conserves_cash_value(self) -> None:
        converted = convert_bonus_to_units(100, 5_000, 10, voluntary=True)
        self.assertEqual((converted.cash_remaining, converted.converted_cash, converted.units), (50, 50, 5))
        with self.assertRaises(StateTransitionRed):
            convert_bonus_to_units(100, 5_000, 10, voluntary=False)

    def test_294_grant_current_and_liquid_values_are_three_separate_columns(self) -> None:
        values = valuation_columns(
            100, grant_price=5, current_price=8, liquidity_bps=2_500
        )
        self.assertEqual((values.grant_value, values.current_value, values.liquid_value), (500, 800, 200))

    def test_295_initial_cliff_blocks_early_vesting(self) -> None:
        grant = self._create_lti(cliff_days=365)
        result = self.kernel.vest_lti(
            grant.grant_id,
            as_of_day=364,
            service_active=True,
            performance_met=True,
            organization_met=True,
            individual_met=True,
            operation_key="vest:early",
            case_serial=1,
        )
        self.assertEqual(result.value, 0)
        self.assertEqual(grant.vested_units, 0)

    def test_296_cadence_vests_only_elapsed_tranches(self) -> None:
        grant = self._create_lti(cliff_days=0, cadence_days=90, periods=4)
        first = self.kernel.vest_lti(
            grant.grant_id,
            as_of_day=0,
            service_active=True,
            performance_met=True,
            organization_met=True,
            individual_met=True,
            operation_key="vest:q1",
            case_serial=1,
        )
        second = self.kernel.vest_lti(
            grant.grant_id,
            as_of_day=90,
            service_active=True,
            performance_met=True,
            organization_met=True,
            individual_met=True,
            operation_key="vest:q2",
            case_serial=1,
        )
        self.assertEqual((first.value, second.value, grant.vested_units), (250, 250, 500))

    def test_297_service_and_performance_tracks_vest_separately(self) -> None:
        grant = self._create_lti(cliff_days=0, periods=1)
        result = self.kernel.vest_lti(
            grant.grant_id,
            as_of_day=0,
            service_active=True,
            performance_met=False,
            organization_met=True,
            individual_met=True,
            operation_key="vest:service-only",
            case_serial=1,
        )
        self.assertEqual(result.value, 500)
        self.assertEqual((grant.unvested_service, grant.unvested_performance), (0, 500))

    def test_298_organization_and_individual_gates_both_must_open(self) -> None:
        grant = self._create_lti(cliff_days=0, periods=1)
        result = self.kernel.vest_lti(
            grant.grant_id,
            as_of_day=0,
            service_active=True,
            performance_met=True,
            organization_met=False,
            individual_met=True,
            operation_key="vest:org-fail",
            case_serial=1,
        )
        self.assertEqual(result.value, 500)
        self.assertEqual(grant.unvested_performance, 500)

    def test_299_good_and_bad_leavers_use_frozen_facts_and_conserve_units(self) -> None:
        good = self._create_lti("good", cliff_days=0, periods=1)
        self.kernel.vest_lti(
            "good",
            as_of_day=0,
            service_active=True,
            performance_met=False,
            organization_met=True,
            individual_met=True,
            operation_key="good:vest",
            case_serial=1,
        )
        good_forfeit = self.kernel.classify_lti_leaver(
            "good", LeaverClass.GOOD, operation_key="good:leave", case_serial=1
        )
        bad = self._create_lti("bad", cliff_days=365)
        bad_forfeit = self.kernel.classify_lti_leaver(
            "bad", LeaverClass.BAD, operation_key="bad:leave", case_serial=1
        )
        self.assertEqual((good_forfeit.value, good.vested_units), (500, 500))
        self.assertEqual((bad_forfeit.value, bad.forfeited_units), (1_000, 1_000))
        good.assert_conserved()
        bad.assert_conserved()

        # Good-leaver status preserves already vested units; it does not
        # silently accelerate a still-unvested service track.
        unvested_good = self._create_lti("unvested-good", cliff_days=365)
        unvested_forfeit = self.kernel.classify_lti_leaver(
            "unvested-good",
            LeaverClass.GOOD,
            operation_key="unvested-good:leave",
            case_serial=1,
        )
        self.assertEqual(unvested_forfeit.value, 1_000)
        self.assertEqual(unvested_good.vested_units, 0)
        self.assertEqual(unvested_good.forfeited_units, 1_000)

    def test_300_repurchase_is_fifo_dual_funded_and_unit_conserving(self) -> None:
        first = self._create_lti("first", cliff_days=0, periods=1)
        second = self._create_lti("second", cliff_days=0, periods=1)
        for grant_id in ("first", "second"):
            self.kernel.vest_lti(
                grant_id,
                as_of_day=0,
                service_active=True,
                performance_met=True,
                organization_met=True,
                individual_met=True,
                operation_key=f"{grant_id}:vest",
                case_serial=1,
            )
        req1 = self.kernel.request_repurchase(
            "first",
            100,
            2,
            window_open=True,
            operation_key="repurchase:req1",
            case_serial=1,
        )
        req2 = self.kernel.request_repurchase(
            "second",
            100,
            2,
            window_open=True,
            operation_key="repurchase:req2",
            case_serial=1,
        )
        with self.assertRaises(QueueOrderRed):
            self.kernel.settle_repurchase(
                req2.detail, operation_key="repurchase:skip", case_serial=1
            )
        settled = self.kernel.settle_repurchase(
            req1.detail, operation_key="repurchase:settle1", case_serial=1
        )
        receipt = self.kernel.journal.receipts[settled.receipt_id or ""]
        self.assertEqual((receipt.treasury_debit, receipt.manager_debit), (140, 60))
        self.assertEqual((first.vested_units, first.repurchased_units), (900, 100))
        first.assert_conserved()


class CompensationInvariantTests(unittest.TestCase):
    def test_dual_payer_split_rejects_zero_side_and_non_total(self) -> None:
        with self.assertRaises(InvalidInputRed):
            FundingSplit(10_000, 0)
        with self.assertRaises(InvalidInputRed):
            FundingSplit(6_000, 3_000)

    def test_balance_precheck_is_atomic_across_both_payers(self) -> None:
        wallets = WalletBook(treasury_gold=100, manager_gold=1)
        journal = TransactionJournal(wallets, FundingSplit(5_000, 5_000), 1)
        before = copy.deepcopy(wallets)
        with self.assertRaises(InsufficientFundsRed):
            journal.pay(20, operation_key="atomic:red", case_serial=1)
        self.assertEqual(wallets, before)
        self.assertEqual(journal.receipts, {})

    def test_reservation_refund_cannot_exceed_original_unspent_receipt(self) -> None:
        journal = TransactionJournal(
            WalletBook(1_000, 1_000), FundingSplit(5_000, 5_000), 1
        )
        reserved = journal.reserve(100, operation_key="reserve", case_serial=1)
        journal.settle_reserved(
            reserved.receipt_id or "", 60, operation_key="settle", case_serial=1
        )
        with self.assertRaises(ReceiptLimitRed):
            journal.refund_reservation(
                reserved.receipt_id or "", 41, operation_key="refund:red", case_serial=1
            )
        journal.refund_reservation(
            reserved.receipt_id or "", 40, operation_key="refund:green", case_serial=1
        )
        journal.assert_conserved()

    def test_same_operation_is_idempotent_and_changed_replay_is_typed_red(self) -> None:
        kernel = CompensationKernel(treasury_gold=100, manager_gold=100)
        first = kernel.pay_spot_award(10, operation_key="spot", case_serial=1)
        balances = copy.deepcopy(kernel.wallets)
        repeated = kernel.pay_spot_award(10, operation_key="spot", case_serial=1)
        self.assertEqual(first.disposition, Disposition.APPLIED)
        self.assertEqual(repeated.disposition, Disposition.IDEMPOTENT_NOOP)
        self.assertEqual(kernel.wallets, balances)
        with self.assertRaises(IdempotencyConflictRed):
            kernel.pay_spot_award(12, operation_key="spot", case_serial=1)

    def test_old_serial_is_stale_noop_and_future_serial_is_typed_red(self) -> None:
        kernel = CompensationKernel(treasury_gold=100, manager_gold=100)
        kernel.advance_case_serial(2)
        stale = kernel.pay_spot_award(10, operation_key="stale", case_serial=1)
        self.assertEqual(stale.disposition, Disposition.STALE_NOOP)
        self.assertEqual(kernel.wallets.recipient_gold, 0)
        with self.assertRaises(FutureSerialRed):
            kernel.pay_spot_award(10, operation_key="future", case_serial=3)

    def test_formula_lock_cannot_be_rewritten_under_a_new_operation_key(self) -> None:
        kernel = CompensationKernel(treasury_gold=1_000, manager_gold=1_000)
        first = BonusFormula(100, 10_000, 10_000, 10_000)
        changed = BonusFormula(200, 10_000, 10_000, 10_000)
        kernel.lock_bonus_formula("award", first, operation_key="lock:1", case_serial=1)
        with self.assertRaises(FormulaLockedRed):
            kernel.lock_bonus_formula("award", changed, operation_key="lock:2", case_serial=1)

    def test_statement_conservation_detects_manual_drift(self) -> None:
        kernel = CompensationKernel(treasury_gold=1_000, manager_gold=1_000)
        kernel.create_pay_statement(
            "statement",
            {"fixed": 100},
            due_day=1,
            performance_grade=350,
            operation_key="statement:create",
            case_serial=1,
        )
        kernel.statements["statement"].owed -= 1
        with self.assertRaises(ConservationRed):
            kernel.statements["statement"].assert_conserved()

    def test_unpaid_correction_reduces_payable_and_owed_with_reason_receipt(self) -> None:
        kernel = CompensationKernel(treasury_gold=1_000, manager_gold=1_000)
        kernel.create_pay_statement(
            "statement",
            {"fixed": 100},
            due_day=1,
            performance_grade=350,
            operation_key="statement:create",
            case_serial=1,
        )
        kernel.cancel_unpaid_obligation(
            "statement",
            20,
            reason="duplicate_allowance_correction",
            operation_key="statement:correct",
            case_serial=1,
        )
        statement = kernel.statements["statement"]
        self.assertEqual((statement.payable, statement.owed), (80, 80))
        self.assertIn(("duplicate_allowance_correction", -20), statement.corrections)
        statement.assert_conserved()

    def test_lti_conservation_detects_manual_unit_creation(self) -> None:
        grant = LTIGrant("grant", 100, 0, 0, 30, 1)
        grant.vested_units += 1
        with self.assertRaises(ConservationRed):
            grant.assert_conserved()

    def test_lti_forfeit_moves_units_from_one_unvested_track_without_destroying_them(self) -> None:
        kernel = CompensationKernel(treasury_gold=1_000, manager_gold=1_000)
        grant = LTIGrant("grant", 100, 0, 30, 30, 2)
        kernel.create_lti_grant(
            grant,
            operation_key="grant:create",
            case_serial=1,
        )
        kernel.forfeit_lti(
            "grant",
            "performance",
            20,
            operation_key="grant:forfeit",
            case_serial=1,
        )
        self.assertEqual((grant.unvested_performance, grant.forfeited_units), (30, 20))
        grant.assert_conserved()

    def test_cash_operation_below_two_units_is_rejected_because_both_must_pay(self) -> None:
        kernel = CompensationKernel(treasury_gold=100, manager_gold=100)
        with self.assertRaises(InvalidInputRed):
            kernel.pay_spot_award(1, operation_key="too-small", case_serial=1)

    def test_unknown_bonus_transition_is_typed_red(self) -> None:
        kernel = CompensationKernel(treasury_gold=100, manager_gold=100)
        with self.assertRaises(StateTransitionRed):
            kernel.reserve_bonus("missing", operation_key="missing", case_serial=1)


if __name__ == "__main__":
    unittest.main()
