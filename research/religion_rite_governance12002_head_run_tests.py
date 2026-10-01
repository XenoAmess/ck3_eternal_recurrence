#!/usr/bin/env python3
"""Run actual Rite-head provider/serializer production fixtures with MSVC Od/O2."""
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
    sources = [native / "src" / name for name in ("ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "religion_rite_governance12002_head.cpp", "religion_rite_governance12002_head_test.cpp")]
    pins = sources + [native / "include/xar_bridge/religion_rite_governance12002_head.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "religion-rite-head-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
                         command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target,
            env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True,
            text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target, capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in target.glob("*.json")}
        current = wire["distinct-heads.json"]; vacant = wire["vacant-title.json"]
        absent = wire["legal-head-absence.json"]; failed = wire["title-unavailable.json"]
        if not (current["actor_rite_id"] == 0 and current["actor_rite_head_character_id"] == 0x84000005 and
                current["faith_main_rite_head_character_id"] == 0x02000006 and
                current["faith_religious_head_title_id"] == 0x88000000 and
                current["faith_religious_head_holder_character_id"] == 0x85000007 and
                vacant["faith_religious_head_title_id"] == 0x88000000 and
                vacant["faith_religious_head_holder_character_id"] is None and
                absent["available"] and absent["actor_rite_head_character_id"] is None and
                not failed["available"] and failed["faith_religious_head_title_id"] is None):
            raise ValueError("Actual C++ wire lost distinct native identity/absence semantics")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
                     "actual_wire_cases": len(wire), "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                     "wire_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                     for path in sorted(target.glob("*.json"))}})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "actual_provider": True,
              "actual_serializer": True, "local_ck3_touched": False, "live_verified": False,
              "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
              "source_sha256": {str(path.relative_to(root)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
