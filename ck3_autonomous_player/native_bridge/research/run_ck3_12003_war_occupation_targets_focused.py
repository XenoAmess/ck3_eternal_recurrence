"""Verify the real war-occupation memory reader, serializer and Python consumer.

Only owned fixture storage and an isolated source projection are used. This
helper does not discover a game process, open a pipe or manipulate a window.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time


EXACT_BUILD = {
    "version": "1.20.0.3",
    "steam_build": 25652598,
    "exe_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
}


def pin(path: Path) -> dict:
    payload = path.read_bytes()
    return {"path": str(path), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--python-consumer", type=Path)
    parser.add_argument("--compiler-helper", type=Path)
    args = parser.parse_args()
    project = args.projection_root.resolve()
    native = project / "ck3_autonomous_player/native_bridge"
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    compiler_helper = (args.compiler_helper or project / "tools/run_native_msvc.py").resolve()
    python_consumer = (args.python_consumer or native /
                       "research/fixtures/run_war_occupation_targets_mcp_fixture.py").resolve()
    helper_spec = importlib.util.spec_from_file_location(
        "occupation_fixture_msvc", compiler_helper)
    if helper_spec is None or helper_spec.loader is None:
        raise RuntimeError("compiler helper import failed")
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    environment = helper.child_environment(output)
    environment, compiler = helper.initialize_msvc(
        helper.visual_studio_installation(None, environment), output, environment)
    sources = [path.resolve() for path in args.source] if args.source else [native / "src" / name for name in (
        "ck3_12003_war_occupation.cpp", "war_occupation_targets_v1_serializer.cpp",
        "ck3_12003_war_occupation_targets_test.cpp", "ck3_12002_world.cpp",
        "ck3_12002_province.cpp", "ck3_12002_army.cpp",
    )]
    source_pins = [pin(path) for path in sources]
    executable = output / "war-occupation-production-fixture.exe"
    command = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/O2",
               "/DNDEBUG", "/W4", "/WX", "/permissive-", "/utf-8",
               "/DNOMINMAX", "/Gy", "/MD", "/I" + str(native / "include"),
               *["/D" + value for value in args.define], *map(str, sources),
               "/Fe:" + str(executable), "/link", "/OPT:REF", "User32.lib"]
    report = {"schema": "ck3-12003-war-occupation-production-fixture/v1",
              "status": "HARNESS-RED", "readiness": "source-ready",
              "exact_build": EXACT_BUILD, "projection": str(project),
              "compiler_argv": command, "source_pins": source_pins,
              "compiler_helper": pin(compiler_helper),
              "compile_exit": None, "run_exit": None, "python_exit": None,
              "whole_dll_built": False, "game_operations": 0,
              "sdk_calls": 0, "window_operations": 0, "git_mutations": 0,
              "game_days_advanced": 0}
    started = time.perf_counter()
    try:
        built = subprocess.run(command, cwd=output, env=environment,
                               capture_output=True, timeout=180)
        (output / "compile.log").write_bytes(built.stdout + built.stderr)
        report.update(compile_exit=built.returncode,
                      compile_log=pin(output / "compile.log"))
        if built.returncode:
            raise RuntimeError("focused production fixture compilation failed")
        report["status"] = "FIXTURE-RED"
        run = subprocess.run([str(executable), str(wire)], cwd=output,
                             env=environment, capture_output=True, timeout=30)
        (output / "run.log").write_bytes(run.stdout + run.stderr)
        report.update(run_exit=run.returncode, run_log=pin(output / "run.log"),
                      executable=pin(executable))
        if run.returncode:
            raise RuntimeError("production reader/serializer fixture failed")
        counts = re.search(rb"PASS checks=(\d+) cases=(\d+)", run.stdout)
        packets = sorted(wire.glob("*.json"))
        if counts is None or len(packets) != int(counts[2]):
            raise RuntimeError("fixture did not emit all native cases")
        report.update(native_assertions=int(counts[1]), native_cases=int(counts[2]),
                      native_json=[pin(path) for path in packets])
        python_command = [sys.executable, str(python_consumer),
                          "--projection-root", str(project),
                          "--native-dir", str(wire)]
        checked = subprocess.run(python_command, cwd=output, env=environment,
                                 capture_output=True, timeout=60)
        (output / "python.log").write_bytes(checked.stdout + checked.stderr)
        report.update(python_exit=checked.returncode, python_argv=python_command,
                      python_log=pin(output / "python.log"),
                      python_consumer=pin(python_consumer))
        if checked.returncode:
            raise RuntimeError("production Python consumer failed")
        if source_pins != [pin(path) for path in sources]:
            raise RuntimeError("owned source changed during fixture execution")
        report.update(status="GREEN", readiness="static-ready")
    except Exception as error:
        report["error"] = repr(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
                      "error": report.get("error"),
                      "native_cases": report.get("native_cases")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
