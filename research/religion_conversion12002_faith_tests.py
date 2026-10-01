#!/usr/bin/env python3
"""Build actual Faith conversion-choice reader fixtures; never access CK3."""
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
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in
        ("ck3_12002.cpp", "ck3_12002_religion_conversion_faith.cpp", "ck3_12002_religion_conversion_faith_test.cpp")]
    pins = sources + [native / "include/xar_bridge/ck3_12002_religion_conversion_faith.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = out / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        exe = target / "faith-conversion-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target,
            env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(exe), str(target)], cwd=target, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        packets = {x.name: json.loads(x.read_text(encoding="utf-8")) for x in target.glob("*.json")}
        positive, blocked, absent = packets["choices.json"], packets["rule-blocked.json"], packets["no-main-rite.json"]
        assert positive["choices"][1]["faith_id"] == 0x83000003
        assert positive["choices"][1]["main_rite_id"] == 0x84000001
        assert positive["choices"][1]["faith_key"] == 'target"faith'
        assert positive["rule_only"] and positive["choices"][1]["native_faith_rule_passes"]
        assert not blocked["choices"][1]["native_faith_rule_passes"]
        assert absent["available"] and absent["choices"][1]["main_rite_id"] is None
        assert packets["candidate-unavailable.json"]["choices"] == []
        assert packets["empty.json"]["available"] and packets["empty.json"]["choices"] == []
        rows = {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in packets}
        runs.append({"mode": mode, "stdout": run.stdout.strip(), "actual_wire_cases": len(packets),
            "wire_sha256": rows, "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
        "native_callbacks": "fixture-owned ABI callbacks; no CK3 calls", "runs": runs,
        "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins}}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
