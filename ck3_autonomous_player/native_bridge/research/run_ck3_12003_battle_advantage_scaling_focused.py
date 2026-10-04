"""Two bounded .3 runtime coefficient cases through the production MCP route.

The native reader, wire serializer and registered normalizer stay real. Synthetic
backing memory supplies three observations: positive, zero and unbound null.
An optional manifest reuses unchanged strict-built dependency objects. No old
test case, full DLL, CK3 process or desktop operation is invoked.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

FIELD = "runtime_advantage_scaling_raw"
LOSS = "current_loss_inputs_v1"
SOURCE_NAMES = ["ck3_12003_battle_advantage_scaling_inputs_test.cpp",
                "ck3_12002_battle.cpp", "ck3_12002_combat.cpp",
                "ck3_12002_battle_journal.cpp",
                "battle_control_snapshot_v1_mailbox.cpp"]
DEPENDENCIES = ["ck3_12002_routes.cpp", "battle_terminal_journal_v1.cpp",
                "ck3_12002_phase_character.cpp"]


def require(value: object, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot import " + str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def shared_helpers(project: Path):
    return load_module("advantage_coefficient_existing_protocol_helpers", project /
        "ck3_autonomous_player/native_bridge/research/run_ck3_12002_battle_primary_levy_damage_inputs_focused.py")


def python_check(args: argparse.Namespace) -> int:
    require(sys.flags.optimize > 0, "registered checks require Python -O")
    project = args.project_root.resolve()
    projection = args.projection_root.resolve()
    sys.path.insert(0, str(project / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge

    adapter = projection / "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py"
    load_module("xar_autoplayer.bridge.battle_control_contract", adapter)
    helper = shared_helpers(project)
    document_path = args.native_dir.resolve() / "runtime_advantage_scaling_cases.json"
    document = json.loads(document_path.read_text(encoding="utf-8"))
    require(document.get("schema_version") == 1 and document.get("actual") == 0,
            "focused native document identity changed")
    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) == 2,
            "exactly two bounded cases required")
    require([row.get("name") for row in cases] == ["positive_runtime_coefficient",
            "zero_unavailable_and_legacy_absence"], "focused case order changed")
    expected_variants = [[("positive", 500000)], [("zero", 0), ("unbound_null", None)]]
    consumed = []
    query_count = 0
    native_frame_count = 0
    for case, variants in zip(cases, expected_variants):
        frames = case.get("frames")
        require(isinstance(frames, list) and len(frames) == len(variants),
                "case reader frame count changed")
        outputs = []
        for observed, (variant, coefficient) in zip(frames, variants):
            require(observed.get("variant") == variant, "reader variant changed")
            helper.require_equal(observed.get("expected_runtime_advantage_scaling_raw"),
                                 coefficient, variant + ".hand_expected")
            frame = observed.get("battle_control_snapshot")
            require(isinstance(frame, dict) and isinstance(frame.get(LOSS), dict),
                    "production serializer omitted current-loss body")
            native_frame_count += 1
            loss = frame[LOSS]
            helper.require_equal(loss.get(FIELD), coefficient, variant + ".native_observation")
            require(FIELD in loss, "new serializer omitted unavailable coefficient")
            helper.require_equal(loss["scale"], 100000, variant + ".q100000")
            helper.require_equal(loss["runtime_damage_scaling_raw"], -3007,
                                 variant + ".separate_outgoing_coefficient")
            result = asyncio.run(helper.registered_query(frame))
            query_count += 1
            normalized = result["battle_control_snapshot"][LOSS]
            helper.require_equal(normalized, loss, variant + ".registered_loss_body")
            outputs.append({"variant": variant, "status": "GREEN", "coefficient": coefficient,
                            "native_revision": frame["snapshot_revision"],
                            "battle_control_ready": result["battle_control_ready"]})
            if variant == "zero":
                legacy = copy.deepcopy(frame)
                del legacy[LOSS][FIELD]
                legacy_result = asyncio.run(helper.registered_query(legacy))
                query_count += 1
                legacy_normalized = legacy_result["battle_control_snapshot"][LOSS]
                require(FIELD not in legacy_normalized,
                        "legacy absent coefficient became invented null or zero")
                helper.require_equal(legacy_normalized, legacy[LOSS], "legacy.registered_loss_body")
                outputs.append({"variant": "legacy_absent_key", "status": "GREEN",
                                "new_key_absent": True,
                                "battle_control_ready": legacy_result["battle_control_ready"]})
        consumed.append({"name": case["name"], "status": "GREEN", "observations": outputs})
    require(native_frame_count == 3 and query_count == 4, "focused pipeline counts changed")
    report = {"schema": "ck3-12003-runtime-advantage-scaling-registered-focused/v1",
              "status": "GREEN", "readiness": "static-ready", "python_optimized": True,
              "bounded_cases": 2, "native_reader_frames": 3,
              "registered_mcp_client_calls": 4, "cases": consumed,
              "native_json": pin(document_path), "normalizer": pin(adapter),
              "protocol_helper": pin(project /
                  "ck3_autonomous_player/native_bridge/research/run_ck3_12002_battle_primary_levy_damage_inputs_focused.py"),
              "old_test_cases_run": 0, "live_game_calls": 0, "window_operations": 0}
    args.python_result.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "cases": 2, "native_frames": 3,
                      "registered_calls": 4, "result": pin(args.python_result.resolve())}))
    return 0


def build_native(args: argparse.Namespace, output: Path, report: dict) -> tuple[dict, Path]:
    project = args.project_root.resolve()
    projection = args.projection_root.resolve()
    src = "ck3_autonomous_player/native_bridge/src"
    sources = [(projection / src / name if (projection / src / name).exists()
                else project / src / name) for name in SOURCE_NAMES]
    reused = []
    if args.reuse_manifest:
        manifest = json.loads(args.reuse_manifest.resolve().read_text(encoding="utf-8"))
        rows = manifest["reused"]
        require({Path(row["source"]).name for row in rows} == set(DEPENDENCIES),
                "unexpected reused dependency set")
        for row in rows:
            current_source = project / src / Path(row["source"]).name
            require(pin(current_source)["sha256"] == row["sha256"],
                    "reused dependency source changed")
            obj = Path(row["object"])
            require(pin(obj)["sha256"] == row["object_sha256"] and
                    row["prior_compile_exit"] == 0, "reused strict object changed")
            reused.append({"source": pin(current_source), "object": pin(obj)})
    else:
        sources.extend(project / src / name for name in DEPENDENCIES)
    report["source_pins"] = [pin(path) for path in sources]
    report["reused_dependency_objects"] = reused
    bootstrap = project / "tools/run_native_msvc.py"
    helper = load_module("advantage_scaling_msvc_bootstrap", bootstrap)
    environment = helper.child_environment(output)
    environment, compiler = helper.initialize_msvc(
        helper.visual_studio_installation(None, environment), output, environment)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    prefix = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
              "/O2", "/DNDEBUG", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
              "/DUNICODE", "/D_UNICODE", "/Gy",
              "/I" + str(projection / "ck3_autonomous_player/native_bridge/include"),
              "/I" + str(project / "ck3_autonomous_player/native_bridge/include")]
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def compile_one(source: Path) -> dict:
        obj = output / (source.stem + ".obj")
        log = output / (source.stem + ".compile.log")
        argv = prefix + ["/c", str(source), "/Fo" + str(obj)]
        result = subprocess.run(argv, cwd=output, env=environment, capture_output=True,
                                timeout=180, creationflags=creation)
        log.write_bytes(result.stdout + result.stderr)
        return {"source": str(source), "argv": argv, "exit_code": result.returncode,
                "object_path": str(obj), "compile_log": pin(log)}

    report["compiler_helper"] = pin(bootstrap)
    report["compile_parallelism"] = len(sources) if args.prior_attempt is None else 0
    if args.prior_attempt is None:
        with ThreadPoolExecutor(max_workers=len(sources)) as pool:
            compiled = list(pool.map(compile_one, sources))
    else:
        prior_path = args.prior_attempt.resolve() / "RESULT.json"
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        require(prior["compile_exit"] == 0, "prior necessary compile did not pass")
        require(prior["source_pins"] == report["source_pins"],
                "prior compiled source changed before incremental relink")
        compiled = prior["compile_commands"]
        require(len(compiled) == len(sources) and
                all(row["exit_code"] == 0 for row in compiled),
                "prior compiled object set is incomplete")
        report["prior_successful_compile"] = pin(prior_path)
        report["reused_prior_compile_objects"] = [pin(Path(row["object_path"]))
                                                 for row in compiled]
    report["compile_commands"] = compiled
    report["new_translation_units_compiled"] = len(sources) if args.prior_attempt is None else 0
    report["compile_exit"] = next((row["exit_code"] for row in compiled if row["exit_code"] != 0), 0)
    require(report["compile_exit"] == 0, "necessary strict translation-unit compile failed")
    executable = output / "battle-runtime-advantage-scaling-focused.exe"
    argv = [str(Path(compiler["cl"]).parent / "link.exe"), "/nologo", "/OPT:REF",
            *[row["object_path"] for row in compiled],
            *[row["object"]["path"] for row in reused],
            "/OUT:" + str(executable), "kernel32.lib", "user32.lib"]
    result = subprocess.run(argv, cwd=output, env=environment, capture_output=True,
                            timeout=60, creationflags=creation)
    log = output / "link.log"
    log.write_bytes(result.stdout + result.stderr)
    report.update(link_argv=argv, link_exit=result.returncode, link_log=pin(log))
    require(result.returncode == 0, "focused production dependency link failed")
    return environment, executable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--reuse-manifest", type=Path)
    parser.add_argument("--prior-attempt", type=Path,
                        help="reuse successful necessary compile after a recorded link harness failure")
    parser.add_argument("--python-check-only", action="store_true")
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--python-result", type=Path)
    args = parser.parse_args()
    if args.python_check_only:
        require(args.native_dir is not None and args.python_result is not None,
                "Python check needs native-dir and python-result")
        return python_check(args)
    require(args.build_dir is not None, "build-dir required")
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    report = {"schema": "ck3-12003-runtime-advantage-scaling-focused/v1",
              "status": "HARNESS-RED", "readiness": "source-ready",
              "runner": pin(Path(__file__).resolve()), "compile_exit": None,
              "run_exit": None, "python_exit": None, "bounded_cases": 2,
              "native_reader_frames": 3, "registered_mcp_client_calls": 4,
              "whole_dll_built": False, "local_ck3_touched": False,
              "live_game_calls": 0, "window_operations": 0, "git_mutations": 0,
              "old_test_cases_run": 0}
    started = time.perf_counter()
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        environment, executable = build_native(args, output, report)
        report["status"] = "FIXTURE-RED"
        result = subprocess.run([str(executable), str(wire)], cwd=output, env=environment,
                                capture_output=True, timeout=30, creationflags=creation)
        log = output / "run.log"
        log.write_bytes(result.stdout + result.stderr)
        report.update(run_exit=result.returncode, run_log=pin(log), executable=pin(executable))
        require(result.returncode == 0, "production native coefficient fixture failed")
        command = [sys.executable, "-O", str(Path(__file__).resolve()), "--python-check-only",
                   "--project-root", str(args.project_root.resolve()), "--projection-root",
                   str(args.projection_root.resolve()), "--native-dir", str(wire),
                   "--python-result", str(output / "REGISTERED-MCP-RESULT.json")]
        result = subprocess.run(command, cwd=output, env=environment, capture_output=True,
                                timeout=60, creationflags=creation)
        log = output / "python.log"
        log.write_bytes(result.stdout + result.stderr)
        report.update(python_argv=command, python_exit=result.returncode, python_log=pin(log))
        require(result.returncode == 0, "registered Python -O coefficient fixture failed")
        report.update(status="GREEN", readiness="static-ready",
                      registered_mcp_result=pin(output / "REGISTERED-MCP-RESULT.json"),
                      native_json=pin(wire / "runtime_advantage_scaling_cases.json"))
    except Exception as error:
        report["error"] = repr(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    result_path = output / "RESULT.json"
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(result_path),
                      "error": report.get("error")}))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
