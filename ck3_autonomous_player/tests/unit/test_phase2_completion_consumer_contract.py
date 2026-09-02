from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "native_bridge/research/phase2_completion_consumer_v1_abi.json"


class Phase2CompletionConsumerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_is_static_and_does_not_promote_readiness(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "static-completion-consumer-bound")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertFalse(contract["evidence"]["ck3_started"])

    def test_completion_consumer_is_unique_in_bounded_slice(self) -> None:
        bounded = self.contract["evidence"]["bounded_slice"]
        self.assertEqual(
            bounded["completion_consumer_read_rvas"], ["0x3B9DEA7"]
        )
        self.assertEqual(len(bounded["state_zero_gate_read_rvas"]), 4)
        consumer = self.contract["evidence"]["consumer"]
        self.assertEqual(consumer["function_rva"], "0x3B9DD50")
        self.assertEqual(consumer["function_end_rva_exclusive"], "0x3B9E025")
        self.assertEqual(consumer["direct_call_rvas"], ["0x3B9E10B", "0x3B9E175"])
        self.assertEqual(consumer["complete_values"], [2, 3])
        self.assertEqual(consumer["retired_publish_rva"], "0x3B9DF7B")

    def test_minimum_read_only_wiring_is_explicit(self) -> None:
        entry = self.contract["observation_entry"]
        self.assertEqual(entry["rva"], "0x3B9DEA7")
        self.assertEqual(
            entry["selected_task_filter"],
            "callback slot 2 target RVA equals 0x88B480",
        )
        self.assertFalse(entry["mutation_required"])
        self.assertFalse(entry["public_schema_change_required"])
        self.assertFalse(entry["live_required_for_static_contract"])
        conclusion = self.contract["conclusion"]
        self.assertFalse(conclusion["explicit_os_wait_or_signal_found"])
        self.assertFalse(conclusion["next_live_required"])


if __name__ == "__main__":
    unittest.main()
