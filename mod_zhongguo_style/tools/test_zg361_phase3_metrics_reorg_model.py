#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the Python-L0 metrics/reorg/demand domain model."""

from __future__ import annotations

import copy
from pathlib import Path
import unittest

import zg361_phase3_metrics_reorg_model as model


def make_model(
    *,
    capacity: int = 200,
    next_capacity: int = 100,
    sample_slots: int = 2,
    emergency_slots: int = 1,
    wip_limit: int = 2,
    management_capacity: int = 10,
    total_hc: int = 20,
) -> model.MetricsReorgModel:
    return model.MetricsReorgModel(
        model_id="metrics-reorg-1",
        owner_id="manager",
        cycle_serial=7,
        case_serial=19,
        capacity_hours_total=capacity,
        next_cycle_capacity_total=next_capacity,
        sample_slot_total=sample_slots,
        emergency_slot_total=emergency_slots,
        wip_limit=wip_limit,
        management_capacity_total=management_capacity,
        total_hc=total_hc,
    )


def apply(instance: model.MetricsReorgModel, behavior: str, command_id: str, **kwargs):
    return getattr(instance, behavior)(instance.command(command_id), **kwargs)


def define_metric(
    instance: model.MetricsReorgModel,
    *,
    metric_id: str = "tax-rate",
    provenance_id: str = "prov-metric-tax",
) -> None:
    apply(
        instance,
        "define_metric_229",
        f"define-{metric_id}",
        metric_id=metric_id,
        owner_id="metric-owner",
        definition="collected tax divided by covered households",
        source="treasury-ledger",
        frequency="annual",
        scope="celestial prefectures",
        denominator=100,
        provenance_id=provenance_id,
    )


def submit_demand(
    instance: model.MetricsReorgModel,
    *,
    demand_id: str,
    proposer_id: str = "proposer",
    provenance_id: str | None = None,
) -> None:
    apply(
        instance,
        "submit_demand_334",
        f"submit-{demand_id}",
        demand_id=demand_id,
        source=model.DemandSource.TERRITORY,
        source_owner_id="prefecture",
        proposer_id=proposer_id,
        provenance_id=provenance_id or f"prov-{demand_id}",
    )


def admit_complete(
    instance: model.MetricsReorgModel, *, demand_id: str, hours: int = 20
) -> None:
    apply(
        instance,
        "admit_demand_336",
        f"admit-{demand_id}",
        demand_id=demand_id,
        benefit="reduce filing delay",
        acceptance="beneficiary accepts in live use",
        boundary="one prefecture",
        dependencies=("records-office",),
        estimated_hours=hours,
        route=model.AdmissionRoute.COMMITMENT,
        forcing_owner_id=None,
    )


class ContractTests(unittest.TestCase):
    def test_readiness_is_honest_python_l0(self) -> None:
        self.assertEqual(model.READINESS, "python-l0-only")

    def test_exact_requested_ids_are_bound(self) -> None:
        expected = set(range(229, 242)) | set(range(301, 312)) | set(range(334, 345))
        self.assertEqual(set(model.MECHANISM_BINDINGS), expected)
        self.assertEqual(set(model.EXPECTED_MECHANISM_IDS), expected)

    def test_every_id_names_a_real_callable_behavior(self) -> None:
        for mid, binding in model.MECHANISM_BINDINGS.items():
            with self.subTest(mid=mid):
                self.assertEqual(binding.mechanism_id, mid)
                self.assertIn(binding.domain, {"AA", "AG", "AJ"})
                self.assertTrue(binding.title_cn)
                self.assertTrue(binding.behaviors)
                for behavior in binding.behaviors:
                    self.assertTrue(
                        callable(getattr(model.MetricsReorgModel, behavior, None))
                    )

    def test_both_owned_files_have_utf8_bom(self) -> None:
        root = Path(__file__).resolve().parent
        for name in (
            "zg361_phase3_metrics_reorg_model.py",
            "test_zg361_phase3_metrics_reorg_model.py",
        ):
            with self.subTest(name=name):
                self.assertTrue((root / name).read_bytes().startswith(b"\xef\xbb\xbf"))


