"""Compile actual readonly penalty source and fake native callbacks, without CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    env = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=env.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    suites = []
    files = ("ck3_12002.cpp", "ck3_12002_family_value.cpp",
             "ck3_12002_phase_character.cpp", "ck3_12002_phase_definitions.cpp",
             "ck3_12002_family_obligations_break_penalty.cpp",
             "ck3_12002_family_obligations_break_penalty_test.cpp")
    for mode, flags in (("Debug", ["/Od", "/MDd"]), ("Release", ["/O2", "/MD"])):
        output = build / f"break-penalty-{mode}.exe"
        command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
                   "/EHsc", "/DNOMINMAX", *flags, f"/I{NATIVE / 'include'}",
                   *(str(NATIVE / "src" / name) for name in files), f"/Fe:{output}"]
        completed = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True)
        (build / f"compile-{mode}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"{mode} compile RED: {completed.stdout}{completed.stderr}")
        completed = subprocess.run([str(output)], cwd=build, env=env, capture_output=True, text=True)
        (build / f"run-{mode}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"{mode} fixture RED: {completed.stdout}{completed.stderr}")
        suites.append({"mode": mode, "status": "GREEN", "output": completed.stdout.strip(),
                       "executable_sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
              "local_ck3_touched": False, "evidence_scope": "actual source with synthetic native callbacks",
              "suites": suites}
    (build / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", required=True, type=Path)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
