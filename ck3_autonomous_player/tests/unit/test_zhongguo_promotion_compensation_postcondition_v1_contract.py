from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "ck3_autonomous_player" / "native_bridge"
HEADER = BRIDGE / "include" / "xar_bridge" / "zhongguo_promotion_compensation_postcondition_v1.hpp"
SOURCE = BRIDGE / "src" / "zhongguo_promotion_compensation_postcondition_v1.cpp"
MAILBOX = (
    BRIDGE / "src" / "zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp"
)
SHARED_MAILBOX = BRIDGE / "src" / "main_thread_query_mailbox_v1.cpp"
SHARED_BRIDGE = BRIDGE / "src" / "bridge.cpp"
GAME_ADAPTER = BRIDGE / "src" / "game_adapter.cpp"
CK3_ADAPTER = BRIDGE / "src" / "ck3_11906_adapter.cpp"
CMAKE = BRIDGE / "CMakeLists.txt"
NATIVE_DRIVER = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
SERVICE = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"
MCP_SERVER = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
SCHEMA = (
    ROOT
    / "ck3_autonomous_player/schemas/"
    "zhongguo-promotion-compensation-postcondition-v1.schema.json"
)
CONTRACT = BRIDGE / "research" / "zhongguo_promotion_compensation_postcondition_v1_abi.json"
SOURCE_CONTRACT = (
    BRIDGE
    / "research/fixtures/"
    "zhongguo_promotion_compensation_postcondition_v1_source_contract.json"
)
EFFECTS_DIR = ROOT / "mod_zhongguo_style" / "common" / "scripted_effects"


def feedback_product() -> str:
    paths = sorted(
        EFFECTS_DIR.glob("zg361_feedback_promotion_pip_[0-9][0-9][0-9]_*_effects.txt")
    )
    if not paths:
        raise AssertionError("missing generated feedback/promotion/PIP effect shards")
    return "\n\n".join(path.read_text(encoding="utf-8-sig") for path in paths)


def compensation_product() -> str:
    paths = sorted(EFFECTS_DIR.glob("zg361_compensation_*_effects.txt"))
    if not paths:
        raise AssertionError("missing generated compensation effect shards")
    return "\n\n".join(path.read_text(encoding="utf-8-sig") for path in paths)


