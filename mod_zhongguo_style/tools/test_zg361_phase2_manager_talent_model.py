#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density tests for the manager/talent Python L0 semantic model."""

from __future__ import annotations

import copy
import dataclasses
import unittest
from typing import Callable

import zg361_phase2_manager_talent_model as model


def player_duke(actor_id: str = "manager") -> model.Actor:
    return model.Actor(actor_id, model.TitleRank.DUKE, True, True)


def ai_duke(actor_id: str = "ai-manager") -> model.Actor:
    return model.Actor(actor_id, model.TitleRank.DUKE, True, True, is_ai=True)


def count(actor_id: str = "official") -> model.Actor:
    return model.Actor(actor_id, model.TitleRank.COUNT, True, True)


def identity(
    *, owner: str = "manager", subject: str = "official", cycle: int = 7, case: int = 1
) -> model.CaseIdentity:
    return model.CaseIdentity(owner, subject, cycle, case)


def manager_case(state: str = "SNAPSHOT_READY") -> model.ManagerReviewCase:
    return model.ManagerReviewCase(
        identity(owner="superior", subject="manager", cycle=8),
        state,
        manager=player_duke("manager"),
        superior=model.Actor("superior", model.TitleRank.KING, True, True),
    )


def market_case(state: str) -> model.InternalMarketCase:
    return model.InternalMarketCase(
        identity(), state, owner=player_duke(), subject=count()
    )


def learning_case(state: str) -> model.LearningCase:
    return model.LearningCase(identity(), state, owner=player_duke(), subject=count())


def policy_case(state: str) -> model.PolicyCase:
    return model.PolicyCase(
        identity(subject="realm-policy"), state, owner=player_duke()
    )


def team_snapshot(*, grandchild: bool = False) -> model.FrozenTeamSnapshot:
    return model.FrozenTeamSnapshot(
        "manager",
        "superior",
        7,
        8,
        1067,
        {
            "targets": 20,
            "jingcha": 10,
            "calibration": 12,
            "pip_success": 8,
            "appeal_overturn": -4,
            "retention": 15,
            "hc_efficiency": 9,
        },
        ("grandchild",) if grandchild else (),
    )


def annual_logs(owner: str = "superior") -> tuple[model.AnnualSystemLog, ...]:
    return tuple(
        model.AnnualSystemLog(owner, year, 3, 6, 1, 1, 2, 1, 1, 10 + year, 4, 80)
        for year in range(1051, 1061)
    )


Scenario = Callable[[unittest.TestCase], None]


def scenario_032(tc: unittest.TestCase) -> None:
    case = manager_case()
    refusal = model.JingchaRefusal("manager", "superior", 1067)
    result = case.score_frozen_team(case.token(), "m032", team_snapshot(), refusal=refusal)
    tc.assertTrue(result.applied)
    tc.assertEqual(case.score, 20)
    tc.assertEqual(case.team_breakdown["jingcha_refusal"], -50)
    tc.assertTrue(refusal.consumed)
    tc.assertFalse(case.score_frozen_team(case.token(), "m032", team_snapshot()).applied)
    tc.assertNotIn("grandchild", case.team_breakdown)


def scenario_033(tc: unittest.TestCase) -> None:
    case = manager_case("MANAGER_SCORED")
    outcome = case.explain_profile(
        case.token(),
        "m033",
        profile="data",
        evidence={"calibration": 4, "appeal": 4, "pip": -4, "bonus": 4, "hc": 4},
        evidence_cap=5,
        relationship_override=2,
    )
    tc.assertTrue(outcome.applied)
    tc.assertEqual(case.state, "REASON_CODED")
    tc.assertEqual(sum(value for _, value in case.reason_codes), 16)
    tc.assertTrue(all(abs(value) <= 5 for _, value in case.reason_codes))
    tc.assertEqual(case.appeal_risk, 2)


def scenario_034(tc: unittest.TestCase) -> None:
    case = manager_case("REASON_CODED")
    before_score = case.score
    result = case.freeze_nine_box(
        case.token(), "m034", performance_history=(82, 88), growth=90, fit=80, potential=85
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.nine_box["label"], "star")
    tc.assertEqual(case.nine_box["history_serials"], 2)
    tc.assertEqual(case.score, before_score)


def scenario_035(tc: unittest.TestCase) -> None:
    case = manager_case()
    result = case.freeze_distribution(
        case.token(),
        "m035",
        mode=model.DistributionMode.MIXED,
        scores=(90,) * 10,
        absolute_threshold=75,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.distribution.bottom_slots, 1)
    tc.assertEqual(case.distribution.bottom_consequence, "lightened")
    tc.assertEqual(
        case.distribution.top_slots
        + case.distribution.middle_slots
        + case.distribution.bottom_slots,
        10,
    )


