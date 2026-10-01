#!/usr/bin/env python3
"""Actual member collector caller/reader/serializer fixture; no game access."""
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
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    stem = "religion_rite_governance12002_organization_members"
    sources = [native / "src" / name for name in ("ck3_12002.cpp", stem + ".cpp", stem + "_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / (stem + ".hpp")]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "organization-members-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
                         command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target,
            env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target, capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in target.glob("*.json")}
        current, empty, missing, absent = [wire[name] for name in
            ("current-members.json", "known-empty.json", "title-unavailable.json", "legal-no-rite.json")]
        if not (current["rite_id"] == 0x85000003 and current["faith_id"] == 0x83000002 and
                current["faith_character_ids"] == [0x03000004, 0x87000005, 0x88000006] and
                current["rite_character_ids"] == [0x03000004, 0x88000006] and
                current["county_title_ids"] == [0x89000002] and
                empty["available"] and empty["rite_character_ids"] == [] and empty["county_title_ids"] == [] and
                not missing["available"] and missing["county_title_ids"] == [] and
                absent["available"] and absent["rite_id"] is None):
            raise ValueError("Actual member wire lost scope/full-generation/empty/unavailable distinctions")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
                     "actual_wire_cases": len(wire), "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
              "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
              "native_collector_callbacks": "fixture-owned; exact ABI separately verified",
              "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
              "source_sha256": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
