#!/usr/bin/env python3
"""Compile and run the isolated army reader fixtures with x64 MSVC C++20.

Only the army producer, its readonly supply dependencies and fixture test are linked.
No game executable, native bridge DLL, Steam installation or private feature
definition is used.
The caller supplies a fresh build directory; logs and failures are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from run_native_msvc import child_environment, visual_studio_installation
import register_project_exe_exclusions as defender_exclusions


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ck3_autonomous_player/native_bridge"
TRANSLATION_UNITS = (
    "src/ck3_12002_army.cpp",
    "src/ck3_12003_army_supply_timing.cpp",
    "src/ck3_12003_army_replenishment_records.cpp",
    "src/ck3_12003_current_province_supply_contributors.cpp",
    "src/ck3_12003_current_land_resupply.cpp",
    "src/ck3_12003_current_land_supply_rate.cpp",
    "src/ck3_12003_scoped_ordered_refill_core.cpp",
    "src/ck3_12003_current_province_besieging_contributors.cpp",
    "src/ck3_12003_fixed_chunk0_preparation.cpp",
    "src/ck3_12002_army_test.cpp",
)
INPUTS = (
    *TRANSLATION_UNITS,
    "include/xar_bridge/ck3_12002_army.hpp",
    "include/xar_bridge/ck3_12003_army_supply_timing.hpp",
    "include/xar_bridge/ck3_12003_army_replenishment_records.hpp",
    "include/xar_bridge/ck3_12003_current_province_supply_contributors.hpp",
    "include/xar_bridge/ck3_12003_current_land_resupply.hpp",
    "include/xar_bridge/ck3_12003_current_land_supply_rate.hpp",
    "include/xar_bridge/ck3_12003_scoped_ordered_refill_core.hpp",
    "include/xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp",
    "include/xar_bridge/ck3_12003_current_province_besieging_contributors.hpp",
    "include/xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp",
    "include/xar_bridge/ck3_12002.hpp",
    "include/xar_bridge/ck3_12003.hpp",
    "include/xar_bridge/game_contract.hpp",
)


def run_logged(argv: list[str], name: str, build_dir: Path,
               environment: dict[str, str], report: dict) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=build_dir, env=environment, capture_output=True)
    stdout = build_dir / f"{name}.stdout.bin"
    stderr = build_dir / f"{name}.stderr.bin"
    with stdout.open("xb") as stream:
        stream.write(result.stdout)
    with stderr.open("xb") as stream:
        stream.write(result.stderr)
    step = {"name": name, "argv": argv, "exit_code": result.returncode,
            "stdout": str(stdout), "stderr": str(stderr)}
    report["steps"].append(step)
    print(json.dumps(step), flush=True)
    if result.returncode:
        # Official CI previously hid the actual linker diagnosis in temp files.
        for diagnostic in (result.stdout, result.stderr):
            if diagnostic:
                print(diagnostic.decode("utf-8", errors="replace"), flush=True)
        raise subprocess.CalledProcessError(result.returncode, argv)
    return result


def run(build_dir: Path, requested_vs: Path | None) -> dict:
    if os.name != "nt":
        raise RuntimeError("This gate requires Windows x64 MSVC")
    build_dir = build_dir.resolve()
    build_dir.mkdir(parents=True, exist_ok=False)
    report = {"schema": "xar.native.army-reader-ci.v1", "status": "running",
              "build_dir": str(build_dir), "steps": [],
              "local_ck3_contacted": False, "private_feature_definitions": [],
              "inputs": {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                         for name in INPUTS}}
    try:
        environment = child_environment(build_dir)
        installation = visual_studio_installation(requested_vs, environment)
        vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
        capture = build_dir / ".msvc-temp/capture-environment.cmd"
        with capture.open("x", encoding="utf-8", newline="\r\n") as stream:
            stream.write(f'@echo off\ncall "{vcvars}" >nul\n'
                         'if errorlevel 1 exit /b %errorlevel%\nset\n')
        setup_argv = [environment.get("COMSPEC", "cmd.exe"), "/d", "/u", "/c", str(capture)]
        # Keep the environment in memory; it may contain CI credentials.
        result = subprocess.run(setup_argv, cwd=build_dir, env=environment, capture_output=True)
        report["steps"].append({"name": "msvc-environment", "argv": setup_argv,
                                "exit_code": result.returncode})
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, setup_argv)
        compiler_environment = environment.copy()
        for line in result.stdout.decode("utf-16-le").splitlines():
            if "=" in line and not line.startswith("="):
                key, value = line.split("=", 1)
                compiler_environment[key.upper()] = value
        for key in ("TEMP", "TMP", "PYTHONPYCACHEPREFIX", "XDG_CACHE_HOME",
                    "CCACHE_DIR", "SCCACHE_DIR", "PYTHONUTF8", "PYTHONIOENCODING", "VSLANG"):
            compiler_environment[key] = environment[key]
        # Do not inherit hidden compiler arguments or feature definitions.
        compiler_environment.pop("CL", None)
        compiler_environment.pop("_CL_", None)
        compiler = shutil.which("cl.exe", path=compiler_environment.get("PATH"))
        if compiler is None:
            raise RuntimeError("vcvars64 did not publish cl.exe")
        executable = build_dir / "xar_ck3_12002_army_test.exe"
        argv = [compiler, "/nologo", "/std:c++20", "/O2", "/MD", "/W4",
                "/permissive-", "/EHsc", "/utf-8", "/UNDEBUG",
                f"/I{SOURCE / 'include'}",
                *(str(SOURCE / name) for name in TRANSLATION_UNITS),
                f"/Fe{executable}"]
        run_logged(argv, "compile", build_dir, compiler_environment, report)
        report["build_status"] = "build_succeeded"
        report["defender_exclusions"] = defender_exclusions.after_successful_command_build(
            ROOT, SOURCE, build_dir, argv, [executable])
        if report["defender_exclusions"]["status"] == "settings_failed":
            raise RuntimeError("build succeeded; Defender registration failed: " + json.dumps(report["defender_exclusions"]))
        run_logged([str(executable)], "army-fixtures", build_dir, compiler_environment, report)
        report["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        with (build_dir / "army-reader-ci-result.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--vs-install", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.build_dir, args.vs_install)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "build_dir": report["build_dir"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
