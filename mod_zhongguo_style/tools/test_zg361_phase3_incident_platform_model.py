#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density tests for phase-three mechanisms 192--228."""

from __future__ import annotations

import copy
import dataclasses
import unittest
from typing import Callable

import zg361_phase3_incident_platform_model as model


def identity(case_serial: int, *, subject: str) -> model.CaseIdentity:
    return model.CaseIdentity("manager-10", subject, 7, case_serial)


def source(mechanism_id: int, suffix: str = "facts") -> tuple[model.SourceRef, ...]:
    return (model.SourceRef("frozen-case-fact", f"m{mechanism_id}:{suffix}", 1),)


def incident_before_credit_netting(case_serial: int = 990) -> model.IncidentCase:
    """Build the shortest legal X lifecycle through the frozen #197 split."""

    case = model.IncidentCase(
        identity(case_serial, subject="incident-credit-audit"),
        model.IncidentState.ON_CALL.value,
    )
    case.configure_rotation(
        case.token(),
        "audit-m192",
        members=("actor", "backup"),
        on_call_id="actor",
        sources=source(192),
    )
    case.record_alert(
        case.token(),
        "audit-m195",
        source_id="alert",
        owner_id="alert-owner",
        total=1,
        false_alerts=0,
        misses=0,
        version=1,
        sources=source(195),
    )
    case.classify_severity(
        case.token(),
        "audit-m196",
        reported=1,
        loss=1,
        scope=1,
        recovery_hours=1,
        sources=source(196),
    )
    case.grant_temporary_authority(
        case.token(),
        "audit-m200",
        model.AuthorityGrant("grant", "actor", "manager-10", 1, 2, frozenset({"rollback"})),
        sources=source(200),
    )
    case.freeze_timeline(
        case.token(),
        "audit-m201",
        (model.TimelineNode("node", 1, "actor", "action", "fixed"),),
        sources=source(201),
    )
    case.allocate_incident_credit(
        case.token(),
        "audit-m197",
        {"actor": 1, "backup": 99},
        {"actor": ("node",), "backup": ("node",)},
        sources=source(197),
    )
    return case


def run_incident() -> model.IncidentCase:
    case = model.IncidentCase(
        identity(192, subject="incident-team"),
        model.IncidentState.ON_CALL.value,
        capacity=model.CapacityLedger(120),
        treasury=model.MoneyLedger(100),
        reliability=model.ReliabilityBudget(5),
    )
    case.configure_rotation(
        case.token(),
        "m192",
        members=("responder-a", "responder-b", "responder-c"),
        on_call_id="responder-a",
        sources=source(192, "rotation-v1"),
    )
    case.record_alert(
        case.token(),
        "m195",
        source_id="alert-source",
        owner_id="alert-owner",
        total=10,
        false_alerts=3,
        misses=1,
        version=1,
        sources=source(195, "alert-window"),
    )
    case.classify_severity(
        case.token(),
        "m196",
        reported=2,
        loss=80,
        scope=60,
        recovery_hours=12,
        sources=source(196, "loss-snapshot"),
    )
    case.grant_temporary_authority(
        case.token(),
        "m200",
        model.AuthorityGrant(
            "grant-200",
            "commander",
            "duke",
            10,
            100,
            frozenset({"rollback", "allocate-resources"}),
        ),
        sources=source(200, "authority-order"),
    )
    case.execute_authority_command(minute=20, scope="rollback", command_id="command-1")
    nodes = (
        model.TimelineNode("n1", 1, "responder-a", "detected", "first signal"),
        model.TimelineNode("n2", 5, "commander", "escalated", "scope confirmed"),
        model.TimelineNode("n3", 20, "commander", "command", "rollback"),
        model.TimelineNode("n4", 30, "responder-b", "action", "rollback applied"),
        model.TimelineNode("n5", 45, "responder-c", "recovered", "service restored"),
    )
    case.freeze_timeline(
        case.token(),
        "m201",
        nodes,
        sources=source(201, "native-clock"),
    )
    case.allocate_incident_credit(
        case.token(),
        "m197",
        {"commander": 35, "responder-b": 40, "responder-c": 25},
        {
            "commander": ("n2", "n3"),
            "responder-b": ("n4",),
            "responder-c": ("n5",),
        },
        sources=source(197, "timeline-credit"),
    )
    case.net_firefighting_credit(
        case.token(),
        "m198",
        actor_id="responder-b",
        gross_credit=40,
        root_penalty=10,
        negligent=True,
        sources=source(198, "root-cause"),
    )
    case.award_prevention_credit(
        case.token(),
        "m199",
        hazard_id="hazard-199",
        protection_id="guard-199",
        observation_days=90,
        incident_occurred=False,
        proposed_credit=20,
        cap=15,
        sources=source(199, "observation-window"),
    )
    case.compensate_on_call(
        case.token(),
        "m193",
        shift_id="shift-193",
        worker_id="responder-a",
        verified_hours=12,
        gold_hours=5,
        time_off_hours=7,
        gold_per_hour=2,
        annual_hour_cap=20,
        sources=source(193, "verified-hours"),
    )
    case.grant_target_relief(
        case.token(),
        "m194",
        worker_id="responder-a",
        incident_hours=12,
        relief_hours=12,
        sources=source(194, "workload-snapshot"),
    )
    case.open_postmortem_actions(
        case.token(),
        "m202",
        (
            model.PostmortemAction(
                "fix-alert",
                "alert-owner",
                ("responder-b",),
                1000,
                "independent-acceptor",
                1,
            ),
        ),
        sources=source(202, "postmortem"),
    )
    case.close_postmortem_action("fix-alert", "acceptance-evidence")
    case.assign_repeat_liability(
        case.token(),
        "m203",
        repeat_id="repeat-203",
        previous_similarity_key="same-root",
        current_similarity_key="same-root",
        prior_action_status="resource-refused",
        resource_denier_id="budget-manager",
        line_worker_id="responder-a",
        sources=source(203, "prior-action"),
    )
    case.consume_reliability_budget(
        case.token(),
        "m204",
        incident_id="incident-192",
        amount=7,
        projects_to_freeze=("feature-project",),
        override_signer_id=None,
        sources=source(204, "budget-ledger"),
    )
    return case


