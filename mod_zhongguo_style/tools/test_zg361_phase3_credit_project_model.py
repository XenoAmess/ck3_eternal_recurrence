#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python L0 tests for the phase-three credit/project executable model."""

from __future__ import annotations

import copy
from pathlib import Path
import unittest

import zg361_phase3_credit_project_model as model


def make_model(
    *,
    capacity: int = 300,
    slots: int = 3,
    attention: int = 3,
    promotion_slots: int = 1,
) -> model.Phase3CreditProjectModel:
    return model.Phase3CreditProjectModel(
        model_id="portfolio-1",
        owner_id="manager",
        cycle_serial=7,
        case_serial=11,
        project_slot_total=slots,
        capacity_hours_total=capacity,
        attention_slot_total=attention,
        promotion_slot_total=promotion_slots,
        active_manager_id="manager",
        historical_cases=(
            model.HistoricalCase(
                "historic-1", "old-historical-manager", "subject", "3.75", False
            ),
            model.HistoricalCase(
                "historic-2", "old-historical-manager", "subject", "3.25", True
            ),
        ),
    )


def apply(
    instance: model.Phase3CreditProjectModel,
    behavior: str,
    command_id: str,
    **kwargs,
):
    return getattr(instance, behavior)(instance.command(command_id), **kwargs)


def seed_project(
    instance: model.Phase3CreditProjectModel,
    *,
    project_id: str = "p1",
    capacity: int = 100,
    participants: tuple[str, ...] = ("worker", "manager", "dotted"),
) -> None:
    result = apply(
        instance,
        "register_project_131",
        f"seed-{project_id}",
        project_id=project_id,
        owner_id=participants[0],
        participants=participants,
        track=model.ProjectTrack.COMMITMENT,
        metric_owner_id=participants[0],
        capacity_hours=capacity,
    )
    assert result.applied


def sign_default_shares(
    instance: model.Phase3CreditProjectModel, *, project_id: str = "p1"
) -> None:
    apply(
        instance,
        "sign_contributions_027",
        f"sign-{project_id}",
        project_id=project_id,
        shares={"worker": 6_000, "manager": 2_000, "dotted": 2_000},
    )


class ContractTests(unittest.TestCase):
    def test_readiness_is_honestly_python_l0_only(self) -> None:
        self.assertEqual(model.READINESS, "python-l0-only")

    def test_exact_requested_mechanism_ranges_are_bound(self) -> None:
        expected = set(range(26, 32)) | set(range(54, 69)) | set(range(129, 135))
        self.assertEqual(set(model.MECHANISM_BINDINGS), expected)
        self.assertEqual(expected, set(model.EXPECTED_MECHANISM_IDS))

    def test_every_binding_names_a_real_callable_behavior(self) -> None:
        for mechanism_id, binding in model.MECHANISM_BINDINGS.items():
            with self.subTest(mechanism_id=mechanism_id):
                self.assertEqual(binding.mechanism_id, mechanism_id)
                self.assertIn(binding.domain, {"E", "I", "J", "R"})
                self.assertTrue(binding.title_cn)
                self.assertTrue(binding.behaviors)
                for behavior in binding.behaviors:
                    self.assertTrue(
                        callable(
                            getattr(model.Phase3CreditProjectModel, behavior, None)
                        )
                    )

    def test_both_owned_python_files_have_utf8_bom(self) -> None:
        root = Path(__file__).resolve().parent
        for filename in (
            "zg361_phase3_credit_project_model.py",
            "test_zg361_phase3_credit_project_model.py",
        ):
            with self.subTest(filename=filename):
                self.assertTrue((root / filename).read_bytes().startswith(b"\xef\xbb\xbf"))


