"""Build the private active-law reader fixture in normal and optimized MSVC."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def run(root: Path, build_root: Path) -> None:
    if build_root.drive.upper() == "C:":
        raise ValueError("build root must be on a writable non-C drive")
    build_root.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ["ProgramFiles(x86)"]) / (
        "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    query = subprocess.run(
        [str(vswhere), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
         "installationPath"],
        check=True, capture_output=True, text=True,
    )
    vcvars = Path(query.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    script = build_root / "capture-msvc-environment.cmd"
    script.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
    base_environment = os.environ.copy()
    base_environment.update({"TEMP": str(build_root), "TMP": str(build_root)})
    captured = subprocess.run(
        ["cmd.exe", "/d", "/c", str(script)],
        env=base_environment, check=True, capture_output=True, text=True,
        encoding="mbcs", errors="replace",
    )
    environment = base_environment.copy()
    for line in captured.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    environment.update({"TEMP": str(build_root), "TMP": str(build_root)})
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC x64 compiler unavailable")
    native = root / "ck3_autonomous_player/native_bridge"
    for mode, flag in (("normal", "/Od"), ("optimized", "/O2")):
        build = build_root / mode
        build.mkdir(exist_ok=True)
        output = build / "realm-law-active-collection-11906-test.exe"
        subprocess.run(
            [compiler, "/nologo", "/std:c++20", "/W4", "/WX",
             "/permissive-", "/EHsc", "/UNDEBUG", flag,
             f"/I{native / 'include'}",
             str(native / "src/realm_law_active_collection_11906.cpp"),
             str(native / "src/realm_law_candidate_collection_11906.cpp"),
             str(native / "src/realm_law_active_collection_11906_test.cpp"),
             f"/Fe:{output}"],
            cwd=build, env=environment, check=True,
        )
        subprocess.run([str(output)], cwd=build, env=environment, check=True)
        print(f"realm_law_active_collection_11906_{mode}: GREEN_W4WX")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--build-root", type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.build_root.resolve())


if __name__ == "__main__":
    main()
