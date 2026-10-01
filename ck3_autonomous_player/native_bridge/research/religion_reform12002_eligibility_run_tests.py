#!/usr/bin/env python3
"""Run the actual draft eligibility library and serializer fixture, without CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    native = Path(__file__).resolve().parents[1]
    root = native.parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src/religion_reform12002_eligibility.cpp",
               native / "src/religion_reform12002_eligibility_test.cpp"]
    pins = sources + [native / "include/xar_bridge/religion_reform12002_eligibility.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "eligibility-test.exe"
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
        if build.returncode:
            raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in target.glob("*.json")}
        negative, positive = wire["observed-negative"], wire["create-positive"]
        absent = wire["window-unavailable"]
        if not (negative["available"] and negative["can_create_rite"] is False and
                negative["can_edit_rite"] is False and negative["draft_actor_id"] == 0x84000005 and
                positive["can_create_rite"] is True and positive["can_edit_rite"] is False and
                not absent["available"] and absent["can_create_rite"] is None and
                absent["unavailable_reason"] == "current_window_unavailable"):
            raise ValueError("Actual C++ wire lost full identity or negative/unavailable distinction")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
                     "actual_wire_cases": len(wire),
                     "wire_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob("*.json")},
                     "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
              "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
              "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
              "source_sha256": {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