def scenario_036(tc: unittest.TestCase) -> None:
    case = manager_case("NINE_BOXED")
    result = case.compile_decade_report(case.token(), "m036", annual_logs())
    tc.assertTrue(result.applied)
    tc.assertEqual(len(case.report["years"]), 10)
    tc.assertEqual(case.report["totals"]["grade_top"], 30)
    tc.assertEqual(
        case.report["totals"]["bonus_net"],
        sum(log.bonus_in - log.bonus_out for log in annual_logs()),
    )


def posting(*, legal: bool = True) -> model.VacancyPosting:
    return model.VacancyPosting(
        "vacancy-1",
        "hc-1" if legal else None,
        "manager",
        "B4",
        "governance outcomes",
        200,
        model.PostingScope.INTERNAL_THEN_EXTERNAL,
        ("official", "candidate-2"),
        ("manager-friend",),
        150,
    )


def scenario_312(tc: unittest.TestCase) -> None:
    case = market_case("POSTED")
    result = case.publish_role(case.token(), "m312", posting())
    tc.assertTrue(result.applied)
    tc.assertTrue(case.posting.visible_to("official", 100))
    case.hire_once("official")
    with tc.assertRaises(model.ModelRed) as caught:
        case.hire_once("candidate-2")
    tc.assertEqual(caught.exception.code, model.RedCode.DUPLICATE_ID)
    fake = market_case("POSTED")
    fake.publish_role(fake.token(), "m312-fake", posting(legal=False))
    tc.assertEqual(fake.market_trust_delta, -2)


def scenario_313(tc: unittest.TestCase) -> None:
    case = market_case("POSTED")
    letter = model.ReferenceLetter(
        "letter-1",
        "manager",
        ("case-achievement",),
        ("risk-known",),
        "pip-1",
        "ready",
        omitted_material_facts=("misconduct-1",),
        retaliatory=True,
    )
    result = case.freeze_reference(case.token(), "m313", letter)
    tc.assertTrue(result.applied)
    tc.assertIn("performance-whitewash-audit", case.manager_consequences)
    tc.assertIn("anti-retaliation-audit", case.manager_consequences)
    tc.assertEqual(case.reference.active_pip_ref, "pip-1")


def scenario_314(tc: unittest.TestCase) -> None:
    case = market_case("APPLIED")
    ledger = model.DualPayerLedger(100, 40)
    result = case.offer_relocation(
        case.token(),
        "m314",
        count(),
        ledger,
        accept=True,
        total_cost=20,
        treasury_share=15,
        receipt_id="relocation-1",
        distance_class="far",
        lump_sum_gold=10,
        temporary_allowance_gold=6,
        allowance_end_day=190,
        family_support_gold=4,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (85, 35))
    tc.assertEqual(case.performance_delta, 0)
    tc.assertEqual(case.relocation_response, "accepted")
    tc.assertEqual(case.relocation_package["allowance_end_day"], 190)


def scenario_315(tc: unittest.TestCase) -> None:
    case = market_case("APPLIED")
    terms = model.TrialTerms(100, 190, 40, 60, "return", "evidence", "evidence")
    result = case.begin_trial(case.token(), "m315", terms)
    tc.assertTrue(result.applied)
    case.finish_trial(success=False, reason="role-mismatch")
    tc.assertEqual(case.trial_result, "returned:role-mismatch")
    tc.assertEqual(case.performance_delta, 0)


def scenario_316(tc: unittest.TestCase) -> None:
    case = market_case("TRIALED")
    case.historical_payments = (40, 40, 40)
    mapping = model.PayMapping("B5", "B4", 30, 10, 5, "step", 200, (38, 36, 35))
    result = case.freeze_pay_mapping(case.token(), "m316", mapping)
    tc.assertTrue(result.applied)
    tc.assertEqual(case.historical_payments, (40, 40, 40))
    tc.assertEqual(case.pay_mapping.schedule[-1], 35)


def scenario_317(tc: unittest.TestCase) -> None:
    case = market_case("TRIALED")
    result = case.project_application_acl(
        case.token(),
        "m317",
        stage="screen",
        viewers=("official", "manager"),
        leaked_to_source=True,
        rating_changed_without_new_evidence=True,
    )
    tc.assertTrue(result.applied)
    tc.assertTrue(case.retaliation_audit)
    tc.assertIn(("screen", "official"), case.disclosure_log)


def scenario_318(tc: unittest.TestCase) -> None:
    case = market_case("APPLIED")
    quota = model.ApplicationQuota()
    outcome = case.consume_application_slot(
        case.token(), "m318", quota, application_id="explore", exploratory=True
    )
    tc.assertTrue(outcome.applied)
    quota.submit("formal-1")
    quota.withdraw("formal-1")
    quota.submit("formal-2")
    tc.assertEqual(quota.used, 2)
    with tc.assertRaises(model.ModelRed) as caught:
        quota.submit("formal-3")
    tc.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
    quota.protect_from_manager_delay("formal-2")
    quota.submit("formal-3")
    tc.assertEqual(quota.applications["formal-2"], "manager-timeout")
    tc.assertEqual(quota.exploratory_talks, 1)


