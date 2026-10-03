"""Build and verify the isolated production commander reader and wire fixture.

This helper initializes only the compiler environment. It never discovers or
starts CK3, touches a pipe, changes a window, or builds the full native DLL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"


def pin(path: Path) -> dict:
    payload = path.read_bytes()
    return {"path": str(path), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--source", action="append", type=Path, required=True)
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--python-fixture", type=Path)
    parser.add_argument("--native-only", action="store_true")
    args = parser.parse_args()
    if not args.native_only and args.python_fixture is None:
        parser.error("--python-fixture is required for the full registered MCP check")
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    sys.path.insert(0, str(ROOT / "tools"))
    from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation

    environment = child_environment(output)
    environment, compiler = initialize_msvc(
        visual_studio_installation(None, environment), output, environment)
    sources = [path.resolve() for path in args.source]
    source_pins = [pin(path) for path in sources]
    executable = output / "commander-observer-focused.exe"
    command = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/O2", "/W4", "/WX",
               "/permissive-", "/utf-8", "/DNOMINMAX", "/Gy", "/MD",
               "/I" + str(NATIVE / "include"),
               *["/D" + value for value in args.define],
               *map(str, sources), "/Fe:" + str(executable), "/link", "/OPT:REF", "User32.lib"]
    report = {"schema": "ck3-12003-commander-observer-focused/v1", "status": "HARNESS-RED",
              "readiness": "source-ready", "compiler_argv": command, "source_pins": source_pins,
              "compile_exit": None, "run_exit": None, "python_exit": None,
              "whole_dll_built": False, "local_ck3_touched": False, "sdk_calls": 0,
              "window_operations": 0, "git_mutations": 0,
              "exact_build": {"version": "1.20.0.3", "steam_build": 25652598,
                              "exe_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"},
              "open_kaishek_preflight": {"status": "not-applicable",
                  "reason": "This fixture exercises native C++ memory readers, callbacks and their JSON/MCP transport; no supported parser/IR/runtime subset."}}
    started = time.perf_counter()
    try:
        built = subprocess.run(command, cwd=output, env=environment, capture_output=True, timeout=180)
        (output / "compile.log").write_bytes(built.stdout + built.stderr)
        report.update(compile_exit=built.returncode, compile_log=pin(output / "compile.log"))
        if built.returncode:
            raise RuntimeError("focused production source compile failed")
        report["status"] = "FIXTURE-RED"
        run = subprocess.run([str(executable), str(wire)], cwd=output, env=environment,
                             capture_output=True, timeout=30)
        (output / "run.log").write_bytes(run.stdout + run.stderr)
        report.update(run_exit=run.returncode, run_log=pin(output / "run.log"), executable=pin(executable))
        if run.returncode:
            raise RuntimeError("production reader/serializer fixture failed")
        counts = re.search(rb"PASS checks=(\d+) cases=(\d+)", run.stdout)
        payloads = sorted(wire.glob("*.json"))
        if counts is None or len(payloads) != int(counts[2]):
            raise RuntimeError("fixture did not emit all completed native cases")
        report.update(native_assertions=int(counts[1]), native_cases=int(counts[2]),
                      native_json=[pin(path) for path in payloads])
        if not args.native_only:
            python_command = [sys.executable, str(args.python_fixture.resolve()),
                              "--projection-root", str(ROOT), "--native-dir", str(wire)]
            checked = subprocess.run(python_command, cwd=output, env=environment,
                                     capture_output=True, timeout=60)
            (output / "python.log").write_bytes(checked.stdout + checked.stderr)
            report.update(python_argv=python_command, python_exit=checked.returncode,
                          python_log=pin(output / "python.log"),
                          python_fixture=pin(args.python_fixture.resolve()))
            if checked.returncode:
                raise RuntimeError("registered Python MCP fixture failed")
        if source_pins != [pin(path) for path in sources]:
            raise RuntimeError("focused source changed during the build/run")
        report.update(status="NATIVE-GREEN" if args.native_only else "GREEN",
                      readiness="source-ready" if args.native_only else "static-ready")
    except Exception as error:
        report["error"] = repr(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
                      "error": report.get("error"), "native_cases": report.get("native_cases")}, indent=2))
    return 0 if report["status"] in {"GREEN", "NATIVE-GREEN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
