"""Run one focused Release production-reader fixture; never opens CK3."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(build: Path, helper: Path) -> int:
    native = Path(__file__).resolve().parents[1]
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    tempfile.tempdir = str(temporary)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(helper))
    from run_domain_construction_cost_legality_live_observer_v1_tests import (
        _visual_studio_environment,
    )

    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    sources = [native / "src" / name for name in (
        "ck3_12002_construction.cpp",
        "ck3_12002_construction_held.cpp",
        "ck3_12002_construction_full_positive_test.cpp",
    )]
    output = build / "construction-full-positive-Release.exe"
    command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX",
               "/permissive-", "/EHsc", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
               "/O2", "/MD", f'/I{native / "src"}', f'/I{native / "include"}',
               *(str(source) for source in sources), f"/Fe:{output}"]
    compiled = subprocess.run(command, cwd=build, env=environment,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    (build / "compile-Release.log").write_text(
        compiled.stdout + compiled.stderr, encoding="utf-8")
    inputs = [*sources, native / "src" / "ck3_12002_construction.hpp",
              native / "src" / "ck3_12002_construction_authored_income.hpp",
              Path(__file__).resolve()]
    result = {
        "status": "RED", "mode": "Release", "optimization": "/O2",
        "evidence_scope": "production finite-positive reader with synthetic memory/cost callbacks",
        "game_process_started": False, "compiler_argv": command,
        "compile_exit_code": compiled.returncode,
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in inputs],
    }
    if compiled.returncode == 0:
        executed = subprocess.run([str(output)], cwd=build, env=environment,
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace")
        (build / "run-Release.log").write_text(
            executed.stdout + executed.stderr, encoding="utf-8")
        result.update(run_exit_code=executed.returncode,
                      output=executed.stdout.strip(),
                      executable_sha256=sha256(output))
        if executed.returncode == 0:
            result["status"] = "GREEN"
    (build / "result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--msvc-environment-helper-dir", type=Path,
                        default=Path(__file__).resolve().parent)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.build_root.resolve(),
                         arguments.msvc_environment_helper_dir.resolve()))