class CommandSemanticsTests(unittest.TestCase):
    def test_stale_command_is_a_noop_even_when_payload_would_be_invalid(self) -> None:
        instance = make_model()
        stale = instance.command("stale-project")
        seed_project(instance)
        before = copy.deepcopy(instance)
        result = instance.register_project_131(
            stale,
            project_id="",
            owner_id="",
            participants=(),
            track="bad",  # type: ignore[arg-type]
            metric_owner_id="",
            capacity_hours=-1,
        )
        self.assertEqual(result.status, model.ActionStatus.STALE_NOOP)
        self.assertEqual(instance, before)

    def test_replayed_applied_command_is_an_idempotent_noop(self) -> None:
        instance = make_model()
        command = instance.command("create-once")
        kwargs = dict(
            project_id="p1",
            owner_id="worker",
            participants=("worker", "manager"),
            track=model.ProjectTrack.EXPLORATION,
            metric_owner_id="worker",
            capacity_hours=10,
        )
        first = instance.register_project_131(command, **kwargs)
        before = copy.deepcopy(instance)
        replay = instance.register_project_131(command, **kwargs)
        self.assertTrue(first.applied)
        self.assertEqual(replay.status, model.ActionStatus.IDEMPOTENT_NOOP)
        self.assertEqual(instance, before)

    def test_command_id_collision_across_mechanisms_is_typed_red(self) -> None:
        instance = make_model()
        seed_project(instance)
        collision = instance.command("seed-p1")
        with self.assertRaises(model.DomainRed) as caught:
            instance.record_effort_026(
                collision,
                project_id="p1",
                delivery_hours=1,
                report_hours=0,
                relationship_hours=0,
            )
        self.assertEqual(caught.exception.code, model.RedCode.COMMAND_COLLISION)

    def test_non_token_command_is_strict_typed_red(self) -> None:
        instance = make_model()
        with self.assertRaises(model.DomainRed) as caught:
            instance.finalize_handoff_064(object())  # type: ignore[arg-type]
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_TYPE)


