from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
RESOLVER = NATIVE / "src" / "raiktor_surrender_truce_v1.cpp"
WRITER = NATIVE / "src" / "ck3_11906.cpp"
HEADER = NATIVE / "include" / "xar_bridge" / "raiktor_surrender_truce_v1.hpp"


class G2TrucePrivateCaptureSourceContractTests(unittest.TestCase):
    def test_capture_is_off_by_default_and_private_to_instrumented_dll(self) -> None:
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        option = re.search(
            r"option\(\s*XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1\s+"
            r'"[^"]+"\s+(ON|OFF)\s*\)',
            cmake,
        )
        self.assertIsNotNone(option)
        self.assertEqual(option.group(1), "OFF")
        self.assertEqual(cmake.count("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1"), 1)

    def test_capture_precedes_production_reset_without_public_wire(self) -> None:
        source = WRITER.read_text(encoding="utf-8")
        observer = source.index("output = ObserveRaiktorSurrenderTruceV1")
        call = source.index("AppendG2TrucePrivateCaptureV1(", observer)
        reset = source.index("output = {};", call)
        self.assertLess(call, reset)
        self.assertIn("xar.ck3.g2_truce_private_capture.v2", source)
        self.assertIn("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH", source)
        private_schema = "xar.ck3.g2_truce_private_capture.v2"
        for public_path in (
            NATIVE / "src" / "bridge.cpp",
            NATIVE / "include" / "xar_bridge" / "game_contract.hpp",
            ROOT / "src" / "xar_autoplayer" / "bridge" / "war_contract.py",
        ):
            self.assertNotIn(private_schema, public_path.read_text(encoding="utf-8"))

    def test_runtime_capture_calls_only_the_source_correlated_index7_helper(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        resolve = resolver.index("ResolveUniqueTruceNode(")
        runtime_call = resolver.index("CaptureTargetedIndex7ForG2(", resolve)
        stale_gate = resolver.index('XAR_G2_SHAPE_STAGE("root_capacity_mismatch")', runtime_call)
        self.assertLess(runtime_call, stale_gate)
        self.assertEqual(resolver.count("CaptureTargetedIndex7ForG2("), 2)
        self.assertEqual(resolver.count("CaptureLoadedScriptedCandidatesForG2("), 1)
        self.assertEqual(resolver.count("CapturePrivateNestedContainerForG2("), 5)
        self.assertIn("constexpr std::size_t kRootIndex = 7", resolver)
        self.assertIn("constexpr std::size_t kHiddenIndex = 1", resolver)
        self.assertNotIn("CaptureLoadedScriptedCandidatesForG2(", resolver[runtime_call:stale_gate])
        self.assertNotIn("CapturePrivateNestedContainerForG2(", resolver[runtime_call:stale_gate])

    def test_targeted_helper_reads_no_siblings_and_never_calls_evaluator(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        begin = resolver.index("void CaptureTargetedIndex7ForG2(")
        end = resolver.index("#endif", begin)
        helper = resolver[begin:end]
        self.assertNotIn("for (", helper)
        self.assertIn("kRootIndex * sizeof(void *)", helper)
        self.assertIn("kHiddenIndex * sizeof(void *)", helper)
        self.assertIn("ReadValue(access, hidden_children, 0, context)", helper)
        self.assertIn("ReadValue(access, context_children, 0, truce)", helper)
        self.assertIn("kTruceDurationScriptValueOffset", helper)
        self.assertNotIn("evaluate_duration_days", helper)
        for old_index in ("root_index == 9", "root_index == 10"):
            self.assertNotIn(old_index, helper)

    def test_exact_target_shape_and_duration_input_are_serialized(self) -> None:
        source = WRITER.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        self.assertIn("targeted_index7_status", header)
        for field in (
            '"targeted_index7_status"',
            '"expected_default_capacity":4',
            '"expected_default_count":4',
            '"expected_hidden_index":1',
            '"expected_hidden_capacity":1',
            '"expected_context_capacity":1',
            '"expected_truce_vtable_rva"',
            '"duration_script_value"',
        ):
            self.assertIn(field.replace('"', '\\"'), source)

    def test_production_contract_and_mutation_surfaces_are_unchanged(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        self.assertIn("kDefeatRootCapacity = 19", resolver)
        self.assertIn("kDefeatRootCount = 14", resolver)
        self.assertIn("kDefeatRootTruceScriptIndex = 9", resolver)
        begin = resolver.index("void CaptureTargetedIndex7ForG2(")
        end = resolver.index("#endif", begin)
        helper = resolver[begin:end]
        for forbidden in (
            "surrender",
            "white_peace",
            "enforce_demands",
            "WriteProcessMemory",
        ):
            self.assertNotIn(forbidden, helper)


if __name__ == "__main__":
    unittest.main()
