#!/usr/bin/env python3
"""Unit tests for the first v0.4 domain-runtime source/model."""

from __future__ import annotations

import dataclasses
import unittest

import zg361_phase2_runtime_data as runtime


def make_case() -> runtime.NoticeCase:
    return runtime.NoticeCase(
        owner_id="manager-10",
        subject_id="official-20",
        cycle_serial=7,
        case_serial=3,
        receipts=runtime.make_receipts(
            (
                ("treasury", "local_treasury", 50),
                ("gold", "personal_gold", 25),
                ("merit", "merit", 60),
            )
        ),
    )


class RuntimeSpecTests(unittest.TestCase):
    def test_first_slice_has_exactly_four_mechanisms(self) -> None:
        self.assertEqual(set(runtime.PHASE2_RUNTIME_SPECS), {"001", "018", "069", "357"})

    def test_all_readiness_labels_remain_honestly_partial(self) -> None:
        for spec in runtime.PHASE2_RUNTIME_SPECS.values():
            self.assertEqual(spec.domain_runtime, "partial")
            self.assertEqual(spec.player_visible_loop, "partial")
            self.assertEqual(spec.runtime_evidence, "static-ready")

    def test_every_spec_binds_owner_subject_cycle_case_hook_state_feedback(self) -> None:
        for spec in runtime.PHASE2_RUNTIME_SPECS.values():
            self.assertTrue(spec.owner_binding)
            self.assertTrue(spec.subject_binding)
            self.assertTrue(spec.cycle_binding)
            self.assertTrue(spec.case_binding)
            self.assertTrue(spec.hook)
            self.assertTrue(spec.states)
            self.assertTrue(spec.feedback)

    def test_spec_validator_rejects_readiness_inflation(self) -> None:
        specs = dict(runtime.PHASE2_RUNTIME_SPECS)
        specs["001"] = dataclasses.replace(specs["001"], runtime_evidence="fixture-live")
        with self.assertRaisesRegex(ValueError, "overstates runtime readiness"):
            runtime.validate_runtime_specs(specs)


class PermissionTests(unittest.TestCase):
    def test_celestial_player_duke_or_above_can_manage(self) -> None:
        permission = runtime.PHASE2_PERMISSION_CONTRACT
        for rank in (runtime.TitleRank.DUKE, runtime.TitleRank.KING, runtime.TitleRank.EMPEROR):
            self.assertTrue(
                permission.can_manage(
                    route=runtime.ActorRoute.PLAYER,
                    title_rank=rank,
                    is_celestial=True,
                )
            )

    def test_authorized_ai_duke_or_above_can_manage(self) -> None:
        self.assertTrue(
            runtime.PHASE2_PERMISSION_CONTRACT.can_manage(
                route=runtime.ActorRoute.AI,
                title_rank=runtime.TitleRank.DUKE,
                is_celestial=True,
            )
        )

    def test_count_and_baron_cannot_manage(self) -> None:
        permission = runtime.PHASE2_PERMISSION_CONTRACT
        for route in runtime.ActorRoute:
            for rank in (runtime.TitleRank.BARON, runtime.TitleRank.COUNT):
                self.assertFalse(
                    permission.can_manage(route=route, title_rank=rank, is_celestial=True)
                )

    def test_non_celestial_or_unlanded_duke_cannot_manage(self) -> None:
        permission = runtime.PHASE2_PERMISSION_CONTRACT
        self.assertFalse(
            permission.can_manage(
                route=runtime.ActorRoute.PLAYER,
                title_rank=runtime.TitleRank.DUKE,
                is_celestial=False,
            )
        )
        self.assertFalse(
            permission.can_manage(
                route=runtime.ActorRoute.AI,
                title_rank=runtime.TitleRank.DUKE,
                is_celestial=True,
                is_landed=False,
            )
        )

    def test_subject_can_act_only_on_own_case(self) -> None:
        permission = runtime.PHASE2_PERMISSION_CONTRACT
        self.assertTrue(permission.can_act_on_subject_case(actor_id="c1", subject_id="c1"))
        self.assertFalse(permission.can_act_on_subject_case(actor_id="c1", subject_id="c2"))


