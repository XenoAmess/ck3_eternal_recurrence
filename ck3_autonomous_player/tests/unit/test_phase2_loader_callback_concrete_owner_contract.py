from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge/research"
CONTRACT_PATH = RESEARCH / "phase2_loader_callback_concrete_owner_v1_abi.json"
EXTRACTOR_PATH = RESEARCH / "extract_phase2_loader_callback_concrete_owner.py"


class Phase2LoaderCallbackConcreteOwnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.extractor = EXTRACTOR_PATH.read_text(encoding="utf-8")

    def test_exact_build_and_extractor_are_pinned(self) -> None:
        self.assertEqual(self.contract["status"], "static-owner-bound")
        self.assertTrue(self.contract["read_only"])
        self.assertFalse(self.contract["production_installed"])
        self.assertFalse(self.contract["production_abi_changed"])
        self.assertFalse(self.contract["readiness_promotion"])
        self.assertEqual(
            self.contract["source"]["extractor_sha256"],
            hashlib.sha256(EXTRACTOR_PATH.read_bytes()).hexdigest().upper(),
        )
        self.assertIn("CALLBACK_RVA = 0x2045330", self.extractor)
        self.assertIn("CONSTRUCTION_REF_RVA = 0x8235A5", self.extractor)
        self.assertIn("OWNER_FUNCTION_RVA = 0x823570", self.extractor)

    def test_unique_construction_body_and_shared_rtti_slots_are_explicit(self) -> None:
        evidence = self.contract["evidence"]
        construction = evidence["direct_construction_path"]
        self.assertEqual(construction["rip_relative_reference_count"], 1)
        self.assertEqual(construction["construction_reference_rva"], "0x8235A5")
        self.assertEqual(construction["unique_code_owner_rva"], "0x823570")
        self.assertEqual(construction["registration_call_rva"], "0x8235FD")
        owner = evidence["source_owner"]
        self.assertIsNone(owner["class_method_name"])
        self.assertEqual(
            [row["rtti_type_name"] for row in owner["vtable_slots"]],
            [".?AVCInterfaceApplication@@", ".?AVCGameApplication@@"],
        )
        self.assertTrue(
            all(
                row["slot_index"] == 23
                and row["slot_target_rva"] == "0x823570"
                for row in owner["vtable_slots"]
            )
        )

    def test_callback_trampoline_and_stop_boundary_do_not_overclaim(self) -> None:
        callback = self.contract["evidence"]["concrete_callback"]
        self.assertEqual(callback["rva"], "0x2045330")
        self.assertEqual(callback["global_object_pointer_rva"], "0x570C0F0")
        self.assertIn("tail-jump vtable slot 2", callback["shape"])
        self.assertFalse(self.contract["evidence"]["ck3_started"])
        self.assertFalse(self.contract["next_entry"]["authorized_in_this_package"])
        self.assertIn(
            "no method name is assigned without source symbols",
            self.contract["limits"],
        )


if __name__ == "__main__":
    unittest.main()