class CommandAndProvenanceTests(unittest.TestCase):
    def test_stale_command_is_noop_before_payload_validation(self) -> None:
        instance = make_model()
        stale = instance.command("stale")
        define_metric(instance)
        before = copy.deepcopy(instance)
        result = instance.define_metric_229(
            stale,
            metric_id="",
            owner_id="",
            definition="",
            source="",
            frequency="",
            scope="",
            denominator=-1,
            provenance_id="",
        )
        self.assertEqual(result.status, model.ActionStatus.STALE_NOOP)
        self.assertEqual(instance, before)

    def test_replay_is_idempotent_and_does_not_extend_provenance_chain(self) -> None:
        instance = make_model()
        command = instance.command("define")
        kwargs = dict(
            metric_id="m",
            owner_id="owner",
            definition="definition",
            source="ledger",
            frequency="annual",
            scope="realm",
            denominator=10,
            provenance_id="prov-m",
        )
        first = instance.define_metric_229(command, **kwargs)
        before = copy.deepcopy(instance)
        replay = instance.define_metric_229(command, **kwargs)
        self.assertTrue(first.applied)
        self.assertEqual(replay.status, model.ActionStatus.IDEMPOTENT_NOOP)
        self.assertEqual(instance, before)
        self.assertEqual(len(instance.receipts), 1)

    def test_command_collision_is_typed_red(self) -> None:
        instance = make_model()
        define_metric(instance)
        collision = instance.command("define-tax-rate")
        with self.assertRaises(model.DomainRed) as caught:
            instance.set_metric_access_233(
                collision,
                metric_id="tax-rate",
                access_level=model.AccessLevel.ALL,
                subject_has_access=True,
                query_channel=True,
            )
        self.assertEqual(caught.exception.code, model.RedCode.COMMAND_COLLISION)

    def test_provenance_id_cannot_bind_two_entities_and_rejection_is_atomic(self) -> None:
        instance = make_model()
        define_metric(instance)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            submit_demand(instance, demand_id="d1", provenance_id="prov-metric-tax")
        self.assertEqual(caught.exception.code, model.RedCode.PROVENANCE_CONFLICT)
        self.assertEqual(instance, before)

    def test_receipts_form_a_contiguous_parent_revision_chain(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "set_metric_access_233",
            "access",
            metric_id="tax-rate",
            access_level=model.AccessLevel.ROLE_LAYERED,
            subject_has_access=False,
            query_channel=True,
        )
        ordered = sorted(instance.receipts.values(), key=lambda row: row.committed_revision)
        self.assertEqual(
            [(row.parent_revision, row.committed_revision) for row in ordered],
            [(0, 1), (1, 2)],
        )


