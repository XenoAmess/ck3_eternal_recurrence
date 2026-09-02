from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
RESEARCH = NATIVE / "research"


class Phase2ProducerConsumerCorrelationObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = json.loads((RESEARCH / "phase2_producer_consumer_correlation_observer_v1_abi.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((RESEARCH / "fixtures/phase2_producer_consumer_correlation_observer_v1_source_contract.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((RESEARCH / "phase2_producer_consumer_correlation_observer_v1_report.schema.json").read_text(encoding="utf-8"))
        cls.header = (NATIVE / "include/xar_bridge/phase2_completion_observer_v1.hpp").read_text(encoding="utf-8")
        cls.source = (NATIVE / "src/phase2_completion_observer_v1.cpp").read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_exact_seams_and_private_boundary(self) -> None:
        self.assertFalse(self.abi["scope"]["installed_by_default"])
        self.assertFalse(self.abi["scope"]["public_abi_changed"])
        self.assertFalse(self.abi["scope"]["readiness_changed"])
        self.assertEqual(self.abi["exact_seams"]["producer"]["post_publish_rva"], "0x3B9CFD7")
        self.assertEqual(self.abi["exact_seams"]["consumer"]["patch_rva"], "0x3B9DEA7")
        self.assertEqual(self.abi["exact_seams"]["producer"]["selected_callback_slot2_rva"], "0x88B480")

    def test_source_tokens_and_report_schema(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.fixture["required_cmake_tokens"]:
            self.assertIn(token, self.cmake)
        self.assertEqual(set(self.fixture["required_report_fields"]), set(self.schema["required"]))
        self.assertEqual(self.schema["properties"]["private_build"]["const"], True)

    def test_dynamic_identity_is_not_old_callback_selector(self) -> None:
        self.assertIn("correlation_source->load(std::memory_order_acquire) == task", self.source)
        self.assertIn("kPhase2SelectedCallbackTargetRvaV1", self.source)
        self.assertIn("telemetry_call_only_on_complete_values", self.abi["exact_seams"]["consumer"])
        self.assertIn("state 0 or 1", " ".join(self.abi["limits"]))


if __name__ == "__main__":
    unittest.main()
