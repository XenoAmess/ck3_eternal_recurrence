from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge/research"


class Phase2Slot2817C20IdentityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.live = json.loads(
            (RESEARCH / "phase2_post_call_list_identity_live_postprocess_v1_contract.json").read_text(encoding="utf-8")
        )
        cls.static = json.loads(
            (RESEARCH / "phase2_slot2_817c20_identity_v1_abi.json").read_text(encoding="utf-8")
        )

    def test_live_capture_is_complete_and_excludes_loader_callback(self) -> None:
        self.assertEqual(self.live["decision"], "complete-list-excludes-loader-callback")
        evidence = self.live["evidence"]
        self.assertEqual(evidence["list_count"], evidence["scan_count"])
        self.assertEqual(evidence["sample_count"], 27)
        self.assertFalse(evidence["loss_or_overflow"])
        self.assertEqual(evidence["loader_callback_0x88B480_count"], 0)
        self.assertEqual(evidence["slot2_rva_distribution"], [{"rva": "0x817C20", "count": 27}])

    def test_pdata_and_parallel_range_worker_layout_are_frozen(self) -> None:
        evidence = self.static["evidence"]
        self.assertEqual(evidence["function"]["entry_rva"], "0x817C20")
        self.assertEqual(evidence["function"]["end_rva_exclusive"], "0x817C9C")
        self.assertEqual(len(evidence["function"]["pdata_fragments"]), 3)
        self.assertEqual(evidence["function"]["pdata_fragments"][1][3], 4)
        cfg = evidence["bounded_cfg"]
        self.assertEqual(cfg["atomic_next_index_offset"], "0x0")
        self.assertEqual(cfg["total_bound_offset"], "0x14")
        self.assertEqual(cfg["batch_size_offset"], "0x1C")
        self.assertEqual(cfg["element_pointer_array_carrier_offset"], "0x28")

    def test_rtti_family_is_shared_and_owner_remains_bounded(self) -> None:
        rtti = self.static["evidence"]["rtti"]
        self.assertEqual(rtti["valid_vtable_count"], 278)
        self.assertIn("SPdxParallelForOverArray", rtti["common_owner_family"])
        conclusion = self.static["conclusion"]
        self.assertEqual(conclusion["task_domain"], "generic SPdxParallelForOverArray range-worker std::function callback")
        self.assertFalse(conclusion["current_list_is_loader_completion_list"])
        self.assertFalse(conclusion["unique_runtime_rtti_owner_resolved"])

    def test_next_seam_returns_to_true_completion_producer(self) -> None:
        conclusion = self.static["conclusion"]
        self.assertEqual(conclusion["next_distinct_primary_seam_rva"], "0x3B9CFD7")
        self.assertEqual(conclusion["preceding_task_identity_rva"], "0x3B9CFD2")
        self.assertIn("callback vptr/slot2", conclusion["next_capture"])
        self.assertFalse(self.static["production_abi_changed"])
        self.assertFalse(self.static["readiness_promotion"])
        self.assertFalse(self.static["evidence"]["ck3_started"])


if __name__ == "__main__":
    unittest.main()
