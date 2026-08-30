#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic tests for the phase-two 361 career/HC reference model."""

from __future__ import annotations

import dataclasses
import unittest
from typing import Callable

import zg361_phase2_career_model as model


def identity(*, subject: str = "official-20", case_serial: int = 3) -> model.CaseIdentity:
    return model.CaseIdentity("manager-10", subject, 7, case_serial)


def promotion_slots(count: int = 2) -> model.SlotLedger:
    return model.SlotLedger.build(
        (f"promotion-{index}", model.SlotKind.PROMOTION, "department")
        for index in range(1, count + 1)
    )


def hc_board() -> model.HcBoard:
    return model.HcBoard(
        model.SlotLedger.build(
            (
                ("growth-1", model.SlotKind.GROWTH, "team-a"),
                ("backfill-1", model.SlotKind.BACKFILL, "team-a"),
                ("project-1", model.SlotKind.PROJECT, "team-a"),
                ("growth-2", model.SlotKind.GROWTH, "team-a"),
                ("growth-3", model.SlotKind.GROWTH, "team-a"),
                ("growth-4", model.SlotKind.GROWTH, "team-a"),
            )
        ),
        model.MoneyLedger(100),
        mentor_capacity=4,
    )


def eligible_case() -> model.CareerAllocationCase:
    case = model.CareerAllocationCase(
        identity(),
        titles=("d_example",),
        authority=frozenset({"old-authority"}),
    )
    result = case.evaluate_eligibility(
        case.token(),
        "eligibility-1",
        model.EligibilityEvidence(2, True, False, True, True),
    )
    if not result.applied:
        raise AssertionError(result)
    return case


def manager_case() -> model.ManagerCertification:
    return model.ManagerCertification(
        identity(),
        boundary=model.ManagerBoundary(model.TitleRank.DUKE, True, True),
    )


def nomination_book(*, quota: int = 3, exceptions: int = 1) -> model.NominationBook:
    return model.NominationBook(
        identity(),
        quota_total=quota,
        tenure_exception_total=exceptions,
    )


def packet(
    suffix: str,
    *,
    candidate: str | None = None,
    sponsor: str | None = "sponsor",
    verified: tuple[str, ...] = (),
    unverified: tuple[str, ...] = (),
) -> model.NominationPacket:
    return model.NominationPacket(
        f"packet-{suffix}",
        candidate or f"candidate-{suffix}",
        "manager-10",
        sponsor,
        "support with evidence",
        f"quota-{suffix}",
        verified_artifacts=verified,
        unverified_artifacts=unverified,
    )


def nominate(
    book: model.NominationBook,
    nomination: model.NominationPacket,
    *,
    serial: str,
) -> None:
    result = book.nominate(book.token(), serial, nomination, self_nomination=True)
    if not result.applied:
        raise AssertionError(result)


def panel_pool() -> list[model.Panelist]:
    return [
        model.Panelist("expert-a", "unit-a", model.PanelistKind.EXPERT),
        model.Panelist("expert-b", "unit-b", model.PanelistKind.EXPERT),
        model.Panelist("outside-a", "unit-c", model.PanelistKind.EXTERNAL),
        model.Panelist("outside-b", "unit-d", model.PanelistKind.EXTERNAL),
        model.Panelist(
            "conflicted",
            "unit-e",
            model.PanelistKind.EXPERT,
            frozenset({"candidate"}),
        ),
    ]


def formed_panel(*, seats: int = 4, seed: int = 9) -> model.PromotionPanel:
    result = model.PromotionPanel(identity(), candidate_id="candidate")
    result.form_panel(
        panel_pool()[:4],
        seats=seats,
        seed=seed,
        expertise_weights={model.PanelistKind.EXPERT: 60, model.PanelistKind.EXTERNAL: 40},
    )
    return result


Scenario = Callable[[unittest.TestCase], None]


def scenario_019(tc: unittest.TestCase) -> None:
    case = model.CareerAllocationCase(identity(), titles=("d_example",))
    original_titles = case.titles
    outcome = case.evaluate_eligibility(
        case.token(),
        "m019",
        model.EligibilityEvidence(2, True, False, False, True),
        sponsor_soft_skips=("tenure",),
    )
    tc.assertTrue(outcome.applied)
    tc.assertEqual(case.titles, original_titles)
    blocked = model.CareerAllocationCase(identity(case_serial=19))
    with tc.assertRaises(model.ModelRed) as caught:
        blocked.evaluate_eligibility(
            blocked.token(),
            "m019-hard",
            model.EligibilityEvidence(2, True, True, True, True),
            sponsor_soft_skips=("active_pip",),
        )
    tc.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)


def scenario_020(tc: unittest.TestCase) -> None:
    case = eligible_case()
    slots = promotion_slots(1)
    frozen = model.PromotionPacket(
        "packet-20",
        ("governance-result", "team-impact", "method-asset"),
        72,
        18,
        ("other-unit-a", "other-unit-b"),
    )
    outcome = case.open_packet(case.token(), "m020-open", frozen, slots, "promotion-1")
    tc.assertTrue(outcome.applied)
    tc.assertEqual(frozen.score, 90)
    tc.assertEqual(slots.count(model.SlotState.RESERVED), 1)
    settled = case.settle_packet(
        case.token(),
        "m020-settle",
        outcome="deferred",
        earliest_retry_day=400,
    )
    tc.assertTrue(settled.applied)
    tc.assertEqual(case.packet_terminal, "deferred")
    tc.assertEqual(case.deferred_until, 400)


