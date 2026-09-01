#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 tests for the isolated workforce/endgame reference model."""

from __future__ import annotations

import copy
import pickle
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zg361_phase3_workforce_endgame_model import (
    ActionStatus,
    ActorRecord,
    BudgetLedger,
    CapacityPeriod,
    CharterPriority,
    CommandToken,
    CompensationRoute,
    ContractType,
    DeliveryHorizon,
    DomainRed,
    EXPECTED_MECHANISM_IDS,
    HistoricalCase,
    MECHANISM_BINDINGS,
    OvertimeKind,
    Phase3WorkforceEndgameModel,
    PolicyDefaults,
    READINESS,
    Rank,
    RatchetMode,
    RedCode,
    Vote,
    WORKFORCE_EXECUTION_ORDER,
    WORKFORCE_EXECUTION_STAGE,
    WorkCategory,
)


def make_model() -> Phase3WorkforceEndgameModel:
    actors = {
        "emperor": ActorRecord(
            "emperor",
            Rank.EMPEROR,
            is_top_celestial_liege=True,
        ),
        "duke": ActorRecord("duke", Rank.DUKE),
        "duke2": ActorRecord("duke2", Rank.DUKE),
        "count": ActorRecord("count", Rank.COUNT),
        "baron": ActorRecord("baron", Rank.BARON),
        "candidate1": ActorRecord("candidate1", Rank.COUNT),
        "candidate2": ActorRecord("candidate2", Rank.BARON),
        "external": ActorRecord("external", Rank.BARON),
    }
    defaults = PolicyDefaults(
        DeliveryHorizon.LONG_TERM,
        "frozen_30_60_10",
        "evidence_first",
        "settled_after_result",
        "authorized_only",
        "manager_cost_visible",
        "full_receipts",
    )
    return Phase3WorkforceEndgameModel(
        model_id="workforce-endgame",
        owner_id="emperor",
        subject_id="count",
        cycle_serial=3,
        case_serial=77,
        actors=actors,
        gold=BudgetLedger(total=2_000, available=2_000),
        formal_hc_total=8,
        formal_hc_available=8,
        formal_hc_reserved=0,
        formal_hc_filled=0,
        formal_hc_vacant=0,
        shadow_hc_total=4,
        shadow_hc_available=4,
        shadow_hc_active=0,
        capacity=CapacityPeriod("capacity-1", 400, 40),
        baseline_defaults=defaults,
        historical_cases=(
            HistoricalCase(
                "history-1",
                "duke",
                "candidate1",
                1,
                "3.25",
                "sha256:history-1",
            ),
        ),
    )


def apply(model: Phase3WorkforceEndgameModel, command_id: str, method_name: str, **kwargs: object) -> None:
    result = getattr(model, method_name)(model.command(command_id), **kwargs)
    if result.status is not ActionStatus.APPLIED:
        raise AssertionError(f"{method_name} did not apply: {result.status}")


