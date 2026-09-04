#!/usr/bin/env python3
"""Build and verify the G2 actual-expiry candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run(command: list[str], *, cwd: Path, environment=None) -> None:
    print("+", subprocess.list2cmdline(command))
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def find_cmake(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    visual_studio = Path(
        r"C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE"
        r"\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    )
    if visual_studio.is_file():
        return visual_studio
    discovered = shutil.which("cmake")
    if discovered is None:
        raise SystemExit("cmake was not found")
    return Path(discovered).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--cmake", type=Path)
    parser.add_argument("--generator", default="Visual Studio 18 2026")
    parser.add_argument("--configuration", default="Release")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    native = Path(__file__).resolve().parents[1]
    project = native.parent
    repository = project.parent
    exe = args.exe.resolve()
    if not exe.is_file() or exe.name.lower() != "ck3.exe":
        raise SystemExit("--exe must name the frozen ck3.exe")
    observed_exe_hash = sha256(exe)
    if observed_exe_hash != EXPECTED_EXE_SHA256:
        raise SystemExit(f"unexpected ck3.exe SHA-256: {observed_exe_hash}")

    cmake = find_cmake(args.cmake)
    build = args.build_dir.resolve()
    run(
        [
            str(cmake),
            "-S",
            str(native),
            "-B",
            str(build),
            "-G",
            args.generator,
            "-A",
            "x64",
            "-DBUILD_TESTING=ON",
            "-DXAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=ON",
        ],
        cwd=repository,
    )
    targets = [
        "xar_ck3_raiktor_actual_truce_expiry_v1_test",
        "xar_ck3_adapter_registry_test",
        "xar_ck3_bridge",
    ]
    run(
        [
            str(cmake),
            "--build",
            str(build),
            "--config",
            args.configuration,
            "--target",
            *targets,
        ],
        cwd=repository,
    )

    configuration = build / args.configuration
    native_test = configuration / "xar_ck3_raiktor_actual_truce_expiry_v1_test.exe"
    registry_test = configuration / "xar_ck3_adapter_registry_test.exe"
    bridge_dll = configuration / "xar_ck3_bridge.dll"
    for path in (native_test, registry_test, bridge_dll):
        if not path.is_file():
            raise SystemExit(f"candidate output missing: {path}")
    run([str(native_test)], cwd=repository)
    run([str(registry_test)], cwd=repository)

    python_environment = os.environ.copy()
    python_environment["PYTHONPATH"] = str(project / "src")
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.unit.test_raiktor_actual_truce_expiry_contract",
            "tests.unit.test_g2_actual_truce_expiry_source_contract",
        ],
        cwd=project,
        environment=python_environment,
    )
    run(
        [
            sys.executable,
            str(native / "research" / "extract_g2_actual_truce_expiry_abi.py"),
            "--exe",
            str(exe),
            "--check",
        ],
        cwd=repository,
    )

    cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
    if "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1:BOOL=ON" not in cache:
        raise SystemExit("candidate option was not enabled in CMakeCache.txt")
    cmake_source = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    option_block = (
        "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1\n"
        "  \"Advertise the exact-build read-only persisted truce-expiry candidate\"\n"
        "  OFF"
    )
    if option_block not in cmake_source:
        raise SystemExit("candidate option no longer defaults to OFF")

    artifact = {
        "schema": "xar.ck3.g2_actual_truce_expiry_preflight.v1",
        "result": "GREEN",
        "ck3_launched": False,
        "ck3_attached": False,
        "mutation_sent": False,
        "candidate_default_enabled": False,
        "candidate_build_enabled": True,
        "product_version": "1.19.0.6",
        "executable_sha256": observed_exe_hash,
        "configuration": args.configuration,
        "bridge_dll": {
            "path": str(bridge_dll),
            "sha256": sha256(bridge_dll),
        },
        "checks": [
            "exact-build ABI --check",
            "focused Python schema/source contracts",
            "native provider fixture",
            "candidate adapter registry",
            "candidate DLL compile",
            "CMake default OFF",
        ],
        "live_checkpoint_required": True,
    }
    output = (
        args.output.resolve()
        if args.output is not None
        else build / "g2_actual_truce_expiry_preflight.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