def scenario_319(tc: unittest.TestCase) -> None:
    case = market_case("RELEASE_DECIDED")
    result = case.make_counteroffer(
        case.token(), "m319", employee_accepts=False, handover_deadline=220
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.counteroffer_count, 1)
    tc.assertEqual(case.settle_release(day=230), -20)
    tc.assertEqual(case.settle_release(day=240), -20)
    accepted = market_case("RELEASE_DECIDED")
    accepted.make_counteroffer(
        accepted.token(),
        "m319-accepted",
        employee_accepts=True,
        handover_deadline=220,
        promised_terms=("salary", "responsibility"),
        commitment_due_day=250,
    )
    tc.assertEqual(
        accepted.settle_counteroffer_commitment(day=251, fulfilled=False), -20
    )


def scenario_320(tc: unittest.TestCase) -> None:
    case = market_case("MOVED")
    book = model.ExitInterviewBook(2)
    outcome = case.aggregate_exit_voice(
        case.token(),
        "m320",
        book,
        (
            model.ExitInterview("i1", "a", "manager", "role", "anonymous", ("retaliation",)),
            model.ExitInterview("i2", "b", "manager", "role", "named", ("retaliation",)),
        ),
    )
    tc.assertTrue(outcome.applied)
    tc.assertEqual(book.audit_issues("manager"), frozenset({"retaliation"}))
    tc.assertEqual(book.public_rows()[0][0], "anonymous")
    book.reclassify("i2", ("culture-fit",))
    tc.assertEqual(book.reclassification_log[0][1], ("retaliation",))


def scenario_321(tc: unittest.TestCase) -> None:
    case = market_case("MOVED")
    network = model.AlumniNetwork()
    record = model.AlumniRecord("alumnus", True, "contact", ("finance",), True)
    ledger = model.DualPayerLedger(30, 10)
    outcome = case.maintain_alumni_relationship(
        case.token(),
        "m321",
        network,
        record,
        ledger,
        cycle_serial=8,
        total_cost=6,
        treasury_share=4,
    )
    tc.assertTrue(outcome.applied)
    network.maintain("alumnus", 8, ledger, total_cost=6, treasury_share=4)
    network.maintain("alumnus", 9, ledger, total_cost=6, treasury_share=4)
    network.add_lead("lead-1")
    network.add_lead("lead-1")
    network.delete_contact_projection("alumnus")
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (22, 6))
    tc.assertEqual(network.talent_reputation, -10)
    tc.assertEqual(network.leads, {"lead-1"})


def scenario_322(tc: unittest.TestCase) -> None:
    market = market_case("ALUMNI")
    registry = model.ReturneeRegistry()
    case = model.ReturneeCase(
        "returnee",
        ("old-review-1", "old-review-2"),
        "healthy-exit",
        ("old-misconduct",),
        ("external-result",),
        9,
        "new-cohort",
        history_wipe_attempt=True,
    )
    outcome = market.open_returnee_case(market.token(), "m322", registry, case)
    tc.assertTrue(outcome.applied)
    tc.assertEqual(registry.cases["returnee"].old_case_ids, ("old-review-1", "old-review-2"))
    tc.assertEqual(registry.cases["returnee"].new_cohort_id, "new-cohort")
    with tc.assertRaises(model.ModelRed) as caught:
        registry.open(dataclasses.replace(case, new_cohort_id="duplicate"))
    tc.assertEqual(caught.exception.code, model.RedCode.CONFLICT)


def scenario_323(tc: unittest.TestCase) -> None:
    case = learning_case("BUDGETED")
    budget = model.LearningBudget(40, 20)
    ledger = model.DualPayerLedger(100, 20)
    result = case.allocate_budget(
        case.token(),
        "m323",
        budget,
        ledger,
        allocation_id="allocation-1",
        target_group="gap",
        gold=10,
        hours=5,
        manager_share=2,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual((budget.allocated_gold, budget.allocated_time), (10, 5))
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (92, 18))
    tc.assertEqual(case.performance_delta, 0)


def scenario_324(tc: unittest.TestCase) -> None:
    case = learning_case("BUDGETED")
    result = case.advance_learning_stages(
        case.token(),
        "m324",
        completion_evidence="certificate",
        application_evidence="applied-to-tax-roll",
        observed_delta=12,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.performance_delta, 12)
    tc.assertEqual(case.data["three_stages"]["completion"], "certificate")
    incomplete = learning_case("BUDGETED")
    incomplete.advance_learning_stages(
        incomplete.token(), "m324-only", completion_evidence="course", application_evidence=None, observed_delta=None
    )
    tc.assertEqual(incomplete.performance_delta, 0)


