#!/usr/bin/env python3
"""Compile/run actual conversion fulfillment provider and serializer fixtures."""
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
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in
        ("ck3_12002.cpp", "ck3_12002_religion_conversion_ai_inputs.cpp", "ck3_12002_religion_conversion_ai_inputs_test.cpp")]
    pins = sources + [native / "include/xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "conversion-ai-inputs-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire_paths = sorted(target.glob("*.json"))
        wire = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
        positive, negative, zero = wire["positive.json"], wire["negative.json"], wire["zero.json"]
        missing, drift = wire["unavailable.json"], wire["frame-changed.json"]
        if not (positive["target_rite_id"] == 0x83000001 and positive["current_rite_id"] == 0 and
                positive["expected_base_change_raw"] == 4600000 and negative["expected_base_change_raw"] == -4600000 and
                zero["available"] and zero["expected_base_change_raw"] == 0 and
                not missing["available"] and missing["expected_base_change_raw"] is None and
                not drift["available"] and drift["unavailable_reason"] == "state_changed" and
                all(not row["is_current_fulfillment"] and not row["is_observed_conversion_gain"] and
                    not row["is_final_ai_desire"] for row in wire.values())):
            raise ValueError("Actual C++ wire lost base/current/outcome/unknown distinctions")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_cases": len(wire), "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "wire_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in wire_paths}})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
