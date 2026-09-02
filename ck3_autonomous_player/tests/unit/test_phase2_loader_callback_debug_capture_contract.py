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
OWNER_CONTRACT = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_runtime_owner_v1_abi.json"
)
OWNER_EXTRACTOR = (
    ROOT
    / "native_bridge/research/extract_phase2_loader_callback_runtime_owner.py"
)
LATER_STALL_CONTRACT = (
    ROOT
    / "native_bridge/research/phase2_loader_callback_later_stall_v1_abi.json"
)


class Phase2LoaderCallbackDebugCaptureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROBE.read_text(encoding="utf-8")
        cls.runtime = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
        cls.owner = json.loads(OWNER_CONTRACT.read_text(encoding="utf-8"))
        cls.extractor = OWNER_EXTRACTOR.read_text(encoding="utf-8")
        cls.later_stall = json.loads(
            LATER_STALL_CONTRACT.read_text(encoding="utf-8")
        )

    def test_probe_is_bound_to_the_frozen_callback_contract(self) -> None:
        self.assertIn("kCallbackCallRva = 0x3B9AB90", self.source)
        self.assertIn("kCallbackSlotTargetRva = 0x3B9BA70", self.source)
        self.assertIn("kCallbackContinuationRva = 0x3B9AB93", self.source)
        self.assertIn("kObservedRuntimeVtableRva = 0x408A450", self.source)
        self.assertIn("kObservedRuntimeSlotTargetRva = 0x947BD0", self.source)
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

    def test_rtti_owner_and_entry_return_evidence_stay_private(self) -> None:
        self.assertEqual(self.owner["status"], "private-entry-return-observed")
        self.assertFalse(self.owner["production_installed"])
        self.assertFalse(self.owner["production_abi_changed"])
        self.assertFalse(self.owner["readiness_promotion"])
        static = self.owner["static_owner_evidence"]
        self.assertEqual(static["runtime_vtable_rva"], "0x408A450")
        self.assertEqual(static["complete_object_locator_rva"], "0x45BD3B0")
        self.assertEqual(static["type_descriptor_rva"], "0x514FE60")
        self.assertEqual(static["slot_2_target_rva"], "0x947BD0")
        self.assertEqual(static["slot_2_bytes"], "48FF6108")
        self.assertEqual(static["callback_storage"], "receiver+0x08")
        observation = self.owner["entry_return_observation"]
        self.assertTrue(observation["same_thread"])
        self.assertEqual(observation["concrete_callback_rva"], "0x2045330")
        self.assertTrue(observation["receiver_survived_return"])
        self.assertTrue(observation["vptr_survived_return"])
        self.assertTrue(observation["callback_function_survived_return"])
        self.assertEqual(
            self.owner["cleanup"]["primary_artifact_result"], "RED"
        )
        self.assertEqual(
            self.owner["cleanup"]["combined_cleanup_result"], "GREEN"
        )
        self.assertIn("EXPECTED_COL_RVA = 0x45BD3B0", self.extractor)
        self.assertIn("EXPECTED_TYPE_DESCRIPTOR_RVA = 0x514FE60", self.extractor)
        self.assertIn("EXPECTED_SLOT_2_BYTES = bytes.fromhex", self.extractor)

    def test_later_stall_sequence_records_bounded_no_go(self) -> None:
        contract = self.later_stall
        self.assertEqual(contract["status"], "private-bounded-sequence-no-go")
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        capture = contract["capture"]
        self.assertEqual(capture["result"], "RED")
        self.assertEqual(
            capture["reason"], "callback-sequence-stall-boundary-unobservable"
        )
        self.assertEqual(capture["entry_count"], 2)
        self.assertEqual(capture["last_successful_sequence"], 2)
        self.assertEqual(capture["first_unreturned_sequence"], 0)
        self.assertTrue(all(entry["returned"] for entry in capture["entries"]))
        self.assertEqual(
            capture["entries"][0]["node_name"], "CGameConceptTypeDatabase"
        )
        self.assertEqual(
            capture["entries"][1]["node_name"], "CJominiLoadScreenDatabase"
        )
        self.assertFalse(
            capture["timeout_boundary"]["instruction_pointer_is_ck3_rva"]
        )
        self.assertIsNone(capture["timeout_boundary"]["node_name"])
        self.assertEqual(contract["cleanup"]["result"], "GREEN")

    def test_sequence_probe_remains_private_and_bounded(self) -> None:
        self.assertIn('else if (name == L"--sequence")', self.source)
        self.assertIn("options.sequence || !capture.callback_return_observed", self.source)
        self.assertIn("callback-sequence-stall-boundary-unobservable", self.source)
        self.assertIn("private_test_only", self.source)
        self.assertIn("public_bridge_abi_changed", self.source)
        self.assertIn("production_detour_installed", self.source)

    def test_next_node_probe_uses_the_static_stop_point_and_exit_edge(self) -> None:
        self.assertIn("kNodeLoadedStopRva = 0x3B9AB53", self.source)
        self.assertIn("kLoopExitRva = 0x3B9ACC4", self.source)
        self.assertIn('else if (name == L"--next-node")', self.source)
        self.assertIn("next-node-loaded", self.source)
        self.assertIn("vector-exhausted", self.source)
        self.assertIn("last-returned-callback-next-node-observed", self.source)
        self.assertIn("last-returned-callback-vector-exhausted", self.source)
        self.assertIn("restore_transition_breakpoints", self.source)


if __name__ == "__main__":
    unittest.main()
