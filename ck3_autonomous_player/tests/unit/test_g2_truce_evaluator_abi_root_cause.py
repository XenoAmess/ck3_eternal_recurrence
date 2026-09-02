from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    ROOT
    / "native_bridge"
    / "research"
    / "g2_truce_evaluator_abi_root_cause_v1.json"
)
EXTRACTOR = (
    ROOT
    / "native_bridge"
    / "research"
    / "extract_g2_truce_evaluator_abi.py"
)


class G2TruceEvaluatorAbiRootCauseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_abi_and_non_runtime_boundary(self) -> None:
        fixture = self.fixture
        self.assertEqual(fixture["status"], "static-ready")
        self.assertTrue(fixture["read_only"])
        self.assertEqual(fixture["evaluator"]["rva"], "0x3373000")
        self.assertEqual(
            fixture["evaluator"]["pdata"],
            ["0x3373000", "0x337312F", "0x4C92B1C"],
        )
        self.assertEqual(
            fixture["evaluator"]["entry_bindings"],
            {
                "RCX": "script_value -> RBX",
                "RDX": "effect_context -> RBP",
                "R8": "evaluation_context -> RSI",
            },
        )
        self.assertFalse(fixture["evaluator"]["incoming_r9_consumed"])
        self.assertFalse(fixture["evaluator"]["incoming_stack_parameter_consumed"])
        self.assertFalse(fixture["evaluator"]["direct_fs_gs_tls_access"])
        self.assertEqual(
            fixture["boundaries"],
            {
                "ck3_started": False,
                "mutation_sent": False,
                "public_abi_changed": False,
                "public_readiness_changed": False,
            },
        )

    def test_all_direct_xrefs_are_unique_and_frozen(self) -> None:
        xrefs = self.fixture["direct_xrefs"]
        self.assertEqual(xrefs["call_count"], 78)
        self.assertEqual(xrefs["tail_jump_count"], 1)
        self.assertEqual(len(xrefs["rvas"]), 79)
        self.assertEqual(len(set(xrefs["rvas"])), 79)
        self.assertEqual(xrefs["rvas"], sorted(xrefs["rvas"], key=lambda value: int(value, 0)))
        self.assertTrue({"0x2EDAF0F", "0x2EDB59E", "0x2EDC204"}.issubset(xrefs["rvas"]))
        self.assertEqual(xrefs["tail_jump_rva"], "0x2EDC204")

    def test_native_callsite_hashes_and_context_kind(self) -> None:
        calls = self.fixture["caddtruce_calls"]
        self.assertEqual([row["call_rva"] for row in calls], ["0x2EDAF0F", "0x2EDB59E"])
        self.assertEqual([row["owner_pdata_begin"] for row in calls], ["0x2EDAD20", "0x2EDB3A0"])
        for row in calls:
            self.assertRegex(row["sequence_sha256"], r"^[0-9A-F]{64}$")
        wrapper = self.fixture["generic_wrapper"]
        self.assertEqual(wrapper["pdata"], ["0x2EDC1B0", "0x2EDC209", "0x4C38E20"])
        self.assertIn("*(void **)(RDX + 0x28)", wrapper["semantic"])
        diagnosis = self.fixture["diagnosis"]
        self.assertTrue(diagnosis["three_parameter_msvc_x64_signature_correct"])
        self.assertFalse(diagnosis["missing_parameter"])
        self.assertFalse(diagnosis["thiscall_mismatch"])
        self.assertEqual(diagnosis["root_cause"], "wrong_evaluation_context_kind")
        self.assertIn("*(void **)", diagnosis["native_expected"])

    def test_live_boundary_correlates_exact_field_address(self) -> None:
        live = self.fixture["frozen_live_boundary"]
        self.assertEqual(int(live["evaluation_context"], 0), int(live["effect_context"], 0) + 0x28)
        self.assertEqual(live["post_call_rows"], 0)
        self.assertEqual(live["terminal"], "process_exit")

    def test_extractor_remains_static_and_hash_binds_inputs(self) -> None:
        source = EXTRACTOR.read_text(encoding="utf-8")
        self.assertIn("runtime_functions", source)
        self.assertIn("scan_direct_xrefs", source)
        self.assertIn("EXPECTED_TERMINAL_SUMMARY_SHA256", source)
        for forbidden in ("OpenProcess(", "CreateRemoteThread(", "Start-Process", "subprocess"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            hashlib.sha256(bytes.fromhex("4C8B42284883C4205BE9F76D4900")).hexdigest().upper(),
            self.fixture["generic_wrapper"]["tail_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