class MetricAndExperimentTests(unittest.TestCase):
    def test_metric_dictionary_has_one_owner_and_complete_frozen_definition(self) -> None:
        instance = make_model()
        define_metric(instance)
        metric = instance.metrics["tax-rate"]
        self.assertEqual(metric.owner_id, "metric-owner")
        self.assertEqual(metric.version, 1)
        self.assertEqual(metric.provenance_id, "prov-metric-tax")
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "define_metric_229",
                "redefine",
                metric_id="tax-rate",
                owner_id="other",
                definition="other",
                source="other",
                frequency="monthly",
                scope="other",
                denominator=10,
                provenance_id="prov-other",
            )
        self.assertEqual(caught.exception.code, model.RedCode.OWNER_CONFLICT)
        self.assertEqual(instance, before)

    def test_source_reconciliation_preserves_all_inputs_and_does_not_pick_max(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "reconcile_sources_230",
            "reconcile",
            reconciliation_id="r1",
            metric_id="tax-rate",
            source_values={"treasury": 90, "prefecture": 120, "project": 100},
            route=model.ReconcileRoute.AUTHORITY,
            authority_source="treasury",
            provenance_id="prov-r1",
        )
        record = instance.reconciliations["r1"]
        self.assertEqual(record["resolved_value"], 90)
        self.assertEqual(len(record["source_values"]), 3)

    def test_denominator_change_preserves_old_version_and_does_not_rewrite_awards(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "change_denominator_231",
            "denominator",
            metric_id="tax-rate",
            new_denominator=150,
            reason="coverage expanded",
            effective_cycle=8,
        )
        metric = instance.metrics["tax-rate"]
        self.assertEqual(metric.denominator, 150)
        self.assertEqual(metric.version, 2)
        self.assertEqual(metric.old_versions[0]["denominator"], 100)
        self.assertFalse(metric.old_versions[0]["awards_rewritten"])

    def test_backfill_requires_independent_signers_and_attributes_deviation_to_method(self) -> None:
        instance = make_model()
        define_metric(instance)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "backfill_missing_data_232",
                "bad-backfill",
                backfill_id="b1",
                metric_id="tax-rate",
                value=95,
                method="manual receipts",
                filler_id="same",
                approver_id="same",
                provenance_id="prov-b1",
            )
        self.assertEqual(caught.exception.code, model.RedCode.SIGNATURE_REQUIRED)
        self.assertEqual(instance, before)
        apply(
            instance,
            "backfill_missing_data_232",
            "good-backfill",
            backfill_id="b1",
            metric_id="tax-rate",
            value=95,
            method="manual receipts",
            filler_id="clerk",
            approver_id="auditor",
            provenance_id="prov-b1",
        )
        self.assertFalse(instance.backfills["b1"]["business_owner_automatically_penalized"])

    def test_no_dashboard_access_means_no_unseen_anomaly_blame(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "set_metric_access_233",
            "access",
            metric_id="tax-rate",
            access_level=model.AccessLevel.MANAGER,
            subject_has_access=False,
            query_channel=False,
        )
        record = instance.signal_records["access:tax-rate"]
        self.assertTrue(record["target_adjustment"])
        self.assertFalse(record["subject_accountable_for_unseen_anomaly"])

    def test_leading_and_lagging_signals_are_separate_and_conflict_is_visible(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "record_signals_234",
            "signals",
            signal_id="s1",
            metric_id="tax-rate",
            leading_value=5,
            lagging_value=-2,
        )
        record = instance.signal_records["s1"]
        self.assertEqual(record["recognition"], "settled")
        self.assertTrue(record["conflict_requires_calibration"])

    def test_guardrail_breach_caps_credit_unless_named_crisis_owner_signs(self) -> None:
        instance = make_model()
        apply(
            instance,
            "evaluate_guardrail_235",
            "guardrail-normal",
            assessment_id="g1",
            primary_value=120,
            guardrail_value=40,
            guardrail_floor=60,
            crisis_override=False,
            override_approver_id=None,
        )
        self.assertFalse(instance.guardrails["g1"]["full_top_credit"])
        apply(
            instance,
            "evaluate_guardrail_235",
            "guardrail-crisis",
            assessment_id="g2",
            primary_value=120,
            guardrail_value=40,
            guardrail_floor=60,
            crisis_override=True,
            override_approver_id="emperor",
        )
        self.assertEqual(instance.guardrails["g2"]["delayed_liability_owner"], "emperor")

    def test_scoring_policy_is_frozen_before_year_end(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "lock_scoring_policy_236",
            "policy",
            metric_id="tax-rate",
            policy=model.ScoringPolicy.HYBRID,
            threshold=100,
        )
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(
                instance,
                "lock_scoring_policy_236",
                "year-end-switch",
                metric_id="tax-rate",
                policy=model.ScoringPolicy.CLIFF,
                threshold=100,
            )
        self.assertEqual(instance, before)

    def test_time_window_audit_restores_full_period_and_flags_pretty_slice(self) -> None:
        instance = make_model()
        apply(
            instance,
            "audit_time_window_237",
            "window",
            audit_id="w1",
            frozen_start=1,
            frozen_end=365,
            claimed_start=200,
            claimed_end=260,
            full_period_value=80,
            claimed_value=140,
        )
        record = instance.window_audits["w1"]
        self.assertTrue(record["cherry_picked"])
        self.assertEqual(record["settled_value"], 80)
        self.assertTrue(record["integrity_penalty"])

    def test_vanity_credit_is_clawed_back_without_adoption_or_value(self) -> None:
        instance = make_model()
        apply(
            instance,
            "settle_vanity_value_238",
            "vanity",
            settlement_id="v1",
            vanity_value=1000,
            adoption_value=0,
            governance_value=0,
            provisional_credit=30,
        )
        record = instance.value_settlements["v1"]
        self.assertEqual(record["credit_kept"], 0)
        self.assertEqual(record["credit_clawback"], 30)

    def test_failed_experiment_gets_capped_learning_not_success_credit(self) -> None:
        instance = make_model()
        apply(
            instance,
            "settle_failed_experiment_239",
            "negative-result",
            experiment_id="exp-negative",
            hypothesis="pilot reduces petitions",
            preregistered=True,
            stopped_on_evidence=True,
            reusable_conclusion=True,
        )
        record = instance.experiments["exp-negative"]
        self.assertEqual(record["learning_credit"], 20)
        self.assertEqual(record["success_kpi_credit"], 0)

    def test_sample_slots_and_overlap_routes_conserve(self) -> None:
        instance = make_model(sample_slots=2)
        apply(
            instance,
            "allocate_sample_240",
            "sample-a",
            experiment_id="exp-a",
            samples=("county-a", "county-b"),
            route=model.SampleConflictRoute.PARTITION,
            provenance_id="prov-exp-a",
        )
        apply(
            instance,
            "allocate_sample_240",
            "sample-queued",
            experiment_id="exp-q",
            samples=("county-b",),
            route=model.SampleConflictRoute.QUEUE,
            provenance_id="prov-exp-q",
        )
        self.assertFalse(instance.sample_allocations["exp-q"].active)
        apply(
            instance,
            "allocate_sample_240",
            "sample-contaminated",
            experiment_id="exp-c",
            samples=("county-b",),
            route=model.SampleConflictRoute.ACCEPT_CONTAMINATION,
            provenance_id="prov-exp-c",
        )
        self.assertTrue(instance.sample_allocations["exp-c"].contaminated)
        self.assertEqual(instance.active_sample_slots, 2)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "allocate_sample_240",
                "sample-over-cap",
                experiment_id="exp-over",
                samples=("county-z",),
                route=model.SampleConflictRoute.PARTITION,
                provenance_id="prov-exp-over",
            )
        self.assertEqual(caught.exception.code, model.RedCode.SAMPLE_SLOT_EXHAUSTED)
        self.assertEqual(instance, before)

    def test_long_tail_benefit_and_delayed_cost_share_one_conserved_attribution(self) -> None:
        instance = make_model()
        apply(
            instance,
            "set_long_tail_attribution_241",
            "tail",
            attribution_id="tail-1",
            project_id="project-1",
            start_cycle=7,
            end_cycle=9,
            shares={"builder": 5_000, "operator": 3_000, "improver": 2_000},
        )
        record = instance.long_tail_attributions["tail-1"]
        self.assertEqual(sum(record["benefit_shares"].values()), 10_000)
        self.assertEqual(record["benefit_shares"], record["delayed_cost_shares"])


