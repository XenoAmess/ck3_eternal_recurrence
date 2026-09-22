from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "native_bridge" / "tools" / "build_fresh.py"


def _load_helper():
    spec = importlib.util.spec_from_file_location("native_build_fresh_for_test", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load fresh-build helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NativeBridgeFreshBuildHelperTests(unittest.TestCase):
    def test_source_contract_covers_the_reproduced_incremental_abi_failure(
        self,
    ) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn('"generator": "Ninja"', source)
        self.assertIn('os.environ["VSLANG"] = "1033"', source)
        self.assertIn("repair_ninja_msvc_dependency_prefix", source)
        self.assertIn('return "repaired-2052-utf8"', source)
        self.assertIn('return "direct-2052-utf8"', source)
        self.assertIn('"5rOo5oSPOiDljIXlkKvmlofku7Y6"', source)
        self.assertIn("fresh native bridge build directory already exists", source)
        self.assertIn("native_bridge_source_fingerprint", source)
        self.assertIn("ck3_11906.cpp.obj", source)
        self.assertIn("ck3_11906_adapter.cpp.obj", source)
        self.assertIn(r"ck3_11906\.hpp", source)
        self.assertIn("Ninja did not record ck3_11906.hpp", source)

    def test_plan_is_non_mutating_and_declares_fresh_dependency_gates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-native-build-plan-") as temporary:
            build_dir = Path(temporary) / "new-build"
            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--build-dir",
                    str(build_dir),
                    "--plan-only",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            plan = json.loads(result.stdout)
            self.assertEqual(plan["generator"], "Ninja")
            self.assertEqual(plan["msvc_output_language"], "1033")
            self.assertEqual(
                plan["msvc_dependency_prefix_strategy"],
                "vslang-1033-with-2052-byte-preserving-repair",
            )
            self.assertTrue(plan["fresh_directory_required"])
            self.assertTrue(plan["source_fingerprint_required"])
            self.assertEqual(plan["dependency_header"], "ck3_11906.hpp")
            self.assertFalse(build_dir.exists())

    def test_robert_build_plan_is_explicit_and_requires_private_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-robert-plan-") as temporary:
            build_dir = Path(temporary) / "new-build"
            base = [
                sys.executable, str(HELPER), "--build-dir", str(build_dir),
                "--plan-only", "--feudal-1066-target-robert",
            ]
            rejected = subprocess.run(
                base, capture_output=True, text=True, encoding="utf-8"
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("requires the private candidate build", rejected.stderr)
            accepted = subprocess.run(
                base + ["--feudal-1066-selected-bookmark-private"],
                check=True, capture_output=True, text=True, encoding="utf-8",
            )
            self.assertTrue(json.loads(accepted.stdout)["feudal_1066_target_robert"])
            self.assertFalse(build_dir.exists())

    def test_2052_only_toolchain_repairs_cmake_mojibake_as_utf8(self) -> None:
        helper = _load_helper()
        with tempfile.TemporaryDirectory(prefix="xar-native-prefix-") as temporary:
            root = Path(temporary)
            build_dir = root / "configured-build"
            rules = build_dir / "CMakeFiles" / "rules.ninja"
            rules.parent.mkdir(parents=True)
            rules.write_text(
                "rule CXX\nmsvc_deps_prefix = 娉ㄦ剰: 鍖呭惈鏂囦欢:  \n",
                encoding="utf-8",
            )
            compiler = root / "toolchain" / "cl.exe"
            compiler.parent.mkdir(parents=True)
            compiler.touch()
            locale_resource = compiler.parent / "2052" / "clui.dll"
            locale_resource.parent.mkdir()
            locale_resource.touch()

            mode = helper.repair_ninja_msvc_dependency_prefix(build_dir, compiler)

            self.assertEqual(mode, "repaired-2052-utf8")
            repaired = rules.read_text(encoding="utf-8")
            self.assertIn("msvc_deps_prefix = 注意: 包含文件:  ", repaired)
            self.assertNotIn("娉ㄦ剰", repaired)

    def test_2052_only_toolchain_accepts_direct_utf8_prefix(self) -> None:
        helper = _load_helper()
        with tempfile.TemporaryDirectory(prefix="xar-native-prefix-direct-") as temporary:
            root = Path(temporary)
            build_dir = root / "configured-build"
            rules = build_dir / "CMakeFiles" / "rules.ninja"
            rules.parent.mkdir(parents=True)
            original = "rule CXX\nmsvc_deps_prefix = 注意: 包含文件:  \n"
            rules.write_text(original, encoding="utf-8")
            compiler = root / "toolchain" / "cl.exe"
            compiler.parent.mkdir(parents=True)
            compiler.touch()
            locale_resource = compiler.parent / "2052" / "clui.dll"
            locale_resource.parent.mkdir()
            locale_resource.touch()

            mode = helper.repair_ninja_msvc_dependency_prefix(build_dir, compiler)

            self.assertEqual(mode, "direct-2052-utf8")
            self.assertEqual(rules.read_text(encoding="utf-8"), original)

    def test_2052_only_toolchain_preserves_cp936_prefix_bytes(self) -> None:
        helper = _load_helper()
        with tempfile.TemporaryDirectory(prefix="xar-native-prefix-cp936-") as temporary:
            root = Path(temporary)
            build_dir = root / "configured-build"
            rules = build_dir / "CMakeFiles" / "rules.ninja"
            rules.parent.mkdir(parents=True)
            before = "# 编译规则\nrule CXX\nmsvc_deps_prefix = ".encode("utf-8")
            prefix = "注意: 包含文件:  "
            after = b"\n  command = cl.exe $in\n"
            rules.write_bytes(before + prefix.encode("cp936") + after)
            compiler = root / "toolchain" / "cl.exe"
            compiler.parent.mkdir(parents=True)
            compiler.touch()
            locale_resource = compiler.parent / "2052" / "clui.dll"
            locale_resource.parent.mkdir()
            locale_resource.touch()

            mode = helper.repair_ninja_msvc_dependency_prefix(build_dir, compiler)

            self.assertEqual(mode, "direct-2052-cp936")
            self.assertEqual(rules.read_bytes(), before + prefix.encode("cp936") + after)

    def test_existing_build_directory_is_rejected_even_for_a_plan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-native-existing-") as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--build-dir",
                    temporary,
                    "--plan-only",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "fresh native bridge build directory already exists",
                result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
