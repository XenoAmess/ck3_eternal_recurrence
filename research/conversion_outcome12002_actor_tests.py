#!/usr/bin/env python3
"""First fixture for the actual conversion-outcome actor provider and serializer."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "ck3_12002_actor_resources.cpp",
        "conversion_outcome12002_actor.cpp", "conversion_outcome12002_actor_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002.hpp", "ck3_12002_religion_context.hpp", "ck3_12002_actor_resources.hpp",
        "conversion_outcome12002_actor.hpp")]

    def cell(mode):
        target = out / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        exe = target / "conversion-outcome-actor-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode:
            return {"mode": mode, "status": "RED", "phase": "compile", "returncode": build.returncode}
        run = subprocess.run([str(exe), str(target)], cwd=target, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        wires = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in target.glob("*.json")}
        if not run.returncode:
            before, after = wires["before.json"], wires["after.json"]
            zero, missing = wires["legal-zero-wallet.json"], wires["resources-unavailable.json"]
            if not (before["available"] and before["current_religion"]["rite_id"] == 0 and
                    before["piety_raw"] == 0 and before["gold_raw"] == -123456 and
                    before["prestige_raw"] == -7654321 and before["raw_scale"] == 100000 and
                    after["current_religion"]["rite_id"] == 0x87000002 and
                    after["piety_raw"] == -17012345 and
                    after["current_religion"]["spiritual_fulfillment_raw"] == -223456 and
                    after["conversion_causality_inferred"] is False and
                    zero["available"] and all(zero[k] == 0 for k in ("piety_raw", "gold_raw", "prestige_raw")) and
                    not missing["available"] and missing["unavailable_reason"] == "resources_unavailable" and
                    missing["current_religion"]["available"] and
                    all(missing[k] is None for k in ("piety_raw", "gold_raw", "prestige_raw"))):
                raise ValueError("Actual actor JSON lost current signed values, nulls or independent outcome semantics")
        return {"mode": mode, "status": "GREEN" if not run.returncode else "RED", "phase": "fixture",
            "returncode": run.returncode, "stdout": run.stdout.strip(), "actual_wire_cases": len(wires),
            "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(cell, ("Od", "O2")))
    green = all(r["status"] == "GREEN" for r in runs)
    result = {"status": "GREEN" if green else "RED", "readiness": "static-ready" if green else "research",
        "local_ck3_touched": False, "live_verified": False, "actual_actor_provider": True,
        "actual_reused_core_religion_resources": True, "actual_serializer": True,
        "native_religion_getters_stubbed_in_fixture": True, "old_fixture_suites_rerun": False,
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