def scenario_325(tc: unittest.TestCase) -> None:
    case = learning_case("BUDGETED")
    case.assess_competence(
        case.token(),
        "m325",
        certificate_passed=True,
        practical_score=30,
        practical_threshold=60,
        test_valid=True,
    )
    tc.assertFalse(case.data["competence"]["competent"])
    invalid = learning_case("BUDGETED")
    invalid.assess_competence(
        invalid.token(),
        "m325-invalid",
        certificate_passed=True,
        practical_score=20,
        practical_threshold=60,
        test_valid=False,
    )
    tc.assertIn("training-owner-test-invalid", invalid.manager_consequences)
    tc.assertEqual(invalid.performance_delta, 0)


def scenario_326(tc: unittest.TestCase) -> None:
    case = learning_case("ENROLLED")
    ledger = model.DualPayerLedger(100, 20)
    result = case.settle_conference(
        case.token(),
        "m326",
        ledger,
        receipt_id="trip-1",
        total_cost=12,
        treasury_share=9,
        days_away=4,
        artifact_id="playbook",
        adopted_value=6,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.performance_delta, 6)
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (91, 17))
    tc.assertEqual(case.data["conference"]["delivery_opportunity_cost"], 4)
    tc.assertEqual(case.data["conference"]["attrition_risk"], 1)


def scenario_327(tc: unittest.TestCase) -> None:
    case = learning_case("ENROLLED")
    result = case.attribute_teaching(
        case.token(),
        "m327",
        teaching_hours=8,
        available_hours=40,
        attendees=("a", "b"),
        applying_attendees=("a",),
        shares={"teacher": 60, "applicator": 40},
        downstream_value=10,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.performance_delta, 6)
    tc.assertEqual(case.data["teaching"]["remaining"], 32)


def scenario_328(tc: unittest.TestCase) -> None:
    case = learning_case("COMPLETED")
    result = case.settle_community(
        case.token(),
        "m328",
        artifacts=("standard", "case-library"),
        maintainers=("expert",),
        contribution_hours={"official": 6},
        available_hours={"official": 10},
        adopting_teams=("team-a", "team-b"),
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.performance_delta, 2)
    tc.assertEqual(case.data["community"]["hours"]["official"], 6)


def scenario_329(tc: unittest.TestCase) -> None:
    case = learning_case("COMPLETED")
    result = case.match_mentor(
        case.token(),
        "m329",
        mentor_id="mentor-other-team",
        goal_ids=("goal-1",),
        committed_hours=6,
        end_day=190,
        application_evidence=("application-1",),
        capacity_payment=2,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.data["mentorship"]["credit"], 1)
    tc.assertEqual(case.data["mentorship"]["end_day"], 190)
    rematch = case.rematch_mentor(
        case.token(),
        "m329-rematch",
        old_mentor_id="mentor-other-team",
        new_mentor_id="mentor-replacement",
        conflict_reason="conflict",
    )
    tc.assertTrue(rematch.applied)
    tc.assertEqual(case.data["mentorship"]["mentor"], "mentor-replacement")
    tc.assertEqual(case.data["mentorship"]["end_day"], 190)


def scenario_330(tc: unittest.TestCase) -> None:
    case = learning_case("APPLIED")
    ledger = model.DualPayerLedger(100, 30)
    result = case.settle_reskill(
        case.token(),
        "m330",
        ledger,
        route="reskill",
        receipt_id="reskill-1",
        total_cost=20,
        treasury_share=15,
        assessment_score=50,
        threshold=70,
        affected_character_ids=("official",),
        target_role_ids=("growth-role",),
        training_days=90,
    )
    tc.assertTrue(result.applied)
    tc.assertFalse(case.data["reskill"]["placed"])
    tc.assertFalse(case.data["reskill"]["failed_is_low_grade"])
    tc.assertEqual(case.data["reskill"]["target_role_ids"], ("growth-role",))
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (85, 25))


