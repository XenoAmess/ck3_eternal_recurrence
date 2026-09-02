from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "native_bridge/research/phase2_outer_completion_edge_v1_abi.json"


class Phase2OuterCompletionEdgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_package_is_static_private_and_read_only(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "static-post-init-edge-bound")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])

    def test_chained_owner_and_runtime_continuation_are_frozen(self) -> None:
        evidence = self.contract["evidence"]
        self.assertFalse(evidence["ck3_started"])
        self.assertEqual(evidence["runtime_continuation_rva"], "0x3B9CFD2")
        owner = evidence["logical_owner"]
        self.assertEqual(owner["entry_rva"], "0x3B9CF50")
        self.assertEqual(owner["end_rva_exclusive"], "0x3B9D04D")
        self.assertEqual(len(owner["chained_pdata"]), 3)
        self.assertEqual(owner["direct_relative_caller_count"], 1267)

    def test_post_init_state_publication_is_direct(self) -> None:
        cfg = self.contract["evidence"]["bounded_cfg"]
        self.assertEqual(cfg["callback_receiver"], "[RBX+0x38]")
        self.assertEqual(cfg["callback_dispatch_rva"], "0x3B9CFCF")
        self.assertEqual(cfg["completion_value_load_rva"], "0x3B9CFD2")
        self.assertEqual(cfg["completion_publish_rva"], "0x3B9CFD7")
        self.assertEqual(cfg["completion_value"], 2)
        self.assertEqual(cfg["state_offset"], "0x60")
        self.assertEqual(cfg["elapsed_time_offset"], "0x68")
        conclusion = self.contract["conclusion"]
        self.assertEqual(conclusion["edge_class"], "post-init callback completion")
        self.assertFalse(conclusion["additional_live_required"])


if __name__ == "__main__":
    unittest.main()