class ProjectAndCreditTests(unittest.TestCase):
    def test_project_identity_version_and_deadline_are_stable_business_state(self) -> None:
        instance = make_model()
        seed_project(instance)
        project = instance.projects["p1"]
        identity = (
            project.project_id,
            project.manager_id,
            project.owner_id,
            project.origin_cycle_serial,
            project.origin_case_serial,
        )
        self.assertEqual(identity, ("p1", "manager", "worker", 7, 11))
        self.assertEqual(project.deadline_cycle, 9)
        self.assertEqual(project.version, 1)
        apply(
            instance,
            "record_effort_026",
            "effort-version",
            project_id="p1",
            delivery_hours=10,
            report_hours=1,
            relationship_hours=1,
        )
        self.assertEqual(project.version, 2)
        self.assertEqual(
            (
                project.project_id,
                project.manager_id,
                project.owner_id,
                project.origin_cycle_serial,
                project.origin_case_serial,
            ),
            identity,
        )

    def test_project_slots_and_capacity_conserve_and_failed_preflight_is_atomic(self) -> None:
        instance = make_model(capacity=30, slots=2)
        seed_project(instance, capacity=20)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "register_project_131",
                "too-large",
                project_id="p2",
                owner_id="worker2",
                participants=("worker2", "manager"),
                track=model.ProjectTrack.COMMITMENT,
                metric_owner_id="worker2",
                capacity_hours=11,
            )
        self.assertEqual(caught.exception.code, model.RedCode.CAPACITY_EXCEEDED)
        self.assertEqual(instance, before)
        self.assertEqual(instance.project_slots_used + instance.project_slots_free, 2)
        self.assertEqual(
            instance.capacity_hours_reserved_or_spent + instance.capacity_hours_free, 30
        )

    def test_resource_race_awards_exactly_one_slot(self) -> None:
        instance = make_model(capacity=50, slots=1)
        apply(
            instance,
            "award_resource_race_030",
            "race",
            project_id="winner-project",
            candidate_ids=("team-a", "team-b"),
            winner_id="team-b",
            participants=("team-b", "helper"),
            capacity_hours=25,
        )
        self.assertEqual(set(instance.projects), {"winner-project"})
        self.assertEqual(instance.projects["winner-project"].owner_id, "team-b")
        self.assertEqual(instance.project_slots_used, 1)
        self.assertEqual(instance.capacity_hours_free, 25)

    def test_real_output_and_visibility_are_distinct_ledgers(self) -> None:
        instance = make_model()
        seed_project(instance, capacity=30)
        apply(
            instance,
            "record_effort_026",
            "effort",
            project_id="p1",
            delivery_hours=10,
            report_hours=2,
            relationship_hours=1,
        )
        project = instance.projects["p1"]
        self.assertEqual(project.hard_output, 10)
        self.assertEqual(project.visibility_points, 7)
        self.assertEqual(project.booked_hours, 13)
        self.assertEqual(project.delivery_capacity_hours, 27)

    def test_signed_contribution_requires_exact_participants_and_ten_thousand(self) -> None:
        instance = make_model()
        seed_project(instance)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "sign_contributions_027",
                "bad-sign",
                project_id="p1",
                shares={"worker": 6_000, "manager": 3_000, "dotted": 999},
            )
        self.assertEqual(caught.exception.code, model.RedCode.SHARE_IMBALANCE)
        self.assertEqual(instance, before)
        sign_default_shares(instance)
        self.assertEqual(
            sum(instance.projects["p1"].signed_contributions.values()), 10_000
        )

    def test_credit_grab_and_audit_reversal_are_each_net_zero(self) -> None:
        instance = make_model()
        seed_project(instance)
        sign_default_shares(instance)
        signed = dict(instance.projects["p1"].signed_contributions)
        apply(
            instance,
            "file_credit_claim_028",
            "grab",
            project_id="p1",
            claim_id="claim-1",
            source_id="worker",
            claimant_id="manager",
            basis_points=500,
        )
        project = instance.projects["p1"]
        self.assertEqual(sum(project.claimed_contributions.values()), 10_000)
        self.assertEqual(sum(project.claims["claim-1"].transfer_delta.values()), 0)
        apply(
            instance,
            "audit_credit_claim_028",
            "reverse",
            project_id="p1",
            claim_id="claim-1",
            upheld=False,
        )
        claim = project.claims["claim-1"]
        self.assertEqual(sum(claim.audit_delta.values()), 0)
        self.assertEqual(project.claimed_contributions, signed)
        self.assertEqual(project.signed_contributions, signed)

    def test_credit_grab_rejects_bool_basis_points_atomically(self) -> None:
        instance = make_model()
        seed_project(instance)
        sign_default_shares(instance)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "file_credit_claim_028",
                "bad-bps",
                project_id="p1",
                claim_id="claim-bad",
                source_id="worker",
                claimant_id="manager",
                basis_points=True,
            )
        self.assertEqual(caught.exception.code, model.RedCode.INVALID_TYPE)
        self.assertEqual(instance, before)

    def test_metric_gaming_and_fraud_settle_delayed_cost_and_clawback_once(self) -> None:
        instance = make_model()
        seed_project(instance)
        apply(
            instance,
            "record_metric_029",
            "metric-record",
            project_id="p1",
            metric_id="tax-packaging",
            baseline=100,
            strategy=model.MetricStrategy.FRAUD,
            short_kpi_gain=20,
            delayed_cost=9,
        )
        command = instance.command("metric-audit")
        first = instance.audit_metric_029(
            command, project_id="p1", metric_id="tax-packaging"
        )
        replay = instance.audit_metric_029(
            command, project_id="p1", metric_id="tax-packaging"
        )
        metric = instance.projects["p1"].metrics["tax-packaging"]
        self.assertTrue(first.applied)
        self.assertEqual(replay.status, model.ActionStatus.IDEMPOTENT_NOOP)
        self.assertEqual(metric.clawback, 20)
        self.assertEqual(metric.realized_delayed_cost, 9)

    def test_sponsor_credit_is_bounded_temporary_and_does_not_create_output(self) -> None:
        instance = make_model()
        seed_project(instance)
        hard_before = instance.projects["p1"].hard_output
        apply(
            instance,
            "apply_sponsorship_031",
            "sponsor",
            actor_id="worker",
            granted_credit=30,
            spent_credit=10,
            expires_cycle=8,
            visibility_bonus=10,
        )
        self.assertEqual(instance.sponsor_lines["worker"].balance, 20)
        self.assertEqual(instance.projects["p1"].hard_output, hard_before)


