from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "ck3_autonomous_player" / "native_bridge"
HEADER = BRIDGE / "include" / "xar_bridge" / "zhongguo_projects_metrics_postcondition_v1.hpp"
SOURCE = BRIDGE / "src" / "zhongguo_projects_metrics_postcondition_v1.cpp"
SERIALIZER = BRIDGE / "src" / "zhongguo_projects_metrics_postcondition_v1_serializer.cpp"
MAILBOX = BRIDGE / "src" / "zhongguo_projects_metrics_postcondition_v1_mailbox.cpp"
SHARED_MAILBOX = BRIDGE / "src" / "main_thread_query_mailbox_v1.cpp"
SHARED_BRIDGE = BRIDGE / "src" / "bridge.cpp"
ABI = BRIDGE / "research" / "zhongguo_projects_metrics_postcondition_v1_abi.json"
SOURCE_CONTRACT = BRIDGE / "research" / "fixtures" / "zhongguo_projects_metrics_postcondition_v1_source_contract.json"
SCHEMA = ROOT / "ck3_autonomous_player" / "schemas" / "zhongguo-projects-metrics-postcondition-v1.schema.json"
NATIVE_DRIVER = ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "bridge" / "native_driver.py"
SERVICE = ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "bridge" / "service.py"
MCP_SERVER = ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "bridge" / "mcp_server.py"
GAME_ADAPTER = BRIDGE / "src" / "game_adapter.cpp"
CK3_ADAPTER = BRIDGE / "src" / "ck3_11906_adapter.cpp"
CP_GENERATOR = ROOT / "mod_zhongguo_style" / "tools" / "gen_361_credit_project_runtime.py"
P3_GENERATOR = ROOT / "mod_zhongguo_style" / "tools" / "gen_361_phase3_metrics_delivery_runtime.py"
CP_PRODUCT = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_credit_project_m026_effort_ledger_effects.txt"
)
P3_PRODUCTS = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_phase3_portfolio_lifecycle_effects.txt",
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_phase3_aa_m229_metric_dictionary_owner_effects.txt",
)


