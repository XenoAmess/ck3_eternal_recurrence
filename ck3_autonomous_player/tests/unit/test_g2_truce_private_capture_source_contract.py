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
        self.assertEqual(cmake.count("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1"), 2)
        self.assertIn("xar_ck3_raiktor_surrender_truce_v1_test PRIVATE", cmake)

    def test_capture_precedes_production_reset_without_public_wire(self) -> None:
        source = WRITER.read_text(encoding="utf-8")
        observer = source.index("output = ObserveRaiktorSurrenderTruceV1")
        call = source.index("AppendG2TrucePrivateCaptureV1(", observer)
        reset = source.index("output = {};", call)
        self.assertLess(call, reset)
        self.assertIn("xar.ck3.g2_truce_private_capture.v3", source)
        self.assertIn("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH", source)
        private_schema = "xar.ck3.g2_truce_private_capture.v3"
        for public_path in (
            NATIVE / "src" / "bridge.cpp",
            NATIVE / "include" / "xar_bridge" / "game_contract.hpp",
            ROOT / "src" / "xar_autoplayer" / "bridge" / "war_contract.py",
        ):
            self.assertNotIn(private_schema, public_path.read_text(encoding="utf-8"))

    def test_runtime_capture_calls_only_the_source_correlated_index7_helper(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        private_leaf = resolver.index(
            "ObserveRaiktorSurrenderTrucePrivateLeafContextV1("
        )
        runtime_call = resolver.index("CaptureTargetedIndex7ForG2(", private_leaf)
        private_leaf_end = resolver.index("\n}\n#endif", runtime_call)
        self.assertLess(runtime_call, private_leaf_end)
        self.assertEqual(resolver.count("CaptureTargetedIndex7ForG2("), 2)
        self.assertEqual(resolver.count("CaptureLoadedScriptedCandidatesForG2("), 1)
        self.assertEqual(resolver.count("CapturePrivateNestedContainerForG2("), 5)
        self.assertIn("constexpr std::size_t kRootIndex = 7", resolver)
        self.assertIn("constexpr std::size_t kHiddenIndex = 1", resolver)
        self.assertNotIn("CaptureLoadedScriptedCandidatesForG2(", resolver[runtime_call:private_leaf_end])
        self.assertNotIn("CapturePrivateNestedContainerForG2(", resolver[runtime_call:private_leaf_end])

    def test_targeted_helper_reads_no_siblings_and_calls_only_duration_evaluator(self) -> None:
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
        self.assertEqual(helper.count("environment.evaluate_duration_days("), 2)
        self.assertIn("const_cast<void *>(duration), request.effect_context", helper)
        self.assertIn("request.evaluation_context", helper)
        self.assertIn("capture.evaluator_call_count", helper)
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
            '"evaluator_capture_status"',
            '"evaluator_function_rva"',
            '"expected_evaluator_function_rva"',
            '"evaluator_effect_context"',
            '"evaluator_evaluation_context"',
            '"evaluator_first_days"',
            '"evaluator_second_days"',
            '"evaluator_call_count"',
            '"evaluator_nonnegative"',
            '"evaluator_stable"',
        ):
            self.assertIn(field.replace('"', '\\"'), source)

    def test_evaluator_boundary_is_durable_and_ordered_around_each_call(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        helper_begin = resolver.index("void CaptureTargetedIndex7ForG2(")
        helper_end = resolver.index("#endif", helper_begin)
        helper = resolver[helper_begin:helper_end]
        pre = helper.index('boundary.stage = "pre_call"')
        first_call = helper.index("capture.evaluator_first_days =")
        post_one = helper.index('boundary.stage = "post_call_1"')
        second_call = helper.index("capture.evaluator_second_days =")
        post_two = helper.index('boundary.stage = "post_call_2"')
        self.assertLess(pre, first_call)
        self.assertLess(first_call, post_one)
        self.assertLess(post_one, second_call)
        self.assertLess(second_call, post_two)
        self.assertIn("pre_call_durable_append_failed", helper)
        self.assertIn("post_call_1_durable_append_failed", helper)
        self.assertIn("post_call_2_durable_append_failed", helper)
        self.assertIn("private_fixture_stop_after_pre_call", helper)

    def test_boundary_writer_flushes_each_complete_jsonl_row(self) -> None:
        source = WRITER.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        self.assertIn(
            "xar.ck3.g2_truce_private_evaluator_boundary.v1", source
        )
        for field in (
            '"stage"',
            '"exact_path"',
            '"exact_path_verified"',
            '"truce_effect"',
            '"truce_vtable_rva"',
            '"duration_script_value"',
            '"duration_is_truce_plus_0x108"',
            '"effect_context"',
            '"evaluation_context"',
            '"evaluator_function_rva"',
            '"planned_call_count"',
            '"completed_call_count"',
            '"evaluated_days"',
        ):
            self.assertIn(field.replace('"', '\\"'), source)
        writer_begin = source.index("bool AppendAndFlushG2TrucePrivateRow(")
        writer_end = source.index(
            "bool AppendG2TrucePrivateEvaluatorBoundaryV1(", writer_begin
        )
        writer = source[writer_begin:writer_end]
        self.assertIn("FILE_APPEND_DATA", writer)
        self.assertIn("WriteFile", writer)
        self.assertIn("written == length", writer)
        self.assertIn("FlushFileBuffers", writer)
        self.assertIn("return write_ok && flush_ok", writer)
        self.assertIn("RaiktorTrucePrivateEvaluatorBoundaryV1", header)
        self.assertIn(
            "RaiktorTruceAppendPrivateEvaluatorBoundaryV1", header
        )

    def test_production_contract_uses_the_live_proven_shape_without_mutation(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        self.assertIn("kDefeatRootCapacity = 13", resolver)
        self.assertIn("kDefeatRootCount = 12", resolver)
        self.assertIn("kDefeatRootTruceScriptIndex = 7", resolver)
        self.assertIn("kScriptDefaultCapacity = 4", resolver)
        self.assertIn("kScriptDefaultCount = 4", resolver)
        self.assertIn("kScriptDefaultHiddenIndex = 1", resolver)
        begin = resolver.index("void CaptureTargetedIndex7ForG2(")
        end = resolver.index("#endif", begin)
        helper = resolver[begin:end]
        for forbidden in (
            "surrender",
            "white_peace",
            "enforce_demands",
            "WriteProcessMemory",
            "Execute",
        ):
            self.assertNotIn(forbidden, helper)

    def test_default_reader_uses_the_proven_synchronous_leaf_seam(self) -> None:
        resolver = RESOLVER.read_text(encoding="utf-8")
        writer = WRITER.read_text(encoding="utf-8")
        begin = resolver.index("ObserveRaiktorSurrenderTruceLeafContextV1(")
        end = resolver.index("\n}\n\nstd::string_view", begin)
        reader = resolver[begin:end]
        self.assertIn("ResolveUniqueTruceNode(", reader)
        self.assertIn("first_node.node != expected_truce_effect", reader)
        self.assertIn("ReadValue(access, request.effect_context, 0x28", reader)
        self.assertEqual(reader.count("environment.evaluate_duration_days("), 2)
        self.assertIn("ReadRaiktorTruceLeafPreviewContextV1", writer)
        self.assertIn("ObserveRaiktorSurrenderTruceLeafContextV1", writer)
        self.assertIn("ReadRaiktorTruceDurationViaNativeLeafPreviewV1", writer)

    def test_v2_uses_only_the_transient_native_leaf_preview_context(self) -> None:
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        writer = WRITER.read_text(encoding="utf-8")
        observer = (
            NATIVE / "src" / "g2_truce_preview_entry_observer_v1.cpp"
        ).read_text(encoding="utf-8")
        option = re.search(
            r"option\(\s*XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2\s+"
            r'"[^"]+"\s+(ON|OFF)\s*\)',
            cmake,
        )
        self.assertIsNotNone(option)
        self.assertEqual(option.group(1), "OFF")
        self.assertIn("XAR_CK3_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2=1", cmake)
        self.assertIn("bindings.traverse_loaded_effect(loaded_effect", writer)
        self.assertIn("CaptureG2TruceLeafPreviewContextV2", writer)
        self.assertIn("LoadAt<void *>(context, 0x28)", writer)
        self.assertIn(
            "ObserveRaiktorSurrenderTrucePrivateLeafContextV1", writer
        )
        self.assertIn("ArmG2TrucePreviewEntryCaptureV1", writer)
        self.assertIn("DisarmG2TrucePreviewEntryCaptureV1", writer)
        self.assertIn("armed_capture_callback", observer)


if __name__ == "__main__":
    unittest.main()
