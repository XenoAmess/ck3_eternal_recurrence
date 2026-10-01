#!/usr/bin/env python3
"""Validate the real new loaded Doctrine catalogue path once in optimized MSVC."""
from __future__ import annotations
import argparse, hashlib, json, os
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
    sources = [native / "src" / n for n in ("ck3_12002.cpp", "religion_doctrine12002_intrinsic.cpp",
        "religion_doctrine12002_catalogue.cpp", "religion_doctrine12002_catalogue_test.cpp")]
    pins = sources + [native / "include/xar_bridge/religion_doctrine12002_catalogue.hpp"]
    temp = out / "tmp"; temp.mkdir(exist_ok=True); exe = out / "doctrine-catalogue-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/utf-8", "/O2",
        "/W4", "/WX", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
    batch = out / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' + command + '\nexit /b %errorlevel%\n', encoding="utf-8")
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=out,
        env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True,
        text=True, encoding="utf-8", errors="replace")
    (out / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode: raise RuntimeError("Compile failed: " + str(out / "build.log"))
    run = subprocess.run([str(exe), str(out)], cwd=out, capture_output=True,
        text=True, encoding="utf-8", errors="replace")
    (out / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode: raise RuntimeError("Fixture failed: " + str(out / "test.log"))
    paths = [out / n for n in ("loaded-catalogue.json", "known-empty.json", "database-unavailable.json")]
    wire = {x.name: json.loads(x.read_text(encoding="utf-8")) for x in paths}
    yes = wire["loaded-catalogue.json"]
    assert yes["available"] and yes["catalogue_complete"] and len(yes["rows"]) == 3
    assert yes["rows"][2]["doctrine_key"] == 'mod_custom_doctrine"信'
    assert yes["rows"][2]["group_key"] == "group_a"
    assert yes["source"] == yes["rows"][2]["source"] == "loaded_doctrine_registry"
    assert wire["known-empty.json"]["catalogue_complete"] and not wire["known-empty.json"]["rows"]
    assert not wire["database-unavailable.json"]["catalogue_complete"]
    sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
    receipt = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "actual_provider": True, "actual_stable_key_resolver": True,
        "actual_serializer": True, "compiler": "MSVC /O2 /W4 /WX", "stdout": run.stdout.strip(),
        "actual_cpp_wire_cases": len(paths), "source_sha256": {str(x.relative_to(root)): sha(x) for x in pins},
        "wire_sha256": {x.name: sha(x) for x in paths}, "fixture_executable_sha256": sha(exe),
        "reused_native_abi": "research/religion_doctrine12002_intrinsic_abi.json",
        "reused_native_abi_sha256": sha(root / "research/religion_doctrine12002_intrinsic_abi.json")}
    (out / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip()); return 0

if __name__ == "__main__": raise SystemExit(main())
