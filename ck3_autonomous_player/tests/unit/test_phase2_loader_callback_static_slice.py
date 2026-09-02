from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ABI_PATH = ROOT / "native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json"
FIXTURE_PATH = (
    ROOT
    / "native_bridge/research/fixtures/phase2_loader_callback_v1_source_contract.json"
)
ANCHORS_PATH = ROOT / "native_bridge/research/ck3_1_19_0_6_anchors.json"


def read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


class Phase2LoaderCallbackStaticSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = read_object(ABI_PATH)
        cls.fixture = read_object(FIXTURE_PATH)
        cls.anchors = read_object(ANCHORS_PATH)

    def test_exact_build_and_reused_fixture_are_pinned(self) -> None:
        self.assertEqual(self.abi["status"], "static-ready")
        self.assertTrue(self.abi["read_only"])
        self.assertFalse(self.abi["production_installed"])
        self.assertFalse(self.abi["production_abi_changed"])
        build = self.abi["build"]
        self.assertEqual(
            build,
            {
                "product_version": self.anchors["build"]["product_version"],
                "executable_sha256": self.anchors["build"]["sha256"],
                "file_size": self.anchors["build"]["file_size"],
                "pe_timestamp": self.anchors["build"]["pe_timestamp"],
                "image_base": self.anchors["build"]["image_base"],
                "size_of_image": self.anchors["build"]["size_of_image"],
                "architecture": "msvc-x64",
            },
        )
        fixture = self.abi["fixture"]
        self.assertEqual(fixture["reused_contract"], "phase2-loader-callback-v1")
        self.assertEqual(
            fixture["sha256"],
            hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest().upper(),
        )
        self.assertEqual(self.fixture["contract"], fixture["reused_contract"])

    def test_prologue_pdata_and_handler_are_machine_readable(self) -> None:
        function = self.abi["function"]
        self.assertEqual(function["rva"], "0x3B9AB00")
        self.assertEqual(function["end_rva_exclusive"], "0x3B9ACED")
        prologue = function["prologue"]
        self.assertEqual(prologue["rva"], "0x3B9AB00")
        self.assertEqual(prologue["end_rva_exclusive"], "0x3B9AB23")
        self.assertEqual(prologue["length_bytes"], 35)
        self.assertEqual(
            prologue["bytes_hex"],
            "48895C2410488974241848897C24205541564157488DAC2410FEFFFF4881ECF0020000",
        )
        self.assertEqual(
            prologue["pdata"],
            {
                "begin_rva": "0x3B9AB00",
                "end_rva_exclusive": "0x3B9ACED",
                "unwind_info_rva": "0x4F0FE28",
            },
        )
        unwind = prologue["unwind"]
        self.assertEqual(unwind["raw_header_hex"], "11230B00")
        self.assertEqual(unwind["version"], 1)
        self.assertEqual(unwind["flags"], 2)
        self.assertEqual(unwind["prolog_size_bytes"], 35)
        self.assertEqual(unwind["unwind_code_count"], 11)
        self.assertEqual(unwind["handler_rva"], "0x3E27DD0")

    def test_win64_register_flow_and_vcall_slot_are_bounded(self) -> None:
        flow = self.abi["win64_parameter_flow"]
        self.assertEqual(flow["calling_convention"], "MSVC x64")
        self.assertEqual(flow["entry_argument_register"], "RCX")
        self.assertEqual(flow["entry_owner_load"], "[RCX+0x08]")
        self.assertEqual(flow["node_vector_begin_load"], "[owner+0x70]")
        self.assertEqual(flow["node_count_load"], "[owner+0x7C]")
        self.assertEqual(flow["callback_receiver_load"], "RCX=[node+0x88]")
        self.assertEqual(flow["vptr_load"], "RAX=[RCX]")
        self.assertEqual(flow["indirect_call"], "[RAX+0x10]")
        self.assertEqual(flow["explicitly_initialized_call_registers"], ["RCX"])
        self.assertEqual(flow["additional_argument_registers"], "not_established")
        self.assertFalse(flow["return_value_consumed_by_loop"])

        vtable = self.abi["callback_vtable"]
        self.assertEqual(vtable["slot_index"], 2)
        self.assertEqual(vtable["byte_offset"], "0x10")
        self.assertEqual(vtable["slot_target_rva"], "0x3B9BA70")
        candidates = vtable["candidate_callable_vtables"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(
            {candidate["vtable_rva"] for candidate in candidates},
            {"0x4558700", "0x4558770"},
        )
        self.assertTrue(
            all(
                candidate["invoke_slot_target_rva"] == "0x3B9BA70"
                for candidate in candidates
            )
        )
        self.assertEqual(vtable["runtime_node_vptr_identity"], "unknown")
        self.assertEqual(vtable["runtime_callback_return_semantics"], "unknown")

    def test_callers_and_thread_lifecycle_do_not_overclaim(self) -> None:
        callers = self.abi["callers"]
        self.assertEqual(callers["count"], 8)
        self.assertEqual(
            callers["direct_relative_callsite_rvas"],
            [
                "0x821E45",
                "0x88B5DC",
                "0x1B3984D",
                "0x1E18C56",
                "0x1E21CD3",
                "0x203FF96",
                "0x2041D8C",
                "0x3B9AEF4",
            ],
        )
        lifecycle = self.abi["thread_lifecycle"]
        self.assertEqual(lifecycle["bounded_dispatch"], "direct_synchronous_call")
        self.assertEqual(lifecycle["continuation_rva"], "0x3B9AB93")
        self.assertTrue(lifecycle["same_function_continuation"])
        self.assertFalse(lifecycle["thread_handoff_observed_in_bounded_range"])
        self.assertEqual(lifecycle["thread_identity"], "unknown")
        self.assertEqual(lifecycle["callback_object_lifetime"], "unknown")
        self.assertEqual(lifecycle["lock_or_quiescence"], "not_observed")
        self.assertTrue(lifecycle["unwind_metadata_present"])
        self.assertFalse(lifecycle["production_detour"])
        self.assertIn(
            "a synchronous direct call does not identify the operating-system thread",
            self.abi["evidence_limits"],
        )
        self.assertIn(
            "no production callback hook, bridge field, or loader-readiness claim follows",
            self.abi["evidence_limits"],
        )


if __name__ == "__main__":
    unittest.main()
