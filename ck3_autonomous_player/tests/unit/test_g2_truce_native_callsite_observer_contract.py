from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class G2TruceNativeCallsiteObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (
                NATIVE / "research/g2_truce_native_callsite_observer_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (
                NATIVE
                / "research/fixtures/g2_truce_native_callsite_observer_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.header = (
            NATIVE
            / "include/xar_bridge/g2_truce_native_callsite_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        cls.source = (
            NATIVE / "src/g2_truce_native_callsite_observer_v1.cpp"
        ).read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_scope_is_private_read_only_and_default_off(self) -> None:
        scope = self.contract["scope"]
        self.assertTrue(scope["private_build_only"])
        self.assertTrue(scope["read_only_game_state"])
        self.assertFalse(scope["installed_by_default"])
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["default_heartbeat_schema_changed"])
        self.assertFalse(scope["public_readiness_changed"])
        self.assertFalse(scope["ck3_started"])

    def test_two_exact_native_callsites_are_frozen(self) -> None:
        calls = self.contract["call_sites"]
        self.assertEqual(
            [row["call_instruction_rva"] for row in calls],
            ["0x2EDAF0F", "0x2EDB59E"],
        )
        self.assertEqual(
            [row["continue_rva"] for row in calls],
            ["0x2EDAF14", "0x2EDB5A3"],
        )
        for row in calls:
            anchor = bytes.fromhex(row["anchor_hex"])
            self.assertEqual(len(anchor), row["patch_bytes"])
            self.assertEqual(
                hashlib.sha256(anchor).hexdigest().upper(),
                row["anchor_sha256"],
            )
            self.assertEqual(row["operands"]["RCX"], "RSI+0x108 script_value")
            self.assertIn("effect_context", row["operands"]["RDX"])
            self.assertIn("loaded evaluation_context", row["operands"]["R8"])

    def test_observer_relocates_only_the_covered_native_call(self) -> None:
        semantics = self.contract["detour_semantics"]
        self.assertTrue(semantics["relocated_original_call"])
        self.assertFalse(semantics["autonomous_evaluator_request"])
        self.assertTrue(semantics["two_site_install_transaction"])
        self.assertTrue(semantics["rollback_restores_original_bytes"])
        self.assertFalse(semantics["context_effect_executed"])
        self.assertFalse(semantics["mutation_executed"])

    def test_source_contract_tokens(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.fixture["required_cmake_tokens"]:
            self.assertIn(token, self.cmake)
        option = "XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1"
        self.assertIn(option, self.cmake)
        self.assertIn(
            "xar_ck3_g2_truce_native_callsite_observer_v1_test", self.cmake
        )


if __name__ == "__main__":
    unittest.main()