def scenario_021(tc: unittest.TestCase) -> None:
    case = model.CareerAllocationCase(identity(), personal_gold=5, salary_percent=20)
    budget = model.MoneyLedger(100)
    result = case.award_bonus_and_salary(
        case.token(),
        "m021",
        budget,
        reservation_id="bonus-cycle-7",
        bonus=30,
        salary_delta_percent=10,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual((budget.available, budget.spent, case.personal_gold), (70, 30, 35))
    tc.assertEqual(case.salary_percent, 25)
    budget.assert_conserved()


def scenario_022(tc: unittest.TestCase) -> None:
    board = hc_board()
    tc.assertEqual(
        {slot.kind for slot in board.ledger.slots.values()},
        {model.SlotKind.GROWTH, model.SlotKind.BACKFILL, model.SlotKind.PROJECT},
    )
    board.convert_project_to_growth("project-1", defended=True)
    board.assert_hc_conserved()
    tc.assertFalse(model.ManagerBoundary(model.TitleRank.COUNT, True, True).can_manage)
    with tc.assertRaises(model.ModelRed) as caught:
        model.ManagerBoundary(model.TitleRank.BARON, True, True).require_manager()
    tc.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)


def scenario_023(tc: unittest.TestCase) -> None:
    case = model.CareerAllocationCase(identity())
    first = case.record_hc_defense(
        case.token(),
        "m023",
        year=1066,
        jingcha_treasury_delta=0,
        jingcha_personal_delta=0,
    )
    tc.assertTrue(first.applied)
    duplicate = case.record_hc_defense(
        case.token(),
        "m023",
        year=1066,
        jingcha_treasury_delta=0,
        jingcha_personal_delta=0,
    )
    tc.assertFalse(duplicate.applied)
    tc.assertEqual(duplicate.code, model.NoOpCode.DUPLICATE_ACTION.value)
    with tc.assertRaises(model.ModelRed):
        case.record_hc_defense(
            case.token(),
            "m023-paid",
            year=1067,
            jingcha_treasury_delta=-1,
            jingcha_personal_delta=0,
        )


def scenario_024(tc: unittest.TestCase) -> None:
    case = model.CareerAllocationCase(identity())
    case.assign_cohort_once(7, "old-team")
    case.accept_transfer_next_cycle(legal_position=True, new_team_id="new-team")
    tc.assertEqual(case.cohort_by_cycle, {7: "old-team", 8: "new-team"})
    with tc.assertRaises(model.ModelRed):
        case.assign_cohort_once(7, "rewritten-team")


def scenario_025(tc: unittest.TestCase) -> None:
    offer = model.TalentOffer(
        "offer-25",
        "star",
        "poaching-lord",
        "legal-office",
        20,
        500,
        True,
        2,
        True,
    )
    offer.resolve(model.OfferState.ACCEPTED)
    tc.assertEqual(offer.state, model.OfferState.ACCEPTED)
    with tc.assertRaises(model.ModelRed):
        offer.resolve(model.OfferState.REJECTED)
    with tc.assertRaises(model.ModelRed):
        model.TalentOffer("bad", "ordinary", "payer", "no-vacancy", 1, 2, False, 2, True)


def scenario_092(tc: unittest.TestCase) -> None:
    expert = model.CareerProfile("star", ("d_star",), pay=10)
    expert.choose_track(model.CareerTrack.EXPERT)
    tc.assertFalse(model.MANAGER_AUTHORITIES.intersection(expert.authority))
    expert.choose_track(model.CareerTrack.MANAGER, manager_training_cost=30)
    tc.assertTrue(model.MANAGER_AUTHORITIES.issubset(expert.authority))
    tc.assertEqual(expert.delivery_capacity, 70)


def scenario_093(tc: unittest.TestCase) -> None:
    profile = model.CareerProfile("manager", ("d_landed",), professional_level="L2")
    profile.choose_track(model.CareerTrack.MANAGER, manager_training_cost=20)
    titles_before = profile.titles
    profile.return_to_expert(retry_day=800)
    tc.assertEqual(profile.track, model.CareerTrack.EXPERT)
    tc.assertFalse(model.MANAGER_AUTHORITIES.intersection(profile.authority))
    tc.assertEqual(profile.titles, titles_before)


def scenario_094(tc: unittest.TestCase) -> None:
    profile = model.CareerProfile("expert", ("d_landed",), professional_level="L1", pay=10)
    profile.advance_micro_level(pay_delta=2, authority_grants=("review-method",))
    tc.assertEqual((profile.professional_level, profile.pay), ("L1.5", 12))
    tc.assertEqual(profile.titles, ("d_landed",))
    profile.grant_empty_micro_title()
    tc.assertEqual(profile.title_inflation_debt, 1)


def scenario_095(tc: unittest.TestCase) -> None:
    profile = model.CareerProfile("duke", ("d_landed",))
    profile.choose_track(model.CareerTrack.MANAGER)
    profile.annual_management_review(
        model.ManagerBoundary(model.TitleRank.DUKE, True, True),
        year=1066,
        outcome="tighten_budget",
    )
    tc.assertNotIn("allocate_hc", profile.authority)
    tc.assertEqual(profile.titles, ("d_landed",))
    with tc.assertRaises(model.ModelRed):
        profile.annual_management_review(
            model.ManagerBoundary(model.TitleRank.DUKE, True, True),
            year=1066,
            outcome="confirm",
        )


def scenario_096(tc: unittest.TestCase) -> None:
    book = model.PromotionSlotBook(promotion_slots(1))
    book.award("promotion-1", "candidate-a", "exceptional-96", exceptional=True)
    tc.assertEqual(book.promoted_candidates, {"candidate-a"})
    tc.assertEqual(book.future_debt, 1)
    tc.assertEqual(book.slots.count(model.SlotState.OCCUPIED), 1)
    with tc.assertRaises(model.ModelRed):
        book.award("promotion-1", "candidate-b", "exceptional-96b", exceptional=True)


