#!/usr/bin/env python3
"""Build and run the shared construction glue in normal and optimized modes."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
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
        [str(vswhere), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
         "installationPath"],
        check=True,
        capture_output=True,
        text=True,
    )
    vcvars = Path(query.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
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
    output = build / f"domain-construction-shared-glue-{mode}.exe"
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    _require(compiler is not None, "cl.exe was not present in the vcvars64 environment")
    command = [
        compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
        "/EHsc", "/UNDEBUG", *flags,
        f"/I{research}", f"/I{source}",
        str(research / "domain_construction_semantic_action_core_v1.cpp"),
        str(research / "domain_construction_native_submit_adapter_v1.cpp"),
        str(source / "domain_construction_shared_glue_v1.cpp"),
        str(source / "domain_construction_shared_glue_v1_test.cpp"),
        f"/Fe:{output}",
    ]
    subprocess.run(command, cwd=build, env=environment, check=True)
    subprocess.run([str(output)], cwd=build, env=environment, check=True)
    print(f"domain-construction-shared-glue-{mode}: GREEN_W4WX")


def run(root: Path) -> None:
    native_bridge = root / "ck3_autonomous_player/native_bridge"
    environment = _visual_studio_environment()
    with tempfile.TemporaryDirectory(
        prefix="xar-domain-construction-shared-glue-"
    ) as temporary:
        build = Path(temporary)
        _compile_and_run(native_bridge, build, "normal", ["/Od"], environment)
        _compile_and_run(native_bridge, build, "optimized", ["/O2"], environment)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    arguments = parser.parse_args()
    run(arguments.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
