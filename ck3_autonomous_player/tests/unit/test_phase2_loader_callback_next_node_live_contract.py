from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_next_node_live_v1_abi.json"
)


class Phase2LoaderCallbackNextNodeLiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_live_result_is_private_and_does_not_promote_readiness(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "private-vector-exhaustion-observed")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertEqual(
            contract["conclusion"]["readiness"],
            "native-readiness RED + not-live",
        )

    def test_last_returned_callback_has_exact_vector_exhaustion(self) -> None:
        capture = self.contract["capture"]
        self.assertEqual(capture["result"], "GREEN")
        self.assertEqual(
            capture["reason"], "last-returned-callback-vector-exhausted"
        )
        self.assertEqual(capture["callback_entry_count"], 2)
        self.assertEqual(capture["last_successful_callback_sequence"], 2)
        last = capture["last_returned_callback_transition"]
        self.assertEqual(last["callback_sequence"], 2)
        self.assertEqual(last["outcome"], "vector-exhausted")
        self.assertFalse(last["next_node_observed"])
        self.assertIsNone(last["next_node"])
        self.assertIsNone(last["next_node_name"])
        self.assertIsNone(last["next_receiver"])
        self.assertIsNone(last["next_receiver_is_null"])
        self.assertTrue(
            all(
                entry["returned"]
                and entry["next_transition"]["outcome"] == "vector-exhausted"
                and entry["next_transition"]["same_thread"]
                for entry in capture["entries"]
            )
        )

    def test_cleanup_and_next_boundary_are_explicit(self) -> None:
        cleanup = self.contract["cleanup"]
        self.assertEqual(cleanup["result"], "GREEN")
        self.assertTrue(cleanup["callback_breakpoint_byte_restored"])
        self.assertTrue(cleanup["continuation_breakpoint_byte_restored"])
        self.assertTrue(cleanup["node_loaded_breakpoint_byte_restored"])
        self.assertTrue(cleanup["loop_exit_breakpoint_byte_restored"])
        self.assertTrue(cleanup["process_terminated"])
        self.assertFalse(cleanup["real_user_profile_targeted"])
        self.assertEqual(cleanup["post_capture_ck3_process_count"], 0)
        self.assertEqual(cleanup["post_capture_probe_process_count"], 0)
        next_entry = self.contract["next_entry"]
        self.assertFalse(next_entry["authorized_in_this_package"])
        self.assertEqual(len(next_entry["candidate_continuations"]), 8)
        self.assertIn("RVA 0x3B9ACE0", next_entry["required"])


if __name__ == "__main__":
    unittest.main()
