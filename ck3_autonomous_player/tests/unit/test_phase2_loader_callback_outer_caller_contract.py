from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_outer_caller_v1_abi.json"
)
EXTRACTOR_PATH = (
    ROOT / "native_bridge/research/extract_phase2_loader_callback_outer_callers.py"
)


class Phase2LoaderCallbackOuterCallerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.extractor = EXTRACTOR_PATH.read_text(encoding="utf-8")

    def test_static_package_is_explicit_no_go(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "static-caller-ambiguous-no-go")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertFalse(contract["evidence"]["ck3_started"])
        self.assertEqual(contract["selection"]["candidate_count_before"], 8)
        self.assertEqual(contract["selection"]["candidate_count_after"], 8)
        self.assertIsNone(contract["selection"]["selected_continuation_rva"])
        self.assertEqual(contract["selection"]["result"], "NO-GO")

    def test_all_exact_continuations_and_return_stop_are_frozen(self) -> None:
        evidence = self.contract["evidence"]
        self.assertEqual(evidence["normal_return_rva"], "0x3B9ACE0")
        self.assertEqual(evidence["normal_return_address_source"], "[RSP] before RET")
        self.assertEqual(evidence["direct_caller_count"], 8)
        self.assertEqual(evidence["distinct_pdata_owner_count"], 8)
        self.assertEqual(len(set(evidence["candidate_continuations"])), 8)
        self.assertEqual(evidence["continuation_shapes"]["callee_return_value_consumed"], 0)
        self.assertIn("NORMAL_RETURN_RVA = 0x3B9ACE0", self.extractor)
        self.assertIn("CALLERS = (", self.extractor)

    def test_next_live_entry_is_not_authorized_here(self) -> None:
        next_entry = self.contract["next_entry"]
        self.assertFalse(next_entry["authorized_in_this_package"])
        self.assertIn("reading [RSP]", next_entry["required"])
        self.assertEqual(self.contract["readiness"], "native-readiness RED + not-live")


if __name__ == "__main__":
    unittest.main()
