#!/usr/bin/env python3
"""Compile and run actual religion context/provider/serializer fixtures with MSVC."""
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
    parser.add_argument("--mode", choices=("Od", "O2"), help="Run only the selected compiler mode")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in
        ("ck3_12002.cpp", "ck3_12002_religion_context.cpp", "ck3_12002_religion_context_test.cpp")]
    pins = sources + [native / "include/xar_bridge/ck3_12002_religion_context.hpp"]
    runs = []
    modes = (args.mode,) if args.mode else ("Od", "O2")
    for mode in modes:
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "religion-context-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode:
            raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        # Read actual C++ serializer output through Python's JSON parser.
        wire = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in target.glob("*.json")}
        zero, absent, missing = wire["current-zero.json"], wire["legal-absent.json"], wire["faith-unavailable.json"]
        if not (zero["rite_id"] == 0 and zero["faith_fervor_raw"] == 0 and
                zero["spiritual_fulfillment_raw"] == 0 and zero["faith_key"] == 'faith"key' and
                zero["religion_id"] == 0x84000005 and zero["religion_key"] == "christianity_religion" and
                absent["rite_id"] is None and
                absent["faith_fervor_raw"] is None and absent["available"] and
                not missing["available"] and missing["faith_fervor_raw"] is None):
            raise ValueError("Actual C++ wire lost zero/absence/full-ref/failure distinction")
        runs.append({"mode": mode, "returncode": run.returncode,
            "stdout": run.stdout.strip(), "actual_wire_cases": len(wire),
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
        "compiler": "MSVC /W4 /WX " + " and ".join("/" + mode for mode in modes), "runs": runs,
        "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
