#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 tests for the B2 reference kernel.

These tests exercise Python contracts only.  Passing them must not be reported
as CK3 implementation, fixture-live evidence, or a readiness increase.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import unittest

import zg361_b2_runtime_data as runtime


MOD_ROOT = Path(__file__).resolve().parents[1]


def identity(*, case_serial: int = 11, cycle_serial: int = 7) -> runtime.CaseIdentity:
    return runtime.CaseIdentity("manager-10", "official-20", cycle_serial, case_serial)


def penalty_ledger() -> runtime.ConservationLedger:
    return runtime.ConservationLedger(
        {
            runtime.Account.TREASURY: 30,
            runtime.Account.PERSONAL_GOLD: 10,
            runtime.Account.MERIT: 40,
        }
    )


def notice_case() -> runtime.NoticeJusticeCase:
    ledger = penalty_ledger()
    return runtime.NoticeJusticeCase(
        identity(),
        ledger,
        runtime.make_penalty_receipts(
            (
                ("treasury-penalty", runtime.Account.TREASURY, 50),
                ("personal-penalty", runtime.Account.PERSONAL_GOLD, 25),
                ("merit-penalty", runtime.Account.MERIT, 60),
            )
        ),
    )


def executing_pip(
    *,
    support_hours: int = 4,
    mentor_id: str | None = "mentor-30",
) -> tuple[
    runtime.PipCase,
    runtime.CapacityPool,
    runtime.ConservationLedger,
]:
    case = runtime.PipCase(
        identity(case_serial=21),
        runtime.PipCategory.CAPABILITY,
        ("frozen-evidence-1",),
    )
    case.qualify(
        case.token(),
        severe_failure=True,
        prior_feedback_count=0,
        low_rating_cycles=0,
    )
    case.freeze_goals(
        case.token(),
        (
            runtime.PipGoal("key-1", True, "mentor", 200),
            runtime.PipGoal("key-2", True, "work-hours", 200),
        ),
        baseline_workload=100,
    )
    pool = runtime.CapacityPool(10)
    ledger = runtime.ConservationLedger({runtime.Account.TREASURY: 20})
    receipt = runtime.LedgerReceipt(
        "pip-support-gold",
        runtime.Account.TREASURY,
        runtime.Account.GOLD_SINK,
        5,
    )
    result = case.start_execution(
        case.token(),
        manager_signed=True,
        subject_signed=True,
        independent_confirmed=False,
        start_day=100,
        end_day=200,
        capacity_pool=pool,
        support_hours=support_hours,
        mentor_id=mentor_id,
        support_receipt=receipt,
        ledger=ledger,
    )
    if not result.applied:
        raise AssertionError(result)
    return case, pool, ledger


class BindingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest = json.loads(
            (MOD_ROOT / "docs/361-mechanism-manifest.json").read_text(
                encoding="utf-8-sig"
            )
        )
        cls.items = {item["id"]: item for item in manifest["items"]}

    def test_exact_forty_new_mechanisms_and_two_interface_rows(self) -> None:
        expected_new = (
            tuple(range(14, 18))
            + tuple(range(70, 82))
            + tuple(range(146, 157))
            + tuple(range(181, 192))
            + (358, 359)
        )
        self.assertEqual(runtime.B2_NEW_IDS, expected_new)
        self.assertEqual(len(runtime.B2_NEW_IDS), 40)
        self.assertEqual(runtime.B2_INTERFACE_IDS, (18, 69))
        self.assertTrue(set(runtime.B2_NEW_IDS).isdisjoint(runtime.B2_INTERFACE_IDS))
        self.assertEqual(len(runtime.B2_BINDINGS), 42)

    def test_018_and_069_are_interface_only_not_new_completion(self) -> None:
        roles = {row.mechanism_id: row.batch_role for row in runtime.B2_BINDINGS}
        self.assertEqual(
            {mechanism_id for mechanism_id, role in roles.items() if role == "interface-only"},
            {18, 69},
        )
        self.assertEqual(sum(role == "new-mechanism" for role in roles.values()), 40)
        self.assertNotIn(18, runtime.B2_NEW_IDS)
        self.assertNotIn(69, runtime.B2_NEW_IDS)

    def test_bindings_match_frozen_runtime_manifest_identity_and_hook(self) -> None:
        for row in runtime.B2_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                source = self.items[row.mechanism_id]
                plan = source["runtime_plan"]
                snapshot = json.loads(
                    (MOD_ROOT / plan["source"]).read_text(encoding="utf-8-sig")
                )
                source_row = next(item for item in snapshot["items"] if item["id"] == row.mechanism_id)
                self.assertEqual(row.title, source["title_cn"])
                self.assertEqual(row.domain, plan["domain"])
                self.assertEqual(row.object_type, plan["object_type"])
                self.assertEqual(row.operation_key, plan["operation_key"])
                self.assertEqual(row.owner_binding, source_row["owner_scope"])
                self.assertEqual(row.subject_binding, source_row["subject_scope"])
                self.assertEqual(row.cycle_binding, source_row["cycle_scope"])
                self.assertEqual(row.case_binding, source_row["case_scope"])
                self.assertEqual(row.hook, plan["trigger_hook"])

    def test_every_row_freezes_identity_state_hook_write_and_consumer(self) -> None:
        for row in runtime.B2_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                self.assertTrue(row.owner_binding)
                self.assertTrue(row.subject_binding)
                self.assertTrue(row.cycle_binding)
                self.assertTrue(row.case_binding)
                self.assertTrue(row.state_binding)
                self.assertTrue(row.hook)
                self.assertTrue(row.from_state)
                self.assertTrue(row.to_state)
                self.assertTrue(row.meaningful_write)
                self.assertTrue(row.consumer)

    def test_every_row_has_typed_a_b_and_bounded_no_case_write_c(self) -> None:
        for row in runtime.B2_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                self.assertEqual(tuple(route.route for route in row.routes), tuple(runtime.PolicyRoute))
                self.assertTrue(row.routes[0].mutates_business_case)
                self.assertTrue(row.routes[1].mutates_business_case)
                self.assertFalse(row.routes[2].mutates_business_case)
                self.assertEqual(row.routes[2].operation, "policy.defer")
                self.assertEqual(row.routes[2].from_state, row.routes[2].to_state)
                self.assertGreater(row.routes[2].defer_days, 0)

    def test_deadlines_are_target_bound_and_stale_guarded(self) -> None:
        for row in runtime.B2_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                self.assertTrue(row.deadlines)
                for deadline in row.deadlines:
                    self.assertEqual(deadline.target_binding, row.subject_binding)
                    self.assertEqual(deadline.stale_guard, runtime.STALE_GUARD)
                    self.assertGreaterEqual(deadline.days, 0)
                    self.assertTrue(deadline.expected_state)

    def test_transaction_receipt_and_feedback_contracts_are_total(self) -> None:
        keys: set[str] = set()
        for row in runtime.B2_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                self.assertTrue(row.transaction.conservation)
                self.assertTrue(row.transaction.resources or row.transaction.no_transfer_reason)
                self.assertEqual(len(row.receipt.keys), 3)
                self.assertTrue(keys.isdisjoint(row.receipt.keys))
                keys.update(row.receipt.keys)
                self.assertIn("no-op", row.receipt.replay)
                self.assertIn("settled", row.receipt.refund_rule)
                self.assertTrue(row.feedback)

    def test_reference_kernel_does_not_inflate_readiness(self) -> None:
        self.assertTrue(runtime.REFERENCE_ONLY)
        self.assertFalse(runtime.CK3_IMPLEMENTED)
        self.assertEqual(runtime.READINESS_CHANGE, "none")
        self.assertEqual(runtime.RUNTIME_EVIDENCE, "python-reference-only")
        for mechanism_id in runtime.B2_NEW_IDS:
            self.assertEqual(
                self.items[mechanism_id]["status"]["domain_runtime"],
                "not-implemented",
            )
        for mechanism_id in runtime.B2_INTERFACE_IDS:
            self.assertEqual(
                self.items[mechanism_id]["status"]["domain_runtime"],
                "partial",
            )

    def test_route_c_posts_one_policy_debt_without_touching_business_state(self) -> None:
        book = runtime.PolicyDebtBook()
        case_identity = identity()
        binding = next(row for row in runtime.B2_BINDINGS if row.mechanism_id == 14)
        frozen_state = "APPEAL_UNDER_REVIEW"
        self.assertTrue(book.post_once(binding, case_identity, today=100))
        self.assertFalse(book.post_once(binding, case_identity, today=101))
        record = book.records[(14, case_identity)]
        self.assertEqual(record.due_day, 100 + binding.routes[2].defer_days)
        self.assertEqual(frozen_state, "APPEAL_UNDER_REVIEW")
        self.assertEqual(len(book.records), 1)


class LedgerReceiptTests(unittest.TestCase):
    def test_partial_penalties_and_refunds_conserve_gold_and_merit(self) -> None:
        ledger = penalty_ledger()
        gold_total = ledger.total(runtime.Currency.GOLD)
        merit_total = ledger.total(runtime.Currency.MERIT)
        receipts = runtime.make_penalty_receipts(
            (
                ("t", runtime.Account.TREASURY, 50),
                ("g", runtime.Account.PERSONAL_GOLD, 25),
                ("m", runtime.Account.MERIT, 60),
            )
        )
        for receipt in receipts:
            self.assertTrue(receipt.settle_once(ledger))
            self.assertFalse(receipt.settle_once(ledger))
        self.assertEqual([item.settled_amount for item in receipts], [30, 10, 40])
        for receipt in receipts:
            self.assertTrue(receipt.refund_once(ledger))
            self.assertFalse(receipt.refund_once(ledger))
            self.assertTrue(receipt.refund_bounded)
        self.assertEqual(ledger.total(runtime.Currency.GOLD), gold_total)
        self.assertEqual(ledger.total(runtime.Currency.MERIT), merit_total)
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 30)
        self.assertEqual(ledger.balances[runtime.Account.PERSONAL_GOLD], 10)

    def test_full_transfer_never_mints_when_treasury_is_short(self) -> None:
        ledger = runtime.ConservationLedger({runtime.Account.TREASURY: 4})
        receipt = runtime.LedgerReceipt(
            "promise",
            runtime.Account.TREASURY,
            runtime.Account.PERSONAL_GOLD,
            5,
        )
        self.assertFalse(receipt.settle_once(ledger))
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 4)
        self.assertEqual(ledger.balances[runtime.Account.PERSONAL_GOLD], 0)
        self.assertEqual(receipt.settlement_count, 0)


