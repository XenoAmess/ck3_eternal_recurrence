"""Compile the 1.20.0.2 building command binding without starting CK3."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess


def run(root: Path, build: Path) -> None:
    build.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "")) / (
        "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    found = subprocess.run([
        str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
        "installationPath"], check=True, capture_output=True, text=True)
    vcvars = Path(found.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    capture = build / "capture-msvc.cmd"
    capture.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
    result = subprocess.run([
        r"C:\Windows\System32\cmd.exe", "/d", "/c", str(capture)],
        check=True, capture_output=True, text=True, encoding="mbcs")
    env = os.environ.copy()
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            env[key.upper()] = value
    compiler = shutil.which("cl.exe", path=env.get("PATH"))
    if not compiler:
        raise RuntimeError("MSVC cl.exe is unavailable")
    bridge = root / "ck3_autonomous_player/native_bridge"
    for mode, flags in (("normal", ["/Od"]), ("optimized", ["/O2"])):
        output = build / f"construction-submit-12002-{mode}.exe"
        subprocess.run([
            compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
            "/EHsc", "/UNDEBUG", *flags, f"/I{bridge / 'include'}",
            str(bridge / "research/ck3_12002_construction_submit_binding.cpp"),
            str(bridge / "research/ck3_12002_construction_submit_binding_test.cpp"),
            str(bridge / "src/player_world_building_action_candidate_v1.cpp"),
            f"/Fe:{output}"], check=True, cwd=build, env=env)
        subprocess.run([str(output)], check=True, cwd=build, env=env)
        print(f"construction-submit-12002-{mode}: GREEN_W4WX", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--build-root", type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.build_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
