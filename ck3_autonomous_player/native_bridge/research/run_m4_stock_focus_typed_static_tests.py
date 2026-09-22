"""Focused /Od and /O2 exact-build stock-focus action tests; never starts CK3."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from run_domain_construction_application_main_runtime_v1_tests import (
    _visual_studio_environment,
)


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
OBJECTS = (
    "CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_lifestyle_formal_precondition_v1.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_lifestyle_formal_wire_v1.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_lifestyle_selection_native_adapter_v1.cpp.obj",
)
TESTS = {
    "precondition": (
        "player_lifestyle_formal_precondition_v1_test.cpp",
        "player_lifestyle_formal_precondition_v1.cpp",
        "player_lifestyle_snapshot_v1.cpp",
        "player_lifestyle_window_candidates_v1.cpp",
        "player_lifestyle_window_source_adapter_v1.cpp",
    ),
    "native-adapter": (
        "player_lifestyle_selection_native_adapter_v1_test.cpp",
        "player_lifestyle_selection_native_adapter_v1.cpp",
        "player_lifestyle_selection_action_v1.cpp",
        "player_lifestyle_window_source_adapter_v1.cpp",
        "player_lifestyle_window_candidates_v1.cpp",
    ),
}


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def _non_c(path: str | Path, label: str) -> Path:
    _need(bool(str(path).strip()), f"{label} is unset")
    value = Path(path).resolve()
    _need(value.drive.upper() not in {"", "C:"}, f"{label} must be non-C")
    return value


def _run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> None:
    result = subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True,
        text=True, errors="replace",
    )
    if result.returncode:
        raise RuntimeError(
            f"focused command failed {result.returncode}: {command}\n"
            f"{result.stdout[-5000:]}\n{result.stderr[-5000:]}"
        )
    if result.stdout.strip():
        print(result.stdout.strip()[-1500:].encode(
            "ascii", errors="backslashreplace").decode("ascii"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--build-root", required=True, type=Path)
    args = parser.parse_args()
    temporary = _non_c(os.environ.get("TEMP", ""), "TEMP")
    _need(temporary == _non_c(os.environ.get("TMP", ""), "TMP"),
          "TEMP/TMP mismatch")
    _need(temporary.is_dir(), "TEMP directory missing")
    executable = args.exe.resolve()
    _need(executable.is_file(), "frozen CK3 EXE missing")
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    _need(digest == EXE_SHA256, "frozen CK3 EXE SHA mismatch")
    build_root = _non_c(args.build_root, "build root")
    build_root.mkdir(parents=True, exist_ok=True)
    native = Path(__file__).resolve().parents[1]
    source = native / "src"
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    _need(compiler is not None, "MSVC compiler unavailable")
    install = Path(environment["VSINSTALLDIR"])
    tools = install / "Common7/IDE/CommonExtensions/Microsoft/CMake"
    cmake = tools / "CMake/bin/cmake.exe"
    ninja = tools / "Ninja/ninja.exe"
    _need(cmake.is_file() and ninja.is_file(), "VS CMake/Ninja unavailable")
    for mode, optimization in (("normal-Debug", "/Od"),
                               ("optimized-Release", "/O2")):
        build = build_root / mode
        build.mkdir(parents=True, exist_ok=True)
        for name, inputs in TESTS.items():
            output = build / f"m4-stock-focus-{name}.exe"
            _run([
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/permissive-", "/EHsc", "/UNDEBUG", optimization,
                f"/I{native / 'include'}",
                *(str(source / entry) for entry in inputs),
                f"/Fe:{output}",
            ], cwd=build, environment=environment)
            _run([str(output)], cwd=build, environment=environment)
            print(f"m4-stock-focus-{name}-{mode}: GREEN")
        _run([
            str(cmake), "-S", str(native), "-B", str(build), "-G", "Ninja",
            f"-DCMAKE_MAKE_PROGRAM={ninja}",
            f"-DCMAKE_BUILD_TYPE={mode.split('-')[1]}",
            "-DBUILD_TESTING=OFF", f"-DXAR_CK3_EXECUTABLE_PATH={executable}",
            "-DXAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1=ON",
        ], cwd=build, environment=environment)
        _run([str(ninja), "-C", str(build), "-j", "1", *OBJECTS],
             cwd=build, environment=environment)
        print(f"m4-stock-focus-private-bridge-{mode}: GREEN_FOCUSED_OBJECTS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