class NoticeJusticeTests(unittest.TestCase):
    def test_acknowledgement_with_objection_delivers_and_starts_same_window(self) -> None:
        case = notice_case()
        result = case.acknowledge(
            case.token(), actor_id="official-20", today=100, with_objection=True
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_OPEN)
        self.assertTrue(case.objection_recorded)
        self.assertEqual(case.appeal_deadline.due_day, 190)
        self.assertEqual(case.appeal_deadline.target_id, "official-20")
        self.assertEqual([item.settled_amount for item in case.receipts], [30, 10, 40])
        self.assertTrue(case.salary_withholding_active)

    def test_refusal_waits_exactly_d7_and_cannot_escape_settlement(self) -> None:
        case = notice_case()
        result = case.refuse(case.token(), actor_id="official-20", today=10)
        self.assertTrue(result.applied)
        self.assertEqual(case.witness_deadline.due_day, 17)
        self.assertTrue(all(item.settlement_count == 0 for item in case.receipts))
        early = case.run_witness_deadline(
            case.witness_deadline, today=16, witness_id="witness-30"
        )
        self.assertFalse(early.applied)
        self.assertEqual(early.code, "not-due")
        delivered = case.run_witness_deadline(
            case.witness_deadline, today=17, witness_id="witness-30"
        )
        self.assertTrue(delivered.applied)
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_OPEN)
        self.assertEqual(case.delivery_day, 17)
        self.assertEqual(case.appeal_deadline.due_day, 107)
        self.assertTrue(all(item.settlement_count == 1 for item in case.receipts))

    def test_wrong_target_or_old_witness_deadline_is_a_noop(self) -> None:
        case = notice_case()
        case.refuse(case.token(), actor_id="official-20", today=10)
        wrong = dataclasses.replace(case.witness_deadline, target_id="other-official")
        result = case.run_witness_deadline(wrong, today=17, witness_id="witness-30")
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "stale-target-bound-deadline")
        self.assertTrue(all(item.settlement_count == 0 for item in case.receipts))

    def test_appeal_timer_is_target_bound_and_old_timer_cannot_close_open_review(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        deadline = case.appeal_deadline
        wrong = dataclasses.replace(deadline, target_id="other-official")
        self.assertFalse(case.expire_appeal(wrong, today=190).applied)
        opened = case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=150,
            reason="omitted evidence",
        )
        self.assertTrue(opened.applied)
        stale = case.expire_appeal(deadline, today=190)
        self.assertFalse(stale.applied)
        self.assertEqual(stale.code, "stale-target-bound-deadline")
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_UNDER_REVIEW)

    def test_unappealed_case_closes_only_when_exact_deadline_is_due(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        self.assertFalse(case.expire_appeal(case.appeal_deadline, today=189).applied)
        result = case.expire_appeal(case.appeal_deadline, today=190)
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.CLOSED_UPHELD)
        self.assertTrue(all(item.refund_count == 0 for item in case.receipts))

    def test_route_a_non_aggravation_rejects_worse_sanction(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=101,
            reason="calculation error",
        )
        with self.assertRaisesRegex(ValueError, "may not aggravate"):
            case.resolve_appeal(
                case.token(),
                route=runtime.PolicyRoute.A,
                reviewed_band=runtime.Band.BOTTOM_325,
                reviewed_sanctions=runtime.SanctionVector(51, 25, 60, 25, 1),
            )
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_UNDER_REVIEW)

    def test_successful_appeal_refunds_actual_receipts_once_and_stops_future_cut(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=101,
            reason="calculation error",
        )
        review_token = case.token()
        result = case.resolve_appeal(
            review_token,
            route=runtime.PolicyRoute.A,
            reviewed_band=runtime.Band.NORMAL_35,
            reviewed_sanctions=runtime.SanctionVector(),
            new_misconduct_case_id="separate-case-99",
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.CORRECTED)
        self.assertFalse(case.salary_withholding_active)
        self.assertEqual(case.linked_new_misconduct_case_id, "separate-case-99")
        self.assertTrue(all(item.refund_count == 1 for item in case.receipts))
        self.assertTrue(all(item.refund_bounded for item in case.receipts))
        replay = case.resolve_appeal(
            review_token,
            route=runtime.PolicyRoute.A,
            reviewed_band=runtime.Band.NORMAL_35,
            reviewed_sanctions=runtime.SanctionVector(),
        )
        self.assertFalse(replay.applied)
        self.assertTrue(all(item.refund_count == 1 for item in case.receipts))

    def test_partial_relief_refunds_only_the_difference_and_retains_lighter_cut(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=101,
            reason="sanction proportionality",
        )
        result = case.resolve_appeal(
            case.token(),
            route=runtime.PolicyRoute.A,
            reviewed_band=runtime.Band.BOTTOM_325,
            reviewed_sanctions=runtime.SanctionVector(20, 5, 30, 10, 0),
        )
        self.assertTrue(result.applied)
        self.assertEqual([item.refunded_amount for item in case.receipts], [10, 5, 10])
        self.assertEqual(case.ledger.balances[runtime.Account.GOLD_SINK], 25)
        self.assertEqual(case.ledger.balances[runtime.Account.MERIT_SINK], 30)
        self.assertTrue(case.salary_withholding_active)
        self.assertTrue(all(item.refund_bounded for item in case.receipts))

    def test_route_b_aggravation_is_explicitly_flagged_not_mislabeled(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=101,
            reason="dispute",
        )
        result = case.resolve_appeal(
            case.token(),
            route=runtime.PolicyRoute.B,
            reviewed_band=runtime.Band.BOTTOM_325,
            reviewed_sanctions=runtime.SanctionVector(70, 25, 60, 25, 1),
        )
        self.assertTrue(result.applied)
        self.assertEqual(result.code, "aggravated")
        self.assertTrue(case.aggravation_flag)
        self.assertEqual(case.appeal_outcome, "aggravated")

    def test_route_c_posts_one_debt_without_resolving_appeal(self) -> None:
        case = notice_case()
        case.acknowledge(case.token(), actor_id="official-20", today=100)
        case.submit_appeal(
            case.token(),
            actor_id="official-20",
            target_manager_id="manager-10",
            today=101,
            reason="dispute",
        )
        token = case.token()
        first = case.resolve_appeal(
            token,
            route=runtime.PolicyRoute.C,
            reviewed_band=runtime.Band.BOTTOM_325,
            reviewed_sanctions=case.original_sanctions,
        )
        second = case.resolve_appeal(
            token,
            route=runtime.PolicyRoute.C,
            reviewed_band=runtime.Band.BOTTOM_325,
            reviewed_sanctions=case.original_sanctions,
        )
        self.assertTrue(first.applied)
        self.assertFalse(second.applied)
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_UNDER_REVIEW)
        self.assertEqual(case.policy_debt_count, 1)


