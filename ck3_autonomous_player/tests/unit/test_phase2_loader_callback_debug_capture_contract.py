from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROBE = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_debug_capture.cpp"
)
RUNTIME_CONTRACT = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_runtime_vtable_v1_abi.json"
)


class Phase2LoaderCallbackDebugCaptureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROBE.read_text(encoding="utf-8")
        cls.runtime = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))

    def test_probe_is_bound_to_the_frozen_callback_contract(self) -> None:
        self.assertIn("kCallbackCallRva = 0x3B9AB90", self.source)
        self.assertIn("kCallbackSlotTargetRva = 0x3B9BA70", self.source)
        self.assertIn("0x4558700", self.source)
        self.assertIn("0x4558770", self.source)
        self.assertIn("{0xFF, 0x50, 0x10}", self.source)
        self.assertIn(
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            self.source,
        )

    def test_probe_remains_private_and_restores_its_one_shot_breakpoint(self) -> None:
        self.assertIn("DEBUG_ONLY_THIS_PROCESS", self.source)
        self.assertIn("private_test_only", self.source)
        self.assertIn("public_bridge_abi_changed", self.source)
        self.assertIn("production_detour_installed", self.source)
        self.assertIn("original_breakpoint_byte_restored", self.source)

        cmake_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in (ROOT / "native_bridge").rglob("CMakeLists.txt")
        )
        self.assertNotIn(PROBE.name, cmake_text)

    def test_runtime_contract_records_the_observation_without_readiness_claims(self) -> None:
        self.assertEqual(self.runtime["status"], "private-runtime-observed")
        self.assertFalse(self.runtime["production_installed"])
        self.assertFalse(self.runtime["production_abi_changed"])
        self.assertFalse(self.runtime["readiness_promotion"])
        capture = self.runtime["capture"]
        self.assertTrue(capture["paused_at_callback_instruction"])
        self.assertTrue(capture["receiver_matches_node"])
        self.assertEqual(capture["runtime_vptr_rva"], "0x408A450")
        self.assertEqual(capture["slot_2_target_rva"], "0x947BD0")
        comparison = self.runtime["static_candidate_comparison"]
        self.assertFalse(comparison["runtime_vptr_matches_candidate"])
        self.assertFalse(comparison["runtime_slot_target_matches_candidate"])
        self.assertEqual(self.runtime["cleanup"]["cleanup_result"], "GREEN")


if __name__ == "__main__":
    unittest.main()
