from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


class Phase2CompletionWrapperCallersContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (
                NATIVE
                / "research/phase2_completion_wrapper_callers_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        cls.extractor = (
            NATIVE
            / "research/extract_phase2_completion_wrapper_callers.py"
        ).read_text(encoding="utf-8")

    def test_all_direct_callers_are_frozen_without_unique_runtime_owner(self) -> None:
        callers = self.contract["direct_callers"]
        self.assertEqual(callers["callsite_count"], 618)
        self.assertEqual(callers["caller_function_count"], 525)
        self.assertEqual(callers["single_call_function_count"], 432)
        self.assertEqual(callers["dual_call_function_count"], 93)
        self.assertFalse(callers["runtime_owner_unique"])

    def test_post_publish_path_requires_external_reinvocation(self) -> None:
        flow = self.contract["post_publish_control_flow"]
        self.assertEqual(
            flow["consumer_calls_before_producer"],
            ["0x3B9E10B", "0x3B9E175"],
        )
        self.assertFalse(flow["consumer_reentry_after_producer"])
        self.assertFalse(flow["wrapper_self_call"])
        self.assertEqual(flow["return_rva"], "0x3B9E265")

    def test_next_observation_maps_entry_return_address(self) -> None:
        observation = self.contract["next_distinct_observation"]
        self.assertEqual(observation["rva"], "0x3B9E030")
        self.assertIn("[RSP]", observation["read"])
        self.assertFalse(observation["live_authorized"])

    def test_scope_stays_private_static_and_read_only(self) -> None:
        scope = self.contract["scope"]
        self.assertFalse(scope["ck3_started"])
        self.assertFalse(scope["production_code_changed"])
        self.assertFalse(scope["public_abi_changed"])
        self.assertFalse(scope["readiness_promotion"])
        self.assertFalse(scope["thread_or_os_wait_inferred"])

    def test_extractor_freezes_instruction_bound_callers(self) -> None:
        for token in (
            "EXPECTED_DIRECT_CALL_COUNT = 618",
            "EXPECTED_CALL_LIST_SHA256",
            "EXPECTED_CALLER_FUNCTION_COUNT = 525",
            "instruction_boundary_verified",
            "consumer_reentry_after_producer",
            "external_reinvocation_required",
        ):
            self.assertIn(token, self.extractor)


if __name__ == "__main__":
    unittest.main()
