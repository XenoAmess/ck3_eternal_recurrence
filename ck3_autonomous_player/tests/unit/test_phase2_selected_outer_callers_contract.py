from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "native_bridge/research/phase2_selected_outer_callers_v1_abi.json"
EXTRACTOR_PATH = ROOT / "native_bridge/research/extract_phase2_selected_outer_callers.py"


class Phase2SelectedOuterCallersContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.extractor = EXTRACTOR_PATH.read_text(encoding="utf-8")

    def test_unique_indirect_owner_is_exact_build_bound(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "static-indirect-owner-bound")
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["readiness_promotion"])
        evidence = contract["evidence"]
        self.assertFalse(evidence["ck3_started"])
        self.assertEqual(evidence["direct_relative_caller_count"], 0)
        self.assertEqual(evidence["static_continuation_count"], 0)
        self.assertEqual(evidence["absolute_function_pointer_ref_count"], 1)
        owner = evidence["indirect_owner"]
        self.assertEqual(owner["vtable_rva"], "0x408DBF0")
        self.assertEqual(owner["slot_index"], 2)
        self.assertEqual(owner["slot_target_rva"], "0x88B480")
        self.assertEqual(owner["construction_reference_rvas"], ["0x82193B", "0x88B650"])

    def test_next_stop_reads_runtime_continuation_without_guessing(self) -> None:
        conclusion = self.contract["conclusion"]
        self.assertEqual(conclusion["next_distinct_stop_point_rva"], "0x88B648")
        self.assertEqual(conclusion["next_read"], "[RSP] exact runtime continuation before RET")
        self.assertFalse(self.contract["next_entry"]["authorized_in_this_static_package"])
        self.assertIn("FUNCTION_RVA = 0x88B480", self.extractor)
        self.assertIn("NORMAL_RETURN_RVA = 0x88B648", self.extractor)
        self.assertEqual(self.contract["readiness"], "native-readiness RED + not-live")


if __name__ == "__main__":
    unittest.main()