class ReorganizationTests(unittest.TestCase):
    def test_core_halo_adjustment_is_evidence_capped(self) -> None:
        instance = make_model()
        apply(
            instance,
            "normalize_halo_301",
            "halo",
            record_id="halo-1",
            raw_outcome=100,
            strategic_tailwind=40,
            resource_advantage=30,
            scale_difficulty=10,
            evidence_strength=20,
        )
        record = instance.halo_records["halo-1"]
        self.assertEqual(record["adjustment"], -5)
        self.assertEqual(record["personal_increment"], 95)

    def test_decline_is_scored_against_headwind_and_concealment_is_separate(self) -> None:
        instance = make_model()
        apply(
            instance,
            "evaluate_decline_302",
            "decline",
            record_id="decline-1",
            expected_decline=30,
            actual_decline=10,
            action="defend core users",
            disclosed=False,
        )
        record = instance.decline_records["decline-1"]
        self.assertEqual(record["decline_avoided"], 20)
        self.assertTrue(record["high_quality_defense"])
        self.assertTrue(record["integrity_penalty"])
        self.assertFalse(record["permanent_headwind_immunity"])

    def test_incubation_protection_expires_within_two_cycles(self) -> None:
        instance = make_model()
        apply(
            instance,
            "grant_incubation_303",
            "incubation",
            team_id="new-team",
            start_cycle=7,
            end_cycle=9,
            exit_route="graduate",
            milestone_evidence=True,
        )
        self.assertFalse(instance.incubations["new-team"]["permanent_c_immunity"])
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(
                instance,
                "grant_incubation_303",
                "too-long",
                team_id="forever-team",
                start_cycle=7,
                end_cycle=10,
                exit_route="pivot",
                milestone_evidence=False,
            )
        self.assertEqual(instance, before)

    def test_dual_parent_manager_and_goal_weights_each_sum_one_hundred(self) -> None:
        instance = make_model()
        apply(
            instance,
            "lock_dual_parent_304",
            "dual-parent",
            subject_id="official",
            manager_weights={"project-manager": 70, "function-manager": 30},
            goal_shares={"project-manager": 60, "function-manager": 40},
            final_owner_id="project-manager",
        )
        record = instance.dual_parent_records["official"]
        self.assertEqual(sum(record["manager_weights"].values()), 100)
        self.assertEqual(sum(record["goal_shares"].values()), 100)

    def test_quiet_period_reorg_requires_crisis_reason_and_superior_signature_atomically(self) -> None:
        instance = make_model()
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "apply_reorg_305",
                "illegal-reorg",
                reorg_id="r1",
                days_to_evidence_cutoff=10,
                crisis_reason=None,
                superior_signer_id=None,
                moved_subjects=("official",),
            )
        self.assertEqual(caught.exception.code, model.RedCode.QUIET_PERIOD_VIOLATION)
        self.assertEqual(instance, before)
        apply(
            instance,
            "apply_reorg_305",
            "signed-reorg",
            reorg_id="r1",
            days_to_evidence_cutoff=10,
            crisis_reason="border emergency",
            superior_signer_id="emperor",
            moved_subjects=("official",),
        )
        self.assertTrue(instance.reorg_records["r1"]["old_cohort_frozen"])

    def test_double_hat_capacity_is_split_once_and_expires(self) -> None:
        instance = make_model()
        apply(
            instance,
            "assign_double_hat_306",
            "double-hat",
            actor_id="acting-manager",
            group_weights={"east": 70, "west": 30},
            expires_cycle=8,
            appointing_owner_id="manager",
            support="deputy",
        )
        record = instance.double_hat_records["acting-manager"]
        self.assertEqual(sum(record["group_weights"].values()), 100)
        self.assertFalse(record["two_full_targets"])

    def test_profit_and_cost_centers_use_different_valid_scorecards(self) -> None:
        instance = make_model()
        apply(
            instance,
            "configure_scorecard_307",
            "profit-card",
            team_id="tax-office",
            center_type=model.CenterType.PROFIT,
            metric_keys=("revenue", "quality"),
        )
        apply(
            instance,
            "configure_scorecard_307",
            "cost-card",
            team_id="archive-office",
            center_type=model.CenterType.COST,
            metric_keys=("savings", "stability", "internal_value"),
        )
        self.assertNotEqual(
            instance.scorecards["tax-office"]["center_type"],
            instance.scorecards["archive-office"]["center_type"],
        )

    def test_manager_expert_hc_rebalance_conserves_total(self) -> None:
        instance = make_model(total_hc=20)
        apply(
            instance,
            "rebalance_hc_308",
            "hc",
            manager_hc=4,
            expert_hc=16,
        )
        self.assertEqual(instance.manager_hc + instance.expert_hc, 20)
        self.assertEqual(instance.scorecards["hc-structure"]["reporting_tax"], 8)

    def test_remote_visibility_costs_manager_time_and_creates_no_delivery(self) -> None:
        instance = make_model(management_capacity=5)
        apply(
            instance,
            "visit_remote_team_309",
            "visit",
            team_id="frontier-team",
            manager_hours=3,
            visibility_gain=8,
        )
        record = instance.remote_visits["frontier-team"]
        self.assertEqual(instance.management_capacity_used, 3)
        self.assertEqual(record["delivery_output_created"], 0)

    def test_legacy_rating_map_never_consumes_current_quota(self) -> None:
        instance = make_model()
        apply(
            instance,
            "map_legacy_ratings_310",
            "legacy",
            team_id="merged-team",
            old_ratings={"a": "A", "b": "C"},
            mapping_route="common_baseline",
        )
        self.assertEqual(instance.legacy_maps["merged-team"]["current_quota_slots_consumed"], 0)

    def test_strategy_pivot_keeps_old_goal_frozen_and_starts_new_goal_on_date(self) -> None:
        instance = make_model()
        apply(
            instance,
            "pivot_strategy_311",
            "pivot",
            pivot_id="pivot-1",
            old_goal_id="expand-east",
            old_goal_completed=45,
            new_goal_id="defend-west",
            effective_day=180,
        )
        record = instance.pivots["pivot-1"]
        self.assertFalse(record["old_goal_rewritten"])
        self.assertEqual(record["old_goal_completed"], 45)
        self.assertEqual(record["effective_day"], 180)


