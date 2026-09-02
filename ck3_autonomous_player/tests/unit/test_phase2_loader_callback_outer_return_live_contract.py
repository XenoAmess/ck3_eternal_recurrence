from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_outer_return_live_v1_abi.json"
)


class Phase2LoaderCallbackOuterReturnLiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_mapping_is_private_and_does_not_promote_readiness(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "private-outer-caller-mapped")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertEqual(contract["readiness"], "native-readiness RED + not-live")

    def test_sequence_two_maps_to_one_frozen_continuation(self) -> None:
        capture = self.contract["capture"]
        self.assertEqual(capture["result"], "GREEN")
        self.assertEqual(capture["reason"], "seq2-outer-caller-continuation-mapped")
        mapping = capture["sequence_2_mapping"]
        self.assertEqual(mapping["selected_from_candidate_count"], 8)
        self.assertEqual(mapping["callsite_rva"], "0x88B5DC")
        self.assertEqual(mapping["continuation_rva"], "0x88B5E1")
        self.assertEqual(mapping["owner_function_rva"], "0x88B480")
        self.assertEqual(mapping["owner_function_end_rva_exclusive"], "0x88B649")
        self.assertTrue(
            all(
                row["vector_transition"] == "vector-exhausted"
                and row["same_thread"]
                and row["matches_frozen_candidate"]
                for row in capture["observations"]
            )
        )

    def test_cleanup_and_next_outer_stop_are_explicit(self) -> None:
        cleanup = self.contract["cleanup"]
        self.assertEqual(cleanup["result"], "GREEN")
        self.assertTrue(cleanup["normal_return_breakpoint_byte_restored"])
        self.assertTrue(cleanup["process_terminated"])
        self.assertEqual(cleanup["post_capture_ck3_process_count"], 0)
        self.assertEqual(cleanup["post_capture_probe_process_count"], 0)
        stop = self.contract["next_outer_stop_point"]
        self.assertEqual(stop["rva"], "0x88B5E1")
        self.assertEqual(stop["first_downstream_call_rva"], "0x88B5E9")
        self.assertEqual(stop["first_downstream_return_rva"], "0x88B5EE")
        self.assertEqual(stop["downstream_call_semantics"], "unknown")


if __name__ == "__main__":
    unittest.main()
