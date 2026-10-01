"""Compile actual alliance-war reader against fixture-owned native callbacks."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
ROOT = NATIVE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run_native_msvc import child_environment, visual_studio_installation, initialize_msvc


def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    sys.pycache_prefix = str(build / ".python-cache")
    environment = child_environment(build)
    installation = visual_studio_installation(None, environment)
    environment, tools = initialize_msvc(installation, build, environment)
    suites = []
    sources = [
        "ck3_12002.cpp", "ck3_12002_commands.cpp", "ck3_12002_context.cpp",
        "ck3_12002_family_obligations_alliance.cpp",
        "ck3_12002_family_obligations_alliance_test.cpp",
    ]
    for name, flags in (("Od", ["/Od", "/MDd"]), ("O2", ["/O2", "/MD"])):
        mode = build / name
        mode.mkdir(exist_ok=True)
        output = mode / "alliance-war-observer.exe"
        arguments = [tools["cl"], "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
                     "/EHsc", "/DNOMINMAX", *flags, f"/I{NATIVE / 'include'}",
                     *[str(NATIVE / "src" / source) for source in sources],
                     f"/Fe:{output}"]
        compiled = subprocess.run(arguments, cwd=mode, env=environment, capture_output=True)
        (mode / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f"{name} compile RED; see {mode / 'compile.log'}")
        result = subprocess.run([str(output)], cwd=mode, env=environment, capture_output=True)
        (mode / "run.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"{name} fixture RED: {(result.stdout + result.stderr).decode('utf-8', errors='replace')}")
        suites.append({"mode": name, "status": "GREEN", "executable_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                       "output": result.stdout.decode("utf-8").strip()})
    report = {"status": "GREEN", "readiness": "static-ready", "process_access": False,
              "live_validation": False, "suites": suites,
              "source_sha256": {name: hashlib.sha256((NATIVE / "src" / name).read_bytes()).hexdigest() for name in sources}}
    (build / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
