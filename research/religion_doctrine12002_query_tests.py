#!/usr/bin/env python3
"""Compile the actual current Doctrine query and parse its three real C++ wires."""
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
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    source_names = ["ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "religion_doctrine12002_intrinsic.cpp", "religion_doctrine12002_rite.cpp",
        "religion_doctrine12002_tenet.cpp", "religion_doctrine12002_query.cpp",
        "religion_doctrine12002_query_test.cpp"]
    sources = [native / "src" / name for name in source_names]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_religion_context.hpp", "religion_doctrine12002_intrinsic.hpp",
        "religion_doctrine12002_rite.hpp", "religion_doctrine12002_tenet.hpp",
        "religion_doctrine12002_query.hpp")]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "current-doctrines-test.exe"
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
            raise RuntimeError("Query fixture failed: " + str(target / "test.log"))
        actual = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in target.glob("*.json")}
        positive = actual["current-scopes.json"]
        empty = actual["known-empty.json"]
        unavailable = actual["parameter-unavailable.json"]
        if not (positive["available"] and positive["capture_epoch"] == 77 and
                positive["current_rite"]["rows"][0]["doctrine_key"] == 'doctrine_actor"礼' and
                positive["faith_main_rite"]["rows"][0]["doctrine_key"] == "doctrine_faith_main" and
                positive["current_rite"]["rite_id"] == 0x81000006 and
                positive["faith_main_rite"]["main_rite_id"] == 0x82000007 and
                positive["boolean_parameters"]["current_rite"]["parameters"][0]["key"] == "actor_rule" and
                positive["boolean_parameters"]["faith_main_rite"]["parameters"][0]["key"] == "main_rule" and
                empty["available"] and empty["current_rite"]["rows"] == [] and
                empty["faith_main_rite"]["rows"] == [] and
                not unavailable["available"] and unavailable["unavailable_reason"].startswith("boolean_parameters:")):
            raise ValueError("Actual composed C++ wire lost scope, full ID, native key or failure semantics")
        runs.append({"mode": mode, "returncode": run.returncode, "actual_cross_provider_cases": 3,
            "stdout": run.stdout.strip(), "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "actual_wire_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in target.glob("*.json")}})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_cross_provider_query": True, "actual_serializer": True,
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
