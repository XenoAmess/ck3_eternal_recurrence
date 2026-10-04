"""Build only the new six-TU observer fixture and run its two registered cases.

Use an assembled repository projection containing ck3_autonomous_player/src,
native_bridge/include and tools/build_release.py. Only the fixture transport is
replayed; no game process, native pipe, window or full bridge DLL is used.
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

sys.dont_write_bytecode = True


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True,
                        help="Repository root, containing ck3_autonomous_player and tools")
    parser.add_argument("--build-dir", type=Path, required=True, help="New attempt directory; it must not exist")
    parser.add_argument("--native-driver", type=Path, required=True, help="The new two-case native fixture source")
    parser.add_argument("--python-consumer", type=Path)
    parser.add_argument("--compiler-helper", type=Path)
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()
    project = args.projection_root.resolve()
    native = project / "ck3_autonomous_player/native_bridge"
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    objects = output / "obj"
    objects.mkdir()
    helper_path = (args.compiler_helper or project / "tools/run_native_msvc.py").resolve()
    consumer_path = (args.python_consumer or native /
                     "research/fixtures/run_siege_phase_event_observer_mcp_fixture.py").resolve()
    sources = [native / "src" / name for name in (
        "ck3_12003_war_occupation.cpp", "war_occupation_targets_v1_serializer.cpp",
        "ck3_12002_world.cpp", "ck3_12002_province.cpp", "ck3_12002_army.cpp",
    )] + [args.native_driver.resolve()]
    report: dict[str, object] = {
        "schema": "ck3-12003-siege-phase-event-observer-production-focused/v1",
        "status": "HARNESS-RED", "readiness": "source-ready",
        "exact_build": {"version": "1.20.0.3", "steam_build": 25652598,
                        "exe_sha256": "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"},
        "projection_root": str(project), "source_pins": [],
        "compile_exit": None, "native_exit": None, "python_exit": None,
        "translation_units": 6, "whole_dll_built": False,
        "game_operations": 0, "sdk_calls_to_game": 0, "pipe_operations": 0,
        "window_operations": 0, "git_mutations": 0, "game_days_advanced": 0,
        "live_validation": False,
    }
    started = time.perf_counter()
    try:
        report["source_pins"] = [pin(path) for path in sources]
        report["compiler_helper"] = pin(helper_path)
        report["python_consumer"] = pin(consumer_path)
        spec = importlib.util.spec_from_file_location("siege_phase_event_fixture_msvc", helper_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("compiler helper import failed")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        environment = helper.child_environment(output)
        environment, compiler = helper.initialize_msvc(
            helper.visual_studio_installation(None, environment), output, environment)
        executable = output / "siege-phase-event-production-fixture.exe"
        command = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc",
                   "/O2", "/DNDEBUG", "/W4", "/WX", "/permissive-", "/utf-8",
                   "/DNOMINMAX", "/Gy", "/MD", f"/MP{args.jobs}",
                   "/I" + str(native / "include"), "/Fo" + str(objects) + "\\",
                   *["/D" + value for value in args.define], *map(str, sources),
                   "/Fe:" + str(executable), "/link", "/OPT:REF", "User32.lib"]
        report["compiler_argv"] = command
        built = subprocess.run(command, cwd=output, env=environment,
                               capture_output=True, timeout=180)
        (output / "compile.log").write_bytes(built.stdout + built.stderr)
        report.update(compile_exit=built.returncode, compile_log=pin(output / "compile.log"))
        if built.returncode:
            raise RuntimeError("new focused production fixture compilation failed")
        report["status"] = "FIXTURE-RED"
        executed = subprocess.run([str(executable), str(wire)], cwd=output,
                                  env=environment, capture_output=True, timeout=30)
        (output / "native.log").write_bytes(executed.stdout + executed.stderr)
        report.update(native_exit=executed.returncode, native_log=pin(output / "native.log"),
                      executable=pin(executable))
        if executed.returncode:
            raise RuntimeError("new native reader/serializer fixture failed")
        counts = re.search(rb"PASS checks=(\d+) cases=(\d+)", executed.stdout)
        packets = [wire / name for name in (
            "available-phase-event-state.json", "no-active-phase-event-state.json",
        )]
        if counts is None or int(counts[2]) != 2 or not all(path.is_file() for path in packets):
            raise RuntimeError("new native fixture did not emit its two declared cases")
        report.update(native_assertions=int(counts[1]), native_cases=2,
                      native_packets=[pin(path) for path in packets])
        report["status"] = "CONSUMER-RED"
        python_command = [sys.executable, str(consumer_path),
                          "--projection-root", str(project), "--native-dir", str(wire),
                          "--output-dir", str(output)]
        report["python_argv"] = python_command
        checked = subprocess.run(python_command, cwd=output, env=environment,
                                 capture_output=True, timeout=90)
        (output / "python.log").write_bytes(checked.stdout + checked.stderr)
        report.update(python_exit=checked.returncode, python_log=pin(output / "python.log"))
        if checked.returncode:
            raise RuntimeError("new registered Python consumer failed")
        consumer_result = json.loads((output / "PYTHON-CONSUMER-RESULT.json").read_text(encoding="utf-8"))
        if consumer_result["status"] != "GREEN" or consumer_result["registered_mcp_calls"] != 2:
            raise RuntimeError("registered consumer did not complete both new cases")
        report.update(status="GREEN", readiness="static-ready",
                      registered_mcp_calls=2, python_assertions=consumer_result["checks"],
                      python_receipt=pin(output / "PYTHON-CONSUMER-RESULT.json"))
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
                      "native_cases": report.get("native_cases"),
                      "registered_mcp_calls": report.get("registered_mcp_calls"),
                      "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
