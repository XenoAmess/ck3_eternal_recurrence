from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2PostCallObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (NATIVE / "research/phase2_post_call_observer_v1_abi.json").read_text(
                encoding="utf-8"
            )
        )
        cls.fixture = json.loads(
            (
                NATIVE
                / "research/fixtures/phase2_post_call_observer_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.header = (
            NATIVE / "include/xar_bridge/phase2_post_call_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        cls.source = (
            NATIVE / "src/phase2_post_call_observer_v1.cpp"
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

    def test_exact_hook_and_relocated_branch_are_frozen(self) -> None:
        hook = self.contract["exact_hook"]
        self.assertEqual(hook["patch_rva"], "0x3407DA1")
        self.assertEqual(hook["continue_rva"], "0x3407DAF")
        self.assertEqual(hook["null_target_rva"], "0x3407DBD")
        self.assertEqual(hook["patch_bytes"], 14)
        self.assertEqual(hook["anchor_hex"], "90488B4C24684885C97411488B01")
        self.assertIn("absolute", hook["replayed_semantics"])

    def test_list_and_selected_fields_are_private(self) -> None:
        hook = self.contract["exact_hook"]["frame_contract"]
        self.assertEqual(hook["producer_list"], "RBP+0xE0")
        self.assertEqual(hook["descriptor_task"], "[descriptor+0x18]")
        self.assertEqual(hook["descriptor_owner"], "[descriptor+0x20]")
        fields = self.contract["private_telemetry"]["fields"]
        for field in (
            "hit_count",
            "descriptor_seen_count",
            "selected_state2_count",
            "raw_last_callback_slot2_target",
            "last_producer_list",
            "last_owner",
            "last_state",
        ):
            self.assertIn(field, fields)

    def test_source_contract_tokens(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        self.assertIn("XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1", self.cmake)
        self.assertIn("xar_ck3_phase2_post_call_observer_v1_test", self.cmake)


if __name__ == "__main__":
    unittest.main()