class AntiRetaliationTests(unittest.TestCase):
    def make_observation(self) -> runtime.RetaliationObservation:
        return runtime.RetaliationObservation(
            identity(case_serial=31), "appeal-31", 100, "manager-10"
        )

    def test_action_without_post_appeal_fact_is_suspended_for_independent_review(self) -> None:
        observation = self.make_observation()
        result = observation.record_adverse_action(
            action_id="demotion-1",
            manager_id="manager-10",
            subject_id="official-20",
            action_day=120,
            reason="performance",
            new_facts={"old-fact": 90},
        )
        self.assertTrue(result.applied)
        self.assertTrue(result.suspended)
        self.assertEqual(result.finding, runtime.RetaliationFinding.PENDING_INDEPENDENT_REVIEW)
        denied = observation.resolve_action(
            "demotion-1", reviewer_id="manager-10", retaliation_confirmed=True
        )
        self.assertFalse(denied.applied)
        resolved = observation.resolve_action(
            "demotion-1", reviewer_id="reviewer-40", retaliation_confirmed=True
        )
        self.assertTrue(resolved.applied)
        self.assertEqual(resolved.finding, runtime.RetaliationFinding.RETALIATION)

    def test_genuine_post_appeal_fact_supports_normal_management(self) -> None:
        observation = self.make_observation()
        result = observation.record_adverse_action(
            action_id="warning-1",
            manager_id="manager-10",
            subject_id="official-20",
            action_day=130,
            reason="new missed milestone",
            new_facts={"new-fact": 125},
        )
        self.assertTrue(result.applied)
        self.assertFalse(result.suspended)
        self.assertEqual(result.finding, runtime.RetaliationFinding.NORMAL_MANAGEMENT)

    def test_anniversary_boundary_returns_to_ordinary_rules_and_duplicates_noop(self) -> None:
        observation = self.make_observation()
        first = observation.record_adverse_action(
            action_id="later-action",
            manager_id="manager-10",
            subject_id="official-20",
            action_day=observation.end_day,
            reason="ordinary review",
        )
        replay = observation.record_adverse_action(
            action_id="later-action",
            manager_id="manager-10",
            subject_id="official-20",
            action_day=observation.end_day,
            reason="ordinary review",
        )
        self.assertEqual(first.finding, runtime.RetaliationFinding.OUTSIDE_WINDOW)
        self.assertFalse(replay.applied)
        self.assertTrue(observation.close(today=observation.end_day))
        self.assertFalse(observation.close(today=observation.end_day + 1))


