"""Build and execute the actual Sway provider fixture without touching CK3."""
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
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / \
        "Microsoft Visual Studio/Installer/vswhere.exe"
    query = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
                            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                           capture_output=True, text=True, check=True)
    vcvars = Path(query.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / item for item in (
        "ck3_12002.cpp", "ck3_12002_commands.cpp", "ck3_12002_context.cpp",
        "ck3_12002_sway_command.cpp", "ck3_12002_sway_command_test.cpp")]
    source_pins = {str(item): hashlib.sha256(item.read_bytes()).hexdigest() for item in sources}
    header = native / "include/xar_bridge/ck3_12002_sway_command.hpp"
    source_pins[str(header)] = hashlib.sha256(header.read_bytes()).hexdigest()
    exe = output / "sway-command-test.exe"
    command = subprocess.list2cmdline([
        "cl.exe", "/nologo", "/std:c++20", "/EHsc", "/O2", "/W4", "/utf-8",
        "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
    batch = output / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
                     command + '\nexit /b %errorlevel%\n', encoding="utf-8")
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=output,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode:
        raise RuntimeError("Sway fixture compile failed; see " + str(output / "build.log"))
    test = subprocess.run([str(exe)], cwd=output, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    (output / "test.log").write_text(test.stdout + test.stderr, encoding="utf-8")
    result = {"status": "GREEN" if test.returncode == 0 else "RED",
              "readiness": "static-ready" if test.returncode == 0 else "fixture-failed",
              "game_version": "1.20.0.2", "actual_provider_path": True,
              "production_submit_command_copy": True, "local_ck3_touched": False,
              "live_verified": False, "compiler": "MSVC /O2", "returncode": test.returncode,
              "source_sha256": source_pins, "test_exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(test.stdout.strip())
    if test.returncode:
        raise RuntimeError("Sway actual-provider fixture failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
