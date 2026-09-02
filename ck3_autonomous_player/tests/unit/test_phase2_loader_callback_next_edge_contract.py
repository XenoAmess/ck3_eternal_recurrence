from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_next_edge_v1_abi.json"
)
EXTRACTOR_PATH = (
    ROOT / "native_bridge/research/extract_phase2_loader_callback_next_edge.py"
)
STATIC_SLICE_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json"
)
LATER_STALL_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_later_stall_v1_abi.json"
)


class Phase2LoaderCallbackNextEdgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.extractor = EXTRACTOR_PATH.read_text(encoding="utf-8")

    def test_exact_build_inputs_and_private_boundary_are_pinned(self) -> None:
        contract = self.contract
        self.assertEqual(contract["status"], "static-stop-point-bound")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertFalse(contract["readiness_promotion"])
        self.assertEqual(
            contract["source"]["static_slice_contract_sha256"],
            hashlib.sha256(STATIC_SLICE_PATH.read_bytes()).hexdigest().upper(),
        )
        self.assertEqual(
            contract["source"]["later_stall_contract_sha256"],
            hashlib.sha256(LATER_STALL_PATH.read_bytes()).hexdigest().upper(),
        )

    def test_next_iterator_edge_decodes_to_node_load_or_exit(self) -> None:
        iterator = self.contract["evidence"]["iterator"]
        raw = bytes.fromhex("4883C308483BDF0F858CFEFFFF")
        self.assertEqual(
            hashlib.sha256(raw).hexdigest().upper(), iterator["edge_bytes_sha256"]
        )
        branch_rva = int(iterator["next_branch_rva"], 0)
        branch = raw[7:]
        displacement = struct.unpack("<i", branch[2:6])[0]
        self.assertEqual(
            branch_rva + len(branch) + displacement,
            int(iterator["next_branch_target_rva"], 0),
        )
        self.assertEqual(
            branch_rva + len(branch),
            int(iterator["exhausted_fallthrough_rva"], 0),
        )

    def test_primary_stop_precedes_nullable_callback_gate(self) -> None:
        stop = self.contract["evidence"]["observable_stop_point"]
        self.assertEqual(stop["rva"], "0x3B9AB53")
        self.assertEqual(stop["preceding_instruction_rva"], "0x3B9AB50")
        self.assertEqual(stop["preceding_instruction"], "mov RSI,[RBX]")
        self.assertEqual(stop["current_node_register"], "RSI")
        self.assertEqual(stop["node_name_pointer"], "[RSI+0x08]")
        self.assertEqual(stop["callback_receiver"], "[RSI+0x88]")
        self.assertTrue(stop["callback_gate_not_yet_executed"])
        self.assertTrue(stop["reached_for_every_nonempty_iteration"])
        self.assertEqual(
            self.contract["evidence"]["loop_exit_discriminator"]["rva"],
            "0x3B9ACC4",
        )

    def test_wait_semantics_and_live_run_are_not_overclaimed(self) -> None:
        boundary = self.contract["wait_edge_boundary"]
        self.assertEqual(boundary["status"], "no-unique-wait-edge-in-bounded-function")
        self.assertEqual(len(boundary["opaque_post_return_call_rvas"]), 4)
        self.assertFalse(self.contract["evidence"]["ck3_started"])
        self.assertFalse(self.contract["next_entry"]["authorized_in_this_package"])
        self.assertIn("EXPECTED_SHA256", self.extractor)
        self.assertIn("NODE_LOADED_STOP_RVA = 0x3B9AB53", self.extractor)
        self.assertIn("NEXT_ADVANCE_RVA = 0x3B9ACB7", self.extractor)
        self.assertIn("LOOP_EXIT_RVA = 0x3B9ACC4", self.extractor)


if __name__ == "__main__":
    unittest.main()
