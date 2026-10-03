"""Build only the new production commander speed reader/serializer/MCP fixture."""
from __future__ import annotations

import argparse
import ctypes
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
    data = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--compiler-tools-root", type=Path, default=ROOT / "tools")
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    sys.pycache_prefix = str(output / ".python-cache")
    sys.path.insert(0, str(args.compiler_tools_root))
    from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation
    environment = child_environment(output)
    environment, compiler = initialize_msvc(visual_studio_installation(None, environment), output, environment)
    sources = [NATIVE / "src" / name for name in (
        "ck3_12002_army.cpp", "ck3_12003_commander.cpp", "ck3_12003_commander_mailbox.cpp",
        "ck3_12002_query_mailbox.cpp", "ck3_12003_abi_profile.cpp",
        "ck3_12003_commander_movement_speed_test.cpp")]
    executable = output / "commander-movement-speed-focused.exe"
    command = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/O2", "/W4", "/WX",
        "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/Gy", "/MD",
        "/I" + str(NATIVE / "include"), *map(str, sources), "/Fe:" + str(executable),
        "/link", "/OPT:REF", "User32.lib"]
    python_fixture = NATIVE / "research/fixtures/run_commander_movement_speed_mcp_fixture.py"
    consumed = sources + [NATIVE / "include/xar_bridge/ck3_12003_commander.hpp",
        ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/army_commander_candidates.py",
        ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
        ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
        ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py", python_fixture]
    report = {"schema": "ck3-12003-commander-movement-speed-focused/v1", "status": "HARNESS-RED",
        "readiness": "source-ready", "compiler_argv": command,
        "source_pins": [pin(path) for path in consumed], "compile_exit": None,
        "run_exit": None, "python_exit": None,
        "whole_dll_built": False, "local_ck3_touched": False, "sdk_calls": 0,
        "window_operations": 0, "git_mutations": 0, "old_fixture_runs": 0,
        "exact_build": {"version": "1.20.0.3", "steam_build": 25652598,
            "exe_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"},
        "native_execution_boundary": "Production C++ reader/serializer with synthetic memory and callback replacements; no CK3 native function executes."}
    started = time.perf_counter()
    try:
        # Keep the compiler launch short; MSVC reads exact arguments from its own
        # response-file format rather than a quoted long Windows command line.
        short_buffer = ctypes.create_unicode_buffer(32768)
        short_size = ctypes.windll.kernel32.GetShortPathNameW(
            str(compiler["cl"]), short_buffer, len(short_buffer))
        if not 0 < short_size < len(short_buffer):
            raise RuntimeError("installed compiler short path is unavailable")
        response_file = output / "compile.rsp"
        # MSVC requires the /link tail on this same line; otherwise later lines
        # are reparsed as compiler options rather than linker arguments.
        response_file.write_text(subprocess.list2cmdline(command[1:]) + "\n", encoding="utf-8")
        launch = [short_buffer.value, "@" + str(response_file)]
        report.update(compiler_launch_argv=launch, compiler_response_file=pin(response_file))
        built = subprocess.run(launch, cwd=output, env=environment, capture_output=True, timeout=180)
        (output / "compile.log").write_bytes(built.stdout + built.stderr)
        report.update(compile_exit=built.returncode, compile_log=pin(output / "compile.log"))
        if built.returncode:
            raise RuntimeError("new focused production source compile failed")
        report["status"] = "FIXTURE-RED"
        run = subprocess.run([str(executable), str(wire)], cwd=output, env=environment,
            capture_output=True, timeout=30)
        (output / "run.log").write_bytes(run.stdout + run.stderr)
        report.update(run_exit=run.returncode, run_log=pin(output / "run.log"), executable=pin(executable))
        if run.returncode:
            raise RuntimeError("new production movement-speed reader/serializer fixture failed")
        counts = re.search(rb"PASS checks=(\d+) cases=(\d+)", run.stdout)
        packets = sorted(wire.glob("*.json"))
        if counts is None or int(counts[2]) != 19 or len(packets) != 19:
            raise RuntimeError("new fixture did not emit exactly nineteen production cases")
        report.update(native_assertions=int(counts[1]), native_cases=int(counts[2]),
            native_json=[pin(path) for path in packets])
        python_command = [sys.executable, str(python_fixture), "--projection-root", str(ROOT),
            "--native-dir", str(wire), "--tools-root", str(args.compiler_tools_root)]
        checked = subprocess.run(python_command, cwd=output, env=environment, capture_output=True, timeout=60)
        (output / "python.log").write_bytes(checked.stdout + checked.stderr)
        report.update(python_argv=python_command, python_exit=checked.returncode,
            python_log=pin(output / "python.log"))
        if (output / "REGISTERED-MCP-RESULT.json").is_file():
            report["registered_mcp_result"] = pin(output / "REGISTERED-MCP-RESULT.json")
        if checked.returncode:
            raise RuntimeError("new registered Python MCP speed fixture failed")
        report.update(status="GREEN", readiness="static-ready")
    except Exception as error:
        report["error"] = repr(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
        "error": report.get("error"), "native_cases": report.get("native_cases")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