class PromotionCompensationProviderContractTests(unittest.TestCase):
    def test_exact_build_and_public_surface_are_frozen(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        header = HEADER.read_text(encoding="utf-8")
        self.assertEqual(contract["game_version"], "1.19.0.6")
        self.assertEqual(
            contract["executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertIn(contract["capability"], header)
        self.assertEqual(
            contract["request"]["public_inputs"],
            ["request_nonce", "expected_revision"],
        )
        for forbidden in contract["request"]["forbidden_inputs"]:
            self.assertNotIn(forbidden, {"request_nonce", "expected_revision"})

    def test_choice_receipt_and_revision_are_real_product_fields(self) -> None:
        product = feedback_product()
        for key in (
            "zg361_pp_m147_receipt_active",
            "zg361_pp_m147_consumed",
            "zg361_pp_m147_receipt_owner",
            "zg361_pp_m147_receipt_subject",
            "zg361_pp_m147_receipt_cycle",
            "zg361_pp_m147_receipt_case",
            "zg361_pp_m147_receipt_route",
            "zg361_pp_m147_consumer_revision",
            "zg361_pp_m147_receipt_serial",
            "zg361_pp_m147_receipt_revision",
        ):
            self.assertIn(key, product)
        self.assertIn(
            "name = zg361_pp_m147_consumer_revision value = var:zg361_case_t_revision",
            product,
        )
        self.assertIn(
            "name = zg361_pp_m147_receipt_serial value = var:zg361_pp_t_result_case",
            product,
        )

    def test_all_compensation_receipts_have_identity_and_visible_revision(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        product = compensation_product()
        for mechanism in contract["compensation_receipt_selector"]["mechanism_allowlist"]:
            prefix = f"zg361_comp_m{mechanism:03d}_"
            for suffix in contract["compensation_receipt_selector"]["fixed_suffixes"]:
                self.assertIn(prefix + suffix, product)
        assignments = re.findall(
            r"set_variable = \{ name = zg361_comp_m\d{3}_visible_revision "
            r"value = var:zg361_case_(?:l|ae|af)_revision \}",
            product,
        )
        self.assertEqual(len(assignments), 33)

        for key in (
            "zg361_comp_promotion_receipt_owner",
            "zg361_comp_promotion_receipt_subject",
            "zg361_comp_promotion_receipt_cycle",
            "zg361_comp_promotion_receipt_case",
            "zg361_comp_promotion_receipt_choice_serial",
            "zg361_comp_promotion_receipt_serial",
            "zg361_comp_promotion_receipt_choice_revision",
            "zg361_comp_promotion_receipt_revision",
            "zg361_comp_promotion_receipt_posted",
        ):
            self.assertIn(key, product)

    def test_provider_is_closed_and_requires_correlated_serials(self) -> None:
        header = HEADER.read_text(encoding="utf-8")
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("kZhongguoPromotionCompensationMechanismAllowlist", header)
        self.assertIn("IsMechanismAllowlisted", source)
        self.assertNotIn("product_receipt_serial_not_persisted", source)
        self.assertIn("ready.receipt_serials_ready =", source)
        self.assertIn("posted_choice_serial_value", source)
        self.assertNotRegex(
            header,
            r"ZhongguoPromotionCompensationRequestV1\s*\{[^}]*"
            r"(subject_character_id|owner_character_id|variable_name|mechanism_id)",
        )

    def test_source_contract_and_typed_schema_are_frozen(self) -> None:
        abi = json.loads(CONTRACT.read_text(encoding="utf-8"))
        source_contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(source_contract["capability"], abi["capability"])
        self.assertEqual(
            source_contract["readiness"],
            "static_and_fixture_ready_live_pending",
        )
        self.assertEqual(
            source_contract["public_inputs"],
            ["request_nonce", "expected_revision"],
        )
        self.assertFalse(source_contract["caller_selected_variable_names"])
        self.assertFalse(source_contract["caller_selected_characters"])
        self.assertEqual(source_contract["source_choice"]["mechanism_id"], 147)
        self.assertEqual(
            source_contract["wired_layers"],
            [
                "reader",
                "serializer",
                "schema",
                "mailbox",
                "bridge",
                "native_driver",
                "service",
                "mcp",
            ],
        )
        self.assertEqual(
            source_contract["shared_wiring"],
            "default_off_complete_not_advertised",
        )
        self.assertEqual(
            source_contract["private_candidate_switch"],
            "XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1",
        )
        self.assertEqual(
            source_contract["allowlists"]["mechanism_ids"],
            abi["compensation_receipt_selector"]["mechanism_allowlist"],
        )
        self.assertFalse(source_contract["default_adapter_advertised"])
        self.assertFalse(source_contract["production_live_ready"])
        self.assertEqual(
            schema["properties"]["capability"]["const"], abi["capability"]
        )
        for typed_name in ("typed_integer", "typed_boolean"):
            branches = schema["$defs"][typed_name]["oneOf"]
            self.assertEqual(len(branches), 2)
            self.assertEqual(
                {branch["properties"]["status"]["const"] for branch in branches},
                {"available", "unavailable"},
            )

    def test_shared_provider_wiring_is_complete_and_default_off(self) -> None:
        mailbox = MAILBOX.read_text(encoding="utf-8")
        shared_mailbox = SHARED_MAILBOX.read_text(encoding="utf-8")
        shared_bridge = SHARED_BRIDGE.read_text(encoding="utf-8")
        game_adapter = GAME_ADAPTER.read_text(encoding="utf-8")
        ck3_adapter = CK3_ADAPTER.read_text(encoding="utf-8")
        cmake = CMAKE.read_text(encoding="utf-8")
        native_driver = NATIVE_DRIVER.read_text(encoding="utf-8")
        service = SERVICE.read_text(encoding="utf-8")
        mcp_server = MCP_SERVER.read_text(encoding="utf-8")
        self.assertIn(
            "ExecuteZhongguoPromotionCompensationMailboxQueryV1", mailbox
        )
        self.assertIn("permitted_executor_trivigintary", shared_mailbox)
        self.assertIn(
            "ExecuteZhongguoPromotionCompensationMailboxQueryV1", shared_bridge
        )
        self.assertIn(
            "zhongguo_promotion_compensation_query_sequence", shared_bridge
        )
        self.assertIn(
            "ParseZhongguoPromotionCompensationPostconditionV1Step(step)",
            game_adapter,
        )
        self.assertIn(
            "def _execute_zhongguo_promotion_compensation_v1_query(",
            native_driver,
        )
        self.assertIn(
            "def query_zhongguo_promotion_compensation_postcondition_v1(",
            service,
        )
        public_tool = re.search(
            r"def ck3_query_zhongguo_promotion_compensation_postcondition_v1\("
            r"(?P<body>.*?)\)\s*->",
            mcp_server,
            re.DOTALL,
        )
        self.assertIsNotNone(public_tool)
        self.assertIn("request_nonce", public_tool.group("body"))
        self.assertIn("expected_revision", public_tool.group("body"))
        for forbidden in ("owner_character_id", "subject_character_id", "variable_name"):
            self.assertNotIn(forbidden, public_tool.group("body"))
        switch = (
            "XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1"
        )
        option = re.search(
            rf"option\(\s*{switch}\s*.*?\s+OFF\s*\)", cmake, re.DOTALL
        )
        self.assertIsNotNone(option)
        guarded_blocks = list(
            re.finditer(
                rf"#if defined\({switch}\)(?P<body>.*?)#endif",
                ck3_adapter,
                re.DOTALL,
            )
        )
        self.assertGreaterEqual(len(guarded_blocks), 2)
        capability = (
            "ck3_11906::kZhongguoPromotionCompensationPostconditionV1Capability"
        )
        capability_blocks = [
            match
            for match in guarded_blocks
            if capability in match.group("body")
        ]
        self.assertEqual(len(capability_blocks), 1)
        guarded = capability_blocks[0]
        self.assertNotIn(
            capability,
            ck3_adapter[: guarded.start()] + ck3_adapter[guarded.end() :],
        )


if __name__ == "__main__":
    unittest.main()
