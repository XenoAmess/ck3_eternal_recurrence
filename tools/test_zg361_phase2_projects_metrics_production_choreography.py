#!/usr/bin/env python3
"""Static regression tests for the projects/metrics production choreography audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tools/zg361_phase2_projects_metrics_production_choreography_contract.json"
SEED = ROOT / "tools/zg361_phase2_seed_contract.json"
PUMP = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_010_serial_pump_effects.txt"
STAGES = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_007_stage07_09_effects.txt"
DISPATCH = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_003_dispatch_control_effects.txt"
CP_ORCHESTRATION = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_credit_project_e_orchestration_effects.txt"
CP_M26 = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_credit_project_m026_effort_ledger_effects.txt"
CP_EVENTS = ROOT / "mod_zhongguo_style/events/zg361_credit_project_runtime_events.txt"
P3_LIFECYCLE = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_phase3_portfolio_lifecycle_effects.txt"
P3_ORCHESTRATION = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_phase3_aa_orchestration_effects.txt"
PROVIDER_ABI = ROOT / "ck3_autonomous_player/native_bridge/research/zhongguo_projects_metrics_postcondition_v1_abi.json"
CAPTURE = ROOT / "tools/zg361_phase2_projects_metrics_source_checkpoint.py"
DOC = ROOT / "docs/phase2-promo/projects-metrics-production-choreography-1341251-2026-09-04.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(source: str, key: str) -> str:
    marker = f"{key} = {{"
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing block {key}")
    opening = source.find("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated block {key}")


class ProjectsMetricsProductionChoreographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(read(CONTRACT))
        cls.seed = json.loads(read(SEED))
        cls.pump = read(PUMP)
        cls.stages = read(STAGES)
        cls.dispatch = read(DISPATCH)
        cls.cp_orchestration = read(CP_ORCHESTRATION)
        cls.cp_m26 = read(CP_M26)
        cls.cp_events = read(CP_EVENTS)
        cls.p3_lifecycle = read(P3_LIFECYCLE)
        cls.p3_orchestration = read(P3_ORCHESTRATION)
        cls.provider_abi = json.loads(read(PROVIDER_ABI))
        cls.capture = read(CAPTURE)
        cls.product_scripts = "\n".join(
            read(path)
            for root in (
                ROOT / "mod_zhongguo_style/common",
                ROOT / "mod_zhongguo_style/events",
            )
            for path in root.rglob("*.txt")
        )

    def test_contract_is_bound_to_current_seed_and_is_honestly_blocked(self) -> None:
        self.assertEqual(self.contract["schema_version"], 1)
        self.assertEqual(
            self.contract["audited_commit"],
            "1341251dd028b68adf5a4adeb497c94acf3a9471",
        )
        self.assertFalse(self.contract["ck3_started"])
        self.assertFalse(self.contract["shared_runner_modified"])
        self.assertEqual(
            self.contract["seed"]["save_sha256"],
            self.seed["source"]["sha256"].upper(),
        )
        verdict = self.contract["reachability_verdict"]
        self.assertFalse(
            verdict["target_reachable_from_seed_on_current_healthy_production_graph"]
        )
        self.assertEqual(verdict["reason_code"], "cp_producer_runs_after_p3_consumer")
        self.assertFalse(verdict["source_checkpoint_capture_contract_satisfiable"])

    def test_central_dispatches_p3_stage_before_cp_stage(self) -> None:
        stage7_dispatch = "var:zg361_p2c_stage = 7 } zg361_p2c_stage_07_metrics_delivery_effect"
        stage8_dispatch = "var:zg361_p2c_stage = 8 } zg361_p2c_stage_08_credit_project_effect"
        self.assertIn(stage7_dispatch, self.pump)
        self.assertIn(stage8_dispatch, self.pump)
        self.assertLess(self.pump.index(stage7_dispatch), self.pump.index(stage8_dispatch))
        stage7 = block(self.stages, "zg361_p2c_stage_07_metrics_delivery_effect")
        stage8 = block(self.stages, "zg361_p2c_stage_08_credit_project_effect")
        self.assertIn("zg361_p3_open_portfolio_effect", stage7)
        self.assertIn("zg361_cp_open_portfolio_effect", stage8)
        self.assertIn("change_variable = { name = zg361_p2c_stage add = 1 }", self.dispatch)
        self.assertIn("zg361_p2c_schedule_pump_effect = { DAYS = 2 }", self.dispatch)

    def test_cp26_real_ui_and_a_b_receipt_edges(self) -> None:
        launch = block(self.cp_orchestration, "zg361_cp_e_launch_effect")
        self.assertIn("root = { is_ai = yes", launch)
        self.assertIn("zg361_cp_e_run_authorized_ai_effect", launch)
        self.assertIn("root = { is_ai = no", launch)
        self.assertIn("trigger_event = { id = zg361cp.30 }", launch)

        cp30 = block(self.cp_events, "zg361cp.30")
        cp26 = block(self.cp_events, "zg361cp.26")
        self.assertIn("is_ai = no", cp26)
        self.assertIn("this = scope:zg361_cp_e_owner", cp26)
        self.assertGreaterEqual(
            cp30.count("trigger_event = { id = zg361cp.26 days = 1 }"), 2
        )
        self.assertIn("zg361_cp_m26_route_a_effect", cp26)
        self.assertIn("zg361_cp_m26_route_b_effect", cp26)
        self.assertGreaterEqual(
            cp26.count("trigger_event = { id = zg361cp.27 days = 1 }"), 2
        )

        required_receipts = self.contract["audited_product_edges"]["credit_project"]["cp26_receipt_variables"]
        route_a = block(self.cp_m26, "zg361_cp_m26_route_a_effect")
        route_b = block(self.cp_m26, "zg361_cp_m26_route_b_effect")
        consume = block(self.cp_m26, "zg361_cp_m26_consume_effect")
        for token in required_receipts[:-1]:
            self.assertIn(token, route_a)
            self.assertIn(token, route_b)
        self.assertEqual(required_receipts[-1], "zg361_cp_m26_visible_value")
        self.assertIn(required_receipts[-1], consume)
        self.assertIn("zg361_cp_m26_consume_effect = yes", route_a)
        self.assertIn("zg361_cp_m26_consume_effect = yes", route_b)
        self.assertIn("zg361_cp_effort_ledger value = 1", route_a)
        self.assertIn("zg361_cp_effort_ledger value = 2", route_b)
        self.assertIn("CHOICE = 1", route_a)
        self.assertIn("CHOICE = 2", route_b)

    def test_p3_source_projection_can_only_be_created_by_initializer(self) -> None:
        initializer = block(self.p3_lifecycle, "zg361_p3_initialize_portfolio_effect")
        launch = block(self.p3_orchestration, "zg361_p3_aa_launch_effect")
        self.assertIn(
            "set_variable = { name = zg361_p3_project_source_ready value = 0 }",
            initializer,
        )
        self.assertIn("has_variable = zg361_cp_m26_contribution_receipt_id", initializer)
        self.assertIn(
            "var:zg361_cp_m26_receipt_cycle = root.var:zg361_review_serial",
            initializer,
        )
        self.assertIn(
            "set_variable = { name = zg361_p3_project_source_ready value = 1 }",
            initializer,
        )
        self.assertEqual(
            self.product_scripts.count(
                "name = zg361_p3_project_source_ready value = 0"
            ),
            1,
        )
        self.assertEqual(
            self.product_scripts.count(
                "name = zg361_p3_project_source_ready value = 1"
            ),
            1,
        )
        self.assertLess(
            launch.index("zg361_p3_initialize_portfolio_effect"),
            launch.index("zg361_p3_aa_run_authorized_ai_effect"),
        )

    def test_existing_provider_cannot_observe_pre_initializer_cp26(self) -> None:
        allowlist = self.provider_abi["allowlist"]
        self.assertTrue(allowlist)
        self.assertTrue(all(name.startswith("zg361_p3_") for name in allowlist))
        self.assertFalse(any(name.startswith("zg361_cp_") for name in allowlist))
        self.assertIn('"source_ready_result_pending"', self.capture)
        self.assertIn('"p3_initializer_not_run": True', self.capture)
        contradiction = self.contract["reachability_verdict"]["capture_contract_contradiction"]
        self.assertIn("source_ready=1", contradiction)
        self.assertIn("zg361_p3_initialize_portfolio_effect", contradiction)

    def test_document_records_the_no_launch_boundary_and_repair_entry(self) -> None:
        document = read(DOC)
        self.assertIn("结论：当前 production graph 不可达", document)
        self.assertIn("stage 7", document)
        self.assertIn("stage 8", document)
        self.assertIn("未启动 CK3", document)
        self.assertIn("未修改共享 runner", document)
        self.assertIn("CP 先于 P3", document)


if __name__ == "__main__":
    unittest.main()