class ReportPacketTests(unittest.TestCase):
    def test_report_packet_has_independent_identity_version_deadline_and_project_link(self) -> None:
        instance = make_model()
        seed_project(instance)
        sign_default_shares(instance)
        apply(
            instance,
            "build_report_054",
            "build-stable-report",
            packet_id="report-stable",
            project_id="p1",
            author_id="worker",
        )
        packet = instance.reports["report-stable"]
        self.assertEqual(
            (
                packet.packet_id,
                packet.project_id,
                packet.owner_id,
                packet.cycle_serial,
                packet.case_serial,
                packet.deadline_cycle,
                packet.object_version,
            ),
            ("report-stable", "p1", "manager", 7, 11, 8, 1),
        )
        apply(
            instance,
            "forward_report_056",
            "forward-stable-report",
            packet_id="report-stable",
            source_id="worker",
            manager_id="manager",
            basis_points=500,
        )
        self.assertEqual(packet.object_version, 2)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(
                instance,
                "sign_report_057",
                "wrong-signature",
                packet_id="report-stable",
                signer_id="manager",
                version=1,
            )
        self.assertEqual(instance, before)

    def _prepared_report(self, *, attention: int = 2):
        instance = make_model(attention=attention)
        seed_project(instance, capacity=30)
        sign_default_shares(instance)
        apply(
            instance,
            "set_report_policy_061",
            "policy",
            policy=model.ReportFormat.LONG_NARRATIVE,
        )
        apply(
            instance,
            "build_report_054",
            "build",
            packet_id="report-1",
            project_id="p1",
            author_id="worker",
        )
        return instance

    def test_report_hours_reduce_delivery_capacity_without_creating_hard_output(self) -> None:
        instance = make_model()
        seed_project(instance, capacity=20)
        project = instance.projects["p1"]
        before_capacity = project.delivery_capacity_hours
        before_output = project.hard_output
        apply(
            instance,
            "set_report_policy_061",
            "long-policy",
            policy=model.ReportFormat.LONG_NARRATIVE,
        )
        apply(
            instance,
            "build_report_054",
            "long-report",
            packet_id="r",
            project_id="p1",
            author_id="worker",
        )
        self.assertEqual(project.delivery_capacity_hours, before_capacity - 4)
        self.assertEqual(project.hard_output, before_output)
        self.assertEqual(instance.reports["r"].hours, 4)

    def test_forwarded_attribution_conserves_then_signature_freezes_version(self) -> None:
        instance = self._prepared_report()
        apply(
            instance,
            "forward_report_056",
            "forward",
            packet_id="report-1",
            source_id="worker",
            manager_id="manager",
            basis_points=400,
        )
        packet = instance.reports["report-1"]
        self.assertEqual(sum(packet.claimed_attribution.values()), 10_000)
        apply(
            instance,
            "sign_report_057",
            "sign-report",
            packet_id="report-1",
            signer_id="worker",
            version=3,
        )
        self.assertEqual(packet.signed_attribution, packet.claimed_attribution)
        self.assertEqual(packet.version_signature, "report-1:v3:worker")

    def test_routing_requires_signature_and_rejection_is_atomic(self) -> None:
        instance = self._prepared_report()
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "route_report_058",
                "route-unsigned",
                packet_id="report-1",
                direct_manager_id="manager",
                skip_level_manager_id="emperor",
            )
        self.assertEqual(caught.exception.code, model.RedCode.SIGNATURE_REQUIRED)
        self.assertEqual(instance, before)

    def test_route_is_not_visibility_until_attention_slot_is_spent(self) -> None:
        instance = self._prepared_report()
        apply(
            instance,
            "sign_report_057",
            "sign-report",
            packet_id="report-1",
            signer_id="worker",
            version=1,
        )
        apply(
            instance,
            "route_report_058",
            "route",
            packet_id="report-1",
            direct_manager_id="manager",
            skip_level_manager_id="emperor",
        )
        packet = instance.reports["report-1"]
        visibility = instance.projects["p1"].visibility_points
        self.assertEqual(packet.seen_by, set())
        apply(
            instance,
            "read_report_055",
            "read",
            packet_id="report-1",
            manager_id="manager",
        )
        self.assertEqual(packet.seen_by, {"manager"})
        self.assertEqual(instance.projects["p1"].visibility_points, visibility + 5)

    def test_attention_slots_are_conserved(self) -> None:
        instance = self._prepared_report(attention=1)
        apply(
            instance,
            "sign_report_057",
            "sign-report",
            packet_id="report-1",
            signer_id="worker",
            version=1,
        )
        apply(
            instance,
            "route_report_058",
            "route",
            packet_id="report-1",
            direct_manager_id="manager",
            skip_level_manager_id="emperor",
        )
        apply(
            instance,
            "read_report_055",
            "read-manager",
            packet_id="report-1",
            manager_id="manager",
        )
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "read_report_055",
                "read-emperor",
                packet_id="report-1",
                manager_id="emperor",
            )
        self.assertEqual(caught.exception.code, model.RedCode.ATTENTION_EXHAUSTED)
        self.assertEqual(instance, before)

    def test_early_risk_report_reduces_loss_and_signed_version_wins_theft_case(self) -> None:
        instance = self._prepared_report()
        apply(
            instance,
            "sign_report_057",
            "sign-report",
            packet_id="report-1",
            signer_id="worker",
            version=1,
        )
        apply(
            instance,
            "record_risk_059",
            "early-risk",
            packet_id="report-1",
            timing=model.RiskTiming.EARLY,
            severity=9,
        )
        apply(
            instance,
            "arbitrate_idea_060",
            "idea-audit",
            packet_id="report-1",
            original_author_id="worker",
            claimed_author_id="manager",
        )
        packet = instance.reports["report-1"]
        self.assertEqual(packet.risk_remaining_loss, 5)
        self.assertEqual(packet.integrity_delta, 1)
        self.assertEqual(packet.idea_owner_id, "worker")
        self.assertTrue(packet.theft_upheld)