def scenario_331(tc: unittest.TestCase) -> None:
    case = learning_case("APPLIED")
    capacity = model.ProtectedLearningTime(100, 10)
    result = case.settle_protected_time(
        case.token(),
        "m331",
        capacity,
        borrow_hours=4,
        current_cycle=7,
        real_crisis=True,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(capacity.repayment_due_cycle, 8)
    tc.assertEqual(capacity.delivery_hours, 94)
    capacity.repay(4, cycle=9)
    tc.assertEqual(capacity.manager_score_delta, -10)


def scenario_332(tc: unittest.TestCase) -> None:
    case = learning_case("MEASURED")
    result = case.run_succession_drill(
        case.token(),
        "m332",
        readiness_before=40,
        success=False,
        emergency_veto_uses=1,
    )
    tc.assertTrue(result.applied)
    drill = case.data["succession_drill"]
    tc.assertTrue(drill["safe_simulation"])
    tc.assertFalse(drill["real_incident"])
    tc.assertFalse(drill["low_grade"])
    tc.assertEqual(drill["development_gap"], "drill-gap")


def scenario_333(tc: unittest.TestCase) -> None:
    case = learning_case("MEASURED")
    ledger = model.DualPayerLedger(100, 30)
    result = case.open_training_commitment(
        case.token(),
        "m333",
        ledger,
        contract_id="contract-1",
        receipt_id="training-1",
        cost=24,
        treasury_share=18,
        completion_day=100,
        service_end_day=460,
        monthly_reduction=2,
        application_evidence=(),
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.data["training_performance_credit"], 0)
    employee_gold, recovered = case.training_contract.settle_exit(
        day=190, reason="voluntary", employee_gold=50
    )
    tc.assertEqual(recovered, 18)
    tc.assertEqual(employee_gold, 32)
    tc.assertEqual((ledger.treasury_gold, ledger.manager_gold), (95, 29))
    employee_gold, duplicate = case.training_contract.settle_exit(
        day=200, reason="voluntary", employee_gold=employee_gold
    )
    tc.assertEqual(duplicate, 0)


def scenario_345(tc: unittest.TestCase) -> None:
    case = policy_case("DRAFTED")
    result = case.freeze_calendar(
        case.token(), "m345", frequency=model.CycleFrequency.ANNUAL, effective_cycle=8
    )
    tc.assertTrue(result.applied)
    calendar = case.data["calendar"]
    tc.assertEqual(calendar.final_review_days, (330,))
    tc.assertEqual(calendar.checkin_days, (180,))
    tc.assertEqual(calendar.event_interrupts, 1)


def scenario_346(tc: unittest.TestCase) -> None:
    case = policy_case("DRAFTED")
    result = case.record_offcycle_signal(
        case.token(),
        "m346",
        signal_id="signal-1",
        materiality=80,
        action="investigate",
    )
    tc.assertTrue(result.applied)
    tc.assertTrue(case.consume_offcycle_signal(8))
    tc.assertFalse(case.consume_offcycle_signal(8))
    tc.assertEqual(case.data["offcycle_signal"]["cohort_reruns"], 0)


def scenario_347(tc: unittest.TestCase) -> None:
    case = policy_case("PILOTED")
    book = model.OverrideBook(("a", "b", "c"), 2)
    result = case.apply_override_book(
        case.token(), "m347", book, (("b", "a", "cross-team-evidence"),)
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(book.used_points, 1)
    tc.assertEqual(sorted(book.final_order), ["a", "b", "c"])
    tc.assertEqual(book.entries[0], ("b", "a", "cross-team-evidence"))
    book.write_back(appeal_overturned=True, later_success=False)
    tc.assertEqual(book.next_cycle_budget, 1)


def scenario_348(tc: unittest.TestCase) -> None:
    case = policy_case("PILOTED")
    exception = model.PolicyException("manager", 7, 9, "exception-1", "newcomer", "official", 200)
    result = case.bind_exception(case.token(), "m348", exception)
    tc.assertTrue(result.applied)
    stale = dataclasses.replace(exception.token(), case_serial=99)
    tc.assertEqual(exception.due(stale, day=200), model.NoOpCode.STALE_TOKEN.value)
    tc.assertEqual(exception.due(exception.token(), day=200), "expired")
    tc.assertEqual(exception.cleanup_entries, ["restore-default"])


def scenario_349(tc: unittest.TestCase) -> None:
    case = policy_case("EFFECTIVE")
    population = {f"case-{index}": (90 if index in {1, 2} else 10) for index in range(20)}
    result = case.run_audit(
        case.token(),
        "m349",
        case_risks=population,
        sample_rate_percent=10,
        seed=42,
        transparency_credit=5,
    )
    tc.assertTrue(result.applied)
    tc.assertGreaterEqual(len(case.data["audit"]["sample"]), 1)
    tc.assertTrue(
        {"case-1", "case-2"} & set(case.data["audit"]["sample"])
    )
    tc.assertEqual(case.data["audit"]["hours"], len(case.data["audit"]["sample"]) * 2)
    replay = policy_case("EFFECTIVE")
    replay.run_audit(
        replay.token(), "m349-replay", case_risks=population, sample_rate_percent=10, seed=42, transparency_credit=5
    )
    tc.assertEqual(case.data["audit"]["sample"], replay.data["audit"]["sample"])


def scenario_350(tc: unittest.TestCase) -> None:
    case = policy_case("EFFECTIVE")
    records = (
        model.HistoricalRecord("h1", 80.0, "old-formula", "v1"),
        model.HistoricalRecord("h2", 81.0, "old-formula", "v1"),
    )
    result = case.version_benchmark(
        case.token(),
        "m350",
        old_version="v1",
        new_version="v2",
        effective_cycle=8,
        thresholds={"top": 85, "middle": 60},
        historical_records=records,
        explanation="strategy harder",
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.data["benchmark"]["effective_cycle"], 8)
    tc.assertEqual(case.data["benchmark"]["history"][0], ("h1", 80.0, "v1"))


def scenario_351(tc: unittest.TestCase) -> None:
    case = policy_case("AUDITED")
    outcomes = {
        "d-pilot-1": {"trust": 8, "delivery": 7},
        "d-pilot-2": {"trust": 9, "delivery": 6},
        "d-control-1": {"trust": 5, "delivery": 6},
        "d-control-2": {"trust": 5, "delivery": 5},
    }
    result = case.measure_pilot(
        case.token(),
        "m351",
        pilot_regions=("d-pilot-1", "d-pilot-2"),
        control_regions=("d-control-1", "d-control-2"),
        metrics=("trust", "delivery"),
        outcomes=outcomes,
        end_cycle=9,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(set(case.data["pilot"]["differences"]), {"trust", "delivery"})
    tc.assertEqual(case.data["pilot"]["differences"]["trust"], 3.5)


def scenario_352(tc: unittest.TestCase) -> None:
    case = policy_case("AUDITED")
    records = (model.HistoricalRecord("old-1", 3.25, "three-band", "v1"),)
    result = case.map_history(
        case.token(), "m352", records, mapping_version="map-v2", multiplier=100
    )
    tc.assertTrue(result.applied)
    mapping = case.data["history_mapping"]
    tc.assertEqual(mapping["original"]["old-1"], (3.25, "three-band", "v1"))
    tc.assertEqual(mapping["mapped"]["old-1"], 325.0)


def scenario_353(tc: unittest.TestCase) -> None:
    case = policy_case("MEASURED")
    result = case.charge_admin_capacity(
        case.token(),
        "m353",
        available_hours=100,
        form_hours=10,
        meeting_hours=12,
        appeal_hours=8,
        calibration_hours=15,
        interruption_hours=5,
        error_rate_delta=3,
        overturn_rate_delta=2,
    )
    tc.assertTrue(result.applied)
    tc.assertEqual(case.data["admin_cost"]["total"], 50)
    tc.assertEqual(case.data["admin_cost"]["remaining"], 50)
    tc.assertEqual(case.manager_score_delta, -5)


def scenario_354(tc: unittest.TestCase) -> None:
    case = policy_case("MEASURED")
    result = case.audit_fairness_metrics(
        case.token(),
        "m354",
        delivered_results=100,
        raw_appeals=20,
        raw_overturns=10,
        raw_exits=20,
        raw_healthy_exits=8,
        reported_appeal_rate=0.05,
        reported_overturn_rate=0.10,
        reported_healthy_exit_rate=0.90,
        self_disclosed=True,
        remediation_completed=True,
    )
    tc.assertTrue(result.applied)
    tc.assertTrue(case.data["fairness_audit"]["gaming"])
    tc.assertEqual(case.data["fairness_audit"]["raw"], (0.2, 0.5, 0.4))
    tc.assertEqual(case.trust_delta, 5)


MECHANISM_SCENARIOS: dict[int, Scenario] = {
    32: scenario_032,
    33: scenario_033,
    34: scenario_034,
    35: scenario_035,
    36: scenario_036,
    312: scenario_312,
    313: scenario_313,
    314: scenario_314,
    315: scenario_315,
    316: scenario_316,
    317: scenario_317,
    318: scenario_318,
    319: scenario_319,
    320: scenario_320,
    321: scenario_321,
    322: scenario_322,
    323: scenario_323,
    324: scenario_324,
    325: scenario_325,
    326: scenario_326,
    327: scenario_327,
    328: scenario_328,
    329: scenario_329,
    330: scenario_330,
    331: scenario_331,
    332: scenario_332,
    333: scenario_333,
    345: scenario_345,
    346: scenario_346,
    347: scenario_347,
    348: scenario_348,
    349: scenario_349,
    350: scenario_350,
    351: scenario_351,
    352: scenario_352,
    353: scenario_353,
    354: scenario_354,
}


class TestContractAndGuards(unittest.TestCase):
    def test_exact_owned_scope_and_honest_readiness(self) -> None:
        expected = frozenset((*range(32, 37), *range(312, 334), *range(345, 355)))
        self.assertEqual(model.EXPECTED_MECHANISM_IDS, expected)
        self.assertEqual(set(model.MECHANISM_TITLES), expected)
        self.assertEqual(set(model.MECHANISM_DOMAINS), expected)
        self.assertEqual(set(model.MECHANISM_OPERATIONS), expected)
        self.assertNotIn(121, expected)
        self.assertEqual(model.READINESS, "python-l0-only")
        self.assertFalse(model.CK3_IMPLEMENTED)
        self.assertEqual(model.MCP_EVIDENCE, "none")

    def test_every_id_has_an_independent_e2e_scenario(self) -> None:
        self.assertEqual(set(MECHANISM_SCENARIOS), model.EXPECTED_MECHANISM_IDS)
        self.assertEqual(len(MECHANISM_SCENARIOS), 37)

    def test_permission_matrix_player_ai_and_assessed_only(self) -> None:
        model.authorize_manager(player_duke(), channel="visible")
        model.authorize_manager(ai_duke(), channel="background")
        with self.assertRaises(model.ModelRed) as caught:
            model.authorize_manager(ai_duke(), channel="visible")
        self.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)
        for rank in (model.TitleRank.BARON, model.TitleRank.COUNT):
            low = model.Actor("low", rank, True, True)
            self.assertTrue(low.assessed_only)
            model.authorize_self_response(low, "low")
            with self.assertRaises(model.ModelRed) as low_red:
                model.authorize_manager(low, channel="visible")
            self.assertEqual(low_red.exception.code, model.RedCode.PERMISSION_DENIED)
        with self.assertRaises(model.ModelRed):
            model.authorize_manager(
                model.Actor("foreign", model.TitleRank.EMPEROR, True, False), channel="visible"
            )

    def test_manager_is_assessed_by_eligible_superior(self) -> None:
        case = manager_case()
        self.assertEqual(case.identity.subject_id, "manager")
        self.assertEqual(case.identity.owner_id, "superior")
        self.assertTrue(case.manager.eligible_manager)
        self.assertTrue(case.superior.eligible_manager)
        with self.assertRaises(model.ModelRed) as caught:
            model.ManagerReviewCase(
                identity(owner="manager", subject="superior", cycle=8),
                "SNAPSHOT_READY",
                manager=player_duke("manager"),
                superior=model.Actor("superior", model.TitleRank.KING, True, True),
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVARIANT_BREACH)

    def test_jingcha_is_free_default_mandatory_and_refusal_is_major_reason(self) -> None:
        mandate = model.JingchaMandate("manager", "superior", 1067)
        refusal = mandate.resolve(player_duke(), hold=False)
        self.assertEqual(refusal.superior_opinion_delta, -25)
        self.assertEqual(refusal.next_review_kpi_delta, -50)
        case = manager_case()
        case.score_frozen_team(case.token(), "jingcha-score", team_snapshot(), refusal=refusal)
        self.assertEqual(case.team_breakdown["jingcha_refusal"], -50)
        self.assertTrue(refusal.consumed)
        ai_mandate = model.JingchaMandate("ai-manager", "superior", 1067)
        with self.assertRaises(model.ModelRed) as caught:
            ai_mandate.resolve(ai_duke(), hold=False)
        self.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)
        ai_mandate.resolve(ai_duke(), hold=True)
        self.assertTrue(ai_mandate.held)

    def test_case_stale_and_idempotent_guards(self) -> None:
        case = manager_case()
        stale = dataclasses.replace(case.token(), case_serial=999)
        stale_result = case.freeze_distribution(
            stale,
            "stale",
            mode=model.DistributionMode.STRICT,
            scores=(80,) * 10,
            absolute_threshold=70,
        )
        self.assertFalse(stale_result.applied)
        self.assertEqual(stale_result.code, model.NoOpCode.STALE_TOKEN.value)
        self.assertIsNone(case.distribution)
        first = case.freeze_distribution(
            case.token(),
            "once",
            mode=model.DistributionMode.STRICT,
            scores=(80,) * 10,
            absolute_threshold=70,
        )
        second = case.freeze_distribution(
            case.token(),
            "once",
            mode=model.DistributionMode.OFF,
            scores=(80,) * 10,
            absolute_threshold=70,
        )
        self.assertTrue(first.applied)
        self.assertFalse(second.applied)
        self.assertEqual(second.code, model.NoOpCode.DUPLICATE_ACTION.value)
        self.assertEqual(case.distribution.mode, model.DistributionMode.STRICT)

    def test_atomic_dual_payer_precheck(self) -> None:
        ledger = model.DualPayerLedger(100, 1)
        budget = model.LearningBudget(50, 20)
        case = learning_case("BUDGETED")
        before = (ledger.treasury_gold, ledger.manager_gold, budget.allocated_gold, budget.allocated_time)
        with self.assertRaises(model.ModelRed) as caught:
            case.allocate_budget(
                case.token(),
                "atomic-red",
                budget,
                ledger,
                allocation_id="too-expensive",
                target_group="gap",
                gold=10,
                hours=5,
                manager_share=2,
            )
        self.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
        self.assertEqual(
            (ledger.treasury_gold, ledger.manager_gold, budget.allocated_gold, budget.allocated_time),
            before,
        )
        self.assertEqual(case.state, "BUDGETED")

    def test_no_grandchild_fact_can_enter_superior_score(self) -> None:
        case = manager_case()
        refusal = model.JingchaRefusal("manager", "superior", 1067)
        with self.assertRaises(model.ModelRed) as caught:
            case.score_frozen_team(
                case.token(), "grandchild-red", team_snapshot(grandchild=True), refusal=refusal
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVARIANT_BREACH)
        self.assertIsNone(case.score)
        self.assertFalse(refusal.consumed)

    def test_defer_route_is_once_visible_and_permission_bound_for_every_id(self) -> None:
        debt = model.PolicyDebtBook()
        manager = player_duke()
        for mechanism_id in sorted(model.EXPECTED_MECHANISM_IDS):
            action = f"defer-{mechanism_id}"
            result = debt.defer(
                mechanism_id,
                manager,
                "official",
                7,
                action,
                channel="visible",
            )
            self.assertTrue(result.applied)
            duplicate = debt.defer(
                mechanism_id,
                manager,
                "official",
                7,
                action,
                channel="visible",
            )
            self.assertFalse(duplicate.applied)
            self.assertEqual(debt.records[(mechanism_id, "manager", 7)], 8)
        ai_result = debt.defer(32, ai_duke(), "official", 8, "ai-defer", channel="background")
        self.assertTrue(ai_result.applied)
        with self.assertRaises(model.ModelRed) as caught:
            debt.defer(32, count(), "official", 8, "count-defer", channel="visible")
        self.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)

    def test_bool_is_not_an_integer_and_red_is_atomic(self) -> None:
        case = manager_case()
        with self.assertRaises(model.ModelRed) as caught:
            case.freeze_distribution(
                case.token(),
                "bool-red",
                mode=model.DistributionMode.STRICT,
                scores=(True,),
                absolute_threshold=70,
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_TYPE)
        self.assertIsNone(case.distribution)

    def test_refund_is_receipt_bounded(self) -> None:
        ledger = model.DualPayerLedger(100, 50)
        plan = ledger.plan_charge("receipt", total=20, treasury_share=15)
        ledger.commit_charge(plan)
        ledger.refund_exact("receipt", 5)
        before = (ledger.treasury_gold, ledger.manager_gold)
        with self.assertRaises(model.ModelRed) as caught:
            ledger.refund_exact("receipt", 16)
        self.assertEqual(caught.exception.code, model.RedCode.INVARIANT_BREACH)
        self.assertEqual((ledger.treasury_gold, ledger.manager_gold), before)

    def test_distribution_modes_are_frozen_and_distinct(self) -> None:
        results = {}
        for index, mode_value in enumerate(model.DistributionMode, start=1):
            case = manager_case()
            case.freeze_distribution(
                case.token(),
                f"mode-{index}",
                mode=mode_value,
                scores=(90,) * 20,
                absolute_threshold=75,
            )
            results[mode_value] = (
                case.distribution.bottom_slots,
                case.distribution.bottom_consequence,
            )
        self.assertEqual(results[model.DistributionMode.STRICT], (2, "full"))
        self.assertEqual(results[model.DistributionMode.RELAXED], (1, "full"))
        self.assertEqual(results[model.DistributionMode.OFF], (0, "full"))
        self.assertEqual(results[model.DistributionMode.MIXED], (2, "lightened"))

    def test_frozen_team_snapshot_rejects_late_mutation(self) -> None:
        snapshot = team_snapshot()
        with self.assertRaises(TypeError):
            snapshot.metrics["targets"] = 999  # type: ignore[index]
        self.assertEqual(snapshot.metrics["targets"], 20)

    def test_protected_time_failed_borrow_is_atomic(self) -> None:
        capacity = model.ProtectedLearningTime(100, 10)
        before = copy.deepcopy(capacity)
        with self.assertRaises(model.ModelRed) as caught:
            capacity.borrow_for_crisis(4, current_cycle=7, real_crisis=False)
        self.assertEqual(caught.exception.code, model.RedCode.PERMISSION_DENIED)
        self.assertEqual(capacity, before)


class TestMechanismScenarios(unittest.TestCase):
    """One separately named end-to-end test is generated for every owned ID."""


def _scenario_test(mechanism_id: int, scenario: Scenario) -> Callable[[unittest.TestCase], None]:
    def test(self: unittest.TestCase) -> None:
        self.assertIn(mechanism_id, model.EXPECTED_MECHANISM_IDS)
        self.assertTrue(model.MECHANISM_OPERATIONS[mechanism_id])
        scenario(self)

    test.__name__ = f"test_mechanism_{mechanism_id:03d}"
    return test


for _mechanism_id, _scenario in MECHANISM_SCENARIOS.items():
    setattr(
        TestMechanismScenarios,
        f"test_mechanism_{_mechanism_id:03d}",
        _scenario_test(_mechanism_id, _scenario),
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