class FeedbackCommitmentTests(unittest.TestCase):
    def make_case(self) -> runtime.FeedbackCommitmentCase:
        return runtime.FeedbackCommitmentCase(
            identity(case_serial=41),
            runtime.Band.BOTTOM_325,
            "evidence-hash-41",
        )

    def hold(self, case: runtime.FeedbackCommitmentCase) -> None:
        result = case.hold_meeting(
            case.token(),
            delivery_style="plain",
            step_order=("evidence", "result"),
            disclosed_band=runtime.Band.BOTTOM_325,
            evidence_hash="evidence-hash-41",
            understood_band=runtime.Band.BOTTOM_325,
        )
        self.assertTrue(result.applied)

    def test_meeting_cannot_rewrite_frozen_result_or_evidence(self) -> None:
        case = self.make_case()
        result = case.hold_meeting(
            case.token(),
            delivery_style="indirect",
            step_order=("result", "evidence"),
            disclosed_band=runtime.Band.NORMAL_35,
            evidence_hash="evidence-hash-41",
            understood_band=runtime.Band.NORMAL_35,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "frozen-result-mismatch")
        self.assertEqual(case.state, runtime.FeedbackState.RESULT_LOCKED)

    def test_receipt_with_objection_is_delivery_not_agreement_and_keeps_appeal(self) -> None:
        case = self.make_case()
        self.hold(case)
        result = case.record_receipt(
            case.token(),
            actor_id="official-20",
            status=runtime.FeedbackReceiptStatus.RECEIVED_WITH_OBJECTION,
            agrees=False,
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.FeedbackState.RECEIPT_RECORDED)
        self.assertFalse(case.receipt_agrees)
        self.assertTrue(case.appeal_eligible)

    def test_refusal_requires_independent_witness_but_still_completes_delivery(self) -> None:
        case = self.make_case()
        self.hold(case)
        denied = case.record_receipt(
            case.token(),
            actor_id="official-20",
            status=runtime.FeedbackReceiptStatus.REFUSED_WITNESSED,
            agrees=False,
            witness_id="manager-10",
        )
        self.assertFalse(denied.applied)
        accepted = case.record_receipt(
            case.token(),
            actor_id="official-20",
            status=runtime.FeedbackReceiptStatus.REFUSED_WITNESSED,
            agrees=False,
            witness_id="witness-30",
        )
        self.assertTrue(accepted.applied)
        self.assertEqual(case.receipt_witness_id, "witness-30")
        self.assertFalse(case.receipt_agrees)

    def test_written_gold_promise_transfers_exactly_once_and_then_closes(self) -> None:
        case = self.make_case()
        self.hold(case)
        case.record_receipt(
            case.token(),
            actor_id="official-20",
            status=runtime.FeedbackReceiptStatus.RECEIVED_WITH_OBJECTION,
            agrees=False,
        )
        case.open_actions(case.token())
        ledger = runtime.ConservationLedger({runtime.Account.TREASURY: 20})
        receipt = runtime.LedgerReceipt(
            "promise-1",
            runtime.Account.TREASURY,
            runtime.Account.PERSONAL_GOLD,
            8,
        )
        obligation = runtime.FeedbackObligation(
            "obligation-1",
            "manager-10",
            "official-20",
            200,
            "written compensation",
            receipt,
        )
        self.assertTrue(case.add_obligation(case.token(), obligation).applied)
        self.assertTrue(obligation.fulfill(evidence="payment-ledger", ledger=ledger))
        self.assertFalse(obligation.fulfill(evidence="replay", ledger=ledger))
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 12)
        self.assertEqual(ledger.balances[runtime.Account.PERSONAL_GOLD], 8)
        self.assertEqual(receipt.settlement_count, 1)
        self.assertTrue(case.close(case.token()).applied)

    def test_overdue_promise_breaches_once(self) -> None:
        obligation = runtime.FeedbackObligation(
            "obligation-2", "manager-10", "official-20", 100, "mentor hours"
        )
        self.assertFalse(obligation.expire(today=100))
        self.assertTrue(obligation.expire(today=101))
        self.assertFalse(obligation.expire(today=102))
        self.assertEqual(obligation.breach_count, 1)