class MatrixAndReorganizationTests(unittest.TestCase):
    def test_matrix_weights_require_exactly_two_managers_and_total_one_hundred(self) -> None:
        instance = make_model()
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "lock_matrix_weights_063",
                "bad-weights",
                subject_id="subject",
                weights={"manager": 80, "dotted": 30},
            )
        self.assertEqual(
            caught.exception.code, model.RedCode.MATRIX_WEIGHT_IMBALANCE
        )
        self.assertEqual(instance, before)
        apply(
            instance,
            "lock_matrix_weights_063",
            "good-weights",
            subject_id="subject",
            weights={"manager": 70, "dotted": 30},
        )
        self.assertEqual(sum(instance.matrix.weights.values()), 100)

    def test_joint_matrix_arbitration_records_conflict_without_reweighting(self) -> None:
        instance = make_model()
        apply(
            instance,
            "lock_matrix_weights_063",
            "weights",
            subject_id="subject",
            weights={"manager": 70, "dotted": 30},
        )
        apply(
            instance,
            "resolve_matrix_conflict_062",
            "conflict",
            choice=model.MatrixConflictChoice.JOINT_ARBITRATION,
            solid_priority="tax rollout",
            dotted_priority="border relief",
        )
        self.assertEqual(instance.matrix.conflict_records[-1]["chosen"], "joint")
        self.assertEqual(sum(instance.matrix.weights.values()), 100)

    def test_handoff_requires_both_signatures_and_never_reowns_history(self) -> None:
        instance = make_model()
        apply(
            instance,
            "lock_matrix_weights_063",
            "weights",
            subject_id="subject",
            weights={"manager": 70, "dotted": 30},
        )
        apply(
            instance,
            "open_handoff_064",
            "handoff-open",
            old_manager_id="manager",
            new_manager_id="new-manager",
        )
        apply(
            instance,
            "sign_handoff_064",
            "old-sign",
            signer_id="manager",
        )
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(instance, "finalize_handoff_064", "premature-finalize")
        self.assertEqual(caught.exception.code, model.RedCode.DUAL_SIGNATURE_REQUIRED)
        self.assertEqual(instance, before)
        apply(
            instance,
            "sign_handoff_064",
            "new-sign",
            signer_id="new-manager",
        )
        owners_before = tuple(case.owner_id for case in instance.historical_cases)
        apply(instance, "finalize_handoff_064", "finalize")
        self.assertEqual(instance.active_manager_id, "new-manager")
        self.assertEqual(sum(instance.matrix.weights.values()), 100)
        self.assertEqual(
            tuple(case.owner_id for case in instance.historical_cases), owners_before
        )

    def test_parachute_staffing_exposes_memory_and_favoritism_tradeoff(self) -> None:
        instance = make_model()
        apply(
            instance,
            "apply_parachute_065",
            "parachute",
            manager_id="manager",
            team_size=10,
            imported_staff=3,
        )
        record = instance.parachute_records[-1]
        self.assertEqual(record["retained_memory"], 7)
        self.assertTrue(record["favoritism_audit"])

    def test_strategic_cancellation_preserves_verified_personal_credit_and_releases_rest(self) -> None:
        instance = make_model(capacity=100, slots=1)
        seed_project(instance, capacity=80)
        apply(
            instance,
            "record_effort_026",
            "work",
            project_id="p1",
            delivery_hours=20,
            report_hours=5,
            relationship_hours=0,
        )
        apply(
            instance,
            "cancel_project_066",
            "cancel",
            project_id="p1",
            strategic_reason="imperial reprioritization",
            verified_milestones=True,
        )
        project = instance.projects["p1"]
        self.assertEqual(project.state, model.ProjectState.CANCELLED)
        self.assertEqual(project.individual_outcome, "verified_contribution_preserved")
        self.assertEqual(instance.project_slots_free, 1)
        self.assertEqual(instance.capacity_hours_free, 75)

    def test_duplicate_role_resolution_has_one_final_holder_or_explicit_transition(self) -> None:
        instance = make_model()
        apply(
            instance,
            "resolve_duplicate_role_067",
            "role",
            role_id="chief-architect",
            incumbents=("incumbent-a", "incumbent-b"),
            method=model.DuplicateRoleMethod.OPEN_COMPETITION,
            retained_id="incumbent-b",
        )
        self.assertEqual(
            instance.duplicate_role_records["chief-architect"]["final_holders"],
            ("incumbent-b",),
        )

    def test_portable_history_is_a_prior_not_current_quota_and_carries_open_pip_explicitly(self) -> None:
        instance = make_model()
        owners_before = tuple(case.owner_id for case in instance.historical_cases)
        apply(
            instance,
            "carry_history_068",
            "carry",
            subject_id="subject",
            new_manager_id="new-manager",
            protection_cycles=1,
            carry_open_pip=True,
        )
        history = instance.portable_histories["subject"]
        self.assertEqual(history.ratings, ("3.75", "3.25"))
        self.assertTrue(history.pip_carried)
        self.assertFalse(history.consumes_current_quota)
        self.assertEqual(
            tuple(case.owner_id for case in instance.historical_cases), owners_before
        )


