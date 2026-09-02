from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2WrapperEntryObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (
                NATIVE / "research/phase2_wrapper_entry_observer_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (
                NATIVE
                / "research/fixtures/phase2_wrapper_entry_observer_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.header = (
            NATIVE / "include/xar_bridge/phase2_wrapper_entry_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        cls.source = (
            NATIVE / "src/phase2_wrapper_entry_observer_v1.cpp"
        ).read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_private_scope_does_not_promote_public_readiness(self) -> None:
        scope = self.contract["scope"]
        self.assertTrue(scope["read_only_game_state"])
        self.assertFalse(scope["installed_by_default"])
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["default_heartbeat_schema_changed"])
        self.assertFalse(scope["readiness_promotion"])
        self.assertFalse(scope["ck3_started"])

    def test_exact_entry_and_stack_contract_are_frozen(self) -> None:
        hook = self.contract["exact_hook"]
        self.assertEqual(hook["patch_rva"], "0x3B9E030")
        self.assertEqual(hook["continue_rva"], "0x3B9E03F")
        self.assertEqual(hook["patch_bytes"], 15)
        self.assertEqual(hook["anchor_hex"], "48895C240848896C24184889742420")
        self.assertEqual(hook["entry_stack_contract"]["return_address"], "[RSP]")
        self.assertEqual(
            hook["entry_stack_contract"]["producer_list"],
            "[RSP+0x28] fifth argument",
        )

    def test_private_fields_are_minimal_and_complete(self) -> None:
        self.assertEqual(
            self.contract["private_telemetry"]["fields"],
            [
                "entry_count",
                "last_return_address",
                "last_callsite_rva",
                "last_scheduler_owner",
                "last_producer_list",
                "last_thread_id",
                "last_timestamp_qpc",
            ],
        )

    def test_source_contract_tokens(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        self.assertIn("XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1", self.cmake)
        self.assertIn("xar_ck3_phase2_wrapper_entry_observer_v1_test", self.cmake)


if __name__ == "__main__":
    unittest.main()
