from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "native_bridge" / "tools" / "build_fresh.ps1"


class NativeBridgeFreshBuildHelperTests(unittest.TestCase):
    def test_source_contract_covers_the_reproduced_incremental_abi_failure(
        self,
    ) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn('generator = "Ninja"', source)
        self.assertIn('$env:VSLANG = "1033"', source)
        self.assertIn("Repair-NinjaMsvcDependencyPrefix", source)
        self.assertIn('return "repaired-2052-utf8"', source)
        self.assertIn('return "direct-2052-utf8"', source)
        self.assertIn('FromBase64String("5rOo5oSPOiDljIXlkKvmlofku7Y6")', source)
        self.assertIn("fresh native bridge build directory already exists", source)
        self.assertIn("Get-NativeBridgeSourceFingerprint", source)
        self.assertIn("ck3_11906.cpp.obj", source)
        self.assertIn("ck3_11906_adapter.cpp.obj", source)
        self.assertIn('"ck3_11906\\.hpp"', source)
        self.assertIn("Ninja did not record ck3_11906.hpp", source)

    @unittest.skipUnless(os.name == "nt", "PowerShell helper targets Windows")
    def test_plan_is_non_mutating_and_declares_fresh_dependency_gates(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory(prefix="xar-native-build-plan-") as temporary:
            build_dir = Path(temporary) / "new-build"
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER),
                    "-BuildDir",
                    str(build_dir),
                    "-PlanOnly",
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
                "vslang-1033-with-2052-utf8-repair",
            )
            self.assertTrue(plan["fresh_directory_required"])
            self.assertTrue(plan["source_fingerprint_required"])
            self.assertEqual(plan["dependency_header"], "ck3_11906.hpp")
            self.assertFalse(build_dir.exists())

    @unittest.skipUnless(os.name == "nt", "PowerShell helper targets Windows")
    def test_2052_only_toolchain_repairs_cmake_mojibake_as_utf8(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory(prefix="xar-native-prefix-") as temporary:
            root = Path(temporary)
            build_dir = root / "configured-build"
            rules = build_dir / "CMakeFiles" / "rules.ninja"
            rules.parent.mkdir(parents=True)
            rules.write_text(
                "rule CXX\n"
                "msvc_deps_prefix = 娉ㄦ剰: 鍖呭惈鏂囦欢:  \n",
                encoding="utf-8",
            )
            compiler = root / "toolchain" / "cl.exe"
            compiler.parent.mkdir(parents=True)
            compiler.touch()
            locale_resource = compiler.parent / "2052" / "clui.dll"
            locale_resource.parent.mkdir()
            locale_resource.touch()

            environment = os.environ.copy()
            environment.update(
                {
                    "XAR_FRESH_HELPER": str(HELPER),
                    "XAR_FRESH_PLAN": str(root / "unused-plan-build"),
                    "XAR_FRESH_FIXTURE_BUILD": str(build_dir),
                    "XAR_FRESH_FIXTURE_COMPILER": str(compiler),
                }
            )
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "$null = . $env:XAR_FRESH_HELPER "
                    "-BuildDir $env:XAR_FRESH_PLAN -PlanOnly; "
                    "$mode = Repair-NinjaMsvcDependencyPrefix "
                    "-BuildRoot $env:XAR_FRESH_FIXTURE_BUILD "
                    "-CompilerPath $env:XAR_FRESH_FIXTURE_COMPILER; "
                    "Write-Output ('MODE=' + $mode)",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )
            self.assertIn("MODE=repaired-2052-utf8", result.stdout)
            repaired = rules.read_text(encoding="utf-8")
            self.assertIn("msvc_deps_prefix = 注意: 包含文件:  ", repaired)
            self.assertNotIn("娉ㄦ剰", repaired)

    @unittest.skipUnless(os.name == "nt", "PowerShell helper targets Windows")
    def test_2052_only_toolchain_accepts_direct_utf8_prefix(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
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

            environment = os.environ.copy()
            environment.update(
                {
                    "XAR_FRESH_HELPER": str(HELPER),
                    "XAR_FRESH_PLAN": str(root / "unused-plan-build"),
                    "XAR_FRESH_FIXTURE_BUILD": str(build_dir),
                    "XAR_FRESH_FIXTURE_COMPILER": str(compiler),
                }
            )
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "$null = . $env:XAR_FRESH_HELPER "
                    "-BuildDir $env:XAR_FRESH_PLAN -PlanOnly; "
                    "$mode = Repair-NinjaMsvcDependencyPrefix "
                    "-BuildRoot $env:XAR_FRESH_FIXTURE_BUILD "
                    "-CompilerPath $env:XAR_FRESH_FIXTURE_COMPILER; "
                    "Write-Output ('MODE=' + $mode)",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )
            self.assertIn("MODE=direct-2052-utf8", result.stdout)
            self.assertEqual(rules.read_text(encoding="utf-8"), original)

    @unittest.skipUnless(os.name == "nt", "PowerShell helper targets Windows")
    def test_existing_build_directory_is_rejected_even_for_a_plan(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory(prefix="xar-native-existing-") as temporary:
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER),
                    "-BuildDir",
                    temporary,
                    "-PlanOnly",
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
