"""Verify copied Sway execution records through the actual owner mailbox and command-result wire."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_wire(path: Path) -> dict:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict) or packet.get("type") != "command_result" or packet.get("ok") is not True:
        raise RuntimeError(f"Actual serializer must emit a successful command_result envelope: {path}")
    if packet.get("protocol_version") != 1 or not isinstance(packet.get("request_id"), str):
        raise RuntimeError(f"Command-result protocol/request identity missing: {path}")
    result = packet.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Command-result body missing: {path}")
    expected = {
        "step": "query-sway-completion-execution-v1-private",
        "accepted": True, "private_build": True, "read_only": True,
        "advertised": False, "build_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "backend_id": "native-headless",
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise RuntimeError(f"Actual private command-result {key} mismatch: {path}")
    state = result.get("sway_completion_execution")
    if not isinstance(state, dict):
        raise RuntimeError(f"Copied execution-source query missing from command-result: {path}")
    if (state.get("material_effect_observed") is not False
            or state.get("native_terminal_state_observed") is not False):
        raise RuntimeError(f"Copied executing input cannot claim independent material/terminal evidence: {path}")
    if result.get("status") != ("available" if state.get("available") else "unavailable"):
        raise RuntimeError(f"Private command-result status disagrees with actual recorder query: {path}")
    for record in state.get("records", []):
        if (record.get("executing_input_observed") is not True
                or record.get("exact_scope_join_ready") is not True
                or record.get("message_enqueue_observed") is not False
                or record.get("material_effect_observed") is not False
                or record.get("native_terminal_state_observed") is not False):
            raise RuntimeError(f"Copied query record has incorrect evidence boundary: {path}")
    return {
        "sha256": _sha256(path), "status": result["status"],
        "record_count": len(state.get("records", [])),
        "observer_attached": state.get("observer_attached"),
        "actor_character_id": state.get("actor_character_id"),
        "target_character_id": state.get("target_character_id"),
        "scheme_instance_id": state.get("scheme_instance_id"),
        "snapshot_revision": result.get("snapshot_revision"),
        "date_raw": result.get("date_raw"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment

    environment = _visual_studio_environment()
    environment["TEMP"] = environment["TMP"] = str(temporary)
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_query_mailbox.cpp",
        "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_mailbox.cpp",
        "ck3_12002_sway_completion_execution_serializer.cpp",
        "ck3_12002_sway_completion_execution_mailbox_test.cpp")]
    handler = native / "src/ck3_12002_sway_completion_execution_handler.cpp"
    pins = sources + [handler, Path(__file__).resolve(),
                      native / "src/ck3_12002_sway_completion_execution_test.cpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_execution.hpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp",
                      native / "include/xar_bridge/ck3_12002_query_mailbox.hpp",
                      native / "include/xar_bridge/ck3_12002_event_window_context.hpp",
                      native / "include/xar_bridge/game_adapter.hpp",
                      native / "include/xar_bridge/ck3_12002.hpp",
                      native.parents[1] / "research/sway_completion12002_history_abi.json"]
    suites: list[dict] = []
    result = {
        "schema": "xar.ck3.sway-completion12002-execution-mailbox-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False, "actual_production_reader": True,
        "actual_copied_recorder": True, "actual_owner_mailbox": True,
        "actual_serializer": True, "handler_compile_only": True,
        "shared_worker_dispatch_included": False,
        "fixture_frame_adapter": True, "fixture_observer_attached_input": True,
        "native_entry_installed": False,
        "native_material_or_terminal_postcondition_verified": False,
        "old_196_check_suite_reexecuted": False,
        "cases": ["not-attached unavailable", "hidden good exact full IDs", "wrong generation available empty"],
        "source_sha256": {str(path): _sha256(path) for path in pins},
        "suites": suites,
    }
    receipt = output / "result.json"
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-completion-execution-mailbox.exe"
            common = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                      "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                      "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                      "/I" + str(native / "include")]
            compile_command = [*common, *map(str, sources), "/Fe:" + str(executable)]
            compiled = subprocess.run(compile_command, cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            run_command = [str(executable), str(cell)]
            executed = subprocess.run(run_command, cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            handler_command = [*common, "/c", str(handler),
                               "/Fo:" + str(cell / "execution-handler.obj")]
            compiled_handler = subprocess.run(handler_command, cwd=cell, env=environment,
                                              capture_output=True, text=True,
                                              encoding="utf-8", errors="replace")
            (cell / "handler-compile.log").write_text(
                compiled_handler.stdout + compiled_handler.stderr, encoding="utf-8")
            if compiled_handler.returncode:
                raise RuntimeError(f"Handler compile RED {mode}: {cell / 'handler-compile.log'}")
            wire_paths = sorted(cell.glob("*-command-result.json"))
            if len(wire_paths) != 3:
                raise RuntimeError(f"Expected three actual transport cases, got {len(wire_paths)}: {cell}")
            wires = {path.name: _validate_wire(path) for path in wire_paths}
            summaries = [(wire["status"], wire["record_count"], wire["observer_attached"])
                         for wire in wires.values()]
            if sorted(summaries) != sorted([
                    ("unavailable", 0, False), ("available", 1, True), ("available", 0, True)]):
                raise RuntimeError(f"Actual transport case availability/record boundary mismatch: {cell}")
            suites.append({
                "mode": mode, "status": "GREEN", "compiler": "MSVC /W4 /WX",
                "optimization": optimization, "runtime": "/MD _ITERATOR_DEBUG_LEVEL=0",
                "exe_sha256": _sha256(executable),
                "handler_object_sha256": _sha256(cell / "execution-handler.obj"),
                "commands": {"compile": compile_command, "run": run_command,
                             "handler_compile": handler_command},
                "wires": wires, "output": executed.stdout.strip(),
            })
            print(mode, executed.stdout.strip())
        result["status"] = "GREEN"
    except Exception as error:
        result["failure"] = str(error)
        raise
    finally:
        receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