def run_maintenance() -> model.MaintenanceCase:
    case = model.MaintenanceCase(
        identity(205, subject="maintenance-team"),
        model.MaintenanceState.REGISTERED.value,
        capacity=model.CapacityLedger(100),
        treasury=model.MoneyLedger(80),
    )
    case.freeze_toil(
        case.token(),
        "m205",
        total_hours=100,
        toil_hours=45,
        remedy="automate",
        cap_percent=30,
        sources=source(205, "hours-snapshot"),
    )
    case.register_debt(
        case.token(),
        "m206",
        model.DebtItem("debt-206", "original-owner", "current-owner", 1, 20, risk=5),
        elapsed_cycles=2,
        interest_percent=10,
        hidden=True,
        sources=source(206, "expedient-change"),
    )
    case.freeze_debt_budget(
        case.token(),
        "m207",
        debt_hours=30,
        business_hours=50,
        remaining_hours=20,
        approved_diversion_hours=0,
        approver_id=None,
        sources=source(207, "cycle-capacity"),
    )
    case.choose_repair_route(
        case.token(),
        "m208",
        route=model.RepairRoute.INCREMENTAL,
        route_version=1,
        work_hours=10,
        exit_condition="risk below 2",
        sources=source(208, "route-decision"),
        debt_id="debt-206",
        repayment_hours=10,
    )
    case.pay_hazard_allowance(
        case.token(),
        "m209",
        worker_id="legacy-owner",
        amount=10,
        cap=15,
        end_day=500,
        sources=source(209, "hazard-contract"),
    )
    case.maintenance_owner_id = "legacy-founder"
    case.rotate_maintenance_owner(
        case.token(),
        "m210",
        incoming_owner_id="trained-owner",
        handover_complete=True,
        practical_verified=True,
        sources=source(210, "rotation-checklist"),
    )
    case.validate_runbook(
        case.token(),
        "m211",
        model.RunbookVersion(
            "runbook-211",
            1,
            "author",
            "newcomer-validator",
            "restore-task",
            True,
            20,
            1,
        ),
        sources=source(211, "practical-run"),
    )
    case.settle_automation_credit(
        case.token(),
        "m212",
        automation_id="automation-212",
        baseline_hours=20,
        observed_hours=5,
        observation_complete=True,
        sources=source(212, "before-after"),
    )
    case.record_review_credit(
        case.token(),
        "m213",
        review_id="review-213",
        reviewer_id="reviewer",
        review_hours=3,
        blocking_hours=1,
        validated_catches=2,
        sources=source(213, "validated-errors"),
    )
    case.record_quality_scope(
        case.token(),
        "m214",
        scope_id="quality-214",
        coverage_percent=95,
        risk_scenarios=("high-risk-a", "high-risk-b", "high-risk-c"),
        critical_miss=True,
        sources=source(214, "post-incident"),
    )
    case.retire_legacy_service(
        case.token(),
        "m215",
        service_id="legacy-service",
        users=("team-a", "team-b"),
        migrated_users=("team-a", "team-b"),
        upheld_appeals=(),
        hc_slot_id="hc-maintenance",
        sources=source(215, "migration-ledger"),
    )
    case.complete_handover(
        case.token(),
        "m216",
        handover_id="handover-216",
        items=(
            model.HandoverItem("assets", "asset-list", True),
            model.HandoverItem("risks", "risk-list", True),
            model.HandoverItem("contacts", "contact-list", True),
            model.HandoverItem("open-items", "open-list", False, "accepted residual"),
        ),
        delay_days=20,
        maximum_delay_days=30,
        sources=source(216, "successor-acceptance"),
    )
    return case