class ProjectGovernanceTests(unittest.TestCase):
    def test_promotion_queue_is_fifo_and_slot_conserving(self) -> None:
        instance = make_model(promotion_slots=1)
        apply(
            instance,
            "enqueue_promotion_129",
            "queue-a",
            subject_id="candidate-a",
            eligible_until_cycle=8,
        )
        apply(
            instance,
            "enqueue_promotion_129",
            "queue-b",
            subject_id="candidate-b",
            eligible_until_cycle=8,
        )
        apply(instance, "allocate_promotion_129", "award-a")
        self.assertEqual(instance.promotion_awards, {"candidate-a"})
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(instance, "allocate_promotion_129", "award-b")
        self.assertEqual(instance, before)

    def test_hidden_pip_dumping_returns_accountability_to_source_manager(self) -> None:
        instance = make_model()
        apply(
            instance,
            "transfer_talent_130",
            "dump",
            subject_id="official",
            source_manager_id="manager",
            destination_manager_id="new-manager",
            pip_disclosed=False,
            wrong_role_evidence=False,
            trial_success=False,
        )
        transfer = instance.talent_transfers["official"]
        self.assertEqual(transfer.outcome, "trial_failed")
        self.assertTrue(transfer.source_accountability)

    def test_project_track_is_frozen_at_registration(self) -> None:
        instance = make_model()
        apply(
            instance,
            "register_project_131",
            "exploration",
            project_id="experiment",
            owner_id="worker",
            participants=("worker", "manager"),
            track=model.ProjectTrack.EXPLORATION,
            metric_owner_id="worker",
            capacity_hours=20,
        )
        project = instance.projects["experiment"]
        self.assertTrue(project.track_locked)
        self.assertEqual(project.track, model.ProjectTrack.EXPLORATION)

    def test_timely_stop_releases_unspent_capacity_and_is_not_automatic_failure(self) -> None:
        instance = make_model(capacity=100, slots=1)
        seed_project(instance, capacity=80)
        apply(
            instance,
            "record_effort_026",
            "work",
            project_id="p1",
            delivery_hours=15,
            report_hours=5,
            relationship_hours=0,
        )
        apply(
            instance,
            "stop_project_132",
            "stop",
            project_id="p1",
            evidence_strength=80,
            avoidable_delay=False,
        )
        project = instance.projects["p1"]
        self.assertEqual(project.stop_judgement, "timely_stop_credit")
        self.assertEqual(
            project.individual_outcome, "judgement_separate_from_business_result"
        )
        self.assertEqual(instance.capacity_hours_free, 80)
        self.assertEqual(instance.project_slots_free, 1)

    def test_postmortem_separates_learning_from_named_liability(self) -> None:
        instance = make_model()
        seed_project(instance)
        apply(
            instance,
            "stop_project_132",
            "stop",
            project_id="p1",
            evidence_strength=70,
            avoidable_delay=False,
        )
        apply(
            instance,
            "record_postmortem_133",
            "postmortem",
            project_id="p1",
            system_causes=("dependency contract was ambiguous",),
            violations_by_actor={"manager": ("hid a frozen risk",)},
            learning_actions=("publish dependency owner",),
        )
        record = instance.postmortems["p1"]
        self.assertFalse(record["blanket_penalty"])
        self.assertEqual(set(record["individual_liability"]), {"manager"})
        self.assertEqual(len(record["learning_actions"]), 1)

    def test_shared_metric_has_one_owner_and_duplicate_assignment_is_atomic(self) -> None:
        instance = make_model()
        apply(
            instance,
            "assign_shared_metric_134",
            "metric-owner",
            metric_id="retention",
            owner_id="manager",
            contributors=("dotted", "worker"),
            dependencies=("hiring", "onboarding"),
        )
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "assign_shared_metric_134",
                "duplicate-owner",
                metric_id="retention",
                owner_id="dotted",
                contributors=("manager",),
                dependencies=(),
            )
        self.assertEqual(caught.exception.code, model.RedCode.UNIQUE_OWNER_REQUIRED)
        self.assertEqual(instance, before)


