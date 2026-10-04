"""Two production army movement reader/serializer/normalizer cases, offline only."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
import types


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def consume(args) -> int:
    """Call the production normalizer; replace no normalizer implementation."""
    sys.dont_write_bytecode = True
    source = args.source_root / "ck3_autonomous_player/src"
    for name, directory in (("xar_autoplayer", source / "xar_autoplayer"),
                            ("xar_autoplayer.bridge", source / "xar_autoplayer/bridge")):
        package = types.ModuleType(name)
        package.__path__ = [str(directory)]
        sys.modules[name] = package
    spec = importlib.util.spec_from_file_location(
        "xar_autoplayer.bridge.war_contract", args.consumer_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("production war consumer cannot be loaded")
    consumer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = consumer
    spec.loader.exec_module(consumer)
    checked = 0

    def require(value, message):
        nonlocal checked
        checked += 1
        if not value:
            raise RuntimeError(message)

    report = {"status": "FIXTURE-RED", "cases": 2,
              "production_consumer": pin(args.consumer_path)}
    try:
        paths = sorted(args.native_dir.glob("*.json"))
        require(len(paths) == 2, "exactly two genuine production serialized cases")
        cases = []
        for path in paths:
            packet = json.loads(path.read_text(encoding="utf-8-sig"))
            rows = consumer.normalize_army_strengths(packet["army_strengths"],
                expected_scope=[{"army_id": 16777217, "scope_role": "player", "war_ids": []}])
            require(rows == packet["army_strengths"], "production consumer preserves the entire genuine row")
            require(rows[0]["status"] == "available", "optional movement observation does not gate strength")
            progress = rows[0]["current_movement_progress"]
            require(progress["source"] == "native_current_route_edge", "observed source remains native")
            for field in ("accumulated_movement_weight_raw", "cached_edge_speed_raw"):
                require(progress[field] == 0, "a read zero Unit operand remains zero")
            operands = ("normalized_edge_progress", "first_route_edge_remaining_duration")
            if path.stem == "movement-progress-zero":
                require(progress["status"] == "available" and progress["unavailable_reason"] is None,
                        "successful zero movement getters are available")
                require(all(progress[key] == {"raw": 0, "scale": 100000} for key in operands),
                        "successful zero ratio and duration retain Q100000")
                legacy = dict(packet["army_strengths"][0])
                legacy.pop("current_movement_progress")
                require(consumer.normalize_army_strengths([legacy]) == [legacy],
                        "older producer omission stays absent")
                legacy["current_movement_progress"] = None
                require(consumer.normalize_army_strengths([legacy]) == [legacy],
                        "older optional null stays null")
            else:
                require(progress["status"] == "unavailable" and isinstance(progress["unavailable_reason"], str),
                        "missing native callbacks remain an unavailable observation")
                require(all(progress[key] is None for key in operands),
                        "unread getter values remain null rather than zero")
            cases.append({"case": path.stem, "status": "GREEN", "packet": pin(path)})
        report.update(status="GREEN", cases=cases, checks=checked,
                      asserts_used=0, readiness="static-ready", sdk_calls=0,
                      native_functions_executed=False)
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc(), checks=checked)
    output = args.native_dir.parent / "PYTHON-NORMALIZER-RESULT.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checked, "receipt": pin(output),
                      "error": report.get("error")}))
    return 0 if report["status"] == "GREEN" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-projection-root", type=Path)
    parser.add_argument("--consumer-path", type=Path, required=True)
    parser.add_argument("--test-source", type=Path)
    parser.add_argument("--reuse-army-object", type=Path)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--native-dir", type=Path)
    args = parser.parse_args()
    if args.native_dir is not None:
        return consume(args)
    if args.build_dir is None or args.test_source is None:
        parser.error("--build-dir and --test-source are required for focused compile")
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    sys.pycache_prefix = str(output / ".python-cache")
    sys.path.insert(0, str(args.source_root / "tools"))
    from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation
    environment = child_environment(output)
    environment, compiler = initialize_msvc(visual_studio_installation(None, environment), output, environment)
    native = args.source_root / "ck3_autonomous_player/native_bridge"
    projected = (args.native_projection_root / "ck3_autonomous_player/native_bridge"
                 if args.native_projection_root else native)
    source = projected / "src/ck3_12002_army.cpp"
    if not source.is_file():
        source = native / "src/ck3_12002_army.cpp"
    executable = output / "army-movement-progress-focused.exe"
    command = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/O2", "/W4", "/WX",
               "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/Gy", "/MD",
               "/I" + str(projected / "include"), "/I" + str(native / "include"),
               str(args.reuse_army_object or source), str(args.test_source), "/Fe:" + str(executable),
               "/link", "/OPT:REF", "User32.lib"]
    report = {"schema": "ck3-12003-army-movement-progress-focused/v1", "status": "HARNESS-RED",
              "readiness": "source-ready", "compiler_argv": command,
              "compile_exit": None, "run_exit": None, "python_exit": None,
              "source_pins": [pin(path) for path in (source, args.test_source, args.consumer_path)],
              "whole_dll_built": False, "local_ck3_touched": False, "sdk_calls": 0,
              "window_operations": 0, "git_mutations": 0, "old_fixture_runs": 0,
              "native_translation_units": 2,
              "compiled_translation_units": 1 if args.reuse_army_object else 2,
              "reused_production_object": pin(args.reuse_army_object) if args.reuse_army_object else None,
              "exact_build": {"version": "1.20.0.3", "steam_build": 25652598,
                "exe_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"},
              "native_execution_boundary": "Production reader and serializer; synthetic memory/callback replacements. No CK3 functions execute."}
    started = time.perf_counter()
    try:
        short_buffer = ctypes.create_unicode_buffer(32768)
        short_size = ctypes.windll.kernel32.GetShortPathNameW(str(compiler["cl"]), short_buffer, len(short_buffer))
        if not 0 < short_size < len(short_buffer):
            raise RuntimeError("installed compiler short path is unavailable")
        response = output / "compile.rsp"
        response.write_text(subprocess.list2cmdline(command[1:]) + "\n", encoding="utf-8")
        launch = [short_buffer.value, "@" + str(response)]
        report.update(compiler_launch_argv=launch, compiler_response_file=pin(response))
        compiled = subprocess.run(launch, cwd=output, env=environment, capture_output=True, timeout=180)
        (output / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        report.update(compile_exit=compiled.returncode, compile_log=pin(output / "compile.log"))
        if compiled.returncode:
            raise RuntimeError("focused production compile failed")
        report["status"] = "FIXTURE-RED"
        run = subprocess.run([str(executable), str(wire)], cwd=output, env=environment, capture_output=True, timeout=30)
        (output / "run.log").write_bytes(run.stdout + run.stderr)
        report.update(run_exit=run.returncode, run_log=pin(output / "run.log"), executable=pin(executable))
        if run.returncode:
            raise RuntimeError("new movement reader/serializer fixture failed")
        counts = re.search(rb"PASS checks=(\d+) cases=(\d+)", run.stdout)
        packets = sorted(wire.glob("*.json"))
        if counts is None or int(counts[2]) != 2 or len(packets) != 2:
            raise RuntimeError("fixture must emit exactly two production cases")
        report.update(native_assertions=int(counts[1]), native_cases=2,
                      native_json=[pin(path) for path in packets])
        checked = subprocess.run([sys.executable, "-B", "-O", str(Path(__file__).resolve()),
            "--source-root", str(args.source_root), "--consumer-path", str(args.consumer_path),
            "--native-dir", str(wire)], cwd=output, env=environment, capture_output=True, timeout=60)
        (output / "python.log").write_bytes(checked.stdout + checked.stderr)
        report.update(python_exit=checked.returncode, python_log=pin(output / "python.log"))
        if (output / "PYTHON-NORMALIZER-RESULT.json").is_file():
            report["python_result"] = pin(output / "PYTHON-NORMALIZER-RESULT.json")
        if checked.returncode:
            raise RuntimeError("production Python normalizer fixture failed")
        report.update(status="GREEN", readiness="static-ready")
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
                      "error": report.get("error"), "native_cases": report.get("native_cases")}))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
