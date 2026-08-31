#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semantic tests for the dedicated manager/governance L0 oracle."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zg361_manager_governance_model as model


def identity(cycle: int = 20, case: int = 7) -> model.CaseIdentity:
    return model.CaseIdentity("emperor", "manager", cycle, case)


def annual_logs() -> tuple[dict[str, int | str], ...]:
    return tuple(
        {
            "annual_id": f"annual-{year}",
            "owner_id": "emperor",
            "year": year,
            "top": 3,
            "middle": 6,
            "bottom": 1,
            "appeal_overturns": year % 2,
            "pip_successes": 2,
            "promotions": 1,
            "exits": 1,
            "bonus_in": 10,
            "bonus_out": 6,
            "hc_efficiency": 80,
        }
        for year in range(100, 110)
    )


def team_metrics() -> dict[str, int]:
    return dict(zip(model.TEAM_METRIC_NAMES, (10, 10, -5, 5, -5, 4, 3), strict=True))


def valid_q_fields(mechanism_id: int) -> dict[str, object]:
    return {
        121: {"trial_team_size": 3, "mentor_id": "mentor", "skip_reviewer_id": "skip", "due_cycle": 21, "outcome": "passed"},
        122: {"result_score": 70, "talent_score": 70, "process_score": 70, "weights": (40, 30, 30), "final_score": 70},
        123: {"sample_count": 3, "six_dimensions": (70,) * 6, "credibility_total": 300, "consensus": "positive"},
        124: {"successor_id": "successor", "trial_due": 21, "handover_status": "accepted", "promotion_released": True, "liability_owner": "emperor"},
        125: {"incident_id": "incident", "budget": 100, "manager_hours": 40, "delegate_id": "delegate", "delegate_hours": 60, "outcome": "resolved"},
        126: {"performance_band": "high", "values_band": "high", "quadrant": "high-high", "disposition": "promote"},
        127: {"report_count": 11, "span_limit": 8, "delegate_count": 3, "evidence_coverage": 100, "distortion": False},
        128: {"pressure": 40, "collaboration": 70, "risk_reporting": 60, "review_trust": 65, "regretted_attrition": 1, "effective_cycle": 21},
    }[mechanism_id]


def q_object(
    mechanism_id: int,
    route: model.Choice,
    *,
    owner: str = "emperor",
    subject: str = "manager",
    cycle: int = 20,
    case: int | None = None,
    revision: int = 1,
) -> model.AuthoritativeManagerObject:
    return model.AuthoritativeManagerObject(
        f"q-{mechanism_id}-{cycle}-{case or mechanism_id}",
        owner,
        subject,
        cycle,
        case or mechanism_id,
        model.Q_EXPECTED_STATE[mechanism_id],
        revision,
        route,
    )