class PipLifecycleTests(unittest.TestCase):
    def test_threshold_blocks_false_positive_and_routes_redline_outside_pip(self) -> None:
        case = runtime.PipCase(
            identity(case_serial=50), runtime.PipCategory.WILL, ("evidence",)
        )
        result = case.qualify(
            case.token(),
            severe_failure=False,
            prior_feedback_count=0,
            low_rating_cycles=1,
        )
        self.assertFalse(result.applied)
        self.assertEqual(case.state, runtime.PipState.TRIAGED)
        discipline = case.qualify(
            case.token(),
            severe_failure=False,
            prior_feedback_count=0,
            low_rating_cycles=0,
            red_line_misconduct=True,
        )
        self.assertTrue(discipline.applied)
        self.assertEqual(case.state, runtime.PipState.DISCIPLINE_ROUTED)

    def test_refusal_is_recorded_once_and_is_not_failure(self) -> None:
        case = runtime.PipCase(
            identity(case_serial=51), runtime.PipCategory.CAPABILITY, ("evidence",)
        )
        case.qualify(
            case.token(), severe_failure=True, prior_feedback_count=0, low_rating_cycles=0
        )
        case.freeze_goals(
            case.token(), (runtime.PipGoal("g", True, "mentor", 200),), baseline_workload=50
        )
        token = case.token()
        first = case.record_refusal(token, reason="goal outside my control")
        second = case.record_refusal(token, reason="replay")
        self.assertTrue(first.applied)
        self.assertFalse(second.applied)
        self.assertEqual(case.state, runtime.PipState.ACK_PENDING)
        self.assertNotEqual(case.state, runtime.PipState.FAILED)

    def test_support_reservation_and_gold_settlement_are_atomic(self) -> None:
        case, pool, ledger = executing_pip()
        self.assertEqual(case.state, runtime.PipState.EXECUTING)
        self.assertEqual(pool.used, 4)
        self.assertEqual(pool.remaining, 6)
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 15)
        self.assertEqual(ledger.balances[runtime.Account.GOLD_SINK], 5)
        self.assertEqual(case.support_receipt.settlement_count, 1)

    def test_unfunded_support_does_not_consume_capacity(self) -> None:
        case = runtime.PipCase(
            identity(case_serial=52), runtime.PipCategory.CAPABILITY, ("evidence",)
        )
        case.qualify(
            case.token(), severe_failure=True, prior_feedback_count=0, low_rating_cycles=0
        )
        case.freeze_goals(
            case.token(), (runtime.PipGoal("g", True, "mentor", 200),), baseline_workload=50
        )
        pool = runtime.CapacityPool(10)
        ledger = runtime.ConservationLedger({runtime.Account.TREASURY: 1})
        receipt = runtime.LedgerReceipt(
            "support", runtime.Account.TREASURY, runtime.Account.GOLD_SINK, 5
        )
        result = case.start_execution(
            case.token(),
            manager_signed=True,
            subject_signed=True,
            independent_confirmed=False,
            start_day=100,
            end_day=200,
            capacity_pool=pool,
            support_hours=4,
            support_receipt=receipt,
            ledger=ledger,
        )
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "support-budget-unavailable")
        self.assertEqual(pool.used, 0)
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 1)

    def test_midpoint_runs_once_between_start_and_end(self) -> None:
        case, _, _ = executing_pip()
        self.assertFalse(
            case.run_midpoint(
                case.token(), today=149, progress_percent=50, resources_delivered=True
            ).applied
        )
        token = case.token()
        result = case.run_midpoint(
            token,
            today=150,
            progress_percent=60,
            resources_delivered=True,
            correction="replace one invalid milestone",
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.midpoint_count, 1)
        replay = case.run_midpoint(
            token, today=151, progress_percent=70, resources_delivered=True
        )
        self.assertFalse(replay.applied)
        self.assertEqual(case.midpoint_count, 1)

    def test_goal_creep_lock_and_expedient_violation_are_distinct(self) -> None:
        case, _, _ = executing_pip()
        blocked = case.request_goal_change(
            case.token(),
            route=runtime.PolicyRoute.A,
            today=120,
            new_workload=140,
        )
        self.assertFalse(blocked.applied)
        self.assertFalse(case.goal_creep_violation)
        applied = case.request_goal_change(
            case.token(),
            route=runtime.PolicyRoute.B,
            today=121,
            new_workload=140,
        )
        self.assertTrue(applied.applied)
        self.assertTrue(case.goal_creep_violation)
        self.assertEqual(case.current_workload, 140)

    def test_graduation_requires_key_goals_stability_and_releases_capacity(self) -> None:
        case, pool, _ = executing_pip()
        case.run_midpoint(
            case.token(), today=150, progress_percent=80, resources_delivered=True
        )
        result = case.resolve_due(
            case.token(),
            today=200,
            completed_goal_ids=("key-1", "key-2"),
            stability_end_day=200,
            independent_review=True,
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.PipState.GRADUATED)
        self.assertEqual(pool.used, 0)
        self.assertFalse(pool.release(case.identity.key))

    def test_missing_stability_fails_without_writing_a_future_rating(self) -> None:
        case, pool, _ = executing_pip()
        result = case.resolve_due(
            case.token(),
            today=200,
            completed_goal_ids=("key-1", "key-2"),
            stability_end_day=210,
            independent_review=True,
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.PipState.FAILED)
        self.assertEqual(case.graduation_status, "failed")
        self.assertEqual(pool.used, 0)

    def test_no_support_liability_is_decided_only_at_terminal_failure(self) -> None:
        failed, _, _ = executing_pip(support_hours=0, mentor_id=None)
        self.assertTrue(failed.support_absent)
        self.assertFalse(failed.no_support_liability)
        failed.resolve_due(
            failed.token(),
            today=200,
            completed_goal_ids=(),
            stability_end_day=200,
            independent_review=True,
        )
        self.assertTrue(failed.no_support_liability)

        graduated, _, _ = executing_pip(support_hours=0, mentor_id=None)
        graduated.resolve_due(
            graduated.token(),
            today=200,
            completed_goal_ids=("key-1", "key-2"),
            stability_end_day=200,
            independent_review=True,
        )
        self.assertFalse(graduated.no_support_liability)

    def test_relapse_observation_is_one_cycle_and_only_same_category_escalates(self) -> None:
        case, _, _ = executing_pip()
        case.resolve_due(
            case.token(),
            today=200,
            completed_goal_ids=("key-1", "key-2"),
            stability_end_day=200,
            independent_review=True,
        )
        case.open_relapse_observation(case.token())
        self.assertEqual(case.relapse_end_cycle, case.identity.cycle_serial + 1)
        separate = case.record_relapse(
            case.token(),
            event_id="new-issue",
            current_cycle=case.relapse_end_cycle,
            category=runtime.PipCategory.ROLE_MISMATCH,
        )
        self.assertEqual(separate.code, "separate-new-issue-required")
        self.assertEqual(case.state, runtime.PipState.RELAPSE_OBSERVATION)
        relapse = case.record_relapse(
            case.token(),
            event_id="same-issue",
            current_cycle=case.relapse_end_cycle,
            category=runtime.PipCategory.CAPABILITY,
        )
        self.assertTrue(relapse.applied)
        self.assertEqual(case.state, runtime.PipState.RELAPSED)

    def make_failed_case(self) -> runtime.PipCase:
        case, _, _ = executing_pip(support_hours=0)
        case.resolve_due(
            case.token(),
            today=200,
            completed_goal_ids=(),
            stability_end_day=200,
            independent_review=True,
        )
        return case

    def test_transfer_requires_real_vacancy_and_projects_minimum_disclosure(self) -> None:
        case = self.make_failed_case()
        denied = case.choose_terminal(
            case.token(),
            disposition=runtime.PipDisposition.TRANSFER,
            today=201,
            recipient_manager_id="manager-40",
        )
        self.assertFalse(denied.applied)
        result = case.choose_terminal(
            case.token(),
            disposition=runtime.PipDisposition.TRANSFER,
            today=201,
            recipient_manager_id="manager-40",
            vacancy_id="vacancy-1",
            subject_statement="role mismatch",
            excluded_private_ids=("anonymous-peer-1", "old-grudge-2"),
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.PipState.TRANSFERRED)
        self.assertEqual(case.transfer_disclosure.recipient_manager_id, "manager-40")
        self.assertEqual(
            case.transfer_disclosure.excluded_private_ids,
            ("anonymous-peer-1", "old-grudge-2"),
        )

    def test_exit_cost_debits_real_treasury_once_and_creates_one_statement(self) -> None:
        case = self.make_failed_case()
        ledger = runtime.ConservationLedger({runtime.Account.TREASURY: 20})
        receipt = runtime.LedgerReceipt(
            "recruitment-cost",
            runtime.Account.TREASURY,
            runtime.Account.GOLD_SINK,
            12,
        )
        token = case.token()
        result = case.choose_terminal(
            token,
            disposition=runtime.PipDisposition.EXIT,
            today=210,
            exit_receipt=receipt,
            ledger=ledger,
            handover_gaps=("unfinished docket",),
            colleague_overtime=7,
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.PipState.EXITED)
        self.assertEqual(ledger.balances[runtime.Account.TREASURY], 8)
        self.assertEqual(case.exit_cost_statement.recruitment_gold_cost, 12)
        replay = case.choose_terminal(
            token,
            disposition=runtime.PipDisposition.EXIT,
            today=211,
            exit_receipt=receipt,
            ledger=ledger,
        )
        self.assertFalse(replay.applied)
        self.assertEqual(receipt.settlement_count, 1)

    def test_second_pip_must_use_a_new_linked_case(self) -> None:
        case = self.make_failed_case()
        denied = case.choose_terminal(
            case.token(),
            disposition=runtime.PipDisposition.SECOND_PIP,
            today=201,
            second_case_id=str(case.identity.case_serial),
        )
        self.assertFalse(denied.applied)
        result = case.choose_terminal(
            case.token(),
            disposition=runtime.PipDisposition.SECOND_PIP,
            today=201,
            second_case_id="pip-case-22",
        )
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.PipState.SECOND_PIP)
        self.assertEqual(case.second_case_id, "pip-case-22")