class DemandDeliveryTests(unittest.TestCase):
    def test_unified_intake_freezes_source_owner_and_provenance_in_fifo_queue(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        submit_demand(instance, demand_id="d2", proposer_id="p2")
        self.assertEqual(instance.demands["d1"].queue_sequence, 0)
        self.assertEqual(instance.demands["d2"].queue_sequence, 1)
        self.assertEqual(instance.demands["d1"].source, model.DemandSource.TERRITORY)
        self.assertEqual(instance.provenance_index["prov-d1"], "demand:d1")

    def test_emergency_slot_overflow_requires_explicit_tradeoff(self) -> None:
        instance = make_model(emergency_slots=1)
        submit_demand(instance, demand_id="d1")
        submit_demand(instance, demand_id="d2")
        apply(
            instance,
            "mark_emergency_335",
            "emergency-1",
            demand_id="d1",
            overflow_tradeoff=None,
        )
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(
                instance,
                "mark_emergency_335",
                "emergency-invalid",
                demand_id="d2",
                overflow_tradeoff=None,
            )
        self.assertEqual(instance, before)
        apply(
            instance,
            "mark_emergency_335",
            "emergency-2",
            demand_id="d2",
            overflow_tradeoff="sponsor_liability",
        )
        self.assertEqual(instance.emergency_slots_used, 1)

    def test_incomplete_demand_can_return_or_take_small_exploration_not_silent_commitment(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        apply(
            instance,
            "admit_demand_336",
            "explore",
            demand_id="d1",
            benefit="discover beneficiary",
            acceptance=None,
            boundary=None,
            dependencies=(),
            estimated_hours=5,
            route=model.AdmissionRoute.EXPLORATION,
            forcing_owner_id=None,
        )
        demand = instance.demands["d1"]
        self.assertTrue(demand.admitted)
        self.assertEqual(demand.admission_route, model.AdmissionRoute.EXPLORATION)
        self.assertFalse(demand.forced_owner_liability)

    def test_change_tax_is_paid_once_and_disaster_waiver_cannot_repeat(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        admit_complete(instance, demand_id="d1")
        apply(
            instance,
            "change_demand_337",
            "change",
            demand_id="d1",
            route=model.ChangeRoute.EXTEND,
            tax_hours=3,
            approver_id="manager",
        )
        apply(
            instance,
            "change_demand_337",
            "waiver",
            demand_id="d1",
            route=model.ChangeRoute.DISASTER_WAIVER,
            tax_hours=0,
            approver_id="emperor",
        )
        self.assertEqual(instance.demands["d1"].change_tax_hours, 3)
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed):
            apply(
                instance,
                "change_demand_337",
                "waiver-again",
                demand_id="d1",
                route=model.ChangeRoute.DISASTER_WAIVER,
                tax_hours=0,
                approver_id="emperor",
            )
        self.assertEqual(instance, before)

    def test_quality_tradeoff_freezes_approver_as_future_liability_owner(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        admit_complete(instance, demand_id="d1")
        apply(
            instance,
            "sign_delivery_triangle_338",
            "triangle",
            demand_id="d1",
            tradeoff=model.TriangleTradeoff.LOWER_QUALITY,
            approver_id="manager",
        )
        demand = instance.demands["d1"]
        self.assertEqual(demand.triangle_approver_id, "manager")
        self.assertEqual(demand.quality_liability_id, "manager")

    def test_estimation_calibration_separates_external_blocking_and_padding(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        admit_complete(instance, demand_id="d1", hours=30)
        apply(
            instance,
            "calibrate_estimate_339",
            "estimate",
            demand_id="d1",
            actual_hours=35,
            complexity_miss=False,
            external_blocking_hours=10,
        )
        demand = instance.demands["d1"]
        self.assertEqual(demand.estimate_error, -5)
        self.assertEqual(demand.estimate_reason, "calibrated")

    def test_wip_limit_allows_signed_or_detected_breach_and_capacity_conserves(self) -> None:
        instance = make_model(wip_limit=1, capacity=60)
        for demand_id in ("d1", "d2"):
            submit_demand(instance, demand_id=demand_id)
            admit_complete(instance, demand_id=demand_id, hours=20)
        apply(
            instance,
            "start_work_340",
            "start-1",
            demand_id="d1",
            exception_owner_id=None,
            hidden_extra_wip=False,
        )
        apply(
            instance,
            "start_work_340",
            "start-hidden",
            demand_id="d2",
            exception_owner_id=None,
            hidden_extra_wip=True,
        )
        self.assertEqual(instance.active_wip, 2)
        self.assertEqual(instance.wip_exception_count, 1)
        self.assertEqual(instance.demands["d2"].hidden_wip_penalty, 2)
        self.assertEqual(instance.capacity_hours_reserved, 40)

    def test_carryover_reserves_next_cycle_once_and_preserves_accepted_work(self) -> None:
        instance = make_model(next_capacity=20)
        submit_demand(instance, demand_id="d1")
        admit_complete(instance, demand_id="d1", hours=20)
        apply(
            instance,
            "start_work_340",
            "start",
            demand_id="d1",
            exception_owner_id=None,
            hidden_extra_wip=False,
        )
        apply(
            instance,
            "carryover_demand_341",
            "carry",
            demand_id="d1",
            unfinished_hours=8,
            accepted_hours=12,
            route=model.CarryoverRoute.SPLIT_ACCEPTED,
        )
        demand = instance.demands["d1"]
        self.assertEqual(instance.next_cycle_capacity_reserved, 8)
        self.assertEqual(demand.accepted_hours, 12)
        self.assertFalse(demand.active)
        self.assertEqual(instance.capacity_hours_reserved, 0)

    def test_blocker_provenance_moves_collaboration_blame_without_auto_low_output(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1")
        apply(
            instance,
            "record_blocker_342",
            "blocker",
            demand_id="d1",
            blocker_owner_id="dependency-team",
            blocked_since_day=100,
            escalated_day=102,
        )
        blocker = instance.demands["d1"].blocker
        self.assertFalse(blocker["executor_low_output_penalty"])
        self.assertFalse(blocker["executor_shared_responsibility"])
        self.assertTrue(blocker["blocker_collaboration_penalty"])

    def test_delivery_requires_three_distinct_signatures_and_matching_proposer(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1", proposer_id="proposer")
        before = copy.deepcopy(instance)
        with self.assertRaises(model.DomainRed) as caught:
            apply(
                instance,
                "accept_delivery_343",
                "bad-signatures",
                demand_id="d1",
                proposer_signer_id="proposer",
                executor_signer_id="same",
                beneficiary_signer_id="same",
                outcome=model.AcceptanceOutcome.ACCEPTED,
            )
        self.assertEqual(caught.exception.code, model.RedCode.SIGNATURE_REQUIRED)
        self.assertEqual(instance, before)

    def test_launch_adoption_value_settle_in_order_and_never_exceed_full_credit(self) -> None:
        instance = make_model()
        submit_demand(instance, demand_id="d1", proposer_id="proposer")
        apply(
            instance,
            "accept_delivery_343",
            "accept",
            demand_id="d1",
            proposer_signer_id="proposer",
            executor_signer_id="executor",
            beneficiary_signer_id="beneficiary",
            outcome=model.AcceptanceOutcome.ACCEPTED,
        )
        for stage, credit in (
            (model.ValueStage.LAUNCH, 2_000),
            (model.ValueStage.ADOPTION, 3_000),
            (model.ValueStage.VALUE, 5_000),
        ):
            apply(
                instance,
                "settle_value_stage_344",
                f"value-{stage.value}",
                demand_id="d1",
                stage=stage,
                credit_basis_points=credit,
            )
        self.assertEqual(sum(instance.demands["d1"].value_credits.values()), 10_000)


class ExactBehaviorCoverageTests(unittest.TestCase):
    def test_one_scenario_applies_every_requested_id_and_preserves_all_invariants(self) -> None:
        instance = make_model()
        define_metric(instance)
        apply(
            instance,
            "reconcile_sources_230",
            "230",
            reconciliation_id="rec",
            metric_id="tax-rate",
            source_values={"treasury": 90, "prefecture": 100},
            route=model.ReconcileRoute.JOINT,
            authority_source=None,
            provenance_id="prov-rec",
        )
        apply(
            instance,
            "change_denominator_231",
            "231",
            metric_id="tax-rate",
            new_denominator=120,
            reason="scope expansion",
            effective_cycle=8,
        )
        apply(
            instance,
            "backfill_missing_data_232",
            "232",
            backfill_id="backfill",
            metric_id="tax-rate",
            value=95,
            method="signed receipts",
            filler_id="clerk",
            approver_id="auditor",
            provenance_id="prov-backfill",
        )
        apply(
            instance,
            "set_metric_access_233",
            "233",
            metric_id="tax-rate",
            access_level=model.AccessLevel.ROLE_LAYERED,
            subject_has_access=True,
            query_channel=True,
        )
        apply(
            instance,
            "record_signals_234",
            "234",
            signal_id="signals",
            metric_id="tax-rate",
            leading_value=5,
            lagging_value=3,
        )
        apply(
            instance,
            "evaluate_guardrail_235",
            "235",
            assessment_id="guardrail",
            primary_value=110,
            guardrail_value=70,
            guardrail_floor=60,
            crisis_override=False,
            override_approver_id=None,
        )
        apply(
            instance,
            "lock_scoring_policy_236",
            "236",
            metric_id="tax-rate",
            policy=model.ScoringPolicy.CONTINUOUS,
            threshold=100,
        )
        apply(
            instance,
            "audit_time_window_237",
            "237",
            audit_id="window",
            frozen_start=1,
            frozen_end=365,
            claimed_start=1,
            claimed_end=365,
            full_period_value=100,
            claimed_value=100,
        )
        apply(
            instance,
            "settle_vanity_value_238",
            "238",
            settlement_id="value",
            vanity_value=100,
            adoption_value=20,
            governance_value=10,
            provisional_credit=30,
        )
        apply(
            instance,
            "settle_failed_experiment_239",
            "239",
            experiment_id="negative",
            hypothesis="pilot works",
            preregistered=True,
            stopped_on_evidence=True,
            reusable_conclusion=True,
        )
        apply(
            instance,
            "allocate_sample_240",
            "240",
            experiment_id="sample-exp",
            samples=("county-a",),
            route=model.SampleConflictRoute.PARTITION,
            provenance_id="prov-sample",
        )
        apply(
            instance,
            "set_long_tail_attribution_241",
            "241",
            attribution_id="tail",
            project_id="project",
            start_cycle=7,
            end_cycle=9,
            shares={"builder": 6_000, "operator": 4_000},
        )
        apply(
            instance,
            "normalize_halo_301",
            "301",
            record_id="halo",
            raw_outcome=100,
            strategic_tailwind=10,
            resource_advantage=5,
            scale_difficulty=10,
            evidence_strength=80,
        )
        apply(
            instance,
            "evaluate_decline_302",
            "302",
            record_id="decline",
            expected_decline=20,
            actual_decline=10,
            action="defend users",
            disclosed=True,
        )
        apply(
            instance,
            "grant_incubation_303",
            "303",
            team_id="incubator",
            start_cycle=7,
            end_cycle=8,
            exit_route="graduate",
            milestone_evidence=True,
        )
        apply(
            instance,
            "lock_dual_parent_304",
            "304",
            subject_id="official",
            manager_weights={"project": 60, "function": 40},
            goal_shares={"project": 70, "function": 30},
            final_owner_id="project",
        )
        apply(
            instance,
            "apply_reorg_305",
            "305",
            reorg_id="reorg",
            days_to_evidence_cutoff=45,
            crisis_reason=None,
            superior_signer_id=None,
            moved_subjects=("official",),
        )
        apply(
            instance,
            "assign_double_hat_306",
            "306",
            actor_id="acting",
            group_weights={"east": 50, "west": 50},
            expires_cycle=8,
            appointing_owner_id="manager",
            support="target_reduction",
        )
        apply(
            instance,
            "configure_scorecard_307",
            "307",
            team_id="profit-team",
            center_type=model.CenterType.PROFIT,
            metric_keys=("revenue", "quality"),
        )
        apply(instance, "rebalance_hc_308", "308", manager_hc=4, expert_hc=16)
        apply(
            instance,
            "visit_remote_team_309",
            "309",
            team_id="remote",
            manager_hours=2,
            visibility_gain=5,
        )
        apply(
            instance,
            "map_legacy_ratings_310",
            "310",
            team_id="legacy",
            old_ratings={"a": "A", "b": "B"},
            mapping_route="context_only",
        )
        apply(
            instance,
            "pivot_strategy_311",
            "311",
            pivot_id="pivot",
            old_goal_id="old",
            old_goal_completed=20,
            new_goal_id="new",
            effective_day=180,
        )
        submit_demand(instance, demand_id="d1", proposer_id="proposer")
        apply(
            instance,
            "mark_emergency_335",
            "335",
            demand_id="d1",
            overflow_tradeoff=None,
        )
        apply(
            instance,
            "admit_demand_336",
            "336",
            demand_id="d1",
            benefit="reduce delay",
            acceptance="beneficiary uses it",
            boundary="one office",
            dependencies=("records",),
            estimated_hours=20,
            route=model.AdmissionRoute.COMMITMENT,
            forcing_owner_id=None,
        )
        apply(
            instance,
            "change_demand_337",
            "337",
            demand_id="d1",
            route=model.ChangeRoute.EXTEND,
            tax_hours=2,
            approver_id="manager",
        )
        apply(
            instance,
            "sign_delivery_triangle_338",
            "338",
            demand_id="d1",
            tradeoff=model.TriangleTradeoff.EXTEND_TIME,
            approver_id="manager",
        )
        apply(
            instance,
            "calibrate_estimate_339",
            "339",
            demand_id="d1",
            actual_hours=22,
            complexity_miss=True,
            external_blocking_hours=0,
        )
        apply(
            instance,
            "start_work_340",
            "340",
            demand_id="d1",
            exception_owner_id=None,
            hidden_extra_wip=False,
        )
        apply(
            instance,
            "carryover_demand_341",
            "341",
            demand_id="d1",
            unfinished_hours=5,
            accepted_hours=15,
            route=model.CarryoverRoute.SPLIT_ACCEPTED,
        )
        apply(
            instance,
            "record_blocker_342",
            "342",
            demand_id="d1",
            blocker_owner_id="records",
            blocked_since_day=100,
            escalated_day=101,
        )
        apply(
            instance,
            "accept_delivery_343",
            "343",
            demand_id="d1",
            proposer_signer_id="proposer",
            executor_signer_id="executor",
            beneficiary_signer_id="beneficiary",
            outcome=model.AcceptanceOutcome.ACCEPTED,
        )
        apply(
            instance,
            "settle_value_stage_344",
            "344",
            demand_id="d1",
            stage=model.ValueStage.LAUNCH,
            credit_basis_points=2_000,
        )
        instance.assert_invariants()
        self.assertEqual(instance.applied_mechanism_ids, set(model.EXPECTED_MECHANISM_IDS))
        self.assertEqual(len(instance.receipts), instance.revision)


if __name__ == "__main__":
    unittest.main()
