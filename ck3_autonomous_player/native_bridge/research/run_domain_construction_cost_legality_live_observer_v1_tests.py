#!/usr/bin/env python3
"""Build and run the private construction live observer in two MSVC modes."""

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
    research: Path,
    build: Path,
    mode: str,
    flags: list[str],
    environment: dict[str, str],
) -> None:
    output = build / f"domain-construction-cost-legality-live-observer-{mode}.exe"
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    _require(compiler is not None, "cl.exe was not present in the vcvars64 environment")
    sources = [
        "domain_construction_candidate_identity_decoder_v1.cpp",
        "domain_construction_candidate_cost_legality_decoder_v1.cpp",
        "domain_construction_cost_legality_collector_source_adapter_v1.cpp",
        "domain_construction_cost_legality_live_observer_v1.cpp",
        "domain_construction_cost_legality_live_observer_v1_test.cpp",
    ]
    command = [
        compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
        "/EHsc", "/UNDEBUG", *flags,
        *(str(research / source) for source in sources),
        f"/Fe:{output}",
    ]
    subprocess.run(command, cwd=build, env=environment, check=True)
    subprocess.run([str(output)], cwd=build, env=environment, check=True)
    print(f"domain-construction-cost-legality-live-observer-{mode}: GREEN_W4WX")


def run(root: Path, build_root: Path | None = None) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    environment = _visual_studio_environment()
    if build_root is None:
        with tempfile.TemporaryDirectory(
            prefix="xar-domain-construction-cost-legality-live-observer-"
        ) as temporary:
            build = Path(temporary)
            _compile_and_run(research, build, "normal", ["/Od"], environment)
            _compile_and_run(research, build, "optimized", ["/O2"], environment)
        return
    build_root.mkdir(parents=True, exist_ok=True)
    _compile_and_run(research, build_root, "normal", ["/Od"], environment)
    _compile_and_run(research, build_root, "optimized", ["/O2"], environment)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--build-root", type=Path)
    arguments = parser.parse_args()
    run(arguments.root.resolve(),
        arguments.build_root.resolve() if arguments.build_root else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