class WorkforceEndgameModelTests(unittest.TestCase):
    def test_catalogue_is_exact_and_every_binding_is_callable(self) -> None:
        self.assertEqual("python-l0-only", READINESS)
        self.assertEqual(EXPECTED_MECHANISM_IDS, frozenset(MECHANISM_BINDINGS))
        self.assertEqual(40, len(MECHANISM_BINDINGS))
        for mechanism_id, binding in MECHANISM_BINDINGS.items():
            self.assertEqual(mechanism_id, binding.mechanism_id)
            self.assertIn(binding.domain, {"AB", "AC", "AD", "AL"})
            self.assertTrue(binding.trigger_hook)
            self.assertTrue(binding.conservation_rule)
            self.assertEqual(1, len(binding.behaviors))
            self.assertTrue(hasattr(Phase3WorkforceEndgameModel, binding.behaviors[0]))
            self.assertEqual(binding.behaviors[0], binding.consumer_key)
            self.assertTrue(binding.object_type)
            self.assertTrue(binding.resource_books)
            self.assertIn(binding.deadline_cycles, (0, 1))
            self.assertEqual(WORKFORCE_EXECUTION_STAGE[mechanism_id], binding.execution_stage)
        self.assertEqual(40, len({binding.object_type for binding in MECHANISM_BINDINGS.values()}))
        self.assertEqual("overtime_claim", MECHANISM_BINDINGS[245].object_type)
        self.assertEqual("vacancy_requisition", MECHANISM_BINDINGS[266].object_type)
        self.assertEqual("pip_exit_vacancy", MECHANISM_BINDINGS[277].object_type)
        self.assertEqual("collective_action", MECHANISM_BINDINGS[360].object_type)
        self.assertEqual("charter_version", MECHANISM_BINDINGS[361].object_type)
        self.assertEqual(
            (254, 255, 260, 261, 256, 258, 259, 257, 262, 263, 264, 265),
            WORKFORCE_EXECUTION_ORDER["AC"],
        )
        self.assertEqual(
            (266, 273, 271, 267, 268, 270, 272, 274, 275, 269, 276, 277),
            WORKFORCE_EXECUTION_ORDER["AD"],
        )

    def test_ab_242_through_253_end_to_end_and_hours_conserve(self) -> None:
        model = make_model()
        apply(
            model,
            "ab-242",
            "record_presence_output_242",
            record_id="presence-1",
            presence_hours=30,
            output_hours=20,
            delivered_value=100,
            reward_presence=False,
        )
        apply(
            model,
            "ab-243",
            "record_after_hours_reply_243",
            message_id="message-1",
            hours=2,
            urgency="critical",
            on_call=True,
            mandatory_for_all=False,
        )
        apply(
            model,
            "ab-244",
            "record_voluntary_effort_244",
            request_id="invite-1",
            voluntary=True,
            written_reward_id="reward-terms-1",
            refused=False,
            frozen_duty_id=None,
            completed=True,
            reward_gold=10,
            reward_recipient_id="count",
        )
        apply(
            model,
            "ab-244-refusal",
            "record_voluntary_effort_244",
            request_id="invite-2",
            voluntary=False,
            written_reward_id=None,
            refused=True,
            frozen_duty_id=None,
        )
        apply(
            model,
            "ab-245",
            "record_overtime_245",
            overtime_id="ot-1",
            hours=5,
            kind=OvertimeKind.APPROVED,
            provenance_id="incident-1",
            approved_by="duke",
        )
        apply(
            model,
            "ab-246",
            "settle_overtime_246",
            compensation_id="comp-1",
            overtime_id="ot-1",
            route=CompensationRoute.GOLD,
            gold_per_hour=3,
        )
        apply(
            model,
            "ab-247",
            "open_sprint_247",
            sprint_id="sprint-1",
            start_day=10,
            end_day=20,
            goal_id="goal-1",
            member_ids=("emperor", "count"),
        )
        apply(
            model,
            "ab-248",
            "record_understaffing_248",
            vacancy_id="vacancy-1",
            overloaded_cycles=3,
            mitigation_route="overtime",
        )
        apply(
            model,
            "ab-249",
            "record_meeting_249",
            meeting_id="meeting-1",
            duration_hours=2,
            attendee_ids=("emperor", "count", "duke"),
            agenda_id="agenda-1",
            decision_owner_id="emperor",
            decision_id="decision-1",
        )
        apply(
            model,
            "ab-250",
            "record_meeting_contribution_250",
            meeting_id="meeting-1",
            evidence_by_contributor={"emperor": "evidence-1"},
        )
        apply(
            model,
            "ab-251",
            "record_meeting_refusal_251",
            refusal_id="refusal-1",
            meeting_id="meeting-1",
            refusing_subject_id="count",
            representative_id=None,
        )
        apply(
            model,
            "ab-252",
            "normalize_leave_252",
            leave_id="leave-1",
            leave_hours=8,
            original_target=100,
            replacement_credit_bps=2_000,
        )
        apply(
            model,
            "ab-253",
            "record_recovery_response_253",
            response_id="response-1",
            response="minimum_duty",
            minimum_duty_met=True,
            appeal_upheld=True,
        )
        self.assertEqual(frozenset(range(242, 254)), model.exact_mechanism_ids_touched)
        self.assertEqual(25, model.gold_credits["count"])
        self.assertEqual(25, model.capacity.work_hours[WorkCategory.OUTPUT])
        self.assertEqual(4, model.capacity.work_hours[WorkCategory.MEETING])
        self.assertEqual(
            model.capacity.accounted_hours,
            sum(model.capacity.work_hours.values()),
        )
        self.assertLessEqual(model.capacity.accounted_hours, model.capacity.authorized_hours)
        self.assertEqual(("emperor",), model.capacity.meetings["meeting-1"].contributors)

    def test_ac_254_through_265_end_to_end_and_resources_conserve(self) -> None:
        model = make_model()
        apply(
            model,
            "ac-254",
            "open_external_contract_254",
            contract_id="contract-1",
            vendor_id="vendor",
            contract_type=ContractType.OUTCOME,
            shadow_hc_units=2,
            budget_gold=100,
            sunset_cycle=4,
        )
        apply(
            model,
            "ac-255",
            "compare_workforce_tco_255",
            contract_id="contract-1",
            tco_by_route={"formal": 120, "external": 110, "mixed": 100},
            selected_route="mixed",
        )
        apply(
            model,
            "ac-260",
            "lock_contract_type_260",
            contract_id="contract-1",
            contract_type=ContractType.OUTCOME,
            ownership_ref="owner-rule-1",
            change_rule_ref="change-rule-1",
        )
        apply(
            model,
            "ac-261",
            "disclose_executor_chain_261",
            contract_id="contract-1",
            executor_chain=("vendor", "tier-2", "executor"),
            actual_executor_id="executor",
        )
        apply(
            model,
            "ac-256",
            "evaluate_supplier_pool_256",
            contract_id="contract-1",
            delivery_score=80,
            quality_score=70,
            sla_score=90,
            decision="renew",
        )
        apply(
            model,
            "ac-258",
            "freeze_controllable_scope_258",
            contract_id="contract-1",
            missing_access_ids=("decision-right",),
            target_adjustment=20,
        )
        apply(
            model,
            "ac-259",
            "allocate_sla_responsibility_259",
            contract_id="contract-1",
            incident_id="sla-incident-1",
            responsibility_bps={"client_change": 3_000, "vendor_management": 7_000},
        )
        apply(
            model,
            "ac-262",
            "open_secondment_review_262",
            secondment_id="secondment-1",
            official_id="count",
            home_manager_id="emperor",
            host_manager_id="duke",
            home_weight=40,
            host_weight=60,
            due_cycle=4,
            return_right="original_role",
        )
        apply(
            model,
            "ac-257",
            "convert_external_worker_257",
            contract_id="contract-1",
            official_id="external",
            effective_cycle=4,
            recruitment_ref="recruitment-1",
        )
        model.cycle_serial = 4
        model._validate()
        apply(
            model,
            "ac-257-settle",
            "settle_external_conversion_257",
            contract_id="contract-1",
        )
        apply(
            model,
            "ac-263",
            "resolve_secondment_return_263",
            secondment_id="secondment-1",
            choice="return",
            as_of_cycle=4,
        )
        apply(
            model,
            "ac-264",
            "accept_knowledge_handoff_264",
            contract_id="contract-1",
            artifact_ids=("documentation", "shadowing", "practical_acceptance"),
            accepted_by="duke",
            as_of_cycle=4,
        )
        apply(
            model,
            "ac-265",
            "audit_external_fraud_265",
            audit_id="audit-1",
            contract_id="contract-1",
            evidence_ids=("invoice", "witness"),
            liability_bps={"vendor": 7_000, "duke": 3_000},
            recovery_gold=20,
            duty_evidence_by_actor={"duke": "duty-evidence-1"},
        )
        audit_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.audit_external_fraud_265(
                model.command("ac-265-ghost"),
                audit_id="audit-ghost",
                contract_id="contract-1",
                evidence_ids=("ghost-claim",),
                liability_bps={"ghost": 10_000},
                recovery_gold=0,
                duty_evidence_by_actor={"ghost": "ghost-duty"},
            )
        self.assertEqual(RedCode.PERMISSION_DENIED, caught.exception.code)
        self.assertEqual(audit_snapshot, model)
        self.assertEqual(frozenset(range(254, 266)), model.exact_mechanism_ids_touched)
        self.assertEqual(8, model.formal_hc_available + model.formal_hc_filled)
        self.assertEqual(4, model.shadow_hc_available + model.shadow_hc_active)
        self.assertEqual(80, model.gold.paid)
        self.assertEqual(80, model.gold_credits["vendor"])
        self.assertEqual(model.gold.total, model.gold.available + model.gold.reserved + model.gold.paid)

    def test_ad_266_through_277_hire_refusal_rehire_and_pip(self) -> None:
        hired = make_model()
        apply(hired, "ad-266", "open_requisition_266", requisition_id="req-1", role_id="role-1", threshold=70, urgency=80)
        apply(hired, "ad-273", "assign_candidate_owner_273", requisition_id="req-1", candidate_id="candidate1", owner_id="emperor", allocation_ref="allocation-1", scout_credit_bps=3_000, hiring_credit_bps=7_000)
        apply(hired, "ad-271", "register_referral_271", requisition_id="req-1", referral_id="referral-1", candidate_id="candidate1", referrer_id="duke", relationship_ref="former-colleague", reward_gold=10)
        apply(hired, "ad-267", "seal_interview_votes_267", requisition_id="req-1", candidate_id="candidate1", votes={"emperor": Vote.HIRE, "duke2": Vote.HOLD}, evidence_by_interviewer={"emperor": "interview-e1", "duke2": "interview-e2"})
        raw_votes = copy.deepcopy(hired.requisitions["req-1"].raw_votes_frozen)
        late_referral_snapshot = copy.deepcopy(hired)
        with self.assertRaises(DomainRed) as caught:
            hired.register_referral_271(
                hired.command("ad-late-referral"),
                requisition_id="req-1",
                referral_id="referral-late",
                candidate_id="candidate1",
                referrer_id="baron",
                relationship_ref="late",
                reward_gold=10,
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(late_referral_snapshot, hired)
        apply(hired, "ad-268", "calibrate_interviewers_268", requisition_id="req-1", normalized_adjustments={"emperor": -2, "duke2": 3}, calibration_snapshot_id="calibration-1")
        apply(hired, "ad-270", "set_hiring_risk_policy_270", requisition_id="req-1", role_class="critical", policy="conservative", threshold=75, policy_version_id="risk-1")
        apply(hired, "ad-272", "issue_offer_272", requisition_id="req-1", offer_id="offer-1", requested_level=5, band_min=3, band_max=4, signing_gold=20, exception_approver_id="emperor", premium_end_cycle=5)
        apply(hired, "ad-274", "resolve_counteroffer_274", requisition_id="req-1", competitor_terms_ref="competitor-1", additional_gold=5, fairness_cap_gold=10)
        apply(hired, "ad-269", "write_back_hire_quality_269", requisition_id="req-1", outcome_id="outcome-1", quality="pass", evidence_ids=("probation-1",), attribution_bps={"emperor": 6_000, "duke2": 4_000}, observed_cycle=4)
        quality_snapshot = copy.deepcopy(hired)
        with self.assertRaises(DomainRed) as caught:
            hired.write_back_hire_quality_269(
                hired.command("ad-269-repeat"),
                requisition_id="req-1",
                outcome_id="outcome-2",
                quality="mismatch",
                evidence_ids=("probation-2",),
                attribution_bps={"emperor": 6_000, "duke2": 4_000},
                observed_cycle=5,
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(quality_snapshot, hired)
        self.assertEqual(raw_votes, hired.requisitions["req-1"].raw_votes_frozen)
        self.assertEqual(25, hired.gold_credits["candidate1"])
        self.assertEqual(10, hired.gold_credits["duke"])
        self.assertEqual(0, hired.formal_hc_reserved)
        self.assertEqual(1, hired.formal_hc_filled)

        refused = make_model()
        apply(refused, "ad2-266", "open_requisition_266", requisition_id="req-2", role_id="role-2", threshold=60, urgency=50)
        apply(refused, "ad2-273", "assign_candidate_owner_273", requisition_id="req-2", candidate_id="candidate2", owner_id="duke", allocation_ref="allocation-2", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        apply(refused, "ad2-267", "seal_interview_votes_267", requisition_id="req-2", candidate_id="candidate2", votes={"emperor": Vote.HIRE}, evidence_by_interviewer={"emperor": "interview-e3"})
        apply(refused, "ad2-268", "calibrate_interviewers_268", requisition_id="req-2", normalized_adjustments={"emperor": 0}, calibration_snapshot_id="calibration-2")
        apply(refused, "ad2-272", "issue_offer_272", requisition_id="req-2", offer_id="offer-2", requested_level=3, band_min=2, band_max=4, signing_gold=10)
        apply(refused, "ad2-275a", "handle_offer_refusal_275", requisition_id="req-2", as_of_cycle=3, hold_until_cycle=5, refusal_reason="compensation")
        self.assertEqual(1, refused.formal_hc_reserved)
        self.assertEqual(0, refused.gold.reserved)
        hold_snapshot = copy.deepcopy(refused)
        with self.assertRaises(DomainRed) as caught:
            refused.handle_offer_refusal_275(
                refused.command("ad2-fake-clock"),
                requisition_id="req-2",
                as_of_cycle=999,
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(hold_snapshot, refused)
        refused.cycle_serial = 5
        refused._validate()
        apply(refused, "ad2-275b", "handle_offer_refusal_275", requisition_id="req-2", as_of_cycle=5)
        self.assertEqual(0, refused.formal_hc_reserved)
        self.assertEqual(8, refused.formal_hc_available)
        apply(refused, "ad2-276", "register_rehire_276", rehire_id="rehire-1", official_id="candidate1", historical_case_ids=("history-1",), growth_evidence_ids=("external-growth-1",), new_cycle=6, retain_misconduct=True)
        available_before_pip = hired.formal_hc_available
        filled_before_pip = hired.formal_hc_filled
        apply(hired, "ad2-277", "record_pip_exit_277", exit_id="pip-exit-1", pip_case_id="pip-closed-1", displaced_subject_id="candidate1", former_hc_slot_id="hc-slot-1", remaining_work_hours=40, workload_provenance_id="workload-1", backfill_route="request_backfill")
        self.assertEqual(available_before_pip, hired.formal_hc_available)
        self.assertEqual(filled_before_pip - 1, hired.formal_hc_filled)
        self.assertEqual(1, hired.formal_hc_vacant)
        self.assertEqual(
            hired.formal_hc_total,
            hired.formal_hc_available
            + hired.formal_hc_reserved
            + hired.formal_hc_filled
            + hired.formal_hc_vacant,
        )
        touched = hired.exact_mechanism_ids_touched | refused.exact_mechanism_ids_touched
        self.assertEqual(frozenset(range(266, 278)), touched)

    def test_275_runner_up_uses_distinct_central_requisition_atomically(self) -> None:
        model = make_model()
        apply(model, "runner-266", "open_requisition_266", requisition_id="req-old", role_id="role-runner", threshold=60, urgency=50)
        apply(model, "runner-273", "assign_candidate_owner_273", requisition_id="req-old", candidate_id="candidate2", owner_id="duke", allocation_ref="allocation-old", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        apply(model, "runner-267", "seal_interview_votes_267", requisition_id="req-old", candidate_id="candidate2", votes={"emperor": Vote.HIRE}, evidence_by_interviewer={"emperor": "old-vote-evidence"})
        apply(model, "runner-268", "calibrate_interviewers_268", requisition_id="req-old", normalized_adjustments={"emperor": 0}, calibration_snapshot_id="old-calibration")
        apply(model, "runner-272", "issue_offer_272", requisition_id="req-old", offer_id="old-offer", requested_level=3, band_min=2, band_max=4, signing_gold=10)
        apply(model, "runner-275-hold", "handle_offer_refusal_275", requisition_id="req-old", as_of_cycle=3, hold_until_cycle=5, refusal_reason="compensation")
        old_case = model.requisitions["req-old"].case_serial
        old_votes = copy.deepcopy(model.requisitions["req-old"].raw_votes_frozen)
        old_offer = model.requisitions["req-old"].offer_id
        model.cycle_serial = 5
        model._validate()

        incomplete_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed):
            model.handle_offer_refusal_275(
                model.command("runner-incomplete"),
                requisition_id="req-old",
                as_of_cycle=5,
                runner_up_id="candidate1",
            )
        self.assertEqual(incomplete_snapshot, model)

        same_case_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.handle_offer_refusal_275(
                model.command("runner-same-case"),
                requisition_id="req-old",
                as_of_cycle=5,
                runner_up_id="candidate1",
                runner_up_evidence_id="runner-evidence",
                new_requisition_id="req-new",
                new_requisition_case=old_case,
                central_receipt_id="central-receipt",
                central_receipt_hash="central-hash",
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(same_case_snapshot, model)

        ghost_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.handle_offer_refusal_275(
                model.command("runner-ghost"),
                requisition_id="req-old",
                as_of_cycle=5,
                runner_up_id="ghost",
                runner_up_evidence_id="runner-evidence",
                new_requisition_id="req-new",
                new_requisition_case=99001,
                central_receipt_id="central-receipt",
                central_receipt_hash="central-hash",
            )
        self.assertEqual(RedCode.NOT_FOUND, caught.exception.code)
        self.assertEqual(ghost_snapshot, model)

        reserved_before = model.formal_hc_reserved
        available_before = model.formal_hc_available
        reopen_token = model.command("runner-reopen")
        result = model.handle_offer_refusal_275(
            reopen_token,
            requisition_id="req-old",
            as_of_cycle=5,
            runner_up_id="candidate1",
            runner_up_evidence_id="runner-evidence",
            new_requisition_id="req-new",
            new_requisition_case=99001,
            central_receipt_id="central-receipt",
            central_receipt_hash="central-hash",
        )
        self.assertEqual(ActionStatus.APPLIED, result.status)
        old = model.requisitions["req-old"]
        new = model.requisitions["req-new"]
        receipt = model.requisition_open_receipts["central-receipt"]
        self.assertEqual("closed", old.status.value)
        self.assertFalse(old.hc_reservation_active)
        self.assertIsNone(old.hc_flight_case)
        self.assertEqual(old_votes, old.raw_votes_frozen)
        self.assertEqual(old_offer, old.offer_id)
        self.assertEqual("open", new.status.value)
        self.assertEqual("req-old", new.predecessor_requisition_id)
        self.assertEqual(99001, new.case_serial)
        self.assertEqual(99001, new.candidate_active_case)
        self.assertEqual(99001, new.hc_flight_case)
        self.assertEqual("candidate1", new.candidate_id)
        self.assertEqual((), new.raw_votes_frozen)
        self.assertIsNone(new.offer_id)
        self.assertEqual(old_case, receipt.predecessor_case_serial)
        self.assertEqual(old_case, receipt.hc_lineage_case_serial)
        self.assertEqual("count", receipt.original_subject_id)
        self.assertEqual("runner-evidence", receipt.runner_evidence_id)
        self.assertEqual(reserved_before, model.formal_hc_reserved)
        self.assertEqual(available_before, model.formal_hc_available)

        replay = model.handle_offer_refusal_275(
            reopen_token,
            requisition_id="req-old",
            as_of_cycle=5,
            runner_up_id="candidate1",
            runner_up_evidence_id="runner-evidence",
            new_requisition_id="req-new",
            new_requisition_case=99001,
            central_receipt_id="central-receipt",
            central_receipt_hash="central-hash",
        )
        self.assertEqual(ActionStatus.IDEMPOTENT_NOOP, replay.status)
        collision_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.handle_offer_refusal_275(
                model.command("runner-reopen"),
                requisition_id="req-old",
                as_of_cycle=5,
                runner_up_id="candidate1",
                runner_up_evidence_id="runner-evidence",
                new_requisition_id="req-new",
                new_requisition_case=99001,
                central_receipt_id="central-receipt",
                central_receipt_hash="different-hash",
            )
        self.assertEqual(RedCode.COMMAND_COLLISION, caught.exception.code)
        self.assertEqual(collision_snapshot, model)

        apply(model, "runner-new-owner", "assign_candidate_owner_273", requisition_id="req-new", candidate_id="candidate1", owner_id="emperor", allocation_ref="allocation-new", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        apply(model, "runner-new-votes", "seal_interview_votes_267", requisition_id="req-new", candidate_id="candidate1", votes={"duke2": Vote.HOLD}, evidence_by_interviewer={"duke2": "new-vote-evidence"})
        self.assertEqual(old_votes, model.requisitions["req-old"].raw_votes_frozen)
        self.assertEqual((("duke2", Vote.HOLD),), model.requisitions["req-new"].raw_votes_frozen)
        model.cycle_serial = 6
        model._validate()

    def test_al_endgame_is_historical_and_future_only(self) -> None:
        model = make_model()
        historical_before = copy.deepcopy(model.historical_cases)
        baseline = model.defaults_for_cycle(3)
        apply(model, "al-355", "apply_target_ratchet_355", ratchet_id="ratchet-1", official_id="count", prior_cycle=2, replicability_ref="repeatability-1", prior_target=100, prior_actual=130, repeatable_excess=20, windfall_excess=10, mode=RatchetMode.LIMITED, cap_bps=1_000, added_resource_gold=20, authority_ref="resource-approval-1")
        ratchet_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.apply_target_ratchet_355(
                model.command("al-355-duplicate-facts"),
                ratchet_id="ratchet-2",
                official_id="count",
                prior_cycle=2,
                replicability_ref="repeatability-2",
                prior_target=100,
                prior_actual=130,
                repeatable_excess=20,
                windfall_excess=10,
                mode=RatchetMode.HOLD,
                cap_bps=0,
                added_resource_gold=0,
                authority_ref=None,
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(ratchet_snapshot, model)
        apply(model, "al-355-peak-risk", "apply_target_ratchet_355", ratchet_id="ratchet-peak", official_id="baron", prior_cycle=2, replicability_ref="repeatability-peak", prior_target=100, prior_actual=150, repeatable_excess=50, windfall_excess=0, mode=RatchetMode.PEAK, cap_bps=10_000, added_resource_gold=0, authority_ref=None)
        self.assertEqual(50, model.target_ratchets["ratchet-peak"].underproduction_risk)
        apply(model, "al-356", "settle_outcome_timing_356", outcome_id="outcome-timing-1", actual_value=50, actual_completion_cycle=1, report_cycle=3, reported_value_by_cycle={1: 50}, evidence_timestamp_ids=("timestamp-1",))
        outcome_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.settle_outcome_timing_356(
                model.command("al-356-reuse"),
                outcome_id="outcome-timing-2",
                actual_value=50,
                actual_completion_cycle=1,
                report_cycle=3,
                reported_value_by_cycle={1: 50},
                evidence_timestamp_ids=("timestamp-1",),
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(outcome_snapshot, model)
        with self.assertRaises(DomainRed) as caught:
            model.settle_outcome_timing_356(
                model.command("al-356-future"),
                outcome_id="outcome-timing-future",
                actual_value=10,
                actual_completion_cycle=4,
                report_cycle=4,
                reported_value_by_cycle={4: 10},
                evidence_timestamp_ids=("timestamp-future",),
            )
        self.assertEqual(RedCode.PROVENANCE_INVALID, caught.exception.code)
        self.assertEqual(outcome_snapshot, model)
        apply(
            model,
            "al-360",
            "resolve_collective_action_360",
            collective_id="collective-1",
            authoritative_members_by_cohort={"cohort-a": ("count", "baron"), "cohort-b": ("candidate1", "candidate2")},
            agenda_by_cohort={"cohort-a": ("baron", "count"), "cohort-b": ("candidate2", "candidate1")},
            c_quota_by_cohort={"cohort-a": 1, "cohort-b": 1},
            forced_c_by_cohort={"cohort-a": ("count",), "cohort-b": ()},
            approved_exceptions_by_cohort={"cohort-a": (), "cohort-b": ("candidate1",)},
            exception_approver_by_cohort={"cohort-a": None, "cohort-b": "emperor"},
            manager_by_cohort={"cohort-a": "emperor", "cohort-b": "duke"},
            evidence_by_cohort={"cohort-a": "minutes-a", "cohort-b": "minutes-b"},
            reform_effective_cycle=4,
        )
        new_defaults = PolicyDefaults(
            DeliveryHorizon.LONG_TERM,
            "exception_audited",
            "symmetric_reopen",
            "verified_delivery",
            "vacancy_bound",
            "collective_review",
            "full_receipts",
        )
        priorities = (
            CharterPriority.EVIDENCE_FAIRNESS,
            CharterPriority.ORGANIZATIONAL_WARMTH,
            CharterPriority.FORCED_COMPETITION,
            CharterPriority.LONG_TERM_INNOVATION,
        )
        mixed_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.adopt_charter_361(
                model.command("al-361-mixed-route"),
                charter_id="charter-mixed",
                priority_order=tuple(CharterPriority),
                defaults=new_defaults,
                completed_cycle_ids=(1, 2, 3),
                long_run_report_id="report-mixed",
                adopted_day=98,
                effective_cycle=4,
                amendment_due_cycle=7,
                visible_costs=("manager-time",),
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(mixed_snapshot, model)
        future_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.adopt_charter_361(
                model.command("al-361-future-evidence"),
                charter_id="charter-future",
                priority_order=priorities,
                defaults=new_defaults,
                completed_cycle_ids=(1, 2, 4),
                long_run_report_id="report-future",
                adopted_day=99,
                effective_cycle=4,
                amendment_due_cycle=7,
                visible_costs=("manager-time",),
            )
        self.assertEqual(RedCode.PROVENANCE_INVALID, caught.exception.code)
        self.assertEqual(future_snapshot, model)
        apply(model, "al-361", "adopt_charter_361", charter_id="charter-1", priority_order=priorities, defaults=new_defaults, completed_cycle_ids=(1, 2, 3), long_run_report_id="report-1", adopted_day=100, effective_cycle=4, amendment_due_cycle=7, visible_costs=("manager-time", "appeal-load"))
        self.assertEqual({355, 356, 360, 361}, model.exact_mechanism_ids_touched)
        self.assertEqual(historical_before, model.historical_cases)
        self.assertEqual(baseline, model.defaults_for_cycle(3))
        self.assertEqual(new_defaults, model.defaults_for_cycle(4))
        self.assertEqual(20, model.gold.reserved)
        self.assertEqual(1, model.manager_score_cost["duke"])
        self.assertNotIn("emperor", model.manager_score_cost)
        collective = model.collective_actions["collective-1"]
        self.assertEqual(("baron", "count"), tuple(sorted(dict(collective.agenda_by_cohort)["cohort-a"])))
        model.cycle_serial = 4
        model._validate()
        apply(model, "al-361-v2", "adopt_charter_361", charter_id="charter-2", priority_order=priorities, defaults=new_defaults, completed_cycle_ids=(1, 2, 3), long_run_report_id="report-1", adopted_day=110, effective_cycle=5, amendment_due_cycle=8, visible_costs=("manager-time",))
        model.cycle_serial = 5
        model._validate()
        self.assertEqual(new_defaults, model.defaults_for_cycle(5))
        snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.adopt_charter_361(
                model.command("al-361-bad"),
                charter_id="charter-3",
                priority_order=priorities,
                defaults=new_defaults,
                completed_cycle_ids=(1, 2, 3),
                long_run_report_id="report-2",
                adopted_day=120,
                effective_cycle=6,
                amendment_due_cycle=9,
                visible_costs=("manager-time",),
            )
        self.assertEqual(RedCode.PROVENANCE_INVALID, caught.exception.code)
        self.assertEqual(snapshot, model)

    def test_permissions_stale_idempotent_collision_and_atomic_red(self) -> None:
        model = make_model()
        denied_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.open_requisition_266(
                model.command("denied", actor_id="count"),
                requisition_id="req-denied",
                role_id="role",
                threshold=50,
                urgency=50,
            )
        self.assertEqual(RedCode.PERMISSION_DENIED, caught.exception.code)
        self.assertEqual(denied_snapshot, model)
        self.assertTrue(model.can_handle_own_assessment("count", "count"))
        self.assertFalse(model.can_handle_own_assessment("baron", "count"))

        bad_snapshot = copy.deepcopy(model)
        with self.assertRaises(DomainRed) as caught:
            model.open_requisition_266(
                model.command("bool-is-not-one"),
                requisition_id="req-bool",
                role_id="role",
                threshold=True,
                urgency=1,
            )
        self.assertEqual(RedCode.INVALID_VALUE, caught.exception.code)
        self.assertEqual(bad_snapshot, model)

        stale = model.command("stale")
        command = model.command("once")
        first = model.open_requisition_266(
            command,
            requisition_id="req-once",
            role_id="role",
            threshold=50,
            urgency=50,
        )
        self.assertEqual(ActionStatus.APPLIED, first.status)
        before_replay = copy.deepcopy(model)
        replay = model.open_requisition_266(
            command,
            requisition_id="req-once",
            role_id="role",
            threshold=50,
            urgency=50,
        )
        self.assertEqual(ActionStatus.IDEMPOTENT_NOOP, replay.status)
        self.assertEqual(before_replay, model)
        with self.assertRaises(DomainRed) as caught:
            model.open_requisition_266(
                command,
                requisition_id="req-different",
                role_id="role",
                threshold=50,
                urgency=50,
            )
        self.assertEqual(RedCode.COMMAND_COLLISION, caught.exception.code)
        self.assertEqual(before_replay, model)
        stale_result = model.open_requisition_266(
            stale,
            requisition_id="",
            role_id="",
            threshold=True,
            urgency=True,
        )
        self.assertEqual(ActionStatus.STALE_NOOP, stale_result.status)
        self.assertEqual(before_replay, model)

        restored = pickle.loads(pickle.dumps(model))
        restored_replay = restored.open_requisition_266(
            command,
            requisition_id="req-once",
            role_id="role",
            threshold=50,
            urgency=50,
        )
        self.assertEqual(ActionStatus.IDEMPOTENT_NOOP, restored_replay.status)
        self.assertEqual(model, restored)

    def test_resource_hours_identity_and_provenance_reds_are_atomic(self) -> None:
        gold_model = make_model()
        gold_snapshot = copy.deepcopy(gold_model)
        with self.assertRaises(DomainRed) as caught:
            gold_model.open_external_contract_254(
                gold_model.command("no-gold"),
                contract_id="contract-too-large",
                vendor_id="vendor",
                contract_type=ContractType.OUTCOME,
                shadow_hc_units=1,
                budget_gold=2_001,
                sunset_cycle=4,
            )
        self.assertEqual(RedCode.RESOURCE_EXHAUSTED, caught.exception.code)
        self.assertEqual(gold_snapshot, gold_model)

        shape_model = make_model()
        apply(
            shape_model,
            "shape-contract",
            "open_external_contract_254",
            contract_id="contract-shape",
            vendor_id="vendor",
            contract_type=ContractType.OUTCOME,
            shadow_hc_units=1,
            budget_gold=10,
            sunset_cycle=4,
        )
        shape_snapshot = copy.deepcopy(shape_model)
        with self.assertRaises(DomainRed) as caught:
            shape_model.compare_workforce_tco_255(
                shape_model.command("bad-shape"),
                contract_id="contract-shape",
                tco_by_route=None,
                selected_route="external",
            )
        self.assertEqual(RedCode.INVALID_TYPE, caught.exception.code)
        self.assertEqual(shape_snapshot, shape_model)

        hc_model = make_model()
        hc_model.formal_hc_available = 0
        hc_model.formal_hc_filled = 8
        hc_model.formal_hc_occupants = {"count": 8}
        hc_model._validate()
        hc_snapshot = copy.deepcopy(hc_model)
        with self.assertRaises(DomainRed) as caught:
            hc_model.open_requisition_266(
                hc_model.command("no-hc"),
                requisition_id="req-no-hc",
                role_id="role",
                threshold=50,
                urgency=50,
            )
        self.assertEqual(RedCode.RESOURCE_EXHAUSTED, caught.exception.code)
        self.assertEqual(hc_snapshot, hc_model)

        hours_model = make_model()
        hours_snapshot = copy.deepcopy(hours_model)
        with self.assertRaises(DomainRed) as caught:
            hours_model.record_meeting_249(
                hours_model.command("too-many-hours"),
                meeting_id="meeting-too-large",
                duration_hours=20,
                attendee_ids=("emperor", "duke", "count"),
                agenda_id="agenda",
                decision_owner_id="emperor",
                decision_id=None,
            )
        self.assertEqual(RedCode.HOURS_IMBALANCE, caught.exception.code)
        self.assertEqual(hours_snapshot, hours_model)

        identity_model = make_model()
        identity_snapshot = copy.deepcopy(identity_model)
        with self.assertRaises(DomainRed) as caught:
            identity_model.open_sprint_247(
                identity_model.command("ghost-member"),
                sprint_id="sprint",
                start_day=1,
                end_day=2,
                goal_id="goal",
                member_ids=("ghost",),
            )
        self.assertEqual(RedCode.NOT_FOUND, caught.exception.code)
        self.assertEqual(identity_snapshot, identity_model)

        agenda_model = make_model()
        agenda_snapshot = copy.deepcopy(agenda_model)
        with self.assertRaises(DomainRed) as caught:
            agenda_model.resolve_collective_action_360(
                agenda_model.command("partial-agenda"),
                collective_id="collective",
                authoritative_members_by_cohort={"cohort": ("count", "baron")},
                agenda_by_cohort={"cohort": ("count",)},
                c_quota_by_cohort={"cohort": 1},
                forced_c_by_cohort={"cohort": ("count",)},
                approved_exceptions_by_cohort={"cohort": ()},
                exception_approver_by_cohort={"cohort": None},
                manager_by_cohort={"cohort": "emperor"},
                evidence_by_cohort={"cohort": "minutes"},
                reform_effective_cycle=None,
            )
        self.assertEqual(RedCode.PROVENANCE_INVALID, caught.exception.code)
        self.assertEqual(agenda_snapshot, agenda_model)

        with self.assertRaises(DomainRed) as caught:
            CommandToken(
                "workforce-endgame",
                "emperor",
                "count",
                3,
                77,
                False,
                "emperor",
                "bool-revision",
            )
        self.assertEqual(RedCode.INVALID_VALUE, caught.exception.code)

    def test_ab_ac_regressions_and_global_identity_uniqueness(self) -> None:
        ab = make_model()
        snapshot = copy.deepcopy(ab)
        with self.assertRaises(DomainRed) as caught:
            ab.record_after_hours_reply_243(
                ab.command("normal-without-duty"),
                message_id="normal-message",
                hours=1,
                urgency="normal",
                on_call=False,
                mandatory_for_all=False,
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(snapshot, ab)
        apply(ab, "meeting", "record_meeting_249", meeting_id="meeting", duration_hours=1, attendee_ids=("emperor", "count"), agenda_id="agenda", decision_owner_id="emperor", decision_id=None)
        apply(ab, "empty-contrib", "record_meeting_contribution_250", meeting_id="meeting", evidence_by_contributor={})
        sealed_snapshot = copy.deepcopy(ab)
        with self.assertRaises(DomainRed) as caught:
            ab.record_meeting_contribution_250(
                ab.command("empty-contrib-again"),
                meeting_id="meeting",
                evidence_by_contributor={},
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(sealed_snapshot, ab)
        with self.assertRaises(DomainRed) as caught:
            ab.record_meeting_refusal_251(
                ab.command("owner-refusal"),
                refusal_id="owner-refusal",
                meeting_id="meeting",
                refusing_subject_id="emperor",
                representative_id="duke",
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(sealed_snapshot, ab)
        with self.assertRaises(DomainRed) as caught:
            ab.record_meeting_refusal_251(
                ab.command("unbudgeted-representative"),
                refusal_id="unbudgeted-representative",
                meeting_id="meeting",
                refusing_subject_id="count",
                representative_id="baron",
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(sealed_snapshot, ab)

        contract_model = make_model()
        apply(contract_model, "contract-open", "open_external_contract_254", contract_id="contract", vendor_id="vendor", contract_type=ContractType.OUTCOME, shadow_hc_units=1, budget_gold=10, sunset_cycle=5)
        contract_snapshot = copy.deepcopy(contract_model)
        with self.assertRaises(DomainRed) as caught:
            contract_model.lock_contract_type_260(
                contract_model.command("type-mismatch"),
                contract_id="contract",
                contract_type=ContractType.STAFF_AUGMENTATION,
                ownership_ref="owner-rule",
                change_rule_ref="change-rule",
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(contract_snapshot, contract_model)
        apply(contract_model, "scope-empty", "freeze_controllable_scope_258", contract_id="contract", missing_access_ids=(), target_adjustment=0)
        scope_snapshot = copy.deepcopy(contract_model)
        with self.assertRaises(DomainRed) as caught:
            contract_model.freeze_controllable_scope_258(
                contract_model.command("scope-empty-repeat"),
                contract_id="contract",
                missing_access_ids=(),
                target_adjustment=0,
            )
        self.assertEqual(RedCode.DUPLICATE, caught.exception.code)
        self.assertEqual(scope_snapshot, contract_model)
        apply(contract_model, "type-lock", "lock_contract_type_260", contract_id="contract", contract_type=ContractType.OUTCOME, ownership_ref="owner-rule", change_rule_ref="change-rule")
        apply(contract_model, "chain", "disclose_executor_chain_261", contract_id="contract", executor_chain=("vendor", "executor"), actual_executor_id="executor")
        apply(contract_model, "supplier", "evaluate_supplier_pool_256", contract_id="contract", delivery_score=80, quality_score=80, sla_score=80, decision="renew")
        apply(contract_model, "incident-1", "allocate_sla_responsibility_259", contract_id="contract", incident_id="incident-1", responsibility_bps={"vendor_management": 10_000})
        apply(contract_model, "incident-2", "allocate_sla_responsibility_259", contract_id="contract", incident_id="incident-2", responsibility_bps={"client_change": 10_000})
        self.assertEqual({"incident-1", "incident-2"}, set(contract_model.external_contracts["contract"].responsibility_by_incident))
        early_snapshot = copy.deepcopy(contract_model)
        with self.assertRaises(DomainRed):
            contract_model.accept_knowledge_handoff_264(
                contract_model.command("early-handoff"),
                contract_id="contract",
                artifact_ids=("documentation", "shadowing", "practical_acceptance"),
                accepted_by="duke",
                as_of_cycle=3,
            )
        self.assertEqual(early_snapshot, contract_model)

        roles = make_model()
        apply(roles, "role-1", "open_requisition_266", requisition_id="req-1", role_id="same-role", threshold=50, urgency=50)
        role_snapshot = copy.deepcopy(roles)
        with self.assertRaises(DomainRed):
            roles.open_requisition_266(roles.command("role-duplicate"), requisition_id="req-2", role_id="same-role", threshold=50, urgency=50)
        self.assertEqual(role_snapshot, roles)
        apply(roles, "role-2", "open_requisition_266", requisition_id="req-2", role_id="other-role", threshold=50, urgency=50)
        apply(roles, "owner-1", "assign_candidate_owner_273", requisition_id="req-1", candidate_id="candidate1", owner_id="emperor", allocation_ref="allocation-1", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        candidate_snapshot = copy.deepcopy(roles)
        with self.assertRaises(DomainRed):
            roles.assign_candidate_owner_273(roles.command("owner-duplicate"), requisition_id="req-2", candidate_id="candidate1", owner_id="duke", allocation_ref="allocation-2", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        self.assertEqual(candidate_snapshot, roles)

        conversion = make_model()
        for suffix in ("1", "2"):
            apply(conversion, f"open-{suffix}", "open_external_contract_254", contract_id=f"contract-{suffix}", vendor_id=f"vendor-{suffix}", contract_type=ContractType.OUTCOME, shadow_hc_units=1, budget_gold=10, sunset_cycle=5)
            apply(conversion, f"lock-{suffix}", "lock_contract_type_260", contract_id=f"contract-{suffix}", contract_type=ContractType.OUTCOME, ownership_ref=f"owner-{suffix}", change_rule_ref=f"change-{suffix}")
            apply(conversion, f"chain-{suffix}", "disclose_executor_chain_261", contract_id=f"contract-{suffix}", executor_chain=(f"vendor-{suffix}", f"executor-{suffix}"), actual_executor_id=f"executor-{suffix}")
            apply(conversion, f"score-{suffix}", "evaluate_supplier_pool_256", contract_id=f"contract-{suffix}", delivery_score=80, quality_score=80, sla_score=80, decision="renew")
        apply(conversion, "conversion-1", "convert_external_worker_257", contract_id="contract-1", official_id="external", effective_cycle=4, recruitment_ref="recruitment-1")
        conversion_snapshot = copy.deepcopy(conversion)
        with self.assertRaises(DomainRed) as caught:
            conversion.convert_external_worker_257(conversion.command("conversion-2"), contract_id="contract-2", official_id="external", effective_cycle=4, recruitment_ref="recruitment-2")
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(conversion_snapshot, conversion)

        secondment = make_model()
        apply(secondment, "secondment", "open_secondment_review_262", secondment_id="secondment", official_id="count", home_manager_id="emperor", host_manager_id="duke", home_weight=50, host_weight=50, due_cycle=4, return_right="original_role")
        secondment_snapshot = copy.deepcopy(secondment)
        with self.assertRaises(DomainRed) as caught:
            secondment.resolve_secondment_return_263(secondment.command("fake-secondment-clock"), secondment_id="secondment", choice="permanent", as_of_cycle=4)
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(secondment_snapshot, secondment)
        secondment.cycle_serial = 4
        secondment._validate()
        apply(secondment, "extend", "resolve_secondment_return_263", secondment_id="secondment", choice="extend", as_of_cycle=4, extension_due_cycle=6)
        self.assertIsNone(secondment.secondments["secondment"].resolved_choice)
        secondment.cycle_serial = 6
        secondment._validate()
        apply(secondment, "return", "resolve_secondment_return_263", secondment_id="secondment", choice="return", as_of_cycle=6)
        self.assertEqual("return", secondment.secondments["secondment"].resolved_choice)

        late = make_model()
        apply(late, "late-open", "open_requisition_266", requisition_id="late-req", role_id="late-role", threshold=50, urgency=50)
        apply(late, "late-owner", "assign_candidate_owner_273", requisition_id="late-req", candidate_id="candidate1", owner_id="emperor", allocation_ref="late-allocation", scout_credit_bps=5_000, hiring_credit_bps=5_000)
        apply(late, "late-vote", "seal_interview_votes_267", requisition_id="late-req", candidate_id="candidate1", votes={"emperor": Vote.HIRE}, evidence_by_interviewer={"emperor": "late-evidence"})
        apply(late, "late-calibration", "calibrate_interviewers_268", requisition_id="late-req", normalized_adjustments={"emperor": 0}, calibration_snapshot_id="late-calibration")
        apply(late, "late-offer", "issue_offer_272", requisition_id="late-req", offer_id="late-offer", requested_level=3, band_min=2, band_max=4, signing_gold=0)
        apply(late, "late-hire", "resolve_counteroffer_274", requisition_id="late-req", competitor_terms_ref="late-competitor", additional_gold=0, fairness_cap_gold=0)
        apply(late, "late-quality", "write_back_hire_quality_269", requisition_id="late-req", outcome_id="late-outcome", quality="pass", evidence_ids=("late-probation",), attribution_bps={"emperor": 10_000}, observed_cycle=4)
        late_snapshot = copy.deepcopy(late)
        with self.assertRaises(DomainRed) as caught:
            late.register_referral_271(late.command("backdated-referral"), requisition_id="late-req", referral_id="backdated", candidate_id="candidate1", referrer_id="duke", relationship_ref="backdated", reward_gold=10)
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(late_snapshot, late)

    def test_263_permanent_rejects_pending_conversion_or_requisition_identity_atomically(self) -> None:
        conversion = make_model()
        apply(
            conversion,
            "conversion-contract",
            "open_external_contract_254",
            contract_id="conversion-contract",
            vendor_id="conversion-vendor",
            contract_type=ContractType.OUTCOME,
            shadow_hc_units=1,
            budget_gold=10,
            sunset_cycle=5,
        )
        apply(
            conversion,
            "conversion-lock",
            "lock_contract_type_260",
            contract_id="conversion-contract",
            contract_type=ContractType.OUTCOME,
            ownership_ref="conversion-owner",
            change_rule_ref="conversion-change",
        )
        apply(
            conversion,
            "conversion-chain",
            "disclose_executor_chain_261",
            contract_id="conversion-contract",
            executor_chain=("conversion-vendor", "conversion-executor"),
            actual_executor_id="conversion-executor",
        )
        apply(
            conversion,
            "conversion-score",
            "evaluate_supplier_pool_256",
            contract_id="conversion-contract",
            delivery_score=80,
            quality_score=80,
            sla_score=80,
            decision="renew",
        )
        apply(
            conversion,
            "conversion-reserve",
            "convert_external_worker_257",
            contract_id="conversion-contract",
            official_id="external",
            effective_cycle=4,
            recruitment_ref="conversion-recruitment",
        )
        apply(
            conversion,
            "conversion-secondment",
            "open_secondment_review_262",
            secondment_id="conversion-secondment",
            official_id="external",
            home_manager_id="emperor",
            host_manager_id="duke",
            home_weight=50,
            host_weight=50,
            due_cycle=4,
            return_right="permanent_option",
        )
        conversion.cycle_serial = 4
        conversion._validate()
        conversion_snapshot = copy.deepcopy(conversion)
        with self.assertRaises(DomainRed) as caught:
            conversion.resolve_secondment_return_263(
                conversion.command("conversion-permanent-collision"),
                secondment_id="conversion-secondment",
                choice="permanent",
                as_of_cycle=4,
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(conversion_snapshot, conversion)
        self.assertEqual((7, 1, 0), (
            conversion.formal_hc_available,
            conversion.formal_hc_reserved,
            conversion.formal_hc_filled,
        ))
        apply(
            conversion,
            "conversion-settle",
            "settle_external_conversion_257",
            contract_id="conversion-contract",
        )
        self.assertEqual((7, 0, 1), (
            conversion.formal_hc_available,
            conversion.formal_hc_reserved,
            conversion.formal_hc_filled,
        ))
        self.assertEqual(1, conversion.formal_hc_occupants["external"])

        requisition = make_model()
        apply(
            requisition,
            "requisition-open",
            "open_requisition_266",
            requisition_id="requisition",
            role_id="requisition-role",
            threshold=50,
            urgency=50,
        )
        apply(
            requisition,
            "requisition-owner",
            "assign_candidate_owner_273",
            requisition_id="requisition",
            candidate_id="external",
            owner_id="emperor",
            allocation_ref="requisition-allocation",
            scout_credit_bps=5_000,
            hiring_credit_bps=5_000,
        )
        apply(
            requisition,
            "requisition-secondment",
            "open_secondment_review_262",
            secondment_id="requisition-secondment",
            official_id="external",
            home_manager_id="emperor",
            host_manager_id="duke",
            home_weight=50,
            host_weight=50,
            due_cycle=4,
            return_right="permanent_option",
        )
        requisition.cycle_serial = 4
        requisition._validate()
        requisition_snapshot = copy.deepcopy(requisition)
        with self.assertRaises(DomainRed) as caught:
            requisition.resolve_secondment_return_263(
                requisition.command("requisition-permanent-collision"),
                secondment_id="requisition-secondment",
                choice="permanent",
                as_of_cycle=4,
            )
        self.assertEqual(RedCode.STATE_CONFLICT, caught.exception.code)
        self.assertEqual(requisition_snapshot, requisition)


if __name__ == "__main__":
    unittest.main()
