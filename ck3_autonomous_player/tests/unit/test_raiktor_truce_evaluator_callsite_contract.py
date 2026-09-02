from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "raiktor_truce_evaluator_callsite_v1_abi.json"
)
ANCHORS_PATH = ROOT / "native_bridge" / "research" / "ck3_1_19_0_6_anchors.json"


class RaiktorTruceEvaluatorCallsiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.anchors = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))

    def test_static_build_and_non_production_boundary(self) -> None:
        contract = self.contract
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["status"], "static-ready")
        self.assertTrue(contract["read_only"])
        self.assertFalse(contract["production_installed"])
        self.assertFalse(contract["production_abi_changed"])
        self.assertEqual(contract["build"], {
            "product_version": self.anchors["build"]["product_version"],
            "executable_sha256": self.anchors["build"]["sha256"],
            "file_size": self.anchors["build"]["file_size"],
            "pe_timestamp": self.anchors["build"]["pe_timestamp"],
            "image_base": self.anchors["build"]["image_base"],
            "size_of_image": self.anchors["build"]["size_of_image"],
            "architecture": self.anchors["build"]["architecture"],
        })
        self.assertFalse(contract["shared_contract"]["expiry_semantics_observed"])
        self.assertIn("public wire", " ".join(contract["evidence_limits"]))

    def test_evaluator_entry_span_and_return_contract(self) -> None:
        evaluator = self.contract["evaluator"]
        entry = bytes.fromhex(evaluator["entry_bytes_hex"])
        self.assertEqual(len(entry), 64)
        self.assertEqual(
            hashlib.sha256(entry).hexdigest().upper(), evaluator["entry_span_sha256"]
        )
        self.assertEqual(evaluator["rva"], "0x3373000")
        self.assertEqual(evaluator["return_rva"], "0x337312E")
        self.assertEqual(evaluator["return_kind"], "int32_in_EAX")
        self.assertEqual(
            self.contract["shared_contract"]["direct_call_target_rva"],
            evaluator["rva"],
        )

    def test_both_call_sites_bind_same_duration_context_and_target(self) -> None:
        rows = self.contract["call_sites"]
        self.assertEqual(len(rows), 2)
        for row in rows:
            start = int(row["sequence_start_rva"], 0)
            call = int(row["call_instruction_rva"], 0)
            end = int(row["sequence_end_rva_exclusive"], 0)
            encoded = bytes.fromhex(row["bytes_hex"])
            self.assertEqual(end - start, len(encoded))
            self.assertEqual(
                hashlib.sha256(encoded).hexdigest().upper(), row["sequence_sha256"]
            )
            call_offset = call - start
            self.assertGreaterEqual(call_offset, 0)
            self.assertEqual(encoded[call_offset], 0xE8)
            displacement = struct.unpack_from("<i", encoded, call_offset + 1)[0]
            self.assertEqual(
                call + 5 + displacement,
                int(row["operands"]["target_rva"], 0),
            )
            self.assertEqual(row["operands"]["target_rva"], "0x3373000")
            self.assertEqual(row["operands"]["script_value"], "RCX = [RSI+0x108]")
            post = bytes.fromhex(row["post_call_bytes_hex"])
            self.assertEqual(
                hashlib.sha256(post).hexdigest().upper(), row["post_call_sha256"]
            )
        self.assertEqual(
            self.contract["shared_contract"]["caddtruce_duration_offset"], "0x108"
        )
        self.assertEqual(
            self.contract["shared_contract"]["evaluation_context_offset"], "0x28"
        )
        self.assertTrue(self.contract["shared_contract"]["return_consumed_as_days"])


if __name__ == "__main__":
    unittest.main()