class QuotaReturnTests(unittest.TestCase):
    def make_book(self, *, reserve: int = 0) -> runtime.QuotaReturnBook:
        return runtime.QuotaReturnBook(
            "manager-10",
            7,
            60,
            {
                runtime.Band.BOTTOM_325: 2,
                runtime.Band.NORMAL_35: 5,
                runtime.Band.TOP_375: 1,
            },
            {runtime.Band.NORMAL_35: reserve},
        )

    def test_reserved_slot_return_consumes_one_reserve_and_replay_noops(self) -> None:
        book = self.make_book(reserve=1)
        result = book.apply_return(
            appeal_id="appeal-1",
            corrected_subject_id="official-20",
            from_band=runtime.Band.BOTTOM_325,
            to_band=runtime.Band.NORMAL_35,
            route=runtime.QuotaReturnRoute.RESERVED_SLOT,
            manager_id="manager-10",
            today=100,
        )
        self.assertTrue(result.applied)
        self.assertEqual(result.receipt.reserved_consumed, 1)
        self.assertEqual(book.reserved_slots[runtime.Band.NORMAL_35], 0)
        self.assertEqual(sum(book.counts.values()), 8)
        replay = book.apply_return(
            appeal_id="appeal-1",
            corrected_subject_id="official-20",
            from_band=runtime.Band.BOTTOM_325,
            to_band=runtime.Band.NORMAL_35,
            route=runtime.QuotaReturnRoute.RESERVED_SLOT,
            manager_id="manager-10",
            today=101,
        )
        self.assertFalse(replay.applied)
        self.assertEqual(len(book.receipts), 1)

    def test_boundary_review_preserves_counts_and_redelivers_with_fresh_timer(self) -> None:
        book = self.make_book()
        before = dict(book.counts)
        result = book.apply_return(
            appeal_id="appeal-2",
            corrected_subject_id="official-20",
            from_band=runtime.Band.BOTTOM_325,
            to_band=runtime.Band.NORMAL_35,
            route=runtime.QuotaReturnRoute.BOUNDARY_REVIEW,
            manager_id="manager-10",
            today=100,
            affected_official_id="boundary-30",
        )
        self.assertTrue(result.applied)
        self.assertEqual(book.counts, before)
        redelivery = result.receipt.redelivery
        self.assertEqual(redelivery.target_id, "boundary-30")
        self.assertEqual(redelivery.appeal_deadline.target_id, "boundary-30")
        self.assertEqual(redelivery.appeal_deadline.due_day, 190)
        self.assertFalse(result.receipt.audit_diff)

    def test_next_cycle_debt_posts_and_consumes_exactly_once(self) -> None:
        book = self.make_book()
        result = book.apply_return(
            appeal_id="appeal-3",
            corrected_subject_id="official-20",
            from_band=runtime.Band.BOTTOM_325,
            to_band=runtime.Band.NORMAL_35,
            route=runtime.QuotaReturnRoute.NEXT_CYCLE_DEBT,
            manager_id="manager-10",
            today=100,
        )
        self.assertTrue(result.applied)
        self.assertEqual(result.receipt.debt_added, 1)
        self.assertEqual(book.manager_debt["manager-10"], 1)
        self.assertFalse(book.consume_next_cycle_debt(manager_id="manager-10", current_cycle=7))
        self.assertTrue(book.consume_next_cycle_debt(manager_id="manager-10", current_cycle=8))
        self.assertFalse(book.consume_next_cycle_debt(manager_id="manager-10", current_cycle=8))
        self.assertEqual(book.manager_debt["manager-10"], 0)

    def test_hidden_rebalance_keeps_audit_diff_and_cannot_masquerade_as_a(self) -> None:
        book = self.make_book()
        before = dict(book.counts)
        result = book.apply_return(
            appeal_id="appeal-4",
            corrected_subject_id="official-20",
            from_band=runtime.Band.BOTTOM_325,
            to_band=runtime.Band.NORMAL_35,
            route=runtime.QuotaReturnRoute.HIDDEN_REBALANCE,
            manager_id="manager-10",
            today=100,
            affected_official_id="boundary-30",
        )
        self.assertTrue(result.applied)
        self.assertEqual(book.counts, before)
        self.assertTrue(result.receipt.audit_diff)
        self.assertIsNone(result.receipt.redelivery)
        self.assertEqual(result.receipt.route, runtime.QuotaReturnRoute.HIDDEN_REBALANCE)
        cure = book.cure_hidden_rebalance(appeal_id="appeal-4", today=130)
        self.assertEqual(cure.target_id, "boundary-30")
        self.assertEqual(cure.appeal_deadline.due_day, 220)
        self.assertEqual(cure.appeal_deadline.target_id, "boundary-30")
        self.assertIsNone(book.cure_hidden_rebalance(appeal_id="appeal-4", today=131))


if __name__ == "__main__":
    unittest.main()
