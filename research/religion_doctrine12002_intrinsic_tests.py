#!/usr/bin/env python3
"""Compile the production Faith-main-Rite reader and actual native DTO fixture."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args(); out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent; native = root / "ck3_autonomous_player/native_bridge"
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    install = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / n for n in ("ck3_12002.cpp",
        "religion_doctrine12002_intrinsic.cpp", "religion_doctrine12002_intrinsic_test.cpp")]
    pins = sources + [native / "include/xar_bridge/religion_doctrine12002_intrinsic.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = out / mode; target.mkdir(exist_ok=True); tmp = target / "tmp"; tmp.mkdir(exist_ok=True)
        exe = target / "faith-main-rite-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/utf-8",
            "/" + mode, "/W4", "/WX", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' + command + '\nexit /b %errorlevel%\n', encoding="utf-8")
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target,
            env=dict(os.environ, TEMP=str(tmp), TMP=str(tmp)), capture_output=True,
            text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        result = subprocess.run([str(exe), str(target)], cwd=target,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wires = {x.name: json.loads(x.read_text(encoding="utf-8")) for x in target.glob("*.json")}
        positive = wires["current-main-rite.json"]
        assert positive["available"] and positive["rite_id"] == 0 and positive["main_rite_id"] == 0x85000002
        assert positive["faith_id"] == 0x83000003 and positive["rows"][1]["doctrine_key"] == 'doctrine_quoted"信'
        assert positive["rows"][1]["group_key"] == "group_b" and positive["rows"][1]["source"] == "faith_main_rite"
        assert wires["known-empty.json"]["available"] and not wires["known-empty.json"]["rows"]
        assert wires["legal-absent.json"]["available"] and wires["legal-absent.json"]["rite_id"] is None
        assert not wires["main-rite-unavailable.json"]["available"]
        runs.append({"mode": mode, "returncode": result.returncode, "stdout": result.stdout.strip(),
            "actual_cpp_wire_cases": len(wires), "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
            "wire_sha256": {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in target.glob("*.json")}})
        print(mode, result.stdout.strip())
    receipt = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "actual_provider": True, "actual_serializer": True,
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(x.relative_to(root)): hashlib.sha256(x.read_bytes()).hexdigest() for x in pins}}
    (out / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
