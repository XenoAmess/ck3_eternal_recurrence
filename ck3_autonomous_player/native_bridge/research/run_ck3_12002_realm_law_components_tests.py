"""Compile the 1.20.0.2 independent realm-law component reader without starting CK3."""
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
        output = build / f"realm-law-enact-12002-{mode}.exe"
        for stem, extra, arguments in (
            ("ck3_12002_realm_law_components", [], []),
        ):
            output = build / f"{stem}-{mode}.exe"
            subprocess.run([
                compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
                "/EHsc", "/UNDEBUG", *flags, f"/I{bridge / 'include'}",
                str(bridge / f"src/{stem}.cpp"),
                str(bridge / f"src/{stem}_test.cpp"),
                f"/Fe:{output}", *extra], check=True, cwd=build, env=env)
            subprocess.run([str(output), *arguments], check=True, cwd=build, env=env)
            print(f"{stem}-{mode}: GREEN_W4WX", flush=True)


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
