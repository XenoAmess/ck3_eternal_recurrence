from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2PostCallListIdentityObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (
                NATIVE
                / "research/phase2_post_call_list_identity_observer_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (
                NATIVE
                / "research/fixtures/phase2_post_call_list_identity_observer_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.header = (
            NATIVE
            / "include/xar_bridge/phase2_post_call_list_identity_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        cls.source = (
            NATIVE / "src/phase2_post_call_list_identity_observer_v1.cpp"
        ).read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_private_default_off_boundary(self) -> None:
        scope = self.contract["scope"]
        self.assertFalse(scope["installed_by_default"])
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["readiness_changed"])
        self.assertFalse(scope["ck3_started"])
        self.assertIn(
            "XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1",
            self.cmake,
        )

    def test_exact_anchor_and_capacities(self) -> None:
        hook = self.contract["exact_hook"]
        self.assertEqual(hook["patch_rva"], "0x3407DA1")
        self.assertEqual(hook["patch_bytes"], 14)
        self.assertEqual(hook["maximum_descriptors"], 4096)
        telemetry = self.contract["private_telemetry"]
        self.assertEqual(telemetry["sample_capacity"], 64)
        self.assertEqual(telemetry["histogram_capacity"], 64)
        self.assertTrue(telemetry["capacity_overflow_explicit"])

    def test_identity_and_histogram_mapping_are_frozen(self) -> None:
        telemetry = self.contract["private_telemetry"]
        self.assertEqual(
            telemetry["selected_target_rva"], "0x88B480"
        )
        self.assertIn("task", telemetry["sample_fields"])
        self.assertIn("owner", telemetry["sample_fields"])
        self.assertIn("callback_slot2_rva", telemetry["sample_fields"])
        self.assertIn("first_task", telemetry["histogram_fields"])
        self.assertIn("last_owner", telemetry["histogram_fields"])

    def test_source_contract_tokens(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.fixture["required_cmake_tokens"]:
            self.assertIn(token, self.cmake)


if __name__ == "__main__":
    unittest.main()
