#!/usr/bin/env python3
"""Build the DEV21 construction runtime in normal and optimized modes."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _visual_studio_environment() -> dict[str, str]:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "")) / (
        "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    _require(vswhere.is_file(), f"vswhere was not found: {vswhere}")
    query = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    installation = Path(query.stdout.strip())
    vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
    _require(vcvars.is_file(), f"vcvars64.bat was not found: {vcvars}")
    with tempfile.TemporaryDirectory(prefix="xar-msvc-environment-") as temporary:
        script = Path(temporary) / "capture-msvc-environment.cmd"
        script.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
        captured = subprocess.run(
            ["cmd.exe", "/d", "/c", str(script)],
            check=True,
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="replace",
        )
    environment = os.environ.copy()
    for line in captured.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    environment["XAR_DEV21_CMAKE"] = str(
        installation
        / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
    )
    environment["XAR_DEV21_NINJA"] = str(
        installation / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
    )
    return environment


def _compile_and_run(
    native_bridge: Path,
    build: Path,
    mode: str,
    flags: list[str],
    environment: dict[str, str],
) -> None:
    research = native_bridge / "research"
    source = native_bridge / "src"
    include = native_bridge / "include"
    output = build / f"domain-construction-application-main-{mode}.exe"
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    _require(compiler is not None, "cl.exe was not present in the vcvars64 environment")
    names = [
        "domain_construction_candidate_identity_decoder_v1.cpp",
        "domain_construction_candidate_cost_legality_decoder_v1.cpp",
        "domain_construction_cost_legality_collector_source_adapter_v1.cpp",
        "domain_construction_cost_legality_live_observer_v1.cpp",
        "domain_construction_semantic_action_core_v1.cpp",
        "domain_construction_native_submit_adapter_v1.cpp",
    ]
    command = [
        compiler,
        "/nologo",
        "/std:c++20",
        "/W4",
        "/WX",
        "/permissive-",
        "/EHsc",
        "/UNDEBUG",
        "/DNOMINMAX",
        "/DWIN32_LEAN_AND_MEAN",
        *flags,
        f"/I{include}",
        f"/I{research}",
        f"/I{source}",
        *(str(research / name) for name in names),
        str(source / "domain_construction_shared_glue_v1.cpp"),
        str(source / "domain_construction_application_main_runtime_v1.cpp"),
        str(source / "domain_construction_application_main_runtime_v1_test.cpp"),
        f"/Fe:{output}",
    ]
    subprocess.run(command, cwd=build, env=environment, check=True)
    subprocess.run([str(output)], cwd=build, env=environment, check=True)
    print(f"domain-construction-application-main-{mode}: GREEN_W4WX")


def _link_default_bridge(
    native_bridge: Path,
    build: Path,
    ck3_executable: Path,
    environment: dict[str, str],
) -> None:
    _require(ck3_executable.is_file(), f"CK3 executable was not found: {ck3_executable}")
    cmake = Path(environment["XAR_DEV21_CMAKE"])
    ninja = Path(environment["XAR_DEV21_NINJA"])
    _require(cmake.is_file(), "Visual Studio cmake.exe was not found")
    _require(ninja.is_file(), "Visual Studio ninja.exe was not found")
    subprocess.run(
        [
            str(cmake),
            "-S",
            str(native_bridge),
            "-B",
            str(build),
            "-G",
            "Ninja",
            f"-DCMAKE_MAKE_PROGRAM={ninja}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=ON",
            f"-DXAR_CK3_EXECUTABLE_PATH={ck3_executable}",
        ],
        env=environment,
        check=True,
    )
    subprocess.run(
        [
            str(cmake),
            "--build",
            str(build),
            "--target",
            "xar_ck3_bridge",
            "xar_ck3_main_thread_query_mailbox_v1_test",
            "xar_ck3_domain_construction_application_main_runtime_v1_test",
        ],
        env=environment,
        check=True,
    )
    _require((build / "xar_ck3_bridge.dll").is_file(),
             "default bridge DLL was not linked")
    ctest = cmake.parent / "ctest.exe"
    _require(ctest.is_file(), "Visual Studio ctest.exe was not found")
    subprocess.run(
        [
            str(ctest),
            "--test-dir",
            str(build),
            "--output-on-failure",
            "-R",
            "(main_thread_query_mailbox_v1|domain_construction_application_main_runtime_v1)$",
        ],
        env=environment,
        check=True,
    )
    print("domain-construction-application-main-default-bridge: GREEN_LINK")


def run(root: Path, ck3_executable: Path) -> None:
    native_bridge = root / "ck3_autonomous_player/native_bridge"
    environment = _visual_studio_environment()
    subprocess.run(
        [
            sys.executable,
            str(
                native_bridge
                / "research/test_domain_construction_application_main_runtime_v1_source_contract.py"
            ),
            "--root",
            str(root),
            "--ck3-executable",
            str(ck3_executable),
        ],
        check=True,
    )
    with tempfile.TemporaryDirectory(
        prefix="xar-domain-construction-application-main-"
    ) as temporary:
        build = Path(temporary)
        _compile_and_run(native_bridge, build, "normal", ["/Od"], environment)
        _compile_and_run(native_bridge, build, "optimized", ["/O2"], environment)
    with tempfile.TemporaryDirectory(
        prefix="xar-domain-construction-default-link-"
    ) as temporary:
        _link_default_bridge(
            native_bridge, Path(temporary), ck3_executable, environment
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-executable", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.root.resolve(), arguments.ck3_executable.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