class ExactBehaviorCoverageTests(unittest.TestCase):
    def test_one_deterministic_scenario_applies_every_requested_mechanism_id(self) -> None:
        instance = make_model(capacity=300, slots=3, attention=3)
        apply(
            instance,
            "register_project_131",
            "131-project",
            project_id="p1",
            owner_id="worker",
            participants=("worker", "manager", "dotted"),
            track=model.ProjectTrack.COMMITMENT,
            metric_owner_id="worker",
            capacity_hours=120,
        )
        apply(
            instance,
            "record_effort_026",
            "026-effort",
            project_id="p1",
            delivery_hours=10,
            report_hours=2,
            relationship_hours=1,
        )
        apply(
            instance,
            "sign_contributions_027",
            "027-sign",
            project_id="p1",
            shares={"worker": 6_000, "manager": 2_000, "dotted": 2_000},
        )
        apply(
            instance,
            "file_credit_claim_028",
            "028-grab",
            project_id="p1",
            claim_id="claim",
            source_id="worker",
            claimant_id="manager",
            basis_points=500,
        )
        apply(
            instance,
            "audit_credit_claim_028",
            "028-audit",
            project_id="p1",
            claim_id="claim",
            upheld=False,
        )
        apply(
            instance,
            "record_metric_029",
            "029-record",
            project_id="p1",
            metric_id="kpi",
            baseline=100,
            strategy=model.MetricStrategy.GAMING,
            short_kpi_gain=10,
            delayed_cost=5,
        )
        apply(
            instance,
            "audit_metric_029",
            "029-audit",
            project_id="p1",
            metric_id="kpi",
        )
        apply(
            instance,
            "award_resource_race_030",
            "030-race",
            project_id="p2",
            candidate_ids=("manager", "rival"),
            winner_id="manager",
            participants=("manager", "rival"),
            capacity_hours=80,
        )
        apply(
            instance,
            "apply_sponsorship_031",
            "031-sponsor",
            actor_id="worker",
            granted_credit=20,
            spent_credit=5,
            expires_cycle=8,
            visibility_bonus=5,
        )
        apply(
            instance,
            "set_report_policy_061",
            "061-policy",
            policy=model.ReportFormat.LONG_NARRATIVE,
        )
        apply(
            instance,
            "build_report_054",
            "054-build",
            packet_id="report",
            project_id="p1",
            author_id="worker",
        )
        apply(
            instance,
            "forward_report_056",
            "056-forward",
            packet_id="report",
            source_id="worker",
            manager_id="manager",
            basis_points=300,
        )
        apply(
            instance,
            "sign_report_057",
            "057-sign",
            packet_id="report",
            signer_id="worker",
            version=1,
        )
        apply(
            instance,
            "lock_matrix_weights_063",
            "063-weights",
            subject_id="subject",
            weights={"manager": 70, "dotted": 30},
        )
        apply(
            instance,
            "route_report_058",
            "058-route",
            packet_id="report",
            direct_manager_id="manager",
            skip_level_manager_id="emperor",
        )
        apply(
            instance,
            "read_report_055",
            "055-read",
            packet_id="report",
            manager_id="manager",
        )
        apply(
            instance,
            "record_risk_059",
            "059-risk",
            packet_id="report",
            timing=model.RiskTiming.EARLY,
            severity=8,
        )
        apply(
            instance,
            "arbitrate_idea_060",
            "060-idea",
            packet_id="report",
            original_author_id="worker",
            claimed_author_id="manager",
        )
        apply(
            instance,
            "resolve_matrix_conflict_062",
            "062-conflict",
            choice=model.MatrixConflictChoice.JOINT_ARBITRATION,
            solid_priority="deadline",
            dotted_priority="quality",
        )
        apply(
            instance,
            "open_handoff_064",
            "064-open",
            old_manager_id="manager",
            new_manager_id="new-manager",
        )
        apply(
            instance,
            "sign_handoff_064",
            "064-old-sign",
            signer_id="manager",
        )
        apply(
            instance,
            "sign_handoff_064",
            "064-new-sign",
            signer_id="new-manager",
        )
        apply(instance, "finalize_handoff_064", "064-finalize")
        apply(
            instance,
            "apply_parachute_065",
            "065-parachute",
            manager_id="new-manager",
            team_size=10,
            imported_staff=3,
        )
        apply(
            instance,
            "cancel_project_066",
            "066-cancel",
            project_id="p2",
            strategic_reason="portfolio reset",
            verified_milestones=True,
        )
        apply(
            instance,
            "resolve_duplicate_role_067",
            "067-role",
            role_id="lead",
            incumbents=("lead-a", "lead-b"),
            method=model.DuplicateRoleMethod.RETAIN_ONE,
            retained_id="lead-a",
        )
        apply(
            instance,
            "carry_history_068",
            "068-history",
            subject_id="subject",
            new_manager_id="new-manager",
            protection_cycles=1,
            carry_open_pip=True,
        )
        apply(
            instance,
            "enqueue_promotion_129",
            "129-queue",
            subject_id="candidate",
            eligible_until_cycle=8,
        )
        apply(instance, "allocate_promotion_129", "129-award")
        apply(
            instance,
            "transfer_talent_130",
            "130-transfer",
            subject_id="transfer-subject",
            source_manager_id="manager",
            destination_manager_id="new-manager",
            pip_disclosed=True,
            wrong_role_evidence=True,
            trial_success=True,
        )
        apply(
            instance,
            "stop_project_132",
            "132-stop",
            project_id="p1",
            evidence_strength=80,
            avoidable_delay=False,
        )
        apply(
            instance,
            "record_postmortem_133",
            "133-postmortem",
            project_id="p1",
            system_causes=("dependency ambiguity",),
            violations_by_actor={"manager": ("late escalation",)},
            learning_actions=("freeze dependency owner",),
        )
        apply(
            instance,
            "assign_shared_metric_134",
            "134-owner",
            metric_id="shared-value",
            owner_id="new-manager",
            contributors=("dotted", "worker"),
            dependencies=("p1",),
        )
        instance.assert_invariants()
        self.assertEqual(instance.applied_mechanism_ids, set(model.EXPECTED_MECHANISM_IDS))


if __name__ == "__main__":
    unittest.main()
