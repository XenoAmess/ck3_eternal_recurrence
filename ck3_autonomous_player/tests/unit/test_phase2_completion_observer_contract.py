from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2CompletionObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (NATIVE / "research/phase2_completion_observer_v1_abi.json").read_text(
                encoding="utf-8"
            )
        )
        cls.fixture = json.loads(
            (
                NATIVE
                / "research/fixtures/phase2_completion_observer_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.header = (
            NATIVE / "include/xar_bridge/phase2_completion_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        cls.source = (
            NATIVE / "src/phase2_completion_observer_v1.cpp"
        ).read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")

    def test_private_scope_does_not_promote_public_readiness(self) -> None:
        scope = self.contract["scope"]
        self.assertTrue(scope["read_only_game_state"])
        self.assertTrue(scope["installed_by_default"] is False)
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["default_heartbeat_schema_changed"])
        self.assertFalse(scope["readiness_promotion"])
        self.assertFalse(scope["ck3_started"])

    def test_exact_hook_and_seed_fields_are_frozen(self) -> None:
        hook = self.contract["exact_hook"]
        self.assertEqual(hook["patch_rva"], "0x3B9DEA7")
        self.assertEqual(hook["patch_bytes"], 15)
        self.assertEqual(hook["continue_rva"], "0x3B9DEB6")
        self.assertEqual(hook["retire_rva"], "0x3B9DF63")
        self.assertEqual(hook["selected_callback_slot2_target_rva"], "0x88B480")
        fields = self.contract["private_telemetry"]["seed_gate_fields"]
        self.assertIn("last_thread_id", fields)
        self.assertIn("last_timestamp_qpc", fields)
        self.assertIn("last_observed_retired", fields)
        self.assertIn("last_will_retire", fields)

    def test_source_contract_tokens(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.fixture["forbidden_default_tokens"]:
            self.assertNotIn(token, self.bridge)


if __name__ == "__main__":
    unittest.main()
