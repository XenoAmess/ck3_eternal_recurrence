"""Build/run actual actor-Rite doctrine reader and serializer; no CK3 process."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = a.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in ("ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "religion_doctrine12002_intrinsic.cpp", "religion_doctrine12002_rite.cpp", "religion_doctrine12002_rite_test.cpp")]
    pins = sources + [native / "include/xar_bridge/religion_doctrine12002_rite.hpp",
                      native / "include/xar_bridge/religion_doctrine12002_intrinsic.hpp"]
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "rite-doctrine-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        wire = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in target.glob("*.json")}
        current = wire["rite-effective.json"]
        if not (current["rite_id"] == 0x85000006 and current["faith_id"] == 0x83000003 and
                current["rows"][0]["doctrine_key"] == "doctrine_head_of_faith_spiritual" and
                current["rows"][1]["doctrine_key"] == '教义"\n' and
                all(r["source"] == "rite_effective" for r in current["rows"]) and
                wire["known-empty.json"]["available"] and wire["known-empty.json"]["rows"] == [] and
                wire["legal-absent.json"]["rite_id"] is None and
                not wire["rite-unavailable.json"]["available"]):
            raise ValueError("Actual wire lost effective scope/full identity/empty/failure semantics")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "actual_wire_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob("*.json")}})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "actual_provider": True, "actual_serializer": True,
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