class ProjectsMetricsPostconditionContractTests(unittest.TestCase):
    def test_exact_build_public_surface_and_fixed_allowlist_are_frozen(self) -> None:
        contract = json.loads(ABI.read_text(encoding="utf-8"))
        header = HEADER.read_text(encoding="utf-8")
        self.assertEqual(contract["game_version"], "1.19.0.6")
        self.assertEqual(
            contract["executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertIn(contract["capability"], header)
        self.assertEqual(len(contract["allowlist"]), 24)
        for variable in contract["allowlist"]:
            self.assertIn(f'"{variable}"', header)
        request_block = re.search(
            r"struct ZhongguoProjectsMetricsPostconditionRequestV1 \{(?P<body>.*?)\};",
            header,
            re.DOTALL,
        )
        self.assertIsNotNone(request_block)
        body = request_block.group("body")
        for forbidden in contract["request"]["forbidden_inputs"]:
            self.assertNotIn(forbidden, body)

    def test_cp26_a_b_mint_real_receipt_id_and_revision_only(self) -> None:
        generator = CP_GENERATOR.read_text(encoding="utf-8")
        product = CP_PRODUCT.read_text(encoding="utf-8-sig")
        receipt_id_write = (
            "set_variable = { name = zg361_cp_m26_contribution_receipt_id "
            "value = var:zg361_cp_contribution_receipt_cursor }"
        )
        receipt_revision_write = (
            "set_variable = { name = zg361_cp_m26_contribution_receipt_revision "
            "value = var:zg361_case_e_revision }"
        )
        self.assertEqual(generator.count(receipt_id_write), 1)
        self.assertEqual(generator.count(receipt_revision_write), 1)
        self.assertEqual(product.count(receipt_id_write), 2)
        self.assertEqual(product.count(receipt_revision_write), 2)
        self.assertEqual(product.count("change_variable = { name = zg361_cp_contribution_receipt_cursor add = 1 }"), 2)

    def test_p3_freezes_and_m229_backlinks_exact_cp_receipt(self) -> None:
        generator = P3_GENERATOR.read_text(encoding="utf-8")
        product = "\n".join(
            path.read_text(encoding="utf-8-sig") for path in P3_PRODUCTS
        )
        frozen_id = (
            "set_variable = { name = zg361_p3_project_source_contribution_receipt_id "
            "value = var:zg361_cp_m26_contribution_receipt_id }"
        )
        frozen_revision = (
            "set_variable = { name = zg361_p3_project_source_contribution_receipt_revision "
            "value = var:zg361_cp_m26_contribution_receipt_revision }"
        )
        result_id = (
            "set_variable = { name = zg361_p3_m229_source_contribution_receipt_id "
            "value = var:zg361_p3_project_source_contribution_receipt_id }"
        )
        result_revision = (
            "set_variable = { name = zg361_p3_m229_source_contribution_receipt_revision "
            "value = var:zg361_p3_project_source_contribution_receipt_revision }"
        )
        self.assertEqual(generator.count(frozen_id), 1)
        self.assertEqual(generator.count(frozen_revision), 1)
        self.assertEqual(generator.count(result_id), 1)
        self.assertEqual(generator.count(result_revision), 1)
        self.assertEqual(product.count(frozen_id), 1)
        self.assertEqual(product.count(frozen_revision), 1)
        self.assertEqual(product.count(result_id), 2)
        self.assertEqual(product.count(result_revision), 2)

    def test_provider_requires_identity_receipt_and_same_frame_equality(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for token in (
            "same_project_case_identity",
            "receipt_lineage_ready",
            "result_operation_committed",
            "same_frame_ready",
            "state_changed",
            "kZhongguoProjectsMetricsPostconditionV1VariableAllowlist",
        ):
            self.assertIn(token, source)
        self.assertIn("first != second", source)
        self.assertNotIn("variable_name", HEADER.read_text(encoding="utf-8"))

    def test_schema_serializer_and_claim_boundary_match(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        serializer = SERIALIZER.read_text(encoding="utf-8")
        source_contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["capability"]["const"], source_contract["capability"])
        self.assertEqual(source_contract["readiness"], "static_and_fixture_ready_not_live")
        self.assertEqual(
            source_contract["mailbox_fixed_slot"],
            "permitted_executor_quattuorvigintary",
        )
        self.assertEqual(
            source_contract["shared_wiring"],
            "default_off_complete_not_advertised",
        )
        self.assertIn('\\"source_contribution_receipt_revision\\"', serializer)
        self.assertIn('\\"character_fallback_slot_rva\\"', serializer)

    def test_shared_slot_driver_service_and_mcp_wiring_are_complete_default_off(self) -> None:
        mailbox = MAILBOX.read_text(encoding="utf-8")
        shared_mailbox = SHARED_MAILBOX.read_text(encoding="utf-8")
        shared_bridge = SHARED_BRIDGE.read_text(encoding="utf-8")
        native_driver = NATIVE_DRIVER.read_text(encoding="utf-8")
        service = SERVICE.read_text(encoding="utf-8")
        mcp_server = MCP_SERVER.read_text(encoding="utf-8")
        game_adapter = GAME_ADAPTER.read_text(encoding="utf-8")
        ck3_adapter = CK3_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("ExecuteZhongguoProjectsMetricsMailboxQueryV1", mailbox)
        self.assertIn("permitted_executor_quattuorvigintary", shared_mailbox)
        self.assertIn("ExecuteZhongguoProjectsMetricsMailboxQueryV1", shared_bridge)
        self.assertIn("zhongguo_projects_metrics_query_sequence", shared_bridge)
        self.assertIn("_execute_zhongguo_projects_metrics_v1_query", native_driver)
        self.assertIn("query_zhongguo_projects_metrics_postcondition_v1", service)
        self.assertIn("ck3_query_zhongguo_projects_metrics_postcondition_v1", mcp_server)
        self.assertIn(
            "ParseZhongguoProjectsMetricsPostconditionV1Step(step)", game_adapter
        )
        self.assertIn(
            '"zhongguo_projects_metrics_v1_query_supported": (', native_driver
        )
        self.assertNotIn(
            "game.command.query-zhongguo-projects-metrics-postcondition-v1",
            ck3_adapter,
        )


if __name__ == "__main__":
    unittest.main()
