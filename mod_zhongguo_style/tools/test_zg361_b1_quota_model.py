#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit contracts for B1 reference primitives, not CK3 runtime completion."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import unittest

from zg361_b1_quota_model import (
    AgendaEntry,
    AgendaCalibrationCase,
    AgendaMode,
    AttentionLedger,
    AttentionSeatLedger,
    BandAssignment,
    BoardRecalculationReceipt,
    CaseIdentity,
    ClosedCalibrationRound,
    CK3_IMPLEMENTED,
    ClosurePhase,
    CohortMember,
    ConservationError,
    ConsensusRecord,
    DebtKind,
    DebtNotDueError,
    DebtState,
    DuplicateInputError,
    DuplicateOperationError,
    DissentRecord,
    DissentRegistry,
    EligibilityPolicy,
    EligibilityTreatment,
    EvidencePolarity,
    EvidenceSegment,
    ExecutiveMustReviewCase,
    ExecutiveReviewRegistry,
    FrozenCandidateGrade,
    IllegalStateError,
    InsufficientSlotError,
    InvalidInputError,
    LateEvidence,
    PendingResolution,
    PendingMilestoneCase,
    PendingSlotLedger,
    PolicyDecisionLedger,
    PolicyRoute,
    PostCutoffCase,
    QuotaBook,
    QuotaCounts,
    QuotaDebt,
    QuotaRoundingCase,
    RatingBand,
    READINESS,
    RedCode,
    SlotTrade,
    StaleOperationError,
    SymmetricReopenPolicy,
    ShadowBandOrderCase,
    TeamCohort,
    ThresholdNotMetError,
    TradeDebtTerms,
    apply_bilateral_slot_trade,
    apply_bilateral_slot_trade_with_debt,
    apply_roster_change,
    allocate_reorganized_subject,
    bind_attention_seat,
    build_agenda,
    compute_quota,
    consume_attention_seat,
    consume_agenda_subject,
    consume_precalibration_meeting,
    consume_post_cutoff_case,
    consume_shadow_band_order,
    hold_pending_slot,
    issue_rewards,
    lock_cohort,
    open_attention_seat_ledger,
    open_agenda_calibration_case,
    open_executive_must_review,
    open_pending_slot_ledger,
    open_pending_milestone_case,
    open_post_cutoff_case,
    open_precalibration_meeting,
    open_quota_rounding_case,
    open_reorganization_ownership_case,
    open_roster_audit,
    open_shadow_rating_case,
    open_shadow_band_order_case,
    open_dissent_case,
    pool_by_common_superior,
    request_symmetric_reopen,
    resolve_executive_must_review,
    resolve_pending_milestone_case,
    reseal_reopened_round,
    resolve_pending_slot,
    settle_due_debt,
    seal_consensus,
    spend_attention,
    submit_shadow_evidence,
    finalize_shadow_rating,
    publish_rounded_quota,
    transfer_attention_seat,
    use_overtime_attention,
    validate_dissent,
)


class ReadinessBoundaryTests(unittest.TestCase):
    def test_reference_model_does_not_claim_ck3_implementation(self) -> None:
        self.assertEqual(READINESS, "python-l0-reference-only")
        self.assertIs(CK3_IMPLEMENTED, False)


def member(
    member_id: str,
    team_id: str,
    *,
    superior_id: str = "sup",
    newcomer: bool = False,
    leaver: bool = False,
    transferred_in: bool = False,
    long_leave: bool = False,
) -> CohortMember:
    return CohortMember(
        member_id=member_id,
        team_id=team_id,
        common_superior_id=superior_id,
        newcomer=newcomer,
        leaver=leaver,
        transferred_in=transferred_in,
        long_leave=long_leave,
    )


def team(
    team_id: str,
    count: int,
    *,
    superior_id: str = "sup",
    cycle: int = 1,
    function_id: str = "default",
) -> TeamCohort:
    return TeamCohort(
        team_id=team_id,
        manager_id=f"manager-{team_id}",
        common_superior_id=superior_id,
        cycle=cycle,
        members=tuple(
            member(f"{team_id}-{index:02d}", team_id, superior_id=superior_id)
            for index in range(1, count + 1)
        ),
        function_id=function_id,
    )


class QuotaRoundingTests(unittest.TestCase):
    def test_required_cohort_sizes_have_deterministic_effective_counts(self) -> None:
        expected = {
            0: QuotaCounts(0, 0, 0),
            1: QuotaCounts(0, 1, 0),
            2: QuotaCounts(0, 2, 0),
            3: QuotaCounts(1, 2, 0),
            4: QuotaCounts(1, 3, 0),
            7: QuotaCounts(2, 4, 1),
            14: QuotaCounts(4, 9, 1),
            23: QuotaCounts(7, 14, 2),
        }
        for cohort_size, counts in expected.items():
            with self.subTest(cohort_size=cohort_size):
                result = compute_quota(cohort_size)
                self.assertEqual(result.effective_counts, counts)
                self.assertEqual(result.effective_counts.total, cohort_size)
                self.assertEqual(result.forced_distribution, cohort_size >= 3)

    def test_twenty_three_exposes_exact_raw_floor_remainder_and_awards(self) -> None:
        result = compute_quota(23)
        top = result.band(RatingBand.TOP)
        middle = result.band(RatingBand.MIDDLE)
        bottom = result.band(RatingBand.BOTTOM)
        self.assertEqual(
            (top.raw, middle.raw, bottom.raw),
            (Fraction(69, 10), Fraction(69, 5), Fraction(23, 10)),
        )
        self.assertEqual((top.floor_slots, middle.floor_slots, bottom.floor_slots), (6, 13, 2))
        self.assertEqual(
            (top.remainder, middle.remainder, bottom.remainder),
            (Fraction(9, 10), Fraction(4, 5), Fraction(3, 10)),
        )
        self.assertEqual(
            (
                top.awarded_remainder_slot,
                middle.awarded_remainder_slot,
                bottom.awarded_remainder_slot,
            ),
            (True, True, False),
        )
        self.assertEqual(result.rounded_counts, QuotaCounts(7, 14, 2))

    def test_small_cohort_neutral_rule_does_not_hide_raw_rounding(self) -> None:
        result = compute_quota(2)
        self.assertEqual(result.rounded_counts, QuotaCounts(1, 1, 0))
        self.assertEqual(result.effective_counts, QuotaCounts(0, 2, 0))
        self.assertFalse(result.forced_distribution)
        self.assertEqual(result.band(RatingBand.TOP).raw, Fraction(3, 5))

    def test_tied_remainders_use_stable_top_middle_bottom_order(self) -> None:
        result = compute_quota(4)
        self.assertEqual(
            result.band(RatingBand.MIDDLE).remainder,
            result.band(RatingBand.BOTTOM).remainder,
        )
        self.assertTrue(result.band(RatingBand.MIDDLE).awarded_remainder_slot)
        self.assertFalse(result.band(RatingBand.BOTTOM).awarded_remainder_slot)
        self.assertEqual(result.effective_counts, QuotaCounts(1, 3, 0))

    def test_maximum_remainder_is_not_the_legacy_minimum_bottom_override(self) -> None:
        self.assertEqual(compute_quota(5).effective_counts, QuotaCounts(2, 3, 0))
        self.assertEqual(compute_quota(6).effective_counts, QuotaCounts(2, 4, 0))

    def test_serializable_audit_record_is_exact_and_repeatable(self) -> None:
        first = compute_quota(23).as_dict()
        second = compute_quota(23).as_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["bands"]["3.75"]["raw"], "69/10")  # type: ignore[index]

    def test_invalid_cohort_size_is_typed_red(self) -> None:
        for value in (-1, True, 2.5):
            with self.subTest(value=value):
                with self.assertRaises(InvalidInputError) as caught:
                    compute_quota(value)  # type: ignore[arg-type]
                self.assertEqual(caught.exception.code, RedCode.INVALID_INPUT)