def scenario_097(tc: unittest.TestCase) -> None:
    book = model.PromotionSlotBook(promotion_slots(1))
    winner = book.cross_team_calibrate(
        "promotion-1",
        {"local-first": (0, 100), "cross-team-second": (2, 80)},
        "cross-team-97",
    )
    tc.assertEqual(winner, "cross-team-second")
    tc.assertEqual(len(book.promoted_candidates), 1)


def scenario_098(tc: unittest.TestCase) -> None:
    board = hc_board()
    tc.assertEqual(len(board.ledger.slots), 6)
    board.convert_project_to_growth("project-1", defended=True)
    tc.assertEqual(board.ledger.slots["project-1"].kind, model.SlotKind.GROWTH)
    board.assert_hc_conserved()


def scenario_099(tc: unittest.TestCase) -> None:
    board = hc_board()
    tc.assertEqual(board.carryover_or_reclaim("growth-1", has_final_candidate=True), "carried-once")
    with tc.assertRaises(model.ModelRed):
        board.carryover_or_reclaim("growth-1", has_final_candidate=True)
    tc.assertEqual(board.carryover_or_reclaim("growth-2", has_final_candidate=False), "reclaimed")


def scenario_100(tc: unittest.TestCase) -> None:
    board = hc_board()
    board.freeze_except_critical(
        ("growth-1", "growth-2"),
        exception_slot_id="growth-1",
        role_id="governance-critical",
        governance_evidence=True,
    )
    tc.assertEqual(board.ledger.slots["growth-1"].state, model.SlotState.RESERVED)
    tc.assertEqual(board.ledger.slots["growth-2"].state, model.SlotState.FROZEN)
    tc.assertEqual(board.ledger.count(model.SlotState.RESERVED), 1)


def scenario_101(tc: unittest.TestCase) -> None:
    board = hc_board()
    board.recruit_workforce_mix(
        (
            ("growth-1", model.HireCandidate("mid", "midlevel", 10)),
            ("growth-2", model.HireCandidate("apprentice-a", "apprentice", 7, 1)),
            ("growth-3", model.HireCandidate("apprentice-b", "apprentice", 7, 1)),
        )
    )
    tc.assertEqual(board.external_character_growth, 3)
    tc.assertEqual(board.ledger.count(model.SlotState.OCCUPIED), 3)
    tc.assertEqual((board.budget.spent, board.mentor_capacity), (24, 2))


def scenario_102(tc: unittest.TestCase) -> None:
    board = hc_board()
    assignments = {
        slot_id: ("new-strategy" if index % 2 else "legacy")
        for index, slot_id in enumerate(board.ledger.slots)
    }
    board.zero_based_reallocate("three-year-1", assignments)
    tc.assertEqual(len(board.ledger.slots), 6)
    with tc.assertRaises(model.ModelRed):
        board.zero_based_reallocate("three-year-1", assignments)


def scenario_103(tc: unittest.TestCase) -> None:
    board = hc_board()
    board.audit_hoarded_slot("growth-1", vacancy_months=12, real_candidate=False)
    tc.assertEqual(board.ledger.slots["growth-1"].state, model.SlotState.RECLAIMED)
    tc.assertIn("hoarding:growth-1", board.audit_flags)


def scenario_104(tc: unittest.TestCase) -> None:
    board = hc_board()
    growth = board.source_mix(
        (
            ("growth-1", model.HireCandidate("new", "newcomer", 5)),
            ("growth-2", model.HireCandidate("mature", "mature", 10)),
            ("growth-3", model.HireCandidate("internal", "internal", 0)),
        ),
        internal_origin_team="origin-team",
    )
    tc.assertEqual(growth, 2)
    tc.assertEqual(len(board.backfill_by_departure), 1)


def scenario_105(tc: unittest.TestCase) -> None:
    board = hc_board()
    board.assign_backfill(
        departure_id="departure-105",
        slot_id="growth-1",
        owner_id="origin-team",
    )
    tc.assertEqual(board.backfill_by_departure["departure-105"], ("growth-1", "origin-team"))
    with tc.assertRaises(model.ModelRed):
        board.assign_backfill(
            departure_id="departure-105",
            slot_id="growth-2",
            owner_id="central",
        )


