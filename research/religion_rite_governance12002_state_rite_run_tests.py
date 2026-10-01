#!/usr/bin/env python3
"""Compile production stateRite reader/serializer and run owned-object fixtures."""
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
    installation = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installation) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in ["ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "religion_rite_governance12002_state_rite.cpp", "religion_rite_governance12002_state_rite_test.cpp"]]
    pins = sources + [native / "include/xar_bridge/religion_rite_governance12002_state_rite.hpp",
                      native / "include/xar_bridge/ck3_12002_religion_context.hpp"]
    runs = []
    for mode in ["Od", "O2"]:
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "state-rite-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' + command +
                         "\nexit /b %errorlevel%\n", encoding="utf-8")
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Build failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire = {path.name: json.loads(path.read_text()) for path in target.glob("*.json")}
        vassal, zero, absent, failed = [wire[name] for name in
            ["vassal.json", "state-rite-zero.json", "state-rite-unset.json", "state-faith-unavailable.json"]]
        if not (vassal["actor_rite_id"] == 0 and vassal["top_liege_character_id"] == 0x84000006 and
                vassal["player_primary_title"]["state_rite_id"] != vassal["realm_primary_title"]["state_rite_id"] and
                zero["available"] and zero["realm_primary_title"]["state_rite_id"] == 0 and
                absent["available"] and absent["realm_primary_title"]["state_rite_id"] is None and
                not failed["available"] and failed["unavailable_reason"] == "title_state_faith_unavailable"):
            raise ValueError("Actual C++ wire did not preserve realm/own/zero/absence/failure identities")
        runs.append({"mode": mode, "returncode": 0, "stdout": run.stdout.strip(), "actual_wire_cases": len(wire),
                     "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()})
        print(mode, run.stdout.strip())
    receipt = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
               "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
               "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
               "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins}}
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
