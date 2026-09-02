from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2RuntimeCaller3407D9CContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (
                NATIVE / "research/phase2_runtime_caller_3407d9c_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        cls.extractor = (
            NATIVE / "research/extract_phase2_runtime_caller_3407d9c.py"
        ).read_text(encoding="utf-8")

    def test_live_tuple_and_sampling_boundary_are_frozen(self) -> None:
        live = self.contract["live_evidence"]
        self.assertEqual(live["entry_count"], 1220)
        self.assertEqual(live["last_callsite_rva"], "0x3407D9C")
        self.assertEqual(live["last_scheduler_owner"], "0x22ED9921A00")
        self.assertEqual(live["last_producer_list"], "0xF282FFEE70")
        self.assertEqual(live["last_thread_id"], 44900)
        self.assertIn("last sampled", live["sampling_boundary"])

    def test_pdata_owner_and_call_arguments_are_bound(self) -> None:
        caller = self.contract["caller"]
        self.assertEqual(caller["function"], "[0x3407C70,0x3407F80)")
        self.assertEqual(caller["unwind_rva"], "0x4C3DD40")
        self.assertEqual(caller["wrapper_call_rva"], "0x3407D9C")
        arguments = self.contract["call_arguments"]
        self.assertIn("0x5772E98", arguments["rcx"])
        self.assertIn("[RBP+0xE0]", arguments["fifth"])
        self.assertEqual(
            arguments["producer_list_layout"]["descriptor_task_offset"],
            "0x18",
        )

    def test_post_return_lifetime_is_bounded(self) -> None:
        lifetime = self.contract["post_return_lifetime"]
        self.assertEqual(lifetime["continuation"], "0x3407DA1")
        self.assertIn("0x3B67B80", lifetime["producer_to_destination_empty_path"])
        self.assertIn("0x3B67DE0", lifetime["producer_to_destination_nonempty_path"])
        self.assertEqual(lifetime["normal_function_return"], "0x3407F7F")

    def test_next_observer_is_exact_private_post_return_seam(self) -> None:
        seam = self.contract["next_distinct_observer"]
        self.assertEqual(seam["patch_rva"], "0x3407DA1")
        self.assertEqual(seam["continue_rva"], "0x3407DAF")
        self.assertEqual(seam["patch_bytes"], 14)
        self.assertIn("0x88B480", seam["filter"])
        self.assertFalse(seam["live_authorized"])

    def test_scope_remains_static_and_private(self) -> None:
        scope = self.contract["scope"]
        self.assertFalse(scope["ck3_started"])
        self.assertFalse(scope["production_code_changed"])
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["readiness_promotion"])
        self.assertFalse(scope["daily_or_weekly_report_changed"])

    def test_extractor_freezes_exact_owner_and_lifetime(self) -> None:
        for token in (
            "CALLER_BEGIN_RVA = 0x3407C70",
            "CALLER_END_RVA = 0x3407F80",
            "WRAPPER_CALL_RVA = 0x3407D9C",
            "SCHEDULER_OWNER_GLOBAL_RVA = 0x5772E98",
            "POST_RETURN_SEAM_RVA = 0x3407DA1",
            "producer_to_destination_empty_path",
            "destination_forward_state0_retry_and_release",
        ):
            self.assertIn(token, self.extractor)


if __name__ == "__main__":
    unittest.main()
