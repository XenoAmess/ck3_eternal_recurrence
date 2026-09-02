from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT / "native_bridge/research/phase2_selected_outer_return_live_v1_abi.json"
)
SOURCE_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_debug_capture.cpp"
)


class Phase2SelectedOuterReturnLiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")

    def test_private_live_does_not_promote_readiness(self) -> None:
        contract = self.contract
        self.assertEqual(
            contract["status"], "private-selected-outer-continuation-mapped"
        )
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertEqual(
            contract["readiness"],
            "native-readiness RED + private-live evidence only",
        )

    def test_ordered_boundary_maps_exact_outer_continuation(self) -> None:
        capture = self.contract["capture"]
        self.assertEqual(capture["result"], "GREEN")
        self.assertEqual(
            capture["reason"], "selected-outer-caller-continuation-mapped"
        )
        self.assertEqual(capture["last_successful_callback_sequence"], 2)
        self.assertEqual(capture["last_transition"], "vector-exhausted")
        self.assertEqual(capture["inner_continuation_rva"], "0x88B5E1")
        self.assertEqual(capture["selected_outer_return_rva"], "0x88B648")
        self.assertEqual(
            capture["selected_outer_continuation_rva"], "0x3B9CFD2"
        )
        self.assertTrue(capture["same_thread"])
        self.assertTrue(capture["continuation_in_image"])

    def test_cleanup_and_next_static_stop_are_explicit(self) -> None:
        cleanup = self.contract["cleanup"]
        self.assertEqual(cleanup["result"], "GREEN")
        self.assertTrue(cleanup["selected_outer_return_breakpoint_byte_restored"])
        self.assertTrue(cleanup["process_terminated"])
        self.assertEqual(cleanup["post_capture_ck3_process_count"], 0)
        self.assertEqual(cleanup["post_capture_probe_process_count"], 0)
        stop = self.contract["next_distinct_stop_point"]
        self.assertEqual(stop["rva"], "0x3B9CFD2")
        self.assertFalse(stop["authorized_in_this_package"])

    def test_probe_has_bounded_selected_outer_mode(self) -> None:
        self.assertIn("--selected-outer-caller", self.source)
        self.assertIn("kSelectedOuterReturnRva = 0x88B648", self.source)
        self.assertIn("selected-outer-caller-continuation-mapped", self.source)


if __name__ == "__main__":
    unittest.main()
