#!/usr/bin/env python3
"""Compile actual Rite creation cost provider/serializer fixtures; no CK3 access."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    native = here.parent
    root = here.parents[2]
    output = a.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / x for x in ("religion_reform12002_costs.cpp", "religion_reform12002_costs_test.cpp")]
    pins = sources + [native / "include/xar_bridge/religion_reform12002_costs.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        exe = target / "rite-creation-costs-test.exe"
        argv = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
                "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
                *map(str, sources), "/Fe:" + str(exe)]
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
                         subprocess.list2cmdline(argv) + "\nexit /b %errorlevel%\n", encoding="utf-8")
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Fixture compile RED: " + str(target / "build.log"))
        test = subprocess.run([str(exe), str(target)], cwd=target, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(test.stdout + test.stderr, encoding="utf-8")
        if test.returncode: raise RuntimeError("Fixture RED: " + str(target / "test.log"))
        wires = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in target.glob("*.json")}
        zero, edit, absent, failed = (wires[x] for x in
            ("zero.json", "editing-affordable.json", "absent-source.json", "native-unavailable.json"))
        if not (len(wires) == 6 and zero["piety_cost_raw"] == 0 and zero["source_rite_id"] == 0 and
                edit["piety_missing_signed_raw"] == -175500000 and edit["source_rite_id"] == 0x84000005 and
                edit["has_enough_piety"] and absent["source_rite_id"] is None and
                failed["piety_cost_raw"] is None and not failed["available"] and
                all(not x["final_creation_legality_observed"] and not x["other_resource_costs_observed"] for x in wires.values())):
            raise ValueError("Actual C++ cost wire lost native zero/absence/signed semantics")
        run = {"mode": mode, "returncode": test.returncode, "stdout": test.stdout.strip(),
               "actual_wire_cases": len(wires), "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
               "wire_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob("*.json")}}
        runs.append(run); print(mode, test.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready library", "local_ck3_touched": False,
              "live_verified": False, "native_exe_callbacks_executed": False,
              "actual_provider": True, "actual_serializer": True, "mcp_registered": False,
              "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
              "source_sha256": {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
