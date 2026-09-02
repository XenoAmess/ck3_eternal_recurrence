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


if __name__ == "__main__":
    unittest.main()
