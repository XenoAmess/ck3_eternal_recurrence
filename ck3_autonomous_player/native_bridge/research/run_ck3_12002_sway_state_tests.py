"""Run the new active Sway source, real typed provider and production serializers offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    names = ("ck3_12002.cpp", "ck3_12002_commands.cpp", "ck3_12002_context.cpp",
        "ck3_12002_gift_opinion.cpp", "ck3_12002_sway_state.cpp", "ck3_12002_sway_command.cpp",
        "active_scheme_semantic_action_v1_private.cpp", "ck3_12002_sway_serializer.cpp",
        "ck3_12002_sway_state_test.cpp")
    sources = [native / "src" / name for name in names]
    pins = sources + [native / "src/ck3_12002_sway_command_test.cpp"] + [
        native / "include/xar_bridge" / name for name in
        ("ck3_12002_sway_state.hpp", "ck3_12002_sway_mailbox.hpp", "ck3_12002_sway_command.hpp")]
    exe = output / "sway-state-test.exe"
    compile_command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
        "/O2", "/Gy", "/W4", "/utf-8", "/I" + str(native / "include"), *map(str, sources),
        "/Fe:" + str(exe), "/link", "/OPT:REF"])
    batch = output / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
        compile_command + "\nexit /b %errorlevel%\n", encoding="utf-8")
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=output,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode:
        raise RuntimeError("Compile failed: " + str(output / "build.log"))
    run = subprocess.run([str(exe), str(output)], cwd=output, capture_output=True,
        text=True, encoding="utf-8", errors="replace")
    (output / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    result = {"status": "GREEN" if run.returncode == 0 else "RED",
        "readiness": "static-ready", "actual_active_provider": True,
        "actual_command_provider": True, "actual_serializer": True,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "live_verified": False, "ck3_touched": False, "compiler": "MSVC /O2 /W4",
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins},
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(), "returncode": run.returncode}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip())
    if run.returncode:
        raise RuntimeError("Fixture failed: " + str(output / "test.log"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