def run_platform() -> model.PlatformCase:
    case = model.PlatformCase(
        identity(217, subject="platform-service"),
        model.PlatformState.PROPOSED.value,
        central_treasury=model.MoneyLedger(100),
        team_treasuries={"team-a": model.MoneyLedger(50), "team-b": model.MoneyLedger(50)},
        platform_capacity=model.CapacityLedger(100),
        user_capacity=model.CapacityLedger(100),
        reform_capacity=model.CapacityLedger(100),
    )
    case.decide_adoption(
        case.token(),
        "m217",
        (
            model.AdoptionDecision("team-a", model.AdoptionState.ADOPTED, pilot_id="pilot-a"),
            model.AdoptionDecision("team-b", model.AdoptionState.APPROVED_EXCEPTION, exception_reason="latency"),
        ),
        mandatory_interface_only=True,
        sources=source(217, "adoption-policy"),
    )
    case.freeze_dual_score(
        case.token(),
        "m218",
        customer_scores={"team-a": 80, "team-b": 40},
        customer_weights={"team-a": 60, "team-b": 40},
        foundation_score=75,
        customer_floor=60,
        foundation_floor=70,
        sources=source(218, "dual-scorecard"),
    )
    case.freeze_value_metrics(
        case.token(),
        "m219",
        (
            model.PlatformMetric("team-a", 90, 20, True),
            model.PlatformMetric("team-b", 20, 0, False),
        ),
        outcome_metric="confirmed-saving",
        counter_metric="migration-burden",
        sources=source(219, "usage-ledger"),
    )
    case.charge_platform_cost(
        case.token(),
        "m220",
        total_cost=50,
        central_share=30,
        team_charges={"team-a": 10, "team-b": 10},
        cycle_serial=7,
        sources=source(220, "cost-formula"),
    )
    case.allocate_migration_cost(
        case.token(),
        "m221",
        total_hours=30,
        shares={"platform": 40, "users": 40, "reform": 20},
        sources=source(221, "benefit-shares"),
    )
    case.start_dual_run(
        case.token(),
        "m222",
        (
            model.DualRunRecord("team-a", True, True, 500, 5),
            model.DualRunRecord("team-b", True, True, 550, 3),
        ),
        sources=source(222, "migration-plan"),
    )
    case.close_old_route("team-a", current_day=500)
    case.record_duplicate_scan(
        case.token(),
        "m223",
        model.DuplicateScan(
            "proposal-223",
            ("existing-platform",),
            "contribute",
        ),
        sources=source(223, "capability-index"),
    )
    case.merge_solutions(
        case.token(),
        "m224",
        solution_a="solution-a",
        solution_b="solution-b",
        sample_id="shared-sample",
        rubric_id="shared-rubric",
        scores={"solution-a": 80, "solution-b": 70},
        contributions={"solution-a": ("author-a",), "solution-b": ("author-b",)},
        reconstruction_hours=10,
        sources=source(224, "pilot-results"),
    )
    case.create_fork(
        case.token(),
        "m225",
        fork_id="fork-225",
        source_platform_id="platform-main",
        upstream_request_id="upstream-request",
        hard_difference="security-isolation",
        approved_by="architecture-panel",
        owner_id="fork-owner",
        maintenance_hours=5,
        sources=source(225, "difference-review"),
    )
    case.settle_inner_source(
        case.token(),
        "m226",
        model.InnerSourceSubmission(
            "submission-226",
            "contributor",
            "maintainer",
            "content-226",
            True,
            "tested and accepted",
        ),
        sources=source(226, "review-result"),
    )
    case.freeze_role_credit(
        case.token(),
        "m227",
        asset_id="platform-asset",
        shares={"founder": 30, "contributors": 40, "maintainers": 30},
        founder_id="founder",
        cycle_serial=8,
        sources=source(227, "role-ledger"),
    )
    case.allocate_blast_liability(
        case.token(),
        "m228",
        incident_id="platform-incident",
        affected_teams=("team-a", "team-b"),
        total_loss=101,
        liability_shares={"platform-root": 50, "user-violation": 20, "executive-push": 30},
        degraded_teams=("team-a",),
        sources=source(228, "root-cause-and-blast"),
    )
    return case


def run_all_domains() -> tuple[model.IncidentCase, model.MaintenanceCase, model.PlatformCase]:
    return run_incident(), run_maintenance(), run_platform()


DomainCase = model.IncidentCase | model.MaintenanceCase | model.PlatformCase
Assertion = Callable[[unittest.TestCase, DomainCase], None]


def assert_192(tc: unittest.TestCase, raw: DomainCase) -> None:
    case = raw
    tc.assertIsInstance(case, model.IncidentCase)
    tc.assertEqual(case.rotation, ("responder-a", "responder-b", "responder-c"))
    tc.assertEqual(case.on_call_id, "responder-a")


def assert_193(tc: unittest.TestCase, raw: DomainCase) -> None:
    case = raw
    tc.assertEqual(case.treasury.spent_gold, 10)
    tc.assertEqual(case.treasury.credits["responder-a"], 10)
    tc.assertEqual(case.time_off_hours["responder-a"], 7)
    tc.assertEqual(case.compensated_shifts, {"shift-193"})


def assert_194(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.target_relief["responder-a"], 12)  # type: ignore[union-attr]


def assert_195(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.alert_snapshot["total"], 10)  # type: ignore[union-attr]
    tc.assertLessEqual(raw.alert_snapshot["false"], raw.alert_snapshot["total"])  # type: ignore[union-attr,operator]