class EligibilityAndPoolingTests(unittest.TestCase):
    def test_default_policy_includes_protected_newcomer_and_excludes_leaver(self) -> None:
        cohort = TeamCohort(
            team_id="a",
            manager_id="manager-a",
            common_superior_id="sup",
            cycle=4,
            members=(
                member("normal", "a"),
                member("new", "a", newcomer=True),
                member("leaving", "a", leaver=True),
                member("new-leaving", "a", newcomer=True, leaver=True),
            ),
        )
        locked = lock_cohort(cohort)
        self.assertEqual(
            tuple(item.member_id for item in locked.included_members), ("new", "normal")
        )
        self.assertEqual(
            tuple(item.member_id for item in locked.bottom_eligible_members), ("normal",)
        )
        self.assertEqual(
            tuple(item.member_id for item in locked.excluded_members),
            ("leaving", "new-leaving"),
        )
        self.assertEqual(locked.quota.effective_counts, QuotaCounts(0, 2, 0))

    def test_explicit_full_policy_makes_newcomer_and_leaver_bottom_eligible(self) -> None:
        cohort = TeamCohort(
            team_id="a",
            manager_id="manager-a",
            common_superior_id="sup",
            cycle=1,
            members=(
                member("new", "a", newcomer=True),
                member("leaving", "a", leaver=True),
            ),
        )
        policy = EligibilityPolicy(
            newcomer=EligibilityTreatment.INCLUDE,
            leaver=EligibilityTreatment.INCLUDE,
        )
        locked = lock_cohort(cohort, policy)
        self.assertEqual(len(locked.included_members), 2)
        self.assertEqual(len(locked.bottom_eligible_members), 2)

    def test_explicit_newcomer_exclusion_changes_the_frozen_denominator(self) -> None:
        cohort = TeamCohort(
            team_id="a",
            manager_id="manager-a",
            common_superior_id="sup",
            cycle=1,
            members=(member("incumbent", "a"), member("new", "a", newcomer=True)),
        )
        policy = EligibilityPolicy(newcomer=EligibilityTreatment.EXCLUDE)
        locked = lock_cohort(cohort, policy)
        self.assertEqual(tuple(item.member_id for item in locked.included_members), ("incumbent",))
        self.assertEqual(locked.quota.cohort_size, 1)

    def test_join_transfer_long_leave_and_leaver_have_explicit_lock_records(self) -> None:
        cohort = TeamCohort(
            team_id="a",
            manager_id="manager-a",
            common_superior_id="sup",
            cycle=1,
            members=(
                member("join", "a", newcomer=True),
                member("transfer", "a", transferred_in=True),
                member("leave", "a", long_leave=True),
                member("leaver", "a", leaver=True),
            ),
        )
        locked = lock_cohort(cohort)
        by_id = {record.member.member_id: record for record in locked.records}
        self.assertTrue(by_id["join"].quota_eligible)
        self.assertFalse(by_id["join"].bottom_eligible)
        self.assertTrue(by_id["transfer"].quota_eligible)
        self.assertFalse(by_id["leave"].quota_eligible)
        self.assertFalse(by_id["leaver"].quota_eligible)

    def test_post_lock_status_change_gets_receipt_and_requires_atomic_reopen(self) -> None:
        cohort = TeamCohort(
            "a", "manager-a", "sup", 1, (member("official", "a"), member("other", "a"))
        )
        state = open_roster_audit(cohort)
        updated = member("official", "a", leaver=True)
        changed = apply_roster_change(
            state,
            updated,
            change_id="change-1",
            reason="formal transfer order",
            actor_id="manager-a",
            approver_id="sup",
            changed_at="cycle-1-day-20",
            operation_id="roster-op-1",
            expected_version=0,
        )
        self.assertEqual(len(state.original.included_members), 2)
        self.assertEqual(len(changed.original.included_members), 2)
        self.assertEqual(len(changed.current.included_members), 1)
        self.assertTrue(changed.calibration_reopen_required)
        self.assertEqual(changed.change_receipts[0].before.leaver, False)
        self.assertEqual(changed.change_receipts[0].after.leaver, True)
        before_failed_attempt = changed
        with self.assertRaises(StaleOperationError):
            apply_roster_change(
                changed,
                replace(updated, long_leave=True),
                change_id="change-2",
                reason="late leave update",
                actor_id="manager-a",
                approver_id="sup",
                changed_at="cycle-1-day-21",
                operation_id="roster-op-2",
                expected_version=0,
            )
        self.assertEqual(changed, before_failed_attempt)

    def test_post_lock_join_transfer_leave_and_leaver_are_receipted(self) -> None:
        state = open_roster_audit(
            TeamCohort(
                "a", "manager-a", "sup", 1, (member("official", "a"),)
            )
        )
        state = apply_roster_change(
            state,
            member("join", "a", newcomer=True),
            change_id="join-change",
            reason="post-lock join",
            actor_id="manager-a",
            approver_id="sup",
            changed_at="cycle-1-day-20",
            operation_id="join-op",
            expected_version=0,
        )
        state = apply_roster_change(
            state,
            member("transfer", "a", transferred_in=True),
            change_id="transfer-change",
            reason="post-lock transfer-in",
            actor_id="manager-a",
            approver_id="sup",
            changed_at="cycle-1-day-21",
            operation_id="transfer-op",
            expected_version=1,
        )
        state = apply_roster_change(
            state,
            member("official", "a", long_leave=True),
            change_id="leave-change",
            reason="approved long leave",
            actor_id="manager-a",
            approver_id="sup",
            changed_at="cycle-1-day-22",
            operation_id="leave-op",
            expected_version=2,
        )
        state = apply_roster_change(
            state,
            member("join", "a", newcomer=True, leaver=True),
            change_id="leaver-change",
            reason="formal departure",
            actor_id="manager-a",
            approver_id="sup",
            changed_at="cycle-1-day-23",
            operation_id="leaver-op",
            expected_version=3,
        )
        self.assertEqual(state.version, 4)
        self.assertEqual(len(state.change_receipts), 4)
        self.assertTrue(state.calibration_reopen_required)
        self.assertIsNone(state.change_receipts[0].before)
        self.assertIsNone(state.change_receipts[1].before)
        self.assertEqual(len(state.original.records), 1)
        self.assertEqual(len(state.current.records), 3)
        by_id = {record.member.member_id: record for record in state.current.records}
        self.assertFalse(by_id["official"].quota_eligible)
        self.assertFalse(by_id["join"].quota_eligible)
        self.assertTrue(by_id["transfer"].quota_eligible)

    def test_three_plus_four_common_superior_forms_one_unique_seven_person_pool(self) -> None:
        pools = pool_by_common_superior((team("a", 3), team("b", 4)))
        self.assertEqual(len(pools), 1)
        pool = pools[0]
        self.assertEqual(pool.source_team_ids, ("a", "b"))
        self.assertEqual(len(pool.included_members), 7)
        self.assertEqual(len({item.member_id for item in pool.included_members}), 7)
        self.assertEqual(pool.quota.effective_counts, QuotaCounts(2, 4, 1))

    def test_pool_id_is_order_stable_and_delimiter_safe(self) -> None:
        first = pool_by_common_superior((team("a+b", 3), team("c", 4)))[0]
        reordered = pool_by_common_superior((team("c", 4), team("a+b", 3)))[0]
        formerly_ambiguous = pool_by_common_superior(
            (team("a", 3), team("b+c", 4))
        )[0]
        self.assertEqual(first.pool_id, reordered.pool_id)
        self.assertNotEqual(first.pool_id, formerly_ambiguous.pool_id)
        self.assertTrue(first.pool_id.startswith("b1-pool-"))

    def test_different_common_superiors_cannot_form_a_shared_pool(self) -> None:
        with self.assertRaises(InvalidInputError):
            pool_by_common_superior(
                (team("a", 3, superior_id="sup-a"), team("b", 4, superior_id="sup-b"))
            )

    def test_different_functions_cannot_form_a_shared_pool(self) -> None:
        with self.assertRaises(InvalidInputError):
            pool_by_common_superior(
                (team("a", 3, function_id="civil"), team("b", 4, function_id="military"))
            )

    def test_non_small_team_cannot_enter_the_small_sample_pool(self) -> None:
        with self.assertRaises(InvalidInputError):
            pool_by_common_superior((team("a", 5), team("b", 3)))
        with self.assertRaises(InvalidInputError):
            pool_by_common_superior((team("a", 3),))

    def test_duplicate_member_across_two_teams_is_typed_red(self) -> None:
        first = TeamCohort("a", "ma", "sup", 1, (member("same", "a"),))
        second = TeamCohort("b", "mb", "sup", 1, (member("same", "b"),))
        with self.assertRaises(DuplicateInputError) as caught:
            pool_by_common_superior((first, second))
        self.assertEqual(caught.exception.code, RedCode.DUPLICATE_INPUT)

    def test_duplicate_member_within_team_and_mismatched_team_are_red(self) -> None:
        duplicate = member("same", "a")
        with self.assertRaises(DuplicateInputError):
            TeamCohort("a", "ma", "sup", 1, (duplicate, duplicate))
        with self.assertRaises(InvalidInputError):
            TeamCohort("a", "ma", "sup", 1, (member("wrong", "b"),))


class BilateralTradeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.donor = QuotaBook("a", "sup", 2, QuotaCounts(2, 4, 1))
        self.receiver = QuotaBook("b", "sup", 2, QuotaCounts(2, 4, 1))

    def trade(self, band: RatingBand = RatingBand.TOP, **changes: object) -> SlotTrade:
        values: dict[str, object] = {
            "operation_id": "trade-1",
            "donor_team_id": "a",
            "receiver_team_id": "b",
            "common_superior_id": "sup",
            "cycle": 2,
            "band": band,
            "expected_donor_version": 0,
            "expected_receiver_version": 0,
        }
        values.update(changes)
        return SlotTrade(**values)  # type: ignore[arg-type]

    def assert_global_bands_conserved(self, result: object) -> None:
        for band in (RatingBand.TOP, RatingBand.MIDDLE, RatingBand.BOTTOM):
            before = self.donor.counts[band] + self.receiver.counts[band]
            after = (
                result.donor.counts[band]  # type: ignore[attr-defined]
                + result.receiver.counts[band]  # type: ignore[attr-defined]
            )
            self.assertEqual(after, before)

    def test_exactly_one_top_slot_is_traded_bilaterally(self) -> None:
        result = apply_bilateral_slot_trade(self.donor, self.receiver, self.trade())
        self.assertEqual(result.donor.counts, QuotaCounts(1, 5, 1))
        self.assertEqual(result.receiver.counts, QuotaCounts(3, 3, 1))
        self.assertEqual((result.donor.version, result.receiver.version), (1, 1))
        self.assertEqual(result.donor_before, self.donor)
        self.assertEqual(result.receiver_before, self.receiver)
        self.assertEqual(result.donor.counts.total, self.donor.counts.total)
        self.assertEqual(result.receiver.counts.total, self.receiver.counts.total)
        self.assert_global_bands_conserved(result)

    def test_exactly_one_bottom_slot_is_traded_bilaterally(self) -> None:
        result = apply_bilateral_slot_trade(
            self.donor, self.receiver, self.trade(RatingBand.BOTTOM)
        )
        self.assertEqual(result.donor.counts, QuotaCounts(2, 5, 0))
        self.assertEqual(result.receiver.counts, QuotaCounts(2, 3, 2))
        self.assert_global_bands_conserved(result)

    def test_two_slot_and_middle_slot_requests_are_illegal_input(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.trade(slots=2)
        with self.assertRaises(InvalidInputError):
            self.trade(slots=True)
        with self.assertRaises(InvalidInputError):
            self.trade(RatingBand.MIDDLE)

    def test_duplicate_and_stale_trade_are_distinct_typed_reds(self) -> None:
        first = apply_bilateral_slot_trade(self.donor, self.receiver, self.trade())
        with self.assertRaises(DuplicateOperationError) as duplicate:
            apply_bilateral_slot_trade(first.donor, first.receiver, self.trade())
        self.assertEqual(duplicate.exception.code, RedCode.DUPLICATE_OPERATION)
        with self.assertRaises(StaleOperationError) as stale:
            apply_bilateral_slot_trade(
                replace(self.donor, version=1), self.receiver, self.trade()
            )
        self.assertEqual(stale.exception.code, RedCode.STALE_OPERATION)

    def test_trade_requires_common_superior_and_available_slots(self) -> None:
        with self.assertRaises(InvalidInputError):
            apply_bilateral_slot_trade(
                self.donor,
                replace(self.receiver, common_superior_id="other"),
                self.trade(),
            )
        with self.assertRaises(InsufficientSlotError):
            apply_bilateral_slot_trade(
                replace(self.donor, counts=QuotaCounts(0, 6, 1)),
                self.receiver,
                self.trade(),
            )
        with self.assertRaises(InsufficientSlotError):
            apply_bilateral_slot_trade(
                self.donor,
                replace(self.receiver, counts=QuotaCounts(6, 0, 1)),
                self.trade(),
            )

    def test_forged_trade_aggregate_is_typed_red_and_inputs_are_unchanged(self) -> None:
        result = apply_bilateral_slot_trade(self.donor, self.receiver, self.trade())
        donor_before = self.donor
        receiver_before = self.receiver
        with self.assertRaises(ConservationError):
            replace(
                result,
                donor=replace(result.donor, counts=self.donor.counts),
            )
        self.assertEqual(self.donor, donor_before)
        self.assertEqual(self.receiver, receiver_before)


class QuotaDebtTests(unittest.TestCase):
    def debt(self, kind: DebtKind = DebtKind.TOP_BORROWED) -> QuotaDebt:
        return QuotaDebt(
            debt_id="debt-1",
            team_id="a",
            common_superior_id="sup",
            kind=kind,
            created_cycle=1,
            due_cycle=2,
            source_trade_id="source-trade",
            creditor_team_id="creditor-team",
            creditor_manager_id="creditor-manager",
            debtor_manager_id="debtor-manager",
            approver_id="approver-manager",
            liability_id="liable-manager",
        )

    def book(self, *, cycle: int = 2, version: int = 0) -> QuotaBook:
        return QuotaBook("a", "sup", cycle, QuotaCounts(2, 4, 1), version=version)

    def settle(self, book: QuotaBook, debt: QuotaDebt, *, cycle: int = 2):
        return settle_due_debt(
            book,
            debt,
            cycle=cycle,
            operation_id="settle-1",
            expected_book_version=book.version,
        )

    def test_due_top_debt_is_settled_once_and_conserves_cohort(self) -> None:
        result = self.settle(self.book(), self.debt())
        self.assertEqual(result.book.counts, QuotaCounts(1, 5, 1))
        self.assertEqual(result.book.counts.total, 7)
        self.assertEqual(result.debt.state, DebtState.SETTLED)
        self.assertEqual(result.debt.settlement_operation_id, "settle-1")
        self.assertEqual(result.debt.approver_id, "approver-manager")
        self.assertEqual(result.debt.liability_id, "liable-manager")
        self.assertEqual(result.overdue_cycles, 0)
        with self.assertRaises(ConservationError):
            replace(
                result,
                book=replace(result.book, applied_operations=frozenset()),
            )
        with self.assertRaises(DuplicateOperationError):
            self.settle(result.book, result.debt)
        with self.assertRaises(DuplicateOperationError):
            settle_due_debt(
                result.book,
                self.debt(),
                cycle=2,
                operation_id="settle-2",
                expected_book_version=1,
            )

    def test_due_bottom_borrow_is_repaid_by_removing_one_bottom_slot(self) -> None:
        result = self.settle(self.book(), self.debt(DebtKind.BOTTOM_BORROWED))
        self.assertEqual(result.book.counts, QuotaCounts(2, 5, 0))
        self.assertEqual(result.book.counts.total, 7)

    def test_top_slot_trade_can_be_repaid_from_the_receivers_next_cycle_book(self) -> None:
        donor = QuotaBook("a", "sup", 1, QuotaCounts(2, 4, 1))
        receiver = QuotaBook("b", "sup", 1, QuotaCounts(2, 4, 1))
        trade = SlotTrade("trade-debt", "a", "b", "sup", 1, RatingBand.TOP, 0, 0)
        result = apply_bilateral_slot_trade_with_debt(
            donor,
            receiver,
            trade,
            TradeDebtTerms(
                debt_id="trade-debt-due",
                creditor_manager_id="donor-manager",
                debtor_manager_id="receiver-manager",
                approver_id="superior-manager",
                liability_id="receiver-manager",
            ),
        )
        self.assertEqual(result.trade_result.receiver.counts, QuotaCounts(3, 3, 1))
        debt = result.debt
        self.assertEqual(debt.source_trade_id, "trade-debt")
        self.assertEqual((debt.creditor_team_id, debt.team_id), ("a", "b"))
        self.assertEqual(debt.due_cycle, 2)
        with self.assertRaises(ConservationError):
            replace(
                result,
                debt=replace(debt, source_trade_id="unrelated-trade"),
            )
        future_book = QuotaBook("b", "sup", 2, QuotaCounts(2, 4, 1))
        settled = settle_due_debt(
            future_book,
            debt,
            cycle=2,
            operation_id="trade-debt-settlement",
            expected_book_version=0,
        )
        self.assertEqual(settled.book.counts, QuotaCounts(1, 5, 1))
        self.assertEqual(settled.debt.state, DebtState.SETTLED)

    def test_before_due_is_red_but_overdue_debt_remains_settleable(self) -> None:
        debt = self.debt()
        with self.assertRaises(DebtNotDueError) as not_due:
            self.settle(self.book(cycle=1), debt, cycle=1)
        self.assertEqual(not_due.exception.code, RedCode.DEBT_NOT_DUE)
        overdue = self.settle(
            QuotaBook("a", "sup", 4, QuotaCounts(2, 4, 1)), debt, cycle=4
        )
        self.assertEqual(overdue.overdue_cycles, 2)
        self.assertEqual(overdue.debt.state, DebtState.SETTLED)

    def test_stale_book_version_and_invalid_debt_shape_are_red(self) -> None:
        with self.assertRaises(StaleOperationError):
            settle_due_debt(
                self.book(version=1),
                self.debt(),
                cycle=2,
                operation_id="settle-1",
                expected_book_version=0,
            )
        with self.assertRaises(InvalidInputError):
            replace(self.debt(), due_cycle=1)
        with self.assertRaises(InvalidInputError):
            replace(self.debt(), due_cycle=3)
        with self.assertRaises(InvalidInputError):
            replace(self.debt(), slots=2)
        with self.assertRaises(InvalidInputError):
            replace(self.debt(), slots=True)


class AgendaAndAttentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = (
            AgendaEntry("one", 1),
            AgendaEntry("two", 2),
            AgendaEntry("three", 3, strategic=True),
        )

    def test_all_agenda_modes_are_deterministic(self) -> None:
        authority = ("one", "two", "three")
        top_plan = build_agenda(
                self.entries,
                AgendaMode.TOP_FIRST,
                authoritative_cohort_ids=authority,
        )
        self.assertEqual(top_plan.subject_ids, ("one", "two", "three"))
        self.assertEqual(top_plan.mode, AgendaMode.TOP_FIRST)
        self.assertEqual(top_plan.authoritative_cohort_ids, authority)
        self.assertEqual(
            build_agenda(
                self.entries,
                AgendaMode.BOTTOM_FIRST,
                authoritative_cohort_ids=authority,
            ).subject_ids,
            ("three", "two", "one"),
        )
        self.assertEqual(
            build_agenda(
                self.entries,
                AgendaMode.STRATEGIC_FIRST,
                authoritative_cohort_ids=authority,
            ).subject_ids,
            ("three", "one", "two"),
        )
        first = build_agenda(
            self.entries,
            AgendaMode.STABLE_RANDOM,
            authoritative_cohort_ids=authority,
            seed="round-9",
        )
        second = build_agenda(
            reversed(self.entries),
            AgendaMode.STABLE_RANDOM,
            authoritative_cohort_ids=authority,
            seed="round-9",
        )
        self.assertEqual(first, second)
        self.assertEqual(set(first.subject_ids), {"one", "two", "three"})
        self.assertEqual(first.seed, "round-9")

    def test_attention_follows_agenda_and_conserves_total(self) -> None:
        ledger = AttentionLedger("round-1", 7, ("one", "two", "three"), total=3)
        ledger = spend_attention(
            ledger,
            subject_id="one",
            cost=1,
            operation_id="attention-1",
            expected_review_serial=7,
        )
        ledger = spend_attention(
            ledger,
            subject_id="two",
            cost=2,
            operation_id="attention-2",
            expected_review_serial=7,
        )
        self.assertEqual(ledger.discussed, ("one", "two"))
        self.assertEqual((ledger.spent, ledger.remaining, ledger.total), (3, 0, 3))
        with self.assertRaises(IllegalStateError):
            spend_attention(
                ledger,
                subject_id="three",
                cost=1,
                operation_id="attention-3",
                expected_review_serial=7,
            )

    def test_out_of_order_duplicate_and_stale_attention_are_typed_red(self) -> None:
        ledger = AttentionLedger("round-1", 7, ("one", "two"), total=2)
        with self.assertRaises(IllegalStateError):
            spend_attention(
                ledger,
                subject_id="two",
                cost=1,
                operation_id="attention-1",
                expected_review_serial=7,
            )
        first = spend_attention(
            ledger,
            subject_id="one",
            cost=1,
            operation_id="attention-1",
            expected_review_serial=7,
        )
        with self.assertRaises(DuplicateOperationError):
            spend_attention(
                first,
                subject_id="two",
                cost=1,
                operation_id="attention-1",
                expected_review_serial=7,
            )
        with self.assertRaises(StaleOperationError):
            spend_attention(
                ledger,
                subject_id="one",
                cost=1,
                operation_id="other",
                expected_review_serial=6,
            )

    def test_duplicate_agenda_subject_or_rank_is_typed_red(self) -> None:
        with self.assertRaises(DuplicateInputError):
            build_agenda(
                (AgendaEntry("same", 1), AgendaEntry("same", 2)),
                AgendaMode.TOP_FIRST,
                authoritative_cohort_ids=("same",),
            )
        with self.assertRaises(DuplicateInputError):
            build_agenda(
                (AgendaEntry("a", 1), AgendaEntry("b", 1)),
                AgendaMode.TOP_FIRST,
                authoritative_cohort_ids=("a", "b"),
            )

    def test_agenda_cannot_omit_or_add_a_cohort_subject(self) -> None:
        with self.assertRaises(ConservationError):
            build_agenda(
                self.entries,
                AgendaMode.TOP_FIRST,
                authoritative_cohort_ids=("one", "two", "three", "four"),
            )
        with self.assertRaises(ConservationError):
            build_agenda(
                self.entries,
                AgendaMode.TOP_FIRST,
                authoritative_cohort_ids=("one", "two"),
            )

    def seat_ledger(self) -> AttentionSeatLedger:
        return open_attention_seat_ledger(
            meeting_id="meeting-1",
            review_serial=7,
            candidate_grades=(
                FrozenCandidateGrade("one", RatingBand.TOP),
                FrozenCandidateGrade("two", RatingBand.MIDDLE),
                FrozenCandidateGrade("three", RatingBand.BOTTOM),
            ),
            seat_owner_ids=("manager-a", "manager-a"),
            total_minutes=20,
        )

    def test_two_attention_seats_bind_at_most_two_of_three_candidates(self) -> None:
        ledger = self.seat_ledger()
        ledger = bind_attention_seat(
            ledger,
            seat_id="seat-1",
            owner_manager_id="manager-a",
            subject_id="one",
            evidence_id="evidence-one",
            operation_id="bind-1",
            expected_review_serial=7,
        )
        ledger = bind_attention_seat(
            ledger,
            seat_id="seat-2",
            owner_manager_id="manager-a",
            subject_id="two",
            evidence_id="evidence-two",
            operation_id="bind-2",
            expected_review_serial=7,
        )
        self.assertEqual(ledger.total_seats, 2)
        self.assertEqual(
            {seat.subject_id for seat in ledger.seats}, {"one", "two"}
        )
        self.assertNotIn("three", {seat.subject_id for seat in ledger.seats})
        with self.assertRaises(IllegalStateError):
            bind_attention_seat(
                ledger,
                seat_id="seat-1",
                owner_manager_id="manager-a",
                subject_id="three",
                evidence_id="evidence-three",
                operation_id="bind-3",
                expected_review_serial=7,
            )

    def test_attention_seat_transfer_changes_owner_but_conserves_total(self) -> None:
        ledger = self.seat_ledger()
        transferred = transfer_attention_seat(
            ledger,
            seat_id="seat-2",
            from_manager_id="manager-a",
            to_manager_id="manager-b",
            operation_id="transfer-1",
            expected_review_serial=7,
        )
        self.assertEqual(transferred.total_seats, ledger.total_seats)
        self.assertEqual(transferred.seat("seat-1").owner_manager_id, "manager-a")
        self.assertEqual(transferred.seat("seat-2").owner_manager_id, "manager-b")
        with self.assertRaises(StaleOperationError):
            transfer_attention_seat(
                transferred,
                seat_id="seat-2",
                from_manager_id="manager-a",
                to_manager_id="manager-c",
                operation_id="transfer-stale",
                expected_review_serial=7,
            )

    def test_attention_seat_consumption_is_one_shot_and_time_conserving(self) -> None:
        ledger = bind_attention_seat(
            self.seat_ledger(),
            seat_id="seat-1",
            owner_manager_id="manager-a",
            subject_id="one",
            evidence_id="evidence-one",
            operation_id="bind-1",
            expected_review_serial=7,
        )
        consumed = consume_attention_seat(
            ledger,
            seat_id="seat-1",
            owner_manager_id="manager-a",
            subject_id="one",
            minutes=12,
            operation_id="consume-1",
            expected_review_serial=7,
        )
        self.assertEqual((consumed.spent_minutes, consumed.remaining_minutes), (12, 8))
        self.assertEqual(
            consumed.spent_minutes + consumed.remaining_minutes,
            consumed.total_minutes,
        )
        with self.assertRaises(DuplicateOperationError):
            consume_attention_seat(
                consumed,
                seat_id="seat-1",
                owner_manager_id="manager-a",
                subject_id="one",
                minutes=1,
                operation_id="consume-again",
                expected_review_serial=7,
            )
        with self.assertRaises(IllegalStateError):
            transfer_attention_seat(
                consumed,
                seat_id="seat-1",
                from_manager_id="manager-a",
                to_manager_id="manager-b",
                operation_id="transfer-consumed",
                expected_review_serial=7,
            )

    def test_overtime_records_displaced_subject_costs_and_never_changes_frozen_grades(
        self,
    ) -> None:
        ledger = bind_attention_seat(
            self.seat_ledger(),
            seat_id="seat-1",
            owner_manager_id="manager-a",
            subject_id="one",
            evidence_id="evidence-one",
            operation_id="bind-1",
            expected_review_serial=7,
        )
        ledger = bind_attention_seat(
            ledger,
            seat_id="seat-2",
            owner_manager_id="manager-a",
            subject_id="two",
            evidence_id="evidence-two",
            operation_id="bind-2",
            expected_review_serial=7,
        )
        ledger = consume_attention_seat(
            ledger,
            seat_id="seat-1",
            owner_manager_id="manager-a",
            subject_id="one",
            minutes=15,
            operation_id="consume-1",
            expected_review_serial=7,
        )
        frozen_before = ledger.frozen_grades
        before_failed_attempt = ledger
        with self.assertRaises(InvalidInputError):
            use_overtime_attention(
                ledger,
                manager_id="manager-a",
                favored_subject_id="three",
                displaced_subject_id="two",
                evidence_id="evidence-three",
                minutes=5,
                patience_cost=2,
                political_cost=3,
                operation_id="not-overtime",
                expected_review_serial=7,
            )
        self.assertEqual(ledger, before_failed_attempt)
        overtime = use_overtime_attention(
            ledger,
            manager_id="manager-a",
            favored_subject_id="three",
            displaced_subject_id="two",
            evidence_id="evidence-three",
            minutes=10,
            patience_cost=2,
            political_cost=3,
            operation_id="overtime-1",
            expected_review_serial=7,
        )
        self.assertEqual(overtime.frozen_grades, frozen_before)
        self.assertEqual((overtime.spent_minutes, overtime.overtime_minutes), (25, 5))
        self.assertEqual((overtime.patience_cost, overtime.political_cost), (2, 3))
        receipt = overtime.overtime_receipts[0]
        self.assertEqual(
            (receipt.favored_subject_id, receipt.displaced_subject_id),
            ("three", "two"),
        )
        self.assertEqual(overtime.seat("seat-2").subject_id, "three")


class PendingSlotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quota = QuotaCounts(2, 4, 1)
        self.ledger = open_pending_slot_ledger(
            round_id="round-1", review_serial=9, quota=self.quota
        )

    def hold(self, ledger: PendingSlotLedger, **changes: object) -> PendingSlotLedger:
        values: dict[str, object] = {
            "hold_id": "hold-1",
            "subject_id": "subject-a",
            "band": RatingBand.TOP,
            "fallback_band": RatingBand.MIDDLE,
            "milestone_id": "milestone-a",
            "verifier_id": "verifier-a",
            "deadline_cycle": 10,
            "frozen_reward": Fraction(125, 2),
            "operation_id": "hold-op",
            "expected_review_serial": 9,
        }
        values.update(changes)
        return hold_pending_slot(ledger, **values)  # type: ignore[arg-type]

    def test_verified_success_commits_exactly_one_held_slot_and_reward_record(self) -> None:
        held = self.hold(self.ledger)
        self.assertEqual(held.free, QuotaCounts(1, 4, 1))
        self.assertEqual(len(held.pending_slots), 1)
        self.assertEqual(held.pending_slots[0].frozen_reward, Fraction(125, 2))
        settled = resolve_pending_slot(
            held,
            hold_id="hold-1",
            subject_id="subject-a",
            verifier_id="verifier-a",
            current_cycle=10,
            resolution=PendingResolution.SUCCESS,
            operation_id="resolve-op",
            expected_review_serial=9,
        )
        self.assertEqual(settled.pending_slots, ())
        self.assertEqual(settled.committed, QuotaCounts(1, 0, 0))
        self.assertEqual(settled.resolved[0].final_band, RatingBand.TOP)
        self.assertEqual(settled.resolved[0].held_band, RatingBand.TOP)
        self.assertEqual(settled.resolved[0].fallback_band, RatingBand.MIDDLE)
        self.assertEqual(settled.resolved[0].deadline_cycle, 10)
        self.assertEqual(settled.resolved[0].frozen_reward, Fraction(125, 2))
        for band in (RatingBand.TOP, RatingBand.MIDDLE, RatingBand.BOTTOM):
            self.assertEqual(settled.free[band] + settled.committed[band], self.quota[band])

    def test_failure_cannot_exchange_a_pending_milestone_for_top(self) -> None:
        held = self.hold(self.ledger)
        failed = resolve_pending_slot(
            held,
            hold_id="hold-1",
            subject_id="subject-a",
            verifier_id="verifier-a",
            current_cycle=9,
            resolution=PendingResolution.FAILURE,
            operation_id="resolve-op",
            expected_review_serial=9,
        )
        self.assertEqual(failed.free, QuotaCounts(2, 3, 1))
        self.assertEqual(failed.committed, QuotaCounts(0, 1, 0))
        self.assertEqual(failed.resolved[0].final_band, RatingBand.MIDDLE)
        self.assertNotEqual(failed.resolved[0].final_band, RatingBand.TOP)
        with self.assertRaises(DuplicateOperationError):
            resolve_pending_slot(
                failed,
                hold_id="hold-1",
                subject_id="subject-a",
                verifier_id="verifier-a",
                current_cycle=10,
                resolution=PendingResolution.FAILURE,
                operation_id="different-replay-op",
                expected_review_serial=9,
            )
        with self.assertRaises(DuplicateOperationError):
            self.hold(failed, operation_id="hold-again")
        with self.assertRaises(DuplicateOperationError):
            self.hold(
                failed,
                hold_id="new-hold-for-same-subject",
                operation_id="new-op-for-same-subject",
            )

    def test_multiple_subjects_may_each_hold_one_slot_in_the_same_round(self) -> None:
        held = self.hold(self.ledger)
        held = self.hold(
            held,
            hold_id="hold-2",
            subject_id="subject-b",
            band=RatingBand.MIDDLE,
            fallback_band=RatingBand.BOTTOM,
            milestone_id="milestone-b",
            verifier_id="verifier-b",
            operation_id="hold-op-2",
        )
        self.assertEqual(len(held.pending_slots), 2)
        self.assertEqual(held.free, QuotaCounts(1, 3, 1))
        for band in (RatingBand.TOP, RatingBand.MIDDLE, RatingBand.BOTTOM):
            pending = sum(slot.band is band for slot in held.pending_slots)
            self.assertEqual(held.free[band] + held.committed[band] + pending, self.quota[band])

    def test_duplicate_hold_subject_and_stale_identity_are_red(self) -> None:
        held = self.hold(self.ledger)
        with self.assertRaises(DuplicateOperationError):
            self.hold(held)
        with self.assertRaises(DuplicateOperationError):
            self.hold(held, operation_id="hold-op-2", hold_id="hold-2")
        with self.assertRaises(StaleOperationError):
            resolve_pending_slot(
                held,
                hold_id="hold-1",
                subject_id="subject-a",
                verifier_id="wrong-verifier",
                current_cycle=10,
                resolution=PendingResolution.SUCCESS,
                operation_id="resolve-op",
                expected_review_serial=9,
            )

    def test_timeout_requires_deadline_and_uses_fallback_band(self) -> None:
        held = self.hold(self.ledger)
        with self.assertRaises(IllegalStateError):
            resolve_pending_slot(
                held,
                hold_id="hold-1",
                subject_id="subject-a",
                verifier_id="verifier-a",
                current_cycle=9,
                resolution=PendingResolution.TIMEOUT,
                operation_id="too-early",
                expected_review_serial=9,
            )
        timed_out = resolve_pending_slot(
            held,
            hold_id="hold-1",
            subject_id="subject-a",
            verifier_id="verifier-a",
            current_cycle=11,
            resolution=PendingResolution.TIMEOUT,
            operation_id="timeout-op",
            expected_review_serial=9,
        )
        self.assertEqual(timed_out.resolved[0].final_band, RatingBand.MIDDLE)

    def test_stale_serial_insufficient_slot_and_broken_conservation_are_red(self) -> None:
        with self.assertRaises(StaleOperationError):
            self.hold(self.ledger, expected_review_serial=8)
        empty_top = open_pending_slot_ledger(
            round_id="round-2", review_serial=9, quota=QuotaCounts(0, 4, 1)
        )
        with self.assertRaises(InsufficientSlotError):
            self.hold(empty_top)
        with self.assertRaises(InvalidInputError):
            self.hold(self.ledger, fallback_band=RatingBand.TOP)
        with self.assertRaises(ConservationError):
            PendingSlotLedger(
                "broken",
                1,
                quota=QuotaCounts(1, 0, 0),
                free=QuotaCounts(),
                committed=QuotaCounts(),
            )

    def test_failed_pending_resolution_is_atomic(self) -> None:
        ledger = open_pending_slot_ledger(
            round_id="atomic-round",
            review_serial=9,
            quota=QuotaCounts(1, 0, 0),
        )
        held = self.hold(ledger)
        before_failed_attempt = held
        with self.assertRaises(InsufficientSlotError):
            resolve_pending_slot(
                held,
                hold_id="hold-1",
                subject_id="subject-a",
                verifier_id="verifier-a",
                current_cycle=9,
                resolution=PendingResolution.FAILURE,
                operation_id="atomic-failure",
                expected_review_serial=9,
            )
        self.assertEqual(held, before_failed_attempt)


class SymmetricReopenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = ClosedCalibrationRound(
            "round-1",
            11,
            QuotaCounts(7, 14, 2),
            "board-cycle-11",
            "board-hash-v1",
            "reward-hash-v1",
        )
        self.policy = SymmetricReopenPolicy(Fraction(5, 2))

    def receipt(
        self,
        evidence_id: str = "evidence-success",
        *,
        board_hash: str = "board-hash-v2",
    ) -> BoardRecalculationReceipt:
        return BoardRecalculationReceipt(
            receipt_id="recompute-1",
            source_board_hash="board-hash-v1",
            evidence_id=evidence_id,
            recomputed_board_hash=board_hash,
            recomputed_quota=QuotaCounts(7, 14, 2),
            reward_snapshot_hash="reward-hash-v2",
        )

    def reopen(self, polarity: EvidencePolarity, *, operation_id: str = "reopen-op"):
        return request_symmetric_reopen(
            self.snapshot,
            LateEvidence(f"evidence-{polarity.value}", polarity, Fraction(5, 2)),
            self.policy,
            operation_id=operation_id,
            expected_review_serial=11,
            expected_board_cycle_id="board-cycle-11",
            expected_board_hash="board-hash-v1",
        )

    def test_equal_success_and_incident_magnitudes_reopen_symmetrically(self) -> None:
        success = self.reopen(EvidencePolarity.SUCCESS)
        incident = self.reopen(EvidencePolarity.INCIDENT)
        self.assertEqual(
            (success.phase, success.reopen_count, success.quota),
            (incident.phase, incident.reopen_count, incident.quota),
        )
        self.assertEqual(success.phase, ClosurePhase.REOPENED)
        self.assertEqual(success.quota, self.snapshot.quota)
        self.assertNotEqual(
            success.accepted_evidence.polarity,  # type: ignore[union-attr]
            incident.accepted_evidence.polarity,  # type: ignore[union-attr]
        )

    def test_threshold_is_inclusive_and_below_threshold_is_red_for_both_polarities(self) -> None:
        self.assertEqual(self.reopen(EvidencePolarity.SUCCESS).phase, ClosurePhase.REOPENED)
        for polarity in EvidencePolarity:
            with self.subTest(polarity=polarity):
                evidence = LateEvidence("below", polarity, Fraction(249, 100))
                with self.assertRaises(ThresholdNotMetError) as caught:
                    request_symmetric_reopen(
                        self.snapshot,
                        evidence,
                        self.policy,
                        operation_id=f"below-{polarity.value}",
                        expected_review_serial=11,
                        expected_board_cycle_id="board-cycle-11",
                        expected_board_hash="board-hash-v1",
                    )
                self.assertEqual(caught.exception.code, RedCode.THRESHOLD_NOT_MET)

    def test_reopen_is_one_shot_even_after_reseal(self) -> None:
        reopened = self.reopen(EvidencePolarity.SUCCESS)
        resealed = reseal_reopened_round(
            reopened,
            receipt=self.receipt(),
            operation_id="reseal-op",
            expected_review_serial=11,
            expected_board_hash="board-hash-v1",
        )
        self.assertEqual(resealed.phase, ClosurePhase.RESEALED)
        self.assertEqual(resealed.board_hash, "board-hash-v2")
        self.assertEqual(resealed.reward_snapshot_hash, "reward-hash-v2")
        with self.assertRaises(DuplicateOperationError):
            request_symmetric_reopen(
                resealed,
                LateEvidence("another", EvidencePolarity.INCIDENT, 3),
                self.policy,
                operation_id="second-reopen",
                expected_review_serial=11,
                expected_board_cycle_id="board-cycle-11",
                expected_board_hash="board-hash-v2",
            )

    def test_rewards_block_reopen_and_reopened_round_blocks_rewards(self) -> None:
        paid = issue_rewards(
            self.snapshot,
            operation_id="reward-op",
            expected_review_serial=11,
            expected_board_hash="board-hash-v1",
            expected_reward_snapshot_hash="reward-hash-v1",
        )
        with self.assertRaises(IllegalStateError):
            request_symmetric_reopen(
                paid,
                LateEvidence("late", EvidencePolarity.SUCCESS, 3),
                self.policy,
                operation_id="reopen-paid",
                expected_review_serial=11,
                expected_board_cycle_id="board-cycle-11",
                expected_board_hash="board-hash-v1",
            )
        with self.assertRaises(IllegalStateError):
            issue_rewards(
                self.reopen(EvidencePolarity.SUCCESS),
                operation_id="reward-too-early",
                expected_review_serial=11,
                expected_board_hash="board-hash-v1",
                expected_reward_snapshot_hash="reward-hash-v1",
            )

    def test_reseal_and_reward_require_latest_atomic_snapshots(self) -> None:
        reopened = self.reopen(EvidencePolarity.SUCCESS)
        before_failed_reseal = reopened
        with self.assertRaises(StaleOperationError):
            reseal_reopened_round(
                reopened,
                receipt=replace(self.receipt(), source_board_hash="stale-board"),
                operation_id="stale-receipt",
                expected_review_serial=11,
                expected_board_hash="board-hash-v1",
            )
        self.assertEqual(reopened, before_failed_reseal)
        resealed = reseal_reopened_round(
            reopened,
            receipt=self.receipt(),
            operation_id="reseal-latest",
            expected_review_serial=11,
            expected_board_hash="board-hash-v1",
        )
        with self.assertRaises(StaleOperationError):
            issue_rewards(
                resealed,
                operation_id="stale-reward",
                expected_review_serial=11,
                expected_board_hash="board-hash-v1",
                expected_reward_snapshot_hash="reward-hash-v1",
            )
        paid = issue_rewards(
            resealed,
            operation_id="latest-reward",
            expected_review_serial=11,
            expected_board_hash="board-hash-v2",
            expected_reward_snapshot_hash="reward-hash-v2",
        )
        self.assertEqual(paid.phase, ClosurePhase.REWARDS_ISSUED)
        with self.assertRaises(DuplicateOperationError):
            issue_rewards(
                paid,
                operation_id="another-reward-op",
                expected_review_serial=11,
                expected_board_hash="board-hash-v2",
                expected_reward_snapshot_hash="reward-hash-v2",
            )
        with self.assertRaises(DuplicateOperationError):
            reseal_reopened_round(
                resealed,
                receipt=self.receipt(),
                operation_id="another-reseal-op",
                expected_review_serial=11,
                expected_board_hash="board-hash-v2",
            )

    def test_stale_duplicate_and_illegal_reseal_are_distinct_reds(self) -> None:
        with self.assertRaises(StaleOperationError):
            request_symmetric_reopen(
                self.snapshot,
                LateEvidence("late", EvidencePolarity.SUCCESS, 3),
                self.policy,
                operation_id="stale",
                expected_review_serial=10,
                expected_board_cycle_id="board-cycle-11",
                expected_board_hash="board-hash-v1",
            )
        reopened = self.reopen(EvidencePolarity.SUCCESS)
        with self.assertRaises(DuplicateOperationError):
            request_symmetric_reopen(
                reopened,
                LateEvidence("same", EvidencePolarity.SUCCESS, 3),
                self.policy,
                operation_id="reopen-op",
                expected_review_serial=11,
                expected_board_cycle_id="board-cycle-11",
                expected_board_hash="board-hash-v1",
            )
        with self.assertRaises(IllegalStateError):
            reseal_reopened_round(
                self.snapshot,
                receipt=self.receipt(),
                operation_id="bad-reseal",
                expected_review_serial=11,
                expected_board_hash="board-hash-v1",
            )

    def test_invalid_evidence_and_impossible_reopen_count_are_red(self) -> None:
        for magnitude in (0, -1, 1.5):
            with self.subTest(magnitude=magnitude):
                with self.assertRaises(InvalidInputError):
                    LateEvidence(
                        "bad", EvidencePolarity.SUCCESS, magnitude  # type: ignore[arg-type]
                    )
        with self.assertRaises(ConservationError):
            ClosedCalibrationRound(
                "bad",
                1,
                QuotaCounts(1, 2, 0),
                "cycle",
                "board",
                "reward",
                reopen_count=2,
            )
        with self.assertRaises(ConservationError):
            ClosedCalibrationRound(
                "bad-phase",
                1,
                QuotaCounts(1, 2, 0),
                "cycle",
                "board",
                "reward",
                phase=ClosurePhase.REOPENED,
            )
        with self.assertRaises(ConservationError):
            ClosedCalibrationRound(
                "forged-paid-reopen",
                1,
                QuotaCounts(1, 2, 0),
                "cycle",
                "board",
                "reward",
                phase=ClosurePhase.REWARDS_ISSUED,
                reopen_count=1,
                accepted_evidence=LateEvidence(
                    "evidence", EvidencePolarity.SUCCESS, 3
                ),
            )


class NumberedCalibrationSemanticTests(unittest.TestCase):
    def identity(
        self,
        case_serial: int,
        *,
        subject_id: str = "subject-a",
        state: str = "policy_open",
        cycle: int = 12,
    ) -> CaseIdentity:
        return CaseIdentity("manager-a", subject_id, cycle, case_serial, state)

    def test_135_shadow_a_writes_evidence_then_final_consumer_b_is_hidden(self) -> None:
        ledger = PolicyDecisionLedger()
        opened_a = open_shadow_rating_case(
            ledger,
            identity=self.identity(135),
            route=PolicyRoute.A,
            shadow_band=RatingBand.TOP,
            notice_day=100,
            deadline_day=110,
            gap_ids=("gap-kpi", "gap-values"),
            gap_magnitude=4,
            operation_id="m135-a-open",
        )
        case_a = opened_a.business_object
        self.assertIsInstance(case_a, object)
        self.assertTrue(case_a.disclosed)  # type: ignore[union-attr]
        self.assertFalse(case_a.quota_committed)  # type: ignore[union-attr]
        self.assertFalse(case_a.reward_issued)  # type: ignore[union-attr]
        case_a = submit_shadow_evidence(
            case_a,  # type: ignore[arg-type]
            evidence_id="supplement-1",
            submitted_day=109,
            evidence_delta=3,
            operation_id="m135-a-evidence",
            expected_identity=case_a.identity,  # type: ignore[union-attr]
        )
        case_a = finalize_shadow_rating(
            case_a,
            final_band=RatingBand.TOP,
            explanation="supplement accepted",
            current_day=110,
            operation_id="m135-a-final",
            expected_identity=case_a.identity,
        )
        self.assertEqual(case_a.accepted_evidence_ids, ("supplement-1",))
        self.assertEqual(case_a.shadow_object_id, 13535)
        self.assertEqual(case_a.evidence_object_id, 13501)
        self.assertEqual(
            (case_a.evidence_revision, case_a.evidence_delta, case_a.response_code),
            (1, 3, 2),
        )
        self.assertEqual(case_a.response_day, 109)
        self.assertTrue(case_a.quota_committed)
        self.assertFalse(case_a.reward_issued)
        self.assertEqual((case_a.feedback_debt_delta, case_a.appeal_weight_delta), (0, 0))

        opened_b = open_shadow_rating_case(
            opened_a.ledger,
            identity=self.identity(1135),
            route=PolicyRoute.B,
            shadow_band=RatingBand.TOP,
            notice_day=100,
            deadline_day=110,
            gap_ids=("gap-hidden",),
            gap_magnitude=2,
            operation_id="m135-b-open",
        )
        case_b = opened_b.business_object
        self.assertFalse(case_b.disclosed)  # type: ignore[union-attr]
        with self.assertRaises(IllegalStateError):
            submit_shadow_evidence(
                case_b,  # type: ignore[arg-type]
                evidence_id="cannot-see",
                submitted_day=105,
                evidence_delta=2,
                operation_id="m135-b-evidence",
                expected_identity=case_b.identity,  # type: ignore[union-attr]
            )
        case_b = finalize_shadow_rating(
            case_b,  # type: ignore[arg-type]
            final_band=RatingBand.MIDDLE,
            explanation="late unexplained downgrade",
            current_day=110,
            operation_id="m135-b-final",
            expected_identity=case_b.identity,  # type: ignore[union-attr]
        )
        self.assertEqual(case_b.final_drop, 1)
        self.assertFalse(case_b.drop_explained)
        self.assertEqual((case_b.feedback_debt_delta, case_b.appeal_weight_delta), (1, 2))

    def test_c_route_has_no_object_adds_one_debt_and_duplicate_is_atomic(self) -> None:
        before = PolicyDecisionLedger()
        result = open_shadow_rating_case(
            before,
            identity=self.identity(2135),
            route=PolicyRoute.C,
            shadow_band=RatingBand.MIDDLE,
            notice_day=100,
            deadline_day=110,
            gap_ids=(),
            gap_magnitude=0,
            operation_id="m135-c",
        )
        self.assertIsNone(result.business_object)
        self.assertEqual((before.policy_debt, result.ledger.policy_debt), (0, 1))
        frozen_after = result.ledger
        with self.assertRaises(DuplicateOperationError):
            open_shadow_rating_case(
                frozen_after,
                identity=self.identity(2135),
                route=PolicyRoute.C,
                shadow_band=RatingBand.MIDDLE,
                notice_day=100,
                deadline_day=110,
                gap_ids=(),
                gap_magnitude=0,
                operation_id="m135-c-replay",
            )
        self.assertEqual(result.ledger, frozen_after)
        with self.assertRaises(StaleOperationError):
            open_shadow_rating_case(
                PolicyDecisionLedger(),
                identity=self.identity(4135, state="already_closed"),
                route=PolicyRoute.C,
                shadow_band=RatingBand.MIDDLE,
                notice_day=100,
                deadline_day=110,
                gap_ids=(),
                gap_magnitude=0,
                operation_id="m135-c-stale-open",
            )

    def test_136_real_multi_manager_huddle_preserves_recommendation_diff(self) -> None:
        cohort = ("one", "two", "three", "four", "five")
        boundary = ("one", "five")
        opened = open_precalibration_meeting(
            PolicyDecisionLedger(),
            identity=self.identity(136, subject_id="cohort-a"),
            route=PolicyRoute.A,
            manager_ids=("manager-a", "manager-b", "manager-c"),
            cohort_ids=cohort,
            boundary_case_ids=boundary,
            standard_snapshot="standard-v12",
            minutes=45,
            suggested_assignments=(
                BandAssignment("one", RatingBand.TOP),
                BandAssignment("five", RatingBand.BOTTOM),
            ),
            operation_id="m136-a-open",
        )
        meeting = opened.business_object
        formal = (
            BandAssignment("one", RatingBand.MIDDLE),
            BandAssignment("two", RatingBand.MIDDLE),
            BandAssignment("three", RatingBand.TOP),
            BandAssignment("four", RatingBand.MIDDLE),
            BandAssignment("five", RatingBand.BOTTOM),
        )
        consumed = consume_precalibration_meeting(
            meeting,  # type: ignore[arg-type]
            formal_assignments=formal,
            operation_id="m136-a-formal",
            expected_identity=meeting.identity,  # type: ignore[union-attr]
        )
        self.assertEqual(consumed.consumed_minutes, 45)
        self.assertEqual(
            tuple((item.subject_id, item.suggested_band, item.formal_band) for item in consumed.diffs),
            (("one", RatingBand.TOP, RatingBand.MIDDLE),),
        )
        self.assertEqual(
            tuple(item.subject_id for item in consumed.suggested_assignments), boundary
        )

        with self.assertRaises(ConservationError):
            open_precalibration_meeting(
                PolicyDecisionLedger(),
                identity=self.identity(3136, subject_id="fake-huddle"),
                route=PolicyRoute.A,
                manager_ids=("manager-a",),
                cohort_ids=cohort,
                boundary_case_ids=boundary,
                standard_snapshot="standard-v12",
                minutes=45,
                suggested_assignments=(
                    BandAssignment("one", RatingBand.TOP),
                    BandAssignment("five", RatingBand.BOTTOM),
                ),
                operation_id="m136-fake-open",
            )

    def test_136_b_preallocates_whole_cohort_and_is_materially_different(self) -> None:
        cohort = ("one", "two", "three")
        assignments = (
            BandAssignment("one", RatingBand.TOP),
            BandAssignment("two", RatingBand.MIDDLE),
            BandAssignment("three", RatingBand.BOTTOM),
        )
        opened = open_precalibration_meeting(
            PolicyDecisionLedger(),
            identity=self.identity(4136, subject_id="cohort-b"),
            route=PolicyRoute.B,
            manager_ids=("manager-a", "manager-b", "manager-c", "manager-d"),
            cohort_ids=cohort,
            boundary_case_ids=("one",),
            standard_snapshot="standard-v12",
            minutes=30,
            suggested_assignments=assignments,
            operation_id="m136-b-open",
        )
        meeting = opened.business_object
        self.assertTrue(meeting.black_box_risk)  # type: ignore[union-attr]
        self.assertEqual(
            len(meeting.suggested_assignments), len(cohort)  # type: ignore[union-attr]
        )

    def test_137_agenda_consumes_attention_and_quota_in_frozen_order(self) -> None:
        entries = (
            AgendaEntry("one", 1),
            AgendaEntry("two", 2, strategic=True),
            AgendaEntry("three", 3),
        )
        opened = open_agenda_calibration_case(
            PolicyDecisionLedger(),
            identity=self.identity(137, subject_id="cohort-agenda"),
            route=PolicyRoute.B,
            entries=entries,
            authoritative_cohort_ids=("one", "two", "three"),
            quota=QuotaCounts(1, 1, 1),
            attention_minutes=12,
            seed="cycle-12",
            operation_id="m137-b-open",
        )
        case = opened.business_object
        self.assertIsInstance(case, AgendaCalibrationCase)
        self.assertEqual(case.plan.subject_ids[0], "two")
        bands = {
            "one": RatingBand.TOP,
            "two": RatingBand.MIDDLE,
            "three": RatingBand.BOTTOM,
        }
        for index, subject_id in enumerate(case.plan.subject_ids, start=1):
            case = consume_agenda_subject(
                case,
                subject_id=subject_id,
                band=bands[subject_id],
                attention_cost=4,
                operation_id=f"m137-consume-{index}",
                expected_identity=case.identity,
            )
        self.assertEqual(case.identity.state, "agenda_consumed")
        self.assertEqual((case.attention.spent, case.attention.remaining), (12, 0))
        self.assertEqual(case.remaining_quota, QuotaCounts())
        self.assertTrue(case.resolutions[-1].late_segment_pressure)

    def test_138_rounding_a_is_rotated_b_is_chair_selected_and_publish_conserves(self) -> None:
        ledger = PolicyDecisionLedger()
        opened_a = open_quota_rounding_case(
            ledger,
            identity=self.identity(138, subject_id="quota-a"),
            route=PolicyRoute.A,
            cohort_size=23,
            team_ids=("red", "blue"),
            rotation_cycle=2,
            operation_id="m138-a-open",
        )
        case_a = opened_a.business_object
        self.assertIsInstance(case_a, QuotaRoundingCase)
        self.assertEqual(case_a.computation.effective_counts, QuotaCounts(7, 14, 2))
        self.assertEqual(case_a.remainder_team_id, "blue")
        published = publish_rounded_quota(
            case_a,
            team_id="pool-a",
            common_superior_id="emperor",
            operation_id="m138-a-publish",
            expected_identity=case_a.identity,
        )
        self.assertEqual(published.published_book.counts.total, 23)  # type: ignore[union-attr]

        opened_b = open_quota_rounding_case(
            opened_a.ledger,
            identity=self.identity(1138, subject_id="quota-b"),
            route=PolicyRoute.B,
            cohort_size=23,
            team_ids=("red", "blue"),
            rotation_cycle=2,
            operation_id="m138-b-open",
            chair_id="chair-favorite",
            discretionary_team_id="red",
        )
        case_b = opened_b.business_object
        self.assertEqual(case_b.remainder_team_id, "red")  # type: ignore[union-attr]
        self.assertTrue(case_b.black_box_risk)  # type: ignore[union-attr]

    def test_140_reorg_keeps_both_evidence_segments_but_occupies_one_slot(self) -> None:
        segments = (
            EvidenceSegment("old-team", "old-manager", 1, 80, ("old-kpi",)),
            EvidenceSegment("new-team", "new-manager", 81, 120, ("new-kpi",)),
        )
        opened_a = open_reorganization_ownership_case(
            PolicyDecisionLedger(),
            identity=self.identity(140),
            route=PolicyRoute.A,
            old_manager_id="old-manager",
            new_manager_id="new-manager",
            old_team_id="old-team",
            new_team_id="new-team",
            old_service_days=80,
            new_service_days=40,
            ownership_freeze_day=90,
            evidence_segments=segments,
            operation_id="m140-a-open",
        )
        case_a = allocate_reorganized_subject(
            opened_a.business_object,  # type: ignore[arg-type]
            operation_id="m140-a-allocate",
            expected_identity=opened_a.business_object.identity,  # type: ignore[union-attr]
        )
        self.assertEqual(case_a.quota_owner_team_id, "old-team")
        self.assertEqual(case_a.allocation_receipt.occupied_slots, 1)  # type: ignore[union-attr]
        self.assertEqual(
            set(case_a.allocation_receipt.evidence_ids),  # type: ignore[union-attr]
            {"old-kpi", "new-kpi"},
        )

        opened_b = open_reorganization_ownership_case(
            opened_a.ledger,
            identity=self.identity(1140),
            route=PolicyRoute.B,
            old_manager_id="old-manager",
            new_manager_id="new-manager",
            old_team_id="old-team",
            new_team_id="new-team",
            old_service_days=80,
            new_service_days=40,
            ownership_freeze_day=90,
            evidence_segments=segments,
            operation_id="m140-b-open",
        )
        self.assertEqual(
            opened_b.business_object.quota_owner_team_id,  # type: ignore[union-attr]
            "new-team",
        )
        self.assertEqual(len(opened_b.business_object.evidence_segments), 2)  # type: ignore[union-attr]

    def test_141_must_review_a_is_advisory_b_is_manager_owned_conserved_swap(self) -> None:
        registry = ExecutiveReviewRegistry()
        opened_a = open_executive_must_review(
            PolicyDecisionLedger(),
            registry,
            identity=self.identity(141),
            route=PolicyRoute.A,
            executive_id="executive",
            direct_manager_id="manager-a",
            reason="written strategic reason",
            intervention_kind="must_review",
            operation_id="m141-a-open",
        )
        case_a = opened_a.policy.business_object
        self.assertIsInstance(case_a, ExecutiveMustReviewCase)
        resolved_a = resolve_executive_must_review(
            case_a,
            direct_manager_band=RatingBand.MIDDLE,
            intervention_supported=False,
            operation_id="m141-a-resolve",
            expected_identity=case_a.identity,
        )
        self.assertEqual(resolved_a.final_band, RatingBand.MIDDLE)
        self.assertEqual((resolved_a.attention_consumed, resolved_a.judgment_credit_delta), (1, -1))
        self.assertEqual(resolved_a.judgment_result, "miss")
        self.assertFalse(resolved_a.swap_executed)
        with self.assertRaises(InsufficientSlotError):
            open_executive_must_review(
                opened_a.policy.ledger,
                opened_a.registry,
                identity=self.identity(1141, subject_id="subject-b"),
                route=PolicyRoute.A,
                executive_id="executive",
                direct_manager_id="manager-a",
                reason="second request",
                intervention_kind="must_review",
                operation_id="m141-a-second",
            )

        opened_b = open_executive_must_review(
            opened_a.policy.ledger,
            opened_a.registry,
            identity=self.identity(2141, subject_id="subject-c", cycle=13),
            route=PolicyRoute.B,
            executive_id="executive",
            direct_manager_id="manager-a",
            reason="attempted direct override",
            intervention_kind="override",
            operation_id="m141-b-open",
        )
        case_b = opened_b.policy.business_object
        resolved_b = resolve_executive_must_review(
            case_b,  # type: ignore[arg-type]
            direct_manager_band=RatingBand.MIDDLE,
            intervention_supported=True,
            operation_id="m141-b-resolve",
            expected_identity=case_b.identity,  # type: ignore[union-attr]
            swap_peer_id="peer-top",
            swap_peer_band=RatingBand.TOP,
            manager_band_counts=QuotaCounts(2, 4, 1),
            expected_book_version=7,
        )
        self.assertEqual(resolved_b.final_band, RatingBand.TOP)
        self.assertEqual(resolved_b.attention_consumed, 1)
        self.assertTrue(resolved_b.override_blocked)
        self.assertTrue(resolved_b.swap_executed)
        self.assertTrue(resolved_b.conservation_valid)
        self.assertEqual(resolved_b.swap_peer_id, "peer-top")
        self.assertEqual(
            (
                resolved_b.subject_band_before,
                resolved_b.subject_band_after,
                resolved_b.peer_band_before,
                resolved_b.peer_band_after,
            ),
            (
                RatingBand.MIDDLE,
                RatingBand.TOP,
                RatingBand.TOP,
                RatingBand.MIDDLE,
            ),
        )
        self.assertEqual(resolved_b.band_counts_before, resolved_b.band_counts_after)
        self.assertEqual(
            (resolved_b.book_version_before, resolved_b.book_version_after), (7, 8)
        )
        self.assertEqual((resolved_b.judgment_result, resolved_b.judgment_credit_delta), ("hit", 1))

        with self.assertRaises(InsufficientSlotError):
            resolve_executive_must_review(
                case_b,  # type: ignore[arg-type]
                direct_manager_band=RatingBand.BOTTOM,
                intervention_supported=True,
                operation_id="m141-b-forged-swap",
                expected_identity=case_b.identity,  # type: ignore[union-attr]
                swap_peer_id="peer-top",
                swap_peer_band=RatingBand.TOP,
                manager_band_counts=QuotaCounts(2, 4, 1),
                expected_book_version=7,
            )


class NumberedTailSemanticTests(unittest.TestCase):
    def identity(
        self,
        case_serial: int,
        *,
        subject_id: str = "subject-a",
        cycle: int = 20,
        state: str = "policy_open",
    ) -> CaseIdentity:
        return CaseIdentity("manager-a", subject_id, cycle, case_serial, state)

    def test_142_a_holds_and_releases_one_slot_b_only_writes_next_cycle(self) -> None:
        quota = QuotaCounts(1, 2, 1)
        slots = open_pending_slot_ledger(
            round_id="round-20", review_serial=20, quota=quota
        )
        opened_a = open_pending_milestone_case(
            PolicyDecisionLedger(),
            slots,
            identity=self.identity(142),
            route=PolicyRoute.A,
            hold_id="hold-a",
            milestone_id="milestone-a",
            verifier_id="verifier-a",
            deadline_cycle=21,
            held_band=RatingBand.TOP,
            fallback_band=RatingBand.MIDDLE,
            frozen_reward=Fraction(75),
            operation_id="m142-a-open",
        )
        case_a = opened_a.policy.business_object
        self.assertIsInstance(case_a, PendingMilestoneCase)
        self.assertEqual(opened_a.slot_ledger.free, QuotaCounts(0, 2, 1))
        self.assertEqual(
            case_a.disclosed_fields,
            ("pending_marker", "milestone_id", "deadline_cycle"),
        )
        self.assertEqual(
            dict(case_a.public_snapshot),
            {
                "pending_marker": True,
                "milestone_id": "milestone-a",
                "deadline_cycle": 21,
            },
        )
        self.assertNotIn("held_band", case_a.public_snapshot)
        self.assertNotIn("frozen_reward", case_a.public_snapshot)
        resolved = resolve_pending_milestone_case(
            case_a,
            opened_a.slot_ledger,
            current_cycle=21,
            resolution=PendingResolution.SUCCESS,
            operation_id="m142-a-resolve",
            expected_identity=case_a.identity,
        )
        self.assertEqual(resolved.case.final_band, RatingBand.TOP)
        self.assertEqual(resolved.case.reward_released, Fraction(75))
        self.assertFalse(resolved.case.quota_held)
        for band in (RatingBand.TOP, RatingBand.MIDDLE, RatingBand.BOTTOM):
            self.assertEqual(
                resolved.slot_ledger.free[band]
                + resolved.slot_ledger.committed[band],
                quota[band],
            )

        slots_before_b = resolved.slot_ledger
        opened_b = open_pending_milestone_case(
            opened_a.policy.ledger,
            slots_before_b,
            identity=self.identity(1142, subject_id="subject-b"),
            route=PolicyRoute.B,
            hold_id="hold-b",
            milestone_id="milestone-b",
            verifier_id="verifier-b",
            deadline_cycle=21,
            held_band=RatingBand.TOP,
            fallback_band=RatingBand.MIDDLE,
            frozen_reward=Fraction(999),
            operation_id="m142-b-open",
        )
        case_b = opened_b.policy.business_object
        self.assertEqual(opened_b.slot_ledger, slots_before_b)
        self.assertFalse(case_b.quota_held)  # type: ignore[union-attr]
        self.assertEqual(case_b.frozen_reward, 0)  # type: ignore[union-attr]
        self.assertEqual(  # type: ignore[union-attr]
            case_b.disclosed_fields,
            ("current_final_unchanged", "next_cycle_evidence"),
        )
        with self.assertRaises(IllegalStateError):
            resolve_pending_milestone_case(
                case_b,  # type: ignore[arg-type]
                opened_b.slot_ledger,
                current_cycle=20,
                resolution=PendingResolution.SUCCESS,
                operation_id="m142-b-too-early",
                expected_identity=case_b.identity,  # type: ignore[union-attr]
                deferred_evidence_id="late-delivery",
            )
        deferred = resolve_pending_milestone_case(
            case_b,  # type: ignore[arg-type]
            opened_b.slot_ledger,
            current_cycle=21,
            resolution=PendingResolution.SUCCESS,
            operation_id="m142-b-next-cycle",
            expected_identity=case_b.identity,  # type: ignore[union-attr]
            deferred_evidence_id="late-delivery",
        )
        self.assertEqual(deferred.case.deferred_evidence_id, "late-delivery")
        self.assertIsNone(deferred.case.final_band)
        self.assertEqual(deferred.slot_ledger, slots_before_b)

    def test_142_c_is_no_object_and_failed_hold_is_atomic(self) -> None:
        slots = open_pending_slot_ledger(
            round_id="round-empty", review_serial=20, quota=QuotaCounts(0, 2, 1)
        )
        before_slots = slots
        before_policy = PolicyDecisionLedger()
        with self.assertRaises(InsufficientSlotError):
            open_pending_milestone_case(
                before_policy,
                slots,
                identity=self.identity(2142),
                route=PolicyRoute.A,
                hold_id="no-top",
                milestone_id="milestone",
                verifier_id="verifier",
                deadline_cycle=21,
                held_band=RatingBand.TOP,
                fallback_band=RatingBand.MIDDLE,
                frozen_reward=Fraction(50),
                operation_id="m142-fail",
            )
        self.assertEqual(slots, before_slots)
        self.assertEqual(before_policy, PolicyDecisionLedger())

        declined = open_pending_milestone_case(
            before_policy,
            slots,
            identity=self.identity(3142),
            route=PolicyRoute.C,
            hold_id="ignored",
            milestone_id="ignored",
            verifier_id="ignored",
            deadline_cycle=21,
            held_band=RatingBand.TOP,
            fallback_band=RatingBand.MIDDLE,
            frozen_reward=Fraction(50),
            operation_id="m142-c",
        )
        self.assertIsNone(declined.policy.business_object)
        self.assertEqual(declined.policy.ledger.policy_debt, 1)
        self.assertEqual(declined.slot_ledger, slots)

    def test_143_a_reopens_b_defers_without_clawing_back_paid_reward(self) -> None:
        board = ClosedCalibrationRound(
            "round-20",
            20,
            QuotaCounts(1, 2, 1),
            "board-cycle-20",
            "board-v1",
            "reward-v1",
        )
        opened_a = open_post_cutoff_case(
            PolicyDecisionLedger(),
            identity=self.identity(143, subject_id="cohort-a"),
            route=PolicyRoute.A,
            board=board,
            evidence=LateEvidence("success", EvidencePolarity.SUCCESS, 3),
            reopen_policy=SymmetricReopenPolicy(Fraction(5, 2)),
            operation_id="m143-a-open",
        )
        case_a = opened_a.business_object
        self.assertIsInstance(case_a, PostCutoffCase)
        self.assertEqual(case_a.board.phase, ClosurePhase.REOPENED)
        receipt = BoardRecalculationReceipt(
            "recalc-20",
            "board-v1",
            "success",
            "board-v2",
            QuotaCounts(1, 2, 1),
            "reward-v2",
        )
        resealed = consume_post_cutoff_case(
            case_a,
            operation_id="m143-a-reseal",
            expected_identity=case_a.identity,
            current_cycle=20,
            receipt=receipt,
        )
        self.assertEqual(resealed.board.phase, ClosurePhase.RESEALED)

        paid = issue_rewards(
            board,
            operation_id="old-reward-paid",
            expected_review_serial=20,
            expected_board_hash="board-v1",
            expected_reward_snapshot_hash="reward-v1",
        )
        opened_b = open_post_cutoff_case(
            opened_a.ledger,
            identity=self.identity(1143, subject_id="cohort-b"),
            route=PolicyRoute.B,
            board=paid,
            evidence=LateEvidence("incident", EvidencePolarity.INCIDENT, 3),
            reopen_policy=SymmetricReopenPolicy(Fraction(5, 2)),
            operation_id="m143-b-open",
        )
        case_b = opened_b.business_object
        self.assertEqual(case_b.board.phase, ClosurePhase.REWARDS_ISSUED)  # type: ignore[union-attr]
        self.assertEqual(case_b.board.reopen_count, 0)  # type: ignore[union-attr]
        deferred = consume_post_cutoff_case(
            case_b,  # type: ignore[arg-type]
            operation_id="m143-b-next",
            expected_identity=case_b.identity,  # type: ignore[union-attr]
            current_cycle=21,
            deferred_evidence_id="next-cycle-incident",
        )
        self.assertEqual(deferred.board, paid)
        self.assertEqual(deferred.deferred_evidence_id, "next-cycle-incident")

    def test_144_dissent_consumes_review_attention_b_keeps_only_consensus(self) -> None:
        registry = DissentRegistry()
        opened_a = open_dissent_case(
            PolicyDecisionLedger(),
            registry,
            identity=self.identity(144),
            route=PolicyRoute.A,
            manager_id="manager-b",
            reason="verified delivery evidence was omitted",
            timestamp=200,
            advocated_band=RatingBand.TOP,
            consensus_manager_ids=(),
            consensus_band=RatingBand.MIDDLE,
            operation_id="m144-a-open",
        )
        dissent = opened_a.policy.business_object
        self.assertIsInstance(dissent, DissentRecord)
        validated = validate_dissent(
            dissent,
            original_band=RatingBand.MIDDLE,
            formal_band=RatingBand.TOP,
            independent_reviewer_id="common-superior-reviewer",
            review_attention_receipt_id="review-attention-144-a",
            operation_id="m144-a-validate",
            expected_identity=dissent.identity,
        )
        self.assertEqual((validated.attention_consumed, validated.credit_delta), (1, 1))
        self.assertEqual(validated.independent_reviewer_id, "common-superior-reviewer")
        self.assertEqual(validated.review_attention_receipt_id, "review-attention-144-a")
        self.assertTrue(validated.self_safe_evidence)
        self.assertFalse(validated.procedural_risk)

        with self.assertRaises(ConservationError):
            validate_dissent(
                dissent,
                original_band=RatingBand.MIDDLE,
                formal_band=RatingBand.TOP,
                independent_reviewer_id=dissent.manager_id,
                review_attention_receipt_id="forged-self-review",
                operation_id="m144-a-forged-reviewer",
                expected_identity=dissent.identity,
            )

        with self.assertRaises(InvalidInputError):
            open_dissent_case(
                opened_a.policy.ledger,
                opened_a.registry,
                identity=self.identity(1144, subject_id="blank-reason"),
                route=PolicyRoute.A,
                manager_id="manager-c",
                reason="",
                timestamp=201,
                advocated_band=RatingBand.TOP,
                consensus_manager_ids=(),
                consensus_band=RatingBand.MIDDLE,
                operation_id="m144-blank",
            )

        opened_b = open_dissent_case(
            opened_a.policy.ledger,
            opened_a.registry,
            identity=self.identity(2144, subject_id="subject-b"),
            route=PolicyRoute.B,
            manager_id="ignored-manager",
            reason="ignored-reason",
            timestamp=202,
            advocated_band=RatingBand.TOP,
            consensus_manager_ids=("manager-a", "manager-b", "manager-c"),
            consensus_band=RatingBand.MIDDLE,
            operation_id="m144-b-open",
        )
        consensus = opened_b.policy.business_object
        self.assertIsInstance(consensus, ConsensusRecord)
        self.assertEqual(len(opened_b.registry.dissent_records), 1)
        sealed = seal_consensus(
            consensus,
            operation_id="m144-b-seal",
            expected_identity=consensus.identity,
        )
        self.assertTrue(sealed.sealed)

    def test_145_only_middle_rank_drives_finite_opportunity_never_compensation(self) -> None:
        subjects = ("one", "two", "three")
        opened_a = open_shadow_band_order_case(
            PolicyDecisionLedger(),
            identity=self.identity(145, subject_id="middle-band-a"),
            route=PolicyRoute.A,
            formal_band=RatingBand.MIDDLE,
            ordered_subject_ids=subjects,
            operation_id="m145-a-open",
        )
        case_a = opened_a.business_object
        self.assertIsInstance(case_a, ShadowBandOrderCase)
        consumed_a = consume_shadow_band_order(
            case_a,
            coaching_count=1,
            opportunity_count=1,
            operation_id="m145-a-consume",
            expected_identity=case_a.identity,
        )
        self.assertTrue(consumed_a.disclosed)
        self.assertEqual(consumed_a.coaching_subject_ids, ("one",))
        self.assertEqual(consumed_a.opportunity_subject_ids, ("one",))
        self.assertEqual(consumed_a.appeal_evidence_subject_ids, ())
        self.assertFalse(consumed_a.black_box_audit)
        self.assertTrue(all(item.band is RatingBand.MIDDLE for item in consumed_a.official_bands))

        opened_b = open_shadow_band_order_case(
            opened_a.ledger,
            identity=self.identity(1145, subject_id="middle-band-b"),
            route=PolicyRoute.B,
            formal_band=RatingBand.MIDDLE,
            ordered_subject_ids=subjects,
            operation_id="m145-b-open",
        )
        case_b = opened_b.business_object
        consumed_b = consume_shadow_band_order(
            case_b,  # type: ignore[arg-type]
            coaching_count=0,
            opportunity_count=1,
            operation_id="m145-b-consume",
            expected_identity=case_b.identity,  # type: ignore[union-attr]
        )
        self.assertFalse(consumed_b.disclosed)
        self.assertEqual(consumed_b.coaching_subject_ids, ())
        self.assertEqual(consumed_b.opportunity_subject_ids, ("one",))
        self.assertEqual(set(consumed_b.appeal_evidence_subject_ids), set(subjects))
        self.assertTrue(consumed_b.black_box_audit)
        self.assertTrue(all(item.band is RatingBand.MIDDLE for item in consumed_b.official_bands))
        for forbidden_field in ("bonus_awards", "reward_budget", "compensation_awards"):
            self.assertFalse(hasattr(consumed_a, forbidden_field))
            self.assertFalse(hasattr(consumed_b, forbidden_field))

        with self.assertRaises(ConservationError):
            open_shadow_band_order_case(
                opened_b.ledger,
                identity=self.identity(2145, subject_id="not-middle"),
                route=PolicyRoute.A,
                formal_band=RatingBand.TOP,
                ordered_subject_ids=subjects,
                operation_id="m145-top-forbidden",
            )
        with self.assertRaises(ConservationError):
            consume_shadow_band_order(
                case_b,  # type: ignore[arg-type]
                coaching_count=1,
                opportunity_count=1,
                operation_id="m145-private-coaching-forbidden",
                expected_identity=case_b.identity,  # type: ignore[union-attr]
            )

    def test_five_field_stale_and_duplicate_consumers_are_atomic(self) -> None:
        opened = open_shadow_band_order_case(
            PolicyDecisionLedger(),
            identity=self.identity(3145, subject_id="atomic-band"),
            route=PolicyRoute.A,
            formal_band=RatingBand.MIDDLE,
            ordered_subject_ids=("one", "two"),
            operation_id="m145-atomic-open",
        )
        case = opened.business_object
        before = case
        with self.assertRaises(DuplicateOperationError):
            consume_shadow_band_order(
                case,  # type: ignore[arg-type]
                coaching_count=1,
                opportunity_count=1,
                operation_id="m145-atomic-open",
                expected_identity=case.identity,  # type: ignore[union-attr]
            )
        self.assertEqual(case, before)
        stale = replace(case.identity, cycle=case.identity.cycle + 1)  # type: ignore[union-attr]
        with self.assertRaises(StaleOperationError):
            consume_shadow_band_order(
                case,  # type: ignore[arg-type]
                coaching_count=1,
                opportunity_count=1,
                operation_id="m145-stale",
                expected_identity=stale,
            )
        self.assertEqual(case, before)
        consumed = consume_shadow_band_order(
            case,  # type: ignore[arg-type]
            coaching_count=1,
            opportunity_count=1,
            operation_id="m145-once",
            expected_identity=case.identity,  # type: ignore[union-attr]
        )
        with self.assertRaises(DuplicateOperationError):
            consume_shadow_band_order(
                consumed,
                coaching_count=1,
                opportunity_count=1,
                operation_id="m145-once",
                expected_identity=consumed.identity,
            )


if __name__ == "__main__":
    unittest.main()
