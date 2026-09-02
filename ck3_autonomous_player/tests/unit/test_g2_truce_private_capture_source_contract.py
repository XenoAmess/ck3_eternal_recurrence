from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"


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
        self.assertIn(
            "if(XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1)", cmake
        )
        self.assertIn(
            "target_compile_definitions(xar_ck3_bridge PRIVATE", cmake
        )
        self.assertEqual(cmake.count("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1"), 1)

    def test_capture_precedes_reset_without_public_serialization(self) -> None:
        source = (NATIVE / "src" / "ck3_11906.cpp").read_text(encoding="utf-8")
        observer = source.index("output = ObserveRaiktorSurrenderTruceV1")
        call = source.index("AppendG2TrucePrivateCaptureV1(", observer)
        reset = source.index("output = {};", call)
        self.assertLess(call, reset)
        self.assertIn("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH", source)
        self.assertIn("XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1", source)

        private_schema = "xar.ck3.g2_truce_private_capture.v1"
        self.assertIn(private_schema, source)
        for public_path in (
            NATIVE / "src" / "bridge.cpp",
            NATIVE / "include" / "xar_bridge" / "game_contract.hpp",
            ROOT / "src" / "xar_autoplayer" / "bridge" / "war_contract.py",
        ):
            self.assertNotIn(
                private_schema, public_path.read_text(encoding="utf-8")
            )

    def test_capture_names_the_failed_loaded_tree_check_and_actual_shape(self) -> None:
        resolver = (
            NATIVE / "src" / "raiktor_surrender_truce_v1.cpp"
        ).read_text(encoding="utf-8")
        writer = (NATIVE / "src" / "ck3_11906.cpp").read_text(
            encoding="utf-8"
        )
        header = (
            NATIVE
            / "include"
            / "xar_bridge"
            / "raiktor_surrender_truce_v1.hpp"
        ).read_text(encoding="utf-8")

        self.assertIn("XAR_G2_SHAPE_RESET();", resolver)
        for check in (
            "root_capacity_mismatch",
            "root_count_mismatch",
            "scripted_vtable_mismatch",
            "default_capacity_mismatch",
            "default_count_mismatch",
            "hidden_count_mismatch",
            "hidden_capacity_mismatch",
            "context_capacity_mismatch",
            "truce_vtable_mismatch",
            "complete",
        ):
            self.assertIn(f'XAR_G2_SHAPE_STAGE("{check}")', resolver)

        self.assertIn("RaiktorTrucePrivateShapeCaptureV1", header)
        self.assertIn("#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)", header)
        for field in (
            '"failed_check"',
            '"root_vtable_rva"',
            '"root_capacity"',
            '"root_count"',
            '"default_child_vtable_rvas"',
            '"hidden_capacity"',
            '"context_capacity"',
            '"truce_vtable_rva"',
        ):
            self.assertIn(field.replace('"', '\\"'), writer)

    def test_root_child_enumeration_is_private_and_precedes_stale_shape_gate(self) -> None:
        resolver = (
            NATIVE / "src" / "raiktor_surrender_truce_v1.cpp"
        ).read_text(encoding="utf-8")
        writer = (NATIVE / "src" / "ck3_11906.cpp").read_text(
            encoding="utf-8"
        )
        header = (
            NATIVE
            / "include"
            / "xar_bridge"
            / "raiktor_surrender_truce_v1.hpp"
        ).read_text(encoding="utf-8")

        helper = resolver.index("void CaptureLoadedRootChildrenForG2(")
        helper_guard = resolver.rfind(
            "#if defined(XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1)", 0, helper
        )
        self.assertGreaterEqual(helper_guard, 0)
        call = resolver.index("CaptureLoadedRootChildrenForG2(", helper + 1)
        stale_gate = resolver.index(
            'XAR_G2_SHAPE_STAGE("root_capacity_mismatch")', call
        )
        self.assertLess(call, stale_gate)
        self.assertIn(
            "child_vtable == environment.scripted_effect_vtable", resolver
        )
        self.assertIn("std::array<std::uintptr_t, 16> root_child_vtables", header)

        for field in (
            '"root_child_capture_status"',
            '"root_child_capture_completed"',
            '"root_child_vtable_rvas"',
            '"root_scripted_match_count"',
            '"root_scripted_match_index"',
        ):
            self.assertIn(field.replace('"', '\\"'), writer)

    def test_only_five_candidates_receive_private_shape_capture(self) -> None:
        resolver = (
            NATIVE / "src" / "raiktor_surrender_truce_v1.cpp"
        ).read_text(encoding="utf-8")
        writer = (NATIVE / "src" / "ck3_11906.cpp").read_text(
            encoding="utf-8"
        )

        self.assertRegex(
            resolver,
            r"kPrivateScriptedCandidateIndices\s*=\s*\{\s*"
            r"6,\s*7,\s*9,\s*10,\s*11\s*\}",
        )
        call = resolver.index("CaptureLoadedScriptedCandidatesForG2(", 1)
        call = resolver.index(
            "CaptureLoadedScriptedCandidatesForG2(", call + 1
        )
        stale_gate = resolver.index(
            'XAR_G2_SHAPE_STAGE("root_capacity_mismatch")', call
        )
        self.assertLess(call, stale_gate)
        self.assertIn("kDefeatRootCapacity = 19", resolver)
        self.assertIn("kDefeatRootCount = 14", resolver)
        self.assertIn("kDefeatRootTruceScriptIndex = 9", resolver)

        for field in (
            '"scripted_candidate_capture_completed"',
            '"scripted_semantic_match_count"',
            '"scripted_semantic_match_root_index"',
            '"scripted_candidates"',
            '"selector_count"',
            '"template_vtable_rva"',
            '"default_capacity"',
            '"default_count"',
            '"semantic_shape_match"',
        ):
            self.assertIn(field.replace('"', '\\"'), writer)


if __name__ == "__main__":
    unittest.main()