def scenario_106(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("critical-role")
    plan.label_role_and_talent(role_critical=True, person_id="replaceable-star", person_key=False)
    tc.assertTrue(plan.critical_role)
    tc.assertNotIn("replaceable-star", plan.key_talent)
    plan.label_role_and_talent(role_critical=True, person_id="unique-talent", person_key=True)
    tc.assertIn("unique-talent", plan.key_talent)


def scenario_107(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    candidate = model.SuccessionCandidate(
        "candidate",
        model.ReadinessBand.READY_TWO_YEARS,
        "mentor",
        700,
        ("acting-evidence",),
    )
    plan.set_readiness(candidate)
    with tc.assertRaises(model.ModelRed):
        plan.advance_readiness("candidate", current_day=699, goals_complete=True)
    plan.advance_readiness("candidate", current_day=700, goals_complete=True)
    tc.assertEqual(plan.candidates["candidate"].band, model.ReadinessBand.READY_NOW)


def scenario_108(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    plan.set_readiness(
        model.SuccessionCandidate("candidate", model.ReadinessBand.LONG_TERM, "mentor", 500)
    )
    trial = model.ActingTrial(
        "trial-108",
        "candidate",
        frozenset({"approve-budget"}),
        10,
        "goal-108",
        600,
    )
    plan.start_trial(trial)
    plan.settle_trial("trial-108", current_day=600, succeeded=True)
    tc.assertEqual(plan.candidates["candidate"].band, model.ReadinessBand.READY_NOW)
    tc.assertEqual(plan.trials["trial-108"].authority, frozenset())


def scenario_109(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    plan.mark_high_potential(
        "candidate",
        readers=("candidate", "manager", "skip-manager"),
        expiry_day=900,
    )
    tc.assertTrue(plan.can_read_high_potential("candidate", "candidate"))
    tc.assertFalse(plan.can_read_high_potential("candidate", "peer"))
    with tc.assertRaises(model.ModelRed) as caught:
        plan.mark_high_potential("hidden-subject", readers=("manager",), expiry_day=900)
    tc.assertEqual(caught.exception.code, model.RedCode.PRIVACY_BREACH)


def scenario_110(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    plan.freeze_performance_before_potential("high-potential-low", "3.25", 95)
    plan.freeze_performance_before_potential("steady-top", "3.75", 50)
    tc.assertEqual(plan.frozen_performance["high-potential-low"], "3.25")
    tc.assertEqual(plan.frozen_performance["steady-top"], "3.75")
    tc.assertGreater(plan.potential["high-potential-low"], plan.potential["steady-top"])


def scenario_111(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    attrition = model.AttritionCase(
        "attrition-111",
        "top-star",
        model.AttritionKind.REGRETTABLE,
        "manager",
    )
    plan.record_attrition(attrition)
    attrition.release_hc_once()
    attrition.revise_for_later_success()
    tc.assertEqual(
        attrition.history,
        [model.AttritionKind.REGRETTABLE, model.AttritionKind.MISEVALUATED],
    )
    with tc.assertRaises(model.ModelRed):
        attrition.release_hc_once()


def scenario_112(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    promise = model.StayPromise("promise-112", "money", 20, 500)
    plan.make_stay_promise(promise)
    budget = model.MoneyLedger(30)
    plan.settle_stay_promise("promise-112", budget)
    tc.assertTrue(promise.settled)
    tc.assertEqual((budget.spent, budget.available), (20, 10))
    with tc.assertRaises(model.ModelRed):
        plan.make_stay_promise(model.StayPromise("second", "authority", 1, 600))


def scenario_113(tc: unittest.TestCase) -> None:
    plan = model.SuccessionPlan("role")
    for knowledge in ("process-a", "process-b", "process-c"):
        plan.register_knowledge(knowledge, "star")
    plan.transfer_knowledge(
        "process-a",
        teacher_id="star",
        deputy_id="deputy",
        milestone_id="milestone-a",
    )
    tc.assertEqual(plan.knowledge_holders["process-a"], {"star", "deputy"})
    tc.assertEqual(plan.knowledge_coverage_percent, 33)
    with tc.assertRaises(model.ModelRed):
        plan.transfer_knowledge(
            "process-a",
            teacher_id="star",
            deputy_id="deputy-2",
            milestone_id="milestone-a",
        )


def scenario_114(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(identity(), state=model.MobilityState.FINALIST.value)
    case.identity_visible_to_origin = True
    accepted = case.accept(case.token(), "m114-accept", start_day=100)
    tc.assertTrue(accepted.applied)
    moved = case.transfer(case.token(), "m114-transfer", current_day=120)
    tc.assertTrue(moved.applied)
    tc.assertTrue(case.export_credit_settled)
    tc.assertTrue(case.backfill_settled)


def scenario_115(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(identity(), state=model.MobilityState.APPLIED.value)
    tc.assertEqual(case.anonymous_origin_view(), {"has_application": False, "applicant_id": None})
    result = case.reach_finalist(case.token(), "m115")
    tc.assertTrue(result.applied)
    tc.assertEqual(case.origin_notified_count, 1)
    tc.assertEqual(case.anonymous_origin_view()["applicant_id"], "applicant")


def scenario_116(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(
        identity(),
        state=model.MobilityState.FINALIST.value,
        identity_visible_to_origin=True,
    )
    case.accept(case.token(), "m116-accept", start_day=100)
    original_due = case.release_due_day
    case.extend_release_once(
        case.token(),
        "m116-extend",
        critical_delivery=True,
        succession_plan=True,
    )
    tc.assertEqual(case.release_due_day, original_due + 60)  # type: ignore[operator]
    with tc.assertRaises(model.ModelRed):
        case.extend_release_once(
            case.token(),
            "m116-extend-again",
            critical_delivery=True,
            succession_plan=True,
        )


def scenario_117(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(identity(), state=model.MobilityState.TRANSFERRED.value)
    case.transferred = True
    case.start_ramp_protection(case.token(), "m117", participation_percent=40)
    tc.assertEqual(case.participation_percent, 40)
    tc.assertTrue(case.protection_used_lifetime)
    case.expire_ramp_protection()
    tc.assertEqual(case.participation_percent, 100)
    with tc.assertRaises(model.ModelRed):
        case.start_ramp_protection(case.token(), "m117-again", participation_percent=50)


def scenario_118(tc: unittest.TestCase) -> None:
    result = model.MobilityCase.probation_and_bottom_quota(
        regular_count=10,
        probation_pass=(False, False),
        bottom_quota=1,
    )
    tc.assertEqual(result["regular_denominator"], 10)
    tc.assertEqual(result["regular_bottom_slots"], 1)
    tc.assertEqual(result["probation_failures"], 2)


def scenario_119(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(identity())
    case.write_hiring_quality(
        model.HiringQuality.MISPLACED,
        proposer_id="proposer",
        selector_id="selector",
        approver_id="approver",
    )
    tc.assertEqual(case.quality_outcome, model.HiringQuality.MISPLACED)
    tc.assertEqual(set(case.quality_receivers), {"proposer", "selector", "approver"})
    with tc.assertRaises(model.ModelRed):
        case.write_hiring_quality(
            model.HiringQuality.SUCCESS,
            proposer_id="proposer",
            selector_id="selector",
            approver_id="approver",
        )


def scenario_120(tc: unittest.TestCase) -> None:
    case = model.MobilityCase(identity())
    mentor = model.MentorPlan("mentor", 1, 20)
    case.assign_mentor(mentor)
    for month in (3, 6, 12):
        mentor.complete_milestone(month)
    mentor.settle_credit(independent_delivery=True)
    tc.assertTrue(all(mentor.milestones.values()))
    tc.assertTrue(mentor.credit_settled)
    with tc.assertRaises(model.ModelRed):
        mentor.complete_milestone(12)


def scenario_121(tc: unittest.TestCase) -> None:
    case = manager_case()
    result = case.start_trial(
        case.token(),
        "m121",
        team=("official-a", "official-b"),
        max_team_size=3,
        mentor_id="mentor",
        skip_reviewer_id="skip-manager",
        due_day=700,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.trial_team, ("official-a", "official-b"))
    with tc.assertRaises(model.ModelRed):
        model.ManagerCertification(
            identity(case_serial=121),
            boundary=model.ManagerBoundary(model.TitleRank.COUNT, True, True),
        )


def scenario_122(tc: unittest.TestCase) -> None:
    case = manager_case()
    case.freeze_scorecard(
        case.token(),
        "m122",
        hard_results=80,
        people_organization=60,
        values_process=90,
    )
    tc.assertEqual(case.score_weights, (40, 30, 30))
    tc.assertAlmostEqual(case.scorecard_total, 77.0)


def scenario_123(tc: unittest.TestCase) -> None:
    case = manager_case()
    case.add_subordinate_survey(model.SubordinateSurvey("credible", 100, 70, 70, 70, 70, 70, 70))
    case.add_subordinate_survey(model.SubordinateSurvey("enemy", 1, 0, 0, 0, 0, 0, 0))
    tc.assertGreater(case.credible_feedback_score, 69)
    with tc.assertRaises(model.ModelRed):
        case.add_subordinate_survey(model.SubordinateSurvey("credible", 50, 80, 80, 80, 80, 80, 80))


def scenario_124(tc: unittest.TestCase) -> None:
    case = manager_case()
    with tc.assertRaises(model.ModelRed):
        case.release_promotion()
    case.bind_successor("successor", accepted=True)
    case.release_promotion()
    tc.assertTrue(case.promotion_released)


def scenario_125(tc: unittest.TestCase) -> None:
    case = manager_case()
    result = case.settle_crisis(
        "incident-125",
        budget_hours=100,
        manager_hours=30,
        subordinate_hours=70,
        subordinate_led=True,
        succeeded=True,
    )
    tc.assertTrue(result["successor_evidence"])
    tc.assertFalse(result["opportunity_loss"])
    with tc.assertRaises(model.ModelRed):
        case.settle_crisis(
            "incident-over",
            budget_hours=100,
            manager_hours=60,
            subordinate_hours=60,
            subordinate_led=False,
            succeeded=True,
        )


def scenario_126(tc: unittest.TestCase) -> None:
    quadrants = {
        model.ManagerCertification.classify_quadrant(performance_high=True, values_high=True),
        model.ManagerCertification.classify_quadrant(performance_high=True, values_high=False),
        model.ManagerCertification.classify_quadrant(performance_high=False, values_high=True),
        model.ManagerCertification.classify_quadrant(performance_high=False, values_high=False),
    }
    tc.assertEqual(quadrants, set(model.ValuesQuadrant))


def scenario_127(tc: unittest.TestCase) -> None:
    case = manager_case()
    reports = tuple(f"report-{index}" for index in range(8))
    tc.assertEqual(case.freeze_span(reports, maximum=5), 3)
    tc.assertEqual(case.span_snapshot, reports)


def scenario_128(tc: unittest.TestCase) -> None:
    case = manager_case()
    snapshot = model.ClimateSnapshot(7, 80, 40, 30, 35, 20)
    case.record_climate(snapshot, policy="weaken-next-cycle-quota")
    tc.assertEqual(case.climate, snapshot)
    tc.assertEqual(case.next_cycle_policy, "weaken-next-cycle-quota")
    tc.assertEqual(case.identity.cycle_serial, 7)


def scenario_157(tc: unittest.TestCase) -> None:
    book = nomination_book(quota=1)
    nomination = packet("157")
    result = book.nominate(book.token(), "m157", nomination, self_nomination=True)
    tc.assertTrue(result.applied)
    tc.assertEqual(book.candidate_packets[nomination.candidate_id], nomination.packet_id)
    tc.assertEqual(book.packets[nomination.packet_id].state, model.PacketState.NOMINATED)
    blocked = nomination_book(quota=1)
    with tc.assertRaises(model.ModelRed):
        blocked.nominate(
            blocked.token(),
            "m157-no-sponsor",
            packet("no-sponsor", sponsor=None),
            self_nomination=True,
        )


def scenario_158(tc: unittest.TestCase) -> None:
    book = nomination_book(quota=3)
    nominate(book, packet("a"), serial="m158-a")
    nominate(book, packet("b"), serial="m158-b")
    book.rank_packets(("packet-b", "packet-a"))
    tc.assertEqual((book.packets["packet-b"].rank, book.packets["packet-a"].rank), (1, 2))
    book.return_unused_quota(1)
    book.assert_quota_conserved()
    tc.assertEqual((book.quota_used, book.quota_returned, book.quota_remaining), (2, 1, 0))


def scenario_159(tc: unittest.TestCase) -> None:
    book = nomination_book()
    record = model.ShelvedStar("star", "successor", 10, 500)
    book.shelve_star(record)
    tc.assertTrue(book.audit_shelving("star", current_day=501, cycle_serial=8))
    tc.assertFalse(book.audit_shelving("star", current_day=502, cycle_serial=8))
    tc.assertTrue(book.audit_shelving("star", current_day=600, cycle_serial=9))


def scenario_160(tc: unittest.TestCase) -> None:
    book = nomination_book(quota=3)
    for suffix in ("a", "b", "c"):
        nominate(book, packet(suffix), serial=f"m160-{suffix}")
    winners = book.prescreen(
        {
            "packet-a": (90, 90, 90),
            "packet-b": (80, 80, 80),
            "packet-c": (70, 70, 70),
        },
        seats=2,
    )
    tc.assertEqual(set(winners), {"packet-a", "packet-b"})
    tc.assertEqual(book.packets["packet-c"].state, model.PacketState.REJECTED)
    tc.assertEqual(book.packets["packet-c"].reason, "rubric-cut")


def scenario_161(tc: unittest.TestCase) -> None:
    book = nomination_book(quota=2)
    nominate(book, packet("main"), serial="m161-main")
    nominate(book, packet("filler"), serial="m161-filler")
    book.mark_filler("packet-filler", preparation_hours=12)
    book.identify_sham("packet-filler", "packet-main")
    tc.assertEqual(book.quota_used, 2)
    tc.assertEqual(book.packets["packet-filler"].preparation_hours, 12)
    tc.assertEqual(book.fairness_debt, 1)


def scenario_162(tc: unittest.TestCase) -> None:
    book = nomination_book(exceptions=1)
    tc.assertTrue(book.admit_tenure_exception("candidate", vote_passed=True))
    tc.assertEqual(book.tenure_exception_used, 1)
    with tc.assertRaises(model.ModelRed):
        book.admit_tenure_exception("candidate-2", vote_passed=True)


def scenario_163(tc: unittest.TestCase) -> None:
    book = nomination_book()
    book.freeze_observation_window(
        (6, 7),
        candidate_histories={"candidate-a": (5, 6, 7), "candidate-b": (4, 6, 7)},
    )
    tc.assertEqual(book.observation_window, (6, 7))
    with tc.assertRaises(model.ModelRed):
        book.freeze_observation_window((7,), candidate_histories={"candidate-a": (7,)})


def scenario_164(tc: unittest.TestCase) -> None:
    book = nomination_book()
    book.add_cross_team_evidence(
        "result-164",
        {"candidate": 40, "team-peer": 60},
        owner_signed=False,
        independently_reviewed=True,
    )
    tc.assertEqual(sum(book.cross_team_evidence["result-164"].values()), 100)
    with tc.assertRaises(model.ModelRed):
        book.add_cross_team_evidence(
            "bad-result",
            {"candidate": 80, "team-peer": 60},
            owner_signed=True,
            independently_reviewed=False,
        )


def scenario_165(tc: unittest.TestCase) -> None:
    book = nomination_book()
    book.start_next_level_trial(
        "candidate",
        authority=("approve-project",),
        compensation=5,
        due_day=800,
        exit_condition="return to old duty",
    )
    trial = book.next_level_trials["candidate"]
    tc.assertEqual(trial["authority"], frozenset({"approve-project"}))
    tc.assertEqual((trial["compensation"], trial["due_day"]), (5, 800))
    with tc.assertRaises(model.ModelRed):
        book.start_next_level_trial(
            "candidate-2",
            authority=(),
            compensation=0,
            due_day=800,
            exit_condition="return",
        )


def scenario_166(tc: unittest.TestCase) -> None:
    book = nomination_book(quota=1)
    nomination = packet(
        "166",
        verified=("verified-a",),
        unverified=("draft-b",),
    )
    nominate(book, nomination, serial="m166")
    reusable = book.withdraw_packet("packet-166")
    tc.assertEqual(reusable, ("verified-a",))
    tc.assertEqual(book.quota_remaining, 1)
    tc.assertNotIn(nomination.candidate_id, book.candidate_packets)
    with tc.assertRaises(model.ModelRed):
        book.withdraw_packet("packet-166")


def scenario_167(tc: unittest.TestCase) -> None:
    book = nomination_book()
    positive = model.SponsorObservation("sponsor", "candidate-a", 3, True, 8)
    negative = model.SponsorObservation("sponsor", "candidate-b", 1, False, 8)
    tc.assertEqual(book.settle_sponsor_observation(positive, current_cycle=8), 3)
    tc.assertEqual(book.settle_sponsor_observation(negative, current_cycle=8), -1)
    tc.assertEqual(book.sponsor_credit["sponsor"], 2)
    with tc.assertRaises(model.ModelRed):
        book.settle_sponsor_observation(positive, current_cycle=9)


def scenario_168(tc: unittest.TestCase) -> None:
    book = nomination_book()
    hit_rate = book.manager_hit_rate(
        (
            model.NominationObservation(5, True, True, True),
            model.NominationObservation(1, True, True, True),
            model.NominationObservation(5, False, False, False),
        ),
        omitted_qualified=1,
    )
    tc.assertAlmostEqual(hit_rate, 6 / 7)


def scenario_169(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    tc.assertEqual(sum(panel.expertise_weights.values()), 100)
    tc.assertIn(model.PanelistKind.EXPERT, {item.kind for item in panel.panelists.values()})
    tc.assertIn(model.PanelistKind.EXTERNAL, {item.kind for item in panel.panelists.values()})


def scenario_170(tc: unittest.TestCase) -> None:
    first = formed_panel(seed=170)
    second = formed_panel(seed=170)
    tc.assertEqual(tuple(first.panelists), tuple(second.panelists))
    tc.assertEqual(len(first.panelists), len(set(first.panelists)))
    with tc.assertRaises(model.ModelRed):
        first.form_panel(
            panel_pool()[:4],
            seats=4,
            seed=170,
            expertise_weights={model.PanelistKind.EXPERT: 50, model.PanelistKind.EXTERNAL: 50},
        )


def scenario_171(tc: unittest.TestCase) -> None:
    panel = model.PromotionPanel(identity(), candidate_id="candidate")
    initial = [
        model.Panelist(
            "conflicted",
            "unit-a",
            model.PanelistKind.EXPERT,
            frozenset({"candidate"}),
        ),
        model.Panelist("outside", "unit-b", model.PanelistKind.EXTERNAL),
    ]
    panel.form_panel(
        initial,
        seats=2,
        seed=1,
        expertise_weights={model.PanelistKind.EXPERT: 50, model.PanelistKind.EXTERNAL: 50},
    )
    panel.recuse_conflicts((model.Panelist("clean-expert", "unit-c", model.PanelistKind.EXPERT),))
    tc.assertIn("conflicted", panel.recused)
    tc.assertEqual(panel.replacement_history["conflicted"], "clean-expert")
    tc.assertNotIn("conflicted", panel.panelists)


def scenario_172(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    panel.freeze_decision_rule(model.DecisionRule.TRIMMED_MEAN)
    result = panel.record_votes(
        {panelist_id: score for panelist_id, score in zip(panel.panelists, (0, 70, 80, 100))}
    )
    tc.assertTrue(result)
    tc.assertEqual(panel.decision_rule, model.DecisionRule.TRIMMED_MEAN)
    with tc.assertRaises(model.ModelRed):
        panel.freeze_decision_rule(model.DecisionRule.MAJORITY)


def scenario_173(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    scores = {panelist_id: 75 for panelist_id in panel.panelists}
    panel.blind_review({"artifact_ids": ("artifact",)}, scores)
    frozen = dict(panel.blind_scores)
    panel.live_review({panelist_id: 80 for panelist_id in panel.panelists})
    tc.assertEqual(panel.blind_scores, frozen)
    with tc.assertRaises(model.ModelRed) as caught:
        other = formed_panel(seed=173)
        other.blind_review({"name": "candidate"}, scores)
    tc.assertEqual(caught.exception.code, model.RedCode.PRIVACY_BREACH)


def scenario_174(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    presentation, questions = panel.allocate_defense_time(
        total=60,
        presentation_requested=70,
        protected_questions=20,
    )
    tc.assertEqual((presentation, questions), (40, 20))
    tc.assertEqual(presentation + questions, 60)


def scenario_175(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    remaining = panel.allocate_coaching(10, {"candidate": 8, "other": 2})
    tc.assertEqual(remaining, 0)
    tc.assertEqual(sum(panel.coaching_allocations.values()), 10)
    with tc.assertRaises(model.ModelRed):
        panel.allocate_coaching(10, {"candidate": 11})


def scenario_176(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    candidate_share = panel.freeze_attribution({"candidate": 40, "peer-a": 35, "peer-b": 25})
    tc.assertEqual(candidate_share, 40)
    tc.assertEqual(sum(panel.attribution.values()), 100)
    with tc.assertRaises(model.ModelRed):
        panel.freeze_attribution({"candidate": 100, "peer": 100})


def scenario_177(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    panel.freeze_scale_and_leverage(scale_score=95, leverage_score=30)
    tc.assertEqual((panel.scale_score, panel.leverage_score), (95, 30))
    tc.assertNotEqual(panel.scale_score, panel.leverage_score)


def scenario_178(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    tc.assertFalse(
        panel.dual_evidence_gate(
            artifact_score=40,
            narrative_score=95,
            artifact_threshold=60,
            narrative_threshold=60,
        )
    )
    tc.assertEqual((panel.artifact_score, panel.narrative_score), (40, 95))
    tc.assertTrue(
        panel.dual_evidence_gate(
            artifact_score=80,
            narrative_score=70,
            artifact_threshold=60,
            narrative_threshold=60,
        )
    )


def scenario_179(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    owner = next(iter(panel.panelists))
    feedback = model.RejectionFeedback(owner, "target-level scope", "lead two cross-team outcomes")
    panel.add_rejection_feedback(feedback)
    tc.assertEqual(panel.rejection_feedback, [feedback])
    with tc.assertRaises(model.ModelRed):
        panel.add_rejection_feedback(
            model.RejectionFeedback("not-a-panelist", "vague", "do better")
        )


def scenario_180(tc: unittest.TestCase) -> None:
    panel = formed_panel()
    panel.freeze_retry(
        cooldown_until=900,
        material_versions=("packet-v1",),
        gaps=("cross-team-impact",),
    )
    with tc.assertRaises(model.ModelRed):
        panel.retry(current_day=800)
    panel.retry(current_day=800, completed_gaps=("cross-team-impact",))
    tc.assertTrue(panel.retried)
    tc.assertEqual(panel.material_versions, ("packet-v1",))


REFERENCE_SCENARIOS: dict[int, Scenario] = {
    19: scenario_019,
    20: scenario_020,
    21: scenario_021,
    22: scenario_022,
    23: scenario_023,
    24: scenario_024,
    25: scenario_025,
    92: scenario_092,
    93: scenario_093,
    94: scenario_094,
    95: scenario_095,
    96: scenario_096,
    97: scenario_097,
    98: scenario_098,
    99: scenario_099,
    100: scenario_100,
    101: scenario_101,
    102: scenario_102,
    103: scenario_103,
    104: scenario_104,
    105: scenario_105,
    106: scenario_106,
    107: scenario_107,
    108: scenario_108,
    109: scenario_109,
    110: scenario_110,
    111: scenario_111,
    112: scenario_112,
    113: scenario_113,
    114: scenario_114,
    115: scenario_115,
    116: scenario_116,
    117: scenario_117,
    118: scenario_118,
    119: scenario_119,
    120: scenario_120,
    121: scenario_121,
    122: scenario_122,
    123: scenario_123,
    124: scenario_124,
    125: scenario_125,
    126: scenario_126,
    127: scenario_127,
    128: scenario_128,
    157: scenario_157,
    158: scenario_158,
    159: scenario_159,
    160: scenario_160,
    161: scenario_161,
    162: scenario_162,
    163: scenario_163,
    164: scenario_164,
    165: scenario_165,
    166: scenario_166,
    167: scenario_167,
    168: scenario_168,
    169: scenario_169,
    170: scenario_170,
    171: scenario_171,
    172: scenario_172,
    173: scenario_173,
    174: scenario_174,
    175: scenario_175,
    176: scenario_176,
    177: scenario_177,
    178: scenario_178,
    179: scenario_179,
    180: scenario_180,
}


class ContractTests(unittest.TestCase):
    def test_registry_and_scenarios_cover_exact_same_68_ids(self) -> None:
        self.assertEqual(set(model.MECHANISM_BEHAVIORS), model.EXPECTED_MECHANISM_IDS)
        self.assertEqual(set(REFERENCE_SCENARIOS), model.EXPECTED_MECHANISM_IDS)
        self.assertEqual(len(REFERENCE_SCENARIOS), 68)

    def test_registry_has_honest_non_ck3_readiness(self) -> None:
        for behavior in model.MECHANISM_BEHAVIORS.values():
            self.assertEqual(behavior.runtime_evidence, "python-l0-model")
            self.assertEqual(behavior.ck3_wiring, "not-implemented")

    def test_registry_is_immutable_dataclass_rows_with_unique_behavior_keys(self) -> None:
        keys = []
        for mechanism_id, behavior in model.MECHANISM_BEHAVIORS.items():
            self.assertEqual(mechanism_id, behavior.mechanism_id)
            self.assertTrue(dataclasses.is_dataclass(behavior))
            keys.append(behavior.behavior_key)
        self.assertEqual(len(keys), len(set(keys)))

    def test_guard_freezes_owner_subject_cycle_case_and_state(self) -> None:
        case = model.CareerAllocationCase(identity())
        correct = case.token()
        stale_tokens = (
            dataclasses.replace(correct, owner_id="other-manager"),
            dataclasses.replace(correct, subject_id="other-subject"),
            dataclasses.replace(correct, cycle_serial=8),
            dataclasses.replace(correct, case_serial=4),
            dataclasses.replace(correct, expected_state="OTHER"),
        )
        for index, stale in enumerate(stale_tokens):
            outcome = case.evaluate_eligibility(
                stale,
                f"stale-{index}",
                model.EligibilityEvidence(2, True, False, True, True),
            )
            self.assertFalse(outcome.applied)
            self.assertEqual(outcome.code, model.NoOpCode.STALE_TOKEN.value)
        self.assertIsNone(case.eligibility)

    def test_duplicate_action_serial_is_idempotent_no_op(self) -> None:
        case = model.CareerAllocationCase(identity())
        first = case.evaluate_eligibility(
            case.token(),
            "same-action",
            model.EligibilityEvidence(2, True, False, True, True),
        )
        second = case.evaluate_eligibility(
            case.token(),
            "same-action",
            model.EligibilityEvidence(2, True, False, True, True),
        )
        self.assertTrue(first.applied)
        self.assertFalse(second.applied)
        self.assertEqual(second.code, model.NoOpCode.DUPLICATE_ACTION.value)

    def test_bool_is_rejected_where_integer_is_required_with_typed_red(self) -> None:
        with self.assertRaises(model.ModelRed) as caught:
            model.MoneyLedger(True)  # type: ignore[arg-type]
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_TYPE)
        self.assertEqual(caught.exception.field_name, "opening")

    def test_slot_and_money_ledgers_reject_resource_creation(self) -> None:
        money = model.MoneyLedger(5)
        with self.assertRaises(model.ModelRed) as caught:
            money.reserve("too-much", 6)
        self.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
        slots = promotion_slots(1)
        slots.reserve("promotion-1", "packet-a")
        with self.assertRaises(model.ModelRed):
            slots.reserve("promotion-1", "packet-b")


class MechanismScenarioTests(unittest.TestCase):
    """One generated unittest method per numbered mechanism, each with real assertions."""


def _make_mechanism_test(mechanism_id: int, scenario: Scenario) -> Callable[[unittest.TestCase], None]:
    def test(self: unittest.TestCase) -> None:
        behavior = model.MECHANISM_BEHAVIORS[mechanism_id]
        self.assertEqual(behavior.mechanism_id, mechanism_id)
        scenario(self)

    test.__name__ = f"test_mechanism_{mechanism_id:03d}_{model.MECHANISM_BEHAVIORS[mechanism_id].behavior_key}"
    test.__doc__ = model.MECHANISM_BEHAVIORS[mechanism_id].title_cn
    return test


for _mechanism_id, _scenario in REFERENCE_SCENARIOS.items():
    setattr(
        MechanismScenarioTests,
        f"test_mechanism_{_mechanism_id:03d}",
        _make_mechanism_test(_mechanism_id, _scenario),
    )


if __name__ == "__main__":
    unittest.main()