def assert_196(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual((raw.reported_severity, raw.corrected_severity), (2, 4))  # type: ignore[union-attr]
    tc.assertEqual(raw.severity_integrity, "underreported")  # type: ignore[union-attr]


def assert_197(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(sum(raw.incident_credit.values()), 100)  # type: ignore[union-attr]
    tc.assertEqual(set(raw.incident_credit), set(raw.role_nodes))  # type: ignore[union-attr]


def assert_198(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.net_firefighting_credits["responder-b"], 30)  # type: ignore[union-attr]
    tc.assertEqual(raw.firefighting_credit_components["responder-b"]["gross"], 40)  # type: ignore[union-attr]
    tc.assertEqual(raw.firefighting_credit_components["responder-b"]["penalty"], 10)  # type: ignore[union-attr]


def assert_199(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.prevention_credit["hazard-199"], 15)  # type: ignore[union-attr]


def assert_200(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertTrue(raw.authority.permits(20, "rollback"))  # type: ignore[union-attr]
    tc.assertEqual(raw.authority_commands, [(20, "rollback", "command-1")])  # type: ignore[union-attr]
    tc.assertFalse(raw.authority.permits(101, "rollback"))  # type: ignore[union-attr]


def assert_201(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual([node.minute for node in raw.timeline], [1, 5, 20, 30, 45])  # type: ignore[union-attr]
    tc.assertEqual(len(raw.timeline_sha256), 64)  # type: ignore[arg-type,union-attr]


def assert_202(tc: unittest.TestCase, raw: DomainCase) -> None:
    action = raw.postmortem_actions["fix-alert"]  # type: ignore[union-attr]
    tc.assertTrue(action.closed)
    tc.assertEqual(action.evidence_id, "acceptance-evidence")


def assert_203(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.repeat_liability["repeat-203"], "budget-manager")  # type: ignore[union-attr]


def assert_204(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.reliability.remaining, 0)  # type: ignore[union-attr]
    tc.assertEqual(raw.reliability.overrun, 2)  # type: ignore[union-attr]
    raw.reliability.assert_conserved()  # type: ignore[union-attr]
    tc.assertEqual(raw.reliability.frozen_projects, {"feature-project"})  # type: ignore[union-attr]
    tc.assertEqual(raw.state, model.IncidentState.RESOLVED.value)


def assert_205(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.toil_snapshot["share"], 45.0)  # type: ignore[union-attr]
    tc.assertEqual(raw.toil_snapshot["delivery"], 55)  # type: ignore[union-attr]
    tc.assertEqual(raw.toil_snapshot["remedy"], "automate")  # type: ignore[union-attr]


def assert_206(tc: unittest.TestCase, raw: DomainCase) -> None:
    debt = raw.debts["debt-206"]  # type: ignore[union-attr]
    tc.assertEqual(debt.outstanding, 14)
    tc.assertEqual(debt.repaid, 10)
    tc.assertEqual(debt.original_owner_id, "original-owner")
    tc.assertFalse(debt.visible)


def assert_207(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.debt_budget, {"debt": 30, "business": 50, "remaining": 20})  # type: ignore[union-attr]
    tc.assertEqual(raw.capacity.available_hours, 20)  # type: ignore[union-attr]


def assert_208(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.repair_route, model.RepairRoute.INCREMENTAL)  # type: ignore[union-attr]
    tc.assertEqual(raw.route_history, [(1, model.RepairRoute.INCREMENTAL)])  # type: ignore[union-attr]
    tc.assertEqual(raw.debt_work_used, 10)  # type: ignore[union-attr]


def assert_209(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.treasury.spent_gold, 10)  # type: ignore[union-attr]
    tc.assertEqual(raw.hazard_pay_end_day["legacy-owner"], 500)  # type: ignore[union-attr]


def assert_210(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.maintenance_owner_id, "trained-owner")  # type: ignore[union-attr]
    tc.assertEqual(raw.owner_history, ["legacy-founder"])  # type: ignore[union-attr]


def assert_211(tc: unittest.TestCase, raw: DomainCase) -> None:
    runbook = raw.runbooks[("runbook-211", 1)]  # type: ignore[union-attr]
    tc.assertNotEqual(runbook.author_id, runbook.validator_id)
    tc.assertTrue(runbook.completed)


def assert_212(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.automation_credit["automation-212"], 15)  # type: ignore[union-attr]


def assert_213(tc: unittest.TestCase, raw: DomainCase) -> None:
    record = raw.review_records["review-213"]  # type: ignore[union-attr]
    tc.assertEqual(record["reviewer_id"], "reviewer")
    tc.assertEqual(record["quality_credit"], 2)
    tc.assertEqual((record["review_hours"], record["blocking_hours"]), (3, 1))


def assert_214(tc: unittest.TestCase, raw: DomainCase) -> None:
    record = raw.quality_records["quality-214"]  # type: ignore[union-attr]
    tc.assertEqual(record["coverage"], 95)
    tc.assertEqual(record["score"], 37)
    tc.assertLess(record["score"], record["coverage"])


def assert_215(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.retired_services, {"legacy-service"})  # type: ignore[union-attr]
    tc.assertEqual(raw.released_hc, {"hc-maintenance"})  # type: ignore[union-attr]


def assert_216(tc: unittest.TestCase, raw: DomainCase) -> None:
    items = raw.handovers["handover-216"]  # type: ignore[union-attr]
    tc.assertEqual({item.category for item in items}, {"assets", "risks", "contacts", "open-items"})
    tc.assertEqual(raw.state, model.MaintenanceState.CLOSED.value)


def assert_217(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.adoption["team-a"].state, model.AdoptionState.ADOPTED)  # type: ignore[union-attr]
    tc.assertEqual(raw.adoption["team-b"].state, model.AdoptionState.APPROVED_EXCEPTION)  # type: ignore[union-attr]
    tc.assertIs(raw.mandatory_interface_only, True)  # type: ignore[union-attr]


def assert_218(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertAlmostEqual(raw.customer_score, 64.0)  # type: ignore[arg-type,union-attr]
    tc.assertEqual(raw.foundation_score, 75.0)  # type: ignore[union-attr]
    tc.assertEqual(sum(raw.customer_weights.values()), 100)  # type: ignore[union-attr]
    tc.assertTrue(raw.full_high_eligible)  # type: ignore[union-attr]


def assert_219(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(set(raw.metrics), {"team-a", "team-b"})  # type: ignore[union-attr]
    tc.assertEqual((raw.outcome_metric, raw.counter_metric), ("confirmed-saving", "migration-burden"))  # type: ignore[union-attr]


def assert_220(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.central_treasury.spent_gold, 30)  # type: ignore[union-attr]
    tc.assertEqual(sum(ledger.spent_gold for ledger in raw.team_treasuries.values()), 20)  # type: ignore[union-attr]
    tc.assertEqual(sum(raw.showback.values()), 50)  # type: ignore[union-attr]


def assert_221(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(sum(raw.migration_shares.values()), 100)  # type: ignore[union-attr]
    tc.assertEqual(sum(raw.migration_hours.values()), 30)  # type: ignore[union-attr]


def assert_222(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(set(raw.dual_runs), {"team-a", "team-b"})  # type: ignore[union-attr]
    tc.assertTrue(raw.dual_runs["team-a"].old_closed)  # type: ignore[union-attr]
    tc.assertEqual(raw.user_capacity.used_hours, 25)  # type: ignore[union-attr]


def assert_223(tc: unittest.TestCase, raw: DomainCase) -> None:
    scan = raw.duplicate_scans["proposal-223"]  # type: ignore[union-attr]
    tc.assertEqual(scan.matched_asset_ids, ("existing-platform",))
    tc.assertEqual(scan.decision, "contribute")


def assert_224(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual((raw.merger_winner, raw.merger_loser), ("solution-a", "solution-b"))  # type: ignore[union-attr]
    tc.assertEqual(raw.merger_contributions["solution-b"], ("author-b",))  # type: ignore[union-attr]


def assert_225(tc: unittest.TestCase, raw: DomainCase) -> None:
    fork = raw.forks["fork-225"]  # type: ignore[union-attr]
    tc.assertEqual((fork["difference"], fork["owner"]), ("security-isolation", "fork-owner"))


def assert_226(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(raw.contributor_credit["contributor"], 1)  # type: ignore[union-attr]
    tc.assertEqual(raw.maintainer_credit["maintainer"], 1)  # type: ignore[union-attr]
    tc.assertTrue(raw.submissions["submission-226"].settled)  # type: ignore[union-attr]


def assert_227(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(sum(raw.role_credit["platform-asset"].values()), 100)  # type: ignore[union-attr]
    tc.assertEqual(raw.founder_halo["founder"], 99)  # type: ignore[union-attr]


def assert_228(tc: unittest.TestCase, raw: DomainCase) -> None:
    tc.assertEqual(sum(raw.blast_liability["platform-incident"].values()), 100)  # type: ignore[union-attr]
    tc.assertEqual(sum(raw.allocated_losses["platform-incident"].values()), 101)  # type: ignore[union-attr]
    tc.assertEqual(raw.blast_affected_teams["platform-incident"], ("team-a", "team-b"))  # type: ignore[union-attr]
    tc.assertEqual(raw.degraded_teams["platform-incident"], ("team-a",))  # type: ignore[union-attr]
    tc.assertEqual(raw.state, model.PlatformState.SETTLED.value)


ASSERTIONS: dict[int, Assertion] = {
    192: assert_192,
    193: assert_193,
    194: assert_194,
    195: assert_195,
    196: assert_196,
    197: assert_197,
    198: assert_198,
    199: assert_199,
    200: assert_200,
    201: assert_201,
    202: assert_202,
    203: assert_203,
    204: assert_204,
    205: assert_205,
    206: assert_206,
    207: assert_207,
    208: assert_208,
    209: assert_209,
    210: assert_210,
    211: assert_211,
    212: assert_212,
    213: assert_213,
    214: assert_214,
    215: assert_215,
    216: assert_216,
    217: assert_217,
    218: assert_218,
    219: assert_219,
    220: assert_220,
    221: assert_221,
    222: assert_222,
    223: assert_223,
    224: assert_224,
    225: assert_225,
    226: assert_226,
    227: assert_227,
    228: assert_228,
}


def domain_for(mechanism_id: int) -> DomainCase:
    if mechanism_id <= 204:
        return run_incident()
    if mechanism_id <= 216:
        return run_maintenance()
    return run_platform()


class ContractTests(unittest.TestCase):
    def test_registry_and_assertions_cover_exact_192_through_228(self) -> None:
        self.assertEqual(set(model.BEHAVIORS), model.EXPECTED_IDS)
        self.assertEqual(set(ASSERTIONS), model.EXPECTED_IDS)
        self.assertEqual(len(ASSERTIONS), 37)

    def test_readiness_is_honestly_python_l0_only(self) -> None:
        self.assertEqual(model.READINESS, "python-l0-only")
        self.assertEqual(model.CK3_WIRING, "not-implemented")
        for behavior in model.BEHAVIORS.values():
            self.assertEqual(behavior.readiness, "python-l0-only")
            self.assertEqual(behavior.ck3_wiring, "not-implemented")

    def test_each_id_binds_an_exact_object_consumer_resource_and_deadline(self) -> None:
        self.assertEqual(model.EXPECTED_IDS, frozenset(model.OBJECT_TYPES))
        self.assertEqual(37, len(set(model.OBJECT_TYPES.values())))
        classes = {
            "X": model.IncidentCase,
            "Y": model.MaintenanceCase,
            "Z": model.PlatformCase,
        }
        for mechanism_id, behavior in model.BEHAVIORS.items():
            self.assertEqual(model.OBJECT_TYPES[mechanism_id], behavior.object_type)
            self.assertEqual(model.CONSUMER_METHODS[mechanism_id], behavior.consumer_method)
            self.assertEqual(model.RESOURCE_BOOKS[mechanism_id], behavior.resource_books)
            self.assertEqual(model.DEADLINE_CYCLES[mechanism_id], behavior.deadline_cycles)
            self.assertTrue(behavior.resource_books)
            self.assertIn(behavior.deadline_cycles, (0, 1))
            self.assertTrue(hasattr(classes[behavior.domain], behavior.consumer_method))

    def test_five_field_stale_guards_are_no_op(self) -> None:
        case = model.IncidentCase(
            identity(900, subject="incident"),
            model.IncidentState.ON_CALL.value,
        )
        token = case.token()
        stale_tokens = (
            dataclasses.replace(token, owner_id="other-owner"),
            dataclasses.replace(token, subject_id="other-subject"),
            dataclasses.replace(token, cycle_serial=8),
            dataclasses.replace(token, case_serial=901),
            dataclasses.replace(token, expected_state="other-state"),
        )
        for index, stale in enumerate(stale_tokens):
            outcome = case.configure_rotation(
                stale,
                f"stale-{index}",
                members=("a", "b"),
                on_call_id="a",
                sources=source(192, f"stale-{index}"),
            )
            self.assertFalse(outcome.applied)
            self.assertEqual(outcome.code, model.NoOpCode.STALE_TOKEN.value)
        self.assertEqual(case.rotation, ())
        self.assertEqual(case.provenance, [])

    def test_duplicate_action_serial_is_idempotent_no_op(self) -> None:
        case = model.IncidentCase(
            identity(901, subject="incident"),
            model.IncidentState.ON_CALL.value,
        )
        first = case.configure_rotation(
            case.token(),
            "same-action",
            members=("a", "b"),
            on_call_id="a",
            sources=source(192, "first"),
        )
        duplicate = case.configure_rotation(
            case.token(),
            "same-action",
            members=("a", "b"),
            on_call_id="a",
            sources=source(192, "second"),
        )
        self.assertTrue(first.applied)
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.code, model.NoOpCode.DUPLICATE_ACTION.value)
        self.assertEqual(len(case.provenance), 1)

    def test_provenance_is_mandatory_and_red_is_atomic(self) -> None:
        case = model.IncidentCase(
            identity(902, subject="incident"),
            model.IncidentState.ON_CALL.value,
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.configure_rotation(
                case.token(),
                "missing-provenance",
                members=("a", "b"),
                on_call_id="a",
                sources=(),
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_VALUE)
        self.assertEqual(case.__dict__, before)

    def test_incident_money_precheck_is_atomic(self) -> None:
        case = model.IncidentCase(
            identity(903, subject="incident"),
            model.IncidentState.ON_CALL.value,
            treasury=model.MoneyLedger(2),
        )
        case.configure_rotation(
            case.token(),
            "rotation-before-compensation",
            members=("worker", "backup"),
            on_call_id="worker",
            sources=source(192),
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.compensate_on_call(
                case.token(),
                "too-expensive",
                shift_id="shift",
                worker_id="worker",
                verified_hours=10,
                gold_hours=10,
                time_off_hours=0,
                gold_per_hour=1,
                annual_hour_cap=10,
                sources=source(193),
            )
        self.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
        self.assertEqual(case.__dict__, before)

    def test_maintenance_capacity_precheck_is_atomic(self) -> None:
        case = model.MaintenanceCase(
            identity(904, subject="maintenance"),
            model.MaintenanceState.REGISTERED.value,
        )
        case.freeze_toil(
            case.token(),
            "toil-before-budget",
            total_hours=100,
            toil_hours=20,
            remedy=None,
            cap_percent=40,
            sources=source(205),
        )
        case.register_debt(
            case.token(),
            "debt-before-budget",
            model.DebtItem("debt-before-budget", "owner", "owner", 1, 20),
            elapsed_cycles=0,
            interest_percent=0,
            hidden=False,
            sources=source(206),
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.freeze_debt_budget(
                case.token(),
                "bad-hours",
                debt_hours=60,
                business_hours=60,
                remaining_hours=0,
                approved_diversion_hours=0,
                approver_id=None,
                sources=source(207),
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVARIANT_BREACH)
        self.assertEqual(case.__dict__, before)

    def test_platform_cost_precheck_is_atomic(self) -> None:
        case = model.PlatformCase(
            identity(905, subject="platform"),
            model.PlatformState.PROPOSED.value,
            central_treasury=model.MoneyLedger(100),
            team_treasuries={"team": model.MoneyLedger(100)},
        )
        case.decide_adoption(
            case.token(),
            "adoption-before-cost",
            (model.AdoptionDecision("team", model.AdoptionState.ADOPTED, pilot_id="pilot"),),
            mandatory_interface_only=True,
            sources=source(217),
        )
        case.freeze_dual_score(
            case.token(),
            "score-before-cost",
            customer_scores={"team": 80},
            customer_weights={"team": 100},
            foundation_score=80,
            customer_floor=60,
            foundation_floor=60,
            sources=source(218),
        )
        case.freeze_value_metrics(
            case.token(),
            "metrics-before-cost",
            (model.PlatformMetric("team", 80, 10, True),),
            outcome_metric="saving",
            counter_metric="migration-cost",
            sources=source(219),
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.charge_platform_cost(
                case.token(),
                "bad-cost",
                total_cost=50,
                central_share=10,
                team_charges={"team": 10},
                cycle_serial=7,
                sources=source(220),
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVARIANT_BREACH)
        self.assertEqual(case.__dict__, before)

    def test_semantic_execution_order_and_dependencies_are_total(self) -> None:
        flattened = tuple(
            mechanism_id
            for domain in ("X", "Y", "Z")
            for mechanism_id in model.DOMAIN_EXECUTION_ORDER[domain]
        )
        self.assertEqual(set(flattened), model.EXPECTED_IDS)
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertLess(flattened.index(201), flattened.index(197))
        self.assertEqual(set(model.MECHANISM_ALLOWED_STATES), model.EXPECTED_IDS)
        self.assertEqual(set(model.MECHANISM_DEPENDENCIES), model.EXPECTED_IDS)
        order_index = {mechanism_id: index for index, mechanism_id in enumerate(flattened)}
        for mechanism_id, dependencies in model.MECHANISM_DEPENDENCIES.items():
            self.assertTrue(all(order_index[item] < order_index[mechanism_id] for item in dependencies))

    def test_correct_token_cannot_bypass_lifecycle_or_dependencies(self) -> None:
        incident = model.IncidentCase(
            identity(907, subject="incident-order"),
            model.IncidentState.ON_CALL.value,
        )
        before = copy.deepcopy(incident.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            incident.consume_reliability_budget(
                incident.token(),
                "close-before-open",
                incident_id="incident",
                amount=1,
                projects_to_freeze=(),
                override_signer_id="manager",
                sources=source(204),
            )
        self.assertEqual(caught.exception.code, model.RedCode.ILLEGAL_STATE)
        self.assertEqual(incident.__dict__, before)
        with self.assertRaises(model.ModelRed) as missing:
            incident.compensate_on_call(
                incident.token(),
                "compensate-without-rotation",
                shift_id="shift",
                worker_id="worker",
                verified_hours=1,
                gold_hours=0,
                time_off_hours=1,
                gold_per_hour=1,
                annual_hour_cap=1,
                sources=source(193),
            )
        self.assertEqual(missing.exception.field_name, "dependencies")

        platform = model.PlatformCase(
            identity(908, subject="platform-order"),
            model.PlatformState.PROPOSED.value,
        )
        with self.assertRaises(model.ModelRed) as merge:
            platform.merge_solutions(
                platform.token(),
                "merge-before-scan",
                solution_a="a",
                solution_b="b",
                sample_id="sample",
                rubric_id="rubric",
                scores={"a": 2, "b": 1},
                contributions={"a": (), "b": ()},
                reconstruction_hours=1,
                sources=source(224),
            )
        self.assertEqual(merge.exception.code, model.RedCode.ILLEGAL_STATE)

    def test_firefighting_net_credit_never_goes_negative(self) -> None:
        case = incident_before_credit_netting()
        outcome = case.net_firefighting_credit(
            case.token(),
            "audit-m198",
            actor_id="actor",
            gross_credit=1,
            root_penalty=5,
            negligent=True,
            sources=source(198),
        )
        self.assertTrue(outcome.applied)
        self.assertEqual(case.net_firefighting_credits["actor"], 0)
        self.assertEqual(case.firefighting_credit_components["actor"]["penalty"], 5)

    def test_reliability_overrun_is_explicit_and_conserved(self) -> None:
        budget = model.ReliabilityBudget(5)
        budget.commit_consume(budget.prepare_consume("incident-a", 7))
        self.assertEqual((budget.remaining, budget.overrun, budget.consumed), (0, 2, 7))
        budget.assert_conserved()
        budget.commit_consume(budget.prepare_consume("incident-b", 3))
        self.assertEqual((budget.remaining, budget.overrun, budget.consumed), (0, 5, 10))
        budget.assert_conserved()

    def test_debt_budget_cumulative_precheck_prevents_partial_commit(self) -> None:
        capacity = model.CapacityLedger(100)
        capacity.commit_allocate(("preexisting", 40))
        case = model.MaintenanceCase(
            identity(909, subject="maintenance-cumulative"),
            model.MaintenanceState.REGISTERED.value,
            capacity=capacity,
        )
        case.freeze_toil(
            case.token(),
            "cumulative-m205",
            total_hours=100,
            toil_hours=20,
            remedy=None,
            cap_percent=40,
            sources=source(205),
        )
        case.register_debt(
            case.token(),
            "cumulative-m206",
            model.DebtItem("cumulative-debt", "owner", "owner", 1, 50),
            elapsed_cycles=0,
            interest_percent=0,
            hidden=False,
            sources=source(206),
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.freeze_debt_budget(
                case.token(),
                "cumulative-m207",
                debt_hours=50,
                business_hours=20,
                remaining_hours=30,
                approved_diversion_hours=0,
                approver_id=None,
                sources=source(207),
            )
        self.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
        self.assertEqual(case.__dict__, before)

    def test_atomic_repair_route_repayment_is_all_or_nothing(self) -> None:
        case = model.MaintenanceCase(
            identity(910, subject="maintenance-repair"),
            model.MaintenanceState.REGISTERED.value,
        )
        case.freeze_toil(
            case.token(),
            "repair-m205",
            total_hours=100,
            toil_hours=20,
            remedy=None,
            cap_percent=40,
            sources=source(205),
        )
        case.register_debt(
            case.token(),
            "repair-m206",
            model.DebtItem("repair-debt", "owner", "owner", 1, 10),
            elapsed_cycles=0,
            interest_percent=0,
            hidden=False,
            sources=source(206),
        )
        case.freeze_debt_budget(
            case.token(),
            "repair-m207",
            debt_hours=10,
            business_hours=70,
            remaining_hours=20,
            approved_diversion_hours=0,
            approver_id=None,
            sources=source(207),
        )
        before = copy.deepcopy(case.__dict__)
        with self.assertRaises(model.ModelRed) as caught:
            case.choose_repair_route(
                case.token(),
                "repair-too-large",
                route=model.RepairRoute.INCREMENTAL,
                route_version=1,
                work_hours=20,
                exit_condition="done",
                sources=source(208),
                debt_id="repair-debt",
                repayment_hours=20,
            )
        self.assertEqual(caught.exception.code, model.RedCode.RESOURCE_EXHAUSTED)
        self.assertEqual(case.__dict__, before)
        applied = case.choose_repair_route(
            case.token(),
            "repair-valid",
            route=model.RepairRoute.INCREMENTAL,
            route_version=1,
            work_hours=10,
            exit_condition="done",
            sources=source(208),
            debt_id="repair-debt",
            repayment_hours=10,
        )
        self.assertTrue(applied.applied)
        self.assertEqual(case.debts["repair-debt"].outstanding, 0)
        self.assertEqual(case.debt_work_used, 10)
        self.assertEqual(case.capacity.available_hours, 20)

    def test_bool_is_not_accepted_as_integer(self) -> None:
        with self.assertRaises(model.ModelRed) as caught:
            model.CapacityLedger(True)  # type: ignore[arg-type]
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_TYPE)

    def test_payload_digest_is_deterministic_for_same_prepared_command(self) -> None:
        cases = []
        for _ in range(2):
            case = model.IncidentCase(
                identity(906, subject="incident"),
                model.IncidentState.ON_CALL.value,
            )
            case.configure_rotation(
                case.token(),
                "same-command",
                members=("a", "b"),
                on_call_id="a",
                sources=source(192, "same-source"),
            )
            cases.append(case)
        self.assertEqual(cases[0].provenance[0].payload_sha256, cases[1].provenance[0].payload_sha256)


class EndToEndTests(unittest.TestCase):
    def test_end_to_end_portfolio_really_touches_every_id_once(self) -> None:
        cases = run_all_domains()
        receipts = [receipt for case in cases for receipt in case.provenance]
        self.assertEqual({receipt.mechanism_id for receipt in receipts}, model.EXPECTED_IDS)
        self.assertEqual(len(receipts), 37)
        self.assertEqual(len({(receipt.mechanism_id, receipt.action_serial) for receipt in receipts}), 37)
        for receipt in receipts:
            self.assertTrue(receipt.sources)
            self.assertTrue(receipt.result_ids)
            self.assertEqual(len(receipt.payload_sha256), 64)

    def test_end_to_end_resource_ledgers_conserve(self) -> None:
        incident, maintenance, platform = run_all_domains()
        incident.capacity.assert_conserved()
        incident.treasury.assert_conserved()
        incident.reliability.assert_conserved()
        maintenance.capacity.assert_conserved()
        maintenance.treasury.assert_conserved()
        platform.central_treasury.assert_conserved()
        platform.platform_capacity.assert_conserved()
        platform.user_capacity.assert_conserved()
        platform.reform_capacity.assert_conserved()
        for ledger in platform.team_treasuries.values():
            ledger.assert_conserved()

    def test_terminal_states_are_real_domain_terminals(self) -> None:
        incident, maintenance, platform = run_all_domains()
        self.assertEqual(incident.state, model.IncidentState.RESOLVED.value)
        self.assertEqual(maintenance.state, model.MaintenanceState.CLOSED.value)
        self.assertEqual(platform.state, model.PlatformState.SETTLED.value)


class MechanismScenarioTests(unittest.TestCase):
    """One independent test method per ID; each inspects its executable outcome."""


def _make_test(mechanism_id: int, assertion: Assertion) -> Callable[[unittest.TestCase], None]:
    def test(self: unittest.TestCase) -> None:
        case = domain_for(mechanism_id)
        receipts = [receipt for receipt in case.provenance if receipt.mechanism_id == mechanism_id]
        self.assertEqual(len(receipts), 1)
        self.assertTrue(receipts[0].sources)
        assertion(self, case)

    test.__name__ = f"test_mechanism_{mechanism_id:03d}_{model.BEHAVIORS[mechanism_id].behavior_key}"
    test.__doc__ = model.BEHAVIORS[mechanism_id].title_cn
    return test


for _mechanism_id, _assertion in ASSERTIONS.items():
    setattr(
        MechanismScenarioTests,
        f"test_mechanism_{_mechanism_id:03d}",
        _make_test(_mechanism_id, _assertion),
    )


if __name__ == "__main__":
    unittest.main()