class ManagerGovernanceModelTests(unittest.TestCase):
    def test_scope_and_readiness_are_honest(self) -> None:
        self.assertEqual(model.OWNED_IDS, (*range(32, 37), *range(345, 355)))
        self.assertEqual(model.Q_PROJECTION_IDS, tuple(range(121, 129)))
        self.assertEqual(model.READINESS, "python-l0-only")
        self.assertEqual(model.MCP_EVIDENCE, "none")
        self.assertFalse(set(model.OWNED_IDS) & set(model.Q_PROJECTION_IDS))
        with self.assertRaisesRegex(model.ModelRed, "outside owned"):
            model.GovernanceLedger().apply(121, model.Choice.A, identity())

    def test_every_owned_id_has_a_b_and_c_stable_outcome(self) -> None:
        builders = {
            32: dict(snapshot_id="team-19", direct_liege_id="emperor", source_team_serial=19, metrics=team_metrics(), grandchild_ids=()),
            33: dict(profile="data", weight_version=1, reason_inputs={"calibration": 3, "appeal": -2, "pip": 4, "delivery": 25, "hc": 6}, before=2, relationship_override=1),
            34: dict(history=(70, 80), potential=85),
            35: dict(cohort=10, ratio_override=None, game_rule="zg361_ratio_strict"),
            36: dict(logs=annual_logs(), current_snapshot={"top": 3, "bottom": 1}, government_eligible=True, generated_day=4000),
            345: dict(effective_cycle=21),
            346: dict(materiality=80, signal_id="signal-1", official_id="manager", signal_type="achievement", evidence_ids=("e-1",), recorded_day=100, original_board_version="board-19", action="reward"),
            347: dict(algorithmic_order=("a", "b", "c"), operations=(("a", "b", "cross-team"),), overturned=(False,)),
            348: dict(exception_id="ex-1", granted_day=100, resolved_day=465, new_evidence=False, jingcha_batch_id="jc-1"),
            349: dict(risks={f"case-{index}": index * 5 for index in range(20)}, seed=42, transparency=5, capacity=100),
            350: dict(old_version="v1", new_version="v2", history=({"kpi": 80, "rating": 3}, {"kpi": 80, "rating": 2}, {"kpi": 80, "rating": 1}), old_threshold=70, strategy_difficulty=5, top_growth=8),
            351: dict(metrics=("quality",), outcomes={"p1": {"quality": 80}, "p2": {"quality": 90}, "c1": {"quality": 60}, "c2": {"quality": 70}}, pilots=("p1", "p2"), controls=("c1", "c2"), regions=("p1", "p2", "c1", "c2"), end_cycle=22),
            352: dict(records=({"record_id": "r1", "original_value": 3, "original_formula": "old", "original_policy_version": "v1"},), mapping_version="map-v2", factor=100),
            353: dict(form_hours=10, meeting_hours=5, appeal_hours=4, calibration_hours=3, interruption_hours=2, available_hours=100, error_rate=2, overturn_rate=1, simplified=("duplicate-form",)),
            354: dict(delivered=10, appeals=4, overturns=2, exits=4, healthy_exits=1, reported=(0.2, 0.25, 0.5)),
        }
        for mechanism_id, facts in builders.items():
            for route in model.Choice:
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    ledger = model.GovernanceLedger()
                    routed_facts = dict(facts)
                    if mechanism_id == 34 and route is model.Choice.B:
                        routed_facts["history"] = (80,)
                    if mechanism_id == 36 and route is model.Choice.B:
                        routed_facts["logs"] = ()
                    result = ledger.apply(mechanism_id, route, identity(case=mechanism_id), **routed_facts)
                    self.assertTrue(result.applied)
                    if route is model.Choice.C:
                        self.assertIsNone(result.business)
                        self.assertTrue(result.policy_debt_created)
                        self.assertEqual(ledger.policy_debts[(mechanism_id, identity(case=mechanism_id))], 21)
                    else:
                        self.assertIsNotNone(result.business)
                        self.assertEqual(result.business.route, route)
                    replay = ledger.apply(mechanism_id, route, identity(case=mechanism_id), **routed_facts)
                    self.assertFalse(replay.applied)
                    self.assertTrue(replay.duplicate)
                    self.assertEqual(replay.route, route)
                    conflicting_route = model.Choice.B if route is model.Choice.A else model.Choice.A
                    with self.assertRaisesRegex(model.ModelRed, "stale:duplicate"):
                        ledger.apply(mechanism_id, conflicting_route, identity(case=mechanism_id), **routed_facts)

    def test_c_policy_debt_has_exact_next_cycle_consumer_and_owner_identity(self) -> None:
        ledger = model.GovernanceLedger()
        source = identity(cycle=20, case=345)
        created = ledger.apply(345, model.Choice.C, source)
        self.assertTrue(created.policy_debt_created)
        self.assertIsNone(created.business)
        self.assertEqual(ledger.policy_debts[(345, source)], 21)
        with self.assertRaisesRegex(model.ModelRed, "stale:current_cycle"):
            ledger.consume_policy_debt(
                345,
                source,
                current_cycle=20,
                settled_by_owner_id="emperor",
                current_direct_liege_id="emperor",
                remediation_code="calendar-reviewed",
            )
        settlement = ledger.consume_policy_debt(
            345,
            source,
            current_cycle=21,
            settled_by_owner_id="new-emperor",
            current_direct_liege_id="new-emperor",
            remediation_code="calendar-reviewed",
        )
        self.assertEqual(settlement.source_identity.owner_id, "emperor")
        self.assertEqual(settlement.settled_by_owner_id, "new-emperor")
        self.assertEqual(settlement.manager_score_delta, -3)
        self.assertEqual(ledger.manager_score_adjustments["manager"], -3)
        self.assertIsNone(
            ledger.consume_policy_debt(
                345,
                source,
                current_cycle=21,
                settled_by_owner_id="new-emperor",
                current_direct_liege_id="new-emperor",
                remediation_code="calendar-reviewed",
            )
        )
        with self.assertRaisesRegex(model.ModelRed, "stale:settlement"):
            ledger.consume_policy_debt(
                345,
                source,
                current_cycle=22,
                settled_by_owner_id="new-emperor",
                current_direct_liege_id="new-emperor",
                remediation_code="different-rewrite",
            )
        with self.assertRaisesRegex(model.ModelRed, "missing:policy_debt"):
            ledger.consume_policy_debt(
                345,
                model.CaseIdentity("other-owner", "manager", 20, 345),
                current_cycle=21,
                settled_by_owner_id="new-emperor",
                current_direct_liege_id="new-emperor",
                remediation_code="wrong-owner",
            )

    def test_all_owned_ids_have_a_negative_case_with_zero_partial_write(self) -> None:
        invalid = {
            32: dict(snapshot_id="s", direct_liege_id="usurper", source_team_serial=19, metrics=team_metrics()),
            33: dict(profile="unknown", weight_version=1, reason_inputs={"calibration": 0, "appeal": 0, "pip": 0, "delivery": 0, "hc": 0}),
            34: dict(history=(), potential=80),
            35: dict(cohort=-1, ratio_override=None, game_rule="zg361_ratio_strict"),
            36: dict(logs=annual_logs()[:-1], government_eligible=True, generated_day=4000),
            345: dict(effective_cycle=99),
            346: dict(materiality=49, signal_id="minor", action="reward"),
            347: dict(algorithmic_order=("a", "b", "c", "d"), operations=(("a", "b", "r1"), ("c", "d", "r2"), ("a", "c", "r3"))),
            348: dict(exception_id="e", granted_day=100, resolved_day=200, new_evidence=False, jingcha_batch_id="j"),
            349: dict(risks={"a": 100}, seed=1, transparency=0, capacity=0),
            350: dict(old_version="v1", new_version="v1", history=({"kpi": 1},) * 3, old_threshold=70),
            351: dict(metrics=("m",), outcomes={"p": {"m": 1}}, pilots=("p", "x"), controls=("p", "y"), end_cycle=21),
            352: dict(records=(), mapping_version="m", factor=1),
            353: dict(form_hours=10, meeting_hours=10, appeal_hours=10, calibration_hours=10, interruption_hours=10, available_hours=1),
            354: dict(delivered=1, appeals=2, overturns=0, exits=1, healthy_exits=0),
        }
        for mechanism_id, facts in invalid.items():
            with self.subTest(mechanism_id=mechanism_id):
                ledger = model.GovernanceLedger()
                before = repr(ledger)
                with self.assertRaises(model.ModelRed):
                    ledger.apply(mechanism_id, model.Choice.A, identity(case=mechanism_id), **facts)
                self.assertEqual(repr(ledger), before)

    def test_stale_successor_owner_drift_and_object_version_identity(self) -> None:
        facts = dict(profile="data", weight_version=1, reason_inputs={"calibration": 1, "appeal": 2, "pip": 3, "delivery": 4, "hc": 5})
        ledger = model.GovernanceLedger()
        first_identity = model.CaseIdentity("emperor", "manager", 20, 33, 2, 1)
        first = ledger.apply(33, 1, first_identity, **facts).business
        revised_identity = model.CaseIdentity("emperor", "manager", 20, 33, 2, 2)
        revised = ledger.apply(33, 1, revised_identity, **facts).business
        self.assertEqual(first.object_id, revised.object_id)
        self.assertEqual(first.content_hash, revised.content_hash)
        with self.assertRaisesRegex(model.ModelRed, "stale:identity"):
            ledger.apply(33, 1, first_identity, **facts)
        with self.assertRaisesRegex(model.ModelRed, "permission:owner_id"):
            ledger.apply(33, 1, model.CaseIdentity("usurper", "manager", 20, 33, 2, 2), **facts)

    def test_q_projection_all_ids_routes_and_never_owns_q_case(self) -> None:
        for mechanism_id in model.Q_PROJECTION_IDS:
            for route in model.Choice:
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    ledger = model.GovernanceLedger()
                    before = (
                        dict(ledger.records),
                        dict(ledger.routes),
                        dict(ledger.operation_fingerprints),
                        dict(ledger.policy_debts),
                        dict(ledger.policy_debt_settlements),
                        dict(ledger.latest_cases),
                    )
                    fields = {"policy_debt_due": 21} if route is model.Choice.C else valid_q_fields(mechanism_id)
                    receipt = model.ManagerCertificationReceipt(
                        mechanism_id,
                        "emperor",
                        "manager",
                        20,
                        mechanism_id,
                        model.Q_EXPECTED_STATE[mechanism_id],
                        1,
                        route,
                        True,
                        {model.Choice.A: 1, model.Choice.B: -1, model.Choice.C: 0}[route],
                        fields,
                        None if route is model.Choice.C else q_object(mechanism_id, route),
                    )
                    self.assertTrue(ledger.project_manager_certification(receipt))
                    self.assertEqual(
                        (
                            ledger.records,
                            ledger.routes,
                            ledger.operation_fingerprints,
                            ledger.policy_debts,
                            ledger.policy_debt_settlements,
                            ledger.latest_cases,
                        ),
                        before,
                    )

    def test_032_previous_cycle_aggregate_and_exact_jingcha_consumption(self) -> None:
        ledger = model.GovernanceLedger()
        facts = dict(
            snapshot_id="team-19",
            direct_liege_id="emperor",
            source_team_serial=19,
            metrics=dict(zip(model.TEAM_METRIC_NAMES, (10, 5, -5, 3, -4, 2, 1), strict=True)),
            grandchild_ids=(),
            saved_superior="emperor",
            mandate_year=1066,
        )
        first = ledger.apply(32, model.Choice.A, identity(case=32), **facts).business
        second = ledger.apply(32, model.Choice.A, identity(cycle=21, case=33), **facts).business
        self.assertEqual(first.get("jingcha_delta"), -50)
        self.assertEqual(second.get("jingcha_delta"), 0)
        with self.assertRaisesRegex(model.ModelRed, "stale:source_team_serial"):
            model.GovernanceLedger().apply(32, 1, identity(), snapshot_id="s", direct_liege_id="emperor", source_team_serial=20, metrics=dict.fromkeys(model.TEAM_METRIC_NAMES, 0))
        with self.assertRaisesRegex(model.ModelRed, "grandchild_ids"):
            model.GovernanceLedger().apply(32, 2, identity(), snapshot_id="s", direct_liege_id="emperor", source_team_serial=19, metrics=dict.fromkeys(model.TEAM_METRIC_NAMES, 0), grandchild_ids=("baron",))

    def test_032_next_cycle_settles_once_inside_official_organization_component(self) -> None:
        ledger = model.GovernanceLedger()
        source = identity(cycle=20, case=32)
        business = ledger.apply(
            32,
            model.Choice.A,
            source,
            snapshot_id="team-19",
            direct_liege_id="emperor",
            source_team_serial=19,
            metrics=team_metrics(),
            grandchild_ids=(),
        ).business
        pending = ledger.manager_organization_pending[source]
        self.assertEqual((pending.due_cycle, pending.score, pending.component_number), (21, business.get("score"), 8))
        components = (1, 2, 3, 4, 5, 6, 7, 8)
        with self.assertRaisesRegex(model.ModelRed, "not due until next cycle"):
            ledger.consume_manager_organization_score(
                source,
                current_cycle=20,
                settled_by_owner_id="emperor",
                current_direct_liege_id="emperor",
                official_components=components,
            )
        with self.assertRaisesRegex(model.ModelRed, "exactly eight components"):
            ledger.consume_manager_organization_score(
                source,
                current_cycle=21,
                settled_by_owner_id="emperor",
                current_direct_liege_id="emperor",
                official_components=(*components, 9),
            )
        receipt = ledger.consume_manager_organization_score(
            source,
            current_cycle=21,
            settled_by_owner_id="new-emperor",
            current_direct_liege_id="new-emperor",
            official_components=components,
        )
        self.assertEqual(len(receipt.components_after), 8)
        self.assertEqual(receipt.components_after[:7], components[:7])
        self.assertEqual(receipt.components_after[7], components[7] + business.get("score"))
        self.assertEqual(receipt.official_kpi_after - receipt.official_kpi_before, business.get("score"))
        self.assertNotIn(source, ledger.manager_organization_pending)
        self.assertIsNone(
            ledger.consume_manager_organization_score(
                source,
                current_cycle=21,
                settled_by_owner_id="new-emperor",
                current_direct_liege_id="new-emperor",
                official_components=components,
            )
        )
        with self.assertRaisesRegex(model.ModelRed, "settled organization evidence cannot be rewritten"):
            ledger.consume_manager_organization_score(
                source,
                current_cycle=22,
                settled_by_owner_id="new-emperor",
                current_direct_liege_id="new-emperor",
                official_components=components,
            )

    def test_033_b_override_is_bounded_visible_and_does_not_erase_evidence(self) -> None:
        facts = dict(profile="political", weight_version=4, reason_inputs={"calibration": 99, "appeal": -99, "pip": 1, "delivery": 2, "hc": 3}, before=2, relationship_override=1)
        business = model.GovernanceLedger().apply(33, 2, identity(), **facts).business
        reasons = dict(business.get("reason_codes"))
        self.assertTrue(all(-25 <= value <= 25 for value in reasons.values()))
        self.assertEqual((business.get("before_band"), business.get("after_band")), (2, 3))
        self.assertGreater(business.get("appeal_risk"), 0)

    def test_034_routes_are_read_only_and_b_expires(self) -> None:
        a = model.GovernanceLedger().apply(34, 1, identity(), history=(30, 80), potential=90).business
        b = model.GovernanceLedger().apply(34, 2, identity(), history=(80,), potential=90).business
        for business in (a, b):
            self.assertEqual((business.get("grade_delta"), business.get("kpi_delta"), business.get("resource_delta")), (0, 0, 0))
        self.assertIsNone(a.get("expires_cycle"))
        self.assertEqual(b.get("expires_cycle"), 21)
        first_cycle = model.GovernanceLedger().apply(34, 1, identity(), history=(80,), potential=90).business
        self.assertFalse(first_cycle.get("ready"))
        self.assertEqual(first_cycle.get("box"), 0)
        self.assertEqual(first_cycle.get("status"), "insufficient-frozen-history")

    def test_035_actual_relaxed_producer_and_forced_strict_conserve(self) -> None:
        facts = dict(cohort=10, ratio_override=None, game_rule="zg361_ratio_relaxed")
        a = model.GovernanceLedger().apply(35, 1, identity(), **facts).business
        b = model.GovernanceLedger().apply(35, 2, identity(), **facts).business
        for business in (a, b):
            self.assertEqual(business.get("top") + business.get("middle") + business.get("bottom"), 10)
            self.assertEqual(business.get("effective_cycle"), 21)
        self.assertEqual((a.get("mode"), a.get("bottom"), a.get("rule_source")), ("relaxed", 0, "game-rule"))
        self.assertEqual((b.get("mode"), b.get("bottom_consequence")), ("strict", "normal"))
        self.assertEqual(b.get("bottom"), 1)

    def test_035_exact_override_precedence_and_three_modes_freeze(self) -> None:
        snapshots = {
            value: model.compute_distribution_snapshot(
                ratio_override=value,
                game_rule="zg361_ratio_off",
                cohort=20,
                review_serial=20,
            )
            for value in (10, 5, 0)
        }
        self.assertEqual({snapshots[value]["mode"] for value in snapshots}, {"strict", "relaxed", "off"})
        self.assertTrue(all(row["rule_source"] == "liege-override" for row in snapshots.values()))
        self.assertEqual(snapshots[10]["bottom"], 2)
        self.assertEqual(snapshots[5]["bottom"], 1)
        self.assertEqual(snapshots[0]["bottom"], 0)
        game_rule = model.compute_distribution_snapshot(
            ratio_override=None,
            game_rule="zg361_ratio_relaxed",
            cohort=20,
            review_serial=20,
        )
        self.assertEqual((game_rule["mode"], game_rule["rule_source"], game_rule["producer_value"]), ("relaxed", "game-rule", "zg361_ratio_relaxed"))
        self.assertEqual(snapshots[10]["top"], 6)
        self.assertTrue(all(row["top"] + row["middle"] + row["bottom"] == 20 for row in snapshots.values()))
        frozen_hash = snapshots[10]["snapshot_hash"]
        later_policy = model.compute_distribution_snapshot(
            ratio_override=0,
            game_rule="zg361_ratio_strict",
            cohort=20,
            review_serial=21,
        )
        self.assertEqual(snapshots[10]["snapshot_hash"], frozen_hash)
        self.assertNotEqual(later_policy["snapshot_hash"], frozen_hash)
        with self.assertRaisesRegex(model.ModelRed, "actual override must be 10/5/0"):
            model.compute_distribution_snapshot(
                ratio_override=7,
                game_rule="zg361_ratio_strict",
                cohort=20,
                review_serial=20,
            )
        with self.assertRaisesRegex(model.ModelRed, "strict/relaxed/off game rule"):
            model.compute_distribution_snapshot(
                ratio_override=None,
                game_rule="invented-mixed",
                cohort=20,
                review_serial=20,
            )

    def test_036_a_is_real_ten_year_report_b_is_explicit_snapshot(self) -> None:
        a = model.GovernanceLedger().apply(36, 1, identity(), logs=annual_logs(), government_eligible=True, generated_day=4000).business
        b = model.GovernanceLedger().apply(36, 2, identity(case=8), current_snapshot={"top": 4, "bottom": 1}, government_eligible=True, generated_day=4000).business
        self.assertTrue(a.get("is_ten_year_report"))
        self.assertEqual(a.get("bonus_net"), 40)
        self.assertFalse(b.get("is_ten_year_report"))
        self.assertEqual(b.get("history_rows"), 0)
        broken = list(annual_logs())
        broken[-1] = dict(broken[-1], owner_id="new-emperor")
        with self.assertRaisesRegex(model.ModelRed, "one owner"):
            model.GovernanceLedger().apply(36, 1, identity(), logs=broken, government_eligible=True, generated_day=4000)
        malformed = list(annual_logs())
        malformed[-1] = {**malformed[-1], "invented_metric": 1}
        with self.assertRaisesRegex(model.ModelRed, "exact annual metric schema"):
            model.GovernanceLedger().apply(36, 1, identity(), logs=malformed, government_eligible=True, generated_day=4000)
        with self.assertRaisesRegex(model.ModelRed, "eligible celestial manager"):
            model.GovernanceLedger().apply(36, 1, identity(), logs=annual_logs(), government_eligible=False, generated_day=4000)

    def test_345_a_batches_once_b_pays_quarterly_cost(self) -> None:
        a = model.GovernanceLedger().apply(345, 1, identity(), effective_cycle=21).business
        b = model.GovernanceLedger().apply(345, 2, identity(case=8), effective_cycle=21).business
        self.assertEqual((a.get("review_instances"), a.get("ai_batches")), (1, 1))
        self.assertEqual((b.get("review_instances"), b.get("ai_batches")), (4, 4))
        self.assertGreater(b.get("admin_hours"), a.get("admin_hours"))

    def test_346_materiality_gate_and_b_preserves_original_board(self) -> None:
        with self.assertRaisesRegex(model.ModelRed, "ordinary fluctuations"):
            model.GovernanceLedger().apply(346, 1, identity(), materiality=49, signal_id="minor", action="reward")
        base = dict(materiality=50, signal_id="major", official_id="manager", signal_type="achievement", evidence_ids=("e-1",), recorded_day=100, original_board_version="board-19", action="reward")
        a = model.GovernanceLedger().apply(346, 1, identity(), **base).business
        b = model.GovernanceLedger().apply(346, 2, identity(case=8), **base).business
        self.assertEqual(a.get("cohort_reruns"), 0)
        self.assertEqual(b.get("cohort_reruns"), 1)
        self.assertTrue(b.get("original_board_preserved"))

    def test_347_budget_neutrality_and_uncapped_audit(self) -> None:
        with self.assertRaisesRegex(model.ModelRed, "budget exhausted"):
            model.GovernanceLedger().apply(347, 1, identity(), algorithmic_order=("a", "b", "c", "d"), operations=(("a", "b", "r1"), ("c", "d", "r2"), ("a", "c", "r3")))
        b = model.GovernanceLedger().apply(347, 2, identity(), algorithmic_order=("a", "b", "c", "d"), operations=(("a", "b", "r1"), ("c", "d", "r2"), ("a", "c", "r3"))).business
        self.assertCountEqual(b.get("algorithmic_order"), b.get("final_order"))
        self.assertEqual(len(b.get("audit")), 3)
        self.assertTrue(b.get("uncapped"))

    def test_offcycle_override_and_fairness_inputs_have_typed_one_shot_receipts(self) -> None:
        source = identity(cycle=20, case=900)
        pending_inputs = (
            model.OffcyclePendingInput(
                source,
                2,
                "signal-team-19",
                "achievement",
                75,
                ("appeal-case-7", "pip-case-4"),
            ),
            model.OverridePendingInput(
                source,
                3,
                "beneficiary",
                "bearer",
                2,
                3,
                701,
                702,
            ),
            model.FairnessPendingInput(
                source,
                4,
                delivered=10,
                appeals=4,
                overturns=2,
                exits=3,
                healthy_exits=1,
            ),
        )
        ledger = model.GovernanceLedger()
        for index, pending in enumerate(pending_inputs):
            with self.subTest(kind=pending.kind):
                consumer_id = model.PENDING_INPUT_CONSUMERS[pending.kind]
                consumer = identity(cycle=21, case=consumer_id + index)
                self.assertTrue(ledger.publish_pending_input(pending))
                self.assertFalse(ledger.publish_pending_input(pending))
                with self.assertRaisesRegex(model.ModelRed, f"belongs to {consumer_id}"):
                    ledger.consume_pending_input(
                        pending,
                        consumer_mechanism_id=999,
                        consumer_identity=consumer,
                    )
                receipt = ledger.consume_pending_input(
                    pending,
                    consumer_mechanism_id=consumer_id,
                    consumer_identity=consumer,
                )
                self.assertEqual(receipt.kind, pending.kind)
                self.assertEqual(receipt.input_revision, pending.input_revision)
                self.assertEqual(receipt.source_identity, source)
                self.assertNotIn(ledger._pending_input_key(pending), ledger.pending_inputs)
                self.assertIsNone(
                    ledger.consume_pending_input(
                        pending,
                        consumer_mechanism_id=consumer_id,
                        consumer_identity=consumer,
                    )
                )
                self.assertFalse(ledger.publish_pending_input(pending))
                with self.assertRaisesRegex(model.ModelRed, "cannot be settled twice"):
                    ledger.consume_pending_input(
                        pending,
                        consumer_mechanism_id=consumer_id,
                        consumer_identity=identity(cycle=22, case=consumer_id + index + 100),
                    )

        with self.assertRaisesRegex(model.ModelRed, "actual lift/rescue result reason"):
            model.OverridePendingInput(source, 5, "beneficiary", "bearer", 99, 3, 701, 702)
        with self.assertRaisesRegex(model.ModelRed, "actual push result reason"):
            model.OverridePendingInput(source, 5, "beneficiary", "bearer", 2, 99, 701, 702)

    def test_manager_runtime_model_has_no_dead_regrade_or_m016_reads(self) -> None:
        source = Path(model.__file__).read_text(encoding="utf-8-sig")
        self.assertNotIn("zg361_result_regrade_delta", source)
        self.assertNotIn("zg361_b2_m016_outcome", source)

    def test_348_expiry_and_grandfather_are_distinct(self) -> None:
        a = model.GovernanceLedger().apply(348, 1, identity(), exception_id="ex", granted_day=100, resolved_day=465, new_evidence=False, jingcha_batch_id="jc").business
        b = model.GovernanceLedger().apply(348, 2, identity(case=8), exception_id="ex").business
        self.assertTrue(a.get("default_restored"))
        self.assertIsNotNone(a.get("expiry_day"))
        self.assertTrue(b.get("grandfathered"))
        self.assertIsNone(b.get("expiry_day"))

    def test_349_seed_is_reproducible_and_capacity_atomic(self) -> None:
        facts = dict(risks={f"case-{index}": index * 5 for index in range(20)}, seed=71, transparency=5, capacity=100)
        first = model.GovernanceLedger().apply(349, 1, identity(), **facts).business
        second = model.GovernanceLedger().apply(349, 1, identity(case=8), **facts).business
        self.assertEqual(first.get("sample"), second.get("sample"))
        self.assertEqual(first.get("capacity_remaining") + first.get("hours"), 100)
        with self.assertRaisesRegex(model.ModelRed, "audit hours unavailable"):
            model.GovernanceLedger().apply(349, 1, identity(), **dict(facts, capacity=0))

    def test_350_history_is_immutable_in_both_routes(self) -> None:
        history = ({"kpi": 80, "rating": 3}, {"kpi": 80, "rating": 2}, {"kpi": 80, "rating": 1})
        a = model.GovernanceLedger().apply(350, 1, identity(), old_version="v1", new_version="v2", history=history, old_threshold=70, strategy_difficulty=5).business
        b = model.GovernanceLedger().apply(350, 2, identity(case=8), old_version="v1", new_version="v2", history=history, old_threshold=70, top_growth=8).business
        self.assertFalse(a.get("history_rewritten"))
        self.assertFalse(b.get("history_rewritten"))
        self.assertGreater(b.get("ratchet_risk"), 0)

    def test_351_a_requires_disjoint_complete_pilot_b_is_full_realm(self) -> None:
        outcomes = {"p1": {"m": 80}, "p2": {"m": 90}, "c1": {"m": 60}, "c2": {"m": 70}}
        a = model.GovernanceLedger().apply(351, 1, identity(), metrics=("m",), outcomes=outcomes, pilots=("p1", "p2"), controls=("c1", "c2"), end_cycle=21).business
        b = model.GovernanceLedger().apply(351, 2, identity(case=8), metrics=("m",), outcomes=outcomes, regions=tuple(outcomes), end_cycle=21).business
        self.assertTrue(a.get("causal_comparison"))
        self.assertFalse(b.get("causal_comparison"))
        with self.assertRaisesRegex(model.ModelRed, "disjoint"):
            model.GovernanceLedger().apply(351, 1, identity(), metrics=("m",), outcomes=outcomes, pilots=("p1", "p2"), controls=("p2", "c2"), end_cycle=21)

    def test_352_b_exposes_contamination_but_preserves_original_archive(self) -> None:
        records = ({"record_id": "r1", "original_value": 3, "original_formula": "old", "original_policy_version": "v1"},)
        b = model.GovernanceLedger().apply(352, 2, identity(), records=records, mapping_version="m2", factor=100).business
        self.assertTrue(b.get("original_archive_preserved"))
        self.assertTrue(b.get("contamination_risk"))
        self.assertEqual(b.get("consumer_refs"), ("appeal", "promotion", "decade-report"))

    def test_353_b_hidden_hours_are_still_audited_and_consumed(self) -> None:
        facts = dict(form_hours=10, meeting_hours=5, appeal_hours=4, calibration_hours=3, interruption_hours=2, available_hours=100, error_rate=2, overturn_rate=1)
        a = model.GovernanceLedger().apply(353, 1, identity(), **facts, simplified=("duplicate-form",)).business
        b = model.GovernanceLedger().apply(353, 2, identity(case=8), **facts).business
        self.assertEqual(a.get("actual_total"), 24)
        self.assertEqual(b.get("reported_total"), 0)
        self.assertEqual(b.get("hidden_capacity_loss"), 24)
        self.assertEqual(b.get("capacity_remaining"), 76)

    def test_354_raw_audit_detects_b_suppression_and_gates_trust(self) -> None:
        facts = dict(delivered=10, appeals=4, overturns=2, exits=4, healthy_exits=1, reported=(0.2, 0.25, 0.5))
        a = model.GovernanceLedger().apply(354, 1, identity(), **facts).business
        b = model.GovernanceLedger().apply(354, 2, identity(case=8), **facts).business
        self.assertTrue(a.get("gaming"))
        self.assertTrue(a.get("suppression_flag"))
        self.assertTrue(a.get("reclassification_flag"))
        self.assertEqual(a.get("long_term_trust_delta"), 0)
        self.assertEqual(a.get("raw_counts"), (("appeals", 4), ("delivered", 10), ("exits", 4), ("healthy_exits", 1), ("overturns", 2)))
        self.assertTrue(b.get("gaming"))
        self.assertTrue(b.get("suppression_flag"))
        self.assertTrue(b.get("reclassification_flag"))
        self.assertEqual(b.get("long_term_trust_delta"), 0)

        zero = model.GovernanceLedger().apply(
            354,
            1,
            identity(case=9),
            delivered=0,
            appeals=0,
            overturns=0,
            exits=0,
            healthy_exits=0,
        ).business
        self.assertEqual(zero.get("raw"), (0.0, 0.0, 0.0))

    def test_q_projection_requires_authoritative_consumed_receipt_and_is_idempotent(self) -> None:
        ledger = model.GovernanceLedger()
        receipt = model.ManagerCertificationReceipt(
            121,
            "emperor",
            "manager",
            20,
            8,
            1,
            2,
            model.Choice.A,
            True,
            1,
            {
                "trial_team_size": 3,
                "mentor_id": "mentor",
                "skip_reviewer_id": "skip",
                "due_cycle": 21,
                "outcome": "passed",
            },
            q_object(121, model.Choice.A, case=8, revision=2),
        )
        self.assertTrue(ledger.project_manager_certification(receipt))
        self.assertFalse(ledger.project_manager_certification(receipt))
        key = (121, "emperor", "manager", 20, 8, 1)
        self.assertIn(("source", "career-hc-authoritative"), ledger.q_projections[key])
        with self.assertRaisesRegex(model.ModelRed, "stale:projection"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    121,
                    "emperor",
                    "manager",
                    20,
                    8,
                    1,
                    3,
                    model.Choice.A,
                    True,
                    1,
                    {
                        "trial_team_size": 3,
                        "mentor_id": "different-mentor",
                        "skip_reviewer_id": "skip",
                        "due_cycle": 21,
                        "outcome": "passed",
                    },
                    q_object(121, model.Choice.A, case=8, revision=3),
                )
            )
        with self.assertRaisesRegex(model.ModelRed, "settle first"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    122,
                    "emperor",
                    "manager",
                    20,
                    8,
                    1,
                    2,
                    model.Choice.A,
                    False,
                    1,
                    {
                        "result_score": 70,
                        "talent_score": 60,
                        "process_score": 50,
                        "weights": (40, 30, 30),
                        "final_score": 61,
                    },
                )
            )
        with self.assertRaisesRegex(model.ModelRed, "value must match"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    123,
                    "emperor",
                    "manager",
                    20,
                    9,
                    2,
                    1,
                    model.Choice.B,
                    True,
                    999,
                    {
                        "sample_count": 3,
                        "six_dimensions": (50,) * 6,
                        "credibility_total": 300,
                        "consensus": "mixed",
                    },
                )
            )
        with self.assertRaisesRegex(model.ModelRed, "projection schema"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    124,
                    "emperor",
                    "manager",
                    20,
                    10,
                    2,
                    1,
                    model.Choice.A,
                    True,
                    1,
                    {"garbage": True},
                )
            )
        with self.assertRaisesRegex(model.ModelRed, "career debt is due next cycle"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    128,
                    "emperor",
                    "manager",
                    20,
                    11,
                    4,
                    1,
                    model.Choice.C,
                    True,
                    0,
                    {"policy_debt_due": 99},
                )
            )

        successor = model.ManagerCertificationReceipt(
            121,
            "new-emperor",
            "manager",
            21,
            9,
            1,
            1,
            model.Choice.A,
            True,
            1,
            {
                "trial_team_size": 3,
                "mentor_id": "mentor-2",
                "skip_reviewer_id": "skip-2",
                "due_cycle": 22,
                "outcome": "passed",
            },
            q_object(121, model.Choice.A, owner="new-emperor", cycle=21, case=9),
        )
        self.assertTrue(ledger.project_manager_certification(successor))
        with self.assertRaisesRegex(model.ModelRed, "older career receipt"):
            ledger.project_manager_certification(receipt)
        with self.assertRaisesRegex(model.ModelRed, "same career case token cannot change owner"):
            ledger.project_manager_certification(
                model.ManagerCertificationReceipt(
                    121,
                    "usurper",
                    "manager",
                    21,
                    9,
                    1,
                    1,
                    model.Choice.A,
                    True,
                    1,
                    successor.fields,
                    q_object(121, model.Choice.A, owner="usurper", cycle=21, case=9),
                )
            )

        with self.assertRaisesRegex(model.ModelRed, "Career/HC object identity"):
            model.GovernanceLedger().project_manager_certification(
                model.ManagerCertificationReceipt(
                    122,
                    "emperor",
                    "manager",
                    20,
                    122,
                    1,
                    1,
                    model.Choice.A,
                    True,
                    1,
                    valid_q_fields(122),
                    q_object(122, model.Choice.A, owner="wrong-owner"),
                )
            )
        with self.assertRaisesRegex(model.ModelRed, "route C must not fabricate"):
            model.GovernanceLedger().project_manager_certification(
                model.ManagerCertificationReceipt(
                    128,
                    "emperor",
                    "manager",
                    20,
                    128,
                    4,
                    1,
                    model.Choice.C,
                    True,
                    0,
                    {"policy_debt_due": 21},
                    q_object(128, model.Choice.C),
                )
            )


if __name__ == "__main__":
    unittest.main()