class KpiAndGradeTests(unittest.TestCase):
    def test_kpi_contract_has_exactly_eight_named_components(self) -> None:
        self.assertEqual(
            runtime.KPI_COMPONENT_KEYS,
            (
                "governance",
                "capability",
                "growth",
                "superior",
                "values",
                "collaboration",
                "jingcha",
                "organization",
            ),
        )

    def test_eight_kpi_components_sum_algebraically(self) -> None:
        sheet = runtime.KpiBreakdown(100, 40, -20, 10, -60, 5, -50, 7)
        self.assertEqual(sheet.total, 32)
        self.assertEqual(len(sheet.as_dict()), 8)

    def test_absolute_grade_boundaries(self) -> None:
        vectors = (
            (50, runtime.Grade.TOP_375),
            (49, runtime.Grade.NORMAL_35),
            (0, runtime.Grade.NORMAL_35),
            (-1, runtime.Grade.BOTTOM_325),
        )
        for total, expected in vectors:
            with self.subTest(total=total):
                self.assertEqual(runtime.absolute_grade_for_kpi(total), expected)

    def test_quota_c_keeps_absolute_fact_and_records_forced_down_reason(self) -> None:
        decision = runtime.resolve_final_grade(
            absolute_grade=runtime.Grade.NORMAL_35,
            quota_grade=runtime.Grade.BOTTOM_325,
        )
        self.assertEqual(decision.absolute_grade, runtime.Grade.NORMAL_35)
        self.assertEqual(decision.final_grade, runtime.Grade.BOTTOM_325)
        self.assertEqual(decision.reason, runtime.FinalGradeReason.QUOTA_C)
        self.assertTrue(decision.forced_down)

    def test_matching_absolute_and_final_grade_has_absolute_reason(self) -> None:
        decision = runtime.resolve_final_grade(
            absolute_grade=runtime.Grade.TOP_375,
            quota_grade=runtime.Grade.TOP_375,
        )
        self.assertEqual(decision.reason, runtime.FinalGradeReason.ABSOLUTE_BAND)
        self.assertFalse(decision.forced_down)

    def test_newcomer_protection_turns_proposed_c_into_normal(self) -> None:
        decision = runtime.resolve_final_grade(
            absolute_grade=runtime.Grade.BOTTOM_325,
            quota_grade=runtime.Grade.BOTTOM_325,
            newcomer_protected=True,
        )
        self.assertEqual(decision.final_grade, runtime.Grade.NORMAL_35)
        self.assertEqual(decision.reason, runtime.FinalGradeReason.NEWCOMER_PROTECTION)

    def test_newcomer_protection_requires_a_proposed_c(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a proposed quota C"):
            runtime.resolve_final_grade(
                absolute_grade=runtime.Grade.NORMAL_35,
                quota_grade=runtime.Grade.NORMAL_35,
                newcomer_protected=True,
            )

    def test_calibration_promotion_is_an_explicit_final_reason(self) -> None:
        decision = runtime.resolve_final_grade(
            absolute_grade=runtime.Grade.NORMAL_35,
            quota_grade=runtime.Grade.BOTTOM_325,
            calibrated_grade=runtime.Grade.NORMAL_35,
        )
        self.assertEqual(decision.final_grade, runtime.Grade.NORMAL_35)
        self.assertEqual(decision.reason, runtime.FinalGradeReason.CALIBRATION_PROMOTION)

    def test_calibration_demotion_is_an_explicit_final_reason(self) -> None:
        decision = runtime.resolve_final_grade(
            absolute_grade=runtime.Grade.TOP_375,
            quota_grade=runtime.Grade.NORMAL_35,
            calibrated_grade=runtime.Grade.BOTTOM_325,
        )
        self.assertEqual(decision.final_grade, runtime.Grade.BOTTOM_325)
        self.assertEqual(decision.reason, runtime.FinalGradeReason.CALIBRATION_DEMOTION)

    def test_calibration_cannot_bypass_newcomer_protection(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot bypass"):
            runtime.resolve_final_grade(
                absolute_grade=runtime.Grade.BOTTOM_325,
                quota_grade=runtime.Grade.BOTTOM_325,
                newcomer_protected=True,
                calibrated_grade=runtime.Grade.BOTTOM_325,
            )

    def test_small_cohort_neutralization_is_not_mislabeled_as_quota(self) -> None:
        for absolute in (runtime.Grade.BOTTOM_325, runtime.Grade.TOP_375):
            with self.subTest(absolute=absolute):
                decision = runtime.resolve_final_grade(
                    absolute_grade=absolute,
                    quota_grade=runtime.Grade.NORMAL_35,
                    small_cohort_neutral=True,
                )
                self.assertEqual(decision.final_grade, runtime.Grade.NORMAL_35)
                self.assertEqual(
                    decision.reason, runtime.FinalGradeReason.SMALL_COHORT_NEUTRAL
                )

    def test_small_cohort_neutralization_requires_a_35_proposal(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires final proposal 3.5"):
            runtime.resolve_final_grade(
                absolute_grade=runtime.Grade.TOP_375,
                quota_grade=runtime.Grade.TOP_375,
                small_cohort_neutral=True,
            )


class ReceiptTests(unittest.TestCase):
    def test_receipt_settles_only_once(self) -> None:
        receipt = runtime.Receipt("g", "gold", 25)
        self.assertTrue(receipt.settle_once())
        self.assertFalse(receipt.settle_once())
        self.assertEqual(receipt.settlement_count, 1)

    def test_receipt_refunds_only_once_and_only_after_settlement(self) -> None:
        receipt = runtime.Receipt("g", "gold", 25)
        self.assertFalse(receipt.refund_once())
        receipt.settle_once()
        self.assertTrue(receipt.refund_once())
        self.assertFalse(receipt.refund_once())
        self.assertEqual(receipt.refund_count, 1)

    def test_notice_rejects_duplicate_receipt_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "receipt ids must be unique"):
            runtime.NoticeCase(
                owner_id="m",
                subject_id="s",
                cycle_serial=1,
                case_serial=1,
                receipts=[
                    runtime.Receipt("same", "gold", 1),
                    runtime.Receipt("same", "treasury", 2),
                ],
            )


class NoticeCaseTests(unittest.TestCase):
    def test_case_starts_prepared_with_unsettled_receipts(self) -> None:
        case = make_case()
        self.assertEqual(case.state, runtime.NoticeState.PREPARED)
        self.assertTrue(all(not receipt.settled for receipt in case.receipts))

    def test_acknowledgement_delivers_and_settles_every_receipt(self) -> None:
        case = make_case()
        result = case.acknowledge_delivery(case.token(), with_objection=True)
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.DELIVERED_SETTLED)
        self.assertEqual(case.delivery_method, "acknowledged_with_objection")
        self.assertTrue(all(receipt.settlement_count == 1 for receipt in case.receipts))

    def test_refusal_requires_witness_and_does_not_prematurely_settle(self) -> None:
        case = make_case()
        result = case.refuse_delivery(case.token())
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.REFUSED_PENDING_WITNESS)
        self.assertTrue(case.witness_required)
        self.assertTrue(all(receipt.settlement_count == 0 for receipt in case.receipts))

    def test_witness_service_after_refusal_reaches_same_settlement(self) -> None:
        case = make_case()
        case.refuse_delivery(case.token())
        result = case.witness_delivery(case.token())
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.DELIVERED_SETTLED)
        self.assertEqual(case.delivery_method, "witness_after_refusal")
        self.assertTrue(all(receipt.settlement_count == 1 for receipt in case.receipts))

    def test_refusal_cannot_jump_to_appeal_close_and_escape_settlement(self) -> None:
        case = make_case()
        case.refuse_delivery(case.token())
        result = case.close_appeal(case.token())
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "illegal-transition")
        self.assertEqual(case.state, runtime.NoticeState.REFUSED_PENDING_WITNESS)

    def test_closed_appeal_keeps_settled_receipts_unrefunded(self) -> None:
        case = make_case()
        case.acknowledge_delivery(case.token())
        result = case.close_appeal(case.token())
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.APPEAL_CLOSED)
        self.assertTrue(all(not receipt.refunded for receipt in case.receipts))

    def test_correction_refunds_each_settled_receipt_exactly_once(self) -> None:
        case = make_case()
        case.acknowledge_delivery(case.token())
        delivered_token = case.token()
        result = case.correct(delivered_token)
        self.assertTrue(result.applied)
        self.assertEqual(case.state, runtime.NoticeState.CORRECTED)
        self.assertTrue(all(receipt.refund_count == 1 for receipt in case.receipts))
        replay = case.correct(delivered_token)
        self.assertFalse(replay.applied)
        self.assertTrue(all(receipt.refund_count == 1 for receipt in case.receipts))

    def test_correction_before_delivery_is_a_noop(self) -> None:
        case = make_case()
        result = case.correct(case.token())
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "illegal-transition")
        self.assertTrue(all(receipt.refund_count == 0 for receipt in case.receipts))

    def test_replayed_old_state_token_is_stale_and_does_not_resettle(self) -> None:
        case = make_case()
        prepared_token = case.token()
        case.refuse_delivery(prepared_token)
        replay = case.refuse_delivery(prepared_token)
        self.assertFalse(replay.applied)
        self.assertEqual(replay.code, "stale-token")
        case.witness_delivery(case.token())
        self.assertTrue(all(receipt.settlement_count == 1 for receipt in case.receipts))

    def test_stale_owner_token_is_a_noop(self) -> None:
        case = make_case()
        token = dataclasses.replace(case.token(), owner_id="old-manager")
        result = case.acknowledge_delivery(token)
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "stale-token")
        self.assertEqual(case.state, runtime.NoticeState.PREPARED)

    def test_stale_subject_token_is_a_noop(self) -> None:
        case = make_case()
        token = dataclasses.replace(case.token(), subject_id="other-official")
        result = case.acknowledge_delivery(token)
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "stale-token")

    def test_stale_cycle_token_is_a_noop(self) -> None:
        case = make_case()
        token = dataclasses.replace(case.token(), cycle_serial=6)
        result = case.refuse_delivery(token)
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "stale-token")

    def test_stale_case_token_is_a_noop(self) -> None:
        case = make_case()
        token = dataclasses.replace(case.token(), case_serial=2)
        result = case.refuse_delivery(token)
        self.assertFalse(result.applied)
        self.assertEqual(result.code, "stale-token")

    def test_replayed_witness_delivery_cannot_double_settle(self) -> None:
        case = make_case()
        case.refuse_delivery(case.token())
        witness_token = case.token()
        case.witness_delivery(witness_token)
        replay = case.witness_delivery(witness_token)
        self.assertFalse(replay.applied)
        self.assertEqual(replay.code, "stale-token")
        self.assertTrue(all(receipt.settlement_count == 1 for receipt in case.receipts))


if __name__ == "__main__":
    unittest.main()
